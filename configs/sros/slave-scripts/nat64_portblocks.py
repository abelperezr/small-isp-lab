#!/usr/bin/env python3
"""
NAT Subscriber Port-Block Report v3
────────────────────────────────────
Reads active NAT64 and NAT44 subscriber port-block allocations.

Field names discovered from SR OS 25.10.r2 state tree:
  port-block key: (outside-router-instance, outside-ip-address, start)
  port-block fields: start, end, outside-router-instance, outside-ip-address

Output: cf3:\scripts\nat_report.csv + console table

Usage:
    pyexec "cf3:\scripts\nat64_portblocks.py"
"""
from pysros.management import connect

INSIDE_ROUTER = "9998"
OUTPUT_FILE = "cf3:\\scripts\\nat_report.csv"


def log(msg):
    print(str(msg))


def safe_str(val):
    if val is None:
        return ""
    if hasattr(val, "data"):
        return str(val.data)
    return str(val)


def get_field(obj, field):
    try:
        return safe_str(obj.get(field))
    except Exception:
        return ""


def extract_subscribers(conn, nat_type, path):
    """Generic extractor for NAT64 or NAT44 subscribers."""
    rows = []
    try:
        data = conn.running.get(path)
    except Exception as e:
        log("  Query failed: " + str(e))
        return rows

    if not hasattr(data, "keys"):
        log("  No subscribers found")
        return rows

    sub_keys = list(data.keys())
    log("  Found " + str(len(sub_keys)) + " subscriber(s)")

    for sk in sub_keys:
        sub = data[sk]

        sub_name = get_field(sub, "name")
        sub_id = get_field(sub, "id")
        inside = get_field(sub, "inside-ip-prefix")
        if not inside:
            inside = get_field(sub, "inside-ip-address")
        policy = get_field(sub, "nat-policy")
        sub_type_val = get_field(sub, "type")

        # Extract port-blocks
        try:
            pbs = sub.get("port-block")
            if pbs is not None and hasattr(pbs, "keys"):
                for pbk in pbs.keys():
                    pb = pbs[pbk]
                    outside_ip = get_field(pb, "outside-ip-address")
                    port_start = get_field(pb, "start")
                    port_end = get_field(pb, "end")
                    outside_ri = get_field(pb, "outside-router-instance")

                    total = ""
                    try:
                        total = str(int(port_end) - int(port_start) + 1)
                    except Exception:
                        pass

                    rows.append({
                        "type": nat_type,
                        "subscriber": sub_name,
                        "sub_id": sub_id,
                        "inside_prefix": inside,
                        "outside_ip": outside_ip,
                        "port_start": port_start,
                        "port_end": port_end,
                        "total_ports": total,
                        "nat_policy": policy,
                        "outside_vrf": outside_ri,
                        "sessions": "",
                    })
            else:
                # No port-blocks
                rows.append({
                    "type": nat_type,
                    "subscriber": sub_name,
                    "sub_id": sub_id,
                    "inside_prefix": inside,
                    "outside_ip": "",
                    "port_start": "",
                    "port_end": "",
                    "total_ports": "",
                    "nat_policy": policy,
                    "outside_vrf": "",
                    "sessions": "",
                })
        except Exception as e:
            log("  port-block error for " + sub_name + ": " + str(e))

        # Try to get active session count from statistics
        try:
            stats = sub.get("statistics")
            if stats is not None:
                sessions_container = stats.get("sessions")
                if sessions_container is not None:
                    active = get_field(sessions_container, "active")
                    peak = get_field(sessions_container, "peak")
                    if rows and rows[-1]["sub_id"] == sub_id:
                        rows[-1]["sessions"] = active + "/" + peak if peak else active
        except Exception:
            pass

    return rows


def print_table(rows):
    """Print a formatted console table."""
    if not rows:
        return

    log("")
    log("=" * 120)
    # Header
    fmt = "{:<6} {:<32} {:<22} {:<18} {:<7} {:<7} {:<7} {:<10} {:<8}"
    log(fmt.format("TYPE", "SUBSCRIBER", "INSIDE PREFIX", "OUTSIDE IP", "START", "END", "PORTS", "POLICY", "SESS"))
    log("-" * 120)

    for r in rows:
        log(fmt.format(
            r.get("type", ""),
            r.get("subscriber", "")[:32],
            r.get("inside_prefix", "")[:22],
            r.get("outside_ip", "")[:18],
            r.get("port_start", ""),
            r.get("port_end", ""),
            r.get("total_ports", ""),
            r.get("nat_policy", "")[:10],
            r.get("sessions", ""),
        ))
    log("=" * 120)


def write_csv(rows, filename):
    cols = ["type", "subscriber", "sub_id", "inside_prefix", "outside_ip",
            "port_start", "port_end", "total_ports", "nat_policy", "outside_vrf", "sessions"]
    header = ",".join(cols)
    lines = [header]
    for r in rows:
        line = ",".join([str(r.get(c, "")) for c in cols])
        lines.append(line)
    csv_text = "\n".join(lines) + "\n"
    try:
        with open(filename, "w") as f:
            f.write(csv_text)
        log("CSV written to: " + filename)
    except Exception as e:
        log("CSV write error: " + str(e))


def main():
    log("=" * 70)
    log("NAT Subscriber Port-Block Report v3")
    log("=" * 70)

    conn = connect()

    all_rows = []

    # NAT64
    log("")
    log("[NAT64] Querying...")
    nat64_path = (
        '/nokia-state:state/service/vprn[service-name="'
        + INSIDE_ROUTER
        + '"]/nat/inside/large-scale/nat64/subscriber'
    )
    nat64_rows = extract_subscribers(conn, "NAT64", nat64_path)
    all_rows.extend(nat64_rows)
    log("  Entries: " + str(len(nat64_rows)))

    # NAT44
    log("")
    log("[NAT44] Querying...")
    nat44_path = (
        '/nokia-state:state/service/vprn[service-name="'
        + INSIDE_ROUTER
        + '"]/nat/inside/large-scale/nat44/subscriber'
    )
    nat44_rows = extract_subscribers(conn, "NAT44", nat44_path)
    all_rows.extend(nat44_rows)
    log("  Entries: " + str(len(nat44_rows)))

    # Print table
    print_table(all_rows)

    # Summary
    log("")
    nat64_count = len([r for r in all_rows if r["type"] == "NAT64"])
    cgnat_count = len([r for r in all_rows if r["nat_policy"] == "natpol"])
    vip_count = len([r for r in all_rows if r["nat_policy"] == "natvip"])
    log("Summary: " + str(nat64_count) + " NAT64, "
        + str(cgnat_count) + " CGNAT, "
        + str(vip_count) + " VIP, "
        + str(len(all_rows)) + " total")

    # Write CSV
    log("")
    write_csv(all_rows, OUTPUT_FILE)

    log("")
    log("DONE")


if __name__ == "__main__":
    main()
