---
sidebar_position: 11
---

# LIG - Lawful Interception Gateway

## General Information

| Parameter | Value |
|-----------|-------|
| **Hostname** | lig |
| **Image** | ghcr.io/srl-labs/network-multitool + Python3 |
| **Management IP** | 10.99.1.12 |
| **SSH port** | 56619 |
| **DashboardWeb** | http://localhost:8092 |
| **LI Listener** | UDP 11111 |

## Function in Topology

The LIG (Lawful Interception Gateway) receives the intercepted traffic from the Nokia BNGs using the **ip-udp-shim** format and presents it on a web dashboard (LEA Console) in real time. For more details on the architecture and operation, see the [LEA Console](../lea-console/index.md) section.

---

## 1. INTERFACES

```text
# eth1: hacia BNG MASTER (VPRN 9999)
ip addr add 172.19.1.1/30 dev eth1
ip -6 addr add 2001:db8:ffff::1/126 dev eth1

# eth2: hacia BNG SLAVE (VPRN 9999)
ip addr add 172.20.1.1/30 dev eth2
```

---

## 2. FORWARDING AND RP_FILTER

```text
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv4.conf.all.rp_filter=0
sysctl -w net.ipv4.conf.eth1.rp_filter=0
sysctl -w net.ipv4.conf.eth2.rp_filter=0
```

---

## 3. NAT MASQUERADE

```text
iptables -P FORWARD ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
iptables -A FORWARD -i eth0 -o eth1 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

---

## 4. SCRIPT LIG (lig.py)

```python
#!/usr/bin/env python3
"""
LIG - Lawful Interception Gateway 
"""

import socket
import struct
import threading
import json
import time
from datetime import datetime
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ─── Almacenamiento en memoria ───────────────────────────────────────────────
MAX_EVENTS = 2000
events = deque(maxlen=MAX_EVENTS)
stats = {
    "total_packets": 0,
    "ingress": 0,
    "egress": 0,
    "ipv4": 0,
    "ipv6": 0,
    "intercepts": {}  # intercept_id → {packets, first_seen, last_seen}
}
lock = threading.Lock()

PROTO_NAMES = {1: "ICMP", 6: "TCP", 17: "UDP", 58: "ICMPv6", 50: "ESP", 51: "AH"}

# ─── Nokia LI ───────────────────────────────────────
#  payload UDP con ip-udp-shim + Ethernet frame:
#
#  Bytes  0-1  : Nokia LI flags  (bit15=direction: 0=ingress,1=egress)
#  Bytes  2-3  : Intercept-ID    (uint16, ej: 0x03e9 = 1001)
#  Bytes  4-5  : Padding         (0x0000)
#  Bytes  6-7  : Session-ID      (uint16, ej: 0x0001 = 1)
#  Bytes  8-13 : Ethernet DST MAC (6 bytes)
#  Bytes 14-19 : Ethernet SRC MAC (6 bytes)
#  Bytes 20-23 : 802.1Q outer tag (0x8100 + outer VLAN)
#  Bytes 24-27 : 802.1Q inner tag (0x8100 + inner VLAN)
#  Bytes 28-29 : EtherType        (0x86dd=IPv6 / 0x0800=IPv4)
#  Bytes 30+   : Inner IP packet

SHIM_HDR_SIZE  = 8   # Nokia shim
ETH_HDR_QINQ   = 22  # DST(6) + SRC(6) + 802.1Q-outer(4) + 802.1Q-inner(4) + EtherType(2)
INNER_OFFSET   = SHIM_HDR_SIZE + ETH_HDR_QINQ  # = 30

ETHERTYPE_IPV4 = 0x0800
ETHERTYPE_IPV6 = 0x86DD
ETHERTYPE_8021Q = 0x8100


def decode_mac(data, offset):
    return ":".join(f"{b:02x}" for b in data[offset:offset+6])


