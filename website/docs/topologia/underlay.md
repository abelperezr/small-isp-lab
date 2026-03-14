---
sidebar_position: 2
---

# Underlay Network

## Diagrama de Conectividad Física

![Topología Underlay](/img/underlay.png)

## Descripción de la Capa Física

El **Underlay** representa la conectividad IP/MPLS entre los BNG MASTER y SLAVE, las conexiones L3 hacia los Carriers, y las conexiones L2 hacia la OLT y servicios auxiliares.

## Direccionamiento IP del Underlay

### Inter-BNG (IS-IS / LDP / iBGP)

| Segmento | Red | BNG MASTER | BNG SLAVE |
|----------|-----|------------|-----------|
| Inter-BNG | 172.99.1.0/31 | .0 | .1 |
| Loopback | /32 | 10.0.0.1 | 10.0.0.2 |
| Redundant IF | 192.168.12.0/31 | .0 | .1 |

### BNG a Carrier 1 (172.16.1.x/31)

| Segmento | Red | BNG | Carrier 1 |
|----------|-----|-----|-----------|
| MASTER → C1 | 172.16.1.0/31 | .0 | .1 |
| SLAVE → C1 | 172.16.1.2/31 | .2 | .3 |

### BNG a Carrier 2 (172.16.2.x/31)

| Segmento | Red | BNG | Carrier 2 |
|----------|-----|-----|-----------|
| MASTER → C2 | 172.16.2.0/31 | .0 | .1 |
| SLAVE → C2 | 172.16.2.2/31 | .2 | .3 |

### BNG a LIG

| Segmento | Red | BNG | LIG |
|----------|-----|-----|-----|
| MASTER → LIG | 172.19.1.0/30 | .2 | .1 |
| SLAVE → LIG | 172.20.1.0/30 | .2 | .1 |

## Protocolos de Routing

### IS-IS (Inter-BNG)

El enlace entre BNG MASTER y SLAVE corre IS-IS Level 2 como protocolo de routing para el underlay MPLS:

```text
/configure router "Base" isis 0 admin-state enable
/configure router "Base" isis 0 level-capability 2
/configure router "Base" isis 0 area-address [49.0001]
/configure router "Base" isis 0 interface "system" admin-state enable
/configure router "Base" isis 0 interface "to_SLAVE" admin-state enable
/configure router "Base" isis 0 interface "to_SLAVE" interface-type point-to-point
```

### LDP (MPLS Label Distribution)

LDP se usa para establecer LSPs entre los BNGs, necesarios para el SDP de la redundant-interface y el transporte VPN-IPv4/v6:

```text
/configure router "Base" ldp interface-parameters interface "to_SLAVE" admin-state enable
/configure router "Base" ldp targeted-session peer 10.0.0.2 admin-state enable
```

### iBGP (VPN-IPv4/v6)

iBGP entre loopbacks transporta las rutas VPN-IPv4 y VPN-IPv6 de las VPRNs 9998 y 9999:

```text
/configure router "Base" bgp group "iBGP" admin-state enable
/configure router "Base" bgp group "iBGP" type internal
/configure router "Base" bgp group "iBGP" local-address 10.0.0.1
/configure router "Base" bgp group "iBGP" family vpn-ipv4 true
/configure router "Base" bgp group "iBGP" family vpn-ipv6 true
/configure router "Base" bgp group "iBGP" local-as as-number 65510
```

## Configuración de Puertos BNG

| Puerto | Encapsulación | Destino | Función |
|--------|---------------|---------|---------|
| 1/1/c1/1 | dot1q | BNG Peer | IS-IS/LDP/iBGP |
| 1/1/c2/1 | qinq | OLT | Acceso suscriptores + SRRP |
| 1/1/c3/1 | dot1q | LIG | Lawful Interception |
| 1/1/c4/1 | hybrid | DNS64 | DNS64 para NAT64 |
| 1/1/c5/1 | dot1q | Carrier 1 | eBGP upstream |
| 1/1/c6/1 | dot1q | Carrier 2 | eBGP upstream |
