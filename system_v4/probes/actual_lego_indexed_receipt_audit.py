#!/usr/bin/env python3
"""Audit indexed lego rows against the current receipt validator."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
WORK_MATRIX_PATH = RESULTS_DIR / "actual_lego_work_matrix.json"
OUT_PATH = RESULTS_DIR / "actual_lego_indexed_receipt_audit.json"

sys.path.insert(0, str(PROJECT_DIR / "scripts"))
from receipt_schema import validate_result_path  # noqa: E402


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_DIR))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_row(row: dict) -> dict:
    result_path_text = row.get("result_path")
    if not result_path_text:
        return {
            "ok": False,
            "hard_finding_count": 1,
            "warning_count": 0,
            "hard_findings": [{"kind": "missing_result_path", "severity": "hard"}],
            "warnings": [],
        }
    record = validate_result_path(Path(result_path_text), root=PROJECT_DIR)
    return {
        "ok": record["ok"],
        "hard_finding_count": len(record.get("hard_findings", [])),
        "warning_count": len(record.get("warnings", [])),
        "hard_findings": record.get("hard_findings", []),
        "warnings": record.get("warnings", []),
    }


def audit_status(audit: dict) -> str:
    if audit["hard_finding_count"]:
        return "hard_blocked"
    if audit["warning_count"]:
        return "hard_green_boundary_warnings"
    return "hard_green_clean"


def main() -> int:
    matrix = read_json(WORK_MATRIX_PATH)
    rows = []
    status_counts: Counter[str] = Counter()
    for row in matrix.get("rows", []):
        if row.get("next_action", {}).get("status") != "indexed":
            continue
        audit = validate_row(row)
        status = audit_status(audit)
        status_counts[status] += 1
        rows.append(
            {
                "lego_id": row.get("lego_id"),
                "lego_name": row.get("lego_name"),
                "section": row.get("section"),
                "source_current_coverage": row.get("source_current_coverage"),
                "machine_current_coverage": row.get("machine_current_coverage"),
                "machine_best_probe": row.get("machine_best_probe"),
                "machine_best_result": row.get("machine_best_result"),
                "result_path": row.get("result_path"),
                "result_classification": row.get("result_classification"),
                "result_all_pass": row.get("result_all_pass"),
                "load_bearing_tools": row.get("load_bearing_tools", []),
                "audit_status": status,
                "claim_ceiling": "indexed_receipt_audit_only_not_admission_or_promotion",
                "promotion_allowed": False,
                **audit,
            }
        )

    payload = {
        "name": "actual_lego_indexed_receipt_audit",
        "schema": "actual_lego_indexed_receipt_audit.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "boundary": "validator_audit_only_not_admission_or_promotion",
        "inputs": {
            "work_matrix": rel(WORK_MATRIX_PATH),
            "validator": "scripts/receipt_schema.py",
        },
        "summary": {
            "row_count": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
            "hard_blocked_count": status_counts.get("hard_blocked", 0),
            "hard_green_count": len(rows) - status_counts.get("hard_blocked", 0),
            "boundary_warning_row_count": status_counts.get("hard_green_boundary_warnings", 0),
            "promotion_allowed_count": 0,
        },
        "rows": rows,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["summary"]["hard_blocked_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
