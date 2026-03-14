#!/usr/bin/env python3
"""Enable or disable an SR OS port via gNMI and verify the applied state."""
import argparse
import os
import sys

from pygnmi.client import gNMIclient


def _extract_port_values(result: dict) -> dict | None:
    notifications = result.get("notification", [])
    for notification in notifications:
        for update in notification.get("update", []):
            values = update.get("val", {})
            if isinstance(values, dict) and "admin-state" in values:
                return values
    return None


def main():
    p = argparse.ArgumentParser(description="Enable/disable SR OS port via gNMI")
    p.add_argument("--host", required=True, help="SR OS management IP")
    p.add_argument("--state", choices=["enable", "disable"], default="disable")
    p.add_argument("--port-id", default="1/1/c1/1", help="Port ID (e.g. 1/1/c1/1)")
    p.add_argument("--user", default=os.getenv("SROS_USERNAME", "admin"))
    p.add_argument("--password", default=os.getenv("SROS_PASSWORD", "lab123"))
    p.add_argument("--gnmi-port", type=int, default=57400)
    args = p.parse_args()

    path = f"/configure/port[port-id={args.port_id}]"
    update_value = {
        "port-id": args.port_id,
        "admin-state": args.state,
    }

    try:
        with gNMIclient(
            target=(args.host, args.gnmi_port),
            username=args.user,
            password=args.password,
            insecure=True,
        ) as gc:
            gc.set(update=[(path, update_value)])
            result = gc.get(path=[path], datatype="all")

        port_values = _extract_port_values(result)
        if not port_values:
            print(
                f"ERROR: no gNMI data returned for port {args.port_id} on {args.host}",
                file=sys.stderr,
            )
            return 1

        actual_admin = port_values.get("admin-state")
        actual_oper = port_values.get("oper-state")
        if actual_admin != args.state:
            print(
                f"ERROR: admin-state is '{actual_admin}' instead of '{args.state}' "
                f"for port {args.port_id} on {args.host}",
                file=sys.stderr,
            )
            return 1

        suffix = f", oper-state={actual_oper}" if actual_oper else ""
        print(
            f"OK: port {args.port_id} admin-state={actual_admin} on {args.host}{suffix}"
        )
        return 0
    except Exception as exc:
        print(
            f"ERROR: failed to update port {args.port_id} on {args.host}: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
