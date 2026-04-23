#!/usr/bin/env python3
"""
Axis Triplet Orthogonality SIM
==============================
Maps 3-axis independence for all C(6,3) triplets using the canonical
superoperators from axis_orthogonality_suite.py.

This is deliberately deeper than the pairwise sweep:
- pairwise overlap can look acceptable while a 3-axis family is rank-deficient
- we therefore test triplet rank and conditioning directly
- a triplet only counts as structurally valid if its three Choi operators remain
  linearly independent across dimensions
"""

import json
import os
from datetime import datetime, UTC
from itertools import combinations

import numpy as np

from proto_ratchet_sim_runner import EvidenceToken
from axis_orthogonality_suite import AXES, build_choi, hs_inner


RESULTS_NAME = "axis_triplet_orthogonality_results.json"
DIMS = [4, 8]
RANK_EPS = 1e-6
COND_CAP = 1e8


def triplet_metrics(axis_names, d):
    chois = [build_choi(AXES[name], d) for name in axis_names]
    flat = np.stack([c.flatten() for c in chois], axis=0)
    gram = np.zeros((3, 3), dtype=float)

    for i in range(3):
        for j in range(3):
            gram[i, j] = float(hs_inner(chois[i], chois[j]))

    sing_vals = np.linalg.svd(flat, compute_uv=False)
    rank = int(np.sum(sing_vals > RANK_EPS))
    min_sv = float(np.min(sing_vals))
    max_sv = float(np.max(sing_vals))
    cond = float(max_sv / max(min_sv, 1e-30))
    max_offdiag = float(
        np.max(np.abs(gram - np.diag(np.diag(gram))))
    )
    independent = rank == 3 and cond < COND_CAP

    return {
        "triplet": list(axis_names),
        "dimension": d,
        "rank": rank,
        "min_singular_value": min_sv,
        "max_singular_value": max_sv,
        "condition_number": cond,
        "max_pairwise_overlap": max_offdiag,
        "gram_matrix": gram.tolist(),
        "status": "PASS" if independent else "KILL",
    }


def run_triplet_sweep():
    triplets = list(combinations(sorted(AXES.keys()), 3))
    measurements = []
    tokens = []

    print("=" * 72)
    print("AXIS TRIPLET ORTHOGONALITY SWEEP")
    print(f"  dimensions={DIMS}  triplets={len(triplets)}")
    print("=" * 72)

    for axis_names in triplets:
        label = " x ".join(axis_names)
        triplet_ok = True
        worst_cond = 0.0
        worst_overlap = 0.0

        for d in DIMS:
            metric = triplet_metrics(axis_names, d)
            measurements.append(metric)
            worst_cond = max(worst_cond, metric["condition_number"])
            worst_overlap = max(worst_overlap, metric["max_pairwise_overlap"])
            if metric["status"] != "PASS":
                triplet_ok = False

        if triplet_ok:
            print(f"  PASS {label:48s} cond={worst_cond:>10.3e} overlap={worst_overlap:>10.3e}")
            tokens.append(EvidenceToken(
                token_id=f"E_SIM_TRIPLET_{'_'.join(axis_names)}_OK",
                sim_spec_id=f"S_SIM_TRIPLET_{'_'.join(axis_names)}",
                status="PASS",
                measured_value=worst_cond,
            ))
        else:
            print(f"  KILL {label:48s} cond={worst_cond:>10.3e} overlap={worst_overlap:>10.3e}")
            tokens.append(EvidenceToken(
                token_id="",
                sim_spec_id=f"S_SIM_TRIPLET_{'_'.join(axis_names)}",
                status="KILL",
                measured_value=worst_cond,
                kill_reason="TRIPLET_RANK_COLLAPSE",
            ))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, RESULTS_NAME)

    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "dimensions": DIMS,
            "rank_epsilon": RANK_EPS,
            "condition_cap": COND_CAP,
            "triplet_count": len(triplets),
            "evidence_ledger": [t.__dict__ for t in tokens],
            "measurements": measurements,
        }, f, indent=2)

    print(f"\n  Results saved: {outpath}")


if __name__ == "__main__":
    run_triplet_sweep()
