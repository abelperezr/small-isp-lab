---
sidebar_position: 7
sidebar_label: 8. CGNAT
---

# 8. CGNAT

## 8.1 Verificar ISA NAT-group y miembros

Verifica el grupo NAT de la ISA y sus miembros.

Comandos relacionados:

- `/show isa nat-group`
- `/show isa nat-group 1 members`

```text
[gl:/configure]
A:admin@MASTER# show isa nat-group 1

===============================================================================
ISA NAT Group 1
===============================================================================
Description                 : (Not Specified)
Admin state                 : inService
Operational state           : inService
Degraded                    : false
Redundancy                  : active-standby
Active MDA limit            : 1
Failed MDA limit            : 0
Operational Group           : N/A
Monitor Operational Group   : N/A
Scaling profile             : profile1

-------------------------------------------------------------------------------
NAT specific information for ISA group 1
-------------------------------------------------------------------------------
Reserved sessions           : 0
High Watermark (%)          : 90
Low Watermark (%)           : 80
Accounting policy           : (Not Specified)
UPnP mapping limit          : 524288
Suppress LsnSubBlksFree     : false
LSN support                 : enabled
Periodic Update Interval    : N/A
Periodic Update Rate Limit  : N/A
Last Mgmt Change            : 03/08/2026 14:00:30
-------------------------------------------------------------------------------
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show isa nat-group 1 members

===============================================================================
ISA Group 1 members
===============================================================================
Group Member State          MDA/VM   Addresses  Blocks     Se-% Hi Se-Prio
-------------------------------------------------------------------------------
1     1      active         2/1      10         164        < 1  N  8
-------------------------------------------------------------------------------
No. of members: 1
===============================================================================
```

## 8.2 Verificar sesiones NAT y operación de políticas

Verifica las sesiones NAT y confirma que NAT funcione de acuerdo con la política configurada.

Comandos relacionados:

- `/show service nat nat-policy`
- `/show router 9999 nat pool "dtpool"`
- `/show router 9999 nat pool`
- `/tools dump nat sessions`
- `/show service nat lsn-subscribers`
- `/tools dump nat isa resources mda "2/1"`

```text
[gl:/configure]
A:admin@MASTER# show service nat nat-policy

===============================================================================
NAT policies
===============================================================================
Policy                           Description                   Creation Origin
-------------------------------------------------------------------------------
nat64-pol                                                      manual
natpol                                                         manual
natvip                                                         manual
-------------------------------------------------------------------------------
No. of NAT policies: 3
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router 9999 nat pool "dtpool"

===============================================================================
NAT Pool dtpool
===============================================================================
Description                           : (Not Specified)
ISA NAT Group                         : 1
Pool type                             : largeScale
Address pooling                       : paired
Applications                          : (None)
Admin state                           : inService
Mode                                  : napt
Port forwarding dyn blocks reserved   : 0
Port forwarding range                 : 1 - 1023
Port reservation                      : 128 blocks
Block usage High Watermark (%)        : (Not Specified)
Block usage Low Watermark (%)         : (Not Specified)
ICMP echo reply                       : disabled
Monitor Operational Group             : N/A
Subscriber limit per IP address       : 8
Active                                : true
Deterministic port reservation        : 64
Last Mgmt Change                      : 03/08/2026 14:00:22
===============================================================================

===============================================================================
NAT address ranges of pool dtpool
===============================================================================
Range                                               Drain Num-blk
-------------------------------------------------------------------------------
99.99.99.99 - 99.99.99.99                                 8
-------------------------------------------------------------------------------
No. of ranges: 1
===============================================================================

===============================================================================
NAT members of pool dtpool ISA NAT group 1
===============================================================================
Member                                                        Block-Usage-% Hi
-------------------------------------------------------------------------------
1                                                             5             N
-------------------------------------------------------------------------------
No. of members: 1
===============================================================================

===============================================================================
Dual-Homing
===============================================================================
Type                                  : (Not Applicable)
Export route                          : (Not Specified)
Monitor route                         : (Not Specified)
Admin state                           : outOfService
Dual-Homing State                     : Disabled (up)
Dual-Homing Down Reason               : pool "dtpool" redundancy node is admin
                                        down
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router 9999 nat pool "one-to-one"

===============================================================================
NAT Pool one-to-one
===============================================================================
Description                           : (Not Specified)
ISA NAT Group                         : 1
Pool type                             : largeScale
Address pooling                       : paired
Applications                          : agnostic
Admin state                           : inService
Mode                                  : oneToOne
Port forwarding dyn blocks reserved   : 0
Port forwarding range                 : N/A
Port reservation                      : 1 blocks
Block usage High Watermark (%)        : (Not Specified)
Block usage Low Watermark (%)         : (Not Specified)
ICMP echo reply                       : disabled
Monitor Operational Group             : N/A
Subscriber limit per IP address       : 1
Active                                : true
Deterministic port reservation        : 5120
Last Mgmt Change                      : 03/08/2026 14:00:21
===============================================================================

===============================================================================
NAT address ranges of pool one-to-one
===============================================================================
Range                                               Drain Num-blk
-------------------------------------------------------------------------------
88.88.88.88 - 88.88.88.95                                 8
-------------------------------------------------------------------------------
No. of ranges: 1
===============================================================================

===============================================================================
NAT members of pool one-to-one ISA NAT group 1
===============================================================================
Member                                                        Block-Usage-% Hi
-------------------------------------------------------------------------------
1                                                             100           N
-------------------------------------------------------------------------------
No. of members: 1
===============================================================================

===============================================================================
Dual-Homing
===============================================================================
Type                                  : (Not Applicable)
Export route                          : (Not Specified)
Monitor route                         : (Not Specified)
Admin state                           : outOfService
Dual-Homing State                     : Disabled (up)
Dual-Homing Down Reason               : pool "one-to-one" redundancy node is
                                        admin down
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# tools dump nat sessions

===============================================================================
Matched 8 sessions on Slot #2 MDA #1
===============================================================================
Owner               : LSN-Host@192.168.5.7
Router              : 9998
Policy              : natvip
FlowType            : *   Pinhole       Timeout             : Infinite
Inside IP Addr      : 192.168.5.7
Inside Port         : *
Outside IP Addr     : 88.88.88.95
Outside Port        : *
Foreign IP Addr     : *
Foreign Port        : *
Dest IP Addr        : *
Nat Group           : 1
Nat Group Member    : 1
-------------------------------------------------------------------------------
Owner               : LSN-Host@192.168.5.3
Router              : 9998
Policy              : natvip
FlowType            : *   Pinhole       Timeout             : Infinite
Inside IP Addr      : 192.168.5.3
Inside Port         : *
Outside IP Addr     : 88.88.88.91
Outside Port        : *
Foreign IP Addr     : *
Foreign Port        : *
Dest IP Addr        : *
Nat Group           : 1
Nat Group Member    : 1
-------------------------------------------------------------------------------
```

