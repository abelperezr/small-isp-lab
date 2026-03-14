---
sidebar_position: 6
sidebar_label: 7. ESM
---

# 7. ESM - Pruebas de Suscriptores

## 7.1 Prerrequisitos

Antes de ejecutar estas pruebas, asegúrate de tener:

- la imagen Radius (véase [RADIUS / AAA](../radius))
- el usuario PPPoE base `test@test.com`

Luego espera a que `ont2` complete el login PPPoE y valida en los BNG:

```text
show service active-subscribers
```

## 7.2 Escenario Validado: Baja y Alta PPPoE con Containerbot

En el `lab.yml`, ONT2 está configurado como PPPoE:

```yaml
ont2:
  kind: linux
  image: ghcr.io/abelperezr/ont-ds:0.3
  env:
    CONNECTION_TYPE: pppoe
    WAN1_MODE: "ipv6"
    PPP_USER: "test@test.com"
    PPP_PASS: "testlab123"
    VLAN_ID: "150"
    IFPHY: "eth1"
    IFLAN: "eth2"
    MAC_ADDRESS: "00:D0:F6:01:01:04"
```

Este procedimiento puede realizarse directamente con los scripts ubicados en `small-isp-lab/configs/cbot/scripts` (para ello hay que tener Python instalado y sus librerías):

```bash
python3 manage_authorize.py list
python3 manage_authorize.py show 'test@test.com'
```

```text
abel@abel:~/small-isp-lab/configs/cbot/scripts$ python3 manage_authorize.py show 'test@test.com'
# ============================================================================
# ONT2-WAN1
# ============================================================================
"test@test.com"      Cleartext-Password := "testlab123"
                    Framed-Pool = "cgnat",
                    Framed-IPv6-Pool = "IPv6",
                    Alc-Delegated-IPv6-Pool = "IPv6",
                    Alc-SLA-Prof-str = "100M",
                    Alc-Subsc-Prof-str = "subprofile",
                    Alc-Subsc-ID-Str = "ONT-002-PPPOE",
                    Alc-MSAP-Interface = "ipv6-only",
                    Fall-Through = Yes
```

Opción alternativa: ejecutar directamente desde `containerbot`:

```bash
docker exec -it containerbot python3 /app/scripts/manage_authorize.py list
docker exec -it containerbot python3 /app/scripts/manage_authorize.py show 'test@test.com'
```

O desde `containerbot`, si seguiste los pasos para sincronizarlo con Telegram:

![Resultado de `manage_authorize.py show test@test.com`](/img/IMAGEN1.png)

Validar el suscriptor en el BNG:

```text
A:admin@MASTER# show service active-subscribers

===============================================================================
Active Subscribers
===============================================================================
Subscriber ONT-002
           (subprofile)
...
2001:db8:100::2/128
              00:d0:f6:01:01:04  PPP 1              DHCP6        9998       Y
2001:db8:200:1::/64
              00:d0:f6:01:01:04  PPP 1              DHCP6-PD-MR  9998       Y
===============================================================================
```

:::note[Valores de ejemplo]
Las direcciones IPv4/IPv6 y los prefijos mostrados en esta sección son **ejemplos de referencia**. Según el estado previo del laboratorio, los recursos disponibles del equipo anfitrión y la secuencia de reconexiones, pueden variar entre ejecuciones.
:::

Validar direccionamiento en `ont2`:

```bash
docker exec ont2 sh -lc 'ip ad show ppp0; echo ---; ip -6 route'
```

```text
docker exec ont2 sh -lc 'ip ad show ppp0; echo ---; ip -6 route'
58: ppp0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1492 qdisc fq_codel state UNKNOWN group default qlen 3
    link/ppp
    inet6 2001:db8:100::3/128 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::a877:b9ac:64af:934 peer fe80::7e20:64ff:fe84:8365/128 scope link nodad
       valid_lft forever preferred_lft forever
---
2001:db8:100::3 dev ppp0 proto kernel metric 256 pref medium
fe80::7e20:64ff:fe84:8365 dev ppp0 proto kernel metric 256 pref medium
fe80::a877:b9ac:64af:934 dev ppp0 proto kernel metric 256 pref medium
fe80::/64 dev eth1 proto kernel metric 256 pref medium
fe80::/64 dev eth1.150 proto kernel metric 256 pref medium
default dev ppp0 metric 1024 pref medium
```

:::note[Valores de ejemplo]
El direccionamiento mostrado arriba es un ejemplo. La IPv6 WAN y el prefijo delegado pueden cambiar entre pruebas sin que eso implique una falla del ATP.
:::

Dar de baja inmediata al suscriptor:

```bash
python3 manage_authorize.py deactivate 'test@test.com'
```

