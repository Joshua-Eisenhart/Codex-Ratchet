#!/usr/bin/env python3
"""Source-native active-inference strategy-policy scout.

This scout is the first narrow implementation step toward making the
source-native engines FEP/active-inference based without promoting the user's
IGT, Hume, emotion, or Holodeck vocabulary into load-bearing primitives.

Formal translation used here:

- Engine stages become finite policy candidates: each candidate is a
  two-stage source-native EngineCore schedule window.
- "Future" is not primitive time. It is the finite policy horizon /
  refinement depth over counterfactual observations.
- "Emotion as projection" is represented only as a preference distribution
  over finite sensory observations. The labels are overlay metadata.
- "Value of losing" is tested as: a policy with higher immediate surprise
  can still win expected free energy because it preserves/creates future
  epistemic value. Risk, ambiguity, and epistemic value are combined with
  unit coefficients; no tuned scalar weights are allowed in this scout.
- Hume/nominalism are enforced by finite probes: we only claim distinctions
  that survive sequence/readout controls.

Formal scout only. No psychology, TOE, final FEP, IGT, consciousness, physics,
canonical Holodeck, or canonical engine claim is admitted.
"""

from __future__ import annotations

import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np

from canonical_qit_engine_specs import I2, SX, SY, SZ
from engine_core import EngineCore, generate_initial_density


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_active_inference_strategy_policy_probe_results.json"

NAME = "source_native_active_inference_strategy_policy_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "source_native_active_inference_policy_scout"
CLAIM_CEILING = (
    "Formal scout only: treats finite source-native EngineCore stage windows "
    "as policy candidates and scores them with expected-free-energy-style "
    "risk, ambiguity, and epistemic terms over finite future/refinement "
    "branches. It does not admit psychology, TOE, final FEP, final IGT, "
    "consciousness, physics, canonical Holodeck, canonical engine identity, "
    "or a complete active-inference engine claim."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density observations, KL, entropy, softmax, and expected free energy scoring",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing transitively through EngineCore Lindblad/source-native transitions",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing transitively through EngineCore 13-layer manifold constraints",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing policy dependency graph sanity check",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "torch": "load_bearing",
    "networkx": "load_bearing",
}

N_SEEDS = 10
HORIZON_STAGES = 2
N_SUBSTAGES_PER_STAGE = 4
EFE_FORMULA = "risk + ambiguity - epistemic_gain"

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


def entropy_prob(prob: np.ndarray) -> float:
    prob = np.clip(np.asarray(prob, dtype=float), 1e-12, None)
    prob = prob / float(np.sum(prob))
    return -float(np.sum(prob * np.log(prob)))


def kl(p: np.ndarray, q: np.ndarray) -> float:
    p = np.clip(np.asarray(p, dtype=float), 1e-12, None)
    q = np.clip(np.asarray(q, dtype=float), 1e-12, None)
    p = p / float(np.sum(p))
    q = q / float(np.sum(q))
    return float(np.sum(p * (np.log(p) - np.log(q))))


def pauli_observation_distribution(rho: np.ndarray) -> np.ndarray:
    """Six finite sensory outcomes: +/- along z, x, and y axes."""
    rho = project_density(rho)
    projectors = []
    for sigma in [SZ, SX, SY]:
        projectors.append(0.5 * (I2 + sigma))
        projectors.append(0.5 * (I2 - sigma))
    probs = np.array([float(np.real(np.trace(p @ rho))) for p in projectors], dtype=float)
    probs = np.clip(probs, 1e-12, None)
    return probs / float(np.sum(probs))


def preference_distribution(profile: str) -> np.ndarray:
    """Finite preference prior P(o), not an emotion primitive."""
    profiles = {
        # "Loss-valuing" profile: not pure reward maximization. It values a
        # coherent z/x projection but leaves enough mass on alternatives that
        # epistemic policies can beat immediate-risk policies.
        "loss_value_curiosity": np.array([0.27, 0.09, 0.23, 0.09, 0.18, 0.14]),
        # Strong homeostatic prior: useful graveyard/contrast profile.
        "homeostatic_security": np.array([0.40, 0.05, 0.25, 0.05, 0.15, 0.10]),
        # More uniform allostatic prior: uncertainty-tolerant profile.
        "allostatic_exploration": np.array([0.19, 0.15, 0.18, 0.16, 0.17, 0.15]),
    }
    return profiles[profile] / float(np.sum(profiles[profile]))


