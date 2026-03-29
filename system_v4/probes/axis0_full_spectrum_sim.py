#!/usr/bin/env python3
"""
Axis 0 Full Spectrum SIM
========================

Purpose
-------
Run the broadest honest Axis-0 option sweep currently supported by the repo.

This probe keeps two anchor truths separate:
  1. Raw L|R on full Hopf/Weyl geometry is a guardrail baseline.
  2. Nontrivial Axis-0 candidates can still appear through explicit Xi bridges.

It compares, on real geometry where available:
  - raw L|R local-only baseline
  - raw L|R coupled control
  - Xi_shell
  - Xi_hist_outer
  - Xi_hist_cycle
  - Xi_LR_control

And for each family, it computes a spectrum of current Axis-0 option readouts:
  - I(A:B)
  - S(A|B)
  - I_c(A->B)
  - D(rho || rho_A ⊗ rho_B)
  - D(rho || Delta_AB(rho))
  - cut-family MI diversity / effective number
  - cut-family MI variance
  - perturbation-response derivatives under local depolarizing and dephasing

This is still a probe, not canon.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime
from typing import Callable, Dict, List

import numpy as np
import scipy.linalg as la

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import axis0_full_constraint_manifold_guardrail_sim as guardrail
import axis0_xi_bakeoff_sim as bakeoff
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER


EPS = 1e-12
DELTA = 0.05
U_SAMPLES = 16
TORUS_CONFIGS = [
    ("inner", TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer", TORUS_OUTER),
]


def ensure_density(rho: np.ndarray) -> np.ndarray:
    return bakeoff.ensure_density(rho)


def entropy(rho: np.ndarray) -> float:
    return bakeoff.von_neumann_entropy(rho)


def mutual_information(rho: np.ndarray, dims: List[int]) -> float:
    return bakeoff.mutual_information(rho, dims)


def conditional_entropy(rho: np.ndarray, dims: List[int]) -> float:
    return bakeoff.conditional_entropy(rho, dims)


def coherent_information(rho: np.ndarray, dims: List[int]) -> float:
    return bakeoff.coherent_information(rho, dims)


def partial_trace(rho: np.ndarray, dims: List[int], keep: List[int]) -> np.ndarray:
    return bakeoff.partial_trace(rho, dims, keep)


def product_reference(rho: np.ndarray, dims: List[int]) -> np.ndarray:
    rho_a = partial_trace(rho, dims, [0])
    rho_b = partial_trace(rho, dims, [1])
    return ensure_density(np.kron(rho_a, rho_b))


def dephase_subsystem(rho: np.ndarray, dims: List[int], target: int) -> np.ndarray:
    if len(dims) != 2:
        raise ValueError("Only bipartite dims supported")
    d_a, d_b = dims
    tensor = rho.reshape(d_a, d_b, d_a, d_b).copy()
    if target == 0:
        for i in range(d_a):
            for k in range(d_a):
                if i != k:
                    tensor[i, :, k, :] = 0.0
    elif target == 1:
        for j in range(d_b):
            for l in range(d_b):
                if j != l:
                    tensor[:, j, :, l] = 0.0
    else:
        raise ValueError("target must be 0 or 1")
    return ensure_density(tensor.reshape(d_a * d_b, d_a * d_b))


def dephase_both(rho: np.ndarray, dims: List[int]) -> np.ndarray:
    return dephase_subsystem(dephase_subsystem(rho, dims, 0), dims, 1)


def relative_entropy(rho: np.ndarray, sigma: np.ndarray) -> float:
    d = rho.shape[0]
    rho_reg = ensure_density((1.0 - 1e-10) * rho + 1e-10 * np.eye(d, dtype=complex) / d)
    sigma_reg = ensure_density((1.0 - 1e-10) * sigma + 1e-10 * np.eye(d, dtype=complex) / d)
    log_rho = la.logm(rho_reg)
    log_sigma = la.logm(sigma_reg)
    val = np.trace(rho_reg @ (log_rho - log_sigma))
    return float(np.real_if_close(val))


def local_replace_A(rho: np.ndarray, dims: List[int], eps: float) -> np.ndarray:
    d_a, d_b = dims
    rho_b = partial_trace(rho, dims, [1])
    maximally_mixed_a = np.eye(d_a, dtype=complex) / d_a
    replaced = np.kron(maximally_mixed_a, rho_b)
    return ensure_density((1.0 - eps) * rho + eps * replaced)


def local_replace_B(rho: np.ndarray, dims: List[int], eps: float) -> np.ndarray:
    d_a, d_b = dims
    rho_a = partial_trace(rho, dims, [0])
    maximally_mixed_b = np.eye(d_b, dtype=complex) / d_b
    replaced = np.kron(rho_a, maximally_mixed_b)
    return ensure_density((1.0 - eps) * rho + eps * replaced)


def perturb_depolarize_both(rho: np.ndarray, dims: List[int], eps: float) -> np.ndarray:
    return local_replace_B(local_replace_A(rho, dims, eps), dims, eps)


def perturb_dephase_both(rho: np.ndarray, dims: List[int], eps: float) -> np.ndarray:
    dephased = dephase_both(rho, dims)
    return ensure_density((1.0 - eps) * rho + eps * dephased)


PERTURBATIONS: Dict[str, Callable[[np.ndarray, List[int], float], np.ndarray]] = {
    "depolarize_both": perturb_depolarize_both,
    "dephase_both": perturb_dephase_both,
}


def metric_suite(rho: np.ndarray, dims: List[int]) -> Dict[str, float]:
    rho_prod = product_reference(rho, dims)
    rho_deph = dephase_both(rho, dims)
    return {
        "I_AB": mutual_information(rho, dims),
        "S_A_given_B": conditional_entropy(rho, dims),
        "I_c_A_to_B": coherent_information(rho, dims),
        "D_to_product": relative_entropy(rho, rho_prod),
        "D_to_dephased": relative_entropy(rho, rho_deph),
    }


def summarize(values: List[float]) -> Dict[str, float]:
    arr = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def family_diversity(values: List[float]) -> Dict[str, float]:
    clipped = np.maximum(np.asarray(values, dtype=float), 0.0)
    total = float(np.sum(clipped))
    if total < EPS:
        return {"entropy": 0.0, "effective_number": 0.0, "variance": 0.0}
    probs = clipped / total
    probs = probs[probs > EPS]
    H = float(-np.sum(probs * np.log(probs)))
    return {
        "entropy": H,
        "effective_number": float(np.exp(H)),
        "variance": float(np.var(clipped)),
    }


def response_derivative(metric_name: str, rho: np.ndarray, dims: List[int], perturb_name: str, eps: float = DELTA) -> float:
    base = metric_suite(rho, dims)[metric_name]
    perturbed = PERTURBATIONS[perturb_name](rho, dims, eps)
    trial = metric_suite(perturbed, dims)[metric_name]
    return float((trial - base) / eps)


def run_guardrail_final_state(order: List[str], eta: float, loop_type: str, mode: str, n_substeps: int = 16) -> np.ndarray:
    phi0 = 0.0
    chi0 = 0.0
    q0 = guardrail.q_on_loop(phi0, chi0, eta, 0.0, loop_type)
    rho_ab = np.kron(guardrail.left_density(q0), guardrail.right_density(q0))
    total_steps = len(order) * n_substeps
    for stage_idx, terrain in enumerate(order):
        for sub_idx in range(n_substeps):
            global_idx = stage_idx * n_substeps + sub_idx + 1
            u = 2.0 * np.pi * global_idx / total_steps
            q = guardrail.q_on_loop(phi0, chi0, eta, u, loop_type)
            kraus_L, kraus_R = guardrail.terrain_kraus_pair(terrain, q)
            rho_ab = guardrail.apply_local_channel(rho_ab, kraus_L, kraus_R)
            if mode == "coupled_control":
                U = guardrail.coupling_unitary(eta, loop_type, terrain)
                rho_ab = guardrail.ensure_valid(U @ rho_ab @ U.conj().T)
    return ensure_density(rho_ab)


def collect_lr_family(mode: str) -> List[Dict[str, object]]:
    states = []
    for torus_label, eta in TORUS_CONFIGS:
        for loop_type in ("fiber", "base"):
            for order in (guardrail.DED_ORDER, guardrail.IND_ORDER):
                rho = run_guardrail_final_state(order, eta, loop_type, mode)
                trace_rec = guardrail.run_cycle(order, eta, loop_type, mode)
                states.append({
                    "rho": rho,
                    "dims": [2, 2],
                    "meta": {
                        "bridge": mode,
                        "torus": torus_label,
                        "eta": float(eta),
                        "loop_type": loop_type,
                        "order_name": "DED" if order == guardrail.DED_ORDER else "IND",
                        "MI_max_trace": float(trace_rec["MI_max"]),
                        "MI_final_trace": float(trace_rec["MI_final"]),
                        "CI_final_trace": float(trace_rec["CI_final"]),
                    },
                })
    return states


def collect_xi_shell_family() -> List[Dict[str, object]]:
    states = []
    u_grid = np.linspace(0.0, 2.0 * np.pi, U_SAMPLES, endpoint=False)
    for torus_label, eta in TORUS_CONFIGS:
        for loop_label, q_fn in (("fiber", bakeoff.exact_fiber_q), ("base", bakeoff.exact_base_q)):
            for u in u_grid:
                q = q_fn(eta, float(u))
                rho, dims, meta = bakeoff.xi_shell_from_q(q)
                states.append({
                    "rho": rho,
                    "dims": dims,
                    "meta": {
                        "bridge": "Xi_shell",
                        "torus": torus_label,
                        "eta": float(eta),
                        "loop_type": loop_label,
                        "u": float(u),
                        **meta,
                    },
                })
    return states


def collect_xi_hist_families() -> Dict[str, List[Dict[str, object]]]:
    outer_states = []
    cycle_states = []
    control_states = []
    for engine_type in (1, 2):
        n_macro = len(bakeoff.LOOP_STAGE_ORDER[engine_type])
        half_idx = n_macro // 2
        full_idx = n_macro
        for torus_label, eta in TORUS_CONFIGS:
            _, snapshots = bakeoff.capture_engine_macrostates(engine_type, eta, n_cycles=1)
            rho_outer, dims_outer, meta_outer = bakeoff.xi_hist_from_states(snapshots[0], snapshots[half_idx])
            rho_cycle, dims_cycle, meta_cycle = bakeoff.xi_hist_from_states(snapshots[0], snapshots[full_idx])
            rho_ctl, dims_ctl, meta_ctl = bakeoff.xi_lr_control_from_state(snapshots[-1])
            common = {
                "engine_type": engine_type,
                "torus": torus_label,
                "eta": float(eta),
            }
            outer_states.append({"rho": rho_outer, "dims": dims_outer, "meta": {"bridge": "Xi_hist_outer", **common, **meta_outer}})
            cycle_states.append({"rho": rho_cycle, "dims": dims_cycle, "meta": {"bridge": "Xi_hist_cycle", **common, **meta_cycle}})
            control_states.append({"rho": rho_ctl, "dims": dims_ctl, "meta": {"bridge": "Xi_LR_control", **common, **meta_ctl}})
    return {
        "Xi_hist_outer": outer_states,
        "Xi_hist_cycle": cycle_states,
        "Xi_LR_control": control_states,
    }


def group_metric_means_by_key(states: List[Dict[str, object]], metric_name: str, key: str) -> Dict[str, float]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    for row in states:
        grouped[str(row["meta"].get(key, "NA"))].append(row["metrics"][metric_name])
    return {k: float(np.mean(v)) for k, v in grouped.items()}


def analyze_family(name: str, states: List[Dict[str, object]]) -> Dict[str, object]:
    enriched = []
    for row in states:
        rho = row["rho"]
        dims = row["dims"]
        metrics = metric_suite(rho, dims)
        responses = {
            pert: {
                metric: response_derivative(metric, rho, dims, pert)
                for metric in ("I_AB", "I_c_A_to_B", "D_to_dephased")
            }
            for pert in PERTURBATIONS
        }
        enriched.append({**row, "metrics": metrics, "responses": responses})

    mi_vals = [row["metrics"]["I_AB"] for row in enriched]
    ic_vals = [row["metrics"]["I_c_A_to_B"] for row in enriched]
    s_vals = [row["metrics"]["S_A_given_B"] for row in enriched]
    d_deph = [row["metrics"]["D_to_dephased"] for row in enriched]
    diversity_base = family_diversity(mi_vals)
    perturb_family = {}
    for pert in PERTURBATIONS:
        pert_mi_vals = []
        for row in enriched:
            rho_p = PERTURBATIONS[pert](row["rho"], row["dims"], DELTA)
            pert_mi_vals.append(metric_suite(rho_p, row["dims"])["I_AB"])
        pert_div = family_diversity(pert_mi_vals)
        perturb_family[pert] = {
            "mean_dI": float(np.mean([row["responses"][pert]["I_AB"] for row in enriched])),
            "mean_dIc": float(np.mean([row["responses"][pert]["I_c_A_to_B"] for row in enriched])),
            "mean_dDdeph": float(np.mean([row["responses"][pert]["D_to_dephased"] for row in enriched])),
            "diversity_delta": float((pert_div["effective_number"] - diversity_base["effective_number"]) / DELTA),
            "variance_delta": float((pert_div["variance"] - diversity_base["variance"]) / DELTA),
        }

    eta_means = group_metric_means_by_key(enriched, "I_c_A_to_B", "torus")
    loop_means = group_metric_means_by_key(enriched, "I_c_A_to_B", "loop_type")
    eta_range = float(max(eta_means.values()) - min(eta_means.values())) if eta_means else 0.0
    loop_range = float(max(loop_means.values()) - min(loop_means.values())) if loop_means else 0.0
    mean_abs_ic = float(np.mean(np.abs(ic_vals)))
    trace_mi_max_vals = [float(row["meta"].get("MI_max_trace", row["metrics"]["I_AB"])) for row in enriched]
    trace_mi_max_mean = float(np.mean(trace_mi_max_vals))

    verdict = {
        "trivial": bool(np.mean(np.abs(mi_vals)) < 1e-6 and trace_mi_max_mean < 1e-6),
        "eta_sensitive": bool(eta_range > 1e-3),
        "loop_sensitive": bool(loop_range > 1e-3),
        "ic_saturated": bool(np.mean(np.abs(mi_vals)) > 0.5 and mean_abs_ic > 0.95 and np.std(ic_vals) < 1e-2),
        "control_only": bool(name == "L|R_coupled_control"),
    }

    return {
        "name": name,
        "count": len(enriched),
        "dims": enriched[0]["dims"] if enriched else [],
        "base_metrics": {
            "I_AB": summarize(mi_vals),
            "I_c_A_to_B": summarize(ic_vals),
            "S_A_given_B": summarize(s_vals),
            "D_to_dephased": summarize(d_deph),
        },
        "cut_family": {
            "MI_diversity_entropy": diversity_base["entropy"],
            "MI_effective_number": diversity_base["effective_number"],
            "MI_variance": diversity_base["variance"],
        },
        "perturbation_response": perturb_family,
        "group_means": {
            "torus_Ic_means": eta_means,
            "loop_Ic_means": loop_means,
        },
        "trace": {
            "MI_max_mean": trace_mi_max_mean,
            "MI_max_max": float(np.max(trace_mi_max_vals)),
        },
        "verdict": verdict,
    }


def main() -> int:
    print("=" * 76)
    print("AXIS 0 FULL SPECTRUM SIM")
    print("=" * 76)
    print("Running real-geometry baselines plus Xi bridge families across multiple kernels")

    families = {
        "L|R_local_only": collect_lr_family("local_only"),
        "L|R_coupled_control": collect_lr_family("coupled_control"),
        "Xi_shell": collect_xi_shell_family(),
        **collect_xi_hist_families(),
    }

    results = {name: analyze_family(name, states) for name, states in families.items()}

    ranked_keep = []
    ranked_kill = []
    ranked_control = []
    for name, result in results.items():
        verdict = result["verdict"]
        if verdict["control_only"]:
            ranked_control.append(name)
        elif verdict["trivial"] or verdict["ic_saturated"]:
            ranked_kill.append(name)
        else:
            ranked_keep.append(name)

    payload = {
        "schema": "AXIS0_FULL_SPECTRUM_V1",
        "timestamp": datetime.now(UTC).isoformat(),
        "delta": DELTA,
        "families": results,
        "summary": {
            "ranked_keep": ranked_keep,
            "ranked_kill": ranked_kill,
            "ranked_control": ranked_control,
            "notes": [
                "L|R_local_only is the honest full-geometry baseline.",
                "L|R_coupled_control is a noncanon positive control.",
                "Xi families are bridge candidates, not raw L|R cuts.",
            ],
        },
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis0_full_spectrum_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("\nFamily summary:")
    print(f"{'family':>22s} {'mean_MI':>10s} {'MImax':>10s} {'mean_Ic':>10s} {'eta_rng':>10s} {'loop_rng':>10s} {'trivial':>8s} {'sat':>6s}")
    print("-" * 92)
    for name, result in results.items():
        print(
            f"{name:>22s} "
            f"{result['base_metrics']['I_AB']['mean']:>10.6f} "
            f"{result['trace']['MI_max_mean']:>10.6f} "
            f"{result['base_metrics']['I_c_A_to_B']['mean']:>10.6f} "
            f"{(max(result['group_means']['torus_Ic_means'].values()) - min(result['group_means']['torus_Ic_means'].values()) if result['group_means']['torus_Ic_means'] else 0.0):>10.6f} "
            f"{(max(result['group_means']['loop_Ic_means'].values()) - min(result['group_means']['loop_Ic_means'].values()) if result['group_means']['loop_Ic_means'] else 0.0):>10.6f} "
            f"{str(result['verdict']['trivial']):>8s} "
            f"{str(result['verdict']['ic_saturated']):>6s}"
        )

    print("\nKeep candidates:", ", ".join(ranked_keep) if ranked_keep else "(none)")
    print("Kill candidates:", ", ".join(ranked_kill) if ranked_kill else "(none)")
    print("Control-only:", ", ".join(ranked_control) if ranked_control else "(none)")
    print(f"\nResults written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
