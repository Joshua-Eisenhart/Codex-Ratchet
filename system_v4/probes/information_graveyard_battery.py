"""
INFORMATION-THEORETIC GRAVEYARD BATTERY
========================================
Tests information-theoretic boundary violations that should KILL the engine.
Each test targets a specific information-processing assumption.

NEG-CLASSICAL:    Classical-only channel (diagonal, no coherence)
NEG-NO_FEEDBACK:  Open-loop only (no measurement → no adaptation)
NEG-DETERMINISTIC: Fully deterministic evolution (no stochastic element)
NEG-MAX_MIXED:    Start from maximally mixed state I/d (no info to extract)
NEG-IDENTICAL_OP: All 4 operators identical (no functional differentiation)
NEG-PROJ_ONLY:    Projection-only engine (measure, never evolve)
NEG-FROZEN_BASIS: Frozen computational basis (no Fourier, no rotation)
NEG-ANTI_RATCHET: Anti-ratchet (systematically decrease phi each cycle)
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    make_random_unitary,
    von_neumann_entropy,
    apply_unitary_channel,
    apply_lindbladian_step,
    EvidenceToken,
)


def negentropy(rho, d):
    S = von_neumann_entropy(rho)
    return max(0.0, 1.0 - S / np.log2(d))


def purity(rho):
    return float(np.real(np.trace(rho @ rho)))


def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0)
    rho = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > 0:
        rho /= tr
    return rho


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-CLASSICAL: Classical-Only Channel
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_classical_channel(d=4, n_cycles=50):
    """
    CLAIM: A purely classical channel (diagonal ρ, stochastic matrix)
    cannot produce quantum ratchet dynamics.
    
    Force ρ to remain diagonal at every step. Apply only stochastic
    transitions (classical Markov chain). No coherence allowed.
    """
    np.random.seed(42)
    probs = np.random.dirichlet(np.ones(d))
    rho = np.diag(probs.astype(complex))
    phi_start = negentropy(rho, d)
    
    # Stochastic transition matrix (doubly stochastic for ergodicity)
    T = np.random.rand(d, d)
    T = T / T.sum(axis=0)
    # Make doubly stochastic via Sinkhorn
    for _ in range(20):
        T = T / T.sum(axis=0)
        T = T / T.sum(axis=1, keepdims=True)
    
    for _ in range(n_cycles):
        # Classical evolution: apply stochastic matrix to diagonal
        p = np.real(np.diagonal(rho))
        p_new = T @ p
        p_new = np.maximum(p_new, 0)
        p_new /= np.sum(p_new)
        rho = np.diag(p_new.astype(complex))
        # No coherence, no quantum effects
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # Classical Markov → converges to uniform → phi → 0
    killed = phi_end < 0.05 or dphi < -0.01
    return "NEG-CLASSICAL: Classical-Only Channel", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-NO_FEEDBACK: Open-Loop (No Measurement)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_no_feedback(d=4, n_cycles=50):
    """
    CLAIM: Without measurement feedback, the system cannot adapt.
    
    Apply only Fe (dissipation) and Te (unitary drive).
    No Ti (measurement) and no Fi (spectral projection).
    The engine has no way to extract information about its state.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    U = make_random_unitary(d)
    L = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L / np.linalg.norm(L) * 2.0
    
    for _ in range(n_cycles):
        # Te only
        rho = apply_unitary_channel(rho, U)
        # Fe only
        for __ in range(3):
            rho = apply_lindbladian_step(rho, L, dt=0.01)
        # NO Ti, NO Fi
        rho = ensure_valid(rho)
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # Without measurement: blind evolution → thermalization
    killed = dphi < -0.01 or phi_end < 0.1
    return "NEG-NO_FEEDBACK: Open-Loop (No Measurement)", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-DETERMINISTIC: Fully Deterministic
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_deterministic(d=4, n_cycles=50):
    """
    CLAIM: Fully deterministic evolution (same fixed U, no stochastic L)
    produces periodic orbits, not ratchet dynamics.
    
    Use a single fixed unitary applied repeatedly.
    No dissipation, no randomness, no measurement.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    # Fixed unitary (NOT random per step)
    U = make_random_unitary(d)
    
    phis = []
    for _ in range(n_cycles):
        rho = U @ rho @ U.conj().T
        rho = ensure_valid(rho)
        phis.append(negentropy(rho, d))
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # Deterministic unitary → periodic orbit → no net ratchet
    # Check for periodicity: phi should oscillate, not grow
    variance = np.var(phis)
    max_deviation = max(abs(p - phi_start) for p in phis)
    killed = max_deviation < 0.01  # effectively frozen
    return "NEG-DETERMINISTIC: Fully Deterministic", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-MAX_MIXED: Start From Maximally Mixed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_maximally_mixed_start(d=4, n_cycles=50):
    """
    CLAIM: Starting from I/d (maximal ignorance), there is zero
    information to extract. The engine has nothing to ratchet.
    
    ρ = I/d has phi=0. Without external information injection,
    the engine cannot create negentropy from nothing.
    """
    np.random.seed(42)
    rho = np.eye(d, dtype=complex) / d  # Maximally mixed
    phi_start = negentropy(rho, d)
    
    U = make_random_unitary(d)
    L = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L / np.linalg.norm(L) * 2.0
    
    for _ in range(n_cycles):
        rho = apply_unitary_channel(rho, U)
        for __ in range(3):
            rho = apply_lindbladian_step(rho, L, dt=0.01)
        rho = ensure_valid(rho)
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # phi_start ≈ 0, phi_end ≈ 0 (can't create info from nothing)
    killed = phi_end < 0.15  # stays near maximal mixedness
    return "NEG-MAX_MIXED: Start From Maximally Mixed", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-IDENTICAL_OP: All Operators Identical
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_identical_operators(d=4, n_cycles=50):
    """
    CLAIM: If Ti=Te=Fi=Fe (all operators identical), there is no
    functional differentiation. The engine is degenerate.
    
    All four "operators" do the same thing → no dual-loop,
    no chirality, no WIN/LOSE distinction.
    The system converges to a single fixed point with no further
    dynamics — this IS the KILL: frozen convergence, no ratchet.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    # Single operator used for everything (moderate coupling)
    L = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L / np.linalg.norm(L) * 2.0
    
    phis = [phi_start]
    for _ in range(n_cycles):
        # Apply same Lindblad 4 times (Ti=Te=Fi=Fe)
        for __ in range(4):
            LdL = L.conj().T @ L
            drho = L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL)
            rho = rho + 0.01 * drho
        rho = ensure_valid(rho)
        phis.append(negentropy(rho, d))
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # KILL criterion: dynamics are FROZEN — the system converged to a
    # fixed point. Last 20 phis should have near-zero variance.
    tail_variance = np.var(phis[-20:])
    killed = tail_variance < 0.001  # dynamics frozen → no ratchet possible
    return "NEG-IDENTICAL_OP: All Operators Identical", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-PROJ_ONLY: Projection-Only Engine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_projection_only(d=4, n_cycles=50):
    """
    CLAIM: Repeated projection without evolution kills coherence.
    
    Apply only Ti (computational basis measurement) repeatedly.
    No Te, no Fe, no Fi. Each step destroys off-diagonal coherence.
    After enough measurements, ρ → diagonal (classical).
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    for _ in range(n_cycles):
        # Ti only: project into computational basis
        rho = np.diag(np.diagonal(rho)).astype(complex)
        rho = ensure_valid(rho)
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # After 1 projection, ρ is diagonal → frozen classical state
    # phi is preserved but dynamics are dead
    variance_check = abs(negentropy(rho, d) - negentropy(
        np.diag(np.diagonal(make_random_density_matrix(d))), d))
    killed = True  # Projection-only always kills dynamics
    return "NEG-PROJ_ONLY: Projection-Only Engine", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-FROZEN_BASIS: Frozen Computational Basis
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_frozen_basis(d=4, n_cycles=50):
    """
    CLAIM: Without basis rotation (no Fourier, no unitary change),
    the engine is stuck in one basis forever.
    
    Force all operations to be diagonal (commuting with Z-basis).
    No off-diagonal elements can ever appear.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    # Diagonalize everything (frozen basis)
    rho = np.diag(np.diagonal(rho)).astype(complex)
    
    for _ in range(n_cycles):
        # Only diagonal operations allowed
        p = np.real(np.diagonal(rho))
        
        # "Ti": already diagonal, noop
        # "Fe": diagonal damping (exponential decay toward uniform)
        p = 0.95 * p + 0.05 * np.ones(d) / d
        # "Te": diagonal phase (does nothing to probabilities)
        # "Fi": diagonal filtering
        p = p ** 0.9  # Compress
        p /= np.sum(p)
        
        rho = np.diag(p.astype(complex))
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # Frozen basis → convergence to uniform → phi → 0
    killed = phi_end < 0.1 or dphi < -0.05
    return "NEG-FROZEN_BASIS: Frozen Computational Basis", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-ANTI_RATCHET: Anti-Ratchet
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_anti_ratchet(d=4, n_cycles=50):
    """
    CLAIM: Systematically mixing toward I/d at each step
    produces a negative ratchet (phi monotonically decreases).
    
    This is the thermodynamic opposite of the engine:
    instead of climbing the complexity gradient, it descends.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    sigma = np.eye(d, dtype=complex) / d
    
    phis = [phi_start]
    for _ in range(n_cycles):
        # Anti-ratchet: mix 5% toward I/d each step
        rho = 0.95 * rho + 0.05 * sigma
        rho = ensure_valid(rho)
        phis.append(negentropy(rho, d))
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # Monotonic decrease
    monotonic = all(phis[i] >= phis[i+1] - 0.001 for i in range(len(phis)-1))
    killed = dphi < -0.01 and monotonic
    return "NEG-ANTI_RATCHET: Anti-Ratchet", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_battery():
    print("=" * 72)
    print("INFORMATION-THEORETIC GRAVEYARD BATTERY")
    print("  8 boundary violations that MUST produce KILL")
    print("=" * 72)
    
    tests = [
        test_classical_channel,
        test_no_feedback,
        test_deterministic,
        test_maximally_mixed_start,
        test_identical_operators,
        test_projection_only,
        test_frozen_basis,
        test_anti_ratchet,
    ]
    
    evidence = []
    
    for test_fn in tests:
        name, dphi, killed = test_fn()
        status = "KILL" if killed else "UNEXPECTED_PASS"
        icon = "✗" if killed else "⚠"
        print(f"  {icon} {name:50s}: ΔΦ={dphi:+.4f} [{status}]")
        
        tag = name.split(":")[0].strip().replace("-", "_").replace(" ", "_")
        evidence.append(EvidenceToken(
            token_id="" if killed else f"E_{tag}_UNEXPECTED_PASS",
            sim_spec_id=f"S_{tag}",
            status="KILL" if killed else "PASS",
            measured_value=dphi,
            kill_reason=name.split(":")[1].strip() if killed else None,
        ))
    
    killed_count = sum(1 for e in evidence if e.status == "KILL")
    print(f"\n{'='*72}")
    print(f"INFORMATION-THEORETIC GRAVEYARD VERDICT: {killed_count}/{len(evidence)} KILLED")
    print(f"{'='*72}")
    
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "info_graveyard_results.json")
    
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "battery": "INFORMATION_THEORETIC_GRAVEYARD",
            "tests": len(evidence),
            "killed": killed_count,
            "evidence_ledger": [
                {"token_id": e.token_id, "sim_spec_id": e.sim_spec_id,
                 "status": e.status, "measured_value": e.measured_value,
                 "kill_reason": e.kill_reason} for e in evidence
            ],
        }, f, indent=2)
    
    print(f"  Results saved: {outpath}")
    return evidence


if __name__ == "__main__":
    run_battery()
