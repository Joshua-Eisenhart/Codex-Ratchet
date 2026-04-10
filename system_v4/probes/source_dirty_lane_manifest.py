#!/usr/bin/env python3
"""
Source-dirty lane manifest generator.

Builds one machine-readable execution manifest for a single checkpoint-ready
source-dirty group. Defaults to the top recommended checkpoint group but
supports explicit group selection.
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
PLAN_PATH = RESULTS_DIR / "source_dirty_checkpoint_plan.json"
OUT_PATH = RESULTS_DIR / "source_dirty_lane_manifest.json"

DEFAULT_VERIFY_COMMANDS = [
    "make source-dirty-checkpoint-plan",
    "make maintenance-report",
]


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain an object")
    return payload


def parse_group_id(argv: list[str]) -> str | None:
    for idx, arg in enumerate(argv):
        if arg == "--group-id" and idx + 1 < len(argv):
            return argv[idx + 1]
    return None


def parse_allow_docs(argv: list[str]) -> bool:
    return "--allow-docs" in argv


def result_companion_for(source_rel: str) -> str | None:
    path = Path(source_rel)
    if path.parent.name != "probes" or not path.name.startswith("sim_"):
        return None
    stem = path.stem[len("sim_") :]
    return f"system_v4/probes/a2_state/sim_results/{stem}_results.json"


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    plan = read_json(PLAN_PATH)
    argv = sys.argv[1:]
    requested_group_id = parse_group_id(argv)
    allow_docs = parse_allow_docs(argv)
    code_only_fallback = plan.get("next_code_only_manual")

    checkpoint_groups = {
        group["group_id"]: group
        for group in plan.get("checkpoint_groups", [])
        if group.get("safe_next_action") == "checkpoint"
    }
    recommended = plan.get("recommended_checkpoint_order", [])

    if requested_group_id:
        selected = checkpoint_groups.get(requested_group_id)
        if selected is None:
            raise SystemExit(f"unknown or non-checkpoint group_id: {requested_group_id}")
        selection_mode = "explicit"
        docs_opt_in_required = False
    else:
        if not recommended:
            # No checkpoint-ready groups — all remaining source pressure is manual-only.
            # This is the success state after a cleanup pass. Write a no-op result and exit 0.
            OUT_PATH.write_text(json.dumps({
                "generated_at": datetime.now(UTC).isoformat(),
                "lane_id": "source_dirty__no_actionable_lanes",
                "source_plan_path": str(PLAN_PATH.relative_to(PROJECT_DIR)),
                "selection_mode": "no_checkpoint_ready_groups",
                "allow_docs": allow_docs,
                "docs_opt_in_required": False,
                "code_only_fallback": code_only_fallback,
                "active_actionable_lane": None,
                "selected_group_id": None,
                "file_count": 0,
                "safe_next_action": None,
                "stop_condition": "No checkpoint-ready lanes remain; manual-only residue must be audited separately.",
                "code_only_fallback_group_id": code_only_fallback["group_id"] if code_only_fallback else None,
                "active_actionable_lane_group_id": None,
                "summary": {
                    "selected_group_id": None,
                    "file_count": 0,
                    "safe_next_action": None,
                    "docs_opt_in_required": False,
                    "code_only_fallback_group_id": code_only_fallback["group_id"] if code_only_fallback else None,
                    "active_actionable_lane_group_id": None,
                    "executable_lane_group_id": None,
                    "ok": True,
                    "status": "no_actionable_lanes",
                    "note": "No checkpoint-ready groups; all remaining source pressure is manual-only or clean.",
                },
                "lane": None,
                "executable_lane": None,
            }, indent=2), encoding="utf-8")
            print(f"Wrote {OUT_PATH}")
            print("selected_group_id=None (no checkpoint-ready groups)")
            print("file_count=0")
            print("SOURCE DIRTY LANE MANIFEST PASSED (no actionable lanes — clean state)")
            return 0
        filtered_recommended = [
            item for item in recommended
            if allow_docs or checkpoint_groups[item["group_id"]].get("bucket") != "docs_and_specs"
        ]
        docs_opt_in_required = False
        if filtered_recommended:
            probe_recommended = [
                item for item in filtered_recommended
                if checkpoint_groups[item["group_id"]].get("bucket") == "probe_source"
            ]
            chosen = probe_recommended[0] if probe_recommended else filtered_recommended[0]
            selected = checkpoint_groups[chosen["group_id"]]
            selection_mode = "default_prefer_probe_source_skip_docs" if not allow_docs else "default_prefer_probe_source"
        else:
            chosen = recommended[0]
            selected = checkpoint_groups[chosen["group_id"]]
            selection_mode = "default_docs_blocked_requires_opt_in"
            docs_opt_in_required = True
    files = list(selected["sample_paths"])
    result_companions = [p for p in (result_companion_for(f) for f in files) if p]
    required_git_paths_clean = files + result_companions
    active_actionable_lane = code_only_fallback if docs_opt_in_required else {
        "group_id": selected["group_id"],
        "file_count": selected["file_count"],
        "safe_next_action": selected["safe_next_action"],
        "selection_mode": selection_mode,
    }
    if active_actionable_lane and code_only_fallback and docs_opt_in_required:
        active_actionable_lane = {
            **active_actionable_lane,
            "source_path": code_only_fallback.get("source_path"),
            "result_path": code_only_fallback.get("result_path"),
        }
    elif active_actionable_lane:
        active_actionable_lane = {
            **active_actionable_lane,
            "source_path": files[0] if len(files) == 1 else None,
            "result_path": result_companions[0] if len(result_companions) == 1 else None,
        }
    executable_lane = {
        "group_id": active_actionable_lane["group_id"] if active_actionable_lane else selected["group_id"],
        "files": [active_actionable_lane["source_path"]] if active_actionable_lane and active_actionable_lane.get("source_path") else files,
        "result_companions": [active_actionable_lane["result_path"]] if active_actionable_lane and active_actionable_lane.get("result_path") else result_companions,
        "required_git_paths_clean": (
            [active_actionable_lane["source_path"], active_actionable_lane["result_path"]]
            if active_actionable_lane and active_actionable_lane.get("source_path") and active_actionable_lane.get("result_path")
            else required_git_paths_clean
        ),
        "goal": "Execute the currently actionable bounded lane without widening scope.",
        "stop_condition": "All files in this executable lane are either checkpointed together or intentionally reclassified in the checkpoint plan.",
    }

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "lane_id": f"source_dirty__{selected['group_id']}",
        "source_plan_path": str(PLAN_PATH.relative_to(PROJECT_DIR)),
        "selection_mode": selection_mode,
        "allow_docs": allow_docs,
        "docs_opt_in_required": docs_opt_in_required,
        "code_only_fallback": code_only_fallback,
        "code_only_fallback_group_id": code_only_fallback["group_id"] if code_only_fallback else None,
        "active_actionable_lane": active_actionable_lane,
        "selected_group_id": selected["group_id"],
        "file_count": selected["file_count"],
        "safe_next_action": selected["safe_next_action"],
        "stop_condition": "All files in this lane are either checkpointed together or intentionally reclassified in the checkpoint plan.",
        "summary": {
            "selected_group_id": selected["group_id"],
            "file_count": selected["file_count"],
            "safe_next_action": selected["safe_next_action"],
            "docs_opt_in_required": docs_opt_in_required,
            "code_only_fallback_group_id": code_only_fallback["group_id"] if code_only_fallback else None,
            "active_actionable_lane_group_id": active_actionable_lane["group_id"] if active_actionable_lane else None,
            "executable_lane_group_id": executable_lane["group_id"],
            "ok": True,
        },
        "lane": {
            "group_id": selected["group_id"],
            "display_name": selected["display_name"],
            "bucket": selected["bucket"],
            "notes": selected["notes"],
            "blocking_reason": selected["blocking_reason"],
            "goal": "Reduce dirty source pressure by resolving one bounded checkpoint-ready lane without widening scope.",
            "stop_condition": "All files in this lane are either checkpointed together or intentionally reclassified in the checkpoint plan.",
            "verification_commands": DEFAULT_VERIFY_COMMANDS,
            "result_companions": result_companions,
            "required_git_paths_clean": required_git_paths_clean,
            "docs_opt_in_required": docs_opt_in_required,
            "code_only_fallback": code_only_fallback,
            "active_actionable_lane": active_actionable_lane,
            "files": files,
        },
        "executable_lane": executable_lane,
    }

    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"selected_group_id={selected['group_id']}")
    print(f"file_count={selected['file_count']}")
    print("SOURCE DIRTY LANE MANIFEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
