---
sidebar_position: 2
---

# Containerbot Operation

## Goal

This guide is for operators and developers who want to use, extend, or maintain Containerbot inside this lab.

The goal is not only to explain how the bot is built, but also to provide a practical bridge into the ATP workflows.

## Before going into the ATPs

First validate that the minimum operational environment is healthy:

```bash
docker ps -a --format '{{.Names}}\t{{.Status}}' | rg '^(containerbot|radius|ont1|ont2|pc1)\b'
docker exec containerbot sh -lc 'ls -1 /app/scripts && echo __SEP__ && ls -1 /app/ansible/playbooks'
docker logs --tail 20 containerbot
```

Expected:

- `containerbot` is `Up`
- `radius` is `Up` if you are going to use `manage_authorize.py`
- scripts are visible under `/app/scripts`
- playbooks are visible under `/app/ansible/playbooks`
- bot logs show no startup errors

Operational note:

- the bot file watcher does auto-reload when mounted scripts or playbooks change
- if `radius` is down, `manage_authorize.py` will not be able to list or modify the remote `authorize` file over SSH

## Two ways to operate

### 1. From Telegram

Use the bot menu or `/run ...` directly in the bot chat.

Examples:

```text
/run olt-to-bng1-down.sh
/run carrier1-to-bng2-down.sh
/run update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1
/run manage_authorize.py list
```

Important:

- `/run ...` is a Telegram bot command
- it is not a generic host shell command

### 2. From the host terminal

Use `docker exec containerbot ...` to run the exact same scripts inside the container, without going through Telegram.

Examples:

```bash
docker exec containerbot sh -lc '/app/scripts/olt-to-bng1-down.sh'
docker exec containerbot sh -lc '/app/scripts/carrier1-to-bng2-down.sh'
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py list'
```

Recommendation:

- if you are following an ATP, prefer the host terminal for exact reproducibility
- use Telegram when you want guided operation and menu confirmations
- for operational Python scripts such as `manage_authorize.py` and `update-ports-sros.py`, the recommended option is to run them with `docker exec` against `containerbot`

## Quick path into the ATPs

Most useful scripts and which ATPs they lead into:

- `update-ports-sros.py`
  - ATP 6: SRRP and BGP
  - ATP 13: SRRP Subscriber Failover
  - useful for shutting or enabling SR OS ports over gNMI
- `olt-to-bng1-down.sh` and `olt-to-bng1-up.sh`
  - ATP 14: Final Boss
  - simulate the `OLT -> BNG MASTER` access failure
- `carrier1-to-bng1-down.sh` and `carrier1-to-bng1-up.sh`
  - ATP 6: SRRP and BGP
  - simulate `Carrier1` failure toward `BNG MASTER`
- `carrier1-to-bng2-down.sh` and `carrier1-to-bng2-up.sh`
  - ATP 14: Final Boss
  - simulate `Carrier1` failure toward `BNG SLAVE`
- `manage_authorize.py`
  - ATP 7: ESM
  - list, deactivate, add, edit, and disconnect FreeRADIUS subscribers
- `subscriber-failover-probes.sh`
  - ATP 13: `srrp-demo`
  - ATP 14: `final-boss`
  - detect current source IPs, launch probes, show logs, and clean up processes

Validated shortcuts:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo start
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo tail
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo stop

bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss start
bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss tail
bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss stop
```

For ATP 6 and ATP 7, prefer these forms:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1'
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c1/1'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py list'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py show \"test@test.com\"'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py deactivate \"test@test.com\"'
```

## Real project structure

Image source code:

- `small-isp-lab/containerbot/`
  - `bot.py`
  - `config.yaml`
  - `entrypoint.sh`
  - `Dockerfile`
  - `requirements.txt`

Runtime configuration mounted by the lab:

- `small-isp-lab/configs/cbot/`
  - `scripts/`
  - `ansible/`
  - `config.yaml`
  - `secrets.env` (local, not versioned)
  - `secrets.env.example` (versioned template)

## Runtime flow

1. `entrypoint.sh` loads `secrets.env`.
2. It starts `sshd` for container management access.
3. It waits for management network reachability (`MGMT_PROBE_IP`).
4. It launches `python3 /app/bot.py`.
5. The bot auto-discovers scripts/playbooks and builds Telegram menus.
6. A file watcher auto-reloads config when files change.

## What the bot auto-discovers

- Scripts in `SCRIPTS_DIR` with `.sh` and `.py` extensions.
- Playbooks in `ANSIBLE_DIR/playbooks` with `.yml`/`.yaml`.
- If there is no override in `config.yaml`, metadata is derived from filename/path.

## `bot.py` guide for humans (safe to modify)

Source file: `small-isp-lab/containerbot/bot.py`.

### 1. Main code blocks

- **Global variables and constants**:
  - `SCRIPTS_DIR`, `ANSIBLE_DIR`, `CONFIG_FILE`
  - internal fallbacks used if `config.yaml` does not define `bot.default_timeout` or `bot.max_message_length`
- **RBAC**:
  - `_parse_ids()`, `_user_is_allowed()`, `_user_is_admin()`
  - These control who can execute and who can reload/upload.
- **Discovery and configuration**:
  - `load_config()`
  - `_discover_scripts()`, `_discover_playbooks()`
  - They read `config.yaml` and build the visible Telegram catalog.
- **Execution path**:
  - `/run` handlers, menu callbacks, script/playbook execution.
  - Includes timeout handling, output capture, and Telegram-safe truncation.
- **Telegram UI**:
  - inline keyboard generation per category and item.
  - commands `/start`, `/menu`, `/list`, `/reload`, `/upload`.

### 2. What to change based on your goal

