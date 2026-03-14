---
sidebar_position: 3
sidebar_label: 4. L2/L3 services
---

# 4. L2/L3 Services

## 4.1 SAP and SDP utilization validation

Verify the SDPs and SAPs associated with each service.

1. Use the following command to review the services configured on the BNG:
   `show service service-using`
2. Use the following command to review the SAPs assigned to the services:
   `show service sap-using`
3. Use the following command to review the SDPs configured on the services:
   `show service sdp-using`

```text
[gl:/configure]
A:admin@MASTER# show service service-using

===============================================================================
Services
===============================================================================
ServiceId    Type      Adm  Opr  CustomerId Service Name
-------------------------------------------------------------------------------
2            VPLS      Up   Up   1          capture-sap
9998         VPRN      Up   Up   1          9998
9999         VPRN      Up   Up   1          9999
111111       Mirror    Up   Up   1          li-dest-1
2147483648   IES       Up   Down 1          _tmnx_InternalIesService
2147483649   intVpls   Up   Down 1          _tmnx_InternalVplsService
-------------------------------------------------------------------------------
Matching Services : 6
-------------------------------------------------------------------------------
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show service sap-using

===============================================================================
Service Access Points
===============================================================================
PortId                          SvcId      Ing.  Ing.    Egr.  Egr.   Adm  Opr
                                           QoS   Fltr    QoS   Fltr
-------------------------------------------------------------------------------
1/1/c2/1:50.*                   2          1     none    1     none   Up   Up
1/1/c2/1:51.*                   2          1     none    1     none   Up   Up
1/1/c2/1:52.*                   2          1     none    1     none   Up   Up
1/1/c2/1:4094.1                 9998       1     none    1     none   Up   Up
1/1/c2/1:4094.2                 9998       1     none    1     none   Up   Up
1/1/c2/1:4094.3                 9998       1     none    1     none   Up   Up
[1/1/c2/1:50.150]               9998       1     none    1     none   Up   Up
[1/1/c2/1:51.200]               9998       1     none    1     none   Up   Up
[1/1/c2/1:52.300]               9998       1     none    1     none   Up   Up
1/1/c4/1:0                      9998       1     none    1     none   Up   Up
[bbg-1.nat-in-ip:1.2]           9998       65538 none    65538 none   Up   Up
1/1/c3/1:0                      9999       1     none    1     none   Up   Up
1/1/c5/1:0                      9999       1     none    1     none   Up   Up
1/1/c6/1:0                      9999       1     none    1     none   Up   Up
[2/1/nat-out-ip:1.3]            9999       65538 none    65538 none   Up   Up
-------------------------------------------------------------------------------
Number of SAPs : 15
-------------------------------------------------------------------------------
Number of Managed SAPs : 3, indicated by [<sap-id>]
Flags : (I) = Idle MSAP
-------------------------------------------------------------------------------
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show service sdp-using

===============================================================================
SDP Using
===============================================================================
SvcId      SdpId              Type   Far End              Opr   I.Label E.Label
                                                          State
-------------------------------------------------------------------------------
9998       10:1               Spok   10.0.0.2             Up    524281  524281
-------------------------------------------------------------------------------
Number of SDPs : 1
-------------------------------------------------------------------------------
===============================================================================
```

## 4.2 VPRN validation

Verify that the VPRN services are operational.

Use the following commands:

- `show service service-using vprn`
- `show router service-id status`
- `show service id service-id base`
- `show router service-id interface`
- `show router service-id route-table`
- `show router service-id route-table ipv6`

```text
[gl:/configure]
A:admin@MASTER# show service service-using vprn

===============================================================================
Services [vprn]
===============================================================================
ServiceId    Type      Adm  Opr  CustomerId Service Name
-------------------------------------------------------------------------------
9998         VPRN      Up   Up   1          9998
9999         VPRN      Up   Up   1          9999
-------------------------------------------------------------------------------
Matching Services : 2
-------------------------------------------------------------------------------
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router "9998" status

===============================================================================
Router Status (Service: 9998)
===============================================================================
                         Admin State                        Oper State
-------------------------------------------------------------------------------
Router                   Up                                 Up
OSPFv2                   Not configured                     Not configured
RIP                      Not configured                     Not configured
RIP-NG                   Not configured                     Not configured
ISIS                     Not configured                     Not configured
MPLS                     Not configured                     Not configured
RSVP                     Not configured                     Not configured
LDP                      Not configured                     Not configured
BGP                      Not configured                     Not configured
IGMP                     Not configured                     Not configured
MLD                      Not configured                     Not configured
PIM                      Not configured                     Not configured
PIMv4                    Not configured                     Not configured
PIMv6                    Not configured                     Not configured
OSPFv3                   Not configured                     Not configured
MSDP                     Not configured                     Not configured
PCE                      Not configured                     Not configured
PCC                      Not configured                     Not configured

Max IPv4 Routes          No Limit
Max IPv6 Routes          No Limit
Total IPv4 Routes        17
Total IPv6 Routes        12
```

