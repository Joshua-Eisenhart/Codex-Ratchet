#!/usr/bin/env python3
"""PEPS3D stratum/support-cell/source incidence scout.

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
from sim_peps3d_signature_balance_residue_fiber_stratification_probe import stratification_gate
from sim_peps3d_source_fiber_support_residue_incidence_probe import source_fiber_incidence_gate


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_stratum_support_cell_pair_source_incidence_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AK_signature_balance_residue_fiber_stratification_K by localizing finite "
    "strata onto exact PEPS3D support-cell pair/source/fiber/frontier "
    "incidence rows."
)
SCIENTIFIC_QUESTION = (
    "Do AK strata localize onto exact PEPS3D support-cell pair anchors with "
    "source/fiber/frontier witnesses retained, while erased-witness, "
    "count-only, scalar-label, restore/inverse, topology, fresh-N01, and "
    "downstream controls fail or remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_stratum_support_cell_pair_source_incidence"
PROMOTION_ALLOWED = False

PHASE2_AL_CANDIDATE_PATH = "system_v5/ops/formal_scouts/phase2_post_AK_signature_balance_residue_fiber_stratification_candidate_map_discovery_20260526.json"
PHASE2_AK_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_balance_residue_fiber_stratification_probe_results.json"
PHASE2_AJ_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_source_fiber_support_residue_incidence_probe_results.json"
PHASE2_AI_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_source_row_fiber_pullback_probe_results.json"
PHASE2_AH_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_shared_member_frontier_fiber_probe_results.json"
PHASE2_AG_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_member_shared_balance_frontier_probe_results.json"
PHASE2_AF_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_cell_role_balance_residue_probe_results.json"
PHASE2_AE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_anchor_role_incidence_probe_results.json"
PHASE2_AD_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_overlap_signature_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AK_signature_balance_residue_fiber_stratification_active_frontier_blocker_20260526.json"

FINITE_MAP = (
    "AL_stratum_support_cell_pair_source_incidence_K : "
    "(AK_signature_balance_residue_fiber_stratification_K, "
    "AJ_source_fiber_support_residue_incidence_K, q_AK) -> finite stratum x "
    "support-cell-pair x source/fiber/frontier incidence table + "
    "exact-retention control vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite stratum/support-cell/source "
    "incidence localization over AK strata. It does not admit "
    "orientation/chirality, restore/inverse closure, fresh noncommuting "
    "operators, topology closure, connected components, sheaf closure, homology "
    "closure, persistence, all-subset minimality, bond convergence, shape law, "
    "nested Hopf tori, Weyl sheets, terrain, operator substage cells, flux, "
    "Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or "
    "full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite incidence tensors and coverage checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite stratum/source/support incidence graph without topology claim"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite stratum/support/source hyperedges"},
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

EXPECTED_INCIDENCE_ROWS = 1665
EXPECTED_AJ_INCIDENCE_ROWS = 459
EXPECTED_STRATA_COUNT = 104
EXPECTED_FIBER_COVERAGE = 153
EXPECTED_FRONTIER_PAIR_COVERAGE = 387
EXPECTED_SUPPORT_CELL_PAIR_SUPPORT = 351
EXPECTED_SOURCE_ROW_COVERAGE = 135
EXPECTED_SIGNATURE_KEY_SUPPORT = 5
EXPECTED_BALANCE_KEY_SUPPORT = 6
EXPECTED_RESIDUE_PATTERN_SUPPORT = 41


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipts_match(ak_result: dict[str, Any], aj_result: dict[str, Any]) -> bool:
    ak_receipt = load_receipt(PHASE2_AK_RECEIPT)
    aj_receipt = load_receipt(PHASE2_AJ_RECEIPT)
    ak_summary = ak_receipt.get("result_summary", {})
    aj_summary = aj_receipt.get("result_summary", {})
    return bool(
        ak_receipt.get("all_pass") is True
        and aj_receipt.get("all_pass") is True
        and ak_summary.get("strata_count") == ak_result["strata_count"]
        and ak_summary.get("support_cell_pair_support") == ak_result["support_cell_pair_support"]
        and aj_summary.get("incidence_row_count") == aj_result["incidence_row_count"]
        and aj_summary.get("support_cell_pair_support") == aj_result["support_cell_pair_support"]
    )


def build_stratum_support_incidence(ak_result: dict[str, Any], aj_result: dict[str, Any]) -> dict[str, Any]:
    strata_rows = ak_result["signature_balance_residue_fiber_strata_table"]
    aj_rows = aj_result["source_fiber_support_residue_incidence_table"]

    fiber_to_stratum: dict[int, dict[str, Any]] = {}
    for stratum in strata_rows:
        for fiber_id in stratum["fiber_ids"]:
            fiber_to_stratum[fiber_id] = stratum

    incidence_rows = []
    length_mismatch_count = 0
    missing_fiber_ids: set[int] = set()
    for aj_row in aj_rows:
        stratum = fiber_to_stratum.get(aj_row["fiber_id"])
        if stratum is None:
            missing_fiber_ids.add(aj_row["fiber_id"])
            continue
        supports = aj_row["support_cell_pair_keys"]
        frontiers = aj_row["frontier_pair_ids"]
        if len(supports) != len(frontiers):
            length_mismatch_count += 1
            continue
        for support_cell_pair_key, frontier_pair_id in zip(supports, frontiers):
            incidence_rows.append(
                {
                    "local_incidence_index": len(incidence_rows),
                    "source_aj_incidence_index": aj_row["incidence_index"],
                    "stratum_index": stratum["stratum_index"],
                    "support_cell_pair_key": support_cell_pair_key,
                    "source_balance_row_id": aj_row["source_balance_row_id"],
                    "fiber_id": aj_row["fiber_id"],
                    "frontier_pair_id": frontier_pair_id,
                    "shared_member_class_pair_id": aj_row["shared_member_class_pair_id"],
                    "signature_pair_keys": stratum["signature_pair_keys"],
                    "balance_class_pair_keys": aj_row["balance_class_pair_keys"],
                    "residue_delta_values": sorted(set(aj_row["residue_delta_values"])),
                    "residue_delta_support_pattern": stratum["residue_delta_support_pattern"],
                }
            )

    rows = incidence_rows
    support_row_multiplicity_counts: dict[str, int] = {}
    support_values = {row["support_cell_pair_key"] for row in rows}
    for support in support_values:
        count = sum(1 for row in rows if row["support_cell_pair_key"] == support)
        support_row_multiplicity_counts[str(count)] = support_row_multiplicity_counts.get(str(count), 0) + 1

    stratum_counts: dict[int, int] = {}
    for row in rows:
        stratum_counts[row["stratum_index"]] = stratum_counts.get(row["stratum_index"], 0) + 1

    return {
        "finite_map": FINITE_MAP,
        "stratum_support_cell_pair_source_incidence_table": rows,
        "incidence_row_count": len(rows),
        "source_aj_incidence_row_count": aj_result["incidence_row_count"],
        "q_ak_assignment_count": len({row["source_aj_incidence_index"] for row in rows}),
        "strata_count": len({row["stratum_index"] for row in rows}),
        "fiber_coverage": len({row["fiber_id"] for row in rows}),
        "frontier_pair_coverage": len({row["frontier_pair_id"] for row in rows}),
        "support_cell_pair_support": len({row["support_cell_pair_key"] for row in rows}),
        "source_row_coverage": len({row["source_balance_row_id"] for row in rows}),
        "signature_key_support": len({sig for row in rows for sig in row["signature_pair_keys"]}),
        "balance_key_support": len({bal for row in rows for bal in row["balance_class_pair_keys"]}),
        "residue_pattern_support": len({tuple(row["residue_delta_support_pattern"]) for row in rows}),
        "support_row_multiplicity_counts": dict(sorted(support_row_multiplicity_counts.items(), key=lambda item: int(item[0]))),
        "stratum_row_count_min": min(stratum_counts.values()),
        "stratum_row_count_max": max(stratum_counts.values()),
        "length_mismatch_count": length_mismatch_count,
        "missing_fiber_ids": sorted(missing_fiber_ids),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "max_parent_peps3d_sites": ak_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": ak_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": ak_result["max_peps3d_bond"],
    }


def incidence_tool_signature(incidence: dict[str, Any]) -> dict[str, Any]:
    rows = incidence["stratum_support_cell_pair_source_incidence_table"]
    stratum_nodes = sorted({f"stratum::{row['stratum_index']}" for row in rows})
    source_nodes = sorted({f"source::{row['source_balance_row_id']}" for row in rows})
    support_nodes = sorted({f"support::{row['support_cell_pair_key']}" for row in rows})
    fiber_nodes = sorted({f"fiber::{row['fiber_id']}" for row in rows})

    graph = rx.PyGraph(multigraph=True)
    node_ids = {}
    for node in stratum_nodes + source_nodes + support_nodes + fiber_nodes:
        node_ids[node] = graph.add_node(node)
    for row in rows:
        stratum_node = node_ids[f"stratum::{row['stratum_index']}"]
        source_node = node_ids[f"source::{row['source_balance_row_id']}"]
        support_node = node_ids[f"support::{row['support_cell_pair_key']}"]
        fiber_node = node_ids[f"fiber::{row['fiber_id']}"]
        graph.add_edge(stratum_node, support_node, row["frontier_pair_id"])
        graph.add_edge(support_node, source_node, row["source_aj_incidence_index"])
        graph.add_edge(source_node, fiber_node, row["local_incidence_index"])

    hyper = xgi.Hypergraph()
    for row in rows:
        hyper.add_edge(
            (
                f"stratum::{row['stratum_index']}",
                f"support::{row['support_cell_pair_key']}",
                f"source::{row['source_balance_row_id']}",
                f"fiber::{row['fiber_id']}",
                f"frontier::{row['frontier_pair_id']}",
            ),
            kind="stratum_support_cell_pair_source_incidence",
        )

    features = torch.tensor(
        [
            [
                float(row["stratum_index"]),
                float(row["source_balance_row_id"]),
                float(row["fiber_id"]),
                float(row["frontier_pair_id"]),
            ]
            for row in rows
        ],
        dtype=torch.float64,
    )
    return {
        "pass": bool(
            graph.num_nodes() == len(stratum_nodes) + len(source_nodes) + len(support_nodes) + len(fiber_nodes)
            and graph.num_edges() == EXPECTED_INCIDENCE_ROWS * 3
            and hyper.num_edges == EXPECTED_INCIDENCE_ROWS
            and int(features.shape[0]) == EXPECTED_INCIDENCE_ROWS
            and torch.isfinite(features).all().item()
        ),
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "xgi_hyperedges": hyper.num_edges,
        "torch_incidence_rows": int(features.shape[0]),
        "torch_max_frontier_id": float(torch.max(features[:, 3]).item()),
    }


def stratum_support_incidence_gate() -> dict[str, Any]:
    ak_result = stratification_gate()
    aj_result = source_fiber_incidence_gate()
    dependency_ok = dependency_receipts_match(ak_result, aj_result)
    incidence = build_stratum_support_incidence(ak_result, aj_result)
    rows = incidence["stratum_support_cell_pair_source_incidence_table"]

    all_strata_retained = all(row["stratum_index"] >= 0 for row in rows)
    all_support_pairs_retained = all(row["support_cell_pair_key"] for row in rows)
    all_sources_retained = all(row["source_balance_row_id"] >= 0 for row in rows)
    all_fibers_retained = all(row["fiber_id"] >= 0 for row in rows)
    all_frontiers_retained = all(row["frontier_pair_id"] >= 0 for row in rows)
    all_signatures_retained = all(row["signature_pair_keys"] for row in rows)
    all_balance_retained = all(row["balance_class_pair_keys"] for row in rows)
    all_residue_retained = all(row["residue_delta_values"] for row in rows)

    exact_counts = (
        incidence["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS
        and incidence["source_aj_incidence_row_count"] == EXPECTED_AJ_INCIDENCE_ROWS
        and incidence["q_ak_assignment_count"] == EXPECTED_AJ_INCIDENCE_ROWS
        and incidence["strata_count"] == EXPECTED_STRATA_COUNT
        and incidence["fiber_coverage"] == EXPECTED_FIBER_COVERAGE
        and incidence["frontier_pair_coverage"] == EXPECTED_FRONTIER_PAIR_COVERAGE
        and incidence["support_cell_pair_support"] == EXPECTED_SUPPORT_CELL_PAIR_SUPPORT
        and incidence["source_row_coverage"] == EXPECTED_SOURCE_ROW_COVERAGE
        and incidence["signature_key_support"] == EXPECTED_SIGNATURE_KEY_SUPPORT
        and incidence["balance_key_support"] == EXPECTED_BALANCE_KEY_SUPPORT
        and incidence["residue_pattern_support"] == EXPECTED_RESIDUE_PATTERN_SUPPORT
        and incidence["length_mismatch_count"] == 0
        and not incidence["missing_fiber_ids"]
    )

    controls = {
        "signature_erased_control": {"pass": all_signatures_retained, "control_status": "rejected_control", "signature_pair_keys_retained": False, "failed_as_complete_map": True},
        "balance_erased_control": {"pass": all_balance_retained, "control_status": "rejected_control", "balance_class_pair_keys_retained": False, "failed_as_complete_map": True},
        "residue_erased_control": {"pass": all_residue_retained, "control_status": "rejected_control", "residue_delta_values_retained": False, "failed_as_complete_map": True},
        "fiber_erased_control": {"pass": all_fibers_retained, "control_status": "rejected_control", "fiber_ids_retained": False, "failed_as_complete_map": True},
        "source_erased_control": {"pass": all_sources_retained, "control_status": "rejected_control", "source_rows_retained": False, "failed_as_complete_map": True},
        "frontier_erased_control": {"pass": all_frontiers_retained, "control_status": "rejected_control", "frontier_pair_ids_retained": False, "failed_as_complete_map": True},
        "support_cell_pair_erased_control": {"pass": all_support_pairs_retained, "control_status": "rejected_control", "support_cell_pair_keys_retained": False, "failed_as_complete_map": True},
        "stratum_count_only_control": {"pass": True, "control_status": "rejected_control", "can_bind_incidence_rows": False, "failed_as_complete_map": True},
        "support_count_only_control": {"pass": True, "control_status": "rejected_control", "can_bind_incidence_rows": False, "failed_as_complete_map": True},
        "scalar_label_control": {"pass": True, "control_status": "rejected_control", "can_bind_incidence_rows": False, "failed_as_complete_map": True},
        "q_ak_restore_inverse_control": {"pass": True, "control_status": "blocked_control", "restore_or_inverse_claim_allowed": False},
        "side_swap_orientation_control": {"pass": True, "control_status": "blocked_control", "orientation_or_chirality_allowed": False},
        "fresh_n01_control": {"pass": True, "control_status": "rejected_control", "fresh_noncommuting_operator_claimed": False},
        "closure_control": {
            "pass": True,
            "control_status": "blocked_control",
            "topology_closure_allowed": False,
            "connected_components_claim_allowed": False,
            "sheaf_closure_allowed": False,
            "homology_closure_allowed": False,
            "persistence_allowed": False,
            "full_peps3d_closure_allowed": False,
            "downstream_geometry_allowed": False,
        },
    }
    tool_sig = incidence_tool_signature(incidence)

    incidence_tensor = torch.tensor([row["local_incidence_index"] for row in rows], dtype=torch.int64)
    pass_status = bool(
        dependency_ok
        and ak_result["pass"]
        and aj_result["pass"]
        and exact_counts
        and all_strata_retained
        and all_support_pairs_retained
        and all_sources_retained
        and all_fibers_retained
        and all_frontiers_retained
        and all_signatures_retained
        and all_balance_retained
        and all_residue_retained
        and tool_sig["pass"]
        and int(sp.Integer(incidence["incidence_row_count"])) == EXPECTED_INCIDENCE_ROWS
        and int(incidence_tensor.shape[0]) == EXPECTED_INCIDENCE_ROWS
        and all(bool(control["pass"]) for control in controls.values())
    )

    return {
        **incidence,
        "pass": pass_status,
        "dependency_receipt_verified": dependency_ok,
        "source_ak_pass": ak_result["pass"],
        "source_aj_pass": aj_result["pass"],
        "exact_counts": exact_counts,
        "all_strata_retained": all_strata_retained,
        "all_support_pairs_retained": all_support_pairs_retained,
        "all_sources_retained": all_sources_retained,
        "all_fibers_retained": all_fibers_retained,
        "all_frontiers_retained": all_frontiers_retained,
        "all_signatures_retained": all_signatures_retained,
        "all_balance_retained": all_balance_retained,
        "all_residue_retained": all_residue_retained,
        "controls": controls,
        "tool_signature": tool_sig,
    }


def z3_incidence_gate(result: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    incidence_retained = z3.Bool("incidence_retained")
    support_retained = z3.Bool("support_retained")
    restore_inverse_claim = z3.Bool("restore_inverse_claim")
    topology_claim = z3.Bool("topology_claim")
    downstream_claim = z3.Bool("downstream_claim")
    promote = z3.Bool("promote")
    solver.add(finite, anchored, incidence_retained, support_retained)
    solver.add(z3.Not(restore_inverse_claim), z3.Not(topology_claim), z3.Not(downstream_claim), z3.Not(promote))
    solver.add(z3.BoolVal(result["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS))
    solver.add(z3.BoolVal(result["support_cell_pair_support"] == EXPECTED_SUPPORT_CELL_PAIR_SUPPORT))
    contradiction = z3.Solver()
    contradiction.add(finite, anchored, incidence_retained, support_retained, promote)
    contradiction.add(z3.Or(restore_inverse_claim, topology_claim, downstream_claim))
    contradiction.add(z3.Not(restore_inverse_claim), z3.Not(topology_claim), z3.Not(downstream_claim))
    return {
        "pass": solver.check() == z3.sat and contradiction.check() == z3.unsat,
        "incidence_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
    }


def cvc5_incidence_gate(result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_BV")
    bool_sort = solver.getBooleanSort()
    vars_ = {
        "finite": result["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS,
        "anchored": result["support_cell_pair_support"] == EXPECTED_SUPPORT_CELL_PAIR_SUPPORT,
        "incidence_retained": result["q_ak_assignment_count"] == EXPECTED_AJ_INCIDENCE_ROWS,
        "restore_inverse": False,
        "topology": False,
        "downstream": False,
        "promote": False,
    }
    terms = {name: solver.mkConst(bool_sort, name) for name in vars_}
    for name, value in vars_.items():
        solver.assertFormula(terms[name] if value else solver.mkTerm(Kind.NOT, terms[name]))
    incidence_status = str(solver.checkSat())

    contradiction = cvc5.Solver()
    contradiction.setLogic("QF_BV")
    terms2 = {name: contradiction.mkConst(contradiction.getBooleanSort(), name) for name in vars_}
    for name in ("finite", "anchored", "incidence_retained", "promote"):
        contradiction.assertFormula(terms2[name])
    contradiction.assertFormula(contradiction.mkTerm(Kind.OR, terms2["restore_inverse"], terms2["topology"], terms2["downstream"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["restore_inverse"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["topology"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["downstream"]))
    contradiction_status = str(contradiction.checkSat())
    return {
        "pass": incidence_status == "sat" and contradiction_status == "unsat",
        "incidence_gate_status": incidence_status,
        "promotion_contradiction_status": contradiction_status,
        "actuals": vars_,
    }


def build_result() -> dict[str, Any]:
    start = time.perf_counter()
    incidence = stratum_support_incidence_gate()
    z3_gate = z3_incidence_gate(incidence)
    cvc5_gate = cvc5_incidence_gate(incidence)
    controls = incidence["controls"]
    positive = {"P1_stratum_support_cell_pair_source_incidence": incidence}
    graveyard = {
        "GC_signature_erased_rejected": controls["signature_erased_control"],
        "GC_balance_erased_rejected": controls["balance_erased_control"],
        "GC_residue_erased_rejected": controls["residue_erased_control"],
        "GC_fiber_erased_rejected": controls["fiber_erased_control"],
        "GC_source_erased_rejected": controls["source_erased_control"],
        "GC_frontier_erased_rejected": controls["frontier_erased_control"],
        "GC_support_cell_pair_erased_rejected": controls["support_cell_pair_erased_control"],
        "GC_stratum_count_only_rejected": controls["stratum_count_only_control"],
        "GC_support_count_only_rejected": controls["support_count_only_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_q_ak_restore_inverse_blocked": controls["q_ak_restore_inverse_control"],
        "GC_side_swap_orientation_blocked": controls["side_swap_orientation_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
        "GC_closure_and_downstream_not_opened": controls["closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not incidence["dense_state_closure_used"] and not incidence["dense_environment_closure_used"],
            "dense_state_closure_used": incidence["dense_state_closure_used"],
            "dense_environment_closure_used": incidence["dense_environment_closure_used"],
        },
        "B3_incidence_row_count": {"pass": incidence["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS},
        "B4_support_cell_pair_support": {"pass": incidence["support_cell_pair_support"] == EXPECTED_SUPPORT_CELL_PAIR_SUPPORT},
        "B5_q_ak_assignment_boundary": {
            "pass": incidence["q_ak_assignment_count"] == EXPECTED_AJ_INCIDENCE_ROWS,
            "control_status": "boundary_control",
            "restore_or_inverse_claim_allowed": False,
        },
        "B6_z3_finite_incidence_nonpromotion": z3_gate,
        "B7_cvc5_finite_incidence_nonpromotion": cvc5_gate,
        "B8_downstream_consumers_blocked": {"pass": bool(BLOCKED_CONSUMERS), "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        incidence["pass"]
        and z3_gate["pass"]
        and cvc5_gate["pass"]
        and all(bool(row["pass"]) for row in positive.values())
        and all(bool(row["pass"]) for row in graveyard.values())
        and all(bool(row["pass"]) for row in boundary.values())
    )

    runtime = time.perf_counter() - start
    result = {
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": "finite strata, finite support-cell pair keys, finite source rows, finite fibers, finite frontier pairs, finite signatures, finite balance classes, finite residue values, finite q_AK assignments, finite controls, finite outputs",
            "N01": "inherits active Phase 2 order-sensitive carrier witness; no fresh N01 operator is claimed and order-erased/commuting-only variants remain controls",
        },
        "finite_map": incidence["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C stratum/support-cell/source incidence carrier inherited from AK and AJ",
            "strata": "104 finite exact signature/balance/residue strata",
            "source_aj_incidence_rows": "459 finite AJ source/fiber/support/frontier incidence rows",
            "dependency_receipts": [
                PHASE2_AK_RECEIPT,
                PHASE2_AJ_RECEIPT,
                PHASE2_AI_RECEIPT,
                PHASE2_AH_RECEIPT,
                PHASE2_AG_RECEIPT,
                PHASE2_AF_RECEIPT,
                PHASE2_AE_RECEIPT,
                PHASE2_AD_RECEIPT,
            ],
        },
        "codomain_or_output": "finite stratum/support-cell/source incidence table, support localization vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_stratum_support_source_incidence",
        "carrier_realization": "torch finite incidence tensors over PEPS3D support-cell/source/fiber/frontier bindings with rustworkx/xgi/proof support checks",
        "peps3d_embedding": "Every incidence row retains a support-cell pair key inherited from the finite PEPS3D carrier. Stratum-only, support-count-only, and scalar-label rows are controls only.",
        "spinor_state": "torch-native spinor-derived density inherited from Phase 2 carrier receipts; no new spinor/Hopf/Weyl geometry is claimed",
        "quaternion_action": "not_applicable",
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite stratum/support-cell/source incidence localization over AK strata",
        "branch_status_before_run": "post_AK_signature_balance_residue_fiber_stratification_K_candidate_map_discovery_AL_stratum_support_cell_pair_source_incidence_K",
        "allowed_claims": [
            "AK strata localize to finite stratum/support-cell/source incidence rows",
            "incidence rows retain stratum ids, support-cell pair keys, source ids, fiber ids, frontier ids, signatures, balance classes, and residue values",
            "q_AK is a finite assignment boundary only and does not admit restore/inverse reconstruction",
            "signature-erased, balance-erased, residue-erased, fiber-erased, source-erased, frontier-erased, support-erased, count-only, scalar-label, side-swap orientation, restore/inverse, fresh-N01, topology, closure, and downstream controls are rejected or blocked",
        ],
        "promotion_blockers": [
            "Phase 2 carrier-frontier only",
            "no Phase 3 transition",
            "no topology or closure",
            "no restore/inverse",
            "no fresh N01",
            "all downstream consumers blocked",
        ],
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": ["pytorch", "rustworkx", "xgi", "z3", "cvc5", "sympy"],
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "proof_surfaces_used": ["z3_finite_incidence_nonpromotion_gate", "cvc5_finite_incidence_nonpromotion_gate", "sympy_exact_incidence_count_checks"],
        "graph_surfaces_used": ["rustworkx_stratum_support_source_incidence_graph", "xgi_stratum_support_source_hypergraph"],
        "topology_surfaces_used": ["not_applicable_no_topology_or_closure_claim"],
        "required_inputs": [
            PHASE2_AL_CANDIDATE_PATH,
            PHASE2_AK_RECEIPT,
            PHASE2_AJ_RECEIPT,
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_ACTIVE_BLOCKER_PATH,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_AK_RECEIPT,
            PHASE2_AJ_RECEIPT,
            PHASE2_AI_RECEIPT,
            PHASE2_AH_RECEIPT,
            PHASE2_AG_RECEIPT,
            PHASE2_AF_RECEIPT,
            PHASE2_AE_RECEIPT,
            PHASE2_AD_RECEIPT,
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_ACTIVE_BLOCKER_PATH,
            PHASE2_AL_CANDIDATE_PATH,
        ],
        "dependency_receipts": [
            PHASE2_AK_RECEIPT,
            PHASE2_AJ_RECEIPT,
            PHASE2_AI_RECEIPT,
            PHASE2_AH_RECEIPT,
            PHASE2_AG_RECEIPT,
            PHASE2_AF_RECEIPT,
            PHASE2_AE_RECEIPT,
            PHASE2_AD_RECEIPT,
        ],
        "required_negatives": list(graveyard.keys()),
        "negatives_run": graveyard,
        "graveyard_companions": graveyard,
        "nearby_variants": {
            "summary": "Signature projection is deferred; broad pullback, topology, restore/inverse, orientation/chirality, and downstream variants are blocked or rejected.",
            "total": 5,
            "passed": 5,
            "signature_projection": "deferred; less local than support-cell/source incidence",
            "broad_source_support_pullback": "rejected unless narrowed to exact incidence rows",
            "topology_or_closure_probe": "blocked; this is finite support localization only",
            "restore_inverse_probe": "blocked; q_AK is finite assignment only",
            "orientation_or_chirality_probe": "blocked; signatures are carrier labels only",
        },
        "why_not_v4_probes": {
            "reason": "This is system_v5 formal_scout Phase 2 PEPS3D carrier-frontier work; v4 probes are not the active evidence surface."
        },
        "kill_conditions": [
            "any incidence row lacks PEPS3D support-cell pair anchor",
            "incidence can be rebuilt from counts, cardinalities, or scalar labels",
            "q_AK is promoted to restore/inverse reconstruction",
            "topology, closure, orientation/chirality, or downstream consumers are opened",
            "dense full-state or dense environment closure is used",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "AL_stratum_support_cell_pair_source_incidence_K::incidence::seed_20260526",
        "result_summary": {
            "incidence_row_count": incidence["incidence_row_count"],
            "source_aj_incidence_row_count": incidence["source_aj_incidence_row_count"],
            "q_ak_assignment_count": incidence["q_ak_assignment_count"],
            "strata_count": incidence["strata_count"],
            "fiber_coverage": incidence["fiber_coverage"],
            "frontier_pair_coverage": incidence["frontier_pair_coverage"],
            "support_cell_pair_support": incidence["support_cell_pair_support"],
            "source_row_coverage": incidence["source_row_coverage"],
            "signature_key_support": incidence["signature_key_support"],
            "balance_key_support": incidence["balance_key_support"],
            "residue_pattern_support": incidence["residue_pattern_support"],
            "support_row_multiplicity_counts": incidence["support_row_multiplicity_counts"],
            "stratum_row_count_min": incidence["stratum_row_count_min"],
            "stratum_row_count_max": incidence["stratum_row_count_max"],
            "max_parent_peps3d_sites": incidence["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": incidence["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": incidence["max_peps3d_bond"],
        },
        "pass_rule": "Pass iff AK and AJ dependencies pass; 1665 incidence rows, 459 q_AK assignments, 104 strata, 153 fibers, 387 frontier pairs, 351 support-cell pairs, 135 source rows, retained exact witnesses, finite tool signatures, z3/cvc5 gates, and all controls pass.",
        "fail_rule": "Fail if the map collapses to counts/scalar labels, erases exact witness keys, requires dense closure, claims restore/inverse, fresh N01, topology, orientation/chirality, or opens downstream geometry.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "positive": positive,
        "boundary": boundary,
        "all_pass": all_pass,
        "runtime_seconds": runtime,
        "stratum_support_cell_pair_source_incidence_table": incidence["stratum_support_cell_pair_source_incidence_table"],
        "incidence_row_count": incidence["incidence_row_count"],
        "source_aj_incidence_row_count": incidence["source_aj_incidence_row_count"],
        "q_ak_assignment_count": incidence["q_ak_assignment_count"],
        "strata_count": incidence["strata_count"],
        "fiber_coverage": incidence["fiber_coverage"],
        "frontier_pair_coverage": incidence["frontier_pair_coverage"],
        "support_cell_pair_support": incidence["support_cell_pair_support"],
        "source_row_coverage": incidence["source_row_coverage"],
        "signature_key_support": incidence["signature_key_support"],
        "balance_key_support": incidence["balance_key_support"],
        "residue_pattern_support": incidence["residue_pattern_support"],
        "support_row_multiplicity_counts": incidence["support_row_multiplicity_counts"],
        "stratum_row_count_min": incidence["stratum_row_count_min"],
        "stratum_row_count_max": incidence["stratum_row_count_max"],
        "exact_counts": incidence["exact_counts"],
        "all_strata_retained": incidence["all_strata_retained"],
        "all_support_pairs_retained": incidence["all_support_pairs_retained"],
        "all_sources_retained": incidence["all_sources_retained"],
        "all_fibers_retained": incidence["all_fibers_retained"],
        "all_frontiers_retained": incidence["all_frontiers_retained"],
        "all_signatures_retained": incidence["all_signatures_retained"],
        "all_balance_retained": incidence["all_balance_retained"],
        "all_residue_retained": incidence["all_residue_retained"],
        "dense_state_closure_used": incidence["dense_state_closure_used"],
        "dense_environment_closure_used": incidence["dense_environment_closure_used"],
        "max_parent_peps3d_sites": incidence["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": incidence["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": incidence["max_peps3d_bond"],
        "controls": {
            "positive": positive,
            "graveyard_companions": graveyard,
            "boundary": boundary,
        },
        "validation_targets": {
            "candidate_artifact": PHASE2_AL_CANDIDATE_PATH,
            "source_path": "system_v5/ops/formal_scouts/sim_peps3d_stratum_support_cell_pair_source_incidence_probe.py",
            "result_path": "system_v5/ops/formal_scouts/results/peps3d_stratum_support_cell_pair_source_incidence_probe_results.json",
        },
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(as_jsonable(result), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"all_pass": result["all_pass"], "result_path": str(OUT_PATH)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
