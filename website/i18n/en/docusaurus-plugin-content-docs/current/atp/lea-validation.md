---
sidebar_position: 11
sidebar_label: 11. LEA and LI
---

# 11. Lawful Interception and LEA validation

This test validates that the BNG sends intercepted traffic to the LIG/LEA and that both the web UI and the APIs reflect the flows for subscriber `ONT-001`.

## 11.0 Select the scenario before starting

Before enabling LI, confirm which scenario you are in:

| Scenario | How the subscriber appears on the BNG | Primary WAN for ATP 11 | Script |
| --- | --- | --- | --- |
| Normal RADIUS | `ONT-001` | `wan2` | `ont1-subscriber-traffic.sh` |
| LUDB fallback | usually `<MAC>\|<SAP>` | `wan1` | `ont1-subscriber-traffic.sh` |
| PPPoE alternative | `ONT-002` / `test@test.com` | `ppp0` | `ont2-subscriber-traffic.sh` |

Recommended pre-check:

```text
A:admin@MASTER# show service active-subscribers
```

Expected result:

- without AAA fallback to LUDB, `ONT-001` should appear under its normal alias and the simplest ATP 11 path is `wan2`
- with LUDB fallback, use the exact active `subscriber-id` returned by the BNG and keep the whole run on that same WAN

All traffic scripts referenced in this section are located under `configs/cbot/scripts/`.

Practical rule for `li-source`:

- before LUDB fallback, the identifier that works consistently is the subscriber alias, for example `subscriber "ONT-001"`
- after LUDB fallback, that alias may stop resolving and the correct identifier becomes the exact active `subscriber-id` returned by the BNG, for example `00:d0:f6:01:01:01|1/1/c2/1:50.150`
- there is no single `subscriber` value that is universal across both states
- if you need a reusable workflow, first discover the real active identifier and then build `li-source` with that value

Important `iperf3` note:

- `ont1-subscriber-traffic.sh` and `ont2-subscriber-traffic.sh` now set `IPERF_MSS=1400` by default
- this avoids the lab case where the TCP session negotiated a jumbo `MSS` close to `9440`, sent an initial burst, and then stalled with no sustained traffic
- if you override `IPERF_MSS`, keep a conservative value or validate yourself that the path can carry large TCP segments reliably

## 11.1 Start the TCP test server

Start `iperf3` on the `dns` node:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh start
```

Verify that it is listening on `2001:db8:aaaa::2:5201`:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh status
```

Expected result:

- `status` must show a `LISTEN` line for `2001:db8:aaaa::2:5201`
- if `status` does not show the listener, do not continue with `upload` or `download`

## 11.2 Enable interception on the BNG

From the `liadmin` user on the active BNG:

- without LUDB fallback, the simplest validated flow is to use `subscriber "ONT-001"`
- if LUDB fallback has already been applied, `ONT-001` stops appearing as an alias on the BNG; in that case use the exact active `subscriber-id` returned by `show service active-subscribers`
- `ONT-002` can also be used as a PPPoE alternative, but the main ATP path remains `ONT-001` because it is the clearest IPoE validation

```text
A:liadmin@MASTER# li private
[pr:/li]
A:liadmin@MASTER# li-source "li-dest-1" subscriber "ONT-001" ingress true
A:liadmin@MASTER# li-source "li-dest-1" subscriber "ONT-001" egress true
A:liadmin@MASTER# li-source "li-dest-1" subscriber "ONT-001" intercept-id 1001
A:liadmin@MASTER# li-source "li-dest-1" subscriber "ONT-001" session-id 1
A:liadmin@MASTER# log log-id "1" netconf-stream "li"
A:liadmin@MASTER# log log-id "1" source li true
A:liadmin@MASTER# log { log-id "1" destination netconf }
A:liadmin@MASTER# commit
```

Note:

- the LIG in this lab consumes the BNG UDP mirror (`ip-udp-shim`)
- `netconf-stream "li"` is still operationally useful, but the LEA panel shown in this lab is fed by the UDP listener on port `11111`
- if the ATP is executed while AAA is in LUDB fallback, the `subscriber-id` may stop being `ONT-001` and show up as `<MAC>|<SAP>` in `show service active-subscribers`
- in that scenario, the most precise way to enable LI is to use the rebuilt `subscriber-id` returned by the BNG; using `SAP` can mix traffic from other sessions if they share the same circuit
- the capture scope depends on how `li-source` is defined: by subscriber alias, by exact `subscriber-id`, or by the real active session context
- for ATP, using the exact identity returned by the BNG for that run is the safest way to avoid mixing traffic from other sessions

Example using the exact active subscriber in LUDB fallback:

```text
A:liadmin@MASTER# li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" ingress true
A:liadmin@MASTER# li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" egress true
A:liadmin@MASTER# li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" intercept-id 2004
A:liadmin@MASTER# li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" session-id 1
A:liadmin@MASTER# commit
```

Exact configuration used in the validated tests for this run:

```text
[pr:/li]
A:liadmin@MASTER# info flat
    li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" ingress true
    li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" egress true
    li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" intercept-id 2101
    li-source "li-dest-1" subscriber "00:d0:f6:01:01:01|1/1/c2/1:50.150" session-id 1
    log log-id "1" netconf-stream "li"
    log log-id "1" source li true
    log { log-id "1" destination netconf }
```

Operational reading of that configuration:

- the capture was tied to the exact `subscriber-id` for `wan1`
- that is why the correct API queries in this validation use `intercept-id 2101`
- that is also why the functional traffic tests were aligned with `ONT_WAN=wan1`
- that same syntax is not the recommended one while AAA is still in its normal state; in that case you should normally intercept `subscriber "ONT-001"`

Important:

- `configs/cbot/scripts/ont1-subscriber-traffic.sh` accepts `ONT_WAN=wan1|wan2|wan3` and automatically resolves the active IPv6 on that WAN
- without AAA fallback to LUDB, the simplest validated option is `ONT_WAN=wan2`, because it matches the normal dual-stack path for `ONT-001`
- `wan1` can also be used without fallback if you intercepted `ONT-001` and want to validate that specific WAN; it is not the primary ATP path because `wan2` is a more representative normal dual-stack case
- if you are coming from LUDB fallback, use the WAN that matches the rebuilt `subscriber-id` you selected
- in the current lab validation, the correct case for `ONT-001` under LUDB fallback is `ONT_WAN=wan1`
- do not mix `wan1` and `wan2` in the same ATP 11 run; if you intercepted `00:d0:f6:01:01:01|1/1/c2/1:50.150`, all traffic tests must use `wan1`
- run `upload`, `download`, and `dns64` sequentially, not in parallel
- use `PARALLEL=1` for ATP; higher values make the test more fragile and add no functional value for LEA
- the scripts already clamp `IPERF_MSS=1400` by default to avoid the initial burst with no sustained TCP traffic
- `configs/cbot/scripts/ont2-subscriber-traffic.sh` is also ready if you want an alternative `ONT-002` PPPoE validation

Quick check:

Without fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan2 bash configs/cbot/scripts/ont1-subscriber-traffic.sh show-bind
```

Alternative without fallback on `wan1`:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh show-bind
```

With LUDB fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh show-bind
```

Expected result:

- without fallback:
  - `ONT_WAN=wan2`
  - `INTERFACE=eth3.200`
  - `ONT_BIND_V6=<active ONT-001 WAN IPv6 on wan2>`
- valid alternative without fallback:
  - `ONT_WAN=wan1`
  - `INTERFACE=eth1.150`
  - `ONT_BIND_V6=<active ONT-001 WAN IPv6 on wan1>`
- with fallback:
  - `ONT_WAN=wan1`
  - `INTERFACE=eth1.150`
  - `ONT_BIND_V6=<active ONT-001 WAN IPv6 on wan1>`

## 11.3 Generate TCP traffic from ONT1

Case without LUDB fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan2 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh upload
```

Alternative without fallback on `wan1`:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh upload
```

Case with LUDB fallback using the rebuilt `ONT-001` subscriber:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh upload
```

Do not run this command in parallel with `download` or `dns64`.

If you need another session, change `ONT_WAN` or provide `ONT_BIND_V6` explicitly. The important point is that traffic must exit through the same session you intercepted on the BNG.

Internally it runs:

```bash
iperf3 -6 -c 2001:db8:aaaa::2 -B <active-IPv6-on-the-selected-WAN> -p 5201 -t 12 -P 1 -M 1400
```

In LEA you should see events such as:

- `PROTO = TCP`
- `IP ORIGIN = active IPv6 on the selected WAN`
- `IP DESTINATION = 2001:db8:aaaa::2`
- `P.ORIG` with high ephemeral ports
- `P.DEST = 5201`

Operational note:

- after the `MSS` fix, `iperf3` should show sustained traffic instead of only an initial burst
- exact throughput is not an ATP KPI; the important point is that the TCP session stays up and LEA records both `INGRESS` and `EGRESS` events
- if you again see `256 KBytes` in the first second and then `0.00 bits/sec`, verify that you did not override `IPERF_MSS`

Visual reference of the expected LEA result:

![Expected LEA view with decoded TCP events](/img/LEA.png)

