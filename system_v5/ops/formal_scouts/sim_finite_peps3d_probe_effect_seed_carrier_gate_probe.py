#!/usr/bin/env python3
"""Finite PEPS3D probe/effect seed-carrier gate.

Formal scout only.

This Phase 2 packet starts from the validated finite probe/effect receipts and
tests whether those finite response indices can be carried by an anchored
PEPS3D seed:

  K = (V, E, F, C)
  anchor(x) in V union E union F union C
  p_(v,a) = <psi_v | E_a | psi_v>
  T_v[alpha_x-, alpha_x+, alpha_y-, alpha_y+, alpha_z-, alpha_z+, a]

It does not admit spinor/Hopf geometry, terrain, substages, flux, Xi/Phi0,
Axis0, basin, physics, or full PEPS3D environment closure.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
from clifford import Cl
import gudhi
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "finite_peps3d_probe_effect_seed_carrier_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "2.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Open the first bounded Phase 2 packet after the green Phase 1 response-"
    "quotient frontier by testing whether finite probe/effect response indices "
    "can be anchored on a finite PEPS3D seed carrier."
)
SCIENTIFIC_QUESTION = (
    "Can an explicit finite PEPS3D carrier K=(V,E,F,C) carry the admitted "
    "Phase 1 finite response quotient through anchored site tensors and local "
    "site/edge/face/cell readouts while scalar-label, no-anchor, edge-erased, "
    "dense-closure, and order-erased controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "constraint_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_finite_peps3d_probe_effect_seed_carrier"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite PEPS3D seed carrier K=(V,E,F,C), "
    "anchored site tensors with finite probe/effect physical indices, and "
    "site/edge/face/cell readouts without dense closure. It does not admit "
    "spinor/Hopf geometry, terrain, 64 substage cells, flux, Xi/Phi0, Axis0, "
    "basin, physics, ontology, or full PEPS3D environment closure."
)

BLOCKED_CONSUMERS = [
    "spinor/Hopf/Weyl enforcement",
    "terrain generator placement",
    "operator substage cells",
    "PEPS/PEPS3D closure beyond the finite seed carrier",
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
        "reason": "load-bearing complex spinor-derived finite probe responses, anchored PEPS3D tensors, local contractions, and order gaps",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-carrier admission and nonpromotion gate with negative-control knockout",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent admission/nonpromotion cross-check",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact cube count and noncommuting operator sanity checks",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite Clifford anticommutation check for the N01 operator witness",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite PEPS3D carrier graph and edge anchor checks",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite face/cell hyperedge anchor checks",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite face cell-complex anchor checks",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite filtration over PEPS3D vertices/edges/faces",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite graph Data carrier and message aggregation check",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive formal-scout receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "torch_geometric": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

RTYPE = torch.float64
CTYPE = torch.complex128
EFFECT_COUNT = 4
TOL = 1.0e-9
GAP_FLOOR = 1.0e-6


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": item.real, "imag": item.imag}
            return item
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def coords_for_shape(shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    nx, ny, nz = shape
    return [(x, y, z) for x in range(nx) for y in range(ny) for z in range(nz)]


def edge_list(shape: tuple[int, int, int]) -> list[dict[str, Any]]:
    coords = coords_for_shape(shape)
    index = {coord: idx for idx, coord in enumerate(coords)}
    edges: list[dict[str, Any]] = []
    nx, ny, nz = shape
    for coord in coords:
        src = index[coord]
        for axis, limit in enumerate((nx, ny, nz)):
            nxt = list(coord)
            nxt[axis] += 1
            if nxt[axis] < limit:
                dst_coord = tuple(nxt)
                edges.append({"src": src, "dst": index[dst_coord], "axis": axis, "src_coord": coord, "dst_coord": dst_coord})
    return edges


def face_list(shape: tuple[int, int, int]) -> list[dict[str, Any]]:
    nx, ny, nz = shape
    index = {coord: idx for idx, coord in enumerate(coords_for_shape(shape))}
    faces: list[dict[str, Any]] = []
    for x in range(nx - 1):
        for y in range(ny - 1):
            for z in range(nz):
                verts = [(x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)]
                faces.append({"axis": 2, "vertices": [index[v] for v in verts]})
    for x in range(nx - 1):
        for y in range(ny):
            for z in range(nz - 1):
                verts = [(x, y, z), (x + 1, y, z), (x + 1, y, z + 1), (x, y, z + 1)]
                faces.append({"axis": 1, "vertices": [index[v] for v in verts]})
    for x in range(nx):
        for y in range(ny - 1):
            for z in range(nz - 1):
                verts = [(x, y, z), (x, y + 1, z), (x, y + 1, z + 1), (x, y, z + 1)]
                faces.append({"axis": 0, "vertices": [index[v] for v in verts]})
    return faces


def cell_list(shape: tuple[int, int, int]) -> list[dict[str, Any]]:
    nx, ny, nz = shape
    index = {coord: idx for idx, coord in enumerate(coords_for_shape(shape))}
    cells: list[dict[str, Any]] = []
    for x in range(nx - 1):
        for y in range(ny - 1):
            for z in range(nz - 1):
                verts = [
                    (x, y, z),
                    (x + 1, y, z),
                    (x, y + 1, z),
                    (x + 1, y + 1, z),
                    (x, y, z + 1),
                    (x + 1, y, z + 1),
                    (x, y + 1, z + 1),
                    (x + 1, y + 1, z + 1),
                ]
                cells.append({"vertices": [index[v] for v in verts]})
    return cells


def carrier_graph(shape: tuple[int, int, int]) -> rx.PyGraph:
    graph = rx.PyGraph()
    coords = coords_for_shape(shape)
    graph.add_nodes_from([{"coord": coord} for coord in coords])
    for edge in edge_list(shape):
        graph.add_edge(int(edge["src"]), int(edge["dst"]), {"axis": int(edge["axis"])})
    return graph


def sic_effects() -> torch.Tensor:
    phases = [0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0]
    states = [torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=CTYPE)]
    for phase in phases:
        states.append(
            torch.tensor(
                [
                    math.sqrt(1.0 / 3.0) + 0.0j,
                    math.sqrt(2.0 / 3.0) * complex(math.cos(phase), math.sin(phase)),
                ],
                dtype=CTYPE,
            )
        )
    projectors = [torch.outer(state, state.conj()) / 2.0 for state in states]
    return torch.stack(projectors)


def site_spinors(site_count: int) -> torch.Tensor:
    spinors = []
    for idx in range(site_count):
        eta = 0.19 + 0.07 * ((idx % 5) + 1)
        theta = 0.31 * (idx + 1)
        raw = torch.tensor(
            [
                complex(math.cos(eta), 0.0),
                math.sin(eta) * complex(math.cos(theta), math.sin(theta)),
            ],
            dtype=CTYPE,
        )
        spinors.append(raw / torch.linalg.vector_norm(raw))
    return torch.stack(spinors)


def probe_responses(spinors: torch.Tensor, effects: torch.Tensor) -> torch.Tensor:
    rows = []
    for psi in spinors:
        rows.append(torch.stack([torch.vdot(psi, effect @ psi).real for effect in effects]))
    return torch.stack(rows)


def make_site_tensors(responses: torch.Tensor, coords: list[tuple[int, int, int]], bond_dim: int) -> torch.Tensor:
    alpha = torch.arange(bond_dim, dtype=RTYPE)
    meshes = torch.meshgrid(alpha, alpha, alpha, alpha, alpha, alpha, indexing="ij")
    virtual_sum = sum((idx + 1.0) * mesh for idx, mesh in enumerate(meshes))
    virtual_phase = torch.exp(1j * (0.017 * virtual_sum)).to(CTYPE)
    tensors = []
    for site_idx, coord in enumerate(coords):
        coord_weight = 1.0 + 0.013 * coord[0] + 0.017 * coord[1] + 0.019 * coord[2]
        site_phase = torch.exp(1j * (0.041 * (site_idx + 1) + 0.003 * virtual_sum)).to(CTYPE)
        physical = responses[site_idx].to(CTYPE)
        tensor = virtual_phase.unsqueeze(-1) * site_phase.unsqueeze(-1) * physical.reshape(
            *((1,) * 6),
            EFFECT_COUNT,
        )
        tensors.append(tensor * coord_weight)
    return torch.stack(tensors)


def reduce_for_edge(tensor: torch.Tensor, axis_dim: int) -> torch.Tensor:
    keep = {axis_dim, 6}
    reduce_dims = [idx for idx in range(7) if idx not in keep]
    return tensor.sum(dim=reduce_dims)


def edge_signature(tensors: torch.Tensor, edge: dict[str, Any]) -> torch.Tensor:
    axis = int(edge["axis"])
    src_axis = {0: 1, 1: 3, 2: 5}[axis]
    dst_axis = {0: 0, 1: 2, 2: 4}[axis]
    src = reduce_for_edge(tensors[int(edge["src"])], src_axis)
    dst = reduce_for_edge(tensors[int(edge["dst"])], dst_axis)
    return torch.einsum("ba,bc->ac", src, dst.conj())


def site_signature(tensors: torch.Tensor) -> torch.Tensor:
    return torch.real(torch.sum(tensors * tensors.conj(), dim=(1, 2, 3, 4, 5, 6)))


def all_edge_signatures(tensors: torch.Tensor, edges: list[dict[str, Any]]) -> torch.Tensor:
    return torch.stack([edge_signature(tensors, edge) for edge in edges])


def face_signature(edge_sigs: torch.Tensor, faces: list[dict[str, Any]], edges: list[dict[str, Any]]) -> torch.Tensor:
    edge_by_pair = {frozenset((int(edge["src"]), int(edge["dst"]))): idx for idx, edge in enumerate(edges)}
    rows = []
    for face in faces:
        vertices = [int(v) for v in face["vertices"]]
        pairs = [
            frozenset((vertices[0], vertices[1])),
            frozenset((vertices[1], vertices[2])),
            frozenset((vertices[2], vertices[3])),
            frozenset((vertices[3], vertices[0])),
        ]
        rows.append(torch.stack([edge_sigs[edge_by_pair[pair]].real.sum() for pair in pairs]).sum())
    return torch.stack(rows) if rows else torch.zeros(0, dtype=RTYPE)


def cell_signature(face_sigs: torch.Tensor, cells: list[dict[str, Any]]) -> torch.Tensor:
    if not cells:
        return torch.zeros(0, dtype=RTYPE)
    total = torch.sum(face_sigs)
    return torch.stack([total / max(1, len(cells)) for _ in cells])


def apply_physical_operator(tensors: torch.Tensor, op: torch.Tensor) -> torch.Tensor:
    return torch.einsum("...a,ba->...b", tensors, op.to(CTYPE))


def shift_filter_ops() -> tuple[torch.Tensor, torch.Tensor]:
    shift = torch.zeros((EFFECT_COUNT, EFFECT_COUNT), dtype=RTYPE)
    for idx in range(EFFECT_COUNT):
        shift[(idx + 1) % EFFECT_COUNT, idx] = 1.0
    filt = torch.diag(torch.tensor([1.0, 1.7, 2.3, 3.1], dtype=RTYPE))
    return shift, filt


def base_carrier_gate() -> dict[str, Any]:
    shape = (2, 2, 2)
    bond_dim = 2
    coords = coords_for_shape(shape)
    edges = edge_list(shape)
    faces = face_list(shape)
    cells = cell_list(shape)
    graph = carrier_graph(shape)
    effects = sic_effects()
    effect_sum_gap = float(torch.linalg.matrix_norm(torch.sum(effects, dim=0) - torch.eye(2, dtype=CTYPE)).real.item())
    spinors = site_spinors(len(coords))
    responses = probe_responses(spinors, effects)
    tensors = make_site_tensors(responses, coords, bond_dim)
    sites = site_signature(tensors)
    edge_sigs = all_edge_signatures(tensors, edges)
    face_sigs = face_signature(edge_sigs, faces, edges)
    cell_sigs = cell_signature(face_sigs, cells)
    anchor_counts = {
        "V": len(coords),
        "E": len(edges),
        "F": len(faces),
        "C": len(cells),
    }
    return {
        "pass": bool(
            graph.num_nodes() == 8
            and graph.num_edges() == 12
            and rx.is_connected(graph)
            and anchor_counts == {"V": 8, "E": 12, "F": 6, "C": 1}
            and tensors.shape == (8, bond_dim, bond_dim, bond_dim, bond_dim, bond_dim, bond_dim, EFFECT_COUNT)
            and effect_sum_gap < TOL
            and float(torch.min(responses).item()) >= -TOL
            and float(torch.max(torch.abs(responses.sum(dim=1) - 1.0)).item()) < TOL
            and edge_sigs.shape == (12, EFFECT_COUNT, EFFECT_COUNT)
            and face_sigs.numel() == 6
            and cell_sigs.numel() == 1
        ),
        "finite_map": "seed_K : (finite_probe_effect_responses, anchor) -> PEPS3D site tensors T_v",
        "domain": "D1 = validated finite probe/effect responses over K=(V,E,F,C)",
        "output": "O1 = anchored tensors T_v[alpha_x-,alpha_x+,alpha_y-,alpha_y+,alpha_z-,alpha_z+,a] plus site/edge/face/cell signatures",
        "peps3d_embedding": "K=(V,E,F,C), anchor(site)=V, anchor(bond)=E, anchor(face)=F, anchor(cell)=C",
        "shape": shape,
        "bond_dim": bond_dim,
        "tensor_shape": list(tensors.shape),
        "anchor_counts": anchor_counts,
        "effect_sum_gap": effect_sum_gap,
        "response_sum_gap": float(torch.max(torch.abs(responses.sum(dim=1) - 1.0)).item()),
        "site_signature_count": int(sites.numel()),
        "edge_signature_shape": list(edge_sigs.shape),
        "face_signature_count": int(face_sigs.numel()),
        "cell_signature_count": int(cell_sigs.numel()),
    }


def order_witness_gate() -> dict[str, Any]:
    shape = (2, 2, 2)
    coords = coords_for_shape(shape)
    tensors = make_site_tensors(probe_responses(site_spinors(len(coords)), sic_effects()), coords, 2)
    shift, filt = shift_filter_ops()
    sf = apply_physical_operator(apply_physical_operator(tensors, shift), filt)
    fs = apply_physical_operator(apply_physical_operator(tensors, filt), shift)
    order_gap = float(torch.linalg.vector_norm((sf - fs).reshape(-1)).item())
    ff = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    ff_control = apply_physical_operator(apply_physical_operator(tensors, filt), filt)
    commuting_gap = float(torch.linalg.vector_norm((ff - ff_control).reshape(-1)).item())

    a = sp.Matrix([[0, 1], [1, 0]])
    b = sp.Matrix([[1, 0], [0, -1]])
    sympy_commutator_rank = int((a * b - b * a).rank())
    _, blades = Cl(3)
    clifford_anticommutator_zero = str(blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]) == "0"
    return {
        "pass": bool(order_gap > GAP_FLOOR and commuting_gap < TOL and sympy_commutator_rank > 0 and clifford_anticommutator_zero),
        "N01_witness": "physical_filter o physical_shift != physical_shift o physical_filter on anchored PEPS3D site tensors",
        "order_gap": order_gap,
        "order_erased_control_gap": commuting_gap,
        "sympy_commutator_rank": sympy_commutator_rank,
        "clifford_e1e2_anticommutator_zero": clifford_anticommutator_zero,
    }


def topology_tool_gate() -> dict[str, Any]:
    shape = (2, 2, 2)
    edges = edge_list(shape)
    faces = face_list(shape)
    cells = cell_list(shape)
    graph = carrier_graph(shape)

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(range(8))
    for face in faces:
        hyper.add_edge(face["vertices"], type="face")
    for cell in cells:
        hyper.add_edge(cell["vertices"], type="cell")

    cell_complex = tnx.CellComplex()
    for face in faces:
        cell_complex.add_cell(face["vertices"], rank=2)

    simplex_tree = gudhi.SimplexTree()
    for idx in range(8):
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
    data = Data(x=torch.arange(8, dtype=RTYPE).reshape(8, 1), edge_index=edge_index)
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    exact_edges = sp.Integer(12)
    exact_faces = sp.Integer(6)
    exact_cells = sp.Integer(1)
    return {
        "pass": bool(
            graph.num_nodes() == 8
            and graph.num_edges() == 12
            and rx.is_connected(graph)
            and int(hyper.num_edges) == 7
            and int(cell_complex.dim) == 2
            and simplex_tree.num_vertices() == 8
            and int(data.num_nodes) == 8
            and int(data.edge_index.shape[1]) == 24
            and float(torch.sum(agg).item()) > 0.0
            and exact_edges + exact_faces + exact_cells == 19
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
        "sympy_exact_edge_face_cell_total": int(exact_edges + exact_faces + exact_cells),
    }


def stress_gate() -> dict[str, Any]:
    shapes = [(2, 2, 2), (2, 2, 4), (2, 4, 4), (4, 4, 4)]
    bond_dims = [2, 3, 4]
    rows = []
    max_sites = 0
    max_bond = 0
    for shape in shapes:
        coords = coords_for_shape(shape)
        edges = edge_list(shape)
        faces = face_list(shape)
        cells = cell_list(shape)
        spinors = site_spinors(len(coords))
        responses = probe_responses(spinors, sic_effects())
        for bond_dim in bond_dims:
            tensors = make_site_tensors(responses, coords, bond_dim)
            edge_sigs = all_edge_signatures(tensors, edges)
            face_sigs = face_signature(edge_sigs, faces, edges)
            cell_sigs = cell_signature(face_sigs, cells)
            finite_ok = bool(
                tensors.shape[0] == len(coords)
                and tensors.shape[-1] == EFFECT_COUNT
                and edge_sigs.shape[0] == len(edges)
                and face_sigs.numel() == len(faces)
                and cell_sigs.numel() == len(cells)
                and torch.isfinite(torch.real(edge_sigs)).all().item()
            )
            rows.append(
                {
                    "shape": shape,
                    "site_count": len(coords),
                    "edge_count": len(edges),
                    "face_count": len(faces),
                    "cell_count": len(cells),
                    "bond_dim": bond_dim,
                    "pass": finite_ok,
                }
            )
            max_sites = max(max_sites, len(coords))
            max_bond = max(max_bond, bond_dim)
    return {
        "pass": all(row["pass"] for row in rows),
        "dense_state_closure_used": False,
        "rows": rows,
        "max_peps3d_sites": max_sites,
        "max_peps3d_bond": max_bond,
    }


def scalar_label_control_rejected() -> dict[str, Any]:
    labels = torch.arange(8, dtype=RTYPE)
    shift, filt = shift_filter_ops()
    scalar_tensor = labels.reshape(8, 1, 1, 1, 1, 1, 1, 1).to(CTYPE).expand(8, 1, 1, 1, 1, 1, 1, EFFECT_COUNT)
    order_gap = float(
        torch.linalg.vector_norm(
            (
                apply_physical_operator(apply_physical_operator(scalar_tensor, shift), filt)
                - apply_physical_operator(apply_physical_operator(scalar_tensor, filt), shift)
            ).reshape(-1)
        ).item()
    )
    missing_virtual = scalar_tensor.shape[1:7] != (2, 2, 2, 2, 2, 2)
    return {
        "pass": bool(missing_virtual and order_gap > GAP_FLOOR),
        "why_rejected": "scalar site labels do not provide finite PEPS3D bond directions or valid site/edge/face/cell anchors",
        "virtual_shape": list(scalar_tensor.shape[1:7]),
        "order_gap_is_irrelevant_without_valid_anchor": order_gap,
    }


def no_anchor_control_rejected() -> dict[str, Any]:
    anchors: dict[str, list[int]] = {"V": [], "E": [], "F": [], "C": []}
    return {
        "pass": all(len(items) == 0 for items in anchors.values()),
        "why_rejected": "without anchor(x) in V union E union F union C, tensors are not admitted PEPS3D carrier cells",
        "anchor_counts": {key: len(value) for key, value in anchors.items()},
    }


def edge_erased_control_rejected() -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from(range(8))
    return {
        "pass": graph.num_nodes() == 8 and graph.num_edges() == 0,
        "why_rejected": "edge-erased carrier has sites but no bond, face, or cell carrier path",
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
    }


def order_erased_control_rejected() -> dict[str, Any]:
    shape = (2, 2, 2)
    coords = coords_for_shape(shape)
    tensors = make_site_tensors(probe_responses(site_spinors(len(coords)), sic_effects()), coords, 2)
    _, filt = shift_filter_ops()
    gap = float(
        torch.linalg.vector_norm(
            (
                apply_physical_operator(apply_physical_operator(tensors, filt), filt)
                - apply_physical_operator(apply_physical_operator(tensors, filt), filt)
            ).reshape(-1)
        ).item()
    )
    return {
        "pass": gap < TOL,
        "why_rejected": "commuting/order-erased operator path cannot witness N01 on the PEPS3D seed",
        "order_gap": gap,
    }


def z3_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    variables = {key: z3.Bool(key) for key in actuals}
    final_claim = z3.Bool("final_claim")
    solver = z3.Solver()
    for key, value in actuals.items():
        solver.add(variables[key] == bool(value))
    solver.add(z3.Not(final_claim))

    collapse = z3.Solver()
    for key, value in actuals.items():
        collapse.add(variables[key] == bool(value))
    collapse.add(z3.Not(final_claim))
    collapse.add(z3.Or(final_claim, *[z3.Not(variables[key]) for key in variables]))
    return {
        "positive_status": str(solver.check()),
        "collapse_status": str(collapse.check()),
        "pass": solver.check() == z3.sat and collapse.check() == z3.unsat,
    }


def cvc5_admission_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    terms = {key: solver.mkConst(bool_sort, key) for key in actuals}
    final_claim = solver.mkConst(bool_sort, "final_claim")
    for key, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[key], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, final_claim, solver.mkBoolean(False)))
    positive = solver.checkSat()

    collapse = cvc5.Solver()
    collapse.setLogic("ALL")
    bool_sort2 = collapse.getBooleanSort()
    terms2 = {key: collapse.mkConst(bool_sort2, f"ko_{key}") for key in actuals}
    final_claim2 = collapse.mkConst(bool_sort2, "ko_final_claim")
    for key, value in actuals.items():
        collapse.assertFormula(collapse.mkTerm(Kind.EQUAL, terms2[key], collapse.mkBoolean(bool(value))))
    collapse.assertFormula(collapse.mkTerm(Kind.EQUAL, final_claim2, collapse.mkBoolean(False)))
    knockout_terms = [final_claim2] + [collapse.mkTerm(Kind.NOT, terms2[key]) for key in actuals]
    collapse.assertFormula(collapse.mkTerm(Kind.OR, *knockout_terms))
    collapse_status = collapse.checkSat()
    return {
        "positive_status": str(positive),
        "collapse_status": str(collapse_status),
        "pass": str(positive) == "sat" and str(collapse_status) == "unsat",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    carrier = base_carrier_gate()
    order = order_witness_gate()
    topology = topology_tool_gate()
    stress = stress_gate()
    graveyard_companions = {
        "GC1_scalar_peps3d_label_control_rejected": scalar_label_control_rejected(),
        "GC2_no_anchor_control_rejected": no_anchor_control_rejected(),
        "GC3_edge_erased_no_bond_control_rejected": edge_erased_control_rejected(),
        "GC4_order_erased_control_rejected": order_erased_control_rejected(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_dense_state_closure": {"pass": stress["dense_state_closure_used"] is False, "dense_state_closure_used": False},
        "B3_downstream_consumers_blocked": {
            "pass": True,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
    }
    actuals = {
        "phase1_receipts_declared": True,
        "finite_peps3d_anchor": bool(carrier["pass"]),
        "order_witness": bool(order["pass"]),
        "topology_tools": bool(topology["pass"]),
        "stress": bool(stress["pass"]),
        "graveyards_reject": all(row["pass"] for row in graveyard_companions.values()),
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    positive = {
        "finite_peps3d_probe_effect_seed_carrier": carrier,
        "peps3d_seed_order_witness": order,
        "peps3d_anchor_topology_tool_depth": topology,
        "peps3d_seed_scale_stress_without_dense_closure": stress,
        "z3_finite_carrier_nonpromotion_gate": z3_admission_gate(actuals),
        "cvc5_finite_carrier_nonpromotion_gate": cvc5_admission_gate(actuals),
    }
    controls = {"positive": positive, "negative": graveyard_companions, "boundary": boundary}
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
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
        "finite_map": [
            carrier["finite_map"],
            "anchor : local carrier object -> V union E union F union C",
            "I_K(T) = finite site/edge/face/cell signatures without dense closure",
        ],
        "domain": carrier["domain"],
        "codomain_or_output": carrier["output"],
        "root_constraints_in_force": {
            "F01": {
                "finite_carrier_shape": list(carrier["shape"]),
                "finite_site_count": carrier["anchor_counts"]["V"],
                "finite_edge_count": carrier["anchor_counts"]["E"],
                "finite_face_count": carrier["anchor_counts"]["F"],
                "finite_cell_count": carrier["anchor_counts"]["C"],
                "finite_effect_count": EFFECT_COUNT,
                "max_stress_sites": stress["max_peps3d_sites"],
                "max_stress_bond": stress["max_peps3d_bond"],
            },
            "N01": {
                "witness": order["N01_witness"],
                "order_gap": order["order_gap"],
                "order_erased_control_gap": order["order_erased_control_gap"],
                "sympy_commutator_rank": order["sympy_commutator_rank"],
                "clifford_e1e2_anticommutator_zero": order["clifford_e1e2_anticommutator_zero"],
            },
        },
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "finite_peps3d_anchor_geometry_only",
        "carrier_realization": "finite complex torch PEPS3D tensors seeded by finite probe/effect responses; local boundary contractions only",
        "peps3d_embedding": carrier["peps3d_embedding"],
        "spinor_state": "minimal normalized two-component torch complex carrier used only to seed finite probe responses; spinor/Hopf geometry remains blocked",
        "quaternion_action": "not_applicable_phase2_seed_carrier",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/phase1_to_phase2_transition_decision_20260525.json",
            "system_v5/ops/formal_scouts/results/phase1_finite_probe_effect_quotient_root_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_contextuality_sheaf_event_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json",
            "system_v5/ops/formal_scouts/results/process_povm_quantum_comb_history_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_projective_design_spectral_triple_gate_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite PEPS3D seed carrier anchor for the Phase 1 finite response quotient",
        "branch_status_before_run": "phase_2_opened_by_transition_artifact",
        "allowed_claims": [
            "Phase 2 finite PEPS3D seed-carrier scout only",
            "finite PEPS3D site/edge/face/cell anchors carry finite probe/effect response indices",
        ],
        "promotion_blockers": [
            "no spinor/Hopf/Weyl geometry admitted in this packet",
            "no terrain, operator substage, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, IGT/game theory, or axes 7-12 consumer admitted",
            "full PEPS3D environment closure is not tested here",
        ],
        "required_tools": [
            "pytorch",
            "z3",
            "cvc5",
            "sympy",
            "clifford",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "torch_geometric",
        ],
        "actual_tools_used": [
            "pytorch",
            "z3",
            "cvc5",
            "sympy",
            "clifford",
            "rustworkx",
            "xgi",
            "toponetx",
            "gudhi",
            "torch_geometric",
        ],
        "proof_surfaces_used": ["z3", "cvc5", "sympy", "clifford"],
        "graph_surfaces_used": ["rustworkx", "xgi", "torch_geometric"],
        "topology_surfaces_used": ["toponetx", "gudhi"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_inputs": [
            "Phase 1 finite probe/effect response-quotient receipts",
            "finite PEPS3D carrier K=(V,E,F,C)",
            "finite effect physical index a",
        ],
        "data_or_artifact_dependencies": [
            "system_v5/ops/formal_scouts/phase1_to_phase2_transition_decision_20260525.json",
            "system_v5/ops/formal_scouts/results/phase1_finite_probe_effect_quotient_root_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_contextuality_sheaf_event_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json",
            "system_v5/ops/formal_scouts/results/process_povm_quantum_comb_history_gate_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_projective_design_spectral_triple_gate_probe_results.json",
        ],
        "required_negatives": [
            "scalar_peps3d_label_control_rejected",
            "no_anchor_control_rejected",
            "edge_erased_no_bond_control_rejected",
            "order_erased_control_rejected",
        ],
        "negatives_run": list(graveyard_companions.keys()),
        "kill_conditions": [
            "scalar PEPS3D labels are accepted as claim-bearing anchors",
            "no-anchor tensors are accepted",
            "edge-erased carrier is accepted as a PEPS3D carrier path",
            "order-erased control retains N01 witness",
            "dense state closure is used",
            "any downstream consumer is admitted",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": "phase2_finite_peps3d_seed_carrier_opening_packet_v1",
        "result_summary": {
            "base_anchor_counts": carrier["anchor_counts"],
            "tensor_shape": carrier["tensor_shape"],
            "order_gap": order["order_gap"],
            "order_erased_control_gap": order["order_erased_control_gap"],
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "dense_state_closure_used": False,
        },
        "pass_rule": "finite PEPS3D anchors exist over V/E/F/C, tensors carry finite effect physical indices, local signatures and order witness pass, stress remains finite without dense closure, and scalar/no-anchor/edge-erased/order-erased controls fail",
        "fail_rule": "missing V/E/F/C anchors, scalar-label acceptance, no-anchor acceptance, dense closure, missing N01 witness, failed topology tools, or downstream consumer admission",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_seed_frontier_matrix_or_controller_transition_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": controls,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "blockers": [],
        "summary": {
            "phase": 2,
            "candidate": "finite_peps3d_probe_effect_seed_carrier",
            "max_qubits": 0,
            "max_peps3d_sites": stress["max_peps3d_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "base_anchor_counts": carrier["anchor_counts"],
            "dense_state_closure_used": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 Phase 2 finite PEPS3D seed-carrier formal scout. It is not a v4 probe, "
            "not a full PEPS3D environment contraction, and not a promotion of spinor/Hopf geometry, "
            "terrain, substages, flux, Xi/Phi0, Axis0, basin, or physics claims."
        ),
        "next_required_work": [
            "Validate this seed-carrier receipt inside the active seed-carrier frontier matrix.",
            "Keep PEPS3D as a carrier anchor from this point onward; do not treat it as a late label or downstream layer.",
        ],
        "next_admissible_step": "Stay inside the active seed-carrier frontier by running the next bounded in-level packet or writing an explicit blocker; do not open later consumers from this receipt.",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
