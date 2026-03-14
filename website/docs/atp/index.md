---
sidebar_position: 1
---

# ATP - Acceptance Test Plan

## Descripción

El **ATP (Acceptance Test Plan)** documenta las pruebas de aceptación del laboratorio Small ISP. Cada sección describe los pasos a seguir, los comandos a ejecutar, y los resultados esperados para validar el correcto funcionamiento de cada subsistema.

## Secciones del ATP

| # | Sección | Descripción |
|---|---------|-------------|
| 1 | [Validación base de BNG](bng-baseline.md) | Validaciones generales de SROS, ISIS y MPLS/LDP en los BNG |
| 2 | [Validación base de Carriers](carriers-baseline.md) | Validación de interfaces, rutas y sesiones BGP en Carrier 1 y Carrier 2 |
| 3 | [Validación base de OLT](olt-baseline.md) | Validación de subinterfaces bridged, asociaciones MAC-VRF y aprendizaje MAC |
| 4 | [Servicios L2/L3](services-l2-l3.md) | Validación de servicios VPLS, VPRN, SAPs, SDPs y BGP dentro de VPRN 9999 |
| 5 | [QoS](qos.md) | Validación de políticas QoS en SAPs y perfiles SLA |
| 6 | [SRRP y BGP](srrp-bgp.md) | Pruebas de redundancia SRRP y BGP Traffic Engineering con EHS |
| 7 | [ESM](esm.md) | Pruebas de gestión de suscriptores |
| 8 | [CGNAT](cgnat.md) | Validación de grupos NAT, pools, sesiones LSN y recursos ISA |
| 9 | [NAT64](nat64.md) | Validación de traducción NAT64 desde ONT IPv6-only |
| 10 | [Pruebas ONT](ont.md) | Validación de conectividad desde ONTs y prefix delegation |
| 11 | [LEA y LI](lea-validation.md) | Validación de interceptación legal, generación de tráfico y consultas API del LEA |
| 12 | [Observabilidad](observability.md) | Validación de tráfico de suscriptores en Prometheus y Grafana |
| 13 | [Failover Suscriptores SRRP](srrp-subscribers-demo.md) | Demostración de continuidad de servicio de ONTs y LAN al cortar el enlace OLT hacia el BNG MASTER |
| 14 | [Final Boss](final-boss.md) | Prueba encadenada de failover SRRP, pérdida de upstream y caída de RADIUS con tráfico activo en ONTs y LAN |
