---
sidebar_position: 2
---

# gNMIC

## Description

gNMIC is the telemetry collector that subscribes to devices via gNMI and exports the metrics in Prometheus format.

## Configuration

The `configs/gnmic/config.yml` file defines the gNMI targets and subscriptions to Nokia devices.

## IP and Port

| Parameter | Value |
|-----------|-------|
| Management IP | 10.99.1.9 |
| Image | ghcr.io/openconfig/gnmic:latest |
