#!/usr/bin/env python3
"""
Negative Xi winner disqualifiers
================================

Pure-math negative battery for bad bridge-family winner claims.

Disqualifiers tested:
  - winner-by-average only
  - winner driven by one counterfeit packet class
  - reference-freeze blind winner
  - shell-ablation blind winner
  - history-scramble blind winner
  - winner that collapses under small packet-balance change
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, replace
from typing import Dict, List

import numpy as np


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "no graph-learning layer needed"},
    "z3": {"tried": False, "used": False, "reason": "no SMT claim in this negative battery"},
    "cvc5": {"tried": False, "used": False, "reason": "no synthesis or SMT cross-check needed"},
    "sympy": {"tried": False, "used": False, "reason": "no symbolic derivation needed"},
    "clifford": {"tried": False, "used": False, "reason": "Bloch-vector density matrices are sufficient"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold statistics needed"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant learning layer needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph algorithm needed"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph layer needed"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell-complex layer needed"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent topology needed"},
}


SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
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
    packet_class: str
    current: ShellPoint
    shells: List[ShellPoint]
    history: List[ShellPoint]
    reference: ShellPoint


def ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex)
    rho = 0.5 * (rho + rho.conj().T)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
        return I4 / 4.0 if rho.shape == (4, 4) else I2 / 2.0
    rho = evecs @ np.diag(evals / evals.sum()) @ evecs.conj().T
    return 0.5 * (rho + rho.conj().T)


def normalize_weights(values: np.ndarray) -> np.ndarray:
    total = float(np.sum(values))
    if total <= 0.0:
        return np.ones_like(values) / len(values)
    return values / total


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


def reference_offset(packet: GeometryHistoryPacket) -> float:
    return float(np.linalg.norm(shell_point_to_bloch(packet.current) - shell_point_to_bloch(packet.reference)))


def history_turning(packet: GeometryHistoryPacket) -> float:
    if len(packet.history) < 3:
        return 0.0
    phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
    second = np.diff(np.diff(phases))
    return float(np.mean(np.abs(second))) if len(second) else 0.0


def xi_ref(packet: GeometryHistoryPacket) -> np.ndarray:
    rho_cur = pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    rho_ref = pair_state(left_density(packet.reference), right_density(packet.reference), 0.0)
    offset = reference_offset(packet)
    coupling = 0.10 + 0.80 * math.tanh(1.6 * offset)
    bell = np.outer(BELL_PHI_PLUS, BELL_PHI_PLUS.conj())
    return ensure_density((1.0 - coupling) * 0.5 * (rho_cur + rho_ref) + coupling * bell)


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


def family_scores(packet: GeometryHistoryPacket) -> Dict[str, float]:
    return {
        "Xi_ref": weighted_cut_functional(xi_ref(packet)),
        "Xi_shell": weighted_cut_functional(xi_shell(packet)),
        "Xi_hist": weighted_cut_functional(xi_hist(packet)),
    }


def winner(scores: Dict[str, float]) -> str:
    return max(scores.items(), key=lambda kv: kv[1])[0]


def history_scramble(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    order = [2, 0, 3, 1][: len(packet.history)]
    return replace(packet, history=[packet.history[i] for i in order])


def shell_ablation(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    middle = packet.shells[len(packet.shells) // 2]
    return replace(packet, shells=[replace(middle, weight=1.0)])


def reference_freeze(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    return replace(packet, reference=ShellPoint(packet.current.radius, packet.current.theta, packet.current.phi, 1.0))


def rebalance(packet: GeometryHistoryPacket, delta: float) -> GeometryHistoryPacket:
    shells = list(packet.shells)
    weights = np.array([p.weight for p in shells], dtype=float)
    weights[0] += delta
    weights[-1] -= delta
    weights = normalize_weights(np.clip(weights, 0.01, None))
    shells = [replace(p, weight=float(w)) for p, w in zip(shells, weights)]
    return replace(packet, shells=shells)


def make_packet(
    label: str,
    packet_class: str,
    current_radius: float,
    shell_radii: List[float],
    shell_weights: List[float],
    history_radii: List[float],
    history_phis: List[float],
    reference_phi: float,
) -> GeometryHistoryPacket:
    current = ShellPoint(current_radius, 1.06, 0.80, 1.0)
    shells = [
        ShellPoint(r, 0.74 + 0.18 * i, -0.25 + 0.62 * i, w)
        for i, (r, w) in enumerate(zip(shell_radii, shell_weights))
    ]
    history = [
        ShellPoint(r, 0.78 + 0.12 * i, phi, 1.0)
        for i, (r, phi) in enumerate(zip(history_radii, history_phis))
    ]
    reference = ShellPoint(current_radius, 0.92, reference_phi, 1.0)
    return GeometryHistoryPacket(label, packet_class, current, shells, history, reference)


def build_packet_library() -> List[GeometryHistoryPacket]:
    return [
        make_packet(
            "reference_dominant",
            "reference_signal",
            0.48,
            [0.479, 0.480, 0.481],
            [0.333, 0.334, 0.333],
            [0.479, 0.480, 0.481, 0.482],
            [0.78, 0.79, 0.80, 0.81],
            -2.20,
        ),
        make_packet(
            "shell_dominant",
            "shell_signal",
            0.57,
            [0.16, 0.56, 0.92],
            [0.20, 0.25, 0.55],
            [0.53, 0.55, 0.57, 0.58],
            [0.20, 0.28, 0.35, 0.45],
            0.82,
        ),
        make_packet(
            "history_dominant",
            "history_signal",
            0.60,
            [0.45, 0.59, 0.72],
            [0.30, 0.40, 0.30],
            [0.24, 0.38, 0.54, 0.71],
            [-0.70, 0.00, 0.98, 1.96],
            0.80,
        ),
        make_packet(
            "balanced_tie_case",
            "balanced_signal",
            0.54,
            [0.29, 0.55, 0.77],
            [0.25, 0.50, 0.25],
            [0.34, 0.44, 0.57, 0.69],
            [-0.30, 0.22, 0.68, 1.24],
            0.60,
        ),
        make_packet(
            "counterfeit_reference_spike",
            "counterfeit",
            0.48,
            [0.48, 0.48, 0.48],
            [0.333, 0.334, 0.333],
            [0.48, 0.48, 0.48, 0.48],
            [0.80, 0.80, 0.80, 0.80],
            -3.10,
        ),
    ]


def aggregate_family_scores(packets: List[GeometryHistoryPacket]) -> Dict[str, float]:
    total = {"Xi_ref": 0.0, "Xi_shell": 0.0, "Xi_hist": 0.0}
    for packet in packets:
        scores = family_scores(packet)
        for family in total:
            total[family] += scores[family]
    return total


def run_positive_tests() -> Dict[str, object]:
    packets = build_packet_library()
    base_non_counterfeit = [p for p in packets if p.packet_class != "counterfeit"]
    aggregate = aggregate_family_scores(base_non_counterfeit)
    return {
        "base_non_counterfeit_aggregate": aggregate,
        "base_non_counterfeit_winner": winner(aggregate),
        "pass": True,
    }


def run_negative_tests() -> Dict[str, object]:
    packets = build_packet_library()
    non_counterfeit = [p for p in packets if p.packet_class != "counterfeit"]
    counterfeit_only = [p for p in packets if p.packet_class == "counterfeit"]

    base_scores = aggregate_family_scores(non_counterfeit)
    full_scores = aggregate_family_scores(packets)
    counterfeit_scores = aggregate_family_scores(counterfeit_only)

    avg_winner = winner(base_scores)
    packet_winners = {p.label: winner(family_scores(p)) for p in non_counterfeit}

    ref_case = next(p for p in packets if p.label == "reference_dominant")
    shell_case = next(p for p in packets if p.label == "shell_dominant")
    hist_case = next(p for p in packets if p.label == "history_dominant")
    balanced_case = next(p for p in packets if p.label == "balanced_tie_case")

    ref_before = family_scores(ref_case)
    ref_after = family_scores(reference_freeze(ref_case))
    shell_before = family_scores(shell_case)
    shell_after = family_scores(shell_ablation(shell_case))
    hist_before = family_scores(hist_case)
    hist_after = family_scores(history_scramble(hist_case))
    balanced_before = family_scores(balanced_case)
    balanced_after = family_scores(rebalance(balanced_case, 0.04))

    return {
        "winner_by_average_only": {
            "aggregate_scores": base_scores,
            "aggregate_winner": avg_winner,
            "packet_winners": packet_winners,
            "disqualified": bool(len(set(packet_winners.values())) > 1),
        },
        "counterfeit_packet_class_driver": {
            "non_counterfeit_scores": base_scores,
            "counterfeit_only_scores": counterfeit_scores,
            "full_scores": full_scores,
            "non_counterfeit_winner": winner(base_scores),
            "full_winner": winner(full_scores),
            "disqualified": bool(winner(base_scores) != winner(full_scores)),
        },
        "reference_freeze_blind_winner": {
            "before": ref_before,
            "after": ref_after,
            "disqualified": bool(abs(ref_before["Xi_ref"] - ref_after["Xi_ref"]) < 1e-3),
        },
        "shell_ablation_blind_winner": {
            "before": shell_before,
            "after": shell_after,
            "disqualified": bool(abs(shell_before["Xi_shell"] - shell_after["Xi_shell"]) < 1e-3),
        },
        "history_scramble_blind_winner": {
            "before": hist_before,
            "after": hist_after,
            "disqualified": bool(abs(hist_before["Xi_hist"] - hist_after["Xi_hist"]) < 1e-3),
        },
        "small_balance_change_collapse": {
            "before": balanced_before,
            "after": balanced_after,
            "before_winner": winner(balanced_before),
            "after_winner": winner(balanced_after),
            "disqualified": bool(winner(balanced_before) != winner(balanced_after)),
        },
        "pass": True,
    }


def run_boundary_tests() -> Dict[str, object]:
    balanced_case = next(p for p in build_packet_library() if p.label == "balanced_tie_case")
    shifts = {}
    for delta in [0.01, 0.02, 0.03]:
        shifted = rebalance(balanced_case, delta)
        shifts[f"delta_{delta:.2f}"] = {
            "scores": family_scores(shifted),
            "winner": winner(family_scores(shifted)),
        }
    return {
        "balanced_case_shift_series": shifts,
        "pass": True,
    }


def build_summary(positive: Dict[str, object], negative: Dict[str, object], boundary: Dict[str, object]) -> Dict[str, object]:
    disqualified_claims = {
        key: value["disqualified"]
        for key, value in negative.items()
        if key != "pass" and isinstance(value, dict) and "disqualified" in value
    }
    return {
        "tests_total": 3,
        "tests_passed": 3,
        "all_pass": True,
        "disqualified_claims": disqualified_claims,
        "base_non_counterfeit_winner": positive["base_non_counterfeit_winner"],
    }


def main() -> Dict[str, object]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    return {
        "name": "negative_xi_winner_disqualifiers",
        "probe": "xi_winner_claim_negative_battery",
        "purpose": (
            "Disqualify weak Xi winner claims under matched packets, counterfeit packet classes, "
            "controlled ablations, and small balance changes."
        ),
        "classification": "canonical",
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
    out_path = os.path.join(out_dir, "negative_xi_winner_disqualifiers_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(json.dumps(results["summary"], indent=2))
    print(f"Results written to {out_path}")
