#!/usr/bin/env python3
"""
FEP ↔ Ratchet Bridge
====================
Translates Codex Ratchet QIT (Quantum Information-Theoretic) EvidenceTokens
and density matrices into Karl Friston's Variational Free Energy (FEP) bounds.

This acts as the physics boundary for the Sofia RL Holodeck:
1. Sofia proposes a state transition.
2. The Ratchet evaluates it against the 6 core axes & topologies.
3. This bridge maps the mathematical result into an RL reward signal 
   strictly governed by the minimization of F: 
   F ≅ Accuracy - Complexity

If a transition throws a KILL token (geometric conflation / entropic decay),
Free Energy spikes algorithmically to prevent the model from crossing the blanket.
"""

import numpy as np
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken, von_neumann_entropy


class FEPRatchetBridge:
    def __init__(self, dimension=4, penalty_spike=1000.0):
        """
        dimension: The d-level Hilbert space dimension of the WorldModel.
        penalty_spike: Free Energy injected into the agent when a constraint is violated.
        """
        self.d = dimension
        self.penalty_spike = penalty_spike

    def calculate_free_energy(self, rho_agent, rho_env_model):
        """
        F ≅ E_q[E(θ)] - H(q)
        Where:
        - H(q) maps to the internal State Dispersion: von_neumann_entropy(rho_agent)
        - E_q[E(θ)] maps to the Prediction Error: Hilbert-Schmidt distance to the expected environment.
        """
        # Complexity / Internal Entropy (agents must maintain negentropy to survive)
        S_internal = von_neumann_entropy(rho_agent)
        
        # Accuracy / Variational Cost (Hilbert-Schmidt inner product translates to surprise)
        overlap = np.real(np.trace(rho_agent.conj().T @ rho_env_model))
        # Surprise is the lack of overlap
        expected_energy = 1.0 - overlap
        
        # Free Energy: E(θ) - S(ρ)
        # Note: in thermodynamics, extracting work requires low internal entropy.
        F = expected_energy + S_internal
        return F

    def evaluate_transition(self, proposed_rho, ratchet_tokens):
        """
        Reads the EvidenceTokens from the lower-level Ratchet engines.
        If any constrain is KILLed, inject infinite Free Energy.
        If PASS, compute the standard variational free energy over the density frame.
        """
        # 1. Look for systemic collapse (KILL tokens) from the constraint manifold
        is_killed = any(token.status == "KILL" for token in ratchet_tokens)
        
        if is_killed:
            # Holodeck agents suffer an irreversible Free Energy spike for illegal moves
            # (e.g. unchecked Triplet composition or Axis conflation)
            reasons = [t.kill_reason for t in ratchet_tokens if t.status == "KILL"]
            return {
                "admitted": False,
                "free_energy": self.penalty_spike,
                "reward_signal": -self.penalty_spike,
                "reasons": reasons
            }
            
        # 2. If mathematically admitted, evaluate thermodynamic cost
        # The Ratchet's "optimal target" for gravity is the decay path
        # Assuming Sofia's env_model provides a target state; for bridging, 
        # we'll approximate the environment as a thermally open equilibrium (mixed)
        # to force the agent to actively fight it.
        rho_env_target = np.eye(self.d, dtype=complex) / self.d
        
        F = self.calculate_free_energy(proposed_rho, rho_env_target)
        
        # RL Reward is exactly the negative Variational Free Energy (Minimize F)
        reward_amount = -F
        
        return {
            "admitted": True,
            "free_energy": float(F),
            "reward_signal": float(reward_amount),
            "reasons": ["RATCHET_ADMITTED"]
        }


def sim_fep_bridge_unit():
    """Unit test for the FEP Bridge"""
    print(f"\n{'='*60}")
    print(f"FEP ↔ RATCHET BRIDGE: HOLODECK INTEGRATION")
    print(f"{'='*60}")
    
    bridge = FEPRatchetBridge(dimension=4)
    
    # 1. Provide an illegal state transition (e.g., Triplet Conflation)
    rho_illegal = np.eye(4) / 4.0
    tokens_illegal = [
        EvidenceToken("E_TEST", "S_TEST", "KILL", 0.0, "SYNTHETIC_CONFLATION_TRIPLET")
    ]
    
    res_kill = bridge.evaluate_transition(rho_illegal, tokens_illegal)
    
    print("Test 1: Illegal Triplet Conflation")
    print(f"  Admitted:      {res_kill['admitted']}")
    print(f"  Free Energy:   {res_kill['free_energy']:.2f} (Spike)")
    print(f"  Reward Signal: {res_kill['reward_signal']:.2f}")
    print(f"  Reason:        {res_kill['reasons']}")
    
    # 2. Provide a legal, highly-structured state transition (Chiral Ratchet Orbit)
    rho_alive = np.zeros((4,4), dtype=complex)
    rho_alive[0,0] = 0.9
    rho_alive[1,1] = 0.1
    
    tokens_alive = [
        EvidenceToken("E_TEST2", "S_TEST", "PASS", 1.0)
    ]
    
    res_pass = bridge.evaluate_transition(rho_alive, tokens_alive)

    print("\nTest 2: Admitted Topological Ratchet")
    print(f"  Admitted:      {res_pass['admitted']}")
    print(f"  Free Energy:   {res_pass['free_energy']:.4f}")
    print(f"  Reward Signal: {res_pass['reward_signal']:.4f}")
    print(f"  Reason:        {res_pass['reasons']}")
    
    # Validation
    if res_kill['admitted'] is False and res_pass['admitted'] is True and res_pass['free_energy'] < res_kill['free_energy']:
        print("\n  ✓ PASS: FEP Bridge properly bounds the Holodeck Constraint Engine!")
    else:
        print("\n  ✗ FAIL: FEP math bounds failed.")

if __name__ == "__main__":
    sim_fep_bridge_unit()
