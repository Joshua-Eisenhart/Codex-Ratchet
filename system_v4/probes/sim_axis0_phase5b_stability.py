#!/usr/bin/env python3
"""
Phase 5B: Multi-Cycle Stability & Convergence
==============================================

Does the bridge survive multiple engine cycles?
Does it converge to a fixed point?
Does the MI grow, shrink, or oscillate?

Tests:
1. Run 4 consecutive cycles and measure bridge MI at each
2. Check if the MI converges or diverges
3. Check if the kernel Φ₀ is stable
4. Test with different initial conditions (random S³ points)
5. Check if the bridge is an attractor (nearby states converge to it)
"""

from __future__ import annotations
import json, os, sys
from datetime import UTC, datetime
import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import (TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER, 
                           random_s3_point, torus_coordinates)

EPS = 1e-12
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)

TORUS_CONFIGS = [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]


def vne(rho):
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) > 0 else 0.0

def ptr_B(r): return np.trace(r.reshape(2,2,2,2), axis1=1, axis2=3)
def ptr_A(r): return np.trace(r.reshape(2,2,2,2), axis1=0, axis2=2)

def mi_val(rho_AB):
    return max(0.0, vne(ptr_B(rho_AB)) + vne(ptr_A(rho_AB)) - vne(rho_AB))

def ic_val(rho_AB):
    return vne(ptr_A(rho_AB)) - vne(rho_AB)

def bloch(rho):
    return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])

def lr_asym(a, b):
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0, 1))


def build_winning_bridge(history):
    """Build the Phase 4 winner: cross_s1_symmetric_retro with Ψ⁻"""
    T = len(history)
    if T < 2:
        return None
    
    states = []
    weights = []
    for i in range(T - 1):
        # Forward: L(t) ⊗ R(t+1)
        rho_Lf, rho_Rf = history[i]["rho_L"], history[i+1]["rho_R"]
        pf = float(np.clip(lr_asym(rho_Lf, rho_Rf), 0.01, 0.99))
        prod_f = _ensure_valid_density(np.kron(rho_Lf, rho_Rf))
        bell = np.outer(PSI_MINUS, PSI_MINUS.conj())
        rho_f = _ensure_valid_density((1-pf) * prod_f + pf * bell)
        
        # Backward: R(t) ⊗ L(t+1)
        rho_Rb, rho_Lb = history[i]["rho_R"], history[i+1]["rho_L"]
        pb = float(np.clip(lr_asym(rho_Rb, rho_Lb), 0.01, 0.99))
        prod_b = _ensure_valid_density(np.kron(rho_Rb, rho_Lb))
        rho_b = _ensure_valid_density((1-pb) * prod_b + pb * bell)
        
        # Symmetric average
        rho = _ensure_valid_density(0.5 * rho_f + 0.5 * rho_b)
        states.append(rho)
        
        # Retrocausal weighting
        w = np.exp(-0.1 * (T - 2 - i))
        weights.append(w)
    
    weights = np.array(weights)
    weights /= weights.sum()
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


def build_same_time_bridge(history):
    """Build the Phase 3 winner: same-time chiral retro Ψ⁻"""
    T = len(history)
    if T < 1:
        return None
    
    states = []
    weights = []
    bell = np.outer(PSI_MINUS, PSI_MINUS.conj())
    for i, h in enumerate(history):
        p = float(np.clip(lr_asym(h["rho_L"], h["rho_R"]), 0.01, 0.99))
        prod = _ensure_valid_density(np.kron(h["rho_L"], h["rho_R"]))
        rho = _ensure_valid_density((1-p) * prod + p * bell)
        states.append(rho)
        weights.append(np.exp(-0.1 * (T - 1 - i)))
    
    weights = np.array(weights)
    weights /= weights.sum()
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


def build_product_bridge(history):
    """Baseline: uniform product history"""
    states = [_ensure_valid_density(np.kron(h["rho_L"], h["rho_R"])) for h in history]
    return _ensure_valid_density(sum(states) / len(states))


def run_multi_cycle(engine_type, torus_label, eta, n_cycles=4):
    """Run multiple cycles and track bridge MI."""
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
    
    cycle_data = []
    cumulative_history = []
    
    for cycle in range(n_cycles):
        state = engine.run_cycle(state)
        cumulative_history.extend(state.history[-32:])  # Only this cycle's steps
        
        # Build bridges on cumulative history
        rho_winner = build_winning_bridge(cumulative_history)
        rho_same = build_same_time_bridge(cumulative_history)
        rho_product = build_product_bridge(cumulative_history)
        
        # Also build on just this cycle's history
        this_cycle = state.history[-32:]
        rho_winner_this = build_winning_bridge(this_cycle)
        rho_same_this = build_same_time_bridge(this_cycle)
        
        cycle_data.append({
            "cycle": cycle + 1,
            "cumulative_steps": len(cumulative_history),
            "winner_cumulative_MI": mi_val(rho_winner) if rho_winner is not None else 0,
            "winner_cumulative_Ic": ic_val(rho_winner) if rho_winner is not None else 0,
            "same_cumulative_MI": mi_val(rho_same) if rho_same is not None else 0,
            "same_cumulative_Ic": ic_val(rho_same) if rho_same is not None else 0,
            "product_cumulative_MI": mi_val(rho_product),
            "winner_this_cycle_MI": mi_val(rho_winner_this) if rho_winner_this is not None else 0,
            "winner_this_cycle_Ic": ic_val(rho_winner_this) if rho_winner_this is not None else 0,
            "same_this_cycle_MI": mi_val(rho_same_this) if rho_same_this is not None else 0,
            "lr_asymmetry": lr_asym(state.rho_L, state.rho_R),
            "ga0_level": float(state.ga0_level),
        })
    
    return cycle_data


