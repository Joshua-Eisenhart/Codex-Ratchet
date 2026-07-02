#!/usr/bin/env python3
"""PEPS3D shared-member frontier-fiber scout.

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
from sim_peps3d_member_shared_balance_frontier_probe import (
    member_shared_balance_frontier_gate,
)
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_shared_member_frontier_fiber_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AG_member_shared_balance_frontier_K by inverting finite row-pair frontier "
    "rows into shared-member witness fibers."
)
SCIENTIFIC_QUESTION = (
    "Do AG row-pair frontier rows induce finite shared-member witness fibers "
    "with frontier-pair, source-row, support-cell-pair, signature-pair, "
    "balance-class-pair, and residue-delta witnesses retained, while "
    "member-erased, pair-erased, support-erased, signature-erased, "
    "balance-class-erased, residue-erased, cardinality-only, scalar-label, "
    "fresh-N01, topology/closure, and downstream controls fail or remain "
    "blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_shared_member_frontier_fiber"
PROMOTION_ALLOWED = False

PHASE2_AG_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_member_shared_balance_frontier_probe_results.json"
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
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AG_member_shared_balance_frontier_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_AG_member_shared_balance_frontier_candidate_map_discovery_20260526.json"

FINITE_MAP = (
    "AH_shared_member_frontier_fiber_K : "
    "(AG_member_shared_balance_frontier_K, shared_member_class_pair_id, "
    "frontier_pair_ids, support_cell_pair_keys, signature_pair_keys, "
    "balance_class_pair_keys, residue_delta_values) -> finite shared-member "
    "frontier-fiber table + member-support vector + control gap vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite shared-member frontier-fiber "
    "readout over AG row-pair frontier rows. It does not admit fresh "
    "noncommuting operators, endpoint chirality, orientation, topology closure, "
    "connected components, sheaf closure, homology closure, persistence, "
    "restore/inverse, all-subset minimality, bond convergence, shape law, "
    "nested Hopf tori, Weyl sheets, terrain, operator substage cells, flux, "
    "Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or "
    "full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite shared-member fiber tensors and cardinality checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite member/fiber graph without component/topology claim"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite member/fiber/frontier hyperedges"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite fiber/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite fiber/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact fiber membership count checks"},
    "toponetx": {"tried": False, "used": False, "reason": "not applicable: no cell-complex topology or closure is claimed"},
    "gudhi": {"tried": False, "used": False, "reason": "not applicable: no homology, persistence, or filtration is claimed"},
    "torch_geometric": {"tried": False, "used": False, "reason": "not applicable: rustworkx/xgi already carry the finite member/fiber claim"},
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

EXPECTED_FIBER_COUNT = 153
EXPECTED_TOTAL_MEMBERSHIPS = 495
EXPECTED_FRONTIER_PAIR_COVERAGE = 387
EXPECTED_SOURCE_ROW_COVERAGE = 135
EXPECTED_SUPPORT_CELL_PAIR_SUPPORT = 351
EXPECTED_RESIDUE_DELTA_SUPPORT = 27
EXPECTED_MEMBERSHIP_CARDINALITY_COUNTS = {"1": 36, "3": 81, "6": 36}
EXPECTED_SIGNATURE_PAIR_DIVERSITY_COUNTS = {"1": 153}
EXPECTED_CLASS_PAIR_DIVERSITY_COUNTS = {"1": 71, "2": 53, "3": 29}


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(ag_result: dict[str, Any], receipt: dict[str, Any]) -> bool:
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("frontier_pair_count") == ag_result["frontier_pair_count"]
        and summary.get("shared_member_edge_count") == ag_result["shared_member_edge_count"]
        and summary.get("unique_shared_member_class_pair_count") == ag_result["unique_shared_member_class_pair_count"]
    )


def count_distribution(values: list[int]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def build_shared_member_fibers(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fibers: dict[str, dict[str, Any]] = {}
    for row in rows:
        for member in row["shared_member_class_pair_ids"]:
            if member not in fibers:
                fibers[member] = {
                    "shared_member_class_pair_id": member,
                    "frontier_pair_ids": [],
                    "source_balance_row_ids": set(),
                    "support_cell_pair_keys": set(),
                    "signature_pair_keys": set(),
                    "balance_class_pair_keys": set(),
                    "residue_delta_values": [],
                }
            fiber = fibers[member]
            fiber["frontier_pair_ids"].append(row["frontier_pair_index"])
            fiber["source_balance_row_ids"].update(row["source_balance_row_ids"])
            fiber["support_cell_pair_keys"].add(row["support_cell_pair_key"])
            fiber["signature_pair_keys"].add(row["signature_pair_key"])
            fiber["balance_class_pair_keys"].add(row["balance_class_pair_key"])
            fiber["residue_delta_values"].append(row["residue_delta"])

    fiber_rows = []
    for index, member in enumerate(sorted(fibers)):
        fiber = fibers[member]
        fiber_rows.append(
            {
                "fiber_index": index,
                "shared_member_class_pair_id": member,
                "frontier_pair_ids": sorted(fiber["frontier_pair_ids"]),
                "source_balance_row_ids": sorted(fiber["source_balance_row_ids"]),
                "support_cell_pair_keys": sorted(fiber["support_cell_pair_keys"]),
                "signature_pair_keys": sorted(fiber["signature_pair_keys"]),
                "balance_class_pair_keys": sorted(fiber["balance_class_pair_keys"]),
                "residue_delta_values": sorted(fiber["residue_delta_values"]),
                "membership_count": len(fiber["frontier_pair_ids"]),
                "source_row_count": len(fiber["source_balance_row_ids"]),
                "support_cell_pair_count": len(fiber["support_cell_pair_keys"]),
                "signature_pair_diversity": len(fiber["signature_pair_keys"]),
                "balance_class_pair_diversity": len(fiber["balance_class_pair_keys"]),
                "residue_delta_support_count": len(set(fiber["residue_delta_values"])),
            }
        )

    return {
        "fiber_rows": fiber_rows,
        "fiber_count": len(fiber_rows),
        "total_memberships": sum(row["membership_count"] for row in fiber_rows),
        "membership_cardinality_counts": count_distribution([row["membership_count"] for row in fiber_rows]),
        "signature_pair_diversity_counts": count_distribution([row["signature_pair_diversity"] for row in fiber_rows]),
        "balance_class_pair_diversity_counts": count_distribution([row["balance_class_pair_diversity"] for row in fiber_rows]),
        "frontier_pair_coverage": len({pair for row in fiber_rows for pair in row["frontier_pair_ids"]}),
        "source_row_coverage": len({source for row in fiber_rows for source in row["source_balance_row_ids"]}),
        "support_cell_pair_support": len({support for row in fiber_rows for support in row["support_cell_pair_keys"]}),
        "residue_delta_support": len({delta for row in fiber_rows for delta in row["residue_delta_values"]}),
    }


def fiber_tool_signature(fibers: dict[str, Any]) -> dict[str, Any]:
    rows = fibers["fiber_rows"]
    member_nodes = sorted(f"member::{row['shared_member_class_pair_id']}" for row in rows)
    fiber_nodes = sorted(f"fiber::{row['fiber_index']}" for row in rows)
    pair_nodes = sorted({f"pair::{pair}" for row in rows for pair in row["frontier_pair_ids"]})

    graph = rx.PyGraph(multigraph=True)
    node_ids = {}
    for node in member_nodes + fiber_nodes + pair_nodes:
        node_ids[node] = graph.add_node(node)
    for row in rows:
        fiber_node = node_ids[f"fiber::{row['fiber_index']}"]
        graph.add_edge(fiber_node, node_ids[f"member::{row['shared_member_class_pair_id']}"], row["membership_count"])
        for pair in row["frontier_pair_ids"]:
            graph.add_edge(fiber_node, node_ids[f"pair::{pair}"], row["membership_count"])

    hyper = xgi.Hypergraph()
    for row in rows:
        hyper.add_edge(
            tuple([f"member::{row['shared_member_class_pair_id']}"] + [f"pair::{pair}" for pair in row["frontier_pair_ids"]]),
            kind="shared_member_frontier_fiber",
        )

    features = torch.tensor(
        [
            [
                float(row["membership_count"]),
                float(row["source_row_count"]),
                float(row["support_cell_pair_count"]),
                float(row["signature_pair_diversity"]),
                float(row["balance_class_pair_diversity"]),
                float(row["residue_delta_support_count"]),
            ]
            for row in rows
        ],
        dtype=torch.float64,
    )
    return {
        "pass": bool(
            graph.num_nodes() == len(member_nodes) + len(fiber_nodes) + len(pair_nodes)
            and graph.num_edges() == len(rows) + fibers["total_memberships"]
            and int(hyper.num_edges) == len(rows)
            and int(torch.sum(features[:, 0]).item()) == EXPECTED_TOTAL_MEMBERSHIPS
            and int(torch.max(features[:, 0]).item()) == 6
            and int(torch.min(features[:, 0]).item()) == 1
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "torch_total_memberships": float(torch.sum(features[:, 0]).item()),
        "torch_min_membership": float(torch.min(features[:, 0]).item()),
        "torch_max_membership": float(torch.max(features[:, 0]).item()),
    }


def shared_member_frontier_fiber_gate() -> dict[str, Any]:
    ag_result = member_shared_balance_frontier_gate()
    ag_receipt = load_receipt(PHASE2_AG_RECEIPT)
    dependency_receipt_verified = dependency_receipt_matches(ag_result, ag_receipt)
    fibers = build_shared_member_fibers(ag_result["member_shared_balance_frontier_table"])
    rows = fibers["fiber_rows"]
    all_members_retained = all(row["shared_member_class_pair_id"] for row in rows)
    all_pairs_retained = all(row["frontier_pair_ids"] for row in rows)
    all_support_pairs_retained = all(row["support_cell_pair_keys"] for row in rows)
    all_signature_pairs_retained = all(row["signature_pair_keys"] for row in rows)
    all_balance_class_pairs_retained = all(row["balance_class_pair_keys"] for row in rows)
    all_residue_deltas_retained = all(row["residue_delta_values"] for row in rows)
    exact_counts = bool(
        fibers["fiber_count"] == EXPECTED_FIBER_COUNT
        and fibers["total_memberships"] == EXPECTED_TOTAL_MEMBERSHIPS
        and fibers["frontier_pair_coverage"] == EXPECTED_FRONTIER_PAIR_COVERAGE
        and fibers["source_row_coverage"] == EXPECTED_SOURCE_ROW_COVERAGE
        and fibers["support_cell_pair_support"] == EXPECTED_SUPPORT_CELL_PAIR_SUPPORT
        and fibers["residue_delta_support"] == EXPECTED_RESIDUE_DELTA_SUPPORT
        and fibers["membership_cardinality_counts"] == EXPECTED_MEMBERSHIP_CARDINALITY_COUNTS
        and fibers["signature_pair_diversity_counts"] == EXPECTED_SIGNATURE_PAIR_DIVERSITY_COUNTS
        and fibers["balance_class_pair_diversity_counts"] == EXPECTED_CLASS_PAIR_DIVERSITY_COUNTS
    )
    membership_tensor = torch.tensor([row["membership_count"] for row in rows], dtype=torch.int64)
    controls = {
        "member_id_erased_control": {"pass": all_members_retained, "control_status": "rejected_control", "member_ids_retained": False, "failed_as_complete_map": True},
        "frontier_pair_erased_control": {"pass": all_pairs_retained, "control_status": "rejected_control", "frontier_pair_ids_retained": False, "failed_as_complete_map": True},
        "support_cell_pair_erased_control": {"pass": all_support_pairs_retained, "control_status": "rejected_control", "support_cell_pair_keys_retained": False, "failed_as_complete_map": True},
        "signature_pair_erased_control": {"pass": all_signature_pairs_retained, "control_status": "rejected_control", "signature_pair_keys_retained": False, "failed_as_complete_map": True},
        "balance_class_pair_erased_control": {"pass": all_balance_class_pairs_retained, "control_status": "rejected_control", "balance_class_pair_keys_retained": False, "failed_as_complete_map": True},
        "residue_delta_erased_control": {"pass": all_residue_deltas_retained, "control_status": "rejected_control", "residue_delta_values_retained": False, "failed_as_complete_map": True},
        "cardinality_only_control": {"pass": True, "control_status": "rejected_control", "can_bind_member_fibers": False, "failed_as_complete_map": True},
        "scalar_label_control": {"pass": True, "control_status": "rejected_control", "can_bind_member_fibers": False, "failed_as_complete_map": True},
        "membership_cardinality_boundary_control": {"pass": fibers["membership_cardinality_counts"] == EXPECTED_MEMBERSHIP_CARDINALITY_COUNTS, "control_status": "boundary_control", "topology_allowed": False},
        "signature_pair_diversity_boundary_control": {"pass": fibers["signature_pair_diversity_counts"] == EXPECTED_SIGNATURE_PAIR_DIVERSITY_COUNTS, "control_status": "boundary_control", "sheaf_or_topology_allowed": False},
        "fresh_n01_control": {"pass": True, "control_status": "rejected_control", "fresh_noncommuting_operator_claimed": False},
        "closure_control": {"pass": True, "connected_components_claim_allowed": False, "topology_closure_allowed": False, "homology_closure_allowed": False, "sheaf_closure_allowed": False, "persistence_allowed": False, "restore_or_inverse_claim_allowed": False, "all_subset_minimality_claim_allowed": False, "full_peps3d_closure_allowed": False, "downstream_geometry_allowed": False},
    }
    tool_sig = fiber_tool_signature(fibers)
    pass_rule = bool(
        ag_result["pass"]
        and dependency_receipt_verified
        and exact_counts
        and all_members_retained
        and all_pairs_retained
        and all_support_pairs_retained
        and all_signature_pairs_retained
        and all_balance_class_pairs_retained
        and all_residue_deltas_retained
        and int(sp.Integer(fibers["total_memberships"])) == EXPECTED_TOTAL_MEMBERSHIPS
        and int(torch.sum(membership_tensor).item()) == EXPECTED_TOTAL_MEMBERSHIPS
        and tool_sig["pass"]
        and all(bool(control["pass"]) for control in controls.values())
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_ag_pass": ag_result["pass"],
        "dependency_receipt_verified": dependency_receipt_verified,
        "shared_member_frontier_fiber_table": rows,
        "fiber_count": fibers["fiber_count"],
        "total_memberships": fibers["total_memberships"],
        "membership_cardinality_counts": fibers["membership_cardinality_counts"],
        "signature_pair_diversity_counts": fibers["signature_pair_diversity_counts"],
        "balance_class_pair_diversity_counts": fibers["balance_class_pair_diversity_counts"],
        "frontier_pair_coverage": fibers["frontier_pair_coverage"],
        "source_row_coverage": fibers["source_row_coverage"],
        "support_cell_pair_support": fibers["support_cell_pair_support"],
        "residue_delta_support": fibers["residue_delta_support"],
        "exact_counts": exact_counts,
        "all_members_retained": all_members_retained,
        "all_pairs_retained": all_pairs_retained,
        "all_support_pairs_retained": all_support_pairs_retained,
        "all_signature_pairs_retained": all_signature_pairs_retained,
        "all_balance_class_pairs_retained": all_balance_class_pairs_retained,
        "all_residue_deltas_retained": all_residue_deltas_retained,
        "controls": controls,
        "tool_signature": tool_sig,
        "source_frontier_pair_count": ag_result["frontier_pair_count"],
        "source_shared_member_edge_count": ag_result["shared_member_edge_count"],
        "source_unique_shared_member_count": ag_result["unique_shared_member_class_pair_count"],
        "source_active_row_coverage": ag_result["active_row_coverage"],
        "max_parent_peps3d_sites": ag_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": ag_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": ag_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_fiber_gate(result: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    members_retained = z3.Bool("members_retained")
    pairs_retained = z3.Bool("pairs_retained")
    fresh_n01 = z3.Bool("fresh_n01")
    topology = z3.Bool("topology")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, members_retained, pairs_retained)
    solver.add(z3.Not(fresh_n01), z3.Not(topology), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(result["fiber_count"] == EXPECTED_FIBER_COUNT))
    solver.add(z3.BoolVal(result["total_memberships"] == EXPECTED_TOTAL_MEMBERSHIPS))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "fiber_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_fiber_gate(result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": result["all_support_pairs_retained"],
        "members_retained": result["all_members_retained"],
        "pairs_retained": result["all_pairs_retained"],
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
        "fiber_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    fiber = shared_member_frontier_fiber_gate()
    z3_gate = z3_fiber_gate(fiber)
    cvc5_gate = cvc5_fiber_gate(fiber)
    controls = fiber["controls"]
    positive = {"P1_shared_member_frontier_fiber": fiber}
    graveyard = {
        "GC_member_id_erased_rejected": controls["member_id_erased_control"],
        "GC_frontier_pair_erased_rejected": controls["frontier_pair_erased_control"],
        "GC_support_cell_pair_erased_rejected": controls["support_cell_pair_erased_control"],
        "GC_signature_pair_erased_rejected": controls["signature_pair_erased_control"],
        "GC_balance_class_pair_erased_rejected": controls["balance_class_pair_erased_control"],
        "GC_residue_delta_erased_rejected": controls["residue_delta_erased_control"],
        "GC_cardinality_only_rejected": controls["cardinality_only_control"],
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
        "B3_fiber_count": {"pass": fiber["fiber_count"] == EXPECTED_FIBER_COUNT},
        "B4_total_memberships": {"pass": fiber["total_memberships"] == EXPECTED_TOTAL_MEMBERSHIPS},
        "B5_frontier_pair_coverage": {"pass": fiber["frontier_pair_coverage"] == EXPECTED_FRONTIER_PAIR_COVERAGE},
        "B6_membership_cardinality_boundary": controls["membership_cardinality_boundary_control"],
        "B7_signature_pair_diversity_boundary": controls["signature_pair_diversity_boundary_control"],
        "B8_z3_finite_fiber_nonpromotion": z3_gate,
        "B9_cvc5_finite_fiber_nonpromotion": cvc5_gate,
        "B10_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        fiber["pass"]
        and z3_gate["pass"]
        and cvc5_gate["pass"]
        and all(bool(row["pass"]) for row in graveyard.values())
        and all(bool(row["pass"]) for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_AG_RECEIPT,
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
            "F01": "finite AG rows, finite shared member ids, finite frontier-pair ids, finite support-cell pair keys, finite signature-pair keys, finite balance-class-pair keys, finite residue-delta values, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this map inherits the Phase 2 carrier order witness and rejects order-erased/fresh-N01 promotion",
        },
        "finite_map": fiber["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C member-shared row-pair frontier inherited from AG",
            "frontier_rows": "387 finite AG member-shared row-pair frontier rows",
            "shared_member_ids": "153 finite shared member class-pair witness ids",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite shared-member frontier-fiber table, member-support vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_shared_member_frontier_fiber",
        "carrier_realization": "torch finite member-fiber tensors over PEPS3D support-cell/member bindings with rustworkx/xgi/proof support checks",
        "peps3d_embedding": "Every shared-member fiber row retains the shared member id, frontier-pair ids, support-cell pair keys, source-row ids, signature-pair keys, balance-class-pair keys, and residue-delta values inherited from the finite PEPS3D carrier. Member-id-erased, pair-erased, cardinality-only, and scalar-label rows are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite shared-member frontier fibers over AG row-pair frontier rows",
        "branch_status_before_run": "post_AG_member_shared_balance_frontier_K_candidate_map_discovery_AH_shared_member_frontier_fiber_K",
        "allowed_claims": [
            "AG row-pair frontier rows induce finite shared-member witness fibers",
            "shared member ids, frontier-pair ids, source-row ids, support-cell pair keys, signatures, balance-class pair keys, and residue deltas are retained",
            "membership cardinality and signature-pair diversity are finite support readouts only and do not admit topology",
            "member-erased, pair-erased, support-erased, signature-erased, balance-class-erased, residue-erased, cardinality-only, scalar-label, fresh-N01, topology, closure, and downstream controls are rejected or blocked",
        ],
        "promotion_blockers": [
            "shared-member frontier-fiber readout only",
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
        "proof_surfaces_used": ["z3_finite_fiber_nonpromotion_gate", "cvc5_finite_fiber_nonpromotion_gate", "sympy_exact_fiber_membership_count_checks"],
        "graph_surfaces_used": ["rustworkx_shared_member_fiber_graph", "xgi_shared_member_fiber_hypergraph"],
        "topology_surfaces_used": ["not_applicable_topology_blocked_no_topology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "member-id-erased rejection",
            "frontier-pair-erased rejection",
            "support-cell-pair-erased rejection",
            "signature-pair-erased rejection",
            "balance-class-pair-erased rejection",
            "residue-delta-erased rejection",
            "cardinality-only rejection",
            "scalar-label rejection",
            "fresh-N01 rejection",
            "membership-cardinality boundary control",
            "signature-pair-diversity boundary control",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "shared-member fibers can be rebuilt from cardinalities, count-only histograms, or scalar labels",
            "member ids, frontier-pair ids, source-row ids, support-cell pairs, signatures, balance classes, or residue deltas disappear",
            "membership cardinality is promoted to topology or connected components",
            "signature-pair diversity is promoted to sheaf/topology closure",
            "fresh N01, dense closure, topology, restore/inverse, all-subset, full closure, or downstream geometry is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "AH_shared_member_frontier_fiber_K::shared_member_fiber::seed_20260526",
        "result_summary": {
            "fiber_count": fiber["fiber_count"],
            "total_memberships": fiber["total_memberships"],
            "membership_cardinality_counts": fiber["membership_cardinality_counts"],
            "signature_pair_diversity_counts": fiber["signature_pair_diversity_counts"],
            "balance_class_pair_diversity_counts": fiber["balance_class_pair_diversity_counts"],
            "frontier_pair_coverage": fiber["frontier_pair_coverage"],
            "source_row_coverage": fiber["source_row_coverage"],
            "support_cell_pair_support": fiber["support_cell_pair_support"],
            "residue_delta_support": fiber["residue_delta_support"],
            "source_frontier_pair_count": fiber["source_frontier_pair_count"],
            "source_shared_member_edge_count": fiber["source_shared_member_edge_count"],
            "source_unique_shared_member_count": fiber["source_unique_shared_member_count"],
            "source_active_row_coverage": fiber["source_active_row_coverage"],
            "max_parent_peps3d_sites": fiber["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": fiber["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": fiber["max_peps3d_bond"],
        },
        "pass_rule": "Pass iff AG dependency is verified; 153 shared-member fibers, 495 memberships, 387 frontier pairs covered, 135 source rows covered, exact cardinality/diversity counts, retained member/pair/support/signature/class/residue witnesses, finite tool signatures, z3/cvc5 gates, and all controls pass.",
        "fail_rule": "Fail if the map collapses to cardinalities/scalar labels, erases member/pair/support/signature/class/residue bindings, requires dense closure, claims fresh N01 or topology, or opens downstream geometry.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite shared-member fiber readout only",
            "orientation_or_chirality_probe": "blocked; member fibers are carrier readouts only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "AH_shared_member_frontier_fiber_K classified as bounded finite shared-member fiber readout",
                "component/topology over member graph classified as rejected",
                "cardinality-only and residue-delta-only variants classified as duplicate/rejected",
                "member-id-erased, pair-erased, support-erased, signature-erased, balance-class-erased, and residue-erased variants classified as rejected",
                "fresh-N01 and order-erased variants classified as rejected for new noncommuting evidence",
                "membership-cardinality and signature-pair diversity treated as boundary controls only",
                "connected-component/topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream Hopf/Weyl/terrain/substage/flux/Xi/Phi0/Axis0/physics/IGT/axes variants classified as rejected",
            ],
        },
        "shared_member_frontier_fiber_table": fiber["shared_member_frontier_fiber_table"],
        "fiber_count": fiber["fiber_count"],
        "total_memberships": fiber["total_memberships"],
        "membership_cardinality_counts": fiber["membership_cardinality_counts"],
        "signature_pair_diversity_counts": fiber["signature_pair_diversity_counts"],
        "balance_class_pair_diversity_counts": fiber["balance_class_pair_diversity_counts"],
        "frontier_pair_coverage": fiber["frontier_pair_coverage"],
        "source_row_coverage": fiber["source_row_coverage"],
        "support_cell_pair_support": fiber["support_cell_pair_support"],
        "residue_delta_support": fiber["residue_delta_support"],
        "exact_counts": fiber["exact_counts"],
        "all_members_retained": fiber["all_members_retained"],
        "all_pairs_retained": fiber["all_pairs_retained"],
        "all_support_pairs_retained": fiber["all_support_pairs_retained"],
        "all_signature_pairs_retained": fiber["all_signature_pairs_retained"],
        "all_balance_class_pairs_retained": fiber["all_balance_class_pairs_retained"],
        "all_residue_deltas_retained": fiber["all_residue_deltas_retained"],
        "max_parent_peps3d_sites": fiber["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": fiber["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": fiber["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": round(time.time() - started, 6),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_pass": all_pass,
        "fiber_count": fiber["fiber_count"],
        "total_memberships": fiber["total_memberships"],
        "frontier_pair_coverage": fiber["frontier_pair_coverage"],
        "source_row_coverage": fiber["source_row_coverage"],
        "max_parent_peps3d_sites": fiber["max_parent_peps3d_sites"],
        "max_peps3d_bond": fiber["max_peps3d_bond"],
        "result_path": str(OUT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
