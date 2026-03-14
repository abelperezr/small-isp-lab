---
sidebar_position: 2
sidebar_label: 1. Validación base de BNG
---

# 1. Validación Base de BNG

:::note[Note]
Aplicar estas validaciones sobre los BNGs que ejecutan SROS.
:::

## 1.1 Pruebas Generales

### 1.1.1 Verificar versión de software y BOF

Usa los siguientes comandos para verificar la versión de software en ejecución y los parámetros del BOF:

```text
[/]
A:admin@MASTER# show version
TiMOS-C-25.10.R2 cpm/x86_64 Nokia 7750 SR Copyright (c) 2000-2025 Nokia.
All rights reserved. All use subject to applicable license agreements.
Built on Wed Dec 17 21:07:16 UTC 2025 by builder in /builds/2510B/R2/panos


A:admin@MASTER# //show bof
INFO: CLI #2051: Switching to the classic CLI engine
INFO: CLI #2050: Classic CLI modification of the configuration is not allowed - 'model-driven' management interface configuration mode active
*A:MASTER# /show bof
===============================================================================
BOF (Memory)
===============================================================================
    primary-image    cf3:\
    primary-config   cf3:\config.cfg
    license-file     cf3:\license.txt
    address          10.99.1.2/24 active
    address          fd00:cafe::2/64 active
    static-route     0.0.0.0/0 next-hop 10.99.1.1
    static-route     ::/0 next-hop fd00:cafe::1
    autonegotiate
    duplex           full
    speed            100
    wait             3
    persist          off
    no li-local-save
    no li-separate
    console-speed    115200
    system-base-mac  1c:59:00:00:00:00
===============================================================================
INFO: CLI #2052: Switching to the MD-CLI engine
```

### 1.1.2 Verificar inventario del nodo

Muestra el tipo, modelo y número de serie del chasis y de las tarjetas instaladas:

```text
[/]
A:admin@MASTER# show card

===============================================================================
Card Summary
===============================================================================
Slot      Provisioned Type                         Admin Operational   Comments
              Equipped Type (if different)         State State
-------------------------------------------------------------------------------
1         iom5-e:he1200g+                          up    up
2         iom4-e-b                                 up    up
A         cpm5                                     up    up/active
B         cpm5                                     up    up/standby
===============================================================================
```

```text
[/]
A:admin@MASTER# show card 1 detail

===============================================================================
Card 1
===============================================================================
Slot      Provisioned Type                         Admin Operational   Comments
              Equipped Type (if different)         State State
-------------------------------------------------------------------------------
1         iom5-e:he1200g+                          up    up

IOM Card Licensing Data
    Licensed Level                : he1200g+
    Description                   : 1.2T /w Agg to 2.4T, High Edge Routing
```

```text
[/]
A:admin@MASTER# show mda

===============================================================================
MDA Summary
===============================================================================
Slot  Mda   Provisioned Type                            Admin     Operational
                Equipped Type (if different)            State     State
-------------------------------------------------------------------------------
1     1     me6-100gb-qsfp28                            up        up
2     1     isa2-bb                                     up        up
                me-isa2-ms
===============================================================================
```

### 1.1.3 Mostrar información del sistema

Usa estos comandos para revisar:

- uptime del router y contexto del último reinicio
- estado de las fuentes de poder
- alarmas activas

