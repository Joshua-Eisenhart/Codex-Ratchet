#!/usr/bin/env python3
"""
64-Stage Dual Szilard Process_Cycle SIM V2
===================================
Tests explicitly for SUPER-ADDITIVITY (C4/C6 logic).
Process_Cycle A is the deductive/cooling cycle.
Process_Cycle B is the inductive/heating cycle.

Instead of identical engines, A and B will have different Hamiltonians (Te)
and different filter eigenbases to ensure they are non-identical.
We test: ΔΦ_AB > ΔΦ_A + ΔΦ_B
"""

import numpy as np
import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    von_neumann_entropy,
    trace_distance,
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

def build_h_and_eigenbasis(d, seed=77):
    np.random.seed(seed)
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2
    evals, evecs = np.linalg.eigh(H)
    return H, evals, evecs

def build_Ti_eigen_ops(evecs, d):
    Ti_ops = []
    for k in range(d):
        v = evecs[:, k].reshape(d, 1)
        L = v @ v.conj().T
        Ti_ops.append(L)
    return Ti_ops

def build_Fe_selective_ops(evals, evecs, d, beta=1.0):
    Fe_ops = []
    for j in range(d):
        for k in range(d):
            if j != k:
                v_j = evecs[:, j].reshape(d, 1)
                v_k = evecs[:, k].reshape(d, 1)
                delta_E = evals[j] - evals[k]
                rate = 1.0 if delta_E > 0 else np.exp(beta * delta_E)
                L = np.sqrt(rate) * (v_k @ v_j.conj().T)
                Fe_ops.append(L)
    return Fe_ops

TYPE1_STAGES = [
    (1, "Ti", False), (2, "Fe", True), (3, "Ti", True), (4, "Fe", False),
    (5, "Fi", False), (6, "Te", False), (7, "Fi", True), (8, "Te", True),
]

def apply_lindblad_stage(rho, d, dominant_op, axis6_up, H, evals, evecs, gamma_dom=5.0, gamma_sub=1.0, dt=0.01):
    omega = np.linalg.norm(H, 'fro') / np.sqrt(d)
    min_gamma = 2.0 * omega
    g_dom_eff = max(gamma_dom, min_gamma)
    
    Ti_ops = build_Ti_eigen_ops(evecs, d)
    Fe_ops = build_Fe_selective_ops(evals, evecs, d)
    
    Fi = np.zeros((d, d), dtype=complex)
    for k in range(d):
        weight = 0.9 if k < d//2 else 0.5
        v = evecs[:, k].reshape(d, 1)
        Fi += weight * (v @ v.conj().T)

    if dominant_op == "Te":
        scale = g_dom_eff * dt
        U = np.linalg.matrix_power(np.eye(d, dtype=complex) - 1j * scale * H, 1)
        Q, _ = np.linalg.qr(U)
        rho = Q @ rho @ Q.conj().T
    elif dominant_op == "Fi":
        f_scale = g_dom_eff * dt
        rho = (1 - f_scale) * rho + f_scale * (Fi @ rho @ Fi.conj().T)
    elif dominant_op == "Ti":
        drho = np.zeros((d, d), dtype=complex)
        for L in Ti_ops:
            LdL = L.conj().T @ L
            drho += g_dom_eff * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
        rho = rho + dt * drho
    elif dominant_op == "Fe":
        drho = np.zeros((d, d), dtype=complex)
        for L in Fe_ops:
            LdL = L.conj().T @ L
            drho += g_dom_eff * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
        rho = rho + dt * drho

    return ensure_valid(rho)

