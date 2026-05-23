#!/usr/bin/env python3
"""Build a single dry-run preview from generated proposal reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "system_v5/ops"
OUT_PATH = OPS / "proposal_apply_preview.json"


INPUTS = {
    "c1": OPS / "c1_classification_proposals.json",
    "c4": OPS / "c4_divergence_log_proposals.json",
    "c6": OPS / "c6_loadbearing_report.json",
}


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def counts_by(rows: list[Any], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            value = "unknown"
        else:
            value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def proposal_counts(name: str, rows: list[Any]) -> tuple[str, dict[str, int]]:
    if name == "c1":
        return "proposed_classification", counts_by(rows, "proposed_classification")
    return "proposal_kind", counts_by(rows, "proposal_kind")


def next_action_for(name: str, rows: list[Any]) -> str:
    if name == "c4":
        kinds = counts_by(rows, "proposal_kind")
        simple = kinds.get("simple_classical_divergence_log", 0)
        review = sum(count for kind, count in kinds.items() if kind != "simple_classical_divergence_log")
        if review:
            return (
                f"review_required_before_source_edit; {simple} simple classical candidates, "
                f"{review} classification_or_stage_review candidates"
            )
    return "owner_review_required_before_any_source_edit"


def main() -> int:
    sections: dict[str, Any] = {}
    action_items = []
    for name, path in INPUTS.items():
        data = load(path)
        if not data:
            sections[name] = {"present": False}
            continue
        rows = data.get("proposals") or data.get("rows") or []
        proposal_count_field, proposal_kind_counts = proposal_counts(name, rows)
        sections[name] = {
            "present": True,
            "path": str(path.relative_to(ROOT)),
            "row_count": len(rows),
            "proposal_count_field": proposal_count_field,
            "proposal_kind_counts": proposal_kind_counts,
            "runner_class_counts": counts_by(rows, "runner_class"),
            "sample": rows[:20],
        }
        action_items.append(
            {
                "proposal_family": name,
                "path": str(path.relative_to(ROOT)),
                "row_count": len(rows),
                "next_action": next_action_for(name, rows),
            }
        )
    report = {
        "schema": "proposal_apply_preview_v1",
        "mode": "dry_run_no_source_edits",
        "action_items": action_items,
        "sections": sections,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"path": str(OUT_PATH.relative_to(ROOT)), "action_item_count": len(action_items)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
