"""
bot.py - Containerbot for Network Labs
=====================================================
A lightweight Telegram bot that discovers and executes .sh, .py, and
Ansible playbook scripts from a configurable directory.  Scripts are
presented to the user as an interactive menu with inline-keyboard buttons.

Architecture
------------
scripts/           <-- Drop .sh / .py files here (auto-discovered)
ansible/playbooks/ <-- Drop .yml playbooks here (auto-discovered)
config.yaml        <-- Bot settings, RBAC, script metadata overrides

The bot builds its menu dynamically at startup (and on /reload).
Each script gets a friendly name, description, and category derived from
the filename or overridden in config.yaml.

Environment variables
---------------------
TELEGRAM_BOT_TOKEN   (required) Bot token from @BotFather
SCRIPTS_DIR          Path to scripts directory       (default: ./scripts)
ANSIBLE_DIR          Path to ansible directory        (default: ./ansible)
CONFIG_FILE          Path to config.yaml              (default: ./config.yaml)
ALLOWED_ADMINS       Comma-separated Telegram user IDs for admin role
ALLOWED_USERS        Comma-separated Telegram user IDs for operator role
LOG_LEVEL            Python log level                 (default: INFO)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Clean proxy env vars that containerlab may inject (breaks httpx/telegram)
# ---------------------------------------------------------------------------
import os

for _pv in (
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
    "http_proxy", "https_proxy", "all_proxy", "no_proxy",
):
    if _pv in os.environ:
        val = os.environ[_pv]
        if ":" in val and not val.startswith("http"):
            del os.environ[_pv]

import asyncio
import hashlib
import logging
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
)
log = logging.getLogger("containerbot")

# ---------------------------------------------------------------------------
# Constants / paths
# ---------------------------------------------------------------------------
BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
SCRIPTS_DIR: str = os.getenv("SCRIPTS_DIR", "/app/scripts")
ANSIBLE_DIR: str = os.getenv("ANSIBLE_DIR", "/app/ansible")
CONFIG_FILE: str = os.getenv("CONFIG_FILE", "/app/config.yaml")

DEFAULT_MAX_MSG_LEN = 4000  # Telegram message size safety limit
DEFAULT_EXEC_TIMEOUT = 120  # Default script execution timeout (seconds)

# Supported script extensions
SCRIPT_EXTENSIONS = {".sh", ".py"}


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean-like environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


ENABLE_SCRIPT_UPLOAD = _env_bool("ENABLE_SCRIPT_UPLOAD", default=False)


def _coerce_int_setting(value: object, default: int, setting_name: str, minimum: int) -> int:
    """Return a validated integer setting or a safe default."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        log.warning("Invalid %s value %r, using default %d", setting_name, value, default)
        return default
    if parsed < minimum:
        log.warning("%s must be >= %d, using default %d", setting_name, minimum, default)
        return default
    return parsed

# ---------------------------------------------------------------------------
# RBAC helpers
# ---------------------------------------------------------------------------
def _parse_ids(env_var: str) -> set[int]:
    """Parse comma-separated Telegram user IDs from an env var."""
    out: set[int] = set()
    for tok in os.getenv(env_var, "").split(","):
        tok = tok.strip()
        if tok.isdigit():
            out.add(int(tok))
    return out


def _user_is_allowed(user_id: int) -> bool:
    """Return True if user_id is authorized (admin or operator)."""
    admins = _parse_ids("ALLOWED_ADMINS")
    users = _parse_ids("ALLOWED_USERS")
    # If no lists are configured at all -> dev mode, allow everyone
    if not admins and not users:
        return True
    return user_id in admins or user_id in users


def _user_is_admin(user_id: int) -> bool:
    admins = _parse_ids("ALLOWED_ADMINS")
    if not admins and not _parse_ids("ALLOWED_USERS"):
        return True  # dev mode
    return user_id in admins


# ---------------------------------------------------------------------------
# Script descriptor
# ---------------------------------------------------------------------------
@dataclass
class ScriptEntry:
    """Represents a single executable script in the menu."""
    file: Path                    # Absolute path to the script
    name: str = ""                # Friendly display name
    description: str = ""         # One-line description
    category: str = "General"     # Menu category / group
    admin_only: bool = False      # Restrict to admins
    confirm: bool = False         # Ask confirmation before running
    timeout: int = DEFAULT_EXEC_TIMEOUT   # Per-script timeout override
    args_prompt: str = ""         # If set, ask user for args before running
    hidden: bool = False          # Hide from menu


@dataclass
class AnsibleEntry:
    """Represents an Ansible playbook."""
    file: Path
    name: str = ""
    description: str = ""
    category: str = "Ansible"
    admin_only: bool = False
    confirm: bool = True
    timeout: int = 180
    hidden: bool = False


# ---------------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------------
@dataclass
class BotConfig:
    """Global bot configuration loaded from config.yaml."""
    scripts: list[ScriptEntry] = field(default_factory=list)
    playbooks: list[AnsibleEntry] = field(default_factory=list)
    ansible_inventory: str = ""
    default_timeout: int = DEFAULT_EXEC_TIMEOUT
    max_message_length: int = DEFAULT_MAX_MSG_LEN
    raw: dict = field(default_factory=dict)


