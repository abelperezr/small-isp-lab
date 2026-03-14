---
sidebar_position: 1
---

# Demos destacadas

Esta sección reúne las demostraciones más atractivas del laboratorio para sesiones cortas de 5 a 10 minutos. Cada demo enlaza al ATP correspondiente, donde se encuentra el procedimiento detallado paso a paso.

## 1. Final Boss

**Qué demuestra:** supervivencia del servicio de suscriptores ante una falla compuesta: caída del acceso OLT hacia el BNG MASTER, pérdida de upstream en el BNG activo y baja de RADIUS.

**Duración estimada:** 10-15 minutos

**Procedimiento detallado:** [Final Boss](../atp/final-boss.md)

## 2. Failover Suscriptores SRRP

**Qué demuestra:** continuidad del servicio de ONTs y hosts detrás de Prefix Delegation durante la conmutación SRRP entre BNG MASTER y BNG SLAVE.

**Duración estimada:** 5-10 minutos

**Procedimiento detallado:** [Failover Suscriptores SRRP](../atp/srrp-subscribers-demo.md)

## 3. Failover SRRP + cambio dinámico de export BGP por EHS

**Qué demuestra:** conmutación entre BNG MASTER y BNG SLAVE, reacción del sistema EHS y cambios en políticas/anuncios BGP.

**Duración estimada:** 5-10 minutos

**Procedimiento detallado:** [SRRP y BGP - Pruebas Generales](../atp/srrp-bgp.md)

## 4. Baja de RADIUS con fallback LUDB

**Qué demuestra:** continuidad operativa del servicio de suscriptores aun cuando RADIUS no está disponible.

**Duración estimada:** 5-10 minutos

**Procedimiento detallado:** [ESM - Pruebas de Suscriptores](../atp/esm.md#74-fallback-a-la-ludb)

## 5. NAT64 end-to-end desde ONT IPv6-only

**Qué demuestra:** traducción IPv6 a IPv4 desde un suscriptor IPv6-only hasta recursos IPv4.

**Duración estimada:** 5 minutos

**Procedimiento detallado:** [NAT64 - Pruebas](../atp/nat64.md)

## 6. Interceptación LEA con visibilidad en API y web

**Qué demuestra:** activación de lawful interception, generación de tráfico y observación de eventos desde la consola y la API del LIG.

**Duración estimada:** 5-10 minutos

**Procedimiento detallado:** [Interceptación legal y validación en LEA](../atp/lea-validation.md)

## 7. Observabilidad en Grafana con tráfico real

**Qué demuestra:** generación simultánea de tráfico desde ONT1 y ONT2 y correlación en Prometheus y Grafana.

**Duración estimada:** 5 minutos

**Procedimiento detallado:** [Validación de observabilidad en Grafana y Prometheus](../atp/observability.md)

## Recomendación de uso

Si quieres una demostración ejecutiva o técnica del laboratorio, este es un buen orden:

1. SRRP + BGP
2. Final Boss
3. Failover Suscriptores SRRP
4. RADIUS fallback
5. NAT64
6. LEA
7. Observabilidad
