#!/usr/bin/env python3
"""Build a row-level closeout ledger for the active lego frontier.

This is a reporting/control artifact.  It does not admit, promote, or rewrite
source labels.  Its job is to make the current frontier state explicit so
controller closeout does not confuse covered receipts with canonical admission.
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
COUPLING_AUDIT_PATH = RESULTS_DIR / "actual_lego_coupling_receipt_audit.json"
COUPLING_CANDIDATES_PATH = RESULTS_DIR / "lego_coupling_candidates.json"
NORMALIZATION_LEDGER_PATH = RESULTS_DIR / "actual_lego_source_label_normalization_ledger.json"
OUT_PATH = RESULTS_DIR / "actual_lego_frontier_closeout_ledger.json"


BLOCKED_ACTIONS = {
    "blocked",
    "needs_probe_or_result_repair",
    "result_failing_repair_needed",
    "indexed_receipt_hard_blocked",
    "source_process_receipt_hard_blocked",
    "coupling_receipt_hard_blocked",
}


DONE_ACTIONS = {
    "indexed_receipt_audited",
    "source_process_receipt_audited",
    "coupling_receipt_audited_closure_candidate",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def row_state(row: dict) -> str:
    action = (row.get("next_action") or {}).get("status")
    if action in BLOCKED_ACTIONS or not row.get("result_exists"):
        return "blocked"
    if row.get("stale_label_risk"):
        return "stale"
    if row.get("use_as_negative_evidence"):
        return "graveyard"
    if row.get("queue_status_normalized") == "ready":
        return "queued"
    if action in DONE_ACTIONS:
        return "done"
    return "queued"


def closeout_row(row: dict) -> dict:
    state = row_state(row)
    action = row.get("next_action") or {}
    return {
        "lego_id": row.get("lego_id"),
        "lego_name": row.get("lego_name"),
        "section": row.get("section"),
        "state": state,
        "source_current_coverage": row.get("source_current_coverage"),
        "machine_current_coverage": row.get("machine_current_coverage"),
        "result_exists": row.get("result_exists"),
        "result_classification": row.get("result_classification"),
        "result_all_pass": row.get("result_all_pass"),
        "machine_best_probe": row.get("machine_best_probe"),
        "machine_best_result": row.get("machine_best_result"),
        "coverage_slots": row.get("coverage_slots", {}),
        "load_bearing_tools": row.get("load_bearing_tools", []),
        "coupling_task_ids": row.get("coupling_task_ids", []),
        "next_action_status": action.get("status"),
        "next_action_reason": action.get("reason"),
        "stale_label_risk": row.get("stale_label_risk"),
        "use_as_negative_evidence": row.get("use_as_negative_evidence"),
        "promotion_allowed": False,
        "claim_ceiling": "frontier_closeout_ledger_only_not_admission_or_promotion",
    }


def main() -> int:
    matrix = read_json(WORK_MATRIX_PATH)
    coupling_audit = read_json(COUPLING_AUDIT_PATH)
    coupling_candidates = read_json(COUPLING_CANDIDATES_PATH)
    normalization_ledger = read_json(NORMALIZATION_LEDGER_PATH)

    rows = [closeout_row(row) for row in matrix.get("rows", [])]
    state_counts = Counter(row["state"] for row in rows)
    section_state_counts = Counter((row["section"], row["state"]) for row in rows)
    slot_counts: Counter[str] = Counter()
    for row in rows:
        for slot, enabled in row["coverage_slots"].items():
            if enabled:
                slot_counts[slot] += 1

    payload = {
        "name": "actual_lego_frontier_closeout_ledger",
        "schema": "actual_lego_frontier_closeout_ledger.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "boundary": "closeout_reporting_only_not_admission_or_promotion",
        "inputs": {
            "work_matrix": str(WORK_MATRIX_PATH.relative_to(PROJECT_DIR)),
            "coupling_audit": str(COUPLING_AUDIT_PATH.relative_to(PROJECT_DIR)),
            "coupling_candidates": str(COUPLING_CANDIDATES_PATH.relative_to(PROJECT_DIR)),
            "normalization_ledger": str(NORMALIZATION_LEDGER_PATH.relative_to(PROJECT_DIR)),
        },
        "summary": {
            "row_count": len(rows),
            "state_counts": dict(sorted(state_counts.items())),
            "result_exists_count": sum(1 for row in rows if row["result_exists"]),
            "missing_result_count": sum(
                1
                for row in rows
                if not row["result_exists"]
                and row.get("machine_current_coverage") != "blocked_as_late_surface"
            ),
            "late_surface_no_result_count": sum(
                1
                for row in rows
                if not row["result_exists"]
                and row.get("machine_current_coverage") == "blocked_as_late_surface"
            ),
            "result_missing_raw_count": sum(1 for row in rows if not row["result_exists"]),
            "stale_label_risk_count": sum(1 for row in rows if row["stale_label_risk"]),
            "graveyard_count": sum(1 for row in rows if row["use_as_negative_evidence"]),
            "coverage_slot_counts": dict(sorted(slot_counts.items())),
            "coupling_audit_summary": coupling_audit.get("summary", {}),
            "coupling_candidate_summary": coupling_candidates.get("summary", {}),
            "normalization_ledger_summary": normalization_ledger.get("summary", {}),
            "promotion_allowed_count": 0,
            "claim_ceiling": "frontier classified, not closed as admitted or promoted",
        },
        "section_state_counts": {
            f"{section} :: {state}": count
            for (section, state), count in sorted(section_state_counts.items())
        },
        "rows": rows,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
