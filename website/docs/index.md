---
sidebar_position: 1
---

# Small ISP con Containerlab

<div className="cardGrid">
  <div className="docCard">
    <h3>Small ISP - Redundancia SRRP</h3>
    <p>Laboratorio de ISP con redundancia SRRP entre BNG MASTER y SLAVE, con BGP Traffic Engineering dinámico vía EHS</p>
  </div>
  <div className="docCard">
    <h3>Nokia SROS + SR Linux</h3>
    <p>Integración de Nokia 7750 SR-7 (BNG), SR Linux (OLT, Carriers) y contenedores Linux en un único lab</p>
  </div>
  <div className="docCard">
    <h3>Stack de Telemetría</h3>
    <p>Monitoreo y logs con gNMIC, Prometheus, Grafana, Alloy y Loki</p>
  </div>
  <div className="docCard">
    <h3>Autenticación RADIUS + LUDB Fallback</h3>
    <p>Autenticación de suscriptores con FreeRADIUS y fallback a Local User Database</p>
  </div>
  <div className="docCard">
    <h3>NAT64 + CGNAT + One-to-One</h3>
    <p>Tres perfiles de NAT: NAT64 para IPv6-only, CGNAT determinístico para dual-stack, y One-to-One para VIP</p>
  </div>
  <div className="docCard">
    <h3>Lawful Interception + LEA Console</h3>
    <p>Interceptación legal con mirror destination ip-udp-shim y consola web para visualización en tiempo real</p>
  </div>
</div>

## Descripción General

Este laboratorio implementa un **Small ISP** completo utilizando **Containerlab** como plataforma de virtualización. La arquitectura incluye redundancia activo/respaldo entre dos BNG Nokia 7750 SR-7 con SRRP (Subscriber Routed Redundancy Protocol) y BGP Traffic Engineering dinámico controlado por EHS (Event Handling System).

### Componentes Principales

| Componente | Modelo/Imagen | IP Gestión | Función |
|------------|---------------|------------|---------|
| **BNG MASTER** | Nokia 7750 SR-7 (SRSIM) | 10.99.1.2 | BNG primario con SRRP priority 200 |
| **BNG SLAVE** | Nokia 7750 SR-7 (SRSIM) | 10.99.1.3 | BNG secundario con SRRP priority 50 |
| **OLT** | Nokia SR Linux 25.10 | 10.99.1.4 | Terminal de línea óptica (MAC-VRF) |
| **Carrier 1** | Nokia SR Linux 25.10 | 10.99.1.252 | Router carrier upstream (AS 65501) |
| **Carrier 2** | Nokia SR Linux 25.10 | 10.99.1.253 | Router carrier upstream (AS 65502) |
| **ONT1** | ont-ds:0.3 o superior (IPoE) | 10.99.1.5 | Terminal óptica - 3 WANs (IPv6, Dual, VIP) |
| **ONT2** | ont-ds:0.3 o superior (PPPoE) | 10.99.1.6 | Terminal óptica - 1 WAN PPPoE IPv6 |
| **RADIUS** | FreeRADIUS | 10.99.1.8 | Servidor de autenticación |
| **gNMIC** | OpenConfig gNMIC | 10.99.1.9 | Colector de telemetría |
| **Prometheus** | Prometheus | 10.99.1.10 | Base de datos de métricas |
| **Grafana** | Grafana 10.3.5 | 10.99.1.11 | Visualización de métricas |
| **LIG** | network-multitool + Python | 10.99.1.12 | Lawful Interception Gateway |
| **DNS64** | BIND9 | 10.99.1.13 | Servidor DNS64 para NAT64 |
| **Internet** | network-multitool | 10.99.1.14 | Simulador de Internet |
| **Loki** | grafana/loki:latest | 10.99.1.15 | Almacenamiento e índice de logs |
| **Alloy** | grafana/alloy:latest | 10.99.1.16 | Colector syslog y normalización de labels |
| **Containerbot** | ghcr.io/abelperezr/containerbot:0.0.1 | 10.99.1.200 | Bot de automatización Telegram |

### Características Técnicas

:::info[Tecnologías Implementadas]

