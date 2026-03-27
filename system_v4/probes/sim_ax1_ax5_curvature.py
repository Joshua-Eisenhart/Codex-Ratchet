#!/usr/bin/env python3
"""
Ax1 vs Ax5 Curvature Separation Test
======================================

Codex correction: the blur proxy was not the real Ax5.

Ax5 proper = curvature class of the evolution trajectory:
  FGA (low curvature): evolution follows straight/gradient-like paths
  FSA (high curvature): evolution follows bent/spectral/curved paths

Ax1 = is the channel open/closed (CPTP vs Unitary)

TEST: On mixed states at varying entropy:
  1. Measure Ax1 as before (CPTP displacement vs Unitary displacement)
  2. Measure Ax5 as GEODESIC CURVATURE of the state trajectory
     under evolution — how much the path bends on the Bloch sphere
  3. Check if they separate

CURVATURE OPERATIONALIZATION:
  Apply a channel to ρ at two different perturbation strengths (ε, 2ε).
  If the trajectory is straight (FGA): ρ(2ε) ≈ 2·ρ(ε) - ρ(0)
  If the trajectory is curved (FSA): ρ(2ε) ≠ 2·ρ(ε) - ρ(0)
  Curvature = ||ρ(2ε) - 2·ρ(ε) + ρ(0)||  (second derivative)
"""

import numpy as np
import scipy.linalg as la
import json, os, sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def make_mixed_state(d, r, rng):
    if d == 2:
        direction = rng.normal(size=3)
        direction /= np.linalg.norm(direction)
        p = r * direction
        sx = np.array([[0,1],[1,0]], dtype=complex)
        sy = np.array([[0,-1j],[1j,0]], dtype=complex)
        sz_mat = np.array([[1,0],[0,-1]], dtype=complex)
        return (np.eye(2, dtype=complex) + p[0]*sx + p[1]*sy + p[2]*sz_mat) / 2
    else:
        psi = rng.normal(size=d) + 1j*rng.normal(size=d)
        psi /= np.linalg.norm(psi)
        rho_pure = np.outer(psi, np.conj(psi))
        rho_mixed = np.eye(d, dtype=complex) / d
        return r * rho_pure + (1-r) * rho_mixed

def ensure_valid(rho):
    rho = (rho+rho.conj().T)/2
    ev, evc = np.linalg.eigh(rho)
    ev = np.maximum(ev, 0)
    rho = evc@np.diag(ev)@evc.conj().T
    tr = np.trace(rho)
    if abs(tr)>1e-12: rho/=tr
    return rho

def normalized_overlap(A, B):
    nA, nB = np.linalg.norm(A,'fro'), np.linalg.norm(B,'fro')
    if nA<1e-12 or nB<1e-12: return 0.0
    return float(abs(np.trace(A.conj().T@B))/(nA*nB))

def von_neumann_entropy(rho):
    ev = np.linalg.eigvalsh(rho)
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(np.maximum(ev, 1e-30))))


# ═══════════════════════════════════════════════════════════════════
# AXES
# ═══════════════════════════════════════════════════════════════════

def ax1_channel_type(rho, d, rng):
    """Ax1: CPTP (open) vs Unitary (closed) displacement."""
    H = rng.normal(size=(d,d)) + 1j*rng.normal(size=(d,d))
    H = (H+H.conj().T)/2; H *= 0.3/max(np.linalg.norm(H),1e-12)
    U = la.expm(-1j*H)
    rho_u = U@rho@U.conj().T
    
    L = np.zeros((d,d), dtype=complex)
    for k in range(d-1): L[k,k+1] = 0.3
    lind = L@rho@L.conj().T - 0.5*(L.conj().T@L@rho + rho@L.conj().T@L)
    rho_c = ensure_valid(rho + lind*0.3)
    return rho_c - rho_u


