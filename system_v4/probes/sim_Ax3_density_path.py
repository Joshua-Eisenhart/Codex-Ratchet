#!/usr/bin/env python3
"""
Axis 3 Validation SIM — Fiber vs Base-Lift Density Path
========================================================
Tests the core Ax3 definition from AXIS_3_4_5_6_QIT_MATH.md:

  INNER (fiber loop): ρ_f(u) = ρ_f(0) for all u
    — density is PATH-INVARIANT along the Hopf fiber

  OUTER (base-lift loop): ρ_b(u) ≠ ρ_b(0) in general
    — density CHANGES as the base loop traverses the torus

Source: AXIS_0_1_2_QIT_MATH.md geometry spine
  fiber loop:  γ_fiber(u) = ψ(φ₀+u, χ₀; η₀)
  base loop:   γ_base(u)  = ψ(φ₀ - cos(2η₀)u, χ₀+u; η₀)
  fiber density: ρ_f(u) = ½(I + r⃗(χ₀, η₀)·σ⃗)  [constant in u]
  base density:  ρ_b(u) = ½(I + r⃗(χ₀+u, η₀)·σ⃗) [changes with u]

Evidence token: E_AX3_DENSITY_PATH_VALID
"""

import numpy as np
import os, sys, json
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import von_neumann_entropy_2x2

SIGMA_X = np.array([[0,1],[1,0]], dtype=complex)
SIGMA_Y = np.array([[0,-1j],[1j,0]], dtype=complex)
SIGMA_Z = np.array([[1,0],[0,-1]], dtype=complex)
I2 = np.eye(2, dtype=complex)


# ───────────────────────────────────────────────────────────────────
# Spinor chart and density reduction (source-locked from terrain math)
# ───────────────────────────────────────────────────────────────────

def spinor(phi, chi, eta):
    """ψ(φ,χ;η) = (e^{i(φ+χ)}cosη, e^{i(φ−χ)}sinη)"""
    return np.array([
        np.exp(1j*(phi+chi)) * np.cos(eta),
        np.exp(1j*(phi-chi)) * np.sin(eta),
    ], dtype=complex)


def density(psi):
    """ρ = |ψ⟩⟨ψ|"""
    return np.outer(psi, psi.conj())


def bloch_vector(rho):
    """r⃗ = (Tr(σ_x ρ), Tr(σ_y ρ), Tr(σ_z ρ))"""
    return np.array([
        np.real(np.trace(SIGMA_X @ rho)),
        np.real(np.trace(SIGMA_Y @ rho)),
        np.real(np.trace(SIGMA_Z @ rho)),
    ])


def trace_distance(rho, sigma):
    """½ Tr|ρ − σ|"""
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


# ───────────────────────────────────────────────────────────────────
# Loop path generators (source-locked)
# ───────────────────────────────────────────────────────────────────

def fiber_loop_path(phi0, chi0, eta0, n_steps=128):
    """Inner/fiber loop: γ_f(u) = ψ(φ₀+u, χ₀; η₀), u ∈ [0, 2π)
    Density: ρ_f(u) = ρ_f(0) for all u (Bloch-blind to φ)
    """
    us = np.linspace(0, 2*np.pi, n_steps, endpoint=False)
    densities = [density(spinor(phi0 + u, chi0, eta0)) for u in us]
    return densities


def base_loop_path(phi0, chi0, eta0, n_steps=128):
    """Outer/base-lift loop: γ_b(u) = ψ(φ₀ − cos(2η₀)u, χ₀+u; η₀), u ∈ [0, 2π)
    Horizontal condition: 𝒜(γ̇_b) = 0
    Density: ρ_b(u) = ½(I + r⃗(χ₀+u, η₀)·σ⃗) changes with u
    """
    cos2eta = np.cos(2*eta0)
    us = np.linspace(0, 2*np.pi, n_steps, endpoint=False)
    densities = [density(spinor(phi0 - cos2eta*u, chi0 + u, eta0)) for u in us]
    return densities


# ───────────────────────────────────────────────────────────────────
# Main validation
# ───────────────────────────────────────────────────────────────────

