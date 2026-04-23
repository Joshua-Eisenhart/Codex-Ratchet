#!/usr/bin/env python3
"""
Broad Axis Discovery Search
============================

Search for ALL independent axes in QIT state space, not just mirrors.
Tests 15 candidate quantum operations from different branches of QIT.

Each candidate is measured for residual (fraction NOT explained by known 6)
and pairwise overlap with every other candidate.

Goal: find the COMPLETE independent axis set.
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this runs a broad numerical search over candidate axes in QIT state space, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "candidate search, residuals, and overlap numerics"},
    "scipy": {"tried": True, "used": True, "reason": "matrix exponentials for candidate constructions"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "scipy": "supportive"}

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
    if abs(tr) > 1e-12: rho /= tr
    return rho

def normalized_overlap(A, B):
    nA, nB = np.linalg.norm(A, 'fro'), np.linalg.norm(B, 'fro')
    if nA < 1e-12 or nB < 1e-12: return 0.0
    return float(abs(np.trace(A.conj().T @ B)) / (nA * nB))

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
# KNOWN 6 AXES
# ═══════════════════════════════════════════════════════════════════

def ax0(rho, d):
    diag = np.diag(np.diag(rho))
    return (0.2*rho + 0.8*diag) - (0.8*rho + 0.2*diag)

def ax15(rho, d):
    H = np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    U = la.expm(-1j*H*0.3); rho_u = U@rho@U.conj().T
    L = np.zeros((d,d),dtype=complex)
    for k in range(d-1): L[k,k+1]=0.3
    lind = L@rho@L.conj().T - 0.5*(L.conj().T@L@rho + rho@L.conj().T@L)
    return ensure_valid(rho + lind*0.3) - rho_u

def ax2(rho, d):
    P = np.eye(d,dtype=complex); P[d-1,d-1]=0.7
    H = np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    return ensure_valid(P@rho@P.conj().T) - la.expm(-1j*H*0.5)@rho@la.expm(1j*H*0.5)

def ax3(rho, d):
    theta = 0.4; pp = np.exp(1j*theta)*np.eye(d); pm = np.exp(-1j*theta)*np.eye(d)
    return (pp@rho@pp.conj().T) - (pm@rho@pm.conj().T)

def ax4(rho, d):
    def mA(r): return 0.7*r + 0.3*np.diag(np.diag(r))
    g=0.2; K0=np.eye(d,dtype=complex); K1=np.zeros((d,d),dtype=complex)
    for k in range(1,d): K0[k,k]=np.sqrt(1-g); K1[k-1,k]=np.sqrt(g)
    def mB(r):
        o=K0@r@K0.conj().T+K1@r@K1.conj().T
        return o/max(abs(np.trace(o)),1e-12)
    return mB(mA(rho)) - mA(mB(rho))

def ax6(rho, d):
    A = np.random.randn(d,d)+1j*np.random.randn(d,d); A/=np.linalg.norm(A)
    return A@rho - rho@A

KNOWN = [("Ax0", ax0), ("Ax1=5", ax15), ("Ax2", ax2),
         ("Ax3", ax3), ("Ax4", ax4), ("Ax6", ax6)]


# ═══════════════════════════════════════════════════════════════════
# 15 CANDIDATE NEW AXES
# ═══════════════════════════════════════════════════════════════════

def c01_measurement_basis(rho, d):
    """Basis choice: z-dephasing vs Fourier-dephasing"""
    proj_z = np.diag(np.diag(rho))
    F = np.zeros((d,d), dtype=complex)
    for i in range(d):
        for j in range(d):
            F[i,j] = np.exp(2j*np.pi*i*j/d) / np.sqrt(d)
    rf = F@rho@F.conj().T; pf = np.diag(np.diag(rf))
    return proj_z - F.conj().T @ pf @ F

def c02_squeezing(rho, d):
    """Variance asymmetry between conjugate observables"""
    sx = np.zeros((d,d),dtype=complex); sz = np.zeros((d,d),dtype=complex)
    for k in range(d-1): sx[k,k+1]=1.0; sx[k+1,k]=1.0
    for k in range(d): sz[k,k] = (2*k-d+1)/(d-1)
    return ensure_valid(rho+0.03*(sz@rho@sz-rho)) - ensure_valid(rho+0.03*(sx@rho@sx-rho))

def c03_purity_gradient(rho, d):
    """Purification vs mixing: move toward pure vs toward I/d"""
    evals, evecs = np.linalg.eigh(rho)
    # Purify: sharpen eigenvalues
    ev_pure = evals.copy(); ev_pure = ev_pure**2; ev_pure /= sum(ev_pure)
    rho_pure = evecs @ np.diag(ev_pure) @ evecs.conj().T
    # Mix: flatten eigenvalues
    ev_mix = 0.7 * evals + 0.3 * np.ones(d)/d; ev_mix /= sum(ev_mix)
    rho_mix = evecs @ np.diag(ev_mix) @ evecs.conj().T
    return rho_pure - rho_mix

def c04_transposition(rho, d):
    """Transpose vs identity (partial transpose structure)"""
    return rho - rho.T

def c05_time_reversal(rho, d):
    """Time reversal: ρ vs σ_y ρ* σ_y (for d=even)"""
    if d == 2:
        sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    else:
        sy = np.zeros((d,d), dtype=complex)
        for k in range(d-1):
            sy[k, k+1] = -1j * (k+1)
            sy[k+1, k] = 1j * (k+1)
        sy /= max(np.linalg.norm(sy), 1e-12)
    rho_tr = sy @ np.conj(rho) @ sy.conj().T
    return rho - rho_tr

def c06_renyi_order(rho, d):
    """Rényi entropy ordering: α=2 vs α=0.5 sensitivity"""
    evals = np.maximum(np.linalg.eigvalsh(rho), 1e-15)
    # α=2 direction: amplify dominant eigenvalue
    ev2 = evals**2; ev2 /= sum(ev2)
    # α=0.5 direction: amplify minor eigenvalues
    ev05 = np.sqrt(evals); ev05 /= sum(ev05)
    evecs = np.linalg.eigh(rho)[1]
    return evecs @ np.diag(ev2) @ evecs.conj().T - evecs @ np.diag(ev05) @ evecs.conj().T

def c07_random_basis_rotation(rho, d):
    """Random basis change: similar to measurement_basis but random"""
    V = np.linalg.qr(np.random.randn(d,d)+1j*np.random.randn(d,d))[0]
    proj_orig = np.diag(np.diag(rho))
    proj_rot = V.conj().T @ np.diag(np.diag(V@rho@V.conj().T)) @ V
    return proj_orig - proj_rot

def c08_depolarization_asymmetry(rho, d):
    """Asymmetric depolarization: noise along one Pauli vs another"""
    sx = np.zeros((d,d),dtype=complex)
    sz = np.zeros((d,d),dtype=complex)
    for k in range(d-1): sx[k,k+1]=1.0; sx[k+1,k]=1.0
    for k in range(d): sz[k,k] = (2*k-d+1)/(d-1)
    p = 0.1
    rho_x = (1-p)*rho + p*sx@rho@sx  # x-noise
    rho_z = (1-p)*rho + p*sz@rho@sz  # z-noise
    return ensure_valid(rho_x) - ensure_valid(rho_z)

def c09_rank_change(rho, d):
    """Rank reduction vs rank preservation"""
    evals, evecs = np.linalg.eigh(rho)
    # Kill smallest eigenvalue
    ev_low = evals.copy()
    ev_low[0] = 0; ev_low /= max(sum(ev_low), 1e-12)
    rho_low = evecs @ np.diag(ev_low) @ evecs.conj().T
    return rho_low - rho

def c10_off_diagonal_phase(rho, d):
    """Phase rotation of off-diagonal elements only"""
    phi = 0.5
    mask = np.ones((d,d),dtype=complex) - np.eye(d,dtype=complex)
    rho_phase = np.diag(np.diag(rho)).astype(complex) + np.exp(1j*phi) * rho * mask
    rho_antiphase = np.diag(np.diag(rho)).astype(complex) + np.exp(-1j*phi) * rho * mask
    return ensure_valid(rho_phase) - ensure_valid(rho_antiphase)

def c11_conditional_entropy(rho, d):
    """Condition on different sub-blocks (split Hilbert space)"""
    h = d // 2
    if h < 1: h = 1
    block_top = rho[:h, :h].copy()
    block_bot = rho[h:, h:].copy()
    # Normalize
    t1 = np.trace(block_top); t2 = np.trace(block_bot)
    if abs(t1) > 1e-12: block_top /= t1
    if abs(t2) > 1e-12: block_bot /= t2
    # Embed back
    rho_cond_top = np.zeros_like(rho); rho_cond_top[:h,:h] = block_top
    rho_cond_bot = np.zeros_like(rho); rho_cond_bot[h:,h:] = block_bot
    return rho_cond_top - rho_cond_bot

def c12_swap_symmetry(rho, d):
    """Symmetric vs antisymmetric permutation structure"""
    # Swap first half and second half
    h = d // 2
    if h < 1: return np.zeros_like(rho)
    P = np.zeros((d,d), dtype=complex)
    for k in range(h): P[k, k+h] = 1.0; P[k+h, k] = 1.0
    for k in range(2*h, d): P[k,k] = 1.0  # identity on remainder
    rho_swapped = P @ rho @ P.conj().T
    return rho - rho_swapped

def c13_nonmarkovianity(rho, d):
    """Non-Markovian vs Markovian channel comparison"""
    # Markovian: simple Lindblad step
    L = np.zeros((d,d),dtype=complex)
    for k in range(d-1): L[k,k+1] = 0.3
    lind = L@rho@L.conj().T - 0.5*(L.conj().T@L@rho + rho@L.conj().T@L)
    rho_markov = ensure_valid(rho + lind * 0.3)
    # Non-Markovian: Lindblad + memory (reverse step followed by forward)
    rho_step1 = ensure_valid(rho - lind * 0.15)  # partial reverse
    lind2 = L@rho_step1@L.conj().T - 0.5*(L.conj().T@L@rho_step1 + rho_step1@L.conj().T@L)
    rho_nonmarkov = ensure_valid(rho_step1 + lind2 * 0.45)
    return rho_markov - rho_nonmarkov

def c14_quantum_fisher(rho, d):
    """Quantum Fisher information direction: sensitivity to parameter"""
    H = np.random.randn(d,d)+1j*np.random.randn(d,d); H=(H+H.conj().T)/2
    dt = 0.01
    # Forward perturbation
    U_fwd = la.expm(-1j*H*(0.3+dt))
    rho_fwd = U_fwd@rho@U_fwd.conj().T
    # Backward perturbation
    U_bwd = la.expm(-1j*H*(0.3-dt))
    rho_bwd = U_bwd@rho@U_bwd.conj().T
    return rho_fwd - rho_bwd  # ∝ dρ/dθ

def c15_majorization(rho, d):
    """Majorization order: more ordered vs less ordered eigenvalue spectrum"""
    evals, evecs = np.linalg.eigh(rho)
    # More majorized: push toward (1,0,...,0)
    ev_maj = evals.copy()
    ev_maj[-1] += 0.1; ev_maj[0] = max(ev_maj[0]-0.1, 0); ev_maj /= sum(ev_maj)
    # Less majorized: push toward (1/d,...,1/d)
    ev_min = 0.8*evals + 0.2*np.ones(d)/d; ev_min /= sum(ev_min)
    return evecs@np.diag(ev_maj)@evecs.conj().T - evecs@np.diag(ev_min)@evecs.conj().T


CANDIDATES = [
    ("C01: measurement basis", c01_measurement_basis),
    ("C02: squeezing", c02_squeezing),
    ("C03: purity gradient", c03_purity_gradient),
    ("C04: transposition", c04_transposition),
    ("C05: time reversal", c05_time_reversal),
    ("C06: Rényi order", c06_renyi_order),
    ("C07: random basis rot", c07_random_basis_rotation),
    ("C08: depol asymmetry", c08_depolarization_asymmetry),
    ("C09: rank change", c09_rank_change),
    ("C10: off-diag phase", c10_off_diagonal_phase),
    ("C11: conditional entropy", c11_conditional_entropy),
    ("C12: swap symmetry", c12_swap_symmetry),
    ("C13: non-Markovianity", c13_nonmarkovianity),
    ("C14: quantum Fisher", c14_quantum_fisher),
    ("C15: majorization", c15_majorization),
]


# ═══════════════════════════════════════════════════════════════════
# MAIN SEARCH
# ═══════════════════════════════════════════════════════════════════

def run_broad_search():
    d = 8
    n_trials = 150
    
    print("=" * 70)
    print("BROAD AXIS DISCOVERY: 15 candidates tested against 6 known axes")
    print(f"d={d}, {n_trials} trials each")
    print("=" * 70)
    
    # Phase 1: Residual analysis (vs known 6)
    print(f"\n{'':4s}{'Candidate':28s}{'Resid':>8s}{'MaxOvl':>8s}{'With':>8s}{'Verdict':>14s}")
    print(f"{'':4s}{'─'*28}{'─'*8}{'─'*8}{'─'*8}{'─'*14}")
    
    axis_labels = [an for an, _ in KNOWN]
    candidate_residuals = {}
    candidate_max_overlaps = {}
    
    for cname, cfn in CANDIDATES:
        res_total = 0.0
        ovl_totals = [0.0] * len(KNOWN)
        valid_count = 0
        
        for trial in range(n_trials):
            np.random.seed(trial + 70000)
            rho = make_random_density_matrix(d)
            
            np.random.seed(trial + 70000)
            known_disps = [fn(rho, d) for _, fn in KNOWN]
            
            np.random.seed(trial + 70000)
            try:
                cd = cfn(rho, d)
            except Exception:
                continue
            
            cdn = np.linalg.norm(cd, 'fro')
            if cdn < 1e-12: continue
            valid_count += 1
            
            proj = project_out(cd, known_disps)
            res_total += np.linalg.norm(proj) / cdn
            
            for ai, kd in enumerate(known_disps):
                ovl_totals[ai] += normalized_overlap(cd, kd)
        
        if valid_count == 0:
            print(f"    {cname:28s}{'SKIP':>8s}")
            continue
        
        res_avg = res_total / valid_count
        ovl_avgs = [o / valid_count for o in ovl_totals]
        max_ovl = max(ovl_avgs)
        max_with = axis_labels[ovl_avgs.index(max_ovl)]
        
        candidate_residuals[cname] = res_avg
        candidate_max_overlaps[cname] = max_ovl
        
        if res_avg > 0.7 and max_ovl < 0.4:
            verdict = "🔥 STRONG"
        elif res_avg > 0.5 and max_ovl < 0.5:
            verdict = "⚠️  POSSIBLE"
        elif res_avg > 0.5:
            verdict = "⚠️  PARTIAL"
        elif res_avg < 0.1:
            verdict = "❌ CAPTURED"
        else:
            verdict = "─ WEAK"
        
        print(f"    {cname:28s}{res_avg:>8.4f}{max_ovl:>8.4f}{max_with:>8s}{verdict:>14s}")
    
    # Phase 2: Find strongest candidates
    strong = [(cn, cr) for cn, cr in candidate_residuals.items() 
              if cr > 0.5 and candidate_max_overlaps[cn] < 0.5]
    strong.sort(key=lambda x: -x[1])
    
    print(f"\n{'─'*70}")
    print(f"  STRONG CANDIDATES (residual > 0.5, max_overlap < 0.5):")
    if not strong:
        print(f"  None found.")
    else:
        for cn, cr in strong:
            print(f"    {cn}: residual={cr:.4f}, max_overlap={candidate_max_overlaps[cn]:.4f}")
    
    # Phase 3: Cross-overlap between strong candidates
    if len(strong) > 1:
        print(f"\n{'─'*70}")
        print(f"  CROSS-OVERLAP between strong candidates:")
        strong_names = [s[0] for s in strong]
        strong_fns = {cn: cfn for cn, cfn in CANDIDATES}
        
        header = f"{'':28s}" + "".join(f"{cn[-10:]:>12s}" for cn in strong_names)
        print(f"    {header}")
        
        for ci, cn1 in enumerate(strong_names):
            row = f"    {cn1:28s}"
            for cj, cn2 in enumerate(strong_names):
                if ci == cj:
                    row += f"{'---':>12s}"
                else:
                    total = 0.0
                    for trial in range(min(n_trials, 100)):
                        np.random.seed(trial + 80000)
                        rho = make_random_density_matrix(d)
                        np.random.seed(trial + 80000)
                        d1 = strong_fns[cn1](rho, d)
                        np.random.seed(trial + 80000)
                        d2 = strong_fns[cn2](rho, d)
                        total += normalized_overlap(d1, d2)
                    avg = total / min(n_trials, 100)
                    marker = "✅" if avg < 0.2 else ("⚠️" if avg < 0.5 else "❌")
                    row += f" {avg:.3f}{marker}  "
            print(row)
    
    # Phase 4: Count total independent axes
    print(f"\n{'='*70}")
    print(f"  AXIS COUNT ESTIMATE:")
    print(f"    Known verified: 6 (Ax0, Ax1=5, Ax2, Ax3, Ax4, Ax6)")
    print(f"    Strong new candidates: {len(strong)}")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "BROAD_AXIS_SEARCH_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "d": d, "n_trials": n_trials,
        "residuals": candidate_residuals,
        "max_overlaps": candidate_max_overlaps,
        "strong_candidates": [s[0] for s in strong],
    }
    out_file = os.path.join(out_dir, "broad_axis_search_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run_broad_search()
