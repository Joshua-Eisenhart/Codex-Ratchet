#!/usr/bin/env python3
"""
validate_pre_entropy_packet.py
==============================

Mechanical validator for the executable pre-entropy ladder.

This packet sits between the formal geometry layer and the entropy readout:
  - direct L|R control
  - point/shell/history bridge family
  - fail-closed bridge admission
  - multi-cycle bridge stability
  - FE-indexed refinement branch
  - dynamic shell as a current unresolved branch
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "pre_entropy_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    xi_strict = load_json(SIM_RESULTS / "axis0_xi_strict_bakeoff_results.json")
    bridge_search = load_json(SIM_RESULTS / "axis0_bridge_search_results.json")
    phase5b = load_json(SIM_RESULTS / "axis0_phase5b_results.json")
    fe_indexed = load_json(SIM_RESULTS / "axis0_fe_indexed_xi_hist_results.json")
    dynamic_shell = load_json(SIM_RESULTS / "axis0_dynamic_shell_results.json")
    weyl_delta = load_json(SIM_RESULTS / "weyl_delta_packet_results.json")
    neg_no_chirality = load_json(SIM_RESULTS / "neg_no_chirality_results.json")
    neg_loop_law_swap = load_json(SIM_RESULTS / "neg_loop_law_swap_results.json")
    joint_ablation = load_json(SIM_RESULTS / "neg_transport_delta_joint_ablation_results.json")
    c1_signed_bridge = load_json(SIM_RESULTS / "c1_signed_bridge_candidate_search_validation.json")

    strict_verdict = xi_strict["verdict"]
    discriminators = strict_verdict["discriminators"]
    row_summary = strict_verdict["rowwise_advantage_summary"]
    history_profile = strict_verdict["history_window_profile_summary"]
    placement_profile = strict_verdict["history_window_placement_summary"]
    early_width_profile = strict_verdict["history_early_width_summary"]
    prefix_drop_profile = strict_verdict["history_prefix_drop_summary"]
    late_anchor_profile = strict_verdict["history_late_anchor_equivalence_summary"]
    xi_hist_signed_law = strict_verdict["xi_hist_signed_law_summary"]
    shell_variation = strict_verdict["pointwise_shell_loop_variation"]
    best_bridge = bridge_search["winner"]
    mean_mi = bridge_search["mean_mi_by_candidate"]
    mean_ic = bridge_search["mean_ic_by_candidate"]
    sorted_bridge_candidates = sorted(mean_mi.items(), key=lambda item: item[1], reverse=True)
    runner_up_name, runner_up_mi = sorted_bridge_candidates[1]
    winner_margin = mean_mi[best_bridge] - runner_up_mi

    phase5b_inner = phase5b["multi_cycle_1/inner"]
    phase5b_outer = phase5b["multi_cycle_1/outer"]
    phase5b_clifford = phase5b["multi_cycle_1/clifford"]

    fe_summary = fe_indexed["summary"]
    shell_summary = dynamic_shell["summary"]
    delta_branches = weyl_delta["branch_map"]
    delta_inventory = weyl_delta["pre_axis_object_inventory"]
    chirality_retention_ratio = float(neg_no_chirality["d_flat"] / neg_no_chirality["d_chiral"])
    owner_worthiness_map = {
        "owner_derived": {
            "xi_hist_signed_law": "admitted",
            "bridge_admission_rule": "admitted",
        },
        "pre_axis_law": {
            "late_anchor_equivalence": "admitted",
            "clifford_local_short_width_stress": "admitted",
            "chirality_separated_transport_deltas": "candidate",
            "chirality_separated_transport_deltas_blocker": "awaiting_owner_promotion_decision_after_nonproxy_support",
        },
        "axis_internal_readout": {
            "I_c_A_to_B": "readout",
            "S_A_given_B": "readout",
            "Xi_chiral_entangle": "current_bridge_candidate",
            "Xi_chiral_entangle_relation": "downstream_of_xi_hist_signed_law_not_alternate_owner_law",
        },
        "diagnostic_only": {
            "raw_delta_packet": "diagnostic_only",
            "single_weyl_flux_object": "not_supported_yet",
            "entropic_left_right_flux": "blocked",
            "post_joint_cut_flux": "downstream_branch",
        },
    }
    joint_necessity_witness = {
        "transport_delta_candidate": "chirality-separated loop-sensitive transport deltas",
        "same_carrier_chirality_ablation": {
            "status": "partial_support",
            "d_chiral": float(neg_no_chirality["d_chiral"]),
            "d_flat": float(neg_no_chirality["d_flat"]),
            "retention_ratio": chirality_retention_ratio,
        },
        "same_carrier_loop_law_ablation": {
            "status": "strong_support",
            "structure_matters": bool(neg_loop_law_swap["structure_matters"]),
            "max_true_fiber_drift": float(neg_loop_law_swap["max_true_fiber_drift"]),
            "min_true_base_traversal": float(neg_loop_law_swap["min_true_base_traversal"]),
            "min_swapped_base_as_fiber": float(neg_loop_law_swap["min_swapped_base_as_fiber"]),
            "min_swapped_fiber_as_base": float(neg_loop_law_swap["min_swapped_fiber_as_base"]),
        },
        "combined_same_carrier_ablation": {
            "status": joint_ablation["owner_read"]["status"],
            "summary": joint_ablation["summary"],
            "blocker": "awaiting_owner_promotion_decision_after_nonproxy_support",
        },
    }
    pre_axis_admission_schema = {
        "object": "pre_axis_admission_schema",
        "scope": "constraint-aligned QIT-grounded machinery before Axis 0 promotion",
        "lifecycle": [
            {
                "stage": "formalized",
                "requirement": "explicit math object and dependency placement",
                "axis_usable": False,
            },
            {
                "stage": "qit_grounded",
                "requirement": "finite-carrier density/operator realization",
                "axis_usable": False,
            },
            {
                "stage": "sim_live",
                "requirement": "mechanically active runner or packet artifact",
                "axis_usable": False,
            },
            {
                "stage": "neg_tested",
                "requirement": "same-carrier negatives or falsification pressure",
                "axis_usable": False,
            },
            {
                "stage": "placement_classified",
                "requirement": "owner-derived vs pre-axis vs axis-internal vs diagnostic-only",
                "axis_usable": False,
            },
            {
                "stage": "axis_eligible",
                "requirement": "admitted or owner-derived object with downstream use allowed",
                "axis_usable": True,
            },
        ],
        "machinery_families": {
            "carrier_basis": {
                "status": "qit_grounded_upstream",
                "objects": ["hopf_carrier_point", "nested_torus_seat"],
            },
            "weyl_refinement": {
                "status": "sim_live",
                "objects": ["weyl_sheet_pair"],
            },
            "transport_differential": {
                "status": "candidate_pre_axis_law",
                "objects": [
                    "loop_sensitive_transport_surface",
                    "chirality_differential_surface",
                    "bloch_differential_surface",
                ],
            },
            "bridge_entropy_entry": {
                "status": "downstream_axis_entry_only",
                "objects": ["bridge_ready_cut_object", "Xi_chiral_entangle", "I_c_A_to_B", "S_A_given_B"],
            },
        },
        "classical_leakage_guards": {
            "continuum_flow": "guarded_by_finite_qit_carrier_and_stagewise_deltas",
            "entropy_first_readout": "guarded_by_pre_entropy_before_entropy_readout",
            "flux_shorthand": "guarded_by_branch_map_and_diagnostic_demotion",
            "same_carrier_necessity": "guarded_by_nonproxy_runtime_support_but_not_promoted",
            "same_carrier_runtime_witness": "direct_sheet_split_and_direct_per_sheet_traversal_are_now_explicit",
            "downstream_cut_smuggling": "guarded_by_downstream_not_pre_axis_fence",
        },
        "axis_embargo": {
            "rule": "No object may function as Axis math before QIT grounding, live simulation, negative support, and placement classification are closed.",
            "required_before_axis_use": [
                "qit_grounded",
                "sim_live",
                "neg_tested",
                "placement_classified",
            ],
            "currently_axis_eligible": {
                "xi_hist_signed_law": "owner_derived",
                "bridge_admission_rule": "owner_derived",
            },
            "currently_embargoed": {
                "chirality_separated_transport_deltas": "candidate_pending_owner_promotion_after_nonproxy_support",
                "raw_delta_packet": "diagnostic_only",
                "single_weyl_flux_object": "not_supported_yet",
                "entropic_left_right_flux": "blocked",
                "post_joint_cut_flux": "downstream_branch",
            },
        },
        "current_mapping": {
            "hopf_carrier_point": "qit_grounded",
            "nested_torus_seat": "qit_grounded",
            "weyl_sheet_pair": "sim_live",
            "loop_sensitive_transport_surface": "sim_live_candidate",
            "chirality_differential_surface": "sim_live_candidate",
            "bloch_differential_surface": "sim_live_candidate",
            "chirality_separated_transport_deltas": "neg_tested_candidate_with_nonproxy_runtime_support_not_axis_eligible",
            "Xi_chiral_entangle": "axis_internal_candidate_not_final_owner_law",
            "xi_hist_signed_law": "axis_eligible_owner_derived",
        },
        "placement_relations": {
            "Xi_chiral_entangle": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
            "xi_hist_signed_law": "owner_derived_law_that_binds_bridge_handoff",
        },
    }

    gates = [
        gate(
            best_bridge == "Xi_chiral_entangle"
            and mean_mi["Xi_LR_direct"] < 1e-12
            and mean_mi["Xi_chiral_entangle"] > 0.5
            and mean_ic["Xi_chiral_entangle"] > 0.05
            and mean_ic[runner_up_name] < 0.0
            and winner_margin > 0.05,
            "P1_bridge_admission_is_fail_closed",
            {
                "winner": best_bridge,
                "winner_mean_mi": mean_mi[best_bridge],
                "winner_mean_i_c": mean_ic[best_bridge],
                "runner_up": runner_up_name,
                "runner_up_mean_mi": runner_up_mi,
                "runner_up_mean_i_c": mean_ic[runner_up_name],
                "winner_margin": winner_margin,
                "lr_direct_mean_mi": mean_mi["Xi_LR_direct"],
            },
        ),
        gate(
            discriminators["hist_outer_minus_lr_mi"] > 0.005
            and discriminators["hist_cycle_minus_lr_mi"] > 0.005
            and discriminators["history_nontrivial_while_shell_flat"]
            and discriminators["point_ref_minus_shell_base_std"] > 0.1,
            "P2_strict_bakeoff_separates_bridge_from_controls",
            {
                "hist_outer_minus_lr_mi": discriminators["hist_outer_minus_lr_mi"],
                "hist_cycle_minus_lr_mi": discriminators["hist_cycle_minus_lr_mi"],
                "history_nontrivial_while_shell_flat": discriminators["history_nontrivial_while_shell_flat"],
                "xi_lr_direct_MI": strict_verdict["means"]["xi_lr_direct_MI"],
                "point_ref_minus_shell_base_std": discriminators["point_ref_minus_shell_base_std"],
            },
        ),
        gate(
            row_summary["history_outer_beats_lr_count"] >= 4
            and row_summary["history_outer_beats_lr_while_shell_flat_count"] >= 4
            and abs(history_profile["mean_history_outer_minus_cycle_mi"]) < 1e-12
            and history_profile["outer_window_beats_cycle_count"] == 0
            and history_profile["cycle_window_beats_outer_count"] == 0,
            "P3_history_windows_currently_degenerate",
            {
                "history_outer_beats_lr_count": row_summary["history_outer_beats_lr_count"],
                "history_outer_beats_lr_while_shell_flat_count": row_summary["history_outer_beats_lr_while_shell_flat_count"],
                "outer_window_beats_cycle_count": history_profile["outer_window_beats_cycle_count"],
                "cycle_window_beats_outer_count": history_profile["cycle_window_beats_outer_count"],
                "mean_history_outer_minus_cycle_mi": history_profile["mean_history_outer_minus_cycle_mi"],
            },
        ),
        gate(
            shell_variation["inner"]["shell_strata"]["fiber_I_std"] < 1e-12
            and shell_variation["inner"]["point_ref"]["base_I_std"] > 0.1
            and shell_variation["clifford"]["point_ref"]["base_I_std"] > 0.1
            and shell_variation["outer"]["point_ref"]["base_I_std"] > 0.1,
            "P4_shell_flat_pointref_varies",
            {
                "inner_shell_fiber_I_std": shell_variation["inner"]["shell_strata"]["fiber_I_std"],
                "inner_pointref_base_I_std": shell_variation["inner"]["point_ref"]["base_I_std"],
                "clifford_pointref_base_I_std": shell_variation["clifford"]["point_ref"]["base_I_std"],
                "outer_pointref_base_I_std": shell_variation["outer"]["point_ref"]["base_I_std"],
            },
        ),
        gate(
            min(item["winner_cumulative_MI"] for item in phase5b_inner) > 1.59
            and min(item["winner_cumulative_MI"] for item in phase5b_outer) > 1.59
            and max(item["product_cumulative_MI"] for item in phase5b_inner) < 0.012
            and max(item["product_cumulative_MI"] for item in phase5b_outer) < 0.012,
            "P5_bridge_is_multicycle_stable_off_clifford",
            {
                "inner_min_winner_cumulative_MI": min(item["winner_cumulative_MI"] for item in phase5b_inner),
                "outer_min_winner_cumulative_MI": min(item["winner_cumulative_MI"] for item in phase5b_outer),
                "inner_max_product_cumulative_MI": max(item["product_cumulative_MI"] for item in phase5b_inner),
                "outer_max_product_cumulative_MI": max(item["product_cumulative_MI"] for item in phase5b_outer),
            },
        ),
        gate(
            max(item["winner_cumulative_MI"] for item in phase5b_clifford) < 1.2
            and max(item["product_cumulative_MI"] for item in phase5b_clifford) < 0.005,
            "P6_clifford_is_the_edge_case_not_the_norm",
            {
                "clifford_max_winner_cumulative_MI": max(item["winner_cumulative_MI"] for item in phase5b_clifford),
                "clifford_max_product_cumulative_MI": max(item["product_cumulative_MI"] for item in phase5b_clifford),
            },
        ),
        gate(
            fe_summary["best_new_bridge"] == "C_fe_pairs_only"
            and fe_summary["winner_counts"]["C_fe_pairs_only"] >= 4
            and fe_summary["best_gain"] > 0.1
            and fe_summary["mean_fe_advantage"] > 0.1,
            "P7_fe_indexed_is_partial_refinement_not_replacement",
            {
                "best_new_bridge": fe_summary["best_new_bridge"],
                "best_gain": fe_summary["best_gain"],
                "winner_counts": fe_summary["winner_counts"],
                "mean_fe_advantage": fe_summary["mean_fe_advantage"],
            },
        ),
        gate(
            shell_summary["full_keeps"] == 0
            and shell_summary["total"] == 6
            and shell_summary["keep_lane_b"] >= 1
            and shell_summary["overall"] == "SHELL PROPOSAL NOT SUPPORTED",
            "P8_dynamic_shell_is_explicitly_unresolved",
            {
                "full_keeps": shell_summary["full_keeps"],
                "total": shell_summary["total"],
                "keep_lane_b": shell_summary["keep_lane_b"],
                "overall": shell_summary["overall"],
            },
        ),
        gate(
            placement_profile["best_placement_by_mi_counts"]["16_31"] == 0
            and placement_profile["best_placement_by_mi_counts"]["0_15"] == 4
            and placement_profile["best_placement_by_mi_counts"]["8_23"] == 2
            and placement_profile["early_window_beats_shifted_count"] == 4
            and early_width_profile["best_early_width_by_mi_counts"]["0_3"] == 6
            and early_width_profile["early_width_mi_monotonic_growth_count"] == 0
            and prefix_drop_profile["prefix_drop_mi_monotonic_loss_count"] == 0,
            "P9_xi_hist_handoff_is_placement_sensitive_not_width_accumulative",
            {
                "best_placement_by_mi_counts": placement_profile["best_placement_by_mi_counts"],
                "early_window_beats_shifted_count": placement_profile["early_window_beats_shifted_count"],
                "best_early_width_by_mi_counts": early_width_profile["best_early_width_by_mi_counts"],
                "early_width_mi_monotonic_growth_count": early_width_profile["early_width_mi_monotonic_growth_count"],
                "best_prefix_drop_by_mi_counts": prefix_drop_profile["best_prefix_drop_by_mi_counts"],
                "prefix_drop_mi_monotonic_loss_count": prefix_drop_profile["prefix_drop_mi_monotonic_loss_count"],
            },
        ),
        gate(
            all(row["best_placement_by_ic"] == "8_23" for row in placement_profile["rows"])
            and all(row["best_early_width_by_ic"] == "0_3" for row in early_width_profile["rows"])
            and all(row["best_prefix_drop_by_ic"] == "8_15" for row in prefix_drop_profile["rows"])
            and all(row["ic_0_15_minus_8_23"] < -0.04 for row in placement_profile["rows"])
            and all(row["ic_0_15_minus_0_3"] < -0.01 for row in early_width_profile["rows"])
            and sum(1 for row in prefix_drop_profile["rows"] if row["ic_0_15_minus_2_15"] < 0.0) >= 5
            and min(
                row["ic_by_prefix_drop"]["8_15"] - row["ic_by_prefix_drop"]["2_15"]
                for row in prefix_drop_profile["rows"]
            ) > 0.04
            and min(
                row["signed_cut_by_placement"]["0_15"] - row["signed_cut_by_placement"]["8_23"]
                for row in placement_profile["rows"]
            ) > 0.04
            and min(
                row["signed_cut_by_early_width"]["0_15"] - row["signed_cut_by_early_width"]["0_3"]
                for row in early_width_profile["rows"]
            ) > 0.01
            and sum(
                1
                for row in prefix_drop_profile["rows"]
                if row["signed_cut_by_prefix_drop"]["0_15"] - row["signed_cut_by_prefix_drop"]["2_15"] > 0.0
            ) >= 5
            and min(
                row["signed_cut_by_prefix_drop"]["2_15"] - row["signed_cut_by_prefix_drop"]["8_15"]
                for row in prefix_drop_profile["rows"]
            ) > 0.04,
            "P10_xi_hist_signed_handoff_prefers_back_half_and_short_stress",
            {
                "best_placement_by_ic_counts": {
                    label: int(sum(1 for row in placement_profile["rows"] if row["best_placement_by_ic"] == label))
                    for label in placement_profile["placement_labels"]
                },
                "best_early_width_by_ic_counts": {
                    label: int(sum(1 for row in early_width_profile["rows"] if row["best_early_width_by_ic"] == label))
                    for label in early_width_profile["width_labels"]
                },
                "best_prefix_drop_by_ic_counts": {
                    label: int(sum(1 for row in prefix_drop_profile["rows"] if row["best_prefix_drop_by_ic"] == label))
                    for label in prefix_drop_profile["prefix_drop_labels"]
                },
                "min_ic_0_15_minus_8_23": min(row["ic_0_15_minus_8_23"] for row in placement_profile["rows"]),
                "min_ic_0_15_minus_0_3": min(row["ic_0_15_minus_0_3"] for row in early_width_profile["rows"]),
                "negative_ic_0_15_minus_2_15_count": int(sum(1 for row in prefix_drop_profile["rows"] if row["ic_0_15_minus_2_15"] < 0.0)),
                "min_ic_8_15_minus_2_15": min(
                    row["ic_by_prefix_drop"]["8_15"] - row["ic_by_prefix_drop"]["2_15"]
                    for row in prefix_drop_profile["rows"]
                ),
                "min_signed_0_15_minus_8_23": min(
                    row["signed_cut_by_placement"]["0_15"] - row["signed_cut_by_placement"]["8_23"]
                    for row in placement_profile["rows"]
                ),
                "min_signed_0_15_minus_0_3": min(
                    row["signed_cut_by_early_width"]["0_15"] - row["signed_cut_by_early_width"]["0_3"]
                    for row in early_width_profile["rows"]
                ),
                "positive_signed_0_15_minus_2_15_count": int(
                    sum(
                        1
                        for row in prefix_drop_profile["rows"]
                        if row["signed_cut_by_prefix_drop"]["0_15"] - row["signed_cut_by_prefix_drop"]["2_15"] > 0.0
                    )
                ),
                "min_signed_2_15_minus_8_15": min(
                    row["signed_cut_by_prefix_drop"]["2_15"] - row["signed_cut_by_prefix_drop"]["8_15"]
                    for row in prefix_drop_profile["rows"]
                ),
            },
        ),
        gate(
            late_anchor_profile["placement_8_23_equals_16_31_count"] == late_anchor_profile["total_rows"]
            and late_anchor_profile["placement_8_23_equals_prefix_8_15_on_mi_count"] == late_anchor_profile["total_rows"]
            and late_anchor_profile["placement_8_23_equals_prefix_8_15_on_ic_count"] == late_anchor_profile["total_rows"]
            and late_anchor_profile["placement_8_23_equals_prefix_8_15_on_signed_count"] == late_anchor_profile["total_rows"]
            and late_anchor_profile["placement_8_23_beats_0_3_on_ic_count"] >= 4,
            "P11_xi_hist_signed_late_anchor_is_equivalent_not_free_placement",
            {
                "total_rows": late_anchor_profile["total_rows"],
                "placement_8_23_equals_16_31_count": late_anchor_profile["placement_8_23_equals_16_31_count"],
                "placement_8_23_equals_prefix_8_15_on_mi_count": late_anchor_profile["placement_8_23_equals_prefix_8_15_on_mi_count"],
                "placement_8_23_equals_prefix_8_15_on_ic_count": late_anchor_profile["placement_8_23_equals_prefix_8_15_on_ic_count"],
                "placement_8_23_equals_prefix_8_15_on_signed_count": late_anchor_profile["placement_8_23_equals_prefix_8_15_on_signed_count"],
                "placement_8_23_beats_0_3_on_ic_count": late_anchor_profile["placement_8_23_beats_0_3_on_ic_count"],
            },
        ),
        gate(
            late_anchor_profile["placement_8_23_beats_0_3_on_ic_off_clifford_count"] == 4
            and late_anchor_profile["short_width_0_3_beats_8_23_on_ic_clifford_count"] == 2,
            "P12_xi_hist_short_width_stress_is_clifford_local_not_global",
            {
                "placement_8_23_beats_0_3_on_ic_off_clifford_count": late_anchor_profile["placement_8_23_beats_0_3_on_ic_off_clifford_count"],
                "short_width_0_3_beats_8_23_on_ic_clifford_count": late_anchor_profile["short_width_0_3_beats_8_23_on_ic_clifford_count"],
                "total_rows": late_anchor_profile["total_rows"],
            },
        ),
        gate(
            all(row["best_early_width_by_ic"] == "0_3" for row in early_width_profile["rows"])
            and all(row["best_prefix_drop_by_ic"] == "8_15" for row in prefix_drop_profile["rows"])
            and all(abs(row["ic_8_23_minus_8_15"]) < 1e-12 for row in late_anchor_profile["rows"])
            and all(abs(row["signed_8_23_minus_8_15"]) < 1e-12 for row in late_anchor_profile["rows"])
            and min(
                row["ic_by_prefix_drop"]["8_15"] - row["ic_by_prefix_drop"]["2_15"]
                for row in prefix_drop_profile["rows"]
            ) > 0.04
            and min(
                row["signed_cut_by_prefix_drop"]["2_15"] - row["signed_cut_by_prefix_drop"]["8_15"]
                for row in prefix_drop_profile["rows"]
            ) > 0.04
            and min(
                row["ic_8_23_minus_0_3"]
                for row in late_anchor_profile["rows"]
                if row["torus"] != "clifford"
            ) > 0.14
            and max(
                row["ic_8_23_minus_0_3"]
                for row in late_anchor_profile["rows"]
                if row["torus"] == "clifford"
            ) < -0.02,
            "P13_xi_hist_typing_law_8_15_vs_2_15_vs_0_3",
            {
                "best_early_width_by_ic_counts": {
                    label: int(sum(1 for row in early_width_profile["rows"] if row["best_early_width_by_ic"] == label))
                    for label in early_width_profile["width_labels"]
                },
                "best_prefix_drop_by_ic_counts": {
                    label: int(sum(1 for row in prefix_drop_profile["rows"] if row["best_prefix_drop_by_ic"] == label))
                    for label in prefix_drop_profile["prefix_drop_labels"]
                },
                "min_ic_8_15_minus_2_15": min(
                    row["ic_by_prefix_drop"]["8_15"] - row["ic_by_prefix_drop"]["2_15"]
                    for row in prefix_drop_profile["rows"]
                ),
                "min_signed_2_15_minus_8_15": min(
                    row["signed_cut_by_prefix_drop"]["2_15"] - row["signed_cut_by_prefix_drop"]["8_15"]
                    for row in prefix_drop_profile["rows"]
                ),
                "off_clifford_min_ic_8_23_minus_0_3": min(
                    row["ic_8_23_minus_0_3"]
                    for row in late_anchor_profile["rows"]
                    if row["torus"] != "clifford"
                ),
                "clifford_max_ic_8_23_minus_0_3": max(
                    row["ic_8_23_minus_0_3"]
                    for row in late_anchor_profile["rows"]
                    if row["torus"] == "clifford"
                ),
            },
        ),
        gate(
            xi_hist_signed_law["law_name"] == "Xi_hist signed law"
            and xi_hist_signed_law["late_anchor_equivalence"]["placement_8_23_equals_16_31"]
            and xi_hist_signed_law["late_anchor_equivalence"]["placement_8_23_equals_prefix_8_15_on_mi"]
            and xi_hist_signed_law["late_anchor_equivalence"]["placement_8_23_equals_prefix_8_15_on_ic"]
            and xi_hist_signed_law["late_anchor_equivalence"]["placement_8_23_equals_prefix_8_15_on_signed_cut"]
            and xi_hist_signed_law["short_width_stress"]["best_early_width_by_ic_is_0_3"]
            and xi_hist_signed_law["short_width_stress"]["late_anchor_beats_0_3_off_clifford"]
            and xi_hist_signed_law["short_width_stress"]["0_3_beats_late_anchor_on_clifford_only"],
            "P14_xi_hist_signed_law_is_explicit_in_strict_bakeoff",
            {
                "law_name": xi_hist_signed_law["law_name"],
                "owner_read": xi_hist_signed_law["owner_read"],
                "late_anchor_equivalence": xi_hist_signed_law["late_anchor_equivalence"],
                "short_width_stress": xi_hist_signed_law["short_width_stress"],
                "counts": xi_hist_signed_law["counts"],
            },
        ),
        gate(
            delta_inventory["raw_delta_packet"]["status"] == "diagnostic_surface_not_final_owner_law"
            and delta_branches["single_weyl_flux_object"]["status"] == "not_supported_yet"
            and owner_worthiness_map["owner_derived"]["xi_hist_signed_law"] == "admitted"
            and owner_worthiness_map["pre_axis_law"]["chirality_separated_transport_deltas"] == "candidate"
            and owner_worthiness_map["diagnostic_only"]["raw_delta_packet"] == "diagnostic_only"
            and owner_worthiness_map["diagnostic_only"]["entropic_left_right_flux"] == "blocked",
            "P15_owner_worthiness_map_demotes_raw_deltas_and_open_flux_labels",
            {
                "owner_worthiness_map": owner_worthiness_map,
                "delta_raw_surface_status": delta_inventory["raw_delta_packet"]["status"],
                "single_weyl_flux_object": delta_branches["single_weyl_flux_object"],
            },
        ),
        gate(
            delta_branches["chirality_separated_transport_deltas"]["status"] == "surviving_pre_axis_candidate"
            and owner_worthiness_map["pre_axis_law"]["chirality_separated_transport_deltas"] == "candidate"
            and owner_worthiness_map["pre_axis_law"]["chirality_separated_transport_deltas_blocker"] == "awaiting_owner_promotion_decision_after_nonproxy_support",
            "P16_transport_delta_branch_survives_but_is_not_owner_law_yet",
            {
                "chirality_separated_transport_deltas": delta_branches["chirality_separated_transport_deltas"],
                "blocker": owner_worthiness_map["pre_axis_law"]["chirality_separated_transport_deltas_blocker"],
            },
        ),
        gate(
            neg_no_chirality["chirality_matters"]
            and chirality_retention_ratio < 0.8
            and neg_loop_law_swap["structure_matters"]
            and neg_loop_law_swap["max_true_fiber_drift"] < 1e-10
            and neg_loop_law_swap["min_true_base_traversal"] > 1e-3
            and joint_necessity_witness["combined_same_carrier_ablation"]["status"] == "nonproxy_runtime_support",
            "P17_transport_delta_branch_now_has_nonproxy_joint_necessity_support",
            joint_necessity_witness,
        ),
        gate(
            joint_ablation["owner_read"]["status"] == "nonproxy_runtime_support"
            and joint_ablation["summary"]["live_min_score"] > 0.1
            and joint_ablation["summary"]["flat_max_score"] == 0.0
            and joint_ablation["summary"]["swapped_max_score"] < 1e-12
            and joint_ablation["summary"]["combined_max_score"] == 0.0
            and joint_ablation["summary"]["flat_beats_live_count"] == 0
            and joint_ablation["summary"]["swapped_beats_live_count"] == 0
            and joint_ablation["summary"]["combined_beats_live_count"] == 0,
            "P18_joint_same_carrier_ablation_keeps_proxy_screen_closed",
            joint_ablation["summary"],
        ),
        gate(
            joint_ablation["summary"]["live_min_transport_gap"] > 0.10
            and joint_ablation["summary"]["combined_max_transport_gap"] < 0.03
            and joint_ablation["summary"]["combined_gap_retention"] < 0.25
            and joint_ablation["summary"]["swapped_max_transport_gap"] < 1e-12,
            "P19_transport_gap_scalar_is_live_and_joint_ablation_collapses_it",
            {
                "live_min_transport_gap": joint_ablation["summary"]["live_min_transport_gap"],
                "combined_max_transport_gap": joint_ablation["summary"]["combined_max_transport_gap"],
                "swapped_max_transport_gap": joint_ablation["summary"]["swapped_max_transport_gap"],
                "combined_gap_retention": joint_ablation["summary"]["combined_gap_retention"],
            },
        ),
        gate(
            joint_ablation["owner_read"]["status"] == "nonproxy_runtime_support"
            and joint_ablation["summary"]["live_min_sheet_split"] > 0.1
            and joint_ablation["summary"]["flat_max_sheet_split"] < 1e-12
            and joint_ablation["summary"]["swapped_max_sheet_split"] > 0.1
            and joint_ablation["summary"]["combined_max_sheet_split"] < 1e-12
            and joint_ablation["summary"]["live_min_direct_min_traversal"] > 0.1
            and joint_ablation["summary"]["swapped_max_direct_min_traversal"] < 1e-12
            and joint_ablation["summary"]["combined_max_direct_min_traversal"] < 1e-12,
            "P20_joint_same_carrier_nonproxy_runtime_witness_is_explicit",
            {
                "owner_read": joint_ablation["owner_read"],
                "live_min_sheet_split": joint_ablation["summary"]["live_min_sheet_split"],
                "flat_max_sheet_split": joint_ablation["summary"]["flat_max_sheet_split"],
                "swapped_max_sheet_split": joint_ablation["summary"]["swapped_max_sheet_split"],
                "combined_max_sheet_split": joint_ablation["summary"]["combined_max_sheet_split"],
                "live_min_direct_min_traversal": joint_ablation["summary"]["live_min_direct_min_traversal"],
                "swapped_max_direct_min_traversal": joint_ablation["summary"]["swapped_max_direct_min_traversal"],
                "combined_max_direct_min_traversal": joint_ablation["summary"]["combined_max_direct_min_traversal"],
            },
        ),
        gate(
            pre_axis_admission_schema["machinery_families"]["carrier_basis"]["status"] == "qit_grounded_upstream"
            and pre_axis_admission_schema["machinery_families"]["transport_differential"]["status"] == "candidate_pre_axis_law"
            and pre_axis_admission_schema["classical_leakage_guards"]["flux_shorthand"] == "guarded_by_branch_map_and_diagnostic_demotion"
            and pre_axis_admission_schema["classical_leakage_guards"]["same_carrier_necessity"] == "guarded_by_nonproxy_runtime_support_but_not_promoted"
            and pre_axis_admission_schema["axis_embargo"]["currently_axis_eligible"]["xi_hist_signed_law"] == "owner_derived"
            and pre_axis_admission_schema["axis_embargo"]["currently_embargoed"]["chirality_separated_transport_deltas"] == "candidate_pending_owner_promotion_after_nonproxy_support"
            and pre_axis_admission_schema["axis_embargo"]["currently_embargoed"]["single_weyl_flux_object"] == "not_supported_yet"
            and pre_axis_admission_schema["current_mapping"]["Xi_chiral_entangle"] == "axis_internal_candidate_not_final_owner_law",
            "P21_pre_axis_admission_schema_is_explicit_and_axis_embargoed",
            pre_axis_admission_schema,
        ),
        gate(
            c1_signed_bridge["passed_gates"] == c1_signed_bridge["total_gates"]
            and c1_signed_bridge["score"] == 1.0,
            "P22_c1_signed_bridge_candidate_is_explicit_and_provisional",
            {
                "passed_gates": c1_signed_bridge["passed_gates"],
                "total_gates": c1_signed_bridge["total_gates"],
                "score": c1_signed_bridge["score"],
            },
        ),
        gate(
            owner_worthiness_map["owner_derived"]["xi_hist_signed_law"] == "admitted"
            and owner_worthiness_map["axis_internal_readout"]["Xi_chiral_entangle"] == "current_bridge_candidate"
            and owner_worthiness_map["axis_internal_readout"]["Xi_chiral_entangle_relation"] == "downstream_of_xi_hist_signed_law_not_alternate_owner_law"
            and pre_axis_admission_schema["axis_embargo"]["currently_axis_eligible"]["xi_hist_signed_law"] == "owner_derived"
            and pre_axis_admission_schema["current_mapping"]["Xi_chiral_entangle"] == "axis_internal_candidate_not_final_owner_law"
            and pre_axis_admission_schema["placement_relations"]["Xi_chiral_entangle"] == "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law"
            and pre_axis_admission_schema["placement_relations"]["xi_hist_signed_law"] == "owner_derived_law_that_binds_bridge_handoff",
            "P23_xi_chiral_entangle_remains_downstream_of_xi_hist_signed_law",
            {
                "owner_worthiness_map": owner_worthiness_map,
                "placement_relations": pre_axis_admission_schema["placement_relations"],
                "current_mapping": pre_axis_admission_schema["current_mapping"],
                "axis_eligible": pre_axis_admission_schema["axis_embargo"]["currently_axis_eligible"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    p11 = next(item for item in gates if item["name"] == "P11_xi_hist_signed_late_anchor_is_equivalent_not_free_placement")
    p12 = next(item for item in gates if item["name"] == "P12_xi_hist_short_width_stress_is_clifford_local_not_global")
    p13 = next(item for item in gates if item["name"] == "P13_xi_hist_typing_law_8_15_vs_2_15_vs_0_3")
    payload = {
        "name": "pre_entropy_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "xi_hist_signed_law": {
            "object": "Xi_hist signed law",
            "admitted": bool(p11["pass"] and p12["pass"] and p13["pass"]),
            "source_gates": [p11["name"], p12["name"], p13["name"]],
            "late_anchor": {
                "placement_label": "8_23",
                "equivalent_labels": ["16_31", "8_15"],
                "detail": p11["detail"],
            },
            "short_width_exception": {
                "width_label": "0_3",
                "scope": "clifford only",
                "detail": p12["detail"],
            },
            "typed_ordering": {
                "winner": "8_15",
                "midpoint_probe": "2_15",
                "local_stress_probe": "0_3",
                "detail": p13["detail"],
            },
        },
        "law_summary": {
            "name": "late-anchor-equivalence_plus_clifford-local-short-width-stress",
            "total_rows": int(late_anchor_profile["total_rows"]),
            "strict_bakeoff_owner_object_present": True,
            "late_anchor_equivalence": {
                "placement_8_23_equals_16_31_count": int(late_anchor_profile["placement_8_23_equals_16_31_count"]),
                "placement_8_23_equals_prefix_8_15_on_mi_count": int(late_anchor_profile["placement_8_23_equals_prefix_8_15_on_mi_count"]),
                "placement_8_23_equals_prefix_8_15_on_ic_count": int(late_anchor_profile["placement_8_23_equals_prefix_8_15_on_ic_count"]),
                "placement_8_23_equals_prefix_8_15_on_signed_count": int(late_anchor_profile["placement_8_23_equals_prefix_8_15_on_signed_count"]),
            },
            "clifford_local_short_width_stress": {
                "placement_8_23_beats_0_3_on_ic_off_clifford_count": int(late_anchor_profile["placement_8_23_beats_0_3_on_ic_off_clifford_count"]),
                "short_width_0_3_beats_8_23_on_ic_clifford_count": int(late_anchor_profile["short_width_0_3_beats_8_23_on_ic_clifford_count"]),
            },
        },
        "owner_worthiness_map": owner_worthiness_map,
        "joint_necessity_witness": joint_necessity_witness,
        "pre_axis_admission_schema": pre_axis_admission_schema,
        "gates": gates,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("PRE-ENTROPY PACKET VALIDATION")
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
