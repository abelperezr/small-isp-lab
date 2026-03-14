---
sidebar_position: 2
---

# Instalación

## Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/abelperezr/small-isp-lab.git
cd small-isp-lab
```

## Paso 2: Verificar Imágenes

```bash
docker images | grep -E "srsim|srlinux|ont-ds|containerbot|multitool|prometheus|grafana|gnmic"
```

## Paso 3: Colocar Licencia

La licencia de Nokia SRSIM debe ser obtenida con un representante de Nokia. El repositorio no incluye ni distribuye este archivo.

```bash
cp /path/to/SR_SIM_license.txt configs/license/SR_SIM_license.txt
```

## Paso 4: Construir Containerbot (si aplica)

```bash
cd /path/to/containerbot
./build
cd /path/to/small-isp-lab
```

## Paso 5: Desplegar

```bash
sudo containerlab deploy -t lab.yml
```

## Paso 6: Verificar

```bash
sudo containerlab inspect -t lab.yml
```

## Paso 7: Acceder a Servicios

```bash
# Grafana
firefox http://localhost:3030

# LEA Console
firefox http://localhost:8092

# ONT1 Web GUI
firefox http://localhost:8090

# SSH a BNG MASTER
ssh -p 56612 admin@localhost
```

## Destruir el Laboratorio

```bash
sudo containerlab destroy -t lab.yml
```
