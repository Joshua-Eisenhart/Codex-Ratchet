#!/usr/bin/env python3
"""
Source-dirty stage plan generator.

Builds a machine-readable stage scope for the current executable lane. This
stays separate from git index mutation.
"""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
LANE_MANIFEST_PATH = RESULTS_DIR / "source_dirty_lane_manifest.json"
CHECKPOINT_PACKET_PATH = RESULTS_DIR / "source_dirty_checkpoint_packet.json"
OUT_PATH = RESULTS_DIR / "source_dirty_stage_plan.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain an object")
    return payload


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = read_json(LANE_MANIFEST_PATH)
    packet = read_json(CHECKPOINT_PACKET_PATH)

    owned_files = list(packet.get("owned_files", []))
    result_companions = list(packet.get("result_companions", []))
    stage_paths = owned_files + result_companions
    excluded_paths = [
        str((RESULTS_DIR / "source_dirty_checkpoint_plan.json").relative_to(PROJECT_DIR)),
        str((RESULTS_DIR / "source_dirty_lane_manifest.json").relative_to(PROJECT_DIR)),
        str((RESULTS_DIR / "source_dirty_checkpoint_packet.json").relative_to(PROJECT_DIR)),
        "system_v4/probes/source_dirty_checkpoint_plan.py",
        "system_v4/probes/source_dirty_lane_manifest.py",
        "system_v4/probes/source_dirty_checkpoint_packet.py",
        "system_v4/probes/source_dirty_stage_plan.py",
    ]

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "lane_id": manifest["lane_id"],
        "group_id": packet.get("group_id"),
        "selected_group_id": manifest.get("selected_group_id"),
        "summary": {
            "stage_path_count": len(stage_paths),
            "excluded_path_count": len(excluded_paths),
            "ready_for_staging": bool(packet.get("ready_for_checkpoint")) and bool(stage_paths),
            "ok": True,
            "status": "no_actionable_lane" if not packet.get("group_id") else "actionable_lane",
        },
        "stage_paths": stage_paths,
        "excluded_paths": excluded_paths,
        "rationale": {
            "include": "Stage executable-lane source files plus direct result companions refreshed by that same lane.",
            "exclude": "Leave planner/manifest/packet maintenance artifacts out of the lane checkpoint because they are transient controller state, not lane-owned work.",
        },
    }

    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"group_id={report['group_id']}")
    print(f"stage_path_count={report['summary']['stage_path_count']}")
    print("SOURCE DIRTY STAGE PLAN PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
