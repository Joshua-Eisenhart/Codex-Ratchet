#!/usr/bin/env python3
"""
Telegram <-> Codex Ratchet command interface.

Setup:
  1. Message @BotFather on Telegram → /newbot → get token
  2. Message your bot once from your phone
  3. Run this script — it will print your chat_id on first message
  4. Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID below (or via env vars)

Usage:
    make telegram
    python3 telegram_bot.py
"""

import glob
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────
FILE_TELEGRAM_TOKEN = ""
FILE_TELEGRAM_CHAT_ID = ""
CODEX_TELEGRAM_ENV_PATH = os.environ.get(
    "CODEX_TELEGRAM_ENV_PATH",
    os.path.expanduser("~/.codex/telegram_bot.env"),
)

def _clean_env_value(value):
    if value is None:
        return ""
    return (
        value.strip()
        .replace("\u201c", "")
        .replace("\u201d", "")
        .replace("\u2018", "")
        .replace("\u2019", "")
    )


def _load_env_file(path):
    loaded = {}
    if not path or not os.path.exists(path):
        return loaded
    try:
        with open(path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                loaded[key] = _clean_env_value(value)
    except Exception as e:
        print(f"  [!] Failed to read env file {path}: {e}", file=sys.stderr)
    return loaded


def _config_value(*names, fallback=""):
    for name in names:
        value = _clean_env_value(os.environ.get(name, ""))
        if value:
            return value
        value = _clean_env_value(FILE_ENV_VARS.get(name, ""))
        if value:
            return value
    return _clean_env_value(fallback)


FILE_ENV_VARS = _load_env_file(CODEX_TELEGRAM_ENV_PATH)
TELEGRAM_TOKEN = _config_value("TELEGRAM_TOKEN", "TELEGRAM_BOT_TOKEN", fallback=FILE_TELEGRAM_TOKEN)
TELEGRAM_CHAT_ID = _config_value("TELEGRAM_CHAT_ID", fallback=FILE_TELEGRAM_CHAT_ID)
POLL_TIMEOUT     = 30
SIM_TIMEOUT      = 300
CODEX_TIMEOUT    = 600
CODEX_MODEL      = os.environ.get("CODEX_MODEL", "").strip()
PROJECT_DIR      = os.environ.get("PROJECT_DIR", "/Users/joshuaeisenhart/Desktop/Codex Ratchet")
RESULTS_DIR      = os.path.join(PROJECT_DIR, "system_v4/probes/a2_state/sim_results")
PROBES_DIR       = os.path.join(PROJECT_DIR, "system_v4/probes")
LIVE_SPINE_PATH  = os.path.join(RESULTS_DIR, "live_anchor_spine.json")
MAX_MSG_LEN      = 4000

PYTHON_BIN      = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
MPLCONFIGDIR    = "/tmp/codex-mpl"
NUMBA_CACHE_DIR = "/tmp/codex-numba"
CODEX_BIN       = os.environ.get("CODEX_BIN", "/usr/local/bin/codex")
CODEX_HOME_DIR  = os.environ.get("CODEX_HOME", "/tmp/codex-telegram-home")
LIVE_QUEUE_CONTROLLER = os.path.join(PROJECT_DIR, "system_v4/probes/live_queue_controller.py")



# ── Telegram API ──────────────────────────────────────────────────────

def _api(method, **params):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    data = urllib.parse.urlencode(params).encode()
    try:
        with urllib.request.urlopen(url, data=data, timeout=POLL_TIMEOUT + 5) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": e.read().decode()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_updates(offset=0):
    """Long-poll for new messages."""
    url = (
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        f"?offset={offset}&timeout={POLL_TIMEOUT}&allowed_updates=message"
    )
    try:
        with urllib.request.urlopen(url, timeout=POLL_TIMEOUT + 10) as r:
            return json.loads(r.read()).get("result", [])
    except Exception as e:
        print(f"  [!] get_updates error: {e}", file=sys.stderr)
        return []


def send_message(text, chat_id=None):
    """Send plain text, chunking at MAX_MSG_LEN."""
    cid = chat_id or TELEGRAM_CHAT_ID
    if not cid:
        print("  [!] No chat_id — message a bot first to set it")
        return {"ok": False, "attempted_count": 0, "sent_count": 0, "errors": ["missing chat_id"]}
    attempted = 0
    sent = 0
    errors = []
    for chunk in _split(text):
        attempted += 1
        result = _api("sendMessage", chat_id=cid, text=chunk)
        if result.get("ok"):
            sent += 1
        else:
            errors.append(result.get("error", "unknown sendMessage error"))
        if len(text) > MAX_MSG_LEN:
            time.sleep(0.5)
    if errors:
        print(f"  [!] send_message error(s): {' | '.join(errors[:3])}", file=sys.stderr)
    return {
        "ok": not errors,
        "attempted_count": attempted,
        "sent_count": sent,
        "errors": errors,
    }



def format_run_status_report(
    *,
    phase,
    summary,
    duration_bound=None,
    primary_lane=None,
    maintenance_lane=None,
    current_task=None,
    health=None,
    last_success=None,
    changed_items=None,
    next_step=None,
    closure_state=None,
    worker_state=None,
    log_path=None,
):
    title = str(phase or "status").strip().upper()
    lines = [f"{title} — {summary}"]
    if duration_bound:
        lines.append(f"Duration: {duration_bound}")
    if primary_lane:
        lines.append(f"Primary lane: {primary_lane}")
    if maintenance_lane:
        lines.append(f"Maintenance lane: {maintenance_lane}")
    if current_task:
        lines.append(f"Current task: {current_task}")
    if health:
        lines.append(f"Health: {health}")
    if last_success:
        lines.append(f"Last success: {last_success}")
    if changed_items:
        lines.append(f"Changed: {', '.join(changed_items)}")
    if next_step:
        lines.append(f"Next: {next_step}")
    if closure_state:
        lines.append(f"Closure: {closure_state}")
    if worker_state:
        lines.append(f"Worker: {worker_state}")
    if log_path:
        lines.append(f"Log: {log_path}")
    return "\n".join(lines)


def _split(text):
    if len(text) <= MAX_MSG_LEN:
        return [text]
    chunks, current = [], ""
    for line in text.split("\n"):
        addition = line + "\n"
        if len(current) + len(addition) > MAX_MSG_LEN and current:
            chunks.append(current.rstrip())
            current = addition
        else:
            current += addition
    if current.strip():
        chunks.append(current.rstrip())
    return chunks or [text[:MAX_MSG_LEN]]


# ── Environment ───────────────────────────────────────────────────────
def _base_env():
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = MPLCONFIGDIR
    env["NUMBA_CACHE_DIR"] = NUMBA_CACHE_DIR
    env["CODEX_HOME"] = CODEX_HOME_DIR
    os.makedirs(env["CODEX_HOME"], exist_ok=True)
    return env


def resolve_incoming_chat(configured_chat_id, incoming_chat_id):
    configured = str(configured_chat_id or "").strip()
    incoming = str(incoming_chat_id or "").strip()
    if not incoming:
        return configured, False, "missing incoming chat_id"
    if not configured:
        return configured, False, f'unconfigured controller; refusing auto-bind from chat {incoming}. Set TELEGRAM_CHAT_ID="{incoming}" explicitly'
    if incoming != configured:
        return configured, False, f"Ignoring message from unknown chat {incoming}"
    return configured, True, ""


# ── Handlers ──────────────────────────────────────────────────────────

def _sim_allowlist():
    files = glob.glob(os.path.join(PROBES_DIR, "sim_*.py"))
    return {os.path.basename(f)[4:-3] for f in files}


def handle_help(args):
    cmds = [k for k in HANDLERS if k not in ("sim",)]
    return "Commands:\n" + "\n".join(f"  {c}" for c in cmds) + "\n\nrun <name>  show <name>  sims [filter]"


def handle_status(args):
    r = subprocess.run(
        ["git", "status", "--short", "system_v4/probes/"],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=15, env=_base_env()
    )
    lines = r.stdout.strip().splitlines()
    if not lines:
        return "git status: no changes"
    modified = [l for l in lines if l.startswith((" M", "M", "MM"))]
    new = [l for l in lines if l.startswith("??")]
    out = f"git status: {len(lines)} changes\n- modified: {len(modified)}\n- untracked: {len(new)}\n"
    for l in modified[:10]:
        out += f"  {l.strip()}\n"
    if len(modified) > 10:
        out += f"  ...+{len(modified)-10} more"
    return out.strip()


def handle_audit(args):
    script = os.path.join(PROBES_DIR, "audit_overclassification.py")
    r = subprocess.run(
        [PYTHON_BIN, script],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=60, env=_base_env()
    )
    out = (r.stdout + r.stderr).strip()
    verdict = "PASSED" if r.returncode == 0 else "FAILED"
    return f"audit {verdict} (rc={r.returncode}):\n{out[:2000]}"


def handle_run(args):
    if not args:
        return "usage: run <sim_name>  (omit sim_ prefix and .py)"
    name = args.strip().removeprefix("sim_").removesuffix(".py")
    allowlist = _sim_allowlist()
    if name not in allowlist:
        close = sorted(s for s in allowlist if name in s)[:5]
        hint = "\nDid you mean:\n" + "\n".join(f"  {s}" for s in close) if close else ""
        return f"unknown sim: {name}{hint}"
    if not name.startswith("pure_lego_"):
        return (
            f"WARNING: {name} is not a pure_lego sim.\n"
            f"Build order requires pure_lego sims first.\n"
            f"Run anyway? Text: run! {name}"
        )
    return _run_sim(name)


def handle_run_force(args):
    """run! <name> — bypass build-order warning."""
    if not args:
        return "usage: run! <sim_name>"
    name = args.strip().removeprefix("sim_").removesuffix(".py")
    if name not in _sim_allowlist():
        return f"unknown sim: {name}"
    return _run_sim(name)


def _run_sim(name):
    script = os.path.join(PROBES_DIR, f"sim_{name}.py")
    ts_start = datetime.now().strftime("%H:%M:%S")
    r = subprocess.run(
        [PYTHON_BIN, script],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=SIM_TIMEOUT, env=_base_env()
    )
    ts_end = datetime.now().strftime("%H:%M:%S")
    out = (r.stdout + r.stderr).strip()
    proof = (
        f"[{ts_start} -> {ts_end}]\n"
        f"python: {PYTHON_BIN}\n"
        f"script: sim_{name}.py\n"
        f"exit: {r.returncode}\n"
        f"---\n"
    )
    return proof + out[:3000]


def handle_show(args):
    if not args:
        return "usage: show <result_name>"
    name = args.strip().removesuffix("_results.json").removesuffix(".json")
    candidates = glob.glob(os.path.join(RESULTS_DIR, f"{name}*_results.json"))
    if not candidates:
        candidates = glob.glob(os.path.join(RESULTS_DIR, f"*{name}*_results.json"))
    if not candidates:
        return f"no result file matching '{name}'"
    fpath = sorted(candidates)[0]
    try:
        with open(fpath) as f:
            d = json.load(f)
    except Exception as e:
        return f"parse error: {e}"
    fname = os.path.basename(fpath)
    cls = d.get("classification", "?")
    summary = d.get("summary", {})
    passed = summary.get("passed", summary.get("pass", "?"))
    total = summary.get("total", summary.get("tests_run", "?"))
    lines = [fname, f"- classification: {cls}", f"- passed: {passed}/{total}"]
    if isinstance(summary, dict):
        for k, v in list(summary.items())[:8]:
            if k not in ("passed", "pass", "total", "tests_run"):
                lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def handle_sims(args):
    names = sorted(_sim_allowlist())
    legos = [n for n in names if n.startswith("pure_lego_")]
    if args.lower() == "all":
        return (
            f"{len(names)} total sims — {len(names)-len(legos)} are out-of-order.\n"
            f"Only pure_lego sims are in scope. Use 'sims' for the valid list."
        )
    if args:
        matches = [n for n in legos if args.lower() in n.lower()]
        if not matches:
            return f"no pure_lego sims matching '{args}'"
        return f"{len(matches)} pure_lego sims matching '{args}':\n" + "\n".join(matches)
    lines = [f"pure_lego sims ({len(legos)} — in-scope work):"] + legos
    return "\n".join(lines)


def handle_log(args):
    log_path = "/tmp/telegram_bot.log"
    if not os.path.exists(log_path):
        return "log not found"
    r = subprocess.run(["tail", "-40", log_path], capture_output=True, text=True, timeout=10)
    return r.stdout.strip() or "(empty)"


def handle_spine(args):
    if not os.path.exists(LIVE_SPINE_PATH):
        return "live anchor spine not found; run 'align' first"
    try:
        with open(LIVE_SPINE_PATH) as f:
            data = json.load(f)
    except Exception as e:
        return f"spine parse error: {e}"
    rows = data.get("rows", [])
    if not rows:
        return "live anchor spine is empty"
    lines = [f"live spine: {len(rows)} entries"]
    for row in rows[:20]:
        ready = "ready" if row.get("promotion_ready") else "risky"
        blockers = row.get("blockers", [])
        suffix = f" [{', '.join(blockers[:2])}]" if blockers else ""
        lines.append(f"- {row.get('stage','?')}: {row.get('result_json','?')} -> {ready}{suffix}")
    return "\n".join(lines)


def handle_align(args):
    script = os.path.join(PROBES_DIR, "controller_alignment_audit.py")
    r = subprocess.run(
        [PYTHON_BIN, script],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=90, env=_base_env()
    )
    out = (r.stdout + r.stderr).strip()
    verdict = "PASSED" if r.returncode == 0 else "FAILED"
    return f"align {verdict} (rc={r.returncode}):\n{out[:2000]}"


def _parse_run_duration_minutes(text):
    m = re.search(r"(\d+)\s*(hour|hours|hr|hrs)", text, flags=re.I)
    if m:
        return int(m.group(1)) * 60
    m = re.search(r"(\d+)\s*(minute|minutes|min|mins)", text, flags=re.I)
    if m:
        return int(m.group(1))
    return None


def handle_live_queue_run(text):
    minutes = _parse_run_duration_minutes(text) or 60
    if not os.path.exists(LIVE_QUEUE_CONTROLLER):
        return "live queue controller missing"
    log_path = f"/tmp/codex_live_queue_run_{int(time.time())}.log"
    with open(log_path, "w", encoding="utf-8") as logf:
        proc = subprocess.Popen(
            [PYTHON_BIN, LIVE_QUEUE_CONTROLLER, "--minutes", str(minutes)],
            cwd=PROJECT_DIR,
            env=_base_env(),
            stdout=logf,
            stderr=subprocess.STDOUT,
            text=True,
        )
    return (
        f"live queue run started\n"
        f"- pid: {proc.pid}\n"
        f"- minutes: {minutes}\n"
        f"- controller: {LIVE_QUEUE_CONTROLLER}\n"
        f"- log: {log_path}"
    )


HANDLERS = {
    "help":    handle_help,
    "status":  handle_status,
    "audit":   handle_audit,
    "align":   handle_align,
    "run":     handle_run,
    "run!":    handle_run_force,
    "show":    handle_show,
    "sims":    handle_sims,
    "sim":     handle_sims,
    "spine":   handle_spine,
    "log":     handle_log,
}


# ── Freeform fallback (Codex) ─────────────────────────────────────────

FREEFORM_PROMPT = """You are a Codex controller for the Codex Ratchet repo.
Reply in plain text only.
Keep replies short.
Work only inside the project directory.
Do not refer to Hermes or Claude Code bots.
Answer normal questions about repo files, docs, and project state.
Only redirect the user to an explicit bot command when they are clearly trying to invoke that command directly."""


def codex_freeform(question):
    output_path = f"/tmp/codex_telegram_reply_{int(time.time() * 1000)}.txt"
    prompt = f"{FREEFORM_PROMPT}\n\nUser request:\n{question}\n"

    cmd = [
        CODEX_BIN,
        "exec",
        "--sandbox", "workspace-write",
        "-C", PROJECT_DIR,
        "-o", output_path,
    ]
    if CODEX_MODEL:
        cmd.extend(["-m", CODEX_MODEL])
    cmd.append(prompt)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CODEX_TIMEOUT,
            cwd=PROJECT_DIR,
            env=_base_env(),
        )

        if os.path.exists(output_path):
            with open(output_path) as f:
                out = f.read().strip()
            if out:
                return out

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if stdout:
            return stdout[-3000:]
        if stderr:
            return f"(codex error)\n{stderr[-3000:]}"
        return f"(codex exited rc={result.returncode})"

    except subprocess.TimeoutExpired:
        return f"(Codex timed out after {CODEX_TIMEOUT}s)"
    except Exception as e:
        return f"(error: {str(e)[:200]})"


