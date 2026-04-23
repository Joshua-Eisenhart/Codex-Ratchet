"""
a2_tracked_work_operator.py

Emit one bounded tracked-work state artifact over existing Ratchet queue and
audit surfaces.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
A2_TRACKED_WORK_JSON = "system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.json"
A2_TRACKED_WORK_MD = "system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.md"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _extract_queue_status(note_text: str) -> dict[str, str]:
    result = {"queue_status": "", "program_status": "", "ready_unit_id": ""}
    for key in result:
        match = re.search(rf"^{key}:\s*(.*)$", note_text, flags=re.MULTILINE)
        if match:
            result[key] = match.group(1).strip()
    return result


def _doc_queue_stats(doc_queue: list[Any]) -> dict[str, int]:
    stats = {"total": 0, "done": 0, "pending": 0}
    for item in doc_queue:
        if not isinstance(item, dict):
            continue
        stats["total"] += 1
        status = str(item.get("status", "")).upper()
        if status == "DONE":
            stats["done"] += 1
        else:
            stats["pending"] += 1
    return stats


def _render_markdown(report: dict[str, Any]) -> str:
    non_goal_lines = [f"- {item}" for item in report.get("non_goals", [])]
    next_action_lines = [f"- {item}" for item in report.get("next_actions", [])]
    next_cluster_candidate = report.get("next_cluster_candidate", "")
    next_first_slice = report.get("next_first_slice", "")
    return "\n".join(
        [
            "# A2 Tracked Work State",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- current_cluster: `{report.get('current_cluster', '')}`",
            f"- next_cluster_candidate: `{next_cluster_candidate or 'None selected'}`",
            f"- next_first_slice: `{next_first_slice or 'None selected'}`",
            f"- queue_status: `{report.get('queue_status', {}).get('queue_status', '')}`",
            "",
            "## Next Actions",
            *next_action_lines,
            "",
            "## Non-Goals",
            *non_goal_lines,
            "",
        ]
    )


def build_a2_tracked_work_report(repo_root: str | Path = REPO_ROOT) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    intake_report = _load_json(root / "system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json")
    cluster_map_text = _load_text(root / "system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md")
    queue_status = _extract_queue_status(
        _load_text(root / "system_v4/a2_state/NESTED_GRAPH_BUILD_QUEUE_STATUS__CURRENT__2026_03_20__v1.md")
    )
    doc_queue = _load_json(root / "system_v4/a2_state/doc_queue.json")

    current_cluster = "SKILL_CLUSTER::tracked-work-planning"
    next_cluster_candidate = ""
    next_first_slice = ""

    status = "ok"
    issues: list[str] = []
    if not isinstance(intake_report, dict) or intake_report.get("status") != "ok":
        status = "attention_required"
        issues.append("current intake report missing or not ok")
    if "tracked-work-planning" not in cluster_map_text:
        status = "attention_required"
        issues.append("tracked work cluster missing from imported cluster map")

    report = {
        "schema": "A2_TRACKED_WORK_STATE_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "current_cluster": current_cluster,
        "current_first_slice": "a2-tracked-work-operator",
        "next_cluster_candidate": next_cluster_candidate,
        "next_first_slice": next_first_slice,
        "queue_status": queue_status,
        "doc_queue_stats": _doc_queue_stats(doc_queue if isinstance(doc_queue, list) else []),
        "next_actions": [
            "Keep the current tracked-work slice stable and reusable through repo-held reports.",
            "No further tracked-work slice is selected right now; do not invent a recursive next-step inside the same cluster.",
            "Use existing queue, audit, and closeout surfaces for routing instead of creating a second planning substrate.",
        ],
        "non_goals": [
            "No .lev/pm handoff or plan directories.",
            "No workflow skill scaffolding import.",
            "No claim that the tracked-work cluster is fully live.",
        ],
        "issues": issues,
    }
    return report


def run_a2_tracked_work(ctx: dict[str, Any]) -> dict[str, Any]:
    repo_root = ctx.get("repo", REPO_ROOT)
    root = Path(repo_root).resolve()
    report = build_a2_tracked_work_report(root)
    report_path = Path(ctx.get("report_path") or (root / A2_TRACKED_WORK_JSON))
    markdown_path = Path(ctx.get("markdown_path") or (root / A2_TRACKED_WORK_MD))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    report["report_path"] = str(report_path)
    report["markdown_path"] = str(markdown_path)
    return report


if __name__ == "__main__":
    report = build_a2_tracked_work_report(REPO_ROOT)
    assert report["status"] == "ok", report["issues"]
    assert report["current_first_slice"] == "a2-tracked-work-operator"
    assert report["next_first_slice"] == ""
    print("PASS: a2_tracked_work_operator self-test")
