#!/usr/bin/env python3
"""
Negative Inverted Major Loop SIM
================================
Graveyard PROBE (Adversarial Stress Test)
Hypothesis to KILL: "The chronological order of constraints (Ti before Fe) doesn't matter, only the topological presence matters."
Test: Reverse the sequence of the Type 1 (Deductive) major loop from Ti->Fe to Fe->Ti.
Expected: Pumping heat before bounding the eigenbasis destroys constraint accumulation. The engine must saturate (ΔΦ ≈ 0) or overheat. Emits INVERTED_MAJOR_LOOP_HEATS.
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
    return max(0.0, np.log(d) - S)

def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    eigvals = np.maximum(np.real(np.linalg.eigvalsh(rho)), 0)
    if sum(eigvals) > 0:
        V = np.linalg.eigh(rho)[1]
        rho = V @ np.diag(eigvals.astype(complex)) @ V.conj().T
        rho = rho / np.trace(rho)
    return rho

def build_h_and_eigenbasis(d, seed=11):
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

# The baseline sequence is: Ti -> Fe -> Ti -> Fe -> Fi -> Te -> Fi -> Te
# We intentionally INVERT the first 4 stages: Fe -> Ti -> Fe -> Ti
INVERTED_STAGES = [
    (1, "Fe", True), (2, "Ti", False), (3, "Fe", False), (4, "Ti", True),
    (5, "Fi", False), (6, "Te", False), (7, "Fi", True), (8, "Te", True),
]

def apply_lindblad_stage(rho, d, dominant_op, H, evals, evecs, dt=0.01):
    g_eff = 5.0
    Ti_ops = build_Ti_eigen_ops(evecs, d)
    Fe_ops = build_Fe_selective_ops(evals, evecs, d)
    
    Fi = np.zeros((d, d), dtype=complex)
    for k in range(d):
        weight = 0.9 if k < d//2 else 0.5
        v = evecs[:, k].reshape(d, 1)
        Fi += weight * (v @ v.conj().T)

    if dominant_op == "Te":
        scale = g_eff * dt
        U = np.linalg.matrix_power(np.eye(d, dtype=complex) - 1j * scale * H, 1)
        Q, _ = np.linalg.qr(U)
        rho = Q @ rho @ Q.conj().T
    elif dominant_op == "Fi":
        f_scale = g_eff * dt
        rho = (1 - f_scale) * rho + f_scale * (Fi @ rho @ Fi.conj().T)
    elif dominant_op == "Ti":
        drho = np.zeros((d, d), dtype=complex)
        for L in Ti_ops:
            LdL = L.conj().T @ L
            drho += g_eff * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
        rho = rho + dt * drho
    elif dominant_op == "Fe":
        drho = np.zeros((d, d), dtype=complex)
        for L in Fe_ops:
            LdL = L.conj().T @ L
            drho += g_eff * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))
        rho = rho + dt * drho

    return ensure_valid(rho)

def sim_inverted_loop_process_cycle():
    print(f"\n{'='*70}")
    print(f"GRAVEYARD: NEGATIVE INVERTED MAJOR LOOP BOUNDARY")
    print(f"{'='*70}")

    d = 4
    np.random.seed(42)
    rho_init = make_random_density_matrix(d)
    
    H, evals, evecs = build_h_and_eigenbasis(d)
    
    phi_start = negentropy(rho_init, d)
    print(f"Initial State Negentropy: {phi_start:.6f}")
    
    rho_current = rho_init.copy()
    
    # Run 4 full cycles using the inverted major loop sequence
    for cycle in range(4):
        for _, dominant, _ in INVERTED_STAGES:
            rho_current = apply_lindblad_stage(rho_current, d, dominant, H, evals, evecs)
            
    phi_end = negentropy(rho_current, d)
    dphi = phi_end - phi_start
    
    print(f"Final State Negentropy:   {phi_end:.6f}")
    print(f"Total Cycles ΔΦ:          {dphi:+.6f}")
    
    # Validation: An inverted sequence pumps heat before constraining the eigenbasis.
    # It will mathematically saturate or fail to significantly wind.
    is_stalled = dphi <= 0.05
    
    tokens = []
    
    if is_stalled:
        print("\n  [KILL] VALIDATED: Inverting the Deductive sequence stalls thermal bounds.")
        tokens.append(EvidenceToken(
            "", "S_NEG_INVERTED_MAJOR_LOOP_V1", "KILL", dphi, "INVERTED_MAJOR_LOOP_HEATS"
        ))
    else:
        print("\n  [FAIL/WARNING] ENGINE WOUND CONTRARY TO THEORY: Inverted loop produced stable ΔΦ > 0.")
        tokens.append(EvidenceToken(
            "E_SIM_INVERTED_IMPOSSIBLE_PASS", "S_NEG_INVERTED_MAJOR_LOOP_V1", "PASS", dphi
        ))

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "neg_inverted_major_loop_results.json"
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
    sim_inverted_loop_process_cycle()
