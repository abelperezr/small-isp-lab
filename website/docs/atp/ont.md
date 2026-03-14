---
sidebar_position: 10
sidebar_label: 10. Pruebas ONT
---

# 10. Pruebas ONT

## 10.0 Validaciones previas

Antes de ejecutar las pruebas desde `ont1` y `pc1`, identificar el prefijo IPv6 delegado actualmente activo en `wan1`.

Opción rápida con `docker exec` desde el host:

```bash
docker exec ont1 sh -lc 'ip -6 addr show dev eth1.150; echo; ip -6 addr show dev eth2'
docker exec pc1 sh -lc 'ip -6 addr show dev eth1; echo; ip -6 route show dev eth1'
```

Qué validar:

- `eth1.150` en `ont1` tiene una dirección WAN IPv6 `/128`
- `eth2` en `ont1` tiene una dirección LAN del prefijo delegado actual, por ejemplo `2001:db8:200:3::1/64`
- `pc1` debe recibir ese mismo prefijo en `eth1`

Importante:

- no asumir que el prefijo delegado siempre será `2001:db8:200:1::/64`
- después de una reconexión o cambio de lease, `pc1` puede conservar temporalmente un prefijo anterior además del actual
- si `pc1` muestra más de un prefijo global en `eth1`, usar como referencia el prefijo que esté configurado actualmente en `ont1` sobre `eth2`

## Conectividad desde ONT1

Gracias a que la imagen ONT tiene PBR (Policy Based Routing), es posible hacer ping a cada uno de los DHCP gateways correspondientes a sus servicios:

### Ping IPv4 CGNAT Gateway (Dual-Stack WAN2)

Opción con `docker exec` desde el host:

```bash
docker exec ont1 ping -c 4 100.80.0.1
```

```text
user@ont1  ~  ping 100.80.0.1
PING 100.80.0.1 (100.80.0.1) 56(84) bytes of data.
64 bytes from 100.80.0.1: icmp_seq=1 ttl=64 time=2.14 ms
64 bytes from 100.80.0.1: icmp_seq=2 ttl=64 time=1.62 ms
64 bytes from 100.80.0.1: icmp_seq=3 ttl=64 time=1.81 ms
64 bytes from 100.80.0.1: icmp_seq=4 ttl=64 time=1.43 ms
^C
--- 100.80.0.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss
```

### Ping IPv4 VIP Gateway (WAN3)

Opción con `docker exec` desde el host:

```bash
docker exec ont1 ping -c 4 192.168.5.1
```

```text
user@ont1  ~  ping 192.168.5.1
PING 192.168.5.1 (192.168.5.1) 56(84) bytes of data.
64 bytes from 192.168.5.1: icmp_seq=1 ttl=64 time=2.33 ms
64 bytes from 192.168.5.1: icmp_seq=2 ttl=64 time=1.81 ms
^C
--- 192.168.5.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss
```

### Ping IPv6 WAN (IPv6-only WAN1)

Opción con `docker exec` desde el host:

```bash
docker exec ont1 ip -6 -o addr show dev eth1.150 scope global
docker exec ont1 ping -6 -c 4 -I <WAN1_IPV6_ACTUAL> 2001:db8:aaaa::2
```

Resultado esperado:

- `ont1` alcanza `2001:db8:aaaa::2` usando como origen la IPv6 WAN actual de `eth1.150`

## 10.1 Verificar Prefix Delegation en PC1

En PC1 se puede observar el prefijo delegado asignado vía DHCPv6-PD.

Opción con `docker exec` desde el host:

```bash
docker exec ont1 ip -6 addr show dev eth2
docker exec pc1 ip -6 addr show dev eth1
```

Qué validar:

- `ont1` anuncia por `eth2` el gateway LAN del prefijo delegado vigente, por ejemplo `2001:db8:200:3::1/64`
- `pc1` recibe una dirección global dentro de ese mismo prefijo en `eth1`

