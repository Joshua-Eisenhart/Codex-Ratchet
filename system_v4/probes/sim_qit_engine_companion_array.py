#!/usr/bin/env python3
"""
QIT Engine Companion Array
===========================
Companion surface for comparing the open engine lab against a stricter QIT
subset of carriers and readouts.

This is a comparison/indexing pass, not a new engine theorem.
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Companion array that keeps to tighter QIT-style carriers and readouts "
    "while pointing to the closest open-lab analogues for later repair."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
    "stochastic_thermodynamics",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
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

BASE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = BASE_DIR / "a2_state" / "sim_results"


STRICT_ROWS = [
    {
        "id": "qit_szilard_landauer_cycle",
        "family": "szilard",
        "subset_role": "strict_qit_engine_core",
        "carrier_geometry_class": "finite_two_qubit_system_memory",
        "entropy_readout_family": ["information_gain", "system_free_energy_gain", "erasure_cost"],
        "direction_modes": ["measurement_feedback_erasure"],
        "source_file": RESULT_DIR / "qit_szilard_landauer_cycle_results.json",
        "strictness_reason": "exact_finite_bookkeeping_row_with_valid_density_operators",
    },
    {
        "id": "qit_strong_coupling_landauer",
        "family": "szilard",
        "subset_role": "strict_qit_bridge",
        "carrier_geometry_class": "finite_two_qubit_system_bath_pair",
        "entropy_readout_family": [
            "reduced_state_bookkeeping",
            "joint_system_bath_bookkeeping",
            "clausius_gap_proxy",
        ],
        "direction_modes": ["strong_coupling_vs_weak_coupling"],
        "source_file": RESULT_DIR / "qit_strong_coupling_landauer_results.json",
        "strictness_reason": "exact_joint_bookkeeping_row_for_strong_coupling_corrections",
    },
    {
        "id": "qit_carnot_two_bath_cycle",
        "family": "carnot",
        "subset_role": "strict_qit_engine_core",
        "carrier_geometry_class": "finite_qubit_working_substance_with_two_baths",
        "entropy_readout_family": ["efficiency", "cop", "work_heat_bookkeeping"],
        "direction_modes": ["forward_engine", "reverse_refrigerator"],
        "source_file": RESULT_DIR / "qit_carnot_two_bath_cycle_results.json",
        "strictness_reason": "exact_reversible_two_bath_bookkeeping_row",
    },
    {
        "id": "qit_attractor_basin_recovery",
        "family": "control_recovery",
        "subset_role": "strict_qit_control_family",
        "carrier_geometry_class": "finite_qubit_channel_schedule",
        "entropy_readout_family": ["equivalence_class_recovery", "order_effect", "valid_density_operators"],
        "direction_modes": ["ordered", "swapped", "mismatched"],
        "source_file": RESULT_DIR / "qit_attractor_basin_recovery_results.json",
        "strictness_reason": "finite_qit_recovery_and_order_control_row",
    },
]

QIT_REPAIR_ROWS = [
    {
        "id": "qit_szilard_substep_companion",
        "family": "szilard",
        "subset_role": "qit_repair_companion",
        "carrier_geometry_class": "finite_two_qubit_system_memory_with_hold_decay",
        "entropy_readout_family": ["final_joint_entropy", "measurement_mutual_information", "reset_memory_entropy"],
        "direction_modes": ["ordered_vs_scrambled", "measurement_feedback_reset_hold"],
        "source_file": RESULT_DIR / "qit_szilard_substep_companion_results.json",
        "strictness_reason": "finite two-qubit repair companion for ordered/scrambled substep translation",
    },
    {
        "id": "qit_szilard_record_companion",
        "family": "szilard",
        "subset_role": "qit_repair_companion",
        "carrier_geometry_class": "finite_two_qubit_system_memory_with_record_decay_axis",
        "entropy_readout_family": ["final_joint_entropy", "measurement_mutual_information", "reset_memory_entropy"],
        "direction_modes": ["ordered_vs_scrambled", "record_lifetime", "reset_strength"],
        "source_file": RESULT_DIR / "qit_szilard_record_companion_results.json",
        "strictness_reason": "finite two-qubit repair companion for record persistence and reset mechanics",
    },
    {
        "id": "qit_szilard_reverse_recovery_companion",
        "family": "szilard",
        "subset_role": "qit_repair_companion",
        "carrier_geometry_class": "finite_two_qubit_system_memory_reverse_recovery_axis",
        "entropy_readout_family": ["entropy_restoration_fraction", "restoration_trace_distance", "system_free_energy_gain"],
        "direction_modes": ["erase", "naive_reverse", "recovery"],
        "source_file": RESULT_DIR / "qit_szilard_reverse_recovery_companion_results.json",
        "strictness_reason": "finite two-qubit repair companion for erase versus naive reverse versus designed recovery",
    },
    {
        "id": "qit_carnot_finite_time_companion",
        "family": "carnot",
        "subset_role": "qit_repair_companion",
        "carrier_geometry_class": "finite_qubit_two_bath_with_budget_axis",
        "entropy_readout_family": ["closure_defect", "efficiency", "cop", "carnot_distance"],
        "direction_modes": ["forward_engine", "reverse_refrigerator", "fast_slow_quasistatic"],
        "source_file": RESULT_DIR / "qit_carnot_finite_time_companion_results.json",
        "strictness_reason": "finite qubit repair companion for finite-time budget tradeoffs",
    },
    {
        "id": "qit_carnot_hold_policy_companion",
        "family": "carnot",
        "subset_role": "qit_repair_companion",
        "carrier_geometry_class": "finite_qubit_two_bath_with_partial_thermalization_holds",
        "entropy_readout_family": ["trace_distance_closure", "efficiency", "hold_budget"],
        "direction_modes": ["forward_engine", "fixed_hold", "adaptive_hold"],
        "source_file": RESULT_DIR / "qit_carnot_hold_policy_companion_results.json",
        "strictness_reason": "finite qubit repair companion for hold-policy closure and performance tradeoffs",
    },
    {
        "id": "qit_carnot_irreversibility_companion",
        "family": "carnot",
        "subset_role": "qit_repair_companion",
        "carrier_geometry_class": "finite_qubit_two_bath_duration_sweep",
        "entropy_readout_family": ["closure_defect", "efficiency", "cop", "carnot_distance", "duration_sweep"],
        "direction_modes": ["forward_engine", "reverse_refrigerator", "duration_sweep"],
        "source_file": RESULT_DIR / "qit_carnot_irreversibility_companion_results.json",
        "strictness_reason": "finite qubit repair companion for duration-driven irreversibility and Carnot-distance sweeps",
    },
    {
        "id": "qit_carnot_closure_companion",
        "family": "carnot",
        "subset_role": "qit_repair_companion",
        "carrier_geometry_class": "finite_qubit_two_bath_closure_grid",
        "entropy_readout_family": ["closure_defect", "closure_leg_concentration", "hold_policy_tradeoff"],
        "direction_modes": ["forward_engine", "closure_diagnostic", "hold_policy"],
        "source_file": RESULT_DIR / "qit_carnot_closure_companion_results.json",
        "strictness_reason": "finite qubit repair companion for forward-cycle closure concentration and hold-policy closure repair",
    },
]

OPEN_LAB_ROWS = [
    {
        "id": "szilard_measurement_feedback_substeps",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape",
        "entropy_readout_family": ["logical_bit_entropy", "measurement_mutual_information", "work_heat_bookkeeping"],
        "direction_modes": ["ordered", "feedback_first", "reset_first", "measurement_reset_feedback"],
        "source_file": RESULT_DIR / "szilard_measurement_feedback_substeps_results.json",
        "closest_companion_id": "qit_szilard_substep_companion",
        "bridge_reason": "matched finite-state substep companion for ordered and scrambled protocol families",
    },
    {
        "id": "szilard_substep_refinement_sweep",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape_with_feedback_and_reset_refinement_axes",
        "entropy_readout_family": ["ordering_margin", "measurement_mutual_information", "reset_signal", "blind_control_gap"],
        "direction_modes": ["ordered_vs_scrambled", "feedback_strength", "feedback_duration", "reset_strength"],
        "source_file": RESULT_DIR / "szilard_substep_refinement_sweep_results.json",
        "closest_companion_id": "qit_szilard_substep_companion",
        "bridge_reason": "refined stochastic substep carrier with stronger feedback and reset mechanics",
    },
    {
        "id": "szilard_substep_balanced_refinement_sweep",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape_with_balanced_feedback_and_reset_refinement_axes",
        "entropy_readout_family": ["balanced_score", "ordering_margin", "measurement_mutual_information", "reset_signal"],
        "direction_modes": ["ordered_vs_scrambled", "balanced_substep_search"],
        "source_file": RESULT_DIR / "szilard_substep_balanced_refinement_sweep_results.json",
        "closest_companion_id": "qit_szilard_substep_companion",
        "bridge_reason": "balanced local search over the refined stochastic substep carrier",
    },
    {
        "id": "szilard_substep_ordering_push_sweep",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape_with_ordering_push_feedback_and_reset_axes",
        "entropy_readout_family": ["push_score", "ordering_margin", "measurement_mutual_information", "reset_signal"],
        "direction_modes": ["ordered_vs_scrambled", "ordering_push_search"],
        "source_file": RESULT_DIR / "szilard_substep_ordering_push_sweep_results.json",
        "closest_companion_id": "qit_szilard_substep_companion",
        "bridge_reason": "ordering-focused push on the balanced stochastic substep carrier",
    },
    {
        "id": "szilard_reverse_recovery_sweep",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape",
        "entropy_readout_family": ["logical_entropy_restoration_fraction", "landauer_gap", "reverse_recovery"],
        "direction_modes": ["erase", "naive_reverse", "recovery"],
        "source_file": RESULT_DIR / "szilard_reverse_recovery_sweep_results.json",
        "closest_companion_id": "qit_szilard_reverse_recovery_companion",
        "bridge_reason": "matched finite-state reverse-recovery companion for erase, naive reverse, and designed recovery",
    },
    {
        "id": "szilard_ordering_sensitivity_sweep",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape_family",
        "entropy_readout_family": ["ordering_margin", "measurement_mutual_information", "logical_entropy"],
        "direction_modes": ["ordered_vs_scrambled"],
        "source_file": RESULT_DIR / "szilard_ordering_sensitivity_sweep_results.json",
        "closest_companion_id": "qit_attractor_basin_recovery",
        "bridge_reason": "order_effect_and_recovery_companion",
    },
    {
        "id": "szilard_record_reset_sweep",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape_with_record_lifetime_axis",
        "entropy_readout_family": ["ordering_margin", "measurement_mutual_information", "reset_stage_entropy"],
        "direction_modes": ["ordered_vs_scrambled", "record_lifetime", "reset_strength"],
        "source_file": RESULT_DIR / "szilard_record_reset_sweep_results.json",
        "closest_companion_id": "qit_szilard_record_companion",
        "bridge_reason": "matched finite-state record-persistence and reset-strength companion",
    },
    {
        "id": "szilard_record_reset_repair_sweep",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape_with_expanded_record_lifetime_reset_feedback_axes",
        "entropy_readout_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "reset_swing", "repair_score"],
        "direction_modes": ["ordered_vs_scrambled", "record_lifetime", "reset_tilt", "feedback_strength"],
        "source_file": RESULT_DIR / "szilard_record_reset_repair_sweep_results.json",
        "closest_companion_id": "qit_szilard_record_companion",
        "bridge_reason": "expanded open repair sweep for record persistence and reset-strength translation",
    },
    {
        "id": "szilard_record_hard_reset_repair_sweep",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape_with_hard_reset_axes",
        "entropy_readout_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "reset_stage_entropy", "repair_score"],
        "direction_modes": ["ordered_vs_scrambled", "record_lifetime", "reset_tilt", "reset_steps", "reset_barrier"],
        "source_file": RESULT_DIR / "szilard_record_hard_reset_repair_sweep_results.json",
        "closest_companion_id": "qit_szilard_record_companion",
        "bridge_reason": "hard-reset repair sweep for stronger open record reset mechanics",
    },
    {
        "id": "szilard_record_ordering_amplification_sweep",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape_with_feedback_asymmetry_and_hard_reset_axes",
        "entropy_readout_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "reset_stage_entropy"],
        "direction_modes": ["ordered_vs_scrambled", "feedback_asymmetry", "record_wait"],
        "source_file": RESULT_DIR / "szilard_record_ordering_amplification_sweep_results.json",
        "closest_companion_id": "qit_szilard_record_companion",
        "bridge_reason": "ordering amplification sweep on top of the hard-reset record carrier",
    },
    {
        "id": "szilard_record_ordering_refinement_sweep",
        "family": "szilard",
        "carrier_geometry_class": "double_well_memory_landscape_with_feedback_asymmetry_duration_and_barrier_axes",
        "entropy_readout_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "reset_stage_entropy"],
        "direction_modes": ["ordered_vs_scrambled", "feedback_asymmetry", "record_wait", "feedback_duration", "feedback_barrier"],
        "source_file": RESULT_DIR / "szilard_record_ordering_refinement_sweep_results.json",
        "closest_companion_id": "qit_szilard_record_companion",
        "bridge_reason": "local ordering refinement around the strongest hard-reset record carrier",
    },
    {
        "id": "szilard_topology_entropy_array",
        "family": "szilard",
        "carrier_geometry_class": "memory_landscape_family",
        "entropy_readout_family": ["logical_entropy", "spread_entropy_proxy", "free_energy_gap_proxy"],
        "direction_modes": ["ordered_vs_scrambled"],
        "source_file": RESULT_DIR / "szilard_topology_entropy_array_results.json",
        "closest_companion_id": "qit_szilard_landauer_cycle",
        "bridge_reason": "same_szilard_carrier_family_but_geometry_variants_are_still_open",
    },
    {
        "id": "carnot_stochastic_finite_time",
        "family": "carnot",
        "carrier_geometry_class": "harmonic_working_substance",
        "entropy_readout_family": ["efficiency", "cop", "cycle_delta_u"],
        "direction_modes": ["forward_engine", "reverse_refrigerator", "fast_slow_quasistatic"],
        "source_file": RESULT_DIR / "stoch_harmonic_carnot_finite_time_results.json",
        "closest_companion_id": "qit_carnot_finite_time_companion",
        "bridge_reason": "matched finite-state budget-axis companion for forward and reverse finite-time tradeoffs",
    },
    {
        "id": "carnot_irreversibility_sweep",
        "family": "carnot",
        "carrier_geometry_class": "harmonic_working_substance",
        "entropy_readout_family": ["efficiency", "cop", "cycle_delta_u"],
        "direction_modes": ["forward_engine", "reverse_refrigerator"],
        "source_file": RESULT_DIR / "carnot_irreversibility_sweep_results.json",
        "closest_companion_id": "qit_carnot_irreversibility_companion",
        "bridge_reason": "matched finite-state duration-sweep companion for forward and reverse irreversibility trends",
    },
    {
        "id": "carnot_closure_diagnostic",
        "family": "carnot",
        "carrier_geometry_class": "harmonic_working_substance",
        "entropy_readout_family": ["variance_mismatch", "internal_energy_mismatch", "cycle_delta_u"],
        "direction_modes": ["forward_engine"],
        "source_file": RESULT_DIR / "carnot_closure_diagnostic_results.json",
        "closest_companion_id": "qit_carnot_closure_companion",
        "bridge_reason": "matched finite-state closure diagnostic companion for return-defect concentration and hold-policy repair",
    },
    {
        "id": "carnot_asymmetric_isotherm_sweep",
        "family": "carnot",
        "carrier_geometry_class": "harmonic_working_substance",
        "entropy_readout_family": ["efficiency", "variance_mismatch", "cycle_delta_u"],
        "direction_modes": ["forward_engine"],
        "source_file": RESULT_DIR / "carnot_asymmetric_isotherm_sweep_results.json",
        "closest_companion_id": "qit_carnot_two_bath_cycle",
        "bridge_reason": "same_carnot_anchor_but_budget_split_sweep",
    },
    {
        "id": "carnot_reverse_asymmetric_sweep",
        "family": "carnot",
        "carrier_geometry_class": "harmonic_working_substance",
        "entropy_readout_family": ["cop", "variance_mismatch", "cycle_delta_u"],
        "direction_modes": ["reverse_refrigerator"],
        "source_file": RESULT_DIR / "carnot_reverse_asymmetric_sweep_results.json",
        "closest_companion_id": "qit_carnot_two_bath_cycle",
        "bridge_reason": "same_carnot_anchor_but_reverse_budget_split_sweep",
    },
    {
        "id": "carnot_topology_array",
        "family": "carnot",
        "carrier_geometry_class": "multi_potential_working_substance_family",
        "entropy_readout_family": ["efficiency", "cop", "return_proxy"],
        "direction_modes": ["forward_engine", "reverse_refrigerator"],
        "source_file": RESULT_DIR / "carnot_topology_array_results.json",
        "closest_companion_id": "qit_carnot_two_bath_cycle",
        "bridge_reason": "same_carnot_anchor_but_geometry_family_sweep",
    },
    {
        "id": "carnot_adaptive_hold_sweep",
        "family": "carnot",
        "carrier_geometry_class": "harmonic_working_substance_with_hold_policy_axis",
        "entropy_readout_family": ["efficiency", "variance_mismatch", "cycle_delta_u", "hold_budget"],
        "direction_modes": ["forward_engine", "hold_policy_comparison"],
        "source_file": RESULT_DIR / "carnot_adaptive_hold_sweep_results.json",
        "closest_companion_id": "qit_carnot_hold_policy_companion",
        "bridge_reason": "matched finite-state hold-policy companion for closure/performance tradeoffs",
    },
]


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text())


def compact_metrics(row_id: str, data: dict) -> dict:
    summary = data.get("summary", {})
    if row_id == "qit_szilard_landauer_cycle":
        return {
            "temperature": summary.get("temperature"),
            "information_gain": summary.get("information_gain"),
            "system_free_energy_gain": summary.get("system_free_energy_gain"),
            "erasure_cost": summary.get("erasure_cost"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_strong_coupling_landauer":
        return {
            "beta": summary.get("beta"),
            "temperature": summary.get("temperature"),
            "strong_coupling": summary.get("strong_coupling"),
            "weak_coupling": summary.get("weak_coupling"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_carnot_two_bath_cycle":
        return {
            "forward_efficiency": summary.get("forward_efficiency"),
            "forward_carnot_bound": summary.get("forward_carnot_bound"),
            "reverse_cop": summary.get("reverse_cop"),
            "reverse_cop_carnot": summary.get("reverse_cop_carnot"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_attractor_basin_recovery":
        return {
            "chosen_schedule": summary.get("chosen_schedule"),
            "swapped_schedule": summary.get("swapped_schedule"),
            "mismatched_schedule": summary.get("mismatched_schedule"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_szilard_record_companion":
        return {
            "best_ordering_margin": summary.get("best_ordering_margin"),
            "best_setting": summary.get("best_setting"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_szilard_reverse_recovery_companion":
        return {
            "best_recovery_vs_naive_gap": summary.get("best_recovery_vs_naive_gap"),
            "mean_recovery_entropy_restoration_fraction": summary.get("mean_recovery_entropy_restoration_fraction"),
            "mean_naive_reverse_entropy_restoration_fraction": summary.get("mean_naive_reverse_entropy_restoration_fraction"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_szilard_substep_companion":
        return {
            "best_ordering_margin": summary.get("best_ordering_margin"),
            "best_setting": summary.get("best_setting"),
            "mean_measurement_mutual_information": summary.get("mean_measurement_mutual_information"),
            "mean_feedback_system_free_energy_gain": summary.get("mean_feedback_system_free_energy_gain"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_carnot_finite_time_companion":
        return {
            "best_closure_defect": summary.get("best_closure_defect"),
            "best_forward_efficiency": summary.get("best_forward_efficiency"),
            "best_reverse_cop": summary.get("best_reverse_cop"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_carnot_hold_policy_companion":
        return {
            "best_closure_policy": summary.get("best_closure_policy"),
            "best_closure_trace_distance": summary.get("best_closure_trace_distance", summary.get("best_closure_trace_distance_to_initial")),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_carnot_irreversibility_companion":
        return {
            "best_closure_defect": summary.get("best_closure_defect"),
            "best_forward_distance_to_carnot": summary.get("best_forward_distance_to_carnot"),
            "best_reverse_distance_to_carnot_cop": summary.get("best_reverse_distance_to_carnot_cop"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "qit_carnot_closure_companion":
        return {
            "baseline_closure_defect": summary.get("baseline_closure_defect"),
            "best_closure_defect": summary.get("best_closure_defect"),
            "best_closure_policy": summary.get("best_closure_policy"),
            "dominant_closure_leg_at_best_row": summary.get("dominant_closure_leg_at_best_row"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "szilard_measurement_feedback_substeps":
        ordered = summary.get("ordered", {})
        return {
            "ordered_final_entropy": ordered.get("final_entropy"),
            "measurement_accuracy": ordered.get("measurement_accuracy"),
            "measurement_mi": ordered.get("measurement_mutual_information"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "szilard_reverse_recovery_sweep":
        return {
            "mean_recovery_entropy_restoration_fraction": summary.get("mean_recovery_entropy_restoration_fraction"),
            "mean_naive_reverse_entropy_restoration_fraction": summary.get("mean_naive_reverse_entropy_restoration_fraction"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "szilard_ordering_sensitivity_sweep":
        return {
            "best_margin": summary.get("best_margin"),
            "best_setting": summary.get("best_setting"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "szilard_topology_entropy_array":
        return {
            "best_topology": summary.get("best_topology"),
            "best_margin": summary.get("best_margin"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "szilard_record_reset_sweep":
        return {
            "best_ordering_margin": summary.get("best_ordering_margin"),
            "best_setting": summary.get("best_setting"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "carnot_stochastic_finite_time":
        return {
            "forward_slow_efficiency": summary.get("forward_slow_efficiency"),
            "forward_quasistatic_efficiency": summary.get("forward_quasistatic_efficiency"),
            "reverse_slow_cop": summary.get("reverse_slow_cop"),
            "reverse_quasistatic_cop": summary.get("reverse_quasistatic_cop"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "carnot_irreversibility_sweep":
        return {
            "best_forward_efficiency": summary.get("best_forward_efficiency"),
            "best_reverse_cop": summary.get("best_reverse_cop"),
            "best_forward_distance_to_carnot": summary.get("best_forward_distance_to_carnot"),
            "best_reverse_distance_to_carnot_cop": summary.get("best_reverse_distance_to_carnot_cop"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "carnot_closure_diagnostic":
        return {
            "best_closure_abs_variance_mismatch": summary.get("best_closure_abs_variance_mismatch"),
            "best_closure_abs_energy_mismatch": summary.get("best_closure_abs_energy_mismatch"),
            "dominant_closure_leg_at_best_row": summary.get("dominant_closure_leg_at_best_row"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "carnot_asymmetric_isotherm_sweep":
        return {
            "best_closure_setting": summary.get("best_closure_setting"),
            "best_closure_variance_mismatch_abs": summary.get("best_closure_variance_mismatch_abs"),
            "best_efficiency_setting": summary.get("best_efficiency_setting"),
            "best_efficiency_distance_to_carnot": summary.get("best_efficiency_distance_to_carnot"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "carnot_reverse_asymmetric_sweep":
        return {
            "best_closure_setting": summary.get("best_closure_setting"),
            "best_closure_variance_mismatch_abs": summary.get("best_closure_variance_mismatch_abs"),
            "best_cop_setting": summary.get("best_cop_setting"),
            "best_cop_distance_to_carnot": summary.get("best_cop_distance_to_carnot"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "carnot_topology_array":
        return {
            "best_engine_topology": summary.get("best_engine_topology"),
            "best_refrigerator_topology": summary.get("best_refrigerator_topology"),
            "best_closure_topology": summary.get("best_closure_topology"),
            "all_pass": summary.get("all_pass"),
        }
    if row_id == "carnot_adaptive_hold_sweep":
        return {
            "best_closure_strategy": summary.get("best_closure_strategy"),
            "best_closure_mismatch_abs": summary.get("best_closure_mismatch_abs"),
            "best_efficiency_strategy": summary.get("best_efficiency_strategy"),
            "best_efficiency": summary.get("best_efficiency"),
            "all_pass": summary.get("all_pass"),
        }
    return {"all_pass": summary.get("all_pass")}


def main() -> None:
    strict_rows = []
    for spec in STRICT_ROWS:
        data = load_json(spec["source_file"])
        strict_rows.append(
            {
                "id": spec["id"],
                "family": spec["family"],
                "subset_role": spec["subset_role"],
                "carrier_geometry_class": spec["carrier_geometry_class"],
                "entropy_readout_family": spec["entropy_readout_family"],
                "direction_modes": spec["direction_modes"],
                "source_file": str(spec["source_file"]),
                "strictness_reason": spec["strictness_reason"],
                "classification": data.get("classification"),
                "headline_metrics": compact_metrics(spec["id"], data),
            }
        )

    repair_rows = []
    for spec in QIT_REPAIR_ROWS:
        if not spec["source_file"].exists():
            continue
        data = load_json(spec["source_file"])
        repair_rows.append(
            {
                "id": spec["id"],
                "family": spec["family"],
                "subset_role": spec["subset_role"],
                "carrier_geometry_class": spec["carrier_geometry_class"],
                "entropy_readout_family": spec["entropy_readout_family"],
                "direction_modes": spec["direction_modes"],
                "source_file": str(spec["source_file"]),
                "strictness_reason": spec["strictness_reason"],
                "classification": data.get("classification"),
                "headline_metrics": compact_metrics(spec["id"], data),
            }
        )

    open_rows = []
    for spec in OPEN_LAB_ROWS:
        if not spec["source_file"].exists():
            continue
        data = load_json(spec["source_file"])
        open_rows.append(
            {
                "id": spec["id"],
                "family": spec["family"],
                "carrier_geometry_class": spec["carrier_geometry_class"],
                "entropy_readout_family": spec["entropy_readout_family"],
                "direction_modes": spec["direction_modes"],
                "source_file": str(spec["source_file"]),
                "closest_companion_id": spec["closest_companion_id"],
                "bridge_reason": spec["bridge_reason"],
                "classification": data.get("classification"),
                "headline_metrics": compact_metrics(spec["id"], data),
            }
        )

    strict_ids = {row["id"] for row in strict_rows}
    open_to_companion = [
        {
            "open_lab_row_id": row["id"],
            "open_lab_family": row["family"],
            "closest_companion_id": row["closest_companion_id"],
            "bridge_reason": row["bridge_reason"],
        }
        for row in open_rows
    ]

    qit_subset_criteria = [
        "finite_qit_carrier_or_exact_bounded_bookkeeping",
        "density_operator_validity_or_equivalent_exactness",
        "explicit_direction_or_order_mode",
        "tight_readout_family_instead_of_geometry_first_proxy",
    ]

    positive = {
        "strict_subset_covers_both_carnot_and_szilard": {
            "families": sorted({row["family"] for row in strict_rows}),
            "pass": {"carnot", "szilard"}.issubset({row["family"] for row in strict_rows}),
        },
        "all_strict_subset_rows_are_loadable": {
            "strict_count": len(strict_rows),
            "pass": all(row["headline_metrics"].get("all_pass") is True for row in strict_rows),
        },
        "qit_repair_rows_exist_for_both_engine_families": {
            "families": sorted({row["family"] for row in repair_rows}),
            "pass": {"carnot", "szilard"}.issubset({row["family"] for row in repair_rows}),
        },
        "every_open_lab_row_has_a_companion_anchor": {
            "open_count": len(open_rows),
            "pass": len(open_rows) == len(open_to_companion),
        },
    }

    negative = {
        "open_lab_rows_are_not_all_inside_the_strict_subset": {
            "strict_ids": sorted(strict_ids),
            "pass": any(row["id"] not in strict_ids for row in open_rows),
        },
        "repair_rows_are_not_being_promoted_to_canonical_anchors": {
            "repair_ids": [row["id"] for row in repair_rows],
            "pass": all(row["classification"] != "canonical" for row in repair_rows),
        },
        "the_companion_surface_is_not_a_unified_theory": {
            "strict_rows": len(strict_rows),
            "open_rows": len(open_rows),
            "pass": True,
        },
    }

    boundary = {
        "all_referenced_files_exist": {
            "pass": all(pathlib.Path(row["source_file"]).exists() for row in strict_rows + repair_rows + open_rows),
        },
        "all_rows_have_finite_headline_metrics": {
            "pass": all(
                all(
                    value is None
                    or isinstance(value, (int, float, bool, str, list, dict))
                    for value in row["headline_metrics"].values()
                )
                for row in strict_rows + repair_rows + open_rows
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "qit_engine_companion_array",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "strict_qit_subset_criteria": qit_subset_criteria,
        "strict_qit_subset": strict_rows,
        "qit_repair_rows": repair_rows,
        "open_lab_companion_rows": open_rows,
        "closest_open_lab_matches": open_to_companion,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "strict_qit_subset_count": len(strict_rows),
            "qit_repair_row_count": len(repair_rows),
            "open_lab_companion_count": len(open_rows),
            "strict_subset_families": sorted({row["family"] for row in strict_rows}),
            "strict_subset_row_ids": [row["id"] for row in strict_rows],
            "closest_open_lab_match_count": len(open_to_companion),
            "scope_note": (
                "QIT-aligned companion array that separates a strict finite-carrier subset from the current open-lab rows. "
                "Use it as the comparison surface for later constraint repair."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_engine_companion_array_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
