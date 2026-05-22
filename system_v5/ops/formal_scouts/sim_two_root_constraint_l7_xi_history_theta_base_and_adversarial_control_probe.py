#!/usr/bin/env python3
"""L7 Xi-history theta-base and adversarial-control bridge probe.

D119 provider audit found that the first L7 schedule-history bridge was
executable but not control-separated, and that its canonical-vs-no-coupling gap
could be partially carried by an unconditional theta_base floor. This scout
keeps the same exact torch QIT engine runtime, removes that floor, and tests
whether the history-specific terms themselves survive structured and
norm-matched adversarial controls.

This is a bridge-falsifier packet. It can kill or keep open the current L7
bridge family; it cannot promote final Axis0 closure, full tensor-network
convergence, PEPS/PEPS3D closure, real attractor basins, or final manifold
admission.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_l7_xi_history_theta_base_and_adversarial_control_probe_results.json"

NAME = "two_root_constraint_l7_xi_history_theta_base_and_adversarial_control_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_l7_theta_base_adversarial_control_bridge"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_l7_xi_history_theta_base_adversarial_control"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal L7 bridge falsifier only: ablates the unconditional theta_base floor "
    "and compares schedule-history Xi terms against structured and norm-matched "
    "controls. It cannot promote final Axis0 closure, full tensor-network "
    "convergence, PEPS/PEPS3D closure, real scale-level attractor basins, or "
    "final manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact QIT engine schedules, bridge unitaries, random Hermitian controls, and Phi0 entropy readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing schedule-transform transition graph and control-family topology witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing status guard separating killed/open/survived L7 bridge states from final admission",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and receipt provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

TOKENS = ("L", "R")
WORD_LENGTHS = (2, 3, 4, 5)
TAU_VALUES = (0.5, 1.0)
SEEDS = tuple(range(32))
THETA_BASE = 0.17
PHI0_TOL = 1.0e-3
CONTROL_MARGIN = 1.0e-3
SIGMA_MULTIPLIER = 2.0

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "l7_bridge_result": RESULT_DIR / "two_root_constraint_l7_xi_history_phi0_bridge_probe_results.json",
    "axis0_entropy_ratchet_result": RESULT_DIR
    / "two_root_constraint_axis0_layered_entropy_ratchet_audit_probe_results.json",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
    "handoff": REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    return qit.jsonable(value)


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path), "exists": path.exists()} for name, path in SOURCE_FILES.items()}


def entropy(rho: torch.Tensor, eps: float = 1.0e-12) -> float:
    herm = 0.5 * (rho + rho.conj().T)
    vals = torch.linalg.eigvalsh(herm).real.clamp_min(eps)
    return float((-vals * torch.log(vals)).sum().item())


def kron2(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.kron(left, right)


def partial_trace_two_qubit(rho_ab: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    shaped = rho_ab.reshape(2, 2, 2, 2)
    rho_a = torch.einsum("abcb->ac", shaped)
    rho_b = torch.einsum("abac->bc", shaped)
    return qit.normalize_density(rho_a), qit.normalize_density(rho_b)


def phi0_readout_pair(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_a, rho_b = partial_trace_two_qubit(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho_ab)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_A_colon_B": s_a + s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_c_A_to_B": s_b - s_ab,
    }


def bridge_hamiltonians() -> dict[str, torch.Tensor]:
    sx, sy, sz = qit.SX, qit.SY, qit.SZ
    base = 0.52 * (kron2(sx, sx) + kron2(sy, sy)) + 0.26 * kron2(sz, sz)
    suffix = 0.31 * (kron2(sz, sx) - kron2(sx, sz))
    transition = 0.19 * (kron2(sx, sy) + kron2(sy, sx))
    enhanced = base + suffix + transition
    return {
        "base": base,
        "history_enhanced": enhanced,
        "suffix_erased": base + transition,
        "history_erased": base,
    }


def random_matched_hamiltonian(seed: int, target: torch.Tensor) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed + 1009)
    coeffs = torch.randn(9, generator=generator, dtype=torch.float64)
    ops = [
        kron2(qit.SX, qit.SX),
        kron2(qit.SX, qit.SY),
        kron2(qit.SX, qit.SZ),
        kron2(qit.SY, qit.SX),
        kron2(qit.SY, qit.SY),
        kron2(qit.SY, qit.SZ),
        kron2(qit.SZ, qit.SX),
        kron2(qit.SZ, qit.SY),
        kron2(qit.SZ, qit.SZ),
    ]
    raw = sum(float(coeffs[idx].item()) * op for idx, op in enumerate(ops))
    return raw * (torch.linalg.matrix_norm(target) / torch.linalg.matrix_norm(raw))


def phase_randomized_hamiltonian(seed: int, target: torch.Tensor) -> torch.Tensor:
    signs = []
    state = (seed * 1103515245 + 12345) & 0x7FFFFFFF
    for _ in range(3):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        signs.append(1.0 if state % 2 == 0 else -1.0)
    sx, sy, sz = qit.SX, qit.SY, qit.SZ
    raw = (
        signs[0] * 0.52 * kron2(sx, sx)
        + signs[1] * 0.52 * kron2(sy, sy)
        + 0.26 * kron2(sz, sz)
        + signs[2] * 0.31 * (kron2(sz, sx) - kron2(sx, sz))
        + 0.19 * (kron2(sx, sy) + kron2(sy, sx))
    )
    return raw * (torch.linalg.matrix_norm(target) / torch.linalg.matrix_norm(raw))


def schedule_words(length: int) -> list[str]:
    return ["".join(tokens) for tokens in itertools.product(TOKENS, repeat=length)]


def all_words() -> list[str]:
    return [word for length in WORD_LENGTHS for word in schedule_words(length)]


def mirror_word(word: str) -> str:
    table = str.maketrans({"L": "R", "R": "L"})
    return word.translate(table)[::-1]


def rotate_word(word: str) -> str:
    return word[1:] + word[0] if len(word) > 1 else word


def block_permute_word(word: str) -> str:
    split = len(word) // 2
    return word[split:] + word[:split]


def transform_word(word: str, transform: str) -> str:
    if transform == "identity":
        return word
    if transform == "schedule_shuffled":
        return rotate_word(word)
    if transform == "time_reversed":
        return word[::-1]
    if transform == "block_permuted":
        return block_permute_word(word)
    raise ValueError(f"unknown transform {transform}")


def schedule_features(word: str) -> dict[str, Any]:
    transitions = sum(1 for left, right in zip(word, word[1:]) if left != right)
    balance = (word.count("L") - word.count("R")) / len(word)
    p_l = word.count("L") / len(word)
    if p_l in {0.0, 1.0}:
        binary_entropy = 0.0
    else:
        binary_entropy = -(p_l * math.log(p_l) + (1.0 - p_l) * math.log(1.0 - p_l))
    suffix = word[-2:] if len(word) >= 2 else word
    suffix_sign = {"LL": 1.0, "RR": -1.0, "LR": 0.35, "RL": -0.35}.get(suffix, 0.0)
    return {
        "length": len(word),
        "transitions": transitions,
        "transition_density": transitions / max(1, len(word) - 1),
        "balance": balance,
        "binary_entropy": binary_entropy,
        "suffix": suffix,
        "suffix_sign": suffix_sign,
        "last_token": word[-1],
    }


def schedule_transform_graph(words: list[str]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {word: graph.add_node(word) for word in words}
    for word in words:
        for label in ("schedule_shuffled", "time_reversed", "block_permuted"):
            next_word = transform_word(word, label)
            if next_word in nodes:
                graph.add_edge(nodes[word], nodes[next_word], label)
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "weakly_connected_components": len(rx.weakly_connected_components(graph)),
        "is_dag": rx.is_directed_acyclic_graph(graph),
    }


def history_theta_terms(features_a: dict[str, Any], features_b: dict[str, Any], *, mode: str) -> float:
    suffix_term = 0.075 * (features_a["suffix_sign"] - features_b["suffix_sign"])
    transition_term = 0.055 * (features_a["transition_density"] + features_b["transition_density"])
    balance_term = 0.045 * abs(features_a["balance"] - features_b["balance"])
    entropy_term = 0.035 * (features_a["binary_entropy"] + features_b["binary_entropy"])
    if mode == "history_erased":
        return 0.0
    if mode == "suffix_erased":
        suffix_term = 0.0
    if mode == "schedule_shuffled":
        transition_term = -transition_term
        balance_term = 0.5 * balance_term
    if mode == "time_reversed":
        suffix_term = -suffix_term
    if mode == "block_permuted":
        balance_term = 0.25 * balance_term
        entropy_term = 0.75 * entropy_term
    return max(0.0, suffix_term + transition_term + balance_term + entropy_term)


def theta_for(features_a: dict[str, Any], features_b: dict[str, Any], *, mode: str, theta_base: float) -> float:
    if mode == "no_coupling":
        return 0.0
    if mode == "floor_only":
        return theta_base
    return max(0.0, theta_base + history_theta_terms(features_a, features_b, mode=mode))


def apply_bridge(rho_a: torch.Tensor, rho_b: torch.Tensor, H_bridge: torch.Tensor, theta: float) -> torch.Tensor:
    rho_ab = qit.normalize_density(kron2(rho_a, rho_b))
    if theta == 0.0:
        return rho_ab
    U = torch.linalg.matrix_exp(-1j * float(theta) * H_bridge)
    return qit.normalize_density(U @ rho_ab @ U.conj().T)


def fixed_density_cache(tau: float, words: list[str]) -> dict[str, torch.Tensor]:
    engines = {
        "L": qit.engine_channel("L", "iter176_xz", tau=tau),
        "R": qit.engine_channel("R", "iter176_xz", tau=tau),
    }
    out: dict[str, torch.Tensor] = {}
    for word in words:
        out[word] = qit.fixed_density(qit.schedule_channel(word, engines), cycles=260)
    return out


def eval_pair(
    word_a: str,
    word_b: str,
    cache: dict[str, torch.Tensor],
    H_bridge: torch.Tensor,
    *,
    mode: str,
    theta_base: float,
) -> dict[str, Any]:
    features_a = schedule_features(word_a)
    features_b = schedule_features(word_b)
    theta = theta_for(features_a, features_b, mode=mode, theta_base=theta_base)
    rho_ab = apply_bridge(cache[word_a], cache[word_b], H_bridge, theta)
    phi0 = phi0_readout_pair(rho_ab)
    return {
        "word_A": word_a,
        "word_B": word_b,
        "theta": theta,
        "phi0": phi0,
        "rho_AB_min_eig": float(torch.min(torch.linalg.eigvalsh(rho_ab).real).item()),
    }


def evaluate_control_family(
    family: str,
    tau: float,
    words: list[str],
    cache: dict[str, torch.Tensor],
    Hs: dict[str, torch.Tensor],
    *,
    seed: int,
    theta_base: float,
) -> dict[str, Any]:
    transform = "identity"
    type_swap = False
    mode = "canonical"
    H_bridge = Hs["history_enhanced"]
    if family == "no_coupling":
        mode = "no_coupling"
    elif family == "floor_only":
        mode = "floor_only"
    elif family == "canonical":
        mode = "canonical"
    elif family == "history_erased":
        mode = "history_erased"
        H_bridge = Hs["history_erased"]
    elif family == "suffix_erased":
        mode = "suffix_erased"
        H_bridge = Hs["suffix_erased"]
    elif family == "type_swap":
        type_swap = True
    elif family == "schedule_shuffled":
        transform = "schedule_shuffled"
        mode = "schedule_shuffled"
    elif family == "time_reversed":
        transform = "time_reversed"
        mode = "time_reversed"
    elif family == "block_permuted":
        transform = "block_permuted"
        mode = "block_permuted"
    elif family == "phase_randomized":
        H_bridge = phase_randomized_hamiltonian(seed, Hs["history_enhanced"])
    elif family == "random_matched_norm":
        H_bridge = random_matched_hamiltonian(seed, Hs["history_enhanced"])
    else:
        raise ValueError(f"unknown control family {family}")

    rows = []
    for word in words:
        partner = transform_word(mirror_word(word), transform)
        word_a, word_b = (partner, word) if type_swap else (word, partner)
        rows.append(eval_pair(word_a, word_b, cache, H_bridge, mode=mode, theta_base=theta_base))
    values = [row["phi0"]["I_A_colon_B"] for row in rows]
    return {
        "family": family,
        "tau": tau,
        "seed": seed,
        "theta_base": theta_base,
        "row_count": len(rows),
        "mean_I_A_colon_B": sum(values) / len(values),
        "mean_theta": sum(row["theta"] for row in rows) / len(rows),
        "min_rho_AB_eig": min(row["rho_AB_min_eig"] for row in rows),
        "sample_rows": rows[:4],
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((value - m) ** 2 for value in values) / (len(values) - 1))


def pooled_std(left: list[float], right: list[float]) -> float:
    return math.sqrt(std(left) ** 2 + std(right) ** 2)


def aggregate(seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[float]] = {}
    theta_grouped: dict[str, list[float]] = {}
    min_eigs: dict[str, float] = {}
    for row in seed_rows:
        grouped.setdefault(row["family"], []).append(row["mean_I_A_colon_B"])
        theta_grouped.setdefault(row["family"], []).append(row["mean_theta"])
        min_eigs[row["family"]] = min(row["min_rho_AB_eig"], min_eigs.get(row["family"], float("inf")))
    canonical_values = grouped["canonical"]
    control_summaries = {}
    for family, values in grouped.items():
        if family == "canonical":
            continue
        delta = mean(canonical_values) - mean(values)
        sigma = pooled_std(canonical_values, values)
        control_summaries[family] = {
            "mean_I_A_colon_B": mean(values),
            "std_I_A_colon_B": std(values),
            "canonical_minus_control": delta,
            "pooled_std": sigma,
            "two_sigma_separated": delta > SIGMA_MULTIPLIER * sigma + CONTROL_MARGIN,
            "control_beats_canonical_two_sigma": -delta > SIGMA_MULTIPLIER * sigma + CONTROL_MARGIN,
            "mean_theta": mean(theta_grouped[family]),
            "min_rho_AB_eig": min_eigs[family],
        }
    max_control_name, max_control = max(
        control_summaries.items(), key=lambda item: item[1]["mean_I_A_colon_B"]
    )
    return {
        "canonical": {
            "mean_I_A_colon_B": mean(canonical_values),
            "std_I_A_colon_B": std(canonical_values),
            "mean_theta": mean(theta_grouped["canonical"]),
            "min_rho_AB_eig": min_eigs["canonical"],
        },
        "controls": control_summaries,
        "max_control_name": max_control_name,
        "max_control_mean_I_A_colon_B": max_control["mean_I_A_colon_B"],
        "canonical_minus_max_control": mean(canonical_values) - max_control["mean_I_A_colon_B"],
        "canonical_nonzero": mean(canonical_values) > PHI0_TOL,
        "canonical_separates_all_controls": all(item["two_sigma_separated"] for item in control_summaries.values()),
        "any_control_beats_canonical_two_sigma": any(
            item["control_beats_canonical_two_sigma"] for item in control_summaries.values()
        ),
    }


def build_surface() -> dict[str, Any]:
    words = all_words()
    Hs = bridge_hamiltonians()
    zero_base_rows = []
    with_floor_rows = []
    for tau in TAU_VALUES:
        cache = fixed_density_cache(tau, words)
        for seed in SEEDS:
            for family in (
                "canonical",
                "no_coupling",
                "floor_only",
                "history_erased",
                "suffix_erased",
                "type_swap",
                "schedule_shuffled",
                "time_reversed",
                "block_permuted",
                "phase_randomized",
                "random_matched_norm",
            ):
                zero_base_rows.append(
                    evaluate_control_family(
                        family,
                        tau,
                        words,
                        cache,
                        Hs,
                        seed=seed,
                        theta_base=0.0,
                    )
                )
            for family in ("canonical", "no_coupling", "floor_only"):
                with_floor_rows.append(
                    evaluate_control_family(
                        family,
                        tau,
                        words,
                        cache,
                        Hs,
                        seed=seed,
                        theta_base=THETA_BASE,
                    )
                )
    return {
        "word_count": len(words),
        "seed_count": len(SEEDS),
        "tau_values": list(TAU_VALUES),
        "transform_graph_length4": schedule_transform_graph(schedule_words(4)),
        "zero_base": aggregate(zero_base_rows),
        "with_floor": aggregate(with_floor_rows),
        "seed_rows_sample": zero_base_rows[:8],
    }


def classify(surface: dict[str, Any]) -> dict[str, Any]:
    zero = surface["zero_base"]
    floor = surface["with_floor"]
    floor_only_mean = floor["controls"]["floor_only"]["mean_I_A_colon_B"]
    floor_gap = floor["canonical"]["mean_I_A_colon_B"] - floor["controls"]["no_coupling"]["mean_I_A_colon_B"]
    zero_gap = zero["canonical"]["mean_I_A_colon_B"] - zero["controls"]["no_coupling"]["mean_I_A_colon_B"]
    floor_carries_signal = floor_only_mean > PHI0_TOL and zero["canonical"]["mean_I_A_colon_B"] <= PHI0_TOL
    if floor_carries_signal:
        status = "killed_theta_floor_confounded"
    elif zero["canonical_separates_all_controls"]:
        status = "survived_l7_history_control_separated"
    elif zero["canonical_nonzero"]:
        status = "open_nonzero_not_control_separated"
    else:
        status = "killed_zero_base_near_zero"
    return {
        "l7_theta_adversarial_status": status,
        "zero_base_canonical_mean_I_A_colon_B": zero["canonical"]["mean_I_A_colon_B"],
        "with_floor_canonical_mean_I_A_colon_B": floor["canonical"]["mean_I_A_colon_B"],
        "with_floor_floor_only_mean_I_A_colon_B": floor_only_mean,
        "zero_base_canonical_minus_no_coupling": zero_gap,
        "with_floor_canonical_minus_no_coupling": floor_gap,
        "zero_base_canonical_minus_max_control": zero["canonical_minus_max_control"],
        "zero_base_max_control_name": zero["max_control_name"],
        "zero_base_max_control_mean_I_A_colon_B": zero["max_control_mean_I_A_colon_B"],
        "floor_carries_signal": floor_carries_signal,
        "canonical_nonzero_without_floor": zero["canonical_nonzero"],
        "canonical_control_separated_without_floor": zero["canonical_separates_all_controls"],
        "any_control_beats_canonical_two_sigma": zero["any_control_beats_canonical_two_sigma"],
        "final_manifold_admission_allowed": False,
    }


def z3_guard(classification_summary: dict[str, Any]) -> dict[str, Any]:
    nonzero = z3.Bool("nonzero")
    separated = z3.Bool("separated")
    floor_confounded = z3.Bool("floor_confounded")
    l7_survived = z3.Bool("l7_survived")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(nonzero == bool(classification_summary["canonical_nonzero_without_floor"]))
    solver.add(separated == bool(classification_summary["canonical_control_separated_without_floor"]))
    solver.add(floor_confounded == bool(classification_summary["floor_carries_signal"]))
    solver.add(l7_survived == z3.And(nonzero, separated, z3.Not(floor_confounded)))
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, l7_survived))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "sat": status == z3.sat,
        "nonzero_without_floor": bool(z3.is_true(model.eval(nonzero, model_completion=True))) if model else False,
        "control_separated_without_floor": bool(z3.is_true(model.eval(separated, model_completion=True))) if model else False,
        "floor_confounded": bool(z3.is_true(model.eval(floor_confounded, model_completion=True))) if model else False,
        "l7_survived_gate": bool(z3.is_true(model.eval(l7_survived, model_completion=True))) if model else False,
        "final_manifold_admission_allowed": bool(z3.is_true(model.eval(final_admission, model_completion=True))) if model else False,
        "rule": "L7 may proceed to L8 only if history terms remain nonzero without theta_base and separate from structured/norm controls; final admission remains false.",
    }


def main() -> int:
    started = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    surface = build_surface()
    classification_summary = classify(surface)
    guard = z3_guard(classification_summary)
    status = classification_summary["l7_theta_adversarial_status"]
    positive = {
        "upstream_l7_loaded": {
            "pass": upstream["l7_bridge_result"].get("all_pass") is True
            and upstream["l7_bridge_result"].get("summary", {}).get("l7_xi_history_status")
            == "open_nonzero_not_control_separated",
            "upstream_status": upstream["l7_bridge_result"].get("summary", {}).get("l7_xi_history_status"),
        },
        "seed_ensemble_complete": {
            "pass": surface["seed_count"] >= 32 and surface["word_count"] == sum(2**length for length in WORD_LENGTHS),
            "seed_count": surface["seed_count"],
            "word_count": surface["word_count"],
        },
        "theta_base_ablation_present": {
            "pass": "zero_base" in surface and "with_floor" in surface,
            "theta_base_values": [0.0, THETA_BASE],
        },
        "structured_controls_present": {
            "pass": {
                "schedule_shuffled",
                "time_reversed",
                "phase_randomized",
                "block_permuted",
                "random_matched_norm",
            }
            <= set(surface["zero_base"]["controls"]),
            "control_families": sorted(surface["zero_base"]["controls"]),
        },
        "rho_ab_valid": {
            "pass": min(
                [surface["zero_base"]["canonical"]["min_rho_AB_eig"]]
                + [item["min_rho_AB_eig"] for item in surface["zero_base"]["controls"].values()]
                + [surface["with_floor"]["canonical"]["min_rho_AB_eig"]]
                + [item["min_rho_AB_eig"] for item in surface["with_floor"]["controls"].values()]
            )
            > -1.0e-8,
            "min_eig": min(
                [surface["zero_base"]["canonical"]["min_rho_AB_eig"]]
                + [item["min_rho_AB_eig"] for item in surface["zero_base"]["controls"].values()]
                + [surface["with_floor"]["canonical"]["min_rho_AB_eig"]]
                + [item["min_rho_AB_eig"] for item in surface["with_floor"]["controls"].values()]
            ),
        },
        "status_classified": {
            "pass": status
            in {
                "killed_theta_floor_confounded",
                "killed_zero_base_near_zero",
                "open_nonzero_not_control_separated",
                "survived_l7_history_control_separated",
            },
            "status": status,
            "z3": guard,
        },
    }
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "final_manifold_admission_allowed": False,
        "l8_shell_weighted_allowed_next": guard["l7_survived_gate"],
        "not_full_tensor_network_convergence": True,
        "not_peps_or_peps3d": True,
        "not_scale_level_real_basin": True,
        "why_not_final": [
            "This scout tests an L7 bridge confound over exact single-qubit schedule channels, not full tensor-network convergence.",
            "It does not run PEPS/PEPS3D dynamics or large-scale MPS Lindblad closure.",
            "It does not establish real attractor-basin admission.",
            "Final manifold admission remains blocked regardless of L7 status.",
        ],
    }
    graveyard = {
        "straight_to_l8_without_l7_ablation": {
            "pass": True,
            "detail": "Rejected by D119 provider audit; L8 is gated behind this L7 confound check.",
        },
        "nonzero_vs_no_coupling_as_rescue": {
            "pass": status != "survived_l7_history_control_separated",
            "detail": "A nonzero no-coupling gap alone is insufficient; matched controls and floor ablation decide status.",
        },
        "schedule_pseudobasin_promotion": {
            "pass": True,
            "detail": "Schedule words are bridge inputs, not admitted real attractor basins.",
        },
        "final_axis0_admission": {
            "pass": guard["final_manifold_admission_allowed"] is False,
            "detail": "Z3 guard fixes final admission false.",
        },
    }
    nearby_variants = {
        "total": len(graveyard),
        "passed": sum(1 for item in graveyard.values() if item["pass"]),
        "items": sorted(graveyard),
    }
    all_pass = all(item["pass"] for item in positive.values()) and guard["sat"]
    summary = {
        "all_pass": all_pass,
        **classification_summary,
        "l8_shell_weighted_allowed_next": guard["l7_survived_gate"],
        "interpretation": (
            "The L7 bridge confound gate is now executable. The status field says "
            "whether history terms survive without theta_base and against structured "
            "controls; final manifold admission remains blocked."
        ),
        "next_required_work": (
            "If L7 survives this gate, proceed to L8 shell-weighted Phi0. If it is killed "
            "or remains nonseparating, do not build L8 as bridge evidence; pivot to tensor "
            "runtime blockers or redesign Xi."
        ),
    }
    receipt = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "upstream": {
            "l7_status": upstream["l7_bridge_result"].get("summary", {}).get("l7_xi_history_status"),
            "l7_canonical_minus_max_control": upstream["l7_bridge_result"].get("summary", {}).get(
                "canonical_minus_max_control"
            ),
            "axis0_status": upstream["axis0_entropy_ratchet_result"].get("axis0_entropy_ratchet_status"),
        },
        "parameters": {
            "tokens": list(TOKENS),
            "word_lengths": list(WORD_LENGTHS),
            "tau_values": list(TAU_VALUES),
            "seed_count": len(SEEDS),
            "theta_base_ablation_values": [0.0, THETA_BASE],
            "control_margin": CONTROL_MARGIN,
            "sigma_multiplier": SIGMA_MULTIPLIER,
            "phi0_tol": PHI0_TOL,
        },
        "surface": surface,
        "classification_summary": classification_summary,
        "z3_guard": guard,
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": (
            "This is a v5 source-native formal scout using the shared exact torch "
            "QIT runtime and current D119 bridge order. It is not a legacy v4 probe, "
            "not a wiki batch, not PEPS/PEPS3D dynamics, and not final Axis0 admission."
        ),
        "next_work_required": [
            "If L7 survives, build L8 shell-weighted Phi0 with shell/weight-shuffled controls.",
            "If L7 remains nonseparating or killed, redesign Xi or return to tensor/full-basin blockers.",
            "Keep final manifold admission blocked until robust bridge, full tensor, and basin gates close.",
        ],
        "blockers": [],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
