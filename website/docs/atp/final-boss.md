---
sidebar_position: 14
sidebar_label: 14. Final Boss
---

# 14. Final Boss

Esta prueba pone al laboratorio contra la pared. La escena arranca con los suscriptores vivos, respirando tráfico real. Luego, uno por uno, caen tres pilares del sistema:

1. el enlace de acceso `OLT -> BNG MASTER`
2. el enlace `Carrier1 -> BNG2`, justo cuando `BNG2` ya quedó como `master`
3. el servidor `RADIUS`

La pregunta no es si la red sufre. La pregunta es si sobrevive.

## 14.1 Objetivo

Validar que el laboratorio mantiene servicio de suscriptores IPoE, PPPoE y LAN delegada durante una cadena de fallas consecutivas.

En esta ejecución real se observó:

- un switchover SRRP exitoso hacia `SLAVE`
- pérdida del upstream `Carrier1` en el nodo activo sin colapso del tráfico probado
- caída completa de `radius` sin expulsar a los suscriptores ya autenticados
- un único hueco de tráfico durante el primer switchover, del orden de 7.6 a 8.1 segundos según el probe

## 14.2 Prerrequisitos

Validar antes de iniciar:

```text
show srrp
show service active-subscribers
show router 9999 bgp summary
```

Estado base esperado:

- `MASTER`: SRRP `master`
- `SLAVE`: SRRP `backupShunt`
- `ONT-001` y `ONT-002` presentes en `show service active-subscribers`
- `Carrier1` y `Carrier2` arriba en el nodo activo

## 14.3 Determinar las IP fuente actuales

Atajo opcional:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss start
```

Si usas este helper, puedes saltarte `14.3` y `14.4` y continuar directamente en `14.5`. El script detecta las IP fuente actuales y lanza todos los probes del ATP.

Para una vista de la secuencia de pings durante la prueba, deja una segunda terminal abierta con:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss watch
```

Así puedes ver en vivo la última respuesta de cada ping mientras ejecutas las caídas del ATP en la terminal principal.

Antes de iniciar los probes, identificar las direcciones vigentes del lab. Estas IP pueden variar entre corridas, por lo que no se recomienda usar valores fijos.

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

## 14.4 Acto I: La Calma antes de la Tormenta

Lanzar los probes continuos:

```bash
docker exec ont1 sh -lc 'rm -f /tmp/final_boss_*; nohup ping -D -n -i 0.2 -W 1 -I <ONT1_WAN1_V6> 2001:db8:aaaa::2 > /tmp/final_boss_ont1_wan1_v6.log 2>&1 & echo $! > /tmp/final_boss_ont1_wan1_v6.pid; nohup ping -D -n -i 0.2 -W 1 -I <ONT1_WAN2_V6> 2001:db8:aaaa::2 > /tmp/final_boss_ont1_wan2_v6.log 2>&1 & echo $! > /tmp/final_boss_ont1_wan2_v6.pid; nohup ping -D -n -i 0.2 -W 1 -I <ONT1_WAN2_V4> 99.99.99.99 > /tmp/final_boss_ont1_wan2_v4.log 2>&1 & echo $! > /tmp/final_boss_ont1_wan2_v4.pid'
docker exec ont2 sh -lc 'rm -f /tmp/final_boss_*; nohup ping -D -n -i 0.2 -W 1 -I <ONT2_PPP_V6> 2001:db8:aaaa::2 > /tmp/final_boss_ont2_ppp_v6.log 2>&1 & echo $! > /tmp/final_boss_ont2_ppp_v6.pid'
docker exec pc1 sh -lc 'rm -f /tmp/final_boss_*; nohup ping -D -n -i 0.2 -W 1 2001:db8:aaaa::2 > /tmp/final_boss_pc1_lan_v6.log 2>&1 & echo $! > /tmp/final_boss_pc1_lan_v6.pid'
```

Reemplazar `<ONT1_WAN1_V6>`, `<ONT1_WAN2_V6>`, `<ONT1_WAN2_V4>` y `<ONT2_PPP_V6>` con los valores detectados en `14.3`.

