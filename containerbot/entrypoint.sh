#!/bin/bash
# =============================================================================
# entrypoint.sh - Containerbot entrypoint for containerlab
# =============================================================================
# 1. Loads secrets from /app/secrets.env (if present)
# 2. Cleans proxy env vars injected by containerlab
# 3. Starts SSH server in background (containerlab management)
# 4. Waits for management network connectivity
# 5. Starts the Telegram bot in foreground (keeps container alive)
# =============================================================================

set -e

# -- Load secrets --
if [ -f /app/secrets.env ]; then
    echo "[entrypoint] Loading /app/secrets.env"
    set -a
    . /app/secrets.env
    set +a
fi

# -- Clean proxy vars (containerlab injects IPv6 addrs that break httpx) --
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY
unset http_proxy https_proxy all_proxy no_proxy
echo "[entrypoint] Proxy env vars cleared"

# -- Start SSH server (background, for containerlab management access) --
echo "[entrypoint] Starting sshd..."
/usr/sbin/sshd -D &

# -- Wait for management network --
echo "[entrypoint] Waiting for management network..."
MAX_WAIT="${MGMT_PROBE_TIMEOUT:-60}"
PROBE_IP="${MGMT_PROBE_IP:-10.99.1.2}"
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
    if ping -c 1 -W 1 "$PROBE_IP" >/dev/null 2>&1; then
        echo "[entrypoint] Management network ready via $PROBE_IP (${WAITED}s)"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "[entrypoint] WARNING: $PROBE_IP not reachable after ${MAX_WAIT}s, starting bot anyway"
fi

# -- Post-boot delay for SR OS nodes --
POST_BOOT_SLEEP="${POST_BOOT_SLEEP:-30}"
echo "[entrypoint] Waiting ${POST_BOOT_SLEEP}s for network nodes to finish booting..."
sleep "$POST_BOOT_SLEEP"

# -- Start the bot (foreground) --
echo "[entrypoint] Starting Containerbot 0.0.1..."
exec python3 /app/bot.py
