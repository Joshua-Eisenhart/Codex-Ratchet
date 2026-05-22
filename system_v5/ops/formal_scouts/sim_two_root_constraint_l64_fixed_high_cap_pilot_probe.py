#!/usr/bin/env python3
"""L64 fixed higher-cap MPS pilot.

The previous two-cycle L64 scout found that adaptive D=2/4 no longer tracks
fixed D=4 and accumulates much larger truncation. This bounded pilot tests the
next simplest tensor route: keep the dynamics identical, but compare fixed D=4
against fixed D=6 on a small matched surface.

This is still bounded 1D MPS quantum-trajectory evidence. It cannot promote
full L64 convergence, PEPS/PEPS3D closure, robust Phi0, real scale-level
attractor basins, or final constraint-manifold admission.
"""

from __future__ import annotations

import hashlib
import json
import math
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
OUT_PATH = RESULT_DIR / "two_root_constraint_l64_fixed_high_cap_pilot_probe_results.json"

NAME = "two_root_constraint_l64_fixed_high_cap_pilot_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_l64_fixed_high_cap_mps_pilot"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_l64_fixed_high_cap_tensor_pilot"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal tensor-runtime pilot only: compares fixed D=4 and fixed D=6 L64 "
    "MPS quantum trajectories on a bounded matched two-cycle surface. It "
    "cannot promote full L64 convergence, PEPS/PEPS3D closure, robust Phi0, "
    "real scale-level attractor basins, or final constraint-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing L64 MPS tensors, fixed-cap quantum-jump trajectory steps, SVD truncation, and Phi0 readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing fixed-cap comparison graph over family, seed, cap, and stage rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion and bounded higher-cap pilot guard",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "statistics": {"tried": True, "used": True, "reason": "supportive timing, truncation, and readout reductions"},
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
FAMILIES = ("plus_x", "alternating_z")
SEEDS = (65052021,)
CAPS = (4, 6)
NORM_TOL = 1.0e-7
READOUT_DELTA_TOL = 0.02
TRUNCATION_IMPROVEMENT_RATIO = 0.5
TIME_BUDGET_SECONDS = 420.0

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "mps_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "cap_bias_source": SCOUT_ROOT / "sim_two_root_constraint_l64_adaptive_bond_bias_sweep_probe.py",
    "two_cycle_result": RESULT_DIR / "two_root_constraint_l64_two_cycle_fixed_adaptive_stability_probe_results.json",
    "cap_bias_result": RESULT_DIR / "two_root_constraint_l64_adaptive_bond_bias_sweep_probe_results.json",
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


def run_fixed_cap_trajectory(family: str, seed: int, cap: int, started: float) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(seed)
    mps = mps_runtime.MPS.product(family, LENGTH)
    token_prev: str | None = "1"
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
            stage_rows.append(
                {
                    "family": family,
                    "seed": seed,
                    "cap": cap,
                    "cycle": cycle,
                    "stage_index": terrain_idx,
                    "token": token,
                    "terrain": terrain,
                    "stage_truncation_error": stage_truncation,
                    "total_truncation_error": total_truncation,
                    "jump_count": jump_count,
                    "max_bond": mps.max_bond(),
                    "norm_error": abs(float(mps.norm_sq().item()) - 1.0),
                    "stage_seconds": time.time() - stage_started,
                    "elapsed_seconds": time.time() - started,
                }
            )
            if time.time() - started > TIME_BUDGET_SECONDS:
                stop_reason = "time_budget_after_completed_stage"
                break
        if stop_reason != "target_complete":
            break
    phi0 = cap_bias.center_pair_phi0(mps)
    return {
        "family": family,
        "seed": seed,
        "cap": cap,
        "length": LENGTH,
        "stages_completed": len(stage_rows),
        "target_stages": STAGES_PER_TRAJECTORY,
        "completed_target": len(stage_rows) == STAGES_PER_TRAJECTORY,
        "stop_reason": stop_reason,
        "max_bond": mps.max_bond(),
        "bond_dims": mps.bond_dims(),
        "norm_error": abs(float(mps.norm_sq().item()) - 1.0),
        "total_truncation_error": total_truncation,
        "total_jumps": total_jumps,
        "mean_stage_seconds": float(statistics.fmean(row["stage_seconds"] for row in stage_rows)) if stage_rows else 0.0,
        "max_stage_seconds": max((row["stage_seconds"] for row in stage_rows), default=0.0),
        "center_pair_phi0": phi0,
        "stage_rows": stage_rows,
    }


