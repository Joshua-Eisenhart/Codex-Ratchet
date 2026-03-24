#!/usr/bin/env python3
"""
Tier-3 Mega SIM: 2-Engine Coupling
==================================
Tests the capability of two independent 8-stage engines to structurally couple
via a shared Lindbladian bath (+Fe entrainment) while strictly preserving
the No-Signaling constraint.

Agents:
  - Agent A: d=2 (Engine A)
  - Agent B: d=2 (Engine B)
  - Total System: d=4

Expected Emits:
  - E_SIM_MEGA_ENTRAINMENT_OK
  - E_SIM_NO_SIGNALING_OK
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
    make_random_unitary,
    von_neumann_entropy,
    trace_distance,
    EvidenceToken,
)

def partial_trace_B(rho_ab, d_a=2, d_b=2):
    rho_a = np.zeros((d_a, d_a), dtype=complex)
    for i in range(d_a):
        for j in range(d_a):
            for k in range(d_b):
                rho_a[i, j] += rho_ab[i * d_b + k, j * d_b + k]
    return rho_a

def partial_trace_A(rho_ab, d_a=2, d_b=2):
    rho_b = np.zeros((d_b, d_b), dtype=complex)
    for i in range(d_b):
        for j in range(d_b):
            for k in range(d_a):
                rho_b[i, j] += rho_ab[k * d_b + i, k * d_b + j]
    return rho_b

def mutual_information(rho_ab, d_a=2, d_b=2):
    rho_a = partial_trace_B(rho_ab, d_a, d_b)
    rho_b = partial_trace_A(rho_ab, d_a, d_b)
    S_a = von_neumann_entropy(rho_a)
    S_b = von_neumann_entropy(rho_b)
    S_ab = von_neumann_entropy(rho_ab)
    return max(0.0, float(S_a + S_b - S_ab))

def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    eigvals = np.maximum(np.real(np.linalg.eigvalsh(rho)), 1e-12)
    V = np.linalg.eigh(rho)[1]
    rho = V @ np.diag(eigvals.astype(complex)) @ V.conj().T
    return rho / np.trace(rho)

def local_lindblad_step(rho_ab, L_A, L_B, dt=0.01):
    """Applies strictly local dissipation: (L_A @ I) and (I @ L_B)"""
    I = np.eye(2, dtype=complex)
    L_tot_A = np.kron(L_A, I)
    L_tot_B = np.kron(I, L_B)
    
    drho = np.zeros_like(rho_ab)
    for L in [L_tot_A, L_tot_B]:
        LdL = L.conj().T @ L
        drho += 5.0 * (L @ rho_ab @ L.conj().T - 0.5 * (LdL @ rho_ab + rho_ab @ LdL))
    
    return ensure_valid(rho_ab + dt * drho)

def coherent_entrainment_step(rho_ab, dt=0.01):
    """Applies the shared +Fe coupling bath where A excites B"""
    # L_A = sigma_minus (cooling), L_B = sigma_plus (heating)
    sm = np.array([[0,0],[1,0]], dtype=complex)
    sp = np.array([[0,1],[0,0]], dtype=complex)
    
    # Joint coupling operator ensuring action is mediated through bath
    L_joint = np.kron(sm, sp)
    LdL = L_joint.conj().T @ L_joint
    
    drho = 10.0 * (L_joint @ rho_ab @ L_joint.conj().T - 0.5 * (LdL @ rho_ab + rho_ab @ LdL))
    return ensure_valid(rho_ab + dt * drho)

def apply_local_unitary(rho_ab, U_A, U_B):
    U_tot = np.kron(U_A, U_B)
    return U_tot @ rho_ab @ U_tot.conj().T

def sim_tier3_mega():
    print(f"\n{'='*70}")
    print(f"TIER-3 MEGA SIM: NO-SIGNALING & ENTRAINMENT COUPLING")
    print(f"{'='*70}")

    np.random.seed(42)
    rho_A = make_random_density_matrix(2)
    rho_B = make_random_density_matrix(2)
    rho_AB = np.kron(rho_A, rho_B)
    
    tokens = []
    
    # 1. Independent Operations must not generate Mutual Info
    U_A = make_random_unitary(2)
    U_B = make_random_unitary(2)
    L_A = np.random.randn(2, 2) + 1j * np.random.randn(2, 2)
    L_B = np.random.randn(2, 2) + 1j * np.random.randn(2, 2)
    
    rho_AB_indep = rho_AB.copy()
    for _ in range(5):
        rho_AB_indep = apply_local_unitary(rho_AB_indep, U_A, U_B)
        rho_AB_indep = local_lindblad_step(rho_AB_indep, L_A, L_B)
        
    mi_indep = mutual_information(rho_AB_indep)
    print(f"  Mutual Info after fully independent cycles: {mi_indep:.6f}")
    assert mi_indep < 0.01, f"Independent operations generated FTL correlation: {mi_indep}"
    
    # 2. Activating the Shared Fe Bath (Entrainment)
    rho_AB_coupled = rho_AB_indep.copy()
    for _ in range(20):
        rho_AB_coupled = coherent_entrainment_step(rho_AB_coupled, dt=0.05)
        
    mi_coupled = mutual_information(rho_AB_coupled)
    print(f"  Mutual Info after active Bath Entrainment: {mi_coupled:.6f}")
    
    is_entrained = mi_coupled > 0.01
    if is_entrained:
        tokens.append(EvidenceToken(
            "E_SIM_MEGA_ENTRAINMENT_OK", "S_SIM_MEGA_ENTRAINMENT_V1", "PASS", mi_coupled
        ))
        
    # 3. No-Signaling Structural Verification
    # We take the coupled state, take the B marginal.
    marginal_B_before = partial_trace_A(rho_AB_coupled)
    
    # We apply a radical, unilateral unitary shock to A ONLY.
    U_shock_A = make_random_unitary(2)
    U_shock_A = np.linalg.matrix_power(U_shock_A, 5) # massive deviation
    I_B = np.eye(2, dtype=complex)
    
    rho_AB_shocked = np.kron(U_shock_A, I_B) @ rho_AB_coupled @ np.kron(U_shock_A, I_B).conj().T
    
    # Check marginal of B immediately after A's shock
    marginal_B_after = partial_trace_A(rho_AB_shocked)
    dist_B = trace_distance(marginal_B_before, marginal_B_after)
    
    print(f"  Trace distance of B marginal after aggressive A-shock: {dist_B:.6e}")
    is_no_signaling = dist_B < 1e-10
    
    if is_no_signaling:
        print("  ✓ NO-SIGNALING THEOREM PRESERVED")
        tokens.append(EvidenceToken(
            "E_SIM_NO_SIGNALING_OK", "S_SIM_NO_SIGNALING_V1", "PASS", float(1.0 - dist_B)
        ))
    else:
        print("  ✗ FTL SIGNALING DETECTED! Physics bounds violated.")
        tokens.append(EvidenceToken(
            "", "S_SIM_NO_SIGNALING_V1", "KILL", float(dist_B), "FTL_COMMUNICATION_ACHIEVED"
        ))

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "tier_3_mega_results.json"
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
    sim_tier3_mega()
