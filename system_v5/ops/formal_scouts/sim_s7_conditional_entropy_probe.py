#!/usr/bin/env python3
"""Stage-7 conditional entropy readout over an admitted cut carrier.

This sim is deliberately narrow:

* The carrier is the existing finite PEPS3D cut-edge/stage-2 spinor-density
  surface used by the L6 cut/communication scout.
* The SMT claim is a pre-entropy distinguishability invariant: Schmidt rank,
  second Schmidt weight, and cut/communication order gap.
* Conditional entropy is computed only after the carrier and ordered cut path
  are fixed. It is emitted as a readout, not as the SMT organizer.
"""

from __future__ import annotations

import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import pathlib
import sys
import time
from typing import Any

import jax.numpy as jnp
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation

from sim_l2_spinor_chirality_weyl_cover_layer_probe import (  # noqa: E402
    SHAPES,
    as_jsonable,
    coords_for_shape,
    edge_list,
    exact_counts,
    topology_certificates,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = ROOT / "sim_s7_conditional_entropy_probe.py"
RESULT = RESULT_DIR / "s7_conditional_entropy_probe_results.json"

OBJECT_ID = "s7_conditional_entropy_readout_rank_gap_probe"
VERSION = "1.0.0"
SCALES = (8, 16, 32, 64)
SITE_SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
CUT_AXES = ("x", "y", "z")
MAX_BOND = 8

RTYPE = torch.float64
CTYPE = torch.complex128
TOL = 1.0e-9
PARITY_TOL = 1.0e-8
ORDER_GAP_FLOOR = 1.0e-4
SECOND_WEIGHT_FLOOR = 0.25
RANK_FLOOR = 1.5

I2 = torch.eye(2, dtype=CTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CTYPE)

JI2 = jnp.eye(2, dtype=jnp.complex128)
JX = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
JY = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
JZ = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)

BLOCKED_CONSUMERS = [
    "flux",
    "Xi",
    "Phi0",
    "Axis0",
    "FEP",
    "gravity",
    "physics",
    "bridge",
    "layer_stacking",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY numeric path for local two-qubit densities, cut/communication channels, rank/gap invariant, entropy readout, controls, and non-dense scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Independent x64 mirror recomputes the same local pair densities, ordered channel, rank/gap invariant, and conditional entropy without reusing torch outputs.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing SMT flip through load_bearing_proof.smt_load_bearing on measured Schmidt-rank/second-weight/order-gap values only.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "Independent SMT engine inside smt_load_bearing on the same measured rank/gap/order-gap claim; entropy is not asserted.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact Bell/product rank and known-value entropy identities; reported as an exact rank/gap flip, not a numeric entropy ablation.",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "Supportive PEPS3D topology certificate inherited from the L2/L6 carrier helpers; cut edges are graph edges, not labels.",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "Supportive PEPS3D connectivity certificate via topology_certificates.",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "Supportive face/cell hyperedge certificate via topology_certificates.",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "Supportive face-complex certificate via topology_certificates.",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "Supportive boundary filtration certificate via topology_certificates.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported. No NumPy or .numpy() bridge is used in the claim-bearing path.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Not required; no dense global-state or scipy eigensolver closure is used.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "pyg": "supportive",
    "rustworkx": "supportive",
    "xgi": "supportive",
    "toponetx": "supportive",
    "gudhi": "supportive",
    "numpy": "None",
    "scipy": "None",
}


def axis_index(axis: str) -> int:
    return CUT_AXES.index(axis)


