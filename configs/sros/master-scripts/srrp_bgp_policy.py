#!/usr/bin/env python3
"""
EHS SRRP BGP Policy Script 
"""
from time import sleep
from pysros.management import connect
from pysros.ehs import get_event

VPRN_SERVICE = "9998"
VPRN_BGP = "9999"
NEIGHBORS = ["172.16.1.1", "172.16.2.1"]
NEIGHBOR_POLICIES = {
    "172.16.1.1": {"master": "public_to_ISP_C1_Master", "backup": "public_to_ISP_C1_Backup"},
    "172.16.2.1": {"master": "public_to_ISP_C2_Master", "backup": "public_to_ISP_C2_Backup"},
}
SRRP_INSTANCES = [("ipv6-only", "1"), ("dual-stack", "2"), ("vip", "3")]
ROLE_RETRIES = 60
APPLY_RETRIES = 6
SLEEP_SEC = 1


def log(msg):
    print(str(msg))


def get_srrp_states(conn):
    states = {}
    for gi_name, srrp_id in SRRP_INSTANCES:
        path = (
            '/nokia-state:state/service/vprn[service-name="{}"]'
            '/subscriber-interface[interface-name="services"]'
            '/group-interface[group-interface-name="{}"]'
            '/srrp[srrp-id={}]'
        ).format(VPRN_SERVICE, gi_name, srrp_id)
        key = gi_name + "/srrp-" + srrp_id
        try:
            data = conn.running.get(path)
            oper_raw = data.get("oper-state")
            if oper_raw is not None and hasattr(oper_raw, "data"):
                oper_str = str(oper_raw.data).lower()
            elif oper_raw is not None:
                oper_str = str(oper_raw).lower()
            else:
                oper_str = "unknown"
            states[key] = oper_str
        except Exception as exc:
            states[key] = "error: " + str(exc).lower()
    return states


def classify_role_from_states(states):
    vals = list(states.values())
    if any(v.startswith("error:") for v in vals):
        return "unknown"
    if all("master" in v for v in vals):
        return "master"
    if all(("backup" in v or "shunt" in v) for v in vals):
        return "backup"
    return "transient"


def get_current_exports(conn):
    current = {}
    for neighbor in NEIGHBORS:
        path = (
            '/nokia-conf:configure/service/vprn[service-name="{}"]/bgp/'
            'neighbor[ip-address="{}"]'
        ).format(VPRN_BGP, neighbor)
        try:
            data = conn.running.get(path)
            export_node = data.get("export")
            if export_node is not None:
                pol = export_node.get("policy")
                if pol is not None:
                    if hasattr(pol, "data"):
                        current[neighbor] = [str(p) for p in pol.data]
                    elif isinstance(pol, (list, tuple)):
                        current[neighbor] = [str(p) for p in pol]
                    else:
                        current[neighbor] = [str(pol)]
                else:
                    current[neighbor] = []
            else:
                current[neighbor] = []
        except Exception:
            current[neighbor] = []
    return current


def apply_exports(conn, target_policies):
    """Delete the entire 'export' container, then set it fresh."""
    for neighbor in NEIGHBORS:
        base = (
            '/nokia-conf:configure/service/vprn[service-name="{}"]/bgp/'
            'neighbor[ip-address="{}"]'
        ).format(VPRN_BGP, neighbor)

        policy_name = target_policies[neighbor]
        log("  [WRITE] " + neighbor + " -> " + policy_name)


        export_path = base + "/export"
        try:
            conn.candidate.delete(export_path)
            log("    [DELETE export] OK")
        except Exception as de:
            log("    [DELETE export] FAILED: " + str(de))


        payload = {"export": {"policy": [policy_name]}}
        try:
            conn.candidate.set(base, payload)
            log("    [SET] OK")
        except Exception as se:
            log("    [SET] FAILED: " + str(se))
            raise

    log("  [COMMIT]...")
    conn.candidate.commit()
    log("  [COMMIT] OK")


def exports_match(current, target):
    return all(current.get(n, []) == [target[n]] for n in NEIGHBORS)


def main():
    conn = connect()
    ev = get_event()
    ev_name = str(ev.name) if ev else "manual"
    ev_text = str(ev.text) if ev else "no event"

    log("=" * 70)
    log("EHS SRRP BGP Policy Script v10 (MASTER)")
    log("=" * 70)
    log("Trigger : " + ev_name)
    log("Text    : " + ev_text)

    role = "unknown"
    last_states = {}
    for attempt in range(1, ROLE_RETRIES + 1):
        last_states = get_srrp_states(conn)
        role = classify_role_from_states(last_states)
        if role in ("master", "backup"):
            log("Role    : " + role.upper() + " (attempt " + str(attempt) + ")")
            break
        sleep(SLEEP_SEC)

    log("States  : " + str(last_states))

    if role not in ("master", "backup"):
        log("RESULT  : FAILED - role did not stabilize")
        log("=" * 70)
        return

    target = {}
    for n in NEIGHBORS:
        target[n] = NEIGHBOR_POLICIES[n][role]
    current = get_current_exports(conn)

    log("Current : " + str(current))
    log("Target  : " + str(target))

    if exports_match(current, target):
        log("RESULT  : SUCCESS (no change needed)")
        log("=" * 70)
        return

    last_err = None
    for attempt in range(1, APPLY_RETRIES + 1):
        log("ATTEMPT : " + str(attempt) + "/" + str(APPLY_RETRIES))
        try:
            apply_exports(conn, target)
        except Exception as exc:
            last_err = str(exc)
            log("  ERROR : " + last_err)
            sleep(SLEEP_SEC)
            continue

        verify = get_current_exports(conn)
        if exports_match(verify, target):
            log("RESULT  : SUCCESS")
            log("=" * 70)
            return

        last_err = "post-check: " + str(verify)
        log("  VERIFY FAILED: " + last_err)
        sleep(SLEEP_SEC)

    log("RESULT  : FAILED - " + str(last_err))
    log("=" * 70)


if __name__ == "__main__":
    main()
