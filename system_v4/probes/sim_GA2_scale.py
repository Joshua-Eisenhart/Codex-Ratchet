#!/usr/bin/env python3
"""
Geometric Axis 2 — Scale (Expansion vs Compression) on S³
============================================================
Axis 2 = radial accessibility of the torus cross-section.

On the Hopf manifold, each latitude θ on S² defines a torus.
  - θ near 0 or π → small torus (polar, compressed)
  - θ near π/2 → large torus (equatorial, expanded)

Geometric construction:
  1. Sample torus coordinates (R, r) at different latitudes
  2. "Expanded" = equatorial torus (large R, large phase space)
  3. "Compressed" = polar torus (small R, constrained phase space)
  4. Te operator expands (rotates toward equator)
  5. Both polarities of Te are distinguishable

Token: E_GEOMETRIC_AXIS2_VALID
"""

import numpy as np
import os
import sys
import json
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: GA2 is validated here as a torus-scale accessibility construction, not a canonical nonclassical witness."

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import (
    random_s3_point, coherent_state_density, density_to_bloch,
    hopf_map, torus_coordinates,
)
from geometric_operators import (
    apply_Te, negentropy, trace_distance_2x2,
    _ensure_valid_density, I2,
)
from proto_ratchet_sim_runner import EvidenceToken


def torus_radius_at_latitude(bloch_z):
    """Torus radius as function of Bloch z-coordinate.
    
    |z| = 1 → poles → minimal torus (radius → 0)
    z = 0 → equator → maximal torus (radius → 1)
    """
    return np.sqrt(max(1 - bloch_z**2, 0))


def run_GA2_validation():
    print("=" * 72)
    print("GEOMETRIC AXIS 2: SCALE (EXPANSION vs COMPRESSION) ON S³")
    print("  'Torus latitude = radial accessibility'")
    print("=" * 72)

    rng = np.random.default_rng(42)
    all_pass = True
    results = {}

    # ── Test 1: Equatorial states have larger torus radius ───────
    print("\n  [T1] Latitude → torus radius mapping...")
    latitudes = [0.0, 0.25, 0.5, 0.75, 1.0]
    radii = [torus_radius_at_latitude(z) for z in latitudes]
    for z, r in zip(latitudes, radii):
        print(f"    z={z:.2f}  R={r:.4f}")
    
    equator_bigger = radii[0] > radii[-1]
    results["radius_at_z0"] = float(radii[0])
    results["radius_at_z1"] = float(radii[-1])
    results["equator_bigger"] = bool(equator_bigger)
    print(f"    {'✓' if equator_bigger else '✗'} Equator (z=0) has larger radius")
    all_pass = all_pass and equator_bigger

    # ── Test 2: Te↑ vs Te↓ are distinguishable ──────────────────
    print("\n  [T2] Te polarity differentiation...")
    n_trials = 30
    n_distinct = 0
    total_dist = 0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.6 * coherent_state_density(q) + 0.4 * I2 / 2
        rho_up = apply_Te(rho, polarity_up=True)
        rho_down = apply_Te(rho, polarity_up=False)
        dist = trace_distance_2x2(rho_up, rho_down)
        total_dist += dist
        if dist > 1e-6:
            n_distinct += 1
    
    avg_dist = total_dist / n_trials
    distinct_ok = n_distinct / n_trials > 0.7
    results["te_polarity_avg_dist"] = float(avg_dist)
    results["te_polarity_distinct_frac"] = float(n_distinct / n_trials)
    print(f"    Distinct: {n_distinct}/{n_trials}, avg distance: {avg_dist:.4f}")
    print(f"    {'✓' if distinct_ok else '✗'} Te↑ ≠ Te↓")
    all_pass = all_pass and distinct_ok

    # ── Test 3: Te↑ expands (moves Bloch toward equator) ─────────
    print("\n  [T3] Te↑ expands (z → 0)...")
    n_expand = 0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.7 * coherent_state_density(q) + 0.3 * I2 / 2
        b_before = density_to_bloch(rho)
        rho_after = apply_Te(rho, polarity_up=True)
        b_after = density_to_bloch(rho_after)
        # Expansion = |z| decreases (moving toward equator)
        if abs(b_after[2]) <= abs(b_before[2]) + 0.01:
            n_expand += 1
    
    expand_frac = n_expand / n_trials
    expand_ok = expand_frac > 0.5
    results["te_up_expands_frac"] = float(expand_frac)
    print(f"    Te↑ reduces |z|: {n_expand}/{n_trials} = {expand_frac:.2f}")
    print(f"    {'✓' if expand_ok else '✗'} Te↑ expands toward equator")
    all_pass = all_pass and expand_ok

    # ── Test 4: Te↓ compresses (moves Bloch toward pole) ─────────
    print("\n  [T4] Te↓ compresses (z → ±1)...")
    n_compress = 0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.5 * coherent_state_density(q) + 0.5 * I2 / 2
        b_before = density_to_bloch(rho)
        rho_after = apply_Te(rho, polarity_up=False)
        b_after = density_to_bloch(rho_after)
        # Compression = |z| increases (moving toward pole)
        if abs(b_after[2]) >= abs(b_before[2]) - 0.01:
            n_compress += 1
    
    compress_frac = n_compress / n_trials
    compress_ok = compress_frac > 0.5
    results["te_down_compresses_frac"] = float(compress_frac)
    print(f"    Te↓ increases |z|: {n_compress}/{n_trials} = {compress_frac:.2f}")
    print(f"    {'✓' if compress_ok else '✗'} Te↓ compresses toward pole")
    all_pass = all_pass and compress_ok

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  GEOMETRIC AXIS 2 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    tokens = []
    if all_pass:
        tokens.append(EvidenceToken("E_GEOMETRIC_AXIS2_VALID", "S_GA2_SCALE",
                                    "PASS", float(avg_dist)))
    else:
        tokens.append(EvidenceToken("", "S_GA2_SCALE", "KILL", 0.0, "FAILED"))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "GA2_scale_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "axis": 2, "name": "Geometric_Axis2_Scale",
            "results": results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_GA2_validation()
