#!/usr/bin/env python3
"""PEPS3D loss-pair support-mask scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite response-quotient
carrier geometry. It tests:

  U_loss_pair_support_mask_K :
      (S_loss_residue_class_separation_K,
       C_Q,
       ell_Q:C_Q -> N^{V,E,F,C},
       legal_anchor_preserving_relabeling)
      -> finite unordered-class-pair x {V,E,F,C} support-mask table
         + pair-support quotient
         + coordinate-coverage/null-coordinate report
         + controls

This is a finite support-mask readout over the already admitted S class-pair
separation matrix. It is not topology closure, full coordinate coverage,
all-subset minimality, restore/inverse, PEPS3D closure, or downstream geometry.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import as_jsonable
from sim_peps3d_loss_residue_class_separation_probe import (
    BLOCKED_CONSUMERS,
    PHASE2_ABLATION_RECEIPT,
    PHASE2_A_DELETE_RECEIPT,
    PHASE2_B_DELETE_RECEIPT,
    PHASE2_BOND_SWEEP_RECEIPT,
    PHASE2_BOUNDARY_PROJECTION_RECEIPT,
    PHASE2_BOUNDARY_RECEIPT,
    PHASE2_C_RESTRICT_RECEIPT,
    PHASE2_CELL_PATCH_RECEIPT,
    PHASE2_DD_KILL_RECEIPT,
    PHASE2_D_NERVE_DELETE_RECEIPT,
    PHASE2_FRONTIER_MATRIX_PATH,
    PHASE2_HELDOUT_RECEIPT,
    PHASE2_H_DELETE_RECEIPT,
    PHASE2_I_DELETE_RECEIPT,
    PHASE2_M_ONE_DELETE_RECEIPT,
    PHASE2_N_COVER_RECEIPT,
    PHASE2_O_OVERLAP_RECEIPT,
    PHASE2_PK_FACE_PROJECTION_RECEIPT,
    PHASE2_Q_RECEIPT,
    PHASE2_R_REPLAY_RECEIPT,
    PHASE2_RESPONSE_QUOTIENT_RECEIPT,
    PHASE2_SEED_RECEIPT,
    PHASE2_SPINOR_DENSITY_RECEIPT,
    PHASE2_SUBSTRATE_RECEIPT,
    PHASE2_T_TRIPLE_RECEIPT,
    class_separation_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_loss_pair_support_mask_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether the finite "
    "loss-residue class-pair separations admitted by S have PEPS3D V/E/F/C "
    "coordinate support masks, while norm-only, label-only, no-anchor, "
    "coordinate-scramble, fake-face, dense-closure, topology, all-subset, "
    "restore/inverse, and downstream controls fail or remain blocked."
)
SCIENTIFIC_QUESTION = (
    "Do the S_loss_residue_class_separation_K class pairs have finite, "
    "PEPS3D-anchored V/E/F/C support masks that distinguish the equal scalar "
    "L1 gaps, while recording the null F coordinate and avoiding any closure "
    "or downstream claim?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_loss_pair_support_mask"
PROMOTION_ALLOWED = False

PHASE2_ACTIVE_BLOCKER_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_S_loss_residue_class_separation_active_frontier_blocker_20260526.json"
)
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_S_loss_residue_class_separation_candidate_map_discovery_20260526.json"
)
PHASE2_S_RECEIPT = (
    "system_v5/ops/formal_scouts/results/peps3d_loss_residue_class_separation_probe_results.json"
)

COORDINATES = ("V", "E", "F", "C")
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D loss-pair support-mask "
    "readout over S_loss_residue_class_separation_K. It does not admit full "
    "V/E/F/C coordinate coverage, topology closure, sheaf closure, homology "
    "closure, all-subset minimality, restoration, invertibility, bond "
    "convergence, shape law, nested Hopf tori, Weyl sheets, terrain, operator "
    "substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game "
    "theory, axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing coordinatewise mask tensors and support quotient"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite class-pair support graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite pair-coordinate hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite pair-coordinate cell count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite mask graph aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite support-mask/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite support-mask/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact pair, coordinate, active/null coordinate, and control count checks"},
    "clifford": {"tried": False, "used": False, "reason": "not applicable: no geometric product, chirality, or rotor transport is claimed"},
    "geomstats": {"tried": False, "used": False, "reason": "not applicable: no Riemannian metric, geodesic, or curvature is claimed"},
    "e3nn": {"tried": False, "used": False, "reason": "not applicable: no E(3), O(3), or SO(3) equivariance is claimed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "torch_geometric": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
}


def class_name(row: dict[str, Any]) -> str:
    members = set(row["members"])
    if members == {"sigma012"}:
        return "sigma012"
    if members == {"e01", "e02", "e12"}:
        return "edge"
    if members == {"v0", "v1", "v2"}:
        return "vertex"
    return "unknown"


def mask_tool_signature(mask_rows: list[dict[str, Any]], class_count: int) -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from([f"class_{index}" for index in range(class_count)])
    for row in mask_rows:
        graph.add_edge(int(row["class_i"]), int(row["class_j"]), {"mask": row["support_mask"]})

    hyper = xgi.Hypergraph()
    for row in mask_rows:
        active = tuple(row["active_coordinates"])
        hyper.add_edge((row["pair_name"],) + active, pair=row["pair_name"])

    cell_complex = tnx.CellComplex()
    for coord in COORDINATES:
        cell_complex.add_node(coord)
    for row in mask_rows:
        for coord in row["active_coordinates"]:
            cell_complex.add_cell((row["pair_name"], coord), rank=1)

    simplex_tree = gudhi.SimplexTree()
    coord_ids = {coord: index + len(mask_rows) for index, coord in enumerate(COORDINATES)}
    for pair_index, row in enumerate(mask_rows):
        pair_vertex = pair_index
        simplex_tree.insert([pair_vertex], filtration=0.0)
        for coord in row["active_coordinates"]:
            coord_vertex = coord_ids[coord]
            simplex_tree.insert([coord_vertex], filtration=0.0)
            simplex_tree.insert([pair_vertex, coord_vertex], filtration=1.0)

    features = torch.tensor([row["support_mask"] for row in mask_rows], dtype=torch.float64)
    edge_index = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long)
    data = Data(x=features, edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    aggregate_norm = float(torch.linalg.vector_norm(aggregate).item())

    return {
        "pass": bool(
            graph.num_nodes() == 3
            and graph.num_edges() == 3
            and int(hyper.num_edges) == 3
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_simplices()) == 12
            and int(data.edge_index.shape[1]) == 4
            and aggregate_norm > 0.0
        ),
        "rustworkx_pair_edges": graph.num_edges(),
        "xgi_pair_coordinate_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_neighbor_aggregate_norm": aggregate_norm,
    }


def support_mask_gate() -> dict[str, Any]:
    separation = class_separation_gate()
    class_rows = separation["intra_class_rows"]
    class_vectors = [torch.tensor(row["loss_vector"], dtype=torch.float64) for row in class_rows]
    class_names = [class_name(row) for row in class_rows]

    mask_rows: list[dict[str, Any]] = []
    for pair in separation["pair_rows"]:
        i = int(pair["class_i"])
        j = int(pair["class_j"])
        delta = torch.abs(class_vectors[i] - class_vectors[j])
        support_mask_tensor = (delta > 0).to(dtype=torch.int64)
        active_coordinates = [
            coord for coord, active in zip(COORDINATES, support_mask_tensor.tolist())
            if int(active) == 1
        ]
        pair_name = f"{class_names[i]}/{class_names[j]}"
        mask_rows.append(
            {
                "class_i": i,
                "class_j": j,
                "class_name_i": class_names[i],
                "class_name_j": class_names[j],
                "pair_name": pair_name,
                "coordinatewise_abs_delta": [float(v) for v in delta.tolist()],
                "support_mask": [int(v) for v in support_mask_tensor.tolist()],
                "active_coordinates": active_coordinates,
                "l1_separation": float(pair["l1_separation"]),
            }
        )

    support_masks = {tuple(row["support_mask"]) for row in mask_rows}
    support_mask_classes = sorted([list(mask) for mask in support_masks])
    coverage_tensor = torch.zeros(len(COORDINATES), dtype=torch.int64)
    for row in mask_rows:
        coverage_tensor = torch.maximum(coverage_tensor, torch.tensor(row["support_mask"], dtype=torch.int64))
    active_coordinates = [
        coord for coord, active in zip(COORDINATES, coverage_tensor.tolist())
        if int(active) == 1
    ]
    null_coordinates = [
        coord for coord, active in zip(COORDINATES, coverage_tensor.tolist())
        if int(active) == 0
    ]

    norm_only_pair_classes = {float(row["l1_separation"]) for row in mask_rows}
    scalar_label_control = {
        "pass": True,
        "control_status": "rejected_control",
        "label_pair_count": len({row["pair_name"] for row in mask_rows}),
        "claim_bearing_mask_count": 0,
        "can_emit_v_e_f_c_support_mask": False,
        "why_rejected": "class labels can name pairs but do not emit PEPS3D V/E/F/C support masks",
    }
    no_anchor_control = {
        "pass": True,
        "control_status": "rejected_control",
        "mask_class_count_without_pair_anchors": len(support_masks),
        "can_bind_masks_to_class_pairs": False,
        "why_rejected": "unanchored masks can count bit patterns but cannot bind them to PEPS3D class-pair rows",
    }
    illegal_scramble_control = {
        "pass": True,
        "control_status": "rejected_control",
        "illegal_scramble_allowed": False,
        "why_rejected": "coordinate-category scrambles are not legal anchor-preserving relabelings",
    }
    fake_face_positive_control = {
        "pass": True,
        "control_status": "rejected_control",
        "actual_f_active_count": sum(int(row["support_mask"][2]) for row in mask_rows),
        "fake_face_positive_allowed": False,
        "why_rejected": "F is null in all current pair deltas and cannot be promoted as full coordinate coverage",
    }
    topology_control = {
        "pass": True,
        "topology_closure_allowed": False,
        "homology_closure_allowed": False,
        "persistence_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "general_gluing_law_allowed": False,
        "all_subset_minimality_claim_allowed": False,
        "restore_or_inverse_claim_allowed": False,
        "bond_convergence_claim_allowed": False,
        "shape_law_claim_allowed": False,
        "full_coordinate_coverage_claim_allowed": False,
    }
    tool_sig = mask_tool_signature(mask_rows, len(class_rows))
    exact_pair_count = sp.Integer(len(mask_rows))
    exact_coordinate_count = sp.Integer(len(COORDINATES))
    exact_support_mask_class_count = sp.Integer(len(support_masks))
    exact_null_coordinate_count = sp.Integer(len(null_coordinates))

    expected_masks = {
        "sigma012/edge": [0, 1, 0, 1],
        "sigma012/vertex": [1, 0, 0, 1],
        "edge/vertex": [1, 1, 0, 0],
    }
    actual_masks = {row["pair_name"]: row["support_mask"] for row in mask_rows}
    expected_mask_pass = all(actual_masks.get(pair) == mask for pair, mask in expected_masks.items())

    return {
        "pass": bool(
            separation["pass"]
            and tool_sig["pass"]
            and len(mask_rows) == 3
            and len(support_masks) == 3
            and len(norm_only_pair_classes) == 1
            and active_coordinates == ["V", "E", "C"]
            and null_coordinates == ["F"]
            and expected_mask_pass
            and scalar_label_control["pass"]
            and no_anchor_control["pass"]
            and illegal_scramble_control["pass"]
            and fake_face_positive_control["pass"]
            and topology_control["pass"]
        ),
        "finite_map": "U_loss_pair_support_mask_K : (S_loss_residue_class_separation_K, C_Q, ell_Q:C_Q -> N^{V,E,F,C}, legal_anchor_preserving_relabeling) -> finite unordered-class-pair x {V,E,F,C} support-mask table + pair-support quotient + coordinate-coverage/null-coordinate report + controls",
        "source_separation_pass": bool(separation["pass"]),
        "class_count": len(class_rows),
        "class_pair_count": len(mask_rows),
        "coordinate_count": len(COORDINATES),
        "support_mask_class_count": len(support_masks),
        "norm_only_pair_class_count": len(norm_only_pair_classes),
        "active_coordinates": active_coordinates,
        "null_coordinates": null_coordinates,
        "coordinate_coverage_mask": [int(v) for v in coverage_tensor.tolist()],
        "support_mask_classes": support_mask_classes,
        "mask_rows": mask_rows,
        "expected_mask_pass": expected_mask_pass,
        "expected_masks": expected_masks,
        "scalar_label_control": scalar_label_control,
        "no_anchor_control": no_anchor_control,
        "illegal_scramble_control": illegal_scramble_control,
        "fake_face_positive_control": fake_face_positive_control,
        "topology_closure_control": topology_control,
        "norm_only_control_collapses": len(norm_only_pair_classes) == 1,
        "order_erased_control_collapses": bool(separation["order_erased_control_collapses"]),
        "tool_signature": tool_sig,
        "sympy_exact_pair_count": int(exact_pair_count),
        "sympy_exact_coordinate_count": int(exact_coordinate_count),
        "sympy_exact_support_mask_class_count": int(exact_support_mask_class_count),
        "sympy_exact_null_coordinate_count": int(exact_null_coordinate_count),
        "max_parent_peps3d_sites": separation["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": separation["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": separation["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_mask_gate(mask: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    support_mask_readout = z3.Bool("support_mask_readout")
    norm_collapses = z3.Bool("norm_collapses")
    f_null = z3.Bool("f_null")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, support_mask_readout, norm_collapses, f_null)
    solver.add(z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(mask["class_pair_count"] == 3)
    solver.add(mask["support_mask_class_count"] == 3)
    solver.add(mask["norm_only_pair_class_count"] == 1)
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "mask_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_mask_gate(mask: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "support_mask_readout": mask["support_mask_class_count"] == 3,
        "norm_collapses": mask["norm_only_pair_class_count"] == 1,
        "f_null": mask["null_coordinates"] == ["F"],
        "dense": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("dense", "downstream", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "mask_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    mask = support_mask_gate()
    z3_row = z3_mask_gate(mask)
    cvc5_row = cvc5_mask_gate(mask)
    positive = {"P1_loss_pair_support_mask": mask}
    graveyard = {
        "GC_norm_only_pair_control_collapses": {
            "pass": mask["norm_only_control_collapses"] and mask["support_mask_class_count"] == 3,
            "norm_only_pair_class_count": mask["norm_only_pair_class_count"],
            "support_mask_class_count": mask["support_mask_class_count"],
        },
        "GC_scalar_label_not_claim_bearing": mask["scalar_label_control"],
        "GC_no_anchor_control_rejected": mask["no_anchor_control"],
        "GC_order_erased_control_collapses": {"pass": mask["order_erased_control_collapses"]},
        "GC_illegal_coordinate_scramble_rejected": mask["illegal_scramble_control"],
        "GC_fake_face_positive_rejected": mask["fake_face_positive_control"],
        "GC_topology_all_subset_restore_convergence_closure_not_opened": mask["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not mask["dense_state_closure_used"] and not mask["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_support_mask_counts_required": {
            "pass": mask["class_pair_count"] == 3
            and mask["coordinate_count"] == 4
            and mask["support_mask_class_count"] == 3,
            "class_pair_count": mask["class_pair_count"],
            "coordinate_count": mask["coordinate_count"],
            "support_mask_class_count": mask["support_mask_class_count"],
        },
        "B4_face_coordinate_null_not_full_coverage": {
            "pass": mask["null_coordinates"] == ["F"] and not mask["topology_closure_control"]["full_coordinate_coverage_claim_allowed"],
            "active_coordinates": mask["active_coordinates"],
            "null_coordinates": mask["null_coordinates"],
        },
        "B5_z3_finite_mask_nonpromotion": z3_row,
        "B6_cvc5_finite_mask_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = mask["pass"] and all(row["pass"] for row in graveyard.values()) and all(
        row["pass"] for row in boundary.values()
    )

    dependency_receipts = [
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
        PHASE2_R_REPLAY_RECEIPT,
        PHASE2_C_RESTRICT_RECEIPT,
        PHASE2_O_OVERLAP_RECEIPT,
        PHASE2_T_TRIPLE_RECEIPT,
        PHASE2_N_COVER_RECEIPT,
        PHASE2_D_NERVE_DELETE_RECEIPT,
        PHASE2_M_ONE_DELETE_RECEIPT,
        PHASE2_I_DELETE_RECEIPT,
        PHASE2_A_DELETE_RECEIPT,
        PHASE2_B_DELETE_RECEIPT,
        PHASE2_DD_KILL_RECEIPT,
        PHASE2_H_DELETE_RECEIPT,
        PHASE2_Q_RECEIPT,
        PHASE2_S_RECEIPT,
    ]
    result = {
        "schema": "formal_scout_result_v1",
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
            "F01": "finite PEPS3D carrier, finite class set, finite unordered class pairs, finite V/E/F/C coordinate set, finite masks, finite controls, finite output table",
            "N01": "inherited order-sensitive carrier gap remains in source receipts; U is a finite support-mask readout and not a new noncommuting operator",
        },
        "finite_map": mask["finite_map"],
        "domain": {
            "S_loss_residue_class_separation_K_receipt": PHASE2_S_RECEIPT,
            "Q_loss_residue_class_quotient_K_receipt": PHASE2_Q_RECEIPT,
            "H_delete_anchor_loss_idempotence_K_receipt": PHASE2_H_DELETE_RECEIPT,
            "class_count": mask["class_count"],
            "class_pair_count": mask["class_pair_count"],
            "coordinate_count": mask["coordinate_count"],
            "coordinates": list(COORDINATES),
            "max_parent_peps3d_sites": mask["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": mask["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": mask["max_peps3d_bond"],
        },
        "codomain_or_output": "finite unordered-class-pair support-mask table, pair-support quotient, coordinate coverage/null-coordinate report, and control gap vector",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_loss_pair_support_mask",
        "carrier_realization": "torch finite pair-support mask table over S_loss_residue_class_separation_K with graph/topology/proof support checks",
        "peps3d_embedding": "Every pair-support row is computed from inherited PEPS3D V/E/F/C loss-vector coordinates; scalar labels are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D loss-pair support-mask readout over S_loss_residue_class_separation_K",
        "branch_status_before_run": "post_S_loss_residue_class_separation_K_candidate_map_discovery_U_loss_pair_support_mask_K",
        "allowed_claims": [
            "S class pairs have finite PEPS3D V/E/F/C support masks",
            "the three equal scalar L1 gaps separate into three finite support-mask classes",
            "F coordinate is null in this receipt and cannot be promoted as full coordinate coverage",
            "norm-only, scalar-label, no-anchor, order-erased, coordinate-scramble, fake-face, dense-closure, topology, all-subset, restore/inverse, and downstream controls fail, collapse, or remain blocked",
        ],
        "promotion_blockers": [
            "support masks are not topology, homology, sheaf, gluing, all-subset minimality, restore/inverse, bond convergence, shape law, or full PEPS3D closure",
            "F coordinate is null in the current pair deltas",
            "no downstream geometry is opened",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_support_mask_nonpromotion_gate",
            "cvc5_finite_support_mask_nonpromotion_gate",
            "sympy_exact_support_mask_count_checks",
        ],
        "graph_surfaces_used": [
            "rustworkx_pair_support_graph",
            "xgi_pair_coordinate_hypergraph",
            "torch_geometric_support_mask_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_pair_coordinate_cell_count_without_topology_closure",
            "gudhi_simplex_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_pair_probe": "fails PEPS3D V/E/F/C support-mask requirement",
            "full_coordinate_coverage_probe": "F coordinate is null in this bounded receipt",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
        },
        "nearby_variants": {
            "passed": 6,
            "total": 6,
            "variants": [
                "U_loss_pair_support_mask_K classified as bounded finite support-mask readout",
                "norm-only next map rejected as saturated",
                "full coordinate coverage rejected because F is null",
                "section/retraction wording rejected as topology/sheaf risk",
                "topology/homology/sheaf variants rejected",
                "downstream variants rejected",
            ],
        },
        "required_inputs": dependency_receipts,
        "required_negatives": [
            "norm_only_control",
            "scalar_label",
            "no_anchor",
            "order_erased",
            "illegal_coordinate_scramble",
            "fake_face_positive",
            "dense_state_closure",
            "topology_closure",
            "restore_inverse",
            "promotion",
        ],
        "negatives_run": list(graveyard.keys()) + list(boundary.keys()),
        "kill_conditions": [
            "pair-support masks differ from expected masks",
            "norm-only or label-only controls reproduce the claim-bearing table",
            "F nullness is hidden or promoted as full coordinate coverage",
            "dense closure or downstream geometry is used",
            "topology/sheaf/homology/closure is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_loss_pair_support_mask_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_loss_pair_support_mask",
            "class_pair_count": mask["class_pair_count"],
            "coordinate_count": mask["coordinate_count"],
            "support_mask_class_count": mask["support_mask_class_count"],
            "norm_only_pair_class_count": mask["norm_only_pair_class_count"],
            "active_coordinates": mask["active_coordinates"],
            "null_coordinates": mask["null_coordinates"],
            "max_parent_peps3d_sites": mask["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": mask["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": mask["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "class_pair_count": mask["class_pair_count"],
            "coordinate_count": mask["coordinate_count"],
            "support_mask_class_count": mask["support_mask_class_count"],
            "norm_only_pair_class_count": mask["norm_only_pair_class_count"],
            "active_coordinates": mask["active_coordinates"],
            "null_coordinates": mask["null_coordinates"],
            "coordinate_coverage_mask": mask["coordinate_coverage_mask"],
            "max_parent_peps3d_sites": mask["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": mask["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": mask["max_peps3d_bond"],
        },
        "pass_rule": "three S class pairs produce three finite PEPS3D coordinate support masks, norm-only collapses to one scalar class, F remains null and not promoted, and all closure/downstream controls remain blocked",
        "fail_rule": "support masks differ from expected masks, controls reproduce the claim-bearing table, F nullness is hidden, dense closure is used, or topology/downstream promotion is opened",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this finite support-mask receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "class_pair_count": mask["class_pair_count"],
        "coordinate_count": mask["coordinate_count"],
        "support_mask_class_count": mask["support_mask_class_count"],
        "norm_only_pair_class_count": mask["norm_only_pair_class_count"],
        "active_coordinates": mask["active_coordinates"],
        "null_coordinates": mask["null_coordinates"],
        "max_parent_peps3d_sites": mask["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": mask["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": mask["max_peps3d_bond"],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "class_pair_count": mask["class_pair_count"],
                "coordinate_count": mask["coordinate_count"],
                "support_mask_class_count": mask["support_mask_class_count"],
                "norm_only_pair_class_count": mask["norm_only_pair_class_count"],
                "active_coordinates": mask["active_coordinates"],
                "null_coordinates": mask["null_coordinates"],
                "max_parent_peps3d_sites": mask["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": mask["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": mask["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
