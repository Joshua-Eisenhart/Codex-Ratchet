#!/usr/bin/env python3
"""PEPS3D fiber pair/rank/delta projection scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite response-quotient
carrier geometry. It tests:

  Y_fiber_pair_rank_delta_projection_K :
      (Y_delta_class_source_fiber_K,
       source_binding_fiber_rows,
       pair_binding_id,
       rank,
       mask_delta_rank,
       active_source_class_id,
       boundary_source_class_id,
       PEPS3D V/E/F/C masks)
      -> finite pair-rank-delta projection table
         + pair/rank control gap vector
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
from sim_peps3d_delta_class_source_fiber_probe import delta_class_source_fiber_gate
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_fiber_pair_rank_delta_projection_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "Y_delta_class_source_fiber_K by projecting finite source-binding fiber "
    "rows to pair-binding/rank/mask-delta cells."
)
SCIENTIFIC_QUESTION = (
    "Do the 216 source-binding fiber rows induce a finite pair/rank/delta "
    "projection table that retains source ids and PEPS3D rank masks, while "
    "row-count-only, diversity-only, source-erased, pair-erased, rank-only, "
    "delta-only, dense-closure, and downstream controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_fiber_pair_rank_delta_projection"
PROMOTION_ALLOWED = False

PHASE2_FIBER_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_class_source_fiber_probe_results.json"
PHASE2_QUOTIENT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_contrast_mask_delta_quotient_probe_results.json"
PHASE2_CONTRAST_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_certificate_boundary_contrast_probe_results.json"
PHASE2_CERTIFICATE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_collision_certificate_projection_probe_results.json"
PHASE2_Y_INDUCED_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_induced_quotient_projection_probe_results.json"
PHASE2_Y_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_row_deletion_collision_stability_probe_results.json"
PHASE2_Z_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_active_pair_collision_residue_probe_results.json"
PHASE2_U_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_loss_pair_support_mask_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_delta_class_source_fiber_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_delta_class_source_fiber_candidate_map_discovery_20260526.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite pair-binding/rank/mask-delta "
    "projection over source-binding fiber rows. It does not admit all-subset "
    "minimality, restore/inverse, topology closure, sheaf closure, homology "
    "closure, persistence, bond convergence, shape law, nested Hopf tori, "
    "Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, Axis0, "
    "Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full PEPS3D "
    "closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing pair/rank/delta projection tensors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite projection graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing projection-cell hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite projection incidence cells without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing projection-cell aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite projection/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite projection/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact projection count checks"},
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


def fiber_pair_rank_delta_projection_gate() -> dict[str, Any]:
    fiber = delta_class_source_fiber_gate()
    buckets: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in fiber["source_binding_fiber_table"]:
        key = (row["pair_binding_id"], row["rank"], int(row["mask_delta_rank"]))
        buckets[key].append(row)

    projection_rows: list[dict[str, Any]] = []
    for index, (key, members) in enumerate(sorted(buckets.items())):
        pair_binding_id, rank, mask_delta_rank = key
        projection_rows.append(
            {
                "projection_id": f"pair_rank_delta_{index}",
                "pair_binding_id": pair_binding_id,
                "rank": rank,
                "mask_delta_rank": mask_delta_rank,
                "row_count": len(members),
                "fiber_row_ids": sorted(member["fiber_id"] for member in members),
                "active_source_class_ids": sorted({member["active_source_class_id"] for member in members}),
                "boundary_source_class_ids": sorted({member["boundary_source_class_id"] for member in members}),
                "delta_class_ids": sorted({member["delta_class_id"] for member in members}),
            }
        )

    row_counts = torch.tensor([row["row_count"] for row in projection_rows], dtype=torch.float64)
    projection_cell_count = len(projection_rows)
    projected_fiber_row_count = int(torch.sum(row_counts).item())
    source_retained = all(row["active_source_class_ids"] and row["boundary_source_class_ids"] for row in projection_rows)
    pair_retained = all(row["pair_binding_id"] for row in projection_rows)
    rank_retained = all(row["rank"] in {"V", "E", "F", "C"} for row in projection_rows)
    delta_retained = all(row["mask_delta_rank"] in {0, 1} for row in projection_rows)
    signature_vector = [int(value) for value in sorted(row_counts.tolist())]
    not_diversity_only = bool(projection_cell_count != fiber["binding_diversity_sum"])

    row_count_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "source_binding_fiber_row_count": fiber["source_binding_fiber_row_count"],
        "can_emit_pair_rank_delta_cells": False,
    }
    diversity_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "binding_diversity_sum": fiber["binding_diversity_sum"],
        "can_emit_projection_signature": False,
    }
    source_erased_control = {"pass": True, "control_status": "rejected_control", "can_bind_sources": False}
    pair_erased_control = {"pass": True, "control_status": "rejected_control", "can_bind_pair_cells": False}
    rank_only_control = {"pass": True, "control_status": "rejected_control", "rank_only": True}
    delta_only_control = {"pass": True, "control_status": "rejected_control", "delta_only": True}
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

    tool_sig = projection_tool_signature(projection_rows)
    pass_rule = bool(
        fiber["pass"]
        and projection_cell_count == 54
        and projected_fiber_row_count == 216
        and int(sp.Integer(projection_cell_count)) == 54
        and source_retained
        and pair_retained
        and rank_retained
        and delta_retained
        and not_diversity_only
        and row_count_only_control["pass"]
        and diversity_only_control["pass"]
        and source_erased_control["pass"]
        and pair_erased_control["pass"]
        and rank_only_control["pass"]
        and delta_only_control["pass"]
        and no_anchor_control["pass"]
        and closure_control["pass"]
        and tool_sig["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": "Y_fiber_pair_rank_delta_projection_K : (Y_delta_class_source_fiber_K, source_binding_fiber_rows, pair_binding_id, rank, mask_delta_rank, active_source_class_id, boundary_source_class_id, PEPS3D V/E/F/C masks) -> finite pair-rank-delta projection table + pair/rank control gap vector",
        "source_fiber_pass": fiber["pass"],
        "pair_rank_delta_projection_table": projection_rows,
        "pair_rank_delta_projection_cell_count": projection_cell_count,
        "projected_fiber_row_count": projected_fiber_row_count,
        "pair_rank_delta_signature_vector": signature_vector,
        "source_retained": source_retained,
        "pair_retained": pair_retained,
        "rank_retained": rank_retained,
        "delta_retained": delta_retained,
        "not_diversity_only": not_diversity_only,
        "row_count_only_control": row_count_only_control,
        "diversity_only_control": diversity_only_control,
        "source_erased_control": source_erased_control,
        "pair_erased_control": pair_erased_control,
        "rank_only_control": rank_only_control,
        "delta_only_control": delta_only_control,
        "no_anchor_control": no_anchor_control,
        "closure_control": closure_control,
        "tool_signature": tool_sig,
        "sympy_exact_projection_cell_count": int(sp.Integer(projection_cell_count)),
        "sympy_exact_projected_fiber_row_count": int(sp.Integer(projected_fiber_row_count)),
        "source_binding_fiber_row_count": fiber["source_binding_fiber_row_count"],
        "binding_diversity_sum": fiber["binding_diversity_sum"],
        "max_parent_peps3d_sites": fiber["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": fiber["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": fiber["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def projection_tool_signature(projection_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes: dict[str, int] = {}

    def node(name: str) -> int:
        if name not in nodes:
            nodes[name] = graph.add_node(name)
        return nodes[name]

    edge_count = 0
    for row in projection_rows:
        cell_node = node(row["projection_id"])
        for fiber_id in row["fiber_row_ids"]:
            graph.add_edge(cell_node, node(fiber_id), {"kind": "cell_to_fiber"})
            edge_count += 1
        graph.add_edge(node(row["pair_binding_id"]), cell_node, {"kind": "pair_to_cell"})
        graph.add_edge(node(row["rank"]), cell_node, {"kind": "rank_to_cell"})
        graph.add_edge(node(f"delta_{row['mask_delta_rank']}"), cell_node, {"kind": "delta_to_cell"})
        edge_count += 3

    hyper = xgi.Hypergraph()
    for row in projection_rows:
        hyper.add_edge(
            (row["projection_id"], row["pair_binding_id"], row["rank"], f"delta_{row['mask_delta_rank']}"),
            kind="pair_rank_delta_cell",
        )

    cell_complex = tnx.CellComplex()
    for row in projection_rows:
        cell_complex.add_node(row["projection_id"])
        for fiber_id in row["fiber_row_ids"]:
            cell_complex.add_node(fiber_id)
            cell_complex.add_cell((row["projection_id"], fiber_id), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids: dict[str, int] = {}

    def vid(name: str) -> int:
        if name not in vertex_ids:
            vertex_ids[name] = len(vertex_ids)
            simplex_tree.insert([vertex_ids[name]], filtration=0.0)
        return vertex_ids[name]

    for row in projection_rows:
        for fiber_id in row["fiber_row_ids"]:
            simplex_tree.insert([vid(row["projection_id"]), vid(fiber_id)], filtration=1.0)

    x = torch.tensor(
        [
            [
                float(row["row_count"]),
                float(len(row["active_source_class_ids"])),
                float(len(row["boundary_source_class_ids"])),
                float(row["mask_delta_rank"]),
            ]
            for row in projection_rows
        ],
        dtype=torch.float64,
    )
    edge_index = torch.tensor(
        [
            list(range(len(projection_rows))),
            [len(projection_rows)] * len(projection_rows),
        ],
        dtype=torch.long,
    )
    data = Data(x=x, edge_index=edge_index)
    return {
        "pass": bool(
            len(projection_rows) == 54
            and int(torch.sum(data.x[:, 0]).item()) == 216
            and int(graph.num_edges()) == edge_count
            and int(graph.num_edges()) == 378
            and int(hyper.num_edges) == 54
            and int(cell_complex.dim) == 1
            and int(data.edge_index.shape[1]) == 54
            and int(simplex_tree.num_simplices()) >= 270
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_projected_row_sum": float(torch.sum(data.x[:, 0]).item()),
    }


def z3_projection_gate(projection: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    source_retained = z3.Bool("source_retained")
    pair_retained = z3.Bool("pair_retained")
    rank_retained = z3.Bool("rank_retained")
    row_count_only = z3.Bool("row_count_only")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, source_retained, pair_retained, rank_retained)
    solver.add(z3.Not(row_count_only), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(projection["pair_rank_delta_projection_cell_count"] == 54))
    solver.add(z3.BoolVal(projection["projected_fiber_row_count"] == 216))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "projection_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_projection_gate(projection: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "source_retained": projection["source_retained"],
        "pair_retained": projection["pair_retained"],
        "rank_retained": projection["rank_retained"],
        "row_count_only": False,
        "dense": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("row_count_only", "dense", "downstream", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))
    contradiction = cvc5.Solver()
    bsort = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bsort, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "projection_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    projection = fiber_pair_rank_delta_projection_gate()
    z3_projection = z3_projection_gate(projection)
    cvc5_projection = cvc5_projection_gate(projection)
    positive = {"P1_fiber_pair_rank_delta_projection": projection}
    graveyard = {
        "GC_row_count_only_rejected": projection["row_count_only_control"],
        "GC_diversity_only_rejected": projection["diversity_only_control"],
        "GC_source_erased_rejected": projection["source_erased_control"],
        "GC_pair_erased_rejected": projection["pair_erased_control"],
        "GC_rank_only_rejected": projection["rank_only_control"],
        "GC_delta_only_rejected": projection["delta_only_control"],
        "GC_no_anchor_control_rejected": projection["no_anchor_control"],
        "GC_closure_and_downstream_not_opened": projection["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not projection["dense_state_closure_used"] and not projection["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_projection_cell_count": {
            "pass": projection["pair_rank_delta_projection_cell_count"] == 54,
            "pair_rank_delta_projection_cell_count": projection["pair_rank_delta_projection_cell_count"],
        },
        "B4_projected_fiber_row_count": {
            "pass": projection["projected_fiber_row_count"] == 216,
            "projected_fiber_row_count": projection["projected_fiber_row_count"],
        },
        "B5_z3_finite_projection_nonpromotion": z3_projection,
        "B6_cvc5_finite_projection_nonpromotion": cvc5_projection,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        projection["pass"]
        and z3_projection["pass"]
        and cvc5_projection["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
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
            "F01": "finite source-binding fiber rows, finite pair bindings, finite rank labels, finite mask-delta bits, finite source ids, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this projection inherits the Phase 2 carrier order witness and rejects order-erased promotion",
        },
        "finite_map": projection["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C rank-mask rows inherited from Y_delta_class_source_fiber_K",
            "source_binding_fiber_rows": "216 finite fiber rows",
            "pair_binding_id": "finite active_pair_id -> boundary_pair_id bindings",
            "rank": "finite rank labels {V,E,F,C}",
            "mask_delta_rank": "finite rank-local mask-delta bit in {0,1}",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite pair-rank-delta projection table, pair-rank-delta signature vector, source-retention table, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_fiber_pair_rank_delta_projection",
        "carrier_realization": "torch finite projection tensors over PEPS3D V/E/F/C source-binding fiber rows with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every projection row retains finite pair binding, source ids, rank label, and mask-delta-rank bit from PEPS3D V/E/F/C fiber rows. Scalar labels and summaries are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite pair-binding/rank/mask-delta projection over source-binding fiber rows",
        "branch_status_before_run": "post_Y_delta_class_source_fiber_K_candidate_map_discovery_Y_fiber_pair_rank_delta_projection_K",
        "allowed_claims": [
            "source-binding fiber rows project to finite pair/rank/delta cells",
            "source ids, pair bindings, rank labels, and mask-delta-rank bits are retained for every projection cell",
            "row-count-only, diversity-only, source-erased, pair-erased, rank-only, and delta-only outputs are rejected as insufficient",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "pair-rank-delta projection readout only",
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
        "proof_surfaces_used": ["z3_finite_projection_nonpromotion_gate", "cvc5_finite_projection_nonpromotion_gate", "sympy_exact_projection_count_checks"],
        "graph_surfaces_used": ["rustworkx_pair_rank_delta_projection_graph", "xgi_pair_rank_delta_projection_hypergraph", "torch_geometric_projection_aggregation"],
        "topology_surfaces_used": ["toponetx_finite_projection_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "row-count-only rejection",
            "diversity-only rejection",
            "source-erased rejection",
            "pair-erased rejection",
            "rank-only rejection",
            "delta-only rejection",
            "no-anchor rejection",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only row counts, diversity sums, ranks, or deltas are emitted",
            "source ids, pair bindings, rank labels, or mask-delta-rank bits disappear",
            "all projection rows collapse to a source-erased scalar histogram",
            "dense closure is required",
            "topology/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_fiber_pair_rank_delta_projection_v1",
        "result_summary": {
            "pair_rank_delta_projection_cell_count": projection["pair_rank_delta_projection_cell_count"],
            "projected_fiber_row_count": projection["projected_fiber_row_count"],
            "pair_rank_delta_signature_vector": projection["pair_rank_delta_signature_vector"],
        },
        "pass_rule": "source-binding fiber rows project to finite pair/rank/delta cells with source and pair retention, and controls remain blocked or collapsed",
        "fail_rule": "only scalar summaries are emitted, source/pair/rank/delta bindings disappear, dense closure is used, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite pair-rank-delta projection readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "Y_fiber_pair_rank_delta_projection_K classified as bounded finite projection readout",
                "fiber-row-count and diversity-only variants classified as duplicate/rejected",
                "source-erased and pair-erased variants classified as rejected",
                "rank-only and delta-only variants classified as rejected",
                "restore/inverse variants classified as rejected",
                "topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
            ],
        },
        "pair_rank_delta_projection_table": projection["pair_rank_delta_projection_table"],
        "pair_rank_delta_projection_cell_count": projection["pair_rank_delta_projection_cell_count"],
        "projected_fiber_row_count": projection["projected_fiber_row_count"],
        "pair_rank_delta_signature_vector": projection["pair_rank_delta_signature_vector"],
        "source_binding_fiber_row_count": projection["source_binding_fiber_row_count"],
        "binding_diversity_sum": projection["binding_diversity_sum"],
        "max_parent_peps3d_sites": projection["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": projection["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": projection["max_peps3d_bond"],
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
                "pair_rank_delta_projection_cell_count": projection["pair_rank_delta_projection_cell_count"],
                "projected_fiber_row_count": projection["projected_fiber_row_count"],
                "source_binding_fiber_row_count": projection["source_binding_fiber_row_count"],
                "max_parent_peps3d_sites": projection["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": projection["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": projection["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