def _slug(path: Path) -> str:
    """Convert filename to a readable name: 'olt-to-bng1-down.sh' -> 'Olt To Bng1 Down'."""
    stem = path.stem
    return stem.replace("-", " ").replace("_", " ").title()


def _discover_scripts(
    directory: str,
    overrides: dict[str, dict],
    default_timeout: int,
) -> list[ScriptEntry]:
    """Walk the scripts directory and return ScriptEntry objects."""
    scripts_path = Path(directory)
    if not scripts_path.is_dir():
        log.warning("Scripts directory not found: %s", directory)
        return []

    entries: list[ScriptEntry] = []
    for f in sorted(scripts_path.rglob("*")):
        if f.suffix not in SCRIPT_EXTENSIONS:
            continue
        if not f.is_file():
            continue

        # Relative key for config overrides (e.g. "olt-to-bng1-down.sh")
        rel = str(f.relative_to(scripts_path))
        ov = overrides.get(rel, overrides.get(f.name, {}))

        entry = ScriptEntry(
            file=f,
            name=ov.get("name", _slug(f)),
            description=ov.get("description", ""),
            category=ov.get("category", _category_from_path(f, scripts_path)),
            admin_only=ov.get("admin_only", False),
            confirm=ov.get("confirm", False),
            timeout=ov.get("timeout", default_timeout),
            args_prompt=ov.get("args_prompt", ""),
            hidden=ov.get("hidden", False),
        )
        entries.append(entry)
    return entries


def _category_from_path(f: Path, base: Path) -> str:
    """Derive category from subdirectory name, or 'General'."""
    rel = f.relative_to(base)
    if len(rel.parts) > 1:
        return rel.parts[0].replace("-", " ").replace("_", " ").title()
    return "General"


def _discover_playbooks(
    directory: str,
    overrides: dict[str, dict],
    default_timeout: int,
) -> list[AnsibleEntry]:
    """Walk ansible/playbooks/ for .yml/.yaml files."""
    pb_dir = Path(directory) / "playbooks"
    if not pb_dir.is_dir():
        log.warning("Ansible playbooks directory not found: %s", pb_dir)
        return []

    entries: list[AnsibleEntry] = []
    for f in sorted(pb_dir.rglob("*.y*ml")):
        if not f.is_file():
            continue
        rel = f.name
        ov = overrides.get(rel, {})
        entries.append(AnsibleEntry(
            file=f,
            name=ov.get("name", _slug(f)),
            description=ov.get("description", ""),
            category=ov.get("category", "Ansible"),
            admin_only=ov.get("admin_only", False),
            confirm=ov.get("confirm", True),
            timeout=ov.get("timeout", default_timeout),
            hidden=ov.get("hidden", False),
        ))
    return entries


def load_config() -> BotConfig:
    """Load config.yaml and discover scripts + playbooks."""
    raw: dict = {}
    cfg_path = Path(CONFIG_FILE)
    if cfg_path.is_file():
        try:
            raw = yaml.safe_load(cfg_path.read_text()) or {}
        except Exception as exc:
            log.error("Failed to parse %s: %s", CONFIG_FILE, exc)

    script_overrides: dict[str, dict] = raw.get("scripts", {}) or {}
    playbook_overrides: dict[str, dict] = raw.get("playbooks", {}) or {}
    bot_settings: dict[str, int] = raw.get("bot", {}) or {}

    default_timeout = _coerce_int_setting(
        bot_settings.get("default_timeout", DEFAULT_EXEC_TIMEOUT),
        DEFAULT_EXEC_TIMEOUT,
        "bot.default_timeout",
        minimum=1,
    )
    max_message_length = _coerce_int_setting(
        bot_settings.get("max_message_length", DEFAULT_MAX_MSG_LEN),
        DEFAULT_MAX_MSG_LEN,
        "bot.max_message_length",
        minimum=200,
    )

    scripts = _discover_scripts(SCRIPTS_DIR, script_overrides, default_timeout)
    playbooks = _discover_playbooks(ANSIBLE_DIR, playbook_overrides, default_timeout)

    inv_file = raw.get("ansible", {}).get("inventory", "")
    if not inv_file:
        default_inv = Path(ANSIBLE_DIR) / "inventory" / "hosts.yml"
        if default_inv.is_file():
            inv_file = str(default_inv)

    log.info("Loaded %d scripts, %d playbooks", len(scripts), len(playbooks))
    return BotConfig(
        scripts=scripts,
        playbooks=playbooks,
        ansible_inventory=inv_file,
        default_timeout=default_timeout,
        max_message_length=max_message_length,
        raw=raw,
    )


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_config: BotConfig = BotConfig()

# Pending args: (chat_id, user_id) -> (script_token, prompt_text)
_pending_args: dict[tuple[int, int], tuple[str, str]] = {}


def get_config() -> BotConfig:
    return _config


# ---------------------------------------------------------------------------
# Script execution
# ---------------------------------------------------------------------------
def _parse_shell_args(raw_args: str) -> list[str]:
    """Parse shell-like arguments preserving quoted segments."""
    if not raw_args.strip():
        return []
    return shlex.split(raw_args)


