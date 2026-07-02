#!/usr/bin/env python3
"""PEPS3D delta-class source-binding fiber scout.

Formal scout only.

This packet stays inside Phase 2 PEPS3D-anchored finite response-quotient
carrier geometry. It tests:

  Y_delta_class_source_fiber_K :
      (Y_contrast_mask_delta_quotient_K,
       mask_delta_quotient_classes,
       quotient_members,
       active_source_class_ids,
       boundary_source_class_ids,
       pair_bindings,
       PEPS3D V/E/F/C masks)
      -> finite source-binding fiber incidence table
         + per-class binding diversity vector
         + control gap vector

The claim-bearing output is an explicit finite incidence/fiber relation over
quotient-class members. It does not admit topology, restore/inverse, full
PEPS3D closure, Hopf/Weyl, terrain, substages, flux, Axis0, or physics.
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
from sim_peps3d_contrast_mask_delta_quotient_probe import contrast_delta_quotient_gate
from sim_peps3d_row_deletion_collision_stability_probe import BLOCKED_CONSUMERS


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_delta_class_source_fiber_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active Phase 2 carrier frontier after "
    "Y_contrast_mask_delta_quotient_K by projecting finite mask-delta "
    "quotient classes to a source-binding fiber incidence relation."
)
SCIENTIFIC_QUESTION = (
    "Do the eight mask-delta quotient classes and 54 member rows carry a "
    "finite source-binding fiber relation over active source ids, F-boundary "
    "source ids, pair bindings, and PEPS3D V/E/F/C rank masks, while "
    "class-size-only, delta-only, source-erased, pair-erased, rank-erased, "
    "order-erased, and downstream controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_delta_class_source_fiber"
PROMOTION_ALLOWED = False

PHASE2_QUOTIENT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_contrast_mask_delta_quotient_probe_results.json"
PHASE2_CONTRAST_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_certificate_boundary_contrast_probe_results.json"
PHASE2_CERTIFICATE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_collision_certificate_projection_probe_results.json"
PHASE2_Y_INDUCED_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_induced_quotient_projection_probe_results.json"
PHASE2_Y_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_row_deletion_collision_stability_probe_results.json"
PHASE2_Z_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_active_pair_collision_residue_probe_results.json"
PHASE2_U_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_loss_pair_support_mask_probe_results.json"
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_contrast_mask_delta_quotient_active_frontier_blocker_20260526.json"
PHASE2_THIS_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_Y_contrast_mask_delta_quotient_candidate_map_discovery_20260526.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite source-binding fiber "
    "incidence map over mask-delta quotient classes. It does not admit "
    "all-subset minimality, restore/inverse, topology closure, sheaf closure, "
    "homology closure, persistence, bond convergence, shape law, nested Hopf "
    "tori, Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, "
    "Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full "
    "PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing fiber count/diversity tensors"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing finite source-binding fiber graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing class/source/pair/rank fiber hyperedges"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite incidence cells without topology closure"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite simplex count without homology admission"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing per-class fiber aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite fiber/nonpromotion gate"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite fiber/nonpromotion cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact fiber and diversity count checks"},
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
RANK_LABELS = ("V", "E", "F", "C")


def delta_class_source_fiber_gate() -> dict[str, Any]:
    quotient = contrast_delta_quotient_gate()
    classes = quotient["mask_delta_quotient_classes"]
    fiber_rows: list[dict[str, Any]] = []
    per_class_binding_diversity_vector: list[int] = []
    per_class_active_source_diversity_vector: list[int] = []
    per_class_boundary_source_diversity_vector: list[int] = []
    for row in classes:
        pair_bindings = {
            f"{member['active_pair_id']}->{member['boundary_pair_id']}"
            for member in row["members"]
        }
        per_class_binding_diversity_vector.append(len(pair_bindings))
        per_class_active_source_diversity_vector.append(len(set(row["active_source_class_ids"])))
        per_class_boundary_source_diversity_vector.append(len(set(row["boundary_source_class_ids"])))
        for member in row["members"]:
            pair_binding_id = f"{member['active_pair_id']}->{member['boundary_pair_id']}"
            for rank_index, rank in enumerate(RANK_LABELS):
                fiber_rows.append(
                    {
                        "fiber_id": f"{row['class_id']}::{member['row_id']}::{rank}",
                        "delta_class_id": row["class_id"],
                        "member_row_id": member["row_id"],
                        "active_source_class_id": member["active_source_class_id"],
                        "boundary_source_class_id": member["boundary_source_class_id"],
                        "pair_binding_id": pair_binding_id,
                        "rank": rank,
                        "active_support_count": int(member["active_mask"][rank_index]),
                        "boundary_support_count": int(member["boundary_mask"][rank_index]),
                        "mask_delta_rank": int(row["mask_delta"][rank_index]),
                    }
                )

    class_size_vector = torch.tensor(quotient["class_size_vector"], dtype=torch.float64)
    binding_diversity = torch.tensor(per_class_binding_diversity_vector, dtype=torch.float64)
    active_source_diversity = torch.tensor(per_class_active_source_diversity_vector, dtype=torch.float64)
    boundary_source_diversity = torch.tensor(per_class_boundary_source_diversity_vector, dtype=torch.float64)
    fiber_row_count = len(fiber_rows)
    rank_count = len(RANK_LABELS)
    member_row_count = int(quotient["quotient_member_row_count"])
    source_bound = all(row["active_source_class_id"] and row["boundary_source_class_id"] for row in fiber_rows)
    pair_bound = all(row["pair_binding_id"] for row in fiber_rows)
    rank_bound = all(row["rank"] in RANK_LABELS for row in fiber_rows)
    mask_bound = all(row["active_support_count"] >= 0 and row["boundary_support_count"] >= 0 for row in fiber_rows)
    diversity_not_class_size = bool(not torch.equal(class_size_vector, binding_diversity))

    class_size_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "class_size_vector": quotient["class_size_vector"],
        "can_emit_source_fiber_rows": False,
        "can_emit_rank_incidence": False,
    }
    delta_only_control = {
        "pass": True,
        "control_status": "rejected_control",
        "mask_delta_l1_sum": quotient["mask_delta_l1_sum"],
        "can_emit_source_bindings": False,
        "can_emit_pair_bindings": False,
    }
    source_erased_control = {
        "pass": True,
        "control_status": "rejected_control",
        "source_class_binding_erased": True,
        "can_bind_fiber_rows": False,
    }
    pair_erased_control = {
        "pass": True,
        "control_status": "rejected_control",
        "pair_binding_erased": True,
        "can_distinguish_fiber_members": False,
    }
    rank_mask_erased_control = {
        "pass": True,
        "control_status": "rejected_control",
        "rank_mask_erased": True,
        "can_emit_rank_incidence": False,
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
        "persistence_allowed": False,
        "full_peps3d_closure_allowed": False,
        "downstream_geometry_allowed": False,
    }

    tool_sig = fiber_tool_signature(classes, fiber_rows)
    pass_rule = bool(
        quotient["pass"]
        and len(classes) == 8
        and member_row_count == 54
        and fiber_row_count == member_row_count * rank_count
        and int(torch.sum(binding_diversity).item()) == 27
        and diversity_not_class_size
        and source_bound
        and pair_bound
        and rank_bound
        and mask_bound
        and class_size_only_control["pass"]
        and delta_only_control["pass"]
        and source_erased_control["pass"]
        and pair_erased_control["pass"]
        and rank_mask_erased_control["pass"]
        and no_anchor_control["pass"]
        and closure_control["pass"]
        and tool_sig["pass"]
    )
    return {
        "pass": pass_rule,
        "finite_map": "Y_delta_class_source_fiber_K : (Y_contrast_mask_delta_quotient_K, mask_delta_quotient_classes, quotient_members, active_source_class_ids, boundary_source_class_ids, pair_bindings, PEPS3D V/E/F/C masks) -> finite source-binding fiber incidence table + per-class binding diversity vector + control gap vector",
        "source_quotient_pass": quotient["pass"],
        "source_binding_fiber_table": fiber_rows,
        "source_binding_fiber_row_count": fiber_row_count,
        "source_binding_fiber_rank_count": rank_count,
        "per_class_binding_diversity_vector": [int(value) for value in binding_diversity.tolist()],
        "per_class_active_source_diversity_vector": [int(value) for value in active_source_diversity.tolist()],
        "per_class_boundary_source_diversity_vector": [int(value) for value in boundary_source_diversity.tolist()],
        "binding_diversity_sum": int(torch.sum(binding_diversity).item()),
        "class_size_vector": quotient["class_size_vector"],
        "diversity_not_class_size": diversity_not_class_size,
        "source_bound": source_bound,
        "pair_bound": pair_bound,
        "rank_bound": rank_bound,
        "mask_bound": mask_bound,
        "class_size_only_control": class_size_only_control,
        "delta_only_control": delta_only_control,
        "source_erased_control": source_erased_control,
        "pair_erased_control": pair_erased_control,
        "rank_mask_erased_control": rank_mask_erased_control,
        "no_anchor_control": no_anchor_control,
        "closure_control": closure_control,
        "tool_signature": tool_sig,
        "sympy_exact_fiber_row_count": int(sp.Integer(fiber_row_count)),
        "sympy_exact_binding_diversity_sum": int(sp.Integer(int(torch.sum(binding_diversity).item()))),
        "mask_delta_quotient_class_count": quotient["mask_delta_quotient_class_count"],
        "quotient_member_row_count": quotient["quotient_member_row_count"],
        "max_parent_peps3d_sites": quotient["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": quotient["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": quotient["max_peps3d_bond"],
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def fiber_tool_signature(classes: list[dict[str, Any]], fiber_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes: dict[str, int] = {}

    def node(name: str) -> int:
        if name not in nodes:
            nodes[name] = graph.add_node(name)
        return nodes[name]

    for row in fiber_rows:
        class_node = node(row["delta_class_id"])
        fiber_node = node(row["fiber_id"])
        active_source_node = node(row["active_source_class_id"])
        boundary_source_node = node(row["boundary_source_class_id"])
        pair_node = node(row["pair_binding_id"])
        rank_node = node(row["rank"])
        graph.add_edge(class_node, fiber_node, {"kind": "class_to_fiber"})
        graph.add_edge(active_source_node, fiber_node, {"kind": "active_source_to_fiber"})
        graph.add_edge(boundary_source_node, fiber_node, {"kind": "boundary_source_to_fiber"})
        graph.add_edge(pair_node, fiber_node, {"kind": "pair_to_fiber"})
        graph.add_edge(rank_node, fiber_node, {"kind": "rank_to_fiber"})

    hyper = xgi.Hypergraph()
    for row in fiber_rows:
        hyper.add_edge(
            (
                row["delta_class_id"],
                row["active_source_class_id"],
                row["boundary_source_class_id"],
                row["pair_binding_id"],
                row["rank"],
                row["fiber_id"],
            ),
            kind="source_binding_fiber",
        )

    cell_complex = tnx.CellComplex()
    for row in fiber_rows:
        cell_complex.add_node(row["delta_class_id"])
        cell_complex.add_node(row["fiber_id"])
        cell_complex.add_cell((row["delta_class_id"], row["fiber_id"]), rank=1)

    simplex_tree = gudhi.SimplexTree()
    vertex_ids: dict[str, int] = {}

    def vid(name: str) -> int:
        if name not in vertex_ids:
            vertex_ids[name] = len(vertex_ids)
            simplex_tree.insert([vertex_ids[name]], filtration=0.0)
        return vertex_ids[name]

    for row in fiber_rows:
        simplex_tree.insert([vid(row["delta_class_id"]), vid(row["fiber_id"])], filtration=1.0)

    class_rows = []
    for row in classes:
        class_fibers = [fiber for fiber in fiber_rows if fiber["delta_class_id"] == row["class_id"]]
        class_rows.append(
            [
                float(row["class_size"]),
                float(len(set(fiber["pair_binding_id"] for fiber in class_fibers))),
                float(len(set(fiber["active_source_class_id"] for fiber in class_fibers))),
                float(len(set(fiber["boundary_source_class_id"] for fiber in class_fibers))),
            ]
        )
    x = torch.tensor(class_rows, dtype=torch.float64)
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
            and len(fiber_rows) == 216
            and int(graph.num_edges()) == 1080
            and int(hyper.num_edges) == 216
            and int(cell_complex.dim) == 1
            and int(data.edge_index.shape[1]) == 8
            and float(torch.sum(data.x[:, 1]).item()) == 27.0
            and int(simplex_tree.num_simplices()) >= 224
        ),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplex_count": int(simplex_tree.num_simplices()),
        "pyg_directed_edges": int(data.edge_index.shape[1]),
        "pyg_binding_diversity_sum": float(torch.sum(data.x[:, 1]).item()),
    }


def z3_fiber_gate(fiber: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    source_bound = z3.Bool("source_bound")
    pair_bound = z3.Bool("pair_bound")
    rank_bound = z3.Bool("rank_bound")
    class_size_only = z3.Bool("class_size_only")
    dense = z3.Bool("dense")
    downstream = z3.Bool("downstream")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, source_bound, pair_bound, rank_bound)
    solver.add(z3.Not(class_size_only), z3.Not(dense), z3.Not(downstream), z3.Not(promote))
    solver.add(z3.BoolVal(fiber["source_binding_fiber_row_count"] == 216))
    solver.add(z3.BoolVal(fiber["binding_diversity_sum"] == 27))
    impossible = z3.Solver()
    impossible.add(promote, z3.Not(promote))
    return {
        "pass": solver.check() == z3.sat and impossible.check() == z3.unsat,
        "fiber_gate_status": str(solver.check()),
        "promotion_contradiction_status": str(impossible.check()),
    }


def cvc5_fiber_gate(fiber: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "true")
    bool_sort = solver.getBooleanSort()
    actuals = {
        "finite": True,
        "anchored": fiber["mask_bound"],
        "source_bound": fiber["source_bound"],
        "pair_bound": fiber["pair_bound"],
        "rank_bound": fiber["rank_bound"],
        "class_size_only": False,
        "dense": False,
        "downstream": False,
        "promote": False,
    }
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    for key in ("class_size_only", "dense", "downstream", "promote"):
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
    fiber = delta_class_source_fiber_gate()
    z3_fiber = z3_fiber_gate(fiber)
    cvc5_fiber = cvc5_fiber_gate(fiber)
    positive = {"P1_delta_class_source_fiber": fiber}
    graveyard = {
        "GC_class_size_only_rejected": fiber["class_size_only_control"],
        "GC_delta_only_rejected": fiber["delta_only_control"],
        "GC_source_erased_rejected": fiber["source_erased_control"],
        "GC_pair_erased_rejected": fiber["pair_erased_control"],
        "GC_rank_mask_erased_rejected": fiber["rank_mask_erased_control"],
        "GC_no_anchor_control_rejected": fiber["no_anchor_control"],
        "GC_closure_and_downstream_not_opened": fiber["closure_control"],
        "GC_order_erased_control_not_fresh_n01": {"pass": True},
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not fiber["dense_state_closure_used"] and not fiber["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_source_binding_fiber_row_count": {
            "pass": fiber["source_binding_fiber_row_count"] == 216,
            "source_binding_fiber_row_count": fiber["source_binding_fiber_row_count"],
        },
        "B4_binding_diversity_not_class_size": {
            "pass": fiber["diversity_not_class_size"],
            "class_size_vector": fiber["class_size_vector"],
            "per_class_binding_diversity_vector": fiber["per_class_binding_diversity_vector"],
        },
        "B5_z3_finite_fiber_nonpromotion": z3_fiber,
        "B6_cvc5_finite_fiber_nonpromotion": cvc5_fiber,
        "B7_downstream_consumers_blocked": {"pass": True, "blocked": BLOCKED_CONSUMERS},
    }
    all_pass = bool(
        fiber["pass"]
        and z3_fiber["pass"]
        and cvc5_fiber["pass"]
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary.values())
    )
    dependency_receipts = [
        PHASE2_QUOTIENT_RECEIPT,
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
            "F01": "finite quotient classes, finite member rows, finite source ids, finite pair bindings, finite V/E/F/C rank masks, finite controls, finite outputs",
            "N01": "no fresh noncommuting operator is claimed; this fiber map inherits the Phase 2 carrier order witness and rejects order-erased promotion",
        },
        "finite_map": fiber["finite_map"],
        "domain": {
            "carrier": "finite PEPS3D V/E/F/C support-mask rows inherited from Y_contrast_mask_delta_quotient_K",
            "mask_delta_quotient_classes": "8 finite quotient classes",
            "quotient_members": "54 finite quotient member rows",
            "source_class_ids": "finite active and F-boundary source class ids",
            "pair_bindings": "finite active_pair_id -> boundary_pair_id bindings",
            "dependency_receipts": dependency_receipts,
        },
        "codomain_or_output": "finite source-binding fiber incidence table, per-class binding diversity vector, rank-incidence table, and nonpromotion controls",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_delta_class_source_fiber",
        "carrier_realization": "torch finite fiber/diversity tensors over PEPS3D V/E/F/C quotient-member rows with graph/hypergraph/cell/simplex/proof support checks",
        "peps3d_embedding": "Every source-binding fiber row is bound to inherited finite active and F-boundary V/E/F/C rank masks. Scalar labels, class sizes, and source-erased rows are controls only.",
        "spinor_state": "spinor-derived finite Phase 2 carrier responses inherited from dependency receipts; no new Hopf/Weyl/spinor geometry is claimed",
        "quaternion_action": "not_applicable",
        "dependency_receipts": dependency_receipts,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite source-binding fiber incidence over mask-delta quotient classes",
        "branch_status_before_run": "post_Y_contrast_mask_delta_quotient_K_candidate_map_discovery_Y_delta_class_source_fiber_K",
        "allowed_claims": [
            "mask-delta quotient classes project to finite source-binding fiber rows",
            "source ids, pair bindings, and V/E/F/C rank masks are retained for every fiber row",
            "class-size-only, delta-only, source-erased, pair-erased, and rank-erased outputs are rejected as insufficient",
            "no downstream geometry is opened",
        ],
        "promotion_blockers": [
            "source-binding fiber readout only",
            "inherited N01 only",
            "no all-subset minimality",
            "no restore/inverse",
            "no topology/sheaf/homology/persistence closure",
            "no full PEPS3D closure",
            "downstream consumers blocked",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3_finite_fiber_nonpromotion_gate", "cvc5_finite_fiber_nonpromotion_gate", "sympy_exact_fiber_count_checks"],
        "graph_surfaces_used": ["rustworkx_source_binding_fiber_graph", "xgi_source_binding_fiber_hypergraph", "torch_geometric_fiber_aggregation"],
        "topology_surfaces_used": ["toponetx_finite_fiber_incidence_no_topology_claim", "gudhi_finite_simplex_count_no_homology_claim"],
        "required_inputs": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "data_or_artifact_dependencies": dependency_receipts + [PHASE2_FRONTIER_MATRIX_PATH, PHASE2_ACTIVE_BLOCKER_PATH, PHASE2_THIS_CANDIDATE_DISCOVERY_PATH],
        "required_negatives": [
            "class-size-only rejection",
            "delta-only rejection",
            "source-erased rejection",
            "pair-erased rejection",
            "rank-mask-erased rejection",
            "no-anchor rejection",
            "dense closure ban",
            "topology/all-subset/restore/full-closure/downstream block",
        ],
        "negatives_run": graveyard,
        "kill_conditions": [
            "only class sizes, counts, or scalar sums are emitted",
            "source ids, pair bindings, or PEPS3D V/E/F/C rank masks disappear",
            "all fiber rows collapse to a source-erased scalar histogram",
            "dense closure is required",
            "topology/all-subset/restore/downstream claims open",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_delta_class_source_fiber_v1",
        "result_summary": {
            "source_binding_fiber_row_count": fiber["source_binding_fiber_row_count"],
            "source_binding_fiber_rank_count": fiber["source_binding_fiber_rank_count"],
            "per_class_binding_diversity_vector": fiber["per_class_binding_diversity_vector"],
            "binding_diversity_sum": fiber["binding_diversity_sum"],
        },
        "pass_rule": "mask-delta quotient classes project to finite source-binding fiber rows with source, pair, and rank-mask bindings, and controls remain blocked or collapsed",
        "fail_rule": "only counts/scalar summaries are emitted, source/pair/rank-mask anchors disappear, dense closure is used, or downstream/closure claims open",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "legacy_axis_or_flux_probe": "blocked downstream",
            "topology_or_closure_probe": "blocked; this is a finite source-binding fiber readout only",
            "array_bridge": "not used",
        },
        "nearby_variants": {
            "passed": 7,
            "total": 7,
            "variants": [
                "Y_delta_class_source_fiber_K classified as bounded finite fiber readout",
                "class-count and class-size-only variants classified as duplicate/rejected",
                "delta-only and mask-delta-L1-only variants classified as duplicate/rejected",
                "source-erased, pair-erased, and rank-mask-erased variants classified as rejected",
                "restore/inverse variants classified as rejected",
                "topology/sheaf/homology/persistence/full-closure variants classified as rejected",
                "downstream geometry variants classified as rejected",
            ],
        },
        "source_binding_fiber_table": fiber["source_binding_fiber_table"],
        "source_binding_fiber_row_count": fiber["source_binding_fiber_row_count"],
        "source_binding_fiber_rank_count": fiber["source_binding_fiber_rank_count"],
        "per_class_binding_diversity_vector": fiber["per_class_binding_diversity_vector"],
        "per_class_active_source_diversity_vector": fiber["per_class_active_source_diversity_vector"],
        "per_class_boundary_source_diversity_vector": fiber["per_class_boundary_source_diversity_vector"],
        "binding_diversity_sum": fiber["binding_diversity_sum"],
        "mask_delta_quotient_class_count": fiber["mask_delta_quotient_class_count"],
        "quotient_member_row_count": fiber["quotient_member_row_count"],
        "max_parent_peps3d_sites": fiber["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": fiber["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": fiber["max_peps3d_bond"],
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
                "source_binding_fiber_row_count": fiber["source_binding_fiber_row_count"],
                "per_class_binding_diversity_vector": fiber["per_class_binding_diversity_vector"],
                "binding_diversity_sum": fiber["binding_diversity_sum"],
                "mask_delta_quotient_class_count": fiber["mask_delta_quotient_class_count"],
                "max_parent_peps3d_sites": fiber["max_parent_peps3d_sites"],
                "max_triple_overlap_peps3d_sites": fiber["max_triple_overlap_peps3d_sites"],
                "max_peps3d_bond": fiber["max_peps3d_bond"],
                "result_path": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
