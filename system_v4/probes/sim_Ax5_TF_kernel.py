#!/usr/bin/env python3
"""
Axis 5 Validation SIM — T-kernel vs F-kernel (Dephasing vs Rotation)
=====================================================================
Tests the Ax5 definition from AXIS_3_4_5_6_QIT_MATH.md using the
LOCKED operator math from v5_OPERATOR_MATH_LEDGER.md:

  T-kernel (Ti, Te): CPTP dephasing channels — kills off-diagonal elements
    Ti: ρ ↦ (1−q₁)ρ + q₁(P₀ρP₀ + P₁ρP₁)   [σ_z dephasing]
    Te: ρ ↦ (1−q₂)ρ + q₂(Q₊ρQ₊ + Q₋ρQ₋)   [σ_x dephasing]

  F-kernel (Fi, Fe): unitary *-automorphisms — preserves purity
    Fi: ρ ↦ U_x(θ)ρU_x(θ)†                  [x-axis rotation]
    Fe: ρ ↦ U_z(φ)ρU_z(φ)†                  [z-axis rotation]

IMPORTANT DISCREPANCY NOTE:
  geometric_operators.py (runtime implementation) diverges from this ledger:
  - apply_Fe is amplitude-damping (CPTP) — should be U_z rotation (unitary)
  - apply_Te is σ_y rotation (unitary) — should be σ_x dephasing (CPTP)
  This sim tests the LOCKED LEDGER math, not the runtime implementation.
  The discrepancy between spec and runtime is tracked as an open issue.

Evidence token: E_AX5_TF_KERNEL_VALID
"""

import numpy as np
import os, sys, json
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import random_s3_point, coherent_state_density, von_neumann_entropy_2x2

SIGMA_X = np.array([[0,1],[1,0]], dtype=complex)
SIGMA_Y = np.array([[0,-1j],[1j,0]], dtype=complex)
SIGMA_Z = np.array([[1,0],[0,-1]], dtype=complex)
I2 = np.eye(2, dtype=complex)

P0 = np.array([[1,0],[0,0]], dtype=complex)
P1 = np.array([[0,0],[0,1]], dtype=complex)
Q_plus  = 0.5 * np.array([[1,1],[1,1]], dtype=complex)
Q_minus = 0.5 * np.array([[1,-1],[-1,1]], dtype=complex)


# ───────────────────────────────────────────────────────────────────
# Locked operator implementations (from v5_OPERATOR_MATH_LEDGER.md)
# ───────────────────────────────────────────────────────────────────

def Ti_locked(rho, q1=0.7):
    """Ti: σ_z dephasing. ρ ↦ (1−q₁)ρ + q₁(P₀ρP₀ + P₁ρP₁)"""
    return (1 - q1)*rho + q1*(P0 @ rho @ P0 + P1 @ rho @ P1)


def Te_locked(rho, q2=0.7):
    """Te: σ_x dephasing. ρ ↦ (1−q₂)ρ + q₂(Q₊ρQ₊ + Q₋ρQ₋)"""
    return (1 - q2)*rho + q2*(Q_plus @ rho @ Q_plus + Q_minus @ rho @ Q_minus)


def Fi_locked(rho, theta=0.4):
    """Fi: U_x(θ) rotation. ρ ↦ U_x(θ) ρ U_x(θ)†"""
    Ux = np.cos(theta/2)*I2 - 1j*np.sin(theta/2)*SIGMA_X
    return Ux @ rho @ Ux.conj().T


def Fe_locked(rho, phi=0.4):
    """Fe: U_z(φ) rotation. ρ ↦ U_z(φ) ρ U_z(φ)†"""
    Uz = np.array([[np.exp(-1j*phi/2), 0], [0, np.exp(1j*phi/2)]], dtype=complex)
    return Uz @ rho @ Uz.conj().T


def trace_distance(rho, sigma):
    """½ Tr|ρ − σ|"""
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


def bloch_radius(rho):
    """||r⃗|| — purity proxy. 1 for pure, 0 for maximally mixed."""
    rx = np.real(np.trace(SIGMA_X @ rho))
    ry = np.real(np.trace(SIGMA_Y @ rho))
    rz = np.real(np.trace(SIGMA_Z @ rho))
    return np.sqrt(rx**2 + ry**2 + rz**2)


def off_diagonal_magnitude(rho):
    """|ρ₀₁| — off-diagonal coherence magnitude."""
    return abs(rho[0, 1])


# ───────────────────────────────────────────────────────────────────
# Main validation
# ───────────────────────────────────────────────────────────────────

