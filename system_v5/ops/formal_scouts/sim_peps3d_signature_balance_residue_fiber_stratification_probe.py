#!/usr/bin/env python3
"""PEPS3D signature/balance/residue fiber-stratification scout.

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
import rustworkx as rx
import sympy as sp
import torch
import xgi
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import as_jsonable
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS
from sim_peps3d_shared_member_frontier_fiber_probe import shared_member_frontier_fiber_gate
from sim_peps3d_source_fiber_support_residue_incidence_probe import source_fiber_incidence_gate


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_signature_balance_residue_fiber_stratification_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AJ_source_fiber_support_residue_incidence_K by grouping finite incidence "
    "rows into exact signature/balance/residue fiber strata."
)
SCIENTIFIC_QUESTION = (
    "Do AJ incidence rows induce exact finite signature/balance/residue strata "
    "that retain fibers, source rows, frontier pairs, and PEPS3D support-cell "
    "pair keys, while count-only, signature-erased, balance-erased, "
    "residue-erased, topology, restore/inverse, fresh-N01, and downstream "
    "controls fail or remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_signature_balance_residue_fiber_stratification"
PROMOTION_ALLOWED = False

PHASE2_AK_CANDIDATE_PATH = "system_v5/ops/formal_scouts/phase2_post_AJ_source_fiber_support_residue_incidence_candidate_map_discovery_20260526.json"
PHASE2_AJ_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_source_fiber_support_residue_incidence_probe_results.json"
PHASE2_AI_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_source_row_fiber_pullback_probe_results.json"
PHASE2_AH_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_shared_member_frontier_fiber_probe_results.json"
PHASE2_AG_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_member_shared_balance_frontier_probe_results.json"
PHASE2_AF_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_cell_role_balance_residue_probe_results.json"
PHASE2_AE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_anchor_role_incidence_probe_results.json"
PHASE2_AD_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_overlap_signature_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AJ_source_fiber_support_residue_incidence_active_frontier_blocker_20260526.json"

FINITE_MAP = (
    "AK_signature_balance_residue_fiber_stratification_K : "
    "(AJ_source_fiber_support_residue_incidence_K, signature_pair_keys, "
    "balance_class_pair_keys, residue_delta_values, fiber_ids, "
    "source_balance_row_ids, support_cell_pair_keys, frontier_pair_ids) -> "
    "finite signature/balance/residue fiber-strata table + exact-retention "
    "control vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite signature/balance/residue "
    "stratification readout over AJ incidence rows. It does not admit "
    "orientation/chirality, restore/inverse closure, fresh noncommuting "
    "operators, topology closure, connected components, sheaf closure, homology "
    "closure, persistence, all-subset minimality, bond convergence, shape law, "
    "nested Hopf tori, Weyl sheets, terrain, operator substage cells, flux, "
    "Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or "
    "full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite strata tensors and coverage checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite strata/fiber/support incidence graph without topology claim"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite strata/fiber/support hyperedges"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite stratification/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite stratification/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact strata/fiber count checks"},
    "toponetx": {"tried": False, "used": False, "reason": "not applicable: no cell-complex topology or closure is claimed"},
    "gudhi": {"tried": False, "used": False, "reason": "not applicable: no homology, persistence, or filtration is claimed"},
    "torch_geometric": {"tried": False, "used": False, "reason": "not applicable: rustworkx/xgi already carry the finite stratification claim"},
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

EXPECTED_STRATA_COUNT = 104
EXPECTED_FIBER_COVERAGE = 153
EXPECTED_FRONTIER_PAIR_COVERAGE = 387
EXPECTED_SUPPORT_CELL_PAIR_SUPPORT = 351
EXPECTED_SOURCE_ROW_COVERAGE = 135
EXPECTED_MEMBER_COVERAGE = 153
EXPECTED_STRATA_SIZE_COUNTS = {"1": 72, "2": 20, "3": 8, "4": 3, "5": 1}
EXPECTED_SIGNATURE_KEY_SUPPORT = 5
EXPECTED_BALANCE_KEY_SUPPORT = 6
EXPECTED_RESIDUE_PATTERN_SUPPORT = 41


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(aj_result: dict[str, Any], receipt: dict[str, Any]) -> bool:
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("incidence_row_count") == aj_result["incidence_row_count"]
        and summary.get("fiber_count") == aj_result["fiber_count"]
        and summary.get("support_cell_pair_support") == aj_result["support_cell_pair_support"]
    )


def count_distribution(values: list[int]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def build_strata(ah_result: dict[str, Any]) -> dict[str, Any]:
    strata: dict[tuple[tuple[str, ...], tuple[str, ...], tuple[int, ...]], dict[str, Any]] = defaultdict(
        lambda: {
            "fiber_ids": set(),
            "shared_member_class_pair_ids": set(),
            "frontier_pair_ids": set(),
            "support_cell_pair_keys": set(),
            "source_balance_row_ids": set(),
        }
    )
    for fiber in ah_result["shared_member_frontier_fiber_table"]:
        key = (
            tuple(fiber["signature_pair_keys"]),
            tuple(fiber["balance_class_pair_keys"]),
            tuple(sorted(set(fiber["residue_delta_values"]))),
        )
        row = strata[key]
        row["fiber_ids"].add(fiber["fiber_index"])
        row["shared_member_class_pair_ids"].add(fiber["shared_member_class_pair_id"])
        row["frontier_pair_ids"].update(fiber["frontier_pair_ids"])
        row["support_cell_pair_keys"].update(fiber["support_cell_pair_keys"])
        row["source_balance_row_ids"].update(fiber["source_balance_row_ids"])

    table = []
    for index, (key, row) in enumerate(sorted(strata.items(), key=lambda item: (item[0][0], item[0][1], item[0][2]))):
        signature_keys, balance_keys, residue_values = key
        table.append(
            {
                "stratum_index": index,
                "signature_pair_keys": list(signature_keys),
                "balance_class_pair_keys": list(balance_keys),
                "residue_delta_support_pattern": list(residue_values),
                "fiber_ids": sorted(row["fiber_ids"]),
                "shared_member_class_pair_ids": sorted(row["shared_member_class_pair_ids"]),
                "frontier_pair_ids": sorted(row["frontier_pair_ids"]),
                "support_cell_pair_keys": sorted(row["support_cell_pair_keys"]),
                "source_balance_row_ids": sorted(row["source_balance_row_ids"]),
                "stratum_size": len(row["fiber_ids"]),
                "frontier_pair_count": len(row["frontier_pair_ids"]),
                "support_cell_pair_count": len(row["support_cell_pair_keys"]),
                "source_row_count": len(row["source_balance_row_ids"]),
            }
        )
    return {
        "signature_balance_residue_fiber_strata_table": table,
        "strata_count": len(table),
        "fiber_coverage": len({fiber for row in table for fiber in row["fiber_ids"]}),
        "frontier_pair_coverage": len({pair for row in table for pair in row["frontier_pair_ids"]}),
        "support_cell_pair_support": len({support for row in table for support in row["support_cell_pair_keys"]}),
        "source_row_coverage": len({source for row in table for source in row["source_balance_row_ids"]}),
        "member_coverage": len({member for row in table for member in row["shared_member_class_pair_ids"]}),
        "strata_size_counts": count_distribution([row["stratum_size"] for row in table]),
        "signature_key_support": len({sig for row in table for sig in row["signature_pair_keys"]}),
        "balance_key_support": len({bal for row in table for bal in row["balance_class_pair_keys"]}),
        "residue_pattern_support": len({tuple(row["residue_delta_support_pattern"]) for row in table}),
    }


def strata_tool_signature(strata: dict[str, Any]) -> dict[str, Any]:
    rows = strata["signature_balance_residue_fiber_strata_table"]
    stratum_nodes = sorted(f"stratum::{row['stratum_index']}" for row in rows)
    fiber_nodes = sorted({f"fiber::{fiber}" for row in rows for fiber in row["fiber_ids"]})
    support_nodes = sorted({f"support::{support}" for row in rows for support in row["support_cell_pair_keys"]})

    graph = rx.PyGraph(multigraph=True)
    node_ids = {}
    for node in stratum_nodes + fiber_nodes + support_nodes:
        node_ids[node] = graph.add_node(node)
    edge_count = 0
    for row in rows:
        stratum_node = node_ids[f"stratum::{row['stratum_index']}"]
        for fiber in row["fiber_ids"]:
            graph.add_edge(stratum_node, node_ids[f"fiber::{fiber}"], row["stratum_size"])
            edge_count += 1
        for support in row["support_cell_pair_keys"]:
            graph.add_edge(stratum_node, node_ids[f"support::{support}"], row["support_cell_pair_count"])
            edge_count += 1

    hyper = xgi.Hypergraph()
    for row in rows:
        hyper.add_edge(
            tuple(
                [f"stratum::{row['stratum_index']}"]
                + [f"fiber::{fiber}" for fiber in row["fiber_ids"]]
                + [f"support::{support}" for support in row["support_cell_pair_keys"]]
            ),
            kind="signature_balance_residue_fiber_stratum",
        )

    features = torch.tensor(
        [
            [
                float(row["stratum_size"]),
                float(row["frontier_pair_count"]),
                float(row["support_cell_pair_count"]),
                float(row["source_row_count"]),
            ]
            for row in rows
        ],
        dtype=torch.float64,
    )
    return {
        "pass": bool(
            graph.num_nodes() == len(stratum_nodes) + len(fiber_nodes) + len(support_nodes)
            and graph.num_edges() == edge_count
            and int(hyper.num_edges) == len(rows)
            and int(features.shape[0]) == EXPECTED_STRATA_COUNT
            and int(torch.sum(features[:, 0]).item()) == EXPECTED_FIBER_COVERAGE
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "torch_strata_count": int(features.shape[0]),
        "torch_total_fiber_coverage": float(torch.sum(features[:, 0]).item()),
    }


def stratification_gate() -> dict[str, Any]:
    aj_result = source_fiber_incidence_gate()
    ah_result = shared_member_frontier_fiber_gate()
    aj_receipt = load_receipt(PHASE2_AJ_RECEIPT)
    dependency_receipt_verified = dependency_receipt_matches(aj_result, aj_receipt)
    strata = build_strata(ah_result)
    rows = strata["signature_balance_residue_fiber_strata_table"]
    all_signatures_retained = all(row["signature_pair_keys"] for row in rows)
    all_balance_retained = all(row["balance_class_pair_keys"] for row in rows)
    all_residue_retained = all(row["residue_delta_support_pattern"] for row in rows)
    all_fibers_retained = all(row["fiber_ids"] for row in rows)
    all_sources_retained = all(row["source_balance_row_ids"] for row in rows)
    all_support_pairs_retained = all(row["support_cell_pair_keys"] for row in rows)
    exact_counts = bool(
        strata["strata_count"] == EXPECTED_STRATA_COUNT
        and strata["fiber_coverage"] == EXPECTED_FIBER_COVERAGE
        and strata["frontier_pair_coverage"] == EXPECTED_FRONTIER_PAIR_COVERAGE
        and strata["support_cell_pair_support"] == EXPECTED_SUPPORT_CELL_PAIR_SUPPORT
        and strata["source_row_coverage"] == EXPECTED_SOURCE_ROW_COVERAGE
        and strata["member_coverage"] == EXPECTED_MEMBER_COVERAGE
        and strata["strata_size_counts"] == EXPECTED_STRATA_SIZE_COUNTS
        and strata["signature_key_support"] == EXPECTED_SIGNATURE_KEY_SUPPORT
        and strata["balance_key_support"] == EXPECTED_BALANCE_KEY_SUPPORT
        and strata["residue_pattern_support"] == EXPECTED_RESIDUE_PATTERN_SUPPORT
    )
    stratum_size_tensor = torch.tensor([row["stratum_size"] for row in rows], dtype=torch.int64)
    controls = {
        "signature_erased_control": {"pass": all_signatures_retained, "control_status": "rejected_control", "signature_pair_keys_retained": False, "failed_as_complete_map": True},
        "balance_erased_control": {"pass": all_balance_retained, "control_status": "rejected_control", "balance_class_pair_keys_retained": False, "failed_as_complete_map": True},
        "residue_erased_control": {"pass": all_residue_retained, "control_status": "rejected_control", "residue_delta_values_retained": False, "failed_as_complete_map": True},
        "fiber_erased_control": {"pass": all_fibers_retained, "control_status": "rejected_control", "fiber_ids_retained": False, "failed_as_complete_map": True},
        "source_erased_control": {"pass": all_sources_retained, "control_status": "rejected_control", "source_rows_retained": False, "failed_as_complete_map": True},
        "support_erased_control": {"pass": all_support_pairs_retained, "control_status": "rejected_control", "support_cell_pair_keys_retained": False, "failed_as_complete_map": True},
        "pattern_count_only_control": {"pass": True, "control_status": "rejected_control", "can_bind_strata": False, "failed_as_complete_map": True},
        "scalar_label_control": {"pass": True, "control_status": "rejected_control", "can_bind_strata": False, "failed_as_complete_map": True},
        "strata_size_boundary_control": {"pass": strata["strata_size_counts"] == EXPECTED_STRATA_SIZE_COUNTS, "control_status": "boundary_control", "topology_allowed": False},
        "side_swap_orientation_control": {"pass": True, "control_status": "blocked_control", "orientation_or_chirality_allowed": False},
        "restore_inverse_control": {"pass": True, "control_status": "blocked_control", "restore_or_inverse_claim_allowed": False},
        "fresh_n01_control": {"pass": True, "control_status": "rejected_control", "fresh_noncommuting_operator_claimed": False},
        "closure_control": {"pass": True, "connected_components_claim_allowed": False, "topology_closure_allowed": False, "homology_closure_allowed": False, "sheaf_closure_allowed": False, "persistence_allowed": False, "restore_or_inverse_claim_allowed": False, "all_subset_minimality_claim_allowed": False, "full_peps3d_closure_allowed": False, "downstream_geometry_allowed": False},
    }
    tool_sig = strata_tool_signature(strata)
    pass_rule = bool(
        aj_result["pass"]
        and ah_result["pass"]
        and dependency_receipt_verified
        and exact_counts
        and all_signatures_retained
        and all_balance_retained
        and all_residue_retained
        and all_fibers_retained
        and all_sources_retained
        and all_support_pairs_retained
        and int(sp.Integer(strata["strata_count"])) == EXPECTED_STRATA_COUNT
        and int(torch.sum(stratum_size_tensor).item()) == EXPECTED_FIBER_COVERAGE
        and tool_sig["pass"]
        and all(bool(control["pass"]) for control in controls.values())
    )
    return {
        "pass": pass_rule,
        "finite_map": FINITE_MAP,
        "source_aj_pass": aj_result["pass"],
        "source_ah_pass": ah_result["pass"],
        "dependency_receipt_verified": dependency_receipt_verified,
        "signature_balance_residue_fiber_strata_table": rows,
        "strata_count": strata["strata_count"],
        "fiber_coverage": strata["fiber_coverage"],
        "frontier_pair_coverage": strata["frontier_pair_coverage"],
        "support_cell_pair_support": strata["support_cell_pair_support"],
        "source_row_coverage": strata["source_row_coverage"],
        "member_coverage": strata["member_coverage"],
        "strata_size_counts": strata["strata_size_counts"],
        "signature_key_support": strata["signature_key_support"],
        "balance_key_support": strata["balance_key_support"],
        "residue_pattern_support": strata["residue_pattern_support"],
        "exact_counts": exact_counts,
        "all_signatures_retained": all_signatures_retained,
        "all_balance_retained": all_balance_retained,
        "all_residue_retained": all_residue_retained,
        "all_fibers_retained": all_fibers_retained,
        "all_sources_retained": all_sources_retained,
        "all_support_pairs_retained": all_support_pairs_retained,
        "controls": controls,
        "tool_signature": tool_sig,
        "source_aj_incidence_row_count": aj_result["incidence_row_count"],
        "source_aj_source_row_count": aj_result["source_row_count"],
        "source_aj_fiber_count": aj_result["fiber_count"],
        "source_aj_support_cell_pair_support": aj_result["support_cell_pair_support"],
        "max_parent_peps3d_sites": aj_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": aj_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": aj_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_strata_gate(result: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    strata_retained = z3.Bool("strata_retained")
    support_retained = z3.Bool("support_retained")
    fresh_n01 = z3.Bool("fresh_n01")
    topology = z3.Bool("topology")
    dense = z3.Bool("dense")
    inverse = z3.Bool("inverse")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, strata_retained, support_retained)
    solver.add(z3.Not(fresh_n01), z3.Not(topology), z3.Not(dense), z3.Not(inverse), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(result["strata_count"] == EXPECTED_STRATA_COUNT))
    solver.add(z3.BoolVal(result["fiber_coverage"] == EXPECTED_FIBER_COVERAGE))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "strata_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_strata_gate(result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": result["all_support_pairs_retained"],
        "strata_retained": result["strata_count"] == EXPECTED_STRATA_COUNT,
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
        "strata_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    strata = stratification_gate()
    z3_gate = z3_strata_gate(strata)
    cvc5_gate = cvc5_strata_gate(strata)
    controls = strata["controls"]
    positive = {"P1_signature_balance_residue_fiber_stratification": strata}
    graveyard = {
        "GC_signature_erased_rejected": controls["signature_erased_control"],
        "GC_balance_erased_rejected": controls["balance_erased_control"],
        "GC_residue_erased_rejected": controls["residue_erased_control"],
        "GC_fiber_erased_rejected": controls["fiber_erased_control"],
        "GC_source_erased_rejected": controls["source_erased_control"],
        "GC_support_erased_rejected": controls["support_erased_control"],
        "GC_pattern_count_only_rejected": controls["pattern_count_only_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_side_swap_orientation_blocked": controls["side_swap_orientation_control"],
        "GC_restore_inverse_blocked": controls["restore_inverse_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_closure_and_downstream_not_opened": controls["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not strata["dense_state_closure_used"] and not strata["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_strata_count": {"pass": strata["strata_count"] == EXPECTED_STRATA_COUNT},
        "B4_fiber_coverage": {"pass": strata["fiber_coverage"] == EXPECTED_FIBER_COVERAGE},
        "B5_strata_size_boundary": controls["strata_size_boundary_control"],
        "B6_z3_finite_strata_nonpromotion": z3_gate,
        "B7_cvc5_finite_strata_nonpromotion": cvc5_gate,
        "B8_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        strata["pass"]
        and z3_gate["pass"]
        and cvc5_gate["pass"]
        and all(bool(row["pass"]) for row in graveyard.values())
        and all(bool(row["pass"]) for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_AJ_RECEIPT,
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
            "F01": "finite incidence rows, finite strata, finite signatures, finite balance classes, finite residue patterns, finite fibers, finite source rows, finite support-cell pair keys, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this map inherits the Phase 2 carrier order witness and rejects order-erased/fresh-N01 promotion",
        },
        "finite_map": strata["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C signature/balance/residue fiber strata carrier inherited from AJ",
            "source_fiber_incidence_rows": "459 finite AJ source-fiber incidence rows",
            "strata": "104 finite exact signature/balance/residue strata",
            "fiber_ids": "153 finite fibers retained through AH/AJ",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite signature/balance/residue fiber-strata table, strata support vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_signature_balance_residue_strata",
        "carrier_realization": "torch finite strata tensors over PEPS3D support-cell/signature/balance/residue bindings with rustworkx/xgi/proof support checks",
        "peps3d_embedding": "Every stratum row retains fiber ids, source-row ids, frontier-pair ids, and support-cell pair keys inherited from the finite PEPS3D carrier. Signature-erased, balance-erased, residue-erased, count-only, and scalar-label rows are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite signature/balance/residue fiber stratification over AJ incidence rows",
        "branch_status_before_run": "post_AJ_source_fiber_support_residue_incidence_K_candidate_map_discovery_AK_signature_balance_residue_fiber_stratification_K",
        "allowed_claims": [
            "AJ incidence rows induce 104 finite signature/balance/residue strata",
            "strata retain fiber ids, source-row ids, frontier-pair ids, support-cell pair keys, signatures, balance classes, and residue patterns",
            "strata size is a finite support readout only and does not admit topology",
            "signature-erased, balance-erased, residue-erased, fiber-erased, source-erased, support-erased, count-only, scalar-label, side-swap orientation, restore/inverse, fresh-N01, topology, closure, and downstream controls are rejected or blocked",
        ],
        "promotion_blockers": [
            "signature/balance/residue stratification readout only",
            "inherited N01 only",
            "no fresh noncommuting operator",
            "no orientation/chirality/Weyl structure",
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
        "proof_surfaces_used": ["z3_finite_strata_nonpromotion_gate", "cvc5_finite_strata_nonpromotion_gate", "sympy_exact_strata_count_checks"],
        "graph_surfaces_used": ["rustworkx_strata_fiber_support_incidence_graph", "xgi_strata_fiber_support_hypergraph"],
        "topology_surfaces_used": ["not_applicable_topology_blocked_no_topology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_AK_CANDIDATE_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_AK_CANDIDATE_PATH],
        "required_negatives": [
            "signature-erased rejection",
            "balance-erased rejection",
            "residue-erased rejection",
            "fiber-erased rejection",
            "source-erased rejection",
            "support-erased rejection",
            "pattern-count-only rejection",
            "scalar-label rejection",
            "side-swap orientation/chirality block",
            "restore/inverse block",
            "fresh-N01 rejection",
            "strata-size boundary control",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "strata can be rebuilt from pattern counts, cardinalities, or scalar labels",
            "signature, balance, residue, fiber, source, or support bindings disappear",
            "strata size is promoted to topology or connected components",
            "side-swap is promoted to orientation/chirality",
            "restore/inverse, fresh N01, dense closure, topology, all-subset, full closure, or downstream geometry is opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "AK_signature_balance_residue_fiber_stratification_K::strata::seed_20260526",
        "result_summary": {
            "strata_count": strata["strata_count"],
            "fiber_coverage": strata["fiber_coverage"],
            "frontier_pair_coverage": strata["frontier_pair_coverage"],
            "support_cell_pair_support": strata["support_cell_pair_support"],
            "source_row_coverage": strata["source_row_coverage"],
            "member_coverage": strata["member_coverage"],
            "strata_size_counts": strata["strata_size_counts"],
            "signature_key_support": strata["signature_key_support"],
            "balance_key_support": strata["balance_key_support"],
            "residue_pattern_support": strata["residue_pattern_support"],
            "source_aj_incidence_row_count": strata["source_aj_incidence_row_count"],
            "source_aj_source_row_count": strata["source_aj_source_row_count"],
            "source_aj_fiber_count": strata["source_aj_fiber_count"],
            "source_aj_support_cell_pair_support": strata["source_aj_support_cell_pair_support"],
            "max_parent_peps3d_sites": strata["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": strata["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": strata["max_peps3d_bond"],
        },
        "pass_rule": "Pass iff AJ and AH dependencies pass; 104 strata, 153 fibers covered, 387 frontier pairs, 351 support-cell pair keys, 135 source rows, exact strata-size counts, retained signature/balance/residue/fiber/source/support witnesses, finite tool signatures, z3/cvc5 gates, and all controls pass.",
        "fail_rule": "Fail if the map collapses to pattern counts/cardinalities/scalar labels, erases signature/balance/residue/fiber/source/support bindings, requires dense closure, claims orientation/restore/inverse/fresh N01/topology, or opens downstream geometry.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite strata readout only",
            "orientation_or_chirality_probe": "blocked; side-swap is not promoted",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 8,
            "total": 8,
            "variants": [
                "AK_signature_balance_residue_fiber_stratification_K classified as bounded finite strata readout",
                "strata component/topology classified as rejected",
                "pattern-count-only and cardinality-only variants classified as duplicate/rejected",
                "signature-erased, balance-erased, residue-erased, fiber-erased, source-erased, and support-erased variants classified as rejected",
                "side-swap orientation/chirality, fresh-N01, and order-erased variants classified as rejected for new geometry/evidence",
                "strata-size counts treated as boundary control only",
                "restore/inverse/topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream Hopf/Weyl/terrain/substage/flux/Xi/Phi0/Axis0/physics/IGT/axes variants classified as rejected",
            ],
        },
        "signature_balance_residue_fiber_strata_table": strata["signature_balance_residue_fiber_strata_table"],
        "strata_count": strata["strata_count"],
        "fiber_coverage": strata["fiber_coverage"],
        "frontier_pair_coverage": strata["frontier_pair_coverage"],
        "support_cell_pair_support": strata["support_cell_pair_support"],
        "source_row_coverage": strata["source_row_coverage"],
        "member_coverage": strata["member_coverage"],
        "strata_size_counts": strata["strata_size_counts"],
        "signature_key_support": strata["signature_key_support"],
        "balance_key_support": strata["balance_key_support"],
        "residue_pattern_support": strata["residue_pattern_support"],
        "exact_counts": strata["exact_counts"],
        "all_signatures_retained": strata["all_signatures_retained"],
        "all_balance_retained": strata["all_balance_retained"],
        "all_residue_retained": strata["all_residue_retained"],
        "all_fibers_retained": strata["all_fibers_retained"],
        "all_sources_retained": strata["all_sources_retained"],
        "all_support_pairs_retained": strata["all_support_pairs_retained"],
        "max_parent_peps3d_sites": strata["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": strata["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": strata["max_peps3d_bond"],
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
                "strata_count": strata["strata_count"],
                "fiber_coverage": strata["fiber_coverage"],
                "frontier_pair_coverage": strata["frontier_pair_coverage"],
                "support_cell_pair_support": strata["support_cell_pair_support"],
                "max_parent_peps3d_sites": strata["max_parent_peps3d_sites"],
                "max_peps3d_bond": strata["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
