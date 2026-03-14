---
sidebar_position: 5
sidebar_label: 6. SRRP y BGP
---

# 6. SRRP y BGP - Pruebas Generales

:::note[Nota]
Esta prueba puede ser realizada contra el enlace entre BNGs o el enlace hacia la OLT. Por ello existen los scripts `olt-to-bng1-down.sh` / `olt-to-bng1-up.sh`.

:::
## 6.1 Verificación de Script EHS

:::warning[Atención]
Cada vez que el script EHS se ejecute, se guardará un archivo de resultados dentro del BNG, en `cf3:\resultsSRRPSwitch`, con formato `resultsSRRPSwitch_20260308-000025-UTC.665049.out`. Esto ocurre al inicio del despliegue del laboratorio y cuando ejecutamos las pruebas de SRRP. Estos archivos ahora son efímeros y desaparecen cuando se destruye el lab.

:::
Verificar que el script está configurado y operativo:

```text
A:admin@MASTER# show system script-control script-policy "Policy-SRRPSwitch"

===============================================================================
Script-policy Information
===============================================================================
Script-policy                : Policy-SRRPSwitch
Script-policy Owner          : TiMOS CLI
Administrative status        : enabled
Operational status           : enabled
Script                       : N/A
Script owner                 : N/A
Python script                : srrp_bgp_policy
Source location              : cf3:\scripts\srrp_bgp_policy.py
Results location             : cf3:\resultsSRRPSwitch
...
```

## 6.2 Revisión de Configuraciones por Default

### Validación en MASTER

```text
show srrp
show router 9999 bgp neighbor 172.16.1.1 detail | match "Export Policy"
show router 9999 bgp neighbor 172.16.2.1 detail | match "Export Policy"
show router 9999 bgp neighbor 172.16.1.1 advertised-routes
show router 9999 bgp neighbor 172.16.2.1 advertised-routes
```

### Validación en SLAVE

```text
show srrp
show router 9999 bgp neighbor 172.16.1.3 detail | match "Export Policy"
show router 9999 bgp neighbor 172.16.2.3 detail | match "Export Policy"
show router 9999 bgp neighbor 172.16.1.3 advertised-routes
show router 9999 bgp neighbor 172.16.2.3 advertised-routes
```

## 6.3 Validación del Sistema EHS para SRRP

### Procedimiento: Apagar interfaz MASTER

Se puede ejecutar de dos maneras equivalentes:

**Opción 1: Desde terminal**

Esta opción requiere que el host desde el que ejecutas el script tenga instaladas las librerías de Python necesarias, al menos:

```bash
python3 -m pip install pygnmi
```

Si no quieres instalar dependencias en tu host, usa la **Opción 2** desde Containerbot, que ya incluye las librerías necesarias para este script.

```bash
python3 configs/cbot/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1
```

**Opción 2: Desde Containerbot**

Ejecutar exactamente el mismo script y los mismos parámetros desde el entorno de **Containerbot**. El comando `/run ...` es un comando del bot, no un comando genérico del shell del host:

```bash
/run update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1
```

También puede ejecutarse directamente con `docker exec` sobre el contenedor `containerbot`:

```bash
docker exec -it containerbot python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1
```

Ambas opciones apagarán el puerto `1/1/c1/1` del BNG MASTER, provocando un SRRP switchover.

:::tip[Ventana de convergencia]
Después de apagar la interfaz, esperar entre **5 y 15 segundos** antes de validar `show srrp` y las `Export Policy`.

Para `advertised-routes`, especialmente hacia **Carrier 2**, puede haber un retardo adicional corto. Si todavía aparece el AS-Path anterior, esperar hasta **15 segundos** y volver a consultar.
:::

![Apagar interface desde Containerbot menu basico](/img/SRRP1.png)

![Apagar interface desde Containerbot opcion general](/img/SRRP2.png)

![Intefaz apagada por Containerbot](/img/SRRP3.png)

### Esperado en MASTER (ahora Backup)