## 11.4 Generate reverse traffic

Without fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan2 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh download
```

Alternative without fallback on `wan1`:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh download
```

With fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh download
```

Expected result:

- the command must not end with `Connection refused`
- the command must not end with `control socket has closed unexpectedly`
- LEA must show TCP flows from `2001:db8:aaaa::2:5201` towards the selected WAN IPv6 classified as `EGRESS`

## 11.5 Generate DNS64/UDP traffic

Without fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan2 DURATION=10 bash configs/cbot/scripts/ont1-subscriber-traffic.sh dns64
```

Alternative without fallback on `wan1`:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=10 bash configs/cbot/scripts/ont1-subscriber-traffic.sh dns64
```

With fallback:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan1 DURATION=10 bash configs/cbot/scripts/ont1-subscriber-traffic.sh dns64
```

In LEA this is usually visible as:

- `PROTO = UDP`
- `IP DESTINATION = 2001:db8:aaaa::2`
- `P.DEST = 53`

Visual reference of the expected LEA result for DNS64/UDP:

![Expected LEA view with DNS64/UDP events](/img/LEA2.png)

## 11.6 Stop and inspect the test server

Stop `iperf3`:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh stop
```

Inspect the server logs:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh logs
```

## 11.7 Query the LEA APIs

General summary:

```bash
curl -s http://10.99.1.12:8080/api/stats | jq
```

Latest events:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=20' | jq
```

Events for a specific interception:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=100&intercept_id=<INTERCEPT_ID_USED_IN_LI>' | jq
```

Interception summary:

```bash
curl -s http://10.99.1.12:8080/api/intercepts | jq
```

## 11.8 Useful event queries

Top observed protocols:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USED_IN_LI>' \
| jq -r 'group_by(.proto)[] | "\(.[0].proto): \(length)"'
```

Top source IPs:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USED_IN_LI>' \
| jq -r 'group_by(.src_ip)[] | "\(.[0].src_ip): \(length)"'
```

Top destination IPs:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USED_IN_LI>' \
| jq -r 'group_by(.dst_ip)[] | "\(.[0].dst_ip): \(length)"'
```

Top destination ports:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USED_IN_LI>' \
| jq -r 'map(select(.dst_port != null)) | group_by(.dst_port)[] | "\(.[0].dst_port): \(length)"'
```

Traffic split by `INGRESS` and `EGRESS`:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USED_IN_LI>' \
| jq -r 'group_by(.direction)[] | "\(.[0].direction): \(length)"'
```

Unique flows `src_ip:src_port -> dst_ip:dst_port`:

```bash
curl -s 'http://10.99.1.12:8080/api/events?limit=500&intercept_id=<INTERCEPT_ID_USED_IN_LI>' \
| jq -r '.[] | "\(.proto) \(.src_ip):\(.src_port) -> \(.dst_ip):\(.dst_port)"' \
| sort | uniq -c
```

## 11.9 Operational notes

- If the APIs return zero counters or empty lists, there is usually no intercepted traffic active at that moment.
- If `li-source` is configured on the wrong BNG, the LIG will not receive packets even though the panel itself is operational.
- If `ONT-001` disappears because of LUDB fallback, do not automatically replace it with `ONT-002`. First inspect `show service active-subscribers` and use the exact active `subscriber-id` for `ONT-001`.
- Without AAA fallback to LUDB, the main ATP 11 run for `ONT-001` uses `wan2`.
- `wan1` is also valid without fallback if you want to observe that specific session.
- Under LUDB fallback, the validated ATP 11 run for `ONT-001` uses `wan1`.
- The correct WAN must always match the identity intercepted in `li-source`.
- If you intercept by exact `subscriber-id`, query the API with that real `intercept-id` and generate traffic on that same session.
- If AAA is still normal, do not assume a `<MAC>|<SAP>` style `subscriber-id` will work for LI; in that state use the subscriber alias exposed by the BNG, for example `ONT-001`.
- If you want a generic method, the right approach is not to hardcode one string but to resolve the currently active subscriber identity first and use that identity in the capture.
- If you test `wan3` or mix `wan1` and `wan2` in the same run, that is a different validation and must not be mixed with the main ATP path.
- `ONT-002` can also be validated now because the LIG parser decodes PPPoE session traffic with IPv6/IPv4.
- For the clearest LEA validation, combine one TCP test (`iperf3`) and one UDP test (`dns64`) to quickly distinguish protocols in the UI.
- If `iperf3` falls back into an initial burst followed by `0.00 bits/sec`, the most likely reason is that an overly large `MSS` is being used on that lab path. Retry with the default `IPERF_MSS=1400`.
