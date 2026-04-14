#!/usr/bin/env python3
"""
Weyl geometry alignment overlay v2.
===================================

Controller-facing overlay for the Weyl/Hopf geometry lane.

This version includes:
  - reusable base legos
  - composed numeric row
  - strict finite-state companion
  - promoted translation lanes
  - repair-comparison surface
  - proof-pressure row
  - family-expansion row
  - routing/controller surfaces

It is an overlay only. It does not make a runtime engine claim or a proof
claim. It just gives the controller one place to see which geometry rows are
available and how they line up.
"""

from __future__ import annotations

import json
import pathlib
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Controller overlay for the Weyl/Hopf geometry lane. It compares base "
    "legos, composed numeric rows, strict companion rows, translation lanes, "
    "repair comparison surfaces, proof-pressure rows, and routing/controller "
    "surfaces when available."
)

LEGO_IDS = [
    "nested_hopf_tori",
    "weyl_pauli_transport",
    "weyl_hopf_spinor_bridge",
    "weyl_hopf_pauli_composed_stack",
    "qit_weyl_geometry_companion",
    "qit_weyl_hypergraph_companion",
    "qit_weyl_geometry_translation_lane",
    "qit_weyl_geometry_carrier_translation_lane",
    "qit_weyl_geometry_repair_comparison_surface",
    "weyl_geometry_proof_pressure",
    "weyl_geometry_family_expansion",
    "weyl_geometry_multifamily_expansion",
    "weyl_geometry_translation_targets",
    "weyl_geometry_graph_proof_alignment",
    "qit_weyl_carnot_bridge",
    "qit_weyl_szilard_geometry_bridge",
    "weyl_hypergraph_geometry_bridge",
    "weyl_hypergraph_follow_on",
    "qit_weyl_hypergraph_translation_lane",
    "weyl_geometry_ladder_audit",
]

PRIMARY_LEGO_IDS = [
    "nested_hopf_tori",
    "weyl_hopf_pauli_composed_stack",
    "qit_weyl_geometry_companion",
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
    "weyl_hopf_spinor_bridge": RESULT_DIR / "lego_weyl_hopf_spinor_bridge_results.json",
    "weyl_hopf_pauli_composed_stack": RESULT_DIR / "weyl_hopf_pauli_composed_stack_results.json",
    "qit_weyl_geometry_companion": RESULT_DIR / "qit_weyl_geometry_companion_results.json",
    "qit_weyl_hypergraph_companion": RESULT_DIR / "qit_weyl_hypergraph_companion_results.json",
    "qit_weyl_geometry_translation_lane": RESULT_DIR / "qit_weyl_geometry_translation_lane_results.json",
    "qit_weyl_geometry_carrier_translation_lane": RESULT_DIR / "qit_weyl_geometry_carrier_translation_lane_results.json",
    "qit_weyl_geometry_repair_comparison_surface": RESULT_DIR / "qit_weyl_geometry_repair_comparison_surface_results.json",
    "weyl_geometry_proof_pressure": RESULT_DIR / "weyl_geometry_proof_pressure_results.json",
    "weyl_geometry_family_expansion": RESULT_DIR / "weyl_geometry_family_expansion_results.json",
    "weyl_geometry_multifamily_expansion": RESULT_DIR / "weyl_geometry_multifamily_expansion_results.json",
    "weyl_geometry_translation_targets": RESULT_DIR / "weyl_geometry_translation_targets_results.json",
    "weyl_geometry_graph_proof_alignment": RESULT_DIR / "weyl_geometry_graph_proof_alignment_results.json",
    "qit_weyl_carnot_bridge": RESULT_DIR / "qit_weyl_carnot_bridge_results.json",
    "qit_weyl_szilard_geometry_bridge": RESULT_DIR / "qit_weyl_szilard_geometry_bridge_results.json",
    "weyl_hypergraph_geometry_bridge": RESULT_DIR / "weyl_hypergraph_geometry_bridge_results.json",
    "weyl_hypergraph_follow_on": RESULT_DIR / "weyl_hypergraph_follow_on_results.json",
    "qit_weyl_hypergraph_translation_lane": RESULT_DIR / "qit_weyl_hypergraph_translation_lane_results.json",
    "lego_weyl_geometry_protocol_dag": RESULT_DIR / "lego_weyl_geometry_protocol_dag_results.json",
    "weyl_geometry_carrier_array": RESULT_DIR / "weyl_geometry_carrier_array_results.json",
    "lego_weyl_geometry_carrier_compare": RESULT_DIR / "lego_weyl_geometry_carrier_compare_results.json",
    "weyl_geometry_ladder_audit": RESULT_DIR / "weyl_geometry_ladder_audit_results.json",
}


