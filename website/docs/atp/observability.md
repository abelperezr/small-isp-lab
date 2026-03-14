---
sidebar_position: 12
sidebar_label: 12. Observabilidad
---

# 12. Validación de observabilidad en Grafana y Prometheus

Esta prueba valida que el tráfico generado por los suscriptores `ONT-001` y `ONT-002` se refleja correctamente en Prometheus y en el dashboard `Small ISP Telemetry` de Grafana.

Esta validación no usa el API del LEA. El LEA sirve para lawful interception y muestra paquetes espejados; la observabilidad de throughput se valida con Prometheus y Grafana.

Para esta validación se recomienda usar `iperf3` en modo UDP con bitrate fijo, ya que genera curvas más estables y visibles que `TCP` en este laboratorio.

Durante la validación real de este ATP:

- `ONT-001` generó octetos no cero en `bngmaster-1`
- `ONT-002` generó octetos no cero en `bngmaster-1`
- ambos suscriptores aparecieron en Prometheus bajo la etiqueta `subscriber_subscriber_id`

## 12.1 Preparar el servidor de prueba

El orquestador de observabilidad levanta automáticamente cuatro instancias de `iperf3` en el nodo `dns`, una por flujo.

Si se quiere revisar el estado de los puertos antes de ejecutar la prueba:

```bash
bash configs/cbot/scripts/observability-traffic.sh status
```

## 12.2 Confirmar que Prometheus ve ambos suscriptores

Listar los `subscriber_subscriber_id` disponibles:

```bash
curl -s 'http://10.99.1.10:9090/api/v1/label/subscriber_subscriber_id/values' | jq
```

El resultado esperado debe incluir:

```json
["ONT-001", "ONT-002"]
```

Ver las sesiones activas:

```bash
curl -s 'http://10.99.1.10:9090/api/v1/query?query=subscriber_mgmt_subscriber_sla_profile_instance_session_up_time' \
| jq '.data.result[] | {subscriber:.metric.subscriber_subscriber_id, source:.metric.source, session_type:.metric.session_type, session_id:.metric.session_id, value:.value[1]}'
```

Resultado esperado:

- `ONT-001` aparece como `session_type="ipoe"`
- `ONT-002` aparece como `session_type="ppp"`

## 12.3 Generar tráfico simultáneo desde ONT-001 y ONT-002

Usar el orquestador del laboratorio:

```bash
bash configs/cbot/scripts/observability-traffic.sh all
```

El perfil por defecto genera cuatro flujos simultáneos:

- `ONT-001 ingress`: `2 Mbit/s`
- `ONT-001 egress`: `2 Mbit/s`
- `ONT-002 ingress`: `3 Mbit/s`
- `ONT-002 egress`: `3 Mbit/s`

Usa puertos separados en `dns` para evitar el error `server is busy` de `iperf3`:

```text
5201 -> ONT-001 ingress
5202 -> ONT-001 egress
5203 -> ONT-002 ingress
5204 -> ONT-002 egress
```
Al finalizar, el mismo script imprime un resumen con los incrementos de octetos IPv6 en Prometheus para `ingress` y `egress`.
Si se quiere cambiar el perfil:

```bash
DURATION=30 \
ONT1_UP_BW=2M ONT1_DOWN_BW=2M \
ONT2_UP_BW=3M ONT2_DOWN_BW=3M \
IPERF_LEN=1200 \
bash configs/cbot/scripts/observability-traffic.sh all
```

Al finalizar, el mismo script imprime un resumen con los incrementos de octetos IPv6 en Prometheus para `ingress` y `egress`.

## 12.4 Perfil validado

Durante la validación real de este ATP:

- `ONT-001` sostuvo `2 Mbit/s` en `ingress` y `2 Mbit/s` en `egress`
- `ONT-002` sostuvo `3 Mbit/s` en `ingress` y `3 Mbit/s` en `egress`
- `ONT-002` quedó por encima de `ONT-001` en ambas gráficas

