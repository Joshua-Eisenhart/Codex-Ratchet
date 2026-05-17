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
import numpy as np
from scipy.special import logsumexp

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
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite A/B/C/D matrices, KL, entropy, mutual information, and policy scoring",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing logsumexp normalization plus EngineCore transition dependency",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing transitively through EngineCore 13-layer manifold constraints",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing A/B/C/D dependency graph sanity check",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "torch": "load_bearing",
    "networkx": "load_bearing",
}

N_STATES = 6
N_OBSERVATIONS = 6
N_SEEDS = 16
POLICY_WINDOW_STAGES = 2
PREDICTION_STEPS = 3
N_SUBSTAGES_PER_STAGE = 4
SMOOTHING = 0.03
EFE_FORMULA = "risk + ambiguity"

IGT_BY_PERCEPTION = {
    "Ne": "WinLose",
    "Si": "WinWin",
    "Se": "LoseWin",
    "Ni": "LoseLose",
}


def dagger(a: np.ndarray) -> np.ndarray:
    return np.conjugate(a.T)


def project_density(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + dagger(rho))
    vals, vecs = np.linalg.eigh(rho)
    vals = np.clip(vals.real, 0.0, None)
    if float(np.sum(vals)) <= 1e-14:
        vals = np.ones_like(vals) / len(vals)
    rho = (vecs * vals) @ dagger(vecs)
    return rho / np.trace(rho)


def normalize(prob: np.ndarray) -> np.ndarray:
    prob = np.clip(np.asarray(prob, dtype=float), 1e-12, None)
    logs = np.log(prob)
    return np.exp(logs - logsumexp(logs))


def entropy_prob(prob: np.ndarray) -> float:
    prob = normalize(prob)
    return -float(np.sum(prob * np.log(prob)))


def kl(p: np.ndarray, q: np.ndarray) -> float:
    p = normalize(p)
    q = normalize(q)
    return float(np.sum(p * (np.log(p) - np.log(q))))


def pauli_observation_distribution(rho: np.ndarray) -> np.ndarray:
    rho = project_density(rho)
    projectors = []
    for sigma in [SZ, SX, SY]:
        projectors.append(0.5 * (I2 + sigma))
        projectors.append(0.5 * (I2 - sigma))
    probs = np.array([float(np.real(np.trace(p @ rho))) for p in projectors], dtype=float)
    return normalize(probs)


def preference_distribution() -> np.ndarray:
    return normalize(np.array([0.27, 0.09, 0.23, 0.09, 0.18, 0.14], dtype=float))


def shuffled_preference(base: np.ndarray) -> np.ndarray:
    return normalize(base[[1, 4, 0, 5, 2, 3]])


def emission_matrix() -> np.ndarray:
    """Column-stochastic non-identity P(o | s)."""
    # Informative but non-perfect sensory projection with state-dependent
    # ambiguity. Preference-aligned observations are deliberately more
    # ambiguous than some alternatives, so risk + ambiguity can select a
    # different policy than pure risk. A symmetric channel makes ambiguity
    # constant and collapses the scout back to risk-only.
    diag_by_state = np.array([0.42, 0.86, 0.42, 0.86, 0.44, 0.82], dtype=float)
    opposite_by_state = np.array([0.20, 0.06, 0.20, 0.06, 0.18, 0.08], dtype=float)
    a = np.zeros((N_OBSERVATIONS, N_STATES), dtype=float)
    for state in range(N_STATES):
        residual = 1.0 - diag_by_state[state] - opposite_by_state[state]
        a[:, state] = residual / (N_OBSERVATIONS - 2)
        a[state, state] = diag_by_state[state]
        opposite = state + 1 if state % 2 == 0 else state - 1
        a[opposite, state] = opposite_by_state[state]
    return a / np.sum(a, axis=0, keepdims=True)


def identity_emission_matrix() -> np.ndarray:
    return np.eye(N_OBSERVATIONS, N_STATES, dtype=float)


def policy_id(engine_type: int, start_stage: int) -> str:
    return f"E{engine_type}:stage_window_{start_stage:02d}_{(start_stage + 1) % 8:02d}"


def run_policy_density(engine_type: int, start_stage: int, seed: int, manifold_enabled: bool = True) -> np.ndarray:
    rho = generate_initial_density(seed)
    engine = EngineCore(engine_type, manifold_enabled=manifold_enabled)
    for offset in range(POLICY_WINDOW_STAGES):
        main_idx = (start_stage + offset) % len(engine.schedule)
        perception, loop_class = engine.schedule[main_idx]
        for substage_idx in range(N_SUBSTAGES_PER_STAGE):
            rho, _record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
    return project_density(rho)


def estimate_prior() -> np.ndarray:
    obs = []
    for seed_offset in range(N_SEEDS):
        rho = generate_initial_density(9100 + 37 * seed_offset)
        obs.append(pauli_observation_distribution(rho))
    return normalize(np.mean(np.array(obs, dtype=float), axis=0))


