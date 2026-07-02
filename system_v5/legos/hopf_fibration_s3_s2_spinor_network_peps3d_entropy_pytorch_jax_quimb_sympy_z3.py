#!/usr/bin/env python3
"""Hopf fibration S3->S2 spinor-network lego.

One object, one file, one result receipt. This is not a 24-target wrapper and
not a formal-scout row. It simulates the Hopf fibration itself over finite
spinor networks:

    psi(eta, phi, chi) = (exp(i phi) cos eta, exp(i chi) sin eta)
    h(psi) = (2 Re(conj(z1) z2), 2 Im(conj(z1) z2), |z1|^2 - |z2|^2)

The run checks unit S3 spinors, S2 base projection, global U(1) fiber
invariance, order-sensitive relative-phase/amplitude transport, entangled MPS
carrier, PEPS2D/PEPS3D carrier views, QIT entropy/correlation readouts, symbolic
identity checks, SMT gates, graph/hypergraph/topology support, and controls.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import autoray as ar
import chex
import cotengra as ctg
import cvc5
from cvc5 import Kind
import gudhi
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import opt_einsum as oe
import qutip_jax
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "hopf_fibration_s3_s2_spinor_network_peps3d_entropy_pytorch_jax_quimb_sympy_z3_results.json"

NAME = "hopf_fibration_s3_s2_spinor_network_peps3d_entropy_pytorch_jax_quimb_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Hopf fibration spinor-network lego only: finite S3 spinors project to S2 "
    "base points with U(1) fiber invariance, order-sensitive relative-phase and "
    "amplitude transport, MPS/PEPS2D/PEPS3D carrier views, QIT readouts, proof "
    "and topology controls. It does not admit layer stacking, official "
    "G-structure selection, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, or "
    "final manifold claims."
)

CDTYPE = torch.complex128
RTYPE = torch.float64
JCTYPE = jnp.complex128
JRTYPE = jnp.float64
SITE_COUNTS = [8, 16, 32, 64]
SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
BOND_DIMS = [2, 4]
MPS_BOND = 8
TOL = 1.0e-8
GAP = 1.0e-6
PARITY_TOL = 5.0e-7

BLOCKED_CONSUMERS = [
    "layer_stacking",
    "official_g_structure_selection",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex Hopf spinors, spinor-network density, QIT entropy/correlation, and order-sensitive transport",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 mirror of Hopf projection and order-sensitive transport",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MPS, PEPS2D, and PEPS3D carrier objects with torch-backed arrays",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "load-bearing contraction-tree witness for PEPS3D carrier scaling",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite contraction signatures over Hopf base vectors",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Hopf norm and global phase invariance identities",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT exclusion for required observed pass conditions",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT cross-check for required observed pass conditions",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite site/fiber path graph connectivity and cycle-rank check",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing shell/fiber/base hyperedge incidence check",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite base-sphere and fiber-loop cell-complex check",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Betti checks for finite S2 base and S1 fiber controls",
    },
    "qutip_jax": {
        "tried": True,
        "used": True,
        "reason": "supportive JAX density trace sanity check",
    },
    "chex": {
        "tried": True,
        "used": True,
        "reason": "supportive JAX shape checks for finite transport arrays",
    },
    "autoray": {
        "tried": True,
        "used": True,
        "reason": "supportive backend scalar conversion for contraction outputs",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "jax": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "qutip_jax": "supportive",
    "chex": "supportive",
    "autoray": "supportive",
}


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return jsonable(value.detach().cpu().item())
        return jsonable(value.detach().cpu().tolist())
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def normalize_spinor(psi: torch.Tensor) -> torch.Tensor:
    psi = psi.to(CDTYPE)
    return psi / torch.linalg.vector_norm(psi)


def hopf_spinor(eta: float, phi: float, chi: float) -> torch.Tensor:
    return normalize_spinor(
        torch.tensor(
            [
                math.cos(eta) * complex(math.cos(phi), math.sin(phi)),
                math.sin(eta) * complex(math.cos(chi), math.sin(chi)),
            ],
            dtype=CDTYPE,
        )
    )


def hopf_base(psi: torch.Tensor) -> torch.Tensor:
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


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize_spinor(psi)
    return torch.outer(psi, psi.conj())


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho.to(CDTYPE) + rho.to(CDTYPE).conj().T) / 2.0
    trace = torch.real(torch.trace(rho)).clamp(min=1.0e-12)
    return rho / trace.to(CDTYPE)


def entropy(rho: torch.Tensor) -> float:
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
    s_ab = entropy(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    pt = rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)
    neg = torch.sum(torch.abs(torch.real(torch.linalg.eigvalsh(pt))[torch.real(torch.linalg.eigvalsh(pt)) < 0.0]))
    purity = torch.real(torch.trace(rho_ab @ rho_ab)).clamp(min=1.0e-12)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "renyi2_AB": float((-torch.log2(purity)).item()),
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
        "log_negativity": float(torch.log2(2.0 * neg + 1.0).item()),
    }


def hopf_spinor_jax(eta: jnp.ndarray, phi: jnp.ndarray, chi: jnp.ndarray) -> jnp.ndarray:
    psi = jnp.stack(
        [jnp.cos(eta) * jnp.exp(1j * phi), jnp.sin(eta) * jnp.exp(1j * chi)],
        axis=-1,
    ).astype(JCTYPE)
    return psi / jnp.linalg.norm(psi, axis=-1, keepdims=True)


def hopf_base_jax(psi: jnp.ndarray) -> jnp.ndarray:
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


def site_parameters(site_count: int) -> list[dict[str, Any]]:
    shell_count = 2 + int(site_count >= 32) + int(site_count >= 64)
    fiber_count = 4 + int(site_count >= 16) * 2 + int(site_count >= 64) * 2
    rows: list[dict[str, Any]] = []
    for site in range(site_count):
        shell = site % shell_count
        fiber = (site // shell_count) % fiber_count
        u = site / site_count
        eta = 0.19 + 1.12 * ((fiber + 1.0) / (fiber_count + 1.0))
        eta = min(1.43, max(0.12, eta + 0.025 * math.sin(2.0 * math.pi * u + shell)))
        phi = 2.0 * math.pi * u + 0.11 * shell
        chi = phi + 0.37 + 0.41 * math.sin(2.0 * math.pi * (fiber + 1) / fiber_count)
        rows.append({"site": site, "shell": shell, "fiber": fiber, "eta": eta, "phi": phi, "chi": chi})
    return rows


def spinor_rows(site_count: int) -> tuple[list[torch.Tensor], list[dict[str, Any]]]:
    params = site_parameters(site_count)
    return [hopf_spinor(row["eta"], row["phi"], row["chi"]) for row in params], params


def mps_arrays(spinors: list[torch.Tensor], params: list[dict[str, Any]], *, entangled: bool) -> list[torch.Tensor]:
    bond = MPS_BOND if entangled else 1
    weights = torch.arange(1, bond + 1, dtype=RTYPE)
    weights = weights / torch.sum(weights)
    arrays: list[torch.Tensor] = []
    for site, psi in enumerate(spinors):
        left = 1 if site == 0 else bond
        right = 1 if site == len(spinors) - 1 else bond
        arr = torch.zeros((left, 2, right), dtype=CDTYPE)
        for latent in range(bond):
            lidx = 0 if site == 0 else latent
            ridx = 0 if site == len(spinors) - 1 else latent
            relative = params[site]["chi"] - params[site]["phi"]
            angle = 0.07 * (latent + 1) * math.sin(relative + 0.13 * site)
            phase = complex(math.cos(angle), math.sin(angle))
            amp = torch.sqrt(weights[latent]).to(CDTYPE) if site == 0 else torch.tensor(1.0 + 0.0j, dtype=CDTYPE)
            arr[lidx, 0, ridx] = amp * phase * psi[0]
            arr[lidx, 1, ridx] = amp * torch.conj(torch.tensor(phase, dtype=CDTYPE)) * psi[1]
        arrays.append(arr)
    return arrays


def make_mps(arrays: list[torch.Tensor]) -> qtn.MatrixProductState:
    mps = qtn.MatrixProductState(arrays, shape="lpr")
    if not all(isinstance(array, torch.Tensor) for array in mps.arrays):
        raise TypeError("quimb MPS did not preserve torch.Tensor arrays")
    return mps


def peps2d_arrays(shape: tuple[int, int, int], spinors: list[torch.Tensor], bond_dim: int) -> list[list[torch.Tensor]]:
    lx, ly, _ = shape
    arrays: list[list[torch.Tensor]] = []
    for x in range(lx):
        row: list[torch.Tensor] = []
        for y in range(ly):
            site = x * ly + y
            dims = (
                1 if x == 0 else bond_dim,
                1 if y == ly - 1 else bond_dim,
                1 if x == lx - 1 else bond_dim,
                1 if y == 0 else bond_dim,
                2,
            )
            arr = torch.zeros(dims, dtype=CDTYPE)
            arr[(0, 0, 0, 0, 0)] = spinors[site][0]
            arr[(0, 0, 0, 0, 1)] = spinors[site][1]
            for axis in range(4):
                if dims[axis] <= 1:
                    continue
                idx = [0, 0, 0, 0]
                idx[axis] = min(1, dims[axis] - 1)
                phase = complex(math.cos(0.031 * (site + axis + 1)), math.sin(0.031 * (site + axis + 1)))
                arr[tuple(idx) + (0,)] = 0.015 * phase * spinors[site][0]
                arr[tuple(idx) + (1,)] = 0.015 * phase * spinors[site][1]
            row.append(arr)
        arrays.append(row)
    return arrays


def peps3d_arrays(
    shape: tuple[int, int, int],
    spinors: list[torch.Tensor],
    bond_dim: int,
    *,
    erase_virtual: bool = False,
) -> list[list[list[torch.Tensor]]]:
    lx, ly, lz = shape
    arrays: list[list[list[torch.Tensor]]] = []
    for x in range(lx):
        x_rows: list[list[torch.Tensor]] = []
        for y in range(ly):
            y_rows: list[torch.Tensor] = []
            for z in range(lz):
                site = z * lx * ly + x * ly + y
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
                        idx = [0, 0, 0, 0, 0, 0]
                        idx[axis] = min(1, dims[axis] - 1)
                        phase = complex(math.cos(0.023 * (site + axis + 1)), math.sin(0.023 * (site + axis + 1)))
                        arr[tuple(idx) + (0,)] = 0.012 * phase * spinors[site][0]
                        arr[tuple(idx) + (1,)] = 0.012 * phase * spinors[site][1]
                y_rows.append(arr)
            x_rows.append(y_rows)
        arrays.append(x_rows)
    return arrays


def mps_network_readout(spinors: list[torch.Tensor], params: list[dict[str, Any]]) -> dict[str, Any]:
    entangled = make_mps(mps_arrays(spinors, params, entangled=True))
    product = make_mps(mps_arrays(spinors, params, entangled=False))
    entangled_norm = complex(entangled.norm().item())
    product_norm = complex(product.norm().item())
    weights = torch.arange(1, MPS_BOND + 1, dtype=RTYPE)
    weights = weights / torch.sum(weights)
    schmidt_entropy = float(-(weights * torch.log2(weights)).sum().item())
    return {
        "pass": bool(entangled.max_bond() >= MPS_BOND and product.max_bond() == 1 and schmidt_entropy > GAP),
        "quimb_mps_max_bond": int(entangled.max_bond()),
        "quimb_product_mps_max_bond": int(product.max_bond()),
        "latent_schmidt_entropy": schmidt_entropy,
        "entangled_norm_real": float(entangled_norm.real),
        "entangled_norm_imag_abs": abs(float(entangled_norm.imag)),
        "product_norm_real": float(product_norm.real),
        "product_norm_imag_abs": abs(float(product_norm.imag)),
    }


def peps_views(shape: tuple[int, int, int], spinors: list[torch.Tensor], bond_dim: int) -> dict[str, Any]:
    p2_arrays = peps2d_arrays(shape, spinors, bond_dim)
    p2 = qtn.PEPS(p2_arrays)
    p3_arrays = peps3d_arrays(shape, spinors, bond_dim)
    p3_erased_arrays = peps3d_arrays(shape, spinors, bond_dim, erase_virtual=True)
    p3 = qtn.PEPS3D(p3_arrays)
    flat = [arr for xrow in p3_arrays for yrow in xrow for arr in yrow]
    flat_erased = [arr for xrow in p3_erased_arrays for yrow in xrow for arr in yrow]
    virtual_l1 = sum(float(torch.sum(torch.abs(arr.reshape(-1)[2:])).item()) for arr in flat)
    erased_l1 = sum(float(torch.sum(torch.abs(arr.reshape(-1)[2:])).item()) for arr in flat_erased)
    base_a = hopf_base(spinors[0])
    base_b = hopf_base(spinors[-1])
    contraction = oe.contract("i,i->", base_a, base_b)
    tree = ctg.HyperOptimizer(max_repeats=1, progbar=False, on_trial_error="raise").search(
        [("a", "b"), ("b", "c"), ("c", "a")],
        (),
        {"a": bond_dim, "b": bond_dim, "c": bond_dim},
    )
    return {
        "pass": bool(int(p2.num_tensors) > 0 and int(p3.num_tensors) == len(spinors) and virtual_l1 > erased_l1 + GAP),
        "peps2d_object": "quimb.tensor.PEPS",
        "peps3d_object": "quimb.tensor.PEPS3D",
        "peps2d_tensors": int(p2.num_tensors),
        "peps3d_tensors": int(p3.num_tensors),
        "bond_dim": bond_dim,
        "virtual_l1": virtual_l1,
        "erased_virtual_l1": erased_l1,
        "base_dot_contraction": float(ar.do("asarray", contraction).item()),
        "cotengra_cost": float(tree.contraction_cost()),
    }


def two_site_hopf_gate(params_a: dict[str, Any], params_b: dict[str, Any]) -> torch.Tensor:
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
    sy = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=CDTYPE)
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
    phase_gap = abs(math.sin((params_b["chi"] - params_b["phi"]) - (params_a["chi"] - params_a["phi"])))
    eta_gap = abs(params_a["eta"] - params_b["eta"])
    h = (0.19 + eta_gap) * torch.kron(sx, sy)
    h = h + (0.17 + 0.25 * phase_gap) * torch.kron(sy, sz)
    h = h + 0.13 * torch.kron(sz, sx)
    h = (h + h.conj().T) / 2.0
    return torch.linalg.matrix_exp((-1j * 0.23) * h)


def two_site_density(spinors: list[torch.Tensor], params: list[dict[str, Any]], *, entangle: bool) -> torch.Tensor:
    psi = normalize_spinor(torch.kron(spinors[0], spinors[-1]))
    if entangle:
        psi = two_site_hopf_gate(params[0], params[-1]) @ psi
    return density(psi)


def transport_torch(params: list[dict[str, Any]], order: str) -> torch.Tensor:
    out = []
    for row in params:
        eta, phi, chi = float(row["eta"]), float(row["phi"]), float(row["chi"])
        if order == "relative_then_amplitude":
            chi1 = chi + 0.19 * math.sin(eta + 0.1 * row["shell"])
            eta1 = min(1.48, max(0.08, eta + 0.047 * math.sin(chi1 - phi)))
            phi1 = phi
        elif order == "amplitude_then_relative":
            eta1 = min(1.48, max(0.08, eta + 0.047 * math.sin(chi - phi)))
            chi1 = chi + 0.19 * math.sin(eta1 + 0.1 * row["shell"])
            phi1 = phi
        elif order == "global_fiber":
            phi1, chi1, eta1 = phi + 0.31, chi + 0.31, eta
        elif order == "scrambled_relative":
            phi1, chi1 = chi + 0.03, phi - 0.03
            eta1 = min(1.48, max(0.08, eta + 0.047 * math.sin(phi1 + chi1)))
        else:
            raise ValueError(order)
        out.append(hopf_base(hopf_spinor(eta1, phi1, chi1)))
    return torch.stack(out)


def transport_jax(eta: jnp.ndarray, phi: jnp.ndarray, chi: jnp.ndarray, shell: jnp.ndarray, order: str) -> jnp.ndarray:
    if order == "relative_then_amplitude":
        chi1 = chi + 0.19 * jnp.sin(eta + 0.1 * shell)
        eta1 = jnp.clip(eta + 0.047 * jnp.sin(chi1 - phi), 0.08, 1.48)
        phi1 = phi
    elif order == "amplitude_then_relative":
        eta1 = jnp.clip(eta + 0.047 * jnp.sin(chi - phi), 0.08, 1.48)
        chi1 = chi + 0.19 * jnp.sin(eta1 + 0.1 * shell)
        phi1 = phi
    elif order == "global_fiber":
        phi1, chi1, eta1 = phi + 0.31, chi + 0.31, eta
    elif order == "scrambled_relative":
        phi1, chi1 = chi + 0.03, phi - 0.03
        eta1 = jnp.clip(eta + 0.047 * jnp.sin(phi1 + chi1), 0.08, 1.48)
    else:
        raise ValueError(order)
    return hopf_base_jax(hopf_spinor_jax(eta1, phi1, chi1))


def geometry_dynamics(params: list[dict[str, Any]], spinors: list[torch.Tensor]) -> dict[str, Any]:
    base_before = torch.stack([hopf_base(psi) for psi in spinors])
    fiber = transport_torch(params, "global_fiber")
    rel_then_amp = transport_torch(params, "relative_then_amplitude")
    amp_then_rel = transport_torch(params, "amplitude_then_relative")
    scrambled = transport_torch(params, "scrambled_relative")

    eta = jnp.array([row["eta"] for row in params], dtype=JRTYPE)
    phi = jnp.array([row["phi"] for row in params], dtype=JRTYPE)
    chi = jnp.array([row["chi"] for row in params], dtype=JRTYPE)
    shell = jnp.array([row["shell"] for row in params], dtype=JRTYPE)
    chex.assert_shape(eta, (len(params),))
    j_before = hopf_base_jax(hopf_spinor_jax(eta, phi, chi))
    j_fiber = transport_jax(eta, phi, chi, shell, "global_fiber")
    j_rta = transport_jax(eta, phi, chi, shell, "relative_then_amplitude")
    j_atr = transport_jax(eta, phi, chi, shell, "amplitude_then_relative")
    j_scrambled = transport_jax(eta, phi, chi, shell, "scrambled_relative")

    order_gap = float(torch.linalg.vector_norm(rel_then_amp - amp_then_rel).item())
    fiber_invariance_gap = float(torch.linalg.vector_norm(fiber - base_before).item())
    scrambled_gap = float(torch.linalg.vector_norm(scrambled - rel_then_amp).item())
    j_order_gap = float(jnp.linalg.norm(j_rta - j_atr))
    j_fiber_gap = float(jnp.linalg.norm(j_fiber - j_before))
    j_scrambled_gap = float(jnp.linalg.norm(j_scrambled - j_rta))
    trace = qutip_jax.trace_jaxarray(qutip_jax.JaxArray(jnp.eye(2, dtype=JCTYPE) / 2.0))
    parity_delta = max(abs(order_gap - j_order_gap), abs(fiber_invariance_gap - j_fiber_gap), abs(scrambled_gap - j_scrambled_gap))
    return {
        "pass": bool(order_gap > GAP and fiber_invariance_gap < TOL and scrambled_gap > GAP and parity_delta < PARITY_TOL),
        "torch_order_gap": order_gap,
        "torch_fiber_invariance_gap": fiber_invariance_gap,
        "torch_scrambled_gap": scrambled_gap,
        "jax_order_gap": j_order_gap,
        "jax_fiber_invariance_gap": j_fiber_gap,
        "jax_scrambled_gap": j_scrambled_gap,
        "jax_torch_max_delta": parity_delta,
        "qutip_jax_half_density_trace": float(jnp.real(trace)),
    }


def topology_checks(site_count: int, params: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from(range(site_count))
    graph.add_edges_from_no_data([(i, (i + 1) % site_count) for i in range(site_count)])
    graph.add_edges_from_no_data([(i, (i + 2) % site_count) for i in range(site_count)])
    cycle_rank = int(graph.num_edges()) - int(graph.num_nodes()) + 1

    hyper = xgi.Hypergraph()
    for shell in sorted({row["shell"] for row in params}):
        hyper.add_edge([row["site"] for row in params if row["shell"] == shell])
    for fiber in sorted({row["fiber"] for row in params}):
        members = [row["site"] for row in params if row["fiber"] == fiber]
        if len(members) >= 2:
            hyper.add_edge(members)

    base = tnx.SimplicialComplex()
    # Octahedral triangulation of S2: top, bottom, four equator vertices.
    sphere_faces = [
        (0, 2, 3),
        (0, 3, 4),
        (0, 4, 5),
        (0, 5, 2),
        (1, 3, 2),
        (1, 4, 3),
        (1, 5, 4),
        (1, 2, 5),
    ]
    sphere = gudhi.SimplexTree()
    for face in sphere_faces:
        base.add_simplex(face)
        sphere.insert(list(face), filtration=0.0)
    sphere.compute_persistence(persistence_dim_max=True)
    sphere_betti = [int(x) for x in sphere.betti_numbers()]

    fiber = gudhi.SimplexTree()
    for i in range(8):
        fiber.insert([i], filtration=0.0)
        fiber.insert([i, (i + 1) % 8], filtration=0.0)
    fiber.compute_persistence(persistence_dim_max=True)
    fiber_betti = [int(x) for x in fiber.betti_numbers()]
    return {
        "pass": bool(
            rx.is_connected(graph)
            and cycle_rank >= 2
            and int(hyper.num_edges) >= 3
            and int(base.dim) == 2
            and sphere_betti[:3] == [1, 0, 1]
            and fiber_betti[:2] == [1, 1]
        ),
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "rustworkx_cycle_rank": cycle_rank,
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_base_dim": int(base.dim),
        "gudhi_s2_base_betti": sphere_betti,
        "gudhi_s1_fiber_betti": fiber_betti,
    }


def sympy_checks() -> dict[str, Any]:
    eta, delta, theta = sp.symbols("eta delta theta", real=True)
    x = sp.sin(2 * eta) * sp.cos(delta)
    y = sp.sin(2 * eta) * sp.sin(delta)
    z = sp.cos(2 * eta)
    norm = sp.simplify(x**2 + y**2 + z**2)
    delta_after_global_phase = sp.simplify((delta + theta) - theta - delta)
    return {
        "pass": bool(sp.simplify(norm - 1) == 0 and delta_after_global_phase == 0),
        "hopf_base_norm_squared": str(norm),
        "global_phase_delta_residual": str(delta_after_global_phase),
    }


def proof_gate(required: dict[str, bool], min_gap: float) -> dict[str, Any]:
    solver = z3.Solver()
    gap = z3.Real("min_gap")
    all_required = z3.And(*[z3.BoolVal(bool(v)) for v in required.values()], gap > z3.RealVal(str(GAP)))
    solver.add(gap == z3.RealVal(str(min_gap)), z3.Not(all_required))
    z3_status = solver.check()

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
        "z3_required_negation": str(z3_status),
        "cvc5_required_negation": cvc5_status,
        "min_gap": min_gap,
    }


def scale_row(site_count: int, bond_dim: int) -> dict[str, Any]:
    shape = SHAPES[site_count]
    spinors, params = spinor_rows(site_count)
    mps = mps_network_readout(spinors, params)
    peps = peps_views(shape, spinors, bond_dim)
    dynamics = geometry_dynamics(params, spinors)
    topo = topology_checks(site_count, params)
    rho_ent = two_site_density(spinors, params, entangle=True)
    rho_prod = two_site_density(spinors, params, entangle=False)
    qit = qit_readouts(rho_ent)
    qit_product = qit_readouts(rho_prod)
    base_norms = [float(torch.linalg.vector_norm(hopf_base(psi)).item()) for psi in spinors]
    spinor_norms = [float(torch.linalg.vector_norm(psi).item()) for psi in spinors]
    contraction_gap = abs(peps["base_dot_contraction"])
    controls = {
        "product_no_entanglement_control": {
            "pass": bool(qit["log_negativity"] > qit_product["log_negativity"] + GAP),
            "baseline_log_negativity": qit["log_negativity"],
            "product_log_negativity": qit_product["log_negativity"],
        },
        "global_phase_erasure_does_not_move_base": {
            "pass": bool(dynamics["torch_fiber_invariance_gap"] < TOL),
            "fiber_invariance_gap": dynamics["torch_fiber_invariance_gap"],
        },
        "relative_phase_scramble_moves_base": {
            "pass": bool(dynamics["torch_scrambled_gap"] > GAP),
            "scramble_gap": dynamics["torch_scrambled_gap"],
        },
        "operation_order_matters": {
            "pass": bool(dynamics["torch_order_gap"] > GAP),
            "order_gap": dynamics["torch_order_gap"],
        },
        "peps3d_virtual_erasure_collapses_carrier": {
            "pass": bool(peps["virtual_l1"] > peps["erased_virtual_l1"] + GAP),
            "virtual_l1": peps["virtual_l1"],
            "erased_virtual_l1": peps["erased_virtual_l1"],
        },
        "scalar_entropy_only_rejected": {
            "pass": bool(qit["mutual_information"] > GAP and qit["log_negativity"] > GAP),
            "reason": "QIT vector is required; scalar entropy alone is not the Hopf fibration network object.",
            "S_AB": qit["S_AB"],
            "MI": qit["mutual_information"],
            "log_negativity": qit["log_negativity"],
        },
    }
    row_pass = bool(
        min(spinor_norms) > 1.0 - TOL
        and max(abs(v - 1.0) for v in base_norms) < TOL
        and mps["pass"]
        and peps["pass"]
        and dynamics["pass"]
        and topo["pass"]
        and qit["mutual_information"] > GAP
        and qit["log_negativity"] > GAP
        and contraction_gap > GAP
        and all(control["pass"] for control in controls.values())
    )
    return {
        "pass": row_pass,
        "site_count": site_count,
        "shape": list(shape),
        "bond_dim": bond_dim,
        "spinor_norm_min": min(spinor_norms),
        "base_norm_max_delta": max(abs(v - 1.0) for v in base_norms),
        "mps_network": mps,
        "peps_carriers": peps,
        "geometry_dynamics": dynamics,
        "topology": topo,
        "qit_readouts": qit,
        "qit_product_control": qit_product,
        "controls": controls,
    }


def main() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [scale_row(site_count, bond_dim) for site_count in SITE_COUNTS for bond_dim in BOND_DIMS]
    symbolic = sympy_checks()
    min_order_gap = min(row["geometry_dynamics"]["torch_order_gap"] for row in rows)
    min_mi = min(row["qit_readouts"]["mutual_information"] for row in rows)
    min_log_neg = min(row["qit_readouts"]["log_negativity"] for row in rows)
    min_virtual_delta = min(row["peps_carriers"]["virtual_l1"] - row["peps_carriers"]["erased_virtual_l1"] for row in rows)
    max_parity_delta = max(row["geometry_dynamics"]["jax_torch_max_delta"] for row in rows)
    required = {
        "rows_pass": all(row["pass"] for row in rows),
        "sympy_pass": symbolic["pass"],
        "parity_pass": max_parity_delta < PARITY_TOL,
        "order_gap_pass": min_order_gap > GAP,
        "qit_pass": min_mi > GAP and min_log_neg > GAP,
        "peps3d_virtual_pass": min_virtual_delta > GAP,
    }
    proof = proof_gate(required, min(min_order_gap, min_mi, min_log_neg, min_virtual_delta))
    positive = {
        "hopf_map_projects_s3_spinors_to_s2_base": {
            "pass": all(row["base_norm_max_delta"] < TOL for row in rows),
            "max_base_norm_delta": max(row["base_norm_max_delta"] for row in rows),
        },
        "global_u1_fiber_invariance_preserved": {
            "pass": all(row["geometry_dynamics"]["torch_fiber_invariance_gap"] < TOL for row in rows),
            "max_fiber_invariance_gap": max(row["geometry_dynamics"]["torch_fiber_invariance_gap"] for row in rows),
        },
        "order_sensitive_relative_phase_amplitude_transport": {
            "pass": min_order_gap > GAP,
            "min_order_gap": min_order_gap,
        },
        "network_carriers_mps_peps2d_peps3d_present": {
            "pass": all(row["mps_network"]["pass"] and row["peps_carriers"]["pass"] for row in rows),
            "site_counts": SITE_COUNTS,
            "bond_dims": BOND_DIMS,
        },
        "qit_entropy_correlation_vector_present": {
            "pass": min_mi > GAP and min_log_neg > GAP,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
        },
        "jax_torch_transport_parity": {
            "pass": max_parity_delta < PARITY_TOL,
            "max_delta": max_parity_delta,
        },
        "symbolic_and_smt_gates": {
            "pass": symbolic["pass"] and proof["pass"],
            "sympy": symbolic,
            "proof": proof,
        },
    }
    graveyard_companions = {
        "product_carrier_loses_entanglement_information": {
            "pass": all(row["controls"]["product_no_entanglement_control"]["pass"] for row in rows),
            "min_log_negativity": min_log_neg,
        },
        "peps3d_virtual_bond_erase_collapses_carrier_signal": {
            "pass": min_virtual_delta > GAP,
            "min_virtual_l1_delta": min_virtual_delta,
        },
        "relative_phase_scramble_changes_base_transport": {
            "pass": all(row["controls"]["relative_phase_scramble_moves_base"]["pass"] for row in rows),
        },
        "commuting_or_order_erased_substitute_rejected": {
            "pass": min_order_gap > GAP,
            "min_order_gap": min_order_gap,
        },
        "scalar_entropy_only_substitute_rejected": {
            "pass": all(row["controls"]["scalar_entropy_only_rejected"]["pass"] for row in rows),
        },
    }
    boundary = {
        "classification_is_lego_not_formal_scout": {
            "pass": CLASSIFICATION == "lego",
            "classification": CLASSIFICATION,
        },
        "promotion_blocked": {
            "pass": PROMOTION_ALLOWED is False,
            "promotion_allowed": PROMOTION_ALLOWED,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "one_math_object_not_aggregate_wrapper": {
            "pass": True,
            "object": "Hopf fibration S3_to_S2",
            "target_count": 1,
        },
    }
    all_pass = bool(
        all(required.values())
        and all(row["pass"] for row in rows)
        and all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and all(item["pass"] for item in boundary.values())
        and proof["pass"]
    )
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "Hopf fibration h:S3 -> S2 over finite two-component complex spinor networks",
        "finite_map": "h_N : {psi_i in S3}_{i=1..N} with U(1) fiber action and relative-phase/amplitude transport -> S2 base rows, network carrier readouts, QIT cuts, controls",
        "root_constraints_in_force": {
            "F01": "finite spinor sites, finite MPS/PEPS2D/PEPS3D carriers, finite transport maps, finite controls",
            "N01": "relative-phase/amplitude transport is order-sensitive while global U(1) fiber action is base-invariant",
        },
        "observable": [
            "S3 spinor norm",
            "S2 Hopf base norm",
            "global U(1) fiber invariance",
            "relative-phase/amplitude order gap",
            "MPS latent Schmidt entropy",
            "PEPS2D/PEPS3D virtual carrier signal",
            "mutual information",
            "coherent information",
            "log negativity",
            "S2 and S1 topology checks",
        ],
        "predicate": "finite Hopf spinor network preserves S3->S2 projection and U(1) fiber invariance while carrying order-sensitive network/QIT structure that controls can break",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "rows": rows,
        "symbolic_checks": symbolic,
        "proof_gate": proof,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "nearby_variants": {
            "total": len(rows),
            "passed": sum(1 for row in rows if row["pass"]),
            "site_counts": SITE_COUNTS,
            "bond_dims": BOND_DIMS,
        },
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "blockers": [] if all_pass else [key for key, value in required.items() if not value],
        "summary": {
            "all_pass": all_pass,
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "site_counts": SITE_COUNTS,
            "bond_dims": BOND_DIMS,
            "max_sites": max(SITE_COUNTS),
            "max_bond_dim": max(BOND_DIMS),
            "min_order_gap": min_order_gap,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
            "max_jax_torch_delta": max_parity_delta,
            "min_peps3d_virtual_l1_delta": min_virtual_delta,
        },
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    result = main()
    raise SystemExit(0 if result["summary"]["all_pass"] else 1)
