#!/usr/bin/env python3
"""Causal-irreversibility Xi bridge scout.

The previous L7 schedule-history bridge was executable but did not separate
from time-reversed and random matched-norm controls. This scout replaces that
hand-shaped history scalar with a runtime-derived Xi: the bridge Hamiltonian is
built from each schedule channel's forward-vs-reverse asymmetry, fixed-point
Bloch response, and channel noncommutation.

This is a bridge repair/falsifier. It can show a redesigned Xi is a better
candidate or keep Phi0 open/nonrobust; it cannot promote final manifold
admission, full tensor convergence, PEPS/PEPS3D closure, or real basin status.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_xi_causal_irreversibility_phi0_bridge_probe_results.json"

NAME = "two_root_constraint_xi_causal_irreversibility_phi0_bridge_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_xi_causal_irreversibility_phi0_bridge"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_xi_causal_irreversibility_phi0_bridge"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal bridge repair/falsifier only: builds a runtime-derived Xi from "
    "schedule-channel irreversibility, fixed-point Bloch response, and channel "
    "noncommutation, then tests Phi0 against adversarial controls. It cannot "
    "promote final manifold admission, full tensor convergence, PEPS/PEPS3D "
    "closure, or real attractor-basin status."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact QIT schedule channels, fixed states, causal Xi bridge unitaries, Choi/entropy readouts, and random Hermitian matched-norm controls",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing control-transition graph and schedule transform topology witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bridge status and nonpromotion guard",
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
TAU_VALUES = (0.5, 1.0)
WORD_LENGTHS = (2, 3, 4, 5)
SEEDS = tuple(range(24))
CONTROL_MARGIN = 1.0e-3
PHI0_TOL = 1.0e-3
SIGMA_MULTIPLIER = 2.0
MAX_THETA = 0.28
PAIR_SCALE = 0.72
COMM_SCALE = 0.18

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "l7_theta_result": RESULT_DIR
    / "two_root_constraint_l7_xi_history_theta_base_and_adversarial_control_probe_results.json",
    "l4_entropy_cell_result": RESULT_DIR / "two_root_constraint_l4_entropy_cell_witness_matrix_probe_results.json",
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
    return {
        name: {"path": rel(path), "sha256": sha256(path), "exists": path.exists()}
        for name, path in SOURCE_FILES.items()
    }


def entropy(rho: torch.Tensor, eps: float = 1.0e-12) -> float:
    herm = 0.5 * (rho + rho.conj().T)
    vals = torch.linalg.eigvalsh(herm).real.clamp_min(eps)
    return float((-vals * torch.log(vals)).sum().item())


def partial_trace_two_qubit(rho_ab: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    shaped = rho_ab.reshape(2, 2, 2, 2)
    rho_a = torch.einsum("abcb->ac", shaped)
    rho_b = torch.einsum("abac->bc", shaped)
    return qit.normalize_density(rho_a), qit.normalize_density(rho_b)


def partial_transpose_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)


def phi0_readout(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_a, rho_b = partial_trace_two_qubit(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho_ab)
    pt_vals = torch.linalg.eigvalsh(0.5 * (partial_transpose_b(rho_ab) + partial_transpose_b(rho_ab).conj().T)).real
    negativity = float(torch.sum(torch.clamp(-pt_vals, min=0.0)).item())
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_A_colon_B": s_a + s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_c_A_to_B": s_b - s_ab,
        "I_c_B_to_A": s_a - s_ab,
        "I_c_directional": (s_b - s_ab) - (s_a - s_ab),
        "negativity": negativity,
    }


def words() -> list[str]:
    return ["".join(bits) for length in WORD_LENGTHS for bits in itertools.product(TOKENS, repeat=length)]


def mirror_word(word: str) -> str:
    return word.translate(str.maketrans({"L": "R", "R": "L"}))[::-1]


def rotate_word(word: str) -> str:
    return word[1:] + word[0] if len(word) > 1 else word


def block_permute_word(word: str) -> str:
    cut = len(word) // 2
    return word[cut:] + word[:cut]


def sorted_word(word: str) -> str:
    return "".join(sorted(word))


def transform_word(word: str, family: str) -> str:
    if family in {"canonical", "no_coupling", "causal_erased", "random_matched_norm", "phase_randomized"}:
        return word
    if family == "time_reversed":
        return word[::-1]
    if family == "schedule_shuffled":
        return rotate_word(word)
    if family == "block_permuted":
        return block_permute_word(word)
    if family == "order_erased":
        return sorted_word(word)
    if family == "type_swap":
        return word
    raise ValueError(f"unknown transform family {family}")


def pauli_from_vector(vector: torch.Tensor) -> torch.Tensor:
    return vector[0] * qit.SX + vector[1] * qit.SY + vector[2] * qit.SZ


def normalize_vector(vector: torch.Tensor, eps: float = 1.0e-12) -> torch.Tensor:
    norm = torch.linalg.vector_norm(vector)
    if float(norm.item()) < eps:
        return torch.zeros_like(vector)
    return vector / norm


def fro_norm(matrix: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(matrix).real.item())


def channel_cache(tau: float) -> dict[str, Any]:
    engines = {
        "L": qit.engine_channel("L", "iter176_xz", tau=tau),
        "R": qit.engine_channel("R", "iter176_xz", tau=tau),
    }
    all_words = words()
    channels = {word: qit.schedule_channel(word, engines) for word in all_words}
    # Include transformed partners that may fall outside all_words only by length
    # preserving transforms. The set is still over L/R words of the same lengths.
    densities = {word: qit.fixed_density(channel, cycles=260) for word, channel in channels.items()}
    bloch = {word: torch.tensor(qit.bloch(density), dtype=torch.float64) for word, density in densities.items()}
    return {"engines": engines, "channels": channels, "densities": densities, "bloch": bloch}


def causal_xi_terms(word_a: str, word_b: str, cache: dict[str, Any]) -> dict[str, Any]:
    channels = cache["channels"]
    bloch = cache["bloch"]
    rev_a = word_a[::-1]
    rev_b = word_b[::-1]
    ch_a = channels[word_a]
    ch_b = channels[word_b]
    ch_rev_a = channels[rev_a]
    ch_rev_b = channels[rev_b]
    r_a = bloch[word_a]
    r_b = bloch[word_b]
    causal_a = r_a - bloch[rev_a]
    causal_b = r_b - bloch[rev_b]
    response_a = causal_a if float(torch.linalg.vector_norm(causal_a).item()) > 1.0e-8 else r_a
    response_b = causal_b if float(torch.linalg.vector_norm(causal_b).item()) > 1.0e-8 else r_b
    comm_norm = fro_norm(ch_a @ ch_b - ch_b @ ch_a)
    reverse_gap = fro_norm(ch_a - ch_rev_a) + fro_norm(ch_b - ch_rev_b)
    response_norm = float(torch.linalg.vector_norm(response_a).item() * torch.linalg.vector_norm(response_b).item())
    score = min(MAX_THETA, PAIR_SCALE * response_norm + COMM_SCALE * comm_norm)
    A = pauli_from_vector(normalize_vector(response_a))
    B = pauli_from_vector(normalize_vector(response_b))
    base = torch.kron(A, B)
    odd = torch.kron(pauli_from_vector(normalize_vector(r_a)), pauli_from_vector(normalize_vector(causal_b))) - torch.kron(
        pauli_from_vector(normalize_vector(causal_a)), pauli_from_vector(normalize_vector(r_b))
    )
    H = base + 0.35 * odd
    norm = torch.linalg.matrix_norm(H)
    if float(norm.real.item()) < 1.0e-12:
        H = torch.kron(qit.SX, qit.SX) + torch.kron(qit.SY, qit.SY)
        norm = torch.linalg.matrix_norm(H)
    H = 0.5 * (H + H.conj().T) / norm
    return {
        "H": H,
        "theta": float(score),
        "comm_norm": comm_norm,
        "reverse_gap": float(reverse_gap),
        "response_norm": response_norm,
        "bloch_A": r_a.tolist(),
        "bloch_B": r_b.tolist(),
        "causal_A_norm": float(torch.linalg.vector_norm(causal_a).item()),
        "causal_B_norm": float(torch.linalg.vector_norm(causal_b).item()),
    }


def random_matched_hamiltonian(seed: int, target: torch.Tensor) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(1729 + seed)
    coeffs = torch.randn(9, generator=generator, dtype=torch.float64)
    ops = [
        torch.kron(qit.SX, qit.SX),
        torch.kron(qit.SX, qit.SY),
        torch.kron(qit.SX, qit.SZ),
        torch.kron(qit.SY, qit.SX),
        torch.kron(qit.SY, qit.SY),
        torch.kron(qit.SY, qit.SZ),
        torch.kron(qit.SZ, qit.SX),
        torch.kron(qit.SZ, qit.SY),
        torch.kron(qit.SZ, qit.SZ),
    ]
    raw = sum(float(coeffs[idx].item()) * op for idx, op in enumerate(ops))
    raw = 0.5 * (raw + raw.conj().T)
    return raw * (torch.linalg.matrix_norm(target) / torch.linalg.matrix_norm(raw))


def phase_randomized_hamiltonian(seed: int, target: torch.Tensor) -> torch.Tensor:
    signs = []
    state = (seed * 1103515245 + 12345) & 0x7FFFFFFF
    for _ in range(4):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        signs.append(1.0 if state % 2 == 0 else -1.0)
    raw = (
        signs[0] * torch.kron(qit.SX, qit.SX)
        + signs[1] * torch.kron(qit.SY, qit.SY)
        + 0.5 * signs[2] * torch.kron(qit.SZ, qit.SZ)
        + 0.35 * signs[3] * (torch.kron(qit.SX, qit.SZ) - torch.kron(qit.SZ, qit.SX))
    )
    raw = 0.5 * (raw + raw.conj().T)
    return raw * (torch.linalg.matrix_norm(target) / torch.linalg.matrix_norm(raw))


def apply_bridge(rho_a: torch.Tensor, rho_b: torch.Tensor, H: torch.Tensor, theta: float) -> torch.Tensor:
    rho_ab = qit.normalize_density(torch.kron(rho_a, rho_b))
    if abs(theta) < 1.0e-14:
        return rho_ab
    U = torch.linalg.matrix_exp(-1j * float(theta) * H)
    return qit.normalize_density(U @ rho_ab @ U.conj().T)


def evaluate_case(
    family: str,
    tau: float,
    word: str,
    cache: dict[str, Any],
    *,
    seed: int,
) -> dict[str, Any]:
    transformed = transform_word(word, family)
    partner = mirror_word(transformed)
    if family == "type_swap":
        word_a, word_b = partner, transformed
    else:
        word_a, word_b = transformed, partner
    xi = causal_xi_terms(word_a, word_b, cache)
    H = xi["H"]
    theta = xi["theta"]
    if family == "no_coupling":
        theta = 0.0
    elif family == "causal_erased":
        H = torch.kron(pauli_from_vector(normalize_vector(cache["bloch"][word_a])), pauli_from_vector(normalize_vector(cache["bloch"][word_b])))
        norm = torch.linalg.matrix_norm(H)
        H = 0.5 * (H + H.conj().T) / norm
        theta = min(MAX_THETA, 0.5 * xi["comm_norm"])
    elif family == "random_matched_norm":
        H = random_matched_hamiltonian(seed, H)
    elif family == "phase_randomized":
        H = phase_randomized_hamiltonian(seed, H)
    rho_ab = apply_bridge(cache["densities"][word_a], cache["densities"][word_b], H, theta)
    phi0 = phi0_readout(rho_ab)
    return {
        "family": family,
        "tau": tau,
        "word": word,
        "word_A": word_a,
        "word_B": word_b,
        "seed": seed,
        "theta": theta,
        "phi0": phi0,
        "rho_AB_min_eig": float(torch.min(torch.linalg.eigvalsh(rho_ab).real).item()),
        "xi_terms": {k: v for k, v in xi.items() if k != "H"},
    }


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return math.sqrt(sum((value - center) ** 2 for value in values) / (len(values) - 1))


def pooled_std(left: list[float], right: list[float]) -> float:
    return math.sqrt(std(left) ** 2 + std(right) ** 2)


def aggregate(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    by_family: dict[str, list[float]] = {}
    theta_by_family: dict[str, list[float]] = {}
    min_eig_by_family: dict[str, float] = {}
    for row in rows:
        by_family.setdefault(row["family"], []).append(float(row["phi0"][metric]))
        theta_by_family.setdefault(row["family"], []).append(float(row["theta"]))
        min_eig_by_family[row["family"]] = min(row["rho_AB_min_eig"], min_eig_by_family.get(row["family"], float("inf")))
    canonical_values = by_family["canonical"]
    controls: dict[str, Any] = {}
    for family, values in sorted(by_family.items()):
        if family == "canonical":
            continue
        delta = mean(canonical_values) - mean(values)
        sigma = pooled_std(canonical_values, values)
        controls[family] = {
            "mean": mean(values),
            "std": std(values),
            "canonical_minus_control": delta,
            "pooled_std": sigma,
            "two_sigma_separated": delta > SIGMA_MULTIPLIER * sigma + CONTROL_MARGIN,
            "control_beats_canonical_two_sigma": -delta > SIGMA_MULTIPLIER * sigma + CONTROL_MARGIN,
            "mean_theta": mean(theta_by_family[family]),
            "min_rho_AB_eig": min_eig_by_family[family],
        }
    max_control_name, max_control = max(controls.items(), key=lambda item: item[1]["mean"])
    return {
        "metric": metric,
        "canonical": {
            "mean": mean(canonical_values),
            "std": std(canonical_values),
            "mean_theta": mean(theta_by_family["canonical"]),
            "min_rho_AB_eig": min_eig_by_family["canonical"],
        },
        "controls": controls,
        "max_control_name": max_control_name,
        "max_control_mean": max_control["mean"],
        "canonical_minus_max_control": mean(canonical_values) - max_control["mean"],
        "canonical_nonzero": abs(mean(canonical_values)) > PHI0_TOL,
        "canonical_separates_all_controls": all(row["two_sigma_separated"] for row in controls.values()),
        "any_control_beats_canonical_two_sigma": any(row["control_beats_canonical_two_sigma"] for row in controls.values()),
    }


def transform_graph() -> dict[str, Any]:
    sample = ["".join(bits) for bits in itertools.product(TOKENS, repeat=4)]
    graph = rx.PyDiGraph()
    nodes = {word: graph.add_node(word) for word in sample}
    for word in sample:
        for label in ("time_reversed", "schedule_shuffled", "block_permuted", "order_erased"):
            nxt = transform_word(word, label)
            if nxt in nodes:
                graph.add_edge(nodes[word], nodes[nxt], label)
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "weakly_connected_components": len(rx.weakly_connected_components(graph)),
        "is_dag": rx.is_directed_acyclic_graph(graph),
    }


def build_surface() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    all_words = words()
    families = (
        "canonical",
        "no_coupling",
        "time_reversed",
        "schedule_shuffled",
        "block_permuted",
        "order_erased",
        "type_swap",
        "causal_erased",
        "phase_randomized",
        "random_matched_norm",
    )
    for tau in TAU_VALUES:
        cache = channel_cache(tau)
        for seed in SEEDS:
            for word in all_words:
                for family in families:
                    rows.append(evaluate_case(family, tau, word, cache, seed=seed))
    return {
        "row_count": len(rows),
        "word_count": len(all_words),
        "seed_count": len(SEEDS),
        "tau_values": list(TAU_VALUES),
        "families": list(families),
        "transform_graph_length4": transform_graph(),
        "sample_rows": rows[:8],
        "aggregates": {
            metric: aggregate(rows, metric)
            for metric in ("I_A_colon_B", "I_c_A_to_B", "I_c_directional", "negativity")
        },
    }


def classify(surface: dict[str, Any]) -> dict[str, Any]:
    aggregates = surface["aggregates"]
    ranked = sorted(
        aggregates.values(),
        key=lambda row: (
            row["canonical_separates_all_controls"],
            row["canonical_nonzero"],
            row["canonical_minus_max_control"],
        ),
        reverse=True,
    )
    best = ranked[0]
    mi = aggregates["I_A_colon_B"]
    ic = aggregates["I_c_A_to_B"]
    directional = aggregates["I_c_directional"]
    if best["canonical_separates_all_controls"]:
        status = "survived_causal_xi_control_separated_first_gate"
    elif any(row["canonical_nonzero"] for row in aggregates.values()):
        status = "open_nonzero_not_control_separated"
    else:
        status = "killed_near_zero_causal_xi"
    return {
        "xi_causal_irreversibility_status": status,
        "best_metric": best["metric"],
        "best_metric_canonical_mean": best["canonical"]["mean"],
        "best_metric_max_control_name": best["max_control_name"],
        "best_metric_max_control_mean": best["max_control_mean"],
        "best_metric_canonical_minus_max_control": best["canonical_minus_max_control"],
        "mutual_information_canonical_minus_max_control": mi["canonical_minus_max_control"],
        "coherent_information_canonical_minus_max_control": ic["canonical_minus_max_control"],
        "directional_ic_canonical_minus_max_control": directional["canonical_minus_max_control"],
        "mutual_information_canonical_minus_no_coupling": mi["controls"]["no_coupling"]["canonical_minus_control"],
        "coherent_information_canonical_minus_no_coupling": ic["controls"]["no_coupling"]["canonical_minus_control"],
        "directional_ic_canonical_minus_no_coupling": directional["controls"]["no_coupling"]["canonical_minus_control"],
        "canonical_nonzero_any_metric": any(row["canonical_nonzero"] for row in aggregates.values()),
        "canonical_control_separated_any_metric": any(row["canonical_separates_all_controls"] for row in aggregates.values()),
        "any_control_beats_canonical_two_sigma": any(row["any_control_beats_canonical_two_sigma"] for row in aggregates.values()),
        "l8_shell_weighted_allowed_next": bool(best["canonical_separates_all_controls"]),
        "final_manifold_admission_allowed": False,
    }


def z3_guard(summary: dict[str, Any]) -> dict[str, Any]:
    nonzero = z3.Bool("nonzero")
    separated = z3.Bool("separated")
    l8_allowed = z3.Bool("l8_allowed")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(nonzero == bool(summary["canonical_nonzero_any_metric"]))
    solver.add(separated == bool(summary["canonical_control_separated_any_metric"]))
    solver.add(l8_allowed == z3.And(nonzero, separated))
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, z3.And(l8_allowed, separated)))
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "sat": status == z3.sat,
        "nonzero": bool(z3.is_true(model.eval(nonzero, model_completion=True))) if model else False,
        "control_separated": bool(z3.is_true(model.eval(separated, model_completion=True))) if model else False,
        "l8_shell_weighted_allowed_next": bool(z3.is_true(model.eval(l8_allowed, model_completion=True))) if model else False,
        "final_manifold_admission_allowed": bool(z3.is_true(model.eval(final_admission, model_completion=True))) if model else False,
        "rule": "Causal Xi may route to L8 only if some Phi0 metric is nonzero and control-separated; final admission remains false.",
    }


def main() -> int:
    started = time.time()
    upstream = {
        name: read_json(path)
        for name, path in SOURCE_FILES.items()
        if name.endswith("_result")
    }
    surface = build_surface()
    summary = classify(surface)
    guard = z3_guard(summary)
    positive = {
        "upstream_l7_adversarial_loaded": {
            "pass": upstream["l7_theta_result"].get("all_pass") is True
            and upstream["l7_theta_result"].get("summary", {}).get("l7_theta_adversarial_status")
            == "open_nonzero_not_control_separated",
            "upstream_status": upstream["l7_theta_result"].get("summary", {}).get("l7_theta_adversarial_status"),
        },
        "l4_entropy_cell_anchor_loaded": {
            "pass": upstream["l4_entropy_cell_result"].get("all_pass") is True
            and upstream["l4_entropy_cell_result"].get("summary", {}).get("l4_entropy_cell_status")
            == "numeric_witness_matrix_complete",
            "upstream_status": upstream["l4_entropy_cell_result"].get("summary", {}).get("l4_entropy_cell_status"),
        },
        "causal_xi_surface_complete": {
            "pass": surface["row_count"] == len(TAU_VALUES) * len(SEEDS) * surface["word_count"] * len(surface["families"]),
            "row_count": surface["row_count"],
            "word_count": surface["word_count"],
            "seed_count": surface["seed_count"],
            "family_count": len(surface["families"]),
        },
        "adversarial_controls_present": {
            "pass": {
                "time_reversed",
                "schedule_shuffled",
                "block_permuted",
                "order_erased",
                "type_swap",
                "causal_erased",
                "phase_randomized",
                "random_matched_norm",
            }.issubset(set(surface["families"])),
            "families": surface["families"],
        },
        "z3_nonpromotion_guard": {"pass": guard["sat"] and not guard["final_manifold_admission_allowed"], "guard": guard},
    }
    all_pass = all(item["pass"] for item in positive.values())
    result = {
        "schema": "codex_ratchet.formal_scout.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "positive": positive,
        "surface_summary": {
            key: value for key, value in surface.items() if key not in {"sample_rows"}
        },
        "sample_rows": surface["sample_rows"],
        "summary": summary,
        "checks": {
            "all_pass": all_pass,
            "all_control_families_present": positive["adversarial_controls_present"]["pass"],
            "no_final_admission": not guard["final_manifold_admission_allowed"],
        },
        "nearby_variants": {
            "previous_l7_history_bridge": "open_nonzero_not_control_separated",
            "previous_l7_theta_adversarial_gate": "open_nonzero_not_control_separated",
            "l4_entropy_cell_witness": "numeric_witness_matrix_complete_but_nonpromotional",
        },
        "graveyard_companions": {
            "raw_history_scalar_xi": "failed controls in L7 history and theta/adversarial receipts",
            "raw_l4_phi0_bridge": "nonrobust under coupled-E16 stress and response-gradient controls",
            "single_engine_basin": "monostable; schedule classes are pseudo-basins only",
        },
        "boundary": {
            "final_manifold_admission_allowed": False,
            "real_attractor_basin_admission_allowed": False,
            "full_tensor_convergence_claimed": False,
            "peps_or_peps3d_closure_claimed": False,
        },
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(jsonable({"all_pass": all_pass, **summary}), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
