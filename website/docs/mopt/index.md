---
sidebar_position: 1
---

# MOPT de Dispositivos

## Método de Operación y Procedimientos Técnicos

Esta sección documenta las configuraciones detalladas de cada dispositivo en el laboratorio. Cada MOPT está organizado por secciones numeradas para facilitar la navegación y referencia.

## Dispositivos en la Topología

<div className="cardGrid">
  <div className="docCard">
    <h3>BNG MASTER - Nokia 7750 SR-7</h3>
    <p>BNG primario con SRRP priority 200, EHS, NAT64, CGNAT, LI <a href="./bng-master/">Ver configuración</a></p>
  </div>
  <div className="docCard">
    <h3>BNG SLAVE - Nokia 7750 SR-7</h3>
    <p>BNG secundario con SRRP priority 50, configuración espejo <a href="./bng-slave/">Ver configuración</a></p>
  </div>
  <div className="docCard">
    <h3>OLT - Nokia SR Linux</h3>
    <p>Terminal de línea óptica con MAC-VRF para bridging multi-servicio <a href="./olt/">Ver configuración</a></p>
  </div>
  <div className="docCard">
    <h3>Carrier 1 - Nokia SR Linux</h3>
    <p>Router upstream AS 65501, LP 300 (primario) <a href="./carrier1/">Ver configuración</a></p>
  </div>
  <div className="docCard">
    <h3>Carrier 2 - Nokia SR Linux</h3>
    <p>Router upstream AS 65502, LP 150 (secundario) <a href="./carrier2/">Ver configuración</a></p>
  </div>
  <div className="docCard">
    <h3>Internet Gateway</h3>
    <p>Simulador de Internet con NAT masquerade <a href="./internet/">Ver configuración</a></p>
  </div>
  <div className="docCard">
    <h3>ONT1 (IPoE)</h3>
    <p>Terminal con 3 WANs: IPv6-only, Dual-Stack, VIP <a href="./ont1/">Ver configuración</a></p>
  </div>
  <div className="docCard">
    <h3>ONT2 (PPPoE)</h3>
    <p>Terminal PPPoE con IPv6-only <a href="./ont2/">Ver configuración</a></p>
  </div>
  <div className="docCard">
    <h3>DNS64</h3>
    <p>Servidor BIND9 para síntesis NAT64 <a href="./dns64/">Ver configuración</a></p>
  </div>
  <div className="docCard">
    <h3>LIG</h3>
    <p>Lawful Interception Gateway con LEA Console <a href="./lig/">Ver configuración</a></p>
  </div>
</div>