def ax5_curvature(rho, d, rng):
    """Ax5: Curvature class of evolution trajectory.
    
    HIGH CURVATURE (FSA/spectral/wave):
      Apply a channel that bends the trajectory.
      Signature: big second derivative = ||ρ(2ε) - 2ρ(ε) + ρ(0)||
    
    LOW CURVATURE (FGA/gradient/line):
      Apply a channel that moves the state straight.
      Signature: small second derivative.
    
    Displacement = high_curvature_result - low_curvature_result
    """
    # HIGH CURVATURE: Apply a Hamiltonian with strong off-diagonal terms
    # These create oscillatory/spectral motion = high geodesic curvature
    H_curved = rng.normal(size=(d,d)) + 1j*rng.normal(size=(d,d))
    H_curved = (H_curved + H_curved.conj().T)/2
    H_curved *= 0.5/max(np.linalg.norm(H_curved),1e-12)
    
    eps = 0.2
    U1 = la.expm(-1j*H_curved*eps)
    U2 = la.expm(-1j*H_curved*2*eps)
    rho_eps = U1@rho@U1.conj().T
    rho_2eps = U2@rho@U2.conj().T
    curv_high = rho_2eps - 2*rho_eps + rho  # second derivative
    
    # LOW CURVATURE: Apply dephasing/diagonal channel
    # Dephasing moves state straight toward diagonal = low geodesic curvature
    diag = np.diag(np.diag(rho))
    rho_eps_low = (1-eps)*rho + eps*diag
    rho_2eps_low = (1-2*eps)*rho + 2*eps*diag
    curv_low = rho_2eps_low - 2*rho_eps_low + rho  # second derivative
    
    return curv_high - curv_low


def run():
    n_trials = 200
    d_values = [2, 4, 8]
    r_values = [1.0, 0.9, 0.7, 0.5, 0.3, 0.1, 0.01]
    
    print("=" * 80)
    print("AX1 vs AX5 (CURVATURE): SEPARATION ON MIXED STATES")
    print(f"{n_trials} trials, d={d_values}")
    print("=" * 80)
    print()
    print("  Ax1 = IS the channel open/closed (CPTP vs Unitary)")
    print("  Ax5 = curvature class (FGA: straight/low-curv vs FSA: bent/high-curv)")
    
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
                rng = np.random.default_rng(trial + 900000 + int(r*1000) + d*10000)
                rho = make_mixed_state(d, r, rng)
                
                rng1 = np.random.default_rng(trial + 900000 + int(r*1000) + d*10000 + 1)
                rng5 = np.random.default_rng(trial + 900000 + int(r*1000) + d*10000 + 2)
                
                d1 = ax1_channel_type(rho, d, rng1)
                d5 = ax5_curvature(rho, d, rng5)
                
                total_ax1_norm += np.linalg.norm(d1, 'fro')
                total_ax5_norm += np.linalg.norm(d5, 'fro')
                total_overlap += normalized_overlap(d1, d5)
                total_entropy += von_neumann_entropy(rho)
            
            avg_ov = total_overlap / n_trials
            avg_ax1 = total_ax1_norm / n_trials
            avg_ax5 = total_ax5_norm / n_trials
            avg_S = total_entropy / n_trials
            
            if avg_ov > 0.7:    verdict = "≈ SAME"
            elif avg_ov > 0.3:  verdict = "⚠️ PARTIAL"
            elif avg_ov > 0.1:  verdict = "🔥 SEPARATING"
            else:               verdict = "✅ DISTINCT"
            
            print(f"  {r:>6.2f} {avg_S:>8.3f} {avg_ax1:>10.4f} {avg_ax5:>10.4f} {avg_ov:>10.4f} {verdict}")
            
            all_results[f"d={d},r={r}"] = {
                "d": d, "r": r,
                "entropy": round(avg_S, 4),
                "ax1_norm": round(avg_ax1, 4),
                "ax5_norm": round(avg_ax5, 4),
                "overlap": round(avg_ov, 4),
            }
    
    # Compare with old probe
    print(f"\n{'='*80}")
    print("  COMPARISON: Curvature probe vs Blur probe")
    print(f"{'='*80}")
    
    old_results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "a2_state", "sim_results", "ax1_ax5_separation.json")
    try:
        with open(old_results_path) as f:
            old = json.load(f)["results"]
        print(f"\n  {'':6s} {'d':>3s} {'Old (blur)':>12s} {'New (curv)':>12s} {'Change':>10s}")
        for d in d_values:
            for r in [1.0, 0.5, 0.1, 0.01]:
                key = f"d={d},r={r}"
                old_ov = old.get(key, {}).get("overlap", -1)
                new_ov = all_results[key]["overlap"]
                delta = new_ov - old_ov if old_ov >= 0 else 0
                print(f"  r={r:<4.2f} d={d:>1d} {old_ov:>12.4f} {new_ov:>12.4f} {delta:>10.4f}")
    except (FileNotFoundError, KeyError):
        print("  (old results not found for comparison)")
    
    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "schema": "AX1_AX5_CURVATURE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "results": all_results,
        "note": "Ax5 operationalized as geodesic curvature class, not entropy blur",
    }
    out_file = os.path.join(out_dir, "ax1_ax5_curvature_separation.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results written to {out_file}")


if __name__ == "__main__":
    run()
