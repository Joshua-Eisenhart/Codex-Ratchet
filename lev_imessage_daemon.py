#!/usr/bin/env python3
"""lev_imessage_daemon.py — Codex Ratchet iMessage bridge."""
import sqlite3, json, time, subprocess, os, datetime, glob

DB      = os.path.expanduser("~/Library/Messages/chat.db")
QUEUE   = "/tmp/lev_imessage_queue.json"
STATE   = "/tmp/lev_imessage_state.json"
SIGNAL  = "/tmp/lev_imessage_signal"
LOG     = "/tmp/lev_imessage_daemon.log"
CONTACT = "joshua.eisenhart@gmail.com"
POLL    = 20
REPO    = os.path.expanduser("~/Desktop/Codex Ratchet")

def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    with open(LOG, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def send_imessage(text):
    safe = text.replace('"', '\\"').replace("\\", "\\\\")
    script = f'''tell application "Messages"
    set svc to 1st service whose service type = iMessage
    set buddy to buddy "{CONTACT}" of svc
    send "{safe}" to buddy
end tell'''
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
    except Exception as e:
        log(f"Send error: {e}")

def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {"last_rowid": 0}

def save_state(state):
    json.dump(state, open(STATE, "w"))

def load_queue():
    try:
        return json.load(open(QUEUE))
    except Exception:
        return []

def save_queue(q):
    json.dump(q, open(QUEUE, "w"), indent=2)

def touch_signal():
    with open(SIGNAL, "w") as f:
        f.write(str(time.time()))

def get_new_messages(last_rowid):
    try:
        conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT m.rowid, m.text, m.is_from_me,
                   CAST((m.date / 1000000000) + 978307200 AS INTEGER) AS timestamp
            FROM message m
            JOIN chat_message_join cmj ON cmj.message_id = m.rowid
            JOIN chat c ON c.rowid = cmj.chat_id
            JOIN chat_handle_join chj ON chj.chat_id = c.rowid
            JOIN handle h ON h.rowid = chj.handle_id
            WHERE h.id = ? AND m.rowid > ?
              AND m.text IS NOT NULL AND m.text != ''
            ORDER BY m.rowid ASC
        """, (CONTACT, last_rowid))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        log(f"DB error: {e}")
        return []

def handle_command(text):
    t = text.strip().lower()
    if t == "help":
        return ("[LEV-BOT] 🧙🏽‍♂️🪄 Commands:\n"
                "  help   — this menu\n"
                "  status — git log + sim count\n"
                "  sims   — lego sim file count\n"
                "  last   — last queued message\n"
                "  ping   — pong")
    if t == "ping":
        return "[LEV-BOT] 🏓 pong"
    if t == "status":
        try:
            r = subprocess.run(
                ["git", "-C", REPO, "log", "--oneline", "-5"],
                capture_output=True, text=True, timeout=10)
            n = len(glob.glob(os.path.join(REPO, "system_v4/probes/sim_lego_*.py")))
            return f"[LEV-BOT] 📊 Last 5 commits:\n{r.stdout.strip()}\n🔬 {n} sim_lego files"
        except Exception as e:
            return f"[LEV-BOT] ❌ status error: {e}"
    if t == "sims":
        n = len(glob.glob(os.path.join(REPO, "system_v4/probes/sim_lego_*.py")))
        return f"[LEV-BOT] 🔬 {n} sim_lego_*.py files found"
    if t == "last":
        q = load_queue()
        if q:
            m = q[-1]
            return f"[LEV-BOT] 📬 [{m.get('rowid')}] {(m.get('text') or '')[:100]}"
        return "[LEV-BOT] 📭 Queue empty"
    return None

def main():
    log("Daemon starting (rebuilt 2026-04-17)")
    state = load_state()
    send_imessage("🧙🏽‍♂️ [LEV-BOT] Codex bot online. Text 'help' for commands.")

    while True:
        try:
            msgs = get_new_messages(state["last_rowid"])
            if msgs:
                q = load_queue()
                q.extend(msgs)
                if len(q) > 1000:
                    q = q[-1000:]
                save_queue(q)
                touch_signal()
                for m in msgs:
                    direction = "Me" if m["is_from_me"] else "User"
                    log(f"{direction} [{m['rowid']}]: {(m.get('text') or '')[:80]}")
                    if not m["is_from_me"] and m.get("text"):
                        reply = handle_command(m["text"])
                        if reply:
                            send_imessage(reply)
                state["last_rowid"] = msgs[-1]["rowid"]
                save_state(state)
                log(f"Queued {len(msgs)} message(s), signal written")
        except Exception as e:
            log(f"Loop error: {e}")
        time.sleep(POLL)

if __name__ == "__main__":
    main()
