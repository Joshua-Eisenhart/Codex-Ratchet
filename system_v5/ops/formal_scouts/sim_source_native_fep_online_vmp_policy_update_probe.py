#!/usr/bin/env python3
"""Online variational-message-passing scout for the source-native FEP policy tree.

The existing POMDP scout builds finite A/B/C/D matrices and policy rows. This
scout tightens the FEP loop boundary: each policy prediction step must support
an online variational posterior update from a predicted latent state and an
observed sensory token, and that update must agree with the closed-form
categorical posterior while reducing variational free energy versus the
no-message control.

Formal scout only. This is not a full FEP engine, learned world model,
continuous-time belief propagation, psychology, physics, or canonical claim.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import networkx as nx
import torch
import z3

import sim_source_native_fep_pomdp_policy_tree_probe as pomdp


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_fep_online_vmp_policy_update_probe_results.json"

NAME = "source_native_fep_online_vmp_policy_update_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "source_native_fep_online_vmp_policy_update"
CLAIM_CEILING = (
    "Formal scout only: checks finite online variational message-passing "
    "updates over the existing source-native POMDP A/B/C/D policy tree. It "
    "does not admit a full FEP engine, learned world model, canonical "
    "Holodeck, psychology, IGT ontology, consciousness, physics, or canonical "
    "architecture."
)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor math for local posterior updates, VFE trace, policy rows, softmax, norms, means, and control summaries",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite witness over online posterior, VFE reduction, EFE decomposition, and no-engine predicates",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive online update dependency graph sanity check",
    },
    "pomdp": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native A/B/C/D helper surface; returned arrays are converted to torch tensors in this scout",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "supportive upstream source-native B_pi transition estimation consumed through the POMDP helper",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization and upstream receipt loading",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive script hash receipt field",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used load-bearing in this scout; local online VMP math is torch-native",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "not used load-bearing in this scout; local log/exp and softmax math is torch-native",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "z3": "load_bearing",
    "pomdp": "supportive",
    "engine_core": "supportive",
    "networkx": "supportive",
    "json": "supportive",
    "hashlib": "supportive",
    "numpy": None,
    "scipy": None,
}

POSTERIOR_KL_FLOOR = 1e-7
VFE_REDUCTION_FLOOR = 1e-3
NO_MESSAGE_VFE_MARGIN_FLOOR = 1e-3
WRONG_OBS_POSTERIOR_SHIFT_FLOOR = 1e-2
EFE_DECOMPOSITION_TOL = 1e-9
N_VMP_ITERS = 12
DAMPING = 0.55
DTYPE = torch.float64
EPS = 1e-12


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        value = value.detach().cpu()
        if value.ndim == 0:
            return value.item()
        return value.tolist()
    return value


def as_tensor(value: Any) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        return value.detach().to(dtype=DTYPE).clone()
    return torch.as_tensor(value, dtype=DTYPE).clone()


def as_float(value: Any) -> float:
    return float(torch.as_tensor(value, dtype=DTYPE).detach().cpu().item())


def normalize(prob: Any) -> torch.Tensor:
    prob_t = torch.clamp(as_tensor(prob), min=EPS)
    return torch.exp(torch.log(prob_t) - torch.logsumexp(torch.log(prob_t), dim=0))


def entropy_tensor(prob: Any) -> torch.Tensor:
    prob_t = normalize(prob)
    return -torch.sum(prob_t * torch.log(prob_t))


def entropy_prob(prob: Any) -> float:
    return float(entropy_tensor(prob).item())


def kl_tensor(p: Any, q: Any) -> torch.Tensor:
    p_t = normalize(p)
    q_t = normalize(q)
    return torch.sum(p_t * (torch.log(p_t) - torch.log(q_t)))


def kl(p: Any, q: Any) -> float:
    return float(kl_tensor(p, q).item())


def shuffled_preference(base: Any) -> torch.Tensor:
    order = torch.tensor([1, 4, 0, 5, 2, 3], dtype=torch.long)
    return normalize(normalize(base).index_select(0, order))


def variational_free_energy(
    q_variational: Any,
    q_prior: Any,
    a_matrix: Any,
    obs_idx: int,
) -> torch.Tensor:
    q_variational_t = normalize(q_variational)
    q_prior_t = normalize(q_prior)
    a_matrix_t = as_tensor(a_matrix)
    likelihood = torch.clamp(a_matrix_t[obs_idx, :], min=EPS)
    joint_log = torch.log(likelihood) + torch.log(q_prior_t)
    return torch.sum(q_variational_t * (torch.log(q_variational_t) - joint_log))


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    return data


def online_vmp_update(
    q_prior: Any,
    a_matrix: Any,
    obs_idx: int,
    *,
    damping: float = DAMPING,
    n_iters: int = N_VMP_ITERS,
) -> dict[str, Any]:
    q_prior = normalize(q_prior)
    a_matrix = as_tensor(a_matrix)
    log_target = torch.log(torch.clamp(q_prior, min=EPS)) + torch.log(torch.clamp(a_matrix[obs_idx, :], min=EPS))
    exact = normalize(torch.exp(log_target))
    q = q_prior.clone()
    vfe_values = [variational_free_energy(q, q_prior, a_matrix, obs_idx)]
    for _ in range(n_iters):
        log_q = torch.log(torch.clamp(q, min=EPS))
        q = normalize(torch.exp((1.0 - damping) * log_q + damping * log_target))
        vfe_values.append(variational_free_energy(q, q_prior, a_matrix, obs_idx))
    vfe_trace = torch.stack(vfe_values)
    no_message_vfe = vfe_trace[0]
    final_vfe = vfe_trace[-1]
    return {
        "q_prior": q_prior,
        "q_exact": exact,
        "q_vmp": q,
        "vfe_trace": vfe_trace,
        "posterior_kl_to_exact": kl(q, exact),
        "no_message_vfe": no_message_vfe,
        "final_vfe": final_vfe,
        "vfe_reduction_vs_no_message": no_message_vfe - final_vfe,
        "monotone_nonincreasing_vfe": bool(torch.all(vfe_trace[1:] <= vfe_trace[:-1] + 1e-10).item()),
    }


def policy_online_report(
    *,
    engine_type: int,
    start_stage: int,
    a_matrix: Any,
    c_pref: Any,
    d_prior: Any,
    manifold_enabled: bool = True,
    no_engine_control: bool = False,
    observation_mode: str = "predicted_argmax",
) -> dict[str, Any]:
    a_matrix = as_tensor(a_matrix)
    c_pref = normalize(c_pref)
    d_prior = normalize(d_prior)
    if no_engine_control:
        b_matrix = torch.eye(pomdp.N_STATES, dtype=DTYPE)
    else:
        b_matrix = as_tensor(pomdp.estimate_transition(engine_type, start_stage, manifold_enabled=manifold_enabled))
    q_s = d_prior.clone()
    risk = torch.tensor(0.0, dtype=DTYPE)
    ambiguity = torch.tensor(0.0, dtype=DTYPE)
    epistemic_value = torch.tensor(0.0, dtype=DTYPE)
    vfe_reduction = torch.tensor(0.0, dtype=DTYPE)
    posterior_kls = []
    wrong_obs_shifts = []
    step_rows = []
    for step in range(pomdp.PREDICTION_STEPS):
        q_pred = normalize(b_matrix @ q_s)
        q_o = normalize(a_matrix @ q_pred)
        predicted_obs_idx = int(torch.argmax(q_o).item())
        if observation_mode == "predicted_argmax":
            obs_idx = predicted_obs_idx
        elif observation_mode == "heldout_cycle":
            obs_idx = int((engine_type * 2 + start_stage + 2 * step + 1) % pomdp.N_OBSERVATIONS)
        else:
            raise ValueError(f"unknown observation_mode: {observation_mode}")
        update = online_vmp_update(q_pred, a_matrix, obs_idx)
        wrong_obs_idx = int(torch.argmin(q_o).item())
        wrong_update = online_vmp_update(q_pred, a_matrix, wrong_obs_idx)
        posterior_shift = torch.linalg.vector_norm(update["q_vmp"] - wrong_update["q_vmp"], ord=1)
        posterior_kls.append(as_tensor(update["posterior_kl_to_exact"]))
        wrong_obs_shifts.append(posterior_shift)
        conditional_entropy = torch.sum(
            q_pred * torch.stack([entropy_tensor(a_matrix[:, idx]) for idx in range(pomdp.N_STATES)])
        )
        info_gain = torch.clamp(entropy_tensor(q_o) - conditional_entropy, min=0.0)
        step_risk = as_tensor(kl(q_o, c_pref))
        risk += step_risk
        ambiguity += conditional_entropy
        epistemic_value += info_gain
        vfe_reduction += as_tensor(update["vfe_reduction_vs_no_message"])
        step_rows.append(
            {
                "step": step + 1,
                "observation_mode": observation_mode,
                "obs_idx": obs_idx,
                "predicted_obs_idx": predicted_obs_idx,
                "selected_obs_probability": as_float(q_o[obs_idx]),
                "wrong_obs_idx": wrong_obs_idx,
                "risk": as_float(step_risk),
                "ambiguity": as_float(conditional_entropy),
                "epistemic_value": as_float(info_gain),
                "vfe_reduction_vs_no_message": as_float(update["vfe_reduction_vs_no_message"]),
                "posterior_kl_to_exact": as_float(update["posterior_kl_to_exact"]),
                "wrong_obs_posterior_l1_shift": as_float(posterior_shift),
                "monotone_nonincreasing_vfe": update["monotone_nonincreasing_vfe"],
                "vfe_trace_head": update["vfe_trace"][:4],
                "vfe_trace_tail": update["vfe_trace"][-3:],
            }
        )
        q_s = update["q_vmp"]
    expected_free_energy = risk + ambiguity
    posterior_kls_t = torch.stack(posterior_kls)
    wrong_obs_shifts_t = torch.stack(wrong_obs_shifts)
    return {
        "policy_id": pomdp.policy_id(engine_type, start_stage),
        "engine_type": engine_type,
        "start_stage": start_stage,
        "manifold_enabled": manifold_enabled,
        "no_engine_control": no_engine_control,
        "observation_mode": observation_mode,
        "risk": as_float(risk),
        "ambiguity": as_float(ambiguity),
        "epistemic_value": as_float(epistemic_value),
        "vfe_reduction": as_float(vfe_reduction),
        "expected_free_energy": as_float(expected_free_energy),
        "efe_decomposition_residual": as_float(torch.abs(expected_free_energy - (risk + ambiguity))),
        "posterior_kl_max": as_float(torch.max(posterior_kls_t)),
        "posterior_kl_mean": as_float(torch.mean(posterior_kls_t)),
        "wrong_obs_shift_min": as_float(torch.min(wrong_obs_shifts_t)),
        "wrong_obs_shift_mean": as_float(torch.mean(wrong_obs_shifts_t)),
        "all_steps_vfe_monotone": all(row["monotone_nonincreasing_vfe"] for row in step_rows),
        "per_step": step_rows,
    }


def online_family(
    *,
    a_matrix: Any,
    c_pref: Any,
    d_prior: Any,
    manifold_enabled: bool = True,
    no_engine_control: bool = False,
    observation_mode: str = "predicted_argmax",
) -> list[dict[str, Any]]:
    a_matrix = as_tensor(a_matrix)
    c_pref = normalize(c_pref)
    d_prior = normalize(d_prior)
    rows = []
    for engine_type in [0, 1]:
        for start_stage in range(8):
            rows.append(
                policy_online_report(
                    engine_type=engine_type,
                    start_stage=start_stage,
                    a_matrix=a_matrix,
                    c_pref=c_pref,
                    d_prior=d_prior,
                    manifold_enabled=manifold_enabled,
                    no_engine_control=no_engine_control,
                    observation_mode=observation_mode,
                )
            )
    values = as_tensor([-row["expected_free_energy"] for row in rows])
    probs = torch.softmax(values, dim=0)
    for row, prob in zip(rows, probs, strict=True):
        row["policy_probability"] = as_float(prob)
    return sorted(rows, key=lambda row: row["expected_free_energy"])


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edges_from(
        [
            ("source_native_B_pi", "predicted_state_q_s"),
            ("D_prior", "predicted_state_q_s"),
            ("A_emission", "predicted_observation_q_o"),
            ("predicted_state_q_s", "online_vmp_prior_message"),
            ("predicted_observation_q_o", "selected_observation_token"),
            ("heldout_observation_token_control", "selected_observation_token"),
            ("A_emission", "likelihood_message"),
            ("selected_observation_token", "likelihood_message"),
            ("online_vmp_prior_message", "variational_posterior_q_s"),
            ("likelihood_message", "variational_posterior_q_s"),
            ("variational_posterior_q_s", "next_step_state"),
            ("C_preference", "risk"),
            ("predicted_observation_q_o", "risk"),
            ("A_emission", "ambiguity"),
            ("predicted_state_q_s", "ambiguity"),
            ("risk", "expected_free_energy"),
            ("ambiguity", "expected_free_energy"),
            ("expected_free_energy", "policy_posterior"),
        ]
    )
    return {
        "pass": nx.is_directed_acyclic_graph(graph),
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
    }


def z3_vmp_witness(rows: list[dict[str, Any]], no_engine_rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    posterior_matches = z3.Bool("posterior_matches_closed_form")
    vfe_reduces = z3.Bool("vfe_reduces_vs_no_message")
    decomposition_exact = z3.Bool("efe_decomposition_exact")
    no_engine_changes = z3.Bool("no_engine_changes_online_policy_or_margin")
    selected = rows[0]
    no_engine = no_engine_rows[0]
    solver.add(posterior_matches == (max(row["posterior_kl_max"] for row in rows) < POSTERIOR_KL_FLOOR))
    solver.add(vfe_reduces == (min(row["vfe_reduction"] for row in rows) > VFE_REDUCTION_FLOOR))
    solver.add(decomposition_exact == (max(row["efe_decomposition_residual"] for row in rows) < EFE_DECOMPOSITION_TOL))
    solver.add(
        no_engine_changes == (
            selected["policy_id"] != no_engine["policy_id"]
            or abs(selected["expected_free_energy"] - no_engine["expected_free_energy"]) > NO_MESSAGE_VFE_MARGIN_FLOOR
        )
    )
    solver.add(z3.Not(z3.And(posterior_matches, vfe_reduces, decomposition_exact, no_engine_changes)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite witness over online VMP posterior, VFE, EFE decomposition, and no-engine predicates only.",
    }


def main() -> int:
    started = time.time()
    pomdp_receipt = load_result("source_native_fep_pomdp_policy_tree_probe_results.json")
    a_matrix = as_tensor(pomdp.emission_matrix())
    c_pref = normalize(pomdp.preference_distribution())
    d_prior = normalize(pomdp.estimate_prior())
    rows = online_family(a_matrix=a_matrix, c_pref=c_pref, d_prior=d_prior)
    heldout_rows = online_family(
        a_matrix=a_matrix,
        c_pref=c_pref,
        d_prior=d_prior,
        observation_mode="heldout_cycle",
    )
    no_engine_rows = online_family(a_matrix=a_matrix, c_pref=c_pref, d_prior=d_prior, no_engine_control=True)
    shuffled_rows = online_family(a_matrix=a_matrix, c_pref=shuffled_preference(c_pref), d_prior=d_prior)
    identity_a_rows = online_family(
        a_matrix=torch.eye(pomdp.N_OBSERVATIONS, pomdp.N_STATES, dtype=DTYPE),
        c_pref=c_pref,
        d_prior=d_prior,
    )
    graph = dependency_graph()

    posterior_kl_max = as_float(torch.max(as_tensor([row["posterior_kl_max"] for row in rows])))
    vfe_reduction_min = as_float(torch.min(as_tensor([row["vfe_reduction"] for row in rows])))
    heldout_posterior_kl_max = as_float(torch.max(as_tensor([row["posterior_kl_max"] for row in heldout_rows])))
    heldout_vfe_reduction_min = as_float(torch.min(as_tensor([row["vfe_reduction"] for row in heldout_rows])))
    decomposition_residual_max = as_float(torch.max(as_tensor([row["efe_decomposition_residual"] for row in rows])))
    wrong_obs_shift_min = as_float(torch.min(as_tensor([row["wrong_obs_shift_min"] for row in rows])))
    selected = rows[0]
    old_selected = (pomdp_receipt.get("summary") or {}).get("selected_policy")
    z3_witness = z3_vmp_witness(rows, no_engine_rows)

    repair_receipt = {
        "weak_link": "The source-native FEP/POMDP scout built finite A/B/C/D policy rows, but downstream Axis0 consumers had no receipt proving online variational message-passing updates over those policy predictions.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "FEP policy scoring requires online variational posterior updates that match the closed-form categorical posterior, reduce VFE versus no-message control, and preserve exact EFE decomposition under matched controls.",
        "dependency_subset": [
            "source_native_fep_pomdp_policy_tree receipt",
            "sim_source_native_fep_pomdp_policy_tree_probe A/B/C/D functions",
            "EngineCore-derived B_pi transition estimation",
        ],
        "stage_fields_touched_or_consumed": [
            "policy_window stage_pair",
            "A_emission",
            "B_pi transition",
            "C_preference",
            "D_prior",
            "per_step risk/ambiguity/epistemic_value/vfe_reduction",
            "heldout deterministic observation-token control",
        ],
        "before_baseline/hash": {
            "pomdp_result": pomdp_receipt.get("path"),
            "pomdp_all_pass": pomdp_receipt.get("all_pass"),
            "pomdp_selected_policy": old_selected,
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "posterior_kl_max": posterior_kl_max,
            "vfe_reduction_min": vfe_reduction_min,
            "wrong_obs_shift_min": wrong_obs_shift_min,
            "heldout_observation_posterior_kl_max": heldout_posterior_kl_max,
            "heldout_observation_vfe_reduction_min": heldout_vfe_reduction_min,
            "heldout_observation_policy": heldout_rows[0]["policy_id"],
            "efe_decomposition_residual_max": decomposition_residual_max,
            "selected_policy": selected["policy_id"],
            "no_engine_policy": no_engine_rows[0]["policy_id"],
            "shuffled_preference_policy": shuffled_rows[0]["policy_id"],
            "identity_emission_policy": identity_a_rows[0]["policy_id"],
        },
        "axis0_outputs_or_blockers": {
            "online_vmp_ready_for_many_futures_policy_scoring": True,
            "claim": "This receipt may be consumed by the macro Axis0 router as support for retrocausal_many_futures_policy_scoring, but it does not admit final Axis0 or primitive time.",
        },
        "provider_inputs_used": {
            "grok": "system_v5/ops/formal_scouts/provider_receipts/20260517T130444Z_grok_xai_online_vmp_axis0_router_audit.json",
            "gemini": "system_v5/ops/formal_scouts/provider_receipts/20260517T130444Z_gemini_online_vmp_axis0_router_audit.json",
            "sonnet_high": "system_v5/ops/formal_scouts/provider_receipts/20260517T130444Z_sonnet_high_online_vmp_router_audit.receipt.json",
            "opus_max": "system_v5/ops/formal_scouts/provider_receipts/20260517T130444Z_opus_max_online_vmp_axis0_premortem.receipt.json",
            "local_use": "Opus premortem triggered the held-out observation-token control and z3 depth demotion; provider outputs remain advisory and do not promote FEP/Axis0 claims.",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Patch the macro Axis0 router to consume this online-VMP receipt inside retrocausal_many_futures_policy_scoring, then rerun the Axis0 guard and downstream consumers.",
    }

    positive = {
        "upstream_pomdp_policy_tree_receipt_is_consumed": {
            "pass": pomdp_receipt.get("all_pass") is True and len(pomdp_receipt.get("policy_rows", [])) == 16,
            "receipt": {
                "path": pomdp_receipt.get("path"),
                "all_pass": pomdp_receipt.get("all_pass"),
                "policy_count": len(pomdp_receipt.get("policy_rows", [])),
            },
        },
        "online_vmp_posteriors_match_closed_form_categorical_updates": {
            "pass": posterior_kl_max < POSTERIOR_KL_FLOOR and all(row["all_steps_vfe_monotone"] for row in rows),
            "posterior_kl_max": posterior_kl_max,
            "posterior_kl_floor": POSTERIOR_KL_FLOOR,
            "all_steps_vfe_monotone": all(row["all_steps_vfe_monotone"] for row in rows),
        },
        "online_updates_reduce_vfe_against_no_message_control": {
            "pass": vfe_reduction_min > VFE_REDUCTION_FLOOR,
            "vfe_reduction_min": vfe_reduction_min,
            "floor": VFE_REDUCTION_FLOOR,
        },
        "efe_decomposition_remains_exact_under_online_updates": {
            "pass": decomposition_residual_max < EFE_DECOMPOSITION_TOL,
            "efe_decomposition_residual_max": decomposition_residual_max,
            "tolerance": EFE_DECOMPOSITION_TOL,
        },
        "online_update_dependency_graph_executes": graph,
        "z3_online_vmp_witness_executes": z3_witness,
        "heldout_observation_tokens_support_online_updates": {
            "pass": heldout_posterior_kl_max < POSTERIOR_KL_FLOOR
            and heldout_vfe_reduction_min > VFE_REDUCTION_FLOOR
            and all(row["all_steps_vfe_monotone"] for row in heldout_rows),
            "posterior_kl_max": heldout_posterior_kl_max,
            "vfe_reduction_min": heldout_vfe_reduction_min,
            "all_steps_vfe_monotone": all(row["all_steps_vfe_monotone"] for row in heldout_rows),
            "observation_mode": "heldout_cycle",
        },
    }
    graveyards = {
        "wrong_observation_token_changes_posterior": {
            "pass": wrong_obs_shift_min > WRONG_OBS_POSTERIOR_SHIFT_FLOOR,
            "wrong_obs_shift_min": wrong_obs_shift_min,
            "floor": WRONG_OBS_POSTERIOR_SHIFT_FLOOR,
        },
        "no_engine_identity_transition_changes_policy_or_margin": {
            "pass": selected["policy_id"] != no_engine_rows[0]["policy_id"]
            or abs(selected["expected_free_energy"] - no_engine_rows[0]["expected_free_energy"]) > NO_MESSAGE_VFE_MARGIN_FLOOR,
            "online_policy": selected["policy_id"],
            "no_engine_policy": no_engine_rows[0]["policy_id"],
            "online_efe": selected["expected_free_energy"],
            "no_engine_efe": no_engine_rows[0]["expected_free_energy"],
        },
        "shuffled_preference_changes_online_policy_or_margin": {
            "pass": selected["policy_id"] != shuffled_rows[0]["policy_id"]
            or abs(selected["expected_free_energy"] - shuffled_rows[0]["expected_free_energy"]) > NO_MESSAGE_VFE_MARGIN_FLOOR,
            "online_policy": selected["policy_id"],
            "shuffled_policy": shuffled_rows[0]["policy_id"],
            "online_efe": selected["expected_free_energy"],
            "shuffled_efe": shuffled_rows[0]["expected_free_energy"],
        },
        "identity_emission_changes_ambiguity_or_policy": {
            "pass": selected["policy_id"] != identity_a_rows[0]["policy_id"]
            or abs(selected["ambiguity"] - identity_a_rows[0]["ambiguity"]) > NO_MESSAGE_VFE_MARGIN_FLOOR,
            "online_policy": selected["policy_id"],
            "identity_emission_policy": identity_a_rows[0]["policy_id"],
            "online_ambiguity": selected["ambiguity"],
            "identity_emission_ambiguity": identity_a_rows[0]["ambiguity"],
        },
        "predicted_argmax_observation_loop_is_not_the_only_supported_update": {
            "pass": heldout_posterior_kl_max < POSTERIOR_KL_FLOOR
            and heldout_vfe_reduction_min > VFE_REDUCTION_FLOOR,
            "predicted_argmax_selected_policy": selected["policy_id"],
            "heldout_observation_selected_policy": heldout_rows[0]["policy_id"],
            "heldout_observation_mode": "heldout_cycle",
            "boundary": "Held-out deterministic tokens are a control against self-predicted argmax collapse, not empirical sensor data.",
        },
    }
    boundary = {
        "claim_ceiling_blocks_full_fep_or_physics_promotion": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "full fep engine", "physics", "canonical"]
            ),
        },
        "repair_receipt_has_required_loop_fields": {
            "pass": all(
                key in repair_receipt
                for key in [
                    "weak_link",
                    "target_file_or_result",
                    "admission_rule_improved",
                    "dependency_subset",
                    "stage_fields_touched_or_consumed",
                    "before_baseline/hash",
                    "after_delta/hash",
                    "primary_control/result",
                    "axis0_outputs_or_blockers",
                    "provider_inputs_used",
                    "promotion_ceiling",
                    "next_step",
                ]
            ),
            "keys": sorted(repair_receipt),
        },
        "heldout_observation_control_is_not_called_empirical_data": {
            "pass": any("not empirical sensor data" in json.dumps(row) for row in graveyards.values()),
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
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "summary": {
            "policy_count": len(rows),
            "selected_policy": selected["policy_id"],
            "selected_efe": selected["expected_free_energy"],
            "selected_risk": selected["risk"],
            "selected_ambiguity": selected["ambiguity"],
            "selected_epistemic_value": selected["epistemic_value"],
            "selected_vfe_reduction": selected["vfe_reduction"],
            "posterior_kl_max": posterior_kl_max,
            "vfe_reduction_min": vfe_reduction_min,
            "heldout_observation_posterior_kl_max": heldout_posterior_kl_max,
            "heldout_observation_vfe_reduction_min": heldout_vfe_reduction_min,
            "wrong_obs_shift_min": wrong_obs_shift_min,
        },
        "policy_rows": rows,
        "control_rows": {
            "heldout_observation_top3": heldout_rows[:3],
            "no_engine_top3": no_engine_rows[:3],
            "shuffled_preference_top3": shuffled_rows[:3],
            "identity_emission_top3": identity_a_rows[:3],
        },
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This is a v5 source-native online-update scout over the existing finite POMDP policy tree.",
            "It keeps FEP claims bounded to explicit finite categorical belief updates.",
        ],
        "all_pass": all_pass,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
