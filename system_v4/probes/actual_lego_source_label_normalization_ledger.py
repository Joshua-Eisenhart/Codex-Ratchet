#!/usr/bin/env python3
"""Build a review ledger for stale source coverage labels.

The source markdown registry keeps owner-authored coverage labels.  The work
matrix overlays machine receipt evidence.  This ledger names rows where machine
evidence is ahead of the markdown label without rewriting the source registry.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
WORK_MATRIX_PATH = RESULTS_DIR / "actual_lego_work_matrix.json"
OUT_PATH = RESULTS_DIR / "actual_lego_source_label_normalization_ledger.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def proposed_coverage(row: dict) -> str:
    source = row.get("source_current_coverage")
    machine = row.get("machine_current_coverage")
    if source == "canonical by process":
        return source
    return machine or source or "unknown"


def ledger_row(row: dict) -> dict:
    source = row.get("source_current_coverage")
    machine = row.get("machine_current_coverage")
    return {
        "lego_id": row.get("lego_id"),
        "lego_name": row.get("lego_name"),
        "section": row.get("section"),
        "source_current_coverage": source,
        "machine_current_coverage": machine,
        "machine_best_probe": row.get("machine_best_probe"),
        "machine_best_result": row.get("machine_best_result"),
        "result_path": row.get("result_path"),
        "result_sha256": row.get("result_sha256"),
        "result_classification": row.get("result_classification"),
        "result_all_pass": row.get("result_all_pass"),
        "mapping_confidence": row.get("machine_mapping_confidence"),
        "load_bearing_tools": row.get("load_bearing_tools", []),
        "coverage_slots": row.get("coverage_slots", {}),
        "proposed_markdown_coverage": proposed_coverage(row),
        "claim_ceiling": "source_label_normalization_only_not_admission_or_promotion",
        "requires_human_markdown_acceptance": True,
        "reason": (
            "machine receipt evidence covers this row, but the owner-authored "
            "markdown coverage label is still older"
        ),
        "next_action_status": row.get("next_action", {}).get("status"),
    }


def main() -> int:
    matrix = read_json(WORK_MATRIX_PATH)
    rows = [
        ledger_row(row)
        for row in matrix.get("rows", [])
        if row.get("stale_label_risk")
        and row.get("machine_current_coverage") == "covered"
        and row.get("result_all_pass") is True
    ]
    source_counts = Counter(row["source_current_coverage"] for row in rows)
    proposed_counts = Counter(row["proposed_markdown_coverage"] for row in rows)
    section_counts = Counter(row["section"] for row in rows)
    payload = {
        "name": "actual_lego_source_label_normalization_ledger",
        "schema": "actual_lego_source_label_normalization_ledger.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "boundary": "review_ledger_only_not_source_markdown_update_not_admission_or_promotion",
        "inputs": {
            "work_matrix": str(WORK_MATRIX_PATH.relative_to(PROJECT_DIR)),
        },
        "summary": {
            "row_count": len(rows),
            "source_coverage_counts": dict(sorted(source_counts.items())),
            "proposed_coverage_counts": dict(sorted(proposed_counts.items())),
            "section_counts": dict(sorted(section_counts.items())),
            "requires_human_markdown_acceptance_count": sum(
                1 for row in rows if row["requires_human_markdown_acceptance"]
            ),
            "promotion_allowed_count": 0,
        },
        "rows": rows,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
