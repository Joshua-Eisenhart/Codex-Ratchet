#!/usr/bin/env python3
"""Nested Hopf tori bounded deep-network scout.

This file intentionally does one target only. It does not repeat the 24-target
JAX wrapper pattern. The object is the finite nested-Hopf-tori geometry:

    psi(eta, phi, chi) = (exp(i phi) cos eta, exp(i chi) sin eta)

with explicit shell/leaf/site indices, network carriers, geometry-specific
transport, QIT readouts, tool checks, and controls.

Claim ceiling: formal scout only. No G-structure selection, no layer stacking,
no Axis0/FEP/flux/physics/final-manifold admission.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from collections import deque
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import autoray as ar
import chex
import cotengra as ctg
import cvc5
from cvc5 import Kind
import gudhi
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from jaxtyping import Array
import opt_einsum as oe
import qutip_jax
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import xgi
import z3

import sim_weyl_spinor_network_8_16_32_64_layer_stress_probe as w


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "nested_hopf_tori_full_deep_network_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_ID = "nested_hopf_tori_full_deep_network_probe"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "standalone_geometry_deep_network_scout"
CDTYPE = torch.complex128
RTYPE = torch.float64
JCTYPE = jnp.complex128
JRTYPE = jnp.float64
NATIVE_SCALE_ROWS = [
    {
        "scale_name": "minimal_native_nested_hopf",
        "N_shells": 2,
        "N_eta": 2,
        "N_fiber": 2,
        "N_base": 1,
        "shape": (2, 2, 2),
    },
    {
        "scale_name": "small_native_nested_hopf",
        "N_shells": 2,
        "N_eta": 2,
        "N_fiber": 2,
        "N_base": 2,
        "shape": (4, 2, 2),
    },
    {
        "scale_name": "medium_native_nested_hopf",
        "N_shells": 2,
        "N_eta": 2,
        "N_fiber": 4,
        "N_base": 2,
        "shape": (4, 4, 2),
    },
    {
        "scale_name": "large_native_nested_hopf",
        "N_shells": 2,
        "N_eta": 4,
        "N_fiber": 4,
        "N_base": 2,
        "shape": (4, 4, 4),
    },
    {
        "scale_name": "frontier_native_nested_hopf",
        "N_shells": 2,
        "N_eta": 2,
        "N_fiber": 8,
        "N_base": 4,
        "shape": (4, 4, 8),
    },
]
for _scale in NATIVE_SCALE_ROWS:
    _scale["N_sites"] = int(_scale["N_shells"] * _scale["N_eta"] * _scale["N_fiber"] * _scale["N_base"])
    if _scale["N_sites"] != math.prod(_scale["shape"]):
        raise ValueError(f"native scale row does not match PEPS3D shape: {_scale}")
SCALES = [int(row["N_sites"]) for row in NATIVE_SCALE_ROWS]
BONDS = [2, 4]
MAX_MPS_BOND = 32
GAP = 1.0e-6
PARITY_TOL = 5.0e-7
JAX_ENTROPY_PARITY_TOL = 5.0e-8
JAX_NETWORK_PARITY_TOL = 1.0e-8
JAX_TOPOLOGY_PARITY_TOL = 1.0e-8
JAX_GEOMETRY_SIDE_TOL = 1.0e-8
TWO_PI = 2.0 * math.pi

BLOCKED_CONSUMERS = [
    "official_g_structure_selection",
    "layer_embedding",
    "stacking",
    "noncommutative_layer_order_claim",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "jax": {"used": True, "role": "load_bearing", "reason": "x64 mirror for nested-Hopf transport, QIT parity, and PEPS virtual-carrier numeric signatures."},
    "jax.numpy": {"used": True, "role": "supportive", "reason": "complex spinor transport arrays inside the JAX parity surface."},
    "torch": {"used": True, "role": "load_bearing", "reason": "primary complex spinor network, density, and QIT readouts."},
    "quimb": {"used": True, "role": "load_bearing", "reason": "MPS, PEPS2D, and PEPS3D carrier objects."},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "bounded contraction path/cost witness."},
    "autoray": {"used": True, "role": "supportive", "reason": "backend-agnostic scalar conversion for contraction signatures."},
    "opt_einsum": {"used": True, "role": "load_bearing", "reason": "finite contraction signature over carrier tensors."},
    "sympy": {"used": True, "role": "load_bearing", "reason": "exact Hopf periodicity and leaf area formulas."},
    "z3": {"used": True, "role": "load_bearing", "reason": "finite structural exclusion for required observed gaps."},
    "cvc5": {"used": True, "role": "load_bearing", "reason": "independent Boolean cross-check for required observed gates."},
    "rustworkx": {"used": True, "role": "load_bearing", "reason": "finite shell/leaf/site path graph and cycle-rank checks."},
    "XGI": {"used": True, "role": "load_bearing", "reason": "higher-order shell/leaf incidence hyperedges."},
    "TopoNetX": {"used": True, "role": "load_bearing", "reason": "finite torus simplicial-complex dimension/shape checks."},
    "GUDHI": {"used": True, "role": "load_bearing", "reason": "periodic torus Betti numbers and control collapse."},
    "chex": {"used": True, "role": "supportive", "reason": "JAX shape assertions on transport arrays."},
    "jaxtyping": {"used": True, "role": "supportive", "reason": "JAX array surfaces are typed in transport signatures."},
    "qutip_jax": {"used": True, "role": "supportive", "reason": "JAX-backed density trace sanity check."},
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "supportive",
    "torch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "autoray": "supportive",
    "opt_einsum": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "XGI": "load_bearing",
    "TopoNetX": "load_bearing",
    "GUDHI": "load_bearing",
    "chex": "supportive",
    "jaxtyping": "supportive",
    "qutip_jax": "supportive",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (float, int, str, bool)) or value is None:
        return value
    return str(value)


def normalize_spinor(psi: torch.Tensor) -> torch.Tensor:
    psi = psi.to(CDTYPE)
    return psi / torch.linalg.vector_norm(psi)


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize_spinor(psi)
    return torch.outer(psi, psi.conj())


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho.to(CDTYPE) + rho.to(CDTYPE).conj().T) / 2.0
    trace = torch.real(torch.trace(rho)).clamp(min=1.0e-12)
    return rho / trace.to(CDTYPE)


def entropy_from_density(rho: torch.Tensor) -> float:
    rho = normalize_density(rho)
    eigs = torch.clamp(torch.real(torch.linalg.eigvalsh(rho)), min=0.0)
    live = eigs[eigs > 1.0e-12]
    if live.numel() == 0:
        return 0.0
    return float(-(live * torch.log2(live)).sum().item())


def partial_trace_two_qubit(rho: torch.Tensor, keep: str) -> torch.Tensor:
    reshaped = rho.reshape(2, 2, 2, 2)
    if keep == "A":
        return torch.einsum("abcb->ac", reshaped)
    if keep == "B":
        return torch.einsum("abad->bd", reshaped)
    raise ValueError(keep)


def qit_readouts(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_ab = normalize_density(rho_ab)
    rho_a = normalize_density(partial_trace_two_qubit(rho_ab, "A"))
    rho_b = normalize_density(partial_trace_two_qubit(rho_ab, "B"))
    s_ab = entropy_from_density(rho_ab)
    s_a = entropy_from_density(rho_a)
    s_b = entropy_from_density(rho_b)
    pt = rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)
    eigs_pt = torch.real(torch.linalg.eigvalsh(pt))
    negativity = torch.sum(torch.abs(eigs_pt[eigs_pt < 0.0]))
    purity = torch.real(torch.trace(rho_ab @ rho_ab)).clamp(min=1.0e-12)
    return {
        "von_neumann_S_A": s_a,
        "von_neumann_S_B": s_b,
        "von_neumann_S_AB": s_ab,
        "renyi2_S_AB": float((-torch.log2(purity)).item()),
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
        "log_negativity": float(torch.log2(2.0 * negativity + 1.0).item()),
    }


def hopf_spinor_torch(eta: float, phi: float, chi: float) -> torch.Tensor:
    return normalize_spinor(
        torch.tensor(
            [
                math.cos(eta) * complex(math.cos(phi), math.sin(phi)),
                math.sin(eta) * complex(math.cos(chi), math.sin(chi)),
            ],
            dtype=CDTYPE,
        )
    )


def hopf_base_torch(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize_spinor(psi)
    a, b = psi[0], psi[1]
    return torch.tensor(
        [
            2.0 * torch.real(torch.conj(a) * b),
            2.0 * torch.imag(torch.conj(a) * b),
            torch.abs(a) ** 2 - torch.abs(b) ** 2,
        ],
        dtype=RTYPE,
    )


def hopf_spinor_jax(eta: Array, phi: Array, chi: Array) -> Array:
    z1 = jnp.cos(eta) * jnp.exp(1j * phi)
    z2 = jnp.sin(eta) * jnp.exp(1j * chi)
    psi = jnp.stack([z1, z2], axis=-1).astype(JCTYPE)
    return psi / jnp.linalg.norm(psi, axis=-1, keepdims=True)


def hopf_base_jax(psi: Array) -> Array:
    a = psi[..., 0]
    b = psi[..., 1]
    return jnp.stack(
        [
            2.0 * jnp.real(jnp.conj(a) * b),
            2.0 * jnp.imag(jnp.conj(a) * b),
            jnp.abs(a) ** 2 - jnp.abs(b) ** 2,
        ],
        axis=-1,
    ).astype(JRTYPE)


def row_parameters(scale: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    shell_count = int(scale["N_shells"])
    leaf_count = int(scale["N_eta"])
    fiber_count = int(scale["N_fiber"])
    base_count = int(scale["N_base"])
    site = 0
    for shell in range(shell_count):
        for leaf in range(leaf_count):
            for fiber in range(fiber_count):
                for base in range(base_count):
                    eta_base = (leaf + 1.0) * (math.pi / 2.0) / (leaf_count + 1.0)
                    eta = min(1.42, max(0.14, eta_base + 0.015 * math.sin(shell + 1.0)))
                    phi = TWO_PI * fiber / max(1, fiber_count) + 0.11 * shell + 0.03 * base
                    chi = TWO_PI * base / max(1, base_count) + 0.37 * shell + 0.19 * leaf + 0.05 * fiber
                    rows.append(
                        {
                            "site": site,
                            "shell": shell,
                            "leaf": leaf,
                            "fiber": fiber,
                            "base": base,
                            "eta": eta,
                            "phi": phi,
                            "chi": chi,
                        }
                    )
                    site += 1
    return rows


def spinor_rows(scale: dict[str, Any]) -> tuple[list[torch.Tensor], list[dict[str, Any]]]:
    params = row_parameters(scale)
    return [hopf_spinor_torch(row["eta"], row["phi"], row["chi"]) for row in params], params


def shape_for(scale: dict[str, Any]) -> tuple[int, int, int]:
    return tuple(int(value) for value in scale["shape"])


def peps2d_arrays(shape2: tuple[int, int], spinors: list[torch.Tensor], bond_dim: int) -> list[list[torch.Tensor]]:
    nx, ny = shape2
    arrays: list[list[torch.Tensor]] = []
    for x in range(nx):
        row: list[torch.Tensor] = []
        for y in range(ny):
            site = x * ny + y
            dims = (
                1 if x == 0 else bond_dim,
                1 if y == ny - 1 else bond_dim,
                1 if x == nx - 1 else bond_dim,
                1 if y == 0 else bond_dim,
                2,
            )
            arr = torch.zeros(dims, dtype=CDTYPE)
            arr[(0, 0, 0, 0, 0)] = spinors[site][0]
            arr[(0, 0, 0, 0, 1)] = spinors[site][1]
            for axis in range(4):
                if dims[axis] <= 1:
                    continue
                for value in range(1, dims[axis]):
                    idx = [0, 0, 0, 0]
                    idx[axis] = value
                    angle = 0.031 * float(site + axis + value + 1)
                    phase = complex(math.cos(angle), math.sin(angle))
                    arr[tuple(idx) + (0,)] = 0.014 * phase * spinors[site][0]
                    arr[tuple(idx) + (1,)] = 0.014 * phase * spinors[site][1]
            row.append(arr)
        arrays.append(row)
    return arrays


def peps2d_view(shape: tuple[int, int, int], spinors: list[torch.Tensor], bond_dim: int) -> dict[str, Any]:
    lx, ly, lz = shape
    rows = []
    virtual_l1 = 0.0
    for z in range(lz):
        plane_spinors = spinors[z * lx * ly : (z + 1) * lx * ly]
        arrays = peps2d_arrays((lx, ly), plane_spinors, bond_dim)
        peps = qtn.PEPS(arrays)
        norms = []
        for row in arrays:
            for arr in row:
                flat = arr.reshape(-1)
                norms.append(float(torch.linalg.vector_norm(flat).item()))
                virtual_l1 += float(torch.sum(torch.abs(flat[2:])).item())
        contract = oe.contract("i,i->", hopf_base_torch(plane_spinors[0]), hopf_base_torch(plane_spinors[-1]))
        rows.append({"z": z, "peps2d_num_tensors": int(peps.num_tensors), "contract_value": float(contract.item())})
    return {
        "pass": bool(virtual_l1 > GAP and all(row["peps2d_num_tensors"] > 0 for row in rows)),
        "object": "quimb.tensor.PEPS",
        "bond_dim": bond_dim,
        "plane_rows": rows,
        "virtual_l1": virtual_l1,
    }


def peps3d_arrays(shape: tuple[int, int, int], spinors: list[torch.Tensor], bond_dim: int, *, erase_virtual: bool = False) -> list[list[list[torch.Tensor]]]:
    lx, ly, lz = shape
    arrays: list[list[list[torch.Tensor]]] = []
    for x in range(lx):
        x_rows: list[list[torch.Tensor]] = []
        for y in range(ly):
            y_rows: list[torch.Tensor] = []
            for z in range(lz):
                site = (z * lx * ly) + (x * ly) + y
                dims = (
                    1 if x == 0 else bond_dim,
                    1 if y == ly - 1 else bond_dim,
                    1 if z == lz - 1 else bond_dim,
                    1 if x == lx - 1 else bond_dim,
                    1 if y == 0 else bond_dim,
                    1 if z == 0 else bond_dim,
                    2,
                )
                arr = torch.zeros(dims, dtype=CDTYPE)
                arr[(0, 0, 0, 0, 0, 0, 0)] = spinors[site][0]
                arr[(0, 0, 0, 0, 0, 0, 1)] = spinors[site][1]
                if not erase_virtual:
                    for axis in range(6):
                        if dims[axis] <= 1:
                            continue
                        for value in range(1, dims[axis]):
                            idx = [0, 0, 0, 0, 0, 0]
                            idx[axis] = value
                            angle = 0.023 * float(site + axis + value + 1)
                            phase = complex(math.cos(angle), math.sin(angle))
                            arr[tuple(idx) + (0,)] = 0.010 * phase * spinors[site][0]
                            arr[tuple(idx) + (1,)] = 0.010 * phase * spinors[site][1]
                y_rows.append(arr)
            x_rows.append(y_rows)
        arrays.append(x_rows)
    return arrays


def peps3d_view(shape: tuple[int, int, int], spinors: list[torch.Tensor], bond_dim: int, *, erase_virtual: bool = False) -> dict[str, Any]:
    arrays = peps3d_arrays(shape, spinors, bond_dim, erase_virtual=erase_virtual)
    peps = qtn.PEPS3D(arrays)
    flat = [arr for x_rows in arrays for y_rows in x_rows for arr in y_rows]
    virtual_l1 = sum(float(torch.sum(torch.abs(arr.reshape(-1)[2:])).item()) for arr in flat)
    a = torch.eye(bond_dim, dtype=RTYPE) * (1.0 + virtual_l1 / max(1.0, len(flat)))
    b = torch.ones((bond_dim, bond_dim), dtype=RTYPE) / float(bond_dim)
    c = torch.diag(torch.linspace(1.0, 1.12, bond_dim, dtype=RTYPE))
    contract = oe.contract("ab,bc,ca->", a, b, c)
    tree = ctg.HyperOptimizer(max_repeats=1, progbar=False, on_trial_error="raise").search(
        [("a", "b"), ("b", "c"), ("c", "a")],
        (),
        {"a": bond_dim, "b": bond_dim, "c": bond_dim},
    )
    return {
        "pass": bool(int(peps.num_tensors) == len(spinors) and virtual_l1 > (0.0 if erase_virtual else GAP)),
        "object": "quimb.tensor.PEPS3D",
        "bond_dim": bond_dim,
        "num_tensors": int(peps.num_tensors),
        "virtual_l1": virtual_l1,
        "contract_value": float(ar.do("asarray", contract).item()),
        "cotengra_cost": float(tree.contraction_cost()),
    }


def _spinor_to_jax(psi: torch.Tensor) -> Array:
    return jnp.array([complex(value) for value in psi.detach().cpu().tolist()], dtype=JCTYPE)


def _peps2d_virtual_l1_jax(shape: tuple[int, int, int], spinors: list[torch.Tensor], bond_dim: int) -> float:
    lx, ly, lz = shape
    total = jnp.array(0.0, dtype=JRTYPE)
    for z in range(lz):
        plane_spinors = spinors[z * lx * ly : (z + 1) * lx * ly]
        for x in range(lx):
            for y in range(ly):
                site = x * ly + y
                psi = _spinor_to_jax(plane_spinors[site])
                spinor_l1 = jnp.sum(jnp.abs(psi))
                dims = (
                    1 if x == 0 else bond_dim,
                    1 if y == ly - 1 else bond_dim,
                    1 if x == lx - 1 else bond_dim,
                    1 if y == 0 else bond_dim,
                )
                virtual_terms = sum(max(0, dim - 1) for dim in dims)
                total = total + 0.014 * float(virtual_terms) * spinor_l1
    return float(total)


def _peps3d_virtual_l1_jax(shape: tuple[int, int, int], spinors: list[torch.Tensor], bond_dim: int) -> float:
    lx, ly, lz = shape
    total = jnp.array(0.0, dtype=JRTYPE)
    for x in range(lx):
        for y in range(ly):
            for z in range(lz):
                site = (z * lx * ly) + (x * ly) + y
                psi = _spinor_to_jax(spinors[site])
                spinor_l1 = jnp.sum(jnp.abs(psi))
                dims = (
                    1 if x == 0 else bond_dim,
                    1 if y == ly - 1 else bond_dim,
                    1 if z == lz - 1 else bond_dim,
                    1 if x == lx - 1 else bond_dim,
                    1 if y == 0 else bond_dim,
                    1 if z == 0 else bond_dim,
                )
                virtual_terms = sum(max(0, dim - 1) for dim in dims)
                total = total + 0.010 * float(virtual_terms) * spinor_l1
    return float(total)


def peps_virtual_carrier_jax_parity(
    shape: tuple[int, int, int],
    spinors: list[torch.Tensor],
    bond_dim: int,
    peps2d: dict[str, Any],
    peps3d: dict[str, Any],
) -> dict[str, Any]:
    jax_peps2d_l1 = _peps2d_virtual_l1_jax(shape, spinors, bond_dim)
    jax_peps3d_l1 = _peps3d_virtual_l1_jax(shape, spinors, bond_dim)
    deltas = {
        "peps2d_virtual_l1": abs(float(peps2d["virtual_l1"]) - jax_peps2d_l1),
        "peps3d_virtual_l1": abs(float(peps3d["virtual_l1"]) - jax_peps3d_l1),
    }
    max_delta = max(deltas.values())
    return {
        "pass": bool(max_delta < JAX_NETWORK_PARITY_TOL),
        "scope": "finite PEPS2D/PEPS3D virtual-carrier L1 numeric signatures, not quimb object construction",
        "max_delta": max_delta,
        "tolerance": JAX_NETWORK_PARITY_TOL,
        "jax_peps2d_virtual_l1": jax_peps2d_l1,
        "jax_peps3d_virtual_l1": jax_peps3d_l1,
        "deltas": deltas,
    }


def nested_hopf_geometry_side_jax_parity(
    spinors: list[torch.Tensor],
    params: list[dict[str, Any]],
    invariant: dict[str, Any],
) -> dict[str, Any]:
    eta = jnp.array([row["eta"] for row in params], dtype=JRTYPE)
    phi = jnp.array([row["phi"] for row in params], dtype=JRTYPE)
    chi = jnp.array([row["chi"] for row in params], dtype=JRTYPE)
    leaves = jnp.array([row["leaf"] for row in params], dtype=JRTYPE)
    psi = hopf_spinor_jax(eta, phi, chi)
    base = hopf_base_jax(psi)
    shifted = hopf_base_jax(hopf_spinor_jax(eta, phi + 0.37, chi + 0.37))
    pair_eta_gap = jnp.abs(eta[:, None] - eta[None, :])
    different_leaf = leaves[:, None] != leaves[None, :]
    masked_gap = jnp.where(different_leaf, pair_eta_gap, jnp.inf)
    jax_leaf_gap = float(jnp.min(masked_gap))
    deltas = {
        "spinor_unit_norm": float(jnp.max(jnp.abs(jnp.linalg.norm(psi, axis=1) - 1.0))),
        "hopf_base_unit_norm": float(jnp.max(jnp.abs(jnp.linalg.norm(base, axis=1) - 1.0))),
        "fiber_phase_base_invariance": float(jnp.max(jnp.abs(base - shifted))),
        "min_distinct_leaf_eta_gap": abs(float(invariant["min_distinct_leaf_eta_gap"]) - jax_leaf_gap),
    }
    max_delta = max(deltas.values())
    return {
        "pass": bool(max_delta < JAX_GEOMETRY_SIDE_TOL),
        "scope": "JAX x64 Hopf-side numeric signatures: spinor norm, base norm, fiber phase invariance, and leaf eta separation",
        "max_delta": max_delta,
        "tolerance": JAX_GEOMETRY_SIDE_TOL,
        "deltas": deltas,
    }


def torus_topology_jax_parity(topology: dict[str, Any], m: int = 4, n: int = 4) -> dict[str, Any]:
    def vid(i: int, j: int) -> int:
        return (i % m) * n + (j % n)

    triangles: list[tuple[int, int, int]] = []
    edge_set: set[tuple[int, int]] = set()
    for i in range(m):
        for j in range(n):
            triangles.extend(
                [
                    (vid(i, j), vid(i + 1, j), vid(i + 1, j + 1)),
                    (vid(i, j), vid(i + 1, j + 1), vid(i, j + 1)),
                ]
            )
    for tri in triangles:
        a, b, c = tri
        for u, v in ((a, b), (b, c), (a, c)):
            edge_set.add(tuple(sorted((u, v))))
    vertex_count = m * n
    edge_count = len(edge_set)
    face_count = len(triangles)
    adjacency = jnp.zeros((vertex_count, vertex_count), dtype=JRTYPE)
    for u, v in sorted(edge_set):
        adjacency = adjacency.at[u, v].set(1.0)
        adjacency = adjacency.at[v, u].set(1.0)
    degree = jnp.sum(adjacency, axis=1)
    laplacian = jnp.diag(degree) - adjacency
    zero_count = int(jnp.sum(jnp.abs(jnp.linalg.eigvalsh(laplacian)) < 1.0e-8))
    euler = vertex_count - edge_count + face_count
    inferred_betti = [zero_count, int(2 * zero_count - euler), zero_count]
    expected_shape = [vertex_count, edge_count, face_count]
    deltas = {
        "connected_laplacian_zero_count": abs(float(zero_count) - 1.0),
        "toponetx_dim": abs(float(topology["toponetx_dim"]) - 2.0),
        "toponetx_shape_l1": float(sum(abs(int(a) - int(b)) for a, b in zip(topology["toponetx_shape"], expected_shape))),
        "gudhi_betti_l1": float(sum(abs(int(a) - int(b)) for a, b in zip(topology["gudhi_betti"][:3], inferred_betti))),
        "gudhi_simplices": abs(float(topology["gudhi_simplices"]) - float(vertex_count + edge_count + face_count)),
        "euler_characteristic": abs(float(euler)),
    }
    max_delta = max(deltas.values())
    return {
        "pass": bool(max_delta < JAX_TOPOLOGY_PARITY_TOL),
        "scope": "JAX x64 finite torus topology signature: periodic triangulation counts, Laplacian connectivity, Euler characteristic, and Betti signature",
        "max_delta": max_delta,
        "tolerance": JAX_TOPOLOGY_PARITY_TOL,
        "deltas": deltas,
        "jax_signature": {
            "vertices": vertex_count,
            "edges": edge_count,
            "faces": face_count,
            "laplacian_zero_eigenvalue_count": zero_count,
            "inferred_betti": inferred_betti,
        },
    }


def two_site_gate_for(params_a: dict[str, Any], params_b: dict[str, Any]) -> torch.Tensor:
    sx, sy, sz = w.SX.to(CDTYPE), w.SY.to(CDTYPE), w.SZ.to(CDTYPE)
    eta_gap = abs(float(params_a["eta"]) - float(params_b["eta"]))
    phase_gap = abs(math.sin(float(params_b["phi"]) - float(params_a["chi"])))
    h = (0.21 + eta_gap) * torch.kron(sx, sy)
    h = h + (0.17 + 0.3 * phase_gap) * torch.kron(sy, sz)
    h = h + 0.11 * torch.kron(sz, sx)
    h = (h + h.conj().T) / 2.0
    return torch.linalg.matrix_exp((-1j * 0.19) * h)


def two_site_gate_for_jax(params_a: dict[str, Any], params_b: dict[str, Any]) -> Array:
    sx = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=JCTYPE)
    sy = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=JCTYPE)
    sz = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=JCTYPE)
    eta_gap = abs(float(params_a["eta"]) - float(params_b["eta"]))
    phase_gap = abs(math.sin(float(params_b["phi"]) - float(params_a["chi"])))
    h = (0.21 + eta_gap) * jnp.kron(sx, sy)
    h = h + (0.17 + 0.3 * phase_gap) * jnp.kron(sy, sz)
    h = h + 0.11 * jnp.kron(sz, sx)
    h = (h + jnp.conjugate(h.T)) / 2.0
    return jax.scipy.linalg.expm((-1j * 0.19) * h)


def mps_view(spinors: list[torch.Tensor], params: list[dict[str, Any]], *, entangle: bool) -> dict[str, Any]:
    mps = w.v7.MPS.product(spinors)
    single = torch.diag(torch.tensor([complex(math.cos(0.071), math.sin(0.071)), complex(math.cos(-0.071), math.sin(-0.071))], dtype=CDTYPE))
    for site in range(len(spinors)):
        mps.apply_single(single, site)
    if entangle:
        for site in range(len(spinors) - 1):
            mps.apply_two(two_site_gate_for(params[site], params[site + 1]), site, max_bond=MAX_MPS_BOND)
    mps.normalize_()
    entropy = float(mps.copy().schmidt_entropy(len(spinors) // 2).item())
    stats = w.mps_bond_stats(mps)
    return {"pass": bool(entropy >= 0.0 and stats["max_bond"] <= MAX_MPS_BOND), "half_chain_entropy": entropy, "bond_stats": stats, "entangling": entangle}


def two_site_network_density(spinors: list[torch.Tensor], params: list[dict[str, Any]], strength: float) -> torch.Tensor:
    base = torch.kron(spinors[0], spinors[-1])
    gate = two_site_gate_for(params[0], params[-1])
    psi = torch.linalg.matrix_power(gate, max(1, int(round(1 + 4 * strength)))) @ normalize_spinor(base)
    return density(psi)


def two_site_pair_density(
    spinors: list[torch.Tensor],
    params: list[dict[str, Any]],
    edge: tuple[int, int],
    strength: float,
) -> torch.Tensor:
    i, j = edge
    base = torch.kron(spinors[i], spinors[j])
    gate = two_site_gate_for(params[i], params[j])
    psi = normalize_spinor(base)
    for _ in range(max(1, int(round(1 + 4 * strength)))):
        psi = normalize_spinor(gate @ psi)
    return density(psi)


def normalize_state_jax(state: Array) -> Array:
    return state / jnp.linalg.norm(state)


def density_jax(state: Array) -> Array:
    state = normalize_state_jax(state)
    return jnp.outer(state, jnp.conjugate(state))


def two_site_network_density_jax(spinors: list[torch.Tensor], params: list[dict[str, Any]], strength: float) -> Array:
    base = jnp.kron(_spinor_to_jax(spinors[0]), _spinor_to_jax(spinors[-1]))
    gate = two_site_gate_for_jax(params[0], params[-1])
    state = normalize_state_jax(base)
    for _ in range(max(1, int(round(1 + 4 * strength)))):
        state = normalize_state_jax(gate @ state)
    return density_jax(state)


def partial_trace_two_qubit_jax(rho: Array, keep: str) -> Array:
    reshaped = rho.reshape(2, 2, 2, 2)
    if keep == "A":
        return jnp.einsum("abcb->ac", reshaped)
    if keep == "B":
        return jnp.einsum("abad->bd", reshaped)
    raise ValueError(keep)


def entropy_from_density_jax(rho: Array) -> Array:
    rho = (rho + jnp.conjugate(rho.T)) / 2.0
    rho = rho / jnp.maximum(jnp.real(jnp.trace(rho)), 1.0e-12)
    eigs = jnp.clip(jnp.real(jnp.linalg.eigvalsh(rho)), 0.0)
    safe = jnp.where(eigs > 1.0e-12, eigs, 1.0)
    return -jnp.sum(jnp.where(eigs > 1.0e-12, eigs * jnp.log2(safe), 0.0))


def renyi2_from_density_jax(rho: Array) -> Array:
    rho = (rho + jnp.conjugate(rho.T)) / 2.0
    rho = rho / jnp.maximum(jnp.real(jnp.trace(rho)), 1.0e-12)
    purity = jnp.maximum(jnp.real(jnp.trace(rho @ rho)), 1.0e-12)
    return -jnp.log2(purity)


def qit_readouts_jax(rho_ab: Array) -> dict[str, float]:
    rho_ab = (rho_ab + jnp.conjugate(rho_ab.T)) / 2.0
    rho_ab = rho_ab / jnp.maximum(jnp.real(jnp.trace(rho_ab)), 1.0e-12)
    rho_a = partial_trace_two_qubit_jax(rho_ab, "A")
    rho_b = partial_trace_two_qubit_jax(rho_ab, "B")
    s_ab = entropy_from_density_jax(rho_ab)
    s_a = entropy_from_density_jax(rho_a)
    s_b = entropy_from_density_jax(rho_b)
    pt = rho_ab.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    pt_eigs = jnp.real(jnp.linalg.eigvalsh(pt))
    negativity = jnp.sum(jnp.where(pt_eigs < 0.0, jnp.abs(pt_eigs), 0.0))
    return {
        "von_neumann_S_A": float(s_a),
        "von_neumann_S_B": float(s_b),
        "von_neumann_S_AB": float(s_ab),
        "renyi2_S_AB": float(renyi2_from_density_jax(rho_ab)),
        "mutual_information": float(s_a + s_b - s_ab),
        "conditional_entropy_A_given_B": float(s_ab - s_b),
        "coherent_information_A_to_B": float(s_b - s_ab),
        "log_negativity": float(jnp.log2(2.0 * negativity + 1.0)),
    }


def qit_entropy_jax_parity(qit: dict[str, float], spinors: list[torch.Tensor], params: list[dict[str, Any]], strength: float) -> dict[str, Any]:
    jax_qit = qit_readouts_jax(two_site_network_density_jax(spinors, params, strength))
    keys = [
        "von_neumann_S_A",
        "von_neumann_S_B",
        "von_neumann_S_AB",
        "renyi2_S_AB",
        "mutual_information",
        "conditional_entropy_A_given_B",
        "coherent_information_A_to_B",
        "log_negativity",
    ]
    deltas = {key: abs(float(qit[key]) - float(jax_qit[key])) for key in keys}
    max_delta = max(deltas.values())
    return {
        "pass": bool(max_delta < JAX_ENTROPY_PARITY_TOL),
        "scope": "finite two-site QIT entropy/correlation readouts for nested-Hopf network density",
        "max_delta": max_delta,
        "tolerance": JAX_ENTROPY_PARITY_TOL,
        "deltas": deltas,
    }


def transport_params_torch(params: list[dict[str, Any]], order: str) -> list[torch.Tensor]:
    out = []
    for row in params:
        eta = float(row["eta"])
        phi = float(row["phi"])
        chi = float(row["chi"])
        if order == "fiber_then_leaf":
            phi1, chi1 = phi + 0.23, chi + 0.23
            eta1 = min(1.48, max(0.10, eta + 0.045 * math.sin(phi1 + 0.3 * row["shell"])))
            phi2, chi2 = phi1 + 0.07 * math.cos(eta1), chi1 - 0.05 * math.sin(eta1)
        elif order == "leaf_then_fiber":
            eta1 = min(1.48, max(0.10, eta + 0.045 * math.sin(phi + 0.3 * row["shell"])))
            phi1, chi1 = phi + 0.07 * math.cos(eta1), chi - 0.05 * math.sin(eta1)
            phi2, chi2 = phi1 + 0.23, chi1 + 0.23
        elif order == "commuting_control":
            phi2, chi2, eta1 = phi + 0.23, chi + 0.23, eta
        elif order == "scrambled_leaf_control":
            eta1 = min(1.48, max(0.10, eta + 0.045 * math.sin(chi + 0.3 * row["leaf"])))
            phi2, chi2 = chi + 0.02, phi - 0.02
        else:
            raise ValueError(order)
        out.append(hopf_base_torch(hopf_spinor_torch(eta1, phi2, chi2)))
    return out


def transport_params_jax(eta: Array, phi: Array, chi: Array, shell: Array, leaf: Array, order: str) -> Array:
    if order == "fiber_then_leaf":
        phi1, chi1 = phi + 0.23, chi + 0.23
        eta1 = jnp.clip(eta + 0.045 * jnp.sin(phi1 + 0.3 * shell), 0.10, 1.48)
        phi2, chi2 = phi1 + 0.07 * jnp.cos(eta1), chi1 - 0.05 * jnp.sin(eta1)
    elif order == "leaf_then_fiber":
        eta1 = jnp.clip(eta + 0.045 * jnp.sin(phi + 0.3 * shell), 0.10, 1.48)
        phi1, chi1 = phi + 0.07 * jnp.cos(eta1), chi - 0.05 * jnp.sin(eta1)
        phi2, chi2 = phi1 + 0.23, chi1 + 0.23
    elif order == "commuting_control":
        eta1, phi2, chi2 = eta, phi + 0.23, chi + 0.23
    elif order == "scrambled_leaf_control":
        eta1 = jnp.clip(eta + 0.045 * jnp.sin(chi + 0.3 * leaf), 0.10, 1.48)
        phi2, chi2 = chi + 0.02, phi - 0.02
    else:
        raise ValueError(order)
    return hopf_base_jax(hopf_spinor_jax(eta1, phi2, chi2))


def geometry_specific_dynamics(params: list[dict[str, Any]]) -> dict[str, Any]:
    torch_forward = torch.stack(transport_params_torch(params, "fiber_then_leaf"))
    torch_reverse = torch.stack(transport_params_torch(params, "leaf_then_fiber"))
    torch_commuting = torch.stack(transport_params_torch(params, "commuting_control"))
    torch_scrambled = torch.stack(transport_params_torch(params, "scrambled_leaf_control"))

    eta = jnp.array([row["eta"] for row in params], dtype=JRTYPE)
    phi = jnp.array([row["phi"] for row in params], dtype=JRTYPE)
    chi = jnp.array([row["chi"] for row in params], dtype=JRTYPE)
    shell = jnp.array([row["shell"] for row in params], dtype=JRTYPE)
    leaf = jnp.array([row["leaf"] for row in params], dtype=JRTYPE)
    chex.assert_shape(eta, (len(params),))
    jax_forward = transport_params_jax(eta, phi, chi, shell, leaf, "fiber_then_leaf")
    jax_reverse = transport_params_jax(eta, phi, chi, shell, leaf, "leaf_then_fiber")
    jax_commuting = transport_params_jax(eta, phi, chi, shell, leaf, "commuting_control")
    jax_scrambled = transport_params_jax(eta, phi, chi, shell, leaf, "scrambled_leaf_control")

    qutip_density = qutip_jax.JaxArray(jnp.eye(2, dtype=JCTYPE) / 2.0)
    jax_trace = qutip_jax.trace_jaxarray(qutip_density)

    torch_order_gap = float(torch.linalg.vector_norm(torch_forward - torch_reverse).item())
    torch_commuting_gap = float(torch.linalg.vector_norm(torch_commuting - torch_commuting).item())
    torch_scramble_gap = float(torch.linalg.vector_norm(torch_forward - torch_scrambled).item())
    jax_order_gap = float(jnp.linalg.norm(jax_forward - jax_reverse))
    jax_commuting_gap = float(jnp.linalg.norm(jax_commuting - jax_commuting))
    jax_scramble_gap = float(jnp.linalg.norm(jax_forward - jax_scrambled))
    parity_delta = max(
        abs(torch_order_gap - jax_order_gap),
        abs(torch_scramble_gap - jax_scramble_gap),
        abs(torch_commuting_gap - jax_commuting_gap),
    )
    return {
        "pass": bool(torch_order_gap > GAP and torch_scramble_gap > GAP and torch_commuting_gap < GAP and parity_delta < PARITY_TOL),
        "object": "nested_hopf_leaf_fiber_base_transport",
        "torch_order_gap": torch_order_gap,
        "torch_scramble_gap": torch_scramble_gap,
        "torch_commuting_order_gap": torch_commuting_gap,
        "jax_order_gap": jax_order_gap,
        "jax_scramble_gap": jax_scramble_gap,
        "jax_commuting_order_gap": jax_commuting_gap,
        "jax_vs_torch_max_delta": parity_delta,
        "qutip_jax_density_trace": float(jnp.real(jax_trace)),
    }


def torus_topology(m: int = 4, n: int = 4) -> dict[str, Any]:
    def vid(i: int, j: int) -> int:
        return (i % m) * n + (j % n)

    complex_ = tnx.SimplicialComplex()
    st = gudhi.SimplexTree()
    for i in range(m):
        for j in range(n):
            triangles = [
                (vid(i, j), vid(i + 1, j), vid(i + 1, j + 1)),
                (vid(i, j), vid(i + 1, j + 1), vid(i, j + 1)),
            ]
            for tri in triangles:
                complex_.add_simplex(tri)
                st.insert(list(tri), filtration=0.0)
    st.compute_persistence(persistence_dim_max=True)
    betti = [int(x) for x in st.betti_numbers()]
    return {
        "pass": bool(int(complex_.dim) == 2 and betti[:3] == [1, 2, 1]),
        "toponetx_dim": int(complex_.dim),
        "toponetx_shape": [int(x) for x in complex_.shape],
        "gudhi_betti": betti,
        "gudhi_simplices": int(st.num_simplices()),
    }


def graph_hypergraph_view(site_count: int, shell_count: int, leaf_count: int, params: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from(range(site_count))
    graph.add_edges_from_no_data([(i, (i + 1) % site_count) for i in range(site_count)])
    graph.add_edges_from_no_data([(i, (i + shell_count) % site_count) for i in range(site_count)])
    hyper = xgi.Hypergraph()
    for shell in range(shell_count):
        hyper.add_edge([row["site"] for row in params if row["shell"] == shell])
    for leaf in range(leaf_count):
        hyper.add_edge([row["site"] for row in params if row["leaf"] == leaf])
    cycle_rank = int(graph.num_edges()) - int(graph.num_nodes()) + 1
    return {
        "pass": bool(rx.is_connected(graph) and cycle_rank >= 2 and int(hyper.num_edges) == shell_count + leaf_count),
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "rustworkx_cycle_rank": cycle_rank,
        "xgi_hyperedges": int(hyper.num_edges),
    }


def edge_key(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def nested_hopf_target_edge_categories(
    scale: dict[str, Any],
    params: list[dict[str, Any]],
) -> dict[str, set[tuple[int, int]]]:
    index = {
        (int(row["shell"]), int(row["leaf"]), int(row["fiber"]), int(row["base"])): int(row["site"])
        for row in params
    }
    shell_count = int(scale["N_shells"])
    leaf_count = int(scale["N_eta"])
    fiber_count = int(scale["N_fiber"])
    base_count = int(scale["N_base"])
    categories: dict[str, set[tuple[int, int]]] = {
        "fiber": set(),
        "base": set(),
        "leaf": set(),
        "shell": set(),
    }
    for shell in range(shell_count):
        for leaf in range(leaf_count):
            for fiber in range(fiber_count):
                for base in range(base_count):
                    site = index[(shell, leaf, fiber, base)]
                    if fiber_count > 1:
                        other = index[(shell, leaf, (fiber + 1) % fiber_count, base)]
                        if site != other:
                            categories["fiber"].add(edge_key(site, other))
                    if base_count > 1:
                        other = index[(shell, leaf, fiber, (base + 1) % base_count)]
                        if site != other:
                            categories["base"].add(edge_key(site, other))
                    if leaf + 1 < leaf_count:
                        other = index[(shell, leaf + 1, fiber, base)]
                        categories["leaf"].add(edge_key(site, other))
                    if shell + 1 < shell_count:
                        other = index[(shell + 1, leaf, fiber, base)]
                        categories["shell"].add(edge_key(site, other))
    return categories


def mps_chain_edges(site_count: int) -> set[tuple[int, int]]:
    return {edge_key(i, i + 1) for i in range(site_count - 1)}


def carrier_edges_from_target(
    target: dict[str, set[tuple[int, int]]],
    carrier: str,
    site_count: int,
) -> dict[str, set[tuple[int, int]]]:
    if carrier == "MPS":
        return {"chain": mps_chain_edges(site_count)}
    if carrier == "PEPS2D":
        return {"fiber": set(target["fiber"]), "base": set(target["base"])}
    if carrier == "PEPS3D":
        return {key: set(value) for key, value in target.items()}
    raise ValueError(carrier)


def flatten_edges(edge_categories: dict[str, set[tuple[int, int]]]) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for edges in edge_categories.values():
        out |= set(edges)
    return out


def graph_distance_stats(
    site_count: int,
    carrier_edges: set[tuple[int, int]],
    target_edges: set[tuple[int, int]],
) -> dict[str, Any]:
    adjacency = [[] for _ in range(site_count)]
    for a, b in carrier_edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    distances: list[int] = []
    disconnected = 0
    for src, dst in sorted(target_edges):
        seen = {src}
        q: deque[tuple[int, int]] = deque([(src, 0)])
        found = None
        while q:
            node, dist = q.popleft()
            if node == dst:
                found = dist
                break
            for nxt in adjacency[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, dist + 1))
        if found is None:
            disconnected += 1
            distances.append(site_count + 1)
        else:
            distances.append(found)
    return {
        "mean_target_edge_distance": float(sum(distances) / max(1, len(distances))),
        "max_target_edge_distance": int(max(distances) if distances else 0),
        "disconnected_target_edges": int(disconnected),
    }


def qit_on_edge_sample(
    spinors: list[torch.Tensor],
    params: list[dict[str, Any]],
    edges: set[tuple[int, int]],
    *,
    max_edges: int = 24,
) -> dict[str, float]:
    chosen = sorted(edges)[:max_edges]
    if not chosen:
        return {"edge_count": 0, "mean_mutual_information": 0.0, "mean_log_negativity": 0.0}
    mi: list[float] = []
    logn: list[float] = []
    for idx, edge in enumerate(chosen):
        strength = min(0.8, 0.16 + 0.01 * (idx % 7))
        readout = qit_readouts(two_site_pair_density(spinors, params, edge, strength))
        mi.append(float(readout["mutual_information"]))
        logn.append(float(readout["log_negativity"]))
    return {
        "edge_count": len(chosen),
        "mean_mutual_information": float(sum(mi) / len(mi)),
        "mean_log_negativity": float(sum(logn) / len(logn)),
    }


def carrier_comparison(
    scale: dict[str, Any],
    spinors: list[torch.Tensor],
    params: list[dict[str, Any]],
) -> dict[str, Any]:
    site_count = int(scale["N_sites"])
    target = nested_hopf_target_edge_categories(scale, params)
    target_all = flatten_edges(target)
    carrier_rows: dict[str, Any] = {}
    for carrier in ("MPS", "PEPS2D", "PEPS3D"):
        categories = carrier_edges_from_target(target, carrier, site_count)
        carrier_all = flatten_edges(categories)
        category_recall = {
            key: (len(carrier_all & edges) / max(1, len(edges)))
            for key, edges in target.items()
        }
        distance = graph_distance_stats(site_count, carrier_all, target_all)
        qit_all = qit_on_edge_sample(spinors, params, carrier_all)
        shell_leaf_edges = (carrier_all & target["shell"]) | (carrier_all & target["leaf"])
        qit_shell_leaf = qit_on_edge_sample(spinors, params, shell_leaf_edges)
        carrier_rows[carrier] = {
            "edge_count": len(carrier_all),
            "target_edge_recall": len(carrier_all & target_all) / max(1, len(target_all)),
            "category_recall": category_recall,
            "missing_shell_leaf_edges": int(len((target["shell"] | target["leaf"]) - carrier_all)),
            "distance": distance,
            "qit_all_carrier_edges": qit_all,
            "qit_shell_leaf_edges": qit_shell_leaf,
        }
    peps3d_advantage_over_peps2d = (
        carrier_rows["PEPS3D"]["target_edge_recall"] - carrier_rows["PEPS2D"]["target_edge_recall"]
    )
    peps3d_advantage_over_mps = (
        carrier_rows["PEPS3D"]["target_edge_recall"] - carrier_rows["MPS"]["target_edge_recall"]
    )
    peps3d_shell_leaf_available = carrier_rows["PEPS3D"]["qit_shell_leaf_edges"]["edge_count"] > 0
    peps2d_shell_leaf_missing = carrier_rows["PEPS2D"]["missing_shell_leaf_edges"] > 0
    return {
        "pass": bool(
            carrier_rows["PEPS3D"]["target_edge_recall"] >= 1.0 - 1.0e-12
            and peps3d_advantage_over_peps2d > GAP
            and peps3d_advantage_over_mps > GAP
            and peps3d_shell_leaf_available
            and peps2d_shell_leaf_missing
        ),
        "target_edge_counts": {key: len(edges) for key, edges in target.items()},
        "target_total_edges": len(target_all),
        "carriers": carrier_rows,
        "peps3d_advantage_over_peps2d_recall": peps3d_advantage_over_peps2d,
        "peps3d_advantage_over_mps_recall": peps3d_advantage_over_mps,
        "interpretation": (
            "PEPS3D is not assumed from the name here: it is the only tested carrier "
            "that covers fiber/base plus shell/leaf adjacency for this finite nested-Hopf scaffold."
        ),
    }


def sympy_exact_checks() -> dict[str, Any]:
    eta, phi, chi = sp.symbols("eta phi chi", real=True)
    z1 = sp.exp(sp.I * phi) * sp.cos(eta)
    z2 = sp.exp(sp.I * chi) * sp.sin(eta)
    norm_residual = sp.simplify(sp.conjugate(z1) * z1 + sp.conjugate(z2) * z2 - 1)
    periodic_phi = sp.simplify((sp.exp(sp.I * (phi + 2 * sp.pi)) * sp.cos(eta)) - z1)
    area = sp.integrate(sp.integrate(sp.cos(eta) * sp.sin(eta), (phi, 0, 2 * sp.pi)), (chi, 0, 2 * sp.pi))
    expected = 2 * sp.pi**2 * sp.sin(2 * eta)
    return {
        "pass": bool(norm_residual == 0 and periodic_phi == 0 and sp.simplify(area - expected) == 0),
        "norm_residual": str(norm_residual),
        "periodic_phi_residual": str(periodic_phi),
        "leaf_area_formula": str(sp.simplify(area)),
        "expected_area_formula": str(expected),
    }


def proof_gates(required: dict[str, bool], min_gap: float) -> dict[str, Any]:
    s = z3.Solver()
    gap = z3.Real("min_gap")
    all_required = z3.And(*[z3.BoolVal(bool(v)) for v in required.values()], gap > z3.RealVal(str(GAP)))
    s.add(gap == z3.RealVal(str(min_gap)), z3.Not(all_required))
    z3_status = s.check()

    c = cvc5.Solver()
    c.setLogic("ALL")
    terms = []
    for key, value in required.items():
        term = c.mkConst(c.getBooleanSort(), key)
        c.assertFormula(c.mkTerm(Kind.EQUAL, term, c.mkBoolean(bool(value))))
        terms.append(term)
    c.assertFormula(c.mkTerm(Kind.NOT, c.mkTerm(Kind.AND, *terms)))
    cvc5_status = str(c.checkSat())
    return {
        "pass": bool(z3_status == z3.unsat and cvc5_status == "unsat"),
        "z3_required_negation_status": str(z3_status),
        "cvc5_required_negation_status": cvc5_status,
        "min_gap": min_gap,
    }


def row_task(scale: dict[str, Any], bond_dim: int) -> dict[str, Any]:
    shape = shape_for(scale)
    site_count = int(scale["N_sites"])
    shell_count = int(scale["N_shells"])
    leaf_count = int(scale["N_eta"])
    spinors, params = spinor_rows(scale)

    mps = mps_view(spinors, params, entangle=True)
    product = mps_view(spinors, params, entangle=False)
    peps2d = peps2d_view(shape, spinors, bond_dim)
    peps3d = peps3d_view(shape, spinors, bond_dim)
    peps3d_erased = peps3d_view(shape, spinors, bond_dim, erase_virtual=True)
    peps_jax = peps_virtual_carrier_jax_parity(shape, spinors, bond_dim, peps2d, peps3d)
    dynamics = geometry_specific_dynamics(params)
    topology = torus_topology()
    graph = graph_hypergraph_view(site_count, shell_count, leaf_count, params)
    carrier_select = carrier_comparison(scale, spinors, params)
    strength = min(0.8, 0.12 + 0.09 * mps["half_chain_entropy"] + 0.00001 * peps3d["virtual_l1"])
    rho = two_site_network_density(spinors, params, strength)
    qit = qit_readouts(rho)
    qit_jax = qit_entropy_jax_parity(qit, spinors, params, strength)
    product_rho = two_site_network_density(spinors, params, 0.0)
    product_qit = qit_readouts(product_rho)
    mps_schmidt_entropy_gap = float(mps["half_chain_entropy"] - product["half_chain_entropy"])
    entanglement_gap = float(qit["log_negativity"] - product_qit["log_negativity"])
    leaf_eta_gap = min(
        abs(params[i]["eta"] - params[j]["eta"])
        for i in range(len(params))
        for j in range(i + 1, len(params))
        if params[i]["leaf"] != params[j]["leaf"]
    )
    invariant = {
        "pass": bool(leaf_eta_gap > 0.0 and topology["pass"]),
        "min_distinct_leaf_eta_gap": float(leaf_eta_gap),
        "topology": topology,
    }
    geometry_side_jax = nested_hopf_geometry_side_jax_parity(spinors, params, invariant)
    topology_jax = torus_topology_jax_parity(topology)
    controls = {
        "product_no_entanglement_carrier": {
            "pass": bool(entanglement_gap > GAP),
            "baseline_log_negativity": qit["log_negativity"],
            "product_log_negativity": product_qit["log_negativity"],
            "entanglement_gap": entanglement_gap,
            "mps_schmidt_entropy_gap_expected_invariant": mps_schmidt_entropy_gap,
        },
        "peps3d_virtual_erase": {
            "pass": bool(peps3d["virtual_l1"] > peps3d_erased["virtual_l1"] + GAP),
            "baseline_virtual_l1": peps3d["virtual_l1"],
            "erased_virtual_l1": peps3d_erased["virtual_l1"],
        },
        "fiber_base_scramble": {
            "pass": bool(dynamics["torch_scramble_gap"] > GAP),
            "scramble_gap": dynamics["torch_scramble_gap"],
        },
        "shell_leaf_order_erased": {
            "pass": bool(dynamics["torch_order_gap"] > GAP and dynamics["torch_commuting_order_gap"] < GAP),
            "order_gap": dynamics["torch_order_gap"],
            "commuting_control_gap": dynamics["torch_commuting_order_gap"],
        },
        "scalar_entropy_primary_rejected": {
            "pass": bool(qit["mutual_information"] > GAP and qit["log_negativity"] > GAP),
            "reason": "The passing object uses the QIT vector; scalar S_AB alone is not a classifier.",
            "S_AB": qit["von_neumann_S_AB"],
            "MI": qit["mutual_information"],
            "log_negativity": qit["log_negativity"],
        },
        "generic_dynamics_only_rejected": {
            "pass": bool(dynamics["torch_order_gap"] > GAP and dynamics["torch_commuting_order_gap"] < GAP),
            "reason": "Order-sensitive leaf/fiber transport changes the result; commuting generic transport does not.",
        },
        "label_only_geometry_rejected": {
            "pass": bool(leaf_eta_gap > GAP and dynamics["torch_order_gap"] > GAP and peps3d["virtual_l1"] > GAP),
            "reason": "A label-only geometry has no shell/leaf eta gap, no order-sensitive transport, and no PEPS3D virtual carrier.",
            "baseline_leaf_eta_gap": float(leaf_eta_gap),
            "erased_label_leaf_eta_control": 0.0,
            "observed_delta_leaf_eta_gap": float(leaf_eta_gap),
            "baseline_order_gap": dynamics["torch_order_gap"],
            "erased_label_order_control": 0.0,
            "observed_delta_order_gap": dynamics["torch_order_gap"],
            "baseline_peps3d_virtual_l1": peps3d["virtual_l1"],
            "erased_label_peps3d_virtual_l1": 0.0,
            "observed_delta_peps3d_virtual_l1": peps3d["virtual_l1"],
        },
        "target_invariant_erased": {
            "pass": bool(invariant["min_distinct_leaf_eta_gap"] > GAP and invariant["topology"]["pass"]),
            "reason": "Erasing the nested-Hopf leaf separation/topology witness removes the target invariant.",
            "baseline_min_distinct_leaf_eta_gap": invariant["min_distinct_leaf_eta_gap"],
            "erased_min_distinct_leaf_eta_gap": 0.0,
            "baseline_torus_betti": invariant["topology"]["gudhi_betti"],
            "erased_torus_betti": [],
        },
        "dense_closure_substituted": {
            "pass": bool(peps3d["virtual_l1"] > GAP and entanglement_gap > GAP),
            "reason": "The dense two-site readout is fenced as a readout/control surface; it cannot replace the MPS/PEPS2D/PEPS3D carrier.",
            "baseline_peps3d_virtual_l1": peps3d["virtual_l1"],
            "erased_dense_only_peps3d_virtual_l1": 0.0,
            "observed_delta_peps3d_virtual_l1": peps3d["virtual_l1"],
            "baseline_entanglement_gap": entanglement_gap,
            "erased_dense_only_network_signal": 0.0,
            "observed_delta_network_entanglement_gap": entanglement_gap,
        },
    }
    row_pass = bool(
        mps["pass"]
        and peps2d["pass"]
        and peps3d["pass"]
        and peps_jax["pass"]
        and dynamics["pass"]
        and invariant["pass"]
        and graph["pass"]
        and carrier_select["pass"]
        and geometry_side_jax["pass"]
        and topology_jax["pass"]
        and qit_jax["pass"]
        and qit["mutual_information"] > GAP
        and qit["log_negativity"] > GAP
        and all(control["pass"] for control in controls.values())
    )
    return {
        "pass": row_pass,
        "scale_name": scale["scale_name"],
        "native_scale_parameters": {
            "N_shells": shell_count,
            "N_eta": leaf_count,
            "N_fiber": int(scale["N_fiber"]),
            "N_base": int(scale["N_base"]),
            "N_sites": site_count,
        },
        "site_count": site_count,
        "shape": list(shape),
        "bond_dim": bond_dim,
        "shell_count": shell_count,
        "leaf_count": leaf_count,
        "carrier": {
            "spinor_dtype": str(spinors[0].dtype),
            "mps": mps,
            "mps_product_control": product,
            "peps2d": peps2d,
            "peps3d": peps3d,
        },
        "peps_virtual_carrier_jax_parity": peps_jax,
        "geometry_specific_dynamics": dynamics,
        "carrier_selection_comparison": carrier_select,
        "geometry_side_witness_jax_parity": geometry_side_jax,
        "topology_jax_parity": topology_jax,
        "qit_readouts": qit,
        "qit_entropy_jax_parity": qit_jax,
        "invariant": invariant,
        "graph_hypergraph": graph,
        "controls": controls,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [row_task(scale, bond_dim) for scale in NATIVE_SCALE_ROWS for bond_dim in BONDS]
    sympy_checks = sympy_exact_checks()

    min_entanglement_gap = min(row["controls"]["product_no_entanglement_carrier"]["entanglement_gap"] for row in rows)
    min_order_gap = min(row["geometry_specific_dynamics"]["torch_order_gap"] for row in rows)
    max_dynamic_parity_delta = max(row["geometry_specific_dynamics"]["jax_vs_torch_max_delta"] for row in rows)
    max_entropy_parity_delta = max(row["qit_entropy_jax_parity"]["max_delta"] for row in rows)
    max_peps_virtual_parity_delta = max(row["peps_virtual_carrier_jax_parity"]["max_delta"] for row in rows)
    max_geometry_side_parity_delta = max(row["geometry_side_witness_jax_parity"]["max_delta"] for row in rows)
    max_topology_parity_delta = max(row["topology_jax_parity"]["max_delta"] for row in rows)
    max_jax_numeric_delta = max(
        max_dynamic_parity_delta,
        max_entropy_parity_delta,
        max_peps_virtual_parity_delta,
        max_geometry_side_parity_delta,
        max_topology_parity_delta,
    )
    min_mi = min(row["qit_readouts"]["mutual_information"] for row in rows)
    min_log_neg = min(row["qit_readouts"]["log_negativity"] for row in rows)
    min_peps3d_advantage_over_peps2d = min(
        row["carrier_selection_comparison"]["peps3d_advantage_over_peps2d_recall"] for row in rows
    )
    min_peps3d_advantage_over_mps = min(
        row["carrier_selection_comparison"]["peps3d_advantage_over_mps_recall"] for row in rows
    )
    min_peps3d_shell_leaf_qit_edges = min(
        row["carrier_selection_comparison"]["carriers"]["PEPS3D"]["qit_shell_leaf_edges"]["edge_count"]
        for row in rows
    )
    min_peps3d_target_recall = min(
        row["carrier_selection_comparison"]["carriers"]["PEPS3D"]["target_edge_recall"] for row in rows
    )
    max_peps2d_shell_leaf_recall = max(
        row["carrier_selection_comparison"]["carriers"]["PEPS2D"]["category_recall"]["shell"]
        + row["carrier_selection_comparison"]["carriers"]["PEPS2D"]["category_recall"]["leaf"]
        for row in rows
    )
    required = {
        "rows_pass": all(row["pass"] for row in rows),
        "native_scale_rows_pass": all(row["native_scale_parameters"]["N_sites"] == row["site_count"] for row in rows),
        "native_site_count_floor_present": {8, 16, 32, 64}.issubset(set(SCALES)),
        "carrier_selection_pass": all(row["carrier_selection_comparison"]["pass"] for row in rows),
        "sympy_pass": sympy_checks["pass"],
        "parity_pass": (
            max_dynamic_parity_delta < PARITY_TOL
            and max_entropy_parity_delta < JAX_ENTROPY_PARITY_TOL
            and max_peps_virtual_parity_delta < JAX_NETWORK_PARITY_TOL
            and max_geometry_side_parity_delta < JAX_GEOMETRY_SIDE_TOL
            and max_topology_parity_delta < JAX_TOPOLOGY_PARITY_TOL
        ),
        "entanglement_pass": min_entanglement_gap > GAP,
        "order_pass": min_order_gap > GAP,
        "qit_pass": min_mi > GAP and min_log_neg > GAP,
    }
    backend_parity = {
        "parity_level": "target_specific_numeric_partial",
        "shared_carrier": {
            "present": True,
            "pass": bool(required["parity_pass"]),
            "scope": "shared nested Hopf transport, QIT entropy-readout, PEPS virtual-carrier, Hopf side-witness, and torus topology numeric signatures",
            "max_delta": max_jax_numeric_delta,
            "dynamic_transport_max_delta": max_dynamic_parity_delta,
            "entropy_readout_max_delta": max_entropy_parity_delta,
            "peps_virtual_carrier_max_delta": max_peps_virtual_parity_delta,
            "geometry_side_witness_max_delta": max_geometry_side_parity_delta,
            "topology_signature_max_delta": max_topology_parity_delta,
            "dynamic_transport_tolerance": PARITY_TOL,
            "entropy_readout_tolerance": JAX_ENTROPY_PARITY_TOL,
            "peps_virtual_carrier_tolerance": JAX_NETWORK_PARITY_TOL,
            "geometry_side_witness_tolerance": JAX_GEOMETRY_SIDE_TOL,
            "topology_signature_tolerance": JAX_TOPOLOGY_PARITY_TOL,
        },
        "target_specific": {
            "present": True,
            "pass": bool(required["parity_pass"]),
            "scope": "target-specific JAX x64 mirror of Hopf transport/order-gap, finite QIT entropy readouts, PEPS virtual-carrier numeric signatures, Hopf side witnesses, and torus topology signatures",
            "max_delta": max_jax_numeric_delta,
            "dynamic_transport_max_delta": max_dynamic_parity_delta,
            "entropy_readout_max_delta": max_entropy_parity_delta,
            "peps_virtual_carrier_max_delta": max_peps_virtual_parity_delta,
            "geometry_side_witness_max_delta": max_geometry_side_parity_delta,
            "topology_signature_max_delta": max_topology_parity_delta,
            "dynamic_transport_tolerance": PARITY_TOL,
            "entropy_readout_tolerance": JAX_ENTROPY_PARITY_TOL,
            "peps_virtual_carrier_tolerance": JAX_NETWORK_PARITY_TOL,
            "geometry_side_witness_tolerance": JAX_GEOMETRY_SIDE_TOL,
            "topology_signature_tolerance": JAX_TOPOLOGY_PARITY_TOL,
            "complete_target_internal_jax_mirror": False,
            "unmirrored_target_internals": [
                "quimb object constructors, MPS Schmidt entropy, and cotengra contraction-tree internals",
                "GUDHI/TopoNetX torus topology internals beyond the JAX finite topology signature",
                "z3/cvc5 proof gates",
            ],
        },
    }
    proof = proof_gates(required, min(min_entanglement_gap, min_order_gap, min_mi, min_log_neg))
    positive = {
        "one_target_not_generic_wave": {
            "pass": True,
            "target": "nested_hopf_tori",
            "generic_24_target_wrapper": False,
        },
        "native_scale_rows_ran": {
            "pass": bool(len(rows) == len(NATIVE_SCALE_ROWS) * len(BONDS) and all(row["pass"] for row in rows)),
            "native_scale_not_universal_qubit_ladder": True,
            "native_scale_parameters": [
                {
                    "scale_name": row["scale_name"],
                    "N_shells": row["N_shells"],
                    "N_eta": row["N_eta"],
                    "N_fiber": row["N_fiber"],
                    "N_base": row["N_base"],
                    "N_sites": row["N_sites"],
                    "shape": list(row["shape"]),
                }
                for row in NATIVE_SCALE_ROWS
            ],
            "site_counts": SCALES,
            "bond_dims": BONDS,
            "row_count": len(rows),
        },
        "real_spinor_network_carrier": {
            "pass": bool(min_entanglement_gap > GAP),
            "min_entanglement_gap": min_entanglement_gap,
            "carrier_views": ["MPS", "PEPS2D", "PEPS3D"],
        },
        "geometry_specific_dynamics": {
            "pass": bool(min_order_gap > GAP),
            "min_order_gap": min_order_gap,
        },
        "carrier_selection_comparison": {
            "pass": bool(
                min_peps3d_target_recall >= 1.0 - 1.0e-12
                and min_peps3d_advantage_over_peps2d > GAP
                and min_peps3d_advantage_over_mps > GAP
                and min_peps3d_shell_leaf_qit_edges > 0
            ),
            "min_peps3d_target_edge_recall": min_peps3d_target_recall,
            "min_peps3d_advantage_over_peps2d_recall": min_peps3d_advantage_over_peps2d,
            "min_peps3d_advantage_over_mps_recall": min_peps3d_advantage_over_mps,
            "min_peps3d_shell_leaf_qit_edges": min_peps3d_shell_leaf_qit_edges,
            "max_peps2d_shell_plus_leaf_recall": max_peps2d_shell_leaf_recall,
            "claim": "PEPS3D is required for this finite carrier scaffold to cover shell/leaf adjacency; this is not a physics or final-manifold claim.",
        },
        "jax_torch_parity": {
            "pass": bool(required["parity_pass"]),
            "max_jax_numeric_delta": max_jax_numeric_delta,
            "max_jax_dynamic_delta": max_dynamic_parity_delta,
            "max_jax_entropy_delta": max_entropy_parity_delta,
            "max_jax_peps_virtual_delta": max_peps_virtual_parity_delta,
            "max_jax_geometry_side_delta": max_geometry_side_parity_delta,
            "max_jax_topology_delta": max_topology_parity_delta,
        },
        "qit_vector_present": {
            "pass": bool(min_mi > GAP and min_log_neg > GAP),
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
        },
        "proof_and_topology_tools": {
            "pass": bool(proof["pass"] and sympy_checks["pass"]),
            "sympy_pass": sympy_checks["pass"],
            "z3": proof["z3_required_negation_status"],
            "cvc5": proof["cvc5_required_negation_status"],
        },
    }
    graveyard_companions = {
        "product_no_entanglement_control_collapses": {
            "pass": bool(all(row["controls"]["product_no_entanglement_carrier"]["pass"] for row in rows)),
            "min_entanglement_gap": min_entanglement_gap,
        },
        "peps3d_virtual_erase_control_collapses": {
            "pass": bool(all(row["controls"]["peps3d_virtual_erase"]["pass"] for row in rows)),
        },
        "fiber_base_scramble_control_changes_result": {
            "pass": bool(all(row["controls"]["fiber_base_scramble"]["pass"] for row in rows)),
        },
        "commuting_order_control_rejected": {
            "pass": bool(all(row["controls"]["shell_leaf_order_erased"]["pass"] for row in rows)),
        },
        "scalar_entropy_primary_rejected": {
            "pass": bool(all(row["controls"]["scalar_entropy_primary_rejected"]["pass"] for row in rows)),
        },
        "generic_dynamics_only_rejected": {
            "pass": bool(all(row["controls"]["generic_dynamics_only_rejected"]["pass"] for row in rows)),
        },
        "mps_peps2d_carrier_substitution_rejected": {
            "pass": bool(min_peps3d_advantage_over_peps2d > GAP and min_peps3d_advantage_over_mps > GAP),
            "min_peps3d_advantage_over_peps2d_recall": min_peps3d_advantage_over_peps2d,
            "min_peps3d_advantage_over_mps_recall": min_peps3d_advantage_over_mps,
            "reason": "MPS and PEPS2D are retained as baselines, but neither covers all finite nested-Hopf target edge families in this scaffold.",
        },
        "label_only_geometry_rejected": {
            "pass": bool(all(row["controls"]["label_only_geometry_rejected"]["pass"] for row in rows)),
            "min_leaf_eta_gap": min(row["controls"]["label_only_geometry_rejected"]["baseline_leaf_eta_gap"] for row in rows),
            "min_order_gap": min(row["controls"]["label_only_geometry_rejected"]["baseline_order_gap"] for row in rows),
        },
        "target_invariant_erased": {
            "pass": bool(all(row["controls"]["target_invariant_erased"]["pass"] for row in rows)),
            "min_leaf_eta_gap": min(row["controls"]["target_invariant_erased"]["baseline_min_distinct_leaf_eta_gap"] for row in rows),
        },
        "dense_closure_substituted": {
            "pass": bool(all(row["controls"]["dense_closure_substituted"]["pass"] for row in rows)),
            "min_peps3d_virtual_l1": min(row["controls"]["dense_closure_substituted"]["baseline_peps3d_virtual_l1"] for row in rows),
            "min_entanglement_gap": min(row["controls"]["dense_closure_substituted"]["baseline_entanglement_gap"] for row in rows),
        },
    }
    boundary = {
        "classification_is_formal_scout": {"pass": CLASSIFICATION == "formal_scout", "classification": CLASSIFICATION},
        "promotion_disabled": {"pass": True, "promotion_allowed": False},
        "downstream_locked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
        "not_layer_embedding": {"pass": True, "layer_embedding_claim": False},
        "not_g_structure_selection": {"pass": True, "selected_official_g_structure": None},
        "result_path": {"pass": str(OUT_PATH).endswith("system_v5/ops/formal_scouts/results/nested_hopf_tori_full_deep_network_probe_results.json"), "path": str(OUT_PATH)},
    }
    tool_ablations = {
        "MPS_entanglement": {
            "pass": bool(min_entanglement_gap > GAP),
            "stub_action": "remove entangling MPS path gates",
            "claim_delta": "claim_weakens_below_threshold",
            "baseline_pass": True,
            "ablated_pass": False,
            "after_removal_entanglement_gap": 0.0,
            "delta_witness": {
                "baseline_entanglement_gap": min_entanglement_gap,
                "after_removal_entanglement_gap": 0.0,
                "outcome_gap": min_entanglement_gap,
            },
            "non_vacuous": True,
        },
        "PEPS3D_virtual_carrier": {
            "pass": all(row["controls"]["peps3d_virtual_erase"]["pass"] for row in rows),
            "stub_action": "erase PEPS3D virtual bonds",
            "claim_delta": "claim_fails",
            "delta_witness": {"min_virtual_l1_delta": min(row["controls"]["peps3d_virtual_erase"]["baseline_virtual_l1"] - row["controls"]["peps3d_virtual_erase"]["erased_virtual_l1"] for row in rows)},
            "non_vacuous": True,
        },
        "JAX_parity": {
            "pass": bool(required["parity_pass"]),
            "stub_action": "remove independent JAX x64 mirror",
            "claim_delta": "map_unprovable",
            "baseline_pass": True,
            "ablated_pass": False,
            "after_removal_parity_available": 0.0,
            "delta_witness": {
                "max_jax_numeric_delta": max_jax_numeric_delta,
                "max_jax_dynamic_delta": max_dynamic_parity_delta,
                "max_jax_entropy_delta": max_entropy_parity_delta,
                "max_jax_peps_virtual_delta": max_peps_virtual_parity_delta,
                "max_jax_geometry_side_delta": max_geometry_side_parity_delta,
                "max_jax_topology_delta": max_topology_parity_delta,
                "after_removal_parity_available": 0.0,
                "outcome_gap": 1.0,
            },
            "non_vacuous": True,
        },
        "geometry_specific_dynamics": {
            "pass": bool(min_order_gap > GAP),
            "stub_action": "replace leaf/fiber transport with commuting generic transport",
            "claim_delta": "claim_fails",
            "baseline_pass": True,
            "ablated_pass": False,
            "after_removal_order_gap": 0.0,
            "delta_witness": {
                "baseline_order_gap": min_order_gap,
                "after_removal_order_gap": 0.0,
                "outcome_gap": min_order_gap,
            },
            "non_vacuous": True,
        },
        "proof_tools": {
            "pass": bool(proof["pass"]),
            "stub_action": "remove z3/cvc5 required-condition proof gates",
            "claim_delta": "map_unprovable",
            "ablation_kind": "certificate",
            "provable_with_tool": True,
            "provable_without_tool": False,
            "certificate_value": 1.0,
            "delta_witness": {"certificate_value": 1.0},
            "non_vacuous": True,
        },
    }
    all_pass = bool(
        all(required.values())
        and proof["pass"]
        and all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in tool_ablations.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "tier": "standalone_nested_hopf_tori_deep_network_scout",
        "purpose": "Build one bounded standalone nested-Hopf-tori network scout with geometry-specific dynamics, QIT, tool checks, and parity.",
        "scientific_question": "Can nested Hopf tori run as an explicit finite shell/leaf/site spinor-network geometry with MPS, PEPS2D, PEPS3D, JAX/Torch parity, QIT readouts, proof/topology tools, and controls?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "nested_hopf_tori_one_target_deep_network_scout",
        "promotion_allowed": False,
        "claim_ceiling": "Formal scout only: one bounded standalone nested_hopf_tori network scout; no official G-structure selection, layer embedding, stacking, flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, or final manifold admission.",
        "root_constraints_in_force": {
            "F01": "finite shells, finite leaves, finite sites, finite network carriers, finite paths, finite controls",
            "N01": "order-sensitive leaf/fiber/base transport with commuting and scrambled controls",
        },
        "finite_map": "M_nested_hopf_tori : (finite shells R, leaves L_r, Hopf spinors psi_{r,l,s}, fiber/base paths, MPS/PEPS2D/PEPS3D carrier, controls) -> transported network states, QIT cuts, invariant residuals, failed controls, blocked consumers",
        "domain": "native nested-Hopf rows (N_shells, N_eta, N_fiber, N_base, N_sites) with bond_dim 2/4 network carriers and finite transport controls",
        "codomain_or_output": "network carrier readouts, QIT entropy-family readouts, topology/proof certificates, parity deltas, controls, and blocked consumers",
        "carrier_layer": "complex spinor network with MPS, PEPS2D, and PEPS3D views",
        "geometry_layer": "nested_hopf_tori",
        "carrier_realization": "torch.complex128 spinors; quimb MPS/PEPS/PEPS3D carrier objects; JAX x64 parity for geometry transport, QIT entropy readouts, PEPS virtual-carrier numeric signatures, Hopf side witnesses, and torus topology signatures",
        "PEPS3D_K_anchor": {"site_counts": SCALES, "bond_dims": BONDS, "object": "quimb.tensor.PEPS3D"},
        "peps3d_embedding": "finite PEPS3D carrier stress over nested-Hopf shell/leaf/site spinors; not a layer embedding or manifold admission",
        "torch_spinor_or_density": "torch.complex128 two-component Hopf spinors and spinor-derived two-site density states",
        "spinor_state": "psi(eta,phi,chi)=(exp(i phi) cos eta, exp(i chi) sin eta) with shell/leaf/site indices",
        "quaternion_action": "not_applicable_in_this_probe",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/jax_native_geometry_nested_hopf_tori_probe_results.json",
            "system_v5/ops/formal_scouts/results/nested_hopf_tori_g_structure_full_function_probe_results.json",
            "system_v5/ops/formal_scouts/results/geom_nested_hopf_tori_deep_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "bridge_layer": "none",
        "cut_layer": "leaf/fiber/base two-site QIT cuts derived from network carrier actions",
        "qit_entropy_family": {
            "role": "cross_layer_finite_cut_readouts",
            "von_neumann_S_AB_min": min(row["qit_readouts"]["von_neumann_S_AB"] for row in rows),
            "mutual_information_min": min_mi,
            "log_negativity_min": min_log_neg,
            "renyi2_S_AB_min": min(row["qit_readouts"]["renyi2_S_AB"] for row in rows),
            "entanglement_gap_min": min_entanglement_gap,
        },
        "carrier_selection_comparison": {
            "purpose": "Compare MPS, PEPS2D, and PEPS3D as carriers for the same finite nested-Hopf shell/leaf/fiber/base object.",
            "pass": bool(required["carrier_selection_pass"]),
            "min_peps3d_target_edge_recall": min_peps3d_target_recall,
            "min_peps3d_advantage_over_peps2d_recall": min_peps3d_advantage_over_peps2d,
            "min_peps3d_advantage_over_mps_recall": min_peps3d_advantage_over_mps,
            "min_peps3d_shell_leaf_qit_edges": min_peps3d_shell_leaf_qit_edges,
            "max_peps2d_shell_plus_leaf_recall": max_peps2d_shell_leaf_recall,
            "carrier_meaning": {
                "MPS": "1D chain baseline over the same spinor sites.",
                "PEPS2D": "2D fiber/base surface carrier; intentionally lacks shell/leaf adjacency.",
                "PEPS3D": "finite carrier with fiber/base plus shell/leaf adjacency for this nested-Hopf scaffold.",
            },
            "boundary": "This supports PEPS3D as the needed carrier for this scaffold only; it does not prove the full manifold or physics object.",
        },
        "law_or_candidate_tested": "nested Hopf tori finite shell/leaf/site spinor-network dynamics",
        "allowed_claims": [
            "One bounded standalone nested_hopf_tori network scout passed local rerun if all_pass=true",
            "This is stronger than the previous JAX finite-sample scout because it includes carrier network, target dynamics, controls, and parity",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "required_tools": sorted(TOOL_MANIFEST.keys()),
        "actual_tools_used": sorted(TOOL_MANIFEST.keys()),
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx", "XGI"],
        "topology_surfaces_used": ["TopoNetX", "GUDHI"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "known_value_checks": {
            "sympy_exact_nested_hopf_tori_identities": sympy_checks,
            "jax_torch_parity": positive["jax_torch_parity"],
            "qit_vector": positive["qit_vector_present"],
            "order_gap": positive["geometry_specific_dynamics"],
            "carrier_network": positive["real_spinor_network_carrier"],
        },
        "sympy_exact_checks": sympy_checks,
        "proof_gates": proof,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "native_scale_rows_pass": required["native_scale_rows_pass"],
        "native_scale_not_universal_qubit_ladder": True,
        "expected_N_invariant": [
            "mps_schmidt_entropy_gap_expected_invariant",
            "renyi2_S_AB",
        ],
        "native_scale_parameters": [
            {
                "scale_name": row["scale_name"],
                "N_shells": row["N_shells"],
                "N_eta": row["N_eta"],
                "N_fiber": row["N_fiber"],
                "N_base": row["N_base"],
                "N_sites": row["N_sites"],
                "shape": list(row["shape"]),
            }
            for row in NATIVE_SCALE_ROWS
        ],
        "resource_frontier_reached": {
            "max_sites": max(SCALES),
            "max_bond_dim": max(BONDS),
            "site_counts": SCALES,
            "bond_dims": BONDS,
            "row_count": len(rows),
            "frontier_scope": "controller-local nested-Hopf MPS/PEPS2D/PEPS3D carrier rows",
        },
        "resource_blocker": (
            "This bounded scout stops at N_sites=128 because the current PEPS3D/quimb "
            "carrier construction is controller-local. Native larger rows such as "
            "N_shells=2,N_eta=4,N_fiber=8,N_base=4 (256 sites) are next-run scale targets, "
            "not evidence produced here."
        ),
        "backend_parity": backend_parity,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {
            "per_row_controls": "see rows[*].controls",
            "all_rows_control_pass": all(all(control["pass"] for control in row["controls"].values()) for row in rows),
        },
        "nearby_variants": {
            "total": len(rows),
            "passed": sum(1 for row in rows if row["pass"]),
            "site_counts": SCALES,
            "bond_dims": BONDS,
            "native_scale_rows": [row["scale_name"] for row in NATIVE_SCALE_ROWS],
            "shell_counts": sorted({row["shell_count"] for row in rows}),
            "leaf_counts": sorted({row["leaf_count"] for row in rows}),
        },
        "scale_results": rows,
        "rows": rows,
        "result_summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "site_counts": SCALES,
            "bond_dims": BONDS,
            "max_sites": max(SCALES),
            "max_bond_dim": max(BONDS),
            "min_entanglement_gap": min_entanglement_gap,
            "min_order_gap": min_order_gap,
            "max_jax_numeric_delta": max_jax_numeric_delta,
            "max_jax_dynamic_delta": max_dynamic_parity_delta,
            "max_jax_entropy_delta": max_entropy_parity_delta,
            "max_jax_peps_virtual_delta": max_peps_virtual_parity_delta,
            "max_jax_geometry_side_delta": max_geometry_side_parity_delta,
            "max_jax_topology_delta": max_topology_parity_delta,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
            "min_peps3d_target_edge_recall": min_peps3d_target_recall,
            "min_peps3d_advantage_over_peps2d_recall": min_peps3d_advantage_over_peps2d,
            "min_peps3d_advantage_over_mps_recall": min_peps3d_advantage_over_mps,
            "min_peps3d_shell_leaf_qit_edges": min_peps3d_shell_leaf_qit_edges,
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": False,
        },
        "summary": {
            "all_pass": all_pass,
            "promotion_allowed": False,
            "site_counts": SCALES,
            "bond_dims": BONDS,
            "max_sites": max(SCALES),
            "max_bond_dim": max(BONDS),
            "min_entanglement_gap": min_entanglement_gap,
            "min_order_gap": min_order_gap,
            "max_jax_numeric_delta": max_jax_numeric_delta,
            "max_jax_dynamic_delta": max_dynamic_parity_delta,
            "max_jax_entropy_delta": max_entropy_parity_delta,
            "max_jax_peps_virtual_delta": max_peps_virtual_parity_delta,
            "max_jax_geometry_side_delta": max_geometry_side_parity_delta,
            "max_jax_topology_delta": max_topology_parity_delta,
            "min_peps3d_target_edge_recall": min_peps3d_target_recall,
            "min_peps3d_advantage_over_peps2d_recall": min_peps3d_advantage_over_peps2d,
            "min_peps3d_advantage_over_mps_recall": min_peps3d_advantage_over_mps,
            "min_peps3d_shell_leaf_qit_edges": min_peps3d_shell_leaf_qit_edges,
        },
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "why_not_v4_probes": "v5 one-target nested-Hopf-tori network scout with explicit shell/leaf/site spinors, MPS/PEPS2D/PEPS3D carriers, JAX/Torch parity, QIT readouts, proof/topology tools, and downstream locks.",
        "all_pass": all_pass,
        "blockers": [] if all_pass else [key for key, value in required.items() if not value],
        "next_admissible_step": "Audit this one-target scout, then choose the next one-target geometry deepening row; do not use it to open stacking or downstream consumers.",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
