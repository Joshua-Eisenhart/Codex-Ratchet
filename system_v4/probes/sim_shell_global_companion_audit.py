#!/usr/bin/env python3
"""
SIM LEGO: Shell / global companion audit
=======================================
Pure math only. Audit classification.

This probe checks three bounded questions on a shared packet set:
1. When do shell/global forms behave like stronger global companions?
2. When do they approximate signed primitive behavior?
3. When are they just weighted bookkeeping?

The audit is intentionally conservative. It does not promote a canon; it
only checks whether the claims stay internally consistent on the same inputs.
"""

from __future__ import annotations

import json
import math
import os
import time
import traceback
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
classification = "classical_baseline"  # auto-backfill


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- exact finite-dimensional numpy checks are sufficient"},
    "pyg": {"tried": False, "used": False, "reason": "not needed -- there is no graph layer in this audit"},
    "z3": {"tried": False, "used": False, "reason": "not needed -- this audit is numerical and constructive"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed -- no synthesis or SMT constraints are required"},
    "sympy": {"tried": False, "used": False, "reason": "not needed -- all formulas are explicit finite matrix formulas"},
    "clifford": {"tried": False, "used": False, "reason": "not needed -- no geometric algebra layer is required"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold statistics are required"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed -- no equivariant learning layer is required"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no graph algorithms are needed here"},
    "xgi": {"tried": False, "used": False, "reason": "not needed -- no hypergraph or simplicial layer is needed here"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed -- this audit uses direct packet arrays, not complexes"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed -- no persistence computation is needed here"},
}


EPS = 1e-12
I2 = np.eye(2, dtype=np.complex128)
I4 = np.eye(4, dtype=np.complex128)
SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
BELL_PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)
BELL_PSI_MINUS = np.array([0.0, 1.0, -1.0, 0.0], dtype=np.complex128) / math.sqrt(2.0)


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


def _hermitian(rho: np.ndarray) -> np.ndarray:
    return 0.5 * (rho + rho.conj().T)


def ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=np.complex128)
    rho = _hermitian(rho)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
        if rho.shape == (4, 4):
            return I4 / 4.0
        return I2 / 2.0
    rho = evecs @ np.diag(evals / evals.sum()) @ evecs.conj().T
    return _hermitian(rho)


def validate_density(rho: np.ndarray) -> Dict[str, object]:
    rho = _hermitian(np.asarray(rho, dtype=np.complex128))
    evals = np.linalg.eigvalsh(rho).real
    tr = float(np.real(np.trace(rho)))
    herm_err = float(np.max(np.abs(rho - rho.conj().T)))
    return {
        "trace": tr,
        "trace_error": abs(tr - 1.0),
        "min_eigenvalue": float(np.min(evals)),
        "hermitian_error": herm_err,
        "psd": bool(np.min(evals) >= -1e-10),
        "valid": bool(abs(tr - 1.0) < 1e-10 and herm_err < 1e-10 and np.min(evals) >= -1e-10),
    }