- **SRRP (Subscriber Routed Redundancy Protocol)**: Redundancia activo/backup entre BNGs
- **EHS (Event Handling System)**: Scripts pySROS para ajuste dinámico de políticas BGP según estado SRRP
- **BGP Traffic Engineering**: AS-Path Prepend diferenciado por carrier y rol SRRP
- **Multi-Chassis Redundancy**: Sincronización de sesiones DHCP/SRRP/ESM entre BNGs
- **ESM (Enhanced Subscriber Management)**: Tres Group Interfaces: ipv6-only, dual-stack, vip
- **NAT64**: Traducción IPv6→IPv4 con prefijo 64:ff9b::/96
- **CGNAT Determinístico**: NAT44 con mapeo determinístico 100.80.0.0/29 → 99.99.99.99
- **NAT One-to-One**: IP pública dedicada 88.88.88.88/29 para suscriptores VIP
- **Lawful Interception**: Mirror destination con ip-udp-shim hacia LEA Console
- **IPoE + PPPoE**: Soporte completo para ambos protocolos
- **Dual-Stack IPv4/IPv6**: DHCPv4, DHCPv6 WAN y Prefix Delegation
- **DNS64**: Resolución DNS con síntesis de registros AAAA para NAT64
- **Logs centralizados**: pipeline syslog con Alloy + Loki integrado en Grafana
- **Containerbot**: Bot Telegram para ejecutar scripts de prueba y monitoreo

:::

### Demos destacadas

Estas son las pruebas más vistosas del laboratorio para una demo rápida. Todas tienen procedimiento detallado dentro del ATP y también están agrupadas en [Demos destacadas](./demos/).

- **Final Boss**: [Final Boss](./atp/final-boss.md)
- **Failover Suscriptores SRRP**: [Failover Suscriptores SRRP](./atp/srrp-subscribers-demo.md)
- **Failover SRRP + BGP por EHS**: [SRRP y BGP - Pruebas Generales](./atp/srrp-bgp.md)
- **RADIUS down + fallback LUDB**: [ESM - Pruebas de Suscriptores](./atp/esm.md#74-fallback-a-la-ludb)
- **NAT64 end-to-end desde ONT IPv6-only**: [NAT64 - Pruebas](./atp/nat64.md)
- **LEA con visibilidad en API y web**: [Interceptación legal y validación en LEA](./atp/lea-validation.md)
- **Observabilidad con tráfico real**: [Validación de observabilidad en Grafana y Prometheus](./atp/observability.md)

### Acceso al Laboratorio

| Servicio | URL/Puerto | Credenciales |
|----------|------------|--------------|
| Grafana | `http://localhost:3030` | admin/admin |
| Prometheus | `http://localhost:9090` | N/A |
| Loki API | `http://localhost:3101` | N/A |
| Alloy UI | `http://localhost:12345` | N/A |
| LEA/LIG | `http://localhost:8092` | admin/multit00l |
| ONT1 Web GUI | `http://localhost:8090` | N/A |
| ONT2 Web GUI | `http://localhost:8091` | N/A |
| ONT1 | `docker exec -it ont1 bash` | user/test |
| ONT2 | `docker exec -it ont2 bash` | user/test |
| BNG MASTER SSH | `ssh -p 56612 admin@localhost` | admin/lab123 |
| BNG SLAVE SSH | `ssh -p 56613 admin@localhost` | admin/lab123 |
| OLT SSH | `ssh -p 56614 admin@localhost` | admin/lab123 |
| Carrier 1 SSH | `ssh -p 56610 admin@localhost` | admin/lab123 |
| Carrier 2 SSH | `ssh -p 56611 admin@localhost` | admin/lab123 |
| Radius | `ssh -p 56617 admin@localhost` | admin/admin |
| PC1 | `docker exec -it pc1 bash` | admin/multit00l |
| Internet | `ssh -p 56620 admin@localhost` | admin/multit00l |
| DNS | `ssh -p 56621 admin@localhost` | admin/multit00l |
| GNMIC | `docker exec -it gnmic /bin/sh` | N/A |


## Inicio Rápido

```bash
# Clonar el repositorio
git clone https://github.com/abelperezr/small-isp-lab.git
cd small-isp-lab

# Desplegar el laboratorio
sudo containerlab deploy -t lab.yml

# Verificar estado de los nodos
sudo containerlab inspect -t lab.yml

# Acceder a Grafana
firefox http://localhost:3030

# Acceder a LEA Console
firefox http://localhost:8092
```

:::warning[Requisitos Previos]

- Docker instalado y funcionando
- Containerlab v0.50+ instalado
- Imagen Nokia SRSIM 25.10.R2 disponible
- Imagen Nokia SR Linux 25.10 disponible
- Imagen ONT-DS 0.3 o superior disponible
- Imagen Containerbot 0.0.1 disponible
- Al menos 24 GB de RAM
- Recomendado: 32 GB para ejecutar el lab con más margen
- Licencia Nokia válida para SRSIM
:::