def load_json(path: pathlib.Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())


def available(data) -> bool:
    return data is not None


def row_base(
    name: str,
    category: str,
    role: str,
    source_key: str,
    key_metrics: dict,
    note: str,
    data,
) -> dict:
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
            "sample_count": summary.get("sample_count"),
            "total_tests": summary.get("total_tests"),
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


def spinor_bridge_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="weyl_hopf_spinor_bridge",
        category="base_lego",
        role="spinor_bridge_base",
        source_key="weyl_hopf_spinor_bridge",
        key_metrics={
            "sample_count": summary.get("sample_count"),
            "graph_node_count": summary.get("graph_node_count"),
            "graph_edge_count": summary.get("graph_edge_count"),
            "graph_is_dag": summary.get("graph_is_dag"),
            "proof_correct_order_sat": summary.get("proof_correct_order_sat"),
            "proof_reverse_order_unsat": summary.get("proof_reverse_order_unsat"),
            "proof_back_edge_unsat": summary.get("proof_back_edge_unsat"),
            "max_left_right_overlap_abs": summary.get("max_left_right_overlap_abs"),
            "max_hopf_roundtrip_gap": summary.get("max_hopf_roundtrip_gap"),
            "max_transport_roundtrip_gap": summary.get("max_transport_roundtrip_gap"),
            "max_pauli_readout_gap": summary.get("max_pauli_readout_gap"),
            "alternate_carrier_gap": summary.get("alternate_carrier_gap"),
            "all_pass": summary.get("all_pass"),
        },
        note="Reusable Weyl/Hopf/Pauli bridge lego with nested-torus transport, alternate-carrier comparison, and finite graph/proof ordering.",
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


def strict_companion_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="qit_weyl_geometry_companion",
        category="strict_companion",
        role="finite_state_strict_anchor",
        source_key="qit_weyl_geometry_companion",
        key_metrics={
            "sample_count": summary.get("sample_count"),
            "carrier_count": summary.get("carrier_count"),
            "row_count": summary.get("row_count"),
            "max_stack_error": summary.get("max_stack_error"),
            "max_transport_error": summary.get("max_transport_error"),
            "max_transport_roundtrip_error": summary.get("max_transport_roundtrip_error"),
            "max_basis_change_covariance_error": summary.get("max_basis_change_covariance_error"),
            "stack_gap_to_open_reference": summary.get("stack_gap_to_open_reference"),
            "stereographic_nonfinite_count": summary.get("stereographic_nonfinite_count"),
            "all_pass": summary.get("all_pass"),
        },
        note="Strict finite-state companion/readout surface for the Weyl/Hopf/Pauli geometry stack.",
        data=data,
    )


def strict_hypergraph_companion_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="qit_weyl_hypergraph_companion",
        category="strict_companion",
        role="finite_hypergraph_strict_anchor",
        source_key="qit_weyl_hypergraph_companion",
        key_metrics={
            "support_pack_count": summary.get("support_pack_count"),
            "strict_node_count": summary.get("strict_node_count"),
            "strict_hyperedge_count": summary.get("strict_hyperedge_count"),
            "strict_shadow_edge_count": summary.get("strict_shadow_edge_count"),
            "strict_dual_node_count": summary.get("strict_dual_node_count"),
            "strict_dual_edge_count": summary.get("strict_dual_edge_count"),
            "cell_complex_shape": summary.get("cell_complex_shape"),
            "graph_path_length": summary.get("graph_path_length"),
            "reverse_order_z3_unsat": summary.get("reverse_order_z3_unsat"),
            "reverse_order_cvc5_unsat": summary.get("reverse_order_cvc5_unsat"),
            "all_pass": summary.get("all_pass"),
        },
        note="Strict bounded companion/readout surface for the Weyl-hypergraph lane with xgi/toponetx carrier checks and z3/cvc5 ordering guards.",
        data=data,
    )


