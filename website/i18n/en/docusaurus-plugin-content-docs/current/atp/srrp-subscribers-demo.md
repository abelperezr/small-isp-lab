---
sidebar_position: 13
sidebar_label: 13. SRRP Subscriber Failover
---

# 13. SRRP Subscriber Failover

This test demonstrates service continuity for IPoE and PPPoE subscribers while cutting the access link between the OLT and the BNG MASTER. The goal is to verify that:

- `SLAVE` takes the `master` role for the three subscriber SRRP group interfaces
- sessions remain visible on both BNGs, with `Fwd` active on the forwarding node
- `ont1`, `ont2`, and the LAN behind `ont1` continue to pass traffic during the switchover

## 13.1 Prerequisites

Validate before starting:

```text
show srrp
show service active-subscribers
```

Expected baseline:

- `MASTER`: SRRP `master` for `ipv6-only`, `dual-stack`, and `vip`
- `SLAVE`: SRRP `backupShunt`
- `ONT-001` and `ONT-002` visible in `show service active-subscribers`

## 13.2 Determine the current source IPs

Optional shortcut:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo start
```

If you use this helper, you can skip `13.2` and `13.3` and continue directly with `13.4`. The script detects the current source IPs and launches all ATP probes.

To view the ping sequence during the test, leave a second terminal open with:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo watch
```

This mode refreshes the latest line from each ping probe live and helps you see the traffic gap exactly when the failover happens.

Before starting the pings, identify the current lab addresses. These IPs may vary between runs, so fixed values should not be used.

Run from the host:

```bash
docker exec ont1 sh -lc "ip -6 addr show dev eth1.150 scope global"
docker exec ont1 sh -lc "ip -6 addr show dev eth3.200 scope global"
docker exec ont1 sh -lc "ip -4 addr show dev eth3.200 scope global"
docker exec ont2 sh -lc "ip -6 addr show dev ppp0 scope global"
```

Use these IPs in the next steps:

- `ONT1_WAN1_V6`: global IPv6 on `eth1.150`
- `ONT1_WAN2_V6`: global IPv6 on `eth3.200`
- `ONT1_WAN2_V4`: global IPv4 on `eth3.200`
- `ONT2_PPP_V6`: global IPv6 on `ppp0`

Example from a real run:

```text
ONT1_WAN1_V6=2001:db8:100::5
ONT1_WAN2_V6=2001:db8:cccc::1
ONT1_WAN2_V4=100.80.0.4
ONT2_PPP_V6=2001:db8:100::4
```

## 13.3 Start continuous pings

Launch the probes from the host with `docker exec`:

```bash
docker exec ont1 sh -lc 'rm -f /tmp/srrp_demo_*; nohup ping -D -n -i 0.2 -W 1 -I <ONT1_WAN1_V6> 2001:db8:aaaa::2 > /tmp/srrp_demo_ont1_wan1_v6.log 2>&1 & echo $! > /tmp/srrp_demo_ont1_wan1_v6.pid'
docker exec ont1 sh -lc 'nohup ping -D -n -i 0.2 -W 1 -I <ONT1_WAN2_V6> 2001:db8:aaaa::2 > /tmp/srrp_demo_ont1_wan2_v6.log 2>&1 & echo $! > /tmp/srrp_demo_ont1_wan2_v6.pid'
docker exec ont1 sh -lc 'nohup ping -D -n -i 0.2 -W 1 -I <ONT1_WAN2_V4> 99.99.99.99 > /tmp/srrp_demo_ont1_wan2_v4.log 2>&1 & echo $! > /tmp/srrp_demo_ont1_wan2_v4.pid'
docker exec ont2 sh -lc 'rm -f /tmp/srrp_demo_*; nohup ping -D -n -i 0.2 -W 1 -I <ONT2_PPP_V6> 2001:db8:aaaa::2 > /tmp/srrp_demo_ont2_ppp_v6.log 2>&1 & echo $! > /tmp/srrp_demo_ont2_ppp_v6.pid'
docker exec pc1 sh -lc 'rm -f /tmp/srrp_demo_pc1_lan_v6.*; nohup ping -D -n -i 0.2 -W 1 2001:db8:aaaa::2 > /tmp/srrp_demo_pc1_lan_v6.log 2>&1 & echo $! > /tmp/srrp_demo_pc1_lan_v6.pid'
```

Replace `<ONT1_WAN1_V6>`, `<ONT1_WAN2_V6>`, `<ONT1_WAN2_V4>`, and `<ONT2_PPP_V6>` with the values discovered in `13.2`.

These five probes cover:

- `ONT1 WAN1 IPv6-only`
- `ONT1 WAN2 dual-stack IPv6`
- `ONT1 WAN2 dual-stack IPv4`
- `ONT2 WAN1 PPPoE IPv6`
- `PC1` behind the PD delivered by `ONT1`

## 13.4 Capture baseline state

On the BNG MASTER:

```text
show srrp
show service active-subscribers
```

On the BNG SLAVE:

```text
show srrp
show service active-subscribers
```

Observed output before the failure:

```text
A:admin@MASTER# show srrp
2  9998  dual-stack  Up  master
1  9998  ipv6-only   Up  master
3  9998  vip         Up  master
```

