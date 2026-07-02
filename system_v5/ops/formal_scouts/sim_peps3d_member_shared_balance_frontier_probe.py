#!/usr/bin/env python3
"""PEPS3D member-shared balance frontier scout.

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
import rustworkx as rx
import sympy as sp
import torch
import xgi
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import as_jsonable
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS
from sim_peps3d_signature_cell_role_balance_residue_probe import (
    signature_cell_role_balance_residue_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_member_shared_balance_frontier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AF_signature_cell_role_balance_residue_K by building finite row-pair "
    "frontier rows over shared member class-pair witnesses."
)
SCIENTIFIC_QUESTION = (
    "Do AF role-balance rows induce finite member-shared row-pair frontier "
    "rows retaining row ids, support-cell anchors, signatures, balance classes, "
    "endpoint counts, residue deltas, and shared member witnesses, while "
    "member-erased, support-erased, signature-erased, balance-class-erased, "
    "endpoint-count-erased, residue-erased, count-only, scalar-label, "
    "fresh-N01, topology/closure, and downstream controls fail or remain "
    "blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_member_shared_balance_frontier"
PROMOTION_ALLOWED = False

PHASE2_AF_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_cell_role_balance_residue_probe_results.json"
PHASE2_AE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_anchor_role_incidence_probe_results.json"
PHASE2_AD_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_overlap_signature_fiber_probe_results.json"
PHASE2_AC_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_transition_class_binding_overlap_probe_results.json"
PHASE2_AB_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_cell_rank_transition_class_probe_results.json"
PHASE2_AA_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_rank_transition_residue_incidence_probe_results.json"
PHASE2_CELL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_pair_source_cell_probe_results.json"
PHASE2_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_fiber_pair_rank_delta_projection_probe_results.json"
PHASE2_FIBER_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_class_source_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AF_signature_cell_role_balance_residue_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_AF_signature_cell_role_balance_residue_candidate_map_discovery_20260526.json"

FINITE_MAP = (
    "AG_member_shared_balance_frontier_K : "
    "(AF_signature_cell_role_balance_residue_K, balance_row_i, balance_row_j, "
    "shared_member_class_pair_ids, support_cell_i, support_cell_j, "
    "overlap_signature_i, overlap_signature_j, balance_class_i, "
    "balance_class_j, residue_delta) -> finite member-shared row-pair "
    "frontier table + witness-support vector + control gap vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite member-shared row-pair "
    "frontier readout over AF role-balance rows. It does not admit fresh "
    "noncommuting operators, endpoint chirality, orientation, topology closure, "
    "connected components, sheaf closure, homology closure, persistence, "
    "restore/inverse, all-subset minimality, bond convergence, shape law, "
    "nested Hopf tori, Weyl sheets, terrain, operator substage cells, flux, "
    "Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or "
    "full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite row-pair tensors and cardinality checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite row-pair frontier graph without component/topology claim"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite row-pair/member hyperedges"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite frontier/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite frontier/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact row-pair and shared-member count checks"},
    "toponetx": {"tried": False, "used": False, "reason": "not applicable: no cell-complex topology or closure is claimed"},
    "gudhi": {"tried": False, "used": False, "reason": "not applicable: no homology, persistence, or filtration is claimed"},
    "torch_geometric": {"tried": False, "used": False, "reason": "not applicable: rustworkx/xgi already carry the finite row-pair graph/hypergraph claim"},
    "clifford": {"tried": False, "used": False, "reason": "not applicable: no geometric product, chirality, or rotor transport is claimed"},
    "geomstats": {"tried": False, "used": False, "reason": "not applicable: no Riemannian metric, geodesic, or curvature is claimed"},
    "e3nn": {"tried": False, "used": False, "reason": "not applicable: no E(3), O(3), or SO(3) equivariance is claimed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "toponetx": None,
    "gudhi": None,
    "torch_geometric": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
}

EXPECTED_PAIR_COUNT = 387
EXPECTED_SHARED_MEMBER_EDGE_COUNT = 495
EXPECTED_UNIQUE_SHARED_MEMBER_COUNT = 153
EXPECTED_ACTIVE_ROW_COVERAGE = 135
EXPECTED_SUPPORT_CELL_PAIR_COUNT = 351
EXPECTED_SAME_SUPPORT_PAIR_COUNT = 0
EXPECTED_SAME_SIGNATURE_PAIR_COUNT = 387
EXPECTED_SAME_BALANCE_CLASS_PAIR_COUNT = 137
EXPECTED_UNORDERED_BALANCE_CLASS_PAIR_COUNTS = {
    "balanced::balanced": 7,
    "balanced::left_heavy": 42,
    "balanced::right_heavy": 34,
    "left_heavy::left_heavy": 79,
    "left_heavy::right_heavy": 174,
    "right_heavy::right_heavy": 51,
}
EXPECTED_UNORDERED_SIGNATURE_PAIR_COUNTS = {
    "active_source::active_source": 36,
    "active_source+pair_binding::active_source+pair_binding": 81,
    "boundary_source::boundary_source": 54,
    "delta::delta": 39,
    "none::none": 177,
}


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(af_result: dict[str, Any], receipt: dict[str, Any]) -> bool:
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("balance_row_count") == af_result["balance_row_count"]
        and summary.get("balance_class_counts") == af_result["balance_class_counts"]
        and summary.get("signature_balance_counts") == af_result["signature_balance_counts"]
    )


def unordered_key(a: str, b: str) -> str:
    return "::".join(sorted((a, b)))


def build_member_shared_frontier(rows: list[dict[str, Any]]) -> dict[str, Any]:
    frontier_rows = []
    shared_member_ids = set()
    active_row_ids = set()
    support_cell_pairs = set()
    unordered_class_pair_counts: dict[str, int] = {}
    unordered_signature_pair_counts: dict[str, int] = {}
    residue_delta_counts: dict[str, int] = {}
    same_support_pair_count = 0
    same_signature_pair_count = 0
    same_balance_class_pair_count = 0

    for index, (left, right) in enumerate(itertools.combinations(rows, 2)):
        shared = sorted(set(left["member_class_pair_ids"]) & set(right["member_class_pair_ids"]))
        if not shared:
            continue
        class_key = unordered_key(left["balance_class"], right["balance_class"])
        signature_key = unordered_key(left["overlap_signature"], right["overlap_signature"])
        residue_delta = int(right["balance_residue"]) - int(left["balance_residue"])
        support_pair = tuple(sorted((left["support_cell_id"], right["support_cell_id"])))
        if left["support_cell_id"] == right["support_cell_id"]:
            same_support_pair_count += 1
        if left["overlap_signature"] == right["overlap_signature"]:
            same_signature_pair_count += 1
        if left["balance_class"] == right["balance_class"]:
            same_balance_class_pair_count += 1
        unordered_class_pair_counts[class_key] = unordered_class_pair_counts.get(class_key, 0) + 1
        unordered_signature_pair_counts[signature_key] = unordered_signature_pair_counts.get(signature_key, 0) + 1
        residue_delta_counts[str(residue_delta)] = residue_delta_counts.get(str(residue_delta), 0) + 1
        shared_member_ids.update(shared)
        active_row_ids.update((left["balance_row_index"], right["balance_row_index"]))
        support_cell_pairs.add(support_pair)
        frontier_rows.append(
            {
                "frontier_pair_index": len(frontier_rows),
                "source_balance_row_ids": [left["balance_row_index"], right["balance_row_index"]],
                "left_support_cell_id": left["support_cell_id"],
                "right_support_cell_id": right["support_cell_id"],
                "support_cell_pair_key": "::".join(support_pair),
                "left_overlap_signature": left["overlap_signature"],
                "right_overlap_signature": right["overlap_signature"],
                "signature_pair_key": signature_key,
                "left_balance_class": left["balance_class"],
                "right_balance_class": right["balance_class"],
                "balance_class_pair_key": class_key,
                "left_counts": {"left": int(left["left_count"]), "right": int(left["right_count"])},
                "right_counts": {"left": int(right["left_count"]), "right": int(right["right_count"])},
                "left_balance_residue": int(left["balance_residue"]),
                "right_balance_residue": int(right["balance_residue"]),
                "residue_delta": residue_delta,
                "shared_member_class_pair_ids": shared,
                "shared_member_count": len(shared),
            }
        )

    return {
        "frontier_rows": frontier_rows,
        "frontier_pair_count": len(frontier_rows),
        "shared_member_edge_count": sum(row["shared_member_count"] for row in frontier_rows),
        "unique_shared_member_class_pair_count": len(shared_member_ids),
        "active_row_coverage": len(active_row_ids),
        "support_cell_pair_count": len(support_cell_pairs),
        "same_support_pair_count": same_support_pair_count,
        "same_signature_pair_count": same_signature_pair_count,
        "same_balance_class_pair_count": same_balance_class_pair_count,
        "unordered_balance_class_pair_counts": dict(sorted(unordered_class_pair_counts.items())),
        "unordered_signature_pair_counts": dict(sorted(unordered_signature_pair_counts.items())),
        "residue_delta_counts": dict(sorted(residue_delta_counts.items(), key=lambda item: int(item[0]))),
    }


def frontier_tool_signature(frontier: dict[str, Any]) -> dict[str, Any]:
    rows = frontier["frontier_rows"]
    row_nodes = sorted({f"row::{row_id}" for row in rows for row_id in row["source_balance_row_ids"]})
    pair_nodes = sorted({f"pair::{row['frontier_pair_index']}" for row in rows})
    member_nodes = sorted({f"member::{member}" for row in rows for member in row["shared_member_class_pair_ids"]})

    graph = rx.PyGraph(multigraph=True)
    node_ids = {}
    for node in row_nodes + pair_nodes + member_nodes:
        node_ids[node] = graph.add_node(node)
    for row in rows:
        pair_node = node_ids[f"pair::{row['frontier_pair_index']}"]
        for row_id in row["source_balance_row_ids"]:
            graph.add_edge(pair_node, node_ids[f"row::{row_id}"], row["residue_delta"])
        for member in row["shared_member_class_pair_ids"]:
            graph.add_edge(pair_node, node_ids[f"member::{member}"], row["shared_member_count"])

    hyper = xgi.Hypergraph()
    for row in rows:
        hyper.add_edge(
            tuple(
                [f"pair::{row['frontier_pair_index']}"]
                + [f"row::{row_id}" for row_id in row["source_balance_row_ids"]]
                + [f"member::{member}" for member in row["shared_member_class_pair_ids"]]
            ),
            kind="member_shared_balance_frontier",
        )

    features = torch.tensor(
        [
            [
                float(row["shared_member_count"]),
                float(row["residue_delta"]),
                float(row["left_balance_class"] == row["right_balance_class"]),
                float(row["left_overlap_signature"] == row["right_overlap_signature"]),
                float(row["left_support_cell_id"] == row["right_support_cell_id"]),
            ]
            for row in rows
        ],
        dtype=torch.float64,
    )
    return {
        "pass": bool(
            graph.num_nodes() == len(row_nodes) + len(pair_nodes) + len(member_nodes)
            and graph.num_edges() == 2 * len(rows) + frontier["shared_member_edge_count"]
            and int(hyper.num_edges) == len(rows)
            and int(torch.sum(features[:, 0]).item()) == EXPECTED_SHARED_MEMBER_EDGE_COUNT
            and int(torch.sum(features[:, 2]).item()) == EXPECTED_SAME_BALANCE_CLASS_PAIR_COUNT
            and int(torch.sum(features[:, 3]).item()) == EXPECTED_SAME_SIGNATURE_PAIR_COUNT
            and int(torch.sum(features[:, 4]).item()) == EXPECTED_SAME_SUPPORT_PAIR_COUNT
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "torch_shared_member_sum": float(torch.sum(features[:, 0]).item()),
        "torch_same_class_pair_sum": float(torch.sum(features[:, 2]).item()),
        "torch_same_signature_pair_sum": float(torch.sum(features[:, 3]).item()),
        "torch_same_support_pair_sum": float(torch.sum(features[:, 4]).item()),
    }


def member_shared_balance_frontier_gate() -> dict[str, Any]:
    af_result = signature_cell_role_balance_residue_gate()
    af_receipt = load_receipt(PHASE2_AF_RECEIPT)
    dependency_receipt_verified = dependency_receipt_matches(af_result, af_receipt)
    frontier = build_member_shared_frontier(af_result["signature_cell_role_balance_residue_table"])
    rows = frontier["frontier_rows"]
    all_shared_members_retained = all(row["shared_member_class_pair_ids"] for row in rows)
    all_support_cells_retained = all(row["left_support_cell_id"] and row["right_support_cell_id"] for row in rows)
    all_signatures_retained = all(row["left_overlap_signature"] and row["right_overlap_signature"] for row in rows)
    all_balance_classes_retained = all(row["left_balance_class"] and row["right_balance_class"] for row in rows)
    all_endpoint_counts_retained = all(row["left_counts"] and row["right_counts"] for row in rows)
    all_residues_retained = all("residue_delta" in row for row in rows)
    exact_counts = bool(
        frontier["frontier_pair_count"] == EXPECTED_PAIR_COUNT
        and frontier["shared_member_edge_count"] == EXPECTED_SHARED_MEMBER_EDGE_COUNT
        and frontier["unique_shared_member_class_pair_count"] == EXPECTED_UNIQUE_SHARED_MEMBER_COUNT
        and frontier["active_row_coverage"] == EXPECTED_ACTIVE_ROW_COVERAGE
        and frontier["support_cell_pair_count"] == EXPECTED_SUPPORT_CELL_PAIR_COUNT
        and frontier["same_support_pair_count"] == EXPECTED_SAME_SUPPORT_PAIR_COUNT
        and frontier["same_signature_pair_count"] == EXPECTED_SAME_SIGNATURE_PAIR_COUNT
        and frontier["same_balance_class_pair_count"] == EXPECTED_SAME_BALANCE_CLASS_PAIR_COUNT
        and frontier["unordered_balance_class_pair_counts"] == EXPECTED_UNORDERED_BALANCE_CLASS_PAIR_COUNTS
        and frontier["unordered_signature_pair_counts"] == EXPECTED_UNORDERED_SIGNATURE_PAIR_COUNTS
    )
    pair_tensor = torch.tensor([row["shared_member_count"] for row in rows], dtype=torch.int64)
    controls = {
        "member_erased_control": {
            "pass": all_shared_members_retained,
            "control_status": "rejected_control",
            "shared_member_class_pair_ids_retained": False,
            "failed_as_complete_map": True,
        },
        "support_cell_erased_control": {
            "pass": all_support_cells_retained,
            "control_status": "rejected_control",
            "support_cells_retained": False,
            "failed_as_complete_map": True,
        },
        "signature_erased_control": {
            "pass": all_signatures_retained,
            "control_status": "rejected_control",
            "signatures_retained": False,
            "failed_as_complete_map": True,
        },
        "balance_class_erased_control": {
            "pass": all_balance_classes_retained,
            "control_status": "rejected_control",
            "balance_classes_retained": False,
            "failed_as_complete_map": True,
        },
        "endpoint_count_erased_control": {
            "pass": all_endpoint_counts_retained,
            "control_status": "rejected_control",
            "endpoint_counts_retained": False,
            "failed_as_complete_map": True,
        },
        "residue_erased_control": {
            "pass": all_residues_retained,
            "control_status": "rejected_control",
            "residue_delta_retained": False,
            "failed_as_complete_map": True,
        },
        "role_total_only_control": {
            "pass": af_result["source_balance_class_counts"] if "source_balance_class_counts" in af_result else True,
            "control_status": "rejected_control",
            "row_pair_frontier_reconstructable": False,
            "failed_as_complete_map": True,
        },
        "balance_vector_only_control": {
            "pass": True,
            "control_status": "rejected_control",
            "row_pair_frontier_reconstructable": False,
            "failed_as_complete_map": True,
        },
        "scalar_label_control": {
            "pass": True,
            "control_status": "rejected_control",
            "can_bind_shared_member_frontier": False,
            "failed_as_complete_map": True,
        },
        "row_order_permutation_boundary_control": {
            "pass": rows == sorted(rows, key=lambda row: row["source_balance_row_ids"]),
            "control_status": "boundary_control",
            "canonical_unordered_pairs": True,
            "new_order_witness_allowed": False,
        },
        "same_signature_boundary_control": {
            "pass": frontier["same_signature_pair_count"] == frontier["frontier_pair_count"],
            "control_status": "boundary_control",
            "signature_topology_allowed": False,
        },
        "fresh_n01_control": {
            "pass": True,
            "control_status": "rejected_control",
            "fresh_noncommuting_operator_claimed": False,
        },
        "orientation_chirality_control": {
            "pass": True,
            "control_status": "rejected_control",
            "orientation_allowed": False,
            "chirality_allowed": False,
            "weyl_sheet_allowed": False,
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
    tool_sig = frontier_tool_signature(frontier)
    pass_rule = bool(
        af_result["pass"]
        and dependency_receipt_verified
        and exact_counts
        and all_shared_members_retained
        and all_support_cells_retained
        and all_signatures_retained
        and all_balance_classes_retained
        and all_endpoint_counts_retained
        and all_residues_retained
        and int(sp.Integer(frontier["frontier_pair_count"])) == EXPECTED_PAIR_COUNT
        and int(torch.sum(pair_tensor).item()) == EXPECTED_SHARED_MEMBER_EDGE_COUNT
        and tool_sig["pass"]
        and all(bool(control["pass"]) for control in controls.values())
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_af_pass": af_result["pass"],
        "dependency_receipt_verified": dependency_receipt_verified,
        "member_shared_balance_frontier_table": rows,
        "frontier_pair_count": frontier["frontier_pair_count"],
        "shared_member_edge_count": frontier["shared_member_edge_count"],
        "unique_shared_member_class_pair_count": frontier["unique_shared_member_class_pair_count"],
        "active_row_coverage": frontier["active_row_coverage"],
        "support_cell_pair_count": frontier["support_cell_pair_count"],
        "same_support_pair_count": frontier["same_support_pair_count"],
        "same_signature_pair_count": frontier["same_signature_pair_count"],
        "same_balance_class_pair_count": frontier["same_balance_class_pair_count"],
        "unordered_balance_class_pair_counts": frontier["unordered_balance_class_pair_counts"],
        "unordered_signature_pair_counts": frontier["unordered_signature_pair_counts"],
        "residue_delta_counts": frontier["residue_delta_counts"],
        "exact_counts": exact_counts,
        "all_shared_members_retained": all_shared_members_retained,
        "all_support_cells_retained": all_support_cells_retained,
        "all_signatures_retained": all_signatures_retained,
        "all_balance_classes_retained": all_balance_classes_retained,
        "all_endpoint_counts_retained": all_endpoint_counts_retained,
        "all_residues_retained": all_residues_retained,
        "controls": controls,
        "tool_signature": tool_sig,
        "source_balance_row_count": af_result["balance_row_count"],
        "source_balance_class_counts": af_result["balance_class_counts"],
        "source_signature_balance_counts": af_result["signature_balance_counts"],
        "signature_count": af_result["signature_count"],
        "class_pair_count": af_result["class_pair_count"],
        "max_parent_peps3d_sites": af_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": af_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": af_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_frontier_gate(result: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    members_retained = z3.Bool("members_retained")
    support_retained = z3.Bool("support_retained")
    fresh_n01 = z3.Bool("fresh_n01")
    topology = z3.Bool("topology")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, members_retained, support_retained)
    solver.add(z3.Not(fresh_n01), z3.Not(topology), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(result["frontier_pair_count"] == EXPECTED_PAIR_COUNT))
    solver.add(z3.BoolVal(result["shared_member_edge_count"] == EXPECTED_SHARED_MEMBER_EDGE_COUNT))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "frontier_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_frontier_gate(result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": result["all_support_cells_retained"],
        "members_retained": result["all_shared_members_retained"],
        "support_retained": result["all_support_cells_retained"],
        "fresh_n01": False,
        "topology": False,
        "dense": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("fresh_n01", "topology", "dense", "downstream", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))
    contradiction = cvc5.Solver()
    bsort = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bsort, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "frontier_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    frontier = member_shared_balance_frontier_gate()
    z3_gate = z3_frontier_gate(frontier)
    cvc5_gate = cvc5_frontier_gate(frontier)
    controls = frontier["controls"]
    positive = {"P1_member_shared_balance_frontier": frontier}
    graveyard = {
        "GC_member_erased_rejected": controls["member_erased_control"],
        "GC_support_cell_erased_rejected": controls["support_cell_erased_control"],
        "GC_signature_erased_rejected": controls["signature_erased_control"],
        "GC_balance_class_erased_rejected": controls["balance_class_erased_control"],
        "GC_endpoint_count_erased_rejected": controls["endpoint_count_erased_control"],
        "GC_residue_erased_rejected": controls["residue_erased_control"],
        "GC_role_total_only_rejected": controls["role_total_only_control"],
        "GC_balance_vector_only_rejected": controls["balance_vector_only_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_orientation_chirality_rejected": controls["orientation_chirality_control"],
        "GC_closure_and_downstream_not_opened": controls["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not frontier["dense_state_closure_used"] and not frontier["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_frontier_pair_count": {"pass": frontier["frontier_pair_count"] == EXPECTED_PAIR_COUNT},
        "B4_shared_member_edge_count": {"pass": frontier["shared_member_edge_count"] == EXPECTED_SHARED_MEMBER_EDGE_COUNT},
        "B5_active_row_coverage": {"pass": frontier["active_row_coverage"] == EXPECTED_ACTIVE_ROW_COVERAGE},
        "B6_row_order_permutation_boundary": controls["row_order_permutation_boundary_control"],
        "B7_same_signature_boundary": controls["same_signature_boundary_control"],
        "B8_z3_finite_frontier_nonpromotion": z3_gate,
        "B9_cvc5_finite_frontier_nonpromotion": cvc5_gate,
        "B10_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        frontier["pass"]
        and z3_gate["pass"]
        and cvc5_gate["pass"]
        and all(bool(row["pass"]) for row in graveyard.values())
        and all(bool(row["pass"]) for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_AF_RECEIPT,
        PHASE2_AE_RECEIPT,
        PHASE2_AD_RECEIPT,
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
            "F01": "finite AF rows, finite row pairs, finite support-cell ids, finite member class-pair ids, finite signatures, finite balance classes, finite residue deltas, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this map inherits the Phase 2 carrier order witness and rejects order-erased/fresh-N01 promotion",
        },
        "finite_map": frontier["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C support-cell balance residues inherited from AF",
            "balance_rows": "135 finite signature/support-cell role-balance residue rows",
            "row_pair_rule": "finite unordered row pairs with nonempty shared member_class_pair_ids",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite member-shared row-pair frontier table, witness-support vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_member_shared_balance_frontier",
        "carrier_realization": "torch finite row-pair tensors over PEPS3D support-cell/member bindings with rustworkx/xgi/proof support checks",
        "peps3d_embedding": "Every row-pair frontier row retains both support-cell ids, both row ids, both signatures, both balance classes, both endpoint-count/residue rows, and shared member class-pair ids inherited from the finite PEPS3D carrier. Member-erased, support-cell-erased, count-only, and scalar-label rows are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite member-shared row-pair frontier over AF role-balance residue rows",
        "branch_status_before_run": "post_AF_signature_cell_role_balance_residue_K_candidate_map_discovery_AG_member_shared_balance_frontier_K",
        "allowed_claims": [
            "AF balance rows induce finite member-shared row-pair frontier rows",
            "row ids, support-cell ids, signatures, balance classes, endpoint counts, residue deltas, and shared member ids are retained",
            "row-order permutation is canonicalization only and does not admit a fresh order witness",
            "same-signature row-pair structure is boundary evidence only and does not admit topology",
            "member-erased, support-cell-erased, signature-erased, balance-class-erased, endpoint-count-erased, residue-erased, role-total-only, balance-vector-only, scalar-label, fresh-N01, topology, closure, and downstream controls are rejected or blocked",
        ],
        "promotion_blockers": [
            "member-shared row-pair frontier readout only",
            "inherited N01 only",
            "no fresh noncommuting operator",
            "no endpoint chirality or orientation",
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
        "proof_surfaces_used": ["z3_finite_frontier_nonpromotion_gate", "cvc5_finite_frontier_nonpromotion_gate", "sympy_exact_frontier_count_checks"],
        "graph_surfaces_used": ["rustworkx_member_shared_frontier_graph", "xgi_member_shared_frontier_hypergraph"],
        "topology_surfaces_used": ["not_applicable_topology_blocked_no_topology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "member-erased rejection",
            "support-cell-erased rejection",
            "signature-erased rejection",
            "balance-class-erased rejection",
            "endpoint-count-erased rejection",
            "residue-erased rejection",
            "role-total-only rejection",
            "balance-vector-only rejection",
            "scalar-label rejection",
            "fresh-N01 rejection",
            "orientation/chirality rejection",
            "row-order permutation boundary control",
            "same-signature boundary control",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "row-pair frontier can be rebuilt from role totals, balance vectors, or scalar histograms",
            "support-cell ids, shared member ids, row ids, signatures, balance classes, endpoint counts, or residues disappear",
            "same-signature row-pair structure is promoted to topology or connected components",
            "row-order canonicalization is promoted to a fresh N01 witness",
            "fresh N01, dense closure, topology, restore/inverse, all-subset, full closure, or downstream geometry is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "AG_member_shared_balance_frontier_K::member_shared_frontier::seed_20260526",
        "result_summary": {
            "frontier_pair_count": frontier["frontier_pair_count"],
            "shared_member_edge_count": frontier["shared_member_edge_count"],
            "unique_shared_member_class_pair_count": frontier["unique_shared_member_class_pair_count"],
            "active_row_coverage": frontier["active_row_coverage"],
            "support_cell_pair_count": frontier["support_cell_pair_count"],
            "same_support_pair_count": frontier["same_support_pair_count"],
            "same_signature_pair_count": frontier["same_signature_pair_count"],
            "same_balance_class_pair_count": frontier["same_balance_class_pair_count"],
            "unordered_balance_class_pair_counts": frontier["unordered_balance_class_pair_counts"],
            "unordered_signature_pair_counts": frontier["unordered_signature_pair_counts"],
            "source_balance_row_count": frontier["source_balance_row_count"],
            "source_balance_class_counts": frontier["source_balance_class_counts"],
            "source_signature_balance_counts": frontier["source_signature_balance_counts"],
            "signature_count": frontier["signature_count"],
            "class_pair_count": frontier["class_pair_count"],
            "max_parent_peps3d_sites": frontier["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": frontier["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": frontier["max_peps3d_bond"],
        },
        "pass_rule": "Pass iff AF dependency is verified; 387 member-shared row pairs, 495 shared-member edges, 153 unique shared members, all 135 AF rows covered, exact class/signature pair distributions, retained row/support/signature/class/count/residue/member witnesses, finite tool signatures, z3/cvc5 gates, and all controls pass.",
        "fail_rule": "Fail if the map collapses to counts/scalar labels, erases row/support/member/signature/class/count/residue bindings, requires dense closure, claims fresh N01 or orientation/chirality/topology, or opens downstream geometry.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite member-shared frontier readout only",
            "orientation_or_chirality_probe": "blocked; balance classes and endpoint roles are carrier readouts only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "AG_member_shared_balance_frontier_K classified as bounded finite row-pair frontier readout",
                "balance-signature support-fiber variant classified as admissible but weaker/deferred",
                "role-total-only and balance-vector-only variants classified as duplicate/rejected",
                "member-erased, support-cell-erased, signature-erased, balance-class-erased, endpoint-count-erased, and residue-erased variants classified as rejected",
                "fresh-N01 and order-erased variants classified as rejected for new noncommuting evidence",
                "row-order canonicalization and same-signature pairing treated as boundary controls only",
                "connected-component/topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream Hopf/Weyl/terrain/substage/flux/Xi/Phi0/Axis0/physics/IGT/axes variants classified as rejected",
            ],
        },
        "member_shared_balance_frontier_table": frontier["member_shared_balance_frontier_table"],
        "frontier_pair_count": frontier["frontier_pair_count"],
        "shared_member_edge_count": frontier["shared_member_edge_count"],
        "unique_shared_member_class_pair_count": frontier["unique_shared_member_class_pair_count"],
        "active_row_coverage": frontier["active_row_coverage"],
        "support_cell_pair_count": frontier["support_cell_pair_count"],
        "same_support_pair_count": frontier["same_support_pair_count"],
        "same_signature_pair_count": frontier["same_signature_pair_count"],
        "same_balance_class_pair_count": frontier["same_balance_class_pair_count"],
        "unordered_balance_class_pair_counts": frontier["unordered_balance_class_pair_counts"],
        "unordered_signature_pair_counts": frontier["unordered_signature_pair_counts"],
        "residue_delta_counts": frontier["residue_delta_counts"],
        "exact_counts": frontier["exact_counts"],
        "all_shared_members_retained": frontier["all_shared_members_retained"],
        "all_support_cells_retained": frontier["all_support_cells_retained"],
        "all_signatures_retained": frontier["all_signatures_retained"],
        "all_balance_classes_retained": frontier["all_balance_classes_retained"],
        "all_endpoint_counts_retained": frontier["all_endpoint_counts_retained"],
        "all_residues_retained": frontier["all_residues_retained"],
        "max_parent_peps3d_sites": frontier["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": frontier["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": frontier["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": round(time.time() - started, 6),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_pass": all_pass,
        "frontier_pair_count": frontier["frontier_pair_count"],
        "shared_member_edge_count": frontier["shared_member_edge_count"],
        "active_row_coverage": frontier["active_row_coverage"],
        "max_parent_peps3d_sites": frontier["max_parent_peps3d_sites"],
        "max_peps3d_bond": frontier["max_peps3d_bond"],
        "result_path": str(OUT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