def run_Ax5_validation():
    print("=" * 72)
    print("AXIS 5: T-KERNEL vs F-KERNEL VALIDATION (LOCKED OPERATOR MATH)")
    print("  T = {Ti, Te} dephasing channels | F = {Fi, Fe} unitary rotations")
    print("=" * 72)
    print()
    print("  NOTE: Testing v5_OPERATOR_MATH_LEDGER.md locked operators.")
    print("  geometric_operators.py runtime has Fe=amplitude-damping and")
    print("  Te=unitary (MISMATCH — tracked as open discrepancy).")
    print()

    rng = np.random.default_rng(42)
    n_trials = 100
    all_pass = True
    results = {}

    # ── Test 1: T-kernel reduces off-diagonal elements ────────────
    print("  [T1] T-kernel: Ti and Te reduce off-diagonal coherence...")
    T_reduces_coherence = True
    min_Ti_reduction = np.inf
    min_Te_reduction = np.inf

    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.7 * coherent_state_density(q) + 0.3 * I2 / 2

        before = off_diagonal_magnitude(rho)

        Ti_out = Ti_locked(rho)
        Te_out = Te_locked(rho)

        Ti_reduction = before - off_diagonal_magnitude(Ti_out)
        Te_reduction = before - off_diagonal_magnitude(Te_out)

        min_Ti_reduction = min(min_Ti_reduction, Ti_reduction)
        min_Te_reduction = min(min_Te_reduction, Te_reduction)

        if Ti_reduction < -1e-10 or Te_reduction < -1e-10:
            T_reduces_coherence = False

    results["T_reduces_coherence"] = bool(T_reduces_coherence)
    results["Ti_min_offdiag_reduction"] = float(min_Ti_reduction)
    results["Te_min_offdiag_reduction"] = float(min_Te_reduction)
    print(f"    Ti min reduction: {min_Ti_reduction:.4f}")
    print(f"    Te min reduction: {min_Te_reduction:.4f}")
    print(f"    {'✓' if T_reduces_coherence else '✗'} T-kernel never increases |ρ₀₁|")
    all_pass = all_pass and T_reduces_coherence

    # ── Test 2: F-kernel preserves purity (Bloch radius) ─────────
    print("\n  [T2] F-kernel: Fi and Fe preserve Bloch radius (purity)...")
    F_preserves_purity = True
    max_Fi_purity_change = 0.0
    max_Fe_purity_change = 0.0

    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = coherent_state_density(q)
        r_before = bloch_radius(rho)

        Fi_out = Fi_locked(rho)
        Fe_out = Fe_locked(rho)

        dFi = abs(bloch_radius(Fi_out) - r_before)
        dFe = abs(bloch_radius(Fe_out) - r_before)
        max_Fi_purity_change = max(max_Fi_purity_change, dFi)
        max_Fe_purity_change = max(max_Fe_purity_change, dFe)

        if dFi > 1e-10 or dFe > 1e-10:
            F_preserves_purity = False

    results["F_preserves_purity"] = bool(F_preserves_purity)
    results["Fi_max_purity_change"] = float(max_Fi_purity_change)
    results["Fe_max_purity_change"] = float(max_Fe_purity_change)
    print(f"    Fi max Bloch-radius change: {max_Fi_purity_change:.2e}")
    print(f"    Fe max Bloch-radius change: {max_Fe_purity_change:.2e}")
    print(f"    {'✓' if F_preserves_purity else '✗'} F-kernel preserves |r⃗| (unitary)")
    all_pass = all_pass and F_preserves_purity

    # ── Test 3: T-kernel eigenvalue spectrum changes ──────────────
    print("\n  [T3] T-kernel: CPTP — eigenvalues change (nonunitary)...")
    T_changes_evals = True
    Ti_eval_changes = []
    Te_eval_changes = []

    for _ in range(n_trials):
        q = random_s3_point(rng)
        # Start from a pure state where dephasing is maximally visible
        rho = coherent_state_density(q)
        # Rotate so off-diagonals are non-zero
        rho = 0.9 * rho + 0.1 * I2 / 2  # slight mixing to ensure nonzero off-diag

        evals_before = sorted(np.real(np.linalg.eigvalsh(rho)))

        Ti_out = Ti_locked(rho)
        Te_out = Te_locked(rho)

        Ti_eval_change = np.linalg.norm(
            np.array(sorted(np.real(np.linalg.eigvalsh(Ti_out)))) - evals_before
        )
        Te_eval_change = np.linalg.norm(
            np.array(sorted(np.real(np.linalg.eigvalsh(Te_out)))) - evals_before
        )
        Ti_eval_changes.append(Ti_eval_change)
        Te_eval_changes.append(Te_eval_change)

    avg_Ti_eval_change = float(np.mean(Ti_eval_changes))
    avg_Te_eval_change = float(np.mean(Te_eval_changes))
    # T-kernel SHOULD change eigenvalues (it increases von Neumann entropy)
    T_changes_evals = avg_Ti_eval_change > 1e-4 and avg_Te_eval_change > 1e-4
    results["T_changes_eigenvalues"] = bool(T_changes_evals)
    results["Ti_avg_eval_change"] = avg_Ti_eval_change
    results["Te_avg_eval_change"] = avg_Te_eval_change
    print(f"    Ti avg eigenvalue change: {avg_Ti_eval_change:.4f}")
    print(f"    Te avg eigenvalue change: {avg_Te_eval_change:.4f}")
    print(f"    {'✓' if T_changes_evals else '✗'} T-kernel changes eigenvalues (nonunitary CPTP)")
    all_pass = all_pass and T_changes_evals

    # ── Test 4: F-kernel preserves eigenvalues ────────────────────
    print("\n  [T4] F-kernel: unitary — eigenvalues preserved...")
    F_preserves_evals = True
    max_Fi_eval_change = 0.0
    max_Fe_eval_change = 0.0

    for _ in range(n_trials):
        q = random_s3_point(rng)
        rho = 0.7 * coherent_state_density(q) + 0.3 * I2 / 2
        evals_before = sorted(np.real(np.linalg.eigvalsh(rho)))

        Fi_out = Fi_locked(rho)
        Fe_out = Fe_locked(rho)

        dFi = np.linalg.norm(
            np.array(sorted(np.real(np.linalg.eigvalsh(Fi_out)))) - evals_before
        )
        dFe = np.linalg.norm(
            np.array(sorted(np.real(np.linalg.eigvalsh(Fe_out)))) - evals_before
        )
        max_Fi_eval_change = max(max_Fi_eval_change, dFi)
        max_Fe_eval_change = max(max_Fe_eval_change, dFe)

        if dFi > 1e-10 or dFe > 1e-10:
            F_preserves_evals = False

    results["F_preserves_eigenvalues"] = bool(F_preserves_evals)
    results["Fi_max_eval_change"] = float(max_Fi_eval_change)
    results["Fe_max_eval_change"] = float(max_Fe_eval_change)
    print(f"    Fi max eigenvalue change: {max_Fi_eval_change:.2e}")
    print(f"    Fe max eigenvalue change: {max_Fe_eval_change:.2e}")
    print(f"    {'✓' if F_preserves_evals else '✗'} F-kernel preserves eigenvalues (unitary)")
    all_pass = all_pass and F_preserves_evals

    # ── Test 5: Ti dephases in σ_z basis, Te in σ_x basis ────────
    print("\n  [T5] Basis specificity: Ti kills σ_z coherence, Te kills σ_x...")
    basis_ok = True

    # Ti kills off-diagonals in Z-basis: ρ₀₁ → 0
    rho_z = 0.5 * (I2 + 0.8 * SIGMA_X)  # coherent in z-basis
    Ti_out = Ti_locked(rho_z, q1=1.0)  # full dephasing
    Ti_kills_z_offdiag = abs(Ti_out[0,1]) < 1e-10
    results["Ti_kills_Z_basis_offdiag"] = bool(Ti_kills_z_offdiag)
    print(f"    Ti |ρ₀₁| after full dephasing: {abs(Ti_out[0,1]):.2e}"
          f"  {'✓' if Ti_kills_z_offdiag else '✗'} (should → 0)")
    if not Ti_kills_z_offdiag:
        basis_ok = False

    # Te kills off-diagonals in X-basis: the X-basis coherences go to zero
    # In X-basis: |+⟩=(|0⟩+|1⟩)/√2, |−⟩=(|0⟩-|1⟩)/√2
    # State coherent in X-basis: ρ = ½(I + r_z σ_z) has off-diags in X-basis
    rho_x = 0.5 * (I2 + 0.8 * SIGMA_Z)  # z-polarized = coherent in x-basis
    Te_out = Te_locked(rho_x, q2=1.0)  # full σ_x dephasing
    # After full Te: diagonal in X-basis → in Z-basis becomes ½I
    Te_pushes_to_halfI = abs(Te_out[0,0] - 0.5) < 1e-10 and abs(Te_out[1,1] - 0.5) < 1e-10
    results["Te_kills_X_basis_coherence"] = bool(Te_pushes_to_halfI)
    print(f"    Te ρ₀₀ after full σ_x dephasing: {np.real(Te_out[0,0]):.4f}"
          f"  {'✓' if Te_pushes_to_halfI else '✗'} (should → 0.5)")
    if not Te_pushes_to_halfI:
        basis_ok = False

    results["basis_specificity"] = bool(basis_ok)
    all_pass = all_pass and basis_ok

    # ── Test 6: T and F are non-commuting ─────────────────────────
    print("\n  [T6] T and F operators are non-commuting...")
    noncomm_ok = False

    q = random_s3_point(rng)
    rho = 0.7 * coherent_state_density(q) + 0.3 * I2 / 2

    TiFi = Fi_locked(Ti_locked(rho))
    FiTi = Ti_locked(Fi_locked(rho))
    d_TiFi = trace_distance(TiFi, FiTi)

    TeFe = Fe_locked(Te_locked(rho))
    FeTe = Te_locked(Fe_locked(rho))
    d_TeFe = trace_distance(TeFe, FeTe)

    print(f"    D(Ti∘Fi, Fi∘Ti) = {d_TiFi:.4f}")
    print(f"    D(Te∘Fe, Fe∘Te) = {d_TeFe:.4f}")
    noncomm_ok = d_TiFi > 1e-6 or d_TeFe > 1e-6
    results["T_F_noncommuting"] = bool(noncomm_ok)
    results["d_TiFi"] = float(d_TiFi)
    results["d_TeFe"] = float(d_TeFe)
    print(f"    {'✓' if noncomm_ok else '✗'} T and F operators do not commute")
    all_pass = all_pass and noncomm_ok

    # ── Test 7: Runtime discrepancy notice ────────────────────────
    print("\n  [T7] Runtime discrepancy check (informational)...")
    try:
        from geometric_operators import apply_Te as runtime_Te, apply_Fe as runtime_Fe

        q = random_s3_point(rng)
        rho = 0.7 * coherent_state_density(q) + 0.3 * I2 / 2

        # Locked Te should reduce off-diagonals (dephasing)
        locked_Te_out = Te_locked(rho)
        runtime_Te_out = runtime_Te(rho)

        locked_Te_reduces = off_diagonal_magnitude(locked_Te_out) < off_diagonal_magnitude(rho)
        runtime_Te_preserves = abs(
            np.linalg.norm(sorted(np.real(np.linalg.eigvalsh(runtime_Te_out)))) -
            np.linalg.norm(sorted(np.real(np.linalg.eigvalsh(rho))))
        ) < 1e-6

        discrepancy_detected = locked_Te_reduces and runtime_Te_preserves
        results["runtime_discrepancy_detected"] = bool(discrepancy_detected)
        results["locked_Te_is_dephasing"] = bool(locked_Te_reduces)
        results["runtime_Te_is_unitary"] = bool(runtime_Te_preserves)
        print(f"    Locked Te is dephasing (reduces off-diag): {locked_Te_reduces}")
        print(f"    Runtime Te is unitary (preserves eigenvalues): {runtime_Te_preserves}")
        if discrepancy_detected:
            print("    ⚠ DISCREPANCY CONFIRMED: runtime Te ≠ locked Te")
        else:
            print("    Runtime and locked agree on Te behavior")
    except ImportError:
        results["runtime_discrepancy_check"] = "geometric_operators not available"
        print("    (geometric_operators.py not importable in this context)")

    # ── Verdict ───────────────────────────────────────────────────
    print(f"\n{'=' * 72}")
    print(f"  AXIS 5 VERDICT: {'PASS ✓' if all_pass else 'KILL ✗'}")
    print(f"{'=' * 72}")

    token_name = "E_AX5_TF_KERNEL_VALID" if all_pass else ""
    verdict = "PASS" if all_pass else "KILL"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "Ax5_TF_kernel_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "axis": 5,
            "name": "Ax5_T_vs_F_Kernel_Validation",
            "definition": "T={Ti,Te}=dephasing, F={Fi,Fe}=unitary-rotation",
            "source": "AXIS_3_4_5_6_QIT_MATH.md + v5_OPERATOR_MATH_LEDGER.md",
            "warning": (
                "geometric_operators.py DIVERGES from locked spec: "
                "runtime Fe=amplitude-damping (should be U_z rotation), "
                "runtime Te=sigma_y rotation (should be sigma_x dephasing)"
            ),
            "verdict": verdict,
            "evidence_token": token_name,
            "results": results,
        }, f, indent=2, default=str)
    print(f"  Results saved: {outpath}")
    return all_pass


if __name__ == "__main__":
    run_Ax5_validation()
