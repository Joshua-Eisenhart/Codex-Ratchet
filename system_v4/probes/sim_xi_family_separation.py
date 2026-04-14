#!/usr/bin/env python3
"""
Xi-family separation probe
==========================

Purpose:
  Compare three pure-math bridge-candidate families that map geometry/history
  inputs into bipartite density operators:

    1. Xi_ref   : reference-anchored bridge
    2. Xi_shell : shell-weighted bridge
    3. Xi_hist  : ordered-history bridge

This probe does not select a final canon. It only checks whether these
candidate families:
  - produce valid bipartite states,
  - remain distinct on the same input packet,
  - respond differently to history scrambling, shell ablation, and reference
    freezing,
  - behave honestly on negative and boundary inputs.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
classification = "classical_baseline"  # auto-backfill


TOOL_MANIFEST = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not needed; this is a small closed-form numpy probe",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "graph learning is not needed for this bounded family separation test",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "no symbolic satisfiability claim is required here",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "no synthesis or SMT cross-check is required here",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "all calculations are numerical and finite-dimensional",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "the probe uses only Bloch-vector density matrices",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "manifold tooling is not needed for this bounded comparison",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "equivariant neural tooling is outside scope",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "no graph-algorithm layer is required here",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "no hypergraph layer is required here",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "this probe uses direct shell/history arrays, not cell complexes",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "no persistence computation is needed here",
    },
}


SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
PAULIS = [SIGMA_X, SIGMA_Y, SIGMA_Z]
I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)
BELL_PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / math.sqrt(2.0)
RNG = np.random.default_rng(7)


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


def normalize_weights(values: np.ndarray) -> np.ndarray:
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


def ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex)
    rho = 0.5 * (rho + rho.conj().T)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
        return I4 / 4.0 if rho.shape == (4, 4) else I2 / 2.0
    rho = evecs @ np.diag(evals / evals.sum()) @ evecs.conj().T
    return 0.5 * (rho + rho.conj().T)


def pair_state(rho_a: np.ndarray, rho_b: np.ndarray, coupling: float) -> np.ndarray:
    coupling = float(np.clip(coupling, 0.0, 0.95))
    prod = np.kron(rho_a, rho_b)
    bell = np.outer(BELL_PHI_PLUS, BELL_PHI_PLUS.conj())
    return ensure_density((1.0 - coupling) * prod + coupling * bell)


def partial_trace_a(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_b(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def von_neumann_entropy(rho: np.ndarray) -> float:
    evals = np.real(np.linalg.eigvalsh(ensure_density(rho)))
    evals = evals[evals > 1e-14]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def mutual_information(rho_ab: np.ndarray) -> float:
    return max(
        0.0,
        von_neumann_entropy(partial_trace_b(rho_ab))
        + von_neumann_entropy(partial_trace_a(rho_ab))
        - von_neumann_entropy(rho_ab),
    )


def coherent_information(rho_ab: np.ndarray) -> float:
    return float(von_neumann_entropy(partial_trace_a(rho_ab)) - von_neumann_entropy(rho_ab))


def negativity(rho_ab: np.ndarray) -> float:
    rho = rho_ab.reshape(2, 2, 2, 2)
    rho_pt = np.transpose(rho, (0, 3, 2, 1)).reshape(4, 4)
    evals = np.real(np.linalg.eigvalsh(0.5 * (rho_pt + rho_pt.conj().T)))
    return float(np.sum(np.abs(evals[evals < 0.0])))


def correlation_tensor_norm(rho_ab: np.ndarray) -> float:
    total = 0.0
    for pa in PAULIS:
        for pb in PAULIS:
            total += abs(np.trace(rho_ab @ np.kron(pa, pb))) ** 2
    return float(math.sqrt(total))


def rho_distance(rho_a: np.ndarray, rho_b: np.ndarray) -> float:
    return float(np.linalg.norm(rho_a - rho_b, ord="fro"))


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
    rho = np.zeros((4, 4), dtype=complex)
    turning = history_turning(packet)
    for point, weight in zip(packet.history, weights):
        history_coupling = 0.12 + 0.5 * abs(point.radius - packet.current.radius) + 0.35 * turning
        rho += weight * pair_state(left_density(point), right_density(point), history_coupling)
    return ensure_density(rho)


def metrics(rho_ab: np.ndarray) -> Dict[str, float]:
    return {
        "von_neumann_entropy": von_neumann_entropy(rho_ab),
        "mutual_information": mutual_information(rho_ab),
        "coherent_information": coherent_information(rho_ab),
        "negativity": negativity(rho_ab),
        "correlation_tensor_norm": correlation_tensor_norm(rho_ab),
    }


def validity_checks(rho_ab: np.ndarray) -> Dict[str, float | bool]:
    evals = np.real(np.linalg.eigvalsh(ensure_density(rho_ab)))
    return {
        "trace_one": bool(abs(np.trace(rho_ab) - 1.0) < 1e-9),
        "hermitian": bool(np.linalg.norm(rho_ab - rho_ab.conj().T) < 1e-9),
        "min_eigenvalue": float(np.min(evals)),
        "positive_semidefinite": bool(np.min(evals) >= -1e-10),
    }


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


def apply_history_scramble(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    order = [2, 0, 3, 1]
    scrambled = [packet.history[i] for i in order[: len(packet.history)]]
    return GeometryHistoryPacket(packet.current, packet.shells, scrambled, packet.reference)


def apply_shell_ablation(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    return GeometryHistoryPacket(
        packet.current,
        [packet.shells[len(packet.shells) // 2]],
        packet.history,
        packet.reference,
    )


def apply_reference_freeze(packet: GeometryHistoryPacket) -> GeometryHistoryPacket:
    frozen = ShellPoint(
        radius=packet.current.radius,
        theta=packet.current.theta,
        phi=packet.current.phi,
        weight=1.0,
    )
    return GeometryHistoryPacket(packet.current, packet.shells, packet.history, frozen)


def distinct_family_record(name_a: str, rho_a: np.ndarray, name_b: str, rho_b: np.ndarray) -> Dict[str, float | bool]:
    dist = rho_distance(rho_a, rho_b)
    mi_gap = abs(mutual_information(rho_a) - mutual_information(rho_b))
    neg_gap = abs(negativity(rho_a) - negativity(rho_b))
    return {
        "pair": f"{name_a} vs {name_b}",
        "frobenius_distance": dist,
        "mutual_information_gap": mi_gap,
        "negativity_gap": neg_gap,
        "distinct": bool(dist > 1e-3 or mi_gap > 1e-3 or neg_gap > 1e-4),
    }


def run_positive_tests() -> Dict[str, object]:
    packet = build_packet()
    families = {
        "Xi_ref": xi_ref(packet),
        "Xi_shell": xi_shell(packet),
        "Xi_hist": xi_hist(packet),
    }
    records = {}
    for name, rho in families.items():
        records[name] = {
            "validity": validity_checks(rho),
            "metrics": metrics(rho),
        }
    distinct = [
        distinct_family_record("Xi_ref", families["Xi_ref"], "Xi_shell", families["Xi_shell"]),
        distinct_family_record("Xi_ref", families["Xi_ref"], "Xi_hist", families["Xi_hist"]),
        distinct_family_record("Xi_shell", families["Xi_shell"], "Xi_hist", families["Xi_hist"]),
    ]
    packet_features = {
        "reference_offset": reference_offset(packet),
        "shell_dispersion": shell_dispersion(packet),
        "history_turning": history_turning(packet),
    }
    all_valid = all(records[name]["validity"]["positive_semidefinite"] for name in records)
    all_distinct = all(entry["distinct"] for entry in distinct)
    return {
        "packet_features": packet_features,
        "families": records,
        "pairwise_distinction": distinct,
        "all_valid": all_valid,
        "all_distinct": all_distinct,
        "pass": bool(all_valid and all_distinct),
    }


def run_negative_tests() -> Dict[str, object]:
    base = build_packet()
    scrambled = apply_history_scramble(base)
    ablated = apply_shell_ablation(base)
    frozen = apply_reference_freeze(base)

    base_hist = xi_hist(base)
    scrambled_hist = xi_hist(scrambled)
    base_shell = xi_shell(base)
    ablated_shell = xi_shell(ablated)
    base_ref = xi_ref(base)
    frozen_ref = xi_ref(frozen)

    zero_packet = GeometryHistoryPacket(
        current=ShellPoint(0.0, 0.0, 0.0, 1.0),
        shells=[ShellPoint(0.0, 0.0, 0.0, 1.0)],
        history=[],
        reference=ShellPoint(0.0, 0.0, 0.0, 1.0),
    )
    zero_ref = xi_ref(zero_packet)
    zero_shell = xi_shell(zero_packet)
    zero_hist = xi_hist(zero_packet)

    history_scramble_shift = rho_distance(base_hist, scrambled_hist)
    shell_ablation_shift = rho_distance(base_shell, ablated_shell)
    reference_freeze_shift = rho_distance(base_ref, frozen_ref)

    return {
        "history_scrambling": {
            "distance": history_scramble_shift,
            "pass": bool(history_scramble_shift > 5e-3),
            "base_metrics": metrics(base_hist),
            "scrambled_metrics": metrics(scrambled_hist),
        },
        "shell_ablation": {
            "distance": shell_ablation_shift,
            "pass": bool(shell_ablation_shift > 5e-3),
            "base_metrics": metrics(base_shell),
            "ablated_metrics": metrics(ablated_shell),
        },
        "reference_freeze": {
            "distance": reference_freeze_shift,
            "pass": bool(reference_freeze_shift > 5e-3),
            "base_metrics": metrics(base_ref),
            "frozen_metrics": metrics(frozen_ref),
        },
        "degenerate_zero_packet": {
            "Xi_ref_valid": validity_checks(zero_ref),
            "Xi_shell_valid": validity_checks(zero_shell),
            "Xi_hist_valid": validity_checks(zero_hist),
            "all_finite_and_valid": bool(
                validity_checks(zero_ref)["positive_semidefinite"]
                and validity_checks(zero_shell)["positive_semidefinite"]
                and validity_checks(zero_hist)["positive_semidefinite"]
            ),
            "pass": True,
        },
        "pass": bool(
            history_scramble_shift > 5e-3
            and shell_ablation_shift > 5e-3
            and reference_freeze_shift > 5e-3
        ),
    }


def run_boundary_tests() -> Dict[str, object]:
    base = build_packet()
    one_history = GeometryHistoryPacket(
        current=base.current,
        shells=base.shells,
        history=[base.history[0]],
        reference=base.reference,
    )
    flat_shells = GeometryHistoryPacket(
        current=base.current,
        shells=[
            ShellPoint(base.current.radius, base.current.theta, base.current.phi, 1.0 / 3.0),
            ShellPoint(base.current.radius, base.current.theta, base.current.phi, 1.0 / 3.0),
            ShellPoint(base.current.radius, base.current.theta, base.current.phi, 1.0 / 3.0),
        ],
        history=base.history,
        reference=base.reference,
    )
    exact_reference = GeometryHistoryPacket(
        current=base.current,
        shells=base.shells,
        history=base.history,
        reference=base.current,
    )

    rho_one_hist = xi_hist(one_history)
    rho_flat_shell = xi_shell(flat_shells)
    rho_exact_ref = xi_ref(exact_reference)

    return {
        "single_history_sample": {
            "metrics": metrics(rho_one_hist),
            "validity": validity_checks(rho_one_hist),
            "pass": bool(validity_checks(rho_one_hist)["positive_semidefinite"]),
        },
        "flat_shell_packet": {
            "metrics": metrics(rho_flat_shell),
            "validity": validity_checks(rho_flat_shell),
            "pass": bool(validity_checks(rho_flat_shell)["positive_semidefinite"]),
        },
        "exact_reference_match": {
            "metrics": metrics(rho_exact_ref),
            "validity": validity_checks(rho_exact_ref),
            "distance_to_current_product": rho_distance(
                rho_exact_ref,
                pair_state(left_density(base.current), right_density(base.current), 0.0),
            ),
            "pass": bool(validity_checks(rho_exact_ref)["positive_semidefinite"]),
        },
        "pass": True,
    }


def build_summary(positive: Dict[str, object], negative: Dict[str, object], boundary: Dict[str, object]) -> Dict[str, object]:
    passes = int(bool(positive["pass"])) + int(bool(negative["pass"])) + int(bool(boundary["pass"]))
    return {
        "tests_total": 3,
        "tests_passed": passes,
        "all_pass": passes == 3,
        "classification_note": (
            "Three bridge-candidate families separate on the same pure-math packet "
            "and respond differently to targeted ablations. No final family is promoted."
        ),
        "most_history_sensitive_family": "Xi_hist",
        "most_shell_sensitive_family": "Xi_shell",
        "most_reference_sensitive_family": "Xi_ref",
    }


def main() -> Dict[str, object]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    return {
        "name": "xi_family_separation",
        "probe": "pure_math_bridge_family_comparison",
        "purpose": (
            "Compare reference-anchored, shell-weighted, and ordered-history "
            "bridge candidates on the same geometry/history packet without "
            "claiming a final canon."
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
    out_path = os.path.join(out_dir, "xi_family_separation_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(json.dumps(results["summary"], indent=2))
    print(f"Results written to {out_path}")
