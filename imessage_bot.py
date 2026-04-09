#!/usr/bin/env python3
"""
iMessage <-> Codex Ratchet command interface.

Architecture (Codex audit 2026-04-08):
  1. Structured handlers run first — real subprocess execution, proof of work
  2. Claude summarizes handler output — read-only tools, no mutations
  3. Fallback for free-form questions — Claude with read-only tools only

Never allows Claude to write/edit/mutate repo files from a text message.
Uses the correct Python: PYTHON_BIN (codex-ratchet env, torch 2.11.0).

Usage:
    make imessage
"""

import glob
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────
DB_PATH        = os.path.expanduser("~/Library/Messages/chat.db")
PHONE_HANDLE   = "+17078673323"
EMAIL_HANDLE   = "joshua.eisenhart@gmail.com"
REPLY_HANDLE   = EMAIL_HANDLE
POLL_INTERVAL  = 10        # seconds between polls
CLAUDE_TIMEOUT = 240       # seconds for Claude summarization
SIM_TIMEOUT    = 300       # seconds for a sim run
CLAUDE_MODEL   = "sonnet"
PROJECT_DIR    = "/Users/joshuaeisenhart/Desktop/Codex Ratchet"
RESULTS_DIR    = os.path.join(PROJECT_DIR, "system_v4/probes/a2_state/sim_results")
PROBES_DIR     = os.path.join(PROJECT_DIR, "system_v4/probes")
LIVE_SPINE_PATH = os.path.join(RESULTS_DIR, "live_anchor_spine.json")
LEGO_AUDIT_PATH = os.path.join(RESULTS_DIR, "lego_stack_audit_results.json")
LEGO_COUPLING_PATH = os.path.join(RESULTS_DIR, "lego_coupling_candidates.json")
LEGO_QUEUE_PATH = os.path.join(RESULTS_DIR, "lego_batch_queue.json")
MAX_MSG_LEN    = 1500      # iMessage safe chunk size

# Correct Python — codex-ratchet env (torch 2.11.0, not homebrew 2.8.0)
PYTHON_BIN = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
MPLCONFIGDIR = "/tmp/codex-mpl"
NUMBA_CACHE_DIR = "/tmp/codex-numba"

# Tag every outgoing message so we never process our own replies
BOT_TAG = "\u200b"  # zero-width space — invisible but detectable

# ── Summarization prompt (read-only Claude) ───────────────────────────
SUMMARIZE_PROMPT = """You are a concise status reporter for the Codex Ratchet project.
You have been given output from a command that was already executed.
Summarize it for a phone screen. Rules:
- Plain text only. No markdown, no **, no ##.
- Short lines. Dashes for structure.
- Lead with the key result in the first line.
- Include: interpreter used, command run, pass/fail counts if present.
- Max 20 lines total.
- No follow-up lists. No status bars. No emoji menus. No "FOLLOW-UPS:".
- Do not say "I ran" — you did not run it. Report what the output shows."""

FREEFORM_PROMPT = """You are a read-only project status assistant for Codex Ratchet.
You can read files and answer questions. You cannot run sims or edit files.
Project dir: /Users/joshuaeisenhart/Desktop/Codex Ratchet
Results: system_v4/probes/a2_state/sim_results/
Sims: system_v4/probes/sim_*.py

Rules:
- Plain text only. Short lines. Dashes for structure.
- No markdown, no **, no ##, no follow-up templates, no status bars.
- Read actual files — do not guess.
- Never ask for clarification — answer from what you find.
- If a file is missing, say "not found" and stop."""


def _base_env():
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = MPLCONFIGDIR
    env["NUMBA_CACHE_DIR"] = NUMBA_CACHE_DIR
    return env


# ── Structured command handlers ───────────────────────────────────────

def _sim_allowlist():
    """Return set of valid sim basenames (without sim_ prefix and .py suffix)."""
    files = glob.glob(os.path.join(PROBES_DIR, "sim_*.py"))
    return {os.path.basename(f)[4:-3] for f in files}  # strip sim_ and .py


def _recommended_lego_sims():
    """Return recommended lego-first sim basenames from the machine audit."""
    if not os.path.exists(LEGO_AUDIT_PATH):
        return []
    try:
        with open(LEGO_AUDIT_PATH) as f:
            audit = json.load(f)
    except Exception:
        return []

    seen = set()
    names = []
    for probe_name in audit.get("recommended_lego_probes", []):
        if not probe_name.startswith("sim_") or not probe_name.endswith(".py"):
            continue
        name = probe_name[4:-3]
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


