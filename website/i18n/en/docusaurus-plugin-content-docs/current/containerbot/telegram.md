---
sidebar_position: 3
---

# Integration with Telegram (BotFather)

## Step 1: Create the Bot in Telegram

1. Open Telegram and search **@BotFather**
2. Click **Start**
3. Send the command `/newbot`
4. Follow the instructions:
   - Bot name: `Small ISP Lab Bot` (or whatever name you prefer)
   - Bot username: `small_isp_lab_bot` (must end in `bot`)
5. BotFather will give you a **token** like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

![Bot creation in BotFather](/img/BOTFATHER1.png)

![Token provided by BotFather](/img/BOTFATHER2.png)

## Step 2: Get your Chat ID

1. Open Telegram and search **@userinfobot**, **@raw_data_bot**, or **@getmyid_bot**
2. Click **Start**
3. The bot will respond with something like:

```text
Your ID: 6111111116
Current chat ID: 6111111116
```

4. That number is your Chat ID

![Chat ID retrieved from Telegram](/img/GETMYID.png)

## Step 3: Configure secrets.env

Edit the `configs/cbot/secrets.env` file:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ALLOWED_ADMINS=6111111116
ALLOWED_USERS=6111111116
ENABLE_SCRIPT_UPLOAD=false
MGMT_PROBE_IP=10.99.1.2
POST_BOOT_SLEEP=30
LOG_LEVEL=INFO
```

Notes:

- `TELEGRAM_BOT_TOKEN` is required.
- `ALLOWED_ADMINS` and `ALLOWED_USERS` accept comma-separated IDs.
- if both are empty, the bot runs in open development mode.
- the versioned reference file is `configs/cbot/secrets.env.example`.

## Step 4: Download the Image

```bash
# From the containerbot repository root
docker pull ghcr.io/abelperezr/containerbot:0.0.1
```

## Step 5: Deploy the Lab

```bash
sudo containerlab deploy -t lab.yml
```

The containerbot will start automatically and connect to Telegram.

## Using the Bot

Once connected, the bot will present a menu with script categories. Select a category to see available scripts and run them with a tap.

:::tip[Useful Commands]

- `/start` - Shows the main menu
- `/help` - Show help
- `/menu` - Interactive category menu
- `/list` - List available scripts/playbooks
- `/run <filename>` - Run a script by filename
:::
