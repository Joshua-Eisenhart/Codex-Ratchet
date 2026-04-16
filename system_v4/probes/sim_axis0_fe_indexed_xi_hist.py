#!/usr/bin/env python3
"""
Axis 0 Fe-Indexed Xi_hist Probe
=================================
Tests whether indexing the Xi_hist construction to Fe-transition events
and using a 7-step compression window produces higher MI/Ic than
the Phase 4 full-trajectory winner.

Motivation (AXIS0_EC3_OPERATOR_COARISING_NOTE.md):
  - ga0 and MI co-arise at every step; peak at Fe-transition events
  - Fe steps carry MI=1.932 vs 1.750 for non-Fe steps (~10% higher)
  - T1 backward MI asymmetry peaks at lag=7 (compression horizon)
  - lag=4 dip confirms one EC-3 cycle = 4 steps; horizon = 1.75 cycles = 7 steps

Three bridge constructions tested against Phase 4 baseline:

  A — Phase 4 winner (baseline)
      cross_s1_symmetric_retro: full 32-step trajectory,
      exponential attractor-proximity weighting over all 31 pairs.
      MI=1.539 from prior campaign; recomputed here for direct comparison.

  B — Fe-indexed 7-step window
      For each of the 8 Fe-transition steps in a 32-step trajectory:
        take the 7-step window [t_Fe-6 .. t_Fe]
        build cross-s1 symmetric bridge within the window
        weight by attractor-proximity within the window
      Average across 8 Fe windows.

  C — Fe-transition pairs only
      Only use pairs (t, t+1) where step t+1 is a Fe-transition.
      These 8 pairs capture the Ti→Fe co-arising event directly.
      Weight by Fe-step MI magnitude.

  D — 7-step rolling window (lag=7 peak, no Fe indexing)
      For each step t, use the pair (t, t+7) — the maximum-asymmetry lag.
      Tests whether the 7-step lag alone (without Fe indexing) already wins.

FEP framing note:
  The Fe step is NOT the sensory correction in a strict FEP sense.
  Phase5A certified marginal-preserving MI ≈ 0 — the predictive prior
  (Bell bridge) dominates completely. The Fe jump is where the predictive
  model is INSTANTIATED (marginals expand), not where it is corrected by
  sensory data. The entire 4-step cycle is prediction unfolding.
  The 25%/75% Fe/non-Fe split is the ratio of instantiation to exploration,
  not correction to prediction.
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
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat
classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "Classical foundation baseline: this probes Fe-indexed Xi history bridges "
    "numerically. The bridge bakeoff is preserved, and a deep contract now "
    "binds the bridge ranking to the same shell bridge, ordered graph/topology, "
    "symbolic expansion, solver closure, geometric algebra, and manifold "
    "witnesses used elsewhere in Axis 0."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "history-window bridge construction, bridge scoring, and aggregate numerics"},
    "scipy": {"tried": True, "used": True, "reason": "matrix exponential propagator for bridge-ranking expansion updates"},
    "pytorch": {"tried": True, "used": True, "reason": "fit and gradient witness over aggregate bridge features"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning Xi-history bridge vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning Xi-history bridge vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered DAG witness over the ranked Xi-history bridges"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order config-to-bridge coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for bridge-ranking closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the Xi-history bridge complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for bridge expansion trends"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing bridge rank order and monotone scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for aggregate bridge geometry"},
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
    _option_cell_complex_surface as _bridge_cell_complex_surface,
    _option_constraint_surface as _bridge_constraint_surface,
    _option_graph_surface as _bridge_graph_surface,
    _option_hypergraph_surface as _bridge_hypergraph_surface,
    _option_manifold_surface as _bridge_manifold_surface,
    _option_scale_history as _bridge_scale_history,
    _option_symbolic_surface as _bridge_symbolic_surface,
    _option_topology_surface as _bridge_topology_surface,
    _torch_ga_roundtrip,
    _torch_option_fit as _torch_bridge_fit,
)

TORUS_CONFIGS = [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]
BRIDGE_ORDER = [
    "A_phase4_winner",
    "B_fe_indexed",
    "C_fe_pairs_only",
    "D_lag7_pairs",
]
PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL = np.outer(PSI_MINUS, PSI_MINUS.conj())
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
EPS = 1e-12
WINDOW = 7   # compression horizon (steps)


# --------------------------------------------------------------------------- #
# Utilities                                                                    #
# --------------------------------------------------------------------------- #

def vne(rho: np.ndarray) -> float:
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0


def ptr_B(r): return np.trace(r.reshape(2, 2, 2, 2), axis1=1, axis2=3)
def ptr_A(r): return np.trace(r.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def mi_val(rho: np.ndarray) -> float:
    return max(0.0, vne(ptr_B(rho)) + vne(ptr_A(rho)) - vne(rho))


def ic_val(rho: np.ndarray) -> float:
    return vne(ptr_A(rho)) - vne(rho)


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(s @ rho)))
                     for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def lr_asym(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0.01, 0.99))


def cross_s1_symmetric(rho_L1: np.ndarray, rho_R1: np.ndarray,
                        rho_L2: np.ndarray, rho_R2: np.ndarray) -> np.ndarray:
    """Phase 4 winner pattern: symmetric forward+backward Bell bridge."""
    p_f = lr_asym(rho_L1, rho_R2)
    rho_f = _ensure_valid_density((1 - p_f) * np.kron(rho_L1, rho_R2) + p_f * BELL)
    p_b = lr_asym(rho_L2, rho_R1)
    rho_b = _ensure_valid_density((1 - p_b) * np.kron(rho_L2, rho_R1) + p_b * BELL)
    return _ensure_valid_density(0.5 * rho_f + 0.5 * rho_b)


# --------------------------------------------------------------------------- #
# Bridge A — Phase 4 winner (baseline)                                        #
# --------------------------------------------------------------------------- #

def bridge_A_phase4_winner(history: list[dict]) -> np.ndarray:
    """Full trajectory, exponential attractor-proximity weighting."""
    T = len(history)
    states, weights = [], []
    for i in range(T - 1):
        rho = cross_s1_symmetric(
            history[i]["rho_L"], history[i]["rho_R"],
            history[i + 1]["rho_L"], history[i + 1]["rho_R"],
        )
        states.append(rho)
        weights.append(np.exp(-0.1 * (T - 2 - i)))
    weights = np.array(weights) / np.sum(weights)
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


# --------------------------------------------------------------------------- #
# Bridge B — Fe-indexed 7-step window                                         #
# --------------------------------------------------------------------------- #

def bridge_B_fe_indexed(history: list[dict]) -> np.ndarray:
    """
    For each Fe-transition step: build Phase 4 bridge within 7-step window.
    Weight each window by the Fe-step's MI magnitude (Fe steps with higher MI
    carry more information about the compression horizon).
    """
    fe_steps = [i for i, s in enumerate(history) if s["op_name"] == "Fe"]

    window_rhos, window_weights = [], []
    for t_fe in fe_steps:
        win_start = max(0, t_fe - (WINDOW - 1))
        window = history[win_start: t_fe + 1]
        if len(window) < 2:
            continue

        # Fe-step MI magnitude as window weight
        rho_L_fe = history[t_fe]["rho_L"]
        rho_R_fe = history[t_fe]["rho_R"]
        p = lr_asym(rho_L_fe, rho_R_fe)
        fe_rho = _ensure_valid_density((1 - p) * np.kron(rho_L_fe, rho_R_fe) + p * BELL)
        fe_mi = mi_val(fe_rho)

        # Build bridge within window using attractor-proximity weighting
        inner_states, inner_weights = [], []
        W = len(window)
        for j in range(W - 1):
            rho = cross_s1_symmetric(
                window[j]["rho_L"], window[j]["rho_R"],
                window[j + 1]["rho_L"], window[j + 1]["rho_R"],
            )
            inner_states.append(rho)
            inner_weights.append(np.exp(-0.1 * (W - 2 - j)))  # attractor-proximity

        inner_weights = np.array(inner_weights) / np.sum(inner_weights)
        window_rho = _ensure_valid_density(
            sum(w * s for w, s in zip(inner_weights, inner_states))
        )
        window_rhos.append(window_rho)
        window_weights.append(fe_mi)

    window_weights = np.array(window_weights) / np.sum(window_weights)
    return _ensure_valid_density(
        sum(w * s for w, s in zip(window_weights, window_rhos))
    )


# --------------------------------------------------------------------------- #
# Bridge C — Fe-transition pairs only                                         #
# --------------------------------------------------------------------------- #

def bridge_C_fe_pairs_only(history: list[dict]) -> np.ndarray:
    """
    Only Ti→Fe pairs: step i (Ti) and step i+1 (Fe).
    The direct co-arising event. Weight by Fe-step MI magnitude.
    """
    states, weights = [], []
    for i in range(len(history) - 1):
        if history[i + 1]["op_name"] != "Fe":
            continue
        rho = cross_s1_symmetric(
            history[i]["rho_L"], history[i]["rho_R"],
            history[i + 1]["rho_L"], history[i + 1]["rho_R"],
        )
        p = lr_asym(history[i + 1]["rho_L"], history[i + 1]["rho_R"])
        fe_rho = _ensure_valid_density(
            (1 - p) * np.kron(history[i + 1]["rho_L"], history[i + 1]["rho_R"]) + p * BELL
        )
        fe_mi = mi_val(fe_rho)
        states.append(rho)
        weights.append(fe_mi)

    weights = np.array(weights) / np.sum(weights)
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


# --------------------------------------------------------------------------- #
# Bridge D — 7-step lag pairs (no Fe indexing)                               #
# --------------------------------------------------------------------------- #

def bridge_D_lag7_pairs(history: list[dict]) -> np.ndarray:
    """
    Cross-temporal pairs at lag=7 (the compression horizon).
    No Fe indexing — tests whether the lag alone explains the gain.
    Exponential attractor-proximity weighting over all lag=7 pairs.
    """
    T = len(history)
    lag = WINDOW  # 7
    states, weights = [], []
    for i in range(T - lag):
        rho = cross_s1_symmetric(
            history[i]["rho_L"], history[i]["rho_R"],
            history[i + lag]["rho_L"], history[i + lag]["rho_R"],
        )
        states.append(rho)
        weights.append(np.exp(-0.1 * (T - lag - 1 - i)))

    weights = np.array(weights) / np.sum(weights)
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


def _aggregate_deep_contract(all_results: list[dict]) -> dict[str, object]:
    shell_bridge_pass_fraction = float(
        np.mean([1.0 if cfg["shell_bridge"]["lane_d_keep"] else 0.0 for cfg in all_results])
    ) if all_results else 0.0

    bridge_values_by_name: dict[str, list[float]] = {name: [] for name in BRIDGE_ORDER}
    bridge_shell_hubble_by_name: dict[str, list[float]] = {name: [] for name in BRIDGE_ORDER}
    bridge_win_by_name: dict[str, list[float]] = {name: [] for name in BRIDGE_ORDER}
    per_config_rankings: list[list[str]] = []

    for cfg in all_results:
        shell_hubble = float(cfg["shell_bridge"]["mean_hubble_proxy"])
        ranking = sorted(
            BRIDGE_ORDER,
            key=lambda name: float(cfg["bridges"][name]["mi"]),
            reverse=True,
        )
        per_config_rankings.append(ranking)
        for bridge_name in BRIDGE_ORDER:
            bridge_values_by_name[bridge_name].append(float(cfg["bridges"][bridge_name]["mi"]))
            bridge_shell_hubble_by_name[bridge_name].append(shell_hubble)
            bridge_win_by_name[bridge_name].append(1.0 if cfg["winner"] == bridge_name else 0.0)

    raw_rows: list[dict[str, object]] = []
    max_mean_abs = 0.0
    for bridge_name in BRIDGE_ORDER:
        values = np.asarray(bridge_values_by_name[bridge_name], dtype=np.float64)
        shell_vals = np.asarray(bridge_shell_hubble_by_name[bridge_name], dtype=np.float64)
        win_vals = np.asarray(bridge_win_by_name[bridge_name], dtype=np.float64)
        shell_alignment = 0.0
        if values.size and values.std() > EPS and shell_vals.std() > EPS:
            shell_alignment = float(np.corrcoef(values, shell_vals)[0, 1])
        mean_abs = float(np.mean(np.abs(values))) if values.size else 0.0
        max_mean_abs = max(max_mean_abs, mean_abs)
        raw_rows.append(
            {
                "bridge": bridge_name,
                "mean_abs_support": mean_abs,
                "mean_signed_support": float(np.mean(values)) if values.size else 0.0,
                "win_fraction": float(np.mean(win_vals)) if win_vals.size else 0.0,
                "shell_alignment": shell_alignment,
                "shell_alignment_abs": abs(shell_alignment),
            }
        )

    row_by_name: dict[str, dict[str, object]] = {}
    for row in raw_rows:
        signal_score = float(row["mean_abs_support"] / max(max_mean_abs, EPS))
        composite_score = float(
            0.45 * float(row["win_fraction"])
            + 0.35 * signal_score
            + 0.20 * float(row["shell_alignment_abs"])
        )
        enriched = dict(row)
        enriched["signal_score"] = signal_score
        enriched["composite_score"] = composite_score
        row_by_name[str(row["bridge"])] = enriched

    ranking = sorted(
        BRIDGE_ORDER,
        key=lambda name: float(row_by_name[name]["composite_score"]),
        reverse=True,
    )
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    bridge_rows: list[dict[str, object]] = []
    ranking_scores: list[float] = []
    for bridge_name in ranking:
        row = row_by_name[bridge_name]
        ranking_scores.append(float(row["composite_score"]))
        bridge_rows.append(
            {
                "option": bridge_name,
                "mean_abs_a0": float(row["mean_abs_support"]),
                "mean_signed_a0": float(row["mean_signed_support"]),
                "doctrine_fit": float(row["win_fraction"]),
                "sign_consistency": float(row["win_fraction"]),
                "shell_alignment": float(row["shell_alignment"]),
                "shell_alignment_abs": float(row["shell_alignment_abs"]),
                "signal_score": float(row["signal_score"]),
                "composite_score": float(row["composite_score"]),
            }
        )

    expansion_drive = np.asarray(
        [
            row["mean_abs_a0"] + row["doctrine_fit"] + row["shell_alignment_abs"]
            for row in bridge_rows
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _bridge_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(
        np.log(np.clip(scale_factors, EPS, None)),
        lambda_shells,
    )

    for row, scale, hubble in zip(
        bridge_rows,
        scale_factors.tolist(),
        hubble_proxy.tolist(),
        strict=True,
    ):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _bridge_graph_surface(bridge_rows)
    ranking_index = {name: idx for idx, name in enumerate(ranking)}
    config_windows = [
        [ranking_index[name] for name in config_ranking[:3]]
        for config_ranking in per_config_rankings
    ]
    hypergraph_surface = _bridge_hypergraph_surface(len(ranking), config_windows)
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
    cell_complex_surface = _bridge_cell_complex_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    topology_surface = _bridge_topology_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    symbolic_surface = _bridge_symbolic_surface(
        lambda_shells,
        scale_factors,
        expansion_drive,
    )
    constraint_surface = _bridge_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray(ranking_scores, dtype=np.float64),
    )
    manifold_surface = _bridge_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in bridge_rows], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in bridge_rows], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in bridge_rows], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_bridge_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in bridge_rows], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in bridge_rows], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in bridge_rows], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner = ranking[0]
    winner_row = next(row for row in bridge_rows if row["option"] == winner)
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

    pass_flag = bool(
        shell_bridge_pass_fraction >= 0.5
        and graph_surface["longest_path_length"] >= len(ranking) - 1
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] == 0
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-2
        and torch_fit["loss"] < 1.0
    )

    return {
        "pass": pass_flag,
        "winner": winner,
        "shell_bridge_pass_fraction": shell_bridge_pass_fraction,
        "bridge_rows": bridge_rows,
        "graph_surface": {
            "edge_count": graph_surface["edge_count"],
            "longest_path_length": graph_surface["longest_path_length"],
            "triad_windows": graph_surface["triad_windows"],
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


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #

def run_torus(engine_type: int, torus_name: str, torus_val: float) -> dict:
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=torus_val)
    final_state = engine.run_cycle(state)
    history = final_state.history
    history_base = []
    for step in history:
        history_base.append(
            {
                "rho_L": step["rho_L"],
                "rho_R": step["rho_R"],
                "eta": float(step.get("ax0_torus_entropy", 0.5)),
            }
        )

    # Fe step statistics
    fe_indices = [i for i, s in enumerate(history) if s["op_name"] == "Fe"]
    mi_series = []
    for i in range(len(history) - 1):
        p = lr_asym(history[i]["rho_L"], history[i + 1]["rho_R"])
        rho = _ensure_valid_density(
            (1 - p) * np.kron(history[i]["rho_L"], history[i + 1]["rho_R"]) + p * BELL
        )
        mi_series.append(mi_val(rho))

    fe_mi_mean = float(np.mean([mi_series[i] for i in fe_indices if i < len(mi_series)]))
    non_fe_mi_mean = float(np.mean([mi_series[i] for i in range(len(mi_series)) if i not in fe_indices]))

    # Build all four bridges
    rho_A = bridge_A_phase4_winner(history)
    rho_B = bridge_B_fe_indexed(history)
    rho_C = bridge_C_fe_pairs_only(history)
    rho_D = bridge_D_lag7_pairs(history)

    results = {}
    for label, rho in [("A_phase4_winner", rho_A), ("B_fe_indexed", rho_B),
                        ("C_fe_pairs_only", rho_C), ("D_lag7_pairs", rho_D)]:
        results[label] = {
            "mi": mi_val(rho),
            "ic": ic_val(rho),
        }

    winner = max(results, key=lambda k: results[k]["mi"])
    winner_mi = results[winner]["mi"]
    baseline_mi = results["A_phase4_winner"]["mi"]
    gain = winner_mi - baseline_mi
    shell_bridge = lane_d_topology_expansion_bridge(history_base)

    print(f"  {engine_type}/{torus_name}: "
          f"A={baseline_mi:.4f} "
          f"B={results['B_fe_indexed']['mi']:.4f} "
          f"C={results['C_fe_pairs_only']['mi']:.4f} "
          f"D={results['D_lag7_pairs']['mi']:.4f} "
          f"| winner={winner} gain={gain:+.4f}")

    return {
        "engine_type": engine_type,
        "torus": torus_name,
        "fe_step_count": len(fe_indices),
        "fe_mi_mean": fe_mi_mean,
        "non_fe_mi_mean": non_fe_mi_mean,
        "fe_advantage": fe_mi_mean - non_fe_mi_mean,
        "bridges": results,
        "winner": winner,
        "winner_mi": winner_mi,
        "baseline_mi": baseline_mi,
        "gain_over_baseline": gain,
        "shell_bridge": shell_bridge,
    }


def main() -> None:
    print("=" * 72)
    print("AXIS 0 Fe-INDEXED Xi_hist PROBE")
    print("=" * 72)
    print("Comparing Fe-indexed bridge constructions against Phase 4 winner.")
    print()
    print("  A = Phase 4 winner (baseline): full trajectory, exp weighting")
    print("  B = Fe-indexed 7-step window: 8 windows at Fe steps, MI-weighted")
    print("  C = Fe pairs only: Ti→Fe adjacent pairs, MI-weighted")
    print("  D = lag=7 pairs: compression horizon lag, no Fe indexing")
    print()

    results = []
    for eng_type in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            r = run_torus(eng_type, torus_name, torus_val)
            results.append(r)

    # Aggregate
    n = len(results)
    winner_counts = {"A_phase4_winner": 0, "B_fe_indexed": 0,
                     "C_fe_pairs_only": 0, "D_lag7_pairs": 0}
    for r in results:
        winner_counts[r["winner"]] += 1

    mean_gains = {
        k: float(np.mean([r["bridges"][k]["mi"] - r["baseline_mi"] for r in results]))
        for k in ["B_fe_indexed", "C_fe_pairs_only", "D_lag7_pairs"]
    }
    mean_mi = {
        k: float(np.mean([r["bridges"][k]["mi"] for r in results]))
        for k in ["A_phase4_winner", "B_fe_indexed", "C_fe_pairs_only", "D_lag7_pairs"]
    }
    mean_ic = {
        k: float(np.mean([r["bridges"][k]["ic"] for r in results]))
        for k in ["A_phase4_winner", "B_fe_indexed", "C_fe_pairs_only", "D_lag7_pairs"]
    }
    mean_fe_adv = float(np.mean([r["fe_advantage"] for r in results]))
    deep_contract = _aggregate_deep_contract(results)

    print()
    print("=" * 72)
    print("OVERALL RESULTS")
    print("=" * 72)
    print(f"  Fe-step MI advantage over non-Fe: {mean_fe_adv:+.4f}")
    print()
    print(f"  {'Bridge':<20} {'mean MI':>8} {'mean Ic':>8} {'gain vs A':>10} {'wins':>5}")
    print(f"  {'-'*55}")
    for k, label in [
        ("A_phase4_winner", "A Phase4 baseline"),
        ("B_fe_indexed",    "B Fe-indexed 7-win"),
        ("C_fe_pairs_only", "C Fe pairs only"),
        ("D_lag7_pairs",    "D lag=7 pairs"),
    ]:
        gain_str = f"{mean_gains.get(k, 0.0):+.4f}" if k != "A_phase4_winner" else "   —"
        print(f"  {label:<20} {mean_mi[k]:>8.4f} {mean_ic[k]:>8.4f} {gain_str:>10} {winner_counts[k]:>5}/{n}")

    print()

    # Interpretation
    best_new = max(["B_fe_indexed", "C_fe_pairs_only", "D_lag7_pairs"],
                   key=lambda k: mean_mi[k])
    best_gain = mean_gains[best_new]

    if best_gain > 0.05:
        print(f"  ✓ KEEP — {best_new} beats Phase 4 winner by {best_gain:+.4f} MI")
        print("    Fe-indexed construction provides meaningful improvement.")
    elif best_gain > 0.0:
        print(f"  ◐ MARGINAL — {best_new} marginally improves by {best_gain:+.4f} MI")
        print("    Fe indexing helps but not dramatically.")
    else:
        print(f"  ✗ KILL — Phase 4 winner holds; Fe indexing adds no MI gain")
        print("    The full-trajectory exponential weighting is already optimal.")

    # FEP framing note
    print()
    print("  FEP framing:")
    print(f"    Fe steps = {results[0]['fe_step_count']}/32 = 25% of trajectory")
    print(f"    Fe MI mean: {float(np.mean([r['fe_mi_mean'] for r in results])):.4f}")
    print(f"    Non-Fe MI: {float(np.mean([r['non_fe_mi_mean'] for r in results])):.4f}")
    print("    Interpretation: Fe is prediction INSTANTIATION, not sensory correction.")
    print("    Phase5A certified marginal-preserving MI ≈ 0 → prediction dominates.")
    print("    The entire 4-step cycle is the prior unfolding; Fe is its peak.")

    print()
    print("─" * 72)
    print("DEEP CONTRACT")
    print("─" * 72)
    print(f"  Deep pass:                    {deep_contract['pass']}")
    print(f"  Shell bridge pass fraction:   {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"  Winning bridge surface:       {deep_contract['winner']}")
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
    print()
    print("================================================================================")
    print(f"PROBE STATUS: {'PASS' if deep_contract['pass'] else 'FAIL'}")
    print("================================================================================")

    def safe(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.bool_,)): return bool(obj)
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, dict): return {k: safe(v) for k, v in obj.items()}
        if isinstance(obj, list): return [safe(v) for v in obj]
        return obj

    output = {
        "timestamp": datetime.now(UTC).isoformat(),
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "compression_horizon_steps": WINDOW,
        "results": safe(results),
        "summary": {
            "winner_counts": winner_counts,
            "mean_mi": mean_mi,
            "mean_ic": mean_ic,
            "mean_gains_vs_A": mean_gains,
            "best_new_bridge": best_new,
            "best_gain": best_gain,
            "mean_fe_advantage": mean_fe_adv,
            "deep_contract_pass": bool(deep_contract["pass"]),
            "deep_contract_winner": deep_contract["winner"],
        },
        "aggregate": {
            "deep_contract": safe(deep_contract),
            "all_pass": bool(deep_contract["pass"]),
        },
        "overall_pass": bool(deep_contract["pass"]),
        "all_pass": bool(deep_contract["pass"]),
    }

    out_path = os.path.join(
        os.path.dirname(__file__),
        "a2_state", "sim_results", "axis0_fe_indexed_xi_hist_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
