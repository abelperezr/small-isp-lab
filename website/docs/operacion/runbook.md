---
sidebar_position: 1
---

# Runbook de operación diaria

Este runbook sintetiza los comandos más útiles del laboratorio para operación diaria. No reemplaza el ATP: lo resume y enlaza a las validaciones detalladas cuando hace falta profundizar.

## 1. Salud general del laboratorio

Revisión rápida del estado de Containerlab y contenedores:

```bash
sudo clab ins -t lab.yml
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Resultado esperado:

- nodos relevantes en `running`
- puertos publicados visibles para Grafana, Prometheus, ONTs y LEA

Servicios principales:

- Grafana: `http://localhost:3030`
- Prometheus: `http://localhost:9090`
- LEA/LIG: `http://localhost:8092`
- ONT1 Web: `http://localhost:8090`
- ONT2 Web: `http://localhost:8091`

Referencia ATP:

- [Validación base de BNG](../atp/bng-baseline.md)
- [Validación base de OLT](../atp/olt-baseline.md)
- [Validación base de Carriers](../atp/carriers-baseline.md)

## 2. Revisión rápida de red base

### BNG MASTER / SLAVE

```text
show system alarms
show port
show router interface
show srrp
show router 9999 bgp summary
```

Esperado:

- sin alarmas críticas
- puertos e interfaces relevantes en `up`
- SRRP operativo
- vecinos BGP establecidos

### OLT

```text
show interface all
show network-instance bd-50 interfaces
macsum bd-50
macsum bd-srrp
```

Esperado:

- subinterfaces bridged en `up`
- MAC-VRFs activas
- aprendizaje MAC coherente

### Carriers

```text
show interface all
show network-instance route-table ipv4-unicast summary
show network-instance route-table ipv6-unicast summary
show network-instance protocols bgp summary
```

Esperado:

- interfaces de upstream en `up`
- rutas IPv4/IPv6 presentes
- BGP `established` con ambos BNG

## 3. Revisar sesiones de suscriptor

En BNG:

```text
show service active-subscribers
```

En ONT2 PPPoE:

```bash
docker exec ont2 sh -lc 'ip ad show ppp0; echo ---; ip -6 route'
```

En PC1 para prefijo delegado:

```bash
docker exec pc1 sh -lc 'ip -6 ad show dev eth1'
```

Esperado:

- `ONT-001` y/o `ONT-002` visibles según el escenario
- `ppp0` operativo en `ont2` cuando PPPoE está activo
- prefijo IPv6 delegado visible en `pc1`

Referencia ATP:

- [ESM](../atp/esm.md)
- [Pruebas ONT](../atp/ont.md)

## 4. Limpiar sesiones y forzar reautenticación

En BNG:

```text
clear service id "9998" ipoe session all
```

Nota:

- después de este `clear`, las sesiones IPoE pueden tardar varios segundos en reconstruirse
- es normal que WAN IPv6, prefijo delegado y leases IPv4/IPv6 vuelvan con valores distintos a los anteriores
- si `ONT-001` no reaparece tras la convergencia, usa la renovación DHCP/DHCPv6 desde la ONT o sigue la referencia del ATP de ESM

Para suspender o reactivar el suscriptor PPPoE:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py deactivate "test@test.com"'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py add "test@test.com" \
  --title "ONT2-WAN1" \
  --password "testlab123" \
  --framed-pool "cgnat" \
  --framed-ipv6-pool "IPv6" \
  --delegated-ipv6-pool "IPv6" \
  --subscriber-id "ONT-002" \
  --subscriber-profile "subprofile" \
  --msap-interface "ipv6-only" \
  --sla-profile "100M"'
