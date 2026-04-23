#!/usr/bin/env python3
"""
Negative Commutative Process_Cycle SIM
======================================
Graveyard PROBE (Adversarial Stress Test)
Hypothesis to KILL: "The engine works with commuting operators"
Test: Replace all operators (Te, Ti, Fe, Fi) with purely diagonal (commuting) versions.
Expected: The engine MUST stall. No super-additive or sustained ratchet winding can occur.
"""

import numpy as np
import json
import os
import sys
from datetime import datetime
try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    von_neumann_entropy,
    EvidenceToken,
)

def negentropy(rho, d):
    S = von_neumann_entropy(rho) * np.log(2)
    return np.log(d) - S

def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    eigvals = np.maximum(np.real(np.linalg.eigvalsh(rho)), 0)
    if sum(eigvals) > 0:
        V = np.linalg.eigh(rho)[1]
        rho = V @ np.diag(eigvals.astype(complex)) @ V.conj().T
        rho = rho / np.trace(rho)
    return rho

def build_commuting_ops(d):
    """
    Builds sets of strictly commuting (diagonal) operators.
    To enforce [A, B] = 0 globally, all operators must share the standard computational basis.
    """
    # Te: Diagonal Hamiltonian (only imparts phase, no population rotation)
    H = np.diag(np.random.randn(d)).astype(complex)
    
    # Ti: Pure dephasing / projective diagonal
    Ti_ops = []
    for k in range(d):
        L = np.zeros((d,d), dtype=complex)
        L[k, k] = 1.0
        Ti_ops.append(L)
        
    # Fe: Normally causes population transfer. To be commuting, it MUST be diagonal.
    # We replace it with strong pure dephasing.
    Fe_ops = []
    for k in range(d):
        L = np.zeros((d,d), dtype=complex)
        L[k, k] = np.random.rand()
        Fe_ops.append(L)
        
    # Fi: Diagonal spectral filter
    Fi = np.diag(np.random.rand(d)).astype(complex)
    
    return H, Ti_ops, Fe_ops, Fi

TYPE1_STAGES = [
    (1, "Ti", False), (2, "Fe", True), (3, "Ti", True), (4, "Fe", False),
    (5, "Fi", False), (6, "Te", False), (7, "Fi", True), (8, "Te", True),
]

def apply_commutative_stage(rho, d, dominant_op, H, Ti_ops, Fe_ops, Fi, dt=0.01):
    g_eff = 5.0
    
    if dominant_op == "Te":
        # Diagonal unitary phase rotation (leaves populations entirely unchanged)
        scale = g_eff * dt
        U = np.diag(np.exp(-1j * scale * np.diag(H)))
        rho = U @ rho @ U.conj().T
    elif dominant_op == "Fi":
        # Diagonal spectral weighting
        f_scale = g_eff * dt
        rho = (1 - f_scale) * rho + f_scale * (Fi @ rho @ Fi.conj().T)
    elif dominant_op == "Ti":
        # Diagonal projection (dephasing)
        drho = np.zeros((d, d), dtype=complex)
        for L in Ti_ops:
            LdL = L.conj().T @ L
            drho += g_eff * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
        rho = rho + dt * drho
    elif dominant_op == "Fe":
        # Commuting dissipation (pure dephasing)
        drho = np.zeros((d, d), dtype=complex)
        for L in Fe_ops:
            LdL = L.conj().T @ L
            drho += g_eff * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
        rho = rho + dt * drho

    return ensure_valid(rho)

def sim_commutative_process_cycle():
    print(f"\n{'='*70}")
    print(f"GRAVEYARD: NEGATIVE COMMUTATIVE PROCESS_CYCLE BOUNDARY")
    print(f"{'='*70}")

    d = 4
    np.random.seed(42)
    rho_init = make_random_density_matrix(d)
    
    H, Ti_ops, Fe_ops, Fi = build_commuting_ops(d)
    
    phi_start = negentropy(rho_init, d)
    print(f"Initial State Negentropy: {phi_start:.6f}")
    
    rho_current = rho_init.copy()
    
    # Run 4 full 8-stage cycles to check for sustained winding
    for cycle in range(4):
        for _, dominant, _ in TYPE1_STAGES:
            rho_current = apply_commutative_stage(rho_current, d, dominant, H, Ti_ops, Fe_ops, Fi)
            
    phi_end = negentropy(rho_current, d)
    dphi = phi_end - phi_start
    
    print(f"Final State Negentropy:   {phi_end:.6f}")
    print(f"Total Cycles ΔΦ:          {dphi:+.6f}")
    
    # Validation: A commutative engine should stall entirely or strictly decohere.
    # Winding requires non-commuting flow across orthogonal bases.
    is_stalled = dphi <= 0.001
    
    tokens = []
    
    if is_stalled:
        print("\n  [KILL] VALIDATED: Commutative operator framework completely stalls ratchet winding.")
        # This is a negative SIM intended to fail. Thus a successful stall emits a KILL token correctly.
        tokens.append(EvidenceToken(
            "", "S_NEG_COMMUTATIVE_PROCESS_CYCLE_V1", "KILL", dphi, "NO_RATCHET_UNDER_COMMUTATIVITY"
        ))
    else:
        print("\n  [FAIL/WARNING] ENGINE WOUND CONTRARY TO THEORY: Commutating operators achieved ΔΦ > 0.")
        tokens.append(EvidenceToken(
            "E_SIM_COMMUTATIVE_IMPOSSIBLE_PASS", "S_NEG_COMMUTATIVE_PROCESS_CYCLE_V1", "PASS", dphi
        ))

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "neg_commutative_process_cycle_results.json"
    )
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    
    with open(out_file, "w") as f:
        json.dump({
            "schema": "SIM_EVIDENCE_v1",
            "file": os.path.basename(__file__),
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    print(f"  Results saved to: {out_file}")

if __name__ == "__main__":
    sim_commutative_process_cycle()
