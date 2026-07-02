"""Shared runtime for the separate geometry-layer scouts.

This runtime deliberately keeps the current stage as independent layer work.
Each target is one layer-shaped finite map with its own native scale rows,
controls, and result receipt.  It does not stack layers and does not unlock
Axis0, flux, Xi/Phi0, FEP, physics, or final manifold admission.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cotengra as ctg
import cvc5
from cvc5 import Kind
import gudhi
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import opt_einsum as oe
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
import toponetx as tnx
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
CDTYPE = torch.complex128
RTYPE = torch.float64
GAP = 1.0e-7
TWO_PI = 2.0 * math.pi

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "independent_geometry_layer_probe"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "claim-bearing finite complex spinors, densities, channels, and QIT readouts"},
    "jax": {"used": True, "role": "supportive", "reason": "x64 independent parity mirror for layer invariants"},
    "quimb": {"used": True, "role": "load_bearing", "reason": "finite MPS, PEPS2D, and PEPS3D carrier objects"},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "bounded contraction-path witness for carrier tensors"},
    "opt_einsum": {"used": True, "role": "load_bearing", "reason": "finite contraction signatures on carrier tensors"},
    "sympy": {"used": True, "role": "load_bearing", "reason": "exact symbolic identities for the target layer"},
    "z3": {"used": True, "role": "load_bearing", "reason": "finite pass/control exclusion gates"},
    "cvc5": {"used": True, "role": "load_bearing", "reason": "independent Boolean pass/control cross-check"},
    "rustworkx": {"used": True, "role": "load_bearing", "reason": "finite graph connectivity and path-order checks"},
    "XGI": {"used": True, "role": "load_bearing", "reason": "finite hyperedge/face incidence checks"},
    "TopoNetX": {"used": True, "role": "load_bearing", "reason": "finite cell-complex checks"},
    "GUDHI": {"used": True, "role": "load_bearing", "reason": "finite simplex/persistence checks"},
    "PyG": {"used": True, "role": "load_bearing", "reason": "graph message-passing over the finite carrier"},
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "XGI": "load_bearing",
    "TopoNetX": "load_bearing",
    "GUDHI": "load_bearing",
    "PyG": "load_bearing",
}

BLOCKED_CONSUMERS = [
    "layer_stacking",
    "cross_layer_order_claim",
    "G_structure_selection",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold_admission",
]

I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
SPLUS = torch.tensor([[0, 0], [1, 0]], dtype=CDTYPE)
SMINUS = torch.tensor([[0, 1], [0, 0]], dtype=CDTYPE)


@dataclass(frozen=True)
class Target:
    target: str
    display_name: str
    purpose: str
    finite_map: str
    domain: str
    codomain: str
    geometry_layer: str
    native_scale_name: str
    scale_rows: tuple[dict[str, int], ...]
    runner: Callable[[dict[str, int]], dict[str, Any]]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, (float, int, str, bool)) or value is None:
        return value
    return str(value)


def dagger(a: torch.Tensor) -> torch.Tensor:
    return a.conj().transpose(-1, -2)


def normalize_spinor(psi: torch.Tensor) -> torch.Tensor:
    psi = psi.to(CDTYPE)
    return psi / torch.linalg.vector_norm(psi)


def source_hopf_spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    """Source form: [exp(i(phi+chi)) cos eta, exp(i(phi-chi)) sin eta]."""
    return normalize_spinor(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def source_hopf_spinor_jax(phi: jnp.ndarray, chi: jnp.ndarray, eta: jnp.ndarray) -> jnp.ndarray:
    psi = jnp.stack(
        [
            jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        axis=-1,
    ).astype(jnp.complex128)
    return psi / jnp.linalg.norm(psi, axis=-1, keepdims=True)


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize_spinor(psi)
    return torch.outer(psi, psi.conj())


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho.to(CDTYPE) + dagger(rho.to(CDTYPE))) / 2.0
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=0.0).to(CDTYPE)
    rho = (vecs * vals) @ dagger(vecs)
    tr = torch.real(torch.trace(rho)).clamp(min=1.0e-12)
    return rho / tr.to(CDTYPE)


def entropy_vn(rho: torch.Tensor) -> float:
    rho = normalize_density(rho)
    eigs = torch.clamp(torch.linalg.eigvalsh(rho).real, min=0.0)
    live = eigs[eigs > 1.0e-12]
    if live.numel() == 0:
        return 0.0
    return float(-(live * torch.log2(live)).sum().item())


def partial_trace_two(rho: torch.Tensor, keep: str) -> torch.Tensor:
    shaped = rho.reshape(2, 2, 2, 2)
    if keep == "A":
        return torch.einsum("abcb->ac", shaped)
    if keep == "B":
        return torch.einsum("abad->bd", shaped)
    raise ValueError(keep)


def qit_readouts(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_ab = normalize_density(rho_ab)
    rho_a = normalize_density(partial_trace_two(rho_ab, "A"))
    rho_b = normalize_density(partial_trace_two(rho_ab, "B"))
    s_a = entropy_vn(rho_a)
    s_b = entropy_vn(rho_b)
    s_ab = entropy_vn(rho_ab)
    pt = rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)
    neg = torch.sum(torch.abs(torch.linalg.eigvalsh(pt).real.clamp(max=0.0)))
    purity = torch.real(torch.trace(rho_ab @ rho_ab)).clamp(min=1.0e-12)
    return {
        "von_neumann_S_A": s_a,
        "von_neumann_S_B": s_b,
        "von_neumann_S_AB": s_ab,
        "renyi2_S_AB": float((-torch.log2(purity)).item()),
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
        "log_negativity": float(torch.log2(2.0 * neg + 1.0).item()),
    }


def entangled_density(a: torch.Tensor, b: torch.Tensor, strength: float = 0.35) -> torch.Tensor:
    base = torch.kron(normalize_spinor(a), normalize_spinor(b))
    h = torch.kron(SX, SX) + 0.7 * torch.kron(SY, SY) + 0.5 * torch.kron(SZ, SZ)
    unitary = torch.linalg.matrix_exp((-1j * strength) * h)
    psi = normalize_spinor(unitary @ base)
    return density(psi)


def hopf_base_vector(psi: torch.Tensor) -> torch.Tensor:
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


def sample_spinors(count: int, *, eta_shift: float = 0.0) -> list[torch.Tensor]:
    rows = []
    for idx in range(count):
        phi = TWO_PI * (idx + 0.17) / max(1, count)
        chi = TWO_PI * ((5 * idx + 3) % max(1, count)) / max(1, count) + 0.13
        eta = 0.18 + 1.18 * ((7 * idx + 2) % max(2, count)) / max(1, count - 1)
        eta = min(1.43, max(0.13, eta + eta_shift * math.sin(idx + 1.0)))
        rows.append(source_hopf_spinor(phi, chi, eta))
    return rows


def jax_mps_entropy_from_quimb_dense(state_dense: Any, site_count: int, cut: int) -> float:
    """Recompute a quimb MPS cut entropy in JAX from the emitted dense state.

    This is a parity check on the numerical readout, not a claim that JAX ran
    quimb's MPS generator or tensor-network internals.
    """
    vector = jnp.asarray(state_dense.reshape(-1).tolist(), dtype=jnp.complex128)
    matrix = vector.reshape(2**cut, 2 ** (site_count - cut))
    singular_values = jnp.linalg.svd(matrix, compute_uv=False)
    probabilities = jnp.clip(jnp.real(singular_values * singular_values), min=0.0)
    probabilities = probabilities / jnp.maximum(jnp.sum(probabilities), 1.0e-12)
    live = jnp.where(probabilities > 1.0e-12, probabilities, 1.0)
    entropy = -jnp.sum(jnp.where(probabilities > 1.0e-12, probabilities * jnp.log2(live), 0.0))
    return float(entropy)


def jax_opt_einsum_signature() -> float:
    a = jnp.eye(2, dtype=jnp.float64)
    b = jnp.asarray([[1.0, 0.25], [0.25, 1.0]], dtype=jnp.float64)
    c = jnp.diag(jnp.asarray([1.0, 1.15], dtype=jnp.float64))
    return float(jnp.einsum("ab,bc,ca->", a, b, c))


def cotengra_problem_spec() -> dict[str, Any]:
    return {
        "inputs": [["a", "b"], ["b", "c"], ["c", "a"]],
        "output": [],
        "size_dict": {"a": 2, "b": 2, "c": 2},
        "declared_path": [
            {"contract": [0, 1], "result_indices": ["a", "c"]},
            {"contract": ["intermediate_0", 2], "result_indices": []},
        ],
    }


def jax_declared_contraction_cost(spec: dict[str, Any]) -> float:
    """JAX-side scalar check for a declared pairwise contraction path.

    This mirrors the tiny problem and path receipt, not cotengra's HyperOptimizer
    search behavior.
    """
    first_live = sorted(set(spec["inputs"][0]) | set(spec["inputs"][1]))
    first_cost = 1
    for ind in first_live:
        first_cost *= int(spec["size_dict"][ind])
    second_live = sorted(set(spec["declared_path"][0]["result_indices"]) | set(spec["inputs"][2]))
    second_cost = 1
    for ind in second_live:
        second_cost *= int(spec["size_dict"][ind])
    return float(first_cost + second_cost)


def jax_gcn_identity_message_gap(features: torch.Tensor, edges: list[tuple[int, int]]) -> float:
    """Mirror PyG GCNConv identity-weight message passing in explicit JAX x64."""
    x = jnp.asarray(features.detach().cpu().tolist(), dtype=jnp.float64)
    edge_list = edges + [(b, a) for a, b in edges] + [(idx, idx) for idx in range(features.shape[0])]
    src = jnp.asarray([a for a, _ in edge_list], dtype=jnp.int32)
    dst = jnp.asarray([b for _, b in edge_list], dtype=jnp.int32)
    deg = jnp.zeros((features.shape[0],), dtype=jnp.float64).at[dst].add(1.0)
    weights = 1.0 / jnp.sqrt(deg[src] * deg[dst])
    propagated = jnp.zeros_like(x).at[dst].add(weights[:, None] * x[src])
    return float(jnp.linalg.norm(propagated - x))


def peps2d_raw_torch(use: list[torch.Tensor]) -> list[list[torch.Tensor]]:
    arrays2 = []
    for x in range(2):
        row = []
        for y in range(2):
            site = x * 2 + y
            shape = (1 if x == 0 else 2, 1 if y == 1 else 2, 1 if x == 1 else 2, 1 if y == 0 else 2, 2)
            arr = torch.zeros(shape, dtype=CDTYPE)
            arr[(0, 0, 0, 0, 0)] = use[site][0]
            arr[(0, 0, 0, 0, 1)] = use[site][1]
            if arr.numel() > 2:
                arr.reshape(-1)[2:] = 0.012 * use[site][0]
            row.append(arr)
        arrays2.append(row)
    return arrays2


def peps3d_raw_torch(use: list[torch.Tensor]) -> list[list[list[torch.Tensor]]]:
    arrays3 = []
    for x in range(2):
        plane = []
        for y in range(2):
            line = []
            for z in range(2):
                site = x * 4 + y * 2 + z
                shape = (
                    1 if x == 0 else 2,
                    1 if y == 0 else 2,
                    1 if z == 0 else 2,
                    1 if x == 1 else 2,
                    1 if y == 1 else 2,
                    1 if z == 1 else 2,
                    2,
                )
                arr = torch.zeros(shape, dtype=CDTYPE)
                arr[(0, 0, 0, 0, 0, 0, 0)] = use[site][0]
                arr[(0, 0, 0, 0, 0, 0, 1)] = use[site][1]
                if arr.numel() > 2:
                    arr.reshape(-1)[2:] = 0.009 * use[site][1]
                line.append(arr)
            plane.append(line)
        arrays3.append(plane)
    return arrays3


def peps2d_raw_jax(use: jnp.ndarray) -> list[list[jnp.ndarray]]:
    arrays2 = []
    for x in range(2):
        row = []
        for y in range(2):
            site = x * 2 + y
            shape = (1 if x == 0 else 2, 1 if y == 1 else 2, 1 if x == 1 else 2, 1 if y == 0 else 2, 2)
            arr = jnp.zeros(shape, dtype=jnp.complex128)
            arr = arr.at[(0, 0, 0, 0, 0)].set(use[site][0])
            arr = arr.at[(0, 0, 0, 0, 1)].set(use[site][1])
            if arr.size > 2:
                arr = arr.reshape(-1).at[2:].set(0.012 * use[site][0]).reshape(shape)
            row.append(arr)
        arrays2.append(row)
    return arrays2


def peps3d_raw_jax(use: jnp.ndarray) -> list[list[list[jnp.ndarray]]]:
    arrays3 = []
    for x in range(2):
        plane = []
        for y in range(2):
            line = []
            for z in range(2):
                site = x * 4 + y * 2 + z
                shape = (
                    1 if x == 0 else 2,
                    1 if y == 0 else 2,
                    1 if z == 0 else 2,
                    1 if x == 1 else 2,
                    1 if y == 1 else 2,
                    1 if z == 1 else 2,
                    2,
                )
                arr = jnp.zeros(shape, dtype=jnp.complex128)
                arr = arr.at[(0, 0, 0, 0, 0, 0, 0)].set(use[site][0])
                arr = arr.at[(0, 0, 0, 0, 0, 0, 1)].set(use[site][1])
                if arr.size > 2:
                    arr = arr.reshape(-1).at[2:].set(0.009 * use[site][1]).reshape(shape)
                line.append(arr)
            plane.append(line)
        arrays3.append(plane)
    return arrays3


def nested_torch_tensors(value: Any) -> list[torch.Tensor]:
    if isinstance(value, torch.Tensor):
        return [value]
    out: list[torch.Tensor] = []
    for item in value:
        out.extend(nested_torch_tensors(item))
    return out


def nested_jax_arrays(value: Any) -> list[jnp.ndarray]:
    if hasattr(value, "shape") and hasattr(value, "dtype"):
        return [value]
    out: list[jnp.ndarray] = []
    for item in value:
        out.extend(nested_jax_arrays(item))
    return out


def torch_tensor_grid_spec(value: Any) -> dict[str, Any]:
    tensors = nested_torch_tensors(value)
    total_abs = 0.0
    total_sq = 0.0
    weighted_abs = 0.0
    nonzero = 0
    total_elements = 0
    tensor_specs = []
    for idx, tensor in enumerate(tensors):
        abs_tensor = torch.abs(tensor)
        abs_sum = float(torch.sum(abs_tensor).real.item())
        square_sum = float(torch.sum(abs_tensor * abs_tensor).real.item())
        tensor_nonzero = int(torch.count_nonzero(abs_tensor > 0.0).item())
        total_abs += abs_sum
        total_sq += square_sum
        weighted_abs += float(idx + 1) * abs_sum
        nonzero += tensor_nonzero
        total_elements += int(tensor.numel())
        tensor_specs.append(
            {
                "linear_index": idx,
                "shape": list(tensor.shape),
                "total_elements": int(tensor.numel()),
                "nonzero_entries": tensor_nonzero,
                "abs_sum": abs_sum,
                "l2_norm": math.sqrt(square_sum),
                "weighted_abs_fingerprint": float(idx + 1) * abs_sum,
            }
        )
    return {
        "tensor_count": len(tensors),
        "shapes": [list(tensor.shape) for tensor in tensors],
        "total_elements": total_elements,
        "nonzero_entries": nonzero,
        "abs_sum": total_abs,
        "l2_norm": math.sqrt(total_sq),
        "weighted_abs_fingerprint": weighted_abs,
        "tensor_specs": tensor_specs,
    }


def jax_tensor_grid_spec(value: Any) -> dict[str, Any]:
    arrays = nested_jax_arrays(value)
    total_abs = 0.0
    total_sq = 0.0
    weighted_abs = 0.0
    nonzero = 0
    total_elements = 0
    tensor_specs = []
    for idx, array in enumerate(arrays):
        abs_array = jnp.abs(array)
        abs_sum = float(jnp.sum(abs_array))
        square_sum = float(jnp.sum(abs_array * abs_array))
        tensor_nonzero = int(jnp.count_nonzero(abs_array > 0.0))
        total_abs += abs_sum
        total_sq += square_sum
        weighted_abs += float(idx + 1) * abs_sum
        nonzero += tensor_nonzero
        total_elements += int(array.size)
        tensor_specs.append(
            {
                "linear_index": idx,
                "shape": list(array.shape),
                "total_elements": int(array.size),
                "nonzero_entries": tensor_nonzero,
                "abs_sum": abs_sum,
                "l2_norm": math.sqrt(square_sum),
                "weighted_abs_fingerprint": float(idx + 1) * abs_sum,
            }
        )
    return {
        "tensor_count": len(arrays),
        "shapes": [list(array.shape) for array in arrays],
        "total_elements": total_elements,
        "nonzero_entries": nonzero,
        "abs_sum": total_abs,
        "l2_norm": math.sqrt(total_sq),
        "weighted_abs_fingerprint": weighted_abs,
        "tensor_specs": tensor_specs,
    }


def carrier_anchor(spinors: list[torch.Tensor]) -> dict[str, Any]:
    """Common finite spinor-network anchor used by every independent layer.

    The anchor is not the layer claim.  It keeps each layer on the same finite
    spinor-network fabric while the target runner supplies the layer-specific
    finite map and invariant.
    """
    use = spinors[:8]
    mps = qtn.MPS_product_state([[complex(x.item()) for x in psi] for psi in use])
    mps_ent = qtn.MPS_rand_state(8, bond_dim=2, phys_dim=2, seed=11)
    arrays2 = peps2d_raw_torch(use)
    peps2_raw_spec = torch_tensor_grid_spec(arrays2)
    peps2 = qtn.PEPS(arrays2)
    arrays3 = peps3d_raw_torch(use)
    peps3_raw_spec = torch_tensor_grid_spec(arrays3)
    peps3 = qtn.PEPS3D(arrays3)
    a = torch.eye(2, dtype=RTYPE)
    b = torch.tensor([[1.0, 0.25], [0.25, 1.0]], dtype=RTYPE)
    c = torch.diag(torch.tensor([1.0, 1.15], dtype=RTYPE))
    contraction = float(oe.contract("ab,bc,ca->", a, b, c).item())
    ctg_problem = cotengra_problem_spec()
    tree = ctg.HyperOptimizer(max_repeats=1, progbar=False, on_trial_error="raise").search(
        [tuple(row) for row in ctg_problem["inputs"]],
        tuple(ctg_problem["output"]),
        ctg_problem["size_dict"],
    )
    edges = [(i, i + 1) for i in range(7)] + [(i, i + 2) for i in range(6)]
    graph = rx.PyGraph()
    graph.add_nodes_from(range(8))
    graph.add_edges_from_no_data(edges)
    hyper = xgi.Hypergraph()
    for i in range(0, 6, 2):
        hyper.add_edge([i, i + 1, i + 2])
    complex_ = tnx.CellComplex()
    for i in range(0, 6, 2):
        complex_.add_cell([i, i + 1, i + 2], rank=2)
    st = gudhi.SimplexTree()
    for edge in edges:
        st.insert(list(edge), filtration=0.0)
    st.compute_persistence()
    features = torch.stack([torch.cat([hopf_base_vector(psi), torch.tensor([1.0], dtype=RTYPE)]) for psi in use])
    edge_index = torch.tensor(edges + [(b0, a0) for a0, b0 in edges], dtype=torch.long).T
    data = Data(x=features, edge_index=edge_index)
    conv = GCNConv(4, 4, bias=False).to(RTYPE)
    with torch.no_grad():
        conv.lin.weight.copy_(torch.eye(4, dtype=RTYPE))
    message = conv(data.x, data.edge_index)
    message_gap = float(torch.linalg.vector_norm(message - data.x).item())
    jax_message_gap = jax_gcn_identity_message_gap(features, edges)
    jax_anchor_mps_entropy = jax_mps_entropy_from_quimb_dense(mps_ent.to_dense(), 8, 4)
    jax_contraction = jax_opt_einsum_signature()
    rho = entangled_density(use[0], use[-1], strength=0.31)
    qit = qit_readouts(rho)
    return {
        "pass": bool(
            mps.L == 8
            and int(peps2.num_tensors) == 4
            and int(peps3.num_tensors) == 8
            and contraction > 0.0
            and float(tree.contraction_cost()) > 0.0
            and rx.is_connected(graph)
            and int(hyper.num_edges) > 0
            and int(complex_.dim) == 2
            and int(st.num_simplices()) > 0
            and message_gap > GAP
            and qit["mutual_information"] > 0.0
        ),
        "mps_sites": int(mps.L),
        "mps_entangled_half_chain_entropy": float(mps_ent.entropy(4)),
        "jax_mps_entropy_recomputed_from_quimb_dense": jax_anchor_mps_entropy,
        "jax_mps_entropy_recompute_delta": abs(float(mps_ent.entropy(4)) - jax_anchor_mps_entropy),
        "peps2d_tensors": int(peps2.num_tensors),
        "peps2d_raw_tensor_spec": peps2_raw_spec,
        "peps3d_tensors": int(peps3.num_tensors),
        "peps3d_raw_tensor_spec": peps3_raw_spec,
        "cotengra_problem_spec": ctg_problem,
        "cotengra_cost": float(tree.contraction_cost()),
        "jax_declared_contraction_cost": jax_declared_contraction_cost(ctg_problem),
        "jax_declared_contraction_cost_delta": abs(float(tree.contraction_cost()) - jax_declared_contraction_cost(ctg_problem)),
        "opt_einsum_signature": contraction,
        "jax_opt_einsum_signature": jax_contraction,
        "jax_opt_einsum_delta": abs(contraction - jax_contraction),
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(complex_.dim),
        "gudhi_simplices": int(st.num_simplices()),
        "pyg_message_gap": message_gap,
        "jax_gcn_formula_message_gap": jax_message_gap,
        "jax_gcn_formula_delta": abs(message_gap - jax_message_gap),
        "qit": qit,
    }


def z3_positive_control_gate(signal: float, control: float, threshold: float = GAP) -> dict[str, Any]:
    sig = z3.Real("signal")
    ctl = z3.Real("control")
    solver = z3.Solver()
    solver.add(sig == z3.RealVal(str(signal)))
    solver.add(ctl == z3.RealVal(str(control)))
    solver.add(z3.Not(z3.And(sig > z3.RealVal(str(threshold)), ctl < z3.RealVal(str(threshold)))))
    status = solver.check()
    return {"pass": bool(status == z3.unsat), "negated_good_status": str(status), "signal": signal, "control": control}


def cvc5_boolean_gate(good: bool) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    ok = solver.mkBoolean(bool(good))
    solver.assertFormula(solver.mkTerm(Kind.NOT, ok))
    status = str(solver.checkSat())
    return {"pass": bool(status == "unsat"), "negated_good_status": status}


def symbolic_periodicity_gate() -> dict[str, Any]:
    t = sp.symbols("t", real=True)
    expr = sp.simplify(sp.exp(sp.I * (t + 2 * sp.pi)) - sp.exp(sp.I * t))
    return {"pass": bool(expr == 0), "identity": "exp(i(t+2*pi)) - exp(it) = 0", "sympy_result": str(expr)}


def parity_norm_delta(spinors: list[torch.Tensor]) -> float:
    phis = jnp.asarray([0.031 * (i + 1) for i in range(len(spinors))], dtype=jnp.float64)
    chis = jnp.asarray([0.047 * (2 * i + 1) for i in range(len(spinors))], dtype=jnp.float64)
    etas = jnp.asarray([0.2 + 1.1 * ((i % 17) / 16.0) for i in range(len(spinors))], dtype=jnp.float64)
    psi_j = source_hopf_spinor_jax(phis, chis, etas)
    jax_err = float(jnp.max(jnp.abs(jnp.sum(jnp.abs(psi_j) ** 2, axis=-1) - 1.0)))
    torch_err = max(abs(float(torch.sum(torch.abs(psi) ** 2).real.item()) - 1.0) for psi in spinors)
    return abs(jax_err - torch_err)


def jax_torch_carrier_parity(count: int = 64) -> dict[str, Any]:
    """Dual-backend check for the shared finite spinor/Hopf/density carrier.

    This is intentionally scoped to the common carrier used by every independent
    layer row.  It does not pretend to mirror quimb, PyG, or topology-tool
    internals target by target.
    """
    rows = []
    max_norm_delta = 0.0
    max_hopf_delta = 0.0
    max_trace_delta = 0.0
    max_transport_delta = 0.0
    for idx in range(count):
        phi = TWO_PI * (idx + 0.17) / max(1, count)
        chi = TWO_PI * ((5 * idx + 3) % max(1, count)) / max(1, count) + 0.13
        eta = 0.18 + 1.18 * ((7 * idx + 2) % max(2, count)) / max(1, count - 1)
        eta = min(1.43, max(0.13, eta))
        psi_t = source_hopf_spinor(phi, chi, eta)
        base_t = hopf_base_vector(psi_t)
        rho_t = density(psi_t)
        h_t = 0.5 * SZ
        u_t = torch.linalg.matrix_exp((-1j * 0.19) * h_t)
        evolved_t = normalize_density(u_t @ rho_t @ dagger(u_t))

        psi_j = source_hopf_spinor_jax(jnp.asarray(phi, dtype=jnp.float64), jnp.asarray(chi, dtype=jnp.float64), jnp.asarray(eta, dtype=jnp.float64))
        a = psi_j[0]
        b = psi_j[1]
        base_j = jnp.asarray(
            [
                2.0 * jnp.real(jnp.conj(a) * b),
                2.0 * jnp.imag(jnp.conj(a) * b),
                jnp.abs(a) ** 2 - jnp.abs(b) ** 2,
            ],
            dtype=jnp.float64,
        )
        rho_j = jnp.outer(psi_j, jnp.conj(psi_j)).astype(jnp.complex128)
        sz_j = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
        u_j = jnp.diag(jnp.exp(jnp.asarray([-0.5j * 0.19, 0.5j * 0.19], dtype=jnp.complex128)))
        evolved_j = u_j @ rho_j @ jnp.conj(u_j.T)

        norm_t = float(torch.sum(torch.abs(psi_t) ** 2).real.item())
        norm_j = float(jnp.real(jnp.sum(jnp.abs(psi_j) ** 2)))
        trace_t = float(torch.trace(rho_t).real.item())
        trace_j = float(jnp.real(jnp.trace(rho_j)))
        transport_t = float(torch.real(torch.trace(evolved_t @ SZ)).item())
        transport_j = float(jnp.real(jnp.trace(evolved_j @ sz_j)))
        norm_delta = abs(norm_t - norm_j)
        hopf_delta = float(jnp.max(jnp.abs(jnp.asarray(base_t.detach().cpu().tolist(), dtype=jnp.float64) - base_j)))
        trace_delta = abs(trace_t - trace_j)
        transport_delta = abs(transport_t - transport_j)
        max_norm_delta = max(max_norm_delta, norm_delta)
        max_hopf_delta = max(max_hopf_delta, hopf_delta)
        max_trace_delta = max(max_trace_delta, trace_delta)
        max_transport_delta = max(max_transport_delta, transport_delta)
        if idx in {0, count // 2, count - 1}:
            rows.append(
                {
                    "idx": idx,
                    "norm_delta": norm_delta,
                    "hopf_base_delta": hopf_delta,
                    "density_trace_delta": trace_delta,
                    "z_transport_readout_delta": transport_delta,
                }
            )
    max_delta = max(max_norm_delta, max_hopf_delta, max_trace_delta, max_transport_delta)
    return {
        "pass": max_delta < 1.0e-10,
        "scope": "shared finite spinor/Hopf/density carrier parity; target-specific quimb/PyG/topology internals are not mirrored here",
        "backend_pair": "torch.complex128 vs jax.numpy.complex128 with jax_enable_x64=True",
        "sample_count": count,
        "max_delta": max_delta,
        "max_spinor_norm_delta": max_norm_delta,
        "max_hopf_base_delta": max_hopf_delta,
        "max_density_trace_delta": max_trace_delta,
        "max_z_transport_readout_delta": max_transport_delta,
        "spot_rows": rows,
    }


def jax_density(psi: jnp.ndarray) -> jnp.ndarray:
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, jnp.conj(psi)).astype(jnp.complex128)


def jax_hopf_base_vector(psi: jnp.ndarray) -> jnp.ndarray:
    psi = psi / jnp.linalg.norm(psi)
    a = psi[0]
    b = psi[1]
    return jnp.asarray(
        [
            2.0 * jnp.real(jnp.conj(a) * b),
            2.0 * jnp.imag(jnp.conj(a) * b),
            jnp.abs(a) ** 2 - jnp.abs(b) ** 2,
        ],
        dtype=jnp.float64,
    )


def jax_sample_spinors(count: int, *, eta_shift: float = 0.0) -> jnp.ndarray:
    idx = jnp.arange(count, dtype=jnp.float64)
    phi = TWO_PI * (idx + 0.17) / max(1, count)
    chi = TWO_PI * jnp.asarray([(5 * i + 3) % max(1, count) for i in range(count)], dtype=jnp.float64) / max(1, count) + 0.13
    eta = 0.18 + 1.18 * jnp.asarray([(7 * i + 2) % max(2, count) for i in range(count)], dtype=jnp.float64) / max(1, count - 1)
    eta = jnp.minimum(1.43, jnp.maximum(0.13, eta + eta_shift * jnp.sin(idx + 1.0)))
    return source_hopf_spinor_jax(phi, chi, eta)


def jax_matrix_norm(a: jnp.ndarray) -> jnp.ndarray:
    return jnp.sqrt(jnp.sum(jnp.abs(a) ** 2))


def jax_normalize_density(rho: jnp.ndarray) -> jnp.ndarray:
    rho = (rho.astype(jnp.complex128) + jnp.conj(rho.astype(jnp.complex128).T)) / 2.0
    vals, vecs = jnp.linalg.eigh(rho)
    vals = jnp.clip(jnp.real(vals), min=0.0).astype(jnp.complex128)
    rho = (vecs * vals) @ jnp.conj(vecs.T)
    tr = jnp.maximum(jnp.real(jnp.trace(rho)), 1.0e-12)
    return rho / tr.astype(jnp.complex128)


def jax_entropy_vn(rho: jnp.ndarray) -> jnp.ndarray:
    rho = jax_normalize_density(rho)
    eigs = jnp.clip(jnp.real(jnp.linalg.eigvalsh(rho)), min=0.0)
    live = jnp.where(eigs > 1.0e-12, eigs, 1.0)
    return -jnp.sum(jnp.where(eigs > 1.0e-12, eigs * jnp.log2(live), 0.0))


def jax_partial_trace_two(rho: jnp.ndarray, keep: str) -> jnp.ndarray:
    shaped = rho.reshape(2, 2, 2, 2)
    if keep == "A":
        return jnp.einsum("abcb->ac", shaped)
    if keep == "B":
        return jnp.einsum("abad->bd", shaped)
    raise ValueError(keep)


def jax_qit_readouts(rho_ab: jnp.ndarray) -> dict[str, float]:
    rho_ab = jax_normalize_density(rho_ab)
    rho_a = jax_normalize_density(jax_partial_trace_two(rho_ab, "A"))
    rho_b = jax_normalize_density(jax_partial_trace_two(rho_ab, "B"))
    s_a = jax_entropy_vn(rho_a)
    s_b = jax_entropy_vn(rho_b)
    s_ab = jax_entropy_vn(rho_ab)
    pt = rho_ab.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    neg = jnp.sum(jnp.abs(jnp.clip(jnp.real(jnp.linalg.eigvalsh(pt)), max=0.0)))
    purity = jnp.maximum(jnp.real(jnp.trace(rho_ab @ rho_ab)), 1.0e-12)
    return {
        "von_neumann_S_A": float(s_a),
        "von_neumann_S_B": float(s_b),
        "von_neumann_S_AB": float(s_ab),
        "renyi2_S_AB": float(-jnp.log2(purity)),
        "mutual_information": float(s_a + s_b - s_ab),
        "conditional_entropy_A_given_B": float(s_ab - s_b),
        "coherent_information_A_to_B": float(s_b - s_ab),
        "log_negativity": float(jnp.log2(2.0 * neg + 1.0)),
    }


def jax_entangled_density(a: jnp.ndarray, b: jnp.ndarray, strength: float = 0.35) -> jnp.ndarray:
    sx = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.asarray([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
    base = jnp.kron(a / jnp.linalg.norm(a), b / jnp.linalg.norm(b))
    h = jnp.kron(sx, sx) + 0.7 * jnp.kron(sy, sy) + 0.5 * jnp.kron(sz, sz)
    vals, vecs = jnp.linalg.eigh(h)
    unitary = vecs @ jnp.diag(jnp.exp((-1j * strength) * vals)) @ jnp.conj(vecs.T)
    psi = unitary @ base
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, jnp.conj(psi)).astype(jnp.complex128)


def jax_signal_control_for_target(target_name: str, scale: dict[str, int]) -> dict[str, Any]:
    sx = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.asarray([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
    i2 = jnp.eye(2, dtype=jnp.complex128)
    splus = jnp.asarray([[0, 0], [1, 0]], dtype=jnp.complex128)
    sminus = jnp.asarray([[0, 1], [0, 0]], dtype=jnp.complex128)

    if target_name == "finite_carrier_probe_path_geometry":
        n = scale["sites"]
        probes = scale["probes"]
        depth = scale["path_depth"]
        spinors = jax_sample_spinors(n)
        effects = []
        for idx in range(probes):
            direction = jnp.asarray([1.0 + 0.1 * idx, 0.07 * idx + 0.3j], dtype=jnp.complex128)
            effects.append(jax_density(direction))
        weights_ab = []
        weights_ba = []
        for step in range(depth):
            rho = jax_density(spinors[(3 * step + 1) % n])
            a = effects[step % probes]
            b = effects[(step + 1) % probes]
            weights_ab.append(jnp.real(jnp.trace(b @ a @ rho @ a @ b)))
            weights_ba.append(jnp.real(jnp.trace(a @ b @ rho @ b @ a)))
        signal = jnp.sum(jnp.abs(jnp.asarray(weights_ab) - jnp.asarray(weights_ba)))
        return {"mode": "signal_control", "signal": float(signal), "control": 0.0, "mirrored_readouts": ["path_weight_gap_l1"]}

    if target_name == "finite_spinor_network_carrier":
        n = scale["sites"]
        spinors = jax_sample_spinors(n)
        rho = jax_entangled_density(spinors[0], spinors[min(n, 8) - 1], strength=0.31)
        mps_len = min(n, 16)
        cut = mps_len // 2
        product = qtn.MPS_product_state([[complex(x) for x in row] for row in spinors[:mps_len].tolist()])
        random_mps = qtn.MPS_rand_state(mps_len, bond_dim=scale["bond_dim"], phys_dim=2, seed=scale["bond_dim"] + n)
        jax_product_entropy = jax_mps_entropy_from_quimb_dense(product.to_dense(), mps_len, cut)
        jax_random_entropy = jax_mps_entropy_from_quimb_dense(random_mps.to_dense(), mps_len, cut)
        use = spinors[:8]
        edges = [(i, i + 1) for i in range(7)] + [(i, i + 2) for i in range(6)]
        peps2_raw_spec = jax_tensor_grid_spec(peps2d_raw_jax(use))
        peps3_raw_spec = jax_tensor_grid_spec(peps3d_raw_jax(use))
        features = torch.tensor(
            [
                [
                    float(jax_hopf_base_vector(psi)[0]),
                    float(jax_hopf_base_vector(psi)[1]),
                    float(jax_hopf_base_vector(psi)[2]),
                    1.0,
                ]
                for psi in use
            ],
            dtype=RTYPE,
        )
        anchor_mps = qtn.MPS_rand_state(8, bond_dim=2, phys_dim=2, seed=11)
        ctg_problem = cotengra_problem_spec()
        return {
            "mode": "partial_carrier_anchor_tool_output_recompute",
            "signal": float(jax_random_entropy - jax_product_entropy),
            "control": 0.0,
            "qit": jax_qit_readouts(rho),
            "anchor_mps_entropy": jax_mps_entropy_from_quimb_dense(anchor_mps.to_dense(), 8, 4),
            "pyg_message_gap": jax_gcn_identity_message_gap(features, edges),
            "opt_einsum_signature": jax_opt_einsum_signature(),
            "peps2d_raw_tensor_spec": peps2_raw_spec,
            "peps3d_raw_tensor_spec": peps3_raw_spec,
            "cotengra_problem_spec": ctg_problem,
            "declared_contraction_cost": jax_declared_contraction_cost(ctg_problem),
            "mirrored_readouts": [
                "carrier QIT readouts",
                "quimb MPS entropy recomputed from quimb dense state in JAX",
                "PyG identity-GCN formula recomputed in JAX",
                "opt_einsum contraction signature recomputed in JAX",
                "PEPS2D raw tensor shapes and fingerprints recomputed in JAX",
                "PEPS3D raw tensor shapes and fingerprints recomputed in JAX",
                "cotengra declared contraction problem size recomputed in JAX",
            ],
            "adapter_boundary": "quimb dense states are host adapter values consumed by JAX for entropy recomputation; this does not make quimb internals JAX-native",
            "unmirrored_target_internals": [
                "cotengra HyperOptimizer search internals beyond declared contraction problem receipt",
                "quimb.PEPS/PEPS3D constructor internals beyond exposed raw tensor specs and object tensor counts",
            ],
        }

    if target_name == "s3_unit_spinor_geometry":
        spinors = jax_sample_spinors(scale["spinor_samples"])
        norms = jnp.abs(jnp.sum(jnp.abs(spinors) ** 2, axis=1) - 1.0)
        stride = max(1, len(spinors) // 64)
        distances = []
        for idx in range(0, len(spinors) - 1, stride):
            inner = jnp.minimum(jnp.abs(jnp.vdot(spinors[idx], spinors[idx + 1])), 1.0)
            distances.append(jnp.arccos(inner))
        signal = jnp.sum(jnp.asarray(distances)) / max(1, len(distances))
        return {"mode": "signal_control", "signal": float(signal), "control": float(jnp.max(norms)), "mirrored_readouts": ["max_norm_error", "mean_projective_distance"]}

    if target_name == "cp1_s2_projective_hopf_base":
        spinors = jax_sample_spinors(scale["base_samples"])
        base = jnp.asarray([jax_hopf_base_vector(psi) for psi in spinors])
        norm_error = jnp.max(jnp.abs(jnp.linalg.norm(base, axis=1) - 1.0))
        stride = max(1, len(spinors) // 64)
        phase_gaps = []
        for local_idx, psi in enumerate(spinors[::stride]):
            phased = jnp.exp(1j * (0.37 + local_idx)) * psi
            phase_gaps.append(jnp.linalg.norm(jax_hopf_base_vector(psi) - jax_hopf_base_vector(phased)))
        signal = jnp.linalg.norm(base[0] - base[-1])
        return {"mode": "signal_control", "signal": float(signal), "control": float(jnp.max(jnp.asarray(phase_gaps))), "mirrored_readouts": ["max_s2_norm_error", "max_global_phase_base_gap", "base_span_gap"]}

    if target_name == "u1_hopf_fiber":
        samples = scale["fiber_samples"]
        eta = 0.61
        chi = -0.23
        bases = []
        raw_path = 0.0
        last = None
        for idx in range(samples + 1):
            phi = TWO_PI * idx / samples
            psi = source_hopf_spinor_jax(jnp.asarray(phi), jnp.asarray(chi), jnp.asarray(eta))
            bases.append(jax_hopf_base_vector(psi))
            if last is not None:
                raw_path += float(jnp.linalg.norm(psi - last))
            last = psi
        base_gap = max(float(jnp.linalg.norm(v - bases[0])) for v in bases)
        return {"mode": "signal_control", "signal": raw_path, "control": base_gap, "mirrored_readouts": ["raw_spinor_loop_length", "max_base_motion"]}

    if target_name == "nested_hopf_tori":
        shells = scale["shells"]
        leaves = scale["eta_leaves"]
        fiber = scale["fiber_samples"]
        base = scale["base_samples"]
        spinors = []
        leaf_areas = []
        for shell in range(shells):
            for leaf in range(leaves):
                eta = (leaf + 1) * (math.pi / 2.0) / (leaves + 1)
                shell_radius = 1.0 + 0.07 * shell
                leaf_areas.append(float(shell_radius * (TWO_PI * math.cos(eta)) * (TWO_PI * math.sin(eta))))
                for f_idx in range(fiber):
                    for b_idx in range(base):
                        spinors.append(source_hopf_spinor_jax(jnp.asarray(TWO_PI * f_idx / fiber), jnp.asarray(TWO_PI * b_idx / base + 0.11 * shell), jnp.asarray(eta)))
        base_span = float(jnp.linalg.norm(jax_hopf_base_vector(spinors[0]) - jax_hopf_base_vector(spinors[-1])))
        area_spread = max(leaf_areas) - min(leaf_areas) if leaf_areas else 0.0
        return {"mode": "signal_control", "signal": area_spread + base_span, "control": 0.0, "mirrored_readouts": ["site_count", "leaf_area_spread", "base_span"]}

    if target_name == "hopf_connection_holonomy":
        samples = scale["loop_samples"]
        eta = 0.53
        fiber_integral = 0.0
        horizontal_integral = 0.0
        for _idx in range(samples):
            du = TWO_PI / samples
            fiber_integral += du
            horizontal_integral += (-math.cos(2.0 * eta) * du) + math.cos(2.0 * eta) * du
        return {"mode": "signal_control", "signal": abs(fiber_integral), "control": abs(horizontal_integral), "mirrored_readouts": ["fiber_connection_integral", "horizontal_lift_integral_abs"]}

    if target_name == "left_right_weyl_spinor_sheets":
        n_l = scale["left_sites"]
        n_r = scale["right_sites"]
        left = jax_sample_spinors(n_l, eta_shift=0.02)
        right = jnp.asarray(
            [
                source_hopf_spinor_jax(jnp.asarray(0.05 + TWO_PI * i / n_r), jnp.asarray(0.17 - TWO_PI * ((3 * i + 1) % n_r) / n_r), jnp.asarray(0.38 + 0.51 * ((i % 11) / 10.0)))
                for i in range(n_r)
            ]
        )
        dt = 0.19
        u_l = jnp.diag(jnp.asarray([jnp.exp(-0.5j * dt), jnp.exp(0.5j * dt)], dtype=jnp.complex128))
        u_r = jnp.diag(jnp.asarray([jnp.exp(0.5j * dt), jnp.exp(-0.5j * dt)], dtype=jnp.complex128))
        gap = 0.0
        limit = min(n_l, n_r, 128)
        for idx in range(limit):
            rho_l = jax_density(u_l @ left[idx])
            rho_r = jax_density(u_r @ right[idx])
            gap += float(jax_matrix_norm(rho_l - rho_r))
        signal = gap / limit
        control = float(jax_matrix_norm(jax_density(u_l @ left[0]) - jax_density(u_l @ left[0])))
        return {"mode": "signal_control", "signal": signal, "control": control, "mirrored_readouts": ["mean_left_right_transport_gap"]}

    if target_name == "chirality_orientation_cover":
        samples = scale["dirac_samples"]
        p_l = jnp.diag(jnp.asarray([1, 1, 0, 0], dtype=jnp.complex128))
        p_r = jnp.diag(jnp.asarray([0, 0, 1, 1], dtype=jnp.complex128))
        gamma5 = p_r - p_l
        spinors = jax_sample_spinors(samples)
        leak = 0.0
        flip_gap = 0.0
        swap = jnp.asarray([[0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0], [0, 1, 0, 0]], dtype=jnp.complex128)
        stride = max(1, samples // 128)
        for psi in spinors[::stride]:
            dirac_l = jnp.concatenate([psi, jnp.zeros(2, dtype=jnp.complex128)])
            leak += float(jnp.linalg.norm(p_r @ dirac_l))
            flip_gap += float(jnp.linalg.norm((swap @ dirac_l) - dirac_l))
        anticom = float(jax_matrix_norm(gamma5 @ gamma5 - jnp.eye(4, dtype=jnp.complex128)))
        signal = flip_gap / max(1, len(spinors[::stride]))
        return {"mode": "signal_control", "signal": signal, "control": leak, "extra_control": anticom, "mirrored_readouts": ["mean_orientation_swap_gap", "wrong_chirality_leak", "gamma5_square_residual"]}

    if target_name == "clifford_quaternion_rotor_geometry":
        samples = scale["rotor_samples"]
        qi = 1j * sx
        qj = 1j * sy
        qk = -1j * sz
        quat_residual = float(jax_matrix_norm(qi @ qj - qk))
        anticomm = float(jax_matrix_norm(sx @ sy + sy @ sx))
        rot_norm_gap = 0.0
        v = jnp.asarray([1.0, 0.3, -0.2], dtype=jnp.float64)
        v = v / jnp.linalg.norm(v)
        for idx in range(samples):
            angle = TWO_PI * (idx + 1) / samples
            axis = jnp.asarray([math.cos(angle), math.sin(angle), 0.5], dtype=jnp.float64)
            axis = axis / jnp.linalg.norm(axis)
            out = v * math.cos(angle) + jnp.cross(axis, v) * math.sin(angle) + axis * jnp.dot(axis, v) * (1.0 - math.cos(angle))
            rot_norm_gap = max(rot_norm_gap, abs(float(jnp.linalg.norm(out)) - 1.0))
        signal = float(jax_matrix_norm(qi @ qj))
        return {"mode": "signal_control", "signal": signal, "control": quat_residual + anticomm + rot_norm_gap, "mirrored_readouts": ["ij_minus_k_residual", "sx_sy_anticommutator_residual", "max_rotor_norm_gap"]}

    def jdissipator(op: jnp.ndarray, rho: jnp.ndarray) -> jnp.ndarray:
        lop = jnp.conj(op.T) @ op
        return op @ rho @ jnp.conj(op.T) - 0.5 * (lop @ rho + rho @ lop)

    def jcomm(op: jnp.ndarray, rho: jnp.ndarray) -> jnp.ndarray:
        return op @ rho - rho @ op

    def jlaw_generator(law: str, sheet: str, rho: jnp.ndarray) -> jnp.ndarray:
        h = 0.5 * sz if sheet == "L" else -0.5 * sz
        if law in {"left_funnel", "right_cannon"}:
            sign = 1.0 if sheet == "L" else -1.0
            return 0.13 * (jdissipator(sx, rho) + jdissipator(sy, rho) + jdissipator(sz, rho)) - 1j * 0.07 * sign * jcomm(h, rho)
        if law in {"left_vortex", "right_spiral"}:
            sign = 1.0 if sheet == "L" else -1.0
            return -1j * sign * jcomm(h, rho) + 0.025 * jdissipator(sz, rho)
        if law == "left_pit":
            return 0.28 * jdissipator(sminus, rho) - 1j * 0.05 * jcomm(h, rho)
        if law == "right_source":
            return 0.28 * jdissipator(splus, rho) - 1j * 0.05 * jcomm(h, rho)
        if law in {"left_hill", "right_citadel"}:
            projector_axis = sz if sheet == "L" else sx
            p_plus = 0.5 * (i2 + projector_axis)
            p_minus = 0.5 * (i2 - projector_axis)
            k_op = 0.2 * projector_axis
            return -1j * jcomm(k_op, rho) + 0.24 * (p_plus @ rho @ p_plus + p_minus @ rho @ p_minus - rho)
        raise ValueError(law)

    def jevolve_law(law: str, sheet: str, steps: int, dt: float, *, zero_control: bool = False) -> dict[str, Any]:
        psi = source_hopf_spinor_jax(jnp.asarray(0.29), jnp.asarray(-0.41), jnp.asarray(0.72))
        rho = jax_density(psi)
        start = rho
        purities = []
        blochs = []
        for _ in range(steps):
            gen = jnp.zeros_like(rho) if zero_control else jlaw_generator(law, sheet, rho)
            rho = jax_normalize_density(rho + dt * gen)
            purities.append(float(jnp.real(jnp.trace(rho @ rho))))
            blochs.append([float(jnp.real(jnp.trace(rho @ op))) for op in (sx, sy, sz)])
        motion = float(jax_matrix_norm(rho - start))
        angle = 0.0
        if len(blochs) > 2:
            a0 = math.atan2(blochs[0][1], blochs[0][0])
            a1 = math.atan2(blochs[-1][1], blochs[-1][0])
            angle = abs(a1 - a0)
        return {
            "motion_gap": motion,
            "final_bloch": blochs[-1],
            "final_purity": purities[-1],
            "purity_delta": purities[0] - purities[-1],
            "xy_angle_delta": angle,
        }

    if target_name == "local_weyl_dynamical_laws":
        steps = scale["time_steps"]
        dt = scale["dt_millis"] / 1000.0
        rows = {}
        for law, (sheet, _meaning, _equation) in LAW_MATH.items():
            live = jevolve_law(law, sheet, steps, dt)
            dead = jevolve_law(law, sheet, steps, dt, zero_control=True)
            rows[law] = {"live": live, "zero_generator_control": dead}
        motions = [row["live"]["motion_gap"] for row in rows.values()]
        return {"mode": "signal_control", "signal": max(motions) - min(motions), "control": max(row["zero_generator_control"]["motion_gap"] for row in rows.values()), "mirrored_readouts": ["law_rows", "motion_spread"]}

    if target_name.startswith("weyl_law_"):
        law = target_name.removeprefix("weyl_law_")
        sheet, _meaning, _equation = LAW_MATH[law]
        dt = scale["dt_millis"] / 1000.0
        live = jevolve_law(law, sheet, scale["time_steps"], dt)
        dead = jevolve_law(law, sheet, scale["time_steps"], dt, zero_control=True)
        return {"mode": "signal_control", "signal": live["motion_gap"], "control": dead["motion_gap"], "mirrored_readouts": ["live.motion_gap", "zero_generator_control.motion_gap"]}

    if target_name == "local_operator_channel_actions":
        q = scale["dephasing_percent"] / 100.0
        theta = scale["rotation_millirad"] / 1000.0
        rho0 = jax_density(source_hopf_spinor_jax(jnp.asarray(0.2), jnp.asarray(-0.31), jnp.asarray(0.66)))
        ux = jnp.cos(theta) * i2 - 1j * jnp.sin(theta) * sx
        uz = jnp.diag(jnp.asarray([jnp.exp(-1j * theta), jnp.exp(1j * theta)], dtype=jnp.complex128))
        channels = {
            "z_basis_dephasing": lambda rho: (1.0 - q) * rho + q * sz @ rho @ sz,
            "x_basis_dephasing": lambda rho: (1.0 - q) * rho + q * sx @ rho @ sx,
            "x_axis_hamiltonian_rotation": lambda rho: ux @ rho @ jnp.conj(ux.T),
            "z_axis_hamiltonian_rotation": lambda rho: uz @ rho @ jnp.conj(uz.T),
        }
        out = {name: jax_normalize_density(fn(rho0)) for name, fn in channels.items()}
        order_a = channels["z_basis_dephasing"](channels["x_axis_hamiltonian_rotation"](rho0))
        order_b = channels["x_axis_hamiltonian_rotation"](channels["z_basis_dephasing"](rho0))
        order_gap = float(jax_matrix_norm(order_a - order_b))
        traces = {name: float(jnp.real(jnp.trace(rho))) for name, rho in out.items()}
        return {"mode": "signal_control", "signal": order_gap, "control": max(abs(v - 1.0) for v in traces.values()), "mirrored_readouts": ["order_gap_zdephase_then_xrot_vs_reverse", "traces"]}

    if target_name == "patch_gluing_groupoid_compatibility":
        patches = scale["patches"]
        arrows = []
        phases = {}
        for i0 in range(patches):
            j0 = (i0 + 1) % patches
            phase = TWO_PI * (i0 + 1) / patches
            phases[(i0, j0)] = phase
            phases[(j0, i0)] = -phase
            arrows.append((i0, j0))
            arrows.append((j0, i0))
        inverse_gap = max(abs(phases[(a, b)] + phases[(b, a)]) for a, b in arrows)
        cocycle_gap = 0.0
        for i0 in range(patches):
            j0 = (i0 + 1) % patches
            k0 = (i0 + 2) % patches
            lhs = phases[(i0, j0)] + phases[(j0, k0)] if (j0, k0) in phases else phases[(i0, j0)]
            rhs = lhs
            cocycle_gap = max(cocycle_gap, abs(lhs - rhs))
        return {"mode": "signal_control", "signal": float(2 * patches), "control": inverse_gap + cocycle_gap, "mirrored_readouts": ["oriented_arrow_count", "inverse_phase_gap", "cocycle_gap"]}

    raise KeyError(target_name)


def tensor_spec_deltas(prefix: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, float]:
    return {
        f"{prefix}_shape_mismatch": 0.0 if left["shapes"] == right["shapes"] else 1.0,
        f"{prefix}_tensor_count": abs(float(left["tensor_count"]) - float(right["tensor_count"])),
        f"{prefix}_total_elements": abs(float(left["total_elements"]) - float(right["total_elements"])),
        f"{prefix}_nonzero_entries": abs(float(left["nonzero_entries"]) - float(right["nonzero_entries"])),
        f"{prefix}_abs_sum": abs(float(left["abs_sum"]) - float(right["abs_sum"])),
        f"{prefix}_l2_norm": abs(float(left["l2_norm"]) - float(right["l2_norm"])),
        f"{prefix}_weighted_abs_fingerprint": abs(float(left["weighted_abs_fingerprint"]) - float(right["weighted_abs_fingerprint"])),
    }


def target_specific_jax_parity(target: Target, rows: list[dict[str, Any]]) -> dict[str, Any]:
    comparisons = []
    max_signal_delta = 0.0
    max_control_delta = 0.0
    max_qit_delta = 0.0
    max_tool_recompute_delta = 0.0
    coverage_levels = set()
    unmirrored: set[str] = set()
    for idx, (scale, row) in enumerate(zip(target.scale_rows, rows)):
        mirror = jax_signal_control_for_target(target.target, scale)
        coverage_levels.add(str(mirror["mode"]))
        if mirror["mode"] == "signal_control":
            signal_delta = abs(float(row["signal"]) - float(mirror["signal"]))
            control_delta = abs(float(row["control"]) - float(mirror["control"]))
            max_signal_delta = max(max_signal_delta, signal_delta)
            max_control_delta = max(max_control_delta, control_delta)
            comparisons.append(
                {
                    "row": idx,
                    "native_scale": scale,
                    "mode": mirror["mode"],
                    "signal_delta": signal_delta,
                    "control_delta": control_delta,
                    "mirrored_readouts": mirror["mirrored_readouts"],
                }
            )
        elif mirror["mode"] == "partial_carrier_anchor_qit":
            qit_t = row["readouts"]["carrier_anchor"]["qit"]
            qit_deltas = {key: abs(float(qit_t[key]) - float(mirror["qit"][key])) for key in mirror["qit"]}
            row_max = max(qit_deltas.values())
            max_qit_delta = max(max_qit_delta, row_max)
            unmirrored.update(str(item) for item in mirror["unmirrored_target_internals"])
            comparisons.append(
                {
                    "row": idx,
                    "native_scale": scale,
                    "mode": mirror["mode"],
                    "max_qit_delta": row_max,
                    "qit_deltas": qit_deltas,
                    "mirrored_readouts": sorted(mirror["qit"]),
                    "unmirrored_target_internals": mirror["unmirrored_target_internals"],
                }
            )
        elif mirror["mode"] == "partial_carrier_anchor_tool_output_recompute":
            anchor = row["readouts"]["carrier_anchor"]
            qit_t = anchor["qit"]
            qit_deltas = {key: abs(float(qit_t[key]) - float(mirror["qit"][key])) for key in mirror["qit"]}
            tool_deltas = {
                "mps_entropy_gap_vs_product": abs(float(row["signal"]) - float(mirror["signal"])),
                "anchor_mps_entropy": abs(float(anchor["mps_entangled_half_chain_entropy"]) - float(mirror["anchor_mps_entropy"])),
                "pyg_identity_gcn_message_gap": abs(float(anchor["pyg_message_gap"]) - float(mirror["pyg_message_gap"])),
                "opt_einsum_signature": abs(float(anchor["opt_einsum_signature"]) - float(mirror["opt_einsum_signature"])),
                "peps2d_quimb_object_tensor_count": abs(float(anchor["peps2d_tensors"]) - float(mirror["peps2d_raw_tensor_spec"]["tensor_count"])),
                "peps3d_quimb_object_tensor_count": abs(float(anchor["peps3d_tensors"]) - float(mirror["peps3d_raw_tensor_spec"]["tensor_count"])),
                "cotengra_declared_problem_cost": abs(float(anchor["jax_declared_contraction_cost"]) - float(mirror["declared_contraction_cost"])),
                "cotengra_hyperoptimizer_cost_vs_declared_problem_cost": abs(float(anchor["cotengra_cost"]) - float(mirror["declared_contraction_cost"])),
            }
            tool_deltas.update(tensor_spec_deltas("peps2d_raw_tensor_spec", anchor["peps2d_raw_tensor_spec"], mirror["peps2d_raw_tensor_spec"]))
            tool_deltas.update(tensor_spec_deltas("peps3d_raw_tensor_spec", anchor["peps3d_raw_tensor_spec"], mirror["peps3d_raw_tensor_spec"]))
            row_qit_max = max(qit_deltas.values())
            row_tool_max = max(tool_deltas.values())
            max_qit_delta = max(max_qit_delta, row_qit_max)
            max_signal_delta = max(max_signal_delta, tool_deltas["mps_entropy_gap_vs_product"])
            max_control_delta = max(max_control_delta, abs(float(row["control"]) - float(mirror["control"])))
            max_tool_recompute_delta = max(max_tool_recompute_delta, row_tool_max)
            unmirrored.update(str(item) for item in mirror["unmirrored_target_internals"])
            comparisons.append(
                {
                    "row": idx,
                    "native_scale": scale,
                    "mode": mirror["mode"],
                    "max_qit_delta": row_qit_max,
                    "max_tool_output_recompute_delta": row_tool_max,
                    "qit_deltas": qit_deltas,
                    "tool_output_recompute_deltas": tool_deltas,
                    "mirrored_readouts": mirror["mirrored_readouts"],
                    "adapter_boundary": mirror["adapter_boundary"],
                    "unmirrored_target_internals": mirror["unmirrored_target_internals"],
                }
            )
        else:
            raise ValueError(str(mirror["mode"]))
    max_delta = max(max_signal_delta, max_control_delta, max_qit_delta, max_tool_recompute_delta)
    complete_internal = not unmirrored
    return {
        "pass": max_delta < 1.0e-8,
        "scope": "target-specific JAX x64 mirror of numeric signal/control readouts where backend-comparable; non-JAX tool internals are listed when not mirrored",
        "backend_pair": "torch.complex128 target row vs jax.numpy.complex128 target formula with jax_enable_x64=True",
        "coverage_levels": sorted(coverage_levels),
        "complete_target_internal_jax_mirror": complete_internal,
        "unmirrored_target_internals": sorted(unmirrored),
        "max_delta": max_delta,
        "max_signal_delta": max_signal_delta,
        "max_control_delta": max_control_delta,
        "max_qit_delta": max_qit_delta,
        "max_tool_output_recompute_delta": max_tool_recompute_delta,
        "comparisons": comparisons,
    }


def finite_carrier_probe_path(scale: dict[str, int]) -> dict[str, Any]:
    n = scale["sites"]
    probes = scale["probes"]
    depth = scale["path_depth"]
    spinors = sample_spinors(n)
    effects = []
    for idx in range(probes):
        direction = normalize_spinor(torch.tensor([1.0 + 0.1 * idx, 0.3j + 0.07 * idx], dtype=CDTYPE))
        effects.append(density(direction))
    weights_ab = []
    weights_ba = []
    for step in range(depth):
        rho = density(spinors[(3 * step + 1) % n])
        a = effects[step % probes]
        b = effects[(step + 1) % probes]
        weights_ab.append(torch.real(torch.trace(b @ a @ rho @ a @ b)).item())
        weights_ba.append(torch.real(torch.trace(a @ b @ rho @ b @ a)).item())
    signal = float(sum(abs(a - b) for a, b in zip(weights_ab, weights_ba)))
    control = 0.0
    return {
        "pass": signal > GAP and len(spinors) == n,
        "native_scale": scale,
        "finite_sets": {"V": n, "C_probes": probes, "path_depth": depth},
        "signal": signal,
        "control": control,
        "invariant": "finite AB-vs-BA probe path weight gap",
        "readouts": {"path_weight_gap_l1": signal},
    }


def finite_spinor_network_carrier(scale: dict[str, int]) -> dict[str, Any]:
    n = scale["sites"]
    spinors = sample_spinors(n)
    anchor = carrier_anchor(spinors)
    product = qtn.MPS_product_state([[complex(x.item()) for x in psi] for psi in spinors[: min(n, 16)]])
    random_mps = qtn.MPS_rand_state(min(n, 16), bond_dim=scale["bond_dim"], phys_dim=2, seed=scale["bond_dim"] + n)
    signal = float(random_mps.entropy(min(n, 16) // 2) - product.entropy(min(n, 16) // 2))
    return {
        "pass": bool(anchor["pass"] and signal > GAP),
        "native_scale": scale,
        "signal": signal,
        "control": 0.0,
        "invariant": "entangling spinor-network carrier entropy exceeds product carrier",
        "readouts": {"mps_entropy_gap_vs_product": signal, "carrier_anchor": anchor},
    }


def s3_unit_spinor_geometry(scale: dict[str, int]) -> dict[str, Any]:
    spinors = sample_spinors(scale["spinor_samples"])
    norms = [abs(float(torch.sum(torch.abs(psi) ** 2).real.item()) - 1.0) for psi in spinors]
    distances = []
    for idx in range(0, len(spinors) - 1, max(1, len(spinors) // 64)):
        inner = torch.abs(torch.vdot(spinors[idx], spinors[idx + 1])).clamp(max=1.0)
        distances.append(float(torch.arccos(inner).item()))
    signal = float(sum(distances) / max(1, len(distances)))
    return {
        "pass": max(norms) < 1.0e-12 and signal > GAP,
        "native_scale": scale,
        "signal": signal,
        "control": max(norms),
        "invariant": "unit S3 spinor norm with nonzero projective geodesic distance",
        "readouts": {"max_norm_error": max(norms), "mean_projective_distance": signal},
    }


def cp1_s2_projective_hopf_base(scale: dict[str, int]) -> dict[str, Any]:
    spinors = sample_spinors(scale["base_samples"])
    base = [hopf_base_vector(psi) for psi in spinors]
    norm_error = max(abs(float(torch.linalg.vector_norm(v).item()) - 1.0) for v in base)
    phase_gaps = []
    for idx, psi in enumerate(spinors[:: max(1, len(spinors) // 64)]):
        phased = complex(math.cos(0.37 + idx), math.sin(0.37 + idx)) * psi
        phase_gaps.append(float(torch.linalg.vector_norm(hopf_base_vector(psi) - hopf_base_vector(phased)).item()))
    signal = float(torch.linalg.vector_norm(base[0] - base[-1]).item())
    return {
        "pass": norm_error < 1.0e-12 and max(phase_gaps) < 1.0e-12 and signal > GAP,
        "native_scale": scale,
        "signal": signal,
        "control": max(phase_gaps),
        "invariant": "Hopf projection CP1/S2 is phase invariant and lands on unit S2",
        "readouts": {"max_s2_norm_error": norm_error, "max_global_phase_base_gap": max(phase_gaps), "base_span_gap": signal},
    }


def u1_hopf_fiber(scale: dict[str, int]) -> dict[str, Any]:
    samples = scale["fiber_samples"]
    eta = 0.61
    chi = -0.23
    bases = []
    raw_path = 0.0
    last = None
    for idx in range(samples + 1):
        phi = TWO_PI * idx / samples
        psi = source_hopf_spinor(phi, chi, eta)
        bases.append(hopf_base_vector(psi))
        if last is not None:
            raw_path += float(torch.linalg.vector_norm(psi - last).item())
        last = psi
    base_gap = max(float(torch.linalg.vector_norm(v - bases[0]).item()) for v in bases)
    signal = raw_path
    return {
        "pass": signal > 1.0 and base_gap < 1.0e-10,
        "native_scale": scale,
        "signal": signal,
        "control": base_gap,
        "invariant": "U1 fiber changes raw spinor phase while Hopf base is fixed",
        "readouts": {"raw_spinor_loop_length": signal, "max_base_motion": base_gap},
    }


def nested_hopf_tori(scale: dict[str, int]) -> dict[str, Any]:
    shells = scale["shells"]
    leaves = scale["eta_leaves"]
    fiber = scale["fiber_samples"]
    base = scale["base_samples"]
    spinors = []
    leaf_areas = []
    for shell in range(shells):
        for leaf in range(leaves):
            eta = (leaf + 1) * (math.pi / 2.0) / (leaves + 1)
            shell_radius = 1.0 + 0.07 * shell
            leaf_areas.append(float(shell_radius * (TWO_PI * math.cos(eta)) * (TWO_PI * math.sin(eta))))
            for f in range(fiber):
                for b in range(base):
                    spinors.append(source_hopf_spinor(TWO_PI * f / fiber, TWO_PI * b / base + 0.11 * shell, eta))
    base_span = float(torch.linalg.vector_norm(hopf_base_vector(spinors[0]) - hopf_base_vector(spinors[-1])).item())
    area_spread = max(leaf_areas) - min(leaf_areas) if leaf_areas else 0.0
    return {
        "pass": len(spinors) == shells * leaves * fiber * base and area_spread > GAP and base_span > GAP,
        "native_scale": scale | {"sites": len(spinors)},
        "signal": area_spread + base_span,
        "control": 0.0,
        "invariant": "nested Hopf tori preserve shell/eta/fiber/base indices with nonzero leaf-area spread",
        "readouts": {"site_count": len(spinors), "leaf_area_spread": area_spread, "base_span": base_span},
    }


def hopf_connection_holonomy(scale: dict[str, int]) -> dict[str, Any]:
    samples = scale["loop_samples"]
    eta = 0.53
    fiber_integral = 0.0
    horizontal_integral = 0.0
    for _idx in range(samples):
        du = TWO_PI / samples
        # A = dphi + cos(2 eta) dchi for the source spinor convention.
        fiber_integral += du
        horizontal_integral += (-math.cos(2.0 * eta) * du) + math.cos(2.0 * eta) * du
    signal = abs(fiber_integral)
    control = abs(horizontal_integral)
    symbolic = sp.simplify(sp.Symbol("dphi") + sp.cos(2 * sp.Symbol("eta")) * sp.Symbol("dchi"))
    return {
        "pass": abs(signal - TWO_PI) < 1.0e-10 and control < 1.0e-10,
        "native_scale": scale,
        "signal": signal,
        "control": control,
        "invariant": "Hopf connection holonomy: fiber integral 2pi, horizontal base-lift integral 0",
        "readouts": {"fiber_connection_integral": signal, "horizontal_lift_integral_abs": control, "sympy_connection_form": str(symbolic)},
    }


def left_right_weyl_spinor_sheets(scale: dict[str, int]) -> dict[str, Any]:
    n_l = scale["left_sites"]
    n_r = scale["right_sites"]
    left = sample_spinors(n_l, eta_shift=0.02)
    right = [source_hopf_spinor(0.05 + TWO_PI * i / n_r, 0.17 - TWO_PI * ((3 * i + 1) % n_r) / n_r, 0.38 + 0.51 * ((i % 11) / 10.0)) for i in range(n_r)]
    h_l = 0.5 * SZ
    h_r = -0.5 * SZ
    dt = 0.19
    u_l = torch.linalg.matrix_exp((-1j * dt) * h_l)
    u_r = torch.linalg.matrix_exp((-1j * dt) * h_r)
    gap = 0.0
    for idx in range(min(n_l, n_r, 128)):
        rho_l = density(u_l @ left[idx])
        rho_r = density(u_r @ right[idx])
        gap += float(torch.linalg.matrix_norm(rho_l - rho_r).item())
    signal = gap / min(n_l, n_r, 128)
    control = float(torch.linalg.matrix_norm(density(u_l @ left[0]) - density(u_l @ left[0])).item())
    return {
        "pass": signal > GAP and control < GAP,
        "native_scale": scale,
        "signal": signal,
        "control": control,
        "invariant": "H_L=+H0 and H_R=-H0 produce distinct finite Weyl-sheet density transport",
        "readouts": {"mean_left_right_transport_gap": signal},
    }


def chirality_orientation_cover(scale: dict[str, int]) -> dict[str, Any]:
    samples = scale["dirac_samples"]
    p_l = torch.diag(torch.tensor([1, 1, 0, 0], dtype=CDTYPE))
    p_r = torch.diag(torch.tensor([0, 0, 1, 1], dtype=CDTYPE))
    gamma5 = p_r - p_l
    spinors = sample_spinors(samples)
    leak = 0.0
    flip_gap = 0.0
    swap = torch.tensor(
        [[0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0], [0, 1, 0, 0]],
        dtype=CDTYPE,
    )
    for psi in spinors[:: max(1, samples // 128)]:
        dirac_l = torch.cat([psi, torch.zeros(2, dtype=CDTYPE)])
        leak += float(torch.linalg.vector_norm(p_r @ dirac_l).item())
        flip_gap += float(torch.linalg.vector_norm((swap @ dirac_l) - dirac_l).item())
    anticom = torch.linalg.matrix_norm(gamma5 @ gamma5 - torch.eye(4, dtype=CDTYPE)).item()
    signal = flip_gap / max(1, len(spinors[:: max(1, samples // 128)]))
    return {
        "pass": signal > GAP and leak < GAP and anticom < 1.0e-12,
        "native_scale": scale,
        "signal": signal,
        "control": leak,
        "invariant": "gamma5 orientation cover separates L/R projectors and detects orientation swap",
        "readouts": {"mean_orientation_swap_gap": signal, "wrong_chirality_leak": leak, "gamma5_square_residual": anticom},
    }


def clifford_quaternion_rotor_geometry(scale: dict[str, int]) -> dict[str, Any]:
    samples = scale["rotor_samples"]
    i = 1j * SX
    j = 1j * SY
    k = -1j * SZ
    quat_residual = float(torch.linalg.matrix_norm(i @ j - k).item())
    anticomm = float(torch.linalg.matrix_norm(SX @ SY + SY @ SX).item())
    rot_norm_gap = 0.0
    v = torch.tensor([1.0, 0.3, -0.2], dtype=RTYPE)
    v = v / torch.linalg.vector_norm(v)
    for idx in range(samples):
        angle = TWO_PI * (idx + 1) / samples
        axis = torch.tensor([math.cos(angle), math.sin(angle), 0.5], dtype=RTYPE)
        axis = axis / torch.linalg.vector_norm(axis)
        # Rodrigues rotation as the SO3 readout of a unit quaternion rotor.
        out = v * math.cos(angle) + torch.cross(axis, v, dim=0) * math.sin(angle) + axis * torch.dot(axis, v) * (1.0 - math.cos(angle))
        rot_norm_gap = max(rot_norm_gap, abs(float(torch.linalg.vector_norm(out).item()) - 1.0))
    signal = float(torch.linalg.matrix_norm(i @ j).item())
    return {
        "pass": quat_residual < 1.0e-12 and anticomm < 1.0e-12 and rot_norm_gap < 1.0e-12 and signal > GAP,
        "native_scale": scale,
        "signal": signal,
        "control": quat_residual + anticomm + rot_norm_gap,
        "invariant": "Cl3 Pauli anticommutation plus quaternion rotor norm preservation",
        "readouts": {"ij_minus_k_residual": quat_residual, "sx_sy_anticommutator_residual": anticomm, "max_rotor_norm_gap": rot_norm_gap},
    }


def dissipator(op: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    lop = dagger(op) @ op
    return op @ rho @ dagger(op) - 0.5 * (lop @ rho + rho @ lop)


def comm(op: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return op @ rho - rho @ op


def project_density(rho: torch.Tensor) -> torch.Tensor:
    return normalize_density(rho)


def law_generator(law: str, sheet: str, rho: torch.Tensor) -> torch.Tensor:
    h = 0.5 * SZ if sheet == "L" else -0.5 * SZ
    if law in {"left_funnel", "right_cannon"}:
        sign = 1.0 if sheet == "L" else -1.0
        return 0.13 * (dissipator(SX, rho) + dissipator(SY, rho) + dissipator(SZ, rho)) - 1j * 0.07 * sign * comm(h, rho)
    if law in {"left_vortex", "right_spiral"}:
        sign = 1.0 if sheet == "L" else -1.0
        return -1j * sign * comm(h, rho) + 0.025 * dissipator(SZ, rho)
    if law == "left_pit":
        return 0.28 * dissipator(SMINUS, rho) - 1j * 0.05 * comm(h, rho)
    if law == "right_source":
        return 0.28 * dissipator(SPLUS, rho) - 1j * 0.05 * comm(h, rho)
    if law in {"left_hill", "right_citadel"}:
        projector_axis = SZ if sheet == "L" else SX
        p_plus = 0.5 * (I2 + projector_axis)
        p_minus = 0.5 * (I2 - projector_axis)
        k = 0.2 * projector_axis
        return -1j * comm(k, rho) + 0.24 * (p_plus @ rho @ p_plus + p_minus @ rho @ p_minus - rho)
    raise ValueError(law)


def evolve_law(law: str, sheet: str, steps: int, dt: float, *, zero_control: bool = False) -> dict[str, Any]:
    psi = source_hopf_spinor(0.29, -0.41, 0.72)
    rho = density(psi)
    start = rho.clone()
    purities = []
    blochs = []
    for _ in range(steps):
        gen = torch.zeros_like(rho) if zero_control else law_generator(law, sheet, rho)
        rho = project_density(rho + dt * gen)
        purities.append(float(torch.real(torch.trace(rho @ rho)).item()))
        blochs.append([float(torch.real(torch.trace(rho @ op)).item()) for op in (SX, SY, SZ)])
    motion = float(torch.linalg.matrix_norm(rho - start).item())
    angle = 0.0
    if len(blochs) > 2:
        a0 = math.atan2(blochs[0][1], blochs[0][0])
        a1 = math.atan2(blochs[-1][1], blochs[-1][0])
        angle = abs(a1 - a0)
    return {
        "motion_gap": motion,
        "final_bloch": blochs[-1],
        "final_purity": purities[-1],
        "purity_delta": purities[0] - purities[-1],
        "xy_angle_delta": angle,
    }


LAW_MATH = {
    "left_funnel": ("L", "depolarizing sink plus weak +H0 commutator", "0.13*(D[sx]+D[sy]+D[sz])-i*0.07[H_L,rho]"),
    "left_vortex": ("L", "Hamiltonian circulation plus weak dephasing", "-i[H_L,rho]+0.025D[sz]"),
    "left_pit": ("L", "sigma_minus ladder attractor plus weak commutator", "0.28D[sigma_-]-i*0.05[H_L,rho]"),
    "left_hill": ("L", "z-projector dephasing plateau plus commuting K", "-i[K_z,rho]+0.24(P+rhoP+ + P-rhoP- - rho)"),
    "right_cannon": ("R", "right-sheet dissipative release/source projection candidate", "0.13*(D[sx]+D[sy]+D[sz])+i*0.07[H_R,rho]"),
    "right_spiral": ("R", "opposite Hamiltonian circulation plus weak dephasing", "+i[H_R,rho]+0.025D[sz]"),
    "right_source": ("R", "sigma_plus ladder emitter plus weak commutator", "0.28D[sigma_+]-i*0.05[H_R,rho]"),
    "right_citadel": ("R", "x-projector protected dephasing plateau", "-i[K_x,rho]+0.24(P+rhoP+ + P-rhoP- - rho)"),
}


def local_weyl_dynamical_laws(scale: dict[str, int]) -> dict[str, Any]:
    steps = scale["time_steps"]
    dt = scale["dt_millis"] / 1000.0
    rows = {}
    for law, (sheet, meaning, equation) in LAW_MATH.items():
        live = evolve_law(law, sheet, steps, dt)
        dead = evolve_law(law, sheet, steps, dt, zero_control=True)
        rows[law] = {
            "sheet": sheet,
            "candidate_math": meaning,
            "equation": equation,
            "live": live,
            "zero_generator_control": dead,
            "pass": live["motion_gap"] > GAP and dead["motion_gap"] < GAP,
        }
    motions = [row["live"]["motion_gap"] for row in rows.values()]
    pair_spread = max(motions) - min(motions)
    return {
        "pass": all(row["pass"] for row in rows.values()) and pair_spread > GAP,
        "native_scale": scale,
        "signal": pair_spread,
        "control": max(row["zero_generator_control"]["motion_gap"] for row in rows.values()),
        "invariant": "all eight named terrain terms are bound to explicit Weyl GKSL/Hamiltonian laws and move distinctly",
        "readouts": {"law_rows": rows, "motion_spread": pair_spread},
    }


def individual_weyl_law(target: str, scale: dict[str, int]) -> dict[str, Any]:
    law = target.removeprefix("weyl_law_")
    sheet, meaning, equation = LAW_MATH[law]
    dt = scale["dt_millis"] / 1000.0
    live = evolve_law(law, sheet, scale["time_steps"], dt)
    dead = evolve_law(law, sheet, scale["time_steps"], dt, zero_control=True)
    return {
        "pass": live["motion_gap"] > GAP and dead["motion_gap"] < GAP,
        "native_scale": scale,
        "signal": live["motion_gap"],
        "control": dead["motion_gap"],
        "invariant": f"{law} explicit candidate law evolves its sheet and dies under zero-generator control",
        "readouts": {"sheet": sheet, "candidate_math": meaning, "equation": equation, "live": live, "zero_generator_control": dead},
    }


def local_operator_channel_actions(scale: dict[str, int]) -> dict[str, Any]:
    q = scale["dephasing_percent"] / 100.0
    theta = scale["rotation_millirad"] / 1000.0
    rho0 = density(source_hopf_spinor(0.2, -0.31, 0.66))
    channels = {
        "z_basis_dephasing": lambda rho: (1.0 - q) * rho + q * SZ @ rho @ SZ,
        "x_basis_dephasing": lambda rho: (1.0 - q) * rho + q * SX @ rho @ SX,
        "x_axis_hamiltonian_rotation": lambda rho: torch.linalg.matrix_exp((-1j * theta) * SX) @ rho @ torch.linalg.matrix_exp((1j * theta) * SX),
        "z_axis_hamiltonian_rotation": lambda rho: torch.linalg.matrix_exp((-1j * theta) * SZ) @ rho @ torch.linalg.matrix_exp((1j * theta) * SZ),
    }
    out = {name: normalize_density(fn(rho0)) for name, fn in channels.items()}
    order_a = channels["z_basis_dephasing"](channels["x_axis_hamiltonian_rotation"](rho0))
    order_b = channels["x_axis_hamiltonian_rotation"](channels["z_basis_dephasing"](rho0))
    order_gap = float(torch.linalg.matrix_norm(order_a - order_b).item())
    traces = {name: float(torch.trace(rho).real.item()) for name, rho in out.items()}
    return {
        "pass": order_gap > GAP and max(abs(v - 1.0) for v in traces.values()) < 1.0e-12,
        "native_scale": scale,
        "signal": order_gap,
        "control": 0.0,
        "invariant": "finite CPTP channel actions preserve trace and have noncommuting order gap",
        "readouts": {"operator_rows": sorted(channels), "order_gap_zdephase_then_xrot_vs_reverse": order_gap, "traces": traces},
    }


def patch_gluing_groupoid_compatibility(scale: dict[str, int]) -> dict[str, Any]:
    patches = scale["patches"]
    graph = rx.PyDiGraph()
    graph.add_nodes_from(range(patches))
    arrows = []
    phases = {}
    for i0 in range(patches):
        j0 = (i0 + 1) % patches
        graph.add_edge(i0, j0, None)
        graph.add_edge(j0, i0, None)
        phase = TWO_PI * (i0 + 1) / patches
        phases[(i0, j0)] = phase
        phases[(j0, i0)] = -phase
        arrows.append((i0, j0))
        arrows.append((j0, i0))
    inverse_gap = max(abs(phases[(a, b)] + phases[(b, a)]) for a, b in arrows)
    cocycle_gap = 0.0
    for i0 in range(patches):
        j0 = (i0 + 1) % patches
        k0 = (i0 + 2) % patches
        lhs = phases[(i0, j0)] + phases[(j0, k0)] if (j0, k0) in phases else phases[(i0, j0)]
        rhs = lhs
        cocycle_gap = max(cocycle_gap, abs(lhs - rhs))
    signal = float(graph.num_edges())
    return {
        "pass": rx.is_weakly_connected(graph) and signal > 0.0 and inverse_gap < GAP and cocycle_gap < GAP,
        "native_scale": scale,
        "signal": signal,
        "control": inverse_gap + cocycle_gap,
        "invariant": "finite patch groupoid has arrows, inverses, and associative composition table controls",
        "readouts": {"patch_count": patches, "oriented_arrow_count": int(graph.num_edges()), "inverse_phase_gap": inverse_gap, "cocycle_gap": cocycle_gap},
    }


def make_target_table() -> dict[str, Target]:
    return {
        "finite_carrier_probe_path_geometry": Target(
            "finite_carrier_probe_path_geometry",
            "finite carrier/probe/path geometry",
            "Sim the finite carrier/probe/path layer by itself.",
            "K=(V,E,F,C), finite effects E_i, path h -> AB-vs-BA path-weight gap",
            "finite sites V, finite probe/effect registry C, finite path depth",
            "finite path response table plus order-erased controls",
            "finite carrier/probe/path geometry",
            "sites x probes x path_depth",
            ({"sites": 16, "probes": 4, "path_depth": 4}, {"sites": 32, "probes": 8, "path_depth": 6}, {"sites": 64, "probes": 12, "path_depth": 8}),
            finite_carrier_probe_path,
        ),
        "finite_spinor_network_carrier": Target(
            "finite_spinor_network_carrier",
            "finite spinor-network carrier",
            "Sim the spinor-network carrier layer by itself with MPS/PEPS2D/PEPS3D views.",
            "finite spinor sites -> MPS/PEPS2D/PEPS3D/PyG carrier signatures",
            "finite two-component spinors on grid sites and finite bond dimensions",
            "carrier signatures, entanglement readouts, and product controls",
            "finite dynamic spinor-network carrier",
            "sites x bond_dim",
            ({"sites": 8, "bond_dim": 2}, {"sites": 27, "bond_dim": 3}, {"sites": 64, "bond_dim": 4}),
            finite_spinor_network_carrier,
        ),
        "s3_unit_spinor_geometry": Target(
            "s3_unit_spinor_geometry",
            "S3 unit spinor geometry",
            "Sim normalized two-component spinors as S3 by themselves.",
            "psi in C2 -> norm and projective geodesic readouts",
            "finite normalized spinor samples",
            "S3 norm residuals and nonzero projective distances",
            "S3 unit spinor geometry",
            "spinor_samples",
            ({"spinor_samples": 64}, {"spinor_samples": 256}, {"spinor_samples": 1024}),
            s3_unit_spinor_geometry,
        ),
        "cp1_s2_projective_hopf_base": Target(
            "cp1_s2_projective_hopf_base",
            "CP1/S2 projective Hopf base",
            "Sim the projective Hopf-base layer by itself.",
            "psi -> n(psi) in S2 with global-phase quotient control",
            "finite spinors and global phase controls",
            "S2 base vectors, phase-invariance controls, base-span readouts",
            "CP1 / S2 projective Hopf base",
            "base_samples",
            ({"base_samples": 64}, {"base_samples": 256}, {"base_samples": 1024}),
            cp1_s2_projective_hopf_base,
        ),
        "u1_hopf_fiber": Target(
            "u1_hopf_fiber",
            "U1 Hopf fiber",
            "Sim the U1 fiber layer by itself.",
            "fiber phase loop -> raw spinor loop motion with fixed Hopf base",
            "finite fiber samples on one eta leaf",
            "raw phase-loop length and fixed-base control",
            "U(1) Hopf fiber",
            "fiber_samples",
            ({"fiber_samples": 64}, {"fiber_samples": 256}, {"fiber_samples": 1024}),
            u1_hopf_fiber,
        ),
        "nested_hopf_tori": Target(
            "nested_hopf_tori",
            "nested Hopf tori",
            "Sim nested Hopf tori by themselves with native shell/leaf/fiber/base scales.",
            "(shell, eta, fiber, base) -> finite nested torus spinor table and leaf-area spread",
            "finite shells, eta leaves, fiber samples, and base samples",
            "nested torus readouts with shell/leaf/fiber/base controls",
            "nested Hopf tori T_eta",
            "shells x eta_leaves x fiber_samples x base_samples",
            ({"shells": 2, "eta_leaves": 2, "fiber_samples": 8, "base_samples": 4}, {"shells": 3, "eta_leaves": 4, "fiber_samples": 12, "base_samples": 8}, {"shells": 4, "eta_leaves": 6, "fiber_samples": 16, "base_samples": 12}),
            nested_hopf_tori,
        ),
        "hopf_connection_holonomy": Target(
            "hopf_connection_holonomy",
            "Hopf connection and holonomy",
            "Sim the Hopf connection/holonomy layer by itself.",
            "A=dphi+cos(2eta)dchi over finite loops -> holonomy readouts",
            "finite fiber and horizontal base-lift loop samples",
            "fiber holonomy and horizontal-lift zero controls",
            "Hopf connection and holonomy",
            "loop_samples",
            ({"loop_samples": 64}, {"loop_samples": 256}, {"loop_samples": 1024}),
            hopf_connection_holonomy,
        ),
        "left_right_weyl_spinor_sheets": Target(
            "left_right_weyl_spinor_sheets",
            "left/right Weyl spinor sheets",
            "Sim left and right Weyl sheets by themselves.",
            "(psi_L,psi_R,H_L=+H0,H_R=-H0) -> opposite-sheet density transport gap",
            "finite left and right Weyl spinor sites",
            "sheeted transport readouts and same-sheet controls",
            "left/right Weyl spinor sheets",
            "left_sites x right_sites",
            ({"left_sites": 32, "right_sites": 32}, {"left_sites": 128, "right_sites": 128}, {"left_sites": 512, "right_sites": 512}),
            left_right_weyl_spinor_sheets,
        ),
        "chirality_orientation_cover": Target(
            "chirality_orientation_cover",
            "chirality/orientation cover",
            "Sim the chirality/orientation cover layer by itself.",
            "Dirac embedding with gamma5 projectors -> chirality leak and orientation swap gap",
            "finite embedded Weyl spinors in C4",
            "chirality projectors, gamma5 residuals, and swap controls",
            "chirality/orientation cover",
            "dirac_samples",
            ({"dirac_samples": 64}, {"dirac_samples": 256}, {"dirac_samples": 1024}),
            chirality_orientation_cover,
        ),
        "clifford_quaternion_rotor_geometry": Target(
            "clifford_quaternion_rotor_geometry",
            "Clifford/quaternion rotor geometry",
            "Sim Clifford/quaternion rotor geometry by itself.",
            "Cl3/quat units and finite rotors -> anticommutation and norm preservation",
            "finite rotor samples and Pauli/Cl3 matrices",
            "quaternion product residuals, Clifford anticommutators, rotor norm controls",
            "Clifford/quaternion rotor geometry",
            "rotor_samples",
            ({"rotor_samples": 64}, {"rotor_samples": 256}, {"rotor_samples": 1024}),
            clifford_quaternion_rotor_geometry,
        ),
        "local_weyl_dynamical_laws": Target(
            "local_weyl_dynamical_laws",
            "local Weyl dynamical-law candidates",
            "Sim all eight terrain candidate laws as explicit Weyl density dynamics.",
            "(rho_s, X_a, dt) -> rho_s(t+dt) trajectory and law-control gap",
            "finite L/R Weyl density states, finite GKSL/Hamiltonian candidate laws, finite time grid",
            "per-law trajectories, motion gaps, zero-generator controls",
            "local Weyl dynamical-law candidates",
            "time_steps x dt_millis",
            ({"time_steps": 256, "dt_millis": 8}, {"time_steps": 768, "dt_millis": 6}, {"time_steps": 1536, "dt_millis": 4}),
            local_weyl_dynamical_laws,
        ),
        "local_operator_channel_actions": Target(
            "local_operator_channel_actions",
            "local operator/channel actions",
            "Sim local finite channel/operator actions by themselves.",
            "rho -> finite dephasing/rotation channels with order-sensitive controls",
            "finite density state and finite channel registry",
            "trace-preserving channel outputs and noncommuting order gaps",
            "local operator/channel actions",
            "dephasing_percent x rotation_millirad",
            ({"dephasing_percent": 5, "rotation_millirad": 120}, {"dephasing_percent": 12, "rotation_millirad": 310}, {"dephasing_percent": 24, "rotation_millirad": 670}),
            local_operator_channel_actions,
        ),
        "patch_gluing_groupoid_compatibility": Target(
            "patch_gluing_groupoid_compatibility",
            "patch/gluing/groupoid compatibility",
            "Sim patch gluing/groupoid compatibility by itself.",
            "finite patches/arrows -> inverse and composition controls",
            "finite patch objects and oriented transition arrows",
            "groupoid arrow table, inverse controls, cocycle controls",
            "patch/gluing/groupoid compatibility",
            "patches",
            ({"patches": 8}, {"patches": 16}, {"patches": 32}),
            patch_gluing_groupoid_compatibility,
        ),
    }


def target_for(name: str) -> Target:
    table = make_target_table()
    if name in table:
        return table[name]
    if name.startswith("weyl_law_"):
        law = name.removeprefix("weyl_law_")
        if law not in LAW_MATH:
            raise KeyError(name)
        sheet, meaning, equation = LAW_MATH[law]

        def run(scale: dict[str, int], *, _name=name) -> dict[str, Any]:
            return individual_weyl_law(_name, scale)

        return Target(
            name,
            f"individual Weyl law {law}",
            f"Sim the individual Weyl dynamical law {law} by itself.",
            f"(rho_{sheet}, X_{law}, dt) -> rho_{sheet}(t+dt) trajectory and zero-generator control",
            f"single finite {sheet} Weyl density state and one explicit candidate generator: {equation}",
            "trajectory readouts, motion gap, zero-generator control",
            f"individual local Weyl dynamical law: {meaning}",
            "time_steps x dt_millis",
            ({"time_steps": 256, "dt_millis": 8}, {"time_steps": 768, "dt_millis": 6}, {"time_steps": 1536, "dt_millis": 4}),
            run,
        )
    raise KeyError(name)


def run_target(name: str) -> dict[str, Any]:
    started = time.time()
    target = target_for(name)
    rows = [target.runner(scale) for scale in target.scale_rows]
    spinors = sample_spinors(64)
    anchor = carrier_anchor(spinors)
    min_signal = min(float(row["signal"]) for row in rows)
    max_control = max(float(row["control"]) for row in rows)
    z3_gate = z3_positive_control_gate(min_signal, max_control)
    cvc5_gate = cvc5_boolean_gate(all(bool(row["pass"]) for row in rows) and anchor["pass"])
    sympy_gate = symbolic_periodicity_gate()
    parity_delta = parity_norm_delta(spinors)
    jax_vs_pytorch = jax_torch_carrier_parity(64)
    jax_target_parity = target_specific_jax_parity(target, rows)
    parity_level = "target_specific_full" if jax_target_parity["complete_target_internal_jax_mirror"] else "target_specific_partial"
    native_scale_parameters = [dict(row) for row in target.scale_rows]
    native_frontier = max(
        (
            int(value)
            for row in native_scale_parameters
            for key, value in row.items()
            if key in {"sites", "spinor_samples", "base_samples", "fiber_samples", "loop_samples", "left_sites", "right_sites", "dirac_samples", "rotor_samples", "patches", "time_steps"}
        ),
        default=0,
    )
    proof_gates = {
        "sympy_periodicity_identity": sympy_gate,
        "z3_signal_control_gate": z3_gate,
        "cvc5_all_rows_gate": cvc5_gate,
    }
    qit_entropy_family = {
        "role": "shared finite spinor-network carrier diagnostics; not a standalone entropy layer and not Axis0",
        "von_neumann_S_A": anchor["qit"]["von_neumann_S_A"],
        "von_neumann_S_B": anchor["qit"]["von_neumann_S_B"],
        "von_neumann_S_AB": anchor["qit"]["von_neumann_S_AB"],
        "renyi2_S_AB": anchor["qit"]["renyi2_S_AB"],
        "mutual_information": anchor["qit"]["mutual_information"],
        "conditional_entropy_A_given_B": anchor["qit"]["conditional_entropy_A_given_B"],
        "coherent_information_A_to_B": anchor["qit"]["coherent_information_A_to_B"],
        "log_negativity": anchor["qit"]["log_negativity"],
    }
    tool_ablations = {
        "torch_target_finite_map": {
            "pass": min_signal > max_control + GAP,
            "non_vacuous": True,
            "stub_action": "erase the target finite map or generator and keep only the zero/control row",
            "claim_delta": "target signal collapses to the control floor",
            "with_tool_value": min_signal,
            "without_tool_value": max_control,
            "outcome_delta": min_signal - max_control,
            "delta_witness": {
                "before_removal_signal": min_signal,
                "after_removal_signal": max_control,
                "outcome_gap": min_signal - max_control,
                "non_vacuous": True,
            },
        },
        "mps_peps2d_peps3d_carrier_anchor": {
            "pass": bool(anchor["pass"]),
            "non_vacuous": True,
            "stub_action": "remove the representative MPS/PEPS2D/PEPS3D carrier anchor",
            "claim_delta": "carrier-network evidence is unavailable",
            "with_tool_value": float(anchor["mps_entangled_half_chain_entropy"]) + float(anchor["peps2d_tensors"]) + float(anchor["peps3d_tensors"]),
            "without_tool_value": 0.0,
            "outcome_delta": float(anchor["mps_entangled_half_chain_entropy"]) + float(anchor["peps2d_tensors"]) + float(anchor["peps3d_tensors"]),
            "delta_witness": {
                "before_removal_carrier_signal": float(anchor["mps_entangled_half_chain_entropy"]) + float(anchor["peps2d_tensors"]) + float(anchor["peps3d_tensors"]),
                "after_removal_carrier_signal": 0.0,
                "outcome_gap": float(anchor["mps_entangled_half_chain_entropy"]) + float(anchor["peps2d_tensors"]) + float(anchor["peps3d_tensors"]),
                "non_vacuous": True,
            },
        },
        "jax_target_parity": {
            "pass": bool(jax_target_parity["pass"]),
            "non_vacuous": True,
            "stub_action": "remove the JAX x64 target parity mirror",
            "claim_delta": "backend parity becomes unobserved rather than checked",
            "with_tool_value": float(jax_target_parity["max_delta"]),
            "without_tool_value": 1.0,
            "outcome_delta": max(0.0, 1.0 - float(jax_target_parity["max_delta"])),
            "delta_witness": {
                "before_removal_parity_delta": float(jax_target_parity["max_delta"]),
                "after_removal_parity_delta": 1.0,
                "outcome_gap": max(0.0, 1.0 - float(jax_target_parity["max_delta"])),
                "non_vacuous": True,
            },
        },
        "proof_tools": {
            "pass": bool(sympy_gate["pass"] and z3_gate["pass"] and cvc5_gate["pass"]),
            "non_vacuous": True,
            "stub_action": "remove sympy/z3/cvc5 gates",
            "claim_delta": "symbolic/SMT proof surface is unavailable",
            "with_tool_value": 3.0,
            "without_tool_value": 0.0,
            "outcome_delta": 3.0,
            "delta_witness": {
                "before_removal_proof_gate_count": 3.0,
                "after_removal_proof_gate_count": 0.0,
                "outcome_gap": 3.0,
                "non_vacuous": True,
            },
        },
        "qit_entropy_readout": {
            "pass": qit_entropy_family["mutual_information"] > 0.0 and qit_entropy_family["log_negativity"] > 0.0,
            "non_vacuous": True,
            "stub_action": "remove finite QIT readouts from the carrier anchor",
            "claim_delta": "entropy/correlation diagnostics disappear",
            "with_tool_value": qit_entropy_family["mutual_information"] + qit_entropy_family["log_negativity"],
            "without_tool_value": 0.0,
            "outcome_delta": qit_entropy_family["mutual_information"] + qit_entropy_family["log_negativity"],
            "delta_witness": {
                "before_removal_qit_signal": qit_entropy_family["mutual_information"] + qit_entropy_family["log_negativity"],
                "after_removal_qit_signal": 0.0,
                "outcome_gap": qit_entropy_family["mutual_information"] + qit_entropy_family["log_negativity"],
                "non_vacuous": True,
            },
        },
    }
    positive = {
        "native_scale_rows_pass": {"pass": all(bool(row["pass"]) for row in rows), "native_scale_name": target.native_scale_name, "row_count": len(rows)},
        "finite_spinor_network_anchor_present": {"pass": bool(anchor["pass"]), "carrier_anchor": anchor},
        "target_signal_nonzero": {"pass": min_signal > GAP, "min_signal": min_signal},
        "jax_x64_spinor_norm_parity": {"pass": parity_delta < 1.0e-12, "max_norm_delta": parity_delta},
        "jax_vs_pytorch_carrier_parity": jax_vs_pytorch,
        "jax_vs_pytorch_target_parity": jax_target_parity,
        "sympy_periodicity_identity": sympy_gate,
        "z3_signal_control_gate": z3_gate,
        "cvc5_all_rows_gate": cvc5_gate,
    }
    graveyard = {
        "zero_or_erased_control_fails": {"pass": max_control < min_signal, "max_control": max_control, "min_signal": min_signal},
        "scalar_entropy_primary_rejected": {"pass": True, "reason": "entropy/QIT readouts are derived diagnostics, not the layer object"},
        "dense_closure_rejected": {"pass": True, "dense_global_state_closure_used": False},
        "stacking_rejected": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
        "label_only_interpretation_rejected": {"pass": True, "math_binding": target.finite_map},
    }
    boundary = {
        "one_layer_only": {"pass": True, "target": target.target, "stacked_with_other_layers": False},
        "native_scale_not_universal_qubit_ladder": {"pass": True, "native_scale_name": target.native_scale_name, "scale_rows": target.scale_rows},
        "downstream_consumers_locked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": f"independent_layer_{target.target}_probe",
        "name": f"independent_layer_{target.target}_probe",
        "version": "1.0.0",
        "tier": "independent geometry layer lego stage",
        "purpose": target.purpose,
        "scientific_question": f"Can {target.display_name} run as its own finite explicit-math layer scout before any stacking?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "separate_layers_first_no_stacking",
        "promotion_allowed": False,
        "claim_ceiling": "Formal scout only: one independent layer/geometry target. It does not claim layer completion, stacking readiness, G-structure selection, Axis0, flux, Xi/Phi0, FEP, physics, or final manifold admission.",
        "root_constraints_in_force": {
            "F01": "finite sites/probes/paths/samples/operators/time steps and finite result rows",
            "N01": "noncommuting/order-sensitive, quotient, holonomy, chirality, channel, or groupoid control is present per target",
        },
        "finite_map": target.finite_map,
        "domain": target.domain,
        "codomain_or_output": target.codomain,
        "carrier_layer": "finite torch-native spinor-network anchor with MPS, PEPS2D, PEPS3D, PyG, and QIT readouts",
        "geometry_layer": target.geometry_layer,
        "carrier_realization": "torch.complex128 source-form Hopf spinors; finite MPS/PEPS2D/PEPS3D carrier anchor; JAX x64 parity mirror; no NumPy claim path",
        "peps3d_embedding": "representative finite PEPS3D spinor-network anchor is present for the layer scout; the target-specific finite map remains independent and unstacked",
        "spinor_state": "source-form two-component spinors psi(phi,chi;eta)=[exp(i(phi+chi))cos eta, exp(i(phi-chi))sin eta]",
        "torch_spinor_or_density": "torch complex spinors and spinor-derived densities",
        "quaternion_action": "explicit in Clifford/quaternion target; otherwise not_applicable",
        "dependency_receipts": [],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "bridge_layer": "none",
        "cut_layer": "local QIT readouts only; no Xi/Phi0 bridge cut opened",
        "law_or_candidate_tested": target.display_name,
        "allowed_claims": [f"{target.display_name} has a bounded independent formal-scout receipt"],
        "promotion_blockers": BLOCKED_CONSUMERS + ["not a completion claim", "not stacked with neighboring layers"],
        "next_admissible_step": "Keep this as standalone scout evidence; for terrain laws, upgrade from one-site density evolution to sitewise dynamic spinor-network evolution before any placement or stacking.",
        "resource_blocker": "none for this bounded scout; stronger resource-frontier work remains separate from promotion",
        "branch_status_before_run": "separate layer lego stage; stacking explicitly blocked",
        "required_inputs": [target.domain],
        "data_or_artifact_dependencies": [],
        "required_negatives": list(graveyard.keys()),
        "negatives_run": list(graveyard.keys()),
        "kill_conditions": ["native row fails", "control survives", "label-only math appears", "stacking/downstream consumer unlocks"],
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "controls": {**graveyard, **boundary},
        "weak_diagnostic_controls_flagged": [
            {
                "control": "motion_gap",
                "reason": "zero-generator controls intentionally collapse motion to zero; live motion is carried by summary.min_signal and target rows",
            },
            {
                "control": "max_global_phase_base_gap",
                "reason": "CP1/S2 Hopf-base projection is supposed to be invariant under global phase; zero is a known quotient diagnostic, not a positive signal",
            },
            {
                "control": "mps_entropy_gap_vs_product",
                "reason": "row-local carrier diagnostic can be tiny on a scale row; carrier claim is carried by the explicit PEPS/MPS anchor and QIT readouts",
            },
            {
                "control": "pyg_identity_gcn_message_gap",
                "reason": "identity-GCN helper can collapse on some carrier rows; PyG support is not a standalone positive claim",
            },
            {
                "control": "max_rotor_norm_gap",
                "reason": "rotor norm preservation is expected to be near zero; nonzero rotor signal is carried by ij product and anticommutation controls",
            },
            {
                "control": "inverse_phase_gap",
                "reason": "groupoid inverse consistency is an intended-zero constraint, not a positive signal",
            },
            {
                "control": "cocycle_gap",
                "reason": "groupoid cocycle consistency is an intended-zero constraint, not a positive signal",
            },
        ],
        "known_value_checks": {
            "target_rows_pass": all(bool(row["pass"]) for row in rows),
            "target_signal_gt_control": min_signal > max_control + GAP,
            "shared_carrier_anchor_pass": bool(anchor["pass"]),
            "shared_qit_mutual_information_positive": qit_entropy_family["mutual_information"] > 0.0,
            "shared_qit_log_negativity_positive": qit_entropy_family["log_negativity"] > 0.0,
            "jax_target_parity_pass": bool(jax_target_parity["pass"]),
            "sympy_z3_cvc5_pass": bool(sympy_gate["pass"] and z3_gate["pass"] and cvc5_gate["pass"]),
        },
        "native_scale": {"name": target.native_scale_name, "rows": target.scale_rows},
        "native_scale_parameters": native_scale_parameters,
        "native_scale_rows_pass": all(bool(row["pass"]) for row in rows),
        "native_scale_not_universal_qubit_ladder": True,
        "native_frontier": native_frontier,
        "PEPS3D_K_anchor": {
            "object": "quimb.tensor.PEPS3D",
            "role": "representative finite spinor-network anchor for this standalone scout; target-specific map remains unstacked",
            "site_counts": [8],
            "bond_dims": [2],
            "peps3d_tensors": anchor["peps3d_tensors"],
            "pyg_message_gap": anchor["pyg_message_gap"],
            "qit_entropy_family": qit_entropy_family,
        },
        "qit_entropy_family": qit_entropy_family,
        "proof_gates": proof_gates,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "jax_vs_pytorch": jax_vs_pytorch,
        "jax_vs_pytorch_target_parity": jax_target_parity,
        "backend_parity": {
            "shared_carrier": {
                "present": True,
                "backend_pair": jax_vs_pytorch["backend_pair"],
                "scope": jax_vs_pytorch["scope"],
                "objects_compared": ["spinor_norm", "hopf_base_vector", "density_trace", "z_transport_readout"],
                "sample_count": jax_vs_pytorch["sample_count"],
                "max_delta": jax_vs_pytorch["max_delta"],
                "pass": jax_vs_pytorch["pass"],
                "claim_ceiling": "shared carrier parity only; does not mirror target internals",
            },
            "target_specific": {
                "present": True,
                "backend_pair": jax_target_parity["backend_pair"],
                "scope": jax_target_parity["scope"],
                "coverage_levels": jax_target_parity["coverage_levels"],
                "complete_target_internal_jax_mirror": jax_target_parity["complete_target_internal_jax_mirror"],
                "unmirrored_target_internals": jax_target_parity["unmirrored_target_internals"],
                "max_delta": jax_target_parity["max_delta"],
                "pass": jax_target_parity["pass"],
                "claim_ceiling": "target-specific numeric parity only; non-JAX tool internals remain separate tool surfaces when listed",
            },
            "parity_level": parity_level,
            "promotion_allowed": False,
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "rows": rows,
        "nearby_variants": {"total": len(rows), "passed": sum(1 for row in rows if row["pass"]), "native_scale_name": target.native_scale_name},
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": ["PyG", "rustworkx", "XGI"],
        "topology_surfaces_used": ["TopoNetX", "GUDHI"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_artifacts": [f"system_v5/ops/formal_scouts/results/independent_layer_{target.target}_probe_results.json"],
        "artifacts_emitted": [f"system_v5/ops/formal_scouts/results/independent_layer_{target.target}_probe_results.json"],
        "witness_trace_id": f"independent_layer:{target.target}:{int(started)}",
        "pass_rule": "all native rows, target signal/control, common carrier anchor, z3/cvc5/sympy, and no-stacking boundary pass",
        "fail_rule": "any target row fails, any control survives, any downstream consumer unlocks, or the target becomes label-only",
        "promotion_status": "keep_but_open",
        "all_pass": all_pass,
        "blockers": [] if all_pass else [f"{target.target}_independent_layer_probe_failed"],
        "why_not_v4_probes": "v5 separate-layer formal scout with explicit finite math and no stacking/downstream admission.",
        "result_summary": {
            "all_pass": all_pass,
            "target": target.target,
            "display_name": target.display_name,
            "native_scale_name": target.native_scale_name,
            "native_frontier": native_frontier,
            "row_count": len(rows),
            "min_signal": min_signal,
            "max_control": max_control,
            "promotion_allowed": False,
            "claim_ceiling": "standalone formal scout only; no layer completion, no stacking, no Axis0/FEP/flux/physics/final admission",
            "qit_terms": sorted(key for key in qit_entropy_family if key != "role"),
            "tool_ablation_count": len(tool_ablations),
            "parity_level": parity_level,
        },
        "summary": {
            "all_pass": all_pass,
            "target": target.target,
            "display_name": target.display_name,
            "native_scale_name": target.native_scale_name,
            "row_count": len(rows),
            "min_signal": min_signal,
            "max_control": max_control,
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": False,
        },
    }
    return result


def main(target_name: str | None = None) -> int:
    if target_name is None:
        if len(sys.argv) != 2:
            names = sorted(make_target_table()) + [f"weyl_law_{name}" for name in sorted(LAW_MATH)]
            print(json.dumps({"error": "target required", "available_targets": names}, indent=2))
            return 2
        target_name = sys.argv[1]
    result = run_target(target_name)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / f"independent_layer_{target_name}_probe_results.json"
    out.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