```text
A:admin@MASTER# show srrp

===============================================================================
SRRP Table
===============================================================================
ID        Service        Group Interface                 Admin     Oper
-------------------------------------------------------------------------------
2         9998           dual-stack                      Up        backupShunt
1         9998           ipv6-only                       Up        backupShunt
3         9998           vip                             Up        backupShunt
-------------------------------------------------------------------------------
No. of SRRP Entries: 3
===============================================================================
```

:::note[Variación de texto según release]
En esta maqueta validada, el estado de standby del SRRP se observó como `backupShunt`. Según la release o la vista CLI, el texto puede variar levemente sin cambiar el significado operacional: el nodo sigue en estado de respaldo.
:::

Export policies cambian a Backup (con prepend):

```text
A:admin@MASTER# show router 9999 bgp neighbor 172.16.1.1 detail | match "Export Policy"
Export Policy        : public_to_ISP_C1_Backup

A:admin@MASTER# show router 9999 bgp neighbor 172.16.2.1 detail | match "Export Policy"
Export Policy        : public_to_ISP_C2_Backup
```

Rutas anunciadas hacia Carrier 1 con **PREPEND x3** (AS-Path: 65520 65520 65520 65520):

```text
A:admin@MASTER# show router 9999 bgp neighbor 172.16.1.1 advertised-routes
...
      As-Path: 65520 65520 65520 65520
```

Rutas anunciadas hacia Carrier 2 con **PREPEND x4** (AS-Path: 65520 65520 65520 65520 65520):

```text
A:admin@MASTER# show router 9999 bgp neighbor 172.16.2.1 advertised-routes
...
      As-Path: 65520 65520 65520 65520 65520
```

### Esperado en SLAVE (ahora Master)

```text
A:admin@SLAVE# show srrp

===============================================================================
SRRP Table
===============================================================================
ID        Service        Group Interface                 Admin     Oper
-------------------------------------------------------------------------------
2         9998           dual-stack                      Up        master
1         9998           ipv6-only                       Up        master
3         9998           vip                             Up        master
-------------------------------------------------------------------------------
No. of SRRP Entries: 3
===============================================================================
```

Export policies cambian a Master:

```text
A:admin@SLAVE# show router 9999 bgp neighbor 172.16.1.3 detail | match "Export Policy"
Export Policy        : public_to_ISP_C1_Master

A:admin@SLAVE# show router 9999 bgp neighbor 172.16.2.3 detail | match "Export Policy"
Export Policy        : public_to_ISP_C2_Master
```

Rutas anunciadas hacia Carrier 1 **SIN PREPEND**:

```text
A:admin@SLAVE# show router 9999 bgp neighbor 172.16.1.3 advertised-routes
...
      As-Path: 65520
```

Rutas anunciadas hacia Carrier 2 con **PREPEND x2**:

```text
A:admin@SLAVE# show router 9999 bgp neighbor 172.16.2.3 advertised-routes
...
      As-Path: 65520 65520 65520
```

## 6.4 Levantar Interfaz de MASTER

Se puede ejecutar de dos maneras equivalentes:

**Opción 1: Desde terminal**

Esta opción requiere que el host desde el que ejecutas el script tenga instaladas las librerías de Python necesarias, al menos:

```bash
python3 -m pip install pygnmi
```

Si no quieres instalar dependencias en tu host, usa la **Opción 2** desde Containerbot, que ya incluye las librerías necesarias para este script.

```bash
python3 configs/cbot/scripts/update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c1/1
```

**Opción 2: Desde Containerbot**

Ejecutar exactamente el mismo script y los mismos parámetros desde el entorno de **Containerbot**. El comando `/run ...` es un comando del bot, no un comando genérico del shell del host:

```bash
/run update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c1/1
```

También puede ejecutarse directamente con `docker exec` sobre el contenedor `containerbot`:

```bash
docker exec -it containerbot python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c1/1
```

![Containerbot Levantar interfaz](/img/SRRP4.png)