- **Change global timeout**: edit `bot.default_timeout` in `configs/cbot/config.yaml`.
- **Change output size limit**: edit `bot.max_message_length` in `configs/cbot/config.yaml`.
- **Change permissions logic**: edit RBAC helper functions.
- **Add a new per-script metadata field**: extend `ScriptEntry` and parsing in `load_config()`.
- **Change menu behavior**: update callbacks and `InlineKeyboardMarkup` creation.
- **Add pre-execution validations**: implement checks before calling `subprocess`.

### 3. Recommended developer workflow

1. Test with a simple script first.
2. Tune metadata in `configs/cbot/config.yaml`.
3. Run `/reload` to validate changes.
4. Check container logs if parsing or permissions fail.

## Containerbot image: default option and local option

The lab uses `ghcr.io/abelperezr/containerbot:0.0.1` in `lab.yml`.

Recommended default: pull from GitHub Container Registry:

```bash
docker pull ghcr.io/abelperezr/containerbot:0.0.1
```

Alternative: build the image locally with the included `Dockerfile`, ideal for developers.

```bash
cd small-isp-lab/containerbot
./build
```

## `config.yaml` reference

Primary file: `configs/cbot/config.yaml` (mounted as `/app/config.yaml`).

This repository also contains `containerbot/config.yaml` as source-code reference. To avoid drift, both files should stay aligned, but the one actually used by the running lab is `configs/cbot/config.yaml`.

```yaml
scripts:
  olt-to-bng1-down.sh:
    name: "OLT -> BNG1 Down"
    description: "Disable ethernet-1/1 on OLT (10.99.1.4)"
    category: "Link Failures"
    admin_only: false
    confirm: true
    timeout: 120
    args_prompt: ""
    hidden: false

playbooks:
  lab_ping.yml:
    name: "Lab Ping All Nodes"
    description: "Ping all lab nodes from the bot container"
    category: "Ansible"
    admin_only: false
    confirm: false
    timeout: 180
    hidden: false

ansible:
  inventory: "/app/ansible/inventory/hosts.yml"

bot:
  default_timeout: 120
  max_message_length: 4000
```

Important:

- The `bot:` section is applied by the current implementation (`bot.py`).
- `default_timeout` becomes the default timeout for scripts and playbooks that do not define their own `timeout`.
- `max_message_length` controls output truncation before replying in Telegram.

Supported keys per script/playbook:

- `name`: display name in Telegram.
- `description`: short description.
- `category`: menu category.
- `admin_only`: admin-only execution.
- `confirm`: ask confirmation before execution.
- `timeout`: per-item timeout.
- `args_prompt`: prompt for runtime arguments.
- `hidden`: hide item from menu.

## Important env vars (`secrets.env`)

Recommended workflow:

```bash
cp configs/cbot/secrets.env.example configs/cbot/secrets.env
```

- `TELEGRAM_BOT_TOKEN`: BotFather token (required).
- `ALLOWED_ADMINS`: Telegram IDs with admin permissions.
- `ALLOWED_USERS`: Telegram IDs with operator permissions.
- `LOG_LEVEL`: `DEBUG|INFO|WARNING|ERROR`.
- `MGMT_PROBE_IP`: probe target for startup readiness.
- `POST_BOOT_SLEEP`: extra delay before bot starts.

Note:

- If both `ALLOWED_ADMINS` and `ALLOWED_USERS` are empty, the bot runs in development mode and allows everyone.

## Actual Telegram commands

- `/start` or `/help`: main menu.
- `/menu`: interactive category menu.
- `/list`: flat list of scripts/playbooks.
- `/run <filename> [args...]`: direct execution by filename.
  The parser supports quoted values, for example: `/run manage_authorize.py add user01 --title "VIP Customer"`.
- `/reload`: reload config/discovery (admin only).
- `/upload`: upload `.sh/.py` scripts (admin only).
- `/cancel`: cancel pending argument input.

Implementation behaviors verified in the code:

- automatic script and playbook discovery
- `args_prompt` support
- `confirm` support
- `admin_only` support
- auto-reload through the file watcher and through `/reload`

## Add a new script

1. Copy the script into `configs/cbot/scripts/`.
2. Make it executable.
3. Optionally add metadata override in `configs/cbot/config.yaml`.
4. Run `/reload` in Telegram or wait for auto-reload.

Example:

```bash
cp my_script.sh small-isp-lab/configs/cbot/scripts/
chmod +x small-isp-lab/configs/cbot/scripts/my_script.sh
```

## Direct execution without Telegram

You can also run scripts from terminal for troubleshooting:

```bash
# Access failure through the OLT
docker exec containerbot sh -lc '/app/scripts/olt-to-bng1-down.sh'
docker exec containerbot sh -lc '/app/scripts/olt-to-bng1-up.sh'

# Failure of the link between the BNGs; this also triggers an SRRP role change through policy 1
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1'
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c1/1'

# ESM / FreeRADIUS operations
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py list'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py show "test@test.com"'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py deactivate "test@test.com"'

# Automatic probes for ATP 13 and ATP 14
docker exec containerbot sh -lc '/app/scripts/subscriber-failover-probes.sh srrp-demo start'
docker exec containerbot sh -lc '/app/scripts/subscriber-failover-probes.sh srrp-demo tail'
docker exec containerbot sh -lc '/app/scripts/subscriber-failover-probes.sh srrp-demo stop'
```

Important notes:

- if you run `update-ports-sros.py` directly from the host instead of from `containerbot`, you need the `pygnmi` library installed
- for `manage_authorize.py`, `radius` must be up and the recommended way is to run it inside `containerbot`
- for ATP 13 and ATP 14, the `subscriber-failover-probes.sh` helper avoids having to manually discover the current `ont1` and `ont2` source IPs
