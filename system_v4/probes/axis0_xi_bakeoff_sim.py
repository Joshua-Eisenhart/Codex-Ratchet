#!/usr/bin/env python3
"""
Axis 0 Xi Bakeoff — Full Geometry Candidate Probe
=================================================

Goal:
  Run the strongest currently available full-stack candidate for Axis 0 on the
  real Hopf/Weyl geometry, without pretending the bridge is canon-locked.

This probe combines:
  1. real S^3 / nested Hopf-torus geometry
  2. explicit left/right Weyl spinors
  3. explicit fiber/base loop structure
  4. candidate Xi bridges into cut states
  5. direct evaluation of Axis 0 kernel candidates on those cut states

Bridge candidates:
  - Xi_shell : pointwise shell-label qubit x Dirac/Weyl-pair state
  - Xi_hist  : history-window label qubit x Dirac/Weyl-pair state
  - Xi_LR_control : noncanon negative control

This is intentionally a bakeoff. Passing here means "strong executable
candidate", not "finished canon".
"""

import copy
import json
import os
from datetime import UTC, datetime
from typing import Dict, List, Tuple

import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, LOOP_STAGE_ORDER, StageControls
from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    fiber_action,
    left_weyl_spinor,
    right_weyl_spinor,
    torus_coordinates,
)
from proto_ratchet_sim_runner import von_neumann_entropy