Opción alternativa: ejecutar directamente desde `containerbot`:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py --disconnect-debug disconnect "test@test.com"'
```

O desde `containerbot`:

```text
/run manage_authorize.py deactivate test@test.com
```

![Resultado de `manage_authorize.py deactivate test@test.com`](/img/IMAGEN2.png)

Validar la baja en el BNG:

```text
A:admin@MASTER# show service active-subscribers
```

Resultado esperado:

- `ONT-002` ya no aparece
- el bot muestra previamente `Disconnect-ACK`

Si `ONT-002` sigue visible:

- la autorización futura ya quedó eliminada, pero la sesión activa no fue expulsada todavía
- en ese caso, lanzar `disconnect` explícito y repetir la validación en el BNG

Validar la baja en `ont2`:

```bash
docker exec ont2 sh -lc 'ip ad show ppp0; echo ---; tail -n 40 /var/log/ppp/pppd.log'
```

```text
 docker exec ont2 sh -lc 'ip ad show ppp0; echo ---; tail -n 40 /var/log/ppp/pppd.log'
66: ppp0: <POINTOPOINT,MULTICAST,NOARP> mtu 1500 qdisc noop state DOWN group default qlen 3
    link/ppp
---
2026-03-08 21:50:37 [pppoe] Timeout esperando ppp0
2026-03-08 21:50:37 [pppoe] Falló la conexión PPPoE
2026-03-08 21:50:37 [pppoe] Falló la conexión PPPoE
2026-03-08 21:50:37 [pppoe] Últimas líneas del log pppd:
sent [LCP TermAck id=0xb3]
Send PPPOE Discovery V1T1 PADR
Connect: ppp0
```

Reactivar el suscriptor:

```bash
python3 manage_authorize.py add 'test@test.com' \
  --title 'ONT2-WAN1' \
  --password 'testlab123' \
  --framed-pool 'cgnat' \
  --framed-ipv6-pool 'IPv6' \
  --delegated-ipv6-pool 'IPv6' \
  --subscriber-id 'ONT-002' \
  --subscriber-profile 'subprofile' \
  --msap-interface 'ipv6-only' \
  --sla-profile '100M'
```

O con `docker exec` sobre `containerbot`:

```bash
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

O desde `containerbot`:

```text
/run manage_authorize.py add test@test.com --title ONT2-WAN1 --password testlab123 --framed-pool cgnat --framed-ipv6-pool IPv6 --delegated-ipv6-pool IPv6 --subscriber-id ONT-002 --subscriber-profile subprofile --msap-interface ipv6-only --sla-profile 100M
```

![Resultado de `manage_authorize.py add test@test.com`](/img/IMAGEN3.png)

Importante:

- `--subscriber-profile 'subprofile'` es obligatorio para que el alta vuelva a reconstruir correctamente el subscriber en el BNG.
- como ventana de convergencia, esperar entre **10 y 120 segundos** antes de ejecutar lo siguiente
- en PCs con más recursos, la recuperación puede ocurrir bastante antes, incluso en pocos segundos

8. Validar nuevamente BNG y ONT:

```text
A:admin@MASTER# show service active-subscribers
```

```bash
docker exec ont2 sh -lc 'ip ad show ppp0; echo ---; ip -6 route'
```

Resultado esperado:

- `ONT-002` vuelve a aparecer en el BNG
- `ont2` recupera `2001:db8:100::2/128`

:::note[Valores de ejemplo]
La IPv6 recuperada en `ont2` se muestra como ejemplo. El valor exacto puede variar entre reconexiones.
:::

9. Editar el `subscriber-id`:

```bash
docker exec containerbot python3 /app/scripts/manage_authorize.py edit 'test@test.com' \
  --subscriber-id 'ONT-002-PPPOE'
```

10. Verificar el cambio en RADIUS:

```bash
docker exec radius cat /etc/raddb/mods-config/files/authorize
```

Resultado esperado:

- el bloque de `test@test.com` debe mostrar `Alc-Subsc-ID-Str = "ONT-002-PPPOE"`

### 7.2.1 Escenario Validado: Corte y Reconexión IPoE de `ONT-001`

Este flujo quedó validado para las tres WAN IPoE de `ont1` usando `docker exec` sobre `containerbot`, sin necesidad de ejecutar `clear service` manual en el BNG.

Base operativa:

- `WAN1` `00:d0:f6:01:01:01` `ipv6-only`
- `WAN2` `00:d0:f6:01:01:02` `dual-stack`
- `WAN3` `00:d0:f6:01:01:03` `vip`

#### Cortar una WAN IPoE

Ejecutar una a una.