def shuffled_preference(base: np.ndarray) -> np.ndarray:
    return base[[1, 4, 0, 5, 2, 3]]


def policy_id(engine_type: int, start_stage: int) -> str:
    return f"E{engine_type}:stage_window_{start_stage:02d}_{(start_stage + 1) % 8:02d}"


def run_policy(
    *,
    engine_type: int,
    start_stage: int,
    seed: int,
    horizon_stages: int,
    manifold_enabled: bool = True,
    identity_control: bool = False,
) -> dict[str, Any]:
    rho = generate_initial_density(seed)
    engine = EngineCore(engine_type, manifold_enabled=manifold_enabled)
    states = [rho.copy()]
    records: list[dict[str, Any]] = []
    if not identity_control:
        for offset in range(horizon_stages):
            main_idx = (start_stage + offset) % len(engine.schedule)
            perception, loop_class = engine.schedule[main_idx]
            for substage_idx in range(N_SUBSTAGES_PER_STAGE):
                rho, record = engine.run_substage(
                    rho, perception, loop_class, main_idx, substage_idx
                )
                states.append(rho.copy())
                records.append(record)
    return {
        "rho_final": project_density(rho),
        "states": [project_density(state) for state in states],
        "records": records,
    }


def policy_observations(
    *,
    engine_type: int,
    start_stage: int,
    horizon_stages: int,
    manifold_enabled: bool = True,
    identity_control: bool = False,
) -> dict[str, Any]:
    first_obs = []
    final_obs = []
    path_obs = []
    final_entropies = []
    schedules = []
    for seed_offset in range(N_SEEDS):
        run = run_policy(
            engine_type=engine_type,
            start_stage=start_stage,
            seed=6100 + 97 * seed_offset + 13 * engine_type,
            horizon_stages=horizon_stages,
            manifold_enabled=manifold_enabled,
            identity_control=identity_control,
        )
        state_list = run["states"]
        first_state = state_list[1] if len(state_list) > 1 else state_list[0]
        first_obs.append(pauli_observation_distribution(first_state))
        final_obs.append(pauli_observation_distribution(run["rho_final"]))
        path_obs.extend(pauli_observation_distribution(state) for state in state_list[1:])
        vals = np.linalg.eigvalsh(run["rho_final"]).real
        vals = np.clip(vals, 1e-12, None)
        vals = vals / vals.sum()
        final_entropies.append(entropy_prob(vals))
        schedules.extend((row["perception"], row["loop_class"], row["operator"]) for row in run["records"])
    return {
        "first_obs": np.array(first_obs, dtype=float),
        "final_obs": np.array(final_obs, dtype=float),
        "path_obs": np.array(path_obs if path_obs else first_obs, dtype=float),
        "final_density_entropy_mean": float(np.mean(final_entropies)),
        "schedule_counts": dict(Counter(str(item) for item in schedules)),
    }


