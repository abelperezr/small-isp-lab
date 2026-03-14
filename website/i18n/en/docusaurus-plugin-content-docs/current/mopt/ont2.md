---
sidebar_position: 9
---

# ONT2 - PPPoE

## General Information

| Parameter | Value |
|-----------|-------|
| **Hostname** | ont2 |
| **Image** | ghcr.io/abelperezr/ont-ds:0.3 or later |
| **Management IP** | 10.99.1.6 |
| **SSH port** | 56689 |
| **Web GUI** | http://localhost:8091 |
| **Connection Type** | PPPoE |

## Function in Topology

ONT2 is an optical network terminal with **PPPoE** connection to the BNG. Unlike ONT1 (IPoE), authentication is done using PPP credentials (user/password) instead of MAC address.

---

## 1. WAN1 CONFIGURATION - PPPoE IPv6 Only

```yaml
# lab.yml
CONNECTION_TYPE: pppoe
WAN1_MODE: "ipv6"
PPP_USER: "test@test.com"
PPP_PASS: "testlab123"
VLAN_ID: "150"
IFPHY: "eth1"
IFLAN: "eth2"
MAC_ADDRESS: "00:D0:F6:01:01:04"
USER_PASSWORD: "test"
```

| Parameter | Value |
|-----------|-------|
| Physical interface | eth1 |
| C-VLAN | 150 |
| S-VLAN (OLT) | 50 |
| MAC | 00:D0:F6:01:01:04 |
| Type | PPPoE |
| PPP User | test@test.com |
| PPP Password | testlab123 |
| stack | IPv6 only |
| Group Interface | ipv6-only |
| Subscriber ID | ONT-002-PPPOE |
| Pool IPv6 WAN | 2001:db8:100::/56 |
| Pool IPv6 PD | 2001:db8:200::/48 |

---

## 2. MAPPED PORTS

| Internal Port | External Port | Service |
|----------------|----------------|----------|
| 22 | 56689 | SSH |
| 8080 | 8091 | Web GUI |
