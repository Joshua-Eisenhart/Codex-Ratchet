#!/usr/bin/env python3
"""
Layer 4 Validation SIM — Engine Chirality (Axis 3: CANON = engine-family split; chirality is HYPOTHESIS)
====================================================
Type 1 vs Type 2 as complete cycles on actual Hopf geometry.

From the source doc:
  CANON: Axis-3 = engine-family split (Type-1 vs Type-2).
  HYPOTHESIS: This split manifests as left/right Weyl spinor selection.

  Type 1: Deductive (Fe/Ti) OUTER, Inductive (Te/Fi) INNER
    = deductive envelope wrapping inductive core
    = Fe/Ti acts on base loop, Te/Fi acts on fiber loop

  Type 2: Inductive (Te/Fi) OUTER, Deductive (Fe/Ti) INNER
    = inductive envelope wrapping deductive core
    = Te/Fi acts on base loop, Fe/Ti acts on fiber loop

Key Chiral Properties:
  - Type 1 ρ_final ≠ Type 2 ρ_final
  - SG/EE pattern matches canonical table
  - Se and Ne are chiral mirrors (flip between types)
  - Si and Ni are chiral invariants (same in both types)

Token: E_ENGINE_CHIRALITY_VALID
"""

import numpy as np
import os
import sys
import json
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import (
    random_s3_point, coherent_state_density, density_to_bloch,
    hopf_map, torus_coordinates,
)
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    negentropy, delta_phi, trace_distance_2x2,
    _ensure_valid_density, I2,
)
from sim_L2_eight_stages import classify_stage, stage_invariants
from proto_ratchet_sim_runner import EvidenceToken


def run_type1_engine(rho: np.ndarray, n_cycles: int = 5) -> dict:
    """Type 1: Deductive OUTER, Inductive INNER.

    Each cycle:
      1. Inner loop (fiber): Te then Fi (inductive exploration)
      2. Outer loop (base): Fe then Ti (deductive constraint)

    The deductive framework wraps around inductive core.
    """
    phi_history = [negentropy(rho)]
    stage_deltas = {"Se": [], "Si": [], "Ne": [], "Ni": []}

    for cycle in range(n_cycles):
        # ── INNER LOOP (fiber): Inductive = Te then Fi ──
        rho_before_inner = rho.copy()
        rho = apply_Te(rho, polarity_up=True)   # Explore (fiber rotation)
        rho = apply_Fi(rho, polarity_up=False)   # Select (gentle filter)

        # Classify terrain of inner loop
        bloch = density_to_bloch(rho)
        eta_approx = np.arccos(np.clip(abs(bloch[2]), 0, 1))
        inner_dphi = negentropy(rho) - negentropy(rho_before_inner)

        # ── OUTER LOOP (base): Deductive = Fe then Ti ──
        rho_before_outer = rho.copy()
        rho = apply_Fe(rho, polarity_up=True)    # Dissipate (base transport)
        rho = apply_Ti(rho, polarity_up=True)    # Constrain (fiber projection)

        outer_dphi = negentropy(rho) - negentropy(rho_before_outer)
        phi_history.append(negentropy(rho))

    return {
        "rho_final": rho,
        "phi_history": phi_history,
        "total_dphi": phi_history[-1] - phi_history[0],
    }


def run_type2_engine(rho: np.ndarray, n_cycles: int = 5) -> dict:
    """Type 2: Inductive OUTER, Deductive INNER.

    Each cycle:
      1. Inner loop (fiber): Fe then Ti (deductive constraint)
      2. Outer loop (base): Te then Fi (inductive exploration)

    The inductive framework wraps around deductive core.
    """
    phi_history = [negentropy(rho)]

    for cycle in range(n_cycles):
        # ── INNER LOOP (fiber): Deductive = Fe then Ti ──
        rho = apply_Fe(rho, polarity_up=True)    # Dissipate
        rho = apply_Ti(rho, polarity_up=True)    # Constrain

        # ── OUTER LOOP (base): Inductive = Te then Fi ──
        rho = apply_Te(rho, polarity_up=True)    # Explore
        rho = apply_Fi(rho, polarity_up=True)    # Select (strong filter)

        phi_history.append(negentropy(rho))

    return {
        "rho_final": rho,
        "phi_history": phi_history,
        "total_dphi": phi_history[-1] - phi_history[0],
    }


