#!/usr/bin/env python3
"""
Weyl geometry alignment overlay.
================================

Controller-facing overlay for the Weyl/Hopf geometry lane.

This surface compares:
  - base legos
  - composed numeric rows
  - graph/proof bridge rows
  - alternate-carrier rows

It is an overlay only. It does not make a runtime engine claim or a proof
claim. It just gives the controller one place to see which geometry rows are
available and how they line up.
"""

from __future__ import annotations

import json
import pathlib
classification = "canonical"


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Controller overlay for the Weyl/Hopf geometry lane. It compares base "
    "legos, composed numeric rows, graph/proof bridge rows, and alternate-"
    "carrier rows when available."
)

LEGO_IDS = [
    "nested_hopf_tori",
    "weyl_pauli_transport",
    "weyl_hopf_pauli_composed_stack",
    "weyl_geometry_graph_proof_alignment",
    "weyl_geometry_ladder_audit",
    "weyl_geometry_carrier_compare",
]

PRIMARY_LEGO_IDS = [
    "nested_hopf_tori",
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

TOOL_INTEGRATION_DEPTH = {name: None for name in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


SOURCE_FILES = {
    "nested_hopf_tori": RESULT_DIR / "lego_nested_hopf_tori_results.json",
    "weyl_pauli_transport": RESULT_DIR / "lego_weyl_pauli_transport_results.json",
    "weyl_hopf_pauli_composed_stack": RESULT_DIR / "weyl_hopf_pauli_composed_stack_results.json",
    "weyl_geometry_graph_proof_alignment": RESULT_DIR / "weyl_geometry_graph_proof_alignment_results.json",
    "weyl_geometry_ladder_audit": RESULT_DIR / "weyl_geometry_ladder_audit_results.json",
    "weyl_geometry_carrier_compare": RESULT_DIR / "lego_weyl_geometry_carrier_compare_results.json",
}


def load_json(path: pathlib.Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())


def available(data) -> bool:
    return data is not None


def row_base(name: str, category: str, role: str, source_key: str, key_metrics: dict, note: str, data) -> dict:
    return {
        "category": category,
        "role": role,
        "row_id": name,
        "source_file": str(SOURCE_FILES[source_key]),
        "classification": data.get("classification") if data else None,
        "available": available(data),
        "all_pass": bool(key_metrics.get("all_pass", False)),
        "key_metrics": key_metrics,
        "note": note,
    }


def nested_hopf_row(data):
    summary = data.get("summary", {})
    positive = data.get("positive", {})
    boundary = data.get("boundary", {})
    spinor = positive.get("spinor_construction", {})
    nested_transport = positive.get("nested_transport", {})
    combined = positive.get("combined_consistency", {})
    return row_base(
        name="nested_hopf_tori",
        category="base_lego",
        role="base_geometry_carrier",
        source_key="nested_hopf_tori",
        key_metrics={
            "total_tests": summary.get("total_tests"),
            "sample_count": summary.get("sample_count"),
            "torus_levels": summary.get("torus_levels"),
            "max_point_norm_error": summary.get("max_point_norm_error"),
            "max_left_hopf_alignment_error": summary.get("max_left_hopf_alignment_error"),
            "max_transport_error": summary.get("max_transport_error"),
            "max_stack_error": summary.get("max_stack_error"),
            "inner_radius_identity": boundary.get("inner_radius_identity", {}).get("pass"),
            "clifford_radius_identity": boundary.get("clifford_radius_identity", {}).get("pass"),
            "outer_radius_identity": boundary.get("outer_radius_identity", {}).get("pass"),
            "all_pass": summary.get("all_pass"),
            "spinor_pass": spinor.get("pass"),
            "transport_pass": nested_transport.get("pass"),
            "combined_pass": combined.get("pass"),
        },
        note="Layered Hopf-torus base lego with Weyl spinors, Pauli/Bloch checks, and transport closure.",
        data=data,
    )


def weyl_pauli_row(data):
    summary = data.get("summary", {})
    positive = data.get("positive", {})
    sample = positive.get("sample_records", [{}])[0] if positive.get("sample_records") else {}
    return row_base(
        name="weyl_pauli_transport",
        category="base_lego",
        role="spinor_transport_base",
        source_key="weyl_pauli_transport",
        key_metrics={
            "sample_count": summary.get("sample_count"),
            "transport_count": summary.get("transport_count"),
            "max_left_right_overlap_abs": positive.get("max_left_right_overlap_abs"),
            "max_bloch_antipodal_gap": positive.get("max_bloch_antipodal_gap"),
            "pauli_readout_gap": positive.get("pauli_readout_gap"),
            "transport_roundtrip_error": positive.get("transport_roundtrip_error"),
            "transport_partial_midpoint_separation": positive.get("transport_partial_midpoint_separation"),
            "radii_monotone": positive.get("radii_monotone"),
            "all_pass": summary.get("all_pass"),
            "first_sample_chiral_z_gap": sample.get("chiral_z_gap"),
        },
        note="Reusable Weyl/Hopf/Pauli transport lego with left/right readouts and bounded transport checks.",
        data=data,
    )


def composed_stack_row(data):
    summary = data.get("summary", {})
    positive = data.get("positive", {})
    spinor = positive.get("spinor_construction", {})
    density = positive.get("density_bloch_pauli", {})
    transport = positive.get("nested_transport", {})
    combined = positive.get("combined_consistency", {})
    return row_base(
        name="weyl_hopf_pauli_composed_stack",
        category="composed_numeric",
        role="composed_geometry_anchor",
        source_key="weyl_hopf_pauli_composed_stack",
        key_metrics={
            "sample_count": summary.get("sample_count"),
            "torus_levels": summary.get("torus_levels"),
            "max_spinor_norm_error": summary.get("max_spinor_norm_error"),
            "max_bloch_alignment_error": summary.get("max_bloch_alignment_error"),
            "max_transport_error": summary.get("max_transport_error"),
            "max_stack_error": summary.get("max_stack_error"),
            "all_pass": summary.get("all_pass"),
            "spinor_pass": spinor.get("pass"),
            "density_pass": density.get("pass"),
            "transport_pass": transport.get("pass"),
            "combined_pass": combined.get("pass"),
        },
        note="Canonical composed stack: nested Hopf tori, left/right Weyl spinors, Pauli/Bloch checks, and transport consistency.",
        data=data,
    )


def graph_proof_row(data):
    graph_summary = data.get("graph_summary", {})
    positive = data.get("positive", {})
    negative = data.get("negative", {})
    boundary = data.get("boundary", {})
    return row_base(
        name="weyl_geometry_graph_proof_alignment",
        category="graph_proof",
        role="schedule_and_proof_bridge",
        source_key="weyl_geometry_graph_proof_alignment",
        key_metrics={
            "node_count": graph_summary.get("node_count"),
            "edge_count": graph_summary.get("edge_count"),
            "longest_path_length": graph_summary.get("longest_path_length"),
            "source_count": graph_summary.get("source_count"),
            "sink_count": graph_summary.get("sink_count"),
            "forward_order_sat": positive.get("z3_forces_the_geometry_stack_ordering", {}).get("forward_order_sat"),
            "reverse_order_unsat": positive.get("z3_forces_the_geometry_stack_ordering", {}).get("reverse_order_unsat"),
            "chirality_unsat": positive.get("z3_separates_left_and_right_chirality_signs", {}).get("pass"),
            "pauli_products_ok": positive.get("pauli_products_match_the_qubit_algebra", {}).get("pass"),
            "max_left_right_overlap_abs": positive.get("left_and_right_spinors_stay_operationally_distinct_on_each_carrier", {}).get("max_left_right_overlap_abs"),
            "max_bloch_antipodal_gap": positive.get("left_and_right_spinors_stay_operationally_distinct_on_each_carrier", {}).get("max_bloch_antipodal_gap"),
            "max_hopf_image_norm_gap": positive.get("hopf_and_torus_carriers_stay_unit_and_finite", {}).get("max_hopf_image_norm_gap"),
            "transport_fraction_inner_to_outer": data.get("geometry_samples", {}).get("transport_fractions", {}).get("inner_to_outer"),
            "all_pass": graph_summary.get("is_dag") and positive.get("pauli_products_match_the_qubit_algebra", {}).get("pass") and positive.get("z3_forces_the_geometry_stack_ordering", {}).get("forward_order_sat"),
            "negative_reverse_order_unsat": negative.get("reverse_geometry_order_is_unsat", {}).get("pass"),
            "negative_same_sign_unsat": negative.get("same_sign_chirality_claim_is_unsat", {}).get("pass"),
            "boundary_pass": all(v.get("pass") for v in boundary.values()) if boundary else None,
        },
        note="Graph/proof bridge over the Weyl/Hopf/Pauli schedule, with rustworkx ordering and z3 legality checks.",
        data=data,
    )


def ladder_audit_row(data):
    summary = data.get("summary", {})
    rungs = data.get("rungs", {})
    verdict = data.get("verdict", {})
    ambient = rungs.get("nested_hopf_tori_to_geometry", [])
    engine = rungs.get("weyl_ambient_to_engine_dof", [])
    return row_base(
        name="weyl_geometry_ladder_audit",
        category="bridge_audit",
        role="ambient_witness_audit",
        source_key="weyl_geometry_ladder_audit",
        key_metrics={
            "ambient_nontrivial_count": summary.get("ambient_nontrivial_count"),
            "clifford_neutral": summary.get("clifford_neutral"),
            "engine_nontrivial": summary.get("engine_nontrivial"),
            "engine_type2_nontrivial": summary.get("engine_type2_nontrivial"),
            "overlay_nontrivial": summary.get("overlay_nontrivial"),
            "witness_separable": summary.get("witness_separable"),
            "type2_witness_separable": summary.get("type2_witness_separable"),
            "guardrail_pass": summary.get("guardrail_pass"),
            "verdict": verdict.get("result"),
            "all_pass": verdict.get("result") == "PASS",
            "ambient_torus_count": len(ambient),
            "engine_torus_count": len(engine),
        },
        note="Independent witness audit for the Weyl-ambient rung before folding it into engine dynamics or bridge language.",
        data=data,
    )


def carrier_compare_row(data):
    summary = data.get("summary", {})
    checks = summary.get("checks", {})
    comp = checks.get("comparison_spread", {})
    return row_base(
        name="weyl_geometry_carrier_compare",
        category="alternate_carrier",
        role="carrier_comparison",
        source_key="weyl_geometry_carrier_compare",
        key_metrics={
            "carrier_count": summary.get("carrier_count"),
            "carrier_order": summary.get("carrier_order"),
            "result_count": summary.get("result_count"),
            "comparison_rows": summary.get("comparison_rows"),
            "mean_left_entropy_spread": comp.get("mean_left_entropy_spread"),
            "mean_step_bloch_jump_spread": comp.get("mean_step_bloch_jump_spread"),
            "all_pass": summary.get("all_pass"),
            "carrier_checks_passed": all(item.get("passed") for item in checks.values()) if checks else None,
        },
        note="Alternate-carrier comparison across Hopf torus, sphere section, graph carrier, and hypergraph carrier.",
        data=data,
    )


def main() -> None:
    overlay_source = {
        key: load_json(path) for key, path in SOURCE_FILES.items()
    }

    rows = [
        nested_hopf_row(overlay_source["nested_hopf_tori"]),
        weyl_pauli_row(overlay_source["weyl_pauli_transport"]),
        composed_stack_row(overlay_source["weyl_hopf_pauli_composed_stack"]),
        graph_proof_row(overlay_source["weyl_geometry_graph_proof_alignment"]),
        ladder_audit_row(overlay_source["weyl_geometry_ladder_audit"]),
        carrier_compare_row(overlay_source["weyl_geometry_carrier_compare"]),
    ]

    available_rows = [row for row in rows if row["available"]]
    all_pass = all(row["all_pass"] for row in available_rows)
    category_counts = {}
    for row in available_rows:
        category_counts[row["category"]] = category_counts.get(row["category"], 0) + 1

    summary = {
        "all_pass": all_pass,
        "row_count": len(rows),
        "available_row_count": len(available_rows),
        "category_counts": category_counts,
        "has_base_legos": category_counts.get("base_lego", 0) >= 2,
        "has_composed_numeric_row": category_counts.get("composed_numeric", 0) >= 1,
        "has_graph_proof_row": category_counts.get("graph_proof", 0) >= 1,
        "has_bridge_audit_row": category_counts.get("bridge_audit", 0) >= 1,
        "has_alternate_carrier_row": category_counts.get("alternate_carrier", 0) >= 1,
        "source_files": {key: str(path) for key, path in SOURCE_FILES.items()},
        "scope_note": (
            "Controller-facing overlay for the Weyl/Hopf geometry lane. It should be "
            "used to compare rows and route follow-on work, not to claim a proof or a runtime engine."
        ),
    }

    out = {
        "name": "weyl_geometry_alignment_overlay",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": summary,
        "rows": rows,
    }

    out_path = RESULT_DIR / "weyl_geometry_alignment_overlay_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
