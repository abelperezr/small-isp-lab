---
sidebar_position: 1
---

# LEA Console - Lawful Interception Gateway

## Description

The **LEA Console** (Law Enforcement Agency Console) is a system composed of a Python script (`lig.py`) and a web interface (`index.html`) that acts as a legal interception gateway. It receives intercepted traffic from Nokia BNGs using the **ip-udp-shim** format and presents it in a web dashboard in real time.

## Components

| Component | Function |
|------------|---------|
| `lig.py` | UDP Listener + Nokia LI Shim Parser + REST API |
| `index.html` | Web dashboard with statistics and events table |

## Access

- **Dashboard Web**: `http://localhost:8092`
- **REST API**: `http://localhost:8092/api/events`
- **SSH**: `ssh -p 56619 root@localhost`

## General Operation

1. The BNG sends intercepted traffic as UDP to port 11111 of the LIG
2. The `lig.py` script listens on UDP 0.0.0.0:11111
3. Each packet is parsed by extracting the Nokia LI Shim header
4. Events are stored in memory (maximum 2000 events)
5. The REST API exposes events and statistics
6. The web dashboard queries the API and displays data in real time

## Configuration in the BNG

### Mirror Destination

```text
/configure mirror mirror-dest "li-dest-1" admin-state enable
/configure mirror mirror-dest "li-dest-1" service-id 111111
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap header-type ip-udp-shim
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap direction-bit true
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap router-instance "9999"
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap gateway ip-address source 172.19.1.2
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap gateway ip-address destination 172.19.1.1
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap gateway udp-port source 11111
/configure mirror mirror-dest "li-dest-1" encap layer-3-encap gateway udp-port destination 11111
```

### Activate Interception (from user liadmin)

```text
# Por suscriptor
li-source "li-dest-1" subscriber "ONT-001" ingress true
li-source "li-dest-1" subscriber "ONT-001" egress true
li-source "li-dest-1" subscriber "ONT-001" intercept-id 1001
li-source "li-dest-1" subscriber "ONT-001" session-id 1

# By SAP
li-source "li-dest-1" sap 1/1/c2/1:50.150 ingress true
li-source "li-dest-1" sap 1/1/c2/1:50.150 egress true
li-source "li-dest-1" sap 1/1/c2/1:50.150 intercept-id 2001
li-source "li-dest-1" sap 1/1/c2/1:50.150 session-id 1
```
