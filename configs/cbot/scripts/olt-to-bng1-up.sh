#!/usr/bin/env bash
curl -s "http://admin:lab123@10.99.1.4/jsonrpc" -d @- <<'EOF' | python3 -m json.tool
{
  "jsonrpc": "2.0",
  "id": 202,
  "method": "set",
  "params": {
    "commands": [
      {
        "action": "update",
        "path": "/interface[name=ethernet-1/1]",
        "value": { "admin-state": "enable" }
      }
    ]
  }
}
EOF