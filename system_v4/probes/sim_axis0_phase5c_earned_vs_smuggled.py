#!/usr/bin/env python3
"""
Phase 5C: Earned vs Smuggled Discriminator
==========================================

The definitive test: is the chiral bridge MI earned or smuggled?

Three tests:
1. INFORMATION DECOMPOSITION: How much MI comes from the Bell injection
   vs how much comes from the geometry/history structure?
   
2. SCRAMBLE TEST: Randomly permute the history order. If MI survives
   scrambling, the information is in the individual states (earned).
   If MI drops after scrambling, the information is in the temporal
   ordering (structure-dependent).

3. DECOUPLED TEST: Build the bridge from TWO INDEPENDENT engine runs.
   If MI survives, it's purely from Bell injection (smuggled).
   If MI drops, the correlation between L and R matters (earned).

4. GEOMETRY RAMP: Slowly increase the geometry contribution while
   keeping Bell injection constant. Does MI track geometry or Bell?
"""

from __future__ import annotations
import json, os, sys
from datetime import UTC, datetime
import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this tests earned-vs-smuggled Axis-0 bridge information numerically, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "scramble, decoupled, and decomposition bridge numerics"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER

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
def mi_val(rho): return max(0.0, vne(ptr_B(rho)) + vne(ptr_A(rho)) - vne(rho))
def ic_val(rho): return vne(ptr_A(rho)) - vne(rho)
def bloch(rho): return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])
def lr_asym(a, b): return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0, 1))


def build_bridge(history, use_bell=True, p_override=None, scramble=False, rng=None):
    """
    Configurable bridge builder.
    use_bell=False: product states only (no Bell injection)
    p_override: fixed p instead of geometry-derived
    scramble: randomly permute history order
    """
    T = len(history)
    if T < 2:
        return None
    
    hist = list(history)
    if scramble and rng is not None:
        rng.shuffle(hist)
    
    bell = np.outer(PSI_MINUS, PSI_MINUS.conj())
    states = []
    weights = []
    
    for i in range(T - 1):
        # Symmetric cross-temporal
        rho_Lf, rho_Rf = hist[i]["rho_L"], hist[i+1]["rho_R"]
        rho_Rb, rho_Lb = hist[i]["rho_R"], hist[i+1]["rho_L"]
        
        if use_bell:
            pf = p_override if p_override is not None else float(np.clip(lr_asym(rho_Lf, rho_Rf), 0.01, 0.99))
            pb = p_override if p_override is not None else float(np.clip(lr_asym(rho_Rb, rho_Lb), 0.01, 0.99))
            prod_f = _ensure_valid_density(np.kron(rho_Lf, rho_Rf))
            prod_b = _ensure_valid_density(np.kron(rho_Rb, rho_Lb))
            rho_f = _ensure_valid_density((1-pf) * prod_f + pf * bell)
            rho_b = _ensure_valid_density((1-pb) * prod_b + pb * bell)
        else:
            rho_f = _ensure_valid_density(np.kron(rho_Lf, rho_Rf))
            rho_b = _ensure_valid_density(np.kron(rho_Rb, rho_Lb))
        
        rho = _ensure_valid_density(0.5 * rho_f + 0.5 * rho_b)
        states.append(rho)
        weights.append(np.exp(-0.1 * (T - 2 - i)))
    
    weights = np.array(weights)
    weights /= weights.sum()
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


