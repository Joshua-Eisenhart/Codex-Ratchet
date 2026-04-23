#!/usr/bin/env python3
"""
Geometry Ratcheting: The Full Constraint Chain
===============================================

THE RATCHET ORDER:
  Level 0: Root constraints (F01_FINITUDE, N01_NONCOMMUTATION)
  Level 1: Weyl spinors (ψ_L, ψ_R) — first constrained objects
  Level 2: Density operators — first stable mathematical structure
  Level 3: Hopf/torus geometry — derived organization
  Level 4: Surviving DOFs — what axes actually exist
  Level 5: Engine structure — what axes DO in the engine

THIS SIM tests two things:

PART A: Map named axes (0-6) to Weyl DOFs
  For each named axis, measure overlap with each of the 8 Weyl DOFs.
  This tells us which named axes are "real" (map to exactly one DOF)
  and which are "composite" (map to multiple DOFs).

PART B: Test the ratchet chain
  Does torus geometry correctly derive from Weyl structure?
  What information is LOST at each level of the chain?
  Which DOFs survive the projection from spinor → density → torus?
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: the geometry ratchet chain is explored here by Weyl/Dirac and torus numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "Weyl/Dirac constructions, overlaps, and ratchet-chain numerics"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    torus_coordinates, coherent_state_density,
    hopf_map, density_to_bloch, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
)

# Pauli matrices
I2 = np.eye(2, dtype=complex)
sx = np.array([[0,1],[1,0]], dtype=complex)
sy = np.array([[0,-1j],[1j,0]], dtype=complex)
sz = np.array([[1,0],[0,-1]], dtype=complex)


def random_weyl_pair(rng):
    psi_L = rng.normal(size=2) + 1j*rng.normal(size=2)
    psi_L /= np.linalg.norm(psi_L)
    psi_R = rng.normal(size=2) + 1j*rng.normal(size=2)
    psi_R /= np.linalg.norm(psi_R)
    return psi_L, psi_R

def weyl_to_dirac_density(psi_L, psi_R):
    psi = np.concatenate([psi_L, psi_R])
    return np.outer(psi, np.conj(psi))

def normalized_overlap(A, B):
    nA, nB = np.linalg.norm(A), np.linalg.norm(B)
    if nA < 1e-12 or nB < 1e-12: return 0.0
    return float(abs(np.vdot(A.flatten(), B.flatten())) / (nA * nB))


# ═══════════════════════════════════════════════════════════════════
# WEYL DOF DISPLACEMENTS (the 8 independent from previous sim)
# ═══════════════════════════════════════════════════════════════════

def weyl_dof_phase(psi_L, psi_R):
    """DOF 1: U(1) relative phase"""
    theta = 0.4
    return (weyl_to_dirac_density(np.exp(1j*theta)*psi_L, np.exp(-1j*theta)*psi_R)
           - weyl_to_dirac_density(np.exp(-1j*theta)*psi_L, np.exp(1j*theta)*psi_R))

def weyl_dof_L_rot(psi_L, psi_R, sigma):
    """DOF 2-4: Left SU(2) rotation"""
    theta = 0.5; U = la.expm(-1j*sigma*theta/2)
    return (weyl_to_dirac_density(U@psi_L, psi_R)
           - weyl_to_dirac_density(U.conj().T@psi_L, psi_R))

def weyl_dof_R_rot(psi_L, psi_R, sigma):
    """DOF 5-7: Right SU(2) rotation"""
    theta = 0.5; U = la.expm(-1j*sigma*theta/2)
    return (weyl_to_dirac_density(psi_L, U@psi_R)
           - weyl_to_dirac_density(psi_L, U.conj().T@psi_R))

def weyl_dof_parity(psi_L, psi_R):
    """DOF 8: Parity exchange"""
    return weyl_to_dirac_density(psi_L, psi_R) - weyl_to_dirac_density(psi_R, psi_L)

WEYL_DOFS = [
    ("phase",  lambda L,R: weyl_dof_phase(L,R)),
    ("L_x",    lambda L,R: weyl_dof_L_rot(L,R,sx)),
    ("L_y",    lambda L,R: weyl_dof_L_rot(L,R,sy)),
    ("L_z",    lambda L,R: weyl_dof_L_rot(L,R,sz)),
    ("R_x",    lambda L,R: weyl_dof_R_rot(L,R,sx)),
    ("R_y",    lambda L,R: weyl_dof_R_rot(L,R,sy)),
    ("R_z",    lambda L,R: weyl_dof_R_rot(L,R,sz)),
    ("parity", lambda L,R: weyl_dof_parity(L,R)),
]


# ═══════════════════════════════════════════════════════════════════
# NAMED AXIS DISPLACEMENTS (lifted to 4×4 Dirac space)
# ═══════════════════════════════════════════════════════════════════

def named_ax0(psi_L, psi_R):
    """Ax0: Coarse-graining — partial dephasing of BOTH chiralities"""
    rho = weyl_to_dirac_density(psi_L, psi_R)
    diag = np.diag(np.diag(rho))
    return (0.2*rho + 0.8*diag) - (0.8*rho + 0.2*diag)

def named_ax1(psi_L, psi_R):
    """Ax1: Dissipation — amplitude damping (CPTP) vs unitary on left block"""
    rho = weyl_to_dirac_density(psi_L, psi_R)
    # Unitary on left block
    H = np.zeros((4,4), dtype=complex)
    H[:2,:2] = sz * 0.3
    U = la.expm(-1j*H)
    rho_u = U@rho@U.conj().T
    # CPTP on left block
    gamma = 0.3
    K0 = np.eye(4, dtype=complex)
    K0[1,1] = np.sqrt(1-gamma)
    K1 = np.zeros((4,4), dtype=complex)
    K1[0,1] = np.sqrt(gamma)
    rho_c = K0@rho@K0.conj().T + K1@rho@K1.conj().T
    rho_c /= max(abs(np.trace(rho_c)), 1e-12)
    return rho_c - rho_u

def named_ax2(psi_L, psi_R):
    """Ax2: Boundary — trace-reduce (Eulerian) vs unitary (Lagrangian)"""
    rho = weyl_to_dirac_density(psi_L, psi_R)
    P = np.diag([1.0, 0.7, 1.0, 0.7]).astype(complex)
    rho_e = P@rho@P.conj().T
    rho_e /= max(abs(np.trace(rho_e)), 1e-12)
    H = np.zeros((4,4), dtype=complex)
    H[:2,:2] = sx * 0.5
    rho_l = la.expm(-1j*H)@rho@la.expm(1j*H)
    return rho_e - rho_l

def named_ax3(psi_L, psi_R):
    """Ax3: Chirality — U on L, U* on R (Weyl conjugate)"""
    H_small = np.array([[0.3, 0.1+0.2j],[0.1-0.2j, -0.3]], dtype=complex)
    U_small = la.expm(-1j*H_small)
    # Left Weyl action: U
    psi_L_plus = U_small@psi_L
    psi_R_plus = np.conj(U_small)@psi_R  # Right gets U*
    # Reverse:
    psi_L_minus = U_small.conj().T@psi_L
    psi_R_minus = np.conj(U_small.conj().T)@psi_R
    return weyl_to_dirac_density(psi_L_plus, psi_R_plus) - weyl_to_dirac_density(psi_L_minus, psi_R_minus)

def named_ax4(psi_L, psi_R):
    """Ax4: Composition order — A∘B vs B∘A on the 4×4 state"""
    rho = weyl_to_dirac_density(psi_L, psi_R)
    # Map A: partial dephasing
    def mA(r): return 0.7*r + 0.3*np.diag(np.diag(r))
    # Map B: amplitude damping on left block
    gamma=0.2
    K0 = np.eye(4, dtype=complex); K0[1,1] = np.sqrt(1-gamma)
    K1 = np.zeros((4,4), dtype=complex); K1[0,1] = np.sqrt(gamma)
    def mB(r):
        o = K0@r@K0.conj().T + K1@r@K1.conj().T
        return o/max(abs(np.trace(o)),1e-12)
    return mB(mA(rho)) - mA(mB(rho))

def named_ax6(psi_L, psi_R):
    """Ax6: Action side — A·ρ vs ρ·A"""
    rho = weyl_to_dirac_density(psi_L, psi_R)
    A = np.zeros((4,4), dtype=complex)
    A[:2,:2] = np.array([[0.5, 0.3+0.4j],[0.1-0.2j, -0.5]])
    A[2:,2:] = np.array([[-0.3, 0.2-0.1j],[0.2+0.1j, 0.3]])
    A /= np.linalg.norm(A)
    return A@rho - rho@A

def named_meas(psi_L, psi_R):
    """measurement_basis: z-basis vs Fourier-basis dephasing"""
    rho = weyl_to_dirac_density(psi_L, psi_R)
    proj_z = np.diag(np.diag(rho))
    d = 4
    F = np.zeros((d,d), dtype=complex)
    for i in range(d):
        for j in range(d):
            F[i,j] = np.exp(2j*np.pi*i*j/d)/np.sqrt(d)
    rf = F@rho@F.conj().T
    pf = np.diag(np.diag(rf))
    return proj_z - F.conj().T@pf@F

NAMED_AXES = [
    ("Ax0", named_ax0),
    ("Ax1", named_ax1),
    ("Ax2", named_ax2),
    ("Ax3", named_ax3),
    ("Ax4", named_ax4),
    ("Ax6", named_ax6),
    ("meas", named_meas),
]


# ═══════════════════════════════════════════════════════════════════
# PART A: MAP NAMED AXES → WEYL DOFS
# ═══════════════════════════════════════════════════════════════════

def part_a_mapping():
    n_trials = 300
    n_weyl = len(WEYL_DOFS)
    n_named = len(NAMED_AXES)
    
    print("=" * 80)
    print("PART A: MAP NAMED AXES → WEYL DOFs")
    print(f"{n_trials} trials, {n_named} named axes × {n_weyl} Weyl DOFs")
    print("=" * 80)
    
    mapping = np.zeros((n_named, n_weyl))
    named_norms = np.zeros(n_named)
    
    for trial in range(n_trials):
        rng = np.random.default_rng(trial + 500000)
        psi_L, psi_R = random_weyl_pair(rng)
        
        weyl_disps = [fn(psi_L, psi_R) for _, fn in WEYL_DOFS]
        named_disps = [fn(psi_L, psi_R) for _, fn in NAMED_AXES]
        
        for i in range(n_named):
            named_norms[i] += np.linalg.norm(named_disps[i])
            for j in range(n_weyl):
                mapping[i,j] += normalized_overlap(named_disps[i], weyl_disps[j])
    
    mapping /= n_trials
    named_norms /= n_trials
    
    # Print mapping table
    weyl_short = [d[0] for d in WEYL_DOFS]
    print(f"\n  {'Named':8s}", end="")
    for ws in weyl_short: print(f"{ws:>8s}", end="")
    print(f"{'norm':>8s}  {'Best DOF':>10s}")
    
    results = {}
    for i in range(n_named):
        name = NAMED_AXES[i][0]
        print(f"  {name:8s}", end="")
        best_j = -1; best_v = 0.0
        for j in range(n_weyl):
            v = mapping[i,j]
            if v > best_v: best_v = v; best_j = j
            m = "██" if v > 0.4 else ("▒▒" if v > 0.2 else "░░" if v > 0.1 else "  ")
            print(f"  {v:.3f}{m[0]}", end="")
        
        best_name = WEYL_DOFS[best_j][0] if best_j >= 0 else "?"
        trivial = named_norms[i] < 0.01
        label = "ZERO" if trivial else best_name
        print(f"  {named_norms[i]:.4f}  → {label}")
        
        results[name] = {
            "best_dof": label,
            "best_overlap": round(best_v, 4),
            "norm": round(float(named_norms[i]), 4),
            "all_overlaps": {WEYL_DOFS[j][0]: round(float(mapping[i,j]),4) for j in range(n_weyl)},
        }
    
    return results


# ═══════════════════════════════════════════════════════════════════
# PART B: RATCHET CHAIN — INFORMATION LOSS AT EACH LEVEL
# ═══════════════════════════════════════════════════════════════════

def part_b_ratchet_chain():
    n_trials = 300
    
    print(f"\n{'='*80}")
    print("PART B: RATCHET CHAIN — INFORMATION LOSS PER LEVEL")
    print(f"{'='*80}")
    print()
    print("  Level 0: Root constraints (F01, N01)")
    print("  Level 1: Weyl spinors (ψ_L, ψ_R) ∈ ℂ² × ℂ² — 8 real params")
    print("  Level 2: Dirac density ρ = |Ψ⟩⟨Ψ| ∈ 4×4 — 15 real params (Hermitian, trace 1)")
    print("  Level 3: Left density ρ_L = |ψ_L⟩⟨ψ_L| ∈ 2×2 — 3 params (Bloch vector)")
    print("  Level 4: Torus coords (η, θ₁, θ₂) — 3 params")
    print("  Level 5: Bloch point on S² — 2 params")
    
    # For each Weyl DOF, track its visibility at each level
    levels = ["Dirac 4×4", "ρ_L 2×2", "ρ_R 2×2", "Bloch_L S²", "Bloch_R S²"]
    
    visibility = {d[0]: {l: 0.0 for l in levels} for d in WEYL_DOFS}
    
    for trial in range(n_trials):
        rng = np.random.default_rng(trial + 600000)
        psi_L, psi_R = random_weyl_pair(rng)
        
        for dof_name, dof_fn in WEYL_DOFS:
            disp_4x4 = dof_fn(psi_L, psi_R)
            
            # Level 2: Dirac 4×4 (always visible by construction)
            visibility[dof_name]["Dirac 4×4"] += np.linalg.norm(disp_4x4, 'fro')
            
            # Level 3: Left block only
            disp_LL = disp_4x4[:2, :2]
            visibility[dof_name]["ρ_L 2×2"] += np.linalg.norm(disp_LL, 'fro')
            
            # Level 3: Right block only
            disp_RR = disp_4x4[2:, 2:]
            visibility[dof_name]["ρ_R 2×2"] += np.linalg.norm(disp_RR, 'fro')
            
            # Level 4: Bloch vector (left)
            rho_L_base = np.outer(psi_L, np.conj(psi_L))
            rho_L_disp = rho_L_base + 0.01 * disp_LL  # small perturbation
            bloch_base = density_to_bloch(rho_L_base)
            # Ensure perturbed state is valid
            rho_L_disp_valid = (rho_L_disp + rho_L_disp.conj().T)/2
            ev, evc = np.linalg.eigh(rho_L_disp_valid)
            ev = np.maximum(ev, 0)
            rho_L_disp_valid = evc@np.diag(ev)@evc.conj().T
            tr = np.trace(rho_L_disp_valid)
            if abs(tr) > 1e-12:
                rho_L_disp_valid /= tr
            bloch_disp = density_to_bloch(rho_L_disp_valid)
            visibility[dof_name]["Bloch_L S²"] += np.linalg.norm(bloch_disp - bloch_base)
            
            # Same for right
            rho_R_base = np.outer(psi_R, np.conj(psi_R))
            rho_R_disp = rho_R_base + 0.01 * disp_RR
            bloch_base_R = density_to_bloch(rho_R_base)
            rho_R_disp_valid = (rho_R_disp + rho_R_disp.conj().T)/2
            ev, evc = np.linalg.eigh(rho_R_disp_valid)
            ev = np.maximum(ev, 0)
            rho_R_disp_valid = evc@np.diag(ev)@evc.conj().T
            tr = np.trace(rho_R_disp_valid)
            if abs(tr) > 1e-12:
                rho_R_disp_valid /= tr
            bloch_disp_R = density_to_bloch(rho_R_disp_valid)
            visibility[dof_name]["Bloch_R S²"] += np.linalg.norm(bloch_disp_R - bloch_base_R)
    
    # Normalize
    for dn in visibility:
        for ln in visibility[dn]:
            visibility[dn][ln] /= n_trials
    
    # Print
    print(f"\n  {'DOF':10s}", end="")
    for l in levels: print(f"{l:>12s}", end="")
    print(f"  {'Lost at':>12s}")
    
    for dof_name, _ in WEYL_DOFS:
        v = visibility[dof_name]
        print(f"  {dof_name:10s}", end="")
        for l in levels:
            val = v[l]
            bar = "████" if val > 0.1 else ("▒▒▒▒" if val > 0.01 else ("░░░░" if val > 0.001 else "    "))
            print(f"  {val:8.4f}{bar[:2]}", end="")
        
        # Determine where it's lost
        if v["Dirac 4×4"] < 0.01:
            lost = "EVERYWHERE"
        elif v["ρ_L 2×2"] < 0.01 and v["ρ_R 2×2"] < 0.01:
            lost = "ρ → ρ_L/R"
        elif v["Bloch_L S²"] < 0.001 and v["Bloch_R S²"] < 0.001:
            lost = "ρ → Bloch"
        else:
            lost = "survives"
        print(f"  {lost}")
    
    return visibility


# ═══════════════════════════════════════════════════════════════════

def main():
    mapping_results = part_a_mapping()
    visibility_results = part_b_ratchet_chain()
    
    # Summary
    print(f"\n{'='*80}")
    print("  GEOMETRY RATCHETING SUMMARY")
    print(f"{'='*80}")
    print()
    print("  THE CONSTRAINT CHAIN:")
    print("    F01 + N01 → Weyl spinors (ψ_L, ψ_R)")
    print("    → 8 independent DOFs: SU(2)_L × SU(2)_R × U(1) × Z₂")
    print()
    print("  NAMED AXIS MAPPING:")
    for name, data in mapping_results.items():
        print(f"    {name:8s} → {data['best_dof']:10s} (overlap {data['best_overlap']:.3f}, norm {data['norm']:.4f})")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "GEOMETRY_RATCHET_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "mapping": mapping_results,
        "visibility": {k: {l: round(v,6) for l,v in vis.items()} 
                       for k, vis in visibility_results.items()},
    }
    out_file = os.path.join(out_dir, "geometry_ratchet_chain.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results written to {out_file}")


if __name__ == "__main__":
    main()