def translation_lane_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="qit_weyl_geometry_translation_lane",
        category="translation_lane",
        role="open_vs_strict_translation",
        source_key="qit_weyl_geometry_translation_lane",
        key_metrics={
            "open_sample_count": summary.get("open_sample_count"),
            "strict_sample_count": summary.get("strict_sample_count"),
            "stack_error_gap": summary.get("stack_error_gap"),
            "transport_error_gap": summary.get("transport_error_gap"),
            "basis_change_gap": summary.get("basis_change_gap"),
            "open_max_stack_error": summary.get("open_max_stack_error"),
            "strict_max_stack_error": summary.get("strict_max_stack_error"),
            "all_pass": summary.get("all_pass"),
            "open_row_id": summary.get("open_row_id"),
            "strict_row_id": summary.get("strict_row_id"),
        },
        note="Promoted open-vs-strict translation lane built from the open composed stack and the strict finite-state geometry companion.",
        data=data,
    )


def carrier_translation_lane_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="qit_weyl_geometry_carrier_translation_lane",
        category="translation_lane",
        role="open_vs_strict_carrier_translation",
        source_key="qit_weyl_geometry_carrier_translation_lane",
        key_metrics={
            "open_carrier_count": summary.get("open_carrier_count"),
            "strict_carrier_count": summary.get("strict_carrier_count"),
            "carrier_count_gap": summary.get("carrier_count_gap"),
            "open_direct_core_count": summary.get("open_direct_core_count"),
            "open_structural_count": summary.get("open_structural_count"),
            "direct_core_count_gap": summary.get("direct_core_count_gap"),
            "open_core_lr_overlap": summary.get("open_core_lr_overlap"),
            "strict_lr_overlap": summary.get("strict_lr_overlap"),
            "carrier_readout_gap_abs": summary.get("carrier_readout_gap_abs"),
            "strict_transport_roundtrip_error": summary.get("strict_transport_roundtrip_error"),
            "strict_basis_change_error": summary.get("strict_basis_change_error"),
            "strict_stack_error": summary.get("strict_stack_error"),
            "all_pass": summary.get("all_pass"),
            "open_best_direct_match": summary.get("open_best_direct_match"),
            "open_richer_alt_geometry": summary.get("open_richer_alt_geometry"),
        },
        note="Open-vs-strict carrier translation lane pairing the carrier array against the strict finite-state companion.",
        data=data,
    )


def hypergraph_translation_lane_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="qit_weyl_hypergraph_translation_lane",
        category="translation_lane",
        role="hypergraph_translation",
        source_key="qit_weyl_hypergraph_translation_lane",
        key_metrics={
            "best_family": summary.get("best_family"),
            "best_family_score": summary.get("best_family_score"),
            "support_pack_count": summary.get("support_pack_count"),
            "hypergraph_support_count": summary.get("hypergraph_support_count"),
            "pairwise_shadow_rankings_differ": summary.get("pairwise_shadow_rankings_differ"),
            "multiway_load_bearing": summary.get("multiway_load_bearing"),
            "support_pack_all_pass": summary.get("support_pack_all_pass"),
            "graph_path_length": summary.get("graph_path_length"),
            "all_pass": summary.get("all_pass"),
        },
        note="Bounded translation lane for the Weyl-hypergraph extension; enough to treat the family as companion-ready in the controller sense.",
        data=data,
    )


def repair_comparison_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="qit_weyl_geometry_repair_comparison_surface",
        category="repair_comparison",
        role="paired_survivor_surface",
        source_key="qit_weyl_geometry_repair_comparison_surface",
        key_metrics={
            "pair_count": summary.get("pair_count"),
            "companion_ready_pair_count": summary.get("companion_ready_pair_count"),
            "strict_anchor_row": summary.get("strict_anchor_row"),
            "top_survivor_row": summary.get("top_survivor_row"),
            "all_pass": summary.get("all_pass"),
        },
        note="Controller-facing repair comparison surface that records which open rows survive translation into the strict companion carrier.",
        data=data,
    )


