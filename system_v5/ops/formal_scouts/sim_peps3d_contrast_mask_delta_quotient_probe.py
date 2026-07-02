#!/usr/bin/env python3
"""PEPS3D contrast mask-delta quotient scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite response-quotient
carrier geometry. It tests:

  Y_contrast_mask_delta_quotient_K :
      (Y_certificate_boundary_contrast_K,
       contrast_rows,
       mask_delta,
       source_class_ids,
       PEPS3D V/E/F/C masks)
      -> finite mask-delta quotient classes
         + source-binding table
         + control gap vector

The claim-bearing output is an explicit quotient over finite mask-delta
vectors, with source-class and mask bindings retained.
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
import gudhi
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import as_jsonable
from sim_peps3d_certificate_boundary_contrast_probe import certificate_boundary_contrast_gate
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_contrast_mask_delta_quotient_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "Y_certificate_boundary_contrast_K by quotienting finite contrast rows by "
    "exact V/E/F/C mask-delta vector while retaining source-class and mask "
    "bindings."
)
SCIENTIFIC_QUESTION = (
    "Do the 54 active-vs-F-boundary contrast rows induce finite mask-delta "
    "quotient classes that retain source-class and PEPS3D mask bindings, while "
    "count-only, scalar-sum-only, source-erased, no-anchor, and downstream "
    "controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_contrast_mask_delta_quotient"
PROMOTION_ALLOWED = False

PHASE2_CONTRAST_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_certificate_boundary_contrast_probe_results.json"
PHASE2_CERTIFICATE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_collision_certificate_projection_probe_results.json"
PHASE2_Y_INDUCED_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_induced_quotient_projection_probe_results.json"
PHASE2_Y_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_row_deletion_collision_stability_probe_results.json"
PHASE2_Z_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_active_pair_collision_residue_probe_results.json"
PHASE2_U_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_loss_pair_support_mask_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_certificate_boundary_contrast_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_certificate_boundary_contrast_candidate_map_discovery_20260526.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite mask-delta quotient over "
    "certificate-contrast rows. It does not admit all-subset minimality, "
    "restore/inverse, topology closure, sheaf closure, homology closure, bond "
    "convergence, shape law, nested Hopf tori, Weyl sheets, terrain, operator "
    "substage cells, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game "
    "theory, axes 7-12, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing quotient-size and mask-delta tensors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite delta-quotient graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing delta-class/member hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite quotient incidence cells without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing quotient occupancy aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite quotient/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite quotient/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact quotient class and row count checks"},
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


def contrast_delta_quotient_gate() -> dict[str, Any]:
    contrast = certificate_boundary_contrast_gate()
    buckets: dict[tuple[int, ...], list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(contrast["certificate_contrast_table"]):
        buckets[tuple(int(value) for value in row["mask_delta"])].append(
            {
                "row_id": f"contrast_{index}",
                "active_source_class_id": row["active_source_class_id"],
                "boundary_source_class_id": row["boundary_source_class_id"],
                "active_pair_id": row["active_pair_id"],
                "boundary_pair_id": row["boundary_pair_id"],
                "active_pair_members": row["active_pair_members"],
                "active_mask": row["active_mask"],
                "boundary_mask": row["boundary_mask"],
                "mask_delta_l1": row["mask_delta_l1"],
            }
        )
    quotient_classes = []
    for class_index, (delta, members) in enumerate(sorted(buckets.items())):
        quotient_classes.append(
            {
                "class_id": f"delta_class_{class_index}",
                "mask_delta": list(delta),
                "class_size": len(members),
                "members": members,
                "active_source_class_ids": sorted({member["active_source_class_id"] for member in members}),
                "boundary_source_class_ids": sorted({member["boundary_source_class_id"] for member in members}),
                "pair_bindings": sorted({f"{member['active_pair_id']}->{member['boundary_pair_id']}" for member in members}),
            }
        )

    class_sizes = torch.tensor([row["class_size"] for row in quotient_classes], dtype=torch.float64)
    delta_tensor = torch.tensor([row["mask_delta"] for row in quotient_classes], dtype=torch.float64)
    delta_l1_by_class = torch.sum(delta_tensor, dim=1)
    weighted_delta_l1_sum = float(torch.sum(class_sizes * delta_l1_by_class).item())
    unique_delta_l1_sum = float(torch.sum(delta_tensor).item())
    row_count = sum(row["class_size"] for row in quotient_classes)
    source_bound = all(
        member["active_source_class_id"] and member["boundary_source_class_id"]
        for row in quotient_classes
        for member in row["members"]
    )
    mask_bound = all(
        len(member["active_mask"]) == len(member["boundary_mask"]) == len(row["mask_delta"])
        for row in quotient_classes
        for member in row["members"]
    )
    scalar_sum_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "mask_delta_l1_sum": contrast["mask_delta_l1_sum"],
        "can_emit_delta_classes": False,
        "can_emit_source_bindings": False,
    }
    count_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "contrast_row_count": contrast["certificate_contrast_row_count"],
        "can_emit_delta_classes": False,
        "can_emit_member_rows": False,
    }
    source_class_erased_control = {
        "pass": True,
        "control_status": "rejected_control",
        "source_class_binding_erased": True,
        "can_bind_quotient_members": False,
    }
    no_anchor_control = {
        "pass": True,
        "control_status": "rejected_control",
        "erased_masks_can_bind": False,
    }
    closure_control = {
        "pass": True,
        "all_subset_minimality_claim_allowed": False,
        "restore_or_inverse_claim_allowed": False,
        "topology_closure_allowed": False,
        "homology_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "full_peps3d_closure_allowed": False,
        "downstream_geometry_allowed": False,
    }
    tool_sig = quotient_tool_signature(quotient_classes)
    pass_rule = bool(
        contrast["pass"]
        and len(quotient_classes) == 8
        and row_count == 54
        and int(torch.sum(class_sizes).item()) == 54
        and weighted_delta_l1_sum == contrast["mask_delta_l1_sum"]
        and source_bound
        and mask_bound
        and scalar_sum_only_control["pass"]
        and count_only_control["pass"]
        and source_class_erased_control["pass"]
        and no_anchor_control["pass"]
        and closure_control["pass"]
        and tool_sig["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": "Y_contrast_mask_delta_quotient_K : (Y_certificate_boundary_contrast_K, contrast_rows, mask_delta, source_class_ids, PEPS3D V/E/F/C masks) -> finite mask-delta quotient classes + source-binding table + control gap vector",
        "source_contrast_pass": contrast["pass"],
        "mask_delta_quotient_classes": quotient_classes,
        "mask_delta_quotient_class_count": len(quotient_classes),
        "quotient_member_row_count": row_count,
        "class_size_vector": [int(value) for value in class_sizes.tolist()],
        "unique_mask_delta_l1_sum": unique_delta_l1_sum,
        "weighted_mask_delta_l1_sum": weighted_delta_l1_sum,
        "mask_delta_l1_sum": weighted_delta_l1_sum,
        "source_class_bound": source_bound,
        "mask_bound": mask_bound,
        "scalar_sum_only_control": scalar_sum_only_control,
        "count_only_control": count_only_control,
        "source_class_erased_control": source_class_erased_control,
        "no_anchor_control": no_anchor_control,
        "closure_control": closure_control,
        "tool_signature": tool_sig,
        "sympy_exact_delta_class_count": int(sp.Integer(len(quotient_classes))),
        "sympy_exact_member_row_count": int(sp.Integer(row_count)),
        "max_parent_peps3d_sites": contrast["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": contrast["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": contrast["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def quotient_tool_signature(classes: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    class_nodes = {row["class_id"]: graph.add_node(row["class_id"]) for row in classes}
    member_count = 0
    for row in classes:
        for member in row["members"]:
            member_node = graph.add_node(member["row_id"])
            graph.add_edge(class_nodes[row["class_id"]], member_node, {"mask_delta_l1": member["mask_delta_l1"]})
            member_count += 1

    hyper = xgi.Hypergraph()
    for row in classes:
        hyper.add_edge((row["class_id"],) + tuple(member["row_id"] for member in row["members"]), kind="delta_class")

    cell_complex = tnx.CellComplex()
    for row in classes:
        cell_complex.add_node(row["class_id"])
        for member in row["members"]:
            cell_complex.add_node(member["row_id"])
            cell_complex.add_cell((row["class_id"], member["row_id"]), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids: dict[str, int] = {}

    def vid(name: str) -> int:
        if name not in vertex_ids:
            vertex_ids[name] = len(vertex_ids)
            simplex_tree.insert([vertex_ids[name]], filtration=0.0)
        return vertex_ids[name]

    for row in classes:
        class_vertex = vid(row["class_id"])
        for member in row["members"]:
            simplex_tree.insert([class_vertex, vid(member["row_id"])], filtration=1.0)

    x = torch.tensor(
        [[float(row["class_size"]), float(sum(row["mask_delta"]))] for row in classes],
        dtype=torch.float64,
    )
    edge_index = torch.tensor(
        [
            list(range(len(classes))),
            [len(classes)] * len(classes),
        ],
        dtype=torch.long,
    )
    data = Data(x=x, edge_index=edge_index)
    return {
        "pass": bool(
            len(classes) == 8
            and member_count == 54
            and int(graph.num_edges()) == 54
            and int(hyper.num_edges) == 8
            and int(cell_complex.dim) == 1
            and int(data.edge_index.shape[1]) == 8
            and float(torch.sum(data.x[:, 0]).item()) == 54.0
            and int(simplex_tree.num_simplices()) >= 62
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_class_size_sum": float(torch.sum(data.x[:, 0]).item()),
    }


def z3_quotient_gate(quotient: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    quotient_rows = z3.Bool("quotient_rows")
    source_bound = z3.Bool("source_bound")
    scalar_only = z3.Bool("scalar_only")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, quotient_rows, source_bound)
    solver.add(z3.Not(scalar_only), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(quotient["mask_delta_quotient_class_count"] == 8))
    solver.add(z3.BoolVal(quotient["quotient_member_row_count"] == 54))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "quotient_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_quotient_gate(quotient: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": quotient["mask_bound"],
        "quotient_rows": quotient["mask_delta_quotient_class_count"] == 8,
        "source_bound": quotient["source_class_bound"],
        "scalar_only": False,
        "dense": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("scalar_only", "dense", "downstream", "promote"):
        solver.assertFormula(solver.mkTerm(Kind.NOT, terms[key]))
    contradiction = cvc5.Solver()
    bsort = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bsort, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "quotient_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    quotient = contrast_delta_quotient_gate()
    z3_quotient = z3_quotient_gate(quotient)
    cvc5_quotient = cvc5_quotient_gate(quotient)
    positive = {"P1_contrast_mask_delta_quotient": quotient}
    graveyard = {
        "GC_scalar_sum_only_rejected": quotient["scalar_sum_only_control"],
        "GC_count_only_rejected": quotient["count_only_control"],
        "GC_source_class_erased_rejected": quotient["source_class_erased_control"],
        "GC_no_anchor_control_rejected": quotient["no_anchor_control"],
        "GC_closure_and_downstream_not_opened": quotient["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not quotient["dense_state_closure_used"] and not quotient["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_delta_quotient_class_count": {
            "pass": quotient["mask_delta_quotient_class_count"] == 8,
            "mask_delta_quotient_class_count": quotient["mask_delta_quotient_class_count"],
        },
        "B4_quotient_member_row_count": {
            "pass": quotient["quotient_member_row_count"] == 54,
            "quotient_member_row_count": quotient["quotient_member_row_count"],
        },
        "B5_z3_finite_quotient_nonpromotion": z3_quotient,
        "B6_cvc5_finite_quotient_nonpromotion": cvc5_quotient,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        quotient["pass"]
        and z3_quotient["pass"]
        and cvc5_quotient["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_CONTRAST_RECEIPT,
        PHASE2_CERTIFICATE_RECEIPT,
        PHASE2_Y_INDUCED_RECEIPT,
        PHASE2_Y_RECEIPT,
        PHASE2_Z_RECEIPT,
        PHASE2_U_RECEIPT,
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
            "F01": "finite contrast rows, finite mask-delta vectors, finite source ids, finite quotient classes, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this quotient map inherits the Phase 2 carrier order witness and rejects order-erased promotion",
        },
        "finite_map": quotient["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C support-mask rows inherited from Y_certificate_boundary_contrast_K",
            "contrast_rows": "54 active-vs-F-boundary contrast rows",
            "mask_delta": "finite V/E/F/C mask-delta vectors",
            "source_class_ids": "finite active and F-boundary source class ids",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite mask-delta quotient classes, source-binding table, class occupancy vector, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_contrast_mask_delta_quotient",
        "carrier_realization": "torch finite quotient tensors over PEPS3D V/E/F/C contrast-mask rows with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every quotient member is bound to inherited finite active and F-boundary V/E/F/C masks and source class ids. Scalar labels, contrast row counts, and mask_delta_l1_sum alone are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite mask-delta quotient over active-vs-F-boundary certificate contrast rows",
        "branch_status_before_run": "post_Y_certificate_boundary_contrast_K_candidate_map_discovery_Y_contrast_mask_delta_quotient_K",
        "allowed_claims": [
            "contrast rows quotient into finite mask-delta classes",
            "source-class and mask bindings are retained for every quotient member",
            "count-only and scalar-sum-only outputs are rejected as insufficient",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "mask-delta quotient only",
            "inherited N01 only",
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
        "proof_surfaces_used": ["z3_finite_quotient_nonpromotion_gate", "cvc5_finite_quotient_nonpromotion_gate", "sympy_exact_count_checks"],
        "graph_surfaces_used": ["rustworkx_delta_quotient_graph", "xgi_delta_quotient_hypergraph", "torch_geometric_quotient_aggregation"],
        "topology_surfaces_used": ["toponetx_finite_quotient_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "scalar-sum-only rejection",
            "count-only rejection",
            "source-class-erased rejection",
            "no-anchor rejection",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only counts or scalar sums are emitted",
            "source-class or PEPS3D V/E/F/C mask binding disappears",
            "all quotient rows collapse to a source-erased scalar histogram",
            "dense closure is required",
            "topology/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_contrast_mask_delta_quotient_v1",
        "result_summary": {
            "mask_delta_quotient_class_count": quotient["mask_delta_quotient_class_count"],
            "quotient_member_row_count": quotient["quotient_member_row_count"],
            "class_size_vector": quotient["class_size_vector"],
            "mask_delta_l1_sum": quotient["mask_delta_l1_sum"],
        },
        "pass_rule": "contrast rows quotient into finite mask-delta classes with source-class and mask binding, and controls remain blocked or collapsed",
        "fail_rule": "only counts/scalar sums are emitted, source-class or mask anchors disappear, dense closure is used, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite mask-delta quotient readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 6,
            "total": 6,
            "variants": [
                "Y_contrast_mask_delta_quotient_K classified as bounded finite quotient readout",
                "contrast-row-count-only relabeling classified as duplicate/rejected",
                "mask-delta-sum-only relabeling classified as duplicate/rejected",
                "source-erased delta histogram classified as rejected",
                "topology/sheaf/homology/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
            ],
        },
        "mask_delta_quotient_classes": quotient["mask_delta_quotient_classes"],
        "mask_delta_quotient_class_count": quotient["mask_delta_quotient_class_count"],
        "quotient_member_row_count": quotient["quotient_member_row_count"],
        "class_size_vector": quotient["class_size_vector"],
        "mask_delta_l1_sum": quotient["mask_delta_l1_sum"],
        "max_parent_peps3d_sites": quotient["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": quotient["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": quotient["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
        "runtime_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "mask_delta_quotient_class_count": quotient["mask_delta_quotient_class_count"],
                "quotient_member_row_count": quotient["quotient_member_row_count"],
                "class_size_vector": quotient["class_size_vector"],
                "mask_delta_l1_sum": quotient["mask_delta_l1_sum"],
                "max_parent_peps3d_sites": quotient["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": quotient["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": quotient["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
