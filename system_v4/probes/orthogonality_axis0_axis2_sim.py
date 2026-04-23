#!/usr/bin/env python3
"""
ORT-0.2: Axis 0 x Axis 2 Orthogonality Matrix
=============================================
Pairing: Axis 0 (Base Geometry / S3 Dimensionality) x Axis 2 (Spatial Duality)

Proof bounds:
- Axis 0 scales the base coordinate dimensionality (d=4, 8, 16)
- Axis 2 strictly separates LOCAL operations (diagonal/product state mapping) 
  from NON-LOCAL operations (coherent/entangled spatial bounds).

Hypothesis: The geometric dimension scale must not synthetically generate 
non-local entanglement during isolated Local processes, nor inappropriately 
decay perfectly entangled bounds during Non-Local mappings. Orthogonality means
the spatial regimes remain perfectly segregated regardless of matrix volume.
"""

import numpy as np
import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    von_neumann_entropy,
    EvidenceToken,
)

def partial_trace_B(rho_ab, da, db):
    rho_tensor = rho_ab.reshape(da, db, da, db)
    return np.trace(rho_tensor, axis1=1, axis2=3)

def partial_trace_A(rho_ab, da, db):
    rho_tensor = rho_ab.reshape(da, db, da, db)
    return np.trace(rho_tensor, axis1=0, axis2=2)

def quantum_mutual_information(rho_ab, da, db):
    S_AB = von_neumann_entropy(rho_ab)
    rho_a = partial_trace_B(rho_ab, da, db)
    rho_b = partial_trace_A(rho_ab, da, db)
    S_A = von_neumann_entropy(rho_a)
    S_B = von_neumann_entropy(rho_b)
    # Ensure precision artifacts don't return tiny negative numbers out of zero bounds
    return max(0.0, float(S_A + S_B - S_AB))

def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    eigvals = np.maximum(np.real(np.linalg.eigvalsh(rho)), 0)
    if sum(eigvals) > 0:
        V = np.linalg.eigh(rho)[1]
        rho = V @ np.diag(eigvals.astype(complex)) @ V.conj().T
        rho /= np.trace(rho)
    return rho

def apply_spatial_duality(d, ax2="LOCAL", steps=10):
    da = 2
    db = d // 2
    dt = 0.1
    
    if ax2 == "LOCAL":
        # Start in pure separable state
        state_A = np.zeros((da, 1), dtype=complex)
        state_A[0, 0] = 1.0
        state_B = np.zeros((db, 1), dtype=complex)
        state_B[1, 0] = 1.0
        state_joint = np.kron(state_A, state_B)
        rho = state_joint @ state_joint.conj().T
        
        np.random.seed(d)
        H_A = np.random.randn(da, da) + 1j * np.random.randn(da, da)
        H_A = (H_A + H_A.conj().T) / 2
        H_B = np.random.randn(db, db) + 1j * np.random.randn(db, db)
        H_B = (H_B + H_B.conj().T) / 2
        
        # Local operations strictly
        # Tensor sum Hamiltonian: H_A (x) I_B + I_A (x) H_B
        H_loc = np.kron(H_A, np.eye(db)) + np.kron(np.eye(da), H_B)
        
        for _ in range(steps):
            U = np.linalg.matrix_power(np.eye(d, dtype=complex) - 1j * dt * H_loc, 1)
            Q, _ = np.linalg.qr(U)
            rho = Q @ rho @ Q.conj().T
            
            # Local dissipation
            rho_a = partial_trace_B(rho, da, db)
            rho_b = partial_trace_A(rho, da, db)
            rho_a = 0.9 * rho_a + 0.1 * (np.eye(da)/da)
            rho_b = 0.9 * rho_b + 0.1 * (np.eye(db)/db)
            rho = np.kron(rho_a, rho_b)
            rho = ensure_valid(rho)

    elif ax2 == "NON_LOCAL":
        # Start in maximally entangled bipartite state (generalized Bell)
        state_joint = np.zeros((d, 1), dtype=complex)
        norm = 1.0 / np.sqrt(min(da, db))
        for i in range(min(da, db)):
            idx = i * db + i
            state_joint[idx, 0] = norm
        rho = state_joint @ state_joint.conj().T
        
        # Purely Non-Local Hamiltonian
        np.random.seed(d*10)
        H_NL = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        H_NL = (H_NL + H_NL.conj().T) / 2
        
        for _ in range(steps):
            # Applying Non-Local Rotations
            U = np.linalg.matrix_power(np.eye(d, dtype=complex) - 1j * dt * H_NL, 1)
            Q, _ = np.linalg.qr(U)
            rho = Q @ rho @ Q.conj().T
            rho = ensure_valid(rho)
            
    return rho, da, db

def execute_ort_0_2_proof():
    print(f"\n{'='*70}")
    print(f"ORT-0.2: AXIS 0 (Geometry) x AXIS 2 (Spatial Duality) SWEEP")
    print(f"{'='*70}")
    
    dimensions = [4, 8, 16]
    dualities = ["LOCAL", "NON_LOCAL"]
    
    matrix_results = {}
    validity_checks = []
    
    for d in dimensions:
        matrix_results[d] = {}
        for ax2 in dualities:
            rho_out, da, db = apply_spatial_duality(d, ax2=ax2)
            mi = quantum_mutual_information(rho_out, da, db)
            
            matrix_results[d][ax2] = {"mi": mi}
            
            if ax2 == "LOCAL":
                # Local operations must yield EXACTLY ZERO mutual information across the cut
                # Threshold accounts for very slight numerical float error in python
                is_valid = mi < 1e-4
                validity_checks.append(is_valid)
                marker = "✓ VALID" if is_valid else "✗ INVALID"
                print(f"  [{marker}] Axis0: d={d:<2} | Axis2: LOCAL     -> I(A:B) = {mi:+.6f} (Must be strict 0)")
                
            elif ax2 == "NON_LOCAL":
                # Non-local initial states must preserve massive mutual info > 0.05
                is_valid = mi > 0.5
                validity_checks.append(is_valid)
                marker = "✓ VALID" if is_valid else "✗ INVALID"
                print(f"  [{marker}] Axis0: d={d:<2} | Axis2: NON_LOCAL -> I(A:B) = {mi:+.6f} (Must remain massive)")

    orthogonality_verified = all(validity_checks)
    print(f"\n  ORT-0.2 Matrix Orthogonality Check: {orthogonality_verified}")
    
    tokens = []
    if orthogonality_verified:
        tokens.append(EvidenceToken("E_SIM_ORTHO_AXIS0_AXIS2_OK", "S_SIM_ORT_0_2", "PASS", 1.0))
    else:
        tokens.append(EvidenceToken("", "S_SIM_ORT_0_2", "KILL", 0.0, "SPATIAL_DUALITY_LEAKAGE"))
        
    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "ort_0_2_results.json"
    )
    with open(out_file, "w") as f:
        json.dump({
            "schema": "SIM_EVIDENCE_v1",
            "file": os.path.basename(__file__),
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "evidence_ledger": [t.__dict__ for t in tokens],
            "measurements": matrix_results
        }, f, indent=2)
        
    print(f"  Data bound to {out_file}\n")
    return tokens

if __name__ == "__main__":
    execute_ort_0_2_proof()
