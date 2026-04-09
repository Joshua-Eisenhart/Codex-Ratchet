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
    python3 system_v4/skills/pi_mono_run.py
    python3 system_v4/skills/pi_mono_run.py --plan .agent/state/pi_mono_claude_launch_plan__current.json
    python3 system_v4/skills/pi_mono_run.py --no-view   # skip Terminal window
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

LIVE_NOTE_PATH = REPO_ROOT / ".agent" / "state" / "PI_MONO_LIVE_STATUS_NOTE__CURRENT.md"
CURRENT_STATUS_JSON = STATE_DIR / "pi_mono_batch_status__current.json"
CURRENT_STATUS_MD = STATE_DIR / "pi_mono_batch_status__current.md"

CLAUDE_FALLBACKS = [
    "/Users/joshuaeisenhart/.claude/local/claude",
    str(Path.home() / ".claude" / "local" / "claude"),
]


# ── Notifications ─────────────────────────────────────────────────────────────

def _notify(title: str, message: str) -> None:
    """Send a macOS notification via osascript. Fails silently."""
    try:
        subprocess.Popen(
            ["osascript", "-e",
             f'display notification "{message}" with title "{title}"'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


# ── Helpers ──────────────────────────────────────────────────────────────────

def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _archive_stale_current(new_batch_id: str) -> None:
    """If __current status files belong to a different batch, rename them as archives."""
    if CURRENT_STATUS_JSON.is_file():
        try:
            old = json.loads(CURRENT_STATUS_JSON.read_text())
            old_id = old.get("batch_id", "")
            if old_id and old_id != new_batch_id:
                archive_json = STATE_DIR / f"pi_mono_batch_status__{old_id}__archived.json"
                CURRENT_STATUS_JSON.rename(archive_json)
                print(f"[run] Archived stale __current.json → {archive_json.name}")
                archive_md = STATE_DIR / f"pi_mono_batch_status__{old_id}__archived.md"
                if CURRENT_STATUS_MD.is_file():
                    CURRENT_STATUS_MD.rename(archive_md)
                    print(f"[run] Archived stale __current.md → {archive_md.name}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"[run] Warning: could not archive stale __current: {e}")


def _sync_current_surfaces(batch_id: str, terminals: list[dict], overall: str) -> None:
    """Write the __current.json and __current.md surfaces from live state."""
    payload = {
        "batch_id": batch_id,
        "checked_at": _utc(),
        "dry_run": False,
        "overall_status": overall,
        "plan_errors": [],
        "terminals": [],
    }
    md_rows = []
    for t in terminals:
        tid = t.get("terminal_id", "?")
        hf = t.get("handoff_file", "")
        ern = t.get("expected_review_note", "")
        rnp = t.get("review_note_present", False)
        st = t.get("status", "?")
        notes = t.get("notes", "")
        payload["terminals"].append({
            "terminal_id": tid,
            "handoff_file": hf,
            "expected_review_note": ern,
            "handoff_file_exists": (REPO_ROOT / hf).is_file() if hf else False,
            "review_note_present": rnp,
            "status": st,
            "notes": notes,
        })
        md_rows.append(f"| {tid} | {(REPO_ROOT / hf).is_file() if hf else False} | {rnp} | {st} | {notes} |")

    try:
        CURRENT_STATUS_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    except OSError:
        pass
    try:
        md = (
            "# Pi-Mono Batch Status\n\n"
            f"- **batch_id**: `{batch_id}`\n"
            f"- **checked_at**: `{payload['checked_at']}`\n"
            f"- **overall_status**: `{overall}`\n"
            f"- **dry_run**: `false`\n\n"
            "## Terminals\n\n"
            "| terminal_id | handoff_exists | review_present | status | notes |\n"
            "|---|---|---|---|---|\n"
            + "\n".join(md_rows) + "\n"
        )
        CURRENT_STATUS_MD.write_text(md)
    except OSError:
        pass


def _write_live_note(batch_id: str, overall: str, terminals: list[dict]) -> None:
    """Write a short human-readable markdown status note."""
    icon = {"all_complete": "complete", "has_errors": "has errors",
            "has_timeouts": "has timeouts", "launched": "running",
            "not_started": "not started"}.get(overall, overall)
    lines = [
        "# Pi-Mono Live Status — Current",
        "",
        f"Date: {time.strftime('%Y-%m-%d')}",
        f"Updated: {_utc()}",
        "",
        f"## Batch: {batch_id}",
        f"Overall: **{icon}**",
        "",
        "## Tasks",
    ]
    for t in terminals:
        tid = t.get("terminal_id", "?")
        st = t.get("status", "?")
        note = t.get("notes", "")
        suffix = f" — {note}" if note else ""
        lines.append(f"- {tid}: `{st}`{suffix}")
    lines.append("")
    lines.append("## Status file")
    lines.append(f"- `.agent/state/pi_mono_batch_status__{batch_id}.json`")
    lines.append("")
    try:
        LIVE_NOTE_PATH.write_text("\n".join(lines) + "\n")
    except OSError:
        pass  # non-critical; don't break the run


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
    _write_live_note(batch_id, overall, terminals)
    _sync_current_surfaces(batch_id, terminals, overall)
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
    python = sys.executable
    cmd = f"cd '{REPO_ROOT}' && '{python}' '{watch_script}' --plan '{plan_path}'; echo ''; echo '\\033[1;32m=== Pi-Mono batch finished ===\\033[0m'; echo 'Press Enter to close this window.'; read"
    # Activate Terminal to bring it to front, then open the script in a new window
    script = (
        'tell application "Terminal"\n'
        f'  do script "{cmd}"\n'
        '  activate\n'
        'end tell'
    )
    try:
        subprocess.Popen(["osascript", "-e", script])
        print("[run] Opened status window in Terminal.app (brought to front)")
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
        _notify("Pi-Mono: Timeout", f"{tid} timed out after {timeout}s")
    elif proc.returncode != 0:
        msg = f"exit {proc.returncode}" + (f"; stderr: {stderr_out[:300]}" if stderr_out else "")
        print(f"[run] '{tid}': ERROR — {msg}")
        _update("error", msg)
        _notify("Pi-Mono: Error", f"{tid} failed — exit {proc.returncode}")
    else:
        print(f"[run] '{tid}': exited 0 but evidence not confirmed")
        _update("error", "exited 0 but review note / required outputs not found")
        _notify("Pi-Mono: Blocked", f"{tid} exited 0 but evidence missing")


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

    # Archive stale __current surfaces from a previous batch
    _archive_stale_current(batch_id)

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

    all_ok = all(s == "complete" for s in statuses)
    if all_ok:
        _notify("Pi-Mono: Batch Complete", f"All {len(statuses)} tasks finished successfully")
    else:
        failed = sum(1 for s in statuses if s in ("error", "timeout"))
        _notify("Pi-Mono: Batch Done", f"{failed}/{len(statuses)} tasks had errors or timeouts")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
