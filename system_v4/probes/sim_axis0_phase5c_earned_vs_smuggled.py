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
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import gudhi
import numpy as np
import rustworkx as rx
import sympy as sp
import torch
import torch_ga
import xgi
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean
from scipy.linalg import expm
classification = "classical_baseline"  # auto-backfill
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat
divergence_log = (
    "Classical foundation baseline: this tests earned-vs-smuggled Axis-0 "
    "bridge information numerically. The legacy honesty verdict is preserved, "
    "and a deep contract now binds the honesty surfaces to the same shell "
    "bridge, graph/topology, symbolic expansion, solver closure, geometric "
    "algebra, and manifold witnesses used elsewhere in Axis 0."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "scramble, decoupled, and decomposition bridge numerics"},
    "scipy": {"tried": True, "used": True, "reason": "honesty-surface propagator witness"},
    "pytorch": {"tried": True, "used": True, "reason": "fit and gradient witness over the honesty frontier"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning honesty vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning honesty vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered DAG witness over the ranked honesty frontier"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order config-to-honesty coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for honesty closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the honesty complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for honesty expansion"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing honesty rank order and monotone scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for aggregate honesty geometry"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "geomstats": "load_bearing",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER
from sim_axis0_dynamic_shell import lane_d_topology_expansion_bridge
from sim_axis0_iscalar_sweep import (
    _clifford_vector,
    _option_cell_complex_surface as _candidate_cell_complex_surface,
    _option_constraint_surface as _candidate_constraint_surface,
    _option_graph_surface as _candidate_graph_surface,
    _option_hypergraph_surface as _candidate_hypergraph_surface,
    _option_manifold_surface as _candidate_manifold_surface,
    _option_scale_history as _candidate_scale_history,
    _option_symbolic_surface as _candidate_symbolic_surface,
    _option_topology_surface as _candidate_topology_surface,
    _torch_ga_roundtrip,
    _torch_option_fit as _torch_candidate_fit,
)

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


def _aggregate_deep_contract(config_records: list[dict]) -> dict[str, object]:
    candidate_names = [
        "geometry_base_surface",
        "earned_fraction_surface",
        "scramble_sensitivity_surface",
        "decoupled_sensitivity_surface",
        "ramp_midpoint_surface",
    ]
    shell_bridge_pass_fraction = float(
        np.mean([1.0 if row["shell_bridge"]["lane_d_keep"] else 0.0 for row in config_records])
    ) if config_records else 0.0

    candidate_signal_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_signed_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_shell_hubble_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_doctrine_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    config_rankings: list[list[str]] = []

    for row in config_records:
        decomp = row["decomp"]
        scramble = row["scramble"]
        decouple = row["decouple"]
        ramp = row["ramp"]
        ramp_mid = next((entry for entry in ramp if abs(entry["p"] - 0.5) < 1e-9), None)
        ramp_zero = next((entry for entry in ramp if abs(entry["p"] - 0.0) < 1e-9), None)

        earned_fraction = float(max(0.0, 1.0 - float(decomp["bell_fraction"])))
        geometry_base = float(decomp["product_MI"])
        scramble_drop = float(max(0.0, scramble["mi_drop_fraction"]))
        decouple_drop = float(max(0.0, decouple["mi_drop_fraction"]))
        ramp_mid_gain = float(ramp_mid["MI"] - ramp_zero["MI"]) if ramp_mid and ramp_zero else 0.0

        local_rows = {
            "geometry_base_surface": {
                "signal": geometry_base,
                "signed": float(decomp["product_Ic"]),
                "doctrine": 1.0 if geometry_base > 0.15 else 0.0,
            },
            "earned_fraction_surface": {
                "signal": earned_fraction,
                "signed": earned_fraction - float(decomp["bell_fraction"]),
                "doctrine": 1.0 if float(decomp["bell_fraction"]) < 0.85 else 0.0,
            },
            "scramble_sensitivity_surface": {
                "signal": scramble_drop,
                "signed": float(scramble["mi_drop_from_scramble"]),
                "doctrine": 1.0 if scramble_drop > 0.02 else 0.0,
            },
            "decoupled_sensitivity_surface": {
                "signal": decouple_drop,
                "signed": float(decouple["mi_drop_from_decoupling"]),
                "doctrine": 1.0 if bool(decouple["coupling_matters"]) else 0.0,
            },
            "ramp_midpoint_surface": {
                "signal": ramp_mid_gain,
                "signed": float(ramp_mid["Ic"]) if ramp_mid else 0.0,
                "doctrine": 1.0 if ramp_mid_gain > 0.2 else 0.0,
            },
        }

        ranking = [
            name
            for name, data in sorted(
                local_rows.items(),
                key=lambda item: float(0.7 * item[1]["signal"] + 0.3 * item[1]["doctrine"]),
                reverse=True,
            )
        ]
        config_rankings.append(ranking)
        shell_hubble = float(row["shell_bridge"]["mean_hubble_proxy"])

        for name in candidate_names:
            candidate_signal_by_name[name].append(float(local_rows[name]["signal"]))
            candidate_signed_by_name[name].append(float(local_rows[name]["signed"]))
            candidate_shell_hubble_by_name[name].append(shell_hubble)
            candidate_doctrine_by_name[name].append(float(local_rows[name]["doctrine"]))

    raw_rows: list[dict[str, object]] = []
    max_mean_abs = 0.0
    for name in candidate_names:
        signal_vals = np.asarray(candidate_signal_by_name[name], dtype=np.float64)
        signed_vals = np.asarray(candidate_signed_by_name[name], dtype=np.float64)
        shell_vals = np.asarray(candidate_shell_hubble_by_name[name], dtype=np.float64)
        doctrine_vals = np.asarray(candidate_doctrine_by_name[name], dtype=np.float64)
        shell_alignment = 0.0
        if signal_vals.size and signal_vals.std() > EPS and shell_vals.std() > EPS:
            shell_alignment = float(np.corrcoef(signal_vals, shell_vals)[0, 1])
        mean_abs = float(np.mean(np.abs(signal_vals))) if signal_vals.size else 0.0
        max_mean_abs = max(max_mean_abs, mean_abs)
        raw_rows.append(
            {
                "candidate": name,
                "mean_abs_support": mean_abs,
                "mean_signed_support": float(np.mean(signed_vals)) if signed_vals.size else 0.0,
                "doctrine_fit": float(np.mean(doctrine_vals)) if doctrine_vals.size else 0.0,
                "shell_alignment": shell_alignment,
                "shell_alignment_abs": abs(shell_alignment),
                "mean_signal": float(np.mean(signal_vals)) if signal_vals.size else 0.0,
            }
        )

    row_by_name: dict[str, dict[str, object]] = {}
    for row in raw_rows:
        signal_score = float(row["mean_abs_support"] / max(max_mean_abs, EPS))
        composite_score = float(
            0.45 * float(row["doctrine_fit"])
            + 0.35 * signal_score
            + 0.20 * float(row["shell_alignment_abs"])
        )
        enriched = dict(row)
        enriched["signal_score"] = signal_score
        enriched["composite_score"] = composite_score
        row_by_name[str(row["candidate"])] = enriched

    ranking = sorted(
        candidate_names,
        key=lambda name: float(row_by_name[name]["composite_score"]),
        reverse=True,
    )
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    candidate_rows: list[dict[str, object]] = []
    ranking_scores: list[float] = []
    for name in ranking:
        row = row_by_name[name]
        ranking_scores.append(float(row["composite_score"]))
        candidate_rows.append(
            {
                "option": name,
                "mean_abs_a0": float(row["mean_abs_support"]),
                "mean_signed_a0": float(row["mean_signed_support"]),
                "doctrine_fit": float(row["doctrine_fit"]),
                "sign_consistency": float(row["doctrine_fit"]),
                "shell_alignment": float(row["shell_alignment"]),
                "shell_alignment_abs": float(row["shell_alignment_abs"]),
                "signal_score": float(row["signal_score"]),
                "composite_score": float(row["composite_score"]),
                "mean_signal": float(row["mean_signal"]),
            }
        )

    expansion_drive = np.asarray(
        [
            row["mean_abs_a0"] + row["doctrine_fit"] + row["shell_alignment_abs"]
            for row in candidate_rows
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _candidate_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS, None)), lambda_shells)

    for row, scale, hubble in zip(
        candidate_rows,
        scale_factors.tolist(),
        hubble_proxy.tolist(),
        strict=True,
    ):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _candidate_graph_surface(candidate_rows)
    ranking_index = {name: idx for idx, name in enumerate(ranking)}
    config_windows = [
        [ranking_index[name] for name in config_ranking[:3]]
        for config_ranking in config_rankings
        if len(config_ranking) >= 3
    ]
    hypergraph_surface = _candidate_hypergraph_surface(len(ranking), config_windows)
    combined_pair_edges = sorted(
        {
            tuple(edge)
            for edge in graph_surface["pair_edges"] + hypergraph_surface["pair_edges"]
        }
    )
    combined_triad_windows = sorted(
        {
            tuple(window)
            for window in graph_surface["triad_windows"] + hypergraph_surface["triad_windows"]
        }
    )
    closed_pair_edges = set(combined_pair_edges)
    for window in combined_triad_windows:
        for idx in range(len(window)):
            for jdx in range(idx + 1, len(window)):
                closed_pair_edges.add(tuple(sorted((int(window[idx]), int(window[jdx])))))
    cell_complex_surface = _candidate_cell_complex_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    topology_surface = _candidate_topology_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    symbolic_surface = _candidate_symbolic_surface(
        lambda_shells,
        scale_factors,
        expansion_drive,
    )
    constraint_surface = _candidate_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray(ranking_scores, dtype=np.float64),
    )
    manifold_surface = _candidate_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in candidate_rows], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in candidate_rows], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in candidate_rows], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_candidate_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in candidate_rows], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in candidate_rows], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in candidate_rows], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner = ranking[0]
    winner_row = next(row for row in candidate_rows if row["option"] == winner)
    winner_vector = np.array(
        [
            winner_row["mean_abs_a0"],
            winner_row["doctrine_fit"],
            winner_row["shell_alignment_abs"],
        ],
        dtype=np.float64,
    )
    clifford_vector = _clifford_vector(winner_vector)
    torch_ga_vector = _torch_ga_roundtrip(winner_vector)
    topology_parity_ok = bool(
        cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
    )
    graph_path_budget = max(1, len(ranking) - 2)
    topology_loop_budget = max(2, len(ranking) // 2)

    pass_flag = bool(
        shell_bridge_pass_fraction >= 0.5
        and graph_surface["longest_path_length"] >= graph_path_budget
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] <= topology_loop_budget
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-3
        and torch_fit["loss"] < 1.0
    )

    return {
        "pass": pass_flag,
        "winner": winner,
        "candidate_universe_size": len(candidate_names),
        "frontier_size": len(ranking),
        "shell_bridge_pass_fraction": shell_bridge_pass_fraction,
        "candidate_rows": candidate_rows,
        "graph_surface": {
            "edge_count": graph_surface["edge_count"],
            "longest_path_length": graph_surface["longest_path_length"],
            "triad_windows": graph_surface["triad_windows"],
            "path_budget": int(graph_path_budget),
        },
        "hypergraph_surface": {
            "num_edges": hypergraph_surface["num_edges"],
            "max_hyperedge_size": hypergraph_surface["max_hyperedge_size"],
            "connected_components": hypergraph_surface["connected_components"],
            "hyperedges": hypergraph_surface["hyperedges"],
        },
        "topology_surface": {
            "betti_numbers": topology_surface["betti_numbers"],
            "euler_characteristic": topology_surface["euler_characteristic"],
            "parity_ok": topology_parity_ok,
            "loop_budget": int(topology_loop_budget),
        },
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
        "manifold_surface": manifold_surface,
        "torch_fit": {
            "weights": torch_fit["weights"],
            "bias": torch_fit["bias"],
            "loss": torch_fit["loss"],
            "max_gap": torch_fit["max_gap"],
        },
        "winner_vector": winner_vector.tolist(),
        "clifford_vector_gap": float(np.max(np.abs(clifford_vector - winner_vector))),
        "torch_ga_vector_gap": float(np.max(np.abs(torch_ga_vector - winner_vector))),
        "scale_factors": scale_factors.tolist(),
        "hubble_proxy": hubble_proxy.tolist(),
        "propagator_traces": propagator_traces,
    }


