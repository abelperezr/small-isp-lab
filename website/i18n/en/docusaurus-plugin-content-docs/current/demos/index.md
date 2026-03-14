---
sidebar_position: 1
---

# Featured demos

This section groups the most compelling demonstrations in the lab for short 5 to 10 minute sessions. Each demo links to the related ATP, where the full step-by-step procedure is documented.

## 1. Final Boss

**What it shows:** subscriber service survival under a compound failure: OLT access loss toward the BNG MASTER, upstream loss on the active BNG, and a RADIUS outage.

**Estimated duration:** 10-15 minutes

**Detailed procedure:** [Final Boss](../atp/final-boss.md)

## 2. SRRP Subscriber Failover

**What it shows:** continuity for ONTs and Prefix Delegation downstream hosts during SRRP switchover between BNG MASTER and BNG SLAVE.

**Estimated duration:** 5-10 minutes

**Detailed procedure:** [SRRP Subscriber Failover](../atp/srrp-subscribers-demo.md)

## 3. SRRP failover + dynamic BGP export change through EHS

**What it shows:** switchover between BNG MASTER and BNG SLAVE, EHS reaction, and BGP policy/announcement changes.

**Estimated duration:** 5-10 minutes

**Detailed procedure:** [SRRP and BGP - General Tests](../atp/srrp-bgp.md)

## 4. RADIUS outage with LUDB fallback

**What it shows:** subscriber service continuity even when RADIUS is unavailable.

**Estimated duration:** 5-10 minutes

**Detailed procedure:** [ESM - Subscriber Tests](../atp/esm.md#74-fallback-to-ludb)

## 5. End-to-end NAT64 from an IPv6-only ONT

**What it shows:** IPv6-to-IPv4 translation from an IPv6-only subscriber towards IPv4 resources.

**Estimated duration:** 5 minutes

**Detailed procedure:** [NAT64 - Tests](../atp/nat64.md)

## 6. LEA interception with API and web visibility

**What it shows:** lawful interception activation, traffic generation, and event visibility from both the web console and the LIG API.

**Estimated duration:** 5-10 minutes

**Detailed procedure:** [Lawful Interception and LEA Validation](../atp/lea-validation.md)

## 7. Grafana observability with real subscriber traffic

**What it shows:** simultaneous traffic generation from ONT1 and ONT2 and correlation in Prometheus and Grafana.

**Estimated duration:** 5 minutes

**Detailed procedure:** [Observability Validation in Grafana and Prometheus](../atp/observability.md)

## Suggested order

If you want an executive or technical demo of the lab, this is a good sequence:

1. SRRP + BGP
2. Final Boss
3. SRRP Subscriber Failover
4. RADIUS fallback
5. NAT64
6. LEA
7. Observability
