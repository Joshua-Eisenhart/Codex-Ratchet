#!/usr/bin/env python3
"""
Definitive Axis Independence Matrix
=====================================

One sim to rule them all. Computes the full N×N overlap matrix for
every verified axis + candidate, using corrected formulations.

Axes included:
  BASE (6):  Ax0, Ax1(=Ax5 merged), Ax2, Ax3(fiber phase), Ax4, Ax6
  COMMUTATOR (4 after dedup): A7=[A1,A3], A8=[A1,A6], A9=[A3,A6], A12=[A1,A5]
  CANDIDATE (1): measurement_basis

Total: 11 axes tested

Output: clean overlap matrix + independence structure
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this computes the broad axis independence matrix numerically, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "independence matrix and overlap numerics"},
    "scipy": {"tried": True, "used": True, "reason": "matrix exponentials for axis transforms"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "scipy": "supportive"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from proto_ratchet_sim_runner import make_random_density_matrix
except ImportError:
    def make_random_density_matrix(d):
        A = np.random.randn(d,d)+1j*np.random.randn(d,d)
        rho = A@A.conj().T; return rho/np.trace(rho)

def ensure_valid(rho):
    rho=(rho+rho.conj().T)/2; ev,evc=np.linalg.eigh(rho)
    ev=np.maximum(ev,0); rho=evc@np.diag(ev)@evc.conj().T
    tr=np.trace(rho)
    if abs(tr)>1e-12: rho/=tr
    return rho

def normalized_overlap(A,B):
    nA,nB=np.linalg.norm(A,'fro'),np.linalg.norm(B,'fro')
    if nA<1e-12 or nB<1e-12: return 0.0
    return float(abs(np.trace(A.conj().T@B))/(nA*nB))


# ═══════════════════════════════════════════════════════════════════
# ALL AXES (corrected formulations)
# ═══════════════════════════════════════════════════════════════════

def ax0_fine_coarse(rho, d):
    """Ax0: fiber coarse-graining (partial dephasing)"""
    diag = np.diag(np.diag(rho))
    return (0.2*rho + 0.8*diag) - (0.8*rho + 0.2*diag)

def ax1_dissipation(rho, d):
    """Ax1=Ax5 merged: CPTP vs Unitary (dissipation class)"""
    H = np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    U = la.expm(-1j*H*0.3); rho_u = U@rho@U.conj().T
    L = np.zeros((d,d),dtype=complex)
    for k in range(d-1): L[k,k+1]=0.3
    lind = L@rho@L.conj().T - 0.5*(L.conj().T@L@rho + rho@L.conj().T@L)
    return ensure_valid(rho + lind*0.3) - rho_u

def ax2_boundary(rho, d):
    """Ax2: Eulerian (open) vs Lagrangian (closed)"""
    P = np.eye(d,dtype=complex); P[d-1,d-1]=0.7
    H = np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    return ensure_valid(P@rho@P.conj().T) - la.expm(-1j*H*0.5)@rho@la.expm(1j*H*0.5)

def ax3_chirality(rho, d):
    """Ax3: Weyl chirality via U vs U* (conjugate representation).
    Left Weyl:  ρ → U ρ U†
    Right Weyl: ρ → U* ρ U†*  (complex conjugate of U)
    Displacement = UρU† − U*ρU^T
    """
    H = np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    U = la.expm(-1j*H*0.3)
    rho_L = U @ rho @ U.conj().T           # left Weyl
    rho_R = np.conj(U) @ rho @ np.conj(U).T  # right Weyl (U*)
    return rho_L - rho_R

def ax4_composition(rho, d):
    """Ax4: B∘A vs A∘B (composition order) — explicit non-trivial maps"""
    # Map A: partial dephasing (Ti-like)
    def mA(r):
        return 0.7*r + 0.3*np.diag(np.diag(r))
    # Map B: amplitude damping (Fe-like)
    g=0.2; K0=np.eye(d,dtype=complex); K1=np.zeros((d,d),dtype=complex)
    for k in range(1,d): K0[k,k]=np.sqrt(1-g); K1[k-1,k]=np.sqrt(g)
    def mB(r):
        o=K0@r@K0.conj().T+K1@r@K1.conj().T; return o/max(abs(np.trace(o)),1e-12)
    ba = mB(mA(rho))  # B∘A
    ab = mA(mB(rho))  # A∘B
    return ba - ab

def ax6_action(rho, d):
    """Ax6: Aρ vs ρA (action side = commutator [A,ρ])"""
    A = np.random.randn(d,d)+1j*np.random.randn(d,d); A/=np.linalg.norm(A)
    return A@rho - rho@A

# --- Commutator axes (top 4 after dedup) ---

def comm_apply(fn_i, fn_j, rho, d):
    """[Ai,Aj](ρ) approximation via sequential perturbation"""
    di = fn_i(rho, d)
    dj = fn_j(rho, d)
    rho_j = ensure_valid(rho + 0.1*dj)
    rho_i = ensure_valid(rho + 0.1*di)
    return fn_i(rho_j, d) - fn_j(rho_i, d)

def a7_comm(rho, d):
    """A7 = [Ax1, Ax3]"""
    return comm_apply(ax1_dissipation, ax3_chirality, rho, d)

def a8_comm(rho, d):
    """A8 = [Ax1, Ax6]"""
    return comm_apply(ax1_dissipation, ax6_action, rho, d)

def a9_comm(rho, d):
    """A9 = [Ax3, Ax6]"""
    return comm_apply(ax3_chirality, ax6_action, rho, d)

def a12_comm(rho, d):
    """A12 = [Ax1, Ax5(≈Ax1)] — testing if truly independent"""
    # Use slightly different Lindblad strengths to see if it produces anything
    def ax5_variant(rho_in, d_val):
        L = np.zeros((d_val,d_val),dtype=complex)
        for k in range(d_val-1): L[k,k+1]=0.4  # different from Ax1's 0.3
        lind = L@rho_in@L.conj().T - 0.5*(L.conj().T@L@rho_in + rho_in@L.conj().T@L)
        rho_fga = ensure_valid(rho_in + lind*0.3)
        H = np.random.randn(d_val,d_val)+1j*np.random.randn(d_val,d_val); H=(H+H.conj().T)/2
        return rho_fga - la.expm(-1j*H*0.3)@rho_in@la.expm(1j*H*0.3)
    return comm_apply(ax1_dissipation, ax5_variant, rho, d)

# --- New candidate ---

def measurement_basis(rho, d):
    """Frame selection: z-basis vs Fourier-basis dephasing"""
    proj_z = np.diag(np.diag(rho))
    F = np.zeros((d,d), dtype=complex)
    for i in range(d):
        for j in range(d):
            F[i,j] = np.exp(2j*np.pi*i*j/d)/np.sqrt(d)
    rf = F@rho@F.conj().T; pf = np.diag(np.diag(rf))
    return proj_z - F.conj().T@pf@F


ALL_AXES = [
    # Base (6)
    ("Ax0:fine/coarse", ax0_fine_coarse),
    ("Ax1:dissipation", ax1_dissipation),
    ("Ax2:boundary", ax2_boundary),
    ("Ax3:chirality", ax3_chirality),
    ("Ax4:composition", ax4_composition),
    ("Ax6:action", ax6_action),
    # Commutator (4 after dedup)
    ("A7:[A1,A3]", a7_comm),
    ("A8:[A1,A6]", a8_comm),
    ("A9:[A3,A6]", a9_comm),
    ("A12:[A1,A5]", a12_comm),
    # New candidate
    ("NEW:meas_basis", measurement_basis),
]


def run_independence_matrix():
    d = 8
    n_trials = 150
    n_axes = len(ALL_AXES)
    
    print("=" * 80)
    print("DEFINITIVE AXIS INDEPENDENCE MATRIX")
    print(f"d={d}, {n_trials} trials, {n_axes} axes")
    print("=" * 80)
    
    overlap_matrix = np.zeros((n_axes, n_axes))
    norm_totals = np.zeros(n_axes)
    
    for trial in range(n_trials):
        np.random.seed(trial + 100000)
        rho = make_random_density_matrix(d)
        
        disps = []
        for _, fn in ALL_AXES:
            np.random.seed(trial + 100000)
            disps.append(fn(rho, d))
        
        for i in range(n_axes):
            norm_totals[i] += np.linalg.norm(disps[i], 'fro')
            for j in range(i+1, n_axes):
                ov = normalized_overlap(disps[i], disps[j])
                overlap_matrix[i,j] += ov
                overlap_matrix[j,i] += ov
    
    overlap_matrix /= n_trials
    norm_avgs = norm_totals / n_trials
    
    # Print matrix
    short_names = [n.split(":")[1][:8] for n in [a[0] for a in ALL_AXES]]
    
    print(f"\n  {'':18s}", end="")
    for sn in short_names:
        print(f"{sn:>9s}", end="")
    print(f"{'norm':>9s}")
    
    print(f"  {'':18s}", end="")
    for _ in short_names:
        print(f"{'─'*9}", end="")
    print(f"{'─'*9}")
    
    independent_count = 0
    for i in range(n_axes):
        name = ALL_AXES[i][0]
        print(f"  {name:18s}", end="")
        max_off_diag = 0.0
        for j in range(n_axes):
            if i == j:
                print(f"{'·':>9s}", end="")
            else:
                v = overlap_matrix[i,j]
                max_off_diag = max(max_off_diag, v)
                if v > 0.5:
                    print(f"\033[91m{v:8.3f}\033[0m ", end="")
                elif v > 0.2:
                    print(f"\033[93m{v:8.3f}\033[0m ", end="")
                else:
                    print(f"\033[92m{v:8.3f}\033[0m ", end="")
        print(f"{norm_avgs[i]:9.4f}", end="")
        if max_off_diag < 0.3:
            print("  ✅ CLEAN")
            independent_count += 1
        elif max_off_diag < 0.5:
            print("  ⚠️ MARGINAL")
        else:
            print("  ❌ CONFLATED")
    
    # Independence clusters (group axes with overlap > 0.5)
    print(f"\n{'─'*80}")
    print(f"  INDEPENDENCE CLUSTERS (grouped by overlap > 0.5):")
    
    visited = set()
    clusters = []
    for i in range(n_axes):
        if i in visited:
            continue
        cluster = [i]
        visited.add(i)
        for j in range(i+1, n_axes):
            if j in visited:
                continue
            if overlap_matrix[i,j] > 0.5:
                cluster.append(j)
                visited.add(j)
        clusters.append(cluster)
    
    for ci, cluster in enumerate(clusters):
        names = [ALL_AXES[i][0] for i in cluster]
        if len(cluster) == 1:
            print(f"    Axis {ci+1}: {names[0]}  (independent)")
        else:
            print(f"    Axis {ci+1}: {' ≈ '.join(names)}  (cluster of {len(cluster)})")
    
    print(f"\n  TOTAL INDEPENDENT AXES: {len(clusters)}")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    
    results = {
        "schema": "AXIS_INDEPENDENCE_MATRIX_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "d": d, "n_trials": n_trials,
        "axes": [a[0] for a in ALL_AXES],
        "overlap_matrix": overlap_matrix.tolist(),
        "norm_avgs": norm_avgs.tolist(),
        "n_clusters": len(clusters),
        "clusters": [[ALL_AXES[i][0] for i in c] for c in clusters],
    }
    out_file = os.path.join(out_dir, "axis_independence_matrix.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run_independence_matrix()