```text
[/]
A:admin@MASTER# show system information

===============================================================================
System Information
===============================================================================
System Name            : MASTER
System Type            : 7750 SR-7
Chassis Topology       : Standalone
System Version         : C-25.10.R2
System Contact         :
System Location        :
System Coordinates     :
System Active Slot     : A
System Up Time         : 0 days, 00:43:21.05 (hr:min:sec)
System Up Time (64-bit): 0 days, 00:43:21.05 (hr:min:sec)

Configuration Mode Cfg : model-driven
Configuration Mode Oper: model-driven
Last Mode Changed      : 2026/03/08 13:10:24 Duration: 0d 00:00:00

SNMP Port              : 161
SNMP Engine ID         : 0000197f00001c5900000000
SNMP Engine Boots      : 3
SNMP Max Message Size  : 9216
SNMP Max Bulk Duration : N/A
SNMP Admin State       : Enabled
SNMP Oper State        : Enabled
SNMP Index Boot Status : Persistent
SNMP Sync State        : OK

Tel/Tel6/SSH/FTP Admin : Disabled/Disabled/Enabled/Disabled
Tel/Tel6/SSH/FTP Oper  : Down/Down/Up/Down

BOF Source             : cf3:
Image Source           : primary
Config Source          : N/A
Last Booted Config File: N/A
Last Boot Cfg Version  : N/A
Last Boot Config Header: #CONTENT - BNG "MASTER" #1. SYSTEM NAME #2. TIME #3.
                         GRPC #4. NETCONF #5. SNMP #6. SSH #7. SYSTEM USERS
                         PROFILES #8. SYSTEM USERS #9. LOGS #10. CARDS #
                         10.1. IOM #    10.2. MDA #    10.3. SFM #11. ROUTER
                         BASE #12. PORTS #    12.1. PORT TO BNG2 #    12.2.
                         PORT TO OLT #    12.3. PORT TO LIG #    12.4. PORT
                         TO DNS #    12.5. PORT TO CARRIER1 #    12.6. PORT
                         TO CARRIER2 #13. INTERFACE TO BNG2 #14. IS-IS #15.
                         LDP #16. IBGP #    16.1. GROUPS #    16.2. NEIGHBORS
                         #17. COMMUNITIES #18. PREFIX-LIST #19. EXPORT/IM
```

```text
[/]
A:admin@MASTER# show chassis power-supply
===============================================================================
Chassis 1 Detail
===============================================================================
Power Supply Information
  Number of power supplies          : 2

  Power supply number               : 1
    Defaulted power supply type     : dc
    Power supply model              : pem
    Status                          : up

  Power supply number               : 2
    Defaulted power supply type     : dc
    Power supply model              : pem
    Status                          : up
===============================================================================
```

```text
[/]
A:admin@MASTER# show system alarms

===============================================================================
Alarms [Critical:0 Major:0 Minor:0 Warning:0 Total:0]
===============================================================================
Index      Date/Time               Severity  Alarm      Resource
   Details
-------------------------------------------------------------------------------
No Matching Entries
===============================================================================
```

### 1.1.4 Mostrar estado de interfaces

Usa los siguientes comandos para verificar el estado operacional de puertos e interfaces del router:

- `show port <port-id> detail`
- `show router interface <id> detail`

```text
[/]
A:admin@MASTER# show port

===============================================================================
Ports on Slot 1
===============================================================================
Port          Admin Link Port    Cfg  Oper LAG/ Port Port Port   C/QS/S/XFP/
Id            State      State   MTU  MTU  Bndl Mode Encp Type   MDIMDX
-------------------------------------------------------------------------------
1/1/c1        Up         Link Up                          conn   100GBASE-LR4*
1/1/c1/1      Up    Yes  Up      8936 8936    - hybr dotq cgige
1/1/c2        Up         Link Up                          conn   100GBASE-LR4*
1/1/c2/1      Up    Yes  Up      8936 8936    - hybr qinq cgige
1/1/c3        Up         Link Up                          conn   100GBASE-LR4*
1/1/c3/1      Up    Yes  Up      8936 8936    - hybr dotq cgige
1/1/c4        Up         Link Up                          conn   100GBASE-LR4*
1/1/c4/1      Up    Yes  Up      8936 8936    - hybr dotq cgige
1/1/c5        Up         Link Up                          conn   100GBASE-LR4*
1/1/c5/1      Up    Yes  Up      8936 8936    - hybr dotq cgige
1/1/c6        Up         Link Up                          conn   100GBASE-LR4*
1/1/c6/1      Up    Yes  Up      8936 8936    - hybr dotq cgige

===============================================================================
Ports on Slot 2
===============================================================================
Port          Admin Link Port    Cfg  Oper LAG/ Port Port Port   C/QS/S/XFP/
Id            State      State   MTU  MTU  Bndl Mode Encp Type   MDIMDX
-------------------------------------------------------------------------------
2/1/nat-in-ip Up    Yes  Up                   - accs qinq vport
2/1/nat-out-ip
              Up    Yes  Up                   - accs qinq vport
2/1/nat-in-l2 Up    Yes  Up                   - netw dotq vport
2/1/lns-net   Up    Yes  Up                   - accs qinq vport
2/1/lns-esm   Up    Yes  Up                   - accs qinq vport
2/1/nat-in-ds Up    Yes  Up                   - accs qinq vport
2/1/lo-gre    Up    Yes  Up                   - accs dotq vport

===============================================================================
Ports on Slot A
===============================================================================
Port          Admin Link Port    Cfg  Oper LAG/ Port Port Port   C/QS/S/XFP/
Id            State      State   MTU  MTU  Bndl Mode Encp Type   MDIMDX
-------------------------------------------------------------------------------
A/1           Up    Yes  Up      1514 1514    - netw null faste  MDI
A/3           Down  No   Down    1514 1514    - netw null faste
A/4           Down  No   Down    1514 1514    - netw null faste

===============================================================================
Ports on Slot B
===============================================================================
Port          Admin Link Port    Cfg  Oper LAG/ Port Port Port   C/QS/S/XFP/
Id            State      State   MTU  MTU  Bndl Mode Encp Type   MDIMDX
-------------------------------------------------------------------------------
B/1           Up    Yes  Up      1514 1514    - netw null faste  MDI
B/3           Down  No   Down    1514 1514    - netw null faste
B/4           Down  No   Down    1514 1514    - netw null faste
===============================================================================
```