Ejemplos:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py --disconnect-debug deactivate 00:d0:f6:01:01:01'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py --disconnect-debug deactivate 00:d0:f6:01:01:02'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py --disconnect-debug deactivate 00:d0:f6:01:01:03'
```

Resultado esperado:

- `containerbot` muestra `Disconnect-Request`
- el BNG responde `Disconnect-ACK`
- sólo desaparece la WAN seleccionada en `show service active-subscribers`
- las otras WAN de `ONT-001` permanecen activas
- `ONT-002` no se afecta

Validación rápida en el BNG:

```text
show service active-subscribers | match 00:d0:f6:01:01:01
show service active-subscribers | match 00:d0:f6:01:01:02
show service active-subscribers | match 00:d0:f6:01:01:03
show service active-subscribers | match 00:d0:f6:01:01:04
```

#### Reactivar una WAN IPoE

Ejemplos:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py add 00:d0:f6:01:01:01 \
  --title ONT1-WAN1-BNG1 \
  --password testlab123 \
  --framed-ipv6-pool IPv6 \
  --delegated-ipv6-pool IPv6 \
  --subscriber-id ONT-001 \
  --subscriber-profile subprofile \
  --msap-interface ipv6-only \
  --sla-profile 100M'

docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py add 00:d0:f6:01:01:02 \
  --title ONT1-WAN2-BNG1 \
  --password testlab123 \
  --framed-pool cgnat \
  --framed-ipv6-pool IPv6-dual-stack \
  --delegated-ipv6-pool IPv6-dual-stack \
  --subscriber-id ONT-001 \
  --subscriber-profile subprofile \
  --msap-interface dual-stack \
  --sla-profile 100M'

docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py add 00:d0:f6:01:01:03 \
  --title ONT1-WAN3-BNG1 \
  --password testlab123 \
  --framed-pool one-to-one \
  --subscriber-id ONT-001 \
  --subscriber-profile subprofile \
  --msap-interface vip \
  --sla-profile 100M'
```

Validación en `ont1`:

```bash
docker exec ont1 sh -lc 'curl -sS http://127.0.0.1:8080/api/status'
```

Resultado esperado:

- `WAN1` vuelve con IPv6 WAN y PD activo
- `WAN2` vuelve con IPv4 + IPv6
- `WAN3` vuelve con IPv4
- la WAN reaparece en `show service active-subscribers`

:::tip[Ventana de convergencia]
La ONT puede recuperar primero la dirección IP y unos segundos después reaparecer en el BNG. En las pruebas validadas, la recuperación ocurrió sin `clear` manual y dentro de una ventana corta de convergencia.
:::

## 7.3 Notas Operativas

- `delete` solo elimina la autorización para autenticaciones futuras
- `deactivate` es la operación recomendada para simular suspensión inmediata
- `deactivate` debe validarse siempre contra dos señales: `Disconnect-ACK` y desaparición de la sesión en el BNG
- si solo se elimina la entrada en FreeRADIUS pero la sesión sigue activa, usar `disconnect` explícito contra el mismo identificador
- para sesiones IPoE, usar la MAC suele ser la forma más robusta de identificar al subscriber
- después de editar atributos de una sesión ya activa, puede ser necesario forzar `disconnect` para que el nuevo valor se refleje en la siguiente sesión
- el laboratorio usa FreeRADIUS oficial derivado, con `radclient`, SSH y accounting habilitado para este flujo

## 7.4 Fallback a la LUDB

El fallback a LUDB quedó verificado para los **tres subscribers IPoE de `ont1`** forzando renews desde CLI contra la API del ONT. El caso PPPoE no hace parte de esta prueba porque la entrada LUDB `ONT2-PPPOE` sigue comentada en `configs/sros/master.txt` y `configs/sros/slave.txt`.

### 7.4.1 Detener RADIUS y limpiar el estado en el BNG Master

```bash
docker stop radius
```

```text
clear service id "9998" ipoe session all
clear router "9998" dhcp6 local-dhcp-server "suscriptores_v6" leases all
```

Resultado esperado:

- las sesiones IPoE activas desaparecen temporalmente
- los leases DHCPv6 quedan en cero
- `show aaa radius-server-policy "radius_policy"` puede mostrar el servidor en `probing` o `out-of-service` según el temporizador de health-check

Ejemplo observado:

```text
[/]
A:admin@MASTER# show router 9998 dhcp6 local-dhcp-server "suscriptores_v6" leases

===============================================================================
Leases for DHCPv6 server suscriptores_v6
===============================================================================
No leases found
===============================================================================
```

### 7.4.2 Forzar renews desde CLI en `ont1`

En lugar de usar la UI, se puede invocar la misma lógica con `curl` contra la API local del ONT.

Desde tu laptop o desde el host donde corre Containerlab, usa el puerto publicado `127.0.0.1:8090`:

