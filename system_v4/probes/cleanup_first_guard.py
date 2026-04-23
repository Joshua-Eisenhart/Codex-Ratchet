#!/usr/bin/env python3
"""
Fail-closed guard for cleanup-first execution.

This is intentionally narrow: block new sim/tool execution while repository
hygiene is red, unless the caller opts in explicitly for maintenance work.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
SUPERVISOR_PATH = RESULTS_DIR / "system_hygiene_supervisor_results.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain an object")
    return payload


def parse_allow_dirty_repo(argv: list[str]) -> bool:
    return "--allow-dirty-repo" in argv


def parse_context(argv: list[str]) -> str:
    for idx, arg in enumerate(argv):
        if arg == "--context" and idx + 1 < len(argv):
            return argv[idx + 1]
    return "sim"


def main() -> int:
    argv = sys.argv[1:]
    allow_dirty_repo = parse_allow_dirty_repo(argv)
    context = parse_context(argv)

    if allow_dirty_repo:
        print(f"CLEANUP FIRST GUARD BYPASSED context={context}")
        return 0

    if not SUPERVISOR_PATH.exists():
        print(f"CLEANUP FIRST GUARD FAILED context={context}")
        print("missing supervisor surface; run `make maintenance-report` first")
        return 1

    supervisor = read_json(SUPERVISOR_PATH)
    repo_hygiene_green = bool(supervisor.get("repo_hygiene_green"))
    overall_green = bool(supervisor.get("overall_green"))
    repair_queue_count = int(supervisor.get("repair_queue_count", 0) or 0)
    active_actionable_lane = supervisor.get("active_actionable_lane") or {}

    if repo_hygiene_green and overall_green and repair_queue_count == 0:
        print(f"CLEANUP FIRST GUARD PASSED context={context}")
        return 0

    print(f"CLEANUP FIRST GUARD FAILED context={context}")
    print("cleanup-first policy is still active; cleanup/checkpoint work must happen before new sim execution")
    print(f"repo_hygiene_green={repo_hygiene_green}")
    print(f"overall_green={overall_green}")
    print(f"repair_queue_count={repair_queue_count}")
    if active_actionable_lane.get("group_id"):
        print(f"active_actionable_lane={active_actionable_lane['group_id']}")
    print(f"supervisor={SUPERVISOR_PATH.relative_to(PROJECT_DIR)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
