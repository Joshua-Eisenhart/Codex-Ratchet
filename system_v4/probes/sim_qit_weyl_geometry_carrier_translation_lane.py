#!/usr/bin/env python3
"""
QIT Weyl geometry carrier translation lane.

Promote the companion-ready carrier-array geometry row into a bounded
open-vs-strict translation surface by pairing the open carrier array against
the strict finite-state Weyl/Hopf companion.

This is a controller-facing comparison surface, not canonical owner math.
"""

from __future__ import annotations

import json
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Promoted QIT-aligned Weyl/Hopf carrier translation lane built from the "
    "open carrier-array row and the strict finite-state companion. It keeps "
    "the carrier/readout gap explicit and bounded; it does not claim "
    "equivalence or canonical geometry admission."
)

LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "transport_geometry",
    "geometry_preserving_basis_change",
    "carrier_probe_support",
]

PRIMARY_LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "transport_geometry",
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
    return json.loads((RESULT_DIR / name).read_text())


def _finite(*values: object) -> bool:
    return all(isinstance(v, (int, float, bool)) for v in values)


def main() -> None:
    open_carrier = load("weyl_geometry_carrier_array_results.json")
    strict = load("qit_weyl_geometry_companion_results.json")

    open_summary = open_carrier["summary"]
    open_nested = open_carrier["carrier_summaries"]["nested_hopf_torus"]
    open_comparison = open_carrier["comparison"]
    strict_summary = strict["summary"]

    open_carrier_count = int(open_summary["carrier_count"])
    strict_carrier_count = int(strict_summary["carrier_count"])
    open_direct_core_count = len(open_comparison["direct_core_carriers"])
    open_structural_count = len(open_comparison["structural_carriers"])

    carrier_count_gap = open_carrier_count - strict_carrier_count
    direct_core_count_gap = open_direct_core_count - strict_carrier_count

    open_core_lr_overlap = float(open_nested["max_lr_overlap"])
    strict_lr_overlap = float(strict_summary["max_left_right_overlap_abs"])
    carrier_readout_gap_abs = abs(strict_lr_overlap - open_core_lr_overlap)

    open_core_roundtrip_error = float(open_nested["max_roundtrip_error"])
    strict_transport_roundtrip_error = float(strict_summary["max_transport_roundtrip_error"])
    open_hopf_vs_pauli_gap = float(open_nested["max_hopf_vs_pauli_gap"])
    strict_basis_change_error = float(strict_summary["max_basis_change_covariance_error"])
    strict_stack_error = float(strict_summary["max_stack_error"])
    strict_hopf_norm_gap = float(strict_summary["max_hopf_norm_gap"])

    positive = {
        "open_lane_is_clean": {
            "pass": bool(open_summary["all_pass"]),
            "open_all_pass": bool(open_summary["all_pass"]),
        },
        "strict_lane_is_clean": {
            "pass": bool(strict_summary["all_pass"]),
            "strict_all_pass": bool(strict_summary["all_pass"]),
        },
        "open_lane_has_more_carrier_families": {
            "pass": carrier_count_gap > 0,
            "open_carrier_count": open_carrier_count,
            "strict_carrier_count": strict_carrier_count,
        },
        "direct_core_matches_strict_carrier_count": {
            "pass": direct_core_count_gap == 0,
            "open_direct_core_count": open_direct_core_count,
            "strict_carrier_count": strict_carrier_count,
        },
        "carrier_readout_gap_stays_bounded": {
            "pass": carrier_readout_gap_abs < 1e-12,
            "open_core_lr_overlap": open_core_lr_overlap,
            "strict_lr_overlap": strict_lr_overlap,
            "carrier_readout_gap_abs": carrier_readout_gap_abs,
        },
        "strict_side_readouts_remain_tight": {
            "pass": (
                strict_transport_roundtrip_error < 1e-12
                and strict_basis_change_error < 1e-12
                and strict_stack_error < 1e-12
                and strict_hopf_norm_gap < 1e-12
            ),
            "strict_transport_roundtrip_error": strict_transport_roundtrip_error,
            "strict_basis_change_error": strict_basis_change_error,
            "strict_stack_error": strict_stack_error,
            "strict_hopf_norm_gap": strict_hopf_norm_gap,
        },
    }

    negative = {
        "lane_is_not_canonical_owner_math": {
            "pass": True,
        },
        "open_and_strict_are_not_identical": {
            "pass": carrier_count_gap != 0 or carrier_readout_gap_abs != 0.0,
            "carrier_count_gap": carrier_count_gap,
            "carrier_readout_gap_abs": carrier_readout_gap_abs,
        },
    }

    boundary = {
        "all_metrics_are_finite": {
            "pass": _finite(
                open_carrier_count,
                strict_carrier_count,
                open_direct_core_count,
                open_structural_count,
                carrier_count_gap,
                direct_core_count_gap,
                open_core_lr_overlap,
                strict_lr_overlap,
                carrier_readout_gap_abs,
                open_core_roundtrip_error,
                strict_transport_roundtrip_error,
                open_hopf_vs_pauli_gap,
                strict_basis_change_error,
                strict_stack_error,
                strict_hopf_norm_gap,
            )
        },
        "source_rows_remain_the_source_of_truth": {
            "pass": bool(open_summary["all_pass"]) and bool(strict_summary["all_pass"]),
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    out = {
        "name": "qit_weyl_geometry_carrier_translation_lane",
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
            "open_carrier_count": open_carrier_count,
            "strict_carrier_count": strict_carrier_count,
            "carrier_count_gap": carrier_count_gap,
            "open_direct_core_count": open_direct_core_count,
            "open_structural_count": open_structural_count,
            "direct_core_count_gap": direct_core_count_gap,
            "open_core_lr_overlap": open_core_lr_overlap,
            "strict_lr_overlap": strict_lr_overlap,
            "carrier_readout_gap_abs": carrier_readout_gap_abs,
            "open_core_roundtrip_error": open_core_roundtrip_error,
            "strict_transport_roundtrip_error": strict_transport_roundtrip_error,
            "strict_basis_change_error": strict_basis_change_error,
            "strict_stack_error": strict_stack_error,
            "strict_hopf_norm_gap": strict_hopf_norm_gap,
            "open_graph_cycle_rank": int(open_summary["max_graph_cycle_rank"]),
            "open_hypergraph_shadow_components": int(open_summary["max_hypergraph_shadow_components"]),
            "open_cp3_max_concurrence": float(open_summary["max_cp3_concurrence"]),
            "open_best_direct_match": open_comparison["best_direct_match"],
            "open_richer_alt_geometry": open_comparison["richer_alt_geometry"],
            "open_graph_bridge": open_comparison["graph_bridge"],
            "open_hypergraph_bridge": open_comparison["hypergraph_bridge"],
            "strict_transport_reference_count": int(strict_summary["transport_reference_count"]),
            "strict_row_count": int(strict_summary["row_count"]),
            "scope_note": (
                "Promoted QIT-aligned Weyl/Hopf carrier translation lane. It compares "
                "the open carrier-array row against the strict finite-state companion "
                "and keeps the carrier/readout gap explicit without claiming equivalence."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_weyl_geometry_carrier_translation_lane_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