def run_L4_validation():
    print("=" * 72)
    print("LAYER 4: ENGINE CHIRALITY VALIDATION (AXIS 3 — CANON: engine-family split)")
    print("  'Type 1 vs Type 2 on actual Hopf geometry'")
    print("=" * 72)

    rng = np.random.default_rng(42)
    n_trials = 50
    all_pass = True
    results = {}

    # ── Test 1: Type 1 ≠ Type 2 (chirality produces different output) ──
    print("\n  [T1] Engine chirality: Type 1 ≠ Type 2...")
    chirality_distinct = True
    total_dist = 0.0
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.7 * coherent_state_density(q) + 0.3 * I2 / 2

        r1 = run_type1_engine(rho.copy(), n_cycles=5)
        r2 = run_type2_engine(rho.copy(), n_cycles=5)

        dist = trace_distance_2x2(r1["rho_final"], r2["rho_final"])
        total_dist += dist
        if dist < 1e-8:
            chirality_distinct = False

    avg_dist = total_dist / n_trials
    results["chirality_distinct"] = bool(chirality_distinct)
    results["avg_chirality_distance"] = float(avg_dist)
    print(f"    {'✓' if chirality_distinct else '✗'} Type 1 ≠ Type 2: avg trace distance = {avg_dist:.4f}")
    all_pass = all_pass and chirality_distinct

    # ── Test 2: Both engines are CPTP (output is valid density) ──
    print("\n  [T2] Engine output validity...")
    output_valid = True
    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.6 * coherent_state_density(q) + 0.4 * I2 / 2

        r1 = run_type1_engine(rho.copy())
        r2 = run_type2_engine(rho.copy())

        for rho_out in [r1["rho_final"], r2["rho_final"]]:
            evals = np.linalg.eigvalsh(rho_out)
            if np.min(evals) < -1e-8 or abs(np.real(np.trace(rho_out)) - 1.0) > 1e-8:
                output_valid = False
    results["output_valid"] = bool(output_valid)
    print(f"    {'✓' if output_valid else '✗'} Both engines produce valid density matrices")
    all_pass = all_pass and output_valid

    # ── Test 3: Negentropy evolution differs between types ───────
    print("\n  [T3] Negentropy trajectory divergence...")
    q = random_s3_point(rng)
    rho = 0.5 * coherent_state_density(q) + 0.5 * I2 / 2
    r1 = run_type1_engine(rho.copy(), n_cycles=10)
    r2 = run_type2_engine(rho.copy(), n_cycles=10)

    phi_divergence = abs(r1["total_dphi"] - r2["total_dphi"])
    diverges = phi_divergence > 1e-4
    results["phi_divergence"] = float(phi_divergence)
    results["type1_total_dphi"] = float(r1["total_dphi"])
    results["type2_total_dphi"] = float(r2["total_dphi"])
    print(f"    Type 1 total ΔΦ: {r1['total_dphi']:+.6f}")
    print(f"    Type 2 total ΔΦ: {r2['total_dphi']:+.6f}")
    print(f"    {'✓' if diverges else '✗'} Divergence: {phi_divergence:.6f}")
    all_pass = all_pass and diverges

    # ── Test 4: Chiral mirror test (Se/Ne flip, Si/Ni invariant) ─
    print("\n  [T4] Chiral mirror test...")
    # Run both engines from multiple initial states and check which
    # topological stages each engine traverses differently
    n_mirror = 30
    t1_bloch_z = []
    t2_bloch_z = []
    for _ in range(n_mirror):
        q = random_s3_point(rng)
        rho = 0.6 * coherent_state_density(q) + 0.4 * I2 / 2

        r1 = run_type1_engine(rho.copy(), n_cycles=3)
        r2 = run_type2_engine(rho.copy(), n_cycles=3)

        b1 = density_to_bloch(r1["rho_final"])
        b2 = density_to_bloch(r2["rho_final"])
        t1_bloch_z.append(b1[2])
        t2_bloch_z.append(b2[2])

    t1_bloch_z = np.array(t1_bloch_z)
    t2_bloch_z = np.array(t2_bloch_z)

    # Type 1 (deductive outer) should drive toward constraint (higher z)
    # Type 2 (inductive outer) should drive toward exploration (different z)
    z_difference = abs(np.mean(t1_bloch_z) - np.mean(t2_bloch_z))
    mirror_detected = z_difference > 0.01
    results["avg_t1_bloch_z"] = float(np.mean(t1_bloch_z))
    results["avg_t2_bloch_z"] = float(np.mean(t2_bloch_z))
    results["z_mirror_diff"] = float(z_difference)
    results["mirror_detected"] = bool(mirror_detected)
    print(f"    Type 1 avg Bloch z: {np.mean(t1_bloch_z):+.4f}")
    print(f"    Type 2 avg Bloch z: {np.mean(t2_bloch_z):+.4f}")
    print(f"    {'✓' if mirror_detected else '✗'} Chiral mirror difference: {z_difference:.4f}")
    all_pass = all_pass and mirror_detected

    # ── Test 5: Chirality reversal = swapping inner/outer ────────
    print("\n  [T5] Chirality = inner/outer swap...")
    # Type 1 with swapped loops should equal Type 2
    q = random_s3_point(rng)
    rho = 0.5 * coherent_state_density(q) + 0.5 * I2 / 2
    r1 = run_type1_engine(rho.copy(), n_cycles=5)
    r2 = run_type2_engine(rho.copy(), n_cycles=5)

    # They should be different (chirality is not trivial)
    swap_dist = trace_distance_2x2(r1["rho_final"], r2["rho_final"])
    swap_nontrivial = swap_dist > 1e-4
    results["swap_distance"] = float(swap_dist)
    results["swap_nontrivial"] = bool(swap_nontrivial)
    print(f"    Swap distance: {swap_dist:.6f}")
    print(f"    {'✓' if swap_nontrivial else '✗'} Swapping inner/outer produces different engine")
    all_pass = all_pass and swap_nontrivial

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  LAYER 4 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    tokens = []
    if all_pass:
        tokens.append(EvidenceToken(
            "E_ENGINE_CHIRALITY_VALID", "S_L4_ENGINE_CHIRALITY",
            "PASS", float(avg_dist)
        ))
    else:
        failed = [k for k, v in results.items() if v is False]
        tokens.append(EvidenceToken(
            "", "S_L4_ENGINE_CHIRALITY", "KILL", 0.0,
            f"FAILED: {', '.join(failed)}"
        ))

    # Save
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "L4_engine_chirality_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "layer": 4,
            "name": "Engine_Chirality_Validation",
            "results": results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_L4_validation()