def find_inner_ip(data, start_offset):
    """
    Navega headers Ethernet/802.1Q desde start_offset hasta encontrar
    el EtherType IPv4 o IPv6. Soporta QinQ (doble tag) y single tag.
    Devuelve el offset del primer byte del IP header, o None.
    """
    off = start_offset
    # Saltar MACs (dst + src = 12 bytes)
    off += 12
    if off + 2 > len(data):
        return None

    # Navegar tags 802.1Q
    for _ in range(3):  # máximo 3 tags (QinQ, S-Tag, C-Tag)
        if off + 2 > len(data):
            return None
        ethertype = struct.unpack("!H", data[off:off+2])[0]
        off += 2
        if ethertype == ETHERTYPE_IPV4 or ethertype == ETHERTYPE_IPV6:
            return off  # encontrado
        elif ethertype == ETHERTYPE_8021Q:
            off += 2    # saltar los 2 bytes de TCI (PCP+DEI+VID)
        else:
            return None  # EtherType desconocido

    return None


def parse_ip_packet(data, offset):
    """Parsea un IP packet (v4 o v6) en data[offset:]. Devuelve dict o None."""
    if offset is None or offset >= len(data):
        return None

    inner = data[offset:]
    src_ip = dst_ip = proto_name = ip_version = None
    src_port = dst_port = None

    if len(inner) >= 20 and (inner[0] >> 4) == 4:
        ip_version = "IPv4"
        src_ip     = socket.inet_ntoa(inner[12:16])
        dst_ip     = socket.inet_ntoa(inner[16:20])
        proto      = inner[9]
        proto_name = PROTO_NAMES.get(proto, str(proto))
        ihl        = (inner[0] & 0x0F) * 4
        if proto in (6, 17) and len(inner) >= ihl + 4:
            src_port = struct.unpack("!H", inner[ihl:ihl+2])[0]
            dst_port = struct.unpack("!H", inner[ihl+2:ihl+4])[0]

    elif len(inner) >= 40 and (inner[0] >> 4) == 6:
        ip_version = "IPv6"
        src_ip     = socket.inet_ntop(socket.AF_INET6, inner[8:24])
        dst_ip     = socket.inet_ntop(socket.AF_INET6, inner[24:40])
        proto      = inner[6]
        proto_name = PROTO_NAMES.get(proto, str(proto))
        if proto in (6, 17) and len(inner) >= 44:
            src_port = struct.unpack("!H", inner[40:42])[0]
            dst_port = struct.unpack("!H", inner[42:44])[0]

    return {
        "ip_version": ip_version,
        "src_ip":     src_ip,
        "dst_ip":     dst_ip,
        "src_port":   src_port,
        "dst_port":   dst_port,
        "proto":      proto_name,
        "size":       len(inner),
    }


# ─── Parser principal ─────────────────────────────────────────────────────────
def parse_shim(data):
    """
    Parsea el payload UDP completo del LI Nokia ip-udp-shim.
    Estructura: [Nokia shim 8B] + [Ethernet frame con QinQ] + [Inner IP]
    """
    if len(data) < SHIM_HDR_SIZE + 14:
        return None

    # ── Nokia LI Shim (8 bytes) ──────────────────────────────────────────────
    flags        = struct.unpack("!H", data[0:2])[0]
    intercept_id = struct.unpack("!H", data[2:4])[0]   # uint16 en bytes 2-3
    # bytes 4-5 = padding
    session_id   = struct.unpack("!H", data[6:8])[0]   # uint16 en bytes 6-7
    direction    = "EGRESS" if (flags & 0x8000) else "INGRESS"

    # ── Ethernet frame (desde byte 8) ────────────────────────────────────────
    eth_offset = SHIM_HDR_SIZE
    mac_dst = decode_mac(data, eth_offset)
    mac_src = decode_mac(data, eth_offset + 6)

    # Encontrar el inner IP navegando los tags 802.1Q
    ip_offset = find_inner_ip(data, eth_offset)
    ip_info   = parse_ip_packet(data, ip_offset)

    # VLANs (extraer outer e inner si existen)
    outer_vlan = inner_vlan = None
    tag_off = eth_offset + 12
    if tag_off + 2 <= len(data):
        et1 = struct.unpack("!H", data[tag_off:tag_off+2])[0]
        if et1 == ETHERTYPE_8021Q and tag_off + 4 <= len(data):
            outer_vlan = struct.unpack("!H", data[tag_off+2:tag_off+4])[0] & 0x0FFF
            et2_off = tag_off + 4
            if et2_off + 2 <= len(data):
                et2 = struct.unpack("!H", data[et2_off:et2_off+2])[0]
                if et2 == ETHERTYPE_8021Q and et2_off + 4 <= len(data):
                    inner_vlan = struct.unpack("!H", data[et2_off+2:et2_off+4])[0] & 0x0FFF

    return {
        "intercept_id": intercept_id,
        "session_id":   session_id,
        "direction":    direction,
        "mac_src":      mac_src,
        "mac_dst":      mac_dst,
        "outer_vlan":   outer_vlan,
        "inner_vlan":   inner_vlan,
        "ip_version":   ip_info["ip_version"]  if ip_info else None,
        "src_ip":       ip_info["src_ip"]       if ip_info else None,
        "dst_ip":       ip_info["dst_ip"]       if ip_info else None,
        "src_port":     ip_info["src_port"]     if ip_info else None,
        "dst_port":     ip_info["dst_port"]     if ip_info else None,
        "proto":        ip_info["proto"]        if ip_info else None,
        "size":         ip_info["size"]         if ip_info else len(data) - SHIM_HDR_SIZE,
        "timestamp":    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
    }