def _entry_token(kind: str, relative_path: str) -> str:
    """Build a short stable token for callback payloads."""
    payload = f"{kind}:{relative_path}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def _script_relative_path(path: Path) -> str:
    return str(path.relative_to(Path(SCRIPTS_DIR)))


def _playbook_relative_path(path: Path) -> str:
    return str(path.relative_to(Path(ANSIBLE_DIR) / "playbooks"))


def _script_token(entry: ScriptEntry) -> str:
    return _entry_token("script", _script_relative_path(entry.file))


def _playbook_token(entry: AnsibleEntry) -> str:
    return _entry_token("playbook", _playbook_relative_path(entry.file))


def _category_token(category: str) -> str:
    return _entry_token("category", category)


def _find_script_by_token(cfg: BotConfig, token: str) -> ScriptEntry | None:
    for entry in cfg.scripts:
        if _script_token(entry) == token:
            return entry
    return None


def _find_playbook_by_token(cfg: BotConfig, token: str) -> AnsibleEntry | None:
    for entry in cfg.playbooks:
        if _playbook_token(entry) == token:
            return entry
    return None


def _find_category_by_token(cfg: BotConfig, token: str, user_id: int) -> str | None:
    is_admin = _user_is_admin(user_id)
    categories: set[str] = set()

    for entry in cfg.scripts:
        if entry.hidden or (entry.admin_only and not is_admin):
            continue
        categories.add(entry.category)

    for entry in cfg.playbooks:
        if entry.hidden or (entry.admin_only and not is_admin):
            continue
        categories.add(entry.category)

    for category in categories:
        if _category_token(category) == token:
            return category
    return None


def _find_scripts_by_name_or_path(cfg: BotConfig, filename: str) -> list[ScriptEntry]:
    target = filename.strip().lstrip("./")
    matches: list[ScriptEntry] = []
    for entry in cfg.scripts:
        rel = _script_relative_path(entry.file)
        if entry.file.name == target or rel == target:
            matches.append(entry)
    return matches


def _find_playbooks_by_name_or_path(cfg: BotConfig, filename: str) -> list[AnsibleEntry]:
    target = filename.strip().lstrip("./")
    matches: list[AnsibleEntry] = []
    for entry in cfg.playbooks:
        rel = _playbook_relative_path(entry.file)
        if entry.file.name == target or rel == target:
            matches.append(entry)
    return matches


def _uploaded_script_destination(file_name: str) -> Path:
    """Return a safe destination path for an uploaded script."""
    if not file_name or file_name in {".", ".."}:
        raise ValueError("empty filename")
    if "\\" in file_name:
        raise ValueError("backslashes are not allowed")

    raw_path = Path(file_name)
    if raw_path.is_absolute():
        raise ValueError("absolute paths are not allowed")
    if any(part in {"", ".", ".."} for part in raw_path.parts):
        raise ValueError("path traversal is not allowed")

    scripts_root = Path(SCRIPTS_DIR).resolve()
    dest = (scripts_root / raw_path).resolve()
    try:
        dest.relative_to(scripts_root)
    except ValueError as exc:
        raise ValueError("destination escapes scripts directory") from exc
    return dest


async def run_script(entry: ScriptEntry, extra_args: list[str] | None = None) -> tuple[int, str, float]:
    """
    Execute a script and return (return_code, combined_output, elapsed_seconds).

    - .sh scripts are run with bash
    - .py scripts are run with python3
    """
    path = entry.file
    if path.suffix == ".sh":
        cmd = ["bash", str(path)]
    elif path.suffix == ".py":
        cmd = ["python3", str(path)]
    else:
        cmd = [str(path)]

    # Append extra arguments if provided
    if extra_args:
        cmd.extend(extra_args)

    log.info(
        "Executing script=%s argc=%d timeout=%ds",
        entry.file.name,
        len(extra_args or []),
        entry.timeout,
    )
    t0 = time.monotonic()

    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=entry.timeout,
            cwd=str(path.parent),
        )
        elapsed = time.monotonic() - t0
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, output, elapsed

    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - t0
        return -1, f"TIMEOUT after {entry.timeout}s", elapsed
    except Exception as exc:
        elapsed = time.monotonic() - t0
        return -1, f"ERROR: {exc}", elapsed


async def run_playbook(entry: AnsibleEntry, inventory: str) -> tuple[int, str, float]:
    """Execute an Ansible playbook and return (rc, output, elapsed)."""
    cmd = ["ansible-playbook", str(entry.file)]
    if inventory:
        cmd.extend(["-i", inventory])
    cmd.append("--timeout=30")

    log.info("Executing playbook: %s", " ".join(cmd))
    t0 = time.monotonic()

    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=entry.timeout,
            env={**os.environ, "ANSIBLE_FORCE_COLOR": "false", "ANSIBLE_NOCOLOR": "1"},
        )
        elapsed = time.monotonic() - t0
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, output, elapsed

    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - t0
        return -1, f"TIMEOUT after {entry.timeout}s", elapsed
    except Exception as exc:
        elapsed = time.monotonic() - t0
        return -1, f"ERROR: {exc}", elapsed


