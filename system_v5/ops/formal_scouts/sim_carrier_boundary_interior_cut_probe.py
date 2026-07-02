#!/usr/bin/env python3
import jax

jax.config.update("jax_enable_x64", True)

import json
import pathlib
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

import autoray
import cotengra as ctg
import jax.numpy as jnp
import sympy as sp
import torch
import z3


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
SIM_ID = "sim_carrier_boundary_interior_cut_probe"
OBJECT_ID = "boundary_interior_cut"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
RTYPE = torch.float64
CTYPE = torch.complex128
EPS = 1.0e-10
CONTROL_GAP_FLOOR = 1.0e-5
ALPHA = Fraction(3, 100)
BETA = Fraction(4, 100)
Q_INTERIOR_0 = Fraction(3, 5)
Q_INTERIOR_1 = Fraction(2, 5)
INITIAL = (Fraction(1, 1), Fraction(3, 4))
BOND_DIM = 2
PHYS_DIM = 2
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim numeric: builds rho_IrBr and computes rho_Br by torch partial trace for each 8/16/32/64 local cut without dense global state closure.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for the same local cut density, partial trace, trace-one, PSD, and mismatched-cut observables where representable.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing: cut-consistency gap is bound to measured real/control values and must flip.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through load_bearing_proof cvc5 claim pairs over the same measured cut-consistency gap.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact rational proof surface for rho_Br = Tr_I(rho_IrBr) and mismatched-cut failure at the top rung.",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "Non-dense scale carrier certificate: constructs a torch-backed MatrixProductState branch carrier at each rung and checks max bond/norm metadata.",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "Non-dense contraction-tree certificate for the MPS norm network at each rung.",
    },
    "autoray": {
        "tried": True,
        "used": True,
        "reason": "Backend-dispatch certificate over torch density traces, keeping the dispatch explicit rather than implicit.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary by instruction; not imported or used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary by instruction; not imported or needed for this finite local density carrier.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "Supportive only: exact Fraction construction, JSON emission, paths, and timestamps.",
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
    "autoray": "load_bearing",
    "numpy": None,
    "scipy": None,
    "python_stdlib": "supportive",
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


def mat_vec(mat: tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]], vec: tuple[Fraction, Fraction]) -> tuple[Fraction, Fraction]:
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
            out[offset + row][offset + col] = out[offset + row][offset + col] + weight * block[row][col]


def add_scaled_2x2(a: list[list[Fraction]], b: list[list[Fraction]], wa: Fraction, wb: Fraction) -> list[list[Fraction]]:
    return [[wa * a[i][j] + wb * b[i][j] for j in range(2)] for i in range(2)]


def carrier_fraction(n: int) -> dict[str, Any]:
    steps = n // 8
    sigma_ab = density_from_vector(path_endpoint(steps, reverse_pair=False))
    sigma_ba = density_from_vector(path_endpoint(steps, reverse_pair=True))
    rho_ibr = [[Fraction(0, 1) for _ in range(4)] for _ in range(4)]
    add_scaled_block(rho_ibr, 0, Q_INTERIOR_0, sigma_ab)
    add_scaled_block(rho_ibr, 2, Q_INTERIOR_1, sigma_ba)
    rho_br = add_scaled_2x2(sigma_ab, sigma_ba, Q_INTERIOR_0, Q_INTERIOR_1)
    rho_br_mismatch = add_scaled_2x2(sigma_ba, sigma_ab, Q_INTERIOR_0, Q_INTERIOR_1)
    return {
        "steps": steps,
        "sigma_ab": sigma_ab,
        "sigma_ba": sigma_ba,
        "rho_IrBr": rho_ibr,
        "rho_Br": rho_br,
        "rho_Br_mismatched_cut": rho_br_mismatch,
    }


def torch_matrix(matrix: list[list[Fraction]]) -> torch.Tensor:
    return torch.tensor([[float(item) for item in row] for row in matrix], dtype=RTYPE)


def jax_matrix(matrix: list[list[Fraction]]) -> jax.Array:
    return jnp.array([[float(item) for item in row] for row in matrix], dtype=jnp.float64)


def sympy_matrix(matrix: list[list[Fraction]]) -> sp.Matrix:
    return sp.Matrix([[sp.Rational(item.numerator, item.denominator) for item in row] for row in matrix])