def handle_status(args):
    """'status' — summary of modified/new probe files."""
    r = subprocess.run(
        ["git", "status", "--short", "system_v4/probes/"],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=15, env=_base_env()
    )
    lines = r.stdout.strip().splitlines()
    if not lines:
        return "git status: no changes"
    modified = [l for l in lines if l.startswith(" M") or l.startswith("M")]
    new = [l for l in lines if l.startswith("??")]
    out = f"git status (probes): {len(lines)} changes\n"
    out += f"- modified: {len(modified)}\n"
    out += f"- untracked: {len(new)}\n"
    # Show first 8 modified files by name
    for l in modified[:8]:
        out += f"  {l.strip()}\n"
    if len(modified) > 8:
        out += f"  ...+{len(modified)-8} more\n"
    return out.strip()


def handle_audit(args):
    """'audit' — run the overclassification audit script."""
    script = os.path.join(PROBES_DIR, "audit_overclassification.py")
    r = subprocess.run(
        [PYTHON_BIN, script],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=60, env=_base_env()
    )
    out = (r.stdout + r.stderr).strip()
    verdict = "PASSED" if r.returncode == 0 else "FAILED"
    return f"audit {verdict} (rc={r.returncode}):\n{out[:800]}"


def handle_align(args):
    """'align' — run the controller alignment audit script."""
    script = os.path.join(PROBES_DIR, "controller_alignment_audit.py")
    r = subprocess.run(
        [PYTHON_BIN, script],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=90, env=_base_env()
    )
    out = (r.stdout + r.stderr).strip()
    verdict = "PASSED" if r.returncode == 0 else "FAILED"
    return f"align {verdict} (rc={r.returncode}):\n{out[:1000]}"


def handle_lego(args):
    """'lego' — run the lego-first backlog audit and summarize it."""
    script = os.path.join(PROBES_DIR, "lego_stack_audit.py")
    r = subprocess.run(
        [PYTHON_BIN, script],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=90, env=_base_env()
    )
    out = (r.stdout + r.stderr).strip()
    verdict = "PASSED" if r.returncode == 0 else "FAILED"
    return f"lego {verdict} (rc={r.returncode}):\n{out[:1000]}"


def handle_lego_coupling(args):
    """'lego-coupling' — run the lego -> coupling routing audit and summarize it."""
    script = os.path.join(PROBES_DIR, "lego_coupling_candidates.py")
    r = subprocess.run(
        [PYTHON_BIN, script],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=90, env=_base_env()
    )
    out = (r.stdout + r.stderr).strip()
    verdict = "PASSED" if r.returncode == 0 else "FAILED"
    return f"lego-coupling {verdict} (rc={r.returncode}):\n{out[:1000]}"


def handle_lego_queue(args):
    """'lego-queue' — run the lego execution queue builder and summarize it."""
    script = os.path.join(PROBES_DIR, "lego_batch_queue.py")
    r = subprocess.run(
        [PYTHON_BIN, script],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=90, env=_base_env()
    )
    out = (r.stdout + r.stderr).strip()
    verdict = "PASSED" if r.returncode == 0 else "FAILED"
    return f"lego-queue {verdict} (rc={r.returncode}):\n{out[:1000]}"


def handle_pairs(args):
    """'pairs' — summarize lego -> coupling candidates from the machine artifact."""
    if not os.path.exists(LEGO_COUPLING_PATH):
        return "lego coupling catalog not found; run 'lego-coupling' first"
    try:
        with open(LEGO_COUPLING_PATH) as f:
            data = json.load(f)
    except Exception as e:
        return f"lego coupling parse error: {e}"

    rows = data.get("rows", [])
    lines = [f"lego->coupling pairs: {len(rows)}"]
    for row in rows[:12]:
        lines.append(
            f"- {row.get('lego_family_id')}: {row.get('status')} -> "
            f"{row.get('coupling_probe') or row.get('existing_anchor') or 'none'}"
        )
    return "\n".join(lines)


