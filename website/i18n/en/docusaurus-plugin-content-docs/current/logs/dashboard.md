---
sidebar_position: 2
---

# Dashboard and Integration

## Architecture used

The lab log integration reuses the existing observability stack instead of introducing an independent logging platform.

### Design rationale

- `Grafana` is already part of the lab
- `Loki` provides storage and querying without adding a second UI
- `Alloy` receives native syslog and normalizes labels before writing to Loki

## Ingestion logic

Ingestion is split by platform to avoid ambiguity between formats:

- `SR OS` enters through `10.99.1.16:5514/udp`
- `SR Linux` enters through `10.99.1.16:1514/udp`

This allows:

- `SR OS` to be handled as `rfc3164`
- `SR Linux` to be handled as `rfc5424`

The active Alloy configuration lives in the repository file `configs/logs/config.alloy`.

## Module files

| File | Role |
|------|------|
| `configs/logs/config.alloy` | Ingress collector; receives syslog, extracts labels, and forwards to Loki |
| `configs/logs/loki-config.yml` | Storage, index, compactor, and retention configuration |
| `configs/logs/prepare.sh` | Optional helper if you want to re-enable host persistence for troubleshooting |
| `configs/logs/loki-data/` | Optional placeholder for host persistence; unused in the default mode |
| `configs/logs/alloy-data/` | Optional placeholder for host persistence; unused in the default mode |

## Storage mode in use

By default, the lab uses ephemeral storage for `Loki` and `Alloy`.

This means:

- `Loki` writes inside the container filesystem
- `Alloy` keeps its state inside the container filesystem
- when the lab is destroyed, this runtime data disappears with the containers
- the workspace does not accumulate persistent log data and you avoid container UID ownership issues

If you ever want to preserve logs across lab recreations, you can mount host directories again and reuse `configs/logs/prepare.sh`.

## `config.alloy` explained block by block

### `logging`

```alloy
logging {
  level  = "info"
  format = "logfmt"
}
```

This defines Alloy's own internal log level and format. It does not change the Nokia logs stored in Loki; it only helps operate the collector itself.

### `loki.relabel "syslog"`

This block takes metadata emitted by the syslog listener and normalizes it into queryable Loki labels:

- `__syslog_message_hostname` -> `hostname`
- `__syslog_message_app_name` -> `app_name`
- `__syslog_message_severity` -> `severity`
- `__syslog_message_facility` -> `facility`
- `__syslog_connection_ip_address` -> `source_ip`

It also initializes `message_type` from `app_name` so there is always at least a minimal event classification dimension even when a more specific event type cannot be extracted later.

### `loki.process "classify"`

This block performs platform-specific parsing:

- for `SR Linux` it uses a regex over the `rfc5424` payload to extract `payload_level`, `payload_severity`, and `message_type`
- for `SR OS` it uses a regex to capture Nokia event identifiers of the form `XXXX-YYYY-ZZZ`

Its purpose is not to store the raw line, but to enrich it so Grafana can group by event type without manual line-by-line inspection.

### `loki.source.syslog "nokia"`

This is where the actual listeners live:

- `0.0.0.0:5514/udp` for `SR OS`
- `0.0.0.0:1514/udp` for `SR Linux`

They are separated because the formats differ:

- `SR OS` is handled as `rfc3164`
- `SR Linux` is handled as `rfc5424`

Each listener also sets base labels such as `job`, `collector`, `transport`, and `source_platform`.

### `loki.write "local"`

This is the final output to Loki:

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

Everything Alloy receives and enriches is pushed to Loki's internal HTTP endpoint. The external label `lab=small-isp-lab` helps distinguish this environment if you later share a centralized Loki instance.

## `loki-config.yml` explained block by block

### `auth_enabled` and `server`

- `auth_enabled: false` keeps the lab simple and avoids extra authentication handling
- `http_listen_port: 3100` defines Loki's internal HTTP port

### `common`

Defines local storage behavior:

- `path_prefix: /loki` sets the internal data root
- `replication_factor: 1` confirms a single-node deployment
- `ring ... inmemory` avoids requiring an external KV store

### `schema_config`

It uses:

- `store: tsdb`
- `object_store: filesystem`
- `schema: v13`
- `period: 24h`

This means Loki rotates and indexes data daily using the local filesystem, without S3 or a distributed backend.

### `storage_config`

This separates two main areas:

- `/loki/chunks` for log data
- `/loki/index` and `/loki/index_cache` for TSDB shipper index and cache

If disk usage grows, the largest impact is usually under `chunks`.