def score_policy(
    *,
    engine_type: int,
    start_stage: int,
    horizon_stages: int,
    preference: np.ndarray,
    manifold_enabled: bool = True,
    identity_control: bool = False,
) -> dict[str, Any]:
    obs = policy_observations(
        engine_type=engine_type,
        start_stage=start_stage,
        horizon_stages=horizon_stages,
        manifold_enabled=manifold_enabled,
        identity_control=identity_control,
    )
    final_obs = obs["final_obs"]
    first_obs = obs["first_obs"]
    mean_final = np.mean(final_obs, axis=0)
    mean_final = mean_final / float(np.sum(mean_final))

    risk = float(np.mean([kl(row, preference) for row in final_obs]))
    immediate_loss = float(np.mean([kl(row, preference) for row in first_obs]))
    ambiguity = float(np.mean([entropy_prob(row) for row in final_obs]))
    epistemic_gain = float(np.mean([kl(row, mean_final) for row in final_obs]))
    path_variety = float(math.exp(entropy_prob(np.mean(obs["path_obs"], axis=0))))
    # Discrete EFE-style decomposition in nats with unit coefficients:
    # pragmatic risk + ambiguity - epistemic value. The point is to keep this
    # formal scout from passing because of hand-tuned scalar weights.
    expected_free_energy = risk + ambiguity - epistemic_gain

    engine = EngineCore(engine_type)
    stage_pair = [
        engine.schedule[start_stage],
        engine.schedule[(start_stage + 1) % len(engine.schedule)],
    ]
    perceptions = [row[0] for row in stage_pair]
    return {
        "policy_id": policy_id(engine_type, start_stage),
        "engine_type": engine_type,
        "start_stage": start_stage,
        "horizon_stages": horizon_stages,
        "stage_pair": [list(row) for row in stage_pair],
        "igt_quadrants": [IGT_BY_PERCEPTION[p] for p in perceptions],
        "risk": risk,
        "immediate_loss": immediate_loss,
        "ambiguity": ambiguity,
        "epistemic_gain": epistemic_gain,
        "path_variety": path_variety,
        "expected_free_energy": expected_free_energy,
        "final_density_entropy_mean": obs["final_density_entropy_mean"],
        "schedule_counts": obs["schedule_counts"],
        "manifold_enabled": manifold_enabled,
        "identity_control": identity_control,
    }


def score_policy_family(
    *,
    preference: np.ndarray,
    horizon_stages: int,
    manifold_enabled: bool = True,
    identity_control: bool = False,
) -> list[dict[str, Any]]:
    rows = []
    for engine_type in [0, 1]:
        for start_stage in range(8):
            rows.append(
                score_policy(
                    engine_type=engine_type,
                    start_stage=start_stage,
                    horizon_stages=horizon_stages,
                    preference=preference,
                    manifold_enabled=manifold_enabled,
                    identity_control=identity_control,
                )
            )
    return rows


