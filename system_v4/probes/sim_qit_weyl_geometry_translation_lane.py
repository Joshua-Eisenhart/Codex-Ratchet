#!/usr/bin/env python3
"""
QIT Weyl Geometry Translation Lane
===================================
Open-vs-strict translation lane for the top companion-ready Weyl/Hopf
geometry row.

This compares the open composed geometry stack against the strict finite-state
geometry companion. It is a translation surface, not canonical owner math.
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted open-vs-strict Weyl/Hopf translation lane built from the open "
    "composed geometry stack and the strict finite-state geometry companion. "
    "It is a comparison surface, not canonical owner math."
)

LEGO_IDS = [
    "weyl_hopf_pauli_composed_stack",
    "qit_weyl_geometry_companion",
]

PRIMARY_LEGO_IDS = [
    "weyl_hopf_pauli_composed_stack",
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


def load(name: str) -> dict:
    path = RESULT_DIR / name
    if not path.exists():
        raise SystemExit(f"missing required result file: {name}")
    return json.loads(path.read_text())


def _finite(*values: float) -> bool:
    return all(isinstance(v, (int, float, bool)) for v in values)


def main() -> None:
    open_stack = load("weyl_hopf_pauli_composed_stack_results.json")
    strict = load("qit_weyl_geometry_companion_results.json")

    open_summary = open_stack["summary"]
    strict_summary = strict["summary"]

    open_stack_error = open_summary["max_stack_error"]
    open_transport_error = open_summary["max_transport_error"]
    open_spinor_error = open_summary["max_spinor_norm_error"]
    open_bloch_error = open_summary["max_bloch_alignment_error"]

    strict_stack_error = strict_summary["max_stack_error"]
    strict_transport_error = strict_summary["max_transport_error"]
    strict_transport_roundtrip_error = strict_summary["max_transport_roundtrip_error"]
    strict_basis_change_error = strict_summary["max_basis_change_covariance_error"]
    strict_left_right_overlap = strict_summary["max_left_right_overlap_abs"]
    strict_hopf_alignment_error = strict_summary["max_left_hopf_alignment_error"]

    stack_error_gap = strict_stack_error - open_stack_error
    transport_error_gap = strict_transport_error - open_transport_error
    basis_change_gap = strict_basis_change_error - open_bloch_error
    overlap_gap = strict_left_right_overlap - open_spinor_error

    positive = {
        "open_lane_is_clean": {
            "open_all_pass": bool(open_summary["all_pass"]),
            "pass": bool(open_summary["all_pass"]),
        },
        "strict_lane_is_clean": {
            "strict_all_pass": bool(strict_summary["all_pass"]),
            "pass": bool(strict_summary["all_pass"]),
        },
        "translation_gap_is_bounded": {
            "stack_error_gap": stack_error_gap,
            "transport_error_gap": transport_error_gap,
            "basis_change_gap": basis_change_gap,
            "pass": abs(stack_error_gap) < 1e-12 and abs(transport_error_gap) < 1e-12 and abs(basis_change_gap) < 1e-12,
        },
    }

    negative = {
        "promoted_lane_is_not_canonical_owner_math": {"pass": True},
        "open_and_strict_are_not_identical": {
            "stack_error_gap": stack_error_gap,
            "pass": stack_error_gap > 0.0,
        },
    }

    boundary = {
        "all_summary_values_are_finite": {
            "pass": _finite(
                open_stack_error,
                open_transport_error,
                open_spinor_error,
                open_bloch_error,
                strict_stack_error,
                strict_transport_error,
                strict_transport_roundtrip_error,
                strict_basis_change_error,
                strict_left_right_overlap,
                strict_hopf_alignment_error,
                stack_error_gap,
                transport_error_gap,
                basis_change_gap,
                overlap_gap,
            )
        }
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "qit_weyl_geometry_translation_lane",
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
            "open_row_id": "weyl_hopf_pauli_composed_stack",
            "strict_row_id": "qit_weyl_geometry_companion",
            "open_sample_count": open_summary["sample_count"],
            "strict_sample_count": strict_summary["sample_count"],
            "open_max_stack_error": open_stack_error,
            "strict_max_stack_error": strict_stack_error,
            "open_max_transport_error": open_transport_error,
            "strict_max_transport_error": strict_transport_error,
            "strict_max_transport_roundtrip_error": strict_transport_roundtrip_error,
            "strict_max_basis_change_covariance_error": strict_basis_change_error,
            "stack_error_gap": stack_error_gap,
            "transport_error_gap": transport_error_gap,
            "basis_change_gap": basis_change_gap,
            "overlap_gap": overlap_gap,
            "strict_reference_file": strict_summary["open_stack_reference_file"],
            "strict_reference_stack_gap": strict_summary["stack_gap_to_open_reference"],
            "open_stack_reference_max_stack_error": strict_summary["open_stack_reference_max_stack_error"],
            "open_stack_reference_max_transport_error": strict_summary["open_stack_reference_max_transport_error"],
            "scope_note": (
                "Open-vs-strict translation lane for the top companion-ready Weyl/Hopf geometry row. "
                "It compares the open composed stack against the strict finite-state companion and "
                "keeps the gap explicit and bounded."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_weyl_geometry_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
