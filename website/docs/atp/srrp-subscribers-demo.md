---
sidebar_position: 13
sidebar_label: 13. Failover Suscriptores SRRP
---

# 13. Failover Suscriptores SRRP

Esta prueba demuestra continuidad de servicio para suscriptores IPoE y PPPoE cuando se corta el enlace de acceso entre la OLT y el BNG MASTER. El objetivo es verificar que:

- `SLAVE` asume el rol `master` en SRRP para los tres group-interface de suscriptores
- las sesiones siguen visibles en ambos BNG con `Fwd` activo en el nodo que queda reenviando
- `ont1`, `ont2` y la LAN detrás de `ont1` continúan respondiendo tráfico durante el switchover

## 13.1 Prerrequisitos

Validar antes de iniciar:

```text
show srrp
show service active-subscribers
```

Estado base esperado:

- `MASTER`: SRRP `master` para `ipv6-only`, `dual-stack` y `vip`
- `SLAVE`: SRRP `backupShunt`
- `ONT-001` y `ONT-002` visibles en `show service active-subscribers`

## 13.2 Determinar las IP fuente actuales

Atajo opcional:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo start
```

Si usas este helper, puedes saltarte `13.2` y `13.3` y continuar directamente en `13.4`. El script detecta las IP fuente actuales y lanza todos los probes del ATP.

Para una vista de la secuencia de pings durante la prueba, deja una segunda terminal abierta con:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo watch
```

Este modo refresca en vivo la última línea de cada ping y ayuda a ver el hueco de tráfico justo cuando ocurre el failover.

Antes de iniciar los pings, identificar las direcciones vigentes del lab. Estas IP pueden variar entre corridas, por lo que no se recomienda usar valores fijos.

Ejecutar desde el host:

```bash
docker exec ont1 sh -lc "ip -6 addr show dev eth1.150 scope global"
docker exec ont1 sh -lc "ip -6 addr show dev eth3.200 scope global"
docker exec ont1 sh -lc "ip -4 addr show dev eth3.200 scope global"
docker exec ont2 sh -lc "ip -6 addr show dev ppp0 scope global"
```

Tomar estas IP para los siguientes pasos:

- `ONT1_WAN1_V6`: IPv6 global de `eth1.150`
- `ONT1_WAN2_V6`: IPv6 global de `eth3.200`
- `ONT1_WAN2_V4`: IPv4 global de `eth3.200`
- `ONT2_PPP_V6`: IPv6 global de `ppp0`

Ejemplo de una corrida real:

```text
ONT1_WAN1_V6=2001:db8:100::5
ONT1_WAN2_V6=2001:db8:cccc::1
ONT1_WAN2_V4=100.80.0.4
ONT2_PPP_V6=2001:db8:100::4
```

## 13.3 Iniciar pings continuos

Lanzar los probes desde host con `docker exec`:

```bash
docker exec ont1 sh -lc 'rm -f /tmp/srrp_demo_*; nohup ping -D -n -i 0.2 -W 1 -I <ONT1_WAN1_V6> 2001:db8:aaaa::2 > /tmp/srrp_demo_ont1_wan1_v6.log 2>&1 & echo $! > /tmp/srrp_demo_ont1_wan1_v6.pid'
docker exec ont1 sh -lc 'nohup ping -D -n -i 0.2 -W 1 -I <ONT1_WAN2_V6> 2001:db8:aaaa::2 > /tmp/srrp_demo_ont1_wan2_v6.log 2>&1 & echo $! > /tmp/srrp_demo_ont1_wan2_v6.pid'
docker exec ont1 sh -lc 'nohup ping -D -n -i 0.2 -W 1 -I <ONT1_WAN2_V4> 99.99.99.99 > /tmp/srrp_demo_ont1_wan2_v4.log 2>&1 & echo $! > /tmp/srrp_demo_ont1_wan2_v4.pid'
docker exec ont2 sh -lc 'rm -f /tmp/srrp_demo_*; nohup ping -D -n -i 0.2 -W 1 -I <ONT2_PPP_V6> 2001:db8:aaaa::2 > /tmp/srrp_demo_ont2_ppp_v6.log 2>&1 & echo $! > /tmp/srrp_demo_ont2_ppp_v6.pid'
docker exec pc1 sh -lc 'rm -f /tmp/srrp_demo_pc1_lan_v6.*; nohup ping -D -n -i 0.2 -W 1 2001:db8:aaaa::2 > /tmp/srrp_demo_pc1_lan_v6.log 2>&1 & echo $! > /tmp/srrp_demo_pc1_lan_v6.pid'
```

Reemplazar `<ONT1_WAN1_V6>`, `<ONT1_WAN2_V6>`, `<ONT1_WAN2_V4>` y `<ONT2_PPP_V6>` con los valores detectados en `13.2`.

Estos cinco pings cubren:

- `ONT1 WAN1 IPv6-only`
- `ONT1 WAN2 dual-stack IPv6`
- `ONT1 WAN2 dual-stack IPv4`
- `ONT2 WAN1 PPPoE IPv6`
- `PC1` detrás del PD entregado por `ONT1`

## 13.4 Capturar el estado base

En el BNG MASTER:

```text
show srrp
show service active-subscribers
```

En el BNG SLAVE:

```text
show srrp
show service active-subscribers
```

Salida observada antes de la caída:

```text
A:admin@MASTER# show srrp
2  9998  dual-stack  Up  master
1  9998  ipv6-only   Up  master
3  9998  vip         Up  master
```

