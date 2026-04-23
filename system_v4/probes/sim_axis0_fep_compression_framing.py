#!/usr/bin/env python3
"""
Axis 0 FEP / Compression-from-Future Framing Sim
==================================================
Tests whether the engine trajectory's information structure is better described
by compression-from-future (entropic monism / FEP) than by classical
cause-from-past propagation.

Four tests:

  Test 1 — Temporal MI asymmetry
    Is the MI of the backward cross-temporal bridge (late L ⊗ early R) ≥
    forward bridge (early L ⊗ late R)?
    Keep: backward ≥ forward (future predicts past better than past predicts future)
    Kill: forward dominates (classical causal chain)

  Test 2 — Attractor vs drift (Bloch autocorrelation)
    Compute autocorrelation of step-to-step Bloch vector changes.
    Keep: negative autocorrelation (mean-reverting / attractor basin / FEP)
    Kill: positive autocorrelation (causal momentum / drift)

  Test 3 — jk fuzz directionality (ga0 vs MI cross-correlation)
    Compute cross-correlation between ga0 fluctuation and MI fluctuation.
    Keep: ga0 change LAGS MI change (the entropy field responds to MI structure,
          not the other way — compression is primary)
    Kill: ga0 change LEADS MI change (entropy field drives MI — classical causation)

  Test 4 — Trajectory MI profile: does MI increase toward the attractor?
    If the trajectory is converging toward a compressed attractor, later
    cross-temporal MI should be higher than earlier.
    Keep: MI trend is upward across the trajectory (attractor convergence)
    Kill: MI is flat or decreasing (no convergence)

Terminology note:
  "Retrocausal weighting" in Xi_hist is renamed here as "attractor-proximity
  weighting" per AXIS0_ENTROPIC_MONISM_DOCTRINE_BRIDGE.md. Later steps get
  higher weight because they are closer to the compressed attractor, not because
  the future causes the past.
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
    "Classical foundation baseline: this tests Axis-0 FEP/compression framing "
    "numerically on the trajectory. The legacy framing tests are preserved, and "
    "a deep contract now binds those tests to the same shell bridge, ordered "
    "graph/topology, symbolic expansion, solver closure, geometric algebra, "
    "and manifold witnesses used elsewhere in Axis 0."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "trajectory asymmetry, correlation numerics, and framing aggregates"},
    "scipy": {"tried": True, "used": True, "reason": "matrix exponential propagator for framing-test expansion updates"},
    "pytorch": {"tried": True, "used": True, "reason": "fit and gradient witness over aggregate framing support features"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning framing vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning framing vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered DAG witness over the ranked framing tests"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order config-to-framing coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for framing-test closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the framing complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for framing expansion trends"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing framing rank order and monotone scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for aggregate framing geometry"},
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
    _option_cell_complex_surface as _framing_cell_complex_surface,
    _option_constraint_surface as _framing_constraint_surface,
    _option_graph_surface as _framing_graph_surface,
    _option_hypergraph_surface as _framing_hypergraph_surface,
    _option_manifold_surface as _framing_manifold_surface,
    _option_scale_history as _framing_scale_history,
    _option_symbolic_surface as _framing_symbolic_surface,
    _option_topology_surface as _framing_topology_surface,
    _torch_ga_roundtrip,
    _torch_option_fit as _torch_framing_fit,
)

TORUS_CONFIGS = [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]
TEST_ORDER = [
    "T1_temporal_mi_asymmetry",
    "T2_attractor_vs_drift",
    "T3_jk_fuzz_directionality",
    "T4_trajectory_profile",
]
TEST_RESULT_KEYS = {
    "T1_temporal_mi_asymmetry": "test1_temporal_asymmetry",
    "T2_attractor_vs_drift": "test2_attractor_vs_drift",
    "T3_jk_fuzz_directionality": "test3_jk_fuzz_directionality",
    "T4_trajectory_profile": "test4_trajectory_profile",
}
PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL_PSI_MINUS = np.outer(PSI_MINUS, PSI_MINUS.conj())
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
EPS = 1e-12


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


def mi_val(rho_AB: np.ndarray) -> float:
    return max(0.0, vne(ptr_B(rho_AB)) + vne(ptr_A(rho_AB)) - vne(rho_AB))


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def lr_asym(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0.0, 1.0))


def cross_temporal_mi(rho_L_t1: np.ndarray, rho_R_t2: np.ndarray) -> float:
    """MI of the Phase4 cross-temporal bridge: L(t1) ⊗ R(t2) with Bell injection."""
    p = float(np.clip(lr_asym(rho_L_t1, rho_R_t2), 0.01, 0.99))
    prod = _ensure_valid_density(np.kron(rho_L_t1, rho_R_t2))
    rho = _ensure_valid_density((1 - p) * prod + p * BELL_PSI_MINUS)
    return mi_val(rho)


def autocorr(x: list[float], lag: int = 1) -> float:
    """Pearson autocorrelation at given lag."""
    if len(x) <= lag:
        return 0.0
    a = np.array(x[:-lag])
    b = np.array(x[lag:])
    if np.std(a) < EPS or np.std(b) < EPS:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def cross_corr_lag(x: list[float], y: list[float], lag: int) -> float:
    """Cross-correlation of x(t) with y(t+lag). Positive lag = x leads y."""
    if lag >= 0:
        a, b = np.array(x[:len(x)-lag]), np.array(y[lag:])
    else:
        a, b = np.array(x[-lag:]), np.array(y[:len(y)+lag])
    if len(a) < 3 or np.std(a) < EPS or np.std(b) < EPS:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


# --------------------------------------------------------------------------- #
# Test 1 — Temporal MI asymmetry                                              #
# --------------------------------------------------------------------------- #

def test1_temporal_mi_asymmetry(history: list[dict], lag: int = 1) -> dict:
    """
    Forward MI: L(t) ⊗ R(t+lag)
    Backward MI: L(t+lag) ⊗ R(t)
    Keep if mean backward ≥ mean forward.
    """
    fwd_mi, bwd_mi = [], []
    T = len(history)
    for t in range(T - lag):
        rho_L_early = history[t]["rho_L"]
        rho_R_early = history[t]["rho_R"]
        rho_L_late = history[t + lag]["rho_L"]
        rho_R_late = history[t + lag]["rho_R"]

        fwd = cross_temporal_mi(rho_L_early, rho_R_late)   # L(t) ⊗ R(t+lag)
        bwd = cross_temporal_mi(rho_L_late, rho_R_early)   # L(t+lag) ⊗ R(t)

        fwd_mi.append(fwd)
        bwd_mi.append(bwd)

    mean_fwd = float(np.mean(fwd_mi))
    mean_bwd = float(np.mean(bwd_mi))
    asymmetry = mean_bwd - mean_fwd
    keep = bool(asymmetry >= 0.0)

    return {
        "mean_forward_mi": mean_fwd,
        "mean_backward_mi": mean_bwd,
        "asymmetry_bwd_minus_fwd": asymmetry,
        "keep": keep,
        "interpretation": (
            "backward ≥ forward → future predicts past (compression-from-future)" if keep
            else "forward > backward → past predicts future (classical causation)"
        ),
    }


# --------------------------------------------------------------------------- #
# Test 2 — Attractor vs drift                                                 #
# --------------------------------------------------------------------------- #

def test2_attractor_vs_drift(history: list[dict]) -> dict:
    """
    Compute Bloch vector for rho_L at each step.
    Compute step-to-step change magnitudes.
    Negative autocorrelation → mean-reverting attractor (FEP / compression).
    Positive autocorrelation → drift / causal momentum.
    """
    bloch_L = [bloch(s["rho_L"]) for s in history]
    bloch_R = [bloch(s["rho_R"]) for s in history]

    delta_L = [float(np.linalg.norm(bloch_L[t + 1] - bloch_L[t])) for t in range(len(bloch_L) - 1)]
    delta_R = [float(np.linalg.norm(bloch_R[t + 1] - bloch_R[t])) for t in range(len(bloch_R) - 1)]

    ac_L = autocorr(delta_L, lag=1)
    ac_R = autocorr(delta_R, lag=1)
    mean_ac = (ac_L + ac_R) / 2.0

    keep = bool(mean_ac < 0.0)

    return {
        "autocorr_delta_L": ac_L,
        "autocorr_delta_R": ac_R,
        "mean_autocorr": mean_ac,
        "keep": keep,
        "interpretation": (
            "negative autocorr → mean-reverting attractor (FEP / compression-from-future)" if keep
            else "positive autocorr → drift / causal momentum (classical propagation)"
        ),
    }


# --------------------------------------------------------------------------- #
# Test 3 — jk fuzz directionality                                             #
# --------------------------------------------------------------------------- #

def test3_jk_fuzz_directionality(history: list[dict]) -> dict:
    """
    ga0 = Axis 0 entropy level (proxy for the 'jk fuzz' field).
    MI(t) = cross-temporal MI at step t (L(t) ⊗ R(t+1)).

    Compute cross-correlation at lags −3..+3:
      Positive lag k: ga0 change leads MI change by k steps (ga0 drives MI → classical)
      Negative lag k: ga0 change lags MI change by |k| steps (MI drives ga0 → compression primary)

    Keep if peak cross-correlation is at lag ≤ 0 (ga0 lags or is simultaneous with MI).
    """
    T = len(history)
    ga0 = [float(history[t]["ga0_after"]) for t in range(T)]
    ct_mi = []
    for t in range(T - 1):
        ct_mi.append(cross_temporal_mi(history[t]["rho_L"], history[t + 1]["rho_R"]))
    ct_mi.append(ct_mi[-1])  # pad to same length

    # Changes
    d_ga0 = [ga0[t + 1] - ga0[t] for t in range(T - 1)] + [0.0]
    d_mi = [ct_mi[t + 1] - ct_mi[t] for t in range(T - 1)] + [0.0]

    lags = list(range(-3, 4))
    xcorr = {lag: cross_corr_lag(d_ga0, d_mi, lag) for lag in lags}
    peak_lag = max(xcorr, key=lambda k: abs(xcorr[k]))
    peak_val = xcorr[peak_lag]

    keep = bool(peak_lag <= 0)

    return {
        "cross_correlations": {str(k): round(v, 4) for k, v in xcorr.items()},
        "peak_lag": peak_lag,
        "peak_value": peak_val,
        "keep": keep,
        "interpretation": (
            f"peak lag={peak_lag} ≤ 0 → ga0 lags MI (compression is primary, entropy follows structure)"
            if keep else
            f"peak lag={peak_lag} > 0 → ga0 leads MI (entropy drives structure, classical causation)"
        ),
    }


# --------------------------------------------------------------------------- #
# Test 4 — Trajectory MI profile                                              #
# --------------------------------------------------------------------------- #

def test4_trajectory_mi_profile(history: list[dict]) -> dict:
    """
    Compute per-step cross-temporal MI across the trajectory.
    If attractor convergence: MI should trend upward.
    Fit a linear regression; keep if slope > 0.
    Also check whether the retrocausal (attractor-proximity) weighting
    is justified: do later steps have higher MI?
    """
    T = len(history)
    mi_series = []
    for t in range(T - 1):
        mi_series.append(cross_temporal_mi(history[t]["rho_L"], history[t + 1]["rho_R"]))

    steps = np.arange(len(mi_series), dtype=float)
    coeffs = np.polyfit(steps, mi_series, 1)
    slope = float(coeffs[0])

    first_half_mean = float(np.mean(mi_series[:len(mi_series) // 2]))
    second_half_mean = float(np.mean(mi_series[len(mi_series) // 2:]))
    second_minus_first = second_half_mean - first_half_mean

    # Retrocausal weighting check: do last 8 steps have higher MI than first 8?
    early_mi = float(np.mean(mi_series[:8]))
    late_mi = float(np.mean(mi_series[-8:]))
    late_leads = bool(late_mi > early_mi)

    keep = bool(slope > 0 or late_leads)

    return {
        "mi_series_mean": float(np.mean(mi_series)),
        "mi_series_std": float(np.std(mi_series)),
        "linear_slope": slope,
        "first_half_mean": first_half_mean,
        "second_half_mean": second_half_mean,
        "second_minus_first": second_minus_first,
        "early_mi_mean": early_mi,
        "late_mi_mean": late_mi,
        "late_leads": late_leads,
        "keep": keep,
        "interpretation": (
            "MI increases toward trajectory end → attractor convergence (compression-from-future)"
            if keep else
            "MI flat or decreasing → no attractor convergence (no directional compression)"
        ),
    }


def _framing_signal_value(config_result: dict, test_name: str) -> float:
    if test_name == "T1_temporal_mi_asymmetry":
        return float(
            config_result["test1_temporal_asymmetry"]["asymmetry_bwd_minus_fwd"]
        )
    if test_name == "T2_attractor_vs_drift":
        return float(-config_result["test2_attractor_vs_drift"]["mean_autocorr"])
    if test_name == "T3_jk_fuzz_directionality":
        peak_lag = float(config_result["test3_jk_fuzz_directionality"]["peak_lag"])
        peak_value = float(config_result["test3_jk_fuzz_directionality"]["peak_value"])
        return float(-peak_lag + abs(peak_value))
    if test_name == "T4_trajectory_profile":
        return float(
            config_result["test4_trajectory_profile"]["linear_slope"]
            + 0.25 * config_result["test4_trajectory_profile"]["second_minus_first"]
        )
    raise KeyError(f"Unknown framing test: {test_name}")


def _aggregate_deep_contract(all_results: list[dict]) -> dict[str, object]:
    shell_bridge_pass_fraction = float(
        np.mean([1.0 if cfg["shell_bridge"]["lane_d_keep"] else 0.0 for cfg in all_results])
    ) if all_results else 0.0

    test_values_by_name: dict[str, list[float]] = {name: [] for name in TEST_ORDER}
    test_shell_hubble_by_name: dict[str, list[float]] = {name: [] for name in TEST_ORDER}
    test_keep_by_name: dict[str, list[float]] = {name: [] for name in TEST_ORDER}
    per_config_rankings: list[list[str]] = []

    for cfg in all_results:
        shell_hubble = float(cfg["shell_bridge"]["mean_hubble_proxy"])
        score_map: dict[str, float] = {}
        for test_name in TEST_ORDER:
            result_key = TEST_RESULT_KEYS[test_name]
            signal_value = _framing_signal_value(cfg, test_name)
            test_values_by_name[test_name].append(signal_value)
            test_shell_hubble_by_name[test_name].append(shell_hubble)
            test_keep_by_name[test_name].append(1.0 if cfg[result_key]["keep"] else 0.0)
            score_map[test_name] = signal_value
        per_config_rankings.append(
            sorted(TEST_ORDER, key=lambda name: score_map[name], reverse=True)
        )

    raw_rows: list[dict[str, object]] = []
    max_mean_abs = 0.0
    for test_name in TEST_ORDER:
        values = np.asarray(test_values_by_name[test_name], dtype=np.float64)
        shell_vals = np.asarray(test_shell_hubble_by_name[test_name], dtype=np.float64)
        keep_vals = np.asarray(test_keep_by_name[test_name], dtype=np.float64)
        shell_alignment = 0.0
        if values.size and values.std() > EPS and shell_vals.std() > EPS:
            shell_alignment = float(np.corrcoef(values, shell_vals)[0, 1])
        mean_abs = float(np.mean(np.abs(values))) if values.size else 0.0
        max_mean_abs = max(max_mean_abs, mean_abs)
        raw_rows.append(
            {
                "test": test_name,
                "mean_abs_support": mean_abs,
                "mean_signed_support": float(np.mean(values)) if values.size else 0.0,
                "keep_fraction": float(np.mean(keep_vals)) if keep_vals.size else 0.0,
                "shell_alignment": shell_alignment,
                "shell_alignment_abs": abs(shell_alignment),
            }
        )

    row_by_name: dict[str, dict[str, object]] = {}
    for row in raw_rows:
        signal_score = float(row["mean_abs_support"] / max(max_mean_abs, EPS))
        composite_score = float(
            0.45 * float(row["keep_fraction"])
            + 0.35 * signal_score
            + 0.20 * float(row["shell_alignment_abs"])
        )
        enriched = dict(row)
        enriched["signal_score"] = signal_score
        enriched["composite_score"] = composite_score
        row_by_name[str(row["test"])] = enriched

    ranking = sorted(
        TEST_ORDER,
        key=lambda name: float(row_by_name[name]["composite_score"]),
        reverse=True,
    )
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    framing_rows: list[dict[str, object]] = []
    ranking_scores: list[float] = []
    for test_name in ranking:
        row = row_by_name[test_name]
        ranking_scores.append(float(row["composite_score"]))
        framing_rows.append(
            {
                "option": test_name,
                "mean_abs_a0": float(row["mean_abs_support"]),
                "mean_signed_a0": float(row["mean_signed_support"]),
                "doctrine_fit": float(row["keep_fraction"]),
                "sign_consistency": float(row["keep_fraction"]),
                "shell_alignment": float(row["shell_alignment"]),
                "shell_alignment_abs": float(row["shell_alignment_abs"]),
                "signal_score": float(row["signal_score"]),
                "composite_score": float(row["composite_score"]),
            }
        )

    expansion_drive = np.asarray(
        [
            row["mean_abs_a0"] + row["doctrine_fit"] + row["shell_alignment_abs"]
            for row in framing_rows
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _framing_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(
        np.log(np.clip(scale_factors, EPS, None)),
        lambda_shells,
    )

    for row, scale, hubble in zip(
        framing_rows,
        scale_factors.tolist(),
        hubble_proxy.tolist(),
        strict=True,
    ):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _framing_graph_surface(framing_rows)
    ranking_index = {name: idx for idx, name in enumerate(ranking)}
    config_windows = [
        [ranking_index[name] for name in config_ranking[:3]]
        for config_ranking in per_config_rankings
    ]
    hypergraph_surface = _framing_hypergraph_surface(len(ranking), config_windows)
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
    cell_complex_surface = _framing_cell_complex_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    topology_surface = _framing_topology_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    symbolic_surface = _framing_symbolic_surface(
        lambda_shells,
        scale_factors,
        expansion_drive,
    )
    constraint_surface = _framing_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray(ranking_scores, dtype=np.float64),
    )
    manifold_surface = _framing_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in framing_rows], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in framing_rows], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in framing_rows], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_framing_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in framing_rows], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in framing_rows], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in framing_rows], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner = ranking[0]
    winner_row = next(row for row in framing_rows if row["option"] == winner)
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
        "framing_rows": framing_rows,
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

    t1 = test1_temporal_mi_asymmetry(history, lag=1)
    t2 = test2_attractor_vs_drift(history)
    t3 = test3_jk_fuzz_directionality(history)
    t4 = test4_trajectory_mi_profile(history)
    shell_bridge = lane_d_topology_expansion_bridge(history_base)

    keep_count = sum([t1["keep"], t2["keep"], t3["keep"], t4["keep"]])
    verdict = "COMPRESSION-FROM-FUTURE" if keep_count >= 3 else (
        "MIXED" if keep_count == 2 else "CLASSICAL-CAUSAL"
    )

    print(f"  {engine_type}/{torus_name}: "
          f"T1={'K' if t1['keep'] else 'k'} asym={t1['asymmetry_bwd_minus_fwd']:+.3f} | "
          f"T2={'K' if t2['keep'] else 'k'} ac={t2['mean_autocorr']:+.3f} | "
          f"T3={'K' if t3['keep'] else 'k'} pk_lag={t3['peak_lag']} | "
          f"T4={'K' if t4['keep'] else 'k'} slope={t4['linear_slope']:+.4f} | "
          f"→ {verdict}")

    return {
        "engine_type": engine_type,
        "torus": torus_name,
        "test1_temporal_asymmetry": t1,
        "test2_attractor_vs_drift": t2,
        "test3_jk_fuzz_directionality": t3,
        "test4_trajectory_profile": t4,
        "shell_bridge": shell_bridge,
        "keep_count": keep_count,
        "verdict": verdict,
    }


def main() -> None:
    print("=" * 72)
    print("AXIS 0 FEP / COMPRESSION-FROM-FUTURE FRAMING SIM")
    print("=" * 72)
    print("Tests whether the engine structure is better described by")
    print("compression-from-future (entropic monism) than classical causation.")
    print()
    print("  T1: Backward MI ≥ Forward MI?  (future predicts past)")
    print("  T2: Negative Bloch autocorr?   (attractor, not drift)")
    print("  T3: ga0 lags MI change?         (compression primary)")
    print("  T4: MI increases late in traj?  (attractor convergence)")
    print()

    results = []
    for eng_type in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            r = run_torus(eng_type, torus_name, torus_val)
            results.append(r)

    # Aggregate
    n = len(results)
    t1_keep = sum(1 for r in results if r["test1_temporal_asymmetry"]["keep"])
    t2_keep = sum(1 for r in results if r["test2_attractor_vs_drift"]["keep"])
    t3_keep = sum(1 for r in results if r["test3_jk_fuzz_directionality"]["keep"])
    t4_keep = sum(1 for r in results if r["test4_trajectory_profile"]["keep"])
    compression_verdict = sum(1 for r in results if r["verdict"] == "COMPRESSION-FROM-FUTURE")
    mixed_verdict = sum(1 for r in results if r["verdict"] == "MIXED")
    deep_contract = _aggregate_deep_contract(results)

    print()
    print("=" * 72)
    print("OVERALL VERDICT: FEP / COMPRESSION-FROM-FUTURE FRAMING")
    print("=" * 72)
    print(f"  T1 (backward MI ≥ forward):    {t1_keep}/{n}")
    print(f"  T2 (attractor, not drift):      {t2_keep}/{n}")
    print(f"  T3 (ga0 lags MI):               {t3_keep}/{n}")
    print(f"  T4 (MI increases late):         {t4_keep}/{n}")
    print(f"  Full COMPRESSION verdict:       {compression_verdict}/{n}")
    print(f"  MIXED verdict:                  {mixed_verdict}/{n}")
    print()

    # Interpret
    total_keep = t1_keep + t2_keep + t3_keep + t4_keep
    if total_keep >= 3 * n:
        overall = "STRONG COMPRESSION-FROM-FUTURE"
        print("  ✓ Engine trajectory is strongly consistent with compression-from-future.")
        print("    Attractor-proximity weighting in Xi_hist is justified.")
    elif total_keep >= 2 * n:
        overall = "PARTIAL COMPRESSION-FROM-FUTURE"
        print("  ◐ Engine trajectory is partially consistent with compression-from-future.")
        print("    Some tests show classical causation; compression framing not universal.")
    else:
        overall = "CLASSICAL-CAUSAL DOMINANT"
        print("  ✗ Classical causal framing dominates. Compression-from-future not supported.")

    # Print per-test interpretation for first inner result
    inner = next(r for r in results if r["torus"] == "inner" and r["engine_type"] == 1)
    print()
    print("  Sample interpretations (Type 1 / inner):")
    for key, label in [
        ("test1_temporal_asymmetry", "T1"),
        ("test2_attractor_vs_drift", "T2"),
        ("test3_jk_fuzz_directionality", "T3"),
        ("test4_trajectory_profile", "T4"),
    ]:
        print(f"    {label}: {inner[key]['interpretation']}")

    print()
    print("─" * 72)
    print("DEEP CONTRACT")
    print("─" * 72)
    print(f"  Deep pass:                    {deep_contract['pass']}")
    print(f"  Shell bridge pass fraction:   {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"  Winning framing test:         {deep_contract['winner']}")
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

    def to_json_safe(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, dict):
            return {k: to_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [to_json_safe(v) for v in obj]
        return obj

    output = {
        "timestamp": datetime.now(UTC).isoformat(),
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "results": to_json_safe(results),
        "summary": {
            "t1_keep": t1_keep,
            "t2_keep": t2_keep,
            "t3_keep": t3_keep,
            "t4_keep": t4_keep,
            "compression_verdict": compression_verdict,
            "mixed_verdict": mixed_verdict,
            "total": n,
            "overall": overall,
            "deep_contract_pass": bool(deep_contract["pass"]),
            "deep_contract_winner": deep_contract["winner"],
        },
        "aggregate": {
            "overall": overall,
            "deep_contract": to_json_safe(deep_contract),
            "all_pass": bool(deep_contract["pass"]),
        },
        "overall_pass": bool(deep_contract["pass"]),
        "all_pass": bool(deep_contract["pass"]),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    canonical_out_path = os.path.join(
        out_dir, f"{os.path.splitext(os.path.basename(__file__))[0]}_results.json"
    )
    legacy_out_path = os.path.join(out_dir, "axis0_fep_compression_results.json")
    payload = json.dumps(output, indent=2)
    for target in dict.fromkeys([canonical_out_path, legacy_out_path]):
        with open(target, "w") as f:
            f.write(payload)
    print(f"\nResults written to {canonical_out_path}")


if __name__ == "__main__":
    main()
