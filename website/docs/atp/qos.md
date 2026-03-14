---
sidebar_position: 4
sidebar_label: 5. QoS
---

# 5. QoS

## 5.1 Verificar políticas de QoS en SAP

Revisa las políticas de ingreso y egreso aplicadas sobre los SAPs:

- `show qos sap-ingress`
- `show qos sap-egress`

```text
[gl:/configure]
A:admin@MASTER# show qos sap-ingress

===============================================================================
Sap Ingress Policies
===============================================================================
Policy-Id  Scope     Name                     Description
-------------------------------------------------------------------------------
1          Template  default                  Default SAP ingress QoS policy.
10         Template  10
65536      Template  _tmnx_nat_lns_ingress    NAT/LNS ingress QoS policy
65538      Template  _tmnx_nat_lns_ingress_v2 NAT/LNS ingress QoS policy for
                                              ISAv2
65539      Template  _tmnx_nat_lns_ingress_v3 NAT/LNS ingress QoS policy for
                                              ESA
65540      Template  _tmnx_nat_ingress_polici NAT ingress QoS policy for
                     ng                       policing
-------------------------------------------------------------------------------
Number of Policies : 6
-------------------------------------------------------------------------------
===============================================================================
```

```text
[gl:/configure]
A:admin@MASTER# show qos sap-egress

===============================================================================
Sap Egress Policies
===============================================================================
Policy-Id  Scope     Name                     Description
-------------------------------------------------------------------------------
1          Template  default                  Default SAP egress QoS policy.
10         Template  10
65536      Template  _tmnx_nat_lns_egress     NAT/LNS egress QoS policy
65538      Template  _tmnx_nat_lns_egress_v2  NAT/LNS egress QoS policy for
                                              ISAv2
65539      Template  _tmnx_nat_lns_egress_v3  NAT/LNS egress QoS policy for ESA
-------------------------------------------------------------------------------
Number of Policies : 5
-------------------------------------------------------------------------------
===============================================================================
```

## 5.2 Verificar asociación de perfiles SLA

Revisa los perfiles SLA disponibles para subscriber management:

- `show subscriber-mgmt sla-profile`

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
