---
sidebar_position: 9
---

# ONT2 - PPPoE

## Información General

| Parámetro | Valor |
|-----------|-------|
| **Hostname** | ont2 |
| **Imagen** | ghcr.io/abelperezr/ont-ds:0.3 o superior |
| **IP de Gestión** | 10.99.1.6 |
| **Puerto SSH** | 56689 |
| **Web GUI** | http://localhost:8091 |
| **Tipo Conexión** | PPPoE |

## Función en la Topología

ONT2 es un terminal de red óptica con conexión **PPPoE** hacia el BNG. A diferencia de ONT1 (IPoE), la autenticación se realiza mediante credenciales PPP (usuario/contraseña) en lugar de MAC address.

---

## 1. CONFIGURACIÓN WAN1 - PPPoE IPv6 Only

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

| Parámetro | Valor |
|-----------|-------|
| Interface física | eth1 |
| C-VLAN | 150 |
| S-VLAN (OLT) | 50 |
| MAC | 00:D0:F6:01:01:04 |
| Tipo | PPPoE |
| PPP User | test@test.com |
| PPP Password | testlab123 |
| Stack | IPv6 only |
| Group Interface | ipv6-only |
| Subscriber ID | ONT-002-PPPOE |
| Pool IPv6 WAN | `2001:db8:100::/56` |
| Pool IPv6 PD | 2001:db8:200::/48 |

---

## 2. PUERTOS MAPEADOS

| Puerto Interno | Puerto Externo | Servicio |
|----------------|----------------|----------|
| 22 | 56689 | SSH |
| 8080 | 8091 | Web GUI |