Ejemplo:

- si `ont1` muestra `2001:db8:200:3::1/64` en `eth2`
- entonces `pc1` debe mostrar una dirección tipo `2001:db8:200:3:xxxx:xxxx:xxxx:xxxx/64`

Este prefijo es enrutado hacia `ont1` por el BNG, y `ont1` lo anuncia vía Router Advertisement hacia `pc1` en la LAN.

Nota:

- si `pc1` conserva un prefijo global anterior además del actual, no es necesariamente una falla del servicio
- puede ser un prefijo stale retenido temporalmente por RA
- en ese caso, usar el prefijo actual configurado en `ont1` como referencia para la prueba de alcanzabilidad
- si se requiere una validación limpia, reiniciar `pc1` antes de continuar:

```bash
docker restart pc1
```

## 10.2 Verificar Alcanzabilidad desde PC1

Una vez identificado el prefijo delegado vigente en `ont1`, `pc1` debe poder alcanzar:

- el gateway IPv6 actual de la LAN en `ont1`
- el DNS interno del laboratorio

Nota operativa:

- después de un redeploy, reinicio o reconexión, `pc1` puede tardar unos segundos en quedar listo con RA/PD
- si una prueba IPv6 devuelve `network unreachable`, normalmente significa que `pc1` todavía no tiene instalada una ruta por defecto utilizable o aún no recibió por completo la conectividad IPv6 en la LAN
- antes de concluir que hay una falla, volver a validar:

```bash
docker exec pc1 sh -lc 'ip -6 addr show dev eth1'
docker exec pc1 sh -lc 'ip -6 route'
docker exec pc1 sh -lc 'ping -6 -c 4 2001:db8:aaaa::2'
```

- si después de eso `pc1` ya alcanza `2001:db8:aaaa::2`, repetir la prueba original

### Gateway IPv6 de la LAN

Opción con `docker exec` desde el host:

```bash
docker exec ont1 ip -6 -o addr show dev eth2 scope global
docker exec pc1 ping -6 -c 4 <LAN_GW_ACTUAL_EN_ONT1>
```

Ejemplo:

```bash
docker exec pc1 ping -6 -c 4 2001:db8:200:3::1
```

Resultado esperado:

- `pc1` alcanza el gateway LAN IPv6 vigente de `ont1`

### DNS interno del laboratorio

Opción con `docker exec` desde el host:

```bash
docker exec pc1 ping -6 -c 4 2001:db8:aaaa::2
```

```text
[*]─[pc1]─[~]
└──> ping -6 2001:db8:aaaa::2
PING 2001:db8:aaaa::2(2001:db8:aaaa::2) 56 data bytes
64 bytes from 2001:db8:aaaa::2: icmp_seq=1 ttl=61 time=28.1 ms
64 bytes from 2001:db8:aaaa::2: icmp_seq=2 ttl=61 time=1.18 ms
64 bytes from 2001:db8:aaaa::2: icmp_seq=3 ttl=61 time=1.42 ms
64 bytes from 2001:db8:aaaa::2: icmp_seq=4 ttl=61 time=3.30 ms

--- 2001:db8:aaaa::2 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss
```

Resultado esperado:

- `ont1` tiene una WAN IPv6 activa en `eth1.150`
- `ont1` tiene un gateway LAN IPv6 activo en `eth2` derivado del prefijo delegado vigente
- `pc1` recibe el prefijo delegado vigente en `eth1`
- `pc1` alcanza el gateway actual de `ont1` en la LAN
- PC1 alcanza el DNS interno del laboratorio en `2001:db8:aaaa::2`

Observación operativa:

- si `pc1` muestra más de un prefijo IPv6 global, la validación debe hacerse contra el prefijo actualmente presente en `ont1`
- un prefijo anterior visible en `pc1` puede persistir durante un tiempo por el lifetime del RA previo y no implica necesariamente una falla del BNG o de la ONT
