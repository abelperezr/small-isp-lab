---
sidebar_position: 4
---

# SRRP Redundancy

## Diagrama SRRP

![SRRP Redundancy](/img/srrp.png)

## Descripción

El **SRRP (Subscriber Routed Redundancy Protocol)** proporciona redundancia activo/backup para las sesiones de suscriptores entre el BNG MASTER y el BNG SLAVE. A diferencia de VRRP que opera en capa 3, SRRP está diseñado específicamente para entornos ESM (Enhanced Subscriber Management).

## Instancias SRRP

El laboratorio configura 3 instancias SRRP, una por cada Group Interface:

| SRRP ID | Group Interface | Servicio | SRRP VLAN |
|---------|-----------------|----------|-----------|
| 1 | ipv6-only | IPv6-only + NAT64 | 4094.1 |
| 2 | dual-stack | Dual-Stack + CGNAT | 4094.2 |
| 3 | vip | VIP + One-to-One NAT | 4094.3 |

## Configuración SRRP (más informacion en MOPT)

### BNG MASTER (Priority 200)

```text
/configure service vprn "9998" subscriber-interface "services" group-interface "ipv6-only" srrp 1 admin-state enable
/configure service vprn "9998" subscriber-interface "services" group-interface "ipv6-only" srrp 1 priority 200
/configure service vprn "9998" subscriber-interface "services" group-interface "ipv6-only" srrp 1 message-path 1/1/c2/1:4094.1
/configure service vprn "9998" subscriber-interface "services" group-interface "ipv6-only" srrp 1 keep-alive-interval 30
/configure service vprn "9998" subscriber-interface "services" group-interface "ipv6-only" srrp 1 policy 1
```

### BNG SLAVE (Priority 50)

```text
/configure service vprn "9998" subscriber-interface "services" group-interface "ipv6-only" srrp 1 admin-state enable
/configure service vprn "9998" subscriber-interface "services" group-interface "ipv6-only" srrp 1 priority 50
/configure service vprn "9998" subscriber-interface "services" group-interface "ipv6-only" srrp 1 message-path 1/1/c2/1:4094.1
```

## SRRP Message Path

Los mensajes SRRP viajan sobre la VLAN 4094 a través de la OLT. Es **crítico** que la OLT tenga configurado un MAC-VRF para la VLAN 4094 que incluya los puertos hacia ambos BNGs:

```text
# En OLT (SR Linux)
set /interface ethernet-1/1 subinterface 4094 type bridged
set /interface ethernet-1/1 subinterface 4094 vlan encap single-tagged vlan-id 4094
set /interface ethernet-1/2 subinterface 4094 type bridged
set /interface ethernet-1/2 subinterface 4094 vlan encap single-tagged vlan-id 4094

set /network-instance bd-srrp type mac-vrf
set /network-instance bd-srrp admin-state enable
set /network-instance bd-srrp interface ethernet-1/1.4094
set /network-instance bd-srrp interface ethernet-1/2.4094
```

:::danger[Problema Conocido: Dual-Master]

Si la OLT no tiene configurado el MAC-VRF `bd-srrp` con la VLAN 4094, los mensajes SRRP no llegarán entre los BNGs y ambos se declararán MASTER simultáneamente, causando conflictos de direcciones IP y pérdida de sesiones.

:::
## Multi-Chassis Redundancy

La sincronización de estado entre BNGs se configura vía MCS (Multi-Chassis Synchronization):

```text
/configure redundancy multi-chassis peer 10.0.0.2 admin-state enable
/configure redundancy multi-chassis peer 10.0.0.2 source-address 10.0.0.1
/configure redundancy multi-chassis peer 10.0.0.2 sync admin-state enable
/configure redundancy multi-chassis peer 10.0.0.2 sync local-dhcp-server true
/configure redundancy multi-chassis peer 10.0.0.2 sync srrp true
/configure redundancy multi-chassis peer 10.0.0.2 sync sub-host-trk true
/configure redundancy multi-chassis peer 10.0.0.2 sync sub-mgmt ipoe true
/configure redundancy multi-chassis peer 10.0.0.2 sync sub-mgmt pppoe true
/configure redundancy multi-chassis peer 10.0.0.2 sync tags port 1/1/c2/1 sync-tag "mcs"
```

## DHCP Failover

Cada pool DHCP tiene configurado failover hacia el peer BNG:

```text
/configure service vprn "9998" dhcp-server dhcpv6 "suscriptores_v6" pool "IPv6" failover admin-state enable
/configure service vprn "9998" dhcp-server dhcpv6 "suscriptores_v6" pool "IPv6" failover ignore-mclt-on-takeover true
/configure service vprn "9998" dhcp-server dhcpv6 "suscriptores_v6" pool "IPv6" failover partner-down-delay 3600
/configure service vprn "9998" dhcp-server dhcpv6 "suscriptores_v6" pool "IPv6" failover peer 10.0.0.2 sync-tag "dhcpv6-only"
```

## Verificación

```bash
# Ver estado SRRP
show srrp

# Verificar multi-chassis
show redundancy multi-chassis all

# Ver sincronización
show redundancy multi-chassis sync peer 10.0.0.2
```
