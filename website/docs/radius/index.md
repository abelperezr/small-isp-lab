---
sidebar_position: 1
---

# Servidor RADIUS

## Descripción

El laboratorio utiliza **FreeRADIUS custom** como servidor de autenticación y accounting para los suscriptores ESM.

## Información

| Parámetro | Valor |
|-----------|-------|
| IP de Gestión | 10.99.1.8 |
| Imagen por defecto | ghcr.io/abelperezr/freeradius-custom:0.1 |
| Secret | testlab123 |
| Puerto Auth | 1812 |
| Puerto Acct | 1813 |
| SSH | 56617 |

## Opciones de despliegue

### Opción 1 (default): usar imagen de GitHub Container Registry

```bash
docker pull ghcr.io/abelperezr/freeradius-custom:0.1
```

`lab.yml` ya está configurado para usar esta imagen en el nodo `radius`.

### Opción 2: construir imagen local

Directorio de build:

- `small-isp-lab/radius-custom`

Comandos:

```bash
cd small-isp-lab/radius-custom
./build.sh
```

Luego puedes cambiar temporalmente la imagen en `lab.yml` por tu tag local.

## Archivos reales usados por el nodo `radius`

### En `lab.yml` (bind-mount)

| Archivo | Destino en contenedor | Función |
|---------|------------------------|---------|
| `configs/radius/clients.tmpl.conf` | `/etc/freeradius/clients.conf` | Clientes RADIUS (BNGs) |
| `configs/radius/authorize` | `/etc/freeradius/mods-config/files/authorize` | Base de usuarios y atributos |

### En `radius-custom/` (imagen)

| Archivo | Función |
|---------|---------|
| `radius-custom/Dockerfile` | Construcción de imagen FreeRADIUS custom |
| `radius-custom/entrypoint.sh` | Arranque del servicio en contenedor |
| `radius-custom/build.sh` | Build rápido de imagen local |
