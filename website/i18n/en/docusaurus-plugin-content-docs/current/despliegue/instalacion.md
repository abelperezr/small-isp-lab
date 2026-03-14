---
sidebar_position: 2
---

# Installation

## Step 1: Clone the Repository

```bash
git clone https://github.com/abelperezr/small-isp-lab.git
cd small-isp-lab
```

## Step 2: Check Images

```bash
docker images | grep -E "srsim|srlinux|ont-ds|containerbot|multitool|prometheus|grafana|gnmic"
```

## Step 3: Place License

The Nokia SRSIM license must be obtained from a Nokia representative. This repository does not include or distribute that file.

```bash
cp /path/to/SR_SIM_license.txt configs/license/SR_SIM_license.txt
```

## Step 4: Build Containerbot (if applicable)

```bash
cd /path/to/containerbot
./build
cd /path/to/small-isp-lab
```

## Step 5: Deploy

```bash
sudo containerlab deploy -t lab.yml
```

## Step 6: Verify

```bash
sudo containerlab inspect -t lab.yml
```

## Step 7: Access Services

```bash
# Grafana
firefox http://localhost:3030

# LEA Console
firefox http://localhost:8092

# ONT1 Web GUI
firefox http://localhost:8090

# SSH to BNG MASTER
ssh -p 56612 admin@localhost
```

## Destroy the Laboratory

```bash
sudo containerlab destroy -t lab.yml
```
