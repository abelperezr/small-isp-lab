---
sidebar_position: 2.1
sidebar_label: 2. Validación base de Carriers
---

# 2. Validación Base de Carriers

## Objetivo

Validar el estado base de los carriers (`carrier1` y `carrier2`) antes de ejecutar pruebas avanzadas de SRRP/BGP y servicios.

## Alcance

- Estado operativo de interfaces y subinterfaces.
- Tabla de ruteo IPv4/IPv6.
- Vecinos y resumen BGP.

## 2.1 Verificación de interfaces

Comandos:

- `show interface all`
- `show interface ethernet-1/1 detail`

Ejemplo:

```text
A:admin@carrier1# show interface all
ethernet-1/1 is up
  ethernet-1/1.0 is up
    IPv4 addr : 172.16.1.1/31
    IPv6 addr : 2001:db8:f1::1/126
ethernet-1/2 is up
  ethernet-1/2.0 is up
    IPv4 addr : 172.16.1.3/31
    IPv6 addr : 2001:db8:f1::5/126
ethernet-1/3 is up
  ethernet-1/3.0 is up
    IPv4 addr : 10.99.100.1/30
    IPv6 addr : fd00:a1::1/126
```

Resultado esperado:

- `ethernet-1/1`, `ethernet-1/2`, `ethernet-1/3` en `up`.
- Subinterfaces `.0` en `up`.
- Direccionamiento L3 presente según diseño.

## 2.2 Verificación de tabla de rutas

Comandos:

- `show network-instance route-table ipv4-unicast summary`
- `show network-instance route-table ipv6-unicast summary`

Resultado esperado:

- Rutas `static` de salida (`0.0.0.0/0`, `::/0`, half-default) activas.
- Prefijos del ISP (`99.99.99.99/32`, `88.88.88.88/29`, `199.199.199.199/32` y prefijos IPv6) aprendidos por BGP.
- Prefijos conectados locales de enlaces a BNG presentes.

## 2.3 Verificación de BGP

Comandos:

- `show network-instance protocols bgp neighbor`
- `show network-instance protocols bgp summary`

Ejemplo:

```text
A:admin@carrier1# show network-instance protocols bgp neighbor
Peer 172.16.1.0 established
Peer 172.16.1.2 established
```

Resultado esperado:

- 2 vecinos configurados por carrier (hacia BNG MASTER y BNG SLAVE).
- Sesiones en estado `established`.
- AFI/SAFI IPv4 e IPv6 activos.

## 2.4 Checklist final

- `show interface all` sin interfaces críticas down.
- Tabla IPv4/IPv6 con rutas estáticas y BGP activas.
- BGP estable con ambos BNG en cada carrier.
