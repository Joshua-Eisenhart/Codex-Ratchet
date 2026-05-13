#!/usr/bin/env python3
"""Classify nonpassing engine-lab rows without promoting or smoothing them."""

from __future__ import annotations

import json
import pathlib
from typing import Any


CLASSIFICATION = "controller_audit"
classification = CLASSIFICATION
divergence_log = (
    "Controller audit over engine-lab rows with summary.all_pass=false. "
    "It separates coverage completion from open scientific failures, repair "
    "targets, and topology/readout sidecars."
)

LEGO_IDS = ["cycle_protocol_receipt_status_matrix", "repair_queue", "graveyard_variant"]
PRIMARY_LEGO_IDS = ["cycle_protocol_receipt_status_matrix"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads matrix and row receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "resolves canonical receipt paths"},
}
TOOL_INTEGRATION_DEPTH = {tool: "supportive" for tool in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def failed_checks(result: dict[str, Any]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for section_name in ["positive", "negative", "boundary", "checks", "fences", "proof_fences"]:
        section = result.get(section_name)
        if not isinstance(section, dict):
            continue
        for check_name, check in section.items():
            if isinstance(check, dict) and check.get("pass") is False:
                failures.append({"section": section_name, "check": check_name})
    return failures


def load_translation_targets() -> dict[str, dict[str, Any]]:
    path = RESULT_DIR / "engine_lab_translation_targets_results.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["row_id"]: row for row in data.get("rows", [])}


SUCCESSOR_ROWS = {
    "carnot_entropy_family_array": [
        "carnot_entropy_family_open_split",
    ],
    "carnot_forward_asymmetric": [
        "carnot_forward_cold_leg_dominance_successor",
    ],
    "carnot_reverse_asymmetric": [
        "carnot_reverse_balanced_return_successor",
    ],
    "szilard_ordering_sensitivity": [
        "szilard_ordering_nonmonotone_noise_successor",
    ],
    "szilard_record_reset_repair_sweep": [
        "szilard_record_lifetime_repair_successor",
    ],
    "szilard_substep_refinement_sweep": [
        "szilard_substep_ordering_reset_successor",
    ],
    "szilard_topology_entropy_array": [
        "szilard_topology_positive_diversity_successor",
    ],
    "qit_szilard_record_translation_lane": [
        "qit_szilard_record_repair_translation_lane",
        "qit_szilard_record_hard_reset_translation_lane",
        "qit_szilard_record_ordering_translation_lane",
        "qit_szilard_record_ordering_refinement_translation_lane",
        "szilard_record_ordering_refinement_reset_swing_sweep",
        "szilard_record_ordering_refinement_reset_axis_widened_sweep",
        "szilard_record_ordering_refinement_measurement_accuracy_recheck",
    ],
    "qit_szilard_substep_refinement_translation_lane": [
        "qit_szilard_substep_translation_lane",
        "qit_szilard_substep_balanced_translation_lane",
        "qit_szilard_substep_ordering_push_translation_lane",
    ],
}


def load_successors(row_id: str) -> list[dict[str, Any]]:
    successors = []
    for successor_id in SUCCESSOR_ROWS.get(row_id, []):
        path = RESULT_DIR / f"{successor_id}_results.json"
        if not path.exists():
            successors.append({"row_id": successor_id, "exists": False, "all_pass": False})
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        summary = data.get("summary", {})
        successors.append(
            {
                "row_id": successor_id,
                "exists": True,
                "classification": data.get("classification"),
                "all_pass": bool(summary.get("all_pass")),
                "scope_note": summary.get("scope_note"),
            }
        )
    return successors


def load_consolidated_rechecks() -> dict[str, dict[str, Any]]:
    path = RESULT_DIR / "engine_lab_repair_gap_consolidated_admission_results.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["row_id"]: row for row in data.get("rows", [])}


def classify(row: dict[str, Any], result: dict[str, Any], target: dict[str, Any] | None) -> dict[str, Any]:
    relation = row["likely_constraint_relation"]
    row_id = row["id"]
    classification = result.get("classification")
    failures = failed_checks(result)
    successors = load_successors(row_id)
    passing_successors = [successor for successor in successors if successor.get("all_pass")]

    if row_id == "engine_lab_repair_gap_consolidated_admission":
        class_label = "controller_recheck_open"
        next_allowed = "repair_or_leave_open_the_underlying_repair_gap_rows"
        promotion_blocker = "controller recheck reports one or more underlying repair-gap blockers still open"
    elif relation == "qit_aligned_repair_surface":
        class_label = "repair_gap"
        next_allowed = (
            "use_passing_successor_as_repair_evidence_keep_original_as_negative"
            if passing_successors
            else "tighten_exact_translation_metrics_before_admission"
        )
        promotion_blocker = "strict translation gaps remain above row-local bounds"
    elif relation == "controller_readout_surface":
        class_label = "readout_split"
        next_allowed = "use_as_negative_readout_evidence_or_rewrite_hypothesis"
        promotion_blocker = "readout families do not currently agree on the claimed ordering"
    elif "topology" in relation or "topology" in row_id:
        class_label = "topology_sidecar_or_graveyard"
        next_allowed = "keep_as_topology_variant_until_reexpressed_on_strict_carrier"
        promotion_blocker = "topology geometry is informative but not yet strict QIT carrier evidence"
    elif relation == "open_or_likely_outside_strict_qit_core":
        class_label = "open_lab_failure"
        next_allowed = "repair_open_row_or_convert_to_negative_graveyard_variant"
        promotion_blocker = "open stochastic row does not satisfy its own pass conditions"
    else:
        class_label = "unclassified_open_row"
        next_allowed = "manual_audit_required"
        promotion_blocker = "nonpassing row has no controller classification"

    return {
        "row_id": row_id,
        "classification": classification,
        "level": row["level"],
        "engine_family": row["engine_family"],
        "likely_constraint_relation": relation,
        "audit_class": class_label,
        "next_allowed_action": next_allowed,
        "promotion_blocker": promotion_blocker,
        "target_action_label": target.get("action_label") if target else None,
        "target_qit_row_id": target.get("target_qit_row_id") if target else None,
        "translation_closeness_score": target.get("translation_closeness_score") if target else None,
        "failed_checks": failures,
        "failed_check_count": len(failures),
        "successor_rows": successors,
        "passing_successor_count": len(passing_successors),
        "summary": result.get("summary", {}),
    }


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "rows": [
            {
                "row_id": row["row_id"],
                "engine_family": row["engine_family"],
                "audit_class": row["audit_class"],
                "next_allowed_action": row["next_allowed_action"],
                "promotion_blocker": row["promotion_blocker"],
                "failed_check_count": row["failed_check_count"],
                "failed_checks": row["failed_checks"],
                "target_qit_row_id": row["target_qit_row_id"],
                "passing_successor_count": row["passing_successor_count"],
                "successor_rows": row["successor_rows"],
                "consolidated_admission_status": row["consolidated_admission_status"],
                "consolidated_admission_receipt": row["consolidated_admission_receipt"],
            }
            for row in result["rows"]
        ],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_visual_payload(result)
    js = "window.ENGINE_LAB_OPEN_ROW_AUDIT_DATA = " + json.dumps(payload, indent=2, default=str) + ";\n"
    (VIS_DIR / "engine-lab-open-row-audit-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    matrix = load_result("cycle_protocol_receipt_status_matrix_results.json")
    target_by_row = load_translation_targets()
    consolidated_by_row = load_consolidated_rechecks()
    matrix_summary = matrix["summary"]
    nonpassing_ids = matrix_summary.get("nonpassing_row_ids", [])
    matrix_rows = {row["id"]: row for row in matrix.get("rows", [])}

    audit_rows = []
    missing = []
    for row_id in nonpassing_ids:
        row = matrix_rows.get(row_id)
        if row is None:
            missing.append({"row_id": row_id, "reason": "missing_from_matrix_rows"})
            continue
        result_path = pathlib.Path(row["result_file"])
        if not result_path.exists():
            missing.append({"row_id": row_id, "reason": "missing_result_file", "path": str(result_path)})
            continue
        result = json.loads(result_path.read_text(encoding="utf-8"))
        audit_row = classify(row, result, target_by_row.get(row_id))
        consolidated = consolidated_by_row.get(row_id)
        audit_row["consolidated_admission_status"] = consolidated.get("status") if consolidated else "not_run"
        audit_row["consolidated_admission_receipt"] = (
            str(RESULT_DIR / "engine_lab_repair_gap_consolidated_admission_results.json")
            if consolidated
            else None
        )
        audit_rows.append(audit_row)

    class_counts = {
        label: sum(row["audit_class"] == label for row in audit_rows)
        for label in sorted({row["audit_class"] for row in audit_rows})
    }
    repair_gap_rows = [row for row in audit_rows if row["audit_class"] == "repair_gap"]
    repair_gap_rechecked = [
        row for row in repair_gap_rows if row["consolidated_admission_status"] != "not_run"
    ]
    unclassified = [row["row_id"] for row in audit_rows if row["audit_class"] == "unclassified_open_row"]
    all_classified = not missing and not unclassified and len(audit_rows) == len(nonpassing_ids)
    out = {
        "name": "engine_lab_open_row_audit",
        "classification": CLASSIFICATION,
        "sim_execution_kind": "controller_index",
        "controller_index_exempt": True,
        "controller_index_exemption_reason": (
            "This audit classifies existing engine-lab receipts and does not claim "
            "new sim physics, QIT admission, or row-level repair success."
        ),
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "cycle_protocol_receipt_status_matrix": str(RESULT_DIR / "cycle_protocol_receipt_status_matrix_results.json"),
            "engine_lab_translation_targets": str(RESULT_DIR / "engine_lab_translation_targets_results.json"),
        },
        "summary": {
            "audit_complete": bool(all_classified),
            "matrix_all_pass": matrix_summary.get("all_pass"),
            "coverage_status": matrix_summary.get("coverage_status"),
            "matrix_status": matrix_summary.get("matrix_status"),
            "available_rows": matrix_summary.get("available_rows"),
            "missing_rows": matrix_summary.get("missing_rows"),
            "nonpassing_row_count": len(nonpassing_ids),
            "audited_nonpassing_rows": len(audit_rows),
            "missing_audit_rows": len(missing),
            "unclassified_open_rows": len(unclassified),
            "audit_class_counts": class_counts,
            "repair_gap_rows": len(repair_gap_rows),
            "repair_gap_rows_with_passing_successor": sum(
                row["passing_successor_count"] > 0 for row in repair_gap_rows
            ),
            "repair_gap_rows_with_consolidated_recheck": len(repair_gap_rechecked),
            "repair_gap_rows_closed_by_consolidated_recheck": sum(
                row["consolidated_admission_status"] == "closed" for row in repair_gap_rechecked
            ),
            "repair_gap_rows_still_open_after_consolidated_recheck": sum(
                row["consolidated_admission_status"] == "still_open" for row in repair_gap_rechecked
            ),
            "qit_or_axis_promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "rows": audit_rows,
        "missing": missing,
        "unclassified": unclassified,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "engine_lab_open_row_audit_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(out)
    print(out_path)
    print(f"ALL PASS: {all_classified}")


if __name__ == "__main__":
    main()
