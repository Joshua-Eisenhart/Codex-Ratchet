#!/usr/bin/env python3
"""L64 tensor-network blocker or mitigation receipt.

This scout is the next scale packet after the L32 low-bond MPS first rung.
It attempts an actual L64 source-native PyTorch MPS trajectory route at a
bounded bond cap. The result is deliberately scoped:

- complete prefix/surface => bounded L64 first-rung evidence only;
- incomplete prefix => precise L64 blocker with algorithm, timing, bond,
  truncation, norm, and Phi0 diagnostics.

It is not full L64 convergence, PEPS/PEPS3D evidence, scale-level basin
admission, or final manifold admission.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_l64_tensor_blocker_or_mitigation_probe_results.json"

NAME = "two_root_constraint_l64_tensor_blocker_or_mitigation_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_l64_low_bond_mps_mitigation_or_blocker"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_l64_tensor_blocker_or_mitigation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal tensor-scaling scout only: attempts a bounded low-bond L64 MPS "
    "trajectory route using the source-native PyTorch MPS runtime and emits "
    "norm, truncation, timing, bond, graph, and Phi0 diagnostics. It cannot "
    "promote full L64 convergence, PEPS, PEPS3D, scale-level basin admission, "
    "or final constraint-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing L64 MPS tensors, local quantum-jump steps, TEBD-style SVD truncation, and two-site Phi0 diagnostics",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing L64 chain graph and trajectory-stage graph witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing guard separating bounded L64 first-rung evidence from final tensor/manifold admission",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and receipt provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "statistics": {"tried": True, "used": True, "reason": "supportive stage-timing summary diagnostics"},
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
BASELINE_LENGTH = 32
TARGET_CYCLES = 3
TARGET_STAGES_PER_CYCLE = len(mps_runtime.TERRAIN_ORDER_BY_TOKEN["1"])
TARGET_STAGES_PER_FAMILY = TARGET_CYCLES * TARGET_STAGES_PER_CYCLE
REQUIRED_FAMILIES = len(mps_runtime.INITIAL_FAMILIES)
LOW_BOND_CAP = 4
TIME_BUDGET_SECONDS = 120.0
NORM_TOL = 1.0e-7

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "mps_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "l16_mps_result": RESULT_DIR / "two_root_constraint_tensor_network_lindblad_runtime_probe_results.json",
    "l32_result": RESULT_DIR / "two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json",
    "post_stress_trace_result": RESULT_DIR / "two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
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
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def chain_graph(length: int, stages: list[dict[str, Any]]) -> dict[str, Any]:
    chain = rx.PyGraph()
    nodes = [chain.add_node(idx) for idx in range(length)]
    for idx in range(length - 1):
        chain.add_edge(nodes[idx], nodes[idx + 1], "mps_chain")
    stage_graph = rx.PyDiGraph()
    previous = None
    for stage in stages:
        node = stage_graph.add_node(f"{stage['family']}:{stage['cycle']}:{stage['stage_index']}:{stage['token']}:{stage['terrain']}")
        if previous is not None:
            stage_graph.add_edge(previous, node, "next")
        previous = node
    return {
        "chain_nodes": chain.num_nodes(),
        "chain_edges": chain.num_edges(),
        "stage_nodes": stage_graph.num_nodes(),
        "stage_edges": stage_graph.num_edges(),
        "stage_graph_is_dag": bool(rx.is_directed_acyclic_graph(stage_graph)),
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


def center_pair_phi0_from_mps(mps: mps_runtime.MPS) -> dict[str, float]:
    site = mps.L // 2 - 1
    return mps_runtime.phi0_readout_pair(two_site_density_adjacent(mps, site))


def run_l64_family(family: str, seed: int, started: float) -> dict[str, Any]:
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
            parity = terrain_idx % 2
            stage_truncation = 0.0
            for site in range(parity, LENGTH - 1, 2):
                stage_truncation += mps.apply_two(gate_two, site, max_bond=LOW_BOND_CAP)
                mps.normalize_()
            total_truncation += stage_truncation
            total_jumps += jump_count
            stage_seconds = time.time() - stage_started
            elapsed = time.time() - started
            stage_rows.append(
                {
                    "family": family,
                    "cycle": cycle,
                    "stage_index": terrain_idx,
                    "token": token,
                    "terrain": terrain,
                    "elapsed_seconds": elapsed,
                    "stage_seconds": stage_seconds,
                    "stage_truncation_error": stage_truncation,
                    "total_truncation_error": total_truncation,
                    "jump_count": jump_count,
                    "max_bond": mps.max_bond(),
                    "bond_dims": mps.bond_dims(),
                    "norm_error": abs(float(mps.norm_sq().item()) - 1.0),
                }
            )
            if elapsed >= TIME_BUDGET_SECONDS:
                stop_reason = "time_budget_after_completed_stage"
                break
        if stop_reason != "target_complete":
            break
    phi0 = center_pair_phi0_from_mps(mps)
    return {
        "family": family,
        "seed": seed,
        "stages_completed": len(stage_rows),
        "target_stages": TARGET_STAGES_PER_FAMILY,
        "stop_reason": stop_reason,
        "completed_full_family": len(stage_rows) == TARGET_STAGES_PER_FAMILY,
        "max_bond": mps.max_bond(),
        "bond_dims": mps.bond_dims(),
        "norm_error": abs(float(mps.norm_sq().item()) - 1.0),
        "total_truncation_error": total_truncation,
        "total_jumps": total_jumps,
        "center_pair_phi0": phi0,
        "stage_rows": stage_rows,
    }


def run_l64_low_bond_surface() -> dict[str, Any]:
    started = time.time()
    family_rows = []
    for idx, family in enumerate(mps_runtime.INITIAL_FAMILIES):
        family_rows.append(run_l64_family(family, seed=64052021 + idx, started=started))
        if time.time() - started >= TIME_BUDGET_SECONDS:
            break
    all_stage_rows = [stage for row in family_rows for stage in row["stage_rows"]]
    stages_completed = sum(row["stages_completed"] for row in family_rows)
    families_completed = sum(1 for row in family_rows if row["completed_full_family"])
    completed_full_required_surface = families_completed == REQUIRED_FAMILIES
    elapsed = time.time() - started
    stage_seconds = [row["stage_seconds"] for row in all_stage_rows]
    projected_single_family_seconds = elapsed / max(len(family_rows), 1) if family_rows else None
    projected_all_family_seconds = (
        projected_single_family_seconds * REQUIRED_FAMILIES if projected_single_family_seconds is not None else None
    )
    return {
        "route": "bounded_low_bond_l64_surface",
        "length": LENGTH,
        "baseline_length": BASELINE_LENGTH,
        "attempted_families": [row["family"] for row in family_rows],
        "low_bond_cap": LOW_BOND_CAP,
        "target_cycles": TARGET_CYCLES,
        "target_stages_per_family": TARGET_STAGES_PER_FAMILY,
        "required_family_count": REQUIRED_FAMILIES,
        "time_budget_seconds": TIME_BUDGET_SECONDS,
        "stages_completed": stages_completed,
        "families_completed": families_completed,
        "stop_reason": "target_complete" if completed_full_required_surface else "time_budget_or_incomplete_surface",
        "completed_full_required_surface": completed_full_required_surface,
        "elapsed_seconds": elapsed,
        "projected_single_family_seconds": projected_single_family_seconds,
        "projected_all_family_seconds": projected_all_family_seconds,
        "max_stage_seconds": max(stage_seconds, default=0.0),
        "mean_stage_seconds": statistics.fmean(stage_seconds) if stage_seconds else None,
        "median_stage_seconds": statistics.median(stage_seconds) if stage_seconds else None,
        "max_bond": max((row["max_bond"] for row in family_rows), default=0),
        "bond_dims_by_family": {row["family"]: row["bond_dims"] for row in family_rows},
        "norm_error": max((row["norm_error"] for row in family_rows), default=float("inf")),
        "total_truncation_error": sum(row["total_truncation_error"] for row in family_rows),
        "max_family_truncation_error": max((row["total_truncation_error"] for row in family_rows), default=0.0),
        "total_jumps": sum(row["total_jumps"] for row in family_rows),
        "center_pair_phi0_by_family": {row["family"]: row["center_pair_phi0"] for row in family_rows},
        "family_rows": [
            {key: value for key, value in row.items() if key != "stage_rows"}
            | {"stage_count": len(row["stage_rows"])}
            for row in family_rows
        ],
        "stage_rows": all_stage_rows,
        "graph_report": chain_graph(LENGTH, all_stage_rows),
    }


def z3_guard(attempt: dict[str, Any], l32_summary: dict[str, Any], trace_summary: dict[str, Any]) -> dict[str, Any]:
    l32_first_rung = z3.Bool("l32_first_rung")
    trace_current = z3.Bool("trace_current_after_phi0_stress")
    l64_attempted = z3.Bool("l64_attempted")
    l64_first_rung_complete = z3.Bool("l64_first_rung_complete")
    l64_full_convergence_claimed = z3.Bool("l64_full_convergence_claimed")
    robust_phi0 = z3.Bool("robust_phi0")
    full_peps = z3.Bool("full_peps")
    scale_basin = z3.Bool("scale_basin")
    final_admission = z3.Bool("final_admission")
    precise_blocker = z3.Bool("precise_blocker")
    solver = z3.Solver()
    solver.add(l32_first_rung == (l32_summary.get("l32_status") == "bounded_low_bond_l32_surface_complete"))
    solver.add(trace_current == (trace_summary.get("trace_refresh_status") == "refreshed_after_phi0_stress_controls"))
    solver.add(l64_attempted == (attempt["length"] == LENGTH and attempt["stages_completed"] > 0))
    solver.add(l64_first_rung_complete == bool(attempt["completed_full_required_surface"]))
    solver.add(l64_full_convergence_claimed == False)
    solver.add(robust_phi0 == False)
    solver.add(full_peps == False)
    solver.add(scale_basin == False)
    solver.add(precise_blocker == z3.And(l64_attempted, z3.Not(l64_first_rung_complete)))
    solver.add(
        final_admission
        == z3.And(l32_first_rung, trace_current, l64_full_convergence_claimed, robust_phi0, full_peps, scale_basin)
    )
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "l32_first_rung": z3.is_true(model.eval(l32_first_rung, model_completion=True)),
        "trace_current_after_phi0_stress": z3.is_true(model.eval(trace_current, model_completion=True)),
        "l64_attempted": z3.is_true(model.eval(l64_attempted, model_completion=True)),
        "l64_first_rung_complete": z3.is_true(model.eval(l64_first_rung_complete, model_completion=True)),
        "precise_blocker": z3.is_true(model.eval(precise_blocker, model_completion=True)),
        "l64_full_convergence_claimed": z3.is_true(model.eval(l64_full_convergence_claimed, model_completion=True)),
        "robust_phi0": z3.is_true(model.eval(robust_phi0, model_completion=True)),
        "full_peps": z3.is_true(model.eval(full_peps, model_completion=True)),
        "scale_basin": z3.is_true(model.eval(scale_basin, model_completion=True)),
        "final_admission_allowed": z3.is_true(model.eval(final_admission, model_completion=True)),
        "rule": "L64 low-bond route can pass only as bounded first-rung evidence or a precise blocker; final admission requires robust Phi0, full tensor evidence, and scale basin admission.",
    }


def main() -> int:
    started = time.time()
    l16_result = read_json(SOURCE_FILES["l16_mps_result"])
    l32_result = read_json(SOURCE_FILES["l32_result"])
    trace_result = read_json(SOURCE_FILES["post_stress_trace_result"])
    l16_summary = l16_result.get("summary", {})
    l32_summary = l32_result.get("summary", {})
    trace_summary = trace_result.get("summary", {})
    attempt = run_l64_low_bond_surface()
    guard = z3_guard(attempt, l32_summary, trace_summary)
    l64_status = (
        "bounded_low_bond_l64_first_rung_complete"
        if attempt["completed_full_required_surface"]
        else "blocked_low_bond_l64_prefix_only"
    )
    positive = {
        "l16_green_baseline_loaded": {
            "pass": l16_summary.get("tensor_runtime_status") == "green_l16_mps_trajectory",
            "baseline_l16_max_bond": l16_summary.get("l16_max_bond"),
            "baseline_l16_max_truncation_error": l16_summary.get("l16_max_truncation_error"),
        },
        "l32_first_rung_loaded": {
            "pass": l32_summary.get("l32_status") == "bounded_low_bond_l32_surface_complete",
            "l32_status": l32_summary.get("l32_status"),
            "l32_total_truncation_error": l32_summary.get("total_truncation_error"),
        },
        "post_stress_trace_loaded": {
            "pass": trace_summary.get("trace_refresh_status") == "refreshed_after_phi0_stress_controls",
            "trace_refresh_status": trace_summary.get("trace_refresh_status"),
            "phi0_current_status": trace_summary.get("phi0_current_status"),
        },
        "l64_low_bond_route_attempted": {
            "pass": attempt["stages_completed"] > 0 and attempt["length"] == LENGTH,
            "stages_completed": attempt["stages_completed"],
            "target_stages_per_family": TARGET_STAGES_PER_FAMILY,
            "families_completed": attempt["families_completed"],
            "required_family_count": REQUIRED_FAMILIES,
            "elapsed_seconds": attempt["elapsed_seconds"],
        },
        "l64_norm_phi0_diagnostics_present": {
            "pass": attempt["norm_error"] < NORM_TOL
            and bool(attempt["center_pair_phi0_by_family"])
            and all("I_A_colon_B" in phi0 for phi0 in attempt["center_pair_phi0_by_family"].values()),
            "norm_error": attempt["norm_error"],
            "center_pair_phi0_by_family": attempt["center_pair_phi0_by_family"],
        },
        "l64_timing_bond_truncation_recorded": {
            "pass": attempt["total_truncation_error"] >= 0.0
            and attempt["projected_all_family_seconds"] is not None
            and attempt["max_stage_seconds"] >= 0.0,
            "total_truncation_error": attempt["total_truncation_error"],
            "projected_all_family_seconds": attempt["projected_all_family_seconds"],
            "max_stage_seconds": attempt["max_stage_seconds"],
            "max_bond": attempt["max_bond"],
        },
        "z3_nonpromotion_guard": {"pass": guard["sat"] and not guard["final_admission_allowed"], "guard": guard},
    }
    graveyard = {
        "full_l64_convergence_not_claimed": {
            "pass": not guard["l64_full_convergence_claimed"],
            "detail": "The result is a bounded low-bond L64 route, not a convergence or bond-scaling theorem.",
        },
        "robust_phi0_not_claimed": {
            "pass": not guard["robust_phi0"],
            "detail": "Phi0 remains open/nonrobust after stress controls.",
        },
        "full_peps_not_claimed": {
            "pass": not guard["full_peps"],
            "detail": "PEPS/PEPS3D remain tiny first rungs, not full tensor evidence.",
        },
        "scale_basin_not_claimed": {
            "pass": not guard["scale_basin"],
            "detail": "No scale-level real basin admission is made.",
        },
        "final_admission_blocked": {
            "pass": not guard["final_admission_allowed"],
            "detail": "Final manifold admission remains blocked.",
        },
    }
    all_pass = all(item["pass"] for item in positive.values()) and all(item["pass"] for item in graveyard.values())
    center_mi = {
        family: phi0["I_A_colon_B"] for family, phi0 in attempt["center_pair_phi0_by_family"].items()
    }
    next_algorithm = (
        "If stronger L64 evidence is required, use adaptive bond scaling with a truncation-bias sweep, "
        "local Krylov/trajectory batching, or vectorized doubled-MPS Lindblad. This D=4 route is a bounded first rung."
    )
    summary = {
        "all_pass": all_pass,
        "l64_status": l64_status,
        "mitigation_route": attempt["route"],
        "stages_completed": attempt["stages_completed"],
        "target_stages_per_family": TARGET_STAGES_PER_FAMILY,
        "required_family_count": REQUIRED_FAMILIES,
        "elapsed_seconds": attempt["elapsed_seconds"],
        "projected_all_family_seconds": attempt["projected_all_family_seconds"],
        "max_stage_seconds": attempt["max_stage_seconds"],
        "mean_stage_seconds": attempt["mean_stage_seconds"],
        "median_stage_seconds": attempt["median_stage_seconds"],
        "max_bond": attempt["max_bond"],
        "total_truncation_error": attempt["total_truncation_error"],
        "max_family_truncation_error": attempt["max_family_truncation_error"],
        "families_completed": attempt["families_completed"],
        "center_pair_mutual_information_by_family": center_mi,
        "precise_blocker": guard["precise_blocker"],
        "final_manifold_admission_allowed": False,
        "next_required_work": next_algorithm,
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
            "l16_mps_summary": l16_summary,
            "l32_summary": l32_summary,
            "post_stress_trace_summary": trace_summary,
        },
        "attempt": attempt,
        "positive": positive,
        "graveyard_companions": graveyard,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "variants": sorted(graveyard),
        },
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "l64_status": l64_status,
            "l64_first_rung_complete": attempt["completed_full_required_surface"],
            "l64_full_convergence_claimed": False,
            "robust_phi0_claimed": False,
            "peps_peps3d_full_claimed": False,
            "scale_basin_claimed": False,
            "final_manifold_admission_allowed": False,
            "why_not_final": [
                "The low-bond L64 route is bounded evidence, not a full L64 convergence or bond-scaling theorem.",
                "Phi0 remains open/nonrobust after stress controls.",
                "PEPS/PEPS3D remain tiny first-rung receipts.",
                "Scale-level basin admission remains open.",
            ],
        },
        "why_not_v4_probes": (
            "This is a v5 bounded tensor-scaling formal scout over the current source-native "
            "MPS runtime, L32 first-rung receipt, and post-stress trace, not a legacy v4 probe "
            "or a canonical admission."
        ),
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
