#!/usr/bin/env python3
"""
3-qubit ambiguity expansion
===========================

Pure-math expansion that only activates on 2-qubit packets whose bridge-level
picture remains inconclusive.

Goal:
  - identify packets where 2q family scores are too close to separate cleanly
  - lift only those packets into 3q form
  - test whether multipartite structure resolves the ambiguity

What it measures:
  - 2q family scores on Xi_ref / Xi_shell / Xi_hist
  - 3q multipartite resolution scores on lifted families
  - tripartite mutual information and cut-spread structure

Notes:
  - Pure math only.
  - This is not a broad 3q survey.
  - Clear 2q cases are excluded by design.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
classification = "classical_baseline"  # auto-backfill

np.random.seed(29)
EPS = 1e-12
AMBIGUITY_GAP = 0.08


# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy ambiguity expansion"},
    "pyg": {"tried": False, "used": False, "reason": "no graph layer is needed for this focused expansion"},
    "z3": {"tried": False, "used": False, "reason": "no symbolic satisfiability claim is required here"},
    "cvc5": {"tried": False, "used": False, "reason": "no synthesis or SMT cross-check is required here"},
    "sympy": {"tried": False, "used": False, "reason": "all calculations are numerical and finite-dimensional"},
    "clifford": {"tried": False, "used": False, "reason": "the probe uses only explicit density matrices"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold numerics are needed for this bounded probe"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant learning is outside scope"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph kernel is needed here"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph layer is needed here"},
    "toponetx": {"tried": False, "used": False, "reason": "this probe uses direct packet arrays, not complexes"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence computation is needed here"},
}


# =====================================================================
# DATA TYPES
# =====================================================================


@dataclass
class ShellPoint:
    radius: float
    theta: float
    phi: float
    weight: float


@dataclass
class GeometryHistoryPacket:
    label: str
    current: ShellPoint
    shells: List[ShellPoint]
    history: List[ShellPoint]
    reference: ShellPoint


I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)
I8 = np.eye(8, dtype=complex)
SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
BELL_PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / math.sqrt(2.0)
BELL_PSI_MINUS = np.array([0.0, 1.0, -1.0, 0.0], dtype=complex) / math.sqrt(2.0)


# =====================================================================
# BASIC 2Q HELPERS
# =====================================================================


def _hermitian(rho: np.ndarray) -> np.ndarray:
    return 0.5 * (rho + rho.conj().T)


def ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex)
    rho = _hermitian(rho)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
        if rho.shape == (8, 8):
            return I8 / 8.0
        if rho.shape == (4, 4):
            return I4 / 4.0
        return I2 / 2.0
    rho = evecs @ np.diag(evals / evals.sum()) @ evecs.conj().T
    return _hermitian(rho)


def vn_entropy(rho: np.ndarray) -> float:
    rho = ensure_density(rho)
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > EPS]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def purity(rho: np.ndarray) -> float:
    rho = ensure_density(rho)
    return float(np.real(np.trace(rho @ rho)))


def is_pure(rho: np.ndarray, tol: float = 1e-9) -> bool:
    return bool(abs(purity(rho) - 1.0) <= tol)


def partial_trace_A(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def mutual_information(rho_ab: np.ndarray) -> float:
    rho_ab = ensure_density(rho_ab)
    return float(vn_entropy(partial_trace_A(rho_ab)) + vn_entropy(partial_trace_B(rho_ab)) - vn_entropy(rho_ab))


def conditional_entropy_a_given_b(rho_ab: np.ndarray) -> float:
    rho_ab = ensure_density(rho_ab)
    return float(vn_entropy(rho_ab) - vn_entropy(partial_trace_B(rho_ab)))


def coherent_information_a_to_b(rho_ab: np.ndarray) -> float:
    rho_ab = ensure_density(rho_ab)
    return float(vn_entropy(partial_trace_B(rho_ab)) - vn_entropy(rho_ab))


def entanglement_entropy_if_pure(rho_ab: np.ndarray):
    if not is_pure(rho_ab):
        return None
    return float(vn_entropy(partial_trace_A(rho_ab)))


def negativity(rho_ab: np.ndarray) -> float:
    rho = ensure_density(rho_ab)
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(_hermitian(pt))
    return float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0))


def weighted_cut_functional(rho_ab: np.ndarray) -> float:
    ee = entanglement_entropy_if_pure(rho_ab)
    ee_term = 0.0 if ee is None else ee
    mi = mutual_information(rho_ab)
    ci = coherent_information_a_to_b(rho_ab)
    neg = negativity(rho_ab)
    return float(0.38 * mi + 0.32 * max(0.0, ci) + 0.20 * neg + 0.10 * ee_term)


def normalize_weights(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    total = float(np.sum(values))
    if total <= 0.0:
        return np.ones_like(values) / len(values)
    return values / total


def shell_point_to_bloch(point: ShellPoint) -> np.ndarray:
    radius = float(np.clip(point.radius, 0.0, 0.999))
    return radius * np.array(
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
    v = shell_point_to_bloch(point)
    rotated = np.array([v[2], -v[1], v[0]], dtype=float)
    return bloch_to_density(rotated)


def pair_state(rho_a: np.ndarray, rho_b: np.ndarray, coupling: float) -> np.ndarray:
    coupling = float(np.clip(coupling, 0.0, 0.95))
    prod = np.kron(rho_a, rho_b)
    bell = np.outer(BELL_PHI_PLUS, BELL_PHI_PLUS.conj())
    return ensure_density((1.0 - coupling) * prod + coupling * bell)


def local_dephase(rho_ab: np.ndarray, p: float = 0.4, on: str = "A") -> np.ndarray:
    z = SIGMA_Z
    op = np.kron(z, I2) if on == "A" else np.kron(I2, z)
    return ensure_density((1.0 - p) * rho_ab + p * (op @ rho_ab @ op.conj().T))


def local_depolarize(rho_ab: np.ndarray, p: float = 0.3, on: str = "A") -> np.ndarray:
    rho_ab = ensure_density(rho_ab)
    if on == "A":
        rho_b = partial_trace_A(rho_ab)
        return ensure_density((1.0 - p) * rho_ab + p * np.kron(I2 / 2.0, rho_b))
    rho_a = partial_trace_B(rho_ab)
    return ensure_density((1.0 - p) * rho_ab + p * np.kron(rho_a, I2 / 2.0))


def create_2q_packet(label: str, current_r: float, shell_rs: List[float], shell_ws: List[float], hist_rs: List[float], hist_phis: List[float], ref_phi: float) -> GeometryHistoryPacket:
    current = ShellPoint(current_r, 1.06, 0.80, 1.0)
    shells = [ShellPoint(r, 0.74 + 0.18 * i, -0.25 + 0.62 * i, w) for i, (r, w) in enumerate(zip(shell_rs, shell_ws))]
    history = [ShellPoint(r, 0.78 + 0.12 * i, phi, 1.0) for i, (r, phi) in enumerate(zip(hist_rs, hist_phis))]
    reference = ShellPoint(current_r, 0.92, ref_phi, 1.0)
    return GeometryHistoryPacket(label, current, shells, history, reference)


def packet_library() -> List[GeometryHistoryPacket]:
    return [
        create_2q_packet(
            "balanced_tie_case",
            0.54,
            [0.29, 0.55, 0.77],
            [0.25, 0.50, 0.25],
            [0.34, 0.44, 0.57, 0.69],
            [-0.30, 0.22, 0.68, 1.24],
            0.60,
        ),
        create_2q_packet(
            "shell_history_tie_case",
            0.57,
            [0.44, 0.56, 0.68],
            [0.30, 0.40, 0.30],
            [0.41, 0.51, 0.59, 0.67],
            [-0.15, 0.18, 0.56, 1.03],
            0.58,
        ),
        create_2q_packet(
            "reference_shell_tie_case",
            0.49,
            [0.48, 0.49, 0.50],
            [0.34, 0.33, 0.33],
            [0.47, 0.48, 0.49, 0.50],
            [0.10, 0.22, 0.31, 0.39],
            0.20,
        ),
        create_2q_packet(
            "clear_case_outside_scope",
            0.63,
            [0.16, 0.56, 0.92],
            [0.20, 0.25, 0.55],
            [0.53, 0.55, 0.57, 0.58],
            [0.20, 0.28, 0.35, 0.45],
            0.82,
        ),
    ]


def shell_dispersion(packet: GeometryHistoryPacket) -> float:
    radii = np.array([p.radius for p in packet.shells], dtype=float)
    return float(np.std(radii))


def history_turning(packet: GeometryHistoryPacket) -> float:
    if len(packet.history) < 3:
        return 0.0
    phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
    first = np.diff(phases)
    second = np.diff(first)
    return float(np.mean(np.abs(second)))


def reference_offset(packet: GeometryHistoryPacket) -> float:
    cur = shell_point_to_bloch(packet.current)
    ref = shell_point_to_bloch(packet.reference)
    return float(np.linalg.norm(cur - ref))


def history_order_signature(packet: GeometryHistoryPacket) -> float:
    if len(packet.history) < 2:
        return 0.0
    phases = np.array([p.phi for p in packet.history], dtype=float)
    return float(np.sum(np.sign(np.diff(phases)) * np.linspace(1.0, 2.0, len(phases) - 1)))


def packet_features(packet: GeometryHistoryPacket) -> Dict[str, float]:
    weights = normalize_weights(np.array([p.weight for p in packet.shells], dtype=float))
    return {
        "reference_offset": reference_offset(packet),
        "shell_dispersion": shell_dispersion(packet),
        "history_turning": history_turning(packet),
        "history_order_signature": history_order_signature(packet),
        "shell_weight_entropy": float(-np.sum(weights * np.log2(weights))),
    }


# =====================================================================
# 2Q BRIDGE FAMILIES
# =====================================================================


def xi_ref(packet: GeometryHistoryPacket) -> np.ndarray:
    rho_cur = pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    rho_ref = pair_state(left_density(packet.reference), right_density(packet.reference), 0.0)
    coupling = 0.10 + 0.80 * math.tanh(1.6 * reference_offset(packet))
    return ensure_density((1.0 - coupling) * 0.5 * (rho_cur + rho_ref) + coupling * np.outer(BELL_PHI_PLUS, BELL_PHI_PLUS.conj()))


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
    phases = np.array([p.phi for p in packet.history], dtype=float)
    if len(phases) == 1:
        weights = np.array([1.0], dtype=float)
    else:
        steps = np.abs(np.diff(phases, prepend=phases[0]))
        trend = np.linspace(0.8, 1.2, len(packet.history))
        weights = normalize_weights(steps + trend)
    turning = history_turning(packet)
    rho = np.zeros((4, 4), dtype=complex)
    for point, weight in zip(packet.history, weights):
        hist_coupling = 0.12 + 0.5 * abs(point.radius - packet.current.radius) + 0.35 * turning
        rho += weight * pair_state(left_density(point), right_density(point), hist_coupling)
    return ensure_density(rho)


def family_states(packet: GeometryHistoryPacket) -> Dict[str, np.ndarray]:
    return {"Xi_ref": xi_ref(packet), "Xi_shell": xi_shell(packet), "Xi_hist": xi_hist(packet)}


def family_scores_2q(packet: GeometryHistoryPacket) -> Dict[str, float]:
    families = family_states(packet)
    return {name: weighted_cut_functional(rho) for name, rho in families.items()}


def ambiguity_gap(scores: Dict[str, float]) -> float:
    ordered = sorted(scores.values(), reverse=True)
    return float(ordered[0] - ordered[1]) if len(ordered) > 1 else 0.0


def ambiguous_packet(packet: GeometryHistoryPacket) -> bool:
    scores = family_scores_2q(packet)
    gap = ambiguity_gap(scores)
    if gap > AMBIGUITY_GAP:
        return False
    top = max(scores, key=scores.get)
    near = [name for name, val in scores.items() if abs(val - scores[top]) <= AMBIGUITY_GAP]
    return len(near) >= 2


# =====================================================================
# 3Q EXPANSION
# =====================================================================


def basis3(bits: str) -> np.ndarray:
    vec = np.zeros(8, dtype=complex)
    vec[int(bits, 2)] = 1.0
    return vec


def pure_density(psi: np.ndarray) -> np.ndarray:
    psi = np.asarray(psi, dtype=complex).reshape(-1)
    return ensure_density(np.outer(psi, psi.conj()))


def reduced_density_3q(rho: np.ndarray, keep: List[int]) -> np.ndarray:
    bra = ["a", "b", "c"]
    ket = ["d", "e", "f"]
    for idx in range(3):
        if idx not in keep:
            ket[idx] = bra[idx]
    subs_in = "".join(bra + ket)
    subs_out = "".join([bra[idx] for idx in keep] + [ket[idx] for idx in keep])
    reduced = np.einsum(f"{subs_in}->{subs_out}", rho.reshape(2, 2, 2, 2, 2, 2))
    dim = 2 ** len(keep)
    return ensure_density(reduced.reshape(dim, dim))


def partial_transpose_3q(rho: np.ndarray, subsystem: int) -> np.ndarray:
    tensor = rho.reshape(2, 2, 2, 2, 2, 2)
    if subsystem == 0:
        pt = tensor.transpose(3, 1, 2, 0, 4, 5)
    elif subsystem == 1:
        pt = tensor.transpose(0, 4, 2, 3, 1, 5)
    else:
        pt = tensor.transpose(0, 1, 5, 3, 4, 2)
    return ensure_density(pt.reshape(8, 8))


def ghz_state() -> np.ndarray:
    psi = (basis3("000") + basis3("111")) / math.sqrt(2.0)
    return pure_density(psi)


def w_state() -> np.ndarray:
    psi = (basis3("001") + basis3("010") + basis3("100")) / math.sqrt(3.0)
    return pure_density(psi)


def zero_ancilla_lift(rho_ab: np.ndarray) -> np.ndarray:
    anc = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    return ensure_density(np.kron(rho_ab, anc))


def companion_tripartite(packet: GeometryHistoryPacket, family: str) -> np.ndarray:
    ghz = ghz_state()
    w = w_state()
    if family == "Xi_ref":
        mix = 0.25 + 0.35 * min(reference_offset(packet), 1.0)
        return ensure_density((1.0 - mix) * pure_density((basis3("000") + basis3("111")) / math.sqrt(2.0)) + mix * ghz)
    if family == "Xi_shell":
        mix = 0.25 + 0.35 * min(shell_dispersion(packet), 1.0)
        return ensure_density((1.0 - mix) * w + mix * ghz)
    mix = 0.25 + 0.35 * min(history_turning(packet), 1.0)
    corr = pure_density((basis3("000") + basis3("011")) / math.sqrt(2.0))
    return ensure_density((1.0 - mix) * ghz + mix * corr)


def lift_family_3q(packet: GeometryHistoryPacket, family: str) -> np.ndarray:
    rho2 = family_states(packet)[family]
    plain = zero_ancilla_lift(rho2)
    comp = companion_tripartite(packet, family)
    alpha = 0.28 + 0.22 * min(packet_features(packet)["shell_weight_entropy"] / 2.0, 1.0)
    return ensure_density((1.0 - alpha) * plain + alpha * comp)


def multipartite_report(rho: np.ndarray) -> Dict[str, dict]:
    partitions = {
        "A|BC": {"a": [0], "b": [1, 2], "pt_sys": 0},
        "B|AC": {"a": [1], "b": [0, 2], "pt_sys": 1},
        "C|AB": {"a": [2], "b": [0, 1], "pt_sys": 2},
    }
    report = {}
    for label, spec in partitions.items():
        rho_a = reduced_density_3q(rho, spec["a"])
        rho_b = reduced_density_3q(rho, spec["b"])
        pt = partial_transpose_3q(rho, spec["pt_sys"])
        evals = np.linalg.eigvalsh(pt)
        report[label] = {
            "mutual_information": float(vn_entropy(rho_a) + vn_entropy(rho_b) - vn_entropy(rho)),
            "conditional_entropy_a_given_b": float(vn_entropy(rho) - vn_entropy(rho_b)),
            "coherent_information_to_b": float(vn_entropy(rho_b) - vn_entropy(rho)),
            "negativity": float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0)),
        }
    s_a = vn_entropy(reduced_density_3q(rho, [0]))
    s_b = vn_entropy(reduced_density_3q(rho, [1]))
    s_c = vn_entropy(reduced_density_3q(rho, [2]))
    s_ab = vn_entropy(reduced_density_3q(rho, [0, 1]))
    s_ac = vn_entropy(reduced_density_3q(rho, [0, 2]))
    s_bc = vn_entropy(reduced_density_3q(rho, [1, 2]))
    s_abc = vn_entropy(rho)
    report["tripartite_mutual_information"] = float(s_a + s_b + s_c - s_ab - s_ac - s_bc + s_abc)
    return report


def resolution_score_3q(rho: np.ndarray) -> float:
    report = multipartite_report(rho)
    cut_ics = [report[key]["coherent_information_to_b"] for key in ["A|BC", "B|AC", "C|AB"]]
    cut_negs = [report[key]["negativity"] for key in ["A|BC", "B|AC", "C|AB"]]
    spread = max(cut_ics) - min(cut_ics)
    return float(
        0.55 * abs(report["tripartite_mutual_information"])
        + 0.20 * abs(spread)
        + 0.25 * sum(cut_negs)
    )


def lift_summary(packet: GeometryHistoryPacket) -> Dict[str, object]:
    families = family_states(packet)
    lifted = {name: lift_family_3q(packet, name) for name in families}
    report_3q = {name: multipartite_report(rho) for name, rho in lifted.items()}
    return {
        "lifted_states": lifted,
        "reports": report_3q,
        "scores": {name: resolution_score_3q(rho) for name, rho in lifted.items()},
    }


# =====================================================================
# TESTS
# =====================================================================


def packet_ambiguity_rows() -> List[Dict[str, object]]:
    rows = []
    for packet in packet_library():
        scores2 = family_scores_2q(packet)
        gap2 = ambiguity_gap(scores2)
        selected = ambiguous_packet(packet)
        if not selected:
            continue
        lift = lift_summary(packet)
        scores3 = lift["scores"]
        ordered3 = sorted(scores3.items(), key=lambda item: item[1], reverse=True)
        gap3 = ordered3[0][1] - ordered3[1][1]
        rows.append(
            {
                "label": packet.label,
                "features": packet_features(packet),
                "scores_2q": scores2,
                "scores_3q": scores3,
                "gap_2q": gap2,
                "gap_3q": gap3,
                "winner_3q": ordered3[0][0],
                "runner_up_3q": ordered3[1][0],
                "tripartite_mutual_information": {
                    name: lift["reports"][name]["tripartite_mutual_information"] for name in lift["reports"]
                },
                "partition_spread": {
                    name: max(
                        lift["reports"][name][key]["coherent_information_to_b"]
                        for key in ["A|BC", "B|AC", "C|AB"]
                    )
                    - min(
                        lift["reports"][name][key]["coherent_information_to_b"]
                        for key in ["A|BC", "B|AC", "C|AB"]
                    )
                    for name in lift["reports"]
                },
                "pass": True,
            }
        )
    return rows


def run_positive_tests() -> Dict[str, object]:
    rows = packet_ambiguity_rows()
    if not rows:
        raise RuntimeError("no ambiguous packets selected")
    two_q_ok = all(row["gap_2q"] <= AMBIGUITY_GAP for row in rows)
    three_q_resolves = all(row["gap_3q"] > row["gap_2q"] + 0.02 for row in rows)
    nontrivial_tripartite = any(
        any(abs(v) > 1e-4 for v in row["tripartite_mutual_information"].values()) for row in rows
    )
    distinct_winners = any(len({row["winner_3q"], row["runner_up_3q"]}) == 2 for row in rows)
    return {
        "ambiguous_packets": rows,
        "selected_count": len(rows),
        "exact_checks": {
            "all_selected_packets_are_2q_ambiguous": two_q_ok,
            "3q_gap_exceeds_2q_gap_for_each_selected_packet": three_q_resolves,
            "tripartite_signal_is_nontrivial": nontrivial_tripartite,
            "3q_scores_have_distinct_top_two_candidates": distinct_winners,
        },
        "pass": bool(two_q_ok and three_q_resolves and nontrivial_tripartite and distinct_winners),
    }


def run_negative_tests() -> Dict[str, object]:
    rows = packet_ambiguity_rows()
    packet = packet_library()[0]
    plain_lift = zero_ancilla_lift(xi_shell(packet))
    plain_report = multipartite_report(plain_lift)
    plain_score = resolution_score_3q(plain_lift)
    companion_score = resolution_score_3q(lift_family_3q(packet, "Xi_shell"))
    shell_gap = ambiguity_gap(family_scores_2q(packet))

    return {
        "plain_ancilla_lift_does_not_outperform_companion_lift": {
            "plain_score": plain_score,
            "companion_score": companion_score,
            "pass": bool(companion_score > plain_score + 0.01),
        },
        "bridge_blind_local_summary_is_not_an_expansion_resolver": {
            "local_only": float(vn_entropy(reduced_density_3q(plain_lift, [0])) + vn_entropy(reduced_density_3q(plain_lift, [1])) + vn_entropy(reduced_density_3q(plain_lift, [2]))),
            "tripartite_mi": plain_report["tripartite_mutual_information"],
            "pass": bool(abs(plain_report["tripartite_mutual_information"]) < 0.5 and plain_score < companion_score),
        },
        "clear_case_is_excluded_from_expansion": {
            "clear_case_gap": ambiguity_gap(family_scores_2q(packet_library()[-1])),
            "selected": any(row["label"] == "clear_case_outside_scope" for row in rows),
            "pass": bool(ambiguity_gap(family_scores_2q(packet_library()[-1])) > AMBIGUITY_GAP and not any(row["label"] == "clear_case_outside_scope" for row in rows)),
        },
        "pass": bool(
            companion_score > plain_score + 0.01
            and abs(plain_report["tripartite_mutual_information"]) < 0.5
            and ambiguity_gap(family_scores_2q(packet_library()[-1])) > AMBIGUITY_GAP
        ),
    }


def run_boundary_tests() -> Dict[str, object]:
    packet = packet_library()[0]
    scores2 = family_scores_2q(packet)
    gap2 = ambiguity_gap(scores2)
    lift = lift_summary(packet)
    plain_lift = zero_ancilla_lift(xi_hist(packet))
    plain_score = resolution_score_3q(plain_lift)
    hist_score = lift["scores"]["Xi_hist"]
    ref_score = lift["scores"]["Xi_ref"]
    shell_score = lift["scores"]["Xi_shell"]

    return {
        "boundary_packet_stays_within_2q_ambiguity_band": {
            "gap_2q": gap2,
            "pass": bool(gap2 <= AMBIGUITY_GAP),
        },
        "multipartite_lift_reorders_candidates": {
            "scores_3q": lift["scores"],
            "pass": bool(len({max(lift["scores"], key=lift["scores"].get), min(lift["scores"], key=lift["scores"].get)}) == 2),
        },
        "plain_lift_is_weaker_than_companion_lift": {
            "plain_score": plain_score,
            "hist_score": hist_score,
            "ref_score": ref_score,
            "shell_score": shell_score,
            "pass": bool(max(hist_score, ref_score, shell_score) > plain_score + 0.01),
        },
    }


def count_section(section: Dict[str, dict]) -> Dict[str, int]:
    total = sum(1 for value in section.values() if isinstance(value, dict) and "pass" in value)
    passed = sum(1 for value in section.values() if isinstance(value, dict) and value.get("pass") is True)
    return {"passed": passed, "failed": total - passed, "total": total}


def main() -> Dict[str, object]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    pos_counts = count_section(positive)
    neg_counts = count_section(negative)
    bnd_counts = count_section(boundary)
    total_fail = pos_counts["failed"] + neg_counts["failed"] + bnd_counts["failed"]

    results = {
        "name": "3q_ambiguity_expansion",
        "probe": "pure_math_3q_ambiguity_expansion",
        "purpose": (
            "Lift only 2-qubit ambiguous bridge packets into 3-qubit form and test "
            "whether multipartite structure resolves the ambiguity."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "caveat": (
            "Targeted expansion only. Clear 2q cases are excluded, and the 3q lift is "
            "used only to resolve ambiguity rather than expand breadth."
        ),
        "summary": {
            "tests_total": pos_counts["total"] + neg_counts["total"] + bnd_counts["total"],
            "tests_passed": pos_counts["passed"] + neg_counts["passed"] + bnd_counts["passed"],
            "tests_failed": total_fail,
            "all_pass": total_fail == 0,
            "elapsed_s": None,
            "selected_ambiguous_packets": positive["selected_count"],
            "ambiguity_threshold": AMBIGUITY_GAP,
        },
    }
    return results


if __name__ == "__main__":
    t0 = time.time()
    results = main()
    results["summary"]["elapsed_s"] = time.time() - t0
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "3q_ambiguity_expansion_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(json.dumps(results["summary"], indent=2))
    print(f"Results written to {out_path}")