def proof_pressure_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="weyl_geometry_proof_pressure",
        category="proof_pressure",
        role="solver_checked_schedule_pressure",
        source_key="weyl_geometry_proof_pressure",
        key_metrics={
            "row_count": summary.get("row_count"),
            "graph_path_length": summary.get("graph_path_length"),
            "base_row_count": summary.get("base_row_count"),
            "bridge_row_count": summary.get("bridge_row_count"),
            "comparison_row_count": summary.get("comparison_row_count"),
            "audit_row_count": summary.get("audit_row_count"),
            "sidecar_row_count": summary.get("sidecar_row_count"),
            "carrier_count": summary.get("carrier_count"),
            "compare_carrier_count": summary.get("compare_carrier_count"),
            "max_left_right_overlap_abs": summary.get("max_left_right_overlap_abs"),
            "max_chiral_z_gap": summary.get("max_chiral_z_gap"),
            "max_transport_roundtrip_error": summary.get("max_transport_roundtrip_error"),
            "max_stack_error": summary.get("max_stack_error"),
            "max_hopf_transport_error": summary.get("max_hopf_transport_error"),
            "all_pass": summary.get("all_pass"),
        },
        note="Solver-backed pressure surface over the existing geometry stack, blocking shortcut ordering and illegal carrier transitions.",
        data=data,
    )


def family_expansion_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="weyl_geometry_family_expansion",
        category="family_expansion",
        role="carrier_family_expansion",
        source_key="weyl_geometry_family_expansion",
        key_metrics={
            "family_count": summary.get("family_count"),
            "source_result_count": summary.get("source_result_count"),
            "carrier_core_count": summary.get("carrier_core_count"),
            "carrier_core_passed_carriers": summary.get("carrier_core_passed_carriers"),
            "carrier_core_failed_carriers": summary.get("carrier_core_failed_carriers"),
            "carrier_compare_carrier_count": summary.get("carrier_compare_carrier_count"),
            "carrier_compare_result_count": summary.get("carrier_compare_result_count"),
            "all_pass": summary.get("all_pass"),
        },
        note="Bounded expansion row that widens the live Weyl/Hopf carrier set into other repo geometry families already present.",
        data=data,
    )


def multifamily_expansion_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="weyl_geometry_multifamily_expansion",
        category="family_expansion",
        role="carrier_family_expansion",
        source_key="weyl_geometry_multifamily_expansion",
        key_metrics={
            "best_family": summary.get("best_family"),
            "runner_up_family": summary.get("runner_up_family"),
            "third_family": summary.get("third_family"),
            "family_count": summary.get("family_count"),
            "weyl_anchor_support_count": summary.get("weyl_anchor_support_count"),
            "hypergraph_support_count": summary.get("hypergraph_support_count"),
            "graph_support_count": summary.get("graph_support_count"),
            "contact_support_count": summary.get("contact_support_count"),
            "all_pass": summary.get("all_pass"),
        },
        note="Family-routing surface that ranks hypergraph, contact/symplectic, and graph follow-on geometry families beside the Weyl/Hopf anchor.",
        data=data,
    )


def hypergraph_follow_on_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="weyl_hypergraph_follow_on",
        category="family_expansion",
        role="hypergraph_follow_on",
        source_key="weyl_hypergraph_follow_on",
        key_metrics={
            "best_family": summary.get("best_family"),
            "best_family_score": summary.get("best_family_score"),
            "hypergraph_support_count": summary.get("hypergraph_support_count"),
            "hypergraph_edge_count": summary.get("hypergraph_edge_count"),
            "hypergraph_edge_sizes": summary.get("hypergraph_edge_sizes"),
            "hypergraph_multiway_load_bearing": summary.get("hypergraph_multiway_load_bearing"),
            "torus_beta1": summary.get("torus_beta1"),
            "all_pass": summary.get("all_pass"),
        },
        note="Dedicated hypergraph follow-on row for the Weyl/Hopf lane; this is the live next-family extension path.",
        data=data,
    )


def translation_targets_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="weyl_geometry_translation_targets",
        category="routing_controller",
        role="promotion_queue",
        source_key="weyl_geometry_translation_targets",
        key_metrics={
            "row_count": summary.get("row_count"),
            "foundation_count": summary.get("foundation_count"),
            "companion_ready_count": summary.get("companion_ready_count"),
            "graph_proof_bridge_count": summary.get("graph_proof_bridge_count"),
            "sidecar_count": summary.get("sidecar_count"),
            "top_foundation_row": summary.get("top_foundation_row"),
            "top_companion_row": summary.get("top_companion_row"),
            "top_bridge_row": summary.get("top_bridge_row"),
            "top_sidecar_row": summary.get("top_sidecar_row"),
            "registry_gap_concept_count": summary.get("registry_gap_concept_count"),
            "registry_new_concept_count": summary.get("registry_new_concept_count"),
            "all_pass": summary.get("all_pass"),
        },
        note="Ranked translation-target queue for the Weyl/Hopf lane; foundation, companion-ready, bridge-only, and sidecar rows are separated explicitly.",
        data=data,
    )


