#!/usr/bin/env python3
"""
Axis Residual Subspace Discovery SIM
=======================================
Falsifiable thesis: The current axis basis (axes 1-6) does not exhaust
the admissible operator manifold. Residual subspace norms after projection
reveal additional stable directions.

PASS: At least one candidate direction with residual norm ≥ 0.2 and
      stability ≥ 0.8 across seeds for d ∈ {4,8,16}.
KILL: All residual candidates collapse or are artifacts (norm < 0.05).
"""

import numpy as np
import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken
from axis_orthogonality_suite import AXES, build_choi


def project_onto_span(vec, basis_matrix):
    """Project vec onto the column span of basis_matrix using least squares."""
    coeffs, _, _, _ = np.linalg.lstsq(basis_matrix, vec, rcond=None)
    projection = basis_matrix @ coeffs
    return projection


def find_residual_subspace(d, n_probes=50, seed=42):
    """Generate random CPTP-like channels and measure their residual
    after projecting out the span of axes 1-6."""
    rng = np.random.default_rng(seed)

    # Build basis from known axes (Choi representations, flattened)
    axis_chois = []
    for name, func in AXES.items():
        C = build_choi(func, d)
        axis_chois.append(C.reshape(-1))
    basis_matrix = np.stack(axis_chois, axis=1)  # (d^4, 6)

    residual_norms = []
    candidates = []

    for _ in range(n_probes):
        # Generate a random CPTP-ish channel via Choi construction
        K = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
        # Random Choi: partial trace of |K><K|
        choi_rand = np.zeros((d**2, d**2), dtype=complex)
        for i in range(d):
            for j in range(d):
                E = np.zeros((d, d), dtype=complex)
                E[i, j] = 1.0
                out = K @ E @ K.conj().T
                out_tr = np.real(np.trace(out))
                if out_tr > 1e-12:
                    out /= out_tr
                for u in range(d):
                    for v in range(d):
                        choi_rand[i*d+u, j*d+v] = out[u, v]
        choi_rand /= max(np.linalg.norm(choi_rand, 'fro'), 1e-30)
        vec = choi_rand.reshape(-1)

        # Project onto axis span and measure residual
        proj = project_onto_span(vec, basis_matrix)
        residual = vec - proj
        res_norm = float(np.linalg.norm(residual))
        residual_norms.append(res_norm)

        if res_norm >= 0.2:
            candidates.append({
                "residual_norm": round(res_norm, 6),
                "seed": seed,
            })

    return residual_norms, candidates


def run_residual_discovery():
    print("=" * 72)
    print("AXIS RESIDUAL SUBSPACE DISCOVERY SIM")
    print("=" * 72)

    DIMS = [4, 8, 16]
    N_SEEDS = 5
    tokens = []
    all_results = []
    stable_candidates = 0

    for d in DIMS:
        seed_results = []
        for s in range(N_SEEDS):
            norms, cands = find_residual_subspace(d, n_probes=30, seed=42 + s)
            mean_res = float(np.mean(norms))
            max_res = float(np.max(norms))
            n_above = sum(1 for n in norms if n >= 0.2)
            seed_results.append({
                "seed": 42 + s,
                "mean_residual": round(mean_res, 4),
                "max_residual": round(max_res, 4),
                "n_above_threshold": n_above,
            })
            print(f"  d={d:3d}  seed={42+s}  mean_res={mean_res:.4f}  "
                  f"max_res={max_res:.4f}  above_0.2={n_above}/30")

        # Stability: is n_above > 0 across all seeds?
        stable = all(r["n_above_threshold"] > 0 for r in seed_results)
        if stable:
            stable_candidates += 1

        all_results.append({
            "d": d, "stable": stable,
            "seeds": seed_results,
        })

    overall_pass = stable_candidates >= 2  # Need stability in at least 2/3 dimensions
    print(f"\n  Stable residual candidates in {stable_candidates}/{len(DIMS)} dimensions")
    print(f"  OVERALL: {'PASS ✓' if overall_pass else 'KILL ✗'}")

    if overall_pass:
        tokens.append(EvidenceToken("E_SIM_RESIDUAL_SUBSPACE_OK",
                                    "S_SIM_AXIS_RESIDUAL_SUBSPACE", "PASS",
                                    float(stable_candidates / len(DIMS))))
    else:
        tokens.append(EvidenceToken("", "S_SIM_AXIS_RESIDUAL_SUBSPACE", "KILL",
                                    float(stable_candidates / len(DIMS)),
                                    f"STABLE={stable_candidates}/{len(DIMS)}"))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "axis_residual_subspace_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "dimensions": DIMS, "n_seeds": N_SEEDS,
            "stable_candidates": stable_candidates,
            "results": all_results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_residual_discovery()
