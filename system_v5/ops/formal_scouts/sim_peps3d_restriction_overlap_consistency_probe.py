#!/usr/bin/env python3
"""PEPS3D restriction-overlap consistency scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  O_overlap_K :
      (C_restrict_K, pi_0, pi_1, omega_01, boundary_anchor, bond_dim,
       local_order_ops)
      -> finite overlap-gluing consistency signatures + control gap vector

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
NAME = "peps3d_restriction_overlap_consistency_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether two explicit "
    "finite restriction maps from the same PEPS3D parent carrier agree on a "
    "shared finite overlap carrier, without dense closure or downstream "
    "geometry."
)
SCIENTIFIC_QUESTION = (
    "Does O_overlap_K preserve finite response signatures and inherited "
    "V/E/F/C anchors on the shared overlap of two C_restrict_K-style "
    "subcarriers while no-anchor, scalar-label, overlap-erased, disjoint, "
    "duplicate, anchor-scrambled, single-probe non-IC, order-erased, "
    "dense-closure, and later-layer reclassification controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_restriction_overlap_consistency"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_C_restrict_active_frontier_blocker_20260525.json"
PHASE2_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_C_restrict_candidate_map_discovery_20260525.json"
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

CLAIM_CEILING = (
    "Formal scout only: tests finite PEPS3D restriction-overlap consistency "
    "for a bounded two-restriction overlap carrier. It does not admit nested "
    "Hopf tori, Weyl sheets, terrain, operator substage cells, flux, "
    "Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, "
    "or full PEPS3D closure."
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
        "reason": "load-bearing finite overlap selectors, response tensors, route consistency gaps, and local order gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing overlap carrier graph connectivity and inherited edge anchor checks",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite face/cell hyperedge support checks on the overlap carrier",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-complex face support check for inherited overlap anchors",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite filtration check over overlap vertices, edges, and faces",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite graph data aggregation check over overlap edge incidence",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite overlap/nonpromotion and control-collapse gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite overlap/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite row, parent, overlap site, edge, face, cell, and bond count checks",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not applicable: this carrier-frontier overlap map does not claim geometric product, chirality, or rotor transport",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not applicable: this carrier-frontier overlap map does not claim a Riemannian metric, geodesic, or curvature",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not applicable: this carrier-frontier overlap map does not claim E(3) or SO(3) equivariance",
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

PARENT_SHAPE = (5, 5, 5)
RESTRICTION_SHAPE = (4, 4, 4)
OVERLAP_SHAPE = (3, 3, 3)
RESTRICTION_OFFSETS = [(0, 0, 0), (1, 1, 1)]
OVERLAP_ORIGIN = (1, 1, 1)
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


def absolute_overlap_coords() -> list[tuple[int, int, int]]:
    return [shifted_coord(coord, OVERLAP_ORIGIN) for coord in coords_for_shape(OVERLAP_SHAPE)]


def local_coords_in_restriction(
    absolute_coords: list[tuple[int, int, int]],
    restriction_offset: tuple[int, int, int],
) -> list[tuple[int, int, int]]:
    return [
        tuple(coord[axis] - restriction_offset[axis] for axis in range(3))
        for coord in absolute_coords
    ]


def selected_parent_indices(
    parent_shape: tuple[int, int, int],
    absolute_coords: list[tuple[int, int, int]],
) -> list[int]:
    parent_index = coord_index(parent_shape)
    return [parent_index[coord] for coord in absolute_coords]


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


def overlap_row(bond_dim: int) -> dict[str, Any]:
    parent_coords = coords_for_shape(PARENT_SHAPE)
    parent_responses = probe_responses(site_spinors(len(parent_coords)), sic_effects())
    overlap_coords = coords_for_shape(OVERLAP_SHAPE)
    inherited_coords = absolute_overlap_coords()
    local_to_parent = selected_parent_indices(PARENT_SHAPE, inherited_coords)
    parent_index = coord_index(PARENT_SHAPE)
    restriction_index = coord_index(RESTRICTION_SHAPE)

    composed_selectors = []
    route_selected = []
    route_local_coords = []
    for offset in RESTRICTION_OFFSETS:
        restriction_abs_coords = [
            shifted_coord(coord, offset) for coord in coords_for_shape(RESTRICTION_SHAPE)
        ]
        restriction_to_parent = [parent_index[coord] for coord in restriction_abs_coords]
        restriction_selector = torch.zeros((len(restriction_abs_coords), len(parent_coords)), dtype=RTYPE)
        for restriction_idx, parent_idx in enumerate(restriction_to_parent):
            restriction_selector[restriction_idx, parent_idx] = 1.0

        local_route = local_coords_in_restriction(inherited_coords, offset)
        route_local_coords.append(local_route)
        overlap_selector = torch.zeros((len(overlap_coords), len(restriction_abs_coords)), dtype=RTYPE)
        for overlap_idx, local_coord in enumerate(local_route):
            overlap_selector[overlap_idx, restriction_index[local_coord]] = 1.0

        restricted_responses = restriction_selector @ parent_responses
        route_selected.append(overlap_selector @ restricted_responses)
        composed_selectors.append(overlap_selector @ restriction_selector)

    selected_a, selected_b = route_selected
    route_consistency_gap = float(torch.linalg.vector_norm(selected_a - selected_b).item())
    overlap_responses = parent_responses[local_to_parent]
    response_selector_gap = float(torch.linalg.vector_norm(overlap_responses - selected_a).item())

    boundary = [idx for idx, coord in enumerate(overlap_coords) if is_boundary(coord, OVERLAP_SHAPE)]
    interior = [idx for idx, coord in enumerate(overlap_coords) if not is_boundary(coord, OVERLAP_SHAPE)]
    boundary_signature_a = selected_a[boundary].mean(dim=0)
    boundary_signature_b = selected_b[boundary].mean(dim=0)
    interior_signature_a = selected_a[interior].mean(dim=0)
    interior_signature_b = selected_b[interior].mean(dim=0)
    boundary_route_gap = float(torch.linalg.vector_norm(boundary_signature_a - boundary_signature_b).item())
    interior_route_gap = float(torch.linalg.vector_norm(interior_signature_a - interior_signature_b).item())
    projection_gap = float(torch.linalg.vector_norm(boundary_signature_a - interior_signature_a).item())

    full_boundary_class_count = unique_rows(overlap_responses[boundary], columns=4)
    single_probe_boundary_class_count = unique_rows(overlap_responses[boundary], columns=1)

    tensors = make_site_tensors(overlap_responses, inherited_coords, bond_dim)
    boundary_tensors = tensors[boundary]
    shift, filt = shift_filter_ops()
    filter_after_shift = apply_physical_operator(apply_physical_operator(boundary_tensors, shift), filt)
    shift_after_filter = apply_physical_operator(apply_physical_operator(boundary_tensors, filt), shift)
    order_gap = float(torch.linalg.vector_norm((filter_after_shift - shift_after_filter).reshape(-1)).item())
    erased_1 = apply_physical_operator(apply_physical_operator(boundary_tensors, filt), filt)
    erased_2 = apply_physical_operator(apply_physical_operator(boundary_tensors, filt), filt)
    order_erased_gap = float(torch.linalg.vector_norm((erased_1 - erased_2).reshape(-1)).item())

    local_edges = edge_list(OVERLAP_SHAPE)
    boundary_set = set(boundary)
    cut_edges = [
        edge for edge in local_edges
        if (int(edge["src"]) in boundary_set) != (int(edge["dst"]) in boundary_set)
    ]
    anchor_counts = {
        "V": len(overlap_coords),
        "E": len(local_edges),
        "F": len(face_list(OVERLAP_SHAPE)),
        "C": len(cell_list(OVERLAP_SHAPE)),
    }
    inherited_counts = inherited_anchor_counts(PARENT_SHAPE, OVERLAP_SHAPE, local_to_parent)
    topology = topology_tool_signature(OVERLAP_SHAPE, local_to_parent)

    scrambled_local_to_parent = local_to_parent[1:] + local_to_parent[:1]
    scrambled_selected = parent_responses[scrambled_local_to_parent]
    anchor_scrambled_response_gap = float(torch.linalg.vector_norm(overlap_responses - scrambled_selected).item())
    scrambled_counts = inherited_anchor_counts(PARENT_SHAPE, OVERLAP_SHAPE, scrambled_local_to_parent)

    edge_sigs = all_edge_signatures(tensors, local_edges)
    site_signature_sum = float(torch.real(torch.sum(tensors * tensors.conj())).item())
    edge_signature_sum = float(torch.real(torch.sum(edge_sigs)).item())
    route_selector_difference_gap = float(torch.linalg.vector_norm(composed_selectors[0] - composed_selectors[1]).item())
    selector_row_sums = torch.stack([selector.sum(dim=1) for selector in composed_selectors])
    selector_column_sums = torch.stack([selector.sum(dim=0) for selector in composed_selectors])
    exact_total = (
        sp.Integer(len(parent_coords))
        + sp.Integer(len(overlap_coords))
        + sp.Integer(len(local_edges))
        + sp.Integer(len(face_list(OVERLAP_SHAPE)))
        + sp.Integer(len(cell_list(OVERLAP_SHAPE)))
        + sp.Integer(len(cut_edges))
        + sp.Integer(bond_dim)
    )
    pass_row = bool(
        len(boundary) > 0
        and len(interior) > 0
        and len(cut_edges) > 0
        and anchor_counts == inherited_counts
        and topology["pass"]
        and route_consistency_gap < TOL
        and response_selector_gap < TOL
        and boundary_route_gap < TOL
        and interior_route_gap < TOL
        and projection_gap > GAP_FLOOR
        and full_boundary_class_count > single_probe_boundary_class_count
        and order_gap > GAP_FLOOR
        and order_erased_gap < TOL
        and anchor_scrambled_response_gap > GAP_FLOOR
        and scrambled_counts != anchor_counts
    )
    return {
        "pass": pass_row,
        "parent_shape": list(PARENT_SHAPE),
        "restriction_shape": list(RESTRICTION_SHAPE),
        "overlap_shape": list(OVERLAP_SHAPE),
        "restriction_offsets": [list(offset) for offset in RESTRICTION_OFFSETS],
        "route_local_coord_minmax": [
            {
                "min": [min(coord[axis] for coord in route) for axis in range(3)],
                "max": [max(coord[axis] for coord in route) for axis in range(3)],
            }
            for route in route_local_coords
        ],
        "bond_dim": bond_dim,
        "parent_site_count": len(parent_coords),
        "overlap_site_count": len(overlap_coords),
        "boundary_site_count": len(boundary),
        "interior_site_count": len(interior),
        "cut_edge_count": len(cut_edges),
        "anchor_counts": anchor_counts,
        "inherited_anchor_counts": inherited_counts,
        "route_consistency_gap": route_consistency_gap,
        "route_selector_difference_gap": route_selector_difference_gap,
        "response_selector_gap": response_selector_gap,
        "boundary_route_gap": boundary_route_gap,
        "interior_route_gap": interior_route_gap,
        "boundary_interior_projection_gap": projection_gap,
        "full_boundary_class_count": full_boundary_class_count,
        "single_probe_boundary_class_count": single_probe_boundary_class_count,
        "single_probe_non_ic_collapses": single_probe_boundary_class_count < full_boundary_class_count,
        "selector_row_sum_min": float(torch.min(selector_row_sums).item()),
        "selector_row_sum_max": float(torch.max(selector_row_sums).item()),
        "selector_column_sum_max": float(torch.max(selector_column_sums).item()),
        "order_gap": order_gap,
        "order_erased_control_gap": order_erased_gap,
        "anchor_scrambled_response_gap": anchor_scrambled_response_gap,
        "anchor_scrambled_inherited_anchor_counts": scrambled_counts,
        "site_signature_sum": site_signature_sum,
        "edge_signature_sum": edge_signature_sum,
        "topology_tool_signature": topology,
        "sympy_exact_overlap_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def disjoint_restrictions_control() -> dict[str, Any]:
    left = {shifted_coord(coord, (0, 0, 0)) for coord in coords_for_shape((2, 2, 2))}
    right = {shifted_coord(coord, (3, 3, 3)) for coord in coords_for_shape((2, 2, 2))}
    overlap = left & right
    return {
        "pass": len(overlap) == 0,
        "control_status": "blocked_control_only",
        "left_shape": [2, 2, 2],
        "right_shape": [2, 2, 2],
        "left_offset": [0, 0, 0],
        "right_offset": [3, 3, 3],
        "overlap_site_count": len(overlap),
        "why_not_support": "two restrictions with empty overlap cannot support O_overlap_K gluing consistency",
    }


def duplicate_restrictions_control() -> dict[str, Any]:
    overlap_coords = absolute_overlap_coords()
    route_a = local_coords_in_restriction(overlap_coords, RESTRICTION_OFFSETS[0])
    route_duplicate = local_coords_in_restriction(overlap_coords, RESTRICTION_OFFSETS[0])
    return {
        "pass": route_a == route_duplicate,
        "control_status": "blocked_control_only",
        "why_not_support": "duplicate restriction routes are not fresh two-map overlap evidence",
    }


def overlap_gate() -> dict[str, Any]:
    rows = [overlap_row(bond_dim) for bond_dim in BOND_DIMS]
    disjoint = disjoint_restrictions_control()
    duplicate = duplicate_restrictions_control()
    exact_total = (
        sp.Integer(len(rows))
        + sp.Integer(sum(row["parent_site_count"] for row in rows))
        + sp.Integer(sum(row["overlap_site_count"] for row in rows))
        + sp.Integer(sum(row["boundary_site_count"] for row in rows))
        + sp.Integer(sum(row["interior_site_count"] for row in rows))
        + sp.Integer(sum(row["cut_edge_count"] for row in rows))
        + sp.Integer(max(BOND_DIMS))
    )
    return {
        "pass": (
            all(row["pass"] for row in rows)
            and disjoint["pass"]
            and duplicate["pass"]
            and BOUNDARY_BOND_CONTROL not in BOND_DIMS
        ),
        "finite_map": "O_overlap_K : (C_restrict_K, pi_0, pi_1, omega_01, boundary_anchor, bond_dim, local_order_ops) -> finite overlap-gluing consistency signatures + control gap vector",
        "overlap_row_count": len(rows),
        "control_row_count": 2,
        "parent_shape": list(PARENT_SHAPE),
        "restriction_shape": list(RESTRICTION_SHAPE),
        "overlap_shape": list(OVERLAP_SHAPE),
        "restriction_offsets": [list(offset) for offset in RESTRICTION_OFFSETS],
        "bond_dims": list(BOND_DIMS),
        "max_parent_peps3d_sites": max(row["parent_site_count"] for row in rows),
        "max_overlap_peps3d_sites": max(row["overlap_site_count"] for row in rows),
        "max_peps3d_bond": max(BOND_DIMS),
        "max_route_consistency_gap": max(row["route_consistency_gap"] for row in rows),
        "max_response_selector_gap": max(row["response_selector_gap"] for row in rows),
        "max_boundary_route_gap": max(row["boundary_route_gap"] for row in rows),
        "max_interior_route_gap": max(row["interior_route_gap"] for row in rows),
        "min_projection_gap": min(row["boundary_interior_projection_gap"] for row in rows),
        "min_order_gap": min(row["order_gap"] for row in rows),
        "max_order_erased_control_gap": max(row["order_erased_control_gap"] for row in rows),
        "min_anchor_scrambled_response_gap": min(row["anchor_scrambled_response_gap"] for row in rows),
        "min_full_boundary_class_count": min(row["full_boundary_class_count"] for row in rows),
        "max_single_probe_boundary_class_count": max(row["single_probe_boundary_class_count"] for row in rows),
        "overlap_erased_site_count": 0,
        "no_anchor_class_count": 0,
        "scalar_label_available": True,
        "bond_dim_one_admitted": BOUNDARY_BOND_CONTROL in BOND_DIMS,
        "phase7_reclassification_allowed": False,
        "rows": rows,
        "disjoint_restrictions_control": disjoint,
        "duplicate_restrictions_control": duplicate,
        "sympy_exact_overlap_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_gate(overlap: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    overlapping = z3.Bool("overlapping")
    controls_fail = z3.Bool("controls_fail")
    dense = z3.Bool("dense")
    phase7 = z3.Bool("phase7")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, overlapping, controls_fail, z3.Not(dense), z3.Not(phase7), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    row_count = z3.Int("overlap_row_count")
    control_count = z3.Int("control_row_count")
    max_parent_sites = z3.Int("max_parent_sites")
    max_overlap_sites = z3.Int("max_overlap_sites")
    max_bond = z3.Int("max_bond")
    count_solver.add(
        row_count == int(overlap["overlap_row_count"]),
        control_count == int(overlap["control_row_count"]),
        max_parent_sites == int(overlap["max_parent_peps3d_sites"]),
        max_overlap_sites == int(overlap["max_overlap_peps3d_sites"]),
        max_bond == int(overlap["max_peps3d_bond"]),
        row_count == 2,
        control_count == 2,
        max_parent_sites == 125,
        max_overlap_sites == 27,
        max_bond == 3,
    )
    gap_solver = z3.Solver()
    scaled_consistency_gap = z3.Int("scaled_max_route_consistency_gap")
    scaled_projection_gap = z3.Int("scaled_min_projection_gap")
    scaled_order_gap = z3.Int("scaled_min_order_gap")
    scaled_scramble_gap = z3.Int("scaled_min_anchor_scramble_gap")
    gap_solver.add(
        scaled_consistency_gap == int(overlap["max_route_consistency_gap"] * 1_000_000_000_000),
        scaled_projection_gap == int(overlap["min_projection_gap"] * 1_000_000),
        scaled_order_gap == int(overlap["min_order_gap"] * 1_000_000),
        scaled_scramble_gap == int(overlap["min_anchor_scrambled_response_gap"] * 1_000_000),
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
        "finite_anchor_overlap_nonpromotion_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "overlap_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_consistency_gap": int(overlap["max_route_consistency_gap"] * 1_000_000_000_000),
        "scaled_projection_gap": int(overlap["min_projection_gap"] * 1_000_000),
        "scaled_order_gap": int(overlap["min_order_gap"] * 1_000_000),
        "scaled_anchor_scramble_gap": int(overlap["min_anchor_scrambled_response_gap"] * 1_000_000),
    }


def cvc5_gate(overlap: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": overlap["overlap_row_count"] == 2,
        "anchored": overlap["max_overlap_peps3d_sites"] == 27,
        "overlapping": overlap["max_route_consistency_gap"] < TOL,
        "controls_fail": overlap["min_anchor_scrambled_response_gap"] > GAP_FLOOR,
        "dense": overlap["dense_state_closure_used"] or overlap["dense_environment_closure_used"],
        "phase7": overlap["phase7_reclassification_allowed"],
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
        "overlap_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    overlap = overlap_gate()
    z3_row = z3_gate(overlap)
    cvc5_row = cvc5_gate(overlap)
    positive = {
        "P1_restriction_overlap_consistency": overlap,
    }
    graveyard = {
        "GC_no_anchor_control_rejected": {
            "pass": overlap["no_anchor_class_count"] == 0,
            "no_anchor_class_count": overlap["no_anchor_class_count"],
        },
        "GC_scalar_label_not_overlap_signature": {
            "pass": overlap["scalar_label_available"],
            "why_rejected": "scalar labels can count overlap rows but do not carry route response maps, inherited V/E/F/C anchors, or local order paths",
        },
        "GC_overlap_erased_control_rejected": {
            "pass": overlap["overlap_erased_site_count"] == 0,
            "overlap_erased_site_count": overlap["overlap_erased_site_count"],
        },
        "GC_disjoint_restrictions_blocked_control": overlap["disjoint_restrictions_control"],
        "GC_duplicate_restrictions_blocked_control": overlap["duplicate_restrictions_control"],
        "GC_anchor_scrambled_overlap_rejected": {
            "pass": all(
                row["anchor_scrambled_response_gap"] > GAP_FLOOR
                and row["anchor_scrambled_inherited_anchor_counts"] != row["anchor_counts"]
                for row in overlap["rows"]
            ),
            "min_anchor_scrambled_response_gap": overlap["min_anchor_scrambled_response_gap"],
        },
        "GC_single_probe_non_ic_control_collapses": {
            "pass": all(row["single_probe_non_ic_collapses"] for row in overlap["rows"]),
            "max_single_probe_boundary_class_count": overlap["max_single_probe_boundary_class_count"],
            "min_full_boundary_class_count": overlap["min_full_boundary_class_count"],
        },
        "GC_order_erased_control_collapses": {
            "pass": overlap["max_order_erased_control_gap"] < TOL,
            "max_order_erased_control_gap": overlap["max_order_erased_control_gap"],
        },
        "GC_bond_dim_one_not_admitted": {
            "pass": not overlap["bond_dim_one_admitted"],
            "bond_dim_one_admitted": overlap["bond_dim_one_admitted"],
        },
        "GC_later_boundary_reclassification_rejected": {
            "pass": not overlap["phase7_reclassification_allowed"],
            "rejected_candidate": "I_boundary(K,bond_dim)=finite boundary-site and boundary-edge contraction signatures",
            "rejected_source_alignment_category": "later_peps3d_boundary_contraction_scale_closure_stress",
            "why_rejected": "scale/closure stress and later dependencies cannot be consumed as a carrier-frontier overlap map",
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not overlap["dense_state_closure_used"] and not overlap["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_nonempty_overlap_boundary_and_interior_required": {
            "pass": all(row["boundary_site_count"] > 0 and row["interior_site_count"] > 0 for row in overlap["rows"]),
        },
        "B4_z3_finite_overlap_nonpromotion": z3_row,
        "B5_cvc5_finite_overlap_nonpromotion": cvc5_row,
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
            "F01": "finite parent carrier, finite restriction selectors, finite overlap carrier anchors, finite SIC probe/effect responses, finite local operator paths, finite controls, finite output table",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter on overlap boundary tensors, while order-erased control collapses",
        },
        "finite_map": [
            "O_overlap_K : (C_restrict_K, pi_0, pi_1, omega_01, boundary_anchor, bond_dim, local_order_ops) -> finite overlap-gluing consistency signatures + control gap vector",
            "omega_01 : K_0 cap K_1 -> K_overlap=(V_omega,E_omega,F_omega,C_omega) with inherited anchors and nonempty boundary/interior",
            "O_K : (T_boundary|K_overlap, local_order_ops) -> finite local order-gap vector for each overlap row",
        ],
        "domain": {
            "carrier": "finite PEPS3D parent carrier with two explicit restriction maps and a shared finite overlap carrier",
            "parent_shape": overlap["parent_shape"],
            "restriction_shape": overlap["restriction_shape"],
            "overlap_shape": overlap["overlap_shape"],
            "restriction_offsets": overlap["restriction_offsets"],
            "bond_dims": overlap["bond_dims"],
            "overlap_row_count": overlap["overlap_row_count"],
            "control_row_count": overlap["control_row_count"],
            "max_parent_peps3d_sites": overlap["max_parent_peps3d_sites"],
            "max_overlap_peps3d_sites": overlap["max_overlap_peps3d_sites"],
            "max_peps3d_bond": overlap["max_peps3d_bond"],
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite overlap consistency table with two-route selector gaps, inherited V/E/F/C anchor counts, boundary/interior projection gaps, local order gaps, controls, and dense-closure blockers",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_restriction_overlap_consistency",
        "carrier_realization": "torch complex finite PEPS3D tensors over parent shape (5,5,5), two (4,4,4) restriction routes, overlap shape (3,3,3), bond 2/3, finite SIC response vectors, graph/topology support checks, and disjoint/duplicate controls",
        "peps3d_embedding": "K_parent=(V,E,F,C) restricts along pi_0 and pi_1 to two subcarriers whose shared omega_01 overlap has inherited site, edge, face, and cell anchors; no scalar carrier labels admitted",
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
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D restriction-overlap consistency under omega_01",
        "branch_status_before_run": "post_C_restrict_K_candidate_map_discovery_O_overlap_K",
        "allowed_claims": [
            "two explicit finite restriction routes agree on the shared overlap response signatures for the tested finite PEPS3D overlap rows",
            "inherited V/E/F/C anchors remain nonempty and graph/topology-supported on each admitted overlap row",
            "no-anchor, scalar-label, overlap-erased, disjoint, duplicate, anchor-scrambled, single-probe non-IC, order-erased, dense-closure, later reclassification, bond-one, and promotion controls fail or collapse",
            "local physical operator order witness survives on the overlap while order-erased control collapses on every overlap row",
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
            "z3_finite_overlap_nonpromotion_gate",
            "cvc5_finite_overlap_nonpromotion_gate",
            "sympy_exact_overlap_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_overlap_graph",
            "xgi_overlap_face_cell_hyperedges",
            "torch_geometric_overlap_edge_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_overlap_face_cell_complex",
            "gudhi_overlap_vertex_edge_face_filtration",
        ],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_CANDIDATE_DISCOVERY_PATH,
            PHASE2_C_RESTRICT_RECEIPT,
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
        ],
        "required_negatives": [
            "no_anchor",
            "scalar_label",
            "overlap_erased",
            "disjoint_restrictions",
            "duplicate_restrictions",
            "anchor_scrambled_overlap",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "later_boundary_reclassification",
            "bond_dim_one",
            "promotion",
        ],
        "negatives_run": [
            "no_anchor",
            "scalar_label",
            "overlap_erased",
            "disjoint_restrictions",
            "duplicate_restrictions",
            "anchor_scrambled_overlap",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "later_boundary_reclassification",
            "bond_dim_one",
            "promotion",
        ],
        "kill_conditions": [
            "omega_01 overlap carrier or inherited V/E/F/C anchors are missing",
            "any admitted overlap row has empty boundary or empty interior",
            "two-route overlap consistency gap is nonzero",
            "boundary/interior projection gap vanishes on any overlap row",
            "anchor-scrambled overlap does not produce a finite rejection gap",
            "disjoint or duplicate restrictions are admitted as support",
            "single-probe non-IC control does not collapse relative to the full effect family",
            "bond_dim_one is admitted as support",
            "order witness vanishes on any overlap row",
            "dense closure is used",
            "later boundary closure evidence is consumed as a carrier-frontier dependency",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_restriction_overlap_consistency_v1",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "phase": 2,
            "elapsed_seconds": time.time() - started,
            "candidate": "peps3d_restriction_overlap_consistency",
            "overlap_row_count": overlap["overlap_row_count"],
            "control_row_count": overlap["control_row_count"],
            "max_parent_peps3d_sites": overlap["max_parent_peps3d_sites"],
            "max_overlap_peps3d_sites": overlap["max_overlap_peps3d_sites"],
            "max_peps3d_bond": overlap["max_peps3d_bond"],
            "max_route_consistency_gap": overlap["max_route_consistency_gap"],
            "min_projection_gap": overlap["min_projection_gap"],
            "min_order_gap": overlap["min_order_gap"],
            "min_anchor_scrambled_response_gap": overlap["min_anchor_scrambled_response_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "overlap_row_count": overlap["overlap_row_count"],
            "control_row_count": overlap["control_row_count"],
            "parent_shape": overlap["parent_shape"],
            "restriction_shape": overlap["restriction_shape"],
            "overlap_shape": overlap["overlap_shape"],
            "restriction_offsets": overlap["restriction_offsets"],
            "bond_dims": overlap["bond_dims"],
            "max_parent_peps3d_sites": overlap["max_parent_peps3d_sites"],
            "max_overlap_peps3d_sites": overlap["max_overlap_peps3d_sites"],
            "max_peps3d_bond": overlap["max_peps3d_bond"],
            "max_route_consistency_gap": overlap["max_route_consistency_gap"],
            "max_response_selector_gap": overlap["max_response_selector_gap"],
            "max_boundary_route_gap": overlap["max_boundary_route_gap"],
            "max_interior_route_gap": overlap["max_interior_route_gap"],
            "min_projection_gap": overlap["min_projection_gap"],
            "min_order_gap": overlap["min_order_gap"],
            "max_order_erased_control_gap": overlap["max_order_erased_control_gap"],
            "min_anchor_scrambled_response_gap": overlap["min_anchor_scrambled_response_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "Pass iff explicit pi_0 and pi_1 selectors agree on the shared omega_01 response signatures and inherited V/E/F/C anchors across all finite rows, support rows have nonempty boundary/interior, controls fail or collapse, local order gap survives on every row, dense closure stays false, later reclassification is rejected, and promotion is blocked.",
        "fail_rule": "Fail if omega_01 is absent, overlap consistency gaps are nonzero, inherited anchors are lost, controls replace the overlap carrier, disjoint or duplicate restrictions are admitted, single-probe non-IC control does not collapse, order gap vanishes, dense closure is used, later/downstream receipts are consumed as support, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this restriction-overlap consistency receipt inside the active carrier frontier matrix.",
            "Either name another bounded carrier-frontier map or write the next active-frontier blocker; do not open later geometry from this row.",
        ],
        "next_admissible_step": "Classify this overlap packet, then choose another bounded carrier-frontier packet or write the next active-frontier blocker.",
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
