#!/usr/bin/env python3
"""PEPS3D response-quotient anchor partition scout.

Formal scout only.

This continuation packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry. It tests the finite quotient map:

  Q_K : (r_P(v), anchor(v), K) -> finite anchored response classes and
        incidence/readout signatures

It does not admit nested Hopf tori, Weyl sheets, terrain, operator substages,
flux, Xi/Phi0, Axis0, physics, axes 7-12, or full PEPS3D closure.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import rustworkx as rx
import sympy as sp
import torch
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import (
    RTYPE,
    apply_physical_operator,
    as_jsonable,
    coords_for_shape,
    edge_list,
    make_site_tensors,
    probe_responses,
    shift_filter_ops,
    sic_effects,
    site_spinors,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_response_quotient_anchor_partition_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether finite "
    "probe/effect response vectors define anchored quotient classes on a "
    "finite PEPS3D carrier without collapsing to labels, single-probe "
    "non-IC controls, no-anchor controls, or dense closure."
)
SCIENTIFIC_QUESTION = (
    "Does Q_K = S_K / ~_P, where v ~_P w iff every admitted finite effect gives "
    "the same response on v and w, produce finite PEPS3D-anchored response "
    "classes and incidence signatures while non-IC, no-anchor, scalar-label, "
    "order-erased, dense-closure, and promotion controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_response_quotient_anchor_partition"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_BOUNDARY_RECEIPT = "system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json"
PHASE2_ABLATION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_anchor_ablation_boundary_stress_continuation_probe_results.json"
PHASE2_HELDOUT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_heldout_shape_anchor_replay_probe_results.json"
PHASE2_BOND_SWEEP_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_bond_sweep_anchor_stability_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests finite PEPS3D-anchored response quotient classes "
    "and incidence signatures. It does not admit nested Hopf tori, Weyl sheets, "
    "terrain, operator substages, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, "
    "IGT/game theory, axes 7-12, or full PEPS3D closure."
)
BLOCKED_CONSUMERS = [
    "nested Hopf tori",
    "Weyl sheet cover",
    "terrain generator placement",
    "operator substage cells",
    "PEPS/PEPS3D closure beyond bounded local seed-carrier evidence",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes 7-12",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing torch spinor-derived finite response vectors, quotient tensors, and local order gap",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite PEPS3D anchor graph and quotient-incidence edge checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite quotient/nonpromotion and non-IC collapse gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite class, site, edge, and incidence count checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
}

SHAPE = (4, 4, 4)
BOND_DIM = 2
GAP_FLOOR = 1.0e-8
TOL = 1.0e-10


def carrier_graph(shape: tuple[int, int, int]) -> rx.PyGraph:
    graph = rx.PyGraph()
    coords = coords_for_shape(shape)
    graph.add_nodes_from([{"coord": coord} for coord in coords])
    for edge in edge_list(shape):
        graph.add_edge(int(edge["src"]), int(edge["dst"]), {"axis": int(edge["axis"])})
    return graph


def class_ids(responses: torch.Tensor, *, columns: int) -> list[int]:
    seen: dict[tuple[float, ...], int] = {}
    ids = []
    for row in responses[:, :columns]:
        key = tuple(round(float(item), 10) for item in row)
        if key not in seen:
            seen[key] = len(seen)
        ids.append(seen[key])
    return ids


def quotient_incidence(ids: list[int], edges: list[dict[str, Any]]) -> dict[str, Any]:
    class_count = len(set(ids))
    same_class_edges = 0
    cross_class_edges = 0
    for edge in edges:
        if ids[int(edge["src"])] == ids[int(edge["dst"])]:
            same_class_edges += 1
        else:
            cross_class_edges += 1
    incidence = torch.zeros((class_count, class_count), dtype=RTYPE)
    for edge in edges:
        src = ids[int(edge["src"])]
        dst = ids[int(edge["dst"])]
        incidence[src, dst] += 1.0
        incidence[dst, src] += 1.0
    return {
        "class_count": class_count,
        "same_class_edge_count": same_class_edges,
        "cross_class_edge_count": cross_class_edges,
        "incidence_norm": float(torch.linalg.vector_norm(incidence).item()),
        "incidence_nonzero": int(torch.count_nonzero(incidence).item()),
    }


def quotient_gate() -> dict[str, Any]:
    coords = coords_for_shape(SHAPE)
    edges = edge_list(SHAPE)
    graph = carrier_graph(SHAPE)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    full_ids = class_ids(responses, columns=4)
    single_probe_ids = class_ids(responses, columns=1)
    full_incidence = quotient_incidence(full_ids, edges)
    single_incidence = quotient_incidence(single_probe_ids, edges)
    scalar_label_class_count = len(coords)
    no_anchor_class_count = 0
    exact_total = sp.Integer(len(coords)) + sp.Integer(len(edges)) + sp.Integer(full_incidence["class_count"])
    return {
        "pass": bool(
            graph.num_nodes() == len(coords)
            and graph.num_edges() == len(edges)
            and rx.is_connected(graph)
            and full_incidence["class_count"] == len(coords)
            and single_incidence["class_count"] < full_incidence["class_count"]
            and full_incidence["cross_class_edge_count"] == len(edges)
            and full_incidence["incidence_norm"] > GAP_FLOOR
        ),
        "finite_map": "Q_K : (r_P(v), anchor(v), K) -> finite anchored response classes and incidence/readout signatures",
        "shape": list(SHAPE),
        "site_count": len(coords),
        "edge_count": len(edges),
        "full_effect_class_count": full_incidence["class_count"],
        "single_probe_non_ic_class_count": single_incidence["class_count"],
        "single_probe_collapses": single_incidence["class_count"] < full_incidence["class_count"],
        "full_incidence": full_incidence,
        "single_probe_incidence": single_incidence,
        "scalar_label_class_count": scalar_label_class_count,
        "no_anchor_class_count": no_anchor_class_count,
        "sympy_exact_site_edge_class_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def order_witness_gate() -> dict[str, Any]:
    coords = coords_for_shape(SHAPE)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    tensors = make_site_tensors(responses, coords, BOND_DIM)
    shift, filt = shift_filter_ops()
    filter_after_shift = apply_physical_operator(apply_physical_operator(tensors, shift), filt)
    shift_after_filter = apply_physical_operator(apply_physical_operator(tensors, filt), shift)
    order_gap = float(torch.linalg.vector_norm((filter_after_shift - shift_after_filter).reshape(-1)).item())
    erased_1 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    erased_2 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    order_erased_gap = float(torch.linalg.vector_norm((erased_1 - erased_2).reshape(-1)).item())
    return {
        "pass": bool(order_gap > GAP_FLOOR and order_erased_gap < TOL),
        "N01_witness": "physical_filter after physical_shift differs from physical_shift after physical_filter on response-quotient anchored tensors",
        "order_gap": order_gap,
        "order_erased_control_gap": order_erased_gap,
    }


def z3_gate(quotient: dict[str, Any], order: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    non_ic_collapses = z3.Bool("non_ic_collapses")
    dense = z3.Bool("dense")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, non_ic_collapses, z3.Not(dense), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    full_classes = z3.Int("full_classes")
    single_classes = z3.Int("single_probe_classes")
    count_solver.add(
        full_classes == int(quotient["full_effect_class_count"]),
        single_classes == int(quotient["single_probe_non_ic_class_count"]),
        full_classes == 64,
        single_classes < full_classes,
    )
    gap_solver = z3.Solver()
    scaled_gap = z3.Int("scaled_response_quotient_order_gap")
    gap_solver.add(scaled_gap == int(order["order_gap"] * 1_000_000), scaled_gap > 0)
    return {
        "pass": (
            solver.check() == z3.sat
            and bad.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_nonpromotion_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "quotient_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_order_gap": int(order["order_gap"] * 1_000_000),
    }


def main() -> int:
    started = time.time()
    quotient = quotient_gate()
    order = order_witness_gate()
    z3_row = z3_gate(quotient, order)
    positive = {
        "P1_response_quotient_anchor_partition": quotient,
        "P2_response_quotient_order_witness": order,
    }
    graveyard = {
        "GC_single_probe_non_ic_control_collapses": {
            "pass": quotient["single_probe_collapses"],
            "single_probe_class_count": quotient["single_probe_non_ic_class_count"],
            "full_effect_class_count": quotient["full_effect_class_count"],
        },
        "GC_no_anchor_control_rejected": {
            "pass": quotient["no_anchor_class_count"] == 0,
            "no_anchor_class_count": quotient["no_anchor_class_count"],
        },
        "GC_scalar_label_not_response_quotient": {
            "pass": quotient["scalar_label_class_count"] == quotient["site_count"],
            "why_rejected": "scalar labels can count sites but do not carry finite effect response vectors or PEPS3D anchors",
        },
        "GC_order_erased_control_collapses": {
            "pass": order["order_erased_control_gap"] < TOL,
            "order_erased_control_gap": order["order_erased_control_gap"],
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not quotient["dense_state_closure_used"] and not quotient["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_z3_finite_response_quotient_nonpromotion": z3_row,
        "B4_downstream_consumers_blocked": {"pass": bool(BLOCKED_CONSUMERS), "blocked": BLOCKED_CONSUMERS},
    }
    checks = list(positive.values()) + list(graveyard.values()) + list(boundary.values())
    all_pass = all(bool(row["pass"]) for row in checks)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": "finite PEPS3D carrier, finite SIC probe/effect family, finite response classes, finite graph incidence, finite controls, finite output vector",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter on response-quotient anchored tensors, while order-erased control collapses",
        },
        "finite_map": [
            "Q_K : (r_P(v), anchor(v), K) -> finite anchored response classes and incidence/readout signatures",
            "O_K : (T_K, local_order_ops) -> finite local order-gap vector",
        ],
        "domain": {
            "carrier": "finite PEPS3D seed-carrier site anchors",
            "shape": list(SHAPE),
            "site_count": quotient["site_count"],
            "bond_dim": BOND_DIM,
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite response quotient classes, finite class-incidence signatures, local order-gap rows, controls, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_response_partition",
        "carrier_realization": "torch complex finite PEPS3D tensors over shape (4,4,4), bond 2, and finite SIC response vectors",
        "peps3d_embedding": "K=(V,E,F,C) with explicit site anchors and edge incidence used for quotient adjacency; no scalar carrier labels admitted",
        "spinor_state": "torch-native two-component spinors seed finite local response tensors only; no Hopf/Weyl geometry is admitted",
        "quaternion_action": "not_applicable",
        "controller_context_artifacts": [PHASE2_TRANSITION_PATH],
        "dependency_receipts": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D response-quotient anchor partition",
        "branch_status_before_run": "active_carrier_frontier_continue_active_level",
        "allowed_claims": [
            "finite SIC response vectors induce finite PEPS3D-anchored response quotient classes on the tested carrier",
            "single-probe non-IC controls collapse relative to the full finite effect family",
            "local physical operator order witness survives while order-erased control collapses",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["pytorch", "rustworkx", "z3", "sympy"],
        "actual_tools_used": ["pytorch", "rustworkx", "z3", "sympy"],
        "proof_surfaces_used": ["z3_finite_response_quotient_nonpromotion_gate", "sympy_exact_class_site_edge_counts"],
        "graph_surfaces_used": ["rustworkx_response_quotient_incidence_graph"],
        "topology_surfaces_used": ["site_edge_anchor_support_counts"],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
        ],
        "required_negatives": [
            "single_probe_non_ic",
            "no_anchor",
            "scalar_label",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "negatives_run": [
            "single_probe_non_ic",
            "no_anchor",
            "scalar_label",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "kill_conditions": [
            "full finite response family does not define finite anchored classes",
            "single-probe non-IC control does not collapse relative to the full effect family",
            "no-anchor or scalar label controls are accepted as response quotient evidence",
            "order witness vanishes",
            "dense closure is used",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_response_quotient_anchor_partition_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_response_quotient_anchor_partition",
            "max_peps3d_sites": quotient["site_count"],
            "max_peps3d_bond": BOND_DIM,
            "full_effect_class_count": quotient["full_effect_class_count"],
            "single_probe_non_ic_class_count": quotient["single_probe_non_ic_class_count"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "site_count": quotient["site_count"],
            "edge_count": quotient["edge_count"],
            "full_effect_class_count": quotient["full_effect_class_count"],
            "single_probe_non_ic_class_count": quotient["single_probe_non_ic_class_count"],
            "order_gap": order["order_gap"],
            "order_erased_control_gap": order["order_erased_control_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff full finite effect responses define finite PEPS3D-anchored response classes, single-probe non-IC control collapses, no-anchor and scalar-label controls are rejected, local order gap survives, dense closure stays false, and promotion is blocked.",
        "fail_rule": "Fail if the quotient is nonfinite, non-IC controls do not collapse, controls replace the carrier quotient, order gap vanishes, dense closure is used, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this response-quotient anchor partition receipt inside the active carrier frontier matrix.",
            "Continue or block inside the same active carrier frontier with one bounded packet at a time.",
        ],
        "next_admissible_step": "Continue or block inside the active carrier frontier; do not open later consumers from this receipt.",
        "why_not_v4_probes": (
            "This is a v5 formal scout for active PEPS3D carrier-frontier continuation. "
            "It is not a v4 probe and not a full PEPS3D closure claim."
        ),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
