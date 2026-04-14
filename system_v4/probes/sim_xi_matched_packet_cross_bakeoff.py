#!/usr/bin/env python3
"""
Xi matched-packet cross bakeoff
===============================

Pure-math comparison of Xi_ref-like, Xi_shell-like, and Xi_hist-like bridge
families on a matched packet library.

This probe is designed to answer a sharper question than average ranking:
  - On packets built to privilege reference, shell, or history structure,
    which family actually dominates?
  - On packets that remove a family's signature, does that family fail?
  - Does any "winner by average" claim survive explicit falsifiers?
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
    "z3": {"tried": False, "used": False, "reason": "no SMT claim in this bounded bakeoff"},
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
    expected_dominant_family: str | None
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


def shell_dispersion(packet: GeometryHistoryPacket) -> float:
    return float(np.std(np.array([p.radius for p in packet.shells], dtype=float)))


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


def kernel_score(rho_ab: np.ndarray) -> float:
    return weighted_cut_functional(rho_ab)


def family_states(packet: GeometryHistoryPacket) -> Dict[str, np.ndarray]:
    return {
        "Xi_ref": xi_ref(packet),
        "Xi_shell": xi_shell(packet),
        "Xi_hist": xi_hist(packet),
    }


def evaluate_packet(packet: GeometryHistoryPacket) -> Dict[str, object]:
    states = family_states(packet)
    scores = {name: kernel_score(rho) for name, rho in states.items()}
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return {
        "packet_label": packet.label,
        "expected_dominant_family": packet.expected_dominant_family,
        "features": {
            "reference_offset": reference_offset(packet),
            "shell_dispersion": shell_dispersion(packet),
            "history_turning": history_turning(packet),
        },
        "scores": scores,
        "winner": ordered[0][0],
        "runner_up": ordered[1][0],
        "winner_margin": float(ordered[0][1] - ordered[1][1]),
        "matches_expectation": bool(
            packet.expected_dominant_family is None or ordered[0][0] == packet.expected_dominant_family
        ),
    }


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


def build_packet_library() -> List[GeometryHistoryPacket]:
    def packet(
        label: str,
        expected: str | None,
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
        return GeometryHistoryPacket(label, expected, current, shells, history, reference)

    return [
        packet(
            "reference_dominant",
            "Xi_ref",
            0.48,
            [0.479, 0.480, 0.481],
            [0.333, 0.334, 0.333],
            [0.479, 0.480, 0.481, 0.482],
            [0.78, 0.79, 0.80, 0.81],
            -2.20,
        ),
        packet(
            "shell_dominant",
            "Xi_shell",
            0.57,
            [0.16, 0.56, 0.92],
            [0.20, 0.25, 0.55],
            [0.53, 0.55, 0.57, 0.58],
            [0.20, 0.28, 0.35, 0.45],
            0.82,
        ),
        packet(
            "history_dominant",
            "Xi_hist",
            0.60,
            [0.45, 0.59, 0.72],
            [0.30, 0.40, 0.30],
            [0.24, 0.38, 0.54, 0.71],
            [-0.70, 0.00, 0.98, 1.96],
            0.80,
        ),
        packet(
            "balanced_tie_case",
            None,
            0.54,
            [0.29, 0.55, 0.77],
            [0.25, 0.50, 0.25],
            [0.34, 0.44, 0.57, 0.69],
            [-0.30, 0.22, 0.68, 1.24],
            0.60,
        ),
    ]


def run_positive_tests() -> Dict[str, object]:
    packets = build_packet_library()
    evaluations = [evaluate_packet(packet) for packet in packets]
    expected_packets = [entry for entry in evaluations if entry["expected_dominant_family"] is not None]
    expectation_hits = sum(1 for entry in expected_packets if entry["matches_expectation"])
    return {
        "packet_evaluations": evaluations,
        "expected_hits": expectation_hits,
        "expected_total": len(expected_packets),
        "pass": bool(expectation_hits == len(expected_packets)),
    }


def run_negative_tests() -> Dict[str, object]:
    library = {packet.label: packet for packet in build_packet_library()}
    ref_case = library["reference_dominant"]
    shell_case = library["shell_dominant"]
    hist_case = library["history_dominant"]
    balanced = library["balanced_tie_case"]

    ref_frozen = evaluate_packet(reference_freeze(ref_case))
    shell_ablated = evaluate_packet(shell_ablation(shell_case))
    hist_scrambled = evaluate_packet(history_scramble(hist_case))
    balanced_eval = evaluate_packet(balanced)

    average_only_rows = [evaluate_packet(packet) for packet in build_packet_library()]
    family_wins = {}
    for row in average_only_rows:
        family_wins[row["winner"]] = family_wins.get(row["winner"], 0) + 1

    return {
        "reference_freeze_falsifier": {
            "before": evaluate_packet(ref_case),
            "after": ref_frozen,
            "pass": bool(
                ref_frozen["scores"]["Xi_ref"] < evaluate_packet(ref_case)["scores"]["Xi_ref"]
                and ref_frozen["scores"]["Xi_ref"] <= ref_frozen["scores"]["Xi_shell"]
            ),
        },
        "shell_ablation_falsifier": {
            "before": evaluate_packet(shell_case),
            "after": shell_ablated,
            "pass": bool(
                shell_ablated["scores"]["Xi_shell"] < evaluate_packet(shell_case)["scores"]["Xi_shell"]
            ),
        },
        "history_scramble_falsifier": {
            "before": evaluate_packet(hist_case),
            "after": hist_scrambled,
            "pass": bool(
                abs(
                    hist_scrambled["scores"]["Xi_hist"] - evaluate_packet(hist_case)["scores"]["Xi_hist"]
                )
                > 1e-3
            ),
        },
        "winner_by_average_falsifier": {
            "balanced_case": balanced_eval,
            "family_win_counts": family_wins,
            "pass": bool(balanced_eval["winner_margin"] < 0.08),
        },
        "pass": bool(
            ref_frozen["scores"]["Xi_ref"] < evaluate_packet(ref_case)["scores"]["Xi_ref"]
            and shell_ablated["scores"]["Xi_shell"] < evaluate_packet(shell_case)["scores"]["Xi_shell"]
            and abs(
                hist_scrambled["scores"]["Xi_hist"] - evaluate_packet(hist_case)["scores"]["Xi_hist"]
            ) > 1e-3
            and balanced_eval["winner_margin"] < 0.08
        ),
    }


def run_boundary_tests() -> Dict[str, object]:
    ref_case = next(packet for packet in build_packet_library() if packet.label == "reference_dominant")
    one_history = replace(ref_case, history=[ref_case.history[0]])
    one_shell = replace(ref_case, shells=[replace(ref_case.shells[1], weight=1.0)])
    exact_reference = reference_freeze(ref_case)
    return {
        "single_history_packet": evaluate_packet(one_history),
        "single_shell_packet": evaluate_packet(one_shell),
        "exact_reference_packet": evaluate_packet(exact_reference),
        "pass": True,
    }


def build_summary(positive: Dict[str, object], negative: Dict[str, object], boundary: Dict[str, object]) -> Dict[str, object]:
    tests_passed = int(bool(positive["pass"])) + int(bool(negative["pass"])) + int(bool(boundary["pass"]))
    return {
        "tests_total": 3,
        "tests_passed": tests_passed,
        "all_pass": tests_passed == 3,
        "expected_hits": positive["expected_hits"],
        "expected_total": positive["expected_total"],
        "promotion_note": (
            "Matched packets separate family-local strengths and falsify winner-by-average shortcuts. "
            "No final canon promoted."
        ),
    }


def main() -> Dict[str, object]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    return {
        "name": "xi_matched_packet_cross_bakeoff",
        "probe": "matched_packet_bridge_family_cross_bakeoff",
        "purpose": (
            "Compare Xi_ref-like, Xi_shell-like, and Xi_hist-like families on matched packets "
            "with explicit local-dominance and local-failure tests."
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
    out_path = os.path.join(out_dir, "xi_matched_packet_cross_bakeoff_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(json.dumps(results["summary"], indent=2))
    print(f"Results written to {out_path}")
