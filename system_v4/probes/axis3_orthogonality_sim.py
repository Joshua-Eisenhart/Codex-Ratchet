#!/usr/bin/env python3
"""
Axis 3 vs Axis 4 Orthogonality Verification SIM (Canonical Revision)
====================================================================
Verifies structural orthogonality using the true canonical operator bases:
  Axis 3 (Engine Family): Type 1 (Fe/Ti) vs Type 2 (Te/Fi)
  Axis 4 (Math Class): Deductive (Constraint First) vs Inductive (Release First)

If the Hilbert-Schmidt inner product of their State Displacements
is nominally 0, the constraint manifold is mathematically valid.
"""

import numpy as np
import scipy.linalg as la
import json
import os
import sys
import dataclasses
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken, make_random_density_matrix
from orthogonality_sim import build_Ti_ops, build_Fe_ops, build_Fi_filter, build_Te_hamiltonian

def hilbert_schmidt_inner_product(A, B):
    """Computes the Hilbert-Schmidt inner product Tr(A† B)."""
    return np.trace(A.conj().T @ B)

# --- Canonical Channel Operators ---

def C_Ti(rho, Ti_ops):
    """Ti Projection Channel (Constraint)"""
    new_rho = np.zeros_like(rho, dtype=complex)
    for P in Ti_ops:
        new_rho += P @ rho @ P.conj().T
    return new_rho

def C_Fe(rho, Fe_ops, dt=0.1):
    """Fe Lindblad Dissipation Channel (Release)
    Applies a discrete step of the Lindblad equation for the off-diagonal jumps.
    """
    new_rho = rho.copy()
    for L in Fe_ops:
        L_dag = L.conj().T
        jump = L @ rho @ L_dag
        anti_com = 0.5 * (L_dag @ L @ rho + rho @ L_dag @ L)
        new_rho += dt * (jump - anti_com)
    new_rho /= np.trace(new_rho)
    return new_rho

def C_Te(rho, Te_hamiltonian, dt=0.5):
    """Te Hamiltonian Rotation Channel (Release)"""
    U = la.expm(-1j * Te_hamiltonian * dt)
    return U @ rho @ U.conj().T

def C_Fi(rho, Fi_operator):
    """Fi Spectral Filter Channel (Constraint)"""
    new_rho = Fi_operator @ rho @ Fi_operator.conj().T
    trace_rho = np.trace(new_rho)
    if abs(trace_rho) > 1e-12:
        return new_rho / trace_rho
    return rho # Failsafe

def simulate_quadrants(d, seed=42):
    """
    Computes the state displacements for a single random setup.
    """
    np.random.seed(seed)
    
    # Initialize physics state & canonical bases
    rho_0 = make_random_density_matrix(d)
    
    Ti_ops = build_Ti_ops(d)
    Fe_ops = build_Fe_ops(d)
    Fi_op = build_Fi_filter(d)
    Te_op = build_Te_hamiltonian(d, seed=seed)

    # 1. Type 1 (Fe/Ti) | Deductive (Ti/Constraint first, then Fe/Release)
    E_1D = C_Ti(rho_0, Ti_ops)
    E_1D = C_Fe(E_1D, Fe_ops)
    
    # 2. Type 1 (Fe/Ti) | Inductive (Fe/Release first, then Ti/Constraint)
    E_1I = C_Fe(rho_0, Fe_ops)
    E_1I = C_Ti(E_1I, Ti_ops)
    
    # 3. Type 2 (Te/Fi) | Deductive (Fi/Constraint first, then Te/Release)
    E_2D = C_Fi(rho_0, Fi_op)
    E_2D = C_Te(E_2D, Te_op)
    
    # 4. Type 2 (Te/Fi) | Inductive (Te/Release first, then Fi/Constraint)
    E_2I = C_Te(rho_0, Te_op)
    E_2I = C_Fi(E_2I, Fi_op)
    
    # 3. Calculate Displacement Vectors
    # Delta Axis 3: Average difference caused by varying Engine Family
    Delta_Ax3 = 0.5 * ((E_1D - E_2D) + (E_1I - E_2I))
    
    # Delta Axis 4: Average difference caused by varying Math Class Ordering
    Delta_Ax4 = 0.5 * ((E_1D - E_1I) + (E_2D - E_2I))

    # 4. Compute Normalized Overlap
    num = abs(hilbert_schmidt_inner_product(Delta_Ax3, Delta_Ax4))
    den = np.linalg.norm(Delta_Ax3) * np.linalg.norm(Delta_Ax4)
    
    if den < 1e-12:
        return 0.0 # Trivial matrices
        
    overlap = num / den
    return float(overlap)


def run_orthogonality_test():
    d_values = [4, 8, 16]
    trials_per_d = 200
    
    results = {}
    tokens = []
    
    axis3_4_clean = True
    
    print("=" * 60)
    print("CANONICAL AXIS 3 vs AXIS 4 STRUCTURAL ORTHOGONALITY SIMULATION")
    print("=" * 60)
    
    for d in d_values:
        total_overlap = 0.0
        max_overlap = 0.0
        
        for trial in range(trials_per_d):
            overlap = simulate_quadrants(d, seed=1000 * d + trial)
            total_overlap += overlap
            max_overlap = max(max_overlap, overlap)
            
        avg_overlap = total_overlap / trials_per_d
        
        results[f"d={d}"] = {
            "trials": trials_per_d,
            "avg_overlap": float(avg_overlap),
            "max_overlap": float(max_overlap)
        }
        
        print(f"Dimension {d}: Avg Overlap = {avg_overlap:.6e}, Max Overlap = {max_overlap:.6e}")
        
        # Rigorous threshold for orthogonal basis decoupling (1% structural noise limit)
        if avg_overlap > 1e-2:
            axis3_4_clean = False

    if axis3_4_clean:
        print("\n  PASS: Axis 3 (Engine Family) is geometrically ORTHOGONAL to Axis 4 (Math Class).")
        tokens.append(EvidenceToken(
            token_id="E_SIM_AXIS3_ENGINE_ORTHOGONAL_OK",
            sim_spec_id="S_SIM_AXIS3_ORTHOGONALITY_V1",
            status="PASS",
            measured_value=results[f"d={d_values[-1]}"]["avg_overlap"]
        ))
    else:
        print("\n  KILL: Basis overlap detected. Axis 3 and Axis 4 remain geometrically coupled!")
        tokens.append(EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_AXIS3_ORTHOGONALITY_V1",
            status="KILL",
            kill_reason="AXIS_3_4_BASIS_OVERLAP_VIOLATION",
            measured_value=results[f"d={d_values[0]}"]["max_overlap"]
        ))

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "axis3_orthogonality_results.json"
    )
    
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    
    output = {
        "schema": "SIM_EVIDENCE_v1",
        "file": os.path.basename(__file__),
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "evidence_ledger": [dataclasses.asdict(t) for t in tokens],
        "measurements": results
    }
    
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
        
    print(f"\nResults written to {out_file}")

if __name__ == "__main__":
    run_orthogonality_test()