```bash
curl -sS -X POST http://127.0.0.1:8090/api/dhcp6/renew/1
curl -sS -X POST http://127.0.0.1:8090/api/dhcp/renew/2
curl -sS -X POST http://127.0.0.1:8090/api/dhcp6/renew/2
curl -sS -X POST http://127.0.0.1:8090/api/dhcp/renew/3
```

Si ejecutas los `curl` **dentro del contenedor `ont1`**, el servicio escucha en `127.0.0.1:8080`. El `lab.yml` publica ese puerto como `8090:8080` para usarlo desde el host.

Salida observada:

```json
{"success": true, "message": "DHCPv6 renewal initiated on eth1.150"}
{"success": true, "message": "DHCP renewal initiated on eth3.200"}
{"success": true, "message": "DHCPv6 renewal initiated on eth3.200"}
{"success": true, "message": "DHCP renewal initiated on eth4.300"}
```

:::tip[Ventana de convergencia]
Después de lanzar los renews, esperar entre **10 y 30 segundos** antes de validar la reconstrucción de sesiones y leases.

En hosts con más recursos, la recuperación puede ocurrir bastante más rápido.
:::

### 7.4.3 Validar que la LUDB reconstruyó los subscribers IPoE

Verifica en el BNG Master:

```text
show service id 9998 ipoe session
show router 9998 dhcp6 local-dhcp-server "suscriptores_v6" leases
show service active-subscribers
```

Resultado observado:

```text
[/]
A:admin@MASTER# show service id 9998 ipoe session

===============================================================================
IPoE sessions for svc-id 9998
===============================================================================
[1/1/c2/1:50.150]                00:d0:f6:01:01:01
[1/1/c2/1:51.200]                00:d0:f6:01:01:02
[1/1/c2/1:52.300]                00:d0:f6:01:01:03
-------------------------------------------------------------------------------
Number of sessions : 3
===============================================================================
```

```text
[/]
A:admin@MASTER# show router 9998 dhcp6 local-dhcp-server "suscriptores_v6" leases

===============================================================================
Leases for DHCPv6 server suscriptores_v6
===============================================================================
2001:db8:100::X/128
2001:db8:200::/64
2001:db8:cccc::1/128
2001:db8:dddd::/64
-------------------------------------------------------------------------------
4 leases found
===============================================================================
```

```text
[/]
A:admin@MASTER# show service active-subscribers

===============================================================================
Active Subscribers
===============================================================================
00:d0:f6:01:01:01|1/1/c2/1:50.150
  2001:db8:100::X/128
  2001:db8:200::/64
00:d0:f6:01:01:02|1/1/c2/1:51.200
  100.80.0.4
  2001:db8:cccc::1/128
  2001:db8:dddd::/64
00:d0:f6:01:01:03|1/1/c2/1:52.300
  192.168.5.4
-------------------------------------------------------------------------------
Number of active subscribers : 3
===============================================================================
```

:::note[Subscriber-ID durante fallback LUDB]
Durante el fallback a LUDB, el `subscriber-id` puede aparecer con formato `MAC|SAP` en lugar de `ONT-001`. Esto ocurre porque la sesión entra usando un usuario por defecto de la LUDB y el BNG reconstruye la identidad operativa a partir de la MAC y del SAP.
:::

### 7.4.4 Validar el estado final en el ONT

Desde tu laptop o desde el host, la consulta se hace por el puerto publicado `8090`:

```bash
curl -sS http://127.0.0.1:8090/api/status
```

Si ejecutas la consulta dentro del contenedor `ont1`, usa `http://127.0.0.1:8080/api/status`.

Puntos a comprobar:

- `WAN1` recupera una dirección del pool `2001:db8:100::/56`
- el PD activo vuelve a ser `2001:db8:200::/64`
- la LAN `eth2` anuncia `2001:db8:200::1/64`
- `WAN2` recupera `100.80.0.4/29` y `2001:db8:cccc::1/128`
- `WAN3` recupera `192.168.5.4/29`

:::note[Valores de ejemplo]
Las direcciones mostradas en esta validación son ejemplos. Tras renovar leases o reconstruir sesiones, los valores exactos pueden cambiar y seguir siendo válidos.
:::

### 7.4.5 Restaurar RADIUS

```bash
docker start radius
```

## 7.5 Verificar políticas y perfiles de suscriptor

Verifica las políticas y perfiles asociados al subscriber management.

Comandos relacionados:

