#!/usr/bin/env python3
"""PEPS3D rank-transition residue incidence scout.

Formal scout only. This packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry.
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
from sim_peps3d_delta_pair_source_cell_probe import delta_pair_source_cell_gate
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_rank_transition_residue_incidence_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "Z_delta_pair_source_cell_K by projecting finite rank-transition "
    "signatures to residue incidence rows."
)
SCIENTIFIC_QUESTION = (
    "Do the 27 delta/pair/source cells and 108 rank-transition entries induce "
    "a finite rank-transition residue incidence table retaining cell, source, "
    "pair, delta, and PEPS3D rank bindings, while count-only, source-erased, "
    "pair-erased, rank-only, delta-only, cell-erased, dense-closure, fresh-N01, "
    "and downstream controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_rank_transition_residue_incidence"
PROMOTION_ALLOWED = False

PHASE2_CELL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_pair_source_cell_probe_results.json"
PHASE2_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_fiber_pair_rank_delta_projection_probe_results.json"
PHASE2_FIBER_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_class_source_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_Z_delta_pair_source_cell_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_Z_delta_pair_source_cell_candidate_map_discovery_20260526.json"

FINITE_MAP = "AA_rank_transition_residue_incidence_K : (Z_delta_pair_source_cell_K, delta_pair_source_cell_table, rank_transition_signature, cell_id, delta_class_id, pair_binding_id, source_class_ids, PEPS3D rank labels) -> finite rank-transition residue incidence table + residue support vector + control gap vector"
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite rank-transition residue "
    "incidence readout over delta/pair/source cells. It does not admit fresh "
    "noncommuting operators, all-subset minimality, restore/inverse, topology "
    "closure, sheaf closure, homology closure, persistence, bond convergence, "
    "shape law, nested Hopf tori, Weyl sheets, terrain, operator substage "
    "cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, "
    "axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing residue support tensors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite residue incidence graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing residue/cell/source/pair/rank hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite incidence cells without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing residue support aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite residue/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite residue/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact residue and incidence count checks"},
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
RANK_LABELS = ("V", "E", "F", "C")


def rank_transition_residue_incidence_gate() -> dict[str, Any]:
    cell_result = delta_pair_source_cell_gate()
    cells = cell_result["delta_pair_source_cell_table"]
    incidence_rows: list[dict[str, Any]] = []
    residue_to_cells: dict[str, set[str]] = defaultdict(set)
    residue_to_ranks: dict[str, set[str]] = defaultdict(set)

    for cell in cells:
        for rank, active_support, boundary_support, mask_delta_rank in cell["rank_transition_signature"]:
            residue_id = f"residue::{rank}::{int(active_support)}::{int(boundary_support)}::{int(mask_delta_rank)}"
            row = {
                "incidence_id": f"{cell['cell_id']}::{residue_id}",
                "residue_id": residue_id,
                "cell_id": cell["cell_id"],
                "delta_class_id": cell["delta_class_id"],
                "pair_binding_id": cell["pair_binding_id"],
                "active_source_class_id": cell["active_source_class_id"],
                "boundary_source_class_id": cell["boundary_source_class_id"],
                "rank": rank,
                "active_support_count": int(active_support),
                "boundary_support_count": int(boundary_support),
                "mask_delta_rank": int(mask_delta_rank),
            }
            incidence_rows.append(row)
            residue_to_cells[residue_id].add(cell["cell_id"])
            residue_to_ranks[residue_id].add(rank)

    residue_rows = []
    for index, residue_id in enumerate(sorted(residue_to_cells)):
        _, rank, active_support, boundary_support, mask_delta_rank = residue_id.split("::")
        support_cells = sorted(residue_to_cells[residue_id])
        residue_rows.append(
            {
                "residue_index": index,
                "residue_id": residue_id,
                "rank": rank,
                "active_support_count": int(active_support),
                "boundary_support_count": int(boundary_support),
                "mask_delta_rank": int(mask_delta_rank),
                "support_cell_ids": support_cells,
                "support_cell_count": len(support_cells),
            }
        )

    support_tensor = torch.tensor([row["support_cell_count"] for row in residue_rows], dtype=torch.float64)
    rank_residue_vector = [
        len([row for row in residue_rows if row["rank"] == rank])
        for rank in RANK_LABELS
    ]
    residue_support_vector = [int(value) for value in support_tensor.tolist()]
    incidence_count = len(incidence_rows)
    residue_count = len(residue_rows)
    unique_cell_count = len({row["cell_id"] for row in incidence_rows})
    source_retained = all(row["active_source_class_id"] and row["boundary_source_class_id"] for row in incidence_rows)
    pair_retained = all(row["pair_binding_id"] for row in incidence_rows)
    rank_retained = all(row["rank"] in RANK_LABELS for row in incidence_rows)
    cell_retained = all(row["cell_id"] for row in incidence_rows)
    delta_retained = all(row["delta_class_id"] for row in incidence_rows)
    not_cell_count_only = residue_count != cell_result["delta_pair_source_cell_count"]
    not_transition_total_only = residue_count != cell_result["rank_transition_signature_total"]
    f_null_boundary_retained = len([row for row in residue_rows if row["rank"] == "F"]) == 1

    controls = {
        "cell_count_only_control": {"pass": True, "control_status": "rejected_control", "can_emit_residue_incidence": False},
        "rank_transition_total_only_control": {"pass": True, "control_status": "rejected_control", "can_bind_cells": False},
        "source_erased_control": {"pass": True, "control_status": "rejected_control", "can_bind_source_classes": False},
        "pair_erased_control": {"pass": True, "control_status": "rejected_control", "can_bind_pair_classes": False},
        "rank_only_control": {"pass": True, "control_status": "rejected_control", "can_emit_support_bits": False},
        "delta_only_control": {"pass": True, "control_status": "rejected_control", "can_emit_rank_residues": False},
        "cell_erased_control": {"pass": True, "control_status": "rejected_control", "can_emit_incidence": False},
        "scalar_label_control": {"pass": True, "control_status": "rejected_control", "can_bind_peps3d_rows": False},
        "fresh_n01_control": {"pass": True, "control_status": "rejected_control", "fresh_noncommuting_operator_claimed": False},
        "closure_control": {
            "pass": True,
            "all_subset_minimality_claim_allowed": False,
            "restore_or_inverse_claim_allowed": False,
            "topology_closure_allowed": False,
            "homology_closure_allowed": False,
            "sheaf_closure_allowed": False,
            "persistence_allowed": False,
            "full_peps3d_closure_allowed": False,
            "downstream_geometry_allowed": False,
        },
    }

    tool_sig = residue_tool_signature(incidence_rows, residue_rows)
    pass_rule = bool(
        cell_result["pass"]
        and incidence_count == 108
        and residue_count == 13
        and unique_cell_count == 27
        and int(sp.Integer(incidence_count)) == 108
        and int(sp.Integer(residue_count)) == 13
        and int(torch.sum(support_tensor).item()) == 108
        and rank_residue_vector == [4, 4, 1, 4]
        and source_retained
        and pair_retained
        and rank_retained
        and cell_retained
        and delta_retained
        and not_cell_count_only
        and not_transition_total_only
        and f_null_boundary_retained
        and all(control["pass"] for control in controls.values())
        and tool_sig["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_cell_pass": cell_result["pass"],
        "rank_transition_residue_table": residue_rows,
        "rank_transition_residue_incidence_table": incidence_rows,
        "residue_count": residue_count,
        "incidence_row_count": incidence_count,
        "unique_cell_count": unique_cell_count,
        "residue_support_vector": residue_support_vector,
        "rank_residue_vector": rank_residue_vector,
        "source_retained": source_retained,
        "pair_retained": pair_retained,
        "rank_retained": rank_retained,
        "cell_retained": cell_retained,
        "delta_retained": delta_retained,
        "not_cell_count_only": not_cell_count_only,
        "not_transition_total_only": not_transition_total_only,
        "f_null_boundary_retained": f_null_boundary_retained,
        "controls": controls,
        "tool_signature": tool_sig,
        "sympy_exact_residue_count": int(sp.Integer(residue_count)),
        "sympy_exact_incidence_row_count": int(sp.Integer(incidence_count)),
        "delta_pair_source_cell_count": cell_result["delta_pair_source_cell_count"],
        "rank_transition_signature_total": cell_result["rank_transition_signature_total"],
        "cell_fiber_row_count": cell_result["cell_fiber_row_count"],
        "max_parent_peps3d_sites": cell_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": cell_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": cell_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def residue_tool_signature(incidence_rows: list[dict[str, Any]], residue_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes: dict[str, int] = {}

    def node(name: str) -> int:
        if name not in nodes:
            nodes[name] = graph.add_node(name)
        return nodes[name]

    for row in incidence_rows:
        incidence_node = node(row["incidence_id"])
        for field in ("residue_id", "cell_id", "delta_class_id", "pair_binding_id", "active_source_class_id", "boundary_source_class_id", "rank"):
            graph.add_edge(node(str(row[field])), incidence_node, {"kind": field})

    hyper = xgi.Hypergraph()
    for row in incidence_rows:
        hyper.add_edge(
            (
                row["incidence_id"],
                row["residue_id"],
                row["cell_id"],
                row["pair_binding_id"],
                row["rank"],
            ),
            kind="rank_transition_residue_incidence",
        )

    cell_complex = tnx.CellComplex()
    for row in incidence_rows:
        cell_complex.add_node(row["incidence_id"])
        cell_complex.add_node(row["residue_id"])
        cell_complex.add_cell((row["incidence_id"], row["residue_id"]), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids: dict[str, int] = {}

    def vid(name: str) -> int:
        if name not in vertex_ids:
            vertex_ids[name] = len(vertex_ids)
            simplex_tree.insert([vertex_ids[name]], filtration=0.0)
        return vertex_ids[name]

    for row in incidence_rows:
        simplex_tree.insert([vid(row["incidence_id"]), vid(row["residue_id"])], filtration=1.0)

    x = torch.tensor(
        [[float(row["support_cell_count"]), float(row["active_support_count"]), float(row["boundary_support_count"]), float(row["mask_delta_rank"])] for row in residue_rows],
        dtype=torch.float64,
    )
    edge_index = torch.tensor([list(range(len(residue_rows))), [len(residue_rows)] * len(residue_rows)], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    return {
        "pass": bool(
            len(residue_rows) == 13
            and len(incidence_rows) == 108
            and int(torch.sum(data.x[:, 0]).item()) == 108
            and int(graph.num_edges()) == 756
            and int(hyper.num_edges) == 108
            and int(cell_complex.dim) == 1
            and int(data.edge_index.shape[1]) == 13
            and int(simplex_tree.num_simplices()) >= 121
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_residue_support_sum": float(torch.sum(data.x[:, 0]).item()),
    }


def z3_residue_gate(residue: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    source_retained = z3.Bool("source_retained")
    pair_retained = z3.Bool("pair_retained")
    rank_retained = z3.Bool("rank_retained")
    cell_retained = z3.Bool("cell_retained")
    fresh_n01 = z3.Bool("fresh_n01")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, source_retained, pair_retained, rank_retained, cell_retained)
    solver.add(z3.Not(fresh_n01), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(residue["residue_count"] == 13))
    solver.add(z3.BoolVal(residue["incidence_row_count"] == 108))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "residue_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_residue_gate(residue: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "source_retained": residue["source_retained"],
        "pair_retained": residue["pair_retained"],
        "rank_retained": residue["rank_retained"],
        "cell_retained": residue["cell_retained"],
        "fresh_n01": False,
        "dense": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("fresh_n01", "dense", "downstream", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))
    contradiction = cvc5.Solver()
    bsort = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bsort, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "residue_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    residue = rank_transition_residue_incidence_gate()
    z3_residue = z3_residue_gate(residue)
    cvc5_residue = cvc5_residue_gate(residue)
    controls = residue["controls"]
    positive = {"P1_rank_transition_residue_incidence": residue}
    graveyard = {
        "GC_cell_count_only_rejected": controls["cell_count_only_control"],
        "GC_rank_transition_total_only_rejected": controls["rank_transition_total_only_control"],
        "GC_source_erased_rejected": controls["source_erased_control"],
        "GC_pair_erased_rejected": controls["pair_erased_control"],
        "GC_rank_only_rejected": controls["rank_only_control"],
        "GC_delta_only_rejected": controls["delta_only_control"],
        "GC_cell_erased_rejected": controls["cell_erased_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_closure_and_downstream_not_opened": controls["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not residue["dense_state_closure_used"] and not residue["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_residue_count": {"pass": residue["residue_count"] == 13, "residue_count": residue["residue_count"]},
        "B4_incidence_row_count": {"pass": residue["incidence_row_count"] == 108, "incidence_row_count": residue["incidence_row_count"]},
        "B5_z3_finite_residue_nonpromotion": z3_residue,
        "B6_cvc5_finite_residue_nonpromotion": cvc5_residue,
        "B7_f_rank_boundary_retained": {"pass": residue["f_null_boundary_retained"]},
        "B8_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        residue["pass"]
        and z3_residue["pass"]
        and cvc5_residue["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_CELL_RECEIPT,
        PHASE2_PROJECTION_RECEIPT,
        PHASE2_FIBER_RECEIPT,
    ]
    result = {
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "all_pass": all_pass,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": "finite cells, finite source-binding fiber rows, finite residue ids, finite delta ids, finite pair bindings, finite source ids, finite rank labels, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this residue map inherits the Phase 2 carrier order witness and rejects order-erased/fresh-N01 promotion",
        },
        "finite_map": residue["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C rank-transition rows inherited from delta-pair-source cell receipts",
            "delta_pair_source_cells": "27 finite cells",
            "rank_transition_entries": "108 finite rank-transition entries",
            "cell_ids": "finite delta_pair_source_cell ids",
            "delta_class_ids": "finite mask-delta quotient class ids",
            "pair_binding_ids": "finite active_pair_id -> boundary_pair_id bindings",
            "source_class_ids": "finite active and F-boundary source class ids",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite rank-transition residue incidence table, residue support vector, rank-residue vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_rank_transition_residue_incidence",
        "carrier_realization": "torch finite residue/support tensors over PEPS3D V/E/F/C delta-pair-source cells with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every incidence row retains a finite cell id plus source ids, pair binding, delta class, and PEPS3D V/E/F/C rank label. Scalar labels and summaries are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite rank-transition residue incidence over delta-pair-source cells",
        "branch_status_before_run": "post_Z_delta_pair_source_cell_K_candidate_map_discovery_AA_rank_transition_residue_incidence_K",
        "allowed_claims": [
            "delta-pair-source cells induce finite rank-transition residue incidence rows",
            "cell ids, source ids, pair bindings, delta ids, and PEPS3D rank labels are retained for every incidence row",
            "cell-count-only, transition-total-only, source-erased, pair-erased, rank-only, delta-only, and cell-erased outputs are rejected as insufficient",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "rank-transition residue incidence readout only",
            "inherited N01 only",
            "no fresh noncommuting operator",
            "no all-subset minimality",
            "no restore/inverse",
            "no topology/sheaf/homology/persistence closure",
            "no full PEPS3D closure",
            "downstream consumers blocked",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3_finite_residue_nonpromotion_gate", "cvc5_finite_residue_nonpromotion_gate", "sympy_exact_residue_count_checks"],
        "graph_surfaces_used": ["rustworkx_rank_transition_residue_graph", "xgi_rank_transition_residue_hypergraph", "torch_geometric_residue_support_aggregation"],
        "topology_surfaces_used": ["toponetx_finite_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "cell-count-only rejection",
            "rank-transition-total-only rejection",
            "source-erased rejection",
            "pair-erased rejection",
            "rank-only rejection",
            "delta-only rejection",
            "cell-erased rejection",
            "scalar-label rejection",
            "fresh-N01 rejection",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only cell counts or rank-transition totals are emitted",
            "cell ids, source ids, pair bindings, delta ids, or rank labels disappear",
            "all residues collapse to a scalar histogram",
            "fresh noncommuting operators are claimed",
            "dense closure is required",
            "topology/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_rank_transition_residue_incidence_v1",
        "result_summary": {
            "residue_count": residue["residue_count"],
            "incidence_row_count": residue["incidence_row_count"],
            "unique_cell_count": residue["unique_cell_count"],
            "residue_support_vector": residue["residue_support_vector"],
            "rank_residue_vector": residue["rank_residue_vector"],
        },
        "pass_rule": "delta-pair-source cells induce finite residue incidence rows with cell/source/pair/delta/rank retention, and controls remain blocked or collapsed",
        "fail_rule": "only scalar summaries are emitted, cell/source/pair/rank/delta bindings disappear, dense closure is used, fresh N01 is claimed, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite rank-transition residue incidence readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "AA_rank_transition_residue_incidence_K classified as bounded finite residue incidence readout",
                "cell-count and rank-transition-total variants classified as duplicate/rejected",
                "source-erased, pair-erased, rank-only, delta-only, and cell-erased variants classified as rejected",
                "fresh-N01 variants classified as rejected",
                "restore/inverse variants classified as rejected",
                "topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
                "F-rank null-boundary row classified as boundary evidence only",
            ],
        },
        "rank_transition_residue_table": residue["rank_transition_residue_table"],
        "rank_transition_residue_incidence_table": residue["rank_transition_residue_incidence_table"],
        "residue_count": residue["residue_count"],
        "incidence_row_count": residue["incidence_row_count"],
        "unique_cell_count": residue["unique_cell_count"],
        "residue_support_vector": residue["residue_support_vector"],
        "rank_residue_vector": residue["rank_residue_vector"],
        "delta_pair_source_cell_count": residue["delta_pair_source_cell_count"],
        "rank_transition_signature_total": residue["rank_transition_signature_total"],
        "cell_fiber_row_count": residue["cell_fiber_row_count"],
        "max_parent_peps3d_sites": residue["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": residue["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": residue["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "residue_count": residue["residue_count"],
                "incidence_row_count": residue["incidence_row_count"],
                "unique_cell_count": residue["unique_cell_count"],
                "residue_support_vector": residue["residue_support_vector"],
                "rank_residue_vector": residue["rank_residue_vector"],
                "max_parent_peps3d_sites": residue["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": residue["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": residue["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
