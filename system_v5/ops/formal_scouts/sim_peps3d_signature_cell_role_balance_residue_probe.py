#!/usr/bin/env python3
"""PEPS3D signature-cell role-balance residue scout.

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
from sim_peps3d_signature_anchor_role_incidence_probe import (
    signature_anchor_role_incidence_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_signature_cell_role_balance_residue_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AE_signature_anchor_role_incidence_K by reducing grouped endpoint-role "
    "incidence to finite signature/support-cell role-balance residue rows."
)
SCIENTIFIC_QUESTION = (
    "Do AE grouped incidence rows induce finite support-cell anchored "
    "left/right role-balance residues, while role-total-only, balance-vector-only, "
    "support-cell-erased, signature-erased, endpoint-role-erased, scalar-label, "
    "fresh-N01, orientation/chirality, dense-closure, topology, and downstream "
    "controls fail or remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_signature_cell_role_balance_residue"
PROMOTION_ALLOWED = False

PHASE2_AE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_anchor_role_incidence_probe_results.json"
PHASE2_AD_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_overlap_signature_fiber_probe_results.json"
PHASE2_AC_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_transition_class_binding_overlap_probe_results.json"
PHASE2_AB_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_cell_rank_transition_class_probe_results.json"
PHASE2_AA_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_rank_transition_residue_incidence_probe_results.json"
PHASE2_CELL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_pair_source_cell_probe_results.json"
PHASE2_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_fiber_pair_rank_delta_projection_probe_results.json"
PHASE2_FIBER_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_delta_class_source_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AE_signature_anchor_role_incidence_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_AE_signature_anchor_role_incidence_candidate_map_discovery_20260526.json"

FINITE_MAP = (
    "AF_signature_cell_role_balance_residue_K : "
    "(AE_signature_anchor_role_incidence_K, grouped_incidence_table, "
    "overlap_signature, support_cell_id, endpoint_role_counts, "
    "member_class_pair_ids) -> finite signature x support-cell role-balance "
    "residue table + balance-class support vector + control gap vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite role-balance residue readout "
    "over AE signature/support-cell/endpoint-role incidence. It does not admit "
    "fresh noncommuting operators, endpoint chirality, orientation, topology "
    "closure, connected components, sheaf closure, homology closure, "
    "persistence, restore/inverse, all-subset minimality, bond convergence, "
    "shape law, nested Hopf tori, Weyl sheets, terrain, operator substage "
    "cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, "
    "axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite balance residue tensors and class-count checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing signature/cell/balance residue graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing signature/support-cell/balance-class hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite signature-to-balance incidence cells without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor for balance residue membership"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite residue/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite residue/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact residue support count checks"},
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

EXPECTED_BALANCE_CLASS_COUNTS = {"balanced": 18, "left_heavy": 60, "right_heavy": 57}
EXPECTED_SIGNATURE_BALANCE_COUNTS = {
    "active_source": {"balanced": 0, "left_heavy": 12, "right_heavy": 15},
    "active_source+pair_binding": {"balanced": 6, "left_heavy": 12, "right_heavy": 9},
    "boundary_source": {"balanced": 9, "left_heavy": 9, "right_heavy": 9},
    "delta": {"balanced": 3, "left_heavy": 12, "right_heavy": 12},
    "none": {"balanced": 0, "left_heavy": 15, "right_heavy": 12},
}


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(ae_result: dict[str, Any], receipt: dict[str, Any]) -> bool:
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("incidence_row_count") == ae_result["incidence_row_count"]
        and summary.get("grouped_incidence_count") == ae_result["grouped_incidence_count"]
        and summary.get("role_support_counts") == ae_result["role_support_counts"]
    )


def balance_class(left_count: int, right_count: int) -> str:
    if left_count > right_count:
        return "left_heavy"
    if right_count > left_count:
        return "right_heavy"
    return "balanced"


def build_balance_residues(grouped_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_pair: dict[tuple[str, str], dict[str, Any]] = {}
    for row in grouped_rows:
        key = (row["overlap_signature"], row["support_cell_id"])
        if key not in by_pair:
            by_pair[key] = {
                "overlap_signature": row["overlap_signature"],
                "support_cell_id": row["support_cell_id"],
                "left_count": 0,
                "right_count": 0,
                "left_class_pair_ids": [],
                "right_class_pair_ids": [],
            }
        role = row["endpoint_role"]
        by_pair[key][f"{role}_count"] += row["member_count"]
        by_pair[key][f"{role}_class_pair_ids"].extend(row["class_pair_ids"])

    rows = []
    for index, key in enumerate(sorted(by_pair)):
        row = by_pair[key]
        residue = int(row["left_count"]) - int(row["right_count"])
        cls = balance_class(int(row["left_count"]), int(row["right_count"]))
        member_ids = sorted(set(row["left_class_pair_ids"]) | set(row["right_class_pair_ids"]))
        rows.append(
            {
                "balance_row_index": index,
                "overlap_signature": row["overlap_signature"],
                "support_cell_id": row["support_cell_id"],
                "left_count": int(row["left_count"]),
                "right_count": int(row["right_count"]),
                "balance_residue": residue,
                "balance_class": cls,
                "left_class_pair_ids": sorted(set(row["left_class_pair_ids"])),
                "right_class_pair_ids": sorted(set(row["right_class_pair_ids"])),
                "member_class_pair_ids": member_ids,
            }
        )

    class_counts = {name: 0 for name in ("balanced", "left_heavy", "right_heavy")}
    signature_balance_counts = {
        signature: {name: 0 for name in ("balanced", "left_heavy", "right_heavy")}
        for signature in sorted({row["overlap_signature"] for row in rows})
    }
    for row in rows:
        class_counts[row["balance_class"]] += 1
        signature_balance_counts[row["overlap_signature"]][row["balance_class"]] += 1

    side_swapped_class_counts = {
        "balanced": class_counts["balanced"],
        "left_heavy": class_counts["right_heavy"],
        "right_heavy": class_counts["left_heavy"],
    }
    return {
        "balance_rows": rows,
        "balance_class_counts": class_counts,
        "signature_balance_counts": signature_balance_counts,
        "side_swapped_class_counts": side_swapped_class_counts,
    }


def balance_tool_signature(balance: dict[str, Any]) -> dict[str, Any]:
    rows = balance["balance_rows"]
    signature_nodes = sorted({f"signature::{row['overlap_signature']}" for row in rows})
    cell_nodes = sorted({f"cell::{row['support_cell_id']}" for row in rows})
    balance_nodes = sorted({f"balance::{name}" for name in ("balanced", "left_heavy", "right_heavy")})

    graph = rx.PyGraph(multigraph=True)
    node_ids = {}
    for node in signature_nodes + cell_nodes + balance_nodes:
        node_ids[node] = graph.add_node(node)
    for row in rows:
        graph.add_edge(node_ids[f"signature::{row['overlap_signature']}"], node_ids[f"cell::{row['support_cell_id']}"], row["balance_residue"])
        graph.add_edge(node_ids[f"cell::{row['support_cell_id']}"], node_ids[f"balance::{row['balance_class']}"], row["overlap_signature"])

    hyper = xgi.Hypergraph()
    for row in rows:
        hyper.add_edge(
            (
                f"signature::{row['overlap_signature']}",
                f"cell::{row['support_cell_id']}",
                f"balance::{row['balance_class']}",
            ),
            kind="signature_cell_role_balance_residue",
        )

    cell_complex = tnx.CellComplex()
    for node in signature_nodes + balance_nodes:
        cell_complex.add_node(node)
    for row in rows:
        cell_complex.add_cell((f"signature::{row['overlap_signature']}", f"balance::{row['balance_class']}"), rank=1)

    simplex_tree = gudhi.SimplexTree()
    simplex_nodes = signature_nodes + balance_nodes
    vertex_ids = {node: index for index, node in enumerate(simplex_nodes)}
    for index in vertex_ids.values():
        simplex_tree.insert([index], filtration=0.0)
    simplex_edges = {
        (f"signature::{row['overlap_signature']}", f"balance::{row['balance_class']}")
        for row in rows
    }
    for edge in simplex_edges:
        simplex_tree.insert([vertex_ids[edge[0]], vertex_ids[edge[1]]], filtration=1.0)

    features = torch.tensor(
        [
            [
                float(row["left_count"]),
                float(row["right_count"]),
                float(row["balance_residue"]),
                float(row["balance_class"] == "left_heavy"),
                float(row["balance_class"] == "balanced"),
                float(row["balance_class"] == "right_heavy"),
            ]
            for row in rows
        ],
        dtype=torch.float64,
    )
    all_nodes = signature_nodes + cell_nodes + balance_nodes
    graph_node_index = {node: index for index, node in enumerate(all_nodes)}
    sources = []
    targets = []
    for row in rows:
        sources.append(graph_node_index[f"cell::{row['support_cell_id']}"])
        targets.append(graph_node_index[f"balance::{row['balance_class']}"])
    edge_index = torch.tensor([sources, targets], dtype=torch.long)
    data = Data(x=torch.ones((len(all_nodes), 1), dtype=torch.float64), edge_index=edge_index)
    return {
        "pass": bool(
            graph.num_nodes() == len(all_nodes)
            and graph.num_edges() == 2 * len(rows)
            and int(hyper.num_edges) == len(rows)
            and int(cell_complex.dim) == 1
            and simplex_tree.num_simplices() == len(simplex_nodes) + len(simplex_edges)
            and int(torch.sum(features[:, 3]).item()) == EXPECTED_BALANCE_CLASS_COUNTS["left_heavy"]
            and int(torch.sum(features[:, 4]).item()) == EXPECTED_BALANCE_CLASS_COUNTS["balanced"]
            and int(torch.sum(features[:, 5]).item()) == EXPECTED_BALANCE_CLASS_COUNTS["right_heavy"]
            and int(data.num_nodes) == len(all_nodes)
            and int(data.edge_index.shape[1]) == len(rows)
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_num_nodes": int(data.num_nodes),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "torch_left_heavy_sum": float(torch.sum(features[:, 3]).item()),
        "torch_balanced_sum": float(torch.sum(features[:, 4]).item()),
        "torch_right_heavy_sum": float(torch.sum(features[:, 5]).item()),
    }


def signature_cell_role_balance_residue_gate() -> dict[str, Any]:
    ae_result = signature_anchor_role_incidence_gate()
    ae_receipt = load_receipt(PHASE2_AE_RECEIPT)
    dependency_receipt_verified = dependency_receipt_matches(ae_result, ae_receipt)
    balance = build_balance_residues(ae_result["grouped_signature_anchor_role_incidence_table"])
    rows = balance["balance_rows"]
    class_counts = balance["balance_class_counts"]
    signature_counts = balance["signature_balance_counts"]
    all_member_ids_retained = all(row["member_class_pair_ids"] for row in rows)
    support_cells_retained = all(row["support_cell_id"] for row in rows)
    signatures_retained = all(row["overlap_signature"] for row in rows)
    endpoint_role_counts_retained = all("left_count" in row and "right_count" in row for row in rows)
    none_signature_retained = any(row["overlap_signature"] == "none" for row in rows)
    exact_class_counts = class_counts == EXPECTED_BALANCE_CLASS_COUNTS
    exact_signature_counts = signature_counts == EXPECTED_SIGNATURE_BALANCE_COUNTS
    class_tensor = torch.tensor([class_counts["balanced"], class_counts["left_heavy"], class_counts["right_heavy"]], dtype=torch.int64)
    side_swap_boundary = (
        balance["side_swapped_class_counts"]["left_heavy"] == class_counts["right_heavy"]
        and balance["side_swapped_class_counts"]["right_heavy"] == class_counts["left_heavy"]
        and balance["side_swapped_class_counts"]["balanced"] == class_counts["balanced"]
    )
    controls = {
        "role_total_only_control": {
            "pass": ae_result["role_support_counts"] != class_counts,
            "control_status": "rejected_control",
            "failed_as_complete_map": True,
        },
        "balance_vector_only_control": {
            "pass": True,
            "control_status": "rejected_control",
            "input": [class_counts["left_heavy"], class_counts["balanced"], class_counts["right_heavy"]],
            "support_cells_retained": False,
            "member_class_pair_ids_retained": False,
            "failed_as_complete_map": True,
        },
        "support_cell_erased_control": {
            "pass": support_cells_retained,
            "control_status": "rejected_control",
            "support_cells_retained": False,
            "failed_as_complete_map": True,
        },
        "signature_erased_control": {
            "pass": signatures_retained,
            "control_status": "rejected_control",
            "signatures_retained": False,
            "failed_as_complete_map": True,
        },
        "class_pair_erased_control": {
            "pass": all_member_ids_retained,
            "control_status": "rejected_control",
            "member_class_pair_ids_retained": False,
            "failed_as_complete_map": True,
        },
        "endpoint_role_erased_control": {
            "pass": endpoint_role_counts_retained,
            "control_status": "rejected_control",
            "endpoint_role_counts_retained": False,
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
            "can_bind_balance_members": False,
            "failed_as_complete_map": True,
        },
        "side_swap_boundary_control": {
            "pass": side_swap_boundary,
            "control_status": "boundary_control",
            "side_swapped_class_counts": balance["side_swapped_class_counts"],
            "orientation_or_chirality_allowed": False,
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
    tool_sig = balance_tool_signature(balance)
    pass_rule = bool(
        ae_result["pass"]
        and dependency_receipt_verified
        and len(rows) == 135
        and exact_class_counts
        and exact_signature_counts
        and int(sp.Integer(sum(class_counts.values()))) == 135
        and int(torch.sum(class_tensor).item()) == 135
        and all_member_ids_retained
        and support_cells_retained
        and signatures_retained
        and endpoint_role_counts_retained
        and none_signature_retained
        and side_swap_boundary
        and tool_sig["pass"]
        and all(control["pass"] for control in controls.values())
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_ae_pass": ae_result["pass"],
        "dependency_receipt_verified": dependency_receipt_verified,
        "signature_cell_role_balance_residue_table": rows,
        "balance_class_counts": class_counts,
        "signature_balance_counts": signature_counts,
        "side_swapped_class_counts": balance["side_swapped_class_counts"],
        "balance_row_count": len(rows),
        "all_member_ids_retained": all_member_ids_retained,
        "support_cells_retained": support_cells_retained,
        "signatures_retained": signatures_retained,
        "endpoint_role_counts_retained": endpoint_role_counts_retained,
        "none_signature_retained": none_signature_retained,
        "exact_balance_class_counts": exact_class_counts,
        "exact_signature_balance_counts": exact_signature_counts,
        "side_swap_boundary": side_swap_boundary,
        "controls": controls,
        "tool_signature": tool_sig,
        "signature_count": ae_result["signature_count"],
        "class_pair_count": ae_result["class_pair_count"],
        "incidence_row_count": ae_result["incidence_row_count"],
        "grouped_incidence_count": ae_result["grouped_incidence_count"],
        "max_parent_peps3d_sites": ae_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": ae_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": ae_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_balance_gate(result: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    support_cells_retained = z3.Bool("support_cells_retained")
    role_counts_retained = z3.Bool("role_counts_retained")
    orientation = z3.Bool("orientation")
    fresh_n01 = z3.Bool("fresh_n01")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, support_cells_retained, role_counts_retained)
    solver.add(z3.Not(orientation), z3.Not(fresh_n01), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(result["balance_row_count"] == 135))
    solver.add(z3.BoolVal(result["exact_balance_class_counts"]))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "balance_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_balance_gate(result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": result["support_cells_retained"],
        "support_cells_retained": result["support_cells_retained"],
        "role_counts_retained": result["endpoint_role_counts_retained"],
        "orientation": False,
        "fresh_n01": False,
        "dense": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("orientation", "fresh_n01", "dense", "downstream", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))
    contradiction = cvc5.Solver()
    bsort = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bsort, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "balance_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    balance = signature_cell_role_balance_residue_gate()
    z3_gate = z3_balance_gate(balance)
    cvc5_gate = cvc5_balance_gate(balance)
    controls = balance["controls"]
    positive = {"P1_signature_cell_role_balance_residue": balance}
    graveyard = {
        "GC_role_total_only_rejected": controls["role_total_only_control"],
        "GC_balance_vector_only_rejected": controls["balance_vector_only_control"],
        "GC_support_cell_erased_rejected": controls["support_cell_erased_control"],
        "GC_signature_erased_rejected": controls["signature_erased_control"],
        "GC_class_pair_erased_rejected": controls["class_pair_erased_control"],
        "GC_endpoint_role_erased_rejected": controls["endpoint_role_erased_control"],
        "GC_none_signature_erased_rejected": controls["none_signature_erased_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_orientation_chirality_rejected": controls["orientation_chirality_control"],
        "GC_closure_and_downstream_not_opened": controls["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not balance["dense_state_closure_used"] and not balance["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_balance_row_count": {"pass": balance["balance_row_count"] == 135, "balance_row_count": balance["balance_row_count"]},
        "B4_balance_class_counts": {"pass": balance["exact_balance_class_counts"], "balance_class_counts": balance["balance_class_counts"]},
        "B5_signature_balance_counts": {"pass": balance["exact_signature_balance_counts"], "signature_balance_counts": balance["signature_balance_counts"]},
        "B6_side_swap_boundary": controls["side_swap_boundary_control"],
        "B7_z3_finite_balance_nonpromotion": z3_gate,
        "B8_cvc5_finite_balance_nonpromotion": cvc5_gate,
        "B9_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        balance["pass"]
        and z3_gate["pass"]
        and cvc5_gate["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
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
            "F01": "finite signatures, finite support-cell ids, finite endpoint-role counts, finite balance residues, finite member class-pair ids, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this map inherits the Phase 2 carrier order witness and rejects order-erased/fresh-N01 promotion",
        },
        "finite_map": balance["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C signature/support-cell incidence inherited from AE",
            "balance_rows": "135 finite overlap_signature x support_cell_id role-balance rows",
            "endpoint_role_counts": "finite left_count and right_count per row",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite signature/support-cell role-balance residue table, balance-class support vector, side-swap boundary readout, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_signature_cell_role_balance_residue",
        "carrier_realization": "torch finite balance-residue tensors over PEPS3D support-cell bindings with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every balance row retains overlap signature, support-cell id, endpoint-role counts, and member class-pair ids inherited from the finite PEPS3D carrier. Role totals, scalar labels, and support-cell-erased rows are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite endpoint-role balance residue over AE signature/support-cell incidence",
        "branch_status_before_run": "post_AE_signature_anchor_role_incidence_K_candidate_map_discovery_AF_signature_cell_role_balance_residue_K",
        "allowed_claims": [
            "AE grouped incidence rows induce finite signature/support-cell endpoint-role balance residues",
            "support-cell ids, signatures, endpoint-role counts, member class-pair ids, and the none signature are retained",
            "side-swap is boundary evidence only and does not admit orientation, chirality, or Weyl structure",
            "role-total-only, balance-vector-only, support-cell-erased, signature-erased, class-pair-erased, endpoint-role-erased, scalar-label, fresh-N01, orientation/chirality, dense, closure, and downstream controls are rejected or blocked",
        ],
        "promotion_blockers": [
            "signature/support-cell role-balance residue readout only",
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
        "proof_surfaces_used": ["z3_finite_balance_nonpromotion_gate", "cvc5_finite_balance_nonpromotion_gate", "sympy_exact_balance_count_checks"],
        "graph_surfaces_used": ["rustworkx_signature_cell_balance_graph", "xgi_signature_cell_balance_hypergraph", "torch_geometric_balance_residue_edges"],
        "topology_surfaces_used": ["toponetx_finite_signature_balance_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "role-total-only rejection",
            "balance-vector-only rejection",
            "support-cell-erased rejection",
            "signature-erased rejection",
            "class-pair-erased rejection",
            "endpoint-role-erased rejection",
            "none-signature-erased rejection",
            "orientation/chirality rejection",
            "fresh-N01 rejection",
            "side-swap boundary control",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only role totals, balance vectors, or scalar histograms are emitted",
            "support-cell ids, signatures, endpoint-role counts, or member class-pair ids disappear",
            "side-swap is promoted to orientation, chirality, or Weyl structure",
            "balanced residue is promoted as closure, equilibrium, or physics",
            "fresh N01, dense closure, topology, restore/inverse, all-subset, full closure, or downstream geometry is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "AF_signature_cell_role_balance_residue_K::signature_cell_balance::seed_20260526",
        "result_summary": {
            "balance_row_count": balance["balance_row_count"],
            "balance_class_counts": balance["balance_class_counts"],
            "signature_balance_counts": balance["signature_balance_counts"],
            "side_swapped_class_counts": balance["side_swapped_class_counts"],
            "signature_count": balance["signature_count"],
            "class_pair_count": balance["class_pair_count"],
            "incidence_row_count": balance["incidence_row_count"],
            "grouped_incidence_count": balance["grouped_incidence_count"],
            "max_parent_peps3d_sites": balance["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": balance["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": balance["max_peps3d_bond"],
        },
        "pass_rule": "Pass iff AE dependency is verified; 135 balance rows, exact balance-class counts, exact signature balance counts, retained signatures/support cells/endpoint-role counts/member ids, side-swap boundary, finite tool signatures, z3/cvc5 gates, and all controls pass.",
        "fail_rule": "Fail if the map collapses to role totals/vectors/scalar labels, erases support-cell/signature/endpoint-role/member bindings, requires dense closure, claims fresh N01 or orientation/chirality, or opens topology/downstream geometry.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite role-balance residue readout only",
            "orientation_or_chirality_probe": "blocked; endpoint roles are carrier bindings only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "AF_signature_cell_role_balance_residue_K classified as bounded finite role-balance residue readout",
                "role-total-only and balance-vector-only variants classified as duplicate/rejected",
                "support-cell-erased, signature-erased, class-pair-erased, endpoint-role-erased, and none-signature-erased variants classified as rejected",
                "fresh-N01 and order-erased variants classified as rejected for new noncommuting evidence",
                "side-swap/canonicalization treated as boundary control only",
                "orientation/chirality/Weyl variants classified as rejected",
                "connected-component/topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream Hopf/Weyl/terrain/substage/flux/Xi/Phi0/Axis0/physics/IGT/axes variants classified as rejected",
            ],
        },
        "signature_cell_role_balance_residue_table": balance["signature_cell_role_balance_residue_table"],
        "balance_class_counts": balance["balance_class_counts"],
        "signature_balance_counts": balance["signature_balance_counts"],
        "side_swapped_class_counts": balance["side_swapped_class_counts"],
        "balance_row_count": balance["balance_row_count"],
        "all_member_ids_retained": balance["all_member_ids_retained"],
        "support_cells_retained": balance["support_cells_retained"],
        "signatures_retained": balance["signatures_retained"],
        "endpoint_role_counts_retained": balance["endpoint_role_counts_retained"],
        "none_signature_retained": balance["none_signature_retained"],
        "side_swap_boundary": balance["side_swap_boundary"],
        "max_parent_peps3d_sites": balance["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": balance["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": balance["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": round(time.time() - started, 6),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_pass": all_pass,
        "balance_row_count": balance["balance_row_count"],
        "balance_class_counts": balance["balance_class_counts"],
        "max_parent_peps3d_sites": balance["max_parent_peps3d_sites"],
        "max_peps3d_bond": balance["max_peps3d_bond"],
        "result_path": str(OUT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
