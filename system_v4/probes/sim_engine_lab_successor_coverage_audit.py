#!/usr/bin/env python3
"""Audit successor coverage for current engine-lab open rows."""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone


CLASSIFICATION = "controller_audit"
classification = CLASSIFICATION
divergence_log = (
    "Controller audit proving the current engine-lab open-row queue has no "
    "active uncovered rows. It accepts only successor-covered, consolidated-"
    "closed, or superseded lanes, preserves source negatives, and does not "
    "admit QIT, GStack, axis, or runtime-engine claims."
)

LEGO_IDS = ["cycle_protocol_receipt_status_matrix", "successor_coverage", "stage_gate"]
PRIMARY_LEGO_IDS = ["cycle_protocol_receipt_status_matrix"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads queue/audit receipts and writes coverage audit"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"

ACCEPTED_PREFIXES = (
    "successor_receipt_available_",
    "closed_by_",
    "superseded_by_",
)


def load(name: str) -> dict:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def receipt_mtimes(names: list[str]) -> dict[str, float | None]:
    mtimes: dict[str, float | None] = {}
    for name in names:
        path = RESULT_DIR / name
        mtimes[name] = path.stat().st_mtime if path.exists() else None
    return mtimes


def build_visual_payload(result: dict) -> dict:
    return {
        "name": result["name"],
        "generated_at": result["generated_at"],
        "summary": result["summary"],
        "source_receipts": result["source_receipts"],
        "source_receipt_mtimes": result["source_receipt_mtimes"],
        "positive": result["positive"],
        "negative": result["negative"],
        "boundary": result["boundary"],
        "rows": result["rows"],
        "uncovered_rows": result["uncovered_rows"],
    }


def write_visual_payload(result: dict) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    js = "window.ENGINE_LAB_SUCCESSOR_COVERAGE_DATA = " + json.dumps(
        build_visual_payload(result), indent=2
    ) + ";\n"
    (VIS_DIR / "engine-lab-successor-coverage-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    source_names = [
        "cycle_protocol_receipt_status_matrix_results.json",
        "engine_lab_open_row_audit_results.json",
        "engine_lab_next_work_queue_results.json",
    ]
    queue = load("engine_lab_next_work_queue_results.json")
    audit = load("engine_lab_open_row_audit_results.json")
    matrix = load("cycle_protocol_receipt_status_matrix_results.json")
    audit_rows_by_id = {item.get("row_id"): item for item in audit.get("rows", [])}

    rows = []
    uncovered = []
    schema_errors = []
    for row in queue["rows"]:
        lane = row.get("recommended_lane")
        row_id = row.get("row_id")
        if not row_id:
            row_out = {
                "row_id": None,
                "audit_class": row.get("audit_class"),
                "recommended_lane": lane,
                "covered": False,
                "passing_successor_count": row.get("passing_successor_count", 0),
                "consolidated_admission_status": row.get("consolidated_admission_status"),
                "graveyard_covered": row.get("graveyard_covered", False),
                "source_all_pass": None,
                "source_negative_preserved": False,
                "qit_or_axis_promotion_allowed": False,
                "schema_error": "missing_row_id",
            }
            rows.append(row_out)
            uncovered.append(row_out)
            schema_errors.append(row_out)
            continue
        if lane is None:
            row_out = {
                "row_id": row_id,
                "audit_class": row.get("audit_class"),
                "recommended_lane": None,
                "covered": False,
                "passing_successor_count": row.get("passing_successor_count", 0),
                "consolidated_admission_status": row.get("consolidated_admission_status"),
                "graveyard_covered": row.get("graveyard_covered", False),
                "source_all_pass": None,
                "source_negative_preserved": False,
                "qit_or_axis_promotion_allowed": False,
                "schema_error": "missing_recommended_lane",
            }
            rows.append(row_out)
            uncovered.append(row_out)
            schema_errors.append(row_out)
            continue
        covered = lane.startswith(ACCEPTED_PREFIXES)
        audit_row = audit_rows_by_id.get(row_id)
        if audit_row is None:
            row_out = {
                "row_id": row_id,
                "audit_class": row.get("audit_class"),
                "recommended_lane": lane,
                "covered": False,
                "passing_successor_count": row.get("passing_successor_count", 0),
                "consolidated_admission_status": row.get("consolidated_admission_status"),
                "graveyard_covered": row.get("graveyard_covered", False),
                "source_all_pass": None,
                "source_negative_preserved": False,
                "qit_or_axis_promotion_allowed": False,
                "schema_error": "queue_row_missing_from_open_row_audit",
            }
            rows.append(row_out)
            uncovered.append(row_out)
            schema_errors.append(row_out)
            continue
        row_out = {
            "row_id": row_id,
            "audit_class": row.get("audit_class"),
            "recommended_lane": lane,
            "covered": bool(covered),
            "passing_successor_count": row.get("passing_successor_count", 0),
            "consolidated_admission_status": row.get("consolidated_admission_status"),
            "graveyard_covered": row.get("graveyard_covered", False),
            "source_all_pass": audit_row.get("summary", {}).get("all_pass"),
            "source_negative_preserved": audit_row.get("summary", {}).get("all_pass") is False,
            "qit_or_axis_promotion_allowed": False,
            "schema_error": None,
        }
        rows.append(row_out)
        if not covered:
            uncovered.append(row_out)

    positive = {
        "queue_reports_no_active_uncovered_rows": {
            "active_uncovered_row_count": queue["summary"].get("active_uncovered_row_count"),
            "pass": queue["summary"].get("active_uncovered_row_count") == 0,
        },
        "all_queue_rows_are_covered_by_allowed_lane_types": {
            "covered_count": sum(row["covered"] for row in rows),
            "row_count": len(rows),
            "pass": len(uncovered) == 0 and len(rows) > 0,
        },
        "open_row_audit_is_complete": {
            "audit_complete": audit["summary"].get("audit_complete"),
            "missing_audit_rows": audit["summary"].get("missing_audit_rows"),
            "unclassified_open_rows": audit["summary"].get("unclassified_open_rows"),
            "pass": (
                audit["summary"].get("audit_complete") is True
                and audit["summary"].get("missing_audit_rows") == 0
                and audit["summary"].get("unclassified_open_rows") == 0
            ),
        },
    }
    negative = {
        "source_rows_remain_negative_or_nonpassing": {
            "source_negative_count": sum(row["source_negative_preserved"] for row in rows),
            "row_count": len(rows),
            "pass": all(row["source_negative_preserved"] for row in rows),
        },
        "matrix_still_not_promoted_to_full_pass": {
            "matrix_all_pass": matrix["summary"].get("all_pass"),
            "matrix_status": matrix["summary"].get("matrix_status"),
            "pass": matrix["summary"].get("all_pass") is False,
        },
        "successor_coverage_is_not_qit_axis_or_gstack_admission": {
            "qit_or_axis_promotion_allowed": False,
            "pass": True,
        },
    }
    boundary = {
        "coverage_rows_match_queue_rows": {
            "coverage_row_count": len(rows),
            "queue_row_count": len(queue["rows"]),
            "pass": len(rows) == len(queue["rows"]),
        },
        "uncovered_rows_are_listed_explicitly": {
            "uncovered_row_count": len(uncovered),
            "uncovered_rows": [row["row_id"] for row in uncovered],
            "pass": len(uncovered) == 0,
        },
    }
    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )
    out = {
        "name": "engine_lab_successor_coverage_audit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": CLASSIFICATION,
        "sim_execution_kind": "controller_index",
        "controller_index_exempt": True,
        "controller_index_exemption_reason": (
            "This audit checks controller coverage over existing queue rows; it does "
            "not create sim physics or admit QIT, GStack, axis, or engine claims."
        ),
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "cycle_protocol_receipt_status_matrix": str(RESULT_DIR / "cycle_protocol_receipt_status_matrix_results.json"),
            "engine_lab_open_row_audit": str(RESULT_DIR / "engine_lab_open_row_audit_results.json"),
            "engine_lab_next_work_queue": str(RESULT_DIR / "engine_lab_next_work_queue_results.json"),
        },
        "source_receipt_mtimes": receipt_mtimes(source_names),
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "queue_row_count": len(rows),
            "active_uncovered_row_count": len(uncovered),
            "covered_by_successor_count": sum(
                row["recommended_lane"].startswith("successor_receipt_available_") for row in rows
            ),
            "covered_by_consolidated_closed_count": sum(
                row["recommended_lane"].startswith("closed_by_") for row in rows
            ),
            "covered_by_superseded_count": sum(
                row["recommended_lane"].startswith("superseded_by_") for row in rows
            ),
            "source_rows_preserved_negative": all(row["source_negative_preserved"] for row in rows),
            "qit_or_axis_promotion_allowed": False,
            "schema_error_count": len(schema_errors),
            "scope_note": divergence_log,
        },
        "rows": rows,
        "uncovered_rows": uncovered,
        "schema_errors": schema_errors,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "engine_lab_successor_coverage_audit_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    write_visual_payload(out)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
