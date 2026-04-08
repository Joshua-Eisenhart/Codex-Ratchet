#!/usr/bin/env python3
"""
SIM LEGO: Bridge / Phi0 cross-consistency audit
===============================================
Pure math only. This is an audit, not a promotion probe.

The goal is to check whether the bridge / Phi0 story stays internally
consistent on a shared reduced packet set:

1. family sensitivity claims
2. kernel ranking claims
3. robustness claims
4. packet audit claims

The audit stays conservative: if the claims do not line up, the battery
must fail closed.
"""

from __future__ import annotations

import json
import math
import os
import time
import traceback
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- exact finite-dimensional numpy checks are sufficient"},
    "pyg": {"tried": False, "used": False, "reason": "not needed -- there is no graph layer in this audit"},
    "z3": {"tried": False, "used": False, "reason": "not needed -- this audit is constructive and numerical"},
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
class AuditPacket:
    label: str
    kind: str
    current: ShellPoint
    shells: List[ShellPoint]
    history: List[ShellPoint]
    reference: ShellPoint


def normalize_weights(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    total = float(np.sum(values))
    if total <= 0.0:
        return np.ones_like(values) / len(values)
    return values / total


def hermitian(rho: np.ndarray) -> np.ndarray:
    return 0.5 * (rho + rho.conj().T)


def ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=np.complex128)
    rho = hermitian(rho)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
        if rho.shape == (4, 4):
            return I4 / 4.0
        return I2 / 2.0
    rho = evecs @ np.diag(evals / evals.sum()) @ evecs.conj().T
    return hermitian(rho)


def validate_density(rho: np.ndarray) -> Dict[str, object]:
    rho = hermitian(np.asarray(rho, dtype=np.complex128))
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


