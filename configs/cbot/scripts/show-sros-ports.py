#!/usr/bin/env python3
"""Show SR OS port admin and oper state via NETCONF using scrapli."""
import argparse
import os
import sys
import xml.etree.ElementTree as ET

from scrapli_netconf.driver import NetconfDriver


NS_CONF = "urn:nokia.com:sros:ns:yang:sr:conf"
NS_STATE = "urn:nokia.com:sros:ns:yang:sr:state"
NS_NC = "urn:ietf:params:xml:ns:netconf:base:1.0"


def _rpc_ok(response) -> None:
    if "<rpc-error>" in response.result:
        raise RuntimeError(response.result)


def _find_data_root(xml_text: str):
    root = ET.fromstring(xml_text)
    return root.find(f".//{{{NS_NC}}}data")


def _parse_config_ports(xml_text: str) -> dict[str, dict[str, str]]:
    ports: dict[str, dict[str, str]] = {}
    data = _find_data_root(xml_text)
    if data is None:
        return ports

    for port in data.findall(f".//{{{NS_CONF}}}port"):
        port_id = port.findtext(f"{{{NS_CONF}}}port-id")
        if not port_id:
            continue
        ports.setdefault(port_id, {})
        admin_state = port.findtext(f"{{{NS_CONF}}}admin-state")
        if admin_state:
            ports[port_id]["admin-state"] = admin_state
    return ports


def _parse_state_ports(xml_text: str) -> dict[str, dict[str, str]]:
    ports: dict[str, dict[str, str]] = {}
    data = _find_data_root(xml_text)
    if data is None:
        return ports

    for port in data.findall(f".//{{{NS_STATE}}}port"):
        port_id = port.findtext(f"{{{NS_STATE}}}port-id")
        if not port_id:
            continue
        ports.setdefault(port_id, {})
        oper_state = port.findtext(f"{{{NS_STATE}}}oper-state")
        if oper_state:
            ports[port_id]["oper-state"] = oper_state
    return ports


def _make_filter(namespace: str, port_id: str | None, leaf_name: str) -> str:
    port_id_xml = f"<port-id>{port_id}</port-id>" if port_id else ""
    top = "configure" if namespace == NS_CONF else "state"
    return f"""
<filter type="subtree">
  <{top} xmlns="{namespace}">
    <port>
      {port_id_xml}
      <{leaf_name}/>
    </port>
  </{top}>
</filter>
""".strip()


def main():
    p = argparse.ArgumentParser(description="Show SR OS port admin/oper state")
    p.add_argument("--host", required=True)
    p.add_argument("--port-id", help="Optional single port to inspect")
    p.add_argument("--user", default=os.getenv("SROS_USERNAME", "admin"))
    p.add_argument("--password", default=os.getenv("SROS_PASSWORD", "lab123"))
    p.add_argument("--netconf-port", type=int, default=830)
    args = p.parse_args()

    conn = None
    try:
        conn = NetconfDriver(
            host=args.host,
            port=args.netconf_port,
            auth_username=args.user,
            auth_password=args.password,
            auth_strict_key=False,
            transport="paramiko",
        )
        conn.open()

        config_reply = conn.get_config(
            source="running",
            filter_=_make_filter(NS_CONF, args.port_id, "admin-state"),
        )
        _rpc_ok(config_reply)

        state_reply = conn.get(
            filter_=_make_filter(NS_STATE, args.port_id, "oper-state"),
        )
        _rpc_ok(state_reply)

        ports = _parse_config_ports(config_reply.result)
        state_ports = _parse_state_ports(state_reply.result)

        for port_id, values in state_ports.items():
            ports.setdefault(port_id, {}).update(values)

        if not ports:
            target = args.port_id or "any ports"
            print(f"No data returned for {target} on {args.host}")
            return 1

        print(f"{'Port ID':<20} {'Admin':<10} {'Oper':<10}")
        print("-" * 42)
        for port_id in sorted(ports):
            admin_state = ports[port_id].get("admin-state", "?")
            oper_state = ports[port_id].get("oper-state", "?")
            print(f"{port_id:<20} {admin_state:<10} {oper_state:<10}")
        return 0
    except Exception as exc:
        print(f"ERROR: failed to query ports on {args.host}: {exc}", file=sys.stderr)
        return 1
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
