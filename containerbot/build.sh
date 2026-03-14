#!/bin/sh
set -eu

docker build -t ghcr.io/abelperezr/containerbot:0.0.1 "$(dirname "$0")"
