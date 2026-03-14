---
sidebar_position: 1
---

# Stack de Telemetría

## Descripción

El laboratorio incluye un stack completo de métricas y visualización basado en gNMIC → Prometheus → Grafana para monitoreo en tiempo real de los equipos Nokia.

## Arquitectura

```mermaid
graph LR
    BNG1[BNG MASTER] -->|gNMI| GNMIC[gNMIC]
    BNG2[BNG SLAVE] -->|gNMI| GNMIC
    OLT[OLT SR Linux] -->|gNMI| GNMIC
    C1[Carrier 1] -->|gNMI| GNMIC
    C2[Carrier 2] -->|gNMI| GNMIC
    GNMIC -->|Prometheus format| PROM[Prometheus]
    PROM -->|PromQL| GRAF[Grafana]
```

## Acceso

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| Grafana | http://localhost:3030 | admin/admin |
| Prometheus | http://localhost:9090 | N/A |

## Dashboards Incluidos

- **SROS Dashboard**: Métricas de los BNGs Nokia (interfaces, sesiones, NAT)
- **Small ISP SR Linux Edge**: Métricas de OLT, Carrier 1 y Carrier 2
- **Nokia Syslog Overview**: Visualización de logs centralizados con Alloy + Loki dentro de Grafana