EPS = 1e-12
TORUS_CONFIGS = [
    ("inner", TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer", TORUS_OUTER),
]


def normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm < EPS:
        raise ValueError("Cannot normalize near-zero vector")
    return vec / norm


def pure_density(vec: np.ndarray) -> np.ndarray:
    vec = normalize(vec)
    return np.outer(vec, vec.conj())


def ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(np.real(evals), 0.0)
    rho = evecs @ np.diag(evals.astype(complex)) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > EPS:
        rho /= tr
    return rho


def partial_trace(rho: np.ndarray, dims: List[int], keep_indices: List[int]) -> np.ndarray:
    num_subsys = len(dims)
    trace_indices = [i for i in range(num_subsys) if i not in keep_indices]
    if not trace_indices:
        return rho

    rho_tensor = rho.reshape(tuple(dims) + tuple(dims))
    axes = keep_indices + trace_indices + [i + num_subsys for i in keep_indices] + [i + num_subsys for i in trace_indices]
    rho_reordered = np.transpose(rho_tensor, axes)

    keep_dims = [dims[i] for i in keep_indices]
    trace_dims = [dims[i] for i in trace_indices]
    d_keep = int(np.prod(keep_dims))
    d_trace = int(np.prod(trace_dims))
    rho_matrix = rho_reordered.reshape((d_keep, d_trace, d_keep, d_trace))
    return np.trace(rho_matrix, axis1=1, axis2=3)


def mutual_information(rho_ab: np.ndarray, dims: List[int]) -> float:
    rho_a = partial_trace(rho_ab, dims, [0])
    rho_b = partial_trace(rho_ab, dims, [1])
    s_a = von_neumann_entropy(rho_a)
    s_b = von_neumann_entropy(rho_b)
    s_ab = von_neumann_entropy(rho_ab)
    return float(max(0.0, s_a + s_b - s_ab))


def conditional_entropy(rho_ab: np.ndarray, dims: List[int]) -> float:
    rho_b = partial_trace(rho_ab, dims, [1])
    s_b = von_neumann_entropy(rho_b)
    s_ab = von_neumann_entropy(rho_ab)
    return float(s_ab - s_b)


def coherent_information(rho_ab: np.ndarray, dims: List[int]) -> float:
    return float(-conditional_entropy(rho_ab, dims))


def overlap_phase(vec_a: np.ndarray, vec_b: np.ndarray) -> complex:
    inner = np.vdot(vec_a, vec_b)
    if abs(inner) < EPS:
        return 1.0 + 0.0j
    return inner / abs(inner)


def q_to_torus_angles(q: np.ndarray) -> Tuple[float, float, float]:
    a, b, c, d = q
    z1 = a + 1j * b
    z2 = c + 1j * d
    eta = float(np.arctan2(abs(z2), abs(z1)))
    theta1 = float(np.angle(z1))
    theta2 = float(np.angle(z2))
    return eta, theta1, theta2


def dirac_from_q(q: np.ndarray) -> np.ndarray:
    psi_l = left_weyl_spinor(q)
    psi_r = right_weyl_spinor(q)
    return normalize(np.concatenate([psi_l, psi_r]))


def dirac_from_state(state) -> np.ndarray:
    return normalize(np.concatenate([state.psi_L, state.psi_R]))


def build_label_superposition(vec_a: np.ndarray, vec_b: np.ndarray, weight_a: float, weight_b: float, phase: complex) -> np.ndarray:
    vec = np.concatenate([
        np.sqrt(weight_a) * normalize(vec_a),
        phase * np.sqrt(weight_b) * normalize(vec_b),
    ])
    return pure_density(vec)


def exact_fiber_q(eta: float, u: float) -> np.ndarray:
    q0 = torus_coordinates(eta, 0.0, 0.0)
    return fiber_action(q0, u)


def exact_base_q(eta: float, u: float) -> np.ndarray:
    theta1 = 2.0 * (np.sin(eta) ** 2) * u
    theta2 = -2.0 * (np.cos(eta) ** 2) * u
    return torus_coordinates(eta, theta1, theta2)


def xi_shell_from_q(q: np.ndarray, delta_eta: float = np.pi / 16) -> Tuple[np.ndarray, List[int], Dict[str, float]]:
    eta, theta1, theta2 = q_to_torus_angles(q)
    eta_in = max(0.01, eta - delta_eta)
    eta_out = min(np.pi / 2 - 0.01, eta + delta_eta)

    q_in = torus_coordinates(eta_in, theta1, theta2)
    q_out = torus_coordinates(eta_out, theta1, theta2)

    dirac_in = dirac_from_q(q_in)
    dirac_out = dirac_from_q(q_out)

    w_in = float(np.cos(eta) ** 2)
    w_out = float(np.sin(eta) ** 2)
    norm = w_in + w_out
    w_in /= norm
    w_out /= norm
    phase = overlap_phase(dirac_in, dirac_out)

    rho = build_label_superposition(dirac_in, dirac_out, w_in, w_out, phase)
    meta = {
        "eta": eta,
        "eta_in": eta_in,
        "eta_out": eta_out,
        "weight_in": w_in,
        "weight_out": w_out,
    }
    return rho, [2, 4], meta


def xi_hist_from_states(state_a, state_b) -> Tuple[np.ndarray, List[int], Dict[str, float]]:
    dirac_a = dirac_from_state(state_a)
    dirac_b = dirac_from_state(state_b)
    phase = overlap_phase(dirac_a, dirac_b)
    rho = build_label_superposition(dirac_a, dirac_b, 0.5, 0.5, phase)
    meta = {
        "eta_a": float(state_a.eta),
        "eta_b": float(state_b.eta),
        "theta1_a": float(state_a.theta1),
        "theta1_b": float(state_b.theta1),
        "theta2_a": float(state_a.theta2),
        "theta2_b": float(state_b.theta2),
    }
    return rho, [2, 4], meta


def xi_lr_control_from_state(state) -> Tuple[np.ndarray, List[int], Dict[str, float]]:
    # Noncanon control: a product bridge that carries the current full Dirac/Weyl
    # state on subsystem B while subsystem A is a fixed equal chirality label.
    dirac = dirac_from_state(state)
    label = normalize(np.array([1.0, 1.0], dtype=complex))
    rho = np.kron(pure_density(label), pure_density(dirac))
    meta = {
        "eta": float(state.eta),
        "theta1": float(state.theta1),
        "theta2": float(state.theta2),
    }
    return ensure_density(rho), [2, 4], meta


def metrics_for_cut_state(rho: np.ndarray, dims: List[int]) -> Dict[str, float]:
    return {
        "I_AB": mutual_information(rho, dims),
        "S_A_given_B": conditional_entropy(rho, dims),
        "I_c_A_to_B": coherent_information(rho, dims),
    }


def capture_engine_macrostates(engine_type: int, eta: float, n_cycles: int = 1):
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=eta, theta1=0.0, theta2=0.0)
    snapshots = [copy.deepcopy(state)]

    for _ in range(n_cycles):
        for terrain_idx in LOOP_STAGE_ORDER[engine_type]:
            state = engine.step(state, stage_idx=terrain_idx, controls=StageControls(torus=eta))
            snapshots.append(copy.deepcopy(state))
    return engine, snapshots


