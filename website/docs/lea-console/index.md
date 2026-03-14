---
sidebar_position: 1
---

# LEA Console - Lawful Interception Gateway

## Descripción

La **LEA Console** (Law Enforcement Agency Console) es un sistema compuesto por un script Python (`lig.py`) y una interfaz web (`index.html`) que actúa como gateway de interceptación legal. Recibe el tráfico interceptado desde los BNGs Nokia mediante el formato **ip-udp-shim** y lo presenta en un dashboard web en tiempo real.

## Componentes

| Componente | Función |
|------------|---------|
| `lig.py` | Listener UDP + Parser Nokia LI Shim + API REST |
| `index.html` | Dashboard web con estadísticas y tabla de eventos |

## Acceso

- **Dashboard Web**: `http://localhost:8092`
- **API REST**: `http://localhost:8092/api/events`
- **SSH**: `ssh -p 56619 root@localhost`

## Funcionamiento General

1. El BNG envía tráfico interceptado como UDP al puerto 11111 del LIG
2. El script `lig.py` escucha en UDP 0.0.0.0:11111
3. Cada paquete se parsea extrayendo el Nokia LI Shim header
4. Los eventos se almacenan en memoria (máximo 2000 eventos)
5. La API REST expone los eventos y estadísticas
6. El dashboard web consulta la API y muestra los datos en tiempo real

## Configuración en el BNG

### Mirror Destination

```text
/configure mirror mirror-dest "li-dest-1" admin-state enable
/configure mirror mirror-dest "li-dest-1" service-id 111111
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap header-type ip-udp-shim
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap direction-bit true
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap router-instance "9999"
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap gateway ip-address source 172.19.1.2
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap gateway ip-address destination 172.19.1.1
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap gateway udp-port source 11111
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap gateway udp-port destination 11111
```

### Activar Interceptación (desde usuario liadmin)

```text
# Por suscriptor
li-source "li-dest-1" subscriber "ONT-001" ingress true
li-source "li-dest-1" subscriber "ONT-001" egress true
li-source "li-dest-1" subscriber "ONT-001" intercept-id 1001
li-source "li-dest-1" subscriber "ONT-001" session-id 1

# Por SAP
li-source "li-dest-1" sap 1/1/c2/1:50.150 ingress true
li-source "li-dest-1" sap 1/1/c2/1:50.150 egress true
li-source "li-dest-1" sap 1/1/c2/1:50.150 intercept-id 2001
li-source "li-dest-1" sap 1/1/c2/1:50.150 session-id 1
```