def test1_information_decomposition(history):
    """Decompose MI into Bell contribution vs geometry contribution."""
    results = {}
    
    # Full bridge (Bell + geometry p)
    rho_full = build_bridge(history, use_bell=True)
    if rho_full is None:
        return {"error": "insufficient history"}
    results["full_MI"] = mi_val(rho_full)
    results["full_Ic"] = ic_val(rho_full)
    
    # Product only (no Bell)
    rho_product = build_bridge(history, use_bell=False)
    results["product_MI"] = mi_val(rho_product)
    results["product_Ic"] = ic_val(rho_product)
    
    # Bell at fixed p values (to isolate Bell contribution)
    for p_fix in [0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0]:
        rho_fixed = build_bridge(history, use_bell=True, p_override=p_fix)
        results[f"bell_p{p_fix:.1f}_MI"] = mi_val(rho_fixed)
        results[f"bell_p{p_fix:.1f}_Ic"] = ic_val(rho_fixed)
    
    # Decomposition
    bell_contribution = results["full_MI"] - results["product_MI"]
    results["bell_contribution_MI"] = bell_contribution
    results["geometry_base_MI"] = results["product_MI"]
    results["bell_fraction"] = bell_contribution / (results["full_MI"] + EPS)
    
    return results


def test2_scramble(history, n_scrambles=20):
    """Test whether temporal ordering matters."""
    rng = np.random.default_rng(42)
    
    # Ordered
    rho_ordered = build_bridge(history, use_bell=True)
    ordered_mi = mi_val(rho_ordered)
    ordered_ic = ic_val(rho_ordered)
    
    # Scrambled (multiple trials)
    scrambled_mis = []
    scrambled_ics = []
    for _ in range(n_scrambles):
        rho_s = build_bridge(history, use_bell=True, scramble=True, rng=rng)
        if rho_s is not None:
            scrambled_mis.append(mi_val(rho_s))
            scrambled_ics.append(ic_val(rho_s))
    
    scrambled_mean = float(np.mean(scrambled_mis))
    scrambled_std = float(np.std(scrambled_mis))
    sigma_band = 2 * scrambled_std
    delta = ordered_mi - scrambled_mean
    ordered_better = bool(delta > sigma_band)
    scramble_better = bool(delta < -sigma_band)
    no_material_difference = not (ordered_better or scramble_better)
    ordering_direction = (
        "ordered_better" if ordered_better
        else "scramble_better" if scramble_better
        else "no_material_difference"
    )

    return {
        "ordered_MI": ordered_mi,
        "ordered_Ic": ordered_ic,
        "scrambled_mean_MI": scrambled_mean,
        "scrambled_std_MI": scrambled_std,
        "scrambled_min_MI": float(np.min(scrambled_mis)),
        "scrambled_max_MI": float(np.max(scrambled_mis)),
        "ordering_matters": ordered_better,
        "ordered_better": ordered_better,
        "scramble_better": scramble_better,
        "no_material_difference": no_material_difference,
        "ordering_direction": ordering_direction,
        "ordering_effect_sigma_band": sigma_band,
        "mi_drop_from_scramble": delta,
        "mi_drop_fraction": delta / (ordered_mi + EPS),
    }


def test3_decoupled(engine_type, eta):
    """Build bridge from two independent engine runs."""
    engine = GeometricEngine(engine_type=engine_type)
    
    # Run A
    state_A = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
    state_A = engine.run_cycle(state_A)
    
    # Run B (different initial angles)
    state_B = engine.init_state(eta=eta, theta1=np.pi/3, theta2=np.pi/5)
    state_B = engine.run_cycle(state_B)
    
    # Coupled bridge (same run): use run A's history
    rho_coupled = build_bridge(state_A.history, use_bell=True)
    coupled_mi = mi_val(rho_coupled) if rho_coupled is not None else 0
    
    # Decoupled bridge: take L from run A, R from run B
    T = min(len(state_A.history), len(state_B.history))
    decoupled_history = []
    for i in range(T):
        decoupled_history.append({
            "rho_L": state_A.history[i]["rho_L"],
            "rho_R": state_B.history[i]["rho_R"],
            "dphi_L": state_A.history[i].get("dphi_L", 0),
            "dphi_R": state_B.history[i].get("dphi_R", 0),
            "loop_role": state_A.history[i].get("loop_role", "heating"),
            "loop_position": state_A.history[i].get("loop_position", "inner"),
        })
    
    rho_decoupled = build_bridge(decoupled_history, use_bell=True)
    decoupled_mi = mi_val(rho_decoupled) if rho_decoupled is not None else 0
    
    # Product decoupled (no Bell)
    rho_dec_product = build_bridge(decoupled_history, use_bell=False)
    dec_product_mi = mi_val(rho_dec_product) if rho_dec_product is not None else 0
    
    return {
        "coupled_MI": coupled_mi,
        "decoupled_MI": decoupled_mi,
        "decoupled_product_MI": dec_product_mi,
        "coupling_matters": bool(abs(coupled_mi - decoupled_mi) > 0.01),
        "mi_drop_from_decoupling": coupled_mi - decoupled_mi,
        "mi_drop_fraction": (coupled_mi - decoupled_mi) / (coupled_mi + EPS),
        "bell_contribution_in_decoupled": decoupled_mi - dec_product_mi,
    }