def sim_dual_szilard_v2(d=4):
    print(f"\n{'='*70}")
    print(f"DUAL SZILARD SUPER-ADDITIVITY TEST V2")
    print(f"{'='*70}")

    np.random.seed(42)
    rho_init = make_random_density_matrix(d)
    
    # Process_Cycle A properties (Deductive loop)
    H_A, evals_A, evecs_A = build_h_and_eigenbasis(d, seed=101)
    
    # Process_Cycle B properties (Inductive loop - Non-identical)
    H_B, evals_B, evecs_B = build_h_and_eigenbasis(d, seed=202)

    # 1. Run Process_Cycle A strictly alone
    rho_A = rho_init.copy()
    phi_start_A = negentropy(rho_A, d)
    for _, dominant, up in TYPE1_STAGES[:4]:
        rho_A = apply_lindblad_stage(rho_A, d, dominant, up, H_A, evals_A, evecs_A)
    for _, dominant, up in TYPE1_STAGES[4:]:
        # Process_Cycle A doing the second half of the loop with its own properties
        rho_A = apply_lindblad_stage(rho_A, d, dominant, up, H_A, evals_A, evecs_A)
    dphi_A = negentropy(rho_A, d) - phi_start_A

    # 2. Run Process_Cycle B strictly alone
    rho_B = rho_init.copy()
    phi_start_B = negentropy(rho_B, d)
    for _, dominant, up in TYPE1_STAGES[:4]:
        # Process_Cycle B doing first half
        rho_B = apply_lindblad_stage(rho_B, d, dominant, up, H_B, evals_B, evecs_B)
    for _, dominant, up in TYPE1_STAGES[4:]:
        rho_B = apply_lindblad_stage(rho_B, d, dominant, up, H_B, evals_B, evecs_B)
    dphi_B = negentropy(rho_B, d) - phi_start_B

    # 3. Run Coupled (A -> B)
    rho_AB = rho_init.copy()
    phi_start_AB = negentropy(rho_AB, d)
    # Stage 1-4 uses Process_Cycle A
    for _, dominant, up in TYPE1_STAGES[:4]:
        rho_AB = apply_lindblad_stage(rho_AB, d, dominant, up, H_A, evals_A, evecs_A)
    # Hand off (Berry Phase coupling mechanism)
    # Stage 5-8 uses Process_Cycle B
    for _, dominant, up in TYPE1_STAGES[4:]:
        rho_AB = apply_lindblad_stage(rho_AB, d, dominant, up, H_B, evals_B, evecs_B)
    dphi_AB = negentropy(rho_AB, d) - phi_start_AB

    print(f"  ΔΦ Process_Cycle A alone: {dphi_A:+.6f}")
    print(f"  ΔΦ Process_Cycle B alone: {dphi_B:+.6f}")
    sum_parts = dphi_A + dphi_B
    print(f"  Current Sum of Parts:  {sum_parts:+.6f}")
    print(f"  ΔΦ Coupled (A→B):  {dphi_AB:+.6f}")

    is_super_additive = bool(dphi_AB > sum_parts)

    tokens = []
    if is_super_additive:
        print(f"\n  ✓ ADDITIVE KILL RESOLVED: Super-additivity confirmed (Coupled > Sum(Parts))")
        tokens.append(EvidenceToken(
            "E_SIM_DUAL_SZILARD_V2_OK", "S_SIM_DUAL_SZILARD_V2", "PASS", dphi_AB
        ))
    else:
        print(f"\n  ✗ NOT SUPER-ADDITIVE: Coupled <= Sum(Parts)")
        tokens.append(EvidenceToken(
            "", "S_SIM_DUAL_SZILARD_V2", "KILL", dphi_AB, "STILL_ADDITIVE"
        ))

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "szilard_64stage_v2_results.json"
    )
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    
    with open(out_file, "w") as f:
        json.dump({
            "schema": "SIM_EVIDENCE_v1",
            "file": "szilard_64stage_v2_sim.py",
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "tokens": [t.__dict__ for t in tokens],
            "measurements": {
                "dphi_A": dphi_A,
                "dphi_B": dphi_B,
                "dphi_sum": sum_parts,
                "dphi_AB": dphi_AB,
                "super_additive": is_super_additive
            }
        }, f, indent=2)
    print(f"  Results saved to: {out_file}")

    return tokens

if __name__ == "__main__":
    try:
        from datetime import UTC
    except ImportError:
        from datetime import timezone
        UTC = timezone.utc
    sim_dual_szilard_v2()
