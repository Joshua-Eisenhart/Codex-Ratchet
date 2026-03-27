#!/usr/bin/env python3
"""
Deep Test: 7th Axis Candidates
================================

Rigorous validation of measurement_basis and squeezing as 7th axis candidates.

TESTS:
  1. Dimension scaling: do residuals HOLD at d=2,4,8,16,32?
  2. Full overlap matrix: each candidate vs ALL 6 known axes
  3. Cross-test: are measurement_basis and squeezing the same or different?
  4. Stability: does the result change with different random operators?
  5. Connection test: does either candidate map to existing Jungian labels?
  6. Operator test: what OPERATORS produce this displacement? (Ti/Fe/Te/Fi)
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
        A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        rho = A @ A.conj().T
        return rho / np.trace(rho)


def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    ev, evc = np.linalg.eigh(rho)
    ev = np.maximum(ev, 0)
    rho = evc @ np.diag(ev) @ evc.conj().T
    tr = np.trace(rho)
    if abs(tr) > 1e-12:
        rho /= tr
    return rho


def normalized_overlap(A, B):
    nA, nB = np.linalg.norm(A, 'fro'), np.linalg.norm(B, 'fro')
    if nA < 1e-12 or nB < 1e-12:
        return 0.0
    return float(abs(np.trace(A.conj().T @ B)) / (nA * nB))


# ═══════════════════════════════════════════════════════════════════
# AXIS DISPLACEMENT GENERATORS
# ═══════════════════════════════════════════════════════════════════

def ax0_disp(rho, d):
    diag = np.diag(np.diag(rho))
    return (0.2*rho + 0.8*diag) - (0.8*rho + 0.2*diag)

def ax15_disp(rho, d):
    """Merged Ax1=Ax5: CPTP vs Unitary"""
    H = np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    U = la.expm(-1j*H*0.3)
    rho_uni = U@rho@U.conj().T
    L = np.zeros((d,d),dtype=complex)
    for k in range(d-1): L[k,k+1]=0.3
    lind = L@rho@L.conj().T - 0.5*(L.conj().T@L@rho + rho@L.conj().T@L)
    rho_cptp = ensure_valid(rho + lind*0.3)
    return rho_cptp - rho_uni

def ax2_disp(rho, d):
    P = np.eye(d,dtype=complex); P[d-1,d-1]=0.7
    rho_e = ensure_valid(P@rho@P.conj().T)
    H = np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    rho_l = la.expm(-1j*H*0.5)@rho@la.expm(1j*H*0.5)
    return rho_e - rho_l

def ax3_disp(rho, d):
    """Chirality via Hopf fiber phase (correct formulation)"""
    theta = 0.4
    pp = np.exp(1j*theta)*np.eye(d)
    pm = np.exp(-1j*theta)*np.eye(d)
    return (pp@rho@pp.conj().T) - (pm@rho@pm.conj().T)

def ax4_disp(rho, d):
    def mA(r): return 0.7*r + 0.3*np.diag(np.diag(r))
    g=0.2; K0=np.eye(d,dtype=complex); K1=np.zeros((d,d),dtype=complex)
    for k in range(1,d): K0[k,k]=np.sqrt(1-g); K1[k-1,k]=np.sqrt(g)
    def mB(r):
        o=K0@r@K0.conj().T+K1@r@K1.conj().T
        return o/max(abs(np.trace(o)),1e-12)
    return mB(mA(rho)) - mA(mB(rho))

def ax6_disp(rho, d):
    A = np.random.randn(d,d)+1j*np.random.randn(d,d); A/=np.linalg.norm(A)
    return A@rho - rho@A

KNOWN_AXES = [
    ("Ax0", ax0_disp), ("Ax1=5", ax15_disp), ("Ax2", ax2_disp),
    ("Ax3", ax3_disp), ("Ax4", ax4_disp), ("Ax6", ax6_disp),
]


# ═══════════════════════════════════════════════════════════════════
# 7TH AXIS CANDIDATES
# ═══════════════════════════════════════════════════════════════════

def measurement_basis_disp(rho, d):
    """Measurement basis: z-basis vs Fourier basis dephasing."""
    proj_z = np.diag(np.diag(rho))
    F = np.zeros((d,d), dtype=complex)
    for i in range(d):
        for j in range(d):
            F[i,j] = np.exp(2j*np.pi*i*j/d) / np.sqrt(d)
    rho_f = F@rho@F.conj().T
    proj_f = np.diag(np.diag(rho_f))
    proj_f_back = F.conj().T @ proj_f @ F
    return proj_z - proj_f_back

def squeezing_disp(rho, d):
    """Squeezing: variance asymmetry between conjugate obs."""
    sx = np.zeros((d,d),dtype=complex)
    sz = np.zeros((d,d),dtype=complex)
    for k in range(d-1): sx[k,k+1]=1.0; sx[k+1,k]=1.0
    for k in range(d): sz[k,k] = (2*k-d+1)/(d-1)
    rho_sq = ensure_valid(rho + 0.03*(sz@rho@sz - rho))
    rho_asq = ensure_valid(rho + 0.03*(sx@rho@sx - rho))
    return rho_sq - rho_asq

CANDIDATES = [
    ("measurement_basis", measurement_basis_disp),
    ("squeezing", squeezing_disp),
]


def project_out(target, basis_vecs):
    res = target.copy().flatten()
    for b in basis_vecs:
        bf = b.flatten()
        nb = np.linalg.norm(bf)
        if nb < 1e-12: continue
        bh = bf / nb
        res -= np.dot(res.conj(), bh) * bh
    return res


# ═══════════════════════════════════════════════════════════════════
# TEST 1: DIMENSION SCALING
# ═══════════════════════════════════════════════════════════════════

def test_dimension_scaling():
    print("=" * 70)
    print("TEST 1: DIMENSION SCALING — Does 7th axis residual hold?")
    print("=" * 70)
    
    d_values = [2, 4, 8, 16, 32]
    n_trials = 100
    
    for cname, cfn in CANDIDATES:
        print(f"\n  {cname}:")
        print(f"  {'d':>4s}  {'Residual':>10s}  {'MaxOvl':>8s}  {'Verdict':>10s}")
        for d in d_values:
            res_total = 0.0
            max_ovl_total = 0.0
            for trial in range(n_trials):
                np.random.seed(trial + 20000 + d*100)
                rho = make_random_density_matrix(d)
                np.random.seed(trial + 20000 + d*100)
                known = [fn(rho, d) for _, fn in KNOWN_AXES]
                np.random.seed(trial + 20000 + d*100)
                cd = cfn(rho, d)
                
                cdn = np.linalg.norm(cd, 'fro')
                if cdn < 1e-12: continue
                
                proj = project_out(cd, known)
                res_total += np.linalg.norm(proj) / cdn
                
                ovls = [normalized_overlap(cd, k) for k in known]
                max_ovl_total += max(ovls)
            
            res_avg = res_total / n_trials
            max_ovl_avg = max_ovl_total / n_trials
            v = "✅ HOLDS" if res_avg > 0.5 else ("⚠️" if res_avg > 0.3 else "❌ DROPS")
            print(f"  {d:>4d}  {res_avg:>10.4f}  {max_ovl_avg:>8.4f}  {v:>10s}")


# ═══════════════════════════════════════════════════════════════════
# TEST 2: FULL OVERLAP DETAIL
# ═══════════════════════════════════════════════════════════════════

def test_full_overlap():
    print("\n" + "=" * 70)
    print("TEST 2: FULL OVERLAP — Each candidate vs each known axis")
    print("=" * 70)
    
    d = 8
    n_trials = 200
    
    for cname, cfn in CANDIDATES:
        overlaps = {an: 0.0 for an, _ in KNOWN_AXES}
        
        for trial in range(n_trials):
            np.random.seed(trial + 30000)
            rho = make_random_density_matrix(d)
            np.random.seed(trial + 30000)
            cd = cfn(rho, d)
            cdn = np.linalg.norm(cd, 'fro')
            if cdn < 1e-12: continue
            
            for an, afn in KNOWN_AXES:
                np.random.seed(trial + 30000)
                ad = afn(rho, d)
                overlaps[an] += normalized_overlap(cd, ad)
        
        print(f"\n  {cname}:")
        for an in overlaps:
            ov = overlaps[an] / n_trials
            bar = "█" * int(ov * 40)
            status = "✅" if ov < 0.1 else ("⚠️" if ov < 0.3 else "❌")
            print(f"    vs {an:8s}: {ov:.4f} {status} {bar}")


# ═══════════════════════════════════════════════════════════════════
# TEST 3: CROSS-TEST — Same or different?
# ═══════════════════════════════════════════════════════════════════

def test_cross():
    print("\n" + "=" * 70)
    print("TEST 3: CROSS-TEST — Are the two candidates the same axis?")
    print("=" * 70)
    
    d_values = [4, 8, 16]
    n_trials = 200
    
    for d in d_values:
        total = 0.0
        for trial in range(n_trials):
            np.random.seed(trial + 40000 + d*100)
            rho = make_random_density_matrix(d)
            np.random.seed(trial + 40000 + d*100)
            d_mb = measurement_basis_disp(rho, d)
            np.random.seed(trial + 40000 + d*100)
            d_sq = squeezing_disp(rho, d)
            total += normalized_overlap(d_mb, d_sq)
        
        avg = total / n_trials
        verdict = "SAME" if avg > 0.8 else ("PARTIAL" if avg > 0.4 else "DISTINCT")
        print(f"  d={d:2d}: overlap = {avg:.4f}  → {verdict}")


# ═══════════════════════════════════════════════════════════════════
# TEST 4: OPERATOR CONNECTION — Which Jungian function produces this?
# ═══════════════════════════════════════════════════════════════════

def test_operator_connection():
    print("\n" + "=" * 70)
    print("TEST 4: OPERATOR CONNECTION — Which operators produce this?")
    print("=" * 70)
    
    d = 4
    n_trials = 200
    
    # Define operator displacements (Ti, Fe, Te, Fi)
    def ti_disp(rho, d_val):
        """Ti = dephasing/projection"""
        return np.diag(np.diag(rho)) - rho
    
    def fe_disp(rho, d_val):
        """Fe = amplitude damping"""
        g = 0.3
        K0 = np.eye(d_val, dtype=complex)
        K1 = np.zeros((d_val,d_val), dtype=complex)
        for k in range(1,d_val): K0[k,k]=np.sqrt(1-g); K1[k-1,k]=np.sqrt(g)
        return K0@rho@K0.conj().T + K1@rho@K1.conj().T - rho
    
    def te_disp(rho, d_val):
        """Te = unitary rotation"""
        H = np.random.randn(d_val,d_val)+1j*np.random.randn(d_val,d_val)
        H = (H+H.conj().T)/2
        U = la.expm(-1j*H*0.3)
        return U@rho@U.conj().T - rho
    
    def fi_disp(rho, d_val):
        """Fi = spectral filter"""
        F = np.diag([1.0] + [0.5]*(d_val-1)).astype(complex)
        out = F@rho@F.conj().T
        out /= max(abs(np.trace(out)), 1e-12)
        return out - rho
    
    ops = [("Ti", ti_disp), ("Fe", fe_disp), ("Te", te_disp), ("Fi", fi_disp)]
    
    for cname, cfn in CANDIDATES:
        print(f"\n  {cname} overlap with operators:")
        for oname, ofn in ops:
            total = 0.0
            for trial in range(n_trials):
                np.random.seed(trial + 50000)
                rho = make_random_density_matrix(d)
                np.random.seed(trial + 50000)
                cd = cfn(rho, d)
                np.random.seed(trial + 50000)
                od = ofn(rho, d)
                total += normalized_overlap(cd, od)
            avg = total / n_trials
            bar = "█" * int(avg * 40)
            print(f"    vs {oname}: {avg:.4f}  {bar}")


# ═══════════════════════════════════════════════════════════════════
# TEST 5: STABILITY — Different random seeds
# ═══════════════════════════════════════════════════════════════════

def test_stability():
    print("\n" + "=" * 70)
    print("TEST 5: STABILITY — Consistent across random seeds?")
    print("=" * 70)
    
    d = 8
    n_trials = 100
    n_seeds = 5
    
    for cname, cfn in CANDIDATES:
        residuals = []
        for seed_offset in range(n_seeds):
            res_total = 0.0
            for trial in range(n_trials):
                s = seed_offset * 100000 + trial + 60000
                np.random.seed(s)
                rho = make_random_density_matrix(d)
                np.random.seed(s)
                known = [fn(rho, d) for _, fn in KNOWN_AXES]
                np.random.seed(s)
                cd = cfn(rho, d)
                cdn = np.linalg.norm(cd, 'fro')
                if cdn < 1e-12: continue
                proj = project_out(cd, known)
                res_total += np.linalg.norm(proj) / cdn
            residuals.append(res_total / n_trials)
        
        mean_r = np.mean(residuals)
        std_r = np.std(residuals)
        print(f"  {cname}: residual = {mean_r:.4f} ± {std_r:.4f}  "
              f"{'✅ STABLE' if std_r < 0.05 else '⚠️  UNSTABLE'}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_dimension_scaling()
    test_full_overlap()
    test_cross()
    test_operator_connection()
    test_stability()
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE")
    print("=" * 70)
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    
    results = {
        "schema": "AXIS7_DEEP_TEST_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "tests_run": ["dimension_scaling", "full_overlap", "cross_test", 
                      "operator_connection", "stability"],
    }
    out_file = os.path.join(out_dir, "axis7_deep_test_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_file}")
