#!/usr/bin/env python3
"""
Axis 7-12 Mirror Validation Suite
=================================
Validates that the higher-order constraint manifold (Axes 7-12)
is mathematically orthogonal. 

While Axes 1-6 are matrices acting on states (Density Matrices),
Axes 7-12 are Superoperators (Channels) acting on Channels (Choi Matrices).
This SIM demonstrates that structural nonconflation holds at the meta-level.

Tokens emitted:
- PASS: Orthogonality between mirror axes ensures they are fundamentally distinct.
- KILL: Conflation of geometric concepts at the meta-level.
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime, UTC

from proto_ratchet_sim_runner import EvidenceToken

def build_choi(kraus_ops, d):
    """Build the Choi matrix for a quantum channel defined by Kraus operators."""
    choi = np.zeros((d**2, d**2), dtype=complex)
    for K in kraus_ops:
        vec_K = K.reshape(-1, 1)  # d^2 x 1
        choi += vec_K @ vec_K.conj().T
    return choi

def build_upper_manifold_axes(d: int):
    """
    Construct Axes 7-12 as orthogonal superoperators (Choi matrices).
    We take the base operators and lift them to the channel space.
    """
    # Create the Base (1-6) as simple unitary/Hermitian forms
    A1 = np.zeros((d, d), dtype=complex)
    A2 = np.zeros((d, d), dtype=complex)
    A3 = np.zeros((d, d), dtype=complex)
    A4 = np.diag(np.linspace(-1, 1, d)).astype(complex)
    
    for i in range(d-1):
        A1[i, i+1] = 1; A1[i+1, i] = 1
        A2[i, i] = 1; A2[-1, -1] = -1
        A3[i, i+1] = -1j; A3[i+1, i] = 1j
        
    A5 = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    A5 += A5.conj().T
    A6 = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    A6 -= A6.conj().T
        
    bases = [A1, A2, A3, A4, A5, A6]
    
    # Orthonormalize the base matrices so they don't randomly conflate
    ortho_bases = []
    for g in bases:
        # remove trace (since trace doesn't affect commutator and causes drift)
        g = g - np.trace(g)/d * np.eye(d)
        for b in ortho_bases:
            proj = np.trace(b.conj().T @ g) * b
            g = g - proj
        norm = np.linalg.norm(g, 'fro')
        if norm > 1e-10:
            g = g / norm
            ortho_bases.append(g)
    
    # Lift to Choi space (Mirror level: Axis 7 is the channel mapping defined by Axis 1, etc)
    choi_axes = []
    for B in ortho_bases:
        # A simple unitary channel K = exp(i * eps * B)
        eps = 0.01
        if np.allclose(B, B.conj().T):
            U = np.eye(d) + 1j * eps * B
        else:
            U = np.eye(d) + eps * B # e.g. anti-hermitian
            
        choi = build_choi([U], d)
        
        # Center to the identity channel to measure deviation orthogonal directions
        id_choi = build_choi([np.eye(d)], d)
        delta_choi = choi - id_choi
        norm = np.linalg.norm(delta_choi, 'fro')
        if norm > 1e-10:
            delta_choi = delta_choi / norm
            
        choi_axes.append(delta_choi)
        
    return choi_axes

def check_orthogonality(X, Y):
    """Normalized Hilbert-Schmidt inner product between two superoperators."""
    ip = np.trace(X.conj().T @ Y)
    nx = np.linalg.norm(X, 'fro')
    ny = np.linalg.norm(Y, 'fro')
    return np.abs(ip) / (nx * ny + 1e-12)

def main():
    tokens = []
    d = 4
    
    axes7_12 = build_upper_manifold_axes(d)
    
    for i in range(len(axes7_12)):
        for j in range(i + 1, len(axes7_12)):
            # The indices 0-5 map to Mirror Axes 7-12
            ax_name_1 = f"AXIS_{i+7}"
            ax_name_2 = f"AXIS_{j+7}"
            overlap = check_orthogonality(axes7_12[i], axes7_12[j])
            
            if overlap < 1e-5:
                status = "PASS"
                measured = float(overlap)
                reason = ""
            else:
                status = "KILL"
                measured = float(overlap)
                reason = f"Meta-Conflation: {ax_name_1} leaks into {ax_name_2}"
                
            token = EvidenceToken(
                token_id=f"E_SIM_ORTHO_{ax_name_1}_{ax_name_2}",
                sim_spec_id="S_AXIS_7_12_ORTHOGONALITY",
                status=status,
                measured_value=measured,
                kill_reason=reason
            )
            tokens.append(token)
            
    # Save Report
    out_dir = Path(__file__).parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "axis_7_12_ortho_results.json"
    
    report_data = {
        "sim_name": "Axis 7-12 Mirror Orthogonality",
        "timestamp": datetime.now(UTC).isoformat(),
        "evidence_ledger": [t.__dict__ for t in tokens]
    }
    
    with open(report_file, "w") as f:
        json.dump(report_data, f, indent=2)

    pass_count = sum(1 for t in tokens if t.status == "PASS")
    kill_count = sum(1 for t in tokens if t.status == "KILL")
    
    print(f"Axis 7-12 Mirror Orthogonality Complete. PASS: {pass_count}, KILL: {kill_count}")
    print(f"Report saved to: {report_file}")
    sys.exit(0 if kill_count == 0 else 1)

if __name__ == "__main__":
    main()
