#!/usr/bin/env python3
"""
Geometric Axis 0 — Entropic Gradient on S³
=============================================
Axis 0 = the dimensionality / coarse-graining degree of freedom.

On the Hopf manifold, Axis 0 is realized as the number of
distinguishable fibers sampled on S². More fibers = more
degrees of freedom = higher entropy ceiling.

Geometric construction:
  1. Sample N points on S² (base space)
  2. Lift each to S³ via Hopf fiber
  3. Build N-qubit density matrix from coherent states
  4. Coarse-grain by tracing out fibers
  5. Measure: S(ρ_N) > S(ρ_{N-1}) monotonically

This is the GEOMETRIC version of axis0_correlation_sim.py.
Instead of generic bipartite entanglement, it uses actual
Hopf fibers as the subsystems.

Token: E_GEOMETRIC_AXIS0_VALID
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
    hopf_map, berry_phase, torus_coordinates,
)
from geometric_operators import negentropy, _ensure_valid_density, I2
from proto_ratchet_sim_runner import EvidenceToken


def von_neumann_entropy_2x2(rho):
    """Von Neumann entropy S = -Tr(ρ log ρ) for 2x2."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals)))


def coarse_grain_fibers(points_s3, n_keep):
    """Build a mixed state from n_keep fibers, trace out the rest.
    
    Each S³ point defines a coherent state |ψ⟩ on a 2D Hilbert space.
    Mixing N coherent states from different fibers creates a density
    matrix that captures N/total of the manifold's information.
    """
    rho = np.zeros((2, 2), dtype=complex)
    for i in range(n_keep):
        rho_i = coherent_state_density(points_s3[i])
        rho += rho_i
    rho /= n_keep
    return _ensure_valid_density(rho)


def run_GA0_validation():
    print("=" * 72)
    print("GEOMETRIC AXIS 0: ENTROPIC GRADIENT ON S³")
    print("  'More fibers sampled = higher entropy'")
    print("=" * 72)

    rng = np.random.default_rng(42)
    all_pass = True
    results = {}

    # ── Test 1: Entropy monotonically increases with fiber count ──
    print("\n  [T1] Entropy vs fiber count...")
    N_max = 32
    points = [random_s3_point(rng) for _ in range(N_max)]
    
    entropies = []
    for n in [1, 2, 4, 8, 16, 32]:
        rho = coarse_grain_fibers(points, n)
        S = von_neumann_entropy_2x2(rho)
        entropies.append(S)
        print(f"    N={n:3d}  S(ρ) = {S:.4f}")
    
    monotone = all(entropies[i] <= entropies[i+1] + 1e-10 for i in range(len(entropies)-1))
    results["entropy_series"] = entropies
    results["monotone"] = bool(monotone)
    print(f"    {'✓' if monotone else '✗'} Entropy monotonically increases")
    all_pass = all_pass and monotone

    # ── Test 2: Single fiber = pure state (S=0) ──────────────────
    print("\n  [T2] Single fiber = pure state...")
    rho_1 = coarse_grain_fibers(points, 1)
    S_1 = von_neumann_entropy_2x2(rho_1)
    is_pure = S_1 < 0.01
    results["single_fiber_entropy"] = float(S_1)
    results["single_fiber_pure"] = bool(is_pure)
    print(f"    S(single fiber) = {S_1:.6f}")
    print(f"    {'✓' if is_pure else '✗'} Pure state (S ≈ 0)")
    all_pass = all_pass and is_pure

    # ── Test 3: Many fibers → maximally mixed (S≈1) ─────────────
    print("\n  [T3] Many fibers → maximally mixed...")
    rho_many = coarse_grain_fibers(points, N_max)
    S_many = von_neumann_entropy_2x2(rho_many)
    near_max = S_many > 0.8  # Max is 1 bit for 2x2
    results["many_fiber_entropy"] = float(S_many)
    results["near_max_mixed"] = bool(near_max)
    print(f"    S({N_max} fibers) = {S_many:.4f}")
    print(f"    {'✓' if near_max else '✗'} Near maximally mixed (S > 0.8)")
    all_pass = all_pass and near_max

    # ── Test 4: Axis 0 coordinate = entropic gradient ────────────
    print("\n  [T4] Axis 0 as gradient between pure and mixed...")
    n_trials = 20
    gradients = []
    for _ in range(n_trials):
        pts = [random_s3_point(rng) for _ in range(8)]
        rho_few = coarse_grain_fibers(pts, 2)
        rho_more = coarse_grain_fibers(pts, 8)
        grad = von_neumann_entropy_2x2(rho_more) - von_neumann_entropy_2x2(rho_few)
        gradients.append(grad)
    
    avg_grad = np.mean(gradients)
    grad_positive = avg_grad > 0
    results["avg_gradient"] = float(avg_grad)
    results["gradient_positive"] = bool(grad_positive)
    print(f"    Avg entropy gradient (8 vs 2 fibers): {avg_grad:+.4f}")
    print(f"    {'✓' if grad_positive else '✗'} Gradient is positive")
    all_pass = all_pass and grad_positive

    # ── Test 5: Bloch vector spread increases with fiber count ────
    print("\n  [T5] Bloch vector spread vs fiber count...")
    pts = [random_s3_point(rng) for _ in range(16)]
    bloch_2 = density_to_bloch(coarse_grain_fibers(pts, 2))
    bloch_16 = density_to_bloch(coarse_grain_fibers(pts, 16))
    r_2 = np.linalg.norm(bloch_2)
    r_16 = np.linalg.norm(bloch_16)
    spread_increases = r_2 > r_16  # More mixing → smaller Bloch radius
    results["bloch_r_2"] = float(r_2)
    results["bloch_r_16"] = float(r_16)
    results["spread_increases"] = bool(spread_increases)
    print(f"    |r|(2 fibers) = {r_2:.4f}")
    print(f"    |r|(16 fibers) = {r_16:.4f}")
    print(f"    {'✓' if spread_increases else '✗'} More fibers → smaller Bloch radius (more mixed)")
    all_pass = all_pass and spread_increases

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  GEOMETRIC AXIS 0 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    tokens = []
    if all_pass:
        tokens.append(EvidenceToken("E_GEOMETRIC_AXIS0_VALID", "S_GA0_ENTROPIC_GRADIENT",
                                    "PASS", float(avg_grad)))
    else:
        tokens.append(EvidenceToken("", "S_GA0_ENTROPIC_GRADIENT", "KILL", 0.0,
                                    "FAILED"))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "GA0_entropic_gradient_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "axis": 0, "name": "Geometric_Axis0_Entropic_Gradient",
            "results": results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_GA0_validation()