- `show subscriber-mgmt authentication "autpolicy"`
- `show subscriber-mgmt authentication "autpolicy" association`
- `show subscriber-mgmt radius-accounting-policy "accounting"`
- `show subscriber-mgmt radius-accounting-policy "accounting" association`
- `show subscriber-mgmt sub-profile`
- `show subscriber-mgmt sla-profile`
- `show subscriber-mgmt sub-ident-policy "subident"`
- `show subscriber-mgmt ipoe-session-policy "ipoe"`
- `show subscriber-mgmt ppp-policy "pppoe"`

```text
[gl:/configure]
A:admin@MASTER# show subscriber-mgmt authentication "autpolicy"

===============================================================================
Authentication Policy autpolicy
===============================================================================
Description          : (Not Specified)
Re-authentication    : Yes                 Username Format      : MAC Address
PPPoE Access Method  : PAP/CHAP            Username Mac-Format  : "aa:"
PPP-Username Oper    : None
PPP-Domain-Name      : N/A
Username Oper        : None
Domain-Name          : N/A
Acct-Stop-On-Fail    :
RADIUS Server Policy : "radius_policy"
Fallback Action      : user-db clientes
Force Probing        : false
Last Mgmt Change     : 03/08/2026 14:00:16
-------------------------------------------------------------------------------
Include Radius Attributes
-------------------------------------------------------------------------------
Remote Id            : Yes                 Circuit Id           : No
NAS Port Id          : Yes                 NAS Identifier       : Yes
PPPoE Service Name   : Yes                 DHCP Vendor Class Id : Yes
Access Loop Options  : Yes                 MAC Address          : Yes
NAS Port Prefix      : None                NAS Port Suffix      : None
NAS-Port-Type        : Yes (standard)      Acct Session Id      : Session
Calling Station Id   : Yes (sap-string)    Called Station Id    : Yes
Tunnel Server Attr   : Yes                 DHCP Options         : Yes
NAS Port             : No                  SAP Session Index    : No
Wifi SSID VLAN       : No
DHCP6 Options        : No
Num-Attached-UEs     : No
Xcon Tunnel Home Addr: No
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show subscriber-mgmt authentication "autpolicy" association

===============================================================================
Authentication Policy autpolicy
===============================================================================
-------------------------------------------------------------------------------
SAP Associations
-------------------------------------------------------------------------------
Service-Id : 2 (VPLS)
 - SAP : 1/1/c2/1:50.*
 - SAP : 1/1/c2/1:51.*
 - SAP : 1/1/c2/1:52.*

-------------------------------------------------------------------------------
Interface Associations
-------------------------------------------------------------------------------
Service-Id : 9998 (VPRN)
 - If Name : dual-stack
 - If Name : ipv6-only
 - If Name : vip
```

