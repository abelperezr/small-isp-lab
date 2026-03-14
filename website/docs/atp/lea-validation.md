---
sidebar_position: 11
sidebar_label: 11. LEA y LI
---

# 11. Interceptación legal y validación en LEA

Esta prueba permite validar que el BNG envía tráfico interceptado hacia el LIG/LEA y que el panel web y las APIs reflejan los flujos del suscriptor `ONT-001`.

## 11.0 Seleccionar el escenario antes de empezar

Antes de activar LI, confirma en qué escenario estás:

| Escenario | Cómo aparece el suscriptor en el BNG | WAN principal para ATP 11 | Script |
| --- | --- | --- | --- |
| RADIUS normal | `ONT-001` | `wan2` | `ont1-subscriber-traffic.sh` |
| Fallback a LUDB | normalmente `<MAC>\|<SAP>` | `wan1` | `ont1-subscriber-traffic.sh` |
| Alternativa PPPoE | `ONT-002` / `test@test.com` | `ppp0` | `ont2-subscriber-traffic.sh` |

Pre-check recomendado:

```text
A:admin@MASTER# show service active-subscribers
```

Resultado esperado:

- sin fallback AAA a LUDB, `ONT-001` debe verse como alias normal y el flujo más simple para ATP 11 es `wan2`
- con fallback a LUDB, usa el `subscriber-id` activo exacto que devuelve el BNG y mantén toda la corrida sobre esa misma WAN

Todos los scripts de tráfico mencionados en esta sección están en `configs/cbot/scripts/`.

Regla práctica para `li-source`:

- antes de fallback a LUDB, el identificador que funciona de forma consistente es el alias del suscriptor, por ejemplo `subscriber "ONT-001"`
- después de fallback a LUDB, ese alias puede dejar de resolver y el identificador correcto pasa a ser el `subscriber-id` activo exacto que devuelve el BNG, por ejemplo `00:d0:f6:01:01:01|1/1/c2/1:50.150`
- no hay un único valor de `subscriber` que sea universal para ambos estados
- si necesitas algo reutilizable, primero descubre el identificador activo real y luego construye `li-source` con ese valor

Nota importante sobre `iperf3`:

- los scripts `ont1-subscriber-traffic.sh` y `ont2-subscriber-traffic.sh` fijan `IPERF_MSS=1400` por defecto
- esto evita el caso visto en laboratorio donde la sesión TCP negociaba un `MSS` jumbo cercano a `9440`, enviaba un burst inicial y luego quedaba sin tráfico sostenido
- si sobrescribes `IPERF_MSS`, mantén un valor conservador o valida tú mismo que el camino soporte segmentos TCP grandes de forma estable

## 11.1 Levantar el servidor TCP de prueba

Iniciar `iperf3` sobre el nodo `dns`:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh start
```

Verificar que escuche en `2001:db8:aaaa::2:5201`:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh status
```

Resultado esperado:

- `status` debe mostrar una línea `LISTEN` para `2001:db8:aaaa::2:5201`
- si `status` no muestra el listener, no continúes con `upload` o `download`

## 11.2 Activar la interceptación en el BNG

Desde el usuario `liadmin` en el BNG activo:

- sin haber aplicado fallback a LUDB, el flujo validado más simple es usar `subscriber "ONT-001"`
- si ya aplicaste fallback a LUDB, `ONT-001` deja de aparecer como alias en el BNG; en ese caso usa el `subscriber-id` activo exacto que devuelve `show service active-subscribers`
- `ONT-002` también puede usarse como alternativa PPPoE, pero el ATP principal sigue siendo `ONT-001` porque es el camino más claro para IPoE

```text
A:liadmin@MASTER# li private
[pr:/li]
A:liadmin@MASTER# li-source "li-dest-1" subscriber "ONT-001" ingress true
A:liadmin@MASTER# li-source "li-dest-1" subscriber "ONT-001" egress true
A:liadmin@MASTER# li-source "li-dest-1" subscriber "ONT-001" intercept-id 1001
A:liadmin@MASTER# li-source "li-dest-1" subscriber "ONT-001" session-id 1
A:liadmin@MASTER# log log-id "1" netconf-stream "li"
A:liadmin@MASTER# log log-id "1" source li true
A:liadmin@MASTER# log { log-id "1" destination netconf }
A:liadmin@MASTER# commit
```

