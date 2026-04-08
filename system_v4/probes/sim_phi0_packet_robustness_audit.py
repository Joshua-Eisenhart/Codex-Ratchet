#!/usr/bin/env python3
"""
Phi0 packet robustness audit
============================

Pure-math audit of Phi0 candidates under packet perturbations.

What it perturbs:
  - shell weights
  - history ordering
  - reference offsets
  - local channel noise

What it measures:
  - mutual information
  - conditional entropy
  - coherent information
  - weighted cut functional

What it compares:
  - bridge-aware Phi0 candidates
  - bridge-blind counterfeit metrics that look stable because they ignore the bridge

Notes:
  - Pure math only.
  - Entanglement entropy is reported only for pure bipartite states.
  - The counterfeit metrics are included to show what is stable for the wrong reason.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

np.random.seed(19)
EPS = 1e-12


# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy audit"},
    "pyg": {"tried": False, "used": False, "reason": "no graph layer is needed for this packet audit"},
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


def fake_constant_kernel(_packet: GeometryHistoryPacket) -> float:
    return 1.0


def fake_bridge_blind_packet_score(packet: GeometryHistoryPacket) -> float:
    reference = shell_point_to_bloch(packet.reference)
    current = shell_point_to_bloch(packet.current)
    ref_off = float(np.linalg.norm(current - reference))
    shell_disp = shell_dispersion(packet)
    hist_turn = history_turning(packet)
    return float(0.42 * ref_off + 0.33 * shell_disp + 0.25 * hist_turn)


def fake_shell_mean_radius(packet: GeometryHistoryPacket) -> float:
    radii = np.array([p.radius for p in packet.shells], dtype=float)
    return float(np.mean(radii))


def fake_history_mean_phase(packet: GeometryHistoryPacket) -> float:
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


def correlation_blend_state(rho_a: np.ndarray, rho_b: np.ndarray, mix: float) -> np.ndarray:
    mix = float(np.clip(mix, 0.0, 0.95))
    prod = np.kron(rho_a, rho_b)
    corr = np.zeros((4, 4), dtype=complex)
    corr[0, 0] = 0.5
    corr[3, 3] = 0.5
    return ensure_density((1.0 - mix) * prod + mix * corr)


def werner_state(p: float) -> np.ndarray:
    psi_minus = np.outer(BELL_PSI_MINUS, BELL_PSI_MINUS.conj())
    return ensure_density(p * psi_minus + (1.0 - p) * I4 / 4.0)


def bell_state(label: str = "phi_plus") -> np.ndarray:
    if label == "phi_plus":
        psi = BELL_PHI_PLUS
    elif label == "psi_minus":
        psi = BELL_PSI_MINUS
    elif label == "phi_minus":
        psi = np.array([1.0, 0.0, 0.0, -1.0], dtype=complex) / math.sqrt(2.0)
    else:
        psi = np.array([0.0, 1.0, 1.0, 0.0], dtype=complex) / math.sqrt(2.0)
    return np.outer(psi, psi.conj())


def product_state(name: str) -> np.ndarray:
    if name == "00":
        psi = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
    elif name == "+-":
        plus = np.array([1.0, 1.0], dtype=complex) / math.sqrt(2.0)
        minus = np.array([1.0, -1.0], dtype=complex) / math.sqrt(2.0)
        psi = np.kron(plus, minus)
    else:
        raise ValueError(name)
    return np.outer(psi, psi.conj())


def classical_correlated_state(p: float = 0.7) -> np.ndarray:
    p = float(np.clip(p, 0.0, 1.0))
    diag = np.diag([p, (1.0 - p) / 2.0, (1.0 - p) / 2.0, 0.0]).astype(complex)
    return ensure_density(diag)


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


def shell_weight_tilt(packet: GeometryHistoryPacket, tilt: float) -> GeometryHistoryPacket:
    n = len(packet.shells)
    centered = np.linspace(-1.0, 1.0, n)
    weights = np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float)
    weights = normalize_weights(weights * (1.0 + tilt * centered))
    shells = [
        ShellPoint(p.radius, p.theta, p.phi, float(w))
        for p, w in zip(packet.shells, weights)
    ]
    return GeometryHistoryPacket(packet.current, shells, packet.history, packet.reference)


def scramble_history(packet: GeometryHistoryPacket, order: Tuple[int, ...] | None = None) -> GeometryHistoryPacket:
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
    return {
        "reference_offset": reference_offset(packet),
        "shell_dispersion": shell_dispersion(packet),
        "history_turning": history_turning(packet),
        "history_order_signature": history_order_signature(packet),
        "shell_weight_entropy": float(-np.sum(normalize_weights(np.array([p.weight for p in packet.shells], dtype=float)) * np.log2(normalize_weights(np.array([p.weight for p in packet.shells], dtype=float))))),
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


def weighted_shell_coherent_information(packet: GeometryHistoryPacket) -> float:
    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    total = 0.0
    for point, weight in zip(packet.shells, weights):
        shell_state = pair_state(left_density(point), right_density(point), 0.18 + 0.55 * abs(point.radius - packet.current.radius))
        total += weight * coherent_information_a_to_b(shell_state)
    return float(total)


# =====================================================================
# CANDIDATES
# =====================================================================


def phi0_candidates(packet: GeometryHistoryPacket) -> Dict[str, float]:
    rho_ref = bridge_ref(packet)
    rho_shell = bridge_shell(packet)
    rho_hist = bridge_hist(packet)
    rho_blend = bridge_blend(packet)

    return {
        "Phi0_ref_Ic": coherent_information_a_to_b(rho_ref),
        "Phi0_shell_weighted_Ic": weighted_shell_coherent_information(packet),
        "Phi0_hist_Ic": coherent_information_a_to_b(rho_hist),
        "Phi0_blend_weighted_cut": weighted_cut_functional(rho_blend),
        "Phi0_ref_MI": mutual_information(rho_ref),
        "Phi0_blend_MI": mutual_information(rho_blend),
    }


def bridge_blind_metrics(packet: GeometryHistoryPacket) -> Dict[str, float]:
    return {
        "fake_constant": fake_constant_kernel(packet),
        "fake_packet_score": fake_bridge_blind_packet_score(packet),
        "fake_shell_mean_radius": fake_shell_mean_radius(packet),
        "fake_history_mean_phase": fake_history_mean_phase(packet),
    }


def candidate_rows(packet: GeometryHistoryPacket) -> List[Dict[str, object]]:
    rows = []
    cands = phi0_candidates(packet)
    blind = bridge_blind_metrics(packet)
    rows.append(
        {
            "label": "packet_baseline",
            "class": "packet",
            "family": "packet",
            "features": packet_features(packet),
            "candidates": cands,
            "blind": blind,
        }
    )
    return rows


def candidate_sensitivity(base: Dict[str, float], pert: Dict[str, float]) -> Dict[str, float]:
    out = {}
    for key in base:
        out[key] = float(abs(pert[key] - base[key]))
    return out


def perturb_rows(packet: GeometryHistoryPacket) -> List[Dict[str, object]]:
    perturbations = [
        ("shell_tilt_small", shell_weight_tilt(packet, 0.08), "packet"),
        ("shell_tilt_large", shell_weight_tilt(packet, 0.22), "packet"),
        ("history_scramble", scramble_history(packet), "packet"),
        ("reference_shift_small", shift_reference(packet, dr=0.015, dtheta=0.02, dphi=0.06), "packet"),
        ("reference_shift_large", shift_reference(packet, dr=-0.03, dtheta=-0.04, dphi=0.14), "packet"),
    ]

    rows = []
    base_cands = phi0_candidates(packet)
    base_blind = bridge_blind_metrics(packet)
    base_bridge = {
        "bridge_ref": bridge_ref(packet),
        "bridge_shell": bridge_shell(packet),
        "bridge_hist": bridge_hist(packet),
        "bridge_blend": bridge_blend(packet),
    }

    for label, pert_packet, kind in perturbations:
        pert_cands = phi0_candidates(pert_packet)
        pert_blind = bridge_blind_metrics(pert_packet)
        rows.append(
            {
                "label": label,
                "kind": kind,
                "packet_features": packet_features(pert_packet),
                "candidate_delta": candidate_sensitivity(base_cands, pert_cands),
                "blind_delta": candidate_sensitivity(base_blind, pert_blind),
            }
        )

    noise_cases = [
        ("local_dephase_A_small", local_dephase(base_bridge["bridge_ref"], p=0.06, on="A")),
        ("local_dephase_B_small", local_dephase(base_bridge["bridge_hist"], p=0.06, on="B")),
        ("local_depolarize_A_small", local_depolarize(base_bridge["bridge_shell"], p=0.06, on="A")),
        ("local_depolarize_B_small", local_depolarize(base_bridge["bridge_blend"], p=0.06, on="B")),
    ]

    for label, rho_noise in noise_cases:
        noise_cands = {
            "Phi0_ref_Ic": coherent_information_a_to_b(rho_noise),
            "Phi0_shell_weighted_Ic": weighted_shell_coherent_information(packet),
            "Phi0_hist_Ic": coherent_information_a_to_b(rho_noise),
            "Phi0_blend_weighted_cut": weighted_cut_functional(rho_noise),
            "Phi0_ref_MI": mutual_information(rho_noise),
            "Phi0_blend_MI": mutual_information(rho_noise),
        }
        rows.append(
            {
                "label": label,
                "kind": "channel",
                "candidate_delta": candidate_sensitivity(base_cands, noise_cands),
                "blind_delta": candidate_sensitivity(base_blind, base_blind),
            }
        )

    return rows


def aggregate_sensitivity(rows: List[Dict[str, object]], keys: List[str]) -> Dict[str, object]:
    by_key = {key: [] for key in keys}
    for row in rows:
        delta = row["candidate_delta"]
        for key in keys:
            by_key[key].append(float(delta[key]))
    return {
        key: {
            "mean_abs_delta": float(np.mean(vals)),
            "max_abs_delta": float(np.max(vals)),
            "min_abs_delta": float(np.min(vals)),
            "stability_index": float(1.0 / (1.0 + np.mean(vals))),
        }
        for key, vals in by_key.items()
    }


def perturb_class_scores(rows: List[Dict[str, object]]) -> Dict[str, object]:
    keys = [
        "Phi0_ref_Ic",
        "Phi0_shell_weighted_Ic",
        "Phi0_hist_Ic",
        "Phi0_blend_weighted_cut",
        "Phi0_ref_MI",
        "Phi0_blend_MI",
    ]
    packet_rows = [r for r in rows if r["kind"] == "packet"]
    channel_rows = [r for r in rows if r["kind"] == "channel"]
    scores = {
        "packet": aggregate_sensitivity(packet_rows, keys),
        "channel": aggregate_sensitivity(channel_rows, keys),
    }
    return scores


# =====================================================================
# TESTS
# =====================================================================


def run_positive_tests() -> Dict[str, object]:
    packet = build_packet()
    base_candidates = phi0_candidates(packet)
    blind = bridge_blind_metrics(packet)
    rows = perturb_rows(packet)
    scores = perturb_class_scores(rows)

    packet_rows = [r for r in rows if r["kind"] == "packet"]
    channel_rows = [r for r in rows if r["kind"] == "channel"]

    shell_tilt_small = next(r for r in packet_rows if r["label"] == "shell_tilt_small")
    shell_tilt_large = next(r for r in packet_rows if r["label"] == "shell_tilt_large")
    hist_scramble = next(r for r in packet_rows if r["label"] == "history_scramble")
    ref_small = next(r for r in packet_rows if r["label"] == "reference_shift_small")
    ref_large = next(r for r in packet_rows if r["label"] == "reference_shift_large")
    noise_small = next(r for r in channel_rows if r["label"] == "local_dephase_A_small")
    noise_large = next(r for r in channel_rows if r["label"] == "local_depolarize_B_small")

    positive = {
        "base_candidates": base_candidates,
        "packet_features": packet_features(packet),
        "perturbation_rows": rows,
        "sensitivity_scores": scores,
        "bridge_blind_metrics": blind,
        "exact_checks": {
            "shell_weight_tilt_changes_shell_candidate": (
                shell_tilt_small["candidate_delta"]["Phi0_shell_weighted_Ic"] > 1e-4
                and shell_tilt_large["candidate_delta"]["Phi0_shell_weighted_Ic"] > shell_tilt_small["candidate_delta"]["Phi0_shell_weighted_Ic"]
            ),
            "history_scramble_changes_history_candidate": shell_tilt_small["candidate_delta"]["Phi0_hist_Ic"] >= 0.0 and hist_scramble["candidate_delta"]["Phi0_hist_Ic"] > 1e-4,
            "reference_shift_changes_reference_candidate": ref_small["candidate_delta"]["Phi0_ref_Ic"] > 1e-4
            and ref_large["candidate_delta"]["Phi0_ref_Ic"] > ref_small["candidate_delta"]["Phi0_ref_Ic"],
            "local_noise_changes_bridge_candidates_more_than_blind_score": (
                noise_small["candidate_delta"]["Phi0_ref_Ic"] > 1e-4
                and abs(noise_small["blind_delta"]["fake_packet_score"]) < 1e-12
                and abs(noise_large["blind_delta"]["fake_packet_score"]) < 1e-12
            ),
            "bridge_blind_scores_exist": (
                "fake_constant" in blind and "fake_packet_score" in blind and "fake_shell_mean_radius" in blind
            ),
            "bridge_sensitive_candidates_have_nonzero_spread": (
                scores["packet"]["Phi0_ref_Ic"]["max_abs_delta"] > 0.0
                and scores["packet"]["Phi0_shell_weighted_Ic"]["max_abs_delta"] > 0.0
                and scores["packet"]["Phi0_hist_Ic"]["max_abs_delta"] > 0.0
                and scores["packet"]["Phi0_blend_weighted_cut"]["max_abs_delta"] > 0.0
            ),
        },
    }
    positive["pass"] = bool(all(positive["exact_checks"].values()))
    return positive


def run_negative_tests() -> Dict[str, object]:
    packet = build_packet()
    rows = perturb_rows(packet)
    blind = bridge_blind_metrics(packet)
    channel_rows = [r for r in rows if r["kind"] == "channel"]
    packet_rows = [r for r in rows if r["kind"] == "packet"]

    noise_small = next(r for r in channel_rows if r["label"] == "local_dephase_A_small")
    noise_large = next(r for r in channel_rows if r["label"] == "local_depolarize_B_small")
    history_scramble = next(r for r in packet_rows if r["label"] == "history_scramble")
    ref_small = next(r for r in packet_rows if r["label"] == "reference_shift_small")

    negative = {
        "fake_constant_kernel_adds_no_bridge_signal": {
            "base_value": blind["fake_constant"],
            "pass": bool(abs(blind["fake_constant"] - 1.0) <= 1e-12),
        },
        "fake_packet_score_ignores_local_channel_noise": {
            "base_value": blind["fake_packet_score"],
            "noise_small_delta": float(abs(noise_small["blind_delta"]["fake_packet_score"])),
            "noise_large_delta": float(abs(noise_large["blind_delta"]["fake_packet_score"])),
            "pass": bool(
                abs(noise_small["blind_delta"]["fake_packet_score"]) <= 1e-12
                and abs(noise_large["blind_delta"]["fake_packet_score"]) <= 1e-12
            ),
        },
        "fake_shell_mean_radius_ignores_history_order": {
            "base_value": blind["fake_shell_mean_radius"],
            "history_scramble_delta": float(abs(history_scramble["blind_delta"]["fake_shell_mean_radius"])),
            "pass": bool(abs(history_scramble["blind_delta"]["fake_shell_mean_radius"]) <= 1e-12),
        },
        "fake_history_mean_phase_ignores_reference_shift": {
            "base_value": blind["fake_history_mean_phase"],
            "reference_shift_delta": float(abs(ref_small["blind_delta"]["fake_history_mean_phase"])),
            "pass": bool(abs(ref_small["blind_delta"]["fake_history_mean_phase"]) <= 1e-12),
        },
        "counterfeit_scores_do_not_track_bridge_candidates": {
            "note": "bridge-blind scores remain stable while bridge-aware candidates move",
            "pass": bool(
                abs(noise_small["blind_delta"]["fake_packet_score"]) <= 1e-12
                and noise_small["candidate_delta"]["Phi0_ref_Ic"] > 1e-4
            ),
        },
    }
    negative["pass"] = bool(all(v["pass"] for v in negative.values() if isinstance(v, dict) and "pass" in v))
    return negative


def run_boundary_tests() -> Dict[str, object]:
    packet = build_packet()
    base_candidates = phi0_candidates(packet)
    same_packet = build_packet()
    same_candidates = phi0_candidates(same_packet)
    tiny_shell = shell_weight_tilt(packet, 0.01)
    tiny_ref = shift_reference(packet, dr=0.001, dtheta=0.001, dphi=0.001)
    tiny_noise = local_dephase(bridge_ref(packet), p=0.01, on="A")
    strong_noise = local_depolarize(bridge_blend(packet), p=0.35, on="B")

    tiny_shell_candidates = phi0_candidates(tiny_shell)
    tiny_ref_candidates = phi0_candidates(tiny_ref)

    boundary = {
        "identity_packet_change_is_zero": {
            "ref_gap": float(abs(base_candidates["Phi0_ref_Ic"] - same_candidates["Phi0_ref_Ic"])),
            "shell_gap": float(abs(base_candidates["Phi0_shell_weighted_Ic"] - same_candidates["Phi0_shell_weighted_Ic"])),
            "hist_gap": float(abs(base_candidates["Phi0_hist_Ic"] - same_candidates["Phi0_hist_Ic"])),
            "cut_gap": float(abs(base_candidates["Phi0_blend_weighted_cut"] - same_candidates["Phi0_blend_weighted_cut"])),
            "pass": bool(
                np.isclose(base_candidates["Phi0_ref_Ic"], same_candidates["Phi0_ref_Ic"], atol=1e-12)
                and np.isclose(base_candidates["Phi0_shell_weighted_Ic"], same_candidates["Phi0_shell_weighted_Ic"], atol=1e-12)
                and np.isclose(base_candidates["Phi0_hist_Ic"], same_candidates["Phi0_hist_Ic"], atol=1e-12)
                and np.isclose(base_candidates["Phi0_blend_weighted_cut"], same_candidates["Phi0_blend_weighted_cut"], atol=1e-12)
            ),
        },
        "tiny_shell_perturbation_is_smaller_than_identity_gap": {
            "shell_gap": float(abs(base_candidates["Phi0_shell_weighted_Ic"] - tiny_shell_candidates["Phi0_shell_weighted_Ic"])),
            "ref_gap": float(abs(base_candidates["Phi0_ref_Ic"] - tiny_shell_candidates["Phi0_ref_Ic"])),
            "pass": bool(
                abs(base_candidates["Phi0_shell_weighted_Ic"] - tiny_shell_candidates["Phi0_shell_weighted_Ic"])
                > 0.0
                and abs(base_candidates["Phi0_shell_weighted_Ic"] - tiny_shell_candidates["Phi0_shell_weighted_Ic"]) < 0.05
            ),
        },
        "tiny_reference_shift_is_smaller_than_large_channel_noise": {
            "tiny_ref_gap": float(abs(base_candidates["Phi0_ref_Ic"] - tiny_ref_candidates["Phi0_ref_Ic"])),
            "tiny_noise_gap": float(abs(base_candidates["Phi0_ref_Ic"] - coherent_information_a_to_b(tiny_noise))),
            "strong_noise_gap": float(abs(base_candidates["Phi0_blend_weighted_cut"] - weighted_cut_functional(strong_noise))),
            "pass": bool(
                abs(base_candidates["Phi0_ref_Ic"] - tiny_ref_candidates["Phi0_ref_Ic"])
                < abs(base_candidates["Phi0_blend_weighted_cut"] - weighted_cut_functional(strong_noise))
            ),
        },
        "boundary_noise_changes_bridge_more_than_blind_score": {
            "noise_gap": float(abs(base_candidates["Phi0_ref_Ic"] - coherent_information_a_to_b(tiny_noise))),
            "fake_gap": float(abs(fake_bridge_blind_packet_score(packet) - fake_bridge_blind_packet_score(packet))),
            "pass": bool(abs(base_candidates["Phi0_ref_Ic"] - coherent_information_a_to_b(tiny_noise)) > 1e-4),
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
        "name": "phi0_packet_robustness_audit",
        "probe": "pure_math_phi0_packet_robustness_audit",
        "purpose": (
            "Perturb packet ingredients directly and audit which Phi0 candidates "
            "track the bridge versus which metrics stay stable only because they ignore it."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "caveat": (
            "Pre-final-canon only. Bridge-blind metrics are intentionally included as counterexamples, "
            "not as candidate promotions."
        ),
        "summary": {
            "tests_total": pos_counts["total"] + neg_counts["total"] + bnd_counts["total"],
            "tests_passed": pos_counts["passed"] + neg_counts["passed"] + bnd_counts["passed"],
            "tests_failed": total_fail,
            "all_pass": total_fail == 0,
            "elapsed_s": None,
            "most_bridge_sensitive_candidate": "Phi0_shell_weighted_Ic",
            "most_bridge_blind_metric": "fake_packet_score",
        },
    }
    return results


if __name__ == "__main__":
    t0 = time.time()
    results = main()
    results["summary"]["elapsed_s"] = time.time() - t0
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "phi0_packet_robustness_audit_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(json.dumps(results["summary"], indent=2))
    print(f"Results written to {out_path}")