```text
A:admin@SLAVE# show srrp
2  9998  dual-stack  Up  backupShunt
1  9998  ipv6-only   Up  backupShunt
3  9998  vip         Up  backupShunt
```

## 13.5 Forzar la caída del enlace OLT -> BNG MASTER

Ejecutar el script desde `containerbot`:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c2/1'
```

Resultado esperado:

```text
OK: port 1/1/c2/1 admin-state=disable on 10.99.1.2
```

## 13.6 Validar el switchover

En `MASTER`:

```text
show srrp
show port 1/1/c2/1 detail
show service active-subscribers
```

En `SLAVE`:

```text
show srrp
show service active-subscribers
```

Resultado observado:

```text
A:admin@MASTER# show srrp
2  9998  dual-stack  Up  initialize
1  9998  ipv6-only   Up  initialize
3  9998  vip         Up  initialize
```

```text
A:admin@SLAVE# show srrp
2  9998  dual-stack  Up  master
1  9998  ipv6-only   Up  master
3  9998  vip         Up  master
```

```text
A:admin@MASTER# show service active-subscribers
...
00:d0:f6:01:01:01  IPoE   DHCP6        9998  N
00:d0:f6:01:01:02  IPoE   DHCP         9998  N
00:d0:f6:01:01:04  PPP 1  DHCP6        9998  N
```

```text
A:admin@SLAVE# show service active-subscribers
...
00:d0:f6:01:01:01  IPoE   DHCP6        9998  Y
00:d0:f6:01:01:02  IPoE   DHCP         9998  Y
00:d0:f6:01:01:04  PPP 1  DHCP6        9998  Y
```

## 13.7 Validar continuidad de tráfico

Si dejaste una terminal aparte con el modo visual, aquí deberías ver en tiempo real qué probes siguen respondiendo, cuáles cambian de `ttl` y si aparece un hueco de `icmp_seq`.

Revisar las colas de ping:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo watch
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo tail
docker exec ont1 sh -lc 'tail -n 12 /tmp/srrp_demo_ont1_wan1_v6.log'
docker exec ont1 sh -lc 'tail -n 12 /tmp/srrp_demo_ont1_wan2_v6.log'
docker exec ont1 sh -lc 'tail -n 12 /tmp/srrp_demo_ont1_wan2_v4.log'
docker exec ont2 sh -lc 'tail -n 12 /tmp/srrp_demo_ont2_ppp_v6.log'
docker exec pc1 sh -lc 'tail -n 12 /tmp/srrp_demo_pc1_lan_v6.log'
```

Señales observadas en esta ejecución:

- hubo continuidad de servicio, pero el switchover no fue hitless
- `ONT1 WAN1` presentó hueco de secuencia entre el último `ttl=62` en `icmp_seq=109` y el primer `ttl=63` en `icmp_seq=144`
- `ONT2 PPPoE` presentó hueco de secuencia entre el último `ttl=62` en `icmp_seq=113` y el primer `ttl=63` en `icmp_seq=154`
- `ONT1 WAN1` y `ONT2 PPPoE` cambiaron de `ttl=62` a `ttl=63`, indicando el nuevo camino vía `SLAVE`
- `ONT1 WAN2 IPv4` continuó respondiendo hacia `99.99.99.99`
- `PC1` siguió alcanzando `2001:db8:aaaa::2`, validando continuidad del PD/LAN

Ejemplo real de `ONT1 WAN1` durante el switchover:

```text
[1773352987.998830] 64 bytes from 2001:db8:aaaa::2: icmp_seq=109 ttl=62 time=2.22 ms
...
[1773352997.495945] 64 bytes from 2001:db8:aaaa::2: icmp_seq=144 ttl=63 time=2082 ms
```

Ejemplo real de `ONT2 PPPoE` durante el switchover:

```text
[1773352988.116137] 64 bytes from 2001:db8:aaaa::2: icmp_seq=113 ttl=62 time=1.32 ms
...
[1773352996.824532] 64 bytes from 2001:db8:aaaa::2: icmp_seq=154 ttl=63 time=1.03 ms
```

En esta prueba, la ventana de convergencia observada para tráfico de suscriptores fue de aproximadamente `8 a 10 segundos`.

## 13.8 Restaurar el puerto del MASTER

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c2/1'
```

Validar regreso al estado nominal:

```text
show srrp
show service active-subscribers
```

Resultado esperado:

- `MASTER` vuelve a `master`
- `SLAVE` vuelve a `backupShunt`
- las sesiones siguen activas
- en los pings IPv6 de `ont1` y `ont2` el `ttl` vuelve a `62`

## 13.9 Limpiar los procesos de ping

Usar solo una de estas dos opciones:

- si iniciaste los probes con el helper opcional, detenerlos con el helper
- si iniciaste los probes manualmente con `docker exec`, detenerlos manualmente con los `kill`

No es necesario ejecutar ambas opciones. Si primero usas el helper y luego ejecutas los `kill` manuales, puede aparecer `No such process` porque los probes ya habrán sido detenidos.

Opción 1, helper:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo stop
```

Opción 2, comandos manuales:

```bash
docker exec ont1 sh -lc 'kill -INT $(cat /tmp/srrp_demo_ont1_wan1_v6.pid) $(cat /tmp/srrp_demo_ont1_wan2_v6.pid) $(cat /tmp/srrp_demo_ont1_wan2_v4.pid)'
docker exec ont2 sh -lc 'kill -INT $(cat /tmp/srrp_demo_ont2_ppp_v6.pid)'
docker exec pc1 sh -lc 'kill -INT $(cat /tmp/srrp_demo_pc1_lan_v6.pid)'
```