def handle_queue(args):
    """'queue' — summarize the lego batch queue."""
    if not os.path.exists(LEGO_QUEUE_PATH):
        return "lego batch queue not found; run 'lego-queue' first"
    try:
        with open(LEGO_QUEUE_PATH) as f:
            data = json.load(f)
    except Exception as e:
        return f"lego batch queue parse error: {e}"

    rows = data.get("rows", [])
    lines = [f"lego batch queue: {len(rows)} tasks"]
    for row in rows[:12]:
        block = f" blocked_by={','.join(row.get('blocked_by', []))}" if row.get("blocked_by") else ""
        lines.append(
            f"- p{row.get('priority')} {row.get('lego_or_pair')}: "
            f"{'ready' if row.get('ready') else 'blocked'} -> {row.get('recommended_sim')}{block}"
        )
    return "\n".join(lines)


def handle_run(args):
    """'run <sim_name>' — execute a sim with the correct interpreter."""
    if not args:
        return "usage: run <sim_name>  (omit sim_ prefix and .py)"

    name = args.strip().removeprefix("sim_").removesuffix(".py")
    allowlist = _sim_allowlist()
    if name not in allowlist:
        close = [s for s in allowlist if name in s][:4]
        hint = f"  Did you mean: {', '.join(close)}" if close else ""
        return f"unknown sim: {name}{hint}\nrun 'sims' to list all."

    script = os.path.join(PROBES_DIR, f"sim_{name}.py")
    ts_start = datetime.now().strftime("%H:%M:%S")
    r = subprocess.run(
        [PYTHON_BIN, script],
        capture_output=True, text=True, cwd=PROJECT_DIR, timeout=SIM_TIMEOUT, env=_base_env()
    )
    ts_end = datetime.now().strftime("%H:%M:%S")
    out = (r.stdout + r.stderr).strip()

    proof = (
        f"[ran {ts_start}→{ts_end}]\n"
        f"interpreter: {PYTHON_BIN}\n"
        f"script: system_v4/probes/sim_{name}.py\n"
        f"exit: {r.returncode}\n"
        f"---\n"
    )
    return proof + out[:1200]


def handle_show(args):
    """'show <result_name>' — print result JSON summary."""
    if not args:
        return "usage: show <result_name>  (omit _results.json)"

    name = args.strip().removesuffix("_results.json").removesuffix(".json")
    # Try exact match then partial
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

    lines = [f"{fname}", f"- classification: {cls}", f"- passed: {passed}/{total}"]
    if isinstance(summary, dict):
        for k, v in list(summary.items())[:6]:
            if k not in ("passed", "pass", "total", "tests_run"):
                lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def handle_spine(args):
    """'spine' — compact view of current live anchor spine."""
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
    for row in rows[:18]:
        stage = row.get("stage", "?")
        name = row.get("result_json", "?")
        ready = "ready" if row.get("promotion_ready") else "risky"
        blockers = row.get("blockers", [])
        suffix = f" [{', '.join(blockers[:2])}]" if blockers else ""
        lines.append(f"- {stage}: {name} -> {ready}{suffix}")
    return "\n".join(lines)


def handle_failures(args):
    """'failures' — compact view of risky spine entries and exploratory branch."""
    if not os.path.exists(LIVE_SPINE_PATH):
        return "live anchor spine not found; run 'align' first"
    try:
        with open(LIVE_SPINE_PATH) as f:
            spine = json.load(f)
    except Exception as e:
        return f"failures parse error: {e}"

    rows = spine.get("rows", [])
    risky = [row for row in rows if not row.get("promotion_ready", False)]

    lines = [f"controller risks: {len(risky)} spine entries"]
    for row in risky[:10]:
        blockers = ", ".join(row.get("blockers", [])[:3]) or "unspecified"
        lines.append(f"- {row.get('stage')}: {row.get('result_json')} [{blockers}]")

    align_path = os.path.join(RESULTS_DIR, "controller_alignment_audit_results.json")
    if os.path.exists(align_path):
        try:
            audit = json.load(open(align_path))
            exploratory = audit.get("exploratory_branch", [])
            if exploratory:
                lines.append(f"exploratory branch: {len(exploratory)}")
                for row in exploratory[:6]:
                    lines.append(f"- {row.get('file')}: {row.get('classification')}")
        except Exception:
            pass

    return "\n".join(lines)


def handle_sims(args):
    """'sims [filter|all]' — recommended lego-first sims by default; raw corpus only on demand."""
    query = args.strip().lower()
    if query == "all":
        names = sorted(_sim_allowlist())
        return (
            f"{len(names)} raw sims exist.\n"
            "This is historical corpus, not a curated build-order list.\n"
            "Use 'sims' for recommended lego-first surfaces.\n"
            + "\n".join(names[:40])
        )

    names = _recommended_lego_sims()
    if not names:
        return "recommended lego sim catalog not found; run 'lego-audit' first"

    if query:
        names = [n for n in names if query in n.lower()]
        if not names:
            return f"no recommended lego sims matching '{args}'"
        return f"{len(names)} recommended lego sims matching '{args}':\n" + "\n".join(names[:40])

    return (
        f"{len(names)} recommended lego-first sims:\n"
        + "\n".join(names[:40])
        + "\nuse 'sims all' only if you want the raw uncurated corpus"
    )