```text
[gl:/configure]
A:admin@MASTER# show subscriber-mgmt radius-accounting-policy "accounting"

===============================================================================
Radius Accounting Policy accounting
===============================================================================
Description          : (Not Specified)
Update Interval      : 720 min.              Mcs Interval       : 0 min.
Oper Interval Jitter : 10%                   Configured Jitter  : 10%
Host Accounting      : None                  Session-id Format  : Number
Queue Instance Acct  : None                  Session Acct       : Interim-Host
Acct-tunn-conn format: %n
Delay Start Time     : None
RADIUS Server Policy : "radius_policy"
Triggered Updates    : None
Last Mgmt Change     : 03/08/2026 14:00:16
-------------------------------------------------------------------------------
Include Radius Attributes
-------------------------------------------------------------------------------
Framed IP Address    : Yes                   Framed Ip Netmask  : Yes
Subscriber Id        : Yes                   Circuit Id         : Yes
Remote Id            : Yes                   NAS Port Id        : Yes
NAS Identifier       : Yes                   Sub-Profile        : Yes
SLA-Profile          : Yes                   User-Name          : Yes
SPI Sharing Id       : No
Calling Station Id   : No                    Called Station Id  : Yes
NAS Port Prefix      : None
NAS Port Suffix      : None
Tunnel Server Attr   : Yes                   Tunnel Client Attr : No
NAS-port             : No                    NAS-Port-Type      : Yes (standar*
NAT-Port-Range       : Yes                   MAC Address        : Yes
Acct-delay-time      : Yes                   Acc-authentic      : Yes
IPv6-Address         : Yes                   Framed-Interface-Id: No
Delegated-IPv6-Prefix: Yes                   Framed-IPv6-Prefix : Yes
Wi-fi SSID VLAN      : No
Wi-fi RSSI           : No                    Alc-Acct-Tr-Reason : Yes
DHCP Vendor Class Id : No
Framed IPv6 Route    : Yes                   Framed Route       : Yes
All-auth-session-addr: No                    Access-loop-options: No
Detailed-Acct-Attr   : Yes                   Std-Acct-Attr      : Yes
v6-aggregate-stats   : No                    Alc-Error-Code     : No
Num-Attached-UEs     : No                    Steering-Profile   : No
BRG-Num-Act-Sess     : No
Bonding-Id           : No                    Active-Connections : No
Firewall-Info        : No
Xcnt-Tunnel-Home-Addr: No
Bearer-Fteid         : No
User-Location-Info   : No
LAC fragmentation    : No
Rat-type             : No
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show subscriber-mgmt radius-accounting-policy "accounting" association

===============================================================================
Radius Accounting Policy accounting
===============================================================================
-------------------------------------------------------------------------------
Sub-Profile Associations
-------------------------------------------------------------------------------
subprofile
-------------------------------------------------------------------------------
Number of Subscriber Profiles : 1
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show subscriber-mgmt sub-profile

===============================================================================
Subscriber Profiles
===============================================================================
Subscriber                       Description
-------------------------------------------------------------------------------
subprofile
-------------------------------------------------------------------------------
Number of Subscriber Profiles : 1
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show subscriber-mgmt sla-profile

===============================================================================
SLA Profiles
===============================================================================
Name                             Description
-------------------------------------------------------------------------------
100M
100M-VIP
-------------------------------------------------------------------------------
Number of SLA Profiles : 2
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show subscriber-mgmt sub-ident-policy "subident"

===============================================================================
Subscriber Identification Policy subident
===============================================================================
Strings-From-Option : No

-------------------------------------------------------------------------------
Sub Profile Map (Use direct map as default)
-------------------------------------------------------------------------------
Key                              Sub profile
-------------------------------------------------------------------------------
No mappings configured.

-------------------------------------------------------------------------------
SLA Profile Map (Use direct map as default)
-------------------------------------------------------------------------------
Key                              SLA profile
-------------------------------------------------------------------------------
No mappings configured.

-------------------------------------------------------------------------------
App Profile Map
-------------------------------------------------------------------------------
Key                              App profile
-------------------------------------------------------------------------------
No mappings configured.

-------------------------------------------------------------------------------
Python Scripts
-------------------------------------------------------------------------------
#         Admin Oper  Script
          State State Name
-------------------------------------------------------------------------------
Primary   Down  Down  N/A
Secondary Down  Down  N/A
Tertiary  Down  Down  N/A
```

```text
[gl:/configure]
A:admin@MASTER# show subscriber-mgmt ipoe-session-policy "ipoe"

===============================================================================
IPoE Session Policy "ipoe"
===============================================================================
Description           : (Not Specified)
Last Mgmt Change      : 03/08/2026 14:00:16
Session Key           : sap-mac
Session Timeout       : unlimited
Circuit-Id from
authentication        : no
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show subscriber-mgmt ppp-policy "pppoe"

===============================================================================
PPP Policy "pppoe"
===============================================================================
Description          : (Not Specified)
Last Mgmt Change     : 03/08/2026 14:00:16
PPP-mtu              : 1500                    Force PPP-mtu >1492  : No
Keepalive Interval   : 10s                     Keepalive Multiplier : 4
Disable AC-Cookies   : No                      PADO Delay           : 0msec
Max Sessions-Per-Mac : 1                       Reply-On-PADT        : Yes
Allow Same CID       : No                      Re-establish Session : Disabled
Max Sessions-Per-Cid : N/A
Allow No CID         : N/A
PPP-Authentication   : pref-PAP                PPP-CHAP Challenge   : 32 - 64
PPP-Init-Delay (ms)  : 50                      IPCP negotiate subnet: No
Unique SIDs-Per-SAP  : disabled                Reject-Disabled-Ncp  : No
Ignore-Magic-Num     : No                      Session Timeout      : unlimited
SID Allocation       : sequential
PADO AC-Name         : (Not Specified)
Default username     : (Not Specified)
Default password     : (Not Specified)
NCP Renegotiation    : terminate-session       Ignore-Identifier    : No

-------------------------------------------------------------------------------
PPP Custom Options
-------------------------------------------------------------------------------
Protocol Number Value
-------------------------------------------------------------------------------
No options configured.

-------------------------------------------------------------------------------
MLPPP
-------------------------------------------------------------------------------
Accept MRRU                 : false
Request short sequence nr.  : false
Endpoint class              : null
Endpoint address            : (Not Specified)
-------------------------------------------------------------------------------
```

## 7.6 Pruebas DHCP

Verifica los servidores DHCP, el estado de los pools y las leases activas.

Comandos relacionados:

- `show router 9998 dhcp servers`
- `show router 9998 dhcp6 servers`
- `show router 9998 dhcp local-dhcp-server "suscriptores" summary`
- `show router 9998 dhcp6 local-dhcp-server "suscriptores_v6" summary`
- `show router 9998 dhcp local-dhcp-server "suscriptores" leases`
- `show router 9998 dhcp6 local-dhcp-server "suscriptores_v6" leases`

