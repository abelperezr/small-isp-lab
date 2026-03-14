#!/usr/bin/env bash
curl -s "http://admin:lab123@10.99.1.252/jsonrpc" -d @- <<'EOF' | jq
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "set",
  "params": {
    "commands": [
      {
        "action": "update",
        "path": "/interface[name=ethernet-1/1]",
        "value": {
          "admin-state": "enable"
        }
      }
    ]
  }
}
EOF