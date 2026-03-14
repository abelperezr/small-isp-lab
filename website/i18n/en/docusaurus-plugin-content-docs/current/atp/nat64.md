---
sidebar_position: 8
sidebar_label: 9. NAT64
---

# 9. NAT64 - Tests

## 9.1 Explicit DNS64 Resolution

From `ont1`, query the lab DNS64 server for a name that only has an `A` record:

```bash
docker exec ont1 sh -lc 'nslookup ipv4.google.com 2001:db8:aaaa::2'
```

Validated output:

```text
Server:		2001:db8:aaaa::2
Address:	2001:db8:aaaa::2#53

Non-authoritative answer:
ipv4.google.com	canonical name = ipv4.l.google.com.
Name:	ipv4.l.google.com
Address: 172.217.28.110
Name:	ipv4.l.google.com
Address: 64:ff9b::acd9:1c6e
```

Expected result:

- DNS64 returns the original `A` record
- it also returns a synthesized `AAAA` within `64:ff9b::/96`

:::tip[Validation from PC1]
`pc1` can explicitly query the lab DNS64 server even if its default resolver is not using DNS64:

```bash
docker exec pc1 sh -lc 'dig @2001:db8:aaaa::2 ipv4.google.com AAAA +short'
```

Expected result:

- a response similar to `64:ff9b::acd9:1c6e` is returned
:::

## 9.2 NAT64 Ping Test

From ONT1 (which is IPv6-only on WAN1), ping the NAT64 prefix:

```text
user@ont1  ~  ping -6 64:ff9b::808:808
PING 64:ff9b::808:808(64:ff9b::808:808) 56 data bytes
64 bytes from 64:ff9b::808:808: icmp_seq=1 ttl=103 time=31.3 ms
64 bytes from 64:ff9b::808:808: icmp_seq=2 ttl=103 time=15.3 ms
64 bytes from 64:ff9b::808:808: icmp_seq=3 ttl=103 time=14.3 ms
64 bytes from 64:ff9b::808:808: icmp_seq=4 ttl=103 time=12.1 ms
64 bytes from 64:ff9b::808:808: icmp_seq=5 ttl=103 time=19.6 ms
^C
--- 64:ff9b::808:808 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 3996ms
```

The address `64:ff9b::808:808` is the NAT64 representation of `8.8.8.8` (Google DNS).

The following DNS64 + ICMP flow using the hostname was also validated:

```bash
docker exec ont1 sh -lc 'ping -6 -c 4 ipv4.google.com'
```

Validated output:

```text
PING ipv4.google.com(pnboga-ac-in-f14.1e100.net (64:ff9b::acd9:1c6e)) 56 data bytes
64 bytes from gru06s09-in-f110.1e100.net (64:ff9b::acd9:1c6e): icmp_seq=1 ttl=112 time=18.3 ms
64 bytes from pnboga-ac-in-f14.1e100.net (64:ff9b::acd9:1c6e): icmp_seq=2 ttl=112 time=22.8 ms
64 bytes from pnboga-ac-in-f14.1e100.net (64:ff9b::acd9:1c6e): icmp_seq=3 ttl=112 time=24.9 ms
64 bytes from pnboga-ac-in-f14.1e100.net (64:ff9b::acd9:1c6e): icmp_seq=4 ttl=112 time=18.9 ms
```

Expected result:

- the hostname resolves to a synthesized `AAAA`
- IPv6 ping works over NAT64

## 9.3 HTTP Test over NAT64

From `ont1`, validate real application traffic:

```bash
docker exec ont1 sh -lc 'curl -6 -I --max-time 15 http://example.com'
```

Validated output:

```text
HTTP/1.1 200 OK
Date: Wed, 11 Mar 2026 14:44:56 GMT
Content-Type: text/html
Connection: keep-alive
Last-Modified: Thu, 05 Mar 2026 11:55:05 GMT
Accept-Ranges: bytes
Server: cloudflare
```

Expected result:

- `curl` returns `HTTP/1.1 200 OK`
- this proves NAT64 works not only for ICMP but also for HTTP traffic

## 9.4 Validation from PC1 behind ONT1

`pc1` receives IPv6 connectivity via Prefix Delegation behind `ont1`. Even if its default DNS does not use the lab DNS64 server, the following were validated:

1. connectivity to the lab DNS64 server
2. explicit DNS64 resolution
3. IPv6 reachability to a known NAT64 destination

Commands:

```bash
docker exec pc1 sh -lc 'ping -6 -c 4 2001:db8:aaaa::2'
docker exec pc1 sh -lc 'dig @2001:db8:aaaa::2 ipv4.google.com AAAA +short'
docker exec pc1 sh -lc 'ping -6 -c 4 64:ff9b::808:808'
```

Expected result:

