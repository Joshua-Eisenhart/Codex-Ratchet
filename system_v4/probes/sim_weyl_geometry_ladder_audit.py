#!/usr/bin/env python3
"""
sim_weyl_geometry_ladder_audit.py
=================================

Lane C discriminator for the Weyl-manifold shift.

Purpose
-------
Audit the first Weyl-specific rung in the proposed geometry ladder:

    nested Hopf tori -> Weyl ambient sheets -> engine DOF

This is not a full doctrine audit. It asks one bounded question:

- does the Weyl-ambient rung have an independent witness before it is folded
  into engine dynamics or bridge language?

Conservative read:
- PASS means the rung has a detectable ambient witness that is not just the
  same scalar signal as engine response.
- KILL means the Weyl-ambient rung is still only naming / overlay under this
  discriminator.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, datetime

import numpy as np

from engine_core import GeometricEngine
from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    berry_phase,
    left_density,
    right_density,
    sample_fiber,
    torus_coordinates,
)
from proto_ratchet_sim_runner import EvidenceToken


RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "weyl_geometry_ladder_audit_results.json",
)


def von_neumann_entropy(rho: np.ndarray) -> float:
    vals = np.real(np.linalg.eigvalsh((rho + rho.conj().T) / 2))
    vals = vals[vals > 1e-15]
    return float(-np.sum(vals * np.log2(vals))) if len(vals) else 0.0


def partial_trace_A(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def mutual_information(rho_ab: np.ndarray) -> float:
    rho_a = partial_trace_B(rho_ab)
    rho_b = partial_trace_A(rho_ab)
    return float(von_neumann_entropy(rho_a) + von_neumann_entropy(rho_b) - von_neumann_entropy(rho_ab))


def torus_base_loop(eta: float, n_points: int = 128) -> np.ndarray:
    points = []
    for k in range(n_points):
        u = 2.0 * np.pi * k / n_points
        theta1 = 2.0 * (np.sin(eta) ** 2) * u
        theta2 = -2.0 * (np.cos(eta) ** 2) * u
        points.append(torus_coordinates(eta, theta1, theta2))
    return np.asarray(points)


def ambient_geometry_case(name: str, eta: float) -> dict:
    q0 = torus_coordinates(eta, 0.0, 0.0)
    fiber_loop = sample_fiber(q0, 128)
    base_loop = torus_base_loop(eta, 128)
    fiber_phase = float(berry_phase(fiber_loop))
    base_phase = float(berry_phase(base_loop))
    berry_gap = float(abs(base_phase - fiber_phase))

    rho_pair = np.kron(left_density(q0), right_density(q0))
    raw_lr_mi = float(mutual_information(rho_pair))

    return {
        "torus": name,
        "eta": float(eta),
        "fiber_berry_phase": fiber_phase,
        "base_berry_phase": base_phase,
        "berry_gap": berry_gap,
        "raw_LR_mutual_information": raw_lr_mi,
    }


def engine_case(engine_type: int, eta: float) -> dict:
    engine = GeometricEngine(engine_type=engine_type)
    state0 = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
    axes_before = engine.read_axes(state0)
    state1 = engine.run_cycle(state0)
    axes_after = engine.read_axes(state1)
    axis_delta_l2 = float(
        np.linalg.norm(
            np.array([axes_after[k] - axes_before[k] for k in sorted(axes_before.keys())], dtype=float)
        )
    )
    return {
        "engine_type": int(engine_type),
        "axis_delta_l2": axis_delta_l2,
        "axes_before": {k: float(v) for k, v in axes_before.items()},
        "axes_after": {k: float(v) for k, v in axes_after.items()},
    }


def max_pairwise_difference(values: list[float]) -> float:
    best = 0.0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            best = max(best, abs(values[i] - values[j]))
    return float(best)


def normalize(values: list[float]) -> list[float]:
    arr = np.asarray(values, dtype=float)
    span = float(np.max(arr) - np.min(arr))
    if span < 1e-12:
        return [0.0 for _ in values]
    return [float((x - np.min(arr)) / span) for x in arr]


def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    print("=" * 72)
    print("WEYL GEOMETRY LADDER AUDIT")
    print("=" * 72)

    torus_cases = [
        ("inner", TORUS_INNER),
        ("clifford", TORUS_CLIFFORD),
        ("outer", TORUS_OUTER),
    ]

    ambient_cases = [ambient_geometry_case(name, eta) for name, eta in torus_cases]
    engine_cases = [
        {
            "torus": name,
            "eta": float(eta),
            "engine_type_1": engine_case(1, eta),
            "engine_type_2": engine_case(2, eta),
        }
        for name, eta in torus_cases
    ]

    berry_gaps = [case["berry_gap"] for case in ambient_cases]
    engine_type1_deltas = [case["engine_type_1"]["axis_delta_l2"] for case in engine_cases]
    engine_type_diff = [
        abs(case["engine_type_1"]["axis_delta_l2"] - case["engine_type_2"]["axis_delta_l2"])
        for case in engine_cases
    ]
    raw_lr_mis = [case["raw_LR_mutual_information"] for case in ambient_cases]

    ambient_nontrivial = sum(int(gap > 0.1) for gap in berry_gaps)
    clifford_neutral = ambient_cases[1]["berry_gap"] < 1e-6
    engine_nontrivial = max_pairwise_difference(engine_type1_deltas) > 1e-3
    overlay_nontrivial = max_pairwise_difference(engine_type_diff) > 1e-4

    ambient_norm = normalize(berry_gaps)
    engine_norm = normalize(engine_type1_deltas)
    witness_separable = max(abs(a - b) for a, b in zip(ambient_norm, engine_norm)) > 0.2
    guardrail_ok = max(abs(v) for v in raw_lr_mis) < 1e-9

    overall_pass = ambient_nontrivial >= 2 and clifford_neutral and engine_nontrivial and overlay_nontrivial and witness_separable and guardrail_ok

    summary = {
        "ambient_nontrivial_count": int(ambient_nontrivial),
        "clifford_neutral": bool(clifford_neutral),
        "engine_nontrivial": bool(engine_nontrivial),
        "overlay_nontrivial": bool(overlay_nontrivial),
        "witness_separable": bool(witness_separable),
        "guardrail_pass": bool(guardrail_ok),
        "berry_gap_vector": berry_gaps,
        "engine_type1_axis_delta_vector": engine_type1_deltas,
        "engine_type_difference_vector": engine_type_diff,
        "ambient_norm_vector": ambient_norm,
        "engine_norm_vector": engine_norm,
    }

    verdict = {
        "result": "PASS" if overall_pass else "KILL",
        "read": (
            "The Weyl-ambient rung has an independent witness: geometric holonomy varies across the torus ladder, engine response varies too, and the two signatures are not the same signal."
            if overall_pass
            else
            "The Weyl-ambient rung does not yet show an independent witness under this ladder audit; it still risks collapsing into overlay or naming."
        ),
    }

    token = EvidenceToken(
        token_id="E_SIM_WEYL_GEOMETRY_LADDER_OK" if overall_pass else "",
        sim_spec_id="S_SIM_WEYL_GEOMETRY_LADDER_AUDIT",
        status="PASS" if overall_pass else "KILL",
        measured_value=float(ambient_nontrivial + int(engine_nontrivial) + int(overlay_nontrivial) + int(witness_separable)),
        kill_reason=None if overall_pass else "WEYL_AMBIENT_RUNG_NOT_INDEPENDENTLY_WITNESSED",
    )

    results = {
        "metadata": {
            "name": "weyl_geometry_ladder_audit",
            "timestamp": datetime.now(UTC).isoformat(),
            "results_path": RESULTS_PATH,
        },
        "rungs": {
            "nested_hopf_tori_to_geometry": ambient_cases,
            "weyl_ambient_to_engine_dof": engine_cases,
        },
        "summary": summary,
        "verdict": verdict,
        "evidence_token": asdict(token),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nSummary")
    print(f"  Ambient nontrivial torus cases: {ambient_nontrivial}/3")
    print(f"  Clifford neutral witness: {clifford_neutral}")
    print(f"  Engine nontrivial across torus ladder: {engine_nontrivial}")
    print(f"  Engine-type overlay difference present: {overlay_nontrivial}")
    print(f"  Ambient/engine witnesses separable: {witness_separable}")
    print(f"  Max raw L|R MI at init: {max(abs(v) for v in raw_lr_mis):.6e}")
    print("\nVerdict")
    print(f"  {verdict['result']}: {verdict['read']}")
    print(f"\nResults saved: {RESULTS_PATH}")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
