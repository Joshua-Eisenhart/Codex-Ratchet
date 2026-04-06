#!/usr/bin/env python3
"""
Axis 0 Bridge — Phase 4: Final Bridge Candidate
=================================================

Phase 3 discoveries:
  - Ψ⁻ × p_geom × retro weighting = 1.531 bits MI (best composite)
  - Cross-temporal L(t)→R(t+1) = 1.76 bits MI (HIGHEST ANYWHERE)
  - Same-sheet temporal (L→L, R→R) ≈ 0 bits (no signal)
  - Geometry-derived p BEATS all fixed values
  - Retrocausal weighting BEATS uniform
  - Clifford torus is the honest kernel site (Φ₀ works correctly there)

This probe now builds and tests the FINAL composite bridge candidates
that combine ALL winning features:

Xi_final = Cross-temporal chiral retrocausal Ψ⁻ bridge

Architecture:
  1. Cross-temporal: entangle L(t) with R(t+1) not L(t) with R(t)
  2. Chiral: use Ψ⁻ (singlet — max boundary info)
  3. Retrocausal: weight by exponential decay into past
  4. Geometry-derived p: LR asymmetry sets coupling strength
  5. Compression-weighted: dphi magnitude as additional weight
  6. Kernel Φ₀ = -S(A|B) as the evaluation metric

Also tests:
  - Forward vs backward temporal direction (L(t)→R(t+1) vs L(t+1)→R(t))
  - Temporal stride (k=1 vs k=2 vs k=4)
  - Marginal-preserving variants (honest entanglement test)
  - Full landscape comparison: all phases side by side

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

PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
PHI_PLUS = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)

TORUS_CONFIGS = [
    ("inner", TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer", TORUS_OUTER),
]


def von_neumann_entropy(rho):
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals))) if len(evals) > 0 else 0.0


def ptr_B(rho_AB):
    return np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def ptr_A(rho_AB):
    return np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def full_metrics(rho_AB):
    rho_A, rho_B = ptr_B(rho_AB), ptr_A(rho_AB)
    S_A, S_B, S_AB = von_neumann_entropy(rho_A), von_neumann_entropy(rho_B), von_neumann_entropy(rho_AB)
    I_AB = max(0.0, S_A + S_B - S_AB)
    Ic = S_B - S_AB
    # Marginal deviation from product check
    product = _ensure_valid_density(np.kron(rho_A, rho_B))
    product_mi = max(0.0, S_A + S_B - von_neumann_entropy(product))
    return {
        "I_AB": I_AB, "I_c": Ic, "S_A": S_A, "S_B": S_B, "S_AB": S_AB,
        "neg_S_A_given_B": Ic, "product_check_MI": product_mi,
    }


def marginal_check(rho_candidate, rho_A_target, rho_B_target):
    rho_A = ptr_B(rho_candidate)
    rho_B = ptr_A(rho_candidate)
    dev_A = float(np.linalg.norm(rho_A - rho_A_target, ord="fro"))
    dev_B = float(np.linalg.norm(rho_B - rho_B_target, ord="fro"))
    return {
        "marginal_dev_A": dev_A,
        "marginal_dev_B": dev_B,
        "max_marginal_dev": max(dev_A, dev_B),
        "preserves_marginals": bool(dev_A < 1e-6 and dev_B < 1e-6),
    }


def bloch(rho):
    return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def lr_asym(rho_a, rho_b):
    return float(np.clip(0.5 * np.linalg.norm(bloch(rho_a) - bloch(rho_b)), 0, 1))


def make_bell_mixed(rho_a, rho_b, bell_psi, p):
    product = _ensure_valid_density(np.kron(rho_a, rho_b))
    rho_bell = np.outer(bell_psi, bell_psi.conj())
    return _ensure_valid_density((1 - p) * product + p * rho_bell)


# ═══════════════════════════════════════════════════════════════════
# CROSS-TEMPORAL BRIDGE BUILDERS
# ═══════════════════════════════════════════════════════════════════

def xi_cross_temporal(history, stride=1, direction="forward", bell_psi=PSI_MINUS,
                      p_fn=None, w_fn=None):
    """
    Cross-temporal chiral bridge: entangle L(t) with R(t+stride).
    
    direction="forward": L(t) ⊗ R(t+stride) — future R conditions present L
    direction="backward": R(t) ⊗ L(t+stride) — future L conditions present R
    direction="symmetric": average of forward and backward
    """
    T = len(history)
    if T < stride + 1:
        return None, {"error": "insufficient history"}
    
    states = []
    weights = []
    
    pairs_range = range(T - stride)
    
    for i in pairs_range:
        if direction == "forward":
            rho_a = history[i]["rho_L"]
            rho_b = history[i + stride]["rho_R"]
        elif direction == "backward":
            rho_a = history[i]["rho_R"]
            rho_b = history[i + stride]["rho_L"]
        else:  # symmetric
            rho_a_f = history[i]["rho_L"]
            rho_b_f = history[i + stride]["rho_R"]
            rho_a_b = history[i]["rho_R"]
            rho_b_b = history[i + stride]["rho_L"]
            # Average forward and backward
            p_f = p_fn(rho_a_f, rho_b_f) if p_fn else lr_asym(rho_a_f, rho_b_f)
            p_f = float(np.clip(p_f, 0.01, 0.99))
            p_b = p_fn(rho_a_b, rho_b_b) if p_fn else lr_asym(rho_a_b, rho_b_b)
            p_b = float(np.clip(p_b, 0.01, 0.99))
            rho_f = make_bell_mixed(rho_a_f, rho_b_f, bell_psi, p_f)
            rho_b_state = make_bell_mixed(rho_a_b, rho_b_b, bell_psi, p_b)
            rho = _ensure_valid_density(0.5 * rho_f + 0.5 * rho_b_state)
            states.append(rho)
            w = w_fn(history, i, stride) if w_fn else 1.0
            weights.append(w)
            continue
        
        p = p_fn(rho_a, rho_b) if p_fn else lr_asym(rho_a, rho_b)
        p = float(np.clip(p, 0.01, 0.99))
        rho = make_bell_mixed(rho_a, rho_b, bell_psi, p)
        states.append(rho)
        w = w_fn(history, i, stride) if w_fn else 1.0
        weights.append(w)
    
    if not states:
        return None, {"error": "no states built"}
    
    weights = np.array(weights)
    weights /= weights.sum()
    rho_final = _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))
    return rho_final, {"n_pairs": len(states), "stride": stride, "direction": direction}


def w_retro_temporal(history, i, stride):
    T = len(history)
    return np.exp(-0.1 * (T - stride - 1 - i))


def w_compress_temporal(history, i, stride):
    dphi_i = abs(history[i].get("dphi_L", 0)) + abs(history[i].get("dphi_R", 0))
    dphi_j = abs(history[i+stride].get("dphi_L", 0)) + abs(history[i+stride].get("dphi_R", 0))
    return (dphi_i + dphi_j) / 2 + EPS


def w_retro_compress_temporal(history, i, stride):
    return w_retro_temporal(history, i, stride) * w_compress_temporal(history, i, stride)


def w_cooling_temporal(history, i, stride):
    r1 = history[i].get("loop_role", "heating")
    r2 = history[i+stride].get("loop_role", "heating")
    w = 1.0
    if r1 == "cooling":
        w *= 1.5
    if r2 == "cooling":
        w *= 1.5
    return w


# ═══════════════════════════════════════════════════════════════════
# SAME-TIME CHIRAL (for comparison)
# ═══════════════════════════════════════════════════════════════════

def xi_chiral_hist(history, bell_psi=PSI_MINUS, w_fn=None):
    """Same-time L(t)⊗R(t) chiral bridge (Phase 2 winner family)."""
    states = []
    weights = []
    for i, h in enumerate(history):
        p = float(np.clip(lr_asym(h["rho_L"], h["rho_R"]), 0.01, 0.99))
        rho = make_bell_mixed(h["rho_L"], h["rho_R"], bell_psi, p)
        states.append(rho)
        w = w_fn(history, i, 0) if w_fn else 1.0
        weights.append(w)
    weights = np.array(weights)
    weights /= weights.sum()
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


def xi_product_hist(history, w_fn=None):
    """Product state history (Phase 1 baseline)."""
    states = []
    weights = []
    for i, h in enumerate(history):
        rho = _ensure_valid_density(np.kron(h["rho_L"], h["rho_R"]))
        states.append(rho)
        w = w_fn(history, i, 0) if w_fn else 1.0
        weights.append(w)
    weights = np.array(weights)
    weights /= weights.sum()
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


# ═══════════════════════════════════════════════════════════════════
# FULL LANDSCAPE TEST
# ═══════════════════════════════════════════════════════════════════

def run_full_landscape(state, eta):
    """Test the complete landscape of bridge candidates."""
    history = state.history
    if not history:
        return {"error": "no history"}
    
    results = {}
    
    # === BASELINE ===
    rho_product = _ensure_valid_density(np.kron(state.rho_L, state.rho_R))
    results["00_product_direct"] = full_metrics(rho_product)
    
    rho_product_hist = xi_product_hist(history)
    results["01_product_hist_uniform"] = full_metrics(rho_product_hist)
    
    # === SAME-TIME CHIRAL (Phase 2-3 winners) ===
    rho_chiral_uni = xi_chiral_hist(history, PSI_MINUS)
    results["10_chiral_Psi_minus_uniform"] = full_metrics(rho_chiral_uni)
    
    def _w_retro_0(h, i, s):
        return np.exp(-0.1 * (len(h) - 1 - i))
    rho_chiral_retro = xi_chiral_hist(history, PSI_MINUS, _w_retro_0)
    results["11_chiral_Psi_minus_retro"] = full_metrics(rho_chiral_retro)
    
    def _w_compress_0(h, i, s):
        return abs(h[i].get("dphi_L", 0)) + abs(h[i].get("dphi_R", 0)) + EPS
    rho_chiral_compress = xi_chiral_hist(history, PSI_MINUS, _w_compress_0)
    results["12_chiral_Psi_minus_compress"] = full_metrics(rho_chiral_compress)
    
    # === CROSS-TEMPORAL (Phase 3 discovery) ===
    
    # Forward: L(t) → R(t+1)
    for stride in [1, 2, 4, 8]:
        for direction in ["forward", "backward", "symmetric"]:
            for w_name, w_fn in [("uniform", None), ("retro", w_retro_temporal),
                                  ("compress", w_compress_temporal),
                                  ("retro_compress", w_retro_compress_temporal),
                                  ("cooling", w_cooling_temporal)]:
                key = f"20_cross_s{stride}_{direction}_{w_name}"
                rho, meta = xi_cross_temporal(history, stride=stride, direction=direction,
                                              bell_psi=PSI_MINUS, w_fn=w_fn)
                if rho is not None:
                    results[key] = {**full_metrics(rho), **meta}
                else:
                    results[key] = meta
    
    # === CROSS-TEMPORAL with Φ+ (for comparison) ===
    rho_phi, meta_phi = xi_cross_temporal(history, stride=1, direction="forward",
                                          bell_psi=PHI_PLUS)
    if rho_phi is not None:
        results["30_cross_s1_forward_PhiPlus_uniform"] = {**full_metrics(rho_phi), **meta_phi}
    
    # === HYBRID: cross-temporal + same-time average ===
    rho_cross, _ = xi_cross_temporal(history, stride=1, direction="symmetric",
                                     bell_psi=PSI_MINUS, w_fn=w_retro_temporal)
    rho_same = xi_chiral_hist(history, PSI_MINUS, _w_retro_0)
    if rho_cross is not None:
        for alpha in [0.25, 0.5, 0.75]:
            rho_hybrid = _ensure_valid_density(alpha * rho_cross + (1 - alpha) * rho_same)
            results[f"40_hybrid_a{alpha:.2f}_cross_retro_same_retro"] = full_metrics(rho_hybrid)
    
    # === MARGINAL PRESERVATION CHECK ===
    # Compute drift for every actual candidate state, not just the headline pair.
    marginal_checks = {}
    candidate_states = {
        "10_chiral_Psi_minus_uniform": rho_chiral_uni,
        "11_chiral_Psi_minus_retro": rho_chiral_retro,
        "12_chiral_Psi_minus_compress": rho_chiral_compress,
        "30_cross_s1_forward_PhiPlus_uniform": rho_phi if "rho_phi" in locals() else None,
        "40_hybrid_a0.25_cross_retro_same_retro": None,
        "40_hybrid_a0.50_cross_retro_same_retro": None,
        "40_hybrid_a0.75_cross_retro_same_retro": None,
    }
    for stride in [1, 2, 4, 8]:
        for direction in ["forward", "backward", "symmetric"]:
            for w_name, w_fn in [("uniform", None), ("retro", w_retro_temporal),
                                  ("compress", w_compress_temporal),
                                  ("retro_compress", w_retro_compress_temporal),
                                  ("cooling", w_cooling_temporal)]:
                key = f"20_cross_s{stride}_{direction}_{w_name}"
                rho, _ = xi_cross_temporal(history, stride=stride, direction=direction,
                                           bell_psi=PSI_MINUS, w_fn=w_fn)
                if rho is not None:
                    candidate_states[key] = rho
    if rho_cross is not None:
        for alpha in [0.25, 0.5, 0.75]:
            key = f"40_hybrid_a{alpha:.2f}_cross_retro_same_retro"
            candidate_states[key] = _ensure_valid_density(alpha * rho_cross + (1 - alpha) * rho_same)

    for key, rho_candidate in candidate_states.items():
        if rho_candidate is not None:
            marginal_checks[key] = marginal_check(rho_candidate, state.rho_L, state.rho_R)
    results["99_marginal_checks"] = marginal_checks
    
    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("AXIS 0 BRIDGE — PHASE 4: FINAL BRIDGE CANDIDATE")
    print("=" * 80)
    
    all_results = []
    
    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for torus_label, eta in TORUS_CONFIGS:
            print(f"\n  Engine {engine_type}/{torus_label}: running full landscape...")
            init_state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            final_state = engine.run_cycle(init_state)
            
            landscape = run_full_landscape(final_state, eta)
            all_results.append({
                "engine_type": engine_type,
                "torus": torus_label,
                "eta": float(eta),
                "landscape": landscape,
            })
    
    # ═══════════════════════════════════════════════════════════════════
    # VERDICTS
    # ═══════════════════════════════════════════════════════════════════
    
    print(f"\n{'=' * 80}")
    print("PHASE 4 — FULL LANDSCAPE RANKING")
    print(f"{'=' * 80}")
    
    # Aggregate all candidates
    all_keys = set()
    for r in all_results:
        all_keys.update(k for k in r["landscape"].keys() if k != "99_marginal_checks")
    
    scores = {}
    for key in all_keys:
        mis = []
        ics = []
        for r in all_results:
            d = r["landscape"].get(key, {})
            if "I_AB" in d:
                mis.append(d["I_AB"])
                ics.append(d.get("I_c", 0))
        if mis:
            scores[key] = (float(np.mean(mis)), float(np.mean(ics)), float(np.std(mis)))
    
    ranking = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)

    marginal_aggregate = {}
    for key in all_keys:
        checks = []
        for r in all_results:
            mc = r["landscape"].get("99_marginal_checks", {})
            if key in mc:
                checks.append(mc[key])
        if checks:
            max_dev = max(c["max_marginal_dev"] for c in checks)
            preserves_all = all(c["preserves_marginals"] for c in checks)
            marginal_aggregate[key] = {
                "max_marginal_dev": float(max_dev),
                "preserves_marginals_all_configs": bool(preserves_all),
            }

    matched_marginal_tol = 1e-3
    matched_marginal_ranking = [
        (name, mi, ic, std, marginal_aggregate[name]["max_marginal_dev"])
        for name, (mi, ic, std) in ranking
        if name in marginal_aggregate and marginal_aggregate[name]["max_marginal_dev"] < matched_marginal_tol
    ]
    
    print(f"\n  Total candidates tested: {len(ranking)}")
    print(f"\n  {'Rank':>4} {'Candidate':<55} {'Mean I_AB':>10} {'Mean I_c':>10} {'Std':>8}")
    print(f"  {'─'*4} {'─'*55} {'─'*10} {'─'*10} {'─'*8}")
    
    for rank, (name, (mi, ic, std)) in enumerate(ranking[:30], 1):
        marker = " ★" if rank == 1 else ""
        print(f"  {rank:>4} {name:<55} {mi:>10.6f} {ic:>10.6f} {std:>8.6f}{marker}")
    
    # === Category analysis ===
    print(f"\n{'=' * 80}")
    print("CATEGORY ANALYSIS")
    print(f"{'=' * 80}")
    
    categories = {
        "Product (baseline)": [k for k in scores if k.startswith("0")],
        "Same-time chiral": [k for k in scores if k.startswith("1")],
        "Cross-temporal": [k for k in scores if k.startswith("2")],
        "Cross-temporal Φ+": [k for k in scores if k.startswith("3")],
        "Hybrid": [k for k in scores if k.startswith("4")],
    }
    
    for cat_name, members in categories.items():
        if not members:
            continue
        cat_mis = [scores[k][0] for k in members if k in scores]
        if cat_mis:
            best_key = max(members, key=lambda k: scores.get(k, (0, 0, 0))[0])
            best_mi = scores[best_key][0]
            print(f"\n  {cat_name}:")
            print(f"    Best: {best_key} = {best_mi:.6f}")
            print(f"    Mean across variants: {np.mean(cat_mis):.6f}")
            print(f"    Count: {len(cat_mis)}")
    
    # === Stride analysis ===
    print(f"\n  STRIDE ANALYSIS (cross-temporal, forward, uniform):")
    for stride in [1, 2, 4, 8]:
        key = f"20_cross_s{stride}_forward_uniform"
        if key in scores:
            mi, ic, std = scores[key]
            print(f"    stride={stride}: I_AB={mi:.6f}, I_c={ic:.6f}")
    
    # === Direction analysis ===
    print(f"\n  DIRECTION ANALYSIS (cross-temporal, stride=1, uniform):")
    for direction in ["forward", "backward", "symmetric"]:
        key = f"20_cross_s1_{direction}_uniform"
        if key in scores:
            mi, ic, std = scores[key]
            print(f"    {direction}: I_AB={mi:.6f}, I_c={ic:.6f}")
    
    # === Weighting analysis (cross-temporal, stride=1, forward) ===
    print(f"\n  WEIGHTING ANALYSIS (cross-temporal, stride=1, forward):")
    for w_name in ["uniform", "retro", "compress", "retro_compress", "cooling"]:
        key = f"20_cross_s1_forward_{w_name}"
        if key in scores:
            mi, ic, std = scores[key]
            print(f"    {w_name}: I_AB={mi:.6f}, I_c={ic:.6f}")
    
    # === Marginal checks ===
    print(f"\n  MARGINAL PRESERVATION:")
    for r in all_results:
        mc = r["landscape"].get("99_marginal_checks", {})
        for cand_name, check in mc.items():
            print(f"    {r['engine_type']}/{r['torus']} {cand_name}: "
                  f"dev_A={check['marginal_dev_A']:.6f}, dev_B={check['marginal_dev_B']:.6f}, "
                  f"preserves={check['preserves_marginals']}")

    print(f"\n  MATCHED-MARGINAL FILTER (tol={matched_marginal_tol:.1e}):")
    if matched_marginal_ranking:
        for name, mi, ic, std, max_dev in matched_marginal_ranking[:10]:
            print(f"    {name}: I_AB={mi:.6f}, I_c={ic:.6f}, max_dev={max_dev:.6f}")
    else:
        print("    No candidate passed the matched-marginal filter.")
    
    # === OVERALL WINNER ===
    winner = ranking[0][0]
    winner_mi = ranking[0][1][0]
    winner_ic = ranking[0][1][1]
    winner_preserves_marginals = marginal_aggregate.get(winner, {}).get("preserves_marginals_all_configs", False)
    baseline_mi = scores.get("00_product_direct", (0, 0, 0))[0]
    phase2_mi = scores.get("10_chiral_Psi_minus_uniform", (0, 0, 0))[0]
    matched_marginal_winner = matched_marginal_ranking[0][0] if matched_marginal_ranking else None
    matched_marginal_winner_mi = matched_marginal_ranking[0][1] if matched_marginal_ranking else None
    winner_vs_matched_marginal_gap = (
        float(winner_mi - matched_marginal_winner_mi)
        if matched_marginal_winner_mi is not None else None
    )
    
    print(f"\n{'=' * 80}")
    print("FINAL VERDICT")
    print(f"{'=' * 80}")
    print(f"\n  WINNER: {winner}")
    print(f"  Mean I_AB: {winner_mi:.6f}")
    print(f"  Mean I_c:  {winner_ic:.6f}")
    print(f"  Winner preserves marginals across all configs: {winner_preserves_marginals}")
    print(f"  vs Product baseline: +{winner_mi - baseline_mi:.6f}")
    print(f"  vs Phase 2 chiral:   +{winner_mi - phase2_mi:.6f}")
    if matched_marginal_winner is not None:
        print(f"  Best matched-marginal candidate: {matched_marginal_winner} ({matched_marginal_winner_mi:.6f})")
        print(f"  Winner gap vs matched-marginal best: {winner_vs_matched_marginal_gap:.6f}")
    else:
        print("  Best matched-marginal candidate: none")
    
    # Per-torus breakdown for winner
    print(f"\n  Per-torus breakdown for winner:")
    for r in all_results:
        d = r["landscape"].get(winner, {})
        print(f"    {r['engine_type']}/{r['torus']}: I_AB={d.get('I_AB', 0):.6f}, I_c={d.get('I_c', 0):.6f}")
    
    # Save
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "a2_state", "sim_results")
    os.makedirs(output_dir, exist_ok=True)
    
    summary = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_axis0_phase4_final_bridge",
        "total_candidates": len(ranking),
        "winner": winner,
        "winner_MI": winner_mi,
        "winner_Ic": winner_ic,
        "winner_preserves_marginals": winner_preserves_marginals,
        "matched_marginal_tolerance": matched_marginal_tol,
        "matched_marginal_winner": matched_marginal_winner,
        "matched_marginal_winner_MI": matched_marginal_winner_mi,
        "winner_vs_matched_marginal_gap": winner_vs_matched_marginal_gap,
        "matched_marginal_ranking_top10": [
            (name, mi, ic, max_dev)
            for name, mi, ic, _, max_dev in matched_marginal_ranking[:10]
        ],
        "marginal_checks": marginal_aggregate,
        "top20": [(name, mi, ic) for name, (mi, ic, _) in ranking[:20]],
        "category_bests": {
            cat: max(members, key=lambda k: scores.get(k, (0, 0, 0))[0])
            for cat, members in categories.items() if members
        },
    }
    
    out_path = os.path.join(output_dir, "axis0_phase4_results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Results saved: {out_path}")
    
    print(f"\n{'=' * 80}")
    print(f"PROBE STATUS: PASS")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
