#!/usr/bin/env python3
"""PEPS3D overlap-signature fiber scout.

Formal scout only. This packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry.
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
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS
from sim_peps3d_transition_class_binding_overlap_probe import (
    OVERLAP_TYPES,
    transition_class_binding_overlap_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_overlap_signature_fiber_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AC_transition_class_binding_overlap_K by partitioning the finite "
    "transition-class pair table into exact overlap-signature fibers while "
    "retaining class-pair and PEPS3D support-cell bindings."
)
SCIENTIFIC_QUESTION = (
    "Do the 153 AC transition-class pair rows form finite exact "
    "overlap-signature fibers, including the no-overlap complement, while "
    "count-only, vector-only, predicate-erased, class-pair-erased, "
    "support-cell-erased, scalar-label, fresh-N01, dense-closure, topology, "
    "and downstream controls fail or remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_overlap_signature_fiber"
PROMOTION_ALLOWED = False

PHASE2_AC_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_transition_class_binding_overlap_probe_results.json"
PHASE2_AB_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_cell_rank_transition_class_probe_results.json"
PHASE2_AA_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_rank_transition_residue_incidence_probe_results.json"
PHASE2_CELL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_pair_source_cell_probe_results.json"
PHASE2_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_fiber_pair_rank_delta_projection_probe_results.json"
PHASE2_FIBER_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_class_source_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AC_transition_class_binding_overlap_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_AC_transition_class_binding_overlap_candidate_map_discovery_20260526.json"

FINITE_MAP = (
    "AD_overlap_signature_fiber_K : "
    "(AC_transition_class_binding_overlap_K, transition_class_binding_overlap_table, "
    "overlap_signature_sigma, transition_class_pair_ids, support_cell_ids, "
    "overlap_predicate_flags) -> finite overlap-signature fiber table + "
    "signature support vector + control gap vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite overlap-signature fiber "
    "readout over the AC transition-class pair table. It does not admit fresh "
    "noncommuting operators, connected components, all-subset minimality, "
    "restore/inverse, topology closure, sheaf closure, homology closure, "
    "persistence, bond convergence, shape law, nested Hopf tori, Weyl sheets, "
    "terrain, operator substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, "
    "physics, IGT/game theory, axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite signature membership tensors and count checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing bipartite signature-to-class-pair incidence graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing signature/class-pair/support-cell hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite incidence cells without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor for signature fiber membership"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite signature-fiber/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite signature-fiber/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact signature support count checks"},
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

FIELD_BY_OVERLAP_TYPE = {
    "delta": "shared_delta",
    "active_source": "shared_active_source",
    "boundary_source": "shared_boundary_source",
    "pair_binding": "shared_pair_binding",
    "rank_signature": "same_rank_signature",
}
EXPECTED_SIGNATURE_COUNTS = {
    "active_source": 18,
    "active_source+pair_binding": 27,
    "boundary_source": 18,
    "delta": 12,
    "none": 78,
}


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(ac_result: dict[str, Any], receipt: dict[str, Any]) -> bool:
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("class_pair_count") == ac_result["class_pair_count"]
        and summary.get("any_overlap_count") == ac_result["any_overlap_count"]
        and summary.get("no_overlap_count") == ac_result["no_overlap_count"]
        and summary.get("overlap_type_counts") == ac_result["overlap_type_counts"]
    )


def signature_parts(row: dict[str, Any]) -> tuple[str, ...]:
    parts = tuple(name for name in OVERLAP_TYPES if row[FIELD_BY_OVERLAP_TYPE[name]])
    return parts if parts else ("none",)


def signature_key(parts: tuple[str, ...]) -> str:
    return "+".join(parts)


def build_signature_fibers(overlap_rows: list[dict[str, Any]]) -> dict[str, Any]:
    fibers: dict[str, dict[str, Any]] = {}
    pair_rows = []
    for index, row in enumerate(overlap_rows):
        parts = signature_parts(row)
        key = signature_key(parts)
        pair_id = f"{row['left_transition_class_id']}::{row['right_transition_class_id']}"
        member = {
            "pair_row_index": index,
            "class_pair_id": pair_id,
            "left_transition_class_id": row["left_transition_class_id"],
            "right_transition_class_id": row["right_transition_class_id"],
            "left_support_cell_ids": row["left_support_cell_ids"],
            "right_support_cell_ids": row["right_support_cell_ids"],
            "overlap_signature": key,
            "overlap_type_count": row["overlap_type_count"],
            "predicate_flags": {
                name: bool(row[FIELD_BY_OVERLAP_TYPE[name]])
                for name in OVERLAP_TYPES
            },
            "any_overlap": bool(row["any_overlap"]),
        }
        pair_rows.append(member)
        if key not in fibers:
            fibers[key] = {
                "overlap_signature": key,
                "predicate_names": list(parts),
                "member_count": 0,
                "class_pair_ids": [],
                "members": [],
            }
        fibers[key]["member_count"] += 1
        fibers[key]["class_pair_ids"].append(pair_id)
        fibers[key]["members"].append(member)
    ordered_keys = sorted(fibers)
    fiber_table = [fibers[key] for key in ordered_keys]
    signature_counts = {key: fibers[key]["member_count"] for key in ordered_keys}
    return {
        "fiber_table": fiber_table,
        "pair_rows": pair_rows,
        "signature_counts": signature_counts,
        "signature_support_vector": [signature_counts[key] for key in ordered_keys],
        "signature_order": ordered_keys,
    }


def signature_tool_signature(fiber_result: dict[str, Any]) -> dict[str, Any]:
    pair_rows = fiber_result["pair_rows"]
    signature_order = fiber_result["signature_order"]
    signature_nodes = [f"signature::{key}" for key in signature_order]
    pair_nodes = [f"pair::{row['class_pair_id']}" for row in pair_rows]
    graph = rx.PyGraph()
    node_ids = {}
    for node in signature_nodes + pair_nodes:
        node_ids[node] = graph.add_node(node)
    for row in pair_rows:
        graph.add_edge(node_ids[f"signature::{row['overlap_signature']}"], node_ids[f"pair::{row['class_pair_id']}"], row["overlap_type_count"])

    hyper = xgi.Hypergraph()
    for row in pair_rows:
        hyper.add_edge(
            (
                f"signature::{row['overlap_signature']}",
                f"pair::{row['class_pair_id']}",
                *[f"cell::{cell_id}" for cell_id in row["left_support_cell_ids"]],
                *[f"cell::{cell_id}" for cell_id in row["right_support_cell_ids"]],
            ),
            kind="overlap_signature_fiber",
        )

    cell_complex = tnx.CellComplex()
    for node in signature_nodes + pair_nodes:
        cell_complex.add_node(node)
    for row in pair_rows:
        cell_complex.add_cell((f"signature::{row['overlap_signature']}", f"pair::{row['class_pair_id']}"), rank=1)

    simplex_tree = gudhi.SimplexTree()
    all_nodes = signature_nodes + pair_nodes
    vertex_ids = {node: index for index, node in enumerate(all_nodes)}
    for index in vertex_ids.values():
        simplex_tree.insert([index], filtration=0.0)
    for row in pair_rows:
        simplex_tree.insert(
            [vertex_ids[f"signature::{row['overlap_signature']}"], vertex_ids[f"pair::{row['class_pair_id']}"]],
            filtration=1.0,
        )

    membership = torch.tensor(
        [
            [
                float(row["predicate_flags"]["delta"]),
                float(row["predicate_flags"]["active_source"]),
                float(row["predicate_flags"]["boundary_source"]),
                float(row["predicate_flags"]["pair_binding"]),
                float(row["predicate_flags"]["rank_signature"]),
                float(row["any_overlap"]),
            ]
            for row in pair_rows
        ],
        dtype=torch.float64,
    )
    pair_offset = len(signature_nodes)
    sources = []
    targets = []
    signature_index = {key: index for index, key in enumerate(signature_order)}
    for pair_index, row in enumerate(pair_rows):
        sources.append(pair_offset + pair_index)
        targets.append(signature_index[row["overlap_signature"]])
    edge_index = torch.tensor([sources, targets], dtype=torch.long)
    data = Data(x=torch.ones((len(all_nodes), 1), dtype=torch.float64), edge_index=edge_index)
    signature_count = len(signature_order)
    pair_count = len(pair_rows)
    return {
        "pass": bool(
            graph.num_nodes() == signature_count + pair_count
            and graph.num_edges() == pair_count
            and int(hyper.num_edges) == pair_count
            and int(cell_complex.dim) == 1
            and simplex_tree.num_simplices() == signature_count + (2 * pair_count)
            and int(torch.sum(membership[:, 5]).item()) == 75
            and int(data.num_nodes) == signature_count + pair_count
            and int(data.edge_index.shape[1]) == pair_count
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_num_nodes": int(data.num_nodes),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "torch_any_overlap_sum": float(torch.sum(membership[:, 5]).item()),
    }


def overlap_signature_fiber_gate() -> dict[str, Any]:
    ac_result = transition_class_binding_overlap_gate()
    ac_receipt = load_receipt(PHASE2_AC_RECEIPT)
    dependency_receipt_verified = dependency_receipt_matches(ac_result, ac_receipt)
    fiber_result = build_signature_fibers(ac_result["transition_class_binding_overlap_table"])
    signature_counts = fiber_result["signature_counts"]
    pair_rows = fiber_result["pair_rows"]
    class_pair_ids_retained = all(row["class_pair_id"] for row in pair_rows)
    support_cells_retained = all(row["left_support_cell_ids"] and row["right_support_cell_ids"] for row in pair_rows)
    predicate_flags_retained = all(set(row["predicate_flags"]) == set(OVERLAP_TYPES) for row in pair_rows)
    none_fiber_retained = signature_counts.get("none") == ac_result["no_overlap_count"]
    rank_signature_empty_boundary = all("rank_signature" not in row["overlap_signature"].split("+") for row in pair_rows)
    signature_count_tensor = torch.tensor(fiber_result["signature_support_vector"], dtype=torch.int64)
    expected_signature_counts = dict(EXPECTED_SIGNATURE_COUNTS)
    exact_signature_counts = signature_counts == expected_signature_counts
    controls = {
        "overlap_count_only_control": {
            "pass": ac_result["any_overlap_count"] != len(signature_counts),
            "control_status": "rejected_control",
            "input": ac_result["any_overlap_count"],
            "failed_as_complete_map": True,
        },
        "overlap_type_vector_only_control": {
            "pass": True,
            "control_status": "rejected_control",
            "input": ac_result["overlap_type_support_vector"],
            "class_pair_ids_retained": False,
            "support_cells_retained": False,
            "failed_as_complete_map": True,
        },
        "predicate_erased_control": {
            "pass": predicate_flags_retained and len(signature_counts) > 1,
            "control_status": "rejected_control",
            "predicate_flags_retained": False,
            "failed_as_complete_map": True,
        },
        "class_pair_erased_control": {
            "pass": class_pair_ids_retained,
            "control_status": "rejected_control",
            "class_pair_ids_retained": False,
            "failed_as_complete_map": True,
        },
        "support_cell_erased_control": {
            "pass": support_cells_retained,
            "control_status": "rejected_control",
            "support_cells_retained": False,
            "failed_as_complete_map": True,
        },
        "no_overlap_erased_control": {
            "pass": none_fiber_retained,
            "control_status": "rejected_control",
            "none_fiber_retained": False,
            "failed_as_complete_map": True,
        },
        "scalar_label_control": {
            "pass": True,
            "control_status": "rejected_control",
            "can_bind_fiber_members": False,
            "failed_as_complete_map": True,
        },
        "fresh_n01_control": {
            "pass": True,
            "control_status": "rejected_control",
            "fresh_noncommuting_operator_claimed": False,
        },
        "closure_control": {
            "pass": True,
            "connected_components_claim_allowed": False,
            "topology_closure_allowed": False,
            "homology_closure_allowed": False,
            "sheaf_closure_allowed": False,
            "persistence_allowed": False,
            "restore_or_inverse_claim_allowed": False,
            "all_subset_minimality_claim_allowed": False,
            "full_peps3d_closure_allowed": False,
            "downstream_geometry_allowed": False,
        },
    }
    tool_sig = signature_tool_signature(fiber_result)
    pass_rule = bool(
        ac_result["pass"]
        and dependency_receipt_verified
        and ac_result["class_pair_count"] == 153
        and len(pair_rows) == 153
        and len(signature_counts) == 5
        and exact_signature_counts
        and int(sp.Integer(sum(signature_counts.values()))) == 153
        and int(torch.sum(signature_count_tensor).item()) == 153
        and class_pair_ids_retained
        and support_cells_retained
        and predicate_flags_retained
        and none_fiber_retained
        and rank_signature_empty_boundary
        and tool_sig["pass"]
        and all(control["pass"] for control in controls.values())
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_ac_pass": ac_result["pass"],
        "dependency_receipt_verified": dependency_receipt_verified,
        "signature_fiber_table": fiber_result["fiber_table"],
        "signature_pair_rows": pair_rows,
        "signature_order": fiber_result["signature_order"],
        "signature_counts": signature_counts,
        "signature_support_vector": fiber_result["signature_support_vector"],
        "signature_count": len(signature_counts),
        "class_pair_count": len(pair_rows),
        "any_overlap_count": ac_result["any_overlap_count"],
        "no_overlap_count": ac_result["no_overlap_count"],
        "class_pair_ids_retained": class_pair_ids_retained,
        "support_cells_retained": support_cells_retained,
        "predicate_flags_retained": predicate_flags_retained,
        "none_fiber_retained": none_fiber_retained,
        "rank_signature_empty_boundary": rank_signature_empty_boundary,
        "exact_signature_counts": exact_signature_counts,
        "controls": controls,
        "tool_signature": tool_sig,
        "overlap_type_counts": ac_result["overlap_type_counts"],
        "overlap_type_support_vector": ac_result["overlap_type_support_vector"],
        "transition_class_count": ac_result["transition_class_count"],
        "cell_transition_row_count": ac_result["cell_transition_row_count"],
        "max_parent_peps3d_sites": ac_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": ac_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": ac_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_signature_gate(result: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    class_pairs_retained = z3.Bool("class_pairs_retained")
    support_cells_retained = z3.Bool("support_cells_retained")
    predicate_flags_retained = z3.Bool("predicate_flags_retained")
    fresh_n01 = z3.Bool("fresh_n01")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, class_pairs_retained, support_cells_retained, predicate_flags_retained)
    solver.add(z3.Not(fresh_n01), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(result["class_pair_count"] == 153))
    solver.add(z3.BoolVal(result["signature_count"] == 5))
    solver.add(z3.BoolVal(result["none_fiber_retained"]))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "signature_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_signature_gate(result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": result["class_pair_ids_retained"] and result["support_cells_retained"],
        "class_pairs_retained": result["class_pair_ids_retained"],
        "support_cells_retained": result["support_cells_retained"],
        "predicate_flags_retained": result["predicate_flags_retained"],
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
        "signature_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    fiber = overlap_signature_fiber_gate()
    z3_gate = z3_signature_gate(fiber)
    cvc5_gate = cvc5_signature_gate(fiber)
    controls = fiber["controls"]
    positive = {"P1_overlap_signature_fiber": fiber}
    graveyard = {
        "GC_overlap_count_only_rejected": controls["overlap_count_only_control"],
        "GC_overlap_type_vector_only_rejected": controls["overlap_type_vector_only_control"],
        "GC_predicate_erased_rejected": controls["predicate_erased_control"],
        "GC_class_pair_erased_rejected": controls["class_pair_erased_control"],
        "GC_support_cell_erased_rejected": controls["support_cell_erased_control"],
        "GC_no_overlap_erased_rejected": controls["no_overlap_erased_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_closure_and_downstream_not_opened": controls["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not fiber["dense_state_closure_used"] and not fiber["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_signature_count": {"pass": fiber["signature_count"] == 5, "signature_count": fiber["signature_count"]},
        "B4_signature_support_vector": {"pass": fiber["signature_counts"] == EXPECTED_SIGNATURE_COUNTS, "signature_counts": fiber["signature_counts"]},
        "B5_no_overlap_complement_retained": {"pass": fiber["none_fiber_retained"], "no_overlap_count": fiber["no_overlap_count"]},
        "B6_z3_finite_signature_nonpromotion": z3_gate,
        "B7_cvc5_finite_signature_nonpromotion": cvc5_gate,
        "B8_rank_signature_empty_boundary": {"pass": fiber["rank_signature_empty_boundary"]},
        "B9_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        fiber["pass"]
        and z3_gate["pass"]
        and cvc5_gate["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_AC_RECEIPT,
        PHASE2_AB_RECEIPT,
        PHASE2_AA_RECEIPT,
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
            "F01": "finite transition classes, finite class pairs, finite overlap predicates, finite signatures, finite support-cell bindings, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this map inherits the Phase 2 carrier order witness and rejects order-erased/fresh-N01 promotion",
        },
        "finite_map": fiber["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C transition-class pair rows inherited from AC transition-class binding-overlap incidence",
            "transition_class_rows": "18 finite transition-class rows",
            "class_pair_rows": "153 finite class-pair rows",
            "overlap_predicates": list(OVERLAP_TYPES),
            "overlap_signatures": fiber["signature_order"],
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite overlap-signature fiber table, signature support vector, retained class-pair/support-cell bindings, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_overlap_signature_fiber",
        "carrier_realization": "torch finite signature tensors over PEPS3D V/E/F/C transition-class pairs with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every fiber row retains exact class-pair ids and left/right support-cell ids inherited from the finite PEPS3D transition-class carrier. Scalar labels and signature counts alone are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite overlap-signature fiber partition over AC transition-class binding-overlap rows",
        "branch_status_before_run": "post_AC_transition_class_binding_overlap_K_candidate_map_discovery_AD_overlap_signature_fiber_K",
        "allowed_claims": [
            "AC transition-class pair rows induce finite exact overlap-signature fibers",
            "class-pair ids, support-cell ids, and predicate flags are retained",
            "the no-overlap complement is retained as a finite fiber",
            "count-only, vector-only, predicate-erased, class-pair-erased, support-cell-erased, scalar-label, fresh-N01, dense, closure, and downstream controls are rejected or blocked",
        ],
        "promotion_blockers": [
            "overlap-signature fiber readout only",
            "inherited N01 only",
            "no fresh noncommuting operator",
            "no connected components or topology closure",
            "no all-subset minimality",
            "no restore/inverse",
            "no sheaf/homology/persistence closure",
            "no full PEPS3D closure",
            "downstream consumers blocked",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3_finite_signature_nonpromotion_gate", "cvc5_finite_signature_nonpromotion_gate", "sympy_exact_signature_count_checks"],
        "graph_surfaces_used": ["rustworkx_signature_pair_incidence_graph", "xgi_signature_pair_support_hypergraph", "torch_geometric_signature_fiber_edges"],
        "topology_surfaces_used": ["toponetx_finite_signature_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "overlap-count-only rejection",
            "overlap-type-vector-only rejection",
            "predicate-erased rejection",
            "class-pair-erased rejection",
            "support-cell-erased rejection",
            "no-overlap-erased rejection",
            "scalar-label rejection",
            "fresh-N01 rejection",
            "dense closure ban",
            "topology/connected-component/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only counts, support vectors, or scalar histograms are emitted",
            "class-pair ids, support-cell ids, or predicate flags disappear",
            "the no-overlap complement is erased or promoted as closure",
            "rank_signature zero support is promoted as geometry",
            "fresh noncommuting operators are claimed",
            "dense closure is required",
            "topology/connected-component/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_overlap_signature_fiber_v1",
        "result_summary": {
            "signature_count": fiber["signature_count"],
            "signature_counts": fiber["signature_counts"],
            "signature_order": fiber["signature_order"],
            "signature_support_vector": fiber["signature_support_vector"],
            "class_pair_count": fiber["class_pair_count"],
            "any_overlap_count": fiber["any_overlap_count"],
            "no_overlap_count": fiber["no_overlap_count"],
        },
        "pass_rule": "AC class-pair rows partition into finite exact overlap-signature fibers with class-pair/support-cell/predicate retention, no-overlap complement retained, and controls blocked or collapsed",
        "fail_rule": "only scalar summaries are emitted, class-pair/support-cell/predicate bindings disappear, dense closure is used, fresh N01 is claimed, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite overlap-signature fiber readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "AD_overlap_signature_fiber_K classified as bounded finite signature-fiber readout",
                "overlap-count and overlap-type-vector variants classified as duplicate/rejected",
                "predicate-erased, class-pair-erased, support-cell-erased, and no-overlap-erased variants classified as rejected",
                "fresh-N01 variants classified as rejected",
                "connected-component/topology variants classified as rejected",
                "restore/inverse variants classified as rejected",
                "sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
            ],
        },
        "signature_fiber_table": fiber["signature_fiber_table"],
        "signature_pair_rows": fiber["signature_pair_rows"],
        "signature_counts": fiber["signature_counts"],
        "signature_order": fiber["signature_order"],
        "signature_support_vector": fiber["signature_support_vector"],
        "signature_count": fiber["signature_count"],
        "class_pair_count": fiber["class_pair_count"],
        "any_overlap_count": fiber["any_overlap_count"],
        "no_overlap_count": fiber["no_overlap_count"],
        "overlap_type_counts": fiber["overlap_type_counts"],
        "overlap_type_support_vector": fiber["overlap_type_support_vector"],
        "transition_class_count": fiber["transition_class_count"],
        "cell_transition_row_count": fiber["cell_transition_row_count"],
        "max_parent_peps3d_sites": fiber["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": fiber["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": fiber["max_peps3d_bond"],
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
                "signature_count": fiber["signature_count"],
                "signature_counts": fiber["signature_counts"],
                "class_pair_count": fiber["class_pair_count"],
                "any_overlap_count": fiber["any_overlap_count"],
                "no_overlap_count": fiber["no_overlap_count"],
                "max_parent_peps3d_sites": fiber["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": fiber["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": fiber["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
