---
sidebar_position: 2
---

# Arquitectura del Script LIG

## Estructura del Código

El script `lig.py` se compone de los siguientes módulos:

### 1. Parser Nokia LI Shim

El formato ip-udp-shim de Nokia tiene la siguiente estructura:

| Bytes | Campo | Descripción |
|-------|-------|-------------|
| 0-1 | Flags | Bit 15 = dirección (0=ingress, 1=egress) |
| 2-3 | Intercept-ID | Identificador de interceptación (uint16) |
| 4-5 | Padding | 0x0000 |
| 6-7 | Session-ID | Identificador de sesión (uint16) |
| 8+ | Ethernet Frame | Frame Ethernet con QinQ + IP inner |

El parser navega las capas:

1. **Nokia Shim** (8 bytes): Extrae flags, intercept-id, session-id, dirección
2. **Ethernet Header**: MAC dst/src + tags 802.1Q (outer/inner VLAN)
3. **IP Header**: Detecta IPv4 o IPv6, extrae src/dst IP, protocolo, puertos

### 2. Listener UDP

```python
def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 11111))
    while True:
        data, addr = sock.recvfrom(65535)
        parsed = parse_shim(data)
        # Almacenar en deque y actualizar estadísticas
```

### 3. API REST

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Dashboard HTML |
| `/api/events` | GET | Lista de eventos (params: limit, intercept_id) |
| `/api/stats` | GET | Estadísticas globales |
| `/api/intercepts` | GET | Lista de intercept-ids activos |
| `/api/clear` | GET | Limpiar todos los datos |

### 4. Almacenamiento en Memoria

- `events`: `deque(maxlen=2000)` - Últimos 2000 eventos parseados
- `stats`: Diccionario con contadores globales (total, ingress, egress, ipv4, ipv6)
- `stats["intercepts"]`: Diccionario por intercept_id con packets, bytes, first/last_seen
- Thread-safe con `threading.Lock()`

## Decisiones de Diseño

:::info[Por qué estas decisiones]

- **Sin dependencias externas**: Solo usa stdlib de Python para que funcione en cualquier contenedor Linux sin instalar paquetes
- **Deque con maxlen**: Limita el uso de memoria a 2000 eventos, descartando los más antiguos automáticamente
- **Threading**: Un thread para el listener UDP y otro para el servidor HTTP, ambos daemon para limpieza automática
- **Parser genérico de 802.1Q**: Navega hasta 3 tags VLAN encadenados, soportando tanto QinQ como single-tag
:::
