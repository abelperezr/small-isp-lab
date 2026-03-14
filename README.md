# Small ISP Lab

End-to-end ISP lab built on Containerlab with **Nokia SROS (SRSIM)**, **Nokia SR Linux**, auxiliary Linux containers, and operational documentation in **Docusaurus (ES/EN)**.
Documentation: https://abelperezr.github.io/small-isp-lab/docs/

This project is designed to validate and demonstrate a realistic access and ISP edge environment with:

- active/standby redundancy between BNGs using **SRRP**
- **BGP Traffic Engineering** with **EHS**
- **IPoE** and **PPPoE** subscribers
- **RADIUS** authentication with **LUDB** fallback
- **IPv6-only**, **dual-stack**, and **VIP** service profiles
- **CGNAT**, **NAT64**, and **one-to-one NAT**
- observability with **gNMIc + Prometheus + Grafana**
- **Lawful Interception / LEA**
- operational automation with **Containerbot**

## Main Topology

| Component | Image / platform | Management |
|-----------|------------------|------------|
| BNG MASTER | `localhost/nokia/srsim:25.10.R2` | `10.99.1.2` |
| BNG SLAVE | `localhost/nokia/srsim:25.10.R2` | `10.99.1.3` |
| OLT | `ghcr.io/nokia/srlinux:25.10` | `10.99.1.4` |
| Carrier 1 | `ghcr.io/nokia/srlinux:25.10` | `10.99.1.252` |
| Carrier 2 | `ghcr.io/nokia/srlinux:25.10` | `10.99.1.253` |
| ONT1 | `ghcr.io/abelperezr/ont-ds:0.4` | `10.99.1.5` |
| ONT2 | `ghcr.io/abelperezr/ont-ds:0.4` | `10.99.1.6` |
| RADIUS | `ghcr.io/abelperezr/freeradius-custom:0.1` | `10.99.1.8` |
| gNMIc | `ghcr.io/openconfig/gnmic:latest` | `10.99.1.9` |
| Prometheus | `prom/prometheus` | `10.99.1.10` |
| Grafana | `grafana/grafana:10.3.5` | `10.99.1.11` |
| LIG / LEA | `ghcr.io/srl-labs/network-multitool` + Python | `10.99.1.12` |
| DNS64 | `ghcr.io/srl-labs/network-multitool:latest` | `10.99.1.13` |
| Internet | `ghcr.io/srl-labs/network-multitool` | `10.99.1.14` |
| Loki | `grafana/loki:latest` | `10.99.1.15` |
| Alloy | `grafana/alloy:latest` | `10.99.1.16` |
| Containerbot | `ghcr.io/abelperezr/containerbot:0.0.1` | `10.99.1.200` |

## Main Use Cases

- SRRP failover with role transition and BGP policy changes
- IPoE/PPPoE subscriber suspension and reactivation through Containerbot
- AAA fallback to LUDB
- NAT64 validation from an IPv6-only ONT
- CGNAT and VIP validation
- subscriber throughput observability in Grafana and Prometheus
- lawful interception visibility through the LEA API and dashboard

## Recommended Demos and ATPs

- [ATP 14 - Final Boss](website/docs/atp/final-boss.md)
- [ATP 6 - SRRP and BGP](website/docs/atp/srrp-bgp.md)
- [ATP 7 - ESM / Subscribers](website/docs/atp/esm.md)
- [ATP 9 - NAT64](website/docs/atp/nat64.md)
- [ATP 10 - ONT Tests](website/docs/atp/ont.md)
- [ATP 11 - LEA / Lawful Interception](website/docs/atp/lea-validation.md)
- [ATP 12 - Observability](website/docs/atp/observability.md)
- [Daily Operations Runbook](website/docs/operacion/runbook.md)

## Quick Start

```bash
git clone https://github.com/abelperezr/small-isp-lab.git
cd small-isp-lab
```

Before deploying, place a valid Nokia SRSIM license in the `configs` tree. The default SRSIM image expected by `lab.yml` is `localhost/nokia/srsim:25.10.R2`.

```bash
mkdir -p configs/license
cp /path/to/SR_SIM_license.txt configs/license/SR_SIM_license.txt
```

Then deploy the lab:

```bash
sudo containerlab deploy -t lab.yml
sudo containerlab inspect -t lab.yml
```

## Requirements

- Docker `24+`
- Containerlab `0.50+`
- Node.js `20+` for local documentation
- jq and curl for API queries and JSON parsing
- at least `24 GB` of RAM
- recommended: `32 GB` for a more comfortable workflow
- a valid **Nokia SRSIM** license

The license must be placed locally at:

```text
configs/license/SR_SIM_license.txt
```

That file is not distributed in the repository.

## Useful Access

| Service | URL / Port | Credentials |
|---------|------------|-------------|
| Grafana | `http://localhost:3030` | `admin/admin` |
| Prometheus | `http://localhost:9090` | `N/A` |
| Loki API | `http://localhost:3101` | `N/A` |
| Alloy UI | `http://localhost:12345` | `N/A` |
| LEA / LIG | `http://localhost:8092` | `admin/multit00l` |
| ONT1 Web GUI | `http://localhost:8090` | `N/A` |
| ONT2 Web GUI | `http://localhost:8091` | `N/A` |
| ONT1 | `docker exec -it ont1 bash` | `user/test` |
| ONT2 | `docker exec -it ont2 bash` | `user/test` |
| BNG MASTER SSH | `ssh -p 56612 admin@localhost` | `admin/lab123` |
| BNG SLAVE SSH | `ssh -p 56613 admin@localhost` | `admin/lab123` |
| OLT SSH | `ssh -p 56614 admin@localhost` | `admin/lab123` |
| Carrier 1 SSH | `ssh -p 56610 admin@localhost` | `admin/lab123` |
| Carrier 2 SSH | `ssh -p 56611 admin@localhost` | `admin/lab123` |
| Radius | `ssh -p 56617 admin@localhost` | `admin/admin` |
| PC1 | `docker exec -it pc1 bash` | `admin/multit00l` |
| Internet | `ssh -p 56620 admin@localhost` | `admin/multit00l` |
| DNS | `ssh -p 56621 admin@localhost` | `admin/multit00l` |
| GNMIC | `docker exec -it gnmic /bin/sh` | `N/A` |
| RADIUS | `ssh -p 56617 admin@localhost` | `admin/admin` |

## Documentation

The `website/` documentation covers:

- deployment and installation
- topology and authentication flow
- per-device MOPTs
- day-to-day operations
- Containerbot
- RADIUS / AAA
- LEA Console
- the full ATP suite

To view it locally:

```bash
cd website
npm install
npm run start
```

URL:

```text
http://localhost:3000/small-isp-lab/docs/
```

## Repository Layout

- `lab.yml`: main Containerlab topology
- `configs/`: configurations, dashboards, scripts, and auxiliary services
- `containerbot/`: bot image source and runtime assets
- `radius-custom/`: Dockerfile for the custom FreeRADIUS image
- `website/`: Docusaurus documentation in Spanish and English

## Operational Notes

- `configs/cbot/secrets.env` is local-only and should not be committed; use `configs/cbot/secrets.env.example` as the template
- `lab.yml.annotations.json` may be kept locally if you want to preserve visual annotations for the lab
- Enjoy!

## License

This project is distributed under a BSD 3-Clause style license. See [LICENSE](LICENSE).