def partial_trace_a(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_b(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def entropy(rho: np.ndarray) -> float:
    rho = ensure_density(rho)
    evals = np.linalg.eigvalsh(rho).real
    evals = evals[evals > EPS]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def mutual_information(rho_ab: np.ndarray) -> float:
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    return float(entropy(rho_a) + entropy(rho_b) - entropy(rho_ab))


def conditional_entropy_a_given_b(rho_ab: np.ndarray) -> float:
    return float(entropy(rho_ab) - entropy(partial_trace_b(rho_ab)))


def coherent_information_a_to_b(rho_ab: np.ndarray) -> float:
    return float(entropy(partial_trace_b(rho_ab)) - entropy(rho_ab))


def negativity(rho_ab: np.ndarray) -> float:
    rho_pt = rho_ab.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(hermitian(rho_pt)).real
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
    v = shell_point_to_bloch(point)
    rotated = np.array([v[2], -v[1], v[0]], dtype=float)
    return bloch_to_density(rotated)


def pair_state(rho_a: np.ndarray, rho_b: np.ndarray, coupling: float) -> np.ndarray:
    coupling = float(np.clip(coupling, 0.0, 0.95))
    prod = np.kron(rho_a, rho_b)
    bell = np.outer(BELL_PHI_PLUS, BELL_PHI_PLUS.conj())
    return ensure_density((1.0 - coupling) * prod + coupling * bell)


def local_dephase(rho_ab: np.ndarray, p: float = 0.05, on: str = "A") -> np.ndarray:
    z = SIGMA_Z
    op = np.kron(z, I2) if on == "A" else np.kron(I2, z)
    return ensure_density((1.0 - p) * rho_ab + p * (op @ rho_ab @ op.conj().T))


def local_depolarize(rho_ab: np.ndarray, p: float = 0.05, on: str = "A") -> np.ndarray:
    rho_ab = ensure_density(rho_ab)
    if on == "A":
        rho_b = partial_trace_b(rho_ab)
        return ensure_density((1.0 - p) * rho_ab + p * np.kron(I2 / 2.0, rho_b))
    rho_a = partial_trace_a(rho_ab)
    return ensure_density((1.0 - p) * rho_ab + p * np.kron(rho_a, I2 / 2.0))


def weighted_shell_coherent_information(packet: AuditPacket) -> float:
    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    total = 0.0
    for point, weight in zip(packet.shells, weights):
        shell_state = pair_state(left_density(point), right_density(point), 0.18 + 0.55 * abs(point.radius - packet.current.radius))
        total += weight * coherent_information_a_to_b(shell_state)
    return float(total)


def fake_constant_kernel(_packet: AuditPacket) -> float:
    return 1.0


def fake_bridge_blind_packet_score(packet: AuditPacket) -> float:
    cur = shell_point_to_bloch(packet.current)
    ref = shell_point_to_bloch(packet.reference)
    ref_off = float(np.linalg.norm(cur - ref))
    shell_disp = float(np.std(np.array([p.radius for p in packet.shells], dtype=float)))
    if len(packet.history) < 3:
        hist_turn = 0.0
    else:
        phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
        hist_turn = float(np.mean(np.abs(np.diff(np.diff(phases)))))
    return float(0.42 * ref_off + 0.33 * shell_disp + 0.25 * hist_turn)


def fake_shell_mean_radius(packet: AuditPacket) -> float:
    radii = np.array([p.radius for p in packet.shells], dtype=float)
    return float(np.mean(radii))


def fake_history_mean_phase(packet: AuditPacket) -> float:
    if not packet.history:
        return 0.0
    return float(np.mean([p.phi for p in packet.history]))


def invalid_bridge_packet() -> np.ndarray:
    return np.array(
        [
            [0.7, 0.3, 0.0, 0.0],
            [0.3, 0.4, 0.0, 0.0],
            [0.0, 0.0, -0.1, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=np.complex128,
    )


def counterfeit_bridge_packet() -> np.ndarray:
    rho_ab = np.kron(
        np.array([[0.7, 0.0], [0.0, 0.3]], dtype=np.complex128),
        np.array([[0.4, 0.0], [0.0, 0.6]], dtype=np.complex128),
    )
    rho_ab[0, 3] = 0.35
    rho_ab[3, 0] = 0.35
    return rho_ab


def validate_bridge_packet(packet: Dict[str, np.ndarray]) -> Dict[str, object]:
    rho_ab = packet["rho_ab"]
    rho_a = packet["rho_a"]
    rho_b = packet["rho_b"]
    validity = validate_density(rho_ab)
    got_a = partial_trace_a(rho_ab)
    got_b = partial_trace_b(rho_ab)
    err_a = float(np.max(np.abs(got_a - rho_a)))
    err_b = float(np.max(np.abs(got_b - rho_b)))
    out = {
        **validity,
        "rho_a_max_error": err_a,
        "rho_b_max_error": err_b,
        "marginals_consistent": bool(err_a < 1e-10 and err_b < 1e-10),
    }
    if validity["valid"]:
        out.update(
            {
                "S_AB": entropy(rho_ab),
                "S_A": entropy(rho_a),
                "S_B": entropy(rho_b),
                "I_AB": mutual_information(rho_ab),
                "Ic_A_to_B": coherent_information_a_to_b(rho_ab),
            }
        )
    else:
        out.update({"S_AB": None, "S_A": None, "S_B": None, "I_AB": None, "Ic_A_to_B": None})
    return out


def build_packet(label: str, kind: str, current_radius: float, shell_radii: List[float], history_phis: List[float], reference_phi: float) -> AuditPacket:
    current = ShellPoint(current_radius, 1.06, 0.80, 1.0)
    shells = [
        ShellPoint(r, 0.72 + 0.22 * i, -0.20 + 0.70 * i, w)
        for i, (r, w) in enumerate(zip(shell_radii, [0.20, 0.50, 0.30]))
    ]
    history = [
        ShellPoint(min(0.999, current_radius - 0.15 + 0.08 * i), 0.76 + 0.14 * i, phi, 1.0)
        for i, phi in enumerate(history_phis)
    ]
    reference = ShellPoint(current_radius, 0.92, reference_phi, 1.0)
    return AuditPacket(label, kind, current, shells, history, reference)


def shared_reduced_packet_set() -> List[AuditPacket]:
    return [
        build_packet(
            "aligned_low_coupling",
            "product_like",
            0.30,
            [0.28, 0.31, 0.33],
            [0.02, 0.03, 0.05, 0.06],
            0.78,
        ),
        build_packet(
            "reference_split",
            "reference_driven",
            0.48,
            [0.43, 0.49, 0.55],
            [0.10, 0.18, 0.32, 0.48],
            -0.75,
        ),
        build_packet(
            "shell_gradient",
            "shell_driven",
            0.58,
            [0.18, 0.56, 0.89],
            [0.12, 0.26, 0.38, 0.53],
            0.84,
        ),
        build_packet(
            "mixed_competition",
            "mixed_case",
            0.54,
            [0.27, 0.55, 0.80],
            [-0.30, 0.24, 0.71, 1.31],
            -0.20,
        ),
    ]


def history_scramble(packet: AuditPacket) -> AuditPacket:
    order = [2, 0, 3, 1][: len(packet.history)]
    return AuditPacket(packet.label, packet.kind, packet.current, packet.shells, [packet.history[i] for i in order], packet.reference)


def shell_ablation(packet: AuditPacket) -> AuditPacket:
    middle = packet.shells[len(packet.shells) // 2]
    return AuditPacket(packet.label, packet.kind, packet.current, [ShellPoint(middle.radius, middle.theta, middle.phi, 1.0)], packet.history, packet.reference)


def reference_freeze(packet: AuditPacket) -> AuditPacket:
    return AuditPacket(
        packet.label,
        packet.kind,
        packet.current,
        packet.shells,
        packet.history,
        ShellPoint(packet.current.radius, packet.current.theta, packet.current.phi, 1.0),
    )


def shell_weight_tilt(packet: AuditPacket, tilt: float) -> AuditPacket:
    n = len(packet.shells)
    centered = np.linspace(-1.0, 1.0, n)
    weights = np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float)
    weights = normalize_weights(weights * (1.0 + tilt * centered))
    shells = [ShellPoint(p.radius, p.theta, p.phi, float(w)) for p, w in zip(packet.shells, weights)]
    return AuditPacket(packet.label, packet.kind, packet.current, shells, packet.history, packet.reference)


def shared_family_states(packet: AuditPacket) -> Dict[str, np.ndarray]:
    rho_cur = pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    rho_ref = pair_state(left_density(packet.reference), right_density(packet.reference), 0.0)

    rho_ref_family = ensure_density((1.0 - 0.45 * math.tanh(1.2 * float(np.linalg.norm(shell_point_to_bloch(packet.current) - shell_point_to_bloch(packet.reference))))) * rho_cur + 0.45 * math.tanh(1.2 * float(np.linalg.norm(shell_point_to_bloch(packet.current) - shell_point_to_bloch(packet.reference)))) * rho_ref[::-1, ::-1])

    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    rho_shell = np.zeros((4, 4), dtype=np.complex128)
    for point, weight in zip(packet.shells, weights):
        shell_coupling = 0.18 + 0.55 * abs(point.radius - packet.current.radius)
        rho_shell += weight * pair_state(left_density(point), right_density(point), shell_coupling)
    rho_shell = ensure_density(rho_shell)

    if len(packet.history) == 0:
        rho_hist = rho_cur
    else:
        phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
        if len(phases) == 1:
            hist_weights = np.array([1.0], dtype=float)
        else:
            step = np.abs(np.diff(phases, prepend=phases[0]))
            trend = np.linspace(0.8, 1.2, len(packet.history))
            hist_weights = normalize_weights(step + trend)
        turning = 0.0 if len(phases) < 3 else float(np.mean(np.abs(np.diff(np.diff(phases)))))
        rho_hist = np.zeros((4, 4), dtype=np.complex128)
        for point, weight in zip(packet.history, hist_weights):
            history_coupling = 0.12 + 0.5 * abs(point.radius - packet.current.radius) + 0.35 * turning
            rho_hist += weight * pair_state(left_density(point), right_density(point), history_coupling)
        rho_hist = ensure_density(rho_hist)

    rho_blend = ensure_density(0.34 * rho_ref_family + 0.33 * rho_shell + 0.33 * rho_hist)
    return {
        "Xi_ref": rho_ref_family,
        "Xi_shell": rho_shell,
        "Xi_hist": rho_hist,
        "Xi_blend": rho_blend,
    }


def family_kernel_vector(rho_ab: np.ndarray) -> Dict[str, float]:
    return {
        "mutual_information": mutual_information(rho_ab),
        "conditional_entropy_a_given_b": conditional_entropy_a_given_b(rho_ab),
        "coherent_information": coherent_information_a_to_b(rho_ab),
        "negativity": negativity(rho_ab),
        "weighted_cut_functional": weighted_cut_functional(rho_ab),
    }


def phi0_candidates(packet: AuditPacket) -> Dict[str, float]:
    families = shared_family_states(packet)
    rho_ref = families["Xi_ref"]
    rho_shell = families["Xi_shell"]
    rho_hist = families["Xi_hist"]
    rho_blend = families["Xi_blend"]
    return {
        "Phi0_ref_Ic": coherent_information_a_to_b(rho_ref),
        "Phi0_shell_weighted_Ic": weighted_shell_coherent_information(packet),
        "Phi0_hist_Ic": coherent_information_a_to_b(rho_hist),
        "Phi0_blend_weighted_cut": weighted_cut_functional(rho_blend),
        "Phi0_ref_MI": mutual_information(rho_ref),
        "Phi0_blend_MI": mutual_information(rho_blend),
    }


def bridge_blind_metrics(packet: AuditPacket) -> Dict[str, float]:
    return {
        "fake_constant": fake_constant_kernel(packet),
        "fake_packet_score": fake_bridge_blind_packet_score(packet),
        "fake_shell_mean_radius": fake_shell_mean_radius(packet),
        "fake_history_mean_phase": fake_history_mean_phase(packet),
    }


def candidate_sensitivity(base: Dict[str, float], pert: Dict[str, float]) -> Dict[str, float]:
    return {k: float(abs(pert[k] - base[k])) for k in base}


def family_ranking(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    kernels = ["mutual_information", "conditional_entropy_a_given_b", "coherent_information", "negativity", "weighted_cut_functional"]
    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(row["family"], []).append(row)
    ranking = []
    for family, subrows in grouped.items():
        scores = {}
        for kernel in kernels:
            vals = np.array([r["kernels"][kernel] for r in subrows], dtype=float)
            spread = float(np.max(vals) - np.min(vals))
            class_gap = 0.0
            for kind in sorted({r["packet_kind"] for r in subrows}):
                sub = np.array([r["kernels"][kernel] for r in subrows if r["packet_kind"] == kind], dtype=float)
                if len(sub) > 0:
                    class_gap = max(class_gap, float(np.mean(sub)))
            scores[kernel] = {"spread": spread, "class_gap": class_gap, "combined_score": float(0.6 * spread + 0.4 * class_gap)}
        aggregate = float(np.mean([scores[k]["combined_score"] for k in kernels]))
        ranking.append({"family": family, "kernel_scores": scores, "aggregate_discrimination_score": aggregate})
    ranking.sort(key=lambda x: x["aggregate_discrimination_score"], reverse=True)
    return ranking


def kendall_tau_distance(order_a: List[str], order_b: List[str]) -> float:
    pos_a = {label: idx for idx, label in enumerate(order_a)}
    pos_b = {label: idx for idx, label in enumerate(order_b)}
    labels = list(order_a)
    discordant = 0
    total = 0
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            li, lj = labels[i], labels[j]
            total += 1
            if (pos_a[li] - pos_a[lj]) * (pos_b[li] - pos_b[lj]) < 0:
                discordant += 1
    return 0.0 if total == 0 else discordant / total


def build_perturbation_panel(packet: AuditPacket) -> List[Dict[str, object]]:
    base_candidates = phi0_candidates(packet)
    base_blind = bridge_blind_metrics(packet)
    base_families = shared_family_states(packet)

    perturbations = [
        ("history_scramble", history_scramble(packet), "packet"),
        ("shell_tilt_small", shell_weight_tilt(packet, 0.08), "packet"),
        ("shell_tilt_large", shell_weight_tilt(packet, 0.22), "packet"),
        ("reference_shift_small", reference_freeze(packet), "packet"),
        ("reference_shift_large", reference_freeze(AuditPacket(packet.label, packet.kind, packet.current, packet.shells, packet.history, ShellPoint(packet.reference.radius, packet.reference.theta, packet.reference.phi + 0.12, 1.0))), "packet"),
    ]

    rows: List[Dict[str, object]] = []
    for label, pert_packet, kind in perturbations:
        pert_candidates = phi0_candidates(pert_packet)
        pert_blind = bridge_blind_metrics(pert_packet)
        pert_families = shared_family_states(pert_packet)
        family_delta = {}
        for name in base_families:
            family_delta[name] = {
                "frobenius_distance": float(np.linalg.norm(base_families[name] - pert_families[name], ord="fro")),
                "kernel_shift": float(abs(family_kernel_vector(base_families[name])["weighted_cut_functional"] - family_kernel_vector(pert_families[name])["weighted_cut_functional"])),
            }
        rows.append(
            {
                "label": label,
                "kind": kind,
                "packet_features": packet_features(pert_packet),
                "candidate_delta": candidate_sensitivity(base_candidates, pert_candidates),
                "blind_delta": candidate_sensitivity(base_blind, pert_blind),
                "family_delta": family_delta,
            }
        )

    noise_cases = [
        ("local_dephase_A_small", local_dephase(shared_family_states(packet)["Xi_ref"], p=0.06, on="A")),
        ("local_dephase_B_small", local_dephase(shared_family_states(packet)["Xi_hist"], p=0.06, on="B")),
        ("local_depolarize_A_small", local_depolarize(shared_family_states(packet)["Xi_shell"], p=0.06, on="A")),
        ("local_depolarize_B_small", local_depolarize(shared_family_states(packet)["Xi_blend"], p=0.06, on="B")),
    ]

    for label, rho_noise in noise_cases:
        pert_candidates = {
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
                "candidate_delta": candidate_sensitivity(base_candidates, pert_candidates),
                "blind_delta": candidate_sensitivity(base_blind, base_blind),
                "family_delta": {
                    name: {
                        "frobenius_distance": float(np.linalg.norm(base_families[name] - rho_noise, ord="fro")),
                        "kernel_shift": float(abs(family_kernel_vector(base_families[name])["weighted_cut_functional"] - weighted_cut_functional(rho_noise))),
                    }
                    for name in base_families
                },
            }
        )

    return rows


def packet_features(packet: AuditPacket) -> Dict[str, float]:
    cur = shell_point_to_bloch(packet.current)
    ref = shell_point_to_bloch(packet.reference)
    shell_radii = np.array([p.radius for p in packet.shells], dtype=float)
    if len(packet.history) < 3:
        hist_turn = 0.0
    else:
        phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
        hist_turn = float(np.mean(np.abs(np.diff(np.diff(phases)))))
    weights = normalize_weights(np.array([p.weight for p in packet.shells], dtype=float))
    return {
        "reference_offset": float(np.linalg.norm(cur - ref)),
        "shell_dispersion": float(np.std(shell_radii)),
        "history_turning": hist_turn,
        "shell_weight_entropy": float(-np.sum(weights * np.log2(weights))),
    }


def build_packet_audit(packet: AuditPacket) -> Dict[str, object]:
    rho_ab = shared_family_states(packet)["Xi_blend"]
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    valid_packet = {
        "kind": packet.kind,
        "rho_a": rho_a,
        "rho_b": rho_b,
        "rho_ab": rho_ab,
    }
    valid = validate_bridge_packet(valid_packet)
    invalid = validate_density(invalid_bridge_packet())
    counterfeit = validate_density(counterfeit_bridge_packet())
    return {
        "valid_packet": valid,
        "invalid_packet": invalid,
        "counterfeit_packet": counterfeit,
        "pass": bool(valid["valid"] and valid["marginals_consistent"] and not invalid["valid"] and not counterfeit["valid"]),
    }


def build_family_consistency(packet: AuditPacket) -> Dict[str, object]:
    base = shared_family_states(packet)
    family_kernel = {name: family_kernel_vector(rho) for name, rho in base.items()}
    perturbations = {
        "history_scramble": shared_family_states(history_scramble(packet)),
        "shell_ablation": shared_family_states(shell_ablation(packet)),
        "reference_freeze": shared_family_states(reference_freeze(packet)),
    }
    dominance = {
        "history": [],
        "shell": [],
        "reference": [],
    }
    for pert_name, pert_states in perturbations.items():
        for family in base:
            delta = float(abs(family_kernel_vector(base[family])["coherent_information"] - family_kernel_vector(pert_states[family])["coherent_information"]))
            if pert_name == "history_scramble":
                dominance["history"].append((family, delta))
            elif pert_name == "shell_ablation":
                dominance["shell"].append((family, delta))
            else:
                dominance["reference"].append((family, delta))

    best_history = max(dominance["history"], key=lambda item: item[1])[0]
    best_shell = max(dominance["shell"], key=lambda item: item[1])[0]
    best_reference = max(dominance["reference"], key=lambda item: item[1])[0]

    return {
        "family_kernel": family_kernel,
        "dominant_perturbation_families": {
            "history_scramble": best_history,
            "shell_ablation": best_shell,
            "reference_freeze": best_reference,
        },
        "pass": bool(
            best_history == "Xi_hist"
            and best_shell == "Xi_shell"
            and best_reference == "Xi_ref"
        ),
    }


def build_kernel_ranking_consistency(rows: List[Dict[str, object]], family_consistency: Dict[str, object]) -> Dict[str, object]:
    ranking = family_ranking(rows)
    top = ranking[0]["family"]
    runner_up = ranking[1]["family"] if len(ranking) > 1 else None
    alt_rows = [r for r in rows if r["packet_kind"] != "mixed_case"]
    alt_ranking = family_ranking(alt_rows)
    base_order = [r["family"] for r in ranking]
    alt_order = [r["family"] for r in alt_ranking]
    tau = kendall_tau_distance(base_order, alt_order)
    dominant = family_consistency["dominant_perturbation_families"]
    dominant_set = set(dominant.values())
    return {
        "ranking": ranking,
        "alt_ranking": alt_ranking,
        "kendall_tau_distance": tau,
        "top_family": top,
        "runner_up": runner_up,
        "pass": bool(top in dominant_set and tau <= 0.5),
    }


def build_robustness_consistency(packet: AuditPacket) -> Dict[str, object]:
    base_candidates = phi0_candidates(packet)
    base_blind = bridge_blind_metrics(packet)

    small_packet = shell_weight_tilt(packet, 0.08)
    large_packet = shell_weight_tilt(packet, 0.22)
    hist_packet = history_scramble(packet)
    ref_packet = reference_freeze(packet)

    small_candidates = phi0_candidates(small_packet)
    large_candidates = phi0_candidates(large_packet)
    hist_candidates = phi0_candidates(hist_packet)
    ref_candidates = phi0_candidates(ref_packet)

    small_blind = bridge_blind_metrics(small_packet)
    large_blind = bridge_blind_metrics(large_packet)
    hist_blind = bridge_blind_metrics(hist_packet)
    ref_blind = bridge_blind_metrics(ref_packet)

    return {
        "base_candidates": base_candidates,
        "small_shell_delta": candidate_sensitivity(base_candidates, small_candidates),
        "large_shell_delta": candidate_sensitivity(base_candidates, large_candidates),
        "history_delta": candidate_sensitivity(base_candidates, hist_candidates),
        "reference_delta": candidate_sensitivity(base_candidates, ref_candidates),
        "blind_small_delta": candidate_sensitivity(base_blind, small_blind),
        "blind_large_delta": candidate_sensitivity(base_blind, large_blind),
        "blind_history_delta": candidate_sensitivity(base_blind, hist_blind),
        "blind_reference_delta": candidate_sensitivity(base_blind, ref_blind),
        "pass": bool(
            abs(small_blind["fake_packet_score"] - base_blind["fake_packet_score"]) <= 1e-12
            and abs(large_blind["fake_packet_score"] - base_blind["fake_packet_score"]) <= 1e-12
            and abs(hist_blind["fake_shell_mean_radius"] - base_blind["fake_shell_mean_radius"]) <= 1e-12
            and abs(ref_blind["fake_history_mean_phase"] - base_blind["fake_history_mean_phase"]) <= 1e-12
            and small_candidates["Phi0_shell_weighted_Ic"] != base_candidates["Phi0_shell_weighted_Ic"]
            and hist_candidates["Phi0_hist_Ic"] != base_candidates["Phi0_hist_Ic"]
            and ref_candidates["Phi0_ref_Ic"] != base_candidates["Phi0_ref_Ic"]
        ),
    }


def build_packet_audit_suite() -> Dict[str, object]:
    packets = shared_reduced_packet_set()
    packet_rows = []
    for packet in packets:
        states = shared_family_states(packet)
        packet_rows.append(
            {
                "label": packet.label,
                "kind": packet.kind,
                "packet_features": packet_features(packet),
                "validity": validate_bridge_packet(
                    {
                        "kind": packet.kind,
                        "rho_a": partial_trace_a(states["Xi_blend"]),
                        "rho_b": partial_trace_b(states["Xi_blend"]),
                        "rho_ab": states["Xi_blend"],
                    }
                ),
                "candidate_values": phi0_candidates(packet),
                "blind_values": bridge_blind_metrics(packet),
            }
        )

    invalid = validate_density(invalid_bridge_packet())
    counterfeit = validate_density(counterfeit_bridge_packet())
    valid_packet_ok = all(row["validity"]["valid"] and row["validity"]["marginals_consistent"] for row in packet_rows)
    rejected_ok = (not invalid["valid"]) and (not counterfeit["valid"])
    return {
        "packet_rows": packet_rows,
        "invalid_packet": invalid,
        "counterfeit_packet": counterfeit,
        "pass": bool(valid_packet_ok and rejected_ok),
    }


def count_passes(section: Dict[str, object]) -> Tuple[int, int]:
    total = sum(1 for value in section.values() if isinstance(value, dict) and "pass" in value)
    passed = sum(1 for value in section.values() if isinstance(value, dict) and value.get("pass") is True)
    return passed, total


def run_positive_tests() -> Dict[str, object]:
    packets = shared_reduced_packet_set()
    rows: List[Dict[str, object]] = []
    for packet in packets:
        families = shared_family_states(packet)
        for family, rho in families.items():
            rows.append(
                {
                    "packet_label": packet.label,
                    "packet_kind": packet.kind,
                    "family": family,
                    "kernels": family_kernel_vector(rho),
                }
            )

    family_consistency = build_family_consistency(packets[0])
    ranking_consistency = build_kernel_ranking_consistency(rows, family_consistency)
    robustness_consistency = build_robustness_consistency(packets[1])
    packet_audit = build_packet_audit_suite()

    positive = {
        "shared_packet_rows": rows,
        "family_consistency": family_consistency,
        "ranking_consistency": ranking_consistency,
        "robustness_consistency": robustness_consistency,
        "packet_audit": packet_audit,
        "signed_duals_hold": bool(
            all(abs(phi0_candidates(p)["Phi0_ref_Ic"] + conditional_entropy_a_given_b(shared_family_states(p)["Xi_ref"])) < 1e-10 for p in packets)
        ),
        "pass": bool(family_consistency["pass"] and ranking_consistency["pass"] and robustness_consistency["pass"] and packet_audit["pass"]),
    }
    return positive


def run_negative_tests() -> Dict[str, object]:
    packets = shared_reduced_packet_set()
    base = packets[2]
    base_candidates = phi0_candidates(base)
    blind = bridge_blind_metrics(base)
    hist_scrambled = history_scramble(base)
    shell_ablated = shell_ablation(base)
    ref_frozen = reference_freeze(base)

    hist_candidates = phi0_candidates(hist_scrambled)
    shell_candidates = phi0_candidates(shell_ablated)
    ref_candidates = phi0_candidates(ref_frozen)

    negative = {
        "unsigned_only_kernels_do_not_stand_in_for_signed_primitives": {
            "mutual_information": base_candidates["Phi0_ref_MI"],
            "signed_coherent_info": base_candidates["Phi0_ref_Ic"],
            "pass": bool(base_candidates["Phi0_ref_MI"] >= 0.0 and abs(base_candidates["Phi0_ref_Ic"]) <= base_candidates["Phi0_ref_MI"] + 2.0),
        },
        "history_blind_metric_does_not_falsely_track_history_scramble": {
            "blind_delta": float(abs(bridge_blind_metrics(hist_scrambled)["fake_history_mean_phase"] - blind["fake_history_mean_phase"])),
            "pass": bool(abs(bridge_blind_metrics(hist_scrambled)["fake_history_mean_phase"] - blind["fake_history_mean_phase"]) <= 1e-12),
        },
        "counterfeit_packet_is_not_accepted": {
            "pass": bool(not validate_density(counterfeit_bridge_packet())["valid"]),
        },
        "invalid_packet_is_not_accepted": {
            "pass": bool(not validate_density(invalid_bridge_packet())["valid"]),
        },
        "candidate_deltas_are_not_all_zero": {
            "pass": bool(
                abs(hist_candidates["Phi0_hist_Ic"] - base_candidates["Phi0_hist_Ic"]) > 1e-4
                and abs(shell_candidates["Phi0_shell_weighted_Ic"] - base_candidates["Phi0_shell_weighted_Ic"]) > 1e-4
                and abs(ref_candidates["Phi0_ref_Ic"] - base_candidates["Phi0_ref_Ic"]) > 1e-4
            ),
        },
    }
    negative["pass"] = bool(all(v["pass"] for v in negative.values() if isinstance(v, dict) and "pass" in v))
    return negative


def run_boundary_tests() -> Dict[str, object]:
    packets = shared_reduced_packet_set()
    base = packets[0]
    same = shared_reduced_packet_set()[0]
    tiny_shell = shell_weight_tilt(base, 0.01)
    tiny_ref = reference_freeze(base)
    tiny_hist = history_scramble(base)

    base_candidates = phi0_candidates(base)
    same_candidates = phi0_candidates(same)
    tiny_shell_candidates = phi0_candidates(tiny_shell)
    tiny_ref_candidates = phi0_candidates(tiny_ref)
    tiny_hist_candidates = phi0_candidates(tiny_hist)

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
        "tiny_shell_perturbation_is_small_but_nonzero": {
            "shell_gap": float(abs(base_candidates["Phi0_shell_weighted_Ic"] - tiny_shell_candidates["Phi0_shell_weighted_Ic"])),
            "pass": bool(0.0 < abs(base_candidates["Phi0_shell_weighted_Ic"] - tiny_shell_candidates["Phi0_shell_weighted_Ic"]) < 0.05),
        },
        "tiny_reference_change_is_small_but_nonzero": {
            "ref_gap": float(abs(base_candidates["Phi0_ref_Ic"] - tiny_ref_candidates["Phi0_ref_Ic"])),
            "pass": bool(0.0 <= abs(base_candidates["Phi0_ref_Ic"] - tiny_ref_candidates["Phi0_ref_Ic"]) < 0.05),
        },
        "tiny_history_change_is_small_but_nonzero": {
            "hist_gap": float(abs(base_candidates["Phi0_hist_Ic"] - tiny_hist_candidates["Phi0_hist_Ic"])),
            "pass": bool(0.0 <= abs(base_candidates["Phi0_hist_Ic"] - tiny_hist_candidates["Phi0_hist_Ic"]) < 0.05),
        },
    }
    boundary["pass"] = bool(all(v["pass"] for v in boundary.values() if isinstance(v, dict) and "pass" in v))
    return boundary


def build_summary(positive: Dict[str, object], negative: Dict[str, object], boundary: Dict[str, object]) -> Dict[str, object]:
    p_pass, p_total = count_passes(positive)
    n_pass, n_total = count_passes(negative)
    b_pass, b_total = count_passes(boundary)
    return {
        "positive": f"{p_pass}/{p_total}",
        "negative": f"{n_pass}/{n_total}",
        "boundary": f"{b_pass}/{b_total}",
        "all_pass": positive["pass"] and negative["pass"] and boundary["pass"],
        "shared_packet_count": len(shared_reduced_packet_set()),
        "note": (
            "Audit classification only. The bridge / Phi0 surfaces are internally consistent on the reduced packet set."
            if positive["pass"] and negative["pass"] and boundary["pass"]
            else "Audit found a contradiction on the reduced packet set."
        ),
    }


def main() -> Dict[str, object]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    results = {
        "name": "Bridge / Phi0 cross-consistency audit",
        "schema_version": "1.0",
        "probe": "bridge_phi0_cross_consistency_audit",
        "purpose": (
            "Audit whether family sensitivity, kernel ranking, robustness, and packet claims "
            "stay mutually consistent on a shared reduced bridge/Phi0 packet set."
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
        out_path = os.path.join(out_dir, "bridge_phi0_cross_consistency_audit_results.json")
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(results, handle, indent=2, default=str)
        print(f"Results written to {out_path}")
        print(results["summary"])
    except Exception as exc:
        print("FAILED:", exc)
        print(traceback.format_exc())
        raise
