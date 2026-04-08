#!/usr/bin/env python3
"""
iMessage <-> Claude Code project interface
Polls the local iMessage DB for commands from your phone,
runs them through Claude CLI with full project context,
and replies with detailed formatted reports via AppleScript.

Zero tokens consumed while idle. Only calls Claude when you text.
"""

import sqlite3
import subprocess
import time
import sys
import os
import json
from datetime import datetime

# Config
DB_PATH = os.path.expanduser("~/Library/Messages/chat.db")
PHONE_HANDLE = "+17078673323"
EMAIL_HANDLE = "joshua.eisenhart@gmail.com"
REPLY_HANDLE = EMAIL_HANDLE  # which thread to reply on
POLL_INTERVAL = 10  # seconds
CLAUDE_MODEL = "sonnet"
BOT_TAG = "\u200b"  # zero-width space to tag bot replies
PROJECT_DIR = "/Users/joshuaeisenhart/Desktop/Codex Ratchet"
MAX_MSG_LEN = 1500  # split long replies into chunks for iMessage

# System prompt — project command interface, not chatbot
SYSTEM_PROMPT = """You are Claude Code running on Joshua's desktop Mac in the Codex Ratchet project directory.
You are a PROJECT COMMAND INTERFACE, not a chatbot. Joshua is texting you from his iPhone to manage sims and get reports.

Your job:
- Run simulations, check results, report status with full detail
- When asked to "run the next batch" or similar, execute the appropriate scripts
- Give well-formatted reports: use line breaks, sections, bullet points, numbers
- No character limit. Be thorough. Format for readability on a phone screen.
- If a sim completes, summarize results AND suggest what to run next
- If asked for status, check actual files/logs, don't guess

You have access to Bash. The project uses: z3 proofs, PyG graphs, TopoNetX topology,
Cl(3)/Cl(6) rotors, 19-layer tool ladder, L0 bifurcation (34 spectral + 19 geometric legos).
PyTorch IS the ratchet architecture: forward=possibilities, backward=constraints, graph=manifold.

Do NOT include follow-up templates, status lines, progress bars, or emoji menus.
Do NOT use markdown formatting like ** or ## — use plain text with line breaks and dashes for structure."""


def get_last_rowid():
    """Get the most recent message ROWID."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT MAX(ROWID) FROM message")
    row = cur.fetchone()
    conn.close()
    return row[0] if row[0] else 0


def extract_text_from_attributed_body(blob):
    """Extract plain text from NSAttributedString blob."""
    try:
        data = bytes(blob)
        parts = data.split(b'NSString')
        if len(parts) > 1:
            raw = parts[1].split(b'NSDictionary')[0]
            text = raw.decode('utf-8', errors='ignore')
            return ''.join(c for c in text if c.isprintable() or c in '\n\t').strip()
    except Exception:
        pass
    return ""


def get_new_messages(since_rowid):
    """Fetch new messages from self-conversation handles."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT m.ROWID, m.text, m.attributedBody, m.is_from_me, h.id as handle
        FROM message m
        LEFT JOIN handle h ON m.handle_id = h.ROWID
        WHERE m.ROWID > ?
          AND (h.id = ? OR h.id = ?)
        ORDER BY m.ROWID ASC
    """, (since_rowid, PHONE_HANDLE, EMAIL_HANDLE))
    raw_messages = cur.fetchall()
    conn.close()

    messages = []
    for rowid, text, abody, is_from_me, handle in raw_messages:
        msg_text = text or ""
        if not msg_text.strip() and abody:
            msg_text = extract_text_from_attributed_body(abody)
        if not msg_text.strip():
            continue
        if BOT_TAG in msg_text:
            continue
        messages.append((rowid, msg_text, is_from_me, handle))
    return messages


def ask_claude(message_text):
    """Send a command to Claude CLI with full project context and tool access."""
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", CLAUDE_MODEL,
             "--allowedTools", "Bash,Read,Glob,Grep",
             "--system-prompt", SYSTEM_PROMPT,
             message_text],
            capture_output=True, text=True, timeout=300,
            cwd=PROJECT_DIR
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            return f"(Claude error: {result.stderr.strip()[:200]})"
    except subprocess.TimeoutExpired:
        return "(Claude timed out after 5min — try a more specific request)"
    except Exception as e:
        return f"(Error: {str(e)[:200]})"


def send_imessage(text, handle=None):
    """Send an iMessage via AppleScript. Splits long messages."""
    if handle is None:
        handle = REPLY_HANDLE
    chunks = split_message(text)
    for chunk in chunks:
        escaped = chunk.replace('\\', '\\\\').replace('"', '\\"')
        script = f'tell application "Messages" to send "{escaped}" to buddy "{handle}" of (first service whose service type is iMessage)'
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
            if len(chunks) > 1:
                time.sleep(1)  # small delay between chunks
        except Exception as e:
            print(f"  [!] Send failed: {e}")


def split_message(text):
    """Split long text into iMessage-friendly chunks at line breaks."""
    if len(text) <= MAX_MSG_LEN:
        return [text]
    chunks = []
    current = ""
    for line in text.split('\n'):
        if len(current) + len(line) + 1 > MAX_MSG_LEN and current:
            chunks.append(current.strip())
            current = line + '\n'
        else:
            current += line + '\n'
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text[:MAX_MSG_LEN]]


def main():
    print("=" * 60)
    print("  Codex Ratchet — iMessage Command Interface")
    print(f"  Watching: {PHONE_HANDLE} + {EMAIL_HANDLE}")
    print(f"  Replying on: {REPLY_HANDLE}")
    print(f"  Polling every {POLL_INTERVAL}s | Timeout 5min")
    print(f"  Model: {CLAUDE_MODEL}")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    last_rowid = get_last_rowid()
    print(f"  Starting from ROWID: {last_rowid}")
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] Listening...\n")

    while True:
        try:
            new_msgs = get_new_messages(last_rowid)

            for rowid, text, is_from_me, handle in new_msgs:
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"  [{timestamp}] 📱 Command: {text}")

                print(f"  [{timestamp}] 🔧 Processing...")
                reply = ask_claude(text)
                preview = reply[:120].replace('\n', ' ')
                print(f"  [{timestamp}] 📋 Reply: {preview}{'...' if len(reply) > 120 else ''}")

                send_imessage(BOT_TAG + reply)
                print(f"  [{timestamp}] ✅ Sent ({len(reply)} chars)\n")

            current_max = get_last_rowid()
            if current_max > last_rowid:
                last_rowid = current_max

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n  Interface stopped.")
            sys.exit(0)
        except Exception as e:
            print(f"  [!] Error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
