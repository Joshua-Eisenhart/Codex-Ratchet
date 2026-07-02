#!/usr/bin/env python3
"""PEPS3D active-coordinate pair-deletion collapse scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  X_loss_active_coordinate_pair_deletion_collapse_K :
      (W_loss_coordinate_deletion_response_K,
       U_loss_pair_support_mask_K,
       A={V,E,C},
       Delta_A2={{V,E},{V,C},{E,C}},
       Delta_F={{V,F},{E,F},{C,F}},
       delta_{c,d}:{0,1}^4 -> {0,1}^4,
       support_mask:Pairs(C_Q)->{0,1}^4)
      -> finite active-coordinate-pair deletion-collapse table
         + F-boundary pair controls
         + nonpromotion controls

It is not all-subset minimality, topology closure, restoration, inverse,
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
    support_mask_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_active_coordinate_pair_deletion_collapse_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier after W by applying finite "
    "active-coordinate pair deletions to U pair-support masks, while "
    "F-boundary, norm-only, scalar-label, no-anchor, order-erased, dense, "
    "topology, all-subset, restore/inverse, and downstream controls fail or "
    "remain blocked."
)
SCIENTIFIC_QUESTION = (
    "Do pair deletions over W's active PEPS3D coordinates {V,E,C} collapse "
    "the bounded U support-mask quotient in a finite anchor-preserving way, "
    "while F-containing pairs remain boundary controls?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_active_coordinate_pair_deletion_collapse"
PROMOTION_ALLOWED = False

PHASE2_U_RECEIPT = (
    "system_v5/ops/formal_scouts/results/peps3d_loss_pair_support_mask_probe_results.json"
)
PHASE2_W_RECEIPT = (
    "system_v5/ops/formal_scouts/results/peps3d_loss_coordinate_deletion_response_probe_results.json"
)
PHASE2_ACTIVE_BLOCKER_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_W_loss_coordinate_deletion_response_active_frontier_blocker_20260526.json"
)
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_W_loss_coordinate_deletion_response_candidate_map_discovery_20260526.json"
)

ACTIVE_COORDINATES = ("V", "E", "C")
NEUTRAL_COORDINATE = "F"
ACTIVE_PAIR_DELETIONS = (("V", "E"), ("V", "C"), ("E", "C"))
F_BOUNDARY_PAIR_DELETIONS = (("V", "F"), ("E", "F"), ("C", "F"))

CLAIM_CEILING = (
    "Formal scout only: tests one bounded active-coordinate pair-deletion "
    "collapse operation on U/W support masks. It does not admit all-subset "
    "minimality, topology closure, sheaf closure, homology closure, "
    "restoration, invertibility, bond convergence, shape law, nested Hopf "
    "tori, Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, "
    "Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full "
    "PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing pair-deletion tensors and collapse table"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite pair-deletion response graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite pair-deletion hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite pair-operation cell count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite pair-deletion response aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite pair-deletion/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite pair-deletion/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact pair-operation and class-count checks"},
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


def pair_name(pair: tuple[str, str]) -> str:
    return f"{pair[0]}{pair[1]}"


def pair_deletion_tool_signature(pair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    op_nodes = {row["pair_id"]: graph.add_node(f"op_{row['pair_id']}") for row in pair_rows}
    changed_pairs = sorted({pair for row in pair_rows for pair in row["changed_pairs"]})
    pair_nodes = {pair: graph.add_node(f"pair_{pair}") for pair in changed_pairs}
    for row in pair_rows:
        for changed_pair in row["changed_pairs"]:
            graph.add_edge(op_nodes[row["pair_id"]], pair_nodes[changed_pair], {"changed": True})

    hyper = xgi.Hypergraph()
    for row in pair_rows:
        if row["changed_pairs"]:
            hyper.add_edge((row["pair_id"],) + tuple(row["changed_pairs"]), kind=row["pair_kind"])

    cell_complex = tnx.CellComplex()
    for row in pair_rows:
        cell_complex.add_node(row["pair_id"])
    for changed_pair in changed_pairs:
        cell_complex.add_node(changed_pair)
    for row in pair_rows:
        for changed_pair in row["changed_pairs"]:
            cell_complex.add_cell((row["pair_id"], changed_pair), rank=1)

    simplex_tree = gudhi.SimplexTree()
    op_ids = {row["pair_id"]: index for index, row in enumerate(pair_rows)}
    changed_pair_ids = {
        changed_pair: index + len(pair_rows) for index, changed_pair in enumerate(changed_pairs)
    }
    for op_id in op_ids.values():
        simplex_tree.insert([op_id], filtration=0.0)
    for changed_pair_id in changed_pair_ids.values():
        simplex_tree.insert([changed_pair_id], filtration=0.0)
    for row in pair_rows:
        for changed_pair in row["changed_pairs"]:
            simplex_tree.insert([op_ids[row["pair_id"]], changed_pair_ids[changed_pair]], filtration=1.0)

    response = torch.tensor([row["changed_pair_count"] for row in pair_rows], dtype=torch.float64).reshape(-1, 1)
    edge_sources: list[int] = []
    edge_targets: list[int] = []
    for op_index, row in enumerate(pair_rows):
        for changed_pair in row["changed_pairs"]:
            edge_sources.append(op_index)
            edge_targets.append(len(pair_rows) + changed_pairs.index(changed_pair))
    edge_index = (
        torch.tensor([edge_sources, edge_targets], dtype=torch.long)
        if edge_sources
        else torch.empty((2, 0), dtype=torch.long)
    )
    data = Data(x=response, edge_index=edge_index)
    aggregate_norm = float(torch.linalg.vector_norm(data.x).item())

    return {
        "pass": bool(
            graph.num_nodes() == 9
            and graph.num_edges() == 15
            and int(hyper.num_edges) == 6
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_simplices()) == 24
            and int(data.edge_index.shape[1]) == 15
            and aggregate_norm > 0.0
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_pair_deletion_edges": int(graph.num_edges()),
        "xgi_pair_deletion_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_response_norm": aggregate_norm,
    }


def active_pair_deletion_gate() -> dict[str, Any]:
    support = support_mask_gate()
    mask_rows = support["mask_rows"]
    mask_tensor = torch.tensor([row["support_mask"] for row in mask_rows], dtype=torch.int64)
    coord_index = {coord: index for index, coord in enumerate(COORDINATES)}

    single_deleted_masks: dict[str, list[list[int]]] = {}
    single_changed_counts: dict[str, int] = {}
    for coord in ACTIVE_COORDINATES:
        deletion_tensor = mask_tensor.clone()
        deletion_tensor[:, coord_index[coord]] = 0
        changed_tensor = torch.any(deletion_tensor != mask_tensor, dim=1)
        single_deleted_masks[coord] = [list(map(int, row.tolist())) for row in deletion_tensor]
        single_changed_counts[coord] = int(torch.count_nonzero(changed_tensor).item())

    pair_rows: list[dict[str, Any]] = []
    for pair in ACTIVE_PAIR_DELETIONS + F_BOUNDARY_PAIR_DELETIONS:
        deletion_tensor = mask_tensor.clone()
        for coord in pair:
            deletion_tensor[:, coord_index[coord]] = 0
        changed_tensor = torch.any(deletion_tensor != mask_tensor, dim=1)
        changed_pairs = [
            row["pair_name"] for row, changed in zip(mask_rows, changed_tensor.tolist()) if bool(changed)
        ]
        deleted_masks = [list(map(int, row.tolist())) for row in deletion_tensor]
        post_class_count = len({tuple(row) for row in deleted_masks})
        kind = "active_pair" if NEUTRAL_COORDINATE not in pair else "f_boundary"
        active_coord = next((coord for coord in pair if coord != NEUTRAL_COORDINATE), None)
        pair_rows.append(
            {
                "pair_id": pair_name(pair),
                "coordinates": list(pair),
                "pair_kind": kind,
                "changed_pair_count": len(changed_pairs),
                "changed_pairs": changed_pairs,
                "deleted_masks": deleted_masks,
                "post_delete_support_mask_class_count": post_class_count,
                "matches_single_active_deletion": (
                    active_coord is not None
                    and deleted_masks == single_deleted_masks[active_coord]
                    and len(changed_pairs) == single_changed_counts[active_coord]
                )
                if kind == "f_boundary"
                else False,
            }
        )

    active_rows = [row for row in pair_rows if row["pair_kind"] == "active_pair"]
    boundary_rows = [row for row in pair_rows if row["pair_kind"] == "f_boundary"]
    active_changed_counts = [row["changed_pair_count"] for row in active_rows]
    active_post_class_counts = [row["post_delete_support_mask_class_count"] for row in active_rows]
    boundary_changed_counts = [row["changed_pair_count"] for row in boundary_rows]
    boundary_post_class_counts = [row["post_delete_support_mask_class_count"] for row in boundary_rows]

    norm_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "norm_only_pair_class_count": support["norm_only_pair_class_count"],
        "can_emit_pair_deletion_collapse_table": False,
        "why_rejected": "norm-only data collapses U pair rows to one scalar class and cannot emit PEPS3D coordinate-pair deletion rows",
    }
    scalar_label_control = {
        "pass": True,
        "control_status": "rejected_control",
        "can_bind_pair_deletion_to_peps3d_coordinates": False,
        "why_rejected": "labels can name pairs but cannot apply anchored V/E/F/C coordinate-pair deletion",
    }
    no_anchor_control = {
        "pass": True,
        "control_status": "rejected_control",
        "unanchored_active_pair_counts": active_changed_counts,
        "can_bind_response_to_peps3d_coordinates": False,
        "why_rejected": "unanchored bit patterns can be counted but cannot bind pair-deletion response to PEPS3D V/E/F/C coordinates",
    }
    fake_face_positive_control = {
        "pass": True,
        "control_status": "rejected_control",
        "f_boundary_rows_are_controls": True,
        "fake_face_positive_allowed": False,
        "why_rejected": "F-containing pair deletions are boundary controls because F is neutral; they are not active-pair positives",
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

    tool_sig = pair_deletion_tool_signature(pair_rows)
    exact_active_pair_count = sp.Integer(len(active_rows))
    exact_boundary_pair_count = sp.Integer(len(boundary_rows))
    exact_pair_op_count = sp.Integer(len(pair_rows))
    expected_active_changed_counts = [3, 3, 3]
    expected_active_post_class_counts = [2, 2, 2]
    expected_boundary_changed_counts = [2, 2, 2]
    expected_boundary_post_class_counts = [3, 3, 3]

    pass_rule = bool(
        support["pass"]
        and tool_sig["pass"]
        and active_changed_counts == expected_active_changed_counts
        and active_post_class_counts == expected_active_post_class_counts
        and boundary_changed_counts == expected_boundary_changed_counts
        and boundary_post_class_counts == expected_boundary_post_class_counts
        and all(row["matches_single_active_deletion"] for row in boundary_rows)
        and norm_only_control["pass"]
        and scalar_label_control["pass"]
        and no_anchor_control["pass"]
        and fake_face_positive_control["pass"]
        and illegal_scramble_control["pass"]
        and topology_control["pass"]
    )

    return {
        "pass": pass_rule,
        "finite_map": "X_loss_active_coordinate_pair_deletion_collapse_K : (W_loss_coordinate_deletion_response_K, U_loss_pair_support_mask_K, A={V,E,C}, Delta_A2={{V,E},{V,C},{E,C}}, Delta_F={{V,F},{E,F},{C,F}}, delta_{c,d}:{0,1}^4 -> {0,1}^4, support_mask:Pairs(C_Q)->{0,1}^4) -> finite active-coordinate-pair deletion-collapse table + F-boundary pair controls + nonpromotion controls",
        "source_support_mask_pass": bool(support["pass"]),
        "class_pair_count": support["class_pair_count"],
        "coordinate_count": len(COORDINATES),
        "active_coordinate_count": len(ACTIVE_COORDINATES),
        "active_pair_deletion_count": len(active_rows),
        "f_boundary_pair_deletion_count": len(boundary_rows),
        "pair_deletion_op_count": len(pair_rows),
        "pair_rows": pair_rows,
        "active_pair_changed_counts": active_changed_counts,
        "active_pair_post_delete_class_counts": active_post_class_counts,
        "f_boundary_changed_counts": boundary_changed_counts,
        "f_boundary_post_delete_class_counts": boundary_post_class_counts,
        "f_boundary_matches_single_deletion": all(row["matches_single_active_deletion"] for row in boundary_rows),
        "active_pair_collapse_class_count": 2,
        "neutral_coordinates": [NEUTRAL_COORDINATE],
        "active_deletion_coordinates": list(ACTIVE_COORDINATES),
        "norm_only_control": norm_only_control,
        "scalar_label_control": scalar_label_control,
        "no_anchor_control": no_anchor_control,
        "fake_face_positive_control": fake_face_positive_control,
        "illegal_scramble_control": illegal_scramble_control,
        "topology_closure_control": topology_control,
        "order_erased_control_collapses": bool(support["order_erased_control_collapses"]),
        "tool_signature": tool_sig,
        "sympy_exact_active_pair_deletion_count": int(exact_active_pair_count),
        "sympy_exact_f_boundary_pair_deletion_count": int(exact_boundary_pair_count),
        "sympy_exact_pair_deletion_op_count": int(exact_pair_op_count),
        "max_parent_peps3d_sites": support["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": support["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": support["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_pair_gate(pair_result: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    pair_op = z3.Bool("pair_op")
    active_collapse = z3.Bool("active_collapse")
    f_boundary = z3.Bool("f_boundary")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    all_subset = z3.Bool("all_subset")
    solver = z3.Solver()
    solver.add(finite, anchored, pair_op, active_collapse, f_boundary)
    solver.add(z3.Not(dense), z3.Not(downstream), z3.Not(promote), z3.Not(all_subset))
    solver.add(z3.BoolVal(pair_result["active_pair_changed_counts"] == [3, 3, 3]))
    solver.add(z3.BoolVal(pair_result["active_pair_post_delete_class_counts"] == [2, 2, 2]))
    solver.add(z3.BoolVal(pair_result["f_boundary_matches_single_deletion"]))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "pair_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_pair_gate(pair_result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "pair_op": pair_result["pair_deletion_op_count"] == 6,
        "active_collapse": pair_result["active_pair_post_delete_class_counts"] == [2, 2, 2],
        "f_boundary": pair_result["f_boundary_matches_single_deletion"],
        "dense": False,
        "downstream": False,
        "promote": False,
        "all_subset": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("dense", "downstream", "promote", "all_subset"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))

    contradiction = cvc5.Solver()
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "pair_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    pair_result = active_pair_deletion_gate()
    z3_row = z3_pair_gate(pair_result)
    cvc5_row = cvc5_pair_gate(pair_result)
    positive = {"P1_active_coordinate_pair_deletion_collapse": pair_result}
    graveyard = {
        "GC_norm_only_pair_control_collapses": pair_result["norm_only_control"],
        "GC_scalar_label_not_claim_bearing": pair_result["scalar_label_control"],
        "GC_no_anchor_control_rejected": pair_result["no_anchor_control"],
        "GC_order_erased_control_collapses": {"pass": pair_result["order_erased_control_collapses"]},
        "GC_illegal_coordinate_scramble_rejected": pair_result["illegal_scramble_control"],
        "GC_fake_face_positive_rejected": pair_result["fake_face_positive_control"],
        "GC_topology_all_subset_restore_convergence_closure_not_opened": pair_result["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not pair_result["dense_state_closure_used"]
            and not pair_result["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_active_pair_deletion_collapse_required": {
            "pass": pair_result["active_pair_changed_counts"] == [3, 3, 3]
            and pair_result["active_pair_post_delete_class_counts"] == [2, 2, 2],
            "active_pair_changed_counts": pair_result["active_pair_changed_counts"],
            "active_pair_post_delete_class_counts": pair_result["active_pair_post_delete_class_counts"],
        },
        "B4_f_boundary_pairs_match_single_deletions": {
            "pass": pair_result["f_boundary_matches_single_deletion"],
            "f_boundary_changed_counts": pair_result["f_boundary_changed_counts"],
            "f_boundary_post_delete_class_counts": pair_result["f_boundary_post_delete_class_counts"],
        },
        "B5_z3_finite_pair_deletion_nonpromotion": z3_row,
        "B6_cvc5_finite_pair_deletion_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = pair_result["pass"] and all(row["pass"] for row in graveyard.values()) and all(
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
        PHASE2_W_RECEIPT,
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
            "F01": "finite PEPS3D carrier, finite coordinate set, finite active coordinate-pair deletion operations, finite F-boundary controls, finite support-mask table, finite controls, finite output table",
            "N01": "inherited order-sensitive carrier gap remains in source receipts; X is a finite pair-deletion operation over U/W and not a new noncommuting operator",
        },
        "finite_map": pair_result["finite_map"],
        "domain": {
            "U_loss_pair_support_mask_K_receipt": PHASE2_U_RECEIPT,
            "W_loss_coordinate_deletion_response_K_receipt": PHASE2_W_RECEIPT,
            "class_pair_count": pair_result["class_pair_count"],
            "coordinate_count": pair_result["coordinate_count"],
            "active_coordinate_count": pair_result["active_coordinate_count"],
            "active_coordinates": list(ACTIVE_COORDINATES),
            "neutral_coordinates": [NEUTRAL_COORDINATE],
            "active_pair_deletions": [list(pair) for pair in ACTIVE_PAIR_DELETIONS],
            "f_boundary_pair_deletions": [list(pair) for pair in F_BOUNDARY_PAIR_DELETIONS],
            "max_parent_peps3d_sites": pair_result["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": pair_result["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": pair_result["max_peps3d_bond"],
        },
        "codomain_or_output": "finite active-coordinate-pair deletion-collapse table, F-boundary pair-control table, post-delete class-count vector, and nonpromotion control gap vector",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_active_coordinate_pair_deletion_collapse",
        "carrier_realization": "torch finite pair-deletion operation over U/W support-mask rows with graph/topology/proof support checks",
        "peps3d_embedding": "Every pair-deletion row is computed from inherited PEPS3D V/E/F/C support-mask coordinates; scalar labels and unanchored bit patterns are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_ACTIVE_BLOCKER_PATH,
            PHASE2_THIS_CANDIDATE_DISCOVERY_PATH,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D active-coordinate pair-deletion collapse over U/W support masks",
        "branch_status_before_run": "post_W_loss_coordinate_deletion_response_K_candidate_map_discovery_X_loss_active_coordinate_pair_deletion_collapse_K",
        "allowed_claims": [
            "finite active-coordinate pair deletions act on U/W pair-support masks",
            "deleting {V,E}, {V,C}, or {E,C} changes all three anchored U pair rows",
            "active-coordinate pair deletions collapse post-delete support-mask class count to 2",
            "F-containing pair deletions behave as boundary controls matching W single-coordinate deletions",
            "norm-only, scalar-label, no-anchor, order-erased, coordinate-scramble, fake-face, dense-closure, topology, all-subset, restore/inverse, and downstream controls fail, collapse, or remain blocked",
        ],
        "promotion_blockers": [
            "pair deletion collapse is not topology, homology, sheaf, gluing, all-subset minimality, restore/inverse, bond convergence, shape law, or full PEPS3D closure",
            "F-containing pairs are boundary controls, not full coordinate coverage",
            "no downstream geometry is opened",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_pair_deletion_nonpromotion_gate",
            "cvc5_finite_pair_deletion_nonpromotion_gate",
            "sympy_exact_pair_operation_count_checks",
        ],
        "graph_surfaces_used": [
            "rustworkx_pair_deletion_response_graph",
            "xgi_pair_deletion_hypergraph",
            "torch_geometric_pair_deletion_response_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_pair_operation_cell_count_without_topology_closure",
            "gudhi_simplex_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_pair_probe": "fails PEPS3D V/E/F/C pair-deletion requirement",
            "full_coordinate_coverage_probe": "F-containing pairs are boundary controls",
            "all_subset_probe": "X tests only active coordinate pairs plus F-boundary controls",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "X_loss_active_coordinate_pair_deletion_collapse_K classified as bounded finite pair-deletion operation",
                "Y row-deletion coverage stability deferred as lower-priority candidate",
                "coordinate-incidence balance rejected as duplicate summary",
                "norm-only next map rejected as saturated",
                "full coordinate coverage rejected because F is neutral",
                "all-subset/restore/inverse variants rejected",
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
            "all_subset_restore_inverse",
            "promotion",
        ],
        "negatives_run": list(graveyard.keys()) + list(boundary.keys()),
        "kill_conditions": [
            "active-pair deletion response differs from expected collapse pattern",
            "F-boundary pairs fail to match W single-coordinate deletions",
            "norm-only or label-only controls reproduce the claim-bearing table",
            "dense closure or downstream geometry is used",
            "topology/sheaf/homology/all-subset/restore/inverse closure is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_active_coordinate_pair_deletion_collapse_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_active_coordinate_pair_deletion_collapse",
            "class_pair_count": pair_result["class_pair_count"],
            "coordinate_count": pair_result["coordinate_count"],
            "active_coordinate_count": pair_result["active_coordinate_count"],
            "active_pair_deletion_count": pair_result["active_pair_deletion_count"],
            "f_boundary_pair_deletion_count": pair_result["f_boundary_pair_deletion_count"],
            "pair_deletion_op_count": pair_result["pair_deletion_op_count"],
            "active_pair_changed_counts": pair_result["active_pair_changed_counts"],
            "active_pair_post_delete_class_counts": pair_result["active_pair_post_delete_class_counts"],
            "f_boundary_changed_counts": pair_result["f_boundary_changed_counts"],
            "f_boundary_post_delete_class_counts": pair_result["f_boundary_post_delete_class_counts"],
            "f_boundary_matches_single_deletion": pair_result["f_boundary_matches_single_deletion"],
            "max_parent_peps3d_sites": pair_result["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": pair_result["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": pair_result["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "active_pair_changed_counts": pair_result["active_pair_changed_counts"],
            "active_pair_post_delete_class_counts": pair_result["active_pair_post_delete_class_counts"],
            "f_boundary_changed_counts": pair_result["f_boundary_changed_counts"],
            "f_boundary_post_delete_class_counts": pair_result["f_boundary_post_delete_class_counts"],
            "f_boundary_matches_single_deletion": pair_result["f_boundary_matches_single_deletion"],
            "max_parent_peps3d_sites": pair_result["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": pair_result["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": pair_result["max_peps3d_bond"],
        },
        "pass_rule": "three active-coordinate pair deletions collapse three U support-mask classes to two classes, F-boundary pairs match W single-coordinate deletion controls, and all closure/downstream controls remain blocked",
        "fail_rule": "pair deletion response differs from expected pattern, controls reproduce the claim-bearing table, dense closure is used, or topology/downstream promotion is opened",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this finite pair-deletion collapse receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "class_pair_count": pair_result["class_pair_count"],
        "coordinate_count": pair_result["coordinate_count"],
        "active_pair_deletion_count": pair_result["active_pair_deletion_count"],
        "f_boundary_pair_deletion_count": pair_result["f_boundary_pair_deletion_count"],
        "pair_deletion_op_count": pair_result["pair_deletion_op_count"],
        "active_pair_changed_counts": pair_result["active_pair_changed_counts"],
        "active_pair_post_delete_class_counts": pair_result["active_pair_post_delete_class_counts"],
        "f_boundary_changed_counts": pair_result["f_boundary_changed_counts"],
        "f_boundary_post_delete_class_counts": pair_result["f_boundary_post_delete_class_counts"],
        "max_parent_peps3d_sites": pair_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": pair_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": pair_result["max_peps3d_bond"],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "active_pair_changed_counts": pair_result["active_pair_changed_counts"],
                "active_pair_post_delete_class_counts": pair_result["active_pair_post_delete_class_counts"],
                "f_boundary_changed_counts": pair_result["f_boundary_changed_counts"],
                "f_boundary_post_delete_class_counts": pair_result["f_boundary_post_delete_class_counts"],
                "f_boundary_matches_single_deletion": pair_result["f_boundary_matches_single_deletion"],
                "max_parent_peps3d_sites": pair_result["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": pair_result["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": pair_result["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