# ── Dispatch ──────────────────────────────────────────────────────────

def dispatch(text):
    stripped = text.strip()
    lower = stripped.lower()
    if lower.startswith("run for ") or lower.startswith("do a ") or lower.startswith("run "):
        if "live queue" in lower or "bounded run" in lower or re.search(r"\d+\s*(hour|hours|hr|hrs|minute|minutes|min|mins)", lower):
            try:
                return handle_live_queue_run(stripped)
            except Exception as e:
                return f"(live-run handler error: {e})"
    for keyword, fn in HANDLERS.items():
        if lower == keyword or lower.startswith(keyword + " "):
            args = stripped[len(keyword):].strip()
            try:
                return fn(args)
            except subprocess.TimeoutExpired:
                return f"(timed out: {keyword})"
            except Exception as e:
                return f"(handler error: {e})"
    return codex_freeform(stripped)


# ── Main loop ─────────────────────────────────────────────────────────

def main():
    global TELEGRAM_CHAT_ID

    if not TELEGRAM_TOKEN:
        print("Set TELEGRAM_TOKEN first.")
        print("  1. Message @BotFather on Telegram")
        print("  2. /newbot → follow prompts → copy token")
        print("  3. export TELEGRAM_TOKEN=<token> && python3 telegram_bot.py")
        sys.exit(1)

    print("=" * 60)
    print("  Codex Ratchet — Telegram Command Interface")
    print(f"  Python  : {PYTHON_BIN}")
    print(f"  Runtime : {CODEX_BIN} (Codex fallback)")
    print(f"  Handlers: {', '.join(HANDLERS)}")
    print("  Ctrl+C to stop")
    print("=" * 60)

    if not os.path.exists(PYTHON_BIN):
        print(f"  [!] Python not found: {PYTHON_BIN}")
        sys.exit(1)

    # Test token
    me = _api("getMe")
    if not me.get("ok"):
        print(f"  [!] Token invalid: {me.get('error','?')}")
        sys.exit(1)
    bot_name = me["result"]["username"]
    print(f"  Bot     : @{bot_name}")

    offset = 0

    if not TELEGRAM_CHAT_ID:
        print("  TELEGRAM_CHAT_ID is unset; the bot will not auto-bind.")
        print("  Send any message to learn your chat_id from the log, then set TELEGRAM_CHAT_ID explicitly.")

    print("  Listening...\n")

    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                text = msg.get("text", "").strip()
                chat_id = str(msg.get("chat", {}).get("id", ""))

                if not text or not chat_id:
                    continue

                resolved_chat_id, should_process, notice = resolve_incoming_chat(TELEGRAM_CHAT_ID, chat_id)
                if notice:
                    level = "[!]" if should_process is False else "[i]"
                    print(f"  {level} {notice}")
                if not should_process:
                    continue

                ts = datetime.now().strftime("%H:%M:%S")
                print(f"  [{ts}] IN  : {text[:80]}")

                reply = dispatch(text)

                preview = reply[:100].replace("\n", " ")
                print(f"  [{ts}] OUT : {preview}{'...' if len(reply) > 100 else ''}")
                send_result = send_message(reply, resolved_chat_id)
                if send_result.get("ok"):
                    print(f"  [{ts}] SENT ({len(reply)} chars)\n")
                else:
                    print(f"  [{ts}] SEND FAILED ({send_result.get('sent_count', 0)}/{send_result.get('attempted_count', 0)} chunks)\n")

        except KeyboardInterrupt:
            print("\n  Stopped.")
            sys.exit(0)
        except Exception as e:
            print(f"  [!] Loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
