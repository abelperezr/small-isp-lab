---
sidebar_position: 3
---

# Integración con lab.yml

## Configuración del Nodo LIG

El nodo LIG en el `lab.yml` está configurado para:

1. Ejecutar en un contenedor `network-multitool`
2. Montar los archivos del LIG como volúmenes read-only
3. Configurar interfaces IP hacia ambos BNGs (VPRN 9999)
4. Habilitar IP forwarding y desactivar rp_filter
5. Configurar NAT masquerade para tráfico saliente
6. Lanzar el script Python en background

```yaml
lig:
  kind: linux
  mgmt-ipv4: 10.99.1.12
  image: ghcr.io/srl-labs/network-multitool
  ports:
    - 56619:22
    - 8092:8080          # Dashboard web
  binds:
    - configs/lig/lig.py:/config/lig.py:ro
    - configs/lig/index.html:/config/index.html:ro
  exec:
    # Configurar IP hacia BNG MASTER (VPRN 9999)
    - bash -c "ip addr add 172.19.1.1/30 dev eth1"
    - bash -c "ip -6 addr add 2001:db8:ffff::1/126 dev eth1"
    # Configurar IP hacia BNG SLAVE (VPRN 9999)
    - bash -c "ip addr add 172.20.1.1/30 dev eth2"
    # Lanzar LIG
    - bash -c "mkdir -p /app && cp /config/lig.py /app/ && cp /config/index.html /app/"
    - bash -c "nohup python3 /app/lig.py > /var/log/lig.log 2>&1 &"
```

## Puerto Mapeado

| Puerto Interno | Puerto Externo | Servicio |
|----------------|----------------|----------|
| 8080 | 8092 | Dashboard Web + API REST |
| 22 | 56619 | SSH |

El listener UDP (puerto 11111) no necesita mapeo externo ya que solo recibe tráfico desde los BNGs dentro de la red del laboratorio.
