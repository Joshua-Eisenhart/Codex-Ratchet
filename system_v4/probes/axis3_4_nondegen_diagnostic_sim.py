#!/usr/bin/env python3
"""
Axis 3↔4 Non-Degeneracy Diagnostic SIM
========================================
Deep Research audit found that axis3_orthogonality_sim.py has a DEGENERATE PASS:
  - Ti (Lüders projector) zeros off-diagonals
  - Fe (Lindblad dissipation) operates ONLY on off-diagonals
  - Result: Ti→Fe ≡ Fe→Ti (operators commute)
  - Delta_Ax4 = 0 at machine precision → trivial 0.0 overlap → false PASS

This diagnostic SIM:
  1. Measures actual displacement norms for both axes
  2. ENFORCES non-triviality gates (KILL if norms < threshold)
  3. Uses properly non-commuting operator pairs to test the REAL question:
     "Does ordering (deductive vs inductive) produce measurably different states?"
  4. The fix: Fe must also have a diagonal component, and Ti must also have
     an off-diagonal component, so they don't operate on orthogonal subspaces.
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


# ═══════════════════════════════════════════════════════════
# HARDENED OPERATOR DEFINITIONS
# These operators are non-commuting by construction:
# each one has BOTH diagonal and off-diagonal components.
# ═══════════════════════════════════════════════════════════

def build_constraint_channel(d, gamma=0.3, seed=0):
    """
    Constraint Channel (Type-1 = Ti/Lüders-like, Type-2 = Fi/Spectral-filter-like).
    Unlike the original Ti, this has BOTH diagonal dephasing AND a partial
    off-diagonal rotation, ensuring it doesn't completely zero the off-diagonals.
    """
    np.random.seed(seed + 1000)
    # Partial dephasing: suppress off-diagonals by factor (1 - gamma), not to zero
    def channel(rho):
        out = rho.copy().astype(complex)
        for i in range(d):
            for j in range(d):
                if i != j:
                    out[i, j] *= (1.0 - gamma)
        # Add a small random unitary perturbation to break commutativity
        H_pert = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        H_pert = (H_pert + H_pert.conj().T) / 2
        H_pert *= 0.1  # small perturbation
        U_pert = la.expm(-1j * H_pert * 0.05)
        out = U_pert @ out @ U_pert.conj().T
        # Enforce PSD + trace
        evals, evecs = np.linalg.eigh(out)
        evals = np.maximum(evals, 0)
        out = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
        tr = np.real(np.trace(out))
        if tr > 1e-12:
            out /= tr
        else:
            out = np.eye(d, dtype=complex) / d
        return out
    return channel


def build_release_channel(d, gamma=0.2, seed=0):
    """
    Release Channel (Type-1 = Fe/Lindblad-like, Type-2 = Te/Hamiltonian-like).
    Unlike the original Fe, this has BOTH off-diagonal dissipation AND
    diagonal population transfer, ensuring it overlaps with constraint channel.
    """
    np.random.seed(seed + 2000)
    # Build a random Lindblad operator with both diagonal and off-diagonal parts
    L = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L *= gamma / np.linalg.norm(L)
    
    def channel(rho):
        L_dag = L.conj().T
        jump = L @ rho @ L_dag
        anti_com = 0.5 * (L_dag @ L @ rho + rho @ L_dag @ L)
        out = rho + 0.1 * (jump - anti_com)
        # Enforce PSD + trace
        evals, evecs = np.linalg.eigh(out)
        evals = np.maximum(evals, 0)
        out = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
        tr = np.real(np.trace(out))
        if tr > 1e-12:
            out /= tr
        else:
            out = np.eye(d, dtype=complex) / d
        return out
    return channel


def run_diagnostic():
    """Run the hardened A3↔A4 non-degeneracy test."""
    d_values = [4, 8, 16]
    n_seeds = 50
    MIN_NORM = 1e-6  # Non-triviality gate
    
    tokens = []
    measurements = {}
    all_pass = True
    
    print("=" * 70)
    print("AXIS 3↔4 NON-DEGENERACY DIAGNOSTIC")
    print("  Testing: Do constraint/release channel orderings produce")
    print("           measurably different states? (non-commuting operators)")
    print("=" * 70)
    
    for d in d_values:
        norms_ax3 = []
        norms_ax4 = []
        overlaps = []
        degenerate_count = 0
        
        for s in range(n_seeds):
            rho_0 = make_random_density_matrix(d)
            
            # Build TWO different engine families (Type-1 vs Type-2)
            constraint_t1 = build_constraint_channel(d, gamma=0.3, seed=s)
            release_t1 = build_release_channel(d, gamma=0.2, seed=s)
            constraint_t2 = build_constraint_channel(d, gamma=0.5, seed=s + 500)
            release_t2 = build_release_channel(d, gamma=0.4, seed=s + 500)
            
            # Quadrant sweep:
            # E_1D = Type-1 Deductive (Constraint first, then Release)
            E_1D = release_t1(constraint_t1(rho_0))
            # E_1I = Type-1 Inductive (Release first, then Constraint)
            E_1I = constraint_t1(release_t1(rho_0))
            # E_2D = Type-2 Deductive 
            E_2D = release_t2(constraint_t2(rho_0))
            # E_2I = Type-2 Inductive
            E_2I = constraint_t2(release_t2(rho_0))
            
            # Axis displacements
            Delta_Ax3 = 0.5 * ((E_1D - E_2D) + (E_1I - E_2I))  # engine family
            Delta_Ax4 = 0.5 * ((E_1D - E_1I) + (E_2D - E_2I))  # ordering
            
            n3 = np.linalg.norm(Delta_Ax3)
            n4 = np.linalg.norm(Delta_Ax4)
            norms_ax3.append(n3)
            norms_ax4.append(n4)
            
            if n3 < MIN_NORM or n4 < MIN_NORM:
                degenerate_count += 1
            elif n3 * n4 > MIN_NORM:
                ovlp = abs(np.trace(Delta_Ax3.conj().T @ Delta_Ax4)) / (n3 * n4)
                overlaps.append(ovlp)
        
        avg_n3 = np.mean(norms_ax3)
        avg_n4 = np.mean(norms_ax4)
        avg_overlap = np.mean(overlaps) if overlaps else float('nan')
        
        measurements[f"d={d}"] = {
            "avg_norm_Ax3": float(avg_n3),
            "avg_norm_Ax4": float(avg_n4),
            "avg_overlap": float(avg_overlap) if overlaps else "DEGENERATE",
            "degenerate_trials": degenerate_count,
            "total_trials": n_seeds,
        }
        
        print(f"\n  d={d}:")
        print(f"    ||Delta_Ax3|| avg = {avg_n3:.6e}  (engine family difference)")
        print(f"    ||Delta_Ax4|| avg = {avg_n4:.6e}  (ordering difference)")
        print(f"    Degenerate trials: {degenerate_count}/{n_seeds}")
        if overlaps:
            print(f"    Avg overlap (non-degenerate): {avg_overlap:.6e}")
        
        # Non-triviality gate
        if avg_n4 < MIN_NORM:
            print(f"    ⛔ KILL: Axis-4 displacement collapsed to zero!")
            all_pass = False
        elif degenerate_count > n_seeds * 0.5:
            print(f"    ⛔ KILL: >50% trials degenerate!")
            all_pass = False
    
    # Emit evidence
    if all_pass:
        tokens.append(EvidenceToken(
            token_id="E_SIM_AXIS3_4_NONDEGEN_PASS",
            sim_spec_id="S_SIM_AXIS3_4_NONDEGEN_V1",
            status="PASS",
            measured_value=avg_n4,
        ))
    else:
        tokens.append(EvidenceToken(
            token_id="E_SIM_AXIS3_4_NONDEGEN_KILL",
            sim_spec_id="S_SIM_AXIS3_4_NONDEGEN_V1",
            status="KILL",
            kill_reason="AXIS4_DISPLACEMENT_DEGENERATE",
            measured_value=avg_n4,
        ))
    
    # Save results
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "axis3_4_nondegen_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "schema": "SIM_EVIDENCE_v1",
            "file": os.path.basename(__file__),
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "evidence_ledger": [dataclasses.asdict(t) for t in tokens],
            "measurements": measurements,
            "diagnosis": {
                "root_cause": "Original Ti projector zeros off-diagonals completely, "
                              "making Fe (off-diagonal-only Lindblad) commute with Ti. "
                              "Delta_Ax4 = 0 at machine precision.",
                "fix_applied": "Hardened operators use partial dephasing + random "
                               "unitary perturbation to ensure non-commutativity."
            }
        }, f, indent=2)
    
    print(f"\n  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_diagnostic()
