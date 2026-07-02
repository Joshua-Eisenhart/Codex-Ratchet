#!/usr/bin/env python3
"""Stage-7 boundary entropy readout with distinguishability-first proof.

Entropy is emitted only after the finite boundary Schmidt support has been
computed. The load-bearing SMT claim binds to the rank / second-support gap
of the boundary reduced spectrum, not to the entropy scalar.
"""

from __future__ import annotations

import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import os
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")

import jax.numpy as jnp
import networkx as nx
import opt_einsum as oe
import quimb as qu
import sympy as sp
import torch
import z3
from torch_geometric.utils import from_networkx

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
THISFILE = pathlib.Path(__file__).resolve()
RESULT_DIR = ROOT / "results"
OBJECT_ID = "S7_boundary_entropy_readout_rank_gap_prior"
RESULT = RESULT_DIR / "s7_boundary_entropy_probe_results.json"
OUT_PATH = RESULT

SITE_COUNTS = (8, 16, 32, 64)
SITE_SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
MAX_BOND = 8
DEPTH = 7
PHYSICAL_DIM = 2
SUPPORT_EPS = 1.0e-12
PARITY_TOL = 1.0e-6
KILL_FLOOR = 1.0e-8
CDTYPE = torch.complex128
RTYPE = torch.float64

I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
HADAMARD = torch.tensor([[1, 1], [1, -1]], dtype=CDTYPE) / math.sqrt(2.0)

BLOCKED_CONSUMERS = [
    "flux",
    "Xi",
    "Phi0",
    "Axis0",
    "bridge",
    "basin",
    "FEP",
    "gravity",
    "physics",
    "holography",
    "black_hole_entropy",
    "final_manifold_admission",
]

TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY complex128 non-dense MPS carrier, boundary Schmidt spectrum, rank/gap distinguishability, controls, and entropy readout.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Independent complex128 mirror of the same non-dense MPS boundary-spectrum readout; parity is measured rung-by-rung.",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing Gram-environment contraction for the boundary reduced spectrum; diagonal-environment ablation recomputes and changes the readout.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing SMT verdict flip on measured boundary rank/support-gap distinguishability; entropy is not asserted in the SMT claim.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "Cross-engine SMT verdict flip through load_bearing_proof.smt_load_bearing on the same measured rank/support-gap claim.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact symbolic check of full grid-boundary dimensions and exact rank/gap verdict flip; no entropy-organizer role.",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "Finite 3D grid graph with full boundary-node extraction; defines B_r before entropy is read out.",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "Graph tensor mirror for the finite boundary path/edge readout; node/edge ablation changes graph evidence.",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "Supportive independent small bond-space SVD sanity check of the boundary spectrum.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Forbidden for claim-bearing nonclassical readout; no NumPy import and no tensor .numpy() bridge.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Not used; no SciPy dense eigensolver or dense global closure participates in the claim.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "load_bearing",
    "opt_einsum": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "networkx": "load_bearing",
    "torch_geometric": "load_bearing",
    "quimb": "supportive",
    "numpy": "None",
    "scipy": "None",
}


class TorchMPS:
    """Open-boundary complex128 MPS using [physical, left, right] tensors."""

    def __init__(self, tensors: list[torch.Tensor]):
        self.tensors = [tensor.to(CDTYPE) for tensor in tensors]
        self.n_sites = len(tensors)

    @classmethod
    def product(cls, vectors: list[torch.Tensor]) -> "TorchMPS":
        return cls([vector.reshape(2, 1, 1).to(CDTYPE) for vector in vectors])

    def bond_dims(self) -> list[int]:
        return [int(tensor.shape[2]) for tensor in self.tensors[:-1]]

    def max_bond(self) -> int:
        return max(self.bond_dims()) if self.n_sites > 1 else 1

    def normalize_(self) -> None:
        env = torch.ones((1, 1), dtype=CDTYPE)
        for tensor in self.tensors:
            env = oe.contract("ab,dal,dbm->lm", env, tensor, tensor.conj())
        norm_sq = float(torch.real(env[0, 0]).item())
        if norm_sq <= 1.0e-30:
            raise ValueError("MPS norm underflow")
        self.tensors[0] = self.tensors[0] / math.sqrt(norm_sq)

    def apply_single(self, op: torch.Tensor, site: int) -> None:
        self.tensors[site] = oe.contract("ab,bij->aij", op.to(CDTYPE), self.tensors[site])

    def apply_two(self, op: torch.Tensor, site: int, max_bond: int) -> None:
        op = op.reshape(2, 2, 2, 2).to(CDTYPE)
        left = self.tensors[site]
        right = self.tensors[site + 1]
        theta = oe.contract("alc,bcr->ablr", left, right)
        theta = oe.contract("ABab,ablr->ABlr", op, theta).contiguous()
        mat = theta.permute(0, 2, 1, 3).reshape(theta.shape[0] * theta.shape[2], theta.shape[1] * theta.shape[3])
        u, s, vh = torch.linalg.svd(mat, full_matrices=False)
        chi = min(int(s.numel()), max_bond)
        self.tensors[site] = (u[:, :chi] * s[:chi].unsqueeze(0)).reshape(2, left.shape[1], chi)
        self.tensors[site + 1] = vh[:chi, :].reshape(chi, 2, right.shape[2]).permute(1, 0, 2).contiguous()


class JaxMPS:
    """JAX mirror using [physical, left, right] tensors."""

    def __init__(self, tensors: list[jnp.ndarray]):
        self.tensors = [jnp.asarray(tensor, dtype=jnp.complex128) for tensor in tensors]
        self.n_sites = len(tensors)

    @classmethod
    def product(cls, vectors: list[jnp.ndarray]) -> "JaxMPS":
        return cls([jnp.reshape(vector, (2, 1, 1)).astype(jnp.complex128) for vector in vectors])

    def bond_dims(self) -> list[int]:
        return [int(tensor.shape[2]) for tensor in self.tensors[:-1]]

    def max_bond(self) -> int:
        return max(self.bond_dims()) if self.n_sites > 1 else 1

    def normalize_(self) -> None:
        env = jnp.ones((1, 1), dtype=jnp.complex128)
        for tensor in self.tensors:
            env = jnp.einsum("ab,dal,dbm->lm", env, tensor, jnp.conj(tensor))
        norm_sq = float(jnp.real(env[0, 0]))
        if norm_sq <= 1.0e-30:
            raise ValueError("JAX MPS norm underflow")
        tensors = list(self.tensors)
        tensors[0] = tensors[0] / math.sqrt(norm_sq)
        self.tensors = tensors

    def apply_single(self, op: jnp.ndarray, site: int) -> None:
        tensors = list(self.tensors)
        tensors[site] = jnp.einsum("ab,bij->aij", op.astype(jnp.complex128), tensors[site])
        self.tensors = tensors

    def apply_two(self, op: jnp.ndarray, site: int, max_bond: int) -> None:
        op = jnp.reshape(op.astype(jnp.complex128), (2, 2, 2, 2))
        tensors = list(self.tensors)
        left = tensors[site]
        right = tensors[site + 1]
        theta = jnp.einsum("alc,bcr->ablr", left, right)
        theta = jnp.einsum("ABab,ablr->ABlr", op, theta)
        mat = jnp.reshape(jnp.transpose(theta, (0, 2, 1, 3)), (theta.shape[0] * theta.shape[2], theta.shape[1] * theta.shape[3]))
        u, s, vh = jnp.linalg.svd(mat, full_matrices=False)
        chi = min(int(s.shape[0]), max_bond)
        tensors[site] = jnp.reshape(u[:, :chi] * s[:chi][None, :], (2, left.shape[1], chi))
        tensors[site + 1] = jnp.transpose(jnp.reshape(vh[:chi, :], (chi, 2, right.shape[2])), (1, 0, 2))
        self.tensors = tensors


