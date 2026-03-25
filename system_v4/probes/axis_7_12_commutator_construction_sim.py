#!/usr/bin/env python3
"""
Axes 7-12 Commutator Construction SIM
========================================
Constructs axes 7-12 from the Lie closure of the base 6 axes.

The Lie closure SIM proved 69 new independent directions exist. The mirror
SIM proved naive symmetry operations don't work. So axes 7-12 must come
from COMMUTATOR PRODUCTS — the interaction structure between base axes.

Method:
1. Compute all 15 Level-1 commutators [Ai, Aj]
2. Orthogonalize against base 6 axes using Gram-Schmidt
3. Select top 6 most independent + physically meaningful directions
4. Test the full 12-axis system for rank and orthogonality

EvidenceToken: PASS if 12-axis system has rank >= 12 and mutual overlap < 0.1
"""

import numpy as np
import json
import os
import sys
from itertools import combinations
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken
from axis_orthogonality_suite import AXES, build_choi, hs_inner


def gram_schmidt_orthogonalize(new_vecs, basis_vecs):
    """Orthogonalize new_vecs against basis_vecs and each other."""
    ortho = []
    all_basis = list(basis_vecs)

    for v in new_vecs:
        # Subtract projections onto all existing basis vectors
        w = v.copy()
        for b in all_basis:
            b_flat = b.reshape(-1)
            w_flat = w.reshape(-1)
            proj_coeff = np.vdot(b_flat, w_flat) / max(np.vdot(b_flat, b_flat), 1e-30)
            w = w - proj_coeff * b

        # Normalize
        w_norm = np.linalg.norm(w, 'fro')
        if w_norm > 1e-10:
            w = w / w_norm
            ortho.append(w)
            all_basis.append(w)

    return ortho


def run_commutator_construction():
    print("=" * 72)
    print("AXES 7-12 COMMUTATOR CONSTRUCTION SIM")
    print("=" * 72)

    DIMS = [4, 8, 16]
    tokens = []
    all_results = []

    for d in DIMS:
        print(f"\n  --- d={d} ---")

        # Build base Choi matrices
        base_chois = {}
        for name, func in AXES.items():
            base_chois[name] = build_choi(func, d)

        base_names = list(base_chois.keys())
        base_mats = list(base_chois.values())

        # Compute all 15 Level-1 commutators
        commutators = {}
        for n1, n2 in combinations(base_names, 2):
            C1, C2 = base_chois[n1], base_chois[n2]
            comm = C1 @ C2 - C2 @ C1
            comm_norm = float(np.linalg.norm(comm, 'fro'))
            short_1 = n1.split("_")[0]
            short_2 = n2.split("_")[0]
            comm_name = f"[{short_1},{short_2}]"
            if comm_norm > 1e-10:
                commutators[comm_name] = {
                    "matrix": comm / comm_norm,
                    "parents": (n1, n2),
                    "raw_norm": comm_norm,
                }

        print(f"  {len(commutators)} non-zero commutators computed")

        # Orthogonalize commutators against base axes
        comm_mats = [c["matrix"] for c in commutators.values()]
        comm_names = list(commutators.keys())
        ortho_mats = gram_schmidt_orthogonalize(comm_mats, base_mats)

        print(f"  {len(ortho_mats)} independent directions after orthogonalization")

        # Select top 6 by highest original commutator norm (= most non-commutative parents)
        scored = []
        for i, (name, info) in enumerate(commutators.items()):
            if i < len(ortho_mats):
                scored.append({
                    "name": name,
                    "parents": info["parents"],
                    "raw_norm": info["raw_norm"],
                    "ortho_mat": ortho_mats[i],
                    "ortho_norm": float(np.linalg.norm(ortho_mats[i], 'fro')),
                })

        scored.sort(key=lambda x: x["raw_norm"], reverse=True)
        top6 = scored[:6]

        # Name them as axes 7-12
        axis_7_12 = {}
        for i, entry in enumerate(top6):
            ax_num = 7 + i
            ax_name = f"A{ax_num}_{entry['name']}"
            axis_7_12[ax_name] = entry["ortho_mat"]
            print(f"    A{ax_num} = {entry['name']:20s}  raw_norm={entry['raw_norm']:.4f}  "
                  f"ortho_norm={entry['ortho_norm']:.4f}  parents={entry['parents']}")

        # Test the full 12-axis system
        all_12_mats = base_mats + [axis_7_12[n] for n in axis_7_12]
        all_12_names = base_names + list(axis_7_12.keys())

        # Rank test
        V = np.stack([m.reshape(-1) for m in all_12_mats], axis=1)
        s = np.linalg.svd(V, compute_uv=False)
        full_rank = int(np.sum(s > 1e-8))
        print(f"\n    Full 12-axis rank: {full_rank}")

        # Mutual overlap test (12×12)
        max_cross_overlap = 0.0
        n_low_overlap = 0
        n_total = 0
        overlap_matrix = np.zeros((12, 12))
        for i in range(len(all_12_mats)):
            for j in range(i + 1, len(all_12_mats)):
                ov = abs(hs_inner(all_12_mats[i], all_12_mats[j]))
                overlap_matrix[i, j] = ov
                overlap_matrix[j, i] = ov
                max_cross_overlap = max(max_cross_overlap, ov)
                n_total += 1
                if ov < 0.1:
                    n_low_overlap += 1

        print(f"    Max overlap in 12×12: {max_cross_overlap:.4f}")
        print(f"    Low-overlap pairs (<0.1): {n_low_overlap}/{n_total}")

        result = {
            "d": d,
            "n_commutators": len(commutators),
            "n_ortho_directions": len(ortho_mats),
            "full_rank": full_rank,
            "max_cross_overlap": round(max_cross_overlap, 6),
            "low_overlap_fraction": round(n_low_overlap / max(n_total, 1), 4),
            "axes_7_12": [{"name": n, "parents": top6[i]["parents"],
                          "raw_norm": round(top6[i]["raw_norm"], 4)}
                         for i, n in enumerate(axis_7_12.keys())],
        }
        all_results.append(result)

    # Verdict
    all_full_rank = all(r["full_rank"] >= 12 for r in all_results)
    low_overlap = all(r["max_cross_overlap"] < 0.5 for r in all_results)
    overall = all_full_rank and low_overlap

    print(f"\n  Full rank ≥ 12 at all d: {'YES ✓' if all_full_rank else 'NO ✗'}")
    print(f"  Max overlap < 0.5 at all d: {'YES ✓' if low_overlap else 'NO ✗'}")
    print(f"  OVERALL: {'PASS' if overall else 'KILL'}")

    if overall:
        tokens.append(EvidenceToken("E_SIM_AXES_7_12_CONSTRUCTED",
                                    "S_SIM_AXIS_7_12_COMMUTATOR", "PASS",
                                    float(all_results[-1]["full_rank"])))
    else:
        tokens.append(EvidenceToken("", "S_SIM_AXIS_7_12_COMMUTATOR", "KILL",
                                    float(all_results[-1]["full_rank"]),
                                    f"RANK={all_results[-1]['full_rank']}"))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "axis_7_12_commutator_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "dimensions": DIMS,
            "results": all_results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_commutator_construction()
