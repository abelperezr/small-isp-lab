---
sidebar_position: 1
---

# Requisitos

## Hardware Recomendado

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| RAM | 24 GB | 32 GB |
| CPU | 4 cores | 8 cores |

## Consumo observado del laboratorio

Medición real tomada con la topología levantada y el stack actual del laboratorio:

- Host usado para la validación: `20 vCPU`, `19 GiB RAM`, `5 GiB swap`
- RAM usada en el host después del arranque: `17 GiB`
- RAM disponible restante: `1.8 GiB`
- Swap en uso: `1.1 GiB`
- Consumo visible por `docker stats`: `~10 GiB`
- Nota: ese `~10 GiB` está subcontado, porque algunos contenedores Nokia no reportan memoria correctamente en `docker stats`, y por eso el uso real del host fue bastante más alto

Conclusión práctica:

- `24 GiB` funciona como mínimo razonable para levantar el lab completo
- `32 GiB` sigue siendo la recomendación para operar con margen, ejecutar ATPs y añadir observabilidad sin quedar tan justo de memoria
- Con menos de `24 GiB`, el lab puede arrancar en algunos entornos, pero ya entra en zona de poco margen, uso de swap y mayor probabilidad de degradación


## Software Requerido

| Software | Versión Mínima |
|----------|----------------|
| Docker | 24.0+ |
| Containerlab | 0.50+ |
| Python | 3.10+ (para scripts) |

## Imágenes Docker

| Imagen | Referencia |
|--------|-----------|
| Nokia SRSIM | localhost/nokia/srsim:25.10.R2 |
| Nokia SR Linux | ghcr.io/nokia/srlinux:25.10 |
| ONT Dual-Stack | ghcr.io/abelperezr/ont-ds:0.3 o superior |
| Containerbot | ghcr.io/abelperezr/containerbot:0.0.1 |
| Network Multitool | ghcr.io/srl-labs/network-multitool |
| Prometheus | prom/prometheus |
| Grafana | grafana/grafana:10.3.5 |
| gNMIC | ghcr.io/openconfig/gnmic:latest |

## Licencia Nokia

Se requiere una licencia válida para Nokia SRSIM. Esta licencia debe ser obtenida a través de un representante de Nokia y colocada localmente en `configs/license/SR_SIM_license.txt`. El repositorio no distribuye dicha licencia.