```text
[gl:/configure]
A:admin@MASTER# show service id 9998 base

===============================================================================
Service Basic Information
===============================================================================
Service Id        : 9998                Vpn Id            : 0
Service Type      : VPRN
MACSec enabled    : no
Name              : 9998
Description       : (Not Specified)
Customer Id       : 1                   Creation Origin   : manual
Last Status Change: 03/08/2026 14:00:42
Last Mgmt Change  : 03/08/2026 14:00:42
Admin State       : Up                  Oper State        : Up

Router Oper State : Up
Route Dist.       : 65510:9998          VPRN Type         : regular
Oper Route Dist   : 65510:9998
Oper RD Type      : configured
AS Number         : None                Router Id         : 10.0.0.1
ECMP              : Enabled             ECMP Max Routes   : 1
Max IPv4 Routes   : No Limit
Local Rt Domain-Id: None                D-Path Lng Ignore : Disabled

Auto Bind Tunnel
Allow Flex-Alg-Fb : Disabled
Resolution        : any
Weighted ECMP     : Disabled            ECMP Max Routes   : 1
Strict Tnl Tag    : Disabled

Max IPv6 Routes   : No Limit
Ignore NH Metric  : Disabled
Hash Label        : Disabled
Entropy Label     : Disabled
Vrf Target        : None
Vrf Import        : import-from-9999
Vrf Export        : export-to-9999
MVPN Vrf Target   : None
MVPN Vrf Import   : None
MVPN Vrf Export   : None
Car. Sup C-VPN    : Disabled
Label mode        : vrf
BGP VPN Backup    : Disabled
BGP Export Inactv : Disabled
LOG all events    : Disabled

SAP Count         : 8                   SDP Bind Count    : 1

-------------------------------------------------------------------------------
Service Access & Destination Points
-------------------------------------------------------------------------------
Identifier                               Type         AdmMTU  OprMTU  Adm  Opr
-------------------------------------------------------------------------------
sap:1/1/c2/1:4094.1                      qinq         8936    8936    Up   Up
sap:1/1/c2/1:4094.2                      qinq         8936    8936    Up   Up
sap:1/1/c2/1:4094.3                      qinq         8936    8936    Up   Up
sap:[1/1/c2/1:50.150]                    qinq         8936    8936    Up   Up
sap:[1/1/c2/1:51.200]                    qinq         8936    8936    Up   Up
sap:[1/1/c2/1:52.300]                    qinq         8936    8936    Up   Up
sap:1/1/c4/1:0                           q-tag        8936    8936    Up   Up
sap:[bbg-1.nat-in-ip:1.2]                qinq         8936    8936    Up   Up
sdp:10:1 S(10.0.0.2)                     TLDP         0       8910    Up   Up
-------------------------------------------------------------------------------
[<sap-id>] indicates a Managed SAP
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router 9998 interface

===============================================================================
Interface Table (Service: 9998)
===============================================================================
Interface-Name                   Adm       Opr(v4/v6)  Mode    Port/SapId
   IP-Address                                                  PfxState
-------------------------------------------------------------------------------
_tmnx_nat-inside                 Up        Up/Up       VPRN    bbg-1.nat-in-ip*
   fe80::200:ff:fe01:101/64                                    PREFERRED
dual-stack                       Up        Up/Up       VPRN G* 1/1/c2/1
ipv6-only                        Up        Up/Up       VPRN G* 1/1/c2/1
loopback                         Up        Up/Up       VPRN    loopback
   9.9.9.9/32                                                  n/a
   fd07:47::aaaa/128                                           PREFERRED
   fe80::1e59:ff:fe00:0/64                                     PREFERRED
network-BNGs                     Up        Up/Up       VPRN R* spoke-10:1
   192.168.12.0/31                                             n/a
services                         Up        Up/Up       VPRN S* subscriber
   100.80.0.5/29                                               n/a
   192.168.5.5/29                                              n/a
   2001:db8:100::/56                                           PREFERRED
   2001:db8:200::/48                                           PREFERRED
   2001:db8:cccc::/56                                          PREFERRED
   2001:db8:dddd::/48                                          PREFERRED
   fe80::7e20:64ff:fe84:8365/64                                PREFERRED
toDNS64                          Up        Up/Up       VPRN    1/1/c4/1:0
   192.168.3.1/30                                              n/a
   2001:db8:aaaa::1/126                                        PREFERRED
   fe80::fa:7679:5f8b:530e/64                                  PREFERRED
vip                              Up        Up/Down     VPRN G* 1/1/c2/1
-------------------------------------------------------------------------------
Interfaces : 8
===============================================================================
* indicates that the corresponding row element may have been truncated.
```

