#!/usr/bin/env python3
"""
pi_mono_watch.py
----------------
Live terminal view for Pi-Mono batch status.

Polls the latest pi_mono_batch_status__*.json file in .agent/state/
and renders a clean status dashboard. Refreshes every POLL_INTERVAL seconds.
Exits automatically when overall_status is 'all_complete' or 'all_already_complete'.

Usage:
    python3 system_v4/skills/pi_mono_watch.py
    python3 system_v4/skills/pi_mono_watch.py --once   # single snapshot, no loop
    python3 system_v4/skills/pi_mono_watch.py --plan .agent/state/pi_mono_claude_launch_plan__wave2.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

POLL_INTERVAL = 5  # seconds
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = REPO_ROOT / ".agent" / "state"

STATUS_ICONS = {
    "complete": "✅",
    "launched": "🚀",
    "not_started": "⬜",
    "already_complete": "✅",
    "timeout": "⏱",
    "failed": "❌",
    "error": "❌",
}

OVERALL_DONE = {"all_complete", "all_already_complete"}
OVERALL_ERROR = {"has_errors", "has_timeouts"}
ACTIVE_STATES = {"launched"}

# Rotating heartbeat frames to show the dashboard is alive
HEARTBEAT_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# ANSI helpers — degrade gracefully on dumb terminals
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_RESET = "\033[0m"

OVERALL_COLORS = {
    "all_complete": _GREEN,
    "all_already_complete": _GREEN,
    "launched": _YELLOW,
    "not_started": _DIM,
    "has_errors": _RED,
    "has_timeouts": _RED,
}

STATUS_COLORS = {
    "complete": _GREEN,
    "already_complete": _GREEN,
    "launched": _YELLOW,
    "not_started": _DIM,
    "timeout": _RED,
    "failed": _RED,
    "error": _RED,
}


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


def find_latest_status_file(batch_id: str | None = None) -> Path | None:
    if batch_id:
        p = STATE_DIR / f"pi_mono_batch_status__{batch_id}.json"
        return p if p.exists() else None
    # find most recently modified status file
    candidates = sorted(
        STATE_DIR.glob("pi_mono_batch_status__*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _progress_bar(done: int, total: int, width: int = 20) -> str:
    if total == 0:
        return "░" * width
    filled = int(width * done / total)
    return "█" * filled + "░" * (width - filled)


def render(data: dict, status_path: Path, tick: int) -> str:
    batch_id = data.get("batch_id", "?")
    overall = data.get("overall_status", "?")
    updated = data.get("updated_at", "?")
    terminals = data.get("terminals", [])
    now_str = datetime.now().strftime("%H:%M:%S")
    heartbeat = HEARTBEAT_FRAMES[tick % len(HEARTBEAT_FRAMES)]
    oc = OVERALL_COLORS.get(overall, "")

    # Count summary
    n_total = len(terminals)
    n_active = sum(1 for t in terminals if t.get("status") in ACTIVE_STATES)
    n_done = sum(1 for t in terminals if t.get("status") in {"complete", "already_complete"})
    n_fail = sum(1 for t in terminals if t.get("status") in {"failed", "error", "timeout"})
    bar = _progress_bar(n_done, n_total)

    lines = []
    lines.append("")
    lines.append(f"  {_BOLD}{_CYAN}╔{'═' * 60}╗{_RESET}")
    lines.append(f"  {_BOLD}{_CYAN}║{_RESET}  {heartbeat}  {_BOLD}Pi-Mono Watch{_RESET}  │  batch: {_BOLD}{batch_id}{_RESET}")
    lines.append(f"  {_BOLD}{_CYAN}╚{'═' * 60}╝{_RESET}")
    lines.append("")
    lines.append(f"  Overall : {oc}{_BOLD}{overall}{_RESET}")
    lines.append(f"  Progress: {bar}  {n_done}/{n_total}")
    lines.append(f"  Active {_YELLOW}{n_active}{_RESET}  Done {_GREEN}{n_done}{_RESET}  Failed {_RED}{n_fail}{_RESET}")
    lines.append(f"  {_DIM}Written {updated}  │  Refreshed {now_str}  │  tick #{tick}{_RESET}")
    lines.append(f"  {_DIM}Source: {status_path.name}{_RESET}")
    lines.append(f"  {'─' * 58}")

    for t in terminals:
        tid = t.get("terminal_id", "?")
        st = t.get("status", "?")
        icon = STATUS_ICONS.get(st, "?")
        sc = STATUS_COLORS.get(st, "")
        # Pulse indicator for active terminals
        if st in ACTIVE_STATES:
            pulse = HEARTBEAT_FRAMES[tick % len(HEARTBEAT_FRAMES)]
            state_display = f"{sc}{_BOLD}{st}{_RESET} {pulse}"
        else:
            state_display = f"{sc}{st}{_RESET}"
        hf = t.get("handoff_file", "")
        hf_short = Path(hf).name if hf else "—"
        review_ok = f"{_GREEN}✓ review{_RESET}" if t.get("review_note_present") else f"{_DIM}· review{_RESET}"
        outputs_ok = f"{_GREEN}✓ outputs{_RESET}" if t.get("required_outputs_present") else f"{_DIM}· outputs{_RESET}"
        lines.append(f"  {icon}  {tid:<22}  {state_display}")
        lines.append(f"     {_DIM}{hf_short}{_RESET}  │  {review_ok}  {outputs_ok}")

    lines.append(f"  {'─' * 58}")
    lines.append(f"  {heartbeat} {_GREEN}alive{_RESET} │ refresh {POLL_INTERVAL}s │ {_DIM}Ctrl+C to exit{_RESET}")
    lines.append("")
    return "\n".join(lines)


def clear_screen() -> None:
    os.system("clear" if os.name != "nt" else "cls")


def watch(batch_id: str | None = None, once: bool = False) -> None:
    tick = 0
    notified_terminal = False  # fire notification at most once
    while True:
        status_path = find_latest_status_file(batch_id)
        timestamp = datetime.now().strftime("%H:%M:%S")
        heartbeat = HEARTBEAT_FRAMES[tick % len(HEARTBEAT_FRAMES)]

        if status_path is None:
            clear_screen()
            print(f"\n  {heartbeat} {_YELLOW}Waiting for status file...{_RESET}  [{timestamp}]")
            print(f"  {_DIM}Looking in: {STATE_DIR}{_RESET}")
            print(f"\n  {_DIM}Launch a batch first to generate a status file.{_RESET}")
        else:
            try:
                data = json.loads(status_path.read_text())
            except Exception as e:
                clear_screen()
                print(f"\n  {heartbeat} {_RED}Read error{_RESET} [{timestamp}]  {status_path.name}")
                print(f"  {_DIM}{e}{_RESET}")
            else:
                clear_screen()
                print(render(data, status_path, tick))
                overall = data.get("overall_status", "")
                if not notified_terminal and overall in OVERALL_DONE:
                    _notify("Pi-Mono Watch", "Batch complete — all tasks finished")
                    notified_terminal = True
                if not notified_terminal and overall in OVERALL_ERROR:
                    _notify("Pi-Mono Watch", f"Batch ended with status: {overall}")
                    notified_terminal = True
                if not once and overall in OVERALL_DONE:
                    print(f"  {_GREEN}{_BOLD}All done!{_RESET} {_DIM}(Ctrl+C to close){_RESET}")

        if once:
            return

        tick += 1
        try:
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\n  Watch interrupted.")
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="Pi-Mono batch status watcher")
    parser.add_argument("--plan", default=None, help="Path to launch plan JSON (to infer batch_id)")
    parser.add_argument("--batch-id", default=None, help="Explicit batch_id to watch")
    parser.add_argument("--once", action="store_true", help="Print once and exit (no loop)")
    args = parser.parse_args()

    batch_id = args.batch_id
    if batch_id is None and args.plan:
        try:
            plan = json.loads(Path(args.plan).read_text())
            batch_id = plan.get("batch_id")
        except Exception:
            pass

    watch(batch_id=batch_id, once=args.once)


if __name__ == "__main__":
    main()
