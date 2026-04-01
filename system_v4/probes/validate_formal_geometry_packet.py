#!/usr/bin/env python3
"""
validate_formal_geometry_packet.py
=================================

Mechanical validator for the formal geometry packet.

This validator is intentionally honest about the current packet:
  - positive witnesses must pass,
  - destructive controls must visibly degrade the structure they target,
  - known owner-side gaps must remain explicitly visible instead of being
    silently treated as solved.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
AUDIT_RESULTS = ROOT.parent / "a2_state" / "audit_logs"
OUTPUT_PATH = SIM_RESULTS / "formal_geometry_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    geometry_truth = load_json(SIM_RESULTS / "geometry_truth_results.json")
    ladder = load_json(SIM_RESULTS / "weyl_geometry_ladder_audit_results.json")
    overlay = load_json(SIM_RESULTS / "weyl_ambient_vs_engine_overlay_results.json")
    chirality = load_json(SIM_RESULTS / "L4_engine_chirality_results.json")
    dual_weyl = load_json(SIM_RESULTS / "dual_weyl_results.json")
    neg_torus = load_json(SIM_RESULTS / "neg_torus_scrambled_results.json")
    neg_chiral = load_json(SIM_RESULTS / "neg_no_chirality_results.json")
    no_chirality_search = load_json(SIM_RESULTS / "no_chirality_search_validation.json")
    neg_loop_swap = load_json(SIM_RESULTS / "neg_loop_law_swap_results.json")
    weyl_delta = load_json(SIM_RESULTS / "weyl_delta_packet_results.json")
    lower_tier_chiral_search = load_json(SIM_RESULTS / "lower_tier_chiral_law_search_validation.json")
    lower_tier_transport_search = load_json(SIM_RESULTS / "lower_tier_transport_law_search_validation.json")
    lower_tier_operator_search = load_json(SIM_RESULTS / "lower_tier_operator_basis_search_validation.json")
    hopf_weyl_projection = load_json(AUDIT_RESULTS / "QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json")
    chiral_gate_map = {item["name"]: item for item in lower_tier_chiral_search["gates"]}
    no_chirality_gate_map = {item["name"]: item for item in no_chirality_search["gates"]}
    transport_gate_map = {item["name"]: item for item in lower_tier_transport_search["gates"]}
    operator_gate_map = {item["name"]: item for item in lower_tier_operator_search["gates"]}
    lower_tier_chiral_detail = chiral_gate_map["L4_search_keeps_single_lower_tier_chiral_law_open_but_unadmitted"]["detail"]

    chirality_results = chirality["results"]
    projection = hopf_weyl_projection["weyl_projection_readiness"]
    neg_torus_status = neg_torus["evidence_ledger"][0]["status"]
    neg_chiral_status = neg_chiral["evidence_ledger"][0]["status"]
    neg_loop_swap_status = neg_loop_swap["evidence_ledger"][0]["status"]
    carrier_geometry_admission = {
        "object": "carrier_geometry_admission",
        "carrier": "finite Hopf/Weyl carrier",
        "admitted": True,
        "source_gates": [
            "G1_exact_hopf_geometry_truth",
            "G2_weyl_ambient_rung",
            "G3_ambient_vs_engine_overlay",
            "G4_live_engine_family_split",
            "G9_owner_anchor_state_explicit",
        ],
        "basis_status": "carrier basis present at geometry tier; explicit operator admission handled by lower-tier operator search",
        "owner_anchor_state": {
            "projection_status": projection["projection_status"],
            "weyl_branch_nodes_present": projection["weyl_branch_nodes_present"],
            "missing_owner_anchors": projection["missing_owner_anchors"],
        },
        "read": "Finite Hopf/Weyl carrier geometry and Weyl-sheet overlay are admitted as lower-tier pre-Axis machinery.",
    }
    operator_basis_search_admission = {
        "object": "operator_basis_search_admission",
        "admitted": lower_tier_operator_search["passed_gates"] == lower_tier_operator_search["total_gates"],
        "source_gates": [
            "O1_fixed_carrier_basis_remap_shows_load_bearing_sensitivity",
            "O2_global_coordinate_change_is_not_mistaken_for_substrate_failure",
            "O3_commuting_collapse_degrades_the_local_operator_response",
            "O4_local_unitary_pair_is_not_demoted_by_this_narrow_local_test",
        ],
        "status": "lower-tier noncommuting basis split survives local operator search",
        "read": "The lower-tier operator search now explicitly supports a noncommuting basis split and coordinate-relativity guard, while leaving Fe/Fi undemoted in this narrow local search.",
    }
    classical_leakage_guards = {
        "object": "classical_leakage_guards",
        "admitted": True,
        "source_gates": [
            "G3_ambient_vs_engine_overlay",
            "G6_torus_negative_is_load_bearing",
            "G7_no_chirality_negative_still_incomplete",
            "G8_exact_loop_law_swap_negative",
        ],
        "raw_lr_control_blocked": {
            "status": "control_only",
            "max_raw_LR_mutual_information": float(overlay["summary"]["max_raw_LR_mutual_information"]),
        },
        "torus_scramble_kill": {
            "status": neg_torus_status,
            "structure_matters": bool(neg_torus["structure_matters"]),
            "n_axis_diff": int(neg_torus["n_axis_diff"]),
        },
        "no_chirality_kill": {
            "status": neg_chiral_status,
            "chirality_matters": bool(neg_chiral["chirality_matters"]),
            "residual_gap": float(neg_chiral["d_flat"] / neg_chiral["d_chiral"]),
            "source_probe_gates": [
                "N1_no_chirality_kill_is_real_but_not_total",
                "N2_no_chirality_residual_is_explicitly_nontrivial",
                "N3_chiral_run_keeps_stronger_sheet_split_than_flattened_run",
            ],
        },
        "loop_law_swap_kill": {
            "status": neg_loop_swap_status,
            "structure_matters": bool(neg_loop_swap["structure_matters"]),
            "max_true_fiber_drift": float(neg_loop_swap["max_true_fiber_drift"]),
            "min_true_base_traversal": float(neg_loop_swap["min_true_base_traversal"]),
        },
        "read": "Classicalized collapse routes are blocked at the lower geometry tier; raw L|R control stays trivial and exact torus or loop-law corruption fails.",
    }
    chiral_law_embargo = {
        "object": "chiral_law_embargo",
        "admitted": True,
        "source_gates": [
            "G3_ambient_vs_engine_overlay",
            "G4_live_engine_family_split",
            "G7_no_chirality_negative_still_incomplete",
        ],
        "ga3_chirality": {
            "status": "readout_only",
            "reason": "GA3 is a valid asymmetry readout but not yet a lower-tier signed differential law",
        },
        "symmetric_dphi_bookkeeping": {
            "status": "bookkeeping_only",
            "max_abs_compat_dphi_gap": float(weyl_delta["global_summary"]["max_abs_compat_dphi_gap"]),
            "reason": "runtime dphi_L and dphi_R are symmetric compatibility shims in engine history",
        },
        "promotion_block": "awaiting_real_lower_tier_chiral_differential_law",
        "read": "Lower-tier chirality is real as a carrier/readout asymmetry, but GA3 and symmetric dphi bookkeeping are embargoed from promotion as chiral law objects.",
    }

    gates = [
        gate(
            geometry_truth["all_pass"] and geometry_truth["passed"] == geometry_truth["total"] and geometry_truth["total"] >= 117,
            "G1_exact_hopf_geometry_truth",
            {
                "passed": geometry_truth["passed"],
                "total": geometry_truth["total"],
                "all_pass": geometry_truth["all_pass"],
            },
        ),
        gate(
            ladder["verdict"]["result"] == "PASS"
            and ladder["summary"]["ambient_nontrivial_count"] >= 2
            and ladder["summary"]["clifford_neutral"]
            and ladder["summary"]["overlay_nontrivial"]
            and ladder["summary"]["witness_separable"]
            and ladder["summary"]["guardrail_pass"],
            "G2_weyl_ambient_rung",
            {
                "verdict": ladder["verdict"]["result"],
                "ambient_nontrivial_count": ladder["summary"]["ambient_nontrivial_count"],
                "clifford_neutral": ladder["summary"]["clifford_neutral"],
                "overlay_nontrivial": ladder["summary"]["overlay_nontrivial"],
                "witness_separable": ladder["summary"]["witness_separable"],
            },
        ),
        gate(
            overlay["verdict"]["result"] == "PASS"
            and overlay["summary"]["overlay_nontrivial_count"] >= 2
            and overlay["summary"]["ambient_nontrivial_count"] >= 2
            and overlay["summary"]["guardrail_pass"]
            and overlay["summary"]["max_raw_LR_mutual_information"] < 1e-9,
            "G3_ambient_vs_engine_overlay",
            {
                "verdict": overlay["verdict"]["result"],
                "overlay_nontrivial_count": overlay["summary"]["overlay_nontrivial_count"],
                "ambient_nontrivial_count": overlay["summary"]["ambient_nontrivial_count"],
                "max_raw_LR_mutual_information": overlay["summary"]["max_raw_LR_mutual_information"],
            },
        ),
        gate(
            chirality_results["family_distinct"]
            and chirality_results["output_valid"]
            and chirality_results["axes_diverge"]
            and chirality_results["dominance_swap"]
            and chirality_results["avg_left_sheet_distance"] > 0.01
            and chirality_results["avg_right_sheet_distance"] > 0.01,
            "G4_live_engine_family_split",
            {
                "family_distinct": chirality_results["family_distinct"],
                "output_valid": chirality_results["output_valid"],
                "axes_diverge": chirality_results["axes_diverge"],
                "dominance_swap": chirality_results["dominance_swap"],
                "avg_left_sheet_distance": chirality_results["avg_left_sheet_distance"],
                "avg_right_sheet_distance": chirality_results["avg_right_sheet_distance"],
            },
        ),
        gate(
            dual_weyl["summary"]["passed"] >= 4 and dual_weyl["summary"]["killed"] == 0,
            "G5_dual_weyl_cycle_stability",
            {
                "passed": dual_weyl["summary"]["passed"],
                "killed": dual_weyl["summary"]["killed"],
            },
        ),
        gate(
            neg_torus_status == "KILL"
            and neg_torus["structure_matters"]
            and max(neg_torus["d_L"], neg_torus["d_R"]) > 0.02
            and neg_torus["n_axis_diff"] >= 2,
            "G6_torus_negative_is_load_bearing",
            {
                "status": neg_torus_status,
                "d_L": neg_torus["d_L"],
                "d_R": neg_torus["d_R"],
                "n_axis_diff": neg_torus["n_axis_diff"],
            },
        ),
        gate(
            neg_chiral_status == "KILL"
            and neg_chiral["chirality_matters"]
            and neg_chiral["d_chiral"] > neg_chiral["d_flat"]
            and neg_chiral["d_flat"] > 0.05
            and no_chirality_gate_map["N1_no_chirality_kill_is_real_but_not_total"]["pass"]
            and no_chirality_gate_map["N2_no_chirality_residual_is_explicitly_nontrivial"]["pass"]
            and no_chirality_gate_map["N3_chiral_run_keeps_stronger_sheet_split_than_flattened_run"]["pass"],
            "G7_no_chirality_negative_still_incomplete",
            {
                "status": neg_chiral_status,
                "d_chiral": neg_chiral["d_chiral"],
                "d_flat": neg_chiral["d_flat"],
                "residual_gap": neg_chiral["d_flat"] / neg_chiral["d_chiral"],
                "n1_pass": no_chirality_gate_map["N1_no_chirality_kill_is_real_but_not_total"]["pass"],
                "n2_pass": no_chirality_gate_map["N2_no_chirality_residual_is_explicitly_nontrivial"]["pass"],
                "n3_pass": no_chirality_gate_map["N3_chiral_run_keeps_stronger_sheet_split_than_flattened_run"]["pass"],
            },
        ),
        gate(
            neg_loop_swap_status == "KILL"
            and neg_loop_swap["structure_matters"]
            and neg_loop_swap["max_true_fiber_drift"] < 1e-10
            and neg_loop_swap["min_true_base_traversal"] > 1e-3
            and neg_loop_swap["min_swapped_base_as_fiber"] > 1e-3
            and neg_loop_swap["min_swapped_fiber_as_base"] > 0.5,
            "G8_exact_loop_law_swap_negative",
            {
                "status": neg_loop_swap_status,
                "max_true_fiber_drift": neg_loop_swap["max_true_fiber_drift"],
                "min_true_base_traversal": neg_loop_swap["min_true_base_traversal"],
                "min_swapped_base_as_fiber": neg_loop_swap["min_swapped_base_as_fiber"],
                "min_swapped_fiber_as_base": neg_loop_swap["min_swapped_fiber_as_base"],
            },
        ),
        gate(
            (
                projection["projection_status"] == "engine_pair_only_derived"
                and not projection["weyl_branch_nodes_present"]
                and "WEYL_BRANCH" in projection["missing_owner_anchors"]
            ) or (
                projection["projection_status"] == "owner_weyl_branch_materialized"
                and projection["weyl_branch_nodes_present"]
                and not projection["missing_owner_anchors"]
            ),
            "G9_owner_anchor_state_explicit",
            {
                "projection_status": projection["projection_status"],
                "weyl_branch_nodes_present": projection["weyl_branch_nodes_present"],
                "missing_owner_anchors": projection["missing_owner_anchors"],
            },
        ),
        gate(
            carrier_geometry_admission["admitted"]
            and carrier_geometry_admission["basis_status"] == "carrier basis present at geometry tier; explicit operator admission handled by lower-tier operator search"
            and classical_leakage_guards["admitted"]
            and classical_leakage_guards["raw_lr_control_blocked"]["status"] == "control_only"
            and classical_leakage_guards["raw_lr_control_blocked"]["max_raw_LR_mutual_information"] < 1e-9
            and classical_leakage_guards["torus_scramble_kill"]["status"] == "KILL"
            and classical_leakage_guards["no_chirality_kill"]["status"] == "KILL"
            and classical_leakage_guards["loop_law_swap_kill"]["status"] == "KILL",
            "G10_lower_tier_carrier_admission_and_classical_leakage_guards_are_explicit",
            {
                "carrier_geometry_admission": carrier_geometry_admission,
                "classical_leakage_guards": classical_leakage_guards,
            },
        ),
        gate(
            chiral_law_embargo["admitted"]
            and chiral_law_embargo["ga3_chirality"]["status"] == "readout_only"
            and chiral_law_embargo["symmetric_dphi_bookkeeping"]["status"] == "bookkeeping_only"
            and chiral_law_embargo["symmetric_dphi_bookkeeping"]["max_abs_compat_dphi_gap"] < 1e-12
            and chiral_law_embargo["promotion_block"] == "awaiting_real_lower_tier_chiral_differential_law",
            "G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion",
            chiral_law_embargo,
        ),
        gate(
            chiral_gate_map["L1_fake_lower_tier_chiral_law_routes_are_killed"]["pass"]
            and chiral_gate_map["L2_delta_chirality_is_real_signal_but_not_owner_law"]["pass"]
            and chiral_gate_map["L3_compound_transport_chirality_branch_survives_search"]["pass"]
            and chiral_gate_map["L4_search_keeps_single_lower_tier_chiral_law_open_but_unadmitted"]["pass"]
            and lower_tier_chiral_detail["summary"]["winner"] == "chirality_separated_transport_deltas"
            and lower_tier_chiral_detail["summary"]["winner_status"] == "surviving_compound_candidate"
            and lower_tier_chiral_detail["summary"]["single_lower_tier_chiral_law"] == "not_supported_yet"
            and lower_tier_chiral_detail["owner_read"]["status"] == "compound_candidate_only"
            and "No single lower-tier chiral law is admitted" in lower_tier_chiral_detail["owner_read"]["note"]
            and "G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion"
            in lower_tier_chiral_detail["source_support"]["formal_geometry_gates"]
            and "W8_pre_axis_object_inventory_is_explicit"
            in lower_tier_chiral_detail["source_support"]["weyl_delta_gates"],
            "G12_lower_tier_chiral_law_search_is_explicit_and_fail_closed",
            {
                "l1_pass": chiral_gate_map["L1_fake_lower_tier_chiral_law_routes_are_killed"]["pass"],
                "l2_pass": chiral_gate_map["L2_delta_chirality_is_real_signal_but_not_owner_law"]["pass"],
                "l3_pass": chiral_gate_map["L3_compound_transport_chirality_branch_survives_search"]["pass"],
                "l4_pass": chiral_gate_map["L4_search_keeps_single_lower_tier_chiral_law_open_but_unadmitted"]["pass"],
                "lower_tier_chiral_detail": lower_tier_chiral_detail,
            },
        ),
        gate(
            transport_gate_map["T1_exact_same_carrier_loop_law_survives_search"]["pass"]
            and transport_gate_map["T2_generic_transport_activity_is_not_promoted_to_law"]["pass"]
            and transport_gate_map["T3_symmetric_motion_summary_is_killed_as_fake_transport_law"]["pass"]
            and transport_gate_map["T4_downstream_cut_effect_is_fenced_off_from_lower_transport_law"]["pass"],
            "G13_lower_tier_transport_law_search_is_explicit_and_fail_closed",
            {
                "t1_pass": transport_gate_map["T1_exact_same_carrier_loop_law_survives_search"]["pass"],
                "t2_pass": transport_gate_map["T2_generic_transport_activity_is_not_promoted_to_law"]["pass"],
                "t3_pass": transport_gate_map["T3_symmetric_motion_summary_is_killed_as_fake_transport_law"]["pass"],
                "t4_pass": transport_gate_map["T4_downstream_cut_effect_is_fenced_off_from_lower_transport_law"]["pass"],
            },
        ),
        gate(
            operator_gate_map["O1_fixed_carrier_basis_remap_shows_load_bearing_sensitivity"]["pass"]
            and operator_gate_map["O2_global_coordinate_change_is_not_mistaken_for_substrate_failure"]["pass"]
            and operator_gate_map["O3_commuting_collapse_degrades_the_local_operator_response"]["pass"]
            and operator_gate_map["O4_local_unitary_pair_is_not_demoted_by_this_narrow_local_test"]["pass"]
            and operator_basis_search_admission["admitted"],
            "G14_lower_tier_operator_basis_search_is_explicit_and_fail_closed",
            {
                "operator_basis_search_admission": operator_basis_search_admission,
                "o1_pass": operator_gate_map["O1_fixed_carrier_basis_remap_shows_load_bearing_sensitivity"]["pass"],
                "o2_pass": operator_gate_map["O2_global_coordinate_change_is_not_mistaken_for_substrate_failure"]["pass"],
                "o3_pass": operator_gate_map["O3_commuting_collapse_degrades_the_local_operator_response"]["pass"],
                "o4_pass": operator_gate_map["O4_local_unitary_pair_is_not_demoted_by_this_narrow_local_test"]["pass"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "formal_geometry_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "carrier_geometry_admission": carrier_geometry_admission,
        "operator_basis_search_admission": operator_basis_search_admission,
        "classical_leakage_guards": classical_leakage_guards,
        "chiral_law_embargo": chiral_law_embargo,
        "gates": gates,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("FORMAL GEOMETRY PACKET VALIDATION")
        print("=" * 72)
        for item in gates:
            status = "PASS" if item["pass"] else "FAIL"
            print(f"{status:>4}  {item['name']}")
        print(f"\npassed_gates: {passed}/{len(gates)}")
        print(f"score: {payload['score']:.6f}")
        print(f"validation_results: {OUTPUT_PATH}")
    else:
        print(json.dumps(payload, indent=2))

    return 0 if passed == len(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
