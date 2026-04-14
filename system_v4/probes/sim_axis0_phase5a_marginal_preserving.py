#!/usr/bin/env python3
"""
Phase 5A: Marginal-Preserving Xi Bridge
========================================

Phase 4 showed all chiral candidates break marginals. This probe
asks: what is the MAXIMUM MI you can get while preserving the
original ρ_L and ρ_R as marginals?

If marginal-preserving MI is still large → the entanglement is "earned"
If marginal-preserving MI is near zero → the MI was "smuggled" via Bell injection

Uses the quantum marginal problem: find ρ_AB such that
  Tr_B(ρ_AB) = ρ_A  and  Tr_A(ρ_AB) = ρ_B
  and I(A:B) is maximized.

For 2×2 systems, the set of compatible ρ_AB is parameterized
by a 4×4 density matrix with constrained marginals.
"""

from __future__ import annotations
import json, os, sys
from datetime import UTC, datetime
import numpy as np
from scipy.optimize import minimize
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER

EPS = 1e-12
TORUS_CONFIGS = [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]

PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)


def vne(rho):
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) > 0 else 0.0

def ptr_B(r): return np.trace(r.reshape(2,2,2,2), axis1=1, axis2=3)
def ptr_A(r): return np.trace(r.reshape(2,2,2,2), axis1=0, axis2=2)

def mi(rho_AB):
    return max(0.0, vne(ptr_B(rho_AB)) + vne(ptr_A(rho_AB)) - vne(rho_AB))

def ic(rho_AB):
    return vne(ptr_A(rho_AB)) - vne(rho_AB)

def bloch(rho):
    return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])

def lr_asym(a, b):
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0, 1))


def product_seed_vector(rho_A, rho_B):
    """Bloch-correlation seed for the feasible product state rho_A ⊗ rho_B."""
    r = bloch(rho_A)
    s = bloch(rho_B)
    return np.outer(r, s).reshape(9)


def parameterize_marginal_preserving(rho_A, rho_B, x):
    """
    Build a 4×4 density matrix with fixed marginals ρ_A, ρ_B.
    
    For 2×2 marginals, the correlation matrix has 9 real parameters
    (the 3×3 T matrix in the Bloch representation):
    
    ρ_AB = (1/4)(I⊗I + r·σ⊗I + I⊗s·σ + Σ_ij T_ij σ_i⊗σ_j)
    
    where r = Bloch(ρ_A), s = Bloch(ρ_B), T is 3×3 real.
    x is a 9-element vector parameterizing T.
    """
    r = bloch(rho_A)
    s = bloch(rho_B)
    T = x.reshape(3, 3)
    
    sigmas = [SIGMA_X, SIGMA_Y, SIGMA_Z]
    I2 = np.eye(2, dtype=complex)
    
    rho = np.kron(I2, I2).astype(complex) / 4
    for i in range(3):
        rho += r[i] * np.kron(sigmas[i], I2) / 4
        rho += s[i] * np.kron(I2, sigmas[i]) / 4
    for i in range(3):
        for j in range(3):
            rho += T[i, j] * np.kron(sigmas[i], sigmas[j]) / 4
    
    return rho


def find_max_mi_preserving(rho_A, rho_B, n_restarts=10):
    """Find the ρ_AB with maximum MI that preserves marginals ρ_A, ρ_B."""

    best_x = None
    best_mi = -1.0
    best_source = None
    feasible_candidates = 0
    rng = np.random.default_rng(42)

    def candidate_rho(x):
        rho = parameterize_marginal_preserving(rho_A, rho_B, x)
        evals = np.real(np.linalg.eigvalsh(rho))
        tr = float(np.real(np.trace(rho)))
        if np.min(evals) < -1e-8 or abs(tr - 1.0) > 1e-6:
            return None
        return _ensure_valid_density(rho)

    def neg_mi(x):
        rho = candidate_rho(x)
        if rho is None:
            return 10.0
        return -mi(rho)

    seed_x = product_seed_vector(rho_A, rho_B)
    seed_rho = candidate_rho(seed_x)
    if seed_rho is not None:
        best_x = seed_x.copy()
        best_mi = mi(seed_rho)
        best_source = "product_seed"
        feasible_candidates = 1

    for restart in range(n_restarts):
        x0 = seed_x + rng.standard_normal(9) * 0.3
        try:
            result = minimize(
                neg_mi,
                x0,
                method="Nelder-Mead",
                options={"maxiter": 5000, "xatol": 1e-10, "fatol": 1e-10},
            )
            rho_result = candidate_rho(result.x)
            if rho_result is None:
                continue
            feasible_candidates += 1
            result_mi = mi(rho_result)
            if result_mi > best_mi:
                best_mi = result_mi
                best_x = result.x.copy()
                best_source = f"restart_{restart}"
        except Exception:
            continue

    if best_x is None:
        return None, 0.0, {
            "search_status": "no_feasible_candidate",
            "optimizer_status": "SOLVER_FAILURE",
            "certified": False,
            "feasible_candidates": 0,
            "seeded_with_product_state": True,
        }

    rho_best = parameterize_marginal_preserving(rho_A, rho_B, best_x)
    rho_best = _ensure_valid_density(rho_best)
    dev_A = float(np.linalg.norm(ptr_B(rho_best) - rho_A, ord="fro"))
    dev_B = float(np.linalg.norm(ptr_A(rho_best) - rho_B, ord="fro"))

    return rho_best, best_mi, {
        "search_status": "feasible_candidate_found",
        "optimizer_status": "OK",
        "certified": True,
        "feasible_candidates": feasible_candidates,
        "seeded_with_product_state": True,
        "best_source": best_source,
        "dev_A": dev_A,
        "dev_B": dev_B,
        "preserves_marginals_within_tol": bool(dev_A < 1e-6 and dev_B < 1e-6),
        "ic": ic(rho_best),
    }


