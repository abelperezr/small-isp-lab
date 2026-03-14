---
sidebar_position: 8
---

# ONT1 - IPoE Multi-WAN

## General Information

| Parameter | Value |
|-----------|-------|
| **Hostname** | ont1 |
| **Image** | ghcr.io/abelperezr/ont-ds:0.3 or later |
| **Management IP** | 10.99.1.5 |
| **SSH port** | 56615 |
| **Web GUI** | http://localhost:8090 |
| **Connection Type** | IPoE |

## Function in Topology

ONT1 is an optical network terminal with **three simultaneous WAN interfaces**, each connected to a different BNG service. The `ont-ds` (ONT Dual-Stack) image supports multi-WAN configuration with VLANs, independent MACs and PBR (Policy Based Routing) to route traffic from each WAN correctly.

---

## 1. WAN1 CONFIGURATION - IPv6 Only

```yaml
# lab.yml
IFPHY: "eth1"
VLAN_ID: "150"
MAC_ADDRESS: "00:D0:F6:01:01:01"
WAN1_MODE: "ipv6"
IFLAN: "eth2"           # LAN to PC1
```

| Parameter | Value |
|-----------|-------|
| Physical interface | eth1 |
| C-VLAN | 150 |
| S-VLAN (OLT) | 50 |
| MAC | 00:D0:F6:01:01:01 |
| stack | IPv6 only |
| Group Interface | ipv6-only |
| NAT | NAT64 (64:ff9b::/96) |
| Pool IPv6 WAN | 2001:db8:100::/56 |
| Pool IPv6 PD | 2001:db8:200::/48 |

---

## 2. WAN2 CONFIGURATION - Dual-Stack

```yaml
# lab.yml
IFPHY2: "eth3"
VLAN_ID2: "200"
MAC_ADDRESS2: "00:D0:F6:01:01:02"
WAN2_MODE: "dual"
WAN2_DHCP_PERSIST: "true"
```

| Parameter | Value |
|-----------|-------|
| Physical interface | eth3 |
| C-VLAN | 200 |
| S-VLAN (OLT) | 51 |
| MAC | 00:D0:F6:01:01:02 |
| stack | Dual-Stack (IPv4 + IPv6) |
| Group Interface | dual-stack |
| IPv4 NAT | CGNAT Deterministic (100.80.0.x → 99.99.99.99) |
| IPv4 Pool | cgnat (100.80.0.0/29) |
| Pool IPv6 WAN | 2001:db8:cccc::/56 |
| Pool IPv6 PD | 2001:db8:dddd::/48 |

---

## 3. WAN3 CONFIGURATION - VIP (IPv4 Only)

```yaml
# lab.yml
IFPHY3: "eth4"
VLAN_ID3: "300"
MAC_ADDRESS3: "00:D0:F6:01:01:03"
WAN3_MODE: "ipv4"
WAN3_DHCP_PERSIST: "true"
```

| Parameter | Value |
|-----------|-------|
| Physical interface | eth4 |
| C-VLAN | 300 |
| S-VLAN (OLT) | 52 |
| MAC | 00:D0:F6:01:01:03 |
| stack | IPv4 only |
| Group Interface | vip |
| NAT | One-to-One (192.168.5.x → 88.88.88.x) |
| IPv4 Pool | one-to-one (192.168.5.0/29) |

---

## 4. LAN

```yaml
IFLAN: "eth2"    # Connects to PC1
```

ONT1 announces the delegated prefixes (PD) via Router Advertisement on its LAN interface (eth2) to PC1.

---

## 5. ADDITIONAL SETTINGS

```yaml
USER_PASSWORD: "test"
DISABLE_MGMT_IPV6: "true"    # Disables IPv6 on the management interface
```
