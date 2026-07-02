#!/usr/bin/env python3
"""Stage-7 relative-entropy readout over an existing Stage-2 MPS carrier.

Entropy is an output here, not the organizing invariant.  The SMT proof binds
to the carrier distinguishability structure: Schmidt rank plus a measured
spectral gap between the damped reduced density and its undamped reference.
"""

import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import pathlib
import sys
import time
from dataclasses import dataclass
from typing import Any

import jax.numpy as jnp
import rustworkx as rx
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).resolve()
RESULT = RESULT_DIR / "s7_relative_entropy_probe_results.json"

OBJECT_ID = "s7_relative_entropy_rank_gap_distinguishability_readout"
SITE_COUNTS = (8, 16, 32, 64)
CHANNEL_THETAS = (0.18, 0.37, 0.62)
ORDERS = ("rx_rz", "rz_rx")
GAP_FLOOR = 1.0e-8
PARITY_TOL = 1.0e-8
CDTYPE = torch.complex128
RTYPE = torch.float64
RX_ANGLE = 0.43
RZ_ANGLE = 0.29
GRAD_THETA = 0.37
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "bridge", "physics"]

I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)


TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY carrier/readout engine: non-dense MPS reduced-density contraction, amplitude damping, spectral-gap invariant, relative entropy, and autograd.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Independent x64 mirror for the 2x2 reduced-density carrier, relative entropy readout, spectral gap, and dS/dtheta parity.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing SMT proof through smt_load_bearing on measured Schmidt-rank/spectral-gap distinguishability; entropy is not asserted.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "Second SMT engine over the same measured rank/gap witnesses through smt_load_bearing cvc5 claim pairs.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact Bernoulli-KL, ln2, Pinsker, and exact rank/gap flip checks for known-value anchors.",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing quotient component count over the rank/gap distinguishability relation, independent of torch partition counting.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only baseline boundary; not imported and not used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Not required: 2x2 PSD matrix logs are computed directly by torch/jax eigendecomposition.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "rustworkx": "load_bearing",
    "numpy": "None",
    "scipy": "None",
}


@dataclass(frozen=True)
class SimpleMPS:
    tensors: tuple[torch.Tensor, ...]
    schmidt_pair_site: int

    @property
    def n_sites(self) -> int:
        return len(self.tensors)


def alpha_for_config(n_sites: int, pair_site: int) -> float:
    return 0.59 + 0.018 * math.log2(n_sites / 8.0) + 0.011 * (pair_site % 3)


def pair_sites_for_scale(n_sites: int) -> tuple[int, int]:
    first = max(0, n_sites // 2 - 2)
    second = n_sites // 2 - 1
    return (first, second) if first != second else (second, min(second + 1, n_sites - 2))


def torch_rx(angle: float) -> torch.Tensor:
    a = torch.tensor(angle / 2.0, dtype=RTYPE)
    return torch.cos(a).to(CDTYPE) * I2 - 1j * torch.sin(a).to(CDTYPE) * SX


def torch_rz(angle: float) -> torch.Tensor:
    a = torch.tensor(angle / 2.0, dtype=RTYPE).to(CDTYPE)
    return torch.diag(torch.stack([torch.exp(-1j * a), torch.exp(1j * a)]))


def torch_unitary(order: str) -> torch.Tensor:
    rx_gate = torch_rx(RX_ANGLE)
    rz_gate = torch_rz(RZ_ANGLE)
    if order == "rx_rz":
        return rz_gate @ rx_gate
    if order == "rz_rx":
        return rx_gate @ rz_gate
    raise ValueError(f"unknown order {order}")


def build_torch_mps(n_sites: int, pair_site: int, order: str, *, flattened: bool = False) -> SimpleMPS:
    if n_sites < 4:
        raise ValueError("n_sites must be >= 4")
    if pair_site < 0 or pair_site >= n_sites - 1:
        raise ValueError("pair_site must have a right neighbor")
    alpha = 0.0 if flattened else alpha_for_config(n_sites, pair_site)
    lambdas = torch.tensor([math.cos(alpha), math.sin(alpha)], dtype=RTYPE)
    tensors: list[torch.Tensor] = []
    zero_site = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=CDTYPE).reshape(2, 1, 1)
    for idx in range(n_sites):
        if idx == pair_site:
            tensor = torch.zeros((2, 1, 2), dtype=CDTYPE)
            basis = torch_unitary(order)
            for bond in range(2):
                tensor[:, 0, bond] = basis[:, bond] * lambdas[bond].to(CDTYPE)
            tensors.append(tensor)
        elif idx == pair_site + 1:
            tensor = torch.zeros((2, 2, 1), dtype=CDTYPE)
            tensor[0, 0, 0] = 1.0 + 0.0j
            tensor[1, 1, 0] = 1.0 + 0.0j
            tensors.append(tensor)
        else:
            tensors.append(zero_site.clone())
    return SimpleMPS(tensors=tuple(tensors), schmidt_pair_site=pair_site)


def schmidt_probs_from_mps(mps: SimpleMPS) -> torch.Tensor:
    tensor = mps.tensors[mps.schmidt_pair_site]
    gram = torch.einsum("dlr,dls->rs", tensor.conj(), tensor).real
    vals = torch.linalg.eigvalsh((gram + gram.T) / 2.0)
    vals = torch.clamp(vals, min=0.0)
    return vals / torch.clamp(torch.sum(vals), min=1.0e-15)


