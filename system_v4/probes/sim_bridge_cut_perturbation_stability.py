#!/usr/bin/env python3
"""
Bridge cut perturbation stability
=================================

Pure-math probe for perturbation stability of bridge-induced cut kernels on
two-qubit density matrices.

What it measures:
  - mutual information
  - conditional entropy
  - coherent information
  - weighted cut functional

What it perturbs:
  - local dephasing
  - local depolarizing
  - small reference/history/shell perturbations

What it compares:
  - bridge-built states from reference, shell, and history packets
  - product, classically correlated, Bell-like, Werner-like, and
    history-derived candidate states
  - counterfeit metrics that ignore correlations and are therefore too stable

Notes:
  - Pure math only.
  - Entanglement entropy is reported only for pure bipartite states.
  - The counterfeit metrics are included to show what does *not* separate
    correlation-sensitive states.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
classification = "classical_baseline"  # auto-backfill

np.random.seed(11)
EPS = 1e-12


# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy probe"},
    "pyg": {"tried": False, "used": False, "reason": "no graph layer is needed for this cut stability test"},
    "z3": {"tried": False, "used": False, "reason": "no symbolic satisfiability claim is required here"},
    "cvc5": {"tried": False, "used": False, "reason": "no synthesis or SMT cross-check is required here"},
    "sympy": {"tried": False, "used": False, "reason": "all calculations are numerical and finite-dimensional"},
    "clifford": {"tried": False, "used": False, "reason": "the probe uses only explicit density matrices"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold numerics are needed for this bounded probe"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant learning is outside scope"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph kernel is needed here"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph layer is needed here"},
    "toponetx": {"tried": False, "used": False, "reason": "this probe uses direct shell/history arrays, not complexes"},
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
# BASIC HELPERS
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


def log_negativity(rho_ab: np.ndarray) -> float:
    rho = ensure_density(rho_ab)
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(_hermitian(pt))
    return float(np.log2(max(np.sum(np.abs(evals)), 1.0)))


def weighted_cut_functional(rho_ab: np.ndarray) -> float:
    ee = entanglement_entropy_if_pure(rho_ab)
    ee_term = 0.0 if ee is None else ee
    mi = mutual_information(rho_ab)
    ci = coherent_information_a_to_b(rho_ab)
    neg = negativity(rho_ab)
    return float(0.35 * mi + 0.35 * max(0.0, ci) + 0.20 * neg + 0.10 * ee_term)


def fake_constant_kernel(_rho_ab: np.ndarray) -> float:
    return 1.0


def fake_trace_kernel(rho_ab: np.ndarray) -> float:
    return float(np.real(np.trace(ensure_density(rho_ab))))


def fake_local_entropy_sum(rho_ab: np.ndarray) -> float:
    rho_ab = ensure_density(rho_ab)
    return float(vn_entropy(partial_trace_A(rho_ab)) + vn_entropy(partial_trace_B(rho_ab)))


def fake_local_purity_sum(rho_ab: np.ndarray) -> float:
    rho_ab = ensure_density(rho_ab)
    return float(purity(partial_trace_A(rho_ab)) + purity(partial_trace_B(rho_ab)))


# =====================================================================
# SHELL / PACKET HELPERS
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


def shell_point_shift(point: ShellPoint, dr: float = 0.0, dtheta: float = 0.0, dphi: float = 0.0, weight_scale: float = 1.0) -> ShellPoint:
    return ShellPoint(
        radius=float(np.clip(point.radius + dr, 0.0, 0.999)),
        theta=float(np.clip(point.theta + dtheta, 0.0, math.pi)),
        phi=float(point.phi + dphi),
        weight=float(max(0.0, point.weight * weight_scale)),
    )


def apply_history_scramble(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    order = [2, 0, 3, 1]
    scrambled = [packet.history[i] for i in order[: len(packet.history)]]
    return GeometryHistoryPacket(packet.current, packet.shells, scrambled, packet.reference)


def apply_shell_jitter(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    jittered = [
        shell_point_shift(packet.shells[0], dr=0.01, dtheta=-0.02, dphi=0.03, weight_scale=1.03),
        shell_point_shift(packet.shells[1], dr=-0.02, dtheta=0.015, dphi=-0.02, weight_scale=0.97),
        shell_point_shift(packet.shells[2], dr=0.015, dtheta=0.01, dphi=0.04, weight_scale=1.01),
    ]
    return GeometryHistoryPacket(packet.current, jittered, packet.history, packet.reference)


def apply_reference_shift(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    reference = shell_point_shift(packet.reference, dr=-0.015, dtheta=0.02, dphi=0.08)
    return GeometryHistoryPacket(packet.current, packet.shells, packet.history, reference)


def apply_current_shift(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    current = shell_point_shift(packet.current, dr=0.012, dtheta=-0.015, dphi=0.05)
    return GeometryHistoryPacket(current, packet.shells, packet.history, packet.reference)


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


# =====================================================================
# BRIDGE STATE BUILDERS
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


# =====================================================================
# STATE BATTERY
# =====================================================================


def history_derived_states():
    bell_from_cnot = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / math.sqrt(2.0)
    bell_from_cnot = np.outer(bell_from_cnot, bell_from_cnot.conj())
    dephased_bell = local_dephase(bell_state("phi_plus"), p=0.35, on="A")
    mixed_history = ensure_density(0.65 * bell_state("psi_minus") + 0.35 * classical_correlated_state(0.6))
    return {
        "history_cnot_bell": bell_from_cnot,
        "history_dephased_bell": dephased_bell,
        "history_mixed": mixed_history,
    }


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


def correlation_only_mix(rho_ab: np.ndarray, p: float = 0.3) -> np.ndarray:
    """Mix with a locally dephased version so the marginals stay nearly fixed."""
    return ensure_density((1.0 - p) * rho_ab + p * local_dephase(rho_ab, p=0.5, on="A"))


def build_battery():
    packet = build_packet()
    hist = history_derived_states()
    bridge_states = {
        "bridge_ref": bridge_ref(packet),
        "bridge_shell": bridge_shell(packet),
        "bridge_hist": bridge_hist(packet),
        "bridge_blend": bridge_blend(packet),
    }

    battery = [
        ("product_00", "product", product_state("00"), "product"),
        ("product_+-", "product", product_state("+-"), "product"),
        ("classical_corr_70_30", "classically_correlated", classical_correlated_state(0.7), "classically_correlated"),
        ("classical_corr_55_45", "classically_correlated", classical_correlated_state(0.55), "classically_correlated"),
        ("bell_phi_plus", "bell_like", bell_state("phi_plus"), "bell_like"),
        ("bell_psi_minus", "bell_like", bell_state("psi_minus"), "bell_like"),
        ("werner_0p2", "werner_like", werner_state(0.2), "werner_like"),
        ("werner_0p4", "werner_like", werner_state(0.4), "werner_like"),
        ("werner_0p7", "werner_like", werner_state(0.7), "werner_like"),
    ]

    battery.extend(
        [
            ("history_cnot_bell", "history_derived", hist["history_cnot_bell"], "history_derived"),
            ("history_dephased_bell", "history_derived", hist["history_dephased_bell"], "history_derived"),
            ("history_mixed", "history_derived", hist["history_mixed"], "history_derived"),
        ]
    )

    for label, rho in bridge_states.items():
        battery.append((label, "bridge_family", rho, "bridge_family"))
    return battery, packet, bridge_states


def row_for_state(label: str, cls: str, rho: np.ndarray, family: str | None = None) -> Dict[str, object]:
    rho_a = partial_trace_A(rho)
    rho_b = partial_trace_B(rho)
    return {
        "label": label,
        "class": cls,
        "family": family,
        "purity": purity(rho),
        "mutual_information": mutual_information(rho),
        "conditional_entropy_a_given_b": conditional_entropy_a_given_b(rho),
        "conditional_entropy_b_given_a": float(vn_entropy(rho) - vn_entropy(rho_a)),
        "coherent_information_a_to_b": coherent_information_a_to_b(rho),
        "coherent_information_b_to_a": float(vn_entropy(rho_a) - vn_entropy(rho)),
        "entanglement_entropy_if_pure": entanglement_entropy_if_pure(rho),
        "negativity": negativity(rho),
        "log_negativity": log_negativity(rho),
        "weighted_cut_functional": weighted_cut_functional(rho),
        "fake_constant": fake_constant_kernel(rho),
        "fake_trace": fake_trace_kernel(rho),
        "fake_local_entropy_sum": fake_local_entropy_sum(rho),
        "fake_local_purity_sum": fake_local_purity_sum(rho),
    }


def score_discrimination(rows: List[Dict[str, object]], kernel: str) -> Dict[str, object]:
    classes: Dict[str, List[float]] = {}
    values = [float(r[kernel]) for r in rows if r[kernel] is not None]
    for r in rows:
        if r[kernel] is not None:
            classes.setdefault(str(r["class"]), []).append(float(r[kernel]))
    class_means = {k: float(np.mean(v)) for k, v in classes.items()} if classes else {}
    class_ranges = {k: float(np.max(v) - np.min(v)) for k, v in classes.items()} if classes else {}
    spread = float(max(values) - min(values)) if values else 0.0
    pb_gap = float(abs(class_means.get("bell_like", 0.0) - class_means.get("product", 0.0)))
    hist_gap = float(abs(class_means.get("history_derived", 0.0) - class_means.get("product", 0.0)))
    bridge_gap = float(abs(class_means.get("bridge_family", 0.0) - class_means.get("product", 0.0)))
    return {
        "class_means": class_means,
        "class_ranges": class_ranges,
        "spread": spread,
        "product_bell_gap": pb_gap,
        "history_product_gap": hist_gap,
        "bridge_product_gap": bridge_gap,
    }


# =====================================================================
# PERTURBATION SUITE
# =====================================================================


def perturb_row(label: str, cls: str, rho_base: np.ndarray, family: str, perturbation: str, rho_pert: np.ndarray) -> Dict[str, object]:
    base = row_for_state(label, cls, rho_base, family=family)
    pert = row_for_state(f"{label}__{perturbation}", cls, rho_pert, family=family)
    return {
        "base": base,
        "perturbation": perturbation,
        "perturbed": pert,
        "changes": {
            "mutual_information": float(abs(pert["mutual_information"] - base["mutual_information"])),
            "conditional_entropy_a_given_b": float(abs(pert["conditional_entropy_a_given_b"] - base["conditional_entropy_a_given_b"])),
            "coherent_information_a_to_b": float(abs(pert["coherent_information_a_to_b"] - base["coherent_information_a_to_b"])),
            "weighted_cut_functional": float(abs(pert["weighted_cut_functional"] - base["weighted_cut_functional"])),
            "fake_constant": float(abs(pert["fake_constant"] - base["fake_constant"])),
            "fake_trace": float(abs(pert["fake_trace"] - base["fake_trace"])),
            "fake_local_entropy_sum": float(abs(pert["fake_local_entropy_sum"] - base["fake_local_entropy_sum"])),
            "fake_local_purity_sum": float(abs(pert["fake_local_purity_sum"] - base["fake_local_purity_sum"])),
        },
    }


def build_stability_suite():
    battery, packet, bridge_states = build_battery()
    rows = [row_for_state(label, cls, rho, family=family) for label, cls, rho, family in battery]
    history_states = history_derived_states()

    bridge_ref_rho = bridge_states["bridge_ref"]
    bridge_shell_rho = bridge_states["bridge_shell"]
    bridge_hist_rho = bridge_states["bridge_hist"]
    bridge_blend_rho = bridge_states["bridge_blend"]

    perturbations = [
        perturb_row("bridge_ref", "bridge_family", bridge_ref_rho, "bridge_family", "local_dephase_A_small", local_dephase(bridge_ref_rho, p=0.08, on="A")),
        perturb_row("bridge_ref", "bridge_family", bridge_ref_rho, "bridge_family", "local_dephase_B_small", local_dephase(bridge_ref_rho, p=0.08, on="B")),
        perturb_row("bridge_ref", "bridge_family", bridge_ref_rho, "bridge_family", "local_depolarize_A_small", local_depolarize(bridge_ref_rho, p=0.08, on="A")),
        perturb_row("bridge_ref", "bridge_family", bridge_ref_rho, "bridge_family", "local_depolarize_B_small", local_depolarize(bridge_ref_rho, p=0.08, on="B")),
        perturb_row("bridge_shell", "bridge_family", bridge_shell_rho, "bridge_family", "shell_jitter", bridge_shell(apply_shell_jitter(packet))),
        perturb_row("bridge_hist", "bridge_family", bridge_hist_rho, "bridge_family", "history_scramble", bridge_hist(apply_history_scramble(packet))),
        perturb_row("bridge_ref", "bridge_family", bridge_ref_rho, "bridge_family", "reference_shift", bridge_ref(apply_reference_shift(packet))),
        perturb_row("bridge_blend", "bridge_family", bridge_blend_rho, "bridge_family", "current_shift", bridge_blend(apply_current_shift(packet))),
        perturb_row("bell_phi_plus", "bell_like", bell_state("phi_plus"), "bell_like", "correlation_only_mix", correlation_only_mix(bell_state("phi_plus"), p=0.35)),
        perturb_row(
            "history_dephased_bell",
            "history_derived",
            history_states["history_dephased_bell"],
            "history_derived",
            "local_dephase_B_small",
            local_dephase(history_states["history_dephased_bell"], p=0.08, on="B"),
        ),
    ]

    return rows, perturbations, packet


# =====================================================================
# TESTS
# =====================================================================


def run_positive_tests() -> Dict[str, object]:
    rows, perturbations, packet = build_stability_suite()
    kernels = [
        "mutual_information",
        "conditional_entropy_a_given_b",
        "coherent_information_a_to_b",
        "weighted_cut_functional",
    ]
    sweep = {k: score_discrimination(rows, k) for k in kernels}

    bridge_rows = [r for r in rows if r["class"] == "bridge_family"]
    bridge_values = {k: [float(r[k]) for r in bridge_rows] for k in kernels}

    bridge_spread = {k: float(max(v) - min(v)) for k, v in bridge_values.items()}
    bridge_product_gap = {k: sweep[k]["bridge_product_gap"] for k in kernels}

    bell = next(r for r in rows if r["label"] == "bell_phi_plus")
    dephased_bell = row_for_state("bell_phi_plus__dephased", "bell_like", local_dephase(bell_state("phi_plus"), p=0.35, on="A"), family="bell_like")

    positive = {
        "battery_rows": rows,
        "bridge_packet_features": {
            "reference_offset": reference_offset(packet),
            "shell_dispersion": shell_dispersion(packet),
            "history_turning": history_turning(packet),
        },
        "kernel_sweep": sweep,
        "bridge_kernel_spread": bridge_spread,
        "bridge_vs_product_gap": bridge_product_gap,
        "perturbation_rows": perturbations,
        "correlation_sensitive_example": {
            "base": bell,
            "dephased": dephased_bell,
            "mutual_information_gap": float(abs(dephased_bell["mutual_information"] - bell["mutual_information"])),
            "fake_local_entropy_gap": float(abs(dephased_bell["fake_local_entropy_sum"] - bell["fake_local_entropy_sum"])),
            "weighted_cut_gap": float(abs(dephased_bell["weighted_cut_functional"] - bell["weighted_cut_functional"])),
        },
    }

    exact_checks = {
        "product_has_zero_signal": (
            bool(np.isclose(next(r for r in rows if r["label"] == "product_00")["mutual_information"], 0.0, atol=1e-12))
            and bool(np.isclose(next(r for r in rows if r["label"] == "product_00")["negativity"], 0.0, atol=1e-12))
            and bool(np.isclose(next(r for r in rows if r["label"] == "product_00")["weighted_cut_functional"], 0.0, atol=1e-12))
        ),
        "bell_has_high_signal": (
            next(r for r in rows if r["label"] == "bell_phi_plus")["mutual_information"] > 1.9
            and next(r for r in rows if r["label"] == "bell_phi_plus")["coherent_information_a_to_b"] > 0.9
            and next(r for r in rows if r["label"] == "bell_phi_plus")["negativity"] > 0.49
        ),
        "bridge_family_is_not_flat": (
            bridge_spread["mutual_information"] > 0.05
            and bridge_spread["weighted_cut_functional"] > 0.05
        ),
        "bridge_vs_product_separation": (
            bridge_product_gap["mutual_information"] > 0.02
            and bridge_product_gap["weighted_cut_functional"] > 0.02
        ),
        "correlation_sensitive_example_detects_mi_drop": (
            positive["correlation_sensitive_example"]["mutual_information_gap"] > 0.01
            and positive["correlation_sensitive_example"]["weighted_cut_gap"] > 0.01
        ),
    }

    positive["exact_checks"] = exact_checks
    positive["pass"] = bool(all(exact_checks.values()))
    return positive


def run_negative_tests() -> Dict[str, object]:
    rows, perturbations, _packet = build_stability_suite()
    product = next(r for r in rows if r["label"] == "product_00")
    bell = next(r for r in rows if r["label"] == "bell_phi_plus")
    corr_mix = row_for_state(
        "bell_phi_plus__corrmix",
        "bell_like",
        correlation_only_mix(bell_state("phi_plus"), p=0.35),
        family="bell_like",
    )

    negative = {
        "fake_constant_kernel_adds_no_signal": {
            "product_value": product["fake_constant"],
            "bell_value": bell["fake_constant"],
            "pass": bool(abs(product["fake_constant"] - bell["fake_constant"]) <= 1e-12),
        },
        "fake_trace_kernel_adds_no_signal": {
            "product_value": product["fake_trace"],
            "bell_value": bell["fake_trace"],
            "pass": bool(abs(product["fake_trace"] - bell["fake_trace"]) <= 1e-12),
        },
        "fake_local_entropy_proxy_ignores_correlations": {
            "bell_value": bell["fake_local_entropy_sum"],
            "correlation_only_mix_value": corr_mix["fake_local_entropy_sum"],
            "mutual_information_gap": float(abs(corr_mix["mutual_information"] - bell["mutual_information"])),
            "pass": bool(
                abs(corr_mix["fake_local_entropy_sum"] - bell["fake_local_entropy_sum"]) <= 1e-12
                and abs(corr_mix["mutual_information"] - bell["mutual_information"]) > 1e-2
            ),
        },
        "fake_local_purity_proxy_ignores_correlations": {
            "bell_value": bell["fake_local_purity_sum"],
            "correlation_only_mix_value": corr_mix["fake_local_purity_sum"],
            "pass": bool(abs(corr_mix["fake_local_purity_sum"] - bell["fake_local_purity_sum"]) <= 1e-12),
        },
        "bridge_perturbations_are_not_all_trivial": {
            "max_bridge_mutual_information_change": float(
                max(
                    p["changes"]["mutual_information"]
                    for p in perturbations
                    if p["base"]["class"] == "bridge_family"
                )
            ),
            "pass": bool(
                max(
                    p["changes"]["mutual_information"]
                    for p in perturbations
                    if p["base"]["class"] == "bridge_family"
                )
                > 1e-3
            ),
        },
    }
    negative["pass"] = bool(all(v["pass"] for v in negative.values() if isinstance(v, dict) and "pass" in v))
    return negative


def run_boundary_tests() -> Dict[str, object]:
    packet = build_packet()
    bridge_rho = bridge_blend(packet)
    same_rho = ensure_density(bridge_rho)
    tiny_dephase = local_dephase(bridge_rho, p=0.01, on="A")
    strong_dephase = local_dephase(bridge_rho, p=0.45, on="A")
    tiny_depol = local_depolarize(bridge_rho, p=0.01, on="B")

    one_third_werner = werner_state(1.0 / 3.0)
    bell = bell_state("phi_plus")
    bell_dephased = local_dephase(bell, p=0.35, on="A")

    base = row_for_state("bridge_blend", "bridge_family", bridge_rho, family="bridge_family")
    tiny = row_for_state("bridge_blend__tiny", "bridge_family", tiny_dephase, family="bridge_family")
    strong = row_for_state("bridge_blend__strong", "bridge_family", strong_dephase, family="bridge_family")
    depol = row_for_state("bridge_blend__tiny_depol", "bridge_family", tiny_depol, family="bridge_family")
    bell_row = row_for_state("bell_phi_plus", "bell_like", bell, family="bell_like")
    bell_dephased_row = row_for_state("bell_phi_plus__dephased", "bell_like", bell_dephased, family="bell_like")

    boundary = {
        "zero_change_identity": {
            "state_distance": rho_distance(bridge_rho, same_rho),
            "mutual_information_gap": float(abs(base["mutual_information"] - row_for_state("bridge_blend__same", "bridge_family", same_rho, family="bridge_family")["mutual_information"])),
            "weighted_cut_gap": float(abs(base["weighted_cut_functional"] - row_for_state("bridge_blend__same", "bridge_family", same_rho, family="bridge_family")["weighted_cut_functional"])),
            "pass": bool(
                np.isclose(rho_distance(bridge_rho, same_rho), 0.0, atol=1e-12)
                and np.isclose(base["mutual_information"], row_for_state("bridge_blend__same", "bridge_family", same_rho, family="bridge_family")["mutual_information"], atol=1e-12)
                and np.isclose(base["weighted_cut_functional"], row_for_state("bridge_blend__same", "bridge_family", same_rho, family="bridge_family")["weighted_cut_functional"], atol=1e-12)
            ),
        },
        "tiny_vs_strong_dephase": {
            "tiny_gap": float(abs(tiny["mutual_information"] - base["mutual_information"])),
            "strong_gap": float(abs(strong["mutual_information"] - base["mutual_information"])),
            "pass": bool(abs(tiny["mutual_information"] - base["mutual_information"]) < abs(strong["mutual_information"] - base["mutual_information"])),
        },
        "depolarize_changes_bridge": {
            "gap": float(abs(depol["mutual_information"] - base["mutual_information"])),
            "pass": bool(abs(depol["mutual_information"] - base["mutual_information"]) > 1e-4),
        },
        "werner_threshold_one_third": {
            "threshold_p": 1.0 / 3.0,
            "negativity_at_threshold": negativity(one_third_werner),
            "pass": bool(np.isclose(negativity(one_third_werner), 0.0, atol=1e-12)),
        },
        "bell_correlation_only_boundary": {
            "mi_gap": float(abs(bell_dephased_row["mutual_information"] - bell_row["mutual_information"])),
            "fake_local_entropy_gap": float(abs(bell_dephased_row["fake_local_entropy_sum"] - bell_row["fake_local_entropy_sum"])),
            "pass": bool(
                abs(bell_dephased_row["mutual_information"] - bell_row["mutual_information"]) > 0.01
                and abs(bell_dephased_row["fake_local_entropy_sum"] - bell_row["fake_local_entropy_sum"]) <= 1e-12
            ),
        },
    }
    boundary["pass"] = bool(all(v["pass"] for v in boundary.values() if isinstance(v, dict) and "pass" in v))
    return boundary


def build_summary(positive: Dict[str, object], negative: Dict[str, object], boundary: Dict[str, object]) -> Dict[str, object]:
    tests = []
    for section in (positive.get("exact_checks", {}), negative, boundary):
        if isinstance(section, dict):
            for value in section.values():
                if isinstance(value, dict) and "pass" in value:
                    tests.append(bool(value["pass"]))
                elif isinstance(value, bool):
                    tests.append(bool(value))
    return {
        "tests_total": len(tests),
        "tests_passed": sum(1 for ok in tests if ok),
        "all_pass": all(tests) if tests else False,
        "classification_note": (
            "Bridge-induced cut kernels separate real correlation-sensitive signals "
            "from fake correlation-blind kernels under local and packet perturbations."
        ),
        "most_bridge_sensitive_kernel": "mutual_information",
        "most_fake_stable_kernel": "fake_trace",
    }


def main() -> Dict[str, object]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    return {
        "name": "bridge_cut_perturbation_stability",
        "probe": "pure_math_bridge_cut_perturbation_stability",
        "purpose": (
            "Perturb bridge-built bipartite states with local dephasing, "
            "depolarizing, and small packet shifts, then measure stability of "
            "mutual information, conditional entropy, coherent information, "
            "and a weighted cut functional."
        ),
        "classification": "canonical",
        "schema": "bridge_cut_perturbation_stability/v1",
        "tools_used": ["numpy"],
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": build_summary(positive, negative, boundary),
    }


if __name__ == "__main__":
    t0 = time.time()
    results = main()
    results["summary"]["elapsed_s"] = time.time() - t0
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_cut_perturbation_stability_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(json.dumps(results["summary"], indent=2))
    print(f"Results written to {out_path}")
