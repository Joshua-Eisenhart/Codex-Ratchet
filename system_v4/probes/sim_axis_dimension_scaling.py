#!/usr/bin/env python3
"""
Axis Independence: Dimension Scaling
======================================

Same 11-axis independence matrix, but at d={2,4,8,16,32}.
Answers:
  Q1: Does the Ax0/Ax1/Ax2 cluster split at higher d?
  Q2: Does Ax3 (U vs U*) get cleaner at higher d?
  Q3: Does Ax4 (composition order) activate at any d?
  Q4: How many true independent axes exist as d→∞?
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
# AXES (same as independence matrix, with Ax4 fix attempt)
# ═══════════════════════════════════════════════════════════════════

def ax0(rho,d):
    diag=np.diag(np.diag(rho)); return (0.2*rho+0.8*diag)-(0.8*rho+0.2*diag)

def ax1(rho,d):
    H=np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    U=la.expm(-1j*H*0.3); rho_u=U@rho@U.conj().T
    L=np.zeros((d,d),dtype=complex)
    for k in range(d-1): L[k,k+1]=0.3
    lind=L@rho@L.conj().T-0.5*(L.conj().T@L@rho+rho@L.conj().T@L)
    return ensure_valid(rho+lind*0.3)-rho_u

def ax2(rho,d):
    P=np.eye(d,dtype=complex); P[d-1,d-1]=0.7
    H=np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    return ensure_valid(P@rho@P.conj().T)-la.expm(-1j*H*0.5)@rho@la.expm(1j*H*0.5)

def ax3(rho,d):
    """U vs U* Weyl chirality"""
    H=np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    U=la.expm(-1j*H*0.3)
    return U@rho@U.conj().T - np.conj(U)@rho@np.conj(U).T

def ax4(rho,d):
    """Composition order: use RANDOM non-commuting maps for each trial"""
    # Map A: random unitary rotation
    H_a = np.random.randn(d,d)+1j*np.random.randn(d,d); H_a=(H_a+H_a.conj().T)/2
    U_a = la.expm(-1j*H_a*0.4)
    def mA(r): return U_a@r@U_a.conj().T
    # Map B: random Lindblad step (dissipative)
    L_b = np.random.randn(d,d)+1j*np.random.randn(d,d)
    L_b *= 0.3/max(np.linalg.norm(L_b),1e-12)
    def mB(r):
        lind = L_b@r@L_b.conj().T - 0.5*(L_b.conj().T@L_b@r + r@L_b.conj().T@L_b)
        return ensure_valid(r + lind*0.5)
    ba = mB(mA(rho))
    ab = mA(mB(rho))
    return ba - ab

def ax6(rho,d):
    A=np.random.randn(d,d)+1j*np.random.randn(d,d); A/=np.linalg.norm(A)
    return A@rho-rho@A

def meas_basis(rho,d):
    proj_z = np.diag(np.diag(rho))
    F = np.zeros((d,d),dtype=complex)
    for i in range(d):
        for j in range(d):
            F[i,j] = np.exp(2j*np.pi*i*j/d)/np.sqrt(d)
    rf=F@rho@F.conj().T; pf=np.diag(np.diag(rf))
    return proj_z - F.conj().T@pf@F

AXES = [
    ("Ax0", ax0), ("Ax1", ax1), ("Ax2", ax2), ("Ax3", ax3),
    ("Ax4", ax4), ("Ax6", ax6), ("meas", meas_basis),
]
# Focus on the 7 most important axes (base + new candidate)
# Skip commutator axes for d-scaling (too slow at d=32)


def run_dscale():
    d_values = [2, 4, 8, 16, 32]
    n_trials = 100
    n_axes = len(AXES)
    all_results = {}
    
    print("=" * 80)
    print("AXIS INDEPENDENCE: DIMENSION SCALING")
    print(f"{n_axes} axes × {len(d_values)} dimensions × {n_trials} trials")
    print("=" * 80)
    
    for d in d_values:
        print(f"\n{'─'*80}")
        print(f"  d = {d}")
        print(f"{'─'*80}")
        
        overlap_matrix = np.zeros((n_axes, n_axes))
        norm_totals = np.zeros(n_axes)
        
        for trial in range(n_trials):
            np.random.seed(trial + 200000 + d*1000)
            rho = make_random_density_matrix(d)
            disps = []
            for _, fn in AXES:
                np.random.seed(trial + 200000 + d*1000)
                disps.append(fn(rho, d))
            
            for i in range(n_axes):
                norm_totals[i] += np.linalg.norm(disps[i], 'fro')
                for j in range(i+1, n_axes):
                    ov = normalized_overlap(disps[i], disps[j])
                    overlap_matrix[i,j] += ov
                    overlap_matrix[j,i] += ov
        
        overlap_matrix /= n_trials
        norm_avgs = norm_totals / n_trials
        
        # Print condensed matrix
        short = [a[0] for a in AXES]
        print(f"  {'':6s}", end="")
        for s in short: print(f"{s:>7s}", end="")
        print(f"{'norm':>8s}")
        
        for i in range(n_axes):
            print(f"  {short[i]:6s}", end="")
            for j in range(n_axes):
                if i==j: print(f"{'·':>7s}", end="")
                else:
                    v = overlap_matrix[i,j]
                    print(f"  {v:.3f}", end="")
            print(f"  {norm_avgs[i]:.4f}")
        
        # Track key metrics
        all_results[f"d={d}"] = {
            "Ax0_Ax1": float(overlap_matrix[0,1]),
            "Ax0_Ax2": float(overlap_matrix[0,2]),
            "Ax1_Ax2": float(overlap_matrix[1,2]),
            "Ax3_max": float(max(overlap_matrix[3,j] for j in range(n_axes) if j!=3)),
            "Ax3_norm": float(norm_avgs[3]),
            "Ax4_norm": float(norm_avgs[4]),
            "Ax4_max": float(max(overlap_matrix[4,j] for j in range(n_axes) if j!=4)),
            "meas_max": float(max(overlap_matrix[6,j] for j in range(n_axes) if j!=6)),
        }
    
    # Summary: tracking key pairs across dimensions
    print(f"\n{'='*80}")
    print(f"  DIMENSION SCALING SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n  Q1: Does Ax0/Ax1/Ax2 cluster split?")
    print(f"  {'d':>4s}  {'Ax0-Ax1':>8s} {'Ax0-Ax2':>8s} {'Ax1-Ax2':>8s}  {'Trend':>10s}")
    for d in d_values:
        r = all_results[f"d={d}"]
        avg = (r["Ax0_Ax1"] + r["Ax0_Ax2"] + r["Ax1_Ax2"]) / 3
        trend = "CLUSTER" if avg > 0.4 else ("SPLITTING" if avg > 0.2 else "SPLIT")
        print(f"  {d:>4d}  {r['Ax0_Ax1']:>8.4f} {r['Ax0_Ax2']:>8.4f} {r['Ax1_Ax2']:>8.4f}  {trend:>10s}")
    
    print(f"\n  Q2: Does Ax3 (U vs U*) get cleaner?")
    print(f"  {'d':>4s}  {'max_ovl':>8s} {'norm':>8s}  {'Status':>10s}")
    for d in d_values:
        r = all_results[f"d={d}"]
        status = "CLEAN" if r["Ax3_max"] < 0.1 else ("MARGINAL" if r["Ax3_max"] < 0.3 else "DIRTY")
        print(f"  {d:>4d}  {r['Ax3_max']:>8.4f} {r['Ax3_norm']:>8.4f}  {status:>10s}")
    
    print(f"\n  Q3: Does Ax4 activate?")
    print(f"  {'d':>4s}  {'norm':>8s} {'max_ovl':>8s}  {'Status':>10s}")
    for d in d_values:
        r = all_results[f"d={d}"]
        status = "ACTIVE" if r["Ax4_norm"] > 0.01 else "ZERO"
        print(f"  {d:>4d}  {r['Ax4_norm']:>8.4f} {r['Ax4_max']:>8.4f}  {status:>10s}")
    
    print(f"\n  Q4: measurement_basis stability?")
    print(f"  {'d':>4s}  {'max_ovl':>8s}  {'Status':>10s}")
    for d in d_values:
        r = all_results[f"d={d}"]
        status = "CLEAN" if r["meas_max"] < 0.2 else ("OK" if r["meas_max"] < 0.3 else "DIRTY")
        print(f"  {d:>4d}  {r['meas_max']:>8.4f}  {status:>10s}")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "AXIS_DSCALE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "d_values": d_values, "n_trials": n_trials,
        "tracking": all_results,
    }
    out_file = os.path.join(out_dir, "axis_dimension_scaling.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run_dscale()
