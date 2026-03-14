---
sidebar_position: 1
---

# Requirements

## Recommended Hardware

| Resource | Minimum | Recommended |
|---------|--------|-------------|
| RAM | 24 GB | 32 GB |
| CPU | 4 cores | 8 cores |

## Observed lab footprint

Real measurement taken with the current lab topology fully started:

- Validation host: `20 vCPU`, `19 GiB RAM`, `5 GiB swap`
- Host RAM in use after boot: `17 GiB`
- Remaining available RAM: `1.8 GiB`
- Swap in use: `1.1 GiB`
- Memory visible in `docker stats`: `~10 GiB`
- Note: that `~10 GiB` is an undercount because some Nokia containers do not report memory correctly in `docker stats`, so actual host usage was significantly higher

Practical conclusion:

- `24 GiB` is a reasonable minimum to boot the full lab
- `32 GiB` remains the recommended target for comfortable operation, ATP execution, and observability add-ons
- Below `24 GiB`, the lab may still boot in some environments, but it becomes a low-headroom scenario with swap usage and a higher chance of degradation


## Required Software

| Software | Minimum Version |
|----------|----------------|
| Docker | 24.0+ |
| Containerlab | 0.50+ |
| Python | 3.10+ (for scripts) |

## Docker Images

| Image | Reference |
|--------|-----------|
| Nokia SRSIM | ghcr.io/abelperezr/srsim:25.10.r2 |
| Nokia SR Linux | ghcr.io/nokia/srlinux:25.10 |
| Dual-Stack ONT | ghcr.io/abelperezr/ont-ds:0.3 or later |
| containerbot | ghcr.io/abelperezr/containerbot:0.0.1 |
| Network Multitool | ghcr.io/srl-labs/network-multitool |
| Prometheus | prom/prometheus |
| Grafana | grafana/grafana:10.3.5 |
| gNMIC | ghcr.io/openconfig/gnmic:latest |

## Nokia license

A valid Nokia SRSIM license is required. This license must be obtained through a Nokia representative and placed locally at `configs/license/SR_SIM_license.txt`. The repository does not distribute that license file.
