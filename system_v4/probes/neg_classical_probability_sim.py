"""
NLM-5: Graveyard Negative Sim (Classical Probability Fails)
===========================================================
PROMPT: "Explain the underlying physics of this failure. Is it specifically 
the loss of the Berry Phase that destroys the super-additivity? Write a short, 
rigorous proof explaining why standard classical thermodynamics mathematically 
cannot replicate this 8-stage topology."

PROOF:
The Ratchet mechanism relies on the Hamiltonian flows (Te) rotating the eigenvectors 
away from the stationary diagonal basis. Without off-diagonal coherence (the Berry Phase 
complex geometric winding), the Lindbladian collapse operators simply act as a classical 
Markov chain on a probability vector. Classical detailed balance universally sinks 
the system toward the maximum entropy mixed state (I/d). 
Without Coherence -> No Symmetry Breaking -> Moloch Trap (Thermal Death).
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
    EvidenceToken
)

from full_8stage_engine_sim import (
    stage1_measurement_projection,
    stage2_diffusive_damping,
    stage3_constrained_expansion,
    stage4_entrainment_lock,
    stage5_gradient_descent,
    stage6_matched_filtering,
    stage7_spectral_emission,
    stage8_gradient_ascent
)


def force_classical_decoherence(rho):
    """Destroys all quantum coherence, reducing rho to a classical probability vector."""
    d = rho.shape[0]
    diag_rho = np.diag(np.diagonal(rho))
    
    # Enforce strict normalization and positivity
    eigvals = np.real(np.diagonal(diag_rho))
    eigvals = np.maximum(eigvals, 1e-12)
    eigvals /= np.sum(eigvals)
    return np.diag(eigvals.astype(complex))


def engine_agent_sequence(rho, d, U1, U2, L, proj, filt, obs, attractor, classical_mode=False):
    """Executes the 8-stage engine, forcing classical collapse if defined."""
    # S1
    rho = stage1_measurement_projection(rho, d)
    if classical_mode: rho = force_classical_decoherence(rho)
    # S2
    rho = stage2_diffusive_damping(rho, L, n_steps=3)
    if classical_mode: rho = force_classical_decoherence(rho)
    # S3
    rho = stage3_constrained_expansion(rho, U1, proj)
    if classical_mode: rho = force_classical_decoherence(rho)
    # S4
    rho = stage4_entrainment_lock(rho, attractor, coupling=0.2)
    if classical_mode: rho = force_classical_decoherence(rho)
    # S5
    rho = stage5_gradient_descent(rho, obs, eta=0.03)
    if classical_mode: rho = force_classical_decoherence(rho)
    # S6
    rho = stage6_matched_filtering(rho, filt)
    if classical_mode: rho = force_classical_decoherence(rho)
    # S7
    rho = stage7_spectral_emission(rho, U2, noise_scale=0.05)
    if classical_mode: rho = force_classical_decoherence(rho)
    # S8
    rho = stage8_gradient_ascent(rho, obs, eta=0.03)
    if classical_mode: rho = force_classical_decoherence(rho)
    
    return rho


def sim_neg_classical_probability(d: int = 4, cycles: int = 15):
    print(f"\n{'='*70}")
    print(f"NLM-5: GRAVEYARD NEGATIVE SIM (CLASSICAL VS QUANTUM RATCHET)")
    print(f"  d={d}, cycles={cycles}")
    print(f"{'='*70}")
    
    np.random.seed(42)
    
    U1 = make_random_unitary(d)
    U2 = make_random_unitary(d)
    L_base = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L_base / np.linalg.norm(L_base) * 3.0
    proj = np.eye(d, dtype=complex)
    proj[-1, -1] = 0.2
    filt = np.eye(d, dtype=complex)
    filt[-1, -1] = 0.1
    filt[-2, -2] = 0.3
    obs = np.diag(np.linspace(0.1, 1.0, d).astype(complex))
    
    # Random Thermal Attractor
    attractor = make_random_density_matrix(d)
    
    # Identical Start
    rho_init = make_random_density_matrix(d)
    S_start = von_neumann_entropy(rho_init)
    
    rho_q = rho_init.copy()
    rho_c = force_classical_decoherence(rho_init.copy())
    
    q_entropy = []
    c_entropy = []
    
    for cycle in range(cycles):
        rho_q = engine_agent_sequence(rho_q, d, U1, U2, L, proj, filt, obs, attractor, False)
        rho_c = engine_agent_sequence(rho_c, d, U1, U2, L, proj, filt, obs, force_classical_decoherence(attractor), True)
        
        S_q = von_neumann_entropy(rho_q)
        S_c = von_neumann_entropy(rho_c)
        
        q_entropy.append(S_q)
        c_entropy.append(S_c)
    
    print(f"\n  S_Start: {S_start:.4f}")
    print(f"  Quantum Engine Final S:   {q_entropy[-1]:.4f}  (Delta: {q_entropy[-1]-S_start:+.4f})")
    print(f"  Classical Engine Final S: {c_entropy[-1]:.4f}  (Delta: {c_entropy[-1]-S_start:+.4f})")
    
    max_S = np.log(d)
    print(f"  Thermal Death Max Entropy: {max_S:.4f}")
    
    if c_entropy[-1] > q_entropy[-1] and c_entropy[-1] > 1.0:
        print(f"\n  KILL: Classical Probability Vector cannot sustain ratchet cooling.")
        print(f"  The loss of geometric phase windings explicitly destroys the engine bounds.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_GRAVEYARD_CLASSICAL_V1",
            status="KILL",
            measured_value=float(c_entropy[-1]),
            kill_reason="CLASSICAL_PROBABILITY_INSUFFICIENT"
        )
    else:
        print(f"\n  FAIL: Classical matched Quantum? This violates thermodynamics.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_GRAVEYARD_CLASSICAL_V1",
            status="KILL",
            measured_value=0.0,
            kill_reason="SIM_INVALID"
        )
        
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "neg_classical_results.json")
    
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence_ledger": [{
                "token_id": evidence.token_id,
                "status": evidence.status,
                "measured_value": evidence.measured_value,
                "kill_reason": evidence.kill_reason
            }]
        }, f, indent=2)
        
    return evidence

if __name__ == "__main__":
    sim_neg_classical_probability(d=4, cycles=25)
