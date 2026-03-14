---
sidebar_position: 2
---

# gNMIC

## Descripción

gNMIC es el colector de telemetría que se suscribe a los equipos via gNMI y exporta las métricas en formato Prometheus.

## Configuración

El archivo `configs/gnmic/config.yml` define los targets y las subscripciones gNMI hacia los equipos Nokia.

## IP y Puerto

| Parámetro | Valor |
|-----------|-------|
| IP de Gestión | 10.99.1.9 |
| Imagen | ghcr.io/openconfig/gnmic:latest |
