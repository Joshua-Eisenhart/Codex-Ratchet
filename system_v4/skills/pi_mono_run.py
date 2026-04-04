#!/usr/bin/env python3
"""
pi_mono_run.py
--------------
One-command Pi-Mono runner.

- Reads a launch plan JSON
- Opens a new Terminal.app window showing live status (macOS only)
- Launches ALL tasks IN PARALLEL via claude -p subprocesses
- Polls for repo evidence (review note + required outputs)
- Writes status JSON after every update
- Exits when all tasks are complete, timed out, or errored

Usage:
    /opt/homebrew/bin/python3 system_v4/skills/pi_mono_run.py
    /opt/homebrew/bin/python3 system_v4/skills/pi_mono_run.py --plan .agent/state/pi_mono_claude_launch_plan__current.json
    /opt/homebrew/bin/python3 system_v4/skills/pi_mono_run.py --no-view   # skip Terminal window
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PLAN = REPO_ROOT / ".agent" / "state" / "pi_mono_claude_launch_plan__current.json"
STATE_DIR = REPO_ROOT / ".agent" / "state"

POLL_INTERVAL = 10       # seconds between evidence checks per task
DEFAULT_TIMEOUT = 900    # seconds per task

CLAUDE_FALLBACKS = [
    "/Users/joshuaeisenhart/.claude/local/claude",
    str(Path.home() / ".claude" / "local" / "claude"),
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_status(batch_id: str, terminals: list[dict]) -> Path:
    statuses = {t["status"] for t in terminals}
    if all(s == "complete" for s in statuses):
        overall = "all_complete"
    elif any(s == "error" for s in statuses):
        overall = "has_errors"
    elif any(s == "timeout" for s in statuses):
        overall = "has_timeouts"
    elif any(s == "launched" for s in statuses):
        overall = "launched"
    else:
        overall = "not_started"

    payload = {
        "batch_id": batch_id,
        "updated_at": _utc(),
        "overall_status": overall,
        "terminals": terminals,
    }
    out = STATE_DIR / f"pi_mono_batch_status__{batch_id}.json"
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    return out


def _evidence_complete(t: dict) -> bool:
    review = REPO_ROOT / t.get("expected_review_note", "")
    required = [REPO_ROOT / p for p in t.get("required_output_files", [])]
    return review.is_file() and all(p.is_file() for p in required)


def _find_claude() -> str | None:
    found = shutil.which("claude")
    if found:
        return found
    for fb in CLAUDE_FALLBACKS:
        p = Path(fb)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return None


# ── Open watch window ─────────────────────────────────────────────────────────

def _open_watch_window(plan_path: str) -> None:
    watch_script = str(REPO_ROOT / "system_v4" / "skills" / "pi_mono_watch.py")
    python = "/opt/homebrew/bin/python3"
    cmd = f"cd '{REPO_ROOT}' && {python} {watch_script} --plan '{plan_path}'; echo '[watch] done — press Enter to close'; read"
    try:
        subprocess.Popen([
            "osascript", "-e",
            f'tell application "Terminal" to do script "{cmd}"'
        ])
        print("[run] Opened status window in Terminal.app")
    except Exception as e:
        print(f"[run] Could not open Terminal.app window: {e}")
        print(f"[run] Run manually: {python} {watch_script} --plan {plan_path}")


# ── Per-task worker ───────────────────────────────────────────────────────────

def _run_task(t: dict, claude_bin: str, timeout: int,
              terminals: list[dict], lock: threading.Lock,
              batch_id: str) -> None:
    tid = t.get("terminal_id", "?")
    launcher = t.get("launcher_text", "").strip()

    def _update(status: str, notes: str = "") -> None:
        with lock:
            entry = next((x for x in terminals if x["terminal_id"] == tid), None)
            if entry:
                entry["status"] = status
                entry["notes"] = notes
                entry["review_note_present"] = (REPO_ROOT / t.get("expected_review_note", "")).is_file()
                entry["required_outputs_present"] = all(
                    (REPO_ROOT / p).is_file() for p in t.get("required_output_files", [])
                )
            _write_status(batch_id, terminals)

    # Already done?
    if _evidence_complete(t):
        print(f"[run] '{tid}': already complete — skipping")
        _update("complete", "repo evidence present before launch")
        return

    # Handoff exists?
    handoff = REPO_ROOT / t.get("handoff_file", "")
    if not handoff.is_file():
        print(f"[run] '{tid}': handoff missing — {handoff}")
        _update("error", f"handoff not found: {t.get('handoff_file')}")
        return

    print(f"[run] '{tid}': launching...")
    _update("launched")

    try:
        proc = subprocess.Popen(
            [claude_bin, "-p", launcher],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as e:
        print(f"[run] '{tid}': launch failed — {e}")
        _update("error", str(e))
        return

    print(f"[run] '{tid}': pid={proc.pid}, polling every {POLL_INTERVAL}s (timeout={timeout}s)")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        time.sleep(POLL_INTERVAL)
        if _evidence_complete(t):
            break

    try:
        _, stderr_out = proc.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        _, stderr_out = proc.communicate()

    if _evidence_complete(t):
        print(f"[run] '{tid}': COMPLETE ✓")
        _update("complete")
    elif time.monotonic() >= deadline:
        print(f"[run] '{tid}': TIMEOUT after {timeout}s")
        _update("timeout", f"timed out after {timeout}s — evidence not confirmed")
    elif proc.returncode != 0:
        msg = f"exit {proc.returncode}" + (f"; stderr: {stderr_out[:300]}" if stderr_out else "")
        print(f"[run] '{tid}': ERROR — {msg}")
        _update("error", msg)
    else:
        print(f"[run] '{tid}': exited 0 but evidence not confirmed")
        _update("error", "exited 0 but review note / required outputs not found")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Pi-Mono parallel runner")
    parser.add_argument("--plan", default=str(DEFAULT_PLAN), help="Path to launch plan JSON")
    parser.add_argument("--no-view", action="store_true", help="Skip opening Terminal watch window")
    args = parser.parse_args()

    plan_path = Path(args.plan)
    if not plan_path.is_absolute():
        plan_path = Path.cwd() / plan_path

    if not plan_path.is_file():
        print(f"[run] ERROR: plan not found: {plan_path}", file=sys.stderr)
        return 1

    try:
        plan = json.loads(plan_path.read_text())
    except Exception as e:
        print(f"[run] ERROR: could not parse plan: {e}", file=sys.stderr)
        return 1

    batch_id = str(plan.get("batch_id", "unknown")).strip()
    task_list = plan.get("terminals", [])
    timeout = int(plan.get("timeout_sec", DEFAULT_TIMEOUT))

    if not task_list:
        print("[run] ERROR: no terminals in plan", file=sys.stderr)
        return 1

    claude_bin = _find_claude()
    if not claude_bin:
        print("[run] ERROR: claude CLI not found", file=sys.stderr)
        return 1

    print(f"[run] batch={batch_id}  tasks={len(task_list)}  claude={claude_bin}")

    # Build initial terminal status entries
    lock = threading.Lock()
    terminals: list[dict] = []
    for t in task_list:
        terminals.append({
            "terminal_id": t.get("terminal_id", "?"),
            "status": "not_started",
            "handoff_file": t.get("handoff_file", ""),
            "expected_review_note": t.get("expected_review_note", ""),
            "review_note_present": False,
            "required_outputs_present": False,
            "notes": "",
        })

    status_path = _write_status(batch_id, terminals)
    print(f"[run] Status file: {status_path}")

    # Open watch window
    if not args.no_view:
        _open_watch_window(str(plan_path))
        time.sleep(1)  # let terminal open

    # Launch all tasks in parallel
    threads = []
    for t in task_list:
        th = threading.Thread(
            target=_run_task,
            args=(t, claude_bin, timeout, terminals, lock, batch_id),
            daemon=True,
        )
        threads.append(th)
        th.start()

    # Wait for all to finish
    for th in threads:
        th.join()

    # Final status
    statuses = [t["status"] for t in terminals]
    print(f"\n[run] All done. Statuses: {statuses}")
    _write_status(batch_id, terminals)

    return 0 if all(s == "complete" for s in statuses) else 1


if __name__ == "__main__":
    sys.exit(main())
