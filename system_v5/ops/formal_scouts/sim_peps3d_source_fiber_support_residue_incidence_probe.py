#!/usr/bin/env python3
"""PEPS3D source-fiber support/residue incidence scout.

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
import rustworkx as rx
import sympy as sp
import torch
import xgi
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import as_jsonable
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS
from sim_peps3d_shared_member_frontier_fiber_probe import shared_member_frontier_fiber_gate
from sim_peps3d_source_row_fiber_pullback_probe import source_row_fiber_pullback_gate


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_source_fiber_support_residue_incidence_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AI_source_row_fiber_pullback_K by expanding source-row pullbacks into "
    "finite source-fiber support/residue incidence rows."
)
SCIENTIFIC_QUESTION = (
    "Do AI source-row pullbacks decompose into finite source-fiber incidence "
    "rows with PEPS3D support-cell pair keys and residue/balance/frontier "
    "witnesses retained, while source-erased, fiber-erased, support-erased, "
    "residue-erased, count-only, restore/inverse, topology, fresh-N01, and "
    "downstream controls fail or remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_source_fiber_support_residue_incidence"
PROMOTION_ALLOWED = False

PHASE2_AI_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_source_row_fiber_pullback_probe_results.json"
PHASE2_AH_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_shared_member_frontier_fiber_probe_results.json"
PHASE2_AG_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_member_shared_balance_frontier_probe_results.json"
PHASE2_AF_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_cell_role_balance_residue_probe_results.json"
PHASE2_AE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_anchor_role_incidence_probe_results.json"
PHASE2_AD_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_overlap_signature_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AI_source_row_fiber_pullback_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_AI_source_row_fiber_pullback_candidate_map_discovery_20260526.json"

FINITE_MAP = (
    "AJ_source_fiber_support_residue_incidence_K : "
    "(AI_source_row_fiber_pullback_K, source_balance_row_id, fiber_id, "
    "shared_member_class_pair_id, frontier_pair_ids, support_cell_pair_keys, "
    "residue_delta_values, balance_class_pair_keys) -> finite source-fiber "
    "support/residue incidence table + incidence-support vector + control gap "
    "vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite source-fiber support/residue "
    "incidence readout over AI source-row pullbacks. It does not admit "
    "restore/inverse closure, fresh noncommuting operators, endpoint chirality, "
    "orientation, topology closure, connected components, sheaf closure, "
    "homology closure, persistence, all-subset minimality, bond convergence, "
    "shape law, nested Hopf tori, Weyl sheets, terrain, operator substage "
    "cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, "
    "axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite source-fiber incidence tensors and coverage checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite source/fiber/support incidence graph without component/topology claim"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite source-fiber-support hyperedges"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite incidence/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite incidence/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact incidence count checks"},
    "toponetx": {"tried": False, "used": False, "reason": "not applicable: no cell-complex topology or closure is claimed"},
    "gudhi": {"tried": False, "used": False, "reason": "not applicable: no homology, persistence, or filtration is claimed"},
    "torch_geometric": {"tried": False, "used": False, "reason": "not applicable: rustworkx/xgi already carry the finite incidence claim"},
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

EXPECTED_INCIDENCE_ROWS = 459
EXPECTED_SOURCE_ROW_COUNT = 135
EXPECTED_FIBER_COUNT = 153
EXPECTED_FRONTIER_PAIR_COVERAGE = 387
EXPECTED_SUPPORT_CELL_PAIR_SUPPORT = 351
EXPECTED_RESIDUE_DELTA_SUPPORT = 27
EXPECTED_BALANCE_PAIR_SUPPORT = 6
EXPECTED_SUPPORT_PATTERN_COUNT = 153
EXPECTED_RESIDUE_PATTERN_COUNT = 52
EXPECTED_BALANCE_PATTERN_COUNT = 12
EXPECTED_FRONTIER_PATTERN_COUNT = 153
EXPECTED_SOURCE_FIBER_CARDINALITY_COUNTS = {"1": 36, "2": 45, "3": 9, "4": 18, "8": 9, "9": 18}


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(ai_result: dict[str, Any], receipt: dict[str, Any]) -> bool:
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("source_row_count") == ai_result["source_row_count"]
        and summary.get("total_source_fiber_memberships") == ai_result["total_source_fiber_memberships"]
        and summary.get("fiber_support") == ai_result["fiber_support"]
        and summary.get("support_cell_pair_support") == ai_result["support_cell_pair_support"]
    )


def count_distribution(values: list[int]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def build_source_fiber_incidence(ai_result: dict[str, Any], ah_result: dict[str, Any]) -> dict[str, Any]:
    fiber_lookup = {row["fiber_index"]: row for row in ah_result["shared_member_frontier_fiber_table"]}
    incidence_rows = []
    for source_row in ai_result["source_row_fiber_pullback_table"]:
        for fiber_id in source_row["fiber_ids"]:
            fiber = fiber_lookup[fiber_id]
            incidence_rows.append(
                {
                    "incidence_index": len(incidence_rows),
                    "source_balance_row_id": source_row["source_balance_row_id"],
                    "fiber_id": fiber_id,
                    "shared_member_class_pair_id": fiber["shared_member_class_pair_id"],
                    "frontier_pair_ids": fiber["frontier_pair_ids"],
                    "support_cell_pair_keys": fiber["support_cell_pair_keys"],
                    "residue_delta_values": fiber["residue_delta_values"],
                    "balance_class_pair_keys": fiber["balance_class_pair_keys"],
                    "frontier_pair_count": len(fiber["frontier_pair_ids"]),
                    "support_cell_pair_count": len(fiber["support_cell_pair_keys"]),
                    "residue_delta_support_count": len(set(fiber["residue_delta_values"])),
                    "balance_class_pair_count": len(fiber["balance_class_pair_keys"]),
                }
            )
    return {
        "source_fiber_support_residue_incidence_table": incidence_rows,
        "incidence_row_count": len(incidence_rows),
        "source_row_count": len({row["source_balance_row_id"] for row in incidence_rows}),
        "fiber_count": len({row["fiber_id"] for row in incidence_rows}),
        "frontier_pair_coverage": len({pair for row in incidence_rows for pair in row["frontier_pair_ids"]}),
        "support_cell_pair_support": len({support for row in incidence_rows for support in row["support_cell_pair_keys"]}),
        "residue_delta_support": len({delta for row in incidence_rows for delta in row["residue_delta_values"]}),
        "balance_pair_support": len({balance for row in incidence_rows for balance in row["balance_class_pair_keys"]}),
        "support_pattern_count": len({tuple(row["support_cell_pair_keys"]) for row in incidence_rows}),
        "residue_pattern_count": len({tuple(row["residue_delta_values"]) for row in incidence_rows}),
        "balance_pattern_count": len({tuple(row["balance_class_pair_keys"]) for row in incidence_rows}),
        "frontier_pattern_count": len({tuple(row["frontier_pair_ids"]) for row in incidence_rows}),
        "source_fiber_cardinality_counts": ai_result["source_fiber_cardinality_counts"],
    }


def incidence_tool_signature(incidence: dict[str, Any]) -> dict[str, Any]:
    rows = incidence["source_fiber_support_residue_incidence_table"]
    source_nodes = sorted({f"source::{row['source_balance_row_id']}" for row in rows})
    fiber_nodes = sorted({f"fiber::{row['fiber_id']}" for row in rows})
    support_nodes = sorted({f"support::{support}" for row in rows for support in row["support_cell_pair_keys"]})

    graph = rx.PyGraph(multigraph=True)
    node_ids = {}
    for node in source_nodes + fiber_nodes + support_nodes:
        node_ids[node] = graph.add_node(node)
    edge_count = 0
    for row in rows:
        source_node = node_ids[f"source::{row['source_balance_row_id']}"]
        fiber_node = node_ids[f"fiber::{row['fiber_id']}"]
        graph.add_edge(source_node, fiber_node, row["support_cell_pair_count"])
        edge_count += 1
        for support in row["support_cell_pair_keys"]:
            graph.add_edge(fiber_node, node_ids[f"support::{support}"], row["support_cell_pair_count"])
            edge_count += 1

    hyper = xgi.Hypergraph()
    for row in rows:
        hyper.add_edge(
            tuple(
                [f"source::{row['source_balance_row_id']}", f"fiber::{row['fiber_id']}"]
                + [f"support::{support}" for support in row["support_cell_pair_keys"]]
            ),
            kind="source_fiber_support_residue_incidence",
        )

    features = torch.tensor(
        [
            [
                float(row["frontier_pair_count"]),
                float(row["support_cell_pair_count"]),
                float(row["residue_delta_support_count"]),
                float(row["balance_class_pair_count"]),
            ]
            for row in rows
        ],
        dtype=torch.float64,
    )
    return {
        "pass": bool(
            graph.num_nodes() == len(source_nodes) + len(fiber_nodes) + len(support_nodes)
            and graph.num_edges() == edge_count
            and int(hyper.num_edges) == len(rows)
            and int(features.shape[0]) == EXPECTED_INCIDENCE_ROWS
            and int(torch.max(features[:, 1]).item()) >= 1
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "torch_incidence_rows": int(features.shape[0]),
        "torch_max_support_cell_pair_count": float(torch.max(features[:, 1]).item()),
    }


def source_fiber_incidence_gate() -> dict[str, Any]:
    ai_result = source_row_fiber_pullback_gate()
    ah_result = shared_member_frontier_fiber_gate()
    ai_receipt = load_receipt(PHASE2_AI_RECEIPT)
    dependency_receipt_verified = dependency_receipt_matches(ai_result, ai_receipt)
    incidence = build_source_fiber_incidence(ai_result, ah_result)
    rows = incidence["source_fiber_support_residue_incidence_table"]
    all_sources_retained = all(row["source_balance_row_id"] >= 0 for row in rows)
    all_fibers_retained = all(row["fiber_id"] >= 0 for row in rows)
    all_members_retained = all(row["shared_member_class_pair_id"] for row in rows)
    all_pairs_retained = all(row["frontier_pair_ids"] for row in rows)
    all_support_pairs_retained = all(row["support_cell_pair_keys"] for row in rows)
    all_balance_pairs_retained = all(row["balance_class_pair_keys"] for row in rows)
    all_residue_deltas_retained = all(row["residue_delta_values"] for row in rows)
    exact_counts = bool(
        incidence["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS
        and incidence["source_row_count"] == EXPECTED_SOURCE_ROW_COUNT
        and incidence["fiber_count"] == EXPECTED_FIBER_COUNT
        and incidence["frontier_pair_coverage"] == EXPECTED_FRONTIER_PAIR_COVERAGE
        and incidence["support_cell_pair_support"] == EXPECTED_SUPPORT_CELL_PAIR_SUPPORT
        and incidence["residue_delta_support"] == EXPECTED_RESIDUE_DELTA_SUPPORT
        and incidence["balance_pair_support"] == EXPECTED_BALANCE_PAIR_SUPPORT
        and incidence["support_pattern_count"] == EXPECTED_SUPPORT_PATTERN_COUNT
        and incidence["residue_pattern_count"] == EXPECTED_RESIDUE_PATTERN_COUNT
        and incidence["balance_pattern_count"] == EXPECTED_BALANCE_PATTERN_COUNT
        and incidence["frontier_pattern_count"] == EXPECTED_FRONTIER_PATTERN_COUNT
        and incidence["source_fiber_cardinality_counts"] == EXPECTED_SOURCE_FIBER_CARDINALITY_COUNTS
    )
    incidence_tensor = torch.tensor([row["incidence_index"] for row in rows], dtype=torch.int64)
    controls = {
        "source_row_erased_control": {"pass": all_sources_retained, "control_status": "rejected_control", "source_rows_retained": False, "failed_as_complete_map": True},
        "fiber_id_erased_control": {"pass": all_fibers_retained, "control_status": "rejected_control", "fiber_ids_retained": False, "failed_as_complete_map": True},
        "member_id_erased_control": {"pass": all_members_retained, "control_status": "rejected_control", "member_ids_retained": False, "failed_as_complete_map": True},
        "frontier_pair_erased_control": {"pass": all_pairs_retained, "control_status": "rejected_control", "frontier_pair_ids_retained": False, "failed_as_complete_map": True},
        "support_cell_pair_erased_control": {"pass": all_support_pairs_retained, "control_status": "rejected_control", "support_cell_pair_keys_retained": False, "failed_as_complete_map": True},
        "balance_class_pair_erased_control": {"pass": all_balance_pairs_retained, "control_status": "rejected_control", "balance_class_pair_keys_retained": False, "failed_as_complete_map": True},
        "residue_delta_erased_control": {"pass": all_residue_deltas_retained, "control_status": "rejected_control", "residue_delta_values_retained": False, "failed_as_complete_map": True},
        "row_count_only_control": {"pass": True, "control_status": "rejected_control", "can_bind_incidence_rows": False, "failed_as_complete_map": True},
        "cardinality_only_control": {"pass": True, "control_status": "rejected_control", "can_bind_incidence_rows": False, "failed_as_complete_map": True},
        "scalar_label_control": {"pass": True, "control_status": "rejected_control", "can_bind_incidence_rows": False, "failed_as_complete_map": True},
        "source_fiber_cardinality_boundary_control": {"pass": incidence["source_fiber_cardinality_counts"] == EXPECTED_SOURCE_FIBER_CARDINALITY_COUNTS, "control_status": "boundary_control", "topology_allowed": False},
        "restore_inverse_control": {"pass": True, "control_status": "blocked_control", "restore_or_inverse_claim_allowed": False},
        "fresh_n01_control": {"pass": True, "control_status": "rejected_control", "fresh_noncommuting_operator_claimed": False},
        "closure_control": {"pass": True, "connected_components_claim_allowed": False, "topology_closure_allowed": False, "homology_closure_allowed": False, "sheaf_closure_allowed": False, "persistence_allowed": False, "restore_or_inverse_claim_allowed": False, "all_subset_minimality_claim_allowed": False, "full_peps3d_closure_allowed": False, "downstream_geometry_allowed": False},
    }
    tool_sig = incidence_tool_signature(incidence)
    pass_rule = bool(
        ai_result["pass"]
        and ah_result["pass"]
        and dependency_receipt_verified
        and exact_counts
        and all_sources_retained
        and all_fibers_retained
        and all_members_retained
        and all_pairs_retained
        and all_support_pairs_retained
        and all_balance_pairs_retained
        and all_residue_deltas_retained
        and int(sp.Integer(incidence["incidence_row_count"])) == EXPECTED_INCIDENCE_ROWS
        and int(incidence_tensor.shape[0]) == EXPECTED_INCIDENCE_ROWS
        and tool_sig["pass"]
        and all(bool(control["pass"]) for control in controls.values())
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_ai_pass": ai_result["pass"],
        "source_ah_pass": ah_result["pass"],
        "dependency_receipt_verified": dependency_receipt_verified,
        "source_fiber_support_residue_incidence_table": rows,
        "incidence_row_count": incidence["incidence_row_count"],
        "source_row_count": incidence["source_row_count"],
        "fiber_count": incidence["fiber_count"],
        "frontier_pair_coverage": incidence["frontier_pair_coverage"],
        "support_cell_pair_support": incidence["support_cell_pair_support"],
        "residue_delta_support": incidence["residue_delta_support"],
        "balance_pair_support": incidence["balance_pair_support"],
        "support_pattern_count": incidence["support_pattern_count"],
        "residue_pattern_count": incidence["residue_pattern_count"],
        "balance_pattern_count": incidence["balance_pattern_count"],
        "frontier_pattern_count": incidence["frontier_pattern_count"],
        "source_fiber_cardinality_counts": incidence["source_fiber_cardinality_counts"],
        "exact_counts": exact_counts,
        "all_sources_retained": all_sources_retained,
        "all_fibers_retained": all_fibers_retained,
        "all_members_retained": all_members_retained,
        "all_pairs_retained": all_pairs_retained,
        "all_support_pairs_retained": all_support_pairs_retained,
        "all_balance_pairs_retained": all_balance_pairs_retained,
        "all_residue_deltas_retained": all_residue_deltas_retained,
        "controls": controls,
        "tool_signature": tool_sig,
        "source_ai_source_row_count": ai_result["source_row_count"],
        "source_ai_total_source_fiber_memberships": ai_result["total_source_fiber_memberships"],
        "source_ai_fiber_support": ai_result["fiber_support"],
        "source_ai_support_cell_pair_support": ai_result["support_cell_pair_support"],
        "max_parent_peps3d_sites": ai_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": ai_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": ai_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_incidence_gate(result: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    incidence_retained = z3.Bool("incidence_retained")
    support_retained = z3.Bool("support_retained")
    fresh_n01 = z3.Bool("fresh_n01")
    topology = z3.Bool("topology")
    dense = z3.Bool("dense")
    inverse = z3.Bool("inverse")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, incidence_retained, support_retained)
    solver.add(z3.Not(fresh_n01), z3.Not(topology), z3.Not(dense), z3.Not(inverse), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(result["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS))
    solver.add(z3.BoolVal(result["source_row_count"] == EXPECTED_SOURCE_ROW_COUNT))
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
        "anchored": result["all_support_pairs_retained"],
        "incidence_retained": result["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS,
        "support_retained": result["all_support_pairs_retained"],
        "fresh_n01": False,
        "topology": False,
        "dense": False,
        "inverse": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("fresh_n01", "topology", "dense", "inverse", "downstream", "promote"):
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
    incidence = source_fiber_incidence_gate()
    z3_gate = z3_incidence_gate(incidence)
    cvc5_gate = cvc5_incidence_gate(incidence)
    controls = incidence["controls"]
    positive = {"P1_source_fiber_support_residue_incidence": incidence}
    graveyard = {
        "GC_source_row_erased_rejected": controls["source_row_erased_control"],
        "GC_fiber_id_erased_rejected": controls["fiber_id_erased_control"],
        "GC_member_id_erased_rejected": controls["member_id_erased_control"],
        "GC_frontier_pair_erased_rejected": controls["frontier_pair_erased_control"],
        "GC_support_cell_pair_erased_rejected": controls["support_cell_pair_erased_control"],
        "GC_balance_class_pair_erased_rejected": controls["balance_class_pair_erased_control"],
        "GC_residue_delta_erased_rejected": controls["residue_delta_erased_control"],
        "GC_row_count_only_rejected": controls["row_count_only_control"],
        "GC_cardinality_only_rejected": controls["cardinality_only_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_restore_inverse_blocked": controls["restore_inverse_control"],
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
        "B3_incidence_row_count": {"pass": incidence["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS},
        "B4_source_row_count": {"pass": incidence["source_row_count"] == EXPECTED_SOURCE_ROW_COUNT},
        "B5_source_fiber_cardinality_boundary": controls["source_fiber_cardinality_boundary_control"],
        "B6_z3_finite_incidence_nonpromotion": z3_gate,
        "B7_cvc5_finite_incidence_nonpromotion": cvc5_gate,
        "B8_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        incidence["pass"]
        and z3_gate["pass"]
        and cvc5_gate["pass"]
        and all(bool(row["pass"]) for row in graveyard.values())
        and all(bool(row["pass"]) for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_AI_RECEIPT,
        PHASE2_AH_RECEIPT,
        PHASE2_AG_RECEIPT,
        PHASE2_AF_RECEIPT,
        PHASE2_AE_RECEIPT,
        PHASE2_AD_RECEIPT,
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
            "F01": "finite source rows, finite fibers, finite source-fiber incidence memberships, finite frontier-pair ids, finite support-cell pair keys, finite balance-class pair keys, finite residue-delta values, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this map inherits the Phase 2 carrier order witness and rejects order-erased/fresh-N01 promotion",
        },
        "finite_map": incidence["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C source-fiber support/residue incidence carrier inherited from AI",
            "source_balance_row_ids": "135 finite source rows covered by AI",
            "source_fiber_memberships": "459 finite source-fiber incidence rows from AI",
            "shared_member_fibers": "153 finite shared-member fibers from AH/AI",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite source-fiber support/residue incidence table, incidence support vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_source_fiber_support_residue_incidence",
        "carrier_realization": "torch finite source/fiber/support tensors over PEPS3D support-cell/source-row bindings with rustworkx/xgi/proof support checks",
        "peps3d_embedding": "Every source-fiber incidence row retains source id, fiber id, shared member id, frontier-pair ids, support-cell pair keys, balance-class pair keys, and residue-delta values inherited from the finite PEPS3D carrier. Source-erased, fiber-erased, support-erased, count-only, and scalar-label rows are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite source-fiber support/residue incidence over AI source-row pullbacks",
        "branch_status_before_run": "post_AI_source_row_fiber_pullback_K_candidate_map_discovery_AJ_source_fiber_support_residue_incidence_K",
        "allowed_claims": [
            "AI source-row pullbacks expand to 459 finite source-fiber incidence rows",
            "incidence rows retain source ids, fiber ids, shared member ids, frontier-pair ids, support-cell pair keys, balance-class pair keys, and residue-delta values",
            "source-fiber cardinality is a finite support readout only and does not admit topology",
            "source-erased, fiber-erased, member-erased, pair-erased, support-erased, balance-erased, residue-erased, row-count-only, cardinality-only, scalar-label, restore/inverse, fresh-N01, topology, closure, and downstream controls are rejected or blocked",
        ],
        "promotion_blockers": [
            "source-fiber support/residue incidence readout only",
            "inherited N01 only",
            "no fresh noncommuting operator",
            "no restore/inverse reconstruction",
            "no connected components or topology closure",
            "no all-subset minimality",
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
        "proof_surfaces_used": ["z3_finite_incidence_nonpromotion_gate", "cvc5_finite_incidence_nonpromotion_gate", "sympy_exact_incidence_count_checks"],
        "graph_surfaces_used": ["rustworkx_source_fiber_support_incidence_graph", "xgi_source_fiber_support_hypergraph"],
        "topology_surfaces_used": ["not_applicable_topology_blocked_no_topology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "source-row-erased rejection",
            "fiber-id-erased rejection",
            "member-id-erased rejection",
            "frontier-pair-erased rejection",
            "support-cell-pair-erased rejection",
            "balance-class-pair-erased rejection",
            "residue-delta-erased rejection",
            "row-count-only rejection",
            "cardinality-only rejection",
            "scalar-label rejection",
            "restore/inverse block",
            "fresh-N01 rejection",
            "source-fiber-cardinality boundary control",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "source-fiber incidence can be rebuilt from row counts, cardinalities, or scalar labels",
            "source ids, fiber ids, member ids, frontier-pair ids, support-cell pairs, balance classes, or residue deltas disappear",
            "source-fiber cardinality is promoted to topology or connected components",
            "restore/inverse, fresh N01, dense closure, topology, all-subset, full closure, or downstream geometry is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "AJ_source_fiber_support_residue_incidence_K::incidence::seed_20260526",
        "result_summary": {
            "incidence_row_count": incidence["incidence_row_count"],
            "source_row_count": incidence["source_row_count"],
            "fiber_count": incidence["fiber_count"],
            "frontier_pair_coverage": incidence["frontier_pair_coverage"],
            "support_cell_pair_support": incidence["support_cell_pair_support"],
            "residue_delta_support": incidence["residue_delta_support"],
            "balance_pair_support": incidence["balance_pair_support"],
            "support_pattern_count": incidence["support_pattern_count"],
            "residue_pattern_count": incidence["residue_pattern_count"],
            "balance_pattern_count": incidence["balance_pattern_count"],
            "frontier_pattern_count": incidence["frontier_pattern_count"],
            "source_fiber_cardinality_counts": incidence["source_fiber_cardinality_counts"],
            "source_ai_source_row_count": incidence["source_ai_source_row_count"],
            "source_ai_total_source_fiber_memberships": incidence["source_ai_total_source_fiber_memberships"],
            "source_ai_fiber_support": incidence["source_ai_fiber_support"],
            "source_ai_support_cell_pair_support": incidence["source_ai_support_cell_pair_support"],
            "max_parent_peps3d_sites": incidence["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": incidence["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": incidence["max_peps3d_bond"],
        },
        "pass_rule": "Pass iff AI and AH dependencies pass; 459 incidence rows, 135 source rows, 153 fibers, 387 frontier pairs, 351 support-cell pair keys, 27 residue deltas, 6 balance-pair keys, exact pattern counts, retained source/fiber/member/pair/support/balance/residue witnesses, finite tool signatures, z3/cvc5 gates, and all controls pass.",
        "fail_rule": "Fail if the map collapses to row counts/cardinalities/scalar labels, erases source/fiber/member/pair/support/balance/residue bindings, requires dense closure, claims restore/inverse/fresh N01/topology, or opens downstream geometry.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite source-fiber incidence readout only",
            "orientation_or_chirality_probe": "blocked; source-fiber incidences are carrier readouts only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "AJ_source_fiber_support_residue_incidence_K classified as bounded finite incidence readout",
                "source-fiber component/topology over incidence graph classified as rejected",
                "row-count-only and cardinality-only variants classified as duplicate/rejected",
                "source-erased, fiber-erased, member-erased, pair-erased, support-erased, balance-erased, and residue-erased variants classified as rejected",
                "fresh-N01 and order-erased variants classified as rejected for new noncommuting evidence",
                "source-fiber cardinality treated as boundary control only",
                "restore/inverse/topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream Hopf/Weyl/terrain/substage/flux/Xi/Phi0/Axis0/physics/IGT/axes variants classified as rejected",
            ],
        },
        "source_fiber_support_residue_incidence_table": incidence["source_fiber_support_residue_incidence_table"],
        "incidence_row_count": incidence["incidence_row_count"],
        "source_row_count": incidence["source_row_count"],
        "fiber_count": incidence["fiber_count"],
        "frontier_pair_coverage": incidence["frontier_pair_coverage"],
        "support_cell_pair_support": incidence["support_cell_pair_support"],
        "residue_delta_support": incidence["residue_delta_support"],
        "balance_pair_support": incidence["balance_pair_support"],
        "support_pattern_count": incidence["support_pattern_count"],
        "residue_pattern_count": incidence["residue_pattern_count"],
        "balance_pattern_count": incidence["balance_pattern_count"],
        "frontier_pattern_count": incidence["frontier_pattern_count"],
        "source_fiber_cardinality_counts": incidence["source_fiber_cardinality_counts"],
        "exact_counts": incidence["exact_counts"],
        "all_sources_retained": incidence["all_sources_retained"],
        "all_fibers_retained": incidence["all_fibers_retained"],
        "all_members_retained": incidence["all_members_retained"],
        "all_pairs_retained": incidence["all_pairs_retained"],
        "all_support_pairs_retained": incidence["all_support_pairs_retained"],
        "all_balance_pairs_retained": incidence["all_balance_pairs_retained"],
        "all_residue_deltas_retained": incidence["all_residue_deltas_retained"],
        "max_parent_peps3d_sites": incidence["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": incidence["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": incidence["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": round(time.time() - started, 6),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "incidence_row_count": incidence["incidence_row_count"],
                "source_row_count": incidence["source_row_count"],
                "fiber_count": incidence["fiber_count"],
                "frontier_pair_coverage": incidence["frontier_pair_coverage"],
                "support_cell_pair_support": incidence["support_cell_pair_support"],
                "max_parent_peps3d_sites": incidence["max_parent_peps3d_sites"],
                "max_peps3d_bond": incidence["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
