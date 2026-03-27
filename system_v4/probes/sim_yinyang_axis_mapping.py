#!/usr/bin/env python3
"""
Yin-Yang ↔ Axis Mapping on the Clifford Torus
===============================================

The taijitu (yin-yang) IS a stereographic projection of the Clifford torus
on S³. This sim constructs each axis as a geometric operation on the
yin-yang / S³ and tests whether the correspondences hold.

YIN-YANG FEATURE → AXIS HYPOTHESIS:
  Ax0: Black vs white (binary partition) → parity DOF
  Ax1: Black-drop+white-dot vs white-drop+black-dot → interpenetration/coupling
  Ax2: Dots vs teardrops → closed vs open (scale/boundary)
  Ax3: Flip the symbol over (mirror) → L/R chirality
  Ax4: Spin direction (CW vs CCW) → composition order
  Ax5: ??? (= Ax1 in the sim data, since they merged)
  Ax6: ??? (maps to L_z like Ax3 — need to distinguish)

FOR Ax5 and Ax6, let's test candidates:
  Ax5 hypothesis A: The BOUNDARY LINE itself (S-curve) vs the REGIONS it separates
       = form/structure vs content (FGA vs FSA = lines vs waves)
  Ax5 hypothesis B: Same as Ax1 (confirmed by sim: overlap 0.9997)
  
  Ax6 hypothesis A: Which side of the S-curve you stand on
       (black pushes into white vs white pushes into black)
       = which operator acts first = Aρ vs ρA
  Ax6 hypothesis B: The S-curve traced clockwise vs counterclockwise
       (reading direction of the boundary)

GEOMETRIC CONSTRUCTION:
  The yin-yang on S³ is the Clifford torus (η = π/4):
    q(θ₁, θ₂) = (cos(π/4)·e^{iθ₁}, sin(π/4)·e^{iθ₂})
  
  The S-curve is where θ₁ = θ₂ (and θ₁ = θ₂ + π)
  Black region: θ₁ - θ₂ ∈ (0, π)
  White region: θ₁ - θ₂ ∈ (π, 2π)
  Black dot: η → 0 (degenerate torus, inside white region)
  White dot: η → π/2 (degenerate torus, inside black region)
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    torus_coordinates, coherent_state_density,
    hopf_map, density_to_bloch, fiber_action,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
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
# YIN-YANG OPERATIONS ON WEYL PAIRS
# ═══════════════════════════════════════════════════════════════════

def yy_ax0_black_white(psi_L, psi_R):
    """Ax0: Black vs White = binary partition.
    Project onto 'yin' (black) vs 'yang' (white) subspaces.
    On spinors: ψ_L is black side, ψ_R is white side.
    Displacement = ρ_LL - ρ_RR (difference in energy per chirality).
    """
    rho = weyl_to_dirac(psi_L, psi_R)
    # Project: zero out off-diagonal blocks differently
    rho_black = rho.copy(); rho_black[2:,:] = 0; rho_black[:,2:] = 0  # keep LL only
    rho_white = rho.copy(); rho_white[:2,:] = 0; rho_white[:,:2] = 0  # keep RR only
    rho_black /= max(abs(np.trace(rho_black)), 1e-12)
    rho_white /= max(abs(np.trace(rho_white)), 1e-12)
    return rho_black - rho_white

def yy_ax1_interpenetration(psi_L, psi_R):
    """Ax1: Each side contains a seed of the other.
    Black-drop has a white-dot; white-drop has a black-dot.
    = The inter-chirality coherence ρ_LR.
    Displacement: coherent part - incoherent (block-diagonal) part.
    """
    rho = weyl_to_dirac(psi_L, psi_R)
    rho_diag = np.zeros_like(rho)
    rho_diag[:2,:2] = rho[:2,:2]
    rho_diag[2:,2:] = rho[2:,2:]
    return rho - rho_diag  # the off-diagonal blocks = interpenetration

def yy_ax2_dots_vs_drops(psi_L, psi_R):
    """Ax2: Dots vs teardrops = small/closed vs large/open.
    Dots are the degenerate tori (η→0 and η→π/2).
    Teardrops are the bulk regions sweeping across the Clifford torus.
    = concentrated (pure eigenstate) vs spread (mixed/superposed).
    """
    rho = weyl_to_dirac(psi_L, psi_R)
    # "Dot" = eigenstates (sharp/localized)
    evals, evecs = np.linalg.eigh(rho)
    rho_dot = np.outer(evecs[:,-1], np.conj(evecs[:,-1]))  # pure top eigenstate
    # "Teardrop" = uniform mixture
    rho_drop = np.eye(4, dtype=complex) / 4
    return rho_dot - rho_drop

def yy_ax3_flip(psi_L, psi_R):
    """Ax3: Flip the yin-yang over (mirror reflection).
    = complex conjugation: ψ_L → ψ_L*, ψ_R → ψ_R*.
    = Left vs Right Weyl representation.
    """
    return weyl_to_dirac(psi_L, psi_R) - weyl_to_dirac(np.conj(psi_L), np.conj(psi_R))

def yy_ax4_spin_direction(psi_L, psi_R):
    """Ax4: Spin the yin-yang CW vs CCW.
    = rotation direction on the Clifford torus.
    = e^{+iθ} vs e^{-iθ} applied to both spinors.
    """
    theta = 0.4
    rho_cw = weyl_to_dirac(np.exp(1j*theta)*psi_L, np.exp(1j*theta)*psi_R)
    rho_ccw = weyl_to_dirac(np.exp(-1j*theta)*psi_L, np.exp(-1j*theta)*psi_R)
    return rho_cw - rho_ccw

def yy_ax5_scurve_vs_regions(psi_L, psi_R):
    """Ax5 hypothesis: S-curve (boundary/form) vs regions (content).
    The S-curve is where θ₁ = θ₂ on the Clifford torus.
    On spinors: gradient structure (how fast things change)
    vs level structure (what the values are).
    = Derivative vs value = Lines vs Waves = FGA vs FSA.
    
    Operationally: apply a differential-like operator vs an averaging operator.
    """
    rho = weyl_to_dirac(psi_L, psi_R)
    # "Lines" = commutator with a sharp operator (differential)
    A = np.zeros((4,4), dtype=complex)
    A[:2,:2] = sz; A[2:,2:] = -sz  # sharp, alternating
    rho_lines = A @ rho @ A.conj().T
    rho_lines /= max(abs(np.trace(rho_lines)), 1e-12)
    # "Waves" = anti-commutator with smooth operator (integral)
    B = np.ones((4,4), dtype=complex) / 2  # maximally mixed/smooth
    B = (B + B.conj().T)/2
    rho_waves = (B @ rho + rho @ B) / 2
    rho_waves /= max(abs(np.trace(rho_waves)), 1e-12)
    return rho_lines - rho_waves

def yy_ax6_which_side_of_boundary(psi_L, psi_R):
    """Ax6 hypothesis: Which side of the S-curve you read from.
    Same boundary, different perspective:
    "Black pushes into white territory" (A·ρ) 
    vs "white pulls black into its territory" (ρ·A).
    = action side = Aρ vs ρA.
    
    On the Clifford torus: the S-curve is θ₁ = θ₂.
    Standing on the black side: you apply ψ_L operators first.
    Standing on the white side: you apply ψ_R operators first.
    """
    rho = weyl_to_dirac(psi_L, psi_R)
    # Use a chiral operator (different on L vs R blocks)
    A = np.zeros((4,4), dtype=complex)
    A[:2,:2] = np.array([[0.5, 0.3+0.4j],[0.1-0.2j, -0.5]])
    A[2:,2:] = np.array([[-0.3, 0.2-0.1j],[0.2+0.1j, 0.3]])
    A /= np.linalg.norm(A)
    return A @ rho - rho @ A


# ═══════════════════════════════════════════════════════════════════
# WEYL DOFs for comparison
# ═══════════════════════════════════════════════════════════════════

def weyl_phase(L, R):
    t = 0.4
    return weyl_to_dirac(np.exp(1j*t)*L, np.exp(-1j*t)*R) - weyl_to_dirac(np.exp(-1j*t)*L, np.exp(1j*t)*R)

def weyl_Lx(L, R):
    U = la.expm(-1j*sx*0.25); return weyl_to_dirac(U@L,R) - weyl_to_dirac(U.conj().T@L,R)
def weyl_Ly(L, R):
    U = la.expm(-1j*sy*0.25); return weyl_to_dirac(U@L,R) - weyl_to_dirac(U.conj().T@L,R)
def weyl_Lz(L, R):
    U = la.expm(-1j*sz*0.25); return weyl_to_dirac(U@L,R) - weyl_to_dirac(U.conj().T@L,R)
def weyl_Rx(L, R):
    U = la.expm(-1j*sx*0.25); return weyl_to_dirac(L,U@R) - weyl_to_dirac(L,U.conj().T@R)
def weyl_Ry(L, R):
    U = la.expm(-1j*sy*0.25); return weyl_to_dirac(L,U@R) - weyl_to_dirac(L,U.conj().T@R)
def weyl_Rz(L, R):
    U = la.expm(-1j*sz*0.25); return weyl_to_dirac(L,U@R) - weyl_to_dirac(L,U.conj().T@R)
def weyl_parity(L, R):
    return weyl_to_dirac(L,R) - weyl_to_dirac(R,L)

WEYL_DOFS = [
    ("phase", weyl_phase), ("L_x", weyl_Lx), ("L_y", weyl_Ly), ("L_z", weyl_Lz),
    ("R_x", weyl_Rx), ("R_y", weyl_Ry), ("R_z", weyl_Rz), ("parity", weyl_parity),
]

YY_OPS = [
    ("YY0:black/white", yy_ax0_black_white),
    ("YY1:interpenetrate", yy_ax1_interpenetration),
    ("YY2:dots/drops", yy_ax2_dots_vs_drops),
    ("YY3:flip", yy_ax3_flip),
    ("YY4:spin_dir", yy_ax4_spin_direction),
    ("YY5:curve/region", yy_ax5_scurve_vs_regions),
    ("YY6:side_of_bound", yy_ax6_which_side_of_boundary),
]


def run():
    n_trials = 300
    n_yy = len(YY_OPS)
    n_w = len(WEYL_DOFS)
    
    print("=" * 80)
    print("YIN-YANG ↔ WEYL DOF MAPPING")
    print(f"{n_trials} trials")
    print("=" * 80)
    
    # Map each yin-yang operation to Weyl DOFs
    mapping = np.zeros((n_yy, n_w))
    yy_norms = np.zeros(n_yy)
    
    # Also measure yin-yang ops against each other
    yy_overlap = np.zeros((n_yy, n_yy))
    
    for trial in range(n_trials):
        rng = np.random.default_rng(trial + 700000)
        psi_L, psi_R = random_weyl_pair(rng)
        
        yy_disps = [fn(psi_L, psi_R) for _, fn in YY_OPS]
        w_disps = [fn(psi_L, psi_R) for _, fn in WEYL_DOFS]
        
        for i in range(n_yy):
            yy_norms[i] += np.linalg.norm(yy_disps[i])
            for j in range(n_w):
                mapping[i,j] += normalized_overlap(yy_disps[i], w_disps[j])
            for j in range(i+1, n_yy):
                ov = normalized_overlap(yy_disps[i], yy_disps[j])
                yy_overlap[i,j] += ov
                yy_overlap[j,i] += ov
    
    mapping /= n_trials
    yy_norms /= n_trials
    yy_overlap /= n_trials
    
    # Print mapping to Weyl DOFs
    print(f"\n  YIN-YANG → WEYL DOF MAPPING:")
    print(f"  {'':20s}", end="")
    for _, (wn, _) in enumerate(WEYL_DOFS):
        print(f"{wn:>8s}", end="")
    print(f"{'norm':>8s}  {'Best':>8s}")
    
    for i in range(n_yy):
        name = YY_OPS[i][0]
        print(f"  {name:20s}", end="")
        best_j = -1; best_v = 0.0
        for j in range(n_w):
            v = mapping[i,j]
            if v > best_v: best_v = v; best_j = j
            bar = "██" if v > 0.4 else ("▒▒" if v > 0.2 else ("░░" if v > 0.1 else "  "))
            print(f"  {v:.3f}{bar[0]}", end="")
        best = WEYL_DOFS[best_j][0] if yy_norms[i] > 0.01 else "ZERO"
        print(f"  {yy_norms[i]:.4f}  → {best}")
    
    # Print yin-yang internal overlaps
    print(f"\n  YIN-YANG INTERNAL OVERLAP:")
    short_yy = [f"YY{i}" for i in range(n_yy)]
    print(f"  {'':20s}", end="")
    for s in short_yy: print(f"{s:>6s}", end="")
    print()
    
    for i in range(n_yy):
        print(f"  {YY_OPS[i][0]:20s}", end="")
        for j in range(n_yy):
            if i == j: print(f"{'·':>6s}", end="")
            else:
                v = yy_overlap[i,j]
                m = "!" if v > 0.5 else ("~" if v > 0.2 else " ")
                print(f" {v:.2f}{m}", end="")
        print()
    
    # Summary
    print(f"\n{'='*80}")
    print("  YIN-YANG AXIS ROSETTA STONE")
    print(f"{'='*80}")
    
    rosetta = [
        ("Ax0: black vs white", "parity (Z₂)", "Binary partition of state"),
        ("Ax1: seeds of other", "phase + parity", "Inter-chirality coherence"),
        ("Ax2: dots vs drops", "mixed", "Concentrated vs spread"),
        ("Ax3: flip over", "L_z + R_z", "Complex conjugation (chirality)"),
        ("Ax4: spin direction", "global phase", "Rotation direction (vanishes)"),
        ("Ax5: S-curve vs regions", "?", "Boundary form vs content"),
        ("Ax6: which side of S-curve", "L_z", "Action side (Aρ vs ρA)"),
    ]
    
    for yy_feat, dof, meaning in rosetta:
        print(f"  {yy_feat:35s} → {dof:15s} ({meaning})")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "YINYANG_MAPPING_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "mapping": mapping.tolist(),
        "yy_overlap": yy_overlap.tolist(),
        "norms": yy_norms.tolist(),
        "axes_yy": [y[0] for y in YY_OPS],
        "axes_weyl": [w[0] for w in WEYL_DOFS],
    }
    out_file = os.path.join(out_dir, "yinyang_axis_mapping.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results written to {out_file}")


if __name__ == "__main__":
    run()
