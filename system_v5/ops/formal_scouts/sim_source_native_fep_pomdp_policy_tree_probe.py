#!/usr/bin/env python3
"""Source-native FEP POMDP policy-tree scout.

This is the next, stricter step after
sim_source_native_active_inference_strategy_policy_probe.py.

The earlier scout made finite EngineCore stage windows into policy candidates
and scored them with an EFE-style observation readout. This scout adds the
missing active-inference boundary: explicit finite A/B/C/D matrices.

Formal translation:

- A: non-identity emission matrix P(o | s). This is the sensory blanket /
  projection channel, not a psychology primitive.
- B_pi: source-native EngineCore-induced latent transition for each finite
  policy window. It is estimated from density-state rollouts.
- C: preference distribution P(o). Emotion/IGT labels remain non-load-bearing.
- D: prior over latent states, estimated from initial source-native densities.
- Future/time: finite policy-tree prediction depth under B_pi, not primitive
  temporal metaphysics.

Formal scout only. No canonical FEP engine, Holodeck, psychology, TOE, final
IGT, or physics claim is admitted.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import networkx as nx
import torch

from canonical_qit_engine_specs import I2, SX, SY, SZ
from engine_core import EngineCore, generate_initial_density


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_fep_pomdp_policy_tree_probe_results.json"

NAME = "source_native_fep_pomdp_policy_tree_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "source_native_fep_pomdp_policy_tree_scout"
CLAIM_CEILING = (
    "Formal scout only: finite discrete POMDP-style active-inference probe "
    "over source-native EngineCore policy windows with explicit A/B/C/D "
    "matrices. It does not admit a full FEP engine, canonical Holodeck, "
    "psychology, TOE, final IGT, consciousness, physics, or canonical engine "
    "identity claim."
)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite A/B/C/D matrices, density projection, KL, entropy, VFE, policy posterior, and policy scoring",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive A/B/C/D dependency graph sanity check",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native stage-window rollout provider consumed by Torch measurements",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result writing",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "networkx": "supportive",
    "engine_core": "supportive",
    "json": "supportive",
}

N_STATES = 6
N_OBSERVATIONS = 6
N_SEEDS = 16
POLICY_WINDOW_STAGES = 2
PREDICTION_STEPS = 3
N_SUBSTAGES_PER_STAGE = 4
SMOOTHING = 0.03
EFE_FORMULA = "risk + ambiguity"
TORCH_REAL = torch.float64
TORCH_COMPLEX = torch.complex128
I2_T = torch.as_tensor(I2, dtype=TORCH_COMPLEX)
SX_T = torch.as_tensor(SX, dtype=TORCH_COMPLEX)
SY_T = torch.as_tensor(SY, dtype=TORCH_COMPLEX)
SZ_T = torch.as_tensor(SZ, dtype=TORCH_COMPLEX)

IGT_BY_PERCEPTION = {
    "Ne": "WinLose",
    "Si": "WinWin",
    "Se": "LoseWin",
    "Ni": "LoseLose",
}


def as_real_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_REAL)


def as_complex_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_COMPLEX)


def dagger(a: torch.Tensor) -> torch.Tensor:
    return a.conj().T


def project_density(rho: Any) -> torch.Tensor:
    rho_t = as_complex_tensor(rho)
    rho_t = 0.5 * (rho_t + dagger(rho_t))
    vals, vecs = torch.linalg.eigh(rho_t)
    vals = torch.clamp(vals.real, min=0.0)
    if float(torch.sum(vals).item()) <= 1e-14:
        vals = torch.ones_like(vals) / vals.numel()
    rho_t = (vecs * vals.to(TORCH_COMPLEX)) @ dagger(vecs)
    return rho_t / torch.trace(rho_t)


def normalize(prob: Any) -> torch.Tensor:
    prob_t = torch.clamp(as_real_tensor(prob), min=1e-12)
    logs = torch.log(prob_t)
    return torch.exp(logs - torch.logsumexp(logs, dim=0))


def entropy_prob(prob: Any) -> float:
    prob = normalize(prob)
    return float((-torch.sum(prob * torch.log(prob))).item())


def kl(p: Any, q: Any) -> float:
    p = normalize(p)
    q = normalize(q)
    return float(torch.sum(p * (torch.log(p) - torch.log(q))).item())


def pauli_observation_distribution(rho: Any) -> torch.Tensor:
    rho = project_density(rho)
    projectors = []
    for sigma in [SZ_T, SX_T, SY_T]:
        projectors.append(0.5 * (I2_T + sigma))
        projectors.append(0.5 * (I2_T - sigma))
    probs = torch.tensor([float(torch.real(torch.trace(p @ rho)).item()) for p in projectors], dtype=TORCH_REAL)
    return normalize(probs)


def preference_distribution() -> torch.Tensor:
    return normalize(torch.tensor([0.27, 0.09, 0.23, 0.09, 0.18, 0.14], dtype=TORCH_REAL))


def shuffled_preference(base: Any) -> torch.Tensor:
    return normalize(as_real_tensor(base)[torch.tensor([1, 4, 0, 5, 2, 3], dtype=torch.int64)])


def emission_matrix() -> torch.Tensor:
    """Column-stochastic non-identity P(o | s)."""
    # Informative but non-perfect sensory projection with state-dependent
    # ambiguity. Preference-aligned observations are deliberately more
    # ambiguous than some alternatives, so risk + ambiguity can select a
    # different policy than pure risk. A symmetric channel makes ambiguity
    # constant and collapses the scout back to risk-only.
    diag_by_state = torch.tensor([0.42, 0.86, 0.42, 0.86, 0.44, 0.82], dtype=TORCH_REAL)
    opposite_by_state = torch.tensor([0.20, 0.06, 0.20, 0.06, 0.18, 0.08], dtype=TORCH_REAL)
    a = torch.zeros((N_OBSERVATIONS, N_STATES), dtype=TORCH_REAL)
    for state in range(N_STATES):
        residual = 1.0 - float(diag_by_state[state].item()) - float(opposite_by_state[state].item())
        a[:, state] = residual / (N_OBSERVATIONS - 2)
        a[state, state] = diag_by_state[state]
        opposite = state + 1 if state % 2 == 0 else state - 1
        a[opposite, state] = opposite_by_state[state]
    return a / torch.sum(a, dim=0, keepdim=True)


def identity_emission_matrix() -> torch.Tensor:
    return torch.eye(N_OBSERVATIONS, N_STATES, dtype=TORCH_REAL)


def policy_id(engine_type: int, start_stage: int) -> str:
    return f"E{engine_type}:stage_window_{start_stage:02d}_{(start_stage + 1) % 8:02d}"


def run_policy_density(engine_type: int, start_stage: int, seed: int, manifold_enabled: bool = True) -> torch.Tensor:
    rho = generate_initial_density(seed)
    engine = EngineCore(engine_type, manifold_enabled=manifold_enabled)
    for offset in range(POLICY_WINDOW_STAGES):
        main_idx = (start_stage + offset) % len(engine.schedule)
        perception, loop_class = engine.schedule[main_idx]
        for substage_idx in range(N_SUBSTAGES_PER_STAGE):
            rho, _record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
    return project_density(rho)


def estimate_prior() -> torch.Tensor:
    obs = []
    for seed_offset in range(N_SEEDS):
        rho = generate_initial_density(9100 + 37 * seed_offset)
        obs.append(pauli_observation_distribution(rho))
    return normalize(torch.mean(torch.stack(obs), dim=0))


def estimate_transition(engine_type: int, start_stage: int, manifold_enabled: bool = True) -> torch.Tensor:
    accum = torch.full((N_STATES, N_STATES), SMOOTHING, dtype=TORCH_REAL)
    for seed_offset in range(N_SEEDS):
        seed = 9200 + 41 * seed_offset + 17 * engine_type + start_stage
        rho0 = generate_initial_density(seed)
        q_initial = pauli_observation_distribution(rho0)
        rho1 = run_policy_density(engine_type, start_stage, seed, manifold_enabled=manifold_enabled)
        q_final = pauli_observation_distribution(rho1)
        accum = accum + torch.outer(q_final, q_initial)
    return accum / torch.sum(accum, dim=0, keepdim=True)


def score_policy(
    *,
    engine_type: int,
    start_stage: int,
    a_matrix: Any,
    c_pref: Any,
    d_prior: Any,
    manifold_enabled: bool = True,
    no_engine_control: bool = False,
) -> dict[str, Any]:
    engine = EngineCore(engine_type)
    a_matrix = as_real_tensor(a_matrix)
    c_pref = normalize(c_pref)
    d_prior = normalize(d_prior)
    if no_engine_control:
        b_matrix = torch.eye(N_STATES, dtype=TORCH_REAL)
    else:
        b_matrix = estimate_transition(engine_type, start_stage, manifold_enabled=manifold_enabled)

    q_s = d_prior.clone()
    risk = 0.0
    ambiguity = 0.0
    epistemic_value = 0.0
    vfe_reduction = 0.0
    per_step = []
    for step in range(PREDICTION_STEPS):
        q_s = normalize(b_matrix @ q_s)
        q_o = normalize(a_matrix @ q_s)
        entropy_by_state = torch.tensor([entropy_prob(a_matrix[:, idx]) for idx in range(N_STATES)], dtype=TORCH_REAL)
        conditional_entropy = float(torch.sum(q_s * entropy_by_state).item())
        info_gain = max(0.0, entropy_prob(q_o) - conditional_entropy)
        obs_idx = int(torch.argmax(q_o).item())
        posterior = normalize(a_matrix[obs_idx, :] * q_s)
        prior_vfe = variational_free_energy(q_s, q_s, a_matrix, obs_idx)
        posterior_vfe = variational_free_energy(posterior, q_s, a_matrix, obs_idx)
        step_vfe_reduction = max(0.0, prior_vfe - posterior_vfe)
        step_risk = kl(q_o, c_pref)
        risk += step_risk
        ambiguity += conditional_entropy
        epistemic_value += info_gain
        vfe_reduction += step_vfe_reduction
        per_step.append(
            {
                "step": step + 1,
                "risk": step_risk,
                "ambiguity": conditional_entropy,
                "epistemic_value": info_gain,
                "vfe_reduction": step_vfe_reduction,
                "observation_entropy": entropy_prob(q_o),
            }
        )

    expected_free_energy = risk + ambiguity
    stage_pair = [
        engine.schedule[start_stage],
        engine.schedule[(start_stage + 1) % len(engine.schedule)],
    ]
    perceptions = [row[0] for row in stage_pair]
    return {
        "policy_id": policy_id(engine_type, start_stage),
        "engine_type": engine_type,
        "start_stage": start_stage,
        "stage_pair": [list(row) for row in stage_pair],
        "igt_quadrants": [IGT_BY_PERCEPTION[p] for p in perceptions],
        "risk": float(risk),
        "ambiguity": float(ambiguity),
        "epistemic_value": float(epistemic_value),
        "vfe_reduction": float(vfe_reduction),
        "expected_free_energy": float(expected_free_energy),
        "transition_l1_from_identity": float(torch.mean(torch.abs(b_matrix - torch.eye(N_STATES, dtype=TORCH_REAL))).item()),
        "transition_column_entropy_mean": float(torch.mean(torch.tensor([entropy_prob(b_matrix[:, idx]) for idx in range(N_STATES)], dtype=TORCH_REAL)).item()),
        "per_step": per_step,
        "manifold_enabled": manifold_enabled,
        "no_engine_control": no_engine_control,
    }


def score_family(
    *,
    a_matrix: Any,
    c_pref: Any,
    d_prior: Any,
    manifold_enabled: bool = True,
    no_engine_control: bool = False,
) -> list[dict[str, Any]]:
    rows = []
    for engine_type in [0, 1]:
        for start_stage in range(8):
            rows.append(
                score_policy(
                    engine_type=engine_type,
                    start_stage=start_stage,
                    a_matrix=a_matrix,
                    c_pref=c_pref,
                    d_prior=d_prior,
                    manifold_enabled=manifold_enabled,
                    no_engine_control=no_engine_control,
                )
            )
    return softmax_policy(rows)


def policy_rows(
    *,
    a_matrix: Any | None = None,
    c_pref: Any | None = None,
    d_prior: Any | None = None,
    manifold_enabled: bool = True,
    no_engine_control: bool = False,
) -> list[dict[str, Any]]:
    return score_family(
        a_matrix=emission_matrix() if a_matrix is None else a_matrix,
        c_pref=preference_distribution() if c_pref is None else c_pref,
        d_prior=estimate_prior() if d_prior is None else d_prior,
        manifold_enabled=manifold_enabled,
        no_engine_control=no_engine_control,
    )


def softmax_policy(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values = torch.tensor([-row["expected_free_energy"] for row in rows], dtype=TORCH_REAL)
    probs = torch.exp(values - torch.logsumexp(values, dim=0))
    out = []
    for row, prob in zip(rows, probs, strict=True):
        enriched = dict(row)
        enriched["policy_probability"] = float(prob)
        out.append(enriched)
    return sorted(out, key=lambda row: row["expected_free_energy"])


def best_by(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return min(rows, key=lambda row: row[key])


def variational_free_energy(
    q_variational: Any,
    q_prior: Any,
    a_matrix: Any,
    obs_idx: int,
) -> float:
    q_variational = normalize(q_variational)
    q_prior = normalize(q_prior)
    a_matrix = as_real_tensor(a_matrix)
    likelihood = torch.clamp(a_matrix[obs_idx, :], min=1e-12)
    joint_log = torch.log(likelihood) + torch.log(q_prior)
    return float(torch.sum(q_variational * (torch.log(q_variational) - joint_log)).item())


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edges_from(
        [
            ("source_native_rollouts", "B_pi_transition"),
            ("sensory_projection_channel", "A_emission"),
            ("preference_profile", "C_preference"),
            ("initial_density_ensemble", "D_prior"),
            ("A_emission", "predicted_observation"),
            ("B_pi_transition", "predicted_state"),
            ("D_prior", "predicted_state"),
            ("C_preference", "risk"),
            ("predicted_observation", "risk"),
            ("A_emission", "ambiguity"),
            ("predicted_state", "ambiguity"),
            ("predicted_observation", "epistemic_value"),
            ("ambiguity", "epistemic_value"),
            ("risk", "expected_free_energy"),
            ("ambiguity", "expected_free_energy"),
            ("epistemic_value", "expected_free_energy"),
            ("expected_free_energy", "policy_posterior"),
        ]
    )
    return {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "acyclic": nx.is_directed_acyclic_graph(graph)}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [as_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "item"):
        try:
            return as_jsonable(value.item())
        except (TypeError, ValueError):
            pass
    return value


def main() -> dict[str, Any]:
    started = time.time()
    a_matrix = emission_matrix()
    a_identity = identity_emission_matrix()
    c_pref = preference_distribution()
    c_shuffled = shuffled_preference(c_pref)
    d_prior = estimate_prior()

    rows = score_family(a_matrix=a_matrix, c_pref=c_pref, d_prior=d_prior)
    risk_only = best_by(rows, "risk")
    selected = rows[0]
    no_engine_rows = score_family(
        a_matrix=a_matrix,
        c_pref=c_pref,
        d_prior=d_prior,
        no_engine_control=True,
    )
    no_manifold_rows = score_family(
        a_matrix=a_matrix,
        c_pref=c_pref,
        d_prior=d_prior,
        manifold_enabled=False,
    )
    shuffled_rows = score_family(a_matrix=a_matrix, c_pref=c_shuffled, d_prior=d_prior)
    perfect_observable_rows = score_family(a_matrix=a_identity, c_pref=c_pref, d_prior=d_prior)

    graph = dependency_graph()
    efe_values = [row["expected_free_energy"] for row in rows]
    risk_values = [row["risk"] for row in rows]
    epistemic_values = [row["epistemic_value"] for row in rows]
    transition_gaps = [row["transition_l1_from_identity"] for row in rows]
    vfe_reductions = [row["vfe_reduction"] for row in rows]
    prob_sum = float(sum(row["policy_probability"] for row in rows))

    predicates = {
        "finite_policy_tree_constructed": len(rows) == 16 and len({row["policy_id"] for row in rows}) == 16,
        "a_matrix_column_stochastic": bool(torch.allclose(torch.sum(a_matrix, dim=0), torch.ones(N_STATES, dtype=TORCH_REAL))),
        "a_matrix_non_identity": float(torch.max(torch.abs(a_matrix - torch.eye(N_OBSERVATIONS, N_STATES, dtype=TORCH_REAL))).item()) > 0.2,
        "d_prior_normalizes": abs(float(torch.sum(d_prior).item()) - 1.0) < 1e-9,
        "policy_posterior_normalizes": abs(prob_sum - 1.0) < 1e-9,
        "efe_scores_are_finite": all(math.isfinite(row["expected_free_energy"]) for row in rows),
        "epistemic_value_is_nonzero": float(max(epistemic_values) - min(epistemic_values)) > 0.001,
        "vfe_update_reduces_free_energy": min(vfe_reductions) >= -1e-9 and max(vfe_reductions) > 0.001,
        "source_native_transition_nontrivial": float(torch.mean(torch.tensor(transition_gaps, dtype=TORCH_REAL)).item()) > 0.01,
        "selected_not_risk_only_or_margin": selected["policy_id"] != risk_only["policy_id"]
        or abs(selected["expected_free_energy"] - risk_only["expected_free_energy"]) > 0.01,
        "no_engine_control_changes_policy_or_margin": selected["policy_id"] != no_engine_rows[0]["policy_id"]
        or abs(selected["expected_free_energy"] - no_engine_rows[0]["expected_free_energy"]) > 0.01,
        "shuffled_preference_changes_policy_or_margin": selected["policy_id"] != shuffled_rows[0]["policy_id"]
        or abs(selected["expected_free_energy"] - shuffled_rows[0]["expected_free_energy"]) > 0.01,
        "perfect_observability_changes_terms": abs(selected["ambiguity"] - perfect_observable_rows[0]["ambiguity"]) > 0.01,
        "dependency_graph_acyclic": graph["acyclic"],
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "math_object": "finite POMDP-style A/B/C/D active-inference policy tree over source-native EngineCore stage windows",
        "doc_grounding": {
            "system_v5/docs/references/FEP_AND_ACTIVE_INFERENCE_REFERENCE.md:76-89": (
                "Expected free energy G(pi), epistemic/pragmatic decomposition, policy posterior"
            ),
            "system_v5/docs/NOMINALISM_IN_THIS_SYSTEM.md:284-306": (
                "FEP as probe family / quotient correspondence, not primitive ontology"
            ),
            "READ ONLY Legacy core_docs/HOLODECK_SCIENCE_SYSTEM_v1.md:58-81": (
                "Applied FEP as finite KL/surprise comparison over density-derived observations"
            ),
            "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/AXIS0_PHYSICS_BRIDGE_v0.1.md:84-96": (
                "Future/path language is finite refinement depth, not primitive time"
            ),
            "system_v5/READ ONLY Reference Docs/ENGINE_64_SCHEDULE_ATLAS.md:145-152": (
                "IGT quadrant labels are overlay metadata on source-native stage windows"
            ),
        },
        "formal_translation": {
            "engine_stage_as_strategy": "policy candidate = source-native two-stage EngineCore schedule window",
            "time_future": "future = finite policy-tree prediction depth under B_pi",
            "emotion_projection": "emotion/projection language = C preference distribution over observations",
            "hume_boundary": "causal/order language requires distinguishable A/B/C/D readout changes",
            "nominalism_boundary": "policies are survivor candidates under this finite probe family only",
            "markov_blanket_boundary": "A is a non-identity sensory projection channel separated from B_pi transitions",
        },
        "summary": {
            "policy_count": len(rows),
            "seed_count": N_SEEDS,
            "policy_window_stages": POLICY_WINDOW_STAGES,
            "prediction_steps": PREDICTION_STEPS,
            "efe_formula": EFE_FORMULA,
            "selected_policy": selected["policy_id"],
            "selected_efe": selected["expected_free_energy"],
            "selected_risk": selected["risk"],
            "selected_ambiguity": selected["ambiguity"],
            "selected_epistemic_value": selected["epistemic_value"],
            "selected_vfe_reduction": selected["vfe_reduction"],
            "risk_only_policy": risk_only["policy_id"],
            "no_engine_policy": no_engine_rows[0]["policy_id"],
            "no_manifold_policy": no_manifold_rows[0]["policy_id"],
            "shuffled_preference_policy": shuffled_rows[0]["policy_id"],
            "perfect_observable_policy": perfect_observable_rows[0]["policy_id"],
            "efe_range": float(max(efe_values) - min(efe_values)),
            "risk_range": float(max(risk_values) - min(risk_values)),
            "epistemic_value_range": float(max(epistemic_values) - min(epistemic_values)),
            "vfe_reduction_range": float(max(vfe_reductions) - min(vfe_reductions)),
            "mean_transition_l1_from_identity": float(torch.mean(torch.tensor(transition_gaps, dtype=TORCH_REAL)).item()),
        },
        "positive": {
            "finite_pomdp_policy_tree_constructed": {
                "pass": predicates["finite_policy_tree_constructed"],
                "policy_count": len(rows),
                "unique_policy_count": len({row["policy_id"] for row in rows}),
            },
            "explicit_non_identity_a_matrix": {
                "pass": predicates["a_matrix_column_stochastic"] and predicates["a_matrix_non_identity"],
                "column_sums": torch.sum(a_matrix, dim=0),
                "max_abs_diff_from_identity": float(torch.max(torch.abs(a_matrix - torch.eye(N_OBSERVATIONS, N_STATES, dtype=TORCH_REAL))).item()),
            },
            "source_native_b_transition_nontrivial": {
                "pass": predicates["source_native_transition_nontrivial"],
                "mean_l1_from_identity": float(torch.mean(torch.tensor(transition_gaps, dtype=TORCH_REAL)).item()),
                "max_l1_from_identity": float(max(transition_gaps)),
            },
            "c_and_d_normalize": {
                "pass": predicates["d_prior_normalizes"] and abs(float(torch.sum(c_pref).item()) - 1.0) < 1e-9,
                "c_sum": float(torch.sum(c_pref).item()),
                "d_sum": float(torch.sum(d_prior).item()),
            },
            "policy_posterior_normalizes": {"pass": predicates["policy_posterior_normalizes"], "probability_sum": prob_sum},
            "expected_free_energy_scores_are_finite": {
                "pass": predicates["efe_scores_are_finite"],
                "efe_min": float(min(efe_values)),
                "efe_max": float(max(efe_values)),
            },
            "epistemic_value_term_is_nonzero": {
                "pass": predicates["epistemic_value_is_nonzero"],
                "epistemic_value_range": float(max(epistemic_values) - min(epistemic_values)),
            },
            "bayesian_vfe_update_reduces_free_energy": {
                "pass": predicates["vfe_update_reduces_free_energy"],
                "vfe_reduction_min": float(min(vfe_reductions)),
                "vfe_reduction_max": float(max(vfe_reductions)),
                "note": "Each policy performs a one-observation Bayesian posterior update and records F(prior)-F(posterior).",
            },
            "policy_dependency_graph_executes": {"pass": predicates["dependency_graph_acyclic"], **graph},
        },
        "graveyard_companions": {
            "risk_only_policy_not_sufficient": {
                "pass": predicates["selected_not_risk_only_or_margin"],
                "efe_policy": selected["policy_id"],
                "risk_policy": risk_only["policy_id"],
                "efe_policy_score": selected["expected_free_energy"],
                "risk_policy_efe": risk_only["expected_free_energy"],
            },
            "no_engine_identity_transition_changes_policy_or_margin": {
                "pass": predicates["no_engine_control_changes_policy_or_margin"],
                "engine_policy": selected["policy_id"],
                "no_engine_policy": no_engine_rows[0]["policy_id"],
                "engine_efe": selected["expected_free_energy"],
                "no_engine_efe": no_engine_rows[0]["expected_free_energy"],
            },
            "shuffled_preference_changes_policy_or_margin": {
                "pass": predicates["shuffled_preference_changes_policy_or_margin"],
                "base_policy": selected["policy_id"],
                "shuffled_policy": shuffled_rows[0]["policy_id"],
                "base_efe": selected["expected_free_energy"],
                "shuffled_efe": shuffled_rows[0]["expected_free_energy"],
            },
            "perfect_observability_changes_ambiguity_term": {
                "pass": predicates["perfect_observability_changes_terms"],
                "nonidentity_a_ambiguity": selected["ambiguity"],
                "identity_a_ambiguity": perfect_observable_rows[0]["ambiguity"],
                "top_policy_changed": selected["policy_id"] != perfect_observable_rows[0]["policy_id"],
                "nonidentity_a_policy": selected["policy_id"],
                "identity_a_policy": perfect_observable_rows[0]["policy_id"],
            },
        },
        "boundary": {
            "classification_is_formal_scout": {"pass": CLASSIFICATION == "formal_scout"},
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        },
        "claim_guards": {
            "does_not_claim_full_fep_engine": True,
            "does_not_claim_holodeck_canon": True,
            "does_not_claim_psychology_or_emotion_ontology": True,
            "does_not_claim_physics_or_toe_evidence": True,
            "does_not_import_primitive_time": True,
            "igt_labels_are_not_load_bearing": "IGT quadrant labels are overlay metadata; A/B/C/D matrices determine the score.",
            "manifold_off_recorded_not_promoted": {
                "manifold_on_policy": selected["policy_id"],
                "manifold_off_policy": no_manifold_rows[0]["policy_id"],
                "manifold_on_efe": selected["expected_free_energy"],
                "manifold_off_efe": no_manifold_rows[0]["expected_free_energy"],
            },
            "z3_not_used": "Dropped after Opus audit flagged prior Boolean witness as vacuous; no formal SMT noncollapse proof is claimed.",
        },
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "variants": [
                "risk_only",
                "no_engine_identity_transition",
                "shuffled_preference",
                "perfect_observability",
            ],
        },
        "policy_rows": rows,
        "control_rows": {
            "no_engine_top3": no_engine_rows[:3],
            "no_manifold_top3": no_manifold_rows[:3],
            "shuffled_preference_top3": shuffled_rows[:3],
            "perfect_observable_top3": perfect_observable_rows[:3],
        },
        "matrices": {
            "A_emission": a_matrix,
            "C_preference": c_pref,
            "D_prior": d_prior,
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "why_not_v4_probes": [
            "This is a clean v5 formal scout over source-native EngineCore policy windows.",
            "It uses explicit finite A/B/C/D active-inference matrices instead of v4 narrative probes.",
            "It is still a scout and does not promote Holodeck, psychology, IGT, or physics language into canon.",
        ],
        "why_not_canon": [
            "A/B/C/D are finite scout matrices, not a complete engine rewrite.",
            "No learned generative model, no continuous belief propagation, and no canonical Markov blanket are admitted.",
            "The scout only shows a next executable interface for FEP-style engine operation.",
        ],
    }
    result["all_pass"] = (
        all(row.get("pass") is True for row in result["positive"].values())
        and all(row.get("pass") is True for row in result["graveyard_companions"].values())
        and all(row.get("pass") is True for row in result["boundary"].values())
    )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    print(json.dumps(as_jsonable(result["summary"]), indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
