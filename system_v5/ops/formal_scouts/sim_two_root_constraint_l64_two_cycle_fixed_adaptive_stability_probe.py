#!/usr/bin/env python3
"""L64 two-cycle fixed-vs-adaptive MPS stability scout.

The previous L64 cap-bias sweep compared fixed D=2, fixed D=4, and adaptive
D=2/4 for one cycle. This scout extends the tensor route one rung further: it
runs two full L64 terrain cycles for fixed D=4 and adaptive D=2/4 on matched
family/seed rows, then compares center-pair Phi0 readouts and truncation.

This is still bounded 1D MPS tensor-runtime evidence. It cannot promote full
L64 convergence, PEPS/PEPS3D closure, robust Phi0, real scale-level basins, or
final manifold admission.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import statistics
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit
import sim_two_root_constraint_l64_adaptive_bond_bias_sweep_probe as cap_bias
import sim_two_root_constraint_tensor_network_lindblad_runtime_probe as mps_runtime


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_l64_two_cycle_fixed_adaptive_stability_probe_results.json"

NAME = "two_root_constraint_l64_two_cycle_fixed_adaptive_stability_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_l64_two_cycle_fixed_adaptive_mps_stability"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_l64_two_cycle_tensor_stability"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal tensor-runtime stability scout only: runs two-cycle L64 MPS "
    "quantum trajectories comparing fixed D=4 and adaptive D=2/4 policies on "
    "matched family/seed rows. It cannot promote full L64 convergence, "
    "PEPS/PEPS3D closure, robust Phi0, real scale-level attractor basins, or "
    "final constraint-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing L64 MPS tensors, two-cycle quantum-jump trajectory steps, SVD truncation, and Phi0 readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing fixed/adaptive trajectory comparison graph",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion and bounded-stability guard",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "statistics": {"tried": True, "used": True, "reason": "supportive stability and timing summary reductions"},
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
TARGET_CYCLES = 2
STAGES_PER_TRAJECTORY = len(mps_runtime.TERRAIN_ORDER_BY_TOKEN["1"]) * TARGET_CYCLES
FAMILIES = tuple(mps_runtime.INITIAL_FAMILIES)
SEEDS = (65052021, 65052022)
POLICIES = ("fixed4", "adaptive2_4")
NORM_TOL = 1.0e-7
STABILITY_TOL = 0.02
TIME_BUDGET_SECONDS = 420.0

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "mps_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "cap_bias_source": SCOUT_ROOT / "sim_two_root_constraint_l64_adaptive_bond_bias_sweep_probe.py",
    "cap_bias_result": RESULT_DIR / "two_root_constraint_l64_adaptive_bond_bias_sweep_probe_results.json",
    "l64_adaptive_result": RESULT_DIR / "two_root_constraint_l64_adaptive_bond_trajectory_batch_probe_results.json",
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


def configure_cap_bias_module() -> None:
    cap_bias.TARGET_CYCLES = TARGET_CYCLES
    cap_bias.STAGES_PER_TRAJECTORY = STAGES_PER_TRAJECTORY
    cap_bias.TIME_BUDGET_SECONDS = TIME_BUDGET_SECONDS


def run_surface() -> dict[str, Any]:
    configure_cap_bias_module()
    started = time.time()
    rows: list[dict[str, Any]] = []
    for family in FAMILIES:
        for seed in SEEDS:
            for policy in POLICIES:
                rows.append(cap_bias.run_policy_trajectory(family, seed, policy, started))
                if time.time() - started > TIME_BUDGET_SECONDS:
                    return aggregate(rows, time.time() - started)
    return aggregate(rows, time.time() - started)


def mean(values: list[float]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def comparison_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("l64_two_cycle_stability")
    by_key: dict[tuple[str, int], int] = {}
    for row in rows:
        key = (row["family"], row["seed"])
        if key not in by_key:
            node = graph.add_node(f"{key[0]}:{key[1]}")
            graph.add_edge(root, node, "matched_row")
            by_key[key] = node
        policy_node = graph.add_node(f"{row['family']}:{row['seed']}:{row['policy']}")
        graph.add_edge(by_key[key], policy_node, "policy")
        for stage in row["stage_rows"]:
            stage_node = graph.add_node(
                f"{row['family']}:{row['seed']}:{row['policy']}:{stage['cycle']}:{stage['stage_index']}"
            )
            graph.add_edge(policy_node, stage_node, "stage")
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
        by_policy.setdefault(row["policy"], []).append(row)
        by_key.setdefault((row["family"], row["seed"]), {})[row["policy"]] = row
    comparisons = []
    for (family, seed), policy_rows in sorted(by_key.items()):
        if set(POLICIES).issubset(policy_rows):
            fixed4 = policy_rows["fixed4"]["center_pair_phi0"]["I_A_colon_B"]
            adaptive = policy_rows["adaptive2_4"]["center_pair_phi0"]["I_A_colon_B"]
            comparisons.append(
                {
                    "family": family,
                    "seed": seed,
                    "fixed4_I_A_colon_B": fixed4,
                    "adaptive_I_A_colon_B": adaptive,
                    "adaptive_minus_fixed4": adaptive - fixed4,
                    "adaptive_abs_delta_to_fixed4": abs(adaptive - fixed4),
                    "fixed4_truncation_error": policy_rows["fixed4"]["total_truncation_error"],
                    "adaptive_truncation_error": policy_rows["adaptive2_4"]["total_truncation_error"],
                    "fixed4_max_bond": policy_rows["fixed4"]["max_bond"],
                    "adaptive_max_bond": policy_rows["adaptive2_4"]["max_bond"],
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
    deltas = [row["adaptive_abs_delta_to_fixed4"] for row in comparisons]
    return {
        "route": "l64_two_cycle_fixed_adaptive_stability",
        "length": LENGTH,
        "target_cycles": TARGET_CYCLES,
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
        "adaptive_mean_abs_delta_to_fixed4": mean(deltas),
        "adaptive_max_abs_delta_to_fixed4": max(deltas, default=0.0),
        "stable_against_fixed4": bool(deltas) and max(deltas) < STABILITY_TOL,
        "comparison_graph": comparison_graph(rows),
        "trajectory_rows": [
            {key: value for key, value in row.items() if key != "stage_rows"} | {"stage_count": len(row["stage_rows"])}
            for row in rows
        ],
        "stage_rows_sample": [stage for row in rows for stage in row["stage_rows"]][:24],
    }


def z3_guard(surface: dict[str, Any]) -> dict[str, Any]:
    complete = z3.Bool("complete")
    two_cycle = z3.Bool("two_cycle")
    stable = z3.Bool("stable")
    full_l64_convergence = z3.Bool("full_l64_convergence")
    robust_phi0 = z3.Bool("robust_phi0")
    peps3d = z3.Bool("peps3d")
    scale_basin = z3.Bool("scale_basin")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(complete == (surface["completed_trajectories"] == surface["target_trajectory_count"]))
    solver.add(two_cycle == (surface["target_cycles"] == 2 and surface["stages_completed"] == surface["target_stages_total"]))
    solver.add(stable == bool(surface["stable_against_fixed4"]))
    solver.add(full_l64_convergence == False)
    solver.add(robust_phi0 == False)
    solver.add(peps3d == False)
    solver.add(scale_basin == False)
    solver.add(final_admission == z3.And(full_l64_convergence, robust_phi0, peps3d, scale_basin))
    check = solver.check()
    model = solver.model() if check == z3.sat else None
    return {
        "sat": check == z3.sat,
        "two_cycle_sweep_complete": bool(z3.is_true(model.eval(complete, model_completion=True))) if model else False,
        "two_cycle_target_met": bool(z3.is_true(model.eval(two_cycle, model_completion=True))) if model else False,
        "adaptive_stable_against_fixed4": bool(z3.is_true(model.eval(stable, model_completion=True))) if model else False,
        "full_l64_convergence_claimed": bool(z3.is_true(model.eval(full_l64_convergence, model_completion=True))) if model else False,
        "robust_phi0_claimed": bool(z3.is_true(model.eval(robust_phi0, model_completion=True))) if model else False,
        "peps3d_claimed": bool(z3.is_true(model.eval(peps3d, model_completion=True))) if model else False,
        "scale_basin_claimed": bool(z3.is_true(model.eval(scale_basin, model_completion=True))) if model else False,
        "final_manifold_admission_allowed": bool(z3.is_true(model.eval(final_admission, model_completion=True))) if model else False,
        "rule": "Two-cycle fixed/adaptive stability can strengthen L64 tensor evidence but cannot imply full convergence, robust Phi0, PEPS3D, scale-basin, or final admission.",
    }


def main() -> int:
    started = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    surface = run_surface()
    guard = z3_guard(surface)
    status = (
        "bounded_l64_two_cycle_stability_complete"
        if surface["completed_trajectories"] == surface["target_trajectory_count"]
        else "bounded_l64_two_cycle_stability_partial"
    )
    positive = {
        "upstream_cap_bias_loaded": {
            "pass": upstream["cap_bias_result"].get("all_pass") is True
            and upstream["cap_bias_result"].get("summary", {}).get("l64_bias_sweep_status")
            == "bounded_l64_adaptive_bias_sweep_complete",
            "upstream_status": upstream["cap_bias_result"].get("summary", {}).get("l64_bias_sweep_status"),
        },
        "all_two_cycle_rows_completed": {
            "pass": guard["two_cycle_sweep_complete"] and guard["two_cycle_target_met"],
            "completed_trajectories": surface["completed_trajectories"],
            "target_trajectory_count": surface["target_trajectory_count"],
            "stages_completed": surface["stages_completed"],
            "target_stages_total": surface["target_stages_total"],
        },
        "adaptive_fixed4_stability_measured": {
            "pass": surface["matched_comparison_count"] == len(FAMILIES) * len(SEEDS),
            "matched_comparison_count": surface["matched_comparison_count"],
            "adaptive_mean_abs_delta_to_fixed4": surface["adaptive_mean_abs_delta_to_fixed4"],
            "adaptive_max_abs_delta_to_fixed4": surface["adaptive_max_abs_delta_to_fixed4"],
            "stable_against_fixed4": surface["stable_against_fixed4"],
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
            "detail": "Two-cycle fixed/adaptive comparison is still bounded finite-horizon evidence.",
        },
        "robust_phi0_not_claimed": {
            "pass": not guard["robust_phi0_claimed"],
            "detail": "Phi0 bridge remains nonrobust under current controls.",
        },
        "peps3d_not_claimed": {
            "pass": not guard["peps3d_claimed"],
            "detail": "This scout is 1D MPS only.",
        },
        "scale_basin_not_claimed": {
            "pass": not guard["scale_basin_claimed"],
            "detail": "No real scale-level attractor-basin admission is made.",
        },
    }
    all_pass = all(item["pass"] for item in positive.values()) and all(item["pass"] for item in graveyard.values())
    summary = {
        "all_pass": all_pass,
        "l64_two_cycle_status": status,
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
        "adaptive_stable_against_fixed4": surface["stable_against_fixed4"],
        "matched_comparison_count": surface["matched_comparison_count"],
        "final_manifold_admission_allowed": False,
        "interpretation": (
            "L64 adaptive D=2/4 has now been compared against fixed D=4 for two complete cycles on matched rows. "
            "This strengthens finite-horizon tensor stability evidence but remains bounded 1D MPS evidence."
        ),
        "next_required_work": (
            "For tensor closure, continue to longer horizon fixed/adaptive sweeps or implement local Krylov/doubled-MPS Lindblad; "
            "robust Phi0 and real scale-basin admission remain separate blockers."
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
            "cap_bias_status": upstream["cap_bias_result"].get("summary", {}).get("l64_bias_sweep_status"),
            "l64_adaptive_status": upstream["l64_adaptive_result"].get("summary", {}).get("l64_adaptive_status"),
        },
        "parameters": {
            "length": LENGTH,
            "target_cycles": TARGET_CYCLES,
            "families": list(FAMILIES),
            "seeds": list(SEEDS),
            "policies": list(POLICIES),
            "time_budget_seconds": TIME_BUDGET_SECONDS,
            "stability_tolerance": STABILITY_TOL,
        },
        "surface": surface,
        "z3_guard": guard,
        "positive": positive,
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "l64_two_cycle_status": status,
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
            "Implement local Krylov or vectorized doubled-MPS Lindblad to move beyond trajectory finite-horizon evidence.",
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
