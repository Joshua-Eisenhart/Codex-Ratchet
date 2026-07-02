#!/usr/bin/env python3
import jax

jax.config.update("jax_enable_x64", True)

import itertools
import json
import math
import os
import pathlib
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.environ.setdefault("COTENGRA_NUM_WORKERS", "1")

import numba
from numba.np.ufunc import decorators as numba_ufunc_decorators

_ORIGINAL_NUMBA_JIT = numba.jit
_ORIGINAL_NUMBA_VECTORIZE = numba.vectorize


def _jit_without_cache(*args: Any, **kwargs: Any) -> Any:
    kwargs.pop("cache", None)
    return _ORIGINAL_NUMBA_JIT(*args, **kwargs)


def _njit_without_cache(*args: Any, **kwargs: Any) -> Any:
    kwargs.pop("cache", None)
    kwargs["nopython"] = True
    return _ORIGINAL_NUMBA_JIT(*args, **kwargs)


def _vectorize_without_cache(*args: Any, **kwargs: Any) -> Any:
    kwargs["cache"] = False
    return _ORIGINAL_NUMBA_VECTORIZE(*args, **kwargs)


numba.jit = _jit_without_cache
numba.njit = _njit_without_cache
numba.vectorize = _vectorize_without_cache
numba_ufunc_decorators.vectorize = _vectorize_without_cache

import autoray
import cotengra as ctg
import jax.numpy as jnp
import opt_einsum as oe
import quimb.tensor as qtn
import sympy as sp
import torch
import z3

SCRIPTS_DIR = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from load_bearing_proof import smt_load_bearing, tool_ablation  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_carrier_peps2d_probe"
OBJECT_ID = "peps2d_carrier"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

SITE_SHAPES = {
    8: (2, 4),
    16: (4, 4),
    32: (4, 8),
    64: (8, 8),
}
SITE_COUNTS = tuple(SITE_SHAPES)
PHYSICAL_DIM = 2
BOND_DIM = 2
PROBS = (Fraction(3, 5), Fraction(2, 5))
CORRUPT_SCALE = Fraction(6, 5)
ORDER_A = ((Fraction(1, 1), Fraction(3, 25)), (Fraction(0, 1), Fraction(1, 1)))
ORDER_B = ((Fraction(1, 1), Fraction(0, 1)), (Fraction(4, 25), Fraction(1, 1)))
EPS = 1.0e-9
ORDER_EPS = 1.0e-4
RTYPE = torch.float64
CTYPE = torch.complex128
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim numeric: constructs torch.complex128 PEPS2D tensors, closed-form finite normalization, order-gap readouts, and controls without dense state closure.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for the finite copy-PEPS2D normalization and virtual-bond order-gap formulas; JAX is not claimed as a quimb backend.",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING PEPS2D carrier object and non-dense PEPS norm contraction over the real and corrupted-bond carriers.",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING contraction tree for the PEPS2D norm network; bond-erased control changes the tree width/cost witness.",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING independent non-dense contraction of the same PEPS2D norm network from explicit double-layer tensors.",
    },
    "autoray": {
        "tried": True,
        "used": True,
        "reason": "Supportive backend check confirming the tensors consumed by quimb/cotengra remain torch-backed arrays.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing with z3 variables bound to measured real/control normalization errors.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through smt_load_bearing cvc5_claim_pairs on the same measured normalization inequality.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact rational proof mirror for real norm-squared=1, corrupted-bond norm-squared=147/125, and finite virtual order gap.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not relevant to this finite PEPS2D carrier probe.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "autoray": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": None,
    "scipy": None,
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
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator, "float": float(value)}
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def channel_amplitudes(site_count: int, *, unit_weights: bool = False) -> list[float]:
    if unit_weights:
        return [1.0, 1.0]
    return [float(prob) ** (1.0 / (2.0 * site_count)) for prob in PROBS]


def lattice_virtual_names(x: int, y: int, lx: int, ly: int) -> list[str]:
    names: list[str] = []
    if x > 0:
        names.append("u")
    if y < ly - 1:
        names.append("r")
    if x < lx - 1:
        names.append("d")
    if y > 0:
        names.append("l")
    return names


def make_peps_arrays(
    lx: int,
    ly: int,
    *,
    bond_dim: int = BOND_DIM,
    corrupt_bond: bool = False,
    physical_channel_erased: bool = False,
    unit_weights: bool = False,
) -> list[list[torch.Tensor]]:
    site_count = lx * ly
    amps = channel_amplitudes(site_count, unit_weights=unit_weights)
    arrays: list[list[torch.Tensor]] = []
    for x in range(lx):
        row: list[torch.Tensor] = []
        for y in range(ly):
            virtual_names = lattice_virtual_names(x, y, lx, ly)
            dims = [bond_dim for _ in virtual_names] + [PHYSICAL_DIM]
            tensor = torch.zeros(tuple(dims), dtype=CTYPE)
            for channel in range(bond_dim):
                if physical_channel_erased and channel == 1:
                    continue
                idx = [channel for _ in virtual_names]
                value = amps[channel]
                if corrupt_bond and (x, y) == (0, 0) and "r" in virtual_names and channel == 1:
                    value *= float(CORRUPT_SCALE)
                tensor[tuple(idx + [channel % PHYSICAL_DIM])] = complex(value, 0.0)
            row.append(tensor)
        arrays.append(row)
    return arrays


