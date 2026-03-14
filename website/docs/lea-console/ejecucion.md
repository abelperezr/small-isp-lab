---
sidebar_position: 4
---

# Ejecución Manual de LEA

## Descripción

Esta opción documenta cómo activar manualmente una interceptación legal desde el MD-CLI del BNG, usando el usuario `liadmin`.

## Acceso al BNG

Accede por SSH con:

- usuario: `liadmin`
- contraseña: `admin123`

Luego entra en modo privado de LI:

```text
[/]
A:liadmin@BNG1# li private
INFO: CLI #2070: Entering private configuration mode
INFO: CLI #2061: Uncommitted changes are discarded on configuration mode exit
```

## Habilitar logging hacia NETCONF

Este procedimiento también puede realizarse manualmente desde CLI:

```text
log log-id "1" netconf-stream "li"
log log-id "1" source li true
log log-id "1" destination netconf
```

## Activar interceptación por suscriptor

Ejemplo de interceptación por suscriptor:

```text
li-source "li-dest-1" subscriber "ONT-001" ingress true
li-source "li-dest-1" subscriber "ONT-001" egress true
li-source "li-dest-1" subscriber "ONT-001" intercept-id 1001
li-source "li-dest-1" subscriber "ONT-001" session-id 1
```

## Notas

- `li private` habilita el modo de configuración privada para cambios de LI.
- `li-dest-1` debe existir previamente como mirror destination.
- El ejemplo anterior intercepta tráfico `ingress` y `egress` del suscriptor `ONT-001` cuando no hay fallback a LUDB.
- `intercept-id` y `session-id` deben ajustarse según la operación requerida.
- Si el subscriber fue reconstruido por fallback a LUDB, `ONT-001` puede no aparecer como `subscriber-id` activo. En ese caso usa el `subscriber-id` exacto que devuelve `show service active-subscribers`, por ejemplo `00:d0:f6:01:01:01|1/1/c2/1:50.150`.
- Si generas tráfico con `configs/cbot/scripts/ont1-subscriber-traffic.sh`, usa preferiblemente `ONT_WAN=wan2` sin fallback y `ONT_WAN=wan1` en el caso validado de fallback a LUDB.
- `configs/cbot/scripts/ont2-subscriber-traffic.sh` también puede usarse para `ONT-002`; el parser actual del LIG ya decodifica PPPoE session con tráfico IP.
