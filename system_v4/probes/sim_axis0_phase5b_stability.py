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
    "Classical foundation baseline: this evaluates multi-cycle stability of the "
    "Axis-0 bridge numerically. The legacy stability verdict is preserved, and "
    "a deep contract now binds the stability surfaces to the same shell bridge, "
    "graph/topology, symbolic expansion, solver closure, geometric algebra, "
    "and manifold witnesses used elsewhere in Axis 0."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "multi-cycle bridge stability and convergence numerics"},
    "scipy": {"tried": True, "used": True, "reason": "stability-surface propagator witness"},
    "pytorch": {"tried": True, "used": True, "reason": "fit and gradient witness over the stability frontier"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning stability vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning stability vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered DAG witness over the ranked stability frontier"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order config-to-stability coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for stability closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the stability complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for stability expansion"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing stability rank order and monotone scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for aggregate stability geometry"},
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
from hopf_manifold import (TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER, 
                           random_s3_point, torus_coordinates)
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
    
    return cycle_data, cumulative_history


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


def _aggregate_deep_contract(config_records: list[dict]) -> dict[str, object]:
    candidate_names = [
        "cumulative_mi_surface",
        "cumulative_ic_surface",
        "convergence_surface",
        "random_init_stability_surface",
        "asymmetry_stability_surface",
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
        multi_cycle = row["multi_cycle"]
        random_init = row["random_init"]
        cumulative_mis = np.asarray([entry["winner_cumulative_MI"] for entry in multi_cycle], dtype=np.float64)
        cumulative_ics = np.asarray([entry["winner_cumulative_Ic"] for entry in multi_cycle], dtype=np.float64)
        lr_asym = np.asarray([entry["lr_asymmetry"] for entry in multi_cycle], dtype=np.float64)
        random_mis = np.asarray([entry["winner_MI"] for entry in random_init], dtype=np.float64)
        mi_gap = float(abs(cumulative_mis[-1] - cumulative_mis[0])) if cumulative_mis.size else 0.0
        asym_gap = float(abs(lr_asym[-1] - lr_asym[0])) if lr_asym.size else 0.0
        random_std = float(np.std(random_mis)) if random_mis.size else 0.0

        local_rows = {
            "cumulative_mi_surface": {
                "signal": float(np.mean(cumulative_mis)) if cumulative_mis.size else 0.0,
                "signed": float(cumulative_mis[-1] - cumulative_mis[0]) if cumulative_mis.size else 0.0,
                "doctrine": 1.0 if mi_gap < 0.1 else 0.0,
            },
            "cumulative_ic_surface": {
                "signal": float(np.mean(np.abs(cumulative_ics))) if cumulative_ics.size else 0.0,
                "signed": float(cumulative_ics[-1]) if cumulative_ics.size else 0.0,
                "doctrine": 1.0 if cumulative_ics.size and cumulative_ics[-1] > -0.05 else 0.0,
            },
            "convergence_surface": {
                "signal": float(1.0 / (1.0 + 10.0 * mi_gap)),
                "signed": -mi_gap,
                "doctrine": 1.0 if mi_gap < 0.1 else 0.0,
            },
            "random_init_stability_surface": {
                "signal": float(1.0 / (1.0 + 10.0 * random_std)),
                "signed": -random_std,
                "doctrine": 1.0 if random_std < 0.05 else 0.0,
            },
            "asymmetry_stability_surface": {
                "signal": float(1.0 / (1.0 + 10.0 * asym_gap)),
                "signed": -asym_gap,
                "doctrine": 1.0 if asym_gap < 0.05 else 0.0,
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
    print("PHASE 5B: MULTI-CYCLE STABILITY & CONVERGENCE")
    print("=" * 80)
    
    all_results = {}
    config_records = []
    
    # 1. Multi-cycle
    print("\n  1. Multi-cycle stability (4 cycles each)...")
    for engine_type in (1, 2):
        for torus_label, eta in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            print(f"    {key}...")
            multi_cycle_data, cumulative_history = run_multi_cycle(engine_type, torus_label, eta, n_cycles=4)
            all_results[f"multi_cycle_{key}"] = multi_cycle_data
            history_base = [
                {
                    "rho_L": step["rho_L"],
                    "rho_R": step["rho_R"],
                    "eta": float(step.get("ax0_torus_entropy", 0.5)),
                }
                for step in cumulative_history
            ]
            config_records.append(
                {
                    "config_key": key,
                    "engine_type": engine_type,
                    "torus": torus_label,
                    "multi_cycle": multi_cycle_data,
                    "shell_bridge": lane_d_topology_expansion_bridge(history_base),
                }
            )
    
    # 2. Random initial conditions
    print("\n  2. Random initial conditions (10 each)...")
    for engine_type in (1, 2):
        for torus_label, eta in TORUS_CONFIGS:
            key = f"{engine_type}/{torus_label}"
            print(f"    {key}...")
            random_init_data = run_random_initial_conditions(engine_type, eta, n_inits=10)
            all_results[f"random_init_{key}"] = random_init_data
            target = next(record for record in config_records if record["config_key"] == key)
            target["random_init"] = random_init_data
    
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

    deep_contract = _aggregate_deep_contract(config_records)

    print(f"\n{'─' * 80}")
    print("DEEP CONTRACT")
    print(f"{'─' * 80}")
    print(f"  Deep pass:                    {deep_contract['pass']}")
    print(
        f"  Stability frontier:          "
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
    legacy_out_path = os.path.join(out_dir, "axis0_phase5b_results.json")
    payload = json.dumps(clean({
            "timestamp": datetime.now(UTC).isoformat(),
            "probe": "sim_axis0_phase5b_stability",
            "classification": classification,
            "divergence_log": divergence_log,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "results": all_results,
            "config_records": config_records,
            "multi_cycle_stable": bool(all_stable),
            "random_init_std_range": [float(min(all_random_stds)), float(max(all_random_stds))],
            "aggregate": {
                "deep_contract": deep_contract,
                "all_pass": bool(deep_contract["pass"]),
            },
            "summary": {
                "multi_cycle_stable": bool(all_stable),
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
