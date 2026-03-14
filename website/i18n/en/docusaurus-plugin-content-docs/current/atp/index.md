---
sidebar_position: 1
---

# ATP - Acceptance Test Plan

## Description

The **ATP (Acceptance Test Plan)** documents the acceptance tests of the Small ISP laboratory. Each section describes the steps to follow, the commands to execute, and the expected results to validate the correct functioning of each subsystem.

## ATP Sections

| # | Section | Description |
|---|---------|-------------|
| 1 | [BNG baseline validation](bng-baseline.md) | General SROS, ISIS, and MPLS/LDP validation on the BNGs |
| 2 | [Carrier baseline validation](carriers-baseline.md) | Interface, route-table, and BGP baseline validation on Carrier 1 and Carrier 2 |
| 3 | [OLT baseline validation](olt-baseline.md) | Validation of bridged subinterfaces, MAC-VRF associations, and MAC learning |
| 4 | [L2/L3 services](services-l2-l3.md) | Validation of VPLS, VPRN, SAPs, SDPs, and BGP inside VPRN 9999 |
| 5 | [QoS](qos.md) | Validation of SAP QoS policies and SLA profiles |
| 6 | [SRRP and BGP](srrp-bgp.md) | SRRP and BGP Traffic Engineering redundancy tests with EHS |
| 7 | [ESM](esm.md) | Subscriber management tests |
| 8 | [CGNAT](cgnat.md) | Validation of NAT groups, pools, LSN sessions, and ISA resources |
| 9 | [NAT64](nat64.md) | NAT64 translation validation from an IPv6-only ONT |
| 10 | [ONT tests](ont.md) | Connectivity validation from ONTs and prefix delegation |
| 11 | [LEA and LI](lea-validation.md) | Validation of lawful interception, traffic generation, and LEA API queries |
| 12 | [Observability](observability.md) | Validation of subscriber traffic in Prometheus and Grafana |
| 13 | [SRRP Subscriber Failover](srrp-subscribers-demo.md) | Demonstration of ONT and LAN service continuity while cutting the OLT link toward the BNG MASTER |
| 14 | [Final Boss](final-boss.md) | Chained SRRP failover, upstream loss, and RADIUS outage test with active ONT and LAN traffic |
