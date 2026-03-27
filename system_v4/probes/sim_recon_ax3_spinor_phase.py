#!/usr/bin/env python3
"""
Phenomenological Reconnaissance: Ax3 Spinor Phase
=================================================
Rule #1: Outside-State Probes Only See Shadows.
Ax3 (Chirality) phase is completely destroyed by the projection down to 
a block-diagonal trace-1 density matrix. 
We must measure overlap at the S3/Weyl-Spinor constraint level.

We test:
1. Pure Parity (L <-> R swap)
2. CP (Inverted Mirror: L <-> R*)
3. gamma5 relative phase shift (e^{i gamma_5 theta})
4. Branch coherence global phase tracking

This probe works explicitly on normalized 4-comp Dirac vectors |psi>, 
not on rho.
"""

import numpy as np
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def generate_dirac_state(rng):
    """Generate a valid, fully normalized 4-comp Dirac/Weyl-pair state."""
    psi_L = rng.normal(size=2) + 1j*rng.normal(size=2)
    psi_R = rng.normal(size=2) + 1j*rng.normal(size=2)
    
    # Must normalize the whole Dirac state to 1 to live on S^7 (S^3 x S^3 bundle)
    psi = np.concatenate([psi_L, psi_R])
    psi /= np.linalg.norm(psi)
    return psi

def d_overlap(psi1, psi2):
    """Fubini-Study / Ray distance metric for pure states. 0 = identical, 1 = orthogonal."""
    # |<psi1|psi2>|^2
    olap_sq = np.abs(np.vdot(psi1, psi2))**2
    return 1.0 - olap_sq

# ═══════════════════════════════════════════════════════════════════
# Candiates: F(psi) -> psi'
# We look at the transformation induced by the candidate.
# To compute overlap between formulations A and B, we measure distance
# between A(psi) and B(psi) (or the operator distance if linear).
# Since these are pure states, we just track the state displacement.
# ═══════════════════════════════════════════════════════════════════

def ax3_parity(psi):
    """Pure spatial inverse: L <-> R block swap"""
    return np.concatenate([psi[2:4], psi[0:2]])

def ax3_cp(psi):
    """CP Mirror: L <-> R*"""
    return np.concatenate([np.conj(psi[2:4]), np.conj(psi[0:2])])

def ax3_g5_phase(psi, theta=np.pi/4):
    """Relative gamma_5 phase: L gets +i*theta, R gets -i*theta"""
    g5 = np.array([1, 1, -1, -1])
    return psi * np.exp(1j * g5 * theta)

def ax3_branch_coherence(psi, theta=np.pi/4):
    """Shift the global relative tracking phase between L and R bundles"""
    return np.concatenate([psi[0:2], psi[2:4] * np.exp(1j * theta)])

CANDIDATES = [
    ("ax3_parity", ax3_parity),
    ("ax3_cp", ax3_cp),
    ("ax3_g5_phase", ax3_g5_phase),
    ("ax3_branch_coherence", ax3_branch_coherence)
]

def run():
    n_trials = 500
    n_cands = len(CANDIDATES)
    
    print("=" * 80)
    print("RECON: Ax3 Spinor Phase (Inhabiting the S^3 / Weyl Geometry)")
    print(f"Trials: {n_trials}")
    print("=" * 80)
    
    # Matrix of Fubini-Study distances between the outputs of different formulations
    dist_matrix = np.zeros((n_cands, n_cands))
    
    # Also track magnitude of internal change (how much does A(psi) differ from psi?)
    displacement_norms = np.zeros(n_cands)
    
    for trial in range(n_trials):
        rng = np.random.default_rng(200000 + trial)
        psi_in = generate_dirac_state(rng)
        
        psi_outs = [fn(psi_in) for name, fn in CANDIDATES]
        
        for i in range(n_cands):
            displacement_norms[i] += d_overlap(psi_in, psi_outs[i])
            for j in range(i+1, n_cands):
                d = d_overlap(psi_outs[i], psi_outs[j])
                dist_matrix[i,j] += d
                dist_matrix[j,i] += d
                
    dist_matrix /= n_trials
    displacement_norms /= n_trials
    
    print("\n  INTERNAL DISPLACEMENT (Distance from Identity, max=1.0):")
    for i, (name, _) in enumerate(CANDIDATES):
        print(f"    {name:22s} : {displacement_norms[i]:.4f}")
        
    print("\n  INTER-CANDIDATE DISTANCE (0 = identical, 1 = orthogonal, >0.5 = conflicting):")
    names = [c[0].replace("ax3_","") for c in CANDIDATES]
    print(f"    {'':18s} " + " ".join([f"{n:>12s}" for n in names]))
    
    for i in range(n_cands):
        print(f"    {names[i]:18s} ", end="")
        for j in range(n_cands):
            if i == j:
                print(f"{'---':>12s} ", end="")
            else:
                print(f"{dist_matrix[i,j]:12.4f} ", end="")
        print()
        
    # Analysis
    g5_vs_branch = dist_matrix[2,3]
    print(f"\n  ANALYSIS:")
    print(f"  - Parity vs CP gap: {dist_matrix[0,1]:.4f}")
    if g5_vs_branch < 0.1:
        print(f"  - SUCCESS: gamma5 and branch coherence converge at the spinor layer (Dist {g5_vs_branch:.4f})")
    else:
        print(f"  - SEPARATION: gamma5 and branch-coherence are distinct families (Dist {g5_vs_branch:.4f})")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "RECON_AX3_SPINOR_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_trials": n_trials,
        "candidates": [c[0] for c in CANDIDATES],
        "displacement_norms": displacement_norms.tolist(),
        "distance_matrix": dist_matrix.tolist()
    }
    out_file = os.path.join(out_dir, "recon_ax3_spinor.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to {out_file}")

if __name__ == "__main__":
    run()
