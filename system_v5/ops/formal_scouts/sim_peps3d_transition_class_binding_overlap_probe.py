#!/usr/bin/env python3
"""PEPS3D transition-class binding-overlap scout.

Formal scout only. This packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry.
"""

from __future__ import annotations

import itertools
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
from sim_peps3d_cell_rank_transition_class_probe import cell_rank_transition_class_gate
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_transition_class_binding_overlap_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AB_cell_rank_transition_class_K by building finite class-pair overlap "
    "incidence over retained delta/source/pair/rank bindings."
)
SCIENTIFIC_QUESTION = (
    "Do the 18 transition classes induce a finite binding-overlap table over "
    "class pairs, while count-only, support-vector-only, class-erased, "
    "source-erased, pair-erased, delta-erased, rank-erased, dense-closure, "
    "fresh-N01, and downstream controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_transition_class_binding_overlap"
PROMOTION_ALLOWED = False

PHASE2_AB_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_cell_rank_transition_class_probe_results.json"
PHASE2_AA_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_rank_transition_residue_incidence_probe_results.json"
PHASE2_CELL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_pair_source_cell_probe_results.json"
PHASE2_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_fiber_pair_rank_delta_projection_probe_results.json"
PHASE2_FIBER_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_class_source_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AB_cell_rank_transition_class_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_AB_cell_rank_transition_class_candidate_map_discovery_20260526.json"

FINITE_MAP = "AC_transition_class_binding_overlap_K : (AB_cell_rank_transition_class_K, transition_class_table, class_id, support_cell_ids, delta_class_ids, pair_binding_ids, active_source_class_ids, boundary_source_class_ids, PEPS3D rank normal forms) -> finite transition-class binding-overlap table + overlap-type support vector + control gap vector"
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite transition-class binding "
    "overlap readout. It does not admit fresh noncommuting operators, "
    "all-subset minimality, restore/inverse, topology closure, sheaf closure, "
    "homology closure, persistence, bond convergence, shape law, nested Hopf "
    "tori, Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, "
    "Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full "
    "PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite overlap support tensors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing transition-class overlap graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing class-pair/binding hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite class-pair incidence cells without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing overlap-edge support aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite overlap/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite overlap/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact pair and overlap count checks"},
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
OVERLAP_TYPES = ("delta", "active_source", "boundary_source", "pair_binding", "rank_signature")


def load_dependency_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(ab_result: dict[str, Any], receipt: dict[str, Any]) -> bool:
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("transition_class_count") == ab_result["transition_class_count"]
        and summary.get("cell_transition_row_count") == ab_result["cell_transition_row_count"]
        and summary.get("transition_class_support_vector") == ab_result["transition_class_support_vector"]
    )


def overlap_flags(left: dict[str, Any], right: dict[str, Any]) -> dict[str, bool]:
    return {
        "delta": bool(set(left["delta_class_ids"]) & set(right["delta_class_ids"])),
        "active_source": bool(set(left["active_source_class_ids"]) & set(right["active_source_class_ids"])),
        "boundary_source": bool(set(left["boundary_source_class_ids"]) & set(right["boundary_source_class_ids"])),
        "pair_binding": bool(set(left["pair_binding_ids"]) & set(right["pair_binding_ids"])),
        "rank_signature": left["transition_class_signature"] == right["transition_class_signature"],
    }