```

Esperado:

- el suscriptor desaparece y vuelve a aparecer en `show service active-subscribers`
- `ont2` pierde y recupera `ppp0`

Referencia ATP:

- [ESM](../atp/esm.md)

## 5. Validar SRRP y recuperación de BGP

Verificación base:

```text
show srrp
show router 9999 bgp summary
show router 9999 bgp neighbor 172.16.1.1 detail | match "Export Policy"
show router 9999 bgp neighbor 172.16.2.1 detail | match "Export Policy"
```

Simular cambio de rol:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1'
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c1/1'
```

Este caso prueba la caída del enlace entre BNGs. El cambio de rol SRRP también ocurre aquí por la `policy 1`, aunque el `message-path` de SRRP siga viajando por `1/1/c2/1` vía OLT.

Esperado:

- SRRP cambia entre `master` y `backup`
- export policies BGP cambian según el rol
- el estado vuelve a la condición original al reactivar el puerto

Referencia ATP:

- [SRRP y BGP](../atp/srrp-bgp.md)

## 6. Validar NAT64 rápido

Desde ONT1:

```bash
docker exec ont1 sh -lc 'ping -6 -c 4 -I 2001:db8:cccc::1 64:ff9b::808:808'
```

En BNG:

```text
tools dump nat sessions
```

Opcional:

```text
pyexec "cf3:\scripts\nat64_portblocks.py"
```

Esperado:

- ping exitoso al prefijo NAT64
- sesiones NAT64 visibles en el BNG

Nota:

- en la validación actual, el camino NAT64 operativo de `ont1` salió por la IPv6 de `wan2` (`2001:db8:cccc::1`)
- como alternativa rápida de aplicación, también funciona:

```bash
docker exec ont1 sh -lc 'curl -6 -I --max-time 15 http://example.com'
```

Referencia ATP:

- [NAT64](../atp/nat64.md)

## 7. Regenerar tráfico para observabilidad

Estado de puertos del orquestador:

```bash
bash configs/cbot/scripts/observability-traffic.sh status
```

Generar tráfico:

```bash
bash configs/cbot/scripts/observability-traffic.sh all
```

Ver resumen:

```bash
bash configs/cbot/scripts/observability-traffic.sh report
```

Detener servidores:

```bash
bash configs/cbot/scripts/observability-traffic.sh stop-servers
```

Esperado:

- incremento de octetos para `ONT-001` y `ONT-002`
- visibilidad en Prometheus y Grafana

Referencia ATP:

- [Observabilidad](../atp/observability.md)

## 8. Validar LEA rápido

Precondición:

- debe existir una captura LI activa en el BNG
- la identidad interceptada puede ser `ONT-001` o un `subscriber-id` reconstruido tipo `MAC|SAP`, según el estado AAA
- la WAN usada para generar tráfico debe corresponder a esa identidad interceptada
- si necesitas preparar o validar esa parte, usa [LEA y LI](../atp/lea-validation.md) y [Consola LEA](../lea-console/ejecucion.md)

Levantar servidor de prueba:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh start
bash configs/cbot/scripts/dns-iperf-server.sh status
```

Generar tráfico desde ONT1:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan2 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh upload
```

Si la captura activa está amarrada a `wan1`, cambia `ONT_WAN=wan1`.

Consultar API:

```bash
curl -s http://10.99.1.12:8080/api/stats | jq
curl -s 'http://10.99.1.12:8080/api/events?limit=20' | jq
```

Detener servidor:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh stop
```

Esperado:

- eventos visibles en LEA
- contadores y flujos presentes en la API

Referencia ATP:

- [LEA y LI](../atp/lea-validation.md)

## 9. Checklist post-cambio

Después de cualquier cambio operativo, validar al menos:

```bash
sudo clab ins -t lab.yml
docker ps --format "table {{.Names}}\t{{.Status}}"
```

```text
show srrp
show router 9999 bgp summary
show service active-subscribers
```

```bash
bash configs/cbot/scripts/observability-traffic.sh report
curl -s http://10.99.1.12:8080/api/stats | jq
```

Si todo está correcto:

- laboratorio en `running`
- SRRP y BGP sanos
- suscriptores visibles
- observabilidad activa
- LEA responde
