#!/usr/bin/env python3
"""
Axis 0 Option Spectrum SIM
==========================

Purpose
-------
Run a broader Axis-0 spectrum over the real repo geometry and current bridge
candidates. This keeps the honest L|R guardrail in place while testing the
nontrivial Xi options under small perturbations.

Bridge / cut families covered:
  - LR_local_only       : true L|R cut with local-only dynamics
  - LR_coupled_control  : true L|R cut with explicit nonlocal coupling control
  - Xi_shell_geometry   : shell-label qubit x Dirac state along exact loops
  - Xi_hist_outer       : outer-half-cycle endpoint history surrogate
  - Xi_hist_cycle       : full-cycle endpoint history surrogate
  - Xi_LR_control       : null control on label qubit x Dirac state

Kernel metrics:
  - I(A:B)
  - S(A|B)
  - I_c(A->B) = -S(A|B)

Perturbation families:
  - depol_A
  - depol_B
  - dephase_A

Notes
-----
- This is still a spectrum / bakeoff probe, not canon.
- It tests response under perturbation, which is the common structure across
  the current Axis-0 spec options.
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime
from typing import Callable, Dict, Iterable, List, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axis0_full_constraint_manifold_guardrail_sim import (  # noqa: E402
    DED_ORDER,
    IND_ORDER,
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    apply_local_channel,
    coupling_unitary,
    left_density,
    q_on_loop,
    right_density,
    run_cycle,
    terrain_kraus_pair,
)
from axis0_xi_bakeoff_sim import (  # noqa: E402
    TORUS_CONFIGS,
    capture_engine_macrostates,
    coherent_information,
    conditional_entropy,
    exact_base_q,
    exact_fiber_q,
    mutual_information,
    partial_trace,
    xi_hist_from_states,
    xi_lr_control_from_state,
    xi_shell_from_q,
)
from proto_ratchet_sim_runner import ensure_valid  # noqa: E402


EPS = 1e-12
SPECTRUM_EPS = 0.02


def summarize(values: List[float]) -> Dict[str, float]:
    arr = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def metric_bundle(rho: np.ndarray, dims: List[int]) -> Dict[str, float]:
    return {
        "I_AB": mutual_information(rho, dims),
        "S_A_given_B": conditional_entropy(rho, dims),
        "I_c_A_to_B": coherent_information(rho, dims),
    }


def replace_subsystem_with_maxmix(rho: np.ndarray, dims: List[int], target: int) -> np.ndarray:
    if len(dims) != 2:
        raise ValueError("Spectrum probe currently supports exactly 2 subsystems")
    other = 1 - target
    rho_other = partial_trace(rho, dims, [other])
    ident_target = np.eye(dims[target], dtype=complex) / dims[target]
    if target == 0:
        out = np.kron(ident_target, rho_other)
    else:
        out = np.kron(rho_other, ident_target)
    return ensure_valid(out)


def depolarize_subsystem(rho: np.ndarray, dims: List[int], target: int, eps: float) -> np.ndarray:
    mixed = replace_subsystem_with_maxmix(rho, dims, target)
    return ensure_valid((1.0 - eps) * rho + eps * mixed)


def dephase_label_A(rho: np.ndarray, dims: List[int], eps: float) -> np.ndarray:
    if dims[0] != 2:
        raise ValueError("dephase_A only defined for a qubit first subsystem")
    p0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    p1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
    ident_b = np.eye(dims[1], dtype=complex)
    projectors = [np.kron(p0, ident_b), np.kron(p1, ident_b)]
    dephased = np.zeros_like(rho, dtype=complex)
    for proj in projectors:
        dephased += proj @ rho @ proj
    return ensure_valid((1.0 - eps) * rho + eps * dephased)


def perturb_state(rho: np.ndarray, dims: List[int], name: str, eps: float = SPECTRUM_EPS) -> np.ndarray:
    if name == "depol_A":
        return depolarize_subsystem(rho, dims, target=0, eps=eps)
    if name == "depol_B":
        return depolarize_subsystem(rho, dims, target=1, eps=eps)
    if name == "dephase_A":
        return dephase_label_A(rho, dims, eps=eps)
    raise ValueError(f"unknown perturbation: {name}")


def finite_difference_bundle(rho: np.ndarray, dims: List[int], perturbation: str, eps: float = SPECTRUM_EPS) -> Dict[str, float]:
    base = metric_bundle(rho, dims)
    perturbed = metric_bundle(perturb_state(rho, dims, perturbation, eps=eps), dims)
    return {key: float((perturbed[key] - base[key]) / eps) for key in base}


def positive_distribution(values: Iterable[float]) -> np.ndarray:
    arr = np.maximum(np.asarray(list(values), dtype=float), 0.0)
    total = float(np.sum(arr))
    if total < EPS:
        return np.array([], dtype=float)
    return arr / total


def shannon_entropy(dist: np.ndarray) -> float:
    if len(dist) == 0:
        return 0.0
    mask = dist > EPS
    return float(-np.sum(dist[mask] * np.log(dist[mask])))


def run_guardrail_final_state(order: List[str], eta: float, loop_type: str, mode: str, n_substeps: int = 16) -> np.ndarray:
    phi0 = 0.0
    chi0 = 0.0
    q0 = q_on_loop(phi0, chi0, eta, 0.0, loop_type)
    rho_ab = np.kron(left_density(q0), right_density(q0))
    total_steps = len(order) * n_substeps

    for stage_idx, terrain in enumerate(order):
        for sub_idx in range(n_substeps):
            global_idx = stage_idx * n_substeps + sub_idx + 1
            u = 2.0 * np.pi * global_idx / total_steps
            q = q_on_loop(phi0, chi0, eta, u, loop_type)
            kraus_L, kraus_R = terrain_kraus_pair(terrain, q)
            rho_ab = apply_local_channel(rho_ab, kraus_L, kraus_R)
            if mode == "coupled_control":
                U = coupling_unitary(eta, loop_type, terrain)
                rho_ab = ensure_valid(U @ rho_ab @ U.conj().T)

    return ensure_valid(rho_ab)


def collect_lr_family() -> List[Dict[str, object]]:
    rows = []
    for eta_label, eta in TORUS_CONFIGS:
        for loop_type in ("fiber", "base"):
            for order_name, order in (("DED", DED_ORDER), ("IND", IND_ORDER)):
                for mode in ("local_only", "coupled_control"):
                    traj = run_cycle(order, eta, loop_type, mode)
                    rho = run_guardrail_final_state(order, eta, loop_type, mode)
                    rows.append({
                        "family": f"LR_{mode}",
                        "rho": rho,
                        "dims": [2, 2],
                        "meta": {
                            "eta_label": eta_label,
                            "eta": float(eta),
                            "loop_type": loop_type,
                            "order_name": order_name,
                            "trajectory_MI_max": float(traj["MI_max"]),
                            "trajectory_MI_final": float(traj["MI_final"]),
                            "trajectory_CI_final": float(traj["CI_final"]),
                        },
                    })
    return rows


def collect_xi_shell_family(n_samples: int = 16) -> List[Dict[str, object]]:
    rows = []
    u_grid = np.linspace(0.0, 2.0 * np.pi, n_samples, endpoint=False)
    for eta_label, eta in TORUS_CONFIGS:
        for loop_type, q_fn in (("fiber", exact_fiber_q), ("base", exact_base_q)):
            for idx, u in enumerate(u_grid):
                rho, dims, meta = xi_shell_from_q(q_fn(eta, float(u)))
                rows.append({
                    "family": "Xi_shell_geometry",
                    "rho": rho,
                    "dims": dims,
                    "meta": {
                        "eta_label": eta_label,
                        "eta": float(eta),
                        "loop_type": loop_type,
                        "sample_idx": idx,
                        **meta,
                    },
                })
    return rows


def collect_engine_xi_families() -> List[Dict[str, object]]:
    rows = []
    for engine_type in (1, 2):
        n_macro_stages = len(capture_engine_macrostates(engine_type, TORUS_CLIFFORD, n_cycles=1)[1]) - 1
        half_cycle_idx = n_macro_stages // 2
        full_cycle_idx = n_macro_stages
        for eta_label, eta in TORUS_CONFIGS:
            _, snapshots = capture_engine_macrostates(engine_type, eta, n_cycles=1)
            outer_end = snapshots[half_cycle_idx]
            cycle_end = snapshots[full_cycle_idx]

            rho_hist_outer, dims_hist, meta_outer = xi_hist_from_states(snapshots[0], outer_end)
            rows.append({
                "family": "Xi_hist_outer",
                "rho": rho_hist_outer,
                "dims": dims_hist,
                "meta": {
                    "engine_type": engine_type,
                    "eta_label": eta_label,
                    "eta": float(eta),
                    **meta_outer,
                },
            })

            rho_hist_cycle, dims_hist, meta_cycle = xi_hist_from_states(snapshots[0], cycle_end)
            rows.append({
                "family": "Xi_hist_cycle",
                "rho": rho_hist_cycle,
                "dims": dims_hist,
                "meta": {
                    "engine_type": engine_type,
                    "eta_label": eta_label,
                    "eta": float(eta),
                    **meta_cycle,
                },
            })

            rho_lr, dims_lr, meta_lr = xi_lr_control_from_state(cycle_end)
            rows.append({
                "family": "Xi_LR_control",
                "rho": rho_lr,
                "dims": dims_lr,
                "meta": {
                    "engine_type": engine_type,
                    "eta_label": eta_label,
                    "eta": float(eta),
                    **meta_lr,
                },
            })
    return rows


def evaluate_rows(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    perturbations = ["depol_A", "depol_B", "dephase_A"]
    evaluated = []
    for row in rows:
        rho = row["rho"]
        dims = row["dims"]
        base = metric_bundle(rho, dims)
        responses = {
            name: finite_difference_bundle(rho, dims, name)
            for name in perturbations
        }
        evaluated.append({
            "family": row["family"],
            "dims": dims,
            "meta": row["meta"],
            "baseline": base,
            "responses": responses,
        })
    return evaluated


def family_summary(entries: List[Dict[str, object]]) -> Dict[str, object]:
    kernels = ["I_AB", "S_A_given_B", "I_c_A_to_B"]
    perturbations = ["depol_A", "depol_B", "dephase_A"]
    summary = {
        "n_instances": len(entries),
        "baseline": {},
        "responses": {},
        "dynamic": {},
        "option_family_views": {},
        "kill_flags": {},
    }

    for kernel in kernels:
        vals = [row["baseline"][kernel] for row in entries]
        summary["baseline"][kernel] = summarize(vals)

    for perturb in perturbations:
        summary["responses"][perturb] = {}
        for kernel in kernels:
            vals = [row["responses"][perturb][kernel] for row in entries]
            summary["responses"][perturb][kernel] = summarize(vals)

    mi_vals = [row["baseline"]["I_AB"] for row in entries]
    ic_pos_vals = [max(row["baseline"]["I_c_A_to_B"], 0.0) for row in entries]
    mi_dist = positive_distribution(mi_vals)
    ic_dist = positive_distribution(ic_pos_vals)
    summary["option_family_views"] = {
        "MI_spread_entropy": shannon_entropy(mi_dist),
        "MI_variance": float(np.var(np.asarray(mi_vals, dtype=float))),
        "Ic_positive_spread_entropy": shannon_entropy(ic_dist),
        "Ic_positive_variance": float(np.var(np.asarray(ic_pos_vals, dtype=float))),
    }

    eta_groups = defaultdict(list)
    loop_groups = defaultdict(list)
    order_groups = defaultdict(list)
    for row in entries:
        meta = row["meta"]
        if "eta_label" in meta:
            eta_groups[str(meta["eta_label"])].append(row["baseline"]["I_c_A_to_B"])
        if "loop_type" in meta:
            loop_groups[str(meta["loop_type"])].append(row["baseline"]["I_c_A_to_B"])
        if "order_name" in meta:
            order_groups[str(meta["order_name"])].append(row["baseline"]["I_c_A_to_B"])

    eta_means = {k: float(np.mean(v)) for k, v in eta_groups.items()}
    loop_means = {k: float(np.mean(v)) for k, v in loop_groups.items()}
    order_means = {k: float(np.mean(v)) for k, v in order_groups.items()}
    summary["group_means"] = {
        "eta": eta_means,
        "loop": loop_means,
        "order": order_means,
    }

    dyn_keys = ["trajectory_MI_max", "trajectory_MI_final", "trajectory_CI_final"]
    for dyn_key in dyn_keys:
        dyn_vals = [row["meta"][dyn_key] for row in entries if dyn_key in row["meta"]]
        if dyn_vals:
            summary["dynamic"][dyn_key] = summarize(dyn_vals)

    i_abs = [abs(v) for v in [row["baseline"]["I_AB"] for row in entries]]
    ic_abs = [abs(v) for v in [row["baseline"]["I_c_A_to_B"] for row in entries]]
    summary["kill_flags"] = {
        "trivial_I": bool(max(i_abs) < 1e-6) if i_abs else True,
        "trivial_Ic": bool(max(ic_abs) < 1e-6) if ic_abs else True,
        "saturated_Ic": bool(np.mean(ic_abs) > 0.95 and np.std(ic_abs) < 0.05) if ic_abs else False,
        "geometry_blind_Ic": bool((max(eta_means.values()) - min(eta_means.values())) < 1e-4) if len(eta_means) >= 2 else False,
        "loop_blind_Ic": bool((max(loop_means.values()) - min(loop_means.values())) < 1e-6) if len(loop_means) >= 2 else False,
        "order_blind_Ic": bool((max(order_means.values()) - min(order_means.values())) < 1e-6) if len(order_means) >= 2 else False,
    }
    return summary


def main() -> None:
    raw_rows = []
    raw_rows.extend(collect_lr_family())
    raw_rows.extend(collect_xi_shell_family())
    raw_rows.extend(collect_engine_xi_families())
    evaluated = evaluate_rows(raw_rows)

    families = sorted({row["family"] for row in evaluated})
    summaries = {
        family: family_summary([row for row in evaluated if row["family"] == family])
        for family in families
    }

    payload = {
        "schema": "AXIS0_OPTION_SPECTRUM_V1",
        "timestamp": datetime.now(UTC).isoformat(),
        "eps": SPECTRUM_EPS,
        "families": families,
        "summaries": summaries,
        "instances": evaluated,
        "notes": {
            "interpretation": "Full-spectrum Axis-0 option scan over current real geometry and bridge candidates.",
            "warning": "Xi families are still candidate bridges, not canon subsystem cuts.",
        },
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis0_option_spectrum_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("=" * 76)
    print("AXIS 0 OPTION SPECTRUM SIM")
    print("=" * 76)
    for family in families:
        s = summaries[family]
        print(
            f"{family:18s} "
            f"Ic_mean={s['baseline']['I_c_A_to_B']['mean']:+.6f} "
            f"Ic_std={s['baseline']['I_c_A_to_B']['std']:.6f} "
            f"dIc/depolB={s['responses']['depol_B']['I_c_A_to_B']['mean']:+.6f} "
            f"kills={s['kill_flags']}"
        )
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
