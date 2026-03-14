---
sidebar_position: 4
---

# OLT - Nokia SR Linux

## General Information

| Parameter | Value |
|-----------|-------|
| **Hostname** | olt |
| **Model** | Nokia SR Linux 25.10 |
| **Management IP** | 10.99.1.4 |
| **SSH port** | 56614 |

## Function in Topology

The OLT acts as **access switch** using MAC-VRFs for bridging between the BNGs and the ONTs. Each service has its own bridge domain with distinct S-VLAN, plus a bridge domain for SRRP.

| MAC-VRF | S-VLAN | C-VLAN | Service | Interfaces |
|---------|--------|--------|----------|------------|
| bd-50 | 50 | 150 | IPv6-only | e1/1.50, e1/2.50, e1/3.150, e1/6.150 |
| bd-51 | 51 | 200 | Dual-Stack | e1/1.51, e1/2.51, e1/4.200 |
| bd-52 | 52 | 300 | VIP | e1/1.52, e1/2.52, e1/5.300 |
| bd-srrp | 4094 | None | SRRP Messages | e1/1.4094, e1/2.4094 |


---


### 1.1. TO BNG MASTER

```text
set /interface ethernet-1/1 admin-state enable
set /interface ethernet-1/1 vlan-tagging true
set /interface ethernet-1/1 subinterface 50 type bridged
set /interface ethernet-1/1 subinterface 50 admin-state enable
set /interface ethernet-1/1 subinterface 50 vlan encap single-tagged vlan-id 50
set /interface ethernet-1/1 subinterface 51 type bridged
set /interface ethernet-1/1 subinterface 51 admin-state enable
set /interface ethernet-1/1 subinterface 51 vlan encap single-tagged vlan-id 51
set /interface ethernet-1/1 subinterface 52 type bridged
set /interface ethernet-1/1 subinterface 52 admin-state enable
set /interface ethernet-1/1 subinterface 52 vlan encap single-tagged vlan-id 52
```


### 1.2. TO BNG SLAVE

```text
set /interface ethernet-1/2 admin-state enable
set /interface ethernet-1/2 vlan-tagging true
set /interface ethernet-1/2 subinterface 50 type bridged
set /interface ethernet-1/2 subinterface 50 admin-state enable
set /interface ethernet-1/2 subinterface 50 vlan encap single-tagged vlan-id 50
set /interface ethernet-1/2 subinterface 51 type bridged
set /interface ethernet-1/2 subinterface 51 admin-state enable
set /interface ethernet-1/2 subinterface 51 vlan encap single-tagged vlan-id 51
set /interface ethernet-1/2 subinterface 52 type bridged
set /interface ethernet-1/2 subinterface 52 admin-state enable
set /interface ethernet-1/2 subinterface 52 vlan encap single-tagged vlan-id 52
```


#### 1.3.1. WAN1 C-VLAN 150

```text
set /interface ethernet-1/3 admin-state enable
set /interface ethernet-1/3 vlan-tagging true
set /interface ethernet-1/3 subinterface 150 type bridged
set /interface ethernet-1/3 subinterface 150 admin-state enable
set /interface ethernet-1/3 subinterface 150 vlan encap single-tagged-range low-vlan-id 150 high-vlan-id 150
```


#### 1.3.2. WAN2 C-VLAN 200

```text
set /interface ethernet-1/4 admin-state enable
set /interface ethernet-1/4 vlan-tagging true
set /interface ethernet-1/4 subinterface 200 type bridged
set /interface ethernet-1/4 subinterface 200 admin-state enable
set /interface ethernet-1/4 subinterface 200 vlan encap single-tagged-range low-vlan-id 200 high-vlan-id 200
```


#### 1.3.3. WAN3 C-VLAN 300

```text
set /interface ethernet-1/5 admin-state enable
set /interface ethernet-1/5 vlan-tagging true
set /interface ethernet-1/5 subinterface 300 type bridged
set /interface ethernet-1/5 subinterface 300 admin-state enable
set /interface ethernet-1/5 subinterface 300 vlan encap single-tagged-range low-vlan-id 300 high-vlan-id 300
```


#### 1.4.1. WAN1 C-VLAN 150

```text
set /interface ethernet-1/6 admin-state enable
set /interface ethernet-1/6 vlan-tagging true
set /interface ethernet-1/6 subinterface 150 type bridged
set /interface ethernet-1/6 subinterface 150 admin-state enable
set /interface ethernet-1/6 subinterface 150 vlan encap single-tagged-range low-vlan-id 150 high-vlan-id 150
```


### 1.5. TPID

```text
set /interface ethernet-1/1 tpid TPID_ANY
set /interface ethernet-1/2 tpid TPID_ANY
set /interface ethernet-1/3 tpid TPID_ANY
set /interface ethernet-1/4 tpid TPID_ANY
set /interface ethernet-1/5 tpid TPID_ANY
set /interface ethernet-1/6 tpid TPID_ANY
```


### 2.1. MAC-VRF BD-50

```text
set /network-instance bd-50 type mac-vrf
set /network-instance bd-50 admin-state enable
set /network-instance bd-50 interface ethernet-1/1.50
set /network-instance bd-50 interface ethernet-1/2.50
set /network-instance bd-50 interface ethernet-1/3.150
set /network-instance bd-50 interface ethernet-1/6.150
```


### 2.2. MAC-VRF BD-51

```text
set /network-instance bd-51 type mac-vrf
set /network-instance bd-51 admin-state enable
set /network-instance bd-51 interface ethernet-1/1.51
set /network-instance bd-51 interface ethernet-1/2.51
set /network-instance bd-51 interface ethernet-1/4.200
```


### 23. MAC-VRF BD-52

```text
set /network-instance bd-52 type mac-vrf
set /network-instance bd-52 admin-state enable
set /network-instance bd-52 interface ethernet-1/1.52
set /network-instance bd-52 interface ethernet-1/2.52
set /network-instance bd-52 interface ethernet-1/5.300
```


## 3. SRRP MESSAGE PATH

```text
set /interface ethernet-1/1 subinterface 4094 type bridged
set /interface ethernet-1/1 subinterface 4094 admin-state enable
set /interface ethernet-1/1 subinterface 4094 vlan encap single-tagged vlan-id 4094
set /interface ethernet-1/2 subinterface 4094 type bridged
set /interface ethernet-1/2 subinterface 4094 admin-state enable
set /interface ethernet-1/2 subinterface 4094 vlan encap single-tagged vlan-id 4094
```


## 4. MAC-VRF BD-SRRP

```text
set /network-instance bd-srrp type mac-vrf
set /network-instance bd-srrp admin-state enable
set /network-instance bd-srrp interface ethernet-1/1.4094
set /network-instance bd-srrp interface ethernet-1/2.4094
set / system aaa authentication admin-user password lab123
```


## 5. LOGS

```text
set /system logging network-instance mgmt
set /system logging remote-server 10.99.1.16 transport udp
set /system logging remote-server 10.99.1.16 remote-port 1514
set /system logging remote-server 10.99.1.16 format RSYSLOG_SyslogProtocol23Format
set /system logging remote-server 10.99.1.16 facility local6 priority match-above informational
```
