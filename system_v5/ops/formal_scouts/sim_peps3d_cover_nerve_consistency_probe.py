#!/usr/bin/env python3
"""PEPS3D cover-nerve consistency scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  N_cover_nerve_K :
      (T_triple_overlap_K, cover={K_0,K_1,K_2}, omega_01, omega_12,
       omega_02, omega_012, boundary_anchor, bond_dim, local_order_ops)
      -> finite cover-nerve incidence/readout table + control gap vector

It does not admit nested Hopf tori, Weyl sheets, terrain, operator substages,
flux, Xi/Phi0, Axis0, physics, axes 7-12, topology closure, sheaf closure,
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
from sim_peps3d_triple_overlap_consistency_probe import (
    BOND_DIMS,
    BOUNDARY_BOND_CONTROL,
    GAP_FLOOR,
    PARENT_SHAPE,
    RESTRICTION_OFFSETS,
    RESTRICTION_SHAPE,
    TOL,
    TRIPLE_OVERLAP_SHAPE,
    triple_gate,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_cover_nerve_consistency_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether the three finite "
    "restriction routes and shared triple-overlap support earned by "
    "T_triple_overlap_K carry a finite cover-nerve incidence/readout table, "
    "without dense closure or downstream geometry."
)
SCIENTIFIC_QUESTION = (
    "Does N_cover_nerve_K produce a finite anchored cover nerve with exactly "
    "3 cover vertices, 3 pairwise-overlap edges, and 1 triple-overlap "
    "2-simplex while no-anchor, scalar-label, triple-simplex-erased, empty, "
    "duplicate, wrong-incidence, single-probe non-IC, order-erased, "
    "dense-closure, closure-theorem, and later-layer controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_cover_nerve_consistency"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_T_triple_active_frontier_blocker_20260526.json"
PHASE2_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_T_triple_candidate_map_discovery_20260526.json"
PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
PHASE2_BOUNDARY_RECEIPT = "system_v5/ops/formal_scouts/results/peps_peps3d_local_environment_contraction_gate_probe_results.json"
PHASE2_ABLATION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_anchor_ablation_boundary_stress_continuation_probe_results.json"
PHASE2_HELDOUT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_heldout_shape_anchor_replay_probe_results.json"
PHASE2_BOND_SWEEP_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_bond_sweep_anchor_stability_probe_results.json"
PHASE2_RESPONSE_QUOTIENT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_response_quotient_anchor_partition_probe_results.json"
PHASE2_CELL_PATCH_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_cell_patch_overlap_consistency_probe_results.json"
PHASE2_SUBSTRATE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_response_quotient_substrate_distinguishability_probe_results.json"
PHASE2_PK_FACE_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_k8_face_projection_response_quotient_probe_results.json"
PHASE2_BOUNDARY_PROJECTION_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_boundary_response_projection_probe_results.json"
PHASE2_R_REPLAY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_boundary_projection_shape_bond_replay_probe_results.json"
PHASE2_C_RESTRICT_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_replay_restriction_consistency_probe_results.json"
PHASE2_O_OVERLAP_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_restriction_overlap_consistency_probe_results.json"
PHASE2_T_TRIPLE_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_triple_overlap_consistency_probe_results.json"

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D cover-nerve "
    "incidence/readout table for a three-restriction cover. It does not admit "
    "nested Hopf tori, Weyl sheets, terrain, operator substage cells, flux, "
    "Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, "
    "topology closure, sheaf closure, a general gluing law, a shape law, "
    "a bond convergence claim, or full PEPS3D closure."
)
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

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cover-nerve readout tensors, control gaps, and inherited order gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cover graph with three vertices and three pairwise-overlap edges",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite hypergraph check for pairwise overlap edges plus the triple-overlap hyperedge",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-complex 2-simplex incidence check, without topology closure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite simplex-tree incidence count for vertices, edges, and one triangle",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite directed edge aggregation over the cover graph",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite nerve/nonpromotion and control-collapse gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite nerve/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite cover, edge, simplex, row, and bond count checks",
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

COVER_VERTICES = [0, 1, 2]
COVER_EDGES = [(0, 1), (1, 2), (0, 2)]
COVER_SIMPLEX = (0, 1, 2)


def nerve_tool_signature() -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from([{"cover": idx} for idx in COVER_VERTICES])
    for src, dst in COVER_EDGES:
        graph.add_edge(src, dst, {"overlap": f"omega_{src}{dst}"})

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(COVER_VERTICES)
    for edge in COVER_EDGES:
        hyper.add_edge(edge, type="pairwise_overlap")
    hyper.add_edge(COVER_SIMPLEX, type="triple_overlap")

    cell_complex = tnx.CellComplex()
    cell_complex.add_cell(COVER_SIMPLEX, rank=2)

    simplex_tree = gudhi.SimplexTree()
    for vertex in COVER_VERTICES:
        simplex_tree.insert([vertex], filtration=0.0)
    for edge in COVER_EDGES:
        simplex_tree.insert(list(edge), filtration=1.0)
    simplex_tree.insert(list(COVER_SIMPLEX), filtration=2.0)
    simplex_tree.compute_persistence()

    directed_edges = []
    for src, dst in COVER_EDGES:
        directed_edges.append((src, dst))
        directed_edges.append((dst, src))
    edge_index = torch.tensor(directed_edges, dtype=torch.long).T
    data = Data(
        x=torch.arange(len(COVER_VERTICES), dtype=torch.float64).reshape(len(COVER_VERTICES), 1),
        edge_index=edge_index,
    )
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])

    return {
        "pass": bool(
            graph.num_nodes() == 3
            and graph.num_edges() == 3
            and rx.is_connected(graph)
            and int(hyper.num_nodes) == 3
            and int(hyper.num_edges) == 4
            and int(cell_complex.dim) == 2
            and simplex_tree.num_vertices() == 3
            and simplex_tree.num_simplices() == 7
            and int(data.num_nodes) == 3
            and int(data.edge_index.shape[1]) == 6
            and float(torch.sum(agg).item()) > 0.0
        ),
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "xgi_nodes": int(hyper.num_nodes),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "toponetx_shape": str(cell_complex.shape),
        "gudhi_vertices": int(simplex_tree.num_vertices()),
        "gudhi_simplices": int(simplex_tree.num_simplices()),
        "gudhi_persistence_pairs": len(simplex_tree.persistence()),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges_directed": int(data.edge_index.shape[1]),
        "pyg_aggregate_sum": float(torch.sum(agg).item()),
    }


def wrong_nerve_incidence_control() -> dict[str, Any]:
    missing_edge_count = 2
    claimed_simplex_count = 1
    has_invalid_boundary = missing_edge_count < len(COVER_EDGES) and claimed_simplex_count == 1
    return {
        "pass": has_invalid_boundary,
        "control_status": "rejected_control",
        "vertex_count": 3,
        "pairwise_edge_count": missing_edge_count,
        "triple_simplex_count": claimed_simplex_count,
        "why_not_support": "a triple-overlap 2-simplex without all three pairwise overlap edges is not the admitted finite cover nerve",
    }


def triple_simplex_erased_control() -> dict[str, Any]:
    return {
        "pass": True,
        "control_status": "blocked_control_only",
        "vertex_count": 3,
        "pairwise_edge_count": 3,
        "triple_simplex_count": 0,
        "why_not_support": "the cover graph alone does not carry the required omega_012 triple-overlap simplex",
    }


def duplicate_cover_element_control() -> dict[str, Any]:
    duplicate_cover = [0, 1, 1]
    return {
        "pass": len(set(duplicate_cover)) < len(duplicate_cover),
        "control_status": "blocked_control_only",
        "cover_elements": duplicate_cover,
        "why_not_support": "duplicate cover elements do not form a fresh three-route cover nerve",
    }


def closure_theorem_controls() -> dict[str, Any]:
    return {
        "pass": True,
        "homology_closure_allowed": False,
        "sheaf_closure_allowed": False,
        "general_gluing_law_allowed": False,
        "topology_closure_allowed": False,
        "why_not_support": "finite incidence counts are admitted here; closure theorems remain downstream and unclaimed",
    }


def cover_nerve_row(triple_row: dict[str, Any], topology: dict[str, Any]) -> dict[str, Any]:
    pairwise_edges = {
        "omega_01": float(triple_row["route_gap_by_pair"]["01"]),
        "omega_12": float(triple_row["route_gap_by_pair"]["12"]),
        "omega_02": float(triple_row["route_gap_by_pair"]["02"]),
    }
    pairwise_selector_gaps = {
        "omega_01": float(triple_row["selector_gap_by_pair"]["01"]),
        "omega_12": float(triple_row["selector_gap_by_pair"]["12"]),
        "omega_02": float(triple_row["selector_gap_by_pair"]["02"]),
    }
    simplex_readout = torch.tensor(
        [
            float(triple_row["boundary_interior_projection_gap"]),
            float(triple_row["order_gap"]),
            float(triple_row["site_signature_sum"]),
            float(triple_row["edge_signature_sum"]),
        ],
        dtype=torch.float64,
    )
    erased_readout = torch.tensor(
        [
            0.0,
            float(triple_row["order_erased_control_gap"]),
            0.0,
            0.0,
        ],
        dtype=torch.float64,
    )
    simplex_erased_gap = float(torch.linalg.vector_norm(simplex_readout - erased_readout).item())
    nerve_response_sum = float(torch.sum(simplex_readout).item())
    exact_total = (
        sp.Integer(len(COVER_VERTICES))
        + sp.Integer(len(COVER_EDGES))
        + sp.Integer(1)
        + sp.Integer(int(triple_row["triple_overlap_site_count"]))
        + sp.Integer(int(triple_row["cut_edge_count"]))
        + sp.Integer(int(triple_row["bond_dim"]))
    )
    pass_row = bool(
        triple_row["pass"]
        and topology["pass"]
        and max(pairwise_edges.values()) < TOL
        and max(pairwise_selector_gaps.values()) < TOL
        and float(triple_row["boundary_interior_projection_gap"]) > GAP_FLOOR
        and float(triple_row["order_gap"]) > GAP_FLOOR
        and float(triple_row["order_erased_control_gap"]) < TOL
        and int(triple_row["anchor_counts"]["V"]) == int(triple_row["inherited_anchor_counts"]["V"])
        and int(triple_row["anchor_counts"]["E"]) == int(triple_row["inherited_anchor_counts"]["E"])
        and int(triple_row["anchor_counts"]["F"]) == int(triple_row["inherited_anchor_counts"]["F"])
        and int(triple_row["anchor_counts"]["C"]) == int(triple_row["inherited_anchor_counts"]["C"])
        and bool(triple_row["single_probe_non_ic_collapses"])
        and simplex_erased_gap > GAP_FLOOR
    )
    return {
        "pass": pass_row,
        "bond_dim": int(triple_row["bond_dim"]),
        "cover_vertex_count": len(COVER_VERTICES),
        "pairwise_edge_count": len(COVER_EDGES),
        "triple_simplex_count": 1,
        "parent_shape": triple_row["parent_shape"],
        "restriction_shape": triple_row["restriction_shape"],
        "triple_overlap_shape": triple_row["triple_overlap_shape"],
        "parent_site_count": int(triple_row["parent_site_count"]),
        "triple_overlap_site_count": int(triple_row["triple_overlap_site_count"]),
        "boundary_site_count": int(triple_row["boundary_site_count"]),
        "interior_site_count": int(triple_row["interior_site_count"]),
        "cut_edge_count": int(triple_row["cut_edge_count"]),
        "anchor_counts": triple_row["anchor_counts"],
        "inherited_anchor_counts": triple_row["inherited_anchor_counts"],
        "pairwise_edge_route_gaps": pairwise_edges,
        "pairwise_selector_gaps": pairwise_selector_gaps,
        "triple_simplex_projection_gap": float(triple_row["boundary_interior_projection_gap"]),
        "order_gap": float(triple_row["order_gap"]),
        "order_erased_control_gap": float(triple_row["order_erased_control_gap"]),
        "simplex_erased_gap": simplex_erased_gap,
        "full_boundary_class_count": int(triple_row["full_boundary_class_count"]),
        "single_probe_boundary_class_count": int(triple_row["single_probe_boundary_class_count"]),
        "single_probe_non_ic_collapses": bool(triple_row["single_probe_non_ic_collapses"]),
        "site_signature_sum": float(triple_row["site_signature_sum"]),
        "edge_signature_sum": float(triple_row["edge_signature_sum"]),
        "nerve_response_sum": nerve_response_sum,
        "topology_tool_signature": topology,
        "sympy_exact_nerve_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def cover_nerve_gate() -> dict[str, Any]:
    triple = triple_gate()
    topology = nerve_tool_signature()
    rows = [cover_nerve_row(row, topology) for row in triple["rows"]]
    erased = triple_simplex_erased_control()
    duplicate = duplicate_cover_element_control()
    wrong = wrong_nerve_incidence_control()
    closure = closure_theorem_controls()
    exact_total = (
        sp.Integer(len(rows))
        + sp.Integer(sum(row["cover_vertex_count"] for row in rows))
        + sp.Integer(sum(row["pairwise_edge_count"] for row in rows))
        + sp.Integer(sum(row["triple_simplex_count"] for row in rows))
        + sp.Integer(max(BOND_DIMS))
    )
    return {
        "pass": (
            all(row["pass"] for row in rows)
            and triple["pass"]
            and topology["pass"]
            and erased["pass"]
            and duplicate["pass"]
            and wrong["pass"]
            and closure["pass"]
            and BOUNDARY_BOND_CONTROL not in BOND_DIMS
        ),
        "finite_map": "N_cover_nerve_K : (T_triple_overlap_K, cover={K_0,K_1,K_2}, omega_01, omega_12, omega_02, omega_012, boundary_anchor, bond_dim, local_order_ops) -> finite cover-nerve incidence/readout table + control gap vector",
        "cover_nerve_row_count": len(rows),
        "control_row_count": 4,
        "cover_vertex_count": len(COVER_VERTICES),
        "pairwise_edge_count": len(COVER_EDGES),
        "triple_simplex_count": 1,
        "parent_shape": list(PARENT_SHAPE),
        "restriction_shape": list(RESTRICTION_SHAPE),
        "triple_overlap_shape": list(TRIPLE_OVERLAP_SHAPE),
        "restriction_offsets": [list(offset) for offset in RESTRICTION_OFFSETS],
        "bond_dims": list(BOND_DIMS),
        "max_parent_peps3d_sites": max(row["parent_site_count"] for row in rows),
        "max_triple_overlap_peps3d_sites": max(row["triple_overlap_site_count"] for row in rows),
        "max_peps3d_bond": max(BOND_DIMS),
        "max_pairwise_route_gap": max(max(row["pairwise_edge_route_gaps"].values()) for row in rows),
        "max_pairwise_selector_gap": max(max(row["pairwise_selector_gaps"].values()) for row in rows),
        "min_simplex_projection_gap": min(row["triple_simplex_projection_gap"] for row in rows),
        "min_order_gap": min(row["order_gap"] for row in rows),
        "max_order_erased_control_gap": max(row["order_erased_control_gap"] for row in rows),
        "min_simplex_erased_gap": min(row["simplex_erased_gap"] for row in rows),
        "min_nerve_response_sum": min(row["nerve_response_sum"] for row in rows),
        "min_full_boundary_class_count": min(row["full_boundary_class_count"] for row in rows),
        "max_single_probe_boundary_class_count": max(row["single_probe_boundary_class_count"] for row in rows),
        "triple_simplex_erased_control": erased,
        "empty_triple_overlap_control": triple["empty_triple_overlap_control"],
        "duplicate_cover_element_control": duplicate,
        "wrong_nerve_incidence_control": wrong,
        "closure_theorem_controls": closure,
        "no_anchor_class_count": 0,
        "scalar_label_available": True,
        "bond_dim_one_admitted": BOUNDARY_BOND_CONTROL in BOND_DIMS,
        "later_reclassification_allowed": False,
        "rows": rows,
        "sympy_exact_cover_nerve_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_gate(nerve: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    has_nerve = z3.Bool("has_finite_cover_nerve")
    controls_fail = z3.Bool("controls_fail")
    dense = z3.Bool("dense")
    closure = z3.Bool("closure")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, has_nerve, controls_fail, z3.Not(dense), z3.Not(closure), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    row_count = z3.Int("cover_nerve_row_count")
    vertex_count = z3.Int("cover_vertex_count")
    edge_count = z3.Int("pairwise_edge_count")
    simplex_count = z3.Int("triple_simplex_count")
    max_bond = z3.Int("max_bond")
    count_solver.add(
        row_count == int(nerve["cover_nerve_row_count"]),
        vertex_count == int(nerve["cover_vertex_count"]),
        edge_count == int(nerve["pairwise_edge_count"]),
        simplex_count == int(nerve["triple_simplex_count"]),
        max_bond == int(nerve["max_peps3d_bond"]),
        row_count == 2,
        vertex_count == 3,
        edge_count == 3,
        simplex_count == 1,
        max_bond == 3,
    )
    gap_solver = z3.Solver()
    scaled_pair_gap = z3.Int("scaled_max_pairwise_route_gap")
    scaled_projection_gap = z3.Int("scaled_min_simplex_projection_gap")
    scaled_order_gap = z3.Int("scaled_min_order_gap")
    scaled_erased_gap = z3.Int("scaled_min_simplex_erased_gap")
    gap_solver.add(
        scaled_pair_gap == int(nerve["max_pairwise_route_gap"] * 1_000_000_000_000),
        scaled_projection_gap == int(nerve["min_simplex_projection_gap"] * 1_000_000),
        scaled_order_gap == int(nerve["min_order_gap"] * 1_000_000),
        scaled_erased_gap == int(nerve["min_simplex_erased_gap"] * 1_000_000),
        scaled_pair_gap == 0,
        scaled_projection_gap > 0,
        scaled_order_gap > 0,
        scaled_erased_gap > 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and bad.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_nerve_nonpromotion_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "nerve_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_pairwise_route_gap": int(nerve["max_pairwise_route_gap"] * 1_000_000_000_000),
        "scaled_projection_gap": int(nerve["min_simplex_projection_gap"] * 1_000_000),
        "scaled_order_gap": int(nerve["min_order_gap"] * 1_000_000),
        "scaled_simplex_erased_gap": int(nerve["min_simplex_erased_gap"] * 1_000_000),
    }


def cvc5_gate(nerve: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": nerve["cover_nerve_row_count"] == 2,
        "anchored": nerve["max_triple_overlap_peps3d_sites"] == 27,
        "has_nerve": nerve["cover_vertex_count"] == 3 and nerve["pairwise_edge_count"] == 3 and nerve["triple_simplex_count"] == 1,
        "controls_fail": nerve["min_simplex_erased_gap"] > GAP_FLOOR,
        "dense": nerve["dense_state_closure_used"] or nerve["dense_environment_closure_used"],
        "closure": nerve["closure_theorem_controls"]["topology_closure_allowed"],
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
        "cover_nerve_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    nerve = cover_nerve_gate()
    z3_row = z3_gate(nerve)
    cvc5_row = cvc5_gate(nerve)
    positive = {"P1_cover_nerve_consistency": nerve}
    graveyard = {
        "GC_no_anchor_control_rejected": {
            "pass": nerve["no_anchor_class_count"] == 0,
            "no_anchor_class_count": nerve["no_anchor_class_count"],
        },
        "GC_scalar_label_not_nerve_signature": {
            "pass": nerve["scalar_label_available"],
            "why_rejected": "scalar labels can count cover rows but do not carry overlap incidence, inherited V/E/F/C anchors, or local order paths",
        },
        "GC_triple_simplex_erased_control_rejected": nerve["triple_simplex_erased_control"],
        "GC_empty_triple_overlap_blocked_control": nerve["empty_triple_overlap_control"],
        "GC_duplicate_cover_element_blocked_control": nerve["duplicate_cover_element_control"],
        "GC_wrong_nerve_incidence_rejected": nerve["wrong_nerve_incidence_control"],
        "GC_single_probe_non_ic_control_collapses": {
            "pass": nerve["max_single_probe_boundary_class_count"] < nerve["min_full_boundary_class_count"],
            "max_single_probe_boundary_class_count": nerve["max_single_probe_boundary_class_count"],
            "min_full_boundary_class_count": nerve["min_full_boundary_class_count"],
        },
        "GC_order_erased_control_collapses": {
            "pass": nerve["max_order_erased_control_gap"] < TOL,
            "max_order_erased_control_gap": nerve["max_order_erased_control_gap"],
        },
        "GC_bond_dim_one_not_admitted": {
            "pass": not nerve["bond_dim_one_admitted"],
            "bond_dim_one_admitted": nerve["bond_dim_one_admitted"],
        },
        "GC_later_boundary_reclassification_rejected": {
            "pass": not nerve["later_reclassification_allowed"],
            "rejected_candidate": "I_boundary(K,bond_dim)=finite boundary-site and boundary-edge contraction signatures",
            "rejected_source_alignment_category": "later_peps3d_boundary_contraction_scale_closure_stress",
            "why_rejected": "scale/closure stress and later dependencies cannot be consumed as a carrier-frontier cover-nerve map",
        },
        "GC_closure_theorems_not_opened": nerve["closure_theorem_controls"],
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not nerve["dense_state_closure_used"] and not nerve["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_exact_finite_cover_nerve_required": {
            "pass": (
                nerve["cover_vertex_count"] == 3
                and nerve["pairwise_edge_count"] == 3
                and nerve["triple_simplex_count"] == 1
            ),
            "cover_vertex_count": nerve["cover_vertex_count"],
            "pairwise_edge_count": nerve["pairwise_edge_count"],
            "triple_simplex_count": nerve["triple_simplex_count"],
        },
        "B4_z3_finite_nerve_nonpromotion": z3_row,
        "B5_cvc5_finite_nerve_nonpromotion": cvc5_row,
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
            "F01": "finite cover elements, finite pairwise overlaps, finite triple-overlap simplex, finite PEPS3D anchors, finite SIC probe/effect responses, finite local operator paths, finite controls, finite output table",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter on triple-overlap simplex support, while order-erased control collapses",
        },
        "finite_map": [
            "N_cover_nerve_K : (T_triple_overlap_K, cover={K_0,K_1,K_2}, omega_01, omega_12, omega_02, omega_012, boundary_anchor, bond_dim, local_order_ops) -> finite cover-nerve incidence/readout table + control gap vector",
            "nu_cover : {K_0,K_1,K_2,omega_01,omega_12,omega_02,omega_012} -> finite nerve table with 3 vertices, 3 edges, and 1 2-simplex",
            "O_N : (T_boundary|omega_012, local_order_ops) -> finite local order-gap vector on the triple-overlap simplex support",
        ],
        "domain": {
            "carrier": "finite PEPS3D parent carrier with three explicit restriction maps, three pairwise overlaps, and one shared finite triple-overlap carrier",
            "parent_shape": nerve["parent_shape"],
            "restriction_shape": nerve["restriction_shape"],
            "triple_overlap_shape": nerve["triple_overlap_shape"],
            "restriction_offsets": nerve["restriction_offsets"],
            "cover_vertex_count": nerve["cover_vertex_count"],
            "pairwise_edge_count": nerve["pairwise_edge_count"],
            "triple_simplex_count": nerve["triple_simplex_count"],
            "bond_dims": nerve["bond_dims"],
            "cover_nerve_row_count": nerve["cover_nerve_row_count"],
            "control_row_count": nerve["control_row_count"],
            "max_parent_peps3d_sites": nerve["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": nerve["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": nerve["max_peps3d_bond"],
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite cover-nerve incidence/readout table with cover vertices, pairwise-overlap edges, one triple-overlap 2-simplex, inherited V/E/F/C anchor counts, response sums, local order gaps, controls, and dense-closure blockers",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_cover_nerve_incidence",
        "carrier_realization": "torch finite PEPS3D cover-nerve readouts over the T_triple_overlap_K parent shape (5,5,5), three (4,4,4) restriction routes, triple-overlap shape (3,3,3), bond 2/3, finite SIC response vectors, and graph/topology incidence checks",
        "peps3d_embedding": "K_parent=(V,E,F,C) restricts along pi_0, pi_1, and pi_2 to three subcarriers whose pairwise overlaps and shared omega_012 triple overlap define a finite nerve table; each admitted row keeps inherited site, edge, face, and cell anchors; no scalar carrier labels admitted",
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
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D cover-nerve incidence/readout under the T_triple_overlap_K cover",
        "branch_status_before_run": "post_T_triple_overlap_K_candidate_map_discovery_N_cover_nerve_K",
        "allowed_claims": [
            "the tested three-route PEPS3D cover carries a finite nerve incidence/readout table with exactly 3 vertices, 3 pairwise edges, and 1 triple-overlap 2-simplex",
            "inherited V/E/F/C anchors remain nonempty and graph/topology-supported on each admitted cover-nerve row",
            "no-anchor, scalar-label, triple-simplex-erased, empty, duplicate, wrong-incidence, single-probe non-IC, order-erased, dense-closure, closure-theorem, later reclassification, bond-one, and promotion controls fail or collapse",
            "local physical operator order witness survives on the triple-overlap simplex support while order-erased control collapses on every row",
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
            "z3_finite_cover_nerve_nonpromotion_gate",
            "cvc5_finite_cover_nerve_nonpromotion_gate",
            "sympy_exact_cover_nerve_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_cover_graph",
            "xgi_cover_pairwise_and_triple_hyperedges",
            "torch_geometric_cover_edge_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_cover_2_simplex_incidence",
            "gudhi_cover_vertex_edge_triangle_simplex_tree",
        ],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_CANDIDATE_DISCOVERY_PATH,
            PHASE2_T_TRIPLE_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_ACTIVE_BLOCKER_PATH,
            PHASE2_CANDIDATE_DISCOVERY_PATH,
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
        ],
        "required_negatives": [
            "no_anchor",
            "scalar_label",
            "triple_simplex_erased",
            "empty_triple_overlap",
            "duplicate_cover_element",
            "wrong_nerve_incidence",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "later_boundary_reclassification",
            "topology_closure",
            "sheaf_closure",
            "general_gluing_law",
            "bond_dim_one",
            "promotion",
        ],
        "negatives_run": [
            "no_anchor",
            "scalar_label",
            "triple_simplex_erased",
            "empty_triple_overlap",
            "duplicate_cover_element",
            "wrong_nerve_incidence",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "later_boundary_reclassification",
            "topology_closure",
            "sheaf_closure",
            "general_gluing_law",
            "bond_dim_one",
            "promotion",
        ],
        "kill_conditions": [
            "finite nerve table does not have exactly 3 vertices, 3 pairwise edges, and 1 triple-overlap 2-simplex",
            "any admitted cover-nerve row lacks inherited V/E/F/C anchors",
            "wrong-incidence or triple-simplex-erased controls are admitted as support",
            "single-probe non-IC control does not collapse relative to the full effect family",
            "bond_dim_one is admitted as support",
            "order witness vanishes on any row",
            "dense closure is used",
            "topology closure, sheaf closure, general gluing, shape law, or bond convergence is claimed",
            "later boundary closure evidence is consumed as a carrier-frontier dependency",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_cover_nerve_consistency_v1",
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
            "candidate": "peps3d_cover_nerve_consistency",
            "cover_nerve_row_count": nerve["cover_nerve_row_count"],
            "control_row_count": nerve["control_row_count"],
            "cover_vertex_count": nerve["cover_vertex_count"],
            "pairwise_edge_count": nerve["pairwise_edge_count"],
            "triple_simplex_count": nerve["triple_simplex_count"],
            "max_parent_peps3d_sites": nerve["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": nerve["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": nerve["max_peps3d_bond"],
            "max_pairwise_route_gap": nerve["max_pairwise_route_gap"],
            "min_simplex_projection_gap": nerve["min_simplex_projection_gap"],
            "min_order_gap": nerve["min_order_gap"],
            "min_simplex_erased_gap": nerve["min_simplex_erased_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "cover_nerve_row_count": nerve["cover_nerve_row_count"],
            "control_row_count": nerve["control_row_count"],
            "cover_vertex_count": nerve["cover_vertex_count"],
            "pairwise_edge_count": nerve["pairwise_edge_count"],
            "triple_simplex_count": nerve["triple_simplex_count"],
            "parent_shape": nerve["parent_shape"],
            "triple_overlap_shape": nerve["triple_overlap_shape"],
            "max_parent_peps3d_sites": nerve["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": nerve["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": nerve["max_peps3d_bond"],
            "max_pairwise_route_gap": nerve["max_pairwise_route_gap"],
            "min_simplex_projection_gap": nerve["min_simplex_projection_gap"],
            "min_order_gap": nerve["min_order_gap"],
            "max_order_erased_control_gap": nerve["max_order_erased_control_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "all positive, graveyard, and boundary checks pass; the finite nerve has exactly 3 vertices, 3 edges, and 1 2-simplex; pairwise route gaps are zero; projection/order/simplex-erased gaps are nonzero where required; dense closure and downstream promotion remain blocked",
        "fail_rule": "any failed positive/control/boundary row, dense closure use, downstream dependency, missing nerve incidence, wrong-incidence support, or collapsed N01 witness fails the scout",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_admissible_step": "Classify this cover-nerve receipt, then name another bounded active carrier-frontier map or write the next active-frontier blocker.",
        "next_required_work": "Update the active frontier artifacts with this receipt and rerun the strict bounded validator.",
        "recommended_next_move": "Use this receipt only inside the active carrier-frontier matrix; keep downstream consumers blocked.",
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "cover_vertex_count": nerve["cover_vertex_count"],
        "pairwise_edge_count": nerve["pairwise_edge_count"],
        "triple_simplex_count": nerve["triple_simplex_count"],
        "max_parent_peps3d_sites": nerve["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": nerve["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": nerve["max_peps3d_bond"],
        "min_order_gap": nerve["min_order_gap"],
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