Nota:

- el LIG de este laboratorio consume el mirror UDP (`ip-udp-shim`) del BNG
- el `netconf-stream "li"` sigue siendo útil como referencia operativa, pero el panel LEA mostrado en el lab se alimenta del listener UDP en el puerto `11111`
- si el ATP se ejecuta con AAA en fallback a LUDB, el `subscriber-id` puede dejar de ser `ONT-001` y aparecer como `<MAC>|<SAP>` en `show service active-subscribers`
- en ese escenario, la forma más precisa de activar LI es usar el `subscriber-id` reconstruido que devuelve el BNG; el uso por `SAP` puede mezclar tráfico de otras sesiones si comparten el mismo circuito
- el alcance de la captura depende de cómo configures `li-source`: por alias de suscriptor, por `subscriber-id` exacto o por el contexto real de la sesión activa
- para ATP conviene usar la identidad exacta que devuelve el BNG en esa corrida, porque así evitas mezclar tráfico de otras sesiones

Ejemplo usando el subscriber activo exacto en fallback a LUDB:

```text
A:liadmin@MASTER# li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" ingress true
A:liadmin@MASTER# li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" egress true
A:liadmin@MASTER# li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" intercept-id 2004
A:liadmin@MASTER# li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" session-id 1
A:liadmin@MASTER# commit
```

Configuración exacta usada en las pruebas validadas de esta corrida:

```text
[pr:/li]
A:liadmin@MASTER# info flat
    li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" ingress true
    li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" egress true
    li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" intercept-id 2101
    li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" session-id 1
    log log-id "1" netconf-stream "li"
    log log-id "1" source li true
    log { log-id "1" destination netconf }
```

Lectura operativa de esa configuración:

- la captura quedó amarrada al `subscriber-id` exacto de `wan1`
- por eso en esta validación las consultas API correctas usan `intercept-id 2101`
- por eso también las pruebas funcionales de tráfico se alinearon con `ONT_WAN=wan1`
- esa misma sintaxis no es la recomendada cuando AAA todavía no ha hecho fallback a LUDB; en ese caso normalmente debes interceptar `subscriber "ONT-001"`

Importante:

- el script `configs/cbot/scripts/ont1-subscriber-traffic.sh` acepta `ONT_WAN=wan1|wan2|wan3` y resuelve automáticamente la IPv6 activa de esa WAN
- sin fallback AAA a LUDB, la opción validada más simple es usar `ONT_WAN=wan2`, porque coincide con el flujo dual-stack normal de `ONT-001`
- `wan1` también puede usarse sin fallback si interceptaste `ONT-001` y quieres validar específicamente esa WAN; no es la ruta principal del ATP porque `wan2` deja una validación más representativa del caso dual-stack normal
- si vienes de fallback a LUDB, usa la WAN que corresponda al `subscriber-id` reconstruido que elegiste
- en la validación actual del laboratorio, el caso correcto para `ONT-001` en fallback a LUDB es `ONT_WAN=wan1`
- no mezclar `wan1` y `wan2` en la misma corrida del ATP 11; si interceptaste `00:d0:f6:01:01:01|1/1/c2/1:50.150`, todas las pruebas deben salir por `wan1`
- ejecutar `upload`, `download` y `dns64` en secuencia, no en paralelo
- para ATP usar `PARALLEL=1`; valores mayores vuelven la prueba más frágil y no aportan valor funcional para LEA
- los scripts ya fijan `IPERF_MSS=1400` por defecto para evitar el burst inicial sin tráfico sostenido
- `configs/cbot/scripts/ont2-subscriber-traffic.sh` también quedó preparado para validar `ONT-002` si quieres una prueba alternativa PPPoE

Comprobación rápida:

