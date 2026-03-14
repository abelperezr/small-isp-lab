---
sidebar_position: 6
---

# Carrier 2 - Nokia SR Linux

## General Information

| Parameter | Value |
|-----------|-------|
| **Hostname** | carrier2 |
| **Model** | Nokia SR Linux 25.10 |
| **Management IP** | 10.99.1.253 |
| **SSH port** | 56611 |
| **ASN** | 65502 |
| **Loopback** | 10.255.2.1/32 |
| **Role** | Secondary Carrier (LP 150 in BNGs) |

## Function in Topology

Carrier 2 is the **secondary** transit provider. The BNGs import their routes with Local-Preference 150. Identical configuration to Carrier 1 but with different addressing.

| neighbor | IP | Peer AS | Description |
|----------|----|---------|-------------|
| BNG MASTER | 172.16.2.0 | 65520 | eBGP IPv4+IPv6 |
| BNG SLAVE | 172.16.2.2 | 65520 | eBGP IPv4+IPv6 |


---


## 1. 1 TO BNG MASTER

```text
set /interface ethernet-1/1 admin-state enable
set /interface ethernet-1/1 subinterface 0 admin-state enable
set /interface ethernet-1/1 subinterface 0 ipv4 admin-state enable
set /interface ethernet-1/1 subinterface 0 ipv4 address 172.16.2.1/31
set /interface ethernet-1/1 subinterface 0 ipv6 admin-state enable
set /interface ethernet-1/1 subinterface 0 ipv6 address 2001:db8:f2::1/126
```


### 1.2. TO BNG SLAVE

```text
set /interface ethernet-1/2 admin-state enable
set /interface ethernet-1/2 subinterface 0 admin-state enable
set /interface ethernet-1/2 subinterface 0 ipv4 admin-state enable
set /interface ethernet-1/2 subinterface 0 ipv4 address 172.16.2.3/31
set /interface ethernet-1/2 subinterface 0 ipv6 admin-state enable
set /interface ethernet-1/2 subinterface 0 ipv6 address 2001:db8:f2::5/126
```


### 1.3. TO INTERNET

```text
set /interface ethernet-1/3 admin-state enable
set /interface ethernet-1/3 subinterface 0 admin-state enable
set /interface ethernet-1/3 subinterface 0 ipv4 admin-state enable
set /interface ethernet-1/3 subinterface 0 ipv4 address 10.99.200.1/30
set /interface ethernet-1/3 subinterface 0 ipv6 admin-state enable
set /interface ethernet-1/3 subinterface 0 ipv6 address fd00:a2::1/126
```


### 1.4. LOOPBACK

```text
set /interface lo0 admin-state enable
set /interface lo0 subinterface 0 admin-state enable
set /interface lo0 subinterface 0 ipv4 admin-state enable
set /interface lo0 subinterface 0 ipv4 address 10.255.2.1/32
```


## 2. NETWORK INSTANCE

```text
set /network-instance default type default
set /network-instance default admin-state enable
set /network-instance default interface ethernet-1/1.0
set /network-instance default interface ethernet-1/2.0
set /network-instance default interface ethernet-1/3.0
set /network-instance default interface lo0.0
```


### 3.1. PREFIX-SET

```text
set /routing-policy prefix-set isp-v4 prefix 99.99.99.99/32 mask-length-range exact
set /routing-policy prefix-set isp-v4 prefix 88.88.88.88/29 mask-length-range exact
set /routing-policy prefix-set isp-v4 prefix 199.199.199.199/32 mask-length-range exact
set /routing-policy prefix-set isp-v6 prefix 2001:db8:100::/56 mask-length-range exact
set /routing-policy prefix-set isp-v6 prefix 2001:db8:200::/48 mask-length-range exact
set /routing-policy prefix-set isp-v6 prefix 2001:db8:cccc::/56 mask-length-range exact
set /routing-policy prefix-set isp-v6 prefix 2001:db8:dddd::/48 mask-length-range exact
set /routing-policy prefix-set half-default-v4-low prefix 0.0.0.0/1 mask-length-range exact
set /routing-policy prefix-set half-default-v4-high prefix 128.0.0.0/1 mask-length-range exact
set /routing-policy prefix-set half-default-v6-low prefix ::/1 mask-length-range exact
set /routing-policy prefix-set half-default-v6-high prefix 8000::/1 mask-length-range exact
```


### 3.2. EXPORT TO BNGS

