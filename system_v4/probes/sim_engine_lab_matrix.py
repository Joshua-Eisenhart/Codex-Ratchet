#!/usr/bin/env python3
"""
Engine Lab Matrix
=================
Collect current Carnot and Szilard engine rows into one comparable array.

This is not a proof surface. It is a controller-facing lab index that makes it
easier to see:
- which rows exist and run
- what level they occupy
- what topology/geometry they use
- what entropy/readout family they use
- whether they look likely admissible, open, or likely out-of-bounds relative
  to the repo's tighter QIT-first constraint discipline
"""

from __future__ import annotations

import json
import pathlib


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Controller-facing engine-lab matrix over Carnot and Szilard rows. "
    "It organizes exact rows, stochastic rows, topology sweeps, and entropy/"
    "readout variants into one comparable surface."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "landauer_erasure",
    "carnot_cycle",
]

PRIMARY_LEGO_IDS = [
    "stochastic_thermodynamics",
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


ROW_SPECS = [
    {
        "id": "szilard_qit_exact",
        "engine_family": "szilard",
        "level": "exact_qit_bookkeeping",
        "geometry_topology": "two_qubit_system_memory",
        "entropy_family": ["von_neumann", "mutual_information", "free_energy"],
        "direction_modes": ["forward"],
        "result_file": RESULT_DIR / "qit_szilard_landauer_cycle_results.json",
        "scope_hint": "narrow_qit_owner_row",
    },
    {
        "id": "szilard_substeps",
        "engine_family": "szilard",
        "level": "stochastic_submechanics",
        "geometry_topology": "double_well_memory",
        "entropy_family": ["logical_bit_entropy", "measurement_mutual_information", "work_heat_bookkeeping"],
        "direction_modes": ["ordered", "scrambled_controls"],
        "result_file": RESULT_DIR / "szilard_measurement_feedback_substeps_results.json",
        "scope_hint": "stochastic_sidecar",
    },
    {
        "id": "szilard_substep_refinement_sweep",
        "engine_family": "szilard",
        "level": "stochastic_submechanics",
        "geometry_topology": "double_well_memory_with_feedback_and_reset_refinement_axes",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "reset_signal", "blind_control_gap"],
        "direction_modes": ["ordered_vs_scrambled", "feedback_strength", "feedback_duration", "reset_strength"],
        "result_file": RESULT_DIR / "szilard_substep_refinement_sweep_results.json",
        "scope_hint": "stochastic_sidecar",
    },
    {
        "id": "szilard_substep_balanced_refinement_sweep",
        "engine_family": "szilard",
        "level": "stochastic_submechanics",
        "geometry_topology": "double_well_memory_with_balanced_feedback_and_reset_refinement_axes",
        "entropy_family": ["balanced_score", "ordering_margin", "measurement_mutual_information", "reset_signal"],
        "direction_modes": ["ordered_vs_scrambled", "balanced_substep_search"],
        "result_file": RESULT_DIR / "szilard_substep_balanced_refinement_sweep_results.json",
        "scope_hint": "stochastic_sidecar",
    },
    {
        "id": "szilard_substep_ordering_push_sweep",
        "engine_family": "szilard",
        "level": "stochastic_submechanics",
        "geometry_topology": "double_well_memory_with_ordering_push_feedback_and_reset_axes",
        "entropy_family": ["push_score", "ordering_margin", "measurement_mutual_information", "reset_signal"],
        "direction_modes": ["ordered_vs_scrambled", "ordering_push_search"],
        "result_file": RESULT_DIR / "szilard_substep_ordering_push_sweep_results.json",
        "scope_hint": "stochastic_sidecar",
    },
    {
        "id": "qit_szilard_substep_companion",
        "engine_family": "szilard",
        "level": "qit_repair_companion",
        "geometry_topology": "finite_two_qubit_memory_with_hold_decay",
        "entropy_family": ["final_joint_entropy", "measurement_mutual_information", "reset_memory_entropy", "hold_decay"],
        "direction_modes": ["ordered_vs_scrambled", "measurement_feedback_reset_hold"],
        "result_file": RESULT_DIR / "qit_szilard_substep_companion_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_szilard_substep_translation_lane",
        "engine_family": "szilard",
        "level": "qit_translation_lane",
        "geometry_topology": "open_double_well_to_finite_substep_translation",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "feedback_signal", "reset_signal", "translation_gap"],
        "direction_modes": ["ordered_vs_scrambled", "measurement_feedback_reset_translation"],
        "result_file": RESULT_DIR / "qit_szilard_substep_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_szilard_substep_refinement_translation_lane",
        "engine_family": "szilard",
        "level": "qit_translation_lane",
        "geometry_topology": "refined_open_double_well_to_finite_substep_translation",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "measurement_accuracy", "reset_signal", "translation_gap"],
        "direction_modes": ["ordered_vs_scrambled", "substep_refinement_translation"],
        "result_file": RESULT_DIR / "qit_szilard_substep_refinement_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_szilard_substep_balanced_translation_lane",
        "engine_family": "szilard",
        "level": "qit_translation_lane",
        "geometry_topology": "balanced_open_double_well_to_finite_substep_translation",
        "entropy_family": ["balanced_score", "ordering_margin", "measurement_mutual_information", "reset_signal", "translation_gap"],
        "direction_modes": ["balanced_substep_translation"],
        "result_file": RESULT_DIR / "qit_szilard_substep_balanced_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_szilard_substep_ordering_push_translation_lane",
        "engine_family": "szilard",
        "level": "qit_translation_lane",
        "geometry_topology": "ordering_push_open_double_well_to_finite_substep_translation",
        "entropy_family": ["push_score", "ordering_margin", "measurement_mutual_information", "reset_signal", "translation_gap"],
        "direction_modes": ["ordering_push_translation"],
        "result_file": RESULT_DIR / "qit_szilard_substep_ordering_push_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "szilard_reverse_recovery",
        "engine_family": "szilard",
        "level": "stochastic_forward_reverse",
        "geometry_topology": "double_well_memory",
        "entropy_family": ["logical_bit_entropy", "landauer_gap", "restoration_fraction"],
        "direction_modes": ["erase", "naive_reverse", "recovery"],
        "result_file": RESULT_DIR / "szilard_reverse_recovery_sweep_results.json",
        "scope_hint": "stochastic_sidecar",
    },
    {
        "id": "qit_szilard_reverse_recovery_companion",
        "engine_family": "szilard",
        "level": "qit_repair_companion",
        "geometry_topology": "finite_two_qubit_memory_reverse_recovery_axis",
        "entropy_family": ["entropy_restoration_fraction", "restoration_trace_distance", "system_free_energy_gain"],
        "direction_modes": ["erase", "naive_reverse", "recovery"],
        "result_file": RESULT_DIR / "qit_szilard_reverse_recovery_companion_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_szilard_reverse_translation_lane",
        "engine_family": "szilard",
        "level": "qit_translation_lane",
        "geometry_topology": "finite_two_qubit_memory_bidirectional_reverse_translation",
        "entropy_family": ["information_gain", "erasure_cost", "entropy_restoration_fraction", "translation_gap"],
        "direction_modes": ["forward", "naive_reverse", "recovery"],
        "result_file": RESULT_DIR / "qit_szilard_reverse_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "szilard_ordering_sensitivity",
        "engine_family": "szilard",
        "level": "parameter_array",
        "geometry_topology": "double_well_memory_family",
        "entropy_family": ["logical_bit_entropy", "measurement_mutual_information", "ordering_margin"],
        "direction_modes": ["ordered_vs_scrambled"],
        "result_file": RESULT_DIR / "szilard_ordering_sensitivity_sweep_results.json",
        "scope_hint": "parameter_map",
    },
    {
        "id": "szilard_record_reset_sweep",
        "engine_family": "szilard",
        "level": "record_reset_array",
        "geometry_topology": "double_well_memory_with_record_lifetime_axis",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "reset_stage_entropy"],
        "direction_modes": ["ordered_vs_scrambled", "record_lifetime", "reset_strength"],
        "result_file": RESULT_DIR / "szilard_record_reset_sweep_results.json",
        "scope_hint": "parameter_map",
    },
    {
        "id": "szilard_record_reset_repair_sweep",
        "engine_family": "szilard",
        "level": "record_reset_array",
        "geometry_topology": "double_well_memory_with_expanded_record_reset_repair_axis",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "reset_swing", "repair_score"],
        "direction_modes": ["ordered_vs_scrambled", "record_lifetime", "reset_tilt", "feedback_strength"],
        "result_file": RESULT_DIR / "szilard_record_reset_repair_sweep_results.json",
        "scope_hint": "parameter_map",
    },
    {
        "id": "szilard_record_hard_reset_repair_sweep",
        "engine_family": "szilard",
        "level": "record_reset_array",
        "geometry_topology": "double_well_memory_with_hard_reset_axes",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "reset_stage_entropy", "repair_score"],
        "direction_modes": ["ordered_vs_scrambled", "record_lifetime", "reset_tilt", "reset_steps", "reset_barrier"],
        "result_file": RESULT_DIR / "szilard_record_hard_reset_repair_sweep_results.json",
        "scope_hint": "parameter_map",
    },
    {
        "id": "szilard_record_ordering_amplification_sweep",
        "engine_family": "szilard",
        "level": "record_reset_array",
        "geometry_topology": "double_well_memory_with_hard_reset_and_feedback_asymmetry_axes",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "reset_stage_entropy"],
        "direction_modes": ["ordered_vs_scrambled", "feedback_asymmetry", "record_wait"],
        "result_file": RESULT_DIR / "szilard_record_ordering_amplification_sweep_results.json",
        "scope_hint": "parameter_map",
    },
    {
        "id": "szilard_record_ordering_refinement_sweep",
        "engine_family": "szilard",
        "level": "record_reset_array",
        "geometry_topology": "double_well_memory_with_hard_reset_feedback_asymmetry_duration_and_barrier_axes",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "reset_stage_entropy"],
        "direction_modes": ["ordered_vs_scrambled", "feedback_asymmetry", "record_wait", "feedback_duration", "feedback_barrier"],
        "result_file": RESULT_DIR / "szilard_record_ordering_refinement_sweep_results.json",
        "scope_hint": "parameter_map",
    },
    {
        "id": "qit_szilard_record_companion",
        "engine_family": "szilard",
        "level": "qit_repair_companion",
        "geometry_topology": "finite_two_qubit_memory_with_record_decay_axis",
        "entropy_family": ["final_joint_entropy", "measurement_mutual_information", "reset_memory_entropy"],
        "direction_modes": ["ordered_vs_scrambled", "record_lifetime", "reset_strength"],
        "result_file": RESULT_DIR / "qit_szilard_record_companion_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_szilard_record_translation_lane",
        "engine_family": "szilard",
        "level": "qit_translation_lane",
        "geometry_topology": "open_record_reset_to_finite_record_decay_translation",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "reset_swing", "translation_gap"],
        "direction_modes": ["ordered_vs_scrambled", "record_lifetime_translation", "reset_axis_translation"],
        "result_file": RESULT_DIR / "qit_szilard_record_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_szilard_record_repair_translation_lane",
        "engine_family": "szilard",
        "level": "qit_translation_lane",
        "geometry_topology": "expanded_open_record_reset_to_finite_record_decay_translation",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "reset_swing", "translation_gap"],
        "direction_modes": ["repair_translation", "record_lifetime_translation", "reset_axis_translation"],
        "result_file": RESULT_DIR / "qit_szilard_record_repair_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_szilard_record_hard_reset_translation_lane",
        "engine_family": "szilard",
        "level": "qit_translation_lane",
        "geometry_topology": "hard_reset_open_record_to_finite_record_decay_translation",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "residual_reset_entropy", "translation_gap"],
        "direction_modes": ["hard_reset_translation"],
        "result_file": RESULT_DIR / "qit_szilard_record_hard_reset_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_szilard_record_ordering_translation_lane",
        "engine_family": "szilard",
        "level": "qit_translation_lane",
        "geometry_topology": "hard_reset_open_record_to_finite_record_decay_ordering_translation",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "residual_reset_entropy", "translation_gap"],
        "direction_modes": ["ordering_translation"],
        "result_file": RESULT_DIR / "qit_szilard_record_ordering_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_szilard_record_ordering_refinement_translation_lane",
        "engine_family": "szilard",
        "level": "qit_translation_lane",
        "geometry_topology": "refined_hard_reset_open_record_to_finite_record_decay_ordering_translation",
        "entropy_family": ["ordering_margin", "measurement_mutual_information", "record_survival", "residual_reset_entropy", "translation_gap"],
        "direction_modes": ["ordering_refinement_translation"],
        "result_file": RESULT_DIR / "qit_szilard_record_ordering_refinement_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "carnot_qit_exact",
        "engine_family": "carnot",
        "level": "exact_qit_bookkeeping",
        "geometry_topology": "qubit_working_substance",
        "entropy_family": ["gibbs_entropy", "free_energy", "heat_work_bookkeeping"],
        "direction_modes": ["forward_engine", "reverse_refrigerator"],
        "result_file": RESULT_DIR / "qit_carnot_two_bath_cycle_results.json",
        "scope_hint": "exact_reference_row",
    },
    {
        "id": "carnot_stochastic_finite_time",
        "engine_family": "carnot",
        "level": "stochastic_operational",
        "geometry_topology": "harmonic_working_substance",
        "entropy_family": ["heat_work_bookkeeping", "efficiency", "cop", "cycle_delta_u"],
        "direction_modes": ["forward_engine", "reverse_refrigerator", "fast_slow_quasistatic"],
        "result_file": RESULT_DIR / "stoch_harmonic_carnot_finite_time_results.json",
        "scope_hint": "stochastic_sidecar",
    },
    {
        "id": "qit_carnot_finite_time_companion",
        "engine_family": "carnot",
        "level": "qit_repair_companion",
        "geometry_topology": "finite_qubit_two_bath_with_budget_axis",
        "entropy_family": ["closure_defect", "efficiency", "cop", "carnot_distance", "budget_axis"],
        "direction_modes": ["forward_engine", "reverse_refrigerator", "fast_slow_quasistatic"],
        "result_file": RESULT_DIR / "qit_carnot_finite_time_companion_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_carnot_finite_time_translation_lane",
        "engine_family": "carnot",
        "level": "qit_translation_lane",
        "geometry_topology": "open_stochastic_to_finite_budget_translation",
        "entropy_family": ["closure_defect", "efficiency", "cop", "translation_gap"],
        "direction_modes": ["forward_engine", "reverse_refrigerator", "budget_translation"],
        "result_file": RESULT_DIR / "qit_carnot_finite_time_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "carnot_irreversibility_sweep",
        "engine_family": "carnot",
        "level": "duration_array",
        "geometry_topology": "harmonic_working_substance",
        "entropy_family": ["efficiency", "cop", "cycle_delta_u"],
        "direction_modes": ["forward_engine", "reverse_refrigerator"],
        "result_file": RESULT_DIR / "carnot_irreversibility_sweep_results.json",
        "scope_hint": "parameter_map",
    },
    {
        "id": "qit_carnot_irreversibility_companion",
        "engine_family": "carnot",
        "level": "qit_repair_companion",
        "geometry_topology": "finite_qubit_two_bath_duration_sweep",
        "entropy_family": ["closure_defect", "efficiency", "cop", "carnot_distance", "duration_sweep"],
        "direction_modes": ["forward_engine", "reverse_refrigerator", "duration_sweep"],
        "result_file": RESULT_DIR / "qit_carnot_irreversibility_companion_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_carnot_irreversibility_translation_lane",
        "engine_family": "carnot",
        "level": "qit_translation_lane",
        "geometry_topology": "open_duration_to_finite_duration_translation",
        "entropy_family": ["carnot_distance", "efficiency", "cop", "translation_gap"],
        "direction_modes": ["forward_engine", "reverse_refrigerator", "duration_translation"],
        "result_file": RESULT_DIR / "qit_carnot_irreversibility_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "carnot_closure_diagnostic",
        "engine_family": "carnot",
        "level": "diagnostic_array",
        "geometry_topology": "harmonic_working_substance",
        "entropy_family": ["internal_energy_gap", "variance_mismatch", "cycle_delta_u"],
        "direction_modes": ["forward_engine"],
        "result_file": RESULT_DIR / "carnot_closure_diagnostic_results.json",
        "scope_hint": "diagnostic",
    },
    {
        "id": "qit_carnot_closure_companion",
        "engine_family": "carnot",
        "level": "qit_repair_companion",
        "geometry_topology": "finite_qubit_two_bath_closure_grid",
        "entropy_family": ["closure_defect", "closure_leg_concentration", "hold_policy_tradeoff"],
        "direction_modes": ["forward_engine", "closure_diagnostic", "hold_policy"],
        "result_file": RESULT_DIR / "qit_carnot_closure_companion_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_carnot_closure_translation_lane",
        "engine_family": "carnot",
        "level": "qit_translation_lane",
        "geometry_topology": "open_closure_to_finite_closure_translation",
        "entropy_family": ["closure_defect", "closure_leg_concentration", "translation_gap"],
        "direction_modes": ["forward_engine", "closure_translation"],
        "result_file": RESULT_DIR / "qit_carnot_closure_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "carnot_forward_asymmetric",
        "engine_family": "carnot",
        "level": "topology_budget_array",
        "geometry_topology": "harmonic_working_substance",
        "entropy_family": ["efficiency", "cycle_delta_u", "variance_mismatch"],
        "direction_modes": ["forward_engine"],
        "result_file": RESULT_DIR / "carnot_asymmetric_isotherm_sweep_results.json",
        "scope_hint": "budget_map",
    },
    {
        "id": "carnot_reverse_asymmetric",
        "engine_family": "carnot",
        "level": "topology_budget_array",
        "geometry_topology": "harmonic_working_substance",
        "entropy_family": ["cop", "cycle_delta_u", "variance_mismatch"],
        "direction_modes": ["reverse_refrigerator"],
        "result_file": RESULT_DIR / "carnot_reverse_asymmetric_sweep_results.json",
        "scope_hint": "budget_map",
    },
    {
        "id": "carnot_topology_array",
        "engine_family": "carnot",
        "level": "topology_array",
        "geometry_topology": "multi_potential_family",
        "entropy_family": ["efficiency", "cop", "closure_metrics"],
        "direction_modes": ["forward_engine", "reverse_refrigerator"],
        "result_file": RESULT_DIR / "carnot_topology_array_results.json",
        "scope_hint": "topology_map",
    },
    {
        "id": "carnot_adaptive_hold_sweep",
        "engine_family": "carnot",
        "level": "adaptive_hold_array",
        "geometry_topology": "harmonic_working_substance_with_hold_policy_axis",
        "entropy_family": ["efficiency", "cycle_delta_u", "variance_mismatch", "hold_budget"],
        "direction_modes": ["forward_engine", "hold_policy_comparison"],
        "result_file": RESULT_DIR / "carnot_adaptive_hold_sweep_results.json",
        "scope_hint": "budget_map",
    },
    {
        "id": "qit_carnot_hold_policy_companion",
        "engine_family": "carnot",
        "level": "qit_repair_companion",
        "geometry_topology": "finite_qubit_two_bath_with_hold_policy_axis",
        "entropy_family": ["efficiency", "trace_distance_closure", "hold_budget"],
        "direction_modes": ["forward_engine", "fixed_vs_adaptive_hold_policy"],
        "result_file": RESULT_DIR / "qit_carnot_hold_policy_companion_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "qit_carnot_hold_translation_lane",
        "engine_family": "carnot",
        "level": "qit_translation_lane",
        "geometry_topology": "open_stochastic_to_finite_hold_policy_translation",
        "entropy_family": ["closure_defect", "efficiency", "translation_gap", "hold_policy"],
        "direction_modes": ["forward_engine", "hold_policy_translation"],
        "result_file": RESULT_DIR / "qit_carnot_hold_translation_lane_results.json",
        "scope_hint": "repair_companion",
    },
    {
        "id": "carnot_entropy_family_array",
        "engine_family": "carnot",
        "level": "entropy_family_array",
        "geometry_topology": "cross_level_cross_topology",
        "entropy_family": ["performance", "bath_entropy_proxy", "closure_proxy", "return_proxy"],
        "direction_modes": ["forward_engine", "reverse_refrigerator"],
        "result_file": RESULT_DIR / "carnot_entropy_family_array_results.json",
        "scope_hint": "readout_map",
    },
    {
        "id": "szilard_topology_entropy_array",
        "engine_family": "szilard",
        "level": "topology_entropy_array",
        "geometry_topology": "memory_landscape_family",
        "entropy_family": ["logical_entropy", "information_metrics", "thermo_readouts"],
        "direction_modes": ["ordered_vs_scrambled"],
        "result_file": RESULT_DIR / "szilard_topology_entropy_array_results.json",
        "scope_hint": "topology_map",
    },
    {
        "id": "qit_engine_companion_array",
        "engine_family": "mixed",
        "level": "qit_companion_array",
        "geometry_topology": "finite_qit_anchor_subset",
        "entropy_family": ["anchor_metrics", "family_bridge_mapping"],
        "direction_modes": ["companion_mapping"],
        "result_file": RESULT_DIR / "qit_engine_companion_array_results.json",
        "scope_hint": "companion_map",
    },
    {
        "id": "qit_entropy_companion_array",
        "engine_family": "mixed",
        "level": "qit_entropy_companion_array",
        "geometry_topology": "finite_qit_anchor_subset",
        "entropy_family": ["strict_qit_readouts", "anchor_entropy_families"],
        "direction_modes": ["companion_readouts"],
        "result_file": RESULT_DIR / "qit_entropy_companion_array_results.json",
        "scope_hint": "companion_map",
    },
    {
        "id": "engine_lab_constraint_audit",
        "engine_family": "mixed",
        "level": "constraint_audit_array",
        "geometry_topology": "open_lab_vs_strict_anchor_overlay",
        "entropy_family": ["alignment_route", "strict_anchor_overlap", "repair_priority"],
        "direction_modes": ["constraint_audit"],
        "result_file": RESULT_DIR / "engine_lab_constraint_audit_results.json",
        "scope_hint": "companion_map",
    },
    {
        "id": "engine_lab_repair_priority",
        "engine_family": "mixed",
        "level": "repair_priority_array",
        "geometry_topology": "open_lab_translation_priority_overlay",
        "entropy_family": ["translation_closeness", "priority_bucket", "repair_queue"],
        "direction_modes": ["repair_priority"],
        "result_file": RESULT_DIR / "engine_lab_repair_priority_results.json",
        "scope_hint": "companion_map",
    },
    {
        "id": "engine_lab_translation_targets",
        "engine_family": "mixed",
        "level": "translation_target_array",
        "geometry_topology": "open_lab_to_qit_translation_overlay",
        "entropy_family": ["translation_action", "priority_bucket", "pair_delta_summary"],
        "direction_modes": ["translation_targeting"],
        "result_file": RESULT_DIR / "engine_lab_translation_targets_results.json",
        "scope_hint": "companion_map",
    },
    {
        "id": "qit_repair_comparison_surface",
        "engine_family": "mixed",
        "level": "qit_repair_comparison_surface",
        "geometry_topology": "open_lab_vs_qit_repair_pairs",
        "entropy_family": ["pairwise_delta_metrics", "repair_translation_gap"],
        "direction_modes": ["open_vs_qit_repair"],
        "result_file": RESULT_DIR / "qit_repair_comparison_surface_results.json",
        "scope_hint": "companion_map",
    },
]