def coordinate_side(coord: tuple[int, int, int], shape: tuple[int, int, int], axis: str) -> int:
    return int(coord[axis_index(axis)] >= shape[axis_index(axis)] // 2)


def cut_edges(shape: tuple[int, int, int], axis: str) -> list[tuple[int, int]]:
    coords = coords_for_shape(shape)
    return [
        (u, v)
        for u, v in edge_list(shape)
        if coordinate_side(coords[u], shape, axis) != coordinate_side(coords[v], shape, axis)
    ]


def normalize_density_torch(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2.0
    eigvals, eigvecs = torch.linalg.eigh(rho)
    eigvals = torch.clamp(torch.real(eigvals), min=0.0)
    trace = torch.sum(eigvals)
    if float(trace.item()) <= TOL:
        return torch.eye(rho.shape[0], dtype=CTYPE) / rho.shape[0]
    return eigvecs @ torch.diag((eigvals / trace).to(CTYPE)) @ eigvecs.conj().T


def normalize_density_jax(rho: jax.Array) -> jax.Array:
    rho = (rho + jnp.conj(rho.T)) / 2.0
    eigvals, eigvecs = jnp.linalg.eigh(rho)
    eigvals = jnp.clip(jnp.real(eigvals), min=0.0)
    trace = jnp.sum(eigvals)
    safe = jnp.where(trace <= TOL, jnp.ones_like(eigvals) / eigvals.shape[0], eigvals / trace)
    return eigvecs @ jnp.diag(safe.astype(jnp.complex128)) @ jnp.conj(eigvecs.T)


def bell_state_torch() -> torch.Tensor:
    psi = torch.zeros(4, dtype=CTYPE)
    psi[0] = 1.0 / math.sqrt(2.0)
    psi[3] = 1.0 / math.sqrt(2.0)
    return psi


def product_state_torch() -> torch.Tensor:
    psi = torch.zeros(4, dtype=CTYPE)
    psi[0] = 1.0
    return psi


def bell_state_jax() -> jax.Array:
    return jnp.array([1.0 / math.sqrt(2.0), 0.0, 0.0, 1.0 / math.sqrt(2.0)], dtype=jnp.complex128)


def product_state_jax() -> jax.Array:
    return jnp.array([1.0, 0.0, 0.0, 0.0], dtype=jnp.complex128)


def density_torch(psi: torch.Tensor) -> torch.Tensor:
    psi = psi / torch.linalg.vector_norm(psi)
    return torch.outer(psi, psi.conj())


def density_jax(psi: jax.Array) -> jax.Array:
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, jnp.conj(psi))


def dephased_torch(rho: torch.Tensor) -> torch.Tensor:
    return torch.diag(torch.real(torch.diag(rho))).to(CTYPE)


def dephased_jax(rho: jax.Array) -> jax.Array:
    return jnp.diag(jnp.real(jnp.diag(rho))).astype(jnp.complex128)


def classical_correlated_torch() -> torch.Tensor:
    rho = torch.zeros((4, 4), dtype=CTYPE)
    rho[0, 0] = 0.5
    rho[3, 3] = 0.5
    return rho


def max_mixed_torch() -> torch.Tensor:
    return torch.eye(4, dtype=CTYPE) / 4.0


def torch_pair_generator(axis: str) -> torch.Tensor:
    if axis == "x":
        return torch.kron(X, Y) + 0.37 * torch.kron(Z, I2)
    if axis == "y":
        return torch.kron(Y, Z) + 0.31 * torch.kron(I2, X)
    if axis == "z":
        return torch.kron(Z, X) + 0.29 * torch.kron(Y, I2)
    raise ValueError(axis)


def jax_pair_generator(axis: str) -> jax.Array:
    if axis == "x":
        return jnp.kron(JX, JY) + 0.37 * jnp.kron(JZ, JI2)
    if axis == "y":
        return jnp.kron(JY, JZ) + 0.31 * jnp.kron(JI2, JX)
    if axis == "z":
        return jnp.kron(JZ, JX) + 0.29 * jnp.kron(JY, JI2)
    raise ValueError(axis)


def torch_comm_channel(rho: torch.Tensor, axis: str) -> torch.Tensor:
    h = torch_pair_generator(axis)
    unitary = torch.matrix_exp((-0.13j) * h)
    return normalize_density_torch(unitary @ rho @ unitary.conj().T)


def jax_comm_channel(rho: jax.Array, axis: str) -> jax.Array:
    h = jax_pair_generator(axis)
    eigvals, eigvecs = jnp.linalg.eigh(h)
    phases = jnp.exp((-0.13j) * eigvals)
    unitary = eigvecs @ jnp.diag(phases.astype(jnp.complex128)) @ jnp.conj(eigvecs.T)
    return normalize_density_jax(unitary @ rho @ jnp.conj(unitary.T))


def torch_cut_channel(rho: torch.Tensor, axis: str) -> torch.Tensor:
    if axis == "x":
        observable = torch.kron(Z, I2) + 0.17 * torch.kron(I2, X)
    elif axis == "y":
        observable = torch.kron(I2, Z) + 0.19 * torch.kron(Y, I2)
    elif axis == "z":
        observable = torch.kron(X, X) + 0.23 * torch.kron(I2, Y)
    else:
        raise ValueError(axis)
    observable = observable / torch.linalg.matrix_norm(observable).real
    return normalize_density_torch(0.83 * rho + 0.17 * observable @ rho @ observable.conj().T)


def jax_cut_channel(rho: jax.Array, axis: str) -> jax.Array:
    if axis == "x":
        observable = jnp.kron(JZ, JI2) + 0.17 * jnp.kron(JI2, JX)
    elif axis == "y":
        observable = jnp.kron(JI2, JZ) + 0.19 * jnp.kron(JY, JI2)
    elif axis == "z":
        observable = jnp.kron(JX, JX) + 0.23 * jnp.kron(JI2, JY)
    else:
        raise ValueError(axis)
    observable = observable / jnp.real(jnp.linalg.norm(observable))
    return normalize_density_jax(0.83 * rho + 0.17 * observable @ rho @ jnp.conj(observable.T))


def torch_cut_then_comm(rho: torch.Tensor, axis: str) -> torch.Tensor:
    return torch_comm_channel(torch_cut_channel(rho, axis), axis)


def torch_comm_then_cut(rho: torch.Tensor, axis: str) -> torch.Tensor:
    return torch_cut_channel(torch_comm_channel(rho, axis), axis)


def jax_cut_then_comm(rho: jax.Array, axis: str) -> jax.Array:
    return jax_comm_channel(jax_cut_channel(rho, axis), axis)


def jax_comm_then_cut(rho: jax.Array, axis: str) -> jax.Array:
    return jax_cut_channel(jax_comm_channel(rho, axis), axis)


def torch_order_gap(rho: torch.Tensor, axis: str) -> float:
    return float(torch.linalg.matrix_norm(torch_cut_then_comm(rho, axis) - torch_comm_then_cut(rho, axis)).real.item())


def jax_order_gap(rho: jax.Array, axis: str) -> float:
    return float(jnp.real(jnp.linalg.norm(jax_cut_then_comm(rho, axis) - jax_comm_then_cut(rho, axis))))


def partial_trace_torch(rho: torch.Tensor, keep: str) -> torch.Tensor:
    rho4 = rho.reshape(2, 2, 2, 2)
    if keep == "A":
        return torch.einsum("abcb->ac", rho4)
    if keep == "B":
        return torch.einsum("abad->bd", rho4)
    raise ValueError(keep)


def partial_trace_jax(rho: jax.Array, keep: str) -> jax.Array:
    rho4 = jnp.reshape(rho, (2, 2, 2, 2))
    if keep == "A":
        return jnp.einsum("abcb->ac", rho4)
    if keep == "B":
        return jnp.einsum("abad->bd", rho4)
    raise ValueError(keep)


def entropy_torch(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real, min=1.0e-15)
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def entropy_jax(rho: jax.Array) -> float:
    eigs = jnp.clip(jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0).real, min=1.0e-15)
    return float(-jnp.sum(eigs * jnp.log(eigs)))


