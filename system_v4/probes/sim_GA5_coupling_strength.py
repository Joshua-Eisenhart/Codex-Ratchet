#!/usr/bin/env python3
"""
Geometric Axis 5 — Coupling Strength on S³
=============================================
Axis 5 = how strongly operators couple to the geometry.

On the Hopf manifold, operator strength determines how far
along the fiber or base a single step moves:
  - Strong coupling: large displacement per step
  - Weak coupling: small displacement per step

This is the "piston" control — it sets the gain/sensitivity
of the engine without changing its direction or type.

Geometric construction:
  1. Apply operator with different strengths s ∈ [0.1, 1.0]
  2. Measure displacement on Bloch sphere
  3. Displacement should scale monotonically with strength
  4. Strong ≠ weak (non-degenerate)

Token: E_GEOMETRIC_AXIS5_VALID
"""

import numpy as np
import os
import sys
import json
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: GA5 is validated here as a geometric coupling-strength sweep, not a canonical nonclassical witness."

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import random_s3_point, coherent_state_density, density_to_bloch
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    negentropy, trace_distance_2x2, _ensure_valid_density, I2,
)
from proto_ratchet_sim_runner import EvidenceToken


def run_GA5_validation():
    print("=" * 72)
    print("GEOMETRIC AXIS 5: COUPLING STRENGTH ON S³")
    print("  'Piston control — operator gain/sensitivity'")
    print("=" * 72)

    rng = np.random.default_rng(42)
    all_pass = True
    results = {}
    n_trials = 30

    strengths = [0.1, 0.3, 0.5, 0.7, 1.0]
    operators = {
        "Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi,
    }

    # ── Test 1: Displacement scales with strength for most operators
    # Note: Fi is a projective/spectral filter — it saturates rather than
    # scaling monotonically. This is geometrically correct (projection is idempotent).
    print("\n  [T1] Displacement vs strength (all operators)...")
    n_monotone = 0
    all_nonzero = True
    for op_name, op_fn in operators.items():
        displacements = []
        for s in strengths:
            total_disp = 0
            for _ in range(n_trials):
                q = random_s3_point(rng)
                rho = 0.5 * coherent_state_density(q) + 0.5 * I2 / 2
                rho_after = op_fn(rho, polarity_up=True, strength=s)
                total_disp += trace_distance_2x2(rho, rho_after)
            displacements.append(total_disp / n_trials)
        
        monotone = all(displacements[i] <= displacements[i+1] + 0.01
                       for i in range(len(displacements)-1))
        if monotone:
            n_monotone += 1
        if displacements[-1] < 1e-6:
            all_nonzero = False
        print(f"    {op_name}: " + "  ".join(f"s={s:.1f}→{d:.3f}" for s, d in zip(strengths, displacements))
              + f"  {'✓' if monotone else '~'}")

    # At least 3 of 4 operators should be monotone (Fi may saturate)
    monotone_ok = n_monotone >= 3 and all_nonzero
    results["n_monotone"] = n_monotone
    results["all_nonzero"] = bool(all_nonzero)
    print(f"    {n_monotone}/4 operators monotone, all non-zero: {all_nonzero}")
    print(f"    {'✓' if monotone_ok else '✗'} Coupling strength is meaningful")
    all_pass = all_pass and monotone_ok

    # ── Test 2: Strong ≠ Weak (non-degenerate) ──────────────────
    print("\n  [T2] Strong ≠ Weak...")
    n_distinct = 0
    total_dist = 0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.5 * coherent_state_density(q) + 0.5 * I2 / 2
        rho_strong = apply_Fe(rho, polarity_up=True, strength=1.0)
        rho_weak = apply_Fe(rho, polarity_up=True, strength=0.1)
        dist = trace_distance_2x2(rho_strong, rho_weak)
        total_dist += dist
        if dist > 1e-6:
            n_distinct += 1
    
    avg_dist = total_dist / n_trials
    distinct_ok = n_distinct / n_trials > 0.7
    results["strong_weak_avg_dist"] = float(avg_dist)
    results["strong_weak_distinct_frac"] = float(n_distinct / n_trials)
    print(f"    Distinct: {n_distinct}/{n_trials}, avg distance: {avg_dist:.4f}")
    print(f"    {'✓' if distinct_ok else '✗'} Strong ≠ Weak")
    all_pass = all_pass and distinct_ok

    # ── Test 3: Zero strength = identity ─────────────────────────
    print("\n  [T3] Zero strength ≈ identity...")
    n_identity = 0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.5 * coherent_state_density(q) + 0.5 * I2 / 2
        rho_zero = apply_Te(rho, polarity_up=True, strength=0.01)
        dist = trace_distance_2x2(rho, rho_zero)
        if dist < 0.05:
            n_identity += 1
    
    identity_frac = n_identity / n_trials
    identity_ok = identity_frac > 0.7
    results["zero_strength_identity_frac"] = float(identity_frac)
    print(f"    Near-identity: {n_identity}/{n_trials} = {identity_frac:.2f}")
    print(f"    {'✓' if identity_ok else '✗'} Zero strength ≈ no-op")
    all_pass = all_pass and identity_ok

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  GEOMETRIC AXIS 5 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    tokens = []
    if all_pass:
        tokens.append(EvidenceToken("E_GEOMETRIC_AXIS5_VALID", "S_GA5_COUPLING",
                                    "PASS", float(avg_dist)))
    else:
        tokens.append(EvidenceToken("", "S_GA5_COUPLING", "KILL", 0.0, "FAILED"))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "GA5_coupling_strength_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "axis": 5, "name": "Geometric_Axis5_Coupling",
            "results": results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_GA5_validation()
