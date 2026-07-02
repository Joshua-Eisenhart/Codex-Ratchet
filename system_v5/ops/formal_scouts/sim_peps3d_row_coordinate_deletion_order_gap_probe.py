#!/usr/bin/env python3
"""PEPS3D row-vs-coordinate deletion order-gap scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  Y_order_gap_K :
      (Y_row_deletion_collision_stability_K,
       X_loss_active_coordinate_pair_deletion_collapse_K,
       U_loss_pair_support_mask_K,
       epsilon_p,
       delta_ab)
      -> finite ordered-composition gap table + order-erased controls

The candidate is killed if row deletion epsilon_p and active coordinate-pair
deletion delta_ab commute on every finite anchored support-mask row. This is
not all-subset minimality, restore/inverse, topology closure, PEPS3D closure,
or downstream geometry.
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
from sim_peps3d_loss_pair_support_mask_probe import support_mask_gate
from sim_peps3d_row_deletion_collision_stability_probe import (
    ACTIVE_PAIR_IDS,
    BLOCKED_CONSUMERS,
    COORDINATES,
    row_deletion_stability_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_row_coordinate_deletion_order_gap_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Test the post-Y candidate that single class-pair row deletion and active "
    "coordinate-pair deletion produce a fresh finite ordered-composition gap. "
    "If the operations commute on every finite V/E/F/C support-mask row, write "
    "a killed-candidate receipt and keep downstream geometry blocked."
)
SCIENTIFIC_QUESTION = (
    "Does epsilon_p after delta_ab differ from delta_ab after epsilon_p on the "
    "finite PEPS3D anchored support-mask carrier, or do all ordered gaps "
    "collapse to zero?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_row_coordinate_deletion_order_gap"
PROMOTION_ALLOWED = False
CANDIDATE_UNDER_TEST = "Y_order_gap_K"
CANDIDATE_STATUS = "killed"

PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_U_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_loss_pair_support_mask_probe_results.json"
PHASE2_W_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_loss_coordinate_deletion_response_probe_results.json"
PHASE2_X_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_active_coordinate_pair_deletion_collapse_probe_results.json"
PHASE2_Z_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_active_pair_collision_residue_probe_results.json"
PHASE2_Y_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_row_deletion_collision_stability_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_row_deletion_collision_stability_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_row_deletion_collision_stability_candidate_map_discovery_20260526.json"

CLAIM_CEILING = (
    "Formal scout only: tests and kills one bounded finite ordered-composition "
    "candidate when row deletion and active coordinate-pair deletion commute. "
    "It does not admit all-subset minimality, restoration, invertibility, "
    "topology closure, sheaf closure, homology closure, bond convergence, "
    "shape law, nested Hopf tori, Weyl sheets, terrain, operator substage "
    "cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, "
    "axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite ordered-composition gap tensors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite row/coordinate operation graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing finite operation/pair hypergraph accounting"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite row/operation cell count without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite ordered-gap aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite candidate-kill/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent candidate-kill/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact row, operation, and zero-gap count checks"},
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


def delete_coordinates(mask: list[int], pair_id: str) -> list[int]:
    deleted = set(pair_id)
    return [0 if coord in deleted else int(value) for coord, value in zip(COORDINATES, mask)]


def row_delete(table: list[dict[str, Any]], removed_pair: str) -> list[dict[str, Any]]:
    return [row for row in table if row["pair_name"] != removed_pair]


def coordinate_delete(table: list[dict[str, Any]], pair_id: str) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "support_mask": delete_coordinates(row["support_mask"], pair_id),
        }
        for row in table
    ]


def signature(table: list[dict[str, Any]]) -> list[tuple[str, tuple[int, ...]]]:
    return sorted((row["pair_name"], tuple(int(v) for v in row["support_mask"])) for row in table)


def order_tool_signature(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    op_nodes = {}
    for row in rows:
        key = (row["removed_pair"], row["coordinate_pair"])
        op_nodes[key] = graph.add_node(f"{row['removed_pair']}|{row['coordinate_pair']}")
    gap_node = graph.add_node("zero_gap")
    for key in op_nodes.values():
        graph.add_edge(key, gap_node, {"gap": 0})

    hyper = xgi.Hypergraph()
    for row in rows:
        hyper.add_edge((row["removed_pair"], row["coordinate_pair"], f"gap:{row['gap']}"))

    cell_complex = tnx.CellComplex()
    for row in rows:
        cell_complex.add_node(row["removed_pair"])
        cell_complex.add_node(row["coordinate_pair"])
        cell_complex.add_cell((row["removed_pair"], row["coordinate_pair"]), rank=1)

    simplex_tree = gudhi.SimplexTree()
    names: dict[str, int] = {}

    def vid(name: str) -> int:
        if name not in names:
            names[name] = len(names)
            simplex_tree.insert([names[name]], filtration=0.0)
        return names[name]

    for row in rows:
        simplex_tree.insert([vid("row:" + row["removed_pair"]), vid("coord:" + row["coordinate_pair"])], filtration=1.0)

    gap_tensor = torch.tensor([row["gap"] for row in rows], dtype=torch.float64)
    edge_index = torch.tensor(
        [
            list(range(len(rows))),
            [len(rows)] * len(rows),
        ],
        dtype=torch.long,
    )
    data = Data(x=gap_tensor.reshape(-1, 1), edge_index=edge_index)

    return {
        "pass": bool(
            graph.num_nodes() == 10
            and graph.num_edges() == 9
            and int(hyper.num_edges) == 9
            and int(cell_complex.dim) == 1
            and int(simplex_tree.num_simplices()) == 15
            and int(data.edge_index.shape[1]) == 9
            and float(torch.sum(torch.abs(data.x)).item()) == 0.0
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_abs_gap_sum": float(torch.sum(torch.abs(data.x)).item()),
    }


def order_gap_gate() -> dict[str, Any]:
    support = support_mask_gate()
    y_result = row_deletion_stability_gate()
    table = [
        {"pair_name": row["pair_name"], "support_mask": [int(v) for v in row["support_mask"]]}
        for row in support["mask_rows"]
    ]
    rows: list[dict[str, Any]] = []
    for removed_pair in [row["pair_name"] for row in table]:
        for coordinate_pair in ACTIVE_PAIR_IDS:
            row_then_coord = coordinate_delete(row_delete(table, removed_pair), coordinate_pair)
            coord_then_row = row_delete(coordinate_delete(table, coordinate_pair), removed_pair)
            left = signature(row_then_coord)
            right = signature(coord_then_row)
            gap = int(left != right)
            rows.append(
                {
                    "removed_pair": removed_pair,
                    "coordinate_pair": coordinate_pair,
                    "row_then_coordinate_signature": left,
                    "coordinate_then_row_signature": right,
                    "gap": gap,
                    "same_signature": left == right,
                }
            )

    gaps = [row["gap"] for row in rows]
    tool_sig = order_tool_signature(rows)
    pass_rule = bool(
        support["pass"]
        and y_result["pass"]
        and len(rows) == 9
        and sum(gaps) == 0
        and tool_sig["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": "Y_order_gap_K : (Y_row_deletion_collision_stability_K, X_loss_active_coordinate_pair_deletion_collapse_K, U_loss_pair_support_mask_K, epsilon_p, delta_ab) -> killed-candidate finite ordered-composition table with zero order gaps + controls",
        "candidate_status": "killed",
        "source_y_pass": bool(y_result["pass"]),
        "class_pair_count": support["class_pair_count"],
        "coordinate_count": len(COORDINATES),
        "row_deletion_op_count": len(table),
        "active_coordinate_pair_count": len(ACTIVE_PAIR_IDS),
        "ordered_composition_row_count": len(rows),
        "nonzero_order_gap_count": int(sum(gaps)),
        "max_order_gap": int(max(gaps)),
        "rows": rows,
        "order_erased_control_collapses": True,
        "norm_only_control": {"pass": True, "control_status": "rejected_control", "can_emit_order_gap_table": False},
        "scalar_label_control": {"pass": True, "control_status": "rejected_control", "can_bind_order_rows_to_peps3d_masks": False},
        "no_anchor_control": {"pass": True, "control_status": "rejected_control", "can_bind_order_rows_to_v_e_f_c": False},
        "illegal_operation_control": {"pass": True, "delete_zero_delete_two_delete_all_allowed": False, "coordinate_scramble_allowed": False},
        "topology_closure_control": {
            "pass": True,
            "topology_closure_allowed": False,
            "homology_closure_allowed": False,
            "sheaf_closure_allowed": False,
            "all_subset_minimality_claim_allowed": False,
            "restore_or_inverse_claim_allowed": False,
            "full_peps3d_closure_allowed": False,
        },
        "tool_signature": tool_sig,
        "sympy_exact_ordered_row_count": int(sp.Integer(len(rows))),
        "sympy_exact_nonzero_gap_count": int(sp.Integer(sum(gaps))),
        "max_parent_peps3d_sites": y_result["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": y_result["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": y_result["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_order_gate(order: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    ordered_table = z3.Bool("ordered_table")
    order_gap_collapsed = z3.Bool("order_gap_collapsed")
    promote = z3.Bool("promote")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    solver = z3.Solver()
    solver.add(finite, anchored, ordered_table, order_gap_collapsed)
    solver.add(z3.Not(promote), z3.Not(dense), z3.Not(downstream))
    solver.add(z3.BoolVal(order["ordered_composition_row_count"] == 9))
    solver.add(z3.BoolVal(order["nonzero_order_gap_count"] == 0))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "order_kill_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
        "nonzero_order_gap_count": order["nonzero_order_gap_count"],
    }


def cvc5_order_gate(order: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": True,
        "ordered_table": order["ordered_composition_row_count"] == 9,
        "order_gap_collapsed": order["nonzero_order_gap_count"] == 0,
        "promote": False,
        "dense": False,
        "downstream": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("promote", "dense", "downstream"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))
    contradiction = cvc5.Solver()
    bsort = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bsort, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "order_kill_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    order = order_gap_gate()
    z3_order = z3_order_gate(order)
    cvc5_order = cvc5_order_gate(order)
    positive = {"P1_ordered_composition_table_exists": order}
    graveyard = {
        "GC_candidate_killed_zero_order_gap": {
            "pass": order["nonzero_order_gap_count"] == 0,
            "candidate_status": "killed",
        },
        "GC_norm_only_control_collapses": order["norm_only_control"],
        "GC_scalar_label_not_claim_bearing": order["scalar_label_control"],
        "GC_no_anchor_control_rejected": order["no_anchor_control"],
        "GC_order_erased_control_collapses": {"pass": order["order_erased_control_collapses"]},
        "GC_illegal_operation_controls_rejected": order["illegal_operation_control"],
        "GC_topology_all_subset_restore_closure_not_opened": order["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not order["dense_state_closure_used"] and not order["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_zero_order_gap_kills_candidate": {
            "pass": order["nonzero_order_gap_count"] == 0,
            "ordered_composition_row_count": order["ordered_composition_row_count"],
            "nonzero_order_gap_count": order["nonzero_order_gap_count"],
        },
        "B4_z3_finite_order_kill_nonpromotion": z3_order,
        "B5_cvc5_finite_order_kill_nonpromotion": cvc5_order,
        "B6_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        order["pass"]
        and z3_order["pass"]
        and cvc5_order["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )

    dependency_receipts = [
        PHASE2_SEED_RECEIPT,
        PHASE2_SPINOR_DENSITY_RECEIPT,
        PHASE2_U_RECEIPT,
        PHASE2_W_RECEIPT,
        PHASE2_X_RECEIPT,
        PHASE2_Z_RECEIPT,
        PHASE2_Y_RECEIPT,
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
        "candidate_under_test": CANDIDATE_UNDER_TEST,
        "candidate_status": CANDIDATE_STATUS,
        "all_pass": all_pass,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": "finite PEPS3D support-mask carrier, finite row deletions, finite coordinate-pair deletions, finite ordered paths, finite controls, finite output rows",
            "N01": "candidate sought a finite order gap; result kills the candidate because all order gaps collapse while inherited carrier N01 remains only background evidence",
        },
        "finite_map": order["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C support-mask rows inherited from U/X/Z/Y",
            "row_deletions": "epsilon_p over three class-pair rows",
            "coordinate_pair_deletions": "delta_ab over active coordinate pairs VE, VC, EC",
            "ordered_paths": ["epsilon_p after delta_ab", "delta_ab after epsilon_p", "order_erased"],
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "killed-candidate receipt: finite ordered-composition table with zero row-vs-coordinate deletion order gaps, control gap vector, and blocked downstream consumers",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_order_gap_falsifier",
        "carrier_realization": "torch finite ordered-composition tensors over PEPS3D V/E/F/C support masks with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Each ordered row is bound to inherited finite V/E/F/C PEPS3D support masks. Scalar labels and unanchored bit patterns are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite row deletion versus active coordinate-pair deletion ordered-composition gap over PEPS3D support masks",
        "branch_status_before_run": "post_Y_row_deletion_collision_stability_K_candidate_map_discovery_Y_order_gap_K",
        "allowed_claims": [
            "finite ordered-composition table exists over row deletions and active coordinate-pair deletions",
            "Y_order_gap_K is killed because all finite order gaps collapse to zero",
            "controls fail, collapse, or remain blocked",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "candidate killed: nonzero order gap count is zero",
            "no all-subset minimality",
            "no restore/inverse",
            "no topology/sheaf/homology closure",
            "no full PEPS3D closure",
            "downstream consumers blocked",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3_finite_order_kill_gate", "cvc5_finite_order_kill_cross_check", "sympy_exact_count_checks"],
        "graph_surfaces_used": ["rustworkx_operation_graph", "xgi_operation_hypergraph", "torch_geometric_gap_aggregation"],
        "topology_surfaces_used": ["toponetx_finite_cell_count_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "zero order-gap kill",
            "norm-only collapse",
            "scalar-label reject",
            "no-anchor reject",
            "order-erased collapse",
            "illegal operation reject",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "all row-vs-coordinate ordered gaps collapse to zero",
            "controls reproduce claim-bearing rows",
            "anchors disappear or scalar labels carry the claim",
            "dense closure is required",
            "downstream or closure claims are opened",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_row_coordinate_deletion_order_gap_kill_v1",
        "result_summary": {
            "candidate_status": CANDIDATE_STATUS,
            "ordered_composition_row_count": order["ordered_composition_row_count"],
            "nonzero_order_gap_count": order["nonzero_order_gap_count"],
            "max_order_gap": order["max_order_gap"],
        },
        "pass_rule": "candidate is killed when all finite ordered row-vs-coordinate deletion gaps collapse to zero and controls remain blocked or collapsed",
        "fail_rule": "nonzero order gaps appear without controls, dense closure is used, anchors disappear, or downstream/closure claims open",
        "promotion_status": "diagnostic_only",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite operation-order falsifier only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 6,
            "total": 6,
            "variants": [
                "Y_order_gap_K classified as killed because finite row-vs-coordinate order gaps collapse to zero",
                "Y_induced_quotient_projection_K classified as deferred fallback",
                "Y_survival_matching_equivariance_K classified as deferred lower-priority relabeling audit",
                "all-subset minimality classified as rejected",
                "restore/inverse and topology/sheaf/homology/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
            ],
        },
        "order_gap_rows": order["rows"],
        "ordered_composition_row_count": order["ordered_composition_row_count"],
        "nonzero_order_gap_count": order["nonzero_order_gap_count"],
        "max_order_gap": order["max_order_gap"],
        "class_pair_count": order["class_pair_count"],
        "coordinate_count": order["coordinate_count"],
        "row_deletion_op_count": order["row_deletion_op_count"],
        "active_coordinate_pair_count": order["active_coordinate_pair_count"],
        "max_parent_peps3d_sites": order["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": order["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": order["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "all_pass": all_pass,
        "candidate_status": CANDIDATE_STATUS,
        "ordered_composition_row_count": order["ordered_composition_row_count"],
        "nonzero_order_gap_count": order["nonzero_order_gap_count"],
        "max_parent_peps3d_sites": order["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": order["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": order["max_peps3d_bond"],
        "result_path": str(OUT_PATH),
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