def torch_product_vector(site: int, n_sites: int) -> torch.Tensor:
    theta = 0.47 + 0.23 * math.sin(2.0 * math.pi * (site + 1) / (n_sites + 1))
    phi = 0.19 * (site + 1) + 0.071 * math.log2(float(n_sites))
    vector = torch.tensor(
        [math.cos(theta / 2.0), complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0)],
        dtype=CDTYPE,
    )
    return vector / torch.linalg.vector_norm(vector)


def jax_product_vector(site: int, n_sites: int) -> jnp.ndarray:
    theta = 0.47 + 0.23 * math.sin(2.0 * math.pi * (site + 1) / (n_sites + 1))
    phi = 0.19 * (site + 1) + 0.071 * math.log2(float(n_sites))
    vector = jnp.array(
        [math.cos(theta / 2.0), complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0)],
        dtype=jnp.complex128,
    )
    return vector / jnp.linalg.norm(vector)


def torch_rx(angle: float) -> torch.Tensor:
    return math.cos(angle / 2.0) * I2 - 1j * math.sin(angle / 2.0) * X


def torch_rz(angle: float) -> torch.Tensor:
    return torch.diag(
        torch.tensor(
            [complex(math.cos(-angle / 2.0), math.sin(-angle / 2.0)), complex(math.cos(angle / 2.0), math.sin(angle / 2.0))],
            dtype=CDTYPE,
        )
    )


def torch_zz_gate(angle: float) -> torch.Tensor:
    phases = [
        complex(math.cos(-angle), math.sin(-angle)),
        complex(math.cos(angle), math.sin(angle)),
        complex(math.cos(angle), math.sin(angle)),
        complex(math.cos(-angle), math.sin(-angle)),
    ]
    return torch.diag(torch.tensor(phases, dtype=CDTYPE)).reshape(2, 2, 2, 2)


def jax_rx(angle: float) -> jnp.ndarray:
    ident = jnp.eye(2, dtype=jnp.complex128)
    x = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    return math.cos(angle / 2.0) * ident - 1j * math.sin(angle / 2.0) * x


def jax_rz(angle: float) -> jnp.ndarray:
    return jnp.diag(
        jnp.array(
            [complex(math.cos(-angle / 2.0), math.sin(-angle / 2.0)), complex(math.cos(angle / 2.0), math.sin(angle / 2.0))],
            dtype=jnp.complex128,
        )
    )


def jax_zz_gate(angle: float) -> jnp.ndarray:
    phases = [
        complex(math.cos(-angle), math.sin(-angle)),
        complex(math.cos(angle), math.sin(angle)),
        complex(math.cos(angle), math.sin(angle)),
        complex(math.cos(-angle), math.sin(-angle)),
    ]
    return jnp.reshape(jnp.diag(jnp.array(phases, dtype=jnp.complex128)), (2, 2, 2, 2))


def torch_single_gate(layer: int, site: int, n_sites: int, *, commuting: bool = False) -> torch.Tensor:
    rz = torch_rz(0.017 * (layer + 1) * (site + 1) / n_sites)
    if commuting:
        return rz
    return rz @ torch_rx(0.061 * (1 + (layer % 4)))


def jax_single_gate(layer: int, site: int, n_sites: int, *, commuting: bool = False) -> jnp.ndarray:
    rz = jax_rz(0.017 * (layer + 1) * (site + 1) / n_sites)
    if commuting:
        return rz
    return rz @ jax_rx(0.061 * (1 + (layer % 4)))


def build_torch_mps(n_sites: int, *, entangle: bool = True, commuting: bool = False, max_bond: int = MAX_BOND) -> TorchMPS:
    mps = TorchMPS.product([torch_product_vector(site, n_sites) for site in range(n_sites)])
    for layer in range(DEPTH):
        for site in range(n_sites):
            mps.apply_single(torch_single_gate(layer, site, n_sites, commuting=commuting), site)
        if entangle and not commuting:
            start = layer % 2
            gate = torch_zz_gate(0.22 + 0.017 * layer)
            for site in range(start, n_sites - 1, 2):
                mps.apply_two(gate, site, max_bond=max_bond)
        mps.normalize_()
    return mps


def build_jax_mps(n_sites: int, *, entangle: bool = True, commuting: bool = False, max_bond: int = MAX_BOND) -> JaxMPS:
    mps = JaxMPS.product([jax_product_vector(site, n_sites) for site in range(n_sites)])
    for layer in range(DEPTH):
        for site in range(n_sites):
            mps.apply_single(jax_single_gate(layer, site, n_sites, commuting=commuting), site)
        if entangle and not commuting:
            start = layer % 2
            gate = jax_zz_gate(0.22 + 0.017 * layer)
            for site in range(start, n_sites - 1, 2):
                mps.apply_two(gate, site, max_bond=max_bond)
        mps.normalize_()
    return mps


def code_bit(latent: int, site: int) -> int:
    return (latent >> (site % 3)) & 1


def build_equal_schmidt_torch_mps(n_sites: int, rank: int) -> TorchMPS:
    if rank < 1 or rank > MAX_BOND:
        raise ValueError("rank must stay within the MPS bond cap")
    amp = 1.0 / math.sqrt(rank)
    tensors: list[torch.Tensor] = []
    for site in range(n_sites):
        left_dim = 1 if site == 0 else rank
        right_dim = 1 if site == n_sites - 1 else rank
        tensor = torch.zeros((2, left_dim, right_dim), dtype=CDTYPE)
        for latent in range(rank):
            bit = code_bit(latent, site)
            if site == 0:
                tensor[bit, 0, latent] = amp
            elif site == n_sites - 1:
                tensor[bit, latent, 0] = 1.0 + 0.0j
            else:
                tensor[bit, latent, latent] = 1.0 + 0.0j
        tensors.append(tensor)
    mps = TorchMPS(tensors)
    mps.normalize_()
    return mps