```text
[gl:/configure]
A:admin@MASTER# show service nat lsn-subscribers

===============================================================================
NAT LSN subscribers
===============================================================================
Subscriber                  : [LSN-Host@100.80.0.0]
NAT policy                  : natpol
Subscriber ID               : 276824064
-------------------------------------------------------------------------------
Type                        : classic-lsn-sub
Inside router               : 9998
Inside IP address prefix    : 100.80.0.0/32
ISA NAT group               : 1
ISA NAT group member        : 1
Outside router              : 9999
Outside IP address          : 99.99.99.99


Subscriber                  : [LSN-Host@100.80.0.1]
NAT policy                  : natpol
Subscriber ID               : 276824065
-------------------------------------------------------------------------------
Type                        : classic-lsn-sub
Inside router               : 9998
Inside IP address prefix    : 100.80.0.1/32
ISA NAT group               : 1
ISA NAT group member        : 1
Outside router              : 9999
Outside IP address          : 99.99.99.99


Subscriber                  : [LSN-Host@100.80.0.2]
NAT policy                  : natpol
Subscriber ID               : 276824066
-------------------------------------------------------------------------------
```

```text
A:admin@MASTER# tools dump nat isa resources mda "2/1"

===============================================================================
ISA NAT MDA 2/1 resources
===============================================================================
Name                                Maximum         Limit
                                     Actual          Peak       Peak Timestamp
-------------------------------------------------------------------------------
Flows                                131072           N/A
                                          8             8  2026/03/08 13:10:34
Policies                               4096           N/A
                                          3             3  2026/03/08 13:10:34
Port-ranges configured               524288          100%
                                        164           164  2026/03/08 13:10:34
Port-ranges used                        164          100%
                                         16            16  2026/03/08 13:10:34
Port-ranges retained                    164          100%
                                          0             0
Ports                            1006632960          100%
                                          8             8  2026/03/08 13:10:34
IP-addresses                          65536          100%
                                          2             2  2026/03/08 13:10:34
Large-scale hosts                      8192          100%
                                         16            16  2026/03/08 13:10:34
Subscriber-cache entries               8192           N/A
                                          0             0
L2-aware subscribers                   2048          100%
                                          0             0
L2-aware hosts                         4096          100%
                                          0             0
Delayed ICMP's                          200           N/A
                                          0             0
ALG session                           24576           N/A
                                          0             0
Upstream fragment lists                2048           N/A
                                          0             0
Downstream fragment lists              1024           N/A
                                          0             0
Upstream fragment bufs                 2048           N/A
                                          0             0
Downstream fragment bufs               1024           N/A
                                          0             0
Dormant subscribers                       0           N/A
                                          0             0
UPnP mappings                          1024           N/A
                                          0             0
UPnP sessions                           100           N/A
                                          0             0
One-to-one IP-addresses                8192          100%
                                          8             8  2026/03/08 13:10:34
Flowlog destinations set 0                2           N/A
                                          0             0
Flowlog destinations set 1                2           N/A
                                          0             0
Flowlog destinations set 2                1           N/A
                                          0             0
Flowlog packets set 0                   256           N/A
                                          0             0
Flowlog packets set 1                   256           N/A
                                          0             0
Flowlog packets set 2                   256           N/A
                                          0             0
PPPoE sessions                         2048           N/A
                                          0             0
Flexible-port IP-addresses              128          100%
                                          0             0  2026/03/08 13:10:34
===============================================================================
Peak values last reset at : N/A
```
