#!/usr/bin/env python3
"""
Axes 7-12 Audit: Redundancy Check + New Candidate Mapping
============================================================

Tests whether axes 7-12 (commutator products) are:
  1. Actually independent (or redundant given Ax1≈Ax5 merge)
  2. The same as our 2 new unnamed candidates (measurement_basis, non_markovianity)

AXES 7-12 CLAIMED CONSTRUCTION:
  A7  = [A1, A3]  — coupling × chirality
  A8  = [A1, A6]  — coupling × action side  (alt: [A4, A6])
  A9  = [A3, A6]  — chirality × action side  ← DANGER: Ax3/Ax6 conflate!
  A10 = [A4, A6]  — composition × action side (alt: [A1, A4])
  A11 = [A2, A6]  — boundary × action side   (alt: [A1, A2])
  A12 = [A1, A5]  — coupling × algebra       ← DANGER: Ax1≈Ax5!

KEY QUESTIONS:
  Q1: Does A12 collapse (since Ax1≈Ax5)?
  Q2: Is A9 meaningful (since Ax3/Ax6 conflate with old math)?
  Q3: Does measurement_basis ≈ any of A7-A12?
  Q4: Does non_markovianity ≈ any of A7-A12?
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from proto_ratchet_sim_runner import make_random_density_matrix
except ImportError:
    def make_random_density_matrix(d):
        A = np.random.randn(d,d)+1j*np.random.randn(d,d)
        rho = A@A.conj().T; return rho/np.trace(rho)

def ensure_valid(rho):
    rho = (rho+rho.conj().T)/2
    ev,evc = np.linalg.eigh(rho); ev=np.maximum(ev,0)
    rho = evc@np.diag(ev)@evc.conj().T
    tr = np.trace(rho)
    if abs(tr)>1e-12: rho/=tr
    return rho

def normalized_overlap(A,B):
    nA,nB = np.linalg.norm(A,'fro'), np.linalg.norm(B,'fro')
    if nA<1e-12 or nB<1e-12: return 0.0
    return float(abs(np.trace(A.conj().T@B))/(nA*nB))


# ═══════════════════════════════════════════════════════════════════
# BASE AXIS DISPLACEMENTS (using corrected formulations)
# ═══════════════════════════════════════════════════════════════════

def disp_ax0(rho,d):
    diag=np.diag(np.diag(rho)); return (0.2*rho+0.8*diag)-(0.8*rho+0.2*diag)

def disp_ax1(rho,d):
    H=np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    U=la.expm(-1j*H*0.3); rho_u=U@rho@U.conj().T
    L=np.zeros((d,d),dtype=complex)
    for k in range(d-1): L[k,k+1]=0.3
    lind=L@rho@L.conj().T-0.5*(L.conj().T@L@rho+rho@L.conj().T@L)
    return ensure_valid(rho+lind*0.3)-rho_u

def disp_ax2(rho,d):
    P=np.eye(d,dtype=complex); P[d-1,d-1]=0.7
    H=np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    return ensure_valid(P@rho@P.conj().T)-la.expm(-1j*H*0.5)@rho@la.expm(1j*H*0.5)

def disp_ax3(rho,d):
    theta=0.4; pp=np.exp(1j*theta)*np.eye(d); pm=np.exp(-1j*theta)*np.eye(d)
    return (pp@rho@pp.conj().T)-(pm@rho@pm.conj().T)

def disp_ax4(rho,d):
    def mA(r): return 0.7*r+0.3*np.diag(np.diag(r))
    g=0.2; K0=np.eye(d,dtype=complex); K1=np.zeros((d,d),dtype=complex)
    for k in range(1,d): K0[k,k]=np.sqrt(1-g); K1[k-1,k]=np.sqrt(g)
    def mB(r):
        o=K0@r@K0.conj().T+K1@r@K1.conj().T; return o/max(abs(np.trace(o)),1e-12)
    return mB(mA(rho))-mA(mB(rho))

def disp_ax5(rho,d):
    """Same as Ax1 but different seed internals for comparison"""
    L=np.zeros((d,d),dtype=complex)
    for k in range(d-1): L[k,k+1]=0.4
    lind=L@rho@L.conj().T-0.5*(L.conj().T@L@rho+rho@L.conj().T@L)
    rho_fga=ensure_valid(rho+lind*0.3)
    H=np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    rho_fsa=la.expm(-1j*H*0.3)@rho@la.expm(1j*H*0.3)
    return rho_fga-rho_fsa

def disp_ax6(rho,d):
    A=np.random.randn(d,d)+1j*np.random.randn(d,d); A/=np.linalg.norm(A)
    return A@rho-rho@A

BASE_AXES = [
    ("A0",disp_ax0),("A1",disp_ax1),("A2",disp_ax2),
    ("A3",disp_ax3),("A4",disp_ax4),("A5",disp_ax5),("A6",disp_ax6),
]


# ═══════════════════════════════════════════════════════════════════
# AXES 7-12: COMMUTATOR PRODUCTS IN STATE SPACE
# ═══════════════════════════════════════════════════════════════════

def commutator_disp(fn_i, fn_j, rho, d):
    """
    [Ai, Aj](ρ) = Ai(Aj(ρ)) - Aj(Ai(ρ))
    The commutator in the space of displacement operators.
    """
    np.random.seed(np.random.randint(0,99999))
    dj = fn_j(rho, d)  # displacement from Aj
    np.random.seed(np.random.randint(0,99999))
    di = fn_i(rho, d)  # displacement from Ai
    
    # Apply Ai to (ρ + dj) and Aj to (ρ + di)
    rho_j = ensure_valid(rho + 0.1*dj)
    rho_i = ensure_valid(rho + 0.1*di)
    
    np.random.seed(np.random.randint(0,99999))
    di_after_j = fn_i(rho_j, d)
    np.random.seed(np.random.randint(0,99999))
    dj_after_i = fn_j(rho_i, d)
    
    return di_after_j - dj_after_i


# ═══════════════════════════════════════════════════════════════════
# NEW CANDIDATES
# ═══════════════════════════════════════════════════════════════════

def measurement_basis(rho, d):
    proj_z = np.diag(np.diag(rho))
    F = np.zeros((d,d),dtype=complex)
    for i in range(d):
        for j in range(d):
            F[i,j] = np.exp(2j*np.pi*i*j/d)/np.sqrt(d)
    rf=F@rho@F.conj().T; pf=np.diag(np.diag(rf))
    return proj_z - F.conj().T@pf@F

def non_markovianity(rho, d):
    L=np.zeros((d,d),dtype=complex)
    for k in range(d-1): L[k,k+1]=0.3
    lind=L@rho@L.conj().T-0.5*(L.conj().T@L@rho+rho@L.conj().T@L)
    rho_markov=ensure_valid(rho+lind*0.3)
    rho_step1=ensure_valid(rho-lind*0.15)
    lind2=L@rho_step1@L.conj().T-0.5*(L.conj().T@L@rho_step1+rho_step1@L.conj().T@L)
    return rho_markov - ensure_valid(rho_step1+lind2*0.45)


# ═══════════════════════════════════════════════════════════════════
# MAIN TEST
# ═══════════════════════════════════════════════════════════════════

def run_axis_7_12_audit():
    d = 8
    n_trials = 100
    
    print("=" * 70)
    print("AXES 7-12 AUDIT: Redundancy + New Candidate Mapping")
    print(f"d={d}, {n_trials} trials")
    print("=" * 70)
    
    # Define the 6 commutator axes per the MASTER spec
    comm_defs = [
        ("A7=[A1,A3]", disp_ax1, disp_ax3),
        ("A8=[A1,A6]", disp_ax1, disp_ax6),
        ("A9=[A3,A6]", disp_ax3, disp_ax6),
        ("A10=[A4,A6]", disp_ax4, disp_ax6),
        ("A11=[A2,A6]", disp_ax2, disp_ax6),
        ("A12=[A1,A5]", disp_ax1, disp_ax5),
    ]
    
    # Step 1: Check if each commutator produces non-trivial displacement
    print("\n  STEP 1: Commutator norms (is it even non-zero?)")
    comm_norms = {}
    for cname, fn_i, fn_j in comm_defs:
        total_norm = 0.0
        for trial in range(n_trials):
            np.random.seed(trial + 90000)
            rho = make_random_density_matrix(d)
            np.random.seed(trial + 90000)
            cd = commutator_disp(fn_i, fn_j, rho, d)
            total_norm += np.linalg.norm(cd, 'fro')
        avg_norm = total_norm / n_trials
        comm_norms[cname] = avg_norm
        status = "✅ nontrivial" if avg_norm > 0.01 else "❌ TRIVIAL (collapses)"
        print(f"    {cname:20s}: avg_norm = {avg_norm:.6f}  {status}")
    
    # Step 2: Overlap between commutator axes (pairwise)
    print("\n  STEP 2: Pairwise overlap between commutator axes")
    comm_names = [c[0] for c in comm_defs]
    n_comm = len(comm_defs)
    comm_overlap = np.zeros((n_comm, n_comm))
    
    for trial in range(n_trials):
        np.random.seed(trial + 91000)
        rho = make_random_density_matrix(d)
        disps = []
        for cname, fn_i, fn_j in comm_defs:
            np.random.seed(trial + 91000)
            disps.append(commutator_disp(fn_i, fn_j, rho, d))
        
        for i in range(n_comm):
            for j in range(i+1, n_comm):
                ov = normalized_overlap(disps[i], disps[j])
                comm_overlap[i,j] += ov
                comm_overlap[j,i] += ov
    
    comm_overlap /= n_trials
    
    print(f"    {'':20s}", end="")
    for cn in comm_names:
        print(f"{cn[-8:]:>10s}", end="")
    print()
    for i in range(n_comm):
        print(f"    {comm_names[i]:20s}", end="")
        for j in range(n_comm):
            if i==j: print(f"{'---':>10s}", end="")
            else:
                v = comm_overlap[i,j]
                m = "❌" if v > 0.5 else ("⚠" if v > 0.2 else "✅")
                print(f" {v:.3f}{m}", end="")
        print()
    
    # Step 3: New candidates vs commutator axes
    print("\n  STEP 3: New candidates vs commutator axes")
    new_cands = [("measurement_basis", measurement_basis), ("non_markovianity", non_markovianity)]
    
    for ncname, ncfn in new_cands:
        print(f"\n    {ncname}:")
        for ci, (cname, fn_i, fn_j) in enumerate(comm_defs):
            total = 0.0
            for trial in range(n_trials):
                np.random.seed(trial + 92000)
                rho = make_random_density_matrix(d)
                np.random.seed(trial + 92000)
                nc_d = ncfn(rho, d)
                np.random.seed(trial + 92000)
                cm_d = commutator_disp(fn_i, fn_j, rho, d)
                total += normalized_overlap(nc_d, cm_d)
            avg = total / n_trials
            m = "❌ SAME?" if avg > 0.5 else ("⚠ partial" if avg > 0.2 else "✅ distinct")
            print(f"      vs {cname:20s}: {avg:.4f}  {m}")
    
    # Step 4: Summary
    print(f"\n{'='*70}")
    print("  SUMMARY")
    print(f"{'='*70}")
    
    trivial = [cn for cn, norm in comm_norms.items() if norm < 0.01]
    if trivial:
        print(f"\n  COLLAPSED axes (trivial commutator):")
        for t in trivial:
            print(f"    {t}")
    
    redundant = []
    for i in range(n_comm):
        for j in range(i+1, n_comm):
            if comm_overlap[i,j] > 0.7:
                redundant.append((comm_names[i], comm_names[j], comm_overlap[i,j]))
    if redundant:
        print(f"\n  REDUNDANT pairs (overlap > 0.7):")
        for a, b, ov in redundant:
            print(f"    {a} ≈ {b}  (overlap = {ov:.3f})")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "AXIS_7_12_AUDIT_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "d": d, "n_trials": n_trials,
        "comm_norms": comm_norms,
        "comm_overlap": comm_overlap.tolist(),
        "trivial_axes": trivial,
        "redundant_pairs": [(a,b,ov) for a,b,ov in redundant],
    }
    out_file = os.path.join(out_dir, "axis_7_12_audit_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run_axis_7_12_audit()
