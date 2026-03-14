#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DURATION="${DURATION:-90}"
ONT1_UP_BW="${ONT1_UP_BW:-2M}"
ONT1_DOWN_BW="${ONT1_DOWN_BW:-2M}"
ONT2_UP_BW="${ONT2_UP_BW:-3M}"
ONT2_DOWN_BW="${ONT2_DOWN_BW:-3M}"
IPERF_LEN="${IPERF_LEN:-1200}"
SERVER_READY_WAIT="${SERVER_READY_WAIT:-2}"

ONT1_UP_PORT="${ONT1_UP_PORT:-5201}"
ONT1_DOWN_PORT="${ONT1_DOWN_PORT:-5202}"
ONT2_UP_PORT="${ONT2_UP_PORT:-5203}"
ONT2_DOWN_PORT="${ONT2_DOWN_PORT:-5204}"

ONT1_USER="${ONT1_USER:-user}"
ONT1_PASS="${ONT1_PASS:-test}"
ONT1_WAN="${ONT1_WAN:-wan2}"
ONT1_BIND_V6="${ONT1_BIND_V6:-}"

ONT2_USER="${ONT2_USER:-root}"
ONT2_PASS="${ONT2_PASS:-test}"
ONT2_BIND_V6="${ONT2_BIND_V6:-}"
PROM_URL="${PROM_URL:-http://10.99.1.10:9090}"
PROM_WINDOW="${PROM_WINDOW:-5m}"

usage() {
  cat <<EOF
Usage: $(basename "$0") <start-servers|stop-servers|status|report|run|all>

Commands:
  start-servers  Start one iperf3 server per observability flow
  stop-servers   Stop all observability iperf3 servers
  status         Show listening status for all observability ports
  report         Query Prometheus for ingress/egress IPv6 octet increases
  run            Run simultaneous ONT-001 and ONT-002 ingress/egress UDP flows
  all            Start servers, run traffic, then stop servers

Default traffic profile:
  ONT-001 ingress (upload):   ${ONT1_UP_BW} on port ${ONT1_UP_PORT}
  ONT-001 egress  (download): ${ONT1_DOWN_BW} on port ${ONT1_DOWN_PORT}
  ONT-002 ingress (upload):   ${ONT2_UP_BW} on port ${ONT2_UP_PORT}
  ONT-002 egress  (download): ${ONT2_DOWN_BW} on port ${ONT2_DOWN_PORT}

Environment overrides:
  DURATION, IPERF_LEN, SERVER_READY_WAIT
  ONT1_UP_BW, ONT1_DOWN_BW, ONT2_UP_BW, ONT2_DOWN_BW
  ONT1_UP_PORT, ONT1_DOWN_PORT, ONT2_UP_PORT, ONT2_DOWN_PORT
  ONT1_USER, ONT1_PASS, ONT1_WAN, ONT1_BIND_V6
  ONT2_USER, ONT2_PASS, ONT2_BIND_V6
  PROM_URL, PROM_WINDOW
EOF
}

dns_server() {
  DNS_PORT="$1" bash "${ROOT_DIR}/scripts/dns-iperf-server.sh" "$2"
}

start_servers() {
  dns_server "${ONT1_UP_PORT}" start
  dns_server "${ONT1_DOWN_PORT}" start
  dns_server "${ONT2_UP_PORT}" start
  dns_server "${ONT2_DOWN_PORT}" start
}

stop_servers() {
  dns_server "${ONT1_UP_PORT}" stop
  dns_server "${ONT1_DOWN_PORT}" stop
  dns_server "${ONT2_UP_PORT}" stop
  dns_server "${ONT2_DOWN_PORT}" stop
}

status_servers() {
  echo "ONT-001 ingress  : port ${ONT1_UP_PORT}"
  dns_server "${ONT1_UP_PORT}" status
  echo "ONT-001 egress   : port ${ONT1_DOWN_PORT}"
  dns_server "${ONT1_DOWN_PORT}" status
  echo "ONT-002 ingress  : port ${ONT2_UP_PORT}"
  dns_server "${ONT2_UP_PORT}" status
  echo "ONT-002 egress   : port ${ONT2_DOWN_PORT}"
  dns_server "${ONT2_DOWN_PORT}" status
}

run_flow() {
  local label="$1"
  shift
  echo "[${label}] starting"
  set +e
  local output
  output="$("$@" 2>&1)"
  local rc=$?
  set -e
  printf '%s\n' "${output}"
  if [[ ${rc} -ne 0 ]] && grep -q "unable to read from stream socket: Resource temporarily unavailable" <<<"${output}"; then
    rc=0
    echo "[${label}] warning: iperf3 closed with a transient stream error after transferring data"
  fi
  if [[ ${rc} -eq 0 ]]; then
    echo "[${label}] done"
  else
    echo "[${label}] failed rc=${rc}"
  fi
  return "${rc}"
}

