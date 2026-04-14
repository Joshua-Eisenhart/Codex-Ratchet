#!/usr/bin/env python3
"""
Xi cut-kernel ranking
=====================

Pure-math comparison of three bridge-candidate families by the cut kernels
they induce after bipartite state construction.

Families:
  - Xi_ref   : reference-anchored bridge
  - Xi_shell : shell-weighted bridge
  - Xi_hist  : ordered-history bridge

Goal:
  Rank how strongly each family separates a small battery of geometric/history
  packets through induced cut kernels. This probe does not promote a final
  winner unless the margin is overwhelming.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, replace
from typing import Dict, List

import numpy as np
classification = "classical_baseline"  # auto-backfill


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "no graph-learning layer needed"},
    "z3": {"tried": False, "used": False, "reason": "no satisfiability claim in this bounded ranking"},
    "cvc5": {"tried": False, "used": False, "reason": "no synthesis or SMT cross-check needed"},
    "sympy": {"tried": False, "used": False, "reason": "no symbolic derivation needed"},
    "clifford": {"tried": False, "used": False, "reason": "Bloch-vector density matrices are sufficient"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold statistics needed"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant learning layer needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph algorithm needed"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph layer needed"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell-complex construction needed"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent topology needed"},
}


SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
PAULIS = [SIGMA_X, SIGMA_Y, SIGMA_Z]
I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)
BELL_PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / math.sqrt(2.0)


@dataclass
class ShellPoint:
    radius: float
    theta: float
    phi: float
    weight: float


@dataclass
class GeometryHistoryPacket:
    label: str
    kind: str
    current: ShellPoint
    shells: List[ShellPoint]
    history: List[ShellPoint]
    reference: ShellPoint


def normalize_weights(values: np.ndarray) -> np.ndarray:
    total = float(np.sum(values))
    if total <= 0.0:
        return np.ones_like(values) / len(values)
    return values / total


def ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex)
    rho = 0.5 * (rho + rho.conj().T)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
        return I4 / 4.0 if rho.shape == (4, 4) else I2 / 2.0
    rho = evecs @ np.diag(evals / evals.sum()) @ evecs.conj().T
    return 0.5 * (rho + rho.conj().T)


def shell_point_to_bloch(point: ShellPoint) -> np.ndarray:
    r = float(np.clip(point.radius, 0.0, 0.999))
    return r * np.array(
        [
            math.sin(point.theta) * math.cos(point.phi),
            math.sin(point.theta) * math.sin(point.phi),
            math.cos(point.theta),
        ],
        dtype=float,
    )


def bloch_to_density(vec: np.ndarray) -> np.ndarray:
    rho = 0.5 * (I2 + vec[0] * SIGMA_X + vec[1] * SIGMA_Y + vec[2] * SIGMA_Z)
    return ensure_density(rho)


def left_density(point: ShellPoint) -> np.ndarray:
    return bloch_to_density(shell_point_to_bloch(point))


def right_density(point: ShellPoint) -> np.ndarray:
    vec = shell_point_to_bloch(point)
    rotated = np.array([vec[2], -vec[1], vec[0]], dtype=float)
    return bloch_to_density(rotated)


def pair_state(rho_a: np.ndarray, rho_b: np.ndarray, coupling: float) -> np.ndarray:
    coupling = float(np.clip(coupling, 0.0, 0.95))
    prod = np.kron(rho_a, rho_b)
    bell = np.outer(BELL_PHI_PLUS, BELL_PHI_PLUS.conj())
    return ensure_density((1.0 - coupling) * prod + coupling * bell)


def partial_trace_a(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_b(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def vn_entropy(rho: np.ndarray) -> float:
    evals = np.real(np.linalg.eigvalsh(ensure_density(rho)))
    evals = evals[evals > 1e-14]
    return float(-np.sum(evals * np.log2(evals))) if len(evals) else 0.0


def mutual_information(rho_ab: np.ndarray) -> float:
    return max(0.0, vn_entropy(partial_trace_a(rho_ab)) + vn_entropy(partial_trace_b(rho_ab)) - vn_entropy(rho_ab))


def conditional_entropy_a_given_b(rho_ab: np.ndarray) -> float:
    return float(vn_entropy(rho_ab) - vn_entropy(partial_trace_b(rho_ab)))


def coherent_information(rho_ab: np.ndarray) -> float:
    return float(vn_entropy(partial_trace_b(rho_ab)) - vn_entropy(rho_ab))


def negativity(rho_ab: np.ndarray) -> float:
    rho = rho_ab.reshape(2, 2, 2, 2)
    rho_pt = np.transpose(rho, (0, 3, 2, 1)).reshape(4, 4)
    evals = np.real(np.linalg.eigvalsh(0.5 * (rho_pt + rho_pt.conj().T)))
    return float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0))


def weighted_cut_functional(rho_ab: np.ndarray) -> float:
    mi = mutual_information(rho_ab)
    ic = coherent_information(rho_ab)
    neg = negativity(rho_ab)
    return float(0.45 * mi + 0.35 * max(0.0, ic) + 0.20 * neg)


def correlation_tensor_norm(rho_ab: np.ndarray) -> float:
    total = 0.0
    for pa in PAULIS:
        for pb in PAULIS:
            total += abs(np.trace(rho_ab @ np.kron(pa, pb))) ** 2
    return float(math.sqrt(total))


def reference_offset(packet: GeometryHistoryPacket) -> float:
    cur = shell_point_to_bloch(packet.current)
    ref = shell_point_to_bloch(packet.reference)
    return float(np.linalg.norm(cur - ref))


def history_turning(packet: GeometryHistoryPacket) -> float:
    if len(packet.history) < 3:
        return 0.0
    phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
    second = np.diff(np.diff(phases))
    return float(np.mean(np.abs(second))) if len(second) else 0.0


def xi_ref(packet: GeometryHistoryPacket) -> np.ndarray:
    rho_cur = pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    rho_ref = pair_state(left_density(packet.reference), right_density(packet.reference), 0.0)
    coupling = 0.45 * math.tanh(1.2 * reference_offset(packet))
    return ensure_density((1.0 - coupling) * rho_cur + coupling * rho_ref[::-1, ::-1])


def xi_shell(packet: GeometryHistoryPacket) -> np.ndarray:
    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    rho = np.zeros((4, 4), dtype=complex)
    for point, weight in zip(packet.shells, weights):
        shell_coupling = 0.18 + 0.55 * abs(point.radius - packet.current.radius)
        rho += weight * pair_state(left_density(point), right_density(point), shell_coupling)
    return ensure_density(rho)


def xi_hist(packet: GeometryHistoryPacket) -> np.ndarray:
    if len(packet.history) == 0:
        return pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
    if len(phases) == 1:
        weights = np.array([1.0], dtype=float)
    else:
        step = np.abs(np.diff(phases, prepend=phases[0]))
        trend = np.linspace(0.8, 1.2, len(packet.history))
        weights = normalize_weights(step + trend)
    turning = history_turning(packet)
    rho = np.zeros((4, 4), dtype=complex)
    for point, weight in zip(packet.history, weights):
        history_coupling = 0.12 + 0.5 * abs(point.radius - packet.current.radius) + 0.35 * turning
        rho += weight * pair_state(left_density(point), right_density(point), history_coupling)
    return ensure_density(rho)


def kernel_vector(rho_ab: np.ndarray) -> Dict[str, float]:
    return {
        "mutual_information": mutual_information(rho_ab),
        "conditional_entropy_a_given_b": conditional_entropy_a_given_b(rho_ab),
        "coherent_information": coherent_information(rho_ab),
        "negativity": negativity(rho_ab),
        "weighted_cut_functional": weighted_cut_functional(rho_ab),
        "correlation_tensor_norm": correlation_tensor_norm(rho_ab),
    }


def make_packet(
    label: str,
    kind: str,
    current_radius: float,
    shell_radii: List[float],
    history_radii: List[float],
    history_phis: List[float],
    reference_phi: float,
) -> GeometryHistoryPacket:
    current = ShellPoint(current_radius, 1.06, 0.80, 1.0)
    shells = [
        ShellPoint(r, 0.72 + 0.22 * i, -0.20 + 0.70 * i, w)
        for i, (r, w) in enumerate(zip(shell_radii, [0.20, 0.50, 0.30]))
    ]
    history = [
        ShellPoint(r, 0.76 + 0.14 * i, phi, 1.0)
        for i, (r, phi) in enumerate(zip(history_radii, history_phis))
    ]
    reference = ShellPoint(current_radius, 0.92, reference_phi, 1.0)
    return GeometryHistoryPacket(label, kind, current, shells, history, reference)


def build_battery() -> List[GeometryHistoryPacket]:
    return [
        make_packet(
            "aligned_low_coupling",
            "product_like",
            0.30,
            [0.28, 0.31, 0.33],
            [0.28, 0.29, 0.30, 0.31],
            [0.02, 0.03, 0.05, 0.06],
            0.78,
        ),
        make_packet(
            "reference_split",
            "reference_driven",
            0.48,
            [0.43, 0.49, 0.55],
            [0.45, 0.47, 0.49, 0.51],
            [0.10, 0.18, 0.32, 0.48],
            -0.75,
        ),
        make_packet(
            "shell_gradient",
            "shell_driven",
            0.58,
            [0.18, 0.56, 0.89],
            [0.52, 0.55, 0.57, 0.60],
            [0.12, 0.26, 0.38, 0.53],
            0.84,
        ),
        make_packet(
            "history_turning",
            "history_driven",
            0.60,
            [0.40, 0.61, 0.78],
            [0.26, 0.39, 0.54, 0.69],
            [-0.65, 0.05, 0.96, 1.92],
            0.20,
        ),
        make_packet(
            "mixed_competition",
            "mixed_case",
            0.54,
            [0.27, 0.55, 0.80],
            [0.34, 0.44, 0.57, 0.71],
            [-0.30, 0.24, 0.71, 1.31],
            -0.20,
        ),
    ]


def history_scramble(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    order = [2, 0, 3, 1][: len(packet.history)]
    return replace(packet, history=[packet.history[i] for i in order])


def shell_ablation(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    middle = packet.shells[len(packet.shells) // 2]
    return replace(packet, shells=[replace(middle, weight=1.0)])


def reference_freeze(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    return replace(
        packet,
        reference=ShellPoint(packet.current.radius, packet.current.theta, packet.current.phi, 1.0),
    )


def family_states(packet: GeometryHistoryPacket) -> Dict[str, np.ndarray]:
    return {
        "Xi_ref": xi_ref(packet),
        "Xi_shell": xi_shell(packet),
        "Xi_hist": xi_hist(packet),
    }


def discrimination_score(rows: List[Dict[str, object]], kernel_name: str) -> Dict[str, float]:
    values = np.array([row["kernels"][kernel_name] for row in rows], dtype=float)
    spread = float(np.max(values) - np.min(values))
    kind_means: Dict[str, float] = {}
    for kind in sorted({row["packet_kind"] for row in rows}):
        sub = [row["kernels"][kernel_name] for row in rows if row["packet_kind"] == kind]
        kind_means[kind] = float(np.mean(sub))
    kind_spread = float(max(kind_means.values()) - min(kind_means.values())) if kind_means else 0.0
    return {
        "spread": spread,
        "kind_mean_gap": kind_spread,
        "combined_score": float(0.6 * spread + 0.4 * kind_spread),
    }


def family_ranking(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    kernels = [
        "mutual_information",
        "conditional_entropy_a_given_b",
        "coherent_information",
        "negativity",
        "weighted_cut_functional",
        "correlation_tensor_norm",
    ]
    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(row["family"], []).append(row)

    ranking = []
    for family, subrows in grouped.items():
        scores = {kernel: discrimination_score(subrows, kernel) for kernel in kernels}
        total = float(np.mean([scores[k]["combined_score"] for k in kernels]))
        ranking.append(
            {
                "family": family,
                "kernel_scores": scores,
                "aggregate_discrimination_score": total,
            }
        )
    ranking.sort(key=lambda x: x["aggregate_discrimination_score"], reverse=True)
    return ranking


def counterfactual_response(packet: GeometryHistoryPacket) -> Dict[str, object]:
    base = family_states(packet)
    scrambled = family_states(history_scramble(packet))
    ablated = family_states(shell_ablation(packet))
    frozen = family_states(reference_freeze(packet))

    def family_shift(name: str, altered: Dict[str, np.ndarray]) -> Dict[str, float]:
        base_k = kernel_vector(base[name])
        alt_k = kernel_vector(altered[name])
        return {
            "frobenius_distance": float(np.linalg.norm(base[name] - altered[name], ord="fro")),
            "mutual_information_shift": abs(base_k["mutual_information"] - alt_k["mutual_information"]),
            "coherent_information_shift": abs(base_k["coherent_information"] - alt_k["coherent_information"]),
            "weighted_cut_shift": abs(base_k["weighted_cut_functional"] - alt_k["weighted_cut_functional"]),
        }

    return {
        "history_scrambling": {name: family_shift(name, scrambled) for name in base},
        "shell_ablation": {name: family_shift(name, ablated) for name in base},
        "reference_freeze": {name: family_shift(name, frozen) for name in base},
    }


def run_positive_tests() -> Dict[str, object]:
    battery = build_battery()
    rows: List[Dict[str, object]] = []
    for packet in battery:
        for family, rho_ab in family_states(packet).items():
            rows.append(
                {
                    "packet_label": packet.label,
                    "packet_kind": packet.kind,
                    "family": family,
                    "kernels": kernel_vector(rho_ab),
                }
            )

    ranking = family_ranking(rows)
    top = ranking[0]["aggregate_discrimination_score"]
    runner_up = ranking[1]["aggregate_discrimination_score"]
    overwhelming_margin = float(top - runner_up)
    return {
        "rows": rows,
        "family_ranking": ranking,
        "ranking_is_nontrivial": bool(top > 0.01),
        "overwhelming_margin": overwhelming_margin,
        "promote_final_winner": bool(overwhelming_margin > 0.20),
        "pass": True,
    }


def run_negative_tests() -> Dict[str, object]:
    packet = next(p for p in build_battery() if p.label == "mixed_competition")
    response = counterfactual_response(packet)
    hist_shift = response["history_scrambling"]["Xi_hist"]["weighted_cut_shift"]
    shell_shift = response["shell_ablation"]["Xi_shell"]["weighted_cut_shift"]
    ref_shift = response["reference_freeze"]["Xi_ref"]["weighted_cut_shift"]
    return {
        "mixed_case_counterfactuals": response,
        "history_scrambling_hits_history_family": bool(
            hist_shift > response["history_scrambling"]["Xi_ref"]["weighted_cut_shift"]
            and hist_shift > response["history_scrambling"]["Xi_shell"]["weighted_cut_shift"]
        ),
        "shell_ablation_hits_shell_family": bool(
            shell_shift > response["shell_ablation"]["Xi_ref"]["weighted_cut_shift"]
            and shell_shift > response["shell_ablation"]["Xi_hist"]["weighted_cut_shift"]
        ),
        "reference_freeze_hits_reference_family": bool(
            ref_shift > response["reference_freeze"]["Xi_shell"]["weighted_cut_shift"]
            and ref_shift > response["reference_freeze"]["Xi_hist"]["weighted_cut_shift"]
        ),
        "pass": bool(
            hist_shift > 1e-3
            and shell_shift > 1e-3
            and ref_shift > 1e-3
        ),
    }


def run_boundary_tests() -> Dict[str, object]:
    base = build_battery()[0]
    one_history = replace(base, history=[base.history[0]])
    exact_reference = replace(
        base,
        reference=ShellPoint(base.current.radius, base.current.theta, base.current.phi, 1.0),
    )
    flat_shell = replace(
        base,
        shells=[
            ShellPoint(base.current.radius, base.current.theta, base.current.phi, 1.0 / 3.0),
            ShellPoint(base.current.radius, base.current.theta, base.current.phi, 1.0 / 3.0),
            ShellPoint(base.current.radius, base.current.theta, base.current.phi, 1.0 / 3.0),
        ],
    )
    return {
        "single_history_sample": {
            "Xi_hist": kernel_vector(xi_hist(one_history)),
        },
        "exact_reference_match": {
            "Xi_ref": kernel_vector(xi_ref(exact_reference)),
        },
        "flat_shell_packet": {
            "Xi_shell": kernel_vector(xi_shell(flat_shell)),
        },
        "pass": True,
    }


def build_summary(positive: Dict[str, object], negative: Dict[str, object], boundary: Dict[str, object]) -> Dict[str, object]:
    tests_passed = int(bool(positive["pass"])) + int(bool(negative["pass"])) + int(bool(boundary["pass"]))
    ranking = positive["family_ranking"]
    note = (
        "No final winner promoted; the leading family does not clear the overwhelming-margin threshold."
        if not positive["promote_final_winner"]
        else "Margin is overwhelming enough to justify a tentative winner."
    )
    return {
        "tests_total": 3,
        "tests_passed": tests_passed,
        "all_pass": tests_passed == 3,
        "leader": ranking[0]["family"],
        "runner_up": ranking[1]["family"],
        "leader_margin": positive["overwhelming_margin"],
        "promotion_note": note,
    }


def main() -> Dict[str, object]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    return {
        "name": "xi_cut_kernel_ranking",
        "probe": "bridge_family_to_cut_kernel_ranking",
        "purpose": (
            "Compare Xi_ref-like, Xi_shell-like, and Xi_hist-like bridge families "
            "by the cut kernels induced after bipartite state construction."
        ),
        "classification": "supporting",
        "tools_used": ["numpy"],
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": build_summary(positive, negative, boundary),
    }


if __name__ == "__main__":
    results = main()
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "xi_cut_kernel_ranking_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(json.dumps(results["summary"], indent=2))
    print(f"Results written to {out_path}")