Verificar que MASTER recupera el rol master y las export policies vuelven a su estado original.

:::tip[Ventana de convergencia]
Después de levantar la interfaz, esperar entre **5 y 15 segundos** antes de validar `show srrp`, `Export Policy` y `advertised-routes`.

Durante esa ventana puede observarse primero el cambio de rol y de policy, y unos segundos después el AS-Path final en `advertised-routes`, sobre todo hacia **Carrier 2**.
:::

:::note[Convergencia transitoria]
Después de levantar la interfaz de `MASTER`, puede existir una ventana corta en la que `show srrp` y las `Export Policy` ya reflejan el retorno al estado normal, pero `show router 9999 bgp neighbor ... advertised-routes` todavía muestre `No Matching Entries Found`.

En las pruebas validadas del laboratorio, ese estado fue transitorio y desapareció unos segundos después, sin requerir intervención adicional.
:::

### Validación en MASTER y SLAVE

Repetir los comandos de la sección **6.2** y verificar que las policies vuelven a su estado por defecto.

## 6.5 Apagar Interfaces de Carrier 1

Se puede ejecutar de dos maneras equivalentes:

**Opción 1: Desde terminal**

Ubicarse en la carpeta `configs/cbot/scripts` y ejecutar:

```bash
./carrier1-to-bng1-down.sh
```

**Opción 2: Desde Containerbot**

Ejecutar este comando desde el entorno de **Containerbot**. El comando `/run ...` es un comando del bot, no un comando genérico del shell del host.

```bash
/run carrier1-to-bng1-down.sh
```

También puede ejecutarse directamente con `docker exec` sobre el contenedor `containerbot`:

```bash
docker exec -it containerbot /app/scripts/carrier1-to-bng1-down.sh
```

![Containerbot Apagar Carrier 1](/img/SRRP5.png)

:::tip[Ventana de convergencia]
Después de apagar Carrier 1, esperar entre **3 y 10 segundos** antes de validar `show router 9999 bgp summary`.
:::

### Esperado en MASTER

El neighbor 172.16.1.1 debe pasar a estado `Connect` (sesión BGP caída):

```text
A:admin@MASTER# show router 9999 bgp summary
...
172.16.1.1
to_CARRIER1
                65501       0    0 00h00m09s Connect
                            0    0
172.16.2.1
to_CARRIER2
                65502      79    0 00h36m04s 2/2/3 (IPv4)
                           85    0           2/2/4 (IPv6)
```

## 6.6 Levantar Interfaces de Carrier 1

Se puede ejecutar de dos maneras equivalentes:

**Opción 1: Desde terminal**

Ubicarse en la carpeta `configs/cbot/scripts` y ejecutar:

```bash
./carrier1-to-bng1-up.sh
```

**Opción 2: Desde Containerbot**

Ejecutar este comando desde el entorno de **Containerbot**. El comando `/run ...` es un comando del bot, no un comando genérico del shell del host.

```bash
/run carrier1-to-bng1-up.sh
```

También puede ejecutarse directamente con `docker exec` sobre el contenedor `containerbot`:

```bash
docker exec -it containerbot /app/scripts/carrier1-to-bng1-up.sh
```

![Containerbot Levantar Carrier 1](/img/SRRP6.png)

Esperar entre **10 y 20 segundos** a que las rutas se establezcan. Carrier 1 debe volver a ser activo con LP 300:

```text
A:admin@MASTER# show router 9999 bgp summary
...
172.16.1.1
to_CARRIER1
                65501       7    0 00h00m09s 2/2/0 (IPv4)
                            3    0           2/2/0 (IPv6)
172.16.2.1
to_CARRIER2
                65502     105    0 00h49m00s 2/0/3 (IPv4)
                          111    0           2/0/4 (IPv6)
```

:::tip[Pruebas sobre BNG SLAVE]
Estas mismas pruebas se pueden ejecutar sobre el BNG SLAVE usando los scripts `carrier1-to-bng2-down.sh` y `carrier1-to-bng2-up.sh`.
:::