- `pc1` reaches the DNS64 server `2001:db8:aaaa::2`
- the `dig` query returns a synthesized `AAAA`
- ping to the NAT64 prefix works from the LAN behind `ont1`

## 9.5 Verify NAT64 Sessions

From BNG MASTER, search for the NAT64 session:

```text
tools dump nat sessions
```

Find an entry similar to:

```text
-------------------------------------------------------------------------------
Owner               : NAT64-Sub@2001:db8:cccc::1
Router              : 9998
Policy              : nat64-pol
FlowType            : ICMP              Timeout (sec)       : 4
Inside IP Addr      : 2001:db8:cccc::1
Inside Identifier   : 480
Outside IP Addr     : 199.199.199.199
Outside Identifier  : 1118
Foreign IP Addr     : 8.8.8.8
Nat Group           : 1
Nat Group Member    : 1
-------------------------------------------------------------------------------
```

:::info[NAT64 components]

- **NAT64 prefix**: `64:ff9b::/96`
- **Pool Outside**: `199.199.199.199` (nat64-pool in VPRN 9999)
- **DNS64**: BIND server on `2001:db8:aaaa::2` that synthesizes AAAA records
- **IPv6 Filter**: Filter entry 10 redirects traffic towards `64:ff9b::/96` to the NAT64 engine
:::

## 9.6 Verify NAT64 Port Blocks

From ONT1 or ONT2, run:

```text
ping -6 ipv4.tlund.se
```

Option using `docker exec` from the host:

```bash
docker exec ont1 ping -6 -c 4 ipv4.tlund.se
docker exec ont2 ping -6 -c 4 ipv4.tlund.se
```

Then, on the BNG MASTER or SLAVE, run:

```text
pyexec "cf3:\scripts\nat64_portblocks.py"
```

The output should show a `NAT64` entry for the IPv6-only subscriber, similar to this:

```text
[/]
A:admin@MASTER# pyexec "cf3:\scripts\nat64_portblocks.py"
======================================================================
NAT Subscriber Port-Block Report v3
======================================================================

[NAT64] Querying...
  Found 1 subscriber(s)
  Entries: 1

[NAT44] Querying...
  Found 16 subscriber(s)
  Entries: 16

========================================================================================================================
TYPE   SUBSCRIBER                       INSIDE PREFIX          OUTSIDE IP         START   END     PORTS   POLICY     SESS
------------------------------------------------------------------------------------------------------------------------
NAT64  [NAT64-Sub@2001:db8:cccc::]      2001:db8:cccc::/64     199.199.199.199    1024    1223    200     nat64-pol  1/1
NAT44  [LSN-Host@100.80.0.5]            100.80.0.5/32          99.99.99.99        1344    1407    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.6]            100.80.0.6/32          99.99.99.99        1408    1471    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.7]            100.80.0.7/32          99.99.99.99        1472    1535    64      natpol     0/0
NAT44  [LSN-Host@192.168.5.0]           192.168.5.0/32         88.88.88.88        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.1]           192.168.5.1/32         88.88.88.89        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.2]           192.168.5.2/32         88.88.88.90        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.3]           192.168.5.3/32         88.88.88.91        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.4]           192.168.5.4/32         88.88.88.92        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.5]           192.168.5.5/32         88.88.88.93        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.6]           192.168.5.6/32         88.88.88.94        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@192.168.5.7]           192.168.5.7/32         88.88.88.95        0       5119    5120    natvip     0/1
NAT44  [LSN-Host@100.80.0.0]            100.80.0.0/32          99.99.99.99        1024    1087    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.1]            100.80.0.1/32          99.99.99.99        1088    1151    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.2]            100.80.0.2/32          99.99.99.99        1152    1215    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.3]            100.80.0.3/32          99.99.99.99        1216    1279    64      natpol     0/0
NAT44  [LSN-Host@100.80.0.4]            100.80.0.4/32          99.99.99.99        1280    1343    64      natpol     0/0
========================================================================================================================

Summary: 1 NAT64, 8 CGNAT, 8 VIP, 17 total

CSV written to: cf3:\scripts\nat_report.csv

DONE
```

Validate that the `NAT64` row appears with the subscriber internal prefix, the outside IP `199.199.199.199`, and policy `nat64-pol`.

During the real lab validation, these two NAT64 entries were observed:

```text
NAT64  [NAT64-Sub@2001:db8:cccc::]      2001:db8:cccc::/64     199.199.199.199    1224    1423    200     nat64-pol  1/2
NAT64  [NAT64-Sub@2001:db8:200:1::]     2001:db8:200:1::/64    199.199.199.199    1424    1623    200     nat64-pol  2/2
```

This confirms:

- one NAT64 entry for the IPv6-only prefix on `ont1`
- one NAT64 entry for the delegated prefix seen behind `pc1`
- the same outside IP `199.199.199.199`
- `nat64-pol` applied correctly