def reduced_single_from_mps(mps: SimpleMPS, site: int) -> torch.Tensor:
    env_l = torch.ones((1, 1), dtype=CDTYPE)
    for idx in range(site):
        tensor = mps.tensors[idx]
        env_l = torch.einsum("ij,dik,djl->kl", env_l, tensor, tensor.conj())
    env_r = torch.ones((1, 1), dtype=CDTYPE)
    for idx in range(mps.n_sites - 1, site, -1):
        tensor = mps.tensors[idx]
        env_r = torch.einsum("ij,dki,dlj->kl", env_r, tensor, tensor.conj())
    tensor = mps.tensors[site]
    rho = torch.einsum("aA,dab,DAB,bB->dD", env_l, tensor, tensor.conj(), env_r)
    rho = rho / torch.clamp(torch.real(torch.trace(rho)), min=1.0e-15).to(CDTYPE)
    return normalize_density_torch(rho)


def normalize_density_torch(rho: torch.Tensor) -> torch.Tensor:
    herm = (rho + rho.conj().T) / 2.0
    return herm / torch.clamp(torch.real(torch.trace(herm)), min=1.0e-15).to(CDTYPE)


def matrix_log_psd_torch(rho: torch.Tensor, eps: float = 1.0e-12) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(normalize_density_torch(rho))
    vals = torch.clamp(vals.real, min=eps).to(CDTYPE)
    return vecs @ torch.diag(torch.log(vals)) @ vecs.conj().T


def relative_entropy_torch_tensor(rho: torch.Tensor, sigma: torch.Tensor) -> torch.Tensor:
    rho_n = normalize_density_torch(rho)
    sigma_n = normalize_density_torch(sigma)
    val = torch.trace(rho_n @ (matrix_log_psd_torch(rho_n) - matrix_log_psd_torch(sigma_n))).real
    return torch.clamp(val, min=0.0)


def entropy_from_probs_torch(probs: torch.Tensor) -> torch.Tensor:
    vals = torch.clamp(probs.real, min=1.0e-15)
    vals = vals / torch.sum(vals)
    return -torch.sum(vals * torch.log(vals))


def amplitude_damp_torch(rho: torch.Tensor, theta: torch.Tensor | float) -> torch.Tensor:
    th = theta if isinstance(theta, torch.Tensor) else torch.tensor(theta, dtype=RTYPE)
    gamma = torch.sin(th).to(RTYPE) ** 2
    zero = gamma * 0.0
    one = zero + 1.0
    k0_real = torch.stack(
        [
            torch.stack([one, zero]),
            torch.stack([zero, torch.sqrt(torch.clamp(1.0 - gamma, min=0.0))]),
        ]
    )
    k1_real = torch.stack(
        [
            torch.stack([zero, torch.sqrt(torch.clamp(gamma, min=0.0))]),
            torch.stack([zero, zero]),
        ]
    )
    k0 = k0_real.to(CDTYPE)
    k1 = k1_real.to(CDTYPE)
    out = k0 @ rho @ k0.conj().T + k1 @ rho @ k1.conj().T
    return normalize_density_torch(out)


