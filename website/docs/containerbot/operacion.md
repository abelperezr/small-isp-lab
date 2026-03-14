---
sidebar_position: 2
---

# Operación del Containerbot

## Objetivo

Esta guía está orientada a operadores y desarrolladores que quieran usar, extender o mantener Containerbot dentro del laboratorio.

La idea no es solo explicar cómo está construido el bot, sino servir como puente práctico hacia los ATP.

## Antes de llegar a los ATP

Validar primero que el entorno operativo mínimo esté sano:

```bash
docker ps -a --format '{{.Names}}\t{{.Status}}' | rg '^(containerbot|radius|ont1|ont2|pc1)\b'
docker exec containerbot sh -lc 'ls -1 /app/scripts && echo __SEP__ && ls -1 /app/ansible/playbooks'
docker logs --tail 20 containerbot
```

Esperado:

- `containerbot` en `Up`
- `radius` en `Up` si vas a usar `manage_authorize.py`
- scripts visibles en `/app/scripts`
- playbooks visibles en `/app/ansible/playbooks`
- logs del bot sin errores de arranque

Nota operativa:

- el file watcher del bot sí recarga automáticamente cuando cambian scripts o playbooks montados
- si `radius` está abajo, `manage_authorize.py` no podrá listar ni modificar `authorize` por SSH remoto

## Dos formas de operar

### 1. Desde Telegram

Usas el menú o `/run ...` directamente en el chat del bot.

Ejemplos:

```text
/run olt-to-bng1-down.sh
/run carrier1-to-bng2-down.sh
/run update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1
/run manage_authorize.py list
```

Importante:

- `/run ...` es un comando del bot de Telegram
- no es un comando genérico del shell del host

### 2. Desde terminal del host

Usas `docker exec containerbot ...` para ejecutar exactamente los mismos scripts dentro del contenedor, sin pasar por Telegram.

Ejemplos:

```bash
docker exec containerbot sh -lc '/app/scripts/olt-to-bng1-down.sh'
docker exec containerbot sh -lc '/app/scripts/carrier1-to-bng2-down.sh'
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py list'
```

Recomendación:

- si estás siguiendo un ATP, usa la terminal del host cuando quieras reproducibilidad exacta
- usa Telegram cuando quieras operación guiada y confirmaciones desde el menú
- para scripts Python operativos como `manage_authorize.py` y `update-ports-sros.py`, la opción recomendada es ejecutarlos con `docker exec` hacia `containerbot`

## Ruta rápida hacia los ATP

Scripts más útiles y a qué ATP te llevan:

- `update-ports-sros.py`
  - ATP 6: SRRP y BGP
  - ATP 13: Failover Suscriptores SRRP
  - útil para bajar o subir puertos SR OS por gNMI
- `olt-to-bng1-down.sh` y `olt-to-bng1-up.sh`
  - ATP 14: Final Boss
  - simulan la caída del acceso `OLT -> BNG MASTER`
- `carrier1-to-bng1-down.sh` y `carrier1-to-bng1-up.sh`
  - ATP 6: SRRP y BGP
  - simulan la caída de `Carrier1` hacia `BNG MASTER`
- `carrier1-to-bng2-down.sh` y `carrier1-to-bng2-up.sh`
  - ATP 14: Final Boss
  - simulan la caída de `Carrier1` hacia `BNG SLAVE`
- `manage_authorize.py`
  - ATP 7: ESM
  - permite listar, desactivar, agregar, editar y desconectar suscriptores en FreeRADIUS
- `subscriber-failover-probes.sh`
  - ATP 13: `srrp-demo`
  - ATP 14: `final-boss`
  - detecta IPs fuente actuales, lanza probes, muestra logs y limpia procesos

Atajos ya validados:

```bash
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo start
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo watch
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo tail
bash configs/cbot/scripts/subscriber-failover-probes.sh srrp-demo stop

bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss start
bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss watch
bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss tail
bash configs/cbot/scripts/subscriber-failover-probes.sh final-boss stop
```

Para ATP 6 y ATP 7, prioriza estas formas:

```bash
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1'
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c1/1'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py list'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py show \"test@test.com\"'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py deactivate \"test@test.com\"'
```

## Estructura real del proyecto

Código de imagen:

- `small-isp-lab/containerbot/`
  - `bot.py`
  - `config.yaml`
  - `entrypoint.sh`
  - `Dockerfile`
  - `requirements.txt`

Configuración montada por el lab:

- `small-isp-lab/configs/cbot/`
  - `scripts/`
  - `ansible/`
  - `config.yaml`
  - `secrets.env` (local, no versionado)
  - `secrets.env.example` (plantilla versionada)

## Flujo de ejecución

1. `entrypoint.sh` carga `secrets.env`.
2. Arranca `sshd` para administración del contenedor.
3. Espera conectividad de gestión (`MGMT_PROBE_IP`).
4. Inicia `python3 /app/bot.py`.
5. El bot hace auto-discovery de scripts/playbooks y construye el menú de Telegram.
6. Un file watcher recarga la configuración automáticamente cuando cambian archivos.

## Qué descubre automáticamente el bot

- Scripts en `SCRIPTS_DIR` con extensiones `.sh` y `.py`.
- Playbooks en `ANSIBLE_DIR/playbooks` con extensión `.yml` o `.yaml`.
- Si no hay override en `config.yaml`, usa valores derivados del nombre del archivo.

## Guía de `bot.py` para modificarlo sin romperlo

Archivo fuente: `small-isp-lab/containerbot/bot.py`.

### 1. Bloques principales del código

- **Variables y constantes globales**:
  - `SCRIPTS_DIR`, `ANSIBLE_DIR`, `CONFIG_FILE`
  - defaults internos usados como fallback si `config.yaml` no define `bot.default_timeout` o `bot.max_message_length`
- **RBAC**:
  - `_parse_ids()`, `_user_is_allowed()`, `_user_is_admin()`
  - Controlan quién puede ejecutar y quién puede recargar/subir.
- **Discovery y configuración**:
  - `load_config()`
  - `_discover_scripts()`, `_discover_playbooks()`
  - Leen `config.yaml` y generan el catálogo visible en Telegram.
- **Ejecución**:
  - handlers de `/run`, callbacks del menú y ejecución de scripts/playbooks.
  - Hay control de timeout, captura de output y truncado para Telegram.
- **UI de Telegram**:
  - construcción de teclados inline por categoría y por ítem.
  - comandos `/start`, `/menu`, `/list`, `/reload`, `/upload`.

### 2. Qué modificar según el objetivo

- **Cambiar timeout global**: editar `bot.default_timeout` en `configs/cbot/config.yaml`.
- **Cambiar límite de output**: editar `bot.max_message_length` en `configs/cbot/config.yaml`.
- **Cambiar lógica de permisos**: editar helpers RBAC.
- **Agregar nuevo metadato por script**: ampliar `ScriptEntry` y su parseo en `load_config()`.
- **Cambiar experiencia de menús**: ajustar callbacks y generación de `InlineKeyboardMarkup`.
- **Agregar validaciones antes de ejecutar**: centralizar en la ruta de ejecución antes del `subprocess`.

### 3. Recomendación de trabajo para developers

1. Probar primero en local con un script simple.
2. Ajustar metadatos en `configs/cbot/config.yaml`.
3. Ejecutar `/reload` para validar cambios.
4. Revisar logs del contenedor si falla parsing o permisos.

## Imagen del Containerbot: opción por defecto y opción local

El laboratorio usa por etiqueta local `ghcr.io/abelperezr/containerbot:0.0.1` en `lab.yml`.

Opción recomendada (por defecto): descargar desde GitHub Container Registry:

```bash
docker pull ghcr.io/abelperezr/containerbot:0.0.1
```

Opción alternativa: construir la imagen local con el `Dockerfile` incluido ideal para desarrolladores.

```bash
cd small-isp-lab/containerbot
./build
```

## Referencia de `config.yaml`

El archivo principal es `configs/cbot/config.yaml` (montado en `/app/config.yaml`).

En este repositorio también existe `containerbot/config.yaml` como referencia del código fuente. Para evitar desalineaciones, conviene mantener ambos archivos consistentes, pero el que realmente usa el lab en runtime es `configs/cbot/config.yaml`.

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

Importante:

- La sección `bot:` sí se aplica en la implementación actual (`bot.py`).
- `default_timeout` define el timeout por defecto para scripts y playbooks que no traen un `timeout` propio.
- `max_message_length` controla el truncado de salida antes de responder por Telegram.