def likely_constraint_relation(scope_hint: str, result: dict) -> str:
    classification = result.get("classification", "")
    summary = result.get("summary", {})
    all_pass = summary.get("all_pass")

    if scope_hint == "narrow_qit_owner_row":
        return "likely_allowed_qit_core"
    if scope_hint == "exact_reference_row":
        return "allowed_as_reference_not_runtime"
    if scope_hint == "repair_companion":
        return "qit_aligned_repair_surface"
    if scope_hint in {"stochastic_sidecar", "parameter_map", "diagnostic", "budget_map", "topology_map"}:
        if all_pass is True and classification == "exploratory":
            return "runs_cleanly_but_still_open_against_repo_constraints"
        return "open_or_likely_outside_strict_qit_core"
    if scope_hint == "readout_map":
        return "controller_readout_surface"
    if scope_hint == "companion_map":
        return "qit_alignment_controller_surface"
    return "unknown"


def extract_headline_metrics(row_id: str, result: dict) -> dict:
    summary = result.get("summary", {})
    metrics = {}
    for key in [
        "all_pass",
        "forward_efficiency",
        "forward_carnot_bound",
        "reverse_cop",
        "reverse_cop_carnot",
        "forward_slow_efficiency",
        "forward_quasistatic_efficiency",
        "reverse_slow_cop",
        "reverse_quasistatic_cop",
        "best_margin",
        "best_ordering_margin",
        "best_forward_distance_to_carnot",
        "best_reverse_distance_to_carnot_cop",
        "best_closure_abs_variance_mismatch",
        "best_closure_variance_mismatch_abs",
        "best_closure_mismatch_abs",
        "best_efficiency_distance_to_carnot",
        "best_cop_distance_to_carnot",
        "best_recovery_vs_naive_gap",
        "mean_recovery_entropy_restoration_fraction",
        "mean_naive_reverse_entropy_restoration_fraction",
        "baseline_final_variance_mismatch_abs",
        "best_efficiency",
        "best_closure_trace_distance",
        "best_closure_defect",
        "best_closure_policy",
        "dominant_closure_leg_at_best_row",
        "mean_measurement_accuracy",
        "mean_measurement_mutual_information",
        "mean_feedback_system_free_energy_gain",
        "best_reverse_cop",
        "baseline_forward_closure_defect",
        "baseline_forward_efficiency",
    ]:
        if key in summary:
            metrics[key] = summary[key]
    if row_id == "szilard_substeps":
        ordered = summary.get("ordered", {})
        metrics["ordered_final_entropy"] = ordered.get("final_entropy")
        metrics["ordered_measurement_mi"] = ordered.get("measurement_mutual_information")
    if row_id == "qit_szilard_substep_translation_lane":
        for key in [
            "open_ordering_margin",
            "qit_best_ordering_margin",
            "measurement_mutual_information_gap",
            "feedback_gain_gap",
            "reset_signal_gap",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "szilard_substep_refinement_sweep":
        for key in [
            "best_ordering_margin",
            "best_measurement_mutual_information",
            "best_measurement_accuracy",
            "best_reset_signal",
            "best_blind_control_gap",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "szilard_substep_balanced_refinement_sweep":
        for key in [
            "best_balanced_score",
            "best_ordering_margin",
            "best_measurement_mutual_information",
            "best_measurement_accuracy",
            "best_reset_signal",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "szilard_substep_ordering_push_sweep":
        for key in [
            "best_push_score",
            "best_ordering_margin",
            "best_measurement_mutual_information",
            "best_measurement_accuracy",
            "best_reset_signal",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "qit_szilard_substep_refinement_translation_lane":
        for key in [
            "ordering_margin_gap",
            "measurement_mutual_information_gap",
            "measurement_accuracy_gap",
            "reset_signal_gap",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "qit_szilard_substep_balanced_translation_lane":
        for key in [
            "ordering_margin_gap",
            "measurement_mutual_information_gap",
            "measurement_accuracy_gap",
            "reset_signal_gap",
            "best_balanced_score",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "qit_szilard_substep_ordering_push_translation_lane":
        for key in [
            "ordering_margin_gap",
            "measurement_mutual_information_gap",
            "measurement_accuracy_gap",
            "reset_signal_gap",
            "best_push_score",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "qit_szilard_record_translation_lane":
        for key in [
            "open_best_ordering_margin",
            "qit_best_ordering_margin",
            "measurement_mi_gap",
            "record_survival_gap",
            "reset_swing_gap",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "szilard_record_reset_repair_sweep":
        for key in [
            "best_repair_score",
            "best_ordering_margin",
            "best_measurement_mutual_information",
            "best_record_survival_fraction",
            "open_reset_swing",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "szilard_record_hard_reset_repair_sweep":
        for key in [
            "best_repair_score",
            "best_ordering_margin",
            "best_measurement_mutual_information",
            "best_record_survival_fraction",
            "best_reset_stage_entropy",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "szilard_record_ordering_amplification_sweep":
        for key in [
            "best_ordering_margin",
            "best_measurement_mutual_information",
            "best_record_survival_fraction",
            "best_reset_stage_entropy",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "szilard_record_ordering_refinement_sweep":
        for key in [
            "best_ordering_margin",
            "best_measurement_mutual_information",
            "best_record_survival_fraction",
            "best_reset_stage_entropy",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "qit_szilard_record_repair_translation_lane":
        for key in [
            "best_repair_score",
            "ordering_margin_gap",
            "measurement_mi_gap",
            "record_survival_gap",
            "reset_swing_gap",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "qit_szilard_record_hard_reset_translation_lane":
        for key in [
            "best_repair_score",
            "ordering_margin_gap",
            "measurement_mi_gap",
            "record_survival_gap",
            "residual_reset_entropy_gap",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "qit_szilard_record_ordering_translation_lane":
        for key in [
            "ordering_margin_gap",
            "measurement_mi_gap",
            "record_survival_gap",
            "residual_reset_entropy_gap",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    if row_id == "qit_szilard_record_ordering_refinement_translation_lane":
        for key in [
            "ordering_margin_gap",
            "measurement_mi_gap",
            "record_survival_gap",
            "residual_reset_entropy_gap",
        ]:
            if key in summary:
                metrics[key] = summary[key]
    return metrics


def main() -> None:
    rows = []
    missing = []
    for spec in ROW_SPECS:
        path = spec["result_file"]
        if not path.exists():
            missing.append({"id": spec["id"], "result_file": str(path)})
            continue
        result = json.loads(path.read_text())
        rows.append(
            {
                "id": spec["id"],
                "engine_family": spec["engine_family"],
                "level": spec["level"],
                "geometry_topology": spec["geometry_topology"],
                "entropy_family": spec["entropy_family"],
                "direction_modes": spec["direction_modes"],
                "classification": result.get("classification"),
                "result_file": str(path),
                "likely_constraint_relation": likely_constraint_relation(spec["scope_hint"], result),
                "headline_metrics": extract_headline_metrics(spec["id"], result),
            }
        )

    available_ids = {row["id"] for row in rows}
    summary = {
        "all_pass": True,
        "available_rows": len(rows),
        "missing_rows": len(missing),
        "available_ids": sorted(available_ids),
        "missing_ids": sorted(item["id"] for item in missing),
        "engine_families": sorted(set(row["engine_family"] for row in rows)),
        "levels": sorted(set(row["level"] for row in rows)),
        "constraint_relation_counts": {
            label: sum(row["likely_constraint_relation"] == label for row in rows)
            for label in sorted(set(row["likely_constraint_relation"] for row in rows))
        },
        "scope_note": (
            "Open engine-lab matrix over exact, stochastic, parameter-sweep, and topology-"
            "sweep rows. This surface is for controller comparison, not canonical admission."
        ),
    }

    out = {
        "name": "engine_lab_matrix",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": summary,
        "rows": rows,
        "missing": missing,
    }

    out_path = RESULT_DIR / "engine_lab_matrix_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