```text
[/]
A:admin@MASTER# show port 1/1/c1/1 detail

===============================================================================
Ethernet Interface
===============================================================================
Description        : 100-Gig Ethernet
Interface          : 1/1/c1/1                   Oper Speed       : 100 Gbps
FP Number          : 1                          MAC Chip Number  : 1
Link-level         : Ethernet                   Config Speed     : N/A
Admin State        : up                         Oper Duplex      : full
Oper State         : up
Config Duplex      : N/A
Physical Link      : Yes                        MTU              : 8936
Single Fiber Mode  : No                         Min Frame Length : 64 Bytes
IfIndex            : 35700737                   Hold time up     : 0 seconds
Last State Change  : 03/08/2026 14:02:16        Hold time down   : 0 seconds
Hold Time Down Rmng: 0 cs                       Hold Time Up Rmng: 0 cs
Last Cleared Time  : N/A
Phys State Chng Cnt: 1
RS-FEC Config Mode : None
RS-FEC Oper Mode   : None
```

En el BNG SLAVE, la interfaz equivalente es `to_MASTER`:

```text
[/]
A:admin@MASTER# show router interface "to_SLAVE" detail

===============================================================================
Interface Table (Router: Base)
===============================================================================

-------------------------------------------------------------------------------
Interface
-------------------------------------------------------------------------------
If Name          : to_SLAVE
Admin State      : Up                   Oper (v4/v6)      : Up/Down
Down Reason V6   : ifProtoOperDown
Protocols        : ISIS LDP
IP Addr/mask     : 172.99.1.0/31        Address Type      : Primary
IGP Inhibit      : Disabled             Broadcast Address : Host-ones
HoldUp-Time      : 0                    Track Srrp Inst   : 0
-------------------------------------------------------------------------------
Details
-------------------------------------------------------------------------------
```

### 1.1.5 Verificar hora del sistema

Usa `show time` para verificar la fecha y hora actuales en los BNGs.

Por defecto, la zona horaria está configurada como `est`. Puedes cambiarla con:

```text
[gl:/configure]
A:admin@MASTER# system time zone standard name

 <name>
 hst
 akst
 pst
 mst
 cst
 est
 ast
 nst
 utc
 gmt
 wet
 cet
 eet
 msk
 msd
 awst
 acst
 aest
 nzst
```

```text
[/]
A:admin@MASTER# show time
Sun Mar  8 14:58:53 EST 2026
```

### 1.1.6 Verificar NTP

Verifica el servidor NTP activo:

Si hace falta, selecciona la IP de Google NTP con menor latencia para la región. Para identificar la IP más cercana, ejecuta:

```text
ping time.google.com

Pinging time.google.com [216.239.35.12] with 32 bytes of data:
Reply from 216.239.35.12: bytes=32 time=8ms TTL=109
Reply from 216.239.35.12: bytes=32 time=8ms TTL=109
Reply from 216.239.35.12: bytes=32 time=8ms TTL=109
Reply from 216.239.35.12: bytes=32 time=8ms TTL=109
```

Esto devuelve la IP que mejor se ajusta a la región actual.