def mean(values: list[float]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def comparison_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("l64_fixed_high_cap_pilot")
    by_key: dict[tuple[str, int], int] = {}
    for row in rows:
        key = (row["family"], row["seed"])
        if key not in by_key:
            node = graph.add_node(f"{key[0]}:{key[1]}")
            graph.add_edge(root, node, "matched_row")
            by_key[key] = node
        cap_node = graph.add_node(f"{row['family']}:{row['seed']}:D{row['cap']}")
        graph.add_edge(by_key[key], cap_node, "fixed_cap")
        for stage in row["stage_rows"]:
            stage_node = graph.add_node(f"{row['family']}:{row['seed']}:D{row['cap']}:{stage['cycle']}:{stage['stage_index']}")
            graph.add_edge(cap_node, stage_node, "stage")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": rx.is_directed_acyclic_graph(graph),
        "weakly_connected_components": len(rx.weakly_connected_components(graph)),
    }


def aggregate(rows: list[dict[str, Any]], elapsed: float) -> dict[str, Any]:
    by_cap: dict[int, list[dict[str, Any]]] = {cap: [] for cap in CAPS}
    by_key: dict[tuple[str, int], dict[int, dict[str, Any]]] = {}
    for row in rows:
        by_cap.setdefault(row["cap"], []).append(row)
        by_key.setdefault((row["family"], row["seed"]), {})[row["cap"]] = row
    comparisons: list[dict[str, Any]] = []
    for (family, seed), cap_rows in sorted(by_key.items()):
        if set(CAPS).issubset(cap_rows):
            fixed4 = cap_rows[4]
            fixed6 = cap_rows[6]
            fixed4_mi = fixed4["center_pair_phi0"]["I_A_colon_B"]
            fixed6_mi = fixed6["center_pair_phi0"]["I_A_colon_B"]
            fixed4_trunc = fixed4["total_truncation_error"]
            fixed6_trunc = fixed6["total_truncation_error"]
            comparisons.append(
                {
                    "family": family,
                    "seed": seed,
                    "fixed4_I_A_colon_B": fixed4_mi,
                    "fixed6_I_A_colon_B": fixed6_mi,
                    "fixed6_minus_fixed4_I_A_colon_B": fixed6_mi - fixed4_mi,
                    "fixed6_abs_delta_to_fixed4": abs(fixed6_mi - fixed4_mi),
                    "fixed4_truncation_error": fixed4_trunc,
                    "fixed6_truncation_error": fixed6_trunc,
                    "fixed6_truncation_ratio_to_fixed4": fixed6_trunc / max(fixed4_trunc, 1.0e-30),
                    "fixed6_improves_truncation": fixed6_trunc < fixed4_trunc,
                    "fixed4_max_stage_seconds": fixed4["max_stage_seconds"],
                    "fixed6_max_stage_seconds": fixed6["max_stage_seconds"],
                    "fixed6_stage_time_ratio_to_fixed4": fixed6["mean_stage_seconds"]
                    / max(fixed4["mean_stage_seconds"], 1.0e-30),
                }
            )
    cap_summary: dict[str, Any] = {}
    for cap, cap_rows in by_cap.items():
        mi_values = [row["center_pair_phi0"]["I_A_colon_B"] for row in cap_rows]
        cap_summary[f"fixed{cap}"] = {
            "trajectory_count": len(cap_rows),
            "completed_trajectories": sum(1 for row in cap_rows if row["completed_target"]),
            "stages_completed": sum(row["stages_completed"] for row in cap_rows),
            "mean_I_A_colon_B": mean(mi_values),
            "max_I_A_colon_B": max(mi_values) if mi_values else 0.0,
            "min_I_A_colon_B": min(mi_values) if mi_values else 0.0,
            "total_truncation_error": sum(row["total_truncation_error"] for row in cap_rows),
            "max_trajectory_truncation_error": max((row["total_truncation_error"] for row in cap_rows), default=0.0),
            "max_bond": max((row["max_bond"] for row in cap_rows), default=0),
            "norm_error": max((row["norm_error"] for row in cap_rows), default=float("inf")),
            "mean_stage_seconds": mean([row["mean_stage_seconds"] for row in cap_rows]),
            "max_stage_seconds": max((row["max_stage_seconds"] for row in cap_rows), default=0.0),
        }
    deltas = [row["fixed6_abs_delta_to_fixed4"] for row in comparisons]
    ratios = [row["fixed6_truncation_ratio_to_fixed4"] for row in comparisons]
    return {
        "route": "l64_fixed_high_cap_pilot",
        "length": LENGTH,
        "target_cycles": TARGET_CYCLES,
        "families": list(FAMILIES),
        "seeds": list(SEEDS),
        "caps": list(CAPS),
        "elapsed_seconds": elapsed,
        "trajectory_count": len(rows),
        "completed_trajectories": sum(1 for row in rows if row["completed_target"]),
        "target_trajectory_count": len(FAMILIES) * len(SEEDS) * len(CAPS),
        "stages_completed": sum(row["stages_completed"] for row in rows),
        "target_stages_total": len(FAMILIES) * len(SEEDS) * len(CAPS) * STAGES_PER_TRAJECTORY,
        "cap_summary": cap_summary,
        "matched_comparison_count": len(comparisons),
        "comparisons": comparisons,
        "fixed6_mean_abs_delta_to_fixed4": mean(deltas),
        "fixed6_max_abs_delta_to_fixed4": max(deltas, default=0.0),
        "fixed6_mean_truncation_ratio_to_fixed4": mean(ratios),
        "fixed6_max_truncation_ratio_to_fixed4": max(ratios, default=0.0),
        "fixed6_all_rows_improve_truncation": bool(comparisons)
        and all(row["fixed6_improves_truncation"] for row in comparisons),
        "fixed6_readout_close_to_fixed4": bool(comparisons) and max(deltas) < READOUT_DELTA_TOL,
        "fixed6_material_truncation_improvement": bool(comparisons)
        and max(ratios, default=1.0) < TRUNCATION_IMPROVEMENT_RATIO,
        "comparison_graph": comparison_graph(rows),
        "trajectory_rows": [
            {key: value for key, value in row.items() if key != "stage_rows"} | {"stage_count": len(row["stage_rows"])}
            for row in rows
        ],
        "stage_rows_sample": [stage for row in rows for stage in row["stage_rows"]][:24],
    }


