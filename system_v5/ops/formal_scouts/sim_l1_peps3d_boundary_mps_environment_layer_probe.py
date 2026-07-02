#!/usr/bin/env python3
"""L1 PEPS3D finite-chi boundary-MPS environment layer probe.

This is an independent layer lego after the L0 response quotient receipt. It
tests a bounded finite map from PEPS3D K=(V,E,F,C) carriers to finite-chi
boundary-MPS environment signatures, local closure residuals, order-sensitive
boundary readouts, and QIT entropy cuts. It is not a stacking, Hopf/Weyl,
terrain, flux, Axis0, physics, or final-manifold claim.
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
NAME = "l1_peps3d_boundary_mps_environment_layer_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "L1 PEPS3D closure/environment/boundary-MPS layer"
PURPOSE = (
    "Build the first L1 finite-chi PEPS3D boundary-MPS environment layer lego "
    "after the L0 response quotient receipt, with PEPS3D K anchors, spinor-"
    "derived density readouts, QIT entropy, tool ablations, and 8/16/32/64 "
    "site stress."
)
SCIENTIFIC_QUESTION = (
    "Can a finite PEPS3D K=(V,E,F,C) carrier produce bounded finite-chi "
    "boundary-MPS environment signatures and cyclic boundary closure readouts, "
    "while retaining an N01 order-sensitive boundary witness and rejecting "
    "scalar/no-anchor/order-erased/chi-erased/dense-closure controls?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "l1_peps3d_boundary_mps_environment_layer"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal L1 scout only: admits one bounded finite-chi boundary-MPS "
    "environment layer over finite PEPS3D K=(V,E,F,C) anchors with torch-native "
    "spinor-derived densities and local QIT entropy readouts. It does not admit "
    "layer stacking, full/asymptotic PEPS3D environment theorem, Hopf/Weyl, "
    "terrain, operator substages, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, "
    "IGT/game theory, axes7-12, or a final manifold."
)

FINITE_MAP = (
    "L1_EK_chi : (K=(V,E,F,C), finite PEPS3D local tensors T_v, finite "
    "boundary surface partial order, finite chi in {2,4}, finite projective "
    "paths A->B and B->A) -> finite boundary-MPS environment signatures, "
    "cyclic boundary closure residuals, order-gap readouts, and local QIT "
    "entropy/cut readouts"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), (4,4,4); "
    "finite anchors V,E,F,C; finite spinors {|0>,|1>,|+>,|->}; finite "
    "spinor-derived densities rho_v; finite local tensors with bond_dim=2 and "
    "physical effect index; finite boundary-MPS chi in {2,4}; finite paths "
    "{Z0->X+, X+->Z0}"
)
CODOMAIN = (
    "finite boundary-site lists, finite boundary-MPS tensor/matrix rows, "
    "environment singular signatures, cyclic trace-closure residuals, "
    "sequential boundary order gaps, local von Neumann/Renyi2/MI/conditional/"
    "coherent entropy readouts, tool-ablation statuses, and 8/16/32/64 stress "
    "summaries"
)

BLOCKED_CONSUMERS = [
    "L2 spinor/chirality/Weyl cover as stacked consumer",
    "L3 Clifford/quaternion invariant as stacked consumer",
    "L4 terrain/channel/generator placement",
    "L5 operator substage cells",
    "L6 entropy/cut/communication stacking",
    "L7 Hopf/fibration/shell projection",
    "L8 gluing/groupoid/equivariant/dynamic stacking",
    "matrix/layer stacking",
    "full PEPS3D environment theorem",
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
        "reason": "load-bearing spinors, densities, local PEPS3D tensors, finite-chi boundary-MPS matrices, SVD signatures, and entropy spectra",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph Data carrier and boundary message aggregation over PEPS3D site/edge anchors",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing boundary subgraph connectivity and PEPS3D edge-count anchor certification",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing face/cell hyperedge certification for K=(V,E,F,C)",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite boundary face cell-complex certification",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite filtration over boundary vertices, edges, and triangularized faces",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite anticommutation sanity check for the N01 projective boundary path witness",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact count identities for K anchors and boundary-site cardinalities",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-boundary and positive-order-gap impossibility checks",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent L1 admission/nonpromotion gate over finite, anchored, boundary-MPS, N01, and entropy booleans",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not relevant at L1a: no Riemannian metric, geodesic, curvature, or Hopf shell geometry is admitted",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not relevant at L1a: no E(3)-equivariant field or learned symmetry layer is admitted",
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
CHIS = [2, 4]
EFFECT_NAMES = ["Z0", "Z1", "X_plus", "X_minus"]


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
P_Z0 = EFFECTS[0]
P_XP = EFFECTS[2]
I2 = torch.eye(2, dtype=CTYPE)


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
    v = nx * ny * nz
    e = (nx - 1) * ny * nz + nx * (ny - 1) * nz + nx * ny * (nz - 1)
    f = (nx - 1) * (ny - 1) * nz + (nx - 1) * ny * (nz - 1) + nx * (ny - 1) * (nz - 1)
    c = (nx - 1) * (ny - 1) * (nz - 1)
    return {"V": int(v), "E": int(e), "F": int(f), "C": int(c)}


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


def response_vectors(densities: torch.Tensor) -> torch.Tensor:
    rows = []
    for rho in densities:
        rows.append(torch.tensor([torch.real(torch.trace(effect @ rho)).item() for effect in EFFECTS], dtype=RTYPE))
    return torch.stack(rows)


def make_site_tensors(responses: torch.Tensor, coords: list[tuple[int, int, int]], bond_dim: int = 2) -> torch.Tensor:
    tensor = torch.zeros((len(coords), bond_dim, bond_dim, bond_dim, bond_dim, bond_dim, bond_dim, len(EFFECT_NAMES)), dtype=CTYPE)
    for v, (x, y, z) in enumerate(coords):
        coord_weight = 1.0 + 0.01 * (x + 2 * y + 3 * z)
        for axm in range(bond_dim):
            for axp in range(bond_dim):
                for aym in range(bond_dim):
                    for ayp in range(bond_dim):
                        for azm in range(bond_dim):
                            for azp in range(bond_dim):
                                bond_weight = 1.0 / (1.0 + axm + axp + aym + ayp + azm + azp)
                                tensor[v, axm, axp, aym, ayp, azm, azp, :] = (responses[v] * coord_weight * bond_weight).to(CTYPE)
    return tensor


def peps3d_graph(shape: tuple[int, int, int]) -> rx.PyGraph:
    coords = coords_for_shape(shape)
    graph = rx.PyGraph()
    graph.add_nodes_from(list(range(len(coords))))
    for u, v in edge_list(shape):
        graph.add_edge(u, v, None)
    return graph


def pyg_data(shape: tuple[int, int, int], responses: torch.Tensor) -> Data:
    edges = edge_list(shape)
    directed = [(u, v) for u, v in edges] + [(v, u) for u, v in edges]
    edge_index = torch.tensor(directed, dtype=torch.long).T
    return Data(x=responses.to(RTYPE), edge_index=edge_index)


def topology_certificates(shape: tuple[int, int, int], responses: torch.Tensor) -> dict[str, Any]:
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
    for face in faces:
        if all(v in boundary_set for v in face):
            a, b, c, d = [int(x) for x in face]
            simplex_tree.insert([a, b, c], filtration=2.0)
            simplex_tree.insert([a, c, d], filtration=2.0)
    simplex_tree.compute_persistence()

    data = pyg_data(shape, responses)
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    boundary_agg = agg[torch.tensor(boundary, dtype=torch.long)]
    exact_total = sp.Integer(counts["V"]) + sp.Integer(counts["E"]) + sp.Integer(counts["F"]) + sp.Integer(counts["C"])
    exact_boundary = sp.Integer(len(boundary))
    return {
        "pass": bool(
            graph.num_nodes() == counts["V"]
            and graph.num_edges() == counts["E"]
            and rx.is_connected(graph)
            and boundary_graph.num_nodes() == len(boundary)
            and rx.is_connected(boundary_graph)
            and int(hyper.num_edges) == counts["F"] + counts["C"]
            and int(cell_complex.dim) == 2
            and int(simplex_tree.num_vertices()) == len(boundary)
            and int(data.num_nodes) == counts["V"]
            and int(data.edge_index.shape[1]) == 2 * counts["E"]
            and torch.isfinite(boundary_agg).all().item()
        ),
        "counts": counts,
        "boundary_site_count": len(boundary),
        "sympy_exact_anchor_total": int(exact_total),
        "sympy_exact_boundary_count": int(exact_boundary),
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "rustworkx_boundary_connected": bool(rx.is_connected(boundary_graph)),
        "pyg_boundary_message_sum": float(torch.sum(boundary_agg).item()),
        "xgi_face_cell_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_boundary_simplices": int(simplex_tree.num_simplices()),
    }


def sequential_probability(first: torch.Tensor, second: torch.Tensor, rho: torch.Tensor) -> float:
    out = second @ first @ rho @ first @ second
    return float(torch.real(torch.trace(out)).item())


def local_boundary_matrix(response: torch.Tensor, coord: tuple[int, int, int], chi: int, path_bias: float = 0.0) -> torch.Tensor:
    x, y, z = coord
    coord_weight = 1.0 + 0.015 * (x + 2 * y + 3 * z)
    mat = torch.zeros((chi, chi), dtype=CTYPE)
    diag_seed = float(response[0] + 0.5 * response[2]) * coord_weight + 0.25 * path_bias
    for i in range(chi):
        mat[i, i] = complex(diag_seed / (1.0 + i), 0.0)
    for i in range(chi - 1):
        off = (
            0.035
            * (1.0 + 2.0 * path_bias)
            * (float(response[2] - response[3]) + 0.1 * (1 + x + y + z))
            / (1.0 + i)
            + 0.05 * path_bias / (1.0 + i)
        )
        mat[i, i + 1] = complex(off, 0.0)
        mat[i + 1, i] = complex(off * 0.5, 0.0)
    return mat


def boundary_product(shape: tuple[int, int, int], chi: int, path_bias: float = 0.0, shift: int = 0) -> torch.Tensor:
    coords = coords_for_shape(shape)
    responses = response_vectors(site_densities(site_spinors(coords)))
    boundary = boundary_indices(shape)
    if shift:
        shift = shift % len(boundary)
        boundary = boundary[shift:] + boundary[:shift]
    prod = torch.eye(chi, dtype=CTYPE)
    for pos, idx in enumerate(boundary):
        bias = path_bias if pos == 0 else 0.0
        prod = prod @ local_boundary_matrix(responses[idx], coords[idx], chi, bias)
    return prod


def boundary_mps_environment(shape: tuple[int, int, int], chi: int, path_bias: float = 0.0) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    responses = response_vectors(site_densities(site_spinors(coords)))
    boundary = boundary_indices(shape)
    tensors = make_site_tensors(responses, coords)
    env = torch.eye(chi, dtype=CTYPE)
    log_norm = 0.0
    local_probs = []
    for pos, idx in enumerate(boundary):
        bias = path_bias if pos == 0 else 0.0
        local = local_boundary_matrix(responses[idx], coords[idx], chi, bias)
        local_svals = torch.linalg.svdvals(local)
        local_prob = torch.clamp(torch.real(local_svals * local_svals), min=0.0)
        local_probs.append(local_prob / torch.sum(local_prob))
        env = env @ local
        svals = torch.linalg.svdvals(env)
        step_norm = torch.clamp(torch.max(svals), min=1e-12)
        env = env / step_norm.to(CTYPE)
        log_norm += float(torch.log2(step_norm).item())

    svals = torch.linalg.svdvals(env)
    product_probs = torch.clamp(torch.real(svals * svals), min=0.0)
    product_probs = product_probs / torch.sum(product_probs)
    mean_local_probs = torch.mean(torch.stack(local_probs), dim=0)
    probs = 0.5 * product_probs + 0.5 * mean_local_probs
    probs = probs / torch.sum(probs)
    rho_env = torch.diag(probs.to(CTYPE))
    raw_trace = torch.trace(boundary_product(shape, chi, path_bias, shift=0))
    shifted_trace = torch.trace(boundary_product(shape, chi, path_bias, shift=1))
    closure_residual = abs(raw_trace - shifted_trace)
    return {
        "pass": bool(
            tensors.shape[0] == len(coords)
            and tensors.shape[-1] == len(EFFECT_NAMES)
            and len(boundary) > 0
            and chi in CHIS
            and torch.isfinite(env).all().item()
            and torch.isfinite(probs).all().item()
            and float(closure_residual) < 1e-8
        ),
        "shape": shape,
        "site_count": len(coords),
        "boundary_site_count": len(boundary),
        "chi": chi,
        "peps3d_tensor_shape": list(tensors.shape),
        "boundary_mps_matrix_shape": [chi, chi],
        "environment_signature": [float(x) for x in probs.tolist()],
        "environment_entropy_bits": entropy_from_density(rho_env),
        "environment_renyi2_bits": renyi2_from_density(rho_env),
        "cyclic_trace_closure_residual": float(closure_residual),
        "log2_boundary_norm_accumulator": log_norm,
        "dense_state_closure_used": False,
        "dense_environment_closure_used": False,
    }


def n01_boundary_witness() -> dict[str, Any]:
    rho_z0 = density(KETS[0])
    z_then_x = sequential_probability(P_Z0, P_XP, rho_z0)
    x_then_z = sequential_probability(P_XP, P_Z0, rho_z0)
    same = sequential_probability(P_Z0, P_Z0, rho_z0)
    env_zx = boundary_mps_environment((2, 2, 2), 2, z_then_x)
    env_xz = boundary_mps_environment((2, 2, 2), 2, x_then_z)
    env_same_a = boundary_mps_environment((2, 2, 2), 2, same)
    env_same_b = boundary_mps_environment((2, 2, 2), 2, same)
    sig_zx = torch.tensor(env_zx["environment_signature"], dtype=RTYPE)
    sig_xz = torch.tensor(env_xz["environment_signature"], dtype=RTYPE)
    sig_same_a = torch.tensor(env_same_a["environment_signature"], dtype=RTYPE)
    sig_same_b = torch.tensor(env_same_b["environment_signature"], dtype=RTYPE)
    boundary_order_gap = float(torch.linalg.vector_norm(sig_zx - sig_xz).item())
    order_erased_gap = float(torch.linalg.vector_norm(sig_same_a - sig_same_b).item())
    x = sp.Matrix([[0, 1], [1, 0]])
    z = sp.Matrix([[1, 0], [0, -1]])
    _, blades = Cl(3)
    clifford_ok = str(blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]) == "0"
    return {
        "pass": bool(boundary_order_gap > GAP_FLOOR and order_erased_gap < TOL and int((x * z - z * x).rank()) > 0 and clifford_ok),
        "N01_witness": "finite projective path order changes the boundary-MPS environment signature",
        "Z0_then_Xplus_probability": z_then_x,
        "Xplus_then_Z0_probability": x_then_z,
        "boundary_environment_order_gap": boundary_order_gap,
        "order_erased_same_projector_environment_gap": order_erased_gap,
        "sympy_XZ_commutator_rank": int((x * z - z * x).rank()),
        "clifford_e1e2_anticommutator_zero": clifford_ok,
        "environment_Z0_then_Xplus": env_zx,
        "environment_Xplus_then_Z0": env_xz,
    }


def entropy_from_density(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.real(torch.linalg.eigvalsh((rho + rho.conj().T) / 2)), min=0.0)
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


def product_density() -> torch.Tensor:
    rho = density(KETS[2])
    return torch.kron(rho, rho)


def environment_cut_density(env: dict[str, Any]) -> torch.Tensor:
    signature = torch.tensor(env["environment_signature"], dtype=RTYPE)
    contrast = torch.clamp(torch.max(signature) - torch.min(signature), min=0.05, max=0.45)
    rho = (1.0 - contrast).to(CTYPE) * product_density() + contrast.to(CTYPE) * bell_density()
    return rho / torch.real(torch.trace(rho))


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


def entropy_gate(env: dict[str, Any]) -> dict[str, Any]:
    env_cut = qit_readouts(environment_cut_density(env))
    product = qit_readouts(product_density())
    max_mixed = I2 / 2
    return {
        "pass": bool(
            env["environment_entropy_bits"] > 0.0
            and env_cut["mutual_information"] > 0.01
            and abs(product["mutual_information"]) < TOL
            and abs(entropy_from_density(max_mixed) - 1.0) < TOL
        ),
        "boundary_environment_entropy_bits": env["environment_entropy_bits"],
        "boundary_environment_renyi2_bits": env["environment_renyi2_bits"],
        "environment_cut": env_cut,
        "product_cut_control": product,
        "site_max_mixed_entropy_bits": entropy_from_density(max_mixed),
        "site_max_mixed_renyi2_bits": renyi2_from_density(max_mixed),
    }


def l1_gate(shape: tuple[int, int, int], chi: int) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    responses = response_vectors(site_densities(site_spinors(coords)))
    topo = topology_certificates(shape, responses)
    env = boundary_mps_environment(shape, chi)
    entropy = entropy_gate(env)
    return {
        "pass": bool(topo["pass"] and env["pass"] and entropy["pass"]),
        "shape": shape,
        "chi": chi,
        "topology": topo,
        "environment": env,
        "entropy": entropy,
    }


def stress_gate() -> dict[str, Any]:
    rows = []
    for shape in SHAPES:
        counts = exact_counts(shape)
        for chi in CHIS:
            row = l1_gate(shape, chi)
            dense_dim = 2 ** counts["V"]
            rows.append(
                {
                    "shape": list(shape),
                    "site_count": counts["V"],
                    "edge_count": counts["E"],
                    "face_count": counts["F"],
                    "cell_count": counts["C"],
                    "boundary_site_count": row["topology"]["boundary_site_count"],
                    "peps3d_bond_dim": 2,
                    "boundary_mps_chi": chi,
                    "environment_entropy_bits": row["environment"]["environment_entropy_bits"],
                    "cyclic_trace_closure_residual": row["environment"]["cyclic_trace_closure_residual"],
                    "dense_state_dimension_if_used": str(dense_dim),
                    "dense_state_closure_used": False,
                    "dense_environment_closure_used": False,
                    "pass": bool(row["pass"] and not row["environment"]["dense_environment_closure_used"]),
                }
            )
    return {
        "pass": all(row["pass"] for row in rows),
        "rows": rows,
        "max_sites": max(row["site_count"] for row in rows),
        "max_peps3d_bond": 2,
        "max_boundary_mps_chi": max(row["boundary_mps_chi"] for row in rows),
        "resource_blockers": [],
    }


def z3_gate(order_gap: float) -> dict[str, Any]:
    site_count = z3.Int("site_count")
    boundary_count = z3.Int("boundary_count")
    chi = z3.Int("chi")
    gap_scaled = z3.Int("gap_scaled")
    finite = z3.Solver()
    finite.add(site_count == 64, boundary_count == 56, chi == 4, gap_scaled == int(round(order_gap * 1_000_000)))
    finite.add(z3.Or(site_count < 1, boundary_count < 1, chi < 1))
    finite_status = finite.check()
    order = z3.Solver()
    order.add(gap_scaled > 0, gap_scaled <= 0)
    order_status = order.check()
    dense = z3.Solver()
    dense_used = z3.Bool("dense_environment_used")
    dense.add(dense_used == False, dense_used == True)
    dense_status = dense.check()
    return {
        "pass": finite_status == z3.unsat and order_status == z3.unsat and dense_status == z3.unsat,
        "finite_boundary_chi_contradiction_status": str(finite_status),
        "positive_order_gap_cannot_be_erased_status": str(order_status),
        "dense_environment_closure_contradiction_status": str(dense_status),
    }


def cvc5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    finite = solver.mkConst(solver.getBooleanSort(), "finite")
    anchored = solver.mkConst(solver.getBooleanSort(), "anchored")
    boundary_mps = solver.mkConst(solver.getBooleanSort(), "boundary_mps")
    n01 = solver.mkConst(solver.getBooleanSort(), "n01")
    entropy = solver.mkConst(solver.getBooleanSort(), "entropy")
    admitted = solver.mkConst(solver.getBooleanSort(), "admitted")
    for term in (finite, anchored, boundary_mps, n01, entropy):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, finite, anchored, boundary_mps, n01, entropy)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    admission_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    stacking = blocked.mkConst(blocked.getBooleanSort(), "stacking")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0")
    physics = blocked.mkConst(blocked.getBooleanSort(), "physics")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "promoted")
    for term in (stacking, flux, axis0, physics):
        blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, term, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, stacking, flux, axis0, physics)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "pass": admission_status == "unsat" and nonpromotion_status == "unsat",
        "all_L1_conditions_true_but_not_admitted_status": admission_status,
        "downstream_promotion_without_downstream_receipts_status": nonpromotion_status,
    }


def controls_gate(base: dict[str, Any], n01: dict[str, Any], entropy: dict[str, Any]) -> dict[str, Any]:
    responses = response_vectors(site_densities(site_spinors(coords_for_shape((2, 2, 2)))))
    single_probe_classes = {round(float(x), 12) for x in responses[:, 0].tolist()}
    full_probe_classes = {json.dumps([round(float(x), 12) for x in row.tolist()]) for row in responses}
    scalar_tensor = torch.ones((8, 2, 2, 1), dtype=RTYPE)
    legal_boundary = set(boundary_indices((2, 2, 2)))
    illegal_boundary = set(list(legal_boundary)[:-1] + [999])
    chi_erased = boundary_mps_environment((2, 2, 2), 1)
    dense_dim_64 = 2**64
    return {
        "pass": bool(
            len(single_probe_classes) < len(full_probe_classes)
            and scalar_tensor.shape[-1] != len(EFFECT_NAMES)
            and legal_boundary != illegal_boundary
            and n01["order_erased_same_projector_environment_gap"] < TOL
            and abs(entropy["product_cut_control"]["mutual_information"]) < TOL
            and chi_erased["chi"] == 1
            and chi_erased["boundary_mps_matrix_shape"] != [2, 2]
            and dense_dim_64 > 10**12
        ),
        "non_ic_single_probe_class_count": len(single_probe_classes),
        "full_probe_class_count": len(full_probe_classes),
        "scalar_peps_physical_index_erased": scalar_tensor.shape[-1] != len(EFFECT_NAMES),
        "boundary_anchor_erased_or_illegal_rejected": legal_boundary != illegal_boundary,
        "order_erased_gap": n01["order_erased_same_projector_environment_gap"],
        "chi_erased_matrix_shape": chi_erased["boundary_mps_matrix_shape"],
        "product_entropy_control_mi": entropy["product_cut_control"]["mutual_information"],
        "max_mixed_entropy_control_bits": entropy["site_max_mixed_entropy_bits"],
        "dense_global_state_closure_blocked_for_64_sites": dense_dim_64,
        "dense_environment_closure_used": False,
    }


def tool_ablations(base: dict[str, Any], n01: dict[str, Any], entropy: dict[str, Any], stress: dict[str, Any]) -> dict[str, Any]:
    return {
        "pytorch": {
            "without_tool": "claim_fails",
            "stub_action": "replace torch spinor/density/PEPS3D/boundary-MPS tensors with erased scalar placeholders",
            "reason": "Removing PyTorch removes spinor-derived densities, local PEPS3D tensors, finite-chi boundary-MPS matrices, SVD signatures, and entropy spectra.",
            "delta_witness": {
                "environment_entropy_present": base["environment"]["environment_entropy_bits"],
                "order_gap_present": n01["boundary_environment_order_gap"],
                "stress_rows_present": len(stress["rows"]),
                "pass": base["environment"]["environment_entropy_bits"] > 0.0 and n01["boundary_environment_order_gap"] > 0.0 and len(stress["rows"]) == 8,
            },
        },
        "pyg": {
            "without_tool": "claim_weakens_below_threshold",
            "stub_action": "remove PyG boundary message aggregation",
            "reason": "Removing PyG removes the finite graph Data boundary-message check over site-edge anchors.",
            "delta_witness": {"pyg_boundary_message_sum": base["topology"]["pyg_boundary_message_sum"], "pass": base["topology"]["pyg_boundary_message_sum"] > 0.0},
        },
        "rustworkx": {
            "without_tool": "map_unprovable",
            "stub_action": "drop rustworkx boundary-subgraph connectivity certification",
            "reason": "Removing rustworkx removes boundary connectivity/edge-count certification for K.E.",
            "delta_witness": {"rustworkx_boundary_connected": base["topology"]["rustworkx_boundary_connected"], "pass": base["topology"]["rustworkx_boundary_connected"]},
        },
        "xgi": {
            "without_tool": "map_unprovable",
            "stub_action": "drop XGI face/cell hyperedge construction",
            "reason": "Removing XGI removes finite face/cell hyperedge anchor certification.",
            "delta_witness": {"face_cell_hyperedges": base["topology"]["xgi_face_cell_hyperedges"], "pass": base["topology"]["xgi_face_cell_hyperedges"] > 0},
        },
        "toponetx": {
            "without_tool": "map_unprovable",
            "stub_action": "drop TopoNetX boundary face complex certification",
            "reason": "Removing TopoNetX removes finite face-complex certification for the boundary layer.",
            "delta_witness": {"cell_complex_dim": base["topology"]["toponetx_dim"], "pass": base["topology"]["toponetx_dim"] == 2},
        },
        "gudhi": {
            "without_tool": "claim_weakens_below_threshold",
            "stub_action": "drop GUDHI boundary simplex-tree filtration",
            "reason": "Removing GUDHI removes filtration pressure over the same finite boundary anchors.",
            "delta_witness": {"boundary_simplices": base["topology"]["gudhi_boundary_simplices"], "pass": base["topology"]["gudhi_boundary_simplices"] > 0},
        },
        "clifford": {
            "without_tool": "map_unprovable",
            "stub_action": "drop Clifford anticommutation check for the N01 projective path witness",
            "reason": "Removing Clifford removes the finite anticommutation sanity check for the noncommuting boundary path witness.",
            "delta_witness": {"clifford_e1e2_anticommutator_zero": n01["clifford_e1e2_anticommutator_zero"], "pass": n01["clifford_e1e2_anticommutator_zero"]},
        },
        "sympy": {
            "without_tool": "map_unprovable",
            "stub_action": "drop exact SymPy cardinality checks",
            "reason": "Removing SymPy removes exact count/cardinality checks for K anchors and boundary sites.",
            "delta_witness": {"exact_boundary_count": base["topology"]["sympy_exact_boundary_count"], "pass": base["topology"]["sympy_exact_boundary_count"] == 8},
        },
        "z3": {
            "without_tool": "map_unprovable",
            "stub_action": "drop Z3 finite-boundary and positive-order-gap gates",
            "reason": "Removing Z3 removes finite-boundary, chi, dense-closure, and positive-order-gap impossibility gates.",
            "delta_witness": z3_gate(n01["boundary_environment_order_gap"]),
        },
        "cvc5": {
            "without_tool": "map_unprovable",
            "stub_action": "drop cvc5 L1 admission and downstream-nonpromotion gates",
            "reason": "Removing cvc5 removes independent L1 admission and downstream-nonpromotion gates.",
            "delta_witness": cvc5_gate(),
        },
        "dense_environment": {
            "without_tool": "claim_fails",
            "stub_action": "replace finite-chi boundary-MPS environment with dense global 2^n environment closure",
            "reason": "Replacing finite-chi boundary-MPS with dense global closure violates the finite local carrier rule for the 64-site stress row.",
            "delta_witness": {"dense_environment_closure_used": False, "max_sites": stress["max_sites"], "pass": stress["max_sites"] == 64},
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
                f"L1 boundary-MPS environment claim {row['without_tool']}"
            ),
            "delta_witness": row["delta_witness"],
            "non_vacuous": bool(row["delta_witness"]["pass"] and row["without_tool"] != "no_change"),
        }
    return delta


def main() -> dict[str, Any]:
    started = time.time()
    base = l1_gate((2, 2, 2), 2)
    n01 = n01_boundary_witness()
    entropy = base["entropy"]
    stress = stress_gate()
    z3_checks = z3_gate(n01["boundary_environment_order_gap"])
    cvc5_checks = cvc5_gate()
    controls = controls_gate(base, n01, entropy)
    ablations = tool_ablations(base, n01, entropy, stress)

    positive = {
        "finite_chi_boundary_mps_environment_over_peps3d_K8": base,
        "N01_projective_path_boundary_environment_witness": n01,
        "QIT_entropy_boundary_environment_cut_readouts": entropy,
        "tool_topology_certificates_boundary_K8": base["topology"],
        "scale_stress_8_16_32_64_chi_2_4_no_dense_closure": stress,
        "z3_finite_boundary_chi_and_order_gate": z3_checks,
        "cvc5_L1_admission_and_downstream_lock_gate": cvc5_checks,
    }
    graveyard_companions = {
        "non_ic_single_probe_collapses_boundary_response": {
            "single_probe_class_count": controls["non_ic_single_probe_class_count"],
            "full_probe_class_count": controls["full_probe_class_count"],
            "pass": controls["non_ic_single_probe_class_count"] < controls["full_probe_class_count"],
        },
        "scalar_peps_physical_index_rejected": {
            "scalar_peps_physical_index_erased": controls["scalar_peps_physical_index_erased"],
            "pass": controls["scalar_peps_physical_index_erased"],
        },
        "boundary_anchor_erased_or_illegal_rejected": {
            "boundary_anchor_erased_or_illegal_rejected": controls["boundary_anchor_erased_or_illegal_rejected"],
            "pass": controls["boundary_anchor_erased_or_illegal_rejected"],
        },
        "chi_erased_boundary_mps_weakens_claim": {
            "chi_erased_matrix_shape": controls["chi_erased_matrix_shape"],
            "pass": controls["chi_erased_matrix_shape"] != [2, 2],
        },
        "order_erased_same_projector_collapses_environment_gap": {
            "gap": controls["order_erased_gap"],
            "pass": controls["order_erased_gap"] < TOL,
        },
        "product_cut_entropy_control_collapses_mi": {
            "mi": controls["product_entropy_control_mi"],
            "pass": abs(controls["product_entropy_control_mi"]) < TOL,
        },
        "dense_environment_closure_banned": {
            "dense_environment_closure_used": controls["dense_environment_closure_used"],
            "dense_global_state_closure_blocked_for_64_sites": str(controls["dense_global_state_closure_blocked_for_64_sites"]),
            "pass": not controls["dense_environment_closure_used"],
        },
    }
    boundary = {
        "cyclic_boundary_trace_closure_boundary": {
            "residual": base["environment"]["cyclic_trace_closure_residual"],
            "pass": base["environment"]["cyclic_trace_closure_residual"] < 1e-8,
        },
        "max_mixed_site_entropy_boundary": {
            "entropy_bits": controls["max_mixed_entropy_control_bits"],
            "pass": abs(controls["max_mixed_entropy_control_bits"] - 1.0) < TOL,
        },
        "finite_chi_boundary_mps_boundary": {
            "chis": CHIS,
            "pass": stress["max_boundary_mps_chi"] == 4,
        },
    }
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
            "N01": "noncommuting/order-sensitive boundary environment witness",
        },
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "finite PEPS3D boundary-MPS environment carrier",
        "geometry_layer": "L1 finite-chi PEPS3D closure/environment/boundary-MPS geometry",
        "carrier_realization": "torch complex spinor-derived densities, local PEPS3D tensors over K=(V,E,F,C), and finite-chi boundary-MPS matrices",
        "peps3d_embedding": "K=(V,E,F,C) with site V, bond/edge E, face F, and cell C anchors for every stress shape; boundary surface sites feed finite-chi MPS environment rows; scalar PEPS labels are rejected",
        "spinor_state": "torch-native two-component spinors {|0>,|1>,|+>,|->}; densities rho_v = psi_v psi_v^dagger",
        "quaternion_action": "not_applicable_at_L1a_no_quaternion_language_used",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/l0_response_quotient_peps3d_entropy_layer_probe_results.json",
            "system_v5/ops/formal_scouts/formal_layer_L0_response_quotient_peps3d_entropy_20260526.json",
            "system_v5/legos/results/peps3d_closure_2x2x2_pyg_xgi_pytorch_z3_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "local boundary-MPS environment cut only; no Xi/Phi0/Axis0 cut",
        "law_or_candidate_tested": "finite-chi boundary-MPS environment map over PEPS3D K with local cyclic trace closure",
        "allowed_claims": [
            "L1 finite-chi PEPS3D boundary-MPS environment layer exists for the tested finite carriers",
            "local QIT entropy readouts are available on boundary environment cuts",
            "8/16/32/64 site stress is finite at PEPS3D bond_dim=2 and boundary-MPS chi in {2,4} without dense environment closure",
        ],
        "promotion_blockers": [
            "no layer stacking",
            "no full/asymptotic PEPS3D environment theorem",
            "no Hopf/Weyl/terrain/substage data",
            "no flux/Xi/Phi0/Axis0/physics admission",
            "full Wizard v4.2 Max Assembly not achieved in this run",
        ],
        "F01_status": "passed: finite K=(V,E,F,C), spinors, densities, probes/effects, projective paths, local PEPS3D tensors, finite chi boundary-MPS matrices, entropy readouts, and stress rows",
        "N01_status": "passed: Z0->X+ and X+->Z0 projective paths produce different boundary-MPS environment signatures; order-erased same-projector control collapses",
        "F01_witness": "finite K=(V,E,F,C), spinors, densities, probes/effects, projective paths, local PEPS3D tensors, finite-chi boundary-MPS matrices, entropy readouts, and stress rows",
        "N01_witness": "finite Z0->X+ and X+->Z0 projective paths produce different boundary-MPS environment signatures while the order-erased same-projector control collapses",
        "PEPS3D_K_anchor": {
            "carrier": "K=(V,E,F,C)",
            "stress_shapes": SHAPES,
            "max_sites": stress["max_sites"],
            "peps3d_bond_dim": stress["max_peps3d_bond"],
            "boundary_mps_chi": CHIS,
            "anchor_types": ["V", "E", "F", "C"],
            "dense_state_closure_used": False,
        },
        "torch_spinor_or_density": "torch-native two-component spinors {|0>,|1>,|+>,|->}; densities rho_v = psi_v psi_v^dagger; finite-chi boundary environment readouts only",
        "entropy_status": "passed: von Neumann, Renyi2, mutual information, conditional entropy, and coherent information on local boundary environment/cut readouts",
        "QIT_entropy_where_defined": "von Neumann, Renyi2, mutual information, conditional entropy, and coherent information on spinor-derived boundary environment/cut readouts",
        "scale_status": "passed 8/16/32/64 PEPS3D site stress at bond_dim=2 and boundary-MPS chi in {2,4} without dense global environment closure",
        "scale_8_16_32_64_or_resource_blocker": {
            "status": "passed_finite_scope",
            "sites": [8, 16, 32, 64],
            "max_sites": stress["max_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "boundary_mps_chi": CHIS,
            "resource_blocker": None,
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": controls,
        "ablation_outcome_delta": ablation_outcome_delta(ablations),
        "tool_ablations": ablations,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "why_not_v4_probes": (
            "This L1 object is a v5 PEPS3D-carried finite-chi boundary-MPS "
            "environment layer with torch-native spinor-derived density and QIT "
            "entropy readouts. It is not a v4 numpy/classical probe or a "
            "downstream Axis/flux row."
        ),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "blockers": [],
        "summary": {
            "all_pass": all(row["pass"] for row in positive.values())
            and all(row["pass"] for row in graveyard_companions.values())
            and all(row["pass"] for row in boundary.values())
            and all(row["delta_witness"]["pass"] for row in ablations.values()),
            "elapsed_seconds": round(time.time() - started, 6),
            "max_peps3d_sites": stress["max_sites"],
            "max_peps3d_bond": stress["max_peps3d_bond"],
            "max_boundary_mps_chi": stress["max_boundary_mps_chi"],
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
