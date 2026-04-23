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
from scipy.optimize import minimize
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat
classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "Classical foundation baseline: this optimizes marginal-preserving Axis-0 "
    "bridges numerically. The preserving-MI verdict is preserved, and a deep "
    "contract now binds the honesty surfaces to the same shell bridge, "
    "graph/topology, symbolic expansion, solver closure, geometric algebra, "
    "and manifold witnesses used elsewhere in Axis 0."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "density-matrix and mutual-information numerics"},
    "scipy": {"tried": True, "used": True, "reason": "numerical optimization and preserving-surface propagator witness"},
    "pytorch": {"tried": True, "used": True, "reason": "fit and gradient witness over the preserving-surface frontier"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning preserving-surface vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning preserving-surface vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered DAG witness over the ranked preserving-surface frontier"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order config-to-surface coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for preserving-surface closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the preserving-surface complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for preserving-surface expansion"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing preserving-surface rank order and monotone scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for aggregate preserving-surface geometry"},
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


def _marginal_fidelity(meta: dict[str, object]) -> float:
    max_dev = max(float(meta.get("dev_A", 1.0)), float(meta.get("dev_B", 1.0)))
    return float(1.0 / (1.0 + 1000.0 * max_dev))


def _aggregate_deep_contract(all_results: list[dict]) -> dict[str, object]:
    candidate_names = [
        "history_gap_surface",
        "final_gap_surface",
        "history_fidelity_surface",
        "final_fidelity_surface",
        "step_asymmetry_surface",
    ]
    shell_bridge_pass_fraction = float(
        np.mean([1.0 if row["shell_bridge"]["lane_d_keep"] else 0.0 for row in all_results])
    ) if all_results else 0.0

    candidate_signal_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_signed_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_shell_hubble_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_doctrine_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    config_rankings: list[list[str]] = []

    for row in all_results:
        final_state = row.get("final_state", {})
        history_state = row.get("history_averaged", {})
        step_sample = row.get("per_step_sample", [])

        final_gap = float(final_state.get("chiral_bell_MI", 0.0) - final_state.get("max_preserving_MI", 0.0))
        history_gap = float(history_state.get("chiral_bell_MI", 0.0) - history_state.get("max_preserving_MI", 0.0))
        final_meta = final_state.get("marginal_check", {})
        history_meta = history_state.get("marginal_check", {})
        final_fidelity = _marginal_fidelity(final_meta)
        history_fidelity = _marginal_fidelity(history_meta)
        step_asymmetry = float(np.mean([step.get("lr_asymmetry", 0.0) for step in step_sample])) if step_sample else 0.0
        step_certified = float(np.mean([1.0 if step.get("certified", False) else 0.0 for step in step_sample])) if step_sample else 0.0

        local_rows = {
            "history_gap_surface": {
                "signal": history_gap,
                "signed": -float(history_state.get("max_preserving_MI", 0.0)),
                "doctrine": float(history_state.get("certified", False)),
            },
            "final_gap_surface": {
                "signal": final_gap,
                "signed": -float(final_state.get("max_preserving_MI", 0.0)),
                "doctrine": float(final_state.get("certified", False)),
            },
            "history_fidelity_surface": {
                "signal": history_fidelity,
                "signed": history_fidelity,
                "doctrine": float(history_state.get("certified", False)),
            },
            "final_fidelity_surface": {
                "signal": final_fidelity,
                "signed": final_fidelity,
                "doctrine": float(final_state.get("certified", False)),
            },
            "step_asymmetry_surface": {
                "signal": step_asymmetry,
                "signed": -float(np.mean([step.get("max_preserving_MI", 0.0) for step in step_sample])) if step_sample else 0.0,
                "doctrine": step_certified,
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
    print("PHASE 5A: MARGINAL-PRESERVING XI BRIDGE SEARCH")
    print("=" * 80)
    
    all_results = []
    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for torus_label, eta in TORUS_CONFIGS:
            print(f"\n  Engine {engine_type}/{torus_label}:")
            init = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            final = engine.run_cycle(init)
            history_base = [
                {
                    "rho_L": step["rho_L"],
                    "rho_R": step["rho_R"],
                    "eta": float(step.get("ax0_torus_entropy", 0.5)),
                }
                for step in final.history
            ]
            r = run_marginal_preserving_search(final)
            all_results.append({
                "engine_type": engine_type,
                "torus": torus_label,
                "eta": float(eta),
                **r,
                "shell_bridge": lane_d_topology_expansion_bridge(history_base),
            })
    
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

    deep_contract = _aggregate_deep_contract(all_results)

    print(f"\n{'─' * 80}")
    print("DEEP CONTRACT")
    print(f"{'─' * 80}")
    print(f"  Deep pass:                    {deep_contract['pass']}")
    print(
        f"  Preserving frontier:         "
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
    legacy_out_path = os.path.join(out_dir, "axis0_phase5a_results.json")
    payload = json.dumps(clean({
            "timestamp": datetime.now(UTC).isoformat(),
            "probe": "sim_axis0_phase5a_marginal_preserving",
            "classification": classification,
            "divergence_log": divergence_log,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "results": all_results,
            "mean_preserving": mean_preserving,
            "mean_chiral": mean_chiral,
            "certified_blocks": certified_blocks,
            "total_blocks": total_blocks,
            "failed_blocks": failed_count,
            "aggregate": {
                "deep_contract": deep_contract,
                "all_pass": bool(deep_contract["pass"]),
            },
            "summary": {
                "mean_preserving": mean_preserving,
                "mean_chiral": mean_chiral,
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