## 12.5 Verificar el incremento de octetos en Prometheus

El orquestador ya imprime este resumen automáticamente. Si se quiere volver a consultarlo manualmente:

```bash
bash configs/cbot/scripts/observability-traffic.sh report
```

Resultado esperado:

- `ONT-001` debe mostrar `octets > 0` en `bngmaster-1` para `ingress` y `egress`
- `ONT-002` debe mostrar `octets > 0` en `bngmaster-1` para `ingress` y `egress`

Si se desea ver la consulta PromQL directa para `ingress`:

```bash
curl -s 'http://10.99.1.10:9090/api/v1/query?query=sum%20by%20(subscriber_subscriber_id,source)%20(increase(subscriber_mgmt_subscriber_sla_profile_instance_ingress_qos_statistics_ipv6_forwarded_octets%7bsubscriber_subscriber_id=~%22ONT-001%7cONT-002%22%7d%5b5m%5d))' \
| jq '.data.result[] | {subscriber:.metric.subscriber_subscriber_id, source:.metric.source, octets:.value[1]}'
```

Y para `egress`:

```bash
curl -s 'http://10.99.1.10:9090/api/v1/query?query=sum%20by%20(subscriber_subscriber_id,source)%20(increase(subscriber_mgmt_subscriber_sla_profile_instance_egress_qos_statistics_ipv6_forwarded_octets%7bsubscriber_subscriber_id=~%22ONT-001%7cONT-002%22%7d%5b5m%5d))' \
| jq '.data.result[] | {subscriber:.metric.subscriber_subscriber_id, source:.metric.source, octets:.value[1]}'
```

## 12.6 Validar en Grafana

Abrir Grafana:

- URL: `http://localhost:3030`
- Dashboard: `Small ISP Telemetry`
- Time range: `Last 5 minutes`
- Refresh: `5s`

Seleccionar:

- `Node = bngmaster-1`
- `Subscriber = ONT-001`

Seleccionar:

- `Node = bngmaster-1`
- `Subscriber = ONT-001 + ONT-002`

Resultado esperado:

![Dashboard de Grafana](/img/grafana.png)

- el bloque `Subscriber Lens · State Tree` muestra ambos suscriptores
- `Ingress Subscriber Throughput` muestra `ONT-002` por encima de `ONT-001`
- `Egress Subscriber Throughput` muestra `ONT-002` por encima de `ONT-001`
- las curvas se ven sostenidas durante toda la duración de la prueba

## 12.7 Referencia visual

Usar la captura del dashboard de Grafana adjunta a esta validación como referencia visual del panel `Subscriber Lens · State Tree` y de las gráficas de throughput.

## 12.8 Limpieza

Detener los servidores del orquestador:

```bash
bash configs/cbot/scripts/observability-traffic.sh stop-servers
```

Ver estado de los puertos:

```bash
bash configs/cbot/scripts/observability-traffic.sh status
```

## 12.9 Consideraciones operativas

- `ONT-001` y `ONT-002` se observan en el dashboard usando el mismo selector `Subscriber`, cambiando solo el valor.
- Si `ONT-002 ingress` termina con `unable to read from stream socket: Resource temporarily unavailable`, en esta maqueta se considera un cierre transitorio de `iperf3` siempre que Prometheus muestre incremento de octetos.
- Si el dashboard no muestra actividad, validar primero en Prometheus que `increase(...)` devuelve octetos no cero.
- En esta topología la actividad útil se observa sobre `bngmaster-1`; en la validación realizada `bngslave-1` permaneció en cero para estos contadores.
- Para que los picos sean más visibles, usar una ventana corta en Grafana (`Last 5 minutes`) y refresh rápido (`5s`).
- Para observabilidad sostenida, usar `configs/cbot/scripts/observability-traffic.sh` en lugar de lanzar pruebas manuales por separado.
- El perfil por defecto ya deja `ONT-002` por encima de `ONT-001` tanto en `ingress` como en `egress`.
