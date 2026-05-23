#!/usr/bin/env python3
"""Build a bounded next-work queue from the engine-lab open-row audit."""

from __future__ import annotations

import json
import pathlib
from typing import Any


CLASSIFICATION = "controller_queue_audit"
classification = CLASSIFICATION
divergence_log = (
    "Controller queue derived from engine-lab open-row audit and repair-priority "
    "receipts. It does not claim row closure; it names bounded next sim moves."
)

LEGO_IDS = ["engine_lab_matrix", "repair_queue", "graveyard_variant"]
PRIMARY_LEGO_IDS = ["engine_lab_matrix"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads audit/priority receipts and writes queue"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {tool: "supportive" for tool in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def priority_map() -> dict[str, dict[str, Any]]:
    path = RESULT_DIR / "engine_lab_repair_priority_results.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["row_id"]: row for row in data.get("rows", [])}


def graveyard_coverage() -> dict[str, dict[str, Any]]:
    coverage: dict[str, dict[str, Any]] = {}
    graveyards = [
        "carnot_asymmetric_direction_graveyard_results.json",
        "szilard_open_failure_graveyard_results.json",
        "engine_lab_sidecar_graveyard_results.json",
    ]
    for name in graveyards:
        path = RESULT_DIR / name
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("rows", []):
            source = row.get("source_row")
            if not source:
                continue
            entry = coverage.setdefault(
                source,
                {
                    "graveyard_receipts": [],
                    "graveyard_variant_count": 0,
                    "graveyard_killed_count": 0,
                    "graveyard_survived_count": 0,
                },
            )
            receipt = str(path)
            if receipt not in entry["graveyard_receipts"]:
                entry["graveyard_receipts"].append(receipt)
            entry["graveyard_variant_count"] += 1
            entry["graveyard_killed_count"] += int(row.get("verdict") == "killed")
            entry["graveyard_survived_count"] += int(row.get("verdict") == "survived")
    return coverage


def recommended_lane(row: dict[str, Any]) -> str:
    audit_class = row["audit_class"]
    row_id = row["row_id"]
    if row_id == "engine_lab_repair_gap_consolidated_admission":
        return "controller_recheck_after_underlying_repair"
    if row_id == "szilard_record_ordering_refinement_reset_swing_sweep":
        return "superseded_by_reset_parameter_recheck_keep_as_negative"
    if row_id == "measurement_record_reset_parameter_sweep":
        return "use_as_reset_parameter_successor_then_recheck_remaining_measurement_accuracy_gap"
    if audit_class == "repair_gap":
        return "exact_threshold_recheck_or_successor_translation_lane"
    if audit_class == "open_lab_failure":
        return "bounded_parameter_repair_or_negative_graveyard_variant"
    if audit_class == "readout_split":
        return "readout_family_split_graveyard_or_readout_rewrite"
    if audit_class == "topology_sidecar_or_graveyard":
        return "topology_sidecar_reexpression_on_strict_carrier"
    return "manual_controller_audit"


def coverage_adjusted_lane(row: dict[str, Any], coverage: dict[str, Any] | None) -> str:
    base = recommended_lane(row)
    if row.get("consolidated_admission_status") == "closed":
        return "closed_by_consolidated_successor_keep_source_negative"
    if row.get("passing_successor_count", 0) > 0 and row["audit_class"] == "readout_split":
        return "successor_receipt_available_keep_source_as_negative_readout_split"
    if row.get("passing_successor_count", 0) > 0 and row["audit_class"] == "open_lab_failure":
        return "successor_receipt_available_keep_source_as_negative_open_failure"
    if row.get("passing_successor_count", 0) > 0 and row["audit_class"] == "topology_sidecar_or_graveyard":
        return "successor_receipt_available_keep_source_as_negative_topology_sidecar"
    if coverage and row["audit_class"] in {
        "open_lab_failure",
        "readout_split",
        "topology_sidecar_or_graveyard",
    }:
        return "graveyard_covered_choose_new_repair_or_leave_open"
    return base


def queue_rank(row: dict[str, Any], priority: dict[str, Any] | None, coverage: dict[str, Any] | None) -> tuple[int, float, str]:
    if priority is not None:
        score = float(priority.get("translation_closeness_score", 0.0))
    else:
        score = 0.0
    class_order = {
        "repair_gap": 0,
        "open_lab_failure": 1,
        "readout_split": 2,
        "topology_sidecar_or_graveyard": 3,
        "controller_recheck_open": 4,
    }.get(row["audit_class"], 5)
    if row.get("consolidated_admission_status") == "closed":
        class_order = 4
    if recommended_lane(row).startswith("superseded_by_"):
        class_order = 5
    if coverage and row["audit_class"] in {
        "open_lab_failure",
        "readout_split",
        "topology_sidecar_or_graveyard",
    }:
        class_order = 3
    if row.get("passing_successor_count", 0) > 0 and row["audit_class"] == "readout_split":
        class_order = 4
    if row.get("passing_successor_count", 0) > 0 and row["audit_class"] == "open_lab_failure":
        class_order = 4
    if row.get("passing_successor_count", 0) > 0 and row["audit_class"] == "topology_sidecar_or_graveyard":
        class_order = 4
    return (class_order, -score, row["row_id"])


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "rows": result["rows"],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    js = "window.ENGINE_LAB_NEXT_WORK_QUEUE_DATA = " + json.dumps(
        build_visual_payload(result), indent=2, default=str
    ) + ";\n"
    (VIS_DIR / "engine-lab-next-work-queue-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    audit = load("engine_lab_open_row_audit_results.json")
    priorities = priority_map()
    graveyard_by_row = graveyard_coverage()
    rows = []
    for audit_row in audit.get("rows", []):
        priority = priorities.get(audit_row["row_id"])
        coverage = graveyard_by_row.get(audit_row["row_id"])
        failed_checks = audit_row.get("failed_checks", [])
        rows.append(
            {
                "row_id": audit_row["row_id"],
                "audit_class": audit_row["audit_class"],
                "engine_family": audit_row["engine_family"],
                "level": audit_row["level"],
                "next_allowed_action": audit_row["next_allowed_action"],
                "recommended_lane": coverage_adjusted_lane(audit_row, coverage),
                "graveyard_covered": bool(coverage),
                "graveyard_variant_count": coverage.get("graveyard_variant_count") if coverage else 0,
                "graveyard_killed_count": coverage.get("graveyard_killed_count") if coverage else 0,
                "graveyard_survived_count": coverage.get("graveyard_survived_count") if coverage else 0,
                "graveyard_receipts": coverage.get("graveyard_receipts") if coverage else [],
                "promotion_blocker": audit_row["promotion_blocker"],
                "failed_check_count": audit_row["failed_check_count"],
                "failed_checks": failed_checks,
                "passing_successor_count": audit_row.get("passing_successor_count", 0),
                "consolidated_admission_status": audit_row.get("consolidated_admission_status"),
                "translation_closeness_score": (
                    priority.get("translation_closeness_score") if priority is not None else None
                ),
                "priority_bucket": priority.get("priority_bucket") if priority is not None else None,
                "qit_or_axis_promotion_allowed": False,
            }
        )
    rows.sort(key=lambda row: queue_rank(row, priorities.get(row["row_id"]), graveyard_by_row.get(row["row_id"])))
    active_rows = [
        row
        for row in rows
        if not (
            row["recommended_lane"].startswith("successor_receipt_available_")
            or row["recommended_lane"].startswith("closed_by_")
            or row["recommended_lane"].startswith("superseded_by_")
        )
    ]
    result = {
        "name": "engine_lab_next_work_queue",
        "classification": CLASSIFICATION,
        "sim_execution_kind": "controller_index",
        "controller_index_exempt": True,
        "controller_index_exemption_reason": (
            "This queue orders existing open-row receipts into bounded next actions; "
            "it does not create sim physics or admit QIT, GStack, axis, or engine claims."
        ),
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "engine_lab_open_row_audit": str(RESULT_DIR / "engine_lab_open_row_audit_results.json"),
            "engine_lab_repair_priority": str(RESULT_DIR / "engine_lab_repair_priority_results.json"),
        },
        "summary": {
            "queue_complete": True,
            "open_row_count": len(rows),
            "active_uncovered_row_count": len(active_rows),
            "repair_gap_count": sum(row["audit_class"] == "repair_gap" for row in rows),
            "open_lab_failure_count": sum(row["audit_class"] == "open_lab_failure" for row in rows),
            "graveyard_covered_open_row_count": sum(row["graveyard_covered"] for row in rows),
            "top_row_id": rows[0]["row_id"] if rows else None,
            "top_active_row_id": active_rows[0]["row_id"] if active_rows else None,
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": rows,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "engine_lab_next_work_queue_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"QUEUE ROWS: {len(rows)}")


if __name__ == "__main__":
    main()
