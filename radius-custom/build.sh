#!/bin/sh
set -eu

docker build -t ghcr.io/abelperezr/freeradius-custom:0.1 "$(dirname "$0")"
