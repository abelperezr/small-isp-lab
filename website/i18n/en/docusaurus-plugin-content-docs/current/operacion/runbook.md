---
sidebar_position: 1
---

# Daily operations runbook

This runbook condenses the most useful day-to-day commands for the lab. It does not replace the ATP: it summarizes it and links back to the detailed validations when deeper troubleshooting is needed.

## 1. Overall lab health

Quick review of Containerlab and container status:

```bash
sudo clab ins -t lab.yml
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected result:

- relevant nodes in `running`
- published ports visible for Grafana, Prometheus, ONTs, and LEA

Main services:

- Grafana: `http://localhost:3030`
- Prometheus: `http://localhost:9090`
- LEA/LIG: `http://localhost:8092`
- ONT1 Web: `http://localhost:8090`
- ONT2 Web: `http://localhost:8091`

ATP reference:

- [BNG baseline validation](../atp/bng-baseline.md)
- [OLT baseline validation](../atp/olt-baseline.md)
- [Carriers baseline validation](../atp/carriers-baseline.md)

## 2. Quick base network review

### BNG MASTER / SLAVE

```text
show system alarms
show port
show router interface
show srrp
show router 9999 bgp summary
```

Expected:

- no critical alarms
- key ports and interfaces `up`
- SRRP operational
- BGP neighbors established

### OLT

```text
show interface all
show network-instance bd-50 interfaces
macsum bd-50
macsum bd-srrp
```

Expected:

- bridged subinterfaces `up`
- MAC-VRFs active
- MAC learning consistent with traffic

### Carriers

```text
show interface all
show network-instance route-table ipv4-unicast summary
show network-instance route-table ipv6-unicast summary
show network-instance protocols bgp summary
```

Expected:

- upstream interfaces `up`
- IPv4/IPv6 routes present
- BGP `established` with both BNGs

## 3. Check subscriber sessions

On the BNG:

```text
show service active-subscribers
```

On ONT2 PPPoE:

```bash
docker exec ont2 sh -lc 'ip ad show ppp0; echo ---; ip -6 route'
```

On PC1 for delegated prefix:

```bash
docker exec pc1 sh -lc 'ip -6 ad show dev eth1'
```

Expected:

- `ONT-001` and/or `ONT-002` visible depending on the scenario
- `ppp0` operational on `ont2` when PPPoE is active
- delegated IPv6 prefix visible on `pc1`

ATP reference:

- [ESM](../atp/esm.md)
- [ONT tests](../atp/ont.md)

## 4. Clear sessions and force reauthentication

On the BNG:

```text
clear service id "9998" ipoe session all
```

Note:

- after this `clear`, IPoE sessions may take several seconds to rebuild
- it is normal for WAN IPv6, delegated prefix, and IPv4/IPv6 leases to come back with different values than before
- if `ONT-001` does not reappear after convergence, use DHCP/DHCPv6 renew from the ONT or follow the ESM ATP reference

To suspend or re-enable the PPPoE subscriber:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py deactivate "test@test.com"'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py add "test@test.com" \
  --title "ONT2-WAN1" \
  --password "testlab123" \
  --framed-pool "cgnat" \
  --framed-ipv6-pool "IPv6" \
  --delegated-ipv6-pool "IPv6" \
  --subscriber-id "ONT-002" \
  --subscriber-profile "subprofile" \
  --msap-interface "ipv6-only" \
  --sla-profile "100M"'
```

Expected:

- the subscriber disappears and then reappears in `show service active-subscribers`
- `ont2` loses and recovers `ppp0`

ATP reference:

- [ESM](../atp/esm.md)

## 5. Validate SRRP and BGP recovery

Base verification:

```text
show srrp
show router 9999 bgp summary
show router 9999 bgp neighbor 172.16.1.1 detail | match "Export Policy"
show router 9999 bgp neighbor 172.16.2.1 detail | match "Export Policy"
```

Simulate role change:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1'
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c1/1'
```

This case tests the failure of the link between the BNGs. The SRRP role change also happens here because of `policy 1`, even though the SRRP `message-path` still runs over `1/1/c2/1` through the OLT.

Expected:

- SRRP transitions between `master` and `backup`
- BGP export policies change according to role
- state returns to normal after re-enabling the port

ATP reference:

- [SRRP and BGP](../atp/srrp-bgp.md)

## 6. Quick NAT64 validation

From ONT1:

```bash
docker exec ont1 sh -lc 'ping -6 -c 4 -I 2001:db8:cccc::1 64:ff9b::808:808'
```

On the BNG:

```text
tools dump nat sessions
```

Optional:

```text
pyexec "cf3:\scripts\nat64_portblocks.py"
```

Expected:

- successful ping to the NAT64 prefix
- NAT64 sessions visible on the BNG

Note:

- in the current validation, the working NAT64 path on `ont1` used the `wan2` IPv6 source (`2001:db8:cccc::1`)
- as a quick application-level alternative, this also works:

```bash
docker exec ont1 sh -lc 'curl -6 -I --max-time 15 http://example.com'
```

ATP reference:

- [NAT64](../atp/nat64.md)

## 7. Regenerate traffic for observability

Check orchestrator ports:

```bash
bash configs/cbot/scripts/observability-traffic.sh status
```

Generate traffic:

```bash
bash configs/cbot/scripts/observability-traffic.sh all
```

Show report:

```bash
bash configs/cbot/scripts/observability-traffic.sh report
```

Stop servers:

```bash
bash configs/cbot/scripts/observability-traffic.sh stop-servers
```

Expected:

- octet increase for `ONT-001` and `ONT-002`
- visibility in Prometheus and Grafana

ATP reference:

- [Observability](../atp/observability.md)

## 8. Quick LEA validation

Precondition:

- there must already be an active LI capture on the BNG
- the intercepted identity may be `ONT-001` or a rebuilt `MAC|SAP` style `subscriber-id`, depending on AAA state
- the WAN used to generate traffic must match that intercepted identity
- if you need to prepare or validate that part, use [LEA and LI](../atp/lea-validation.md) and [LEA Console](../lea-console/ejecucion.md)

Start the test server:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh start
bash configs/cbot/scripts/dns-iperf-server.sh status
```

Generate traffic from ONT1:

```bash
ONT_USER=user ONT_PASS=test ONT_WAN=wan2 DURATION=12 PARALLEL=1 bash configs/cbot/scripts/ont1-subscriber-traffic.sh upload
```

If the active capture is tied to `wan1`, change this to `ONT_WAN=wan1`.

Query the API:

```bash
curl -s http://10.99.1.12:8080/api/stats | jq
curl -s 'http://10.99.1.12:8080/api/events?limit=20' | jq
```

Stop the server:

```bash
bash configs/cbot/scripts/dns-iperf-server.sh stop
```

Expected:

- events visible in LEA
- counters and flows present in the API

ATP reference:

- [LEA and LI](../atp/lea-validation.md)

## 9. Post-change checklist

After any operational change, validate at least:

```bash
sudo clab ins -t lab.yml
docker ps --format "table {{.Names}}\t{{.Status}}"
```

```text
show srrp
show router 9999 bgp summary
show service active-subscribers
```

```bash
bash configs/cbot/scripts/observability-traffic.sh report
curl -s http://10.99.1.12:8080/api/stats | jq
```

If everything is healthy:

- lab in `running`
- SRRP and BGP healthy
- subscribers visible
- observability active
- LEA responsive