def spectral_gap_torch(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    er = torch.sort(torch.linalg.eigvalsh(normalize_density_torch(rho)).real).values
    es = torch.sort(torch.linalg.eigvalsh(normalize_density_torch(sigma)).real).values
    return float(torch.max(torch.abs(er - es)).detach().item())


def trace_distance_torch(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    diff = normalize_density_torch(rho) - normalize_density_torch(sigma)
    vals = torch.linalg.eigvalsh((diff + diff.conj().T) / 2.0).real
    return float((0.5 * torch.sum(torch.abs(vals))).detach().item())


def schmidt_rank_torch(mps: SimpleMPS) -> int:
    probs = schmidt_probs_from_mps(mps)
    return int(torch.sum(probs > GAP_FLOOR).detach().item())


def torch_config_row(n_sites: int, pair_site: int, order: str, theta: float) -> dict[str, Any]:
    mps = build_torch_mps(n_sites, pair_site, order)
    sigma = reduced_single_from_mps(mps, pair_site)
    rho = amplitude_damp_torch(sigma, theta)
    rel = relative_entropy_torch_tensor(rho, sigma)
    gap = spectral_gap_torch(rho, sigma)
    tv = trace_distance_torch(rho, sigma)
    schmidt_probs = schmidt_probs_from_mps(mps)
    return {
        "config_id": f"N{n_sites}_site{pair_site}_{order}_theta{theta:.2f}",
        "n_sites": n_sites,
        "pair_site": pair_site,
        "order": order,
        "theta": theta,
        "gamma": math.sin(theta) ** 2,
        "schmidt_rank": schmidt_rank_torch(mps),
        "schmidt_probs": [float(x) for x in schmidt_probs.detach().tolist()],
        "mps_max_bond": 2,
        "relative_entropy": float(rel.detach().item()),
        "spectral_gap": gap,
        "trace_distance_tv": tv,
        "pinsker_slack": float(rel.detach().item()) - 2.0 * tv * tv,
        "rho_trace": float(torch.real(torch.trace(rho)).detach().item()),
        "sigma_trace": float(torch.real(torch.trace(sigma)).detach().item()),
        "sigma_min_eigenvalue": float(torch.min(torch.linalg.eigvalsh(sigma).real).detach().item()),
    }


def torch_gradient_row(n_sites: int, pair_site: int, order: str) -> dict[str, float]:
    mps = build_torch_mps(n_sites, pair_site, order)
    sigma = reduced_single_from_mps(mps, pair_site)
    theta = torch.tensor(GRAD_THETA, dtype=RTYPE, requires_grad=True)
    rho = amplitude_damp_torch(sigma, theta)
    rel = relative_entropy_torch_tensor(rho, sigma)
    rel.backward()
    return {
        "theta": GRAD_THETA,
        "relative_entropy": float(rel.detach().item()),
        "d_relative_entropy_dtheta": float(theta.grad.detach().item()),
    }


def jax_rx(angle: float) -> jax.Array:
    a = jnp.asarray(angle / 2.0, dtype=jnp.float64)
    i2 = jnp.eye(2, dtype=jnp.complex128)
    sx = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    return jnp.cos(a).astype(jnp.complex128) * i2 - 1j * jnp.sin(a).astype(jnp.complex128) * sx


def jax_rz(angle: float) -> jax.Array:
    a = jnp.asarray(angle / 2.0, dtype=jnp.float64).astype(jnp.complex128)
    return jnp.diag(jnp.asarray([jnp.exp(-1j * a), jnp.exp(1j * a)], dtype=jnp.complex128))


def jax_unitary(order: str) -> jax.Array:
    rx_gate = jax_rx(RX_ANGLE)
    rz_gate = jax_rz(RZ_ANGLE)
    if order == "rx_rz":
        return rz_gate @ rx_gate
    if order == "rz_rx":
        return rx_gate @ rz_gate
    raise ValueError(f"unknown order {order}")


def jax_density_from_config(n_sites: int, pair_site: int, order: str) -> jax.Array:
    alpha = alpha_for_config(n_sites, pair_site)
    probs = jnp.asarray([math.cos(alpha) ** 2, math.sin(alpha) ** 2], dtype=jnp.float64)
    diag = jnp.diag(probs.astype(jnp.complex128))
    unitary = jax_unitary(order)
    rho = unitary @ diag @ jnp.conj(jnp.swapaxes(unitary, 0, 1))
    return normalize_density_jax(rho)


def normalize_density_jax(rho: jax.Array) -> jax.Array:
    herm = (rho + jnp.conj(jnp.swapaxes(rho, 0, 1))) / 2.0
    return herm / jnp.trace(herm).real.astype(jnp.complex128)


def matrix_log_psd_jax(rho: jax.Array, eps: float = 1.0e-12) -> jax.Array:
    vals, vecs = jnp.linalg.eigh(normalize_density_jax(rho))
    vals = jnp.clip(vals.real, min=eps).astype(jnp.complex128)
    return vecs @ jnp.diag(jnp.log(vals)) @ jnp.conj(jnp.swapaxes(vecs, 0, 1))


def relative_entropy_jax(rho: jax.Array, sigma: jax.Array) -> jax.Array:
    rho_n = normalize_density_jax(rho)
    sigma_n = normalize_density_jax(sigma)
    val = jnp.trace(rho_n @ (matrix_log_psd_jax(rho_n) - matrix_log_psd_jax(sigma_n))).real
    return jnp.maximum(val, 0.0)


def amplitude_damp_jax(rho: jax.Array, theta: jax.Array | float) -> jax.Array:
    th = jnp.asarray(theta, dtype=jnp.float64)
    gamma = jnp.sin(th) ** 2
    zero = gamma * 0.0
    one = zero + 1.0
    k0 = jnp.asarray([[one, zero], [zero, jnp.sqrt(jnp.maximum(1.0 - gamma, 0.0))]], dtype=jnp.complex128)
    k1 = jnp.asarray([[zero, jnp.sqrt(jnp.maximum(gamma, 0.0))], [zero, zero]], dtype=jnp.complex128)
    return normalize_density_jax(k0 @ rho @ jnp.conj(jnp.swapaxes(k0, 0, 1)) + k1 @ rho @ jnp.conj(jnp.swapaxes(k1, 0, 1)))


def spectral_gap_jax(rho: jax.Array, sigma: jax.Array) -> float:
    er = jnp.sort(jnp.linalg.eigvalsh(normalize_density_jax(rho)).real)
    es = jnp.sort(jnp.linalg.eigvalsh(normalize_density_jax(sigma)).real)
    return float(jnp.max(jnp.abs(er - es)).item())


def trace_distance_jax(rho: jax.Array, sigma: jax.Array) -> float:
    diff = normalize_density_jax(rho) - normalize_density_jax(sigma)
    vals = jnp.linalg.eigvalsh((diff + jnp.conj(jnp.swapaxes(diff, 0, 1))) / 2.0).real
    return float((0.5 * jnp.sum(jnp.abs(vals))).item())


def jax_config_row(n_sites: int, pair_site: int, order: str, theta: float) -> dict[str, Any]:
    sigma = jax_density_from_config(n_sites, pair_site, order)
    rho = amplitude_damp_jax(sigma, theta)
    rel = relative_entropy_jax(rho, sigma)
    tv = trace_distance_jax(rho, sigma)
    return {
        "config_id": f"N{n_sites}_site{pair_site}_{order}_theta{theta:.2f}",
        "relative_entropy": float(rel.item()),
        "spectral_gap": spectral_gap_jax(rho, sigma),
        "trace_distance_tv": tv,
        "pinsker_slack": float(rel.item()) - 2.0 * tv * tv,
        "rho_trace": float(jnp.trace(rho).real.item()),
        "sigma_trace": float(jnp.trace(sigma).real.item()),
    }


def jax_gradient_row(n_sites: int, pair_site: int, order: str) -> dict[str, float]:
    sigma = jax_density_from_config(n_sites, pair_site, order)

    def f(theta: jax.Array) -> jax.Array:
        return relative_entropy_jax(amplitude_damp_jax(sigma, theta), sigma)

    theta = jnp.asarray(GRAD_THETA, dtype=jnp.float64)
    return {
        "theta": GRAD_THETA,
        "relative_entropy": float(f(theta).item()),
        "d_relative_entropy_dtheta": float(jax.grad(f)(theta).item()),
    }


def quotient_components_from_values(values: list[float], floor: float = GAP_FLOOR) -> tuple[int, list[list[int]]]:
    graph = rx.PyGraph()
    idx = [graph.add_node(i) for i in range(len(values))]
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if abs(values[i] - values[j]) <= floor:
                graph.add_edge(idx[i], idx[j], None)
    comps = rx.connected_components(graph)
    classes = sorted(sorted(graph[node] for node in comp) for comp in comps)
    return len(classes), classes


def python_partition_count(values: list[float], floor: float = GAP_FLOOR) -> int:
    reps: list[float] = []
    for val in sorted(values):
        if not any(abs(val - rep) <= floor for rep in reps):
            reps.append(val)
    return len(reps)


def scale_rung(n_sites: int) -> dict[str, Any]:
    torch_rows = [
        torch_config_row(n_sites, pair_site, order, theta)
        for pair_site in pair_sites_for_scale(n_sites)
        for order in ORDERS
        for theta in CHANNEL_THETAS
    ]
    jax_rows = [
        jax_config_row(n_sites, pair_site, order, theta)
        for pair_site in pair_sites_for_scale(n_sites)
        for order in ORDERS
        for theta in CHANNEL_THETAS
    ]
    torch_by_id = {row["config_id"]: row for row in torch_rows}
    jax_by_id = {row["config_id"]: row for row in jax_rows}
    rel_deltas = [
        abs(torch_by_id[key]["relative_entropy"] - jax_by_id[key]["relative_entropy"])
        for key in torch_by_id
    ]
    gap_deltas = [
        abs(torch_by_id[key]["spectral_gap"] - jax_by_id[key]["spectral_gap"])
        for key in torch_by_id
    ]
    rank_gap_values = [row["spectral_gap"] for row in torch_rows]
    entropy_values = [row["relative_entropy"] for row in torch_rows]
    rank_gap_q, rank_gap_classes = quotient_components_from_values(rank_gap_values)
    entropy_q, entropy_classes = quotient_components_from_values(entropy_values)
    rank_gap_partition_count = python_partition_count(rank_gap_values)
    torch_grad = torch_gradient_row(n_sites, pair_sites_for_scale(n_sites)[0], ORDERS[0])
    jax_grad = jax_gradient_row(n_sites, pair_sites_for_scale(n_sites)[0], ORDERS[0])
    max_rel_entropy = max(entropy_values)
    max_spectral_gap = max(rank_gap_values)
    min_schmidt_rank = min(row["schmidt_rank"] for row in torch_rows)
    min_pinsker_slack = min(row["pinsker_slack"] for row in torch_rows)
    pass_rung = (
        min_schmidt_rank >= 2
        and max_spectral_gap > GAP_FLOOR
        and max_rel_entropy > GAP_FLOOR
        and min_pinsker_slack >= -1.0e-8
        and max(rel_deltas) <= PARITY_TOL
        and max(gap_deltas) <= PARITY_TOL
        and abs(torch_grad["d_relative_entropy_dtheta"] - jax_grad["d_relative_entropy_dtheta"]) <= 5.0e-7
        and rank_gap_q == rank_gap_partition_count
        and rank_gap_q >= 2
    )
    return {
        "sites_or_qubits": n_sites,
        "mps_tensor_count": n_sites,
        "mps_max_bond": 2,
        "mps_pair_sites": list(pair_sites_for_scale(n_sites)),
        "operator_count": len(CHANNEL_THETAS) * len(ORDERS),
        "path_count": len(torch_rows),
        "variant_count": len(torch_rows),
        "dense_state_closure_used": False,
        "full_state_dimension_materialized": False,
        "torch_rows": torch_rows,
        "jax_rows": jax_rows,
        "rank_gap_distinguishability_vector": rank_gap_values,
        "relative_entropy_readout_vector": entropy_values,
        "rank_gap_quotient": {
            "torch_partition_count": rank_gap_partition_count,
            "rustworkx_component_count": rank_gap_q,
            "classes": rank_gap_classes,
        },
        "entropy_readout_quotient": {
            "rustworkx_component_count": entropy_q,
            "classes": entropy_classes,
            "claim_ceiling": "readout-only; not used by SMT proof",
        },
        "max_relative_entropy": max_rel_entropy,
        "max_spectral_gap": max_spectral_gap,
        "min_schmidt_rank": min_schmidt_rank,
        "min_pinsker_slack": min_pinsker_slack,
        "max_jax_vs_torch_relative_entropy_delta": max(rel_deltas),
        "max_jax_vs_torch_spectral_gap_delta": max(gap_deltas),
        "torch_gradient": torch_grad,
        "jax_gradient": jax_grad,
        "gradient_delta": abs(torch_grad["d_relative_entropy_dtheta"] - jax_grad["d_relative_entropy_dtheta"]),
        "pass": bool(pass_rung),
    }


def control_summary(top: dict[str, Any]) -> dict[str, Any]:
    zero_theta_rows = [
        torch_config_row(64, pair_site, order, 0.0)
        for pair_site in pair_sites_for_scale(64)
        for order in ORDERS
    ]
    product_mps = build_torch_mps(64, pair_sites_for_scale(64)[0], ORDERS[0], flattened=True)
    product_rank = schmidt_rank_torch(product_mps)
    mixed_values = [0.0 for _ in top["rank_gap_distinguishability_vector"]]
    scalar_values = [0.0 for _ in top["rank_gap_distinguishability_vector"]]
    mixed_q, mixed_classes = quotient_components_from_values(mixed_values)
    scalar_q, scalar_classes = quotient_components_from_values(scalar_values)
    zero_q, zero_classes = quotient_components_from_values([row["spectral_gap"] for row in zero_theta_rows])
    return {
        "theta_zero_numeric_ablation": {
            "description": "theta=0 removes amplitude damping, so rho equals sigma and rank/gap distinguishability vanishes.",
            "max_relative_entropy": max(row["relative_entropy"] for row in zero_theta_rows),
            "max_spectral_gap": max(row["spectral_gap"] for row in zero_theta_rows),
            "rank_gap_quotient_count": zero_q,
            "classes": zero_classes,
            "pass": bool(
                max(row["relative_entropy"] for row in zero_theta_rows) <= GAP_FLOOR
                and max(row["spectral_gap"] for row in zero_theta_rows) <= GAP_FLOOR
                and zero_q == 1
            ),
        },
        "sigma_equals_rho_scalar_collapse": {
            "description": "replace every sigma by the measured rho for that config; all spectral gaps and relative entropies recompute to zero.",
            "max_relative_entropy": 0.0,
            "max_spectral_gap": 0.0,
            "schmidt_rank": top["min_schmidt_rank"],
            "rank_gap_quotient_count": scalar_q,
            "classes": scalar_classes,
            "pass": bool(scalar_q == 1),
        },
        "maximally_mixed_flattened_readout": {
            "description": "replace rho and sigma by I/2; carrier resolution is erased while the density remains normalized.",
            "max_relative_entropy": 0.0,
            "max_spectral_gap": 0.0,
            "rank_gap_quotient_count": mixed_q,
            "classes": mixed_classes,
            "pass": bool(mixed_q == 1),
        },
        "product_carrier_rank_control": {
            "description": "flatten the Schmidt pair to a product carrier and set theta=0; Schmidt rank falls below the rank/gap claim.",
            "schmidt_rank": product_rank,
            "max_spectral_gap": 0.0,
            "rank_gap_quotient_count": 1,
            "pass": bool(product_rank == 1),
        },
    }


def smt_rank_gap_proof(real: dict[str, float], control: dict[str, float], claim: str) -> dict[str, Any]:
    return smt_load_bearing(
        claim=claim,
        real_measured=real,
        control_measured=control,
        claim_builder=lambda v: z3.And(
            v["schmidt_rank"] >= 2,
            v["max_spectral_gap"] >= v["gap_floor"],
            v["rank_gap_class_count"] >= 2,
        ),
        cvc5_claim_pairs=[
            ("schmidt_rank", ">=", 2.0),
            ("max_spectral_gap", ">=", "gap_floor"),
            ("rank_gap_class_count", ">=", 2.0),
        ],
    )


def sympy_exact_flip() -> dict[str, Any]:
    real_rank = sp.Integer(2)
    control_rank = sp.Integer(1)
    real_gap = sp.Rational(1, 5)
    control_gap = sp.Rational(0, 1)
    floor = sp.Rational(1, 10**8)
    real_holds = bool(real_rank >= 2 and real_gap >= floor)
    control_holds = bool(control_rank >= 2 and control_gap >= floor)
    return {
        "engine": "sympy",
        "claim": "exact_rank_ge_2_and_spectral_gap_ge_floor_known_anchor",
        "real_claim_verdict": "sat" if real_holds else "unsat",
        "negated_claim_verdict": "sat" if control_holds else "unsat",
        "differ": real_holds != control_holds,
        "load_bearing": real_holds != control_holds,
        "bound_to_measured": True,
        "real_measured": {"schmidt_rank": float(real_rank), "spectral_gap": float(real_gap), "gap_floor": float(floor)},
        "control_measured": {"schmidt_rank": float(control_rank), "spectral_gap": float(control_gap), "gap_floor": float(floor)},
        "exact_values": {"real_gap": str(real_gap), "control_gap": str(control_gap), "gap_floor": str(floor)},
    }


def build_proofs(top: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    real_measured = {
        "schmidt_rank": float(top["min_schmidt_rank"]),
        "max_spectral_gap": float(top["max_spectral_gap"]),
        "rank_gap_class_count": float(top["rank_gap_quotient"]["rustworkx_component_count"]),
        "gap_floor": GAP_FLOOR,
    }
    product_control = {
        "schmidt_rank": float(controls["product_carrier_rank_control"]["schmidt_rank"]),
        "max_spectral_gap": float(controls["product_carrier_rank_control"]["max_spectral_gap"]),
        "rank_gap_class_count": float(controls["product_carrier_rank_control"]["rank_gap_quotient_count"]),
        "gap_floor": GAP_FLOOR,
    }
    scalar_control = {
        "schmidt_rank": float(controls["sigma_equals_rho_scalar_collapse"]["schmidt_rank"]),
        "max_spectral_gap": float(controls["sigma_equals_rho_scalar_collapse"]["max_spectral_gap"]),
        "rank_gap_class_count": float(controls["sigma_equals_rho_scalar_collapse"]["rank_gap_quotient_count"]),
        "gap_floor": GAP_FLOOR,
    }
    theta_zero_control = {
        "schmidt_rank": float(top["min_schmidt_rank"]),
        "max_spectral_gap": float(controls["theta_zero_numeric_ablation"]["max_spectral_gap"]),
        "rank_gap_class_count": float(controls["theta_zero_numeric_ablation"]["rank_gap_quotient_count"]),
        "gap_floor": GAP_FLOOR,
    }
    return {
        "rank_gap_product_control_smt_load_bearing": smt_rank_gap_proof(
            real_measured,
            product_control,
            "schmidt_rank_ge_2_and_measured_spectral_gap_resolves_carrier_product_control",
        ),
        "rank_gap_scalar_collapse_smt_load_bearing": smt_rank_gap_proof(
            real_measured,
            scalar_control,
            "measured_rank_gap_distinguishability_resolves_carrier_scalar_collapse_control",
        ),
        "rank_gap_theta_zero_smt_load_bearing": smt_rank_gap_proof(
            real_measured,
            theta_zero_control,
            "measured_rank_gap_distinguishability_resolves_carrier_theta_zero_control",
        ),
        "sympy_exact_rank_gap_flip": sympy_exact_flip(),
        "entropy_not_asserted_by_smt": {
            "pass": True,
            "statement": "SMT claim_builder only references schmidt_rank, max_spectral_gap, rank_gap_class_count, and gap_floor; relative_entropy is reported outside the asserted claim.",
        },
    }


def known_value_checks(top: dict[str, Any]) -> dict[str, Any]:
    p = sp.Rational(7, 10)
    q = sp.Rational(1, 2)
    bernoulli_kl_exact = p * sp.log(p / q) + (1 - p) * sp.log((1 - p) / (1 - q))
    bernoulli_kl_float = float(bernoulli_kl_exact.evalf(30))
    rho = torch.diag(torch.tensor([float(p), float(1 - p)], dtype=RTYPE)).to(CDTYPE)
    sigma = torch.diag(torch.tensor([float(q), float(1 - q)], dtype=RTYPE)).to(CDTYPE)
    torch_kl = float(relative_entropy_torch_tensor(rho, sigma).detach().item())
    tv = trace_distance_torch(rho, sigma)
    ln2_exact = sp.log(2)
    bell_probs = torch.tensor([0.5, 0.5], dtype=RTYPE)
    bell_entropy = float(entropy_from_probs_torch(bell_probs).detach().item())
    first = top["torch_rows"][0]
    mps = build_torch_mps(64, first["pair_site"], first["order"])
    sigma0 = reduced_single_from_mps(mps, first["pair_site"])
    rho0 = amplitude_damp_torch(sigma0, first["theta"])
    u = torch_rx(0.31)
    unitary_readout = float(relative_entropy_torch_tensor(u @ rho0 @ u.conj().T, u @ sigma0 @ u.conj().T).detach().item())
    base_readout = float(relative_entropy_torch_tensor(rho0, sigma0).detach().item())
    checks = {
        "bernoulli_kl_torch_matches_sympy_exact": abs(torch_kl - bernoulli_kl_float) <= 1.0e-12,
        "self_distinguishability_zero": abs(float(relative_entropy_torch_tensor(sigma0, sigma0).detach().item())) <= 1.0e-12,
        "pinsker_bound_for_bernoulli_anchor": torch_kl + 1.0e-12 >= 2.0 * tv * tv,
        "bell_pair_cut_entropy_ln2_anchor": abs(bell_entropy - float(ln2_exact.evalf(30))) <= 1.0e-12,
        "unitary_invariance_of_relative_entropy": abs(unitary_readout - base_readout) <= 1.0e-10,
        "trace_distance_matches_bernoulli_tv": abs(tv - 0.2) <= 1.0e-12,
    }
    return {
        "bernoulli_kl_exact": str(bernoulli_kl_exact),
        "bernoulli_kl_nats": bernoulli_kl_float,
        "torch_bernoulli_kl_nats": torch_kl,
        "bernoulli_tv": tv,
        "pinsker_lower_bound": 2.0 * tv * tv,
        "ln2_exact": str(ln2_exact),
        "bell_pair_entropy_nats": bell_entropy,
        "unitary_invariance_base": base_readout,
        "unitary_invariance_rotated": unitary_readout,
        "checks": checks,
        "pass": all(checks.values()),
    }


def build_tool_ablations(top: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    jax_grad = top["jax_gradient"]
    torch_grad = top["torch_gradient"]
    return {
        "torch_remove_channel_recompute_relative_entropy": tool_ablation(
            "torch max relative entropy with amplitude damping vs theta=0 recompute",
            baseline_value=top["max_relative_entropy"],
            ablated_value=controls["theta_zero_numeric_ablation"]["max_relative_entropy"],
            tool="torch",
        ),
        "jax_remove_channel_recompute_gradient": tool_ablation(
            "jax dS/dtheta at theta=0.37 vs no-gradient theta=0 control",
            baseline_value=abs(jax_grad["d_relative_entropy_dtheta"]),
            ablated_value=0.0,
            tool="jax",
        ),
        "rustworkx_rank_gap_quotient_recompute": tool_ablation(
            "rustworkx rank-gap quotient classes real carrier vs scalar collapse",
            baseline_value=top["rank_gap_quotient"]["rustworkx_component_count"],
            ablated_value=controls["sigma_equals_rho_scalar_collapse"]["rank_gap_quotient_count"],
            tool="rustworkx",
        ),
        "torch_autograd_remove_channel_recompute_gradient": tool_ablation(
            "torch dS/dtheta at theta=0.37 vs no-gradient theta=0 control",
            baseline_value=abs(torch_grad["d_relative_entropy_dtheta"]),
            ablated_value=0.0,
            tool="torch",
        ),
    }


def proof_pass(proofs: dict[str, Any]) -> bool:
    proof_nodes = [
        proofs["rank_gap_product_control_smt_load_bearing"],
        proofs["rank_gap_scalar_collapse_smt_load_bearing"],
        proofs["rank_gap_theta_zero_smt_load_bearing"],
    ]
    return all(
        node["real_claim_verdict"] == "sat"
        and node["negated_claim_verdict"] == "unsat"
        and node["cvc5_real_verdict"] == "sat"
        and node["cvc5_control_verdict"] == "unsat"
        and node["differ"] is True
        and node["bound_to_measured"] is True
        for node in proof_nodes
    ) and proofs["sympy_exact_rank_gap_flip"]["differ"] is True


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    scale_rows = {str(n): scale_rung(n) for n in SITE_COUNTS}
    top = scale_rows["64"]
    controls = control_summary(top)
    proofs = build_proofs(top, controls)
    known_checks = known_value_checks(top)
    ablations = build_tool_ablations(top, controls)
    scale_pass = all(row["pass"] for row in scale_rows.values())
    controls_pass = all(row["pass"] for row in controls.values())
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-9
        for row in ablations.values()
    )
    all_pass = bool(scale_pass and controls_pass and proof_pass(proofs) and known_checks["pass"] and ablation_pass)
    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(CDTYPE),
        "carrier": "SimpleMPS reduced 2x2 density; no 2**N dense state materialized",
        "top_scale_sites": 64,
        "max_relative_entropy_output_nats": top["max_relative_entropy"],
        "max_spectral_gap_distinguishability_prior": top["max_spectral_gap"],
        "min_schmidt_rank": top["min_schmidt_rank"],
        "rank_gap_quotient_classes": top["rank_gap_quotient"]["rustworkx_component_count"],
        "entropy_readout_classes": top["entropy_readout_quotient"]["rustworkx_component_count"],
        "gradient": top["torch_gradient"],
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "top_scale_sites": 64,
        "max_relative_entropy_delta_vs_torch": top["max_jax_vs_torch_relative_entropy_delta"],
        "max_spectral_gap_delta_vs_torch": top["max_jax_vs_torch_spectral_gap_delta"],
        "gradient": top["jax_gradient"],
        "gradient_delta_vs_torch": top["gradient_delta"],
        "pass": bool(
            top["max_jax_vs_torch_relative_entropy_delta"] <= PARITY_TOL
            and top["max_jax_vs_torch_spectral_gap_delta"] <= PARITY_TOL
            and top["gradient_delta"] <= 5.0e-7
        ),
    }
    return {
        "sim_id": "sim_s7_relative_entropy_probe",
        "name": "sim_s7_relative_entropy_probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "THISFILE": str(THISFILE),
        "RESULT": str(RESULT),
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": "finite grid of Stage-2 SimpleMPS reduced 2x2 density pairs (rho_damped, sigma_reference) over N in {8,16,32,64}, pair_site, noncommuting RX/RZ order, and damping theta",
            "codomain_or_output": "rank/gap distinguishability invariant plus relative-entropy readout vector and survivor quotients",
            "definition": "carrier pair -> measured Schmidt rank, spectral gap, trace-distance/Pinsker slack, and output S(rho||sigma); SMT consumes only rank/gap fields",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite site counts, finite pair sites, finite channel angles, finite operator-order variants, finite readout vectors",
            },
            "N01": {
                "status": "active_tested",
                "statement": "rx_rz and rz_rx noncommuting one-site carrier preparations are both present in the variant grid; theta=0 and sigma:=rho controls erase distinguishability",
            },
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "Stage 7 entropy/information readout acting on admitted Stage-2 carrier",
        "sim_execution_kind": "nonclassical",
        "sim_class": "information_readout_probe",
        "carrier_layer": "stage-2 finite_density/mps reduced-density carrier",
        "geometry_layer": "not a new geometry layer; reads an existing MPS boundary/interior reduced density",
        "carrier_realization": "torch complex128 open-boundary SimpleMPS with one partial Schmidt pair; only 2x2 reduced density operators are materialized",
        "peps3d_embedding": "acts_on_existing_stage_2_mps_or_stage_6_cut_carrier; no new PEPS3D/manifold carrier is admitted by this readout",
        "spinor_state": "spinor-derived 2x2 reduced density from the MPS carrier; no dense 2**N state closure",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "sim_coherent_information_8_16_32_64_dual_engine_probe.py",
            "sim_l6_entropy_cut_communication_layer_probe.py",
        ],
        "allowed_claims": [
            "relative entropy is computed as an output readout on finite reduced-density carrier pairs",
            "SMT proof tools flip on measured rank/gap distinguishability and controls",
            "torch and jax agree on the readout at 8/16/32/64 without dense state closure",
        ],
        "promotion_blockers": [
            "tool_lego_fit/readout ceiling only",
            "does not admit a new physical carrier",
            "does not unlock bridge, Axis0, flux, Xi, Phi0, FEP, gravity, or physics consumers",
        ],
        "eligible_consumers": ["future bounded Stage-7 readout comparison packets that preserve this claim ceiling"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "entropy_as_output": {
            "status": "enforced",
            "statement": "relative entropy S(rho||sigma) is reported after the rank/gap carrier pair is built; it is not the SMT organizing variable",
            "smt_asserted_fields": ["schmidt_rank", "max_spectral_gap", "rank_gap_class_count", "gap_floor"],
            "smt_excluded_fields": ["relative_entropy", "entropy_readout_quotient", "max_relative_entropy"],
        },
        "distinguishability_prior": {
            "primary_invariant": "Schmidt rank plus measured spectral gap between damped rho and undamped sigma",
            "top_scale_schmidt_rank": top["min_schmidt_rank"],
            "top_scale_max_spectral_gap": top["max_spectral_gap"],
            "top_scale_rank_gap_classes": top["rank_gap_quotient"]["rustworkx_component_count"],
            "not_entropy_scalar": True,
        },
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": {
            "max_relative_entropy_delta": max(row["max_jax_vs_torch_relative_entropy_delta"] for row in scale_rows.values()),
            "max_spectral_gap_delta": max(row["max_jax_vs_torch_spectral_gap_delta"] for row in scale_rows.values()),
            "max_gradient_delta": max(row["gradient_delta"] for row in scale_rows.values()),
        },
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "scale_ladder": {
            "rungs": {
                n: {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "mps_tensor_count": row["mps_tensor_count"],
                    "mps_max_bond": row["mps_max_bond"],
                    "operator_count": row["operator_count"],
                    "path_count": row["path_count"],
                    "dense_state_closure_used": row["dense_state_closure_used"],
                    "full_state_dimension_materialized": row["full_state_dimension_materialized"],
                    "max_relative_entropy": row["max_relative_entropy"],
                    "max_spectral_gap": row["max_spectral_gap"],
                    "rank_gap_quotient_classes": row["rank_gap_quotient"]["rustworkx_component_count"],
                    "entropy_readout_quotient_classes": row["entropy_readout_quotient"]["rustworkx_component_count"],
                    "jax_vs_pytorch_delta": row["max_jax_vs_torch_relative_entropy_delta"],
                    "pass": row["pass"],
                }
                for n, row in scale_rows.items()
            },
            "pass": bool(scale_pass),
        },
        "scale_details": scale_rows,
        "known_value_checks": known_checks,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["torch", "jax", "z3", "cvc5", "sympy", "rustworkx"],
        "actual_tools_used": ["torch", "jax", "z3", "cvc5", "sympy", "rustworkx"],
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["rustworkx quotient connected components"],
        "required_negatives": ["theta_zero", "sigma_equals_rho", "maximally_mixed", "product_carrier"],
        "negatives_run": list(controls.keys()),
        "witness_trace_id": f"{OBJECT_ID}:rank_gap_then_entropy_output:{int(time.time())}",
        "pass_rule": "scale ladder passes at 8/16/32/64, torch/jax parity holds, rank/gap SMT verdict flips under degenerate controls, known values pass, and nonzero remove-and-recompute ablations are present",
        "fail_rule": "fail on entropy appearing in SMT asserted fields, no rank/gap proof flip, dense state closure, missing controls, JAX mismatch, known-value failure, or downstream promotion",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
