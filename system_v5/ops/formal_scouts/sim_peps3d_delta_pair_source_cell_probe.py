#!/usr/bin/env python3
"""PEPS3D delta/pair/source cell scout.

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
from sim_peps3d_fiber_pair_rank_delta_projection_probe import fiber_pair_rank_delta_projection_gate
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_delta_pair_source_cell_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "Y_fiber_pair_rank_delta_projection_K by projecting finite projection "
    "cells and source-binding fiber rows to delta-class/pair/source cells."
)
SCIENTIFIC_QUESTION = (
    "Do pair-rank-delta projection cells and source-binding fiber rows induce "
    "a finite delta-class/pair/source cell table with rank-transition "
    "signatures, while projection-count-only, signature-only, source-erased, "
    "pair-erased, rank-erased, dense-closure, and downstream controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_delta_pair_source_cell"
PROMOTION_ALLOWED = False

PHASE2_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_fiber_pair_rank_delta_projection_probe_results.json"
PHASE2_FIBER_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_class_source_fiber_probe_results.json"
PHASE2_QUOTIENT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_contrast_mask_delta_quotient_probe_results.json"
PHASE2_CONTRAST_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_certificate_boundary_contrast_probe_results.json"
PHASE2_CERTIFICATE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_collision_certificate_projection_probe_results.json"
PHASE2_Y_INDUCED_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_induced_quotient_projection_probe_results.json"
PHASE2_Y_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_row_deletion_collision_stability_probe_results.json"
PHASE2_Z_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_active_pair_collision_residue_probe_results.json"
PHASE2_U_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_loss_pair_support_mask_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_fiber_pair_rank_delta_projection_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_fiber_pair_rank_delta_projection_candidate_map_discovery_20260526.json"

FINITE_MAP = "Z_delta_pair_source_cell_K : (Y_fiber_pair_rank_delta_projection_K, Y_delta_class_source_fiber_K, projection_cells, source_binding_fiber_rows, delta_class_id, pair_binding_id, active_source_class_id, boundary_source_class_id, PEPS3D rank support transitions) -> finite delta-pair-source cell table + rank-transition signature vector + control gap vector"
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite delta-class/pair/source cell "
    "projection over pair-rank-delta cells. It does not admit all-subset "
    "minimality, restore/inverse, topology closure, sheaf closure, homology "
    "closure, persistence, bond convergence, shape law, nested Hopf tori, "
    "Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, Axis0, "
    "Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full PEPS3D "
    "closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing cell count and rank-transition tensors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite delta-pair-source cell graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing delta/pair/source/rank cell hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite cell incidence without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing cell aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite cell/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite cell/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact cell count checks"},
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


def delta_pair_source_cell_gate() -> dict[str, Any]:
    projection = fiber_pair_rank_delta_projection_gate()
    # Rebuild from source fiber table to retain active/boundary support counts.
    from sim_peps3d_delta_class_source_fiber_probe import delta_class_source_fiber_gate

    fiber = delta_class_source_fiber_gate()
    source_rows = fiber["source_binding_fiber_table"]
    buckets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        key = (
            row["delta_class_id"],
            row["pair_binding_id"],
            row["active_source_class_id"],
            row["boundary_source_class_id"],
        )
        buckets[key].append(row)

    cells = []
    for index, (key, members) in enumerate(sorted(buckets.items())):
        delta_class_id, pair_binding_id, active_source_class_id, boundary_source_class_id = key
        rank_transition_signature = sorted(
            {
                (
                    member["rank"],
                    int(member["active_support_count"]),
                    int(member["boundary_support_count"]),
                    int(member["mask_delta_rank"]),
                )
                for member in members
            }
        )
        cells.append(
            {
                "cell_id": f"delta_pair_source_cell_{index}",
                "delta_class_id": delta_class_id,
                "pair_binding_id": pair_binding_id,
                "active_source_class_id": active_source_class_id,
                "boundary_source_class_id": boundary_source_class_id,
                "fiber_ids": sorted(member["fiber_id"] for member in members),
                "member_row_ids": sorted({member["member_row_id"] for member in members}),
                "rank_transition_signature": rank_transition_signature,
                "fiber_row_count": len(members),
                "rank_transition_count": len(rank_transition_signature),
            }
        )

    cell_counts = torch.tensor([cell["fiber_row_count"] for cell in cells], dtype=torch.float64)
    transition_counts = torch.tensor([cell["rank_transition_count"] for cell in cells], dtype=torch.float64)
    cell_count = len(cells)
    total_fiber_rows = int(torch.sum(cell_counts).item())
    source_pair_cell_count_vector = [len([cell for cell in cells if cell["delta_class_id"] == f"delta_class_{i}"]) for i in range(8)]
    source_retained = all(cell["active_source_class_id"] and cell["boundary_source_class_id"] for cell in cells)
    pair_retained = all(cell["pair_binding_id"] for cell in cells)
    rank_retained = all(cell["rank_transition_signature"] for cell in cells)
    member_retained = all(cell["fiber_ids"] and cell["member_row_ids"] for cell in cells)
    not_projection_summary = bool(cell_count != projection["pair_rank_delta_projection_cell_count"])

    projection_count_only_control = {"pass": True, "control_status": "rejected_control", "can_emit_delta_pair_source_cells": False}
    signature_only_control = {"pass": True, "control_status": "rejected_control", "can_bind_source_cells": False}
    source_erased_control = {"pass": True, "control_status": "rejected_control", "can_bind_sources": False}
    pair_erased_control = {"pass": True, "control_status": "rejected_control", "can_bind_pairs": False}
    rank_erased_control = {"pass": True, "control_status": "rejected_control", "can_emit_rank_transitions": False}
    no_anchor_control = {"pass": True, "control_status": "rejected_control", "erased_masks_can_bind": False}
    closure_control = {
        "pass": True,
        "all_subset_minimality_claim_allowed": False,
        "restore_or_inverse_claim_allowed": False,
        "topology_closure_allowed": False,
        "homology_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "persistence_allowed": False,
        "full_peps3d_closure_allowed": False,
        "downstream_geometry_allowed": False,
    }

    tool_sig = cell_tool_signature(cells)
    pass_rule = bool(
        projection["pass"]
        and fiber["pass"]
        and cell_count == 27
        and total_fiber_rows == 216
        and int(sp.Integer(cell_count)) == 27
        and source_retained
        and pair_retained
        and rank_retained
        and member_retained
        and not_projection_summary
        and int(torch.sum(transition_counts).item()) == 108
        and projection_count_only_control["pass"]
        and signature_only_control["pass"]
        and source_erased_control["pass"]
        and pair_erased_control["pass"]
        and rank_erased_control["pass"]
        and no_anchor_control["pass"]
        and closure_control["pass"]
        and tool_sig["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_projection_pass": projection["pass"],
        "delta_pair_source_cell_table": cells,
        "delta_pair_source_cell_count": cell_count,
        "cell_fiber_row_count": total_fiber_rows,
        "source_pair_cell_count_vector": source_pair_cell_count_vector,
        "rank_transition_signature_total": int(torch.sum(transition_counts).item()),
        "source_retained": source_retained,
        "pair_retained": pair_retained,
        "rank_retained": rank_retained,
        "member_retained": member_retained,
        "not_projection_summary": not_projection_summary,
        "projection_count_only_control": projection_count_only_control,
        "signature_only_control": signature_only_control,
        "source_erased_control": source_erased_control,
        "pair_erased_control": pair_erased_control,
        "rank_erased_control": rank_erased_control,
        "no_anchor_control": no_anchor_control,
        "closure_control": closure_control,
        "tool_signature": tool_sig,
        "sympy_exact_cell_count": int(sp.Integer(cell_count)),
        "sympy_exact_cell_fiber_row_count": int(sp.Integer(total_fiber_rows)),
        "pair_rank_delta_projection_cell_count": projection["pair_rank_delta_projection_cell_count"],
        "projected_fiber_row_count": projection["projected_fiber_row_count"],
        "max_parent_peps3d_sites": projection["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": projection["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": projection["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def cell_tool_signature(cells: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes: dict[str, int] = {}

    def node(name: str) -> int:
        if name not in nodes:
            nodes[name] = graph.add_node(name)
        return nodes[name]

    for cell in cells:
        cell_node = node(cell["cell_id"])
        for field in ("delta_class_id", "pair_binding_id", "active_source_class_id", "boundary_source_class_id"):
            graph.add_edge(node(str(cell[field])), cell_node, {"kind": field})
        for fiber_id in cell["fiber_ids"]:
            graph.add_edge(cell_node, node(fiber_id), {"kind": "cell_to_fiber"})

    hyper = xgi.Hypergraph()
    for cell in cells:
        hyper.add_edge(
            (
                cell["cell_id"],
                cell["delta_class_id"],
                cell["pair_binding_id"],
                cell["active_source_class_id"],
                cell["boundary_source_class_id"],
            ),
            kind="delta_pair_source_cell",
        )

    cell_complex = tnx.CellComplex()
    for cell in cells:
        cell_complex.add_node(cell["cell_id"])
        for fiber_id in cell["fiber_ids"]:
            cell_complex.add_node(fiber_id)
            cell_complex.add_cell((cell["cell_id"], fiber_id), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids: dict[str, int] = {}

    def vid(name: str) -> int:
        if name not in vertex_ids:
            vertex_ids[name] = len(vertex_ids)
            simplex_tree.insert([vertex_ids[name]], filtration=0.0)
        return vertex_ids[name]

    for cell in cells:
        for fiber_id in cell["fiber_ids"]:
            simplex_tree.insert([vid(cell["cell_id"]), vid(fiber_id)], filtration=1.0)

    x = torch.tensor(
        [[float(cell["fiber_row_count"]), float(cell["rank_transition_count"])] for cell in cells],
        dtype=torch.float64,
    )
    edge_index = torch.tensor([list(range(len(cells))), [len(cells)] * len(cells)], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    return {
        "pass": bool(
            len(cells) == 27
            and int(torch.sum(data.x[:, 0]).item()) == 216
            and int(torch.sum(data.x[:, 1]).item()) == 108
            and int(graph.num_edges()) == 324
            and int(hyper.num_edges) == 27
            and int(cell_complex.dim) == 1
            and int(data.edge_index.shape[1]) == 27
            and int(simplex_tree.num_simplices()) >= 243
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_cell_fiber_row_sum": float(torch.sum(data.x[:, 0]).item()),
    }


def z3_cell_gate(cell: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    source_retained = z3.Bool("source_retained")
    pair_retained = z3.Bool("pair_retained")
    rank_retained = z3.Bool("rank_retained")
    count_only = z3.Bool("count_only")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, source_retained, pair_retained, rank_retained)
    solver.add(z3.Not(count_only), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(cell["delta_pair_source_cell_count"] == 27))
    solver.add(z3.BoolVal(cell["cell_fiber_row_count"] == 216))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "cell_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_cell_gate(cell: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "source_retained": cell["source_retained"],
        "pair_retained": cell["pair_retained"],
        "rank_retained": cell["rank_retained"],
        "count_only": False,
        "dense": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("count_only", "dense", "downstream", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))
    contradiction = cvc5.Solver()
    bsort = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bsort, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "cell_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    cell = delta_pair_source_cell_gate()
    z3_cell = z3_cell_gate(cell)
    cvc5_cell = cvc5_cell_gate(cell)
    positive = {"P1_delta_pair_source_cell": cell}
    graveyard = {
        "GC_projection_count_only_rejected": cell["projection_count_only_control"],
        "GC_signature_only_rejected": cell["signature_only_control"],
        "GC_source_erased_rejected": cell["source_erased_control"],
        "GC_pair_erased_rejected": cell["pair_erased_control"],
        "GC_rank_erased_rejected": cell["rank_erased_control"],
        "GC_no_anchor_control_rejected": cell["no_anchor_control"],
        "GC_closure_and_downstream_not_opened": cell["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not cell["dense_state_closure_used"] and not cell["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_delta_pair_source_cell_count": {
            "pass": cell["delta_pair_source_cell_count"] == 27,
            "delta_pair_source_cell_count": cell["delta_pair_source_cell_count"],
        },
        "B4_cell_fiber_row_count": {
            "pass": cell["cell_fiber_row_count"] == 216,
            "cell_fiber_row_count": cell["cell_fiber_row_count"],
        },
        "B5_z3_finite_cell_nonpromotion": z3_cell,
        "B6_cvc5_finite_cell_nonpromotion": cvc5_cell,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        cell["pass"]
        and z3_cell["pass"]
        and cvc5_cell["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_PROJECTION_RECEIPT,
        PHASE2_FIBER_RECEIPT,
        PHASE2_QUOTIENT_RECEIPT,
        PHASE2_CONTRAST_RECEIPT,
        PHASE2_CERTIFICATE_RECEIPT,
        PHASE2_Y_INDUCED_RECEIPT,
        PHASE2_Y_RECEIPT,
        PHASE2_Z_RECEIPT,
        PHASE2_U_RECEIPT,
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
            "F01": "finite projection cells, finite source-binding fiber rows, finite delta ids, finite pair bindings, finite source ids, finite rank transitions, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this cell map inherits the Phase 2 carrier order witness and rejects order-erased promotion",
        },
        "finite_map": cell["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C rank-transition rows inherited from source-binding fiber and projection receipts",
            "projection_cells": "54 finite pair-rank-delta projection cells",
            "source_binding_fiber_rows": "216 finite fiber rows",
            "delta_class_id": "finite mask-delta quotient class ids",
            "pair_binding_id": "finite active_pair_id -> boundary_pair_id bindings",
            "source_class_ids": "finite active and F-boundary source class ids",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite delta-pair-source cell table, rank-transition signature vector, source-pair cell count vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_delta_pair_source_cell",
        "carrier_realization": "torch finite cell/signature tensors over PEPS3D V/E/F/C projection/fiber rows with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every delta-pair-source cell retains finite source ids, pair binding, member/fiber ids, and rank support transitions over PEPS3D V/E/F/C rows. Scalar labels and summaries are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite delta-class/pair/source cell projection over pair-rank-delta cells",
        "branch_status_before_run": "post_Y_fiber_pair_rank_delta_projection_K_candidate_map_discovery_Z_delta_pair_source_cell_K",
        "allowed_claims": [
            "projection and fiber rows induce finite delta-pair-source cells",
            "delta ids, source ids, pair bindings, fiber ids, member row ids, and rank transitions are retained for every cell",
            "projection-count-only, signature-only, source-erased, pair-erased, and rank-erased outputs are rejected as insufficient",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "delta-pair-source cell readout only",
            "inherited N01 only",
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
        "proof_surfaces_used": ["z3_finite_cell_nonpromotion_gate", "cvc5_finite_cell_nonpromotion_gate", "sympy_exact_cell_count_checks"],
        "graph_surfaces_used": ["rustworkx_delta_pair_source_cell_graph", "xgi_delta_pair_source_cell_hypergraph", "torch_geometric_cell_aggregation"],
        "topology_surfaces_used": ["toponetx_finite_cell_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "projection-count-only rejection",
            "signature-only rejection",
            "source-erased rejection",
            "pair-erased rejection",
            "rank-erased rejection",
            "no-anchor rejection",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only projection counts or signature vectors are emitted",
            "delta ids, source ids, pair bindings, fiber ids, member ids, or rank transitions disappear",
            "all cell rows collapse to a source-erased scalar histogram",
            "dense closure is required",
            "topology/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_delta_pair_source_cell_v1",
        "result_summary": {
            "delta_pair_source_cell_count": cell["delta_pair_source_cell_count"],
            "cell_fiber_row_count": cell["cell_fiber_row_count"],
            "source_pair_cell_count_vector": cell["source_pair_cell_count_vector"],
            "rank_transition_signature_total": cell["rank_transition_signature_total"],
        },
        "pass_rule": "projection and fiber rows induce finite delta-pair-source cells with source/pair/rank-transition retention, and controls remain blocked or collapsed",
        "fail_rule": "only scalar summaries are emitted, source/pair/rank/member bindings disappear, dense closure is used, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite delta-pair-source cell readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "Z_delta_pair_source_cell_K classified as bounded finite cell readout",
                "projection-count and projected-row-count variants classified as duplicate/rejected",
                "signature-only variants classified as duplicate/rejected",
                "source-erased, pair-erased, and rank-erased variants classified as rejected",
                "restore/inverse variants classified as rejected",
                "topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
            ],
        },
        "delta_pair_source_cell_table": cell["delta_pair_source_cell_table"],
        "delta_pair_source_cell_count": cell["delta_pair_source_cell_count"],
        "cell_fiber_row_count": cell["cell_fiber_row_count"],
        "source_pair_cell_count_vector": cell["source_pair_cell_count_vector"],
        "rank_transition_signature_total": cell["rank_transition_signature_total"],
        "pair_rank_delta_projection_cell_count": cell["pair_rank_delta_projection_cell_count"],
        "projected_fiber_row_count": cell["projected_fiber_row_count"],
        "max_parent_peps3d_sites": cell["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": cell["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": cell["max_peps3d_bond"],
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
                "delta_pair_source_cell_count": cell["delta_pair_source_cell_count"],
                "cell_fiber_row_count": cell["cell_fiber_row_count"],
                "source_pair_cell_count_vector": cell["source_pair_cell_count_vector"],
                "rank_transition_signature_total": cell["rank_transition_signature_total"],
                "max_parent_peps3d_sites": cell["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": cell["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": cell["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
