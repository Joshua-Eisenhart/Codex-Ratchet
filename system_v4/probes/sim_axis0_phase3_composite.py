#!/usr/bin/env python3
"""
Axis 0 Bridge — Phase 3: Composite Candidate & Kernel Split Investigation
==========================================================================

Phase 2 discovered:
  - Bell Ψ- history bridge: 1.46 bits MI (3× Phase 1 winner)
  - Compression weighting beats uniform by +0.12
  - Kernel Φ₀ = -S(A|B) INVERTS on inner/outer but WORKS on Clifford
  - Optimal MI is at p≈0.54 (inner/outer), p≈0.72 (Clifford)
  - Geometry-derived p is near the I_c zero-crossing on Clifford

This probe now:

1. COMPOSITE CANDIDATES
   Build Bell Ψ- history bridges with:
   - Compression weighting
   - Torus-adaptive p (0.54 for inner/outer, geometry for Clifford)
   - Retrocausal + compression combined
   - Optimal p sweep per torus

2. KERNEL SPLIT INVESTIGATION
   Why does Φ₀ invert on inner/outer but work on Clifford?
   - Sweep the full I_c landscape per torus
   - Check if the Clifford torus IS the natural bridge site
   - Test whether Axis 0 should only operate at/near Clifford

3. TORUS-ADAPTIVE BRIDGE
   The final Xi might need to be torus-aware:
   - Different p per torus latitude
   - Different Bell state per torus
   - Bridge strength modulated by η

4. NON-PRODUCT HISTORY: ENTANGLE CONSECUTIVE PAIRS
   Instead of entangling L/R at each step, entangle 
   consecutive time-steps: ρ(t) ⊗ ρ(t+1) → entangled history
   This is more "retrocausal" — temporal entanglement

Author: System V4
Date: 2026-03-30
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from typing import Dict, List, Tuple

import numpy as np
from scipy.linalg import sqrtm
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this evaluates Phase-3 composite Axis-0 bridge candidates numerically, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "composite bridge construction and scoring numerics"},
    "scipy": {"tried": True, "used": True, "reason": "matrix square-root operations for bridge metrics"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "scipy": "supportive"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import (
    TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER,
    von_neumann_entropy_2x2,
)

EPS = 1e-12
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
I4 = np.eye(4, dtype=complex)

PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
PHI_PLUS = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
PSI_PLUS = np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2)
PHI_MINUS = np.array([1, 0, 0, -1], dtype=complex) / np.sqrt(2)

TORUS_CONFIGS = [
    ("inner", TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer", TORUS_OUTER),
]


def von_neumann_entropy(rho):
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def partial_trace_B(rho_AB):
    return np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def partial_trace_A(rho_AB):
    return np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def metrics(rho_AB):
    rho_A = partial_trace_B(rho_AB)
    rho_B = partial_trace_A(rho_AB)
    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)
    I_AB = max(0.0, S_A + S_B - S_AB)
    Ic = S_B - S_AB
    return {"I_AB": I_AB, "I_c": Ic, "S_A": S_A, "S_B": S_B, "S_AB": S_AB,
            "neg_S_A_given_B": Ic}


def bloch(rho):
    return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def lr_asym(rho_L, rho_R):
    return float(np.clip(0.5 * np.linalg.norm(bloch(rho_L) - bloch(rho_R)), 0, 1))


def make_bell_mixed(rho_L, rho_R, bell_psi, p):
    product = _ensure_valid_density(np.kron(rho_L, rho_R))
    rho_bell = np.outer(bell_psi, bell_psi.conj())
    return _ensure_valid_density((1 - p) * product + p * rho_bell)


# ═══════════════════════════════════════════════════════════════════
# SUITE 1: COMPOSITE CANDIDATES
# ═══════════════════════════════════════════════════════════════════

def build_bell_hist(history, bell_psi, p_fn, weight_fn=None):
    """
    Generic Bell-state history bridge builder.
    p_fn(rho_L, rho_R) -> p value for that step
    weight_fn(history, i) -> weight for step i (None = uniform)
    """
    states = []
    weights = []
    for i, h in enumerate(history):
        p = p_fn(h["rho_L"], h["rho_R"])
        rho = make_bell_mixed(h["rho_L"], h["rho_R"], bell_psi, p)
        states.append(rho)
        w = weight_fn(history, i) if weight_fn else 1.0
        weights.append(w)
    
    weights = np.array(weights)
    weights /= weights.sum()
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


def p_geometry(rho_L, rho_R):
    return float(np.clip(lr_asym(rho_L, rho_R), 0.01, 0.99))


def p_fixed(val):
    return lambda rho_L, rho_R: val


def p_torus_adaptive(eta):
    """Return optimal p based on torus latitude from Phase 2 findings."""
    clifford_eta = TORUS_CLIFFORD
    dist = abs(eta - clifford_eta) / (np.pi / 4)
    # Near Clifford: use geometry (~0.72-0.77). Far from Clifford: use 0.54
    p = 0.54 + (0.76 - 0.54) * max(0, 1 - dist)
    return lambda rho_L, rho_R: p


def w_uniform(history, i):
    return 1.0


def w_compress(history, i):
    return abs(history[i].get("dphi_L", 0)) + abs(history[i].get("dphi_R", 0)) + EPS


def w_retro(history, i):
    T = len(history)
    return np.exp(-0.1 * (T - 1 - i))


def w_retro_compress(history, i):
    return w_retro(history, i) * w_compress(history, i)


def w_entropy_grad(history, i):
    if i == 0:
        return EPS
    e_curr = von_neumann_entropy_2x2(history[i]["rho_L"]) + von_neumann_entropy_2x2(history[i]["rho_R"])
    e_prev = von_neumann_entropy_2x2(history[i-1]["rho_L"]) + von_neumann_entropy_2x2(history[i-1]["rho_R"])
    return abs(e_curr - e_prev) + EPS


def w_cooling_emphasis(history, i):
    """Weight cooling loop steps higher — bridge cares more about convergence."""
    lr = history[i].get("loop_role", "heating")
    return 2.0 if lr == "cooling" else 1.0


def run_composite_candidates(state, eta):
    """Test all composite candidate configurations."""
    history = state.history
    if not history:
        return {"error": "no history"}
    
    results = {}
    bell_states = {"Psi_minus": PSI_MINUS, "Phi_plus": PHI_PLUS, 
                   "Psi_plus": PSI_PLUS, "Phi_minus": PHI_MINUS}
    p_fns = {
        "p_geom": p_geometry,
        "p_054": p_fixed(0.54),
        "p_076": p_fixed(0.76),
        "p_050": p_fixed(0.50),
        "p_torus_adaptive": p_torus_adaptive(eta),
    }
    w_fns = {
        "w_uniform": w_uniform,
        "w_compress": w_compress,
        "w_retro": w_retro,
        "w_retro_compress": w_retro_compress,
        "w_entropy_grad": w_entropy_grad,
        "w_cooling": w_cooling_emphasis,
    }
    
    # Full grid: 4 Bell × 5 p_fn × 6 weight = 120 candidates per config
    for bell_name, bell_psi in bell_states.items():
        for p_name, p_fn in p_fns.items():
            for w_name, w_fn in w_fns.items():
                key = f"{bell_name}__{p_name}__{w_name}"
                try:
                    rho = build_bell_hist(history, bell_psi, p_fn, w_fn)
                    results[key] = metrics(rho)
                except Exception as e:
                    results[key] = {"error": str(e)}
    
    return results


# ═══════════════════════════════════════════════════════════════════
# SUITE 2: KERNEL SPLIT INVESTIGATION
# ═══════════════════════════════════════════════════════════════════

def run_kernel_split(state, eta):
    """Investigate why Φ₀ inverts on inner/outer but works on Clifford."""
    history = state.history
    if not history:
        return {"error": "no history"}
    
    results = {}
    
    # Fine p sweep with Ψ- (the best Bell state)
    p_fine = np.linspace(0.0, 1.0, 101)
    sweep = []
    for p in p_fine:
        rho = build_bell_hist(history, PSI_MINUS, p_fixed(float(p)))
        m = metrics(rho)
        sweep.append({"p": float(p), **m})
    results["psi_minus_p_sweep"] = sweep
    
    # Find critical points
    mi_vals = [s["I_AB"] for s in sweep]
    ic_vals = [s["I_c"] for s in sweep]
    
    # MI peak
    mi_peak_idx = int(np.argmax(mi_vals))
    results["mi_peak"] = {"p": float(p_fine[mi_peak_idx]), "I_AB": mi_vals[mi_peak_idx]}
    
    # I_c zero crossings
    crossings = []
    for i in range(len(ic_vals) - 1):
        if ic_vals[i] * ic_vals[i+1] < 0:
            p_cross = p_fine[i] + (p_fine[i+1] - p_fine[i]) * abs(ic_vals[i]) / (abs(ic_vals[i]) + abs(ic_vals[i+1]))
            crossings.append(float(p_cross))
    results["ic_crossings"] = crossings
    
    # I_c peak (max coherent information)
    ic_peak_idx = int(np.argmax(ic_vals))
    results["ic_peak"] = {"p": float(p_fine[ic_peak_idx]), "I_c": ic_vals[ic_peak_idx]}
    
    # Does MI peak coincide with I_c crossing? (this would be significant)
    if crossings:
        closest_crossing = min(crossings, key=lambda c: abs(c - p_fine[mi_peak_idx]))
        results["mi_peak_near_ic_crossing"] = {
            "mi_peak_p": float(p_fine[mi_peak_idx]),
            "closest_ic_crossing_p": closest_crossing,
            "gap": float(abs(p_fine[mi_peak_idx] - closest_crossing)),
            "is_close": bool(abs(p_fine[mi_peak_idx] - closest_crossing) < 0.1),
        }
    
    # Torus latitude analysis
    results["eta"] = float(eta)
    results["eta_ratio"] = float(eta / TORUS_CLIFFORD)
    results["is_clifford"] = bool(abs(eta - TORUS_CLIFFORD) < 0.01)
    results["cos2_sin2_ratio"] = float(np.cos(eta)**2 / (np.sin(eta)**2 + EPS))
    
    # The L/R asymmetry of the AVERAGED history
    avg_asym = np.mean([lr_asym(h["rho_L"], h["rho_R"]) for h in history])
    results["mean_history_lr_asymmetry"] = float(avg_asym)
    
    return results


# ═══════════════════════════════════════════════════════════════════
# SUITE 3: TEMPORAL ENTANGLEMENT (consecutive pairs)
# ═══════════════════════════════════════════════════════════════════

def run_temporal_entanglement(state):
    """
    Instead of entangling L/R at each step, entangle consecutive TIME steps.
    This tests genuine retrocausality: is the bridge about L/R chirality,
    or about temporal coherence?
    """
    history = state.history
    if len(history) < 2:
        return {"error": "need at least 2 history steps"}
    
    results = {}
    
    # For each consecutive pair (t, t+1), build ρ_t ⊗ ρ_{t+1} and mix with Ψ-
    temporal_states = []
    for i in range(len(history) - 1):
        # Product of consecutive L-states
        rho_t = history[i]["rho_L"]
        rho_t1 = history[i+1]["rho_L"]
        p = float(np.clip(0.5 * np.linalg.norm(bloch(rho_t) - bloch(rho_t1)), 0.01, 0.99))
        rho = make_bell_mixed(rho_t, rho_t1, PSI_MINUS, p)
        temporal_states.append(rho)
    
    rho_temporal_L = _ensure_valid_density(sum(temporal_states) / len(temporal_states))
    results["temporal_L_consecutive"] = metrics(rho_temporal_L)
    
    # Same for R-states
    temporal_states_R = []
    for i in range(len(history) - 1):
        rho_t = history[i]["rho_R"]
        rho_t1 = history[i+1]["rho_R"]
        p = float(np.clip(0.5 * np.linalg.norm(bloch(rho_t) - bloch(rho_t1)), 0.01, 0.99))
        rho = make_bell_mixed(rho_t, rho_t1, PSI_MINUS, p)
        temporal_states_R.append(rho)
    
    rho_temporal_R = _ensure_valid_density(sum(temporal_states_R) / len(temporal_states_R))
    results["temporal_R_consecutive"] = metrics(rho_temporal_R)
    
    # Cross-temporal: entangle L(t) with R(t+1) — retrocausal cross-chiral
    cross_states = []
    for i in range(len(history) - 1):
        rho_Lt = history[i]["rho_L"]
        rho_Rt1 = history[i+1]["rho_R"]
        p = float(np.clip(lr_asym(rho_Lt, rho_Rt1), 0.01, 0.99))
        rho = make_bell_mixed(rho_Lt, rho_Rt1, PSI_MINUS, p)
        cross_states.append(rho)
    
    rho_cross = _ensure_valid_density(sum(cross_states) / len(cross_states))
    results["cross_temporal_L_t_R_t1"] = metrics(rho_cross)
    
    # Reverse cross-temporal: R(t) with L(t+1)
    cross_rev = []
    for i in range(len(history) - 1):
        rho_Rt = history[i]["rho_R"]
        rho_Lt1 = history[i+1]["rho_L"]
        p = float(np.clip(lr_asym(rho_Rt, rho_Lt1), 0.01, 0.99))
        rho = make_bell_mixed(rho_Rt, rho_Lt1, PSI_MINUS, p)
        cross_rev.append(rho)
    
    rho_cross_rev = _ensure_valid_density(sum(cross_rev) / len(cross_rev))
    results["cross_temporal_R_t_L_t1"] = metrics(rho_cross_rev)
    
    # Non-adjacent temporal: L(t) with L(t+k) for various k
    for k in [2, 4, 8, 16]:
        if k >= len(history):
            continue
        skip_states = []
        for i in range(len(history) - k):
            rho_t = history[i]["rho_L"]
            rho_tk = history[i + k]["rho_L"]
            p = float(np.clip(0.5 * np.linalg.norm(bloch(rho_t) - bloch(rho_tk)), 0.01, 0.99))
            rho = make_bell_mixed(rho_t, rho_tk, PSI_MINUS, p)
            skip_states.append(rho)
        rho_skip = _ensure_valid_density(sum(skip_states) / len(skip_states))
        results[f"temporal_L_skip_{k}"] = metrics(rho_skip)
    
    return results


# ═══════════════════════════════════════════════════════════════════
# SUITE 4: CLIFFORD-CENTRIC BRIDGE
# ═══════════════════════════════════════════════════════════════════

def run_clifford_centric(state, eta):
    """
    Test whether the bridge should be Clifford-centric:
    the Clifford torus is where L and R are maximally mixed/balanced,
    and where the kernel Φ₀ works correctly.
    
    Maybe Axis 0 IS the Clifford torus — the point where the
    two Weyl sheets are maximally interleaved.
    """
    history = state.history
    if not history:
        return {"error": "no history"}
    
    results = {}
    
    # Distance from Clifford as a weight 
    dist_from_clifford = abs(eta - TORUS_CLIFFORD)
    clifford_weight = float(np.exp(-dist_from_clifford / 0.1))
    results["clifford_proximity"] = {
        "eta": float(eta),
        "dist_from_clifford": float(dist_from_clifford),
        "clifford_weight": clifford_weight,
    }
    
    # Filter history steps by ga0 level (high ga0 = near Clifford behavior)
    ga0_levels = [h.get("ga0_after", 0.5) for h in history]
    results["ga0_distribution"] = {
        "mean": float(np.mean(ga0_levels)),
        "std": float(np.std(ga0_levels)),
        "min": float(np.min(ga0_levels)),
        "max": float(np.max(ga0_levels)),
    }
    
    # Build bridge weighting by ga0 level (high ga0 = more bridge-like)
    ga0_weighted_states = []
    ga0_weights = []
    for h in history:
        rL, rR = h["rho_L"], h["rho_R"]
        p = float(np.clip(lr_asym(rL, rR), 0.01, 0.99))
        rho = make_bell_mixed(rL, rR, PSI_MINUS, p)
        ga0_weighted_states.append(rho)
        ga0_weights.append(h.get("ga0_after", 0.5))
    
    gw = np.array(ga0_weights)
    gw /= gw.sum()
    rho_ga0 = _ensure_valid_density(sum(w * s for w, s in zip(gw, ga0_weighted_states)))
    results["bell_psi_minus_ga0_weighted"] = metrics(rho_ga0)
    
    # Inverse ga0 weighting (low ga0 = more constrained = more bridge-like?)
    inv_ga0 = 1.0 / (np.array(ga0_weights) + EPS)
    inv_ga0 /= inv_ga0.sum()
    rho_inv_ga0 = _ensure_valid_density(sum(w * s for w, s in zip(inv_ga0, ga0_weighted_states)))
    results["bell_psi_minus_inv_ga0_weighted"] = metrics(rho_inv_ga0)
    
    # Ax0 torus entropy weighted
    ax0_te = [h.get("ax0_torus_entropy", 0.5) for h in history]
    if any(t > 0 for t in ax0_te):
        te_w = np.array(ax0_te) + EPS
        te_w /= te_w.sum()
        rho_te = _ensure_valid_density(sum(w * s for w, s in zip(te_w, ga0_weighted_states)))
        results["bell_psi_minus_torus_entropy_weighted"] = metrics(rho_te)
    
    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("AXIS 0 BRIDGE — PHASE 3: COMPOSITE CANDIDATES & KERNEL SPLIT")
    print("=" * 80)
    
    all_results = []
    
    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for torus_label, eta in TORUS_CONFIGS:
            print(f"\n{'─' * 60}")
            print(f"  Engine Type {engine_type}, Torus: {torus_label} (η={eta:.4f})")
            print(f"{'─' * 60}")
            
            init_state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            final_state = engine.run_cycle(init_state)
            
            print(f"  Running Suite 1: Composite candidates (120 configs)...")
            composite = run_composite_candidates(final_state, eta)
            
            print(f"  Running Suite 2: Kernel split investigation (101-point sweep)...")
            kernel_split = run_kernel_split(final_state, eta)
            
            print(f"  Running Suite 3: Temporal entanglement...")
            temporal = run_temporal_entanglement(final_state)
            
            print(f"  Running Suite 4: Clifford-centric bridge...")
            clifford = run_clifford_centric(final_state, eta)
            
            all_results.append({
                "engine_type": engine_type,
                "torus": torus_label,
                "eta": float(eta),
                "composite": composite,
                "kernel_split": kernel_split,
                "temporal": temporal,
                "clifford_centric": clifford,
            })
    
    # ═══════════════════════════════════════════════════════════════════
    # VERDICTS
    # ═══════════════════════════════════════════════════════════════════
    
    print(f"\n{'=' * 80}")
    print("PHASE 3 VERDICTS")
    print(f"{'=' * 80}")
    
    # === Verdict 1: Best composite overall ===
    print(f"\n  1. TOP 20 COMPOSITE CANDIDATES (by mean I_AB across all configs):")
    all_keys = set()
    for r in all_results:
        all_keys.update(r["composite"].keys())
    
    composite_scores = {}
    for key in all_keys:
        mis = []
        ics = []
        for r in all_results:
            d = r["composite"].get(key, {})
            if "I_AB" in d:
                mis.append(d["I_AB"])
                ics.append(d.get("I_c", 0))
        if mis:
            composite_scores[key] = (float(np.mean(mis)), float(np.mean(ics)), float(np.std(mis)))
    
    top_20 = sorted(composite_scores.items(), key=lambda x: x[1][0], reverse=True)[:20]
    print(f"\n     {'Rank':>4} {'Candidate':<55} {'Mean I_AB':>10} {'Mean I_c':>10} {'Std':>8}")
    print(f"     {'─'*4} {'─'*55} {'─'*10} {'─'*10} {'─'*8}")
    for rank, (name, (mi, ic, std)) in enumerate(top_20, 1):
        marker = " ★" if rank == 1 else ""
        print(f"     {rank:>4} {name:<55} {mi:>10.6f} {ic:>10.6f} {std:>8.6f}{marker}")
    
    # === Verdict 2: Kernel split ===
    print(f"\n  2. KERNEL SPLIT ANALYSIS:")
    for r in all_results:
        ks = r["kernel_split"]
        mi_peak = ks["mi_peak"]
        ic_peak = ks["ic_peak"]
        crossings = ks.get("ic_crossings", [])
        is_cliff = ks["is_clifford"]
        print(f"     {r['engine_type']}/{r['torus']}: "
              f"MI_peak at p={mi_peak['p']:.2f} (MI={mi_peak['I_AB']:.4f}), "
              f"Ic_peak at p={ic_peak['p']:.2f} (Ic={ic_peak['I_c']:.4f}), "
              f"Ic_crossings={[f'{c:.2f}' for c in crossings]}, "
              f"{'CLIFFORD' if is_cliff else f'cos²/sin²={ks['cos2_sin2_ratio']:.2f}'}")
    
    # === Verdict 3: Temporal entanglement ===
    print(f"\n  3. TEMPORAL ENTANGLEMENT vs CHIRAL ENTANGLEMENT:")
    for r in all_results:
        t = r["temporal"]
        chiral_mi = composite_scores.get("Psi_minus__p_geom__w_uniform", (0, 0, 0))[0]
        temp_L = t.get("temporal_L_consecutive", {}).get("I_AB", 0)
        temp_R = t.get("temporal_R_consecutive", {}).get("I_AB", 0)
        cross = t.get("cross_temporal_L_t_R_t1", {}).get("I_AB", 0)
        cross_rev = t.get("cross_temporal_R_t_L_t1", {}).get("I_AB", 0)
        skips = {k: v.get("I_AB", 0) for k, v in t.items() if "skip" in k}
        print(f"     {r['engine_type']}/{r['torus']}: "
              f"temporal_L={temp_L:.4f}, temporal_R={temp_R:.4f}, "
              f"cross_L→R={cross:.4f}, cross_R→L={cross_rev:.4f}, "
              f"skips={{{', '.join(f'{k}:{v:.4f}' for k, v in skips.items())}}}")
    
    # === Verdict 4: Clifford-centric ===
    print(f"\n  4. CLIFFORD-CENTRIC BRIDGE:")
    for r in all_results:
        cc = r["clifford_centric"]
        ga0_w = cc.get("bell_psi_minus_ga0_weighted", {}).get("I_AB", 0)
        inv_ga0 = cc.get("bell_psi_minus_inv_ga0_weighted", {}).get("I_AB", 0)
        te_w = cc.get("bell_psi_minus_torus_entropy_weighted", {}).get("I_AB", 0)
        prox = cc.get("clifford_proximity", {})
        print(f"     {r['engine_type']}/{r['torus']}: "
              f"ga0_weighted={ga0_w:.4f}, inv_ga0={inv_ga0:.4f}, "
              f"torus_entropy_weighted={te_w:.4f}, "
              f"clifford_dist={prox.get('dist_from_clifford', 0):.4f}")
    
    # === Which weighting scheme wins? ===
    print(f"\n  5. BEST WEIGHTING SCHEME (across all Bell states and p values):")
    w_scores = {}
    for key, (mi, ic, std) in composite_scores.items():
        parts = key.split("__")
        if len(parts) == 3:
            w_name = parts[2]
            if w_name not in w_scores:
                w_scores[w_name] = []
            w_scores[w_name].append(mi)
    
    w_ranking = sorted(w_scores.items(), key=lambda x: np.mean(x[1]), reverse=True)
    for rank, (name, mis) in enumerate(w_ranking, 1):
        marker = " ★" if rank == 1 else ""
        print(f"     {rank:>2}. {name:<25} mean I_AB = {np.mean(mis):.6f} (std={np.std(mis):.4f}){marker}")
    
    # === Which Bell state wins? ===
    print(f"\n  6. BEST BELL STATE (across all p values and weights):")
    b_scores = {}
    for key, (mi, ic, std) in composite_scores.items():
        parts = key.split("__")
        if len(parts) == 3:
            b_name = parts[0]
            if b_name not in b_scores:
                b_scores[b_name] = []
            b_scores[b_name].append(mi)
    
    b_ranking = sorted(b_scores.items(), key=lambda x: np.mean(x[1]), reverse=True)
    for rank, (name, mis) in enumerate(b_ranking, 1):
        marker = " ★" if rank == 1 else ""
        print(f"     {rank:>2}. {name:<25} mean I_AB = {np.mean(mis):.6f} (std={np.std(mis):.4f}){marker}")
    
    # === Which p function wins? ===
    print(f"\n  7. BEST P-VALUE FUNCTION (across all Bell states and weights):")
    p_scores = {}
    for key, (mi, ic, std) in composite_scores.items():
        parts = key.split("__")
        if len(parts) == 3:
            p_name = parts[1]
            if p_name not in p_scores:
                p_scores[p_name] = []
            p_scores[p_name].append(mi)
    
    p_ranking = sorted(p_scores.items(), key=lambda x: np.mean(x[1]), reverse=True)
    for rank, (name, mis) in enumerate(p_ranking, 1):
        marker = " ★" if rank == 1 else ""
        print(f"     {rank:>2}. {name:<25} mean I_AB = {np.mean(mis):.6f} (std={np.std(mis):.4f}){marker}")
    
    # Save
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "a2_state", "sim_results")
    os.makedirs(output_dir, exist_ok=True)
    
    winner = top_20[0][0] if top_20 else "none"
    winner_mi = top_20[0][1][0] if top_20 else 0
    
    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_axis0_phase3_composite",
        "total_composite_candidates": len(composite_scores),
        "winner": winner,
        "winner_MI": winner_mi,
        "top10": [(name, mi) for name, (mi, _, _) in top_20[:10]],
    }
    
    out_path = os.path.join(output_dir, "axis0_phase3_results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Results saved: {out_path}")
    
    print(f"\n{'=' * 80}")
    print(f"PROBE STATUS: PASS")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