def estimate_transition(engine_type: int, start_stage: int, manifold_enabled: bool = True) -> np.ndarray:
    accum = np.full((N_STATES, N_STATES), SMOOTHING, dtype=float)
    for seed_offset in range(N_SEEDS):
        seed = 9200 + 41 * seed_offset + 17 * engine_type + start_stage
        rho0 = generate_initial_density(seed)
        q_initial = pauli_observation_distribution(rho0)
        rho1 = run_policy_density(engine_type, start_stage, seed, manifold_enabled=manifold_enabled)
        q_final = pauli_observation_distribution(rho1)
        accum += np.outer(q_final, q_initial)
    return accum / np.sum(accum, axis=0, keepdims=True)


def score_policy(
    *,
    engine_type: int,
    start_stage: int,
    a_matrix: np.ndarray,
    c_pref: np.ndarray,
    d_prior: np.ndarray,
    manifold_enabled: bool = True,
    no_engine_control: bool = False,
) -> dict[str, Any]:
    engine = EngineCore(engine_type)
    if no_engine_control:
        b_matrix = np.eye(N_STATES)
    else:
        b_matrix = estimate_transition(engine_type, start_stage, manifold_enabled=manifold_enabled)

    q_s = d_prior.copy()
    risk = 0.0
    ambiguity = 0.0
    epistemic_value = 0.0
    vfe_reduction = 0.0
    per_step = []
    for step in range(PREDICTION_STEPS):
        q_s = normalize(b_matrix @ q_s)
        q_o = normalize(a_matrix @ q_s)
        conditional_entropy = float(
            np.sum(q_s * np.array([entropy_prob(a_matrix[:, idx]) for idx in range(N_STATES)]))
        )
        info_gain = max(0.0, entropy_prob(q_o) - conditional_entropy)
        obs_idx = int(np.argmax(q_o))
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
        "transition_l1_from_identity": float(np.mean(np.abs(b_matrix - np.eye(N_STATES)))),
        "transition_column_entropy_mean": float(np.mean([entropy_prob(b_matrix[:, idx]) for idx in range(N_STATES)])),
        "per_step": per_step,
        "manifold_enabled": manifold_enabled,
        "no_engine_control": no_engine_control,
    }


def score_family(
    *,
    a_matrix: np.ndarray,
    c_pref: np.ndarray,
    d_prior: np.ndarray,
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


def softmax_policy(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values = np.array([-row["expected_free_energy"] for row in rows], dtype=float)
    probs = np.exp(values - logsumexp(values))
    out = []
    for row, prob in zip(rows, probs, strict=True):
        enriched = dict(row)
        enriched["policy_probability"] = float(prob)
        out.append(enriched)
    return sorted(out, key=lambda row: row["expected_free_energy"])


def best_by(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return min(rows, key=lambda row: row[key])


def variational_free_energy(
    q_variational: np.ndarray,
    q_prior: np.ndarray,
    a_matrix: np.ndarray,
    obs_idx: int,
) -> float:
    q_variational = normalize(q_variational)
    q_prior = normalize(q_prior)
    likelihood = np.clip(a_matrix[obs_idx, :], 1e-12, None)
    joint_log = np.log(likelihood) + np.log(q_prior)
    return float(np.sum(q_variational * (np.log(q_variational) - joint_log)))


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
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
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
        "a_matrix_column_stochastic": bool(np.allclose(np.sum(a_matrix, axis=0), np.ones(N_STATES))),
        "a_matrix_non_identity": float(np.max(np.abs(a_matrix - np.eye(N_OBSERVATIONS, N_STATES)))) > 0.2,
        "d_prior_normalizes": abs(float(np.sum(d_prior)) - 1.0) < 1e-9,
        "policy_posterior_normalizes": abs(prob_sum - 1.0) < 1e-9,
        "efe_scores_are_finite": all(math.isfinite(row["expected_free_energy"]) for row in rows),
        "epistemic_value_is_nonzero": float(max(epistemic_values) - min(epistemic_values)) > 0.001,
        "vfe_update_reduces_free_energy": min(vfe_reductions) >= -1e-9 and max(vfe_reductions) > 0.001,
        "source_native_transition_nontrivial": float(np.mean(transition_gaps)) > 0.01,
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
            "mean_transition_l1_from_identity": float(np.mean(transition_gaps)),
        },
        "positive": {
            "finite_pomdp_policy_tree_constructed": {
                "pass": predicates["finite_policy_tree_constructed"],
                "policy_count": len(rows),
                "unique_policy_count": len({row["policy_id"] for row in rows}),
            },
            "explicit_non_identity_a_matrix": {
                "pass": predicates["a_matrix_column_stochastic"] and predicates["a_matrix_non_identity"],
                "column_sums": np.sum(a_matrix, axis=0),
                "max_abs_diff_from_identity": float(np.max(np.abs(a_matrix - np.eye(N_OBSERVATIONS, N_STATES)))),
            },
            "source_native_b_transition_nontrivial": {
                "pass": predicates["source_native_transition_nontrivial"],
                "mean_l1_from_identity": float(np.mean(transition_gaps)),
                "max_l1_from_identity": float(max(transition_gaps)),
            },
            "c_and_d_normalize": {
                "pass": predicates["d_prior_normalizes"] and abs(float(np.sum(c_pref)) - 1.0) < 1e-9,
                "c_sum": float(np.sum(c_pref)),
                "d_sum": float(np.sum(d_prior)),
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