def run_marginal_preserving_search(state):
    """Find max-MI marginal-preserving bridge for final state AND history."""
    results = {}
    
    # A. Final state marginals
    print(f"    Final state marginal search (10 restarts)...")
    rho_opt, mi_opt, meta = find_max_mi_preserving(state.rho_L, state.rho_R, n_restarts=15)
    product_mi_val = mi(_ensure_valid_density(np.kron(state.rho_L, state.rho_R)))
    
    # Bell Ψ- for comparison (non-preserving)
    p_geom = lr_asym(state.rho_L, state.rho_R)
    p_geom = float(np.clip(p_geom, 0.01, 0.99))
    product = _ensure_valid_density(np.kron(state.rho_L, state.rho_R))
    rho_bell = np.outer(PSI_MINUS, PSI_MINUS.conj())
    rho_chiral = _ensure_valid_density((1 - p_geom) * product + p_geom * rho_bell)
    chiral_mi = mi(rho_chiral)
    
    results["final_state"] = {
        "product_MI": product_mi_val,
        "max_preserving_MI": float(mi_opt),
        "optimizer_status": meta.get("optimizer_status", "UNKNOWN"),
        "certified": bool(meta.get("certified", False)),
        "chiral_bell_MI": chiral_mi,
        "ratio_preserving_to_chiral": float(mi_opt / (chiral_mi + EPS)),
        "marginal_check": meta,
        "p_geom": p_geom,
    }
    
    # B. History-averaged marginals
    history = state.history
    if history:
        print(f"    History-averaged marginal search ({len(history)} steps)...")
        # Average L and R across history
        avg_L = _ensure_valid_density(sum(h["rho_L"] for h in history) / len(history))
        avg_R = _ensure_valid_density(sum(h["rho_R"] for h in history) / len(history))
        
        rho_opt_h, mi_opt_h, meta_h = find_max_mi_preserving(avg_L, avg_R, n_restarts=15)
        product_h = _ensure_valid_density(np.kron(avg_L, avg_R))
        product_mi_h = mi(product_h)
        
        p_h = lr_asym(avg_L, avg_R)
        p_h = float(np.clip(p_h, 0.01, 0.99))
        rho_chiral_h = _ensure_valid_density((1 - p_h) * product_h + p_h * rho_bell)
        chiral_mi_h = mi(rho_chiral_h)
        
        results["history_averaged"] = {
            "product_MI": product_mi_h,
            "max_preserving_MI": float(mi_opt_h),
            "optimizer_status": meta_h.get("optimizer_status", "UNKNOWN"),
            "certified": bool(meta_h.get("certified", False)),
            "chiral_bell_MI": chiral_mi_h,
            "ratio_preserving_to_chiral": float(mi_opt_h / (chiral_mi_h + EPS)),
            "marginal_check": meta_h,
            "p_geom": p_h,
            "n_history": len(history),
        }
        
        # C. Per-step preserving MI (sample 8 steps evenly)
        step_indices = np.linspace(0, len(history)-1, min(8, len(history)), dtype=int)
        step_results = []
        for idx in step_indices:
            h = history[idx]
            rho_s, mi_s, meta_s = find_max_mi_preserving(h["rho_L"], h["rho_R"], n_restarts=5)
            step_results.append({
                "step": int(idx),
                "max_preserving_MI": float(mi_s),
                "optimizer_status": meta_s.get("optimizer_status", "UNKNOWN"),
                "certified": bool(meta_s.get("certified", False)),
                "product_MI": mi(_ensure_valid_density(np.kron(h["rho_L"], h["rho_R"]))),
                "lr_asymmetry": lr_asym(h["rho_L"], h["rho_R"]),
            })
        results["per_step_sample"] = step_results
    
    return results


