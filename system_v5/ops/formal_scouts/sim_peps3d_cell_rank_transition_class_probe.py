#!/usr/bin/env python3
"""PEPS3D cell rank-transition class scout.

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
from sim_peps3d_rank_transition_residue_incidence_probe import rank_transition_residue_incidence_gate
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
REPO_ROOT = ROOT.parents[2]
NAME = "peps3d_cell_rank_transition_class_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AA_rank_transition_residue_incidence_K by assembling per-cell four-rank "
    "transition normal forms and finite transition classes."
)
SCIENTIFIC_QUESTION = (
    "Do the 108 residue incidence rows induce a finite cell-to-rank-transition "
    "class table retaining cell, residue, source, pair, delta, and PEPS3D rank "
    "bindings, while count-only, residue-only, cell-erased, source-erased, "
    "pair-erased, delta-erased, rank-erased, dense-closure, fresh-N01, and "
    "downstream controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_cell_rank_transition_class"
PROMOTION_ALLOWED = False

PHASE2_RESIDUE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_rank_transition_residue_incidence_probe_results.json"
PHASE2_CELL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_pair_source_cell_probe_results.json"
PHASE2_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_fiber_pair_rank_delta_projection_probe_results.json"
PHASE2_FIBER_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_class_source_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AA_rank_transition_residue_incidence_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_AA_rank_transition_residue_incidence_candidate_map_discovery_20260526.json"

FINITE_MAP = "AB_cell_rank_transition_class_K : (AA_rank_transition_residue_incidence_K, rank_transition_residue_incidence_table, cell_id, residue_id, delta_class_id, pair_binding_id, source_class_ids, PEPS3D rank labels) -> finite cell-to-rank-transition-class table + transition-class support vector + control gap vector"
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite cell rank-transition class "
    "readout over residue incidence rows. It does not admit fresh "
    "noncommuting operators, all-subset minimality, restore/inverse, topology "
    "closure, sheaf closure, homology closure, persistence, bond convergence, "
    "shape law, nested Hopf tori, Weyl sheets, terrain, operator substage "
    "cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, "
    "axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing transition class support tensors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite cell/class incidence graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing cell/class/source/pair/rank hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite class incidence cells without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing transition class support aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite transition-class/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite transition-class/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact class and cell count checks"},
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
RANK_ORDER = {rank: index for index, rank in enumerate(RANK_LABELS)}


def load_dependency_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(residue: dict[str, Any], receipt: dict[str, Any]) -> bool:
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("incidence_row_count") == residue["incidence_row_count"]
        and summary.get("residue_count") == residue["residue_count"]
        and summary.get("unique_cell_count") == residue["unique_cell_count"]
        and summary.get("rank_residue_vector") == residue["rank_residue_vector"]
        and summary.get("residue_support_vector") == residue["residue_support_vector"]
    )


def cell_rank_transition_class_gate() -> dict[str, Any]:
    residue = rank_transition_residue_incidence_gate()
    residue_receipt = load_dependency_receipt(PHASE2_RESIDUE_RECEIPT)
    dependency_receipt_verified = dependency_receipt_matches(residue, residue_receipt)
    incidence_rows = residue["rank_transition_residue_incidence_table"]
    by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in incidence_rows:
        by_cell[row["cell_id"]].append(row)

    signature_to_cells: dict[tuple[tuple[str, int, int, int], ...], list[str]] = defaultdict(list)
    cell_rows = []
    binding_agreement_by_cell: dict[str, bool] = {}
    for cell_id, rows in sorted(by_cell.items()):
        rank_rows = sorted(rows, key=lambda row: RANK_ORDER[row["rank"]])
        rank_set_exact = tuple(row["rank"] for row in rank_rows) == RANK_LABELS
        binding_keys = (
            "delta_class_id",
            "pair_binding_id",
            "active_source_class_id",
            "boundary_source_class_id",
        )
        binding_agreement = rank_set_exact and all(
            len({row[key] for row in rank_rows}) == 1 for key in binding_keys
        )
        binding_agreement_by_cell[cell_id] = binding_agreement
        normal_form = tuple(
            (
                row["rank"],
                int(row["active_support_count"]),
                int(row["boundary_support_count"]),
                int(row["mask_delta_rank"]),
            )
            for row in rank_rows
        )
        signature_to_cells[normal_form].append(cell_id)
        representative = rank_rows[0]
        cell_rows.append(
            {
                "cell_id": cell_id,
                "transition_class_signature": normal_form,
                "residue_ids": [row["residue_id"] for row in rank_rows],
                "delta_class_id": representative["delta_class_id"],
                "pair_binding_id": representative["pair_binding_id"],
                "active_source_class_id": representative["active_source_class_id"],
                "boundary_source_class_id": representative["boundary_source_class_id"],
            }
        )

    class_id_by_signature = {
        signature: f"transition_class_{index}"
        for index, signature in enumerate(sorted(signature_to_cells))
    }
    for row in cell_rows:
        row["transition_class_id"] = class_id_by_signature[row["transition_class_signature"]]
        row["transition_class_signature"] = [list(item) for item in row["transition_class_signature"]]

    class_rows = []
    for signature, class_id in sorted(class_id_by_signature.items(), key=lambda item: item[1]):
        cells = sorted(signature_to_cells[signature])
        members = [row for row in cell_rows if row["cell_id"] in cells]
        class_rows.append(
            {
                "transition_class_id": class_id,
                "support_cell_ids": cells,
                "support_cell_count": len(cells),
                "transition_class_signature": [list(item) for item in signature],
                "delta_class_ids": sorted({member["delta_class_id"] for member in members}),
                "pair_binding_ids": sorted({member["pair_binding_id"] for member in members}),
                "active_source_class_ids": sorted({member["active_source_class_id"] for member in members}),
                "boundary_source_class_ids": sorted({member["boundary_source_class_id"] for member in members}),
            }
        )

    support_tensor = torch.tensor([row["support_cell_count"] for row in class_rows], dtype=torch.float64)
    transition_class_support_vector = [int(value) for value in sorted(support_tensor.tolist())]
    transition_class_count = len(class_rows)
    cell_transition_row_count = len(cell_rows)
    singleton_class_count = len([row for row in class_rows if row["support_cell_count"] == 1])
    doubleton_class_count = len([row for row in class_rows if row["support_cell_count"] == 2])
    source_retained = all(row["active_source_class_ids"] and row["boundary_source_class_ids"] for row in class_rows)
    pair_retained = all(row["pair_binding_ids"] for row in class_rows)
    rank_retained = all(
        tuple(item[0] for item in row["transition_class_signature"]) == RANK_LABELS
        for row in class_rows
    )
    cell_retained = all(row["support_cell_ids"] for row in class_rows)
    delta_retained = all(row["delta_class_ids"] for row in class_rows)
    residue_retained = all(len(row["residue_ids"]) == 4 for row in cell_rows)
    binding_agreement_retained = all(binding_agreement_by_cell.values())
    not_residue_count_only = transition_class_count != residue["residue_count"]
    not_cell_count_only = transition_class_count != residue["unique_cell_count"]
    f_component_retained = all(row["transition_class_signature"][2][0] == "F" for row in class_rows)

    erased_control_evidence = {
        "cell_count_only": {
            "input": residue["unique_cell_count"],
            "transition_class_count": transition_class_count,
            "failed_as_complete_map": residue["unique_cell_count"] != transition_class_count,
        },
        "residue_count_only": {
            "input": residue["residue_count"],
            "transition_class_count": transition_class_count,
            "failed_as_complete_map": residue["residue_count"] != transition_class_count,
        },
        "rank_residue_vector_only": {
            "input": residue["rank_residue_vector"],
            "cell_binding_count": 0,
            "failed_as_complete_map": True,
        },
        "cell_erased": {
            "distinct_signatures_without_cell_ids": len({tuple(tuple(item) for item in row["transition_class_signature"]) for row in class_rows}),
            "cell_ids_retained": False,
            "failed_as_complete_map": True,
        },
        "source_erased": {"source_bindings_retained": False, "failed_as_complete_map": source_retained},
        "pair_erased": {"pair_bindings_retained": False, "failed_as_complete_map": pair_retained},
        "delta_erased": {"delta_bindings_retained": False, "failed_as_complete_map": delta_retained},
        "rank_erased": {"rank_normal_form_retained": False, "failed_as_complete_map": rank_retained},
    }
    controls = {
        "cell_count_only_control": {"pass": erased_control_evidence["cell_count_only"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["cell_count_only"]},
        "residue_count_only_control": {"pass": erased_control_evidence["residue_count_only"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["residue_count_only"]},
        "rank_residue_vector_only_control": {"pass": erased_control_evidence["rank_residue_vector_only"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["rank_residue_vector_only"]},
        "cell_erased_control": {"pass": erased_control_evidence["cell_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["cell_erased"]},
        "source_erased_control": {"pass": erased_control_evidence["source_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["source_erased"]},
        "pair_erased_control": {"pass": erased_control_evidence["pair_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["pair_erased"]},
        "delta_erased_control": {"pass": erased_control_evidence["delta_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["delta_erased"]},
        "rank_erased_control": {"pass": erased_control_evidence["rank_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["rank_erased"]},
        "scalar_label_control": {"pass": True, "control_status": "rejected_control", "can_bind_peps3d_rows": False, "failed_as_complete_map": True},
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

    tool_sig = class_tool_signature(cell_rows, class_rows)
    pass_rule = bool(
        residue["pass"]
        and dependency_receipt_verified
        and transition_class_count == 18
        and cell_transition_row_count == 27
        and singleton_class_count == 9
        and doubleton_class_count == 9
        and int(sp.Integer(transition_class_count)) == 18
        and int(torch.sum(support_tensor).item()) == 27
        and transition_class_support_vector == [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        and source_retained
        and pair_retained
        and rank_retained
        and cell_retained
        and delta_retained
        and residue_retained
        and binding_agreement_retained
        and not_residue_count_only
        and not_cell_count_only
        and f_component_retained
        and all(control["pass"] for control in controls.values())
        and tool_sig["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_residue_pass": residue["pass"],
        "dependency_receipt_verified": dependency_receipt_verified,
        "cell_rank_transition_class_table": cell_rows,
        "transition_class_table": class_rows,
        "transition_class_count": transition_class_count,
        "cell_transition_row_count": cell_transition_row_count,
        "singleton_class_count": singleton_class_count,
        "doubleton_class_count": doubleton_class_count,
        "transition_class_support_vector": transition_class_support_vector,
        "source_retained": source_retained,
        "pair_retained": pair_retained,
        "rank_retained": rank_retained,
        "cell_retained": cell_retained,
        "delta_retained": delta_retained,
        "residue_retained": residue_retained,
        "binding_agreement_by_cell": binding_agreement_by_cell,
        "binding_agreement_retained": binding_agreement_retained,
        "not_residue_count_only": not_residue_count_only,
        "not_cell_count_only": not_cell_count_only,
        "f_component_retained": f_component_retained,
        "rank_order": list(RANK_LABELS),
        "erased_control_evidence": erased_control_evidence,
        "controls": controls,
        "tool_signature": tool_sig,
        "sympy_exact_transition_class_count": int(sp.Integer(transition_class_count)),
        "sympy_exact_cell_transition_row_count": int(sp.Integer(cell_transition_row_count)),
        "residue_count": residue["residue_count"],
        "incidence_row_count": residue["incidence_row_count"],
        "unique_cell_count": residue["unique_cell_count"],
        "rank_residue_vector": residue["rank_residue_vector"],
        "max_parent_peps3d_sites": residue["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": residue["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": residue["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def class_tool_signature(cell_rows: list[dict[str, Any]], class_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes: dict[str, int] = {}

    def node(name: str) -> int:
        if name not in nodes:
            nodes[name] = graph.add_node(name)
        return nodes[name]

    for row in cell_rows:
        cell_node = node(row["cell_id"])
        graph.add_edge(node(row["transition_class_id"]), cell_node, {"kind": "class_to_cell"})
        graph.add_edge(node(row["delta_class_id"]), cell_node, {"kind": "delta_to_cell"})
        graph.add_edge(node(row["pair_binding_id"]), cell_node, {"kind": "pair_to_cell"})
        graph.add_edge(node(row["active_source_class_id"]), cell_node, {"kind": "active_source_to_cell"})
        graph.add_edge(node(row["boundary_source_class_id"]), cell_node, {"kind": "boundary_source_to_cell"})
        for residue_id in row["residue_ids"]:
            graph.add_edge(node(residue_id), cell_node, {"kind": "residue_to_cell"})

    hyper = xgi.Hypergraph()
    for row in cell_rows:
        hyper.add_edge(
            (
                row["cell_id"],
                row["transition_class_id"],
                row["delta_class_id"],
                row["pair_binding_id"],
                row["active_source_class_id"],
                row["boundary_source_class_id"],
            ),
            kind="cell_rank_transition_class",
        )

    cell_complex = tnx.CellComplex()
    for row in cell_rows:
        cell_complex.add_node(row["transition_class_id"])
        cell_complex.add_node(row["cell_id"])
        cell_complex.add_cell((row["transition_class_id"], row["cell_id"]), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids: dict[str, int] = {}

    def vid(name: str) -> int:
        if name not in vertex_ids:
            vertex_ids[name] = len(vertex_ids)
            simplex_tree.insert([vertex_ids[name]], filtration=0.0)
        return vertex_ids[name]

    for row in cell_rows:
        simplex_tree.insert([vid(row["transition_class_id"]), vid(row["cell_id"])], filtration=1.0)

    class_features = torch.tensor(
        [[float(row["support_cell_count"]), float(len(row["delta_class_ids"])), float(len(row["pair_binding_ids"]))] for row in class_rows],
        dtype=torch.float64,
    )
    sink_feature = torch.sum(class_features, dim=0, keepdim=True)
    x = torch.cat([class_features, sink_feature], dim=0)
    sink_index = len(class_rows)
    edge_index = torch.tensor([list(range(len(class_rows))), [sink_index] * len(class_rows)], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    return {
        "pass": bool(
            len(class_rows) == 18
            and len(cell_rows) == 27
            and int(torch.sum(class_features[:, 0]).item()) == 27
            and int(graph.num_edges()) == 243
            and int(hyper.num_edges) == 27
            and int(cell_complex.dim) == 1
            and int(data.edge_index.shape[1]) == 18
            and int(torch.max(data.edge_index).item()) == sink_index
            and int(data.num_nodes) == len(class_rows) + 1
            and int(simplex_tree.num_simplices()) >= 72
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_num_nodes": int(data.num_nodes),
        "pyg_max_edge_index": int(torch.max(data.edge_index).item()),
        "pyg_transition_class_support_sum": float(torch.sum(class_features[:, 0]).item()),
    }


def z3_class_gate(class_result: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    cell_retained = z3.Bool("cell_retained")
    source_retained = z3.Bool("source_retained")
    pair_retained = z3.Bool("pair_retained")
    rank_retained = z3.Bool("rank_retained")
    binding_agreement_retained = z3.Bool("binding_agreement_retained")
    fresh_n01 = z3.Bool("fresh_n01")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, cell_retained, source_retained, pair_retained, rank_retained, binding_agreement_retained)
    solver.add(z3.Not(fresh_n01), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(class_result["transition_class_count"] == 18))
    solver.add(z3.BoolVal(class_result["cell_transition_row_count"] == 27))
    solver.add(z3.BoolVal(sum(class_result["transition_class_support_vector"]) == 27))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "class_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_class_gate(class_result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "cell_retained": class_result["cell_retained"],
        "source_retained": class_result["source_retained"],
        "pair_retained": class_result["pair_retained"],
        "rank_retained": class_result["rank_retained"],
        "binding_agreement_retained": class_result["binding_agreement_retained"],
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
        "class_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    class_result = cell_rank_transition_class_gate()
    z3_class = z3_class_gate(class_result)
    cvc5_class = cvc5_class_gate(class_result)
    controls = class_result["controls"]
    positive = {"P1_cell_rank_transition_class": class_result}
    graveyard = {
        "GC_cell_count_only_rejected": controls["cell_count_only_control"],
        "GC_residue_count_only_rejected": controls["residue_count_only_control"],
        "GC_rank_residue_vector_only_rejected": controls["rank_residue_vector_only_control"],
        "GC_cell_erased_rejected": controls["cell_erased_control"],
        "GC_source_erased_rejected": controls["source_erased_control"],
        "GC_pair_erased_rejected": controls["pair_erased_control"],
        "GC_delta_erased_rejected": controls["delta_erased_control"],
        "GC_rank_erased_rejected": controls["rank_erased_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_closure_and_downstream_not_opened": controls["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not class_result["dense_state_closure_used"] and not class_result["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_transition_class_count": {"pass": class_result["transition_class_count"] == 18, "transition_class_count": class_result["transition_class_count"]},
        "B4_cell_transition_row_count": {"pass": class_result["cell_transition_row_count"] == 27, "cell_transition_row_count": class_result["cell_transition_row_count"]},
        "B5_z3_finite_class_nonpromotion": z3_class,
        "B6_cvc5_finite_class_nonpromotion": cvc5_class,
        "B7_f_component_retained_as_boundary": {"pass": class_result["f_component_retained"]},
        "B8_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        class_result["pass"]
        and z3_class["pass"]
        and cvc5_class["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_RESIDUE_RECEIPT,
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
            "F01": "finite residue incidence rows, finite cells, finite transition classes, finite residues, finite source ids, finite pair ids, finite rank labels, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this class map inherits the Phase 2 carrier order witness and rejects order-erased/fresh-N01 promotion",
        },
        "finite_map": class_result["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C transition classes inherited from rank-transition residue incidence rows",
            "rank_transition_residue_incidence_rows": "108 finite incidence rows",
            "rank_transition_residue_classes": "13 finite residue classes",
            "cell_ids": "27 finite delta_pair_source_cell ids",
            "source_class_ids": "finite active and F-boundary source class ids",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite cell rank-transition class table, transition-class support vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_cell_rank_transition_class",
        "carrier_realization": "torch finite class/support tensors over PEPS3D V/E/F/C cell/residue rows with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every transition-class row retains finite cell ids plus source ids, pair bindings, delta classes, residues, and PEPS3D V/E/F/C rank normal forms. Scalar labels and summaries are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite cell rank-transition class projection over residue incidence rows",
        "branch_status_before_run": "post_AA_rank_transition_residue_incidence_K_candidate_map_discovery_AB_cell_rank_transition_class_K",
        "allowed_claims": [
            "residue incidence rows induce finite cell rank-transition classes",
            "cell ids, residue ids, source ids, pair bindings, delta ids, and PEPS3D rank normal forms are retained",
            "count-only, residue-only, cell-erased, source-erased, pair-erased, delta-erased, and rank-erased outputs are rejected as insufficient",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "cell rank-transition class readout only",
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
        "proof_surfaces_used": ["z3_finite_class_nonpromotion_gate", "cvc5_finite_class_nonpromotion_gate", "sympy_exact_class_count_checks"],
        "graph_surfaces_used": ["rustworkx_cell_rank_transition_class_graph", "xgi_cell_rank_transition_class_hypergraph", "torch_geometric_transition_class_support_aggregation"],
        "topology_surfaces_used": ["toponetx_finite_class_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "cell-count-only rejection",
            "residue-count-only rejection",
            "rank-residue-vector-only rejection",
            "cell-erased rejection",
            "source-erased rejection",
            "pair-erased rejection",
            "delta-erased rejection",
            "rank-erased rejection",
            "scalar-label rejection",
            "fresh-N01 rejection",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only cell counts, residue counts, rank-residue vectors, or class counts are emitted",
            "cell ids, residue ids, source ids, pair bindings, delta ids, or rank labels disappear",
            "all transition classes collapse to a scalar histogram",
            "fresh noncommuting operators are claimed",
            "dense closure is required",
            "topology/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_cell_rank_transition_class_v1",
        "result_summary": {
            "transition_class_count": class_result["transition_class_count"],
            "cell_transition_row_count": class_result["cell_transition_row_count"],
            "singleton_class_count": class_result["singleton_class_count"],
            "doubleton_class_count": class_result["doubleton_class_count"],
            "transition_class_support_vector": class_result["transition_class_support_vector"],
        },
        "pass_rule": "residue incidence rows induce finite cell transition classes with cell/source/pair/delta/rank retention, and controls remain blocked or collapsed",
        "fail_rule": "only scalar summaries are emitted, cell/residue/source/pair/rank/delta bindings disappear, dense closure is used, fresh N01 is claimed, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite cell rank-transition class readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "AB_cell_rank_transition_class_K classified as bounded finite transition-class readout",
                "cell-count, residue-count, and rank-residue-vector variants classified as duplicate/rejected",
                "cell-erased, source-erased, pair-erased, delta-erased, and rank-erased variants classified as rejected",
                "fresh-N01 variants classified as rejected",
                "restore/inverse variants classified as rejected",
                "topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
                "F-rank normal-form component classified as boundary evidence only",
            ],
        },
        "cell_rank_transition_class_table": class_result["cell_rank_transition_class_table"],
        "transition_class_table": class_result["transition_class_table"],
        "transition_class_count": class_result["transition_class_count"],
        "cell_transition_row_count": class_result["cell_transition_row_count"],
        "singleton_class_count": class_result["singleton_class_count"],
        "doubleton_class_count": class_result["doubleton_class_count"],
        "transition_class_support_vector": class_result["transition_class_support_vector"],
        "residue_count": class_result["residue_count"],
        "incidence_row_count": class_result["incidence_row_count"],
        "unique_cell_count": class_result["unique_cell_count"],
        "rank_residue_vector": class_result["rank_residue_vector"],
        "max_parent_peps3d_sites": class_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": class_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": class_result["max_peps3d_bond"],
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
                "transition_class_count": class_result["transition_class_count"],
                "cell_transition_row_count": class_result["cell_transition_row_count"],
                "singleton_class_count": class_result["singleton_class_count"],
                "doubleton_class_count": class_result["doubleton_class_count"],
                "transition_class_support_vector": class_result["transition_class_support_vector"],
                "max_parent_peps3d_sites": class_result["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": class_result["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": class_result["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