# ─── Listener UDP ─────────────────────────────────────────────────────────────
def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", 11111))
    print("[LIG] Escuchando en UDP 0.0.0.0:11111")

    while True:
        try:
            data, addr = sock.recvfrom(65535)
            parsed = parse_shim(data)
            if not parsed:
                continue

            with lock:
                events.appendleft(parsed)
                stats["total_packets"] += 1
                stats["ingress" if parsed["direction"] == "INGRESS" else "egress"] += 1
                if parsed["ip_version"] == "IPv4":
                    stats["ipv4"] += 1
                elif parsed["ip_version"] == "IPv6":
                    stats["ipv6"] += 1

                iid = str(parsed["intercept_id"])
                if iid not in stats["intercepts"]:
                    stats["intercepts"][iid] = {
                        "packets": 0,
                        "bytes": 0,
                        "first_seen": parsed["timestamp"],
                        "last_seen": parsed["timestamp"]
                    }
                stats["intercepts"][iid]["packets"] += 1
                stats["intercepts"][iid]["bytes"]   += parsed["size"]
                stats["intercepts"][iid]["last_seen"] = parsed["timestamp"]

        except Exception as e:
            print(f"[LIG] Error UDP: {e}")


# ─── API REST ─────────────────────────────────────────────────────────────────
class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silenciar logs HTTP

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs     = parse_qs(parsed.query)

        if parsed.path == "/api/events":
            limit  = int(qs.get("limit", [100])[0])
            iid    = qs.get("intercept_id", [None])[0]
            with lock:
                result = list(events)
            if iid:
                result = [e for e in result if str(e["intercept_id"]) == iid]
            self.send_json(result[:limit])

        elif parsed.path == "/api/stats":
            with lock:
                self.send_json(dict(stats))

        elif parsed.path == "/api/intercepts":
            with lock:
                ids = [
                    {"intercept_id": int(k), **v}
                    for k, v in stats["intercepts"].items()
                ]
            self.send_json(ids)

        elif parsed.path == "/api/clear":
            with lock:
                events.clear()
                stats["total_packets"] = 0
                stats["ingress"] = 0
                stats["egress"] = 0
                stats["ipv4"] = 0
                stats["ipv6"] = 0
                stats["intercepts"] = {}
            self.send_json({"status": "cleared"})

        elif parsed.path == "/" or parsed.path == "/index.html":
            try:
                with open("/app/index.html", "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_json({"error": "index.html not found"}, 404)
        else:
            self.send_json({"error": "not found"}, 404)


def api_server():
    server = HTTPServer(("0.0.0.0", 8080), APIHandler)
    print("[LIG] API REST en http://0.0.0.0:8080")
    server.serve_forever()


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    t1 = threading.Thread(target=udp_listener, daemon=True)
    t2 = threading.Thread(target=api_server,   daemon=True)
    t1.start()
    t2.start()
    print("[LIG] Sistema iniciado. Ctrl+C para detener.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[LIG] Detenido.")

```

---

## 5. STARTING

```text
mkdir -p /app
cp /config/lig.py /app/
cp /config/index.html /app/
nohup python3 /app/lig.py > /var/log/lig.log 2>&1 &
```