def run_surface() -> dict[str, Any]:
    started = time.time()
    rows: list[dict[str, Any]] = []
    for family in FAMILIES:
        for seed in SEEDS:
            for cap in CAPS:
                rows.append(run_fixed_cap_trajectory(family, seed, cap, started))
                if time.time() - started > TIME_BUDGET_SECONDS:
                    return aggregate(rows, time.time() - started)
    return aggregate(rows, time.time() - started)


def z3_guard(surface: dict[str, Any]) -> dict[str, Any]:
    complete = z3.Bool("complete")
    two_cycle = z3.Bool("two_cycle")
    high_cap_compared = z3.Bool("high_cap_compared")
    readout_close = z3.Bool("readout_close")
    material_truncation_improvement = z3.Bool("material_truncation_improvement")
    full_l64_convergence = z3.Bool("full_l64_convergence")
    robust_phi0 = z3.Bool("robust_phi0")
    peps3d = z3.Bool("peps3d")
    scale_basin = z3.Bool("scale_basin")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(complete == (surface["completed_trajectories"] == surface["target_trajectory_count"]))
    solver.add(two_cycle == (surface["target_cycles"] == 2 and surface["stages_completed"] == surface["target_stages_total"]))
    solver.add(high_cap_compared == (surface["matched_comparison_count"] == len(FAMILIES) * len(SEEDS)))
    solver.add(readout_close == bool(surface["fixed6_readout_close_to_fixed4"]))
    solver.add(material_truncation_improvement == bool(surface["fixed6_material_truncation_improvement"]))
    solver.add(full_l64_convergence == False)
    solver.add(robust_phi0 == False)
    solver.add(peps3d == False)
    solver.add(scale_basin == False)
    solver.add(final_admission == z3.And(full_l64_convergence, robust_phi0, peps3d, scale_basin))
    check = solver.check()
    model = solver.model() if check == z3.sat else None
    return {
        "sat": check == z3.sat,
        "two_cycle_pilot_complete": bool(z3.is_true(model.eval(complete, model_completion=True))) if model else False,
        "two_cycle_target_met": bool(z3.is_true(model.eval(two_cycle, model_completion=True))) if model else False,
        "higher_cap_compared": bool(z3.is_true(model.eval(high_cap_compared, model_completion=True))) if model else False,
        "fixed6_readout_close_to_fixed4": bool(z3.is_true(model.eval(readout_close, model_completion=True))) if model else False,
        "fixed6_material_truncation_improvement": bool(z3.is_true(model.eval(material_truncation_improvement, model_completion=True))) if model else False,
        "full_l64_convergence_claimed": bool(z3.is_true(model.eval(full_l64_convergence, model_completion=True))) if model else False,
        "robust_phi0_claimed": bool(z3.is_true(model.eval(robust_phi0, model_completion=True))) if model else False,
        "peps3d_claimed": bool(z3.is_true(model.eval(peps3d, model_completion=True))) if model else False,
        "scale_basin_claimed": bool(z3.is_true(model.eval(scale_basin, model_completion=True))) if model else False,
        "final_manifold_admission_allowed": bool(z3.is_true(model.eval(final_admission, model_completion=True))) if model else False,
        "rule": "A bounded fixed D=6 pilot can justify or reject a higher-cap route, but cannot imply full L64 convergence, robust Phi0, PEPS3D, scale-basin, or final admission.",
    }