```text
[gl:/configure system time ntp]
A:admin@MASTER# show system ntp servers

===============================================================================
NTP Active Associations
===============================================================================
State                     Reference ID    St Type  A  Poll Reach     Offset(ms)
    Router         Remote
-------------------------------------------------------------------------------
chosen                    GOOG            1  srvr  -  64   ....YYYY  -236.000
    9999           216.239.35.12
===============================================================================

===============================================================================
NTP Clients
===============================================================================
vRouter                                                    Time Last Request Rx
    Address
-------------------------------------------------------------------------------
===============================================================================
```

### 1.1.7 Mostrar estado del router

Usa `show router status` para verificar el estado de los protocolos habilitados en el router:

```text
A:admin@MASTER# show router status

===============================================================================
Router Status (Router: Base)
===============================================================================
                         Admin State                        Oper State
-------------------------------------------------------------------------------
Router                   Up                                 Up
OSPFv2                   Not configured                     Not configured
RIP                      Not configured                     Not configured
RIP-NG                   Not configured                     Not configured
ISIS-0                   Up                                 Up
MPLS                     Not configured                     Not configured
P2MP-SR-TREE             Not configured                     Not configured
RSVP                     Not configured                     Not configured
LDP                      Up                                 Up
BGP                      Up                                 Up
IGMP                     Not configured                     Not configured
MLD                      Not configured                     Not configured
PIM                      Not configured                     Not configured
PIMv4                    Not configured                     Not configured
PIMv6                    Not configured                     Not configured
OSPFv3                   Not configured                     Not configured
MSDP                     Not configured                     Not configured
BIER                     Not configured                     Not configured
PCE                      Not configured                     Not configured
PCC                      Not configured                     Not configured
```

## 1.2 ISIS

Verifica que las adyacencias ISIS estén establecidas entre los nodos y que las rutas ISIS hayan sido aprendidas.

### 1.2.1 Verificar interfaces ISIS

```text
[gl:/configure]
A:admin@MASTER# show router isis interface

===============================================================================
Rtr Base ISIS Instance 0 Interfaces
===============================================================================
Interface                        Level CircID  Oper      L1/L2 Metric     Type
                                               State
-------------------------------------------------------------------------------
system                           L2    1       Up        -/0              p2p
to_SLAVE                         L1L2  2       Up        10/10            p2p
-------------------------------------------------------------------------------
Interfaces : 2
===============================================================================
```

### 1.2.2 Verificar adyacencia ISIS

```text
[gl:/configure]
A:admin@MASTER# show router isis adjacency

===============================================================================
Rtr Base ISIS Instance 0 Adjacency
===============================================================================
System ID                Usage State Hold Interface                     MT-ID
-------------------------------------------------------------------------------
SLAVE                    L2    Up    20   to_SLAVE                      0
-------------------------------------------------------------------------------
Adjacencies : 1
===============================================================================
```

### 1.2.3 Verificar tabla de rutas

```text
[gl:/configure]
A:admin@MASTER# show router route-table protocol isis

===============================================================================
Route Table (Router: Base)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric
-------------------------------------------------------------------------------
10.0.0.2/32                                   Remote  ISIS      01h25m09s  18
       172.99.1.1                                                   10
-------------------------------------------------------------------------------
No. of Routes: 1
Flags: n = Number of times nexthop is repeated
       B = BGP backup route available
       L = LFA nexthop available
       S = Sticky ECMP requested
===============================================================================
```

### 1.2.4 Verificar base de datos ISIS

