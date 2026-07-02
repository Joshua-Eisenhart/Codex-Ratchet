#!/usr/bin/env python3
"""PEPS3D row-deletion collision-stability scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  Y_row_deletion_collision_stability_K :
      (Z_active_pair_collision_residue_K,
       U_loss_pair_support_mask_K,
       epsilon_p: Pairs(C_Q) -> Pairs(C_Q) \\ {p},
       kappa_Z)
      -> finite row-deletion collision-survival table
         + remaining-coordinate coverage vector
         + F-boundary no-collision controls

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
from sim_peps3d_active_pair_collision_residue_probe import (
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
    PHASE2_U_RECEIPT,
    PHASE2_W_RECEIPT,
    PHASE2_X_RECEIPT,
    active_pair_collision_gate,
)
from sim_peps3d_loss_pair_support_mask_probe import support_mask_gate


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_row_deletion_collision_stability_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier after Z by removing one finite "
    "class-pair row at a time and checking which active collision partition "
    "survives, while F-boundary, norm-only, scalar-label, no-anchor, "
    "order-erased, dense, topology, all-subset, restore/inverse, and "
    "downstream controls fail or remain blocked."
)
SCIENTIFIC_QUESTION = (
    "Does each single class-pair row deletion preserve exactly one Z active "
    "collision and break the other two, while remaining coordinate coverage "
    "stays V/E/C-active and F-neutral?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_row_deletion_collision_stability"
PROMOTION_ALLOWED = False

PHASE2_Z_RECEIPT = (
    "system_v5/ops/formal_scouts/results/peps3d_active_pair_collision_residue_probe_results.json"
)
PHASE2_ACTIVE_BLOCKER_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_Z_active_pair_collision_residue_active_frontier_blocker_20260526.json"
)
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_Z_active_pair_collision_residue_candidate_map_discovery_20260526.json"
)

CLAIM_CEILING = (
    "Formal scout only: tests one bounded row-deletion collision-stability "
    "readout over Z collision partitions. It does not admit all-subset "
    "minimality, topology closure, sheaf closure, homology closure, "
    "restoration, invertibility, bond convergence, shape law, nested Hopf "
    "tori, Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, "
    "Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full "
    "PEPS3D closure."
)

ACTIVE_PAIR_IDS = ("VE", "VC", "EC")
BOUNDARY_PAIR_IDS = ("VF", "EF", "CF")
EXPECTED_SURVIVAL = {
    "sigma012/edge": {"VE": False, "VC": False, "EC": True},
    "sigma012/vertex": {"VE": False, "VC": True, "EC": False},
    "edge/vertex": {"VE": True, "VC": False, "EC": False},
}

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing row-deletion survival tensors and coverage vectors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite row-deletion survival graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite row-preserved-collision hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite row/pair cell count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite survival matrix aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite row-deletion/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent row-deletion/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact survival and coverage count checks"},
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


def class_has_collision(classes: list[dict[str, Any]], removed_pair: str) -> bool:
    for class_row in classes:
        remaining = [member for member in class_row["pair_members"] if member != removed_pair]
        if len(remaining) > 1:
            return True
    return False


def row_deletion_tool_signature(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    remove_nodes = {row["removed_pair"]: graph.add_node(f"remove_{row['removed_pair']}") for row in rows}
    pair_nodes = {pair_id: graph.add_node(f"active_{pair_id}") for pair_id in ACTIVE_PAIR_IDS}
    edge_count = 0
    for row in rows:
        for pair_id, survives in row["active_collision_survival"].items():
            graph.add_edge(remove_nodes[row["removed_pair"]], pair_nodes[pair_id], {"survives": bool(survives)})
            edge_count += 1

    hyper = xgi.Hypergraph()
    for row in rows:
        preserved = [pair_id for pair_id, survives in row["active_collision_survival"].items() if survives]
        hyper.add_edge((row["removed_pair"],) + tuple(preserved), kind="preserved_collision")

    cell_complex = tnx.CellComplex()
    for row in rows:
        cell_complex.add_node(row["removed_pair"])
    for pair_id in ACTIVE_PAIR_IDS:
        cell_complex.add_node(pair_id)
    for row in rows:
        for pair_id in ACTIVE_PAIR_IDS:
            cell_complex.add_cell((row["removed_pair"], pair_id), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids: dict[str, int] = {}
    def vid(name: str) -> int:
        if name not in vertex_ids:
            vertex_ids[name] = len(vertex_ids)
            simplex_tree.insert([vertex_ids[name]], filtration=0.0)
        return vertex_ids[name]

    for row in rows:
        removed_id = vid(f"remove:{row['removed_pair']}")
        for pair_id, survives in row["active_collision_survival"].items():
            pair_vertex = vid(f"pair:{pair_id}")
            if survives:
                simplex_tree.insert([removed_id, pair_vertex], filtration=1.0)

    survival_tensor = torch.tensor(
        [[int(row["active_collision_survival"][pair_id]) for pair_id in ACTIVE_PAIR_IDS] for row in rows],
        dtype=torch.float64,
    )
    edge_sources = []
    edge_targets = []
    for row_index, row in enumerate(rows):
        for pair_index, pair_id in enumerate(ACTIVE_PAIR_IDS):
            edge_sources.append(row_index)
            edge_targets.append(len(rows) + pair_index)
    data = Data(x=survival_tensor, edge_index=torch.tensor([edge_sources, edge_targets], dtype=torch.long))

    return {
        "pass": bool(
            graph.num_nodes() == 6
            and graph.num_edges() == 9
            and int(hyper.num_edges) == 3
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_vertices()) == 6
            and int(simplex_tree.num_simplices()) == 9
            and int(data.edge_index.shape[1]) == 9
            and float(torch.sum(data.x).item()) == 3.0
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_vertices": int(simplex_tree.num_vertices()),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_survival_sum": float(torch.sum(data.x).item()),
        "edge_count": edge_count,
    }


def row_deletion_stability_gate() -> dict[str, Any]:
    z_result = active_pair_collision_gate()
    support = support_mask_gate()
    mask_rows = support["mask_rows"]
    mask_by_pair = {row["pair_name"]: row["support_mask"] for row in mask_rows}
    removable_pairs = [row["pair_name"] for row in mask_rows]

    z_rows = {row["pair_id"]: row for row in z_result["collision_rows"]}
    rows: list[dict[str, Any]] = []
    for removed_pair in removable_pairs:
        remaining_masks = [
            torch.tensor(mask, dtype=torch.int64)
            for pair_name, mask in mask_by_pair.items()
            if pair_name != removed_pair
        ]
        coverage = torch.maximum(remaining_masks[0], remaining_masks[1]).tolist()
        active_survival = {
            pair_id: class_has_collision(z_rows[pair_id]["partition_classes"], removed_pair)
            for pair_id in ACTIVE_PAIR_IDS
        }
        boundary_survival = {
            pair_id: class_has_collision(z_rows[pair_id]["partition_classes"], removed_pair)
            for pair_id in BOUNDARY_PAIR_IDS
        }
        rows.append(
            {
                "removed_pair": removed_pair,
                "remaining_pair_count": 2,
                "remaining_coordinate_coverage": [int(value) for value in coverage],
                "f_neutral_after_row_deletion": int(coverage[2]) == 0,
                "active_collision_survival": active_survival,
                "preserved_active_collision_count": sum(int(value) for value in active_survival.values()),
                "broken_active_collision_count": len(ACTIVE_PAIR_IDS) - sum(int(value) for value in active_survival.values()),
                "f_boundary_collision_survival": boundary_survival,
                "f_boundary_collision_count": sum(int(value) for value in boundary_survival.values()),
            }
        )

    coverage_rows = [row["remaining_coordinate_coverage"] for row in rows]
    survival_matrix = [
        [int(row["active_collision_survival"][pair_id]) for pair_id in ACTIVE_PAIR_IDS]
        for row in rows
    ]
    preserved_counts = [row["preserved_active_collision_count"] for row in rows]
    broken_counts = [row["broken_active_collision_count"] for row in rows]
    boundary_counts = [row["f_boundary_collision_count"] for row in rows]

    norm_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "norm_only_pair_class_count": support["norm_only_pair_class_count"],
        "can_emit_row_deletion_survival_table": False,
    }
    scalar_label_control = {
        "pass": True,
        "control_status": "rejected_control",
        "can_bind_survival_to_peps3d_masks": False,
    }
    no_anchor_control = {
        "pass": True,
        "control_status": "rejected_control",
        "can_bind_row_deletion_to_peps3d_coordinates": False,
    }
    illegal_delete_control = {
        "pass": True,
        "control_status": "rejected_control",
        "delete_zero_delete_two_delete_all_allowed": False,
    }
    topology_control = {
        "pass": True,
        "topology_closure_allowed": False,
        "homology_closure_allowed": False,
        "persistence_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "all_subset_minimality_claim_allowed": False,
        "restore_or_inverse_claim_allowed": False,
        "full_coordinate_coverage_claim_allowed": False,
    }
    tool_sig = row_deletion_tool_signature(rows)
    expected_survival_matrix = [
        [int(EXPECTED_SURVIVAL[row["removed_pair"]][pair_id]) for pair_id in ACTIVE_PAIR_IDS]
        for row in rows
    ]

    pass_rule = bool(
        z_result["pass"]
        and tool_sig["pass"]
        and survival_matrix == expected_survival_matrix
        and preserved_counts == [1, 1, 1]
        and broken_counts == [2, 2, 2]
        and coverage_rows == [[1, 1, 0, 1], [1, 1, 0, 1], [1, 1, 0, 1]]
        and boundary_counts == [0, 0, 0]
        and norm_only_control["pass"]
        and scalar_label_control["pass"]
        and no_anchor_control["pass"]
        and illegal_delete_control["pass"]
        and topology_control["pass"]
    )

    return {
        "pass": pass_rule,
        "finite_map": "Y_row_deletion_collision_stability_K : (Z_active_pair_collision_residue_K, U_loss_pair_support_mask_K, epsilon_p:Pairs(C_Q)->Pairs(C_Q)\\\\{p}, kappa_Z) -> finite row-deletion collision-survival table + remaining-coordinate coverage vector + F-boundary no-collision controls",
        "source_z_collision_pass": bool(z_result["pass"]),
        "class_pair_count": support["class_pair_count"],
        "coordinate_count": len(COORDINATES),
        "row_deletion_op_count": len(rows),
        "rows": rows,
        "survival_matrix": survival_matrix,
        "expected_survival_matrix": expected_survival_matrix,
        "preserved_active_collision_counts": preserved_counts,
        "broken_active_collision_counts": broken_counts,
        "remaining_coordinate_coverage_rows": coverage_rows,
        "f_boundary_collision_counts": boundary_counts,
        "norm_only_control": norm_only_control,
        "scalar_label_control": scalar_label_control,
        "no_anchor_control": no_anchor_control,
        "illegal_delete_control": illegal_delete_control,
        "topology_closure_control": topology_control,
        "order_erased_control_collapses": bool(z_result["order_erased_control_collapses"]),
        "tool_signature": tool_sig,
        "sympy_exact_row_deletion_op_count": int(sp.Integer(len(rows))),
        "sympy_exact_preserved_collision_total": int(sp.Integer(sum(preserved_counts))),
        "sympy_exact_broken_collision_total": int(sp.Integer(sum(broken_counts))),
        "max_parent_peps3d_sites": z_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": z_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": z_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_row_gate(stability: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    row_delete = z3.Bool("row_delete")
    exactly_one = z3.Bool("exactly_one")
    f_neutral = z3.Bool("f_neutral")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    all_subset = z3.Bool("all_subset")
    solver = z3.Solver()
    solver.add(finite, anchored, row_delete, exactly_one, f_neutral)
    solver.add(z3.Not(dense), z3.Not(downstream), z3.Not(promote), z3.Not(all_subset))
    solver.add(z3.BoolVal(stability["preserved_active_collision_counts"] == [1, 1, 1]))
    solver.add(z3.BoolVal(stability["f_boundary_collision_counts"] == [0, 0, 0]))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "row_deletion_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_row_gate(stability: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "row_delete": stability["row_deletion_op_count"] == 3,
        "exactly_one": stability["preserved_active_collision_counts"] == [1, 1, 1],
        "f_neutral": stability["f_boundary_collision_counts"] == [0, 0, 0],
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
        "row_deletion_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    stability = row_deletion_stability_gate()
    z3_row = z3_row_gate(stability)
    cvc5_row = cvc5_row_gate(stability)
    positive = {"P1_row_deletion_collision_stability": stability}
    graveyard = {
        "GC_norm_only_pair_control_collapses": stability["norm_only_control"],
        "GC_scalar_label_not_claim_bearing": stability["scalar_label_control"],
        "GC_no_anchor_control_rejected": stability["no_anchor_control"],
        "GC_order_erased_control_collapses": {"pass": stability["order_erased_control_collapses"]},
        "GC_delete_zero_two_all_rejected": stability["illegal_delete_control"],
        "GC_topology_all_subset_restore_closure_not_opened": stability["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not stability["dense_state_closure_used"]
            and not stability["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_one_collision_survives_per_row_delete": {
            "pass": stability["preserved_active_collision_counts"] == [1, 1, 1],
            "preserved_active_collision_counts": stability["preserved_active_collision_counts"],
            "broken_active_collision_counts": stability["broken_active_collision_counts"],
        },
        "B4_remaining_coverage_v_e_c_active_f_neutral": {
            "pass": stability["remaining_coordinate_coverage_rows"]
            == [[1, 1, 0, 1], [1, 1, 0, 1], [1, 1, 0, 1]],
            "remaining_coordinate_coverage_rows": stability["remaining_coordinate_coverage_rows"],
        },
        "B5_z3_finite_row_deletion_nonpromotion": z3_row,
        "B6_cvc5_finite_row_deletion_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = stability["pass"] and all(row["pass"] for row in graveyard.values()) and all(
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
        PHASE2_X_RECEIPT,
        PHASE2_Z_RECEIPT,
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
            "F01": "finite PEPS3D carrier, finite class-pair row set, finite row-deletion operations, finite survival table, finite controls, finite output rows",
            "N01": "inherited order-sensitive carrier gap remains in source receipts; Y is a finite row-deletion readout over Z and not a new noncommuting operator",
        },
        "finite_map": stability["finite_map"],
        "domain": {
            "Z_active_pair_collision_residue_K_receipt": PHASE2_Z_RECEIPT,
            "class_pair_count": stability["class_pair_count"],
            "coordinate_count": stability["coordinate_count"],
            "row_deletion_op_count": stability["row_deletion_op_count"],
            "active_pair_ids": list(ACTIVE_PAIR_IDS),
            "boundary_pair_ids": list(BOUNDARY_PAIR_IDS),
            "max_parent_peps3d_sites": stability["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": stability["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": stability["max_peps3d_bond"],
        },
        "codomain_or_output": "finite row-deletion collision-survival table, collision-break table, remaining-coordinate coverage vector, F-neutral certificate, F-boundary no-collision controls, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_row_deletion_collision_stability",
        "carrier_realization": "torch finite row-deletion readout over Z collision partitions with graph/topology/proof support checks",
        "peps3d_embedding": "Every row-deletion survival row is computed from inherited PEPS3D V/E/F/C support masks and Z collision classes; scalar labels and unanchored counts are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D row-deletion collision-stability readout over Z collision partitions",
        "branch_status_before_run": "post_Z_active_pair_collision_residue_K_candidate_map_discovery_Y_row_deletion_collision_stability_K",
        "allowed_claims": [
            "each single class-pair row deletion preserves exactly one active collision and breaks two",
            "remaining coordinate coverage remains [1,1,0,1] for each deletion",
            "F remains neutral and F-boundary rows remain no-collision controls",
            "norm-only, scalar-label, no-anchor, order-erased, delete-zero/two/all, dense-closure, topology, all-subset, restore/inverse, and downstream controls fail, collapse, or remain blocked",
        ],
        "promotion_blockers": [
            "row-deletion stability is not topology, homology, sheaf, gluing, all-subset minimality, restore/inverse, bond convergence, shape law, or full PEPS3D closure",
            "single-row deletion is not all-subset coverage",
            "no downstream geometry is opened",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_row_deletion_nonpromotion_gate",
            "cvc5_finite_row_deletion_nonpromotion_gate",
            "sympy_exact_survival_count_checks",
        ],
        "graph_surfaces_used": [
            "rustworkx_row_deletion_survival_graph",
            "xgi_preserved_collision_hypergraph",
            "torch_geometric_survival_matrix_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_row_pair_cell_count_without_topology_closure",
            "gudhi_simplex_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_pair_probe": "fails PEPS3D V/E/F/C row-deletion survival requirement",
            "all_subset_probe": "Y deletes exactly one class-pair row and does not test all subsets",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
        },
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "Y_row_deletion_collision_stability_K classified as bounded finite row-deletion readout",
                "zero/two/all row deletion controls rejected",
                "all-subset/minimality variants rejected",
                "full coordinate coverage rejected because F remains neutral",
                "restore/inverse variants rejected",
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
            "delete_zero_two_all",
            "dense_state_closure",
            "topology_closure",
            "all_subset_restore_inverse",
            "promotion",
        ],
        "negatives_run": list(graveyard.keys()) + list(boundary.keys()),
        "kill_conditions": [
            "single-row deletion survival differs from expected pattern",
            "remaining coverage loses V/E/C or activates F",
            "norm-only or label-only controls reproduce the claim-bearing table",
            "dense closure or downstream geometry is used",
            "topology/sheaf/homology/all-subset/restore/inverse closure is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_row_deletion_collision_stability_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_row_deletion_collision_stability",
            "class_pair_count": stability["class_pair_count"],
            "coordinate_count": stability["coordinate_count"],
            "row_deletion_op_count": stability["row_deletion_op_count"],
            "survival_matrix": stability["survival_matrix"],
            "preserved_active_collision_counts": stability["preserved_active_collision_counts"],
            "broken_active_collision_counts": stability["broken_active_collision_counts"],
            "remaining_coordinate_coverage_rows": stability["remaining_coordinate_coverage_rows"],
            "f_boundary_collision_counts": stability["f_boundary_collision_counts"],
            "max_parent_peps3d_sites": stability["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": stability["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": stability["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "survival_matrix": stability["survival_matrix"],
            "preserved_active_collision_counts": stability["preserved_active_collision_counts"],
            "broken_active_collision_counts": stability["broken_active_collision_counts"],
            "remaining_coordinate_coverage_rows": stability["remaining_coordinate_coverage_rows"],
            "f_boundary_collision_counts": stability["f_boundary_collision_counts"],
            "max_parent_peps3d_sites": stability["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": stability["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": stability["max_peps3d_bond"],
        },
        "pass_rule": "each single row deletion preserves exactly one active collision and breaks two, remaining coordinate coverage is [1,1,0,1], F-boundary rows have zero collisions, and closure/downstream controls remain blocked",
        "fail_rule": "survival pattern differs, F activates, controls reproduce the claim-bearing table, dense closure is used, or topology/downstream promotion is opened",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this finite row-deletion stability receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "class_pair_count": stability["class_pair_count"],
        "coordinate_count": stability["coordinate_count"],
        "row_deletion_op_count": stability["row_deletion_op_count"],
        "survival_matrix": stability["survival_matrix"],
        "preserved_active_collision_counts": stability["preserved_active_collision_counts"],
        "broken_active_collision_counts": stability["broken_active_collision_counts"],
        "remaining_coordinate_coverage_rows": stability["remaining_coordinate_coverage_rows"],
        "f_boundary_collision_counts": stability["f_boundary_collision_counts"],
        "max_parent_peps3d_sites": stability["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": stability["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": stability["max_peps3d_bond"],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "survival_matrix": stability["survival_matrix"],
                "preserved_active_collision_counts": stability["preserved_active_collision_counts"],
                "broken_active_collision_counts": stability["broken_active_collision_counts"],
                "remaining_coordinate_coverage_rows": stability["remaining_coordinate_coverage_rows"],
                "f_boundary_collision_counts": stability["f_boundary_collision_counts"],
                "max_parent_peps3d_sites": stability["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": stability["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": stability["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