```text
A:admin@MASTER# show router 9998 route-table

===============================================================================
Route Table (Service: 9998)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric
-------------------------------------------------------------------------------
0.0.0.0/0                                     Remote  NAT       01h42m20s  0
       NAT inside                                                   0
0.0.0.0/1                                     Remote  BGP VPN   01h42m33s  170
       Local VRF [9999:to_CARRIER1]                                 0
9.9.9.9/32                                    Local   Local     01h42m56s  0
       loopback                                                     0
88.88.88.88/29                                Remote  BGP VPN   01h42m48s  0
       Local VRF [9999:_tmnx_nat-outside_2/1]                       0
99.99.99.99/32                                Remote  BGP VPN   01h42m48s  0
       Local VRF [9999:_tmnx_nat-outside_2/1]                       0
100.80.0.0/29                                 Local   Local     01h42m33s  0
       services                                                     0
100.80.0.2/32                                 Remote  Sub Mgmt  01h42m20s  0
       [dual-stack]                                                 0
100.80.0.6/32                                 Remote  Sub Mgmt  01h42m22s  0
       [network-BNGs]                                               0
128.0.0.0/1                                   Remote  BGP VPN   01h42m33s  170
       Local VRF [9999:to_CARRIER1]                                 0
172.16.1.0/31                                 Remote  BGP VPN   01h42m46s  0
       Local VRF [9999:to_CARRIER1]                                 0
172.16.1.2/31                                 Remote  BGP VPN   01h42m24s  170
       10.0.0.2 (tunneled)                                          10
172.16.2.0/31                                 Remote  BGP VPN   01h42m46s  0
       Local VRF [9999:to_CARRIER2]                                 0
172.16.2.2/31                                 Remote  BGP VPN   01h42m24s  170
       10.0.0.2 (tunneled)                                          10
172.19.1.0/30                                 Remote  BGP VPN   01h42m46s  0
       Local VRF [9999:to_LIG]                                      0
172.20.1.0/30                                 Remote  BGP VPN   01h42m24s  170
       10.0.0.2 (tunneled)                                          10
192.168.3.0/30                                Local   Local     01h42m46s  0
       toDNS64                                                      0
192.168.5.0/29                                Local   Local     01h42m33s  0
       services                                                     0
192.168.5.2/32                                Remote  Sub Mgmt  01h42m20s  0
       [vip]                                                        0
192.168.5.6/32                                Remote  Sub Mgmt  01h42m22s  0
       [network-BNGs]                                               0
192.168.12.0/31                               Local   Local     01h42m42s  0
       network-BNGs                                                 0
199.199.199.199/32                            Remote  BGP VPN   01h42m48s  0
       Local VRF [9999:_tmnx_nat-outside_2/1]                       0
-------------------------------------------------------------------------------
No. of Routes: 21
Flags: n = Number of times nexthop is repeated
       B = BGP backup route available
       L = LFA nexthop available
       S = Sticky ECMP requested
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router 9998 route-table ipv6

===============================================================================
IPv6 Route Table (Service: 9998)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric
-------------------------------------------------------------------------------
::/1                                          Remote  BGP VPN   01h43m17s  170
       Local VRF [9999:to_CARRIER1]                                 0
64:ff9b::/96                                  Remote  NAT       01h43m03s  0
       NAT (isa-ms)                                                 0
2001:db8:100::/56                             Local   Local     01h43m16s  0
       services                                                     0
2001:db8:100::/96                             Local   Local     01h43m02s  0
       services                                                     0
2001:db8:100::2/128                           Remote  Sub Mgmt  01h42m49s  0
       [ipv6-only]                                                  0
2001:db8:100::3/128                           Remote  Sub Mgmt  01h21m20s  0
       [ipv6-only]                                                  0
2001:db8:200::/48                             Local   Local     01h43m16s  0
       services                                                     0
2001:db8:200:1::/64                           Remote  Managed   01h42m49s  0
       2001:db8:100::2                                              0
2001:db8:200:2::/64                           Remote  Managed   01h21m20s  0
       2001:db8:100::3                                              0
2001:db8:aaaa::/126                           Local   Local     01h43m28s  0
       toDNS64                                                      0
2001:db8:cccc::/56                            Local   Local     01h43m16s  0
       services                                                     0
2001:db8:cccc::/96                            Local   Local     01h43m03s  0
       services                                                     0
2001:db8:cccc::1/128                          Remote  Sub Mgmt  01h43m03s  0
       [dual-stack]                                                 0
2001:db8:dddd::/48                            Local   Local     01h43m16s  0
       services                                                     0
2001:db8:dddd::/64                            Remote  Managed   01h43m03s  0
       2001:db8:cccc::1                                             0
2001:db8:fffe::/126                           Remote  BGP VPN   01h43m08s  170
       10.0.0.2 (tunneled)                                          10
2001:db8:ffff::/126                           Remote  BGP VPN   01h43m28s  0
       Local VRF [9999:to_LIG]                                      0
8000::/1                                      Remote  BGP VPN   01h43m17s  170
       Local VRF [9999:to_CARRIER1]                                 0
fd07:47::aaaa/128                             Local   Local     01h43m37s  0
       loopback                                                     0
-------------------------------------------------------------------------------
No. of Routes: 19
Flags: n = Number of times nexthop is repeated
       B = BGP backup route available
       L = LFA nexthop available
       S = Sticky ECMP requested
===============================================================================
```

