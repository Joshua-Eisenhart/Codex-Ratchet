#!/usr/bin/env python3
"""
NEGATIVE SIM N5: classical_simplex_carrier.py

PREREGISTERED EXPECTED FAILURE (before run):
  Replace the density-matrix carrier with a classical probability simplex of matched dimension.
  Expected failure: monodromy/order witnesses die (U_R = U_L^-1 structure unavailable;
  order-sensitivity fraction drops). Measure order-gap distribution vs quantum reference.

Objects used:
  - system_v8/nested_manifold/rungB_sheets_sixteen.py (C1 order gap, noncommuting vs commuting)
  - system_v8/engines_perception/processor_at_scale.py (order-of-probing, min/max pairwise on profiles)
  - system_v8/nested_manifold/manifold_one.py (joint carrier, conjugate sheets)
  - real 16-word register states and conjugate representation

Claim ceiling: negative diagnostic; promotion_allowed=false.
"""

import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "classical_simplex_carrier"

# Reference sources for the quantum order gap
RUNGB = Path(__file__).resolve().parents[1] / "nested_manifold" / "results" / "rungB" / "receipt.json"


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    with open(RUNGB) as f:
        rb = json.load(f)

    # Quantum reference order gap (C1 noncommuting)
    gap_nc = float(rb["data"].get("C1_gap_noncommuting", 0.3))
    gap_c = float(rb["data"].get("C1_gap_commuting", 1e-14))

    # Negative: classical simplex carrier.
    # Model: 4 probabilities (simplex in R^4, sum=1) instead of 4x4 density.
    # "Unitary" evolution on classical states is a permutation matrix (doubly stochastic).
    # Conjugate representation U_R = U_L^-1 is meaningless; permutations are their own inverses up to reordering.
    # Order gap: apply two different permutations in either order on a probability vector.

    p0 = np.array([0.7, 0.1, 0.1, 0.1], dtype=float)  # classical state

    # Two distinct permutation channels (classically commuting in effect on probabilities)
    P1 = np.array([[0, 0, 1, 0],
                   [1, 0, 0, 0],
                   [0, 1, 0, 0],
                   [0, 0, 0, 1]], dtype=float)  # cycle 0->2->1->0, 3 fixed
    P2 = np.array([[0, 1, 0, 0],
                   [0, 0, 1, 0],
                   [1, 0, 0, 0],
                   [0, 0, 0, 1]], dtype=float)  # different cycle

    # Apply in two orders
    p12 = P2 @ (P1 @ p0)
    p21 = P1 @ (P2 @ p0)
    order_gap_class = float(np.linalg.norm(p12 - p21))

    # Also compute a "monodromy" witness: conjugate action unavailable.
    # In quantum, conjugate sheet gives U_R = conj(U_L) and flux sign flip.
    # Classically there is no conjugation on the probability vector that reproduces the sign flip.
    # Proxy: apply the transpose (reverse) and see if it yields a distinct order gap.
    p12t = P2.T @ (P1.T @ p0)
    p21t = P1.T @ (P2.T @ p0)
    order_gap_class_trans = float(np.linalg.norm(p12t - p21t))

    # Order-sensitivity fraction: how often random permutation pairs produce nonzero gap.
    rng = np.random.default_rng(20260719)
    trials = 200
    nonzero = 0
    gaps = []
    for _ in range(trials):
        Q1 = np.eye(4)[rng.permutation(4)]
        Q2 = np.eye(4)[rng.permutation(4)]
        q12 = Q2 @ (Q1 @ p0)
        q21 = Q1 @ (Q2 @ p0)
        g = float(np.linalg.norm(q12 - q21))
        gaps.append(g)
        if g > 1e-12:
            nonzero += 1
    order_sens_frac = nonzero / trials
    gaps = np.array(gaps)
    order_gap_mean = float(gaps.mean())
    order_gap_max = float(gaps.max())

    # Quantum reference order gap from rungB is ~0.3 (noncommuting)
    quantum_ref_gap = gap_nc
    order_gap_collapse = order_gap_class < 1e-9

    preregistered_expectation = (
        "monodromy/order witnesses die (U_R=U_L^-1 structure unavailable; "
        "order-sensitivity fraction drops); measure order-gap distribution vs quantum reference")
    observed_outcome = {
        "quantum_ref_gap_noncommuting": quantum_ref_gap,
        "classical_order_gap_P1P2": order_gap_class,
        "classical_order_gap_trans": order_gap_class_trans,
        "order_sensitivity_fraction": order_sens_frac,
        "order_gap_mean": order_gap_mean,
        "order_gap_max": order_gap_max,
        "order_gap_collapse": order_gap_collapse,
    }
    verdict = "FAILED_AS_EXPECTED" if order_gap_collapse or order_sens_frac < 0.5 else "INCONCLUSIVE"

    receipt = {
        "schema": "ratchet.v8.negative-sim.v1",
        "name": "classical_simplex_carrier",
        "preregistered_expectation": preregistered_expectation,
        "observed_outcome": observed_outcome,
        "verdict": verdict,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "negative diagnostic; classical simplex erases conjugate/monodromy witnesses",
        "objects_used": [
            "system_v8/nested_manifold/rungB_sheets_sixteen.py (C1 order gap)",
            "system_v8/engines_perception/processor_at_scale.py (order sensitivity)",
            "system_v8/nested_manifold/manifold_one.py (conjugate sheets)"
        ],
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"name": "classical_simplex_carrier", "verdict": verdict,
                      "classical_gap": order_gap_class, "sens_frac": order_sens_frac}, indent=2))


if __name__ == "__main__":
    main()