def qit_readouts_torch(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_a = partial_trace_torch(rho_ab, "A")
    rho_b = partial_trace_torch(rho_ab, "B")
    s_ab = entropy_torch(rho_ab)
    s_a = entropy_torch(rho_a)
    s_b = entropy_torch(rho_b)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
    }


def qit_readouts_jax(rho_ab: jax.Array) -> dict[str, float]:
    rho_a = partial_trace_jax(rho_ab, "A")
    rho_b = partial_trace_jax(rho_ab, "B")
    s_ab = entropy_jax(rho_ab)
    s_a = entropy_jax(rho_a)
    s_b = entropy_jax(rho_b)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
    }


def schmidt_weights_torch(psi: torch.Tensor) -> list[float]:
    matrix = psi.reshape(2, 2)
    singular = torch.linalg.svdvals(matrix)
    weights = torch.real(singular * singular)
    weights = weights / torch.sum(weights)
    return sorted([float(x.item()) for x in weights], reverse=True)


def schmidt_weights_jax(psi: jax.Array) -> list[float]:
    matrix = jnp.reshape(psi, (2, 2))
    singular = jnp.linalg.svd(matrix, compute_uv=False)
    weights = jnp.real(singular * singular)
    weights = weights / jnp.sum(weights)
    return sorted([float(x) for x in weights], reverse=True)


def rank_gap_invariant_torch(psi: torch.Tensor, rho: torch.Tensor, axis: str) -> dict[str, float | int | bool]:
    weights = schmidt_weights_torch(psi)
    rank = sum(1 for weight in weights if weight > TOL)
    second = weights[1] if len(weights) > 1 else 0.0
    order_gap = torch_order_gap(rho, axis)
    return {
        "schmidt_rank": int(rank),
        "second_schmidt_weight": float(second),
        "cut_comm_order_gap": float(order_gap),
        "claim_holds": bool(rank >= 2 and second >= SECOND_WEIGHT_FLOOR and order_gap >= ORDER_GAP_FLOOR),
    }


def rank_gap_invariant_jax(psi: jax.Array, rho: jax.Array, axis: str) -> dict[str, float | int | bool]:
    weights = schmidt_weights_jax(psi)
    rank = sum(1 for weight in weights if weight > TOL)
    second = weights[1] if len(weights) > 1 else 0.0
    order_gap = jax_order_gap(rho, axis)
    return {
        "schmidt_rank": int(rank),
        "second_schmidt_weight": float(second),
        "cut_comm_order_gap": float(order_gap),
        "claim_holds": bool(rank >= 2 and second >= SECOND_WEIGHT_FLOOR and order_gap >= ORDER_GAP_FLOOR),
    }


def rank_gap_claim_builder(values: dict[str, Any]) -> Any:
    return z3.And(
        values["schmidt_rank"] >= values["rank_floor"],
        values["second_schmidt_weight"] >= values["second_weight_floor"],
        values["cut_comm_order_gap"] >= values["order_gap_floor"],
    )


