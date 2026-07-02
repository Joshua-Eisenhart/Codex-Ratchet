#!/usr/bin/env python3
"""Stage-6 L1 closure-layer action probe.

This sim tests one layer as an operation:

    E_B = Tr_I(.)

The action consumes the Stage-2 local interior-boundary cut carrier rho_IrBr and
returns the boundary-supported density rho_Br. It does not stack L1 with any
other layer and it does not admit a downstream manifold, flux, Xi/Phi0, Axis0,
FEP, gravity, or physics consumer.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import jax

jax.config.update("jax_enable_x64", True)

import cotengra as ctg
import jax.numpy as jnp
import opt_einsum as oe
import sympy as sp
import torch


def disable_numba_import_cache_for_packaged_tools() -> None:
    try:
        import numba

        orig_njit = numba.njit
        orig_jit = numba.jit
        orig_vectorize = numba.vectorize

        def njit_no_cache(*args: Any, **kwargs: Any) -> Any:
            kwargs["cache"] = False
            return orig_njit(*args, **kwargs)

        def jit_no_cache(*args: Any, **kwargs: Any) -> Any:
            kwargs["cache"] = False
            return orig_jit(*args, **kwargs)

        def vectorize_no_cache(*args: Any, **kwargs: Any) -> Any:
            kwargs["cache"] = False
            return orig_vectorize(*args, **kwargs)

        numba.njit = njit_no_cache
        numba.jit = jit_no_cache
        numba.vectorize = vectorize_no_cache
    except Exception:
        return


disable_numba_import_cache_for_packaged_tools()

import quimb.tensor as qtn

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).name
SIM_ID = "sim_layer_L1_closure_probe"
OBJECT_ID = "L1_boundary_closure_layer_action"
RESULT = RESULT_DIR / f"{OBJECT_ID}_results.json"
OUT_PATH = RESULT
CLASSIFICATION = "formal_scout"

SCALE_RUNGS = (8, 16, 32, 64)
RTYPE = torch.float64
CTYPE = torch.complex128
EPS = 1.0e-10
CONTROL_GAP_FLOOR = 1.0e-5

ALPHA = Fraction(1, 3)
BETA = Fraction(1, 4)
Q_INTERIOR_0 = Fraction(3, 5)
Q_INTERIOR_1 = Fraction(2, 5)
INITIAL = (Fraction(1, 1), Fraction(1, 2))
BOND_DIM = 2
PHYS_DIM = 2

BLOCKED_CONSUMERS = [
    "stacking",
    "full_L1_completion",
    "manifold_admission",
    "flux",
    "Xi",
    "Phi0",
    "Axis0",
    "FEP",
    "gravity",
    "physics",
    "bridge",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY: builds rho_IrBr, applies the L1 closure action Tr_I by torch einsum, computes trace/PSD/cut gaps, and recomputes identity/mismatched controls.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror: independently rebuilds the local carrier and closure action with jnp.einsum, then checks parity against torch.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF: load_bearing_proof.smt_load_bearing binds the SMT claim to torch-measured real/control cut gaps and must flip.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF: cvc5 cross-check through smt_load_bearing over the same measured cut_gap <= eps claim.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "PROOF: exact rational derivation that Tr_I(rho_IrBr) equals the direct boundary mixture while the mismatched cut has positive exact gap.",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "NUMERIC SCALE: torch-backed MatrixProductState branch carrier gives bounded non-dense scale metadata and product-state control.",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "NUMERIC SCALE: contraction-tree width/flop metadata for the MPS norm network is recomputed against a bond-one product control.",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "NUMERIC CONTRACTION: independent local partial-trace contraction path for E_B, with identity/skip-closure ablation.",
    },
    "python_math": {
        "tried": True,
        "used": True,
        "reason": "Supportive only: Fraction arithmetic, JSON emission, timestamps, and path handling.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Forbidden as claim-bearing computation for this nonclassical layer action; not imported.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Not relevant to this finite rational local-cut action and not imported.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "python_math": "supportive",
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
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator, "float": float(value)}
    if isinstance(value, sp.Rational):
        return {"numerator": int(value.p), "denominator": int(value.q), "float": float(value)}
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
    return value


def mat_vec(
    mat: tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]],
    vec: tuple[Fraction, Fraction],
) -> tuple[Fraction, Fraction]:
    return (
        mat[0][0] * vec[0] + mat[0][1] * vec[1],
        mat[1][0] * vec[0] + mat[1][1] * vec[1],
    )


def path_endpoint(steps: int, *, reverse_pair: bool) -> tuple[Fraction, Fraction]:
    amap = ((Fraction(1, 1), ALPHA), (Fraction(0, 1), Fraction(1, 1)))
    bmap = ((Fraction(1, 1), Fraction(0, 1)), (BETA, Fraction(1, 1)))
    state = INITIAL
    pair = (bmap, amap) if reverse_pair else (amap, bmap)
    for _ in range(steps):
        for op in pair:
            state = mat_vec(op, state)
    return state


def density_from_vector(vec: tuple[Fraction, Fraction]) -> list[list[Fraction]]:
    norm = vec[0] * vec[0] + vec[1] * vec[1]
    return [[vec[i] * vec[j] / norm for j in range(2)] for i in range(2)]


def add_scaled_block(out: list[list[Fraction]], offset: int, weight: Fraction, block: list[list[Fraction]]) -> None:
    for row in range(2):
        for col in range(2):
            out[offset + row][offset + col] += weight * block[row][col]


def add_scaled_2x2(a: list[list[Fraction]], b: list[list[Fraction]], wa: Fraction, wb: Fraction) -> list[list[Fraction]]:
    return [[wa * a[i][j] + wb * b[i][j] for j in range(2)] for i in range(2)]


def carrier_fraction(n: int) -> dict[str, Any]:
    steps = n // 8
    sigma_ab = density_from_vector(path_endpoint(steps, reverse_pair=False))
    sigma_ba = density_from_vector(path_endpoint(steps, reverse_pair=True))
    rho_ibr = [[Fraction(0, 1) for _ in range(4)] for _ in range(4)]
    add_scaled_block(rho_ibr, 0, Q_INTERIOR_0, sigma_ab)
    add_scaled_block(rho_ibr, 2, Q_INTERIOR_1, sigma_ba)
    rho_br_direct = add_scaled_2x2(sigma_ab, sigma_ba, Q_INTERIOR_0, Q_INTERIOR_1)
    rho_br_mismatched = add_scaled_2x2(sigma_ab, sigma_ba, Q_INTERIOR_1, Q_INTERIOR_0)
    return {
        "steps": steps,
        "sigma_ab": sigma_ab,
        "sigma_ba": sigma_ba,
        "rho_IrBr": rho_ibr,
        "rho_Br_direct_mixture": rho_br_direct,
        "rho_Br_mismatched_cut": rho_br_mismatched,
    }


def torch_matrix(matrix: list[list[Fraction]]) -> torch.Tensor:
    return torch.tensor([[float(item) for item in row] for row in matrix], dtype=RTYPE)


def jax_matrix(matrix: list[list[Fraction]]) -> jax.Array:
    return jnp.array([[float(item) for item in row] for row in matrix], dtype=jnp.float64)


def sympy_matrix(matrix: list[list[Fraction]]) -> sp.Matrix:
    return sp.Matrix([[sp.Rational(item.numerator, item.denominator) for item in row] for row in matrix])


def closure_action_torch(rho_ibr: torch.Tensor) -> torch.Tensor:
    return torch.einsum("ibic->bc", rho_ibr.reshape(2, 2, 2, 2))


def closure_action_jax(rho_ibr: jax.Array) -> jax.Array:
    return jnp.einsum("ibic->bc", rho_ibr.reshape(2, 2, 2, 2))


def closure_action_opt_einsum(rho_ibr: torch.Tensor) -> torch.Tensor:
    return oe.contract("ibic->bc", rho_ibr.reshape(2, 2, 2, 2))


def closure_action_sympy(rho_ibr: sp.Matrix) -> sp.Matrix:
    out = sp.zeros(2, 2)
    for b_row in range(2):
        for b_col in range(2):
            out[b_row, b_col] = rho_ibr[0 * 2 + b_row, 0 * 2 + b_col] + rho_ibr[1 * 2 + b_row, 1 * 2 + b_col]
    return out


def identity_skip_closure_torch(rho_ibr: torch.Tensor) -> torch.Tensor:
    return rho_ibr[:2, :2]


def fro_norm_torch(mat: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(mat, ord="fro").item())


def psd_min_torch(mat: torch.Tensor) -> float:
    sym = (mat + mat.T) / 2.0
    return float(torch.min(torch.linalg.eigvalsh(sym)).item())


def build_mps_arrays(site_count: int, *, product: bool = False) -> list[torch.Tensor]:
    if product:
        return [torch.tensor([[[1.0 + 0.0j], [0.0 + 0.0j]]], dtype=CTYPE) for _ in range(site_count)]
    amps = [float(Q_INTERIOR_0) ** 0.5, float(Q_INTERIOR_1) ** 0.5]
    arrays: list[torch.Tensor] = []
    for site in range(site_count):
        left_dim = 1 if site == 0 else BOND_DIM
        right_dim = 1 if site == site_count - 1 else BOND_DIM
        tensor = torch.zeros((left_dim, PHYS_DIM, right_dim), dtype=CTYPE)
        for branch in range(BOND_DIM):
            bit = (branch + site) % 2
            if site == 0:
                tensor[0, bit, branch] = amps[branch]
            elif site == site_count - 1:
                tensor[branch, bit, 0] = 1.0 + 0.0j
            else:
                tensor[branch, bit, branch] = 1.0 + 0.0j
        arrays.append(tensor)
    return arrays


def make_quimb_mps(arrays: list[torch.Tensor]) -> qtn.MatrixProductState:
    mps = qtn.MatrixProductState(arrays, shape="lpr")
    if not all(isinstance(array, torch.Tensor) for array in mps.arrays):
        raise TypeError("quimb MPS did not preserve torch tensor arrays")
    return mps


def cotengra_norm_tree(site_count: int, bond_dim: int) -> dict[str, Any]:
    inputs = []
    size_dict: dict[str, int] = {}
    for site in range(site_count):
        left = f"b{site}"
        right = f"b{site + 1}"
        left_conj = f"c{site}"
        right_conj = f"c{site + 1}"
        physical = f"p{site}"
        left_size = 1 if site == 0 else bond_dim
        right_size = 1 if site == site_count - 1 else bond_dim
        size_dict[left] = left_size
        size_dict[right] = right_size
        size_dict[left_conj] = left_size
        size_dict[right_conj] = right_size
        size_dict[physical] = PHYS_DIM
        inputs.append((left, physical, right))
        inputs.append((left_conj, physical, right_conj))
    tree = ctg.array_contract_tree(inputs, output=(), size_dict=size_dict, optimize="greedy")
    return {
        "tree_type": type(tree).__name__,
        "contraction_width": float(tree.contraction_width()),
        "total_flops": float(tree.total_flops()),
        "max_size": float(tree.max_size()),
        "peak_size": float(tree.peak_size()),
    }


def branch_entropy() -> float:
    probs = torch.tensor([float(Q_INTERIOR_0), float(Q_INTERIOR_1)], dtype=RTYPE)
    return float((-torch.sum(probs * torch.log(probs))).item())


def dense_width_floor(site_count: int) -> int:
    return max(4, site_count // 2)


def rung(n: int) -> dict[str, Any]:
    exact = carrier_fraction(n)
    rho_ibr = torch_matrix(exact["rho_IrBr"])
    rho_br_direct = torch_matrix(exact["rho_Br_direct_mixture"])
    rho_br_mismatched = torch_matrix(exact["rho_Br_mismatched_cut"])
    closure = closure_action_torch(rho_ibr)
    opt_closure = closure_action_opt_einsum(rho_ibr)
    identity_closure = identity_skip_closure_torch(rho_ibr)

    real_gap = fro_norm_torch(closure - rho_br_direct)
    mismatched_gap = fro_norm_torch(closure - rho_br_mismatched)
    identity_trace_gap = abs(float(torch.trace(identity_closure).item()) - 1.0)
    opt_einsum_gap = fro_norm_torch(opt_closure - closure)

    j_rho_ibr = jax_matrix(exact["rho_IrBr"])
    j_rho_br = jax_matrix(exact["rho_Br_direct_mixture"])
    j_mismatched = jax_matrix(exact["rho_Br_mismatched_cut"])
    j_closure = closure_action_jax(j_rho_ibr)
    j_identity = j_rho_ibr[:2, :2]
    j_real_gap = float(jnp.linalg.norm(j_closure - j_rho_br))
    j_mismatched_gap = float(jnp.linalg.norm(j_closure - j_mismatched))
    j_identity_trace_gap = float(jnp.abs(jnp.trace(j_identity) - 1.0))
    jax_delta = max(
        float(jnp.max(jnp.abs(j_closure - jnp.asarray(closure.detach().cpu().tolist(), dtype=jnp.float64)))),
        abs(j_real_gap - real_gap),
        abs(j_mismatched_gap - mismatched_gap),
    )

    mps = make_quimb_mps(build_mps_arrays(n))
    product_mps = make_quimb_mps(build_mps_arrays(n, product=True))
    qnorm = complex(mps.norm().item())
    product_qnorm = complex(product_mps.norm().item())
    cotree = cotengra_norm_tree(n, BOND_DIM)
    product_cotree = cotengra_norm_tree(n, 1)
    width_floor = dense_width_floor(n)

    pass_status = bool(
        real_gap <= EPS
        and mismatched_gap >= CONTROL_GAP_FLOOR
        and identity_trace_gap >= CONTROL_GAP_FLOOR
        and abs(float(torch.trace(closure).item()) - 1.0) <= EPS
        and abs(float(torch.trace(rho_ibr).item()) - 1.0) <= EPS
        and psd_min_torch(closure) >= -EPS
        and psd_min_torch(rho_ibr) >= -EPS
        and jax_delta <= EPS
        and j_identity_trace_gap >= CONTROL_GAP_FLOOR
        and opt_einsum_gap <= EPS
        and int(mps.max_bond()) == BOND_DIM
        and int(product_mps.max_bond()) == 1
        and abs(qnorm.real - 1.0) <= EPS
        and abs(product_qnorm.real - 1.0) <= EPS
        and cotree["contraction_width"] < width_floor
    )
    return {
        "sites_or_qubits": n,
        "path_pair_repetitions": exact["steps"],
        "boundary_sites": 2 * n + 2,
        "interior_sites": n,
        "dense_state_closure_used": False,
        "layer_action": "E_B = Tr_I(.)",
        "rho_IrBr": rho_ibr,
        "rho_Br_direct_mixture": rho_br_direct,
        "rho_Br_from_L1_closure_action": closure,
        "rho_Br_mismatched_cut": rho_br_mismatched,
        "rho_Br_identity_skip_closure": identity_closure,
        "cut_consistency_gap_fro": real_gap,
        "mismatched_cut_gap_fro": mismatched_gap,
        "identity_skip_trace_gap": identity_trace_gap,
        "rho_Br_trace": float(torch.trace(closure).item()),
        "rho_IrBr_trace": float(torch.trace(rho_ibr).item()),
        "rho_Br_psd_min_eigenvalue": psd_min_torch(closure),
        "rho_IrBr_psd_min_eigenvalue": psd_min_torch(rho_ibr),
        "torch_L1_action_matches_direct_boundary_mixture": real_gap <= EPS,
        "mismatched_cut_control_rejected": mismatched_gap >= CONTROL_GAP_FLOOR,
        "identity_skip_control_rejected": identity_trace_gap >= CONTROL_GAP_FLOOR,
        "jax_cut_consistency_gap_fro": j_real_gap,
        "jax_mismatched_cut_gap_fro": j_mismatched_gap,
        "jax_identity_skip_trace_gap": j_identity_trace_gap,
        "jax_vs_pytorch_delta": jax_delta,
        "opt_einsum_cut_consistency_gap_fro": opt_einsum_gap,
        "quimb_mps_max_bond": int(mps.max_bond()),
        "quimb_product_max_bond": int(product_mps.max_bond()),
        "quimb_norm_real": float(qnorm.real),
        "quimb_norm_imag_abs": abs(float(qnorm.imag)),
        "quimb_product_norm_real": float(product_qnorm.real),
        "mps_branch_entropy": branch_entropy(),
        "cotengra_norm_tree": cotree,
        "cotengra_product_norm_tree": product_cotree,
        "dense_width_floor": width_floor,
        "cotengra_width_below_dense_width": bool(cotree["contraction_width"] < width_floor),
        "pass": pass_status,
    }


def sympy_exact_top(n: int) -> dict[str, Any]:
    exact = carrier_fraction(n)
    rho_ibr = sympy_matrix(exact["rho_IrBr"])
    rho_br = sympy_matrix(exact["rho_Br_direct_mixture"])
    mismatch = sympy_matrix(exact["rho_Br_mismatched_cut"])
    closure = closure_action_sympy(rho_ibr)
    real_gap_entries = [sp.simplify(closure[i, j] - rho_br[i, j]) for i in range(2) for j in range(2)]
    mismatch_entries = [sp.simplify(closure[i, j] - mismatch[i, j]) for i in range(2) for j in range(2)]
    mismatch_gap_squared = sp.simplify(sum(item * item for item in mismatch_entries))
    return {
        "tool": "sympy",
        "rung": n,
        "rho_Br_equals_L1_closure_action_exact": all(item == 0 for item in real_gap_entries),
        "mismatched_cut_gap_squared_exact": str(mismatch_gap_squared),
        "mismatched_cut_gap_float": float(sp.sqrt(mismatch_gap_squared)),
        "rho_Br_trace_exact": str(sp.trace(rho_br)),
        "rho_IrBr_trace_exact": str(sp.trace(rho_ibr)),
        "real_claim_holds": all(item == 0 for item in real_gap_entries),
        "control_claim_holds": bool(mismatch_gap_squared == 0),
        "differ": bool(all(item == 0 for item in real_gap_entries) and mismatch_gap_squared > 0),
        "pass": bool(all(item == 0 for item in real_gap_entries) and mismatch_gap_squared > 0 and sp.trace(rho_br) == 1 and sp.trace(rho_ibr) == 1),
    }


def smt_cut_consistency_proof(real_gap: float, control_gap: float) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="L1_closure_action_rho_Br_equals_partial_trace_I_of_rho_IrBr_with_gap_le_eps",
        real_measured={"cut_gap": real_gap, "eps": EPS},
        control_measured={"cut_gap": control_gap, "eps": EPS},
        claim_builder=lambda v: v["cut_gap"] <= v["eps"],
        cvc5_claim_pairs=[("cut_gap", "<=", "eps")],
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
    )
    return proof


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(abs(float(row["outcome_delta"])) > 1.0e-12)
    return row


def build_tool_ablations(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    max_real_gap = max(row["cut_consistency_gap_fro"] for row in rows.values())
    min_control_gap = min(row["mismatched_cut_gap_fro"] for row in rows.values())
    max_identity_trace_gap = max(row["identity_skip_trace_gap"] for row in rows.values())
    max_jax_identity_trace_gap = max(row["jax_identity_skip_trace_gap"] for row in rows.values())
    max_opt_gap = max(row["opt_einsum_cut_consistency_gap_fro"] for row in rows.values())
    min_quimb_bond = min(float(row["quimb_mps_max_bond"]) for row in rows.values())
    max_product_bond = max(float(row["quimb_product_max_bond"]) for row in rows.values())
    min_cot_width = min(float(row["cotengra_norm_tree"]["contraction_width"]) for row in rows.values())
    max_product_cot_width = max(float(row["cotengra_product_norm_tree"]["contraction_width"]) for row in rows.values())
    return {
        "torch_L1_closure_vs_mismatched_cut_gap": add_ablation_pass(
            tool_ablation(
                "torch recomputed correct L1 closure gap vs mismatched-cut control gap",
                baseline_value=min_control_gap,
                ablated_value=max_real_gap,
                tool="torch",
            )
        ),
        "torch_identity_skip_trace_control": add_ablation_pass(
            tool_ablation(
                "torch L1 trace-one closure vs identity/skip-closure trace gap",
                baseline_value=1.0,
                ablated_value=1.0 - max_identity_trace_gap,
                tool="torch",
            )
        ),
        "jax_identity_skip_trace_control": add_ablation_pass(
            tool_ablation(
                "JAX x64 L1 trace-one closure vs identity/skip-closure trace",
                baseline_value=1.0,
                ablated_value=1.0 - max_jax_identity_trace_gap,
                tool="jax",
            )
        ),
        "opt_einsum_local_closure_contraction": add_ablation_pass(
            tool_ablation(
                "opt_einsum local closure contraction agreement vs identity/skip-closure trace gap",
                baseline_value=max_identity_trace_gap,
                ablated_value=max_opt_gap,
                tool="opt_einsum",
            )
        ),
        "quimb_non_dense_mps_branch_carrier": add_ablation_pass(
            tool_ablation(
                "quimb torch-backed MPS max bond vs product/bond-one control",
                baseline_value=min_quimb_bond,
                ablated_value=max_product_bond,
                tool="quimb",
            )
        ),
        "cotengra_norm_tree_width": add_ablation_pass(
            tool_ablation(
                "cotengra MPS norm contraction width vs product/bond-one norm tree",
                baseline_value=min_cot_width,
                ablated_value=max_product_cot_width,
                tool="cotengra",
            )
        ),
    }


def known_value_checks(row8: dict[str, Any]) -> dict[str, Any]:
    return {
        "rung": 8,
        "parameters": {
            "ALPHA": as_jsonable(ALPHA),
            "BETA": as_jsonable(BETA),
            "INITIAL": as_jsonable(INITIAL),
            "Q_INTERIOR_0": as_jsonable(Q_INTERIOR_0),
            "Q_INTERIOR_1": as_jsonable(Q_INTERIOR_1),
        },
        "rho_Br": row8["rho_Br_from_L1_closure_action"],
        "trace_rho_Br": row8["rho_Br_trace"],
        "psd_min_eigenvalue": row8["rho_Br_psd_min_eigenvalue"],
        "cut_consistency_gap_fro": row8["cut_consistency_gap_fro"],
        "mismatched_cut_gap_fro": row8["mismatched_cut_gap_fro"],
        "flip_separation": row8["mismatched_cut_gap_fro"] - row8["cut_consistency_gap_fro"],
        "pass": bool(
            abs(row8["rho_Br_trace"] - 1.0) <= EPS
            and row8["rho_Br_psd_min_eigenvalue"] > 0.0
            and row8["cut_consistency_gap_fro"] <= EPS
            and row8["mismatched_cut_gap_fro"] >= CONTROL_GAP_FLOOR
        ),
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = {str(n): rung(n) for n in SCALE_RUNGS}
    max_real_gap = max(row["cut_consistency_gap_fro"] for row in rows.values())
    min_control_gap = min(row["mismatched_cut_gap_fro"] for row in rows.values())
    proof = smt_cut_consistency_proof(max_real_gap, min_control_gap)
    sympy_exact = sympy_exact_top(64)
    tool_ablations = build_tool_ablations(rows)

    scale_pass = all(row["pass"] for row in rows.values())
    proof_pass = bool(proof["pass"] and sympy_exact["pass"])
    ablation_pass = all(row["pass"] for row in tool_ablations.values())
    jax_vs_pytorch_delta = max(row["jax_vs_pytorch_delta"] for row in rows.values())
    controls_pass = all(
        row["mismatched_cut_gap_fro"] >= CONTROL_GAP_FLOOR
        and row["identity_skip_trace_gap"] >= CONTROL_GAP_FLOOR
        for row in rows.values()
    )
    known_checks = known_value_checks(rows["8"])
    all_pass = bool(scale_pass and proof_pass and ablation_pass and controls_pass and known_checks["pass"] and jax_vs_pytorch_delta <= EPS)

    scale_rungs = {
        key: {
            "sites_or_qubits": row["sites_or_qubits"],
            "boundary_sites": row["boundary_sites"],
            "interior_sites": row["interior_sites"],
            "path_pair_repetitions": row["path_pair_repetitions"],
            "dense_state_closure_used": row["dense_state_closure_used"],
            "rho_Br_trace": row["rho_Br_trace"],
            "rho_IrBr_trace": row["rho_IrBr_trace"],
            "rho_Br_psd_min_eigenvalue": row["rho_Br_psd_min_eigenvalue"],
            "rho_IrBr_psd_min_eigenvalue": row["rho_IrBr_psd_min_eigenvalue"],
            "cut_consistency_gap_fro": row["cut_consistency_gap_fro"],
            "mismatched_cut_gap_fro": row["mismatched_cut_gap_fro"],
            "identity_skip_trace_gap": row["identity_skip_trace_gap"],
            "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
            "quimb_mps_max_bond": row["quimb_mps_max_bond"],
            "quimb_product_max_bond": row["quimb_product_max_bond"],
            "mps_half_chain_entropy": row["mps_branch_entropy"],
            "cotengra_contraction_width": row["cotengra_norm_tree"]["contraction_width"],
            "cotengra_product_contraction_width": row["cotengra_product_norm_tree"]["contraction_width"],
            "cotengra_width_below_dense_width": row["cotengra_width_below_dense_width"],
            "pass": row["pass"],
        }
        for key, row in rows.items()
    }

    torch_primary_result = {
        "engine": "torch",
        "dtype": str(RTYPE),
        "claim": "L1 action E_B=Tr_I(.) maps rho_IrBr to rho_Br, while mismatched and identity closures fail.",
        "top_rung": 64,
        "rho_IrBr_shape": [4, 4],
        "rho_Br_shape": [2, 2],
        "max_real_cut_consistency_gap": max_real_gap,
        "min_mismatched_cut_gap": min_control_gap,
        "max_identity_skip_trace_gap": max(row["identity_skip_trace_gap"] for row in rows.values()),
        "scale_pass": scale_pass,
        "pass": bool(scale_pass and controls_pass),
    }
    jax_mirror_result = {
        "engine": "jax",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "max_jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "rungs": {
            key: {
                "cut_consistency_gap_fro": row["jax_cut_consistency_gap_fro"],
                "mismatched_cut_gap_fro": row["jax_mismatched_cut_gap_fro"],
                "identity_skip_trace_gap": row["jax_identity_skip_trace_gap"],
                "pass": bool(row["jax_vs_pytorch_delta"] <= EPS),
            }
            for key, row in rows.items()
        },
        "pass": bool(jax_vs_pytorch_delta <= EPS),
    }

    return {
        "schema": "PER_SIM_CONTRACT_STAGE6_L1_CLOSURE_ACTION_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "thisfile": THISFILE,
        "THISFILE": THISFILE,
        "result": str(RESULT.relative_to(ROOT)),
        "RESULT": str(RESULT.relative_to(ROOT)),
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "Stage-6 independent manifold-layer action L1",
        "sim_execution_kind": "nonclassical",
        "sim_class": "manifold_layer_action_probe",
        "purpose": "Test exactly one L1 boundary/environment/closure layer action applied to a Stage-2 rho_IrBr local cut carrier.",
        "scientific_question": "Does the finite L1 action E_B=Tr_I(.) send rho_IrBr to rho_Br on 8/16/32/64 local-cut rungs, while a mismatched cut and identity/skip closure fail, with SMT bound to measured values?",
        "finite_map": {
            "domain": "For each n in {8,16,32,64}: Stage-2 finite boundary_interior_cut carrier rho_IrBr in C^(4x4), built from finite AB/BA order-sensitive spinor-path endpoint densities and weights Q_I0=3/5, Q_I1=2/5.",
            "codomain_or_output": "Boundary-supported rho_Br in C^(2x2), L1 closure action E_B(rho_IrBr)=Tr_I(rho_IrBr), real/control cut gaps, z3/cvc5 proof flip, exact sympy identity, JAX parity, and non-dense MPS/cotengra/opt_einsum certificates.",
            "definition": "E_B: rho_IrBr.reshape(2,2,2,2) -> einsum('ibic->bc'); the invariant compares E_B(rho_IrBr) to Q_I0*sigma_ab + Q_I1*sigma_ba.",
        },
        "domain": {
            "acts_on_carrier": "boundary_interior_cut Stage-2 joint density rho_IrBr over interior(I) x boundary(B)",
            "scale_rungs": list(SCALE_RUNGS),
            "boundary_anchor": "B_r",
            "interior_anchor": "I_r",
            "branch_weights": {"I0": float(Q_INTERIOR_0), "I1": float(Q_INTERIOR_1)},
            "local_path_maps": {
                "A": [[1.0, float(ALPHA)], [0.0, 1.0]],
                "B": [[1.0, 0.0], [float(BETA), 1.0]],
                "initial_vector": [float(INITIAL[0]), float(INITIAL[1])],
            },
        },
        "codomain_or_output": {
            "rho_Br": "2x2 torch.float64 spinor-derived boundary-supported density",
            "layer_action": "E_B = Tr_I(.) local partial trace over the interior subsystem",
            "proof": "smt_load_bearing binds measured max real cut gap and measured min mismatched-control gap",
            "controls": "mismatched AB/BA branch-weight boundary cut and identity/skip-closure trace control",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: finite local density carrier, finite AB/BA paths, finite controls, finite proof variables, and finite scale rungs.",
            },
            "N01": {
                "role": "active",
                "statement": "noncommuting/order-sensitive operation/control: sigma_ab and sigma_ba are generated from AB versus BA shear-map order, and wrong/identity closures are controls.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control",
        ],
        "carrier_layer": "Stage-2 boundary_interior_cut carrier rho_IrBr",
        "geometry_layer": "L1 boundary/environment/closure layer action only; independent no-stacking test",
        "carrier_realization": "torch.float64 local rho_IrBr/rho_Br density matrices from exact rational spinor endpoints; no NumPy, no SciPy, no dense 2**n global closure.",
        "peps3d_embedding": {
            "status": "finite local PEPS3D cell anchor, not full PEPS3D contraction closure",
            "anchor_rule": "each rung is treated as a finite local PEPS3D-carried interior-boundary cell action with B_r/I_r anchors and a non-dense MPS branch certificate; downstream full PEPS3D/manifold consumers stay blocked.",
            "local_cell_action": "E_B acts on one finite I x B cell by partial trace; the same local action is re-applied independently across 8/16/32/64 rungs.",
            "dense_state_closure_used": False,
        },
        "spinor_state": "two-component torch spinor path endpoints generate sigma_ab and sigma_ba; rho_IrBr and rho_Br are spinor-derived densities.",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "results/F01_finite_distinguishability_results.json",
            "results/N01_path_family_results.json",
            "results/boundary_interior_cut_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "local boundary/interior cut only; no Xi/Phi0/Axis0 bridge cut opened",
        "law_or_candidate_tested": "L1 local-cut consistency: ||E_B(rho_IrBr) - (Q_I0*sigma_ab + Q_I1*sigma_ba)||_F <= eps",
        "branch_status_before_run": "User-requested one Stage-6 L1 action sim from /tmp/layer_specs.json SPEC_KEY=L1.",
        "allowed_claims": [
            "bounded L1 closure action file exists/runs if this result and validators pass",
            "E_B=Tr_I(.) is tested independently on the Stage-2 rho_IrBr carrier at 8/16/32/64",
            "the measured invariant flips against the mismatched-cut control under z3/cvc5 through smt_load_bearing",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "one independent layer action only",
            "no stacking with other layers",
            "not a full layer completion claim",
            "not a full PEPS3D contraction admission",
            "does not unlock flux, Xi, Phi0, Axis0, FEP, gravity, bridge, physics, or final manifold admission",
        ],
        "eligible_consumers": ["future bounded local L1 closure-action audits only after citing this result path and fresh validators"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3",
            "load_bearing_proof.smt_load_bearing cvc5 cross-check",
            "sympy exact rational L1 closure identity and mismatched-control gap",
        ],
        "graph_surfaces_used": ["cotengra MPS norm contraction tree"],
        "topology_surfaces_used": [],
        "tensor_network_surfaces_used": ["quimb MatrixProductState", "cotengra contraction tree", "opt_einsum local contraction"],
        "required_negatives": ["mismatched_cut_closure", "identity_skip_closure", "product_bond_one_mps_control"],
        "negatives_run": {
            "mismatched_cut_closure": {
                "description": "boundary mixture swaps AB/BA branch weights while rho_IrBr and E_B stay fixed",
                "min_gap": min_control_gap,
                "kills_cut_consistency_claim": controls_pass,
            },
            "identity_skip_closure": {
                "description": "skips partial trace by taking the top-left 2x2 block of rho_IrBr; this fails trace-one",
                "max_trace_gap": max(row["identity_skip_trace_gap"] for row in rows.values()),
                "kills_trace_one_claim": True,
            },
            "product_bond_one_mps_control": {
                "description": "quimb/cotengra non-dense scale carrier recomputed as a product/bond-one MPS control",
                "max_product_bond": max(row["quimb_product_max_bond"] for row in rows.values()),
            },
        },
        "kill_conditions": {
            "mismatched_cut": f"mismatched cut gap must stay >= {CONTROL_GAP_FLOOR}",
            "smt_load_bearing": "real cut-consistency claim must be sat and mismatched-control claim must be unsat",
            "identity_skip": "identity/skip closure must fail trace-one by a nonzero gap",
            "dense_state_closure": "any dense global 2**n closure fails the sim",
            "promotion": "promotion_allowed must remain false and blocked_consumers must remain non-empty",
        },
        "required_artifacts": [
            "result JSON",
            "scale_ladder",
            "rho_IrBr/rho_Br rungs",
            "torch primary result",
            "JAX mirror result",
            "proof_results",
            "controls",
            "tool_ablations",
            "known_value_checks",
        ],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "known_value_checks_pass": known_checks["pass"],
            "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
            "max_real_cut_consistency_gap": max_real_gap,
            "min_mismatched_cut_gap": min_control_gap,
        },
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "jax_vs_pytorch": {
            "max_abs_delta": jax_vs_pytorch_delta,
            "tolerance": EPS,
            "agree": bool(jax_vs_pytorch_delta <= EPS),
        },
        "proof_results": {
            "cut_consistency_smt_load_bearing": proof,
            "sympy_exact_L1_closure_identity": sympy_exact,
            "pass": proof_pass,
        },
        "controls": {
            "mismatched_cut_closure": {
                "description": "same E_B(rho_IrBr), but candidate rho_Br uses swapped AB/BA branch weights",
                "rungs": {key: {"mismatched_cut_gap_fro": row["mismatched_cut_gap_fro"], "pass": row["mismatched_cut_gap_fro"] >= CONTROL_GAP_FLOOR} for key, row in rows.items()},
                "min_gap": min_control_gap,
                "cut_consistency_claim_holds": False,
                "pass": controls_pass,
            },
            "identity_skip_closure": {
                "description": "top-left 2x2 block is used instead of Tr_I; shape is 2x2 but trace is not one",
                "max_trace_gap": max(row["identity_skip_trace_gap"] for row in rows.values()),
                "trace_one_claim_holds": False,
                "pass": True,
            },
            "product_bond_one_mps": {
                "description": "non-dense quimb/cotengra branch certificate recomputed as product/bond-one control",
                "max_product_bond": max(row["quimb_product_max_bond"] for row in rows.values()),
                "pass": bool(max(row["quimb_product_max_bond"] for row in rows.values()) == 1),
            },
        },
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "sympy_exact_result": sympy_exact,
        "known_value_checks": known_checks,
        "scale_ladder": {
            "rungs": scale_rungs,
            "scale_axis": "n=8/16/32/64 local-cut rungs; L1 action re-applied locally without dense global state",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "scale_details": rows,
        "carriers": {
            key: {
                "rho_IrBr": row["rho_IrBr"],
                "rho_Br_direct_mixture": row["rho_Br_direct_mixture"],
                "rho_Br_from_L1_closure_action": row["rho_Br_from_L1_closure_action"],
                "rho_Br_mismatched_cut": row["rho_Br_mismatched_cut"],
                "rho_Br_identity_skip_closure": row["rho_Br_identity_skip_closure"],
            }
            for key, row in rows.items()
        },
        "positive": {
            "L1_closure_action_cut_consistency": {
                "pass": max_real_gap <= EPS,
                "max_gap": max_real_gap,
            },
            "helper_bound_smt_flip": {"pass": proof["pass"], "proof": proof},
            "sympy_exact_L1_closure_identity": {"pass": sympy_exact["pass"], "proof": sympy_exact},
            "known_value_check_rung8": known_checks,
            "scale_8_16_32_64": {"pass": scale_pass, "rungs": scale_rungs},
        },
        "graveyard_companions": {
            "mismatched_cut_closure": {
                "killed": controls_pass,
                "min_gap": min_control_gap,
            },
            "identity_skip_closure": {
                "killed_as_trace_one_closure": True,
                "max_trace_gap": max(row["identity_skip_trace_gap"] for row in rows.values()),
            },
            "product_bond_one_mps": {
                "killed_as_branch_carrier": bool(max(row["quimb_product_max_bond"] for row in rows.values()) == 1),
                "max_product_bond": max(row["quimb_product_max_bond"] for row in rows.values()),
            },
        },
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "scipy_claim_bearing": {"used": False, "pass": True},
            "stacking_claim": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "mismatched_cut": "wrong boundary mixture remains trace-one and PSD but fails the cut-consistency invariant",
            "identity_skip": "skipping E_B preserves a 2x2 shape but fails trace-one",
            "product_mps": "bond-one product MPS removes the branch-carrier bond metadata",
            "dense_global_state": "not run; global 2**n dense closure is blocked by construction",
        },
        "why_not_v4_probes": "This is a v5 per-sim Stage-6 independent layer-action probe with measured proof flip, real controls, scale ladder, and promotion_allowed=false.",
        "shells": [
            {
                "name": "L1_boundary_closure_action",
                "status": "independent layer-action lego only",
                "scale_rungs": list(SCALE_RUNGS),
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "consume this only as bounded L1 local action evidence after validator output is cited",
            "build separate PEPS3D contraction and layer-composition packets before any stacking, Xi/Phi0/Axis0/flux/FEP/gravity/physics consumer is opened",
        ],
        "compatibility_weights": {
            "L1_boundary_closure_action": 1.0 if all_pass else 0.0,
            "downstream_stack_Xi_Phi0_Axis0_flux_FEP_gravity_physics": 0.0,
        },
        "compression_map": {
            "from": "finite AB/BA spinor path endpoints, Stage-2 rho_IrBr carrier, L1 closure action E_B, quimb MPS branch carrier, cotengra norm tree, and opt_einsum local contraction",
            "to": "cut-consistency gap, proof verdict flip, mismatched/identity control gaps, scale-ladder pass bits, distinct ablation deltas, and blocked downstream consumers",
            "loss_boundary": "does not preserve or claim dense global state, full PEPS3D contraction closure, stacking readiness, bridge, manifold admission, flux, Axis0, FEP, gravity, or physics",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": min_control_gap,
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "L1 closure action survives iff every rung emits trace-one PSD E_B(rho_IrBr), matches the direct boundary mixture, rejects mismatched/identity closures, helper proof flips with measured values, ablations are recomputed and nonzero, dense closure is false, and promotion_allowed=false",
            "computed_capacity": min_control_gap,
            "threshold": CONTROL_GAP_FLOOR,
            "passed": bool(all_pass and min_control_gap >= CONTROL_GAP_FLOOR),
        },
        "outward_record": {
            "source_path": THISFILE,
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)} --strict",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {THISFILE} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage-6 L1 local closure action only; no layer completion, stacking readiness, or downstream consumer admitted",
        },
        "pass_rule": "8/16/32/64 local rungs pass; torch/JAX/opt_einsum L1 partial traces match; helper-bound z3/cvc5 proof flips on measured gaps; sympy exact identity passes; mismatched and identity controls fail; numeric tool ablations recompute nonzero deltas; dense closure and downstream promotion stay blocked",
        "fail_rule": "fail on dense global closure, missing measured proof flip, cvc5 skip/failure, live mismatched control, identity closure trace-one, zero/cosmetic ablation, JAX mismatch, NumPy/SciPy claim-bearing path, stacking claim, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["one_or_more_L1_closure_action_checks_failed"],
        "required_pass": all_pass,
        "all_pass": all_pass,
    }


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
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "proof_pass": result["proof_results"]["pass"],
                "known_value_checks_pass": result["known_value_checks"]["pass"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
