---
sidebar_position: 3
---

# Integración con Telegram (BotFather)

## Paso 1: Crear el Bot en Telegram

1. Abrir Telegram y buscar **@BotFather**
2. Hacer clic en **Start**
3. Enviar el comando `/newbot`
4. Seguir las instrucciones:
   - Nombre del bot: `Small ISP Lab Bot` (o el nombre que prefieras)
   - Username del bot: `small_isp_lab_bot` (debe terminar en `bot`)
5. BotFather te dará un **token** como: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

![Creación del bot en BotFather](/img/BOTFATHER1.png)

![Token entregado por BotFather](/img/BOTFATHER2.png)

## Paso 2: Obtener tu Chat ID

1. Abrir Telegram y buscar **@userinfobot**, **@raw_data_bot** o **@getmyid_bot**
2. Hacer clic en **Start**
3. El bot responderá con algo como:

```text
Your ID: 6111111116
Current chat ID: 6111111116
```

4. Ese número es tu Chat ID

![Chat ID obtenido desde Telegram](/img/GETMYID.png)

## Paso 3: Configurar secrets.env

Editar el archivo `configs/cbot/secrets.env`:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ALLOWED_ADMINS=6111111116
ALLOWED_USERS=6111111116
ENABLE_SCRIPT_UPLOAD=false
MGMT_PROBE_IP=10.99.1.2
POST_BOOT_SLEEP=30
LOG_LEVEL=INFO
```

Notas:

- `TELEGRAM_BOT_TOKEN` es obligatorio.
- `ALLOWED_ADMINS` y `ALLOWED_USERS` aceptan IDs separados por coma.
- si ambos quedan vacíos, el bot opera en modo abierto para desarrollo.
- el archivo versionado de referencia es `configs/cbot/secrets.env.example`.

## Paso 4: Descargar la imagen

```bash
# Desde la raíz del repositorio del containerbot
docker pull ghcr.io/abelperezr/containerbot:0.0.1
```

## Paso 5: Desplegar el Lab

```bash
sudo containerlab deploy -t lab.yml
```

El containerbot se iniciará automáticamente y se conectará a Telegram.

## Uso del Bot

Una vez conectado, el bot presentará un menú con categorías de scripts. Selecciona una categoría para ver los scripts disponibles y ejecútalos con un tap.

:::tip[Comandos Útiles]

- `/start` - Muestra el menú principal
- `/help` - Muestra ayuda
- `/menu` - Menú interactivo por categorías
- `/list` - Lista todos los scripts/playbooks disponibles
- `/run <archivo>` - Ejecuta un script por nombre
:::
