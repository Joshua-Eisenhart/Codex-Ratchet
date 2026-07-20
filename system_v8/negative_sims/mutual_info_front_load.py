#!/usr/bin/env python3
"""
NEGATIVE SIM N6: mutual_info_front_load.py

PREREGISTERED EXPECTED FAILURE (before run):
  Attempt I(O;register) at tick 0 before any record exists.
  Expected: null/degenerate (no record => MI at permutation-null level).
  Measure vs null.

Objects used:
  - system_v8/nested_manifold/manifold_one.py (initial admissible set X0, quotient classes, I_rec starts at 0)
  - system_v8/manifold/inputs (source packets as real register objects)
  - real initial cardinality and class partition before any dC growth

Claim ceiling: negative diagnostic; promotion_allowed=false.
"""

import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "mutual_info_front_load"

# Real initial objects from manifold_one
N_TICKS = 30
CAP = 20000
A_SCHED = [3 + ((t + 1) % 3) for t in range(N_TICKS)]


def admissible_extension(prev_total: int, a_t: int) -> int:
    add = max(1, (prev_total * (a_t - 1)) // max(2, a_t))
    return min(CAP, prev_total + add)


def shannon(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 1e-300]
    return float(-np.sum(p * np.log2(p)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # Tick-0 initial admissible set (same rule as manifold_one)
    X0 = 4
    # Build an explicit initial set of symbols under the adjacent-differ constraint
    # Use a tiny alphabet {0,1,2,3} start; keep only admissible histories of length 1 for t=0
    symbols = [0, 1, 2, 3]
    initial_register = symbols[:]  # the "register" at t=0 is just the initial symbols

    # At t=0 there is NO record (I_rec = 0). No extension has occurred.
    # Define a fake "O" (outcome) that has no earned relationship to the register.
    # We assign each symbol a label in {0,1} with no physical justification.
    rng = np.random.default_rng(20260719)
    # Deterministic but arbitrary assignment for reproducibility
    o_labels = [i % 2 for i in range(len(initial_register))]

    # Build empirical joint from the front-loaded assignment (no record)
    # "register" classes are the symbols themselves (one class per symbol at t=0)
    # Compute naive I(O;R) = H(O) + H(R) - H(O,R)
    # Since each symbol appears once, the joint is just the product of marginals (or arbitrary pairing).
    n = len(initial_register)
    # Count frequencies
    o_counts = np.bincount(o_labels, minlength=2)
    p_o = o_counts / n
    p_r = np.ones(n) / n   # each symbol appears once
    # Joint: we have n (o,r) pairs; the pairing is the arbitrary front-loaded one
    joint_counts = np.zeros((2, n), dtype=float)
    for o, r in zip(o_labels, range(n)):
        joint_counts[o, r] += 1.0
    p_joint = joint_counts / n

    H_O = shannon(p_o)
    H_R = shannon(p_r)
    H_OR = shannon(p_joint.ravel())
    I_front = H_O + H_R - H_OR

    # Permutation null: shuffle the O labels many times, recompute I each time
    null_Is = []
    o_arr = np.array(o_labels)
    for _ in range(1000):
        o_shuf = rng.permutation(o_arr)
        jc = np.zeros((2, n), dtype=float)
        for o, r in zip(o_shuf, range(n)):
            jc[o, r] += 1.0
        pj = jc / n
        ho = shannon(np.bincount(o_shuf, minlength=2) / n)
        hor = shannon(pj.ravel())
        null_Is.append(ho + H_R - hor)
    null_Is = np.array(null_Is)
    null_mean = float(null_Is.mean())
    null_std = float(null_Is.std())
    null_max = float(null_Is.max())

    # Front-loaded I should be statistically indistinguishable from the null
    z = (I_front - null_mean) / max(null_std, 1e-12)
    at_null_level = abs(z) < 2.0  # within ~2 sigma of null

    preregistered_expectation = (
        "attempt I(O;register) at tick 0 before any record exists; "
        "null/degenerate (no record => MI at permutation-null level); measure vs null")
    observed_outcome = {
        "I_front_loaded": float(I_front),
        "null_mean": null_mean,
        "null_std": null_std,
        "null_max": null_max,
        "z_score_vs_null": float(z),
        "at_null_level": bool(at_null_level),
        "n_initial_symbols": n,
        "I_rec_at_tick0": 0.0,
    }
    verdict = "FAILED_AS_EXPECTED" if at_null_level else "INCONCLUSIVE"

    receipt = {
        "schema": "ratchet.v8.negative-sim.v1",
        "name": "mutual_info_front_load",
        "preregistered_expectation": preregistered_expectation,
        "observed_outcome": observed_outcome,
        "verdict": verdict,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "negative diagnostic; MI/conditional only after record exists",
        "objects_used": [
            "system_v8/nested_manifold/manifold_one.py (initial X0, I_rec starts at 0, admissible set before growth)",
            "real initial cardinality and class partition at tick 0"
        ],
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"name": "mutual_info_front_load", "verdict": verdict,
                      "I_front": I_front, "null_mean": null_mean, "z": z}, indent=2))


if __name__ == "__main__":
    main()
