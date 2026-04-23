#!/usr/bin/env python3
"""
Engine Phase-Space Explorer
============================
Maps the full engine dynamics across the (η, seed, engine_type) parameter space.

For each point, captures:
  - Total ΔΦ (left + right spinors)
  - Chirality (trace distance L↔R)
  - Final entropy
  - Axis trajectory deltas
  - Operator dominance (which operator moved the state most)

Outputs a 2D scan artifact suitable for heatmap visualization.
"""

import json
import os
import sys
import time
import numpy as np
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine, StageControls, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER
from geometric_operators import negentropy, trace_distance_2x2
from hopf_manifold import von_neumann_entropy_2x2, torus_radii

AUDIT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                         "system_v4", "a2_state", "audit_logs")


def run_single(engine_type, eta, seed, n_cycles=5):
    """Run engine at (type, eta, seed) and return metrics."""
    engine = GeometricEngine(engine_type=engine_type)
    rng = np.random.default_rng(seed)
    state = engine.init_state(eta=eta, rng=rng)
    axes_before = engine.read_axes(state)

    controls = {i: StageControls(torus=eta) for i in range(8)}
    for _ in range(n_cycles):
        state = engine.run_cycle(state, controls=controls)

    axes_after = engine.read_axes(state)
    total_dphi_L = sum(h["dphi_L"] for h in state.history)
    total_dphi_R = sum(h["dphi_R"] for h in state.history)
    chir = float(trace_distance_2x2(state.rho_L, state.rho_R))
    S = von_neumann_entropy_2x2((state.rho_L + state.rho_R) / 2)

    # Operator dominance: which operator moved state most per step?
    op_deltas = defaultdict(float)
    for h in state.history:
        op = h.get("operator", "unknown")
        op_deltas[op] += abs(h["dphi_L"]) + abs(h["dphi_R"])

    return {
        "engine_type": engine_type,
        "eta": round(float(eta), 4),
        "seed": int(seed),
        "n_cycles": n_cycles,
        "steps": len(state.history),
        "dphi_L": round(total_dphi_L, 6),
        "dphi_R": round(total_dphi_R, 6),
        "dphi_total": round(total_dphi_L + total_dphi_R, 6),
        "chirality": round(chir, 6),
        "entropy": round(S, 6),
        "axes_before": {k: round(v, 4) for k, v in axes_before.items()},
        "axes_after": {k: round(v, 4) for k, v in axes_after.items()},
        "axis_deltas": {k: round(axes_after[k] - axes_before[k], 6) for k in axes_before},
        "operator_dominance": {k: round(v, 4) for k, v in sorted(op_deltas.items(), key=lambda x: -x[1])},
    }


def main():
    print(f"\n{'='*72}")
    print("ENGINE PHASE-SPACE EXPLORER")
    print(f"{'='*72}")

    # Parameter grid
    etas = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
            0.2, 0.4, 0.6, 0.8, 1.0, 1.2]
    seeds = list(range(10))  # 10 different random seeds
    types = [1, 2]

    total = len(etas) * len(seeds) * len(types)
    print(f"  Grid: {len(etas)} η × {len(seeds)} seeds × {len(types)} types = {total} runs")

    results = []
    for et in types:
        for eta in etas:
            for seed in seeds:
                r = run_single(et, eta, seed, n_cycles=5)
                results.append(r)
        print(f"  Type-{et}: {len(etas)*len(seeds)} runs complete")

    # Summary statistics per (type, eta)
    summary = {}
    for et in types:
        for eta in etas:
            runs = [r for r in results if r["engine_type"] == et and abs(r["eta"] - round(float(eta), 4)) < 0.001]
            if runs:
                dphi_totals = [r["dphi_total"] for r in runs]
                chiralities = [r["chirality"] for r in runs]
                entropies = [r["entropy"] for r in runs]
                key = f"T{et}_eta{round(float(eta),3)}"
                summary[key] = {
                    "dphi_total_mean": round(float(np.mean(dphi_totals)), 6),
                    "dphi_total_std": round(float(np.std(dphi_totals)), 6),
                    "chirality_mean": round(float(np.mean(chiralities)), 6),
                    "chirality_std": round(float(np.std(chiralities)), 6),
                    "entropy_mean": round(float(np.mean(entropies)), 6),
                    "entropy_std": round(float(np.std(entropies)), 6),
                    "run_count": len(runs),
                }

    # Operator dominance aggregate
    op_totals = defaultdict(lambda: defaultdict(float))
    for r in results:
        et = r["engine_type"]
        for op, val in r["operator_dominance"].items():
            op_totals[et][op] += val
    op_dominance = {}
    for et, ops in op_totals.items():
        total_delta = sum(ops.values())
        op_dominance[f"type_{et}"] = {
            op: round(val / max(total_delta, 1e-10), 4)
            for op, val in sorted(ops.items(), key=lambda x: -x[1])
        }

    # Print summary
    print(f"\n  SUMMARY:")
    for key, s in sorted(summary.items()):
        print(f"    {key:20s}: ΔΦ={s['dphi_total_mean']:+.4f}±{s['dphi_total_std']:.4f}  "
              f"chir={s['chirality_mean']:.4f}±{s['chirality_std']:.4f}  "
              f"S={s['entropy_mean']:.4f}±{s['entropy_std']:.4f}")

    print(f"\n  OPERATOR DOMINANCE:")
    for et_key, ops in op_dominance.items():
        print(f"    {et_key}: {ops}")

    output = {
        "schema": "ENGINE_PHASE_SPACE_v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "grid": {"eta_count": len(etas), "seed_count": len(seeds), "type_count": len(types), "total_runs": total},
        "summary": summary,
        "operator_dominance": op_dominance,
        "runs": results,
    }

    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "audit_logs")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "ENGINE_PHASE_SPACE__CURRENT__v1.json")
    with open(outpath, "w") as f:
        json.dump(output, indent=2, fp=f)
    print(f"\n  Saved: {outpath}")


if __name__ == "__main__":
    main()
