---
sidebar_position: 1
---

# Small ISP with Containerlab

<div className="cardGrid">
  <div className="docCard">
    <h3>Small ISP - SRRP Redundancy</h3>
    <p>ISP laboratory with SRRP redundancy between BNG MASTER and SLAVE, with dynamic BGP Traffic Engineering via EHS</p>
  </div>
  <div className="docCard">
    <h3>Nokia SROS + SR Linux</h3>
    <p>Integration of Nokia 7750 SR-7 (BNG), SR Linux (OLT, Carriers) and Linux containers in a single lab</p>
  </div>
  <div className="docCard">
    <h3>Telemetry Stack</h3>
    <p>Metrics and logs with gNMIC, Prometheus, Grafana, Alloy, and Loki</p>
  </div>
  <div className="docCard">
    <h3>RADIUS Authentication + LUDB Fallback</h3>
    <p>Subscriber authentication with FreeRADIUS and fallback to Local User Database</p>
  </div>
  <div className="docCard">
    <h3>NAT64 + CGNAT + One-to-One</h3>
    <p>Three NAT profiles: NAT64 for IPv6-only, deterministic CGNAT for dual-stack, and One-to-One for VIP</p>
  </div>
  <div className="docCard">
    <h3>Lawful Interception + LEA Console</h3>
    <p>Legal interception with mirror destination ip-udp-shim and web console for real-time viewing</p>
  </div>
</div>

## General Description

This lab implements a complete **Small ISP** using **Containerlab** as a virtualization platform. The architecture includes active/backup redundancy between two Nokia 7750 SR-7 BNGs with SRRP (Subscriber Routed Redundancy Protocol) and dynamic BGP Traffic Engineering controlled by EHS (Event Handling System).

### Main Components

| Component | Model/Image | IP Management | Function |
|------------|---------------|------------|---------|
| **BNG MASTER** | Nokia 7750 SR-7 (SRSIM) | 10.99.1.2 | Primary BNG with SRRP priority 200 |
| **BNG SLAVE** | Nokia 7750 SR-7 (SRSIM) | 10.99.1.3 | Secondary BNG with SRRP priority 50 |
| **OLT** | Nokia SR Linux 25.10 | 10.99.1.4 | Optical line terminal (MAC-VRF) |
| **Carrier 1** | Nokia SR Linux 25.10 | 10.99.1.252 | Upstream carrier router (AS 65501) |
| **Carrier 2** | Nokia SR Linux 25.10 | 10.99.1.253 | Upstream carrier router (AS 65502) |
| **ONT1** | ont-ds:0.3 or later (IPoE) | 10.99.1.5 | Optical terminal - 3 WANs (IPv6, Dual, VIP) |
| **ONT2** | ont-ds:0.3 or later (PPPoE) | 10.99.1.6 | Optical terminal - 1 WAN PPPoE IPv6 |
| **RADIUS** | FreeRADIUS | 10.99.1.8 | Authentication server |
| **gNMIC** | OpenConfig gNMIC | 10.99.1.9 | Telemetry collector |
| **Prometheus** | Prometheus | 10.99.1.10 | Metrics Database |
| **Grafana** | Grafana 10.3.5 | 10.99.1.11 | Viewing metrics |
| **LIG** | network-multitool + Python | 10.99.1.12 | Lawful Interception Gateway |
| **DNS64** | BIND9 | 10.99.1.13 | DNS64 Server for NAT64 |
| **Internet** | network-multitool | 10.99.1.14 | Internet simulator |
| **Loki** | grafana/loki:latest | 10.99.1.15 | Log storage and indexing |
| **Alloy** | grafana/alloy:latest | 10.99.1.16 | Syslog collector and label normalization |
| **Containerbot** | ghcr.io/abelperezr/containerbot:0.0.1 | 10.99.1.200 | Telegram automation bot |

### Technical Features

:::info[Implemented Technologies]

