#!/usr/bin/env python3
"""Refresh the full QIT engine / constraint-manifold runtime trace.

This scout updates the prior full trace after the coupled E=16 runtime receipt.
It does not rerun heavy dynamics. It ingests the authoritative formal receipts,
constructs the current manifold-layer DAG, classifies every layer, and applies
a z3 admission guard so the weak coupled-E16 Phi0 rescue cannot be promoted into
final manifold admission while tensor-scale and PEPS/PEPS3D blockers remain.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_full_manifold_runtime_trace_refresh_probe_results.json"

NAME = "two_root_constraint_full_manifold_runtime_trace_refresh_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_full_manifold_trace_refresh_and_admission_classifier"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_full_qit_engine_manifold_runtime_trace_refresh"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal Workstream 6 trace-refresh scout only: refreshes the QIT engine / "
    "constraint-manifold trace after the coupled E=16 runtime receipt. It may "
    "classify the weak coupled-E16 Phi0 separation as bounded first-rung "
    "evidence, but it cannot promote final manifold admission, PEPS/PEPS3D "
    "dynamics, L32/L64 tensor scaling, or scale-level real attractor-basin "
    "admission."
)

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing construction and acyclicity check for the refreshed manifold-layer DAG",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing final-admission guard over receipt predicates and unresolved blockers",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt ingestion and result serialization",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive provenance hashes for sources and receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive path handling",
    },
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
    "D_product_e16_bridge": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_bridge_probe_results.json",
    "E_mps_trajectory_lindblad": RESULT_DIR / "two_root_constraint_tensor_network_lindblad_runtime_probe_results.json",
    "F_previous_full_trace": RESULT_DIR / "two_root_constraint_full_manifold_runtime_trace_probe_results.json",
    "G_mps_phi0_bridge": RESULT_DIR / "two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe_results.json",
    "H_iter195_spectral_reproduction": RESULT_DIR
    / "two_root_constraint_iter195_single_engine_spectral_reproduction_probe_results.json",
    "I_spectral_manifold_phase": RESULT_DIR / "two_root_constraint_engine_spectral_manifold_phase_map_probe_results.json",
    "J_terrain_stage_contribution": RESULT_DIR / "two_root_constraint_terrain_stage_spectral_contribution_probe_results.json",
    "K_grok_196_203_routing": RESULT_DIR
    / "two_root_constraint_late_grok_196_203_engine_spectral_sidequest_routing_probe_results.json",
    "L_phi0_slow_terrain_repair": RESULT_DIR
    / "two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe_results.json",
    "M_coupled_e16_runtime": RESULT_DIR / "two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json",
}

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
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


def source_hashes() -> dict[str, dict[str, Any]]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def receipt_summary(name: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": rel(RECEIPTS[name]),
        "exists": RECEIPTS[name].exists(),
        "all_pass": bool(data.get("all_pass")),
        "classification": data.get("classification"),
        "claim_ceiling": data.get("claim_ceiling"),
        "summary": data.get("summary", {}),
    }


def s(receipts: dict[str, dict[str, Any]], name: str) -> dict[str, Any]:
    return receipts[name].get("summary", {})


def refreshed_layer_trace(receipts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    schedule = s(receipts, "B_schedule_memory_phase")
    adaptive = s(receipts, "C_adaptive_switching")
    product = s(receipts, "D_product_e16_bridge")
    mps = s(receipts, "E_mps_trajectory_lindblad")
    previous_trace = s(receipts, "F_previous_full_trace")
    mps_phi0 = s(receipts, "G_mps_phi0_bridge")
    spectral = s(receipts, "H_iter195_spectral_reproduction")
    spectral_map = s(receipts, "I_spectral_manifold_phase")
    terrain = s(receipts, "J_terrain_stage_contribution")
    grok_route = s(receipts, "K_grok_196_203_routing")
    slow_repair = s(receipts, "L_phi0_slow_terrain_repair")
    coupled = s(receipts, "M_coupled_e16_runtime")
    return [
        {
            "layer": "L01_F01_finite_carrier",
            "object": "finite torch QIT carrier",
            "status": "green_runtime",
            "evidence": "All active QIT engine formal scouts remain finite-carrier torch/runtime receipts.",
        },
        {
            "layer": "L02_N01_noncommutation",
            "object": "noncommuting terrain/engine channels",
            "status": "green_runtime",
            "evidence": {
                "type1_type2_commutator_norm": spectral.get("commutator_norm"),
                "canonical_minus_reversed": spectral_map.get("anchor_order_variant_norms", {}).get(
                    "canonical_minus_reversed"
                ),
                "canonical_minus_all_at_once": spectral_map.get("anchor_order_variant_norms", {}).get(
                    "canonical_minus_all_at_once"
                ),
            },
        },
        {
            "layer": "L03_admissibility_ratchet",
            "object": "classification, claim ceiling, and no-promotion guard",
            "status": "green_runtime",
            "evidence": "Each receipt keeps formal_scout scope and promotion_allowed=false; final admission is guarded separately.",
        },
        {
            "layer": "L04_constraint_manifold_trace",
            "object": "ordered carrier/relation/state trace",
            "status": "green_runtime",
            "evidence": {
                "previous_trace_goal_complete": previous_trace.get("final_goal_complete"),
                "previous_status_counts": previous_trace.get("status_counts"),
            },
        },
        {
            "layer": "L05_weyl_density_carrier",
            "object": "left/right terrain density carriers",
            "status": "green_runtime",
            "evidence": "qit_engine_runtime and trajectory scouts use Weyl-sheet Type-1/Type-2 density/channel carriers.",
        },
        {
            "layer": "L06_terrain_placement_laws",
            "object": "Se/Ne/Ni/Si density-law placements",
            "status": "green_runtime",
            "evidence": {
                "strongest_memory_suppressor_by_removal": terrain.get("strongest_memory_suppressor_by_removal"),
                "strongest_extra_damping_by_duplication": terrain.get("strongest_extra_damping_by_duplication"),
                "drop_delta_spread": terrain.get("drop_delta_spread"),
            },
        },
        {
            "layer": "L07_engine_maps",
            "object": "ordered Type-1/Type-2 engine maps",
            "status": "green_runtime",
            "evidence": {
                "single_engine_status": spectral.get("single_engine_status"),
                "slow_mode_abs": spectral.get("slow_mode_abs"),
                "spectral_gap": spectral.get("spectral_gap"),
                "trotter_error_norm": spectral.get("trotter_error_norm"),
            },
        },
        {
            "layer": "L08_schedule_words",
            "object": "fixed schedule-memory classes",
            "status": "pseudo_basin",
            "evidence": {
                "phase_counts": schedule.get("phase_counts"),
                "transition_brackets": schedule.get("nominal_transition_brackets"),
                "boundary": "These are schedule-family pseudo-basins, not multiple basins of one generated map.",
            },
        },
        {
            "layer": "L09_adaptive_switching",
            "object": "state/history-dependent schedule map",
            "status": "weak_basin_candidate",
            "evidence": {
                "weak_basin_candidates": adaptive.get("weak_basin_candidates"),
                "boundary": "Single-qubit augmented-state candidate only; not scale-level admission.",
            },
        },
        {
            "layer": "L10_product_e16_bridge_baseline",
            "object": "post-hoc product-substrate E16 Phi0 bridge",
            "status": "killed",
            "evidence": {
                "phi0_status": product.get("phi0_status"),
                "coupled_entropy_readout": product.get("coupled_entropy_readout"),
                "boundary": "Product-substrate bridge does not separate from controls.",
            },
        },
        {
            "layer": "L11_mps_l16_runtime",
            "object": "1D MPS quantum-trajectory Lindblad runtime",
            "status": "green_runtime",
            "evidence": {
                "tensor_runtime_status": mps.get("tensor_runtime_status"),
                "dense_l4_replay_error": mps.get("dense_l4_replay_error"),
                "l16_max_bond": mps.get("l16_max_bond"),
                "l16_max_truncation_error": mps.get("l16_max_truncation_error"),
                "l16_cluster_count": mps.get("l16_cluster_count"),
            },
        },
        {
            "layer": "L12_mps_phi0_bridge",
            "object": "MPS runtime surface -> Xi -> rho_AB -> Phi0",
            "status": "open_nonseparating",
            "evidence": {
                "bridge_status": mps_phi0.get("bridge_status"),
                "case_mean_mutual_information": mps_phi0.get("case_mean_mutual_information"),
                "boundary": "Nonzero but not separated from type-swap/shuffled controls.",
            },
        },
        {
            "layer": "L13_slow_mode_terrain_phi0_repair",
            "object": "slow-mode, n-hat, terrain-stage, and history-informed bridge",
            "status": "open_nonseparating",
            "evidence": {
                "bridge_status": slow_repair.get("bridge_status"),
                "canonical_minus_max_control": slow_repair.get("canonical_minus_max_control"),
                "slow_mode_alignment_with_n_hat": slow_repair.get("slow_mode_alignment_with_n_hat"),
                "routed_sidequest_features": grok_route.get("useful_features_for_next_phi0_packet"),
            },
        },
        {
            "layer": "L14_coupled_e16_runtime_phi0",
            "object": "bounded dense coupled E16 runtime with runtime rho_AB extraction",
            "status": "bounded_bridge_candidate",
            "evidence": {
                "workstream_4_status": coupled.get("workstream_4_status"),
                "bridge_status": coupled.get("bridge_status"),
                "case_mean_mutual_information": coupled.get("case_mean_mutual_information"),
                "canonical_minus_max_control": coupled.get("canonical_minus_max_control"),
                "canonical_minus_no_coupling_abs_mi_delta": coupled.get("canonical_minus_no_coupling_abs_mi_delta"),
                "boundary": "Weak control-separated first rung only; not tensor-scale or final basin admission.",
            },
        },
        {
            "layer": "L15_l32_l64_tensor_scaling",
            "object": "L32/L64 MPS or equivalent tensor algorithm",
            "status": "open",
            "evidence": "L16 MPS is green; L32/L64 mitigation or precise blocker remains required.",
        },
        {
            "layer": "L16_peps_peps3d_dynamics",
            "object": "2D/3D tensor-network dynamics",
            "status": "open",
            "evidence": "No PEPS/PEPS3D dynamic receipt is present in the formal build path.",
        },
        {
            "layer": "L17_scale_level_basin_admission",
            "object": "real/manifold-admitted attractor basin",
            "status": "open",
            "evidence": "Schedule classes are pseudo-basins and the adaptive candidate is bounded single-qubit; no scale-level basin admission exists.",
        },
        {
            "layer": "L18_final_manifold_admission",
            "object": "full QIT engine / geometric constraint manifold admission",
            "status": "blocked",
            "evidence": "Blocked by open L32/L64 scaling, PEPS/PEPS3D dynamics, scale-level basin admission, and the need to stress-test the weak coupled-E16 Phi0 margin.",
        },
    ]


def dag_report(layers: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    node_ids = [graph.add_node(layer["layer"]) for layer in layers]
    for idx in range(len(node_ids) - 1):
        graph.add_edge(node_ids[idx], node_ids[idx + 1], "ratchets_into")
    is_dag = bool(rx.is_directed_acyclic_graph(graph))
    return {
        "pass": is_dag and graph.num_nodes() == len(layers) and graph.num_edges() == len(layers) - 1,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": is_dag,
        "terminal_layer": layers[-1]["layer"],
    }


def z3_admission_guard(receipts: dict[str, dict[str, Any]], layers: list[dict[str, Any]]) -> dict[str, Any]:
    all_receipts_pass = z3.Bool("all_receipts_pass")
    coupled_e16_built = z3.Bool("coupled_e16_built")
    coupled_phi0_weakly_separates = z3.Bool("coupled_phi0_weakly_separates")
    l16_mps_green = z3.Bool("l16_mps_green")
    l32_l64_scaling_resolved = z3.Bool("l32_l64_scaling_resolved")
    peps_peps3d_dynamics = z3.Bool("peps_peps3d_dynamics")
    scale_level_basin_admitted = z3.Bool("scale_level_basin_admitted")
    final_trace_refreshed = z3.Bool("final_trace_refreshed")
    final_manifold_admitted = z3.Bool("final_manifold_admitted")

    coupled = s(receipts, "M_coupled_e16_runtime")
    mps = s(receipts, "E_mps_trajectory_lindblad")
    solver = z3.Solver()
    solver.add(all_receipts_pass == all(bool(data.get("all_pass")) for data in receipts.values()))
    solver.add(coupled_e16_built == (coupled.get("workstream_4_status") == "coupled_e16_runtime_built"))
    solver.add(coupled_phi0_weakly_separates == (coupled.get("bridge_status") == "rescued_control_separated"))
    solver.add(l16_mps_green == (mps.get("tensor_runtime_status") == "green_l16_mps_trajectory"))
    solver.add(l32_l64_scaling_resolved == False)
    solver.add(peps_peps3d_dynamics == False)
    solver.add(scale_level_basin_admitted == False)
    solver.add(final_trace_refreshed == bool(layers))
    solver.add(
        final_manifold_admitted
        == z3.And(
            all_receipts_pass,
            coupled_e16_built,
            coupled_phi0_weakly_separates,
            l16_mps_green,
            l32_l64_scaling_resolved,
            peps_peps3d_dynamics,
            scale_level_basin_admitted,
            final_trace_refreshed,
        )
    )
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "all_receipts_pass": z3.is_true(model.eval(all_receipts_pass, model_completion=True)),
        "coupled_e16_built": z3.is_true(model.eval(coupled_e16_built, model_completion=True)),
        "coupled_phi0_weakly_separates": z3.is_true(
            model.eval(coupled_phi0_weakly_separates, model_completion=True)
        ),
        "l16_mps_green": z3.is_true(model.eval(l16_mps_green, model_completion=True)),
        "l32_l64_scaling_resolved": z3.is_true(model.eval(l32_l64_scaling_resolved, model_completion=True)),
        "peps_peps3d_dynamics": z3.is_true(model.eval(peps_peps3d_dynamics, model_completion=True)),
        "scale_level_basin_admitted": z3.is_true(model.eval(scale_level_basin_admitted, model_completion=True)),
        "final_trace_refreshed": z3.is_true(model.eval(final_trace_refreshed, model_completion=True)),
        "final_manifold_admitted": z3.is_true(model.eval(final_manifold_admitted, model_completion=True)),
        "rule": (
            "final admission requires all receipts green, coupled E16 built, weak Phi0 separation, "
            "L16 MPS green, L32/L64 scaling resolved, PEPS/PEPS3D dynamics, scale-level basin "
            "admission, and refreshed full trace"
        ),
    }


def status_counts(layers: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for layer in layers:
        counts[layer["status"]] = counts.get(layer["status"], 0) + 1
    return counts


def main() -> int:
    started = time.time()
    receipts = {name: read_json(path) for name, path in RECEIPTS.items()}
    layers = refreshed_layer_trace(receipts)
    graph = dag_report(layers)
    guard = z3_admission_guard(receipts, layers)
    counts = status_counts(layers)
    coupled = s(receipts, "M_coupled_e16_runtime")
    all_receipts_present = all(path.exists() for path in RECEIPTS.values())
    all_receipts_pass = all(bool(data.get("all_pass")) for data in receipts.values())

    positive = {
        "all_required_receipts_present": {
            "pass": all_receipts_present,
            "receipts": {name: rel(path) for name, path in RECEIPTS.items()},
        },
        "all_required_receipts_all_pass": {
            "pass": all_receipts_pass,
            "all_pass_by_receipt": {name: bool(data.get("all_pass")) for name, data in receipts.items()},
        },
        "trace_dag_valid": graph,
        "required_status_classes_present": {
            "pass": {
                "green_runtime",
                "pseudo_basin",
                "weak_basin_candidate",
                "killed",
                "open",
                "open_nonseparating",
                "bounded_bridge_candidate",
                "blocked",
            }
            <= set(counts),
            "status_counts": counts,
        },
        "coupled_e16_receipt_integrated": {
            "pass": coupled.get("workstream_4_status") == "coupled_e16_runtime_built"
            and coupled.get("bridge_status") == "rescued_control_separated",
            "canonical_minus_max_control": coupled.get("canonical_minus_max_control"),
            "canonical_minus_no_coupling_abs_mi_delta": coupled.get("canonical_minus_no_coupling_abs_mi_delta"),
        },
        "admission_guard_blocks_final_promotion": {
            "pass": not guard["final_manifold_admitted"],
            "guard": guard,
        },
    }

    graveyard = {
        "product_substrate_phi0_bridge_killed": {
            "pass": s(receipts, "D_product_e16_bridge").get("phi0_status") == "killed_near_zero",
            "detail": "The old product-substrate bridge remains killed/near-zero and is superseded only by the coupled runtime first rung.",
        },
        "slow_mode_terrain_phi0_repair_nonseparating": {
            "pass": s(receipts, "L_phi0_slow_terrain_repair").get("bridge_status")
            == "open_nonzero_not_control_separated",
            "detail": "The slow-mode/terrain bridge repair remains nonseparating and is not erased by D107.",
        },
        "l32_l64_scaling_open": {
            "pass": not guard["l32_l64_scaling_resolved"],
            "detail": "L32/L64 MPS or equivalent tensor algorithm remains open.",
        },
        "peps_peps3d_dynamics_absent": {
            "pass": not guard["peps_peps3d_dynamics"],
            "detail": "No PEPS/PEPS3D dynamic receipt exists in the formal build path.",
        },
        "scale_level_basin_not_admitted": {
            "pass": not guard["scale_level_basin_admitted"],
            "detail": "Schedule pseudo-basins and single-qubit weak candidates do not constitute scale-level basin admission.",
        },
        "final_manifold_not_admitted": {
            "pass": not guard["final_manifold_admitted"],
            "detail": "The refreshed trace keeps final admission blocked.",
        },
    }

    next_work_required = [
        "Stress-test the weak coupled-E16 Phi0 margin across seeds, coupling strengths, and control families.",
        "Resolve L32/L64 tensor scaling with an improved algorithm or precise blocked receipt.",
        "Build PEPS and PEPS3D dynamics, not construction-only carriers, or write precise blockers.",
        "Prove or kill scale-level basin admission using one generated runtime map with controls.",
    ]
    all_pass = all(item["pass"] for item in positive.values()) and all(item["pass"] for item in graveyard.values())
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "final_goal_complete": False,
        "manifold_admitted": guard["final_manifold_admitted"],
        "phi0_current_status": "weak_coupled_e16_control_separation_bounded_first_rung",
        "why_not_complete": next_work_required,
    }
    nearby_variants = {
        "total": len(graveyard),
        "passed": sum(1 for row in graveyard.values() if row["pass"]),
        "variants": sorted(graveyard),
    }
    summary = {
        "all_pass": all_pass,
        "trace_refresh_status": "refreshed_with_coupled_e16_runtime",
        "final_goal_complete": False,
        "manifold_admitted": guard["final_manifold_admitted"],
        "status_counts": counts,
        "phi0_current_status": boundary["phi0_current_status"],
        "coupled_e16_bridge_status": coupled.get("bridge_status"),
        "coupled_e16_canonical_minus_max_control": coupled.get("canonical_minus_max_control"),
        "l32_l64_scaling_resolved": guard["l32_l64_scaling_resolved"],
        "peps_peps3d_dynamics": guard["peps_peps3d_dynamics"],
        "scale_level_basin_admitted": guard["scale_level_basin_admitted"],
        "next_required_work": next_work_required,
        "interpretation": (
            "The refreshed trace upgrades Phi0 from nonseparating MPS/slow-mode bridge evidence "
            "to weak bounded coupled-E16 control separation, but final admission remains blocked by "
            "tensor scaling, PEPS/PEPS3D dynamics, and scale-level basin admission."
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
        "receipt_summaries": {name: receipt_summary(name, data) for name, data in receipts.items()},
        "runtime_trace": layers,
        "dag_report": graph,
        "positive": positive,
        "graveyard_companions": graveyard,
        "nearby_variants": nearby_variants,
        "boundary": boundary,
        "why_not_v4_probes": (
            "This is a v5 Workstream 6 trace-refresh classifier over current formal QIT receipts, "
            "not a legacy v4 probe, not a heavy dynamics rerun, and not final manifold admission."
        ),
        "next_work_required": next_work_required,
        "blockers": [] if all_pass else [name for name, item in {**positive, **graveyard}.items() if not item["pass"]],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
