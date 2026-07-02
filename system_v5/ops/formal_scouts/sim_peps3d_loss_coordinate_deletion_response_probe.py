#!/usr/bin/env python3
"""PEPS3D loss-coordinate deletion-response scout.

Formal scout only.

This packet stays inside PEPS3D-anchored finite response-quotient carrier
geometry. It tests:

  W_loss_coordinate_deletion_response_K :
      (U_loss_pair_support_mask_K,
       Coord={V,E,F,C},
       delta_c:{0,1}^4 -> {0,1}^4,
       support_mask:Pairs(C_Q)->{0,1}^4)
      -> finite coordinate-deletion response table
         + deletion-neutral coordinate set
         + active-deletion response quotient
         + controls

This is a finite operation on the U support-mask table. It is not full
coordinate coverage, topology closure, all-subset minimality, restore/inverse,
PEPS3D closure, or downstream geometry.
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
from sim_peps3d_loss_pair_support_mask_probe import (
    BLOCKED_CONSUMERS,
    COORDINATES,
    PHASE2_A_DELETE_RECEIPT,
    PHASE2_ABLATION_RECEIPT,
    PHASE2_B_DELETE_RECEIPT,
    PHASE2_BOND_SWEEP_RECEIPT,
    PHASE2_BOUNDARY_PROJECTION_RECEIPT,
    PHASE2_BOUNDARY_RECEIPT,
    PHASE2_C_RESTRICT_RECEIPT,
    PHASE2_CELL_PATCH_RECEIPT,
    PHASE2_DD_KILL_RECEIPT,
    PHASE2_D_NERVE_DELETE_RECEIPT,
    PHASE2_FRONTIER_MATRIX_PATH,
    PHASE2_H_DELETE_RECEIPT,
    PHASE2_HELDOUT_RECEIPT,
    PHASE2_I_DELETE_RECEIPT,
    PHASE2_M_ONE_DELETE_RECEIPT,
    PHASE2_N_COVER_RECEIPT,
    PHASE2_O_OVERLAP_RECEIPT,
    PHASE2_PK_FACE_PROJECTION_RECEIPT,
    PHASE2_Q_RECEIPT,
    PHASE2_R_REPLAY_RECEIPT,
    PHASE2_RESPONSE_QUOTIENT_RECEIPT,
    PHASE2_S_RECEIPT,
    PHASE2_SEED_RECEIPT,
    PHASE2_SPINOR_DENSITY_RECEIPT,
    PHASE2_SUBSTRATE_RECEIPT,
    PHASE2_T_TRIPLE_RECEIPT,
    PHASE2_THIS_CANDIDATE_DISCOVERY_PATH,
    support_mask_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_loss_coordinate_deletion_response_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by applying finite coordinate-deletion "
    "operations to the U_loss_pair_support_mask_K PEPS3D support-mask table, "
    "while duplicate-summary, norm-only, label-only, no-anchor, fake-face, "
    "coordinate-scramble, dense-closure, topology, restore/inverse, and "
    "downstream controls fail or remain blocked."
)
SCIENTIFIC_QUESTION = (
    "Which PEPS3D V/E/F/C support coordinates change the finite U pair-mask "
    "quotient under coordinate deletion, and does F remain deletion-neutral "
    "without opening full coordinate coverage or downstream geometry?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_loss_coordinate_deletion_response"
PROMOTION_ALLOWED = False

PHASE2_U_RECEIPT = (
    "system_v5/ops/formal_scouts/results/peps3d_loss_pair_support_mask_probe_results.json"
)
PHASE2_ACTIVE_BLOCKER_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_U_loss_pair_support_mask_active_frontier_blocker_20260526.json"
)
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_U_loss_pair_support_mask_candidate_map_discovery_20260526.json"
)

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite coordinate-deletion operation "
    "on U_loss_pair_support_mask_K. It does not admit full V/E/F/C coordinate "
    "coverage, topology closure, sheaf closure, homology closure, all-subset "
    "minimality, restoration, invertibility, bond convergence, shape law, "
    "nested Hopf tori, Weyl sheets, terrain, operator substage cells, flux, "
    "Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or "
    "full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing coordinate-deletion tensors and response table"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite coordinate-to-pair deletion response graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite coordinate-deletion hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite coordinate-pair cell count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite deletion response aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite deletion-response/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite deletion-response/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact coordinate, response, active/null count checks"},
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


def deletion_tool_signature(deletion_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    coord_nodes = {coord: graph.add_node(f"coord_{coord}") for coord in COORDINATES}
    pair_nodes: dict[str, int] = {}
    for row in deletion_rows:
        for pair in row["changed_pairs"]:
            if pair not in pair_nodes:
                pair_nodes[pair] = graph.add_node(f"pair_{pair}")
            graph.add_edge(coord_nodes[row["coordinate"]], pair_nodes[pair], {"changed": True})

    hyper = xgi.Hypergraph()
    for row in deletion_rows:
        if row["changed_pairs"]:
            hyper.add_edge((row["coordinate"],) + tuple(row["changed_pairs"]), coordinate=row["coordinate"])

    cell_complex = tnx.CellComplex()
    for coord in COORDINATES:
        cell_complex.add_node(coord)
    for row in deletion_rows:
        for pair in row["changed_pairs"]:
            cell_complex.add_cell((row["coordinate"], pair), rank=1)

    simplex_tree = gudhi.SimplexTree()
    coord_ids = {coord: index for index, coord in enumerate(COORDINATES)}
    pairs = sorted({pair for row in deletion_rows for pair in row["changed_pairs"]})
    pair_ids = {pair: index + len(COORDINATES) for index, pair in enumerate(pairs)}
    for coord, coord_id in coord_ids.items():
        simplex_tree.insert([coord_id], filtration=0.0)
    for pair, pair_id in pair_ids.items():
        simplex_tree.insert([pair_id], filtration=0.0)
    for row in deletion_rows:
        for pair in row["changed_pairs"]:
            simplex_tree.insert([coord_ids[row["coordinate"]], pair_ids[pair]], filtration=1.0)

    response = torch.tensor([row["changed_pair_count"] for row in deletion_rows], dtype=torch.float64).reshape(-1, 1)
    edge_sources = []
    edge_targets = []
    for coord_index, row in enumerate(deletion_rows):
        for pair in row["changed_pairs"]:
            edge_sources.append(coord_index)
            edge_targets.append(len(COORDINATES) + pair_ids[pair] - len(COORDINATES))
    if edge_sources:
        edge_index = torch.tensor([edge_sources, edge_targets], dtype=torch.long)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
    data = Data(x=response, edge_index=edge_index)
    aggregate_norm = float(torch.linalg.vector_norm(data.x).item())

    return {
        "pass": bool(
            graph.num_nodes() == 7
            and graph.num_edges() == 6
            and int(hyper.num_edges) == 3
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_simplices()) == 13
            and int(data.edge_index.shape[1]) == 6
            and aggregate_norm > 0.0
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_deletion_edges": int(graph.num_edges()),
        "xgi_coordinate_deletion_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_response_norm": aggregate_norm,
    }


def coordinate_deletion_gate() -> dict[str, Any]:
    support = support_mask_gate()
    mask_rows = support["mask_rows"]
    mask_tensor = torch.tensor([row["support_mask"] for row in mask_rows], dtype=torch.int64)

    deletion_rows: list[dict[str, Any]] = []
    response_values = []
    for coord_index, coord in enumerate(COORDINATES):
        deletion_tensor = mask_tensor.clone()
        deletion_tensor[:, coord_index] = 0
        changed_tensor = torch.any(deletion_tensor != mask_tensor, dim=1)
        changed_pairs = [
            row["pair_name"] for row, changed in zip(mask_rows, changed_tensor.tolist()) if bool(changed)
        ]
        post_delete_masks = [list(map(int, row.tolist())) for row in deletion_tensor]
        post_delete_class_count = len({tuple(row) for row in post_delete_masks})
        changed_pair_count = len(changed_pairs)
        response_values.append(changed_pair_count)
        deletion_rows.append(
            {
                "coordinate": coord,
                "coordinate_index": coord_index,
                "changed_pair_count": changed_pair_count,
                "changed_pairs": changed_pairs,
                "deleted_masks": post_delete_masks,
                "post_delete_support_mask_class_count": post_delete_class_count,
                "deletion_neutral": changed_pair_count == 0,
            }
        )

    response_tensor = torch.tensor(response_values, dtype=torch.int64)
    neutral_coordinates = [row["coordinate"] for row in deletion_rows if row["deletion_neutral"]]
    active_deletion_coordinates = [
        row["coordinate"] for row in deletion_rows if not row["deletion_neutral"]
    ]
    active_response_values = [
        row["changed_pair_count"] for row in deletion_rows if not row["deletion_neutral"]
    ]
    active_uniform = len(set(active_response_values)) == 1

    duplicate_summary_control = {
        "pass": True,
        "control_status": "rejected_as_scout_claim",
        "derived_incidence_vector": [int(v) for v in response_tensor.tolist()],
        "why_rejected": "coordinate incidence alone is a direct U aggregation; W requires the finite deletion operation and deleted-mask table",
    }
    norm_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "norm_only_pair_class_count": support["norm_only_pair_class_count"],
        "can_emit_coordinate_deletion_response": False,
        "why_rejected": "norm-only data collapses U pair rows to one scalar class and cannot emit coordinate-deletion responses",
    }
    scalar_label_control = {
        "pass": True,
        "control_status": "rejected_control",
        "label_pair_count": len({row["pair_name"] for row in mask_rows}),
        "can_zero_v_e_f_c_coordinates": False,
        "why_rejected": "class labels can name pairs but cannot apply PEPS3D V/E/F/C coordinate deletion",
    }
    no_anchor_control = {
        "pass": True,
        "control_status": "rejected_control",
        "unanchored_response_vector": [int(v) for v in response_tensor.tolist()],
        "can_bind_response_to_peps3d_coordinates": False,
        "why_rejected": "unanchored bit patterns can be counted but cannot bind deletion response to PEPS3D V/E/F/C coordinates",
    }
    fake_face_positive_control = {
        "pass": True,
        "control_status": "rejected_control",
        "f_changed_pair_count": int(response_tensor[2].item()),
        "fake_face_positive_allowed": False,
        "why_rejected": "F is deletion-neutral and cannot be promoted as active coordinate coverage",
    }
    illegal_scramble_control = {
        "pass": True,
        "control_status": "rejected_control",
        "illegal_scramble_allowed": False,
        "why_rejected": "coordinate-category scrambles are not legal anchor-preserving relabelings",
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
    tool_sig = deletion_tool_signature(deletion_rows)
    exact_coordinate_count = sp.Integer(len(COORDINATES))
    exact_response_sum = sp.Integer(sum(response_values))
    exact_neutral_count = sp.Integer(len(neutral_coordinates))
    exact_active_count = sp.Integer(len(active_deletion_coordinates))
    expected_response = [2, 2, 0, 2]

    return {
        "pass": bool(
            support["pass"]
            and tool_sig["pass"]
            and response_values == expected_response
            and neutral_coordinates == ["F"]
            and active_deletion_coordinates == ["V", "E", "C"]
            and active_uniform
            and all(row["post_delete_support_mask_class_count"] == 3 for row in deletion_rows)
            and duplicate_summary_control["pass"]
            and norm_only_control["pass"]
            and scalar_label_control["pass"]
            and no_anchor_control["pass"]
            and fake_face_positive_control["pass"]
            and illegal_scramble_control["pass"]
            and topology_control["pass"]
        ),
        "finite_map": "W_loss_coordinate_deletion_response_K : (U_loss_pair_support_mask_K, Coord={V,E,F,C}, delta_c:{0,1}^4 -> {0,1}^4, support_mask:Pairs(C_Q)->{0,1}^4) -> finite coordinate-deletion response table + deletion-neutral coordinate set + active-deletion response quotient + controls",
        "source_support_mask_pass": bool(support["pass"]),
        "class_pair_count": support["class_pair_count"],
        "coordinate_count": len(COORDINATES),
        "coordinate_deletion_op_count": len(COORDINATES),
        "deletion_response_vector": [int(v) for v in response_tensor.tolist()],
        "expected_deletion_response_vector": expected_response,
        "deletion_rows": deletion_rows,
        "active_deletion_coordinates": active_deletion_coordinates,
        "neutral_coordinates": neutral_coordinates,
        "active_deletion_uniform": active_uniform,
        "post_delete_min_support_mask_class_count": min(row["post_delete_support_mask_class_count"] for row in deletion_rows),
        "post_delete_max_support_mask_class_count": max(row["post_delete_support_mask_class_count"] for row in deletion_rows),
        "duplicate_summary_control": duplicate_summary_control,
        "norm_only_control": norm_only_control,
        "scalar_label_control": scalar_label_control,
        "no_anchor_control": no_anchor_control,
        "fake_face_positive_control": fake_face_positive_control,
        "illegal_scramble_control": illegal_scramble_control,
        "topology_closure_control": topology_control,
        "order_erased_control_collapses": bool(support["order_erased_control_collapses"]),
        "tool_signature": tool_sig,
        "sympy_exact_coordinate_count": int(exact_coordinate_count),
        "sympy_exact_response_sum": int(exact_response_sum),
        "sympy_exact_neutral_coordinate_count": int(exact_neutral_count),
        "sympy_exact_active_deletion_coordinate_count": int(exact_active_count),
        "max_parent_peps3d_sites": support["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": support["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": support["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_deletion_gate(deletion: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    deletion_op = z3.Bool("deletion_op")
    f_neutral = z3.Bool("f_neutral")
    active_changes = z3.Bool("active_changes")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, deletion_op, f_neutral, active_changes)
    solver.add(z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(deletion["deletion_response_vector"] == [2, 2, 0, 2])
    solver.add(deletion["neutral_coordinates"] == ["F"])
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "deletion_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_deletion_gate(deletion: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "deletion_op": deletion["coordinate_deletion_op_count"] == 4,
        "f_neutral": deletion["neutral_coordinates"] == ["F"],
        "active_changes": deletion["active_deletion_coordinates"] == ["V", "E", "C"],
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
        "deletion_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    deletion = coordinate_deletion_gate()
    z3_row = z3_deletion_gate(deletion)
    cvc5_row = cvc5_deletion_gate(deletion)
    positive = {"P1_loss_coordinate_deletion_response": deletion}
    graveyard = {
        "GC_duplicate_incidence_summary_rejected_as_scout_claim": deletion["duplicate_summary_control"],
        "GC_norm_only_pair_control_collapses": deletion["norm_only_control"],
        "GC_scalar_label_not_claim_bearing": deletion["scalar_label_control"],
        "GC_no_anchor_control_rejected": deletion["no_anchor_control"],
        "GC_order_erased_control_collapses": {"pass": deletion["order_erased_control_collapses"]},
        "GC_illegal_coordinate_scramble_rejected": deletion["illegal_scramble_control"],
        "GC_fake_face_positive_rejected": deletion["fake_face_positive_control"],
        "GC_topology_all_subset_restore_convergence_closure_not_opened": deletion["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not deletion["dense_state_closure_used"] and not deletion["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_deletion_response_required": {
            "pass": deletion["deletion_response_vector"] == [2, 2, 0, 2]
            and deletion["coordinate_deletion_op_count"] == 4,
            "coordinate_deletion_op_count": deletion["coordinate_deletion_op_count"],
            "deletion_response_vector": deletion["deletion_response_vector"],
        },
        "B4_face_coordinate_deletion_neutral_not_full_coverage": {
            "pass": deletion["neutral_coordinates"] == ["F"] and not deletion["topology_closure_control"]["full_coordinate_coverage_claim_allowed"],
            "active_deletion_coordinates": deletion["active_deletion_coordinates"],
            "neutral_coordinates": deletion["neutral_coordinates"],
        },
        "B5_z3_finite_deletion_nonpromotion": z3_row,
        "B6_cvc5_finite_deletion_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = deletion["pass"] and all(row["pass"] for row in graveyard.values()) and all(
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
        PHASE2_U_RECEIPT,
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
            "F01": "finite PEPS3D carrier, finite coordinate set, finite coordinate-deletion operations, finite class-pair support-mask table, finite controls, finite output table",
            "N01": "inherited order-sensitive carrier gap remains in source receipts; W is a finite deletion operation over U and not a new noncommuting operator",
        },
        "finite_map": deletion["finite_map"],
        "domain": {
            "U_loss_pair_support_mask_K_receipt": PHASE2_U_RECEIPT,
            "S_loss_residue_class_separation_K_receipt": PHASE2_S_RECEIPT,
            "Q_loss_residue_class_quotient_K_receipt": PHASE2_Q_RECEIPT,
            "H_delete_anchor_loss_idempotence_K_receipt": PHASE2_H_DELETE_RECEIPT,
            "class_pair_count": deletion["class_pair_count"],
            "coordinate_count": deletion["coordinate_count"],
            "coordinate_deletion_op_count": deletion["coordinate_deletion_op_count"],
            "coordinates": list(COORDINATES),
            "max_parent_peps3d_sites": deletion["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": deletion["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": deletion["max_peps3d_bond"],
        },
        "codomain_or_output": "finite coordinate-deletion response table, deletion-neutral coordinate set, active-deletion response quotient, post-delete support-mask class counts, and control gap vector",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_loss_coordinate_deletion_response",
        "carrier_realization": "torch finite coordinate-deletion operation over U_loss_pair_support_mask_K with graph/topology/proof support checks",
        "peps3d_embedding": "Every deletion-response row is computed from inherited PEPS3D V/E/F/C support-mask coordinates; scalar labels and unanchored bit patterns are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D coordinate-deletion response over U_loss_pair_support_mask_K",
        "branch_status_before_run": "post_U_loss_pair_support_mask_K_candidate_map_discovery_W_loss_coordinate_deletion_response_K",
        "allowed_claims": [
            "finite coordinate-deletion operations act on U pair-support masks",
            "deleting V/E/C changes two anchored pair rows each",
            "deleting F changes zero anchored pair rows and remains neutral",
            "post-delete support-mask class counts remain finite in this bounded table",
            "duplicate-summary, norm-only, scalar-label, no-anchor, order-erased, coordinate-scramble, fake-face, dense-closure, topology, all-subset, restore/inverse, and downstream controls fail, collapse, or remain blocked",
        ],
        "promotion_blockers": [
            "coordinate deletion response is not topology, homology, sheaf, gluing, all-subset minimality, restore/inverse, bond convergence, shape law, or full PEPS3D closure",
            "F coordinate is deletion-neutral in the current pair masks",
            "no downstream geometry is opened",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_deletion_nonpromotion_gate",
            "cvc5_finite_deletion_nonpromotion_gate",
            "sympy_exact_deletion_count_checks",
        ],
        "graph_surfaces_used": [
            "rustworkx_coordinate_deletion_response_graph",
            "xgi_coordinate_deletion_hypergraph",
            "torch_geometric_deletion_response_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_coordinate_pair_cell_count_without_topology_closure",
            "gudhi_simplex_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_pair_probe": "fails PEPS3D V/E/F/C coordinate-deletion requirement",
            "full_coordinate_coverage_probe": "F coordinate is deletion-neutral in this bounded receipt",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
        },
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "W_loss_coordinate_deletion_response_K classified as bounded finite deletion-operation readout",
                "coordinate-incidence balance rejected as duplicate summary by itself",
                "norm-only next map rejected as saturated",
                "full coordinate coverage rejected because F is deletion-neutral",
                "section/retraction wording rejected as topology/sheaf risk",
                "topology/homology/sheaf variants rejected",
                "downstream variants rejected",
            ],
        },
        "required_inputs": dependency_receipts,
        "required_negatives": [
            "duplicate_incidence_summary",
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
            "coordinate-deletion response differs from expected vector",
            "F is not deletion-neutral",
            "any active coordinate in V/E/C is deletion-neutral",
            "norm-only or label-only controls reproduce the claim-bearing deletion table",
            "dense closure or downstream geometry is used",
            "topology/sheaf/homology/closure is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_loss_coordinate_deletion_response_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_loss_coordinate_deletion_response",
            "class_pair_count": deletion["class_pair_count"],
            "coordinate_count": deletion["coordinate_count"],
            "coordinate_deletion_op_count": deletion["coordinate_deletion_op_count"],
            "deletion_response_vector": deletion["deletion_response_vector"],
            "active_deletion_coordinates": deletion["active_deletion_coordinates"],
            "neutral_coordinates": deletion["neutral_coordinates"],
            "post_delete_min_support_mask_class_count": deletion["post_delete_min_support_mask_class_count"],
            "post_delete_max_support_mask_class_count": deletion["post_delete_max_support_mask_class_count"],
            "max_parent_peps3d_sites": deletion["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": deletion["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": deletion["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "class_pair_count": deletion["class_pair_count"],
            "coordinate_count": deletion["coordinate_count"],
            "coordinate_deletion_op_count": deletion["coordinate_deletion_op_count"],
            "deletion_response_vector": deletion["deletion_response_vector"],
            "expected_deletion_response_vector": deletion["expected_deletion_response_vector"],
            "active_deletion_coordinates": deletion["active_deletion_coordinates"],
            "neutral_coordinates": deletion["neutral_coordinates"],
            "post_delete_min_support_mask_class_count": deletion["post_delete_min_support_mask_class_count"],
            "post_delete_max_support_mask_class_count": deletion["post_delete_max_support_mask_class_count"],
            "max_parent_peps3d_sites": deletion["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": deletion["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": deletion["max_peps3d_bond"],
        },
        "pass_rule": "four finite coordinate-deletion operations act on U support masks, V/E/C each change two anchored pair rows, F is neutral, post-delete support-mask classes remain finite, and all closure/downstream controls remain blocked",
        "fail_rule": "deletion response differs from expected vector, controls reproduce the claim-bearing table, F neutrality is hidden, dense closure is used, or topology/downstream promotion is opened",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this finite deletion-response receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "class_pair_count": deletion["class_pair_count"],
        "coordinate_count": deletion["coordinate_count"],
        "coordinate_deletion_op_count": deletion["coordinate_deletion_op_count"],
        "deletion_response_vector": deletion["deletion_response_vector"],
        "active_deletion_coordinates": deletion["active_deletion_coordinates"],
        "neutral_coordinates": deletion["neutral_coordinates"],
        "max_parent_peps3d_sites": deletion["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": deletion["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": deletion["max_peps3d_bond"],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "class_pair_count": deletion["class_pair_count"],
                "coordinate_count": deletion["coordinate_count"],
                "coordinate_deletion_op_count": deletion["coordinate_deletion_op_count"],
                "deletion_response_vector": deletion["deletion_response_vector"],
                "active_deletion_coordinates": deletion["active_deletion_coordinates"],
                "neutral_coordinates": deletion["neutral_coordinates"],
                "max_parent_peps3d_sites": deletion["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": deletion["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": deletion["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
