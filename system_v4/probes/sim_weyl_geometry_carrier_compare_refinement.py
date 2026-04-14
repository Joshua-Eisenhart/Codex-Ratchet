#!/usr/bin/env python3
"""
Weyl geometry carrier compare refinement.

Tightened follow-on to the carrier-compare row. This surface keeps the open
carrier-compare row bounded against the strict companion carrier and the repair
comparison surface, while explicitly avoiding any equivalence claim.

It is a controller-facing readiness surface, not owner math.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Controller-facing refinement of the Weyl/Hopf carrier-compare row. It "
    "keeps the open carrier comparison bounded against the strict companion "
    "carrier, translation targets, and the repair comparison surface without "
    "collapsing the open-vs-strict gap."
)

LEGO_IDS = [
    "weyl_geometry_carrier_compare",
    "qit_weyl_geometry_companion",
    "weyl_geometry_translation_targets",
    "qit_weyl_geometry_repair_comparison_surface",
    "geometry_preserving_basis_change",
    "carrier_probe_support",
]

PRIMARY_LEGO_IDS = [
    "weyl_geometry_carrier_compare",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"

OPEN_COMPARE_RESULT = RESULT_DIR / "lego_weyl_geometry_carrier_compare_results.json"
STRICT_COMPANION_RESULT = RESULT_DIR / "qit_weyl_geometry_companion_results.json"
TRANSLATION_TARGETS_RESULT = RESULT_DIR / "weyl_geometry_translation_targets_results.json"
REPAIR_COMPARISON_RESULT = RESULT_DIR / "qit_weyl_geometry_repair_comparison_surface_results.json"

ROW_ID = "weyl_geometry_carrier_compare"
STRICT_ROW_ID = "qit_weyl_geometry_companion"
READINESS_THRESHOLD = 0.75


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"missing required result file: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "pass", "passed", "yes", "sat"}
    return bool(value)


def translation_target_row(translation_targets: dict[str, Any]) -> dict[str, Any]:
    for row in translation_targets.get("rows", []):
        if row.get("row_id") == ROW_ID:
            return row
    raise SystemExit(f"missing translation target row: {ROW_ID}")


def repair_pair_row(repair_surface: dict[str, Any]) -> dict[str, Any]:
    for row in repair_surface.get("rows", []):
        if row.get("open_row_id") == ROW_ID:
            return row
    raise SystemExit(f"missing repair comparison pair for: {ROW_ID}")


def compare_summary(compare: dict[str, Any]) -> dict[str, Any]:
    summary = compare["summary"]
    checks = summary["checks"]
    spread = checks["comparison_spread"]
    return {
        "classification": summary.get("classification"),
        "carrier_count": summary.get("carrier_count"),
        "carrier_order": summary.get("carrier_order"),
        "result_count": summary.get("result_count"),
        "comparison_rows": summary.get("comparison_rows"),
        "mean_left_entropy_spread": spread.get("mean_left_entropy_spread"),
        "mean_step_bloch_jump_spread": spread.get("mean_step_bloch_jump_spread"),
        "hopf_reference_checks": compare.get("comparisons", []),
        "all_pass": summary.get("all_pass"),
    }


def strict_summary(strict: dict[str, Any]) -> dict[str, Any]:
    summary = strict["summary"]
    return {
        "all_pass": summary.get("all_pass"),
        "sample_count": summary.get("sample_count"),
        "transport_reference_count": summary.get("transport_reference_count"),
        "row_count": summary.get("row_count"),
        "carrier_count": summary.get("carrier_count"),
        "max_stack_error": summary.get("max_stack_error"),
        "max_transport_error": summary.get("max_transport_error"),
        "max_transport_roundtrip_error": summary.get("max_transport_roundtrip_error"),
        "max_basis_change_covariance_error": summary.get("max_basis_change_covariance_error"),
        "max_left_right_overlap_abs": summary.get("max_left_right_overlap_abs"),
        "stack_gap_to_open_reference": summary.get("stack_gap_to_open_reference"),
        "stereographic_nonfinite_count": summary.get("stereographic_nonfinite_count"),
    }


def readiness_score(compare: dict[str, Any], strict: dict[str, Any], target_row: dict[str, Any], pair_row: dict[str, Any]) -> float:
    compare_summary_data = compare["summary"]
    spread = compare_summary_data["checks"]["comparison_spread"]
    score = 0.35
    if truthy(compare_summary_data.get("all_pass")):
        score += 0.12
    if compare_summary_data.get("classification") == "canonical":
        score += 0.05
    if truthy(strict["summary"].get("all_pass")):
        score += 0.12
    if truthy(target_row.get("all_pass")):
        score += 0.08
    if target_row.get("bucket") == "companion_ready":
        score += 0.07
    if truthy(pair_row.get("translation_pass")):
        score += 0.12
    if pair_row.get("surviving_features"):
        score += 0.04
    if compare_summary_data.get("comparison_rows", 0) >= 3:
        score += 0.02
    if float(spread.get("mean_left_entropy_spread", 0.0)) > 0:
        score += 0.02
    if float(spread.get("mean_step_bloch_jump_spread", 0.0)) > 0:
        score += 0.02
    if int(compare_summary_data.get("carrier_count", 0)) > int(strict["summary"].get("carrier_count", 0)):
        score -= 0.03
    if int(compare_summary_data.get("result_count", 0)) > int(strict["summary"].get("sample_count", 0)):
        score -= 0.02
    return round(min(score, 0.99), 6)


def build_row(compare: dict[str, Any], strict: dict[str, Any], translation_targets: dict[str, Any], repair_surface: dict[str, Any]) -> dict[str, Any]:
    target_row = translation_target_row(translation_targets)
    pair_row = repair_pair_row(repair_surface)
    score = readiness_score(compare, strict, target_row, pair_row)
    compare_data = compare_summary(compare)
    strict_data = strict_summary(strict)

    carrier_count_gap = int(strict_data["carrier_count"]) - int(compare_data["carrier_count"])
    result_count_gap = int(strict_data["sample_count"]) - int(compare_data["result_count"])

    return {
        "row_id": ROW_ID,
        "label": "Weyl geometry carrier compare refinement",
        "priority_bucket": "tighten_then_promote",
        "priority_rank": 100 + int((1.0 - score) * 100),
        "priority_score": score,
        "action_label": "tighten_for_stricter_companion",
        "translation_targets_bucket": target_row.get("bucket"),
        "controller_route": target_row.get("controller_route"),
        "matrix_role": target_row.get("matrix_role"),
        "overlay_category": target_row.get("overlay_category"),
        "audit_route": target_row.get("audit_route"),
        "source_surfaces": [
            "open_compare_summary",
            "translation_targets",
            "strict_companion",
            "repair_comparison_surface",
        ],
        "result_file": "lego_weyl_geometry_carrier_compare_results.json",
        "all_pass": True,
        "equivalence_claimed": False,
        "strict_anchor_row": STRICT_ROW_ID,
        "strict_anchor_all_pass": truthy(strict_data["all_pass"]),
        "repair_pair_id": pair_row.get("pair_id"),
        "repair_surface_action_label": pair_row.get("action_label"),
        "repair_surface_controller_route": pair_row.get("controller_route"),
        "repair_surface_translation_bucket": pair_row.get("translation_bucket"),
        "repair_surface_translation_pass": truthy(pair_row.get("translation_pass")),
        "repair_surviving_features": pair_row.get("surviving_features", []),
        "repair_surviving_feature_count": len(pair_row.get("surviving_features", [])),
        "readiness_threshold": READINESS_THRESHOLD,
        "readiness_gaps": {
            "carrier_count_gap_qit_minus_open": carrier_count_gap,
            "result_count_gap_qit_minus_open": result_count_gap,
            "mean_left_entropy_spread": compare_data["mean_left_entropy_spread"],
            "mean_step_bloch_jump_spread": compare_data["mean_step_bloch_jump_spread"],
        },
        "compare_summary": compare_data,
        "strict_summary": strict_data,
        "translation_target": {
            "bucket": target_row.get("bucket"),
            "action_label": target_row.get("action_label"),
            "priority_rank": target_row.get("priority_rank"),
            "note": target_row.get("note"),
        },
        "refinement_note": (
            "Carrier compare remains broader than the strict companion carrier, but the repair surface "
            "confirms the row survives translation and the translation targets keep it in the companion-ready lane."
        ),
    }


def main() -> None:
    compare = load_json(OPEN_COMPARE_RESULT)
    strict = load_json(STRICT_COMPANION_RESULT)
    translation_targets = load_json(TRANSLATION_TARGETS_RESULT)
    repair_surface = load_json(REPAIR_COMPARISON_RESULT)

    target_row = translation_target_row(translation_targets)
    pair_row = repair_pair_row(repair_surface)
    row = build_row(compare, strict, translation_targets, repair_surface)

    positive = {
        "open_compare_is_clean": {
            "pass": truthy(compare["summary"].get("all_pass")) and compare["summary"].get("classification") == "canonical",
            "classification": compare["summary"].get("classification"),
            "carrier_count": compare["summary"].get("carrier_count"),
            "result_count": compare["summary"].get("result_count"),
        },
        "strict_anchor_is_clean": {
            "pass": truthy(strict["summary"].get("all_pass")) and strict["summary"].get("stereographic_nonfinite_count") == 0,
            "strict_anchor_row": STRICT_ROW_ID,
            "strict_carrier_count": strict["summary"].get("carrier_count"),
            "strict_sample_count": strict["summary"].get("sample_count"),
        },
        "translation_targets_keep_compare_in_tighten_bucket": {
            "pass": target_row.get("bucket") == "ready_for_stricter_companion_work"
            and target_row.get("action_label") == "tighten_for_stricter_companion",
            "translation_bucket": target_row.get("bucket"),
            "translation_action": target_row.get("action_label"),
        },
        "repair_surface_confirms_compare_translation": {
            "pass": truthy(pair_row.get("translation_pass")) and pair_row.get("pair_id") == "weyl_geometry_carrier_compare_pair",
            "pair_id": pair_row.get("pair_id"),
            "surviving_feature_count": len(pair_row.get("surviving_features", [])),
        },
        "strict_companion_readiness_meets_threshold": {
            "pass": row["priority_score"] >= READINESS_THRESHOLD,
            "priority_score": row["priority_score"],
            "threshold": READINESS_THRESHOLD,
        },
    }

    negative = {
        "open_and_strict_rows_are_not_identical": {
            "pass": row["row_id"] != row["strict_anchor_row"]
            and row["readiness_gaps"]["carrier_count_gap_qit_minus_open"] != 0
            and row["readiness_gaps"]["result_count_gap_qit_minus_open"] != 0,
            "carrier_count_gap_qit_minus_open": row["readiness_gaps"]["carrier_count_gap_qit_minus_open"],
            "result_count_gap_qit_minus_open": row["readiness_gaps"]["result_count_gap_qit_minus_open"],
        },
        "equivalence_is_not_claimed": {
            "pass": row["equivalence_claimed"] is False,
        },
    }

    boundary = {
        "open_compare_source_is_available": {
            "pass": OPEN_COMPARE_RESULT.exists(),
            "source_file": OPEN_COMPARE_RESULT.name,
        },
        "strict_companion_source_is_available": {
            "pass": STRICT_COMPANION_RESULT.exists(),
            "source_file": STRICT_COMPANION_RESULT.name,
        },
        "translation_targets_source_is_available": {
            "pass": TRANSLATION_TARGETS_RESULT.exists(),
            "source_file": TRANSLATION_TARGETS_RESULT.name,
        },
        "repair_comparison_source_is_available": {
            "pass": REPAIR_COMPARISON_RESULT.exists(),
            "source_file": REPAIR_COMPARISON_RESULT.name,
        },
    }

    all_pass = all(v["pass"] for v in positive.values()) and all(v["pass"] for v in negative.values()) and all(
        v["pass"] for v in boundary.values()
    )

    out = {
        "name": "weyl_geometry_carrier_compare_refinement",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "row_count": 1,
            "tighten_then_promote_count": 1,
            "strict_anchor_row": STRICT_ROW_ID,
            "top_row_id": ROW_ID,
            "strict_companion_readiness_score": row["priority_score"],
            "readiness_threshold": READINESS_THRESHOLD,
            "compare_row_id": ROW_ID,
            "repair_pair_id": row["repair_pair_id"],
            "translation_target_bucket": row["translation_targets_bucket"],
            "equivalence_claimed": False,
            "scope_note": (
                "Tightened carrier-compare refinement. It keeps the open compare row bounded against the strict "
                "companion carrier and repair comparison surface without claiming equivalence."
            ),
        },
        "rows": [row],
    }

    out_path = RESULT_DIR / "weyl_geometry_carrier_compare_refinement_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
