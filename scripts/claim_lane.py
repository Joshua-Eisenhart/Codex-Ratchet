#!/usr/bin/env python3
"""File-locked atomic row claim for docs/plans/lanes.md.

Usage:
    claim_lane.py claim <lane_id> <owner>
    claim_lane.py release <lane_id>
    claim_lane.py set-status <lane_id> <status> [--result-path PATH]
"""
from __future__ import annotations

import argparse
import fcntl
import re
import sys
from pathlib import Path

LANES = Path(__file__).resolve().parents[1] / "docs" / "plans" / "lanes.md"
VALID_STATUS = {
    "open", "in_progress", "runs",
    "passes local rerun", "canonical by process", "blocked",
}


def _rewrite_row(text: str, lane_id: str, *, owner: str | None, status: str | None,
                 result_path: str | None) -> str:
    pattern = re.compile(rf"^\| {re.escape(lane_id)} \|([^\n]*)$", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        raise SystemExit(f"lane id not found: {lane_id}")
    cells = [c.strip() for c in m.group(1).split("|")]
    # row layout: | id | <col1> | owner | status | result_path |
    # cells here is everything after the id cell, including trailing empty
    if len(cells) < 5:
        raise SystemExit(f"unexpected row shape for {lane_id}: {m.group(0)}")
    col1, cur_owner, cur_status, cur_result, *rest = cells
    new_owner = owner if owner is not None else cur_owner
    new_status = status if status is not None else cur_status
    new_result = result_path if result_path is not None else cur_result
    if new_status and new_status not in VALID_STATUS:
        raise SystemExit(f"invalid status: {new_status}")
    new_row = f"| {lane_id} | {col1} | {new_owner} | {new_status} | {new_result} |"
    return text[:m.start()] + new_row + text[m.end():]


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("claim"); c.add_argument("lane_id"); c.add_argument("owner")
    r = sub.add_parser("release"); r.add_argument("lane_id")
    s = sub.add_parser("set-status")
    s.add_argument("lane_id"); s.add_argument("status")
    s.add_argument("--result-path", default=None)
    args = ap.parse_args()

    with LANES.open("r+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        text = fh.read()
        if args.cmd == "claim":
            # refuse if already claimed
            m = re.search(rf"^\| {re.escape(args.lane_id)} \|[^|]*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|",
                          text, re.MULTILINE)
            if m and m.group(1).strip() and m.group(2).strip() not in ("", "open"):
                print(f"already claimed by {m.group(1).strip()} ({m.group(2).strip()})", file=sys.stderr)
                return 2
            text = _rewrite_row(text, args.lane_id, owner=args.owner,
                                status="in_progress", result_path=None)
        elif args.cmd == "release":
            text = _rewrite_row(text, args.lane_id, owner="", status="open", result_path="")
        elif args.cmd == "set-status":
            text = _rewrite_row(text, args.lane_id, owner=None,
                                status=args.status, result_path=args.result_path)
        fh.seek(0); fh.truncate(); fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
