---
sidebar_position: 5
---

# BGP Traffic Engineering

## Diagrama BGP

![BGP Traffic Engineering](/img/bgp.png)

## Descripción

El sistema de BGP Traffic Engineering utiliza el **EHS (Event Handling System)** de Nokia SROS para ajustar dinámicamente las export policies de los neighbors eBGP según el estado SRRP del BNG. Esto permite que el tráfico de Internet entre preferentemente por el BNG que es SRRP Master.

## Arquitectura BGP

### ASN y Peers

| Entidad | ASN | Rol |
|---------|-----|-----|
| ISP (BNGs) | 65520 | eBGP hacia carriers |
| BNGs (Base) | 65510 | iBGP entre BNGs |
| Carrier 1 | 65501 | eBGP upstream |
| Carrier 2 | 65502 | eBGP upstream |

### Local Preference (Inbound)

| Carrier | Import Policy | Local-Pref | Prioridad |
|---------|---------------|------------|-----------|
| Carrier 1 | IMPORT-CARRIER1 | 300 | **Primario** |
| Carrier 2 | IMPORT-CARRIER2 | 150 | Secundario |

### AS-Path Prepend (Outbound - EHS Dinámico)

El EHS ajusta las export policies según el rol SRRP:

| BNG Rol | Carrier 1 | Carrier 2 |
|---------|-----------|-----------|
| **MASTER** | Sin prepend (MED=50) | Prepend x2 (MED=50) |
| **BACKUP** | Prepend x3 (MED=100) | Prepend x4 (MED=100) |

:::tip[Lógica del EHS]

Cuando un BNG es SRRP Master, anuncia sus prefijos con el menor AS-Path posible hacia Carrier 1 (preferido) y con prepend x2 hacia Carrier 2. Cuando es Backup, añade más prepends para que el tráfico de retorno sea enviado al BNG que actualmente es Master.

:::
## Prefijos Anunciados

```text
# IPv4
/configure policy-options prefix-list "public-nat-v4" prefix 99.99.99.99/32 type exact    # CGNAT
/configure policy-options prefix-list "public-nat-v4" prefix 199.199.199.199/32 type exact # NAT64
/configure policy-options prefix-list "public-nat-v4" prefix 88.88.88.88/29 type exact     # VIP 1:1

# IPv6
/configure policy-options prefix-list "public-v6" prefix 2001:db8:100::/56 type exact   # WAN IPv6
/configure policy-options prefix-list "public-v6" prefix 2001:db8:200::/48 type exact   # PD IPv6
/configure policy-options prefix-list "public-v6" prefix 2001:db8:cccc::/56 type exact  # WAN DS
/configure policy-options prefix-list "public-v6" prefix 2001:db8:dddd::/48 type exact  # PD DS
```

## EHS - Event Handling System

### Flujo del Script

1. SRRP cambia de estado → evento `tmnxSrrpTrapNewMaster` o `tmnxSrrpBecameBackup`
2. El log filter "10" captura eventos de `mc-redundancy`
3. El handler "Handler-SRRPSwitch" ejecuta el script Python `srrp_bgp_policy.py`
4. El script lee el estado de las 3 instancias SRRP
5. Determina el rol (master/backup) cuando todas las instancias coinciden
6. Aplica las export policies correspondientes a los neighbors eBGP

### Configuración EHS

```text
# Python Script
/configure python python-script "srrp_bgp_policy" admin-state enable
/configure python python-script "srrp_bgp_policy" urls ["cf3:\scripts\srrp_bgp_policy.py"]

# Script Policy
/configure system script-control script-policy "Policy-SRRPSwitch" admin-state enable
/configure system script-control script-policy "Policy-SRRPSwitch" results "cf3:\resultsSRRPSwitch"
/configure system script-control script-policy "Policy-SRRPSwitch" python-script name "srrp_bgp_policy"

# Log Filter
/configure log filter "10" named-entry "1" match application eq mc-redundancy

# Event Triggers
/configure log event-trigger mc-redundancy event tmnxSrrpTrapNewMaster entry 1 handler "Handler-SRRPSwitch"
/configure log event-trigger mc-redundancy event tmnxSrrpBecameBackup entry 1 handler "Handler-SRRPSwitch"
```

### Script pySROS (Lógica Principal)

El script `srrp_bgp_policy.py` implementa la siguiente lógica:

1. Lee el estado operativo de las 3 instancias SRRP (ipv6-only, dual-stack, vip)
2. Clasifica el rol: "master" si todas son master, "backup" si todas son backup/shunt
3. Determina las export policies objetivo para cada neighbor
4. Compara con las policies actuales
5. Si difieren, elimina el container "export" del neighbor y lo recrea con la nueva policy
6. Verifica post-commit que los cambios se aplicaron correctamente

Los resultados del script se guardan en `cf3:\resultsSRRPSwitch` con formato:

```
resultsSRRPSwitch_20260308-000025-UTC.665049.out
```

Estos archivos viven dentro del filesystem del BNG y son efímeros. Si destruyes el lab, desaparecen con el nodo.

## Verificación

```bash
# Ver export policy actual
show router 9999 bgp neighbor 172.16.1.1 detail | match "Export Policy"

# Ver rutas anunciadas (observar AS-Path)
show router 9999 bgp neighbor 172.16.1.1 advertised-routes

# Ver resultados del script EHS
show system script-control script-policy "Policy-SRRPSwitch"
```
