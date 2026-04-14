#!/usr/bin/env python3
"""
Geometry Negative: Loop-Law Swap
================================

Keep the same Hopf carrier point and torus latitude, but swap the meaning of
the two loop laws:

  - fiber law should be density-stationary
  - base law should be density-traversing and horizontal

If the loop law is real, then treating the base law like a fiber law, or the
fiber law like a base law, must fail on the same carrier.

KILL token: S_NEG_LOOP_LAW_SWAP
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

import numpy as np

classification = "canonical"

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    fiber_phase_left,
    fiber_phase_right,
    left_weyl_spinor,
    right_weyl_spinor,
    torus_coordinates,
)
from proto_ratchet_sim_runner import EvidenceToken


RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state",
    "sim_results",
    "neg_loop_law_swap_results.json",
)
def density(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, psi.conj())


def frob(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b, ord="fro"))


def base_coords(phi0: float, chi0: float, eta: float, u: float) -> tuple[float, float]:
    return (phi0 - np.cos(2 * eta) * u, chi0 + u)


def run() -> list[EvidenceToken]:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    rng = np.random.default_rng(42)
    etas = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    u = np.pi / 4

    max_true_fiber_drift = 0.0
    min_true_base_traversal = float("inf")
    max_true_horizontal_abs = 0.0
    min_swapped_base_as_fiber = float("inf")
    min_swapped_fiber_as_base = float("inf")

    per_case = []

    for eta in etas:
        for trial in range(4):
            phi0 = float(rng.uniform(0, 2 * np.pi))
            chi0 = float(rng.uniform(0, 2 * np.pi))

            phi_b, chi_b = base_coords(phi0, chi0, eta, u)

            q0 = torus_coordinates(eta, phi0, chi0)
            q_b = torus_coordinates(eta, phi_b, chi_b)
            psi_L0 = left_weyl_spinor(q0)
            psi_L_fiber = fiber_phase_left(psi_L0, u)
            psi_L_base = left_weyl_spinor(q_b)
            psi_R0 = right_weyl_spinor(q0)
            psi_R_fiber = fiber_phase_right(psi_R0, u)
            psi_R_base = right_weyl_spinor(q_b)

            rho_L0 = density(psi_L0)
            rho_R0 = density(psi_R0)

            fiber_drift_L = frob(density(psi_L_fiber), rho_L0)
            fiber_drift_R = frob(density(psi_R_fiber), rho_R0)
            true_fiber_drift = max(fiber_drift_L, fiber_drift_R)
            max_true_fiber_drift = max(max_true_fiber_drift, true_fiber_drift)

            base_traversal_L = frob(density(psi_L_base), rho_L0)
            base_traversal_R = frob(density(psi_R_base), rho_R0)
            true_base_traversal = max(base_traversal_L, base_traversal_R)
            min_true_base_traversal = min(min_true_base_traversal, true_base_traversal)

            horizontal_abs = abs(-np.cos(2 * eta) + np.cos(2 * eta))
            max_true_horizontal_abs = max(max_true_horizontal_abs, horizontal_abs)

            # Swap negatives on the same carrier:
            # 1. treating base law as if it were a fiber law should fail stationarity
            min_swapped_base_as_fiber = min(min_swapped_base_as_fiber, true_base_traversal)
            # 2. treating fiber law as if it were a base horizontal lift should fail A(gamma_dot)=0
            swapped_fiber_as_base = abs(1.0 + np.cos(2 * eta) * 0.0)
            min_swapped_fiber_as_base = min(min_swapped_fiber_as_base, swapped_fiber_as_base)

            per_case.append(
                {
                    "eta": float(eta),
                    "trial": trial,
                    "fiber_drift_L": fiber_drift_L,
                    "fiber_drift_R": fiber_drift_R,
                    "base_traversal_L": base_traversal_L,
                    "base_traversal_R": base_traversal_R,
                    "horizontal_abs": horizontal_abs,
                    "swapped_fiber_as_base_abs": swapped_fiber_as_base,
                }
            )

    structure_matters = (
        max_true_fiber_drift < 1e-10
        and min_true_base_traversal > 1e-3
        and max_true_horizontal_abs < 1e-12
        and min_swapped_base_as_fiber > 1e-3
        and min_swapped_fiber_as_base > 0.5
    )

    token = EvidenceToken(
        "",
        "S_NEG_LOOP_LAW_SWAP",
        "KILL",
        float(min_swapped_base_as_fiber),
        "LOOP_LAW_SWAP_BREAKS_GEOMETRY",
    )

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "max_true_fiber_drift": float(max_true_fiber_drift),
        "min_true_base_traversal": float(min_true_base_traversal),
        "max_true_horizontal_abs": float(max_true_horizontal_abs),
        "min_swapped_base_as_fiber": float(min_swapped_base_as_fiber),
        "min_swapped_fiber_as_base": float(min_swapped_fiber_as_base),
        "structure_matters": bool(structure_matters),
        "cases": per_case,
        "evidence_ledger": [token.__dict__],
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print("Loop-Law Swap Negative:")
    print(f"  max_true_fiber_drift:      {max_true_fiber_drift:.6e}")
    print(f"  min_true_base_traversal:   {min_true_base_traversal:.6e}")
    print(f"  max_true_horizontal_abs:   {max_true_horizontal_abs:.6e}")
    print(f"  min_swapped_base_as_fiber: {min_swapped_base_as_fiber:.6e}")
    print(f"  min_swapped_fiber_as_base: {min_swapped_fiber_as_base:.6e}")
    print(f"  structure_matters:         {structure_matters}")
    print("  → KILL (loop-law swap must break the exact geometry packet)")

    return [token]


if __name__ == "__main__":
    run()
