---
sidebar_position: 4
---

# SRRP Redundancy

## SRRP Diagram

![SRRP Redundancy](/img/srrp.png)

## Description

**SRRP (Subscriber Routed Redundancy Protocol)** provides active/backup redundancy for subscriber sessions between the BNG MASTER and the BNG SLAVE. Unlike VRRP which operates at layer 3, SRRP is designed specifically for ESM (Enhanced Subscriber Management) environments.

## SRRP instances

The lab configures 3 SRRP instances, one for each Group Interface:

| SRRP ID | Group Interface | Service | SRRP VLAN |
|---------|-----------------|----------|-----------|
| 1 | ipv6-only | IPv6-only + NAT64 | 4094.1 |
| 2 | dual-stack | Dual-Stack + CGNAT | 4094.2 |
| 3 | vip | VIP + One-to-One NAT | 4094.3 |

## SRRP Configuration (more information at MOPT)

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

SRRP messages travel over VLAN 4094 through the OLT. It is **critical** that the OLT has a MAC-VRF configured for VLAN 4094 that includes the ports to both BNGs:

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

:::danger[Known Issue: Dual-Master]

If the OLT does not have MAC-VRF `bd-srrp` configured with VLAN 4094, SRRP messages will not arrive between the BNGs and both will declare MASTER simultaneously, causing IP address conflicts and session loss.

:::
## Multi-Chassis Redundancy

State synchronization between BNGs is configured via MCS (Multi-Chassis Synchronization):

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

Each DHCP pool has failover configured towards the BNG peer:

```text
/configure service vprn "9998" dhcp-server dhcpv6 "suscriptores_v6" pool "IPv6" failover admin-state enable
/configure service vprn "9998" dhcp-server dhcpv6 "suscriptores_v6" pool "IPv6" failover ignore-mclt-on-takeover true
/configure service vprn "9998" dhcp-server dhcpv6 "suscriptores_v6" pool "IPv6" failover partner-down-delay 3600
/configure service vprn "9998" dhcp-server dhcpv6 "suscriptores_v6" pool "IPv6" failover peer 10.0.0.2 sync-tag "dhcpv6-only"
```

## Verification

```bash
# Ver estado SRRP
show srrp

# Verificar multi-chassis
show redundancy multi-chassis all

# Ver sincronización
show redundancy multi-chassis sync peer 10.0.0.2
```
