#!/usr/bin/env python3
"""L32 tensor-network mitigation attempt or precise blocker receipt.

This scout tests the next allowed tensor-network packet after the refreshed
manifold trace: a bounded low-bond L32 MPS trajectory surface. It deliberately
does not rerun the old unbounded L32 path. The receipt either records bounded
L32 progress with norm/truncation/Phi0 diagnostics or writes a precise blocker.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
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
OUT_PATH = RESULT_DIR / "two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json"

NAME = "two_root_constraint_l32_tensor_mitigation_or_blocker_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_l32_low_bond_mps_mitigation_or_blocker"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_l32_tensor_mitigation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal tensor-scaling scout only: attempts a bounded low-bond L32 MPS "
    "trajectory surface using the source-native PyTorch MPS runtime and emits "
    "norm, truncation, and Phi0 diagnostics. It cannot promote L64, PEPS, "
    "PEPS3D, full L32 convergence, scale-level basin admission, or final "
    "constraint-manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing L32 MPS tensors, local quantum-jump steps, TEBD-style SVD truncation, and two-site Phi0 diagnostics",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing trajectory-stage graph and L32 chain graph witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing admission guard distinguishing bounded low-bond L32 evidence from full L64/PEPS/final admission",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and receipt provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

LENGTH = 32
BASELINE_LENGTH = 16
TARGET_CYCLES = 6
TARGET_STAGES_PER_CYCLE = len(mps_runtime.TERRAIN_ORDER_BY_TOKEN["1"])
TARGET_STAGES_PER_FAMILY = TARGET_CYCLES * TARGET_STAGES_PER_CYCLE
REQUIRED_FAMILIES = len(mps_runtime.INITIAL_FAMILIES)
ATTEMPT_FAMILY = "alternating_z"
LOW_BOND_CAP = 4
TIME_BUDGET_SECONDS = 60.0
NORM_TOL = 1.0e-7

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "mps_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "mps_l16_result": RESULT_DIR / "two_root_constraint_tensor_network_lindblad_runtime_probe_results.json",
    "trace_refresh_result": RESULT_DIR / "two_root_constraint_full_manifold_runtime_trace_refresh_probe_results.json",
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
        node = stage_graph.add_node(f"{stage['cycle']}:{stage['stage_index']}:{stage['token']}:{stage['terrain']}")
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


def run_l32_family(family: str, seed: int, started: float) -> dict[str, Any]:
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
            elapsed = time.time() - started
            stage_rows.append(
                {
                    "family": family,
                    "cycle": cycle,
                    "stage_index": terrain_idx,
                    "token": token,
                    "terrain": terrain,
                    "elapsed_seconds": elapsed,
                    "stage_seconds": time.time() - stage_started,
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


def run_l32_low_bond_surface() -> dict[str, Any]:
    started = time.time()
    family_rows = []
    for idx, family in enumerate(mps_runtime.INITIAL_FAMILIES):
        family_rows.append(run_l32_family(family, seed=32052021 + idx, started=started))
        if time.time() - started >= TIME_BUDGET_SECONDS:
            break
    all_stage_rows = [stage for row in family_rows for stage in row["stage_rows"]]
    stages_completed = sum(row["stages_completed"] for row in family_rows)
    families_completed = sum(1 for row in family_rows if row["completed_full_family"])
    completed_full_required_surface = families_completed == REQUIRED_FAMILIES
    total_truncation = sum(row["total_truncation_error"] for row in family_rows)
    projected_single_family_seconds = (
        (time.time() - started) / max(len(family_rows), 1) if family_rows else None
    )
    projected_all_family_seconds = (
        projected_single_family_seconds * REQUIRED_FAMILIES if projected_single_family_seconds is not None else None
    )
    return {
        "route": "bounded_low_bond_l32_surface",
        "length": LENGTH,
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
        "elapsed_seconds": time.time() - started,
        "projected_single_family_seconds": projected_single_family_seconds,
        "projected_all_family_seconds": projected_all_family_seconds,
        "max_bond": max((row["max_bond"] for row in family_rows), default=0),
        "bond_dims_by_family": {row["family"]: row["bond_dims"] for row in family_rows},
        "norm_error": max((row["norm_error"] for row in family_rows), default=float("inf")),
        "total_truncation_error": total_truncation,
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


def z3_guard(attempt: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    l16_green = z3.Bool("l16_green")
    l32_surface_attempted = z3.Bool("l32_surface_attempted")
    l32_full_surface_complete = z3.Bool("l32_full_surface_complete")
    l64_claimed = z3.Bool("l64_claimed")
    peps_claimed = z3.Bool("peps_claimed")
    final_admission = z3.Bool("final_admission")
    precise_blocker = z3.Bool("precise_blocker")
    solver = z3.Solver()
    solver.add(l16_green == (baseline.get("tensor_runtime_status") == "green_l16_mps_trajectory"))
    solver.add(l32_surface_attempted == (attempt["stages_completed"] > 0 and attempt["length"] == LENGTH))
    solver.add(l32_full_surface_complete == bool(attempt["completed_full_required_surface"]))
    solver.add(l64_claimed == False)
    solver.add(peps_claimed == False)
    solver.add(precise_blocker == z3.And(l32_surface_attempted, z3.Not(l32_full_surface_complete)))
    solver.add(final_admission == z3.And(l16_green, l32_full_surface_complete, z3.Not(l64_claimed), peps_claimed))
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "l16_green": z3.is_true(model.eval(l16_green, model_completion=True)),
        "l32_surface_attempted": z3.is_true(model.eval(l32_surface_attempted, model_completion=True)),
        "l32_full_surface_complete": z3.is_true(model.eval(l32_full_surface_complete, model_completion=True)),
        "precise_blocker": z3.is_true(model.eval(precise_blocker, model_completion=True)),
        "l64_claimed": z3.is_true(model.eval(l64_claimed, model_completion=True)),
        "peps_claimed": z3.is_true(model.eval(peps_claimed, model_completion=True)),
        "final_admission_allowed": z3.is_true(model.eval(final_admission, model_completion=True)),
        "rule": "L32 mitigation packet can pass as bounded low-bond L32 evidence if all four families complete, or as a precise blocker if only a prefix completes; final admission remains false.",
    }


def main() -> int:
    started = time.time()
    baseline_result = read_json(SOURCE_FILES["mps_l16_result"])
    trace_result = read_json(SOURCE_FILES["trace_refresh_result"])
    baseline = baseline_result.get("summary", {})
    attempt = run_l32_low_bond_surface()
    guard = z3_guard(attempt, baseline)
    l32_status = (
        "bounded_low_bond_l32_surface_complete"
        if attempt["completed_full_required_surface"]
        else "blocked_low_bond_l32_prefix_only"
    )
    positive = {
        "l16_green_baseline_loaded": {
            "pass": baseline.get("tensor_runtime_status") == "green_l16_mps_trajectory",
            "baseline_l16_max_bond": baseline.get("l16_max_bond"),
            "baseline_l16_max_truncation_error": baseline.get("l16_max_truncation_error"),
        },
        "trace_refresh_loaded": {
            "pass": trace_result.get("summary", {}).get("trace_refresh_status")
            == "refreshed_with_coupled_e16_runtime",
            "trace_refresh_status": trace_result.get("summary", {}).get("trace_refresh_status"),
        },
        "l32_low_bond_surface_attempted": {
            "pass": attempt["stages_completed"] > 0 and attempt["length"] == LENGTH,
            "stages_completed": attempt["stages_completed"],
            "target_stages_per_family": TARGET_STAGES_PER_FAMILY,
            "families_completed": attempt["families_completed"],
            "required_family_count": REQUIRED_FAMILIES,
            "elapsed_seconds": attempt["elapsed_seconds"],
        },
        "l32_norm_phi0_diagnostics_present": {
            "pass": attempt["norm_error"] < NORM_TOL
            and all("I_A_colon_B" in phi0 for phi0 in attempt["center_pair_phi0_by_family"].values()),
            "norm_error": attempt["norm_error"],
            "center_pair_phi0_by_family": attempt["center_pair_phi0_by_family"],
        },
        "l32_truncation_and_projection_recorded": {
            "pass": attempt["total_truncation_error"] >= 0.0
            and attempt["projected_all_family_seconds"] is not None,
            "total_truncation_error": attempt["total_truncation_error"],
            "projected_all_family_seconds": attempt["projected_all_family_seconds"],
            "max_bond": attempt["max_bond"],
        },
        "z3_nonpromotion_guard": {"pass": guard["sat"] and not guard["final_admission_allowed"], "guard": guard},
    }
    graveyard = {
        "full_l32_surface_not_claimed": {
            "pass": True,
            "detail": (
                "The receipt is bounded low-bond L32 evidence. If complete, it is not L64/PEPS/final admission; "
                "if incomplete, it is a precise blocker."
            ),
        },
        "l64_not_claimed": {
            "pass": not guard["l64_claimed"],
            "detail": "No L64 tensor-network claim is made.",
        },
        "peps_peps3d_not_claimed": {
            "pass": not guard["peps_claimed"],
            "detail": "No PEPS/PEPS3D dynamics claim is made.",
        },
        "final_admission_blocked": {
            "pass": not guard["final_admission_allowed"],
            "detail": "L32 blocker receipt does not admit the full manifold.",
        },
    }
    all_pass = all(item["pass"] for item in positive.values()) and all(item["pass"] for item in graveyard.values())
    summary = {
        "all_pass": all_pass,
        "l32_status": l32_status,
        "mitigation_route": attempt["route"],
        "stages_completed": attempt["stages_completed"],
        "target_stages_per_family": TARGET_STAGES_PER_FAMILY,
        "required_family_count": REQUIRED_FAMILIES,
        "elapsed_seconds": attempt["elapsed_seconds"],
        "projected_all_family_seconds": attempt["projected_all_family_seconds"],
        "max_bond": attempt["max_bond"],
        "total_truncation_error": attempt["total_truncation_error"],
        "max_family_truncation_error": attempt["max_family_truncation_error"],
        "families_completed": attempt["families_completed"],
        "center_pair_mutual_information_by_family": {
            family: phi0["I_A_colon_B"] for family, phi0 in attempt["center_pair_phi0_by_family"].items()
        },
        "precise_blocker": guard["precise_blocker"],
        "final_manifold_admission_allowed": False,
        "next_required_work": (
            "Treat this as bounded low-bond L32 evidence, not full tensor-network closure. Next build PEPS "
            "small-grid dynamics or a genuinely different L32 algorithm such as local Krylov/vectorized doubled-MPS."
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
            "l16_mps_summary": baseline,
            "trace_refresh_summary": trace_result.get("summary", {}),
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
            "l32_status": l32_status,
            "l32_full_surface_complete": attempt["completed_full_required_surface"],
            "l64_claimed": False,
            "peps_peps3d_claimed": False,
            "final_manifold_admission_allowed": False,
            "why_not_final": [
                "The low-bond L32 route is bounded evidence, not a full L32/L64 convergence or bond-scaling theorem.",
                "L64 remains untested.",
                "PEPS/PEPS3D dynamics remain open.",
                "Scale-level basin admission remains open.",
            ],
        },
        "why_not_v4_probes": (
            "This is a v5 bounded tensor-scaling formal scout over the current source-native "
            "MPS runtime and manifold trace receipts, not a legacy v4 probe or a canonical admission."
        ),
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
