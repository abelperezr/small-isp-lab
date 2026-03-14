---
sidebar_position: 2.1
sidebar_label: 2. Carrier baseline validation
---

# 2. Carrier Baseline Validation

## Objective

Validate the baseline status of both carriers (`carrier1` and `carrier2`) before running advanced SRRP/BGP and service tests.

## Scope

- Operational status of interfaces and subinterfaces.
- IPv4/IPv6 route table health.
- BGP neighbor and summary status.

## 2.1 Interface validation

Commands:

- `show interface all`
- `show interface ethernet-1/1 detail`

Example:

```text
A:admin@carrier1# show interface all
ethernet-1/1 is up
  ethernet-1/1.0 is up
    IPv4 addr : 172.16.1.1/31
    IPv6 addr : 2001:db8:f1::1/126
ethernet-1/2 is up
  ethernet-1/2.0 is up
    IPv4 addr : 172.16.1.3/31
    IPv6 addr : 2001:db8:f1::5/126
ethernet-1/3 is up
  ethernet-1/3.0 is up
    IPv4 addr : 10.99.100.1/30
    IPv6 addr : fd00:a1::1/126
```

Expected result:

- `ethernet-1/1`, `ethernet-1/2`, `ethernet-1/3` are `up`.
- `.0` subinterfaces are `up`.
- L3 addressing matches the topology design.

## 2.2 Route-table validation

Commands:

- `show network-instance route-table ipv4-unicast summary`
- `show network-instance route-table ipv6-unicast summary`

Expected result:

- Egress `static` routes (`0.0.0.0/0`, `::/0`, half-default) are active.
- ISP prefixes (`99.99.99.99/32`, `88.88.88.88/29`, `199.199.199.199/32` and IPv6 pools) are learned via BGP.
- Connected local prefixes to BNG links are present.

## 2.3 BGP validation

Commands:

- `show network-instance protocols bgp neighbor`
- `show network-instance protocols bgp summary`

Example:

```text
A:admin@carrier1# show network-instance protocols bgp neighbor
Peer 172.16.1.0 established
Peer 172.16.1.2 established
```

Expected result:

- 2 neighbors per carrier (to BNG MASTER and BNG SLAVE).
- Sessions in `established` state.
- IPv4 and IPv6 AFI/SAFI active.

## 2.4 Final checklist

- `show interface all` has no critical interfaces down.
- IPv4/IPv6 route tables include active static and BGP routes.
- BGP is stable against both BNGs on each carrier.