def graph_proof_row(data):
    graph_summary = data.get("graph_summary", {})
    summary = data.get("summary", {})
    positive = data.get("positive", {})
    negative = data.get("negative", {})
    boundary = data.get("boundary", {})
    return row_base(
        name="weyl_geometry_graph_proof_alignment",
        category="graph_proof_bridge",
        role="schedule_and_proof_bridge",
        source_key="weyl_geometry_graph_proof_alignment",
        key_metrics={
            "node_count": graph_summary.get("node_count"),
            "edge_count": graph_summary.get("edge_count"),
            "graph_path_length": summary.get("graph_path_length"),
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
            "all_pass": bool(graph_summary.get("is_dag") and positive.get("pauli_products_match_the_qubit_algebra", {}).get("pass") and positive.get("z3_forces_the_geometry_stack_ordering", {}).get("forward_order_sat")),
            "negative_reverse_order_unsat": negative.get("reverse_geometry_order_is_unsat", {}).get("pass"),
            "negative_same_sign_unsat": negative.get("same_sign_chirality_claim_is_unsat", {}).get("pass"),
            "boundary_pass": all(v.get("pass") for v in boundary.values()) if boundary else None,
        },
        note="Graph/proof bridge over the Weyl/Hopf/Pauli schedule, with rustworkx ordering and z3 legality checks.",
        data=data,
    )


def carnot_bridge_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="qit_weyl_carnot_bridge",
        category="graph_proof_bridge",
        role="engine_bridge",
        source_key="qit_weyl_carnot_bridge",
        key_metrics={
            "geometry_stage_count": summary.get("geometry_stage_count"),
            "engine_graph_path_length": summary.get("engine_graph_path_length"),
            "geometry_engine_stage_gap": summary.get("geometry_engine_stage_gap"),
            "bridge_node_count": summary.get("bridge_node_count"),
            "bridge_edge_count": summary.get("bridge_edge_count"),
            "bridge_path_length": summary.get("bridge_path_length"),
            "bridge_order_unsat": summary.get("bridge_order_unsat"),
            "stage_count_unsat": summary.get("stage_count_unsat"),
            "engine_forward_efficiency": summary.get("engine_forward_efficiency"),
            "engine_forward_carnot_bound": summary.get("engine_forward_carnot_bound"),
            "engine_reverse_cop": summary.get("engine_reverse_cop"),
            "engine_reverse_cop_carnot": summary.get("engine_reverse_cop_carnot"),
            "all_pass": summary.get("all_pass"),
        },
        note="Bounded geometry-to-Carnot bridge that keeps the geometry carrier and Carnot family distinct while checking ordering and stage-count compatibility.",
        data=data,
    )


def szilard_bridge_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="qit_weyl_szilard_geometry_bridge",
        category="graph_proof_bridge",
        role="engine_bridge",
        source_key="qit_weyl_szilard_geometry_bridge",
        key_metrics={
            "graph_path_length": summary.get("graph_path_length"),
            "geometry_left_right_guess_probability": summary.get("geometry_left_right_guess_probability"),
            "geometry_left_right_overlap_abs": summary.get("geometry_left_right_overlap_abs"),
            "szilard_measurement_guess_probability": summary.get("szilard_measurement_guess_probability"),
            "szilard_erased_guess_probability": summary.get("szilard_erased_guess_probability"),
            "wrong_order_vs_feedback_guess_probability": summary.get("wrong_order_vs_feedback_guess_probability"),
            "geometry_to_protocol_order_unsat": summary.get("geometry_to_protocol_order_unsat"),
            "weyl_transport_roundtrip_error": summary.get("weyl_transport_roundtrip_error"),
            "weyl_translation_stack_gap": summary.get("weyl_translation_stack_gap"),
            "all_pass": summary.get("all_pass"),
        },
        note="Bounded geometry-to-Szilard bridge that ties Weyl/Hopf readout structure to the measurement/feedback/reset protocol chain.",
        data=data,
    )


