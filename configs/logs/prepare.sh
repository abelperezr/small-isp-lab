#!/usr/bin/env bash
set -euo pipefail

mkdir -p configs/logs/loki-data configs/logs/alloy-data
chmod 777 configs/logs/loki-data configs/logs/alloy-data

echo "Prepared writable directories for Loki and Alloy:"
echo "  configs/logs/loki-data"
echo "  configs/logs/alloy-data"
