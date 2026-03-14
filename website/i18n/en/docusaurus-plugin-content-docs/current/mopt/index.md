---
sidebar_position: 1
---

# Device MOPT

## Method of Operation and Technical Procedures

This section documents the detailed configurations of each device in the lab. Each MOPT is organized by numbered sections for easy navigation and reference.

## Devices in the Topology

<div className="cardGrid">
  <div className="docCard">
    <h3>BNG MASTER - Nokia 7750 SR-7</h3>
    <p>Primary BNG with SRRP priority 200, EHS, NAT64, CGNAT, LI <a href="./bng-master/">View settings</a></p>
  </div>
  <div className="docCard">
    <h3>BNG SLAVE - Nokia 7750 SR-7</h3>
    <p>Secondary BNG with SRRP priority 50, mirror configuration <a href="./bng-slave/">View settings</a></p>
  </div>
  <div className="docCard">
    <h3>OLT - Nokia SR Linux</h3>
    <p>Optical line terminal with MAC-VRF for multi-service bridging <a href="./olt/">View settings</a></p>
  </div>
  <div className="docCard">
    <h3>Carrier 1 - Nokia SR Linux</h3>
    <p>AS 65501 upstream router, LP 300 (primary) <a href="./carrier1/">View configuration</a></p>
  </div>
  <div className="docCard">
    <h3>Carrier 2 - Nokia SR Linux</h3>
    <p>AS 65502 upstream router, LP 150 (secondary) <a href="./carrier2/">View configuration</a></p>
  </div>
  <div className="docCard">
    <h3>Internet Gateway</h3>
    <p>Internet simulator with NAT masquerade <a href="./internet/">View settings</a></p>
  </div>
  <div className="docCard">
    <h3>ONT1 ​​(IPoE)</h3>
    <p>Terminal with 3 WANs: IPv6-only, Dual-Stack, VIP <a href="./ont1/">View configuration</a></p>
  </div>
  <div className="docCard">
    <h3>ONT2 (PPPoE)</h3>
    <p>PPPoE terminal with IPv6-only <a href="./ont2/">View configuration</a></p>
  </div>
  <div className="docCard">
    <h3>DNS64</h3>
    <p>BIND9 server for NAT64 synthesis <a href="./dns64/">View configuration</a></p>
  </div>
  <div className="docCard">
    <h3>LIG</h3>
    <p>Lawful Interception Gateway with LEA Console <a href="./lig/">View settings</a></p>
  </div>
</div>
