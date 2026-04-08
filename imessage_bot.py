#!/usr/bin/env python3
"""
iMessage <-> Claude Code project interface
Polls the local iMessage DB for commands from your phone,
runs them through Claude CLI with full project context,
and replies with detailed formatted reports via AppleScript.

Zero tokens consumed while idle. Only calls Claude when you text.

Usage:
    make imessage
    python3 imessage_bot.py
"""

import sqlite3
import subprocess
import time
import sys
import os
import plistlib
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────
DB_PATH       = os.path.expanduser("~/Library/Messages/chat.db")
PHONE_HANDLE  = "+17078673323"
EMAIL_HANDLE  = "joshua.eisenhart@gmail.com"
REPLY_HANDLE  = EMAIL_HANDLE
POLL_INTERVAL = 10        # seconds between polls
CLAUDE_TIMEOUT = 300      # seconds before giving up on Claude
CLAUDE_MODEL  = "sonnet"
PROJECT_DIR   = "/Users/joshuaeisenhart/Desktop/Codex Ratchet"
MAX_MSG_LEN   = 1500      # iMessage safe chunk size

# Tag every outgoing message so we never process our own replies
BOT_TAG = "\u200b"  # zero-width space — invisible but detectable

# ── System prompt ─────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are Claude Code running on Joshua's desktop Mac in the Codex Ratchet project directory.
You are a PROJECT COMMAND INTERFACE. Joshua is texting from his iPhone to run sims and get reports.

Project context:
- Constraint-admissibility geometry: distinguishability constraints are more fundamental than entropy summaries
- 5 candidate shells: Hopf torus (L1), Weyl chirality (L2), Phase damping (L3), Phi0 bridge (L4), Werner mixing (L5)
- Coupling program: shell-local legos -> pairwise coupling -> multi-shell coexistence -> topology variants -> emergence
- Tool stack: pytorch, z3 (UNSAT proofs), cvc5, sympy, clifford Cl(3)/Cl(6), geomstats, e3nn, rustworkx, XGI, TopoNetX, GUDHI, PyG
- Key result: L3 dephasing DESTROYS L1 Hopf topology; L4 bridge connects to base cluster only via L1/L2 corridor
- Status labels: exists / runs / passes local rerun / canonical by process

Your job:
- Run sims, check result JSONs, report status concisely
- When asked to run something, do it with /opt/homebrew/bin/python3
- For status, check actual files — do not guess
- Format for phone: short lines, plain text, dashes for structure, no markdown ** or ##
- No follow-up templates, no emoji menus, no status bars"""


# ── SQLite helpers ────────────────────────────────────────────────────

def _db_connect():
    """Open Messages DB read-only. WAL mode allows concurrent reads with Messages app."""
    uri = f"file:{DB_PATH}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def get_last_rowid():
    """Return the highest message ROWID currently in the DB."""
    try:
        conn = _db_connect()
        row = conn.execute("SELECT MAX(ROWID) FROM message").fetchone()
        conn.close()
        return row[0] if row and row[0] else 0
    except Exception as e:
        print(f"  [!] DB read error: {e}")
        return 0


def extract_text(text_col, abody_col):
    """Return plain text from message row. Handles both text and attributedBody."""
    if text_col and text_col.strip():
        return text_col.strip()
    if abody_col:
        return _decode_attributed_body(bytes(abody_col))
    return ""


def _decode_attributed_body(blob):
    """
    Decode NSAttributedString stored as binary plist.
    Falls back to stripping non-printable bytes if plist parse fails.
    """
    # Try binary plist decode first (most reliable)
    try:
        pl = plistlib.loads(blob, fmt=plistlib.FMT_BINARY)
        # The string lives at pl["$objects"][2] (or similar index) — find it
        if "$objects" in pl:
            for obj in pl["$objects"]:
                if isinstance(obj, str) and len(obj) > 0 and obj != "$null":
                    return obj.strip()
    except Exception:
        pass

    # Fallback: extract printable UTF-8 between NSString markers
    try:
        parts = blob.split(b"NSString\x94")
        if len(parts) > 1:
            raw = parts[1].split(b"NSDictionary")[0]
            candidate = raw.decode("utf-8", errors="ignore")
            text = "".join(c for c in candidate if c.isprintable() or c in "\n\t")
            if len(text.strip()) > 1:
                return text.strip()
    except Exception:
        pass

    return ""


def get_new_messages(since_rowid):
    """
    Return list of (rowid, text) for inbound messages from our handles
    that arrived after since_rowid. Filters out:
      - messages containing BOT_TAG (only valid dedup guard for self-chats,
        where ALL messages show is_from_me=1 regardless of sending device)
      - empty messages
    NOTE: is_from_me=0 filter intentionally omitted — iMessage self-chat
    stores iPhone-sent messages as is_from_me=1 on the Mac side.
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
        if not content:
            continue
        if BOT_TAG in content:
            continue
        messages.append((rowid, content))
    return messages


