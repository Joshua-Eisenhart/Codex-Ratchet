#!/usr/bin/env python3
"""
Phenomenological Reconnaissance: Ax4 Process Path Integral
==========================================================
Rule #2: Inhabit the Geometry (Process Paths).
Ax4 (Traversal Direction / Inductive vs Deductive) was dead when 
tested as an instantaneous state property.
We must test it as a sequential loop hysteresis:
    CW Loop:  O1 -> O2 -> O3 -> O4
    CCW Loop: O4 -> O3 -> O2 -> O1

We compare this directly against Ax6 (Action Precedence), which
tests Left-application vs Right-application of the same operator loop:
    Post-multiply (rho A) vs Pre-multiply (A rho).

If the path hysteresis (Ax4) separates from the algebraic side (Ax6), 
we establish them as independent DOFs.
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sx = np.array([[0,1],[1,0]], dtype=complex)
sy = np.array([[0,-1j],[1j,0]], dtype=complex)
sz = np.array([[1,0],[0,-1]], dtype=complex)

def generate_mixed_state(rng, r=0.5):
    """Generate a valid, normalized trace-1 Dirac state density matrix."""
    psi_L = rng.normal(size=2) + 1j*rng.normal(size=2)
    psi_R = rng.normal(size=2) + 1j*rng.normal(size=2)
    psi = np.concatenate([psi_L, psi_R])
    psi /= np.linalg.norm(psi)
    rho_pure = np.outer(psi, np.conj(psi))
    rho = r * rho_pure + (1-r) * np.eye(4, dtype=complex)/4
    return rho

def build_operators(rng):
    """Generate 4 non-commuting Hamiltonians to act as Ti, Fe, Te, Fi."""
    ops = []
    for _ in range(4):
        H = rng.normal(size=(4,4)) + 1j*rng.normal(size=(4,4))
        H = H + H.conj().T
        H /= np.linalg.norm(H, 'fro')
        ops.append(la.expm(-1j * H * 0.4)) # small step unitary
    return ops

def noverlap(A, B):
    """Hilbert-Schmidt overlap for displacements."""
    nA = np.linalg.norm(A, 'fro')
    nB = np.linalg.norm(B, 'fro')
    if nA < 1e-12 or nB < 1e-12: return 0.0
    return float(np.abs(np.trace(A.conj().T @ B)) / (nA * nB))

def run():
    n_trials = 300
    r = 0.5
    
    print("=" * 80)
    print("RECON: Ax4 Process Loop vs Ax6 Precedence")
    print(f"Trials: {n_trials}, r: {r}")
    print("=" * 80)
    
    norm_ax4 = 0.0
    norm_ax6 = 0.0
    overlap_4_6 = 0.0
    
    for trial in range(n_trials):
        rng = np.random.default_rng(300000 + trial)
        rho = generate_mixed_state(rng, r)
        O = build_operators(rng)
        
        # ----------------------------------------------------
        # Ax4: Traversal Direction (CW vs CCW Sequence)
        # Using standard conjugation updates: rho -> U rho U^dag
        # ----------------------------------------------------
        # CW (1 -> 2 -> 3 -> 4)
        rho_cw = rho.copy()
        for k in range(4):
            rho_cw = O[k] @ rho_cw @ O[k].conj().T
            
        # CCW (4 -> 3 -> 2 -> 1)
        rho_ccw = rho.copy()
        for k in reversed(range(4)):
            rho_ccw = O[k] @ rho_ccw @ O[k].conj().T
            
        Disp_Ax4 = rho_cw - rho_ccw
        
        # ----------------------------------------------------
        # Ax6: Action Precedence (Left-action vs Right-action)
        # Apply the sequential product operator to the left vs right
        # ----------------------------------------------------
        # Sequential product operator of the CW loop
        U_total = O[3] @ O[2] @ O[1] @ O[0]
        
        # Pre-multiply vs Post-multiply (A rho vs rho A)
        Disp_Ax6 = (U_total @ rho) - (rho @ U_total.conj().T)
        
        norm_ax4 += np.linalg.norm(Disp_Ax4, 'fro')
        norm_ax6 += np.linalg.norm(Disp_Ax6, 'fro')
        overlap_4_6 += noverlap(Disp_Ax4, Disp_Ax6)
        
    norm_ax4 /= n_trials
    norm_ax6 /= n_trials
    overlap_4_6 /= n_trials
    
    print(f"\n  AX4 (Sequence Hysteresis) Mean Norm : {norm_ax4:.4f}")
    print(f"  AX6 (Left vs Right Action) Mean Norm: {norm_ax6:.4f}")
    print(f"  Overlap (Ax4 vs Ax6)                : {overlap_4_6:.4f}")
    
    if overlap_4_6 < 0.5:
        print("\n  SUCCESS: Ax4 and Ax6 mathematically separate when Ax4 is tested as a full process loop.")
    else:
        print("\n  FAILURE: Ax4 and Ax6 remain entangled even as a process loop.")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "RECON_AX4_PROCESS_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_trials": n_trials,
        "norm_ax4": norm_ax4,
        "norm_ax6": norm_ax6,
        "overlap_4_6": overlap_4_6
    }
    out_file = os.path.join(out_dir, "recon_ax4_process.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to {out_file}")

if __name__ == "__main__":
    run()
