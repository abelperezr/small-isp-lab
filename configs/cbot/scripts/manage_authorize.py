#!/usr/bin/env python3
"""Manage subscriber entries in the FreeRADIUS authorize file over SSH."""

from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


SEPARATOR_RE = re.compile(r"^#\s*=+\s*$")
REFERENCES_RE = re.compile(r"^#\s*References\b", re.IGNORECASE)
DEFAULT_LOCAL_FILE = Path("/app/scripts/authorize")
DEFAULT_REMOTE_FILE = "/etc/freeradius/mods-config/files/authorize"
DEFAULT_RADACCT_DIR = "/var/log/freeradius/radacct"
INDENT = " " * 20
DETAIL_ATTR_RE = re.compile(r'^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*=\s*(.+?)\s*$')
ACTIVE_ACCT_STATUSES = {"Start", "Interim-Update", "Alive"}


@dataclass
class SubscriberBlock:
    title: str
    identifier: str
    attrs: list[tuple[str, str]] = field(default_factory=list)

    def identifier_key(self) -> str:
        return normalize_identifier(self.identifier)

    def get_attr(self, key: str) -> str | None:
        key_lower = key.lower()
        for attr_key, attr_value in self.attrs:
            if attr_key.lower() == key_lower:
                return attr_value
        return None

    def set_attr(self, key: str, value: str) -> None:
        key_lower = key.lower()
        for index, (attr_key, _) in enumerate(self.attrs):
            if attr_key.lower() == key_lower:
                self.attrs[index] = (attr_key, value)
                return
        self.attrs.append((key, value))

    def del_attr(self, key: str) -> bool:
        key_lower = key.lower()
        for index, (attr_key, _) in enumerate(self.attrs):
            if attr_key.lower() == key_lower:
                del self.attrs[index]
                return True
        return False

    def render(self) -> list[str]:
        lines = [
            "# ============================================================================",
            f"# {self.title}",
            "# ============================================================================",
        ]
        if not self.attrs:
            raise ValueError(f"subscriber '{self.identifier}' has no attributes")

        first_key, first_value = self.attrs[0]
        if first_key == "Cleartext-Password":
            lines.append(f"{self.identifier:<20} {first_key} := {format_value(first_value)}")
        else:
            lines.append(f"{self.identifier:<20} {first_key} = {format_value(first_value)}")
        for index, (key, value) in enumerate(self.attrs[1:], start=1):
            suffix = "," if index < len(self.attrs) - 1 else ""
            lines.append(f"{INDENT}{key} = {format_value(value)}{suffix}")
        lines.append("")
        return lines


@dataclass
class SessionRecord:
    attrs: dict[str, str]
    timestamp: int

    def get(self, key: str) -> str | None:
        return self.attrs.get(key)

    def status(self) -> str:
        return self.attrs.get("Acct-Status-Type", "")

    def session_key(self) -> tuple[str, str]:
        return (
            self.attrs.get("NAS-IP-Address", ""),
            self.attrs.get("Acct-Session-Id", ""),
        )

    def is_active(self) -> bool:
        return self.status() in ACTIVE_ACCT_STATUSES


def normalize_identifier(value: str) -> str:
    return value.strip().strip('"').lower()