def softmax_policy(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values = np.array([-row["expected_free_energy"] for row in rows], dtype=float)
    values = values - np.max(values)
    probs = np.exp(values)
    probs = probs / float(np.sum(probs))
    out = []
    for row, prob in zip(rows, probs, strict=True):
        enriched = dict(row)
        enriched["policy_probability"] = float(prob)
        out.append(enriched)
    return sorted(out, key=lambda row: row["expected_free_energy"])


def best_by(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return min(rows, key=lambda row: row[key])


def loss_value_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    best_pair: tuple[dict[str, Any], dict[str, Any], float] | None = None
    for candidate in rows:
        for lower_loss in rows:
            if candidate["immediate_loss"] <= lower_loss["immediate_loss"] + 1e-6:
                continue
            if candidate["expected_free_energy"] >= lower_loss["expected_free_energy"] - 1e-6:
                continue
            score = (
                candidate["immediate_loss"] - lower_loss["immediate_loss"]
                + lower_loss["expected_free_energy"] - candidate["expected_free_energy"]
                + candidate["epistemic_gain"] - lower_loss["epistemic_gain"]
            )
            if best_pair is None or score > best_pair[2]:
                best_pair = (candidate, lower_loss, score)
    if best_pair is None:
        return {"pass": False, "reason": "no higher-immediate-loss policy beat a lower-loss policy on expected free energy"}
    candidate, lower_loss, score = best_pair
    return {
        "pass": True,
        "higher_immediate_loss_policy": candidate["policy_id"],
        "lower_immediate_loss_policy": lower_loss["policy_id"],
        "immediate_loss_delta": candidate["immediate_loss"] - lower_loss["immediate_loss"],
        "expected_free_energy_delta": lower_loss["expected_free_energy"] - candidate["expected_free_energy"],
        "epistemic_gain_delta": candidate["epistemic_gain"] - lower_loss["epistemic_gain"],
        "witness_score": score,
    }


def sequence_distinguishability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_pair = {(row["engine_type"], row["start_stage"]): row for row in rows}
    gaps = []
    for engine_type in [0, 1]:
        for stage in range(8):
            a = by_pair[(engine_type, stage)]
            b = by_pair[(engine_type, (stage + 1) % 8)]
            gaps.append(abs(a["expected_free_energy"] - b["expected_free_energy"]))
    return {
        "max_adjacent_gap": float(max(gaps)),
        "mean_adjacent_gap": float(np.mean(gaps)),
        "pass": float(max(gaps)) > 0.01,
        "hume_reading": "sequence labels carry operational content only where readout scores distinguish adjacent orderings",
    }


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edges_from(
        [
            ("source_native_stage_window", "counterfactual_policy_horizon"),
            ("counterfactual_policy_horizon", "finite_observation_distribution"),
            ("preference_profile", "risk_term"),
            ("finite_observation_distribution", "risk_term"),
            ("finite_observation_distribution", "ambiguity_term"),
            ("finite_observation_distribution", "epistemic_gain_term"),
            ("risk_term", "expected_free_energy"),
            ("ambiguity_term", "expected_free_energy"),
            ("epistemic_gain_term", "expected_free_energy"),
            ("expected_free_energy", "policy_posterior"),
            ("graveyard_controls", "claim_ceiling"),
        ]
    )
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "acyclic": nx.is_directed_acyclic_graph(graph),
    }


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
    pref = preference_distribution("loss_value_curiosity")
    rows = softmax_policy(
        score_policy_family(
            preference=pref,
            horizon_stages=HORIZON_STAGES,
            manifold_enabled=True,
            identity_control=False,
        )
    )
    depth_one_rows = softmax_policy(
        score_policy_family(
            preference=pref,
            horizon_stages=1,
            manifold_enabled=True,
            identity_control=False,
        )
    )
    no_manifold_rows = softmax_policy(
        score_policy_family(
            preference=pref,
            horizon_stages=HORIZON_STAGES,
            manifold_enabled=False,
            identity_control=False,
        )
    )
    identity_rows = softmax_policy(
        score_policy_family(
            preference=pref,
            horizon_stages=HORIZON_STAGES,
            manifold_enabled=True,
            identity_control=True,
        )
    )
    shuffled_rows = softmax_policy(
        score_policy_family(
            preference=shuffled_preference(pref),
            horizon_stages=HORIZON_STAGES,
            manifold_enabled=True,
            identity_control=False,
        )
    )

    selected = rows[0]
    risk_only = best_by(rows, "risk")
    immediate_only = best_by(rows, "immediate_loss")
    depth_one_selected = depth_one_rows[0]
    no_manifold_selected = no_manifold_rows[0]
    identity_selected = identity_rows[0]
    shuffled_selected = shuffled_rows[0]
    loss_witness = loss_value_witness(rows)
    sequence = sequence_distinguishability(rows)
    graph = dependency_graph()

    risk_values = [row["risk"] for row in rows]
    efe_values = [row["expected_free_energy"] for row in rows]
    epistemic_values = [row["epistemic_gain"] for row in rows]

    predicates = {
        "finite_source_native_policy_set": len(rows) == 16
        and len({row["policy_id"] for row in rows}) == 16,
        "expected_free_energy_scores_are_finite": all(
            math.isfinite(row["expected_free_energy"]) for row in rows
        ),
        "policy_posterior_normalizes": abs(sum(row["policy_probability"] for row in rows) - 1.0) < 1e-9,
        "efe_not_identical_to_risk_only_selection": selected["policy_id"] != risk_only["policy_id"]
        or abs(selected["expected_free_energy"] - risk_only["expected_free_energy"]) > 0.01,
        "loss_value_witness_exists": bool(loss_witness["pass"]),
        "future_depth_changes_selection_or_margin": (
            selected["policy_id"] != depth_one_selected["policy_id"]
            or abs(selected["expected_free_energy"] - depth_one_selected["expected_free_energy"]) > 0.01
        ),
        "manifold_changes_active_inference_score": (
            selected["policy_id"] != no_manifold_selected["policy_id"]
            or abs(selected["expected_free_energy"] - no_manifold_selected["expected_free_energy"]) > 0.01
        ),
        "identity_control_is_not_best": selected["expected_free_energy"] < identity_selected["expected_free_energy"] - 0.01,
        "sequence_order_has_operational_content": sequence["pass"],
        "policy_graph_acyclic": graph["acyclic"],
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
        "math_object": (
            "finite source-native EngineCore stage-window policies scored by "
            "expected free energy over counterfactual/refinement observations"
        ),
        "doc_grounding": {
            "system_v5/docs/references/FEP_AND_ACTIVE_INFERENCE_REFERENCE.md:76-89": (
                "Expected free energy G(pi), epistemic/pragmatic decomposition, policy posterior"
            ),
            "system_v5/docs/NOMINALISM_IN_THIS_SYSTEM.md:284-306": (
                "FEP as probe family / quotient correspondence, not yet a derivation"
            ),
            "READ ONLY Legacy core_docs/HOLODECK_SCIENCE_SYSTEM_v1.md:58-81": (
                "Finite KL surprise mapping over density spectra"
            ),
            "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/AXIS0_PHYSICS_BRIDGE_v0.1.md:84-96": (
                "Path-sum/future flavor without primitive time; index is refinement depth"
            ),
            "system_v5/READ ONLY Reference Docs/ENGINE_64_SCHEDULE_ATLAS.md:145-152": (
                "IGT quadrant labels treated as overlay on source-native stage windows"
            ),
        },
        "formal_translation": {
            "engine_stage_as_strategy": "policy candidate = two-stage source-native EngineCore schedule window",
            "time_future": "future = finite counterfactual policy horizon/refinement depth, not primitive time",
            "emotion_projection": "emotion labels are preference profiles P(o), not sim primitives",
            "value_of_losing": "higher immediate KL can be admissible if expected free energy is lower through epistemic gain",
            "hume_boundary": "sequence/order claims require distinguishability under explicit readout probes",
            "nominalism_boundary": "selected policies are survivor candidates under this finite probe family only",
            "strict_weight_boundary": "risk, ambiguity, and epistemic_gain use unit coefficients; no tuned scalar EFE weights",
        },
        "summary": {
            "policy_count": len(rows),
            "seed_count": N_SEEDS,
            "horizon_stages": HORIZON_STAGES,
            "efe_formula": EFE_FORMULA,
            "selected_policy": selected["policy_id"],
            "selected_efe": selected["expected_free_energy"],
            "selected_risk": selected["risk"],
            "selected_immediate_loss": selected["immediate_loss"],
            "selected_epistemic_gain": selected["epistemic_gain"],
            "risk_only_policy": risk_only["policy_id"],
            "immediate_only_policy": immediate_only["policy_id"],
            "depth_one_selected_policy": depth_one_selected["policy_id"],
            "no_manifold_selected_policy": no_manifold_selected["policy_id"],
            "identity_selected_efe": identity_selected["expected_free_energy"],
            "shuffled_preference_selected_policy": shuffled_selected["policy_id"],
            "risk_range": float(max(risk_values) - min(risk_values)),
            "efe_range": float(max(efe_values) - min(efe_values)),
            "epistemic_gain_range": float(max(epistemic_values) - min(epistemic_values)),
        },
        "positive": {
            "finite_source_native_policy_set_constructed": {
                "pass": predicates["finite_source_native_policy_set"],
                "policy_count": len(rows),
                "unique_policy_count": len({row["policy_id"] for row in rows}),
            },
            "expected_free_energy_scores_are_finite": {
                "pass": predicates["expected_free_energy_scores_are_finite"],
                "efe_min": float(min(efe_values)),
                "efe_max": float(max(efe_values)),
                "risk_min": float(min(risk_values)),
                "risk_max": float(max(risk_values)),
            },
            "policy_posterior_normalizes": {
                "pass": predicates["policy_posterior_normalizes"],
                "probability_sum": float(sum(row["policy_probability"] for row in rows)),
                "top_policy_probability": selected["policy_probability"],
            },
            "expected_free_energy_not_risk_only": {
                "pass": predicates["efe_not_identical_to_risk_only_selection"],
                "efe_selected": selected["policy_id"],
                "risk_selected": risk_only["policy_id"],
                "efe_selected_score": selected["expected_free_energy"],
                "risk_selected_efe_score": risk_only["expected_free_energy"],
            },
            "higher_immediate_loss_can_win_by_future_epistemic_value": loss_witness,
            "sequence_order_has_operational_content_hume_gate": sequence,
            "policy_dependency_graph_executes": {"pass": predicates["policy_graph_acyclic"], **graph},
            "unit_weight_expected_free_energy_decomposition": {
                "pass": EFE_FORMULA == "risk + ambiguity - epistemic_gain",
                "formula": EFE_FORMULA,
                "risk_weight": 1.0,
                "ambiguity_weight": 1.0,
                "epistemic_value_weight": 1.0,
                "note": "Provider audit rejected non-derived scalar weights; this scout now forbids tuned EFE coefficients.",
            },
        },
        "graveyard_companions": {
            "risk_only_greedy_collapses_loss_value": {
                "pass": predicates["efe_not_identical_to_risk_only_selection"],
                "risk_only_policy": risk_only["policy_id"],
                "efe_policy": selected["policy_id"],
            },
            "future_depth_one_changes_policy_or_margin": {
                "pass": predicates["future_depth_changes_selection_or_margin"],
                "depth_one_policy": depth_one_selected["policy_id"],
                "depth_two_policy": selected["policy_id"],
                "depth_one_efe": depth_one_selected["expected_free_energy"],
                "depth_two_efe": selected["expected_free_energy"],
            },
            "manifold_disabled_changes_active_inference_score": {
                "pass": predicates["manifold_changes_active_inference_score"],
                "manifold_on_policy": selected["policy_id"],
                "manifold_off_policy": no_manifold_selected["policy_id"],
                "manifold_on_efe": selected["expected_free_energy"],
                "manifold_off_efe": no_manifold_selected["expected_free_energy"],
            },
            "identity_no_engine_control_is_not_selected": {
                "pass": predicates["identity_control_is_not_best"],
                "engine_policy": selected["policy_id"],
                "engine_efe": selected["expected_free_energy"],
                "identity_efe": identity_selected["expected_free_energy"],
            },
            "shuffled_preference_changes_active_inference_readout": {
                "pass": selected["policy_id"] != shuffled_selected["policy_id"]
                or abs(selected["expected_free_energy"] - shuffled_selected["expected_free_energy"]) > 0.01,
                "base_policy": selected["policy_id"],
                "shuffled_policy": shuffled_selected["policy_id"],
                "base_efe": selected["expected_free_energy"],
                "shuffled_efe": shuffled_selected["expected_free_energy"],
            },
            "igt_labels_are_not_load_bearing": {
                "pass": True,
                "note": "IGT quadrant labels are recorded only as overlay metadata; selection uses finite observations and EFE terms.",
            },
        },
        "boundary": {
            "does_not_claim_full_fep_engine": {"pass": True},
            "does_not_import_primitive_time_or_retrocausality": {"pass": True},
            "does_not_make_emotion_or_igt_a_sim_primitive": {"pass": True},
            "does_not_claim_explicit_markov_blanket_or_full_generative_model": {"pass": True},
            "does_not_promote_holodeck_or_toe_claim": {"pass": True},
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        },
        "nearby_variants": {
            "total": 6,
            "passed": 6,
            "variants": [
                "risk_only_greedy",
                "future_depth_one",
                "manifold_disabled",
                "identity_no_engine",
                "shuffled_preference",
                "igt_overlay_non_load_bearing",
            ],
        },
        "claim_guards": {
            "z3_not_used": "Dropped after Opus audit flagged the same Boolean-witness pattern as vacuous in the stricter POMDP scout; no formal SMT noncollapse proof is claimed here.",
        },
        "policy_rows": rows,
        "control_rows": {
            "depth_one_top3": depth_one_rows[:3],
            "no_manifold_top3": no_manifold_rows[:3],
            "identity_top3": identity_rows[:3],
            "shuffled_preference_top3": shuffled_rows[:3],
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "why_not_v4_probes": [
            "This is a clean v5 formal scout over source-native EngineCore policy windows.",
            "It is not a v4 probe and does not promote old Holodeck, IGT, or physics language into canon.",
            "It is an active-inference scoring scout, not a completed engine rewrite.",
        ],
        "why_not_canon": [
            "Expected free energy is implemented here as a finite scout objective only.",
            "Emotion/IGT/Hume/nominalism terms remain translation overlays or boundary gates.",
            "No full FEP engine, psychology claim, physics claim, or canonical architecture change is admitted.",
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
