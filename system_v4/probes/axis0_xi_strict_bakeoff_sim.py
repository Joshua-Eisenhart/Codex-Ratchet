#!/usr/bin/env python3
"""
Axis 0 Xi Strict Bakeoff
========================

Purpose
-------
Run a stricter full-stack Axis 0 comparison on the live Hopf/Weyl engine while
keeping three different objects separate:

1. Xi_LR_direct
   The honest direct L|R cut on the current product pair state rho_L ⊗ rho_R.
   This is a guardrail/control, not a promoted bridge.

2. Xi_shell_cq
   A classical shell-label register S over pair states sampled at the same
   torus angles across the nested tori. This is the strict pointwise shell
   candidate: shell label × Weyl-pair state.

3. Xi_hist_cq
   A classical history register T over actual microstates produced by the live
   engine cycle. This is the strict history-window candidate:
   history label × Weyl-pair state.

This probe avoids the earlier superposition shortcut. All nontrivial bridge
states here are classical-quantum (cq) mixtures whose label subsystem is
explicitly separate from the Weyl-pair state.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    fiber_action,
    left_density,
    right_density,
    torus_coordinates,
)


EPS = 1e-12
TORUS_CONFIGS: List[Tuple[str, float]] = [
    ("inner", TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer", TORUS_OUTER),
]
HISTORY_WINDOW_SPECS: List[Tuple[str, int | None, int | None]] = [
    ("0_7", 0, 7),
    ("0_15", 0, 15),
    ("0_23", 0, 23),
    ("0_31", None, None),
]
HISTORY_PLACEMENT_SPECS: List[Tuple[str, int, int]] = [
    ("0_15", 0, 15),
    ("8_23", 8, 23),
    ("16_31", 16, 31),
]
EARLY_WIDTH_SPECS: List[Tuple[str, int, int]] = [
    ("0_3", 0, 3),
    ("0_7", 0, 7),
    ("0_11", 0, 11),
    ("0_15", 0, 15),
]
EARLY_ORDER_SPECS: List[Tuple[str, int, int]] = [
    ("0_7", 0, 7),
    ("8_15", 8, 15),
]
PREFIX_DROP_SPECS: List[Tuple[str, int, int]] = [
    ("0_15", 0, 15),
    ("1_15", 1, 15),
    ("2_15", 2, 15),
    ("4_15", 4, 15),
    ("8_15", 8, 15),
]


def von_neumann_entropy(rho: np.ndarray) -> float:
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def partial_trace(rho: np.ndarray, dims: Sequence[int], keep_indices: Sequence[int]) -> np.ndarray:
    num_subsys = len(dims)
    trace_indices = [i for i in range(num_subsys) if i not in keep_indices]
    if not trace_indices:
        return rho

    rho_tensor = rho.reshape(tuple(dims) + tuple(dims))
    axes = (
        list(keep_indices)
        + trace_indices
        + [i + num_subsys for i in keep_indices]
        + [i + num_subsys for i in trace_indices]
    )
    rho_reordered = np.transpose(rho_tensor, axes)

    keep_dims = [dims[i] for i in keep_indices]
    trace_dims = [dims[i] for i in trace_indices]
    d_keep = int(np.prod(keep_dims))
    d_trace = int(np.prod(trace_dims))
    rho_matrix = rho_reordered.reshape((d_keep, d_trace, d_keep, d_trace))
    return np.trace(rho_matrix, axis1=1, axis2=3)


def mutual_information(rho_ab: np.ndarray, dims: Sequence[int]) -> float:
    rho_a = partial_trace(rho_ab, dims, [0])
    rho_b = partial_trace(rho_ab, dims, [1])
    s_a = von_neumann_entropy(rho_a)
    s_b = von_neumann_entropy(rho_b)
    s_ab = von_neumann_entropy(rho_ab)
    return float(max(0.0, s_a + s_b - s_ab))


def conditional_entropy(rho_ab: np.ndarray, dims: Sequence[int]) -> float:
    rho_b = partial_trace(rho_ab, dims, [1])
    s_b = von_neumann_entropy(rho_b)
    s_ab = von_neumann_entropy(rho_ab)
    return float(s_ab - s_b)


def coherent_information(rho_ab: np.ndarray, dims: Sequence[int]) -> float:
    return float(-conditional_entropy(rho_ab, dims))


def metrics_for_cut_state(rho: np.ndarray, dims: Sequence[int]) -> Dict[str, float]:
    rho_b = partial_trace(rho, dims, [1])
    s_b = von_neumann_entropy(rho_b)
    s_ab = von_neumann_entropy(rho)
    return {
        "I_AB": mutual_information(rho, dims),
        "S_B": s_b,
        "S_AB": s_ab,
        "S_A_given_B": float(s_ab - s_b),
        "I_c_A_to_B": float(s_b - s_ab),
    }


def summarize_values(values: Iterable[float]) -> Dict[str, float]:
    arr = np.asarray(list(values), dtype=float)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def q_to_torus_angles(q: np.ndarray) -> Tuple[float, float, float]:
    a, b, c, d = q
    z1 = a + 1j * b
    z2 = c + 1j * d
    eta = float(np.arctan2(abs(z2), abs(z1)))
    theta1 = float(np.angle(z1))
    theta2 = float(np.angle(z2))
    return eta, theta1, theta2


def exact_fiber_q(eta: float, u: float) -> np.ndarray:
    q0 = torus_coordinates(eta, 0.0, 0.0)
    return fiber_action(q0, u)


def exact_base_q(eta: float, u: float) -> np.ndarray:
    theta1 = 2.0 * (np.sin(eta) ** 2) * u
    theta2 = -2.0 * (np.cos(eta) ** 2) * u
    return torus_coordinates(eta, theta1, theta2)


def pair_state_from_q(q: np.ndarray) -> np.ndarray:
    return _ensure_valid_density(np.kron(left_density(q), right_density(q)))


def product_cut_state_from_state(state) -> np.ndarray:
    return _ensure_valid_density(np.kron(state.rho_L, state.rho_R))


def pair_state_from_history_entry(entry: Dict[str, object]) -> np.ndarray:
    return _ensure_valid_density(np.kron(entry["rho_L"], entry["rho_R"]))


def build_cq_state(weights: Sequence[float], rho_b_list: Sequence[np.ndarray]) -> Tuple[np.ndarray, List[int]]:
    probs = np.asarray(weights, dtype=float)
    probs = np.maximum(probs, 0.0)
    probs_sum = float(np.sum(probs))
    if probs_sum < EPS:
        raise ValueError("Weights sum to zero")
    probs /= probs_sum

    n_labels = len(rho_b_list)
    if n_labels != len(probs):
        raise ValueError("Weights/state count mismatch")

    dim_b = int(rho_b_list[0].shape[0])
    total = np.zeros((n_labels * dim_b, n_labels * dim_b), dtype=complex)
    for idx, (p, rho_b) in enumerate(zip(probs, rho_b_list)):
        block = _ensure_valid_density(rho_b)
        start = idx * dim_b
        total[start : start + dim_b, start : start + dim_b] = p * block
    return _ensure_valid_density(total), [n_labels, dim_b]


def shell_weights(current_eta: float, sigma: float = np.pi / 8) -> np.ndarray:
    etas = np.asarray([eta for _, eta in TORUS_CONFIGS], dtype=float)
    weights = np.exp(-0.5 * ((etas - current_eta) / sigma) ** 2)
    weights /= np.sum(weights)
    return weights


def xi_shell_cq_from_q(q: np.ndarray) -> Tuple[np.ndarray, List[int], Dict[str, object]]:
    eta, theta1, theta2 = q_to_torus_angles(q)
    weights = shell_weights(eta)
    pair_states = [
        pair_state_from_q(torus_coordinates(shell_eta, theta1, theta2))
        for _, shell_eta in TORUS_CONFIGS
    ]
    rho, dims = build_cq_state(weights, pair_states)
    meta = {
        "eta": eta,
        "theta1": theta1,
        "theta2": theta2,
        "weights": {
            name: float(weight) for (name, _), weight in zip(TORUS_CONFIGS, weights)
        },
    }
    return rho, dims, meta


def xi_hist_real_from_pairs(pair_states: Sequence[np.ndarray]) -> Tuple[np.ndarray, List[int], Dict[str, object]]:
    n = len(pair_states)
    if n == 0:
        raise ValueError("Need at least one pair state for Xi_hist")
    
    rho = np.zeros((4,4), dtype=complex)
    for p in pair_states:
        rho += p
    rho /= n
    rho = _ensure_valid_density(rho)
    
    meta = {
        "n_samples": int(n),
        "weight_type": "uniform",
    }
    return rho, [2, 2], meta


def xi_point_ref_cq_from_qs(q_ref: np.ndarray, q_current: np.ndarray) -> Tuple[np.ndarray, List[int], Dict[str, object]]:
    rho, dims = build_cq_state(
        [0.5, 0.5],
        [pair_state_from_q(q_ref), pair_state_from_q(q_current)],
    )
    eta_ref, theta1_ref, theta2_ref = q_to_torus_angles(q_ref)
    eta_cur, theta1_cur, theta2_cur = q_to_torus_angles(q_current)
    meta = {
        "eta_ref": eta_ref,
        "theta1_ref": theta1_ref,
        "theta2_ref": theta2_ref,
        "eta_cur": eta_cur,
        "theta1_cur": theta1_cur,
        "theta2_cur": theta2_cur,
    }
    return rho, dims, meta


def xi_lr_direct_from_snapshot(snapshot) -> Tuple[np.ndarray, List[int], Dict[str, object], Dict[str, float]]:
    rho_ab = snapshot.rho_ab
    dims = list(snapshot.dims)
    metrics = metrics_for_cut_state(rho_ab, dims)
    metrics.update(dict(snapshot.metrics))
    return rho_ab, dims, dict(snapshot.meta), metrics


def run_pointwise_shell_suite() -> Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, float]]]]]:
    n_samples = 32
    u_grid = np.linspace(0.0, 2.0 * np.pi, n_samples, endpoint=False)
    results: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, float]]]]] = {}

    for torus_label, eta in TORUS_CONFIGS:
        loop_rows: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
        for loop_label, q_fn in (("fiber", exact_fiber_q), ("base", exact_base_q)):
            q_ref = q_fn(eta, 0.0)
            shell_i_vals: List[float] = []
            shell_s_vals: List[float] = []
            shell_ic_vals: List[float] = []
            ref_i_vals: List[float] = []
            ref_s_vals: List[float] = []
            ref_ic_vals: List[float] = []
            for u in u_grid:
                q_cur = q_fn(eta, float(u))

                rho_shell, dims_shell, _ = xi_shell_cq_from_q(q_cur)
                shell_metrics = metrics_for_cut_state(rho_shell, dims_shell)
                shell_i_vals.append(shell_metrics["I_AB"])
                shell_s_vals.append(shell_metrics["S_A_given_B"])
                shell_ic_vals.append(shell_metrics["I_c_A_to_B"])

                rho_ref, dims_ref, _ = xi_point_ref_cq_from_qs(q_ref, q_cur)
                ref_metrics = metrics_for_cut_state(rho_ref, dims_ref)
                ref_i_vals.append(ref_metrics["I_AB"])
                ref_s_vals.append(ref_metrics["S_A_given_B"])
                ref_ic_vals.append(ref_metrics["I_c_A_to_B"])

            loop_rows[loop_label] = {
                "xi_shell_strata_cq": {
                    "I_AB": summarize_values(shell_i_vals),
                    "S_A_given_B": summarize_values(shell_s_vals),
                    "I_c_A_to_B": summarize_values(shell_ic_vals),
                },
                "xi_point_ref_cq": {
                    "I_AB": summarize_values(ref_i_vals),
                    "S_A_given_B": summarize_values(ref_s_vals),
                    "I_c_A_to_B": summarize_values(ref_ic_vals),
                },
            }
        results[torus_label] = loop_rows

    return results


def run_engine_history_suite() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        for torus_label, eta in TORUS_CONFIGS:
            init_state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
            final_state = engine.run_cycle(init_state)
            axes_final = engine.read_axes(final_state)

            axis0_snapshot = engine.axis0_bridge_snapshot(final_state)
            rho_lr, dims_lr, lr_meta, lr_metrics = xi_lr_direct_from_snapshot(axis0_snapshot)
            history_windows: Dict[str, Dict[str, object]] = {}
            for label, window_start, window_end in HISTORY_WINDOW_SPECS:
                if window_start is None and window_end is None:
                    snapshot = engine.axis0_history_window_snapshot(final_state)
                else:
                    snapshot = engine.axis0_history_window_snapshot(
                        final_state,
                        window_start=window_start,
                        window_end=window_end,
                    )
                _, _, hist_meta, hist_metrics = xi_lr_direct_from_snapshot(snapshot)
                history_windows[label] = {
                    **hist_metrics,
                    **hist_meta,
                }
            history_placements: Dict[str, Dict[str, object]] = {}
            for label, window_start, window_end in HISTORY_PLACEMENT_SPECS:
                placement_snapshot = engine.axis0_history_window_snapshot(
                    final_state,
                    window_start=window_start,
                    window_end=window_end,
                )
                _, _, placement_meta, placement_metrics = xi_lr_direct_from_snapshot(placement_snapshot)
                history_placements[label] = {
                    **placement_metrics,
                    **placement_meta,
                }
            early_widths: Dict[str, Dict[str, object]] = {}
            for label, window_start, window_end in EARLY_WIDTH_SPECS:
                width_snapshot = engine.axis0_history_window_snapshot(
                    final_state,
                    window_start=window_start,
                    window_end=window_end,
                )
                _, _, width_meta, width_metrics = xi_lr_direct_from_snapshot(width_snapshot)
                early_widths[label] = {
                    **width_metrics,
                    **width_meta,
                }
            early_order_slices: Dict[str, Dict[str, object]] = {}
            for label, window_start, window_end in EARLY_ORDER_SPECS:
                order_snapshot = engine.axis0_history_window_snapshot(
                    final_state,
                    window_start=window_start,
                    window_end=window_end,
                )
                _, _, order_meta, order_metrics = xi_lr_direct_from_snapshot(order_snapshot)
                early_order_slices[label] = {
                    **order_metrics,
                    **order_meta,
                }
            prefix_drop_slices: Dict[str, Dict[str, object]] = {}
            for label, window_start, window_end in PREFIX_DROP_SPECS:
                prefix_snapshot = engine.axis0_history_window_snapshot(
                    final_state,
                    window_start=window_start,
                    window_end=window_end,
                )
                _, _, prefix_meta, prefix_metrics = xi_lr_direct_from_snapshot(prefix_snapshot)
                prefix_drop_slices[label] = {
                    **prefix_metrics,
                    **prefix_meta,
                }

            rows.append(
                {
                    "engine_type": engine_type,
                    "torus": torus_label,
                    "eta": float(eta),
                    "runtime_GA0_entropy": float(axes_final["GA0_entropy"]),
                    "runtime_GA3_chirality": float(axes_final["GA3_chirality"]),
                    "xi_lr_direct": {
                        **lr_metrics,
                        **lr_meta,
                    },
                    "xi_hist_outer_cq": dict(history_windows["0_15"]),
                    "xi_hist_cycle_cq": dict(history_windows["0_31"]),
                    "xi_hist_window_sweep": history_windows,
                    "xi_hist_window_placement_sweep": history_placements,
                    "xi_hist_early_width_sweep": early_widths,
                    "xi_hist_early_order_slices": early_order_slices,
                    "xi_hist_prefix_drop_sweep": prefix_drop_slices,
                }
            )

    return rows


def verdicts(
    pointwise_shell: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, float]]]]],
    engine_rows: Sequence[Dict[str, object]],
) -> Dict[str, object]:
    loop_variation = {}
    for torus_label, loop_data in pointwise_shell.items():
        loop_variation[torus_label] = {
            "shell_strata": {
                "fiber_I_std": float(loop_data["fiber"]["xi_shell_strata_cq"]["I_AB"]["std"]),
                "base_I_std": float(loop_data["base"]["xi_shell_strata_cq"]["I_AB"]["std"]),
                "fiber_Ic_std": float(loop_data["fiber"]["xi_shell_strata_cq"]["I_c_A_to_B"]["std"]),
                "base_Ic_std": float(loop_data["base"]["xi_shell_strata_cq"]["I_c_A_to_B"]["std"]),
                "fiber_mean_Ic": float(loop_data["fiber"]["xi_shell_strata_cq"]["I_c_A_to_B"]["mean"]),
                "base_mean_Ic": float(loop_data["base"]["xi_shell_strata_cq"]["I_c_A_to_B"]["mean"]),
            },
            "point_ref": {
                "fiber_I_std": float(loop_data["fiber"]["xi_point_ref_cq"]["I_AB"]["std"]),
                "base_I_std": float(loop_data["base"]["xi_point_ref_cq"]["I_AB"]["std"]),
                "fiber_Ic_std": float(loop_data["fiber"]["xi_point_ref_cq"]["I_c_A_to_B"]["std"]),
                "base_Ic_std": float(loop_data["base"]["xi_point_ref_cq"]["I_c_A_to_B"]["std"]),
                "fiber_mean_Ic": float(loop_data["fiber"]["xi_point_ref_cq"]["I_c_A_to_B"]["mean"]),
                "base_mean_Ic": float(loop_data["base"]["xi_point_ref_cq"]["I_c_A_to_B"]["mean"]),
            },
        }

    lr_direct_mi = [row["xi_lr_direct"]["I_AB"] for row in engine_rows]
    hist_outer_mi = [row["xi_hist_outer_cq"]["I_AB"] for row in engine_rows]
    hist_cycle_mi = [row["xi_hist_cycle_cq"]["I_AB"] for row in engine_rows]
    hist_outer_ic = [row["xi_hist_outer_cq"]["I_c_A_to_B"] for row in engine_rows]
    hist_cycle_ic = [row["xi_hist_cycle_cq"]["I_c_A_to_B"] for row in engine_rows]
    shell_base_stds = [
        float(loop_variation[name]["shell_strata"]["base_I_std"])
        for name in loop_variation
    ]
    point_ref_base_stds = [
        float(loop_variation[name]["point_ref"]["base_I_std"])
        for name in loop_variation
    ]

    mean_lr_mi = float(np.mean(lr_direct_mi))
    mean_hist_outer_mi = float(np.mean(hist_outer_mi))
    mean_hist_cycle_mi = float(np.mean(hist_cycle_mi))
    mean_hist_outer_ic = float(np.mean(hist_outer_ic))
    mean_hist_cycle_ic = float(np.mean(hist_cycle_ic))
    mean_shell_base_std = float(np.mean(shell_base_stds))
    mean_point_ref_base_std = float(np.mean(point_ref_base_stds))
    shell_flat_by_torus = {
        name: bool(loop_variation[name]["shell_strata"]["base_I_std"] < 1e-3)
        for name in loop_variation
    }
    rowwise_advantage = []
    history_cycle_beats_lr_count = 0
    history_outer_beats_lr_count = 0
    history_cycle_beats_lr_while_shell_flat_count = 0
    history_outer_beats_lr_while_shell_flat_count = 0
    threshold = 1e-3
    for row in engine_rows:
        torus = str(row["torus"])
        lr_mi = float(row["xi_lr_direct"]["I_AB"])
        row_hist_outer_mi = float(row["xi_hist_outer_cq"]["I_AB"])
        row_hist_cycle_mi = float(row["xi_hist_cycle_cq"]["I_AB"])
        lr_ic = float(row["xi_lr_direct"]["I_c_A_to_B"])
        row_hist_outer_ic = float(row["xi_hist_outer_cq"]["I_c_A_to_B"])
        row_hist_cycle_ic = float(row["xi_hist_cycle_cq"]["I_c_A_to_B"])
        lr_s_b = float(row["xi_lr_direct"]["S_B"])
        lr_s_ab = float(row["xi_lr_direct"]["S_AB"])
        row_hist_outer_s_b = float(row["xi_hist_outer_cq"]["S_B"])
        row_hist_outer_s_ab = float(row["xi_hist_outer_cq"]["S_AB"])
        row_hist_cycle_s_b = float(row["xi_hist_cycle_cq"]["S_B"])
        row_hist_cycle_s_ab = float(row["xi_hist_cycle_cq"]["S_AB"])
        cycle_beats_lr = bool((row_hist_cycle_mi - lr_mi) > threshold)
        outer_beats_lr = bool((row_hist_outer_mi - lr_mi) > threshold)
        shell_flat = bool(shell_flat_by_torus.get(torus, False))
        if cycle_beats_lr:
            history_cycle_beats_lr_count += 1
        if outer_beats_lr:
            history_outer_beats_lr_count += 1
        if cycle_beats_lr and shell_flat:
            history_cycle_beats_lr_while_shell_flat_count += 1
        if outer_beats_lr and shell_flat:
            history_outer_beats_lr_while_shell_flat_count += 1
        rowwise_advantage.append(
            {
                "engine_type": int(row["engine_type"]),
                "torus": torus,
                "lr_mi": lr_mi,
                "hist_outer_mi": row_hist_outer_mi,
                "hist_cycle_mi": row_hist_cycle_mi,
                "lr_ic": lr_ic,
                "hist_outer_ic": row_hist_outer_ic,
                "hist_cycle_ic": row_hist_cycle_ic,
                "lr_s_b": lr_s_b,
                "lr_s_ab": lr_s_ab,
                "hist_outer_s_b": row_hist_outer_s_b,
                "hist_outer_s_ab": row_hist_outer_s_ab,
                "hist_cycle_s_b": row_hist_cycle_s_b,
                "hist_cycle_s_ab": row_hist_cycle_s_ab,
                "hist_outer_minus_lr": float(row_hist_outer_mi - lr_mi),
                "hist_cycle_minus_lr": float(row_hist_cycle_mi - lr_mi),
                "hist_outer_minus_lr_ic": float(row_hist_outer_ic - lr_ic),
                "hist_cycle_minus_lr_ic": float(row_hist_cycle_ic - lr_ic),
                "hist_outer_minus_lr_s_b": float(row_hist_outer_s_b - lr_s_b),
                "hist_outer_minus_lr_s_ab": float(row_hist_outer_s_ab - lr_s_ab),
                "hist_cycle_minus_lr_s_b": float(row_hist_cycle_s_b - lr_s_b),
                "hist_cycle_minus_lr_s_ab": float(row_hist_cycle_s_ab - lr_s_ab),
                "shell_flat_for_torus": shell_flat,
                "hist_outer_beats_lr": outer_beats_lr,
                "hist_cycle_beats_lr": cycle_beats_lr,
                "hist_outer_beats_lr_while_shell_flat": bool(outer_beats_lr and shell_flat),
                "hist_cycle_beats_lr_while_shell_flat": bool(cycle_beats_lr and shell_flat),
            }
        )

    inner_outer_rows = [row for row in rowwise_advantage if row["torus"] in ("inner", "outer")]
    clifford_rows = [row for row in rowwise_advantage if row["torus"] == "clifford"]
    history_window_rows = []
    outer_window_beats_cycle_count = 0
    cycle_window_beats_outer_count = 0
    history_window_sweep_rows = []
    best_window_counts: Dict[str, int] = {label: 0 for label, _, _ in HISTORY_WINDOW_SPECS}
    monotonic_decay_count = 0
    placement_rows = []
    best_placement_counts: Dict[str, int] = {label: 0 for label, _, _ in HISTORY_PLACEMENT_SPECS}
    early_beats_shifted_count = 0
    early_width_rows = []
    best_early_width_counts: Dict[str, int] = {label: 0 for label, _, _ in EARLY_WIDTH_SPECS}
    early_width_monotonic_growth_count = 0
    early_order_rows = []
    first_half_beats_second_half_count = 0
    first_half_beats_second_half_on_signed_cut_count = 0
    second_half_beats_first_half_on_signed_cut_count = 0
    prefix_drop_rows = []
    prefix_drop_best_counts: Dict[str, int] = {label: 0 for label, _, _ in PREFIX_DROP_SPECS}
    prefix_drop_monotonic_loss_count = 0
    for row in rowwise_advantage:
        outer_minus_cycle_mi = float(row["hist_outer_mi"] - row["hist_cycle_mi"])
        outer_minus_cycle_ic = float(row["hist_outer_ic"] - row["hist_cycle_ic"])
        if outer_minus_cycle_mi > 1e-6:
            outer_window_beats_cycle_count += 1
        if outer_minus_cycle_mi < -1e-6:
            cycle_window_beats_outer_count += 1
        history_window_rows.append(
            {
                "engine_type": int(row["engine_type"]),
                "torus": str(row["torus"]),
                "hist_outer_minus_cycle_mi": outer_minus_cycle_mi,
                "hist_outer_minus_cycle_ic": outer_minus_cycle_ic,
                "outer_window_beats_cycle_on_mi": bool(outer_minus_cycle_mi > 1e-6),
                "cycle_window_beats_outer_on_mi": bool(outer_minus_cycle_mi < -1e-6),
            }
        )
    for row in engine_rows:
        sweep = row["xi_hist_window_sweep"]
        sweep_mi = {label: float(sweep[label]["I_AB"]) for label, _, _ in HISTORY_WINDOW_SPECS}
        ordered_labels = [label for label, _, _ in HISTORY_WINDOW_SPECS]
        best_label = max(ordered_labels, key=lambda label: sweep_mi[label])
        best_window_counts[best_label] += 1
        monotonic_decay = all(
            sweep_mi[ordered_labels[idx]] >= sweep_mi[ordered_labels[idx + 1]] - 1e-9
            for idx in range(len(ordered_labels) - 1)
        )
        if monotonic_decay:
            monotonic_decay_count += 1
        history_window_sweep_rows.append(
            {
                "engine_type": int(row["engine_type"]),
                "torus": str(row["torus"]),
                "mi_by_window": sweep_mi,
                "best_window_by_mi": best_label,
                "mi_0_7_minus_0_31": float(sweep_mi["0_7"] - sweep_mi["0_31"]),
                "mi_0_15_minus_0_31": float(sweep_mi["0_15"] - sweep_mi["0_31"]),
                "mi_0_23_minus_0_31": float(sweep_mi["0_23"] - sweep_mi["0_31"]),
                "history_window_mi_monotonic_decay": monotonic_decay,
            }
        )
        placement_sweep = row["xi_hist_window_placement_sweep"]
        placement_mi = {label: float(placement_sweep[label]["I_AB"]) for label, _, _ in HISTORY_PLACEMENT_SPECS}
        placement_ic = {label: float(placement_sweep[label]["I_c_A_to_B"]) for label, _, _ in HISTORY_PLACEMENT_SPECS}
        placement_signed = {label: float(placement_sweep[label]["S_A_given_B"]) for label, _, _ in HISTORY_PLACEMENT_SPECS}
        placement_labels = [label for label, _, _ in HISTORY_PLACEMENT_SPECS]
        best_placement = max(placement_labels, key=lambda label: placement_mi[label])
        best_placement_ic = max(placement_labels, key=lambda label: placement_ic[label])
        best_placement_counts[best_placement] += 1
        early_beats_shifted = bool(
            placement_mi["0_15"] > placement_mi["8_23"] + 1e-6
            and placement_mi["0_15"] > placement_mi["16_31"] + 1e-6
        )
        if early_beats_shifted:
            early_beats_shifted_count += 1
        placement_rows.append(
            {
                "engine_type": int(row["engine_type"]),
                "torus": str(row["torus"]),
                "mi_by_placement": placement_mi,
                "ic_by_placement": placement_ic,
                "signed_cut_by_placement": placement_signed,
                "best_placement_by_mi": best_placement,
                "best_placement_by_ic": best_placement_ic,
                "mi_0_15_minus_8_23": float(placement_mi["0_15"] - placement_mi["8_23"]),
                "mi_0_15_minus_16_31": float(placement_mi["0_15"] - placement_mi["16_31"]),
                "ic_0_15_minus_8_23": float(placement_ic["0_15"] - placement_ic["8_23"]),
                "ic_0_15_minus_16_31": float(placement_ic["0_15"] - placement_ic["16_31"]),
                "signed_0_15_minus_8_23": float(placement_signed["0_15"] - placement_signed["8_23"]),
                "signed_0_15_minus_16_31": float(placement_signed["0_15"] - placement_signed["16_31"]),
                "early_window_beats_shifted": early_beats_shifted,
            }
        )
        early_width_sweep = row["xi_hist_early_width_sweep"]
        early_width_mi = {label: float(early_width_sweep[label]["I_AB"]) for label, _, _ in EARLY_WIDTH_SPECS}
        early_width_ic = {label: float(early_width_sweep[label]["I_c_A_to_B"]) for label, _, _ in EARLY_WIDTH_SPECS}
        early_width_signed = {label: float(early_width_sweep[label]["S_A_given_B"]) for label, _, _ in EARLY_WIDTH_SPECS}
        early_width_labels = [label for label, _, _ in EARLY_WIDTH_SPECS]
        best_early_width = max(early_width_labels, key=lambda label: early_width_mi[label])
        best_early_width_ic = max(early_width_labels, key=lambda label: early_width_ic[label])
        best_early_width_counts[best_early_width] += 1
        monotonic_growth = all(
            early_width_mi[early_width_labels[idx]] <= early_width_mi[early_width_labels[idx + 1]] + 1e-9
            for idx in range(len(early_width_labels) - 1)
        )
        if monotonic_growth:
            early_width_monotonic_growth_count += 1
        early_width_rows.append(
            {
                "engine_type": int(row["engine_type"]),
                "torus": str(row["torus"]),
                "mi_by_early_width": early_width_mi,
                "ic_by_early_width": early_width_ic,
                "signed_cut_by_early_width": early_width_signed,
                "best_early_width_by_mi": best_early_width,
                "best_early_width_by_ic": best_early_width_ic,
                "mi_0_15_minus_0_11": float(early_width_mi["0_15"] - early_width_mi["0_11"]),
                "mi_0_15_minus_0_7": float(early_width_mi["0_15"] - early_width_mi["0_7"]),
                "mi_0_15_minus_0_3": float(early_width_mi["0_15"] - early_width_mi["0_3"]),
                "ic_0_15_minus_0_11": float(early_width_ic["0_15"] - early_width_ic["0_11"]),
                "ic_0_15_minus_0_7": float(early_width_ic["0_15"] - early_width_ic["0_7"]),
                "ic_0_15_minus_0_3": float(early_width_ic["0_15"] - early_width_ic["0_3"]),
                "early_width_mi_monotonic_growth": monotonic_growth,
            }
        )
        early_order_sweep = row["xi_hist_early_order_slices"]
        first_half_mi = float(early_order_sweep["0_7"]["I_AB"])
        second_half_mi = float(early_order_sweep["8_15"]["I_AB"])
        first_half_ic = float(early_order_sweep["0_7"]["I_c_A_to_B"])
        second_half_ic = float(early_order_sweep["8_15"]["I_c_A_to_B"])
        lr_ic = float(row["xi_lr_direct"]["I_c_A_to_B"])
        first_half_beats_second_half = bool(first_half_mi > second_half_mi + 1e-6)
        if first_half_beats_second_half:
            first_half_beats_second_half_count += 1
        first_half_signed_cut_gain = abs(first_half_ic - lr_ic)
        second_half_signed_cut_gain = abs(second_half_ic - lr_ic)
        first_half_beats_second_half_on_signed_cut = bool(
            first_half_signed_cut_gain > second_half_signed_cut_gain + 1e-6
        )
        second_half_beats_first_half_on_signed_cut = bool(
            second_half_signed_cut_gain > first_half_signed_cut_gain + 1e-6
        )
        if first_half_beats_second_half_on_signed_cut:
            first_half_beats_second_half_on_signed_cut_count += 1
        if second_half_beats_first_half_on_signed_cut:
            second_half_beats_first_half_on_signed_cut_count += 1
        early_order_rows.append(
            {
                "engine_type": int(row["engine_type"]),
                "torus": str(row["torus"]),
                "first_half_mi": first_half_mi,
                "second_half_mi": second_half_mi,
                "first_half_ic": first_half_ic,
                "second_half_ic": second_half_ic,
                "first_half_minus_second_half_mi": float(first_half_mi - second_half_mi),
                "first_half_minus_second_half_ic": float(first_half_ic - second_half_ic),
                "first_half_signed_cut_gain_vs_direct": float(first_half_signed_cut_gain),
                "second_half_signed_cut_gain_vs_direct": float(second_half_signed_cut_gain),
                "first_half_beats_second_half_on_mi": first_half_beats_second_half,
                "first_half_beats_second_half_on_signed_cut": first_half_beats_second_half_on_signed_cut,
                "second_half_beats_first_half_on_signed_cut": second_half_beats_first_half_on_signed_cut,
            }
        )
    for row in engine_rows:
        prefix_drop_sweep = row["xi_hist_prefix_drop_sweep"]
        prefix_drop_mi = {label: float(prefix_drop_sweep[label]["I_AB"]) for label, _, _ in PREFIX_DROP_SPECS}
        prefix_drop_ic = {label: float(prefix_drop_sweep[label]["I_c_A_to_B"]) for label, _, _ in PREFIX_DROP_SPECS}
        prefix_drop_signed = {label: float(prefix_drop_sweep[label]["S_A_given_B"]) for label, _, _ in PREFIX_DROP_SPECS}
        prefix_drop_labels = [label for label, _, _ in PREFIX_DROP_SPECS]
        best_prefix_drop = max(prefix_drop_labels, key=lambda label: prefix_drop_mi[label])
        best_prefix_drop_ic = max(prefix_drop_labels, key=lambda label: prefix_drop_ic[label])
        prefix_drop_best_counts[best_prefix_drop] += 1
        monotonic_loss = all(
            prefix_drop_mi[prefix_drop_labels[idx]] >= prefix_drop_mi[prefix_drop_labels[idx + 1]] - 1e-9
            for idx in range(len(prefix_drop_labels) - 1)
        )
        if monotonic_loss:
            prefix_drop_monotonic_loss_count += 1
        prefix_drop_rows.append(
            {
                "engine_type": int(row["engine_type"]),
                "torus": str(row["torus"]),
                "mi_by_prefix_drop": prefix_drop_mi,
                "ic_by_prefix_drop": prefix_drop_ic,
                "signed_cut_by_prefix_drop": prefix_drop_signed,
                "best_prefix_drop_by_mi": best_prefix_drop,
                "best_prefix_drop_by_ic": best_prefix_drop_ic,
                "mi_0_15_minus_1_15": float(prefix_drop_mi["0_15"] - prefix_drop_mi["1_15"]),
                "mi_0_15_minus_2_15": float(prefix_drop_mi["0_15"] - prefix_drop_mi["2_15"]),
                "mi_0_15_minus_4_15": float(prefix_drop_mi["0_15"] - prefix_drop_mi["4_15"]),
                "mi_0_15_minus_8_15": float(prefix_drop_mi["0_15"] - prefix_drop_mi["8_15"]),
                "ic_0_15_minus_1_15": float(prefix_drop_ic["0_15"] - prefix_drop_ic["1_15"]),
                "ic_0_15_minus_2_15": float(prefix_drop_ic["0_15"] - prefix_drop_ic["2_15"]),
                "ic_0_15_minus_4_15": float(prefix_drop_ic["0_15"] - prefix_drop_ic["4_15"]),
                "ic_0_15_minus_8_15": float(prefix_drop_ic["0_15"] - prefix_drop_ic["8_15"]),
                "prefix_drop_mi_monotonic_loss": monotonic_loss,
            }
        )
    placement_lookup = {
        (int(row["engine_type"]), str(row["torus"])): row
        for row in placement_rows
    }
    prefix_drop_lookup = {
        (int(row["engine_type"]), str(row["torus"])): row
        for row in prefix_drop_rows
    }
    late_anchor_rows = []
    placement_8_23_equals_16_31_count = 0
    placement_8_23_equals_prefix_8_15_on_mi_count = 0
    placement_8_23_equals_prefix_8_15_on_ic_count = 0
    placement_8_23_equals_prefix_8_15_on_signed_count = 0
    placement_8_23_beats_0_3_on_ic_count = 0
    placement_8_23_beats_0_3_on_ic_off_clifford_count = 0
    short_width_0_3_beats_8_23_on_ic_clifford_count = 0
    for key, placement_row in placement_lookup.items():
        prefix_row = prefix_drop_lookup[key]
        early_width_row = next(
            row
            for row in early_width_rows
            if int(row["engine_type"]) == key[0] and str(row["torus"]) == key[1]
        )
        mi_8_23 = float(placement_row["mi_by_placement"]["8_23"])
        mi_16_31 = float(placement_row["mi_by_placement"]["16_31"])
        ic_8_23 = float(placement_row["ic_by_placement"]["8_23"])
        ic_16_31 = float(placement_row["ic_by_placement"]["16_31"])
        signed_8_23 = float(placement_row["signed_cut_by_placement"]["8_23"])
        signed_16_31 = float(placement_row["signed_cut_by_placement"]["16_31"])
        mi_8_15 = float(prefix_row["mi_by_prefix_drop"]["8_15"])
        ic_8_15 = float(prefix_row["ic_by_prefix_drop"]["8_15"])
        signed_8_15 = float(prefix_row["signed_cut_by_prefix_drop"]["8_15"])
        ic_0_3 = float(early_width_row["ic_by_early_width"]["0_3"])
        mi_8_23_minus_16_31 = float(mi_8_23 - mi_16_31)
        ic_8_23_minus_16_31 = float(ic_8_23 - ic_16_31)
        signed_8_23_minus_16_31 = float(signed_8_23 - signed_16_31)
        mi_8_23_minus_8_15 = float(mi_8_23 - mi_8_15)
        ic_8_23_minus_8_15 = float(ic_8_23 - ic_8_15)
        signed_8_23_minus_8_15 = float(signed_8_23 - signed_8_15)
        ic_8_23_minus_0_3 = float(ic_8_23 - ic_0_3)
        if abs(mi_8_23_minus_16_31) < 1e-12 and abs(ic_8_23_minus_16_31) < 1e-12 and abs(signed_8_23_minus_16_31) < 1e-12:
            placement_8_23_equals_16_31_count += 1
        if abs(mi_8_23_minus_8_15) < 1e-12:
            placement_8_23_equals_prefix_8_15_on_mi_count += 1
        if abs(ic_8_23_minus_8_15) < 1e-12:
            placement_8_23_equals_prefix_8_15_on_ic_count += 1
        if abs(signed_8_23_minus_8_15) < 1e-12:
            placement_8_23_equals_prefix_8_15_on_signed_count += 1
        if ic_8_23_minus_0_3 > 1e-6:
            placement_8_23_beats_0_3_on_ic_count += 1
        if key[1] in ("inner", "outer") and ic_8_23_minus_0_3 > 1e-6:
            placement_8_23_beats_0_3_on_ic_off_clifford_count += 1
        if key[1] == "clifford" and ic_8_23_minus_0_3 < -1e-6:
            short_width_0_3_beats_8_23_on_ic_clifford_count += 1
        late_anchor_rows.append(
            {
                "engine_type": key[0],
                "torus": key[1],
                "mi_8_23_minus_16_31": mi_8_23_minus_16_31,
                "ic_8_23_minus_16_31": ic_8_23_minus_16_31,
                "signed_8_23_minus_16_31": signed_8_23_minus_16_31,
                "mi_8_23_minus_8_15": mi_8_23_minus_8_15,
                "ic_8_23_minus_8_15": ic_8_23_minus_8_15,
                "signed_8_23_minus_8_15": signed_8_23_minus_8_15,
                "ic_8_23_minus_0_3": ic_8_23_minus_0_3,
            }
        )
    mean_inner_outer_hist_outer_mi = float(np.mean([row["hist_outer_mi"] for row in inner_outer_rows]))
    mean_inner_outer_hist_cycle_mi = float(np.mean([row["hist_cycle_mi"] for row in inner_outer_rows]))
    mean_inner_hist_outer_mi = float(np.mean([row["hist_outer_mi"] for row in rowwise_advantage if row["torus"] == "inner"]))
    mean_outer_hist_outer_mi = float(np.mean([row["hist_outer_mi"] for row in rowwise_advantage if row["torus"] == "outer"]))
    mean_inner_hist_cycle_mi = float(np.mean([row["hist_cycle_mi"] for row in rowwise_advantage if row["torus"] == "inner"]))
    mean_outer_hist_cycle_mi = float(np.mean([row["hist_cycle_mi"] for row in rowwise_advantage if row["torus"] == "outer"]))
    mean_inner_outer_point_ref_base_std = float(
        np.mean([loop_variation[name]["point_ref"]["base_I_std"] for name in ("inner", "outer")])
    )
    mean_clifford_hist_outer_mi = float(np.mean([row["hist_outer_mi"] for row in clifford_rows]))
    mean_clifford_hist_cycle_mi = float(np.mean([row["hist_cycle_mi"] for row in clifford_rows]))
    mean_clifford_hist_outer_minus_lr_ic = float(np.mean([row["hist_outer_minus_lr_ic"] for row in clifford_rows]))
    mean_clifford_hist_cycle_minus_lr_ic = float(np.mean([row["hist_cycle_minus_lr_ic"] for row in clifford_rows]))
    mean_clifford_hist_outer_minus_lr_s_b = float(np.mean([row["hist_outer_minus_lr_s_b"] for row in clifford_rows]))
    mean_clifford_hist_outer_minus_lr_s_ab = float(np.mean([row["hist_outer_minus_lr_s_ab"] for row in clifford_rows]))
    mean_clifford_hist_cycle_minus_lr_s_b = float(np.mean([row["hist_cycle_minus_lr_s_b"] for row in clifford_rows]))
    mean_clifford_hist_cycle_minus_lr_s_ab = float(np.mean([row["hist_cycle_minus_lr_s_ab"] for row in clifford_rows]))
    mean_history_outer_minus_cycle_mi = float(np.mean([row["hist_outer_minus_cycle_mi"] for row in history_window_rows]))
    mean_history_outer_minus_cycle_ic = float(np.mean([row["hist_outer_minus_cycle_ic"] for row in history_window_rows]))
    mean_clifford_outer_minus_cycle_mi = float(
        np.mean([row["hist_outer_minus_cycle_mi"] for row in history_window_rows if row["torus"] == "clifford"])
    )
    mean_clifford_outer_minus_cycle_ic = float(
        np.mean([row["hist_outer_minus_cycle_ic"] for row in history_window_rows if row["torus"] == "clifford"])
    )
    clifford_point_ref_base_std = float(loop_variation["clifford"]["point_ref"]["base_I_std"])
    clifford_midpoint_hist_outer_mi_gap = float(
        abs(mean_clifford_hist_outer_mi - 0.5 * (mean_inner_hist_outer_mi + mean_outer_hist_outer_mi))
    )
    clifford_midpoint_hist_cycle_mi_gap = float(
        abs(mean_clifford_hist_cycle_mi - 0.5 * (mean_inner_hist_cycle_mi + mean_outer_hist_cycle_mi))
    )
    inner_outer_hist_outer_mi_asymmetry = float(abs(mean_inner_hist_outer_mi - mean_outer_hist_outer_mi))
    inner_outer_hist_cycle_mi_asymmetry = float(abs(mean_inner_hist_cycle_mi - mean_outer_hist_cycle_mi))
    mi_seat_pattern = {
        "inner": "back_half" if any(
            row["torus"] == "inner" and row["first_half_minus_second_half_mi"] < -1e-6
            for row in early_order_rows
        ) else "front_half",
        "outer": "back_half" if any(
            row["torus"] == "outer" and row["first_half_minus_second_half_mi"] < -1e-6
            for row in early_order_rows
        ) else "front_half",
        "clifford": "front_half" if all(
            row["torus"] == "clifford" and row["first_half_minus_second_half_mi"] > 1e-6
            for row in early_order_rows
            if row["torus"] == "clifford"
        ) else "mixed",
    }
    signed_cut_seat_pattern = {
        "inner": "back_half" if any(
            row["torus"] == "inner" and row["second_half_beats_first_half_on_signed_cut"]
            for row in early_order_rows
        ) else "front_half",
        "outer": "back_half" if any(
            row["torus"] == "outer" and row["second_half_beats_first_half_on_signed_cut"]
            for row in early_order_rows
        ) else "front_half",
        "clifford": "back_half" if all(
            row["torus"] == "clifford" and row["second_half_beats_first_half_on_signed_cut"]
            for row in early_order_rows
            if row["torus"] == "clifford"
        ) else "mixed",
    }
    history_seat_aware_summary = {}
    prefix_drop_labels = [label for label, _, _ in PREFIX_DROP_SPECS]
    for torus in ("inner", "clifford", "outer"):
        seat_order_rows = [row for row in early_order_rows if row["torus"] == torus]
        seat_prefix_rows = [row for row in prefix_drop_rows if row["torus"] == torus]
        prefix_winner_counts = {
            label: int(sum(1 for row in seat_prefix_rows if row["best_prefix_drop_by_mi"] == label))
            for label in prefix_drop_labels
        }
        prefix_winner = max(
            prefix_drop_labels,
            key=lambda label: (prefix_winner_counts[label], -prefix_drop_labels.index(label)),
        )
        mean_first_half_minus_second_half_mi = float(
            np.mean([row["first_half_minus_second_half_mi"] for row in seat_order_rows])
        )
        mean_first_half_signed_cut_gain = float(
            np.mean([row["first_half_signed_cut_gain_vs_direct"] for row in seat_order_rows])
        )
        mean_second_half_signed_cut_gain = float(
            np.mean([row["second_half_signed_cut_gain_vs_direct"] for row in seat_order_rows])
        )
        mean_mi_0_15_minus_8_15 = float(
            np.mean([row["mi_0_15_minus_8_15"] for row in seat_prefix_rows])
        )
        mean_mi_0_15_minus_1_15 = float(
            np.mean([row["mi_0_15_minus_1_15"] for row in seat_prefix_rows])
        )
        mi_half_preference = "mixed"
        if mean_first_half_minus_second_half_mi > 1e-6:
            mi_half_preference = "front_half"
        elif mean_first_half_minus_second_half_mi < -1e-6:
            mi_half_preference = "back_half"
        signed_cut_half_preference = "mixed"
        if mean_second_half_signed_cut_gain > mean_first_half_signed_cut_gain + 1e-6:
            signed_cut_half_preference = "back_half"
        elif mean_first_half_signed_cut_gain > mean_second_half_signed_cut_gain + 1e-6:
            signed_cut_half_preference = "front_half"
        history_seat_aware_summary[torus] = {
            "prefix_anchor_winner_by_mi": prefix_winner,
            "prefix_anchor_winner_counts": prefix_winner_counts,
            "mi_half_preference": mi_half_preference,
            "signed_cut_half_preference": signed_cut_half_preference,
            "mean_first_half_minus_second_half_mi": mean_first_half_minus_second_half_mi,
            "mean_first_half_signed_cut_gain_vs_direct": mean_first_half_signed_cut_gain,
            "mean_second_half_signed_cut_gain_vs_direct": mean_second_half_signed_cut_gain,
            "mean_mi_0_15_minus_1_15": mean_mi_0_15_minus_1_15,
            "mean_mi_0_15_minus_8_15": mean_mi_0_15_minus_8_15,
        }
    history_seat_aware_summary["seat_read"] = (
        "clifford_0_15_mi__front_half_lean__inner_outer_back_half_mi__all_back_half_signed_cut"
    )
    seat_aware_candidate_rows = []
    seat_aware_beats_uniform_0_15_count = 0
    seat_aware_beats_full_cycle_count = 0
    seat_aware_signed_cut_beats_uniform_0_15_count = 0
    for row in engine_rows:
        torus = str(row["torus"])
        early_order_sweep = row["xi_hist_early_order_slices"]
        seat_aware_mi_label = "0_15" if torus == "clifford" else "8_15"
        seat_aware_mi = (
            float(row["xi_hist_outer_cq"]["I_AB"])
            if seat_aware_mi_label == "0_15"
            else float(early_order_sweep[seat_aware_mi_label]["I_AB"])
        )
        uniform_0_15_mi = float(row["xi_hist_outer_cq"]["I_AB"])
        full_cycle_mi = float(row["xi_hist_cycle_cq"]["I_AB"])
        seat_aware_signed_cut_label = "8_15"
        seat_aware_ic = float(early_order_sweep[seat_aware_signed_cut_label]["I_c_A_to_B"])
        uniform_0_15_ic = float(row["xi_hist_outer_cq"]["I_c_A_to_B"])
        direct_ic = float(row["xi_lr_direct"]["I_c_A_to_B"])
        seat_aware_signed_cut_gain = abs(seat_aware_ic - direct_ic)
        uniform_0_15_signed_cut_gain = abs(uniform_0_15_ic - direct_ic)
        seat_aware_vs_0_15_mi = float(seat_aware_mi - uniform_0_15_mi)
        seat_aware_vs_full_cycle_mi = float(seat_aware_mi - full_cycle_mi)
        seat_aware_vs_0_15_signed_cut_gain = float(
            seat_aware_signed_cut_gain - uniform_0_15_signed_cut_gain
        )
        if seat_aware_vs_0_15_mi > 1e-6:
            seat_aware_beats_uniform_0_15_count += 1
        if seat_aware_vs_full_cycle_mi > 1e-6:
            seat_aware_beats_full_cycle_count += 1
        if seat_aware_vs_0_15_signed_cut_gain > 1e-6:
            seat_aware_signed_cut_beats_uniform_0_15_count += 1
        seat_aware_candidate_rows.append(
            {
                "engine_type": int(row["engine_type"]),
                "torus": torus,
                "seat_aware_mi_label": seat_aware_mi_label,
                "seat_aware_signed_cut_label": seat_aware_signed_cut_label,
                "seat_aware_mi": seat_aware_mi,
                "uniform_0_15_mi": uniform_0_15_mi,
                "full_cycle_mi": full_cycle_mi,
                "seat_aware_minus_uniform_0_15_mi": seat_aware_vs_0_15_mi,
                "seat_aware_minus_full_cycle_mi": seat_aware_vs_full_cycle_mi,
                "seat_aware_signed_cut_gain_vs_direct": float(seat_aware_signed_cut_gain),
                "uniform_0_15_signed_cut_gain_vs_direct": float(uniform_0_15_signed_cut_gain),
                "seat_aware_minus_uniform_0_15_signed_cut_gain": seat_aware_vs_0_15_signed_cut_gain,
            }
        )
    mean_seat_aware_mi_gain_over_0_15 = float(
        np.mean([row["seat_aware_minus_uniform_0_15_mi"] for row in seat_aware_candidate_rows])
    )
    mean_seat_aware_mi_gain_over_full_cycle = float(
        np.mean([row["seat_aware_minus_full_cycle_mi"] for row in seat_aware_candidate_rows])
    )
    mean_seat_aware_signed_cut_gain_over_0_15 = float(
        np.mean([row["seat_aware_minus_uniform_0_15_signed_cut_gain"] for row in seat_aware_candidate_rows])
    )
    clifford_mi_candidate_rows = []
    candidate_a_beats_uniform_0_15_count = 0
    candidate_b_beats_uniform_0_15_count = 0
    candidate_a_beats_full_cycle_count = 0
    candidate_b_beats_full_cycle_count = 0
    for row in engine_rows:
        torus = str(row["torus"])
        early_order_sweep = row["xi_hist_early_order_slices"]
        candidate_a_label = "0_7" if torus == "clifford" else "8_15"
        candidate_b_label = "0_15" if torus == "clifford" else "8_15"
        candidate_a_mi = float(early_order_sweep[candidate_a_label]["I_AB"])
        candidate_b_mi = (
            float(row["xi_hist_outer_cq"]["I_AB"])
            if candidate_b_label == "0_15"
            else float(early_order_sweep[candidate_b_label]["I_AB"])
        )
        uniform_0_15_mi = float(row["xi_hist_outer_cq"]["I_AB"])
        full_cycle_mi = float(row["xi_hist_cycle_cq"]["I_AB"])
        candidate_a_minus_uniform_0_15 = float(candidate_a_mi - uniform_0_15_mi)
        candidate_b_minus_uniform_0_15 = float(candidate_b_mi - uniform_0_15_mi)
        candidate_a_minus_full_cycle = float(candidate_a_mi - full_cycle_mi)
        candidate_b_minus_full_cycle = float(candidate_b_mi - full_cycle_mi)
        candidate_b_minus_candidate_a = float(candidate_b_mi - candidate_a_mi)
        if candidate_a_minus_uniform_0_15 > 1e-6:
            candidate_a_beats_uniform_0_15_count += 1
        if candidate_b_minus_uniform_0_15 > 1e-6:
            candidate_b_beats_uniform_0_15_count += 1
        if candidate_a_minus_full_cycle > 1e-6:
            candidate_a_beats_full_cycle_count += 1
        if candidate_b_minus_full_cycle > 1e-6:
            candidate_b_beats_full_cycle_count += 1
        clifford_mi_candidate_rows.append(
            {
                "engine_type": int(row["engine_type"]),
                "torus": torus,
                "candidate_a_mi_label": candidate_a_label,
                "candidate_b_mi_label": candidate_b_label,
                "candidate_a_mi": candidate_a_mi,
                "candidate_b_mi": candidate_b_mi,
                "uniform_0_15_mi": uniform_0_15_mi,
                "full_cycle_mi": full_cycle_mi,
                "candidate_a_minus_uniform_0_15_mi": candidate_a_minus_uniform_0_15,
                "candidate_b_minus_uniform_0_15_mi": candidate_b_minus_uniform_0_15,
                "candidate_a_minus_full_cycle_mi": candidate_a_minus_full_cycle,
                "candidate_b_minus_full_cycle_mi": candidate_b_minus_full_cycle,
                "candidate_b_minus_candidate_a_mi": candidate_b_minus_candidate_a,
            }
        )
    mean_candidate_a_gain_over_0_15 = float(
        np.mean([row["candidate_a_minus_uniform_0_15_mi"] for row in clifford_mi_candidate_rows])
    )
    mean_candidate_b_gain_over_0_15 = float(
        np.mean([row["candidate_b_minus_uniform_0_15_mi"] for row in clifford_mi_candidate_rows])
    )
    mean_candidate_a_gain_over_full_cycle = float(
        np.mean([row["candidate_a_minus_full_cycle_mi"] for row in clifford_mi_candidate_rows])
    )
    mean_candidate_b_gain_over_full_cycle = float(
        np.mean([row["candidate_b_minus_full_cycle_mi"] for row in clifford_mi_candidate_rows])
    )
    clifford_only_rows = [row for row in clifford_mi_candidate_rows if row["torus"] == "clifford"]
    mean_clifford_candidate_b_minus_candidate_a_mi = float(
        np.mean([row["candidate_b_minus_candidate_a_mi"] for row in clifford_only_rows])
    )
    better_clifford_mi_candidate = "tie"
    if mean_clifford_candidate_b_minus_candidate_a_mi > 1e-6:
        better_clifford_mi_candidate = "B"
    elif mean_clifford_candidate_b_minus_candidate_a_mi < -1e-6:
        better_clifford_mi_candidate = "A"
    xi_hist_signed_law_summary = {
        "law_name": "Xi_hist signed law",
        "owner_read": "late-anchor equivalence plus clifford-local short-width stress",
        "late_anchor_equivalence": {
            "placement_8_23_equals_16_31": bool(
                placement_8_23_equals_16_31_count == len(late_anchor_rows)
            ),
            "placement_8_23_equals_prefix_8_15_on_mi": bool(
                placement_8_23_equals_prefix_8_15_on_mi_count == len(late_anchor_rows)
            ),
            "placement_8_23_equals_prefix_8_15_on_ic": bool(
                placement_8_23_equals_prefix_8_15_on_ic_count == len(late_anchor_rows)
            ),
            "placement_8_23_equals_prefix_8_15_on_signed_cut": bool(
                placement_8_23_equals_prefix_8_15_on_signed_count == len(late_anchor_rows)
            ),
        },
        "short_width_stress": {
            "best_early_width_by_ic_is_0_3": bool(
                all(row["best_early_width_by_ic"] == "0_3" for row in early_width_rows)
            ),
            "late_anchor_beats_0_3_off_clifford": bool(
                placement_8_23_beats_0_3_on_ic_off_clifford_count == 4
            ),
            "0_3_beats_late_anchor_on_clifford_only": bool(
                short_width_0_3_beats_8_23_on_ic_clifford_count == 2
            ),
        },
        "counts": {
            "total_rows": len(late_anchor_rows),
            "off_clifford_rows": int(sum(1 for row in late_anchor_rows if row["torus"] in ("inner", "outer"))),
            "clifford_rows": int(sum(1 for row in late_anchor_rows if row["torus"] == "clifford")),
            "placement_8_23_beats_0_3_on_ic_off_clifford_count": placement_8_23_beats_0_3_on_ic_off_clifford_count,
            "short_width_0_3_beats_8_23_on_ic_clifford_count": short_width_0_3_beats_8_23_on_ic_clifford_count,
        },
    }

    return {
        "pointwise_shell_loop_variation": loop_variation,
        "ranges": {
            "xi_lr_direct_MI_range": float(max(lr_direct_mi) - min(lr_direct_mi)),
            "xi_hist_outer_MI_range": float(max(hist_outer_mi) - min(hist_outer_mi)),
            "xi_hist_cycle_MI_range": float(max(hist_cycle_mi) - min(hist_cycle_mi)),
            "xi_hist_outer_Ic_range": float(max(hist_outer_ic) - min(hist_outer_ic)),
            "xi_hist_cycle_Ic_range": float(max(hist_cycle_ic) - min(hist_cycle_ic)),
        },
        "means": {
            "xi_lr_direct_MI": mean_lr_mi,
            "xi_hist_outer_MI": mean_hist_outer_mi,
            "xi_hist_cycle_MI": mean_hist_cycle_mi,
            "xi_hist_outer_Ic": mean_hist_outer_ic,
            "xi_hist_cycle_Ic": mean_hist_cycle_ic,
            "xi_shell_strata_base_I_std": mean_shell_base_std,
            "xi_point_ref_base_I_std": mean_point_ref_base_std,
        },
        "discriminators": {
            "hist_outer_minus_lr_mi": float(mean_hist_outer_mi - mean_lr_mi),
            "hist_cycle_minus_lr_mi": float(mean_hist_cycle_mi - mean_lr_mi),
            "point_ref_minus_shell_base_std": float(mean_point_ref_base_std - mean_shell_base_std),
            "history_nontrivial_while_direct_trivial": bool(mean_hist_cycle_mi > 1e-3 and max(abs(v) for v in lr_direct_mi) < 1e-9),
            "history_nontrivial_while_shell_flat": bool(mean_hist_cycle_mi > 1e-3 and max(shell_base_stds) < 1e-3),
        },
        "rowwise_advantage_summary": {
            "threshold_mi_gain": threshold,
            "total_rows": len(engine_rows),
            "history_outer_beats_lr_count": history_outer_beats_lr_count,
            "history_cycle_beats_lr_count": history_cycle_beats_lr_count,
            "history_outer_beats_lr_while_shell_flat_count": history_outer_beats_lr_while_shell_flat_count,
            "history_cycle_beats_lr_while_shell_flat_count": history_cycle_beats_lr_while_shell_flat_count,
            "rows": rowwise_advantage,
        },
        "history_window_profile_summary": {
            "total_rows": len(history_window_rows),
            "outer_window_beats_cycle_count": outer_window_beats_cycle_count,
            "cycle_window_beats_outer_count": cycle_window_beats_outer_count,
            "mean_history_outer_minus_cycle_mi": mean_history_outer_minus_cycle_mi,
            "mean_history_outer_minus_cycle_ic": mean_history_outer_minus_cycle_ic,
            "mean_clifford_outer_minus_cycle_mi": mean_clifford_outer_minus_cycle_mi,
            "mean_clifford_outer_minus_cycle_ic": mean_clifford_outer_minus_cycle_ic,
            "rows": history_window_rows,
        },
        "history_window_sweep_summary": {
            "window_labels": [label for label, _, _ in HISTORY_WINDOW_SPECS],
            "total_rows": len(history_window_sweep_rows),
            "best_window_by_mi_counts": best_window_counts,
            "history_window_mi_monotonic_decay_count": monotonic_decay_count,
            "rows": history_window_sweep_rows,
        },
        "history_window_placement_summary": {
            "placement_labels": [label for label, _, _ in HISTORY_PLACEMENT_SPECS],
            "total_rows": len(placement_rows),
            "best_placement_by_mi_counts": best_placement_counts,
            "early_window_beats_shifted_count": early_beats_shifted_count,
            "rows": placement_rows,
        },
        "history_early_width_summary": {
            "width_labels": [label for label, _, _ in EARLY_WIDTH_SPECS],
            "total_rows": len(early_width_rows),
            "best_early_width_by_mi_counts": best_early_width_counts,
            "early_width_mi_monotonic_growth_count": early_width_monotonic_growth_count,
            "rows": early_width_rows,
        },
        "history_early_order_summary": {
            "slice_labels": [label for label, _, _ in EARLY_ORDER_SPECS],
            "total_rows": len(early_order_rows),
            "first_half_beats_second_half_count": first_half_beats_second_half_count,
            "first_half_beats_second_half_on_signed_cut_count": first_half_beats_second_half_on_signed_cut_count,
            "second_half_beats_first_half_on_signed_cut_count": second_half_beats_first_half_on_signed_cut_count,
            "rows": early_order_rows,
        },
        "history_prefix_drop_summary": {
            "prefix_drop_labels": [label for label, _, _ in PREFIX_DROP_SPECS],
            "total_rows": len(prefix_drop_rows),
            "best_prefix_drop_by_mi_counts": prefix_drop_best_counts,
            "prefix_drop_mi_monotonic_loss_count": prefix_drop_monotonic_loss_count,
            "rows": prefix_drop_rows,
        },
        "history_late_anchor_equivalence_summary": {
            "total_rows": len(late_anchor_rows),
            "placement_8_23_equals_16_31_count": placement_8_23_equals_16_31_count,
            "placement_8_23_equals_prefix_8_15_on_mi_count": placement_8_23_equals_prefix_8_15_on_mi_count,
            "placement_8_23_equals_prefix_8_15_on_ic_count": placement_8_23_equals_prefix_8_15_on_ic_count,
            "placement_8_23_equals_prefix_8_15_on_signed_count": placement_8_23_equals_prefix_8_15_on_signed_count,
            "placement_8_23_beats_0_3_on_ic_count": placement_8_23_beats_0_3_on_ic_count,
            "placement_8_23_beats_0_3_on_ic_off_clifford_count": placement_8_23_beats_0_3_on_ic_off_clifford_count,
            "short_width_0_3_beats_8_23_on_ic_clifford_count": short_width_0_3_beats_8_23_on_ic_clifford_count,
            "rows": late_anchor_rows,
        },
        "xi_hist_signed_law_summary": xi_hist_signed_law_summary,
        "history_seat_aware_summary": history_seat_aware_summary,
        "seat_aware_candidate_comparison_summary": {
            "mi_candidate_rule": "inner_outer_use_8_15__clifford_use_0_15",
            "signed_cut_candidate_rule": "all_seats_use_8_15",
            "mi_baselines": ["uniform_0_15", "uniform_0_31"],
            "signed_cut_baseline": "uniform_0_15",
            "total_rows": len(seat_aware_candidate_rows),
            "seat_aware_beats_uniform_0_15_count": seat_aware_beats_uniform_0_15_count,
            "seat_aware_beats_full_cycle_count": seat_aware_beats_full_cycle_count,
            "seat_aware_signed_cut_beats_uniform_0_15_count": seat_aware_signed_cut_beats_uniform_0_15_count,
            "mean_seat_aware_mi_gain_over_0_15": mean_seat_aware_mi_gain_over_0_15,
            "mean_seat_aware_mi_gain_over_full_cycle": mean_seat_aware_mi_gain_over_full_cycle,
            "mean_seat_aware_signed_cut_gain_over_0_15": mean_seat_aware_signed_cut_gain_over_0_15,
            "rows": seat_aware_candidate_rows,
        },
        "clifford_mi_candidate_comparison_summary": {
            "mi_candidate_a_rule": "inner_outer_use_8_15__clifford_use_0_7",
            "mi_candidate_b_rule": "inner_outer_use_8_15__clifford_use_0_15",
            "mi_baselines": ["uniform_0_15", "uniform_0_31"],
            "total_rows": len(clifford_mi_candidate_rows),
            "candidate_a_beats_uniform_0_15_count": candidate_a_beats_uniform_0_15_count,
            "candidate_b_beats_uniform_0_15_count": candidate_b_beats_uniform_0_15_count,
            "candidate_a_beats_full_cycle_count": candidate_a_beats_full_cycle_count,
            "candidate_b_beats_full_cycle_count": candidate_b_beats_full_cycle_count,
            "mean_candidate_a_gain_over_0_15": mean_candidate_a_gain_over_0_15,
            "mean_candidate_b_gain_over_0_15": mean_candidate_b_gain_over_0_15,
            "mean_candidate_a_gain_over_full_cycle": mean_candidate_a_gain_over_full_cycle,
            "mean_candidate_b_gain_over_full_cycle": mean_candidate_b_gain_over_full_cycle,
            "mean_clifford_candidate_b_minus_candidate_a_mi": mean_clifford_candidate_b_minus_candidate_a_mi,
            "better_clifford_mi_candidate": better_clifford_mi_candidate,
            "rows": clifford_mi_candidate_rows,
        },
        "axis0_current_live_seat_summary": {
            "mi_seat_pattern": mi_seat_pattern,
            "signed_cut_seat_pattern": signed_cut_seat_pattern,
            "mi_read": "inner_outer_back_half__clifford_0_15__clifford_front_half_lean",
            "signed_cut_read": "all_seats_back_half",
        },
        "clifford_edge_case_summary": {
            "threshold_mi_gain": threshold,
            "mean_clifford_hist_outer_mi": mean_clifford_hist_outer_mi,
            "mean_clifford_hist_cycle_mi": mean_clifford_hist_cycle_mi,
            "mean_inner_outer_hist_outer_mi": mean_inner_outer_hist_outer_mi,
            "mean_inner_outer_hist_cycle_mi": mean_inner_outer_hist_cycle_mi,
            "hist_outer_clifford_vs_inner_outer_gap": float(
                mean_clifford_hist_outer_mi - mean_inner_outer_hist_outer_mi
            ),
            "hist_cycle_clifford_vs_inner_outer_gap": float(
                mean_clifford_hist_cycle_mi - mean_inner_outer_hist_cycle_mi
            ),
            "mean_clifford_hist_outer_minus_lr_ic": mean_clifford_hist_outer_minus_lr_ic,
            "mean_clifford_hist_cycle_minus_lr_ic": mean_clifford_hist_cycle_minus_lr_ic,
            "mean_clifford_hist_outer_minus_lr_s_b": mean_clifford_hist_outer_minus_lr_s_b,
            "mean_clifford_hist_outer_minus_lr_s_ab": mean_clifford_hist_outer_minus_lr_s_ab,
            "mean_clifford_hist_cycle_minus_lr_s_b": mean_clifford_hist_cycle_minus_lr_s_b,
            "mean_clifford_hist_cycle_minus_lr_s_ab": mean_clifford_hist_cycle_minus_lr_s_ab,
            "clifford_point_ref_base_std": clifford_point_ref_base_std,
            "mean_inner_outer_point_ref_base_std": mean_inner_outer_point_ref_base_std,
            "point_ref_base_std_clifford_vs_inner_outer_gap": float(
                clifford_point_ref_base_std - mean_inner_outer_point_ref_base_std
            ),
            "clifford_midpoint_hist_outer_mi_gap": clifford_midpoint_hist_outer_mi_gap,
            "clifford_midpoint_hist_cycle_mi_gap": clifford_midpoint_hist_cycle_mi_gap,
            "inner_outer_hist_outer_mi_asymmetry": inner_outer_hist_outer_mi_asymmetry,
            "inner_outer_hist_cycle_mi_asymmetry": inner_outer_hist_cycle_mi_asymmetry,
            "clifford_is_midpoint_on_hist_outer_mi": bool(
                clifford_midpoint_hist_outer_mi_gap <= inner_outer_hist_outer_mi_asymmetry
            ),
            "clifford_is_midpoint_on_hist_cycle_mi": bool(
                clifford_midpoint_hist_cycle_mi_gap <= inner_outer_hist_cycle_mi_asymmetry
            ),
            "clifford_history_suppressed_on_mi": bool(
                mean_clifford_hist_cycle_mi < threshold and mean_clifford_hist_outer_mi < threshold
            ),
            "clifford_history_nonflat_on_signed_cut": bool(
                abs(mean_clifford_hist_cycle_minus_lr_ic) > 1e-2
                or abs(mean_clifford_hist_outer_minus_lr_ic) > 1e-2
            ),
            "clifford_point_ref_base_peak": bool(
                clifford_point_ref_base_std > mean_inner_outer_point_ref_base_std
            ),
        },
        "kills": {
            "xi_lr_direct_correlation_trivial": bool(max(abs(v) for v in lr_direct_mi) < 1e-9),
            "xi_shell_strata_fiber_constant": bool(
                all(abs(loop_variation[name]["shell_strata"]["fiber_I_std"]) < 1e-9 for name in loop_variation)
            ),
            "xi_shell_strata_base_varies": bool(
                any(loop_variation[name]["shell_strata"]["base_I_std"] > 1e-3 for name in loop_variation)
            ),
            "xi_point_ref_fiber_constant": bool(
                all(abs(loop_variation[name]["point_ref"]["fiber_I_std"]) < 1e-9 for name in loop_variation)
            ),
            "xi_point_ref_base_varies": bool(
                any(loop_variation[name]["point_ref"]["base_I_std"] > 1e-3 for name in loop_variation)
            ),
            "xi_hist_cycle_nontrivial": bool(np.mean(hist_cycle_mi) > 1e-3),
            "xi_hist_outer_nontrivial": bool(np.mean(hist_outer_mi) > 1e-3),
        },
    }


def main() -> None:
    pointwise_shell = run_pointwise_shell_suite()
    engine_rows = run_engine_history_suite()
    verdict = verdicts(pointwise_shell, engine_rows)

    payload = {
        "schema": "AXIS0_XI_STRICT_BAKEOFF_V1",
        "timestamp": datetime.now(UTC).isoformat(),
        "pointwise_shell": pointwise_shell,
        "engine_history_bakeoff": engine_rows,
        "verdict": verdict,
        "note": (
            "Strict Ax0 bakeoff on the live Hopf/Weyl engine. Xi_shell and Xi_hist "
            "are classical-label bridge candidates; Xi_LR_direct is an honest direct "
            "L|R control."
        ),
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis0_xi_strict_bakeoff_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("=" * 72)
    print("AXIS 0 XI STRICT BAKEOFF")
    print("=" * 72)
    print("\nPointwise shell bridge:")
    for torus_label, loop_data in pointwise_shell.items():
        fiber_shell = loop_data["fiber"]["xi_shell_strata_cq"]
        base_shell = loop_data["base"]["xi_shell_strata_cq"]
        fiber_ref = loop_data["fiber"]["xi_point_ref_cq"]
        base_ref = loop_data["base"]["xi_point_ref_cq"]
        print(
            f"  {torus_label:9s} "
            f"shell[fiber std={fiber_shell['I_AB']['std']:.6f}, base std={base_shell['I_AB']['std']:.6f}]   "
            f"ref[fiber std={fiber_ref['I_AB']['std']:.6f}, base std={base_ref['I_AB']['std']:.6f}]"
        )

    print("\nEngine history bakeoff:")
    for row in engine_rows:
        print(
            f"  T{row['engine_type']} {row['torus']:9s} "
            f"LR MI={row['xi_lr_direct']['I_AB']:.6f} "
            f"Hist_outer MI={row['xi_hist_outer_cq']['I_AB']:.6f} "
            f"Hist_cycle MI={row['xi_hist_cycle_cq']['I_AB']:.6f} "
            f"Hist_cycle Ic={row['xi_hist_cycle_cq']['I_c_A_to_B']:+.6f}"
        )

    print("\nVerdict summary:")
    print(json.dumps(verdict, indent=2))
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