run_traffic() {
  local rc=0

  (
    cd "${ROOT_DIR}"

    run_flow "ONT-001 ingress" env \
      ONT_USER="${ONT1_USER}" \
      ONT_PASS="${ONT1_PASS}" \
      ONT_WAN="${ONT1_WAN}" \
      ONT_BIND_V6="${ONT1_BIND_V6}" \
      DURATION="${DURATION}" \
      IPERF_BW="${ONT1_UP_BW}" \
      IPERF_LEN="${IPERF_LEN}" \
      IPERF_PORT="${ONT1_UP_PORT}" \
      bash scripts/ont1-subscriber-traffic.sh udp-upload
  ) &
  local pid1=$!

  (
    cd "${ROOT_DIR}"

    run_flow "ONT-001 egress" env \
      ONT_USER="${ONT1_USER}" \
      ONT_PASS="${ONT1_PASS}" \
      ONT_WAN="${ONT1_WAN}" \
      ONT_BIND_V6="${ONT1_BIND_V6}" \
      DURATION="${DURATION}" \
      IPERF_BW="${ONT1_DOWN_BW}" \
      IPERF_LEN="${IPERF_LEN}" \
      IPERF_PORT="${ONT1_DOWN_PORT}" \
      bash scripts/ont1-subscriber-traffic.sh udp-download
  ) &
  local pid2=$!

  (
    cd "${ROOT_DIR}"

    run_flow "ONT-002 ingress" env \
      ONT_USER="${ONT2_USER}" \
      ONT_PASS="${ONT2_PASS}" \
      ONT_BIND_V6="${ONT2_BIND_V6}" \
      DURATION="${DURATION}" \
      IPERF_BW="${ONT2_UP_BW}" \
      IPERF_LEN="${IPERF_LEN}" \
      IPERF_PORT="${ONT2_UP_PORT}" \
      bash scripts/ont2-subscriber-traffic.sh udp-upload
  ) &
  local pid3=$!

  (
    cd "${ROOT_DIR}"

    run_flow "ONT-002 egress" env \
      ONT_USER="${ONT2_USER}" \
      ONT_PASS="${ONT2_PASS}" \
      ONT_BIND_V6="${ONT2_BIND_V6}" \
      DURATION="${DURATION}" \
      IPERF_BW="${ONT2_DOWN_BW}" \
      IPERF_LEN="${IPERF_LEN}" \
      IPERF_PORT="${ONT2_DOWN_PORT}" \
      bash scripts/ont2-subscriber-traffic.sh udp-download
  ) &
  local pid4=$!

  wait "${pid1}" || rc=1
  wait "${pid2}" || rc=1
  wait "${pid3}" || rc=1
  wait "${pid4}" || rc=1

  return "${rc}"
}

prom_query() {
  local query="$1"
  curl -fsS --get \
    --data-urlencode "query=${query}" \
    "${PROM_URL}/api/v1/query"
}

report_prometheus() {
  local filter='subscriber_subscriber_id=~"ONT-001|ONT-002"'
  local ingress_query="sum by (subscriber_subscriber_id,source) (increase(subscriber_mgmt_subscriber_sla_profile_instance_ingress_qos_statistics_ipv6_forwarded_octets{${filter}}[${PROM_WINDOW}]))"
  local egress_query="sum by (subscriber_subscriber_id,source) (increase(subscriber_mgmt_subscriber_sla_profile_instance_egress_qos_statistics_ipv6_forwarded_octets{${filter}}[${PROM_WINDOW}]))"

  echo "Prometheus window: ${PROM_WINDOW}"
  echo "--- ingress octets increase ---"
  prom_query "${ingress_query}" | jq '.data.result[] | {subscriber:.metric.subscriber_subscriber_id, source:.metric.source, octets:.value[1]}'
  echo "--- egress octets increase ---"
  prom_query "${egress_query}" | jq '.data.result[] | {subscriber:.metric.subscriber_subscriber_id, source:.metric.source, octets:.value[1]}'
}

cmd="${1:-}"

case "${cmd}" in
  start-servers)
    start_servers
    ;;
  stop-servers)
    stop_servers
    ;;
  status)
    status_servers
    ;;
  report)
    report_prometheus
    ;;
  run)
    run_traffic
    report_prometheus
    ;;
  all)
    trap stop_servers EXIT
    start_servers
    sleep "${SERVER_READY_WAIT}"
    run_traffic
    report_prometheus
    ;;
  *)
    usage
    exit 1
    ;;
esac
