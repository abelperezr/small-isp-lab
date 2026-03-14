#!/usr/bin/env bash

for ip in 10.99.1.252 10.99.1.253 10.99.1.4; do
  echo "==== $ip ethernet-1/1 ===="
  curl -s "http://admin:lab123@${ip}/jsonrpc" -d @- <<'EOF' | python3 -m json.tool
{
  "jsonrpc": "2.0",
  "id": 100,
  "method": "get",
  "params": {
    "commands": [
      {
        "path": "/interface[name=ethernet-1/1]/admin-state",
        "datastore": "running"
      },
      {
        "path": "/interface[name=ethernet-1/1]/oper-state",
        "datastore": "state"
      }
    ]
  }
}
EOF
done