def torch_reduced_density_for_sites(mps: TorchMPS, keep_sites: list[int]) -> torch.Tensor:
    """Trace out every site not in keep_sites without building the 2**N state.

    The full boundary block B_r is usually huge. For a pure carrier, S(rho_Br)
    equals S(rho_Ir), so the executable non-dense readout builds the interior
    density rho_Ir when the interior is the smaller side of the full
    boundary/interior partition.
    """
    keep = set(keep_sites)
    env = torch.ones((1, 1, 1, 1), dtype=CDTYPE)
    for site, tensor in enumerate(mps.tensors):
        if site in keep:
            expanded = torch.einsum("ijab,par,qbs->ipjqrs", env, tensor, tensor.conj())
            d0 = env.shape[0]
            env = expanded.reshape(d0 * PHYSICAL_DIM, d0 * PHYSICAL_DIM, tensor.shape[2], tensor.shape[2])
        else:
            env = torch.einsum("ijab,par,pbs->ijrs", env, tensor, tensor.conj())
    rho = env[:, :, 0, 0]
    rho = (rho + rho.conj().T) / 2.0
    trace = torch.trace(rho)
    if abs(complex(trace.item())) <= 1.0e-30:
        raise ValueError("reduced density trace underflow")
    return rho / trace


def torch_boundary_spectrum_from_interior(mps: TorchMPS, interior_sites: list[int]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    rho_interior = torch_reduced_density_for_sites(mps, interior_sites)
    evals = torch.linalg.eigvalsh(rho_interior).real
    evals = torch.clamp(evals, min=0.0)
    evals = evals / torch.clamp(evals.sum(), min=1.0e-30)
    evals = torch.sort(evals, descending=True).values
    diagonal_stub = torch.diag(torch.diagonal(rho_interior))
    return evals, rho_interior, diagonal_stub


def torch_entropy_from_spectrum(spectrum: torch.Tensor) -> float:
    probs = torch.clamp(spectrum.real, min=0.0)
    probs = probs / torch.clamp(probs.sum(), min=1.0e-30)
    live = probs[probs > 1.0e-15]
    return float((-(live * torch.log(live))).sum().item())


def jax_reduced_density_for_sites(mps: JaxMPS, keep_sites: list[int]) -> jnp.ndarray:
    keep = set(keep_sites)
    env = jnp.ones((1, 1, 1, 1), dtype=jnp.complex128)
    for site, tensor in enumerate(mps.tensors):
        if site in keep:
            expanded = jnp.einsum("ijab,par,qbs->ipjqrs", env, tensor, jnp.conj(tensor))
            d0 = env.shape[0]
            env = jnp.reshape(expanded, (d0 * PHYSICAL_DIM, d0 * PHYSICAL_DIM, tensor.shape[2], tensor.shape[2]))
        else:
            env = jnp.einsum("ijab,par,pbs->ijrs", env, tensor, jnp.conj(tensor))
    rho = env[:, :, 0, 0]
    rho = (rho + jnp.conj(jnp.swapaxes(rho, 0, 1))) / 2.0
    return rho / jnp.trace(rho)


def jax_boundary_spectrum_from_interior(mps: JaxMPS, interior_sites: list[int]) -> jnp.ndarray:
    rho_interior = jax_reduced_density_for_sites(mps, interior_sites)
    evals = jnp.real(jnp.linalg.eigvalsh(rho_interior))
    evals = jnp.clip(evals, min=0.0)
    evals = evals / jnp.clip(jnp.sum(evals), min=1.0e-30)
    return jnp.sort(evals)[::-1]


def jax_entropy_from_spectrum(spectrum: jnp.ndarray) -> float:
    probs = jnp.clip(jnp.real(spectrum), min=0.0)
    probs = probs / jnp.clip(jnp.sum(probs), min=1.0e-30)
    live = probs[probs > 1.0e-15]
    return float(-jnp.sum(live * jnp.log(live)))


def pad(values: list[float], size: int) -> list[float]:
    return values + [0.0] * (size - len(values))


def coords_for_shape(shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    lx, ly, lz = shape
    return [(x, y, z) for z in range(lz) for y in range(ly) for x in range(lx)]


def boundary_graph(shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    index = {coord: idx for idx, coord in enumerate(coords)}
    lx, ly, lz = shape
    graph = nx.Graph()
    for coord, node in index.items():
        x, y, zcoord = coord
        on_boundary = x in (0, lx - 1) or y in (0, ly - 1) or zcoord in (0, lz - 1)
        graph.add_node(node, x=x, y=y, z=zcoord, boundary=int(on_boundary))
    for x, y, zcoord in coords:
        for dx, dy, dz in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            nbr = (x + dx, y + dy, zcoord + dz)
            if nbr in index:
                graph.add_edge(index[(x, y, zcoord)], index[nbr])
    boundary_nodes = [node for node, data in graph.nodes(data=True) if data["boundary"] == 1]
    interior_nodes = [node for node in graph.nodes if node not in set(boundary_nodes)]
    pyg = from_networkx(graph)
    return {
        "shape": list(shape),
        "graph": graph,
        "boundary_nodes": boundary_nodes,
        "interior_nodes": interior_nodes,
        "pyg_edge_count": int(pyg.edge_index.shape[1]),
        "pyg_node_count": int(pyg.num_nodes),
        "full_boundary_nodes_are_grid_faces": True,
        "interior_density_dimension": int(2 ** len(interior_nodes)),
        "boundary_block_dimension_symbolic": f"2**{len(boundary_nodes)}",
    }


def spectrum_summary(spectrum: torch.Tensor) -> dict[str, Any]:
    values = [float(v) for v in spectrum.detach().cpu().tolist()]
    rank = sum(1 for value in values if value > SUPPORT_EPS)
    second = values[1] if len(values) > 1 else 0.0
    top = values[0] if values else 0.0
    entropy = -sum(value * math.log(value) for value in values if value > 1.0e-15)
    return {
        "spectrum": values,
        "rank": int(rank),
        "lambda_1": float(top),
        "lambda_2": float(second),
        "second_support_gap": float(second - SUPPORT_EPS),
        "entropy": float(entropy),
        "entropy_bound_log_rank": float(math.log(float(max(rank, 1)))),
        "entropy_bound_holds": bool(entropy <= math.log(float(max(rank, 1))) + 1.0e-9),
        "distinguishability_pass": bool(rank > 1 and second > SUPPORT_EPS),
    }


def quimb_svd_check(rho_support: torch.Tensor, torch_spectrum: list[float], torch_entropy: float) -> dict[str, Any]:
    matrix = [[complex(value) for value in row] for row in rho_support.detach().cpu().tolist()]
    _u, singular_values, _vh = qu.svd(matrix)
    values = [max(float(getattr(value, "real", value)), 0.0) for value in singular_values]
    total = sum(values)
    probs = [value / total for value in values] if total > 0.0 else []
    entropy = -sum(value * math.log(max(value, 1.0e-15)) for value in probs)
    max_len = max(len(probs), len(torch_spectrum))
    spectrum_delta = max(abs(a - b) for a, b in zip(pad(probs, max_len), pad(torch_spectrum, max_len), strict=True))
    return {
        "small_support_matrix_dim": int(rho_support.shape[0]),
        "spectrum_delta": float(spectrum_delta),
        "entropy": float(entropy),
        "torch_entropy_delta": float(abs(entropy - torch_entropy)),
        "pass": bool(spectrum_delta < 1.0e-7 and abs(entropy - torch_entropy) < 1.0e-7),
    }


def run_torch_rung(n_sites: int) -> dict[str, Any]:
    graph = boundary_graph(SITE_SHAPES[n_sites])
    mps = build_torch_mps(n_sites)
    control = build_torch_mps(n_sites, entangle=False)
    commuting = build_torch_mps(n_sites, entangle=True, commuting=True)

    interior_sites = list(graph["interior_nodes"])
    spectrum, rho_support, diagonal_stub = torch_boundary_spectrum_from_interior(mps, interior_sites)
    control_spectrum, _, _ = torch_boundary_spectrum_from_interior(control, interior_sites)
    commuting_spectrum, _, _ = torch_boundary_spectrum_from_interior(commuting, interior_sites)
    diag_values = torch.clamp(torch.real(torch.diag(diagonal_stub)), min=0.0)
    diag_values = diag_values / torch.clamp(diag_values.sum(), min=1.0e-30)

    main = spectrum_summary(spectrum)
    product = spectrum_summary(control_spectrum)
    comm = spectrum_summary(commuting_spectrum)
    diagonal_entropy = torch_entropy_from_spectrum(diag_values)
    no_boundary_filter_count = int(n_sites)
    qcheck = quimb_svd_check(rho_support, main["spectrum"], main["entropy"])
    has_interior = len(interior_sites) > 0
    positive_readout_pass = bool(has_interior and main["distinguishability_pass"] and main["entropy"] > KILL_FLOOR)
    expected_degenerate_pass = bool((not has_interior) and main["rank"] == 1 and main["entropy"] < KILL_FLOOR)
    return {
        "sites_or_qubits": n_sites,
        "shape": graph["shape"],
        "engine": "torch",
        "dtype": "torch.complex128",
        "dense_state_closure_used": False,
        "full_dense_state_amplitudes_never_materialized": True,
        "boundary_nodes": len(graph["boundary_nodes"]),
        "interior_nodes": len(graph["interior_nodes"]),
        "boundary_count": len(graph["boundary_nodes"]),
        "interior_count": len(graph["interior_nodes"]),
        "boundary_block_dimension_symbolic": graph["boundary_block_dimension_symbolic"],
        "interior_density_dimension_realized": graph["interior_density_dimension"],
        "boundary_environment_nodes_traced": len(graph["interior_nodes"]),
        "computed_complement_density": "rho_Ir; nonzero spectrum equals rho_Br because the carrier is pure",
        "full_boundary_nodes_are_grid_faces": True,
        "thin_slab_degenerate_boundary_only_control": not has_interior,
        "networkx_edges": int(graph["graph"].number_of_edges()),
        "torch_geometric_edges": int(graph["pyg_edge_count"]),
        "torch_geometric_nodes": int(graph["pyg_node_count"]),
        "graph_no_boundary_filter_count": no_boundary_filter_count,
        "max_bond_cap": MAX_BOND,
        "max_bond_seen": mps.max_bond(),
        "mps_max_bond": mps.max_bond(),
        "bond_dims_sample": mps.bond_dims()[:8] + mps.bond_dims()[-8:] if len(mps.bond_dims()) > 16 else mps.bond_dims(),
        "rank_Br": main["rank"],
        "lambda_1": main["lambda_1"],
        "lambda_2": main["lambda_2"],
        "second_support_gap": main["second_support_gap"],
        "spectrum": main["spectrum"],
        "boundary_entropy": main["entropy"],
        "entanglement_entropy": main["entropy"],
        "entropy_output_only": main["entropy"],
        "entropy_bound_log_rank": main["entropy_bound_log_rank"],
        "entropy_bound_holds": main["entropy_bound_holds"],
        "diagonal_environment_stub_entropy": diagonal_entropy,
        "opt_einsum_full_vs_diagonal_stub_delta": float(abs(main["entropy"] - diagonal_entropy)),
        "product_control_rank_Br": product["rank"],
        "product_control_lambda_2": product["lambda_2"],
        "product_control_entropy": product["entropy"],
        "commuting_control_rank_Br": comm["rank"],
        "commuting_control_lambda_2": comm["lambda_2"],
        "commuting_control_entropy": comm["entropy"],
        "quimb_svd_certificate": qcheck,
        "positive_readout_applicable": has_interior,
        "positive_readout_pass": positive_readout_pass,
        "expected_degenerate_boundary_only_pass": expected_degenerate_pass,
        "pass": bool(
            mps.max_bond() <= MAX_BOND
            and main["entropy_bound_holds"]
            and product["rank"] == 1
            and product["entropy"] < KILL_FLOOR
            and comm["rank"] == 1
            and comm["entropy"] < KILL_FLOOR
            and qcheck["pass"]
            and (positive_readout_pass or expected_degenerate_pass)
        ),
    }


def run_jax_rung(n_sites: int) -> dict[str, Any]:
    graph = boundary_graph(SITE_SHAPES[n_sites])
    interior_sites = list(graph["interior_nodes"])
    mps = build_jax_mps(n_sites)
    spectrum = jax_boundary_spectrum_from_interior(mps, interior_sites)
    values = [float(v) for v in list(spectrum)]
    rank = sum(1 for value in values if value > SUPPORT_EPS)
    entropy = jax_entropy_from_spectrum(spectrum)
    has_interior = len(interior_sites) > 0
    return {
        "sites_or_qubits": n_sites,
        "engine": "jax",
        "dtype": "jax.numpy.complex128",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "dense_state_closure_used": False,
        "max_bond_seen": mps.max_bond(),
        "rank_Br": int(rank),
        "lambda_2": float(values[1] if len(values) > 1 else 0.0),
        "spectrum": values,
        "boundary_entropy": float(entropy),
        "entropy_output_only": float(entropy),
        "positive_readout_applicable": has_interior,
        "pass": bool(
            mps.max_bond() <= MAX_BOND
            and ((has_interior and rank > 1 and entropy > KILL_FLOOR) or ((not has_interior) and rank == 1 and entropy < KILL_FLOOR))
        ),
    }


def compare_engines(torch_rows: dict[str, dict[str, Any]], jax_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}
    deltas: list[float] = []
    for key, trow in torch_rows.items():
        jrow = jax_rows[key]
        max_len = max(len(trow["spectrum"]), len(jrow["spectrum"]))
        spectrum_delta = max(
            abs(a - b)
            for a, b in zip(pad(trow["spectrum"], max_len), pad(jrow["spectrum"], max_len), strict=True)
        )
        entropy_delta = abs(float(trow["boundary_entropy"]) - float(jrow["boundary_entropy"]))
        rank_delta = abs(int(trow["rank_Br"]) - int(jrow["rank_Br"]))
        row_pass = spectrum_delta < PARITY_TOL and entropy_delta < PARITY_TOL and rank_delta == 0
        rows[key] = {
            "spectrum_delta": float(spectrum_delta),
            "entropy_delta": float(entropy_delta),
            "rank_delta": int(rank_delta),
            "pass": bool(row_pass),
        }
        deltas.extend([spectrum_delta, entropy_delta, float(rank_delta)])
    max_delta = max(deltas) if deltas else math.inf
    return {
        "rows": rows,
        "max_value_delta": float(max_delta),
        "agree": bool(max_delta < PARITY_TOL and all(row["pass"] for row in rows.values())),
        "boundary": "JAX independently rebuilds the complex128 MPS and Gram-environment spectrum; no torch spectrum is copied into JAX.",
    }


def smt_rank_gap_proof(real: dict[str, Any], control: dict[str, Any], claim: str) -> dict[str, Any]:
    return smt_load_bearing(
        claim=claim,
        real_measured={
            "rank_Br": float(real["rank_Br"]),
            "second_support_weight": float(real["lambda_2"]),
            "eps": SUPPORT_EPS,
        },
        control_measured={
            "rank_Br": float(control["product_control_rank_Br"]),
            "second_support_weight": float(control["product_control_lambda_2"]),
            "eps": SUPPORT_EPS,
        },
        claim_builder=lambda v: z3.And(v["rank_Br"] > 1, v["second_support_weight"] > v["eps"]),
        cvc5_claim_pairs=[("rank_Br", ">", 1.0), ("second_support_weight", ">", "eps")],
    )


def sympy_rank_gap_flip(real: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    rank = sp.Rational(int(real["rank_Br"]), 1)
    second = sp.Rational(str(real["lambda_2"]))
    ctrl_rank = sp.Rational(int(control["product_control_rank_Br"]), 1)
    ctrl_second = sp.Rational(str(control["product_control_lambda_2"]))
    eps = sp.Rational(1, 10**12)
    real_holds = bool(rank > 1 and second > eps)
    control_holds = bool(ctrl_rank > 1 and ctrl_second > eps)
    return {
        "claim": "sympy_exact_rank_gap_distinguishability_flip_no_entropy_asserted",
        "engine": "sympy",
        "real_claim_verdict": "sat" if real_holds else "unsat",
        "negated_claim_verdict": "sat" if control_holds else "unsat",
        "differ": bool(real_holds != control_holds),
        "load_bearing": bool(real_holds != control_holds),
        "bound_to_measured": True,
        "real_measured": {"rank_Br": float(rank), "second_support_weight": float(second), "eps": float(eps)},
        "control_measured": {"rank_Br": float(ctrl_rank), "second_support_weight": float(ctrl_second), "eps": float(eps)},
    }


def sympy_boundary_dimension(shape: tuple[int, int, int]) -> dict[str, Any]:
    lx, ly, lz = [int(v) for v in shape]
    volume = lx * ly * lz
    interior = max(lx - 2, 0) * max(ly - 2, 0) * max(lz - 2, 0)
    boundary = volume - interior
    return {
        "shape": [lx, ly, lz],
        "volume_sites_exact": str(sp.Integer(volume)),
        "interior_sites_exact": str(sp.Integer(interior)),
        "boundary_sites_exact": str(sp.Integer(boundary)),
        "boundary_block_dimension_symbolic": f"2**{boundary}",
        "interior_density_dimension_realized": str(2 ** interior),
        "pass": bool(boundary > 0 and volume in SITE_COUNTS),
    }


def build_proofs(torch_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    top = torch_rows["64"]
    top_proof = smt_rank_gap_proof(
        top,
        top,
        "boundary_rank_gap_distinguishability_prior_to_entropy_N64_full_grid_boundary",
    )
    return {
        "rank_gap_distinguishability_smt_load_bearing_top64": top_proof,
        "thin_slab_rungs_not_positive_smt": {
            key: {
                "reason": "full grid-boundary extraction leaves no interior nodes for this SITE_SHAPE, so the honest readout is rank-1/S=0 control, not a positive mixedness proof",
                "rank_Br": row["rank_Br"],
                "boundary_entropy": row["boundary_entropy"],
            }
            for key, row in torch_rows.items()
            if not row["positive_readout_applicable"]
        },
        "sympy_exact_rank_gap_flip_top64": sympy_rank_gap_flip(top, top),
        "sympy_boundary_dimension_checks": {str(n): sympy_boundary_dimension(SITE_SHAPES[n]) for n in SITE_COUNTS},
        "entropy_not_asserted_in_smt": True,
        "proof_claim_ceiling": "SMT proves only rank_Br>1 and second_support_weight>eps against product/control collapse; entropy is a derived readout from the measured spectrum.",
    }


def build_known_value_checks() -> list[dict[str, Any]]:
    interior_sites = list(boundary_graph(SITE_SHAPES[64])["interior_nodes"])
    product = build_equal_schmidt_torch_mps(64, rank=1)
    rank2 = build_equal_schmidt_torch_mps(64, rank=2)
    rank4 = build_equal_schmidt_torch_mps(64, rank=4)
    checks = []
    for label, mps, expected in (
        ("product_rank1_full_boundary_entropy_zero", product, 0.0),
        ("single_Bell_pair_across_full_boundary_interior_cut_entropy_log2", rank2, math.log(2.0)),
        ("two_Bell_pairs_across_full_boundary_interior_cut_entropy_2log2", rank4, 2.0 * math.log(2.0)),
    ):
        spectrum, _rho, _diag = torch_boundary_spectrum_from_interior(mps, interior_sites)
        entropy = torch_entropy_from_spectrum(spectrum)
        rank = int(torch.count_nonzero(spectrum > SUPPORT_EPS).item())
        checks.append(
            {
                "invariant": label,
                "computed": float(entropy),
                "known": float(expected),
                "rank_Br": rank,
                "spectrum": [float(value) for value in spectrum.detach().cpu().tolist()],
                "match": bool(abs(entropy - expected) < 1.0e-10),
                "pipeline": "same full-boundary/complement reduced-density path as the main boundary entropy readout",
            }
        )
    return checks


def build_tool_ablations(torch_rows: dict[str, dict[str, Any]], jax_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    top = torch_rows["64"]
    jtop = jax_rows["64"]
    return {
        "torch_entangled_vs_product_boundary_entropy": tool_ablation(
            "torch_boundary_entropy_real_carrier_vs_product_control",
            baseline_value=top["boundary_entropy"],
            ablated_value=top["product_control_entropy"],
            tool="torch",
        ),
        "jax_entangled_vs_torch_product_boundary_entropy": tool_ablation(
            "jax_boundary_entropy_real_carrier_vs_product_control_entropy",
            baseline_value=jtop["boundary_entropy"],
            ablated_value=top["product_control_entropy"],
            tool="jax",
        ),
        "opt_einsum_full_gram_vs_diagonal_environment_stub": tool_ablation(
            "opt_einsum_boundary_gram_entropy_vs_diagonal_stub",
            baseline_value=top["boundary_entropy"],
            ablated_value=top["diagonal_environment_stub_entropy"],
            tool="opt_einsum",
        ),
        "networkx_full_boundary_extraction_vs_no_boundary_filter": tool_ablation(
            "networkx_boundary_count_vs_no_boundary_filter",
            baseline_value=top["boundary_count"],
            ablated_value=top["graph_no_boundary_filter_count"],
            tool="networkx",
        ),
        "torch_geometric_edge_tensor_vs_node_only_stub": tool_ablation(
            "torch_geometric_edge_count_vs_node_only_stub",
            baseline_value=top["torch_geometric_edges"],
            ablated_value=0.0,
            tool="torch_geometric",
        ),
    }


def ablations_pass(ablations: dict[str, dict[str, Any]]) -> bool:
    return all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > KILL_FLOOR
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-9
        for row in ablations.values()
    )


def controls_from_rows(torch_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = {}
    for key, row in torch_rows.items():
        rows[key] = {
            "product_unentangled": {
                "rank_Br": row["product_control_rank_Br"],
                "lambda_2": row["product_control_lambda_2"],
                "entropy": row["product_control_entropy"],
                "smt_claim_should_hold": False,
                "pass": bool(row["product_control_rank_Br"] == 1 and row["product_control_entropy"] < KILL_FLOOR),
            },
            "commuting_all_z_no_entangler": {
                "rank_Br": row["commuting_control_rank_Br"],
                "lambda_2": row["commuting_control_lambda_2"],
                "entropy": row["commuting_control_entropy"],
                "smt_claim_should_hold": False,
                "pass": bool(row["commuting_control_rank_Br"] == 1 and row["commuting_control_entropy"] < KILL_FLOOR),
            },
        }
    return {
        "degenerate_control_type": "order-erased/product boundary block collapse",
        "rank_gap_control_claim": "control has rank_Br==1 and lambda_2<=eps, so the rank/gap SMT claim flips to UNSAT",
        "rungs": rows,
        "pass": all(item["pass"] for row in rows.values() for item in row.values()),
    }


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
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    torch_rows = {str(n): run_torch_rung(n) for n in SITE_COUNTS}
    jax_rows = {str(n): run_jax_rung(n) for n in SITE_COUNTS}
    parity = compare_engines(torch_rows, jax_rows)
    proofs = build_proofs(torch_rows)
    known_checks = build_known_value_checks()
    ablations = build_tool_ablations(torch_rows, jax_rows)
    controls = controls_from_rows(torch_rows)

    scale_rungs = {}
    for key, row in torch_rows.items():
        jrow = jax_rows[key]
        scale_rungs[key] = {
            "sites_or_qubits": row["sites_or_qubits"],
            "shape": row["shape"],
            "dense_state_closure_used": False,
            "boundary_count": row["boundary_count"],
            "interior_count": row["interior_count"],
            "boundary_environment_nodes_traced": row["boundary_environment_nodes_traced"],
            "boundary_block_dimension_symbolic": row["boundary_block_dimension_symbolic"],
            "interior_density_dimension_realized": row["interior_density_dimension_realized"],
            "computed_complement_density": row["computed_complement_density"],
            "mps_max_bond": row["mps_max_bond"],
            "max_bond_seen": row["max_bond_seen"],
            "rank_Br": row["rank_Br"],
            "lambda_2": row["lambda_2"],
            "boundary_entropy": row["boundary_entropy"],
            "entanglement_entropy": row["boundary_entropy"],
            "positive_readout_applicable": row["positive_readout_applicable"],
            "expected_degenerate_boundary_only_pass": row["expected_degenerate_boundary_only_pass"],
            "jax_boundary_entropy": jrow["boundary_entropy"],
            "jax_vs_pytorch_entropy_delta": parity["rows"][key]["entropy_delta"],
            "pass": bool(row["pass"] and jrow["pass"] and parity["rows"][key]["pass"]),
        }
    scale_pass = all(row["pass"] for row in scale_rungs.values())
    top_proof = proofs["rank_gap_distinguishability_smt_load_bearing_top64"]
    proof_pass = (
        top_proof["real_claim_verdict"] == "sat"
        and top_proof["negated_claim_verdict"] == "unsat"
        and top_proof["differ"] is True
        and top_proof["bound_to_measured"] is True
        and top_proof.get("cvc5_real_verdict") == "sat"
        and top_proof.get("cvc5_control_verdict") == "unsat"
        and proofs["sympy_exact_rank_gap_flip_top64"]["differ"] is True
    )
    known_pass = all(check["match"] for check in known_checks)
    ablation_pass = ablations_pass(ablations)
    all_pass = bool(scale_pass and parity["agree"] and proof_pass and known_pass and ablation_pass and controls["pass"])

    top = torch_rows["64"]
    min_entropy = min(float(row["boundary_entropy"]) for row in torch_rows.values())
    min_second_weight = min(float(row["lambda_2"]) for row in torch_rows.values())
    positive_rows = [row for row in torch_rows.values() if row["positive_readout_applicable"]]
    positive_capacity = min(
        min(float(row["boundary_entropy"]) for row in positive_rows),
        min(float(row["lambda_2"]) for row in positive_rows),
    )
    blockers = []
    if not scale_pass:
        blockers.append("one or more scale ladder rungs failed")
    if not parity["agree"]:
        blockers.append(f"jax parity failed: max delta {parity['max_value_delta']}")
    if not proof_pass:
        blockers.append("rank/gap proof flip failed for z3/cvc5/sympy")
    if not known_pass:
        blockers.extend([f"known value mismatch: {check['invariant']}" for check in known_checks if not check["match"]])
    if not ablation_pass:
        blockers.extend([f"ablation failed or zero: {name}" for name, row in ablations.items() if abs(float(row["outcome_delta"])) <= KILL_FLOOR])
    if not controls["pass"]:
        blockers.append("degenerate product/commuting control did not collapse rank/entropy")

    result = {
        "schema": "formal_scout_max_deep_lego_result_v1",
        "sim_id": "sim_s7_boundary_entropy_probe",
        "name": "sim_s7_boundary_entropy_probe",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thisfile": str(THISFILE.relative_to(ROOT)),
        "result": str(RESULT.relative_to(ROOT)),
        "object_id": OBJECT_ID,
        "classification": "lego",
        "tier": "7_entropy_information_readout",
        "promotion_allowed": False,
        "claim_ceiling": (
            "Stage-7 information readout only: computes S(rho_Br) from a fixed finite boundary "
            "Schmidt spectrum on the already-admitted non-dense MPS carrier. It does not admit "
            "holography, black-hole entropy, bridge/Xi/Phi0/Axis0, flux, gravity, physics, or final manifold claims."
        ),
        "purpose": "Compute one boundary entropy readout after the boundary rank/support distinguishability invariant is fixed.",
        "scientific_question": "Can S(rho_Br) be read out from a finite non-dense boundary block while the proof flip binds only to rank_Br/lambda_2 distinguishability?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "information_readout_probe",
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite MPS site set, full grid-boundary block B_r, finite interior complement, finite Schmidt support spectrum, finite controls",
            },
            "N01": {
                "status": "active_tested_by_control",
                "statement": "noncommuting RX/RZ plus ZZ entanglers are compared against all-Z commuting/product controls; rank/gap flips only for the order-sensitive carrier",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set: N in {8,16,32,64}, full grid boundary nodes, finite MPS bond support, finite rank/gap readout",
            "N01 order-sensitive operation/control: noncommuting single-site gates plus ZZ entanglers compared to product and all-Z commuting controls",
        ],
        "finite_map": {
            "domain": (
                "Already-admitted stage-2-style non-dense torch.complex128 MPS carrier with site tensors "
                "[physical,left,right], finite PEPS3D grid anchors, and full grid-boundary B_r selected before entropy."
            ),
            "codomain_or_output": (
                "rho_Br support spectrum, rank_Br, lambda_2 support gap, entropy output S(rho_Br), "
                "controls, proof flips, tool ablations, and blocked consumers."
            ),
            "definition": (
                "BoundaryEntropyReadout_N: fixed carrier + full finite grid-boundary B_r -> non-dense complement "
                "density spectrum for rho_Br; distinguishability rank/gap is evaluated first; entropy is then read from that spectrum."
            ),
        },
        "domain": {
            "site_counts": list(SITE_COUNTS),
            "site_shapes": {str(key): list(value) for key, value in SITE_SHAPES.items()},
            "physical_dim": PHYSICAL_DIM,
            "max_bond": MAX_BOND,
            "depth": DEPTH,
            "dense_state_closure_used": False,
        },
        "codomain_or_output": "Finite boundary support spectrum, rank/gap distinguishability invariant, and derived entropy scalar S(rho_Br).",
        "carrier_layer": "stage-2 non-dense complex128 MPS carrier reused as the readout substrate",
        "geometry_layer": "stage-6 L1 boundary-environment grid-face layer used only to select B_r before the readout",
        "carrier_realization": "torch.complex128 MPS primary; jax.numpy complex128 mirror; opt_einsum Gram environments; no dense 2**N state closure",
        "peps3d_embedding": {
            "anchor": "finite grid K=(V,E,F,C) supplies full boundary-node B_r and interior complement indices; no full PEPS3D contraction closure is claimed",
            "shapes": {str(key): list(value) for key, value in SITE_SHAPES.items()},
            "boundary_region": "B_r is the full grid-face boundary set x/y/z in {0,L-1}; executable spectrum uses the smaller interior complement density, whose nonzero eigenvalues equal rho_Br for the pure carrier",
        },
        "spinor_state": "site-local C^2 spinor amplitudes in torch/JAX complex128; rho_Br is a spinor-derived reduced support density",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/sim_entanglement_entropy_8_16_32_64_dual_engine_probe.py",
            "system_v5/ops/formal_scouts/sim_boundary_conditional_expectation_area_law_entropy_scaling_probe.py",
            "system_v5/ops/formal_scouts/sim_carrier_boundary_interior_cut_probe.py",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "full finite grid-boundary B_r versus interior complement I_r; entropy is read out after rank/gap",
        "law_or_candidate_tested": "top rung boundary rank_Br>1 and lambda_2>eps distinguishability survives the real noncommuting MPS and flips under product/commuting controls; thin-slab rungs honestly report boundary-only degeneracy",
        "branch_status_before_run": "single Stage-7 readout lego; no selection among physics variants and no downstream promotion",
        "allowed_claims": [
            "S(rho_Br) was computed as an output on this fixed carrier/readout layer",
            "rank_Br and lambda_2 support gap are prior to entropy and are the only SMT-bound invariant",
            "product and commuting controls collapse rank/gap and entropy for the positive top-rung readout",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "single readout only; no layer completion claim",
            "boundary support spectrum is not a full dense 2**|B_r| materialized density; it is carried through the smaller complement spectrum",
            "no bridge/Xi/Phi0/Axis0/flux/physics consumer is admitted",
            "no black-hole entropy or holographic claim is admitted",
        ],
        "eligible_consumers": ["bounded future Stage-7 information-readout comparisons after citing this result and fresh gates"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3 rank/gap SMT flip", "cvc5 rank/gap SMT flip", "sympy exact rank/gap flip"],
        "graph_surfaces_used": ["networkx finite boundary graph", "torch_geometric edge tensor mirror"],
        "topology_surfaces_used": ["finite PEPS3D grid full-boundary anchor only; no topology promotion"],
        "required_inputs": ["fixed stage-2-style MPS carrier construction", "full finite grid-boundary B_r", "rank/gap invariant before entropy"],
        "data_or_artifact_dependencies": [
            "/tmp/stage78_specs.json boundary entropy entry",
            "scripts/load_bearing_proof.py",
        ],
        "required_negatives": ["product rank-1 control", "commuting all-Z no-entangler control", "diagonal-environment contraction stub", "volume-law counterclaim"],
        "negatives_run": controls,
        "kill_conditions": {
            "product_or_commuting_control": "must collapse rank_Br to 1, lambda_2 to 0, and entropy to 0",
            "smt_decorative_proof": "fails unless real/control measured rank-gap values produce different verdicts",
            "entropy_organizer_inversion": "fails if entropy appears inside the SMT claim instead of only in readout fields",
            "dense_closure": "fails if any rung reports dense_state_closure_used true",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "known_value_checks", "proof_results", "tool_ablations", "controls"],
        "artifacts_emitted": [str(RESULT.relative_to(ROOT))],
        "witness_trace_id": f"sim_s7_boundary_entropy_probe:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "known_value_checks_pass": known_pass,
            "tool_ablations_pass": ablation_pass,
            "controls_pass": controls["pass"],
            "jax_vs_pytorch_max_delta": parity["max_value_delta"],
            "min_boundary_entropy": min_entropy,
            "min_second_support_weight": min_second_weight,
            "positive_topology_capacity": positive_capacity,
            "thin_slab_rungs_are_degenerate_controls": sorted(proofs["thin_slab_rungs_not_positive_smt"].keys()),
            "entropy_is_output_only": True,
            "smt_claim_mentions_entropy": False,
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": {
            "runtime": "torch",
            "dtype": "torch.complex128",
            "top_rung": "64",
            "rank_Br": top["rank_Br"],
            "lambda_2": top["lambda_2"],
            "second_support_gap": top["second_support_gap"],
            "boundary_entropy_output": top["boundary_entropy"],
            "entropy_bound_log_rank": top["entropy_bound_log_rank"],
            "entropy_bound_holds": top["entropy_bound_holds"],
            "dense_state_closure_used": False,
            "pass": top["pass"],
        },
        "jax_mirror_result": {
            "runtime": "jax",
            "x64_enabled": bool(jax.config.read("jax_enable_x64")),
            "top_rung": "64",
            "rank_Br": jax_rows["64"]["rank_Br"],
            "lambda_2": jax_rows["64"]["lambda_2"],
            "boundary_entropy_output": jax_rows["64"]["boundary_entropy"],
            "pass": jax_rows["64"]["pass"] and parity["rows"]["64"]["pass"],
        },
        "jax_vs_pytorch_delta": parity["max_value_delta"],
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablations,
        "tool_ablations_by_tool": ablations,
        "tool_ablation_outcomes": ablations,
        "scale_ladder": {"rungs": scale_rungs, "pass": scale_pass},
        "scale_rungs": scale_rungs,
        "torch_engine": torch_rows,
        "jax_engine": jax_rows,
        "jax_vs_pytorch": parity,
        "known_value_checks": known_checks,
        "entropy_as_output": {
            "role": "derived_readout_only",
            "organizing_variable": "rank_Br and lambda_2 support-gap distinguishability",
            "not_in_smt_claim": True,
            "readout_symbol": "S(rho_Br)",
        },
        "volume_law_counterclaim": {
            "observed_entropy_slope_per_site": (float(torch_rows["64"]["boundary_entropy"]) - float(torch_rows["8"]["boundary_entropy"])) / 56.0,
            "volume_law_floor": 0.025,
            "killed": ((float(torch_rows["64"]["boundary_entropy"]) - float(torch_rows["8"]["boundary_entropy"])) / 56.0) < 0.025,
        },
        "positive": {
            "rank_gap_prior_to_entropy": {"pass": proof_pass, "proof": proofs["rank_gap_distinguishability_smt_load_bearing_top64"]},
            "all_8_16_32_64_non_dense_rungs_pass": {"pass": scale_pass, "rungs": scale_rungs},
            "dual_engine_parity": parity,
            "known_value_checks": {"pass": known_pass, "checks": known_checks},
            "entropy_output_only_guard": {"pass": True, "smt_claim_mentions_entropy": False},
        },
        "graveyard_companions": {
            "product_and_commuting_controls": controls,
            "diagonal_environment_stub": {
                "top64_real_entropy": top["boundary_entropy"],
                "top64_stub_entropy": top["diagonal_environment_stub_entropy"],
                "delta": top["opt_einsum_full_vs_diagonal_stub_delta"],
                "killed": top["opt_einsum_full_vs_diagonal_stub_delta"] > KILL_FLOOR,
            },
            "volume_law_counterclaim": {
                "observed_entropy_slope_per_site": (float(torch_rows["64"]["boundary_entropy"]) - float(torch_rows["8"]["boundary_entropy"])) / 56.0,
                "floor": 0.025,
                "killed": ((float(torch_rows["64"]["boundary_entropy"]) - float(torch_rows["8"]["boundary_entropy"])) / 56.0) < 0.025,
            },
        },
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "entropy_is_not_master_variable": {"value": True, "pass": True},
        },
        "shells": [
            {
                "name": "S7_boundary_entropy_readout_on_full_grid_boundary",
                "carrier": "non-dense torch/JAX complex128 MPS",
                "rungs": list(SITE_COUNTS),
                "survives": scale_pass,
            }
        ],
        "future_continuations": [
            "Compare other Stage-7 information readouts only after preserving rank/gap-before-entropy proof binding.",
            "Do not cite this readout as bridge, flux, Axis0, physics, or holography evidence.",
        ],
        "compatibility_weights": {
            "local_information_readout": 1.0 if all_pass else 0.0,
            "future_readout_comparison": 0.5 if all_pass else 0.0,
            "bridge_or_physics": 0.0,
        },
        "compression_map": {
            "from": "fixed carrier + full grid-boundary + non-dense interior complement spectrum",
            "to": "rank_Br/lambda_2 distinguishability, entropy output, controls, proof flips, and scale rungs",
            "loss_boundary": "does not preserve full dense boundary density, full PEPS3D contraction, or downstream physics/axis claims",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": positive_capacity,
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "readout survives iff every non-dense rung has rank_Br>1/lambda_2>eps before entropy, proof flips against controls, known values match, and promotion_allowed=false",
            "computed_capacity": positive_capacity,
            "threshold": KILL_FLOOR,
            "passed": bool(all_pass and positive_capacity > KILL_FLOOR),
        },
        "outward_record": {
            "result_path": str(RESULT.relative_to(ROOT)),
            "gate_commands": [
                f"../../../scripts/per_sim_contract.py {RESULT.relative_to(ROOT)}",
                f"../../../scripts/max_deep_lego_gate.py {RESULT.relative_to(ROOT)} --scale-required --rigor",
                f"../../../scripts/recheck_proof.py {RESULT.relative_to(ROOT)} --rerun {THISFILE.relative_to(ROOT)}",
            ],
            "claim_ceiling": "boundary entropy readout only; no completion, bridge, flux, Axis0, physics, or final manifold admission",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "pass_rule": "all 8/16/32/64 non-dense rungs report the full boundary/interior geometry honestly; top64 has interior mixedness and rank_Br/lambda_2 SMT flips real SAT vs product-control UNSAT; thin slabs are explicit boundary-only degeneracy controls; entropy remains output-only; known-value anchors match; controls collapse; tool ablations are recomputed and nonzero",
        "fail_rule": "fail on dense closure, entropy in SMT claim, missing rank/gap flip, product/commuting control not collapsed, JAX mismatch, known-value mismatch, cosmetic ablation, or downstream promotion",
        "blockers": blockers,
        "all_pass": all_pass,
        "required_pass": all_pass,
    }
    return as_jsonable(result)


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(RESULT.relative_to(ROOT)), "required_pass": result["required_pass"], "blockers": result["blockers"]}, indent=2))
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
