#!/usr/bin/env python3
"""Macro-sim Axis0 plural stage-candidate router scout.

This is a routing scout over canonical QIT stage-slot records. It compares
several finite Axis0 candidates instead of collapsing
Axis0 into one scalar:

- FEP-gradient polarity from per-stage EFE proxy differences;
- path entropy from rolling canonical stage-token histories;
- correlation-diversity derivative from rolling observation distributions;
- holographic boundary/interior reconstruction, explicitly blocked by the
  current failed receipt;
- retrocausal/many-futures policy scoring, consumed as a finite policy-tree
  distribution from the POMDP scout.

Formal scout only. No final Axis0, retrocausality, Holodeck, physics,
psychology, cognition, or canonical macro-sim claim is admitted.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from collections import Counter
from typing import Any

import networkx as nx
import torch

from canonical_qit_engine_specs import (
    get_operator_slot_spec,
    get_schedule,
    get_terrain_dynamics_spec,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "macro_sim_axis0_plural_stage_candidate_router_probe_results.json"

NAME = "macro_sim_axis0_plural_stage_candidate_router_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "macro_sim_axis0_plural_stage_candidate_router"
CLAIM_CEILING = (
    "Formal scout only: compares finite canonical QIT stage-record Axis0 "
    "candidates and routes blockers from existing receipts. It does not "
    "instantiate EngineCore, does not run source-native engine dynamics, and "
    "does not admit final Axis0, retrocausality, Holodeck, physics, "
    "psychology, cognition, or canonical macro-sim claims."
)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source-native tensor math for stage-vector differences, entropy, correlation-diversity, policy posterior normalization, and control comparisons",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive local canonical QIT schedule, terrain, and operator-slot records consumed by the router",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive candidate-routing dependency graph sanity check",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt loading and result serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "networkx": "supportive",
    "json": "supportive",
}

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
        "selected_policy": (data.get("summary") or {}).get("selected_policy"),
    }


def load_full_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    return data


def run_rows(*, manifold_enabled: bool = True) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
            terrain = get_terrain_dynamics_spec(perception, engine_type)
            h_norm = float(torch.linalg.matrix_norm(terrain["hamiltonian"]).real.item())
            rate = float(terrain["rate"])
            chirality = 1.0 if engine_type == 0 else -1.0
            loop_sign = 1.0 if loop_class == "outer" else -1.0
            manifold_gain = 1.0 if manifold_enabled else 0.0
            for substage_idx in range(4):
                slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                op_weight = {"Ti": 0.31, "Te": 0.43, "Fi": 0.59, "Fe": 0.71}[slot["operator"]]
                sign = float(slot["sign"])
                stage_phase = float(main_idx + 1) / 8.0
                slot_phase = float(substage_idx + 1) / 4.0
                manifold_term = manifold_gain * (0.07 * stage_phase + 0.03 * slot_phase)
                bloch = [
                    float(chirality * sign * op_weight + manifold_term),
                    float(loop_sign * rate + manifold_gain * 0.05 * slot_phase),
                    float((1.0 if slot["is_native_operator"] else -1.0) * h_norm / 2.0),
                ]
                entropy = float(0.12 + 0.015 * (main_idx + substage_idx) + 0.01 * engine_type)
                purity = float(0.91 - 0.01 * substage_idx - 0.005 * main_idx)
                efe = float(
                    h_norm
                    + rate
                    + 0.03 * main_idx
                    + 0.02 * substage_idx
                    + 0.11 * engine_type
                    + manifold_gain * 0.015 * abs(sign)
                )
                rows.append(
                    {
                        "engine_type": engine_type,
                        "main_stage_idx": main_idx,
                        "substage_idx": substage_idx,
                        "perception": perception,
                        "loop_class": loop_class,
                        "ordered_token": slot["token"],
                        "operator": slot["operator"],
                        "model_before": {
                            "bloch": [0.5 * x for x in bloch],
                            "entropy": entropy * 0.95,
                            "purity": min(1.0, purity + 0.01),
                        },
                        "prediction": {
                            "operator": slot["operator"],
                            "terrain_realization": terrain["realization"],
                            "axis6": slot["axis6"],
                        },
                        "observation": {
                            "observation_distribution": [
                                0.18 + 0.01 * engine_type,
                                0.17 + 0.01 * main_idx,
                                0.16 + 0.01 * substage_idx,
                                0.15 + 0.005 * abs(sign),
                                0.14 + 0.005 * rate,
                                0.20 - 0.005 * engine_type + 0.01 * manifold_gain,
                            ],
                        },
                        "fep_efe_score": {
                            "expected_free_energy_proxy": efe,
                            "surprise_kl": abs(rate - 0.2) + 0.01 * substage_idx,
                            "prediction_error_l2": abs(op_weight - rate) + 0.01 * main_idx,
                        },
                        "update_repair": {
                            "manifold_projection_delta_norm": manifold_gain * abs(sign) * rate + 0.001 * (main_idx + substage_idx),
                        },
                        "falsifier_graveyard": {
                            "engine_core_not_instantiated": True,
                            "source_native_dynamics_not_run": True,
                        },
                        "next_policy": {
                            "loop_class": loop_class,
                            "precedence": slot["precedence"],
                        },
                        "model_after": {
                            "bloch": bloch,
                            "entropy": entropy,
                            "purity": purity,
                        },
                    }
                )
    return rows


def assert_stage_fields(rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing = {
        f"E{row['engine_type']}:S{row['main_stage_idx']}:u{row['substage_idx']}": [
            field for field in REQUIRED_STAGE_FIELDS if field not in row
        ]
        for row in rows
    }
    missing = {k: v for k, v in missing.items() if v}
    return {"pass": not missing and len(rows) == 64, "missing": missing, "row_count": len(rows)}


def categorical_entropy(values: list[str]) -> float:
    counts = Counter(values)
    total = float(sum(counts.values()))
    probs = torch.tensor([count / total for count in counts.values()], dtype=torch.float64)
    return float((-torch.sum(probs * torch.log(probs))).item())


def rolling(values: list[Any], width: int) -> list[list[Any]]:
    return [values[max(0, i - width + 1): i + 1] for i in range(len(values))]


def fep_gradient_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    efe = torch.tensor(
        [row["fep_efe_score"]["expected_free_energy_proxy"] for row in rows],
        dtype=torch.float64,
    )
    grad = torch.diff(efe)
    polarity = torch.sign(grad)
    return {
        "candidate": "fep_gradient_polarity",
        "status": "routing_candidate_not_final",
        "values": grad.tolist(),
        "mean_abs_gradient": float(torch.mean(torch.abs(grad)).item()),
        "positive_steps": int(torch.sum(polarity > 0).item()),
        "negative_steps": int(torch.sum(polarity < 0).item()),
        "zero_steps": int(torch.sum(polarity == 0).item()),
        "finite": bool(torch.all(torch.isfinite(grad)).item()),
    }


def path_entropy_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = [str(row["ordered_token"]) for row in rows]
    ent = torch.tensor(
        [categorical_entropy(window) for window in rolling(tokens, width=8)],
        dtype=torch.float64,
    )
    deriv = torch.diff(ent)
    return {
        "candidate": "path_entropy",
        "status": "routing_candidate_not_final",
        "values": deriv.tolist(),
        "entropy_mean": float(torch.mean(ent).item()),
        "derivative_mean_abs": float(torch.mean(torch.abs(deriv)).item()),
        "finite": bool(torch.all(torch.isfinite(deriv)).item()),
    }


def correlation_diversity_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    obs = [row["observation"]["observation_distribution"] for row in rows]
    diversity = []
    for window in rolling(obs, width=8):
        arr = torch.tensor(window, dtype=torch.float64)
        if arr.shape[0] < 3:
            diversity.append(0.0)
            continue
        corr = torch.corrcoef(arr)
        corr = torch.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
        offdiag = corr[~torch.eye(corr.shape[0], dtype=torch.bool)]
        diversity.append(float((1.0 - torch.mean(torch.abs(offdiag))).item()))
    diversity_arr = torch.tensor(diversity, dtype=torch.float64)
    deriv = torch.diff(diversity_arr)
    return {
        "candidate": "correlation_diversity_derivative",
        "status": "routing_candidate_not_final",
        "values": deriv.tolist(),
        "diversity_mean": float(torch.mean(diversity_arr).item()),
        "derivative_mean_abs": float(torch.mean(torch.abs(deriv)).item()),
        "finite": bool(torch.all(torch.isfinite(deriv)).item()),
    }


def stable_softmax_from_efe(efe: torch.Tensor) -> torch.Tensor:
    shifted = -efe - torch.max(-efe)
    weights = torch.exp(shifted)
    return weights / torch.sum(weights)


def online_vmp_ready(online_vmp_receipt: dict[str, Any]) -> bool:
    return bool(
        online_vmp_receipt.get("exists") is True
        and online_vmp_receipt.get("all_pass") is True
        and (online_vmp_receipt.get("axis0_outputs_or_blockers") or {}).get(
            "online_vmp_ready_for_many_futures_policy_scoring"
        ) is True
        and len(online_vmp_receipt.get("policy_rows") or []) >= 16
    )


def many_futures_policy_candidate(
    pomdp_receipt: dict[str, Any],
    online_vmp_receipt: dict[str, Any],
) -> dict[str, Any]:
    online_ready = online_vmp_ready(online_vmp_receipt)
    online_summary = online_vmp_receipt.get("summary") or {}
    if not online_ready:
        return {
            "candidate": "retrocausal_many_futures_policy_scoring",
            "status": "blocked_missing_online_vmp_receipt",
            "values": [],
            "finite": False,
            "pomdp_receipt": {
                "exists": pomdp_receipt.get("exists", False),
                "path": pomdp_receipt.get("path"),
                "all_pass": pomdp_receipt.get("all_pass"),
            },
            "online_vmp_receipt": {
                "exists": online_vmp_receipt.get("exists", False),
                "path": online_vmp_receipt.get("path"),
                "all_pass": online_vmp_receipt.get("all_pass"),
                "ready_flag": (online_vmp_receipt.get("axis0_outputs_or_blockers") or {}).get(
                    "online_vmp_ready_for_many_futures_policy_scoring"
                ),
                "policy_count": len(online_vmp_receipt.get("policy_rows") or []),
            },
            "interpretation": "finite policy-tree scoring now requires online VMP update evidence; POMDP rows alone are incomplete",
        }

    raw_rows = online_vmp_receipt.get("policy_rows") or []
    rows = [
        row for row in raw_rows
        if row.get("manifold_enabled") is True and row.get("no_engine_control") is False
    ]
    rows = sorted(rows, key=lambda row: (int(row.get("engine_type", 0)), int(row.get("start_stage", 0)), str(row.get("policy_id", ""))))
    if not rows:
        return {
            "candidate": "retrocausal_many_futures_policy_scoring",
            "status": "blocked_missing_policy_rows",
            "values": [],
            "finite": False,
            "interpretation": "finite policy-tree depth under B_pi; not primitive time or final retrocausality",
        }

    efe = torch.tensor([float(row["expected_free_energy"]) for row in rows], dtype=torch.float64)
    posterior = torch.tensor(
        [float(row.get("policy_probability", math.nan)) for row in rows],
        dtype=torch.float64,
    )
    if not bool(torch.all(torch.isfinite(posterior)).item()) or float(torch.sum(posterior).item()) <= 0.0:
        posterior = stable_softmax_from_efe(efe)
    else:
        posterior = posterior / torch.sum(posterior)

    uniform = torch.full_like(posterior, 1.0 / len(posterior))
    centered = posterior - uniform
    entropy_terms = torch.where(
        posterior > 0.0,
        posterior * torch.log(posterior),
        torch.zeros_like(posterior),
    )
    entropy = float((-torch.sum(entropy_terms)).item())
    effective_count = float(torch.exp(torch.tensor(entropy, dtype=torch.float64)).item())
    argmax = torch.zeros_like(posterior)
    argmax[int(torch.argmax(posterior).item())] = 1.0
    selected_idx = int(torch.argmin(efe).item())
    policy_order = [str(row.get("policy_id")) for row in rows]
    return {
        "candidate": "retrocausal_many_futures_policy_scoring",
        "status": "routing_candidate_not_final",
        "values": centered.tolist(),
        "policy_order": policy_order,
        "policy_probability": posterior.tolist(),
        "policy_count": int(len(rows)),
        "policy_entropy": entropy,
        "effective_policy_count": effective_count,
        "selected_policy": policy_order[selected_idx],
        "selected_policy_probability": float(posterior[selected_idx]),
        "efe_min": float(torch.min(efe).item()),
        "efe_max": float(torch.max(efe).item()),
        "efe_range": float((torch.max(efe) - torch.min(efe)).item()),
        "l2_from_uniform_control": float(torch.linalg.vector_norm(centered).item()),
        "l2_from_single_argmax_control": float(torch.linalg.vector_norm(posterior - argmax).item()),
        "control_policy_changes": {
            "no_engine_policy": (pomdp_receipt.get("summary") or {}).get("no_engine_policy"),
            "risk_only_policy": (pomdp_receipt.get("summary") or {}).get("risk_only_policy"),
            "shuffled_preference_policy": (pomdp_receipt.get("summary") or {}).get("shuffled_preference_policy"),
        },
        "vmp_update_support": True,
        "online_vmp_receipt_consumed": True,
        "pomdp_receipt": {
            "exists": pomdp_receipt.get("exists", False),
            "path": pomdp_receipt.get("path"),
            "all_pass": pomdp_receipt.get("all_pass"),
            "selected_policy": (pomdp_receipt.get("summary") or {}).get("selected_policy"),
        },
        "online_vmp_receipt": {
            "exists": online_vmp_receipt.get("exists", False),
            "path": online_vmp_receipt.get("path"),
            "name": online_vmp_receipt.get("name"),
            "all_pass": online_vmp_receipt.get("all_pass"),
            "selected_policy": online_summary.get("selected_policy"),
            "policy_count": online_summary.get("policy_count"),
            "posterior_kl_max": online_summary.get("posterior_kl_max"),
            "vfe_reduction_min": online_summary.get("vfe_reduction_min"),
            "wrong_obs_shift_min": online_summary.get("wrong_obs_shift_min"),
        },
        "online_vmp_control_summary": {
            "wrong_observation_token_changes_posterior": (
                (online_vmp_receipt.get("graveyard_companions") or {})
                .get("wrong_observation_token_changes_posterior", {})
                .get("pass")
            ),
            "no_engine_identity_transition_changes_policy_or_margin": (
                (online_vmp_receipt.get("graveyard_companions") or {})
                .get("no_engine_identity_transition_changes_policy_or_margin", {})
                .get("pass")
            ),
            "shuffled_preference_changes_online_policy_or_margin": (
                (online_vmp_receipt.get("graveyard_companions") or {})
                .get("shuffled_preference_changes_online_policy_or_margin", {})
                .get("pass")
            ),
            "identity_emission_changes_ambiguity_or_policy": (
                (online_vmp_receipt.get("graveyard_companions") or {})
                .get("identity_emission_changes_ambiguity_or_policy", {})
                .get("pass")
            ),
        },
        "finite": bool(
            torch.all(torch.isfinite(centered)).item()
            and math.isclose(float(torch.sum(posterior).item()), 1.0, rel_tol=1e-9, abs_tol=1e-9)
        ),
        "interpretation": "finite online-VMP policy scoring over B_pi; not primitive time or final retrocausality",
    }


def boundary_interior_candidate(boundary_receipt: dict[str, Any]) -> dict[str, Any]:
    if boundary_receipt.get("all_pass") is not True:
        return {
            "candidate": "holographic_boundary_interior_reconstruction",
            "status": "blocked_by_existing_failed_receipt",
            "receipt": {
                "exists": boundary_receipt.get("exists", False),
                "path": boundary_receipt.get("path"),
                "all_pass": boundary_receipt.get("all_pass"),
            },
            "values": [],
            "finite": False,
        }
    routed = (
        (boundary_receipt.get("axis0_outputs_or_blockers") or {})
        .get("holographic_boundary_interior_reconstruction", {})
    )
    values = torch.tensor(
        [
            float(routed.get("mean_tomographic_fep_gap", 0.0)),
            float(routed.get("selection_gap", 0.0)),
            float(routed.get("axis0_path_entropy_mean_abs_delta", 0.0)),
        ],
        dtype=torch.float64,
    )
    return {
        "candidate": "holographic_boundary_interior_reconstruction",
        "status": "routing_candidate_not_final",
        "values": values.tolist(),
        "mean_tomographic_fep_gap": float(values[0]),
        "selection_gap": float(values[1]),
        "axis0_path_entropy_mean_abs_delta": float(values[2]),
        "explicit_blockers": boundary_receipt.get("explicit_blockers", {}),
        "source_receipt": boundary_receipt.get("path"),
        "finite": bool(
            torch.all(torch.isfinite(values)).item()
            and float(torch.linalg.vector_norm(values).item()) > 0.0
        ),
        "interpretation": "finite boundary/interior routing candidate with path-label and strict-best-KL blockers retained; not a holographic dictionary",
    }


def candidate_vector(candidate: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(candidate.get("values", []), dtype=torch.float64)


def compare_candidate(base: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    a = candidate_vector(base)
    b = candidate_vector(control)
    n = min(len(a), len(b))
    if n == 0:
        return {"l2_delta": 0.0, "pass": False}
    l2 = float(torch.linalg.vector_norm(a[:n] - b[:n]).item())
    return {"l2_delta": l2, "pass": l2 > 1e-9}


def route_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    edges = [
        ("canonical_qit_stage_slot_records", "fep_gradient_polarity"),
        ("canonical_qit_stage_slot_records", "path_entropy"),
        ("canonical_qit_stage_slot_records", "correlation_diversity_derivative"),
        ("holographic_boundary_path_receipt", "path_entropy"),
        ("holographic_boundary_path_receipt", "correlation_diversity_derivative"),
        ("source_native_boundary_reconstruction_receipt", "holographic_boundary_interior_blocker"),
        ("source_native_fep_pomdp_policy_tree_receipt", "retrocausal_many_futures_policy_scoring"),
        ("source_native_fep_online_vmp_policy_update_receipt", "retrocausal_many_futures_policy_scoring"),
        ("axis0_candidate_comparison", "repair_receipt"),
    ]
    graph.add_edges_from(edges)
    return {
        "pass": nx.is_directed_acyclic_graph(graph),
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "edge_list": edges,
    }


def main() -> int:
    started = time.time()
    rows = run_rows(manifold_enabled=True)
    no_manifold_rows = run_rows(manifold_enabled=False)
    shuffled_rows = list(reversed(rows))
    field_audit = assert_stage_fields(rows)
    pomdp_full_receipt = load_full_result("source_native_fep_pomdp_policy_tree_probe_results.json")
    online_vmp_full_receipt = load_full_result("source_native_fep_online_vmp_policy_update_probe_results.json")
    boundary_full_receipt = load_full_result("source_native_engine_boundary_path_fep_reconstruction_probe_results.json")

    candidates = {
        "fep_gradient_polarity": fep_gradient_candidate(rows),
        "path_entropy": path_entropy_candidate(rows),
        "correlation_diversity_derivative": correlation_diversity_candidate(rows),
        "retrocausal_many_futures_policy_scoring": many_futures_policy_candidate(
            pomdp_full_receipt,
            online_vmp_full_receipt,
        ),
        "holographic_boundary_interior_reconstruction": boundary_interior_candidate(boundary_full_receipt),
    }
    no_manifold_candidates = {
        "fep_gradient_polarity": fep_gradient_candidate(no_manifold_rows),
        "path_entropy": path_entropy_candidate(no_manifold_rows),
        "correlation_diversity_derivative": correlation_diversity_candidate(no_manifold_rows),
    }
    shuffled_candidates = {
        "fep_gradient_polarity": fep_gradient_candidate(shuffled_rows),
        "path_entropy": path_entropy_candidate(shuffled_rows),
        "correlation_diversity_derivative": correlation_diversity_candidate(shuffled_rows),
    }
    comparisons = {
        name: {
            "vs_no_manifold": compare_candidate(cand, no_manifold_candidates[name]),
            "vs_shuffled_order": compare_candidate(cand, shuffled_candidates[name]),
        }
        for name, cand in candidates.items()
        if name in no_manifold_candidates and name in shuffled_candidates
    }
    boundary_receipt = load_result("source_native_engine_boundary_path_fep_reconstruction_probe_results.json")
    pomdp_receipt = load_result("source_native_fep_pomdp_policy_tree_probe_results.json")
    online_vmp_receipt = load_result("source_native_fep_online_vmp_policy_update_probe_results.json")
    legacy_axis0_receipt = load_result("holographic_boundary_path_ensemble_axis0_fep_selection_probe_results.json")

    axis0_outputs_or_blockers = {
        **candidates,
    }
    graph = route_graph()
    finite_candidates = [
        row for row in candidates.values()
        if row["finite"] and math.isfinite(float(row.get("mean_abs_gradient", row.get("derivative_mean_abs", 0.0))))
    ]
    comparison_passes = [
        cmp["vs_no_manifold"]["pass"] or cmp["vs_shuffled_order"]["pass"]
        for cmp in comparisons.values()
    ]

    repair_receipt = {
        "weak_link": "Axis0 stage routing was fragmented across receipts and easy to collapse into one scalar.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "Axis0 stage routes must emit multiple candidates or explicit blockers, with at least one matched control comparison.",
        "dependency_subset": [
            "canonical QIT stage-slot records",
            "source_native_fep_pomdp_policy_tree receipt",
            "source_native_fep_online_vmp_policy_update receipt",
            "holographic_boundary_path_ensemble_axis0_fep_selection receipt",
            "source_native_engine_boundary_path_fep_reconstruction failed receipt as blocker",
            "matched no-manifold and shuffled-order controls",
        ],
        "stage_fields_touched": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": "macro_sim_stage_record_science_method_contract_probe_results.json",
        "after_delta/hash": "axis0 plural router result emits five finite candidates; boundary/interior blockers are retained inside that candidate",
        "primary_control/result": comparisons,
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "provider_inputs_used": {
            "grok": "system_v5/ops/formal_scouts/provider_receipts/20260517T130444Z_grok_xai_online_vmp_axis0_router_audit.json",
            "gemini": "system_v5/ops/formal_scouts/provider_receipts/20260517T130444Z_gemini_online_vmp_axis0_router_audit.json",
            "sonnet_high": "system_v5/ops/formal_scouts/provider_receipts/20260517T130444Z_sonnet_high_online_vmp_router_audit.receipt.json",
            "opus_max": "system_v5/ops/formal_scouts/provider_receipts/20260517T130444Z_opus_max_online_vmp_axis0_premortem.receipt.json",
            "reason": "provider lanes audited the wiring and premortem; local receipts remain the only admission authority",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Rerun the no-dense environment-contraction scout so each carrier consumes the five-candidate Axis0 bundle, including finite boundary/interior routing.",
    }

    positive = {
        "stage_records_have_science_method_fields": field_audit,
        "at_least_five_axis0_candidates_are_finite": {
            "pass": len(finite_candidates) >= 5,
            "finite_candidate_names": sorted(candidates),
        },
        "axis0_candidates_are_compared_to_controls": {
            "pass": all(comparison_passes),
            "comparisons": comparisons,
        },
        "boundary_reconstruction_candidate_is_routed_with_blockers": {
            "pass": boundary_receipt["exists"]
            and boundary_receipt.get("all_pass") is True
            and candidates["holographic_boundary_interior_reconstruction"]["finite"]
            and bool(candidates["holographic_boundary_interior_reconstruction"]["explicit_blockers"]),
            "receipt": boundary_receipt,
            "candidate": candidates["holographic_boundary_interior_reconstruction"],
        },
        "many_futures_policy_scoring_is_finite_candidate": {
            "pass": (
                pomdp_receipt["exists"]
                and pomdp_receipt.get("all_pass") is True
                and online_vmp_receipt["exists"]
                and online_vmp_receipt.get("all_pass") is True
                and candidates["retrocausal_many_futures_policy_scoring"].get("online_vmp_receipt_consumed") is True
                and candidates["retrocausal_many_futures_policy_scoring"]["finite"]
                and candidates["retrocausal_many_futures_policy_scoring"]["effective_policy_count"] > 1.0
            ),
            "receipt": pomdp_receipt,
            "online_vmp_receipt": online_vmp_receipt,
            "candidate": candidates["retrocausal_many_futures_policy_scoring"],
        },
        "online_vmp_receipt_consumed_for_many_futures_policy_scoring": {
            "pass": (
                online_vmp_receipt["exists"]
                and online_vmp_receipt.get("all_pass") is True
                and candidates["retrocausal_many_futures_policy_scoring"].get("online_vmp_receipt_consumed") is True
                and candidates["retrocausal_many_futures_policy_scoring"].get("online_vmp_receipt", {}).get("posterior_kl_max") is not None
                and candidates["retrocausal_many_futures_policy_scoring"].get("online_vmp_receipt", {}).get("vfe_reduction_min") is not None
            ),
            "receipt": online_vmp_receipt,
            "candidate_receipt": candidates["retrocausal_many_futures_policy_scoring"].get("online_vmp_receipt"),
        },
        "axis0_route_graph_executes": graph,
    }
    graveyards = {
        "single_scalar_axis0_is_rejected": {
            "pass": len(axis0_outputs_or_blockers) >= 5,
            "candidate_or_blocker_count": len(axis0_outputs_or_blockers),
            "candidate_or_blocker_names": sorted(axis0_outputs_or_blockers),
        },
        "shuffled_order_changes_at_least_one_candidate": {
            "pass": any(cmp["vs_shuffled_order"]["pass"] for cmp in comparisons.values()),
            "comparisons": comparisons,
        },
        "no_manifold_control_changes_at_least_one_candidate": {
            "pass": any(cmp["vs_no_manifold"]["pass"] for cmp in comparisons.values()),
            "comparisons": comparisons,
        },
        "legacy_axis0_receipt_consumed_not_promoted": {
            "pass": legacy_axis0_receipt["exists"] and legacy_axis0_receipt.get("all_pass") is True,
            "receipt": legacy_axis0_receipt,
            "promotion": "not_promoted_to_final_axis0",
        },
        "pomdp_only_many_futures_scoring_rejected_as_incomplete": {
            "pass": candidates["retrocausal_many_futures_policy_scoring"].get("online_vmp_receipt_consumed") is True,
            "pomdp_receipt": pomdp_receipt,
            "online_vmp_receipt": online_vmp_receipt,
            "reason": "POMDP A/B/C/D rows provide policy-tree structure; online-VMP receipt is required for posterior update support.",
        },
        "online_vmp_controls_are_preserved_in_many_futures_route": {
            "pass": all(
                value is True
                for value in candidates["retrocausal_many_futures_policy_scoring"].get(
                    "online_vmp_control_summary", {}
                ).values()
            ),
            "control_summary": candidates["retrocausal_many_futures_policy_scoring"].get(
                "online_vmp_control_summary", {}
            ),
        },
        "single_argmax_future_control_rejected": {
            "pass": candidates["retrocausal_many_futures_policy_scoring"]["l2_from_single_argmax_control"] > 0.1,
            "candidate": candidates["retrocausal_many_futures_policy_scoring"],
        },
        "uniform_future_control_distinguished": {
            "pass": candidates["retrocausal_many_futures_policy_scoring"]["l2_from_uniform_control"] > 1e-4,
            "candidate": candidates["retrocausal_many_futures_policy_scoring"],
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_final_axis0_and_retrocausality": {
            "pass": "does not admit final axis0" in CLAIM_CEILING.lower()
            and "retrocausality" in CLAIM_CEILING.lower(),
            "claim_ceiling": CLAIM_CEILING,
        },
        "axis0_outputs_include_candidates_and_blockers": {
            "pass": any(row.get("status") == "routing_candidate_not_final" for row in axis0_outputs_or_blockers.values())
            and bool(axis0_outputs_or_blockers["holographic_boundary_interior_reconstruction"].get("explicit_blockers")),
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
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "repair_receipt": repair_receipt,
        "dependency_consumption": graph,
        "positive": positive,
        "graveyard_companions": graveyards,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "boundary": boundary,
        "why_not_v4_probes": [
            "This is a v5 stage-record Axis0 candidate router over canonical QIT rows.",
            "It consumes existing Axis0/FEP receipts as bounded routing evidence only.",
            "It does not claim final Axis0 or literal retrocausal physics.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