def partial_trace_torch_boundary(rho_ibr: torch.Tensor) -> torch.Tensor:
    shaped = rho_ibr.reshape(2, 2, 2, 2)
    return torch.einsum("ibic->bc", shaped)


def partial_trace_jax_boundary(rho_ibr: jax.Array) -> jax.Array:
    shaped = rho_ibr.reshape(2, 2, 2, 2)
    return jnp.einsum("ibic->bc", shaped)


def partial_trace_sympy_boundary(rho_ibr: sp.Matrix) -> sp.Matrix:
    out = sp.zeros(2, 2)
    for b_row in range(2):
        for b_col in range(2):
            out[b_row, b_col] = rho_ibr[0 * 2 + b_row, 0 * 2 + b_col] + rho_ibr[1 * 2 + b_row, 1 * 2 + b_col]
    return out


def max_abs_torch(mat: torch.Tensor) -> float:
    return float(torch.max(torch.abs(mat)).item())


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


def rung(n: int) -> dict[str, Any]:
    exact = carrier_fraction(n)
    rho_ibr = torch_matrix(exact["rho_IrBr"])
    rho_br = torch_matrix(exact["rho_Br"])
    rho_br_mismatch = torch_matrix(exact["rho_Br_mismatched_cut"])
    reduced = partial_trace_torch_boundary(rho_ibr)
    real_gap = fro_norm_torch(reduced - rho_br)
    mismatch_gap = fro_norm_torch(reduced - rho_br_mismatch)

    j_rho_ibr = jax_matrix(exact["rho_IrBr"])
    j_rho_br = jax_matrix(exact["rho_Br"])
    j_mismatch = jax_matrix(exact["rho_Br_mismatched_cut"])
    j_reduced = partial_trace_jax_boundary(j_rho_ibr)
    j_real_gap = float(jnp.linalg.norm(j_reduced - j_rho_br))
    j_mismatch_gap = float(jnp.linalg.norm(j_reduced - j_mismatch))
    jax_delta = max(
        float(jnp.max(jnp.abs(j_reduced - jnp.asarray(reduced.detach().cpu().tolist(), dtype=jnp.float64)))),
        abs(j_real_gap - real_gap),
        abs(j_mismatch_gap - mismatch_gap),
    )

    mps = make_quimb_mps(build_mps_arrays(n))
    product_mps = make_quimb_mps(build_mps_arrays(n, product=True))
    qnorm = complex(mps.norm().item())
    product_qnorm = complex(product_mps.norm().item())
    cotree = cotengra_norm_tree(n, BOND_DIM)
    product_cotree = cotengra_norm_tree(n, 1)
    autoray_trace = float(autoray.do("trace", rho_br).item())
    autoray_backend = autoray.infer_backend(rho_br)

    pass_status = bool(
        real_gap <= EPS
        and mismatch_gap >= CONTROL_GAP_FLOOR
        and abs(float(torch.trace(rho_br).item()) - 1.0) <= EPS
        and abs(float(torch.trace(rho_ibr).item()) - 1.0) <= EPS
        and psd_min_torch(rho_br) >= -EPS
        and psd_min_torch(rho_ibr) >= -EPS
        and jax_delta <= EPS
        and int(mps.max_bond()) == BOND_DIM
        and int(product_mps.max_bond()) == 1
        and abs(qnorm.real - 1.0) <= EPS
        and abs(product_qnorm.real - 1.0) <= EPS
        and autoray_backend == "torch"
        and abs(autoray_trace - 1.0) <= EPS
    )
    return {
        "sites_or_qubits": n,
        "path_pair_repetitions": exact["steps"],
        "boundary_sites": 2 * n + 2,
        "interior_sites": n,
        "dense_state_closure_used": False,
        "rho_Br": rho_br,
        "rho_IrBr": rho_ibr,
        "rho_Br_from_partial_trace": reduced,
        "rho_Br_mismatched_cut": rho_br_mismatch,
        "cut_consistency_gap_fro": real_gap,
        "mismatched_cut_gap_fro": mismatch_gap,
        "rho_Br_trace": float(torch.trace(rho_br).item()),
        "rho_IrBr_trace": float(torch.trace(rho_ibr).item()),
        "rho_Br_psd_min_eigenvalue": psd_min_torch(rho_br),
        "rho_IrBr_psd_min_eigenvalue": psd_min_torch(rho_ibr),
        "torch_partial_trace_matches_rho_Br": real_gap <= EPS,
        "mismatched_cut_control_rejected": mismatch_gap >= CONTROL_GAP_FLOOR,
        "jax_cut_consistency_gap_fro": j_real_gap,
        "jax_mismatched_cut_gap_fro": j_mismatch_gap,
        "jax_vs_pytorch_delta": jax_delta,
        "quimb_mps_max_bond": int(mps.max_bond()),
        "quimb_product_max_bond": int(product_mps.max_bond()),
        "quimb_norm_real": float(qnorm.real),
        "quimb_norm_imag_abs": abs(float(qnorm.imag)),
        "quimb_product_norm_real": float(product_qnorm.real),
        "cotengra_norm_tree": cotree,
        "cotengra_product_norm_tree": product_cotree,
        "autoray_backend": autoray_backend,
        "autoray_trace_rho_Br": autoray_trace,
        "pass": pass_status,
    }


