#!/usr/bin/env python3
"""
ORT-0.6: Axis 0 x Axis 6 Orthogonality Matrix
=============================================
Pairing: Axis 0 (Base Geometry / S3 Dimensionality) x Axis 6 (Composition Sidedness)

Proof bounds:
- Axis 0 scales the base coordinate dimensionality (d=4, 8, 16).
- Axis 6 specifies computational Precedence / Composition Sidedness (UP vs DOWN).
    - UP Mode: Operation A followed by Operation B.
    - DOWN Mode: Operation B followed by Operation A.

Hypothesis: Mathematical non-commutativity must remain strict. If the geometric 
volume (Axis 0) arbitrarily forces non-commuting operators to mathematically
overlap or artificially separate beyond topological norms, Axis 0 and Axis 6 conflate.
Orthogonality dictates that the Trace Distance between UP and DOWN operations
remains consistently bounded and massive regardless of coordinates.
"""

import numpy as np
import scipy.linalg as la
import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken
from axis3_orthogonality_sim import C_Ti, C_Te
from orthogonality_sim import build_Ti_ops, build_Te_hamiltonian

def trace_distance(rho_1, rho_2):
    diff = rho_1 - rho_2
    eigvals = np.real(la.eigvalsh(diff))
    return 0.5 * np.sum(np.abs(eigvals))

def execute_ort_0_6_proof():
    print(f"\n{'='*70}")
    print(f"ORT-0.6: AXIS 0 (Geometry) x AXIS 6 (Composition Sidedness) SWEEP")
    print(f"{'='*70}")
    
    dimensions = [4, 8, 16]
    
    matrix_results = {}
    validity_checks = []
    
    for d in dimensions:
        matrix_results[d] = {}
        
        # Start in a localized pure state to maximize commutator divergence
        # Setting psi0 to |0> ensures that projection (A) leaves it invariant, while 
        # rotation (B) forcibly throws it into a distributed wave. 
        psi0 = np.zeros((d, 1), dtype=complex)
        psi0[0, 0] = 1.0
        rho_init = psi0 @ psi0.conj().T
        
        # Define Operator A (Diagonal Constraint) and Operator B (Continuous Rotation)
        Ti_ops = build_Ti_ops(d)
        Te_op = build_Te_hamiltonian(d, seed=42)
        
        # Operator A: Deductive projection
        def apply_A(rho):
            return C_Ti(rho, Ti_ops)
            
        # Operator B: Inductive rotation
        def apply_B(rho):
            return C_Te(rho, Te_op, dt=1.0)
            
        # AXIS 6 UP MODE: A(B(rho))
        rho_UP = apply_A(apply_B(rho_init.copy()))
        
        # AXIS 6 DOWN MODE: B(A(rho))
        rho_DOWN = apply_B(apply_A(rho_init.copy()))
        
        # Compute Structural Sidedness Asymmetry
        commutator_distance = trace_distance(rho_UP, rho_DOWN)
        
        # Normalize trace distance against maximum possible topological distance
        # For trace distance, Max = 1.0 (Completely distinguishable orthogonal states)
        matrix_results[d] = {
            "Sidedness_Asymmetry_T": float(commutator_distance)
        }
        
        # Sidedness must mathematically shatter the matrix, yielding massive asymmetry >= 0.20
        # If D=16 falls to 0.00, Geometry destroyed Precedence.
        is_valid = commutator_distance > 0.20
        validity_checks.append(is_valid)
        
        marker = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"  [{marker}] Axis0: d={d:<2} | Sidedness Asymmetry T(UP, DOWN) = {commutator_distance:.5f} (Must remain > 0.20)")

    # Test dimensional cross-coupling (Asymmetry must not wildly vary as a function of volume alone)
    d4_asym = matrix_results[4]["Sidedness_Asymmetry_T"]
    d16_asym = matrix_results[16]["Sidedness_Asymmetry_T"]
    
    drift_coupling = abs(d16_asym - d4_asym)
    matrix_aligned = drift_coupling < 0.25 # Arbitrary loose topological coupling constraint
    
    print(f"\n  Axis 0 vs Axis 6 Sidedness Drift Coupling: {drift_coupling:.5f} (Allowed < 0.25)")
    
    orthogonality_verified = all(validity_checks) and matrix_aligned
    print(f"  ORT-0.6 Matrix Orthogonality Check: {orthogonality_verified}")
    
    tokens = []
    if orthogonality_verified:
        tokens.append(EvidenceToken("E_SIM_ORTHO_AXIS0_AXIS6_OK", "S_SIM_ORT_0_6", "PASS", 1.0))
    else:
        tokens.append(EvidenceToken("", "S_SIM_ORT_0_6", "KILL", 0.0, "SIDEDNESS_GEOMETRIC_LEAKAGE"))
        
    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "ort_0_6_results.json"
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
    execute_ort_0_6_proof()
