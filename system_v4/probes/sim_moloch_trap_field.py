"""
PRO-15: N-AGENT MOLOCH FIELD SIM
================================
Expands the IGT Moloch Trap to a multi-agent field manifold.

Classical Agents: WIN-only, using only +Te/+Ti gradient ascent operators.
  These agents greedily extract negentropy without paying Landauer costs.
  
Dual-Loop Agents: Execute the necessary LOSE -Fe/-Fi dissipation cycles.
  These agents maintain sustainable NESS by venting entropy to the bath.

Target: Prove that Classical Agents saturate their phase space and
thermalize to I/d (maximal mixedness), while Dual-Loop Agents establish
a stable Non-Equilibrium Steady State (NESS) with phi > 0.
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    make_random_unitary,
    von_neumann_entropy,
    EvidenceToken,
)


def negentropy(rho, d):
    S = von_neumann_entropy(rho)
    return max(0.0, 1.0 - S / np.log2(d))


def purity(rho):
    return np.real(np.trace(rho @ rho))


class ClassicalAgent:
    """WIN-only agent: uses gradient ascent (Te/Ti) without dissipation."""
    
    def __init__(self, d, agent_id):
        self.d = d
        self.agent_id = agent_id
        np.random.seed(100 + agent_id)
        self.rho = make_random_density_matrix(d)
        H_raw = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        self.H = (H_raw + H_raw.conj().T) / 2
        self.observable = np.diag(np.linspace(0.1, 1.0, d).astype(complex))
    
    def step(self, shared_bath):
        d = self.d
        # Te: Hamiltonian unitary drive (WIN extraction)
        dt = 0.05
        U = np.eye(d, dtype=complex) - 1j * self.H * dt
        u, _, vh = np.linalg.svd(U)
        U = u @ vh
        self.rho = U @ self.rho @ U.conj().T
        
        # Ti: Gradient ascent (greedy extraction)
        grad = self.observable @ self.rho - self.rho @ self.observable
        self.rho = self.rho + 0.03 * grad
        # Enforce Hermiticity and positive semi-definiteness
        self.rho = (self.rho + self.rho.conj().T) / 2
        evals, evecs = np.linalg.eigh(self.rho)
        evals = np.maximum(evals, 0)  # Clamp negative eigenvalues
        self.rho = evecs @ np.diag(evals) @ evecs.conj().T
        self.rho /= np.trace(self.rho)
        
        # Extract from shared bath (take heat without giving back)
        extraction = 0.02 * (self.rho - shared_bath)
        self.rho = self.rho + extraction
        self.rho = (self.rho + self.rho.conj().T) / 2
        evals, evecs = np.linalg.eigh(self.rho)
        evals = np.maximum(evals, 0)
        self.rho = evecs @ np.diag(evals) @ evecs.conj().T
        self.rho /= np.trace(self.rho)
        
        return self.rho


class DualLoopAgent:
    """Dual-loop agent: executes both WIN (Te/Ti) and LOSE (Fe/Fi) cycles."""
    
    def __init__(self, d, agent_id):
        self.d = d
        self.agent_id = agent_id
        np.random.seed(200 + agent_id)
        self.rho = make_random_density_matrix(d)
        H_raw = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        self.H = (H_raw + H_raw.conj().T) / 2
        L_raw = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        self.L = L_raw / np.linalg.norm(L_raw) * 2.0
        self.observable = np.diag(np.linspace(0.1, 1.0, d).astype(complex))
    
    def step(self, shared_bath):
        d = self.d
        dt = 0.05
        
        # ── WIN STROKE (Te/Ti): Extract negentropy ──
        U = np.eye(d, dtype=complex) - 1j * self.H * dt
        u, _, vh = np.linalg.svd(U)
        U = u @ vh
        self.rho = U @ self.rho @ U.conj().T
        
        # Ti: Measurement-guided convergence
        probs = np.abs(np.diagonal(self.rho))
        probs /= max(np.sum(probs), 1e-12)
        rho_meas = np.diag(probs.astype(complex))
        self.rho = 0.8 * self.rho + 0.2 * rho_meas
        
        # ── LOSE STROKE (Fe/Fi): Pay Landauer costs ──
        # Fe: Lindbladian dissipation (entropy export to bath)
        L = self.L
        LdL = L.conj().T @ L
        drho = L @ self.rho @ L.conj().T - 0.5 * (LdL @ self.rho + self.rho @ LdL)
        self.rho = self.rho + drho * dt
        
        # Fi: Fourier spectral smoothing (structural cooling)
        F = np.zeros((d, d), dtype=complex)
        for j in range(d):
            for k in range(d):
                F[j, k] = np.exp(2j * np.pi * j * k / d) / np.sqrt(d)
        rho_fourier = F @ self.rho @ F.conj().T
        self.rho = 0.9 * self.rho + 0.1 * rho_fourier
        
        # Cooperate with bath (give AND take)
        coupling = 0.03
        self.rho = (1 - coupling) * self.rho + coupling * shared_bath
        self.rho = (self.rho + self.rho.conj().T) / 2
        self.rho /= np.trace(self.rho)
        
        return self.rho


def run_moloch_field(d=4, n_classical=5, n_dualloop=5, n_cycles=100):
    """Execute the N-agent Moloch Field simulation."""
    print("=" * 70)
    print("PRO-15: N-AGENT MOLOCH FIELD SIM")
    print(f"  d={d}, classical={n_classical}, dual-loop={n_dualloop}")
    print(f"  cycles={n_cycles}")
    print("=" * 70)
    
    # Initialize agents
    classical_agents = [ClassicalAgent(d, i) for i in range(n_classical)]
    dualloop_agents = [DualLoopAgent(d, i) for i in range(n_dualloop)]
    
    # Shared thermal bath (starts at I/d)
    shared_bath = np.eye(d, dtype=complex) / d
    
    # Trajectories
    classical_phi = {i: [negentropy(a.rho, d)] for i, a in enumerate(classical_agents)}
    dualloop_phi = {i: [negentropy(a.rho, d)] for i, a in enumerate(dualloop_agents)}
    bath_entropy = [von_neumann_entropy(shared_bath)]
    
    for cycle in range(n_cycles):
        # All agents act on the shared bath
        all_rhos = []
        
        for i, agent in enumerate(classical_agents):
            rho = agent.step(shared_bath)
            all_rhos.append(rho)
            classical_phi[i].append(negentropy(rho, d))
        
        for i, agent in enumerate(dualloop_agents):
            rho = agent.step(shared_bath)
            all_rhos.append(rho)
            dualloop_phi[i].append(negentropy(rho, d))
        
        # Update shared bath: average of all agent states (thermalization)
        shared_bath = np.mean(all_rhos, axis=0)
        shared_bath = (shared_bath + shared_bath.conj().T) / 2
        shared_bath /= np.trace(shared_bath)
        bath_entropy.append(von_neumann_entropy(shared_bath))
        
        if cycle % 20 == 0:
            avg_c = np.mean([classical_phi[i][-1] for i in range(n_classical)])
            avg_d = np.mean([dualloop_phi[i][-1] for i in range(n_dualloop)])
            print(f"  Cycle {cycle:3d}: "
                  f"classical_avg_phi={avg_c:.4f} "
                  f"dualloop_avg_phi={avg_d:.4f} "
                  f"bath_S={bath_entropy[-1]:.4f}")
    
    # ── VERDICT ──
    avg_classical_final = np.mean([classical_phi[i][-1] for i in range(n_classical)])
    avg_dualloop_final = np.mean([dualloop_phi[i][-1] for i in range(n_dualloop)])
    classical_collapsed = avg_classical_final < 0.05
    dualloop_ness = avg_dualloop_final > 0.01
    
    print(f"\n{'='*70}")
    print(f"MOLOCH FIELD VERDICT")
    print(f"{'='*70}")
    print(f"  Classical agents avg phi: {avg_classical_final:.4f} "
          f"({'THERMALIZED' if classical_collapsed else 'ALIVE'})")
    print(f"  Dual-loop agents avg phi: {avg_dualloop_final:.4f} "
          f"({'NESS' if dualloop_ness else 'COLLAPSED'})")
    print(f"  Bath entropy: {bath_entropy[-1]:.4f} / {np.log2(d):.4f}")
    
    evidence = []
    
    # Classical thermalization check
    if classical_collapsed:
        print(f"  MOLOCH TRAP: Classical agents → I/d (thermal death)")
        evidence.append(EvidenceToken(
            token_id="E_MOLOCH_CLASSICAL_THERMAL_DEATH",
            sim_spec_id="S_MOLOCH_FIELD_V1",
            status="PASS",
            measured_value=avg_classical_final,
        ))
    else:
        evidence.append(EvidenceToken(
            token_id="E_MOLOCH_CLASSICAL_SURVIVED",
            sim_spec_id="S_MOLOCH_FIELD_V1",
            status="KILL",
            measured_value=avg_classical_final,
            kill_reason="CLASSICAL_AGENTS_SURVIVED_UNEXPECTEDLY",
        ))
    
    # Dual-loop NESS check
    if dualloop_ness:
        print(f"  NESS: Dual-loop agents sustain local gradients")
        evidence.append(EvidenceToken(
            token_id="E_MOLOCH_DUALLOOP_NESS_PASS",
            sim_spec_id="S_MOLOCH_DUALLOOP_NESS_V1",
            status="PASS",
            measured_value=avg_dualloop_final,
        ))
    else:
        evidence.append(EvidenceToken(
            token_id="",
            sim_spec_id="S_MOLOCH_DUALLOOP_NESS_V1",
            status="KILL",
            measured_value=avg_dualloop_final,
            kill_reason="DUALLOOP_AGENTS_COLLAPSED",
        ))
    
    # Save
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "moloch_trap_field_results.json")
    
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "d": d,
            "n_classical": n_classical,
            "n_dualloop": n_dualloop,
            "n_cycles": n_cycles,
            "classical_final_phi": float(avg_classical_final),
            "dualloop_final_phi": float(avg_dualloop_final),
            "classical_thermalized": bool(classical_collapsed),
            "dualloop_ness": bool(dualloop_ness),
            "bath_final_entropy": float(bath_entropy[-1]),
            "evidence_ledger": [
                {"token_id": e.token_id, "sim_spec_id": e.sim_spec_id,
                 "status": e.status, "measured_value": e.measured_value,
                 "kill_reason": e.kill_reason} for e in evidence
            ],
        }, f, indent=2)
    
    print(f"\n  Results saved: {outpath}")
    return evidence


if __name__ == "__main__":
    run_moloch_field(d=4, n_classical=5, n_dualloop=5, n_cycles=100)