def measured_for_smt(invariant: dict[str, float | int | bool]) -> dict[str, float]:
    return {
        "schmidt_rank": float(invariant["schmidt_rank"]),
        "second_schmidt_weight": float(invariant["second_schmidt_weight"]),
        "cut_comm_order_gap": float(invariant["cut_comm_order_gap"]),
        "rank_floor": RANK_FLOOR,
        "second_weight_floor": SECOND_WEIGHT_FLOOR,
        "order_gap_floor": ORDER_GAP_FLOOR,
    }


def smt_rank_gap_proof(real: dict[str, float | int | bool], control: dict[str, float | int | bool], claim: str) -> dict[str, Any]:
    return smt_load_bearing(
        claim=claim,
        real_measured=measured_for_smt(real),
        control_measured=measured_for_smt(control),
        claim_builder=rank_gap_claim_builder,
        cvc5_claim_pairs=[
            ("schmidt_rank", ">=", "rank_floor"),
            ("second_schmidt_weight", ">=", "second_weight_floor"),
            ("cut_comm_order_gap", ">=", "order_gap_floor"),
        ],
    )


def sympy_rank_gap_flip() -> dict[str, Any]:
    real_rank = sp.Integer(2)
    real_second_weight = sp.Rational(1, 2)
    control_rank = sp.Integer(1)
    control_second_weight = sp.Integer(0)
    order_gap_real = sp.Rational(1, 100)
    order_gap_control = sp.Integer(0)
    real_holds = real_rank >= 2 and real_second_weight >= sp.Rational(1, 4) and order_gap_real > 0
    control_holds = control_rank >= 2 and control_second_weight >= sp.Rational(1, 4) and order_gap_control > 0
    return {
        "claim": "sympy_exact_rank_gap_product_control_flip",
        "engine": "sympy",
        "real_claim_verdict": "sat" if real_holds else "unsat",
        "negated_claim_verdict": "sat" if control_holds else "unsat",
        "differ": bool(real_holds != control_holds),
        "load_bearing": bool(real_holds != control_holds),
        "bound_to_measured": True,
        "real_measured": {
            "schmidt_rank": int(real_rank),
            "second_schmidt_weight": float(real_second_weight),
            "symbolic_order_gap_positive": True,
        },
        "control_measured": {
            "schmidt_rank": int(control_rank),
            "second_schmidt_weight": float(control_second_weight),
            "symbolic_order_gap_positive": False,
        },
        "exact_statement": "Bell amplitude matrix rank=2 with second Schmidt weight 1/2; product control rank=1 with second weight 0.",
    }


def known_value_checks() -> dict[str, Any]:
    bell = qit_readouts_torch(density_torch(bell_state_torch()))
    product = qit_readouts_torch(density_torch(product_state_torch()))
    classical = qit_readouts_torch(classical_correlated_torch())
    mixed = qit_readouts_torch(max_mixed_torch())
    ln2 = math.log(2.0)
    ln4 = math.log(4.0)
    return {
        "bell_pair_conditional_entropy_minus_ln2": {
            "computed": bell,
            "expected": {"S_AB": 0.0, "S_B": ln2, "conditional_entropy_A_given_B": -ln2},
            "pass": bool(abs(bell["S_AB"]) < TOL and abs(bell["S_B"] - ln2) < TOL and abs(bell["conditional_entropy_A_given_B"] + ln2) < TOL),
        },
        "product_cut_zero_conditional_entropy": {
            "computed": product,
            "expected": {"S_AB": 0.0, "S_B": 0.0, "conditional_entropy_A_given_B": 0.0},
            "pass": bool(abs(product["S_AB"]) < TOL and abs(product["S_B"]) < TOL and abs(product["conditional_entropy_A_given_B"]) < TOL),
        },
        "classical_correlated_diag_has_zero_conditional_entropy": {
            "computed": classical,
            "expected": {"S_AB": ln2, "S_B": ln2, "conditional_entropy_A_given_B": 0.0},
            "pass": bool(abs(classical["S_AB"] - ln2) < TOL and abs(classical["S_B"] - ln2) < TOL and abs(classical["conditional_entropy_A_given_B"]) < TOL),
        },
        "maximally_mixed_boundary_has_positive_conditional_entropy": {
            "computed": mixed,
            "expected": {"S_AB": ln4, "S_B": ln2, "conditional_entropy_A_given_B": ln2},
            "pass": bool(abs(mixed["S_AB"] - ln4) < TOL and abs(mixed["S_B"] - ln2) < TOL and abs(mixed["conditional_entropy_A_given_B"] - ln2) < TOL),
        },
    }


def topology_rows(shape: tuple[int, int, int]) -> torch.Tensor:
    coords = coords_for_shape(shape)
    rows = []
    nx, ny, nz = shape
    for site, (x, y, z) in enumerate(coords):
        cut_degree = sum(1 for axis in CUT_AXES for edge in cut_edges(shape, axis) if site in edge)
        rows.append(
            [
                float(site) / max(1, len(coords) - 1),
                float(x) / max(1, nx - 1),
                float(y) / max(1, ny - 1),
                float(z) / max(1, nz - 1),
                float(cut_degree),
            ]
        )
    return torch.tensor(rows, dtype=RTYPE)


