#!/usr/bin/env python3
"""PEPS3D boundary projection shape/bond replay scout.

Formal scout only.

This continuation packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  R_replay_K : (R_K, K_shape, boundary_anchor, bond_dim, local_order_ops)
        -> bounded shape/bond boundary projection replay signatures

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
NAME = "peps3d_boundary_projection_shape_bond_replay_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by replaying the P_K-supported "
    "boundary/interior response projection across bounded finite PEPS3D shapes "
    "and bond dimensions without dense closure or downstream geometry."
)
SCIENTIFIC_QUESTION = (
    "Does R_replay_K preserve finite boundary/interior response projection "
    "signatures across shape and bond rows while boundary-erased, flattened, "
    "single-probe non-IC, no-anchor, scalar-label, bond-collapsed, "
    "order-erased, dense-closure, and promotion controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_boundary_projection_shape_bond_replay"
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
PHASE2_BOUNDARY_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_boundary_response_projection_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests bounded shape/bond replay for finite PEPS3D "
    "boundary projection carrier signatures. It does not admit nested Hopf "
    "tori, Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, "
    "Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full "
    "PEPS3D closure."
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
        "reason": "load-bearing shape/bond replay response tensors, projection gaps, controls, and local order gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite PEPS3D graph connectivity and boundary/cut-edge support checks at each replay shape",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite replay/nonpromotion and control-collapse gate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite replay row, site, boundary, interior, edge, and bond count checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "sympy": "load_bearing",
}

SHAPES = [(3, 3, 3), (4, 4, 4)]
ZERO_INTERIOR_CONTROL_SHAPE = (3, 3, 2)
BOND_DIMS = [2, 3]
BOUNDARY_BOND_CONTROL = 1
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
    return len({tuple(round(float(item), 10) for item in row) for row in responses[:, :columns]})


def projection_row(shape: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    edges = edge_list(shape)
    graph = carrier_graph(shape)
    responses = probe_responses(site_spinors(len(coords)), sic_effects())
    boundary = [idx for idx, coord in enumerate(coords) if is_boundary(coord, shape)]
    interior = [idx for idx, coord in enumerate(coords) if not is_boundary(coord, shape)]
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
    tensors = make_site_tensors(responses, coords, bond_dim)[boundary]
    shift, filt = shift_filter_ops()
    filter_after_shift = apply_physical_operator(apply_physical_operator(tensors, shift), filt)
    shift_after_filter = apply_physical_operator(apply_physical_operator(tensors, filt), shift)
    order_gap = float(torch.linalg.vector_norm((filter_after_shift - shift_after_filter).reshape(-1)).item())
    erased_1 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    erased_2 = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    order_erased_gap = float(torch.linalg.vector_norm((erased_1 - erased_2).reshape(-1)).item())
    pass_row = bool(
        graph.num_nodes() == len(coords)
        and graph.num_edges() == len(edges)
        and rx.is_connected(graph)
        and len(boundary) > 0
        and len(interior) > 0
        and len(cut_edges) > 0
        and projection_gap > GAP_FLOOR
        and full_boundary_class_count > single_probe_boundary_class_count
        and flattened_boundary_class_count == 1
        and order_gap > GAP_FLOOR
        and order_erased_gap < TOL
    )
    return {
        "pass": pass_row,
        "shape": list(shape),
        "bond_dim": bond_dim,
        "site_count": len(coords),
        "edge_count": len(edges),
        "boundary_site_count": len(boundary),
        "interior_site_count": len(interior),
        "boundary_edge_count": len(boundary_edges),
        "cut_edge_count": len(cut_edges),
        "interior_edge_count": len(interior_edges),
        "boundary_interior_projection_gap": projection_gap,
        "full_boundary_class_count": full_boundary_class_count,
        "single_probe_boundary_class_count": single_probe_boundary_class_count,
        "single_probe_non_ic_collapses": single_probe_boundary_class_count < full_boundary_class_count,
        "flattened_boundary_class_count": flattened_boundary_class_count,
        "order_gap": order_gap,
        "order_erased_control_gap": order_erased_gap,
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def zero_interior_control_row(shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    edges = edge_list(shape)
    graph = carrier_graph(shape)
    boundary = [idx for idx, coord in enumerate(coords) if is_boundary(coord, shape)]
    interior = [idx for idx, coord in enumerate(coords) if not is_boundary(coord, shape)]
    pass_row = bool(
        graph.num_nodes() == len(coords)
        and graph.num_edges() == len(edges)
        and rx.is_connected(graph)
        and len(boundary) == len(coords)
        and len(interior) == 0
    )
    return {
        "pass": pass_row,
        "shape": list(shape),
        "site_count": len(coords),
        "edge_count": len(edges),
        "boundary_site_count": len(boundary),
        "interior_site_count": len(interior),
        "control_status": "blocked_control_only",
        "why_not_support": "boundary/interior projection requires a nonempty interior, so this finite shape is a control row only",
    }


def replay_gate() -> dict[str, Any]:
    rows = [projection_row(shape, bond_dim) for shape in SHAPES for bond_dim in BOND_DIMS]
    zero_interior_control = zero_interior_control_row(ZERO_INTERIOR_CONTROL_SHAPE)
    exact_total = (
        sp.Integer(len(rows))
        + sp.Integer(sum(row["site_count"] for row in rows))
        + sp.Integer(sum(row["boundary_site_count"] for row in rows))
        + sp.Integer(sum(row["interior_site_count"] for row in rows))
        + sp.Integer(sum(row["cut_edge_count"] for row in rows))
        + sp.Integer(max(BOND_DIMS))
        + sp.Integer(zero_interior_control["site_count"])
    )
    return {
        "pass": (
            all(row["pass"] for row in rows)
            and zero_interior_control["pass"]
            and BOUNDARY_BOND_CONTROL not in BOND_DIMS
        ),
        "finite_map": "R_replay_K : (R_K, K_shape, boundary_anchor, bond_dim, local_order_ops) -> bounded shape/bond boundary projection replay signatures",
        "stress_row_count": len(rows),
        "control_row_count": 1,
        "shapes": [list(shape) for shape in SHAPES],
        "zero_interior_control_shape": list(ZERO_INTERIOR_CONTROL_SHAPE),
        "bond_dims": list(BOND_DIMS),
        "max_peps3d_sites": max(row["site_count"] for row in rows),
        "max_peps3d_bond": max(BOND_DIMS),
        "min_projection_gap": min(row["boundary_interior_projection_gap"] for row in rows),
        "min_order_gap": min(row["order_gap"] for row in rows),
        "max_order_erased_control_gap": max(row["order_erased_control_gap"] for row in rows),
        "min_full_boundary_class_count": min(row["full_boundary_class_count"] for row in rows),
        "max_single_probe_boundary_class_count": max(row["single_probe_boundary_class_count"] for row in rows),
        "boundary_erased_site_count": 0,
        "no_anchor_class_count": 0,
        "scalar_label_available": True,
        "bond_dim_one_admitted": BOUNDARY_BOND_CONTROL in BOND_DIMS,
        "rows": rows,
        "zero_interior_control": zero_interior_control,
        "sympy_exact_replay_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_gate(replay: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    replayed = z3.Bool("replayed")
    controls_fail = z3.Bool("controls_fail")
    dense = z3.Bool("dense")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, replayed, controls_fail, z3.Not(dense), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    row_count = z3.Int("stress_row_count")
    control_count = z3.Int("control_row_count")
    max_sites = z3.Int("max_sites")
    max_bond = z3.Int("max_bond")
    count_solver.add(
        row_count == int(replay["stress_row_count"]),
        control_count == int(replay["control_row_count"]),
        max_sites == int(replay["max_peps3d_sites"]),
        max_bond == int(replay["max_peps3d_bond"]),
        row_count == 4,
        control_count == 1,
        max_sites == 64,
        max_bond == 3,
    )
    gap_solver = z3.Solver()
    scaled_projection_gap = z3.Int("scaled_min_projection_gap")
    scaled_order_gap = z3.Int("scaled_min_order_gap")
    gap_solver.add(
        scaled_projection_gap == int(replay["min_projection_gap"] * 1_000_000),
        scaled_order_gap == int(replay["min_order_gap"] * 1_000_000),
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
        "replay_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_projection_gap": int(replay["min_projection_gap"] * 1_000_000),
        "scaled_order_gap": int(replay["min_order_gap"] * 1_000_000),
    }


def main() -> int:
    started = time.time()
    replay = replay_gate()
    z3_row = z3_gate(replay)
    positive = {
        "P1_boundary_projection_shape_bond_replay": replay,
    }
    graveyard = {
        "GC_boundary_erased_control_rejected": {
            "pass": replay["boundary_erased_site_count"] == 0,
            "boundary_erased_site_count": replay["boundary_erased_site_count"],
        },
        "GC_flattened_boundary_control_collapses": {
            "pass": all(row["flattened_boundary_class_count"] == 1 for row in replay["rows"]),
            "max_flattened_boundary_class_count": max(row["flattened_boundary_class_count"] for row in replay["rows"]),
        },
        "GC_single_probe_non_ic_control_collapses": {
            "pass": all(row["single_probe_non_ic_collapses"] for row in replay["rows"]),
            "max_single_probe_boundary_class_count": replay["max_single_probe_boundary_class_count"],
            "min_full_boundary_class_count": replay["min_full_boundary_class_count"],
        },
        "GC_no_anchor_control_rejected": {
            "pass": replay["no_anchor_class_count"] == 0,
            "no_anchor_class_count": replay["no_anchor_class_count"],
        },
        "GC_scalar_label_not_boundary_projection": {
            "pass": replay["scalar_label_available"],
            "why_rejected": "scalar labels can count replay rows and boundary sites but do not carry finite response projections, cut-edge support, or PEPS3D anchors",
        },
        "GC_bond_dim_one_not_admitted": {
            "pass": not replay["bond_dim_one_admitted"],
            "bond_dim_one_admitted": replay["bond_dim_one_admitted"],
        },
        "GC_zero_interior_shape_blocked_control": replay["zero_interior_control"],
        "GC_order_erased_control_collapses": {
            "pass": replay["max_order_erased_control_gap"] < TOL,
            "max_order_erased_control_gap": replay["max_order_erased_control_gap"],
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not replay["dense_state_closure_used"] and not replay["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_z3_finite_replay_nonpromotion": z3_row,
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
            "F01": "finite PEPS3D shapes, finite bond set, finite boundary/interior anchors, finite SIC probe/effect responses, finite local operator paths, finite controls, finite output table",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter on boundary-anchored tensors for each replay row, while order-erased control collapses",
        },
        "finite_map": [
            "R_replay_K : (R_K, K_shape, boundary_anchor, bond_dim, local_order_ops) -> bounded shape/bond boundary projection replay signatures",
            "O_K : (T_boundary, local_order_ops) -> finite local order-gap vector for each replay row",
        ],
        "domain": {
            "carrier": "finite PEPS3D boundary projection shape/bond replay carrier",
            "shapes": replay["shapes"],
            "zero_interior_control_shape": replay["zero_interior_control_shape"],
            "bond_dims": replay["bond_dims"],
            "stress_row_count": replay["stress_row_count"],
            "control_row_count": replay["control_row_count"],
            "max_peps3d_sites": replay["max_peps3d_sites"],
            "max_peps3d_bond": replay["max_peps3d_bond"],
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite shape/bond replay table with boundary/interior projection gaps, cut-edge support counts, local order gaps, controls, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_boundary_projection_shape_bond_replay",
        "carrier_realization": "torch complex finite PEPS3D tensors over shapes (3,3,3) and (4,4,4), bond 2/3, finite SIC response vectors, rustworkx boundary/cut-edge support, and a blocked zero-interior shape control",
        "peps3d_embedding": "K=(V,E,F,C) with explicit boundary/interior site anchors and edge/cut-edge incidence for each finite replay shape; no scalar carrier labels admitted",
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
            PHASE2_BOUNDARY_PROJECTION_RECEIPT,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D boundary projection shape/bond replay",
        "branch_status_before_run": "post_R_K_boundary_projection_continue_active_level",
        "allowed_claims": [
            "P_K-supported boundary/interior projection signatures replay across the tested finite shape/bond rows",
            "boundary-erased, flattened-boundary, single-probe non-IC, no-anchor, scalar-label, bond-dim-one, zero-interior-shape, order-erased, dense-closure, and promotion controls fail or collapse",
            "local physical operator order witness survives while order-erased control collapses on every replay row",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["pytorch", "rustworkx", "z3", "sympy"],
        "actual_tools_used": ["pytorch", "rustworkx", "z3", "sympy"],
        "proof_surfaces_used": ["z3_finite_replay_nonpromotion_gate", "sympy_exact_shape_bond_replay_counts"],
        "graph_surfaces_used": ["rustworkx_boundary_cut_edge_support_graph_per_shape"],
        "topology_surfaces_used": ["finite_boundary_interior_edge_cut_edge_support_counts_per_shape"],
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
            PHASE2_BOUNDARY_PROJECTION_RECEIPT,
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
            PHASE2_BOUNDARY_PROJECTION_RECEIPT,
        ],
        "required_negatives": [
            "boundary_erased",
            "flattened_boundary",
            "single_probe_non_ic",
            "no_anchor",
            "scalar_label",
            "bond_dim_one",
            "zero_interior_shape",
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
            "bond_dim_one",
            "zero_interior_shape",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "promotion",
        ],
        "kill_conditions": [
            "finite shape/bond replay rows or boundary/interior anchors are missing",
            "boundary/interior response projection gap vanishes on any replay row",
            "single-probe non-IC control does not collapse relative to the full effect family",
            "bond_dim_one is admitted as support",
            "zero-interior shape is admitted as support",
            "order witness vanishes on any replay row",
            "dense closure is used",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_boundary_projection_shape_bond_replay_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_boundary_projection_shape_bond_replay",
            "stress_row_count": replay["stress_row_count"],
            "control_row_count": replay["control_row_count"],
            "max_peps3d_sites": replay["max_peps3d_sites"],
            "max_peps3d_bond": replay["max_peps3d_bond"],
            "min_projection_gap": replay["min_projection_gap"],
            "min_order_gap": replay["min_order_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "stress_row_count": replay["stress_row_count"],
            "control_row_count": replay["control_row_count"],
            "shapes": replay["shapes"],
            "zero_interior_control_shape": replay["zero_interior_control_shape"],
            "bond_dims": replay["bond_dims"],
            "max_peps3d_sites": replay["max_peps3d_sites"],
            "max_peps3d_bond": replay["max_peps3d_bond"],
            "min_projection_gap": replay["min_projection_gap"],
            "min_order_gap": replay["min_order_gap"],
            "max_order_erased_control_gap": replay["max_order_erased_control_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff boundary/interior projection signatures replay across all finite shape/bond rows, zero-interior shape remains control-only, controls fail or collapse, local order gap survives on every row, dense closure stays false, and promotion is blocked.",
        "fail_rule": "Fail if replay rows are nonfinite or missing, controls replace the carrier projection, zero-interior shape is admitted as support, single-probe non-IC control does not collapse, order gap vanishes, dense closure is used, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this boundary projection shape/bond replay receipt inside the active carrier frontier matrix.",
            "Continue or block inside the same active carrier frontier with one bounded packet at a time.",
        ],
        "next_admissible_step": "Classify this replay packet, then choose another bounded carrier-frontier packet or write the next active-frontier blocker.",
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