def handle_result(args):
    """'result <sim_name>' — shortcut for show, using sim name."""
    name = args.strip().removeprefix("sim_").removesuffix(".py") if args else ""
    return handle_show(name)


def handle_log(args):
    """'log' — tail the bot's own log."""
    log_path = "/tmp/imessage_bot.log"
    if not os.path.exists(log_path):
        return "log not found at /tmp/imessage_bot.log"
    r = subprocess.run(["tail", "-30", log_path], capture_output=True, text=True, env=_base_env())
    return r.stdout.strip() or "(empty log)"


def handle_tools(args):
    """'tools' — summarize tool-stack coverage; 'tools run' reruns the omnibus check."""
    if args.strip().lower() == "run":
        script = os.path.join(PROBES_DIR, "sim_tools_load_bearing.py")
        r = subprocess.run(
            [PYTHON_BIN, script],
            capture_output=True, text=True, cwd=PROJECT_DIR, timeout=120, env=_base_env()
        )
        out = (r.stdout + r.stderr).strip()
        return f"tools check (rc={r.returncode}):\n{out[:800]}"

    align_path = os.path.join(RESULTS_DIR, "controller_alignment_audit_results.json")
    if not os.path.exists(align_path):
        return "tool summary not found; run 'align' first"

    try:
        with open(align_path) as f:
            audit = json.load(f)
    except Exception as e:
        return f"tool summary parse error: {e}"

    stack = audit.get("tool_stack_summary", {})
    per_tool = stack.get("per_tool", {})
    shallow = stack.get("shallow_tools", [])
    files = stack.get("files_with_manifest_or_depth", 0)

    lines = [f"tool stack over {files} result files"]
    if shallow:
        lines.append(f"shallow tools: {', '.join(shallow)}")
    for tool in ["pytorch", "z3", "sympy", "rustworkx", "xgi", "toponetx", "cvc5", "pyg", "e3nn", "geomstats", "gudhi"]:
        info = per_tool.get(tool, {})
        lines.append(
            f"- {tool}: tried {info.get('tried_count', 0)}, used {info.get('used_count', 0)}, "
            f"load-bearing {info.get('load_bearing_count', 0)}"
        )
    forcing = stack.get("forcing_targets", {})
    for tool in shallow[:4]:
        targets = forcing.get(tool) or []
        if targets:
            lines.append(f"- next {tool}: {', '.join(targets[:3])}")
    return "\n".join(lines)


# Handler registry — keyword → function
HANDLERS = {
    "status": handle_status,
    "audit":  handle_audit,
    "align":  handle_align,
    "lego":   handle_lego,
    "lego-coupling": handle_lego_coupling,
    "lego-queue": handle_lego_queue,
    "pairs": handle_pairs,
    "queue": handle_queue,
    "run":    handle_run,
    "show":   handle_show,
    "spine":  handle_spine,
    "failures": handle_failures,
    "result": handle_result,
    "sims":   handle_sims,
    "sim":    handle_sims,   # alias
    "log":    handle_log,
    "tools":  handle_tools,
    "help":   lambda _: "Commands: " + ", ".join(k for k in HANDLERS if k != "help") + "\nrun <name>, show <name>, sims [filter]",
}


def dispatch(text):
    """
    Route to a structured handler or fall back to Claude.
    Returns (reply_text, used_handler: bool).
    """
    stripped = text.strip()
    lower = stripped.lower()

    for keyword, fn in HANDLERS.items():
        if lower == keyword or lower.startswith(keyword + " "):
            args = stripped[len(keyword):].strip()
            try:
                result = fn(args)
            except subprocess.TimeoutExpired:
                result = f"(timed out running {keyword})"
            except Exception as e:
                result = f"(handler error: {e})"
            return result, True

    # No handler matched — use Claude (read-only)
    return None, False


# ── Claude (read-only summarizer / fallback) ──────────────────────────

