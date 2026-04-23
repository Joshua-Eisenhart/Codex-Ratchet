#!/usr/bin/env python3
"""
Axis Interaction Matrix
========================
For every pair (i,j) of axes 0-5, measures how much axis i's delta
changes when the engine is pinned to different torus placements,
conditioned on axis j's value.

This builds the actual interaction structure between axes — not just
pairwise orthogonality (which is about Choi matrices), but dynamic
coupling (which axes move together in practice).

Outputs a 6×6 interaction matrix + cross-axis correlation data.
"""

import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine, StageControls, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER


def _run_and_get_axes(engine_type, eta, n_cycles=5, seed=42):
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=eta, rng=np.random.default_rng(seed))
    axes_before = engine.read_axes(state)
    controls = {i: StageControls(torus=eta) for i in range(8)}
    for _ in range(n_cycles):
        state = engine.run_cycle(state, controls=controls)
    axes_after = engine.read_axes(state)
    deltas = {k: axes_after[k] - axes_before[k] for k in axes_before}
    return deltas


def main():
    print(f"\n{'='*72}")
    print("AXIS INTERACTION MATRIX")
    print(f"{'='*72}")

    etas = np.linspace(0.15, 1.4, 25)
    axis_names = ["GA0_entropy", "GA1_boundary", "GA2_scale",
                   "GA3_chirality", "GA4_variance", "GA5_coupling"]

    all_deltas = {et: {ax: [] for ax in axis_names} for et in [1, 2]}

    for et in [1, 2]:
        for eta in etas:
            deltas = _run_and_get_axes(et, float(eta), n_cycles=5)
            for ax in axis_names:
                all_deltas[et][ax].append(deltas.get(ax, 0.0))

    # Compute correlation matrix
    results = {}
    for et in [1, 2]:
        vectors = np.array([all_deltas[et][ax] for ax in axis_names])  # 6 × 25
        corr = np.corrcoef(vectors)
        corr_dict = {}
        for i, ax_i in enumerate(axis_names):
            for j, ax_j in enumerate(axis_names):
                if i < j:
                    c_val = float(corr[i, j])
                    corr_dict[f"{ax_i}↔{ax_j}"] = round(c_val, 4) if not np.isnan(c_val) else 0.0

        # Max absolute response per axis
        max_response = {}
        for ax in axis_names:
            vals = all_deltas[et][ax]
            max_response[ax] = {
                "range": round(max(vals) - min(vals), 6),
                "mean": round(float(np.mean(vals)), 6),
                "std": round(float(np.std(vals)), 6),
            }

        results[f"type_{et}"] = {
            "correlation_matrix": corr_dict,
            "axis_response": max_response,
        }

        print(f"\n  Type-{et} Axis Interaction Correlations:")
        for pair, c in sorted(corr_dict.items(), key=lambda x: -abs(x[1])):
            if np.isnan(c):
                bar = "[zero-variance]"
                sign = " "
            else:
                bar = "█" * int(abs(c) * 20)
                sign = "+" if c > 0 else "-"
            print(f"    {pair:35s}: {sign}{abs(c):.3f} {bar}")

        print(f"\n  Type-{et} Axis Response Range (across η sweep):")
        for ax, resp in sorted(max_response.items()):
            print(f"    {ax:18s}: range={resp['range']:.4f}  mean={resp['mean']:+.4f}  std={resp['std']:.4f}")

    # Type-1 vs Type-2 correlation difference
    print(f"\n  TYPE-1 vs TYPE-2 CORRELATION DIFFERENCE:")
    t1_corr = results["type_1"]["correlation_matrix"]
    t2_corr = results["type_2"]["correlation_matrix"]
    for pair in sorted(t1_corr.keys()):
        diff = abs(t1_corr[pair] - t2_corr[pair])
        print(f"    {pair:35s}: |Δcorr|={diff:.4f}")

    output = {
        "schema": "AXIS_INTERACTION_MATRIX_v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "eta_count": len(etas),
        "axis_names": axis_names,
        "results": results,
    }

    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "audit_logs")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "AXIS_INTERACTION_MATRIX__CURRENT__v1.json")
    with open(outpath, "w") as f:
        json.dump(output, indent=2, fp=f)
    print(f"\n  Saved: {outpath}")


if __name__ == "__main__":
    main()
