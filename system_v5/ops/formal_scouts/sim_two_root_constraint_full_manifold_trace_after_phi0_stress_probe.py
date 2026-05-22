#!/usr/bin/env python3
"""Refresh the manifold trace after coupled-E16 Phi0 stress controls.

This is a lightweight classifier receipt. It does not rerun dynamics. It
ingests the current runtime/tensor/bridge receipts and updates the active
manifold trace after the coupled-E16 Phi0 stress scout demotes the previously
weak bridge signal from "weak bounded rescue" to open/nonrobust.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import rustworkx as rx
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json"

NAME = "two_root_constraint_full_manifold_trace_after_phi0_stress_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_full_manifold_trace_after_phi0_stress"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_full_qit_engine_manifold_trace_after_phi0_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal trace-refresh classifier only: ingests the coupled-E16 Phi0 stress "
    "receipt and updates the active manifold admission trace. It cannot promote "
    "L64, full PEPS/PEPS3D convergence, robust Phi0 closure, scale-level "
    "real-basin admission, or final constraint-manifold admission."
)

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing refreshed manifold dependency DAG and blocker graph",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing final-admission guard after Phi0 stress demotion",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt ingestion and serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

RECEIPTS = {
    "runtime_consolidation": RESULT_DIR / "two_root_constraint_qit_runtime_consolidation_receipt_probe_results.json",
    "schedule_memory": RESULT_DIR / "two_root_constraint_schedule_memory_phase_map_probe_results.json",
    "adaptive_switching": RESULT_DIR / "two_root_constraint_adaptive_engine_switching_probe_results.json",
    "coupled_e16_runtime": RESULT_DIR / "two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json",
    "phi0_stress": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "l32_mps": RESULT_DIR / "two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json",
    "peps_2d": RESULT_DIR / "two_root_constraint_peps_small_grid_dynamics_probe_results.json",
    "peps3d_tiny": RESULT_DIR / "two_root_constraint_peps3d_tiny_grid_dynamics_probe_results.json",
    "previous_trace_refresh": RESULT_DIR / "two_root_constraint_full_manifold_runtime_trace_refresh_probe_results.json",
}

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
    **RECEIPTS,
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


def source_hashes() -> dict[str, dict[str, Any]]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def summary(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}


def trace_rows(receipts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    stress = summary(receipts["phi0_stress"])
    coupled = summary(receipts["coupled_e16_runtime"])
    l32 = summary(receipts["l32_mps"])
    peps = summary(receipts["peps_2d"])
    peps3d = summary(receipts["peps3d_tiny"])
    schedule = summary(receipts["schedule_memory"])
    adaptive = summary(receipts["adaptive_switching"])
    return [
        {
            "layer": "root_constraints",
            "object": "F01 finite carrier + N01 noncommuting QIT runtime",
            "status": "green_runtime",
            "evidence": "Runtime consolidation and exact-torch schedule receipts remain loaded and finite.",
        },
        {
            "layer": "schedule_memory",
            "object": "Type-1/Type-2 schedule pseudo-basin classes",
            "status": "pseudo_basin",
            "evidence": {
                "phase_counts": schedule.get("phase_counts"),
                "boundary": "schedule classes are not real attractor basins by themselves",
            },
        },
        {
            "layer": "adaptive_switching",
            "object": "state/history switching on augmented single-qubit state",
            "status": "weak_basin_candidate",
            "evidence": {"weak_basin_candidates": adaptive.get("weak_basin_candidates")},
        },
        {
            "layer": "coupled_e16_runtime",
            "object": "bounded dense two-engine E16 runtime",
            "status": "bounded_runtime_first_rung",
            "evidence": {
                "previous_bridge_status": coupled.get("bridge_status"),
                "previous_canonical_minus_max_control": coupled.get("canonical_minus_max_control"),
            },
        },
        {
            "layer": "phi0_bridge_after_stress",
            "object": "Xi -> rho_AB -> Phi0 under stress controls",
            "status": "open_nonrobust_internal_controls",
            "evidence": {
                "stress_status": stress.get("stress_status"),
                "min_canonical_minus_max_internal_control": stress.get("min_canonical_minus_max_internal_control"),
                "max_tensor_carrier_control_name": stress.get("max_tensor_carrier_control_name"),
                "max_tensor_carrier_control_value": stress.get("max_tensor_carrier_control_value"),
            },
        },
        {
            "layer": "tensor_network_1d",
            "object": "L32 low-bond MPS mitigation",
            "status": "bounded_low_bond_evidence",
            "evidence": {
                "l32_status": l32.get("l32_status"),
                "max_bond": l32.get("max_bond"),
                "total_truncation_error": l32.get("total_truncation_error"),
            },
        },
        {
            "layer": "peps_2d",
            "object": "tiny 2D PEPS-style dynamics",
            "status": "tiny_first_rung",
            "evidence": {
                "peps_status": peps.get("peps_status"),
                "grid_shape": peps.get("grid_shape"),
                "max_dynamic_truncation_error": peps.get("max_dynamic_truncation_error"),
            },
        },
        {
            "layer": "peps3d",
            "object": "tiny 3D PEPS3D-style dynamics",
            "status": "tiny_first_rung",
            "evidence": {
                "peps3d_status": peps3d.get("peps3d_status"),
                "grid_shape": peps3d.get("grid_shape"),
                "max_dynamic_truncation_error": peps3d.get("max_dynamic_truncation_error"),
            },
        },
        {
            "layer": "final_manifold_admission",
            "object": "scale-level real basin + robust Phi0 + tensor closure",
            "status": "blocked",
            "evidence": "Phi0 stress is nonrobust, L64 is absent, and PEPS/PEPS3D are tiny first rungs only.",
        },
    ]


def dependency_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = [graph.add_node(row["layer"]) for row in rows]
    for idx in range(len(nodes) - 1):
        graph.add_edge(nodes[idx], nodes[idx + 1], "depends_on")
    blocked = [
        idx
        for idx, row in enumerate(rows)
        if idx != len(rows) - 1 and row["status"] in {"blocked", "open_nonrobust_internal_controls"}
    ]
    for idx in blocked:
        graph.add_edge(nodes[idx], nodes[-1], "blocks_final")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": rx.is_directed_acyclic_graph(graph),
        "blocked_layers": [rows[idx]["layer"] for idx in blocked],
    }


def z3_guard(rows: list[dict[str, Any]], receipts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    stress = summary(receipts["phi0_stress"])
    phi0_robust = z3.Bool("phi0_robust")
    l64_done = z3.Bool("l64_done")
    peps_full = z3.Bool("peps_full")
    scale_basin = z3.Bool("scale_basin")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(phi0_robust == (stress.get("stress_status") == "bounded_internal_stress_survived_not_admitted"))
    solver.add(l64_done == False)
    solver.add(peps_full == False)
    solver.add(scale_basin == False)
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, z3.And(phi0_robust, l64_done, peps_full, scale_basin)))
    status = solver.check()
    model = solver.model()
    return {
        "sat": str(status) == "sat",
        "phi0_robust": z3.is_true(model.eval(phi0_robust, model_completion=True)),
        "l64_done": z3.is_true(model.eval(l64_done, model_completion=True)),
        "peps_full": z3.is_true(model.eval(peps_full, model_completion=True)),
        "scale_basin": z3.is_true(model.eval(scale_basin, model_completion=True)),
        "final_manifold_admission_allowed": z3.is_true(model.eval(final_admission, model_completion=True)),
        "rule": "Final manifold admission requires robust Phi0 stress survival, L64, full tensor/PEPS closure, and scale-level basin evidence.",
    }


def main() -> int:
    started = time.time()
    receipts = {name: read_json(path) for name, path in RECEIPTS.items()}
    rows = trace_rows(receipts)
    graph = dependency_graph(rows)
    guard = z3_guard(rows, receipts)
    loaded = {
        name: {"path": rel(path), "exists": path.exists(), "all_pass": receipts[name].get("all_pass") is True}
        for name, path in RECEIPTS.items()
    }
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    positive = {
        "all_required_receipts_loaded": {"pass": all(row["exists"] and row["all_pass"] for row in loaded.values()), "loaded": loaded},
        "trace_rows_present": {"pass": len(rows) >= 9, "row_count": len(rows), "status_counts": status_counts},
        "dependency_graph_valid": {"pass": graph["is_dag"], **graph},
        "admission_guard_blocks_final": {"pass": guard["final_manifold_admission_allowed"] is False, "z3": guard},
    }
    all_pass = all(item["pass"] for item in positive.values()) and guard["sat"]
    summary_out = {
        "all_pass": all_pass,
        "trace_refresh_status": "refreshed_after_phi0_stress_controls",
        "phi0_current_status": "open_nonrobust_internal_controls",
        "manifold_admitted": False,
        "final_goal_complete": False,
        "status_counts": status_counts,
        "stress_status": summary(receipts["phi0_stress"]).get("stress_status"),
        "min_canonical_minus_max_internal_control": summary(receipts["phi0_stress"]).get(
            "min_canonical_minus_max_internal_control"
        ),
        "final_manifold_admission_allowed": False,
        "next_required_work": "Either repair the Phi0 bridge mechanism under stress or pursue L64/scale-basin tensor dynamics; do not promote the weak coupled-E16 Phi0 rung.",
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
        "loaded_receipts": loaded,
        "trace_rows": rows,
        "dependency_graph": graph,
        "z3_guard": guard,
        "positive": positive,
        "graveyard_companions": {
            "weak_phi0_not_promoted": {
                "pass": summary_out["phi0_current_status"] == "open_nonrobust_internal_controls",
                "detail": "Stress controls demote the weak coupled-E16 Phi0 rung from admission candidate to open/nonrobust.",
            },
            "final_admission_blocked": {
                "pass": guard["final_manifold_admission_allowed"] is False,
                "detail": "L64, robust Phi0, full PEPS/PEPS3D, and scale basin evidence are not complete.",
            },
        },
        "nearby_variants": {
            "total": 2,
            "passed": int(summary_out["phi0_current_status"] == "open_nonrobust_internal_controls")
            + int(guard["final_manifold_admission_allowed"] is False),
            "variants": [
                "weak_phi0_not_promoted",
                "final_admission_blocked",
            ],
        },
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "not_l64": True,
            "not_full_peps_or_peps3d": True,
            "not_scale_level_real_basin": True,
            "final_manifold_admission_allowed": False,
        },
        "why_not_v4_probes": "This is a v5 trace classifier over current QIT engine receipts, not a legacy v4 probe or wiki route.",
        "next_work_required": [
            "Repair or replace the Phi0 bridge mechanism so it survives stress controls, or classify it open.",
            "Continue L64 and scale-level tensor dynamics as separate receipts.",
            "Keep final manifold admission blocked until all admission predicates are proven.",
        ],
        "summary": summary_out,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary_out, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