def hypergraph_bridge_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="weyl_hypergraph_geometry_bridge",
        category="graph_proof_bridge",
        role="hypergraph_bridge",
        source_key="weyl_hypergraph_geometry_bridge",
        key_metrics={
            "best_family": summary.get("best_family"),
            "hyperedge_count": summary.get("hyperedge_count"),
            "max_hyperedge_size": summary.get("max_hyperedge_size"),
            "pairwise_shadow_edge_count": summary.get("pairwise_shadow_edge_count"),
            "graph_path_length": summary.get("graph_path_length"),
            "bridge_order_unsat": summary.get("bridge_order_unsat"),
            "cell_complex_shape": summary.get("cell_complex_shape"),
            "all_pass": summary.get("all_pass"),
        },
        note="Bounded geometry-to-hypergraph bridge that keeps the multiway family explicit and distinct from pairwise collapse.",
        data=data,
    )


def protocol_dag_row(data):
    summary = data.get("summary", {})
    positive = data.get("positive", {})
    negative = data.get("negative", {})
    boundary = data.get("boundary", {})
    return row_base(
        name="weyl_geometry_protocol_dag",
        category="graph_proof_bridge",
        role="protocol_schedule_bridge",
        source_key="lego_weyl_geometry_protocol_dag",
        key_metrics={
            "node_count": summary.get("node_count"),
            "edge_count": summary.get("edge_count"),
            "graph_path_length": summary.get("graph_path_length"),
            "source_count": summary.get("source_count"),
            "sink_count": summary.get("sink_count"),
            "forward_order_sat": positive.get("forward_order_sat"),
            "reverse_order_unsat": positive.get("reverse_order_unsat"),
            "ordering_unsat": positive.get("ordering_unsat"),
            "chirality_unsat": positive.get("chirality_unsat"),
            "pauli_products_ok": positive.get("pauli_products_ok"),
            "transport_fraction_inner_to_outer": data.get("geometry_samples", {}).get("transport_fractions", {}).get("inner_to_outer"),
            "all_pass": summary.get("all_pass"),
            "negative_back_edge_unsat": negative.get("back_edge_to_base_unsat"),
            "boundary_pass": all(v.get("pass") for v in boundary.values()) if boundary else None,
        },
        note="Reusable graph/proof protocol DAG for the Weyl/Hopf geometry stack.",
        data=data,
    )


def carrier_array_row(data):
    summary = data.get("summary", {})
    return row_base(
        name="weyl_geometry_carrier_array",
        category="alternate_carrier",
        role="carrier_family_array",
        source_key="weyl_geometry_carrier_array",
        key_metrics={
            "total_tests": summary.get("total_tests"),
            "passed": summary.get("passed"),
            "failed": summary.get("failed"),
            "carrier_count": summary.get("carrier_count"),
            "passed_carriers": summary.get("passed_carriers"),
            "failed_carriers": summary.get("failed_carriers"),
            "max_nested_lr_overlap": summary.get("max_nested_lr_overlap"),
            "max_nested_bloch_gap": summary.get("max_nested_bloch_gap"),
            "max_graph_cycle_rank": summary.get("max_graph_cycle_rank"),
            "max_hypergraph_shadow_components": summary.get("max_hypergraph_shadow_components"),
            "max_cp3_concurrence": summary.get("max_cp3_concurrence"),
            "all_pass": summary.get("all_pass"),
        },
        note="Carrier array that runs the same spinor/Pauli core across multiple geometry carriers already in the repo.",
        data=data,
    )


