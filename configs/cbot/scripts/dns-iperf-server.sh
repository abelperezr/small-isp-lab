#!/usr/bin/env bash

set -euo pipefail

DNS_HOST="${DNS_HOST:-10.99.1.13}"
DNS_USER="${DNS_USER:-admin}"
DNS_PASS="${DNS_PASS:-multit00l}"
DNS_CONTAINER="${DNS_CONTAINER:-dns}"
DNS_BIND_V6="${DNS_BIND_V6:-2001:db8:aaaa::2}"
DNS_PORT="${DNS_PORT:-5201}"
DNS_LOG="${DNS_LOG:-/tmp/iperf3-dns-${DNS_PORT}.log}"

usage() {
  cat <<EOF
Usage: $(basename "$0") <start|stop|status|logs>

Environment overrides:
  DNS_HOST      default: ${DNS_HOST}
  DNS_USER      default: ${DNS_USER}
  DNS_PASS      default: ${DNS_PASS}
  DNS_CONTAINER default: ${DNS_CONTAINER}
  DNS_BIND_V6   default: ${DNS_BIND_V6}
  DNS_PORT      default: ${DNS_PORT}
  DNS_LOG       default: ${DNS_LOG}
EOF
}

ssh_dns() {
  sshpass -p "${DNS_PASS}" ssh \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    "${DNS_USER}@${DNS_HOST}" "$@"
}

run_dns() {
  local cmd="$1"

  if docker inspect "${DNS_CONTAINER}" >/dev/null 2>&1; then
    docker exec -u 0 "${DNS_CONTAINER}" sh -lc "${cmd}"
    return
  fi

  ssh_dns "${cmd}"
}

ensure_ipv6_service_routes() {
  run_dns "
    ip -6 route replace 2001:db8:100::/56 via 2001:db8:aaaa::1 dev eth1
    ip -6 route replace 2001:db8:200::/48 via 2001:db8:aaaa::1 dev eth1
    ip -6 route replace 2001:db8:cccc::/56 via 2001:db8:aaab::1 dev eth2
    ip -6 route replace 2001:db8:dddd::/48 via 2001:db8:aaab::1 dev eth2
  "
}

cmd="${1:-}"

case "${cmd}" in
  start)
    ensure_ipv6_service_routes
    run_dns "for pid in \$(netstat -lntp 2>/dev/null | grep ':${DNS_PORT} ' | sed -n 's/.*LISTEN[[:space:]]*\\([0-9][0-9]*\\)\\/iperf3.*/\\1/p' || true); do kill \${pid} || true; done"
    if docker inspect "${DNS_CONTAINER}" >/dev/null 2>&1; then
      docker exec -u 0 "${DNS_CONTAINER}" iperf3 -s -D -B "${DNS_BIND_V6}" -p "${DNS_PORT}" --logfile "${DNS_LOG}" >/dev/null
    else
      ssh_dns "nohup iperf3 -s -D -B ${DNS_BIND_V6} -p ${DNS_PORT} --logfile ${DNS_LOG} >/dev/null 2>&1 </dev/null &"
    fi
    sleep 1
    run_dns "netstat -lnt 2>/dev/null | grep ':${DNS_PORT} ' || true"
    ;;
  stop)
    run_dns "for pid in \$(netstat -lntp 2>/dev/null | grep ':${DNS_PORT} ' | sed -n 's/.*LISTEN[[:space:]]*\\([0-9][0-9]*\\)\\/iperf3.*/\\1/p' || true); do kill \${pid} || true; done"
    ;;
  status)
    run_dns "netstat -lntp 2>/dev/null | grep ':${DNS_PORT} ' || true"
    ;;
  logs)
    run_dns "tail -n 50 ${DNS_LOG} || true"
    ;;
  *)
    usage
    exit 1
    ;;
esac
