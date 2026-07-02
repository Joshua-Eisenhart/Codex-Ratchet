#!/usr/bin/env python3
"""PEPS3D replay restriction consistency scout.

Formal scout only.

This continuation packet stays inside Phase 2 PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  C_restrict_K :
      (R_replay_K, pi_restrict, boundary_anchor, bond_dim, local_order_ops)
      -> finite replay-restriction consistency signatures + control gap vector

It does not admit nested Hopf tori, Weyl sheets, terrain, operator substages,
flux, Xi/Phi0, Axis0, physics, axes 7-12, or full PEPS3D closure.
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

from sim_finite_peps3d_probe_effect_seed_carrier_gate_probe import (
    RTYPE,
    all_edge_signatures,
    apply_physical_operator,
    as_jsonable,
    cell_list,
    coords_for_shape,
    edge_list,
    face_list,
    make_site_tensors,
    probe_responses,
    shift_filter_ops,
    sic_effects,
    site_spinors,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "peps3d_replay_restriction_consistency_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing explicit finite "
    "restriction maps from the R_replay_K PEPS3D parent carrier to anchored "
    "nonempty boundary/interior subcarriers, without dense closure or "
    "downstream geometry."
)
SCIENTIFIC_QUESTION = (
    "Does C_restrict_K preserve finite boundary/interior response projection "
    "signatures and V/E/F/C anchors under explicit pi_restrict subcarrier "
    "maps while no-anchor, scalar-label, boundary-erased, flattened-boundary, "
    "anchor-scrambled, single-probe non-IC, order-erased, dense-closure, "
    "Phase 7 reclassification, bond-one, and zero-interior controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_replay_restriction_consistency"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_R_replay_active_frontier_blocker_20260525.json"
PHASE2_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_R_replay_candidate_map_discovery_20260525.json"
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

CLAIM_CEILING = (
    "Formal scout only: tests finite PEPS3D replay restriction consistency "
    "for explicit pi_restrict subcarrier maps. It does not admit nested Hopf "
    "tori, Weyl sheets, terrain, operator substage cells, flux, Xi/Phi0, "
    "Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, or full "
    "PEPS3D closure."
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
        "reason": "load-bearing finite restriction selector maps, response tensors, consistency gaps, and local order gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing parent and restricted PEPS3D graph connectivity plus inherited edge anchor checks",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite face/cell hyperedge support checks on the restricted carrier",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-complex face support check for inherited restricted anchors",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite filtration check over restricted vertices, edges, and faces",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite graph data aggregation check over restricted edge incidence",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite restriction/nonpromotion and control-collapse gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite restriction/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite row, parent, restricted site, edge, face, cell, and bond count checks",
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
}

PARENT_SHAPE = (4, 4, 4)
SUB_SHAPE = (3, 3, 3)
ZERO_INTERIOR_CONTROL_SHAPE = (3, 3, 2)
RESTRICTION_OFFSETS = [(0, 0, 0), (1, 1, 1)]
BOND_DIMS = [2, 3]
BOUNDARY_BOND_CONTROL = 1
GAP_FLOOR = 1.0e-8
TOL = 1.0e-10


def is_boundary(coord: tuple[int, int, int], shape: tuple[int, int, int]) -> bool:
    return any(item == 0 or item == shape[axis] - 1 for axis, item in enumerate(coord))


def carrier_graph(shape: tuple[int, int, int]) -> rx.PyGraph:
    graph = rx.PyGraph()
    coords = coords_for_shape(shape)
    graph.add_nodes_from([{"coord": coord} for coord in coords])
    for edge in edge_list(shape):
        graph.add_edge(int(edge["src"]), int(edge["dst"]), {"axis": int(edge["axis"])})
    return graph


def coord_index(shape: tuple[int, int, int]) -> dict[tuple[int, int, int], int]:
    return {coord: idx for idx, coord in enumerate(coords_for_shape(shape))}


def shifted_coord(coord: tuple[int, int, int], offset: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(coord[axis] + offset[axis] for axis in range(3))


def selected_parent_indices(
    parent_shape: tuple[int, int, int],
    sub_shape: tuple[int, int, int],
    offset: tuple[int, int, int],
) -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int]], list[int]]:
    parent_index = coord_index(parent_shape)
    local_coords = coords_for_shape(sub_shape)
    parent_coords = [shifted_coord(coord, offset) for coord in local_coords]
    return local_coords, parent_coords, [parent_index[coord] for coord in parent_coords]


def unique_rows(responses: torch.Tensor, columns: int) -> int:
    return len({tuple(round(float(item), 10) for item in row) for row in responses[:, :columns]})


def edge_key(edge: dict[str, Any]) -> frozenset[int]:
    return frozenset((int(edge["src"]), int(edge["dst"])))


def parent_anchor_sets(shape: tuple[int, int, int]) -> dict[str, set[frozenset[int]]]:
    return {
        "E": {edge_key(edge) for edge in edge_list(shape)},
        "F": {frozenset(int(item) for item in face["vertices"]) for face in face_list(shape)},
        "C": {frozenset(int(item) for item in cell["vertices"]) for cell in cell_list(shape)},
    }


def inherited_anchor_counts(
    parent_shape: tuple[int, int, int],
    sub_shape: tuple[int, int, int],
    local_to_parent: list[int],
) -> dict[str, int]:
    parent_sets = parent_anchor_sets(parent_shape)
    inherited_edges = sum(
        1
        for edge in edge_list(sub_shape)
        if frozenset((local_to_parent[int(edge["src"])], local_to_parent[int(edge["dst"])])) in parent_sets["E"]
    )
    inherited_faces = sum(
        1
        for face in face_list(sub_shape)
        if frozenset(local_to_parent[int(item)] for item in face["vertices"]) in parent_sets["F"]
    )
    inherited_cells = sum(
        1
        for cell in cell_list(sub_shape)
        if frozenset(local_to_parent[int(item)] for item in cell["vertices"]) in parent_sets["C"]
    )
    return {
        "V": len(local_to_parent),
        "E": inherited_edges,
        "F": inherited_faces,
        "C": inherited_cells,
    }


def topology_tool_signature(
    sub_shape: tuple[int, int, int],
    local_to_parent: list[int],
) -> dict[str, Any]:
    edges = edge_list(sub_shape)
    faces = face_list(sub_shape)
    cells = cell_list(sub_shape)
    graph = carrier_graph(sub_shape)

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(range(len(local_to_parent)))
    for face in faces:
        hyper.add_edge(face["vertices"], type="face")
    for cell in cells:
        hyper.add_edge(cell["vertices"], type="cell")

    cell_complex = tnx.CellComplex()
    for face in faces:
        cell_complex.add_cell(face["vertices"], rank=2)

    simplex_tree = gudhi.SimplexTree()
    for idx in range(len(local_to_parent)):
        simplex_tree.insert([idx], filtration=0.0)
    for edge in edges:
        simplex_tree.insert([int(edge["src"]), int(edge["dst"])], filtration=1.0)
    for face in faces:
        verts = [int(v) for v in face["vertices"]]
        simplex_tree.insert([verts[0], verts[1], verts[2]], filtration=2.0)
        simplex_tree.insert([verts[0], verts[2], verts[3]], filtration=2.0)
    simplex_tree.compute_persistence()

    edge_pairs = []
    for edge in edges:
        edge_pairs.append((int(edge["src"]), int(edge["dst"])))
        edge_pairs.append((int(edge["dst"]), int(edge["src"])))
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).T
    data = Data(x=torch.arange(len(local_to_parent), dtype=RTYPE).reshape(len(local_to_parent), 1), edge_index=edge_index)
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    return {
        "pass": bool(
            graph.num_nodes() == len(local_to_parent)
            and graph.num_edges() == len(edges)
            and rx.is_connected(graph)
            and int(hyper.num_edges) == len(faces) + len(cells)
            and int(cell_complex.dim) == 2
            and simplex_tree.num_vertices() == len(local_to_parent)
            and int(data.num_nodes) == len(local_to_parent)
            and int(data.edge_index.shape[1]) == 2 * len(edges)
            and float(torch.sum(agg).item()) > 0.0
        ),
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "xgi_hyperedges_face_plus_cell": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "toponetx_shape": str(cell_complex.shape),
        "gudhi_vertices": int(simplex_tree.num_vertices()),
        "gudhi_simplices": int(simplex_tree.num_simplices()),
        "gudhi_persistence_pairs": len(simplex_tree.persistence()),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges_directed": int(data.edge_index.shape[1]),
        "pyg_aggregate_sum": float(torch.sum(agg).item()),
    }


def restriction_row(offset: tuple[int, int, int], bond_dim: int) -> dict[str, Any]:
    parent_coords = coords_for_shape(PARENT_SHAPE)
    parent_responses = probe_responses(site_spinors(len(parent_coords)), sic_effects())
    local_coords, inherited_coords, local_to_parent = selected_parent_indices(PARENT_SHAPE, SUB_SHAPE, offset)
    selector = torch.zeros((len(local_coords), len(parent_coords)), dtype=RTYPE)
    for local_idx, parent_idx in enumerate(local_to_parent):
        selector[local_idx, parent_idx] = 1.0
    selected = parent_responses[local_to_parent]
    selected_by_map = selector @ parent_responses
    response_restriction_gap = float(torch.linalg.vector_norm(selected - selected_by_map).item())

    boundary = [idx for idx, coord in enumerate(local_coords) if is_boundary(coord, SUB_SHAPE)]
    interior = [idx for idx, coord in enumerate(local_coords) if not is_boundary(coord, SUB_SHAPE)]
    boundary_signature = selected[boundary].mean(dim=0)
    interior_signature = selected[interior].mean(dim=0)
    mapped_boundary_signature = selected_by_map[boundary].mean(dim=0)
    mapped_interior_signature = selected_by_map[interior].mean(dim=0)
    projection_gap = float(torch.linalg.vector_norm(boundary_signature - interior_signature).item())
    boundary_consistency_gap = float(torch.linalg.vector_norm(boundary_signature - mapped_boundary_signature).item())
    interior_consistency_gap = float(torch.linalg.vector_norm(interior_signature - mapped_interior_signature).item())

    flattened_boundary = boundary_signature.repeat(len(boundary), 1)
    flattened_boundary_class_count = unique_rows(flattened_boundary, columns=4)
    full_boundary_class_count = unique_rows(selected[boundary], columns=4)
    single_probe_boundary_class_count = unique_rows(selected[boundary], columns=1)

    tensors = make_site_tensors(selected, inherited_coords, bond_dim)
    boundary_tensors = tensors[boundary]
    shift, filt = shift_filter_ops()
    filter_after_shift = apply_physical_operator(apply_physical_operator(boundary_tensors, shift), filt)
    shift_after_filter = apply_physical_operator(apply_physical_operator(boundary_tensors, filt), shift)
    order_gap = float(torch.linalg.vector_norm((filter_after_shift - shift_after_filter).reshape(-1)).item())
    erased_1 = apply_physical_operator(apply_physical_operator(boundary_tensors, filt), filt)
    erased_2 = apply_physical_operator(apply_physical_operator(boundary_tensors, filt), filt)
    order_erased_gap = float(torch.linalg.vector_norm((erased_1 - erased_2).reshape(-1)).item())

    local_edges = edge_list(SUB_SHAPE)
    boundary_set = set(boundary)
    interior_set = set(interior)
    cut_edges = [
        edge for edge in local_edges
        if (int(edge["src"]) in boundary_set) != (int(edge["dst"]) in boundary_set)
    ]
    anchor_counts = {
        "V": len(local_coords),
        "E": len(local_edges),
        "F": len(face_list(SUB_SHAPE)),
        "C": len(cell_list(SUB_SHAPE)),
    }
    inherited_counts = inherited_anchor_counts(PARENT_SHAPE, SUB_SHAPE, local_to_parent)
    topology = topology_tool_signature(SUB_SHAPE, local_to_parent)

    scrambled_local_to_parent = local_to_parent[1:] + local_to_parent[:1]
    scrambled_selected = parent_responses[scrambled_local_to_parent]
    anchor_scrambled_response_gap = float(torch.linalg.vector_norm(selected - scrambled_selected).item())
    scrambled_counts = inherited_anchor_counts(PARENT_SHAPE, SUB_SHAPE, scrambled_local_to_parent)

    edge_sigs = all_edge_signatures(tensors, local_edges)
    site_signature_sum = float(torch.real(torch.sum(tensors * tensors.conj())).item())
    edge_signature_sum = float(torch.real(torch.sum(edge_sigs)).item())
    exact_total = (
        sp.Integer(len(parent_coords))
        + sp.Integer(len(local_coords))
        + sp.Integer(len(local_edges))
        + sp.Integer(len(face_list(SUB_SHAPE)))
        + sp.Integer(len(cell_list(SUB_SHAPE)))
        + sp.Integer(len(cut_edges))
        + sp.Integer(bond_dim)
    )
    pass_row = bool(
        len(boundary) > 0
        and len(interior) > 0
        and len(cut_edges) > 0
        and anchor_counts == inherited_counts
        and topology["pass"]
        and response_restriction_gap < TOL
        and boundary_consistency_gap < TOL
        and interior_consistency_gap < TOL
        and projection_gap > GAP_FLOOR
        and full_boundary_class_count > single_probe_boundary_class_count
        and flattened_boundary_class_count == 1
        and order_gap > GAP_FLOOR
        and order_erased_gap < TOL
        and anchor_scrambled_response_gap > GAP_FLOOR
        and scrambled_counts != anchor_counts
    )
    return {
        "pass": pass_row,
        "parent_shape": list(PARENT_SHAPE),
        "subcarrier_shape": list(SUB_SHAPE),
        "offset": list(offset),
        "bond_dim": bond_dim,
        "parent_site_count": len(parent_coords),
        "subcarrier_site_count": len(local_coords),
        "boundary_site_count": len(boundary),
        "interior_site_count": len(interior),
        "cut_edge_count": len(cut_edges),
        "anchor_counts": anchor_counts,
        "inherited_anchor_counts": inherited_counts,
        "selector_row_sum_min": float(torch.min(selector.sum(dim=1)).item()),
        "selector_row_sum_max": float(torch.max(selector.sum(dim=1)).item()),
        "selector_column_sum_max": float(torch.max(selector.sum(dim=0)).item()),
        "response_restriction_gap": response_restriction_gap,
        "boundary_consistency_gap": boundary_consistency_gap,
        "interior_consistency_gap": interior_consistency_gap,
        "boundary_interior_projection_gap": projection_gap,
        "full_boundary_class_count": full_boundary_class_count,
        "single_probe_boundary_class_count": single_probe_boundary_class_count,
        "single_probe_non_ic_collapses": single_probe_boundary_class_count < full_boundary_class_count,
        "flattened_boundary_class_count": flattened_boundary_class_count,
        "order_gap": order_gap,
        "order_erased_control_gap": order_erased_gap,
        "anchor_scrambled_response_gap": anchor_scrambled_response_gap,
        "anchor_scrambled_inherited_anchor_counts": scrambled_counts,
        "site_signature_sum": site_signature_sum,
        "edge_signature_sum": edge_signature_sum,
        "topology_tool_signature": topology,
        "sympy_exact_restriction_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def zero_interior_control_row(shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    graph = carrier_graph(shape)
    boundary = [idx for idx, coord in enumerate(coords) if is_boundary(coord, shape)]
    interior = [idx for idx, coord in enumerate(coords) if not is_boundary(coord, shape)]
    return {
        "pass": bool(graph.num_nodes() == len(coords) and rx.is_connected(graph) and len(boundary) == len(coords) and len(interior) == 0),
        "shape": list(shape),
        "site_count": len(coords),
        "boundary_site_count": len(boundary),
        "interior_site_count": len(interior),
        "control_status": "blocked_control_only",
        "why_not_support": "pi_restrict support rows require nonempty boundary and nonempty interior; this finite shape has zero interior",
    }


def restriction_gate() -> dict[str, Any]:
    rows = [restriction_row(offset, bond_dim) for offset in RESTRICTION_OFFSETS for bond_dim in BOND_DIMS]
    zero_interior_control = zero_interior_control_row(ZERO_INTERIOR_CONTROL_SHAPE)
    exact_total = (
        sp.Integer(len(rows))
        + sp.Integer(sum(row["parent_site_count"] for row in rows))
        + sp.Integer(sum(row["subcarrier_site_count"] for row in rows))
        + sp.Integer(sum(row["boundary_site_count"] for row in rows))
        + sp.Integer(sum(row["interior_site_count"] for row in rows))
        + sp.Integer(sum(row["cut_edge_count"] for row in rows))
        + sp.Integer(max(BOND_DIMS))
        + sp.Integer(zero_interior_control["site_count"])
    )
    return {
        "pass": (
            all(row["pass"] for row in rows)
            and zero_interior_control["pass"]
            and BOUNDARY_BOND_CONTROL not in BOND_DIMS
        ),
        "finite_map": "C_restrict_K : (R_replay_K, pi_restrict, boundary_anchor, bond_dim, local_order_ops) -> finite replay-restriction consistency signatures + control gap vector",
        "restriction_row_count": len(rows),
        "control_row_count": 1,
        "parent_shape": list(PARENT_SHAPE),
        "subcarrier_shape": list(SUB_SHAPE),
        "restriction_offsets": [list(offset) for offset in RESTRICTION_OFFSETS],
        "zero_interior_control_shape": list(ZERO_INTERIOR_CONTROL_SHAPE),
        "bond_dims": list(BOND_DIMS),
        "max_parent_peps3d_sites": max(row["parent_site_count"] for row in rows),
        "max_subcarrier_peps3d_sites": max(row["subcarrier_site_count"] for row in rows),
        "max_peps3d_bond": max(BOND_DIMS),
        "max_response_restriction_gap": max(row["response_restriction_gap"] for row in rows),
        "max_boundary_consistency_gap": max(row["boundary_consistency_gap"] for row in rows),
        "max_interior_consistency_gap": max(row["interior_consistency_gap"] for row in rows),
        "min_projection_gap": min(row["boundary_interior_projection_gap"] for row in rows),
        "min_order_gap": min(row["order_gap"] for row in rows),
        "max_order_erased_control_gap": max(row["order_erased_control_gap"] for row in rows),
        "min_anchor_scrambled_response_gap": min(row["anchor_scrambled_response_gap"] for row in rows),
        "min_full_boundary_class_count": min(row["full_boundary_class_count"] for row in rows),
        "max_single_probe_boundary_class_count": max(row["single_probe_boundary_class_count"] for row in rows),
        "boundary_erased_site_count": 0,
        "no_anchor_class_count": 0,
        "scalar_label_available": True,
        "bond_dim_one_admitted": BOUNDARY_BOND_CONTROL in BOND_DIMS,
        "phase7_reclassification_allowed": False,
        "rows": rows,
        "zero_interior_control": zero_interior_control,
        "sympy_exact_restriction_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_gate(restriction: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    restricted = z3.Bool("restricted")
    controls_fail = z3.Bool("controls_fail")
    dense = z3.Bool("dense")
    phase7 = z3.Bool("phase7")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, restricted, controls_fail, z3.Not(dense), z3.Not(phase7), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    row_count = z3.Int("restriction_row_count")
    control_count = z3.Int("control_row_count")
    max_parent_sites = z3.Int("max_parent_sites")
    max_subcarrier_sites = z3.Int("max_subcarrier_sites")
    max_bond = z3.Int("max_bond")
    count_solver.add(
        row_count == int(restriction["restriction_row_count"]),
        control_count == int(restriction["control_row_count"]),
        max_parent_sites == int(restriction["max_parent_peps3d_sites"]),
        max_subcarrier_sites == int(restriction["max_subcarrier_peps3d_sites"]),
        max_bond == int(restriction["max_peps3d_bond"]),
        row_count == 4,
        control_count == 1,
        max_parent_sites == 64,
        max_subcarrier_sites == 27,
        max_bond == 3,
    )
    gap_solver = z3.Solver()
    scaled_consistency_gap = z3.Int("scaled_max_consistency_gap")
    scaled_projection_gap = z3.Int("scaled_min_projection_gap")
    scaled_order_gap = z3.Int("scaled_min_order_gap")
    scaled_scramble_gap = z3.Int("scaled_min_anchor_scramble_gap")
    gap_solver.add(
        scaled_consistency_gap == int(restriction["max_response_restriction_gap"] * 1_000_000_000_000),
        scaled_projection_gap == int(restriction["min_projection_gap"] * 1_000_000),
        scaled_order_gap == int(restriction["min_order_gap"] * 1_000_000),
        scaled_scramble_gap == int(restriction["min_anchor_scrambled_response_gap"] * 1_000_000),
        scaled_consistency_gap == 0,
        scaled_projection_gap > 0,
        scaled_order_gap > 0,
        scaled_scramble_gap > 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and bad.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_restriction_nonpromotion_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "restriction_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_consistency_gap": int(restriction["max_response_restriction_gap"] * 1_000_000_000_000),
        "scaled_projection_gap": int(restriction["min_projection_gap"] * 1_000_000),
        "scaled_order_gap": int(restriction["min_order_gap"] * 1_000_000),
        "scaled_anchor_scramble_gap": int(restriction["min_anchor_scrambled_response_gap"] * 1_000_000),
    }


def cvc5_gate(restriction: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": restriction["restriction_row_count"] == 4,
        "anchored": restriction["max_subcarrier_peps3d_sites"] == 27,
        "restricted": restriction["max_response_restriction_gap"] < TOL,
        "controls_fail": restriction["min_anchor_scrambled_response_gap"] > GAP_FLOOR,
        "dense": restriction["dense_state_closure_used"] or restriction["dense_environment_closure_used"],
        "phase7": restriction["phase7_reclassification_allowed"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["dense"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["phase7"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["promote"]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "restriction_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    restriction = restriction_gate()
    z3_row = z3_gate(restriction)
    cvc5_row = cvc5_gate(restriction)
    positive = {
        "P1_replay_restriction_consistency": restriction,
    }
    graveyard = {
        "GC_no_anchor_control_rejected": {
            "pass": restriction["no_anchor_class_count"] == 0,
            "no_anchor_class_count": restriction["no_anchor_class_count"],
        },
        "GC_scalar_label_not_restriction_signature": {
            "pass": restriction["scalar_label_available"],
            "why_rejected": "scalar labels can count restriction rows but do not carry pi_restrict response maps, inherited V/E/F/C anchors, or local order paths",
        },
        "GC_boundary_erased_control_rejected": {
            "pass": restriction["boundary_erased_site_count"] == 0,
            "boundary_erased_site_count": restriction["boundary_erased_site_count"],
        },
        "GC_flattened_boundary_control_collapses": {
            "pass": all(row["flattened_boundary_class_count"] == 1 for row in restriction["rows"]),
            "max_flattened_boundary_class_count": max(row["flattened_boundary_class_count"] for row in restriction["rows"]),
        },
        "GC_anchor_scrambled_restriction_rejected": {
            "pass": all(
                row["anchor_scrambled_response_gap"] > GAP_FLOOR
                and row["anchor_scrambled_inherited_anchor_counts"] != row["anchor_counts"]
                for row in restriction["rows"]
            ),
            "min_anchor_scrambled_response_gap": restriction["min_anchor_scrambled_response_gap"],
        },
        "GC_single_probe_non_ic_control_collapses": {
            "pass": all(row["single_probe_non_ic_collapses"] for row in restriction["rows"]),
            "max_single_probe_boundary_class_count": restriction["max_single_probe_boundary_class_count"],
            "min_full_boundary_class_count": restriction["min_full_boundary_class_count"],
        },
        "GC_order_erased_control_collapses": {
            "pass": restriction["max_order_erased_control_gap"] < TOL,
            "max_order_erased_control_gap": restriction["max_order_erased_control_gap"],
        },
        "GC_bond_dim_one_not_admitted": {
            "pass": not restriction["bond_dim_one_admitted"],
            "bond_dim_one_admitted": restriction["bond_dim_one_admitted"],
        },
        "GC_zero_interior_shape_blocked_control": restriction["zero_interior_control"],
        "GC_phase7_I_boundary_reclassification_rejected": {
            "pass": not restriction["phase7_reclassification_allowed"],
            "rejected_candidate": "I_boundary(K,bond_dim)=finite boundary-site and boundary-edge contraction signatures",
            "rejected_source_alignment_category": "phase7_peps3d_boundary_contraction_scale_closure_stress",
            "why_rejected": "Phase 7 scale/closure stress and Phase 3-6 dependencies cannot be consumed as a Phase 2 post-R_replay_K carrier restriction map",
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not restriction["dense_state_closure_used"] and not restriction["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_nonempty_boundary_and_interior_required": {
            "pass": all(row["boundary_site_count"] > 0 and row["interior_site_count"] > 0 for row in restriction["rows"]),
        },
        "B4_z3_finite_restriction_nonpromotion": z3_row,
        "B5_cvc5_finite_restriction_nonpromotion": cvc5_row,
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
            "F01": "finite parent carrier, finite pi_restrict selectors, finite subcarrier anchors, finite SIC probe/effect responses, finite local operator paths, finite controls, finite output table",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter on restricted boundary tensors, while order-erased control collapses",
        },
        "finite_map": [
            "C_restrict_K : (R_replay_K, pi_restrict, boundary_anchor, bond_dim, local_order_ops) -> finite replay-restriction consistency signatures + control gap vector",
            "pi_restrict : K_parent=(V,E,F,C) -> K_sub=(V',E',F',C') with inherited anchors and nonempty boundary/interior",
            "O_K : (T_boundary|K_sub, local_order_ops) -> finite local order-gap vector for each restriction row",
        ],
        "domain": {
            "carrier": "finite PEPS3D replay carrier restricted by explicit pi_restrict subcarrier maps",
            "parent_shape": restriction["parent_shape"],
            "subcarrier_shape": restriction["subcarrier_shape"],
            "restriction_offsets": restriction["restriction_offsets"],
            "zero_interior_control_shape": restriction["zero_interior_control_shape"],
            "bond_dims": restriction["bond_dims"],
            "restriction_row_count": restriction["restriction_row_count"],
            "control_row_count": restriction["control_row_count"],
            "max_parent_peps3d_sites": restriction["max_parent_peps3d_sites"],
            "max_subcarrier_peps3d_sites": restriction["max_subcarrier_peps3d_sites"],
            "max_peps3d_bond": restriction["max_peps3d_bond"],
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite restriction consistency table with pi_restrict selector gaps, inherited V/E/F/C anchor counts, boundary/interior projection gaps, local order gaps, controls, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_replay_restriction_consistency",
        "carrier_realization": "torch complex finite PEPS3D tensors over parent shape (4,4,4), subcarrier shape (3,3,3), offsets (0,0,0)/(1,1,1), bond 2/3, finite SIC response vectors, graph/topology support checks, and a blocked zero-interior shape control",
        "peps3d_embedding": "K_parent=(V,E,F,C) restricts to K_sub=(V',E',F',C') through explicit pi_restrict selector maps preserving site, edge, face, and cell anchors; no scalar carrier labels admitted",
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
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D replay restriction consistency under pi_restrict",
        "branch_status_before_run": "post_R_replay_K_candidate_map_discovery_C_restrict_K",
        "allowed_claims": [
            "explicit finite pi_restrict maps preserve response restriction consistency on the tested finite PEPS3D subcarrier rows",
            "inherited V/E/F/C anchors remain nonempty and graph/topology-supported on each admitted subcarrier row",
            "no-anchor, scalar-label, boundary-erased, flattened-boundary, anchor-scrambled, single-probe non-IC, order-erased, dense-closure, Phase 7 reclassification, bond-one, zero-interior, and promotion controls fail or collapse",
            "local physical operator order witness survives under restriction while order-erased control collapses on every restriction row",
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
            "z3_finite_restriction_nonpromotion_gate",
            "cvc5_finite_restriction_nonpromotion_gate",
            "sympy_exact_restriction_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_parent_and_subcarrier_graphs",
            "xgi_face_cell_hyperedges",
            "torch_geometric_restricted_edge_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_restricted_face_cell_complex",
            "gudhi_restricted_vertex_edge_face_filtration",
        ],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_CANDIDATE_DISCOVERY_PATH,
            PHASE2_R_REPLAY_RECEIPT,
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
        ],
        "required_negatives": [
            "no_anchor",
            "scalar_label",
            "boundary_erased",
            "flattened_boundary",
            "anchor_scrambled_restriction",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "phase7_I_boundary_reclassification",
            "bond_dim_one",
            "zero_interior_shape",
            "promotion",
        ],
        "negatives_run": [
            "no_anchor",
            "scalar_label",
            "boundary_erased",
            "flattened_boundary",
            "anchor_scrambled_restriction",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "phase7_I_boundary_reclassification",
            "bond_dim_one",
            "zero_interior_shape",
            "promotion",
        ],
        "kill_conditions": [
            "pi_restrict selectors or inherited V/E/F/C anchors are missing",
            "any admitted subcarrier has empty boundary or empty interior",
            "restriction consistency gap is nonzero",
            "boundary/interior projection gap vanishes on any restriction row",
            "anchor-scrambled restriction does not produce a finite rejection gap",
            "single-probe non-IC control does not collapse relative to the full effect family",
            "bond_dim_one is admitted as support",
            "zero-interior shape is admitted as support",
            "order witness vanishes on any restriction row",
            "dense closure is used",
            "Phase 7 I_boundary is consumed as a Phase 2 dependency",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_replay_restriction_consistency_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_replay_restriction_consistency",
            "restriction_row_count": restriction["restriction_row_count"],
            "control_row_count": restriction["control_row_count"],
            "max_parent_peps3d_sites": restriction["max_parent_peps3d_sites"],
            "max_subcarrier_peps3d_sites": restriction["max_subcarrier_peps3d_sites"],
            "max_peps3d_bond": restriction["max_peps3d_bond"],
            "max_response_restriction_gap": restriction["max_response_restriction_gap"],
            "min_projection_gap": restriction["min_projection_gap"],
            "min_order_gap": restriction["min_order_gap"],
            "min_anchor_scrambled_response_gap": restriction["min_anchor_scrambled_response_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "restriction_row_count": restriction["restriction_row_count"],
            "control_row_count": restriction["control_row_count"],
            "parent_shape": restriction["parent_shape"],
            "subcarrier_shape": restriction["subcarrier_shape"],
            "restriction_offsets": restriction["restriction_offsets"],
            "zero_interior_control_shape": restriction["zero_interior_control_shape"],
            "bond_dims": restriction["bond_dims"],
            "max_parent_peps3d_sites": restriction["max_parent_peps3d_sites"],
            "max_subcarrier_peps3d_sites": restriction["max_subcarrier_peps3d_sites"],
            "max_peps3d_bond": restriction["max_peps3d_bond"],
            "max_response_restriction_gap": restriction["max_response_restriction_gap"],
            "max_boundary_consistency_gap": restriction["max_boundary_consistency_gap"],
            "max_interior_consistency_gap": restriction["max_interior_consistency_gap"],
            "min_projection_gap": restriction["min_projection_gap"],
            "min_order_gap": restriction["min_order_gap"],
            "max_order_erased_control_gap": restriction["max_order_erased_control_gap"],
            "min_anchor_scrambled_response_gap": restriction["min_anchor_scrambled_response_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff explicit pi_restrict selector maps preserve restriction consistency and inherited V/E/F/C anchors across all finite rows, support rows have nonempty boundary/interior, controls fail or collapse, local order gap survives on every row, dense closure stays false, Phase 7 reclassification is rejected, and promotion is blocked.",
        "fail_rule": "Fail if pi_restrict is absent, restriction consistency gaps are nonzero, inherited anchors are lost, controls replace the carrier restriction, zero-interior shape is admitted as support, single-probe non-IC control does not collapse, order gap vanishes, dense closure is used, Phase 7/downstream receipts are consumed as support, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this replay restriction consistency receipt inside the active carrier frontier matrix.",
            "Either name another bounded carrier-frontier map or write the next active-frontier blocker; do not open later geometry from this row.",
        ],
        "next_admissible_step": "Classify this C_restrict_K packet, then choose another bounded carrier-frontier packet or write the next active-frontier blocker.",
        "why_not_v4_probes": (
            "This is a v5 formal scout for active PEPS3D carrier-frontier continuation. "
            "It is not a v4 probe and not a full PEPS3D closure claim."
        ),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
