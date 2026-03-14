---
sidebar_position: 5
---

# BGP Traffic Engineering

## BGP diagram

![BGP Traffic Engineering](/img/bgp.png)

## Description

The BGP Traffic Engineering system uses the **EHS (Event Handling System)** of Nokia SROS to dynamically adjust the export policies of the eBGP neighbors according to the SRRP state of the BNG. This allows Internet traffic to preferably enter through the BNG which is SRRP Master.

## BGP architecture

### ASN and Peers

| Entity | ASN | Role |
|---------|-----|-----|
| ISP (BNGs) | 65520 | eBGP to carriers |
| BNGs (Base) | 65510 | iBGP between BNGs |
| Carrier 1 | 65501 | eBGP upstream |
| Carrier 2 | 65502 | eBGP upstream |

### Local Preference (Inbound)

| Carrier | Import Policy | Local-Pref | Priority |
|---------|---------------|------------|-----------|
| Carrier 1 | IMPORT-CARRIER1 | 300 | **Primary** |
| Carrier 2 | IMPORT-CARRIER2 | 150 | Secondary |

### AS-Path Prepend (Outbound - Dynamic EHS)

The EHS adjusts the export policies based on the SRRP role:

| BNG Role | Carrier 1 | Carrier 2 |
|---------|-----------|-----------|
| **MASTER** | Without prepend (MED=50) | Prepend x2 (MED=50) |
| **BACKUP** | Prepend x3 (MED=100) | Prepend x4 (MED=100) |

:::tip[EHS logic]

When a BNG is SRRP Master, it announces its prefixes with the lowest possible AS-Path towards Carrier 1 (preferred) and with prepend x2 towards Carrier 2. When it is Backup, it adds more prepends so that return traffic is sent to the BNG that is currently Master.

:::
## Advertised Prefixes

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

### Script Flow

1. SRRP changes state → event `tmnxSrrpTrapNewMaster` or `tmnxSrrpBecameBackup`
2. Log filter "10" captures `mc-redundancy` events
3. The handler "Handler-SRRPSwitch" executes the Python script `srrp_bgp_policy.py`
4. The script reads the status of the 3 SRRP instances
5. Determines the role (master/backup) when all instances match
6. Apply the corresponding export policies to the eBGP neighbors

### EHS Configuration

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

### pySROS Script (Main Logic)

The `srrp_bgp_policy.py` script implements the following logic:

1. Read the operational status of the 3 SRRP instances (ipv6-only, dual-stack, vip)
2. Classify the role: "master" if all are master, "backup" if all are backup/shunt
3. Determine the target export policies for each neighbor
4. Compare with current policies
5. If they differ, delete the neighbor's "export" container and recreate it with the new policy
6. Verify post-commit that the changes were applied correctly

The results of the script are saved in `cf3:\resultsSRRPSwitch` with format:

```
resultsSRRPSwitch_20260308-000025-UTC.665049.out
```

These files live inside the BNG filesystem and are ephemeral. If you destroy the lab, they disappear with the node.

## Verification

```bash
# Ver export policy actual
show router 9999 bgp neighbor 172.16.1.1 detail | match "Export Policy"

# Ver rutas anunciadas (observar AS-Path)
show router 9999 bgp neighbor 172.16.1.1 advertised-routes

# Ver resultados del script EHS
show system script-control script-policy "Policy-SRRPSwitch"
```
