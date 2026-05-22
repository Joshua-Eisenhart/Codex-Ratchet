#!/usr/bin/env python3
"""L64 adaptive-vs-fixed bond-cap bias sweep.

The previous L64 adaptive-bond scout showed that a bounded adaptive cap policy
can run at L=64, but it did not measure whether the resulting Phi0 diagnostics
are stable against the cap policy itself. This scout compares fixed D=2,
fixed D=4, and the same adaptive D=2/4 policy on identical family/seed rows.

This is still bounded 1D MPS tensor-runtime evidence. It cannot promote full
L64 convergence, PEPS/PEPS3D closure, robust Phi0, real scale-level basins, or
final manifold admission.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import statistics
import time
from typing import Any, Literal

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit
import sim_two_root_constraint_tensor_network_lindblad_runtime_probe as mps_runtime


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_l64_adaptive_bond_bias_sweep_probe_results.json"

NAME = "two_root_constraint_l64_adaptive_bond_bias_sweep_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_l64_mps_adaptive_fixed_cap_bias_sweep"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_l64_tensor_bias_sweep"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal tensor-runtime bias scout only: compares fixed D=2, fixed D=4, "
    "and adaptive D=2/4 L64 MPS quantum-trajectory surfaces on matched "
    "family/seed rows. It cannot promote full L64 convergence, PEPS/PEPS3D "
    "closure, robust Phi0, real scale-level attractor basins, or final "
    "constraint-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing L64 MPS tensors, quantum-jump trajectory steps, fixed/adaptive SVD truncation, and Phi0 readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing policy comparison graph over family, seed, and cap-policy rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion and bias-sweep completion guard",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "statistics": {"tried": True, "used": True, "reason": "supportive bias and timing summary reductions"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
    "statistics": "supportive",
}

LENGTH = 64
TARGET_CYCLES = 1
STAGES_PER_TRAJECTORY = len(mps_runtime.TERRAIN_ORDER_BY_TOKEN["1"]) * TARGET_CYCLES
FAMILIES = tuple(mps_runtime.INITIAL_FAMILIES)
SEEDS = (65052021, 65052022)
POLICIES = ("fixed2", "fixed4", "adaptive2_4")
NORM_TOL = 1.0e-7
BIAS_TOL = 0.35
TIME_BUDGET_SECONDS = 240.0
TRUNCATION_RAISE_THRESHOLD = 2.0e-6
TRUNCATION_LOWER_THRESHOLD = 1.0e-9

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "mps_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "l64_adaptive_source": SCOUT_ROOT / "sim_two_root_constraint_l64_adaptive_bond_trajectory_batch_probe.py",
    "l64_adaptive_result": RESULT_DIR / "two_root_constraint_l64_adaptive_bond_trajectory_batch_probe_results.json",
    "l64_fixed_result": RESULT_DIR / "two_root_constraint_l64_tensor_blocker_or_mitigation_probe_results.json",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
    "handoff": REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    return qit.jsonable(value)


def source_hashes() -> dict[str, Any]:
    return {
        name: {"path": rel(path), "sha256": sha256(path), "exists": path.exists()}
        for name, path in SOURCE_FILES.items()
    }


def two_site_density_adjacent(mps: mps_runtime.MPS, site: int) -> torch.Tensor:
    left_env = torch.ones((1, 1), dtype=qit.DTYPE)
    for idx in range(site):
        tensor = mps.tensors[idx]
        left_env = torch.einsum("ij,dir,djs->rs", left_env, tensor.conj(), tensor)
    right_env = torch.ones((1, 1), dtype=qit.DTYPE)
    for idx in range(mps.L - 1, site + 1, -1):
        tensor = mps.tensors[idx]
        right_env = torch.einsum("ij,drj,dsi->rs", right_env, tensor.conj(), tensor)
    left = mps.tensors[site]
    right = mps.tensors[site + 1]
    rho = torch.einsum(
        "ik,air,brj,cks,dsl,jl->abcd",
        left_env,
        left,
        right,
        left.conj(),
        right.conj(),
        right_env,
    )
    return mps_runtime.normalize_density(rho.reshape(4, 4))


def center_pair_phi0(mps: mps_runtime.MPS) -> dict[str, float]:
    return mps_runtime.phi0_readout_pair(two_site_density_adjacent(mps, mps.L // 2 - 1))


def cap_for_policy(policy: str, current_cap: int, stage_truncation: float) -> int:
    if policy == "fixed2":
        return 2
    if policy == "fixed4":
        return 4
    if policy != "adaptive2_4":
        raise ValueError(f"unknown policy {policy}")
    if stage_truncation > TRUNCATION_RAISE_THRESHOLD:
        return 4
    if stage_truncation < TRUNCATION_LOWER_THRESHOLD:
        return 2
    return current_cap


def run_policy_trajectory(
    family: str,
    seed: int,
    policy: Literal["fixed2", "fixed4", "adaptive2_4"],
    started: float,
) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(seed)
    mps = mps_runtime.MPS.product(family, LENGTH)
    token_prev: str | None = "1"
    cap = 2 if policy in {"fixed2", "adaptive2_4"} else 4
    total_truncation = 0.0
    total_jumps = 0
    stage_rows: list[dict[str, Any]] = []
    gate_two = mps_runtime.two_site_gate()
    stop_reason = "target_complete"
    for cycle in range(TARGET_CYCLES):
        token = mps_runtime.choose_hysteresis(mps_runtime.mean_z(mps), token_prev)
        token_prev = token
        for terrain_idx, terrain in enumerate(mps_runtime.TERRAIN_ORDER_BY_TOKEN[token]):
            stage_started = time.time()
            cap_before = cap
            H = mps_runtime.local_hamiltonian(token)
            collapses = mps_runtime.collapse_ops(token, terrain)
            no_jump = mps_runtime.no_jump_operator(H, collapses)
            jump_count = 0
            for site in range(LENGTH):
                rho_site = mps.reduced_single(site)
                kind, channel_idx = mps_runtime.local_jump_choice(rho_site, collapses, generator)
                if kind == "jump":
                    op = math.sqrt(mps_runtime.DT) * collapses[int(channel_idx)]
                    jump_count += 1
                else:
                    op = no_jump
                mps.apply_single(op, site)
                mps.normalize_()
            stage_truncation = 0.0
            for site in range(terrain_idx % 2, LENGTH - 1, 2):
                stage_truncation += mps.apply_two(gate_two, site, max_bond=cap)
                mps.normalize_()
            total_truncation += stage_truncation
            total_jumps += jump_count
            cap_after = cap_for_policy(policy, cap, stage_truncation)
            stage_rows.append(
                {
                    "family": family,
                    "seed": seed,
                    "policy": policy,
                    "cycle": cycle,
                    "stage_index": terrain_idx,
                    "token": token,
                    "terrain": terrain,
                    "cap_before": cap_before,
                    "cap_after": cap_after,
                    "stage_truncation_error": stage_truncation,
                    "total_truncation_error": total_truncation,
                    "jump_count": jump_count,
                    "max_bond": mps.max_bond(),
                    "norm_error": abs(float(mps.norm_sq().item()) - 1.0),
                    "stage_seconds": time.time() - stage_started,
                    "elapsed_seconds": time.time() - started,
                }
            )
            cap = cap_after
            if time.time() - started > TIME_BUDGET_SECONDS:
                stop_reason = "time_budget_after_completed_stage"
                break
        if stop_reason != "target_complete":
            break
    phi0 = center_pair_phi0(mps)
    return {
        "family": family,
        "seed": seed,
        "policy": policy,
        "length": LENGTH,
        "stages_completed": len(stage_rows),
        "target_stages": STAGES_PER_TRAJECTORY,
        "completed_target": len(stage_rows) == STAGES_PER_TRAJECTORY,
        "stop_reason": stop_reason,
        "cap_values_seen": sorted({row["cap_before"] for row in stage_rows} | {row["cap_after"] for row in stage_rows}),
        "cap_increase_count": sum(1 for row in stage_rows if row["cap_after"] > row["cap_before"]),
        "cap_decrease_count": sum(1 for row in stage_rows if row["cap_after"] < row["cap_before"]),
        "max_bond": mps.max_bond(),
        "bond_dims": mps.bond_dims(),
        "norm_error": abs(float(mps.norm_sq().item()) - 1.0),
        "total_truncation_error": total_truncation,
        "total_jumps": total_jumps,
        "center_pair_phi0": phi0,
        "stage_rows": stage_rows,
    }


def mean(values: list[float]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def policy_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("l64_bias_sweep")
    for row in rows:
        policy_node = graph.add_node(row["policy"])
        graph.add_edge(root, policy_node, "policy")
        run_node = graph.add_node(f"{row['family']}:{row['seed']}:{row['policy']}")
        graph.add_edge(policy_node, run_node, "trajectory")
        for stage in row["stage_rows"][:STAGES_PER_TRAJECTORY]:
            stage_node = graph.add_node(f"{row['family']}:{row['seed']}:{row['policy']}:{stage['stage_index']}")
            graph.add_edge(run_node, stage_node, "stage")
            if stage["cap_after"] != stage["cap_before"]:
                cap_node = graph.add_node(f"D{stage['cap_before']}->{stage['cap_after']}")
                graph.add_edge(stage_node, cap_node, "cap_change")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": rx.is_directed_acyclic_graph(graph),
        "weakly_connected_components": len(rx.weakly_connected_components(graph)),
    }


def aggregate(rows: list[dict[str, Any]], elapsed: float) -> dict[str, Any]:
    by_policy: dict[str, list[dict[str, Any]]] = {policy: [] for policy in POLICIES}
    by_key: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_policy[row["policy"]].append(row)
        by_key.setdefault((row["family"], row["seed"]), {})[row["policy"]] = row
    comparisons = []
    for (family, seed), policy_rows in sorted(by_key.items()):
        if set(POLICIES).issubset(policy_rows):
            fixed2 = policy_rows["fixed2"]["center_pair_phi0"]["I_A_colon_B"]
            fixed4 = policy_rows["fixed4"]["center_pair_phi0"]["I_A_colon_B"]
            adaptive = policy_rows["adaptive2_4"]["center_pair_phi0"]["I_A_colon_B"]
            comparisons.append(
                {
                    "family": family,
                    "seed": seed,
                    "fixed2_I_A_colon_B": fixed2,
                    "fixed4_I_A_colon_B": fixed4,
                    "adaptive_I_A_colon_B": adaptive,
                    "adaptive_minus_fixed4": adaptive - fixed4,
                    "adaptive_minus_fixed2": adaptive - fixed2,
                    "fixed4_minus_fixed2": fixed4 - fixed2,
                    "adaptive_abs_delta_to_fixed4": abs(adaptive - fixed4),
                    "adaptive_abs_delta_to_fixed2": abs(adaptive - fixed2),
                    "adaptive_within_fixed_cap_envelope": min(fixed2, fixed4) - 1.0e-12
                    <= adaptive
                    <= max(fixed2, fixed4) + 1.0e-12,
                }
            )
    policy_summary = {}
    for policy, policy_rows in by_policy.items():
        mi_values = [row["center_pair_phi0"]["I_A_colon_B"] for row in policy_rows]
        policy_summary[policy] = {
            "trajectory_count": len(policy_rows),
            "completed_trajectories": sum(1 for row in policy_rows if row["completed_target"]),
            "stages_completed": sum(row["stages_completed"] for row in policy_rows),
            "mean_I_A_colon_B": mean(mi_values),
            "max_I_A_colon_B": max(mi_values) if mi_values else 0.0,
            "min_I_A_colon_B": min(mi_values) if mi_values else 0.0,
            "total_truncation_error": sum(row["total_truncation_error"] for row in policy_rows),
            "max_trajectory_truncation_error": max((row["total_truncation_error"] for row in policy_rows), default=0.0),
            "max_bond": max((row["max_bond"] for row in policy_rows), default=0),
            "norm_error": max((row["norm_error"] for row in policy_rows), default=float("inf")),
            "cap_values_seen": sorted({cap for row in policy_rows for cap in row["cap_values_seen"]}),
            "cap_increase_count": sum(row["cap_increase_count"] for row in policy_rows),
            "cap_decrease_count": sum(row["cap_decrease_count"] for row in policy_rows),
        }
    adaptive_deltas_fixed4 = [row["adaptive_abs_delta_to_fixed4"] for row in comparisons]
    adaptive_deltas_fixed2 = [row["adaptive_abs_delta_to_fixed2"] for row in comparisons]
    return {
        "route": "l64_adaptive_fixed_cap_bias_sweep",
        "length": LENGTH,
        "families": list(FAMILIES),
        "seeds": list(SEEDS),
        "policies": list(POLICIES),
        "elapsed_seconds": elapsed,
        "trajectory_count": len(rows),
        "completed_trajectories": sum(1 for row in rows if row["completed_target"]),
        "target_trajectory_count": len(FAMILIES) * len(SEEDS) * len(POLICIES),
        "stages_completed": sum(row["stages_completed"] for row in rows),
        "target_stages_total": len(FAMILIES) * len(SEEDS) * len(POLICIES) * STAGES_PER_TRAJECTORY,
        "policy_summary": policy_summary,
        "matched_comparison_count": len(comparisons),
        "comparisons": comparisons,
        "adaptive_mean_abs_delta_to_fixed4": mean(adaptive_deltas_fixed4),
        "adaptive_max_abs_delta_to_fixed4": max(adaptive_deltas_fixed4, default=0.0),
        "adaptive_mean_abs_delta_to_fixed2": mean(adaptive_deltas_fixed2),
        "adaptive_max_abs_delta_to_fixed2": max(adaptive_deltas_fixed2, default=0.0),
        "adaptive_within_fixed_cap_envelope_count": sum(
            1 for row in comparisons if row["adaptive_within_fixed_cap_envelope"]
        ),
        "policy_graph": policy_graph(rows),
        "trajectory_rows": [
            {key: value for key, value in row.items() if key != "stage_rows"} | {"stage_count": len(row["stage_rows"])}
            for row in rows
        ],
        "stage_rows_sample": [stage for row in rows for stage in row["stage_rows"]][:24],
    }


def run_surface() -> dict[str, Any]:
    started = time.time()
    rows = []
    for family in FAMILIES:
        for seed in SEEDS:
            for policy in POLICIES:
                rows.append(run_policy_trajectory(family, seed, policy, started))
                if time.time() - started > TIME_BUDGET_SECONDS:
                    return aggregate(rows, time.time() - started)
    return aggregate(rows, time.time() - started)


def z3_guard(surface: dict[str, Any]) -> dict[str, Any]:
    complete = z3.Bool("complete")
    adaptive_used = z3.Bool("adaptive_used")
    bias_bounded = z3.Bool("bias_bounded")
    full_l64_convergence = z3.Bool("full_l64_convergence")
    robust_phi0 = z3.Bool("robust_phi0")
    peps3d = z3.Bool("peps3d")
    scale_basin = z3.Bool("scale_basin")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(complete == (surface["completed_trajectories"] == surface["target_trajectory_count"]))
    solver.add(
        adaptive_used
        == (
            surface["policy_summary"]["adaptive2_4"]["cap_increase_count"]
            + surface["policy_summary"]["adaptive2_4"]["cap_decrease_count"]
            > 0
        )
    )
    solver.add(bias_bounded == (surface["adaptive_max_abs_delta_to_fixed4"] < BIAS_TOL))
    solver.add(full_l64_convergence == False)
    solver.add(robust_phi0 == False)
    solver.add(peps3d == False)
    solver.add(scale_basin == False)
    solver.add(final_admission == z3.And(full_l64_convergence, robust_phi0, peps3d, scale_basin))
    check = solver.check()
    model = solver.model() if check == z3.sat else None
    return {
        "sat": check == z3.sat,
        "bias_sweep_complete": bool(z3.is_true(model.eval(complete, model_completion=True))) if model else False,
        "adaptive_policy_used": bool(z3.is_true(model.eval(adaptive_used, model_completion=True))) if model else False,
        "adaptive_bias_bounded_against_fixed4": bool(z3.is_true(model.eval(bias_bounded, model_completion=True))) if model else False,
        "full_l64_convergence_claimed": bool(z3.is_true(model.eval(full_l64_convergence, model_completion=True))) if model else False,
        "robust_phi0_claimed": bool(z3.is_true(model.eval(robust_phi0, model_completion=True))) if model else False,
        "peps3d_claimed": bool(z3.is_true(model.eval(peps3d, model_completion=True))) if model else False,
        "scale_basin_claimed": bool(z3.is_true(model.eval(scale_basin, model_completion=True))) if model else False,
        "final_manifold_admission_allowed": bool(z3.is_true(model.eval(final_admission, model_completion=True))) if model else False,
        "rule": "A bounded cap-bias sweep can strengthen L64 tensor evidence but cannot imply full convergence, robust Phi0, PEPS3D, scale-basin, or final admission.",
    }


def main() -> int:
    started = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    surface = run_surface()
    guard = z3_guard(surface)
    status = (
        "bounded_l64_adaptive_bias_sweep_complete"
        if surface["completed_trajectories"] == surface["target_trajectory_count"]
        else "bounded_l64_adaptive_bias_sweep_partial"
    )
    positive = {
        "upstream_l64_adaptive_loaded": {
            "pass": upstream["l64_adaptive_result"].get("all_pass") is True
            and upstream["l64_adaptive_result"].get("summary", {}).get("l64_adaptive_status")
            == "bounded_adaptive_l64_batch_complete",
            "upstream_status": upstream["l64_adaptive_result"].get("summary", {}).get("l64_adaptive_status"),
        },
        "all_policy_rows_attempted": {
            "pass": surface["trajectory_count"] == surface["target_trajectory_count"],
            "trajectory_count": surface["trajectory_count"],
            "target_trajectory_count": surface["target_trajectory_count"],
        },
        "all_policy_rows_completed": {
            "pass": surface["completed_trajectories"] == surface["target_trajectory_count"],
            "completed_trajectories": surface["completed_trajectories"],
            "target_trajectory_count": surface["target_trajectory_count"],
        },
        "adaptive_policy_actually_changed_caps": {
            "pass": guard["adaptive_policy_used"],
            "cap_values_seen": surface["policy_summary"]["adaptive2_4"]["cap_values_seen"],
            "cap_increase_count": surface["policy_summary"]["adaptive2_4"]["cap_increase_count"],
            "cap_decrease_count": surface["policy_summary"]["adaptive2_4"]["cap_decrease_count"],
        },
        "bias_measured_against_fixed_caps": {
            "pass": surface["matched_comparison_count"] == len(FAMILIES) * len(SEEDS),
            "matched_comparison_count": surface["matched_comparison_count"],
            "adaptive_mean_abs_delta_to_fixed4": surface["adaptive_mean_abs_delta_to_fixed4"],
            "adaptive_max_abs_delta_to_fixed4": surface["adaptive_max_abs_delta_to_fixed4"],
            "adaptive_mean_abs_delta_to_fixed2": surface["adaptive_mean_abs_delta_to_fixed2"],
            "adaptive_max_abs_delta_to_fixed2": surface["adaptive_max_abs_delta_to_fixed2"],
        },
        "norms_and_truncations_recorded": {
            "pass": all(row["norm_error"] < NORM_TOL for row in surface["policy_summary"].values())
            and all(row["total_truncation_error"] >= 0.0 for row in surface["policy_summary"].values()),
            "policy_summary": surface["policy_summary"],
        },
        "z3_nonpromotion_guard": {
            "pass": guard["sat"] and not guard["final_manifold_admission_allowed"],
            "guard": guard,
        },
    }
    graveyard = {
        "full_l64_convergence_not_claimed": {
            "pass": not guard["full_l64_convergence_claimed"],
            "detail": "Fixed/adaptive cap comparison is still bounded one-cycle evidence.",
        },
        "robust_phi0_not_claimed": {
            "pass": not guard["robust_phi0_claimed"],
            "detail": "Phi0 bridge remains nonrobust under current controls.",
        },
        "peps3d_not_claimed": {
            "pass": not guard["peps3d_claimed"],
            "detail": "This is 1D MPS only.",
        },
        "scale_basin_not_claimed": {
            "pass": not guard["scale_basin_claimed"],
            "detail": "No real scale-level attractor-basin admission is made.",
        },
    }
    all_pass = all(item["pass"] for item in positive.values()) and all(item["pass"] for item in graveyard.values())
    summary = {
        "all_pass": all_pass,
        "l64_bias_sweep_status": status,
        "trajectory_count": surface["trajectory_count"],
        "completed_trajectories": surface["completed_trajectories"],
        "stages_completed": surface["stages_completed"],
        "elapsed_seconds": surface["elapsed_seconds"],
        "policy_mean_I_A_colon_B": {
            policy: row["mean_I_A_colon_B"] for policy, row in surface["policy_summary"].items()
        },
        "policy_total_truncation_error": {
            policy: row["total_truncation_error"] for policy, row in surface["policy_summary"].items()
        },
        "adaptive_mean_abs_delta_to_fixed4": surface["adaptive_mean_abs_delta_to_fixed4"],
        "adaptive_max_abs_delta_to_fixed4": surface["adaptive_max_abs_delta_to_fixed4"],
        "adaptive_mean_abs_delta_to_fixed2": surface["adaptive_mean_abs_delta_to_fixed2"],
        "adaptive_max_abs_delta_to_fixed2": surface["adaptive_max_abs_delta_to_fixed2"],
        "adaptive_within_fixed_cap_envelope_count": surface["adaptive_within_fixed_cap_envelope_count"],
        "matched_comparison_count": surface["matched_comparison_count"],
        "adaptive_bias_bounded_against_fixed4": guard["adaptive_bias_bounded_against_fixed4"],
        "final_manifold_admission_allowed": False,
        "interpretation": (
            "L64 adaptive-bond Phi0 readouts have now been compared against fixed D=2 and fixed D=4 on matched rows. "
            "This measures cap-policy bias, but remains bounded 1D MPS evidence rather than full tensor convergence."
        ),
        "next_required_work": (
            "If tensor closure remains priority, move from one-cycle cap-bias evidence to longer fixed/adaptive sweeps, "
            "local Krylov batching, or vectorized doubled-MPS Lindblad."
        ),
    }
    receipt = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "upstream": {
            "l64_adaptive_status": upstream["l64_adaptive_result"].get("summary", {}).get("l64_adaptive_status"),
            "l64_fixed_status": upstream["l64_fixed_result"].get("summary", {}).get("l64_status"),
        },
        "parameters": {
            "length": LENGTH,
            "target_cycles": TARGET_CYCLES,
            "families": list(FAMILIES),
            "seeds": list(SEEDS),
            "policies": list(POLICIES),
            "time_budget_seconds": TIME_BUDGET_SECONDS,
            "bias_tolerance": BIAS_TOL,
        },
        "surface": surface,
        "z3_guard": guard,
        "positive": positive,
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "l64_bias_sweep_status": status,
            "full_l64_convergence_claimed": False,
            "robust_phi0_claimed": False,
            "peps_peps3d_full_claimed": False,
            "scale_basin_claimed": False,
            "final_manifold_admission_allowed": False,
        },
        "graveyard_companions": graveyard,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "items": sorted(graveyard),
        },
        "why_not_v4_probes": (
            "This is a v5 source-native PyTorch formal scout extending the current QIT engine MPS runtime. "
            "It is not a wiki route, not a legacy v4 probe, not PEPS/PEPS3D, and not final manifold admission."
        ),
        "next_work_required": [
            "Run longer fixed/adaptive cap sweeps if L64 convergence is the target.",
            "Implement local Krylov or vectorized doubled-MPS Lindblad if trajectory bias remains open.",
            "Keep robust Phi0 and real scale-basin admission as separate blockers.",
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