def format_identifier(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value
    if ":" in value and "@" not in value and " " not in value:
        return value.lower()
    return f'"{value}"'


def format_value(value: str) -> str:
    if value in {"Yes", "No", "yes", "no"}:
        return value
    if value.startswith('"') and value.endswith('"'):
        return value
    return f'"{value}"'


def parse_attr_line(line: str) -> tuple[str, str]:
    content = line.rstrip(",")
    if ":=" in content:
        key, value = content.split(":=", 1)
        return key.strip(), value.strip().strip('"')
    if "=" in content:
        key, value = content.split("=", 1)
        return key.strip(), value.strip().strip('"')
    raise ValueError(f"invalid attribute line: {line}")


def parse_blocks(managed_lines: list[str]) -> tuple[list[str], list[SubscriberBlock]]:
    preamble: list[str] = []
    blocks: list[SubscriberBlock] = []
    index = 0

    while index < len(managed_lines):
        line = managed_lines[index]
        if SEPARATOR_RE.match(line):
            break
        preamble.append(line)
        index += 1

    while index < len(managed_lines):
        if not SEPARATOR_RE.match(managed_lines[index]):
            index += 1
            continue
        if index + 2 >= len(managed_lines):
            break
        title_line = managed_lines[index + 1]
        if not title_line.startswith("# "):
            break
        if not SEPARATOR_RE.match(managed_lines[index + 2]):
            break

        title = title_line[2:].strip()
        index += 3
        entry_lines: list[str] = []
        while index < len(managed_lines) and managed_lines[index].strip() != "":
            entry_lines.append(managed_lines[index])
            index += 1
        while index < len(managed_lines) and managed_lines[index].strip() == "":
            index += 1
        if not entry_lines:
            continue

        first_parts = entry_lines[0].split(None, 1)
        if len(first_parts) != 2:
            raise ValueError(f"invalid first line in block '{title}': {entry_lines[0]}")
        block = SubscriberBlock(title=title, identifier=first_parts[0], attrs=[])
        first_attr_key, first_attr_value = parse_attr_line(first_parts[1])
        block.attrs.append((first_attr_key, first_attr_value))
        for raw_line in entry_lines[1:]:
            attr_key, attr_value = parse_attr_line(raw_line.strip())
            block.attrs.append((attr_key, attr_value))
        blocks.append(block)

    return preamble, blocks


def load_authorize(path: Path) -> tuple[list[str], list[SubscriberBlock], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    split_index = next((i for i, line in enumerate(lines) if REFERENCES_RE.match(line)), len(lines))
    managed_lines = lines[:split_index]
    tail_lines = lines[split_index:]
    preamble, blocks = parse_blocks(managed_lines)
    return preamble, blocks, tail_lines


def write_authorize(path: Path, preamble: list[str], blocks: list[SubscriberBlock], tail_lines: list[str], backup: bool) -> None:
    if backup:
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    output: list[str] = []
    output.extend(preamble)
    if output and output[-1] != "":
        output.append("")
    for block in blocks:
        output.extend(block.render())
    if tail_lines:
        output.extend(tail_lines)
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def strip_quotes(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def parse_session_records(text: str) -> list[SessionRecord]:
    records: list[SessionRecord] = []
    attrs: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if attrs:
                timestamp = int(attrs.get("Timestamp", "0") or "0")
                records.append(SessionRecord(attrs=dict(attrs), timestamp=timestamp))
                attrs.clear()
            continue
        match = DETAIL_ATTR_RE.match(line)
        if not match:
            continue
        key, raw_value = match.groups()
        attrs[key] = strip_quotes(raw_value)
    if attrs:
        timestamp = int(attrs.get("Timestamp", "0") or "0")
        records.append(SessionRecord(attrs=dict(attrs), timestamp=timestamp))
    return records


def read_local_radacct(radacct_dir: str) -> str:
    base = Path(radacct_dir)
    if not base.exists():
        raise RuntimeError(f"radacct directory not found: {base}")
    chunks: list[str] = []
    for path in sorted(base.rglob("detail-*")):
        chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def read_remote_radacct(args: argparse.Namespace) -> str:
    remote_command = (
        "find "
        + shlex.quote(args.radacct_dir)
        + " -type f -name 'detail-*' | sort | xargs -r cat"
    )
    result = run_remote(args, f"sudo sh -lc {shlex.quote(remote_command)}")
    return result.stdout


def load_session_records(args: argparse.Namespace) -> list[SessionRecord]:
    if args.local:
        return parse_session_records(read_local_radacct(args.radacct_dir))
    return parse_session_records(read_remote_radacct(args))


def identifier_candidates(block: SubscriberBlock | None, identifier: str) -> set[str]:
    candidates = {normalize_identifier(identifier)}
    if block is not None:
        candidates.add(block.identifier_key())
        for key in ("Alc-Client-Hardware-Addr", "User-Name", "Alc-Subsc-ID-Str"):
            value = block.get_attr(key)
            if value:
                candidates.add(normalize_identifier(value))
    return {value for value in candidates if value}


def record_matches_identifier(record: SessionRecord, candidates: set[str]) -> bool:
    for key in ("Alc-Client-Hardware-Addr", "Calling-Station-Id", "User-Name", "Alc-Subsc-ID-Str", "Acct-Session-Id"):
        value = record.get(key)
        if value and normalize_identifier(value) in candidates:
            return True
    return False


def candidate_groups(block: SubscriberBlock | None, identifier: str) -> set[str]:
    primary = {normalize_identifier(identifier)}

    if block is not None:
        block_identifier = block.identifier_key()
        if block_identifier:
            primary.add(block_identifier)

        for key in ("Alc-Client-Hardware-Addr", "User-Name", "Calling-Station-Id"):
            value = block.get_attr(key)
            if value:
                primary.add(normalize_identifier(value))

    return {value for value in primary if value}


def find_active_session(args: argparse.Namespace, identifier: str, block: SubscriberBlock | None = None) -> SessionRecord | None:
    primary_candidates = candidate_groups(block, identifier)
    primary_sessions: dict[tuple[str, str], SessionRecord] = {}
    for record in load_session_records(args):
        if record_matches_identifier(record, primary_candidates):
            primary_sessions[record.session_key()] = record

    active = [record for record in primary_sessions.values() if record.is_active()]
    if not active:
        return None
    active.sort(key=lambda record: record.timestamp, reverse=True)
    return active[0]


def build_disconnect_attributes(record: SessionRecord) -> list[tuple[str, str]]:
    attrs: list[tuple[str, str]] = []
    for key in (
        "User-Name",
        "Acct-Session-Id",
        "Acct-Multi-Session-Id",
        "NAS-IP-Address",
        "NAS-Port-Id",
        "Calling-Station-Id",
        "Alc-Client-Hardware-Addr",
        "Alc-Subsc-ID-Str",
    ):
        value = record.get(key)
        if value:
            attrs.append((key, value))
    return attrs


def render_disconnect_payload(record: SessionRecord) -> str:
    return "\n".join(f"{key} = {format_value(value)}" for key, value in build_disconnect_attributes(record)) + "\n"


def execute_disconnect(args: argparse.Namespace, record: SessionRecord) -> int:
    nas_ip = record.get("NAS-IP-Address")
    session_id = record.get("Acct-Session-Id")
    if not nas_ip or not session_id:
        print("Active session is missing NAS-IP-Address or Acct-Session-Id.", file=sys.stderr)
        return 1

    fields = {
        "nas_ip": nas_ip,
        "coa_port": args.coa_port,
        "disconnect_secret": args.disconnect_secret,
        "identifier": args.identifier,
        "user_name": record.get("User-Name") or "",
        "acct_session_id": session_id,
        "nas_port_id": record.get("NAS-Port-Id") or "",
        "acct_multi_session_id": record.get("Acct-Multi-Session-Id") or "",
    }
    command = args.disconnect_command.format(**fields)
    payload = render_disconnect_payload(record)

    if args.disconnect_via == "remote":
        remote_command = "sudo sh -lc " + shlex.quote(command)
        try:
            run_remote(args, remote_command, capture_output=False, input_text=payload)
        except subprocess.CalledProcessError as exc:
            print(f"Disconnect command failed on remote host: {exc}", file=sys.stderr)
            return 1
        print(f"Sent Disconnect-Request for session {session_id} to {nas_ip}:{args.coa_port}.")
        return 0

    try:
        subprocess.run(
            shlex.split(command),
            check=True,
            text=True,
            input=payload,
            capture_output=not args.disconnect_debug,
        )
    except FileNotFoundError:
        print(
            f"Disconnect command not found: {command}. "
            "Set --disconnect-command or use --disconnect-via remote.",
            file=sys.stderr,
        )
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Disconnect command failed: {exc}", file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr, end="" if exc.stderr.endswith("\n") else "\n")
        return 1

    print(f"Sent Disconnect-Request for session {session_id} to {nas_ip}:{args.coa_port}.")
    return 0


def maybe_run_disconnect(args: argparse.Namespace) -> int:
    if not getattr(args, "_disconnect_after", False):
        return 0
    record = find_active_session(args, args.identifier, getattr(args, "_disconnect_block", None))
    if record is None:
        print(f"No active accounting session found for '{args.identifier}'.")
        return 0
    return execute_disconnect(args, record)


def require_sshpass() -> None:
    if shutil.which("sshpass") is None:
        raise RuntimeError("sshpass is required for remote mode")


def run_remote(
    args: argparse.Namespace,
    remote_command: str,
    capture_output: bool = True,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    require_sshpass()
    command = [
        "sshpass",
        "-p",
        args.ssh_password,
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-p",
        str(args.ssh_port),
        f"{args.ssh_user}@{args.ssh_host}",
        remote_command,
    ]
    return subprocess.run(command, check=True, text=True, capture_output=capture_output, input=input_text)


def fetch_remote_authorize(args: argparse.Namespace) -> Path:
    result = run_remote(args, f"sudo cat {shlex.quote(args.file)}")
    temp = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
    try:
        temp.write(result.stdout)
        temp.flush()
    finally:
        temp.close()
    return Path(temp.name)


def push_remote_authorize(args: argparse.Namespace, local_path: Path, backup: bool, reload_radius: bool) -> None:
    require_sshpass()
    remote_tmp = f"/tmp/authorize.{os.getpid()}.tmp"
    upload_command = [
        "sshpass",
        "-p",
        args.ssh_password,
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-p",
        str(args.ssh_port),
        f"{args.ssh_user}@{args.ssh_host}",
        f"cat > {shlex.quote(remote_tmp)}",
    ]
    subprocess.run(
        upload_command,
        check=True,
        text=True,
        input=local_path.read_text(encoding="utf-8"),
        capture_output=True,
    )
    remote_file = str(args.remote_file)
    remote_steps: list[str] = []
    if backup:
        remote_steps.append(f"cp {shlex.quote(remote_file)} {shlex.quote(remote_file + '.bak')}")
    remote_steps.append(f"cat {shlex.quote(remote_tmp)} > {shlex.quote(remote_file)}")
    remote_steps.append(f"rm -f {shlex.quote(remote_tmp)}")
    if reload_radius:
        remote_steps.append("pkill -HUP -x freeradius || pkill -HUP -x radiusd")
    remote_command = "sudo sh -lc " + shlex.quote(" && ".join(remote_steps))
    try:
        run_remote(args, remote_command, capture_output=False)
    except Exception:
        run_remote(args, f"rm -f {shlex.quote(remote_tmp)}", capture_output=False)
        raise


def with_authorize_file(args: argparse.Namespace, handler) -> int:
    if not getattr(args, "needs_authorize", True):
        return handler(args)

    if args.local:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Authorize file not found: {file_path}", file=sys.stderr)
            return 1
        args.file = file_path
        result = handler(args)
        if result == 0:
            post_result = maybe_run_disconnect(args)
            if post_result != 0:
                return post_result
        return result

    temp_path = fetch_remote_authorize(args)
    original_file = args.file
    args.remote_file = original_file
    try:
        args.file = temp_path
        result = handler(args)
        if result == 0 and getattr(args, "mutates", False):
            push_remote_authorize(
                args,
                temp_path,
                backup=not args.no_backup,
                reload_radius=not args.no_reload,
            )
        if result == 0:
            post_result = maybe_run_disconnect(args)
            if post_result != 0:
                return post_result
        return result
    finally:
        args.file = original_file
        temp_path.unlink(missing_ok=True)


def find_block(blocks: list[SubscriberBlock], identifier: str) -> SubscriberBlock | None:
    key = normalize_identifier(identifier)
    for block in blocks:
        if block.identifier_key() == key:
            return block
    return None


def parse_key_value(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got '{value}'")
    key, raw_value = value.split("=", 1)
    key = key.strip()
    raw_value = raw_value.strip().strip('"')
    if not key:
        raise argparse.ArgumentTypeError(f"empty key in '{value}'")
    return key, raw_value


def canonical_attrs(args: argparse.Namespace) -> list[tuple[str, str]]:
    attrs: list[tuple[str, str]] = []
    if args.password:
        attrs.append(("Cleartext-Password", args.password))
    if args.framed_pool:
        attrs.append(("Framed-Pool", args.framed_pool))
    if args.framed_ipv6_pool:
        attrs.append(("Framed-IPv6-Pool", args.framed_ipv6_pool))
    if args.delegated_ipv6_pool:
        attrs.append(("Alc-Delegated-IPv6-Pool", args.delegated_ipv6_pool))
    if args.sla_profile:
        attrs.append(("Alc-SLA-Prof-str", args.sla_profile))
    if args.subscriber_profile:
        attrs.append(("Alc-Subsc-Prof-str", args.subscriber_profile))
    if args.subscriber_id:
        attrs.append(("Alc-Subsc-ID-Str", args.subscriber_id))
    if args.msap_interface:
        attrs.append(("Alc-MSAP-Interface", args.msap_interface))
    if args.fall_through is not None:
        attrs.append(("Fall-Through", args.fall_through))
    for item in args.attr or []:
        attrs.append(parse_key_value(item))
    return attrs


def cmd_list(args: argparse.Namespace) -> int:
    _, blocks, _ = load_authorize(args.file)
    if not blocks:
        print("No subscribers found.")
        return 0
    print(f"{'Identifier':<22} {'Title':<30} {'Interface':<12} {'Sub-ID'}")
    print(f"{'-' * 22} {'-' * 30} {'-' * 12} {'-' * 20}")
    for block in blocks:
        print(
            f"{block.identifier:<22} "
            f"{block.title:<30} "
            f"{(block.get_attr('Alc-MSAP-Interface') or '-'): <12} "
            f"{block.get_attr('Alc-Subsc-ID-Str') or '-'}"
        )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    _, blocks, _ = load_authorize(args.file)
    block = find_block(blocks, args.identifier)
    if not block:
        print(f"Subscriber '{args.identifier}' not found.", file=sys.stderr)
        return 1
    print("\n".join(block.render()).rstrip())
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    preamble, blocks, tail_lines = load_authorize(args.file)
    if find_block(blocks, args.identifier):
        print(f"Subscriber '{args.identifier}' already exists.", file=sys.stderr)
        return 1
    attrs = canonical_attrs(args)
    if not any(key == "Cleartext-Password" for key, _ in attrs):
        print("Missing required --password.", file=sys.stderr)
        return 1
    block = SubscriberBlock(title=args.title, identifier=format_identifier(args.identifier), attrs=attrs)
    blocks.append(block)
    write_authorize(args.file, preamble, blocks, tail_lines, backup=not args.no_backup)
    print(f"Added subscriber '{args.identifier}'.")
    return 0


def cmd_edit(args: argparse.Namespace) -> int:
    preamble, blocks, tail_lines = load_authorize(args.file)
    block = find_block(blocks, args.identifier)
    if not block:
        print(f"Subscriber '{args.identifier}' not found.", file=sys.stderr)
        return 1
    if args.title:
        block.title = args.title
    if args.new_identifier:
        block.identifier = format_identifier(args.new_identifier)
    field_updates = {
        "Cleartext-Password": args.password,
        "Framed-Pool": args.framed_pool,
        "Framed-IPv6-Pool": args.framed_ipv6_pool,
        "Alc-Delegated-IPv6-Pool": args.delegated_ipv6_pool,
        "Alc-SLA-Prof-str": args.sla_profile,
        "Alc-Subsc-Prof-str": args.subscriber_profile,
        "Alc-Subsc-ID-Str": args.subscriber_id,
        "Alc-MSAP-Interface": args.msap_interface,
        "Fall-Through": args.fall_through,
    }
    for key, value in field_updates.items():
        if value is not None:
            block.set_attr(key, value)
    for item in args.attr or []:
        key, value = parse_key_value(item)
        block.set_attr(key, value)
    for key in args.remove_attr or []:
        if key.lower() == "cleartext-password":
            print("Cannot remove Cleartext-Password.", file=sys.stderr)
            return 1
        block.del_attr(key)
    write_authorize(args.file, preamble, blocks, tail_lines, backup=not args.no_backup)
    print(f"Updated subscriber '{args.identifier}'.")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    preamble, blocks, tail_lines = load_authorize(args.file)
    block = find_block(blocks, args.identifier)
    if not block:
        print(f"Subscriber '{args.identifier}' not found.", file=sys.stderr)
        return 1
    blocks = [item for item in blocks if item.identifier_key() != block.identifier_key()]
    write_authorize(args.file, preamble, blocks, tail_lines, backup=not args.no_backup)
    print(f"Deleted subscriber '{args.identifier}'.")
    return 0


def cmd_disconnect(args: argparse.Namespace) -> int:
    record = find_active_session(args, args.identifier)
    if record is None:
        print(f"No active accounting session found for '{args.identifier}'.", file=sys.stderr)
        return 1
    return execute_disconnect(args, record)


def cmd_deactivate(args: argparse.Namespace) -> int:
    preamble, blocks, tail_lines = load_authorize(args.file)
    block = find_block(blocks, args.identifier)
    if not block:
        print(f"Subscriber '{args.identifier}' not found.", file=sys.stderr)
        return 1
    args._disconnect_after = True
    args._disconnect_block = block
    blocks = [item for item in blocks if item.identifier_key() != block.identifier_key()]
    write_authorize(args.file, preamble, blocks, tail_lines, backup=not args.no_backup)
    print(f"Deactivated subscriber '{args.identifier}'.")
    return 0


def add_common_subscriber_args(parser: argparse.ArgumentParser, require_title: bool, default_fall_through: str | None) -> None:
    if require_title:
        parser.add_argument("--title", required=True, help="Comment title for the subscriber block")
    else:
        parser.add_argument("--title", help="New comment title for the subscriber block")
    parser.add_argument("--password", help="Cleartext password")
    parser.add_argument("--framed-pool", help="Framed-Pool value")
    parser.add_argument("--framed-ipv6-pool", help="Framed-IPv6-Pool value")
    parser.add_argument("--delegated-ipv6-pool", help="Alc-Delegated-IPv6-Pool value")
    parser.add_argument("--sla-profile", help="Alc-SLA-Prof-str value")
    parser.add_argument("--subscriber-profile", help="Alc-Subsc-Prof-str value")
    parser.add_argument("--subscriber-id", help="Alc-Subsc-ID-Str value")
    parser.add_argument("--msap-interface", help="Alc-MSAP-Interface value")
    parser.add_argument("--fall-through", default=default_fall_through, help="Fall-Through value")
    parser.add_argument("--attr", action="append", help="Extra attribute in KEY=VALUE format")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage subscribers in FreeRADIUS authorize")
    parser.add_argument("--local", action="store_true", help="Operate on a local file instead of the remote radius node")
    parser.add_argument("--file", default=DEFAULT_REMOTE_FILE, help=f"Authorize path. Remote default: {DEFAULT_REMOTE_FILE}")
    parser.add_argument("--radacct-dir", default=DEFAULT_RADACCT_DIR, help=f"Accounting detail directory. Default: {DEFAULT_RADACCT_DIR}")
    parser.add_argument("--ssh-host", default="10.99.1.8", help="Radius SSH host")
    parser.add_argument("--ssh-port", type=int, default=22, help="Radius SSH port")
    parser.add_argument("--ssh-user", default="admin", help="Radius SSH user")
    parser.add_argument("--ssh-password", default="admin", help="Radius SSH password")
    parser.add_argument("--coa-port", type=int, default=3799, help="Disconnect/CoA destination port")
    parser.add_argument("--disconnect-secret", default="testlab123", help="Shared secret for Disconnect/CoA requests")
    parser.add_argument(
        "--disconnect-command",
        default="radclient -x {nas_ip}:{coa_port} disconnect {disconnect_secret}",
        help="Command template used to send Disconnect-Request",
    )
    parser.add_argument(
        "--disconnect-via",
        choices=("local", "remote"),
        default="remote",
        help="Execute the disconnect command locally or on the remote radius host",
    )
    parser.add_argument("--disconnect-debug", action="store_true", help="Do not capture disconnect command output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_list = subparsers.add_parser("list", help="List subscribers")
    parser_list.set_defaults(func=cmd_list)

    parser_show = subparsers.add_parser("show", help="Show one subscriber block")
    parser_show.add_argument("identifier", help="Subscriber identifier (MAC or username)")
    parser_show.set_defaults(func=cmd_show)

    parser_add = subparsers.add_parser("add", help="Add a subscriber")
    parser_add.add_argument("identifier", help="Subscriber identifier (MAC or username)")
    add_common_subscriber_args(parser_add, require_title=True, default_fall_through="Yes")
    parser_add.add_argument("--no-backup", action="store_true", help="Do not create authorize.bak")
    parser_add.add_argument("--no-reload", action="store_true", help="Do not reload radiusd after writing")
    parser_add.set_defaults(func=cmd_add, mutates=True)

    parser_edit = subparsers.add_parser("edit", help="Edit a subscriber")
    parser_edit.add_argument("identifier", help="Current subscriber identifier")
    parser_edit.add_argument("--new-identifier", help="New subscriber identifier")
    add_common_subscriber_args(parser_edit, require_title=False, default_fall_through=None)
    parser_edit.add_argument("--remove-attr", action="append", help="Remove attribute by key")
    parser_edit.add_argument("--no-backup", action="store_true", help="Do not create authorize.bak")
    parser_edit.add_argument("--no-reload", action="store_true", help="Do not reload radiusd after writing")
    parser_edit.set_defaults(func=cmd_edit, mutates=True)

    parser_delete = subparsers.add_parser("delete", help="Delete a subscriber")
    parser_delete.add_argument("identifier", help="Subscriber identifier (MAC or username)")
    parser_delete.add_argument("--no-backup", action="store_true", help="Do not create authorize.bak")
    parser_delete.add_argument("--no-reload", action="store_true", help="Do not reload radiusd after writing")
    parser_delete.set_defaults(func=cmd_delete, mutates=True)

    parser_disconnect = subparsers.add_parser("disconnect", help="Disconnect the latest active subscriber session")
    parser_disconnect.add_argument("identifier", help="Subscriber identifier (MAC, username, or subscriber ID)")
    parser_disconnect.set_defaults(func=cmd_disconnect, needs_authorize=False)

    parser_deactivate = subparsers.add_parser("deactivate", help="Delete a subscriber and disconnect the latest active session")
    parser_deactivate.add_argument("identifier", help="Subscriber identifier (MAC or username)")
    parser_deactivate.add_argument("--no-backup", action="store_true", help="Do not create authorize.bak")
    parser_deactivate.add_argument("--no-reload", action="store_true", help="Do not reload radiusd after writing")
    parser_deactivate.set_defaults(func=cmd_deactivate, mutates=True)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return with_authorize_file(args, args.func)


if __name__ == "__main__":
    raise SystemExit(main())