```text
[gl:/configure]
A:admin@MASTER# show router 9998 dhcp servers

==================================================================
Overview of DHCP Servers
==================================================================
Active Leases:      8
Maximum Leases:     786432

Router              Server                           Admin State
------------------------------------------------------------------
Service: 9998       suscriptores                     inService
==================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router 9998 dhcp6 servers

==================================================================
Overview of DHCP Servers
==================================================================
Active Leases:      8
Maximum Leases:     786432

Router              Server                           Admin State
------------------------------------------------------------------
Service: 9998       suscriptores_v6                  inService
==================================================================
```

```text
A:admin@MASTER# show router 9998 dhcp local-dhcp-server "suscriptores" summary

===============================================================================
DHCP server suscriptores  router 9998
===============================================================================
Admin State            : inService
Operational State      : inService
Persistency State      : shutdown
User Data Base         : N/A
Use gateway IP address : enabled (scope subnet)
Use pool from client   : enabled
Send force-renewals    : disabled
Creation Origin        : manual
Lease Hold Time        : 0h0m0s
Lease Hold Time For    : N/A
User-ident             : mac-circuit-id

Failover Admin State   : outOfService
Failover Oper State    : shutdown
Failover Persist Key   : N/A
Administrative MCLT    : 0h10m0s
Operational MCLT       : 0h10m0s
Startup wait time      : 0h2m0s
Partner down delay     : 23h59m59s
  Ignore MCLT          : disabled

-------------------------------------------------------------------------------
Pool name : cgnat
-------------------------------------------------------------------------------
Failover Admin State   : inService
Failover Oper State    : normal
Failover Persist Key   : N/A
Administrative MCLT    : 0h10m0s
Operational MCLT       : 0h10m0s
Startup wait time      : 0h2m0s
Partner down delay     : 1h0m0s
  Ignore MCLT          : enabled
-------------------------------------------------------------------------------
Subnet                 Free     %    Stable   Declined Offered  Rem-pend Drain
-------------------------------------------------------------------------------
100.80.0.0/29      (L) 2        66%  1        0        0        0        N
                   (R) N/A           0        N/A      N/A      N/A      N

Totals for pool        2        66%  1        0        0        0
-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
Pool name : one-to-one
-------------------------------------------------------------------------------
Failover Admin State   : inService
Failover Oper State    : normal
Failover Persist Key   : N/A
Administrative MCLT    : 0h10m0s
Operational MCLT       : 0h10m0s
Startup wait time      : 0h2m0s
Partner down delay     : 1h0m0s
  Ignore MCLT          : enabled
-------------------------------------------------------------------------------
Subnet                 Free     %    Stable   Declined Offered  Rem-pend Drain
-------------------------------------------------------------------------------
192.168.5.0/29     (L) 2        66%  1        0        0        0        N
                   (R) N/A           0        N/A      N/A      N/A      N

Totals for pool        2        66%  1        0        0        0
-------------------------------------------------------------------------------

Totals for server      4        66%  2        0        0        0

-------------------------------------------------------------------------------
Interface associations
Interface                        Admin
-------------------------------------------------------------------------------
loopback                         Up

-------------------------------------------------------------------------------
Local Address Assignment associations
Group interface                  Admin
-------------------------------------------------------------------------------
No associated firewall domains found.
===============================================================================
```

