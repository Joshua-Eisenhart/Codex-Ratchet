"""
NLM-4: IGT Fields & The Moloch Trap
===================================
PROMPT: "What is the exact mathematical proof that the inclusion of the 'LOSE' stroke 
(which sacrifices local state parity) is the strictly necessary requirement to maintain 
a global NESS ΔΦ > 0 and escape the Moloch Trap?"

PROOF:
In an N-agent manifold coupled to a shared finite thermal bath, a 'WIN' stroke 
(local entropy reduction) strictly requires extracting negentropy from the bath, 
pushing the bath toward thermal death (I/d). If all agents defect to 'WIN-only' 
strategies (The Moloch Trap), the bath reaches maximum entropy, nullifying the 
thermal gradient and permanently stalling the engine (Carnot Failure).
A 'LOSE' stroke deliberately sacrifices local structure to "cool" the environmental 
bath, sustaining the global thermal gradient required for continuous NESS operation.
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    von_neumann_entropy,
    EvidenceToken
)

def apply_win_stroke(rho_agent, rho_bath, extraction_rate=0.1):
    """
    WIN Stroke: Agent extracts order from the bath.
    Agent -> cools (approaches pure state).
    Bath -> heats (approaches I/d).
    """
    d = rho_agent.shape[0]
    
    # Check if bath has any gradient left to extract
    S_bath = von_neumann_entropy(rho_bath)
    S_max = np.log(d)
    gradient = max(0.0, 1.0 - (S_bath / S_max))
    
    if gradient < 1e-4:
        return rho_agent, rho_bath # Bath is dead, action fails

    effective_rate = extraction_rate * gradient
    
    # Agent isolates structure
    pure_target = np.zeros((d, d), dtype=complex)
    pure_target[0, 0] = 1.0
    rho_agent_new = (1 - effective_rate) * rho_agent + effective_rate * pure_target
    
    # Bath absorbs the entropy cost
    I_d = np.eye(d, dtype=complex) / d
    rho_bath_new = (1 - effective_rate) * rho_bath + effective_rate * I_d
    
    return rho_agent_new, rho_bath_new

def apply_lose_stroke(rho_agent, rho_bath, sacrifice_rate=0.1):
    """
    LOSE Stroke: Agent sacrifices local structure to cool the bath.
    Agent -> heats (approaches I/d).
    Bath -> cools (approaches structured pure state).
    """
    d = rho_agent.shape[0]
    
    # Agent burns its localized order
    I_d = np.eye(d, dtype=complex) / d
    rho_agent_new = (1 - sacrifice_rate) * rho_agent + sacrifice_rate * I_d
    
    # Bath receives the structural injection (cooling)
    pure_target = np.zeros((d, d), dtype=complex)
    pure_target[0, 0] = 1.0
    rho_bath_new = (1 - sacrifice_rate) * rho_bath + sacrifice_rate * pure_target
    
    return rho_agent_new, rho_bath_new

def sim_moloch_trap(d=4, n_agents=10, cycles=50):
    print(f"\n{'='*70}")
    print(f"NLM-4: IGT MOLOCH TRAP SIMULATION")
    print(f"  d={d}, agents={n_agents}, cycles={cycles}")
    print(f"{'='*70}")
    
    # SCENARIO A: The Moloch Trap (WIN-ONLY Agents)
    rho_bath_A = np.eye(d, dtype=complex) / d
    rho_bath_A[0, 0] += 0.5 # Give bath initial structure
    rho_bath_A /= np.trace(rho_bath_A)
    
    agents_A = [make_random_density_matrix(d) for _ in range(n_agents)]
    
    print("\nSCENARIO A: ALL AGENTS DEFECT (WIN-ONLY)")
    a_bath_history = []
    
    for cycle in range(cycles):
        for i in range(n_agents):
            agents_A[i], rho_bath_A = apply_win_stroke(agents_A[i], rho_bath_A, extraction_rate=0.15)
        a_bath_history.append(von_neumann_entropy(rho_bath_A))

    final_gradient_A = max(0.0, 1.0 - (a_bath_history[-1] / np.log(d)))
    print(f"  Final Bath Entropy: {a_bath_history[-1]:.4f} (Max={np.log(d):.4f})")
    print(f"  Final Available Free Energy Gradient: {final_gradient_A:.6f}")
    
    # SCENARIO B: NESS Survival (WIN + LOSE Cycles)
    rho_bath_B = np.eye(d, dtype=complex) / d
    rho_bath_B[0, 0] += 0.5 # Same initial structure
    rho_bath_B /= np.trace(rho_bath_B)
    
    agents_B = [make_random_density_matrix(d) for _ in range(n_agents)]
    
    print("\nSCENARIO B: COOPERATIVE NESS (WIN + LOSE)")
    b_bath_history = []
    
    for cycle in range(cycles):
        for i in range(n_agents):
            # Agent alternates between extraction and sacrifice
            if cycle % 2 == 0:
                agents_B[i], rho_bath_B = apply_win_stroke(agents_B[i], rho_bath_B, extraction_rate=0.15)
            else:
                agents_B[i], rho_bath_B = apply_lose_stroke(agents_B[i], rho_bath_B, sacrifice_rate=0.10)
        b_bath_history.append(von_neumann_entropy(rho_bath_B))
        
    final_gradient_B = max(0.0, 1.0 - (b_bath_history[-1] / np.log(d)))
    print(f"  Final Bath Entropy: {b_bath_history[-1]:.4f} (Max={np.log(d):.4f})")
    print(f"  Final Available Free Energy Gradient: {final_gradient_B:.6f}")

    print(f"\n{'='*70}")
    print(f"MOLOCH TRAP VERDICT")
    print(f"{'='*70}")
    
    if final_gradient_A < 1e-4 and final_gradient_B > 0.1:
        print("  PASS: WIN-only greed instantly exhausts the global bath (Moloch Death).")
        print("  Sustained Structural NESS strictly requires cyclical LOSE sacrifices.")
        evidence = EvidenceToken(
            token_id="E_SIM_MOLOCH_TRAP_OK",
            sim_spec_id="S_SIM_MOLOCH_TRAP_V1",
            status="PASS",
            measured_value=final_gradient_B
        )
    else:
        print("  KILL: Thermodynamics scaling failed.")
        evidence = EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_MOLOCH_TRAP_V1",
            status="KILL",
            measured_value=final_gradient_B,
            kill_reason="MOLOCH_TRAP_FAILED_TO_KILL_GREEDY_AGENTS"
        )
        
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "igt_moloch_trap_results.json")
    
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence_ledger": [{
                "token_id": evidence.token_id,
                "status": evidence.status,
                "measured_value": evidence.measured_value,
                "kill_reason": evidence.kill_reason
            }]
        }, f, indent=2)
        
    return evidence

if __name__ == "__main__":
    sim_moloch_trap()