Caso sin fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan2 bash configs/cbot/scripts/ont1-subscriber-traffic.sh show-bind
```

Caso alternativo sin fallback sobre `wan1`:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh show-bind
```

Caso con fallback a LUDB:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh show-bind
```

Resultado esperado:

- sin fallback:
  - `ONT_WAN=wan2`
  - `INTERFACE=eth3.200`
  - `ONT_BIND_V6=<IPv6 WAN activa de ONT-001 en wan2>`
- alternativa válida sin fallback:
  - `ONT_WAN=wan1`
  - `INTERFACE=eth1.150`
  - `ONT_BIND_V6=<IPv6 WAN activa de ONT-001 en wan1>`
- con fallback:
  - `ONT_WAN=wan1`
  - `INTERFACE=eth1.150`
  - `ONT_BIND_V6=<IPv6 WAN activa de ONT-001 en wan1>`

## 11.3 Generar tráfico TCP desde ONT1

Caso sin fallback a LUDB:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan2 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh upload
```

Caso alternativo sin fallback sobre `wan1`:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh upload
```

Caso con fallback a LUDB sobre el subscriber reconstruido de `ONT-001`:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh upload
```

No lanzar este comando en paralelo con `download` o `dns64`.

Si necesitas otra sesión, cambia `ONT_WAN` o usa `ONT_BIND_V6` explícito. Lo importante es que el tráfico salga por la misma sesión que interceptaste en el BNG.

Internamente ejecuta:

```bash
iperf3 -6 -c 2001:db8:aaaa::2 -B <IPv6-activa-de-la-WAN-elegida> -p 5201 -t 12 -P 1 -M 1400
```

En LEA se deben observar eventos similares a:

- `PROTO = TCP`
- `IP ORIGEN = IPv6 activa de la WAN elegida`
- `IP DESTINO = 2001:db8:aaaa::2`
- `P.ORIG` con puertos efímeros altos
- `P.DEST` igual a `5201`

Nota operativa:

- después del fix de `MSS`, `iperf3` debe mostrar tráfico sostenido en vez de sólo un burst inicial
- el throughput exacto no es un KPI del ATP; lo importante es que la sesión TCP se mantenga y que el LEA registre eventos `INGRESS` y `EGRESS`
- si vuelves a ver `256 KBytes` en el primer segundo y luego `0.00 bits/sec`, revisa que no hayas sobrescrito `IPERF_MSS`

Referencia visual del resultado esperado en LEA:

![Vista esperada de LEA con eventos TCP decodificados](/img/LEA.png)

## 11.4 Generar tráfico en sentido inverso

Sin fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan2 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh download
```

Alternativa sin fallback sobre `wan1`:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh download
```

Con fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh download
```

Resultado esperado:

- el comando no debe terminar con `Connection refused`
- el comando no debe terminar con `control socket has closed unexpectedly`
- en LEA deben aparecer flujos TCP desde `2001:db8:aaaa::2:5201` hacia la IPv6 de la WAN elegida clasificados como `EGRESS`

## 11.5 Generar tráfico DNS64/UDP

Sin fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan2 DURATION=10 bash configs/cbot/scripts/ont1-subscriber-traffic.sh dns64
```

Alternativa sin fallback sobre `wan1`:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=10 bash configs/cbot/scripts/ont1-subscriber-traffic.sh dns64
```

Con fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=10 bash configs/cbot/scripts/ont1-subscriber-traffic.sh dns64
```

En LEA esto suele verse como:

- `PROTO = UDP`
- `IP DESTINO = 2001:db8:aaaa::2`
- `P.DEST = 53`

Referencia visual del resultado esperado en LEA para DNS64/UDP:

![Vista esperada de LEA con eventos DNS64/UDP](/img/LEA2.png)

## 11.6 Detener y revisar el servidor de pruebas

Detener `iperf3`:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh stop
```

Ver logs del servidor:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh logs
```

## 11.7 Consultar las APIs del LEA

Prerequisitos en el host desde donde vas a consultar la API:

```bash
sudo apt install jq curl
```

Resumen general:

```bash
curl -s http://10.99.1.12:8080/api/stats | jq
```

