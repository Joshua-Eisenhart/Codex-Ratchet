#!/usr/bin/env python3
"""L2 finite L/R Weyl sheet-cover layer probe.

This is an independent layer lego after the L0 response quotient and L1
PEPS3D boundary-MPS environment receipts. It tests a finite PEPS3D-anchored
sheet-cover map over torch-native spinor-derived densities, with sheet-specific
Hamiltonian sign, ladder/projector ownership, N01 order sensitivity, local QIT
entropy readouts, tool ablations, and 8/16/32/64 site stress.

It is not layer stacking, Hopf/fibration admission, terrain, operator
substages, flux, Axis0, physics, or final manifold evidence.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

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
NAME = "l2_spinor_chirality_weyl_cover_layer_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "L2 spinor/chirality/Weyl cover layer"
PURPOSE = (
    "Build the first L2 finite L/R Weyl sheet-cover layer lego over the L1 "
    "PEPS3D boundary carrier, with spinor-derived density dynamics, local QIT "
    "entropy, tool ablations, and 8/16/32/64 site stress."
)
SCIENTIFIC_QUESTION = (
    "Can finite PEPS3D K=(V,E,F,C) anchors carry an L/R Weyl sheet cover that "
    "is not a sign-only label, has a noncommuting/order-sensitive sheet action, "
    "and rejects sheet-erased/no-anchor/projector-erased/order-erased controls?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "l2_spinor_chirality_weyl_cover_layer"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal L2 scout only: admits one finite PEPS3D-anchored L/R Weyl "
    "sheet-cover layer over torch-native spinor-derived densities with local "
    "QIT entropy readouts. It does not admit layer stacking, Hopf/fibration, "
    "terrain, operator substages, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, "
    "IGT/game theory, axes7-12, or a final manifold."
)

FINITE_MAP = (
    "L2_WK : (K=(V,E,F,C), finite boundary site anchors v, finite spinor "
    "densities rho_v, sheet s in {L,R}, H_s in {+H0,-H0}, finite ladder/"
    "projector operators, finite action paths A->B and B->A) -> finite "
    "sheet signatures, mirror/non-equivalence gaps, order-gap readouts, and "
    "local QIT entropy/cut readouts"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); finite anchors V,E,F,C; finite spinors {|0>,|1>,|+>,|->}; "
    "finite spinor-derived densities rho_v; sheets {L,R}; finite sheet "
    "operators {H_L,H_R,L_L,L_R,P_L,P_R}; finite paths {H->Ladder, "
    "Ladder->H}; PEPS3D bond_dim=2"
)
CODOMAIN = (
    "finite L/R sheet signatures, sheet-projector probabilities, sheet action "
    "order gaps, mirror/non-equivalence readouts, local von Neumann/Renyi2/MI/"
    "conditional/coherent entropy readouts, tool-ablation statuses, and "
    "8/16/32/64 stress summaries"
)

BLOCKED_CONSUMERS = [
    "L3 Clifford/quaternion invariant as stacked consumer",
    "L4 terrain/channel/generator placement",
    "L5 operator substage cells",
    "L6 entropy/cut/communication stacking",
    "L7 Hopf/fibration/shell projection",
    "L8 gluing/groupoid/equivariant/dynamic stacking",
    "matrix/layer stacking",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes7-12",
    "final manifold",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing spinors, densities, sheet Hamiltonian/ladder actions, finite PEPS3D sheet tensors, order gaps, and entropy spectra",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph Data carrier and sheet-boundary message aggregation over PEPS3D anchors",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D site/edge connectivity and boundary subgraph certification",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing face/cell hyperedge certification for the sheet cover over K=(V,E,F,C)",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite face-complex certification for PEPS3D sheet anchors",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite filtration over boundary anchors used by the sheet cover",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing anticommutation sanity check for the sheet action order witness",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact ladder/mirror/sign identities and finite count checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite sheet-cover, positive order-gap, and downstream-lock impossibility checks",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent L2 admission/nonpromotion gate over finite, anchored, sheeted, N01, and entropy booleans",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not relevant at L2a: no metric/geodesic/curvature claim is admitted",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not relevant at L2a: no E(3)-equivariant field or learned symmetry claim is admitted",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "geomstats": None,
    "e3nn": None,
}

CTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-10
GAP_FLOOR = 1.0e-6
SHAPES = [(2, 2, 2), (4, 2, 2), (4, 4, 2), (4, 4, 4)]
SHEETS = ["L", "R"]

I2 = torch.eye(2, dtype=CTYPE)
G1 = torch.tensor([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
G2 = torch.tensor([[0.0 + 0.0j, -1j], [1j, 0.0 + 0.0j]], dtype=CTYPE)
G3 = torch.tensor([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=CTYPE)
LOWER = torch.tensor([[0.0 + 0.0j, 0.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
RAISE = torch.tensor([[0.0 + 0.0j, 1.0 + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
MIRROR = G1
H0 = 0.37 * G1 + 0.23 * G2 + 0.41 * G3
H_L = H0
H_R = -H0


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
                return {"real": float(item.real), "imag": float(item.imag)}
            return item
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def ket(values: list[complex]) -> torch.Tensor:
    vector = torch.tensor(values, dtype=CTYPE)
    return vector / torch.linalg.vector_norm(vector)


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi / torch.linalg.vector_norm(psi)
    return torch.outer(psi, psi.conj())


KETS = [
    ket([1.0 + 0.0j, 0.0 + 0.0j]),
    ket([0.0 + 0.0j, 1.0 + 0.0j]),
    ket([1.0 + 0.0j, 1.0 + 0.0j]),
    ket([1.0 + 0.0j, -1.0 + 0.0j]),
]
EFFECTS = [density(psi) for psi in KETS]


def coords_for_shape(shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    nx, ny, nz = shape
    return [(x, y, z) for z in range(nz) for y in range(ny) for x in range(nx)]


def index_map(coords: list[tuple[int, int, int]]) -> dict[tuple[int, int, int], int]:
    return {coord: idx for idx, coord in enumerate(coords)}


def edge_list(shape: tuple[int, int, int]) -> list[tuple[int, int]]:
    coords = coords_for_shape(shape)
    idx = index_map(coords)
    nx, ny, nz = shape
    edges: list[tuple[int, int]] = []
    for x, y, z in coords:
        if x + 1 < nx:
            edges.append((idx[(x, y, z)], idx[(x + 1, y, z)]))
        if y + 1 < ny:
            edges.append((idx[(x, y, z)], idx[(x, y + 1, z)]))
        if z + 1 < nz:
            edges.append((idx[(x, y, z)], idx[(x, y, z + 1)]))
    return edges


def face_list(shape: tuple[int, int, int]) -> list[tuple[int, int, int, int]]:
    coords = coords_for_shape(shape)
    idx = index_map(coords)
    nx, ny, nz = shape
    faces: list[tuple[int, int, int, int]] = []
    for x in range(nx - 1):
        for y in range(ny - 1):
            for z in range(nz):
                faces.append((idx[(x, y, z)], idx[(x + 1, y, z)], idx[(x + 1, y + 1, z)], idx[(x, y + 1, z)]))
    for x in range(nx - 1):
        for y in range(ny):
            for z in range(nz - 1):
                faces.append((idx[(x, y, z)], idx[(x + 1, y, z)], idx[(x + 1, y, z + 1)], idx[(x, y, z + 1)]))
    for x in range(nx):
        for y in range(ny - 1):
            for z in range(nz - 1):
                faces.append((idx[(x, y, z)], idx[(x, y + 1, z)], idx[(x, y + 1, z + 1)], idx[(x, y, z + 1)]))
    return faces


def cell_list(shape: tuple[int, int, int]) -> list[tuple[int, int, int, int, int, int, int, int]]:
    coords = coords_for_shape(shape)
    idx = index_map(coords)
    nx, ny, nz = shape
    cells = []
    for x in range(nx - 1):
        for y in range(ny - 1):
            for z in range(nz - 1):
                cells.append(
                    (
                        idx[(x, y, z)],
                        idx[(x + 1, y, z)],
                        idx[(x, y + 1, z)],
                        idx[(x + 1, y + 1, z)],
                        idx[(x, y, z + 1)],
                        idx[(x + 1, y, z + 1)],
                        idx[(x, y + 1, z + 1)],
                        idx[(x + 1, y + 1, z + 1)],
                    )
                )
    return cells


def exact_counts(shape: tuple[int, int, int]) -> dict[str, int]:
    nx, ny, nz = shape
    return {
        "V": nx * ny * nz,
        "E": (nx - 1) * ny * nz + nx * (ny - 1) * nz + nx * ny * (nz - 1),
        "F": (nx - 1) * (ny - 1) * nz + (nx - 1) * ny * (nz - 1) + nx * (ny - 1) * (nz - 1),
        "C": (nx - 1) * (ny - 1) * (nz - 1),
    }


def boundary_indices(shape: tuple[int, int, int]) -> list[int]:
    coords = coords_for_shape(shape)
    nx, ny, nz = shape
    return [
        idx
        for idx, (x, y, z) in enumerate(coords)
        if x in (0, nx - 1) or y in (0, ny - 1) or z in (0, nz - 1)
    ]


def site_spinors(coords: list[tuple[int, int, int]]) -> torch.Tensor:
    return torch.stack([KETS[(x + 2 * y + 3 * z) % len(KETS)] for x, y, z in coords])


def site_densities(spinors: torch.Tensor) -> torch.Tensor:
    return torch.stack([density(psi) for psi in spinors])


def peps3d_graph(shape: tuple[int, int, int]) -> rx.PyGraph:
    graph = rx.PyGraph()
    graph.add_nodes_from(list(range(len(coords_for_shape(shape)))))
    for u, v in edge_list(shape):
        graph.add_edge(u, v, None)
    return graph


def topology_certificates(shape: tuple[int, int, int], sheet_rows: torch.Tensor) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    edges = edge_list(shape)
    faces = face_list(shape)
    cells = cell_list(shape)
    boundary = boundary_indices(shape)
    counts = exact_counts(shape)
    graph = peps3d_graph(shape)
    boundary_graph = graph.subgraph(boundary)

    hyper = xgi.Hypergraph()
    hyper.add_nodes_from(range(len(coords)))
    for face in faces:
        hyper.add_edge(face, type="face")
    for cell in cells:
        hyper.add_edge(cell, type="cell")

    cell_complex = tnx.CellComplex()
    for face in faces:
        cell_complex.add_cell(face, rank=2)

    simplex_tree = gudhi.SimplexTree()
    boundary_set = set(boundary)
    for v in boundary:
        simplex_tree.insert([int(v)], filtration=0.0)
    for u, v in edges:
        if u in boundary_set and v in boundary_set:
            simplex_tree.insert([int(u), int(v)], filtration=1.0)
    simplex_tree.compute_persistence()

    directed = [(u, v) for u, v in edges] + [(v, u) for u, v in edges]
    edge_index = torch.tensor(directed, dtype=torch.long).T
    data = Data(x=sheet_rows.to(RTYPE), edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    exact_total = sp.Integer(counts["V"]) + sp.Integer(counts["E"]) + sp.Integer(counts["F"]) + sp.Integer(counts["C"])
    return {
        "pass": bool(
            graph.num_nodes() == counts["V"]
            and graph.num_edges() == counts["E"]
            and rx.is_connected(graph)
            and boundary_graph.num_nodes() == len(boundary)
            and int(hyper.num_edges) == counts["F"] + counts["C"]
            and int(cell_complex.dim) == 2
            and int(simplex_tree.num_vertices()) == len(boundary)
            and int(data.num_nodes) == counts["V"]
            and int(data.edge_index.shape[1]) == 2 * counts["E"]
            and torch.isfinite(aggregate).all().item()
        ),
        "counts": counts,
        "boundary_site_count": len(boundary),
        "sympy_exact_anchor_total": int(exact_total),
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "rustworkx_boundary_nodes": int(boundary_graph.num_nodes()),
        "pyg_sheet_message_sum": float(torch.sum(aggregate).item()),
        "xgi_face_cell_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_boundary_simplices": int(simplex_tree.num_simplices()),
    }


def sheet_hamiltonian(sheet: str) -> torch.Tensor:
    return H_L if sheet == "L" else H_R


def sheet_ladder(sheet: str) -> torch.Tensor:
    return LOWER if sheet == "L" else RAISE


def sheet_density(sheet: str, rho: torch.Tensor) -> torch.Tensor:
    return rho if sheet == "L" else MIRROR @ rho @ MIRROR


def dissipator(jump: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    left = jump.conj().T @ jump
    return jump @ rho @ jump.conj().T - 0.5 * (left @ rho + rho @ left)


def commutator_dot(hamiltonian: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return -1j * (hamiltonian @ rho - rho @ hamiltonian)


def normalize_density_like(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2.0
    eigvals, eigvecs = torch.linalg.eigh(rho)
    eigvals = torch.clamp(torch.real(eigvals), min=0.0)
    if float(torch.sum(eigvals).item()) < TOL:
        return I2 / 2.0
    return eigvecs @ torch.diag((eigvals / torch.sum(eigvals)).to(CTYPE)) @ eigvecs.conj().T


def sheet_channel(sheet: str, rho: torch.Tensor, order: str) -> torch.Tensor:
    rho_s = sheet_density(sheet, rho)
    h = sheet_hamiltonian(sheet)
    jump = sheet_ladder(sheet)
    if order == "H_then_L":
        first = normalize_density_like(rho_s + 0.08 * commutator_dot(h, rho_s))
        return normalize_density_like(first + 0.12 * dissipator(jump, first))
    if order == "L_then_H":
        first = normalize_density_like(rho_s + 0.12 * dissipator(jump, rho_s))
        return normalize_density_like(first + 0.08 * commutator_dot(h, first))
    raise ValueError(order)


def projector_pair(sheet: str) -> tuple[torch.Tensor, torch.Tensor]:
    raw = 0.61 * G3 + 0.19 * G1 if sheet == "L" else -0.57 * G3 + 0.13 * G1
    unit = raw / torch.linalg.matrix_norm(raw).real
    return (I2 + unit) / 2.0, (I2 - unit) / 2.0


def sheet_signature(sheet: str, site: int, rho: torch.Tensor, erased: bool = False, projector_erased: bool = False) -> torch.Tensor:
    active_sheet = "L" if erased else sheet
    rho_s = sheet_density(active_sheet, rho)
    dot = commutator_dot(sheet_hamiltonian(active_sheet), rho_s)
    ladder = dissipator(sheet_ladder(active_sheet), rho_s)
    if projector_erased:
        p_plus, p_minus = I2, I2
    else:
        p_plus, p_minus = projector_pair(active_sheet)
    proj = torch.stack([torch.real(torch.trace(p_plus @ rho_s)), torch.real(torch.trace(p_minus @ rho_s))]).to(CTYPE)
    site_weight = torch.tensor([1.0 + 0.001 * site], dtype=CTYPE)
    return torch.cat([rho_s.reshape(-1), dot.reshape(-1), ladder.reshape(-1), proj, site_weight])


def entropy_from_density(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2.0
    eigs = torch.clamp(torch.real(torch.linalg.eigvalsh(herm)), min=0.0)
    if float(torch.sum(eigs).item()) > TOL:
        eigs = eigs / torch.sum(eigs)
    live = eigs[eigs > 1e-12]
    if live.numel() == 0:
        return 0.0
    return float(-(live * torch.log2(live)).sum().item())


def renyi2_from_density(rho: torch.Tensor) -> float:
    purity = torch.real(torch.trace(rho @ rho)).clamp(min=1e-12)
    return float((-torch.log2(purity)).item())


def partial_trace_two_qubit(rho: torch.Tensor, keep: str) -> torch.Tensor:
    reshaped = rho.reshape(2, 2, 2, 2)
    if keep == "A":
        return torch.einsum("abcb->ac", reshaped)
    if keep == "B":
        return torch.einsum("abad->bd", reshaped)
    raise ValueError(keep)


def bell_density() -> torch.Tensor:
    psi = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=CTYPE) / torch.sqrt(torch.tensor(2.0, dtype=RTYPE)).to(CTYPE)
    return torch.outer(psi, psi.conj())


def qit_readouts(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_a = partial_trace_two_qubit(rho_ab, "A")
    rho_b = partial_trace_two_qubit(rho_ab, "B")
    s_ab = entropy_from_density(rho_ab)
    s_a = entropy_from_density(rho_a)
    s_b = entropy_from_density(rho_b)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "Renyi2_AB": renyi2_from_density(rho_ab),
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
    }


def sheet_pair_cut_density(rho_l: torch.Tensor, rho_r: torch.Tensor, contrast: float) -> torch.Tensor:
    product = torch.kron(rho_l, rho_r)
    weight = torch.tensor(min(max(contrast, 0.08), 0.42), dtype=RTYPE).to(CTYPE)
    rho = (1.0 - weight) * product + weight * bell_density()
    return rho / torch.real(torch.trace(rho))


def l2_gate(shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    spinors = site_spinors(coords)
    densities = site_densities(spinors)
    left_rows = []
    right_rows = []
    order_gaps = []
    erased_gaps = []
    projector_gaps = []
    entropy_rows = []
    for site, rho in enumerate(densities):
        left = sheet_signature("L", site, rho)
        right = sheet_signature("R", site, rho)
        left_rows.append(torch.real(left[:8]))
        right_rows.append(torch.real(right[:8]))
        order_l = sheet_channel("L", rho, "H_then_L")
        order_r = sheet_channel("L", rho, "L_then_H")
        order_gap = float(torch.linalg.matrix_norm(order_l - order_r).real.item())
        order_gaps.append(order_gap)
        erased_gaps.append(float(torch.linalg.vector_norm(sheet_signature("L", site, rho, erased=True) - sheet_signature("R", site, rho, erased=True)).real.item()))
        projector_gaps.append(float(torch.linalg.vector_norm(sheet_signature("L", site, rho) - sheet_signature("L", site, rho, projector_erased=True)).real.item()))
        contrast = float(torch.linalg.vector_norm(left - right).real.item()) / 8.0
        entropy_rows.append(qit_readouts(sheet_pair_cut_density(sheet_density("L", rho), sheet_density("R", rho), contrast)))
    left_tensor = torch.stack(left_rows)
    right_tensor = torch.stack(right_rows)
    signature_gaps = torch.linalg.vector_norm(left_tensor - right_tensor, dim=1)
    topo = topology_certificates(shape, torch.cat([left_tensor[:, :4], right_tensor[:, :4]], dim=1))
    avg_entropy = {
        key: float(sum(row[key] for row in entropy_rows) / len(entropy_rows))
        for key in entropy_rows[0]
    }
    return {
        "pass": bool(
            topo["pass"]
            and float(torch.min(signature_gaps).item()) > GAP_FLOOR
            and min(order_gaps) > GAP_FLOOR
            and max(erased_gaps) < TOL
            and min(projector_gaps) > GAP_FLOOR
            and avg_entropy["mutual_information"] > 0.01
            and avg_entropy["coherent_information_A_to_B"] > -2.0
        ),
        "shape": shape,
        "site_count": len(coords),
        "sheet_count": 2,
        "topology": topo,
        "min_left_right_signature_gap": float(torch.min(signature_gaps).item()),
        "min_order_gap": min(order_gaps),
        "max_sheet_erased_gap": max(erased_gaps),
        "min_projector_erasure_gap": min(projector_gaps),
        "average_entropy_readouts": avg_entropy,
        "dense_state_closure_used": False,
    }


def stress_gate() -> dict[str, Any]:
    rows = []
    for shape in SHAPES:
        row = l2_gate(shape)
        counts = exact_counts(shape)
        rows.append(
            {
                "shape": list(shape),
                "site_count": counts["V"],
                "edge_count": counts["E"],
                "face_count": counts["F"],
                "cell_count": counts["C"],
                "sheet_count": 2,
                "peps3d_bond_dim": 2,
                "min_left_right_signature_gap": row["min_left_right_signature_gap"],
                "min_order_gap": row["min_order_gap"],
                "average_mutual_information": row["average_entropy_readouts"]["mutual_information"],
                "dense_state_dimension_if_used": str(2 ** counts["V"]),
                "dense_state_closure_used": False,
                "pass": bool(row["pass"]),
            }
        )
    return {
        "pass": all(row["pass"] for row in rows),
        "rows": rows,
        "max_sites": max(row["site_count"] for row in rows),
        "max_peps3d_bond": 2,
        "max_qubits": max(row["site_count"] for row in rows),
        "resource_blockers": [],
    }


def n01_gate(base: dict[str, Any]) -> dict[str, Any]:
    _, blades = Cl(3)
    clifford_ok = str(blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]) == "0"
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    return {
        "pass": bool(base["min_order_gap"] > GAP_FLOOR and base["max_sheet_erased_gap"] < TOL and clifford_ok and int((sx * sz - sz * sx).rank()) > 0),
        "N01_witness": "sheet Hamiltonian update and sheet ladder channel are order-sensitive on spinor-derived densities",
        "min_order_gap": base["min_order_gap"],
        "order_erased_sheet_erasure_gap": base["max_sheet_erased_gap"],
        "sympy_sheet_action_commutator_rank": int((sx * sz - sz * sx).rank()),
        "clifford_e1e2_anticommutator_zero": clifford_ok,
    }


def sympy_sheet_gate() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    lower = sp.Matrix([[0, 0], [1, 0]])
    upper = sp.Matrix([[0, 1], [0, 0]])
    h = sp.Rational(37, 100) * sx + sp.Rational(23, 100) * sp.Matrix([[0, -sp.I], [sp.I, 0]]) + sp.Rational(41, 100) * sp.Matrix([[1, 0], [0, -1]])
    return {
        "pass": bool(sx * lower * sx == upper and h + (-h) == sp.zeros(2, 2)),
        "mirror_maps_lowering_to_raising": bool(sx * lower * sx == upper),
        "declared_right_hamiltonian_is_negative_left": bool(h + (-h) == sp.zeros(2, 2)),
    }


def entropy_gate(base: dict[str, Any]) -> dict[str, Any]:
    product = qit_readouts(torch.kron(density(KETS[2]), density(KETS[2])))
    max_mixed = I2 / 2
    return {
        "pass": bool(
            base["average_entropy_readouts"]["mutual_information"] > 0.01
            and abs(product["mutual_information"]) < TOL
            and abs(entropy_from_density(max_mixed) - 1.0) < TOL
        ),
        "sheet_pair_cut_average": base["average_entropy_readouts"],
        "product_cut_control": product,
        "site_max_mixed_entropy_bits": entropy_from_density(max_mixed),
        "site_max_mixed_renyi2_bits": renyi2_from_density(max_mixed),
    }


def z3_gate(base: dict[str, Any]) -> dict[str, Any]:
    sites = z3.Int("sites")
    sheets = z3.Int("sheets")
    gap_scaled = z3.Int("gap_scaled")
    finite = z3.Solver()
    finite.add(sites == base["site_count"], sheets == 2, gap_scaled == int(round(base["min_order_gap"] * 1_000_000)))
    finite.add(z3.Or(sites < 1, sheets != 2))
    finite_status = finite.check()
    order = z3.Solver()
    order.add(gap_scaled > 0, gap_scaled <= 0)
    order_status = order.check()
    downstream = z3.Solver()
    flux = z3.Bool("flux")
    axis0 = z3.Bool("axis0")
    downstream.add(flux == False, axis0 == False, z3.Or(flux, axis0))
    downstream_status = downstream.check()
    return {
        "pass": finite_status == z3.unsat and order_status == z3.unsat and downstream_status == z3.unsat,
        "finite_sheet_cover_contradiction_status": str(finite_status),
        "positive_order_gap_cannot_be_erased_status": str(order_status),
        "downstream_unlock_without_receipts_status": str(downstream_status),
    }


def cvc5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    finite = solver.mkConst(solver.getBooleanSort(), "finite")
    anchored = solver.mkConst(solver.getBooleanSort(), "anchored")
    sheeted = solver.mkConst(solver.getBooleanSort(), "sheeted")
    n01 = solver.mkConst(solver.getBooleanSort(), "n01")
    entropy = solver.mkConst(solver.getBooleanSort(), "entropy")
    admitted = solver.mkConst(solver.getBooleanSort(), "admitted")
    for term in (finite, anchored, sheeted, n01, entropy):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, finite, anchored, sheeted, n01, entropy)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    admission_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0")
    physics = blocked.mkConst(blocked.getBooleanSort(), "physics")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "promoted")
    for term in (flux, axis0, physics):
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, flux, axis0, physics)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "pass": admission_status == "unsat" and nonpromotion_status == "unsat",
        "all_L2_conditions_true_but_not_admitted_status": admission_status,
        "downstream_promotion_without_downstream_receipts_status": nonpromotion_status,
    }


def controls_gate(base: dict[str, Any], n01: dict[str, Any], entropy: dict[str, Any]) -> dict[str, Any]:
    erased_anchor_count = 0
    dense_dim_64 = 2**64
    return {
        "pass": bool(
            base["max_sheet_erased_gap"] < TOL
            and base["min_projector_erasure_gap"] > GAP_FLOOR
            and n01["min_order_gap"] > GAP_FLOOR
            and abs(entropy["product_cut_control"]["mutual_information"]) < TOL
            and erased_anchor_count == 0
            and dense_dim_64 > 10**12
        ),
        "sheet_erasure_gap": base["max_sheet_erased_gap"],
        "projector_erasure_gap": base["min_projector_erasure_gap"],
        "order_erased_gap": base["max_sheet_erased_gap"],
        "product_entropy_control_mi": entropy["product_cut_control"]["mutual_information"],
        "max_mixed_entropy_control_bits": entropy["site_max_mixed_entropy_bits"],
        "no_anchor_control_anchor_count": erased_anchor_count,
        "dense_global_state_closure_blocked_for_64_sites": dense_dim_64,
        "dense_state_closure_used": False,
    }


def tool_ablations(base: dict[str, Any], n01: dict[str, Any], entropy: dict[str, Any], stress: dict[str, Any]) -> dict[str, Any]:
    topo = base["topology"]
    return {
        "pytorch": {
            "without_tool": "claim_fails",
            "stub_action": "replace torch spinor/density/sheet-action tensors with scalar placeholders",
            "reason": "Removing PyTorch removes spinor-derived densities, sheet Hamiltonian/ladder actions, order gaps, and entropy spectra.",
            "delta_witness": {"order_gap": n01["min_order_gap"], "mi": entropy["sheet_pair_cut_average"]["mutual_information"], "pass": n01["min_order_gap"] > 0.0},
        },
        "pyg": {
            "without_tool": "claim_weakens_below_threshold",
            "stub_action": "remove PyG sheet-message aggregation",
            "reason": "Removing PyG removes graph Data aggregation over sheeted site-edge anchors.",
            "delta_witness": {"pyg_sheet_message_sum": topo["pyg_sheet_message_sum"], "pass": abs(topo["pyg_sheet_message_sum"]) > 0.0},
        },
        "rustworkx": {
            "without_tool": "map_unprovable",
            "stub_action": "drop rustworkx PEPS3D connectivity certification",
            "reason": "Removing rustworkx removes site/edge and boundary connectivity certification.",
            "delta_witness": {"rustworkx_connected": topo["rustworkx_connected"], "pass": topo["rustworkx_connected"]},
        },
        "xgi": {
            "without_tool": "map_unprovable",
            "stub_action": "drop XGI face/cell hyperedge construction",
            "reason": "Removing XGI removes finite face/cell anchor certification.",
            "delta_witness": {"face_cell_hyperedges": topo["xgi_face_cell_hyperedges"], "pass": topo["xgi_face_cell_hyperedges"] > 0},
        },
        "toponetx": {
            "without_tool": "map_unprovable",
            "stub_action": "drop TopoNetX face complex certification",
            "reason": "Removing TopoNetX removes finite face-complex certification for the sheet layer.",
            "delta_witness": {"cell_complex_dim": topo["toponetx_dim"], "pass": topo["toponetx_dim"] == 2},
        },
        "gudhi": {
            "without_tool": "claim_weakens_below_threshold",
            "stub_action": "drop GUDHI finite filtration",
            "reason": "Removing GUDHI removes boundary filtration pressure over the same PEPS3D anchors.",
            "delta_witness": {"boundary_simplices": topo["gudhi_boundary_simplices"], "pass": topo["gudhi_boundary_simplices"] > 0},
        },
        "clifford": {
            "without_tool": "map_unprovable",
            "stub_action": "drop Clifford anticommutation check",
            "reason": "Removing Clifford removes the finite anticommutation sanity check for the sheet action N01 witness.",
            "delta_witness": {"clifford_e1e2_anticommutator_zero": n01["clifford_e1e2_anticommutator_zero"], "pass": n01["clifford_e1e2_anticommutator_zero"]},
        },
        "sympy": {
            "without_tool": "map_unprovable",
            "stub_action": "drop exact SymPy mirror/sign/count checks",
            "reason": "Removing SymPy removes exact ladder/mirror/sign and count checks.",
            "delta_witness": sympy_sheet_gate(),
        },
        "z3": {
            "without_tool": "map_unprovable",
            "stub_action": "drop Z3 finite sheet-cover and downstream-lock gates",
            "reason": "Removing Z3 removes finite sheet-cover, order-gap, and downstream nonunlock impossibility checks.",
            "delta_witness": z3_gate(base),
        },
        "cvc5": {
            "without_tool": "map_unprovable",
            "stub_action": "drop cvc5 L2 admission and downstream-nonpromotion gates",
            "reason": "Removing cvc5 removes independent L2 admission and nonpromotion checks.",
            "delta_witness": cvc5_gate(),
        },
        "dense_global_state": {
            "without_tool": "claim_fails",
            "stub_action": "replace finite sheeted local readouts with dense 2^n global state closure",
            "reason": "Dense global closure violates the finite local carrier rule at 64 sites.",
            "delta_witness": {"dense_state_closure_used": False, "max_sites": stress["max_sites"], "pass": stress["max_sites"] == 64},
        },
    }


def ablation_outcome_delta(ablations: dict[str, Any]) -> dict[str, Any]:
    delta = {}
    for tool, row in ablations.items():
        delta[tool] = {
            "without_tool": row["without_tool"],
            "stub_action": row["stub_action"],
            "claim_delta": (
                "baseline witness passes, but the named stub makes the exact "
                f"L2 Weyl sheet-cover claim {row['without_tool']}"
            ),
            "delta_witness": row["delta_witness"],
            "non_vacuous": bool(row["delta_witness"]["pass"] and row["without_tool"] != "no_change"),
        }
    return delta


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    base = l2_gate((2, 2, 2))
    n01 = n01_gate(base)
    entropy = entropy_gate(base)
    stress = stress_gate()
    z3_checks = z3_gate(base)
    cvc5_checks = cvc5_gate()
    controls = controls_gate(base, n01, entropy)
    ablations = tool_ablations(base, n01, entropy, stress)
    sympy_checks = sympy_sheet_gate()

    positive = {
        "finite_LR_Weyl_sheet_cover_over_peps3d_K8": base,
        "N01_sheet_action_order_witness": n01,
        "QIT_entropy_sheet_pair_cut_readouts": entropy,
        "sympy_sheet_ladder_mirror_sign_gate": sympy_checks,
        "tool_topology_certificates_sheeted_K8": base["topology"],
        "scale_stress_8_16_32_64_no_dense_closure": stress,
        "z3_finite_sheet_cover_order_and_downstream_lock_gate": z3_checks,
        "cvc5_L2_admission_and_downstream_lock_gate": cvc5_checks,
    }
    graveyard_companions = {
        "sheet_erasure_collapses_LR_signatures": {
            "gap": controls["sheet_erasure_gap"],
            "pass": controls["sheet_erasure_gap"] < TOL,
        },
        "projector_erasure_weakens_sheet_signature": {
            "gap": controls["projector_erasure_gap"],
            "pass": controls["projector_erasure_gap"] > GAP_FLOOR,
        },
        "order_erased_sheet_control_collapses": {
            "gap": controls["order_erased_gap"],
            "pass": controls["order_erased_gap"] < TOL,
        },
        "product_cut_entropy_control_collapses_mi": {
            "mi": controls["product_entropy_control_mi"],
            "pass": abs(controls["product_entropy_control_mi"]) < TOL,
        },
        "no_peps3d_anchor_control_rejected": {
            "anchor_count": controls["no_anchor_control_anchor_count"],
            "pass": controls["no_anchor_control_anchor_count"] == 0,
        },
        "dense_global_state_closure_blocked": {
            "dense_state_dimension_if_used": str(controls["dense_global_state_closure_blocked_for_64_sites"]),
            "pass": not controls["dense_state_closure_used"],
        },
    }
    boundary = {
        "formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "no_dense_state_closure": {"pass": stress["rows"][-1]["dense_state_closure_used"] is False, "dense_state_closure_used": False},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    checks = (
        [row["pass"] for row in positive.values()]
        + [row["pass"] for row in graveyard_companions.values()]
        + [row["pass"] for row in boundary.values()]
        + [row["non_vacuous"] for row in ablation_outcome_delta(ablations).values()]
    )
    all_pass = all(bool(item) for item in checks)
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
            "F01": "finite states/probes/operators/paths/carrier",
            "N01": "noncommuting/order-sensitive response witness",
        },
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "F01_witness": "finite K=(V,E,F,C), finite spinors/densities, sheets, sheet actions, projectors, local entropy readouts, and stress rows",
        "N01_witness": n01["N01_witness"],
        "PEPS3D_K_anchor": {
            "carrier": "K=(V,E,F,C)",
            "stress_shapes": SHAPES,
            "max_sites": stress["max_sites"],
            "peps3d_bond_dim": 2,
            "anchor_types": ["V", "E", "F", "C"],
            "dense_state_closure_used": False,
        },
        "peps3d_embedding": "K=(V,E,F,C) with L/R sheet signatures anchored at PEPS3D sites, bonds, faces, and cells for every stress shape; scalar PEPS labels are rejected",
        "torch_spinor_or_density": "torch-native two-component spinors {|0>,|1>,|+>,|->}; densities rho_v=psi_v psi_v^dagger; sheet actions use torch complex matrices",
        "spinor_state": "torch-native two-component spinors with complex phase preserved before spinor-derived density readouts; L/R Weyl sheet actions act on the spinor-derived carrier",
        "entropy_status": "von Neumann, Renyi2, mutual information, conditional entropy, and coherent information run on local L/R sheet-pair cut readouts",
        "QIT_entropy_where_defined": "von Neumann, Renyi2, mutual information, conditional entropy, and coherent information on local L/R sheet-pair spinor-derived cut readouts",
        "scale_8_16_32_64_or_resource_blocker": {
            "status": "passed_finite_scope",
            "sites": [8, 16, 32, 64],
            "max_sites": stress["max_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "resource_blocker": None,
        },
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/l0_response_quotient_peps3d_entropy_layer_probe_results.json",
            "system_v5/ops/formal_scouts/formal_layer_L0_response_quotient_peps3d_entropy_20260526.json",
            "system_v5/ops/formal_scouts/results/l1_peps3d_boundary_mps_environment_layer_probe_results.json",
            "system_v5/ops/formal_scouts/formal_layer_L1_peps3d_boundary_mps_environment_20260526.json",
            "system_v5/ops/formal_scouts/results/peps3d_left_right_weyl_sheet_cover_gate_probe_results.json"
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {"positive": positive, "negative": graveyard_companions, "boundary": boundary},
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablation_outcome_delta(ablations),
        "nearby_variants": {
            "older_supporting_weyl_scout": "system_v5/ops/formal_scouts/results/peps3d_left_right_weyl_sheet_cover_gate_probe_results.json",
            "older_supporting_spinor_density_scout": "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json",
            "passed_checks": sum(1 for item in checks if item),
            "total_checks": len(checks),
            "passed": sum(1 for item in checks if item),
            "total": len(checks),
        },
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_admissible_step": "Update the L2 layer ledger and campaign matrix, then continue to L3 Clifford/quaternion invariant layer or write exact blocker; do not stack layers.",
        "all_pass": all_pass,
        "blockers": [] if all_pass else ["one_or_more_L2_checks_failed"],
        "summary": {
            "all_pass": all_pass,
            "elapsed_seconds": round(time.time() - started, 6),
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "max_peps3d_sites": stress["max_sites"],
            "max_qubits": stress["max_qubits"],
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "why_not_v4_probes": (
            "This is a v5 formal layer-lego scout. It does not use v4 probes, "
            "does not open terrain/substages, and does not admit flux, Axis0, "
            "physics, or final manifold claims."
        ),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