def claude_summarize(command_output, original_question):
    """Ask Claude to summarize already-executed command output. No tools needed."""
    prompt = (
        f"Command output to summarize:\n\n{command_output}\n\n"
        f"Original question: {original_question}"
    )
    return _claude_call(prompt, SUMMARIZE_PROMPT, tools=None)  # no tools, just summarize text


def claude_freeform(question):
    """Handle free-form questions with Claude in read-only mode."""
    # Hard-block questions that should be handler commands — Claude answers from memory
    lower = question.lower()
    if any(w in lower for w in ("list sim", "what sim", "show sim", "sims", "which sim")):
        return "use 'sims' command for sim list"
    if any(w in lower for w in ("run sim", "run the sim", "execute")):
        return "use 'run <sim_name>' to execute a sim"
    if any(w in lower for w in ("status", "git status")):
        return "use 'status' command"
    return _claude_call(question, FREEFORM_PROMPT, tools="Read,Glob,Grep")


def _claude_call(prompt, system_prompt, tools):
    # --allowedTools requires prompt via stdin, not positional arg
    tool_args = ["--allowedTools", tools] if tools else []  # no flag = Claude answers from prompt text only
    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--model", CLAUDE_MODEL,
                "--effort", "high",
                "--system-prompt", system_prompt,
            ] + tool_args,
            input=prompt,          # always via stdin — works with and without --allowedTools
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            cwd=PROJECT_DIR,
            env=_base_env(),
        )
        out = result.stdout.strip()
        if result.returncode == 0 and out:
            return _strip_wizard(out)
        err = result.stderr.strip()
        return f"(Claude error rc={result.returncode}: {err[:200]})"
    except subprocess.TimeoutExpired:
        return f"(Claude timed out after {CLAUDE_TIMEOUT}s)"
    except FileNotFoundError:
        return "(claude CLI not found)"
    except Exception as e:
        return f"(Claude error: {str(e)[:150]})"


def _strip_wizard(text):
    """Remove wizard formatting artifacts that bleed from global CLAUDE.md."""
    # Strip FOLLOW-UPS block and everything after it (\n* not \n+ — catches first-line case)
    text = re.sub(r'\n*\*?\*?FOLLOW-UPS.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Strip STATUS bar line
    text = re.sub(r'\n*STATUS\s*[─\-]+.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Strip wizard emoji lines
    text = re.sub(r'\n*🧙.*', '', text)
    # Strip markdown bold
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # Strip ## headers
    text = re.sub(r'^#{1,3}\s+', '', text, flags=re.MULTILINE)
    return text.strip()


# ── SQLite helpers ────────────────────────────────────────────────────

def _db_connect():
    uri = f"file:{DB_PATH}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def get_last_rowid():
    try:
        conn = _db_connect()
        row = conn.execute("SELECT MAX(ROWID) FROM message").fetchone()
        conn.close()
        return row[0] if row and row[0] else 0
    except Exception as e:
        print(f"  [!] DB read error: {e}")
        return 0


def extract_text(text_col, abody_col):
    if text_col and text_col.strip():
        return text_col.strip()
    if abody_col:
        return _decode_attributed_body(bytes(abody_col))
    return ""


def _decode_attributed_body(blob):
    """NSTypedStream decoder — Messages attributedBody is NOT binary plist."""
    try:
        marker = b"NSString\x01"
        idx = blob.find(marker)
        if idx == -1:
            return ""
        pos = idx + len(marker) + 4  # skip 4 header bytes
        if pos >= len(blob):
            return ""
        length_byte = blob[pos]; pos += 1
        if length_byte == 0x81:
            length = blob[pos]; pos += 1
        elif length_byte == 0x82:
            length = int.from_bytes(blob[pos:pos+2], "big"); pos += 2
        elif length_byte == 0x83:
            length = int.from_bytes(blob[pos:pos+3], "big"); pos += 3
        else:
            length = length_byte
        if length == 0 or pos + length > len(blob):
            return ""
        return blob[pos:pos + length].decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


def get_new_messages(since_rowid):
    """
    Return list of (rowid, text) for inbound messages from our handles.
    No is_from_me filter — self-chat stores iPhone messages as is_from_me=1 on Mac.
    BOT_TAG (zero-width space) is the dedup guard.
    """
    try:
        conn = _db_connect()
        rows = conn.execute("""
            SELECT m.ROWID, m.text, m.attributedBody
            FROM message m
            LEFT JOIN handle h ON m.handle_id = h.ROWID
            WHERE m.ROWID > ?
              AND (h.id = ? OR h.id = ?)
            ORDER BY m.ROWID ASC
        """, (since_rowid, PHONE_HANDLE, EMAIL_HANDLE)).fetchall()
        conn.close()
    except Exception as e:
        print(f"  [!] DB query error: {e}")
        return []

    messages = []
    for rowid, text, abody in rows:
        content = extract_text(text, abody)
        if not content or BOT_TAG in content:
            continue
        messages.append((rowid, content))
    return messages


# ── iMessage sending ──────────────────────────────────────────────────

def send_imessage(text, handle=None):
    target = handle or REPLY_HANDLE
    for i, chunk in enumerate(split_message(text)):
        _send_chunk(chunk, target)
        if i > 0:
            time.sleep(1.2)


def _send_chunk(text, handle):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "")
    script = (
        f'tell application "Messages"\n'
        f'  set targetBuddy to buddy "{handle}" of (first service whose service type is iMessage)\n'
        f'  send "{escaped}" to targetBuddy\n'
        f'end tell'
    )
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, timeout=15)
        if r.returncode != 0:
            err = r.stderr.decode(errors="ignore").strip()
            print(f"  [!] AppleScript error: {err[:120]}")
    except subprocess.TimeoutExpired:
        print("  [!] AppleScript timed out")
    except Exception as e:
        print(f"  [!] Send failed: {e}")


