#!/usr/bin/env python3
"""
Ax1 vs Ax5 on Mixed States: Do They Separate?
===============================================

Previous finding: Ax1 ≈ Ax5 (overlap 0.9997) on pure states.

User hypothesis: They separate on MIXED states because:
  Ax1 = IS the channel open or closed (CPTP vs Unitary)
  Ax5 = WHAT SHAPE is the boundary (sharp vs blurry, set by entropy)

On pure states: only dissipation can blur → Ax1 = Ax5.
On mixed states: entropy can vary independently of channel type → Ax1 ≠ Ax5.

TEST: Measure Ax1/Ax5 overlap at different Bloch radii (r=1: pure, r→0: hot).
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def make_mixed_state(d, r, rng):
    """Create a mixed state with Bloch radius r.
    r=1: pure state (cold), r=0: maximally mixed (hot).
    """
    if d == 2:
        direction = rng.normal(size=3)
        direction /= np.linalg.norm(direction)
        p = r * direction
        sx = np.array([[0,1],[1,0]], dtype=complex)
        sy = np.array([[0,-1j],[1j,0]], dtype=complex)
        sz = np.array([[1,0],[0,-1]], dtype=complex)
        return (np.eye(2, dtype=complex) + p[0]*sx + p[1]*sy + p[2]*sz) / 2
    else:
        # General d: interpolate between random pure and maximally mixed
        psi = rng.normal(size=d) + 1j*rng.normal(size=d)
        psi /= np.linalg.norm(psi)
        rho_pure = np.outer(psi, np.conj(psi))
        rho_mixed = np.eye(d, dtype=complex) / d
        return r * rho_pure + (1-r) * rho_mixed


def ensure_valid(rho):
    rho = (rho + rho.conj().T)/2
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


def von_neumann_entropy(rho):
    ev = np.linalg.eigvalsh(rho)
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(np.maximum(ev, 1e-30))))


def ax1_dissipation(rho, d):
    """Ax1: CPTP (open channel) vs Unitary (closed channel).
    Binary: IS dissipation happening?
    """
    # Unitary
    H = np.zeros((d,d), dtype=complex)
    H[0,0] = 0.3; H[1,1] = -0.3
    if d > 2: H[2,2] = 0.1
    U = la.expm(-1j*H)
    rho_u = U @ rho @ U.conj().T
    # CPTP: amplitude damping
    gamma = 0.3
    K0 = np.eye(d, dtype=complex)
    K1 = np.zeros((d,d), dtype=complex)
    K0[1,1] = np.sqrt(1-gamma)
    K1[0,1] = np.sqrt(gamma)
    rho_c = K0@rho@K0.conj().T + K1@rho@K1.conj().T
    rho_c /= max(abs(np.trace(rho_c)), 1e-12)
    return rho_c - rho_u


def ax5_boundary_shape(rho, d):
    """Ax5: SHAPE of the boundary = sharp vs blurry.
    The curvature of the S-curve = how much the off-diagonal
    structure is preserved.
    
    Sharp boundary (lines/FGA): eigenvalues are concentrated,
    off-diagonals dominate → commutator-like structure.
    
    Blurry boundary (waves/FSA): eigenvalues are spread,
    diagonals dominate → anti-commutator-like structure.
    """
    # "Sharp" (lines): measure via commutator with a sharp operator
    # This extracts the non-commutative (off-diagonal) structure
    A = np.zeros((d,d), dtype=complex)
    for i in range(d):
        A[i,i] = (2*i - d + 1) / d  # discrete gradient
    sharp = A @ rho - rho @ A  # commutator = off-diagonal sensitivity
    
    # "Blurry" (waves): measure via anti-commutator with smooth operator
    # This extracts the commutative (diagonal) structure
    B = np.ones((d,d), dtype=complex) / d  # uniform = maximally smooth
    blurry = (B @ rho + rho @ B) / 2  # anti-commutator = on-diagonal sensitivity
    blurry /= max(np.linalg.norm(blurry, 'fro'), 1e-12)
    
    return sharp - blurry


def run():
    n_trials = 200
    d_values = [2, 4, 8]
    r_values = [1.0, 0.9, 0.7, 0.5, 0.3, 0.1, 0.01]  # pure → hot
    
    print("=" * 80)
    print("AX1 vs AX5: SEPARATION ON MIXED STATES")
    print(f"{n_trials} trials, d={d_values}, r=pure(1.0)→hot(0.01)")
    print("=" * 80)
    
    all_results = {}
    
    for d in d_values:
        print(f"\n  {'─'*70}")
        print(f"  d = {d}")
        print(f"  {'─'*70}")
        print(f"  {'r':>6s} {'S(ρ)':>8s} {'Ax1_norm':>10s} {'Ax5_norm':>10s} {'overlap':>10s} {'verdict':>12s}")
        
        for r in r_values:
            total_overlap = 0.0
            total_ax1_norm = 0.0
            total_ax5_norm = 0.0
            total_entropy = 0.0
            
            for trial in range(n_trials):
                rng = np.random.default_rng(trial + 800000 + int(r*1000) + d*10000)
                rho = make_mixed_state(d, r, rng)
                
                d1 = ax1_dissipation(rho, d)
                d5 = ax5_boundary_shape(rho, d)
                
                total_ax1_norm += np.linalg.norm(d1, 'fro')
                total_ax5_norm += np.linalg.norm(d5, 'fro')
                total_overlap += normalized_overlap(d1, d5)
                total_entropy += von_neumann_entropy(rho)
            
            avg_ov = total_overlap / n_trials
            avg_ax1 = total_ax1_norm / n_trials
            avg_ax5 = total_ax5_norm / n_trials
            avg_S = total_entropy / n_trials
            
            if avg_ov > 0.7:
                verdict = "≈ SAME"
            elif avg_ov > 0.3:
                verdict = "⚠️ PARTIAL"
            elif avg_ov > 0.1:
                verdict = "🔥 SEPARATING"
            else:
                verdict = "✅ DISTINCT"
            
            print(f"  {r:>6.2f} {avg_S:>8.3f} {avg_ax1:>10.4f} {avg_ax5:>10.4f} {avg_ov:>10.4f} {verdict}")
            
            key = f"d={d},r={r}"
            all_results[key] = {
                "d": d, "r": r,
                "entropy": round(avg_S, 4),
                "ax1_norm": round(avg_ax1, 4),
                "ax5_norm": round(avg_ax5, 4),
                "overlap": round(avg_ov, 4),
            }
    
    # Summary
    print(f"\n{'='*80}")
    print("  SUMMARY")
    print(f"{'='*80}")
    print()
    print("  Ax1 = IS the channel open or closed (binary)")
    print("  Ax5 = WHAT SHAPE the boundary has (depends on entropy)")
    print()
    print("  If they SEPARATE on mixed states but not pure states,")
    print("  then the previous Ax1≈Ax5 merge was an artifact of")
    print("  testing on pure states only.")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "AX1_AX5_SEPARATION_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "results": all_results,
    }
    out_file = os.path.join(out_dir, "ax1_ax5_separation.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results written to {out_file}")


if __name__ == "__main__":
    run()
