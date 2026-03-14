---
sidebar_position: 2
---

# LIG Script Architecture

## Code Structure

The `lig.py` script is made up of the following modules:

### 1. Nokia LI Shim Parser

The Nokia ip-udp-shim format has the following structure:

| Bytes | Field | Description |
|-------|-------|-------------|
| 0-1 | Flags | Bit 15 = address (0=ingress, 1=egress) |
| 23 | Intercept-ID | Interception identifier (uint16) |
| 4-5 | Padding | 0x0000 |
| 6-7 | Session-ID | Session identifier (uint16) |
| 8+ | Ethernet Frame | Frame Ethernet with QinQ + IP inner |

The parser navigates the layers:

1. **Nokia Shim** (8 bytes): Extract flags, intercept-id, session-id, address
2. **Ethernet Header**: MAC dst/src + 802.1Q tags (outer/inner VLAN)
3. **IP Header**: Detect IPv4 or IPv6, extract src/dst IP, protocol, ports

### 2. UDP Listener

```python
def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 11111))
    while True:
        data, addr = sock.recvfrom(65535)
        parsed = parse_shim(data)
        # Almacenar en deque y actualizar estadísticas
```

### 3. REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | HTML Dashboard |
| `/api/events` | GET | Event list (params: limit, intercept_id) |
| `/api/stats` | GET | Global statistics |
| `/api/intercepts` | GET | List of active intercept-ids |
| `/api/clear` | GET | Clear all data |

### 4. Memory Storage

- `events`: `deque(maxlen=2000)` - Last 2000 events parsed
- `stats`: Dictionary with global counters (total, ingress, egress, ipv4, ipv6)
- `stats["intercepts"]`: Dictionary by intercept_id with packets, bytes, first/last_seen
- Thread-safe with `threading.Lock()`

## Design Decisions

:::info[Why these decisions]

- **No external dependencies**: Just use Python stdlib to work on any Linux container without installing packages
- **Deque with maxlen**: Limit memory usage to 2000 events, discarding the oldest ones automatically
- **Threading**: One thread for the UDP listener and another for the HTTP server, both daemons for automatic cleaning
- **Generic 802.1Q Parser**: Navigate up to 3 chained VLAN tags, supporting both QinQ and single-tag
:::
