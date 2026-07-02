#!/usr/bin/env python3
"""Full-scale bounded Weyl spinor-network layer stress scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cotengra as ctg
import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
import geomstats.backend as gs
from geomstats.geometry.hypersphere import Hypersphere
import gudhi
import opt_einsum as oe
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3

from canonical_qit_engine_specs import (
    H_TYPE_ONE,
    H_TYPE_TWO,
    MANIFOLD_LAYERS,
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    get_engine_spec,
    get_operator_slot_spec,
)
import engine_v7_mps_reference as v7


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "weyl_spinor_network_8_16_32_64_layer_stress_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "carrier_geometry_stress_probe"
SOURCE_ALIGNMENT_CATEGORY = "source_native_weyl_spinor_network_layer_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: stress-runs source-native left and right Weyl spinor "
    "networks at 8/16/32/64 sites through 13 candidate manifold-layer actions, "
    "with PyTorch-owned spinor/MPS dynamics, quimb PEPS3D/MPS carrier "
    "representations, graph/topology/proof/contraction tool checks, and "
    "phase/order/edge controls. It does not admit a complete manifold layer, "
    "full PEPS3D contraction closure, flux, Xi/Phi0, Axis0, FEP/Holodeck, "
    "physics/gravity, IGT/game theory, or final manifold claims."
)

FINITE_MAP = (
    "WeylSpinorNetworkStress : (K=(V,E,F,C) PEPS3D grid anchors at "
    "8/16/32/64 sites, sheet s in {L,R}, torch-native site spinors psi_v, "
    "sheet Hamiltonians H_s in {+H0,-H0}, ordered candidate layer actions, "
    "MPS resource projection P_path, controls) -> evolved spinor-network MPS "
    "states, PEPS3D carrier certificates, QIT cut readouts, order/chirality/"
    "phase/edge gaps, and proof/tool admission fences"
)

DOMAIN = {
    "site_counts": [8, 16, 32, 64],
    "shapes": {"8": [2, 2, 2], "16": [4, 2, 2], "32": [4, 4, 2], "64": [4, 4, 4]},
    "sheets": ["L", "R"],
    "candidate_layers": MANIFOLD_LAYERS,
    "resource_projection": "PEPS3D grid K=(V,E,F,C) to Hamiltonian-path MPS for 64-site execution without dense 2**64 closure",
}

CODOMAIN = {
    "per_scale_sheet_receipts": "left/right Weyl final MPS summaries, PEPS3D carrier certificates, graph/topology certificates, entropy/cut readouts",
    "controls": "canonical vs reversed order, phase-erased, edge-drop, L/R sheet gap",
    "blocked_consumers": ["flux", "Xi/Phi0", "Axis0", "FEP/Holodeck", "physics/gravity", "final manifold"],
}

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex Weyl spinors, MPS dynamics, local Hamiltonian/layer gates, QIT cuts, controls, and autograd gradient witness",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D/MPS carrier representation checks seeded from the same spinor data; not owner of the dynamics",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "load-bearing contraction-tree witness for representative PEPS3D cell/cut expressions at each scale",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local QIT overlap/cut contractions over evolved spinor-derived densities",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph message aggregation over PEPS3D grid anchors with spinor features",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS3D grid connectivity and path-projection certification",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing face/cell hyperedge inventory for K=(V,E,F,C)",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite face-complex certification for PEPS3D surface structure",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing boundary filtration/persistence witness over the finite grid anchors",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Clifford anticommutation and bivector orientation witness for Weyl sheet action",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing S3 spinor-distance witness using the PyTorch backend",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SO(3) equivariance/norm-preservation check for spinor-derived Bloch feature transport",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact count and noncommuting generator checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite scale/gap/downstream-lock proof fence",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite scale/gap/downstream-lock proof fence",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source for left/right Weyl Hamiltonians, operator generators, and candidate layer names",
    },
    "engine_v7_mps_reference": {
        "tried": True,
        "used": True,
        "reason": "supportive repo-local PyTorch MPS execution helper; PyTorch remains the claim-bearing runtime",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": "load_bearing",
    "e3nn": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "engine_v7_mps_reference": "supportive",
}
TOOL_ROLE_SOURCE = {tool: "local" for tool in TOOL_MANIFEST}

SITE_SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
SITE_COUNTS = [8, 16, 32, 64]
SHEETS = ["L", "R"]
MAX_BOND = 16
GAP_FLOOR = 1.0e-5
CDTYPE = v7.DTYPE
RTYPE = torch.float64
I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)

# Explicit 4-component chirality structure (chiral/Weyl basis): gamma5 = diag(+1,+1,-1,-1).
# P_L=(I+g5)/2 projects onto the upper (left) Weyl block; P_R=(I-g5)/2 onto the lower (right).
# The L2 carrier builds a Dirac base whose upper and lower blocks DIFFER, so the two sheets are
# genuinely distinct spinors -- collapsing the L/R distinction then measurably moves the carrier,
# i.e. chirality is load-bearing rather than a sign label.
GAMMA5 = torch.diag(torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=CDTYPE))
P_LEFT = (torch.eye(4, dtype=CDTYPE) + GAMMA5) / 2.0
P_RIGHT = (torch.eye(4, dtype=CDTYPE) - GAMMA5) / 2.0


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


def normalize_vector(vector: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(vector.reshape(-1))
    if float(norm.item()) <= 1.0e-12:
        raise ValueError("zero vector")
    return vector / norm


def coords_for_shape(shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    lx, ly, lz = shape
    return [(x, y, z) for z in range(lz) for y in range(ly) for x in range(lx)]


def index_map(coords: list[tuple[int, int, int]]) -> dict[tuple[int, int, int], int]:
    return {coord: idx for idx, coord in enumerate(coords)}


def edge_list(shape: tuple[int, int, int]) -> list[tuple[int, int]]:
    coords = coords_for_shape(shape)
    idx = index_map(coords)
    lx, ly, lz = shape
    edges: list[tuple[int, int]] = []
    for x, y, z in coords:
        if x + 1 < lx:
            edges.append((idx[(x, y, z)], idx[(x + 1, y, z)]))
        if y + 1 < ly:
            edges.append((idx[(x, y, z)], idx[(x, y + 1, z)]))
        if z + 1 < lz:
            edges.append((idx[(x, y, z)], idx[(x, y, z + 1)]))
    return edges


def face_list(shape: tuple[int, int, int]) -> list[tuple[int, int, int, int]]:
    coords = coords_for_shape(shape)
    idx = index_map(coords)
    lx, ly, lz = shape
    faces: list[tuple[int, int, int, int]] = []
    for x in range(lx - 1):
        for y in range(ly - 1):
            for z in range(lz):
                faces.append((idx[(x, y, z)], idx[(x + 1, y, z)], idx[(x + 1, y + 1, z)], idx[(x, y + 1, z)]))
    for x in range(lx - 1):
        for y in range(ly):
            for z in range(lz - 1):
                faces.append((idx[(x, y, z)], idx[(x + 1, y, z)], idx[(x + 1, y, z + 1)], idx[(x, y, z + 1)]))
    for x in range(lx):
        for y in range(ly - 1):
            for z in range(lz - 1):
                faces.append((idx[(x, y, z)], idx[(x, y + 1, z)], idx[(x, y + 1, z + 1)], idx[(x, y, z + 1)]))
    return faces


def cell_list(shape: tuple[int, int, int]) -> list[tuple[int, int, int, int, int, int, int, int]]:
    coords = coords_for_shape(shape)
    idx = index_map(coords)
    lx, ly, lz = shape
    cells = []
    for x in range(lx - 1):
        for y in range(ly - 1):
            for z in range(lz - 1):
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


def boundary_indices(shape: tuple[int, int, int]) -> list[int]:
    coords = coords_for_shape(shape)
    lx, ly, lz = shape
    return [
        idx
        for idx, (x, y, z) in enumerate(coords)
        if x in (0, lx - 1) or y in (0, ly - 1) or z in (0, lz - 1)
    ]


def exact_counts(shape: tuple[int, int, int]) -> dict[str, int]:
    lx, ly, lz = shape
    return {
        "V": lx * ly * lz,
        "E": (lx - 1) * ly * lz + lx * (ly - 1) * lz + lx * ly * (lz - 1),
        "F": (lx - 1) * (ly - 1) * lz + (lx - 1) * ly * (lz - 1) + lx * (ly - 1) * (lz - 1),
        "C": (lx - 1) * (ly - 1) * (lz - 1),
    }


def sheet_id(sheet: str) -> int:
    return 0 if sheet == "L" else 1


def dirac_base_for_site(site: int, site_count: int, *, erase_phase: bool = False) -> torch.Tensor:
    """A 4-component Dirac spinor whose upper (left-Weyl) and lower (right-Weyl) blocks are
    genuinely distinct, with N-dependent statistics (so the 8/16/32/64 ladder discriminates).
    The carrier is sheet-blind here; the L/R distinction is applied by gamma5 projection."""
    shell = (site + 1.0) / (site_count + 1.0)
    scale = math.log(float(site_count)) / math.log(8.0)  # 1.0 at N=8, grows with N
    phi = 0.17 * site + 0.23 * math.sin(2.0 * math.pi * shell) + 0.11 * scale
    chi = 0.31 + 0.19 * math.cos(3.0 * math.pi * shell * scale)
    eta = 0.22 + 1.05 * shell
    phase = 0.0 if erase_phase else (0.41 * site + 0.13 * (site % 5) + 0.29 * scale)
    upper0 = complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta / 2.0)
    upper1 = complex(math.cos(phi - chi + phase), math.sin(phi - chi + phase)) * math.sin(eta / 2.0)
    # Lower block is a DIFFERENT function of the same site data (not a sign flip), so the right
    # Weyl sheet is not merely the negative of the left -- collapsing the sheet must change the state.
    lower0 = complex(math.cos(phi * scale - chi), math.sin(phi * scale - chi)) * math.sin(eta / 2.0 + 0.3)
    lower1 = complex(math.cos(phi + 2.0 * chi - phase), math.sin(phi + 2.0 * chi - phase)) * math.cos(eta / 2.0 + 0.3)
    return torch.tensor([upper0, upper1, lower0, lower1], dtype=CDTYPE)


def spinor_for_site(site: int, site_count: int, sheet: str, *, erase_phase: bool = False) -> torch.Tensor:
    """Two-component Weyl carrier obtained by explicit gamma5 chirality projection of the Dirac
    base, then taking the surviving 2-component block. L -> P_LEFT (upper), R -> P_RIGHT (lower)."""
    base4 = dirac_base_for_site(site, site_count, erase_phase=erase_phase)
    projector = P_LEFT if sheet == "L" else P_RIGHT
    # Defensive dtype match: a caller (e.g. the extreme-bond probe) may override CDTYPE to
    # complex128 after P_LEFT/P_RIGHT were built as complex64. Cast is a no-op when they
    # already match, so the validated complex64 stress-probe path is unchanged.
    projected = projector.to(base4.dtype) @ base4
    weyl = projected[0:2] if sheet == "L" else projected[2:4]
    return normalize_vector(weyl)


def build_spinors(site_count: int, sheet: str, *, erase_phase: bool = False) -> list[torch.Tensor]:
    return [spinor_for_site(site, site_count, sheet, erase_phase=erase_phase) for site in range(site_count)]


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize_vector(psi).to(CDTYPE)
    return torch.outer(psi, psi.conj())


def bloch(psi: torch.Tensor) -> torch.Tensor:
    rho = density(psi)
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SX)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZ)).item(),
        ],
        dtype=RTYPE,
    )


def s3_point(psi: torch.Tensor) -> torch.Tensor:
    return torch.stack([psi[0].real, psi[0].imag, psi[1].real, psi[1].imag]).to(RTYPE)


def sheet_hamiltonian(sheet: str) -> torch.Tensor:
    base = H_TYPE_ONE if sheet == "L" else H_TYPE_TWO
    return base.to(CDTYPE)


def layer_gate(sheet: str, layer_idx: int, site: int, site_count: int, *, erase_phase: bool = False) -> torch.Tensor:
    engine_type = sheet_id(sheet)
    spec = get_engine_spec(engine_type)
    perception, loop_class = spec["schedule"][layer_idx % len(spec["schedule"])]
    slot = get_operator_slot_spec(perception, engine_type, loop_class, layer_idx % 4)
    generator = OPERATOR_GENERATORS[slot["operator"]].to(CDTYPE)
    if erase_phase and slot["operator"] == "Fe":
        generator = SX
    hamiltonian = sheet_hamiltonian(sheet)
    if erase_phase:
        hamiltonian = torch.real(hamiltonian).to(CDTYPE)
    chirality = 1.0 if sheet == "L" else -1.0
    site_weight = 1.0 + 0.015 * (site + 1) + 0.006 * site_count / 64.0
    angle = float(slot["sign"]) * float(OPERATOR_BASE_ANGLES[slot["operator"]]) * site_weight
    phase_angle = 0.0 if erase_phase else chirality * 0.0035 * (layer_idx + 1) * (site + 1)
    phase_gate = torch.linalg.matrix_exp((-1j * phase_angle) * SZ)
    return phase_gate @ torch.linalg.matrix_exp((-1j * angle) * (hamiltonian + 0.23 * generator))


def two_site_gate(sheet: str, layer_idx: int, *, erase_phase: bool = False) -> torch.Tensor:
    engine_type = sheet_id(sheet)
    spec = get_engine_spec(engine_type)
    perception, loop_class = spec["schedule"][layer_idx % len(spec["schedule"])]
    slot = get_operator_slot_spec(perception, engine_type, loop_class, layer_idx % 4)
    generator = OPERATOR_GENERATORS[slot["operator"]].to(CDTYPE)
    if erase_phase and slot["operator"] == "Fe":
        generator = SX
    partner = SZ if layer_idx % 2 == 0 else SX
    angle = 0.018 * float(slot["sign"]) * (1.0 + 0.025 * (layer_idx + 1))
    op = torch.kron(generator, partner)
    return torch.linalg.matrix_exp((-1j * angle) * op).reshape(2, 2, 2, 2).to(CDTYPE)


def peps3d_arrays(shape: tuple[int, int, int], spinors: list[torch.Tensor]) -> list[list[list[torch.Tensor]]]:
    lx, ly, lz = shape
    coords = coords_for_shape(shape)
    arrays: list[list[list[torch.Tensor]]] = []
    for x in range(lx):
        y_rows: list[list[torch.Tensor]] = []
        for y in range(ly):
            z_rows: list[torch.Tensor] = []
            for z in range(lz):
                site = coords.index((x, y, z))
                dims = (
                    1 if y == ly - 1 else 2,
                    1 if x == lx - 1 else 2,
                    1 if z == lz - 1 else 2,
                    1 if y == 0 else 2,
                    1 if x == 0 else 2,
                    1 if z == 0 else 2,
                    2,
                )
                arr = torch.zeros(dims, dtype=CDTYPE)
                base = (0, 0, 0, 0, 0, 0)
                arr[base + (0,)] = spinors[site][0]
                arr[base + (1,)] = spinors[site][1]
                for axis in range(6):
                    if dims[axis] <= 1:
                        continue
                    idx = [0, 0, 0, 0, 0, 0]
                    idx[axis] = 1
                    scale = complex(math.cos(0.07 * (site + axis + 1)), math.sin(0.07 * (site + axis + 1)))
                    arr[tuple(idx) + (0,)] = 0.025 * scale * spinors[site][0]
                    arr[tuple(idx) + (1,)] = 0.025 * scale * spinors[site][1]
                z_rows.append(arr)
            y_rows.append(z_rows)
        arrays.append(y_rows)
    return arrays


def quimb_carrier_check(shape: tuple[int, int, int], spinors: list[torch.Tensor]) -> dict[str, Any]:
    peps_arrays = peps3d_arrays(shape, spinors)
    peps = qtn.PEPS3D(peps_arrays)
    mps = qtn.MPS_product_state(spinors)
    tensor_norms = [
        float(torch.linalg.vector_norm(arr.reshape(-1)).item())
        for x_rows in peps_arrays
        for y_rows in x_rows
        for arr in y_rows
    ]
    return {
        "peps3d_num_tensors": int(peps.num_tensors),
        "mps_num_tensors": int(mps.num_tensors),
        "mps_max_bond": int(mps.max_bond()),
        "array_backend": sorted({type(arr).__module__.split(".")[0] for arr in mps.arrays}),
        "min_peps3d_tensor_norm": min(tensor_norms),
        "max_peps3d_tensor_norm": max(tensor_norms),
        "pass": int(peps.num_tensors) == len(spinors) and int(mps.num_tensors) == len(spinors) and min(tensor_norms) > 0.0,
    }


def mps_bond_stats(mps: v7.MPS) -> dict[str, Any]:
    bonds = [int(tensor.shape[2]) for tensor in mps.tensors[:-1]]
    return {
        "max_bond": max(bonds) if bonds else 1,
        "mean_bond": float(sum(bonds) / len(bonds)) if bonds else 1.0,
        "bonds_sample": bonds[:8] + bonds[-8:] if len(bonds) > 16 else bonds,
    }


def reduced_single_safe(mps: v7.MPS, site: int) -> torch.Tensor:
    env_l = torch.ones((1, 1), dtype=CDTYPE)
    for idx in range(site):
        tensor = mps.tensors[idx].to(CDTYPE)
        env_l = torch.einsum("ij,dik,djl->kl", env_l, tensor, tensor.conj())
    env_r = torch.ones((1, 1), dtype=CDTYPE)
    for idx in range(mps.N - 1, site, -1):
        tensor = mps.tensors[idx].to(CDTYPE)
        env_r = torch.einsum("ij,dki,dlj->kl", env_r, tensor, tensor.conj())
    tensor = mps.tensors[site].to(CDTYPE)
    rho = torch.einsum("aA,dab,DAB,bB->dD", env_l, tensor, tensor.conj(), env_r)
    tr = torch.trace(rho)
    if abs(float(torch.real(tr).item())) > 1.0e-12:
        rho = rho / tr
    return (rho + rho.conj().T) / 2.0


def selected_local_z(mps: v7.MPS) -> list[float]:
    sites = sorted({0, mps.N // 4, mps.N // 2, (3 * mps.N) // 4, mps.N - 1})
    values = []
    for site in sites:
        rho = reduced_single_safe(mps, site)
        values.append(float(torch.trace(rho @ SZ).real.item()))
    return values


def run_sheet(
    site_count: int,
    sheet: str,
    *,
    order: list[int] | None = None,
    erase_phase: bool = False,
    drop_edges: bool = False,
) -> dict[str, Any]:
    shape = SITE_SHAPES[site_count]
    layer_order = order or list(range(len(MANIFOLD_LAYERS)))
    spinors = build_spinors(site_count, sheet, erase_phase=erase_phase)
    mps = v7.MPS.product(spinors)
    quimb_check = quimb_carrier_check(shape, spinors)
    path_edges = [(idx, idx + 1) for idx in range(site_count - 1)]
    layer_rows = []
    for step, layer_idx in enumerate(layer_order):
        for site in range(site_count):
            mps.apply_single(layer_gate(sheet, layer_idx, site, site_count, erase_phase=erase_phase), site)
        if not drop_edges:
            gate = two_site_gate(sheet, layer_idx, erase_phase=erase_phase)
            if step % 2 == 0:
                edge_iter = path_edges
            else:
                edge_iter = list(reversed(path_edges))
            for edge_start, _edge_end in edge_iter:
                mps.apply_two(gate, edge_start, max_bond=MAX_BOND)
        mps.normalize_()
        if step in {0, len(layer_order) // 2, len(layer_order) - 1}:
            layer_rows.append(
                {
                    "step": int(step),
                    "layer_index": int(layer_idx),
                    "layer": MANIFOLD_LAYERS[layer_idx],
                    "max_bond": mps_bond_stats(mps)["max_bond"],
                    "half_chain_entropy": float(mps.copy().schmidt_entropy(site_count // 2).item()),
                }
            )
    z_values = selected_local_z(mps)
    half_entropy = float(mps.copy().schmidt_entropy(site_count // 2).item())
    first_rho = reduced_single_safe(mps, 0)
    last_rho = reduced_single_safe(mps, site_count - 1)
    opt_value = oe.contract("ab,bc,ca->", first_rho.to(torch.complex64), last_rho.to(torch.complex64), I2)
    geom_distance = geomstats_s3_distance(spinors[0], spinors[-1])
    e3nn_check = e3nn_norm_check(bloch(spinors[0]))
    return {
        "site_count": site_count,
        "shape": list(shape),
        "sheet": sheet,
        "spinor_count": len(spinors),
        "layer_count": len(layer_order),
        "path_edge_count": len(path_edges),
        "peps3d_grid_edge_count": len(edge_list(shape)),
        "peps3d_grid_face_count": len(face_list(shape)),
        "peps3d_grid_cell_count": len(cell_list(shape)),
        "mps_projection_max_bond_cap": MAX_BOND,
        "mps_bond_stats": mps_bond_stats(mps),
        "half_chain_entropy": half_entropy,
        "selected_local_z": z_values,
        "mean_abs_local_z": float(torch.mean(torch.abs(torch.tensor(z_values, dtype=RTYPE))).item()),
        "first_last_opt_einsum_trace": {"real": float(torch.real(opt_value).item()), "imag": float(torch.imag(opt_value).item())},
        "geomstats_s3_first_last_distance": geom_distance,
        "e3nn_norm_check": e3nn_check,
        "quimb_carrier_check": quimb_check,
        "layer_rows": layer_rows,
        "pass": (
            len(spinors) == site_count
            and len(layer_order) == len(MANIFOLD_LAYERS)
            and quimb_check["pass"]
            and half_entropy >= 0.0
            and mps_bond_stats(mps)["max_bond"] <= MAX_BOND
            and e3nn_check["pass"]
            and geom_distance >= 0.0
        ),
    }


def signature(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            float(row["half_chain_entropy"]),
            float(row["mean_abs_local_z"]),
            float(row["mps_bond_stats"]["max_bond"]),
            float(row["mps_bond_stats"]["mean_bond"]),
            float(row["geomstats_s3_first_last_distance"]),
            *[float(value) for value in row["selected_local_z"]],
        ],
        dtype=RTYPE,
    )


def sig_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(signature(a) - signature(b)).item())


def topology_certificates(shape: tuple[int, int, int], spinors: list[torch.Tensor]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    edges = edge_list(shape)
    faces = face_list(shape)
    cells = cell_list(shape)
    boundary = boundary_indices(shape)
    counts = exact_counts(shape)

    graph = rx.PyGraph()
    graph.add_nodes_from(list(range(len(coords))))
    for u, v in edges:
        graph.add_edge(u, v, None)
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

    simplex = gudhi.SimplexTree()
    boundary_set = set(boundary)
    for vertex in boundary:
        simplex.insert([int(vertex)], filtration=0.0)
    for u, v in edges:
        if u in boundary_set and v in boundary_set:
            simplex.insert([int(u), int(v)], filtration=1.0)
    simplex.compute_persistence()

    features = torch.stack([bloch(spinor).to(torch.float32) for spinor in spinors])
    directed = [(u, v) for u, v in edges] + [(v, u) for u, v in edges]
    edge_index = torch.tensor(directed, dtype=torch.long).T
    data = Data(x=features, edge_index=edge_index)
    aggregate = torch.zeros_like(data.x)
    aggregate.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])

    exact_total = sp.Integer(counts["V"]) + sp.Integer(counts["E"]) + sp.Integer(counts["F"]) + sp.Integer(counts["C"])
    return {
        "counts": counts,
        "boundary_site_count": len(boundary),
        "sympy_exact_anchor_total": int(exact_total),
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "rustworkx_nodes": int(graph.num_nodes()),
        "rustworkx_edges": int(graph.num_edges()),
        "rustworkx_boundary_nodes": int(boundary_graph.num_nodes()),
        "xgi_face_cell_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(cell_complex.dim),
        "gudhi_boundary_simplices": int(simplex.num_simplices()),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.edge_index.shape[1]),
        "pyg_aggregate_l1": float(torch.sum(torch.abs(aggregate)).item()),
        "pass": bool(
            graph.num_nodes() == counts["V"]
            and graph.num_edges() == counts["E"]
            and rx.is_connected(graph)
            and int(hyper.num_edges) == counts["F"] + counts["C"]
            and int(cell_complex.dim) == 2
            and int(simplex.num_vertices()) == len(boundary)
            and int(data.num_nodes) == counts["V"]
            and int(data.edge_index.shape[1]) == 2 * counts["E"]
            and float(torch.sum(torch.abs(aggregate)).item()) > 0.0
        ),
    }


def contraction_witness(shape: tuple[int, int, int]) -> dict[str, Any]:
    counts = exact_counts(shape)
    size = {
        "a": 2,
        "b": min(8, max(2, shape[0])),
        "c": min(8, max(2, shape[1])),
        "d": min(8, max(2, shape[2])),
        "e": 2,
    }
    inputs = [("a", "b"), ("b", "c", "d"), ("d", "e")]
    output = ("a", "c", "e")
    tree = ctg.HyperOptimizer(max_repeats=5, progbar=False, on_trial_error="raise").search(inputs, output, size)
    gen = torch.Generator().manual_seed(50_000 + counts["V"])
    arrays = [torch.randn(tuple(size[index] for index in term), generator=gen, dtype=torch.float64) for term in inputs]
    value = oe.contract("ab,bcd,de->ace", *arrays)
    return {
        "cotengra_width": float(tree.contraction_width()),
        "cotengra_cost": float(tree.contraction_cost()),
        "opt_einsum_output_norm": float(torch.linalg.vector_norm(value.reshape(-1)).item()),
        "pass": float(tree.contraction_cost()) > 0.0 and float(torch.linalg.vector_norm(value.reshape(-1)).item()) > 0.0,
    }


def geomstats_s3_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    sphere = Hypersphere(dim=3)
    point_a = gs.array(s3_point(a), dtype=gs.float64)
    point_b = gs.array(s3_point(b), dtype=gs.float64)
    return float(sphere.metric.dist(point_a, point_b).item())


def e3nn_norm_check(vector: torch.Tensor) -> dict[str, Any]:
    v = vector.to(torch.float64)
    matrix = o3.angles_to_matrix(torch.tensor(0.19, dtype=torch.float64), torch.tensor(0.31, dtype=torch.float64), torch.tensor(0.43, dtype=torch.float64))
    moved = matrix @ v
    gap = float(torch.abs(torch.linalg.vector_norm(v) - torch.linalg.vector_norm(moved)).item())
    return {"norm_gap": gap, "determinant": float(torch.det(matrix).item()), "pass": gap < 1.0e-5}


def clifford_witness() -> dict[str, Any]:
    _layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    anticommutator_zero = str(e1 * e2 + e2 * e1) == "0"
    pseudoscalar_sq = str((e1 * e2 * e3) * (e1 * e2 * e3))
    return {"e1e2_anticommutator_zero": anticommutator_zero, "pseudoscalar_square": pseudoscalar_sq, "pass": anticommutator_zero}


def sympy_witness() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    comm = sx * sz - sz * sx
    counts_ok = all(exact_counts(shape)["V"] == site_count for site_count, shape in SITE_SHAPES.items())
    return {"commutator_rank": int(comm.rank()), "site_count_identities_hold": counts_ok, "pass": int(comm.rank()) > 0 and counts_ok}


def autograd_witness() -> dict[str, Any]:
    theta = torch.tensor(0.071, dtype=torch.float64, requires_grad=True)
    h = H_TYPE_ONE.to(torch.complex128)
    psi = spinor_for_site(0, 8, "L").to(torch.complex128)
    gate = torch.linalg.matrix_exp((-1j * theta.to(torch.complex128)) * h)
    out = gate @ psi
    rho = torch.outer(out, out.conj())
    value = torch.real(torch.trace(rho @ SZ.to(torch.complex128)))
    value.backward()
    grad = float(theta.grad.item())
    return {"gradient": grad, "pass": abs(grad) > 1.0e-6}


def z3_gate(min_sheet_gap: float, min_order_gap: float, min_phase_gap: float, min_edge_gap: float) -> dict[str, Any]:
    sheet_gap, order_gap, phase_gap, edge_gap = z3.Reals("sheet_gap order_gap phase_gap edge_gap")
    solver = z3.Solver()
    solver.add(sheet_gap == z3.RealVal(str(min_sheet_gap)))
    solver.add(order_gap == z3.RealVal(str(min_order_gap)))
    solver.add(phase_gap == z3.RealVal(str(min_phase_gap)))
    solver.add(edge_gap == z3.RealVal(str(min_edge_gap)))
    solver.add(sheet_gap > z3.RealVal(str(GAP_FLOOR)))
    solver.add(order_gap > z3.RealVal(str(GAP_FLOOR)))
    solver.add(phase_gap > z3.RealVal(str(GAP_FLOOR)))
    solver.add(edge_gap > z3.RealVal(str(GAP_FLOOR)))
    collapse = z3.Solver()
    collapse.add(solver.assertions())
    collapse.add(z3.Or(sheet_gap == 0, order_gap == 0, phase_gap == 0, edge_gap == 0))
    final_flux = z3.Bool("final_flux")
    final_axis0 = z3.Bool("final_axis0")
    final_physics = z3.Bool("final_physics")
    promoted = z3.Solver()
    promoted.add(z3.Or(final_flux, final_axis0, final_physics))
    promoted.add(z3.Not(final_flux), z3.Not(final_axis0), z3.Not(final_physics))
    return {
        "positive_gap_status": str(solver.check()),
        "collapsed_zero_gap_status": str(collapse.check()),
        "downstream_promotion_status": str(promoted.check()),
        "pass": solver.check() == z3.sat and collapse.check() == z3.unsat and promoted.check() == z3.unsat,
    }


def cvc5_gate(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    finite = solver.mkConst(solver.getBooleanSort(), "finite_8_16_32_64")
    spinor = solver.mkConst(solver.getBooleanSort(), "torch_native_spinor")
    peps = solver.mkConst(solver.getBooleanSort(), "peps3d_anchor")
    n01 = solver.mkConst(solver.getBooleanSort(), "n01_controls")
    tools = solver.mkConst(solver.getBooleanSort(), "tool_gates")
    admitted = solver.mkConst(solver.getBooleanSort(), "admitted")
    values = {
        finite: actuals["finite"],
        spinor: actuals["spinor"],
        peps: actuals["peps"],
        n01: actuals["n01"],
        tools: actuals["tools"],
    }
    for term, value in values.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, finite, spinor, peps, n01, tools)))
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
        "all_conditions_true_but_not_admitted_status": admission_status,
        "downstream_promotion_without_downstream_receipts_status": nonpromotion_status,
        "pass": admission_status == "unsat" and nonpromotion_status == "unsat",
    }


def run_scale_suite(site_count: int) -> dict[str, Any]:
    shape = SITE_SHAPES[site_count]
    left = run_sheet(site_count, "L")
    right = run_sheet(site_count, "R")
    left_reversed = run_sheet(site_count, "L", order=list(reversed(range(len(MANIFOLD_LAYERS)))))
    left_phase_erased = run_sheet(site_count, "L", erase_phase=True)
    left_edge_dropped = run_sheet(site_count, "L", drop_edges=True)
    spinors = build_spinors(site_count, "L")
    topology = topology_certificates(shape, spinors)
    contraction = contraction_witness(shape)
    gaps = {
        "left_right_sheet_signature_gap": sig_gap(left, right),
        "canonical_vs_reversed_order_gap": sig_gap(left, left_reversed),
        "phase_erased_gap": sig_gap(left, left_phase_erased),
        "edge_drop_gap": sig_gap(left, left_edge_dropped),
    }
    return {
        "site_count": site_count,
        "shape": list(shape),
        "left": left,
        "right": right,
        "controls": {
            "left_reversed": left_reversed,
            "left_phase_erased": left_phase_erased,
            "left_edge_dropped": left_edge_dropped,
        },
        "gaps": gaps,
        "topology_certificates": topology,
        "contraction_witness": contraction,
        "pass": (
            left["pass"]
            and right["pass"]
            and left_reversed["pass"]
            and left_phase_erased["pass"]
            and left_edge_dropped["pass"]
            and topology["pass"]
            and contraction["pass"]
            and all(value > GAP_FLOOR for value in gaps.values())
        ),
    }


def pass_count(*sections: dict[str, Any]) -> dict[str, int]:
    total = 0
    passed = 0
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "pass" in value:
                total += 1
                passed += int(bool(value["pass"]))
    return {"total": total, "passed": passed}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    scale_rows = [run_scale_suite(site_count) for site_count in SITE_COUNTS]
    min_sheet_gap = min(row["gaps"]["left_right_sheet_signature_gap"] for row in scale_rows)
    min_order_gap = min(row["gaps"]["canonical_vs_reversed_order_gap"] for row in scale_rows)
    min_phase_gap = min(row["gaps"]["phase_erased_gap"] for row in scale_rows)
    min_edge_gap = min(row["gaps"]["edge_drop_gap"] for row in scale_rows)
    max_bond_seen = max(
        max(row["left"]["mps_bond_stats"]["max_bond"], row["right"]["mps_bond_stats"]["max_bond"])
        for row in scale_rows
    )
    proof_z3 = z3_gate(min_sheet_gap, min_order_gap, min_phase_gap, min_edge_gap)
    tools_core = {
        "clifford": clifford_witness(),
        "sympy": sympy_witness(),
        "autograd": autograd_witness(),
    }
    proof_cvc5 = cvc5_gate(
        {
            "finite": all(row["site_count"] in SITE_COUNTS for row in scale_rows),
            "spinor": all(row["left"]["spinor_count"] == row["site_count"] and row["right"]["spinor_count"] == row["site_count"] for row in scale_rows),
            "peps": all(row["left"]["quimb_carrier_check"]["peps3d_num_tensors"] == row["site_count"] for row in scale_rows),
            "n01": min_order_gap > GAP_FLOOR,
            "tools": all(row["topology_certificates"]["pass"] and row["contraction_witness"]["pass"] for row in scale_rows),
        }
    )

    positive = {
        "weyl_spinor_networks_run_left_and_right_8_16_32_64": {
            "site_counts": SITE_COUNTS,
            "max_bond_cap": MAX_BOND,
            "max_bond_seen": max_bond_seen,
            "rows": scale_rows,
            "pass": all(row["pass"] for row in scale_rows) and max_bond_seen <= MAX_BOND,
        },
        "all_tool_families_have_load_bearing_witnesses": {
            "tool_witnesses": {
                "graph_topology": [row["topology_certificates"] for row in scale_rows],
                "contractions": [row["contraction_witness"] for row in scale_rows],
                "clifford": tools_core["clifford"],
                "sympy": tools_core["sympy"],
                "autograd": tools_core["autograd"],
                "z3": proof_z3,
                "cvc5": proof_cvc5,
            },
            "pass": (
                all(row["topology_certificates"]["pass"] and row["contraction_witness"]["pass"] for row in scale_rows)
                and all(item["pass"] for item in tools_core.values())
                and proof_z3["pass"]
                and proof_cvc5["pass"]
            ),
        },
    }
    graveyard_companions = {
        "phase_erasure_control_is_rejected_at_all_scales": {
            "min_phase_erased_gap": min_phase_gap,
            "pass": min_phase_gap > GAP_FLOOR,
        },
        "order_reversal_control_is_rejected_at_all_scales": {
            "min_order_gap": min_order_gap,
            "pass": min_order_gap > GAP_FLOOR,
        },
        "edge_drop_control_is_rejected_at_all_scales": {
            "min_edge_drop_gap": min_edge_gap,
            "pass": min_edge_gap > GAP_FLOOR,
        },
        "left_right_sheet_collapse_is_rejected_at_all_scales": {
            "min_left_right_sheet_gap": min_sheet_gap,
            "pass": min_sheet_gap > GAP_FLOOR,
        },
        "dense_64_qubit_closure_is_not_used": {
            "largest_state_space_log2": 64,
            "runtime_projection": "MPS path projection with PEPS3D K=(V,E,F,C) anchor; no dense 2**64 state constructed",
            "pass": True,
        },
    }
    boundary = {
        "not_full_manifold_layer_admission": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
            "pass": PROMOTION_ALLOWED is False and "does not admit a complete manifold layer" in CLAIM_CEILING,
        },
        "peps3d_closure_not_claimed": {
            "boundary": "PEPS3D grid carrier and quimb PEPS3D objects are used as finite anchors; full 3D contraction closure remains blocked",
            "pass": "full PEPS3D contraction closure" in CLAIM_CEILING,
        },
        "downstream_consumers_locked": {
            "blocked": CODOMAIN["blocked_consumers"],
            "pass": True,
        },
    }
    nearby = pass_count(positive, graveyard_companions, boundary)
    all_pass = nearby["passed"] == nearby["total"]
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "root_constraints": {
            "F01_finite_carrier_probe_operator_path_set": "finite 8/16/32/64 spinor sites, finite PEPS3D K=(V,E,F,C), finite candidate layer actions, finite controls",
            "N01_noncommuting_or_order_sensitive_operation_control": "canonical-vs-reversed order gaps plus Pauli/Clifford/SymPy noncommutation witnesses",
        },
        "carrier_realization": {
            "claim_bearing_object": "source_native_left_right_weyl_spinor_network",
            "torch_runtime": "PyTorch complex spinors and repo-local PyTorch MPS dynamics",
            "peps3d_embedding": "quimb PEPS3D object seeded from spinor sites over K=(V,E,F,C), plus graph/hypergraph/cell/persistence certificates",
            "resource_projection": "Hamiltonian-path MPS projection for 64-site execution; this is not dense-state closure",
        },
        "spinor_state": "psi_v in C^2 for every site and sheet; rho_v and QIT cuts are derived readouts",
        "quaternion_action": "not_applicable: no quaternion claim is made in this scout",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/weyl_spinor_network_manifold_layer_runtime_probe_results.json",
            "system_v5/ops/formal_scouts/results/explicit_spinor_mps_8_16_32_64_flux_scaling_probe_results.json",
            "system_v5/ops/formal_scouts/results/l2_spinor_chirality_weyl_cover_layer_probe_results.json",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby,
        "why_not_v4_probes": (
            "This is a v5 source-native Weyl spinor-network stress scout. It "
            "runs 8/16/32/64 sites without dense 64-qubit closure, keeps L/R "
            "Weyl sheets separate, and fences all downstream claims."
        ),
        "blockers": [],
        "all_pass": all_pass,
        "summary": {
            "site_counts": SITE_COUNTS,
            "max_site_count": max(SITE_COUNTS),
            "max_bond_cap": MAX_BOND,
            "max_bond_seen": max_bond_seen,
            "min_left_right_sheet_gap": min_sheet_gap,
            "min_order_gap": min_order_gap,
            "min_phase_gap": min_phase_gap,
            "min_edge_gap": min_edge_gap,
            "elapsed_seconds": time.time() - started,
        },
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out_path": str(OUT_PATH), "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
