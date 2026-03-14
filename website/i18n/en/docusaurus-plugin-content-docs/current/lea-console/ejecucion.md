---
sidebar_position: 4
---

# Manual LEA Execution

## Description

This option documents how to manually activate lawful interception from the BNG MD-CLI using the `liadmin` user.

## BNG Access

Access the BNG over SSH with:

- username: `liadmin`
- password: `admin123`

Then enter LI private mode:

```text
[/]
A:liadmin@BNG1# li private
INFO: CLI #2070: Entering private configuration mode
INFO: CLI #2061: Uncommitted changes are discarded on configuration mode exit
```

## Enable logging towards NETCONF

This procedure can also be performed manually from the CLI:

```text
log log-id "1" netconf-stream "li"
log log-id "1" source li true
log log-id "1" destination netconf
```

## Activate interception by subscriber

Example of subscriber-based interception:

```text
li-source "li-dest-1" subscriber "ONT-001" ingress true
li-source "li-dest-1" subscriber "ONT-001" egress true
li-source "li-dest-1" subscriber "ONT-001" intercept-id 1001
li-source "li-dest-1" subscriber "ONT-001" session-id 1
```

## Notes

- `li private` enables private configuration mode for LI changes.
- `li-dest-1` must already exist as a mirror destination.
- The example above intercepts both `ingress` and `egress` traffic for subscriber `ONT-001` when LUDB fallback is not active.
- `intercept-id` and `session-id` must be adjusted according to the required operation.
- If the subscriber was rebuilt by LUDB fallback, `ONT-001` may no longer appear as the active `subscriber-id`. In that case use the exact `subscriber-id` returned by `show service active-subscribers`, for example `00:d0:f6:01:01:01|1/1/c2/1:50.150`.
- If you generate traffic with `configs/cbot/scripts/ont1-subscriber-traffic.sh`, prefer `ONT_WAN=wan2` without fallback and `ONT_WAN=wan1` in the validated LUDB fallback case.
- `configs/cbot/scripts/ont2-subscriber-traffic.sh` can also be used for `ONT-002`; the current LIG parser now decodes PPPoE session traffic carrying IP.
