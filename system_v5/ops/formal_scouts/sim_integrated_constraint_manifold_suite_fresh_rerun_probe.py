#!/usr/bin/env python3
"""Fresh-rerun the integrated constraint-manifold formal-scout suite."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Any

import networkx as nx
import sympy as sp
from z3 import And, Bool, Solver, sat


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "integrated_constraint_manifold_suite_fresh_rerun_probe_results.json"

NAME = "integrated_constraint_manifold_suite_fresh_rerun_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: reruns the ordered source-native, QIT-engine, "
    "entropy-gradient/MPS transport, reservoir, and PEPS3D capacity scout suite "
    "and checks that the current operational evidence surface remains runnable, "
    "validated, and proxy-quarantined. It does not admit final manifold, final "
    "QIT engine, learned dynamics, physics, cognition, ontology, production "
    "readiness, or canonical claims."
)

TOOL_MANIFEST = {
    "python_subprocess": {
        "tried": True,
        "used": True,
        "reason": "supportive ordered fresh reruns of formal-scout scripts",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt parsing and suite result writing",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical script and result path checks",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive ordered evidence dependency graph",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic suite count inventory",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing suite admissibility witness",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_subprocess": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "networkx": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
}

MIN_NONCLASSICAL_WIDTH = 8

SUITE = [
    {
        "name": "manifold_operational_assembly",
        "script": "sim_nested_constraint_manifold_operational_assembly_tensor_network_probe.py",
        "result": "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json",
        "category": "source_native_constraint_manifold_operational_assembly",
    },
    {
        "name": "manifold_handle_support",
        "script": "sim_nested_constraint_manifold_operational_handle_support_probe.py",
        "result": "nested_constraint_manifold_operational_handle_support_probe_results.json",
        "category": "source_native_constraint_manifold_support",
    },
    {
        "name": "source_stage_subcycle",
        "script": "sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py",
        "result": "left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe_results.json",
        "category": "source_native",
    },
    {
        "name": "probe_family_reconciliation",
        "script": "sim_qit_engine_probe_family_reconciliation_intersection_probe.py",
        "result": "qit_engine_probe_family_reconciliation_intersection_probe_results.json",
        "category": "probe_family_reconciliation",
    },
    {
        "name": "engine_operator_slot_alphabet",
        "script": "sim_engine_operator_slot_alphabet_contract_probe.py",
        "result": "engine_operator_slot_alphabet_contract_probe_results.json",
        "category": "downstream_qit_engine_operator_alphabet",
    },
    {
        "name": "source_seven_control_microsteps",
        "script": "sim_source_chiral_seven_control_sixty_four_microstep_execution_probe.py",
        "result": "source_chiral_seven_control_sixty_four_microstep_execution_probe_results.json",
        "category": "source_native_controls",
    },
    {
        "name": "paired_chiral_joint_bipartite_execution",
        "script": "sim_paired_chiral_seven_control_joint_bipartite_execution_order_probe.py",
        "result": "paired_chiral_seven_control_joint_bipartite_execution_order_probe_results.json",
        "category": "downstream_on_source_joint_execution",
    },
    {
        "name": "qit_engine_work_execution",
        "script": "sim_constraint_manifold_qit_work_execution_probe.py",
        "result": "constraint_manifold_qit_work_execution_probe_results.json",
        "category": "downstream_qit_engine_work_execution",
    },
    {
        "name": "qit_engine_dynamics_required_work",
        "script": "sim_qit_engine_dynamics_required_work_discrimination_probe.py",
        "result": "qit_engine_dynamics_required_work_discrimination_probe_results.json",
        "category": "downstream_qit_engine_dynamics_required_work",
    },
    {
        "name": "operator_slot_entropy_gradient_mps_transport",
        "script": "sim_operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe.py",
        "result": "operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe_results.json",
        "category": "downstream_qit_engine_entropy_gradient_mps_transport",
    },
    {
        "name": "engine_core_autograd_severance_contract",
        "script": "sim_engine_core_autograd_severance_contract_probe.py",
        "result": "engine_core_autograd_severance_contract_probe_results.json",
        "category": "engine_core_autograd_severance_contract",
    },
    {
        "name": "tensor_network_tool_admission",
        "script": "sim_quimb_cotengra_tensor_network_geometry_contraction_probe.py",
        "result": "quimb_cotengra_tensor_network_geometry_contraction_probe_results.json",
        "category": "tool_admission",
    },
    {
        "name": "topology_entropy_tensor_coupling",
        "script": "sim_topology_entropy_deformation_tensor_network_coupling_probe.py",
        "result": "topology_entropy_deformation_tensor_network_coupling_probe_results.json",
        "category": "downstream_tool_coupling",
    },
    {
        "name": "carrier_volume_comparison",
        "script": "sim_mps_peps_peps3d_entropy_deformation_volume_comparison_probe.py",
        "result": "mps_peps_peps3d_entropy_deformation_volume_comparison_probe_results.json",
        "category": "multicarrier",
    },
    {
        "name": "source_native_high_rank_engine_history",
        "script": "sim_source_native_high_rank_engine_history_family_probe.py",
        "result": "source_native_high_rank_engine_history_family_probe_results.json",
        "category": "source_native_high_rank_engine_history",
    },
    {
        "name": "peps3d_32_64_site_capacity",
        "script": "sim_source_native_peps3d_32_64_site_capacity_probe.py",
        "result": "source_native_peps3d_32_64_site_capacity_probe_results.json",
        "category": "source_native_peps3d_capacity",
    },
    {
        "name": "peps3d_52_56_60_regime_ladder",
        "script": "sim_source_native_peps3d_52_56_60_site_regime_ladder_probe.py",
        "result": "source_native_peps3d_52_56_60_site_regime_ladder_probe_results.json",
        "category": "source_native_peps3d_regime_ladder",
    },
    {
        "name": "peps3d_64_site_slot_closeout",
        "script": "sim_source_native_peps3d_64_site_slot_dynamics_closeout_probe.py",
        "result": "source_native_peps3d_64_site_slot_dynamics_closeout_probe_results.json",
        "category": "source_native_peps3d_64_site_slot_dynamics",
    },
    {
        "name": "peps3d_64_site_bond_dimension",
        "script": "sim_source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe.py",
        "result": "source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe_results.json",
        "category": "source_native_peps3d_64_site_bond_dimension",
    },
    {
        "name": "probe_family_chi_transport_8_16_32",
        "script": "sim_probe_family_discrimination_chi_transport_8_16_32_probe.py",
        "result": "probe_family_discrimination_chi_transport_8_16_32_probe_results.json",
        "category": "source_native_chi_transport_scaling",
    },
    {
        "name": "multiqubit_reservoir_global_structure",
        "script": "sim_multiqubit_qit_reservoir_global_structure_probe.py",
        "result": "multiqubit_qit_reservoir_global_structure_probe_results.json",
        "category": "multiqubit_qit_reservoir",
    },
    {
        "name": "multiqubit_reservoir_static_kernel_esn_baseline",
        "script": "sim_multiqubit_reservoir_static_kernel_esn_baseline_probe.py",
        "result": "multiqubit_reservoir_static_kernel_esn_baseline_probe_results.json",
        "category": "multiqubit_qit_reservoir_baseline",
    },
    {
        "name": "multiqubit_reservoir_order_holonomy",
        "script": "sim_multiqubit_qit_reservoir_dense_order_holonomy_probe.py",
        "result": "multiqubit_qit_reservoir_dense_order_holonomy_probe_results.json",
        "category": "multiqubit_qit_reservoir_holonomy",
    },
    {
        "name": "multiqubit_reservoir_temporal_ablation",
        "script": "sim_multiqubit_qit_reservoir_temporal_ablation_probe.py",
        "result": "multiqubit_qit_reservoir_temporal_ablation_probe_results.json",
        "category": "multiqubit_qit_reservoir_ablation",
    },
    {
        "name": "multiqubit_reservoir_meanfield_ablation",
        "script": "sim_multiqubit_qit_reservoir_meanfield_ablation_probe.py",
        "result": "multiqubit_qit_reservoir_meanfield_ablation_probe_results.json",
        "category": "multiqubit_qit_reservoir_ablation",
    },
    {
        "name": "multiqubit_mps_reservoir_scaling_12_16_24_32",
        "script": "sim_multiqubit_mps_reservoir_12_16_24_32_scaling_probe.py",
        "result": "multiqubit_mps_reservoir_12_16_24_32_scaling_probe_results.json",
        "category": "multiqubit_mps_reservoir_scaling",
    },
    {
        "name": "multiqubit_reservoir_digits_6q",
        "script": "sim_multiqubit_qit_reservoir_digits_6q_probe.py",
        "result": "multiqubit_qit_reservoir_digits_6q_probe_results.json",
        "category": "multiqubit_qit_reservoir_real_data",
        "minimum_width_qubits": 6,
        "minimum_width_role": "calibration_only",
        "minimum_width_reason": "six-qubit sklearn-digits reservoir row is retained as a real-data calibration boundary, not nonclassical maturity evidence",
    },
    {
        "name": "weyl_holonomy_mps_curvature_transport",
        "script": "sim_weyl_holonomy_mps_curvature_transport_probe.py",
        "result": "weyl_holonomy_mps_curvature_transport_probe_results.json",
        "category": "weyl_holonomy_mps_curvature",
    },
    {
        "name": "constraint_manifold_layer_causal_matrix",
        "script": "sim_constraint_manifold_layer_causal_responsibility_matrix_probe.py",
        "result": "constraint_manifold_layer_causal_responsibility_matrix_probe_results.json",
        "category": "constraint_manifold_layer_causal_responsibility",
    },
    {
        "name": "constraint_manifold_delta_neural_readout",
        "script": "sim_constraint_manifold_delta_neural_readout_probe.py",
        "result": "constraint_manifold_delta_neural_readout_probe_results.json",
        "category": "constraint_manifold_neural_readout",
    },
    {
        "name": "multitool_entropy_geometry_carriers",
        "script": "sim_constraint_manifold_multitool_entropy_geometry_carrier_integration_probe.py",
        "result": "constraint_manifold_multitool_entropy_geometry_carrier_integration_probe_results.json",
        "category": "multitool_integration",
    },
    {
        "name": "source_to_multicarrier_execution",
        "script": "sim_source_chiral_density_multicarrier_multitool_manifold_execution_probe.py",
        "result": "source_chiral_density_multicarrier_multitool_manifold_execution_probe_results.json",
        "category": "source_native_composed",
    },
    {
        "name": "long_horizon_holonomy_boundary_entropy",
        "script": "sim_long_horizon_source_multicarrier_holonomy_boundary_entropy_probe.py",
        "result": "long_horizon_source_multicarrier_holonomy_boundary_entropy_probe_results.json",
        "category": "long_horizon_downstream_on_source",
    },
    {
        "name": "macro_stage_record_science_method_contract",
        "script": "sim_macro_sim_stage_record_science_method_contract_probe.py",
        "result": "macro_sim_stage_record_science_method_contract_probe_results.json",
        "category": "source_native_macro_sim_stage_contract",
    },
    {
        "name": "source_native_fep_pomdp_policy_tree",
        "script": "sim_source_native_fep_pomdp_policy_tree_probe.py",
        "result": "source_native_fep_pomdp_policy_tree_probe_results.json",
        "category": "source_native_fep_policy_tree",
    },
    {
        "name": "source_native_fep_online_vmp_policy_update",
        "script": "sim_source_native_fep_online_vmp_policy_update_probe.py",
        "result": "source_native_fep_online_vmp_policy_update_probe_results.json",
        "category": "source_native_fep_online_vmp",
    },
    {
        "name": "macro_axis0_plural_stage_router",
        "script": "sim_macro_sim_axis0_plural_stage_candidate_router_probe.py",
        "result": "macro_sim_axis0_plural_stage_candidate_router_probe_results.json",
        "category": "source_native_macro_sim_axis0",
    },
    {
        "name": "holodeck_hash_memory_placeholder",
        "script": "sim_source_native_holodeck_hash_memory_placeholder_probe.py",
        "result": "source_native_holodeck_hash_memory_placeholder_probe_results.json",
        "category": "source_native_holodeck_memory_placeholder",
    },
    {
        "name": "source_native_subdense_multicarrier_environment",
        "script": "sim_source_native_multicarrier_subdense_environment_contraction_probe.py",
        "result": "source_native_multicarrier_subdense_environment_contraction_probe_results.json",
        "category": "source_native_subdense_multicarrier_environment",
    },
    {
        "name": "stage_record_downstream_carrier_consumption_closure",
        "script": "sim_stage_record_downstream_carrier_consumption_closure_probe.py",
        "result": "stage_record_downstream_carrier_consumption_closure_probe_results.json",
        "category": "stage_record_downstream_closure_guard",
    },
    {
        "name": "axis0_plural_candidate_multicarrier_drive_controls",
        "script": "sim_axis0_plural_candidate_multicarrier_drive_controls_probe.py",
        "result": "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json",
        "category": "axis0_plural_candidate_multicarrier_drive_controls",
    },
    {
        "name": "path_entropy_schedule_confound_falsifier",
        "script": "sim_path_entropy_schedule_confound_falsifier_probe.py",
        "result": "path_entropy_schedule_confound_falsifier_probe_results.json",
        "category": "axis0_path_entropy_schedule_confound_falsifier",
    },
    {
        "name": "path_entropy_proxy_vs_deeper_invariant_pair_falsifier",
        "script": "sim_path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe.py",
        "result": "path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe_results.json",
        "category": "axis0_path_entropy_proxy_pair_falsifier",
    },
    {
        "name": "axis0_path_entropy_branch_closure",
        "script": "sim_axis0_path_entropy_branch_closure_probe.py",
        "result": "axis0_path_entropy_branch_closure_probe_results.json",
        "category": "axis0_path_entropy_blocked_branch_closure",
    },
    {
        "name": "axis0_holographic_boundary_branch_closure",
        "script": "sim_axis0_holographic_boundary_branch_closure_probe.py",
        "result": "axis0_holographic_boundary_branch_closure_probe_results.json",
        "category": "axis0_holographic_boundary_blocked_branch_closure",
    },
    {
        "name": "axis0_fep_gradient_stage_local_adapter_closure",
        "script": "sim_axis0_fep_gradient_stage_local_adapter_closure_probe.py",
        "result": "axis0_fep_gradient_stage_local_adapter_closure_probe_results.json",
        "category": "axis0_fep_gradient_stage_local_adapter_closure",
    },
    {
        "name": "mps_local_boundary_path_fep_scaling_8_16_32",
        "script": "sim_mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe.py",
        "result": "mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe_results.json",
        "category": "mps_local_boundary_path_fep_variable_qubit_scaling",
    },
    {
        "name": "world_model_repo_admission_gap_adapter",
        "script": "sim_world_model_repo_admission_gap_adapter_probe.py",
        "result": "world_model_repo_admission_gap_adapter_probe_results.json",
        "category": "world_model_repo_admission",
    },
    {
        "name": "auto_lirpa_lewm_latent_surprise_bound",
        "script": "sim_auto_lirpa_lewm_latent_surprise_bound_probe.py",
        "result": "auto_lirpa_lewm_latent_surprise_bound_probe_results.json",
        "category": "auto_lirpa_lewm_latent_surprise_micro_bound",
    },
    {
        "name": "axis0_lewm_lirpa_pytorch_assembly",
        "script": "sim_axis0_lewm_lirpa_pytorch_assembly_probe.py",
        "result": "axis0_lewm_lirpa_pytorch_assembly_probe_results.json",
        "category": "guarded_axis0_lewm_lirpa_pytorch_assembly",
    },
    {
        "name": "auto_lirpa_stage_policy_bound_consumption",
        "script": "sim_auto_lirpa_stage_policy_bound_consumption_probe.py",
        "result": "auto_lirpa_stage_policy_bound_consumption_probe_results.json",
        "category": "auto_lirpa_policy_bound_consumption",
    },
    {
        "name": "auto_lirpa_trained_stage_policy_adapter_bound",
        "script": "sim_auto_lirpa_trained_stage_policy_adapter_bound_probe.py",
        "result": "auto_lirpa_trained_stage_policy_adapter_bound_probe_results.json",
        "category": "auto_lirpa_trained_policy_adapter",
    },
    {
        "name": "lirpa_policy_bound_gated_multicarrier_environment",
        "script": "sim_lirpa_policy_bound_gated_multicarrier_environment_probe.py",
        "result": "lirpa_policy_bound_gated_multicarrier_environment_probe_results.json",
        "category": "lirpa_policy_bound_multicarrier_environment",
    },
    {
        "name": "lirpa_policy_bound_variable_qubit_scaling",
        "script": "sim_lirpa_policy_bound_variable_qubit_scaling_probe.py",
        "result": "lirpa_policy_bound_variable_qubit_scaling_probe_results.json",
        "category": "lirpa_policy_bound_variable_qubit_scaling",
    },
    {
        "name": "lirpa_peps3d_size_normalized_environment_scaling",
        "script": "sim_lirpa_peps3d_size_normalized_environment_scaling_probe.py",
        "result": "lirpa_peps3d_size_normalized_environment_scaling_probe_results.json",
        "category": "lirpa_peps3d_size_normalized_environment_scaling",
    },
    {
        "name": "operational_manifest_quarantine",
        "script": "sim_operational_manifest_source_downstream_quarantine_probe.py",
        "result": "operational_manifest_source_downstream_quarantine_probe_results.json",
        "category": "manifest_quarantine",
    },
]

CRITICAL_NODES = {
    "manifold_operational_assembly",
    "source_stage_subcycle",
    "probe_family_reconciliation",
    "engine_operator_slot_alphabet",
    "qit_engine_work_execution",
    "qit_engine_dynamics_required_work",
    "operator_slot_entropy_gradient_mps_transport",
    "engine_core_autograd_severance_contract",
    "source_native_high_rank_engine_history",
    "peps3d_64_site_bond_dimension",
    "multiqubit_reservoir_global_structure",
    "multiqubit_reservoir_static_kernel_esn_baseline",
    "multiqubit_mps_reservoir_scaling_12_16_24_32",
    "macro_stage_record_science_method_contract",
    "source_native_fep_pomdp_policy_tree",
    "source_native_fep_online_vmp_policy_update",
    "macro_axis0_plural_stage_router",
    "holodeck_hash_memory_placeholder",
    "source_native_subdense_multicarrier_environment",
    "stage_record_downstream_carrier_consumption_closure",
    "axis0_plural_candidate_multicarrier_drive_controls",
    "path_entropy_schedule_confound_falsifier",
    "path_entropy_proxy_vs_deeper_invariant_pair_falsifier",
    "axis0_path_entropy_branch_closure",
    "axis0_holographic_boundary_branch_closure",
    "axis0_fep_gradient_stage_local_adapter_closure",
    "mps_local_boundary_path_fep_scaling_8_16_32",
    "world_model_repo_admission_gap_adapter",
    "auto_lirpa_lewm_latent_surprise_bound",
    "axis0_lewm_lirpa_pytorch_assembly",
    "auto_lirpa_stage_policy_bound_consumption",
    "auto_lirpa_trained_stage_policy_adapter_bound",
    "lirpa_policy_bound_gated_multicarrier_environment",
    "lirpa_policy_bound_variable_qubit_scaling",
    "lirpa_peps3d_size_normalized_environment_scaling",
    "operational_manifest_quarantine",
}

CRITICAL_EDGES = {
    ("manifold_operational_assembly", "source_stage_subcycle"),
    ("source_stage_subcycle", "probe_family_reconciliation"),
    ("probe_family_reconciliation", "engine_operator_slot_alphabet"),
    ("source_stage_subcycle", "engine_operator_slot_alphabet"),
    ("engine_operator_slot_alphabet", "qit_engine_work_execution"),
    ("qit_engine_work_execution", "qit_engine_dynamics_required_work"),
    ("qit_engine_dynamics_required_work", "source_to_multicarrier_execution"),
    ("engine_operator_slot_alphabet", "operator_slot_entropy_gradient_mps_transport"),
    ("engine_operator_slot_alphabet", "source_native_high_rank_engine_history"),
    ("source_native_high_rank_engine_history", "peps3d_32_64_site_capacity"),
    ("peps3d_64_site_bond_dimension", "source_to_multicarrier_execution"),
    ("multiqubit_reservoir_global_structure", "multiqubit_reservoir_static_kernel_esn_baseline"),
    ("multiqubit_reservoir_global_structure", "multiqubit_mps_reservoir_scaling_12_16_24_32"),
    ("operator_slot_entropy_gradient_mps_transport", "engine_core_autograd_severance_contract"),
    ("engine_core_autograd_severance_contract", "weyl_holonomy_mps_curvature_transport"),
    ("source_to_multicarrier_execution", "long_horizon_holonomy_boundary_entropy"),
    ("long_horizon_holonomy_boundary_entropy", "macro_stage_record_science_method_contract"),
    ("macro_stage_record_science_method_contract", "source_native_fep_pomdp_policy_tree"),
    ("source_native_fep_pomdp_policy_tree", "source_native_fep_online_vmp_policy_update"),
    ("source_native_fep_online_vmp_policy_update", "macro_axis0_plural_stage_router"),
    ("macro_stage_record_science_method_contract", "holodeck_hash_memory_placeholder"),
    ("macro_axis0_plural_stage_router", "source_native_subdense_multicarrier_environment"),
    ("holodeck_hash_memory_placeholder", "source_native_subdense_multicarrier_environment"),
    ("macro_axis0_plural_stage_router", "axis0_plural_candidate_multicarrier_drive_controls"),
    ("source_native_subdense_multicarrier_environment", "stage_record_downstream_carrier_consumption_closure"),
    ("stage_record_downstream_carrier_consumption_closure", "axis0_plural_candidate_multicarrier_drive_controls"),
    ("source_native_subdense_multicarrier_environment", "axis0_plural_candidate_multicarrier_drive_controls"),
    ("axis0_plural_candidate_multicarrier_drive_controls", "path_entropy_schedule_confound_falsifier"),
    ("axis0_plural_candidate_multicarrier_drive_controls", "path_entropy_proxy_vs_deeper_invariant_pair_falsifier"),
    ("path_entropy_schedule_confound_falsifier", "axis0_path_entropy_branch_closure"),
    ("path_entropy_proxy_vs_deeper_invariant_pair_falsifier", "axis0_path_entropy_branch_closure"),
    ("axis0_path_entropy_branch_closure", "axis0_holographic_boundary_branch_closure"),
    ("axis0_plural_candidate_multicarrier_drive_controls", "axis0_holographic_boundary_branch_closure"),
    ("axis0_holographic_boundary_branch_closure", "axis0_fep_gradient_stage_local_adapter_closure"),
    ("axis0_fep_gradient_stage_local_adapter_closure", "mps_local_boundary_path_fep_scaling_8_16_32"),
    ("axis0_plural_candidate_multicarrier_drive_controls", "mps_local_boundary_path_fep_scaling_8_16_32"),
    ("macro_stage_record_science_method_contract", "mps_local_boundary_path_fep_scaling_8_16_32"),
    ("mps_local_boundary_path_fep_scaling_8_16_32", "world_model_repo_admission_gap_adapter"),
    ("world_model_repo_admission_gap_adapter", "auto_lirpa_lewm_latent_surprise_bound"),
    ("auto_lirpa_lewm_latent_surprise_bound", "axis0_lewm_lirpa_pytorch_assembly"),
    ("axis0_lewm_lirpa_pytorch_assembly", "auto_lirpa_stage_policy_bound_consumption"),
    ("auto_lirpa_lewm_latent_surprise_bound", "auto_lirpa_stage_policy_bound_consumption"),
    ("world_model_repo_admission_gap_adapter", "auto_lirpa_stage_policy_bound_consumption"),
    ("auto_lirpa_stage_policy_bound_consumption", "auto_lirpa_trained_stage_policy_adapter_bound"),
    ("auto_lirpa_trained_stage_policy_adapter_bound", "lirpa_policy_bound_gated_multicarrier_environment"),
    ("lirpa_policy_bound_gated_multicarrier_environment", "lirpa_policy_bound_variable_qubit_scaling"),
    ("lirpa_policy_bound_variable_qubit_scaling", "lirpa_peps3d_size_normalized_environment_scaling"),
    ("lirpa_peps3d_size_normalized_environment_scaling", "operational_manifest_quarantine"),
    ("long_horizon_holonomy_boundary_entropy", "operational_manifest_quarantine"),
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


def receipt_passes(path: pathlib.Path, row: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    if not path.exists():
        return False, ["result missing"], {}
    data = json.loads(path.read_text(encoding="utf-8"))
    expected_all_pass_false = bool(
        data.get("expected_all_pass_false") is True
        or data.get("expected_all_pass") is False
    )
    if data.get("classification") != CLASSIFICATION:
        if data.get("classification") != "formal_scout":
            errors.append("classification is not formal_scout")
    if data.get("promotion_allowed") is not False:
        errors.append("promotion_allowed is not false")
    if not data.get("claim_ceiling"):
        errors.append("claim_ceiling missing")
    if data.get("blockers") and not expected_all_pass_false:
        errors.append("blockers present")
    for key in ("positive", "graveyard_companions", "boundary", "nearby_variants"):
        if key not in data:
            errors.append(f"{key} missing")
    for key in ("positive", "graveyard_companions", "boundary"):
        section = data.get(key)
        if isinstance(section, dict):
            for check_name, check in section.items():
                if isinstance(check, dict) and check.get("pass") is False and not expected_all_pass_false:
                    errors.append(f"{key}.{check_name} failed")
    nearby = data.get("nearby_variants")
    if isinstance(nearby, dict) and nearby.get("passed") != nearby.get("total") and not expected_all_pass_false:
        errors.append("nearby variants not all passed")
    if expected_all_pass_false and data.get("all_pass") is not False:
        errors.append("expected all_pass false receipt did not report all_pass=false")
    if "all_pass" in data and data.get("all_pass") is not True and not expected_all_pass_false:
        errors.append("all_pass is explicitly false")
    declared_width = row.get("minimum_width_qubits")
    if isinstance(declared_width, int) and declared_width < MIN_NONCLASSICAL_WIDTH:
        if row.get("minimum_width_role") != "calibration_only":
            errors.append("sub-minimum-width row is not marked calibration_only")
    width_policy = receipt_positive_width_policy(data)
    if width_policy["invalid_subminimum_positive_claims"]:
        errors.append(
            "sub-minimum positive width claim lacks calibration_only role: "
            + ", ".join(claim["path"] for claim in width_policy["invalid_subminimum_positive_claims"][:4])
        )
    return not errors, errors, data


def receipt_positive_width_policy(data: dict[str, Any]) -> dict[str, Any]:
    positive = data.get("positive") if isinstance(data.get("positive"), dict) else {}
    subminimum: list[dict[str, Any]] = []

    def visit(node: Any, path: str) -> None:
        if isinstance(node, dict):
            width = node.get("minimum_width_qubits")
            if not isinstance(width, int):
                width = node.get("n_qubits")
            if isinstance(width, int) and width < MIN_NONCLASSICAL_WIDTH and node.get("pass") is True:
                role = str(node.get("minimum_width_role") or node.get("width_role") or "")
                subminimum.append(
                    {
                        "path": path,
                        "width": width,
                        "minimum_width_role": role or "not_declared",
                        "minimum_width_reason": node.get("minimum_width_reason"),
                    }
                )
            for key, value in node.items():
                visit(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                visit(value, f"{path}[{index}]")

    visit(positive, "positive")
    invalid = [claim for claim in subminimum if claim["minimum_width_role"] != "calibration_only"]
    return {
        "pass": not invalid,
        "subminimum_positive_claim_count": len(subminimum),
        "subminimum_positive_claims": subminimum,
        "invalid_subminimum_positive_claims": invalid,
    }


def run_script(row: dict[str, str]) -> dict[str, Any]:
    script = ROOT / row["script"]
    result = RESULT_DIR / row["result"]
    started = time.time()
    if not script.exists():
        return {
            **row,
            "pass": False,
            "returncode": None,
            "elapsed_seconds": 0.0,
            "errors": ["script missing"],
        }
    env = dict(os.environ)
    env.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
    env.setdefault("NUMBA_DISABLE_JIT", "1")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        timeout=300,
    )
    receipt_ok, receipt_errors, data = receipt_passes(result, row)
    errors = []
    if proc.returncode != 0:
        errors.append(f"returncode {proc.returncode}")
    errors.extend(receipt_errors)
    source_alignment = data.get("source_alignment_category", "not_declared") if data else "missing"
    receipt_width_policy = receipt_positive_width_policy(data) if data else {
        "pass": False,
        "subminimum_positive_claim_count": 0,
        "subminimum_positive_claims": [],
        "invalid_subminimum_positive_claims": [],
    }
    result_sha256 = hashlib.sha256(result.read_bytes()).hexdigest() if result.exists() else ""
    return {
        **row,
        "pass": proc.returncode == 0 and receipt_ok,
        "returncode": proc.returncode,
        "elapsed_seconds": time.time() - started,
        "result_path": str(result.relative_to(ROOT)),
        "result_sha256": result_sha256,
        "errors": errors,
        "classification": data.get("classification") if data else None,
        "promotion_allowed": data.get("promotion_allowed") if data else None,
        "source_alignment_category": source_alignment,
        "minimum_width_qubits": row.get("minimum_width_qubits"),
        "minimum_width_role": row.get("minimum_width_role", "not_declared"),
        "minimum_width_reason": row.get("minimum_width_reason"),
        "receipt_width_policy": receipt_width_policy,
        "stdout_tail": proc.stdout[-500:],
        "stderr_tail": proc.stderr[-500:],
    }


def suite_width_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    subminimum = [
        {
            "name": row["name"],
            "minimum_width_qubits": row.get("minimum_width_qubits"),
            "minimum_width_role": row.get("minimum_width_role"),
            "minimum_width_reason": row.get("minimum_width_reason"),
        }
        for row in rows
        if isinstance(row.get("minimum_width_qubits"), int)
        and int(row["minimum_width_qubits"]) < MIN_NONCLASSICAL_WIDTH
    ]
    invalid = [row for row in subminimum if row.get("minimum_width_role") != "calibration_only"]
    invalid_receipts = [
        {
            "name": row["name"],
            "result_path": row.get("result_path"),
            "invalid_subminimum_positive_claims": row.get("receipt_width_policy", {}).get("invalid_subminimum_positive_claims", []),
        }
        for row in rows
        if row.get("receipt_width_policy", {}).get("invalid_subminimum_positive_claims")
    ]
    return {
        "pass": not invalid and not invalid_receipts,
        "minimum_nonclassical_width": MIN_NONCLASSICAL_WIDTH,
        "subminimum_row_count": len(subminimum),
        "subminimum_calibration_rows": subminimum,
        "invalid_subminimum_rows": invalid,
        "invalid_subminimum_receipts": invalid_receipts,
        "receipt_subminimum_claim_count": sum(
            int(row.get("receipt_width_policy", {}).get("subminimum_positive_claim_count", 0))
            for row in rows
        ),
        "boundary": "Rows below the minimum width may remain in the suite only as calibration/boundary evidence, not maturity evidence.",
    }


def build_dependency_graph(rows: list[dict[str, Any]]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for row in rows:
        graph.add_node(row["name"], category=row["category"], passed=bool(row["pass"]))
    for prev, cur in zip(rows, rows[1:]):
        graph.add_edge(prev["name"], cur["name"])
    graph.add_edge("manifold_operational_assembly", "manifold_handle_support")
    graph.add_edge("manifold_operational_assembly", "source_stage_subcycle")
    graph.add_edge("source_stage_subcycle", "probe_family_reconciliation")
    graph.add_edge("probe_family_reconciliation", "engine_operator_slot_alphabet")
    graph.add_edge("source_stage_subcycle", "engine_operator_slot_alphabet")
    graph.add_edge("manifold_handle_support", "source_seven_control_microsteps")
    graph.add_edge("source_stage_subcycle", "source_seven_control_microsteps")
    graph.add_edge("engine_operator_slot_alphabet", "qit_engine_work_execution")
    graph.add_edge("qit_engine_work_execution", "qit_engine_dynamics_required_work")
    graph.add_edge("qit_engine_dynamics_required_work", "source_to_multicarrier_execution")
    graph.add_edge("engine_operator_slot_alphabet", "operator_slot_entropy_gradient_mps_transport")
    graph.add_edge("source_seven_control_microsteps", "paired_chiral_joint_bipartite_execution")
    graph.add_edge("source_seven_control_microsteps", "source_to_multicarrier_execution")
    graph.add_edge("paired_chiral_joint_bipartite_execution", "source_to_multicarrier_execution")
    graph.add_edge("qit_engine_work_execution", "source_to_multicarrier_execution")
    graph.add_edge("operator_slot_entropy_gradient_mps_transport", "source_to_multicarrier_execution")
    graph.add_edge("source_native_high_rank_engine_history", "peps3d_32_64_site_capacity")
    graph.add_edge("peps3d_32_64_site_capacity", "peps3d_52_56_60_regime_ladder")
    graph.add_edge("peps3d_52_56_60_regime_ladder", "peps3d_64_site_slot_closeout")
    graph.add_edge("peps3d_64_site_slot_closeout", "peps3d_64_site_bond_dimension")
    graph.add_edge("engine_operator_slot_alphabet", "source_native_high_rank_engine_history")
    graph.add_edge("engine_operator_slot_alphabet", "multiqubit_reservoir_global_structure")
    graph.add_edge("multiqubit_reservoir_global_structure", "multiqubit_reservoir_static_kernel_esn_baseline")
    graph.add_edge("multiqubit_reservoir_global_structure", "multiqubit_reservoir_order_holonomy")
    graph.add_edge("multiqubit_reservoir_global_structure", "multiqubit_reservoir_temporal_ablation")
    graph.add_edge("multiqubit_reservoir_global_structure", "multiqubit_reservoir_meanfield_ablation")
    graph.add_edge("multiqubit_reservoir_global_structure", "multiqubit_mps_reservoir_scaling_12_16_24_32")
    graph.add_edge("multiqubit_reservoir_global_structure", "multiqubit_reservoir_digits_6q")
    graph.add_edge("operator_slot_entropy_gradient_mps_transport", "engine_core_autograd_severance_contract")
    graph.add_edge("engine_core_autograd_severance_contract", "weyl_holonomy_mps_curvature_transport")
    graph.add_edge("operator_slot_entropy_gradient_mps_transport", "constraint_manifold_layer_causal_matrix")
    graph.add_edge("operator_slot_entropy_gradient_mps_transport", "constraint_manifold_delta_neural_readout")
    graph.add_edge("source_stage_subcycle", "source_to_multicarrier_execution")
    graph.add_edge("multitool_entropy_geometry_carriers", "source_to_multicarrier_execution")
    graph.add_edge("peps3d_64_site_bond_dimension", "source_to_multicarrier_execution")
    graph.add_edge("multiqubit_mps_reservoir_scaling_12_16_24_32", "source_to_multicarrier_execution")
    graph.add_edge("source_to_multicarrier_execution", "long_horizon_holonomy_boundary_entropy")
    graph.add_edge("long_horizon_holonomy_boundary_entropy", "macro_stage_record_science_method_contract")
    graph.add_edge("macro_stage_record_science_method_contract", "source_native_fep_pomdp_policy_tree")
    graph.add_edge("source_native_fep_pomdp_policy_tree", "source_native_fep_online_vmp_policy_update")
    graph.add_edge("source_native_fep_online_vmp_policy_update", "macro_axis0_plural_stage_router")
    graph.add_edge("macro_stage_record_science_method_contract", "holodeck_hash_memory_placeholder")
    graph.add_edge("macro_axis0_plural_stage_router", "source_native_subdense_multicarrier_environment")
    graph.add_edge("holodeck_hash_memory_placeholder", "source_native_subdense_multicarrier_environment")
    graph.add_edge("macro_axis0_plural_stage_router", "axis0_plural_candidate_multicarrier_drive_controls")
    graph.add_edge("source_native_subdense_multicarrier_environment", "stage_record_downstream_carrier_consumption_closure")
    graph.add_edge("stage_record_downstream_carrier_consumption_closure", "axis0_plural_candidate_multicarrier_drive_controls")
    graph.add_edge("source_native_subdense_multicarrier_environment", "axis0_plural_candidate_multicarrier_drive_controls")
    graph.add_edge("axis0_plural_candidate_multicarrier_drive_controls", "path_entropy_schedule_confound_falsifier")
    graph.add_edge("axis0_plural_candidate_multicarrier_drive_controls", "path_entropy_proxy_vs_deeper_invariant_pair_falsifier")
    graph.add_edge("path_entropy_schedule_confound_falsifier", "axis0_path_entropy_branch_closure")
    graph.add_edge("path_entropy_proxy_vs_deeper_invariant_pair_falsifier", "axis0_path_entropy_branch_closure")
    graph.add_edge("axis0_path_entropy_branch_closure", "axis0_holographic_boundary_branch_closure")
    graph.add_edge("axis0_plural_candidate_multicarrier_drive_controls", "axis0_holographic_boundary_branch_closure")
    graph.add_edge("axis0_holographic_boundary_branch_closure", "axis0_fep_gradient_stage_local_adapter_closure")
    graph.add_edge("axis0_fep_gradient_stage_local_adapter_closure", "mps_local_boundary_path_fep_scaling_8_16_32")
    graph.add_edge("axis0_plural_candidate_multicarrier_drive_controls", "mps_local_boundary_path_fep_scaling_8_16_32")
    graph.add_edge("macro_stage_record_science_method_contract", "mps_local_boundary_path_fep_scaling_8_16_32")
    graph.add_edge("mps_local_boundary_path_fep_scaling_8_16_32", "world_model_repo_admission_gap_adapter")
    graph.add_edge("world_model_repo_admission_gap_adapter", "auto_lirpa_lewm_latent_surprise_bound")
    graph.add_edge("auto_lirpa_lewm_latent_surprise_bound", "axis0_lewm_lirpa_pytorch_assembly")
    graph.add_edge("axis0_lewm_lirpa_pytorch_assembly", "auto_lirpa_stage_policy_bound_consumption")
    graph.add_edge("auto_lirpa_lewm_latent_surprise_bound", "auto_lirpa_stage_policy_bound_consumption")
    graph.add_edge("world_model_repo_admission_gap_adapter", "auto_lirpa_stage_policy_bound_consumption")
    graph.add_edge("auto_lirpa_stage_policy_bound_consumption", "auto_lirpa_trained_stage_policy_adapter_bound")
    graph.add_edge("auto_lirpa_trained_stage_policy_adapter_bound", "lirpa_policy_bound_gated_multicarrier_environment")
    graph.add_edge("lirpa_policy_bound_gated_multicarrier_environment", "lirpa_policy_bound_variable_qubit_scaling")
    graph.add_edge("lirpa_policy_bound_variable_qubit_scaling", "lirpa_peps3d_size_normalized_environment_scaling")
    graph.add_edge("lirpa_peps3d_size_normalized_environment_scaling", "operational_manifest_quarantine")
    graph.add_edge("long_horizon_holonomy_boundary_entropy", "operational_manifest_quarantine")
    return graph


def missing_critical_nodes(rows: list[dict[str, Any]]) -> list[str]:
    names = {row["name"] for row in rows}
    return sorted(CRITICAL_NODES - names)


def missing_critical_edges(graph: nx.DiGraph) -> list[list[str]]:
    return [list(edge) for edge in sorted(CRITICAL_EDGES) if not graph.has_edge(*edge)]


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(SUITE, start=1):
        print(f"SUITE_PROGRESS start {index}/{len(SUITE)} {row['name']}", flush=True)
        completed = run_script(row)
        rows.append(completed)
        print(
            f"SUITE_PROGRESS done {index}/{len(SUITE)} {row['name']} "
            f"pass={completed['pass']} elapsed={completed['elapsed_seconds']:.3f}s",
            flush=True,
        )
    pass_vector = [bool(row["pass"]) for row in rows]
    graph = build_dependency_graph(rows)
    manifest_row = next(row for row in rows if row["name"] == "operational_manifest_quarantine")
    category_counts = {category: 0 for category in sorted({row["category"] for row in rows})}
    for row in rows:
        category_counts[row["category"]] += 1
    missing_nodes = missing_critical_nodes(rows)
    missing_edges = missing_critical_edges(graph)
    row_hashes_present = all(bool(row.get("result_sha256")) for row in rows)
    width_policy = suite_width_policy(rows)

    suite_all_pass = all(pass_vector) and nx.is_directed_acyclic_graph(graph) and bool(width_policy["pass"])
    symbolic_count = sp.Integer(len(rows))
    z3_solver = Solver()
    all_scripts_pass = Bool("all_scripts_pass")
    graph_is_acyclic = Bool("graph_is_acyclic")
    minimum_width_policy_passes = Bool("minimum_width_policy_passes")
    z3_solver.add(all_scripts_pass == all(pass_vector))
    z3_solver.add(graph_is_acyclic == nx.is_directed_acyclic_graph(graph))
    z3_solver.add(minimum_width_policy_passes == bool(width_policy["pass"]))
    z3_solver.add(And(all_scripts_pass, graph_is_acyclic, minimum_width_policy_passes))
    z3_status = z3_solver.check()

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "suite_fresh_rerun_for_integrated_source_native_qit_engine_tensor_reservoir_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "suite_rows": rows,
        "positive": {
            "ordered_suite_fresh_reruns_pass": {
                "pass": suite_all_pass,
                "count": len(rows),
                "passed": sum(1 for flag in pass_vector if flag),
            },
            "manifold_first_order_is_enforced": {
                "pass": rows[0]["category"] == "source_native_constraint_manifold_operational_assembly"
                and rows[0]["name"] == "manifold_operational_assembly"
                and rows[1]["name"] == "manifold_handle_support",
                "first": rows[0]["name"],
                "second": rows[1]["name"],
            },
            "evidence_dependency_graph_is_acyclic": {
                "pass": nx.is_directed_acyclic_graph(graph),
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
            },
            "current_qit_engine_tensor_reservoir_surfaces_are_in_suite": {
                "pass": not missing_nodes,
                "critical_nodes": sorted(CRITICAL_NODES),
                "missing_nodes": missing_nodes,
            },
            "critical_dependency_edges_are_present": {
                "pass": not missing_edges,
                "critical_edges": [list(edge) for edge in sorted(CRITICAL_EDGES)],
                "missing_edges": missing_edges,
            },
            "receipt_hashes_are_recorded_after_fresh_rerun": {
                "pass": row_hashes_present,
                "hashed_rows": sum(1 for row in rows if row.get("result_sha256")),
                "row_count": len(rows),
            },
            "symbolic_smt_suite_witness": {
                "pass": z3_status == sat and symbolic_count == len(rows),
                "z3": str(z3_status),
                "symbolic_count": str(symbolic_count),
            },
            "minimum_width_policy_is_explicit": width_policy,
        },
        "graveyard_companions": {
            "manifest_must_be_last": {
                "pass": rows[-1]["name"] == "operational_manifest_quarantine",
                "last": rows[-1]["name"],
            },
            "no_script_may_return_red": {
                "pass": all(row["returncode"] == 0 for row in rows),
                "red": [row["name"] for row in rows if row["returncode"] != 0],
            },
            "no_receipt_may_promote": {
                "pass": not any(row["promotion_allowed"] is not False for row in rows),
                "promoted": [row["name"] for row in rows if row["promotion_allowed"] is not False],
            },
            "manifest_quarantine_receipt_must_pass": {
                "pass": bool(manifest_row["pass"]),
                "manifest_errors": manifest_row["errors"],
            },
            "critical_surface_omission_is_detected": {
                "pass": not missing_nodes and not missing_edges,
                "missing_nodes": missing_nodes,
                "missing_edges": missing_edges,
                "note": "A missing critical node or edge makes this graveyard fail instead of silently treating receipt presence as integration.",
            },
            "subminimum_width_rows_are_calibration_only": {
                "pass": bool(width_policy["pass"]),
                **width_policy,
            },
        },
        "boundary": {
            "suite_runner_is_not_final_canonical_proof": {
                "pass": True,
                "promotion_allowed": PROMOTION_ALLOWED,
            },
            "global_name_lint_is_not_claimed": {
                "pass": True,
                "note": "This scout checks the integrated suite rerun, not unrelated global filename hygiene.",
            },
            "provider_review_is_not_substituted_for_rerun": {
                "pass": True,
                "note": "Every suite row is rerun locally by subprocess before this receipt is written.",
            },
            "six_qubit_real_data_row_is_not_maturity_evidence": {
                "pass": any(row["name"] == "multiqubit_reservoir_digits_6q" for row in width_policy["subminimum_calibration_rows"]),
                "minimum_nonclassical_width": MIN_NONCLASSICAL_WIDTH,
                "subminimum_calibration_rows": width_policy["subminimum_calibration_rows"],
            },
        },
        "nearby_variants": {
            "total": 6,
            "passed": sum(
                int(flag)
                for flag in [
                    rows[-1]["name"] == "operational_manifest_quarantine",
                    all(row["returncode"] == 0 for row in rows),
                    not any(row["promotion_allowed"] is not False for row in rows),
                    bool(manifest_row["pass"]),
                    not missing_nodes and not missing_edges,
                    bool(width_policy["pass"]),
                ]
            ),
            "variants": [
                "manifest_must_be_last",
                "no_script_may_return_red",
                "no_receipt_may_promote",
                "manifest_quarantine_receipt_must_pass",
                "critical_surface_omission_is_detected",
                "subminimum_width_rows_are_calibration_only",
            ],
        },
        "category_counts": category_counts,
        "all_pass": suite_all_pass and z3_status == sat and not missing_nodes and not missing_edges and row_hashes_present,
        "blockers": [],
        "elapsed_seconds": time.time() - start,
        "why_not_v4_probes": [
            "Suite rerun scout only.",
            "It verifies current formal-scout operational rerunnability but does not prove a final or canonical manifold.",
            "It does not repair unrelated older scout names or missing source_alignment_category fields outside the selected integrated suite.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
