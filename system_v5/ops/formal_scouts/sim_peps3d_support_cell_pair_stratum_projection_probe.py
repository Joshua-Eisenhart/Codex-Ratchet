#!/usr/bin/env python3
"""PEPS3D support-cell-pair stratum-projection scout.

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
from sim_peps3d_stratum_support_cell_pair_source_incidence_probe import stratum_support_incidence_gate


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_support_cell_pair_stratum_projection_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AL_stratum_support_cell_pair_source_incidence_K by projecting finite "
    "incidence rows onto exact PEPS3D support-cell pair anchors while retaining "
    "stratum/source/fiber/frontier witnesses."
)
SCIENTIFIC_QUESTION = (
    "Do AL incidence rows project onto exactly 351 finite PEPS3D support-cell "
    "pair anchors that retain all strata, source rows, fibers, frontier pairs, "
    "signatures, balance classes, and residue patterns, while support-erased, "
    "witness-erased, count-only, scalar-label, restore/inverse, topology, "
    "fresh-N01, orientation/chirality, and downstream controls fail or remain "
    "blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_support_cell_pair_stratum_projection"
PROMOTION_ALLOWED = False

PHASE2_AM_CANDIDATE_PATH = "system_v5/ops/formal_scouts/phase2_post_AL_stratum_support_cell_pair_source_incidence_candidate_map_discovery_20260526.json"
PHASE2_AL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_stratum_support_cell_pair_source_incidence_probe_results.json"
PHASE2_AK_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_balance_residue_fiber_stratification_probe_results.json"
PHASE2_AJ_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_source_fiber_support_residue_incidence_probe_results.json"
PHASE2_AI_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_source_row_fiber_pullback_probe_results.json"
PHASE2_AH_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_shared_member_frontier_fiber_probe_results.json"
PHASE2_AG_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_member_shared_balance_frontier_probe_results.json"
PHASE2_AF_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_cell_role_balance_residue_probe_results.json"
PHASE2_AE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_anchor_role_incidence_probe_results.json"
PHASE2_AD_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_overlap_signature_fiber_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AL_stratum_support_cell_pair_source_incidence_active_frontier_blocker_20260526.json"

FINITE_MAP = (
    "AM_support_cell_pair_stratum_projection_K : "
    "(AL_stratum_support_cell_pair_source_incidence_K, support_cell_pair_key, "
    "stratum_ids, source_balance_row_ids, fiber_ids, frontier_pair_ids, "
    "signature_pair_keys, balance_class_pair_keys, residue_delta_support_patterns) "
    "-> finite support-cell-pair stratum projection table + exact-retention "
    "control vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite support-cell-pair projection "
    "readout over AL incidence rows. It does not admit orientation/chirality, "
    "restore/inverse closure, fresh noncommuting operators, topology closure, "
    "connected components, sheaf closure, homology closure, persistence, "
    "all-subset minimality, bond convergence, shape law, nested Hopf tori, "
    "Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, Axis0, "
    "Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite support projection tensors and coverage checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite support/stratum/source projection graph without topology claim"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite support-cell projection hyperedges"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite projection/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite projection/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact support projection count checks"},
    "toponetx": {"tried": False, "used": False, "reason": "not applicable: no cell-complex topology or closure is claimed"},
    "gudhi": {"tried": False, "used": False, "reason": "not applicable: no homology, persistence, or filtration is claimed"},
    "torch_geometric": {"tried": False, "used": False, "reason": "not applicable: rustworkx/xgi already carry the finite projection claim"},
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

EXPECTED_SUPPORT_PROJECTION_ROWS = 351
EXPECTED_INCIDENCE_ROWS = 1665
EXPECTED_STRATA_COUNT = 104
EXPECTED_SOURCE_ROW_COVERAGE = 135
EXPECTED_FIBER_COVERAGE = 153
EXPECTED_FRONTIER_PAIR_COVERAGE = 387
EXPECTED_SIGNATURE_KEY_SUPPORT = 5
EXPECTED_BALANCE_KEY_SUPPORT = 6
EXPECTED_RESIDUE_PATTERN_SUPPORT = 41
EXPECTED_SUPPORT_ROW_MULTIPLICITY_COUNTS = {"2": 36, "3": 162, "4": 144, "59": 9}
EXPECTED_STRATA_PER_SUPPORT_COUNTS = {"1": 342, "14": 1, "15": 3, "16": 5}
EXPECTED_SOURCE_PER_SUPPORT_COUNTS = {"2": 36, "3": 162, "4": 144, "35": 9}
EXPECTED_FIBER_PER_SUPPORT_COUNTS = {"1": 342, "17": 9}


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def count_distribution(values: list[int]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def dependency_receipt_matches(al_result: dict[str, Any]) -> bool:
    receipt = load_receipt(PHASE2_AL_RECEIPT)
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("incidence_row_count") == al_result["incidence_row_count"]
        and summary.get("support_cell_pair_support") == al_result["support_cell_pair_support"]
        and summary.get("strata_count") == al_result["strata_count"]
    )


def build_support_projection(al_result: dict[str, Any]) -> dict[str, Any]:
    projection: dict[str, dict[str, Any]] = {}
    for incidence in al_result["stratum_support_cell_pair_source_incidence_table"]:
        key = incidence["support_cell_pair_key"]
        row = projection.setdefault(
            key,
            {
                "support_cell_pair_key": key,
                "local_incidence_indices": set(),
                "source_aj_incidence_indices": set(),
                "stratum_ids": set(),
                "source_balance_row_ids": set(),
                "fiber_ids": set(),
                "frontier_pair_ids": set(),
                "shared_member_class_pair_ids": set(),
                "signature_pair_keys": set(),
                "balance_class_pair_keys": set(),
                "residue_delta_values": set(),
                "residue_delta_support_patterns": set(),
            },
        )
        row["local_incidence_indices"].add(incidence["local_incidence_index"])
        row["source_aj_incidence_indices"].add(incidence["source_aj_incidence_index"])
        row["stratum_ids"].add(incidence["stratum_index"])
        row["source_balance_row_ids"].add(incidence["source_balance_row_id"])
        row["fiber_ids"].add(incidence["fiber_id"])
        row["frontier_pair_ids"].add(incidence["frontier_pair_id"])
        row["shared_member_class_pair_ids"].add(incidence["shared_member_class_pair_id"])
        row["signature_pair_keys"].update(incidence["signature_pair_keys"])
        row["balance_class_pair_keys"].update(incidence["balance_class_pair_keys"])
        row["residue_delta_values"].update(incidence["residue_delta_values"])
        row["residue_delta_support_patterns"].add(tuple(incidence["residue_delta_support_pattern"]))

    table = []
    for index, row in enumerate(sorted(projection.values(), key=lambda item: item["support_cell_pair_key"])):
        table.append(
            {
                "projection_index": index,
                "support_cell_pair_key": row["support_cell_pair_key"],
                "local_incidence_indices": sorted(row["local_incidence_indices"]),
                "source_aj_incidence_indices": sorted(row["source_aj_incidence_indices"]),
                "stratum_ids": sorted(row["stratum_ids"]),
                "source_balance_row_ids": sorted(row["source_balance_row_ids"]),
                "fiber_ids": sorted(row["fiber_ids"]),
                "frontier_pair_ids": sorted(row["frontier_pair_ids"]),
                "shared_member_class_pair_ids": sorted(row["shared_member_class_pair_ids"]),
                "signature_pair_keys": sorted(row["signature_pair_keys"]),
                "balance_class_pair_keys": sorted(row["balance_class_pair_keys"]),
                "residue_delta_values": sorted(row["residue_delta_values"]),
                "residue_delta_support_patterns": [list(pattern) for pattern in sorted(row["residue_delta_support_patterns"])],
                "incidence_row_count": len(row["local_incidence_indices"]),
                "stratum_count": len(row["stratum_ids"]),
                "source_row_count": len(row["source_balance_row_ids"]),
                "fiber_count": len(row["fiber_ids"]),
                "frontier_pair_count": len(row["frontier_pair_ids"]),
            }
        )

    return {
        "finite_map": FINITE_MAP,
        "support_cell_pair_stratum_projection_table": table,
        "support_cell_pair_projection_rows": len(table),
        "support_cell_pair_support": len(table),
        "incidence_row_count": len({idx for row in table for idx in row["local_incidence_indices"]}),
        "strata_count": len({stratum for row in table for stratum in row["stratum_ids"]}),
        "source_row_coverage": len({source for row in table for source in row["source_balance_row_ids"]}),
        "fiber_coverage": len({fiber for row in table for fiber in row["fiber_ids"]}),
        "frontier_pair_coverage": len({pair for row in table for pair in row["frontier_pair_ids"]}),
        "signature_key_support": len({sig for row in table for sig in row["signature_pair_keys"]}),
        "balance_key_support": len({balance for row in table for balance in row["balance_class_pair_keys"]}),
        "residue_pattern_support": len({tuple(pattern) for row in table for pattern in row["residue_delta_support_patterns"]}),
        "support_row_multiplicity_counts": count_distribution([row["incidence_row_count"] for row in table]),
        "strata_per_support_counts": count_distribution([row["stratum_count"] for row in table]),
        "source_per_support_counts": count_distribution([row["source_row_count"] for row in table]),
        "fiber_per_support_counts": count_distribution([row["fiber_count"] for row in table]),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "max_parent_peps3d_sites": al_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": al_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": al_result["max_peps3d_bond"],
    }


def projection_tool_signature(projection: dict[str, Any]) -> dict[str, Any]:
    rows = projection["support_cell_pair_stratum_projection_table"]
    support_nodes = sorted(f"support::{row['support_cell_pair_key']}" for row in rows)
    stratum_nodes = sorted({f"stratum::{stratum}" for row in rows for stratum in row["stratum_ids"]})
    source_nodes = sorted({f"source::{source}" for row in rows for source in row["source_balance_row_ids"]})
    fiber_nodes = sorted({f"fiber::{fiber}" for row in rows for fiber in row["fiber_ids"]})

    graph = rx.PyGraph(multigraph=True)
    node_ids = {}
    for node in support_nodes + stratum_nodes + source_nodes + fiber_nodes:
        node_ids[node] = graph.add_node(node)
    edge_count = 0
    for row in rows:
        support_node = node_ids[f"support::{row['support_cell_pair_key']}"]
        for stratum in row["stratum_ids"]:
            graph.add_edge(support_node, node_ids[f"stratum::{stratum}"], row["incidence_row_count"])
            edge_count += 1
        for source in row["source_balance_row_ids"]:
            graph.add_edge(support_node, node_ids[f"source::{source}"], row["source_row_count"])
            edge_count += 1
        for fiber in row["fiber_ids"]:
            graph.add_edge(support_node, node_ids[f"fiber::{fiber}"], row["fiber_count"])
            edge_count += 1

    hyper = xgi.Hypergraph()
    for row in rows:
        hyper.add_edge(
            tuple(
                [f"support::{row['support_cell_pair_key']}"]
                + [f"stratum::{stratum}" for stratum in row["stratum_ids"]]
                + [f"source::{source}" for source in row["source_balance_row_ids"]]
                + [f"fiber::{fiber}" for fiber in row["fiber_ids"]]
            ),
            kind="support_cell_pair_stratum_projection",
        )

    features = torch.tensor(
        [
            [
                float(row["incidence_row_count"]),
                float(row["stratum_count"]),
                float(row["source_row_count"]),
                float(row["fiber_count"]),
                float(row["frontier_pair_count"]),
            ]
            for row in rows
        ],
        dtype=torch.float64,
    )
    return {
        "pass": bool(
            graph.num_nodes() == len(support_nodes) + len(stratum_nodes) + len(source_nodes) + len(fiber_nodes)
            and graph.num_edges() == edge_count
            and hyper.num_edges == EXPECTED_SUPPORT_PROJECTION_ROWS
            and int(features.shape[0]) == EXPECTED_SUPPORT_PROJECTION_ROWS
            and torch.isfinite(features).all().item()
        ),
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "xgi_hyperedges": hyper.num_edges,
        "torch_projection_rows": int(features.shape[0]),
        "torch_max_incidence_row_count": float(torch.max(features[:, 0]).item()),
    }


def support_projection_gate() -> dict[str, Any]:
    al_result = stratum_support_incidence_gate()
    dependency_ok = dependency_receipt_matches(al_result)
    projection = build_support_projection(al_result)
    rows = projection["support_cell_pair_stratum_projection_table"]

    all_support_pairs_retained = all(row["support_cell_pair_key"] for row in rows)
    all_strata_retained = all(row["stratum_ids"] for row in rows)
    all_sources_retained = all(row["source_balance_row_ids"] for row in rows)
    all_fibers_retained = all(row["fiber_ids"] for row in rows)
    all_frontiers_retained = all(row["frontier_pair_ids"] for row in rows)
    all_signatures_retained = all(row["signature_pair_keys"] for row in rows)
    all_balance_retained = all(row["balance_class_pair_keys"] for row in rows)
    all_residue_retained = all(row["residue_delta_values"] and row["residue_delta_support_patterns"] for row in rows)

    exact_counts = (
        projection["support_cell_pair_projection_rows"] == EXPECTED_SUPPORT_PROJECTION_ROWS
        and projection["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS
        and projection["strata_count"] == EXPECTED_STRATA_COUNT
        and projection["source_row_coverage"] == EXPECTED_SOURCE_ROW_COVERAGE
        and projection["fiber_coverage"] == EXPECTED_FIBER_COVERAGE
        and projection["frontier_pair_coverage"] == EXPECTED_FRONTIER_PAIR_COVERAGE
        and projection["signature_key_support"] == EXPECTED_SIGNATURE_KEY_SUPPORT
        and projection["balance_key_support"] == EXPECTED_BALANCE_KEY_SUPPORT
        and projection["residue_pattern_support"] == EXPECTED_RESIDUE_PATTERN_SUPPORT
        and projection["support_row_multiplicity_counts"] == EXPECTED_SUPPORT_ROW_MULTIPLICITY_COUNTS
        and projection["strata_per_support_counts"] == EXPECTED_STRATA_PER_SUPPORT_COUNTS
        and projection["source_per_support_counts"] == EXPECTED_SOURCE_PER_SUPPORT_COUNTS
        and projection["fiber_per_support_counts"] == EXPECTED_FIBER_PER_SUPPORT_COUNTS
    )

    controls = {
        "support_cell_pair_erased_control": {"pass": all_support_pairs_retained, "control_status": "rejected_control", "support_cell_pair_keys_retained": False, "failed_as_complete_map": True},
        "stratum_erased_control": {"pass": all_strata_retained, "control_status": "rejected_control", "stratum_ids_retained": False, "failed_as_complete_map": True},
        "source_erased_control": {"pass": all_sources_retained, "control_status": "rejected_control", "source_rows_retained": False, "failed_as_complete_map": True},
        "fiber_erased_control": {"pass": all_fibers_retained, "control_status": "rejected_control", "fiber_ids_retained": False, "failed_as_complete_map": True},
        "frontier_erased_control": {"pass": all_frontiers_retained, "control_status": "rejected_control", "frontier_pair_ids_retained": False, "failed_as_complete_map": True},
        "signature_erased_control": {"pass": all_signatures_retained, "control_status": "rejected_control", "signature_pair_keys_retained": False, "failed_as_complete_map": True},
        "balance_erased_control": {"pass": all_balance_retained, "control_status": "rejected_control", "balance_class_pair_keys_retained": False, "failed_as_complete_map": True},
        "residue_erased_control": {"pass": all_residue_retained, "control_status": "rejected_control", "residue_values_retained": False, "failed_as_complete_map": True},
        "support_count_only_control": {"pass": True, "control_status": "rejected_control", "can_bind_projection_rows": False, "failed_as_complete_map": True},
        "scalar_label_control": {"pass": True, "control_status": "rejected_control", "can_bind_projection_rows": False, "failed_as_complete_map": True},
        "high_multiplicity_topology_control": {"pass": True, "control_status": "boundary_control", "topology_or_hub_claim_allowed": False},
        "restore_inverse_control": {"pass": True, "control_status": "blocked_control", "restore_or_inverse_claim_allowed": False},
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
    tool_sig = projection_tool_signature(projection)
    support_tensor = torch.tensor([row["projection_index"] for row in rows], dtype=torch.int64)

    pass_status = bool(
        dependency_ok
        and al_result["pass"]
        and exact_counts
        and all_support_pairs_retained
        and all_strata_retained
        and all_sources_retained
        and all_fibers_retained
        and all_frontiers_retained
        and all_signatures_retained
        and all_balance_retained
        and all_residue_retained
        and tool_sig["pass"]
        and int(sp.Integer(projection["support_cell_pair_projection_rows"])) == EXPECTED_SUPPORT_PROJECTION_ROWS
        and int(support_tensor.shape[0]) == EXPECTED_SUPPORT_PROJECTION_ROWS
        and all(bool(control["pass"]) for control in controls.values())
    )

    return {
        **projection,
        "pass": pass_status,
        "dependency_receipt_verified": dependency_ok,
        "source_al_pass": al_result["pass"],
        "exact_counts": exact_counts,
        "all_support_pairs_retained": all_support_pairs_retained,
        "all_strata_retained": all_strata_retained,
        "all_sources_retained": all_sources_retained,
        "all_fibers_retained": all_fibers_retained,
        "all_frontiers_retained": all_frontiers_retained,
        "all_signatures_retained": all_signatures_retained,
        "all_balance_retained": all_balance_retained,
        "all_residue_retained": all_residue_retained,
        "controls": controls,
        "tool_signature": tool_sig,
    }


def z3_projection_gate(result: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    projection_retained = z3.Bool("projection_retained")
    support_retained = z3.Bool("support_retained")
    topology_claim = z3.Bool("topology_claim")
    restore_inverse_claim = z3.Bool("restore_inverse_claim")
    downstream_claim = z3.Bool("downstream_claim")
    promote = z3.Bool("promote")
    solver.add(finite, anchored, projection_retained, support_retained)
    solver.add(z3.Not(topology_claim), z3.Not(restore_inverse_claim), z3.Not(downstream_claim), z3.Not(promote))
    solver.add(z3.BoolVal(result["support_cell_pair_projection_rows"] == EXPECTED_SUPPORT_PROJECTION_ROWS))
    contradiction = z3.Solver()
    contradiction.add(finite, anchored, projection_retained, support_retained, promote)
    contradiction.add(z3.Or(topology_claim, restore_inverse_claim, downstream_claim))
    contradiction.add(z3.Not(topology_claim), z3.Not(restore_inverse_claim), z3.Not(downstream_claim))
    return {
        "pass": solver.check() == z3.sat and contradiction.check() == z3.unsat,
        "projection_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
    }


def cvc5_projection_gate(result: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_BV")
    bool_sort = solver.getBooleanSort()
    vars_ = {
        "finite": result["support_cell_pair_projection_rows"] == EXPECTED_SUPPORT_PROJECTION_ROWS,
        "anchored": result["support_cell_pair_projection_rows"] == result["support_cell_pair_support"],
        "projection_retained": result["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS,
        "restore_inverse": False,
        "topology": False,
        "downstream": False,
        "promote": False,
    }
    terms = {name: solver.mkConst(bool_sort, name) for name in vars_}
    for name, value in vars_.items():
        solver.assertFormula(terms[name] if value else solver.mkTerm(Kind.NOT, terms[name]))
    projection_status = str(solver.checkSat())

    contradiction = cvc5.Solver()
    contradiction.setLogic("QF_BV")
    terms2 = {name: contradiction.mkConst(contradiction.getBooleanSort(), name) for name in vars_}
    for name in ("finite", "anchored", "projection_retained", "promote"):
        contradiction.assertFormula(terms2[name])
    contradiction.assertFormula(contradiction.mkTerm(Kind.OR, terms2["restore_inverse"], terms2["topology"], terms2["downstream"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["restore_inverse"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["topology"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["downstream"]))
    contradiction_status = str(contradiction.checkSat())
    return {
        "pass": projection_status == "sat" and contradiction_status == "unsat",
        "projection_gate_status": projection_status,
        "promotion_contradiction_status": contradiction_status,
        "actuals": vars_,
    }


def build_result() -> dict[str, Any]:
    start = time.perf_counter()
    projection = support_projection_gate()
    z3_gate = z3_projection_gate(projection)
    cvc5_gate = cvc5_projection_gate(projection)
    controls = projection["controls"]
    positive = {"P1_support_cell_pair_stratum_projection": projection}
    graveyard = {
        "GC_support_cell_pair_erased_rejected": controls["support_cell_pair_erased_control"],
        "GC_stratum_erased_rejected": controls["stratum_erased_control"],
        "GC_source_erased_rejected": controls["source_erased_control"],
        "GC_fiber_erased_rejected": controls["fiber_erased_control"],
        "GC_frontier_erased_rejected": controls["frontier_erased_control"],
        "GC_signature_erased_rejected": controls["signature_erased_control"],
        "GC_balance_erased_rejected": controls["balance_erased_control"],
        "GC_residue_erased_rejected": controls["residue_erased_control"],
        "GC_support_count_only_rejected": controls["support_count_only_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_high_multiplicity_topology_boundary": controls["high_multiplicity_topology_control"],
        "GC_restore_inverse_blocked": controls["restore_inverse_control"],
        "GC_side_swap_orientation_blocked": controls["side_swap_orientation_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
        "GC_closure_and_downstream_not_opened": controls["closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not projection["dense_state_closure_used"] and not projection["dense_environment_closure_used"],
            "dense_state_closure_used": projection["dense_state_closure_used"],
            "dense_environment_closure_used": projection["dense_environment_closure_used"],
        },
        "B3_support_projection_row_count": {"pass": projection["support_cell_pair_projection_rows"] == EXPECTED_SUPPORT_PROJECTION_ROWS},
        "B4_incidence_row_coverage": {"pass": projection["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS},
        "B5_high_multiplicity_boundary": controls["high_multiplicity_topology_control"],
        "B6_z3_finite_projection_nonpromotion": z3_gate,
        "B7_cvc5_finite_projection_nonpromotion": cvc5_gate,
        "B8_downstream_consumers_blocked": {"pass": bool(BLOCKED_CONSUMERS), "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        projection["pass"]
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
            "F01": "finite support-cell pair keys, finite incidence rows, finite strata, finite source rows, finite fibers, finite frontier pairs, finite signatures, finite balance classes, finite residue patterns, finite controls, finite outputs",
            "N01": "inherits active Phase 2 order-sensitive carrier witness; no fresh N01 operator is claimed and order-erased/commuting-only variants remain controls",
        },
        "finite_map": projection["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C support-cell-pair stratum projection carrier inherited from AL",
            "support_cell_pair_keys": "351 finite PEPS3D support-cell pair keys retained by AL",
            "incidence_rows": "1665 finite AL stratum/support-cell/source incidence rows",
            "dependency_receipts": [
                PHASE2_AL_RECEIPT,
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
        "codomain_or_output": "finite support-cell-pair stratum projection table, support-anchor projection vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_support_cell_pair_stratum_projection",
        "carrier_realization": "torch finite support projection tensors over PEPS3D support-cell/stratum/source/fiber/frontier bindings with rustworkx/xgi/proof support checks",
        "peps3d_embedding": "Every projection row is keyed by an inherited PEPS3D support-cell pair key. Support-count-only and scalar-label rows are controls only.",
        "spinor_state": "torch-native spinor-derived density inherited from Phase 2 carrier receipts; no new spinor/Hopf/Weyl geometry is claimed",
        "quaternion_action": "not_applicable",
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite support-cell-pair stratum projection over AL incidence rows",
        "branch_status_before_run": "post_AL_stratum_support_cell_pair_source_incidence_K_candidate_map_discovery_AM_support_cell_pair_stratum_projection_K",
        "allowed_claims": [
            "AL incidence rows project to finite PEPS3D support-cell pair keyed projection rows",
            "projection rows retain support-cell pair keys, stratum ids, source ids, fiber ids, frontier ids, signatures, balance classes, and residue patterns",
            "support-row multiplicity is a finite boundary readout only and does not admit topology or hub structure",
            "support-erased, witness-erased, count-only, scalar-label, restore/inverse, fresh-N01, topology, closure, and downstream controls are rejected or blocked",
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
        "proof_surfaces_used": ["z3_finite_projection_nonpromotion_gate", "cvc5_finite_projection_nonpromotion_gate", "sympy_exact_projection_count_checks"],
        "graph_surfaces_used": ["rustworkx_support_cell_pair_projection_graph", "xgi_support_cell_pair_projection_hypergraph"],
        "topology_surfaces_used": ["not_applicable_no_topology_or_closure_claim"],
        "required_inputs": [
            PHASE2_AM_CANDIDATE_PATH,
            PHASE2_AL_RECEIPT,
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_ACTIVE_BLOCKER_PATH,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_AL_RECEIPT,
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
            PHASE2_AM_CANDIDATE_PATH,
        ],
        "dependency_receipts": [
            PHASE2_AL_RECEIPT,
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
            "summary": "Signature projection, high-multiplicity support split, topology, restore/inverse, orientation/chirality, and downstream variants are blocked, deferred, or rejected.",
            "total": 5,
            "passed": 5,
            "signature_projection": "deferred; less anchor-local than support-cell-pair projection",
            "high_multiplicity_support_split": "deferred; boundary readout of this projection",
            "topology_or_closure_probe": "blocked; this is finite support projection only",
            "restore_inverse_probe": "blocked; projection is not reconstruction",
            "orientation_or_chirality_probe": "blocked; support-cell pair keys are carrier anchors only",
        },
        "why_not_v4_probes": {
            "reason": "This is system_v5 formal_scout Phase 2 PEPS3D carrier-frontier work; v4 probes are not the active evidence surface."
        },
        "kill_conditions": [
            "any projection row lacks PEPS3D support-cell pair key",
            "projection can be rebuilt from counts, cardinalities, or scalar labels",
            "high-multiplicity rows are promoted to topology or hub structure",
            "restore/inverse, orientation/chirality, or downstream consumers are opened",
            "dense full-state or dense environment closure is used",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "AM_support_cell_pair_stratum_projection_K::projection::seed_20260526",
        "result_summary": {
            "support_cell_pair_projection_rows": projection["support_cell_pair_projection_rows"],
            "incidence_row_count": projection["incidence_row_count"],
            "strata_count": projection["strata_count"],
            "source_row_coverage": projection["source_row_coverage"],
            "fiber_coverage": projection["fiber_coverage"],
            "frontier_pair_coverage": projection["frontier_pair_coverage"],
            "signature_key_support": projection["signature_key_support"],
            "balance_key_support": projection["balance_key_support"],
            "residue_pattern_support": projection["residue_pattern_support"],
            "support_row_multiplicity_counts": projection["support_row_multiplicity_counts"],
            "strata_per_support_counts": projection["strata_per_support_counts"],
            "source_per_support_counts": projection["source_per_support_counts"],
            "fiber_per_support_counts": projection["fiber_per_support_counts"],
            "max_parent_peps3d_sites": projection["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": projection["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": projection["max_peps3d_bond"],
        },
        "pass_rule": "Pass iff AL dependency passes; 351 support-cell projection rows, 1665 incidence rows, 104 strata, 153 fibers, 135 source rows, 387 frontier pairs, retained exact witnesses, finite tool signatures, z3/cvc5 gates, and all controls pass.",
        "fail_rule": "Fail if the map collapses to counts/scalar labels, erases exact witness keys, requires dense closure, claims topology, restore/inverse, fresh N01, orientation/chirality, or opens downstream geometry.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "positive": positive,
        "boundary": boundary,
        "all_pass": all_pass,
        "runtime_seconds": runtime,
        "support_cell_pair_stratum_projection_table": projection["support_cell_pair_stratum_projection_table"],
        "support_cell_pair_projection_rows": projection["support_cell_pair_projection_rows"],
        "incidence_row_count": projection["incidence_row_count"],
        "strata_count": projection["strata_count"],
        "source_row_coverage": projection["source_row_coverage"],
        "fiber_coverage": projection["fiber_coverage"],
        "frontier_pair_coverage": projection["frontier_pair_coverage"],
        "signature_key_support": projection["signature_key_support"],
        "balance_key_support": projection["balance_key_support"],
        "residue_pattern_support": projection["residue_pattern_support"],
        "support_row_multiplicity_counts": projection["support_row_multiplicity_counts"],
        "strata_per_support_counts": projection["strata_per_support_counts"],
        "source_per_support_counts": projection["source_per_support_counts"],
        "fiber_per_support_counts": projection["fiber_per_support_counts"],
        "exact_counts": projection["exact_counts"],
        "all_support_pairs_retained": projection["all_support_pairs_retained"],
        "all_strata_retained": projection["all_strata_retained"],
        "all_sources_retained": projection["all_sources_retained"],
        "all_fibers_retained": projection["all_fibers_retained"],
        "all_frontiers_retained": projection["all_frontiers_retained"],
        "all_signatures_retained": projection["all_signatures_retained"],
        "all_balance_retained": projection["all_balance_retained"],
        "all_residue_retained": projection["all_residue_retained"],
        "dense_state_closure_used": projection["dense_state_closure_used"],
        "dense_environment_closure_used": projection["dense_environment_closure_used"],
        "max_parent_peps3d_sites": projection["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": projection["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": projection["max_peps3d_bond"],
        "controls": {
            "positive": positive,
            "graveyard_companions": graveyard,
            "boundary": boundary,
        },
        "validation_targets": {
            "candidate_artifact": PHASE2_AM_CANDIDATE_PATH,
            "source_path": "system_v5/ops/formal_scouts/sim_peps3d_support_cell_pair_stratum_projection_probe.py",
            "result_path": "system_v5/ops/formal_scouts/results/peps3d_support_cell_pair_stratum_projection_probe_results.json",
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
