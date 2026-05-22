#!/usr/bin/env python3
"""Emit the full QIT engine / constraint-manifold runtime trace.

This Workstream F scout consolidates the current QIT engine receipts into one explicit
runtime/admission trace. It does not rerun the heavy dynamics; it checks the
authoritative result JSONs, builds the layer DAG, classifies each layer/status,
and records whether the current evidence admits or blocks the full manifold.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_full_manifold_runtime_trace_probe_results.json"

NAME = "two_root_constraint_full_manifold_runtime_trace_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_full_manifold_trace_and_admission_classifier"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_full_qit_engine_manifold_runtime_trace"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal Workstream F scout only: emits a full runtime/admission trace over "
    "the current QIT engine receipts. It can classify evidence as killed, "
    "open, pseudo, weak-candidate, or green-runtime, but cannot promote "
    "final manifold admission when Phi0 separation or PEPS/PEPS3D/full-scope "
    "evidence is missing."
)

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing layer/runtime DAG construction and acyclicity witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing final admission guard over current QIT receipt predicates and blockers",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt ingestion and trace serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
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
    "A_runtime_consolidation": RESULT_DIR / "two_root_constraint_qit_runtime_consolidation_receipt_probe_results.json",
    "B_schedule_memory_phase": RESULT_DIR / "two_root_constraint_schedule_memory_phase_map_probe_results.json",
    "C_adaptive_switching": RESULT_DIR / "two_root_constraint_adaptive_engine_switching_probe_results.json",
    "D_coupled_e16_phi0_bridge": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_bridge_probe_results.json",
    "E_mps_trajectory_lindblad": RESULT_DIR / "two_root_constraint_tensor_network_lindblad_runtime_probe_results.json",
    "G_mps_phi0_bridge_rescue": RESULT_DIR / "two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe_results.json",
    "H_coupled_e16_slow_mode_bridge": RESULT_DIR
    / "two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json",
}
SOURCE_FILES = {
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
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


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def receipt_summaries(receipts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        name: {
            "path": rel(RECEIPTS[name]),
            "exists": RECEIPTS[name].exists(),
            "all_pass": bool(data.get("all_pass")),
            "claim_ceiling": data.get("claim_ceiling"),
            "summary": data.get("summary", {}),
        }
        for name, data in receipts.items()
    }


def layer_trace(receipts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    b_summary = receipts["B_schedule_memory_phase"].get("summary", {})
    c_summary = receipts["C_adaptive_switching"].get("summary", {})
    d_summary = receipts["D_coupled_e16_phi0_bridge"].get("summary", {})
    e_summary = receipts["E_mps_trajectory_lindblad"].get("summary", {})
    g_summary = receipts["G_mps_phi0_bridge_rescue"].get("summary", {})
    h_summary = receipts["H_coupled_e16_slow_mode_bridge"].get("summary", {})
    return [
        {
            "layer": "L01_two_root_constraints",
            "object": "F01 finite carrier + N01 noncommutation",
            "status": "green_runtime",
            "evidence": "Current QIT scouts preserve finite torch QIT carriers and noncommuting engine/channel order.",
        },
        {
            "layer": "L02_admissibility_ratchet",
            "object": "status ladder and claim ceiling",
            "status": "green_runtime",
            "evidence": "All current QIT receipts are formal_scout, promotion_allowed=false, with explicit claim ceilings.",
        },
        {
            "layer": "L03_qit_runtime_helper",
            "object": "shared exact torch terrain/engine/schedule runtime",
            "status": "green_runtime",
            "evidence": receipts["A_runtime_consolidation"].get("summary", {}),
        },
        {
            "layer": "L04_terrain_placements",
            "object": "Se/Ne/Ni/Si density-law placements on Weyl sheets",
            "status": "green_runtime",
            "evidence": "qit_engine_runtime terrain_stage_channels used by the current QIT build path.",
        },
        {
            "layer": "L05_engine_maps",
            "object": "Type-1/Type-2 engine channels",
            "status": "green_runtime",
            "evidence": "Fixed single-engine maps remain monostable in D90/D95; used as building blocks only.",
        },
        {
            "layer": "L06_schedule_memory",
            "object": "fixed schedule-family classes",
            "status": "pseudo_basin",
            "evidence": {
                "phase_counts": b_summary.get("phase_counts"),
                "nominal_transition_brackets": b_summary.get("nominal_transition_brackets"),
                "boundary": "fixed schedule classes are not real basins for one map",
            },
        },
        {
            "layer": "L07_adaptive_switching",
            "object": "schedule_memory_hysteresis_z piecewise map",
            "status": "weak_basin_candidate",
            "evidence": {
                "weak_basin_candidates": c_summary.get("weak_basin_candidates"),
                "control_reproductions": c_summary.get("control_reproductions"),
                "boundary": "single-qubit augmented-state weak candidate only; no basin-radius, contraction-margin, multiseed, or readout-invariance proof",
            },
        },
        {
            "layer": "L08_coupled_e16_product_bridge",
            "object": "two E=8 adaptive surfaces with two-qubit rho_AB cuts",
            "status": "killed",
            "evidence": {
                "phi0_status": d_summary.get("phi0_status"),
                "coupled_entropy_readout": d_summary.get("coupled_entropy_readout"),
                "z3_phi0_guard": d_summary.get("z3_phi0_guard"),
                "boundary": "product-substrate bridge does not separate Phi0 from controls",
            },
        },
        {
            "layer": "L09_coupled_e16_slow_mode_bridge",
            "object": "dense E=16 runtime with slow-mode bridge gates",
            "status": "weak_bridge_candidate",
            "evidence": {
                "bridge_status": h_summary.get("bridge_status"),
                "bridge_status_note": h_summary.get("bridge_status_note"),
                "canonical_minus_max_control": h_summary.get("canonical_minus_max_control"),
                "max_control_name": h_summary.get("max_control_name"),
                "boundary": "dense E16 slow-mode bridge weakly separates from controls, with type-swap nearly tied; not PEPS/PEPS3D or a final bridge theorem",
            },
        },
        {
            "layer": "L10_mps_lindblad_trajectory",
            "object": "1D MPS quantum trajectory through L=16",
            "status": "green_runtime",
            "evidence": {
                "tensor_runtime_status": e_summary.get("tensor_runtime_status"),
                "dense_l4_replay_error": e_summary.get("dense_l4_replay_error"),
                "l16_max_bond": e_summary.get("l16_max_bond"),
                "l16_max_truncation_error": e_summary.get("l16_max_truncation_error"),
                "l16_cluster_count": e_summary.get("l16_cluster_count"),
            },
        },
        {
            "layer": "L11_mps_phi0_bridge_rescue",
            "object": "MPS trajectory surface -> bridge-level Xi -> rho_AB -> Phi0",
            "status": "open",
            "evidence": {
                "bridge_status": g_summary.get("bridge_status"),
                "case_mean_mutual_information": g_summary.get("case_mean_mutual_information"),
                "z3_rescue_guard": g_summary.get("z3_rescue_guard"),
                "boundary": "canonical MPS bridge is nonzero but not separated from shuffled/type-swap controls",
            },
        },
        {
            "layer": "L12_xi_rhoab_phi0",
            "object": "Xi -> rho_AB -> Phi0 bridge",
            "status": "open",
            "evidence": "Product-substrate Phi0 was killed/near-zero, dense E16 slow-mode bridge weakly separates with a near-tied type-swap control, and MPS bridge rescue remains open/nonzero-but-not-control-separated. This is not closure.",
        },
        {
            "layer": "L13_peps_peps3d_extension",
            "object": "higher-dimensional tensor-network dynamics",
            "status": "open",
            "evidence": "Not attempted in this build path; explicitly deferred until 1D MPS route is stable.",
        },
        {
            "layer": "L14_final_manifold_admission",
            "object": "full geometric constraint manifold admission",
            "status": "open",
            "evidence": "Blocked by cross-carrier Phi0 inconsistency, weak dense-E16 margin, MPS Phi0 nonseparation, missing PEPS/PEPS3D extension, and no final admitted bridge theorem.",
        },
    ]


def dag_report(layers: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = [graph.add_node(layer["layer"]) for layer in layers]
    for idx in range(len(nodes) - 1):
        graph.add_edge(nodes[idx], nodes[idx + 1], "depends_on")
    cycle = rx.is_directed_acyclic_graph(graph)
    return {
        "pass": bool(cycle) and graph.num_nodes() == len(layers) and graph.num_edges() == len(layers) - 1,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": bool(cycle),
        "terminal_layer": layers[-1]["layer"],
    }


def z3_admission_guard(receipts: dict[str, dict[str, Any]], layers: list[dict[str, Any]]) -> dict[str, Any]:
    all_receipts_pass = z3.Bool("all_receipts_pass")
    adaptive_weak_candidate = z3.Bool("adaptive_weak_candidate")
    e_mps_green = z3.Bool("e_mps_green")
    dense_e16_bridge_separates = z3.Bool("dense_e16_bridge_separates")
    mps_phi0_separates = z3.Bool("mps_phi0_separates")
    robust_phi0_separates = z3.Bool("robust_phi0_separates")
    peps_extension = z3.Bool("peps_extension")
    final_trace = z3.Bool("final_trace")
    manifold_admitted = z3.Bool("manifold_admitted")
    g_guard = receipts["G_mps_phi0_bridge_rescue"].get("summary", {}).get("z3_rescue_guard", {})
    h_guard = (
        receipts["H_coupled_e16_slow_mode_bridge"]
        .get("positive", {})
        .get("bridge_status_classified", {})
        .get("z3", {})
    )
    e_status = receipts["E_mps_trajectory_lindblad"].get("summary", {}).get("tensor_runtime_status")
    c_candidates = receipts["C_adaptive_switching"].get("summary", {}).get("weak_basin_candidates", [])
    solver = z3.Solver()
    solver.add(all_receipts_pass == all(bool(data.get("all_pass")) for data in receipts.values()))
    solver.add(adaptive_weak_candidate == ("schedule_memory_hysteresis_z" in c_candidates))
    solver.add(e_mps_green == (e_status == "green_l16_mps_trajectory"))
    solver.add(dense_e16_bridge_separates == bool(h_guard.get("separates_from_controls")))
    solver.add(mps_phi0_separates == bool(g_guard.get("separates_from_controls")))
    solver.add(robust_phi0_separates == z3.And(dense_e16_bridge_separates, mps_phi0_separates))
    solver.add(peps_extension == False)
    solver.add(final_trace == bool(layers))
    solver.add(
        manifold_admitted
        == z3.And(
            all_receipts_pass,
            adaptive_weak_candidate,
            e_mps_green,
            robust_phi0_separates,
            peps_extension,
            final_trace,
        )
    )
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "all_receipts_pass": z3.is_true(model.eval(all_receipts_pass, model_completion=True)),
        "adaptive_weak_candidate": z3.is_true(model.eval(adaptive_weak_candidate, model_completion=True)),
        "e_mps_green": z3.is_true(model.eval(e_mps_green, model_completion=True)),
        "dense_e16_bridge_separates": z3.is_true(model.eval(dense_e16_bridge_separates, model_completion=True)),
        "mps_phi0_separates": z3.is_true(model.eval(mps_phi0_separates, model_completion=True)),
        "robust_phi0_separates": z3.is_true(model.eval(robust_phi0_separates, model_completion=True)),
        "peps_extension": z3.is_true(model.eval(peps_extension, model_completion=True)),
        "final_trace": z3.is_true(model.eval(final_trace, model_completion=True)),
        "manifold_admitted": z3.is_true(model.eval(manifold_admitted, model_completion=True)),
        "rule": "final admission requires all current QIT receipts green, adaptive weak candidate, MPS green, robust cross-carrier Phi0 separation, PEPS/PEPS3D extension, and full trace",
    }


def main() -> int:
    started = time.time()
    receipts = {name: read_json(path) for name, path in RECEIPTS.items()}
    layers = layer_trace(receipts)
    graph = dag_report(layers)
    guard = z3_admission_guard(receipts, layers)
    status_counts: dict[str, int] = {}
    for layer in layers:
        status_counts[layer["status"]] = status_counts.get(layer["status"], 0) + 1
    positive = {
        "all_required_receipts_present": {
            "pass": all(path.exists() for path in RECEIPTS.values()),
            "receipts": {name: rel(path) for name, path in RECEIPTS.items()},
        },
        "all_required_receipts_all_pass": {
            "pass": all(bool(data.get("all_pass")) for data in receipts.values()),
            "all_pass_by_receipt": {name: bool(data.get("all_pass")) for name, data in receipts.items()},
        },
        "trace_dag_valid": graph,
        "required_status_classes_present": {
            "pass": {"pseudo_basin", "weak_basin_candidate", "weak_bridge_candidate", "killed", "open", "green_runtime"}
            <= set(status_counts),
            "status_counts": status_counts,
        },
        "admission_guard_blocks_final_promotion": {
            "pass": not guard["manifold_admitted"],
            "guard": guard,
        },
    }
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "final_goal_complete": False,
        "manifold_admitted": guard["manifold_admitted"],
        "why_not_complete": [
            "Dense E16 slow-mode bridge clears the control margin only weakly, with type-swap nearly tied.",
            "MPS bridge-level Phi0 is nonzero but does not separate from shuffled/type-swap controls.",
            "PEPS/PEPS3D extension is absent.",
            "No final bridge theorem or manifold admission receipt exists.",
        ],
    }
    graveyard = {
        "robust_phi0_separation_not_cleared": {
            "pass": not guard["robust_phi0_separates"],
            "source": rel(RECEIPTS["G_mps_phi0_bridge_rescue"]),
            "detail": "Dense E16 weakly separates, but MPS bridge has nonzero mutual information without shuffled/type-swap separation.",
        },
        "dense_e16_bridge_margin_is_weak": {
            "pass": guard["dense_e16_bridge_separates"] is True and guard["robust_phi0_separates"] is False,
            "source": rel(RECEIPTS["H_coupled_e16_slow_mode_bridge"]),
            "detail": "Dense E16 bridge is useful Workstream 4 runtime evidence, but it is not robust cross-carrier bridge closure.",
        },
        "peps_peps3d_extension_absent": {
            "pass": not guard["peps_extension"],
            "detail": "E is 1D MPS quantum-trajectory evidence, not PEPS/PEPS3D.",
        },
        "final_manifold_not_admitted": {
            "pass": not guard["manifold_admitted"],
            "detail": "This trace classifies the current QIT build state and keeps final admission blocked.",
        },
    }
    nearby_variants = {
        "total": len(graveyard),
        "passed": sum(1 for row in graveyard.values() if row["pass"]),
        "variants": sorted(graveyard),
    }
    next_work_required = boundary["why_not_complete"]
    all_pass = all(item["pass"] for item in positive.values()) and all(item["pass"] for item in graveyard.values())
    summary = {
        "all_pass": all_pass,
        "final_goal_complete": False,
        "manifold_admitted": guard["manifold_admitted"],
        "status_counts": status_counts,
        "admission_guard": guard,
        "interpretation": (
            "Workstream F emits the full current runtime trace over the QIT build path. The "
            "trace has green runtime through the 1D MPS L=16 rung, a bounded "
            "single-qubit adaptive weak-basin candidate, and a dense E16 slow-mode "
            "bridge that weakly separates from controls. Final manifold admission "
            "remains blocked by missing robust cross-carrier Phi0 separation, "
            "MPS bridge-level Phi0 nonseparation from controls, and absent "
            "PEPS/PEPS3D extension."
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
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "receipt_summaries": receipt_summaries(receipts),
        "runtime_trace": layers,
        "dag_report": graph,
        "positive": positive,
        "graveyard_companions": graveyard,
        "nearby_variants": nearby_variants,
        "boundary": boundary,
        "why_not_v4_probes": (
            "This is a v5 Workstream F trace/admission classifier over current "
            "current QIT receipt JSONs; it is not a legacy v4 probe, a rerun of heavy "
            "dynamics, PEPS/PEPS3D execution, Phi0 closure, or final manifold "
            "admission."
        ),
        "next_work_required": next_work_required,
        "blockers": [] if all_pass else [
            name
            for name, item in {**positive, **graveyard}.items()
            if not item.get("pass")
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