# ---------------------------------------------------------------------------
# Telegram helpers
# ---------------------------------------------------------------------------
def _trunc(text: str, limit: int | None = None) -> str:
    """Truncate text to fit Telegram message limits."""
    if limit is None:
        limit = get_config().max_message_length
    if len(text) <= limit:
        return text
    half = (limit - 30) // 2
    return text[:half] + "\n\n... [truncated] ...\n\n" + text[-half:]


def _result_output_limit(name: str, filename: str) -> int:
    """Reserve room for Markdown headers and keep the output block within Telegram limits."""
    overhead = len(name) + len(filename) + 200
    max_len = get_config().max_message_length
    return max(200, max_len - overhead)


def _build_result_text(
    icon: str,
    title: str,
    filename: str,
    file_icon: str,
    rc: int,
    output: str,
    elapsed: float,
) -> str:
    snippet = _trunc(output.strip(), _result_output_limit(title, filename))
    return (
        f"{icon} *{title}*\n"
        f"{file_icon} `{filename}`\n"
        f"⏱ {elapsed:.1f}s  |  exit: {rc}\n\n"
        f"```\n{snippet}\n```"
    )


def _inline_entry_text(kind_label: str, title: str, filename: str, description: str) -> str:
    """Build the message inserted when a user picks an inline result."""
    lines = [
        "Containerbot",
        f"{kind_label}: {title}",
        f"File: {filename}",
    ]
    if description:
        lines.append(f"Description: {description}")
    lines.append("Open the bot in private chat to execute this item.")
    return "\n".join(lines)


async def _bot_private_url(ctx: ContextTypes.DEFAULT_TYPE) -> str:
    """Return a t.me URL pointing to the bot private chat."""
    username = ctx.bot.username
    if not username:
        me = await ctx.bot.get_me()
        username = me.username or ""
    if not username:
        return "https://t.me/"
    return f"https://t.me/{username}"


