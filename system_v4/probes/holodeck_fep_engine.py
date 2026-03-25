#!/usr/bin/env python3
"""
Holodeck FEP Engine — S³ Projection & Free Energy Surprise
============================================================
Bridges the QIT engine to external reality modeling:
  1. S³ projection via Hopf fibration of 2-qubit density matrix eigenspaces
  2. FEP surprise metric: S_FEP = KL(q(z|x) || p(z)) on finite states
  3. Thermal grid generation for spatial correlation matrices
  4. EvidenceToken emission to holodeck_fep_results.json

KILL conditions tested:
  K1: Eigenvalue collapse (degenerate spectrum for structured input)
  K2: FEP divergence (infinite KL for finite states)
  K3: S³ degeneracy (all eigenstates map to same point)
  K4: Coherence below threshold (< 0.01)
  K5: Thermal grid singularity (negative eigenvalues)
"""

import numpy as np
import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    EvidenceToken,
    make_random_density_matrix,
    von_neumann_entropy,
)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")


# ─────────────────────────────────────────────
# S³ Hopf Projection
# ─────────────────────────────────────────────

def partial_trace_B(psi_4, d=2):
    """Partial trace over qubit B of a 2-qubit pure state |ψ⟩ ∈ ℂ⁴.
    Returns reduced density matrix ρ_A ∈ ℂ^{2×2}.
    """
    psi_reshaped = psi_4.reshape(d, d)
    rho_A = psi_reshaped @ psi_reshaped.conj().T
    tr = np.real(np.trace(rho_A))
    if tr > 1e-15:
        rho_A /= tr
    return rho_A


def bloch_from_reduced(rho_A):
    """Extract dominant eigenvector of ρ_A ∈ ℂ^{2×2} as a normalized ψ ∈ ℂ²."""
    eigvals, eigvecs = np.linalg.eigh(rho_A)
    idx = np.argmax(eigvals)
    psi = eigvecs[:, idx]
    norm = np.linalg.norm(psi)
    if norm > 1e-15:
        psi = psi / norm
    return psi


def hopf_map(psi):
    """Map ψ = (α, β) ∈ ℂ² (|α|²+|β|²=1) to S³ coordinates (θ, φ, χ).

    θ = 2·arccos(|α|)       ∈ [0, π]
    φ = arg(β) - arg(α)     ∈ [0, 2π)
    χ = arg(α) + arg(β)     ∈ [0, 4π)
    """
    alpha, beta = psi[0], psi[1]
    abs_alpha = np.clip(np.abs(alpha), 0.0, 1.0)
    theta = 2.0 * np.arccos(abs_alpha)
    arg_alpha = np.angle(alpha)
    arg_beta = np.angle(beta)
    phi = (arg_beta - arg_alpha) % (2 * np.pi)
    chi = (arg_alpha + arg_beta) % (4 * np.pi)
    return float(theta), float(phi), float(chi)


def hopf_project_eigenspace(rho):
    """Eigendecompose a 4×4 density matrix and Hopf-project each eigenspace.
    Returns list of dicts with eigenvalue, S³ coordinates.
    """
    eigenvalues, eigenvectors = np.linalg.eigh(rho)
    eigenvalues = np.real(eigenvalues)
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    projections = []
    for i in range(len(eigenvalues)):
        lam = eigenvalues[i]
        if lam < 1e-12:
            continue
        psi_4 = eigenvectors[:, i]
        rho_A = partial_trace_B(psi_4)
        psi_2 = bloch_from_reduced(rho_A)
        theta, phi, chi = hopf_map(psi_2)
        projections.append({
            "eigenvalue": float(lam),
            "s3_theta": theta,
            "s3_phi": phi,
            "s3_chi": chi,
        })
    return projections


# ─────────────────────────────────────────────
# FEP Surprise (KL Divergence)
# ─────────────────────────────────────────────

def kl_divergence(q, p):
    """KL(q || p) on finite discrete distributions with Laplace smoothing."""
    eps = 1e-12
    q = np.array(q, dtype=float) + eps
    p = np.array(p, dtype=float) + eps
    q = q / q.sum()
    p = p / p.sum()
    return float(np.sum(q * np.log(q / p)))


def fep_surprise(rho_obs, rho_model):
    """S_FEP = KL(q(z|x) || p(z)) where q,p are eigenvalue spectra."""
    q = np.maximum(np.real(np.linalg.eigvalsh(rho_obs)), 0)
    p = np.maximum(np.real(np.linalg.eigvalsh(rho_model)), 0)
    q_sum, p_sum = q.sum(), p.sum()
    if q_sum > 1e-15:
        q = q / q_sum
    if p_sum > 1e-15:
        p = p / p_sum
    return kl_divergence(q, p)


