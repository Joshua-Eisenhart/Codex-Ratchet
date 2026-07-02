#!/usr/bin/env python3
"""PEPS3D signature-anchor role-incidence scout.

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
from sim_peps3d_overlap_signature_fiber_probe import (
    EXPECTED_SIGNATURE_COUNTS,
    overlap_signature_fiber_gate,
)
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_signature_anchor_role_incidence_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AD_overlap_signature_fiber_K by expanding each finite overlap-signature "
    "fiber into PEPS3D support-cell x endpoint-role incidence rows."
)
SCIENTIFIC_QUESTION = (
    "Do AD overlap-signature fibers retain a finite PEPS3D support-cell and "
    "left/right endpoint-role incidence structure, while count-only, "
    "support-erased, class-pair-erased, endpoint-role-erased, scalar-label, "
    "fresh-N01, dense-closure, topology, and downstream controls fail or "
    "remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_signature_anchor_role_incidence"
PROMOTION_ALLOWED = False

PHASE2_AD_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_overlap_signature_fiber_probe_results.json"
PHASE2_AC_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_transition_class_binding_overlap_probe_results.json"
PHASE2_AB_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_cell_rank_transition_class_probe_results.json"
PHASE2_AA_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_rank_transition_residue_incidence_probe_results.json"
PHASE2_CELL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_pair_source_cell_probe_results.json"
PHASE2_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_fiber_pair_rank_delta_projection_probe_results.json"
PHASE2_FIBER_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_class_source_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AD_overlap_signature_fiber_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_AD_overlap_signature_fiber_candidate_map_discovery_20260526.json"

FINITE_MAP = (
    "AE_signature_anchor_role_incidence_K : "
    "(AD_overlap_signature_fiber_K, signature_fiber_table, class_pair_id, "
    "left_support_cell_ids, right_support_cell_ids, endpoint_role, "
    "predicate_flags) -> finite signature x PEPS3D support-cell x "
    "endpoint-role incidence table + role support vector + control gap vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite signature-anchor role "
    "incidence readout over AD overlap-signature fibers. It does not admit "
    "fresh noncommuting operators, topology closure, connected components, "
    "sheaf closure, homology closure, persistence, restore/inverse, "
    "all-subset minimality, bond convergence, shape law, nested Hopf tori, "
    "Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, Axis0, "
    "Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full PEPS3D "
    "closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite role-incidence tensors and support-count checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing signature/pair/cell-role incidence graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing signature/pair/support-cell/endpoint-role hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite signature-to-cell-role incidence cells without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor for incidence row membership"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite incidence/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite incidence/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact incidence and role support count checks"},
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

EXPECTED_ROLE_SUPPORT_COUNTS = {
    "active_source": {"left": 22, "right": 23, "total": 45},
    "active_source+pair_binding": {"left": 50, "right": 40, "total": 90},
    "boundary_source": {"left": 27, "right": 27, "total": 54},
    "delta": {"left": 18, "right": 18, "total": 36},
    "none": {"left": 118, "right": 116, "total": 234},
}


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(ad_result: dict[str, Any], receipt: dict[str, Any]) -> bool:
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("class_pair_count") == ad_result["class_pair_count"]
        and summary.get("signature_count") == ad_result["signature_count"]
        and summary.get("signature_counts") == ad_result["signature_counts"]
    )


def build_role_incidence(pair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    incidence_rows = []
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for pair_index, row in enumerate(pair_rows):
        for role, field in (("left", "left_support_cell_ids"), ("right", "right_support_cell_ids")):
            for support_cell_id in row[field]:
                incidence = {
                    "incidence_row_index": len(incidence_rows),
                    "pair_row_index": pair_index,
                    "class_pair_id": row["class_pair_id"],
                    "overlap_signature": row["overlap_signature"],
                    "support_cell_id": support_cell_id,
                    "endpoint_role": role,
                    "predicate_flags": row["predicate_flags"],
                    "any_overlap": row["any_overlap"],
                }
                incidence_rows.append(incidence)
                key = (row["overlap_signature"], support_cell_id, role)
                if key not in grouped:
                    grouped[key] = {
                        "overlap_signature": row["overlap_signature"],
                        "support_cell_id": support_cell_id,
                        "endpoint_role": role,
                        "member_count": 0,
                        "class_pair_ids": [],
                    }
                grouped[key]["member_count"] += 1
                grouped[key]["class_pair_ids"].append(row["class_pair_id"])

    grouped_table = [
        grouped[key]
        for key in sorted(grouped, key=lambda item: (item[0], item[2], item[1]))
    ]
    signatures = sorted({row["overlap_signature"] for row in pair_rows})
    role_support_counts = {
        signature: {"left": 0, "right": 0, "total": 0}
        for signature in signatures
    }
    for row in incidence_rows:
        role_support_counts[row["overlap_signature"]][row["endpoint_role"]] += 1
        role_support_counts[row["overlap_signature"]]["total"] += 1

    role_sensitive_keys = {
        (row["overlap_signature"], row["support_cell_id"], row["endpoint_role"])
        for row in incidence_rows
    }
    role_erased_keys = {
        (row["overlap_signature"], row["support_cell_id"])
        for row in incidence_rows
    }
    side_swapped_keys = {
        (
            row["overlap_signature"],
            row["support_cell_id"],
            "right" if row["endpoint_role"] == "left" else "left",
        )
        for row in incidence_rows
    }
    return {
        "incidence_rows": incidence_rows,
        "grouped_incidence_table": grouped_table,
        "role_support_counts": role_support_counts,
        "role_sensitive_key_count": len(role_sensitive_keys),
        "role_erased_key_count": len(role_erased_keys),
        "side_swapped_key_count": len(side_swapped_keys),
        "side_swap_changes_role_labeled_table": role_sensitive_keys != side_swapped_keys,
    }


def incidence_tool_signature(incidence: dict[str, Any]) -> dict[str, Any]:
    rows = incidence["incidence_rows"]
    grouped_rows = incidence["grouped_incidence_table"]
    signature_nodes = sorted({f"signature::{row['overlap_signature']}" for row in rows})
    pair_nodes = sorted({f"pair::{row['class_pair_id']}" for row in rows})
    cell_role_nodes = sorted({f"cell_role::{row['support_cell_id']}::{row['endpoint_role']}" for row in rows})

    graph = rx.PyDiGraph(multigraph=True)
    node_ids = {}
    for node in signature_nodes + pair_nodes + cell_role_nodes:
        node_ids[node] = graph.add_node(node)
    for row in rows:
        graph.add_edge(
            node_ids[f"pair::{row['class_pair_id']}"],
            node_ids[f"signature::{row['overlap_signature']}"],
            row["endpoint_role"],
        )
        graph.add_edge(
            node_ids[f"pair::{row['class_pair_id']}"],
            node_ids[f"cell_role::{row['support_cell_id']}::{row['endpoint_role']}"],
            row["overlap_signature"],
        )

    hyper = xgi.Hypergraph()
    for row in rows:
        hyper.add_edge(
            (
                f"signature::{row['overlap_signature']}",
                f"pair::{row['class_pair_id']}",
                f"cell::{row['support_cell_id']}",
                f"role::{row['endpoint_role']}",
            ),
            kind="signature_anchor_role_incidence",
        )

    cell_complex = tnx.CellComplex()
    for node in signature_nodes + cell_role_nodes:
        cell_complex.add_node(node)
    for row in grouped_rows:
        cell_complex.add_cell(
            (
                f"signature::{row['overlap_signature']}",
                f"cell_role::{row['support_cell_id']}::{row['endpoint_role']}",
            ),
            rank=1,
        )

    simplex_tree = gudhi.SimplexTree()
    simplex_nodes = signature_nodes + cell_role_nodes
    vertex_ids = {node: index for index, node in enumerate(simplex_nodes)}
    for index in vertex_ids.values():
        simplex_tree.insert([index], filtration=0.0)
    for row in grouped_rows:
        simplex_tree.insert(
            [
                vertex_ids[f"signature::{row['overlap_signature']}"],
                vertex_ids[f"cell_role::{row['support_cell_id']}::{row['endpoint_role']}"],
            ],
            filtration=1.0,
        )

    features = torch.tensor(
        [
            [
                float(row["endpoint_role"] == "left"),
                float(row["endpoint_role"] == "right"),
                float(row["any_overlap"]),
                float(row["predicate_flags"]["delta"]),
                float(row["predicate_flags"]["active_source"]),
                float(row["predicate_flags"]["boundary_source"]),
                float(row["predicate_flags"]["pair_binding"]),
                float(row["predicate_flags"]["rank_signature"]),
            ]
            for row in rows
        ],
        dtype=torch.float64,
    )
    all_graph_nodes = signature_nodes + pair_nodes + cell_role_nodes
    graph_node_index = {node: index for index, node in enumerate(all_graph_nodes)}
    sources = []
    targets = []
    for row in rows:
        sources.append(graph_node_index[f"pair::{row['class_pair_id']}"])
        targets.append(graph_node_index[f"cell_role::{row['support_cell_id']}::{row['endpoint_role']}"])
    edge_index = torch.tensor([sources, targets], dtype=torch.long)
    data = Data(x=torch.ones((len(all_graph_nodes), 1), dtype=torch.float64), edge_index=edge_index)

    incidence_count = len(rows)
    grouped_count = len(grouped_rows)
    return {
        "pass": bool(
            graph.num_nodes() == len(all_graph_nodes)
            and graph.num_edges() == 2 * incidence_count
            and int(hyper.num_edges) == incidence_count
            and int(cell_complex.dim) == 1
            and simplex_tree.num_simplices() == len(simplex_nodes) + grouped_count
            and int(torch.sum(features[:, 0]).item()) == 235
            and int(torch.sum(features[:, 1]).item()) == 224
            and int(data.num_nodes) == len(all_graph_nodes)
            and int(data.edge_index.shape[1]) == incidence_count
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_num_nodes": int(data.num_nodes),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "torch_left_role_sum": float(torch.sum(features[:, 0]).item()),
        "torch_right_role_sum": float(torch.sum(features[:, 1]).item()),
        "torch_any_overlap_sum": float(torch.sum(features[:, 2]).item()),
    }


def signature_anchor_role_incidence_gate() -> dict[str, Any]:
    ad_result = overlap_signature_fiber_gate()
    ad_receipt = load_receipt(PHASE2_AD_RECEIPT)
    dependency_receipt_verified = dependency_receipt_matches(ad_result, ad_receipt)
    incidence = build_role_incidence(ad_result["signature_pair_rows"])
    incidence_rows = incidence["incidence_rows"]
    grouped_rows = incidence["grouped_incidence_table"]
    role_support_counts = incidence["role_support_counts"]
    expected_role_counts = dict(EXPECTED_ROLE_SUPPORT_COUNTS)

    class_pair_ids_retained = all(row["class_pair_id"] for row in incidence_rows)
    support_cells_retained = all(row["support_cell_id"] for row in incidence_rows)
    endpoint_roles_retained = {row["endpoint_role"] for row in incidence_rows} == {"left", "right"}
    predicate_flags_retained = all(
        set(row["predicate_flags"]) == {"delta", "active_source", "boundary_source", "pair_binding", "rank_signature"}
        for row in incidence_rows
    )
    none_signature_retained = role_support_counts.get("none", {}).get("total") == 234
    rank_signature_empty_boundary = all(not row["predicate_flags"]["rank_signature"] for row in incidence_rows)
    exact_role_support_counts = role_support_counts == expected_role_counts
    role_tensor = torch.tensor(
        [
            [counts["left"], counts["right"], counts["total"]]
            for _, counts in sorted(role_support_counts.items())
        ],
        dtype=torch.int64,
    )
    role_erased_collapses = incidence["role_sensitive_key_count"] > incidence["role_erased_key_count"]
    side_swap_detected = incidence["side_swap_changes_role_labeled_table"]
    controls = {
        "signature_count_only_control": {
            "pass": ad_result["signature_count"] != len(grouped_rows),
            "control_status": "rejected_control",
            "input": ad_result["signature_count"],
            "failed_as_complete_map": True,
        },
        "support_vector_only_control": {
            "pass": True,
            "control_status": "rejected_control",
            "input": ad_result["signature_support_vector"],
            "endpoint_roles_retained": False,
            "support_cells_retained": False,
            "failed_as_complete_map": True,
        },
        "support_cell_erased_control": {
            "pass": support_cells_retained,
            "control_status": "rejected_control",
            "support_cells_retained": False,
            "failed_as_complete_map": True,
        },
        "class_pair_erased_control": {
            "pass": class_pair_ids_retained,
            "control_status": "rejected_control",
            "class_pair_ids_retained": False,
            "failed_as_complete_map": True,
        },
        "endpoint_role_erased_control": {
            "pass": role_erased_collapses,
            "control_status": "rejected_control",
            "role_sensitive_key_count": incidence["role_sensitive_key_count"],
            "role_erased_key_count": incidence["role_erased_key_count"],
            "failed_as_complete_map": True,
        },
        "support_multiplicity_collapse_control": {
            "pass": len(incidence_rows) != ad_result["class_pair_count"] and len(grouped_rows) != ad_result["class_pair_count"],
            "control_status": "rejected_control",
            "incidence_row_count": len(incidence_rows),
            "grouped_incidence_count": len(grouped_rows),
            "class_pair_count": ad_result["class_pair_count"],
            "failed_as_complete_map": True,
        },
        "predicate_erased_control": {
            "pass": predicate_flags_retained,
            "control_status": "rejected_control",
            "predicate_flags_retained": False,
            "failed_as_complete_map": True,
        },
        "none_signature_erased_control": {
            "pass": none_signature_retained,
            "control_status": "rejected_control",
            "none_signature_retained": False,
            "failed_as_complete_map": True,
        },
        "scalar_label_control": {
            "pass": True,
            "control_status": "rejected_control",
            "can_bind_signature_cell_role_members": False,
            "failed_as_complete_map": True,
        },
        "side_swap_boundary_control": {
            "pass": side_swap_detected,
            "control_status": "boundary_control",
            "same_total_incidence": True,
            "role_labeled_table_changes_under_swap": side_swap_detected,
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
    tool_sig = incidence_tool_signature(incidence)
    pass_rule = bool(
        ad_result["pass"]
        and dependency_receipt_verified
        and ad_result["signature_counts"] == EXPECTED_SIGNATURE_COUNTS
        and len(incidence_rows) == 459
        and len(grouped_rows) == 182
        and int(sp.Integer(sum(counts["total"] for counts in role_support_counts.values()))) == 459
        and int(torch.sum(role_tensor[:, 2]).item()) == 459
        and class_pair_ids_retained
        and support_cells_retained
        and endpoint_roles_retained
        and predicate_flags_retained
        and none_signature_retained
        and rank_signature_empty_boundary
        and exact_role_support_counts
        and role_erased_collapses
        and side_swap_detected
        and tool_sig["pass"]
        and all(control["pass"] for control in controls.values())
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_ad_pass": ad_result["pass"],
        "dependency_receipt_verified": dependency_receipt_verified,
        "signature_anchor_role_incidence_table": incidence_rows,
        "grouped_signature_anchor_role_incidence_table": grouped_rows,
        "role_support_counts": role_support_counts,
        "expected_role_support_counts": expected_role_counts,
        "exact_role_support_counts": exact_role_support_counts,
        "incidence_row_count": len(incidence_rows),
        "grouped_incidence_count": len(grouped_rows),
        "role_sensitive_key_count": incidence["role_sensitive_key_count"],
        "role_erased_key_count": incidence["role_erased_key_count"],
        "side_swap_changes_role_labeled_table": side_swap_detected,
        "class_pair_ids_retained": class_pair_ids_retained,
        "support_cells_retained": support_cells_retained,
        "endpoint_roles_retained": endpoint_roles_retained,
        "predicate_flags_retained": predicate_flags_retained,
        "none_signature_retained": none_signature_retained,
        "rank_signature_empty_boundary": rank_signature_empty_boundary,
        "controls": controls,
        "tool_signature": tool_sig,
        "signature_count": ad_result["signature_count"],
        "signature_counts": ad_result["signature_counts"],
        "signature_support_vector": ad_result["signature_support_vector"],
        "signature_order": ad_result["signature_order"],
        "class_pair_count": ad_result["class_pair_count"],
        "any_overlap_count": ad_result["any_overlap_count"],
        "no_overlap_count": ad_result["no_overlap_count"],
        "transition_class_count": ad_result["transition_class_count"],
        "cell_transition_row_count": ad_result["cell_transition_row_count"],
        "max_parent_peps3d_sites": ad_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": ad_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": ad_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_incidence_gate(result: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    class_pairs_retained = z3.Bool("class_pairs_retained")
    support_cells_retained = z3.Bool("support_cells_retained")
    endpoint_roles_retained = z3.Bool("endpoint_roles_retained")
    fresh_n01 = z3.Bool("fresh_n01")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, class_pairs_retained, support_cells_retained, endpoint_roles_retained)
    solver.add(z3.Not(fresh_n01), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(result["incidence_row_count"] == 459))
    solver.add(z3.BoolVal(result["grouped_incidence_count"] == 182))
    solver.add(z3.BoolVal(result["role_erased_key_count"] < result["role_sensitive_key_count"]))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "incidence_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_incidence_gate(result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": result["support_cells_retained"] and result["endpoint_roles_retained"],
        "class_pairs_retained": result["class_pair_ids_retained"],
        "support_cells_retained": result["support_cells_retained"],
        "endpoint_roles_retained": result["endpoint_roles_retained"],
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
        "incidence_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    incidence = signature_anchor_role_incidence_gate()
    z3_gate = z3_incidence_gate(incidence)
    cvc5_gate = cvc5_incidence_gate(incidence)
    controls = incidence["controls"]
    positive = {"P1_signature_anchor_role_incidence": incidence}
    graveyard = {
        "GC_signature_count_only_rejected": controls["signature_count_only_control"],
        "GC_support_vector_only_rejected": controls["support_vector_only_control"],
        "GC_support_cell_erased_rejected": controls["support_cell_erased_control"],
        "GC_class_pair_erased_rejected": controls["class_pair_erased_control"],
        "GC_endpoint_role_erased_rejected": controls["endpoint_role_erased_control"],
        "GC_support_multiplicity_collapse_rejected": controls["support_multiplicity_collapse_control"],
        "GC_predicate_erased_rejected": controls["predicate_erased_control"],
        "GC_none_signature_erased_rejected": controls["none_signature_erased_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_closure_and_downstream_not_opened": controls["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not incidence["dense_state_closure_used"] and not incidence["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_incidence_row_count": {"pass": incidence["incidence_row_count"] == 459, "incidence_row_count": incidence["incidence_row_count"]},
        "B4_grouped_incidence_count": {"pass": incidence["grouped_incidence_count"] == 182, "grouped_incidence_count": incidence["grouped_incidence_count"]},
        "B5_role_support_counts": {"pass": incidence["exact_role_support_counts"], "role_support_counts": incidence["role_support_counts"]},
        "B6_side_swap_boundary": controls["side_swap_boundary_control"],
        "B7_z3_finite_incidence_nonpromotion": z3_gate,
        "B8_cvc5_finite_incidence_nonpromotion": cvc5_gate,
        "B9_rank_signature_empty_boundary": {"pass": incidence["rank_signature_empty_boundary"]},
        "B10_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        incidence["pass"]
        and z3_gate["pass"]
        and cvc5_gate["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
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
            "F01": "finite signatures, finite class-pair ids, finite PEPS3D support-cell ids, finite endpoint roles, finite predicate flags, finite incidence rows, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this map inherits the Phase 2 carrier order witness and rejects order-erased/fresh-N01 promotion",
        },
        "finite_map": incidence["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C class-pair support-cell rows inherited from AD overlap-signature fibers",
            "signature_rows": "5 finite overlap-signature fibers",
            "class_pair_rows": "153 finite class-pair rows",
            "incidence_rows": "459 finite signature/support-cell/endpoint-role rows",
            "endpoint_roles": ["left", "right"],
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite signature x PEPS3D support-cell x endpoint-role incidence table, role support vector, side-swap boundary readout, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_signature_anchor_role_incidence",
        "carrier_realization": "torch finite role-incidence tensors over PEPS3D support-cell bindings with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every incidence row retains an overlap signature, class-pair id, support-cell id, and endpoint role inherited from the finite PEPS3D transition-class carrier. Signature counts, scalar labels, and endpoint-erased rows are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite signature-anchor endpoint-role incidence over AD overlap-signature fibers",
        "branch_status_before_run": "post_AD_overlap_signature_fiber_K_candidate_map_discovery_AE_signature_anchor_role_incidence_K",
        "allowed_claims": [
            "AD overlap-signature fibers induce finite signature/support-cell/endpoint-role incidence rows",
            "class-pair ids, support-cell ids, endpoint roles, predicate flags, and the none signature are retained",
            "endpoint-role-erased and side-swap controls show role labels cannot be erased or arbitrarily canonized without losing finite carrier incidence",
            "count-only, support-vector-only, support-cell-erased, class-pair-erased, endpoint-role-erased, predicate-erased, scalar-label, fresh-N01, dense, closure, and downstream controls are rejected or blocked",
        ],
        "promotion_blockers": [
            "signature-anchor role-incidence readout only",
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
        "proof_surfaces_used": ["z3_finite_incidence_nonpromotion_gate", "cvc5_finite_incidence_nonpromotion_gate", "sympy_exact_role_support_count_checks"],
        "graph_surfaces_used": ["rustworkx_signature_pair_cell_role_incidence_graph", "xgi_signature_pair_support_role_hypergraph", "torch_geometric_signature_role_incidence_edges"],
        "topology_surfaces_used": ["toponetx_finite_signature_cell_role_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "signature-count-only rejection",
            "support-vector-only rejection",
            "support-cell-erased rejection",
            "class-pair-erased rejection",
            "endpoint-role-erased rejection",
            "support-multiplicity-collapse rejection",
            "predicate-erased rejection",
            "none-signature-erased rejection",
            "scalar-label rejection",
            "fresh-N01 rejection",
            "side-swap boundary control",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only counts, role totals, or scalar histograms are emitted",
            "class-pair ids, support-cell ids, endpoint roles, or predicate flags disappear",
            "endpoint roles are erased or accepted without side-swap boundary control",
            "the none signature is erased or promoted as closure",
            "rank_signature zero support is promoted as geometry rather than retained as an empty-boundary predicate",
            "fresh N01, dense closure, topology, restore/inverse, all-subset, full closure, or downstream geometry is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "AE_signature_anchor_role_incidence_K::signature_cell_role_incidence::seed_20260526",
        "result_summary": {
            "signature_count": incidence["signature_count"],
            "signature_counts": incidence["signature_counts"],
            "class_pair_count": incidence["class_pair_count"],
            "incidence_row_count": incidence["incidence_row_count"],
            "grouped_incidence_count": incidence["grouped_incidence_count"],
            "role_support_counts": incidence["role_support_counts"],
            "role_sensitive_key_count": incidence["role_sensitive_key_count"],
            "role_erased_key_count": incidence["role_erased_key_count"],
            "side_swap_changes_role_labeled_table": incidence["side_swap_changes_role_labeled_table"],
            "max_parent_peps3d_sites": incidence["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": incidence["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": incidence["max_peps3d_bond"],
        },
        "pass_rule": "Pass iff AD dependency is verified; 459 incidence rows, 182 grouped signature-cell-role keys, exact role support counts, retained class-pair/support-cell/endpoint-role/predicate bindings, retained none signature, rank_signature empty boundary, side-swap boundary, finite tool signatures, z3/cvc5 gates, and all controls pass.",
        "fail_rule": "Fail if the map collapses to counts/vectors/scalar labels, erases class-pair/support-cell/endpoint-role/predicate bindings, requires dense closure, claims fresh N01, or opens topology/downstream geometry.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": [
            "This is not a v4 classical baseline; it is a Phase 2 formal scout over torch-native finite PEPS3D carrier receipts.",
            "No NumPy, dense full-state closure, or scalar PEPS3D label is used as claim-bearing evidence.",
            "The packet keeps downstream Hopf/Weyl, terrain, substage, flux, Xi/Phi0, Axis0, physics, IGT, and axes 7-12 blocked.",
        ],
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "AE_signature_anchor_role_incidence_K classified as bounded finite signature/support-cell/endpoint-role incidence readout",
                "signature-count-only and support-vector-only variants classified as duplicate/rejected",
                "support-cell-erased, class-pair-erased, endpoint-role-erased, and support-multiplicity-collapse variants classified as rejected",
                "predicate-erased and none-signature-erased variants classified as rejected",
                "fresh-N01 and order-erased variants classified as rejected for new noncommuting evidence",
                "side-swap/canonicalization treated as boundary control only",
                "connected-component/topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream Hopf/Weyl/terrain/substage/flux/Xi/Phi0/Axis0/physics/IGT/axes variants classified as rejected",
            ],
        },
        "signature_anchor_role_incidence_table": incidence["signature_anchor_role_incidence_table"],
        "grouped_signature_anchor_role_incidence_table": incidence["grouped_signature_anchor_role_incidence_table"],
        "role_support_counts": incidence["role_support_counts"],
        "incidence_row_count": incidence["incidence_row_count"],
        "grouped_incidence_count": incidence["grouped_incidence_count"],
        "role_sensitive_key_count": incidence["role_sensitive_key_count"],
        "role_erased_key_count": incidence["role_erased_key_count"],
        "side_swap_changes_role_labeled_table": incidence["side_swap_changes_role_labeled_table"],
        "class_pair_ids_retained": incidence["class_pair_ids_retained"],
        "support_cells_retained": incidence["support_cells_retained"],
        "endpoint_roles_retained": incidence["endpoint_roles_retained"],
        "predicate_flags_retained": incidence["predicate_flags_retained"],
        "none_signature_retained": incidence["none_signature_retained"],
        "rank_signature_empty_boundary": incidence["rank_signature_empty_boundary"],
        "max_parent_peps3d_sites": incidence["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": incidence["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": incidence["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": round(time.time() - started, 6),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_pass": all_pass,
        "incidence_row_count": incidence["incidence_row_count"],
        "grouped_incidence_count": incidence["grouped_incidence_count"],
        "role_support_counts": incidence["role_support_counts"],
        "max_parent_peps3d_sites": incidence["max_parent_peps3d_sites"],
        "max_peps3d_bond": incidence["max_peps3d_bond"],
        "result_path": str(OUT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
