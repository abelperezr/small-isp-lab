---
sidebar_position: 10
sidebar_label: 10. ONT tests
---

# 10. ONT tests

## 10.0 Pre-checks

Before running the tests from `ont1` and `pc1`, identify the currently active IPv6 delegated prefix on `wan1`.

Quick option using `docker exec` from the host:

```bash
docker exec ont1 sh -lc 'ip -6 addr show dev eth1.150; echo; ip -6 addr show dev eth2'
docker exec pc1 sh -lc 'ip -6 addr show dev eth1; echo; ip -6 route show dev eth1'
```

What to validate:

- `eth1.150` on `ont1` has a WAN IPv6 `/128`
- `eth2` on `ont1` has a LAN address from the current delegated prefix, for example `2001:db8:200:3::1/64`
- `pc1` should receive that same prefix on `eth1`

Important:

- do not assume the delegated prefix will always be `2001:db8:200:1::/64`
- after a reconnect or lease change, `pc1` may temporarily keep a previous prefix in addition to the current one
- if `pc1` shows more than one global prefix on `eth1`, use the prefix currently configured on `ont1` `eth2` as the source of truth

## Connectivity from ONT1

Thanks to the fact that the ONT image has PBR (Policy Based Routing), it is possible to ping each of the DHCP gateways corresponding to its services:

### Ping IPv4 CGNAT Gateway (Dual-Stack WAN2)

Option using `docker exec` from the host:

```bash
docker exec ont1 ping -c 4 100.80.0.1
```

```text
user@ont1  ~  ping 100.80.0.1
PING 100.80.0.1 (100.80.0.1) 56(84) bytes of data.
64 bytes from 100.80.0.1: icmp_seq=1 ttl=64 time=2.14 ms
64 bytes from 100.80.0.1: icmp_seq=2 ttl=64 time=1.62 ms
64 bytes from 100.80.0.1: icmp_seq=3 ttl=64 time=1.81 ms
64 bytes from 100.80.0.1: icmp_seq=4 ttl=64 time=1.43 ms
^C
--- 100.80.0.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss
```

### Ping IPv4 VIP Gateway (WAN3)

Option using `docker exec` from the host:

```bash
docker exec ont1 ping -c 4 192.168.5.1
```

```text
user@ont1  ~  ping 192.168.5.1
PING 192.168.5.1 (192.168.5.1) 56(84) bytes of data.
64 bytes from 192.168.5.1: icmp_seq=1 ttl=64 time=2.33 ms
64 bytes from 192.168.5.1: icmp_seq=2 ttl=64 time=1.81 ms
^C
--- 192.168.5.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss
```

### IPv6 WAN Ping (IPv6-only WAN1)

Option using `docker exec` from the host:

```bash
docker exec ont1 ip -6 -o addr show dev eth1.150 scope global
docker exec ont1 ping -6 -c 4 -I <CURRENT_WAN1_IPV6> 2001:db8:aaaa::2
```

Expected result:

- `ont1` reaches `2001:db8:aaaa::2` using the current WAN IPv6 on `eth1.150` as source

## 10.1 Check Prefix Delegation on PC1

On PC1 you can see the delegated prefix assigned via DHCPv6-PD.

Option using `docker exec` from the host:

```bash
docker exec ont1 ip -6 addr show dev eth2
docker exec pc1 ip -6 addr show dev eth1
```

What to validate:

- `ont1` advertises the LAN gateway for the current delegated prefix on `eth2`, for example `2001:db8:200:3::1/64`
- `pc1` receives a global address from that same prefix on `eth1`

Example:

- if `ont1` shows `2001:db8:200:3::1/64` on `eth2`
- then `pc1` should show an address like `2001:db8:200:3:xxxx:xxxx:xxxx:xxxx/64`

This prefix is routed to `ont1` by the BNG, and `ont1` advertises it to `pc1` on the LAN through Router Advertisement.

Note:

- if `pc1` keeps a previous global prefix in addition to the current one, that is not necessarily a service failure
- it may be a stale prefix temporarily kept due to RA lifetime
- in that case, use the current prefix configured on `ont1` as the reference for the reachability test
- if a clean validation is required, restart `pc1` before continuing:

```bash
docker restart pc1
```

## 10.2 Check Reachability from PC1

Once the current delegated prefix has been identified on `ont1`, `pc1` must be able to reach:

- the current IPv6 LAN gateway on `ont1`
- the internal lab DNS server

### IPv6 LAN Gateway

Option using `docker exec` from the host:

```bash
docker exec ont1 ip -6 -o addr show dev eth2 scope global
docker exec pc1 ping -6 -c 4 <CURRENT_LAN_GW_ON_ONT1>
```

Example:

```bash
docker exec pc1 ping -6 -c 4 2001:db8:200:3::1
```

Expected result:

- `pc1` reaches the current IPv6 LAN gateway on `ont1`

### Internal Lab DNS

Option using `docker exec` from the host:

```bash
docker exec pc1 ping -6 -c 4 2001:db8:aaaa::2
```

```text
[*]─[pc1]─[~]
└──> ping -6 2001:db8:aaaa::2
PING 2001:db8:aaaa::2(2001:db8:aaaa::2) 56 data bytes
64 bytes from 2001:db8:aaaa::2: icmp_seq=1 ttl=61 time=28.1 ms
64 bytes from 2001:db8:aaaa::2: icmp_seq=2 ttl=61 time=1.18 ms
64 bytes from 2001:db8:aaaa::2: icmp_seq=3 ttl=61 time=1.42 ms
64 bytes from 2001:db8:aaaa::2: icmp_seq=4 ttl=61 time=3.30 ms

--- 2001:db8:aaaa::2 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss
```

Expected result:

- `ont1` has an active WAN IPv6 on `eth1.150`
- `ont1` has an active LAN IPv6 gateway on `eth2` derived from the current delegated prefix
- `pc1` receives the current delegated prefix on `eth1`
- `pc1` reaches the current LAN gateway on `ont1`
- PC1 reaches the internal lab DNS at `2001:db8:aaaa::2`

Operational note:

- if `pc1` shows more than one global IPv6 prefix, validation must be done against the prefix currently present on `ont1`
- an old prefix still visible on `pc1` may persist for some time due to the previous RA lifetime and does not necessarily mean a BNG or ONT failure