def summarize_values(values: List[float]) -> Dict[str, float]:
    arr = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def run_pointwise_geometry_suite() -> Dict[str, Dict[str, Dict[str, float]]]:
    n_samples = 32
    u_grid = np.linspace(0.0, 2.0 * np.pi, n_samples, endpoint=False)
    results = {}

    for torus_label, eta in TORUS_CONFIGS:
        torus_result = {}
        for loop_label, q_fn in (("fiber", exact_fiber_q), ("base", exact_base_q)):
            i_vals = []
            s_vals = []
            ic_vals = []
            for u in u_grid:
                q = q_fn(eta, float(u))
                rho_shell, dims, _ = xi_shell_from_q(q)
                metrics = metrics_for_cut_state(rho_shell, dims)
                i_vals.append(metrics["I_AB"])
                s_vals.append(metrics["S_A_given_B"])
                ic_vals.append(metrics["I_c_A_to_B"])

            torus_result[loop_label] = {
                "I_AB": summarize_values(i_vals),
                "S_A_given_B": summarize_values(s_vals),
                "I_c_A_to_B": summarize_values(ic_vals),
            }
        results[torus_label] = torus_result

    return results


def run_engine_bakeoff(n_cycles: int = 1) -> List[Dict[str, object]]:
    rows = []

    for engine_type in (1, 2):
        n_macro_stages = len(LOOP_STAGE_ORDER[engine_type])
        half_cycle_idx = n_macro_stages // 2
        full_cycle_idx = n_macro_stages
        for torus_label, eta in TORUS_CONFIGS:
            engine, snapshots = capture_engine_macrostates(engine_type, eta, n_cycles=n_cycles)
            axes_final = engine.read_axes(snapshots[-1])

            rho_shell, dims_shell, shell_meta = xi_shell_from_q(snapshots[-1].q())
            shell_metrics = metrics_for_cut_state(rho_shell, dims_shell)

            rho_lr, dims_lr, lr_meta = xi_lr_control_from_state(snapshots[-1])
            lr_metrics = metrics_for_cut_state(rho_lr, dims_lr)

            outer_end = snapshots[half_cycle_idx]
            cycle_end = snapshots[full_cycle_idx]
            rho_hist_outer, dims_hist, outer_meta = xi_hist_from_states(snapshots[0], outer_end)
            rho_hist_cycle, _, cycle_meta = xi_hist_from_states(snapshots[0], cycle_end)
            hist_outer_metrics = metrics_for_cut_state(rho_hist_outer, dims_hist)
            hist_cycle_metrics = metrics_for_cut_state(rho_hist_cycle, dims_hist)

            rows.append({
                "engine_type": engine_type,
                "torus": torus_label,
                "eta": float(eta),
                "runtime_GA0_entropy": float(axes_final["GA0_entropy"]),
                "runtime_GA3_chirality": float(axes_final["GA3_chirality"]),
                "xi_shell": {
                    **shell_metrics,
                    **shell_meta,
                },
                "xi_hist_outer": {
                    **hist_outer_metrics,
                    **outer_meta,
                },
                "xi_hist_cycle": {
                    **hist_cycle_metrics,
                    **cycle_meta,
                },
                "xi_lr_control": {
                    **lr_metrics,
                    **lr_meta,
                },
            })

    return rows