# ── Claude ────────────────────────────────────────────────────────────

def ask_claude(message_text):
    """Run the user's command through Claude CLI with full project context."""
    try:
        result = subprocess.run(
            [
                "claude", "-p",
                "--model", CLAUDE_MODEL,
                "--allowedTools", "Bash,Read,Glob,Grep,Write,Edit",
                "--system-prompt", SYSTEM_PROMPT,
                message_text,
            ],
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            cwd=PROJECT_DIR,
        )
        output = result.stdout.strip()
        if result.returncode == 0 and output:
            return output
        err = result.stderr.strip()
        return f"(Claude error rc={result.returncode}: {err[:300]})"
    except subprocess.TimeoutExpired:
        return f"(Timed out after {CLAUDE_TIMEOUT//60}min — try a narrower request)"
    except FileNotFoundError:
        return "(claude CLI not found — is it on PATH?)"
    except Exception as e:
        return f"(Error: {e!s:.200}"


# ── iMessage sending ──────────────────────────────────────────────────

def send_imessage(text, handle=None):
    """Send via AppleScript, chunking if needed."""
    target = handle or REPLY_HANDLE
    for i, chunk in enumerate(split_message(text)):
        _send_chunk(chunk, target)
        if i > 0:
            time.sleep(1.2)  # avoid bursting


def _send_chunk(text, handle):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "")
    script = (
        f'tell application "Messages"\n'
        f'  set targetBuddy to buddy "{handle}" of (first service whose service type is iMessage)\n'
        f'  send "{escaped}" to targetBuddy\n'
        f'end tell'
    )
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, timeout=15
        )
        if r.returncode != 0:
            err = r.stderr.decode(errors="ignore").strip()
            print(f"  [!] AppleScript error: {err[:120]}")
    except subprocess.TimeoutExpired:
        print("  [!] AppleScript timed out")
    except Exception as e:
        print(f"  [!] Send failed: {e}")


def split_message(text):
    """Split into chunks <= MAX_MSG_LEN, preferring newline boundaries."""
    if len(text) <= MAX_MSG_LEN:
        return [text]
    chunks, current = [], ""
    for line in text.split("\n"):
        # If a single line itself exceeds the limit, hard-split it
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
    print(f"  Watching : {PHONE_HANDLE}  |  {EMAIL_HANDLE}")
    print(f"  Replying : {REPLY_HANDLE}")
    print(f"  Poll     : every {POLL_INTERVAL}s  |  Timeout {CLAUDE_TIMEOUT}s")
    print(f"  Model    : {CLAUDE_MODEL}")
    print("  Ctrl+C to stop")
    print("=" * 60)

    # Sanity-check DB access
    if not os.path.exists(DB_PATH):
        print(f"\n  [!] Messages DB not found: {DB_PATH}")
        print("  Grant Full Disk Access to Terminal in System Settings.")
        sys.exit(1)

    last_rowid = get_last_rowid()
    print(f"  Starting from ROWID {last_rowid}")
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] Listening...\n")

    # Let the user know the bot is live
    send_imessage(f"{BOT_TAG}Codex bot online. Text a command.")

    while True:
        try:
            new_msgs = get_new_messages(last_rowid)

            for rowid, text in new_msgs:
                # ── CRITICAL: advance last_rowid BEFORE calling Claude ──
                # This prevents re-processing if Claude takes > POLL_INTERVAL
                last_rowid = rowid

                ts = datetime.now().strftime("%H:%M:%S")
                print(f"  [{ts}] IN  : {text[:80]}")
                print(f"  [{ts}] ...processing")

                reply = ask_claude(text)

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