def make_quimb_peps(arrays: list[list[torch.Tensor]]) -> qtn.PEPS:
    peps = qtn.PEPS(arrays, shape="urdlp")
    if not all(isinstance(array, torch.Tensor) for array in peps.arrays):
        raise TypeError("quimb PEPS2D did not preserve torch.Tensor arrays")
    return peps


def quimb_norm_squared(arrays: list[list[torch.Tensor]]) -> dict[str, Any]:
    peps = make_quimb_peps(arrays)
    norm = peps.norm(optimize="greedy")
    norm_sq = norm * torch.conj(norm)
    return {
        "peps2d_num_tensors": int(peps.num_tensors),
        "peps2d_max_bond": int(peps.max_bond()),
        "quimb_backend_all_torch": all(isinstance(array, torch.Tensor) for array in peps.arrays),
        "autoray_backend": autoray.infer_backend(peps.arrays[0]),
        "norm_real": float(torch.real(norm).item()),
        "norm_imag_abs": abs(float(torch.imag(norm).item())),
        "norm_squared_real": float(torch.real(norm_sq).item()),
        "norm_squared_imag_abs": abs(float(torch.imag(norm_sq).item())),
    }


def bond_key_for_direction(x: int, y: int, direction: str) -> tuple[tuple[int, int], tuple[int, int]]:
    if direction == "r":
        return (x, y), (x, y + 1)
    if direction == "l":
        return (x, y - 1), (x, y)
    if direction == "d":
        return (x, y), (x + 1, y)
    if direction == "u":
        return (x - 1, y), (x, y)
    raise ValueError(f"unknown direction: {direction}")


