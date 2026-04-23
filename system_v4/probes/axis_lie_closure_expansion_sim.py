#!/usr/bin/env python3
"""
Axis Lie Closure Expansion SIM
================================
Falsifiable thesis: The Lie closure (commutator closure) of axis generators
either closes within existing axes (finite basis) or generates new independent
directions (new degrees of freedom for axes 7-12).

PASS: Closure rank increases beyond base rank by ≥ 1 (evidence of hidden DoF).
KILL: Closure rank never increases (degenerate / too symmetric).
"""

import numpy as np
import json
import os
import sys
from itertools import combinations
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken
from axis_orthogonality_suite import AXES, build_choi


def commutator(A, B):
    """Matrix commutator [A, B] = AB - BA."""
    return A @ B - B @ A


def closure_rank(matrices, tol=1e-8):
    """Rank of the vector space spanned by a set of flattened matrices."""
    if not matrices:
        return 0
    V = np.stack([m.reshape(-1) for m in matrices], axis=1)
    s = np.linalg.svd(V, compute_uv=False)
    return int(np.sum(s > tol))


def run_lie_closure():
    print("=" * 72)
    print("AXIS LIE CLOSURE EXPANSION SIM")
    print("=" * 72)

    DIMS = [4, 8, 16]
    tokens = []
    all_results = []

    for d in DIMS:
        # Build Choi matrices for all 6 axes
        chois = {}
        for name, func in AXES.items():
            chois[name] = build_choi(func, d)

        base_mats = list(chois.values())
        base_rank = closure_rank(base_mats)

        print(f"\n  d={d}: Base rank (6 axes) = {base_rank}")

        # Level 1: Add all pairwise commutators
        level1_comms = []
        for (n1, C1), (n2, C2) in combinations(chois.items(), 2):
            comm = commutator(C1, C2)
            comm_norm = float(np.linalg.norm(comm, 'fro'))
            if comm_norm > 1e-10:
                level1_comms.append(comm / comm_norm)

        rank_after_L1 = closure_rank(base_mats + level1_comms)
        print(f"  + Level-1 commutators ({len(level1_comms)} non-zero) → rank = {rank_after_L1}")

        # Level 2: Commutators of commutators with base axes
        level2_comms = []
        for comm in level1_comms[:10]:  # Limit to prevent explosion
            for C in base_mats:
                c2 = commutator(comm, C)
                c2_norm = float(np.linalg.norm(c2, 'fro'))
                if c2_norm > 1e-10:
                    level2_comms.append(c2 / c2_norm)

        rank_after_L2 = closure_rank(base_mats + level1_comms + level2_comms)
        print(f"  + Level-2 commutators ({len(level2_comms)} non-zero) → rank = {rank_after_L2}")

        # Compute expansion ratios
        expansion_L1 = rank_after_L1 - base_rank
        expansion_L2 = rank_after_L2 - rank_after_L1

        # Commutator norm statistics
        comm_norms = [float(np.linalg.norm(commutator(C1, C2), 'fro'))
                      for (_, C1), (_, C2) in combinations(chois.items(), 2)]

        result = {
            "d": d,
            "base_rank": base_rank,
            "rank_after_L1": rank_after_L1,
            "rank_after_L2": rank_after_L2,
            "expansion_L1": expansion_L1,
            "expansion_L2": expansion_L2,
            "n_L1_commutators": len(level1_comms),
            "n_L2_commutators": len(level2_comms),
            "comm_norm_mean": round(float(np.mean(comm_norms)), 4),
            "comm_norm_max": round(float(np.max(comm_norms)), 4),
        }
        all_results.append(result)

        print(f"  Expansion L1: +{expansion_L1}  L2: +{expansion_L2}")
        print(f"  Commutator norms: mean={np.mean(comm_norms):.4f}  max={np.max(comm_norms):.4f}")

    # Verdict: PASS if any dimension shows closure rank increase
    any_expansion = any(r["expansion_L1"] > 0 or r["expansion_L2"] > 0 for r in all_results)
    max_expansion = max(r["expansion_L1"] + r["expansion_L2"] for r in all_results)

    print(f"\n  Any closure expansion detected: {'YES ✓' if any_expansion else 'NO ✗'}")
    print(f"  Max total expansion: +{max_expansion}")
    print(f"  OVERALL: {'PASS' if any_expansion else 'KILL'}")

    if any_expansion:
        tokens.append(EvidenceToken("E_SIM_LIE_CLOSURE_EXPANSION_OK",
                                    "S_SIM_AXIS_LIE_CLOSURE", "PASS",
                                    float(max_expansion)))
    else:
        tokens.append(EvidenceToken("", "S_SIM_AXIS_LIE_CLOSURE", "KILL",
                                    0.0, "NO_EXPANSION"))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "axis_lie_closure_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "dimensions": DIMS,
            "results": all_results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_lie_closure()
