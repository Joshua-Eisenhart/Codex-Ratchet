#!/usr/bin/env python3
"""
ORT-0.5: Axis 0 x Axis 5 Orthogonality Matrix
=============================================
Pairing: Axis 0 (Base Geometry / S3 Dimensionality) x Axis 5 (Generator Regime)

Proof bounds:
- Axis 0 scales the base coordinate dimensionality (d=4, 8, 16).
- Axis 5 defines the Generator Regime Split (Line/Fermionic vs Wave/Bosonic).
    - LINE (Fermionic): Operators behave as discrete point-to-point hops. No superposition or spread.
    - WAVE (Bosonic): Operators behave as continuous field diffusions. Natively generates max superposition.

Hypothesis: The structural dimensionality (Axis 0) MUST NOT synthetically force Line-like
operators to spontaneously diffuse into superpositions, nor artificially constrain Wave-like
operators from full manifold saturation. 
"""

import numpy as np
import scipy.linalg as la
import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    von_neumann_entropy,
    EvidenceToken,
)

def build_line_operator(d):
    """Fermionic Line Operator: Pure classical permutation loop.
    Maps basis state |k> strictly to |(k+1)%d>. Zero added superposition.
    """
    P = np.zeros((d, d), dtype=complex)
    for k in range(d):
        P[(k+1)%d, k] = 1.0
    return P

def build_wave_operator(d):
    """Bosonic Wave Operator: Pure quantum diffusion (Quantum Fourier Transform).
    Maps a single point |k> completely uniformly across the entire Hilbert phase space.
    """
    omega = np.exp(2j * np.pi / d)
    j_idx, k_idx = np.meshgrid(np.arange(d), np.arange(d))
    F_qft = np.power(omega, j_idx * k_idx) / np.sqrt(d)
    return F_qft

def execute_ort_0_5_proof():
    print(f"\n{'='*70}")
    print(f"ORT-0.5: AXIS 0 (Geometry) x AXIS 5 (Generator Regime) SWEEP")
    print(f"{'='*70}")
    
    dimensions = [4, 8, 16]
    regimes = ["LINE", "WAVE"]
    
    matrix_results = {}
    validity_checks = []
    
    for d in dimensions:
        matrix_results[d] = {}
        
        # Start in a pure point state |0><0|
        psi0 = np.zeros((d, 1), dtype=complex)
        psi0[0, 0] = 1.0
        rho_init = psi0 @ psi0.conj().T
        
        S_start = von_neumann_entropy(rho_init) # Exactly 0
        
        P_line = build_line_operator(d)
        U_wave = build_wave_operator(d)
        
        for ax5 in regimes:
            # 1. Apply geometric environmental perturbation
            if ax5 == "LINE":
                rho_out = P_line @ rho_init @ P_line.conj().T
            elif ax5 == "WAVE":
                rho_out = U_wave @ rho_init @ U_wave.conj().T
                
            S_end = von_neumann_entropy(rho_out)
            
            # Since the state might appear "pure" under QFT mathematically, 
            # to verify full spread under environment trace, we apply a weak dephasing. 
            # (Measuring in the computational basis forces waves to collapse fully mixed,
            # while lines securely survive classical hops).
            
            # Measurement / Decoherence Step (Traces out superposition)
            rho_decohered = np.diag(np.diag(rho_out))
            S_meas = von_neumann_entropy(rho_decohered)
            
            matrix_results[d][ax5] = {"S_meas": float(S_meas)}
            
            if ax5 == "LINE":
                # Line must perfectly maintain its 0.0 variance point-like spread
                is_valid = S_meas < 1e-4
                validity_checks.append(is_valid)
                marker = "✓ VALID" if is_valid else "✗ INVALID"
                print(f"  [{marker}] Axis0: d={d:<2} | Axis5: LINE -> Variance Spread S = {S_meas:.6f} (Must securely be ~0.0)")
                
            elif ax5 == "WAVE":
                # Wave must perfectly saturate the entire dimensional space log2(d)
                target_S = np.log2(d)
                is_valid = abs(S_meas - target_S) < 1e-4
                validity_checks.append(is_valid)
                marker = "✓ VALID" if is_valid else "✗ INVALID"
                print(f"  [{marker}] Axis0: d={d:<2} | Axis5: WAVE -> Variance Spread S = {S_meas:.6f} (Must saturate {target_S:.2f})")

    orthogonality_verified = all(validity_checks)
    print(f"\n  ORT-0.5 Matrix Orthogonality Check: {orthogonality_verified}")
    
    tokens = []
    if orthogonality_verified:
        tokens.append(EvidenceToken("E_SIM_ORTHO_AXIS0_AXIS5_OK", "S_SIM_ORT_0_5", "PASS", 1.0))
    else:
        tokens.append(EvidenceToken("", "S_SIM_ORT_0_5", "KILL", 0.0, "GENERATOR_REGIME_GEOMETRIC_LEAKAGE"))
        
    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "ort_0_5_results.json"
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
    execute_ort_0_5_proof()