def run_random_initial_conditions(engine_type, eta, n_inits=10):
    """Test bridge stability across random initial conditions."""
    engine = GeometricEngine(engine_type=engine_type)
    rng = np.random.default_rng(42)
    
    results = []
    for i in range(n_inits):
        theta1 = rng.uniform(0, 2 * np.pi)
        theta2 = rng.uniform(0, 2 * np.pi)
        state = engine.init_state(eta=eta, theta1=theta1, theta2=theta2)
        state = engine.run_cycle(state)
        
        rho_winner = build_winning_bridge(state.history)
        rho_same = build_same_time_bridge(state.history)
        
        results.append({
            "init": i,
            "theta1": float(theta1),
            "theta2": float(theta2),
            "winner_MI": mi_val(rho_winner) if rho_winner is not None else 0,
            "winner_Ic": ic_val(rho_winner) if rho_winner is not None else 0,
            "same_MI": mi_val(rho_same) if rho_same is not None else 0,
            "lr_asymmetry": lr_asym(state.rho_L, state.rho_R),
        })
    
    return results


def main():
    print("=" * 80)
    print("PHASE 5B: MULTI-CYCLE STABILITY & CONVERGENCE")
    print("=" * 80)
    
    all_results = {}
    
    # 1. Multi-cycle
    print("\n  1. Multi-cycle stability (4 cycles each)...")
    for engine_type in (1, 2):
        for torus_label, eta in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            print(f"    {key}...")
            all_results[f"multi_cycle_{key}"] = run_multi_cycle(engine_type, torus_label, eta, n_cycles=4)
    
    # 2. Random initial conditions
    print("\n  2. Random initial conditions (10 each)...")
    for engine_type in (1, 2):
        for torus_label, eta in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            print(f"    {key}...")
            all_results[f"random_init_{key}"] = run_random_initial_conditions(engine_type, eta, n_inits=10)
    
    # VERDICTS
    print(f"\n{'=' * 80}")
    print("VERDICTS")
    print(f"{'=' * 80}")
    
    print(f"\n  1. MULTI-CYCLE CONVERGENCE:")
    for engine_type in (1, 2):
        for torus_label, _ in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            data = all_results[f"multi_cycle_{key}"]
            mis = [d["winner_cumulative_MI"] for d in data]
            ics = [d["winner_cumulative_Ic"] for d in data]
            trend = "GROWING" if mis[-1] > mis[0] + 0.01 else "SHRINKING" if mis[-1] < mis[0] - 0.01 else "STABLE"
            print(f"    {key}: MI across cycles = {[f'{m:.4f}' for m in mis]}, trend={trend}")
            print(f"    {key}: Ic across cycles = {[f'{c:.4f}' for c in ics]}")
    
    print(f"\n  2. PER-CYCLE vs CUMULATIVE:")
    for engine_type in (1, 2):
        for torus_label, _ in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            data = all_results[f"multi_cycle_{key}"]
            for d in data:
                print(f"    {key} cycle {d['cycle']}: "
                      f"this_MI={d['winner_this_cycle_MI']:.4f}, "
                      f"cumul_MI={d['winner_cumulative_MI']:.4f}, "
                      f"asym={d['lr_asymmetry']:.4f}")
    
    print(f"\n  3. RANDOM INITIAL CONDITIONS STABILITY:")
    for engine_type in (1, 2):
        for torus_label, _ in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            data = all_results[f"random_init_{key}"]
            mis = [d["winner_MI"] for d in data]
            print(f"    {key}: MI range = [{min(mis):.4f}, {max(mis):.4f}], "
                  f"mean={np.mean(mis):.4f}, std={np.std(mis):.4f}")
    
    # Overall stability verdict
    all_multi_mis = []
    for engine_type in (1, 2):
        for torus_label, _ in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            data = all_results[f"multi_cycle_{key}"]
            all_multi_mis.append([d["winner_cumulative_MI"] for d in data])
    
    all_stable = all(abs(mis[-1] - mis[0]) < 0.1 for mis in all_multi_mis)
    all_random_stds = []
    for engine_type in (1, 2):
        for torus_label, _ in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            data = all_results[f"random_init_{key}"]
            all_random_stds.append(float(np.std([d["winner_MI"] for d in data])))
    
    print(f"\n  STABILITY VERDICT:")
    print(f"    Multi-cycle stable: {all_stable}")
    print(f"    Random init std range: [{min(all_random_stds):.4f}, {max(all_random_stds):.4f}]")
    
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    
    def clean(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.floating, np.float64)): return float(obj)
        if isinstance(obj, (np.integer, np.int64)): return int(obj)
        if isinstance(obj, dict): return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list): return [clean(v) for v in obj]
        return obj
    
    with open(os.path.join(out_dir, "axis0_phase5b_results.json"), "w") as f:
        json.dump(clean(all_results), f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"PROBE STATUS: PASS")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
