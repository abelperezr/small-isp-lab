---
sidebar_position: 8
---

# ONT1 - IPoE Multi-WAN

## Información General

| Parámetro | Valor |
|-----------|-------|
| **Hostname** | ont1 |
| **Imagen** | ghcr.io/abelperezr/ont-ds:0.3 o superior |
| **IP de Gestión** | 10.99.1.5 |
| **Puerto SSH** | 56615 |
| **Web GUI** | http://localhost:8090 |
| **Tipo Conexión** | IPoE |

## Función en la Topología

ONT1 es un terminal de red óptica con **tres interfaces WAN** simultáneas, cada una conectada a un servicio diferente del BNG. La imagen `ont-ds` (ONT Dual-Stack) soporta configuración multi-WAN con VLANs, MACs independientes y PBR (Policy Based Routing) para enrutar el tráfico de cada WAN correctamente.

---

## 1. CONFIGURACIÓN WAN1 - IPv6 Only

```yaml
# lab.yml
IFPHY: "eth1"
VLAN_ID: "150"
MAC_ADDRESS: "00:D0:F6:01:01:01"
WAN1_MODE: "ipv6"
IFLAN: "eth2"           # LAN hacia PC1
```

| Parámetro | Valor |
|-----------|-------|
| Interface física | eth1 |
| C-VLAN | 150 |
| S-VLAN (OLT) | 50 |
| MAC | 00:D0:F6:01:01:01 |
| Stack | IPv6 only |
| Group Interface | ipv6-only |
| NAT | NAT64 (64:ff9b::/96) |
| Pool IPv6 WAN | `2001:db8:100::/56` |
| Pool IPv6 PD | 2001:db8:200::/48 |

---

## 2. CONFIGURACIÓN WAN2 - Dual-Stack

```yaml
# lab.yml
IFPHY2: "eth3"
VLAN_ID2: "200"
MAC_ADDRESS2: "00:D0:F6:01:01:02"
WAN2_MODE: "dual"
WAN2_DHCP_PERSIST: "true"
```

| Parámetro | Valor |
|-----------|-------|
| Interface física | eth3 |
| C-VLAN | 200 |
| S-VLAN (OLT) | 51 |
| MAC | 00:D0:F6:01:01:02 |
| Stack | Dual-Stack (IPv4 + IPv6) |
| Group Interface | dual-stack |
| NAT IPv4 | CGNAT Determinístico (100.80.0.x → 99.99.99.99) |
| Pool IPv4 | cgnat (100.80.0.0/29) |
| Pool IPv6 WAN | 2001:db8:cccc::/56 |
| Pool IPv6 PD | 2001:db8:dddd::/48 |

---

## 3. CONFIGURACIÓN WAN3 - VIP (IPv4 Only)

```yaml
# lab.yml
IFPHY3: "eth4"
VLAN_ID3: "300"
MAC_ADDRESS3: "00:D0:F6:01:01:03"
WAN3_MODE: "ipv4"
WAN3_DHCP_PERSIST: "true"
```

| Parámetro | Valor |
|-----------|-------|
| Interface física | eth4 |
| C-VLAN | 300 |
| S-VLAN (OLT) | 52 |
| MAC | 00:D0:F6:01:01:03 |
| Stack | IPv4 only |
| Group Interface | vip |
| NAT | One-to-One (192.168.5.x → 88.88.88.x) |
| Pool IPv4 | one-to-one (192.168.5.0/29) |

---

## 4. LAN

```yaml
IFLAN: "eth2"    # Conecta a PC1
```

ONT1 anuncia los prefijos delegados (PD) via Router Advertisement en su interfaz LAN (eth2) hacia PC1.

---

## 5. CONFIGURACIÓN ADICIONAL

```yaml
USER_PASSWORD: "test"
DISABLE_MGMT_IPV6: "true"    # Deshabilita IPv6 en la interfaz de gestión
```
