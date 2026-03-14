---
sidebar_position: 1
---

# RADIUS server

## Description

The lab uses a **custom FreeRADIUS** image as the authentication and accounting server for ESM subscribers.

## Information

| Parameter | Value |
|-----------|-------|
| Management IP | 10.99.1.8 |
| Default image | ghcr.io/abelperezr/freeradius-custom:0.1 |
| Secret | testlab123 |
| Auth Port | 1812 |
| Acct Port | 1813 |
| SSH | 56617 |

## Deployment options

### Option 1 (default): pull from GitHub Container Registry

```bash
docker pull ghcr.io/abelperezr/freeradius-custom:0.1
```

`lab.yml` is already configured to use this image for the `radius` node.

### Option 2: build locally

Build directory:

- `small-isp-lab/radius-custom`

Commands:

```bash
cd small-isp-lab/radius-custom
./build.sh
```

Then you can temporarily switch the image in `lab.yml` to your local tag.

## Actual files used by the `radius` node

### In `lab.yml` (bind mounts)

| File | Container destination | Purpose |
|------|------------------------|---------|
| `configs/radius/clients.tmpl.conf` | `/etc/freeradius/clients.conf` | RADIUS clients (BNGs) |
| `configs/radius/authorize` | `/etc/freeradius/mods-config/files/authorize` | User and attribute database |

### In `radius-custom/` (image build)

| File | Purpose |
|------|---------|
| `radius-custom/Dockerfile` | Custom FreeRADIUS image build |
| `radius-custom/entrypoint.sh` | Container startup logic |
| `radius-custom/build.sh` | Quick local image build |