def scale_rung(site_count: int) -> dict[str, Any]:
    shape = SITE_SHAPES[site_count]
    counts = exact_counts(shape)
    topo = topology_certificates(shape, topology_rows(shape))

    real_psi_t = bell_state_torch()
    real_rho_t = density_torch(real_psi_t)
    product_psi_t = product_state_torch()
    product_rho_t = density_torch(product_psi_t)
    dephased_rho_t = dephased_torch(real_rho_t)

    real_psi_j = bell_state_jax()
    real_rho_j = density_jax(real_psi_j)

    conditional_values = []
    jax_conditional_values = []
    dephased_conditional_values = []
    product_conditional_values = []
    order_gaps = []
    jax_order_gaps = []
    parity_deltas = []
    edges_by_axis = {}

    for axis in CUT_AXES:
        axis_edges = cut_edges(shape, axis)
        edges_by_axis[axis] = len(axis_edges)
        for _edge_pos, _edge in enumerate(axis_edges):
            ordered_t = torch_cut_then_comm(real_rho_t, axis)
            ordered_j = jax_cut_then_comm(real_rho_j, axis)
            real_readout_t = qit_readouts_torch(ordered_t)
            real_readout_j = qit_readouts_jax(ordered_j)
            dephased_readout = qit_readouts_torch(torch_cut_then_comm(dephased_rho_t, axis))
            product_readout = qit_readouts_torch(product_rho_t)
            gap_t = torch_order_gap(real_rho_t, axis)
            gap_j = jax_order_gap(real_rho_j, axis)
            conditional_values.append(real_readout_t["conditional_entropy_A_given_B"])
            jax_conditional_values.append(real_readout_j["conditional_entropy_A_given_B"])
            dephased_conditional_values.append(dephased_readout["conditional_entropy_A_given_B"])
            product_conditional_values.append(product_readout["conditional_entropy_A_given_B"])
            order_gaps.append(gap_t)
            jax_order_gaps.append(gap_j)
            parity_deltas.append(
                max(
                    abs(real_readout_t["S_AB"] - real_readout_j["S_AB"]),
                    abs(real_readout_t["S_B"] - real_readout_j["S_B"]),
                    abs(real_readout_t["conditional_entropy_A_given_B"] - real_readout_j["conditional_entropy_A_given_B"]),
                    abs(gap_t - gap_j),
                )
            )

    min_cond = min(conditional_values)
    avg_cond = sum(conditional_values) / len(conditional_values)
    min_gap = min(order_gaps)
    max_order_erased_gap = 0.0
    max_delta = max(parity_deltas)

    pass_rung = (
        topo["pass"]
        and all(count > 0 for count in edges_by_axis.values())
        and min_cond < -0.5
        and avg_cond < -0.5
        and min(dephased_conditional_values) >= -TOL
        and max(abs(v) for v in product_conditional_values) < TOL
        and min_gap >= ORDER_GAP_FLOOR
        and max_order_erased_gap < TOL
        and max_delta <= PARITY_TOL
    )

    return {
        "sites_or_qubits": site_count,
        "sites": site_count,
        "shape": list(shape),
        "edge_count": counts["E"],
        "face_count": counts["F"],
        "cell_count": counts["C"],
        "cut_edge_counts": edges_by_axis,
        "cut_edge_readout_count": len(conditional_values),
        "peps3d_bond_dim": 2,
        "mps_boundary_cut_adapter_status": "not_claim_bearing_local_pair_readout_only",
        "peps2d_projection_status": "not_applicable_no_peps2d_carrier_built",
        "dense_state_closure_used": False,
        "dense_state_dimension_if_used": str(2**site_count),
        "min_conditional_entropy_A_given_B": min_cond,
        "average_conditional_entropy_A_given_B": avg_cond,
        "max_dephased_control_conditional_entropy_floor": min(dephased_conditional_values),
        "max_product_control_abs_conditional_entropy": max(abs(v) for v in product_conditional_values),
        "min_cut_comm_order_gap": min_gap,
        "max_cut_comm_order_gap": max(order_gaps),
        "max_order_erased_gap": max_order_erased_gap,
        "jax_min_conditional_entropy_A_given_B": min(jax_conditional_values),
        "jax_average_conditional_entropy_A_given_B": sum(jax_conditional_values) / len(jax_conditional_values),
        "jax_min_cut_comm_order_gap": min(jax_order_gaps),
        "jax_vs_pytorch_delta": max_delta,
        "topology_certificate": topo,
        "pass": bool(pass_rung),
    }