def carrier_compare_row(data):
    summary = data.get("summary", {})
    checks = summary.get("checks", {})
    spread = checks.get("comparison_spread", {})
    return row_base(
        name="weyl_geometry_carrier_compare",
        category="alternate_carrier",
        role="carrier_family_comparison",
        source_key="lego_weyl_geometry_carrier_compare",
        key_metrics={
            "carrier_count": summary.get("carrier_count"),
            "sample_count": summary.get("sample_count"),
            "comparison_rows": summary.get("comparison_rows"),
            "mean_left_entropy_spread": spread.get("mean_left_entropy_spread"),
            "mean_step_bloch_jump_spread": spread.get("mean_step_bloch_jump_spread"),
            "all_pass": summary.get("all_pass"),
        },
        note="Reusable comparison lego that keeps the Weyl-style readout core fixed while varying the carrier plumbing.",
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
        category="sidecar",
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


def main() -> None:
    sources = {key: load_json(path) for key, path in SOURCE_FILES.items()}

    rows = [
        nested_hopf_row(sources["nested_hopf_tori"]),
        weyl_pauli_row(sources["weyl_pauli_transport"]),
        spinor_bridge_row(sources["weyl_hopf_spinor_bridge"]),
        composed_stack_row(sources["weyl_hopf_pauli_composed_stack"]),
        strict_companion_row(sources["qit_weyl_geometry_companion"]),
        strict_hypergraph_companion_row(sources["qit_weyl_hypergraph_companion"]),
        translation_lane_row(sources["qit_weyl_geometry_translation_lane"]),
        carrier_translation_lane_row(sources["qit_weyl_geometry_carrier_translation_lane"]),
        repair_comparison_row(sources["qit_weyl_geometry_repair_comparison_surface"]),
        proof_pressure_row(sources["weyl_geometry_proof_pressure"]),
        hypergraph_follow_on_row(sources["weyl_hypergraph_follow_on"]),
        multifamily_expansion_row(sources["weyl_geometry_multifamily_expansion"]),
        family_expansion_row(sources["weyl_geometry_family_expansion"]),
        translation_targets_row(sources["weyl_geometry_translation_targets"]),
        graph_proof_row(sources["weyl_geometry_graph_proof_alignment"]),
        carnot_bridge_row(sources["qit_weyl_carnot_bridge"]),
        szilard_bridge_row(sources["qit_weyl_szilard_geometry_bridge"]),
        hypergraph_bridge_row(sources["weyl_hypergraph_geometry_bridge"]),
        hypergraph_translation_lane_row(sources["qit_weyl_hypergraph_translation_lane"]),
        protocol_dag_row(sources["lego_weyl_geometry_protocol_dag"]),
        carrier_array_row(sources["weyl_geometry_carrier_array"]),
        carrier_compare_row(sources["lego_weyl_geometry_carrier_compare"]),
        ladder_audit_row(sources["weyl_geometry_ladder_audit"]),
    ]

    category_counts = {}
    for row in rows:
        category_counts[row["category"]] = category_counts.get(row["category"], 0) + 1

    top_rows = {}
    for row in rows:
        category = row["category"]
        if category not in top_rows:
            top_rows[category] = row["row_id"]

    summary = {
        "all_pass": all(row["all_pass"] for row in rows if row["available"]),
        "row_count": len(rows),
        "available_row_count": sum(1 for row in rows if row["available"]),
        "category_counts": category_counts,
        "has_base_legos": category_counts.get("base_lego", 0) == 3,
        "has_composed_numeric_row": category_counts.get("composed_numeric", 0) == 1,
        "has_strict_companion_row": category_counts.get("strict_companion", 0) == 2,
        "has_translation_lanes": category_counts.get("translation_lane", 0) == 3,
        "has_repair_comparison_row": category_counts.get("repair_comparison", 0) == 1,
        "has_proof_pressure_row": category_counts.get("proof_pressure", 0) == 1,
        "has_family_expansion_row": category_counts.get("family_expansion", 0) == 3,
        "has_routing_controller_row": category_counts.get("routing_controller", 0) == 1,
        "has_graph_proof_rows": category_counts.get("graph_proof_bridge", 0) == 5,
        "has_alternate_carrier_rows": category_counts.get("alternate_carrier", 0) == 2,
        "has_sidecar_row": category_counts.get("sidecar", 0) == 1,
        "top_foundation_row": top_rows.get("base_lego"),
        "top_composed_row": top_rows.get("composed_numeric"),
        "top_strict_row": top_rows.get("strict_companion"),
        "top_translation_row": top_rows.get("translation_lane"),
        "top_repair_row": top_rows.get("repair_comparison"),
        "top_proof_row": top_rows.get("proof_pressure"),
        "top_family_row": top_rows.get("family_expansion"),
        "top_routing_row": top_rows.get("routing_controller"),
        "top_bridge_row": top_rows.get("graph_proof_bridge"),
        "top_carrier_row": top_rows.get("alternate_carrier"),
        "top_sidecar_row": top_rows.get("sidecar"),
        "scope_note": (
            "Controller-facing overlay for the Weyl/Hopf geometry lane. It now includes "
            "base legos, the composed stack, strict companion, translation lanes, repair "
            "comparison, proof pressure, family expansion, routing targets, bridge rows, "
            "engine bridges, carrier comparison, and sidecar diagnostics."
        ),
    }

    out = {
        "name": "weyl_geometry_alignment_overlay_v2",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": summary,
        "rows": rows,
    }

    out_path = RESULT_DIR / "weyl_geometry_alignment_overlay_v2_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
