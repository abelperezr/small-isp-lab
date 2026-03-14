---
sidebar_position: 8
sidebar_label: 9. NAT64
---

# 9. NAT64 - Pruebas

## 9.1 Resolución DNS64 explícita

Desde `ont1`, consultar el DNS64 del laboratorio para un nombre que solo tenga registro `A`:

```bash
docker exec ont1 sh -lc 'nslookup ipv4.google.com 2001:db8:aaaa::2'
```

Salida validada:

```text
Server:		2001:db8:aaaa::2
Address:	2001:db8:aaaa::2#53

Non-authoritative answer:
ipv4.google.com	canonical name = ipv4.l.google.com.
Name:	ipv4.l.google.com
Address: 172.217.28.110
Name:	ipv4.l.google.com
Address: 64:ff9b::acd9:1c6e
```

Resultado esperado:

- el DNS64 devuelve el registro `A` original
- también devuelve un `AAAA` sintetizado dentro de `64:ff9b::/96`

:::tip[Validación desde PC1]
`pc1` puede consultar explícitamente el DNS64 del laboratorio aunque su resolvedor por defecto no use DNS64:

Antes de ejecutar `dig`, confirmar que `pc1` ya recibió IPv6 global por PD y una ruta por defecto válida:

```bash
docker exec pc1 sh -lc 'ip -6 addr show dev eth1'
docker exec pc1 sh -lc 'ip -6 route'
docker exec pc1 sh -lc 'ping -6 -c 4 2001:db8:aaaa::2'
```

Si `dig` devuelve `network unreachable`, normalmente significa que `pc1` todavía no tiene lista la conectividad IPv6 en la LAN detrás de `ont1`. En ese caso, esperar unos segundos a que termine RA/PD y repetir la prueba.

Luego ejecutar:

```bash
docker exec pc1 sh -lc 'dig @2001:db8:aaaa::2 ipv4.google.com AAAA +short'
```

Resultado esperado:

- aparece una respuesta similar a `64:ff9b::acd9:1c6e`
- si antes apareció `network unreachable`, repetir la prueba solo después de confirmar conectividad IPv6 hacia `2001:db8:aaaa::2`
:::

## 9.2 Prueba de Ping NAT64

Desde ONT1 (que tiene IPv6-only en WAN1), hacer ping al prefijo NAT64:

```text
user@ont1  ~  ping -6 64:ff9b::808:808
PING 64:ff9b::808:808(64:ff9b::808:808) 56 data bytes
64 bytes from 64:ff9b::808:808: icmp_seq=1 ttl=103 time=31.3 ms
64 bytes from 64:ff9b::808:808: icmp_seq=2 ttl=103 time=15.3 ms
64 bytes from 64:ff9b::808:808: icmp_seq=3 ttl=103 time=14.3 ms
64 bytes from 64:ff9b::808:808: icmp_seq=4 ttl=103 time=12.1 ms
64 bytes from 64:ff9b::808:808: icmp_seq=5 ttl=103 time=19.6 ms
^C
--- 64:ff9b::808:808 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 3996ms
```

La dirección `64:ff9b::808:808` es la representación NAT64 de `8.8.8.8` (Google DNS).

También se validó un flujo DNS64 + ICMP usando el nombre:

```bash
docker exec ont1 sh -lc 'ping -6 -c 4 ipv4.google.com'
```

Salida validada:

```text
PING ipv4.google.com(pnboga-ac-in-f14.1e100.net (64:ff9b::acd9:1c6e)) 56 data bytes
64 bytes from gru06s09-in-f110.1e100.net (64:ff9b::acd9:1c6e): icmp_seq=1 ttl=112 time=18.3 ms
64 bytes from pnboga-ac-in-f14.1e100.net (64:ff9b::acd9:1c6e): icmp_seq=2 ttl=112 time=22.8 ms
64 bytes from pnboga-ac-in-f14.1e100.net (64:ff9b::acd9:1c6e): icmp_seq=3 ttl=112 time=24.9 ms
64 bytes from pnboga-ac-in-f14.1e100.net (64:ff9b::acd9:1c6e): icmp_seq=4 ttl=112 time=18.9 ms
```

Resultado esperado:

- el nombre resuelve a un `AAAA` sintetizado
- el ping IPv6 funciona sobre NAT64

## 9.3 Prueba HTTP sobre NAT64

Desde `ont1`, validar tráfico de aplicación real:

```bash
docker exec ont1 sh -lc 'curl -6 -I --max-time 15 http://example.com'
```

Salida validada:

```text
HTTP/1.1 200 OK
Date: Wed, 11 Mar 2026 14:44:56 GMT
Content-Type: text/html
Connection: keep-alive
Last-Modified: Thu, 05 Mar 2026 11:55:05 GMT
Accept-Ranges: bytes
Server: cloudflare
```

Resultado esperado:

- `curl` devuelve `HTTP/1.1 200 OK`
- queda demostrado que NAT64 no solo funciona para ICMP, sino también para tráfico HTTP

## 9.4 Validación desde PC1 detrás de ONT1

`pc1` recibe conectividad IPv6 vía Prefix Delegation detrás de `ont1`. Aunque su DNS por defecto puede no usar el DNS64 del laboratorio, se validó:

1. conectividad hacia el DNS64 del lab
2. resolución DNS64 explícita
3. alcance IPv6 a un destino NAT64 conocido