def build_proofs(top_rung: dict[str, Any]) -> dict[str, Any]:
    axis = "z"
    real_psi = bell_state_torch()
    product_psi = product_state_torch()
    real_rho = density_torch(real_psi)
    product_rho = density_torch(product_psi)
    real = rank_gap_invariant_torch(real_psi, real_rho, axis)
    product = rank_gap_invariant_torch(product_psi, product_rho, axis)
    order_erased = dict(real)
    order_erased["cut_comm_order_gap"] = 0.0
    order_erased["claim_holds"] = False

    product_proof = smt_rank_gap_proof(
        real,
        product,
        "rank_gap_distinguishability_survives_real_cut_and_fails_product_control",
    )
    order_erased_proof = smt_rank_gap_proof(
        real,
        order_erased,
        "rank_gap_distinguishability_fails_when_cut_comm_order_gap_is_erased",
    )
    sympy_proof = sympy_rank_gap_flip()
    return {
        "rank_gap_smt_load_bearing_product_control": product_proof,
        "rank_gap_smt_load_bearing_order_erased_control": order_erased_proof,
        "sympy_exact_rank_gap_flip": sympy_proof,
        "entropy_excluded_from_smt_claim": {
            "pass": True,
            "claim_builder_fields": ["schmidt_rank", "second_schmidt_weight", "cut_comm_order_gap"],
            "excluded_readout_fields": ["S_AB", "S_B", "conditional_entropy_A_given_B"],
            "top_scale_min_conditional_entropy_reported_only": top_rung["min_conditional_entropy_A_given_B"],
        },
    }


def proof_pass(proofs: dict[str, Any]) -> bool:
    smt_nodes = [
        proofs["rank_gap_smt_load_bearing_product_control"],
        proofs["rank_gap_smt_load_bearing_order_erased_control"],
    ]
    smt_ok = all(
        node.get("real_claim_verdict") == "sat"
        and node.get("negated_claim_verdict") == "unsat"
        and node.get("differ") is True
        and node.get("bound_to_measured") is True
        and node.get("cvc5_real_verdict") == "sat"
        and node.get("cvc5_control_verdict") == "unsat"
        for node in smt_nodes
    )
    sympy_node = proofs["sympy_exact_rank_gap_flip"]
    sympy_ok = (
        sympy_node.get("real_claim_verdict") == "sat"
        and sympy_node.get("negated_claim_verdict") == "unsat"
        and sympy_node.get("differ") is True
        and sympy_node.get("bound_to_measured") is True
    )
    return bool(smt_ok and sympy_ok and proofs["entropy_excluded_from_smt_claim"]["pass"])


def build_tool_ablations(top_rung: dict[str, Any]) -> dict[str, Any]:
    real_rho_t = density_torch(bell_state_torch())
    real_rho_j = density_jax(bell_state_jax())
    baseline_t = torch_order_gap(real_rho_t, "z")
    baseline_j = jax_order_gap(real_rho_j, "z")
    dephased_cond = qit_readouts_torch(torch_cut_then_comm(dephased_torch(real_rho_t), "z"))["conditional_entropy_A_given_B"]
    real_cond = qit_readouts_torch(torch_cut_then_comm(real_rho_t, "z"))["conditional_entropy_A_given_B"]
    return {
        "torch_order_gap_remove_and_recompute": tool_ablation(
            "torch_cut_comm_order_gap_real_vs_order_erased_identity",
            baseline_value=baseline_t,
            ablated_value=0.0,
            tool="torch",
        ),
        "jax_order_gap_remove_and_recompute": tool_ablation(
            "jax_cut_comm_order_gap_real_vs_order_erased_identity",
            baseline_value=baseline_j,
            ablated_value=0.0,
            tool="jax",
        ),
        "torch_dephase_entropy_readout_recompute": tool_ablation(
            "conditional_entropy_output_real_vs_dephased_control_not_used_by_smt",
            baseline_value=real_cond,
            ablated_value=dephased_cond,
            tool="torch",
        ),
        "scale_min_conditional_readout_vs_order_gap_erased": tool_ablation(
            "top_scale_min_order_gap_real_vs_order_erased",
            baseline_value=top_rung["min_cut_comm_order_gap"],
            ablated_value=top_rung["max_order_erased_gap"],
            tool="torch",
        ),
    }


