#!/usr/bin/env python3
"""
Engine Convergence Diagnostic
===============================
Traces how quickly each engine type converges to its attractor at
different torus placements. Measures step-by-step chirality, entropy,
and negentropy to find:
  1. How many cycles to reach steady state?
  2. Is convergence exponential, linear, or oscillatory?
  3. Does the convergence rate depend on torus placement?

Since the engine has zero seed sensitivity (deterministic attractors),
this probe measures the convergence *trajectory* to characterize
the attractor basin depth.
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


def trace_convergence(engine_type, eta, n_cycles=30, seed=42):
    """Run n_cycles and record per-cycle metrics."""
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=eta, rng=np.random.default_rng(seed))
    controls = {i: StageControls(torus=eta) for i in range(8)}

    trajectory = []
    for cycle in range(n_cycles):
        rho_L_before = state.rho_L.copy()
        rho_R_before = state.rho_R.copy()

        state = engine.run_cycle(state, controls=controls)

        chir = float(trace_distance_2x2(state.rho_L, state.rho_R))
        S = von_neumann_entropy_2x2((state.rho_L + state.rho_R) / 2)
        step_dphi_L = sum(h["dphi_L"] for h in state.history[-8:])  # last cycle
        step_dphi_R = sum(h["dphi_R"] for h in state.history[-8:])

        # State change from previous cycle
        delta_L = float(np.linalg.norm(state.rho_L - rho_L_before, "fro"))
        delta_R = float(np.linalg.norm(state.rho_R - rho_R_before, "fro"))

        trajectory.append({
            "cycle": cycle,
            "chirality": round(chir, 6),
            "entropy": round(S, 6),
            "dphi_L": round(step_dphi_L, 6),
            "dphi_R": round(step_dphi_R, 6),
            "delta_L": round(delta_L, 8),
            "delta_R": round(delta_R, 8),
            "delta_total": round(delta_L + delta_R, 8),
        })

    return trajectory


def classify_convergence(trajectory):
    """Classify convergence type from delta_total series."""
    deltas = [t["delta_total"] for t in trajectory]

    # Check if converged (last 5 cycles have delta < 1e-6)
    final_deltas = deltas[-5:]
    converged = all(d < 1e-6 for d in final_deltas)

    # Find 1e-4 convergence cycle
    conv_cycle = None
    for i, d in enumerate(deltas):
        if d < 1e-4:
            conv_cycle = i
            break

    # Check if oscillatory (non-monotonic early phase)
    early = deltas[:10]
    monotonic = all(early[i] >= early[i+1] for i in range(len(early)-1))

    # Estimate convergence rate (exponential fit)
    if conv_cycle and conv_cycle > 2:
        rate = -np.log(deltas[conv_cycle] / max(deltas[0], 1e-15)) / max(conv_cycle, 1)
    else:
        rate = 0.0

    return {
        "converged": converged,
        "convergence_cycle_1e4": conv_cycle,
        "monotonic_convergence": monotonic,
        "estimated_rate": round(float(rate), 4),
        "final_delta": round(float(deltas[-1]), 10),
    }


def main():
    print(f"\n{'='*72}")
    print("ENGINE CONVERGENCE DIAGNOSTIC")
    print(f"{'='*72}")

    configs = [
        (1, TORUS_INNER, "T1_inner"),
        (1, TORUS_CLIFFORD, "T1_clifford"),
        (1, TORUS_OUTER, "T1_outer"),
        (2, TORUS_INNER, "T2_inner"),
        (2, TORUS_CLIFFORD, "T2_clifford"),
        (2, TORUS_OUTER, "T2_outer"),
    ]

    all_results = []
    for et, eta, label in configs:
        traj = trace_convergence(et, eta, n_cycles=30)
        conv = classify_convergence(traj)
        result = {
            "label": label,
            "engine_type": et,
            "eta": round(float(eta), 4),
            "convergence": conv,
            "trajectory": traj,
        }
        all_results.append(result)

        print(f"  {label:12s}: converged={str(conv['converged']):5s}  "
              f"cycle_1e4={'N/A' if conv['convergence_cycle_1e4'] is None else conv['convergence_cycle_1e4']:>3}  "
              f"monotonic={str(conv['monotonic_convergence']):5s}  "
              f"rate={conv['estimated_rate']:.2f}  "
              f"final_Δ={conv['final_delta']:.2e}")

    # Summary
    all_converged = all(r["convergence"]["converged"] for r in all_results)
    all_monotonic = all(r["convergence"]["monotonic_convergence"] for r in all_results)
    print(f"\n  ALL CONVERGED: {all_converged}")
    print(f"  ALL MONOTONIC: {all_monotonic}")

    output = {
        "schema": "ENGINE_CONVERGENCE_DIAGNOSTIC_v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_cycles": 30,
        "all_converged": all_converged,
        "all_monotonic": all_monotonic,
        "results": all_results,
    }

    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "audit_logs")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "ENGINE_CONVERGENCE_DIAGNOSTIC__CURRENT__v1.json")
    with open(outpath, "w") as f:
        json.dump(output, indent=2, fp=f)
    print(f"\n  Saved: {outpath}")


if __name__ == "__main__":
    main()