Comandos:

```bash
docker exec pc1 sh -lc 'ping -6 -c 4 2001:db8:aaaa::2'
docker exec pc1 sh -lc 'dig @2001:db8:aaaa::2 ipv4.google.com AAAA +short'
docker exec pc1 sh -lc 'ping -6 -c 4 64:ff9b::808:808'
```

Resultado esperado:

- `pc1` alcanza el DNS64 `2001:db8:aaaa::2`
- la consulta `dig` devuelve un `AAAA` sintetizado
- el ping al prefijo NAT64 funciona desde la LAN detrás de `ont1`

## 9.5 Verificar Sesiones NAT64

Desde BNG MASTER, buscar la sesión NAT64:

```text
tools dump nat sessions
```

Buscar una entrada similar a:

```text
-------------------------------------------------------------------------------
Owner               : NAT64-Sub@2001:db8:cccc::1
Router              : 9998
Policy              : nat64-pol
FlowType            : ICMP              Timeout (sec)       : 4
Inside IP Addr      : 2001:db8:cccc::1
Inside Identifier   : 480
Outside IP Addr     : 199.199.199.199
Outside Identifier  : 1118
Foreign IP Addr     : 8.8.8.8
Nat Group           : 1
Nat Group Member    : 1
-------------------------------------------------------------------------------
```

:::info[Componentes NAT64]

- **Prefijo NAT64**: `64:ff9b::/96`
- **Pool Outside**: `199.199.199.199` (nat64-pool en VPRN 9999)
- **DNS64**: Servidor BIND en `2001:db8:aaaa::2` que sintetiza registros AAAA
- **Filtro IPv6**: Filter entry 10 redirige tráfico hacia `64:ff9b::/96` al motor NAT64
:::

## 9.6 Verificar Port-Blocks NAT64

Desde ONT1 u ONT2, ejecutar:

```text
ping -6 ipv4.tlund.se
```

Opción con `docker exec` desde el host:

```bash
docker exec ont1 ping -6 -c 4 ipv4.tlund.se
docker exec ont2 ping -6 -c 4 ipv4.tlund.se
```

Luego, en el BNG MASTER o en el SLAVE, ejecutar:

```text
pyexec "cf3:\scripts\nat64_portblocks.py"
```

La salida debe mostrar una entrada `NAT64` para el suscriptor IPv6-only, similar a esta:

```text
[/]
A:admin@MASTER# pyexec "cf3:\scripts\nat64_portblocks.py"
======================================================================
NAT Subscriber Port-Block Report v3
======================================================================

[NAT64] Querying...
  Found 1 subscriber(s)
  Entries: 1

[NAT44] Querying...
  Found 16 subscriber(s)
  Entries: 16

========================================================================================================================
TYPE   SUBSCRIBER                       INSIDE PREFIX          OUTSIDE IP         START   END     PORTS   POLICY     SESS
------------------------------------------------------------------------------------------------------------------------
NAT64  [NAT64-Sub@2001:db8:cccc::]      2001:db8:cccc::/64     199.199.199.199    1024    1223    200     nat64-pol  1/1
NAT44  [LSN-Host@100.80.0.5]            100.80.0.5/32          99.99.99.99        1344    1407    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.6]            100.80.0.6/32          99.99.99.99        1408    1471    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.7]            100.80.0.7/32          99.99.99.99        1472    1535    64      natpol     0/0
NAT44  [LSN-Host@192.168.5.0]           192.168.5.0/32         88.88.88.88        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.1]           192.168.5.1/32         88.88.88.89        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.2]           192.168.5.2/32         88.88.88.90        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.3]           192.168.5.3/32         88.88.88.91        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.4]           192.168.5.4/32         88.88.88.92        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.5]           192.168.5.5/32         88.88.88.93        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.6]           192.168.5.6/32         88.88.88.94        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.7]           192.168.5.7/32         88.88.88.95        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@100.80.0.0]            100.80.0.0/32          99.99.99.99        1024    1087    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.1]            100.80.0.1/32          99.99.99.99        1088    1151    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.2]            100.80.0.2/32          99.99.99.99        1152    1215    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.3]            100.80.0.3/32          99.99.99.99        1216    1279    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.4]            100.80.0.4/32          99.99.99.99        1280    1343    64      natpol     0/0
========================================================================================================================

Summary: 1 NAT64, 8 CGNAT, 8 VIP, 17 total

CSV written to: cf3:\scripts\nat_report.csv

DONE
```

Validar que la fila `NAT64` aparezca con el prefijo interno del suscriptor, la IP outside `199.199.199.199` y la política `nat64-pol`.

Durante la validación real del laboratorio se observaron estas dos entradas NAT64:

```text
NAT64  [NAT64-Sub@2001:db8:cccc::]      2001:db8:cccc::/64     199.199.199.199    1224    1423    200     nat64-pol  1/2
NAT64  [NAT64-Sub@2001:db8:200:1::]     2001:db8:200:1::/64    199.199.199.199    1424    1623    200     nat64-pol  2/2
```

Esto confirma:

- una entrada NAT64 para el prefijo IPv6-only de `ont1`
- una entrada NAT64 para el prefijo delegado visto detrás de `pc1`
- misma IP outside `199.199.199.199`
- política `nat64-pol` aplicada correctamente