```text
[gl:/configure]
A:admin@MASTER# show router isis database detail

===============================================================================
Rtr Base ISIS Instance 0 Database (detail)
===============================================================================

Displaying Level 1 database
-------------------------------------------------------------------------------
Level (1) LSP Count : 0

Displaying Level 2 database
-------------------------------------------------------------------------------
LSP ID    : MASTER.00-00                                Level     : L2
Sequence  : 0xc                    Checksum  : 0xbb77   Lifetime  : 800
Version   : 1                      Pkt Type  : 20       Pkt Ver   : 1
Attributes: L1L2                   Max Area  : 3        Alloc Len : 1492
SYS ID    : 0100.0000.0001         SysID Len : 6        Used Len  : 105

TLVs :
  Area Addresses:
    Area Address : (3) 49.0001
  Supp Protocols:
    Protocols     : IPv4
  IS-Hostname   : MASTER
  Router ID   :
    Router ID   : 10.0.0.1
  I/F Addresses :
    I/F Address   : 172.99.1.0
    I/F Address   : 10.0.0.1
  TE IS Nbrs   :
    Nbr   : SLAVE.00
    Default Metric  : 10
    Sub TLV Len     : 12
    IF Addr   : 172.99.1.0
    Nbr IP    : 172.99.1.1
  TE IP Reach   :
    Default Metric  : 10
    Control Info:    , prefLen 31
    Prefix   : 172.99.1.0
    Default Metric  : 0
    Control Info:    , prefLen 32
    Prefix   : 10.0.0.1

-------------------------------------------------------------------------------
LSP ID    : SLAVE.00-00                                 Level     : L2
Sequence  : 0xb                    Checksum  : 0x91f0   Lifetime  : 702
Version   : 1                      Pkt Type  : 20       Pkt Ver   : 1
Attributes: L1L2                   Max Area  : 3        Alloc Len : 104
SYS ID    : 0100.0000.0002         SysID Len : 6        Used Len  : 104

TLVs :
  Area Addresses:
    Area Address : (3) 49.0001
  Supp Protocols:
    Protocols     : IPv4
  IS-Hostname   : SLAVE
  Router ID   :
    Router ID   : 10.0.0.2
  I/F Addresses :
    I/F Address   : 172.99.1.1
    I/F Address   : 10.0.0.2
  TE IS Nbrs   :
    Nbr   : MASTER.00
    Default Metric  : 10
    Sub TLV Len     : 12
    IF Addr   : 172.99.1.1
    Nbr IP    : 172.99.1.0
  TE IP Reach   :
    Default Metric  : 10
    Control Info:    , prefLen 31
    Prefix   : 172.99.1.0
    Default Metric  : 0
    Control Info:    , prefLen 32
    Prefix   : 10.0.0.2

Level (2) LSP Count : 2
-------------------------------------------------------------------------------
Control Info     : D = Prefix Leaked Down
                   S = Sub-TLVs Present
Attribute Flags  : N = Node Flag
                   R = Re-advertisement Flag
                   X = External Prefix Flag
                   E = Entropy Label Capability (ELC) Flag
Adj-SID Flags    : v4/v6 = IPv4 or IPv6 Address-Family
                   B = Backup Flag
                   V = Adj-SID carries a value
                   L = value/index has local significance
                   S = Set of Adjacencies
                   P = Persistently allocated
Prefix-SID Flags : R = Re-advertisement Flag
                   N = Node-SID Flag
                   nP = no penultimate hop POP
                   E = Explicit-Null Flag
                   V = Prefix-SID carries a value
                   L = value/index has local significance
Lbl-Binding Flags: v4/v6 = IPv4 or IPv6 Address-Family
                   M = Mirror Context Flag
                   S = SID/Label Binding flooding
                   D = Prefix Leaked Down
                   A = Attached Flag
SABM-flags Flags:  R = RSVP-TE
                   S = SR-TE
                   F = LFA
                   X = FLEX-ALGO
FAD-flags Flags:   M = Prefix Metric
===============================================================================
```

## 1.3 MPLS / LDP

Verifica que las sesiones dinámicas de LDP se creen correctamente.

### 1.3.1 Verificar interfaces LDP operacionales

```text
[gl:/configure]
A:admin@MASTER# show router ldp interface

===============================================================================
LDP Interfaces
===============================================================================
Interface                         Adm/Opr
 Sub-Interface(s)                  Adm/Opr  Hello Hold  KA    KA    Transport
                                            Fctr  Time  Fctr  Time  Address
-------------------------------------------------------------------------------
to_SLAVE                          Up/Up
  ipv4                              Up/Up   3     15    3     30    System
-------------------------------------------------------------------------------
No. of Interfaces: 1
===============================================================================
```

### 1.3.2 Verificar sesiones IPv4 de LDP

```text
[gl:/configure]
A:admin@MASTER# show router ldp session

==============================================================================
LDP IPv4 Sessions
==============================================================================
Peer LDP Id         Adj Type  State         Msg Sent  Msg Recv  Up Time
------------------------------------------------------------------------------
10.0.0.2:0          Both      Established   2429      2602      0d 01:29:40
------------------------------------------------------------------------------
No. of IPv4 Sessions: 1
==============================================================================

===============================================================================
LDP IPv6 Sessions
===============================================================================
Peer LDP Id
 Adj Type            State          Msg Sent       Msg Recv       Up Time
-------------------------------------------------------------------------------
No Matching Entries Found
===============================================================================
```