- **SRRP (Subscriber Routed Redundancy Protocol)**: Active/backup redundancy between BNGs
- **EHS (Event Handling System)**: pySROS scripts for dynamic adjustment of BGP policies according to SRRP status
- **BGP Traffic Engineering**: AS-Path Prepend differentiated by carrier and SRRP role
- **Multi-Chassis Redundancy**: Synchronization of DHCP/SRRP/ESM sessions between BNGs
- **ESM (Enhanced Subscriber Management)**: Three Group Interfaces: ipv6-only, dual-stack, vip
- **NAT64**: IPv6→IPv4 translation with prefix 64:ff9b::/96
- **CGNAT Deterministic**: NAT44 with deterministic mapping 100.80.0.0/29 → 99.99.99.99
- **NAT One-to-One**: Dedicated public IP 88.88.88.88/29 for VIP subscribers
- **Lawful Interception**: Mirror destination with ip-udp-shim to LEA Console
- **IPoE + PPPoE**: Full support for both protocols
- **Dual-Stack IPv4/IPv6**: DHCPv4, DHCPv6 WAN and Prefix Delegation
- **DNS64**: DNS resolution with AAAA record synthesis for NAT64
- **Centralized logs**: syslog pipeline with Alloy + Loki integrated into Grafana
- **Containerbot**: Telegram bot to run testing and monitoring scripts

:::

### Featured demos

These are the most compelling lab demonstrations for a short showcase. Each one has a detailed ATP procedure and is also grouped under [Featured demos](./demos/).

- **Final Boss**: [Final Boss](./atp/final-boss.md)
- **SRRP Subscriber Failover**: [SRRP Subscriber Failover](./atp/srrp-subscribers-demo.md)
- **SRRP failover + BGP through EHS**: [SRRP and BGP - General Tests](./atp/srrp-bgp.md)
- **RADIUS down + LUDB fallback**: [ESM - Subscriber Tests](./atp/esm.md#74-fallback-to-ludb)
- **End-to-end NAT64 from an IPv6-only ONT**: [NAT64 - Tests](./atp/nat64.md)
- **LEA with API and web visibility**: [Lawful Interception and LEA Validation](./atp/lea-validation.md)
- **Observability with real traffic**: [Observability Validation in Grafana and Prometheus](./atp/observability.md)

### Access to the Laboratory

| Service | URL/Port | Credentials |
|---------|----------|-------------|
| Grafana | `http://localhost:3030` | admin/admin |
| Prometheus | `http://localhost:9090` | N/A |
| Loki API | `http://localhost:3101` | N/A |
| Alloy UI | `http://localhost:12345` | N/A |
| LEA/LIG | `http://localhost:8092` | admin/multit00l |
| ONT1 Web GUI | `http://localhost:8090` | N/A |
| ONT2 Web GUI | `http://localhost:8091` | N/A |
| ONT1 | `docker exec -it ont1 bash` | user/test |
| ONT2 | `docker exec -it ont2 bash` | user/test |
| BNG MASTER SSH | `ssh -p 56612 admin@localhost` | admin/lab123 |
| BNG SLAVE SSH | `ssh -p 56613 admin@localhost` | admin/lab123 |
| OLT SSH | `ssh -p 56614 admin@localhost` | admin/lab123 |
| Carrier 1 SSH | `ssh -p 56610 admin@localhost` | admin/lab123 |
| Carrier 2 SSH | `ssh -p 56611 admin@localhost` | admin/lab123 |
| Radius | `ssh -p 56617 admin@localhost` | admin/admin |
| PC1 | `docker exec -it pc1 bash` | admin/multit00l |
| Internet | `ssh -p 56620 admin@localhost` | admin/multit00l |
| DNS | `ssh -p 56621 admin@localhost` | admin/multit00l |
| GNMIC | `docker exec -it gnmic /bin/sh` | N/A |
 
## Quick Start

```bash
# Clone the repository
git clone https://github.com/abelperezr/small-isp-lab.git
cd small-isp-lab

# Deploy the lab
sudo containerlab deploy -t lab.yml

# Verify node status
sudo containerlab inspect -t lab.yml

# Access Grafana
firefox http://localhost:3030

# Access LEA Console
firefox http://localhost:8092
```

:::warning[Prerequisites]

- Docker installed and working
- Containerlab v0.50+ installed
- Nokia SRSIM 25.10.R2 image available
- Nokia SR Linux 25.10 image available
- ONT-DS 0.3 or later image available
- Containerbot 0.0.1 image available
- At least 24 GB of RAM
- Recommended: 32 GB for more operational headroom
- Nokia license valid for SRSIM
:::
