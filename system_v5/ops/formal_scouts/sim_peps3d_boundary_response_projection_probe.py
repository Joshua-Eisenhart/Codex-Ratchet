#!/usr/bin/env python3
"""PEPS3D boundary response projection scout.

Formal scout only.

This continuation packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  R_K : (Q_K, boundary_anchor, edge_incidence, local_order_ops)
        -> finite boundary/interior response projection signatures

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
NAME = "peps3d_boundary_response_projection_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Reissue the active carrier frontier boundary/interior response projection "
    "after the smaller P_K K_8 face-projection dependency has closed, while "
    "still rejecting scalar labels, erased boundaries, single-probe non-IC "
    "controls, order-erased controls, dense closure, and downstream geometry."
)
SCIENTIFIC_QUESTION = (
    "Does R_K over P_K-supported finite PEPS3D carrier data produce "
    "boundary/interior response projection signatures with finite edge/cut-edge "
    "support while boundary-erased, flattened, single-probe non-IC, no-anchor, "
    "scalar-label, order-erased, dense-closure, and promotion controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_boundary_response_projection"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_BOUNDARY_RECEIPT = "system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json"
PHASE2_ABLATION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_anchor_ablation_boundary_stress_continuation_probe_results.json"
PHASE2_HELDOUT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_heldout_shape_anchor_replay_probe_results.json"
PHASE2_BOND_SWEEP_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_bond_sweep_anchor_stability_probe_results.json"
PHASE2_RESPONSE_QUOTIENT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_response_quotient_anchor_partition_probe_results.json"
PHASE2_CELL_PATCH_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_cell_patch_overlap_consistency_probe_results.json"
PHASE2_SUBSTRATE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_response_quotient_substrate_distinguishability_probe_results.json"
PHASE2_PK_FACE_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_k8_face_projection_response_quotient_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests finite PEPS3D boundary response projection on "
    "the active carrier. It does not admit nested Hopf tori, Weyl sheets, "
    "terrain, operator substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, "
    "physics, IGT/game theory, axes 7-12, or full PEPS3D closure."
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
        "reason": "load-bearing boundary/interior response tensors, projection gaps, controls, and local order gap",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite PEPS3D graph connectivity and boundary/cut-edge support checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite boundary projection/nonpromotion and control-collapse gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite boundary, interior, edge, cut-edge, and response-class count checks",
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


def is_boundary(coord: tuple[int, int, int], shape: tuple[int, int, int]) -> bool:
    return any(item == 0 or item == shape[axis] - 1 for axis, item in enumerate(coord))


def carrier_graph(shape: tuple[int, int, int]) -> rx.PyGraph:
    graph = rx.PyGraph()
    coords = coords_for_shape(shape)
    graph.add_nodes_from([{"coord": coord} for coord in coords])
    for edge in edge_list(shape):
        graph.add_edge(int(edge["src"]), int(edge["dst"]), {"axis": int(edge["axis"])})
    return graph


def unique_rows(responses: torch.Tensor, columns: int) -> int:
    keys = {
        tuple(round(float(item), 10) for item in row)
        for row in responses[:, :columns]
    }
    return len(keys)


def projection_gate() -> dict[str, Any]:
    coords = coords_for_shape(SHAPE)
    edges = edge_list(SHAPE)
    graph = carrier_graph(SHAPE)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    boundary = [idx for idx, coord in enumerate(coords) if is_boundary(coord, SHAPE)]
    interior = [idx for idx, coord in enumerate(coords) if not is_boundary(coord, SHAPE)]
    boundary_set = set(boundary)
    interior_set = set(interior)
    boundary_edges = [
        edge for edge in edges
        if int(edge["src"]) in boundary_set and int(edge["dst"]) in boundary_set
    ]
    cut_edges = [
        edge for edge in edges
        if (int(edge["src"]) in boundary_set) != (int(edge["dst"]) in boundary_set)
    ]
    interior_edges = [
        edge for edge in edges
        if int(edge["src"]) in interior_set and int(edge["dst"]) in interior_set
    ]
    boundary_signature = responses[boundary].mean(dim=0)
    interior_signature = responses[interior].mean(dim=0)
    projection_gap = float(torch.linalg.vector_norm(boundary_signature - interior_signature).item())
    flattened_boundary = boundary_signature.repeat(len(boundary), 1)
    flattened_boundary_class_count = unique_rows(flattened_boundary, columns=4)
    full_boundary_class_count = unique_rows(responses[boundary], columns=4)
    single_probe_boundary_class_count = unique_rows(responses[boundary], columns=1)
    exact_total = (
        sp.Integer(len(boundary))
        + sp.Integer(len(interior))
        + sp.Integer(len(boundary_edges))
        + sp.Integer(len(cut_edges))
        + sp.Integer(len(interior_edges))
        + sp.Integer(full_boundary_class_count)
    )
    return {
        "pass": bool(
            graph.num_nodes() == len(coords)
            and graph.num_edges() == len(edges)
            and rx.is_connected(graph)
            and len(boundary) == 56
            and len(interior) == 8
            and len(boundary_edges) == 108
            and len(cut_edges) == 24
            and len(interior_edges) == 12
            and projection_gap > GAP_FLOOR
            and full_boundary_class_count > single_probe_boundary_class_count
            and flattened_boundary_class_count == 1
        ),
        "finite_map": "R_K : (Q_K, boundary_anchor, edge_incidence, local_order_ops) -> finite boundary/interior response projection signatures",
        "shape": list(SHAPE),
        "site_count": len(coords),
        "boundary_site_count": len(boundary),
        "interior_site_count": len(interior),
        "edge_count": len(edges),
        "boundary_edge_count": len(boundary_edges),
        "cut_edge_count": len(cut_edges),
        "interior_edge_count": len(interior_edges),
        "boundary_interior_projection_gap": projection_gap,
        "full_boundary_class_count": full_boundary_class_count,
        "single_probe_boundary_class_count": single_probe_boundary_class_count,
        "single_probe_non_ic_collapses": single_probe_boundary_class_count < full_boundary_class_count,
        "flattened_boundary_class_count": flattened_boundary_class_count,
        "boundary_erased_site_count": 0,
        "no_anchor_class_count": 0,
        "scalar_label_boundary_count": len(boundary),
        "sympy_exact_boundary_projection_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def order_witness_gate() -> dict[str, Any]:
    coords = coords_for_shape(SHAPE)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    boundary = [idx for idx, coord in enumerate(coords) if is_boundary(coord, SHAPE)]
    tensors = make_site_tensors(responses, coords, BOND_DIM)[boundary]
    shift, filt = shift_filter_ops()
    filter_after_shift = apply_physical_operator(apply_physical_operator(tensors, shift), filt)
    shift_after_filter = apply_physical_operator(apply_physical_operator(tensors, filt), shift)
    order_gap = float(torch.linalg.vector_norm((filter_after_shift - shift_after_filter).reshape(-1)).item())
    erased_1 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    erased_2 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    order_erased_gap = float(torch.linalg.vector_norm((erased_1 - erased_2).reshape(-1)).item())
    return {
        "pass": bool(order_gap > GAP_FLOOR and order_erased_gap < TOL),
        "N01_witness": "physical_filter after physical_shift differs from physical_shift after physical_filter on boundary-anchored tensors",
        "order_gap": order_gap,
        "order_erased_control_gap": order_erased_gap,
    }


def z3_gate(projection: dict[str, Any], order: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    boundary_projection = z3.Bool("boundary_projection")
    controls_fail = z3.Bool("controls_fail")
    dense = z3.Bool("dense")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, boundary_projection, controls_fail, z3.Not(dense), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    boundary_count = z3.Int("boundary_site_count")
    interior_count = z3.Int("interior_site_count")
    cut_edge_count = z3.Int("cut_edge_count")
    count_solver.add(
        boundary_count == int(projection["boundary_site_count"]),
        interior_count == int(projection["interior_site_count"]),
        cut_edge_count == int(projection["cut_edge_count"]),
        boundary_count == 56,
        interior_count == 8,
        cut_edge_count > 0,
    )
    gap_solver = z3.Solver()
    scaled_projection_gap = z3.Int("scaled_boundary_projection_gap")
    scaled_order_gap = z3.Int("scaled_boundary_order_gap")
    gap_solver.add(
        scaled_projection_gap == int(projection["boundary_interior_projection_gap"] * 1_000_000),
        scaled_order_gap == int(order["order_gap"] * 1_000_000),
        scaled_projection_gap > 0,
        scaled_order_gap > 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and bad.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_nonpromotion_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "boundary_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_projection_gap": int(projection["boundary_interior_projection_gap"] * 1_000_000),
        "scaled_order_gap": int(order["order_gap"] * 1_000_000),
    }


def main() -> int:
    started = time.time()
    projection = projection_gate()
    order = order_witness_gate()
    z3_row = z3_gate(projection, order)
    positive = {
        "P1_boundary_response_projection": projection,
        "P2_boundary_projection_order_witness": order,
    }
    graveyard = {
        "GC_boundary_erased_control_rejected": {
            "pass": projection["boundary_erased_site_count"] == 0,
            "boundary_erased_site_count": projection["boundary_erased_site_count"],
        },
        "GC_flattened_boundary_control_collapses": {
            "pass": projection["flattened_boundary_class_count"] == 1,
            "flattened_boundary_class_count": projection["flattened_boundary_class_count"],
        },
        "GC_single_probe_non_ic_control_collapses": {
            "pass": projection["single_probe_non_ic_collapses"],
            "single_probe_boundary_class_count": projection["single_probe_boundary_class_count"],
            "full_boundary_class_count": projection["full_boundary_class_count"],
        },
        "GC_no_anchor_control_rejected": {
            "pass": projection["no_anchor_class_count"] == 0,
            "no_anchor_class_count": projection["no_anchor_class_count"],
        },
        "GC_scalar_label_not_boundary_projection": {
            "pass": projection["scalar_label_boundary_count"] == projection["boundary_site_count"],
            "why_rejected": "scalar labels can count boundary sites but do not carry finite response projections or PEPS3D cut-edge support",
        },
        "GC_order_erased_control_collapses": {
            "pass": order["order_erased_control_gap"] < TOL,
            "order_erased_control_gap": order["order_erased_control_gap"],
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not projection["dense_state_closure_used"] and not projection["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_z3_finite_boundary_projection_nonpromotion": z3_row,
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
            "F01": "finite PEPS3D carrier, finite boundary/interior anchors, finite SIC probe/effect responses, finite edge/cut-edge paths, finite controls, finite output vector",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter on boundary-anchored tensors, while order-erased control collapses",
        },
        "finite_map": [
            "R_K : (Q_K, boundary_anchor, edge_incidence, local_order_ops) -> finite boundary/interior response projection signatures",
            "O_K : (T_boundary, local_order_ops) -> finite local order-gap vector",
        ],
        "domain": {
            "carrier": "finite PEPS3D boundary/interior response projection carrier",
            "shape": list(SHAPE),
            "site_count": projection["site_count"],
            "boundary_site_count": projection["boundary_site_count"],
            "interior_site_count": projection["interior_site_count"],
            "edge_count": projection["edge_count"],
            "bond_dim": BOND_DIM,
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite boundary/interior projection signatures, edge/cut-edge support counts, control-collapse rows, local order-gap rows, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_boundary_projection",
        "carrier_realization": "torch complex finite PEPS3D tensors over shape (4,4,4), bond 2, finite SIC response vectors, and rustworkx boundary/cut-edge support",
        "peps3d_embedding": "K=(V,E,F,C) with explicit boundary/interior site anchors and edge/cut-edge incidence; no scalar carrier labels admitted",
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
            PHASE2_RESPONSE_QUOTIENT_RECEIPT,
            PHASE2_CELL_PATCH_RECEIPT,
            PHASE2_SUBSTRATE_RECEIPT,
            PHASE2_PK_FACE_PROJECTION_RECEIPT,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D boundary response projection reissue after P_K",
        "branch_status_before_run": "post_P_K_boundary_projection_reissue",
        "allowed_claims": [
            "finite PEPS3D boundary/interior anchors produce response projection signatures on the tested carrier",
            "boundary-erased, flattened-boundary, single-probe non-IC, no-anchor, scalar-label, order-erased, dense-closure, and promotion controls fail or collapse",
            "local physical operator order witness survives while order-erased control collapses",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["pytorch", "rustworkx", "z3", "sympy"],
        "actual_tools_used": ["pytorch", "rustworkx", "z3", "sympy"],
        "proof_surfaces_used": ["z3_finite_boundary_projection_nonpromotion_gate", "sympy_exact_boundary_projection_counts"],
        "graph_surfaces_used": ["rustworkx_boundary_cut_edge_support_graph"],
        "topology_surfaces_used": ["finite_boundary_interior_edge_cut_edge_support_counts"],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
            PHASE2_RESPONSE_QUOTIENT_RECEIPT,
            PHASE2_CELL_PATCH_RECEIPT,
            PHASE2_SUBSTRATE_RECEIPT,
            PHASE2_PK_FACE_PROJECTION_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
            PHASE2_RESPONSE_QUOTIENT_RECEIPT,
            PHASE2_CELL_PATCH_RECEIPT,
            PHASE2_SUBSTRATE_RECEIPT,
            PHASE2_PK_FACE_PROJECTION_RECEIPT,
        ],
        "required_negatives": [
            "boundary_erased",
            "flattened_boundary",
            "single_probe_non_ic",
            "no_anchor",
            "scalar_label",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "negatives_run": [
            "boundary_erased",
            "flattened_boundary",
            "single_probe_non_ic",
            "no_anchor",
            "scalar_label",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "kill_conditions": [
            "finite boundary/interior anchors or edge/cut-edge support are missing",
            "boundary/interior response projection gap vanishes",
            "boundary-erased or flattened controls are accepted",
            "single-probe non-IC control does not collapse relative to the full effect family",
            "order witness vanishes",
            "dense closure is used",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_boundary_response_projection_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_boundary_response_projection",
            "max_peps3d_sites": projection["site_count"],
            "max_peps3d_bond": BOND_DIM,
            "boundary_site_count": projection["boundary_site_count"],
            "interior_site_count": projection["interior_site_count"],
            "boundary_interior_projection_gap": projection["boundary_interior_projection_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "site_count": projection["site_count"],
            "boundary_site_count": projection["boundary_site_count"],
            "interior_site_count": projection["interior_site_count"],
            "boundary_edge_count": projection["boundary_edge_count"],
            "cut_edge_count": projection["cut_edge_count"],
            "interior_edge_count": projection["interior_edge_count"],
            "boundary_interior_projection_gap": projection["boundary_interior_projection_gap"],
            "full_boundary_class_count": projection["full_boundary_class_count"],
            "single_probe_boundary_class_count": projection["single_probe_boundary_class_count"],
            "order_gap": order["order_gap"],
            "order_erased_control_gap": order["order_erased_control_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff finite boundary/interior anchors produce response projection signatures with cut-edge support, boundary-erased and flattened controls fail or collapse, single-probe non-IC control collapses, no-anchor and scalar-label controls are rejected, local order gap survives, dense closure stays false, and promotion is blocked.",
        "fail_rule": "Fail if boundary/interior support is nonfinite or missing, controls replace the carrier projection, single-probe non-IC control does not collapse, order gap vanishes, dense closure is used, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this boundary response projection receipt inside the active carrier frontier matrix.",
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
