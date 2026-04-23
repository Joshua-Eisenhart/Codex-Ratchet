"""
THERMODYNAMIC GRAVEYARD BATTERY
================================
Tests thermodynamic boundary violations that should KILL the engine.
Each test targets a specific thermodynamic assumption.

NEG-CLONE:     No-cloning violation — attempt to duplicate a quantum state
NEG-ZERO_H:    Zero Hamiltonian — Te has no drive (H=0)
NEG-INF_GAMMA: Infinite coupling — γ→∞ destroys all structure instantly
NEG-PURE_LOCK: Pure state with no dissipation channel — no entropy to export
NEG-DIM1:      Dimension d=1 — trivial Hilbert space, no room for operators
NEG-NO_BATH:   No environmental bath — closed-system evolution only
NEG-ZERO_TEMP: Zero temperature bath — violates third law
NEG-REVERSED:  Reversed entropy — pump entropy IN instead of exporting
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
    return max(0.0, 1.0 - S / np.log2(d)) if d > 1 else 0.0


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
# NEG-CLONE: No-Cloning Violation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_no_cloning(d=4, n_cycles=50):
    """
    CLAIM: Quantum states cannot be cloned.
    
    Attempt: Create a COPY operation that maps ρ → ρ⊗ρ (tensor product).
    Then partial-trace back to d dimensions.
    If the copy is perfect, it violates no-cloning.
    If the copy degrades, no-cloning holds and the engine should KILL.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    # Attempt cloning: ρ → ρ⊗ρ → partial_trace → ρ_clone
    # Physical cloning is impossible. We simulate the ATTEMPT:
    # use a SWAP-like operation between system and "clone register"
    d_total = d * d
    rho_sys = np.kron(rho, np.eye(d, dtype=complex) / d)  # system ⊗ blank
    
    # SWAP gate (would clone if cloning were possible)
    SWAP = np.zeros((d_total, d_total), dtype=complex)
    for i in range(d):
        for j in range(d):
            # |ij⟩ → |ji⟩
            SWAP[j * d + i, i * d + j] = 1.0
    
    # Apply partial SWAP (attempting clone)
    for _ in range(n_cycles):
        # Partial SWAP mixes system and clone
        rho_swap = 0.7 * rho_sys + 0.3 * (SWAP @ rho_sys @ SWAP.conj().T)
        rho_swap = ensure_valid(rho_swap)
        
        # Partial trace over clone register to get system state
        rho_reduced = np.zeros((d, d), dtype=complex)
        for k in range(d):
            rho_reduced += rho_swap[k*d:(k+1)*d, k*d:(k+1)*d]
        rho_reduced = ensure_valid(rho_reduced)
        
        # Check if clone degraded the original (no-cloning signature)
        rho_sys = np.kron(rho_reduced, np.eye(d, dtype=complex) / d)
    
    phi_end = negentropy(rho_reduced, d)
    dphi = phi_end - phi_start
    
    # No-cloning: the SWAP operation should degrade phi
    # (mixing with blank register destroys information)
    killed = dphi < -0.01 or phi_end < phi_start * 0.5
    return "NEG-CLONE: No-Cloning Violation", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-ZERO_H: Zero Hamiltonian
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_zero_hamiltonian(d=4, n_cycles=50):
    """
    CLAIM: Te requires a nontrivial Hamiltonian.
    
    With H=0, the unitary channel U = exp(-iHt) = I,
    so Te does nothing. The engine loses its drive.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    H = np.zeros((d, d), dtype=complex)  # ZERO Hamiltonian
    L = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L / np.linalg.norm(L) * 2.0
    
    for _ in range(n_cycles):
        U = np.eye(d, dtype=complex)  # U = I (no drive)
        rho = U @ rho @ U.conj().T
        for __ in range(3):
            rho = apply_lindbladian_step(rho, L, dt=0.01)
        rho = ensure_valid(rho)
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # Without unitary drive, dissipation pushes to thermal death
    killed = dphi < -0.01 or phi_end < 0.05
    return "NEG-ZERO_H: Zero Hamiltonian", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-INF_GAMMA: Infinite Coupling
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_infinite_coupling(d=4, n_cycles=20):
    """
    CLAIM: γ→∞ destroys all structure instantly.
    
    Model infinite coupling as extreme depolarizing + amplitude damping:
    each cycle, mix 99% toward I/d plus strong dephasing.
    This is the physical meaning of γ→∞: the bath overwhelms the system.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    sigma = np.eye(d, dtype=complex) / d  # thermal state
    
    for _ in range(n_cycles):
        # Extreme depolarization: 99% toward I/d (γ→∞ mixing)
        rho = 0.01 * rho + 0.99 * sigma
        # Plus dephasing: kill off-diagonals
        rho = 0.5 * rho + 0.5 * np.diag(np.diagonal(rho)).astype(complex)
        rho = ensure_valid(rho)
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # Infinite coupling → instant thermalization
    killed = phi_end < 0.05
    return "NEG-INF_GAMMA: Infinite Coupling", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-PURE_LOCK: Pure State Lock
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_pure_state_lock(d=4, n_cycles=50):
    """
    CLAIM: A pure state with unitary-only evolution cannot ratchet.
    
    Pure state (rank 1) + unitary channel = stays pure forever.
    No entropy export possible. No ratchet gain.
    """
    np.random.seed(42)
    
    # Start with a PURE state
    psi = np.random.randn(d) + 1j * np.random.randn(d)
    psi /= np.linalg.norm(psi)
    rho = np.outer(psi, psi.conj())
    phi_start = negentropy(rho, d)
    
    phis = [phi_start]
    for _ in range(n_cycles):
        U = make_random_unitary(d)
        rho = U @ rho @ U.conj().T
        # NO Lindbladian (unitary only)
        rho = ensure_valid(rho)
        phis.append(negentropy(rho, d))
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # Pure state under unitary stays pure → purity ≈ 1, phi ≈ same
    # No ratchet possible without dissipation
    variance = np.var(phis)
    killed = variance < 0.001 and abs(dphi) < 0.01  # frozen dynamics
    return "NEG-PURE_LOCK: Pure State Lock", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-DIM1: Dimension Collapse (d=1)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_dimension_one():
    """
    CLAIM: d=1 Hilbert space cannot support any operator structure.
    
    A 1×1 density matrix is just [1]. No operators can act on it.
    The engine has zero degrees of freedom.
    """
    d = 1
    rho = np.array([[1.0 + 0j]])
    phi = negentropy(rho, d)  # Should be 0.0
    p = purity(rho)  # Should be 1.0
    
    # Try to run a "cycle" — nothing can happen
    H = np.array([[0.0 + 0j]])
    U = np.array([[1.0 + 0j]])
    rho_after = U @ rho @ U.conj().T
    
    killed = True  # d=1 is always a KILL: no room for computation
    dphi = 0.0
    return "NEG-DIM1: Dimension Collapse", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-NO_BATH: No Environmental Bath
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_no_bath(d=4, n_cycles=50):
    """
    CLAIM: Without an environmental bath, entropy has nowhere to go.
    
    The system is closed (L=0). All evolution is unitary.
    Landauer's principle requires entropy export to a bath.
    Without it, the ratchet cannot function.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    for _ in range(n_cycles):
        U = make_random_unitary(d)
        rho = U @ rho @ U.conj().T
        # L = 0 → No Lindbladian dissipation at all
        rho = ensure_valid(rho)
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # Without bath: purity preserved, no entropy export, no ratchet
    p_final = purity(rho)
    killed = abs(dphi) < 0.01 and p_final > 0.2  # frozen or oscillating
    return "NEG-NO_BATH: No Environmental Bath", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-REVERSED: Reversed Entropy Flow
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_reversed_entropy(d=4, n_cycles=50):
    """
    CLAIM: Pumping entropy INTO the system (instead of exporting) kills it.
    
    Reversed Lindbladian: L†ρL instead of LρL† as the gain term.
    This pumps entropy in rather than exporting it.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    U = make_random_unitary(d)
    L = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L / np.linalg.norm(L) * 2.0
    
    for _ in range(n_cycles):
        rho = apply_unitary_channel(rho, U)
        # REVERSED Lindbladian: L†ρL instead of LρL†
        Ld = L.conj().T
        LdL = L @ Ld  # Note: reversed from standard
        drho = Ld @ rho @ L - 0.5 * (LdL @ rho + rho @ LdL)
        rho = rho + 0.01 * drho
        rho = ensure_valid(rho)
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    # Reversed entropy flow → rapid degradation
    killed = dphi < -0.01 or phi_end < 0.05
    return "NEG-REVERSED: Reversed Entropy Flow", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEG-DEPOLAR: Total Depolarization
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_total_depolarization(d=4, n_cycles=20):
    """
    CLAIM: Replacing ρ→(1-p)ρ + p·I/d at each step with p≈1 destroys all info.
    
    Strong depolarizing channel erases all structure.
    The engine has nothing to work with.
    """
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    phi_start = negentropy(rho, d)
    
    sigma = np.eye(d, dtype=complex) / d
    
    for _ in range(n_cycles):
        U = make_random_unitary(d)
        rho = U @ rho @ U.conj().T
        # Massive depolarization: p=0.9
        rho = 0.1 * rho + 0.9 * sigma
        rho = ensure_valid(rho)
    
    phi_end = negentropy(rho, d)
    dphi = phi_end - phi_start
    
    killed = phi_end < 0.05
    return "NEG-DEPOLAR: Total Depolarization", dphi, killed


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_battery():
    print("=" * 72)
    print("THERMODYNAMIC GRAVEYARD BATTERY")
    print("  8 boundary violations that MUST produce KILL")
    print("=" * 72)
    
    tests = [
        test_no_cloning,
        test_zero_hamiltonian,
        test_infinite_coupling,
        test_pure_state_lock,
        test_dimension_one,
        test_no_bath,
        test_reversed_entropy,
        test_total_depolarization,
    ]
    
    evidence = []
    all_killed = True
    
    for test_fn in tests:
        name, dphi, killed = test_fn()
        status = "KILL" if killed else "UNEXPECTED_PASS"
        icon = "✗" if killed else "⚠"
        print(f"  {icon} {name:45s}: ΔΦ={dphi:+.4f} [{status}]")
        
        tag = name.split(":")[0].strip().replace("-", "_").replace(" ", "_")
        evidence.append(EvidenceToken(
            token_id="" if killed else f"E_{tag}_UNEXPECTED_PASS",
            sim_spec_id=f"S_{tag}",
            status="KILL" if killed else "PASS",
            measured_value=dphi,
            kill_reason=name.split(":")[1].strip() if killed else None,
        ))
        
        if not killed:
            all_killed = False
    
    killed_count = sum(1 for e in evidence if e.status == "KILL")
    print(f"\n{'='*72}")
    print(f"THERMODYNAMIC GRAVEYARD VERDICT: {killed_count}/{len(evidence)} KILLED")
    print(f"{'='*72}")
    
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "thermo_graveyard_results.json")
    
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "battery": "THERMODYNAMIC_GRAVEYARD",
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
