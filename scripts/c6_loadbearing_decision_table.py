#!/usr/bin/env python3
"""Build a review table for blocked C6 classical/load-bearing rows.

This does not edit sims. It turns existing reports into an owner-review queue
with explicit candidate actions and stop conditions.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BLOCKED_REPORT = ROOT / "system_v5/ops/blocked_reason_breakdown.json"
C6_REPORT = ROOT / "system_v5/ops/c6_loadbearing_report.json"
OUT_PATH = ROOT / "system_v5/ops/c6_loadbearing_decision_table.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def candidate_action(row: dict[str, Any]) -> str:
    bucket = str(row.get("bucket") or "")
    result_path = row.get("result_path")
    evidence = str(row.get("evidence") or "")
    if bucket == "decorative_load_bearing_demote_tool":
        return "remove_or_demote_tool_depth_candidate"
    if bucket == "genuinely_load_bearing_so_promote_to_canonical_candidate":
        return "promote_to_canonical_candidate_after_owner_review"
    if bucket == "inconclusive_needs_owner" and result_path is None:
        return "owner_review_missing_result_before_edit"
    if bucket == "inconclusive_needs_owner":
        return "owner_review_inconclusive"
    if result_path is None:
        return "owner_review_missing_result_before_edit"
    if evidence == "result_json_mentions_tool":
        return "owner_review_result_forensics"
    return "owner_review_inconclusive"


def main() -> int:
    blocked = load_json(BLOCKED_REPORT)
    c6 = load_json(C6_REPORT)

    blocked_c6_sims = {
        str(row.get("sim_path"))
        for row in blocked.get("rows", [])
        if isinstance(row, dict)
        and row.get("blocked_reason") == "wizard_admission_blocked"
        and "C6_classical_has_load_bearing" in list(row.get("subreasons") or [])
        and row.get("sim_path")
    }

    rows_by_sim: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in c6.get("rows", []):
        if isinstance(row, dict) and row.get("sim") in blocked_c6_sims:
            rows_by_sim[str(row["sim"])].append(row)

    decisions = []
    action_counts: Counter[str] = Counter()
    tool_counts: Counter[str] = Counter()
    bucket_counts: Counter[str] = Counter()
    for sim in sorted(rows_by_sim):
        for row in sorted(rows_by_sim[sim], key=lambda item: str(item.get("tool") or "")):
            action = candidate_action(row)
            action_counts[action] += 1
            tool_counts[str(row.get("tool") or "unknown")] += 1
            bucket_counts[str(row.get("bucket") or "unknown")] += 1
            decisions.append(
                {
                    "sim": sim,
                    "tool": row.get("tool"),
                    "bucket": row.get("bucket"),
                    "result_path": row.get("result_path"),
                    "evidence": row.get("evidence"),
                    "candidate_action": action,
                    "owner_review_required": True,
                    "source_edit_allowed": False,
                    "stop_condition": "Do not edit source until owner review selects remove/demote, prove, or promote path.",
                }
            )

    report = {
        "schema": "c6_loadbearing_decision_table_v1",
        "mode": "review_only_no_source_edits",
        "source_reports": [str(BLOCKED_REPORT.relative_to(ROOT)), str(C6_REPORT.relative_to(ROOT))],
        "source_report_row_counts": {
            "blocked_reason_breakdown": len([row for row in blocked.get("rows", []) if isinstance(row, dict)]),
            "c6_loadbearing_report": len([row for row in c6.get("rows", []) if isinstance(row, dict)]),
        },
        "blocked_c6_sim_count": len(blocked_c6_sims),
        "decision_row_count": len(decisions),
        "action_counts": dict(action_counts),
        "tool_counts": dict(tool_counts.most_common()),
        "bucket_counts": dict(bucket_counts),
        "rows": decisions,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "path": str(OUT_PATH.relative_to(ROOT)),
                "blocked_c6_sim_count": len(blocked_c6_sims),
                "decision_row_count": len(decisions),
                "action_counts": dict(action_counts),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