async def handle_inline_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Answer inline queries with a safe searchable catalog of scripts/playbooks."""
    inline_query = update.inline_query
    user = update.effective_user
    if not inline_query or not user or not _user_is_allowed(user.id):
        if inline_query:
            await inline_query.answer([], cache_time=0, is_personal=True)
        return

    query = (inline_query.query or "").strip().lower()
    is_admin = _user_is_admin(user.id)
    cfg = get_config()
    private_url = await _bot_private_url(ctx)

    candidates: list[tuple[int, InlineQueryResultArticle]] = []

    for entry in cfg.scripts:
        if entry.hidden or (entry.admin_only and not is_admin):
            continue
        haystack = " ".join([
            entry.name,
            entry.file.name,
            entry.description,
            entry.category,
        ]).lower()
        if query:
            if query not in haystack:
                continue
            score = 2 if entry.name.lower().startswith(query) else 1
        else:
            score = 0

        subtitle = entry.description or f"Category: {entry.category}"
        if entry.admin_only:
            subtitle = f"[Admin] {subtitle}"

        candidates.append((
            score,
            InlineQueryResultArticle(
                id=f"s:{_script_token(entry)}",
                title=f"{'🐍' if entry.file.suffix == '.py' else '🔧'} {entry.name}",
                description=subtitle[:120],
                input_message_content=InputTextMessageContent(
                    _inline_entry_text("Script", entry.name, entry.file.name, entry.description)
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Open Containerbot", url=private_url),
                ]]),
            ),
        ))

    for entry in cfg.playbooks:
        if entry.hidden or (entry.admin_only and not is_admin):
            continue
        haystack = " ".join([
            entry.name,
            entry.file.name,
            entry.description,
            entry.category,
        ]).lower()
        if query:
            if query not in haystack:
                continue
            score = 2 if entry.name.lower().startswith(query) else 1
        else:
            score = 0

        subtitle = entry.description or f"Category: {entry.category}"
        if entry.admin_only:
            subtitle = f"[Admin] {subtitle}"

        candidates.append((
            score,
            InlineQueryResultArticle(
                id=f"p:{_playbook_token(entry)}",
                title=f"📘 {entry.name}",
                description=subtitle[:120],
                input_message_content=InputTextMessageContent(
                    _inline_entry_text("Playbook", entry.name, entry.file.name, entry.description)
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Open Containerbot", url=private_url),
                ]]),
            ),
        ))

    candidates.sort(key=lambda item: (-item[0], item[1].title))
    results = [article for _, article in candidates[:25]]
    await inline_query.answer(results, cache_time=0, is_personal=True)


async def _safe_edit(msg, text: str, parse_mode: str | None = "Markdown", **kw):
    """Edit a message with Markdown fallback to plain text."""
    try:
        await msg.edit_text(text, parse_mode=parse_mode, **kw)
    except BadRequest:
        await msg.edit_text(text, parse_mode=None, **kw)


async def _safe_reply(message, text: str, parse_mode: str | None = "Markdown", **kw):
    """Reply with Markdown fallback to plain text."""
    try:
        return await message.reply_text(text, parse_mode=parse_mode, **kw)
    except BadRequest:
        return await message.reply_text(text, parse_mode=None, **kw)


def _auth_check(update: Update) -> bool:
    """Return True if the user is authorized, else send a rejection."""
    user = update.effective_user
    if not user:
        return False
    return _user_is_allowed(user.id)


async def _reject(update: Update):
    uid = update.effective_user.id if update.effective_user else "?"
    await _safe_reply(
        update.effective_message,
        f"⛔ Not authorized.\nYour User ID: `{uid}`",
    )


# ---------------------------------------------------------------------------
# Menu builder
# ---------------------------------------------------------------------------
def _build_menu_text(cfg: BotConfig) -> str:
    """Build the main menu message text."""
    return (
        "🤖 *Containerbot 0.0.1*\n"
        f"📁 {len(cfg.scripts)} scripts  |  📘 {len(cfg.playbooks)} playbooks\n\n"
        "Use /menu to browse and execute scripts.\n"
        "Use /list to see all available scripts.\n"
        "Use /run <filename> to run a script directly.\n"
        "Use /reload to rescan the scripts directory.\n"
        "Use /help for this message."
    )


def _build_category_keyboard(cfg: BotConfig, user_id: int) -> InlineKeyboardMarkup:
    """Build the top-level category selection keyboard."""
    is_admin = _user_is_admin(user_id)
    categories: dict[str, int] = {}

    for s in cfg.scripts:
        if s.hidden:
            continue
        if s.admin_only and not is_admin:
            continue
        categories[s.category] = categories.get(s.category, 0) + 1

    for p in cfg.playbooks:
        if p.hidden:
            continue
        if p.admin_only and not is_admin:
            continue
        categories[p.category] = categories.get(p.category, 0) + 1

    buttons = []
    for cat, count in sorted(categories.items()):
        buttons.append([InlineKeyboardButton(
            f"📂 {cat} ({count})",
            callback_data=f"cat:{_category_token(cat)}",
        )])
    return InlineKeyboardMarkup(buttons)


def _build_scripts_keyboard(
    cfg: BotConfig, category: str, user_id: int
) -> InlineKeyboardMarkup:
    """Build keyboard listing scripts in a given category."""
    is_admin = _user_is_admin(user_id)
    buttons = []

    # Scripts
    for s in cfg.scripts:
        if s.hidden or s.category != category:
            continue
        if s.admin_only and not is_admin:
            continue
        icon = "🐍" if s.file.suffix == ".py" else "🔧"
        label = f"{icon} {s.name}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"run:s:{_script_token(s)}")])

    # Playbooks
    for p in cfg.playbooks:
        if p.hidden or p.category != category:
            continue
        if p.admin_only and not is_admin:
            continue
        buttons.append([InlineKeyboardButton(
            f"📘 {p.name}", callback_data=f"run:p:{_playbook_token(p)}"
        )])

    buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back:menu")])
    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /start and /help - show main menu."""
    if not _auth_check(update):
        await _reject(update)
        return

    cfg = get_config()
    uid = update.effective_user.id if update.effective_user else 0
    await _safe_reply(
        update.message,
        _build_menu_text(cfg),
        reply_markup=_build_category_keyboard(cfg, uid),
    )


async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /menu - show interactive category menu."""
    if not _auth_check(update):
        await _reject(update)
        return
    cfg = get_config()
    uid = update.effective_user.id if update.effective_user else 0
    await _safe_reply(
        update.message,
        "📂 *Select a category:*",
        reply_markup=_build_category_keyboard(cfg, uid),
    )


async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /list - show a flat text list of all scripts."""
    if not _auth_check(update):
        await _reject(update)
        return

    cfg = get_config()
    is_admin = _user_is_admin(update.effective_user.id)
    lines = ["📋 *Available scripts:*\n"]

    current_cat = ""
    for s in cfg.scripts:
        if s.hidden or (s.admin_only and not is_admin):
            continue
        if s.category != current_cat:
            current_cat = s.category
            lines.append(f"\n*{current_cat}:*")
        icon = "🐍" if s.file.suffix == ".py" else "🔧"
        desc = f" - _{s.description}_" if s.description else ""
        lines.append(f"  {icon} `{s.file.name}`{desc}")

    if cfg.playbooks:
        lines.append("\n*Ansible:*")
        for p in cfg.playbooks:
            if p.hidden or (p.admin_only and not is_admin):
                continue
            desc = f" - _{p.description}_" if p.description else ""
            lines.append(f"  📘 `{p.file.name}`{desc}")

    await _safe_reply(update.message, "\n".join(lines))


