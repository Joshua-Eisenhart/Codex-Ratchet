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
    return {
        "I_AB": mutual_information(rho, dims),
        "S_A_given_B": conditional_entropy(rho, dims),
        "I_c_A_to_B": coherent_information(rho, dims),
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


def pair_state_from_state(state) -> np.ndarray:
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


def xi_hist_cq_from_pairs(pair_states: Sequence[np.ndarray]) -> Tuple[np.ndarray, List[int], Dict[str, object]]:
    n = len(pair_states)
    if n == 0:
        raise ValueError("Need at least one pair state for Xi_hist")
    weights = np.full(n, 1.0 / n, dtype=float)
    rho, dims = build_cq_state(weights, pair_states)
    meta = {
        "n_samples": int(n),
        "weight_type": "uniform",
    }
    return rho, dims, meta


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


def xi_lr_direct_from_state(state) -> Tuple[np.ndarray, List[int], Dict[str, object]]:
    rho = pair_state_from_state(state)
    meta = {
        "eta": float(state.eta),
        "theta1": float(state.theta1),
        "theta2": float(state.theta2),
    }
    return rho, [2, 2], meta


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

            rho_lr, dims_lr, lr_meta = xi_lr_direct_from_state(final_state)
            lr_metrics = metrics_for_cut_state(rho_lr, dims_lr)

            pair_history = [pair_state_from_state(init_state)] + [
                pair_state_from_history_entry(entry) for entry in final_state.history
            ]

            outer_pairs = pair_history[:17]   # initial + first 16 microsteps = outer loop
            cycle_pairs = pair_history        # full 32-microstep cycle + initial

            rho_hist_outer, dims_hist_outer, outer_meta = xi_hist_cq_from_pairs(outer_pairs)
            rho_hist_cycle, dims_hist_cycle, cycle_meta = xi_hist_cq_from_pairs(cycle_pairs)
            hist_outer_metrics = metrics_for_cut_state(rho_hist_outer, dims_hist_outer)
            hist_cycle_metrics = metrics_for_cut_state(rho_hist_cycle, dims_hist_cycle)

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
                    "xi_hist_outer_cq": {
                        **hist_outer_metrics,
                        **outer_meta,
                    },
                    "xi_hist_cycle_cq": {
                        **hist_cycle_metrics,
                        **cycle_meta,
                    },
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
            "xi_lr_direct_MI": float(np.mean(lr_direct_mi)),
            "xi_hist_outer_MI": float(np.mean(hist_outer_mi)),
            "xi_hist_cycle_MI": float(np.mean(hist_cycle_mi)),
            "xi_hist_outer_Ic": float(np.mean(hist_outer_ic)),
            "xi_hist_cycle_Ic": float(np.mean(hist_cycle_ic)),
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
