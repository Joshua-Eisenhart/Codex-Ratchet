#!/usr/bin/env python3
"""Build an all-lane source-dirty review catalog.

This is a generated planning surface. It does not stage, commit, or classify
any lane as admitted; it expands the current source-dirty plan into bounded
review/checkpoint candidate bundles.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
PLAN_PATH = RESULTS_DIR / "source_dirty_checkpoint_plan.json"
TRUTH_AUDIT_PATH = RESULTS_DIR / "probe_truth_audit_results.json"
REPO_HYGIENE_PATH = RESULTS_DIR / "repo_hygiene_audit_results.json"
OUT_PATH = RESULTS_DIR / "source_dirty_lane_catalog.json"
OUT_MD = RESULTS_DIR / "source_dirty_lane_catalog.md"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} did not contain an object")
    return payload


def result_companion_for(source_rel: str) -> str | None:
    path = Path(source_rel)
    if path.parent.name != "probes" or not path.name.startswith("sim_"):
        return None
    stem = path.stem[len("sim_") :]
    return f"system_v4/probes/a2_state/sim_results/{stem}_results.json"


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


def lane_paths(group: dict[str, Any]) -> list[str]:
    paths = group.get("path_prefixes") or group.get("sample_paths") or []
    return [str(path) for path in paths if isinstance(path, str)]


def build_lane(group: dict[str, Any]) -> dict[str, Any]:
    owned_files = lane_paths(group)
    result_companions = [
        companion
        for companion in (result_companion_for(path) for path in owned_files)
        if companion
    ]
    for visual_payload in visual_payload_companions(result_companions):
        if visual_payload not in result_companions:
            result_companions.append(visual_payload)
    stage_paths = owned_files + result_companions
    missing_companions = [
        path for path in result_companions if not (PROJECT_DIR / path).exists()
    ]
    git_status = git_status_for(stage_paths)
    return {
        "group_id": group["group_id"],
        "display_name": group.get("display_name"),
        "bucket": group.get("bucket"),
        "safe_next_action": group.get("safe_next_action"),
        "manual_review_required": group.get("safe_next_action") != "checkpoint",
        "file_count": group.get("file_count", len(owned_files)),
        "owned_files": owned_files,
        "result_companions": result_companions,
        "stage_paths": stage_paths,
        "stage_path_count": len(stage_paths),
        "missing_companions": missing_companions,
        "ready_for_checkpoint_review": bool(owned_files) and not missing_companions,
        "git_status": git_status,
        "notes": group.get("notes"),
        "decision_needed": decision_needed(group),
    }


def decision_needed(group: dict[str, Any]) -> str:
    action = group.get("safe_next_action")
    bucket = group.get("bucket")
    if action == "checkpoint":
        return "checkpoint_lane_after_review"
    if action == "archive_review" or bucket == "legacy_runtime":
        return "archive_or_restore_decision"
    if bucket == "probe_source":
        return "checkpoint_or_rework_probe_lane"
    if bucket == "other_source":
        return "split_checkpoint_or_reclassify"
    return "manual_review"


def write_markdown(report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# Source Dirty Lane Catalog",
        "",
        "Generated planning surface. This does not stage, commit, or admit any lane.",
        "",
        "## Summary",
        f"- lanes: {summary['lane_count']}",
        f"- ready for checkpoint review: {summary['ready_for_checkpoint_review_count']}",
        f"- manual-review lanes: {summary['manual_review_lane_count']}",
        f"- stage/review paths: {summary['stage_path_count']}",
        f"- missing companions: {summary['missing_companion_count']}",
        "",
        "## Lanes",
    ]
    for lane in report["lanes"]:
        lines.extend(
            [
                f"### {lane['group_id']}",
                f"- display: {lane.get('display_name')}",
                f"- bucket/action: {lane.get('bucket')} / {lane.get('safe_next_action')}",
                f"- decision needed: {lane.get('decision_needed')}",
                f"- owned files: {len(lane.get('owned_files', []))}",
                f"- result companions: {len(lane.get('result_companions', []))}",
                f"- stage/review paths: {lane.get('stage_path_count')}",
                f"- missing companions: {len(lane.get('missing_companions', []))}",
                f"- ready for checkpoint review: {lane.get('ready_for_checkpoint_review')}",
            ]
        )
        notes = lane.get("notes")
        if notes:
            lines.append(f"- notes: {notes}")
        sample_status = lane.get("git_status", [])[:8]
        if sample_status:
            lines.append("- git status sample:")
            for line in sample_status:
                lines.append(f"  - `{line}`")
        lines.append("")
    OUT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    plan = read_json(PLAN_PATH)
    truth = read_json(TRUTH_AUDIT_PATH) if TRUTH_AUDIT_PATH.exists() else {}
    repo = read_json(REPO_HYGIENE_PATH) if REPO_HYGIENE_PATH.exists() else {}
    groups = list(plan.get("checkpoint_groups", []))
    lanes = [build_lane(group) for group in groups if isinstance(group, dict) and group.get("group_id")]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_plan_path": str(PLAN_PATH.relative_to(PROJECT_DIR)),
        "truth_ok": bool((truth.get("summary") or {}).get("ok")),
        "repo_hygiene_ok": bool((repo.get("summary") or {}).get("ok")),
        "summary": {
            "lane_count": len(lanes),
            "ready_for_checkpoint_review_count": sum(
                1 for lane in lanes if lane["ready_for_checkpoint_review"]
            ),
            "manual_review_lane_count": sum(
                1 for lane in lanes if lane["manual_review_required"]
            ),
            "stage_path_count": sum(lane["stage_path_count"] for lane in lanes),
            "missing_companion_count": sum(len(lane["missing_companions"]) for lane in lanes),
            "ok": True,
        },
        "lanes": lanes,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report)
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {OUT_MD}")
    print(f"lane_count={report['summary']['lane_count']}")
    print(f"stage_path_count={report['summary']['stage_path_count']}")
    print("SOURCE DIRTY LANE CATALOG PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
