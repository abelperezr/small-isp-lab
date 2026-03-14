#!/usr/bin/env bash

set -euo pipefail

ONT_HOST="${ONT_HOST:-10.99.1.6}"
ONT_USER="${ONT_USER:-root}"
ONT_PASS="${ONT_PASS:-test}"
ONT_CONTAINER="${ONT_CONTAINER:-ont2}"

IPERF_SERVER_V6="${IPERF_SERVER_V6:-2001:db8:aaaa::2}"
ONT_BIND_V6="${ONT_BIND_V6:-}"
IPERF_PORT="${IPERF_PORT:-5201}"
DURATION="${DURATION:-20}"
PARALLEL="${PARALLEL:-1}"
IPERF_MSS="${IPERF_MSS:-1400}"
IPERF_BW="${IPERF_BW:-5M}"
IPERF_LEN="${IPERF_LEN:-1200}"

usage() {
  cat <<EOF
Usage: $(basename "$0") <upload|download|both|udp-upload|udp-download|dns64>

Commands:
  upload     Run iperf3 from ont2 to dns over the subscriber IPv6 address
  download   Run iperf3 reverse mode from dns to ont2
  both       Run upload and then download
  udp-upload Run iperf3 UDP with fixed bitrate from ont2 to dns
  udp-download Run iperf3 UDP reverse mode with fixed bitrate
  dns64      Generate repeated DNS64 AAAA lookups from ont2
  show-bind  Print the resolved IPv6 source on ppp0

Environment overrides:
  ONT_HOST        default: ${ONT_HOST}
  ONT_USER        default: ${ONT_USER}
  ONT_PASS        default: ${ONT_PASS}
  ONT_CONTAINER   default: ${ONT_CONTAINER} (used when sshpass is unavailable)
  IPERF_SERVER_V6 default: ${IPERF_SERVER_V6}
  ONT_BIND_V6     override the detected IPv6 source address on ppp0
  IPERF_PORT      default: ${IPERF_PORT}
  DURATION        default: ${DURATION}
  PARALLEL        default: ${PARALLEL}
  IPERF_MSS       default: ${IPERF_MSS} (set 0 to disable MSS clamp)
  IPERF_BW        default: ${IPERF_BW}
  IPERF_LEN       default: ${IPERF_LEN}
EOF
}

ont_exec() {
  local cmd="$1"

  if command -v sshpass >/dev/null 2>&1; then
    sshpass -p "${ONT_PASS}" ssh \
      -o StrictHostKeyChecking=no \
      -o UserKnownHostsFile=/dev/null \
      "${ONT_USER}@${ONT_HOST}" "${cmd}"
    return
  fi

  if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -Fxq "${ONT_CONTAINER}"; then
    docker exec "${ONT_CONTAINER}" bash -lc "${cmd}"
    return
  fi

  printf 'Neither sshpass nor docker fallback for container %s is available\n' "${ONT_CONTAINER}" >&2
  exit 1
}

resolve_bind_v6() {
  local bind_v6

  if [[ -n "${ONT_BIND_V6}" ]]; then
    printf '%s\n' "${ONT_BIND_V6}"
    return
  fi

  bind_v6="$(
    ont_exec "ip -o -6 addr show dev ppp0 scope global | awk 'NR==1 {print \$4}' | cut -d/ -f1"
  )"

  if [[ -z "${bind_v6}" ]]; then
    printf 'Could not resolve a global IPv6 address on ppp0\n' >&2
    exit 1
  fi

  printf '%s\n' "${bind_v6}"
}

show_bind() {
  local bind_v6
  bind_v6="$(resolve_bind_v6)"
  printf 'INTERFACE=ppp0\n'
  printf 'ONT_BIND_V6=%s\n' "${bind_v6}"
}

run_iperf() {
  local reverse_flag="${1:-}" bind_v6 mss_flag=""
  bind_v6="$(resolve_bind_v6)"
  if [[ "${IPERF_MSS}" != "0" ]]; then
    mss_flag="-M ${IPERF_MSS}"
  fi
  ont_exec "iperf3 -6 -c ${IPERF_SERVER_V6} -B ${bind_v6} -p ${IPERF_PORT} -t ${DURATION} -P ${PARALLEL} ${mss_flag} ${reverse_flag}"
}

run_iperf_udp() {
  local reverse_flag="${1:-}" bind_v6
  bind_v6="$(resolve_bind_v6)"
  ont_exec "iperf3 -6 -u -c ${IPERF_SERVER_V6} -B ${bind_v6} -p ${IPERF_PORT} -t ${DURATION} -b ${IPERF_BW} -l ${IPERF_LEN} ${reverse_flag}"
}

run_dns64() {
  local bind_v6
  bind_v6="$(resolve_bind_v6)"
  ont_exec "start=\$(date +%s); end=\$((start+${DURATION})); while [ \"\$(date +%s)\" -lt \"\$end\" ]; do dig -b ${bind_v6} @${IPERF_SERVER_V6} openai.com AAAA +short > /dev/null; done"
}

cmd="${1:-}"

case "${cmd}" in
  upload)
    run_iperf ""
    ;;
  download)
    run_iperf "-R"
    ;;
  both)
    run_iperf ""
    run_iperf "-R"
    ;;
  udp-upload)
    run_iperf_udp ""
    ;;
  udp-download)
    run_iperf_udp "-R"
    ;;
  dns64)
    run_dns64
    ;;
  show-bind)
    show_bind
    ;;
  *)
    usage
    exit 1
    ;;
esac