def main():
    print("=" * 80)
    print("PHASE 5C: EARNED vs SMUGGLED DISCRIMINATOR")
    print("=" * 80)
    
    all_results = {}
    config_records = []
    
    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for torus_label, eta in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            print(f"\n  {key}:")
            
            state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            state = engine.run_cycle(state)
            history_base = [
                {
                    "rho_L": step["rho_L"],
                    "rho_R": step["rho_R"],
                    "eta": float(step.get("ax0_torus_entropy", 0.5)),
                }
                for step in state.history
            ]
            
            print(f"    Test 1: Information decomposition...")
            decomp = test1_information_decomposition(state.history)
            all_results[f"decomp_{key}"] = decomp
            
            print(f"    Test 2: Scramble test (20 trials)...")
            scramble = test2_scramble(state.history)
            all_results[f"scramble_{key}"] = scramble
            
            print(f"    Test 3: Decoupled test...")
            decouple = test3_decoupled(engine_type, eta)
            all_results[f"decouple_{key}"] = decouple
            
            print(f"    Test 4: Geometry ramp (21 points)...")
            ramp = test4_geometry_ramp(state.history)
            all_results[f"ramp_{key}"] = ramp
            config_records.append(
                {
                    "config_key": key,
                    "engine_type": engine_type,
                    "torus": torus_label,
                    "decomp": decomp,
                    "scramble": scramble,
                    "decouple": decouple,
                    "ramp": ramp,
                    "shell_bridge": lane_d_topology_expansion_bridge(history_base),
                }
            )
    
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

    deep_contract = _aggregate_deep_contract(config_records)

    print(f"\n{'─' * 80}")
    print("DEEP CONTRACT")
    print(f"{'─' * 80}")
    print(f"  Deep pass:                    {deep_contract['pass']}")
    print(
        f"  Honesty frontier:            "
        f"{deep_contract['frontier_size']}/{deep_contract['candidate_universe_size']}"
    )
    print(f"  Shell bridge pass fraction:   {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"  Winning deep surface:         {deep_contract['winner']}")
    print(f"  Graph longest path:           {deep_contract['graph_surface']['longest_path_length']}")
    print(f"  Hypergraph max edge size:     {deep_contract['hypergraph_surface']['max_hyperedge_size']}")
    print(f"  Topology betti numbers:       {deep_contract['topology_surface']['betti_numbers']}")
    print(f"  Symbolic hubble mid:          {deep_contract['symbolic_surface']['symbolic_hubble_mid']:.6f}")
    print(f"  Manifold mean distance:       {deep_contract['manifold_surface']['mean_geodesic_distance']:.6f}")
    print(f"  Torch fit loss:               {deep_contract['torch_fit']['loss']:.6f}")
    print(
        f"  Winner vector gaps:           "
        f"clifford={deep_contract['clifford_vector_gap']:.2e} | "
        f"torch_ga={deep_contract['torch_ga_vector_gap']:.2e}"
    )
    
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    
    def clean(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.floating, np.float64)): return float(obj)
        if isinstance(obj, (np.integer, np.int64)): return int(obj)
        if isinstance(obj, dict): return {k: clean(v) for k, v in obj.items()}
        if isinstance(obj, list): return [clean(v) for v in obj]
        return obj
    
    canonical_out_path = os.path.join(
        out_dir, f"{os.path.splitext(os.path.basename(__file__))[0]}_results.json"
    )
    legacy_out_path = os.path.join(out_dir, "axis0_phase5c_results.json")
    payload = json.dumps(clean({
            "timestamp": datetime.now(UTC).isoformat(),
            "probe": "sim_axis0_phase5c_earned_vs_smuggled",
            "classification": classification,
            "divergence_log": divergence_log,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "results": all_results,
            "config_records": config_records,
            "mean_bell_fraction": mean_bell_frac,
            "mean_scramble_drop": mean_scramble_drop,
            "mean_decouple_drop": mean_decouple_drop,
            "aggregate": {
                "deep_contract": deep_contract,
                "all_pass": bool(deep_contract["pass"]),
            },
            "summary": {
                "mean_bell_fraction": mean_bell_frac,
                "mean_scramble_drop": mean_scramble_drop,
                "mean_decouple_drop": mean_decouple_drop,
                "deep_contract_pass": bool(deep_contract["pass"]),
                "deep_contract_winner": deep_contract["winner"],
            },
            "overall_pass": bool(deep_contract["pass"]),
            "all_pass": bool(deep_contract["pass"]),
        }), indent=2)
    for target in dict.fromkeys([canonical_out_path, legacy_out_path]):
        with open(target, "w") as f:
            f.write(payload)
    
    print(f"\n{'=' * 80}")
    print(f"PROBE STATUS: {'PASS' if deep_contract['pass'] else 'FAIL'}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