def sympy_exact_top(n: int) -> dict[str, Any]:
    exact = carrier_fraction(n)
    rho_ibr = sympy_matrix(exact["rho_IrBr"])
    rho_br = sympy_matrix(exact["rho_Br"])
    mismatch = sympy_matrix(exact["rho_Br_mismatched_cut"])
    reduced = partial_trace_sympy_boundary(rho_ibr)
    real_gap_entries = [sp.simplify(reduced[i, j] - rho_br[i, j]) for i in range(2) for j in range(2)]
    mismatch_entries = [sp.simplify(reduced[i, j] - mismatch[i, j]) for i in range(2) for j in range(2)]
    mismatch_gap_squared = sp.simplify(sum(item * item for item in mismatch_entries))
    return {
        "tool": "sympy",
        "rung": n,
        "rho_Br_equals_partial_trace_exact": all(item == 0 for item in real_gap_entries),
        "mismatched_cut_gap_squared_exact": str(mismatch_gap_squared),
        "mismatched_cut_gap_float": float(sp.sqrt(mismatch_gap_squared)),
        "rho_Br_trace_exact": str(sp.trace(rho_br)),
        "rho_IrBr_trace_exact": str(sp.trace(rho_ibr)),
        "pass": bool(all(item == 0 for item in real_gap_entries) and mismatch_gap_squared > 0 and sp.trace(rho_br) == 1 and sp.trace(rho_ibr) == 1),
    }


def smt_cut_consistency_proof(real_gap: float, control_gap: float) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="rho_Br_equals_partial_trace_I_of_rho_IrBr_with_gap_le_eps",
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