```text
A:admin@SLAVE# show srrp
2  9998  dual-stack  Up  backupShunt
1  9998  ipv6-only   Up  backupShunt
3  9998  vip         Up  backupShunt
```

## 13.5 Trigger the OLT -> BNG MASTER failure

Run the script from `containerbot`:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c2/1'
```

Expected result:

```text
OK: port 1/1/c2/1 admin-state=disable on 10.99.1.2
```

## 13.6 Validate the switchover

On `MASTER`:

```text
show srrp
show port 1/1/c2/1 detail
show service active-subscribers
```

On `SLAVE`:

```text
show srrp
show service active-subscribers
```

Observed result:

```text
A:admin@MASTER# show srrp
2  9998  dual-stack  Up  initialize
1  9998  ipv6-only   Up  initialize
3  9998  vip         Up  initialize
```

```text
A:admin@SLAVE# show srrp
2  9998  dual-stack  Up  master
1  9998  ipv6-only   Up  master
3  9998  vip         Up  master
```

```text
A:admin@MASTER# show service active-subscribers
...
00:d0:f6:01:01:01  IPoE   DHCP6        9998  N
00:d0:f6:01:01:02  IPoE   DHCP         9998  N
00:d0:f6:01:01:04  PPP 1  DHCP6        9998  N
```

```text
A:admin@SLAVE# show service active-subscribers
...
00:d0:f6:01:01:01  IPoE   DHCP6        9998  Y
00:d0:f6:01:01:02  IPoE   DHCP         9998  Y
00:d0:f6:01:01:04  PPP 1  DHCP6        9998  Y
```

## 13.7 Validate traffic continuity

Inspect the ping queues:

```bash
docker exec ont1 sh -lc 'tail -n 12 /tmp/srrp_demo_ont1_wan1_v6.log'
docker exec ont1 sh -lc 'tail -n 12 /tmp/srrp_demo_ont1_wan2_v6.log'
docker exec ont1 sh -lc 'tail -n 12 /tmp/srrp_demo_ont1_wan2_v4.log'
docker exec ont2 sh -lc 'tail -n 12 /tmp/srrp_demo_ont2_ppp_v6.log'
docker exec pc1 sh -lc 'tail -n 12 /tmp/srrp_demo_pc1_lan_v6.log'
```

Observed signals in this run:

- service continuity was preserved, but the switchover was not hitless
- `ONT1 WAN1` showed a sequence gap between the last `ttl=62` at `icmp_seq=109` and the first `ttl=63` at `icmp_seq=144`
- `ONT2 PPPoE` showed a sequence gap between the last `ttl=62` at `icmp_seq=113` and the first `ttl=63` at `icmp_seq=154`
- `ONT1 WAN1` and `ONT2 PPPoE` changed from `ttl=62` to `ttl=63`, indicating the new forwarding path through `SLAVE`
- `ONT1 WAN2 IPv4` kept answering toward `99.99.99.99`
- `PC1` kept reaching `2001:db8:aaaa::2`, validating PD/LAN continuity

Real example from `ONT1 WAN1` during switchover:

```text
[1773352987.998830] 64 bytes from 2001:db8:aaaa::2: icmp_seq=109 ttl=62 time=2.22 ms
...
[1773352997.495945] 64 bytes from 2001:db8:aaaa::2: icmp_seq=144 ttl=63 time=2082 ms
```

Real example from `ONT2 PPPoE` during switchover:

```text
[1773352988.116137] 64 bytes from 2001:db8:aaaa::2: icmp_seq=113 ttl=62 time=1.32 ms
...
[1773352996.824532] 64 bytes from 2001:db8:aaaa::2: icmp_seq=154 ttl=63 time=1.03 ms
```

In this test, the observed convergence window for subscriber traffic was approximately `8 to 10 seconds`.

## 13.8 Restore the MASTER port

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c2/1'
```

Validate the return to nominal state:

```text
show srrp
show service active-subscribers
```

Expected result:

- `MASTER` returns to `master`
- `SLAVE` returns to `backupShunt`
- sessions remain active
- the IPv6 pings from `ont1` and `ont2` return to `ttl=62`

## 13.9 Clean up the ping processes

Use only one of these two options:

- if you started the probes with the optional helper, stop them with the helper
- if you started the probes manually with `docker exec`, stop them manually with the `kill` commands

There is no need to run both options. If you use the helper first and then run the manual `kill` commands, you may see `No such process` because the probes were already stopped.

Option 1, helper:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo stop
```

Option 2, manual commands:

```bash
docker exec ont1 sh -lc 'kill -INT $(cat /tmp/srrp_demo_ont1_wan1_v6.pid) $(cat /tmp/srrp_demo_ont1_wan2_v6.pid) $(cat /tmp/srrp_demo_ont1_wan2_v4.pid)'
docker exec ont2 sh -lc 'kill -INT $(cat /tmp/srrp_demo_ont2_ppp_v6.pid)'
docker exec pc1 sh -lc 'kill -INT $(cat /tmp/srrp_demo_pc1_lan_v6.pid)'
```
