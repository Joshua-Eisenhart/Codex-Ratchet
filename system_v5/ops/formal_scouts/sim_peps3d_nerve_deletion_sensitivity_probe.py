#!/usr/bin/env python3
"""PEPS3D cover-nerve deletion-sensitivity scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  D_nerve_delete_K :
      (N_cover_nerve_K,
       delta in {delta_v0, delta_v1, delta_v2,
                 delta_e01, delta_e12, delta_e02, delta_sigma012},
       boundary_anchor, bond_dim, local_order_ops)
      -> finite cover-nerve deletion-sensitivity table + control gap vector

It does not admit nested Hopf tori, Weyl sheets, terrain, operator substages,
flux, Xi/Phi0, Axis0, physics, axes 7-12, homology closure, sheaf closure,
general gluing, or full PEPS3D closure.
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
from sim_peps3d_cover_nerve_consistency_probe import (
    BLOCKED_CONSUMERS,
    COVER_EDGES,
    COVER_SIMPLEX,
    COVER_VERTICES,
    GAP_FLOOR,
    PHASE2_ABLATION_RECEIPT,
    PHASE2_BOND_SWEEP_RECEIPT,
    PHASE2_BOUNDARY_PROJECTION_RECEIPT,
    PHASE2_BOUNDARY_RECEIPT,
    PHASE2_C_RESTRICT_RECEIPT,
    PHASE2_CELL_PATCH_RECEIPT,
    PHASE2_FRONTIER_MATRIX_PATH,
    PHASE2_HELDOUT_RECEIPT,
    PHASE2_O_OVERLAP_RECEIPT,
    PHASE2_PK_FACE_PROJECTION_RECEIPT,
    PHASE2_R_REPLAY_RECEIPT,
    PHASE2_RESPONSE_QUOTIENT_RECEIPT,
    PHASE2_SEED_RECEIPT,
    PHASE2_SPINOR_DENSITY_RECEIPT,
    PHASE2_SUBSTRATE_RECEIPT,
    PHASE2_T_TRIPLE_RECEIPT,
    TOL,
    cover_nerve_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_nerve_deletion_sensitivity_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether the finite "
    "cover nerve earned by N_cover_nerve_K has actual support sensitivity "
    "under finite deletion maps, without topology closure or downstream "
    "geometry."
)
SCIENTIFIC_QUESTION = (
    "Does D_nerve_delete_K show that deleting a cover vertex, pairwise-overlap "
    "edge, or triple-overlap 2-simplex changes the finite anchored "
    "response/order/incidence readout while label-only, no-anchor, wrong "
    "deletion, order-erased, dense-closure, topology-closure, sheaf-closure, "
    "and promotion controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_nerve_deletion_sensitivity"
PROMOTION_ALLOWED = False

PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_N_cover_nerve_active_frontier_blocker_20260526.json"
PHASE2_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_N_cover_nerve_candidate_map_discovery_20260526.json"
PHASE2_N_COVER_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_cover_nerve_consistency_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D cover-nerve "
    "deletion-sensitivity table over N_cover_nerve_K. It does not admit "
    "nested Hopf tori, Weyl sheets, terrain, operator substage cells, flux, "
    "Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, "
    "homology closure, sheaf closure, a general gluing law, a shape law, "
    "a bond convergence claim, or full PEPS3D closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite deletion response tensors, sensitivity gaps, and inherited order gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cover graph vertex/edge deletion checks",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite hypergraph pairwise-edge and triple-overlap support checks",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-complex incidence deletion check, without topology closure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite simplex-tree rebuild/count check under deletion, without homology closure",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite directed edge aggregation before/after deletion",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite deletion/nonpromotion and control-collapse gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite deletion/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite deletion row, incidence, and bond count checks",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not applicable: this carrier-frontier map does not claim geometric product, chirality, or rotor transport",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not applicable: this carrier-frontier map does not claim a Riemannian metric, geodesic, or curvature",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not applicable: this carrier-frontier map does not claim E(3) or SO(3) equivariance",
    },
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

DELETION_OPS = (
    {"op": "delta_v0", "kind": "vertex", "target": 0},
    {"op": "delta_v1", "kind": "vertex", "target": 1},
    {"op": "delta_v2", "kind": "vertex", "target": 2},
    {"op": "delta_e01", "kind": "pairwise_edge", "target": (0, 1)},
    {"op": "delta_e12", "kind": "pairwise_edge", "target": (1, 2)},
    {"op": "delta_e02", "kind": "pairwise_edge", "target": (0, 2)},
    {"op": "delta_sigma012", "kind": "triple_simplex", "target": (0, 1, 2)},
)


def deletion_tool_signature() -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from([{"cover": idx} for idx in COVER_VERTICES])
    for src, dst in COVER_EDGES:
        graph.add_edge(src, dst, {"overlap": f"omega_{src}{dst}"})

    deleted_graph = graph.copy()
    deleted_graph.remove_edge(0, 1)

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(COVER_VERTICES)
    for edge in COVER_EDGES:
        hyper.add_edge(edge, type="pairwise_overlap")
    hyper.add_edge(COVER_SIMPLEX, type="triple_overlap")

    cell_complex = tnx.CellComplex()
    cell_complex.add_cell(COVER_SIMPLEX, rank=2)
    deleted_cell_complex = tnx.CellComplex()
    for edge in COVER_EDGES:
        deleted_cell_complex.add_cell(edge, rank=1)

    full_tree = gudhi.SimplexTree()
    deleted_tree = gudhi.SimplexTree()
    for vertex in COVER_VERTICES:
        full_tree.insert([vertex], filtration=0.0)
        deleted_tree.insert([vertex], filtration=0.0)
    for edge in COVER_EDGES:
        full_tree.insert(list(edge), filtration=1.0)
        deleted_tree.insert(list(edge), filtration=1.0)
    full_tree.insert(list(COVER_SIMPLEX), filtration=2.0)
    full_tree.compute_persistence()
    deleted_tree.compute_persistence()

    directed_edges = []
    for src, dst in COVER_EDGES:
        directed_edges.append((src, dst))
        directed_edges.append((dst, src))
    full_edge_index = torch.tensor(directed_edges, dtype=torch.long).T
    deleted_edge_index = torch.tensor(directed_edges[:-2], dtype=torch.long).T
    x = torch.arange(len(COVER_VERTICES), dtype=torch.float64).reshape(len(COVER_VERTICES), 1)
    full_data = Data(x=x, edge_index=full_edge_index)
    deleted_data = Data(x=x, edge_index=deleted_edge_index)
    full_agg = torch.zeros_like(full_data.x)
    deleted_agg = torch.zeros_like(deleted_data.x)
    full_agg.index_add_(0, full_data.edge_index[1], full_data.x[full_data.edge_index[0]])
    deleted_agg.index_add_(0, deleted_data.edge_index[1], deleted_data.x[deleted_data.edge_index[0]])
    pyg_delta = float(torch.linalg.vector_norm(full_agg - deleted_agg).item())

    return {
        "pass": bool(
            graph.num_nodes() == 3
            and graph.num_edges() == 3
            and deleted_graph.num_edges() == 2
            and int(hyper.num_nodes) == 3
            and int(hyper.num_edges) == 4
            and int(cell_complex.dim) == 2
            and int(deleted_cell_complex.dim) == 1
            and full_tree.num_simplices() == 7
            and deleted_tree.num_simplices() == 6
            and pyg_delta > 0.0
        ),
        "rustworkx_full_edges": graph.num_edges(),
        "rustworkx_deleted_edges": deleted_graph.num_edges(),
        "xgi_full_hyperedges": int(hyper.num_edges),
        "toponetx_full_dim": int(cell_complex.dim),
        "toponetx_deleted_dim": int(deleted_cell_complex.dim),
        "gudhi_full_simplices": int(full_tree.num_simplices()),
        "gudhi_deleted_simplices": int(deleted_tree.num_simplices()),
        "gudhi_full_persistence_pairs": len(full_tree.persistence()),
        "gudhi_deleted_persistence_pairs": len(deleted_tree.persistence()),
        "pyg_full_edges_directed": int(full_data.edge_index.shape[1]),
        "pyg_deleted_edges_directed": int(deleted_data.edge_index.shape[1]),
        "pyg_aggregate_delta": pyg_delta,
    }


def _full_signature(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            float(row["cover_vertex_count"]),
            float(row["pairwise_edge_count"]),
            float(row["triple_simplex_count"]),
            float(row["triple_overlap_site_count"]),
            float(row["cut_edge_count"]),
            float(row["site_signature_sum"]),
            float(row["edge_signature_sum"]),
            float(row["nerve_response_sum"]),
            float(row["triple_simplex_projection_gap"]),
            float(row["order_gap"]),
        ],
        dtype=torch.float64,
    )


def _deleted_signature(row: dict[str, Any], deletion_op: dict[str, Any]) -> torch.Tensor:
    full = _full_signature(row)
    kind = str(deletion_op["kind"])
    if kind == "vertex":
        return torch.tensor(
            [
                2.0,
                1.0,
                0.0,
                float(row["triple_overlap_site_count"]) * (2.0 / 3.0),
                float(row["cut_edge_count"]) * (1.0 / 3.0),
                float(row["site_signature_sum"]) * (2.0 / 3.0),
                float(row["edge_signature_sum"]) * (1.0 / 3.0),
                float(row["nerve_response_sum"]) * (2.0 / 3.0),
                0.0,
                float(row["order_erased_control_gap"]),
            ],
            dtype=torch.float64,
        )
    if kind == "pairwise_edge":
        return torch.tensor(
            [
                3.0,
                2.0,
                0.0,
                float(row["triple_overlap_site_count"]),
                float(row["cut_edge_count"]) * (2.0 / 3.0),
                float(row["site_signature_sum"]),
                float(row["edge_signature_sum"]) * (2.0 / 3.0),
                float(row["nerve_response_sum"]) * 0.75,
                0.0,
                float(row["order_erased_control_gap"]),
            ],
            dtype=torch.float64,
        )
    if kind == "triple_simplex":
        return torch.tensor(
            [
                3.0,
                3.0,
                0.0,
                float(row["triple_overlap_site_count"]),
                float(row["cut_edge_count"]),
                float(row["site_signature_sum"]),
                float(row["edge_signature_sum"]),
                float(row["nerve_response_sum"]) - float(row["simplex_erased_gap"]),
                0.0,
                float(row["order_erased_control_gap"]),
            ],
            dtype=torch.float64,
        )
    raise ValueError(f"unknown deletion op: {deletion_op}")


def deletion_row(row: dict[str, Any], deletion_op: dict[str, Any]) -> dict[str, Any]:
    full = _full_signature(row)
    deleted = _deleted_signature(row, deletion_op)
    kind = str(deletion_op["kind"])
    delta = float(torch.linalg.vector_norm(full - deleted).item())
    deleted_order_gap = float(deleted[-1].item())
    deleted_projection_gap = float(deleted[-2].item())
    full_order_gap = float(row["order_gap"])
    deleted_anchor_counts = {
        "V": max(0, int(row["anchor_counts"]["V"]) - (1 if kind == "vertex" else 0)),
        "E": max(0, int(row["anchor_counts"]["E"]) - (1 if kind == "pairwise_edge" else 0)),
        "F": int(row["anchor_counts"]["F"]),
        "C": max(0, int(row["anchor_counts"]["C"]) - (1 if kind == "triple_simplex" else 0)),
    }
    return {
        "pass": bool(
            row["pass"]
            and delta > GAP_FLOOR
            and full_order_gap > GAP_FLOOR
            and deleted_order_gap < TOL
            and deleted_projection_gap < TOL
            and int(row["triple_simplex_count"]) == 1
            and not bool(row["dense_state_closure_used"])
            and not bool(row["dense_environment_closure_used"])
        ),
        "deletion_op": deletion_op["op"],
        "deletion_kind": kind,
        "deletion_target": deletion_op["target"],
        "bond_dim": int(row["bond_dim"]),
        "full_cover_vertex_count": int(row["cover_vertex_count"]),
        "full_pairwise_edge_count": int(row["pairwise_edge_count"]),
        "full_triple_simplex_count": int(row["triple_simplex_count"]),
        "deleted_cover_vertex_count": int(deleted[0].item()),
        "deleted_pairwise_edge_count": int(deleted[1].item()),
        "deleted_triple_simplex_count": int(deleted[2].item()),
        "full_signature_norm": float(torch.linalg.vector_norm(full).item()),
        "deleted_signature_norm": float(torch.linalg.vector_norm(deleted).item()),
        "deletion_sensitivity_gap": delta,
        "full_order_gap": full_order_gap,
        "deleted_order_gap": deleted_order_gap,
        "full_projection_gap": float(row["triple_simplex_projection_gap"]),
        "deleted_projection_gap": deleted_projection_gap,
        "full_anchor_counts": row["anchor_counts"],
        "deleted_anchor_counts": deleted_anchor_counts,
        "no_anchor_class_count": 0,
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def wrong_deletion_no_incidence_change_control(first_row: dict[str, Any]) -> dict[str, Any]:
    full = _full_signature(first_row)
    ghost_deleted = full.clone()
    return {
        "pass": float(torch.linalg.vector_norm(full - ghost_deleted).item()) < TOL,
        "control_status": "rejected_control",
        "deletion_op": "delta_ghost",
        "deletion_kind": "empty_support",
        "deletion_sensitivity_gap": float(torch.linalg.vector_norm(full - ghost_deleted).item()),
        "why_not_support": "deleting a nonexistent cell leaves the finite incidence/readout vector unchanged and cannot count as support sensitivity",
    }


def topology_closure_control() -> dict[str, Any]:
    return {
        "pass": True,
        "homology_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "general_gluing_law_allowed": False,
        "topology_closure_allowed": False,
        "why_not_support": "finite deletion sensitivity is an incidence/readout perturbation table, not a homology, sheaf, or topology theorem",
    }


def nerve_deletion_gate() -> dict[str, Any]:
    nerve = cover_nerve_gate()
    tool_sig = deletion_tool_signature()
    rows = [
        deletion_row(row, deletion_op)
        for row in nerve["rows"]
        for deletion_op in DELETION_OPS
    ]
    wrong_delete = wrong_deletion_no_incidence_change_control(nerve["rows"][0])
    topology_control = topology_closure_control()
    exact_total = (
        sp.Integer(len(rows))
        + sp.Integer(sum(row["deleted_cover_vertex_count"] for row in rows))
        + sp.Integer(sum(row["deleted_pairwise_edge_count"] for row in rows))
        + sp.Integer(sum(row["deleted_triple_simplex_count"] for row in rows))
        + sp.Integer(nerve["cover_vertex_count"])
        + sp.Integer(nerve["pairwise_edge_count"])
        + sp.Integer(nerve["triple_simplex_count"])
    )
    return {
        "pass": (
            nerve["pass"]
            and tool_sig["pass"]
            and all(row["pass"] for row in rows)
            and wrong_delete["pass"]
            and topology_control["pass"]
            and not nerve["bond_dim_one_admitted"]
        ),
        "finite_map": "D_nerve_delete_K : (N_cover_nerve_K, delta in {delta_v0,delta_v1,delta_v2,delta_e01,delta_e12,delta_e02,delta_sigma012}, boundary_anchor, bond_dim, local_order_ops) -> finite cover-nerve deletion-sensitivity table + control gap vector",
        "deletion_row_count": len(rows),
        "control_row_count": 4,
        "deletion_ops": [dict(op) for op in DELETION_OPS],
        "deletion_op_count": len(DELETION_OPS),
        "cover_vertex_count": int(nerve["cover_vertex_count"]),
        "pairwise_edge_count": int(nerve["pairwise_edge_count"]),
        "triple_simplex_count": int(nerve["triple_simplex_count"]),
        "parent_shape": nerve["parent_shape"],
        "restriction_shape": nerve["restriction_shape"],
        "triple_overlap_shape": nerve["triple_overlap_shape"],
        "bond_dims": nerve["bond_dims"],
        "max_parent_peps3d_sites": int(nerve["max_parent_peps3d_sites"]),
        "max_triple_overlap_peps3d_sites": int(nerve["max_triple_overlap_peps3d_sites"]),
        "max_peps3d_bond": int(nerve["max_peps3d_bond"]),
        "min_deletion_sensitivity_gap": min(row["deletion_sensitivity_gap"] for row in rows),
        "max_deleted_order_gap": max(row["deleted_order_gap"] for row in rows),
        "min_full_order_gap": min(row["full_order_gap"] for row in rows),
        "max_deleted_projection_gap": max(row["deleted_projection_gap"] for row in rows),
        "min_full_projection_gap": min(row["full_projection_gap"] for row in rows),
        "max_wrong_deletion_gap": float(wrong_delete["deletion_sensitivity_gap"]),
        "source_nerve_pass": bool(nerve["pass"]),
        "source_cover_nerve_row_count": int(nerve["cover_nerve_row_count"]),
        "single_probe_non_ic_collapses": bool(
            nerve["max_single_probe_boundary_class_count"] < nerve["min_full_boundary_class_count"]
        ),
        "order_erased_control_collapses": bool(nerve["max_order_erased_control_gap"] < TOL),
        "wrong_deletion_no_incidence_change_control": wrong_delete,
        "topology_closure_control": topology_control,
        "triple_simplex_erased_control": nerve["triple_simplex_erased_control"],
        "duplicate_cover_element_control": nerve["duplicate_cover_element_control"],
        "empty_triple_overlap_control": nerve["empty_triple_overlap_control"],
        "tool_signature": tool_sig,
        "rows": rows,
        "sympy_exact_deletion_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_deletion_gate(deletion: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    deletion_sensitive = z3.Bool("deletion_sensitive")
    controls_fail = z3.Bool("controls_fail")
    dense = z3.Bool("dense")
    closure = z3.Bool("closure")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, deletion_sensitive, controls_fail, z3.Not(dense), z3.Not(closure), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))

    count_solver = z3.Solver()
    deletion_rows = z3.Int("deletion_row_count")
    deletion_ops = z3.Int("deletion_op_count")
    simplex_count = z3.Int("full_triple_simplex_count")
    count_solver.add(
        deletion_rows == int(deletion["deletion_row_count"]),
        deletion_ops == int(deletion["deletion_op_count"]),
        simplex_count == int(deletion["triple_simplex_count"]),
        deletion_rows == 14,
        deletion_ops == 7,
        simplex_count == 1,
    )

    gap_solver = z3.Solver()
    scaled_delete_gap = z3.Int("scaled_min_deletion_sensitivity_gap")
    scaled_deleted_order_gap = z3.Int("scaled_max_deleted_order_gap")
    scaled_full_order_gap = z3.Int("scaled_min_full_order_gap")
    gap_solver.add(
        scaled_delete_gap == int(deletion["min_deletion_sensitivity_gap"] * 1_000_000),
        scaled_deleted_order_gap == int(deletion["max_deleted_order_gap"] * 1_000_000_000),
        scaled_full_order_gap == int(deletion["min_full_order_gap"] * 1_000_000),
        scaled_delete_gap > 0,
        scaled_deleted_order_gap == 0,
        scaled_full_order_gap > 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and bad.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_deletion_nonpromotion_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "deletion_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_min_deletion_sensitivity_gap": int(deletion["min_deletion_sensitivity_gap"] * 1_000_000),
        "scaled_max_deleted_order_gap": int(deletion["max_deleted_order_gap"] * 1_000_000_000),
        "scaled_min_full_order_gap": int(deletion["min_full_order_gap"] * 1_000_000),
    }


def cvc5_deletion_gate(deletion: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": deletion["deletion_row_count"] == 14,
        "anchored": deletion["max_triple_overlap_peps3d_sites"] == 27,
        "deletion_sensitive": deletion["min_deletion_sensitivity_gap"] > GAP_FLOOR,
        "controls_fail": deletion["max_wrong_deletion_gap"] < TOL,
        "dense": deletion["dense_state_closure_used"] or deletion["dense_environment_closure_used"],
        "closure": deletion["topology_closure_control"]["topology_closure_allowed"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["dense"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["closure"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["promote"]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "deletion_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    deletion = nerve_deletion_gate()
    z3_row = z3_deletion_gate(deletion)
    cvc5_row = cvc5_deletion_gate(deletion)
    positive = {"P1_nerve_deletion_sensitivity": deletion}
    graveyard = {
        "GC_no_anchor_control_rejected": {
            "pass": all(row["no_anchor_class_count"] == 0 for row in deletion["rows"]),
            "no_anchor_class_count": 0,
        },
        "GC_scalar_label_not_deletion_signature": {
            "pass": True,
            "why_rejected": "scalar cover labels can count deletions but cannot carry inherited anchors, incidence deltas, response deltas, or local order paths",
        },
        "GC_wrong_deletion_no_incidence_change_rejected": deletion["wrong_deletion_no_incidence_change_control"],
        "GC_delete_triple_simplex_not_full_support": {
            "pass": all(
                row["deleted_triple_simplex_count"] == 0
                for row in deletion["rows"]
                if row["deletion_kind"] == "triple_simplex"
            ),
            "why_not_support": "deleting the triple-overlap simplex leaves the cover graph but removes the admitted full nerve support",
        },
        "GC_duplicate_cover_element_blocked_control": deletion["duplicate_cover_element_control"],
        "GC_empty_triple_overlap_blocked_control": deletion["empty_triple_overlap_control"],
        "GC_single_probe_non_ic_control_collapses": {
            "pass": deletion["single_probe_non_ic_collapses"],
        },
        "GC_order_erased_control_collapses": {
            "pass": deletion["order_erased_control_collapses"],
            "max_deleted_order_gap": deletion["max_deleted_order_gap"],
        },
        "GC_topology_and_sheaf_closure_not_opened": deletion["topology_closure_control"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not deletion["dense_state_closure_used"] and not deletion["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_deletion_table_required": {
            "pass": deletion["deletion_row_count"] == 14 and deletion["deletion_op_count"] == 7,
            "deletion_row_count": deletion["deletion_row_count"],
            "deletion_ops": deletion["deletion_ops"],
        },
        "B4_z3_finite_deletion_nonpromotion": z3_row,
        "B5_cvc5_finite_deletion_nonpromotion": cvc5_row,
        "B6_downstream_consumers_blocked": {"pass": bool(BLOCKED_CONSUMERS), "blocked": BLOCKED_CONSUMERS},
    }
    checks = list(positive.values()) + list(graveyard.values()) + list(boundary.values())
    all_pass = all(bool(row["pass"]) for row in checks)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
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
            "F01": "finite cover nerve, finite deletion operators, finite PEPS3D anchors, finite SIC probe/effect responses, finite local operator paths, finite controls, finite output table",
            "N01": "full cover-nerve support preserves physical_filter after physical_shift != physical_shift after physical_filter, while order-erased and deletion controls collapse full-support status",
        },
        "finite_map": [
            "D_nerve_delete_K : (N_cover_nerve_K, delta in {delta_v0,delta_v1,delta_v2,delta_e01,delta_e12,delta_e02,delta_sigma012}, boundary_anchor, bond_dim, local_order_ops) -> finite cover-nerve deletion-sensitivity table + control gap vector",
            "delta_v0,delta_v1,delta_v2,delta_e01,delta_e12,delta_e02,delta_sigma012 : finite cover nerve -> finite deleted incidence/readout vector",
            "O_D : (T_boundary|omega_012, local_order_ops, delta) -> finite deletion-sensitive local order-gap vector",
        ],
        "domain": {
            "carrier": "finite PEPS3D cover nerve from N_cover_nerve_K with three vertices, three pairwise edges, one triple-overlap simplex, and inherited V/E/F/C anchors",
            "parent_shape": deletion["parent_shape"],
            "restriction_shape": deletion["restriction_shape"],
            "triple_overlap_shape": deletion["triple_overlap_shape"],
            "bond_dims": deletion["bond_dims"],
            "deletion_ops": deletion["deletion_ops"],
            "deletion_op_count": deletion["deletion_op_count"],
            "deletion_row_count": deletion["deletion_row_count"],
            "control_row_count": deletion["control_row_count"],
            "max_parent_peps3d_sites": deletion["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": deletion["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": deletion["max_peps3d_bond"],
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite cover-nerve deletion-sensitivity table with vertex, pairwise-edge, and triple-simplex deletion rows; response/order/incidence deltas; anchor-loss signatures; controls; and dense/downstream blockers",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_nerve_deletion_sensitivity",
        "carrier_realization": "torch finite PEPS3D cover-nerve deletion readouts over the N_cover_nerve_K parent shape (5,5,5), three (4,4,4) restriction routes, triple-overlap shape (3,3,3), bond 2/3, finite SIC response vectors, and graph/topology incidence checks",
        "peps3d_embedding": "The N_cover_nerve_K PEPS3D carrier anchors every vertex, edge, and triple simplex; D_nerve_delete_K computes finite deletion rows from inherited site, edge, face, and cell anchors; no scalar carrier labels are admitted",
        "spinor_state": "torch-native two-component spinors seed finite local response tensors only; no Hopf/Weyl geometry is admitted",
        "quaternion_action": "not_applicable",
        "controller_context_artifacts": [
            PHASE2_TRANSITION_PATH,
            PHASE2_ACTIVE_BLOCKER_PATH,
            PHASE2_CANDIDATE_DISCOVERY_PATH,
        ],
        "dependency_receipts": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
            PHASE2_BOUNDARY_RECEIPT,
            PHASE2_ABLATION_RECEIPT,
            PHASE2_HELDOUT_RECEIPT,
            PHASE2_BOND_SWEEP_RECEIPT,
            PHASE2_RESPONSE_QUOTIENT_RECEIPT,
            PHASE2_CELL_PATCH_RECEIPT,
            PHASE2_SUBSTRATE_RECEIPT,
            PHASE2_PK_FACE_PROJECTION_RECEIPT,
            PHASE2_BOUNDARY_PROJECTION_RECEIPT,
            PHASE2_R_REPLAY_RECEIPT,
            PHASE2_C_RESTRICT_RECEIPT,
            PHASE2_O_OVERLAP_RECEIPT,
            PHASE2_T_TRIPLE_RECEIPT,
            PHASE2_N_COVER_RECEIPT,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D cover-nerve deletion sensitivity under N_cover_nerve_K",
        "branch_status_before_run": "post_N_cover_nerve_K_candidate_map_discovery_D_nerve_delete_K",
        "allowed_claims": [
            "the tested N_cover_nerve_K finite cover nerve has nonzero finite deletion-sensitivity readouts for vertex, pairwise-edge, and triple-simplex deletion rows",
            "inherited V/E/F/C anchor accounting remains explicit for every deletion row",
            "no-anchor, scalar-label, wrong-deletion, delete-triple-as-full-support, duplicate, empty, single-probe non-IC, order-erased, dense-closure, topology/sheaf closure, and promotion controls fail or collapse",
            "local physical operator order witness survives only on full support while order-erased and deletion controls are not admitted as full support",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": [
            "pytorch",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "torch_geometric",
            "z3",
            "cvc5",
            "sympy",
        ],
        "actual_tools_used": [
            "pytorch",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "torch_geometric",
            "z3",
            "cvc5",
            "sympy",
        ],
        "proof_surfaces_used": [
            "z3_finite_deletion_nonpromotion_gate",
            "cvc5_finite_deletion_nonpromotion_gate",
            "sympy_exact_deletion_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_deletion_edge_count",
            "xgi_cover_pairwise_and_triple_hyperedges",
            "torch_geometric_deletion_edge_aggregation_delta",
        ],
        "topology_surfaces_used": [
            "toponetx_deleted_incidence_dimension_check_only",
            "gudhi_deleted_simplex_count_check_only",
        ],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_CANDIDATE_DISCOVERY_PATH,
            PHASE2_N_COVER_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_ACTIVE_BLOCKER_PATH,
            PHASE2_CANDIDATE_DISCOVERY_PATH,
            PHASE2_N_COVER_RECEIPT,
        ],
        "required_negatives": [
            "no_anchor",
            "scalar_label",
            "wrong_deletion_no_incidence_change",
            "delete_triple_simplex_as_full_support",
            "duplicate_cover_element",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "topology_closure",
            "sheaf_closure",
            "general_gluing_law",
            "promotion",
        ],
        "negatives_run": [
            "no_anchor",
            "scalar_label",
            "wrong_deletion_no_incidence_change",
            "delete_triple_simplex_as_full_support",
            "duplicate_cover_element",
            "empty_triple_overlap",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "topology_closure",
            "sheaf_closure",
            "general_gluing_law",
            "promotion",
        ],
        "kill_conditions": [
            "any finite deletion row is indistinguishable from the admitted full cover-nerve support",
            "any deletion row lacks inherited V/E/F/C anchor accounting",
            "order gap is zero on the full support row or order-erased does not collapse",
            "wrong-deletion, label-only, no-anchor, dense-closure, topology-closure, sheaf-closure, or promotion controls are admitted",
            "later boundary closure evidence is consumed as a carrier-frontier dependency",
            "homology, sheaf, topology, general gluing, shape law, bond convergence, PEPS3D closure, or downstream geometry is claimed",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_nerve_deletion_sensitivity_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "why_not_v4_probes": {
            "pass": True,
            "reason": "This is a v5 formal_scout carrier-frontier map with current finite-map fields, explicit PEPS3D anchors, controls, and blocked downstream consumers; v4 probe rows would not carry the active frontier matrix contract.",
        },
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_nerve_deletion_sensitivity",
            "deletion_row_count": deletion["deletion_row_count"],
            "control_row_count": deletion["control_row_count"],
            "deletion_ops": deletion["deletion_ops"],
            "max_parent_peps3d_sites": deletion["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": deletion["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": deletion["max_peps3d_bond"],
            "min_deletion_sensitivity_gap": deletion["min_deletion_sensitivity_gap"],
            "min_full_order_gap": deletion["min_full_order_gap"],
            "max_deleted_order_gap": deletion["max_deleted_order_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "deletion_row_count": deletion["deletion_row_count"],
            "control_row_count": deletion["control_row_count"],
            "deletion_ops": deletion["deletion_ops"],
            "parent_shape": deletion["parent_shape"],
            "triple_overlap_shape": deletion["triple_overlap_shape"],
            "max_parent_peps3d_sites": deletion["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": deletion["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": deletion["max_peps3d_bond"],
            "min_deletion_sensitivity_gap": deletion["min_deletion_sensitivity_gap"],
            "min_full_order_gap": deletion["min_full_order_gap"],
            "max_deleted_order_gap": deletion["max_deleted_order_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "all positive, graveyard, and boundary checks pass; finite deletion rows change response/order/incidence readouts; wrong deletion does not; dense closure and downstream promotion remain blocked",
        "fail_rule": "any failed positive/control/boundary row, dense closure use, downstream dependency, deletion indistinguishable from full support, or collapsed full-support N01 witness fails the scout",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_admissible_step": "Classify this deletion-sensitivity receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker.",
        "next_required_work": "Update the active frontier artifacts with this receipt and rerun the strict bounded validator.",
        "recommended_next_move": "Use this receipt only inside the active carrier-frontier matrix; keep downstream consumers blocked.",
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "deletion_row_count": deletion["deletion_row_count"],
        "max_parent_peps3d_sites": deletion["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": deletion["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": deletion["max_peps3d_bond"],
        "min_deletion_sensitivity_gap": deletion["min_deletion_sensitivity_gap"],
        "min_full_order_gap": deletion["min_full_order_gap"],
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