def main() -> int:
    started = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    surface = run_surface()
    guard = z3_guard(surface)
    status = (
        "bounded_l64_fixed_high_cap_pilot_complete"
        if surface["completed_trajectories"] == surface["target_trajectory_count"]
        else "bounded_l64_fixed_high_cap_pilot_partial"
    )
    positive = {
        "upstream_two_cycle_negative_loaded": {
            "pass": upstream["two_cycle_result"].get("all_pass") is True
            and upstream["two_cycle_result"].get("summary", {}).get("l64_two_cycle_status")
            == "bounded_l64_two_cycle_stability_complete",
            "upstream_status": upstream["two_cycle_result"].get("summary", {}).get("l64_two_cycle_status"),
        },
        "all_fixed_cap_rows_completed": {
            "pass": guard["two_cycle_pilot_complete"] and guard["two_cycle_target_met"],
            "completed_trajectories": surface["completed_trajectories"],
            "target_trajectory_count": surface["target_trajectory_count"],
            "stages_completed": surface["stages_completed"],
            "target_stages_total": surface["target_stages_total"],
        },
        "fixed6_fixed4_comparison_measured": {
            "pass": guard["higher_cap_compared"],
            "matched_comparison_count": surface["matched_comparison_count"],
            "fixed6_mean_abs_delta_to_fixed4": surface["fixed6_mean_abs_delta_to_fixed4"],
            "fixed6_max_abs_delta_to_fixed4": surface["fixed6_max_abs_delta_to_fixed4"],
            "fixed6_readout_close_to_fixed4": surface["fixed6_readout_close_to_fixed4"],
            "fixed6_mean_truncation_ratio_to_fixed4": surface["fixed6_mean_truncation_ratio_to_fixed4"],
            "fixed6_material_truncation_improvement": surface["fixed6_material_truncation_improvement"],
        },
        "norms_and_truncations_recorded": {
            "pass": all(row["norm_error"] < NORM_TOL for row in surface["cap_summary"].values())
            and all(row["total_truncation_error"] >= 0.0 for row in surface["cap_summary"].values()),
            "cap_summary": surface["cap_summary"],
        },
        "z3_nonpromotion_guard": {
            "pass": guard["sat"] and not guard["final_manifold_admission_allowed"],
            "guard": guard,
        },
    }
    graveyard = {
        "full_l64_convergence_not_claimed": {
            "pass": not guard["full_l64_convergence_claimed"],
            "detail": "A two-family fixed D=6 pilot is still bounded finite-horizon evidence.",
        },
        "robust_phi0_not_claimed": {
            "pass": not guard["robust_phi0_claimed"],
            "detail": "Center-pair Phi0 diagnostics are not a robust bridge theorem.",
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
        "l64_fixed_high_cap_status": status,
        "trajectory_count": surface["trajectory_count"],
        "completed_trajectories": surface["completed_trajectories"],
        "stages_completed": surface["stages_completed"],
        "elapsed_seconds": surface["elapsed_seconds"],
        "cap_mean_I_A_colon_B": {
            cap: row["mean_I_A_colon_B"] for cap, row in surface["cap_summary"].items()
        },
        "cap_total_truncation_error": {
            cap: row["total_truncation_error"] for cap, row in surface["cap_summary"].items()
        },
        "fixed6_mean_abs_delta_to_fixed4": surface["fixed6_mean_abs_delta_to_fixed4"],
        "fixed6_max_abs_delta_to_fixed4": surface["fixed6_max_abs_delta_to_fixed4"],
        "fixed6_mean_truncation_ratio_to_fixed4": surface["fixed6_mean_truncation_ratio_to_fixed4"],
        "fixed6_material_truncation_improvement": surface["fixed6_material_truncation_improvement"],
        "matched_comparison_count": surface["matched_comparison_count"],
        "final_manifold_admission_allowed": False,
        "interpretation": (
            "Fixed D=6 has now been compared against fixed D=4 on a bounded two-cycle L64 surface. "
            "This tests whether higher fixed caps are a useful next tensor route, but remains 1D MPS pilot evidence."
        ),
        "next_required_work": (
            "If fixed D=6 materially reduces truncation or changes readouts, expand to more seeds/families or D=8. "
            "If it does not, prioritize local Krylov or vectorized doubled-MPS Lindblad instead of cap-only scaling."
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
            "two_cycle_status": upstream["two_cycle_result"].get("summary", {}).get("l64_two_cycle_status"),
            "cap_bias_status": upstream["cap_bias_result"].get("summary", {}).get("l64_bias_sweep_status"),
        },
        "parameters": {
            "length": LENGTH,
            "target_cycles": TARGET_CYCLES,
            "families": list(FAMILIES),
            "seeds": list(SEEDS),
            "caps": list(CAPS),
            "time_budget_seconds": TIME_BUDGET_SECONDS,
            "readout_delta_tolerance": READOUT_DELTA_TOL,
            "truncation_improvement_ratio": TRUNCATION_IMPROVEMENT_RATIO,
        },
        "surface": surface,
        "z3_guard": guard,
        "positive": positive,
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "l64_fixed_high_cap_status": status,
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
            "Expand fixed D=6 to more families/seeds if the pilot is materially informative.",
            "Try fixed D=8 only as a bounded pilot if D=6 gives a clear signal and runtime remains acceptable.",
            "Prefer local Krylov or vectorized doubled-MPS Lindblad if cap-only scaling stops improving truncation/readout stability.",
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
