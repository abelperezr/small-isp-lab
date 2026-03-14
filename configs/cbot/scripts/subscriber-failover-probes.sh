#!/usr/bin/env bash

set -euo pipefail

TARGET_V6="${TARGET_V6:-2001:db8:aaaa::2}"
TARGET_V4="${TARGET_V4:-99.99.99.99}"
PING_INTERVAL="${PING_INTERVAL:-0.2}"
PING_TIMEOUT="${PING_TIMEOUT:-1}"
TAIL_LINES="${TAIL_LINES:-12}"

PREFIX=""

usage() {
  cat <<'EOF'
Usage: subscriber-failover-probes.sh <srrp-demo|final-boss> <show-bindings|start|stop|tail|watch>

Commands:
  show-bindings  Resolve and print the current subscriber source IPs
  start          Resolve the source IPs and launch all ATP ping probes
  stop           Stop all ATP ping probes for the selected scenario
  tail           Show the latest lines from all ATP probe logs
  watch          Refresh a live dashboard with the latest line from each probe log

Environment overrides:
  TARGET_V6      default: 2001:db8:aaaa::2
  TARGET_V4      default: 99.99.99.99
  PING_INTERVAL  default: 0.2
  PING_TIMEOUT   default: 1
  TAIL_LINES     default: 12
  WATCH_INTERVAL default: 1
EOF
}

require_command() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    printf 'Required command not found: %s\n' "${cmd}" >&2
    exit 1
  fi
}

set_prefix() {
  local scenario="$1"

  case "${scenario}" in
    srrp-demo)
      PREFIX="srrp_demo"
      ;;
    final-boss)
      PREFIX="final_boss"
      ;;
    *)
      printf 'Unknown scenario: %s\n' "${scenario}" >&2
      usage
      exit 1
      ;;
  esac
}

docker_sh() {
  local container="$1"
  local command="$2"

  docker exec "${container}" sh -lc "${command}"
}

resolve_single() {
  local container="$1"
  local command="$2"
  local value

  value="$(docker_sh "${container}" "${command}")"
  value="${value//$'\r'/}"

  if [[ -z "${value}" ]]; then
    printf 'Could not resolve the required source IP on %s\n' "${container}" >&2
    exit 1
  fi

  printf '%s\n' "${value}"
}

resolve_bindings() {
  ONT1_WAN1_V6="$(resolve_single ont1 "ip -o -6 addr show dev eth1.150 scope global | awk 'NR==1 {print \$4}' | cut -d/ -f1")"
  ONT1_WAN2_V6="$(resolve_single ont1 "ip -o -6 addr show dev eth3.200 scope global | awk 'NR==1 {print \$4}' | cut -d/ -f1")"
  ONT1_WAN2_V4="$(resolve_single ont1 "ip -o -4 addr show dev eth3.200 scope global | awk 'NR==1 {print \$4}' | cut -d/ -f1")"
  ONT2_PPP_V6="$(resolve_single ont2 "ip -o -6 addr show dev ppp0 scope global | awk 'NR==1 {print \$4}' | cut -d/ -f1")"
}

print_bindings() {
  printf 'ONT1_WAN1_V6=%s\n' "${ONT1_WAN1_V6}"
  printf 'ONT1_WAN2_V6=%s\n' "${ONT1_WAN2_V6}"
  printf 'ONT1_WAN2_V4=%s\n' "${ONT1_WAN2_V4}"
  printf 'ONT2_PPP_V6=%s\n' "${ONT2_PPP_V6}"
}

start_probes() {
  resolve_bindings
  print_bindings

  stop_probes >/dev/null 2>&1 || true

  docker_sh ont1 "rm -f /tmp/${PREFIX}_*"
  docker_sh ont2 "rm -f /tmp/${PREFIX}_*"
  docker_sh pc1 "rm -f /tmp/${PREFIX}_*"

  docker_sh ont1 "nohup ping -D -n -i ${PING_INTERVAL} -W ${PING_TIMEOUT} -I ${ONT1_WAN1_V6} ${TARGET_V6} > /tmp/${PREFIX}_ont1_wan1_v6.log 2>&1 & echo \$! > /tmp/${PREFIX}_ont1_wan1_v6.pid"
  docker_sh ont1 "nohup ping -D -n -i ${PING_INTERVAL} -W ${PING_TIMEOUT} -I ${ONT1_WAN2_V6} ${TARGET_V6} > /tmp/${PREFIX}_ont1_wan2_v6.log 2>&1 & echo \$! > /tmp/${PREFIX}_ont1_wan2_v6.pid"
  docker_sh ont1 "nohup ping -D -n -i ${PING_INTERVAL} -W ${PING_TIMEOUT} -I ${ONT1_WAN2_V4} ${TARGET_V4} > /tmp/${PREFIX}_ont1_wan2_v4.log 2>&1 & echo \$! > /tmp/${PREFIX}_ont1_wan2_v4.pid"
  docker_sh ont2 "nohup ping -D -n -i ${PING_INTERVAL} -W ${PING_TIMEOUT} -I ${ONT2_PPP_V6} ${TARGET_V6} > /tmp/${PREFIX}_ont2_ppp_v6.log 2>&1 & echo \$! > /tmp/${PREFIX}_ont2_ppp_v6.pid"
  docker_sh pc1 "nohup ping -D -n -i ${PING_INTERVAL} -W ${PING_TIMEOUT} ${TARGET_V6} > /tmp/${PREFIX}_pc1_lan_v6.log 2>&1 & echo \$! > /tmp/${PREFIX}_pc1_lan_v6.pid"

  printf 'Started probes for %s\n' "${PREFIX}"
}

