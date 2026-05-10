#!/usr/bin/env python3
"""
Source-dirty checkpoint packet generator.

Builds a small machine-readable packet for the currently selected source-dirty
lane. This packet is a checkpoint-prep artifact, not a supervisor input.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
LANE_MANIFEST_PATH = RESULTS_DIR / "source_dirty_lane_manifest.json"
TRUTH_AUDIT_PATH = RESULTS_DIR / "probe_truth_audit_results.json"
REPO_HYGIENE_PATH = RESULTS_DIR / "repo_hygiene_audit_results.json"
OUT_PATH = RESULTS_DIR / "source_dirty_checkpoint_packet.json"


def packet_path_for(group_id: str | None) -> Path:
    if not group_id:
        return OUT_PATH.parent / "source_dirty_checkpoint_packet__no_actionable_lane.json"
    safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in group_id)
    return OUT_PATH.parent / f"source_dirty_checkpoint_packet__{safe}.json"


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


def git_status_for(paths: list[str]) -> list[str]:
    if not paths:
        return []
    completed = subprocess.run(
        ["git", "status", "--short", "--", *paths],
        cwd=PROJECT_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def visual_payload_companions(result_paths: list[str]) -> list[str]:
    companions: list[str] = []
    for rel in result_paths:
        path = PROJECT_DIR / rel
        if not path.exists() or path.suffix != ".json":
            continue
        try:
            payload = read_json(path)
        except Exception:  # noqa: BLE001
            continue
        visual_payload = (payload.get("summary") or {}).get("visual_payload")
        if not isinstance(visual_payload, str):
            continue
        if visual_payload.startswith("visualizer/") and (PROJECT_DIR / visual_payload).exists():
            companions.append(visual_payload)
    return companions


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = read_json(LANE_MANIFEST_PATH)
    requested_group_id = parse_group_id(sys.argv[1:])
    truth = read_json(TRUTH_AUDIT_PATH)
    repo = read_json(REPO_HYGIENE_PATH)

    executable_lane = manifest.get("executable_lane") or manifest.get("lane")
    if not executable_lane:
        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "lane_id": manifest["lane_id"],
            "group_id": None,
            "selected_group_id": manifest.get("selected_group_id"),
            "latest_packet_path": str(OUT_PATH.relative_to(PROJECT_DIR)),
            "lane_specific_packet_path": str(packet_path_for(None).relative_to(PROJECT_DIR)),
            "concurrency_note": (
                "source_dirty_checkpoint_packet.json is a last-write-wins latest pointer; "
                "parallel cleanup consumers should read the lane-specific packet path."
            ),
            "owned_files": [],
            "result_companions": [],
            "verification_snapshot": {
                "checks_run": ["lane_manifest_present", "no_actionable_lane_state"],
                "checks_passed": ["lane_manifest_present", "no_actionable_lane_state"],
                "checks_failed": [],
                "notes": [
                    "No checkpoint-ready lane is available; manual-only residue remains outside packetized cleanup."
                ],
                "git_status": [],
            },
            "required_git_paths_clean": [],
            "ready_for_checkpoint": False,
            "status": "no_actionable_lane",
        }
        packet_path = packet_path_for(None)
        serialized = json.dumps(report, indent=2)
        OUT_PATH.write_text(serialized, encoding="utf-8")
        packet_path.write_text(serialized, encoding="utf-8")
        print(f"Wrote {OUT_PATH}")
        print(f"Wrote {packet_path}")
        print("group_id=None")
        print("ready_for_checkpoint=False")
        print("SOURCE DIRTY CHECKPOINT PACKET PASSED (no actionable lane)")
        return 0
    executable_group_id = executable_lane.get("group_id", manifest.get("selected_group_id"))

    if requested_group_id and executable_group_id != requested_group_id:
        raise SystemExit(
            "lane manifest/group mismatch: "
            f"requested {requested_group_id}, manifest has executable lane {executable_group_id}"
        )

    lane = executable_lane
    owned_files = list(lane["files"])
    result_companions = list(lane.get("result_companions", []))
    for visual_payload in visual_payload_companions(result_companions):
        if visual_payload not in result_companions:
            result_companions.append(visual_payload)
    required_git_paths_clean = list(lane.get("required_git_paths_clean", owned_files + result_companions))
    for path in result_companions:
        if path not in required_git_paths_clean:
            required_git_paths_clean.append(path)
    git_snapshot = git_status_for(required_git_paths_clean)

    checks_run = [
        "lane_manifest_present",
        "truth_audit_green",
        "result_companions_present",
        "repo_hygiene_no_result_placement_drift",
        "git_snapshot_collected",
    ]
    checks_passed: list[str] = []
    checks_failed: list[str] = []
    notes: list[str] = []

    checks_passed.append("lane_manifest_present")

    truth_ok = bool((truth.get("summary") or {}).get("ok"))
    if truth_ok:
        checks_passed.append("truth_audit_green")
    else:
        checks_failed.append("truth_audit_green")

    companion_presence = []
    for rel in result_companions:
        present = (PROJECT_DIR / rel).exists()
        companion_presence.append({"path": rel, "present": present})
    if all(item["present"] for item in companion_presence):
        checks_passed.append("result_companions_present")
    else:
        checks_failed.append("result_companions_present")

    repo_summary = repo.get("summary") or {}
    no_result_placement_drift = (
        repo_summary.get("root_result_orphan_count", 0) == 0
        and repo_summary.get("secondary_result_count", 0) == 0
        and repo_summary.get("duplicate_result_basename_count", 0) == 0
    )
    if no_result_placement_drift:
        checks_passed.append("repo_hygiene_no_result_placement_drift")
    else:
        checks_failed.append("repo_hygiene_no_result_placement_drift")

    if git_snapshot:
        checks_passed.append("git_snapshot_collected")
    else:
        checks_failed.append("git_snapshot_collected")

    if any(line.startswith("?? ") for line in git_snapshot):
        notes.append("Lane still includes untracked paths; checkpoint should stage full lane deliberately.")
    if any("xgi_dual_hypergraph_results.json" in line for line in git_snapshot):
        notes.append("xgi_dual_hypergraph result did not rewrite in the latest rerun but remains present under the canonical result root.")

    ready_for_checkpoint = len(checks_failed) == 0

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "lane_id": manifest["lane_id"],
        "group_id": executable_group_id,
        "selected_group_id": manifest["selected_group_id"],
        "latest_packet_path": str(OUT_PATH.relative_to(PROJECT_DIR)),
        "lane_specific_packet_path": str(packet_path_for(executable_group_id).relative_to(PROJECT_DIR)),
        "concurrency_note": (
            "source_dirty_checkpoint_packet.json is a last-write-wins latest pointer; "
            "parallel cleanup consumers should read the lane-specific packet path."
        ),
        "owned_files": owned_files,
        "result_companions": result_companions,
        "verification_snapshot": {
            "checks_run": checks_run,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "notes": notes,
            "git_status": git_snapshot,
        },
        "required_git_paths_clean": required_git_paths_clean,
        "ready_for_checkpoint": ready_for_checkpoint,
    }

    packet_path = packet_path_for(executable_group_id)
    serialized = json.dumps(report, indent=2)
    OUT_PATH.write_text(serialized, encoding="utf-8")
    packet_path.write_text(serialized, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {packet_path}")
    print(f"group_id={report['group_id']}")
    print(f"ready_for_checkpoint={report['ready_for_checkpoint']}")
    print("SOURCE DIRTY CHECKPOINT PACKET PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