## 4.3 BGP inside VPRN 9999

Use the following commands to review BGP peer status and advertised and received routes:

- `show router 9999 bgp neighbor ip-neighbor advertised-routes`
- `show router 9999 bgp neighbor ip-neighbor received-routes`
- `show router 9999 bgp neighbor ip-neighbor advertised-routes ipv6`
- `show router 9999 bgp neighbor ip-neighbor received-routes ipv6`

```text
[gl:/configure]
A:admin@MASTER# show router 9999 bgp neighbor "172.16.1.1" advertised-routes
===============================================================================
 BGP Router ID:10.0.0.1         AS:65520       Local AS:65520
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge,
                 w - unused-weight-only
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     IGP Cost
      As-Path                                                        Label
-------------------------------------------------------------------------------
?     88.88.88.88/29                                     n/a         50
      172.16.1.0                                         None        n/a
      65520                                                          -
?     99.99.99.99/32                                     n/a         50
      172.16.1.0                                         None        n/a
      65520                                                          -
?     199.199.199.199/32                                 n/a         50
      172.16.1.0                                         None        n/a
      65520                                                          -
-------------------------------------------------------------------------------
Routes : 3
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router 9999 bgp neighbor "172.16.1.1" received-routes
===============================================================================
 BGP Router ID:10.0.0.1         AS:65520       Local AS:65520
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge,
                 w - unused-weight-only
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     IGP Cost
      As-Path                                                        Label
-------------------------------------------------------------------------------
u*>?  0.0.0.0/1                                          n/a         None
      172.16.1.1                                         None        0
      65501                                                          -
u*>?  128.0.0.0/1                                        n/a         None
      172.16.1.1                                         None        0
      65501                                                          -
-------------------------------------------------------------------------------
Routes : 2
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router 9999 bgp neighbor "172.16.1.1" advertised-routes ipv6
===============================================================================
 BGP Router ID:10.0.0.1         AS:65520       Local AS:65520
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge,
                 w - unused-weight-only
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv6 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     IGP Cost
      As-Path                                                        Label
-------------------------------------------------------------------------------
i     2001:db8:100::/56                                  n/a         50
      ::ac10:100                                         None        n/a
      65520                                                          -
i     2001:db8:200::/48                                  n/a         50
      ::ac10:100                                         None        n/a
      65520                                                          -
i     2001:db8:cccc::/56                                 n/a         50
      ::ac10:100                                         None        n/a
      65520                                                          -
i     2001:db8:dddd::/48                                 n/a         50
      ::ac10:100                                         None        n/a
      65520                                                          -
-------------------------------------------------------------------------------
Routes : 4
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show router 9999 bgp neighbor "172.16.1.1" received-routes ipv6
===============================================================================
 BGP Router ID:10.0.0.1         AS:65520       Local AS:65520
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge,
                 w - unused-weight-only
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv6 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     IGP Cost
      As-Path                                                        Label
-------------------------------------------------------------------------------
u*>?  ::/1                                               n/a         None
      ::ffff:172.16.1.1                                  None        0
      65501                                                          -
u*>?  8000::/1                                           n/a         None
      ::ffff:172.16.1.1                                  None        0
      65501                                                          -
-------------------------------------------------------------------------------
Routes : 2
===============================================================================
```
