#!/usr/bin/env python3
"""
Source-dirty stage plan generator.

Builds a machine-readable stage scope for the current executable lane. This
stays separate from git index mutation.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
LANE_MANIFEST_PATH = RESULTS_DIR / "source_dirty_lane_manifest.json"
CHECKPOINT_PACKET_PATH = RESULTS_DIR / "source_dirty_checkpoint_packet.json"
OUT_PATH = RESULTS_DIR / "source_dirty_stage_plan.json"


def safe_suffix(group_id: str | None) -> str:
    if not group_id:
        return "no_actionable_lane"
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in group_id)


def parse_group_id(argv: list[str]) -> str | None:
    for idx, arg in enumerate(argv):
        if arg == "--group-id" and idx + 1 < len(argv):
            return argv[idx + 1]
    return None


def selected_manifest_path(group_id: str | None) -> Path:
    if not group_id:
        return LANE_MANIFEST_PATH
    return OUT_PATH.parent / f"source_dirty_lane_manifest__{safe_suffix(group_id)}.json"


def selected_packet_path(group_id: str | None) -> Path:
    if not group_id:
        return CHECKPOINT_PACKET_PATH
    return OUT_PATH.parent / f"source_dirty_checkpoint_packet__{safe_suffix(group_id)}.json"


def stage_plan_path_for(group_id: str | None) -> Path:
    if not group_id:
        return OUT_PATH.parent / "source_dirty_stage_plan__latest.json"
    return OUT_PATH.parent / f"source_dirty_stage_plan__{safe_suffix(group_id)}.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain an object")
    return payload


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    requested_group_id = parse_group_id(sys.argv[1:])
    manifest_path = selected_manifest_path(requested_group_id)
    packet_path = selected_packet_path(requested_group_id)
    manifest = read_json(manifest_path)
    packet = read_json(packet_path)

    owned_files = list(packet.get("owned_files", []))
    result_companions = list(packet.get("result_companions", []))
    stage_paths = owned_files + result_companions
    excluded_paths = [
        str((RESULTS_DIR / "source_dirty_checkpoint_plan.json").relative_to(PROJECT_DIR)),
        str((RESULTS_DIR / "source_dirty_lane_manifest.json").relative_to(PROJECT_DIR)),
        str((RESULTS_DIR / "source_dirty_checkpoint_packet.json").relative_to(PROJECT_DIR)),
    ]

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_manifest_path": str(manifest_path.relative_to(PROJECT_DIR)),
        "source_packet_path": str(packet_path.relative_to(PROJECT_DIR)),
        "latest_stage_plan_path": str(OUT_PATH.relative_to(PROJECT_DIR)),
        "lane_specific_stage_plan_path": str(stage_plan_path_for(packet.get("group_id")).relative_to(PROJECT_DIR)),
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
            "exclude": "Leave transient generated planning artifacts out of the lane checkpoint. Source maintenance scripts are included when they are part of the executable lane.",
        },
    }

    stage_plan_path = stage_plan_path_for(packet.get("group_id"))
    serialized = json.dumps(report, indent=2)
    OUT_PATH.write_text(serialized, encoding="utf-8")
    stage_plan_path.write_text(serialized, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {stage_plan_path}")
    print(f"group_id={report['group_id']}")
    print(f"stage_path_count={report['summary']['stage_path_count']}")
    print("SOURCE DIRTY STAGE PLAN PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
