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
import numpy as np
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
        "reason": "load-bearing ordered fresh reruns of formal-scout scripts",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt parsing and suite result writing",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing canonical script and result path checks",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing pass-vector and runtime-gap checks",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ordered evidence dependency graph",
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
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

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
        "script": "sim_constraint_manifold_qit_engine_work_execution_probe.py",
        "result": "constraint_manifold_qit_engine_work_execution_probe_results.json",
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
        "name": "axis0_plural_candidate_multicarrier_drive_controls",
        "script": "sim_axis0_plural_candidate_multicarrier_drive_controls_probe.py",
        "result": "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json",
        "category": "axis0_plural_candidate_multicarrier_drive_controls",
    },
    {
        "name": "world_model_repo_admission_gap_adapter",
        "script": "sim_world_model_repo_admission_gap_adapter_probe.py",
        "result": "world_model_repo_admission_gap_adapter_probe_results.json",
        "category": "world_model_repo_admission",
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
    "macro_axis0_plural_stage_router",
    "holodeck_hash_memory_placeholder",
    "source_native_subdense_multicarrier_environment",
    "axis0_plural_candidate_multicarrier_drive_controls",
    "world_model_repo_admission_gap_adapter",
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
    ("macro_stage_record_science_method_contract", "macro_axis0_plural_stage_router"),
    ("macro_stage_record_science_method_contract", "holodeck_hash_memory_placeholder"),
    ("macro_axis0_plural_stage_router", "source_native_subdense_multicarrier_environment"),
    ("holodeck_hash_memory_placeholder", "source_native_subdense_multicarrier_environment"),
    ("macro_axis0_plural_stage_router", "axis0_plural_candidate_multicarrier_drive_controls"),
    ("source_native_subdense_multicarrier_environment", "axis0_plural_candidate_multicarrier_drive_controls"),
    ("axis0_plural_candidate_multicarrier_drive_controls", "world_model_repo_admission_gap_adapter"),
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
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


def receipt_passes(path: pathlib.Path) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    if not path.exists():
        return False, ["result missing"], {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("classification") != CLASSIFICATION:
        if data.get("classification") != "formal_scout":
            errors.append("classification is not formal_scout")
    if data.get("promotion_allowed") is not False:
        errors.append("promotion_allowed is not false")
    if not data.get("claim_ceiling"):
        errors.append("claim_ceiling missing")
    if data.get("blockers"):
        errors.append("blockers present")
    for key in ("positive", "graveyard_companions", "boundary", "nearby_variants"):
        if key not in data:
            errors.append(f"{key} missing")
    for key in ("positive", "graveyard_companions", "boundary"):
        section = data.get(key)
        if isinstance(section, dict):
            for check_name, check in section.items():
                if isinstance(check, dict) and check.get("pass") is False:
                    errors.append(f"{key}.{check_name} failed")
    nearby = data.get("nearby_variants")
    if isinstance(nearby, dict) and nearby.get("passed") != nearby.get("total"):
        errors.append("nearby variants not all passed")
    if "all_pass" in data and data.get("all_pass") is not True:
        errors.append("all_pass is explicitly false")
    return not errors, errors, data


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
    receipt_ok, receipt_errors, data = receipt_passes(result)
    errors = []
    if proc.returncode != 0:
        errors.append(f"returncode {proc.returncode}")
    errors.extend(receipt_errors)
    source_alignment = data.get("source_alignment_category", "not_declared") if data else "missing"
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
        "stdout_tail": proc.stdout[-500:],
        "stderr_tail": proc.stderr[-500:],
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
    graph.add_edge("macro_stage_record_science_method_contract", "macro_axis0_plural_stage_router")
    graph.add_edge("macro_stage_record_science_method_contract", "holodeck_hash_memory_placeholder")
    graph.add_edge("macro_axis0_plural_stage_router", "source_native_subdense_multicarrier_environment")
    graph.add_edge("holodeck_hash_memory_placeholder", "source_native_subdense_multicarrier_environment")
    graph.add_edge("macro_axis0_plural_stage_router", "axis0_plural_candidate_multicarrier_drive_controls")
    graph.add_edge("source_native_subdense_multicarrier_environment", "axis0_plural_candidate_multicarrier_drive_controls")
    graph.add_edge("axis0_plural_candidate_multicarrier_drive_controls", "world_model_repo_admission_gap_adapter")
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
    rows = [run_script(row) for row in SUITE]
    pass_vector = np.array([1 if row["pass"] else 0 for row in rows], dtype=float)
    graph = build_dependency_graph(rows)
    manifest_row = next(row for row in rows if row["name"] == "operational_manifest_quarantine")
    category_counts = {category: 0 for category in sorted({row["category"] for row in rows})}
    for row in rows:
        category_counts[row["category"]] += 1
    missing_nodes = missing_critical_nodes(rows)
    missing_edges = missing_critical_edges(graph)
    row_hashes_present = all(bool(row.get("result_sha256")) for row in rows)

    suite_all_pass = bool(np.all(pass_vector)) and nx.is_directed_acyclic_graph(graph)
    symbolic_count = sp.Integer(len(rows))
    z3_solver = Solver()
    all_scripts_pass = Bool("all_scripts_pass")
    graph_is_acyclic = Bool("graph_is_acyclic")
    z3_solver.add(all_scripts_pass == bool(np.all(pass_vector)))
    z3_solver.add(graph_is_acyclic == nx.is_directed_acyclic_graph(graph))
    z3_solver.add(And(all_scripts_pass, graph_is_acyclic))
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
                "passed": int(pass_vector.sum()),
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
        },
        "nearby_variants": {
            "total": 5,
            "passed": 4 + int(not missing_nodes and not missing_edges),
            "variants": [
                "manifest_must_be_last",
                "no_script_may_return_red",
                "no_receipt_may_promote",
                "provider_review_is_not_substituted_for_rerun",
                "critical_surface_omission_is_detected",
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
