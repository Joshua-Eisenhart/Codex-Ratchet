#!/usr/bin/env python3
"""
Mass Wiggle Exploration: Multiple Formulations Per Axis
========================================================

NO CANON. NO NARRATIVE. JUST NUMBERS.

For each axis concept (0-6), test 3-4 candidate mathematical
formulations on properly normalized states. Report the full
overlap matrix for every combination. Let the numbers speak.

State construction:
  Dirac spinor ψ = (ψ_L, ψ_R), ||ψ|| = 1
  ρ_pure = |ψ><ψ|, ρ = r·ρ_pure + (1-r)·I/4

Formulation naming: {axis}_{variant}
  e.g. ax3_A = U vs U*, ax3_B = parity, ax3_C = CP
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


def make_state(r, rng):
    psi_L = rng.normal(size=2) + 1j*rng.normal(size=2); psi_L /= np.linalg.norm(psi_L)
    psi_R = rng.normal(size=2) + 1j*rng.normal(size=2); psi_R /= np.linalg.norm(psi_R)
    psi = np.concatenate([psi_L, psi_R])
    psi /= np.linalg.norm(psi)
    rho_pure = np.outer(psi, np.conj(psi))
    rho = r * rho_pure + (1-r) * np.eye(4, dtype=complex)/4
    return rho, psi_L, psi_R

def noverlap(A, B):
    nA, nB = np.linalg.norm(A,'fro'), np.linalg.norm(B,'fro')
    if nA < 1e-12 or nB < 1e-12: return 0.0
    return float(abs(np.trace(A.conj().T@B))/(nA*nB))


# ═══════════════════════════════════════════════════════════════════
# Ax0 CANDIDATES: coarse-graining / resolution
# ═══════════════════════════════════════════════════════════════════
def ax0_A(rho, pL, pR):
    """Dephasing: diagonal vs full"""
    diag = np.diag(np.diag(rho))
    return rho - diag

def ax0_B(rho, pL, pR):
    """Partial trace left: Tr_R(ρ) embedded vs ρ"""
    rho_L = rho[:2,:2]
    embed = np.zeros_like(rho)
    embed[:2,:2] = rho_L / max(abs(np.trace(rho_L)),1e-12)
    return rho - embed

def ax0_C(rho, pL, pR):
    """Eigenvalue truncation: keep top eigenstate vs full"""
    ev, evc = np.linalg.eigh(rho)
    rho_top = np.outer(evc[:,-1], np.conj(evc[:,-1]))
    return rho - rho_top


# ═══════════════════════════════════════════════════════════════════
# Ax1 CANDIDATES: dissipation / channel type
# ═══════════════════════════════════════════════════════════════════
def ax1_A(rho, pL, pR):
    """Amplitude damping vs unitary (fixed H)"""
    H = np.zeros((4,4),dtype=complex); H[0,0]=0.3; H[1,1]=-0.3
    U = la.expm(-1j*H); rho_u = U@rho@U.conj().T
    g=0.3; K0=np.eye(4,dtype=complex); K0[1,1]=np.sqrt(1-g)
    K1=np.zeros((4,4),dtype=complex); K1[0,1]=np.sqrt(g)
    rho_c = K0@rho@K0.conj().T + K1@rho@K1.conj().T
    rho_c /= max(abs(np.trace(rho_c)),1e-12)
    return rho_c - rho_u

def ax1_B(rho, pL, pR):
    """Lindblad dissipator vs Hamiltonian"""
    L = np.zeros((4,4),dtype=complex)
    for k in range(3): L[k,k+1] = 0.3
    lind = L@rho@L.conj().T - 0.5*(L.conj().T@L@rho + rho@L.conj().T@L)
    H = np.zeros((4,4),dtype=complex); H[:2,:2] = sz*0.3
    ham = -1j*(H@rho - rho@H)
    return lind - ham

def ax1_C(rho, pL, pR):
    """Depolarizing channel vs identity"""
    lam = 0.3
    rho_dep = (1-lam)*rho + lam*np.eye(4,dtype=complex)/4
    return rho_dep - rho


# ═══════════════════════════════════════════════════════════════════
# Ax2 CANDIDATES: boundary / Eulerian vs Lagrangian
# ═══════════════════════════════════════════════════════════════════
def ax2_A(rho, pL, pR):
    """Projection (lossy) vs unitary (lossless)"""
    P = np.diag([1., 0.7, 1., 0.7]).astype(complex)
    rho_e = P@rho@P.conj().T; rho_e /= max(abs(np.trace(rho_e)),1e-12)
    H = np.zeros((4,4),dtype=complex); H[:2,:2] = sx*0.5
    rho_l = la.expm(-1j*H)@rho@la.expm(1j*H)
    return rho_e - rho_l

def ax2_B(rho, pL, pR):
    """Partial trace (discard R) vs keep full"""
    rho_L = rho[:2,:2]; tr_L = np.trace(rho_L)
    rho_reduced = np.zeros_like(rho)
    if abs(tr_L) > 1e-12: rho_reduced[:2,:2] = rho_L/tr_L
    return rho_reduced - rho

def ax2_C(rho, pL, pR):
    """Block-diagonal (closed boundary) vs full (open boundary)"""
    block = np.zeros_like(rho)
    block[:2,:2] = rho[:2,:2]; block[2:,2:] = rho[2:,2:]
    return block - rho

# ═══════════════════════════════════════════════════════════════════
# Ax3 CANDIDATES: chirality
# ═══════════════════════════════════════════════════════════════════
def ax3_A(rho, pL, pR):
    """U vs U* (original Weyl conjugate)"""
    H_small = np.array([[0.3, 0.1+0.2j],[0.1-0.2j, -0.3]], dtype=complex)
    H_big = np.zeros((4,4),dtype=complex)
    H_big[:2,:2] = H_small; H_big[2:,2:] = H_small
    U = la.expm(-1j*H_big)
    U_star = np.conj(U)
    return U@rho@U.conj().T - U_star@rho@U_star.conj().T

def ax3_B(rho, pL, pR):
    """Parity: swap L↔R blocks"""
    P = np.zeros((4,4), dtype=complex)
    P[0,2]=1; P[1,3]=1; P[2,0]=1; P[3,1]=1
    rho_P = P@rho@P.conj().T
    return rho - rho_P

def ax3_C(rho, pL, pR):
    """CP: swap L↔R AND conjugate (inverted mirror)"""
    P = np.zeros((4,4), dtype=complex)
    P[0,2]=1; P[1,3]=1; P[2,0]=1; P[3,1]=1
    rho_P = P@rho@P.conj().T
    rho_CP = np.conj(rho_P)
    return rho - rho_CP

def ax3_D(rho, pL, pR):
    """γ₅ chirality: diag(+1,+1,-1,-1)"""
    g5 = np.diag([1.,1.,-1.,-1.]).astype(complex)
    return g5@rho - rho@g5

# ═══════════════════════════════════════════════════════════════════
# Ax4 CANDIDATES: composition order / process direction
# ═══════════════════════════════════════════════════════════════════
def ax4_A(rho, pL, pR):
    """A∘B vs B∘A on endpoint"""
    def mA(r):
        return 0.7*r + 0.3*np.diag(np.diag(r))
    g=0.2; K0=np.eye(4,dtype=complex); K0[1,1]=np.sqrt(1-g)
    K1=np.zeros((4,4),dtype=complex); K1[0,1]=np.sqrt(g)
    def mB(r):
        o=K0@r@K0.conj().T+K1@r@K1.conj().T
        return o/max(abs(np.trace(o)),1e-12)
    return mB(mA(rho)) - mA(mB(rho))

def ax4_B(rho, pL, pR):
    """CW vs CCW path integral (process tensor)"""
    n=16; H=np.zeros((4,4),dtype=complex)
    H[:2,:2]=np.array([[0.3,0.1+0.2j],[0.1-0.2j,-0.3]])
    H[2:,2:]=np.array([[-0.2,0.15-0.1j],[0.15+0.1j,0.2]])
    H/=np.linalg.norm(H)
    ang=np.linspace(0,2*np.pi,n,endpoint=False)
    pcw=np.zeros_like(rho); pccw=np.zeros_like(rho)
    for t in range(n):
        Ucw=la.expm(-1j*H*ang[t]*0.3); Uccw=la.expm(-1j*H*(-ang[t])*0.3)
        pcw+=Ucw@rho@Ucw.conj().T; pccw+=Uccw@rho@Uccw.conj().T
    return (pcw-pccw)/n

def ax4_C(rho, pL, pR):
    """Commutator [H1,H2] direction: apply H1 then H2 vs H2 then H1"""
    H1=np.zeros((4,4),dtype=complex); H1[:2,:2]=sx*0.3
    H2=np.zeros((4,4),dtype=complex); H2[:2,:2]=sz*0.3
    U1=la.expm(-1j*H1*0.2); U2=la.expm(-1j*H2*0.2)
    return (U2@U1@rho@U1.conj().T@U2.conj().T -
            U1@U2@rho@U2.conj().T@U1.conj().T)


# ═══════════════════════════════════════════════════════════════════
# Ax5 CANDIDATES: FGA/FSA / curvature / texture
# ═══════════════════════════════════════════════════════════════════
def ax5_A(rho, pL, pR):
    """Geodesic curvature: second derivative along evolution"""
    H=np.zeros((4,4),dtype=complex)
    H[:2,:2]=np.array([[0.3,0.2+0.1j],[0.2-0.1j,-0.3]])
    H[2:,2:]=np.array([[-0.1,0.3-0.2j],[0.3+0.2j,0.1]])
    H/=np.linalg.norm(H); eps=0.2
    U1=la.expm(-1j*H*eps); U2=la.expm(-1j*H*2*eps)
    curv_h=U2@rho@U2.conj().T - 2*(U1@rho@U1.conj().T) + rho
    diag=np.diag(np.diag(rho))
    curv_l=(1-2*eps)*rho+2*eps*diag - 2*((1-eps)*rho+eps*diag) + rho
    return curv_h - curv_l

def ax5_B(rho, pL, pR):
    """Commutator (off-diagonal / sharp) vs anti-commutator (diagonal / smooth)"""
    A=np.zeros((4,4),dtype=complex)
    for i in range(4): A[i,i]=(2*i-3)/4
    sharp=A@rho-rho@A
    smooth=(A@rho+rho@A)/2
    return sharp - smooth

def ax5_C(rho, pL, pR):
    """Spectral gap: spread of eigenvalues"""
    ev=np.linalg.eigvalsh(rho)
    gap=ev[-1]-ev[0]
    diag=np.diag(np.diag(rho))
    # High gap (peaked) vs low gap (flat)
    return gap*(rho-diag)

def ax5_D(rho, pL, pR):
    """Von Neumann entropy gradient direction"""
    ev,evc=np.linalg.eigh(rho)
    ev_c=np.maximum(ev,1e-15)
    S = -np.sum(ev_c*np.log(ev_c))
    # Direction of entropy increase = toward max mixed
    dS = np.eye(4,dtype=complex)/4 - rho
    return S * dS  # scale by current entropy


# ═══════════════════════════════════════════════════════════════════
# Ax6 CANDIDATES: action side / precedence
# ═══════════════════════════════════════════════════════════════════
def ax6_A(rho, pL, pR):
    """Aρ - ρA with chiral operator"""
    A=np.zeros((4,4),dtype=complex)
    A[:2,:2]=np.array([[0.5,0.3+0.4j],[0.1-0.2j,-0.5]])
    A[2:,2:]=np.array([[-0.3,0.2-0.1j],[0.2+0.1j,0.3]])
    A/=np.linalg.norm(A)
    return A@rho - rho@A

def ax6_B(rho, pL, pR):
    """Aρ - ρA with random Hermitian"""
    # Use Pauli-z on full space
    g5=np.diag([1.,-1.,1.,-1.]).astype(complex)
    return g5@rho - rho@g5

def ax6_C(rho, pL, pR):
    """Left-multiply vs right-multiply by Lindblad"""
    L=np.zeros((4,4),dtype=complex)
    for k in range(3): L[k,k+1]=0.3
    return L@rho@L.conj().T - L.conj().T@rho@L

def ax6_D(rho, pL, pR):
    """ρ^(1/2)·A - A·ρ^(1/2) (sqrt-state commutator)"""
    ev,evc=np.linalg.eigh(rho)
    ev_s=np.sqrt(np.maximum(ev,0))
    rho_sqrt=evc@np.diag(ev_s)@evc.conj().T
    A=np.zeros((4,4),dtype=complex)
    A[:2,:2]=sx*0.3; A[2:,2:]=sz*0.3
    return rho_sqrt@A - A@rho_sqrt


# ═══════════════════════════════════════════════════════════════════
ALL_CANDIDATES = [
    ("ax0_A", ax0_A), ("ax0_B", ax0_B), ("ax0_C", ax0_C),
    ("ax1_A", ax1_A), ("ax1_B", ax1_B), ("ax1_C", ax1_C),
    ("ax2_A", ax2_A), ("ax2_B", ax2_B), ("ax2_C", ax2_C),
    ("ax3_A", ax3_A), ("ax3_B", ax3_B), ("ax3_C", ax3_C), ("ax3_D", ax3_D),
    ("ax4_A", ax4_A), ("ax4_B", ax4_B), ("ax4_C", ax4_C),
    ("ax5_A", ax5_A), ("ax5_B", ax5_B), ("ax5_C", ax5_C), ("ax5_D", ax5_D),
    ("ax6_A", ax6_A), ("ax6_B", ax6_B), ("ax6_C", ax6_C), ("ax6_D", ax6_D),
]


def run():
    n_trials = 150
    n_cands = len(ALL_CANDIDATES)
    r = 0.5  # mixed state, middle ground
    
    print("=" * 80)
    print("MASS WIGGLE EXPLORATION: Multiple formulations per axis")
    print(f"{n_cands} candidates, {n_trials} trials, r={r}")
    print("NO CANON. NO NARRATIVE. JUST NUMBERS.")
    print("=" * 80)
    
    overlap = np.zeros((n_cands, n_cands))
    norms = np.zeros(n_cands)
    
    for trial in range(n_trials):
        rng = np.random.default_rng(trial + 2000000)
        rho, pL, pR = make_state(r, rng)
        
        disps = []
        for _, fn in ALL_CANDIDATES:
            try:
                d = fn(rho, pL, pR)
                disps.append(d)
            except Exception:
                disps.append(np.zeros((4,4), dtype=complex))
        
        for i in range(n_cands):
            norms[i] += np.linalg.norm(disps[i], 'fro')
            for j in range(i+1, n_cands):
                ov = noverlap(disps[i], disps[j])
                overlap[i,j] += ov
                overlap[j,i] += ov
    
    overlap /= n_trials
    norms /= n_trials
    
    # Print full matrix would be huge. Instead: print intra-axis and cross-axis summaries
    
    axis_groups = {
        "ax0": [0,1,2],
        "ax1": [3,4,5],
        "ax2": [6,7,8],
        "ax3": [9,10,11,12],
        "ax4": [13,14,15],
        "ax5": [16,17,18,19],
        "ax6": [20,21,22,23],
    }
    
    # 1. Intra-axis: how much do formulations of the SAME axis agree?
    print(f"\n  INTRA-AXIS AGREEMENT (same concept, different math):")
    print(f"  {'Axis':6s} {'Candidates':30s} {'Min-Max overlap':20s} {'Verdict':12s}")
    
    for axis_name, idxs in axis_groups.items():
        pairs = []
        for i in range(len(idxs)):
            for j in range(i+1, len(idxs)):
                pairs.append(overlap[idxs[i], idxs[j]])
        mn, mx = min(pairs), max(pairs)
        avg = sum(pairs)/len(pairs)
        v = "STABLE" if mn > 0.5 else ("MIXED" if mn > 0.2 else "DIVERGENT")
        cand_names = ", ".join(ALL_CANDIDATES[k][0] for k in idxs)
        print(f"  {axis_name:6s} {cand_names:30s} {mn:.3f} — {mx:.3f} (avg {avg:.3f})  {v}")
    
    # 2. Cross-axis: for each pair of axis concepts, what's the max overlap?
    print(f"\n  CROSS-AXIS MAX OVERLAP (different concepts):")
    axis_names = list(axis_groups.keys())
    print(f"  {'':6s}", end="")
    for an in axis_names: print(f"{an:>8s}", end="")
    print()
    
    for i, an_i in enumerate(axis_names):
        print(f"  {an_i:6s}", end="")
        for j, an_j in enumerate(axis_names):
            if i == j:
                print(f"{'·':>8s}", end="")
            else:
                max_cross = 0.0
                for ii in axis_groups[an_i]:
                    for jj in axis_groups[an_j]:
                        max_cross = max(max_cross, overlap[ii, jj])
                print(f"  {max_cross:.3f}", end="")
        print()
    
    # 3. Per-candidate norms (is the candidate even alive?)
    print(f"\n  CANDIDATE NORMS:")
    for i, (name, _) in enumerate(ALL_CANDIDATES):
        bar = "████" if norms[i] > 0.1 else ("▒▒▒▒" if norms[i] > 0.01 else "░░░░" if norms[i] > 0.001 else "    ")
        print(f"    {name:8s} {norms[i]:.4f} {bar}")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "WIGGLE_EXPLORATION_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_trials": n_trials,
        "r": r,
        "candidates": [c[0] for c in ALL_CANDIDATES],
        "overlap": overlap.tolist(),
        "norms": norms.tolist(),
    }
    out_file = os.path.join(out_dir, "wiggle_exploration.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results written to {out_file}")


if __name__ == "__main__":
    run()