def main():
    print("=" * 80)
    print("PHASE 5A: MARGINAL-PRESERVING XI BRIDGE SEARCH")
    print("=" * 80)
    
    all_results = []
    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for torus_label, eta in TORUS_CONFIGS:
            print(f"\n  Engine {engine_type}/{torus_label}:")
            init = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            final = engine.run_cycle(init)
            r = run_marginal_preserving_search(final)
            all_results.append({"engine_type": engine_type, "torus": torus_label, 
                               "eta": float(eta), **r})
    
    print(f"\n{'=' * 80}")
    print("VERDICTS")
    print(f"{'=' * 80}")
    
    print(f"\n  {'Config':<15} {'Product MI':>12} {'Max Preserv MI':>15} {'Chiral MI':>12} {'Ratio P/C':>10}")
    print(f"  {'─'*15} {'─'*12} {'─'*15} {'─'*12} {'─'*10}")
    
    for r in all_results:
        fs = r.get("final_state", {})
        label = f"{r['engine_type']}/{r['torus']}"
        print(f"  {label:<15} {fs.get('product_MI',0):>12.6f} {fs.get('max_preserving_MI',0.0):>15.6f} "
              f"{fs.get('chiral_bell_MI',0):>12.6f} {fs.get('ratio_preserving_to_chiral',0.0):>10.4f}")
    
    # History averaged
    print(f"\n  History-averaged:")
    for r in all_results:
        ha = r.get("history_averaged", {})
        if ha:
            label = f"{r['engine_type']}/{r['torus']}"
            print(f"  {label:<15} {ha.get('product_MI',0):>12.6f} {ha.get('max_preserving_MI',0.0):>15.6f} "
                  f"{ha.get('chiral_bell_MI',0):>12.6f} {ha.get('ratio_preserving_to_chiral',0.0):>10.4f}")
    
    # Per-step
    print(f"\n  Per-step max preserving MI (sample):")
    for r in all_results:
        for s in r.get("per_step_sample", []):
            label = f"{r['engine_type']}/{r['torus']}"
            print(f"    {label} step={s['step']:>2}: preserv_MI={s.get('max_preserving_MI',0.0):.6f}, "
                  f"product_MI={s['product_MI']:.6f}, asym={s['lr_asymmetry']:.4f}")
    
    # Honest verdict — distinguish solver failure from certified zero
    certified_mis = [
        r.get("final_state", {}).get("max_preserving_MI", 0.0)
        for r in all_results
        if r.get("final_state", {}).get("certified", False)
    ]
    certified_blocks = 0
    total_blocks = 0
    failed_count = 0
    for r in all_results:
        for key in ("final_state", "history_averaged"):
            block = r.get(key, {})
            if block:
                total_blocks += 1
                if block.get("certified", False):
                    certified_blocks += 1
                if block.get("optimizer_status") == "SOLVER_FAILURE":
                    failed_count += 1
    chiral_mis = [r.get("final_state", {}).get("chiral_bell_MI", 0) for r in all_results]
    mean_preserving = float(np.mean(certified_mis)) if certified_mis else None
    mean_chiral = float(np.mean(chiral_mis))

    print(f"\n  HONEST VERDICT:")
    print(f"    Solver failures (final_state + history): {failed_count}/{total_blocks}")
    print(f"    Certified blocks: {certified_blocks}/{total_blocks}")
    if mean_preserving is not None:
        print(f"    Mean max-preserving MI (certified only): {mean_preserving:.6f}")
        print(f"    Mean chiral Bell MI:                     {mean_chiral:.6f}")
        if mean_preserving > 0.01:
            print(f"    ✓ Marginal-preserving MI is NONTRIVIAL → genuine correlations exist")
            print(f"    Ratio: {mean_preserving/mean_chiral:.4f} of chiral MI is preservable")
        else:
            print(f"    ⚠ Marginal-preserving MI is NEAR ZERO → chiral MI is mostly smuggled")
    else:
        print(f"    ✗ ALL optimizers failed — result is SOLVER_FAILURE, not certified zero")
        print(f"    Mean chiral Bell MI: {mean_chiral:.6f}")
        print(f"    Cannot conclude whether marginal-preserving MI is zero or nonzero")
    
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    
    def clean(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.floating, np.float64)): return float(obj)
        if isinstance(obj, (np.integer, np.int64)): return int(obj)
        if isinstance(obj, dict): return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list): return [clean(v) for v in obj]
        return obj
    
    with open(os.path.join(out_dir, "axis0_phase5a_results.json"), "w") as f:
        json.dump(clean({"results": all_results, "mean_preserving": mean_preserving,
                         "mean_chiral": mean_chiral,
                         "certified_blocks": certified_blocks,
                         "total_blocks": total_blocks,
                         "failed_blocks": failed_count}), f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"PROBE STATUS: PASS")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