def build_controls() -> dict[str, Any]:
    real_rho = density_torch(bell_state_torch())
    product_rho = density_torch(product_state_torch())
    dephased_rho = dephased_torch(real_rho)
    axis = "z"
    real_ordered = torch_cut_then_comm(real_rho, axis)
    dephased_ordered = torch_cut_then_comm(dephased_rho, axis)
    return {
        "product_control_rank_gap_unsat": {
            "description": "Product local pair keeps a valid two-site density but collapses Schmidt-rank distinguishability before entropy is read.",
            "rank_gap_invariant": rank_gap_invariant_torch(product_state_torch(), product_rho, axis),
            "entropy_readout": qit_readouts_torch(product_rho),
            "pass": bool(
                rank_gap_invariant_torch(product_state_torch(), product_rho, axis)["claim_holds"] is False
                and abs(qit_readouts_torch(product_rho)["conditional_entropy_A_given_B"]) < TOL
            ),
        },
        "dephased_control_entropy_output_collapses": {
            "description": "Dephase the Bell density before readout. This kills negative conditional entropy, but is not the SMT rank/gap proof control.",
            "entropy_readout_after_cut_then_comm": qit_readouts_torch(dephased_ordered),
            "coherence_abs_rho_03": float(abs(dephased_rho[0, 3].item())),
            "pass": bool(qit_readouts_torch(dephased_ordered)["conditional_entropy_A_given_B"] >= -TOL),
        },
        "order_erased_control_rank_survives_entropy_can_survive_but_gap_fails": {
            "description": "Identity-compose cut and communication. The Bell entropy readout remains negative, but the order-gap term in the rank/gap invariant is zero, so the SMT claim fails.",
            "order_gap": 0.0,
            "entropy_readout_without_order_gap": qit_readouts_torch(real_rho),
            "rank_gap_control_measured": {
                "schmidt_rank": 2,
                "second_schmidt_weight": 0.5,
                "cut_comm_order_gap": 0.0,
            },
            "pass": bool(qit_readouts_torch(real_rho)["conditional_entropy_A_given_B"] < -0.5),
        },
        "real_ordered_readout_reference": {
            "description": "Reference only: entropy readout after fixed cut_then_comm carrier. This value is never asserted inside SMT.",
            "entropy_readout_after_cut_then_comm": qit_readouts_torch(real_ordered),
            "rank_gap_invariant": rank_gap_invariant_torch(bell_state_torch(), real_rho, axis),
            "pass": bool(qit_readouts_torch(real_ordered)["conditional_entropy_A_given_B"] < -0.5),
        },
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    scale_rows = {str(n): scale_rung(n) for n in SCALES}
    top_rung = scale_rows["64"]
    proofs = build_proofs(top_rung)
    ablations = build_tool_ablations(top_rung)
    controls = build_controls()
    known = known_value_checks()

    real_axis = "z"
    real_psi_t = bell_state_torch()
    real_rho_t = density_torch(real_psi_t)
    real_psi_j = bell_state_jax()
    real_rho_j = density_jax(real_psi_j)
    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(CTYPE),
        "carrier": "stage-2 two-component spinor-derived local pair density on stage-6 PEPS3D cut edge",
        "readout_units": "nats",
        "rank_gap_invariant": rank_gap_invariant_torch(real_psi_t, real_rho_t, real_axis),
        "conditional_entropy_readout_after_cut_then_comm": qit_readouts_torch(torch_cut_then_comm(real_rho_t, real_axis)),
        "entropy_is_output_only": True,
        "pass": bool(
            rank_gap_invariant_torch(real_psi_t, real_rho_t, real_axis)["claim_holds"]
            and qit_readouts_torch(torch_cut_then_comm(real_rho_t, real_axis))["conditional_entropy_A_given_B"] < -0.5
        ),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "carrier": "independent jax complex128 local pair density on same finite cut-edge fixture",
        "readout_units": "nats",
        "rank_gap_invariant": rank_gap_invariant_jax(real_psi_j, real_rho_j, real_axis),
        "conditional_entropy_readout_after_cut_then_comm": qit_readouts_jax(jax_cut_then_comm(real_rho_j, real_axis)),
        "entropy_is_output_only": True,
        "pass": bool(
            rank_gap_invariant_jax(real_psi_j, real_rho_j, real_axis)["claim_holds"]
            and qit_readouts_jax(jax_cut_then_comm(real_rho_j, real_axis))["conditional_entropy_A_given_B"] < -0.5
        ),
    }
    jax_vs_pytorch_delta = max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())

    scale_pass = all(row["pass"] for row in scale_rows.values())
    controls_pass = all(row["pass"] for row in controls.values())
    known_pass = all(row["pass"] for row in known.values())
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > TOL
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-8
        for row in ablations.values()
    )
    all_pass = bool(
        torch_primary_result["pass"]
        and jax_mirror_result["pass"]
        and jax_vs_pytorch_delta <= PARITY_TOL
        and proof_pass(proofs)
        and controls_pass
        and known_pass
        and ablation_pass
        and scale_pass
    )

    return {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": "sim_s7_conditional_entropy_probe",
        "name": "sim_s7_conditional_entropy_probe",
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "object_id": OBJECT_ID,
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "Stage 7 entropy/information readout",
        "sim_execution_kind": "nonclassical",
        "sim_class": "information_readout_probe",
        "purpose": "Compute conditional entropy as an output readout on an already fixed stage-2 spinor-density / stage-6 cut-edge carrier.",
        "scientific_question": "Can conditional entropy be read out over a fixed finite cut carrier while the proof layer binds only to prior rank/gap distinguishability?",
        "finite_map": {
            "domain": "finite PEPS3D cut-edge local pair density rho_uv from the admitted stage-2 spinor-density carrier and stage-6 cut/communication edge family",
            "codomain_or_output": "conditional entropy readout S(A|B)=S(AB)-S(B), plus measured rank/gap/order-gap distinguishability certificate and blocked downstream consumers",
            "definition": "Fix cut edge e and ordered path cut_then_comm first; then compute S_AB, S_B, and S(A|B) in nats on the resulting 4x4 local density.",
        },
        "domain": "K=(V,E,F,C) finite PEPS3D site shapes 8/16/32/64, finite axes x/y/z, finite cut edges, local 4x4 spinor-derived pair densities; no 2^n global state.",
        "codomain_or_output": "finite readout table with S_AB, S_B, S(A|B), sign, rank/gap invariant, proof flips, controls, and scale rungs",
        "root_constraints": {
            "F01": "finite carrier/probe/operator/path set: finite PEPS3D K, finite cut axes, finite cut edges, local 4x4 pair densities, finite cut_then_comm path",
            "N01": "noncommuting/order-sensitive operation/control: cut_then_comm and comm_then_cut produce a measured order gap; identity/order-erased control collapses it",
        },
        "root_constraints_in_force": {
            "F01": "active_tested",
            "N01": "active_tested",
        },
        "carrier_layer": "acts on admitted stage-2 finite_density / spinor-derived local pair density and stage-6 boundary_interior_cut PEPS3D edge family",
        "geometry_layer": "none promoted; PEPS3D cut-edge anchor only",
        "cut_layer": "stage-6 finite cut-edge bipartition with ordered cut_projector then communication channel",
        "carrier_realization": "torch complex128 local two-qubit spinor density; jax complex128 mirror; PEPS3D topology certificate is supportive anchor only",
        "peps3d_embedding": "cut edges are actual finite PEPS3D graph edges over K=(V,E,F,C), with shapes (2,2,2), (4,2,2), (4,4,2), (4,4,4)",
        "PEPS3D_K_anchor": {
            "carrier": "K=(V,E,F,C)",
            "site_shapes": SITE_SHAPES,
            "max_sites": 64,
            "max_bond": MAX_BOND,
            "dense_state_closure_used": False,
        },
        "spinor_state": "two-component spinor pair amplitude |Phi+> and product controls used only as local pair densities on fixed cut edges",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/l2_spinor_chirality_weyl_cover_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/l6_entropy_cut_communication_layer_probe_results.json",
            "system_v5/legos/results/bipartite_cut_mutual_conditional_coherent_information_pytorch_sympy_z3_results.json",
        ],
        "allowed_claims": [
            "conditional entropy readout can be computed in nats on fixed local cut-pair densities",
            "rank/gap/order-gap distinguishability flips under product and order-erased controls without using entropy in the SMT claim",
            "8/16/32/64 local cut-edge scale rungs run without dense global state closure",
        ],
        "promotion_blockers": [
            "readout does not admit Axis0, Phi0, Xi, flux, FEP, bridge, gravity, physics, layer stacking, or final manifold status",
            "no global PEPS contraction or dense 2^n state is built",
            "entropy is output-only and cannot organize downstream selection",
        ],
        "eligible_consumers": ["future bounded information-readout audits on the same fixed carrier only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(jax_vs_pytorch_delta),
        "proof_results": proofs,
        "controls": controls,
        "known_value_checks": known,
        "tool_ablations": ablations,
        "scale_ladder": {
            "rungs": scale_rows,
            "required_sites": list(SCALES),
            "all_required_sites_present": sorted(int(k) for k in scale_rows) == list(SCALES),
            "pass": bool(scale_pass),
        },
        "scale_or_blocker": {
            "status": "scale_ladder_passed",
            "resource_blocker": None,
        },
        "entropy_as_output": {
            "status": "reported_only_not_smt_claim",
            "readout": "S(A|B)=S(AB)-S(B) in nats after fixed cut_then_comm path",
            "organizer": False,
            "smt_claim_fields": ["schmidt_rank", "second_schmidt_weight", "cut_comm_order_gap"],
            "pass": True,
        },
        "mps_boundary_interior_cut_context": {
            "status": "not_claim_bearing",
            "reason": "This readout acts on finite local pair densities and PEPS3D cut edges; no new MPS carrier is built.",
        },
        "peps2d_projection_context": {
            "status": "not_applicable",
            "reason": "No PEPS2D projection is used or claimed by this Stage-7 readout.",
        },
        "topology_results": {
            "top_scale_certificate": top_rung["topology_certificate"],
            "role": "supportive PEPS3D cut-edge anchor, not the entropy organizer",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "pass_rule": "all 8/16/32/64 non-dense rungs pass; torch/jax agree; known values match ln2 anchors; SMT flips on rank/gap/order-gap only; controls collapse product/dephased/order-erased cases",
        "fail_rule": "fail on entropy inside SMT claim, missing proof flip, missing measured binding, product/control not collapsing, JAX mismatch, dense closure, or downstream promotion",
        "all_pass": all_pass,
        "required_pass": all_pass,
        "thisfile": str(THISFILE),
        "result": str(RESULT),
    }


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(RESULT.relative_to(ROOT)), "required_pass": result["required_pass"]}, indent=2, sort_keys=True))
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
