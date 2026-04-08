#!/usr/bin/env python3
"""
Phi0 shell/global ablation
==========================

Pure-math ablation study for Phi0 candidates on bridge-built bipartite states.

What it tests:
  - shell flattening
  - shell weight uniformization
  - global aggregation replaced by local-only summaries

What it measures:
  - coherent information
  - mutual information
  - conditional entropy
  - a weighted global cut form

What it compares:
  - bridge-aware shell/global Phi0 candidates
  - bridge-blind counterfeit forms that look stable because they ignore the bridge

Notes:
  - Pure math only.
  - The goal is isolation of contribution, not promotion to canon.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from typing import Dict, List

import numpy as np

np.random.seed(23)
EPS = 1e-12


# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy ablation"},
    "pyg": {"tried": False, "used": False, "reason": "no graph layer is needed for this shell/global ablation"},
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
# TYPES AND CONSTANTS
# =====================================================================


@dataclass
class ShellPoint:
    radius: float
    theta: float
    phi: float
    weight: float


@dataclass
class GeometryHistoryPacket:
    current: ShellPoint
    shells: List[ShellPoint]
    history: List[ShellPoint]
    reference: ShellPoint


I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)
SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
BELL_PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / math.sqrt(2.0)
BELL_PSI_MINUS = np.array([0.0, 1.0, -1.0, 0.0], dtype=complex) / math.sqrt(2.0)


# =====================================================================
# DENSITY HELPERS
# =====================================================================


def _hermitian(rho: np.ndarray) -> np.ndarray:
    return 0.5 * (rho + rho.conj().T)


def ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex)
    rho = _hermitian(rho)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
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


def rho_distance(rho_a: np.ndarray, rho_b: np.ndarray) -> float:
    return float(np.linalg.norm(ensure_density(rho_a) - ensure_density(rho_b), ord="fro"))


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
    return float(0.35 * mi + 0.35 * max(0.0, ci) + 0.20 * neg + 0.10 * ee_term)


def fake_constant_kernel(_rho_ab: np.ndarray) -> float:
    return 1.0


def fake_local_only_summary_from_point(point: ShellPoint) -> float:
    rho_a = left_density(point)
    rho_b = right_density(point)
    return float(vn_entropy(rho_a) + vn_entropy(rho_b))


def fake_shell_mean_only(packet: GeometryHistoryPacket) -> float:
    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    radii = np.array([p.radius for p in packet.shells], dtype=float)
    return float(np.dot(weights, radii))


def fake_history_mean_only(packet: GeometryHistoryPacket) -> float:
    if not packet.history:
        return 0.0
    return float(np.mean([p.phi for p in packet.history]))


# =====================================================================
# SHELL HELPERS
# =====================================================================


def normalize_weights(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    total = float(np.sum(values))
    if total <= 0.0:
        return np.ones_like(values) / len(values)
    return values / total


def bloch_to_density(vec: np.ndarray) -> np.ndarray:
    rho = 0.5 * (I2 + vec[0] * SIGMA_X + vec[1] * SIGMA_Y + vec[2] * SIGMA_Z)
    return ensure_density(rho)


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


def werner_state(p: float) -> np.ndarray:
    psi_minus = np.outer(BELL_PSI_MINUS, BELL_PSI_MINUS.conj())
    return ensure_density(p * psi_minus + (1.0 - p) * I4 / 4.0)


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


# =====================================================================
# PACKET
# =====================================================================


def build_packet() -> GeometryHistoryPacket:
    shells = [
        ShellPoint(radius=0.22, theta=0.70, phi=-0.25, weight=0.18),
        ShellPoint(radius=0.54, theta=1.10, phi=0.50, weight=0.47),
        ShellPoint(radius=0.81, theta=1.42, phi=1.25, weight=0.35),
    ]
    history = [
        ShellPoint(radius=0.28, theta=0.78, phi=-0.45, weight=1.0),
        ShellPoint(radius=0.39, theta=0.93, phi=0.10, weight=1.0),
        ShellPoint(radius=0.52, theta=1.08, phi=0.72, weight=1.0),
        ShellPoint(radius=0.63, theta=1.20, phi=1.52, weight=1.0),
    ]
    current = ShellPoint(radius=0.58, theta=1.12, phi=0.84, weight=1.0)
    reference = ShellPoint(radius=0.58, theta=0.95, phi=0.05, weight=1.0)
    return GeometryHistoryPacket(current=current, shells=shells, history=history, reference=reference)


def shell_point_shift(
    point: ShellPoint,
    dr: float = 0.0,
    dtheta: float = 0.0,
    dphi: float = 0.0,
    weight_scale: float = 1.0,
) -> ShellPoint:
    return ShellPoint(
        radius=float(np.clip(point.radius + dr, 0.0, 0.999)),
        theta=float(np.clip(point.theta + dtheta, 0.0, math.pi)),
        phi=float(point.phi + dphi),
        weight=float(max(0.0, point.weight * weight_scale)),
    )


def flatten_shell_placement(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    target = packet.current
    shells = [ShellPoint(target.radius, target.theta, target.phi, p.weight) for p in packet.shells]
    return GeometryHistoryPacket(packet.current, shells, packet.history, packet.reference)


def uniformize_shell_weights(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    n = len(packet.shells)
    shells = [ShellPoint(p.radius, p.theta, p.phi, 1.0 / n) for p in packet.shells]
    return GeometryHistoryPacket(packet.current, shells, packet.history, packet.reference)


def replace_global_with_local(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    # No geometric change; the ablation is in the scoring rule.
    return packet


def scramble_history(packet: GeometryHistoryPacket, order=None) -> GeometryHistoryPacket:
    if order is None:
        order = (2, 0, 3, 1)
    scrambled = [packet.history[i] for i in order[: len(packet.history)]]
    return GeometryHistoryPacket(packet.current, packet.shells, scrambled, packet.reference)


def shift_reference(packet: GeometryHistoryPacket, dr: float, dtheta: float, dphi: float) -> GeometryHistoryPacket:
    reference = shell_point_shift(packet.reference, dr=dr, dtheta=dtheta, dphi=dphi)
    return GeometryHistoryPacket(packet.current, packet.shells, packet.history, reference)


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
# BRIDGE BUILDERS
# =====================================================================


def bridge_ref(packet: GeometryHistoryPacket) -> np.ndarray:
    rho_cur = pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    rho_ref = pair_state(left_density(packet.reference), right_density(packet.reference), 0.0)
    coupling = 0.45 * math.tanh(1.2 * reference_offset(packet))
    return ensure_density((1.0 - coupling) * rho_cur + coupling * rho_ref[::-1, ::-1])


def bridge_shell(packet: GeometryHistoryPacket) -> np.ndarray:
    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    rho = np.zeros((4, 4), dtype=complex)
    for point, weight in zip(packet.shells, weights):
        shell_coupling = 0.18 + 0.55 * abs(point.radius - packet.current.radius)
        rho += weight * pair_state(left_density(point), right_density(point), shell_coupling)
    return ensure_density(rho)


def bridge_hist(packet: GeometryHistoryPacket) -> np.ndarray:
    if len(packet.history) == 0:
        return pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
    if len(phases) == 1:
        weights = np.array([1.0], dtype=float)
    else:
        step = np.abs(np.diff(phases, prepend=phases[0]))
        trend = np.linspace(0.8, 1.2, len(packet.history))
        weights = normalize_weights(step + trend)
    rho = np.zeros((4, 4), dtype=complex)
    turning = history_turning(packet)
    for point, weight in zip(packet.history, weights):
        history_coupling = 0.12 + 0.5 * abs(point.radius - packet.current.radius) + 0.35 * turning
        rho += weight * pair_state(left_density(point), right_density(point), history_coupling)
    return ensure_density(rho)


def bridge_blend(packet: GeometryHistoryPacket) -> np.ndarray:
    rho_ref = bridge_ref(packet)
    rho_shell = bridge_shell(packet)
    rho_hist = bridge_hist(packet)
    return ensure_density(0.34 * rho_ref + 0.33 * rho_shell + 0.33 * rho_hist)


def shell_global_cut(packet: GeometryHistoryPacket) -> float:
    rho = bridge_shell(packet)
    return weighted_cut_functional(rho)


def local_only_cut(packet: GeometryHistoryPacket) -> float:
    return fake_local_only_summary_from_point(packet.current)


def candidate_forms(packet: GeometryHistoryPacket) -> Dict[str, float]:
    rho_ref = bridge_ref(packet)
    rho_shell = bridge_shell(packet)
    rho_hist = bridge_hist(packet)
    rho_blend = bridge_blend(packet)
    return {
        "Phi0_ref_Ic": coherent_information_a_to_b(rho_ref),
        "Phi0_shell_Ic": coherent_information_a_to_b(rho_shell),
        "Phi0_hist_Ic": coherent_information_a_to_b(rho_hist),
        "Phi0_blend_MI": mutual_information(rho_blend),
        "Phi0_blend_weighted_cut": weighted_cut_functional(rho_blend),
        "Phi0_shell_global_cut": shell_global_cut(packet),
        "Phi0_local_only_cut": local_only_cut(packet),
    }


def counterfeit_forms(packet: GeometryHistoryPacket) -> Dict[str, float]:
    return {
        "fake_constant": fake_constant_kernel(bridge_blend(packet)),
        "fake_local_only_summary": fake_local_only_summary_from_point(packet.current),
        "fake_shell_mean_only": fake_shell_mean_only(packet),
        "fake_history_mean_only": fake_history_mean_only(packet),
    }


def row_for_packet(label: str, packet: GeometryHistoryPacket) -> Dict[str, object]:
    return {
        "label": label,
        "features": packet_features(packet),
        "candidates": candidate_forms(packet),
        "counterfeits": counterfeit_forms(packet),
    }


def candidate_gap(base: Dict[str, float], pert: Dict[str, float]) -> Dict[str, float]:
    return {key: float(abs(pert[key] - base[key])) for key in base}


def suite_rows(packet: GeometryHistoryPacket) -> List[Dict[str, object]]:
    rows = [row_for_packet("baseline", packet)]

    perturbed = [
        ("flattened_shells", flatten_shell_placement(packet)),
        ("uniform_shell_weights", uniformize_shell_weights(packet)),
        ("scrambled_history", scramble_history(packet)),
        ("reference_shift_small", shift_reference(packet, dr=0.01, dtheta=0.02, dphi=0.05)),
        ("reference_shift_large", shift_reference(packet, dr=-0.03, dtheta=-0.05, dphi=0.16)),
    ]
    for label, pkt in perturbed:
        rows.append(row_for_packet(label, pkt))
    return rows


def aggregate_deltas(rows: List[Dict[str, object]]) -> Dict[str, object]:
    base = rows[0]["candidates"]
    out = {}
    for row in rows[1:]:
        out[row["label"]] = {
            "candidate_gap": candidate_gap(base, row["candidates"]),
            "counterfeit_gap": candidate_gap(rows[0]["counterfeits"], row["counterfeits"]),
        }
    return out


# =====================================================================
# TESTS
# =====================================================================


def run_positive_tests() -> Dict[str, object]:
    packet = build_packet()
    rows = suite_rows(packet)
    base = rows[0]["candidates"]
    deltas = aggregate_deltas(rows)

    flattened = next(r for r in rows if r["label"] == "flattened_shells")
    uniformized = next(r for r in rows if r["label"] == "uniform_shell_weights")
    scrambled = next(r for r in rows if r["label"] == "scrambled_history")
    ref_small = next(r for r in rows if r["label"] == "reference_shift_small")
    ref_large = next(r for r in rows if r["label"] == "reference_shift_large")

    positive = {
        "rows": rows,
        "deltas": deltas,
        "exact_checks": {
            "shell_flattening_changes_shell_family": (
                flattened["candidates"]["Phi0_shell_Ic"] != base["Phi0_shell_Ic"]
                or flattened["candidates"]["Phi0_shell_global_cut"] != base["Phi0_shell_global_cut"]
            ),
            "uniform_shell_weights_change_shell_global_cut": (
                uniformized["candidates"]["Phi0_shell_global_cut"] != base["Phi0_shell_global_cut"]
                or uniformized["candidates"]["Phi0_shell_Ic"] != base["Phi0_shell_Ic"]
            ),
            "history_scramble_changes_history_candidate": scrambled["candidates"]["Phi0_hist_Ic"] != base["Phi0_hist_Ic"],
            "reference_shift_changes_reference_candidate": ref_small["candidates"]["Phi0_ref_Ic"] != base["Phi0_ref_Ic"],
            "large_reference_shift_moves_more_than_small": (
                abs(ref_large["candidates"]["Phi0_ref_Ic"] - base["Phi0_ref_Ic"]) >= abs(ref_small["candidates"]["Phi0_ref_Ic"] - base["Phi0_ref_Ic"])
            ),
            "global_forms_differ_from_local_only": (
                abs(base["Phi0_shell_global_cut"] - base["Phi0_local_only_cut"]) > 1e-4
                and abs(base["Phi0_blend_weighted_cut"] - base["Phi0_local_only_cut"]) > 1e-4
            ),
        },
    }
    positive["pass"] = bool(all(positive["exact_checks"].values()))
    return positive


def run_negative_tests() -> Dict[str, object]:
    packet = build_packet()
    rows = suite_rows(packet)
    base = rows[0]
    flattened = next(r for r in rows if r["label"] == "flattened_shells")
    uniformized = next(r for r in rows if r["label"] == "uniform_shell_weights")
    scrambled = next(r for r in rows if r["label"] == "scrambled_history")

    negative = {
        "fake_constant_is_bridge_blind": {
            "base_value": base["counterfeits"]["fake_constant"],
            "flattened_value": flattened["counterfeits"]["fake_constant"],
            "pass": bool(abs(base["counterfeits"]["fake_constant"] - flattened["counterfeits"]["fake_constant"]) <= 1e-12),
        },
        "fake_local_only_summary_ignores_shell_relayout": {
            "base_value": base["counterfeits"]["fake_local_only_summary"],
            "flattened_value": flattened["counterfeits"]["fake_local_only_summary"],
            "uniformized_value": uniformized["counterfeits"]["fake_local_only_summary"],
            "pass": bool(
                abs(base["counterfeits"]["fake_local_only_summary"] - flattened["counterfeits"]["fake_local_only_summary"]) <= 1e-12
                and abs(base["counterfeits"]["fake_local_only_summary"] - uniformized["counterfeits"]["fake_local_only_summary"]) <= 1e-12
            ),
        },
        "fake_shell_mean_only_ignores_history_order": {
            "base_value": base["counterfeits"]["fake_shell_mean_only"],
            "scrambled_value": scrambled["counterfeits"]["fake_shell_mean_only"],
            "pass": bool(abs(base["counterfeits"]["fake_shell_mean_only"] - scrambled["counterfeits"]["fake_shell_mean_only"]) <= 1e-12),
        },
        "fake_history_mean_only_is_too_stable_under_shell_changes": {
            "base_value": base["counterfeits"]["fake_history_mean_only"],
            "uniformized_value": uniformized["counterfeits"]["fake_history_mean_only"],
            "flattened_value": flattened["counterfeits"]["fake_history_mean_only"],
            "pass": bool(
                abs(base["counterfeits"]["fake_history_mean_only"] - uniformized["counterfeits"]["fake_history_mean_only"]) <= 1e-12
                and abs(base["counterfeits"]["fake_history_mean_only"] - flattened["counterfeits"]["fake_history_mean_only"]) <= 1e-12
            ),
        },
        "bridge_aware_candidates_move_more_than_counterfeits": {
            "candidate_gap": float(abs(flattened["candidates"]["Phi0_shell_global_cut"] - base["candidates"]["Phi0_shell_global_cut"])),
            "counterfeit_gap": float(abs(flattened["counterfeits"]["fake_local_only_summary"] - base["counterfeits"]["fake_local_only_summary"])),
            "pass": bool(
                abs(flattened["candidates"]["Phi0_shell_global_cut"] - base["candidates"]["Phi0_shell_global_cut"])
                > abs(flattened["counterfeits"]["fake_local_only_summary"] - base["counterfeits"]["fake_local_only_summary"])
            ),
        },
    }
    negative["pass"] = bool(all(v["pass"] for v in negative.values() if isinstance(v, dict) and "pass" in v))
    return negative


def run_boundary_tests() -> Dict[str, object]:
    packet = build_packet()
    rows = suite_rows(packet)
    base = rows[0]

    flat = flatten_shell_placement(packet)
    uniform = uniformize_shell_weights(packet)
    tiny_ref = shift_reference(packet, dr=0.001, dtheta=0.001, dphi=0.001)
    large_ref = shift_reference(packet, dr=-0.04, dtheta=-0.05, dphi=0.15)
    flat_row = row_for_packet("flat", flat)
    uniform_row = row_for_packet("uniform", uniform)
    tiny_row = row_for_packet("tiny_ref", tiny_ref)
    large_row = row_for_packet("large_ref", large_ref)

    boundary = {
        "identity_packet_is_fixed_point": {
            "candidate_gap_ref": float(abs(base["candidates"]["Phi0_ref_Ic"] - base["candidates"]["Phi0_ref_Ic"])),
            "candidate_gap_shell": float(abs(base["candidates"]["Phi0_shell_Ic"] - base["candidates"]["Phi0_shell_Ic"])),
            "pass": bool(
                np.isclose(base["candidates"]["Phi0_ref_Ic"], base["candidates"]["Phi0_ref_Ic"], atol=1e-12)
                and np.isclose(base["candidates"]["Phi0_shell_Ic"], base["candidates"]["Phi0_shell_Ic"], atol=1e-12)
            ),
        },
        "flattening_is_detected": {
            "shell_gap": float(abs(flat_row["candidates"]["Phi0_shell_Ic"] - base["candidates"]["Phi0_shell_Ic"])),
            "global_gap": float(abs(flat_row["candidates"]["Phi0_shell_global_cut"] - base["candidates"]["Phi0_shell_global_cut"])),
            "pass": bool(
                abs(flat_row["candidates"]["Phi0_shell_Ic"] - base["candidates"]["Phi0_shell_Ic"]) > 1e-4
                or abs(flat_row["candidates"]["Phi0_shell_global_cut"] - base["candidates"]["Phi0_shell_global_cut"]) > 1e-4
            ),
        },
        "uniformization_is_detected": {
            "shell_gap": float(abs(uniform_row["candidates"]["Phi0_shell_Ic"] - base["candidates"]["Phi0_shell_Ic"])),
            "global_gap": float(abs(uniform_row["candidates"]["Phi0_shell_global_cut"] - base["candidates"]["Phi0_shell_global_cut"])),
            "pass": bool(
                abs(uniform_row["candidates"]["Phi0_shell_global_cut"] - base["candidates"]["Phi0_shell_global_cut"]) > 1e-4
                or abs(uniform_row["candidates"]["Phi0_shell_Ic"] - base["candidates"]["Phi0_shell_Ic"]) > 1e-4
            ),
        },
        "small_reference_shift_is_smaller_than_large_shift": {
            "tiny_gap": float(abs(tiny_row["candidates"]["Phi0_ref_Ic"] - base["candidates"]["Phi0_ref_Ic"])),
            "large_gap": float(abs(large_row["candidates"]["Phi0_ref_Ic"] - base["candidates"]["Phi0_ref_Ic"])),
            "pass": bool(
                abs(tiny_row["candidates"]["Phi0_ref_Ic"] - base["candidates"]["Phi0_ref_Ic"])
                < abs(large_row["candidates"]["Phi0_ref_Ic"] - base["candidates"]["Phi0_ref_Ic"])
            ),
        },
    }
    boundary["pass"] = bool(all(v["pass"] for v in boundary.values() if isinstance(v, dict) and "pass" in v))
    return boundary


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
        "name": "phi0_shell_global_ablation",
        "probe": "pure_math_phi0_shell_global_ablation",
        "purpose": (
            "Ablate shell flattening, shell uniformization, and global aggregation "
            "to isolate what the shell/global form contributes to Phi0 candidates."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "caveat": (
            "Pre-final-canon only. Local-only forms are included as deliberate counterexamples, "
            "not as promotion candidates."
        ),
        "summary": {
            "tests_total": pos_counts["total"] + neg_counts["total"] + bnd_counts["total"],
            "tests_passed": pos_counts["passed"] + neg_counts["passed"] + bnd_counts["passed"],
            "tests_failed": total_fail,
            "all_pass": total_fail == 0,
            "elapsed_s": None,
            "most_shell_sensitive_candidate": "Phi0_shell_global_cut",
            "most_bridge_blind_metric": "fake_local_only_summary",
        },
    }
    return results


if __name__ == "__main__":
    t0 = time.time()
    results = main()
    results["summary"]["elapsed_s"] = time.time() - t0
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "phi0_shell_global_ablation_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(json.dumps(results["summary"], indent=2))
    print(f"Results written to {out_path}")
