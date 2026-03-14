---
sidebar_position: 3
---

# Integration with lab.yml

## LIG Node Configuration

The LIG node at `lab.yml` is configured to:

1. Run in a `network-multitool` container
2. Mount LIG files as read-only volumes
3. Configure IP interfaces towards both BNGs (VPRN 9999)
4. Enable IP forwarding and disable rp_filter
5. Configure NAT masquerade for outgoing traffic
6. Launch Python script in background

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
    # Configure IP toward BNG MASTER (VPRN 9999)
    - bash -c "ip addr add 172.19.1.1/30 dev eth1"
    - bash -c "ip -6 addr add 2001:db8:ffff::1/126 dev eth1"
    # Configure IP toward BNG SLAVE (VPRN 9999)
    - bash -c "ip addr add 172.20.1.1/30 dev eth2"
    # Launch LIG
    - bash -c "mkdir -p /app && cp /config/lig.py /app/ && cp /config/index.html /app/"
    - bash -c "nohup python3 /app/lig.py > /var/log/lig.log 2>&1 &"
```

## Mapped Port

| Internal Port | External Port | Service |
|----------------|----------------|----------|
| 8080 | 8092 | Web Dashboard + REST API |
| 22 | 56619 | SSH |

The UDP listener (port 11111) does not need external mapping since it only receives traffic from the BNGs within the laboratory network.
