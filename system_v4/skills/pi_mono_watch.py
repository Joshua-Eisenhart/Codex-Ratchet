#!/usr/bin/env python3
"""
pi_mono_watch.py
----------------
Live terminal view for Pi-Mono batch status.

Polls the latest pi_mono_batch_status__*.json file in .agent/state/
and renders a clean status dashboard. Refreshes every POLL_INTERVAL seconds.
Exits automatically when overall_status is 'all_complete' or 'all_already_complete'.

Usage:
    /opt/homebrew/bin/python3 system_v4/skills/pi_mono_watch.py
    /opt/homebrew/bin/python3 system_v4/skills/pi_mono_watch.py --once   # single snapshot, no loop
    /opt/homebrew/bin/python3 system_v4/skills/pi_mono_watch.py --plan .agent/state/pi_mono_claude_launch_plan__wave2.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
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


def render(data: dict, status_path: Path) -> str:
    batch_id = data.get("batch_id", "?")
    overall = data.get("overall_status", "?")
    updated = data.get("updated_at", "?")
    terminals = data.get("terminals", [])

    lines = []
    lines.append("=" * 64)
    lines.append(f"  Pi-Mono Watch  |  batch: {batch_id}")
    lines.append(f"  Overall: {overall}")
    lines.append(f"  Updated: {updated}")
    lines.append(f"  Source:  {status_path.name}")
    lines.append("-" * 64)

    for t in terminals:
        tid = t.get("terminal_id", "?")
        st = t.get("status", "?")
        icon = STATUS_ICONS.get(st, "?")
        hf = t.get("handoff_file", "")
        # shorten handoff path to just the filename
        hf_short = Path(hf).name if hf else "?"
        review_ok = "✓ review" if t.get("review_note_present") else "· review"
        outputs_ok = "✓ outputs" if t.get("required_outputs_present") else "· outputs"
        lines.append(f"  {icon}  {tid:<22}  [{st}]")
        lines.append(f"      {hf_short}")
        lines.append(f"      {review_ok}  {outputs_ok}")

    lines.append("=" * 64)
    lines.append(f"  [refreshing every {POLL_INTERVAL}s — Ctrl+C to exit]")
    return "\n".join(lines)


def clear_screen() -> None:
    os.system("clear" if os.name != "nt" else "cls")


def watch(batch_id: str | None = None, once: bool = False) -> None:
    while True:
        status_path = find_latest_status_file(batch_id)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if status_path is None:
            clear_screen()
            print(f"[{timestamp}] No status file found in {STATE_DIR}")
            print("Run the launcher first:")
            print("  /opt/homebrew/bin/python3 system_v4/skills/pi_mono_claude_batch_launcher.py \\")
            print("      --plan .agent/state/pi_mono_claude_launch_plan__wave2.json --mode dry-run")
        else:
            try:
                data = json.loads(status_path.read_text())
            except Exception as e:
                clear_screen()
                print(f"[{timestamp}] Error reading {status_path.name}: {e}")
            else:
                clear_screen()
                print(render(data, status_path))
                overall = data.get("overall_status", "")
                if not once and overall in OVERALL_DONE:
                    print(f"\n  All done! (Ctrl+C to close)")
                    # Keep displaying — don't exit so the user can see final state

        if once:
            return

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
