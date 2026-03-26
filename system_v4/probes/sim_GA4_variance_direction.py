#!/usr/bin/env python3
"""
Geometric Axis 4 — Variance Direction (Fe/Ti vs Te/Fi) on S³
================================================================
Axis 4 = which operator family acts on the geometry.

On the Hopf manifold:
  - Fe/Ti family: acts along the fiber (vertical, S¹ action)
    Fe = amplitude damping along fiber
    Ti = dephasing in fiber basis
  - Te/Fi family: acts across fibers (horizontal, base S² action)
    Te = rotation on base S²
    Fi = spectral filtering across base

The two families produce genuinely different geometric evolution
because fiber-action and base-action are topologically inequivalent
(one is S¹, the other is S²).

Token: E_GEOMETRIC_AXIS4_VALID
"""

import numpy as np
import os
import sys
import json
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import random_s3_point, coherent_state_density, density_to_bloch
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    negentropy, trace_distance_2x2, _ensure_valid_density, I2,
)
from proto_ratchet_sim_runner import EvidenceToken


def run_GA4_validation():
    print("=" * 72)
    print("GEOMETRIC AXIS 4: VARIANCE DIRECTION (Fe/Ti vs Te/Fi) ON S³")
    print("  'Fiber-action vs base-action are topologically inequivalent'")
    print("=" * 72)

    rng = np.random.default_rng(42)
    all_pass = True
    results = {}
    n_trials = 30

    # ── Test 1: Fe/Ti ≠ Te/Fi on same initial state ─────────────
    print("\n  [T1] Fe/Ti vs Te/Fi produce different output...")
    n_distinct = 0
    total_dist = 0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.6 * coherent_state_density(q) + 0.4 * I2 / 2
        
        # Family 1: Fe then Ti (deductive = fiber-aligned)
        rho_feti = apply_Ti(apply_Fe(rho.copy(), polarity_up=True), polarity_up=True)
        # Family 2: Te then Fi (inductive = base-aligned)
        rho_tefi = apply_Fi(apply_Te(rho.copy(), polarity_up=True), polarity_up=True)
        
        dist = trace_distance_2x2(rho_feti, rho_tefi)
        total_dist += dist
        if dist > 1e-6:
            n_distinct += 1
    
    avg_dist = total_dist / n_trials
    distinct_ok = n_distinct / n_trials > 0.7
    results["families_distinct_frac"] = float(n_distinct / n_trials)
    results["families_avg_distance"] = float(avg_dist)
    print(f"    Distinct: {n_distinct}/{n_trials}, avg distance: {avg_dist:.4f}")
    print(f"    {'✓' if distinct_ok else '✗'} Fe/Ti ≠ Te/Fi")
    all_pass = all_pass and distinct_ok

    # ── Test 2: Bloch vector displacement directions differ ──────
    print("\n  [T2] Displacement direction differs between families...")
    angles = []
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.5 * coherent_state_density(q) + 0.5 * I2 / 2
        b0 = density_to_bloch(rho)
        
        rho_feti = apply_Ti(apply_Fe(rho.copy(), polarity_up=True), polarity_up=True)
        rho_tefi = apply_Fi(apply_Te(rho.copy(), polarity_up=True), polarity_up=True)
        
        b_feti = density_to_bloch(rho_feti)
        b_tefi = density_to_bloch(rho_tefi)
        
        d_feti = b_feti - b0
        d_tefi = b_tefi - b0
        
        n1 = np.linalg.norm(d_feti)
        n2 = np.linalg.norm(d_tefi)
        if n1 > 1e-8 and n2 > 1e-8:
            cos_angle = np.clip(np.dot(d_feti, d_tefi) / (n1 * n2), -1, 1)
            angles.append(np.arccos(abs(cos_angle)))
    
    avg_angle = np.mean(angles) if angles else 0
    angle_nonzero = avg_angle > 0.1  # At least ~6 degrees
    results["avg_displacement_angle_rad"] = float(avg_angle)
    results["angle_nonzero"] = bool(angle_nonzero)
    print(f"    Avg displacement angle: {np.degrees(avg_angle):.1f}°")
    print(f"    {'✓' if angle_nonzero else '✗'} Families displace in different directions")
    all_pass = all_pass and angle_nonzero

    # ── Test 3: Negentropy change differs between families ───────
    print("\n  [T3] Negentropy response differs...")
    dphi_feti_list = []
    dphi_tefi_list = []
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.5 * coherent_state_density(q) + 0.5 * I2 / 2
        phi0 = negentropy(rho)
        
        rho_feti = apply_Ti(apply_Fe(rho.copy(), polarity_up=True), polarity_up=True)
        rho_tefi = apply_Fi(apply_Te(rho.copy(), polarity_up=True), polarity_up=True)
        
        dphi_feti_list.append(negentropy(rho_feti) - phi0)
        dphi_tefi_list.append(negentropy(rho_tefi) - phi0)
    
    avg_dphi_feti = np.mean(dphi_feti_list)
    avg_dphi_tefi = np.mean(dphi_tefi_list)
    dphi_different = abs(avg_dphi_feti - avg_dphi_tefi) > 0.01
    results["avg_dphi_feti"] = float(avg_dphi_feti)
    results["avg_dphi_tefi"] = float(avg_dphi_tefi)
    results["dphi_different"] = bool(dphi_different)
    print(f"    Fe/Ti avg ΔΦ: {avg_dphi_feti:+.4f}")
    print(f"    Te/Fi avg ΔΦ: {avg_dphi_tefi:+.4f}")
    print(f"    {'✓' if dphi_different else '✗'} Different negentropy response")
    all_pass = all_pass and dphi_different

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  GEOMETRIC AXIS 4 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    tokens = []
    if all_pass:
        tokens.append(EvidenceToken("E_GEOMETRIC_AXIS4_VALID", "S_GA4_VARIANCE",
                                    "PASS", float(avg_dist)))
    else:
        tokens.append(EvidenceToken("", "S_GA4_VARIANCE", "KILL", 0.0, "FAILED"))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "GA4_variance_direction_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "axis": 4, "name": "Geometric_Axis4_Variance_Direction",
            "results": results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_GA4_validation()
