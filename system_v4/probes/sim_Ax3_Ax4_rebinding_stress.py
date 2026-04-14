#!/usr/bin/env python3
"""
sim_Ax3_Ax4_rebinding_stress.py
================================

Lane B discriminator for the Weyl-manifold shift.

Purpose
-------
Stress-test whether the current Ax3 / Ax4 bindings remain robust when
the engine is treated as DOF on Weyl ambient geometry rather than as the
deepest available structure.

Conservative read:
  - PASS means the current bindings survive this ambient-sheet stress test.
  - PASS does NOT mean the bindings are metaphysically final.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, datetime

import numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

from geometric_operators import _ensure_valid_density, trace_distance_2x2
from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    left_density,
    right_density,
    torus_coordinates,
)
from proto_ratchet_sim_runner import EvidenceToken
from sim_Ax4_commutation import apply_EUEU, apply_UEUE


RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "Ax3_Ax4_rebinding_stress_results.json",
)

AMBIENT_SAMPLES = [
    (0.0, 0.0),
    (0.3, 0.1),
    (0.7, 0.2),
    (1.1, 0.4),
]


def spinor(phi: float, chi: float, eta: float) -> np.ndarray:
    return np.array(
        [
            np.exp(1j * (phi + chi)) * np.cos(eta),
            np.exp(1j * (phi - chi)) * np.sin(eta),
        ],
        dtype=complex,
    )


def density(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, psi.conj())


def fiber_path(phi0: float, chi0: float, eta0: float, n_steps: int = 64) -> list[np.ndarray]:
    us = np.linspace(0, 2 * np.pi, n_steps, endpoint=False)
    return [density(spinor(phi0 + u, chi0, eta0)) for u in us]


def base_path(phi0: float, chi0: float, eta0: float, n_steps: int = 64) -> list[np.ndarray]:
    c2 = np.cos(2 * eta0)
    us = np.linspace(0, 2 * np.pi, n_steps, endpoint=False)
    return [density(spinor(phi0 - c2 * u, chi0 + u, eta0)) for u in us]


def max_deviation_from_start(path: list[np.ndarray]) -> float:
    rho0 = path[0]
    return float(max(trace_distance_2x2(rho, rho0) for rho in path[1:]))


def vn_entropy(rho: np.ndarray) -> float:
    vals = np.real(np.linalg.eigvalsh((rho + rho.conj().T) / 2))
    vals = vals[vals > 1e-15]
    return float(-np.sum(vals * np.log(vals))) if len(vals) else 0.0


def path_class_case(name: str, eta: float) -> dict:
    phi0 = 0.0
    chi0 = 0.0
    fiber = fiber_path(phi0, chi0, eta)
    base = base_path(phi0, chi0, eta)
    fiber_dev = max_deviation_from_start(fiber)
    base_dev = max_deviation_from_start(base)

    # Ambient Weyl sheet samples at the same torus point.
    q = torus_coordinates(eta, phi0, chi0)
    rho_L = left_density(q)
    rho_R = right_density(q)
    sheet_dist = trace_distance_2x2(rho_L, rho_R)

    fiber_ok = fiber_dev < 1e-10
    base_ok = base_dev > 1e-6
    return {
        "torus": name,
        "eta": float(eta),
        "fiber_max_deviation": fiber_dev,
        "base_max_deviation": base_dev,
        "weyl_sheet_trace_distance": float(sheet_dist),
        "fiber_stationary": fiber_ok,
        "base_traversing": base_ok,
        "pass": fiber_ok and base_ok,
    }


def ordering_metrics(eta: float, phi: float, chi: float) -> dict:
    q = torus_coordinates(eta, phi, chi)
    rho_L = _ensure_valid_density(left_density(q))
    rho_R = _ensure_valid_density(right_density(q))

    left_ueue = apply_UEUE(rho_L.copy())
    left_eueu = apply_EUEU(rho_L.copy())
    right_ueue = apply_UEUE(rho_R.copy())
    right_eueu = apply_EUEU(rho_R.copy())

    left_dist = trace_distance_2x2(left_ueue, left_eueu)
    right_dist = trace_distance_2x2(right_ueue, right_eueu)
    return {
        "phi": float(phi),
        "chi": float(chi),
        "left_trace_distance": float(left_dist),
        "right_trace_distance": float(right_dist),
        "left_entropy_gap": float(abs(vn_entropy(left_ueue) - vn_entropy(left_eueu))),
        "right_entropy_gap": float(abs(vn_entropy(right_ueue) - vn_entropy(right_eueu))),
        "left_ordering_distinguishable": bool(left_dist > 1e-4),
        "right_ordering_distinguishable": bool(right_dist > 1e-4),
    }


def ordering_case(name: str, eta: float) -> dict:
    sample_metrics = [ordering_metrics(eta, phi, chi) for phi, chi in AMBIENT_SAMPLES]
    nontrivial_samples = [
        m for m in sample_metrics if m["left_ordering_distinguishable"] and m["right_ordering_distinguishable"]
    ]
    anchor = sample_metrics[0]
    anchor_degenerate = not anchor["left_ordering_distinguishable"] and not anchor["right_ordering_distinguishable"]
    pass_case = len(nontrivial_samples) >= 1
    symmetry_note = ""
    if anchor_degenerate and pass_case:
        symmetry_note = "Exact neutral anchor is degenerate, but perturbed ambient samples remain ordering-distinguishable."

    return {
        "torus": name,
        "eta": float(eta),
        "samples": sample_metrics,
        "nontrivial_sample_count": len(nontrivial_samples),
        "anchor_degenerate": anchor_degenerate,
        "symmetry_note": symmetry_note,
        "pass": pass_case,
    }


def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    print("=" * 72)
    print("AX3 / AX4 REBINDING STRESS TEST")
    print("=" * 72)

    torus_cases = [
        ("inner", TORUS_INNER),
        ("clifford", TORUS_CLIFFORD),
        ("outer", TORUS_OUTER),
    ]

    ax3_cases = [path_class_case(name, eta) for name, eta in torus_cases]
    ax4_cases = [ordering_case(name, eta) for name, eta in torus_cases]

    ax3_pass_count = sum(int(c["pass"]) for c in ax3_cases)
    ax4_pass_count = sum(int(c["pass"]) for c in ax4_cases)
    overall_pass = ax3_pass_count == len(ax3_cases) and ax4_pass_count == len(ax4_cases)

    summary = {
        "ax3_pass_count": ax3_pass_count,
        "ax4_pass_count": ax4_pass_count,
        "ax3_total": len(ax3_cases),
        "ax4_total": len(ax4_cases),
    }

    verdict = {
        "result": "PASS" if overall_pass else "KILL",
        "read": (
            "Current Ax3 fiber/base and Ax4 ordering bindings remain robust under this Weyl-sheet ambient stress test."
            if overall_pass
            else
            "Current Ax3/Ax4 bindings do not survive this Weyl-sheet ambient stress test cleanly."
        ),
    }

    token = EvidenceToken(
        token_id="E_SIM_AX3_AX4_REBINDING_STRESS_OK" if overall_pass else "",
        sim_spec_id="S_SIM_AX3_AX4_REBINDING_STRESS",
        status="PASS" if overall_pass else "KILL",
        measured_value=float(ax3_pass_count + ax4_pass_count),
        kill_reason=None if overall_pass else "AX3_AX4_BINDINGS_NOT_ROBUST_UNDER_WEYL_STRESS",
    )

    results = {
        "metadata": {
            "name": "Ax3_Ax4_rebinding_stress",
            "timestamp": datetime.now(UTC).isoformat(),
            "results_path": RESULTS_PATH,
        },
        "cases": {
            "ax3_path_class": ax3_cases,
            "ax4_ordering": ax4_cases,
        },
        "summary": summary,
        "verdict": verdict,
        "evidence_token": asdict(token),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nSummary")
    print(f"  Ax3 pass count: {ax3_pass_count}/{len(ax3_cases)}")
    print(f"  Ax4 pass count: {ax4_pass_count}/{len(ax4_cases)}")
    print("\nVerdict")
    print(f"  {verdict['result']}: {verdict['read']}")
    print(f"\nResults saved: {RESULTS_PATH}")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
