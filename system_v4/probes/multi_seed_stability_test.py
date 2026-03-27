#!/usr/bin/env python3
"""
Multi-Seed Engine Stability Test
==================================
Runs 100 seeds × 2 engine types × 3 torus placements to measure:
  - ΔΦ stability (std across seeds)
  - Chirality convergence
  - Operator fixed-point behavior
  - Whether the engine has attractors or is seed-dependent

This is a statistical stability audit, not a physics claim.
"""

import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine, StageControls, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER
from geometric_operators import negentropy, trace_distance_2x2
from hopf_manifold import von_neumann_entropy_2x2


def run_stability_scan(engine_type, eta, n_seeds=100, n_cycles=5):
    """Run n_seeds engines and compute stability statistics."""
    dphi_Ls = []
    dphi_Rs = []
    chiralities = []
    entropies = []

    for seed in range(n_seeds):
        engine = GeometricEngine(engine_type=engine_type)
        state = engine.init_state(eta=eta, rng=np.random.default_rng(seed))
        controls = {i: StageControls(torus=eta) for i in range(8)}
        for _ in range(n_cycles):
            state = engine.run_cycle(state, controls=controls)

        dphi_L = sum(h["dphi_L"] for h in state.history)
        dphi_R = sum(h["dphi_R"] for h in state.history)
        chir = float(trace_distance_2x2(state.rho_L, state.rho_R))
        S = von_neumann_entropy_2x2((state.rho_L + state.rho_R) / 2)

        dphi_Ls.append(dphi_L)
        dphi_Rs.append(dphi_R)
        chiralities.append(chir)
        entropies.append(S)

    return {
        "engine_type": engine_type,
        "eta": round(float(eta), 4),
        "n_seeds": n_seeds,
        "n_cycles": n_cycles,
        "dphi_L": {"mean": round(float(np.mean(dphi_Ls)), 6), "std": round(float(np.std(dphi_Ls)), 6),
                   "min": round(float(np.min(dphi_Ls)), 6), "max": round(float(np.max(dphi_Ls)), 6)},
        "dphi_R": {"mean": round(float(np.mean(dphi_Rs)), 6), "std": round(float(np.std(dphi_Rs)), 6),
                   "min": round(float(np.min(dphi_Rs)), 6), "max": round(float(np.max(dphi_Rs)), 6)},
        "chirality": {"mean": round(float(np.mean(chiralities)), 6), "std": round(float(np.std(chiralities)), 6),
                      "min": round(float(np.min(chiralities)), 6), "max": round(float(np.max(chiralities)), 6)},
        "entropy": {"mean": round(float(np.mean(entropies)), 6), "std": round(float(np.std(entropies)), 6),
                    "min": round(float(np.min(entropies)), 6), "max": round(float(np.max(entropies)), 6)},
        "has_attractor": float(np.std(chiralities)) < 0.05,  # low chirality spread = attractor-like
        "seed_sensitive": float(np.std(dphi_Ls)) > 0.1,  # high ΔΦ spread = seed-sensitive
    }


def main():
    print(f"\n{'='*72}")
    print("MULTI-SEED ENGINE STABILITY TEST")
    print(f"{'='*72}")

    configs = [
        (1, TORUS_INNER, "T1_inner"),
        (1, TORUS_CLIFFORD, "T1_clifford"),
        (1, TORUS_OUTER, "T1_outer"),
        (2, TORUS_INNER, "T2_inner"),
        (2, TORUS_CLIFFORD, "T2_clifford"),
        (2, TORUS_OUTER, "T2_outer"),
    ]

    results = []
    for et, eta, label in configs:
        r = run_stability_scan(et, eta, n_seeds=100, n_cycles=5)
        results.append(r)
        print(f"  {label:12s}: ΔΦ_L={r['dphi_L']['mean']:+.4f}±{r['dphi_L']['std']:.4f}  "
              f"chir={r['chirality']['mean']:.4f}±{r['chirality']['std']:.4f}  "
              f"attractor={'YES' if r['has_attractor'] else 'NO'}  "
              f"seed_sensitive={'YES' if r['seed_sensitive'] else 'NO'}")

    # Cross-type comparison at each torus
    print(f"\n  CROSS-TYPE COMPARISON:")
    for torus_name, eta in [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]:
        t1 = [r for r in results if r["engine_type"] == 1 and abs(r["eta"] - round(float(eta), 4)) < 0.001][0]
        t2 = [r for r in results if r["engine_type"] == 2 and abs(r["eta"] - round(float(eta), 4)) < 0.001][0]
        dphi_diff = abs(t1["dphi_L"]["mean"] - t2["dphi_L"]["mean"])
        chir_diff = abs(t1["chirality"]["mean"] - t2["chirality"]["mean"])
        print(f"    {torus_name:8s}: |ΔΦ_L diff|={dphi_diff:.4f}  |chir diff|={chir_diff:.4f}")

    output = {
        "schema": "MULTI_SEED_STABILITY_v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_seeds": 100,
        "n_cycles": 5,
        "results": results,
    }

    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "audit_logs")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "MULTI_SEED_STABILITY__CURRENT__v1.json")
    with open(outpath, "w") as f:
        json.dump(output, indent=2, fp=f)
    print(f"\n  Saved: {outpath}")


if __name__ == "__main__":
    main()