Ultimos eventos:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=20' | jq
```

Eventos de una interceptación específica:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=100&intercept_id=<INTERCEPT_ID_USADO_EN_LI>' | jq
```

Resumen de interceptaciones:

```bash
curl -s http://10.99.1.12:8080/api/intercepts | jq
```

## 11.8 Consultas útiles sobre los eventos

Antes de ejecutar estos comandos, reemplaza explícitamente `<INTERCEPT_ID_USADO_EN_LI>` por el `intercept-id` real que configuraste en `li-source`.

Ejemplo:

```text
Si en LI configuraste:
intercept-id 1001

entonces debes cambiar:
<INTERCEPT_ID_USADO_EN_LI>

por:
1001
```

Top protocolos observados:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USADO_EN_LI>' \
| jq -r 'group_by(.proto)[] | "\(.[0].proto): \(length)"'
```

Top IPs origen:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USADO_EN_LI>' \
| jq -r 'group_by(.src_ip)[] | "\(.[0].src_ip): \(length)"'
```

Top IPs destino:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USADO_EN_LI>' \
| jq -r 'group_by(.dst_ip)[] | "\(.[0].dst_ip): \(length)"'
```

Top puertos destino:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USADO_EN_LI>' \
| jq -r 'map(select(.dst_port != null)) | group_by(.dst_port)[] | "\(.[0].dst_port): \(length)"'
```

Separación de tráfico `INGRESS` y `EGRESS`:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USADO_EN_LI>' \
| jq -r 'group_by(.direction)[] | "\(.[0].direction): \(length)"'
```

Flujos únicos `src_ip:src_port -> dst_ip:dst_port`:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USADO_EN_LI>' \
| jq -r '.[] | "\(.proto) \(.src_ip):\(.src_port) -> \(.dst_ip):\(.dst_port)"' \
| sort | uniq -c
```

## 11.9 Consideraciones operativas

- Si las APIs devuelven contadores en cero o listas vacías, normalmente no hay tráfico interceptado activo en ese momento.
- Si el `li-source` se configura en el BNG equivocado, el LIG no verá paquetes aunque el panel esté operativo.
- Si `ONT-001` desaparece por fallback a LUDB, no lo sustituyas automáticamente por `ONT-002`. Primero revisa `show service active-subscribers` y usa el `subscriber-id` activo exacto de `ONT-001`.
- Sin fallback AAA a LUDB, la corrida principal de ATP 11 para `ONT-001` se hace sobre `wan2`.
- `wan1` también es válida sin fallback si quieres observar esa sesión en particular.
- En fallback a LUDB, la corrida validada de ATP 11 para `ONT-001` se hace sobre `wan1`.
- La WAN correcta siempre debe corresponder a la identidad que hayas interceptado en `li-source`.
- Si interceptas por `subscriber-id` exacto, consulta la API con ese `intercept-id` real y genera tráfico por esa misma sesión.
- Si AAA todavía está normal, no asumas que el `subscriber-id` estilo `<MAC>|<SAP>` servirá para LI; en ese estado usa el alias del suscriptor que expone el BNG, por ejemplo `ONT-001`.
- Si buscas un método genérico, el enfoque correcto no es fijar un string único sino resolver primero la identidad activa del suscriptor y usar esa identidad en la captura.
- Si pruebas `wan3` o mezclas `wan1` y `wan2` en la misma corrida, eso ya es otra validación distinta y no debe mezclarse con el ATP principal.
- `ONT-002` también puede validarse ahora por LEA, porque el parser del LIG ya decodifica PPPoE session con IPv6/IPv4.
- Para la validación más clara del LEA, combinar una prueba TCP (`iperf3`) y otra UDP (`dns64`) permite distinguir rápidamente los protocolos en la interfaz.
- Si `iperf3` vuelve a caer en un burst inicial seguido de `0.00 bits/sec`, la causa más probable es que se esté usando un `MSS` demasiado grande para ese camino de laboratorio. Vuelve a probar con el valor por defecto `IPERF_MSS=1400`.