def split_message(text):
    if len(text) <= MAX_MSG_LEN:
        return [text]
    chunks, current = [], ""
    for line in text.split("\n"):
        while len(line) > MAX_MSG_LEN:
            space = MAX_MSG_LEN - len(current)
            if space > 0:
                current += line[:space]
            chunks.append(current)
            current = ""
            line = line[space:]
        addition = line + "\n"
        if len(current) + len(addition) > MAX_MSG_LEN and current:
            chunks.append(current.rstrip())
            current = addition
        else:
            current += addition
    if current.strip():
        chunks.append(current.rstrip())
    return chunks or [text[:MAX_MSG_LEN]]


# ── Main loop ─────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Codex Ratchet — iMessage Command Interface")
    print(f"  Python  : {PYTHON_BIN}")
    print(f"  Watching: {PHONE_HANDLE}  |  {EMAIL_HANDLE}")
    print(f"  Replying: {REPLY_HANDLE}")
    print(f"  Poll    : every {POLL_INTERVAL}s  |  Sim timeout {SIM_TIMEOUT}s")
    print(f"  Model   : {CLAUDE_MODEL} (read-only summarization only)")
    print(f"  Handlers: {', '.join(HANDLERS)}")
    print("  Ctrl+C to stop")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"\n  [!] Messages DB not found: {DB_PATH}")
        print("  Grant Full Disk Access to Terminal in System Settings.")
        sys.exit(1)

    if not os.path.exists(PYTHON_BIN):
        print(f"\n  [!] Python not found: {PYTHON_BIN}")
        sys.exit(1)

    last_rowid = get_last_rowid()
    print(f"  Starting from ROWID {last_rowid}")
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] Listening...\n")

    cmds = ", ".join(k for k in HANDLERS if k not in ("sim", "help"))  # dedupe aliases
    send_imessage(f"{BOT_TAG}Codex bot online. Text 'help' for commands.")

    while True:
        try:
            new_msgs = get_new_messages(last_rowid)

            for rowid, text in new_msgs:
                last_rowid = rowid  # advance BEFORE processing to prevent re-processing

                ts = datetime.now().strftime("%H:%M:%S")
                print(f"  [{ts}] IN  : {text[:80]}")

                handler_output, used_handler = dispatch(text)

                if used_handler:
                    # Handler ran — only summarize if output exceeds phone limit
                    if len(handler_output) > MAX_MSG_LEN:
                        print(f"  [{ts}] summarizing handler output ({len(handler_output)} chars)...")
                        reply = claude_summarize(handler_output, text)
                    else:
                        reply = handler_output
                else:
                    # Free-form question — Claude reads files, no execution
                    print(f"  [{ts}] no handler matched, asking Claude (read-only)...")
                    reply = claude_freeform(text)

                preview = reply[:100].replace("\n", " ")
                print(f"  [{ts}] OUT : {preview}{'…' if len(reply) > 100 else ''}")
                send_imessage(BOT_TAG + reply)
                print(f"  [{ts}] SENT ({len(reply)} chars)\n")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n  Stopped.")
            sys.exit(0)
        except Exception as e:
            print(f"  [!] Loop error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
