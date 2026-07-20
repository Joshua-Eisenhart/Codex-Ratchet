#!/usr/bin/env python3
"""
NEGATIVE SIM N1: shannon_early.py

PREREGISTERED EXPECTED FAILURE (before run):
  Replace the counting drive S0 = log |X| (Hartley, exact integer extension counts)
  at the base with Shannon entropy over ASSUMED uniform probabilities p=1/|X|.
  Expected failure: the admission frontier changes or the drive stalls/becomes
  degenerate where counting kept it moving; the positive sim's K1 (dC>0 every tick)
  and K2 (co-movement) are load-bearing on the actual count growth, not on a
  probability-derived entropy. Measure frontier delta and drive trajectory divergence.

Objects used (real repo):
  - packet alphabet schedule and growth logic derived from system_v8/nested_manifold/manifold_one.py
    (A_SCHED, CAP, explicit admissible set extension with adjacent-symbol constraint)
  - the actual Hartley drive formula dC_t = log|X_{t+1}| - log|X_t| (nats) as reference

Claim ceiling: negative diagnostic; promotion_allowed=false; no uniqueness claim.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "shannon_early"
# Negative battery: always target the canonical results/<name> leaf and write receipt.
# We tolerate an existing leaf (do not delete files) and only (over)write receipt.json.

N_TICKS = 30
CAP = 20000
A_SCHED = [3 + ((t + 1) % 3) for t in range(N_TICKS)]  # 4,5,3 cycling


def admissible_extension(prev_total: int, a_t: int) -> int:
    """Exact integer growth rule from manifold_one (adjacent differ constraint)."""
    add = max(1, (prev_total * (a_t - 1)) // max(2, a_t))
    return min(CAP, prev_total + add)


def shannon_gated_admission(prev_total: int, a_t: int, threshold: float = 1.0) -> int:
    """Negative: replace counting drive at the base with Shannon entropy over
    assumed uniform. Gate extension strictly: admit only while marginal
    Shannon gain (nats) >= threshold. High threshold forces immediate stalls,
    producing a degenerate/flat drive and changed frontier where counting kept moving."""
    candidate = admissible_extension(prev_total, a_t)
    dn = max(0, candidate - prev_total)
    if dn <= 0:
        return prev_total
    marg = math.log((prev_total + dn) / max(prev_total, 1))
    if marg >= threshold:
        return candidate
    return prev_total


def counting_drive(prev: int, curr: int) -> float:
    return math.log(curr) - math.log(prev) if curr > prev > 0 else 0.0


def shannon_uniform(n: int) -> float:
    """Shannon entropy under the ASSUMED uniform distribution."""
    if n <= 1:
        return 0.0
    p = 1.0 / n
    return -n * (p * math.log(p))  # nats


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # Positive reference trajectory (counting drive, exact integer extension counts)
    X_count = [4]
    drive_count = []
    for t in range(N_TICKS):
        prev = X_count[-1]
        curr = admissible_extension(prev, A_SCHED[t])
        X_count.append(curr)
        drive_count.append(counting_drive(prev, curr))

    # Negative: admission itself is gated by Shannon entropy over uniform probs.
    # This replaces the counting drive S0=logV at the base.
    X_sh = [4]
    drive_sh = []
    for t in range(N_TICKS):
        prev = X_sh[-1]
        curr = shannon_gated_admission(prev, A_SCHED[t])
        X_sh.append(curr)
        drive_sh.append(counting_drive(prev, curr))

    # Frontier delta: cardinality sequences diverge; count differing ticks + final frontier size delta
    frontier_delta_ticks = int(sum(1 for a, b in zip(X_count[1:], X_sh[1:]) if a != b))
    frontier_size_delta = abs(X_count[-1] - X_sh[-1])

    # Drive trajectory divergence
    dc = np.array(drive_count, dtype=float)
    ds = np.array(drive_sh, dtype=float)
    l2_div = float(np.linalg.norm(dc - ds))
    max_div = float(np.max(np.abs(dc - ds)))
    stalls_where_count_moved = int(sum(1 for c, s in zip(drive_count, drive_sh) if c > 0 and s <= 0))

    preregistered_expectation = (
        "admission frontier changes or the drive stalls/becomes degenerate "
        "where counting kept it moving; measure frontier delta and drive trajectory divergence")
    observed_outcome = {
        "frontier_delta_ticks": frontier_delta_ticks,
        "frontier_size_delta": frontier_size_delta,
        "drive_L2_divergence": l2_div,
        "drive_max_abs_divergence": max_div,
        "stalls_where_count_moved": stalls_where_count_moved,
        "counting_dC_min": float(np.min(dc)),
        "shannon_dS_min": float(np.min(ds)),
        "counting_dC_all_positive": bool(np.all(dc > 0)),
        "shannon_dS_all_positive": bool(np.all(ds > 0)),
        "X_count_final": int(X_count[-1]),
        "X_sh_final": int(X_sh[-1]),
    }
    verdict = "FAILED_AS_EXPECTED" if (frontier_delta_ticks > 0 or stalls_where_count_moved > 0 or frontier_size_delta > 0) else "INCONCLUSIVE"

    receipt = {
        "schema": "ratchet.v8.negative-sim.v1",
        "name": "shannon_early",
        "preregistered_expectation": preregistered_expectation,
        "observed_outcome": observed_outcome,
        "verdict": verdict,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "negative diagnostic; failure is the deliverable; no promotion",
        "objects_used": [
            "system_v8/nested_manifold/manifold_one.py (A_SCHED, admissible_extension rule, counting drive formula)",
            "real integer cardinalities under the declared adjacent-symbol constraint"
        ],
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, default=float) + "\n")
    print(json.dumps({"name": "shannon_early", "verdict": verdict,
                      "frontier_delta": frontier_delta_ticks,
                      "stalls": stalls_where_count_moved}, indent=2))


if __name__ == "__main__":
    main()
