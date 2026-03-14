---
sidebar_position: 7
---

# Internet Gateway

## Información General

| Parámetro | Valor |
|-----------|-------|
| **Hostname** | internet |
| **Imagen** | ghcr.io/srl-labs/network-multitool |
| **IP de Gestión** | 10.99.1.14 |
| **Puerto SSH** | 56620 |

## Función en la Topología

El nodo Internet simula la conectividad hacia el mundo exterior. Actúa como gateway para ambos carriers con NAT masquerade hacia la interfaz de gestión Docker, y mantiene rutas estáticas de retorno hacia los prefijos públicos del ISP.

---

## 1. INTERFACES

```text
# eth1: hacia Carrier1
ip link set eth1 up
ip addr add 10.99.100.2/30 dev eth1
ip -6 addr add fd00:a1::2/126 dev eth1

# eth2: hacia Carrier2
ip link set eth2 up
ip addr add 10.99.200.2/30 dev eth2
ip -6 addr add fd00:a2::2/126 dev eth2
```

---

## 2. FORWARDING Y RP_FILTER

```text
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv4.conf.all.rp_filter=0
sysctl -w net.ipv4.conf.eth0.rp_filter=0
sysctl -w net.ipv4.conf.eth1.rp_filter=0
sysctl -w net.ipv4.conf.eth2.rp_filter=0
sysctl -w net.ipv6.conf.all.forwarding=1
```

---

## 3. NAT MASQUERADE

```text
# IPv4
iptables -P FORWARD ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
iptables -A FORWARD -i eth2 -o eth0 -j ACCEPT
iptables -A FORWARD -i eth0 -o eth1 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -i eth0 -o eth2 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# IPv6
ip6tables -P FORWARD ACCEPT
ip6tables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
ip6tables -A FORWARD -i eth1 -o eth0 -j ACCEPT
ip6tables -A FORWARD -i eth2 -o eth0 -j ACCEPT
ip6tables -A FORWARD -i eth0 -o eth1 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
ip6tables -A FORWARD -i eth0 -o eth2 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

---

## 4. RUTAS DE RETORNO IPv4

```text
# Prefijos públicos del ISP via Carrier 1
ip route add 99.99.99.99/32 via 10.99.100.1 dev eth1
ip route add 88.88.88.88/29 via 10.99.100.1 dev eth1
ip route add 199.199.199.199/32 via 10.99.100.1 dev eth1

# Segmentos inter-BNG/Carrier
ip route add 172.16.1.0/31 via 10.99.100.1 dev eth1
ip route add 172.16.1.2/31 via 10.99.100.1 dev eth1
ip route add 172.16.2.0/31 via 10.99.200.1 dev eth2
ip route add 172.16.2.2/31 via 10.99.200.1 dev eth2
```

---

## 5. RUTAS DE RETORNO IPv6

```text
ip -6 route add 2001:db8:100::/56 via fd00:a1::1 dev eth1
ip -6 route add 2001:db8:200::/48 via fd00:a1::1 dev eth1
ip -6 route add 2001:db8:cccc::/56 via fd00:a2::1 dev eth2
ip -6 route add 2001:db8:dddd::/48 via fd00:a2::1 dev eth2
```
