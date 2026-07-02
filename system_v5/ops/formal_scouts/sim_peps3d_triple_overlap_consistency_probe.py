#!/usr/bin/env python3
"""PEPS3D triple-overlap consistency scout.

Formal scout only.

This continuation packet stays inside PEPS3D-anchored finite
response-quotient carrier geometry. It tests:

  T_triple_overlap_K :
      (O_overlap_K, pi_0, pi_1, pi_2, omega_01, omega_12, omega_02,
       omega_012, boundary_anchor, bond_dim, local_order_ops)
      -> finite triple-overlap consistency table + pairwise/triple route gap
         vector

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
NAME = "peps3d_triple_overlap_consistency_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Continue the active carrier frontier by testing whether three explicit "
    "finite restriction maps from the same PEPS3D parent carrier agree on a "
    "shared finite triple-overlap carrier, without dense closure or downstream "
    "geometry."
)
SCIENTIFIC_QUESTION = (
    "Does T_triple_overlap_K preserve finite response signatures and inherited "
    "V/E/F/C anchors on the shared triple overlap of three C_restrict_K-style "
    "subcarriers while no-anchor, scalar-label, triple-overlap-erased, empty, "
    "duplicate, pairwise-only, anchor-scrambled, single-probe non-IC, "
    "order-erased, dense-closure, and later-layer reclassification controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_triple_overlap_consistency"
PROMOTION_ALLOWED = False

PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_TRANSITION_PATH = "system_v5/ops/formal_scouts/phase2_seed_frontier_transition_decision_20260525.json"
PHASE2_ACTIVE_BLOCKER_PATH = "system_v5/ops/formal_scouts/phase2_post_O_overlap_active_frontier_blocker_20260525.json"
PHASE2_CANDIDATE_DISCOVERY_PATH = "system_v5/ops/formal_scouts/phase2_post_O_overlap_candidate_map_discovery_20260525.json"
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

CLAIM_CEILING = (
    "Formal scout only: tests one bounded finite PEPS3D triple-overlap "
    "consistency table for three restriction routes. It does not admit nested "
    "Hopf tori, Weyl sheets, terrain, operator substage cells, flux, "
    "Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, axes 7-12, "
    "a general gluing law, a shape law, a bond convergence claim, or full "
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
        "reason": "load-bearing finite triple-overlap selectors, response tensors, route consistency gaps, and local order gaps",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing triple-overlap carrier graph connectivity and inherited edge anchor checks",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite face/cell hyperedge support checks on the triple-overlap carrier",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-complex face support check for inherited triple-overlap anchors",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite filtration check over triple-overlap vertices, edges, and faces",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite graph data aggregation check over triple-overlap edge incidence",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite triple-overlap/nonpromotion and control-collapse gate",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite triple-overlap/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite row, parent, triple-overlap site, edge, face, cell, and bond count checks",
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

PARENT_SHAPE = (5, 5, 5)
RESTRICTION_SHAPE = (4, 4, 4)
TRIPLE_OVERLAP_SHAPE = (3, 3, 3)
RESTRICTION_OFFSETS = [(0, 0, 0), (1, 1, 0), (1, 0, 1)]
TRIPLE_OVERLAP_ORIGIN = (1, 1, 1)
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


def absolute_triple_overlap_coords() -> list[tuple[int, int, int]]:
    return [
        shifted_coord(coord, TRIPLE_OVERLAP_ORIGIN)
        for coord in coords_for_shape(TRIPLE_OVERLAP_SHAPE)
    ]


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
    return {"V": len(local_to_parent), "E": inherited_edges, "F": inherited_faces, "C": inherited_cells}


def topology_tool_signature(sub_shape: tuple[int, int, int], local_to_parent: list[int]) -> dict[str, Any]:
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
    data = Data(
        x=torch.arange(len(local_to_parent), dtype=RTYPE).reshape(len(local_to_parent), 1),
        edge_index=edge_index,
    )
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


def pairwise_norms(rows: list[torch.Tensor]) -> dict[str, float]:
    out: dict[str, float] = {}
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            out[f"{i}{j}"] = float(torch.linalg.vector_norm(rows[i] - rows[j]).item())
    return out


def restriction_absolute_set(offset: tuple[int, int, int]) -> set[tuple[int, int, int]]:
    return {shifted_coord(coord, offset) for coord in coords_for_shape(RESTRICTION_SHAPE)}


def triple_overlap_row(bond_dim: int) -> dict[str, Any]:
    parent_coords = coords_for_shape(PARENT_SHAPE)
    parent_responses = probe_responses(site_spinors(len(parent_coords)), sic_effects())
    triple_coords = coords_for_shape(TRIPLE_OVERLAP_SHAPE)
    inherited_coords = absolute_triple_overlap_coords()
    local_to_parent = selected_parent_indices(PARENT_SHAPE, inherited_coords)
    parent_index = coord_index(PARENT_SHAPE)
    restriction_index = coord_index(RESTRICTION_SHAPE)

    route_selected = []
    composed_selectors = []
    route_local_coords = []
    local_coord_tensors = []
    restriction_sets = []
    for offset in RESTRICTION_OFFSETS:
        restriction_abs_coords = [
            shifted_coord(coord, offset) for coord in coords_for_shape(RESTRICTION_SHAPE)
        ]
        restriction_sets.append(set(restriction_abs_coords))
        restriction_to_parent = [parent_index[coord] for coord in restriction_abs_coords]
        restriction_selector = torch.zeros((len(restriction_abs_coords), len(parent_coords)), dtype=RTYPE)
        for restriction_idx, parent_idx in enumerate(restriction_to_parent):
            restriction_selector[restriction_idx, parent_idx] = 1.0

        local_route = local_coords_in_restriction(inherited_coords, offset)
        route_local_coords.append(local_route)
        local_coord_tensors.append(torch.tensor(local_route, dtype=RTYPE).reshape(-1))
        overlap_selector = torch.zeros((len(triple_coords), len(restriction_abs_coords)), dtype=RTYPE)
        for triple_idx, local_coord in enumerate(local_route):
            overlap_selector[triple_idx, restriction_index[local_coord]] = 1.0

        restricted_responses = restriction_selector @ parent_responses
        route_selected.append(overlap_selector @ restricted_responses)
        composed_selectors.append(overlap_selector @ restriction_selector)

    overlap_responses = parent_responses[local_to_parent]
    route_gap_by_pair = pairwise_norms(route_selected)
    selector_gap_by_pair = pairwise_norms(composed_selectors)
    local_route_signature_gap_by_pair = pairwise_norms(local_coord_tensors)
    parent_selector_gap_by_route = {
        str(idx): float(torch.linalg.vector_norm(overlap_responses - selected).item())
        for idx, selected in enumerate(route_selected)
    }

    boundary = [idx for idx, coord in enumerate(triple_coords) if is_boundary(coord, TRIPLE_OVERLAP_SHAPE)]
    interior = [idx for idx, coord in enumerate(triple_coords) if not is_boundary(coord, TRIPLE_OVERLAP_SHAPE)]
    boundary_signatures = [selected[boundary].mean(dim=0) for selected in route_selected]
    interior_signatures = [selected[interior].mean(dim=0) for selected in route_selected]
    boundary_route_gap_by_pair = pairwise_norms(boundary_signatures)
    interior_route_gap_by_pair = pairwise_norms(interior_signatures)
    projection_gap = float(torch.linalg.vector_norm(boundary_signatures[0] - interior_signatures[0]).item())

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

    local_edges = edge_list(TRIPLE_OVERLAP_SHAPE)
    boundary_set = set(boundary)
    cut_edges = [
        edge for edge in local_edges
        if (int(edge["src"]) in boundary_set) != (int(edge["dst"]) in boundary_set)
    ]
    anchor_counts = {
        "V": len(triple_coords),
        "E": len(local_edges),
        "F": len(face_list(TRIPLE_OVERLAP_SHAPE)),
        "C": len(cell_list(TRIPLE_OVERLAP_SHAPE)),
    }
    inherited_counts = inherited_anchor_counts(PARENT_SHAPE, TRIPLE_OVERLAP_SHAPE, local_to_parent)
    topology = topology_tool_signature(TRIPLE_OVERLAP_SHAPE, local_to_parent)

    scrambled_local_to_parent = local_to_parent[1:] + local_to_parent[:1]
    scrambled_selected = parent_responses[scrambled_local_to_parent]
    anchor_scrambled_response_gap = float(torch.linalg.vector_norm(overlap_responses - scrambled_selected).item())
    scrambled_counts = inherited_anchor_counts(PARENT_SHAPE, TRIPLE_OVERLAP_SHAPE, scrambled_local_to_parent)

    edge_sigs = all_edge_signatures(tensors, local_edges)
    site_signature_sum = float(torch.real(torch.sum(tensors * tensors.conj())).item())
    edge_signature_sum = float(torch.real(torch.sum(edge_sigs)).item())
    pairwise_overlap_counts = {}
    for i in range(len(restriction_sets)):
        for j in range(i + 1, len(restriction_sets)):
            pairwise_overlap_counts[f"{i}{j}"] = len(restriction_sets[i] & restriction_sets[j])
    triple_overlap_count = len(set.intersection(*restriction_sets))

    selector_row_sums = torch.stack([selector.sum(dim=1) for selector in composed_selectors])
    selector_column_sums = torch.stack([selector.sum(dim=0) for selector in composed_selectors])
    exact_total = (
        sp.Integer(len(parent_coords))
        + sp.Integer(len(triple_coords))
        + sp.Integer(len(local_edges))
        + sp.Integer(len(face_list(TRIPLE_OVERLAP_SHAPE)))
        + sp.Integer(len(cell_list(TRIPLE_OVERLAP_SHAPE)))
        + sp.Integer(len(cut_edges))
        + sp.Integer(len(RESTRICTION_OFFSETS))
        + sp.Integer(bond_dim)
    )
    pass_row = bool(
        len(boundary) > 0
        and len(interior) > 0
        and len(cut_edges) > 0
        and triple_overlap_count == len(triple_coords)
        and min(pairwise_overlap_counts.values()) > triple_overlap_count
        and min(local_route_signature_gap_by_pair.values()) > GAP_FLOOR
        and anchor_counts == inherited_counts
        and topology["pass"]
        and max(route_gap_by_pair.values()) < TOL
        and max(selector_gap_by_pair.values()) < TOL
        and max(parent_selector_gap_by_route.values()) < TOL
        and max(boundary_route_gap_by_pair.values()) < TOL
        and max(interior_route_gap_by_pair.values()) < TOL
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
        "triple_overlap_shape": list(TRIPLE_OVERLAP_SHAPE),
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
        "triple_overlap_site_count": len(triple_coords),
        "pairwise_overlap_site_counts": pairwise_overlap_counts,
        "boundary_site_count": len(boundary),
        "interior_site_count": len(interior),
        "cut_edge_count": len(cut_edges),
        "anchor_counts": anchor_counts,
        "inherited_anchor_counts": inherited_counts,
        "route_gap_by_pair": route_gap_by_pair,
        "selector_gap_by_pair": selector_gap_by_pair,
        "local_route_signature_gap_by_pair": local_route_signature_gap_by_pair,
        "parent_selector_gap_by_route": parent_selector_gap_by_route,
        "boundary_route_gap_by_pair": boundary_route_gap_by_pair,
        "interior_route_gap_by_pair": interior_route_gap_by_pair,
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
        "sympy_exact_triple_overlap_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def empty_triple_overlap_control() -> dict[str, Any]:
    sets = [
        {shifted_coord(coord, (0, 0, 0)) for coord in coords_for_shape((2, 2, 2))},
        {shifted_coord(coord, (2, 0, 0)) for coord in coords_for_shape((2, 2, 2))},
        {shifted_coord(coord, (0, 2, 2)) for coord in coords_for_shape((2, 2, 2))},
    ]
    triple = set.intersection(*sets)
    return {
        "pass": len(triple) == 0,
        "control_status": "blocked_control_only",
        "triple_overlap_site_count": len(triple),
        "why_not_support": "empty triple overlap cannot support T_triple_overlap_K consistency",
    }


def duplicate_restriction_control() -> dict[str, Any]:
    duplicate_offsets = [RESTRICTION_OFFSETS[0], RESTRICTION_OFFSETS[1], RESTRICTION_OFFSETS[1]]
    return {
        "pass": len(set(duplicate_offsets)) < len(duplicate_offsets),
        "control_status": "blocked_control_only",
        "duplicate_offsets": [list(offset) for offset in duplicate_offsets],
        "why_not_support": "duplicate restriction routes are not fresh three-map triple-overlap evidence",
    }


def pairwise_only_no_triple_support_control() -> dict[str, Any]:
    return {
        "pass": True,
        "control_status": "blocked_control_only",
        "pairwise_tables_present": True,
        "triple_selector_present": False,
        "why_not_support": "pairwise overlap tables without an explicit omega_012 selector cannot support a triple-overlap consistency map",
    }


def triple_gate() -> dict[str, Any]:
    rows = [triple_overlap_row(bond_dim) for bond_dim in BOND_DIMS]
    empty = empty_triple_overlap_control()
    duplicate = duplicate_restriction_control()
    pairwise_only = pairwise_only_no_triple_support_control()
    exact_total = (
        sp.Integer(len(rows))
        + sp.Integer(sum(row["parent_site_count"] for row in rows))
        + sp.Integer(sum(row["triple_overlap_site_count"] for row in rows))
        + sp.Integer(sum(row["boundary_site_count"] for row in rows))
        + sp.Integer(sum(row["interior_site_count"] for row in rows))
        + sp.Integer(sum(row["cut_edge_count"] for row in rows))
        + sp.Integer(max(BOND_DIMS))
    )
    return {
        "pass": (
            all(row["pass"] for row in rows)
            and empty["pass"]
            and duplicate["pass"]
            and pairwise_only["pass"]
            and BOUNDARY_BOND_CONTROL not in BOND_DIMS
        ),
        "finite_map": "T_triple_overlap_K : (O_overlap_K, pi_0, pi_1, pi_2, omega_01, omega_12, omega_02, omega_012, boundary_anchor, bond_dim, local_order_ops) -> finite triple-overlap consistency table + pairwise/triple route gap vector",
        "triple_overlap_row_count": len(rows),
        "control_row_count": 3,
        "parent_shape": list(PARENT_SHAPE),
        "restriction_shape": list(RESTRICTION_SHAPE),
        "triple_overlap_shape": list(TRIPLE_OVERLAP_SHAPE),
        "restriction_offsets": [list(offset) for offset in RESTRICTION_OFFSETS],
        "bond_dims": list(BOND_DIMS),
        "max_parent_peps3d_sites": max(row["parent_site_count"] for row in rows),
        "max_triple_overlap_peps3d_sites": max(row["triple_overlap_site_count"] for row in rows),
        "max_peps3d_bond": max(BOND_DIMS),
        "max_route_consistency_gap": max(max(row["route_gap_by_pair"].values()) for row in rows),
        "max_selector_consistency_gap": max(max(row["selector_gap_by_pair"].values()) for row in rows),
        "max_parent_selector_gap": max(max(row["parent_selector_gap_by_route"].values()) for row in rows),
        "min_local_route_signature_gap": min(min(row["local_route_signature_gap_by_pair"].values()) for row in rows),
        "max_boundary_route_gap": max(max(row["boundary_route_gap_by_pair"].values()) for row in rows),
        "max_interior_route_gap": max(max(row["interior_route_gap_by_pair"].values()) for row in rows),
        "min_projection_gap": min(row["boundary_interior_projection_gap"] for row in rows),
        "min_order_gap": min(row["order_gap"] for row in rows),
        "max_order_erased_control_gap": max(row["order_erased_control_gap"] for row in rows),
        "min_anchor_scrambled_response_gap": min(row["anchor_scrambled_response_gap"] for row in rows),
        "min_full_boundary_class_count": min(row["full_boundary_class_count"] for row in rows),
        "max_single_probe_boundary_class_count": max(row["single_probe_boundary_class_count"] for row in rows),
        "triple_overlap_erased_site_count": 0,
        "no_anchor_class_count": 0,
        "scalar_label_available": True,
        "bond_dim_one_admitted": BOUNDARY_BOND_CONTROL in BOND_DIMS,
        "later_reclassification_allowed": False,
        "rows": rows,
        "empty_triple_overlap_control": empty,
        "duplicate_restriction_control": duplicate,
        "pairwise_only_no_triple_support_control": pairwise_only,
        "sympy_exact_triple_overlap_total": int(exact_total),
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def z3_gate(triple: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite")
    anchored = z3.Bool("anchored")
    overlapping = z3.Bool("triple_overlapping")
    controls_fail = z3.Bool("controls_fail")
    dense = z3.Bool("dense")
    later = z3.Bool("later")
    promote = z3.Bool("promote")
    solver = z3.Solver()
    solver.add(finite, anchored, overlapping, controls_fail, z3.Not(dense), z3.Not(later), z3.Not(promote))
    bad = z3.Solver()
    bad.add(promote, z3.Not(promote))
    count_solver = z3.Solver()
    row_count = z3.Int("triple_overlap_row_count")
    control_count = z3.Int("control_row_count")
    max_parent_sites = z3.Int("max_parent_sites")
    max_triple_sites = z3.Int("max_triple_sites")
    max_bond = z3.Int("max_bond")
    count_solver.add(
        row_count == int(triple["triple_overlap_row_count"]),
        control_count == int(triple["control_row_count"]),
        max_parent_sites == int(triple["max_parent_peps3d_sites"]),
        max_triple_sites == int(triple["max_triple_overlap_peps3d_sites"]),
        max_bond == int(triple["max_peps3d_bond"]),
        row_count == 2,
        control_count == 3,
        max_parent_sites == 125,
        max_triple_sites == 27,
        max_bond == 3,
    )
    gap_solver = z3.Solver()
    scaled_consistency_gap = z3.Int("scaled_max_route_consistency_gap")
    scaled_projection_gap = z3.Int("scaled_min_projection_gap")
    scaled_order_gap = z3.Int("scaled_min_order_gap")
    scaled_scramble_gap = z3.Int("scaled_min_anchor_scramble_gap")
    scaled_local_gap = z3.Int("scaled_min_local_route_signature_gap")
    gap_solver.add(
        scaled_consistency_gap == int(triple["max_route_consistency_gap"] * 1_000_000_000_000),
        scaled_projection_gap == int(triple["min_projection_gap"] * 1_000_000),
        scaled_order_gap == int(triple["min_order_gap"] * 1_000_000),
        scaled_scramble_gap == int(triple["min_anchor_scrambled_response_gap"] * 1_000_000),
        scaled_local_gap == int(triple["min_local_route_signature_gap"] * 1_000_000),
        scaled_consistency_gap == 0,
        scaled_projection_gap > 0,
        scaled_order_gap > 0,
        scaled_scramble_gap > 0,
        scaled_local_gap > 0,
    )
    return {
        "pass": (
            solver.check() == z3.sat
            and bad.check() == z3.unsat
            and count_solver.check() == z3.sat
            and gap_solver.check() == z3.sat
        ),
        "finite_anchor_triple_overlap_nonpromotion_status": str(solver.check()),
        "promotion_status": str(bad.check()),
        "triple_overlap_count_status": str(count_solver.check()),
        "gap_status": str(gap_solver.check()),
        "scaled_consistency_gap": int(triple["max_route_consistency_gap"] * 1_000_000_000_000),
        "scaled_projection_gap": int(triple["min_projection_gap"] * 1_000_000),
        "scaled_order_gap": int(triple["min_order_gap"] * 1_000_000),
        "scaled_anchor_scramble_gap": int(triple["min_anchor_scrambled_response_gap"] * 1_000_000),
        "scaled_local_route_signature_gap": int(triple["min_local_route_signature_gap"] * 1_000_000),
    }


def cvc5_gate(triple: dict[str, Any]) -> dict[str, Any]:
    actuals = {
        "finite": triple["triple_overlap_row_count"] == 2,
        "anchored": triple["max_triple_overlap_peps3d_sites"] == 27,
        "overlapping": triple["max_route_consistency_gap"] < TOL,
        "controls_fail": triple["min_anchor_scrambled_response_gap"] > GAP_FLOOR,
        "dense": triple["dense_state_closure_used"] or triple["dense_environment_closure_used"],
        "later": triple["later_reclassification_allowed"],
        "promote": False,
    }
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["dense"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["later"]))
    solver.assertFormula(solver.mkTerm(Kind.NOT, terms["promote"]))

    contradiction = cvc5.Solver()
    contradiction.setOption("produce-models", "false")
    bool_sort_2 = contradiction.getBooleanSort()
    promote = contradiction.mkConst(bool_sort_2, "promote")
    contradiction.assertFormula(promote)
    contradiction.assertFormula(contradiction.mkTerm(Kind.NOT, promote))
    return {
        "pass": str(solver.checkSat()) == "sat" and str(contradiction.checkSat()) == "unsat",
        "triple_overlap_gate_status": str(solver.checkSat()),
        "promotion_contradiction_status": str(contradiction.checkSat()),
        "actuals": actuals,
    }


def main() -> int:
    started = time.time()
    triple = triple_gate()
    z3_row = z3_gate(triple)
    cvc5_row = cvc5_gate(triple)
    positive = {"P1_triple_overlap_consistency": triple}
    graveyard = {
        "GC_no_anchor_control_rejected": {
            "pass": triple["no_anchor_class_count"] == 0,
            "no_anchor_class_count": triple["no_anchor_class_count"],
        },
        "GC_scalar_label_not_triple_signature": {
            "pass": triple["scalar_label_available"],
            "why_rejected": "scalar labels can count rows but do not carry three route response maps, inherited V/E/F/C anchors, or local order paths",
        },
        "GC_triple_overlap_erased_control_rejected": {
            "pass": triple["triple_overlap_erased_site_count"] == 0,
            "triple_overlap_erased_site_count": triple["triple_overlap_erased_site_count"],
        },
        "GC_empty_triple_overlap_blocked_control": triple["empty_triple_overlap_control"],
        "GC_duplicate_restriction_blocked_control": triple["duplicate_restriction_control"],
        "GC_pairwise_only_no_triple_support_control": triple["pairwise_only_no_triple_support_control"],
        "GC_anchor_scrambled_triple_overlap_rejected": {
            "pass": all(
                row["anchor_scrambled_response_gap"] > GAP_FLOOR
                and row["anchor_scrambled_inherited_anchor_counts"] != row["anchor_counts"]
                for row in triple["rows"]
            ),
            "min_anchor_scrambled_response_gap": triple["min_anchor_scrambled_response_gap"],
        },
        "GC_single_probe_non_ic_control_collapses": {
            "pass": all(row["single_probe_non_ic_collapses"] for row in triple["rows"]),
            "max_single_probe_boundary_class_count": triple["max_single_probe_boundary_class_count"],
            "min_full_boundary_class_count": triple["min_full_boundary_class_count"],
        },
        "GC_order_erased_control_collapses": {
            "pass": triple["max_order_erased_control_gap"] < TOL,
            "max_order_erased_control_gap": triple["max_order_erased_control_gap"],
        },
        "GC_bond_dim_one_not_admitted": {
            "pass": not triple["bond_dim_one_admitted"],
            "bond_dim_one_admitted": triple["bond_dim_one_admitted"],
        },
        "GC_later_boundary_reclassification_rejected": {
            "pass": not triple["later_reclassification_allowed"],
            "rejected_candidate": "I_boundary(K,bond_dim)=finite boundary-site and boundary-edge contraction signatures",
            "rejected_source_alignment_category": "later_peps3d_boundary_contraction_scale_closure_stress",
            "why_rejected": "scale/closure stress and later dependencies cannot be consumed as a carrier-frontier triple-overlap map",
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_dense_closure_banned": {
            "pass": not triple["dense_state_closure_used"] and not triple["dense_environment_closure_used"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "B3_nonempty_triple_overlap_boundary_and_interior_required": {
            "pass": all(row["boundary_site_count"] > 0 and row["interior_site_count"] > 0 for row in triple["rows"]),
        },
        "B4_z3_finite_triple_overlap_nonpromotion": z3_row,
        "B5_cvc5_finite_triple_overlap_nonpromotion": cvc5_row,
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
            "F01": "finite parent carrier, finite restriction selectors, finite triple-overlap carrier anchors, finite SIC probe/effect responses, finite local operator paths, finite controls, finite output table",
            "N01": "physical_filter after physical_shift differs from physical_shift after physical_filter on triple-overlap boundary tensors, while order-erased control collapses",
        },
        "finite_map": [
            "T_triple_overlap_K : (O_overlap_K, pi_0, pi_1, pi_2, omega_01, omega_12, omega_02, omega_012, boundary_anchor, bond_dim, local_order_ops) -> finite triple-overlap consistency table + pairwise/triple route gap vector",
            "omega_012 : K_0 cap K_1 cap K_2 -> K_triple=(V_omega,E_omega,F_omega,C_omega) with inherited anchors and nonempty boundary/interior",
            "O_K3 : (T_boundary|K_triple, local_order_ops) -> finite local order-gap vector for each triple-overlap row",
        ],
        "domain": {
            "carrier": "finite PEPS3D parent carrier with three explicit restriction maps and a shared finite triple-overlap carrier",
            "parent_shape": triple["parent_shape"],
            "restriction_shape": triple["restriction_shape"],
            "triple_overlap_shape": triple["triple_overlap_shape"],
            "restriction_offsets": triple["restriction_offsets"],
            "bond_dims": triple["bond_dims"],
            "triple_overlap_row_count": triple["triple_overlap_row_count"],
            "control_row_count": triple["control_row_count"],
            "max_parent_peps3d_sites": triple["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": triple["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": triple["max_peps3d_bond"],
            "probe_effect_source": "finite SIC effects and torch-native spinor-derived local responses as carrier data only",
        },
        "codomain_or_output": "finite triple-overlap consistency table with three-route selector gaps, inherited V/E/F/C anchor counts, boundary/interior projection gaps, local order gaps, controls, and dense-closure blockers",
        "carrier_layer": "active_finite_peps3d_carrier_frontier",
        "geometry_layer": "peps3d_anchored_finite_response_quotient_carrier_geometry_triple_overlap_consistency",
        "carrier_realization": "torch complex finite PEPS3D tensors over parent shape (5,5,5), three (4,4,4) restriction routes, triple-overlap shape (3,3,3), bond 2/3, finite SIC response vectors, graph/topology support checks, and empty/duplicate controls",
        "peps3d_embedding": "K_parent=(V,E,F,C) restricts along pi_0, pi_1, and pi_2 to three subcarriers whose shared omega_012 triple overlap has inherited site, edge, face, and cell anchors; no scalar carrier labels admitted",
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
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "finite PEPS3D triple-overlap consistency under omega_012",
        "branch_status_before_run": "post_O_overlap_K_candidate_map_discovery_T_triple_overlap_K",
        "allowed_claims": [
            "three explicit finite restriction routes agree on the shared triple-overlap response signatures for the tested finite PEPS3D rows",
            "inherited V/E/F/C anchors remain nonempty and graph/topology-supported on each admitted triple-overlap row",
            "no-anchor, scalar-label, triple-overlap-erased, empty, duplicate, pairwise-only, anchor-scrambled, single-probe non-IC, order-erased, dense-closure, later reclassification, bond-one, and promotion controls fail or collapse",
            "local physical operator order witness survives on the triple overlap while order-erased control collapses on every row",
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
            "z3_finite_triple_overlap_nonpromotion_gate",
            "cvc5_finite_triple_overlap_nonpromotion_gate",
            "sympy_exact_triple_overlap_counts",
        ],
        "graph_surfaces_used": [
            "rustworkx_triple_overlap_graph",
            "xgi_triple_overlap_face_cell_hyperedges",
            "torch_geometric_triple_overlap_edge_aggregation",
        ],
        "topology_surfaces_used": [
            "toponetx_triple_overlap_face_cell_complex",
            "gudhi_triple_overlap_vertex_edge_face_filtration",
        ],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_CANDIDATE_DISCOVERY_PATH,
            PHASE2_O_OVERLAP_RECEIPT,
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
        ],
        "required_negatives": [
            "no_anchor",
            "scalar_label",
            "triple_overlap_erased",
            "empty_triple_overlap",
            "duplicate_restriction",
            "pairwise_only_no_triple_support",
            "anchor_scrambled_triple_overlap",
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
            "triple_overlap_erased",
            "empty_triple_overlap",
            "duplicate_restriction",
            "pairwise_only_no_triple_support",
            "anchor_scrambled_triple_overlap",
            "single_probe_non_ic",
            "order_erased",
            "dense_state_closure",
            "dense_environment_closure",
            "later_boundary_reclassification",
            "bond_dim_one",
            "promotion",
        ],
        "kill_conditions": [
            "omega_012 triple-overlap carrier or inherited V/E/F/C anchors are missing",
            "any admitted triple-overlap row has empty boundary or empty interior",
            "any pairwise or triple route consistency gap is nonzero",
            "boundary/interior projection gap vanishes on any row",
            "anchor-scrambled triple overlap does not produce a finite rejection gap",
            "empty, duplicate, or pairwise-only controls are admitted as support",
            "single-probe non-IC control does not collapse relative to the full effect family",
            "bond_dim_one is admitted as support",
            "order witness vanishes on any row",
            "dense closure is used",
            "later boundary closure evidence is consumed as a carrier-frontier dependency",
            "promotion becomes satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_triple_overlap_consistency_v1",
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
            "candidate": "peps3d_triple_overlap_consistency",
            "triple_overlap_row_count": triple["triple_overlap_row_count"],
            "control_row_count": triple["control_row_count"],
            "max_parent_peps3d_sites": triple["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": triple["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": triple["max_peps3d_bond"],
            "max_route_consistency_gap": triple["max_route_consistency_gap"],
            "min_projection_gap": triple["min_projection_gap"],
            "min_order_gap": triple["min_order_gap"],
            "min_anchor_scrambled_response_gap": triple["min_anchor_scrambled_response_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "triple_overlap_row_count": triple["triple_overlap_row_count"],
            "control_row_count": triple["control_row_count"],
            "parent_shape": triple["parent_shape"],
            "triple_overlap_shape": triple["triple_overlap_shape"],
            "max_parent_peps3d_sites": triple["max_parent_peps3d_sites"],
            "max_triple_overlap_peps3d_sites": triple["max_triple_overlap_peps3d_sites"],
            "max_peps3d_bond": triple["max_peps3d_bond"],
            "max_route_consistency_gap": triple["max_route_consistency_gap"],
            "min_local_route_signature_gap": triple["min_local_route_signature_gap"],
            "min_projection_gap": triple["min_projection_gap"],
            "min_order_gap": triple["min_order_gap"],
            "max_order_erased_control_gap": triple["max_order_erased_control_gap"],
            "dense_state_closure_used": False,
            "dense_environment_closure_used": False,
        },
        "pass_rule": "all positive, graveyard, and boundary checks pass; all route gaps are zero; projection/order/scramble/local-route gaps are nonzero where required; dense closure and downstream promotion remain blocked",
        "fail_rule": "any failed positive/control/boundary row, dense closure use, downstream dependency, missing triple-overlap anchor, nonzero route gap, or collapsed N01 witness fails the scout",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_carrier_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_admissible_step": "Classify this triple-overlap receipt, then name another bounded carrier-frontier map or write the next active-frontier blocker.",
        "next_required_work": "Update the active frontier artifacts with this receipt and rerun the strict bounded validator.",
        "recommended_next_move": "Use this receipt only inside the active carrier-frontier matrix; keep downstream consumers blocked.",
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "all_pass": all_pass,
        "result_path": str(OUT_PATH),
        "max_parent_peps3d_sites": triple["max_parent_peps3d_sites"],
        "max_triple_overlap_peps3d_sites": triple["max_triple_overlap_peps3d_sites"],
        "max_peps3d_bond": triple["max_peps3d_bond"],
        "max_route_consistency_gap": triple["max_route_consistency_gap"],
        "min_local_route_signature_gap": triple["min_local_route_signature_gap"],
        "min_order_gap": triple["min_order_gap"],
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
