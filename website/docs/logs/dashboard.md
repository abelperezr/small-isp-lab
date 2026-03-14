---
sidebar_position: 2
---

# Dashboard e Integración

## Arquitectura usada

La integración de logs del laboratorio reutiliza el stack existente de observabilidad en lugar de introducir una plataforma independiente.

### Razón del diseño

- `Grafana` ya existe en el laboratorio
- `Loki` resuelve almacenamiento y consulta de logs sin agregar una UI nueva
- `Alloy` recibe syslog nativo y permite normalizar etiquetas antes de escribir en Loki

## Lógica de ingesta

Se separó la ingesta por plataforma para evitar ambiguedades entre formatos:

- `SR OS` entra por `10.99.1.16:5514/udp`
- `SR Linux` entra por `10.99.1.16:1514/udp`

Esto permite tratar:

- `SR OS` como flujo `rfc3164`
- `SR Linux` como flujo `rfc5424`

La configuración activa de Alloy vive en el archivo `configs/logs/config.alloy` del repositorio.

## Archivos del módulo

| Archivo | Rol |
|------|-----|
| `configs/logs/config.alloy` | Collector de entrada; recibe syslog, extrae labels y reenvía a Loki |
| `configs/logs/loki-config.yml` | Configuración de almacenamiento, índice, compactor y retención |
| `configs/logs/prepare.sh` | Script opcional si quieres volver a usar persistencia en host para troubleshooting |
| `configs/logs/loki-data/` | Placeholder opcional para persistencia en host; no se usa en el modo por defecto |
| `configs/logs/alloy-data/` | Placeholder opcional para persistencia en host; no se usa en el modo por defecto |

## Modo de almacenamiento usado

Por defecto, el laboratorio usa almacenamiento efímero para `Loki` y `Alloy`.

Esto significa:

- `Loki` escribe dentro del filesystem del contenedor
- `Alloy` guarda su estado dentro del filesystem del contenedor
- al destruir el lab, esos datos desaparecen junto con los contenedores
- el workspace no se llena con logs persistentes ni aparecen problemas de ownership por UID de contenedores

Si en algún momento quieres conservar logs entre recreaciones del lab, puedes volver a montar directorios del host y reutilizar `configs/logs/prepare.sh`.

## `config.alloy` explicado por bloques

### `logging`

```alloy
logging {
  level  = "info"
  format = "logfmt"
}
```

Define el nivel y formato de logs internos de Alloy. No afecta el contenido de los logs Nokia en Loki; solo ayuda a operar el propio collector.

### `loki.relabel "syslog"`

Este bloque toma metadatos generados por el listener syslog y los normaliza en labels consultables en Loki:

- `__syslog_message_hostname` -> `hostname`
- `__syslog_message_app_name` -> `app_name`
- `__syslog_message_severity` -> `severity`
- `__syslog_message_facility` -> `facility`
- `__syslog_connection_ip_address` -> `source_ip`

También rellena `message_type` inicialmente con `app_name`, para que siempre exista una dimensión mínima de clasificación incluso cuando no se logra extraer un tipo de evento más específico.

### `loki.process "classify"`

Este bloque hace parsing adicional por plataforma:

- para `SR Linux` usa una expresión regular sobre el payload `rfc5424` para extraer `payload_level`, `payload_severity` y `message_type`
- para `SR OS` usa una expresión regular para capturar identificadores Nokia del estilo `XXXX-YYYY-ZZZ`

Su objetivo no es almacenar el log crudo, sino enriquecerlo para que Grafana pueda agrupar por tipo de evento sin depender de inspección manual línea por línea.

### `loki.source.syslog "nokia"`

Aquí viven los listeners reales:

- `0.0.0.0:5514/udp` para `SR OS`
- `0.0.0.0:1514/udp` para `SR Linux`

Se separan porque los formatos no son iguales:

- `SR OS` se procesa como `rfc3164`
- `SR Linux` se procesa como `rfc5424`

Además, cada listener ya añade labels base como `job`, `collector`, `transport` y `source_platform`.

### `loki.write "local"`

Es la salida final hacia Loki:

```alloy
loki.write "local" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }

  external_labels = {
    lab = "small-isp-lab",
  }
}
```

Todo lo que Alloy recibe y enriquece termina enviándose al endpoint HTTP interno de Loki. El label externo `lab=small-isp-lab` sirve para diferenciar este entorno si en el futuro compartes un Loki centralizado.

## `loki-config.yml` explicado por bloques

### `auth_enabled` y `server`

- `auth_enabled: false` simplifica el lab y evita manejar autenticación extra
- `http_listen_port: 3100` define el puerto HTTP interno del contenedor Loki

### `common`

Define el almacenamiento local:

- `path_prefix: /loki` fija la raíz interna de datos
- `replication_factor: 1` confirma que es un despliegue single-node
- `ring ... inmemory` evita depender de un KV externo

### `schema_config`

Usa:

- `store: tsdb`
- `object_store: filesystem`
- `schema: v13`
- `period: 24h`

Esto significa que Loki rota e indexa la información por períodos diarios usando filesystem local, sin S3 ni backend distribuido.

### `storage_config`

Separa dos áreas:

- `/loki/chunks` para los datos de log
- `/loki/index` y `/loki/index_cache` para índice y caché del `tsdb_shipper`

Si el uso de disco crece, normalmente el mayor impacto aparece en `chunks`.

### `limits_config`

La línea más importante para laboratorio es:

```yaml
retention_period: 1h
```

Eso equivale a `1 hora`. En el modo efímero por defecto, esa retención vive dentro del contenedor `Loki` y desaparece al destruir el lab.

### `compactor`

El compactor:

- consolida datos periódicamente
- aplica la retención
- procesa borrados sobre filesystem

Sin este bloque, la retención configurada no se aplicaría de forma efectiva.

## Retención y consumo de disco

En este lab:

- por defecto, el crecimiento ocurre dentro del contenedor `Loki`, no en el repo
- `Alloy` también usa almacenamiento efímero local al contenedor
- con `retention_period: 1h`, Loki conserva hasta `1 hora` de logs mientras el contenedor exista

Operativamente esto significa:

- para demos cortas, no dejas residuos persistentes en el workspace
- si dejas el lab muchos días generando syslog, el consumo crecerá dentro del almacenamiento Docker del host
- si necesitas un lab más liviano, lo primero a reducir es la retención de Loki, no Alloy
- si reactivas bind mounts persistentes, entonces el crecimiento volverá a verse en `configs/logs/loki-data/`

## Etiquetas normalizadas en Loki

Alloy genera etiquetas que simplifican el filtrado del dashboard:

| Label | Uso |
|------|-----|
| `source_platform` | `sros` o `srlinux` |
| `hostname` | nombre del equipo |
| `app_name` | proceso o aplicación emisora |
| `severity` | severidad syslog |
| `facility` | facility syslog |
| `source_ip` | IP de gestión del origen |
| `message_type` | tipo de evento; en SR Linux cae por defecto a `app_name` |

## Dashboard de Grafana

El dashboard `Nokia Syslog Overview` fue diseñado para no mezclar ambos formatos en la operación diaria.

### Filtros

#### Compartido

- `Transport`

#### SR OS

- `SrosHost`
- `SrosApp`
- `SrosType`

#### SR Linux

- `SrlHost`
- `SrlApp`
- `SrlType`

### Paneles

- `Log Lines`
- `Active Streams`
- `SR OS Errors`
- `SR OS Warnings`
- `SR Linux Errors`
- `SR Linux Warnings`
- `SR OS Lines by Type`
- `SR OS Lines by Host`
- `SR Linux Lines by App`
- `SR Linux Lines by Host`
- `Raw Syslog - SR OS`
- `Raw Syslog - SR Linux`

## Configuración aplicada en SR OS

La referencia del startup-config quedó documentada en:

- [BNG MASTER](../mopt/bng-master.md)
- [BNG SLAVE](../mopt/bng-slave.md)

Fragmento lógico:

```text
/configure log log-id "77" description "Default System Log to Syslog"
/configure log log-id "77" source main true
/configure log log-id "77" destination syslog "1"
/configure log route-preference primary outband
/configure log syslog "1" description "syslog container"
/configure log syslog "1" address 10.99.1.16
/configure log syslog "1" facility local6
/configure log syslog "1" severity info
/configure log syslog "1" port 5514
/configure log syslog "1" hostname use-system-name
```

### Resultado operativo

- `MASTER` y `SLAVE` publican eventos administrativos y de sistema hacia Alloy
- los eventos mantienen el nombre del equipo
- el dashboard puede filtrar por `BNGMASTER`, `BNGSLAVE`, `MASTER`, `SLAVE` y por tipo de evento Nokia

## Configuración aplicada en SR Linux

La referencia del startup-config quedó documentada en:

- [OLT](../mopt/olt.md)
- [Carrier 1](../mopt/carrier1.md)
- [Carrier 2](../mopt/carrier2.md)

Fragmento lógico:

```text
set /system grpc-server eda-mgmt admin-state disable
set /system logging network-instance mgmt
set /system logging remote-server 10.99.1.16 transport udp
set /system logging remote-server 10.99.1.16 remote-port 1514
set /system logging remote-server 10.99.1.16 format RSYSLOG_SyslogProtocol23Format
set /system logging remote-server 10.99.1.16 facility local6 priority match-above informational
```

### Razón del ajuste `eda-mgmt`

Durante la validación real se observó este mensaje repetitivo:

```text
sr_grpc_server ... Unable to retrieve TLS profile 'EDA'
```

La causa fue que `grpc-server eda-mgmt` estaba habilitado pero referenciaba un perfil TLS inexistente en estos nodos. Para evitar ruido innecesario en Loki y Grafana, se dejó `admin-state disable`.

## Consultas útiles

Todos los logs:

```logql
{job="nokia-syslog"}
```

Solo SR OS:

```logql
{job="nokia-syslog", source_platform="sros"}
```

Solo SR Linux:

```logql
{job="nokia-syslog", source_platform="srlinux"}
```

Solo warnings de SR Linux:

```logql
{job="nokia-syslog", source_platform="srlinux", severity="warning"}
```

Solo errores de SR OS:

```logql
{job="nokia-syslog", source_platform="sros", severity="error"}
```

## Validación recomendada

1. Abrir Grafana en `http://localhost:3030`
2. Entrar al dashboard `Nokia Syslog Overview`
3. Confirmar que existan datos en `Raw Syslog - SR OS` y `Raw Syslog - SR Linux`
4. Filtrar por `SrosHost=MASTER` o `SrlHost=olt`
5. Revisar que los paneles de warnings y errores cambien según el filtro

## Troubleshooting rápido

- Si no ves logs SR OS, revisa que los BNG apunten a `10.99.1.16:5514/udp`
- Si no ves logs SR Linux, revisa que `OLT`, `Carrier1` y `Carrier2` apunten a `10.99.1.16:1514/udp`
- Si Loki responde pero Grafana no muestra datos, prueba `{job="nokia-syslog"}` en Explore
- Si el disco crece más de lo esperado, revisa el uso de almacenamiento de Docker; si reactivaste persistencia en host, revisa `configs/logs/loki-data/`
