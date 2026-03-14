---
sidebar_position: 2.2
sidebar_label: 3. OLT baseline validation
---

# 3. OLT Baseline Validation

## Objective

Validate that the SR Linux OLT has its bridged subinterfaces up, correctly associated to MAC-VRF instances, and learning MAC addresses as expected.

## Scope

- Interface and subinterface operational state.
- Subinterface-to-MAC-VRF association (`bd-50`, `bd-51`, `bd-52`, `bd-srrp`).
- MAC table learning status per instance.

## 3.1 Interface validation

Commands:

- `show interface all`
- `show network-instance bd-50 interfaces`

Example:

```text
A:admin@olt# show interface all
ethernet-1/1.50 is up  -> bd-50
ethernet-1/1.51 is up  -> bd-51
ethernet-1/1.52 is up  -> bd-52
ethernet-1/1.4094 is up -> bd-srrp
...
ethernet-1/6.150 is up -> bd-50
```

Expected result:

- Uplinks to BNGs (`ethernet-1/1`, `ethernet-1/2`) are `up`.
- Access subinterfaces (`ethernet-1/3.150`, `ethernet-1/4.200`, `ethernet-1/5.300`, `ethernet-1/6.150`) are `up`.
- Each subinterface is mapped to the correct MAC-VRF.

## 3.2 MAC-VRF and MAC-table validation

Commands:

- `macsum bd-50`
- `macsum bd-srrp`
- `show network-instance bd-50 summary`

Operational note:

- If validation is done long after deployment, MAC entries may have aged out.
- In that case, generate traffic (for example `ping` from ONTs to BNGs) and run `macsum` again.

Example:

```text
A:admin@olt# macsum bd-50
Total Learnt Macs : 2 Total 2 Active

A:admin@olt# macsum bd-srrp
Total Learnt Macs : 3 Total 3 Active
```

Expected result:

- Active MAC learning is visible in `bd-50`, `bd-51`, `bd-52`, and `bd-srrp` according to current traffic.
- MAC-VRF instances are in `up` state.

## 3.3 Final checklist

- Critical interfaces and subinterfaces are `up`.
- MAC-VRF associations are correct.
- MAC learning is consistent with active services and current lab state.
