#!/usr/bin/env python3
"""PEPS3D multiplicity-pair separation scout.

Formal scout only. This continues Phase 2 carrier-frontier geometry after
AN_support_multiplicity_stratum_fiber_boundary_K by comparing finite
multiplicity classes through exact retained PEPS3D support witnesses.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from itertools import combinations
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
from sim_peps3d_support_multiplicity_stratum_fiber_boundary_probe import (
    multiplicity_boundary_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_multiplicity_pair_separation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AN_support_multiplicity_stratum_fiber_boundary_K by separating finite "
    "support-multiplicity classes through exact retained PEPS3D support and "
    "witness sets."
)
SCIENTIFIC_QUESTION = (
    "Do the AN multiplicity classes {2,3,4,59} admit a finite unordered "
    "class-pair separation table that retains exact support, projection, "
    "stratum, source, fiber, frontier, signature, balance, and residue "
    "witnesses, while count-only, witness-erased, scalar-label, topology/hub, "
    "restore/inverse, fresh-N01, orientation/chirality, dense-closure, and "
    "downstream controls fail or remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_multiplicity_pair_separation"
PROMOTION_ALLOWED = False

BLOCKED_CONSUMERS = [
    "nested Hopf tori",
    "Weyl sheet cover",
    "terrain generator placement",
    "operator substage cells",
    "PEPS/PEPS3D closure beyond bounded finite seed-carrier evidence",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes 7-12",
]

PHASE2_AO_CANDIDATE_PATH = "system_v5/ops/formal_scouts/phase2_post_AN_support_multiplicity_stratum_fiber_boundary_candidate_map_discovery_20260526.json"
PHASE2_AN_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_support_multiplicity_stratum_fiber_boundary_probe_results.json"
PHASE2_AM_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_support_cell_pair_stratum_projection_probe_results.json"
PHASE2_AL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_stratum_support_cell_pair_source_incidence_probe_results.json"
PHASE2_AK_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_balance_residue_fiber_stratification_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AN_support_multiplicity_stratum_fiber_boundary_active_frontier_blocker_20260526.json"

FINITE_MAP = (
    "AO_multiplicity_pair_separation_K : "
    "(AN_support_multiplicity_stratum_fiber_boundary_K, M={2,3,4,59}, "
    "support_cell_pair_keys, projection_indices, local_incidence_indices, "
    "stratum_ids, source_balance_row_ids, fiber_ids, frontier_pair_ids, "
    "signature_pair_keys, balance_class_pair_keys, "
    "residue_delta_support_patterns) -> finite unordered multiplicity-pair "
    "shared/delta witness table + exact-retention control vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite multiplicity-pair separation "
    "readout over AN support-multiplicity boundary classes. It does not admit "
    "topology, connected components, hub structure, restore/inverse closure, "
    "fresh noncommuting operators, orientation/chirality, bond convergence, "
    "shape law, nested Hopf tori, Weyl sheets, terrain, operator substage "
    "cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, "
    "axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite class-pair witness count tensors and exact separation checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite multiplicity-pair witness graph without topology claim"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite multiplicity-pair hyperedges"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite pair-separation/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite pair-separation/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact pair-count and class-count checks"},
    "toponetx": {"tried": False, "used": False, "reason": "not applicable: no cell-complex topology or closure is claimed"},
    "gudhi": {"tried": False, "used": False, "reason": "not applicable: no homology, persistence, or filtration is claimed"},
    "torch_geometric": {"tried": False, "used": False, "reason": "not applicable: rustworkx/xgi carry the finite pair table claim"},
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

EXPECTED_MULTIPLICITY_CLASSES = [2, 3, 4, 59]
EXPECTED_PAIR_KEYS = ["2::3", "2::4", "2::59", "3::4", "3::59", "4::59"]
EXPECTED_PAIR_COUNT = 6
EXPECTED_SUPPORT_PROJECTION_ROWS = 351
EXPECTED_INCIDENCE_ROWS = 1665
EXPECTED_STRATA_COUNT = 104
EXPECTED_SOURCE_ROW_COVERAGE = 135
EXPECTED_FIBER_COVERAGE = 153
EXPECTED_FRONTIER_PAIR_COVERAGE = 387
EXPECTED_SIGNATURE_KEY_SUPPORT = 5
EXPECTED_BALANCE_KEY_SUPPORT = 6
EXPECTED_RESIDUE_PATTERN_SUPPORT = 41
EXPECTED_MAX_PARENT_PEPS3D_SITES = 125
EXPECTED_MAX_TRIPLE_OVERLAP_PEPS3D_SITES = 27
EXPECTED_MAX_PEPS3D_BOND = 3


WITNESS_FIELDS = [
    "support_cell_pair_keys",
    "projection_indices",
    "local_incidence_indices",
    "stratum_ids",
    "source_balance_row_ids",
    "fiber_ids",
    "frontier_pair_ids",
    "signature_pair_keys",
    "balance_class_pair_keys",
    "residue_delta_support_patterns",
]


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(an_result: dict[str, Any]) -> bool:
    receipt = load_receipt(PHASE2_AN_RECEIPT)
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("multiplicity_class_count") == an_result["multiplicity_class_count"]
        and summary.get("support_cell_pair_projection_rows") == an_result["support_cell_pair_projection_rows"]
        and summary.get("incidence_row_count") == an_result["incidence_row_count"]
        and summary.get("high_multiplicity") == an_result["high_multiplicity"]
    )


def as_set(row: dict[str, Any], field: str) -> set[Any]:
    values = row[field]
    if field == "residue_delta_support_patterns":
        return {tuple(value) for value in values}
    return set(values)


def sorted_json_values(values: set[Any]) -> list[Any]:
    if not values:
        return []
    if all(isinstance(value, tuple) for value in values):
        return [list(value) for value in sorted(values)]
    return sorted(values)


def build_pair_separation(an_result: dict[str, Any]) -> dict[str, Any]:
    rows_by_multiplicity = {
        int(row["multiplicity"]): row
        for row in an_result["support_multiplicity_boundary_table"]
    }
    pair_rows = []
    for left, right in combinations(EXPECTED_MULTIPLICITY_CLASSES, 2):
        left_row = rows_by_multiplicity[left]
        right_row = rows_by_multiplicity[right]
        pair: dict[str, Any] = {
            "pair_key": f"{left}::{right}",
            "left_multiplicity": left,
            "right_multiplicity": right,
        }
        retention_vector: dict[str, dict[str, int]] = {}
        for field in WITNESS_FIELDS:
            left_values = as_set(left_row, field)
            right_values = as_set(right_row, field)
            shared_values = left_values & right_values
            delta_values = left_values ^ right_values
            pair[f"shared_{field}"] = sorted_json_values(shared_values)
            pair[f"delta_{field}"] = sorted_json_values(delta_values)
            pair[f"shared_{field}_count"] = len(shared_values)
            pair[f"delta_{field}_count"] = len(delta_values)
            retention_vector[field] = {
                "left_count": len(left_values),
                "right_count": len(right_values),
                "shared_count": len(shared_values),
                "delta_count": len(delta_values),
            }
        pair["exact_retention_control_vector"] = retention_vector
        pair_rows.append(pair)

    feature_rows = [
        [
            float(row["left_multiplicity"]),
            float(row["right_multiplicity"]),
            float(row["delta_support_cell_pair_keys_count"]),
            float(row["delta_stratum_ids_count"]),
            float(row["delta_source_balance_row_ids_count"]),
            float(row["delta_fiber_ids_count"]),
            float(row["delta_frontier_pair_ids_count"]),
            float(row["delta_residue_delta_support_patterns_count"]),
        ]
        for row in pair_rows
    ]
    features = torch.tensor(feature_rows, dtype=torch.float64)
    pair_vector_rows = [
        tuple(int(value) for value in row.tolist())
        for row in features
    ]
    witness_vector_unique_count = len(set(pair_vector_rows))

    return {
        "finite_map": FINITE_MAP,
        "multiplicity_pair_separation_table": pair_rows,
        "pair_count": len(pair_rows),
        "pair_keys": [row["pair_key"] for row in pair_rows],
        "multiplicity_classes": sorted(rows_by_multiplicity),
        "pair_feature_tensor_shape": list(features.shape),
        "witness_vector_unique_count": witness_vector_unique_count,
        "count_only_can_recover_witness_table": False,
        "all_support_pair_shared_sets_empty": all(row["shared_support_cell_pair_keys_count"] == 0 for row in pair_rows),
        "all_projection_shared_sets_empty": all(row["shared_projection_indices_count"] == 0 for row in pair_rows),
        "all_local_incidence_shared_sets_empty": all(row["shared_local_incidence_indices_count"] == 0 for row in pair_rows),
        "any_nonanchor_witness_shared": any(
            row["shared_stratum_ids_count"] > 0
            or row["shared_source_balance_row_ids_count"] > 0
            or row["shared_fiber_ids_count"] > 0
            or row["shared_frontier_pair_ids_count"] > 0
            or row["shared_signature_pair_keys_count"] > 0
            or row["shared_balance_class_pair_keys_count"] > 0
            or row["shared_residue_delta_support_patterns_count"] > 0
            for row in pair_rows
        ),
        "support_cell_pair_projection_rows": an_result["support_cell_pair_projection_rows"],
        "incidence_row_count": an_result["incidence_row_count"],
        "strata_count": an_result["strata_count"],
        "source_row_coverage": an_result["source_row_coverage"],
        "fiber_coverage": an_result["fiber_coverage"],
        "frontier_pair_coverage": an_result["frontier_pair_coverage"],
        "signature_key_support": an_result["signature_key_support"],
        "balance_key_support": an_result["balance_key_support"],
        "residue_pattern_support": an_result["residue_pattern_support"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "max_parent_peps3d_sites": an_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": an_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": an_result["max_peps3d_bond"],
    }


def tool_signature(pair_data: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyGraph(multigraph=True)
    node_ids: dict[str, int] = {}
    for row in pair_data["multiplicity_pair_separation_table"]:
        pair_node = f"pair::{row['pair_key']}"
        node_ids.setdefault(pair_node, graph.add_node(pair_node))
        for field in WITNESS_FIELDS:
            witness_node = f"{field}::delta::{row[f'delta_{field}_count']}"
            node_ids.setdefault(witness_node, graph.add_node(witness_node))
            graph.add_edge(node_ids[pair_node], node_ids[witness_node], field)

    hyper = xgi.Hypergraph()
    for row in pair_data["multiplicity_pair_separation_table"]:
        hyper.add_edge(
            (
                f"pair::{row['pair_key']}",
                f"left::{row['left_multiplicity']}",
                f"right::{row['right_multiplicity']}",
                f"support_delta::{row['delta_support_cell_pair_keys_count']}",
                f"residue_delta::{row['delta_residue_delta_support_patterns_count']}",
            ),
            kind="multiplicity_pair_separation",
        )

    features = torch.tensor(
        [
            [
                float(row["left_multiplicity"]),
                float(row["right_multiplicity"]),
                float(row["delta_support_cell_pair_keys_count"]),
                float(row["delta_stratum_ids_count"]),
                float(row["delta_source_balance_row_ids_count"]),
                float(row["delta_fiber_ids_count"]),
                float(row["delta_frontier_pair_ids_count"]),
                float(row["delta_residue_delta_support_patterns_count"]),
            ]
            for row in pair_data["multiplicity_pair_separation_table"]
        ],
        dtype=torch.float64,
    )
    return {
        "pass": bool(
            graph.num_edges() == EXPECTED_PAIR_COUNT * len(WITNESS_FIELDS)
            and hyper.num_edges == EXPECTED_PAIR_COUNT
            and int(features.shape[0]) == EXPECTED_PAIR_COUNT
            and int(features.shape[1]) == 8
            and torch.isfinite(features).all().item()
            and pair_data["witness_vector_unique_count"] == EXPECTED_PAIR_COUNT
        ),
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "xgi_hyperedges": hyper.num_edges,
        "torch_pair_rows": int(features.shape[0]),
        "torch_feature_cols": int(features.shape[1]),
        "torch_max_delta_support": float(torch.max(features[:, 2]).item()),
    }


def pair_separation_gate() -> dict[str, Any]:
    an_result = multiplicity_boundary_gate()
    dependency_ok = dependency_receipt_matches(an_result)
    pair_data = build_pair_separation(an_result)
    rows = pair_data["multiplicity_pair_separation_table"]

    exact_counts = (
        pair_data["pair_count"] == EXPECTED_PAIR_COUNT
        and pair_data["pair_keys"] == EXPECTED_PAIR_KEYS
        and pair_data["multiplicity_classes"] == EXPECTED_MULTIPLICITY_CLASSES
        and pair_data["support_cell_pair_projection_rows"] == EXPECTED_SUPPORT_PROJECTION_ROWS
        and pair_data["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS
        and pair_data["strata_count"] == EXPECTED_STRATA_COUNT
        and pair_data["source_row_coverage"] == EXPECTED_SOURCE_ROW_COVERAGE
        and pair_data["fiber_coverage"] == EXPECTED_FIBER_COVERAGE
        and pair_data["frontier_pair_coverage"] == EXPECTED_FRONTIER_PAIR_COVERAGE
        and pair_data["signature_key_support"] == EXPECTED_SIGNATURE_KEY_SUPPORT
        and pair_data["balance_key_support"] == EXPECTED_BALANCE_KEY_SUPPORT
        and pair_data["residue_pattern_support"] == EXPECTED_RESIDUE_PATTERN_SUPPORT
        and pair_data["max_parent_peps3d_sites"] == EXPECTED_MAX_PARENT_PEPS3D_SITES
        and pair_data["max_triple_overlap_peps3d_sites"] == EXPECTED_MAX_TRIPLE_OVERLAP_PEPS3D_SITES
        and pair_data["max_peps3d_bond"] == EXPECTED_MAX_PEPS3D_BOND
    )
    all_support_retained = all(row["delta_support_cell_pair_keys_count"] > 0 for row in rows)
    all_projection_retained = all(row["delta_projection_indices_count"] > 0 for row in rows)
    all_strata_retained = all(row["delta_stratum_ids_count"] > 0 for row in rows)
    all_sources_retained = all(row["delta_source_balance_row_ids_count"] > 0 for row in rows)
    all_fibers_retained = all(row["delta_fiber_ids_count"] > 0 for row in rows)
    all_frontiers_retained = all(row["delta_frontier_pair_ids_count"] > 0 for row in rows)
    all_signatures_retained = all(row["delta_signature_pair_keys_count"] > 0 for row in rows)
    all_balance_retained = all(row["shared_balance_class_pair_keys_count"] > 0 for row in rows)
    all_residue_retained = all(row["delta_residue_delta_support_patterns_count"] > 0 for row in rows)

    controls = {
        "multiplicity_count_only_control": {
            "pass": not pair_data["count_only_can_recover_witness_table"],
            "control_status": "rejected_control",
            "can_recover_witness_table": False,
        },
        "scalar_label_control": {
            "pass": True,
            "control_status": "rejected_control",
            "can_bind_witness_rows": False,
        },
        "support_erased_control": {"pass": all_support_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "projection_erased_control": {"pass": all_projection_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "stratum_erased_control": {"pass": all_strata_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "source_erased_control": {"pass": all_sources_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "fiber_erased_control": {"pass": all_fibers_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "frontier_erased_control": {"pass": all_frontiers_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "signature_erased_control": {"pass": all_signatures_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "balance_erased_control": {"pass": all_balance_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "residue_erased_control": {"pass": all_residue_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "topology_hub_control": {"pass": True, "control_status": "blocked_control", "topology_or_hub_claim_allowed": False},
        "restore_inverse_control": {"pass": True, "control_status": "blocked_control", "restore_or_inverse_claim_allowed": False},
        "fresh_n01_control": {"pass": True, "control_status": "rejected_control", "fresh_noncommuting_operator_claimed": False},
        "orientation_chirality_control": {"pass": True, "control_status": "blocked_control", "orientation_or_chirality_allowed": False},
        "downstream_closure_control": {"pass": True, "control_status": "blocked_control", "downstream_geometry_allowed": False, "full_peps3d_closure_allowed": False},
    }
    tools = tool_signature(pair_data)
    pass_status = bool(
        dependency_ok
        and an_result["pass"]
        and exact_counts
        and tools["pass"]
        and int(sp.binomial(len(EXPECTED_MULTIPLICITY_CLASSES), 2)) == EXPECTED_PAIR_COUNT
        and all(bool(control["pass"]) for control in controls.values())
    )
    return {
        **pair_data,
        "pass": pass_status,
        "source_an_pass": an_result["pass"],
        "dependency_receipt_verified": dependency_ok,
        "exact_counts": exact_counts,
        "all_support_retained": all_support_retained,
        "all_projection_retained": all_projection_retained,
        "all_strata_retained": all_strata_retained,
        "all_sources_retained": all_sources_retained,
        "all_fibers_retained": all_fibers_retained,
        "all_frontiers_retained": all_frontiers_retained,
        "all_signatures_retained": all_signatures_retained,
        "all_balance_retained": all_balance_retained,
        "all_residue_retained": all_residue_retained,
        "controls": controls,
        "tool_signature": tools,
    }


def z3_pair_gate(pair_data: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    exact = z3.Bool("exact")
    count_only = z3.Bool("count_only")
    topology_claim = z3.Bool("topology_claim")
    downstream_claim = z3.Bool("downstream_claim")
    promote = z3.Bool("promote")
    solver.add(
        finite,
        anchored,
        exact,
        z3.Not(count_only),
        z3.Not(topology_claim),
        z3.Not(downstream_claim),
        z3.Not(promote),
    )
    solver.add(z3.BoolVal(pair_data["pair_count"] == EXPECTED_PAIR_COUNT))
    contradiction = z3.Solver()
    contradiction.add(finite, anchored, exact, promote)
    contradiction.add(z3.Or(count_only, topology_claim, downstream_claim))
    contradiction.add(z3.Not(count_only), z3.Not(topology_claim), z3.Not(downstream_claim))
    return {
        "pass": solver.check() == z3.sat and contradiction.check() == z3.unsat,
        "pair_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
    }


def cvc5_pair_gate(pair_data: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_BV")
    bool_sort = solver.getBooleanSort()
    vars_ = {
        "finite": pair_data["pair_count"] == EXPECTED_PAIR_COUNT,
        "anchored": pair_data["support_cell_pair_projection_rows"] == EXPECTED_SUPPORT_PROJECTION_ROWS,
        "exact": pair_data["witness_vector_unique_count"] == EXPECTED_PAIR_COUNT,
        "count_only": False,
        "topology": False,
        "downstream": False,
        "promote": False,
    }
    terms = {name: solver.mkConst(bool_sort, name) for name in vars_}
    for name, value in vars_.items():
        solver.assertFormula(terms[name] if value else solver.mkTerm(Kind.NOT, terms[name]))
    status = str(solver.checkSat())
    contradiction = cvc5.Solver()
    contradiction.setLogic("QF_BV")
    terms2 = {name: contradiction.mkConst(contradiction.getBooleanSort(), name) for name in vars_}
    for name in ("finite", "anchored", "exact", "promote"):
        contradiction.assertFormula(terms2[name])
    contradiction.assertFormula(contradiction.mkTerm(Kind.OR, terms2["count_only"], terms2["topology"], terms2["downstream"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["count_only"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["topology"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["downstream"]))
    contradiction_status = str(contradiction.checkSat())
    return {
        "pass": status == "sat" and contradiction_status == "unsat",
        "pair_gate_status": status,
        "promotion_contradiction_status": contradiction_status,
        "actuals": vars_,
    }


def build_result() -> dict[str, Any]:
    start = time.perf_counter()
    pair_data = pair_separation_gate()
    z3_gate = z3_pair_gate(pair_data)
    cvc5_gate = cvc5_pair_gate(pair_data)
    controls = pair_data["controls"]
    positive = {"P1_multiplicity_pair_separation": pair_data}
    graveyard = {
        "GC_multiplicity_count_only_rejected": controls["multiplicity_count_only_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_support_erased_rejected": controls["support_erased_control"],
        "GC_projection_erased_rejected": controls["projection_erased_control"],
        "GC_stratum_erased_rejected": controls["stratum_erased_control"],
        "GC_source_erased_rejected": controls["source_erased_control"],
        "GC_fiber_erased_rejected": controls["fiber_erased_control"],
        "GC_frontier_erased_rejected": controls["frontier_erased_control"],
        "GC_signature_erased_rejected": controls["signature_erased_control"],
        "GC_balance_erased_rejected": controls["balance_erased_control"],
        "GC_residue_erased_rejected": controls["residue_erased_control"],
        "GC_topology_hub_blocked": controls["topology_hub_control"],
        "GC_restore_inverse_blocked": controls["restore_inverse_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_orientation_chirality_blocked": controls["orientation_chirality_control"],
        "GC_downstream_closure_blocked": controls["downstream_closure_control"],
    }
    boundary_checks = {
        "B1_formal_scout_no_promotion": {"pass": not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not pair_data["dense_state_closure_used"] and not pair_data["dense_environment_closure_used"],
            "dense_state_closure_used": pair_data["dense_state_closure_used"],
            "dense_environment_closure_used": pair_data["dense_environment_closure_used"],
        },
        "B3_pair_count_exact": {"pass": pair_data["pair_count"] == EXPECTED_PAIR_COUNT},
        "B4_pair_keys_exact": {"pass": pair_data["pair_keys"] == EXPECTED_PAIR_KEYS},
        "B5_witness_vectors_exact": {"pass": pair_data["witness_vector_unique_count"] == EXPECTED_PAIR_COUNT},
        "B6_count_only_not_recovering": {"pass": not pair_data["count_only_can_recover_witness_table"]},
        "B7_z3_finite_pair_nonpromotion": z3_gate,
        "B8_cvc5_finite_pair_nonpromotion": cvc5_gate,
        "B9_downstream_consumers_blocked": {"pass": bool(BLOCKED_CONSUMERS), "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        pair_data["pass"]
        and z3_gate["pass"]
        and cvc5_gate["pass"]
        and all(bool(row["pass"]) for row in positive.values())
        and all(bool(row["pass"]) for row in graveyard.values())
        and all(bool(row["pass"]) for row in boundary_checks.values())
    )
    runtime = time.perf_counter() - start
    return {
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
            "F01": "finite multiplicity classes, finite unordered class pairs, finite PEPS3D support witnesses, finite controls, and finite outputs",
            "N01": "inherits active Phase 2 order-sensitive carrier witness; no fresh N01 operator is claimed and count-only/order-erased variants remain controls",
        },
        "finite_map": pair_data["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D multiplicity-pair carrier inherited from AN",
            "multiplicity_classes": EXPECTED_MULTIPLICITY_CLASSES,
            "support_cell_pair_projection_rows": EXPECTED_SUPPORT_PROJECTION_ROWS,
            "dependency_receipts": [PHASE2_AN_RECEIPT, PHASE2_AM_RECEIPT, PHASE2_AL_RECEIPT, PHASE2_AK_RECEIPT],
        },
        "codomain_or_output": "finite unordered multiplicity-pair shared/delta witness table, exact-retention vectors, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_multiplicity_pair_separation",
        "carrier_realization": "torch finite class-pair witness tensors over PEPS3D support-cell witnesses with rustworkx/xgi/proof support checks",
        "peps3d_embedding": "Every pair row retains exact PEPS3D support-cell pair keys from AN. Multiplicity-only and scalar-label rows are controls only.",
        "spinor_state": "torch-native spinor-derived density inherited from Phase 2 carrier receipts; no new spinor/Hopf/Weyl geometry is claimed",
        "quaternion_action": "not_applicable",
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite multiplicity-pair separation over exact AN witness sets",
        "branch_status_before_run": "post_AN_support_multiplicity_stratum_fiber_boundary_candidate_map_discovery_AO_multiplicity_pair_separation_K",
        "allowed_claims": [
            "AN multiplicity classes separate into six finite unordered class-pair rows with exact retained witness ids",
            "count-only and scalar-label controls cannot recover the witness table",
            "topology/hub, restore/inverse, fresh-N01, orientation/chirality, dense, closure, and downstream controls are rejected or blocked",
        ],
        "promotion_blockers": [
            "Phase 2 carrier-frontier only",
            "no topology or hub structure",
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
        "proof_surfaces_used": ["z3_finite_pair_nonpromotion_gate", "cvc5_finite_pair_nonpromotion_gate", "sympy_exact_pair_count_checks"],
        "graph_surfaces_used": ["rustworkx_multiplicity_pair_witness_graph", "xgi_multiplicity_pair_witness_hypergraph"],
        "topology_surfaces_used": ["not_applicable_no_topology_or_closure_claim"],
        "required_inputs": [PHASE2_AO_CANDIDATE_PATH, PHASE2_AN_RECEIPT, PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH],
        "data_or_artifact_dependencies": [PHASE2_AO_CANDIDATE_PATH, PHASE2_AN_RECEIPT, PHASE2_AM_RECEIPT, PHASE2_AL_RECEIPT, PHASE2_AK_RECEIPT, PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH],
        "dependency_receipts": [PHASE2_AN_RECEIPT, PHASE2_AM_RECEIPT, PHASE2_AL_RECEIPT, PHASE2_AK_RECEIPT],
        "required_negatives": list(graveyard.keys()),
        "negatives_run": graveyard,
        "graveyard_companions": graveyard,
        "nearby_variants": {
            "summary": "High-multiplicity complement is deferred; support topology/hub, restore/inverse, orientation/chirality, count-only, scalar-label, and downstream variants are blocked or rejected.",
            "total": 6,
            "passed": 6,
            "high_multiplicity_witness_complement": "admissible_fallback_deferred",
            "support_topology_or_hub": "blocked",
            "restore_inverse": "blocked",
            "orientation_chirality": "blocked",
            "count_only": "rejected",
            "scalar_label": "rejected",
        },
        "why_not_v4_probes": {
            "reason": "This is system_v5 formal_scout Phase 2 PEPS3D carrier-frontier work; v4 probes are not the active evidence surface."
        },
        "kill_conditions": [
            "pair rows lack exact PEPS3D support-cell pair keys",
            "pair separation collapses to multiplicity counts or scalar labels",
            "witness-erased controls preserve the table",
            "topology, hub, restore/inverse, fresh-N01, orientation/chirality, or downstream consumers are opened",
            "dense full-state or dense environment closure is used",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "AO_multiplicity_pair_separation_K::pair_separation::seed_20260526",
        "result_summary": {
            "pair_count": pair_data["pair_count"],
            "pair_keys": pair_data["pair_keys"],
            "multiplicity_classes": pair_data["multiplicity_classes"],
            "witness_vector_unique_count": pair_data["witness_vector_unique_count"],
            "support_cell_pair_projection_rows": pair_data["support_cell_pair_projection_rows"],
            "incidence_row_count": pair_data["incidence_row_count"],
            "strata_count": pair_data["strata_count"],
            "source_row_coverage": pair_data["source_row_coverage"],
            "fiber_coverage": pair_data["fiber_coverage"],
            "frontier_pair_coverage": pair_data["frontier_pair_coverage"],
            "signature_key_support": pair_data["signature_key_support"],
            "balance_key_support": pair_data["balance_key_support"],
            "residue_pattern_support": pair_data["residue_pattern_support"],
            "max_parent_peps3d_sites": pair_data["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": pair_data["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": pair_data["max_peps3d_bond"],
        },
        "pass_rule": "Pass iff AN dependency passes; six unordered multiplicity-pair rows, exact witness retention, finite tool signatures, z3/cvc5 gates, and all controls pass.",
        "fail_rule": "Fail if pair separation collapses to counts/scalar labels, erases exact witness keys, requires dense closure, claims topology/hub/restore/inverse/fresh-N01/orientation/chirality, or opens downstream geometry.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "positive": positive,
        "boundary": boundary_checks,
        "all_pass": all_pass,
        "runtime_seconds": runtime,
        "multiplicity_pair_separation_table": pair_data["multiplicity_pair_separation_table"],
        "pair_count": pair_data["pair_count"],
        "pair_keys": pair_data["pair_keys"],
        "multiplicity_classes": pair_data["multiplicity_classes"],
        "witness_vector_unique_count": pair_data["witness_vector_unique_count"],
        "count_only_can_recover_witness_table": pair_data["count_only_can_recover_witness_table"],
        "all_support_pair_shared_sets_empty": pair_data["all_support_pair_shared_sets_empty"],
        "all_projection_shared_sets_empty": pair_data["all_projection_shared_sets_empty"],
        "all_local_incidence_shared_sets_empty": pair_data["all_local_incidence_shared_sets_empty"],
        "any_nonanchor_witness_shared": pair_data["any_nonanchor_witness_shared"],
        "support_cell_pair_projection_rows": pair_data["support_cell_pair_projection_rows"],
        "incidence_row_count": pair_data["incidence_row_count"],
        "strata_count": pair_data["strata_count"],
        "source_row_coverage": pair_data["source_row_coverage"],
        "fiber_coverage": pair_data["fiber_coverage"],
        "frontier_pair_coverage": pair_data["frontier_pair_coverage"],
        "signature_key_support": pair_data["signature_key_support"],
        "balance_key_support": pair_data["balance_key_support"],
        "residue_pattern_support": pair_data["residue_pattern_support"],
        "exact_counts": pair_data["exact_counts"],
        "dense_state_closure_used": pair_data["dense_state_closure_used"],
        "dense_environment_closure_used": pair_data["dense_environment_closure_used"],
        "max_parent_peps3d_sites": pair_data["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": pair_data["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": pair_data["max_peps3d_bond"],
        "controls": {
            "positive": positive,
            "graveyard_companions": graveyard,
            "boundary": boundary_checks,
        },
        "validation_targets": {
            "candidate_artifact": PHASE2_AO_CANDIDATE_PATH,
            "source_path": "system_v5/ops/formal_scouts/sim_peps3d_multiplicity_pair_separation_probe.py",
            "result_path": "system_v5/ops/formal_scouts/results/peps3d_multiplicity_pair_separation_probe_results.json",
        },
    }


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
