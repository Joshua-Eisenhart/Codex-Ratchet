#!/usr/bin/env python3
"""
PURE LEGO: Xi Packet Expansion Stress
====================================
Bounded pure-math stress batch for surviving Xi-family winner claims.

Targeted packet classes:
  - counterfeit-driver
  - freeze-blind
  - shell-ablation-blind
  - history-scramble-blind
  - small-balance-collapse

Goal:
  expand packet coverage and test whether any Xi-family winner claim remains
  robust under more adversarial packet classes, without promoting final canon.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, replace
from typing import Dict, List

import numpy as np
classification = "classical_baseline"  # auto-backfill

EPS = 1e-12

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this bounded packet stress sim"},
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
class XiPacket:
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


def reference_offset(packet: XiPacket) -> float:
    return float(np.linalg.norm(shell_point_to_bloch(packet.current) - shell_point_to_bloch(packet.reference)))


def history_turning(packet: XiPacket) -> float:
    if len(packet.history) < 3:
        return 0.0
    phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
    second = np.diff(np.diff(phases))
    return float(np.mean(np.abs(second))) if len(second) else 0.0


def xi_ref(packet: XiPacket) -> np.ndarray:
    rho_cur = pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    rho_ref = pair_state(left_density(packet.reference), right_density(packet.reference), 0.0)
    coupling = 0.10 + 0.80 * math.tanh(1.6 * reference_offset(packet))
    bell = np.outer(BELL_PHI_PLUS, BELL_PHI_PLUS.conj())
    return ensure_density((1.0 - coupling) * 0.5 * (rho_cur + rho_ref) + coupling * bell)


def xi_shell(packet: XiPacket) -> np.ndarray:
    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    rho = np.zeros((4, 4), dtype=complex)
    for point, weight in zip(packet.shells, weights):
        coupling = 0.18 + 0.55 * abs(point.radius - packet.current.radius)
        rho += weight * pair_state(left_density(point), right_density(point), coupling)
    return ensure_density(rho)


def xi_hist(packet: XiPacket) -> np.ndarray:
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
        coupling = 0.12 + 0.5 * abs(point.radius - packet.current.radius) + 0.35 * turning
        rho += weight * pair_state(left_density(point), right_density(point), coupling)
    return ensure_density(rho)


def family_scores(packet: XiPacket) -> Dict[str, float]:
    return {
        "Xi_ref": weighted_cut_functional(xi_ref(packet)),
        "Xi_shell": weighted_cut_functional(xi_shell(packet)),
        "Xi_hist": weighted_cut_functional(xi_hist(packet)),
    }


def winner(scores: Dict[str, float]) -> str:
    return max(scores.items(), key=lambda kv: kv[1])[0]


def margin(scores: Dict[str, float]) -> float:
    ordered = sorted(scores.values(), reverse=True)
    return float(ordered[0] - ordered[1])


def history_scramble(packet: XiPacket) -> XiPacket:
    order = [2, 0, 3, 1][: len(packet.history)]
    return replace(packet, history=[packet.history[i] for i in order])


def shell_ablation(packet: XiPacket) -> XiPacket:
    mid = packet.shells[len(packet.shells) // 2]
    return replace(packet, shells=[replace(mid, weight=1.0)])


def reference_freeze(packet: XiPacket) -> XiPacket:
    return replace(packet, reference=ShellPoint(packet.current.radius, packet.current.theta, packet.current.phi, 1.0))


def rebalance(packet: XiPacket, delta: float) -> XiPacket:
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
) -> XiPacket:
    current = ShellPoint(current_radius, 1.02, 0.75, 1.0)
    shells = [
        ShellPoint(r, 0.72 + 0.16 * i, -0.2 + 0.55 * i, w)
        for i, (r, w) in enumerate(zip(shell_radii, shell_weights))
    ]
    history = [
        ShellPoint(r, 0.80 + 0.10 * i, phi, 1.0)
        for i, (r, phi) in enumerate(zip(history_radii, history_phis))
    ]
    reference = ShellPoint(current_radius, 1.02, reference_phi, 1.0)
    return XiPacket(label, packet_class, current, shells, history, reference)


def build_packets() -> Dict[str, XiPacket]:
    return {
        "reference_target": make_packet(
            "reference_target", "reference_target",
            0.28,
            [0.28, 0.29, 0.30, 0.28], [0.25, 0.25, 0.25, 0.25],
            [0.28, 0.29, 0.28, 0.29], [0.75, 0.82, 0.79, 0.81],
            2.85,
        ),
        "shell_target": make_packet(
            "shell_target", "shell_target",
            0.24,
            [0.10, 0.32, 0.66, 0.90], [0.08, 0.18, 0.29, 0.45],
            [0.24, 0.25, 0.24, 0.23], [0.76, 0.79, 0.81, 0.83],
            0.88,
        ),
        "history_target": make_packet(
            "history_target", "history_target",
            0.27,
            [0.26, 0.27, 0.28, 0.27], [0.25, 0.25, 0.25, 0.25],
            [0.12, 0.65, 0.16, 0.72], [0.10, 2.45, 0.35, 2.80],
            0.95,
        ),
        "counterfeit_driver": make_packet(
            "counterfeit_driver", "counterfeit_driver",
            0.18,
            [0.18, 0.18, 0.19, 0.18], [0.92, 0.03, 0.03, 0.02],
            [0.18, 0.18, 0.18, 0.18], [0.75, 0.77, 0.76, 0.75],
            0.79,
        ),
        "freeze_blind": make_packet(
            "freeze_blind", "freeze_blind",
            0.34,
            [0.20, 0.42, 0.63, 0.83], [0.10, 0.20, 0.30, 0.40],
            [0.34, 0.33, 0.35, 0.34], [0.60, 0.95, 1.40, 1.95],
            0.76,
        ),
        "shell_ablation_blind": make_packet(
            "shell_ablation_blind", "shell_ablation_blind",
            0.26,
            [0.14, 0.51, 0.83, 0.24], [0.06, 0.14, 0.54, 0.26],
            [0.26, 0.27, 0.26, 0.27], [0.73, 0.76, 0.74, 0.77],
            0.84,
        ),
        "history_scramble_blind": make_packet(
            "history_scramble_blind", "history_scramble_blind",
            0.29,
            [0.29, 0.30, 0.29, 0.28], [0.25, 0.25, 0.25, 0.25],
            [0.14, 0.70, 0.18, 0.74], [0.20, 2.60, 0.45, 3.00],
            0.92,
        ),
        "small_balance_collapse": make_packet(
            "small_balance_collapse", "small_balance_collapse",
            0.22,
            [0.18, 0.24, 0.62, 0.66], [0.24, 0.25, 0.26, 0.25],
            [0.22, 0.23, 0.22, 0.23], [0.72, 0.78, 0.74, 0.80],
            0.86,
        ),
    }


def run_positive_tests() -> Dict[str, dict]:
    packets = build_packets()

    ref_scores = family_scores(packets["reference_target"])
    shell_scores = family_scores(packets["shell_target"])
    hist_scores = family_scores(packets["history_target"])

    return {
        "reference_target_prefers_xi_ref": {
            "scores": ref_scores,
            "winner": winner(ref_scores),
            "pass": winner(ref_scores) == "Xi_ref",
        },
        "shell_target_prefers_xi_shell": {
            "scores": shell_scores,
            "winner": winner(shell_scores),
            "pass": winner(shell_scores) == "Xi_shell",
        },
        "history_target_prefers_xi_hist": {
            "scores": hist_scores,
            "winner": winner(hist_scores),
            "pass": winner(hist_scores) == "Xi_hist",
        },
        "expanded_library_has_no_universal_winner": {
            "winners": {
                "reference_target": winner(ref_scores),
                "shell_target": winner(shell_scores),
                "history_target": winner(hist_scores),
            },
            "distinct_winners": len({winner(ref_scores), winner(shell_scores), winner(hist_scores)}),
            "pass": len({winner(ref_scores), winner(shell_scores), winner(hist_scores)}) == 3,
        },
    }


def run_negative_tests() -> Dict[str, dict]:
    packets = build_packets()

    counterfeit_scores = family_scores(packets["counterfeit_driver"])
    counterfeit_rebalanced = family_scores(rebalance(packets["counterfeit_driver"], 0.08))

    freeze_scores = family_scores(packets["freeze_blind"])
    freeze_frozen = family_scores(reference_freeze(packets["freeze_blind"]))

    shell_scores = family_scores(packets["shell_ablation_blind"])
    shell_ablated = family_scores(shell_ablation(packets["shell_ablation_blind"]))

    hist_scores = family_scores(packets["history_scramble_blind"])
    hist_scrambled = family_scores(history_scramble(packets["history_scramble_blind"]))

    balance_scores = family_scores(packets["small_balance_collapse"])
    balance_shifted = family_scores(rebalance(packets["small_balance_collapse"], 0.04))

    return {
        "counterfeit_driver_packet_is_fragile_low_margin_even_before_rebalance": {
            "base_scores": counterfeit_scores,
            "shifted_scores": counterfeit_rebalanced,
            "base_margin": margin(counterfeit_scores),
            "shifted_margin": margin(counterfeit_rebalanced),
            "low_margin_regime": margin(counterfeit_scores) < 0.02 and margin(counterfeit_rebalanced) < 0.02,
            "pass": margin(counterfeit_scores) < 0.02 and margin(counterfeit_rebalanced) < 0.02,
        },
        "freeze_candidate_is_not_reference_dominated_under_expanded_coverage": {
            "base_scores": freeze_scores,
            "frozen_scores": freeze_frozen,
            "xi_ref_drop": freeze_scores["Xi_ref"] - freeze_frozen["Xi_ref"],
            "shell_remains_winner": winner(freeze_scores) == winner(freeze_frozen) == "Xi_shell",
            "pass": winner(freeze_scores) == winner(freeze_frozen) == "Xi_shell",
        },
        "shell_ablation_candidate_remains_shell_dominated_after_ablation": {
            "base_scores": shell_scores,
            "ablated_scores": shell_ablated,
            "xi_shell_change": shell_ablated["Xi_shell"] - shell_scores["Xi_shell"],
            "shell_still_wins": winner(shell_scores) == winner(shell_ablated) == "Xi_shell",
            "pass": winner(shell_scores) == winner(shell_ablated) == "Xi_shell",
        },
        "history_scramble_candidate_is_genuinely_scramble_blind_here": {
            "base_scores": hist_scores,
            "scrambled_scores": hist_scrambled,
            "xi_hist_change": hist_scrambled["Xi_hist"] - hist_scores["Xi_hist"],
            "winner_stable": winner(hist_scores) == winner(hist_scrambled) == "Xi_hist",
            "near_invariant": abs(hist_scrambled["Xi_hist"] - hist_scores["Xi_hist"]) < 1e-3,
            "pass": winner(hist_scores) == winner(hist_scrambled) == "Xi_hist"
                    and abs(hist_scrambled["Xi_hist"] - hist_scores["Xi_hist"]) < 1e-3,
        },
        "small_balance_candidate_does_not_collapse_under_tiny_rebalance": {
            "base_scores": balance_scores,
            "shifted_scores": balance_shifted,
            "base_margin": margin(balance_scores),
            "shifted_margin": margin(balance_shifted),
            "winner_stable": winner(balance_scores) == winner(balance_shifted) == "Xi_shell",
            "margin_reduction_small": (margin(balance_scores) - margin(balance_shifted)) < 0.02,
            "pass": winner(balance_scores) == winner(balance_shifted) == "Xi_shell"
                    and (margin(balance_scores) - margin(balance_shifted)) < 0.02,
        },
    }


def run_boundary_tests() -> Dict[str, dict]:
    packets = build_packets()
    shell_target = family_scores(packets["shell_target"])
    shell_rebalanced = family_scores(rebalance(packets["shell_target"], 0.02))
    ref_target = family_scores(packets["reference_target"])
    hist_target = family_scores(packets["history_target"])

    return {
        "matched_target_packets_keep_clear_positive_margins": {
            "reference_margin": margin(ref_target),
            "shell_margin": margin(shell_target),
            "history_margin": margin(hist_target),
            "all_positive": margin(ref_target) > 0.01 and margin(shell_target) > 0.01 and margin(hist_target) > 0.01,
            "pass": margin(ref_target) > 0.01 and margin(shell_target) > 0.01 and margin(hist_target) > 0.01,
        },
        "small_rebalance_does_not_break_legitimate_shell_target": {
            "base_scores": shell_target,
            "rebalanced_scores": shell_rebalanced,
            "same_winner": winner(shell_target) == winner(shell_rebalanced) == "Xi_shell",
            "pass": winner(shell_target) == winner(shell_rebalanced) == "Xi_shell",
        },
        "expanded_packets_separate_targeted_and_counterfeit_classes": {
            "target_winners": {
                "reference": winner(ref_target),
                "shell": winner(shell_target),
                "history": winner(hist_target),
            },
            "counterfeit_winner": winner(family_scores(packets["counterfeit_driver"])),
            "not_all_same": len({
                winner(ref_target),
                winner(shell_target),
                winner(hist_target),
                winner(family_scores(packets["counterfeit_driver"])),
            }) > 1,
            "pass": len({
                winner(ref_target),
                winner(shell_target),
                winner(hist_target),
                winner(family_scores(packets["counterfeit_driver"])),
            }) > 1,
        },
    }


def count_section(section: Dict[str, dict]) -> Dict[str, int]:
    total = sum(1 for v in section.values() if isinstance(v, dict) and "pass" in v)
    passed = sum(1 for v in section.values() if isinstance(v, dict) and v.get("pass") is True)
    return {"passed": passed, "failed": total - passed, "total": total}


def main() -> None:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    pos = count_section(positive)
    neg = count_section(negative)
    bnd = count_section(boundary)
    total_fail = pos["failed"] + neg["failed"] + bnd["failed"]

    results = {
        "name": "PURE LEGO: Xi Packet Expansion Stress",
        "probe": "xi_packet_expansion_stress",
        "purpose": "Stress surviving Xi-family winner claims against expanded packet families and targeted disqualifiers",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "classical_baseline",
        "caveat": "Bounded stress battery only. This expands packet coverage around Xi-family winner claims but does not promote final canon.",
        "summary": {
            "positive_pass": pos["passed"],
            "positive_fail": pos["failed"],
            "negative_pass": neg["passed"],
            "negative_fail": neg["failed"],
            "boundary_pass": bnd["passed"],
            "boundary_fail": bnd["failed"],
            "total_fail": total_fail,
            "all_pass": total_fail == 0,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "xi_packet_expansion_stress_results.json")
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2)

    print(f"Results written to {out_path}")
    print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    main()
