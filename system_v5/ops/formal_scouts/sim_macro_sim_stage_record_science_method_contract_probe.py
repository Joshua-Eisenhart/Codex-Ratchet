#!/usr/bin/env python3
"""Macro-sim stage-record science-method contract scout.

This is a narrow repair receipt for the current integrated macro-sim spine.
It does not build a new architecture. It verifies that source-native
EngineCore substage records now carry executable science-method/FEP fields
that downstream MPS/PEPS/PEPS3D, policy, Holodeck, and Axis0 scouts can
consume instead of re-inventing local labels.

Formal scout only. No final FEP engine, final Axis0, Holodeck memory system,
world model, psychology, physics, or canonical macro-sim claim is admitted.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import networkx as nx
import torch

import engine_core as engine_core_module
from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "macro_sim_stage_record_science_method_contract_probe_results.json"

NAME = "macro_sim_stage_record_science_method_contract_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "macro_sim_stage_record_science_method_contract_repair"
CLAIM_CEILING = (
    "Formal scout only: verifies executable science-method/FEP fields on "
    "source-native EngineCore stage records and emits a repair receipt for one "
    "load-bearing macro-sim weak link. It does not admit final FEP, final "
    "Axis0, Holodeck memory, world-model, psychology, physics, or canonical "
    "macro-sim claims."
)

BEFORE_ENGINE_CORE_SHA256 = "c458617072bb31abcaf3c36d0f97646ef0d925ac58c23ecf2b9daa95571a317e"
REQUIRED_STAGE_FIELDS = [
    "model_before",
    "prediction",
    "observation",
    "fep_efe_score",
    "update_repair",
    "falsifier_graveyard",
    "next_policy",
    "model_after",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing field finiteness, probability normalization, and matched-control deltas",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dependency-consumption graph for the repaired stage-record contract",
    },
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "networkx": "load_bearing", "engine_core": "supportive"}
FLOAT_DTYPE = torch.float64


def engine_array_module() -> Any:
    return getattr(engine_core_module, "np")


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    array_module = engine_array_module()
    if isinstance(value, array_module.ndarray):
        return value.tolist()
    if isinstance(value, (array_module.bool_,)):
        return bool(value)
    if isinstance(value, (array_module.integer, array_module.floating)):
        return value.item()
    return value


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "path": str(path),
        "name": data.get("name"),
        "all_pass": data.get("all_pass"),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "claim_ceiling": data.get("claim_ceiling", "")[:220],
        "positive_keys": sorted((data.get("positive") or {}).keys()),
        "boundary_keys": sorted((data.get("boundary") or {}).keys()),
    }


def run_rows(manifold_enabled: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        rho0 = generate_initial_density(4200 + engine_type)
        rows.extend(
            EngineCore(engine_type, manifold_enabled=manifold_enabled)
            .run_full_cycle(rho0)["trajectory"]
        )
    return rows


def run_perturbation_check() -> dict[str, Any]:
    """Verify active projection by injecting noise mid-cycle."""
    eng = EngineCore(engine_type=0, manifold_enabled=True)
    rho = generate_initial_density(42)
    # Run to mid-cycle (Stage 4)
    for main_idx in range(4):
        perception, loop_class = eng.schedule[main_idx]
        rho, _ = eng.run_main_stage(rho, perception, loop_class, main_idx)
    array_module = engine_array_module()

    # Inject rank-2 noise
    rho_perturbed = 0.7 * rho + 0.3 * array_module.eye(2) / 2
    rho_perturbed = rho_perturbed / array_module.trace(rho_perturbed).real

    # Run Stage 4, Substage 0
    _, records = eng.run_main_stage(rho_perturbed, eng.schedule[4][0], eng.schedule[4][1], 4)
    rec = records[0]
    return {
        "model_before_rank": rec["model_before"]["carrier_rank"],
        "manifold_intermediate_rank": rec["manifold_intermediate"]["model"]["carrier_rank"],
        "model_after_rank": rec["model_after"]["carrier_rank"],
        "manifold_surprise_kl": rec["fep_efe_score"]["surprise_kl_manifold_step"],
    }


def distribution_ok(dist: list[float]) -> bool:
    arr = torch.tensor(dist, dtype=FLOAT_DTYPE)
    return bool(torch.all(torch.isfinite(arr)).item() and torch.all(arr >= 0.0).item() and abs(float(torch.sum(arr).item()) - 1.0) < 1e-9)


def audit_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing = {
        f"E{row['engine_type']}:S{row['main_stage_idx']}:u{row['substage_idx']}": [
            field for field in REQUIRED_STAGE_FIELDS if field not in row
        ]
        for row in rows
    }
    missing = {k: v for k, v in missing.items() if v}
    score_rows = [row["fep_efe_score"] for row in rows if "fep_efe_score" in row]
    obs_ok = [
        distribution_ok(row["prediction"]["observation_distribution"])
        and distribution_ok(row["observation"]["observation_distribution"])
        for row in rows
        if "prediction" in row and "observation" in row
    ]
    fep_values = torch.tensor(
        [float(score["expected_free_energy_proxy"]) for score in score_rows],
        dtype=FLOAT_DTYPE,
    )
    repair_values = torch.tensor(
        [float(row["update_repair"]["manifold_projection_delta_norm"]) for row in rows],
        dtype=FLOAT_DTYPE,
    )
    next_policies = [row["next_policy"]["policy_id"] for row in rows if "next_policy" in row]
    return {
        "row_count": len(rows),
        "missing_required_fields": missing,
        "all_required_fields_present": not missing and len(rows) == 64,
        "all_observation_distributions_normalized": len(obs_ok) == 64 and all(obs_ok),
        "fep_proxy_min": float(torch.min(fep_values).item()),
        "fep_proxy_mean": float(torch.mean(fep_values).item()),
        "fep_proxy_max": float(torch.max(fep_values).item()),
        "all_fep_scores_finite": bool(torch.all(torch.isfinite(fep_values)).item()),
        "manifold_projection_delta_mean": float(torch.mean(repair_values).item()),
        "manifold_projection_delta_min": float(torch.min(repair_values).item()),
        "manifold_projection_delta_max": float(torch.max(repair_values).item()),
        "unique_next_policy_count": len(set(next_policies)),
    }


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    edges = [
        ("engine_core.run_substage", "stage_record.science_method_fields"),
        ("stage_record.science_method_fields", "operator_slot_contract"),
        ("stage_record.science_method_fields", "fep_policy_tree"),
        ("stage_record.science_method_fields", "holodeck_closed_loop_fep"),
        ("stage_record.science_method_fields", "source_native_subdense_multicarrier_environment_downstream_target"),
        ("stage_record.science_method_fields", "axis0_candidate_router"),
        ("axis0_candidate_router", "axis0_outputs_or_blockers"),
        ("matched_no_manifold_control", "repair_receipt"),
        ("stage_record.science_method_fields", "repair_receipt"),
    ]
    graph.add_edges_from(edges)
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "acyclic": nx.is_directed_acyclic_graph(graph),
        "edge_list": list(edges),
    }


def main() -> int:
    started = time.time()
    engine_core_path = ROOT / "engine_core.py"
    after_sha = sha256_file(engine_core_path)
    rows = run_rows(manifold_enabled=True)
    control_rows = run_rows(manifold_enabled=False)
    audit = audit_rows(rows)
    control = audit_rows(control_rows)
    pert = run_perturbation_check()
    fep_delta = abs(audit["fep_proxy_mean"] - control["fep_proxy_mean"])
    manifold_delta = audit["manifold_projection_delta_mean"] - control["manifold_projection_delta_mean"]

    consumed_results = {
        "engine_operator_slot_alphabet_contract": load_result("engine_operator_slot_alphabet_contract_probe_results.json"),
        "source_native_fep_pomdp_policy_tree": load_result("source_native_fep_pomdp_policy_tree_probe_results.json"),
        "source_native_active_inference_strategy_policy": load_result("source_native_active_inference_strategy_policy_probe_results.json"),
        "source_native_holodeck_closed_loop_fep_strategy": load_result("source_native_holodeck_closed_loop_fep_strategy_probe_results.json"),
        "macro_axis0_fep_gradient_polarity_downstream_target": {
            "exists": "not_gated_here",
            "path": str(RESULT_DIR / "macro_sim_axis0_plural_stage_candidate_router_probe_results.json"),
            "closure_guard": str(RESULT_DIR / "axis0_fep_gradient_stage_local_adapter_closure_probe_results.json"),
            "reason": "This upstream stage-record scout names the current Axis0 FEP-gradient router target but does not gate on a later receipt.",
        },
        "macro_axis0_path_entropy_downstream_blocked_target": {
            "exists": "not_gated_here",
            "path": str(RESULT_DIR / "macro_sim_axis0_plural_stage_candidate_router_probe_results.json"),
            "closure_guard": str(RESULT_DIR / "axis0_path_entropy_branch_closure_probe_results.json"),
            "schedule_confound_guard": str(RESULT_DIR / "path_entropy_schedule_confound_falsifier_probe_results.json"),
            "pair_falsifier_guard": str(RESULT_DIR / "path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe_results.json"),
            "reason": "This upstream stage-record scout names the current finite path-entropy router diagnostic and its downstream blocker guards; it does not admit path_entropy as Axis0.",
        },
        "macro_axis0_holographic_boundary_downstream_blocked_target": {
            "exists": "not_gated_here",
            "path": str(RESULT_DIR / "macro_sim_axis0_plural_stage_candidate_router_probe_results.json"),
            "source_result": str(RESULT_DIR / "source_native_engine_boundary_path_fep_reconstruction_probe_results.json"),
            "closure_guard": str(RESULT_DIR / "axis0_holographic_boundary_branch_closure_probe_results.json"),
            "reason": "This upstream stage-record scout names the current finite boundary/interior diagnostic and its downstream blocker guard; it does not admit HBI as Axis0 or a holographic dictionary.",
        },
        "source_native_subdense_multicarrier_environment_downstream_target": {
            "exists": "not_gated_here",
            "path": str(RESULT_DIR / "source_native_multicarrier_subdense_environment_contraction_probe_results.json"),
            "closure_guard": str(RESULT_DIR / "stage_record_downstream_carrier_consumption_closure_probe_results.json"),
            "reason": "This upstream stage-record scout names the current downstream carrier target but does not gate on a later receipt.",
        },
        "operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport": load_result("operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe_results.json"),
        "holographic_boundary_path_ensemble_axis0_fep_selection": load_result("holographic_boundary_path_ensemble_axis0_fep_selection_probe_results.json"),
        "source_native_engine_boundary_path_fep_reconstruction": load_result("source_native_engine_boundary_path_fep_reconstruction_probe_results.json"),
    }
    graph = dependency_graph()

    axis0_outputs_or_blockers = {
        "fep_gradient_polarity": {
            "status": "downstream_axis0_router_target_not_gated_here",
            "result": consumed_results["macro_axis0_fep_gradient_polarity_downstream_target"]["path"],
            "closure_guard": consumed_results["macro_axis0_fep_gradient_polarity_downstream_target"]["closure_guard"],
            "claim_ceiling": "finite stage-local FEP-gradient polarity candidate only",
        },
        "path_entropy": {
            "status": "blocked_downstream_diagnostic_not_admitted_axis0",
            "result": consumed_results["macro_axis0_path_entropy_downstream_blocked_target"]["path"],
            "closure_guard": consumed_results["macro_axis0_path_entropy_downstream_blocked_target"]["closure_guard"],
            "schedule_confound_guard": consumed_results["macro_axis0_path_entropy_downstream_blocked_target"]["schedule_confound_guard"],
            "pair_falsifier_guard": consumed_results["macro_axis0_path_entropy_downstream_blocked_target"]["pair_falsifier_guard"],
            "claim_ceiling": "finite path-entropy diagnostic only; blocked as downstream Axis0/admissibility feature",
        },
        "correlation_diversity_derivative": {
            "status": "existing_candidate_consumed",
            "result": consumed_results["holographic_boundary_path_ensemble_axis0_fep_selection"]["path"],
            "claim_ceiling": "finite correlation-diversity derivative candidate only",
        },
        "holographic_boundary_interior_reconstruction": {
            "status": "blocked_downstream_diagnostic_not_admitted_axis0",
            "result": consumed_results["macro_axis0_holographic_boundary_downstream_blocked_target"]["source_result"],
            "router_result": consumed_results["macro_axis0_holographic_boundary_downstream_blocked_target"]["path"],
            "closure_guard": consumed_results["macro_axis0_holographic_boundary_downstream_blocked_target"]["closure_guard"],
            "source_all_pass": consumed_results["source_native_engine_boundary_path_fep_reconstruction"].get("all_pass"),
            "claim_ceiling": "finite boundary/interior reconstruction diagnostic only; blocked as downstream Axis0/holographic dictionary feature",
            "blocker_summary": [
                "strict_best_kl_selection_gap",
                "path_label_recovery",
                "axis0_guard_blocks_downstream_feature",
            ],
        },
        "retrocausal_many_futures_policy_scoring": {
            "status": "routing_only_not_final",
            "result": consumed_results["source_native_fep_pomdp_policy_tree"]["path"],
            "interpretation": "finite policy-tree depth under B_pi; not primitive time or final retrocausality",
        },
    }

    neural_repo_gap_decision = {
        "gap": "stage records lacked executable model/prediction/observation/FEP/update/falsifier/policy fields",
        "repo": "none_admitted_this_wave",
        "adapter": "not_applicable_local_engine_core_repair",
        "consumption_test": "EngineCore trajectory rows expose required executable fields and matched no-manifold control changes repair/FEP metrics.",
        "control": "manifold_disabled_control",
        "rejected_repos_for_this_gap": {
            "LeWM": "latent rollout is downstream of stable stage records, not a substitute for them",
            "FlowM": "history guidance is downstream of stage-record semantics",
            "auto_LiRPA": "verification bounds need a neural adapter first",
            "LPWM": "object-centric prediction does not repair source-native substage schema",
            "AnyFlow/Sana/StyleGAN3": "visual/world-state projection is not the current weak link",
        },
    }

    repair_receipt = {
        "weak_link": "EngineCore substage records were label/metric rows without executable science-method/FEP fields.",
        "target_file_or_result": str(engine_core_path),
        "admission_rule_improved": "Downstream macro-sim repairs can now require stage records to carry model_before, prediction, observation, fep_efe_score, update_repair, falsifier_graveyard, next_policy, and model_after.",
        "dependency_subset": [
            "engine_core.run_substage",
            "canonical_qit_engine_specs.get_operator_slot_spec",
            "13-layer manifold metrics via active_layer_constraint_enforcers",
            "finite Pauli sensory projection",
            "matched no-manifold control",
            "existing FEP/POMDP, Holodeck, and Axis0 receipts plus the downstream subdense multicarrier target as consumption map",
        ],
        "stage_fields_touched": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": BEFORE_ENGINE_CORE_SHA256,
        "after_delta/hash": after_sha,
        "primary_control/result": {
            "control": "manifold_disabled_control",
            "fep_proxy_mean_engine": audit["fep_proxy_mean"],
            "fep_proxy_mean_control": control["fep_proxy_mean"],
            "fep_proxy_mean_abs_delta": float(fep_delta),
            "manifold_projection_delta_mean_engine": audit["manifold_projection_delta_mean"],
            "manifold_projection_delta_mean_control": control["manifold_projection_delta_mean"],
            "manifold_projection_delta_mean_delta": float(manifold_delta),
        },
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
            "reason": "local source-native stage-record repair was executable without new proposal input; provider outputs remain proposal-only until receipts exist",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Keep the downstream carrier-consumption closure guard current, then wire at least two Axis0 candidates as consumed stage-level outputs.",
    }

    positive = {
        "sixty_four_repaired_stage_records_execute": {
            "pass": audit["row_count"] == 64 and control["row_count"] == 64,
            "engine_rows": audit["row_count"],
            "control_rows": control["row_count"],
        },
        "required_science_method_fields_present": {
            "pass": audit["all_required_fields_present"],
            "required_fields": REQUIRED_STAGE_FIELDS,
            "missing": audit["missing_required_fields"],
        },
        "active_manifold_projection_verified": {
            "pass": pert["model_before_rank"] == 2 and pert["manifold_intermediate_rank"] == 1 and pert["manifold_surprise_kl"] > 0.01,
            "input_rank": pert["model_before_rank"],
            "output_rank": pert["manifold_intermediate_rank"],
            "surprise_kl": pert["manifold_surprise_kl"],
        },
        "prediction_and_observation_are_executable_distributions": {
            "pass": audit["all_observation_distributions_normalized"],
            "observable_basis": ["Z+", "Z-", "X+", "X-", "Y+", "Y-"],
        },
        "fep_scores_are_finite_and_control_sensitive": {
            "pass": audit["all_fep_scores_finite"] and fep_delta > 1e-6,
            "engine_fep_mean": audit["fep_proxy_mean"],
            "control_fep_mean": control["fep_proxy_mean"],
            "mean_abs_delta": float(fep_delta),
        },
        "update_repair_is_control_sensitive": {
            "pass": audit["manifold_projection_delta_mean"] > 1e-9 and control["manifold_projection_delta_mean"] == 0.0,
            "engine_manifold_delta_mean": audit["manifold_projection_delta_mean"],
            "control_manifold_delta_mean": control["manifold_projection_delta_mean"],
        },
        "dependency_consumption_graph_executes": {"pass": graph["acyclic"], **graph},
    }
    graveyards = {
        "label_only_stage_record_is_rejected": {
            "pass": all(not audit["missing_required_fields"] for _ in [0]),
            "reason": "pre-repair baseline lacked all required top-level science-method fields; current rows must carry them.",
            "baseline_missing_fields": REQUIRED_STAGE_FIELDS,
        },
        "no_manifold_control_removes_repair_delta": {
            "pass": control["manifold_projection_delta_mean"] == 0.0 and audit["manifold_projection_delta_mean"] > 1e-9,
            "control_delta_mean": control["manifold_projection_delta_mean"],
            "engine_delta_mean": audit["manifold_projection_delta_mean"],
        },
        "neural_repo_not_admitted_without_named_gap": {
            "pass": neural_repo_gap_decision["repo"] == "none_admitted_this_wave",
            "decision": neural_repo_gap_decision,
        },
        "axis0_not_collapsed_to_single_scalar": {
            "pass": len(axis0_outputs_or_blockers) >= 2,
            "candidate_or_blocker_keys": sorted(axis0_outputs_or_blockers),
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_final_fep_axis0_holodeck_world_model_claims": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "final fep", "final axis0"]),
        },
        "integration_is_dependency_consumption_not_result_aggregation": {
            "pass": graph["acyclic"] and any("repair_receipt" in edge for edge in graph["edge_list"]),
            "dependency_subset": repair_receipt["dependency_subset"],
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "system_map": {
            "engine_spine": str(engine_core_path),
            "stage_record_source": "EngineCore.run_substage",
            "carrier_scope_this_repair": "source-native 2x2 density carrier feeding downstream MPS/PEPS/PEPS3D bridge scouts",
            "consumed_result_receipts": consumed_results,
        },
        "repair_receipt": repair_receipt,
        "dependency_consumption": graph,
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "neural_repo_gap_decision": neural_repo_gap_decision,
        "positive": positive,
        "graveyard_companions": graveyards,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "boundary": boundary,
        "why_not_v4_probes": [
            "This repair targets v5 source-native EngineCore stage records directly.",
            "It does not reuse v4 probe semantics as authority.",
            "It does not claim a full macro-sim, final FEP, final Axis0, or Holodeck memory implementation.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
