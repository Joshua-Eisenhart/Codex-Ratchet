#!/usr/bin/env python3
"""
Weyl Spinor Degrees of Freedom Analysis
==========================================

THE FUNDAMENTAL OBJECTS ARE TWO WEYL SPINORS, NOT TORI.

The nested Hopf tori are derived structure. The engine's root constraints are:
  ψ_L ∈ (1/2, 0) — left Weyl spinor
  ψ_R ∈ (0, 1/2) — right Weyl spinor

Together they form a 4-component Dirac spinor Ψ = (ψ_L, ψ_R).

DOF COUNTING:
  Single Weyl spinor ψ ∈ ℂ²:
    4 real params - 1 norm - 1 phase = 2 real DOF = S² (Bloch sphere)
  
  Pair (ψ_L, ψ_R):
    Each: 2 real DOF on S²
    Plus: relative phase between them = 1 more DOF
    Total: 2 + 2 + 1 = 5 real DOF
    
    OR if we track density matrices:
    ρ_L = |ψ_L⟩⟨ψ_L| ∈ 2×2 (2 DOF on Bloch)
    ρ_R = |ψ_R⟩⟨ψ_R| ∈ 2×2 (2 DOF on Bloch)
    ρ_LR = |ψ_L⟩⟨ψ_R| = inter-chirality coherence (4 real DOF)
    
    Total state space: ρ_L × ρ_R × ρ_LR = 2+2+4 = 8 DOF (before constraints)

THIS SIM:
  1. Represent engine state as (ψ_L, ψ_R) pair
  2. Enumerate ALL independent displacement directions
  3. Map each to physical meaning
  4. Test which ones correspond to known axes
  5. Find the TRUE axis count from first principles
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def normalized_overlap(A, B):
    nA, nB = np.linalg.norm(A), np.linalg.norm(B)
    if nA < 1e-12 or nB < 1e-12: return 0.0
    return float(abs(np.vdot(A.flatten(), B.flatten())) / (nA * nB))


# ═══════════════════════════════════════════════════════════════════
# WEYL SPINOR REPRESENTATION
# ═══════════════════════════════════════════════════════════════════

def random_weyl_pair(rng):
    """Generate a random (ψ_L, ψ_R) Weyl spinor pair.
    Each is a normalized ℂ² spinor.
    """
    psi_L = rng.normal(size=2) + 1j * rng.normal(size=2)
    psi_L /= np.linalg.norm(psi_L)
    psi_R = rng.normal(size=2) + 1j * rng.normal(size=2)
    psi_R /= np.linalg.norm(psi_R)
    return psi_L, psi_R

def weyl_to_density(psi_L, psi_R):
    """Build the full 4×4 Dirac density matrix from Weyl pair.
    
    Ψ = (ψ_L, ψ_R) ∈ ℂ⁴
    ρ = |Ψ⟩⟨Ψ| = [[ρ_LL, ρ_LR], [ρ_RL, ρ_RR]]
    
    The 2×2 blocks encode:
      ρ_LL = |ψ_L⟩⟨ψ_L|  (left-left: same chirality)
      ρ_RR = |ψ_R⟩⟨ψ_R|  (right-right: same chirality)
      ρ_LR = |ψ_L⟩⟨ψ_R|  (left-right: inter-chirality coherence)
      ρ_RL = |ψ_R⟩⟨ψ_L|  (right-left: conjugate)
    """
    psi = np.concatenate([psi_L, psi_R])
    return np.outer(psi, np.conj(psi))

def density_to_components(rho_4x4):
    """Extract the 4 blocks from 4×4 Dirac density matrix."""
    rho_LL = rho_4x4[:2, :2]  # left-left
    rho_LR = rho_4x4[:2, 2:]  # left-right (inter-chirality)
    rho_RL = rho_4x4[2:, :2]  # right-left
    rho_RR = rho_4x4[2:, 2:]  # right-right
    return rho_LL, rho_LR, rho_RL, rho_RR


# ═══════════════════════════════════════════════════════════════════
# DISPLACEMENT GENERATORS ON WEYL PAIRS
# ═══════════════════════════════════════════════════════════════════
# Each displacement acts on the full 4-component Dirac spinor state.
# We enumerate ALL structurally distinct operations.

# Pauli matrices
I2 = np.eye(2, dtype=complex)
sx = np.array([[0,1],[1,0]], dtype=complex)
sy = np.array([[0,-1j],[1j,0]], dtype=complex)
sz = np.array([[1,0],[0,-1]], dtype=complex)

# Dirac gamma matrices (Weyl/chiral basis)
gamma5 = np.block([[I2, np.zeros((2,2))], [np.zeros((2,2)), -I2]])  # chirality


def disp_01_left_phase(psi_L, psi_R):
    """DOF 1: Phase rotation of ψ_L only.
    ψ_L → e^{iθ}ψ_L, ψ_R unchanged.
    Changes: ρ_LR phase (inter-chirality coherence).
    Does NOT change ρ_LL or ρ_RR individually.
    """
    theta = 0.4
    psi_L_plus = np.exp(1j*theta) * psi_L
    psi_L_minus = np.exp(-1j*theta) * psi_L
    return weyl_to_density(psi_L_plus, psi_R) - weyl_to_density(psi_L_minus, psi_R)

def disp_02_right_phase(psi_L, psi_R):
    """DOF 2: Phase rotation of ψ_R only.
    ψ_R → e^{iθ}ψ_R, ψ_L unchanged.
    """
    theta = 0.4
    psi_R_plus = np.exp(1j*theta) * psi_R
    psi_R_minus = np.exp(-1j*theta) * psi_R
    return weyl_to_density(psi_L, psi_R_plus) - weyl_to_density(psi_L, psi_R_minus)

def disp_03_relative_phase(psi_L, psi_R):
    """DOF 3: Relative phase between L and R.
    ψ_L → e^{+iθ}ψ_L, ψ_R → e^{-iθ}ψ_R.
    This is CHIRALITY (γ₅ rotation).
    """
    theta = 0.4
    psi_L_p = np.exp(1j*theta) * psi_L
    psi_R_p = np.exp(-1j*theta) * psi_R
    psi_L_m = np.exp(-1j*theta) * psi_L
    psi_R_m = np.exp(1j*theta) * psi_R
    return weyl_to_density(psi_L_p, psi_R_p) - weyl_to_density(psi_L_m, psi_R_m)

def disp_04_left_sz_rotation(psi_L, psi_R):
    """DOF 4: SU(2) rotation of ψ_L around z-axis.
    ψ_L → exp(-iσ_z·θ/2)ψ_L
    Changes Bloch direction of left spinor.
    """
    theta = 0.5
    U = la.expm(-1j*sz*theta/2)
    return weyl_to_density(U@psi_L, psi_R) - weyl_to_density(U.conj().T@psi_L, psi_R)

def disp_05_left_sx_rotation(psi_L, psi_R):
    """DOF 5: SU(2) rotation of ψ_L around x-axis."""
    theta = 0.5
    U = la.expm(-1j*sx*theta/2)
    return weyl_to_density(U@psi_L, psi_R) - weyl_to_density(U.conj().T@psi_L, psi_R)

def disp_06_left_sy_rotation(psi_L, psi_R):
    """DOF 6: SU(2) rotation of ψ_L around y-axis."""
    theta = 0.5
    U = la.expm(-1j*sy*theta/2)
    return weyl_to_density(U@psi_L, psi_R) - weyl_to_density(U.conj().T@psi_L, psi_R)

def disp_07_right_sz_rotation(psi_L, psi_R):
    """DOF 7: SU(2) rotation of ψ_R around z-axis."""
    theta = 0.5
    U = la.expm(-1j*sz*theta/2)
    return weyl_to_density(psi_L, U@psi_R) - weyl_to_density(psi_L, U.conj().T@psi_R)

def disp_08_right_sx_rotation(psi_L, psi_R):
    """DOF 8: SU(2) rotation of ψ_R around x-axis."""
    theta = 0.5
    U = la.expm(-1j*sx*theta/2)
    return weyl_to_density(psi_L, U@psi_R) - weyl_to_density(psi_L, U.conj().T@psi_R)

def disp_09_right_sy_rotation(psi_L, psi_R):
    """DOF 9: SU(2) rotation of ψ_R around y-axis."""
    theta = 0.5
    U = la.expm(-1j*sy*theta/2)
    return weyl_to_density(psi_L, U@psi_R) - weyl_to_density(psi_L, U.conj().T@psi_R)

def disp_10_correlated_rotation(psi_L, psi_R):
    """DOF 10: SAME rotation applied to both L and R.
    ψ_L → Uψ_L, ψ_R → Uψ_R (vector-like).
    This preserves chirality structure.
    """
    H = sz * 0.3 + sx * 0.2
    U = la.expm(-1j*H)
    return weyl_to_density(U@psi_L, U@psi_R) - weyl_to_density(U.conj().T@psi_L, U.conj().T@psi_R)

def disp_11_opposite_rotation(psi_L, psi_R):
    """DOF 11: OPPOSITE rotation on L and R.
    ψ_L → Uψ_L, ψ_R → U*ψ_R (axial-like / chirality-sensitive).
    This is the Weyl chirality distinction: U vs U*.
    """
    H = sz * 0.3 + sx * 0.2
    U = la.expm(-1j*H)
    U_conj = np.conj(U)
    rho_p = weyl_to_density(U@psi_L, U_conj@psi_R)
    rho_m = weyl_to_density(U.conj().T@psi_L, np.conj(U.conj().T)@psi_R)
    return rho_p - rho_m

def disp_12_amplitude_transfer(psi_L, psi_R):
    """DOF 12: Transfer amplitude from L to R (mass-like coupling).
    In Dirac theory, mass couples L↔R: m·ψ̄ψ = m(ψ_L†ψ_R + ψ_R†ψ_L).
    """
    eps = 0.2
    # Mix L and R
    psi_L_new = np.sqrt(1-eps) * psi_L + np.sqrt(eps) * psi_R
    psi_R_new = np.sqrt(1-eps) * psi_R + np.sqrt(eps) * psi_L
    psi_L_new /= np.linalg.norm(psi_L_new)
    psi_R_new /= np.linalg.norm(psi_R_new)
    # Anti-transfer
    psi_L_anti = np.sqrt(1-eps) * psi_L - np.sqrt(eps) * psi_R
    psi_R_anti = np.sqrt(1-eps) * psi_R - np.sqrt(eps) * psi_L
    psi_L_anti /= np.linalg.norm(psi_L_anti)
    psi_R_anti /= np.linalg.norm(psi_R_anti)
    return weyl_to_density(psi_L_new, psi_R_new) - weyl_to_density(psi_L_anti, psi_R_anti)

def disp_13_parity(psi_L, psi_R):
    """DOF 13: Parity operation P: ψ_L ↔ ψ_R.
    Displacement = ρ(ψ_L, ψ_R) − ρ(ψ_R, ψ_L).
    """
    return weyl_to_density(psi_L, psi_R) - weyl_to_density(psi_R, psi_L)


ALL_DOFS = [
    ("L_phase",        disp_01_left_phase),
    ("R_phase",        disp_02_right_phase),
    ("rel_phase",      disp_03_relative_phase),
    ("L_rot_z",        disp_04_left_sz_rotation),
    ("L_rot_x",        disp_05_left_sx_rotation),
    ("L_rot_y",        disp_06_left_sy_rotation),
    ("R_rot_z",        disp_07_right_sz_rotation),
    ("R_rot_x",        disp_08_right_sx_rotation),
    ("R_rot_y",        disp_09_right_sy_rotation),
    ("corr_rot",       disp_10_correlated_rotation),
    ("opp_rot",        disp_11_opposite_rotation),
    ("amp_transfer",   disp_12_amplitude_transfer),
    ("parity",         disp_13_parity),
]


def run_weyl_dof_analysis():
    n_trials = 300
    n_dofs = len(ALL_DOFS)
    
    print("=" * 80)
    print("WEYL SPINOR DEGREES OF FREEDOM ANALYSIS")
    print(f"13 candidate DOFs, {n_trials} trials")
    print("=" * 80)
    print()
    print("  Root constraints: ψ_L ∈ (1/2,0), ψ_R ∈ (0,1/2)")
    print("  State: Ψ = (ψ_L, ψ_R), ρ = |Ψ⟩⟨Ψ| ∈ 4×4")
    
    overlap_matrix = np.zeros((n_dofs, n_dofs))
    norm_totals = np.zeros(n_dofs)
    
    for trial in range(n_trials):
        rng = np.random.default_rng(trial + 400000)
        psi_L, psi_R = random_weyl_pair(rng)
        
        disps = []
        for _, fn in ALL_DOFS:
            disps.append(fn(psi_L, psi_R))
        
        for i in range(n_dofs):
            norm_totals[i] += np.linalg.norm(disps[i], 'fro')
            for j in range(i+1, n_dofs):
                ov = normalized_overlap(disps[i], disps[j])
                overlap_matrix[i,j] += ov
                overlap_matrix[j,i] += ov
    
    overlap_matrix /= n_trials
    norm_avgs = norm_totals / n_trials
    
    # Print matrix
    short = [d[0][:8] for d in ALL_DOFS]
    print(f"\n  {'':14s}", end="")
    for s in short: print(f"{s:>9s}", end="")
    print(f"{'norm':>8s}")
    
    for i in range(n_dofs):
        name = ALL_DOFS[i][0]
        max_off = 0.0
        print(f"  {name:14s}", end="")
        for j in range(n_dofs):
            if i == j:
                print(f"{'·':>9s}", end="")
            else:
                v = overlap_matrix[i,j]
                max_off = max(max_off, v)
                m = "!" if v > 0.5 else (" " if v < 0.2 else "~")
                print(f"  {v:.3f}{m}", end="")
        trivial = norm_avgs[i] < 0.01
        if trivial:
            status = "☠️ ZERO"
        elif max_off < 0.2:
            status = "✅ CLEAN"
        elif max_off < 0.5:
            status = "⚠️ MARGINAL"
        else:
            status = "❌ OVERLAP"
        print(f"  {norm_avgs[i]:.4f} {status}")
    
    # Independence clustering
    print(f"\n{'─'*80}")
    print("  INDEPENDENCE CLUSTERS (overlap > 0.5):")
    visited = set()
    clusters = []
    for i in range(n_dofs):
        if i in visited or norm_avgs[i] < 0.01: continue
        cluster = [i]
        visited.add(i)
        for j in range(i+1, n_dofs):
            if j in visited or norm_avgs[j] < 0.01: continue
            if overlap_matrix[i,j] > 0.5:
                cluster.append(j)
                visited.add(j)
        clusters.append(cluster)
    
    trivial_count = sum(1 for i in range(n_dofs) if norm_avgs[i] < 0.01)
    
    for ci, cluster in enumerate(clusters):
        names = [ALL_DOFS[i][0] for i in cluster]
        if len(cluster) == 1:
            print(f"    DOF {ci+1}: {names[0]}")
        else:
            print(f"    DOF {ci+1}: {' ≈ '.join(names)}")
    
    print(f"\n  Non-trivial DOFs: {n_dofs - trivial_count}")
    print(f"  Independent clusters: {len(clusters)}")
    print(f"  TOTAL INDEPENDENT DOFs FROM WEYL PAIR: {len(clusters)}")
    
    # Physical meaning mapping
    print(f"\n{'─'*80}")
    print("  PHYSICAL MEANING OF INDEPENDENT DOFs:")
    meaning_map = {
        "L_phase": "Left Weyl U(1) phase",
        "R_phase": "Right Weyl U(1) phase",
        "rel_phase": "Relative L/R phase = chiral angle (γ₅)",
        "L_rot_z": "Left SU(2) rotation (z)",
        "L_rot_x": "Left SU(2) rotation (x)",
        "L_rot_y": "Left SU(2) rotation (y)",
        "R_rot_z": "Right SU(2) rotation (z)",
        "R_rot_x": "Right SU(2) rotation (x)",
        "R_rot_y": "Right SU(2) rotation (y)",
        "corr_rot": "Vector rotation (same on L and R)",
        "opp_rot": "Axial rotation (opposite on L and R)",
        "amp_transfer": "L↔R amplitude mixing (mass coupling)",
        "parity": "P: ψ_L ↔ ψ_R exchange",
    }
    for ci, cluster in enumerate(clusters):
        names = [ALL_DOFS[i][0] for i in cluster]
        meanings = [meaning_map.get(n, "?") for n in names]
        print(f"    DOF {ci+1}: {', '.join(meanings)}")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "WEYL_DOF_ANALYSIS_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_trials": n_trials,
        "dofs": [d[0] for d in ALL_DOFS],
        "overlap_matrix": overlap_matrix.tolist(),
        "norms": norm_avgs.tolist(),
        "n_independent": len(clusters),
        "clusters": [[ALL_DOFS[i][0] for i in c] for c in clusters],
    }
    out_file = os.path.join(out_dir, "weyl_dof_analysis.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run_weyl_dof_analysis()