def test4_geometry_ramp(history):
    """Ramp geometry contribution while keeping Bell constant at p=0.5."""
    ramp_results = []
    
    # Fix p at various values, use geometry-ordered history
    for p in np.linspace(0.0, 1.0, 21):
        if p < 0.001:
            rho = build_bridge(history, use_bell=False)
        elif p > 0.999:
            # Pure Bell, no product
            rho = build_bridge(history, use_bell=True, p_override=1.0)
        else:
            rho = build_bridge(history, use_bell=True, p_override=float(p))
        
        if rho is not None:
            ramp_results.append({
                "p": float(p),
                "MI": mi_val(rho),
                "Ic": ic_val(rho),
            })
    
    return ramp_results


def main():
    print("=" * 80)
    print("PHASE 5C: EARNED vs SMUGGLED DISCRIMINATOR")
    print("=" * 80)
    
    all_results = {}
    
    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for torus_label, eta in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            print(f"\n  {key}:")
            
            state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            state = engine.run_cycle(state)
            
            print(f"    Test 1: Information decomposition...")
            all_results[f"decomp_{key}"] = test1_information_decomposition(state.history)
            
            print(f"    Test 2: Scramble test (20 trials)...")
            all_results[f"scramble_{key}"] = test2_scramble(state.history)
            
            print(f"    Test 3: Decoupled test...")
            all_results[f"decouple_{key}"] = test3_decoupled(engine_type, eta)
            
            print(f"    Test 4: Geometry ramp (21 points)...")
            all_results[f"ramp_{key}"] = test4_geometry_ramp(state.history)
    
    # VERDICTS
    print(f"\n{'=' * 80}")
    print("VERDICTS")
    print(f"{'=' * 80}")
    
    print(f"\n  1. INFORMATION DECOMPOSITION:")
    for engine_type in (1, 2):
        for torus_label, _ in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            d = all_results[f"decomp_{key}"]
            print(f"    {key}: full_MI={d['full_MI']:.4f}, product_MI={d['product_MI']:.4f}, "
                  f"bell_contrib={d['bell_contribution_MI']:.4f} ({d['bell_fraction']:.1%} from Bell)")
    
    print(f"\n  2. SCRAMBLE TEST:")
    for engine_type in (1, 2):
        for torus_label, _ in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            s = all_results[f"scramble_{key}"]
            print(f"    {key}: ordered={s['ordered_MI']:.4f}, scrambled={s['scrambled_mean_MI']:.4f}±{s['scrambled_std_MI']:.4f}, "
                  f"drop={s['mi_drop_from_scramble']:.4f} ({s['mi_drop_fraction']:.1%}), "
                  f"ordering_matters={s['ordering_matters']}")
    
    print(f"\n  3. DECOUPLED TEST:")
    for engine_type in (1, 2):
        for torus_label, _ in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            dc = all_results[f"decouple_{key}"]
            print(f"    {key}: coupled={dc['coupled_MI']:.4f}, decoupled={dc['decoupled_MI']:.4f}, "
                  f"drop={dc['mi_drop_from_decoupling']:.4f} ({dc['mi_drop_fraction']:.1%}), "
                  f"coupling_matters={dc['coupling_matters']}")
    
    print(f"\n  4. GEOMETRY RAMP (sample):")
    for engine_type in (1, 2):
        for torus_label, _ in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            ramp = all_results[f"ramp_{key}"]
            # Show p=0, 0.25, 0.5, 0.75, 1.0
            for r in ramp:
                if r["p"] in [0.0, 0.25, 0.5, 0.75, 1.0]:
                    print(f"    {key}: p={r['p']:.2f} → MI={r['MI']:.4f}, Ic={r['Ic']:.4f}")
    
    # OVERALL HONEST VERDICT
    print(f"\n{'=' * 80}")
    print("OVERALL HONEST VERDICT: EARNED vs SMUGGLED")
    print(f"{'=' * 80}")
    
    # Aggregate
    bell_fractions = [all_results[f"decomp_{et}/{tl}"]["bell_fraction"] 
                      for et in (1,2) for tl, _ in TORUS_CONFIGS]
    scramble_drops = [all_results[f"scramble_{et}/{tl}"]["mi_drop_fraction"] 
                      for et in (1,2) for tl, _ in TORUS_CONFIGS]
    ordering_directions = [all_results[f"scramble_{et}/{tl}"]["ordering_direction"]
                           for et in (1,2) for tl, _ in TORUS_CONFIGS]
    decouple_drops = [all_results[f"decouple_{et}/{tl}"]["mi_drop_fraction"] 
                      for et in (1,2) for tl, _ in TORUS_CONFIGS]
    
    mean_bell_frac = float(np.mean(bell_fractions))
    mean_scramble_drop = float(np.mean(scramble_drops))
    mean_decouple_drop = float(np.mean(decouple_drops))
    ordered_better_count = sum(1 for x in ordering_directions if x == "ordered_better")
    scramble_better_count = sum(1 for x in ordering_directions if x == "scramble_better")
    neutral_count = sum(1 for x in ordering_directions if x == "no_material_difference")
    
    print(f"\n  Mean Bell fraction of total MI:     {mean_bell_frac:.1%}")
    print(f"  Mean MI drop from scrambling:       {mean_scramble_drop:.1%}")
    print(f"  Mean MI drop from decoupling:       {mean_decouple_drop:.1%}")
    print(f"  Ordering directions:                ordered_better={ordered_better_count}, scramble_better={scramble_better_count}, neutral={neutral_count}")
    
    if mean_bell_frac > 0.95:
        print(f"\n  ⚠ VERDICT: MI is >95% from Bell injection → MOSTLY SMUGGLED")
        print(f"    The chiral bridge creates correlations, it doesn't discover them.")
    elif mean_bell_frac > 0.5:
        print(f"\n  ◐ VERDICT: MI is {mean_bell_frac:.0%} from Bell → PARTIALLY EARNED")
        print(f"    Bell injection creates the structure, but geometry parameterizes it meaningfully.")
    else:
        print(f"\n  ✓ VERDICT: MI is {1-mean_bell_frac:.0%} from geometry → MOSTLY EARNED")
    
    if mean_scramble_drop > 0.1:
        print(f"    ✓ Temporal ordering contributes {mean_scramble_drop:.1%} → order matters")
    else:
        print(f"    ⚠ Temporal ordering contributes only {mean_scramble_drop:.1%} → order doesn't matter much")
    
    if mean_decouple_drop > 0.1:
        print(f"    ✓ L/R coupling contributes {mean_decouple_drop:.1%} → coupling matters") 
    else:
        print(f"    ⚠ L/R coupling contributes only {mean_decouple_drop:.1%} → decoupled runs match")
    
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    
    def clean(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.floating, np.float64)): return float(obj)
        if isinstance(obj, (np.integer, np.int64)): return int(obj)
        if isinstance(obj, dict): return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list): return [clean(v) for v in obj]
        return obj
    
    with open(os.path.join(out_dir, "axis0_phase5c_results.json"), "w") as f:
        json.dump(clean(all_results), f, indent=2)
    
    print(f"\n{'=' * 80}")
    print(f"PROBE STATUS: PASS")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
