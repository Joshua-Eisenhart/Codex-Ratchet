#!/usr/bin/env python3
"""
System hygiene repair.

Safe, bounded self-repair for low-risk hygiene issues:
  - quarantine root-level orphan result JSONs
  - optionally quarantine unique JSONs from the legacy secondary result root

This script never deletes, never overwrites, and never touches ambiguous
duplicate basenames or runtime state directories.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
REPO_AUDIT_PATH = RESULTS_DIR / "repo_hygiene_audit_results.json"
OUT_PATH = RESULTS_DIR / "system_hygiene_repair_results.json"
SECONDARY_RESULTS_DIR = SCRIPT_DIR / "sim_results"
QUARANTINE_ROOT = PROJECT_DIR / "work" / "hygiene_quarantine"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain an object")
    return payload


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_DIR))


def plan_move(source: Path, destination_root: Path, reason: str) -> dict[str, Any]:
    return {
        "reason": reason,
        "source": rel(source),
        "destination": rel(destination_root / source.name),
        "safe_auto": True,
        "will_apply": False,
    }


def main() -> int:
    apply = "--apply" in sys.argv[1:]
    include_secondary_unique = "--include-secondary-unique" in sys.argv[1:]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    repo_audit = read_json(REPO_AUDIT_PATH)

    run_tag = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root_quarantine = QUARANTINE_ROOT / "root_result_orphans" / run_tag
    secondary_quarantine = QUARANTINE_ROOT / "secondary_unique_results" / run_tag

    planned_actions: list[dict[str, Any]] = []
    blocked_actions: list[dict[str, Any]] = []

    for name in repo_audit.get("root_result_files", []):
        source = PROJECT_DIR / name
        destination = root_quarantine / name
        if not source.exists():
            blocked_actions.append({
                "reason": "missing_source",
                "source": name,
                "destination": rel(destination),
            })
            continue
        if destination.exists():
            blocked_actions.append({
                "reason": "destination_exists",
                "source": name,
                "destination": rel(destination),
            })
            continue
        planned_actions.append(plan_move(source, root_quarantine, "root_result_json_orphans"))

    if include_secondary_unique:
        for name in repo_audit.get("secondary_unique_results", []):
            source = SECONDARY_RESULTS_DIR / name
            destination = secondary_quarantine / name
            if not source.exists():
                blocked_actions.append({
                    "reason": "missing_source",
                    "source": rel(source),
                    "destination": rel(destination),
                })
                continue
            if destination.exists():
                blocked_actions.append({
                    "reason": "destination_exists",
                    "source": rel(source),
                    "destination": rel(destination),
                })
                continue
            action = plan_move(source, secondary_quarantine, "secondary_unique_results")
            action["opt_in_only"] = True
            planned_actions.append(action)

    applied_count = 0
    if apply and blocked_actions:
        outcome = "blocked"
    elif apply:
        for action in planned_actions:
            source = PROJECT_DIR / action["source"]
            destination = PROJECT_DIR / action["destination"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            action["will_apply"] = True
            applied_count += 1
        outcome = "applied"
    else:
        outcome = "dry_run"

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "apply": apply,
        "include_secondary_unique": include_secondary_unique,
        "outcome": outcome,
        "summary": {
            "planned_action_count": len(planned_actions),
            "blocked_action_count": len(blocked_actions),
            "applied_action_count": applied_count,
            "ok": (not apply) or (apply and not blocked_actions),
        },
        "quarantine_roots": {
            "root_result_orphans": rel(root_quarantine),
            "secondary_unique_results": rel(secondary_quarantine),
        },
        "planned_actions": planned_actions,
        "blocked_actions": blocked_actions,
    }

    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"planned_action_count={report['summary']['planned_action_count']}")
    print(f"blocked_action_count={report['summary']['blocked_action_count']}")
    print(f"applied_action_count={report['summary']['applied_action_count']}")

    if apply and blocked_actions:
        print("SYSTEM HYGIENE REPAIR FAILED")
        return 1

    print("SYSTEM HYGIENE REPAIR PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