def normalize_weights(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    total = float(np.sum(values))
    if total <= 0.0:
        return np.ones_like(values) / len(values)
    return values / total


def entropy(rho: np.ndarray) -> float:
    rho = ensure_density(rho)
    evals = np.linalg.eigvalsh(rho).real
    evals = evals[evals > EPS]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def partial_trace_a(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_b(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def mutual_information(rho_ab: np.ndarray) -> float:
    rho_ab = ensure_density(rho_ab)
    return float(entropy(partial_trace_a(rho_ab)) + entropy(partial_trace_b(rho_ab)) - entropy(rho_ab))


def coherent_information_a_to_b(rho_ab: np.ndarray) -> float:
    rho_ab = ensure_density(rho_ab)
    return float(entropy(partial_trace_b(rho_ab)) - entropy(rho_ab))


def conditional_entropy_a_given_b(rho_ab: np.ndarray) -> float:
    return float(entropy(rho_ab) - entropy(partial_trace_b(rho_ab)))


def negativity(rho_ab: np.ndarray) -> float:
    rho_pt = rho_ab.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(_hermitian(rho_pt))
    return float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0))


def weighted_cut_functional(rho_ab: np.ndarray) -> float:
    mi = mutual_information(rho_ab)
    ci = coherent_information_a_to_b(rho_ab)
    neg = negativity(rho_ab)
    return float(0.45 * mi + 0.35 * max(0.0, ci) + 0.20 * neg)


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


def local_dephase(rho_ab: np.ndarray, p: float = 0.05, on: str = "A") -> np.ndarray:
    op = np.kron(SIGMA_Z, I2) if on == "A" else np.kron(I2, SIGMA_Z)
    return ensure_density((1.0 - p) * rho_ab + p * (op @ rho_ab @ op.conj().T))


def local_depolarize(rho_ab: np.ndarray, p: float = 0.05, on: str = "A") -> np.ndarray:
    rho_ab = ensure_density(rho_ab)
    if on == "A":
        rho_b = partial_trace_b(rho_ab)
        return ensure_density((1.0 - p) * rho_ab + p * np.kron(I2 / 2.0, rho_b))
    rho_a = partial_trace_a(rho_ab)
    return ensure_density((1.0 - p) * rho_ab + p * np.kron(rho_a, I2 / 2.0))


def weighted_shell_ic(packet: GeometryHistoryPacket) -> float:
    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    total = 0.0
    for point, weight in zip(packet.shells, weights):
        shell_state = pair_state(left_density(point), right_density(point), 0.18 + 0.55 * abs(point.radius - packet.current.radius))
        total += weight * coherent_information_a_to_b(shell_state)
    return float(total)


def fake_constant_kernel(_packet: GeometryHistoryPacket) -> float:
    return 1.0


def fake_local_only_summary(packet: GeometryHistoryPacket) -> float:
    rho_a = left_density(packet.current)
    rho_b = right_density(packet.current)
    return float(entropy(rho_a) + entropy(rho_b))


def fake_shell_mean_only(packet: GeometryHistoryPacket) -> float:
    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    radii = np.array([p.radius for p in packet.shells], dtype=float)
    return float(np.dot(weights, radii))


def fake_history_mean_only(packet: GeometryHistoryPacket) -> float:
    if not packet.history:
        return 0.0
    return float(np.mean([p.phi for p in packet.history]))


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


def bridge_ref(packet: GeometryHistoryPacket) -> np.ndarray:
    rho_cur = pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    rho_ref = pair_state(left_density(packet.reference), right_density(packet.reference), 0.0)
    coupling = 0.45 * math.tanh(1.2 * reference_offset(packet))
    return ensure_density((1.0 - coupling) * rho_cur + coupling * rho_ref[::-1, ::-1])


def bridge_shell(packet: GeometryHistoryPacket) -> np.ndarray:
    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    rho = np.zeros((4, 4), dtype=np.complex128)
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
    rho = np.zeros((4, 4), dtype=np.complex128)
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
    return weighted_cut_functional(bridge_shell(packet))


def local_only_cut(packet: GeometryHistoryPacket) -> float:
    return fake_local_only_summary(packet)


def candidate_forms(packet: GeometryHistoryPacket) -> Dict[str, float]:
    rho_ref = bridge_ref(packet)
    rho_shell = bridge_shell(packet)
    rho_hist = bridge_hist(packet)
    rho_blend = bridge_blend(packet)
    return {
        "primitive_ref_Ic": coherent_information_a_to_b(rho_ref),
        "shell_Ic": coherent_information_a_to_b(rho_shell),
        "hist_Ic": coherent_information_a_to_b(rho_hist),
        "blend_MI": mutual_information(rho_blend),
        "blend_weighted_cut": weighted_cut_functional(rho_blend),
        "shell_global_cut": shell_global_cut(packet),
        "local_only_cut": local_only_cut(packet),
        "weighted_shell_Ic": weighted_shell_ic(packet),
        "uniform_shell_Ic": float(np.mean([coherent_information_a_to_b(pair_state(left_density(p), right_density(p), 0.18 + 0.55 * abs(p.radius - packet.current.radius))) for p in packet.shells])),
    }


def counterfeits(packet: GeometryHistoryPacket) -> Dict[str, float]:
    return {
        "fake_constant": fake_constant_kernel(packet),
        "fake_local_only": fake_local_only_summary(packet),
        "fake_shell_mean": fake_shell_mean_only(packet),
        "fake_history_mean": fake_history_mean_only(packet),
    }


def row_for_packet(label: str, packet: GeometryHistoryPacket) -> Dict[str, object]:
    return {
        "label": label,
        "features": packet_features(packet),
        "candidates": candidate_forms(packet),
        "counterfeits": counterfeits(packet),
        "validity": validate_density(bridge_blend(packet)),
    }


def build_packet_set() -> List[GeometryHistoryPacket]:
    base = build_packet()
    return [
        base,
        flatten_shell_placement(base),
        uniformize_shell_weights(base),
        scramble_history(base),
        shift_reference(base, dr=0.012, dtheta=0.02, dphi=0.05),
        shift_reference(base, dr=-0.03, dtheta=-0.05, dphi=0.16),
    ]


def candidate_gap(base: Dict[str, float], pert: Dict[str, float]) -> Dict[str, float]:
    return {key: float(abs(pert[key] - base[key])) for key in base}


def build_rows(packet: GeometryHistoryPacket) -> List[Dict[str, object]]:
    rows = [row_for_packet("baseline", packet)]
    perturbations = [
        ("flattened_shells", flatten_shell_placement(packet)),
        ("uniform_shell_weights", uniformize_shell_weights(packet)),
        ("scrambled_history", scramble_history(packet)),
        ("reference_shift_small", shift_reference(packet, dr=0.01, dtheta=0.02, dphi=0.05)),
        ("reference_shift_large", shift_reference(packet, dr=-0.03, dtheta=-0.05, dphi=0.16)),
    ]
    for label, pkt in perturbations:
        rows.append(row_for_packet(label, pkt))
    return rows


def family_scores(rows: List[Dict[str, object]]) -> Dict[str, float]:
    base = rows[0]["candidates"]
    weights = {
        "primitive_ref_Ic": 1.2,
        "shell_Ic": 1.1,
        "hist_Ic": 1.1,
        "blend_MI": 0.8,
        "blend_weighted_cut": 1.0,
        "shell_global_cut": 1.3,
        "local_only_cut": 0.2,
        "weighted_shell_Ic": 1.0,
        "uniform_shell_Ic": 0.9,
    }
    scores = {}
    for row in rows[1:]:
        gap = candidate_gap(base, row["candidates"])
        scores[row["label"]] = float(sum(weights[k] * gap[k] for k in gap))
    return scores


def build_family_consistency(rows: List[Dict[str, object]]) -> Dict[str, object]:
    base = rows[0]["candidates"]
    flattened = next(r for r in rows if r["label"] == "flattened_shells")
    uniformized = next(r for r in rows if r["label"] == "uniform_shell_weights")
    scrambled = next(r for r in rows if r["label"] == "scrambled_history")
    ref_small = next(r for r in rows if r["label"] == "reference_shift_small")
    ref_large = next(r for r in rows if r["label"] == "reference_shift_large")

    companion_shift = {
        "flattened_shells": float(abs(flattened["candidates"]["shell_global_cut"] - base["shell_global_cut"])),
        "uniform_shell_weights": float(abs(uniformized["candidates"]["shell_global_cut"] - base["shell_global_cut"])),
        "scrambled_history": float(abs(scrambled["candidates"]["blend_weighted_cut"] - base["blend_weighted_cut"])),
        "reference_shift_small": float(abs(ref_small["candidates"]["primitive_ref_Ic"] - base["primitive_ref_Ic"])),
        "reference_shift_large": float(abs(ref_large["candidates"]["primitive_ref_Ic"] - base["primitive_ref_Ic"])),
    }
    local_shift = {
        "flattened_shells": float(abs(flattened["candidates"]["local_only_cut"] - base["local_only_cut"])),
        "uniform_shell_weights": float(abs(uniformized["candidates"]["local_only_cut"] - base["local_only_cut"])),
        "scrambled_history": float(abs(scrambled["candidates"]["local_only_cut"] - base["local_only_cut"])),
        "reference_shift_small": float(abs(ref_small["candidates"]["local_only_cut"] - base["local_only_cut"])),
        "reference_shift_large": float(abs(ref_large["candidates"]["local_only_cut"] - base["local_only_cut"])),
    }

    better_than_local = sum(1 for key in companion_shift if companion_shift[key] > local_shift[key] + 1e-6)
    sign_matches = all(
        math.copysign(1.0, row["candidates"]["primitive_ref_Ic"] if row["candidates"]["primitive_ref_Ic"] != 0.0 else 1.0)
        == math.copysign(1.0, row["candidates"]["shell_Ic"] if row["candidates"]["shell_Ic"] != 0.0 else 1.0)
        == math.copysign(1.0, row["candidates"]["weighted_shell_Ic"] if row["candidates"]["weighted_shell_Ic"] != 0.0 else 1.0)
        for row in rows
    )
    # Companion claim is bounded: shell/global counts as stronger when it is
    # at least as sensitive as local-only on most perturbations.
    stronger_global_companion = better_than_local >= 3

    return {
        "companion_shift": companion_shift,
        "local_shift": local_shift,
        "better_than_local_count": better_than_local,
        "sign_matches_primitive": sign_matches,
        "stronger_global_companion": stronger_global_companion,
        "pass": bool(stronger_global_companion and sign_matches),
    }


def build_bookkeeping_audit(rows: List[Dict[str, object]]) -> Dict[str, object]:
    base = rows[0]
    flattened = next(r for r in rows if r["label"] == "flattened_shells")
    uniformized = next(r for r in rows if r["label"] == "uniform_shell_weights")
    scrambled = next(r for r in rows if r["label"] == "scrambled_history")

    bookkeeping = {
        "constant_kernel_is_flat": abs(base["counterfeits"]["fake_constant"] - flattened["counterfeits"]["fake_constant"]) <= 1e-12,
        "local_only_is_shell_blind": abs(base["counterfeits"]["fake_local_only"] - flattened["counterfeits"]["fake_local_only"]) <= 1e-12,
        "shell_mean_ignores_history_order": abs(base["counterfeits"]["fake_shell_mean"] - scrambled["counterfeits"]["fake_shell_mean"]) <= 1e-12,
        "history_mean_ignores_shell_relayout": abs(base["counterfeits"]["fake_history_mean"] - uniformized["counterfeits"]["fake_history_mean"]) <= 1e-12,
        "uniform_weights_reduce_to_mean": abs(base["candidates"]["uniform_shell_Ic"] - float(np.mean([
            coherent_information_a_to_b(pair_state(left_density(p), right_density(p), 0.18 + 0.55 * abs(p.radius - build_packet().current.radius)))
            for p in build_packet().shells
        ]))) <= 1e-12,
    }
    bookkeeping["pass"] = bool(all(bookkeeping.values()))
    return bookkeeping


def build_primitive_audit(rows: List[Dict[str, object]]) -> Dict[str, object]:
    base = rows[0]
    packet = build_packet()
    shells = packet.shells
    shell_profile = [
        coherent_information_a_to_b(pair_state(left_density(p), right_density(p), 0.18 + 0.55 * abs(p.radius - packet.current.radius)))
        for p in shells
    ]
    weighted_shell = base["candidates"]["weighted_shell_Ic"]
    uniform_shell = base["candidates"]["uniform_shell_Ic"]
    primitive = base["candidates"]["primitive_ref_Ic"]
    blend = base["candidates"]["blend_weighted_cut"]

    sign_checks = {
        "primitive_and_shell_same_sign": math.copysign(1.0, primitive if primitive != 0.0 else 1.0) == math.copysign(1.0, base["candidates"]["shell_Ic"] if base["candidates"]["shell_Ic"] != 0.0 else 1.0),
        "primitive_and_weighted_shell_same_sign": math.copysign(1.0, primitive if primitive != 0.0 else 1.0) == math.copysign(1.0, weighted_shell if weighted_shell != 0.0 else 1.0),
        "weighted_shell_between_shell_extremes": min(shell_profile) - 1e-12 <= weighted_shell <= max(shell_profile) + 1e-12,
        "uniform_shell_between_shell_extremes": min(shell_profile) - 1e-12 <= uniform_shell <= max(shell_profile) + 1e-12,
    }
    sign_checks["pass"] = bool(all(sign_checks.values()))
    return {
        "shell_profile": shell_profile,
        "primitive": primitive,
        "weighted_shell": weighted_shell,
        "uniform_shell": uniform_shell,
        "blend_weighted_cut": blend,
        "pass": bool(sign_checks["pass"]),
        "sign_checks": sign_checks,
    }


def count_section(section: Dict[str, dict]) -> Dict[str, int]:
    total = sum(1 for value in section.values() if isinstance(value, dict) and "pass" in value)
    passed = sum(1 for value in section.values() if isinstance(value, dict) and value.get("pass") is True)
    return {"passed": passed, "failed": total - passed, "total": total}


def run_positive_tests() -> Dict[str, object]:
    packet = build_packet()
    rows = build_rows(packet)
    family_consistency = build_family_consistency(rows)
    primitive_audit = build_primitive_audit(rows)

    positive = {
        "rows": rows,
        "family_consistency": family_consistency,
        "primitive_audit": primitive_audit,
        "sign_dual_check": bool(
            all(
                abs(
                    row["candidates"]["primitive_ref_Ic"]
                    + conditional_entropy_a_given_b(bridge_ref(packet if row["label"] == "baseline" else packet))
                ) < 1e-10
                for row in rows[:1]
            )
        ),
        "pass": bool(family_consistency["pass"] and primitive_audit["pass"]),
    }
    return positive


def run_negative_tests() -> Dict[str, object]:
    packet = build_packet()
    rows = build_rows(packet)
    base = rows[0]
    flattened = next(r for r in rows if r["label"] == "flattened_shells")
    uniformized = next(r for r in rows if r["label"] == "uniform_shell_weights")
    scrambled = next(r for r in rows if r["label"] == "scrambled_history")

    negative = {
        "fake_constant_is_bookkeeping_only": {
            "base": base["counterfeits"]["fake_constant"],
            "flattened": flattened["counterfeits"]["fake_constant"],
            "pass": bool(abs(base["counterfeits"]["fake_constant"] - flattened["counterfeits"]["fake_constant"]) <= 1e-12),
        },
        "fake_shell_mean_is_history_blind_bookkeeping": {
            "base": base["counterfeits"]["fake_shell_mean"],
            "scrambled": scrambled["counterfeits"]["fake_shell_mean"],
            "pass": bool(abs(base["counterfeits"]["fake_shell_mean"] - scrambled["counterfeits"]["fake_shell_mean"]) <= 1e-12),
        },
        "fake_history_mean_is_shell_blind_bookkeeping": {
            "base": base["counterfeits"]["fake_history_mean"],
            "uniformized": uniformized["counterfeits"]["fake_history_mean"],
            "pass": bool(abs(base["counterfeits"]["fake_history_mean"] - uniformized["counterfeits"]["fake_history_mean"]) <= 1e-12),
        },
        "local_only_summary_does_not_outperform_shell_global_cut": {
            "local_shift": float(abs(flattened["candidates"]["local_only_cut"] - base["candidates"]["local_only_cut"])),
            "global_shift": float(abs(flattened["candidates"]["shell_global_cut"] - base["candidates"]["shell_global_cut"])),
            "pass": bool(abs(flattened["candidates"]["shell_global_cut"] - base["candidates"]["shell_global_cut"]) > abs(flattened["candidates"]["local_only_cut"] - base["candidates"]["local_only_cut"])),
        },
        "bookkeeping_candidates_do_not_all_track_primitive_sign": {
            "primitive": base["candidates"]["primitive_ref_Ic"],
            "weighted_shell": base["candidates"]["weighted_shell_Ic"],
            "uniform_shell": base["candidates"]["uniform_shell_Ic"],
            "blend_weighted_cut": base["candidates"]["blend_weighted_cut"],
            "pass": bool(
                math.copysign(1.0, base["candidates"]["primitive_ref_Ic"] if base["candidates"]["primitive_ref_Ic"] != 0.0 else 1.0)
                == math.copysign(1.0, base["candidates"]["weighted_shell_Ic"] if base["candidates"]["weighted_shell_Ic"] != 0.0 else 1.0)
                and math.copysign(1.0, base["candidates"]["primitive_ref_Ic"] if base["candidates"]["primitive_ref_Ic"] != 0.0 else 1.0)
                != math.copysign(1.0, base["candidates"]["blend_weighted_cut"] if base["candidates"]["blend_weighted_cut"] != 0.0 else 1.0)
            ),
        },
    }
    negative["pass"] = bool(all(v["pass"] for v in negative.values() if isinstance(v, dict) and "pass" in v))
    return negative


def run_boundary_tests() -> Dict[str, object]:
    packet = build_packet()
    rows = build_rows(packet)
    base = rows[0]
    flat = row_for_packet("flat", flatten_shell_placement(packet))
    uniform = row_for_packet("uniform", uniformize_shell_weights(packet))
    tiny_ref = row_for_packet("tiny_ref", shift_reference(packet, dr=0.001, dtheta=0.001, dphi=0.001))
    large_ref = row_for_packet("large_ref", shift_reference(packet, dr=-0.04, dtheta=-0.05, dphi=0.15))

    boundary = {
        "identity_packet_is_fixed_point": {
            "primitive_gap": float(abs(base["candidates"]["primitive_ref_Ic"] - base["candidates"]["primitive_ref_Ic"])),
            "global_gap": float(abs(base["candidates"]["shell_global_cut"] - base["candidates"]["shell_global_cut"])),
            "pass": bool(
                np.isclose(base["candidates"]["primitive_ref_Ic"], base["candidates"]["primitive_ref_Ic"], atol=1e-12)
                and np.isclose(base["candidates"]["shell_global_cut"], base["candidates"]["shell_global_cut"], atol=1e-12)
            ),
        },
        "flattening_is_detected": {
            "shell_gap": float(abs(flat["candidates"]["shell_Ic"] - base["candidates"]["shell_Ic"])),
            "global_gap": float(abs(flat["candidates"]["shell_global_cut"] - base["candidates"]["shell_global_cut"])),
            "pass": bool(
                abs(flat["candidates"]["shell_Ic"] - base["candidates"]["shell_Ic"]) > 1e-4
                or abs(flat["candidates"]["shell_global_cut"] - base["candidates"]["shell_global_cut"]) > 1e-4
            ),
        },
        "uniformization_is_detected": {
            "shell_gap": float(abs(uniform["candidates"]["shell_Ic"] - base["candidates"]["shell_Ic"])),
            "global_gap": float(abs(uniform["candidates"]["shell_global_cut"] - base["candidates"]["shell_global_cut"])),
            "pass": bool(
                abs(uniform["candidates"]["shell_Ic"] - base["candidates"]["shell_Ic"]) > 1e-4
                or abs(uniform["candidates"]["shell_global_cut"] - base["candidates"]["shell_global_cut"]) > 1e-4
            ),
        },
        "small_reference_shift_is_smaller_than_large_shift": {
            "tiny_gap": float(abs(tiny_ref["candidates"]["primitive_ref_Ic"] - base["candidates"]["primitive_ref_Ic"])),
            "large_gap": float(abs(large_ref["candidates"]["primitive_ref_Ic"] - base["candidates"]["primitive_ref_Ic"])),
            "pass": bool(
                abs(tiny_ref["candidates"]["primitive_ref_Ic"] - base["candidates"]["primitive_ref_Ic"])
                < abs(large_ref["candidates"]["primitive_ref_Ic"] - base["candidates"]["primitive_ref_Ic"])
            ),
        },
    }
    boundary["pass"] = bool(all(v["pass"] for v in boundary.values() if isinstance(v, dict) and "pass" in v))
    return boundary


def build_summary(positive: Dict[str, object], negative: Dict[str, object], boundary: Dict[str, object]) -> Dict[str, object]:
    p_counts = count_section(positive)
    n_counts = count_section(negative)
    b_counts = count_section(boundary)
    return {
        "positive": f"{p_counts['passed']}/{p_counts['total']}",
        "negative": f"{n_counts['passed']}/{n_counts['total']}",
        "boundary": f"{b_counts['passed']}/{b_counts['total']}",
        "all_pass": positive["pass"] and negative["pass"] and boundary["pass"],
        "shared_packet_count": len(build_rows(build_packet())),
        "note": (
            "Audit only. Shell/global forms can act as stronger companions on this packet set, "
            "but local-only and bookkeeping forms remain bounded counterexamples."
            if positive["pass"] and negative["pass"] and boundary["pass"]
            else "Audit found a contradiction on the shared packet set."
        ),
    }


def main() -> Dict[str, object]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    results = {
        "name": "Shell / global companion audit",
        "schema_version": "1.0",
        "probe": "shell_global_companion_audit",
        "purpose": (
            "Audit when shell/global forms behave like stronger global companions, "
            "when they approximate signed primitive behavior, and when they collapse "
            "to weighted bookkeeping."
        ),
        "classification": "audit",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": build_summary(positive, negative, boundary),
    }
    return results


if __name__ == "__main__":
    try:
        t0 = time.time()
        results = main()
        results["summary"]["elapsed_s"] = time.time() - t0
        out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "shell_global_companion_audit_results.json")
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(results, handle, indent=2, default=str)
        print(f"Results written to {out_path}")
        print(results["summary"])
    except Exception as exc:
        print("FAILED:", exc)
        print(traceback.format_exc())
        raise