def verdicts(pointwise_results: Dict[str, Dict[str, Dict[str, float]]], engine_rows: List[Dict[str, object]]) -> Dict[str, object]:
    fiber_base_diffs = {}
    for torus_label, loop_data in pointwise_results.items():
        fiber_ic = loop_data["fiber"]["I_c_A_to_B"]["mean"]
        base_ic = loop_data["base"]["I_c_A_to_B"]["mean"]
        fiber_base_diffs[torus_label] = float(base_ic - fiber_ic)

    shell_abs = [abs(row["xi_shell"]["I_c_A_to_B"]) for row in engine_rows]
    hist_abs = [abs(row["xi_hist_cycle"]["I_c_A_to_B"]) for row in engine_rows]
    lr_abs = [abs(row["xi_lr_control"]["I_c_A_to_B"]) for row in engine_rows]

    shell_eta_range = max(row["xi_shell"]["I_c_A_to_B"] for row in engine_rows) - min(row["xi_shell"]["I_c_A_to_B"] for row in engine_rows)
    hist_eta_range = max(row["xi_hist_cycle"]["I_c_A_to_B"] for row in engine_rows) - min(row["xi_hist_cycle"]["I_c_A_to_B"] for row in engine_rows)

    return {
        "fiber_base_Ic_mean_diffs": fiber_base_diffs,
        "mean_abs_Ic": {
            "xi_shell": float(np.mean(shell_abs)),
            "xi_hist_cycle": float(np.mean(hist_abs)),
            "xi_lr_control": float(np.mean(lr_abs)),
        },
        "eta_sensitivity": {
            "xi_shell_Ic_range": float(shell_eta_range),
            "xi_hist_cycle_Ic_range": float(hist_eta_range),
        },
        "kills": {
            "xi_lr_control_trivial": bool(np.mean(lr_abs) < 1e-6),
            "xi_shell_geometry_blind": bool(abs(shell_eta_range) < 1e-4),
            "xi_hist_geometry_blind": bool(abs(hist_eta_range) < 1e-4),
            "xi_shell_loop_blind": bool(max(abs(v) for v in fiber_base_diffs.values()) < 1e-8),
            "xi_hist_saturated": bool(np.mean(hist_abs) > 0.95 and abs(hist_eta_range) < 1e-2),
        },
    }


def main():
    pointwise = run_pointwise_geometry_suite()
    engine_rows = run_engine_bakeoff(n_cycles=1)
    verdict = verdicts(pointwise, engine_rows)

    payload = {
        "schema": "AXIS0_XI_BAKEOFF_V1",
        "timestamp": datetime.now(UTC).isoformat(),
        "pointwise_geometry": pointwise,
        "engine_bakeoff": engine_rows,
        "verdict": verdict,
        "note": "Candidate full-stack Ax0 probe. Xi_shell and Xi_hist are executable candidates; Xi_LR is a noncanon control.",
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis0_xi_bakeoff_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("=" * 72)
    print("AXIS 0 XI BAKEOFF — FULL GEOMETRY CANDIDATE PROBE")
    print("=" * 72)
    print("\nPointwise shell bridge mean coherent information:")
    for torus_label, loops in pointwise.items():
        fiber_ic = loops["fiber"]["I_c_A_to_B"]["mean"]
        base_ic = loops["base"]["I_c_A_to_B"]["mean"]
        print(f"  {torus_label:9s} fiber={fiber_ic:+.6f}  base={base_ic:+.6f}")

    print("\nEngine-cycle bakeoff (per engine type / torus):")
    for row in engine_rows:
        print(
            f"  T{row['engine_type']} {row['torus']:9s} "
            f"GA0={row['runtime_GA0_entropy']:.6f} "
            f"Xi_shell Ic={row['xi_shell']['I_c_A_to_B']:+.6f} "
            f"Xi_hist Ic={row['xi_hist_cycle']['I_c_A_to_B']:+.6f} "
            f"Xi_LR_ctl Ic={row['xi_lr_control']['I_c_A_to_B']:+.6f}"
        )

    print("\nVerdict summary:")
    print(json.dumps(verdict, indent=2))
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
