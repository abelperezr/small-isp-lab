---
sidebar_position: 2
---

# Underlay Network

## Physical Connectivity Diagram

![Underlay Topology](/img/underlay.png)

## Description of the Physical Layer

The **Underlay** represents the IP/MPLS connectivity between the BNG MASTER and SLAVE, the L3 connections to the Carriers, and the L2 connections to the OLT and auxiliary services.

## Underlay IP Addressing

### Inter-BNG (IS-IS/LDP/iBGP)

| Segment | Grid | BNG MASTER | BNG SLAVE |
|----------|-----|------------|-----------|
| Inter-BNG | 172.99.1.0/31 | .0 | .1 |
| Loopback | /32 | 10.0.0.1 | 10.0.0.2 |
| Redundant IF | 192.168.12.0/31 | .0 | .1 |

### BNG to Carrier 1 (172.16.1.x/31)

| Segment | Grid | BNG | Carrier 1 |
|----------|-----|-----|-----------|
| MASTER → C1 | 172.16.1.0/31 | .0 | .1 |
| SLAVE → C1 | 172.16.1.2/31 | .2 | .3 |

### BNG to Carrier 2 (172.16.2.x/31)

| Segment | Grid | BNG | Carrier 2 |
|----------|-----|-----|-----------|
| MASTER → C2 | 172.16.2.0/31 | .0 | .1 |
| SLAVE → C2 | 172.16.2.2/31 | .2 | .3 |

### BNG to LIG

| Segment | Grid | BNG | LIG |
|----------|-----|-----|-----|
| MASTER → LIG | 172.19.1.0/30 | .2 | .1 |
| SLAVE → LIG | 172.20.1.0/30 | .2 | .1 |

## Routing Protocols

### IS-IS (Inter-BNG)

The link between BNG MASTER and SLAVE runs IS-IS Level 2 as the routing protocol for the MPLS underlay:

```text
/configure router "Base" isis 0 admin-state enable
/configure router "Base" isis 0 level-capability 2
/configure router "Base" isis 0 area-address [49.0001]
/configure router "Base" isis 0 interface "system" admin-state enable
/configure router "Base" isis 0 interface "to_SLAVE" admin-state enable
/configure router "Base" isis 0 interface "to_SLAVE" interface-type point-to-point
```

### LDP (MPLS Label Distribution)

LDP is used to establish LSPs between BNGs, necessary for the redundant-interface SDP and VPN-IPv4/v6 transport:

```text
/configure router "Base" ldp interface-parameters interface "to_SLAVE" admin-state enable
/configure router "Base" ldp targeted-session peer 10.0.0.2 admin-state enable
```

### iBGP (VPN-IPv4/v6)

iBGP between loopbacks carries the VPN-IPv4 and VPN-IPv6 routes of VPRNs 9998 and 9999:

```text
/configure router "Base" bgp group "iBGP" admin-state enable
/configure router "Base" bgp group "iBGP" type internal
/configure router "Base" bgp group "iBGP" local-address 10.0.0.1
/configure router "Base" bgp group "iBGP" family vpn-ipv4 true
/configure router "Base" bgp group "iBGP" family vpn-ipv6 true
/configure router "Base" bgp group "iBGP" local-as as-number 65510
```

## BNG Port Configuration

| Port | Encapsulation | Destination | Function |
|--------|---------------|---------|---------|
| 1/1/c1/1 | dot1q | BNG Peer | IS-IS/LDP/iBGP |
| 1/1/c2/1 | qinq | OLT | Subscriber access + SRRP |
| 1/1/c3/1 | dot1q | LIG | Lawful Interception |
| 1/1/c4/1 | hybrid | DNS64 | DNS64 for NAT64 |
| 1/1/c5/1 | dot1q | Carrier 1 | eBGP upstream |
| 1/1/c6/1 | dot1q | Carrier 2 | eBGP upstream |