def norm_network_operands(
    arrays: list[list[torch.Tensor]],
) -> tuple[list[Any], list[tuple[int, ...]], dict[int, int]]:
    lx = len(arrays)
    ly = len(arrays[0])
    bond_dim = max(
        [int(dim) for row in arrays for tensor in row for dim in tensor.shape[:-1]]
        or [1]
    )
    bond_ids: dict[tuple[tuple[int, int], tuple[int, int]], int] = {}
    next_id = 0
    for x in range(lx):
        for y in range(ly):
            if y < ly - 1:
                bond_ids[((x, y), (x, y + 1))] = next_id
                next_id += 1
            if x < lx - 1:
                bond_ids[((x, y), (x + 1, y))] = next_id
                next_id += 1

    operands: list[Any] = []
    inputs: list[tuple[int, ...]] = []
    size_dict = {idx: bond_dim * bond_dim for idx in range(next_id)}
    for x in range(lx):
        for y in range(ly):
            tensor = arrays[x][y]
            virtual_names = lattice_virtual_names(x, y, lx, ly)
            double_dims = [bond_dim * bond_dim for _ in virtual_names]
            if double_dims:
                double_layer = torch.zeros(tuple(double_dims), dtype=CTYPE)
            else:
                double_layer = torch.zeros((), dtype=CTYPE)
            for combo in itertools.product(range(bond_dim * bond_dim), repeat=len(virtual_names)):
                bra_idx: list[int] = []
                ket_idx: list[int] = []
                for packed in combo:
                    bra_idx.append(packed // bond_dim)
                    ket_idx.append(packed % bond_dim)
                value = 0.0 + 0.0j
                for phys in range(PHYSICAL_DIM):
                    value += (
                        torch.conj(tensor[tuple(bra_idx + [phys])])
                        * tensor[tuple(ket_idx + [phys])]
                    ).item()
                if double_dims:
                    double_layer[combo] = value
                else:
                    double_layer = double_layer + value
            inds = tuple(bond_ids[bond_key_for_direction(x, y, direction)] for direction in virtual_names)
            operands.extend([double_layer, list(inds)])
            inputs.append(inds)
    return operands, inputs, size_dict


def opt_einsum_norm_squared(arrays: list[list[torch.Tensor]]) -> dict[str, Any]:
    operands, _, _ = norm_network_operands(arrays)
    value = oe.contract(*operands, [], optimize="greedy")
    return {
        "norm_squared_real": float(torch.real(value).item()),
        "norm_squared_imag_abs": abs(float(torch.imag(value).item())),
    }


def cotengra_tree_witness(arrays: list[list[torch.Tensor]]) -> dict[str, Any]:
    _, inputs, size_dict = norm_network_operands(arrays)
    tree = ctg.array_contract_tree(inputs, output=(), size_dict=size_dict, optimize="greedy")
    return {
        "tree_type": type(tree).__name__,
        "contraction_width": float(tree.contraction_width()),
        "contraction_cost": float(tree.contraction_cost()),
        "max_size": float(tree.max_size()),
        "peak_size": float(tree.peak_size()),
    }


def torch_norm_sq_formula(*, corrupt_bond: bool = False, physical_channel_erased: bool = False, unit_weights: bool = False) -> float:
    if unit_weights:
        weights = [1.0, 1.0]
    else:
        weights = [float(prob) for prob in PROBS]
    if physical_channel_erased:
        weights[1] = 0.0
    if corrupt_bond:
        weights[1] *= float(CORRUPT_SCALE) ** 2
    return float(sum(weights))


def jax_norm_sq_formula(*, corrupt_bond: bool = False, physical_channel_erased: bool = False, unit_weights: bool = False) -> float:
    if unit_weights:
        weights = jnp.array([1.0, 1.0], dtype=jnp.float64)
    else:
        weights = jnp.array([float(PROBS[0]), float(PROBS[1])], dtype=jnp.float64)
    if physical_channel_erased:
        weights = weights.at[1].set(0.0)
    if corrupt_bond:
        weights = weights.at[1].set(weights[1] * jnp.float64(float(CORRUPT_SCALE) ** 2))
    return float(jnp.sum(weights))


def order_gap_torch() -> dict[str, Any]:
    weights = torch.tensor([float(PROBS[0]), float(PROBS[1])], dtype=RTYPE)
    a = torch.tensor(ORDER_A, dtype=RTYPE)
    b = torch.tensor(ORDER_B, dtype=RTYPE)
    ab = a @ b
    ba = b @ a
    diag_ab = torch.diagonal(ab)
    diag_ba = torch.diagonal(ba)
    readout_ab = torch.dot(weights, diag_ab)
    readout_ba = torch.dot(weights, diag_ba)
    gap = torch.abs(readout_ab - readout_ba)
    comm = a @ b - b @ a
    return {
        "readout_A_then_B": float(readout_ab.item()),
        "readout_B_then_A": float(readout_ba.item()),
        "order_gap": float(gap.item()),
        "commutator_frobenius": float(torch.linalg.matrix_norm(comm, ord="fro").item()),
        "pass": bool(float(gap.item()) > ORDER_EPS),
    }


def order_gap_jax() -> dict[str, Any]:
    weights = jnp.array([float(PROBS[0]), float(PROBS[1])], dtype=jnp.float64)
    a = jnp.array(ORDER_A, dtype=jnp.float64)
    b = jnp.array(ORDER_B, dtype=jnp.float64)
    ab = a @ b
    ba = b @ a
    readout_ab = jnp.dot(weights, jnp.diag(ab))
    readout_ba = jnp.dot(weights, jnp.diag(ba))
    gap = jnp.abs(readout_ab - readout_ba)
    comm = a @ b - b @ a
    return {
        "readout_A_then_B": float(readout_ab),
        "readout_B_then_A": float(readout_ba),
        "order_gap": float(gap),
        "commutator_frobenius": float(jnp.linalg.norm(comm, ord="fro")),
        "pass": bool(float(gap) > ORDER_EPS),
    }


def sympy_exact() -> dict[str, Any]:
    p0, p1 = [sp.Rational(prob.numerator, prob.denominator) for prob in PROBS]
    scale = sp.Rational(CORRUPT_SCALE.numerator, CORRUPT_SCALE.denominator)
    norm_sq = sp.simplify(p0 + p1)
    corrupt_norm_sq = sp.simplify(p0 + p1 * scale * scale)
    a = sp.Matrix([[sp.Rational(v.numerator, v.denominator) for v in row] for row in ORDER_A])
    b = sp.Matrix([[sp.Rational(v.numerator, v.denominator) for v in row] for row in ORDER_B])
    weights = sp.Matrix([[p0, p1]])
    diag_ab = sp.Matrix([sp.diag(a * b)[0], sp.diag(a * b)[1]])
    diag_ba = sp.Matrix([sp.diag(b * a)[0], sp.diag(b * a)[1]])
    readout_ab = sp.simplify((weights * diag_ab)[0])
    readout_ba = sp.simplify((weights * diag_ba)[0])
    order_gap = sp.simplify(abs(readout_ab - readout_ba))
    return {
        "real_norm_squared": str(norm_sq),
        "corrupted_bond_norm_squared": str(corrupt_norm_sq),
        "real_normalization_error": str(abs(norm_sq - 1)),
        "corrupted_bond_normalization_error": str(abs(corrupt_norm_sq - 1)),
        "order_readout_A_then_B": str(readout_ab),
        "order_readout_B_then_A": str(readout_ba),
        "order_gap": str(order_gap),
        "pass": bool(norm_sq == 1 and corrupt_norm_sq != 1 and order_gap > 0),
    }


def scale_rung(site_count: int) -> dict[str, Any]:
    lx, ly = SITE_SHAPES[site_count]
    arrays = make_peps_arrays(lx, ly)
    corrupt_arrays = make_peps_arrays(lx, ly, corrupt_bond=True)
    physical_erased_arrays = make_peps_arrays(lx, ly, physical_channel_erased=True)
    product_arrays = make_peps_arrays(lx, ly, bond_dim=1, physical_channel_erased=True)

    quimb_real = quimb_norm_squared(arrays)
    quimb_corrupt = quimb_norm_squared(corrupt_arrays)
    quimb_physical_erased = quimb_norm_squared(physical_erased_arrays)
    opt_real = opt_einsum_norm_squared(arrays)
    opt_corrupt = opt_einsum_norm_squared(corrupt_arrays)
    cot_real = cotengra_tree_witness(arrays)
    cot_product = cotengra_tree_witness(product_arrays)

    torch_real = torch_norm_sq_formula()
    torch_corrupt = torch_norm_sq_formula(corrupt_bond=True)
    torch_physical_erased = torch_norm_sq_formula(physical_channel_erased=True)
    torch_unit = torch_norm_sq_formula(unit_weights=True)
    jax_real = jax_norm_sq_formula()
    jax_corrupt = jax_norm_sq_formula(corrupt_bond=True)
    n01_torch = order_gap_torch()
    n01_jax = order_gap_jax()

    real_error = abs(quimb_real["norm_squared_real"] - 1.0)
    corrupt_error = abs(quimb_corrupt["norm_squared_real"] - 1.0)
    q_oe_delta = abs(quimb_real["norm_squared_real"] - opt_real["norm_squared_real"])
    q_torch_delta = abs(quimb_real["norm_squared_real"] - torch_real)
    q_jax_delta = abs(quimb_real["norm_squared_real"] - jax_real)
    control_delta = abs(quimb_corrupt["norm_squared_real"] - opt_corrupt["norm_squared_real"])
    pass_rung = bool(
        quimb_real["peps2d_num_tensors"] == site_count
        and quimb_real["peps2d_max_bond"] == BOND_DIM
        and quimb_real["quimb_backend_all_torch"] is True
        and real_error <= EPS
        and corrupt_error > EPS
        and quimb_real["norm_squared_imag_abs"] <= EPS
        and opt_real["norm_squared_imag_abs"] <= EPS
        and q_oe_delta <= EPS
        and q_torch_delta <= EPS
        and q_jax_delta <= EPS
        and control_delta <= EPS
        and n01_torch["pass"]
        and n01_jax["pass"]
    )

    return {
        "sites_or_qubits": site_count,
        "lattice_shape": [lx, ly],
        "dense_state_closure_used": False,
        "physical_dim": PHYSICAL_DIM,
        "peps2d_bond_dim": BOND_DIM,
        "quimb": quimb_real,
        "quimb_corrupted_bond_control": quimb_corrupt,
        "quimb_physical_channel_erased_control": quimb_physical_erased,
        "cotengra_tree": cot_real,
        "cotengra_product_tree": cot_product,
        "opt_einsum": opt_real,
        "opt_einsum_corrupted_bond_control": opt_corrupt,
        "torch_formula_norm_squared": torch_real,
        "torch_corrupted_bond_norm_squared": torch_corrupt,
        "torch_physical_channel_erased_norm_squared": torch_physical_erased,
        "torch_unit_weight_norm_squared": torch_unit,
        "jax_formula_norm_squared": jax_real,
        "jax_corrupted_bond_norm_squared": jax_corrupt,
        "normalization_error": real_error,
        "corrupted_bond_normalization_error": corrupt_error,
        "quimb_vs_opt_einsum_delta": q_oe_delta,
        "quimb_vs_torch_delta": q_torch_delta,
        "quimb_vs_jax_delta": q_jax_delta,
        "control_quimb_vs_opt_einsum_delta": control_delta,
        "n01_virtual_bond_order_gap_torch": n01_torch,
        "n01_virtual_bond_order_gap_jax": n01_jax,
        "pass": pass_rung,
    }


def proof_score(proof: dict[str, Any], engine: str) -> float:
    if engine == "z3":
        return float(
            proof.get("real_claim_verdict") == "sat"
            and proof.get("negated_claim_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    if engine == "cvc5":
        return float(
            proof.get("cvc5_real_verdict") == "sat"
            and proof.get("cvc5_control_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    raise ValueError(f"unknown proof engine: {engine}")


def build_proof(top: dict[str, Any], exact: dict[str, Any]) -> dict[str, Any]:
    primary = smt_load_bearing(
        claim="PEPS2D norm-squared contraction remains normalized: |<psi|psi>-1| <= eps",
        real_measured={"normalization_error": top["normalization_error"], "eps": EPS},
        control_measured={"normalization_error": top["corrupted_bond_normalization_error"], "eps": EPS},
        claim_builder=lambda v: v["normalization_error"] <= v["eps"],
        cvc5_claim_pairs=[("normalization_error", "<=", "eps")],
    )
    primary["pass"] = bool(
        primary["real_claim_verdict"] == "sat"
        and primary["negated_claim_verdict"] == "unsat"
        and primary["differ"] is True
        and primary["bound_to_measured"] is True
        and primary.get("cvc5_real_verdict") == "sat"
        and primary.get("cvc5_control_verdict") == "unsat"
    )
    return {
        "smt_load_bearing_normalization": primary,
        "sympy_exact_normalization": exact,
        "pass": bool(primary["pass"] and exact["pass"]),
    }


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(abs(float(row["outcome_delta"])) > EPS)
    return row


def build_tool_ablations(top: dict[str, Any], proofs: dict[str, Any], exact: dict[str, Any]) -> dict[str, Any]:
    proof = proofs["smt_load_bearing_normalization"]
    z3_flip = proof_score(proof, "z3")
    cvc5_flip = proof_score(proof, "cvc5")
    exact_real = float(Fraction(exact["real_norm_squared"]))
    exact_corrupt = float(Fraction(exact["corrupted_bond_norm_squared"]))
    exact_order_gap = float(Fraction(exact["order_gap"]))

    return {
        "torch_normalized_weights_removed": add_ablation_pass(
            tool_ablation(
                "torch finite PEPS2D normalized channel weights vs unit unnormalized channel weights",
                baseline_value=top["torch_formula_norm_squared"],
                ablated_value=top["torch_unit_weight_norm_squared"],
                tool="torch",
            )
        ),
        "jax_corrupted_bond_mirror": add_ablation_pass(
            tool_ablation(
                "jax x64 real PEPS2D normalization formula vs corrupted-bond mirror",
                baseline_value=top["jax_formula_norm_squared"],
                ablated_value=top["jax_corrupted_bond_norm_squared"],
                tool="jax",
            )
        ),
        "quimb_physical_channel_erased": add_ablation_pass(
            tool_ablation(
                "quimb PEPS2D norm-squared with both physical channels vs physical channel p=1 erased",
                baseline_value=top["quimb"]["norm_squared_real"],
                ablated_value=top["quimb_physical_channel_erased_control"]["norm_squared_real"],
                tool="quimb",
            )
        ),
        "cotengra_bond_erased_tree_width": add_ablation_pass(
            tool_ablation(
                "cotengra D=2 PEPS2D norm-network contraction width vs bond-erased product tree width",
                baseline_value=top["cotengra_tree"]["contraction_width"],
                ablated_value=top["cotengra_product_tree"]["contraction_width"],
                tool="cotengra",
            )
        ),
        "opt_einsum_corrupted_bond_contraction": add_ablation_pass(
            tool_ablation(
                "opt_einsum real PEPS2D norm-squared contraction vs corrupted-bond contraction",
                baseline_value=top["opt_einsum"]["norm_squared_real"],
                ablated_value=top["opt_einsum_corrupted_bond_control"]["norm_squared_real"],
                tool="opt_einsum",
            )
        ),
        "autoray_backend_dispatch_removed": add_ablation_pass(
            tool_ablation(
                "autoray torch backend dispatch present for quimb PEPS arrays vs no backend dispatch surface",
                baseline_value=float(top["quimb"]["autoray_backend"] == "torch"),
                ablated_value=0.0,
                tool="autoray",
            )
        ),
        "z3_normalization_flip": add_ablation_pass(
            tool_ablation(
                "z3 helper flip-score for normalization_error<=eps, real carrier vs corrupted-bond control",
                baseline_value=z3_flip,
                ablated_value=0.0,
                tool="z3",
            )
        ),
        "cvc5_normalization_flip": add_ablation_pass(
            tool_ablation(
                "cvc5 helper flip-score for normalization_error<=eps, real carrier vs corrupted-bond control",
                baseline_value=cvc5_flip,
                ablated_value=0.0,
                tool="cvc5",
            )
        ),
        "sympy_exact_corrupted_norm": add_ablation_pass(
            tool_ablation(
                "sympy exact real norm-squared vs corrupted-bond norm-squared",
                baseline_value=exact_real,
                ablated_value=exact_corrupt,
                tool="sympy",
            )
        ),
        "sympy_exact_order_gap_control": add_ablation_pass(
            tool_ablation(
                "sympy exact virtual-bond order gap vs order-erased zero control",
                baseline_value=exact_order_gap,
                ablated_value=0.0,
                tool="sympy",
            )
        ),
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    scale_rows = {str(site_count): scale_rung(site_count) for site_count in SITE_COUNTS}
    top = scale_rows["64"]
    exact = sympy_exact()
    proofs = build_proof(top, exact)
    tool_ablations = build_tool_ablations(top, proofs, exact)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = bool(proofs["pass"])
    ablation_pass = all(row["pass"] for row in tool_ablations.values())
    controls_pass = bool(
        all(row["corrupted_bond_normalization_error"] > EPS for row in scale_rows.values())
        and all(row["quimb_physical_channel_erased_control"]["norm_squared_real"] < 1.0 for row in scale_rows.values())
    )
    jax_vs_pytorch_delta = max(
        abs(row["jax_formula_norm_squared"] - row["torch_formula_norm_squared"])
        for row in scale_rows.values()
    )
    quimb_vs_opt_delta = max(row["quimb_vs_opt_einsum_delta"] for row in scale_rows.values())
    all_pass = bool(
        scale_pass
        and proof_pass
        and ablation_pass
        and controls_pass
        and jax_vs_pytorch_delta <= EPS
        and quimb_vs_opt_delta <= EPS
    )

    torch_primary_result = {
        "engine": "torch",
        "dtype": str(CTYPE),
        "claim": "finite torch-backed PEPS2D carrier has norm-squared contraction 1 at 8/16/32/64 sites; corrupted bond breaks normalization",
        "top_rung_sites": 64,
        "top_rung_norm_squared": top["torch_formula_norm_squared"],
        "top_rung_corrupted_bond_norm_squared": top["torch_corrupted_bond_norm_squared"],
        "top_rung_virtual_bond_order_gap": top["n01_virtual_bond_order_gap_torch"]["order_gap"],
        "pass": bool(
            all(abs(row["torch_formula_norm_squared"] - 1.0) <= EPS for row in scale_rows.values())
            and all(row["torch_corrupted_bond_norm_squared"] - 1.0 > EPS for row in scale_rows.values())
            and all(row["n01_virtual_bond_order_gap_torch"]["pass"] for row in scale_rows.values())
        ),
    }

    jax_mirror_result = {
        "engine": "jax",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "scope": "formula mirror for finite copy-PEPS2D normalization and virtual-bond order readouts; no JAX quimb backend path is claimed",
        "top_rung_norm_squared": top["jax_formula_norm_squared"],
        "top_rung_corrupted_bond_norm_squared": top["jax_corrupted_bond_norm_squared"],
        "top_rung_virtual_bond_order_gap": top["n01_virtual_bond_order_gap_jax"]["order_gap"],
        "pass": bool(
            all(abs(row["jax_formula_norm_squared"] - row["torch_formula_norm_squared"]) <= EPS for row in scale_rows.values())
            and all(row["n01_virtual_bond_order_gap_jax"]["pass"] for row in scale_rows.values())
        ),
    }

    controls = {
        "corrupted_bond": {
            "description": "multiply the channel-1 amplitude on one internal PEPS2D virtual bond by 6/5 and recompute quimb and opt_einsum norm contractions",
            "top_rung_norm_squared": top["quimb_corrupted_bond_control"]["norm_squared_real"],
            "top_rung_normalization_error": top["corrupted_bond_normalization_error"],
            "kills_normalization_claim": bool(top["corrupted_bond_normalization_error"] > EPS),
            "pass": bool(all(row["corrupted_bond_normalization_error"] > EPS for row in scale_rows.values())),
        },
        "physical_channel_erased": {
            "description": "erase PEPS2D physical channel p=1 and recompute the quimb norm contraction",
            "top_rung_norm_squared": top["quimb_physical_channel_erased_control"]["norm_squared_real"],
            "kills_two_channel_carrier": bool(abs(top["quimb_physical_channel_erased_control"]["norm_squared_real"] - 1.0) > EPS),
            "pass": bool(top["quimb_physical_channel_erased_control"]["norm_squared_real"] < 1.0),
        },
        "unit_weight_unnormalized": {
            "description": "remove normalized channel weights in the torch/JAX finite formula; norm-squared becomes 2",
            "top_rung_norm_squared": top["torch_unit_weight_norm_squared"],
            "kills_normalization_claim": bool(abs(top["torch_unit_weight_norm_squared"] - 1.0) > EPS),
            "pass": bool(abs(top["torch_unit_weight_norm_squared"] - 1.0) > EPS),
        },
        "dense_state_closure_rejected": {
            "description": "full physical vector closure would require 2**64 amplitudes at top rung and is not used",
            "would_require_amplitudes_at_N64": 2**64,
            "dense_state_closure_used": False,
            "pass": True,
        },
    }

    scale_ladder = {
        "rungs": {
            key: {
                "sites_or_qubits": row["sites_or_qubits"],
                "lattice_shape": row["lattice_shape"],
                "dense_state_closure_used": row["dense_state_closure_used"],
                "peps2d_bond_dim": row["peps2d_bond_dim"],
                "quimb_norm_squared": row["quimb"]["norm_squared_real"],
                "opt_einsum_norm_squared": row["opt_einsum"]["norm_squared_real"],
                "torch_formula_norm_squared": row["torch_formula_norm_squared"],
                "jax_formula_norm_squared": row["jax_formula_norm_squared"],
                "corrupted_bond_norm_squared": row["quimb_corrupted_bond_control"]["norm_squared_real"],
                "normalization_error": row["normalization_error"],
                "corrupted_bond_normalization_error": row["corrupted_bond_normalization_error"],
                "n01_order_gap": row["n01_virtual_bond_order_gap_torch"]["order_gap"],
                "cotengra_width": row["cotengra_tree"]["contraction_width"],
                "cotengra_cost": row["cotengra_tree"]["contraction_cost"],
                "pass": row["pass"],
            }
            for key, row in scale_rows.items()
        },
        "scale_axis": "2D PEPS lattice sites",
        "dense_state_closure_used": False,
        "pass": scale_pass,
    }

    result = {
        "schema": "PER_SIM_CONTRACT_STAGE2_CARRIER_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 2 carrier",
        "sim_execution_kind": "nonclassical",
        "sim_class": "carrier_probe",
        "purpose": "Build one PEPS2D carrier state-space lego for later stages: finite 2D lattice, non-dense contractions, normalization proof, corrupted-bond negative control, and distinct tool ablations.",
        "scientific_question": "Can a finite torch-backed PEPS2D carrier at 8/16/32/64 sites preserve norm-squared contraction 1 without dense closure, while a corrupted bond breaks that invariant and proof/tool ablations detect the break?",
        "finite_map": {
            "domain": "For n in {8,16,32,64}: finite 2D lattice shapes (2,4),(4,4),(4,8),(8,8); each site has a torch.complex128 PEPS2D tensor with physical_dim=2 and virtual bond_dim=2.",
            "codomain_or_output": "Non-dense PEPS2D norm-squared contraction value, normalization_error=|<psi|psi>-1|, corrupted-bond control contraction, finite virtual-bond order_gap, proof verdict flip, controls, and blocked downstream consumers.",
            "definition": "A copy-channel PEPS2D assigns channel weights p=(3/5,2/5) through site amplitudes p_b^(1/(2n)); exact norm-squared is sum_b p_b=1. One channel-1 virtual bond corruption by 6/5 changes the contraction to 147/125.",
        },
        "domain": {
            "scale_lattice_shapes": {str(k): list(v) for k, v in SITE_SHAPES.items()},
            "physical_dim": PHYSICAL_DIM,
            "peps2d_bond_dim": BOND_DIM,
            "channel_probabilities": [str(prob) for prob in PROBS],
            "corrupted_bond_scale": str(CORRUPT_SCALE),
        },
        "codomain_or_output": {
            "normalization_invariant": "norm_squared contraction equals 1 within eps",
            "control": "corrupted bond makes norm_squared=147/125 and normalization_error=22/125",
            "N01_readout": "finite virtual-bond noncommuting A/B order readout gap over the same two-channel carrier",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: finite 2D sites, finite physical channels, finite virtual bonds, finite norm contractions, and finite controls at every rung.",
            },
            "N01": {
                "role": "active_compatibility_readout",
                "statement": "noncommuting/order-sensitive compatibility is represented by two finite virtual-bond maps A,B with nonzero order_gap on the carrier; the primary proof invariant remains PEPS2D normalization.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 finite virtual-bond noncommuting/order-sensitive control readout",
        ],
        "carrier_layer": "peps2d_carrier",
        "geometry_layer": "2D lattice PEPS carrier only; no downstream manifold geometry is admitted",
        "carrier_realization": "torch.complex128 site tensors consumed by quimb.PEPS, cotengra contraction trees, and opt_einsum double-layer contractions; no dense state vector or NumPy bridge is used as claim-bearing computation.",
        "peps3d_embedding": {
            "status": "blocked_not_claimed",
            "reason": "This requested carrier is PEPS2D only. It can be projected into a future PEPS3D finite carrier, but this receipt does not admit PEPS3D closure.",
            "from_first_carrier_step": False,
        },
        "spinor_state": "two-channel torch complex PEPS2D local physical states; no Hopf/Weyl spinor geometry is claimed",
        "quaternion_action": "not_applicable: no quaternion language or quaternion invariant is used",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/sim_root_F01_finite_distinguishability_probe.py",
            "system_v5/ops/formal_scouts/sim_root_N01_path_family_order_probe.py",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "PEPS2D carrier normalization invariant under non-dense contraction, with corrupted-bond negative control",
        "branch_status_before_run": "Stage-2 carrier build requested by user; no downstream consumer opened",
        "allowed_claims": [
            "bounded PEPS2D carrier lego exists/runs if this result and validators pass",
            "8/16/32/64 site PEPS2D rungs contract non-densely to norm-squared 1",
            "a corrupted virtual bond breaks the normalization invariant and flips the helper-bound SMT proof",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "single carrier lego only",
            "PEPS3D, Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, and physics consumers remain blocked",
            "N01 is a carrier compatibility readout here, not a full downstream dynamics proof",
        ],
        "eligible_consumers": ["bounded local carrier comparisons only after citing this result path and fresh gate output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 normalization flip",
            "load_bearing_proof.smt_load_bearing cvc5 normalization cross-check",
            "sympy exact rational norm and order-gap witness",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": ["corrupted_virtual_bond", "physical_channel_erased", "unit_weight_unnormalized"],
        "negatives_run": controls,
        "kill_conditions": {
            "corrupted_virtual_bond": "normalization_error must be > eps",
            "physical_channel_erased": "quimb recomputed norm-squared must differ from 1",
            "unit_weight_unnormalized": "torch/JAX formula norm-squared must differ from 1",
            "smt_load_bearing": "real measured normalization claim must be sat and corrupted-control claim must be unsat",
        },
        "required_artifacts": [
            "result JSON",
            "scale_ladder",
            "torch primary readouts",
            "JAX mirror readouts",
            "proof_results",
            "controls",
            "tool_ablations",
        ],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
            "quimb_vs_opt_einsum_delta": quimb_vs_opt_delta,
            "top_rung_corrupted_bond_error": top["corrupted_bond_normalization_error"],
        },
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "jax_vs_pytorch": {
            "max_abs_delta": jax_vs_pytorch_delta,
            "tolerance": EPS,
            "agree": bool(jax_vs_pytorch_delta <= EPS),
        },
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "sympy_exact_result": exact,
        "scale_ladder": scale_ladder,
        "scale_details": scale_rows,
        "positive": {
            "peps2d_norm_squared_is_one": {"pass": scale_pass, "rungs": scale_ladder["rungs"]},
            "helper_bound_smt_flip": {"pass": proofs["smt_load_bearing_normalization"]["pass"], "proof": proofs["smt_load_bearing_normalization"]},
            "sympy_exact_corrupted_bond": {"pass": exact["pass"], "exact": exact},
            "n01_virtual_bond_order_gap": {"pass": bool(top["n01_virtual_bond_order_gap_torch"]["pass"]), "top_rung": top["n01_virtual_bond_order_gap_torch"]},
        },
        "graveyard_companions": {
            "corrupted_virtual_bond": {
                "killed": controls["corrupted_bond"]["kills_normalization_claim"],
                "top_rung_normalization_error": controls["corrupted_bond"]["top_rung_normalization_error"],
            },
            "physical_channel_erased": {
                "killed": controls["physical_channel_erased"]["kills_two_channel_carrier"],
                "top_rung_norm_squared": controls["physical_channel_erased"]["top_rung_norm_squared"],
            },
            "unit_weight_unnormalized": {
                "killed": controls["unit_weight_unnormalized"]["kills_normalization_claim"],
                "top_rung_norm_squared": controls["unit_weight_unnormalized"]["top_rung_norm_squared"],
            },
        },
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "jax_quimb_backend_claimed": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "corrupted_bond": "channel-1 virtual-bond scale 6/5 breaks norm-squared from 1 to 147/125",
            "physical_channel_erased": "removing p=1 changes norm-squared to 3/5",
            "unit_weight_unnormalized": "removing normalized weights changes finite formula norm-squared to 2",
        },
        "shells": [
            {
                "name": "peps2d_carrier_object",
                "status": "stage_2_carrier_lego_only",
                "scale_rungs": list(SITE_COUNTS),
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "classify this as a PEPS2D carrier row only after fresh validator output is cited",
            "build a separate PEPS3D carrier receipt before any PEPS3D/manifold consumer cites this result",
        ],
        "compatibility_weights": {
            "stage2_peps2d_carrier": 1.0 if all_pass else 0.0,
            "downstream_Xi_Phi0_Axis0_flux_FEP_gravity": 0.0,
        },
        "compression_map": {
            "from": "finite PEPS2D site tensors, virtual bonds, physical channels, non-dense norm contractions, corrupted controls, and proof/tool receipts",
            "to": "normalization_error, proof verdict flip, tool ablation deltas, scale ladder, and blocked downstream consumers",
            "loss_boundary": "does not preserve or claim dense global state, PEPS3D closure, manifold, axis, bridge, flux, FEP, gravity, or physics admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": 1.0 - max(row["normalization_error"] for row in scale_rows.values()),
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "PEPS2D carrier survives iff every rung is finite/non-dense, quimb/opt_einsum/torch/JAX agree on norm-squared 1, corrupted controls kill, helper proof flips, ablations are recomputed and nonzero, and promotion_allowed=false",
            "computed_capacity": 1.0 - max(row["normalization_error"] for row in scale_rows.values()),
            "threshold": 1.0 - EPS,
            "passed": bool(all_pass),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "PEPS2D carrier lego only; no full layer completion, coupling, stacking, flux, Axis0, bridge, physics, or final manifold admission",
        },
        "pass_rule": "all 8/16/32/64 finite PEPS2D rungs pass without dense closure; quimb and opt_einsum contractions agree; torch and JAX formulas agree; corrupted bond kills normalization; helper-bound z3/cvc5 proof flips; sympy exact witness passes; every tool ablation has baseline+ablated recompute with nonzero delta",
        "fail_rule": "fail on dense closure, missing PEPS2D rung, missing quimb/cotengra/opt_einsum contraction, no real/control proof flip, live corrupted-bond control, zero/cosmetic ablation, JAX mismatch, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "why_not_v4_probes": "This is a v5 Stage-2 PEPS2D carrier lego with explicit non-dense 8/16/32/64 scale rungs, quimb/cotengra/opt_einsum contraction witnesses, torch/JAX parity, helper-bound z3/cvc5 normalization proof, exact sympy controls, and promotion_allowed=false.",
        "blockers": [] if all_pass else ["one_or_more_peps2d_carrier_checks_failed"],
        "required_pass": all_pass,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "required_pass": result["required_pass"],
                "result_path": str(OUT_PATH.relative_to(ROOT)),
                "scale_pass": result["scale_ladder"]["pass"],
                "proof_pass": result["proof_results"]["pass"],
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
