"""
NLM-1: Axis 0 Mathematical Gradient SIM
=====================================
Calculate and provide the explicit Python-ready math for Axis 0.
Should we use Quantum Conditional Entropy S(A|B) = S(AB) - S(B) or Mutual Information I(A:B)?

Mathematical Proof: 
Quantum Mutual Information is strictly non-negative (I(A:B) >= 0). 
Axis 0 must be capable of establishing a negative gradient to reverse entropy flow 
and trap thermodynamic sinks. Therefore, Axis 0 executes strictly via
Quantum Conditional Entropy S(A|B), which can be negative for highly entangled states.
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    von_neumann_entropy,
    EvidenceToken
)

def build_bell_state_density():
    """Generates a maximally entangled bipartite Bell state |Φ+⟩."""
    phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    return np.outer(phi_plus, phi_plus.conj())

def build_separable_state_density():
    """Generates a separable mixed state."""
    rho = np.eye(4, dtype=complex) / 4.0
    return rho

def quantum_mutual_information(rho_AB, d_A=2, d_B=2):
    tensor_rho = rho_AB.reshape((d_A, d_B, d_A, d_B))
    rho_A = np.trace(tensor_rho, axis1=1, axis2=3)
    rho_B = np.trace(tensor_rho, axis1=0, axis2=2)
    
    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)
    
    # I(A:B) = S(A) + S(B) - S(AB)
    return S_A + S_B - S_AB

def quantum_conditional_entropy(rho_AB, d_A=2, d_B=2):
    tensor_rho = rho_AB.reshape((d_A, d_B, d_A, d_B))
    rho_B = np.trace(tensor_rho, axis1=0, axis2=2)
    
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)
    
    # S(A|B) = S(AB) - S(B)
    return S_AB - S_B

def sim_axis0_gradient():
    print(f"\n{'='*70}")
    print(f"NLM-1: AXIS 0 CORRELATION GRADIENT SIMULATION")
    print(f"Comparing I(A:B) with S(A|B)")
    print(f"{'='*70}")
    
    rho_sep = build_separable_state_density()
    rho_entangled = build_bell_state_density()
    
    print("\nTEST 1: Separable State (No Entanglement)")
    I_sep = quantum_mutual_information(rho_sep)
    S_cond_sep = quantum_conditional_entropy(rho_sep)
    print(f"  I(A:B)  = {I_sep:.6f}")
    print(f"  S(A|B)  = {S_cond_sep:.6f}")
    
    print("\nTEST 2: Bell State (Maximal Entanglement)")
    I_ent = quantum_mutual_information(rho_entangled)
    S_cond_ent = quantum_conditional_entropy(rho_entangled)
    print(f"  I(A:B)  = {I_ent:.6f}")
    print(f"  S(A|B)  = {S_cond_ent:.6f}")
    
    # Adjudication
    axis0_formula_is_conditional = (S_cond_ent < 0.0)
    
    print(f"\n{'='*70}")
    print(f"AXIS 0 MATHEMATICAL VERDICT")
    print(f"{'='*70}")
    if axis0_formula_is_conditional:
        print("  PASS: Only Quantum Conditional Entropy S(A|B) can drop below Zero.")
        print("  Axis 0 requires negative correlations to dictate engine flow.")
        print("  Therefore, Axis 0 strictly computes S(A|B).")
        evidence = EvidenceToken(
            token_id="E_SIM_AXIS0_GRADIENT_OK",
            sim_spec_id="S_SIM_AXIS0_GRADIENT_V1",
            status="PASS",
            measured_value=float(S_cond_ent)
        )
    else:
        print("  KILL: Entanglement failed to generate negative entropy.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_AXIS0_GRADIENT_V1",
            status="KILL",
            measured_value=float(S_cond_ent),
            kill_reason="NO_NEGATIVE_ENTROPY"
        )
    
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "axis0_gradient_results.json")
    
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence_ledger": [{
                "token_id": evidence.token_id,
                "status": evidence.status,
                "measured_value": evidence.measured_value
            }]
        }, f, indent=2)
        
    return evidence

if __name__ == "__main__":
    sim_axis0_gradient()