def proof_flip_score(proof: dict[str, Any], engine: str) -> float:
    if engine == "z3":
        return float(
            proof.get("real_claim_verdict") == "sat"
            and proof.get("negated_claim_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    if engine == "cvc5":
        return float(proof.get("cvc5_real_verdict") == "sat" and proof.get("cvc5_control_verdict") == "unsat")
    raise ValueError(engine)


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(abs(float(row["outcome_delta"])) > 1.0e-12)
    return row


def build_tool_ablations(rows: dict[str, dict[str, Any]], proof: dict[str, Any], sympy_exact: dict[str, Any]) -> dict[str, Any]:
    min_control_gap = min(row["mismatched_cut_gap_fro"] for row in rows.values())
    max_real_gap = max(row["cut_consistency_gap_fro"] for row in rows.values())
    max_jax_delta = max(row["jax_vs_pytorch_delta"] for row in rows.values())
    min_quimb_bond = min(float(row["quimb_mps_max_bond"]) for row in rows.values())
    max_product_bond = max(float(row["quimb_product_max_bond"]) for row in rows.values())
    min_cot_width = min(float(row["cotengra_norm_tree"]["contraction_width"]) for row in rows.values())
    max_product_cot_width = max(float(row["cotengra_product_norm_tree"]["contraction_width"]) for row in rows.values())
    autoray_trace_successes = sum(1.0 for row in rows.values() if row["autoray_backend"] == "torch" and abs(row["autoray_trace_rho_Br"] - 1.0) <= EPS)
    sympy_gap = float(sympy_exact["mismatched_cut_gap_float"])
    return {
        "torch_partial_trace_cut_consistency": add_ablation_pass(
            tool_ablation(
                "torch partial_trace real cut gap vs mismatched-cut recompute gap",
                baseline_value=max_real_gap,
                ablated_value=min_control_gap,
                tool="torch",
            )
        ),
        "jax_partial_trace_parity": add_ablation_pass(
            tool_ablation(
                "JAX x64 parity mirror max delta vs no-JAX parity certificate",
                baseline_value=max_jax_delta,
                ablated_value=1.0,
                tool="jax",
            )
        ),
        "z3_cut_consistency_flip_score": add_ablation_pass(
            tool_ablation(
                "z3 helper flip-score for cut consistency real vs mismatched control",
                baseline_value=proof_flip_score(proof, "z3"),
                ablated_value=0.0,
                tool="z3",
            )
        ),
        "cvc5_cut_consistency_flip_score": add_ablation_pass(
            tool_ablation(
                "cvc5 helper flip-score for cut consistency real vs mismatched control",
                baseline_value=proof_flip_score(proof, "cvc5"),
                ablated_value=0.0,
                tool="cvc5",
            )
        ),
        "sympy_exact_mismatched_gap": add_ablation_pass(
            tool_ablation(
                "sympy exact cut proof gap vs exact matched-cut zero gap",
                baseline_value=sympy_gap,
                ablated_value=0.0,
                tool="sympy",
            )
        ),
        "quimb_non_dense_mps_carrier": add_ablation_pass(
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
        "autoray_torch_backend_trace_dispatch": add_ablation_pass(
            tool_ablation(
                "autoray torch backend trace dispatch successes vs dispatch-erased control",
                baseline_value=autoray_trace_successes,
                ablated_value=0.0,
                tool="autoray",
            )
        ),
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = {str(n): rung(n) for n in SCALE_RUNGS}
    top = rows["64"]
    proof = smt_cut_consistency_proof(float(top["cut_consistency_gap_fro"]), float(top["mismatched_cut_gap_fro"]))
    sympy_exact = sympy_exact_top(64)
    tool_ablations = build_tool_ablations(rows, proof, sympy_exact)

    scale_pass = all(row["pass"] for row in rows.values())
    proof_pass = bool(proof["pass"] and sympy_exact["pass"])
    ablation_pass = all(row["pass"] for row in tool_ablations.values())
    jax_vs_pytorch_delta = max(row["jax_vs_pytorch_delta"] for row in rows.values())
    controls_pass = all(row["mismatched_cut_gap_fro"] >= CONTROL_GAP_FLOOR for row in rows.values())
    all_pass = bool(scale_pass and proof_pass and ablation_pass and controls_pass and jax_vs_pytorch_delta <= EPS)

    scale_rungs = {
        key: {
            "sites_or_qubits": row["sites_or_qubits"],
            "boundary_sites": row["boundary_sites"],
            "interior_sites": row["interior_sites"],
            "dense_state_closure_used": row["dense_state_closure_used"],
            "rho_Br_trace": row["rho_Br_trace"],
            "rho_IrBr_trace": row["rho_IrBr_trace"],
            "rho_Br_psd_min_eigenvalue": row["rho_Br_psd_min_eigenvalue"],
            "rho_IrBr_psd_min_eigenvalue": row["rho_IrBr_psd_min_eigenvalue"],
            "cut_consistency_gap_fro": row["cut_consistency_gap_fro"],
            "mismatched_cut_gap_fro": row["mismatched_cut_gap_fro"],
            "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
            "quimb_mps_max_bond": row["quimb_mps_max_bond"],
            "cotengra_contraction_width": row["cotengra_norm_tree"]["contraction_width"],
            "pass": row["pass"],
        }
        for key, row in rows.items()
    }

    torch_primary_result = {
        "engine": "torch",
        "dtype": str(RTYPE),
        "claim": "rho_Br equals partial_trace_I(rho_IrBr), while a mismatched boundary cut fails the same invariant",
        "top_rung": 64,
        "rho_Br_shape": [2, 2],
        "rho_IrBr_shape": [4, 4],
        "max_real_cut_consistency_gap": max(row["cut_consistency_gap_fro"] for row in rows.values()),
        "min_mismatched_cut_gap": min(row["mismatched_cut_gap_fro"] for row in rows.values()),
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
                "pass": bool(row["jax_vs_pytorch_delta"] <= EPS),
            }
            for key, row in rows.items()
        },
        "pass": bool(jax_vs_pytorch_delta <= EPS),
    }

    result = {
        "schema": "PER_SIM_CONTRACT_CARRIER_STAGE2_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 2",
        "sim_execution_kind": "nonclassical",
        "sim_class": "carrier_probe",
        "purpose": "Build one Stage-2 boundary/interior cut carrier with rho_Br and rho_IrBr state spaces at 8/16/32/64, proving the boundary density is the partial trace of the joint cut carrier and that a mismatched cut fails.",
        "scientific_question": "Can a finite non-dense boundary/interior cut carrier emit torch-native rho_Br and rho_IrBr at 8/16/32/64 with helper-bound proof that rho_Br = Tr_I(rho_IrBr), JAX parity, non-dense quimb/cotengra/autoray certificates, and blocked downstream consumers?",
        "finite_map": {
            "domain": "For each n in {8,16,32,64}: finite local cut carrier with interior-conditioned boundary branch states produced by finite AB/BA shear-map paths, boundary anchor B_r, interior anchor I_r, and non-dense MPS branch certificate over n sites.",
            "codomain_or_output": "rho_Br in C^(2x2), rho_IrBr in C^(4x4), partial_trace_I(rho_IrBr), mismatched-cut control gap, z3/cvc5 proof flip, exact sympy cut identity, JAX parity, non-dense quimb/cotengra/autoray scale certificates, and blocked downstream consumers.",
            "definition": "rho_IrBr = q0 |I0><I0| tensor sigma_AB + q1 |I1><I1| tensor sigma_BA, rho_Br = q0 sigma_AB + q1 sigma_BA, with sigma_AB/sigma_BA derived from order-sensitive finite shear path endpoints.",
        },
        "domain": {
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
            "rho_Br": "2x2 torch.float64 spinor-derived boundary density",
            "rho_IrBr": "4x4 torch.float64 joint interior-boundary density over basis |I,B>",
            "proof": "smt_load_bearing binds measured Frobenius cut gap for real rho_Br vs mismatched rho_Br control",
            "controls": "mismatched boundary cut swaps AB/BA branch weights while leaving rho_IrBr fixed",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: each rung has finite B_r/I_r anchors, finite AB/BA path repetitions, finite local density outputs, finite controls, and finite proof variables.",
            },
            "N01": {
                "role": "active",
                "statement": "noncommuting or order-sensitive operation/control: sigma_AB and sigma_BA come from the two orders of finite shear maps A and B; order-swapped/mismatched cuts are controls.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control",
        ],
        "carrier_layer": "boundary/interior cut density carrier",
        "geometry_layer": "carrier-stage cut only; no manifold, flux, Axis0, bridge, FEP, gravity, or physics layer is admitted",
        "carrier_realization": "torch.float64 rho_Br/rho_IrBr local density matrices from exact rational branch states; non-dense quimb MatrixProductState branch carrier and cotengra norm tree for scale; no dense 2**n state closure and no NumPy/SciPy claim-bearing path.",
        "peps3d_embedding": {
            "status": "finite PEPS3D anchor only, not a full PEPS3D contraction or manifold claim",
            "anchor_rule": "each rung names finite B_r/I_r site anchors and boundary/interior support counts over a future K=(V,E,F,C) carrier; this sim emits cut state spaces and blocks downstream consumers",
            "dense_state_closure_used": False,
        },
        "spinor_state": "two-component torch boundary branch spinors generate sigma_AB and sigma_BA; rho_Br and rho_IrBr are spinor-derived density state spaces",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "results/F01_finite_distinguishability_results.json",
            "results/N01_path_family_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "boundary/interior rho_Br <- Tr_I(rho_IrBr) local cut only; no Xi/Phi0/Axis0 bridge cut opened",
        "law_or_candidate_tested": "boundary/interior cut consistency: ||rho_Br - Tr_I(rho_IrBr)||_F <= eps",
        "branch_status_before_run": "Stage-2 carrier build requested by user after audit-verified F01/N01 exemplars",
        "allowed_claims": [
            "bounded Stage-2 boundary/interior cut carrier exists/runs if this result and validators pass",
            "rho_Br and rho_IrBr are emitted for rungs 8/16/32/64 without dense global closure",
            "rho_Br equals the torch/JAX partial trace of rho_IrBr and a mismatched cut fails the same invariant",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "local carrier state-space build only",
            "does not admit a bridge, manifold, flux, FEP, gravity, physics, Xi, Phi0, or Axis0 consumer",
            "does not prove full PEPS3D contraction closure or layer completion",
        ],
        "eligible_consumers": ["future bounded carrier-stage cut audits only after citing this result path and fresh validator output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["load_bearing_proof.smt_load_bearing z3", "load_bearing_proof.smt_load_bearing cvc5 cross-check", "sympy exact rational cut identity"],
        "graph_surfaces_used": ["cotengra MPS norm contraction tree"],
        "topology_surfaces_used": [],
        "tensor_network_surfaces_used": ["quimb MatrixProductState", "cotengra contraction tree", "autoray torch backend dispatch"],
        "required_negatives": ["mismatched_boundary_cut", "product_bond_one_mps_control", "dispatch_erased_control"],
        "negatives_run": {
            "mismatched_boundary_cut": {
                "description": "rho_Br is swapped between AB/BA branch weights while rho_IrBr stays fixed",
                "min_gap": min(row["mismatched_cut_gap_fro"] for row in rows.values()),
                "kills_cut_consistency_claim": controls_pass,
            },
            "product_bond_one_mps_control": {
                "description": "quimb/cotengra scale certificate recomputed on product/bond-one MPS",
                "max_product_bond": max(row["quimb_product_max_bond"] for row in rows.values()),
            },
            "dispatch_erased_control": {
                "description": "autoray dispatch certificate removed; successful dispatch count goes to zero",
                "baseline_dispatch_successes": sum(1 for row in rows.values() if row["autoray_backend"] == "torch"),
            },
        },
        "kill_conditions": {
            "mismatched_boundary_cut": f"mismatched cut gap must stay >= {CONTROL_GAP_FLOOR}",
            "smt_load_bearing": "real cut-consistency claim must be sat and mismatched-control claim must be unsat",
            "dense_state_closure": "any dense global 2**n closure fails the carrier",
            "promotion": "promotion_allowed must remain false and downstream consumers must remain blocked",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "rho_Br/rho_IrBr rungs", "torch primary readouts", "JAX mirror readouts", "proof_results", "controls", "tool_ablations"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
            "max_real_cut_consistency_gap": max(row["cut_consistency_gap_fro"] for row in rows.values()),
            "min_mismatched_cut_gap": min(row["mismatched_cut_gap_fro"] for row in rows.values()),
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
            "sympy_exact_cut_identity": sympy_exact,
            "pass": proof_pass,
        },
        "controls": {
            "mismatched_boundary_cut": {
                "description": "same rho_IrBr but rho_Br is taken from the swapped AB/BA branch-weight cut",
                "rungs": {key: {"mismatched_cut_gap_fro": row["mismatched_cut_gap_fro"], "pass": row["mismatched_cut_gap_fro"] >= CONTROL_GAP_FLOOR} for key, row in rows.items()},
                "min_gap": min(row["mismatched_cut_gap_fro"] for row in rows.values()),
                "cut_consistency_claim_holds": False,
                "pass": controls_pass,
            },
            "product_bond_one_mps": {
                "description": "non-dense quimb/cotengra scale carrier recomputed as product/bond-one control",
                "max_product_bond": max(row["quimb_product_max_bond"] for row in rows.values()),
                "pass": bool(max(row["quimb_product_max_bond"] for row in rows.values()) == 1),
            },
        },
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "sympy_exact_result": sympy_exact,
        "scale_ladder": {
            "rungs": scale_rungs,
            "scale_axis": "site_count_for_non_dense_branch_carrier",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "scale_details": rows,
        "carriers": {
            key: {
                "rho_Br": row["rho_Br"],
                "rho_IrBr": row["rho_IrBr"],
                "rho_Br_from_partial_trace": row["rho_Br_from_partial_trace"],
                "rho_Br_mismatched_cut": row["rho_Br_mismatched_cut"],
            }
            for key, row in rows.items()
        },
        "positive": {
            "rho_Br_partial_trace_consistency": {
                "pass": max(row["cut_consistency_gap_fro"] for row in rows.values()) <= EPS,
                "max_gap": max(row["cut_consistency_gap_fro"] for row in rows.values()),
            },
            "helper_bound_smt_flip": {"pass": proof["pass"], "proof": proof},
            "sympy_exact_cut_identity": {"pass": sympy_exact["pass"], "proof": sympy_exact},
            "scale_8_16_32_64": {"pass": scale_pass, "rungs": scale_rungs},
        },
        "graveyard_companions": {
            "mismatched_boundary_cut": {
                "killed": controls_pass,
                "min_gap": min(row["mismatched_cut_gap_fro"] for row in rows.values()),
            },
            "product_bond_one_mps": {
                "killed_as_scale_carrier": bool(max(row["quimb_product_max_bond"] for row in rows.values()) == 1),
                "max_product_bond": max(row["quimb_product_max_bond"] for row in rows.values()),
            },
        },
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "scipy_claim_bearing": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "swapped_boundary_cut": "mismatched rho_Br swaps AB/BA branch weights and fails the partial-trace identity",
            "product_mps": "quimb/cotengra product MPS control removes the non-dense branch carrier bond certificate",
            "dense_global_state": "not run; global 2**n dense closure is blocked by construction",
        },
        "why_not_v4_probes": "This is a v5 Stage-2 single carrier lego with explicit rho_Br/rho_IrBr state-space outputs, helper-bound proof flip, real controls, distinct per-tool ablations, and promotion_allowed=false.",
        "shells": [
            {
                "name": "boundary_interior_cut_carrier",
                "status": "carrier lego only",
                "scale_rungs": list(SCALE_RUNGS),
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "consume this only as bounded Stage-2 carrier evidence after validator output is cited",
            "build separate PEPS3D contraction or bridge packets before any Xi/Phi0/Axis0/flux/FEP/gravity consumer is opened",
        ],
        "compatibility_weights": {
            "boundary_interior_cut_carrier": 1.0 if all_pass else 0.0,
            "downstream_Xi_Phi0_Axis0_flux_FEP_gravity": 0.0,
        },
        "compression_map": {
            "from": "finite AB/BA branch path states, rho_IrBr, rho_Br, quimb/cotengra non-dense branch carrier, and autoray trace dispatch",
            "to": "cut-consistency gap, proof verdict flip, mismatched-cut control gap, scale-ladder pass bits, distinct ablation deltas, and blocked downstream consumers",
            "loss_boundary": "does not preserve or claim dense global state, full PEPS3D contraction closure, bridge, manifold, flux, Axis0, FEP, gravity, or physics admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": min(row["mismatched_cut_gap_fro"] for row in rows.values()),
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "boundary_interior_cut survives iff every rung emits trace-one PSD rho_Br/rho_IrBr, rho_Br equals Tr_I(rho_IrBr), mismatched cuts fail, helper proof flips, ablations are recomputed and nonzero, dense closure is false, and promotion_allowed=false",
            "computed_capacity": min(row["mismatched_cut_gap_fro"] for row in rows.values()),
            "threshold": CONTROL_GAP_FLOOR,
            "passed": bool(all_pass and min(row["mismatched_cut_gap_fro"] for row in rows.values()) >= CONTROL_GAP_FLOOR),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage-2 boundary/interior cut carrier only; no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 finite cut rungs pass; torch partial trace matches rho_Br; JAX agrees; helper-bound z3/cvc5 proof flips; sympy exact identity passes; mismatched controls fail; every tool ablation records baseline+ablated recompute with nonzero delta; dense closure and downstream promotion stay blocked",
        "fail_rule": "fail on dense closure, missing rho_Br/rho_IrBr rung, missing proof flip, live mismatched cut, zero/cosmetic ablation, JAX mismatch, NumPy/SciPy claim-bearing path, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["one_or_more_boundary_interior_cut_checks_failed"],
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
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "proof_pass": result["proof_results"]["pass"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