stop_pidfile() {
  local container="$1"
  local pidfile="$2"
  local pid

  pid="$(docker_sh "${container}" "cat ${pidfile} 2>/dev/null" || true)"
  pid="${pid//$'\r'/}"

  if [[ -n "${pid}" ]]; then
    docker_sh "${container}" "kill -INT ${pid} 2>/dev/null || true"
  fi
}

stop_probes() {
  stop_pidfile ont1 "/tmp/${PREFIX}_ont1_wan1_v6.pid"
  stop_pidfile ont1 "/tmp/${PREFIX}_ont1_wan2_v6.pid"
  stop_pidfile ont1 "/tmp/${PREFIX}_ont1_wan2_v4.pid"
  stop_pidfile ont2 "/tmp/${PREFIX}_ont2_ppp_v6.pid"
  stop_pidfile pc1 "/tmp/${PREFIX}_pc1_lan_v6.pid"

  printf 'Stopped probes for %s\n' "${PREFIX}"
}

tail_probes() {
  printf '=== ont1 WAN1 IPv6 ===\n'
  docker_sh ont1 "tail -n ${TAIL_LINES} /tmp/${PREFIX}_ont1_wan1_v6.log 2>/dev/null || true"
  printf '=== ont1 WAN2 IPv6 ===\n'
  docker_sh ont1 "tail -n ${TAIL_LINES} /tmp/${PREFIX}_ont1_wan2_v6.log 2>/dev/null || true"
  printf '=== ont1 WAN2 IPv4 ===\n'
  docker_sh ont1 "tail -n ${TAIL_LINES} /tmp/${PREFIX}_ont1_wan2_v4.log 2>/dev/null || true"
  printf '=== ont2 PPP IPv6 ===\n'
  docker_sh ont2 "tail -n ${TAIL_LINES} /tmp/${PREFIX}_ont2_ppp_v6.log 2>/dev/null || true"
  printf '=== pc1 LAN IPv6 ===\n'
  docker_sh pc1 "tail -n ${TAIL_LINES} /tmp/${PREFIX}_pc1_lan_v6.log 2>/dev/null || true"
}

print_watch_block() {
  local title="$1"
  local container="$2"
  local logfile="$3"
  local latest

  latest="$(docker_sh "${container}" "tail -n 1 ${logfile} 2>/dev/null || true")"
  latest="${latest//$'\r'/}"

  printf '=== %s ===\n' "${title}"
  if [[ -n "${latest}" ]]; then
    printf '%s\n' "${latest}"
  else
    printf '(waiting for probe output)\n'
  fi
  printf '\n'
}

watch_probes() {
  local watch_interval="${WATCH_INTERVAL:-1}"

  while true; do
    clear
    printf 'Scenario: %s\n' "${PREFIX}"
    printf 'Updated: %s\n\n' "$(date '+%Y-%m-%d %H:%M:%S')"

    print_watch_block "ont1 WAN1 IPv6" ont1 "/tmp/${PREFIX}_ont1_wan1_v6.log"
    print_watch_block "ont1 WAN2 IPv6" ont1 "/tmp/${PREFIX}_ont1_wan2_v6.log"
    print_watch_block "ont1 WAN2 IPv4" ont1 "/tmp/${PREFIX}_ont1_wan2_v4.log"
    print_watch_block "ont2 PPP IPv6" ont2 "/tmp/${PREFIX}_ont2_ppp_v6.log"
    print_watch_block "pc1 LAN IPv6" pc1 "/tmp/${PREFIX}_pc1_lan_v6.log"

    printf 'Press Ctrl+C to exit.\n'
    sleep "${watch_interval}"
  done
}

main() {
  local scenario="${1:-}"
  local command="${2:-}"

  if [[ -z "${scenario}" || -z "${command}" ]]; then
    usage
    exit 1
  fi

  require_command docker
  set_prefix "${scenario}"

  case "${command}" in
    show-bindings)
      resolve_bindings
      print_bindings
      ;;
    start)
      start_probes
      ;;
    stop)
      stop_probes
      ;;
    tail)
      tail_probes
      ;;
    watch)
      watch_probes
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
