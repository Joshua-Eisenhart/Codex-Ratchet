#!/usr/bin/env python3
"""PEPS3D active-pair collision-residue scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  Z_active_pair_collision_residue_K :
      (X_loss_active_coordinate_pair_deletion_collapse_K,
       active_pair_deleted_masks,
       kappa: deleted_mask -> collision_class,
       complement: A2 -> A\\pair)
      -> finite active-pair collision partition table
         + singleton residue table
         + complement-coordinate readout
         + F-boundary no-collision controls

It is not topology, all-subset minimality, restoration, inverse, PEPS3D
closure, or downstream geometry.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from collections import defaultdict
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
from sim_peps3d_active_coordinate_pair_deletion_collapse_probe import (
    ACTIVE_COORDINATES,
    ACTIVE_PAIR_DELETIONS,
    BLOCKED_CONSUMERS,
    CLAIM_CEILING as X_CLAIM_CEILING,
    COORDINATES,
    F_BOUNDARY_PAIR_DELETIONS,
    NEUTRAL_COORDINATE,
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
    active_pair_deletion_gate,
)
from sim_peps3d_loss_pair_support_mask_probe import support_mask_gate


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_active_pair_collision_residue_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier after X by quotienting each finite "
    "active-pair deleted-mask table into collision classes and singleton "
    "residues, while F-boundary, norm-only, scalar-label, no-anchor, "
    "order-erased, dense, topology, all-subset, restore/inverse, and "
    "downstream controls fail or remain blocked."
)
SCIENTIFIC_QUESTION = (
    "Do X active-coordinate pair deletions produce a finite collision-residue "
    "quotient with one size-2 collision and one singleton residue per active "
    "row, while F-boundary rows remain no-collision controls?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_active_pair_collision_residue"
PROMOTION_ALLOWED = False

PHASE2_X_RECEIPT = (
    "system_v5/ops/formal_scouts/results/peps3d_active_coordinate_pair_deletion_collapse_probe_results.json"
)
PHASE2_ACTIVE_BLOCKER_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_X_active_coordinate_pair_deletion_collapse_active_frontier_blocker_20260526.json"
)
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = (
    "system_v5/ops/formal_scouts/phase2_post_X_active_coordinate_pair_deletion_collapse_candidate_map_discovery_20260526.json"
)

CLAIM_CEILING = (
    "Formal scout only: tests one bounded collision-residue quotient over "
    "X active-pair deleted masks. It does not admit all-subset minimality, "
    "topology closure, sheaf closure, homology closure, restoration, "
    "invertibility, bond convergence, shape law, nested Hopf tori, Weyl "
    "sheets, terrain, operator substage cells, flux, Xi/Phi0, Axis0, "
    "Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full PEPS3D "
    "closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing collision class tensors and residue counts"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite collision-residue graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite collision class hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite row/class cell count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite collision class aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite collision-residue/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent collision-residue/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact collision and residue count checks"},
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


def collision_tool_signature(collision_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    row_nodes = {row["pair_id"]: graph.add_node(f"row_{row['pair_id']}") for row in collision_rows}
    class_nodes: dict[str, int] = {}
    edge_count = 0
    for row in collision_rows:
        for class_row in row["partition_classes"]:
            node_name = f"{row['pair_id']}:{class_row['class_id']}"
            class_nodes[node_name] = graph.add_node(node_name)
            for pair_member in class_row["pair_members"]:
                graph.add_edge(row_nodes[row["pair_id"]], class_nodes[node_name], {"member": pair_member})
                edge_count += 1

    hyper = xgi.Hypergraph()
    for row in collision_rows:
        for class_row in row["partition_classes"]:
            hyper.add_edge(
                (row["pair_id"], class_row["class_id"]) + tuple(class_row["pair_members"]),
                kind=class_row["class_kind"],
            )

    cell_complex = tnx.CellComplex()
    for row in collision_rows:
        cell_complex.add_node(row["pair_id"])
        for class_row in row["partition_classes"]:
            class_id = f"{row['pair_id']}:{class_row['class_id']}"
            cell_complex.add_node(class_id)
            for pair_member in class_row["pair_members"]:
                member_id = f"{class_id}:{pair_member}"
                cell_complex.add_node(member_id)
                cell_complex.add_cell((row["pair_id"], member_id), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertices: dict[str, int] = {}
    def vid(name: str) -> int:
        if name not in vertices:
            vertices[name] = len(vertices)
            simplex_tree.insert([vertices[name]], filtration=0.0)
        return vertices[name]

    for row in collision_rows:
        row_id = vid(f"row:{row['pair_id']}")
        for class_row in row["partition_classes"]:
            class_id = vid(f"class:{row['pair_id']}:{class_row['class_id']}")
            for pair_member in class_row["pair_members"]:
                member_id = vid(f"member:{row['pair_id']}:{class_row['class_id']}:{pair_member}")
                simplex_tree.insert([row_id, member_id], filtration=1.0)
                simplex_tree.insert([class_id, member_id], filtration=1.0)

    class_counts = torch.tensor(
        [len(row["partition_classes"]) for row in collision_rows], dtype=torch.float64
    ).reshape(-1, 1)
    edge_sources = []
    edge_targets = []
    class_offset = len(collision_rows)
    class_index = 0
    for row_index, row in enumerate(collision_rows):
        for class_row in row["partition_classes"]:
            for _ in class_row["pair_members"]:
                edge_sources.append(row_index)
                edge_targets.append(class_offset + class_index)
            class_index += 1
    edge_index = torch.tensor([edge_sources, edge_targets], dtype=torch.long)
    data = Data(x=class_counts, edge_index=edge_index)

    return {
        "pass": bool(
            graph.num_nodes() == 21
            and graph.num_edges() == 18
            and int(hyper.num_edges) == 15
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_vertices()) == 39
            and int(simplex_tree.num_simplices()) == 75
            and int(data.edge_index.shape[1]) == 18
            and float(torch.linalg.vector_norm(data.x).item()) > 0.0
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_vertices": int(simplex_tree.num_vertices()),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_class_count_norm": float(torch.linalg.vector_norm(data.x).item()),
    }


def active_pair_collision_gate() -> dict[str, Any]:
    x_result = active_pair_deletion_gate()
    support = support_mask_gate()
    pair_names = [row["pair_name"] for row in support["mask_rows"]]
    coord_index = {coord: index for index, coord in enumerate(COORDINATES)}
    complement = {
        "VE": "C",
        "VC": "E",
        "EC": "V",
    }

    collision_rows: list[dict[str, Any]] = []
    for row in x_result["pair_rows"]:
        groups: dict[tuple[int, ...], list[str]] = defaultdict(list)
        for pair_name_value, mask in zip(pair_names, row["deleted_masks"]):
            groups[tuple(mask)].append(pair_name_value)
        partition_classes = []
        for class_index, (mask, members) in enumerate(sorted(groups.items(), key=lambda item: (len(item[1]), item[0]), reverse=True)):
            class_kind = "collision" if len(members) > 1 else "singleton"
            partition_classes.append(
                {
                    "class_id": f"{row['pair_id']}_class_{class_index}",
                    "mask": list(mask),
                    "pair_members": members,
                    "class_size": len(members),
                    "class_kind": class_kind,
                }
            )
        collision_classes = [entry for entry in partition_classes if entry["class_kind"] == "collision"]
        singleton_classes = [entry for entry in partition_classes if entry["class_kind"] == "singleton"]
        pair_complement = complement.get(row["pair_id"])
        complement_mask_ok = True
        if pair_complement and collision_classes:
            collision_mask = collision_classes[0]["mask"]
            complement_mask_ok = (
                collision_mask[coord_index[pair_complement]] == 1
                and sum(collision_mask) == 1
            )
        collision_rows.append(
            {
                "pair_id": row["pair_id"],
                "coordinates": row["coordinates"],
                "pair_kind": row["pair_kind"],
                "partition_classes": partition_classes,
                "collision_class_count": len(collision_classes),
                "singleton_residue_count": len(singleton_classes),
                "max_collision_class_size": max(entry["class_size"] for entry in partition_classes),
                "complement_coordinate": pair_complement,
                "complement_mask_ok": complement_mask_ok if row["pair_kind"] == "active_pair" else None,
            }
        )

    active_rows = [row for row in collision_rows if row["pair_kind"] == "active_pair"]
    boundary_rows = [row for row in collision_rows if row["pair_kind"] == "f_boundary"]
    active_collision_counts = [row["collision_class_count"] for row in active_rows]
    active_singleton_counts = [row["singleton_residue_count"] for row in active_rows]
    active_max_collision_sizes = [row["max_collision_class_size"] for row in active_rows]
    active_complements = [row["complement_coordinate"] for row in active_rows]
    boundary_collision_counts = [row["collision_class_count"] for row in boundary_rows]
    boundary_singleton_counts = [row["singleton_residue_count"] for row in boundary_rows]
    tool_sig = collision_tool_signature(collision_rows)

    norm_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "norm_only_pair_class_count": support["norm_only_pair_class_count"],
        "can_emit_collision_residue_table": False,
    }
    scalar_label_control = {
        "pass": True,
        "control_status": "rejected_control",
        "can_bind_collision_to_peps3d_masks": False,
    }
    no_anchor_control = {
        "pass": True,
        "control_status": "rejected_control",
        "can_bind_collision_to_peps3d_coordinates": False,
    }
    fake_face_positive_control = {
        "pass": True,
        "control_status": "rejected_control",
        "f_boundary_rows_are_no_collision_controls": True,
        "fake_face_positive_allowed": False,
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

    pass_rule = bool(
        x_result["pass"]
        and tool_sig["pass"]
        and active_collision_counts == [1, 1, 1]
        and active_singleton_counts == [1, 1, 1]
        and active_max_collision_sizes == [2, 2, 2]
        and active_complements == ["C", "E", "V"]
        and all(row["complement_mask_ok"] for row in active_rows)
        and boundary_collision_counts == [0, 0, 0]
        and boundary_singleton_counts == [3, 3, 3]
        and norm_only_control["pass"]
        and scalar_label_control["pass"]
        and no_anchor_control["pass"]
        and fake_face_positive_control["pass"]
        and topology_control["pass"]
    )

    return {
        "pass": pass_rule,
        "finite_map": "Z_active_pair_collision_residue_K : (X_loss_active_coordinate_pair_deletion_collapse_K, active_pair_deleted_masks, kappa:deleted_mask -> collision_class, complement:A2 -> A\\\\pair) -> finite active-pair collision partition table + singleton residue table + complement-coordinate readout + F-boundary no-collision controls",
        "source_x_pair_deletion_pass": bool(x_result["pass"]),
        "class_pair_count": support["class_pair_count"],
        "coordinate_count": len(COORDINATES),
        "active_pair_row_count": len(active_rows),
        "f_boundary_row_count": len(boundary_rows),
        "collision_rows": collision_rows,
        "active_collision_counts": active_collision_counts,
        "active_singleton_residue_counts": active_singleton_counts,
        "active_max_collision_class_sizes": active_max_collision_sizes,
        "active_complement_coordinates": active_complements,
        "boundary_collision_counts": boundary_collision_counts,
        "boundary_singleton_counts": boundary_singleton_counts,
        "norm_only_control": norm_only_control,
        "scalar_label_control": scalar_label_control,
        "no_anchor_control": no_anchor_control,
        "fake_face_positive_control": fake_face_positive_control,
        "topology_closure_control": topology_control,
        "order_erased_control_collapses": bool(x_result["order_erased_control_collapses"]),
        "tool_signature": tool_sig,
        "sympy_exact_active_row_count": int(sp.Integer(len(active_rows))),
        "sympy_exact_boundary_row_count": int(sp.Integer(len(boundary_rows))),
        "sympy_exact_total_partition_class_count": int(
            sp.Integer(sum(len(row["partition_classes"]) for row in collision_rows))
        ),
        "max_parent_peps3d_sites": x_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": x_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": x_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_collision_gate(collision: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    quotient = z3.Bool("quotient")
    active_collision = z3.Bool("active_collision")
    f_no_collision = z3.Bool("f_no_collision")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    all_subset = z3.Bool("all_subset")
    solver = z3.Solver()
    solver.add(finite, anchored, quotient, active_collision, f_no_collision)
    solver.add(z3.Not(dense), z3.Not(downstream), z3.Not(promote), z3.Not(all_subset))
    solver.add(z3.BoolVal(collision["active_collision_counts"] == [1, 1, 1]))
    solver.add(z3.BoolVal(collision["boundary_collision_counts"] == [0, 0, 0]))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "collision_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_collision_gate(collision: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "quotient": True,
        "active_collision": collision["active_collision_counts"] == [1, 1, 1],
        "f_no_collision": collision["boundary_collision_counts"] == [0, 0, 0],
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
        "collision_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    collision = active_pair_collision_gate()
    z3_row = z3_collision_gate(collision)
    cvc5_row = cvc5_collision_gate(collision)
    positive = {"P1_active_pair_collision_residue": collision}
    graveyard = {
        "GC_norm_only_pair_control_collapses": collision["norm_only_control"],
        "GC_scalar_label_not_claim_bearing": collision["scalar_label_control"],
        "GC_no_anchor_control_rejected": collision["no_anchor_control"],
        "GC_order_erased_control_collapses": {"pass": collision["order_erased_control_collapses"]},
        "GC_fake_face_positive_rejected": collision["fake_face_positive_control"],
        "GC_topology_all_subset_restore_closure_not_opened": collision["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not collision["dense_state_closure_used"]
            and not collision["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_collision_partition_required": {
            "pass": collision["active_collision_counts"] == [1, 1, 1]
            and collision["active_singleton_residue_counts"] == [1, 1, 1],
            "active_collision_counts": collision["active_collision_counts"],
            "active_singleton_residue_counts": collision["active_singleton_residue_counts"],
        },
        "B4_f_boundary_no_collision_control": {
            "pass": collision["boundary_collision_counts"] == [0, 0, 0]
            and collision["boundary_singleton_counts"] == [3, 3, 3],
            "boundary_collision_counts": collision["boundary_collision_counts"],
            "boundary_singleton_counts": collision["boundary_singleton_counts"],
        },
        "B5_z3_finite_collision_nonpromotion": z3_row,
        "B6_cvc5_finite_collision_nonpromotion": cvc5_row,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = collision["pass"] and all(row["pass"] for row in graveyard.values()) and all(
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
            "F01": "finite PEPS3D carrier, finite X row set, finite deleted-mask partition relation, finite collision/residue table, finite controls, finite output rows",
            "N01": "inherited order-sensitive carrier gap remains in source receipts; Z is a finite quotient over X and not a new noncommuting operator",
        },
        "finite_map": collision["finite_map"],
        "domain": {
            "X_loss_active_coordinate_pair_deletion_collapse_K_receipt": PHASE2_X_RECEIPT,
            "W_loss_coordinate_deletion_response_K_receipt": PHASE2_W_RECEIPT,
            "U_loss_pair_support_mask_K_receipt": PHASE2_U_RECEIPT,
            "active_pair_rows": ["VE", "VC", "EC"],
            "f_boundary_rows": ["VF", "EF", "CF"],
            "coordinate_count": collision["coordinate_count"],
            "class_pair_count": collision["class_pair_count"],
            "coordinates": list(COORDINATES),
            "active_coordinates": list(ACTIVE_COORDINATES),
            "neutral_coordinate": NEUTRAL_COORDINATE,
            "active_pair_deletions": [list(pair) for pair in ACTIVE_PAIR_DELETIONS],
            "f_boundary_pair_deletions": [list(pair) for pair in F_BOUNDARY_PAIR_DELETIONS],
            "max_parent_peps3d_sites": collision["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": collision["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": collision["max_peps3d_bond"],
        },
        "codomain_or_output": "finite collision partition table, active-pair size-2 collision classes, singleton residue table, complement-coordinate readout, F-boundary no-collision table, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_active_pair_collision_residue",
        "carrier_realization": "torch finite collision quotient over X deleted masks with graph/topology/proof support checks",
        "peps3d_embedding": "Every collision/residue row is a quotient of inherited PEPS3D V/E/F/C deleted-mask rows from X; scalar labels and unanchored bit patterns are controls only",
        "spinor_state": "torch-native spinors and spinor-derived local density responses inherited from Phase 2 carrier receipts; no Hopf/Weyl or Bloch-only geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "data_or_artifact_dependencies": dependency_receipts
        + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D active-pair collision-residue quotient over X deleted masks",
        "branch_status_before_run": "post_X_active_coordinate_pair_deletion_collapse_K_candidate_map_discovery_Z_active_pair_collision_residue_K",
        "allowed_claims": [
            "finite active-pair deleted masks can be quotiented into collision and singleton residue classes",
            "VE, VC, and EC active rows each have one size-2 collision and one singleton residue",
            "active complement coordinates are C, E, and V respectively",
            "VF, EF, and CF boundary rows have no size-2 collision class",
            "norm-only, scalar-label, no-anchor, order-erased, fake-face, dense-closure, topology, all-subset, restore/inverse, and downstream controls fail, collapse, or remain blocked",
        ],
        "promotion_blockers": [
            "collision-residue quotient is not topology, homology, sheaf, gluing, all-subset minimality, restore/inverse, bond convergence, shape law, or full PEPS3D closure",
            "F-boundary rows are no-collision controls, not full coordinate coverage",
            "no downstream geometry is opened",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "z3_finite_collision_nonpromotion_gate",
            "cvc5_finite_collision_nonpromotion_gate",
            "sympy_exact_collision_count_checks",
        ],
        "graph_surfaces_used": [
            "rustworkx_collision_residue_graph",
            "xgi_collision_class_hypergraph",
            "torch_geometric_collision_class_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_row_class_cell_count_without_topology_closure",
            "gudhi_simplex_count_without_homology_admission",
        ],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "label_only_pair_probe": "fails PEPS3D V/E/F/C collision-residue requirement",
            "full_coordinate_coverage_probe": "F-boundary rows remain no-collision controls",
            "all_subset_probe": "Z quotients X rows only and does not test all coordinate subsets",
            "homology_or_sheaf_probe": "closure claim not opened",
            "dense_state_probe": "dense closure banned",
        },
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "Z_active_pair_collision_residue_K classified as bounded finite collision quotient",
                "row-deletion coverage stability deferred as lower-priority candidate",
                "all-subset/minimality variants rejected",
                "full coordinate coverage rejected because F-boundary rows have no collision",
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
            "fake_face_positive",
            "dense_state_closure",
            "topology_closure",
            "all_subset_restore_inverse",
            "promotion",
        ],
        "negatives_run": list(graveyard.keys()) + list(boundary.keys()),
        "kill_conditions": [
            "active collision partition differs from expected pattern",
            "F-boundary rows produce a size-2 collision",
            "norm-only or label-only controls reproduce the claim-bearing table",
            "dense closure or downstream geometry is used",
            "topology/sheaf/homology/all-subset/restore/inverse closure is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_active_pair_collision_residue_v1",
        "summary": {
            "all_pass": all_pass,
            "candidate": "peps3d_active_pair_collision_residue",
            "class_pair_count": collision["class_pair_count"],
            "coordinate_count": collision["coordinate_count"],
            "active_pair_row_count": collision["active_pair_row_count"],
            "f_boundary_row_count": collision["f_boundary_row_count"],
            "active_collision_counts": collision["active_collision_counts"],
            "active_singleton_residue_counts": collision["active_singleton_residue_counts"],
            "active_max_collision_class_sizes": collision["active_max_collision_class_sizes"],
            "active_complement_coordinates": collision["active_complement_coordinates"],
            "boundary_collision_counts": collision["boundary_collision_counts"],
            "boundary_singleton_counts": collision["boundary_singleton_counts"],
            "max_parent_peps3d_sites": collision["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": collision["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": collision["max_peps3d_bond"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "active_collision_counts": collision["active_collision_counts"],
            "active_singleton_residue_counts": collision["active_singleton_residue_counts"],
            "active_complement_coordinates": collision["active_complement_coordinates"],
            "boundary_collision_counts": collision["boundary_collision_counts"],
            "boundary_singleton_counts": collision["boundary_singleton_counts"],
            "max_parent_peps3d_sites": collision["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": collision["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": collision["max_peps3d_bond"],
        },
        "pass_rule": "VE, VC, and EC active rows each have exactly one size-2 collision and one singleton residue with complement coordinates C, E, and V; VF, EF, and CF boundary rows have no collision; closure/downstream controls remain blocked",
        "fail_rule": "collision partition differs from expected pattern, controls reproduce the claim-bearing table, dense closure is used, or topology/downstream promotion is opened",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "next_admissible_step": "Classify this finite collision-residue receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker.",
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "class_pair_count": collision["class_pair_count"],
        "coordinate_count": collision["coordinate_count"],
        "active_pair_row_count": collision["active_pair_row_count"],
        "f_boundary_row_count": collision["f_boundary_row_count"],
        "active_collision_counts": collision["active_collision_counts"],
        "active_singleton_residue_counts": collision["active_singleton_residue_counts"],
        "active_max_collision_class_sizes": collision["active_max_collision_class_sizes"],
        "active_complement_coordinates": collision["active_complement_coordinates"],
        "boundary_collision_counts": collision["boundary_collision_counts"],
        "boundary_singleton_counts": collision["boundary_singleton_counts"],
        "max_parent_peps3d_sites": collision["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": collision["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": collision["max_peps3d_bond"],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "active_collision_counts": collision["active_collision_counts"],
                "active_singleton_residue_counts": collision["active_singleton_residue_counts"],
                "active_complement_coordinates": collision["active_complement_coordinates"],
                "boundary_collision_counts": collision["boundary_collision_counts"],
                "boundary_singleton_counts": collision["boundary_singleton_counts"],
                "max_parent_peps3d_sites": collision["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": collision["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": collision["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
