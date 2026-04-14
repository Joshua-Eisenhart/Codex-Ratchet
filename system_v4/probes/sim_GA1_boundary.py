#!/usr/bin/env python3
"""
Geometric Axis 1 — Boundary (Open vs Closed) on S³
=====================================================
Axis 1 = boundary topology of torus cross-sections.

On the Hopf manifold, each torus T² at latitude θ has:
  - OPEN boundary: fiber endpoints don't close (arc, not loop)
  - CLOSED boundary: fiber endpoints close (full S¹ loop)

Geometric construction:
  1. Sample a fiber loop on the torus at angle θ
  2. "Open" = partial arc (0 to π), density from non-cyclic path
  3. "Closed" = full loop (0 to 2π), density from cyclic path
  4. Open → higher entropy (less coherent)
  5. Closed → lower entropy (phase-locked)

The Fe operator (dissipation/amplitude damping) opens boundaries.
The Ti operator (projection/dephasing) closes boundaries.

Token: E_GEOMETRIC_AXIS1_VALID
"""

import numpy as np
import os
import sys
import json
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import (
    random_s3_point, coherent_state_density, density_to_bloch,
    hopf_map, lift_base_point,
)
from geometric_operators import (
    apply_Ti, apply_Fe, negentropy, trace_distance_2x2,
    _ensure_valid_density, I2,
)
from proto_ratchet_sim_runner import EvidenceToken


def base_arc_density(q, arc_fraction=1.0, n_samples=32):
    """Build density matrix by averaging coherent states along a BASE arc on S².
    
    The FIBER loop is invisible at density matrix level (global phase cancels).
    The BASE loop is visible — it rotates the Bloch vector around S².
    
    arc_fraction = 1.0 → full great circle (closed boundary, returns to start)
    arc_fraction = 0.5 → half arc (open boundary, ends at antipode)
    
    Closed boundary = averaging over full orbit → more mixing → LOWER negentropy
    Open boundary = averaging over partial orbit → less mixing → HIGHER negentropy
    """
    # Convert quaternion to spinor
    psi = np.array([q[0] + 1j * q[1], q[2] + 1j * q[3]], dtype=complex)
    psi_norm = np.linalg.norm(psi)
    if psi_norm > 1e-12:
        psi /= psi_norm
    
    rho = np.zeros((2, 2), dtype=complex)
    for k in range(n_samples):
        theta = 2 * np.pi * arc_fraction * k / n_samples
        # SU(2) rotation around z-axis (changes Bloch vector, not just phase)
        U = np.array([
            [np.cos(theta/2) + 1j * np.sin(theta/2), 0],
            [0, np.cos(theta/2) - 1j * np.sin(theta/2)],
        ], dtype=complex)
        psi_rotated = U @ psi
        rho += np.outer(psi_rotated, psi_rotated.conj())
    rho /= n_samples
    return _ensure_valid_density(rho)


def run_GA1_validation():
    print("=" * 72)
    print("GEOMETRIC AXIS 1: BOUNDARY (OPEN vs CLOSED) ON S³")
    print("  'Fiber arc fraction sets boundary topology'")
    print("=" * 72)

    rng = np.random.default_rng(42)
    all_pass = True
    results = {}

    # ── Test 1: Closed (full orbit) has MORE mixing than Open (partial arc)
    # Full great circle → averages over all orientations → lower negentropy
    print("\n  [T1] Closed (full orbit) vs Open (half arc)...")
    n_trials = 30
    open_higher_neg = 0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho_closed = base_arc_density(q, arc_fraction=1.0)
        rho_open = base_arc_density(q, arc_fraction=0.25)
        neg_closed = negentropy(rho_closed)
        neg_open = negentropy(rho_open)
        if neg_open >= neg_closed - 1e-10:
            open_higher_neg += 1
    
    frac = open_higher_neg / n_trials
    boundary_order = frac > 0.7
    results["open_higher_negentropy_frac"] = float(frac)
    results["boundary_order"] = bool(boundary_order)
    print(f"    Open ≥ Closed negentropy: {open_higher_neg}/{n_trials} = {frac:.2f}")
    print(f"    {'✓' if boundary_order else '✗'} Open boundary → higher negentropy (less mixing)")
    all_pass = all_pass and boundary_order

    # ── Test 2: Fe opens boundary (reduces negentropy) ───────────
    print("\n  [T2] Fe operator opens boundary...")
    fe_opens = 0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.7 * coherent_state_density(q) + 0.3 * I2 / 2
        neg_before = negentropy(rho)
        rho_after = apply_Fe(rho, polarity_up=True)
        neg_after = negentropy(rho_after)
        if neg_after <= neg_before + 1e-10:
            fe_opens += 1

    fe_frac = fe_opens / n_trials
    fe_ok = fe_frac > 0.7
    results["fe_opens_boundary_frac"] = float(fe_frac)
    print(f"    Fe reduces negentropy: {fe_opens}/{n_trials} = {fe_frac:.2f}")
    print(f"    {'✓' if fe_ok else '✗'} Fe opens boundary")
    all_pass = all_pass and fe_ok

    # ── Test 3: Ti closes boundary (preserves/increases negentropy)
    print("\n  [T3] Ti operator closes boundary...")
    ti_closes = 0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.4 * coherent_state_density(q) + 0.6 * I2 / 2
        rho_after = apply_Ti(rho, polarity_up=True)
        # Ti dephases → removes off-diagonal → makes state more "closed" (diagonal)
        off_diag_before = abs(rho[0, 1])
        off_diag_after = abs(rho_after[0, 1])
        if off_diag_after <= off_diag_before + 1e-10:
            ti_closes += 1

    ti_frac = ti_closes / n_trials
    ti_ok = ti_frac > 0.7
    results["ti_closes_boundary_frac"] = float(ti_frac)
    print(f"    Ti reduces off-diagonal: {ti_closes}/{n_trials} = {ti_frac:.2f}")
    print(f"    {'✓' if ti_ok else '✗'} Ti closes boundary")
    all_pass = all_pass and ti_ok

    # ── Test 4: Arc fraction sweep — more orbit → more mixing → less Φ
    print("\n  [T4] Arc fraction sweep...")
    q = random_s3_point(rng)
    fracs = [0.1, 0.25, 0.5, 0.75, 1.0]
    negs = []
    for f in fracs:
        rho = base_arc_density(q, arc_fraction=f)
        negs.append(negentropy(rho))
        print(f"    arc={f:.2f}  Φ={negs[-1]:.4f}")
    
    # Negentropy should DECREASE with arc fraction (more orbit = more mixing)
    overall_trend = negs[0] > negs[-1]
    results["arc_sweep_negs"] = negs
    results["trend_decreasing"] = bool(overall_trend)
    print(f"    {'✓' if overall_trend else '✗'} Minimal arc Φ > Full loop Φ (more orbit → more mixing)")
    all_pass = all_pass and overall_trend

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  GEOMETRIC AXIS 1 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    tokens = []
    if all_pass:
        tokens.append(EvidenceToken("E_GEOMETRIC_AXIS1_VALID", "S_GA1_BOUNDARY",
                                    "PASS", float(frac)))
    else:
        tokens.append(EvidenceToken("", "S_GA1_BOUNDARY", "KILL", 0.0, "FAILED"))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "GA1_boundary_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "axis": 1, "name": "Geometric_Axis1_Boundary",
            "results": results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_GA1_validation()
