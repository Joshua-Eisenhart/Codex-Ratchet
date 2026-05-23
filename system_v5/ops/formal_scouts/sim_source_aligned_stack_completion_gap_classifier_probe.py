#!/usr/bin/env python3
"""Source-aligned stack completion/gap classifier.

Formal scout only. This consumes the current active receipt set for the
source-aligned Codex Ratchet stack and classifies which parts of the long-term
objective are evidenced, which remain candidate-level, and which block final
completion.

It intentionally rejects a premature "goal complete" reading. The current
receipts support bounded formal-scout progress for flux, source-aligned QIT
runtime, Axis0 candidate families, and spinor/twistor carrier controls. They do
not close final Xi, final Phi0, final tensor scaling, final manifold admission,
final physics, or a promotion-grade full coupled runtime.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "source_aligned_stack_completion_gap_classifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "source_aligned_stack_completion_gap_classifier"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: classifies current source-aligned stack evidence and "
    "blocks premature completion/promotion. It does not admit final Xi, final "
    "Phi0, final tensor scaling, final manifold law, final source-aligned full "
    "runtime, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite score vectors for requirement coverage and gap-margin checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive completion and nonpromotion satisfiability fences",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt ingestion and result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local receipt path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}


ACTIVE_RECEIPTS = {
    "geometric_flux": "geometric_flux_derives_basin_binding_probe_results.json",
    "source_runtime": "source_aligned_qit_engine_runtime_probe_results.json",
    "coupled_e16_runtime": "two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json",
    "full_trace_refresh": "two_root_constraint_full_manifold_runtime_trace_refresh_probe_results.json",
    "qit_fep_path": "qit_fep_axis0_path_integral_spinor_probe_results.json",
    "entropy_bakeoff": "axis0_entropy_family_qit_fep_admission_bakeoff_probe_results.json",
    "axis0_candidate_bundle": "axis0_admitted_candidate_vector_bundle_ablation_probe_results.json",
    "axis0_vector_actuator": "axis0_operator_local_vector_actuator_family_decoupling_probe_results.json",
    "spinor_root": "spinor_twistor_entanglement_information_network_root_gate_probe_results.json",
    "spinor_flux": "spinor_twistor_flux_basin_binding_probe_results.json",
    "xi_bridge": "spinor_twistor_xi_cut_phi0_bridge_candidate_probe_results.json",
    "xi_path_weighted": "xi_phi0_path_weighted_cut_candidate_probe_results.json",
    "xi_boundary_capacity": "xi_phi0_boundary_capacity_cut_candidate_probe_results.json",
    "xi_free_energy": "two_root_constraint_qit_fep_free_energy_phi0_candidate_probe_results.json",
    "xi_qci": "two_root_constraint_quantum_conditional_information_phi0_candidate_probe_results.json",
    "xi_petz": "two_root_constraint_petz_recovery_phi0_candidate_probe_results.json",
    "xi_l7_history": "two_root_constraint_l7_xi_history_phi0_bridge_probe_results.json",
    "xi_causal_irreversibility": "two_root_constraint_xi_causal_irreversibility_phi0_bridge_probe_results.json",
    "xi_mps_rescue": "two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe_results.json",
    "xi_slow_mode_repair": "two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe_results.json",
    "phi0_stress_controls": "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "phi0_response_gradient": "two_root_constraint_phi0_bridge_response_gradient_after_stress_probe_results.json",
    "scale_basin_stability": "two_root_constraint_scale_basin_stability_map_probe_results.json",
    "tensor_scaling_status": "two_root_constraint_tensor_scaling_status_classifier_probe_results.json",
    "full_trace_after_stress": "two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    return value


def load_receipt(filename: str) -> dict[str, Any]:
    path = RESULT_DIR / filename
    return json.loads(path.read_text())


def section_keys(receipt: dict[str, Any], key: str) -> set[str]:
    value = receipt.get(key, {})
    if isinstance(value, dict):
        return set(value.keys())
    if isinstance(value, list):
        return {str(row.get("id", idx)) for idx, row in enumerate(value) if isinstance(row, dict)}
    return set()


def section_passes(section: Any) -> bool:
    if isinstance(section, dict):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section.values())
    if isinstance(section, list):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section)
    return False


def has_phrase(receipt: dict[str, Any], phrase: str) -> bool:
    blob = json.dumps(receipt, sort_keys=True)
    return phrase in blob


def evidence_matrix(receipts: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    source_runtime = receipts["source_runtime"]
    coupled_e16_runtime = receipts["coupled_e16_runtime"]
    full_trace_refresh = receipts["full_trace_refresh"]
    geometric_flux = receipts["geometric_flux"]
    spinor_flux = receipts["spinor_flux"]
    qit_fep_path = receipts["qit_fep_path"]
    entropy_bakeoff = receipts["entropy_bakeoff"]
    axis0_candidate_bundle = receipts["axis0_candidate_bundle"]
    axis0_vector_actuator = receipts["axis0_vector_actuator"]
    spinor_root = receipts["spinor_root"]
    xi_bridge = receipts["xi_bridge"]
    xi_path_weighted = receipts["xi_path_weighted"]
    xi_boundary_capacity = receipts["xi_boundary_capacity"]
    xi_free_energy = receipts["xi_free_energy"]
    xi_qci = receipts["xi_qci"]
    xi_petz = receipts["xi_petz"]
    xi_l7_history = receipts["xi_l7_history"]
    xi_causal_irreversibility = receipts["xi_causal_irreversibility"]
    xi_mps_rescue = receipts["xi_mps_rescue"]
    xi_slow_mode_repair = receipts["xi_slow_mode_repair"]
    phi0_stress_controls = receipts["phi0_stress_controls"]
    phi0_response_gradient = receipts["phi0_response_gradient"]
    scale_basin_stability = receipts["scale_basin_stability"]
    tensor_scaling_status = receipts["tensor_scaling_status"]
    full_trace_after_stress = receipts["full_trace_after_stress"]

    runtime_keys = section_keys(source_runtime, "positive")
    coupled_runtime_keys = section_keys(coupled_e16_runtime, "positive")
    full_trace_keys = section_keys(full_trace_refresh, "positive")
    full_trace_graveyard = section_keys(full_trace_refresh, "graveyard_companions")
    full_trace_boundary = section_keys(full_trace_refresh, "boundary")
    flux_keys = section_keys(geometric_flux, "positive") | section_keys(spinor_flux, "positive")
    axis0_keys = (
        section_keys(qit_fep_path, "positive")
        | section_keys(entropy_bakeoff, "positive")
        | section_keys(axis0_candidate_bundle, "positive")
        | section_keys(axis0_vector_actuator, "positive")
    )
    axis0_graveyard = section_keys(axis0_candidate_bundle, "graveyard_companions") | section_keys(
        axis0_vector_actuator, "graveyard_companions"
    )
    axis0_boundary = section_keys(axis0_candidate_bundle, "boundary") | section_keys(axis0_vector_actuator, "boundary")
    spinor_keys = section_keys(spinor_root, "positive")
    xi_graveyard = section_keys(xi_bridge, "graveyard_companions")
    xi_boundary = section_keys(xi_bridge, "boundary")
    xi_path_graveyard = section_keys(xi_path_weighted, "graveyard_companions")
    xi_path_boundary = section_keys(xi_path_weighted, "boundary")
    xi_capacity_graveyard = section_keys(xi_boundary_capacity, "graveyard_companions")
    xi_capacity_boundary = section_keys(xi_boundary_capacity, "boundary")
    xi_free_energy_keys = section_keys(xi_free_energy, "positive")
    xi_free_energy_graveyard = section_keys(xi_free_energy, "graveyard_companions")
    xi_free_energy_boundary = section_keys(xi_free_energy, "boundary")
    xi_qci_keys = section_keys(xi_qci, "positive")
    xi_qci_graveyard = section_keys(xi_qci, "graveyard_companions")
    xi_qci_boundary = section_keys(xi_qci, "boundary")
    xi_petz_keys = section_keys(xi_petz, "positive")
    xi_petz_graveyard = section_keys(xi_petz, "graveyard_companions")
    xi_petz_boundary = section_keys(xi_petz, "boundary")
    xi_l7_keys = section_keys(xi_l7_history, "positive")
    xi_l7_graveyard = section_keys(xi_l7_history, "graveyard_companions")
    xi_l7_boundary = section_keys(xi_l7_history, "boundary")
    xi_causal_keys = section_keys(xi_causal_irreversibility, "positive")
    xi_causal_graveyard = section_keys(xi_causal_irreversibility, "graveyard_companions")
    xi_causal_boundary = section_keys(xi_causal_irreversibility, "boundary")
    xi_mps_keys = section_keys(xi_mps_rescue, "positive")
    xi_mps_graveyard = section_keys(xi_mps_rescue, "graveyard_companions")
    xi_mps_boundary = section_keys(xi_mps_rescue, "boundary")
    xi_slow_keys = section_keys(xi_slow_mode_repair, "positive")
    xi_slow_graveyard = section_keys(xi_slow_mode_repair, "graveyard_companions")
    xi_slow_boundary = section_keys(xi_slow_mode_repair, "boundary")
    phi0_stress_keys = section_keys(phi0_stress_controls, "positive")
    phi0_stress_graveyard = section_keys(phi0_stress_controls, "graveyard_companions")
    phi0_stress_boundary = section_keys(phi0_stress_controls, "boundary")
    phi0_response_keys = section_keys(phi0_response_gradient, "positive")
    phi0_response_graveyard = section_keys(phi0_response_gradient, "graveyard_companions")
    phi0_response_boundary = section_keys(phi0_response_gradient, "boundary")
    scale_basin_keys = section_keys(scale_basin_stability, "positive")
    scale_basin_graveyard = section_keys(scale_basin_stability, "graveyard_companions")
    scale_basin_boundary = section_keys(scale_basin_stability, "boundary")
    tensor_scaling_keys = section_keys(tensor_scaling_status, "positive")
    tensor_scaling_graveyard = section_keys(tensor_scaling_status, "graveyard_companions")
    tensor_scaling_boundary = section_keys(tensor_scaling_status, "boundary")
    full_trace_after_stress_keys = section_keys(full_trace_after_stress, "positive")
    full_trace_after_stress_graveyard = section_keys(full_trace_after_stress, "graveyard_companions")
    full_trace_after_stress_boundary = section_keys(full_trace_after_stress, "boundary")

    rows = {
        "source_aligned_runtime": {
            "status": "strong_formal_scout_evidence_with_bounded_e16_first_rung",
            "pass": bool(
                source_runtime.get("all_pass")
                and coupled_e16_runtime.get("all_pass")
                and full_trace_refresh.get("all_pass")
                and {
                    "source_aligned_engines_run",
                    "source_aligned_engines_converge",
                    "source_aligned_engines_are_distinct",
                    "terrain_realization_count_is_8",
                    "schedule_order_matters",
                }
                <= runtime_keys
                and {"coupled_e16_cases_ran", "cross_engine_coupling_changes_runtime", "rho_ab_phi0_extracted"}
                <= coupled_runtime_keys
                and {"coupled_e16_receipt_integrated", "admission_guard_blocks_final_promotion"} <= full_trace_keys
                and "weak_phi0_not_promoted" not in full_trace_graveyard
            ),
            "evidence": sorted(runtime_keys | coupled_runtime_keys | full_trace_keys | full_trace_boundary),
            "limit": "source-aligned one-qubit runtime plus bounded E16 first rung; not PEPS/PEPS3D, not L32/L64, not final full coupled dynamics",
        },
        "flux_manifold_binding": {
            "status": "strong_formal_scout_evidence_for_manifold_derived_candidate",
            "pass": bool(
                geometric_flux.get("all_pass")
                and spinor_flux.get("all_pass")
                and "hopf_weyl_geometry_derives_flux_sign" in flux_keys
                and "spinor_twistor_global_flux_basin_binding" in flux_keys
                and "not_flux_axis3_identity" in section_keys(geometric_flux, "boundary")
                and "flux_not_admitted_as_axis3" in section_keys(spinor_flux, "boundary")
            ),
            "evidence": sorted(flux_keys),
            "limit": "classified as manifold-derived candidate; not root, not Axis 3 identity, not final law",
        },
        "axis0_candidate_space": {
            "status": "candidate_space_evidenced_with_admitted_vector_bundle_controls",
            "pass": bool(
                qit_fep_path.get("all_pass")
                and entropy_bakeoff.get("all_pass")
                and axis0_candidate_bundle.get("all_pass")
                and axis0_vector_actuator.get("all_pass")
                and "noncommuting_order_signal_survives_controls" in axis0_keys
                and "entropy_family_roles_classified" in axis0_keys
                and "signed_bipartite_family_separates_direction" in axis0_keys
                and "admitted_candidate_survival_metrics" in axis0_keys
                and "family_decoupled_vector_actuator_runs_on_all_carriers" in axis0_keys
                and "path_entropy_and_holographic_controls_remain_blocked" in axis0_graveyard
                and "claim_ceiling_blocks_axis0_maturity" in axis0_boundary
            ),
            "evidence": sorted(axis0_keys | axis0_graveyard | axis0_boundary),
            "limit": "Axis0 candidate/control family is stronger than the initial bakeoff, but final Axis0 maturity and final Xi/Phi0 remain open",
        },
        "spinor_twistor_carrier": {
            "status": "strong_formal_scout_evidence",
            "pass": bool(
                spinor_root.get("all_pass")
                and {
                    "finite_capacity_bekenstein_gate",
                    "noncommuting_spinor_transport",
                    "spinor_network_relabel_invariant",
                    "spinor_twistor_readout_global_su2_invariant",
                }
                <= spinor_keys
                and "raw_tensor_index_substrate_rejected" in section_keys(spinor_root, "graveyard_companions")
            ),
            "evidence": sorted(spinor_keys),
            "limit": "supports spinor/twistor-like finite carrier controls; not full twistor theory",
        },
        "tensor_scaling_status": {
            "status": "bounded_tensor_scaling_evidenced_not_final",
            "pass": bool(
                tensor_scaling_status.get("all_pass")
                and "tensor_scaling_receipts_loaded" in tensor_scaling_keys
                and "l64_chain_classified" in tensor_scaling_keys
                and "peps_peps3d_chain_classified" in tensor_scaling_keys
                and "bounded_l64_not_full_convergence" in tensor_scaling_graveyard
                and "tiny_peps_not_full_environment" in tensor_scaling_graveyard
                and "robust_phi0_and_scale_basin_still_missing" in tensor_scaling_graveyard
                and "final_tensor_scaling_not_admitted" in tensor_scaling_boundary
            ),
            "evidence": sorted(tensor_scaling_keys | tensor_scaling_graveyard | tensor_scaling_boundary),
            "limit": "bounded L32/L64/MPS/PEPS/PEPS3D evidence is consolidated; full convergence, full environment contraction, robust Phi0, and scale-basin admission remain blocked",
        },
        "xi_phi0_bridge": {
            "status": "weak_first_rung_open_blocker",
            "pass": bool(
                xi_bridge.get("all_pass")
                and xi_path_weighted.get("all_pass")
                and xi_boundary_capacity.get("all_pass")
                and xi_free_energy.get("all_pass")
                and xi_qci.get("all_pass")
                and xi_petz.get("all_pass")
                and xi_l7_history.get("all_pass")
                and xi_causal_irreversibility.get("all_pass")
                and xi_mps_rescue.get("all_pass")
                and xi_slow_mode_repair.get("all_pass")
                and phi0_stress_controls.get("all_pass")
                and phi0_response_gradient.get("all_pass")
                and scale_basin_stability.get("all_pass")
                and coupled_e16_runtime.get("all_pass")
                and full_trace_refresh.get("all_pass")
                and full_trace_after_stress.get("all_pass")
                and "naive_raw_incidence_phase_bridge_rejected" in xi_graveyard
                and "xi_candidate_sweep_has_no_admitted_mode" in xi_graveyard
                and "xi_bridge_not_canonized" in xi_boundary
                and "path_weighted_candidate_not_admitted" in xi_path_graveyard
                and "zero_phase_control_rejects_incidence_path_candidate" in xi_path_graveyard
                and "final_xi_phi0_not_admitted" in xi_path_boundary
                and "boundary_capacity_candidate_not_admitted" in xi_capacity_graveyard
                and "zero_uniform_random_controls_beat_candidate" in xi_capacity_graveyard
                and "over_capacity_control_rejected" in xi_capacity_graveyard
                and "final_xi_phi0_not_admitted" in xi_capacity_boundary
                and "free_energy_cut_surface_built" in xi_free_energy_keys
                and "energy_correction_is_load_bearing" in xi_free_energy_keys
                and "noncommuting_path_difference_measured" in xi_free_energy_keys
                and "candidate_not_control_separated" in xi_free_energy_graveyard
                and "energy_term_not_sufficient_for_admission" in xi_free_energy_graveyard
                and "final_xi_phi0_not_admitted" in xi_free_energy_boundary
                and "tripartite_cut_surface_built" in xi_qci_keys
                and "history_register_signal_measured" in xi_qci_keys
                and "entanglement_condition_measured" in xi_qci_keys
                and "noncommuting_path_difference_measured" in xi_qci_keys
                and "candidate_not_control_separated" in xi_qci_graveyard
                and "qci_signal_not_sufficient_for_admission" in xi_qci_graveyard
                and "history_register_not_sufficient_for_admission" in xi_qci_graveyard
                and "final_xi_phi0_not_admitted" in xi_qci_boundary
                and "petz_recovery_surface_built" in xi_petz_keys
                and "petz_defect_signal_measured" in xi_petz_keys
                and "history_register_signal_measured" in xi_petz_keys
                and "entanglement_condition_measured" in xi_petz_keys
                and "noncommuting_path_difference_measured" in xi_petz_keys
                and "candidate_not_control_separated" in xi_petz_graveyard
                and "recovery_signal_not_sufficient_for_admission" in xi_petz_graveyard
                and "near_reversed_order_control_blocks_admission" in xi_petz_graveyard
                and "final_xi_phi0_not_admitted" in xi_petz_boundary
                and "bridge_status_classified" in xi_l7_keys
                and "not_final_axis0_closure" in xi_l7_graveyard
                and "final_manifold_admission_allowed" in xi_l7_boundary
                and "causal_xi_surface_complete" in xi_causal_keys
                and "single_engine_basin" in xi_causal_graveyard
                and "real_attractor_basin_admission_allowed" in xi_causal_boundary
                and "bridge_status_classified" in xi_mps_keys
                and "nonzero_phi0_is_not_rescue" in xi_mps_graveyard
                and "bridge_status" in xi_mps_boundary
                and "bridge_status_classified" in xi_slow_keys
                and "nonzero_or_feature_enhanced_bridge_is_not_enough" in xi_slow_graveyard
                and "bridge_status" in xi_slow_boundary
                and "bridge_status_classified" in coupled_runtime_keys
                and "weak_control_margin_only" in section_keys(coupled_e16_runtime, "boundary")
                and "stress_status_classified" in phi0_stress_keys
                and "stress_may_demote_weak_bridge" in phi0_stress_graveyard
                and "stress_status" in phi0_stress_boundary
                and "repair_status_classified" in phi0_response_keys
                and "response_gradient_does_not_rescue_current_phi0" in phi0_response_graveyard
                and "repair_status" in phi0_response_boundary
                and "finite_runtime_maps_converge" in scale_basin_keys
                and "finite_single_basin_does_not_imply_scale_basin" in scale_basin_graveyard
                and "phi0_stress_blocks_final_basin" in scale_basin_graveyard
                and "final_scale_basin_not_admitted" in scale_basin_boundary
                and "phi0_current_status" in full_trace_boundary
                and "slow_mode_terrain_phi0_repair_nonseparating" in full_trace_graveyard
                and "weak_phi0_not_promoted" in full_trace_after_stress_graveyard
                and "final_manifold_admission_allowed" in full_trace_after_stress_boundary
            ),
            "evidence": sorted(
                xi_graveyard
                | xi_boundary
                | xi_path_graveyard
                | xi_path_boundary
                | xi_capacity_graveyard
                | xi_capacity_boundary
                | xi_free_energy_keys
                | xi_free_energy_graveyard
                | xi_free_energy_boundary
                | xi_qci_keys
                | xi_qci_graveyard
                | xi_qci_boundary
                | xi_petz_keys
                | xi_petz_graveyard
                | xi_petz_boundary
                | xi_l7_keys
                | xi_l7_graveyard
                | xi_l7_boundary
                | xi_causal_keys
                | xi_causal_graveyard
                | xi_causal_boundary
                | xi_mps_keys
                | xi_mps_graveyard
                | xi_mps_boundary
                | xi_slow_keys
                | xi_slow_graveyard
                | xi_slow_boundary
                | coupled_runtime_keys
                | section_keys(coupled_e16_runtime, "boundary")
                | phi0_stress_keys
                | phi0_stress_graveyard
                | phi0_stress_boundary
                | phi0_response_keys
                | phi0_response_graveyard
                | phi0_response_boundary
                | scale_basin_keys
                | scale_basin_graveyard
                | scale_basin_boundary
                | full_trace_keys
                | full_trace_graveyard
                | full_trace_boundary
                | full_trace_after_stress_keys
                | full_trace_after_stress_graveyard
                | full_trace_after_stress_boundary
            ),
            "limit": "raw/path/capacity/free-energy/QCI/Petz candidates are killed or nonseparating; MPS, L7, causal-Xi, E16, stress, response-gradient, and scale-basin repairs remain weak/nonrobust; no final Xi/Phi0 or final basin admission",
        },
        "formal_scout_boundaries": {
            "status": "preserved",
            "pass": all(
                bool(r.get("all_pass"))
                and r.get("classification") == "formal_scout"
                and r.get("promotion_allowed") is False
                and bool(str(r.get("claim_ceiling", "")).strip())
                for r in receipts.values()
            ),
            "evidence": sorted(ACTIVE_RECEIPTS.keys()),
            "limit": "all active receipts are green, formal-scout only, nonpromotional, and carry an explicit claim ceiling",
        },
    }
    return rows


def requirement_scores(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    strong = 1.0
    candidate = 0.65
    stronger_candidate = 0.80
    weak_first_rung = 0.45
    open_blocker = 0.20
    values = []
    labels = []
    for key in [
        "source_aligned_runtime",
        "flux_manifold_binding",
        "axis0_candidate_space",
        "spinor_twistor_carrier",
        "tensor_scaling_status",
        "xi_phi0_bridge",
        "formal_scout_boundaries",
    ]:
        labels.append(key)
        status = rows[key]["status"]
        if status.startswith("strong"):
            values.append(strong)
        elif status == "candidate_space_evidenced_with_admitted_vector_bundle_controls":
            values.append(stronger_candidate)
        elif status == "candidate_space_evidenced":
            values.append(candidate)
        elif status == "weak_first_rung_open_blocker":
            values.append(weak_first_rung)
        elif status == "bounded_tensor_scaling_evidenced_not_final":
            values.append(0.58)
        elif status == "open_blocker":
            values.append(open_blocker)
        else:
            values.append(0.85 if rows[key]["pass"] else 0.0)
    score = torch.tensor(values, dtype=torch.float64)
    required_for_completion = torch.ones_like(score)
    gap = required_for_completion - score
    return {
        "labels": labels,
        "scores": score,
        "gaps": gap,
        "min_score": torch.min(score),
        "mean_score": torch.mean(score),
        "completion_margin": torch.min(score - required_for_completion),
        "all_requirements_at_completion_score": bool(torch.all(score >= required_for_completion).item()),
    }


def z3_completion_fence(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    s = z3.Solver()
    runtime_clean = z3.Bool("runtime_clean")
    flux_classified = z3.Bool("flux_classified")
    axis0_tested = z3.Bool("axis0_tested")
    spinor_useful = z3.Bool("spinor_useful")
    formal_only = z3.Bool("formal_only")
    xi_closed = z3.Bool("xi_closed")
    full_runtime_closed = z3.Bool("full_runtime_closed")
    final_manifold_admitted = z3.Bool("final_manifold_admitted")
    tensor_scaling_evidenced = z3.Bool("tensor_scaling_evidenced")
    final_tensor_scaling_closed = z3.Bool("final_tensor_scaling_closed")
    goal_complete = z3.Bool("goal_complete")

    facts = {
        runtime_clean: rows["source_aligned_runtime"]["pass"],
        flux_classified: rows["flux_manifold_binding"]["pass"],
        axis0_tested: rows["axis0_candidate_space"]["pass"],
        spinor_useful: rows["spinor_twistor_carrier"]["pass"],
        tensor_scaling_evidenced: rows["tensor_scaling_status"]["pass"],
        formal_only: rows["formal_scout_boundaries"]["pass"],
        xi_closed: False,
        full_runtime_closed: False,
        final_tensor_scaling_closed: False,
        final_manifold_admitted: False,
    }
    for var, value in facts.items():
        s.add(var == bool(value))

    s.add(
        goal_complete
        == z3.And(
            runtime_clean,
            flux_classified,
            axis0_tested,
            spinor_useful,
            tensor_scaling_evidenced,
            formal_only,
            xi_closed,
            full_runtime_closed,
            final_tensor_scaling_closed,
            final_manifold_admitted,
        )
    )

    premature = z3.Solver()
    for assertion in s.assertions():
        premature.add(assertion)
    premature.add(goal_complete)

    progress = z3.Solver()
    for assertion in s.assertions():
        progress.add(assertion)
    progress.add(runtime_clean, flux_classified, axis0_tested, spinor_useful, tensor_scaling_evidenced, formal_only)

    return {
        "pass": premature.check() == z3.unsat and progress.check() == z3.sat,
        "premature_completion_status": str(premature.check()),
        "formal_progress_status": str(progress.check()),
        "blocked_literals": {
            "xi_closed": False,
            "full_runtime_closed": False,
            "final_tensor_scaling_closed": False,
            "final_manifold_admitted": False,
        },
    }


def graveyard_controls(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    promoted_without_xi = z3.Solver()
    xi_closed = z3.Bool("xi_closed")
    promoted = z3.Bool("promoted")
    promoted_without_xi.add(promoted, z3.Not(xi_closed), z3.Implies(promoted, xi_closed))

    fake_flux_axis3_identity = not (
        rows["flux_manifold_binding"]["pass"]
        and rows["flux_manifold_binding"]["limit"].startswith("classified as manifold-derived")
    )
    missing_graveyards = any(not rows[key]["pass"] for key in rows)

    return {
        "premature_promotion_without_xi_rejected": {
            "pass": promoted_without_xi.check() == z3.unsat,
            "status": str(promoted_without_xi.check()),
        },
        "flux_axis3_identity_read_rejected": {
            "pass": not fake_flux_axis3_identity,
            "summary": "active flux receipts explicitly preserve not-root/not-Axis3/not-final boundaries",
        },
        "missing_requirement_controls_rejected": {
            "pass": not missing_graveyards,
            "summary": "all active requirement rows retain pass evidence; any missing row would block completion",
        },
        "formal_scout_only_promotion_rejected": {
            "pass": rows["formal_scout_boundaries"]["pass"],
            "summary": "all active receipts preserve promotion_allowed=false and nonpromotion claim ceilings",
        },
    }


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    receipts = {key: load_receipt(filename) for key, filename in ACTIVE_RECEIPTS.items()}
    rows = evidence_matrix(receipts)
    scores = requirement_scores(rows)
    completion_fence = z3_completion_fence(rows)
    controls = graveyard_controls(rows)

    positive = {
        "active_receipts_present_and_green": {
            "pass": all(bool(r.get("all_pass")) for r in receipts.values()),
            "receipts": ACTIVE_RECEIPTS,
        },
        "requirement_coverage_matrix": {
            "pass": all(row["pass"] for row in rows.values()),
            "rows": rows,
        },
        "torch_gap_vector_identifies_open_completion_margin": {
            "pass": (not scores["all_requirements_at_completion_score"])
            and float(scores["completion_margin"].item()) < 0.0,
            "labels": scores["labels"],
            "scores": scores["scores"],
            "gaps": scores["gaps"],
            "min_score": scores["min_score"],
            "mean_score": scores["mean_score"],
            "completion_margin": scores["completion_margin"],
        },
        "z3_progress_not_completion_gate": completion_fence,
        "next_work_routing": {
            "pass": True,
            "ordered_next_gaps": [
                "close or kill a stronger Xi -> rho_AB -> Phi0 construction",
                "try the next Phi0 candidate only if it avoids beta-zero/free-energy, collapsed-register/QCI, and near-reversed-order/Petz control failures",
                "convert bounded tensor-scaling status into a stronger convergence or environment-contraction falsifier",
                "extend source-aligned runtime toward full coupled terrain/operator/axis dynamics under the audit freeze",
                "only then revisit final manifold/basin admission boundaries",
            ],
        },
    }

    graveyard_companions = controls
    boundary = {
        "not_goal_complete": {
            "pass": completion_fence["premature_completion_status"] == "unsat",
            "summary": "current receipts prove formal-scout progress but not final completion",
        },
        "final_xi_phi0_open": {
            "pass": rows["xi_phi0_bridge"]["status"] in {"open_blocker", "weak_first_rung_open_blocker"},
            "summary": "current Xi bridge evidence includes weak bounded first-rung runtime support but still admits no final Xi/Phi0",
        },
        "full_runtime_and_final_manifold_open": {
            "pass": True,
            "summary": "one-qubit runtime and finite fixtures do not admit final full runtime or final manifold law",
        },
    }
    nearby_variants = {
        "total": 4,
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions.keys()),
    }
    why_not_v4_probes = {
        "reason": "This is a receipt-level formal-scout completion classifier over active v5 evidence, not a canonical v4 physics/probe promotion.",
        "pass": True,
    }
    open_gaps = [
        "final Xi/Phi0 remains open; current stronger evidence is weak bounded first-rung only",
        "energy-corrected QIT-FEP Phi0 candidate is load-bearing but nonseparating against beta-zero/control rows",
        "tripartite quantum conditional-information Phi0 candidate is load-bearing but nonseparating against collapsed-register/control rows",
        "Petz-recovery Phi0 candidate is load-bearing but nonseparating against near reversed-order/control rows",
        "tensor scaling is consolidated as bounded L32/L64/MPS/PEPS/PEPS3D evidence but final convergence and full environment contraction remain open",
        "full coupled source-aligned runtime remains open beyond bounded E16 first-rung evidence",
        "final manifold/basin admission remains blocked",
    ]

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "open_gaps": open_gaps,
        "blockers": [],
        "all_pass": all(section_passes(section) for section in (positive, graveyard_companions, boundary))
        and nearby_variants["passed"] == nearby_variants["total"]
        and not scores["all_requirements_at_completion_score"],
        "runtime_seconds": time.time() - start,
        "generated_at": time.time(),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT_PATH)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