### `limits_config`

The most important line for a lab is:

```yaml
retention_period: 1h
```

That is `1 hour`. In the default ephemeral mode, this retention lives inside the `Loki` container and disappears when the lab is destroyed.

### `compactor`

The compactor:

- periodically compacts data
- applies retention
- processes deletes on filesystem storage

Without this block, the configured retention would not be enforced effectively.

## Retention and disk usage

In this lab:

- by default, growth happens inside the `Loki` container, not in the repo
- `Alloy` also uses container-local ephemeral storage
- with `retention_period: 1h`, Loki keeps up to `1 hour` of logs while the container exists

Operationally this means:

- for short demos, no persistent residue is left in the workspace
- if you leave the lab running for many days generating syslog, usage will grow inside Docker storage on the host
- if you need a lighter lab, the first thing to reduce is Loki retention, not Alloy
- if you re-enable host bind mounts, growth will again appear under `configs/logs/loki-data/`

## Normalized labels in Loki

Alloy creates labels that simplify dashboard filtering:

| Label | Purpose |
|------|---------|
| `source_platform` | `sros` or `srlinux` |
| `hostname` | node system name |
| `app_name` | emitting process or application |
| `severity` | syslog severity |
| `facility` | syslog facility |
| `source_ip` | sender management IP |
| `message_type` | event type; in SR Linux it falls back to `app_name` |

## Grafana dashboard

The `Nokia Syslog Overview` dashboard was designed so daily operations do not mix both log formats unnecessarily.

### Filters

#### Shared

- `Transport`

#### SR OS

- `SrosHost`
- `SrosApp`
- `SrosType`

#### SR Linux

- `SrlHost`
- `SrlApp`
- `SrlType`

### Panels

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

## Configuration applied on SR OS

The startup-config reference is documented in:

- [BNG MASTER](../mopt/bng-master.md)
- [BNG SLAVE](../mopt/bng-slave.md)

Logical fragment:

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

### Operational result

- `MASTER` and `SLAVE` export administrative and system events to Alloy
- events keep the node system name
- the dashboard can filter by `BNGMASTER`, `BNGSLAVE`, `MASTER`, `SLAVE`, and Nokia event type

## Configuration applied on SR Linux

The startup-config reference is documented in:

- [OLT](../mopt/olt.md)
- [Carrier 1](../mopt/carrier1.md)
- [Carrier 2](../mopt/carrier2.md)

Logical fragment:

```text
set /system grpc-server eda-mgmt admin-state disable
set /system logging network-instance mgmt
set /system logging remote-server 10.99.1.16 transport udp
set /system logging remote-server 10.99.1.16 remote-port 1514
set /system logging remote-server 10.99.1.16 format RSYSLOG_SyslogProtocol23Format
set /system logging remote-server 10.99.1.16 facility local6 priority match-above informational
```

### Reason for the `eda-mgmt` adjustment

During live validation, this repetitive message was observed:

```text
sr_grpc_server ... Unable to retrieve TLS profile 'EDA'
```

The cause was that `grpc-server eda-mgmt` was enabled while referencing a TLS profile that does not exist on these nodes. To reduce unnecessary noise in Loki and Grafana, it was set to `admin-state disable`.

## Useful queries

All logs:

```logql
{job="nokia-syslog"}
```

Only SR OS:

```logql
{job="nokia-syslog", source_platform="sros"}
```

Only SR Linux:

```logql
{job="nokia-syslog", source_platform="srlinux"}
```

Only SR Linux warnings:

```logql
{job="nokia-syslog", source_platform="srlinux", severity="warning"}
```

Only SR OS errors:

```logql
{job="nokia-syslog", source_platform="sros", severity="error"}
```

## Recommended validation

1. Open Grafana at `http://localhost:3030`
2. Open the `Nokia Syslog Overview` dashboard
3. Confirm data exists in `Raw Syslog - SR OS` and `Raw Syslog - SR Linux`
4. Filter with `SrosHost=MASTER` or `SrlHost=olt`
5. Verify that warning and error panels change with the selected filters

## Quick troubleshooting

- If you do not see SR OS logs, verify that the BNGs point to `10.99.1.16:5514/udp`
- If you do not see SR Linux logs, verify that `OLT`, `Carrier1`, and `Carrier2` point to `10.99.1.16:1514/udp`
- If Loki is up but Grafana shows no data, try `{job="nokia-syslog"}` in Explore
- If disk usage grows more than expected, inspect Docker storage usage; if you re-enabled host persistence, inspect `configs/logs/loki-data/`
