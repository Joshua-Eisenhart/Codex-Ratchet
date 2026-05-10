#!/usr/bin/env python3
"""Audit linked lego coupling receipts without promoting them."""

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
OUT_PATH = RESULTS_DIR / "actual_lego_coupling_receipt_audit.json"
SCRIPTS_DIR = PROJECT_DIR / "scripts"

AUDITABLE_STATUSES = {
    "coupling_receipt_linked_audit_needed",
    "coupling_supporting_receipt_indexed",
    "coupling_receipt_audited_not_closure_grade",
    "coupling_supporting_receipt_audited",
    "coupling_receipt_hard_blocked",
    "coupling_receipt_boundary_warnings",
}

sys.path.insert(0, str(SCRIPTS_DIR))
from receipt_schema import summary_all_pass, validate_result_path  # noqa: E402


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_DIR))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def result_name_for_probe(probe: str | None) -> str | None:
    if not probe or not probe.endswith(".py"):
        return None
    stem = probe[:-3]
    if stem.startswith("sim_"):
        stem = stem[4:]
    return f"{stem}_results.json"


def audit_status(audit: dict, payload: dict) -> str:
    if audit["hard_finding_count"]:
        return "hard_blocked"
    if audit["warning_count"]:
        return "hard_green_boundary_warnings"
    if payload.get("classification") == "supporting":
        return "hard_green_supporting_only"
    if not (payload.get("positive") and payload.get("negative") and payload.get("boundary")):
        return "hard_green_not_closure_grade"
    return "hard_green_closure_candidate"


def main() -> int:
    matrix = read_json(WORK_MATRIX_PATH)
    rows = []
    seen: set[tuple[str, str]] = set()
    status_counts: Counter[str] = Counter()
    for row in matrix.get("rows", []):
        next_action = row.get("next_action", {})
        if next_action.get("status") not in AUDITABLE_STATUSES:
            continue
        packet = next_action.get("packet") or row.get("recommended_sim")
        result_name = result_name_for_probe(packet)
        if not result_name:
            continue
        result_path = RESULTS_DIR / result_name
        key = (row.get("lego_id"), result_name)
        if key in seen:
            continue
        seen.add(key)
        if not result_path.exists():
            audit = {
                "ok": False,
                "hard_finding_count": 1,
                "warning_count": 0,
                "hard_findings": [{"kind": "missing_coupling_result", "severity": "hard"}],
                "warnings": [],
            }
            payload = {}
        else:
            payload = read_json(result_path)
            audit_record = validate_result_path(result_path, root=PROJECT_DIR)
            audit = {
                "ok": audit_record["ok"],
                "hard_finding_count": len(audit_record.get("hard_findings", [])),
                "warning_count": len(audit_record.get("warnings", [])),
                "hard_findings": audit_record.get("hard_findings", []),
                "warnings": audit_record.get("warnings", []),
            }
        status = audit_status(audit, payload)
        status_counts[status] += 1
        rows.append(
            {
                "lego_id": row.get("lego_id"),
                "lego_name": row.get("lego_name"),
                "section": row.get("section"),
                "task_ids": row.get("coupling_task_ids", []),
                "packet": packet,
                "coupling_result": rel(result_path),
                "coupling_classification": payload.get("classification"),
                "coupling_all_pass": summary_all_pass(payload) if payload else None,
                "has_positive_negative_boundary": bool(
                    payload.get("positive") and payload.get("negative") and payload.get("boundary")
                ),
                "audit_status": status,
                "promotion_allowed": False,
                "claim_ceiling": "coupling_receipt_audit_only_not_admission_or_promotion",
                "closure_gate": (
                    "Requires canonical/closure-grade coupling receipt, ablation/coexistence evidence, "
                    "and explicit stage-gate admission."
                ),
                **audit,
            }
        )

    payload = {
        "name": "actual_lego_coupling_receipt_audit",
        "schema": "actual_lego_coupling_receipt_audit.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "boundary": "coupling_receipt_audit_only_not_admission_or_promotion",
        "inputs": {
            "work_matrix": rel(WORK_MATRIX_PATH),
            "validator": "scripts/receipt_schema.py",
        },
        "summary": {
            "row_count": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
            "hard_blocked_count": status_counts.get("hard_blocked", 0),
            "boundary_warning_row_count": status_counts.get("hard_green_boundary_warnings", 0),
            "closure_candidate_count": status_counts.get("hard_green_closure_candidate", 0),
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