```text
A:admin@MASTER# show router 9998 dhcp6 local-dhcp-server "suscriptores_v6" summary

===============================================================================
DHCP server suscriptores_v6  router 9998
===============================================================================
Admin State            : inService
Operational State      : inService
Persistency State      : shutdown
User Data Base         : N/A
Use Link Address       : enabled (scope pool)
Use pool from client   : enabled
Creation Origin        : manual
Lease Hold Time        : 0h0m0s
Lease Hold Time For    : N/A
User-ident             : duid
Interface-id-mapping   : disabled
Ignore-rapid-commit    : disabled
Allow-lease-query      : disabled
Auto-provisioned       : false

Failover Admin State   : outOfService
Failover Oper State    : shutdown
Failover Persist Key   : N/A
Administrative MCLT    : 0h10m0s
Operational MCLT       : 0h10m0s
Startup wait time      : 0h2m0s
Partner down delay     : 23h59m59s
  Ignore MCLT          : disabled

-------------------------------------------------------------------------------
Pool name : IPv6
-------------------------------------------------------------------------------
Failover Admin State   : inService
Failover Oper State    : normal
Failover Persist Key   : N/A
Administrative MCLT    : 0h10m0s
Operational MCLT       : 0h10m0s
Startup wait time      : 0h2m0s
Partner down delay     : 1h0m0s
  Ignore MCLT          : enabled
-------------------------------------------------------------------------------
Prefix
                                     Stable   Declined Advert   Rem-pend Drain
-------------------------------------------------------------------------------
2001:db8:100::/56
                                (L)  2        0        0        0        N
2001:db8:200::/48
                                (L)  2        0        0        0        N

Totals for pool                      4        0        0        0
-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
Pool name : IPv6-dual-stack
-------------------------------------------------------------------------------
Failover Admin State   : inService
Failover Oper State    : normal
Failover Persist Key   : N/A
Administrative MCLT    : 0h10m0s
Operational MCLT       : 0h10m0s
Startup wait time      : 0h2m0s
Partner down delay     : 1h0m0s
  Ignore MCLT          : enabled
-------------------------------------------------------------------------------
Prefix
                                     Stable   Declined Advert   Rem-pend Drain
-------------------------------------------------------------------------------
2001:db8:cccc::/56
                                (L)  1        0        0        0        N
2001:db8:dddd::/48
                                (L)  1        0        0        0        N

Totals for pool                      2        0        0        0
-------------------------------------------------------------------------------

Totals for server                    6        0        0        0

-------------------------------------------------------------------------------
Interface associations
Interface                        Admin
-------------------------------------------------------------------------------
loopback                         Up

-------------------------------------------------------------------------------
Local Address Assignment associations
Group interface                  Admin
-------------------------------------------------------------------------------
No associated firewall domains found.
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router 9998 dhcp local-dhcp-server "suscriptores" leases

===============================================================================
Leases for DHCP server suscriptores router 9998
===============================================================================
IP Address      Lease State       Mac Address       Remaining   Clnt  Fail
  PPP user name/Opt82 Circuit Id                    LifeTime    Type  Ctrl
  User-db/Sticky-lease Hostname
-------------------------------------------------------------------------------
100.80.0.2      stable            00:d0:f6:01:01:02 5476d9h40m  dhcp  local

192.168.5.2     stable            00:d0:f6:01:01:03 5476d9h40m  dhcp  local

-------------------------------------------------------------------------------
2 leases found
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router 9998 dhcp6 local-dhcp-server "suscriptores_v6" leases

===============================================================================
Leases for DHCPv6 server suscriptores_v6
===============================================================================
IP Address/Prefix                          Lease State       Remaining   Fail
  Link-local Address                                         LifeTime    Ctrl
-------------------------------------------------------------------------------
2001:db8:100::2/128
  fe80::2d0:f6ff:fe01:101                  stable            1d3h40m     local
2001:db8:100::3/128
  fe80::a877:b9ac:64af:934                 stable            1d4h2m      local
2001:db8:200:1::/64
  fe80::2d0:f6ff:fe01:101                  stable            1d3h40m     local
2001:db8:200:2::/64
  fe80::a877:b9ac:64af:934                 stable            1d4h2m      local
2001:db8:cccc::1/128
  fe80::2d0:f6ff:fe01:102                  stable            1d3h40m     local
2001:db8:dddd::/64
  fe80::2d0:f6ff:fe01:102                  stable            1d3h40m     local
-------------------------------------------------------------------------------
6 leases found
===============================================================================
```

## 7.7 Pruebas IPoE y PPP

Verifica las sesiones activas de IPoE y PPP dentro del servicio 9998.

```text
[gl:/configure]
A:admin@MASTER# show service id 9998 ipoe session

===============================================================================
IPoE sessions for svc-id 9998
===============================================================================
Sap Id                           Mac Address         Up Time         MC-Stdby
    Subscriber-Id
        [CircuitID] | [RemoteID]
-------------------------------------------------------------------------------
[1/1/c2/1:50.150]                00:d0:f6:01:01:01   0d 03:14:55
    ONT-001
[1/1/c2/1:51.200]                00:d0:f6:01:01:02   0d 03:15:19
    ONT-001
[1/1/c2/1:52.300]                00:d0:f6:01:01:03   0d 03:15:19
    ONT-001
-------------------------------------------------------------------------------
CID | RID displayed when included in session-key
Number of sessions : 3
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show service id 9998 ppp session

===============================================================================
PPP sessions for service 9998
===============================================================================
User-Name
  Descr.
           Up Time       Type  Termination     IP/L2TP-Id/Interface-Id MC-Stdby
-------------------------------------------------------------------------------
test@test.com
  svc:9998 sap:[1/1/c2/1:50.150] mac:00:d0:f6:01:01:04 sid:1
           0d 02:03:48   oE    local           A8:77:B9:AC:64:AF:09:34
-------------------------------------------------------------------------------
No. of PPP sessions: 1
===============================================================================
```