async def cmd_run(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /run <filename> [args] - run a script directly by filename."""
    if not _auth_check(update):
        await _reject(update)
        return

    text = update.message.text or ""
    raw_args = text.split(maxsplit=1)
    if len(raw_args) < 2:
        await _safe_reply(update.message, "Usage: `/run <filename> [args...]`")
        return

    try:
        parsed_args = _parse_shell_args(raw_args[1])
    except ValueError as exc:
        await _safe_reply(update.message, f"❌ Invalid arguments: `{exc}`")
        return

    if not parsed_args:
        await _safe_reply(update.message, "Usage: `/run <filename> [args...]`")
        return

    filename = parsed_args[0]
    extra_args = parsed_args[1:]
    cfg = get_config()
    is_admin = _user_is_admin(update.effective_user.id)

    # Search in scripts
    script_matches = _find_scripts_by_name_or_path(cfg, filename)
    if script_matches:
        if len(script_matches) > 1:
            rel_paths = ", ".join(f"`{_script_relative_path(entry.file)}`" for entry in script_matches[:5])
            await _safe_reply(
                update.message,
                "❌ Ambiguous script name. Use the relative path instead.\n"
                f"Matches: {rel_paths}",
            )
            return
        entry = script_matches[0]
        if entry.admin_only and not is_admin:
            await _safe_reply(update.message, "⛔ Admin-only script.")
            return
        await _execute_and_reply(update, entry, extra_args=extra_args)
        return

    # Search in playbooks
    playbook_matches = _find_playbooks_by_name_or_path(cfg, filename)
    if playbook_matches:
        if len(playbook_matches) > 1:
            rel_paths = ", ".join(f"`{_playbook_relative_path(entry.file)}`" for entry in playbook_matches[:5])
            await _safe_reply(
                update.message,
                "❌ Ambiguous playbook name. Use the relative path instead.\n"
                f"Matches: {rel_paths}",
            )
            return
        entry = playbook_matches[0]
        if entry.admin_only and not is_admin:
            await _safe_reply(update.message, "⛔ Admin-only playbook.")
            return
        await _execute_playbook_and_reply(update, entry)
        return

    await _safe_reply(update.message, f"❌ Script not found: `{filename}`")


async def cmd_reload(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /reload - rescan scripts directory."""
    if not _auth_check(update):
        await _reject(update)
        return
    if not _user_is_admin(update.effective_user.id):
        await _safe_reply(update.message, "⛔ Admin-only command.")
        return

    global _config
    _config = load_config()
    cfg = _config
    await _safe_reply(
        update.message,
        f"✅ Reloaded: {len(cfg.scripts)} scripts, {len(cfg.playbooks)} playbooks",
    )


async def cmd_upload(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /upload - instructions for uploading scripts."""
    if not _auth_check(update):
        await _reject(update)
        return

    if not ENABLE_SCRIPT_UPLOAD:
        await _safe_reply(
            update.message,
            "⛔ Script upload is disabled. Set `ENABLE_SCRIPT_UPLOAD=true` to enable it.",
        )
        return

    await _safe_reply(
        update.message,
        "📤 *Upload a script*\n\n"
        "Send a `.sh` or `.py` file as a document to this chat.\n"
        "It will be saved to the scripts directory and available in /menu.\n\n"
        "Only admins can upload scripts.",
    )


async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded .sh/.py documents - save to scripts dir."""
    if not _auth_check(update):
        return
    if not ENABLE_SCRIPT_UPLOAD:
        await _safe_reply(update.message, "⛔ Script upload is disabled.")
        return
    if not _user_is_admin(update.effective_user.id):
        await _safe_reply(update.message, "⛔ Only admins can upload scripts.")
        return

    doc = update.message.document
    if not doc or not doc.file_name:
        return

    ext = Path(doc.file_name).suffix
    if ext not in SCRIPT_EXTENSIONS:
        await _safe_reply(update.message, f"⚠️ Unsupported extension: `{ext}`\nAllowed: {SCRIPT_EXTENSIONS}")
        return

    tg_file = await doc.get_file()
    try:
        dest = _uploaded_script_destination(doc.file_name)
    except ValueError as exc:
        await _safe_reply(update.message, f"⚠️ Invalid filename: `{exc}`")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    await tg_file.download_to_drive(str(dest))
    dest.chmod(0o755)

    # Reload config to pick up the new script
    global _config
    _config = load_config()

    await _safe_reply(
        update.message,
        f"✅ Saved `{doc.file_name}` to scripts directory.\n"
        f"Total scripts: {len(_config.scripts)}",
    )


# ---------------------------------------------------------------------------
# Callback query handlers (inline keyboard)
# ---------------------------------------------------------------------------
async def cb_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Central callback query dispatcher."""
    q = update.callback_query
    if not q or not q.data:
        return
    await q.answer()

    user = update.effective_user
    if not user or not _user_is_allowed(user.id):
        await q.edit_message_text("⛔ Not authorized.")
        return

    data = q.data
    cfg = get_config()

    # ── Back to main menu ──
    if data == "back:menu":
        await q.edit_message_text(
            "📂 *Select a category:*",
            parse_mode="Markdown",
            reply_markup=_build_category_keyboard(cfg, user.id),
        )
        return

    # ── Category selected ──
    if data.startswith("cat:"):
        category_token = data[4:]
        category = _find_category_by_token(cfg, category_token, user.id)
        if category is None:
            await q.edit_message_text("❌ Category no longer available. Try /menu again.")
            return
        await q.edit_message_text(
            f"📂 *{category}*\nSelect a script to run:",
            parse_mode="Markdown",
            reply_markup=_build_scripts_keyboard(cfg, category, user.id),
        )
        return

    # ── Run script ──
    if data.startswith("run:s:"):
        token = data[6:]
        entry = _find_script_by_token(cfg, token)
        if entry is None:
            await q.edit_message_text("❌ Script no longer available. Try /menu again.")
            return

        if entry.admin_only and not _user_is_admin(user.id):
            await q.edit_message_text("⛔ Admin-only script.")
            return

        # If script needs args, ask user for input
        if entry.args_prompt:
            pending_key = (update.effective_chat.id, user.id)
            _pending_args[pending_key] = (token, entry.args_prompt)
            await q.edit_message_text(
                f"📝 *{entry.name}*\n\n{entry.args_prompt}\n\n"
                "Type the arguments and send (or /cancel):",
                parse_mode="Markdown",
            )
            return

        # If confirmation required, ask first
        if entry.confirm:
            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ Yes, run",
                        callback_data=f"confirm:s:{user.id}:{token}",
                    ),
                    InlineKeyboardButton("❌ Cancel", callback_data="back:menu"),
                ]
            ])
            desc = f"\n_{entry.description}_" if entry.description else ""
            await q.edit_message_text(
                f"⚠️ *Confirm execution:*\n`{entry.file.name}`{desc}",
                parse_mode="Markdown",
                reply_markup=kb,
            )
            return

        # Execute directly
        await _execute_from_callback(q, entry)
        return

    # ── Run playbook ──
    if data.startswith("run:p:"):
        token = data[6:]
        entry = _find_playbook_by_token(cfg, token)
        if entry is None:
            await q.edit_message_text("❌ Playbook no longer available. Try /menu again.")
            return

        if entry.admin_only and not _user_is_admin(user.id):
            await q.edit_message_text("⛔ Admin-only playbook.")
            return

        if entry.confirm:
            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ Yes, run",
                        callback_data=f"confirm:p:{user.id}:{token}",
                    ),
                    InlineKeyboardButton("❌ Cancel", callback_data="back:menu"),
                ]
            ])
            await q.edit_message_text(
                f"⚠️ *Confirm playbook execution:*\n`{entry.file.name}`",
                parse_mode="Markdown",
                reply_markup=kb,
            )
            return

        await _execute_playbook_from_callback(q, entry)
        return

    # ── Confirm execution ──
    if data.startswith("confirm:s:"):
        parts = data.split(":")
        if len(parts) != 4:
            await q.edit_message_text("❌ Invalid confirmation token.")
            return
        owner_id = int(parts[2])
        token = parts[3]
        if user.id != owner_id:
            await q.answer("Only the user who requested this action can confirm it.", show_alert=True)
            return
        entry = _find_script_by_token(cfg, token)
        if entry is None:
            await q.edit_message_text("❌ Script no longer available. Try /menu again.")
            return
        if entry.admin_only and not _user_is_admin(user.id):
            await q.edit_message_text("⛔ Admin-only script.")
            return
        await _execute_from_callback(q, entry)
        return

    if data.startswith("confirm:p:"):
        parts = data.split(":")
        if len(parts) != 4:
            await q.edit_message_text("❌ Invalid confirmation token.")
            return
        owner_id = int(parts[2])
        token = parts[3]
        if user.id != owner_id:
            await q.answer("Only the user who requested this action can confirm it.", show_alert=True)
            return
        entry = _find_playbook_by_token(cfg, token)
        if entry is None:
            await q.edit_message_text("❌ Playbook no longer available. Try /menu again.")
            return
        if entry.admin_only and not _user_is_admin(user.id):
            await q.edit_message_text("⛔ Admin-only playbook.")
            return
        await _execute_playbook_from_callback(q, entry)
        return


async def handle_text_args(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages that might be args for a pending script."""
    if not _auth_check(update):
        return

    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return  # Not waiting for args, ignore

    pending_key = (chat.id, user.id)
    if pending_key not in _pending_args:
        return

    token, prompt_text = _pending_args.pop(pending_key)
    cfg = get_config()
    entry = _find_script_by_token(cfg, token)
    if entry is None:
        await _safe_reply(update.message, "❌ Script no longer available. Try /menu again.")
        return

    if entry.admin_only and not _user_is_admin(user.id):
        await _safe_reply(update.message, "⛔ Admin-only script.")
        return

    try:
        extra_args = _parse_shell_args(update.message.text.strip())
    except ValueError as exc:
        _pending_args[pending_key] = (token, prompt_text)
        await _safe_reply(update.message, f"❌ Invalid arguments: `{exc}`")
        return

    await _execute_and_reply(update, entry, extra_args=extra_args)


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel - cancel pending arg input."""
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    pending_key = (chat.id, user.id)
    if pending_key in _pending_args:
        _pending_args.pop(pending_key)
        await _safe_reply(update.message, "❌ Cancelled.")
    else:
        await _safe_reply(update.message, "Nothing to cancel.")


# ---------------------------------------------------------------------------
# Execution + reply helpers
# ---------------------------------------------------------------------------
async def _execute_from_callback(query, entry: ScriptEntry, extra_args: list[str] | None = None):
    """Run a script triggered from an inline-keyboard callback."""
    await query.edit_message_text(f"⏳ Running `{entry.file.name}`...", parse_mode="Markdown")

    rc, output, elapsed = await run_script(entry, extra_args)
    _format_and_send(query, entry.name, entry.file.name, rc, output, elapsed)

    icon = "✅" if rc == 0 else "❌"
    text = _build_result_text(icon, entry.name, entry.file.name, "📄", rc, output, elapsed)
    await _safe_edit(query.message, text)


async def _execute_and_reply(
    update: Update,
    entry: ScriptEntry,
    extra_args: list[str] | None = None,
):
    """Run a script triggered from a /run command or arg input."""
    msg = await _safe_reply(
        update.message, f"⏳ Running `{entry.file.name}`...",
    )

    rc, output, elapsed = await run_script(entry, extra_args)

    icon = "✅" if rc == 0 else "❌"
    text = _build_result_text(icon, entry.name, entry.file.name, "📄", rc, output, elapsed)
    await _safe_edit(msg, text)


async def _execute_playbook_from_callback(query, entry: AnsibleEntry):
    """Run an Ansible playbook from callback."""
    cfg = get_config()
    await query.edit_message_text(
        f"⏳ Running playbook `{entry.file.name}`...", parse_mode="Markdown"
    )

    rc, output, elapsed = await run_playbook(entry, cfg.ansible_inventory)

    icon = "✅" if rc == 0 else "❌"
    text = _build_result_text(icon, entry.name, entry.file.name, "📘", rc, output, elapsed)
    await _safe_edit(query.message, text)


async def _execute_playbook_and_reply(update: Update, entry: AnsibleEntry):
    """Run an Ansible playbook from /run command."""
    cfg = get_config()
    msg = await _safe_reply(
        update.message, f"⏳ Running playbook `{entry.file.name}`...",
    )

    rc, output, elapsed = await run_playbook(entry, cfg.ansible_inventory)

    icon = "✅" if rc == 0 else "❌"
    text = _build_result_text(icon, entry.name, entry.file.name, "📘", rc, output, elapsed)
    await _safe_edit(msg, text)


def _format_and_send(query, name, filename, rc, output, elapsed):
    """Log execution result (audit trail)."""
    user = query.from_user
    log.info(
        "EXEC user=%s(%s) script=%s rc=%d elapsed=%.1fs",
        user.full_name if user else "?",
        user.id if user else 0,
        filename,
        rc,
        elapsed,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main():
    if not BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN is not set!")
        return

    # Load configuration and discover scripts
    global _config
    _config = load_config()
    log.info(
        "Discovered %d scripts, %d playbooks",
        len(_config.scripts),
        len(_config.playbooks),
    )

    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("run", cmd_run))
    app.add_handler(CommandHandler("reload", cmd_reload))
    app.add_handler(CommandHandler("upload", cmd_upload))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(InlineQueryHandler(handle_inline_query))

    # Document upload handler (for uploading new scripts)
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Plain text handler (for args input)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_text_args
    ))

    # Inline keyboard callback handler
    app.add_handler(CallbackQueryHandler(cb_handler))

    # Start background file watcher (auto-reload when scripts change)
    _start_file_watcher(app)

    log.info("Bot starting (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


# ---------------------------------------------------------------------------
# File watcher - auto-reload when scripts/ contents change
# ---------------------------------------------------------------------------
_last_snapshot: dict[str, float] = {}


def _take_snapshot() -> dict[str, float]:
    """Return {relative_path: mtime} for all scripts and playbooks."""
    snap: dict[str, float] = {}
    scripts_path = Path(SCRIPTS_DIR)
    if scripts_path.is_dir():
        for f in scripts_path.rglob("*"):
            if f.is_file() and f.suffix in SCRIPT_EXTENSIONS:
                snap[str(f)] = f.stat().st_mtime
    pb_path = Path(ANSIBLE_DIR) / "playbooks"
    if pb_path.is_dir():
        for f in pb_path.rglob("*.y*ml"):
            if f.is_file():
                snap[str(f)] = f.stat().st_mtime
    cfg = Path(CONFIG_FILE)
    if cfg.is_file():
        snap[str(cfg)] = cfg.stat().st_mtime
    return snap


async def _watch_loop(app: Application) -> None:
    """Periodically check for file changes and reload config."""
    global _config, _last_snapshot
    _last_snapshot = _take_snapshot()

    while True:
        await asyncio.sleep(10)  # Check every 10 seconds
        try:
            new_snap = _take_snapshot()
            if new_snap != _last_snapshot:
                _last_snapshot = new_snap
                old_count = len(_config.scripts) + len(_config.playbooks)
                _config = load_config()
                new_count = len(_config.scripts) + len(_config.playbooks)
                log.info(
                    "Auto-reload: scripts changed (%d -> %d items)",
                    old_count, new_count,
                )
        except Exception as exc:
            log.warning("File watcher error: %s", exc)


def _start_file_watcher(app: Application) -> None:
    """Launch the file watcher as a background asyncio task."""
    loop = asyncio.get_event_loop()
    loop.create_task(_watch_loop(app))
    log.info("File watcher started (checking every 10s)")


if __name__ == "__main__":
    main()
