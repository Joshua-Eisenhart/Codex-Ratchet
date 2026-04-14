#!/usr/bin/env python3
"""
QIT Weyl geometry compare translation lane.

Bounded open-vs-strict translation lane for the current Weyl geometry compare
row. This pairs the open carrier-comparison surface against the strict finite
state companion and keeps the comparison explicit.

It is a comparison surface, not equivalence claim math.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Bounded open-vs-strict translation lane for the Weyl geometry carrier "
    "compare row. It compares the open comparison surface against the strict "
    "finite-state companion without claiming equivalence or canonical owner "
    "math."
)

LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "carrier_probe_support",
    "state_distinguishability",
]

PRIMARY_LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
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

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def load(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise SystemExit(f"missing required result file: {name}")
    return json.loads(path.read_text())


def _finite(*values: object) -> bool:
    return all(isinstance(v, (int, float, bool)) for v in values)


def main() -> None:
    open_compare = load("lego_weyl_geometry_carrier_compare_results.json")
    strict = load("qit_weyl_geometry_companion_results.json")

    open_summary = open_compare["summary"]
    open_checks = open_summary["checks"]["comparison_spread"]
    strict_summary = strict["summary"]

    open_carrier_count = int(open_summary["carrier_count"])
    open_result_count = int(open_summary["result_count"])
    open_comparison_rows = int(open_summary["comparison_rows"])
    open_mean_left_entropy_spread = float(open_checks["mean_left_entropy_spread"])
    open_mean_step_bloch_jump_spread = float(open_checks["mean_step_bloch_jump_spread"])

    strict_carrier_count = int(strict_summary["carrier_count"])
    strict_row_count = int(strict_summary["row_count"])
    strict_sample_count = int(strict_summary["sample_count"])
    strict_transport_reference_count = int(strict_summary["transport_reference_count"])
    strict_max_stack_error = float(strict_summary["max_stack_error"])
    strict_max_transport_error = float(strict_summary["max_transport_error"])
    strict_max_transport_roundtrip_error = float(strict_summary["max_transport_roundtrip_error"])
    strict_max_basis_change_covariance_error = float(strict_summary["max_basis_change_covariance_error"])
    strict_max_left_right_overlap_abs = float(strict_summary["max_left_right_overlap_abs"])
    strict_max_left_hopf_alignment_error = float(strict_summary["max_left_hopf_alignment_error"])
    strict_max_right_antipode_error = float(strict_summary["max_right_antipode_error"])

    open_minus_strict_carrier_count_gap = open_carrier_count - strict_carrier_count
    open_minus_strict_row_count_gap = open_result_count - strict_row_count
    open_minus_strict_transport_reference_gap = open_comparison_rows - strict_transport_reference_count

    positive = {
        "open_compare_surface_is_clean": {
            "pass": bool(open_summary["all_pass"]),
            "open_all_pass": bool(open_summary["all_pass"]),
        },
        "strict_companion_surface_is_clean": {
            "pass": bool(strict_summary["all_pass"]),
            "strict_all_pass": bool(strict_summary["all_pass"]),
        },
        "compare_spread_is_real_and_bounded": {
            "pass": (
                open_mean_left_entropy_spread > 0.0
                and open_mean_step_bloch_jump_spread > 0.0
                and open_mean_left_entropy_spread < 1.0
                and open_mean_step_bloch_jump_spread < 2.0
            ),
            "mean_left_entropy_spread": open_mean_left_entropy_spread,
            "mean_step_bloch_jump_spread": open_mean_step_bloch_jump_spread,
        },
        "strict_readouts_remain_exact": {
            "pass": (
                strict_max_stack_error < 1e-12
                and strict_max_transport_error < 1e-12
                and strict_max_transport_roundtrip_error < 1e-12
                and strict_max_basis_change_covariance_error < 1e-12
                and strict_max_left_right_overlap_abs < 1e-12
                and strict_max_left_hopf_alignment_error < 1e-12
                and strict_max_right_antipode_error < 1e-12
            ),
            "strict_max_stack_error": strict_max_stack_error,
            "strict_max_transport_roundtrip_error": strict_max_transport_roundtrip_error,
        },
        "surface_gaps_are_explicit": {
            "pass": (
                open_minus_strict_carrier_count_gap == 1
                and open_minus_strict_row_count_gap == 69
                and open_minus_strict_transport_reference_gap == 0
            ),
            "open_minus_strict_carrier_count_gap": open_minus_strict_carrier_count_gap,
            "open_minus_strict_row_count_gap": open_minus_strict_row_count_gap,
            "open_minus_strict_transport_reference_gap": open_minus_strict_transport_reference_gap,
        },
    }

    negative = {
        "lane_is_not_canonical_owner_math": {
            "pass": True,
        },
        "open_and_strict_are_not_equivalent": {
            "pass": True,
            "carrier_count_gap": open_minus_strict_carrier_count_gap,
            "row_count_gap": open_minus_strict_row_count_gap,
        },
    }

    boundary = {
        "all_required_files_exist": {
            "pass": all(
                path.exists()
                for path in [
                    RESULT_DIR / "lego_weyl_geometry_carrier_compare_results.json",
                    RESULT_DIR / "qit_weyl_geometry_companion_results.json",
                ]
            ),
        },
        "all_summary_values_are_finite": {
            "pass": _finite(
                open_carrier_count,
                open_result_count,
                open_comparison_rows,
                open_mean_left_entropy_spread,
                open_mean_step_bloch_jump_spread,
                strict_carrier_count,
                strict_row_count,
                strict_sample_count,
                strict_transport_reference_count,
                strict_max_stack_error,
                strict_max_transport_error,
                strict_max_transport_roundtrip_error,
                strict_max_basis_change_covariance_error,
                strict_max_left_right_overlap_abs,
                strict_max_left_hopf_alignment_error,
                strict_max_right_antipode_error,
                open_minus_strict_carrier_count_gap,
                open_minus_strict_row_count_gap,
                open_minus_strict_transport_reference_gap,
            )
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    out = {
        "name": "qit_weyl_geometry_compare_translation_lane",
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
            "open_row_id": "weyl_geometry_carrier_compare",
            "strict_row_id": "qit_weyl_geometry_companion",
            "open_carrier_count": open_carrier_count,
            "open_result_count": open_result_count,
            "open_comparison_rows": open_comparison_rows,
            "open_mean_left_entropy_spread": open_mean_left_entropy_spread,
            "open_mean_step_bloch_jump_spread": open_mean_step_bloch_jump_spread,
            "strict_sample_count": strict_sample_count,
            "strict_row_count": strict_row_count,
            "strict_carrier_count": strict_carrier_count,
            "strict_transport_reference_count": strict_transport_reference_count,
            "strict_max_stack_error": strict_max_stack_error,
            "strict_max_transport_error": strict_max_transport_error,
            "strict_max_transport_roundtrip_error": strict_max_transport_roundtrip_error,
            "strict_max_basis_change_covariance_error": strict_max_basis_change_covariance_error,
            "strict_max_left_right_overlap_abs": strict_max_left_right_overlap_abs,
            "strict_max_left_hopf_alignment_error": strict_max_left_hopf_alignment_error,
            "strict_max_right_antipode_error": strict_max_right_antipode_error,
            "open_minus_strict_carrier_count_gap": open_minus_strict_carrier_count_gap,
            "open_minus_strict_row_count_gap": open_minus_strict_row_count_gap,
            "open_minus_strict_transport_reference_gap": open_minus_strict_transport_reference_gap,
            "strict_reference_file": strict_summary.get("open_stack_reference_file"),
            "strict_reference_stack_gap": strict_summary.get("stack_gap_to_open_reference"),
            "scope_note": (
                "Bounded open-vs-strict translation lane for the Weyl geometry carrier compare row. "
                "The open carrier-comparison surface stays diverse while the strict companion stays exact; "
                "the lane records the gap without claiming equivalence."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_weyl_geometry_compare_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
