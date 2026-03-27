#!/usr/bin/env python3
"""
Corrected Axis Formulations — The Yin-Yang Geometry
=====================================================

Previous failures:
  Ax3: U vs U* (wrong — that's just conjugation, not inverted mirror)
  Ax4: B∘A vs A∘B on endpoints (wrong — composition order is a PROCESS, 
       not visible in endpoints)

Corrected formulations:
  Ax3 = INVERTED MIRROR = CP transformation
    Swap L↔R AND conjugate: ψ_L ↔ ψ_R*
    In yin-yang: flip the symbol AND invert the colors
    On Möbius strip: CW twist vs CCW twist (opposite handedness)
    
  Ax4 = PATH DIRECTION = Berry phase sign
    Same loop on the manifold, traversed CW vs CCW
    NOT visible in ρ(endpoint) — visible in the PHASE ACCUMULATED
    along the path. Need to track the process, not the state.
    
    Operationalization: Berry phase of CW loop vs CCW loop.
    These give opposite geometric phases. The DIFFERENCE is Ax4.

Also: retest Ax3/Ax6 separation with corrected Ax3.
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    torus_coordinates, coherent_state_density,
    berry_phase, fiber_action, hopf_map,
    TORUS_CLIFFORD,
)

sx = np.array([[0,1],[1,0]], dtype=complex)
sy = np.array([[0,-1j],[1j,0]], dtype=complex)
sz = np.array([[1,0],[0,-1]], dtype=complex)


def random_weyl_pair(rng):
    psi_L = rng.normal(size=2) + 1j*rng.normal(size=2)
    psi_L /= np.linalg.norm(psi_L)
    psi_R = rng.normal(size=2) + 1j*rng.normal(size=2)
    psi_R /= np.linalg.norm(psi_R)
    return psi_L, psi_R

def weyl_to_dirac(psi_L, psi_R):
    psi = np.concatenate([psi_L, psi_R])
    return np.outer(psi, np.conj(psi))

def normalized_overlap(A, B):
    nA, nB = np.linalg.norm(A), np.linalg.norm(B)
    if nA < 1e-12 or nB < 1e-12: return 0.0
    return float(abs(np.vdot(A.flatten(), B.flatten())) / (nA * nB))


# ═══════════════════════════════════════════════════════════════════
# CORRECTED AXES
# ═══════════════════════════════════════════════════════════════════

def ax3_inverted_mirror(psi_L, psi_R):
    """Ax3: CP transformation = inverted mirror.
    
    ψ_L ↔ ψ_R*  (swap AND conjugate)
    
    This combines parity (L↔R swap) with charge conjugation (conjugate).
    On the yin-yang: flip it AND swap black/white.
    On a Möbius strip: the operation that turns CW twist into CCW twist.
    
    ρ(ψ_L, ψ_R) − ρ(ψ_R*, ψ_L*)
    """
    rho_original = weyl_to_dirac(psi_L, psi_R)
    rho_CP = weyl_to_dirac(np.conj(psi_R), np.conj(psi_L))
    return rho_original - rho_CP


def ax4_process_direction(psi_L, psi_R):
    """Ax4: Process direction = Berry phase sign.
    
    Apply a sequence of N small rotations CW and CCW around a loop.
    Track the STATE after each step. The Berry phase accumulated
    along the CW path is -γ, along CCW path is +γ.
    
    The displacement is NOT in the final state (which is the same)
    but in the PROCESS TENSOR — the sequence of intermediate states.
    
    We compute the path-integrated overlap matrix:
      P_CW  = Σ_t ρ(t) for CW  traversal
      P_CCW = Σ_t ρ(t) for CCW traversal
    The difference captures what endpoints miss.
    """
    n_steps = 16
    
    # Build a small rotation loop on SU(2)
    # This traces a great circle on the Bloch sphere
    angles_cw = np.linspace(0, 2*np.pi, n_steps, endpoint=False)
    angles_ccw = -angles_cw
    
    H = np.array([[0.3, 0.1+0.2j],[0.1-0.2j, -0.3]], dtype=complex)
    H /= np.linalg.norm(H)
    
    # Build 4×4 Dirac Hamiltonian that acts on both spinors
    H_dirac = np.zeros((4,4), dtype=complex)
    H_dirac[:2,:2] = H
    H_dirac[2:,2:] = H * 0.7  # slightly different on R to break symmetry
    
    psi_full = np.concatenate([psi_L, psi_R])
    
    path_cw = np.zeros((4,4), dtype=complex)
    path_ccw = np.zeros((4,4), dtype=complex)
    
    for t in range(n_steps):
        U_cw = la.expm(-1j * H_dirac * angles_cw[t] * 0.3)
        U_ccw = la.expm(-1j * H_dirac * angles_ccw[t] * 0.3)
        
        psi_cw = U_cw @ psi_full
        psi_ccw = U_ccw @ psi_full
        
        path_cw += np.outer(psi_cw, np.conj(psi_cw))
        path_ccw += np.outer(psi_ccw, np.conj(psi_ccw))
    
    # Normalize by path length
    path_cw /= n_steps
    path_ccw /= n_steps
    
    return path_cw - path_ccw


def ax4_berry_observable(psi_L, psi_R):
    """Ax4 alternative: encode Berry phase as an observable difference.
    
    Build two process matrices that differ by the SIGN of the accumulated
    geometric phase. The process matrix is: χ = Σ_t E_t ⊗ E_t*
    where E_t = U(t)|ψ⟩⟨ψ|U(t)†.
    
    For CW: Berry phase = -Ω/2
    For CCW: Berry phase = +Ω/2
    """
    n_steps = 20
    
    # Create a path on SU(2) that encloses solid angle
    psi_full = np.concatenate([psi_L, psi_R])
    
    # Three rotation axes to create a triangular loop
    axes = [
        np.array([[0.3,0],[0,-0.3]], dtype=complex),   # z
        np.array([[0,0.3],[0.3,0]], dtype=complex),      # x
        np.array([[0,-0.3j],[0.3j,0]], dtype=complex),   # y
    ]
    
    process_cw = np.zeros((4,4), dtype=complex)
    process_ccw = np.zeros((4,4), dtype=complex)
    
    psi_cw = psi_full.copy()
    psi_ccw = psi_full.copy()
    
    for step in range(n_steps):
        # CW: apply axes in order x→y→z
        H_cw = np.zeros((4,4), dtype=complex)
        H_cw[:2,:2] = axes[step % 3]
        U_cw = la.expm(-1j * H_cw * 0.15)
        psi_cw = U_cw @ psi_cw
        psi_cw /= np.linalg.norm(psi_cw)
        
        # CCW: apply axes in reverse order z→y→x
        H_ccw = np.zeros((4,4), dtype=complex)
        H_ccw[:2,:2] = axes[(n_steps - 1 - step) % 3]
        U_ccw = la.expm(-1j * H_ccw * 0.15)
        psi_ccw = U_ccw @ psi_ccw
        psi_ccw /= np.linalg.norm(psi_ccw)
        
        process_cw += np.outer(psi_cw, np.conj(psi_cw))
        process_ccw += np.outer(psi_ccw, np.conj(psi_ccw))
    
    return (process_cw - process_ccw) / n_steps


# ═══════════════════════════════════════════════════════════════════
# OTHER AXES (for comparison)
# ═══════════════════════════════════════════════════════════════════

def ax0(L, R):
    rho = weyl_to_dirac(L, R)
    diag = np.diag(np.diag(rho))
    return (0.2*rho + 0.8*diag) - (0.8*rho + 0.2*diag)

def ax1(L, R):
    rho = weyl_to_dirac(L, R)
    H = np.zeros((4,4), dtype=complex); H[0,0]=0.3; H[1,1]=-0.3
    U = la.expm(-1j*H)
    rho_u = U@rho@U.conj().T
    g=0.3; K0=np.eye(4,dtype=complex); K0[1,1]=np.sqrt(1-g)
    K1=np.zeros((4,4),dtype=complex); K1[0,1]=np.sqrt(g)
    rho_c = K0@rho@K0.conj().T + K1@rho@K1.conj().T
    rho_c /= max(abs(np.trace(rho_c)),1e-12)
    return rho_c - rho_u

def ax2(L, R):
    rho = weyl_to_dirac(L, R)
    P = np.diag([1., 0.7, 1., 0.7]).astype(complex)
    rho_e = P@rho@P.conj().T; rho_e /= max(abs(np.trace(rho_e)),1e-12)
    H = np.zeros((4,4),dtype=complex); H[:2,:2] = sx*0.5
    rho_l = la.expm(-1j*H)@rho@la.expm(1j*H)
    return rho_e - rho_l

def ax6(L, R):
    rho = weyl_to_dirac(L, R)
    A = np.zeros((4,4), dtype=complex)
    A[:2,:2] = np.array([[0.5,0.3+0.4j],[0.1-0.2j,-0.5]])
    A[2:,2:] = np.array([[-0.3,0.2-0.1j],[0.2+0.1j,0.3]])
    A /= np.linalg.norm(A)
    return A@rho - rho@A

def meas(L, R):
    rho = weyl_to_dirac(L, R)
    proj_z = np.diag(np.diag(rho))
    d=4; F=np.zeros((d,d),dtype=complex)
    for i in range(d):
        for j in range(d):
            F[i,j]=np.exp(2j*np.pi*i*j/d)/np.sqrt(d)
    rf=F@rho@F.conj().T; pf=np.diag(np.diag(rf))
    return proj_z - F.conj().T@pf@F


# ═══════════════════════════════════════════════════════════════════
# MAIN TEST
# ═══════════════════════════════════════════════════════════════════

ALL_AXES = [
    ("Ax0:coarse", ax0),
    ("Ax1:dissip", ax1),
    ("Ax2:boundary", ax2),
    ("Ax3:CP_mirror", ax3_inverted_mirror),
    ("Ax4:process_dir", ax4_process_direction),
    ("Ax4b:berry", ax4_berry_observable),
    ("Ax6:action", ax6),
    ("meas_basis", meas),
]

def run():
    n_trials = 200
    n_axes = len(ALL_AXES)
    
    print("=" * 80)
    print("CORRECTED AXIS FORMULATIONS TEST")
    print(f"Ax3=CP (inverted mirror), Ax4=process direction, {n_trials} trials")
    print("=" * 80)
    
    overlap = np.zeros((n_axes, n_axes))
    norms = np.zeros(n_axes)
    
    for trial in range(n_trials):
        rng = np.random.default_rng(trial + 1000000)
        psi_L, psi_R = random_weyl_pair(rng)
        
        disps = [fn(psi_L, psi_R) for _, fn in ALL_AXES]
        
        for i in range(n_axes):
            norms[i] += np.linalg.norm(disps[i])
            for j in range(i+1, n_axes):
                ov = normalized_overlap(disps[i], disps[j])
                overlap[i,j] += ov
                overlap[j,i] += ov
    
    overlap /= n_trials
    norms /= n_trials
    
    # Print
    short = [a[0][:8] for a in ALL_AXES]
    print(f"\n  {'':15s}", end="")
    for s in short: print(f"{s:>9s}", end="")
    print(f"{'norm':>8s}")
    
    for i in range(n_axes):
        name = ALL_AXES[i][0]
        max_off = 0.0
        print(f"  {name:15s}", end="")
        for j in range(n_axes):
            if i==j: print(f"{'·':>9s}", end="")
            else:
                v = overlap[i,j]
                max_off = max(max_off, v)
                m = "!" if v>0.5 else ("~" if v>0.2 else " ")
                print(f"  {v:.3f}{m}", end="")
        status = "✅" if max_off < 0.3 else ("⚠️" if max_off < 0.5 else "❌")
        print(f"  {norms[i]:.4f} {status}")
    
    # Key questions
    print(f"\n{'─'*80}")
    print("  KEY QUESTIONS:")
    
    ax3_idx = 3; ax6_idx = 6
    print(f"  Q1: Ax3 (CP) vs Ax6 (action):  {overlap[ax3_idx,ax6_idx]:.4f}",
          "→ DISTINCT" if overlap[ax3_idx,ax6_idx] < 0.3 else "→ OVERLAPPING")
    
    ax4_idx = 4
    print(f"  Q2: Ax4 (process) norm:         {norms[ax4_idx]:.4f}",
          "→ ALIVE" if norms[ax4_idx] > 0.01 else "→ DEAD")
    
    ax4b_idx = 5
    print(f"  Q3: Ax4b (berry) norm:          {norms[ax4b_idx]:.4f}",
          "→ ALIVE" if norms[ax4b_idx] > 0.01 else "→ DEAD")
    
    print(f"  Q4: Ax3 (CP) vs Ax1 (dissip):   {overlap[ax3_idx,1]:.4f}",
          "→ CLEAN" if overlap[ax3_idx,1] < 0.2 else "→ OVERLAP")
    
    print(f"  Q5: Ax4 vs Ax3 (CP):            {overlap[ax4_idx,ax3_idx]:.4f}",
          "→ DISTINCT" if overlap[ax4_idx,ax3_idx] < 0.3 else "→ OVERLAPPING")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "CORRECTED_AXES_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_trials": n_trials,
        "axes": [a[0] for a in ALL_AXES],
        "overlap": overlap.tolist(),
        "norms": norms.tolist(),
    }
    out_file = os.path.join(out_dir, "corrected_axes_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results written to {out_file}")


if __name__ == "__main__":
    run()