```text
set /routing-policy policy export-to-bngs statement 10 match prefix prefix-set half-default-v4-low
set /routing-policy policy export-to-bngs statement 10 action policy-result accept
set /routing-policy policy export-to-bngs statement 15 match prefix prefix-set half-default-v4-high
set /routing-policy policy export-to-bngs statement 15 action policy-result accept
set /routing-policy policy export-to-bngs statement 20 match prefix prefix-set half-default-v6-low
set /routing-policy policy export-to-bngs statement 20 action policy-result accept
set /routing-policy policy export-to-bngs statement 25 match prefix prefix-set half-default-v6-high
set /routing-policy policy export-to-bngs statement 25 action policy-result accept
set /routing-policy policy export-to-bngs statement 99 action policy-result reject
```


### 3.3. IMPORT FROM BNGS

```text
set /routing-policy policy import-from-bngs statement 10 match prefix prefix-set isp-v4
set /routing-policy policy import-from-bngs statement 10 action policy-result accept
set /routing-policy policy import-from-bngs statement 20 match prefix prefix-set isp-v6
set /routing-policy policy import-from-bngs statement 20 action policy-result accept
set /routing-policy policy import-from-bngs statement 99 action policy-result reject
```


## 4. STATIC ROUTES

```text
set /network-instance default next-hop-groups group to-gateway nexthop 0 ip-address 10.99.200.2
set /network-instance default next-hop-groups group to-gateway nexthop 0 admin-state enable
set /network-instance default next-hop-groups group to-gateway-v6 nexthop 0 ip-address fd00:a2::2
set /network-instance default next-hop-groups group to-gateway-v6 nexthop 0 admin-state enable
```


### 4.1. IPv4 STATIC ROUTES TO UPSTREAM GATEWAY

```text
set /network-instance default static-routes route 0.0.0.0/0 admin-state enable
set /network-instance default static-routes route 0.0.0.0/0 next-hop-group to-gateway
set /network-instance default static-routes route 0.0.0.0/1 admin-state enable
set /network-instance default static-routes route 0.0.0.0/1 next-hop-group to-gateway
set /network-instance default static-routes route 128.0.0.0/1 admin-state enable
set /network-instance default static-routes route 128.0.0.0/1 next-hop-group to-gateway
```


### 4.2. IPv6 DEFAULT AND HALF-DEFAULT STATIC ROUTES

```text
set /network-instance default static-routes route ::/0 admin-state enable
set /network-instance default static-routes route ::/0 next-hop-group to-gateway-v6
set /network-instance default static-routes route ::/1 admin-state enable
set /network-instance default static-routes route ::/1 next-hop-group to-gateway-v6
set /network-instance default static-routes route 8000::/1 admin-state enable
set /network-instance default static-routes route 8000::/1 next-hop-group to-gateway-v6
```


## 5. BGP

```text
set /network-instance default protocols bgp admin-state enable
set /network-instance default protocols bgp autonomous-system 65502
set /network-instance default protocols bgp router-id 10.255.2.1
set /network-instance default protocols bgp afi-safi ipv4-unicast admin-state enable
set /network-instance default protocols bgp afi-safi ipv6-unicast admin-state enable
```


### 5.1. GROUPS

```text
set /network-instance default protocols bgp group to-bngs admin-state enable
set /network-instance default protocols bgp group to-bngs export-policy [export-to-bngs]
set /network-instance default protocols bgp group to-bngs import-policy [import-from-bngs]
set /network-instance default protocols bgp group to-bngs peer-as 65520
set /network-instance default protocols bgp group to-bngs timers connect-retry 10
set /network-instance default protocols bgp group to-bngs afi-safi ipv4-unicast admin-state enable
set /network-instance default protocols bgp group to-bngs afi-safi ipv6-unicast admin-state enable
```


### 5.2. NEIGHBORS

```text
set /network-instance default protocols bgp neighbor 172.16.2.0 admin-state enable
set /network-instance default protocols bgp neighbor 172.16.2.0 description "to-BNG-MASTER"
set /network-instance default protocols bgp neighbor 172.16.2.0 peer-group to-bngs
set /network-instance default protocols bgp neighbor 172.16.2.2 admin-state enable
set /network-instance default protocols bgp neighbor 172.16.2.2 description "to-BNG-SLAVE"
set /network-instance default protocols bgp neighbor 172.16.2.2 peer-group to-bngs
```


## 6. CREDENTIALS

```text
set / system aaa authentication admin-user password lab123
```


## 7. LOGS

```text
set /system logging network-instance mgmt
set /system logging remote-server 10.99.1.16 transport udp
set /system logging remote-server 10.99.1.16 remote-port 1514
set /system logging remote-server 10.99.1.16 format RSYSLOG_SyslogProtocol23Format
set /system logging remote-server 10.99.1.16 facility local6 priority match-above informational
```