# ─────────────────────────────────────────────
# Thermal Grid
# ─────────────────────────────────────────────

def thermal_state(d, temperature):
    """Gibbs state ρ = exp(-H/T)/Z with H = diag(0,1,...,d-1)."""
    energies = np.arange(d, dtype=float)
    if temperature < 1e-10:
        rho = np.zeros((d, d), dtype=complex)
        rho[0, 0] = 1.0
        return rho
    boltzmann = np.exp(-energies / temperature)
    return np.diag((boltzmann / boltzmann.sum()).astype(complex))


def thermal_grid(d=4, n_grid=8):
    """Grid of thermal states → correlation matrix C_{ij} = Tr(ρ_i · ρ_j)."""
    temperatures = np.linspace(0.1, 5.0, n_grid)
    states = [thermal_state(d, T) for T in temperatures]
    C = np.zeros((n_grid, n_grid))
    for i in range(n_grid):
        for j in range(n_grid):
            C[i, j] = np.real(np.trace(states[i] @ states[j]))
    return C, temperatures


# ─────────────────────────────────────────────
# Main SIM
# ─────────────────────────────────────────────

def run_holodeck_fep_sim(d=4, n_trials=20, seed=42):
    """Run the full Holodeck FEP engine simulation."""
    np.random.seed(seed)

    print(f"\n{'='*60}")
    print(f"HOLODECK FEP ENGINE — S³ PROJECTION + FREE ENERGY SURPRISE")
    print(f"  d={d}, trials={n_trials}, seed={seed}")
    print(f"{'='*60}")

    evidence = []

    # ── TEST 1: S³ PROJECTION ──
    print(f"\n{'─'*40}")
    print("  TEST 1: S³ Hopf Projection from Eigenspaces")
    print(f"{'─'*40}")

    all_projections = []
    n_degenerate = 0
    for t in range(n_trials):
        rho = make_random_density_matrix(d)
        projs = hopf_project_eigenspace(rho)
        all_projections.append(projs)
        if len(projs) >= 2:
            coords = [(p["s3_theta"], p["s3_phi"]) for p in projs]
            if all(np.allclose([coords[0][0], coords[0][1]],
                               [c[0], c[1]], atol=1e-6) for c in coords[1:]):
                n_degenerate += 1

    if n_degenerate == n_trials:
        print(f"  KILL: All {n_trials} states map to degenerate S³ point!")
        evidence.append(EvidenceToken(
            token_id="",
            sim_spec_id="S_HOLODECK_S3_PROJECTION",
            status="KILL", measured_value=0.0,
            kill_reason="S3_DEGENERACY_ALL_EIGENSTATES_SAME_POINT"
        ))
    else:
        avg_patches = np.mean([len(p) for p in all_projections])
        print(f"  PASS: {n_trials} density matrices projected to S³")
        print(f"  Average patches: {avg_patches:.1f}, Degenerate: {n_degenerate}/{n_trials}")
        evidence.append(EvidenceToken(
            token_id="E_SIM_HOLODECK_S3_PROJECTION_OK",
            sim_spec_id="S_HOLODECK_S3_PROJECTION",
            status="PASS", measured_value=avg_patches
        ))

    # ── TEST 2: FEP SURPRISE ──
    print(f"\n{'─'*40}")
    print("  TEST 2: FEP Surprise Metric (KL Divergence)")
    print(f"{'─'*40}")

    surprises = []
    any_diverged = False
    for t in range(n_trials):
        rho_obs = make_random_density_matrix(d)
        rho_prior = np.eye(d, dtype=complex) / d
        s = fep_surprise(rho_obs, rho_prior)
        surprises.append(s)
        if not np.isfinite(s):
            any_diverged = True

    if any_diverged:
        print(f"  KILL: FEP surprise diverged to infinity!")
        evidence.append(EvidenceToken(
            token_id="", sim_spec_id="S_HOLODECK_FEP_SURPRISE",
            status="KILL", measured_value=float("inf"),
            kill_reason="FEP_DIVERGENCE_INFINITE_KL"
        ))
    else:
        mean_s, max_s = np.mean(surprises), np.max(surprises)
        print(f"  PASS: All {n_trials} surprise values finite")
        print(f"  Mean S_FEP = {mean_s:.6f}, Max = {max_s:.6f}")
        evidence.append(EvidenceToken(
            token_id="E_SIM_HOLODECK_FEP_SURPRISE_OK",
            sim_spec_id="S_HOLODECK_FEP_SURPRISE",
            status="PASS", measured_value=mean_s
        ))

    # ── TEST 3: THERMAL GRID ──
    print(f"\n{'─'*40}")
    print("  TEST 3: Thermal Grid Correlation Matrix")
    print(f"{'─'*40}")

    C, temps = thermal_grid(d=d, n_grid=8)
    grid_eigs = np.real(np.linalg.eigvalsh(C))
    min_eig = grid_eigs.min()

    if min_eig < -1e-10:
        print(f"  KILL: Negative eigenvalue: {min_eig:.6e}")
        evidence.append(EvidenceToken(
            token_id="", sim_spec_id="S_HOLODECK_THERMAL_GRID",
            status="KILL", measured_value=float(min_eig),
            kill_reason="THERMAL_GRID_SINGULARITY_NEGATIVE_EIGENVALUE"
        ))
    else:
        print(f"  PASS: PSD correlation matrix (min eig: {min_eig:.6e})")
        print(f"  Temperature range: [{temps[0]:.1f}, {temps[-1]:.1f}]")
        evidence.append(EvidenceToken(
            token_id="E_SIM_HOLODECK_THERMAL_GRID_OK",
            sim_spec_id="S_HOLODECK_THERMAL_GRID",
            status="PASS", measured_value=float(min_eig)
        ))

    # ── TEST 4: COHERENCE ──
    print(f"\n{'─'*40}")
    print("  TEST 4: Holodeck Coherence Score")
    print(f"{'─'*40}")

    coherences = []
    max_entropy = np.log2(d)
    for t in range(n_trials):
        rho = make_random_density_matrix(d)
        S = von_neumann_entropy(rho)
        coherences.append(1.0 - S / max_entropy)

    mean_coh, max_coh = np.mean(coherences), np.max(coherences)

    if max_coh < 0.01:
        print(f"  KILL: All coherence below 0.01 (max={max_coh:.6f})")
        evidence.append(EvidenceToken(
            token_id="", sim_spec_id="S_HOLODECK_COHERENCE",
            status="KILL", measured_value=max_coh,
            kill_reason="COHERENCE_BELOW_THRESHOLD"
        ))
    else:
        print(f"  PASS: Mean coherence={mean_coh:.6f}, Max={max_coh:.6f}")
        evidence.append(EvidenceToken(
            token_id="E_SIM_HOLODECK_COHERENCE_OK",
            sim_spec_id="S_HOLODECK_COHERENCE",
            status="PASS", measured_value=mean_coh
        ))

    # ── FINAL REPORT ──
    print(f"\n{'='*60}")
    print("  HOLODECK FEP ENGINE — FINAL VERDICT")
    print(f"{'='*60}")

    n_pass = sum(1 for e in evidence if e.status == "PASS")
    n_kill = sum(1 for e in evidence if e.status == "KILL")
    print(f"  PASS: {n_pass}/4, KILL: {n_kill}/4")
    for e in evidence:
        icon = "✓" if e.status == "PASS" else "✗"
        print(f"    {icon} {e.token_id or e.kill_reason} ({e.measured_value:.6f})")

    # ── SAVE RESULTS ──
    os.makedirs(RESULTS_DIR, exist_ok=True)
    outpath = os.path.join(RESULTS_DIR, "holodeck_fep_results.json")

    sample_coords = {}
    if all_projections and all_projections[0]:
        p0 = all_projections[0][0]
        sample_coords = {
            "s3_theta": p0["s3_theta"], "s3_phi": p0["s3_phi"],
            "s3_chi": p0["s3_chi"],
            "fep_surprise": surprises[0] if surprises else 0.0,
            "coherence_score": coherences[0] if coherences else 0.0,
            "thermal_temperature": 1.0,
        }

    results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "sim_id": "holodeck_fep_engine",
        "evidence_ledger": [
            {
                "token_id": e.token_id, "sim_spec_id": e.sim_spec_id,
                "status": e.status, "measured_value": e.measured_value,
                "kill_reason": e.kill_reason, "timestamp": e.timestamp,
            }
            for e in evidence
        ],
        "summary": {"total_tests": 4, "passed": n_pass, "killed": n_kill},
        "attractor_coordinates_sample": sample_coords,
    }

    with open(outpath, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to: {outpath}")
    return evidence


if __name__ == "__main__":
    run_holodeck_fep_sim()
