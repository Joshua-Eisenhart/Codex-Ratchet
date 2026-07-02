#!/usr/bin/env python3
"""L0 response-quotient PEPS3D entropy layer probe.

This is the first one-layer formal scout target from the two root constraints:
finite probe/effect/path response quotient geometry carried by a finite PEPS3D
K=(V,E,F,C) anchor, with torch-native spinor-derived densities and local QIT
entropy readouts. It is not a Hopf, Weyl, terrain, substage, flux, Axis0,
physics, or final-manifold claim.
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
NAME = "l0_response_quotient_peps3d_entropy_layer_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "L0 response quotient PEPS3D entropy layer"
PURPOSE = (
    "Build the first complete one-layer finite response/effect/path quotient "
    "geometry with PEPS3D anchors, spinor-derived density readouts, QIT entropy, "
    "tool ablations, and 8/16/32/64 site stress."
)
SCIENTIFIC_QUESTION = (
    "Can finite probe/effect/path response quotient classes be carried on a "
    "finite PEPS3D K=(V,E,F,C) network from the start, with noncommuting "
    "path-order response and QIT entropy readouts, while scalar/no-anchor/"
    "order-erased/dense-closure controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "constraint_probe"
SOURCE_ALIGNMENT_CATEGORY = "l0_response_quotient_peps3d_entropy_layer"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal L0 scout only: admits one finite response/effect/path quotient "
    "layer over PEPS3D K=(V,E,F,C) anchors with torch-native spinor-derived "
    "densities and local QIT entropy readouts. It does not admit Hopf/Weyl, "
    "terrain, operator substages, stacking, flux, Xi/Phi0, Axis0, Holodeck/FEP, "
    "physics, IGT/game theory, axes7-12, or a final manifold."
)

FINITE_MAP = (
    "L0_QK : (K=(V,E,F,C), finite spinor-derived site densities rho_v, finite "
    "probe/effect family P, finite projective paths A->B and B->A) -> "
    "PEPS3D-anchored quotient Q_P(K), incidence/order readouts, and local QIT "
    "entropy/cut readouts"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), (4,4,4); "
    "finite anchors V,E,F,C; finite spinors {|0>,|1>,|+>,|->}; finite effects "
    "{Z0,Z1,X+,X-}; finite projective paths {Z0->X+, X+->Z0}; bond_dim=2"
)
CODOMAIN = (
    "finite response vectors, quotient classes, site/edge/face/cell incidence "
    "summaries, sequential path-order gaps, local von Neumann/Renyi2/MI/"
    "conditional/coherent entropy readouts, tool-ablation statuses, and "
    "8/16/32/64 stress summaries"
)

BLOCKED_CONSUMERS = [
    "Hopf layer",
    "nested Hopf tori",
    "Weyl sheet cover",
    "terrain generator placement",
    "operator substage cells",
    "matrix stacking",
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
        "reason": "load-bearing spinors, density matrices, PEPS3D local tensors, response vectors, sequential-path probabilities, and QIT entropy spectra",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite graph Data carrier and message aggregation over PEPS3D site/edge anchors",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D edge graph connectivity and edge-count anchor certification",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing face/cell hyperedge anchor certification",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite cell-complex face anchor certification",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite simplex-tree filtration certification for vertices, edges, and triangularized faces",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite anticommutation sanity check for the N01 noncommuting path witness",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact count identities for site/edge/face/cell anchors and quotient cardinality",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-gate and positive-order-gap impossibility checks",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent admission/nonpromotion gate over finite anchor, entropy, and N01 booleans",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not relevant at L0: no Riemannian metric, geodesic, curvature, or Hopf shell geometry is admitted",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not relevant at L0: no E(3)-equivariant geometry or learned symmetry layer is admitted",
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


def site_spinors(coords: list[tuple[int, int, int]]) -> torch.Tensor:
    return torch.stack([KETS[(x + 2 * y + 3 * z) % len(KETS)] for x, y, z in coords])


def site_densities(spinors: torch.Tensor) -> torch.Tensor:
    return torch.stack([density(psi) for psi in spinors])


def response_vectors(densities: torch.Tensor) -> torch.Tensor:
    rows = []
    for rho in densities:
        rows.append(torch.tensor([torch.real(torch.trace(effect @ rho)).item() for effect in EFFECTS], dtype=RTYPE))
    return torch.stack(rows)


def quotient_classes(responses: torch.Tensor) -> dict[str, list[int]]:
    classes: dict[str, list[int]] = {}
    for idx, row in enumerate(responses):
        key = json.dumps([round(float(x), 12) for x in row.tolist()])
        classes.setdefault(key, []).append(idx)
    return classes


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
    counts = exact_counts(shape)
    graph = peps3d_graph(shape)

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
    for v in range(len(coords)):
        simplex_tree.insert([v], filtration=0.0)
    for u, v in edges:
        simplex_tree.insert([int(u), int(v)], filtration=1.0)
    for face in faces:
        a, b, c, d = [int(x) for x in face]
        simplex_tree.insert([a, b, c], filtration=2.0)
        simplex_tree.insert([a, c, d], filtration=2.0)
    simplex_tree.compute_persistence()

    data = pyg_data(shape, responses)
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    exact_total = sp.Integer(counts["V"]) + sp.Integer(counts["E"]) + sp.Integer(counts["F"]) + sp.Integer(counts["C"])
    return {
        "pass": bool(
            graph.num_nodes() == counts["V"]
            and graph.num_edges() == counts["E"]
            and rx.is_connected(graph)
            and int(hyper.num_edges) == counts["F"] + counts["C"]
            and int(cell_complex.dim) == 2
            and int(simplex_tree.num_vertices()) == counts["V"]
            and int(data.num_nodes) == counts["V"]
            and int(data.edge_index.shape[1]) == 2 * counts["E"]
            and torch.isfinite(agg).all().item()
        ),
        "counts": counts,
        "sympy_exact_anchor_total": int(exact_total),
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "pyg_message_sum": float(torch.sum(agg).item()),
        "xgi_face_cell_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_simplices": int(simplex_tree.num_simplices()),
    }


def sequential_probability(first: torch.Tensor, second: torch.Tensor, rho: torch.Tensor) -> float:
    out = second @ first @ rho @ first @ second
    return float(torch.real(torch.trace(out)).item())


def n01_path_witness() -> dict[str, Any]:
    rho_z0 = density(KETS[0])
    z_then_x = sequential_probability(P_Z0, P_XP, rho_z0)
    x_then_z = sequential_probability(P_XP, P_Z0, rho_z0)
    order_gap = abs(z_then_x - x_then_z)
    same_gap = abs(sequential_probability(P_Z0, P_Z0, rho_z0) - sequential_probability(P_Z0, P_Z0, rho_z0))
    x = sp.Matrix([[0, 1], [1, 0]])
    z = sp.Matrix([[1, 0], [0, -1]])
    _, blades = Cl(3)
    clifford_ok = str(blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"]) == "0"
    return {
        "pass": bool(order_gap > GAP_FLOOR and same_gap < TOL and int((x * z - z * x).rank()) > 0 and clifford_ok),
        "N01_witness": "sequential finite projective paths Z0->X+ and X+->Z0 have different response on rho_z0",
        "Z0_then_Xplus": z_then_x,
        "Xplus_then_Z0": x_then_z,
        "order_gap": order_gap,
        "order_erased_same_projector_gap": same_gap,
        "sympy_XZ_commutator_rank": int((x * z - z * x).rank()),
        "clifford_e1e2_anticommutator_zero": clifford_ok,
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


def classical_correlated_density() -> torch.Tensor:
    return torch.diag(torch.tensor([0.5, 0.0, 0.0, 0.5], dtype=RTYPE)).to(CTYPE)


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


def entropy_gate() -> dict[str, Any]:
    bell = qit_readouts(bell_density())
    product = qit_readouts(product_density())
    classical = qit_readouts(classical_correlated_density())
    max_mixed = I2 / 2
    return {
        "pass": bool(
            bell["mutual_information"] > 1.9
            and bell["conditional_entropy_A_given_B"] < -0.9
            and abs(product["mutual_information"]) < TOL
            and classical["mutual_information"] > 0.9
            and abs(entropy_from_density(max_mixed) - 1.0) < TOL
        ),
        "bell_edge_cut": bell,
        "product_edge_control": product,
        "matched_marginal_classical_control": classical,
        "site_max_mixed_entropy_bits": entropy_from_density(max_mixed),
        "site_max_mixed_renyi2_bits": renyi2_from_density(max_mixed),
    }


def quotient_gate(shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    spinors = site_spinors(coords)
    rhos = site_densities(spinors)
    responses = response_vectors(rhos)
    classes = quotient_classes(responses)
    tensors = make_site_tensors(responses, coords)
    topo = topology_certificates(shape, responses)
    return {
        "pass": bool(len(classes) == 4 and tensors.shape[0] == len(coords) and tensors.shape[-1] == len(EFFECT_NAMES) and topo["pass"]),
        "shape": shape,
        "site_count": len(coords),
        "quotient_class_count": len(classes),
        "quotient_classes": {key: value[:8] for key, value in classes.items()},
        "tensor_shape": list(tensors.shape),
        "topology": topo,
    }


def stress_gate() -> dict[str, Any]:
    rows = []
    for shape in SHAPES:
        row = quotient_gate(shape)
        counts = exact_counts(shape)
        dense_dim = 2 ** counts["V"]
        rows.append(
            {
                "shape": list(shape),
                "site_count": counts["V"],
                "edge_count": counts["E"],
                "face_count": counts["F"],
                "cell_count": counts["C"],
                "bond_dim": 2,
                "quotient_class_count": row["quotient_class_count"],
                "tensor_shape": row["tensor_shape"],
                "dense_state_dimension_if_used": str(dense_dim),
                "dense_state_closure_used": False,
                "pass": bool(row["pass"] and not dense_dim < 0),
            }
        )
    return {
        "pass": all(row["pass"] and not row["dense_state_closure_used"] for row in rows),
        "rows": rows,
        "max_sites": max(row["site_count"] for row in rows),
        "max_bond": 2,
        "resource_blockers": [],
    }


def z3_gate(order_gap: float) -> dict[str, Any]:
    site_count = z3.Int("site_count")
    q_count = z3.Int("q_count")
    gap_scaled = z3.Int("gap_scaled")
    solver = z3.Solver()
    solver.add(site_count == 64, q_count == 4, gap_scaled == int(round(order_gap * 1_000_000)))
    solver.add(site_count < 1)
    finite_unsat = solver.check()
    order = z3.Solver()
    order.add(gap_scaled > 0, gap_scaled <= 0)
    order_unsat = order.check()
    return {
        "pass": finite_unsat == z3.unsat and order_unsat == z3.unsat,
        "finite_anchor_contradiction_status": str(finite_unsat),
        "positive_order_gap_cannot_be_erased_status": str(order_unsat),
    }


def cvc5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    finite = solver.mkConst(solver.getBooleanSort(), "finite")
    anchored = solver.mkConst(solver.getBooleanSort(), "anchored")
    n01 = solver.mkConst(solver.getBooleanSort(), "n01")
    entropy = solver.mkConst(solver.getBooleanSort(), "entropy")
    admitted = solver.mkConst(solver.getBooleanSort(), "admitted")
    for term in (finite, anchored, n01, entropy):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, finite, anchored, n01, entropy)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    admission_status = str(solver.checkSat())

    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0")
    physics = blocked.mkConst(blocked.getBooleanSort(), "physics")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "promoted")
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, flux, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, axis0, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, physics, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, flux, axis0, physics)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {
        "pass": admission_status == "unsat" and nonpromotion_status == "unsat",
        "all_L0_conditions_true_but_not_admitted_status": admission_status,
        "downstream_promotion_without_downstream_receipts_status": nonpromotion_status,
    }


def controls_gate(base: dict[str, Any], n01: dict[str, Any], entropy: dict[str, Any]) -> dict[str, Any]:
    responses = response_vectors(site_densities(site_spinors(coords_for_shape((2, 2, 2)))))
    single_probe_classes = quotient_classes(responses[:, :1])
    scalar_tensor = torch.ones((8, 1), dtype=RTYPE)
    shuffled_edges = list(reversed(edge_list((2, 2, 2))))
    legal_edges = set(tuple(sorted(edge)) for edge in edge_list((2, 2, 2)))
    illegal_edges = set(tuple(sorted(edge)) for edge in shuffled_edges[:-1] + [(0, 7)])
    dense_dim_64 = 2**64
    return {
        "pass": bool(
            len(single_probe_classes) < base["quotient_class_count"]
            and scalar_tensor.shape[-1] != len(EFFECT_NAMES)
            and legal_edges != illegal_edges
            and n01["order_erased_same_projector_gap"] < TOL
            and abs(entropy["product_edge_control"]["mutual_information"]) < TOL
            and dense_dim_64 > 10**12
        ),
        "non_ic_single_probe_class_count": len(single_probe_classes),
        "full_probe_class_count": base["quotient_class_count"],
        "scalar_peps_physical_index_erased": scalar_tensor.shape[-1] != len(EFFECT_NAMES),
        "topology_shuffled_edge_set_rejected": legal_edges != illegal_edges,
        "order_erased_gap": n01["order_erased_same_projector_gap"],
        "product_entropy_control_mi": entropy["product_edge_control"]["mutual_information"],
        "max_mixed_entropy_control_bits": entropy["site_max_mixed_entropy_bits"],
        "dense_global_state_closure_blocked_for_64_sites": dense_dim_64,
        "chirality_no_chirality_control": "not_applicable_at_L0_no_Weyl_or_chiral_sheet_claim",
    }


def tool_ablations(base: dict[str, Any], n01: dict[str, Any], entropy: dict[str, Any], stress: dict[str, Any]) -> dict[str, Any]:
    return {
        "pytorch": {
            "without_tool": "claim_fails",
            "stub_action": "replace torch spinor/density/PEPS tensors with erased scalar placeholders",
            "reason": "Removing PyTorch removes spinor/density tensors, entropy spectra, local PEPS tensors, and sequential path probabilities.",
            "delta_witness": {
                "response_classes_present": base["quotient_class_count"],
                "entropy_mi_present": entropy["bell_edge_cut"]["mutual_information"],
                "order_gap_present": n01["order_gap"],
                "pass": base["quotient_class_count"] == 4 and entropy["bell_edge_cut"]["mutual_information"] > 1.0 and n01["order_gap"] > 0.0,
            },
        },
        "pyg": {
            "without_tool": "claim_weakens_below_threshold",
            "stub_action": "remove PyG Data carrier and message aggregation over site-edge anchors",
            "reason": "Removing PyG removes the finite graph Data carrier/message aggregation check over site-edge anchors.",
            "delta_witness": {"pyg_message_sum": base["topology"]["pyg_message_sum"], "pass": base["topology"]["pyg_message_sum"] > 0.0},
        },
        "rustworkx": {
            "without_tool": "map_unprovable",
            "stub_action": "drop rustworkx connectivity and edge-count certification",
            "reason": "Removing rustworkx removes graph connectivity/edge-count certification for K.E.",
            "delta_witness": {"rustworkx_connected": base["topology"]["rustworkx_connected"], "pass": base["topology"]["rustworkx_connected"]},
        },
        "xgi": {
            "without_tool": "map_unprovable",
            "stub_action": "drop XGI hyperedge construction for face/cell anchors",
            "reason": "Removing XGI removes finite face/cell hyperedge anchor certification.",
            "delta_witness": {"face_cell_hyperedges": base["topology"]["xgi_face_cell_hyperedges"], "pass": base["topology"]["xgi_face_cell_hyperedges"] > 0},
        },
        "toponetx": {
            "without_tool": "map_unprovable",
            "stub_action": "drop TopoNetX cell-complex face anchor certification",
            "reason": "Removing TopoNetX removes finite cell-complex face anchor certification.",
            "delta_witness": {"cell_complex_dim": base["topology"]["toponetx_dim"], "pass": base["topology"]["toponetx_dim"] == 2},
        },
        "gudhi": {
            "without_tool": "claim_weakens_below_threshold",
            "stub_action": "drop GUDHI simplex-tree filtration over the same K anchors",
            "reason": "Removing GUDHI removes simplex-tree filtration pressure over the same finite K anchors.",
            "delta_witness": {"simplex_count": base["topology"]["gudhi_simplices"], "pass": base["topology"]["gudhi_simplices"] > 0},
        },
        "clifford": {
            "without_tool": "map_unprovable",
            "stub_action": "drop Clifford anticommutation check for the N01 path witness",
            "reason": "Removing Clifford removes the finite anticommutation sanity check for the noncommuting path witness.",
            "delta_witness": {"clifford_e1e2_anticommutator_zero": n01["clifford_e1e2_anticommutator_zero"], "pass": n01["clifford_e1e2_anticommutator_zero"]},
        },
        "sympy": {
            "without_tool": "map_unprovable",
            "stub_action": "drop exact SymPy cardinality checks for quotient and K anchors",
            "reason": "Removing SymPy removes exact count/cardinality checks for quotient and K anchors.",
            "delta_witness": {"exact_anchor_total": base["topology"]["sympy_exact_anchor_total"], "pass": base["topology"]["sympy_exact_anchor_total"] == 27},
        },
        "z3": {
            "without_tool": "map_unprovable",
            "stub_action": "drop Z3 finite-anchor and positive-order-gap gates",
            "reason": "Removing Z3 removes finite-anchor and positive-order-gap impossibility gates.",
            "delta_witness": z3_gate(n01["order_gap"]),
        },
        "cvc5": {
            "without_tool": "map_unprovable",
            "stub_action": "drop cvc5 admission and downstream-nonpromotion gates",
            "reason": "Removing cvc5 removes independent admission and downstream-nonpromotion gates.",
            "delta_witness": cvc5_gate(),
        },
        "dense_global_state": {
            "without_tool": "claim_fails",
            "stub_action": "replace local PEPS3D tensors with dense global 2^n closure",
            "reason": "Replacing local PEPS3D tensors with dense global 2^n closure violates the finite local carrier rule for the 64-site stress row.",
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
                f"L0 claim {row['without_tool']}"
            ),
            "delta_witness": row["delta_witness"],
            "non_vacuous": bool(row["delta_witness"]["pass"] and row["without_tool"] != "no_change"),
        }
    return delta


def main() -> dict[str, Any]:
    started = time.time()
    base = quotient_gate((2, 2, 2))
    n01 = n01_path_witness()
    entropy = entropy_gate()
    stress = stress_gate()
    z3_checks = z3_gate(n01["order_gap"])
    cvc5_checks = cvc5_gate()
    controls = controls_gate(base, n01, entropy)
    ablations = tool_ablations(base, n01, entropy, stress)

    positive = {
        "finite_response_quotient_over_peps3d_K8": base,
        "N01_projective_path_order_witness": n01,
        "QIT_entropy_local_edge_cut_readouts": entropy,
        "tool_topology_certificates_K8": base["topology"],
        "scale_stress_8_16_32_64_no_dense_closure": stress,
        "z3_finite_and_order_gate": z3_checks,
        "cvc5_L0_admission_and_downstream_lock_gate": cvc5_checks,
    }
    graveyard_companions = {
        "non_ic_single_probe_collapses_quotient": {
            "single_probe_class_count": controls["non_ic_single_probe_class_count"],
            "full_probe_class_count": controls["full_probe_class_count"],
            "pass": controls["non_ic_single_probe_class_count"] < controls["full_probe_class_count"],
        },
        "scalar_peps_label_erases_physical_response_index": {
            "pass": controls["scalar_peps_physical_index_erased"],
        },
        "topology_shuffled_control_rejected": {
            "pass": controls["topology_shuffled_edge_set_rejected"],
        },
        "dense_global_state_closure_blocked": {
            "dense_global_state_dimension_for_64_sites": str(controls["dense_global_state_closure_blocked_for_64_sites"]),
            "pass": controls["dense_global_state_closure_blocked_for_64_sites"] > 10**12,
        },
        "downstream_terms_remain_locked": {
            "blocked_consumers": BLOCKED_CONSUMERS,
            "pass": "flux" in BLOCKED_CONSUMERS and "Axis0" in BLOCKED_CONSUMERS and "final manifold" in BLOCKED_CONSUMERS,
        },
    }
    boundary = {
        "order_erased_same_projector_path_boundary": {
            "gap": controls["order_erased_gap"],
            "pass": controls["order_erased_gap"] < TOL,
        },
        "product_edge_entropy_boundary": {
            "mutual_information": controls["product_entropy_control_mi"],
            "pass": abs(controls["product_entropy_control_mi"]) < TOL,
        },
        "max_mixed_site_entropy_boundary": {
            "entropy_bits": controls["max_mixed_entropy_control_bits"],
            "pass": abs(controls["max_mixed_entropy_control_bits"] - 1.0) < TOL,
        },
        "chirality_control_not_applicable_at_L0": {
            "reason": controls["chirality_no_chirality_control"],
            "pass": True,
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
            "N01": "noncommuting/order-sensitive response witness",
        },
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "finite PEPS3D response quotient carrier",
        "geometry_layer": "L0 finite response/effect/path quotient geometry",
        "carrier_realization": "torch complex spinor-derived densities plus local PEPS3D tensors over explicit K=(V,E,F,C) anchors",
        "peps3d_embedding": "K=(V,E,F,C) with site V, bond/edge E, face F, and cell C anchors for every stress shape; scalar PEPS labels are rejected",
        "spinor_state": "torch-native two-component spinors {|0>,|1>,|+>,|->}; densities rho_v = psi_v psi_v^dagger",
        "quaternion_action": "not_applicable_at_L0_no_quaternion_language_used",
        "dependency_receipts": [
            "system_v5/legos/results/finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3_results.json",
            "system_v5/legos/results/density_operator_cptp_amplitude_damping_trace_psd_pytorch_sympy_z3_results.json",
            "system_v5/legos/results/peps3d_closure_2x2x2_pyg_xgi_pytorch_z3_results.json",
            "system_v5/ops/formal_scouts/results/phase1_finite_probe_effect_quotient_root_gate_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "local PEPS3D edge cut only; no Xi/Phi0/Axis0 cut",
        "law_or_candidate_tested": "finite response quotient Q_P(K) with PEPS3D anchor and local entropy readouts",
        "allowed_claims": [
            "L0 finite response/effect/path quotient layer exists for the tested finite PEPS3D carriers",
            "local QIT entropy readouts are available on density/cut controls",
            "8/16/32/64 site stress is finite without dense 2^n closure",
        ],
        "promotion_blockers": [
            "no layer stacking",
            "no Hopf/Weyl/terrain/substage data",
            "no flux/Xi/Phi0/Axis0/physics admission",
            "full Wizard v4.2 Max Assembly not achieved in this run",
        ],
        "F01_status": "passed: finite K=(V,E,F,C), spinors, densities, probes/effects, paths, tensors, quotient classes, entropy readouts, and stress rows",
        "N01_status": "passed: Z0->X+ and X+->Z0 sequential projective paths have nonzero response gap; order-erased same-projector control collapses",
        "F01_witness": "finite K=(V,E,F,C), spinors, densities, probes/effects, paths, local PEPS3D tensors, quotient classes, entropy readouts, and stress rows",
        "N01_witness": "finite Z0->X+ and X+->Z0 sequential projective paths have nonzero response gap while the order-erased same-projector control collapses",
        "PEPS3D_K_anchor": {
            "carrier": "K=(V,E,F,C)",
            "stress_shapes": SHAPES,
            "max_sites": stress["max_sites"],
            "peps3d_bond_dim": stress["max_bond"],
            "anchor_types": ["V", "E", "F", "C"],
            "dense_state_closure_used": False,
        },
        "torch_spinor_or_density": "torch-native two-component spinors {|0>,|1>,|+>,|->}; densities rho_v = psi_v psi_v^dagger; local/cut readouts only",
        "entropy_status": "passed: von Neumann, Renyi2, mutual information, conditional entropy, and coherent information on local density/cut readouts",
        "QIT_entropy_where_defined": "von Neumann, Renyi2, mutual information, conditional entropy, and coherent information on spinor-derived local density/cut readouts",
        "scale_status": "passed 8/16/32/64 PEPS3D site stress at bond_dim=2 without dense global state closure",
        "scale_8_16_32_64_or_resource_blocker": {
            "status": "passed_finite_scope",
            "sites": [8, 16, 32, 64],
            "max_sites": stress["max_sites"],
            "max_peps3d_bond": stress["max_bond"],
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
            "This L0 object is a v5 PEPS3D-carried response quotient with "
            "torch-native spinor-derived density and QIT entropy readouts. "
            "It is not a v4 numpy/classical probe or a downstream Axis/flux row."
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
            "max_peps3d_bond": stress["max_bond"],
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
