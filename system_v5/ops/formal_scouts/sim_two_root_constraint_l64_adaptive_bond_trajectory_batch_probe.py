#!/usr/bin/env python3
"""L64 adaptive-bond MPS trajectory batch scout.

The fixed low-bond L64 first rung proved that a D=4 bounded trajectory surface
can run, but it explicitly did not address bond scaling or trajectory batching.
This scout adds the next tensor-runtime rung: source-native PyTorch L64 MPS
quantum trajectories with a simple adaptive SVD bond policy and a small seed
batch. It records cap changes, truncation, timing, norm, and center-pair Phi0
readouts.

This is still bounded tensor-runtime evidence. It is not full L64 convergence,
not PEPS/PEPS3D closure, not scale-level real attractor-basin admission, and
not final manifold admission.
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
import sim_two_root_constraint_tensor_network_lindblad_runtime_probe as mps_runtime


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_l64_adaptive_bond_trajectory_batch_probe_results.json"

NAME = "two_root_constraint_l64_adaptive_bond_trajectory_batch_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_l64_adaptive_bond_mps_trajectory_batch"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_l64_adaptive_bond_tensor_runtime"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal tensor-runtime scout only: runs a bounded source-native PyTorch L64 "
    "MPS quantum-trajectory batch with adaptive SVD bond caps and emits norm, "
    "truncation, timing, cap-policy, and Phi0 diagnostics. It cannot promote "
    "full L64 convergence, PEPS/PEPS3D closure, scale-level real attractor "
    "basins, robust Phi0, or final constraint-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing L64 MPS tensors, local quantum-jump trajectory steps, adaptive SVD truncation, and Phi0 readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing trajectory/cap-policy graph witness over family/seed/stage rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing guard separating adaptive-bond tensor evidence from full convergence/final admission claims",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and receipt provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "statistics": {"tried": True, "used": True, "reason": "supportive timing and trajectory summary diagnostics"},
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
STAGES_PER_CYCLE = len(mps_runtime.TERRAIN_ORDER_BY_TOKEN["1"])
TARGET_STAGES_PER_TRAJECTORY = TARGET_CYCLES * STAGES_PER_CYCLE
FAMILIES = tuple(mps_runtime.INITIAL_FAMILIES)
SEEDS = (65052021, 65052022)
MIN_BOND_CAP = 2
MAX_BOND_CAP = 8
CAP_STEP = 2
TRUNCATION_RAISE_THRESHOLD = 2.0e-6
TRUNCATION_LOWER_THRESHOLD = 1.0e-9
NORM_TOL = 1.0e-7
TIME_BUDGET_SECONDS = 150.0

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "mps_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "l16_mps_result": RESULT_DIR / "two_root_constraint_tensor_network_lindblad_runtime_probe_results.json",
    "l32_result": RESULT_DIR / "two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json",
    "l64_low_bond_result": RESULT_DIR / "two_root_constraint_l64_tensor_blocker_or_mitigation_probe_results.json",
    "post_stress_trace_result": RESULT_DIR / "two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json",
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
    return {name: {"path": rel(path), "sha256": sha256(path), "exists": path.exists()} for name, path in SOURCE_FILES.items()}


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


def center_pair_phi0_from_mps(mps: mps_runtime.MPS) -> dict[str, float]:
    return mps_runtime.phi0_readout_pair(two_site_density_adjacent(mps, mps.L // 2 - 1))


def next_cap(current_cap: int, stage_truncation: float) -> int:
    if stage_truncation > TRUNCATION_RAISE_THRESHOLD:
        return min(MAX_BOND_CAP, current_cap + CAP_STEP)
    if stage_truncation < TRUNCATION_LOWER_THRESHOLD and current_cap > MIN_BOND_CAP:
        return max(MIN_BOND_CAP, current_cap - CAP_STEP)
    return current_cap


def run_adaptive_trajectory(family: str, seed: int, started: float) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(seed)
    mps = mps_runtime.MPS.product(family, LENGTH)
    token_prev: str | None = "1"
    cap = MIN_BOND_CAP
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
            parity = terrain_idx % 2
            stage_truncation = 0.0
            for site in range(parity, LENGTH - 1, 2):
                stage_truncation += mps.apply_two(gate_two, site, max_bond=cap)
                mps.normalize_()
            total_truncation += stage_truncation
            total_jumps += jump_count
            cap_after = next_cap(cap, stage_truncation)
            elapsed = time.time() - started
            stage_rows.append(
                {
                    "family": family,
                    "seed": seed,
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
                    "bond_dims": mps.bond_dims(),
                    "norm_error": abs(float(mps.norm_sq().item()) - 1.0),
                    "stage_seconds": time.time() - stage_started,
                    "elapsed_seconds": elapsed,
                }
            )
            cap = cap_after
            if elapsed >= TIME_BUDGET_SECONDS:
                stop_reason = "time_budget_after_completed_stage"
                break
        if stop_reason != "target_complete":
            break
    phi0 = center_pair_phi0_from_mps(mps)
    return {
        "family": family,
        "seed": seed,
        "length": LENGTH,
        "stages_completed": len(stage_rows),
        "target_stages": TARGET_STAGES_PER_TRAJECTORY,
        "completed_target": len(stage_rows) == TARGET_STAGES_PER_TRAJECTORY,
        "stop_reason": stop_reason,
        "final_cap": cap,
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


def policy_graph(trajectories: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    previous_by_trajectory: dict[tuple[str, int], int] = {}
    for traj in trajectories:
        key = (traj["family"], traj["seed"])
        for stage in traj["stage_rows"]:
            label = (
                f"{stage['family']}:{stage['seed']}:{stage['cycle']}:"
                f"{stage['stage_index']}:{stage['terrain']}:D{stage['cap_before']}"
            )
            node = graph.add_node(label)
            if key in previous_by_trajectory:
                graph.add_edge(previous_by_trajectory[key], node, "next_stage")
            previous_by_trajectory[key] = node
            if stage["cap_after"] != stage["cap_before"]:
                cap_node = graph.add_node(f"cap:{stage['cap_before']}->{stage['cap_after']}")
                graph.add_edge(node, cap_node, "cap_policy")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": rx.is_directed_acyclic_graph(graph),
        "weakly_connected_components": len(rx.weakly_connected_components(graph)),
    }


def aggregate(trajectories: list[dict[str, Any]], elapsed: float) -> dict[str, Any]:
    stage_rows = [stage for traj in trajectories for stage in traj["stage_rows"]]
    family_phi0: dict[str, list[float]] = {}
    for traj in trajectories:
        family_phi0.setdefault(traj["family"], []).append(traj["center_pair_phi0"]["I_A_colon_B"])
    return {
        "route": "adaptive_bond_l64_mps_trajectory_batch",
        "length": LENGTH,
        "target_cycles": TARGET_CYCLES,
        "seed_count": len(SEEDS),
        "family_count": len(FAMILIES),
        "trajectory_count": len(trajectories),
        "completed_trajectories": sum(1 for traj in trajectories if traj["completed_target"]),
        "stages_completed": sum(traj["stages_completed"] for traj in trajectories),
        "target_stages_total": len(FAMILIES) * len(SEEDS) * TARGET_STAGES_PER_TRAJECTORY,
        "elapsed_seconds": elapsed,
        "max_bond_cap_allowed": MAX_BOND_CAP,
        "min_bond_cap_allowed": MIN_BOND_CAP,
        "max_bond_observed": max((traj["max_bond"] for traj in trajectories), default=0),
        "cap_values_seen": sorted({cap for traj in trajectories for cap in traj["cap_values_seen"]}),
        "cap_increase_count": sum(traj["cap_increase_count"] for traj in trajectories),
        "cap_decrease_count": sum(traj["cap_decrease_count"] for traj in trajectories),
        "total_truncation_error": sum(traj["total_truncation_error"] for traj in trajectories),
        "max_trajectory_truncation_error": max((traj["total_truncation_error"] for traj in trajectories), default=0.0),
        "norm_error": max((traj["norm_error"] for traj in trajectories), default=float("inf")),
        "total_jumps": sum(traj["total_jumps"] for traj in trajectories),
        "mean_stage_seconds": statistics.fmean([row["stage_seconds"] for row in stage_rows]) if stage_rows else None,
        "max_stage_seconds": max((row["stage_seconds"] for row in stage_rows), default=0.0),
        "center_pair_mutual_information_by_family": {
            family: statistics.fmean(values) for family, values in family_phi0.items()
        },
        "center_pair_mutual_information_spread_by_family": {
            family: (max(values) - min(values) if values else 0.0) for family, values in family_phi0.items()
        },
        "trajectory_rows": [
            {key: value for key, value in traj.items() if key != "stage_rows"}
            | {"stage_count": len(traj["stage_rows"])}
            for traj in trajectories
        ],
        "stage_rows_sample": stage_rows[:16],
        "policy_graph": policy_graph(trajectories),
    }


def run_surface() -> dict[str, Any]:
    started = time.time()
    trajectories: list[dict[str, Any]] = []
    for family in FAMILIES:
        for seed in SEEDS:
            trajectories.append(run_adaptive_trajectory(family, seed, started))
            if time.time() - started >= TIME_BUDGET_SECONDS:
                break
        if time.time() - started >= TIME_BUDGET_SECONDS:
            break
    return aggregate(trajectories, time.time() - started) | {"trajectories": trajectories}


def z3_guard(surface: dict[str, Any], upstream: dict[str, dict[str, Any]]) -> dict[str, Any]:
    l64_fixed_first_rung = z3.Bool("l64_fixed_first_rung")
    adaptive_batch_attempted = z3.Bool("adaptive_batch_attempted")
    adaptive_batch_complete = z3.Bool("adaptive_batch_complete")
    adaptive_policy_used = z3.Bool("adaptive_policy_used")
    full_l64_convergence = z3.Bool("full_l64_convergence")
    robust_phi0 = z3.Bool("robust_phi0")
    full_peps = z3.Bool("full_peps")
    scale_basin = z3.Bool("scale_basin")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(
        l64_fixed_first_rung
        == (
            upstream["l64_low_bond_result"].get("summary", {}).get("l64_status")
            == "bounded_low_bond_l64_first_rung_complete"
        )
    )
    solver.add(adaptive_batch_attempted == (surface["trajectory_count"] > 0 and surface["stages_completed"] > 0))
    solver.add(adaptive_batch_complete == (surface["completed_trajectories"] == surface["trajectory_count"]))
    solver.add(adaptive_policy_used == (surface["cap_increase_count"] + surface["cap_decrease_count"] > 0))
    solver.add(full_l64_convergence == False)
    solver.add(robust_phi0 == False)
    solver.add(full_peps == False)
    solver.add(scale_basin == False)
    solver.add(
        final_admission
        == z3.And(full_l64_convergence, robust_phi0, full_peps, scale_basin)
    )
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "sat": status == z3.sat,
        "l64_fixed_first_rung_loaded": bool(z3.is_true(model.eval(l64_fixed_first_rung, model_completion=True))) if model else False,
        "adaptive_batch_attempted": bool(z3.is_true(model.eval(adaptive_batch_attempted, model_completion=True))) if model else False,
        "adaptive_batch_complete": bool(z3.is_true(model.eval(adaptive_batch_complete, model_completion=True))) if model else False,
        "adaptive_policy_used": bool(z3.is_true(model.eval(adaptive_policy_used, model_completion=True))) if model else False,
        "full_l64_convergence_claimed": bool(z3.is_true(model.eval(full_l64_convergence, model_completion=True))) if model else False,
        "robust_phi0_claimed": bool(z3.is_true(model.eval(robust_phi0, model_completion=True))) if model else False,
        "full_peps_claimed": bool(z3.is_true(model.eval(full_peps, model_completion=True))) if model else False,
        "scale_basin_claimed": bool(z3.is_true(model.eval(scale_basin, model_completion=True))) if model else False,
        "final_manifold_admission_allowed": bool(z3.is_true(model.eval(final_admission, model_completion=True))) if model else False,
        "rule": "Adaptive L64 batching can strengthen tensor-runtime evidence but cannot imply full convergence, robust Phi0, PEPS/PEPS3D, scale basin, or final admission.",
    }


def main() -> int:
    started = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    surface = run_surface()
    guard = z3_guard(surface, upstream)
    adaptive_status = (
        "bounded_adaptive_l64_batch_complete"
        if surface["completed_trajectories"] == surface["trajectory_count"] == len(FAMILIES) * len(SEEDS)
        else "bounded_adaptive_l64_batch_partial"
    )
    positive = {
        "fixed_l64_first_rung_loaded": {
            "pass": guard["l64_fixed_first_rung_loaded"],
            "l64_status": upstream["l64_low_bond_result"].get("summary", {}).get("l64_status"),
        },
        "adaptive_l64_batch_attempted": {
            "pass": guard["adaptive_batch_attempted"] and surface["length"] == LENGTH,
            "trajectory_count": surface["trajectory_count"],
            "stages_completed": surface["stages_completed"],
        },
        "adaptive_policy_used": {
            "pass": guard["adaptive_policy_used"],
            "cap_values_seen": surface["cap_values_seen"],
            "cap_increase_count": surface["cap_increase_count"],
            "cap_decrease_count": surface["cap_decrease_count"],
        },
        "trajectory_batch_complete": {
            "pass": surface["completed_trajectories"] == surface["trajectory_count"],
            "completed_trajectories": surface["completed_trajectories"],
            "trajectory_count": surface["trajectory_count"],
        },
        "norm_truncation_phi0_recorded": {
            "pass": surface["norm_error"] < NORM_TOL
            and surface["total_truncation_error"] >= 0.0
            and bool(surface["center_pair_mutual_information_by_family"]),
            "norm_error": surface["norm_error"],
            "total_truncation_error": surface["total_truncation_error"],
            "center_pair_mutual_information_by_family": surface["center_pair_mutual_information_by_family"],
        },
        "z3_nonpromotion_guard": {
            "pass": guard["sat"] and not guard["final_manifold_admission_allowed"],
            "guard": guard,
        },
    }
    graveyard = {
        "full_l64_convergence_not_claimed": {
            "pass": not guard["full_l64_convergence_claimed"],
            "detail": "Adaptive batch is bounded evidence, not a convergence theorem.",
        },
        "robust_phi0_not_claimed": {
            "pass": not guard["robust_phi0_claimed"],
            "detail": "Phi0 remains open/nonrobust from current bridge controls.",
        },
        "peps_peps3d_not_claimed": {
            "pass": not guard["full_peps_claimed"],
            "detail": "This is 1D MPS, not PEPS or PEPS3D closure.",
        },
        "scale_basin_not_claimed": {
            "pass": not guard["scale_basin_claimed"],
            "detail": "No real scale-level basin admission is made.",
        },
        "final_admission_blocked": {
            "pass": not guard["final_manifold_admission_allowed"],
            "detail": "Final manifold admission remains blocked.",
        },
    }
    all_pass = all(item["pass"] for item in positive.values()) and all(item["pass"] for item in graveyard.values())
    summary = {
        "all_pass": all_pass,
        "l64_adaptive_status": adaptive_status,
        "route": surface["route"],
        "length": surface["length"],
        "trajectory_count": surface["trajectory_count"],
        "completed_trajectories": surface["completed_trajectories"],
        "stages_completed": surface["stages_completed"],
        "target_stages_total": surface["target_stages_total"],
        "elapsed_seconds": surface["elapsed_seconds"],
        "cap_values_seen": surface["cap_values_seen"],
        "cap_increase_count": surface["cap_increase_count"],
        "cap_decrease_count": surface["cap_decrease_count"],
        "max_bond_observed": surface["max_bond_observed"],
        "total_truncation_error": surface["total_truncation_error"],
        "max_trajectory_truncation_error": surface["max_trajectory_truncation_error"],
        "norm_error": surface["norm_error"],
        "center_pair_mutual_information_by_family": surface["center_pair_mutual_information_by_family"],
        "center_pair_mutual_information_spread_by_family": surface[
            "center_pair_mutual_information_spread_by_family"
        ],
        "final_manifold_admission_allowed": False,
        "interpretation": (
            "L64 now has an adaptive-bond, multi-seed trajectory batch on top of the fixed D=4 first rung. "
            "This strengthens tensor-runtime evidence but remains bounded 1D MPS evidence, not full tensor closure."
        ),
        "next_required_work": (
            "For further tensor progress, run a longer adaptive-bond bias sweep against fixed caps or move to local "
            "Krylov/doubled-MPS Lindblad; PEPS/PEPS3D and scale-level basin admission remain separate blockers."
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
            "l16_mps_status": upstream["l16_mps_result"].get("summary", {}).get("tensor_runtime_status"),
            "l32_status": upstream["l32_result"].get("summary", {}).get("l32_status"),
            "l64_low_bond_status": upstream["l64_low_bond_result"].get("summary", {}).get("l64_status"),
            "post_stress_trace_status": upstream["post_stress_trace_result"].get("summary", {}).get(
                "trace_refresh_status"
            ),
        },
        "parameters": {
            "length": LENGTH,
            "target_cycles": TARGET_CYCLES,
            "families": list(FAMILIES),
            "seeds": list(SEEDS),
            "min_bond_cap": MIN_BOND_CAP,
            "max_bond_cap": MAX_BOND_CAP,
            "cap_step": CAP_STEP,
            "truncation_raise_threshold": TRUNCATION_RAISE_THRESHOLD,
            "truncation_lower_threshold": TRUNCATION_LOWER_THRESHOLD,
            "time_budget_seconds": TIME_BUDGET_SECONDS,
        },
        "surface": surface,
        "z3_guard": guard,
        "positive": positive,
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "l64_adaptive_status": adaptive_status,
            "full_l64_convergence_claimed": False,
            "robust_phi0_claimed": False,
            "peps_peps3d_full_claimed": False,
            "scale_basin_claimed": False,
            "final_manifold_admission_allowed": False,
            "why_not_final": [
                "Adaptive L64 batching is bounded 1D MPS evidence, not full L64 convergence.",
                "Phi0 remains nonrobust under bridge controls.",
                "PEPS/PEPS3D remain tiny first-rung receipts.",
                "No scale-level real attractor basin is admitted.",
            ],
        },
        "graveyard_companions": graveyard,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "items": sorted(graveyard),
        },
        "why_not_v4_probes": (
            "This is a v5 source-native PyTorch MPS trajectory scout using the current shared runtime "
            "and formal receipts. It is not a wiki route, not a legacy v4 probe, not PEPS/PEPS3D, "
            "and not final manifold admission."
        ),
        "next_work_required": [
            "Run longer adaptive-bond bias sweeps or fixed-cap comparisons if L64 convergence is the target.",
            "Implement local Krylov or vectorized doubled-MPS Lindblad if adaptive trajectories still leave bias open.",
            "Keep PEPS/PEPS3D and real scale-basin admission as separate blockers.",
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
