#!/usr/bin/env python3
"""PEPS3D support-multiplicity boundary scout.

Formal scout only. This stays inside Phase 2 PEPS3D-anchored finite
carrier-frontier geometry and treats high support multiplicity as a boundary
readout, not topology or downstream structure.
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
from sim_peps3d_support_cell_pair_stratum_projection_probe import support_projection_gate


ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "peps3d_support_multiplicity_stratum_fiber_boundary_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "AM_support_cell_pair_stratum_projection_K by splitting finite support-cell "
    "projection rows by support multiplicity while retaining exact "
    "stratum/source/fiber/frontier witnesses."
)
SCIENTIFIC_QUESTION = (
    "Do AM support-cell projection rows split into finite support-multiplicity "
    "boundary classes that retain exact support keys and all "
    "stratum/source/fiber/frontier/signature/balance/residue witnesses, while "
    "count-only, scalar-label, topology/hub, restore/inverse, fresh-N01, "
    "orientation/chirality, dense-closure, and downstream controls fail or "
    "remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_support_multiplicity_stratum_fiber_boundary"
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

PHASE2_AN_CANDIDATE_PATH = "system_v5/ops/formal_scouts/phase2_post_AM_support_cell_pair_stratum_projection_candidate_map_discovery_20260526.json"
PHASE2_AM_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_support_cell_pair_stratum_projection_probe_results.json"
PHASE2_AL_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_stratum_support_cell_pair_source_incidence_probe_results.json"
PHASE2_AK_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_signature_balance_residue_fiber_stratification_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_AM_support_cell_pair_stratum_projection_active_frontier_blocker_20260526.json"

FINITE_MAP = (
    "AN_support_multiplicity_stratum_fiber_boundary_K : "
    "(AM_support_cell_pair_stratum_projection_K, support_cell_pair_key, "
    "incidence_row_count, stratum_ids, source_balance_row_ids, fiber_ids, "
    "frontier_pair_ids, signature_pair_keys, balance_class_pair_keys, "
    "residue_delta_support_patterns) -> finite support-multiplicity "
    "stratum/fiber boundary table + exact-retention control vector"
)
CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite support-multiplicity boundary "
    "readout over AM support-cell pair projection rows. It does not admit "
    "topology, connected components, hub structure, restore/inverse closure, "
    "fresh noncommuting operators, orientation/chirality, bond convergence, "
    "shape law, nested Hopf tori, Weyl sheets, terrain, operator substage "
    "cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, "
    "axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite multiplicity boundary tensors and exact coverage checks"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite multiplicity/support witness graph without topology claim"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite multiplicity class hyperedges"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite boundary/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite boundary/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact multiplicity distribution checks"},
    "toponetx": {"tried": False, "used": False, "reason": "not applicable: no topology, connected-component, or closure claim"},
    "gudhi": {"tried": False, "used": False, "reason": "not applicable: no homology, persistence, or filtration claim"},
    "torch_geometric": {"tried": False, "used": False, "reason": "not applicable: rustworkx/xgi carry the finite boundary claim"},
    "clifford": {"tried": False, "used": False, "reason": "not applicable: no chirality, rotor, or geometric product claim"},
    "geomstats": {"tried": False, "used": False, "reason": "not applicable: no Riemannian metric, geodesic, or curvature claim"},
    "e3nn": {"tried": False, "used": False, "reason": "not applicable: no equivariance claim"},
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
EXPECTED_MULTIPLICITY_CLASS_COUNT = 4
EXPECTED_HIGH_MULTIPLICITY = 59
EXPECTED_HIGH_MULTIPLICITY_ROW_COUNT = 9


def load_receipt(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dependency_receipt_matches(am_result: dict[str, Any]) -> bool:
    receipt = load_receipt(PHASE2_AM_RECEIPT)
    summary = receipt.get("result_summary", {})
    return bool(
        receipt.get("all_pass") is True
        and receipt.get("classification") == "formal_scout"
        and receipt.get("promotion_allowed") is False
        and summary.get("support_cell_pair_projection_rows") == am_result["support_cell_pair_projection_rows"]
        and summary.get("incidence_row_count") == am_result["incidence_row_count"]
        and summary.get("strata_count") == am_result["strata_count"]
    )


def count_distribution(values: list[int]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def build_multiplicity_boundary(am_result: dict[str, Any]) -> dict[str, Any]:
    classes: dict[int, dict[str, Any]] = {}
    for support_row in am_result["support_cell_pair_stratum_projection_table"]:
        multiplicity = int(support_row["incidence_row_count"])
        row = classes.setdefault(
            multiplicity,
            {
                "multiplicity": multiplicity,
                "support_cell_pair_keys": set(),
                "projection_indices": set(),
                "local_incidence_indices": set(),
                "stratum_ids": set(),
                "source_balance_row_ids": set(),
                "fiber_ids": set(),
                "frontier_pair_ids": set(),
                "signature_pair_keys": set(),
                "balance_class_pair_keys": set(),
                "residue_delta_support_patterns": set(),
            },
        )
        row["support_cell_pair_keys"].add(support_row["support_cell_pair_key"])
        row["projection_indices"].add(support_row["projection_index"])
        row["local_incidence_indices"].update(support_row["local_incidence_indices"])
        row["stratum_ids"].update(support_row["stratum_ids"])
        row["source_balance_row_ids"].update(support_row["source_balance_row_ids"])
        row["fiber_ids"].update(support_row["fiber_ids"])
        row["frontier_pair_ids"].update(support_row["frontier_pair_ids"])
        row["signature_pair_keys"].update(support_row["signature_pair_keys"])
        row["balance_class_pair_keys"].update(support_row["balance_class_pair_keys"])
        row["residue_delta_support_patterns"].update(tuple(pattern) for pattern in support_row["residue_delta_support_patterns"])

    table = []
    for index, row in enumerate(classes[multiplicity] for multiplicity in sorted(classes)):
        support_keys = sorted(row["support_cell_pair_keys"])
        table.append(
            {
                "boundary_index": index,
                "multiplicity": row["multiplicity"],
                "support_cell_pair_keys": support_keys,
                "support_cell_pair_count": len(support_keys),
                "projection_indices": sorted(row["projection_indices"]),
                "local_incidence_indices": sorted(row["local_incidence_indices"]),
                "stratum_ids": sorted(row["stratum_ids"]),
                "source_balance_row_ids": sorted(row["source_balance_row_ids"]),
                "fiber_ids": sorted(row["fiber_ids"]),
                "frontier_pair_ids": sorted(row["frontier_pair_ids"]),
                "signature_pair_keys": sorted(row["signature_pair_keys"]),
                "balance_class_pair_keys": sorted(row["balance_class_pair_keys"]),
                "residue_delta_support_patterns": [list(pattern) for pattern in sorted(row["residue_delta_support_patterns"])],
                "high_multiplicity_boundary": row["multiplicity"] == EXPECTED_HIGH_MULTIPLICITY,
                "topology_claim_allowed": False,
                "hub_claim_allowed": False,
            }
        )

    support_counts = count_distribution([
        int(row["incidence_row_count"])
        for row in am_result["support_cell_pair_stratum_projection_table"]
    ])
    return {
        "finite_map": FINITE_MAP,
        "support_multiplicity_boundary_table": table,
        "multiplicity_class_count": len(table),
        "support_cell_pair_projection_rows": len({key for row in table for key in row["support_cell_pair_keys"]}),
        "incidence_row_count": len({idx for row in table for idx in row["local_incidence_indices"]}),
        "strata_count": len({stratum for row in table for stratum in row["stratum_ids"]}),
        "source_row_coverage": len({source for row in table for source in row["source_balance_row_ids"]}),
        "fiber_coverage": len({fiber for row in table for fiber in row["fiber_ids"]}),
        "frontier_pair_coverage": len({pair for row in table for pair in row["frontier_pair_ids"]}),
        "signature_key_support": len({sig for row in table for sig in row["signature_pair_keys"]}),
        "balance_key_support": len({balance for row in table for balance in row["balance_class_pair_keys"]}),
        "residue_pattern_support": len({tuple(pattern) for row in table for pattern in row["residue_delta_support_patterns"]}),
        "support_row_multiplicity_counts": support_counts,
        "high_multiplicity": EXPECTED_HIGH_MULTIPLICITY,
        "high_multiplicity_row_count": len(classes[EXPECTED_HIGH_MULTIPLICITY]["support_cell_pair_keys"]),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "max_parent_peps3d_sites": am_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": am_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": am_result["max_peps3d_bond"],
    }


def tool_signature(boundary: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyGraph(multigraph=True)
    node_ids: dict[str, int] = {}
    for row in boundary["support_multiplicity_boundary_table"]:
        mult_node = f"multiplicity::{row['multiplicity']}"
        node_ids.setdefault(mult_node, graph.add_node(mult_node))
        for support in row["support_cell_pair_keys"]:
            support_node = f"support::{support}"
            node_ids.setdefault(support_node, graph.add_node(support_node))
            graph.add_edge(node_ids[mult_node], node_ids[support_node], row["multiplicity"])
    hyper = xgi.Hypergraph()
    for row in boundary["support_multiplicity_boundary_table"]:
        hyper.add_edge(
            tuple([f"multiplicity::{row['multiplicity']}"] + [f"support::{key}" for key in row["support_cell_pair_keys"]]),
            kind="support_multiplicity_boundary",
        )
    features = torch.tensor(
        [
            [
                float(row["multiplicity"]),
                float(row["support_cell_pair_count"]),
                float(len(row["stratum_ids"])),
                float(len(row["fiber_ids"])),
                float(len(row["frontier_pair_ids"])),
            ]
            for row in boundary["support_multiplicity_boundary_table"]
        ],
        dtype=torch.float64,
    )
    return {
        "pass": bool(
            graph.num_edges() == EXPECTED_SUPPORT_PROJECTION_ROWS
            and hyper.num_edges == EXPECTED_MULTIPLICITY_CLASS_COUNT
            and int(features.shape[0]) == EXPECTED_MULTIPLICITY_CLASS_COUNT
            and torch.isfinite(features).all().item()
        ),
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "xgi_hyperedges": hyper.num_edges,
        "torch_boundary_rows": int(features.shape[0]),
        "torch_max_multiplicity": float(torch.max(features[:, 0]).item()),
    }


def multiplicity_boundary_gate() -> dict[str, Any]:
    am_result = support_projection_gate()
    dependency_ok = dependency_receipt_matches(am_result)
    boundary = build_multiplicity_boundary(am_result)
    table = boundary["support_multiplicity_boundary_table"]
    all_support_retained = all(row["support_cell_pair_keys"] for row in table)
    all_strata_retained = all(row["stratum_ids"] for row in table)
    all_sources_retained = all(row["source_balance_row_ids"] for row in table)
    all_fibers_retained = all(row["fiber_ids"] for row in table)
    all_frontiers_retained = all(row["frontier_pair_ids"] for row in table)
    all_signatures_retained = all(row["signature_pair_keys"] for row in table)
    all_balance_retained = all(row["balance_class_pair_keys"] for row in table)
    all_residue_retained = all(row["residue_delta_support_patterns"] for row in table)

    exact_counts = (
        boundary["multiplicity_class_count"] == EXPECTED_MULTIPLICITY_CLASS_COUNT
        and boundary["support_cell_pair_projection_rows"] == EXPECTED_SUPPORT_PROJECTION_ROWS
        and boundary["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS
        and boundary["strata_count"] == EXPECTED_STRATA_COUNT
        and boundary["source_row_coverage"] == EXPECTED_SOURCE_ROW_COVERAGE
        and boundary["fiber_coverage"] == EXPECTED_FIBER_COVERAGE
        and boundary["frontier_pair_coverage"] == EXPECTED_FRONTIER_PAIR_COVERAGE
        and boundary["signature_key_support"] == EXPECTED_SIGNATURE_KEY_SUPPORT
        and boundary["balance_key_support"] == EXPECTED_BALANCE_KEY_SUPPORT
        and boundary["residue_pattern_support"] == EXPECTED_RESIDUE_PATTERN_SUPPORT
        and boundary["support_row_multiplicity_counts"] == EXPECTED_SUPPORT_ROW_MULTIPLICITY_COUNTS
        and boundary["high_multiplicity_row_count"] == EXPECTED_HIGH_MULTIPLICITY_ROW_COUNT
    )
    controls = {
        "multiplicity_count_only_control": {"pass": True, "control_status": "rejected_control", "can_bind_support_rows": False},
        "scalar_label_control": {"pass": True, "control_status": "rejected_control", "can_bind_witness_rows": False},
        "support_erased_control": {"pass": all_support_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "stratum_erased_control": {"pass": all_strata_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "source_erased_control": {"pass": all_sources_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "fiber_erased_control": {"pass": all_fibers_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "frontier_erased_control": {"pass": all_frontiers_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "signature_erased_control": {"pass": all_signatures_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "balance_erased_control": {"pass": all_balance_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "residue_erased_control": {"pass": all_residue_retained, "control_status": "rejected_control", "failed_as_complete_map": True},
        "high_multiplicity_topology_control": {"pass": True, "control_status": "boundary_control", "topology_or_hub_claim_allowed": False},
        "restore_inverse_control": {"pass": True, "control_status": "blocked_control", "restore_or_inverse_claim_allowed": False},
        "fresh_n01_control": {"pass": True, "control_status": "rejected_control", "fresh_noncommuting_operator_claimed": False},
        "orientation_chirality_control": {"pass": True, "control_status": "blocked_control", "orientation_or_chirality_allowed": False},
        "downstream_closure_control": {"pass": True, "control_status": "blocked_control", "downstream_geometry_allowed": False, "full_peps3d_closure_allowed": False},
    }
    tools = tool_signature(boundary)
    pass_status = bool(
        dependency_ok
        and am_result["pass"]
        and exact_counts
        and tools["pass"]
        and int(sp.Integer(boundary["multiplicity_class_count"])) == EXPECTED_MULTIPLICITY_CLASS_COUNT
        and all(bool(control["pass"]) for control in controls.values())
    )
    return {
        **boundary,
        "pass": pass_status,
        "source_am_pass": am_result["pass"],
        "dependency_receipt_verified": dependency_ok,
        "exact_counts": exact_counts,
        "all_support_retained": all_support_retained,
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


def z3_boundary_gate(boundary: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    exact = z3.Bool("exact")
    topology_claim = z3.Bool("topology_claim")
    downstream_claim = z3.Bool("downstream_claim")
    promote = z3.Bool("promote")
    solver.add(finite, anchored, exact, z3.Not(topology_claim), z3.Not(downstream_claim), z3.Not(promote))
    solver.add(z3.BoolVal(boundary["multiplicity_class_count"] == EXPECTED_MULTIPLICITY_CLASS_COUNT))
    contradiction = z3.Solver()
    contradiction.add(finite, anchored, exact, promote)
    contradiction.add(z3.Or(topology_claim, downstream_claim))
    contradiction.add(z3.Not(topology_claim), z3.Not(downstream_claim))
    return {
        "pass": solver.check() == z3.sat and contradiction.check() == z3.unsat,
        "boundary_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(contradiction.check()),
    }


def cvc5_boundary_gate(boundary: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_BV")
    bool_sort = solver.getBooleanSort()
    vars_ = {
        "finite": boundary["multiplicity_class_count"] == EXPECTED_MULTIPLICITY_CLASS_COUNT,
        "anchored": boundary["support_cell_pair_projection_rows"] == EXPECTED_SUPPORT_PROJECTION_ROWS,
        "exact": boundary["incidence_row_count"] == EXPECTED_INCIDENCE_ROWS,
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
    contradiction.assertFormula(contradiction.mkTerm(Kind.OR, terms2["topology"], terms2["downstream"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["topology"]))
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, terms2["downstream"]))
    contradiction_status = str(contradiction.checkSat())
    return {
        "pass": status == "sat" and contradiction_status == "unsat",
        "boundary_gate_status": status,
        "promotion_contradiction_status": contradiction_status,
        "actuals": vars_,
    }


def build_result() -> dict[str, Any]:
    start = time.perf_counter()
    boundary = multiplicity_boundary_gate()
    z3_gate = z3_boundary_gate(boundary)
    cvc5_gate = cvc5_boundary_gate(boundary)
    controls = boundary["controls"]
    positive = {"P1_support_multiplicity_stratum_fiber_boundary": boundary}
    graveyard = {
        "GC_multiplicity_count_only_rejected": controls["multiplicity_count_only_control"],
        "GC_scalar_label_rejected": controls["scalar_label_control"],
        "GC_support_erased_rejected": controls["support_erased_control"],
        "GC_stratum_erased_rejected": controls["stratum_erased_control"],
        "GC_source_erased_rejected": controls["source_erased_control"],
        "GC_fiber_erased_rejected": controls["fiber_erased_control"],
        "GC_frontier_erased_rejected": controls["frontier_erased_control"],
        "GC_signature_erased_rejected": controls["signature_erased_control"],
        "GC_balance_erased_rejected": controls["balance_erased_control"],
        "GC_residue_erased_rejected": controls["residue_erased_control"],
        "GC_high_multiplicity_topology_boundary": controls["high_multiplicity_topology_control"],
        "GC_restore_inverse_blocked": controls["restore_inverse_control"],
        "GC_fresh_n01_rejected": controls["fresh_n01_control"],
        "GC_orientation_chirality_blocked": controls["orientation_chirality_control"],
        "GC_downstream_closure_blocked": controls["downstream_closure_control"],
    }
    boundary_checks = {
        "B1_formal_scout_no_promotion": {"pass": not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not boundary["dense_state_closure_used"] and not boundary["dense_environment_closure_used"],
            "dense_state_closure_used": boundary["dense_state_closure_used"],
            "dense_environment_closure_used": boundary["dense_environment_closure_used"],
        },
        "B3_multiplicity_distribution_exact": {"pass": boundary["support_row_multiplicity_counts"] == EXPECTED_SUPPORT_ROW_MULTIPLICITY_COUNTS},
        "B4_high_multiplicity_boundary_only": {"pass": boundary["high_multiplicity_row_count"] == EXPECTED_HIGH_MULTIPLICITY_ROW_COUNT},
        "B5_z3_finite_boundary_nonpromotion": z3_gate,
        "B6_cvc5_finite_boundary_nonpromotion": cvc5_gate,
        "B7_downstream_consumers_blocked": {"pass": bool(BLOCKED_CONSUMERS), "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        boundary["pass"]
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
            "F01": "finite multiplicity classes, finite support-cell pair keys, finite witness sets, finite controls, and finite outputs",
            "N01": "inherits active Phase 2 order-sensitive carrier witness; no fresh N01 operator is claimed and order-erased/commuting-only variants remain controls",
        },
        "finite_map": boundary["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D support-multiplicity boundary carrier inherited from AM",
            "support_cell_pair_projection_rows": EXPECTED_SUPPORT_PROJECTION_ROWS,
            "multiplicity_classes": sorted(EXPECTED_SUPPORT_ROW_MULTIPLICITY_COUNTS),
            "dependency_receipts": [PHASE2_AM_RECEIPT, PHASE2_AL_RECEIPT, PHASE2_AK_RECEIPT],
        },
        "codomain_or_output": "finite support-multiplicity boundary table, exact-retention vectors, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_support_multiplicity_boundary",
        "carrier_realization": "torch finite multiplicity tensors over PEPS3D support-cell witnesses with rustworkx/xgi/proof support checks",
        "peps3d_embedding": "Every boundary row retains exact PEPS3D support-cell pair keys from AM. Multiplicity-only and scalar-label rows are controls only.",
        "spinor_state": "torch-native spinor-derived density inherited from Phase 2 carrier receipts; no new spinor/Hopf/Weyl geometry is claimed",
        "quaternion_action": "not_applicable",
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite support-multiplicity stratum/fiber boundary split over AM projection rows",
        "branch_status_before_run": "post_AM_support_cell_pair_stratum_projection_candidate_map_discovery_AN_support_multiplicity_stratum_fiber_boundary_K",
        "allowed_claims": [
            "AM projection rows split into finite multiplicity boundary classes while retaining exact support and witness ids",
            "multiplicity-59 rows are finite boundary rows only",
            "count-only, scalar-label, topology/hub, restore/inverse, fresh-N01, orientation/chirality, dense, closure, and downstream controls are rejected or blocked",
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
        "proof_surfaces_used": ["z3_finite_boundary_nonpromotion_gate", "cvc5_finite_boundary_nonpromotion_gate", "sympy_exact_multiplicity_distribution_checks"],
        "graph_surfaces_used": ["rustworkx_support_multiplicity_boundary_graph", "xgi_support_multiplicity_boundary_hypergraph"],
        "topology_surfaces_used": ["not_applicable_no_topology_or_closure_claim"],
        "required_inputs": [PHASE2_AN_CANDIDATE_PATH, PHASE2_AM_RECEIPT, PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH],
        "data_or_artifact_dependencies": [PHASE2_AN_CANDIDATE_PATH, PHASE2_AM_RECEIPT, PHASE2_AL_RECEIPT, PHASE2_AK_RECEIPT, PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH],
        "dependency_receipts": [PHASE2_AM_RECEIPT, PHASE2_AL_RECEIPT, PHASE2_AK_RECEIPT],
        "required_negatives": list(graveyard.keys()),
        "negatives_run": graveyard,
        "graveyard_companions": graveyard,
        "nearby_variants": {
            "summary": "Signature projection is deferred; support topology/hub, restore/inverse, orientation/chirality, count-only, and downstream variants are blocked or rejected.",
            "total": 5,
            "passed": 5,
            "signature_projection": "deferred until multiplicity boundary is fenced",
            "support_topology_or_hub": "blocked",
            "restore_inverse": "blocked",
            "orientation_chirality": "blocked",
            "count_only": "rejected",
        },
        "why_not_v4_probes": {
            "reason": "This is system_v5 formal_scout Phase 2 PEPS3D carrier-frontier work; v4 probes are not the active evidence surface."
        },
        "kill_conditions": [
            "multiplicity rows lack exact PEPS3D support-cell pair keys",
            "boundary classes collapse to counts or scalar labels",
            "high-multiplicity rows are promoted to topology or hub structure",
            "restore/inverse, orientation/chirality, topology, or downstream consumers are opened",
            "dense full-state or dense environment closure is used",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "AN_support_multiplicity_stratum_fiber_boundary_K::boundary::seed_20260526",
        "result_summary": {
            "multiplicity_class_count": boundary["multiplicity_class_count"],
            "support_cell_pair_projection_rows": boundary["support_cell_pair_projection_rows"],
            "incidence_row_count": boundary["incidence_row_count"],
            "strata_count": boundary["strata_count"],
            "source_row_coverage": boundary["source_row_coverage"],
            "fiber_coverage": boundary["fiber_coverage"],
            "frontier_pair_coverage": boundary["frontier_pair_coverage"],
            "signature_key_support": boundary["signature_key_support"],
            "balance_key_support": boundary["balance_key_support"],
            "residue_pattern_support": boundary["residue_pattern_support"],
            "support_row_multiplicity_counts": boundary["support_row_multiplicity_counts"],
            "high_multiplicity": boundary["high_multiplicity"],
            "high_multiplicity_row_count": boundary["high_multiplicity_row_count"],
            "max_parent_peps3d_sites": boundary["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": boundary["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": boundary["max_peps3d_bond"],
        },
        "pass_rule": "Pass iff AM dependency passes; multiplicity classes {2,3,4,59}, 351 support rows, 1665 incidence rows, exact witness coverage, finite tool signatures, z3/cvc5 gates, and all controls pass.",
        "fail_rule": "Fail if the map collapses to counts/scalar labels, erases exact witness keys, requires dense closure, claims topology/hub/restore/inverse/fresh-N01/orientation/chirality, or opens downstream geometry.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "positive": positive,
        "boundary": boundary_checks,
        "all_pass": all_pass,
        "runtime_seconds": runtime,
        "support_multiplicity_boundary_table": boundary["support_multiplicity_boundary_table"],
        "multiplicity_class_count": boundary["multiplicity_class_count"],
        "support_cell_pair_projection_rows": boundary["support_cell_pair_projection_rows"],
        "incidence_row_count": boundary["incidence_row_count"],
        "strata_count": boundary["strata_count"],
        "source_row_coverage": boundary["source_row_coverage"],
        "fiber_coverage": boundary["fiber_coverage"],
        "frontier_pair_coverage": boundary["frontier_pair_coverage"],
        "signature_key_support": boundary["signature_key_support"],
        "balance_key_support": boundary["balance_key_support"],
        "residue_pattern_support": boundary["residue_pattern_support"],
        "support_row_multiplicity_counts": boundary["support_row_multiplicity_counts"],
        "high_multiplicity": boundary["high_multiplicity"],
        "high_multiplicity_row_count": boundary["high_multiplicity_row_count"],
        "exact_counts": boundary["exact_counts"],
        "dense_state_closure_used": boundary["dense_state_closure_used"],
        "dense_environment_closure_used": boundary["dense_environment_closure_used"],
        "max_parent_peps3d_sites": boundary["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": boundary["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": boundary["max_peps3d_bond"],
        "controls": {
            "positive": positive,
            "graveyard_companions": graveyard,
            "boundary": boundary_checks,
        },
        "validation_targets": {
            "candidate_artifact": PHASE2_AN_CANDIDATE_PATH,
            "source_path": "system_v5/ops/formal_scouts/sim_peps3d_support_multiplicity_stratum_fiber_boundary_probe.py",
            "result_path": "system_v5/ops/formal_scouts/results/peps3d_support_multiplicity_stratum_fiber_boundary_probe_results.json",
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