Estos probes cubren:

- `ONT1 WAN1 IPv6-only -> DNS64`
- `ONT1 WAN2 IPv6 -> DNS64`
- `ONT1 WAN2 IPv4 -> 99.99.99.99`
- `ONT2 PPPoE IPv6 -> DNS64`
- `PC1 detrás del PD -> DNS64`

Para revisar los logs generados por los probes:

Opción 1, helper:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss watch
bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss tail
```

Opción 2, comandos manuales:

```bash
docker exec ont1 sh -lc 'tail -n 12 /tmp/final_boss_ont1_wan1_v6.log'
docker exec ont1 sh -lc 'tail -n 12 /tmp/final_boss_ont1_wan2_v6.log'
docker exec ont1 sh -lc 'tail -n 12 /tmp/final_boss_ont1_wan2_v4.log'
docker exec ont2 sh -lc 'tail -n 12 /tmp/final_boss_ont2_ppp_v6.log'
docker exec pc1 sh -lc 'tail -n 12 /tmp/final_boss_pc1_lan_v6.log'
```

Muestras base observadas:

```text
[1773326051.535098] 64 bytes from 2001:db8:aaaa::2: icmp_seq=43 ttl=62 time=3.97 ms
[1773326051.543326] 64 bytes from 99.99.99.99: icmp_seq=43 ttl=63 time=11.2 ms
[1773326051.648545] 64 bytes from 2001:db8:aaaa::2: icmp_seq=43 ttl=62 time=1.73 ms
[1773326051.667407] 64 bytes from 2001:db8:aaaa::2: icmp_seq=43 ttl=61 time=1.83 ms
```

## 14.5 Acto II: El Primer Impacto

Cortar el enlace `OLT -> BNG MASTER`:

```bash
docker exec containerbot sh -lc '/app/scripts/olt-to-bng1-down.sh'
```

Validar:

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

Aquí llegó el golpe más fuerte. Los probes no murieron, pero sí hubo una pausa real durante el switchover.

Ejemplo observado en `ONT1 WAN1`:

```text
[1773326055.947060] 64 bytes from 2001:db8:aaaa::2: icmp_seq=65 ttl=62 time=3.00 ms
[1773326063.996298] 64 bytes from 2001:db8:aaaa::2: icmp_seq=103 ttl=63 time=1.92 ms
```

Interpretación:

- hubo un único hueco de aproximadamente 8 segundos en el primer failover
- al regresar el tráfico, `ttl=62` pasó a `ttl=63`, señal de que el camino ya iba por `SLAVE`

## 14.6 Acto III: Aislamiento Progresivo

Con `SLAVE` ya como `master`, cortar `Carrier1 -> BNG2`:

```bash
docker exec containerbot sh -lc '/app/scripts/carrier1-to-bng2-down.sh'
```

Validar en `SLAVE`:

```text
show router 9999 bgp summary
show srrp
```

Resultado observado:

```text
A:admin@SLAVE# show router 9999 bgp summary
...
172.16.1.3
to_CARRIER1
                65501       0    0 00h00m01s Connect
                            0    0
172.16.2.3
to_CARRIER2
                65502     181    0 01h27m08s 2/2/3 (IPv4)
                          191    0           2/2/4 (IPv6)