Claves soportadas por script/playbook:

- `name`: nombre visible en Telegram.
- `description`: descripción corta.
- `category`: categoría del menú.
- `admin_only`: solo admins.
- `confirm`: requiere confirmación antes de ejecutar.
- `timeout`: timeout por ítem.
- `args_prompt`: solicita argumentos antes de ejecutar.
- `hidden`: oculta el ítem del menú.

## Variables de entorno importantes (`secrets.env`)

Flujo recomendado:

```bash
cp configs/cbot/secrets.env.example configs/cbot/secrets.env
```

- `TELEGRAM_BOT_TOKEN`: token de BotFather (requerido).
- `ALLOWED_ADMINS`: IDs Telegram con permisos admin.
- `ALLOWED_USERS`: IDs Telegram con permisos de operador.
- `LOG_LEVEL`: `DEBUG|INFO|WARNING|ERROR`.
- `MGMT_PROBE_IP`: IP para validar red de gestión en el arranque.
- `POST_BOOT_SLEEP`: espera adicional antes de iniciar el bot.

Nota:

- Si `ALLOWED_ADMINS` y `ALLOWED_USERS` están vacíos, el bot queda en modo desarrollo y permite a todos.

## Comandos reales de Telegram

- `/start` o `/help`: menú principal.
- `/menu`: menú interactivo por categorías.
- `/list`: listado plano de scripts/playbooks.
- `/run <archivo> [args...]`: ejecución directa por nombre de archivo.
  El parser soporta comillas, por ejemplo: `/run manage_authorize.py add user01 --title "Cliente VIP"`.
- `/reload`: recarga configuración y discovery (solo admin).
- `/upload`: permite subir scripts `.sh/.py` (solo admin).
- `/cancel`: cancela captura de argumentos pendiente.

Comportamientos verificados en la implementación:

- discovery automático de scripts y playbooks
- soporte de `args_prompt`
- soporte de `confirm`
- soporte de `admin_only`
- recarga automática por file watcher y por `/reload`

## Cómo agregar un script nuevo

1. Copia el script a `configs/cbot/scripts/`.
2. Dale permisos de ejecución.
3. (Opcional) agrega override en `configs/cbot/config.yaml`.
4. Ejecuta `/reload` en Telegram o espera auto-reload.

Ejemplo:

```bash
cp mi_script.sh small-isp-lab/configs/cbot/scripts/
chmod +x small-isp-lab/configs/cbot/scripts/mi_script.sh
```

## Ejecución directa sin Telegram

También puedes ejecutar desde terminal para troubleshooting:

```bash
# Falla de acceso vía OLT
docker exec containerbot sh -lc '/app/scripts/olt-to-bng1-down.sh'
docker exec containerbot sh -lc '/app/scripts/olt-to-bng1-up.sh'

# Falla del enlace entre BNGs; también dispara cambio de rol SRRP por policy 1
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state disable --port-id 1/1/c1/1'
docker exec containerbot sh -lc 'python3 /app/scripts/update-ports-sros.py --host 10.99.1.2 --state enable --port-id 1/1/c1/1'

# Operaciones de ESM / FreeRADIUS
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py list'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py show "test@test.com"'
docker exec containerbot sh -lc 'python3 /app/scripts/manage_authorize.py deactivate "test@test.com"'

# Probes automáticos para ATP 13 y ATP 14
docker exec containerbot sh -lc '/app/scripts/subscriber-failover-probes.sh srrp-demo start'
docker exec containerbot sh -lc '/app/scripts/subscriber-failover-probes.sh srrp-demo tail'
docker exec containerbot sh -lc '/app/scripts/subscriber-failover-probes.sh srrp-demo stop'
```

Notas importantes:

- si ejecutas `update-ports-sros.py` directamente desde el host y no desde `containerbot`, necesitas tener instalada la librería `pygnmi`
- para `manage_authorize.py`, `radius` debe estar arriba y la forma recomendada es ejecutarlo dentro de `containerbot`
- para ATP 13 y ATP 14, el helper `subscriber-failover-probes.sh` evita tener que descubrir manualmente las IP actuales de `ont1` y `ont2`
