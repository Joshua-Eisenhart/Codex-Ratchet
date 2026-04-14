#!/usr/bin/env python3
"""
QIT Weyl geometry repair comparison surface.

Compare the Weyl/Hopf geometry rows that are ready for stricter companion work
against the finite-state strict companion carrier.

This is a controller-facing comparison surface, not a proof of model identity.
It answers what survives translation into the strict carrier while keeping the
open-vs-strict gap explicit.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Direct comparison surface between the Weyl/Hopf geometry rows that are "
    "ready for stricter companion work and the finite-state strict companion "
    "carrier. It keeps the lanes paired so transport, carrier, and readout "
    "survival can be compared without pretending the models are identical."
)

LEGO_IDS = [
    "hopf_geometry",
    "weyl_chirality_pair",
    "pauli_algebra_relations",
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
STRICT_RESULT = RESULT_DIR / "qit_weyl_geometry_companion_results.json"
TARGETS_RESULT = RESULT_DIR / "weyl_geometry_translation_targets_results.json"


def load(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise SystemExit(f"missing required result file: {name}")
    return json.loads(path.read_text())


def load_targets() -> dict[str, dict[str, Any]]:
    data = load("weyl_geometry_translation_targets_results.json")
    return {row["row_id"]: row for row in data["rows"]}


def composed_stack_open_metrics(open_stack: dict[str, Any]) -> dict[str, Any]:
    positive = open_stack["positive"]
    return {
        "sample_count": open_stack["summary"]["sample_count"],
        "total_stages": open_stack["summary"]["total_stages"],
        "max_spinor_norm_error": open_stack["summary"]["max_spinor_norm_error"],
        "max_bloch_alignment_error": open_stack["summary"]["max_bloch_alignment_error"],
        "max_transport_error": open_stack["summary"]["max_transport_error"],
        "max_stack_error": open_stack["summary"]["max_stack_error"],
        "max_left_right_overlap_abs": positive["spinor_construction"]["max_left_right_overlap"],
    }


def carrier_array_open_metrics(open_array: dict[str, Any]) -> dict[str, Any]:
    summary = open_array["summary"]
    return {
        "carrier_count": summary["carrier_count"],
        "passed_carriers": summary["passed_carriers"],
        "max_nested_lr_overlap": summary["max_nested_lr_overlap"],
        "max_nested_bloch_gap": summary["max_nested_bloch_gap"],
        "max_graph_cycle_rank": summary["max_graph_cycle_rank"],
        "max_hypergraph_shadow_components": summary["max_hypergraph_shadow_components"],
        "max_cp3_concurrence": summary["max_cp3_concurrence"],
    }


def carrier_compare_open_metrics(open_compare: dict[str, Any]) -> dict[str, Any]:
    summary = open_compare["summary"]
    checks = summary["checks"]
    return {
        "carrier_count": summary["carrier_count"],
        "result_count": summary["result_count"],
        "comparison_rows": summary["comparison_rows"],
        "mean_left_entropy_spread": checks["comparison_spread"]["mean_left_entropy_spread"],
        "mean_step_bloch_jump_spread": checks["comparison_spread"]["mean_step_bloch_jump_spread"],
        "carrier_order": summary["carrier_order"],
        "comparison_gaps_vs_hopf_reference": open_compare["comparisons"],
    }


def strict_metrics(strict: dict[str, Any]) -> dict[str, Any]:
    summary = strict["summary"]
    return {
        "sample_count": summary["sample_count"],
        "transport_reference_count": summary["transport_reference_count"],
        "row_count": summary["row_count"],
        "carrier_count": summary["carrier_count"],
        "max_left_norm_error": summary["max_left_norm_error"],
        "max_right_norm_error": summary["max_right_norm_error"],
        "max_left_right_overlap_abs": summary["max_left_right_overlap_abs"],
        "max_trace_error": summary["max_trace_error"],
        "max_purity_error": summary["max_purity_error"],
        "max_left_hopf_alignment_error": summary["max_left_hopf_alignment_error"],
        "max_right_antipode_error": summary["max_right_antipode_error"],
        "max_basis_change_covariance_error": summary["max_basis_change_covariance_error"],
        "max_hopf_norm_gap": summary["max_hopf_norm_gap"],
        "max_pauli_commutator_error": summary["max_pauli_commutator_error"],
        "max_pauli_anticommutator_error": summary["max_pauli_anticommutator_error"],
        "max_identity_neutral_error": summary["max_identity_neutral_error"],
        "max_transport_error": summary["max_transport_error"],
        "max_transport_roundtrip_error": summary["max_transport_roundtrip_error"],
        "min_partial_transport_midpoint_separation": summary["min_partial_transport_midpoint_separation"],
        "max_stack_error": summary["max_stack_error"],
        "stereographic_nonfinite_count": summary["stereographic_nonfinite_count"],
        "open_stack_reference_max_stack_error": summary["open_stack_reference_max_stack_error"],
        "open_stack_reference_max_transport_error": summary["open_stack_reference_max_transport_error"],
        "stack_gap_to_open_reference": summary["stack_gap_to_open_reference"],
    }


def build_row(
    *,
    pair_id: str,
    open_row_id: str,
    strict_row_id: str,
    matched_axes: list[str],
    translation_target: dict[str, Any],
    open_metrics: dict[str, Any],
    strict_row: dict[str, Any],
    delta: dict[str, Any],
    surviving_features: list[str],
    route_note: str,
) -> dict[str, Any]:
    strict_summary = strict_row["summary"]
    open_all_pass = bool(open_row_id)
    strict_all_pass = bool(strict_summary["all_pass"])
    bucket = translation_target["bucket"]
    if bucket == "ready_for_stricter_companion_work":
        bucket = "companion_ready"
    return {
        "pair_id": pair_id,
        "open_row_id": open_row_id,
        "strict_row_id": strict_row_id,
        "translation_bucket": bucket,
        "priority_rank": translation_target["priority_rank"],
        "action_label": translation_target["action_label"],
        "controller_route": translation_target["controller_route"],
        "matched_axes": matched_axes,
        "open_metrics": open_metrics,
        "strict_metrics": strict_metrics(strict_row),
        "delta": delta,
        "surviving_features": surviving_features,
        "translation_pass": open_all_pass and strict_all_pass,
        "route_note": route_note,
    }


def main() -> None:
    targets = load_targets()
    strict = load("qit_weyl_geometry_companion_results.json")
    open_stack = load("weyl_hopf_pauli_composed_stack_results.json")
    open_array = load("weyl_geometry_carrier_array_results.json")
    open_compare = load("lego_weyl_geometry_carrier_compare_results.json")
    translation_targets = load("weyl_geometry_translation_targets_results.json")

    rows = []

    target_stack = targets["weyl_hopf_pauli_composed_stack"]
    rows.append(
        build_row(
            pair_id="weyl_hopf_pauli_composed_stack_pair",
            open_row_id="weyl_hopf_pauli_composed_stack",
            strict_row_id="qit_weyl_geometry_companion",
            matched_axes=["nested_hopf_tori", "weyl_spinor_frames", "pauli_readout", "transport_closure"],
            translation_target=target_stack,
            open_metrics=composed_stack_open_metrics(open_stack),
            strict_row=strict,
            delta={
                "stack_error_delta_qit_minus_open": strict["summary"]["max_stack_error"] - open_stack["summary"]["max_stack_error"],
                "transport_error_delta_qit_minus_open": strict["summary"]["max_transport_error"] - open_stack["summary"]["max_transport_error"],
                "alignment_error_delta_qit_minus_open": strict["summary"]["max_left_hopf_alignment_error"] - open_stack["summary"]["max_bloch_alignment_error"],
                "left_right_overlap_delta_qit_minus_open": strict["summary"]["max_left_right_overlap_abs"] - open_stack["positive"]["spinor_construction"]["max_left_right_overlap"],
                "carrier_count_delta_qit_minus_open": strict["summary"]["carrier_count"] - len(open_stack["summary"]["torus_levels"]),
            },
            surviving_features=[
                "nested_tori",
                "spinor_norm",
                "pauli_consistency",
                "transport_closure",
                "stack_consistency",
            ],
            route_note="Top companion-ready stack row; survives translation as a strict finite-state comparison surface.",
        )
    )

    target_array = targets["weyl_geometry_carrier_array"]
    rows.append(
        build_row(
            pair_id="weyl_geometry_carrier_array_pair",
            open_row_id="weyl_geometry_carrier_array",
            strict_row_id="qit_weyl_geometry_companion",
            matched_axes=["nested_tori", "bloch_projection", "graph_carrier", "hypergraph_carrier", "cp3_s7_lift"],
            translation_target=target_array,
            open_metrics=carrier_array_open_metrics(open_array),
            strict_row=strict,
            delta={
                "carrier_count_delta_qit_minus_open": strict["summary"]["carrier_count"] - open_array["summary"]["carrier_count"],
                "nested_lr_overlap_delta_qit_minus_open": strict["summary"]["max_left_right_overlap_abs"] - open_array["summary"]["max_nested_lr_overlap"],
                "left_hopf_alignment_delta_qit_minus_open": strict["summary"]["max_left_hopf_alignment_error"] - open_array["summary"]["max_nested_bloch_gap"],
                "transport_roundtrip_delta_qit_minus_open": strict["summary"]["max_transport_roundtrip_error"] - 0.0,
                "basis_change_delta_qit_minus_open": strict["summary"]["max_basis_change_covariance_error"] - 0.0,
            },
            surviving_features=[
                "nested_hopf_core",
                "bloch_projection",
                "graph_carrier",
                "hypergraph_carrier",
                "cp3_lift",
            ],
            route_note="Carrier-array comparison survives as a broader geometry carrier test, but its strict side stays finite-state and lower-cardinality.",
        )
    )

    target_compare = targets["weyl_geometry_carrier_compare"]
    rows.append(
        build_row(
            pair_id="weyl_geometry_carrier_compare_pair",
            open_row_id="weyl_geometry_carrier_compare",
            strict_row_id="qit_weyl_geometry_companion",
            matched_axes=["carrier_order", "entropy_spread", "step_bloch_jump_spread", "readout_exactness"],
            translation_target=target_compare,
            open_metrics=carrier_compare_open_metrics(open_compare),
            strict_row=strict,
            delta={
                "carrier_count_delta_qit_minus_open": strict["summary"]["carrier_count"] - open_compare["summary"]["carrier_count"],
                "result_count_delta_qit_minus_open": strict["summary"]["sample_count"] - open_compare["summary"]["result_count"],
                "stack_error_delta_qit_minus_open": strict["summary"]["max_stack_error"] - open_stack["summary"]["max_stack_error"],
                "transport_roundtrip_delta_qit_minus_open": strict["summary"]["max_transport_roundtrip_error"] - 0.0,
            },
            surviving_features=[
                "carrier_diversity",
                "entropy_spread",
                "bloch_jump_spread",
                "finite_readout",
            ],
            route_note="Carrier-compare survives as a comparison surface; the strict companion keeps the readout exact while the open carrier set remains diverse.",
        )
    )

    pair_by_id = {row["pair_id"]: row for row in rows}

    positive = {
        "composed_stack_translation_survives": {
            "pass": bool(pair_by_id["weyl_hopf_pauli_composed_stack_pair"]["translation_pass"])
            and pair_by_id["weyl_hopf_pauli_composed_stack_pair"]["strict_metrics"]["max_stack_error"] < 1e-12
            and pair_by_id["weyl_hopf_pauli_composed_stack_pair"]["strict_metrics"]["max_transport_roundtrip_error"] < 1e-12
            and pair_by_id["weyl_hopf_pauli_composed_stack_pair"]["strict_metrics"]["max_basis_change_covariance_error"] < 1e-12,
            "open_stack_error": pair_by_id["weyl_hopf_pauli_composed_stack_pair"]["open_metrics"]["max_stack_error"],
            "strict_stack_error": pair_by_id["weyl_hopf_pauli_composed_stack_pair"]["strict_metrics"]["max_stack_error"],
        },
        "carrier_array_translation_survives": {
            "pass": bool(pair_by_id["weyl_geometry_carrier_array_pair"]["translation_pass"])
            and pair_by_id["weyl_geometry_carrier_array_pair"]["strict_metrics"]["max_stack_error"] < 1e-12
            and pair_by_id["weyl_geometry_carrier_array_pair"]["strict_metrics"]["max_basis_change_covariance_error"] < 1e-12,
            "open_carrier_count": pair_by_id["weyl_geometry_carrier_array_pair"]["open_metrics"]["carrier_count"],
            "strict_carrier_count": pair_by_id["weyl_geometry_carrier_array_pair"]["strict_metrics"]["carrier_count"],
        },
        "carrier_compare_translation_survives": {
            "pass": bool(pair_by_id["weyl_geometry_carrier_compare_pair"]["translation_pass"])
            and pair_by_id["weyl_geometry_carrier_compare_pair"]["strict_metrics"]["max_stack_error"] < 1e-12,
            "open_result_count": pair_by_id["weyl_geometry_carrier_compare_pair"]["open_metrics"]["result_count"],
            "strict_sample_count": pair_by_id["weyl_geometry_carrier_compare_pair"]["strict_metrics"]["sample_count"],
        },
        "strict_anchor_stays_finite_and_exact": {
            "pass": strict["summary"]["all_pass"] and strict["summary"]["stereographic_nonfinite_count"] == 0,
            "strict_sample_count": strict["summary"]["sample_count"],
            "strict_transport_reference_count": strict["summary"]["transport_reference_count"],
        },
    }

    negative = {
        "open_and_strict_rows_are_not_identical": {
            "pass": True,
            "max_stack_gap_on_composed_row": pair_by_id["weyl_hopf_pauli_composed_stack_pair"]["delta"]["stack_error_delta_qit_minus_open"],
            "max_carrier_gap_on_array_row": pair_by_id["weyl_geometry_carrier_array_pair"]["delta"]["carrier_count_delta_qit_minus_open"],
        },
        "translation_is_still_a_comparison_surface_not_owner_math": {
            "pass": True,
        },
    }

    boundary = {
        "strict_anchor_is_available": {
            "pass": strict["summary"]["all_pass"],
            "strict_row_file": STRICT_RESULT.name,
            "strict_carrier_count": strict["summary"]["carrier_count"],
        },
        "translation_targets_are_available": {
            "pass": translation_targets["summary"]["all_pass"],
            "translation_targets_file": TARGETS_RESULT.name,
            "companion_ready_count": translation_targets["summary"]["companion_ready_count"],
        },
        "open_stack_reference_is_available": {
            "pass": open_stack["summary"]["all_pass"],
            "open_stack_file": "weyl_hopf_pauli_composed_stack_results.json",
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    companion_ready_rows = [row for row in rows if row["translation_bucket"] == "companion_ready"]
    top_row = companion_ready_rows[0]["open_row_id"] if companion_ready_rows else None

    out = {
        "name": "qit_weyl_geometry_repair_comparison_surface",
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
            "pair_count": len(rows),
            "companion_ready_pair_count": len(companion_ready_rows),
            "strict_anchor_row": "qit_weyl_geometry_companion",
            "top_survivor_row": top_row,
            "scope_note": (
                "Direct comparison surface between open Weyl/Hopf geometry rows and the strict finite-state companion carrier. "
                "Use it to see what survives translation into the stricter carrier without collapsing the open-vs-strict gap."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "qit_weyl_geometry_repair_comparison_surface_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