```

```text
A:admin@SLAVE# show srrp
2  9998  dual-stack  Up  master
1  9998  ipv6-only   Up  master
3  9998  vip         Up  master
```

Señales observadas en los probes:

- no aparecieron huecos nuevos de `icmp_seq`
- `ONT1 WAN2 IPv4 -> 99.99.99.99` siguió respondiendo
- los flujos IPv6 internos (`ONT1`, `ONT2`, `PC1`) siguieron vivos

Ejemplo real tras esta segunda caída:

```text
[1773326087.851562] 64 bytes from 99.99.99.99: icmp_seq=222 ttl=63 time=16.3 ms
[1773326088.052683] 64 bytes from 99.99.99.99: icmp_seq=223 ttl=63 time=16.8 ms
```

## 14.7 Acto IV: Muerte Cerebral

Apagar `RADIUS`:

```bash
docker stop radius
```

Validar:

```bash
docker ps -a --format '{{.Names}}\t{{.Status}}' | rg '^radius\b'
```

```text
show service active-subscribers
```

Resultado observado:

```text
radius    Exited (0) 32 seconds ago
```

Los suscriptores ya activos siguieron presentes y reenviando en el nodo master:

```text
A:admin@SLAVE# show service active-subscribers
...
2001:db8:100::5/128
              00:d0:f6:01:01:01  IPoE               DHCP6        9998       Y
100.80.0.4
              00:d0:f6:01:01:02  IPoE               DHCP         9998       Y
2001:db8:100::4/128
              00:d0:f6:01:01:04  PPP 1              DHCP6        9998       Y
```

Y los probes siguieron vivos:

```text
[1773326125.789863] 64 bytes from 99.99.99.99: icmp_seq=411 ttl=63 time=6.39 ms
[1773326125.737325] 64 bytes from 2001:db8:aaaa::2: icmp_seq=410 ttl=63 time=1.79 ms
[1773326125.757919] 64 bytes from 2001:db8:aaaa::2: icmp_seq=410 ttl=62 time=1.85 ms
```

Nota operativa:

- con `Test account` deshabilitado en el policy de health-check, `show aaa radius-server-policy "radius_policy"` puede tardar en reflejar la caída aunque el contenedor ya esté abajo
- en esta prueba no se forzaron nuevas autenticaciones; se verificó continuidad de las sesiones ya establecidas

## 14.8 Veredicto

El laboratorio sobrevive al “Final Boss”.

Pero la verdad importa:

- **no fue hitless**
- el primer switchover (`OLT -> BNG MASTER` down) generó una interrupción visible de unos 8 segundos
- después de ese golpe inicial, la red absorbió la caída de `Carrier1` en el nodo activo y la caída de `RADIUS` sin perder los flujos probados

Conclusión:

- si el criterio es **supervivencia del servicio**, la prueba pasa
- si el criterio es **cero pérdida durante el primer failover**, la prueba no pasa todavía

## 14.9 Restauración

```bash
docker exec containerbot sh -lc '/app/scripts/carrier1-to-bng2-up.sh'
docker exec containerbot sh -lc '/app/scripts/olt-to-bng1-up.sh'
docker start radius
```

Nota:

- `carrier1-to-bng2-up.sh` debe habilitar `ethernet-1/2` en `Carrier1`, que es la interfaz afectada en el paso de caída

Validar regreso al estado nominal:

```text
show srrp
show router 9999 bgp summary
```

Estado esperado:

- `MASTER` vuelve a `master`
- `SLAVE` vuelve a `backupShunt`
- `Carrier1` y `Carrier2` regresan
- `radius` vuelve a `Up`

## 14.10 Limpiar los probes

Usar solo una de estas dos opciones:

- si iniciaste los probes con el helper opcional, detenerlos con el helper
- si iniciaste los probes manualmente con `docker exec`, detenerlos manualmente con los `kill`

No es necesario ejecutar ambas opciones. Si primero usas el helper y luego ejecutas los `kill` manuales, puede aparecer `No such process` porque los probes ya habrán sido detenidos.

Opción 1, helper:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss stop
```

Opción 2, comandos manuales:

```bash
docker exec ont1 sh -lc 'kill -INT $(cat /tmp/final_boss_ont1_wan1_v6.pid) $(cat /tmp/final_boss_ont1_wan2_v6.pid) $(cat /tmp/final_boss_ont1_wan2_v4.pid)'
docker exec ont2 sh -lc 'kill -INT $(cat /tmp/final_boss_ont2_ppp_v6.pid)'
docker exec pc1 sh -lc 'kill -INT $(cat /tmp/final_boss_pc1_lan_v6.pid)'
```