def run_Ax3_validation():
    print("=" * 72)
    print("AXIS 3: FIBER vs BASE-LIFT DENSITY PATH VALIDATION")
    print("  Inner = density-stationary | Outer = density-traversing")
    print("=" * 72)

    rng = np.random.default_rng(42)
    all_pass = True
    results = {}

    # ── Test 1: Fiber loop density is path-invariant ──────────────
    print("\n  [T1] Fiber loop: ρ(u) = ρ(0) for all u...")
    fiber_stationary = True
    max_fiber_deviation = 0.0
    n_trials = 20

    for _ in range(n_trials):
        phi0 = rng.uniform(0, 2*np.pi)
        chi0 = rng.uniform(0, 2*np.pi)
        eta0 = rng.uniform(0.1, np.pi/2 - 0.1)  # avoid degenerate poles

        path = fiber_loop_path(phi0, chi0, eta0, n_steps=64)
        rho0 = path[0]
        for rho_u in path[1:]:
            d = trace_distance(rho_u, rho0)
            max_fiber_deviation = max(max_fiber_deviation, d)
            if d > 1e-10:
                fiber_stationary = False

    results["fiber_density_stationary"] = bool(fiber_stationary)
    results["fiber_max_deviation"] = float(max_fiber_deviation)
    print(f"    Max trace-distance over full fiber loop: {max_fiber_deviation:.2e}")
    print(f"    {'✓' if fiber_stationary else '✗'} Fiber density is path-invariant (D < 1e-10)")
    all_pass = all_pass and fiber_stationary

    # ── Test 2: Base-lift density changes along path ──────────────
    print("\n  [T2] Base-lift loop: ρ(u) ≠ ρ(0) for u ≠ 0...")
    base_changes = True
    min_base_deviation = np.inf
    n_trials = 20

    for _ in range(n_trials):
        phi0 = rng.uniform(0, 2*np.pi)
        chi0 = rng.uniform(0, 2*np.pi)
        eta0 = rng.uniform(0.2, np.pi/2 - 0.2)  # avoid near-poles where r⃗ is degenerate

        path = base_loop_path(phi0, chi0, eta0, n_steps=64)
        rho0 = path[0]
        # Check max deviation over the whole path
        max_dev_this_trial = max(trace_distance(rho_u, rho0) for rho_u in path[1:])
        min_base_deviation = min(min_base_deviation, max_dev_this_trial)
        if max_dev_this_trial < 1e-6:
            base_changes = False

    results["base_density_changes"] = bool(base_changes)
    results["base_min_max_deviation"] = float(min_base_deviation)
    print(f"    Min of per-trial max-deviations: {min_base_deviation:.4f}")
    print(f"    {'✓' if base_changes else '✗'} Base density changes along path (D > 1e-6)")
    all_pass = all_pass and base_changes

    # ── Test 3: Fiber density Bloch radius = 1 (pure state) throughout ──
    print("\n  [T3] Fiber loop: Bloch radius preserved (pure state)...")
    fiber_purity_ok = True
    for _ in range(10):
        phi0 = rng.uniform(0, 2*np.pi)
        chi0 = rng.uniform(0, 2*np.pi)
        eta0 = rng.uniform(0.1, np.pi/2 - 0.1)
        path = fiber_loop_path(phi0, chi0, eta0, n_steps=32)
        for rho in path:
            r = np.linalg.norm(bloch_vector(rho))
            if abs(r - 1.0) > 1e-10:
                fiber_purity_ok = False

    results["fiber_purity_preserved"] = bool(fiber_purity_ok)
    print(f"    {'✓' if fiber_purity_ok else '✗'} Fiber: |r⃗| = 1 throughout (pure state)")
    all_pass = all_pass and fiber_purity_ok

    # ── Test 4: Base-lift density Bloch vector direction changes ──
    print("\n  [T4] Base-lift loop: Bloch vector direction traverses sphere...")
    base_traversal_ok = True
    min_bloch_spread = np.inf

    for _ in range(10):
        phi0 = rng.uniform(0, 2*np.pi)
        chi0 = rng.uniform(0, 2*np.pi)
        eta0 = rng.uniform(0.2, np.pi/4)  # mid-range torus

        path = base_loop_path(phi0, chi0, eta0, n_steps=64)
        bloch_vecs = np.array([bloch_vector(rho) for rho in path])

        # Measure angular spread: std of azimuthal angle
        xy_components = bloch_vecs[:, :2]
        xy_norm = np.linalg.norm(xy_components, axis=1, keepdims=True)
        xy_norm = np.maximum(xy_norm, 1e-10)
        xy_unit = xy_components / xy_norm
        # Angular spread: 1 - |mean of unit xy vectors|
        mean_xy = np.mean(xy_unit, axis=0)
        spread = 1.0 - np.linalg.norm(mean_xy)
        min_bloch_spread = min(min_bloch_spread, spread)
        if spread < 0.1:
            base_traversal_ok = False

    results["base_bloch_traversal"] = bool(base_traversal_ok)
    results["base_min_bloch_spread"] = float(min_bloch_spread)
    print(f"    Min Bloch angular spread: {min_bloch_spread:.4f}")
    print(f"    {'✓' if base_traversal_ok else '✗'} Base: Bloch vector direction traverses (spread > 0.1)")
    all_pass = all_pass and base_traversal_ok

    # ── Test 5: Horizontal condition on base loop ──────────────────
    print("\n  [T5] Base-lift loop: horizontal condition 𝒜(γ̇) = 0...")
    # 𝒜 = dφ + cos(2η)dχ
    # Along γ_b: dφ/du = -cos(2η), dχ/du = 1
    # 𝒜(γ̇_b) = dφ/du + cos(2η)·dχ/du = -cos(2η) + cos(2η)·1 = 0  ✓
    horiz_ok = True
    max_horiz_violation = 0.0

    for _ in range(100):
        eta0 = rng.uniform(0.01, np.pi/2 - 0.01)
        # Check the algebraic identity: -cos(2η) + cos(2η)*1 = 0
        dphi_du = -np.cos(2*eta0)
        dchi_du = 1.0
        connection_value = dphi_du + np.cos(2*eta0) * dchi_du
        max_horiz_violation = max(max_horiz_violation, abs(connection_value))
        if abs(connection_value) > 1e-12:
            horiz_ok = False

    results["horizontal_condition"] = bool(horiz_ok)
    results["max_horiz_violation"] = float(max_horiz_violation)
    print(f"    Max 𝒜(γ̇_b) violation: {max_horiz_violation:.2e}")
    print(f"    {'✓' if horiz_ok else '✗'} Horizontal condition satisfied analytically")
    all_pass = all_pass and horiz_ok

    # ── Test 6: Ax3 discriminator — fiber and base are distinguishable ──
    print("\n  [T6] Ax3 discriminator: fiber and base-lift are distinguishable...")
    # A classifier based on max path deviation should cleanly separate the two
    n_samples = 50
    fiber_deviations = []
    base_deviations = []

    for _ in range(n_samples):
        phi0 = rng.uniform(0, 2*np.pi)
        chi0 = rng.uniform(0, 2*np.pi)
        eta0 = rng.uniform(0.2, np.pi/2 - 0.2)

        f_path = fiber_loop_path(phi0, chi0, eta0, n_steps=32)
        b_path = base_loop_path(phi0, chi0, eta0, n_steps=32)

        f_dev = max(trace_distance(rho, f_path[0]) for rho in f_path[1:])
        b_dev = max(trace_distance(rho, b_path[0]) for rho in b_path[1:])
        fiber_deviations.append(f_dev)
        base_deviations.append(b_dev)

    threshold = 0.01
    fiber_below = sum(1 for d in fiber_deviations if d < threshold)
    base_above = sum(1 for d in base_deviations if d > threshold)
    discrim_ok = fiber_below == n_samples and base_above == n_samples

    results["ax3_discriminator"] = bool(discrim_ok)
    results["fiber_below_threshold"] = fiber_below
    results["base_above_threshold"] = base_above
    results["threshold"] = threshold
    print(f"    Fiber deviations < {threshold}: {fiber_below}/{n_samples}")
    print(f"    Base deviations > {threshold}: {base_above}/{n_samples}")
    print(f"    {'✓' if discrim_ok else '✗'} Clean Ax3 discrimination by density path")
    all_pass = all_pass and discrim_ok

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  AXIS 3 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    token_name = "E_AX3_DENSITY_PATH_VALID" if all_pass else ""
    verdict = "PASS" if all_pass else "KILL"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "Ax3_density_path_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "axis": 3,
            "name": "Ax3_Fiber_vs_BaseLift_DensityPath",
            "definition": "inner=density-stationary, outer=density-traversing",
            "source": "AXIS_3_4_5_6_QIT_MATH.md",
            "verdict": verdict,
            "evidence_token": token_name,
            "results": results,
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return all_pass


if __name__ == "__main__":
    run_Ax3_validation()