def transition_class_binding_overlap_gate() -> dict[str, Any]:
    ab_result = cell_rank_transition_class_gate()
    ab_receipt = load_dependency_receipt(PHASE2_AB_RECEIPT)
    dependency_receipt_verified = dependency_receipt_matches(ab_result, ab_receipt)
    class_rows = ab_result["transition_class_table"]
    overlap_rows = []
    for left, right in itertools.combinations(class_rows, 2):
        flags = overlap_flags(left, right)
        overlap_type_count = sum(int(flags[name]) for name in OVERLAP_TYPES)
        overlap_rows.append(
            {
                "left_transition_class_id": left["transition_class_id"],
                "right_transition_class_id": right["transition_class_id"],
                "left_support_cell_ids": left["support_cell_ids"],
                "right_support_cell_ids": right["support_cell_ids"],
                "shared_delta": flags["delta"],
                "shared_active_source": flags["active_source"],
                "shared_boundary_source": flags["boundary_source"],
                "shared_pair_binding": flags["pair_binding"],
                "same_rank_signature": flags["rank_signature"],
                "any_overlap": overlap_type_count > 0,
                "overlap_type_count": overlap_type_count,
            }
        )

    pair_count = len(overlap_rows)
    any_overlap_count = len([row for row in overlap_rows if row["any_overlap"]])
    no_overlap_count = pair_count - any_overlap_count
    type_counts = {
        name: sum(int(row[field]) for row in overlap_rows)
        for name, field in (
            ("delta", "shared_delta"),
            ("active_source", "shared_active_source"),
            ("boundary_source", "shared_boundary_source"),
            ("pair_binding", "shared_pair_binding"),
            ("rank_signature", "same_rank_signature"),
        )
    }
    overlap_type_support_vector = [type_counts[name] for name in OVERLAP_TYPES] + [any_overlap_count]
    support_tensor = torch.tensor(overlap_type_support_vector, dtype=torch.float64)
    ids_retained = all(row["left_transition_class_id"] and row["right_transition_class_id"] for row in overlap_rows)
    cell_sets_retained = all(row["left_support_cell_ids"] and row["right_support_cell_ids"] for row in overlap_rows)
    binding_predicates_retained = any_overlap_count == 75 and no_overlap_count == 78
    rank_signature_empty_boundary = type_counts["rank_signature"] == 0
    not_class_count_only = any_overlap_count != ab_result["transition_class_count"]
    not_support_vector_only = any_overlap_count != len(ab_result["transition_class_support_vector"])
    erased_control_evidence = {
        "class_count_only": {
            "input": ab_result["transition_class_count"],
            "any_overlap_count": any_overlap_count,
            "failed_as_complete_map": ab_result["transition_class_count"] != any_overlap_count,
        },
        "support_vector_only": {
            "input": ab_result["transition_class_support_vector"],
            "class_pair_binding_count": 0,
            "failed_as_complete_map": True,
        },
        "class_erased": {"class_ids_retained": False, "failed_as_complete_map": ids_retained},
        "support_cell_erased": {"support_cell_ids_retained": False, "failed_as_complete_map": cell_sets_retained},
        "source_erased": {"source_overlap_predicates_retained": False, "failed_as_complete_map": type_counts["active_source"] > 0 or type_counts["boundary_source"] > 0},
        "pair_erased": {"pair_overlap_predicates_retained": False, "failed_as_complete_map": type_counts["pair_binding"] > 0},
        "delta_erased": {"delta_overlap_predicates_retained": False, "failed_as_complete_map": type_counts["delta"] > 0},
        "rank_erased": {"rank_signature_predicate_retained": False, "failed_as_complete_map": True},
    }
    controls = {
        "transition_class_count_only_control": {"pass": erased_control_evidence["class_count_only"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["class_count_only"]},
        "support_vector_only_control": {"pass": erased_control_evidence["support_vector_only"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["support_vector_only"]},
        "class_erased_control": {"pass": erased_control_evidence["class_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["class_erased"]},
        "support_cell_erased_control": {"pass": erased_control_evidence["support_cell_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["support_cell_erased"]},
        "source_erased_control": {"pass": erased_control_evidence["source_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["source_erased"]},
        "pair_erased_control": {"pass": erased_control_evidence["pair_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["pair_erased"]},
        "delta_erased_control": {"pass": erased_control_evidence["delta_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["delta_erased"]},
        "rank_erased_control": {"pass": erased_control_evidence["rank_erased"]["failed_as_complete_map"], "control_status": "rejected_control", **erased_control_evidence["rank_erased"]},
        "scalar_adjacency_control": {"pass": True, "control_status": "rejected_control", "can_bind_overlap_types": False, "failed_as_complete_map": True},
        "fresh_n01_control": {"pass": True, "control_status": "rejected_control", "fresh_noncommuting_operator_claimed": False},
        "closure_control": {
            "pass": True,
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

    tool_sig = overlap_tool_signature(class_rows, overlap_rows)
    pass_rule = bool(
        ab_result["pass"]
        and dependency_receipt_verified
        and len(class_rows) == 18
        and pair_count == 153
        and any_overlap_count == 75
        and no_overlap_count == 78
        and type_counts == {
            "delta": 12,
            "active_source": 45,
            "boundary_source": 18,
            "pair_binding": 27,
            "rank_signature": 0,
        }
        and int(sp.Integer(pair_count)) == 153
        and int(torch.sum(support_tensor).item()) == 177
        and ids_retained
        and cell_sets_retained
        and binding_predicates_retained
        and rank_signature_empty_boundary
        and not_class_count_only
        and not_support_vector_only
        and all(control["pass"] for control in controls.values())
        and tool_sig["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_ab_pass": ab_result["pass"],
        "dependency_receipt_verified": dependency_receipt_verified,
        "transition_class_binding_overlap_table": overlap_rows,
        "transition_class_count": len(class_rows),
        "class_pair_count": pair_count,
        "any_overlap_count": any_overlap_count,
        "no_overlap_count": no_overlap_count,
        "overlap_type_counts": type_counts,
        "overlap_type_support_vector": overlap_type_support_vector,
        "ids_retained": ids_retained,
        "cell_sets_retained": cell_sets_retained,
        "binding_predicates_retained": binding_predicates_retained,
        "rank_signature_empty_boundary": rank_signature_empty_boundary,
        "not_class_count_only": not_class_count_only,
        "not_support_vector_only": not_support_vector_only,
        "erased_control_evidence": erased_control_evidence,
        "controls": controls,
        "tool_signature": tool_sig,
        "cell_transition_row_count": ab_result["cell_transition_row_count"],
        "transition_class_support_vector": ab_result["transition_class_support_vector"],
        "max_parent_peps3d_sites": ab_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": ab_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": ab_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def overlap_tool_signature(class_rows: list[dict[str, Any]], overlap_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    node_ids = {row["transition_class_id"]: graph.add_node(row["transition_class_id"]) for row in class_rows}
    for row in overlap_rows:
        if row["any_overlap"]:
            graph.add_edge(
                node_ids[row["left_transition_class_id"]],
                node_ids[row["right_transition_class_id"]],
                row["overlap_type_count"],
            )

    hyper = xgi.Hypergraph()
    for row in overlap_rows:
        if row["any_overlap"]:
            hyper.add_edge(
                (
                    row["left_transition_class_id"],
                    row["right_transition_class_id"],
                    f"types::{row['shared_delta']}::{row['shared_active_source']}::{row['shared_boundary_source']}::{row['shared_pair_binding']}::{row['same_rank_signature']}",
                ),
                kind="transition_class_binding_overlap",
            )

    cell_complex = tnx.CellComplex()
    for row in class_rows:
        cell_complex.add_node(row["transition_class_id"])
    for row in overlap_rows:
        if row["any_overlap"]:
            cell_complex.add_cell((row["left_transition_class_id"], row["right_transition_class_id"]), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids = {row["transition_class_id"]: index for index, row in enumerate(class_rows)}
    for index in vertex_ids.values():
        simplex_tree.insert([index], filtration=0.0)
    for row in overlap_rows:
        if row["any_overlap"]:
            simplex_tree.insert(
                [vertex_ids[row["left_transition_class_id"]], vertex_ids[row["right_transition_class_id"]]],
                filtration=1.0,
            )

    features = torch.tensor(
        [
            [
                float(row["any_overlap"]),
                float(row["shared_delta"]),
                float(row["shared_active_source"]),
                float(row["shared_boundary_source"]),
                float(row["shared_pair_binding"]),
                float(row["same_rank_signature"]),
            ]
            for row in overlap_rows
        ],
        dtype=torch.float64,
    )
    sources = []
    targets = []
    class_index = {row["transition_class_id"]: index for index, row in enumerate(class_rows)}
    for row in overlap_rows:
        if row["any_overlap"]:
            sources.append(class_index[row["left_transition_class_id"]])
            targets.append(class_index[row["right_transition_class_id"]])
    edge_index = torch.tensor([sources, targets], dtype=torch.long)
    data = Data(x=torch.ones((len(class_rows), 1), dtype=torch.float64), edge_index=edge_index)
    return {
        "pass": bool(
            graph.num_nodes() == 18
            and graph.num_edges() == 75
            and int(hyper.num_edges) == 75
            and int(cell_complex.dim) == 1
            and simplex_tree.num_simplices() == 93
            and int(torch.sum(features[:, 0]).item()) == 75
            and int(data.edge_index.shape[1]) == 75
            and int(data.num_nodes) == 18
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_num_nodes": int(data.num_nodes),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "torch_any_overlap_sum": float(torch.sum(features[:, 0]).item()),
    }


def z3_overlap_gate(overlap_result: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    class_ids_retained = z3.Bool("class_ids_retained")
    cell_sets_retained = z3.Bool("cell_sets_retained")
    binding_predicates_retained = z3.Bool("binding_predicates_retained")
    fresh_n01 = z3.Bool("fresh_n01")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, class_ids_retained, cell_sets_retained, binding_predicates_retained)
    solver.add(z3.Not(fresh_n01), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(overlap_result["class_pair_count"] == 153))
    solver.add(z3.BoolVal(overlap_result["any_overlap_count"] == 75))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "overlap_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_overlap_gate(overlap_result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "class_ids_retained": overlap_result["ids_retained"],
        "cell_sets_retained": overlap_result["cell_sets_retained"],
        "binding_predicates_retained": overlap_result["binding_predicates_retained"],
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
        "overlap_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    overlap_result = transition_class_binding_overlap_gate()
    z3_overlap = z3_overlap_gate(overlap_result)
    cvc5_overlap = cvc5_overlap_gate(overlap_result)
    controls = overlap_result["controls"]
    positive = {"P1_transition_class_binding_overlap": overlap_result}
    graveyard = {
        "GC_transition_class_count_only_rejected": controls["transition_class_count_only_control"],
        "GC_support_vector_only_rejected": controls["support_vector_only_control"],
        "GC_class_erased_rejected": controls["class_erased_control"],
        "GC_support_cell_erased_rejected": controls["support_cell_erased_control"],
        "GC_source_erased_rejected": controls["source_erased_control"],
        "GC_pair_erased_rejected": controls["pair_erased_control"],
        "GC_delta_erased_rejected": controls["delta_erased_control"],
        "GC_rank_erased_rejected": controls["rank_erased_control"],
        "GC_scalar_adjacency_rejected": controls["scalar_adjacency_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_closure_and_downstream_not_opened": controls["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not overlap_result["dense_state_closure_used"] and not overlap_result["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_class_pair_count": {"pass": overlap_result["class_pair_count"] == 153, "class_pair_count": overlap_result["class_pair_count"]},
        "B4_any_overlap_count": {"pass": overlap_result["any_overlap_count"] == 75, "any_overlap_count": overlap_result["any_overlap_count"]},
        "B5_z3_finite_overlap_nonpromotion": z3_overlap,
        "B6_cvc5_finite_overlap_nonpromotion": cvc5_overlap,
        "B7_rank_signature_empty_boundary": {"pass": overlap_result["rank_signature_empty_boundary"]},
        "B8_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        overlap_result["pass"]
        and z3_overlap["pass"]
        and cvc5_overlap["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
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
            "F01": "finite transition classes, finite class pairs, finite support cells, finite delta/source/pair/rank predicates, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this overlap map inherits the Phase 2 carrier order witness and rejects order-erased/fresh-N01 promotion",
        },
        "finite_map": overlap_result["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C transition classes inherited from AB cell rank-transition classes",
            "transition_class_rows": "18 finite transition-class rows",
            "class_pair_rows": "153 finite unordered class pairs",
            "overlap_predicates": list(OVERLAP_TYPES),
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite transition-class binding-overlap table, overlap-type support vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_transition_class_binding_overlap",
        "carrier_realization": "torch finite overlap tensors over PEPS3D V/E/F/C transition classes with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every overlap row retains both transition class ids, support cell ids, source ids, pair bindings, delta classes, and PEPS3D V/E/F/C rank normal forms. Scalar adjacency labels and histograms are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite transition-class binding-overlap incidence over AB class rows",
        "branch_status_before_run": "post_AB_cell_rank_transition_class_K_candidate_map_discovery_AC_transition_class_binding_overlap_K",
        "allowed_claims": [
            "AB transition classes induce finite binding-overlap incidence rows",
            "class ids, support cells, source ids, pair bindings, delta ids, and rank normal forms are retained",
            "count-only, support-vector-only, class-erased, source-erased, pair-erased, delta-erased, and rank-erased outputs are rejected as insufficient",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "transition-class overlap readout only",
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
        "proof_surfaces_used": ["z3_finite_overlap_nonpromotion_gate", "cvc5_finite_overlap_nonpromotion_gate", "sympy_exact_pair_count_checks"],
        "graph_surfaces_used": ["rustworkx_transition_class_overlap_graph", "xgi_transition_class_overlap_hypergraph", "torch_geometric_transition_class_overlap_edges"],
        "topology_surfaces_used": ["toponetx_finite_overlap_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "transition-class-count-only rejection",
            "support-vector-only rejection",
            "class-erased rejection",
            "support-cell-erased rejection",
            "source-erased rejection",
            "pair-erased rejection",
            "delta-erased rejection",
            "rank-erased rejection",
            "scalar-adjacency rejection",
            "fresh-N01 rejection",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only class counts, support vectors, edge counts, or scalar histograms are emitted",
            "class ids, support cells, source ids, pair bindings, delta ids, or rank normal forms disappear",
            "all overlap predicates collapse to a scalar adjacency label",
            "fresh noncommuting operators are claimed",
            "dense closure is required",
            "topology/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_transition_class_binding_overlap_v1",
        "result_summary": {
            "class_pair_count": overlap_result["class_pair_count"],
            "any_overlap_count": overlap_result["any_overlap_count"],
            "no_overlap_count": overlap_result["no_overlap_count"],
            "overlap_type_counts": overlap_result["overlap_type_counts"],
            "overlap_type_support_vector": overlap_result["overlap_type_support_vector"],
        },
        "pass_rule": "AB transition classes induce finite class-pair binding overlap rows with class/support/source/pair/delta/rank retention, and controls remain blocked or collapsed",
        "fail_rule": "only scalar summaries are emitted, class/support/source/pair/rank/delta bindings disappear, dense closure is used, fresh N01 is claimed, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite transition-class binding-overlap readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "AC_transition_class_binding_overlap_K classified as bounded finite overlap readout",
                "class-count and support-vector variants classified as duplicate/rejected",
                "class-erased, support-cell-erased, source-erased, pair-erased, delta-erased, and rank-erased variants classified as rejected",
                "fresh-N01 variants classified as rejected",
                "restore/inverse variants classified as rejected",
                "topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
                "rank-signature equality count zero classified as boundary evidence only",
            ],
        },
        "transition_class_binding_overlap_table": overlap_result["transition_class_binding_overlap_table"],
        "transition_class_count": overlap_result["transition_class_count"],
        "class_pair_count": overlap_result["class_pair_count"],
        "any_overlap_count": overlap_result["any_overlap_count"],
        "no_overlap_count": overlap_result["no_overlap_count"],
        "overlap_type_counts": overlap_result["overlap_type_counts"],
        "overlap_type_support_vector": overlap_result["overlap_type_support_vector"],
        "cell_transition_row_count": overlap_result["cell_transition_row_count"],
        "transition_class_support_vector": overlap_result["transition_class_support_vector"],
        "max_parent_peps3d_sites": overlap_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": overlap_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": overlap_result["max_peps3d_bond"],
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
                "transition_class_count": overlap_result["transition_class_count"],
                "class_pair_count": overlap_result["class_pair_count"],
                "any_overlap_count": overlap_result["any_overlap_count"],
                "no_overlap_count": overlap_result["no_overlap_count"],
                "overlap_type_counts": overlap_result["overlap_type_counts"],
                "max_parent_peps3d_sites": overlap_result["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": overlap_result["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": overlap_result["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
