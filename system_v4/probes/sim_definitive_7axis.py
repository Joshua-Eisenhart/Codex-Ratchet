#!/usr/bin/env python3
"""
7-Axis Exploratory Validation on Mixed States
==============================================

Exploratory test: all 7 axes with corrected formulations, tested on
mixed states at varying entropy. Axis formulations are still candidate
operationalizations, not locked canon.

NOTE: v2 fixes the normalization bug where concatenated Dirac spinor
had norm sqrt(2) instead of 1, giving trace-2 density matrices.
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


def make_mixed_dirac(r, rng):
    """Mixed state in 4×4 Dirac space at Bloch radius r.
    
    FIXED (v2): Concatenated Dirac spinor is renormalized to unit norm
    before forming ρ_pure. Previously had ||ψ|| = √2 giving Tr(ρ) = 2.
    """
    psi_L = rng.normal(size=2) + 1j*rng.normal(size=2); psi_L /= np.linalg.norm(psi_L)
    psi_R = rng.normal(size=2) + 1j*rng.normal(size=2); psi_R /= np.linalg.norm(psi_R)
    psi = np.concatenate([psi_L, psi_R])
    psi /= np.linalg.norm(psi)  # CRITICAL: normalize the 4-vector
    rho_pure = np.outer(psi, np.conj(psi))  # now Tr(rho_pure) = 1
    rho_mixed = np.eye(4, dtype=complex) / 4
    rho = r * rho_pure + (1-r) * rho_mixed  # Tr = r·1 + (1-r)·1 = 1 ✓
    return rho, psi_L, psi_R

def ensure_valid(rho):
    rho = (rho+rho.conj().T)/2
    ev, evc = np.linalg.eigh(rho)
    ev = np.maximum(ev, 0)
    rho = evc@np.diag(ev)@evc.conj().T
    tr = np.trace(rho)
    if abs(tr) > 1e-12: rho /= tr
    return rho

def normalized_overlap(A, B):
    nA, nB = np.linalg.norm(A,'fro'), np.linalg.norm(B,'fro')
    if nA < 1e-12 or nB < 1e-12: return 0.0
    return float(abs(np.trace(A.conj().T@B))/(nA*nB))


# ═══════════════════════════════════════════════════════════════════
# DEFINITIVE AXIS FORMULATIONS (CORRECTED)
# ═══════════════════════════════════════════════════════════════════

def ax0_coarsegraining(rho, pL, pR):
    """Ax0: Black vs white = binary partition = coarse vs fine."""
    diag = np.diag(np.diag(rho))
    return (0.2*rho + 0.8*diag) - (0.8*rho + 0.2*diag)

def ax1_dissipation(rho, pL, pR):
    """Ax1: Open vs closed channel."""
    H = np.zeros((4,4),dtype=complex); H[0,0]=0.3; H[1,1]=-0.3
    U = la.expm(-1j*H); rho_u = U@rho@U.conj().T
    g=0.3; K0=np.eye(4,dtype=complex); K0[1,1]=np.sqrt(1-g)
    K1=np.zeros((4,4),dtype=complex); K1[0,1]=np.sqrt(g)
    rho_c = K0@rho@K0.conj().T + K1@rho@K1.conj().T
    rho_c /= max(abs(np.trace(rho_c)),1e-12)
    return rho_c - rho_u

def ax2_boundary(rho, pL, pR):
    """Ax2: Dots vs teardrops = concentrated vs spread."""
    P = np.diag([1., 0.7, 1., 0.7]).astype(complex)
    rho_e = P@rho@P.conj().T; rho_e /= max(abs(np.trace(rho_e)),1e-12)
    H = np.zeros((4,4),dtype=complex); H[:2,:2] = sx*0.5
    rho_l = la.expm(-1j*H)@rho@la.expm(1j*H)
    return rho_e - rho_l

def ax3_CP_mirror(rho, pL, pR):
    """Ax3: Inverted mirror = CP transformation.
    Swap L↔R AND conjugate: ρ(ψ_L,ψ_R) - ρ(ψ_R*,ψ_L*).
    On mixed states: apply the CP superoperator.
    """
    # CP operator: swap blocks AND conjugate
    # P swaps the two 2×2 blocks, C conjugates
    P_swap = np.zeros((4,4), dtype=complex)
    P_swap[0,2] = 1; P_swap[1,3] = 1; P_swap[2,0] = 1; P_swap[3,1] = 1
    rho_P = P_swap @ rho @ P_swap.conj().T  # parity
    rho_CP = np.conj(rho_P)  # charge conjugation
    return rho - rho_CP

def ax4_process(rho, pL, pR):
    """Ax4: Process direction = CW vs CCW path integration."""
    n_steps = 16
    H_dirac = np.zeros((4,4), dtype=complex)
    H_dirac[:2,:2] = np.array([[0.3,0.1+0.2j],[0.1-0.2j,-0.3]])
    H_dirac[2:,2:] = np.array([[-0.2,0.15-0.1j],[0.15+0.1j,0.2]])
    H_dirac /= np.linalg.norm(H_dirac)
    
    angles = np.linspace(0, 2*np.pi, n_steps, endpoint=False)
    path_cw = np.zeros((4,4), dtype=complex)
    path_ccw = np.zeros((4,4), dtype=complex)
    
    for t in range(n_steps):
        U_cw = la.expm(-1j * H_dirac * angles[t] * 0.3)
        U_ccw = la.expm(-1j * H_dirac * (-angles[t]) * 0.3)
        path_cw += U_cw @ rho @ U_cw.conj().T
        path_ccw += U_ccw @ rho @ U_ccw.conj().T
    
    return (path_cw - path_ccw) / n_steps

def ax5_curvature(rho, pL, pR):
    """Ax5: S-curve curvature = FGA/FSA = trajectory bending."""
    H_curved = np.zeros((4,4), dtype=complex)
    H_curved[:2,:2] = np.array([[0.3,0.2+0.1j],[0.2-0.1j,-0.3]])
    H_curved[2:,2:] = np.array([[-0.1,0.3-0.2j],[0.3+0.2j,0.1]])
    H_curved /= np.linalg.norm(H_curved)
    
    eps = 0.2
    U1 = la.expm(-1j*H_curved*eps); U2 = la.expm(-1j*H_curved*2*eps)
    rho_eps = U1@rho@U1.conj().T; rho_2eps = U2@rho@U2.conj().T
    curv_high = rho_2eps - 2*rho_eps + rho
    
    diag = np.diag(np.diag(rho))
    rho_eps_l = (1-eps)*rho + eps*diag
    rho_2eps_l = (1-2*eps)*rho + 2*eps*diag
    curv_low = rho_2eps_l - 2*rho_eps_l + rho
    return curv_high - curv_low

def ax6_action_side(rho, pL, pR):
    """Ax6: Which fish chases which = Aρ vs ρA."""
    A = np.zeros((4,4), dtype=complex)
    A[:2,:2] = np.array([[0.5,0.3+0.4j],[0.1-0.2j,-0.5]])
    A[2:,2:] = np.array([[-0.3,0.2-0.1j],[0.2+0.1j,0.3]])
    A /= np.linalg.norm(A)
    return A@rho - rho@A


ALL_AXES = [
    ("Ax0", ax0_coarsegraining),
    ("Ax1", ax1_dissipation),
    ("Ax2", ax2_boundary),
    ("Ax3", ax3_CP_mirror),
    ("Ax4", ax4_process),
    ("Ax5", ax5_curvature),
    ("Ax6", ax6_action_side),
]


def run():
    n_trials = 200
    n_axes = 7
    r_values = [1.0, 0.7, 0.5, 0.3, 0.1]
    
    print("=" * 80)
    print("7-AXIS EXPLORATORY VALIDATION ON MIXED STATES (v2 — normalized)")
    print(f"Candidate formulations, {n_trials} trials per condition")
    print("=" * 80)
    
    all_results = {}
    
    for r in r_values:
        print(f"\n{'─'*80}")
        print(f"  Bloch radius r = {r}  ({'PURE' if r==1.0 else f'MIXED (entropy ~ {1-r:.1f})'})")
        print(f"{'─'*80}")
        
        overlap = np.zeros((n_axes, n_axes))
        norms = np.zeros(n_axes)
        
        for trial in range(n_trials):
            rng = np.random.default_rng(trial + 1100000 + int(r*10000))
            rho, pL, pR = make_mixed_dirac(r, rng)
            
            disps = [fn(rho, pL, pR) for _, fn in ALL_AXES]
            
            for i in range(n_axes):
                norms[i] += np.linalg.norm(disps[i], 'fro')
                for j in range(i+1, n_axes):
                    ov = normalized_overlap(disps[i], disps[j])
                    overlap[i,j] += ov
                    overlap[j,i] += ov
        
        overlap /= n_trials
        norms /= n_trials
        
        names = [a[0] for a in ALL_AXES]
        print(f"  {'':6s}", end="")
        for n in names: print(f"{n:>7s}", end="")
        print(f"{'norm':>8s} {'max_ov':>8s}")
        
        for i in range(n_axes):
            print(f"  {names[i]:6s}", end="")
            max_off = 0.0
            for j in range(n_axes):
                if i==j: print(f"{'·':>7s}", end="")
                else:
                    v = overlap[i,j]
                    max_off = max(max_off, v)
                    print(f"  {v:.3f}", end="")
            status = "✅" if max_off < 0.3 else ("⚠️" if max_off < 0.5 else "❌")
            print(f"  {norms[i]:.4f} {max_off:.3f} {status}")
        
        all_results[f"r={r}"] = {
            "overlap": overlap.tolist(),
            "norms": norms.tolist(),
            "max_overlaps": [float(max(overlap[i,j] for j in range(n_axes) if j!=i)) for i in range(n_axes)],
        }
    
    # Summary table
    print(f"\n{'='*80}")
    print("  SUMMARY: Max overlap per axis across entropy levels")
    print(f"{'='*80}")
    print(f"  {'':6s}", end="")
    for r in r_values: print(f"{'r='+str(r):>8s}", end="")
    print(f"  {'Verdict':>10s}")
    
    for i in range(n_axes):
        name = ALL_AXES[i][0]
        print(f"  {name:6s}", end="")
        worst = 0.0
        for r in r_values:
            mo = all_results[f"r={r}"]["max_overlaps"][i]
            worst = max(worst, mo)
            print(f"  {mo:6.3f}", end="")
        v = "✅ CLEAN" if worst < 0.3 else ("⚠️ MARGINAL" if worst < 0.5 else "❌ DIRTY")
        print(f"  {v}")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "DEFINITIVE_7AXIS_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_trials": n_trials,
        "axes": [a[0] for a in ALL_AXES],
        "r_values": r_values,
        "results": all_results,
    }
    out_file = os.path.join(out_dir, "definitive_7axis_validation.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results written to {out_file}")


if __name__ == "__main__":
    run()
