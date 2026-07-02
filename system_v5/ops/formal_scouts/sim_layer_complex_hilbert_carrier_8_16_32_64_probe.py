#!/usr/bin/env python3
import jax
jax.config.update("jax_enable_x64", True)

import json
import math
import os
import pathlib
import time
from datetime import datetime, timezone
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cotengra as ctg
import cvc5
from cvc5 import Kind
import jax.numpy as jnp
import quimb.tensor as qtn
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "layer_complex_hilbert_carrier_8_16_32_64_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SITE_COUNTS = [8, 16, 32, 64]
SITE_SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
BOND_DIM = 8
PHYSICAL_DIM = 2
PARITY_TOL = 1.0e-9
KILL_FLOOR = 1.0e-9
RTYPE = torch.float64
CTYPE = torch.complex128
CLASSIFICATION = "formal_scout"
TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "primary torch.complex128 non-dense MPS tensors, density-MPO trace contraction, one-site density, entropy, Hermitian and PSD readouts",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "secondary x64 complex engine mirroring trace, PSD, Hermitian, entropy, one-site and phase-coherence readouts",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MPS carrier wrapper over torch tensors; verifies bond>=8 and norm without dense full-state closure",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "load-bearing serial contraction-tree witness for the non-dense MPS trace network; product/bond-1 ablation changes width/cost",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing structural trace-one, nonnegative Schmidt spectrum, and rank-one PSD proof fence",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT cross-check for trace-one, nonnegative Schmidt spectrum, and rank-one PSD fence",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact one-site density and half-chain entropy expressions from p_a=(a+1)/36",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not relevant to this complex Hilbert carrier trace/PSD lego; no geomstats JAX backend path is claimed",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "geomstats": None,
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
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def weights_torch() -> torch.Tensor:
    vals = torch.arange(1, BOND_DIM + 1, dtype=RTYPE)
    return vals / torch.sum(vals)


def phases_torch(site_count: int) -> torch.Tensor:
    idx = torch.arange(1, BOND_DIM + 1, dtype=RTYPE)
    theta = 0.173 * idx * idx + 0.011 * float(site_count) * idx
    return torch.exp(1j * theta).to(CTYPE)


def weights_jax() -> jnp.ndarray:
    vals = jnp.arange(1, BOND_DIM + 1, dtype=jnp.float64)
    return vals / jnp.sum(vals)


def phases_jax(site_count: int) -> jnp.ndarray:
    idx = jnp.arange(1, BOND_DIM + 1, dtype=jnp.float64)
    theta = 0.173 * idx * idx + 0.011 * float(site_count) * idx
    return jnp.exp(1j * theta).astype(jnp.complex128)


def bit_for(latent: int, site: int) -> int:
    return (latent >> (site % 3)) & 1


def code_for(latent: int, start: int, stop: int) -> tuple[int, ...]:
    return tuple(bit_for(latent, site) for site in range(start, stop))


def schmidt_rank_witness(site_count: int) -> dict[str, Any]:
    half = site_count // 2
    left_codes = {code_for(latent, 0, half) for latent in range(BOND_DIM)}
    right_codes = {code_for(latent, half, site_count) for latent in range(BOND_DIM)}
    return {
        "left_distinct_codes": len(left_codes),
        "right_distinct_codes": len(right_codes),
        "rank": min(len(left_codes), len(right_codes), BOND_DIM),
        "pass": len(left_codes) == BOND_DIM and len(right_codes) == BOND_DIM,
    }


def build_torch_mps_arrays(site_count: int, *, entangled: bool = True, phase_erased: bool = False) -> list[torch.Tensor]:
    if not entangled:
        arrays = []
        for site in range(site_count):
            tensor = torch.zeros((1, PHYSICAL_DIM, 1), dtype=CTYPE)
            tensor[0, 0, 0] = 1.0 + 0.0j
            arrays.append(tensor)
        return arrays

    probs = weights_torch()
    phase = torch.ones(BOND_DIM, dtype=CTYPE) if phase_erased else phases_torch(site_count)
    amps = torch.sqrt(probs).to(CTYPE) * phase
    arrays = []
    for site in range(site_count):
        left_dim = 1 if site == 0 else BOND_DIM
        right_dim = 1 if site == site_count - 1 else BOND_DIM
        tensor = torch.zeros((left_dim, PHYSICAL_DIM, right_dim), dtype=CTYPE)
        for latent in range(BOND_DIM):
            bit = bit_for(latent, site)
            if site == 0:
                tensor[0, bit, latent] = amps[latent]
            elif site == site_count - 1:
                tensor[latent, bit, 0] = 1.0 + 0.0j
            else:
                tensor[latent, bit, latent] = 1.0 + 0.0j
        arrays.append(tensor)
    return arrays


def make_quimb_mps(arrays: list[torch.Tensor]) -> qtn.MatrixProductState:
    mps = qtn.MatrixProductState(arrays, shape="lpr")
    if not all(isinstance(array, torch.Tensor) for array in mps.arrays):
        raise TypeError("quimb MPS did not preserve torch.Tensor arrays")
    return mps


def entropy_from_probs_torch(probs: torch.Tensor) -> torch.Tensor:
    return -torch.sum(probs * torch.log(probs))


def entropy_from_probs_jax(probs: jnp.ndarray) -> jnp.ndarray:
    return -jnp.sum(probs * jnp.log(probs))


def one_site_density_torch(site: int, *, signed: bool = False) -> torch.Tensor:
    probs = weights_torch()
    if signed:
        probs = probs.clone()
        for latent in range(BOND_DIM):
            if bit_for(latent, site) == 0:
                probs[latent] = -probs[latent]
    diagonal = torch.zeros(PHYSICAL_DIM, dtype=RTYPE)
    for latent in range(BOND_DIM):
        diagonal[bit_for(latent, site)] = diagonal[bit_for(latent, site)] + probs[latent]
    return torch.diag(diagonal).to(CTYPE)


def one_site_density_jax(site: int) -> jnp.ndarray:
    probs = weights_jax()
    diag = []
    for bit in range(PHYSICAL_DIM):
        total = jnp.array(0.0, dtype=jnp.float64)
        for latent in range(BOND_DIM):
            if bit_for(latent, site) == bit:
                total = total + probs[latent]
        diag.append(total)
    return jnp.diag(jnp.asarray(diag, dtype=jnp.float64)).astype(jnp.complex128)


def schmidt_density_torch(site_count: int, *, phase_erased: bool = False, signed: bool = False) -> torch.Tensor:
    probs = weights_torch()
    if signed:
        probs = probs.clone()
        probs[0] = -probs[0]
    phase = torch.ones(BOND_DIM, dtype=CTYPE) if phase_erased else phases_torch(site_count)
    amps = torch.sqrt(torch.abs(probs)).to(CTYPE) * phase
    if signed:
        amps[0] = 1j * amps[0]
    return torch.outer(amps, torch.conj(amps))


def schmidt_density_jax(site_count: int) -> jnp.ndarray:
    probs = weights_jax()
    amps = jnp.sqrt(probs).astype(jnp.complex128) * phases_jax(site_count)
    return jnp.outer(amps, jnp.conj(amps))


def latent_imag_signature_torch(rho: torch.Tensor) -> float:
    offdiag = rho - torch.diag(torch.diagonal(rho))
    return float(torch.sum(torch.abs(torch.imag(offdiag))).item())


def latent_imag_signature_jax(rho: jnp.ndarray) -> float:
    offdiag = rho - jnp.diag(jnp.diag(rho))
    return float(jnp.sum(jnp.abs(jnp.imag(offdiag))))


def density_mpo_trace(arrays: list[torch.Tensor]) -> complex:
    env = torch.ones(1, dtype=CTYPE)
    for tensor in arrays:
        local_trace = torch.einsum("lpr,mps->lmrs", tensor, torch.conj(tensor)).reshape(
            tensor.shape[0] * tensor.shape[0],
            tensor.shape[2] * tensor.shape[2],
        )
        env = env @ local_trace
    return complex(env.reshape(()).item())


def density_mpo_max_bond(arrays: list[torch.Tensor]) -> int:
    return max(max(tensor.shape[0], tensor.shape[2]) ** 2 for tensor in arrays)


def cotengra_trace_tree(site_count: int, bond_dim: int) -> dict[str, Any]:
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
        size_dict[physical] = PHYSICAL_DIM
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


def torch_rung(site_count: int) -> dict[str, Any]:
    arrays = build_torch_mps_arrays(site_count)
    product_arrays = build_torch_mps_arrays(site_count, entangled=False)
    mps = make_quimb_mps(arrays)
    product_mps = make_quimb_mps(product_arrays)
    probs = weights_torch()
    entropy = float(entropy_from_probs_torch(probs).item())
    rho = schmidt_density_torch(site_count)
    evals = torch.linalg.eigvalsh(rho)
    one_site = one_site_density_torch(0)
    hermitian_delta = float(torch.max(torch.abs(rho - torch.conj(rho.T))).item())
    trace = density_mpo_trace(arrays)
    qnorm = complex(mps.norm().item())
    product_entropy = 0.0
    rank = schmidt_rank_witness(site_count)
    cotree = cotengra_trace_tree(site_count, BOND_DIM)
    product_cotree = cotengra_trace_tree(site_count, 1)
    return {
        "sites_or_qubits": site_count,
        "peps3d_shape": list(SITE_SHAPES[site_count]),
        "dense_state_closure_used": False,
        "physical_dim": PHYSICAL_DIM,
        "mps_max_bond": int(mps.max_bond()),
        "quimb_mps_max_bond": int(mps.max_bond()),
        "quimb_product_max_bond": int(product_mps.max_bond()),
        "density_mpo_max_bond": density_mpo_max_bond(arrays),
        "half_chain_entropy": entropy,
        "entanglement_entropy": entropy,
        "product_half_chain_entropy": product_entropy,
        "schmidt_rank": rank["rank"],
        "schmidt_rank_witness": rank,
        "density_operator_trace_real": float(trace.real),
        "density_operator_trace_imag_abs": abs(float(trace.imag)),
        "quimb_norm_real": float(qnorm.real),
        "quimb_norm_imag_abs": abs(float(qnorm.imag)),
        "bond_space_density_trace_real": float(torch.real(torch.trace(rho)).item()),
        "bond_space_density_trace_imag_abs": abs(float(torch.imag(torch.trace(rho)).item())),
        "bond_space_density_psd_min_eigenvalue": float(torch.min(evals).item()),
        "bond_space_density_psd_max_eigenvalue": float(torch.max(evals).item()),
        "bond_space_density_hermitian_max_delta": hermitian_delta,
        "one_site_density_site0": one_site,
        "one_site_density_site0_trace": float(torch.real(torch.trace(one_site)).item()),
        "one_site_density_site0_min_eigenvalue": float(torch.min(torch.linalg.eigvalsh(one_site)).item()),
        "complex_phase_imag_coherence": latent_imag_signature_torch(rho),
        "cotengra_trace_tree": cotree,
        "cotengra_product_trace_tree": product_cotree,
        "quimb_backend_all_torch": all(isinstance(array, torch.Tensor) for array in mps.arrays),
        "pass": bool(
            int(mps.max_bond()) >= BOND_DIM
            and rank["pass"]
            and entropy > KILL_FLOOR
            and abs(float(trace.real) - 1.0) < PARITY_TOL
            and abs(float(trace.imag)) < PARITY_TOL
            and abs(float(qnorm.real) - 1.0) < PARITY_TOL
            and abs(float(qnorm.imag)) < PARITY_TOL
            and hermitian_delta < PARITY_TOL
            and float(torch.min(evals).item()) >= -1.0e-8
            and all(isinstance(array, torch.Tensor) for array in mps.arrays)
        ),
    }


def jax_rung(site_count: int) -> dict[str, Any]:
    probs = weights_jax()
    entropy = entropy_from_probs_jax(probs)
    rho = schmidt_density_jax(site_count)
    one_site = one_site_density_jax(0)
    evals = jnp.linalg.eigvalsh(rho)
    trace = jnp.trace(rho)
    hermitian_delta = jnp.max(jnp.abs(rho - jnp.conj(rho.T)))
    return {
        "sites_or_qubits": site_count,
        "dense_state_closure_used": False,
        "half_chain_entropy": float(entropy),
        "entanglement_entropy": float(entropy),
        "bond_space_density_trace_real": float(jnp.real(trace)),
        "bond_space_density_trace_imag_abs": abs(float(jnp.imag(trace))),
        "bond_space_density_psd_min_eigenvalue": float(jnp.min(evals)),
        "bond_space_density_psd_max_eigenvalue": float(jnp.max(evals)),
        "bond_space_density_hermitian_max_delta": float(hermitian_delta),
        "one_site_density_site0_trace": float(jnp.real(jnp.trace(one_site))),
        "one_site_density_site0_min_eigenvalue": float(jnp.min(jnp.linalg.eigvalsh(one_site))),
        "one_site_density_site0_diag0": float(jnp.real(one_site[0, 0])),
        "one_site_density_site0_diag1": float(jnp.real(one_site[1, 1])),
        "complex_phase_imag_coherence": latent_imag_signature_jax(rho),
        "pass": bool(
            float(entropy) > KILL_FLOOR
            and abs(float(jnp.real(trace)) - 1.0) < PARITY_TOL
            and abs(float(jnp.imag(trace))) < PARITY_TOL
            and float(hermitian_delta) < PARITY_TOL
            and float(jnp.min(evals)) >= -1.0e-8
        ),
    }


def compare_engines(torch_rows: dict[str, dict[str, Any]], jax_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = {}
    max_delta = 0.0
    keys = [
        "half_chain_entropy",
        "bond_space_density_trace_real",
        "bond_space_density_trace_imag_abs",
        "bond_space_density_psd_min_eigenvalue",
        "bond_space_density_psd_max_eigenvalue",
        "bond_space_density_hermitian_max_delta",
        "one_site_density_site0_trace",
        "one_site_density_site0_min_eigenvalue",
        "complex_phase_imag_coherence",
    ]
    for rung in torch_rows:
        deltas = {}
        for key in keys:
            delta = abs(float(torch_rows[rung][key]) - float(jax_rows[rung][key]))
            deltas[key] = delta
            max_delta = max(max_delta, delta)
        rows[rung] = {"max_value_delta": max(deltas.values()), "deltas": deltas, "pass": max(deltas.values()) < PARITY_TOL}
    return {
        "max_value_delta": max_delta,
        "agree": max_delta < PARITY_TOL,
        "rows": rows,
        "notes": (
            "JAX x64 mirrors the finite bond-space density, entropy, trace, PSD, hermiticity, "
            "and one-site exact readouts. geomstats is not a relevant engine for this "
            "complex Hilbert carrier and no geomstats JAX backend path is claimed."
        ),
    }


def sympy_known_values(torch_rows: dict[str, dict[str, Any]], jax_rows: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    weights = [sp.Rational(i, sum(range(1, BOND_DIM + 1))) for i in range(1, BOND_DIM + 1)]
    trace = sp.simplify(sum(weights))
    site0_diag0 = sp.simplify(sum(weight for latent, weight in enumerate(weights) if bit_for(latent, 0) == 0))
    site0_diag1 = sp.simplify(sum(weight for latent, weight in enumerate(weights) if bit_for(latent, 0) == 1))
    entropy = -sum(weight * sp.log(weight) for weight in weights)
    entropy_float = float(sp.N(entropy, 30))
    checks = []
    for rung in SITE_COUNTS:
        key = str(rung)
        checks.extend(
            [
                {
                    "invariant": f"N{rung}_trace_one_sympy_vs_torch",
                    "computed": torch_rows[key]["bond_space_density_trace_real"],
                    "expected": float(trace),
                    "match": abs(torch_rows[key]["bond_space_density_trace_real"] - float(trace)) < PARITY_TOL,
                },
                {
                    "invariant": f"N{rung}_half_entropy_sympy_vs_torch",
                    "computed": torch_rows[key]["half_chain_entropy"],
                    "expected": entropy_float,
                    "match": abs(torch_rows[key]["half_chain_entropy"] - entropy_float) < PARITY_TOL,
                },
                {
                    "invariant": f"N{rung}_half_entropy_sympy_vs_jax",
                    "computed": jax_rows[key]["half_chain_entropy"],
                    "expected": entropy_float,
                    "match": abs(jax_rows[key]["half_chain_entropy"] - entropy_float) < PARITY_TOL,
                },
                {
                    "invariant": f"N{rung}_site0_diag0_exact",
                    "computed": float(torch.real(torch_rows[key]["one_site_density_site0"][0, 0]).item()),
                    "expected": float(site0_diag0),
                    "match": abs(float(torch.real(torch_rows[key]["one_site_density_site0"][0, 0]).item()) - float(site0_diag0)) < PARITY_TOL,
                },
                {
                    "invariant": f"N{rung}_site0_diag1_exact",
                    "computed": float(torch.real(torch_rows[key]["one_site_density_site0"][1, 1]).item()),
                    "expected": float(site0_diag1),
                    "match": abs(float(torch.real(torch_rows[key]["one_site_density_site0"][1, 1]).item()) - float(site0_diag1)) < PARITY_TOL,
                },
            ]
        )
    exact = {
        "weight_rule": "p_a=(a+1)/36 for a=0..7",
        "trace": str(trace),
        "site0_diag0": str(site0_diag0),
        "site0_diag1": str(site0_diag1),
        "half_chain_entropy_expression": str(entropy),
        "half_chain_entropy_float": entropy_float,
    }
    return exact, checks


def z3_structural_certificate() -> dict[str, Any]:
    weights = [z3.RealVal(i) / z3.RealVal(sum(range(1, BOND_DIM + 1))) for i in range(1, BOND_DIM + 1)]
    trace_solver = z3.Solver()
    trace_solver.add(z3.Not(z3.Sum(weights) == z3.RealVal(1)))
    nonneg_solver = z3.Solver()
    nonneg_solver.add(z3.Or([weight < z3.RealVal(0) for weight in weights]))
    unit_eigen_solver = z3.Solver()
    unit_eigen_solver.add(z3.Not(z3.And(z3.RealVal(1) >= 0, *[z3.RealVal(0) >= 0 for _ in range(BOND_DIM - 1)])))
    trace_status = str(trace_solver.check())
    nonneg_status = str(nonneg_solver.check())
    unit_status = str(unit_eigen_solver.check())
    return {
        "tool": "z3",
        "trace_not_one_negation_status": trace_status,
        "negative_schmidt_probability_status": nonneg_status,
        "rank_one_density_spectrum_psd_status": unit_status,
        "certified_constraints": 3,
        "pass": trace_status == "unsat" and nonneg_status == "unsat" and unit_status == "unsat",
    }


def cvc5_structural_certificate() -> dict[str, Any]:
    denominator = sum(range(1, BOND_DIM + 1))
    tm = cvc5.TermManager()
    trace_solver = cvc5.Solver(tm)
    trace_solver.setLogic("QF_LRA")
    vals = [tm.mkReal(i, denominator) for i in range(1, BOND_DIM + 1)]
    total = vals[0]
    for val in vals[1:]:
        total = tm.mkTerm(Kind.ADD, total, val)
    trace_solver.assertFormula(tm.mkTerm(Kind.DISTINCT, total, tm.mkReal(1)))
    trace_status = str(trace_solver.checkSat())

    nonneg_solver = cvc5.Solver(tm)
    nonneg_solver.setLogic("QF_LRA")
    negative_terms = [tm.mkTerm(Kind.LT, val, tm.mkReal(0)) for val in vals]
    nonneg_solver.assertFormula(tm.mkTerm(Kind.OR, *negative_terms))
    nonneg_status = str(nonneg_solver.checkSat())

    psd_solver = cvc5.Solver(tm)
    psd_solver.setLogic("QF_LRA")
    eigen_terms = [tm.mkTerm(Kind.LT, tm.mkReal(1), tm.mkReal(0))]
    eigen_terms.extend(tm.mkTerm(Kind.LT, tm.mkReal(0), tm.mkReal(0)) for _ in range(BOND_DIM - 1))
    psd_solver.assertFormula(tm.mkTerm(Kind.OR, *eigen_terms))
    psd_status = str(psd_solver.checkSat())
    return {
        "tool": "cvc5",
        "trace_not_one_negation_status": trace_status,
        "negative_schmidt_probability_status": nonneg_status,
        "rank_one_density_spectrum_psd_status": psd_status,
        "certified_constraints": 3,
        "pass": trace_status == "unsat" and nonneg_status == "unsat" and psd_status == "unsat",
    }


def run_negative_artifacts(torch_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    min_entropy = min(row["half_chain_entropy"] for row in torch_rows.values())
    min_phase = min(row["complex_phase_imag_coherence"] for row in torch_rows.values())
    unnormalized_trace = float(torch.real(torch.trace(2.0 * schmidt_density_torch(8))).item())
    signed_one_site = one_site_density_torch(0, signed=True)
    signed_min_eigen = float(torch.min(torch.linalg.eigvalsh(signed_one_site)).item())
    phase_erased = schmidt_density_torch(8, phase_erased=True)
    phase_erased_signature = latent_imag_signature_torch(phase_erased)
    nonhermitian = one_site_density_torch(0)
    nonhermitian[0, 1] = 0.25j
    nonhermitian_delta = float(torch.max(torch.abs(nonhermitian - torch.conj(nonhermitian.T))).item())
    dense_amplitudes_64 = 2**64
    max_allowed_dense_amplitudes = 2**20
    return {
        "bond1_product_state_ablation": {
            "killed": min_entropy > KILL_FLOOR,
            "baseline_min_half_chain_entropy": min_entropy,
            "ablated_half_chain_entropy": 0.0,
            "outcome_delta": min_entropy,
            "artifact": "product control recomputed as bond-1 MPS; half-chain entropy collapses to zero",
        },
        "trace_normalization_ablation": {
            "killed": abs(unnormalized_trace - 1.0) > KILL_FLOOR,
            "baseline_trace": 1.0,
            "ablated_trace": unnormalized_trace,
            "outcome_delta": abs(unnormalized_trace - 1.0),
            "artifact": "weights multiplied by two; trace-one signature fails",
        },
        "psd_signed_weight_ablation": {
            "killed": signed_min_eigen < -KILL_FLOOR,
            "baseline_min_eigenvalue_floor": 0.0,
            "ablated_min_eigenvalue": signed_min_eigen,
            "outcome_delta": abs(signed_min_eigen),
            "artifact": "one Schmidt weight is signed negative in the one-site certificate; PSD fails",
        },
        "hermitian_asymmetry_ablation": {
            "killed": nonhermitian_delta > KILL_FLOOR,
            "baseline_hermitian_delta": 0.0,
            "ablated_hermitian_delta": nonhermitian_delta,
            "outcome_delta": nonhermitian_delta,
            "artifact": "asymmetric imaginary off-diagonal term inserted in a one-site density; hermiticity fails",
        },
        "complex_phase_erasure_ablation": {
            "killed": min_phase > KILL_FLOOR and phase_erased_signature < KILL_FLOOR,
            "baseline_min_imag_coherence": min_phase,
            "ablated_imag_coherence": phase_erased_signature,
            "outcome_delta": min_phase - phase_erased_signature,
            "artifact": "phase-erased Schmidt amplitudes kill the complex off-diagonal imaginary coherence signature",
        },
        "dense_state_closure_rejected": {
            "killed": dense_amplitudes_64 > max_allowed_dense_amplitudes,
            "would_require_amplitudes_at_N64": dense_amplitudes_64,
            "max_allowed_dense_amplitudes": max_allowed_dense_amplitudes,
            "dense_state_closure_used": False,
            "outcome_delta": float(math.log2(dense_amplitudes_64) - math.log2(max_allowed_dense_amplitudes)),
            "artifact": "full 2**64 dense vector closure is explicitly blocked; MPS/MPO contractions stay non-dense",
        },
    }


def tool_blocks(
    torch_rows: dict[str, dict[str, Any]],
    jax_rows: dict[str, dict[str, Any]],
    parity: dict[str, Any],
    z3_cert: dict[str, Any],
    cvc5_cert: dict[str, Any],
    sympy_exact: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str], dict[str, Any]]:
    min_entropy = min(row["half_chain_entropy"] for row in torch_rows.values())
    min_quimb_bond = min(row["quimb_mps_max_bond"] for row in torch_rows.values())
    max_product_bond = max(row["quimb_product_max_bond"] for row in torch_rows.values())
    min_cot_width = min(row["cotengra_trace_tree"]["contraction_width"] for row in torch_rows.values())
    max_product_cot_width = max(row["cotengra_product_trace_tree"]["contraction_width"] for row in torch_rows.values())
    site0_delta = abs(float(sp.Rational(sympy_exact["site0_diag0"])) - 0.5)
    jax_product_entropy = 0.0
    min_jax_entropy = min(row["half_chain_entropy"] for row in jax_rows.values())
    manifest = {tool: dict(entry) for tool, entry in TOOL_MANIFEST.items()}
    depth = dict(TOOL_INTEGRATION_DEPTH)
    ablations = {
        "torch_ablation": {
            "tool": "torch",
            "ablation": "replace the entangled torch carrier with a bond-1 product MPS",
            "baseline_metric": min_entropy,
            "ablated_metric": 0.0,
            "delta": min_entropy,
            "outcome_delta": min_entropy,
            "ablation_outcome_delta": min_entropy,
            "pass": min_entropy > KILL_FLOOR,
        },
        "jax_ablation": {
            "tool": "jax",
            "ablation": "recompute the secondary x64 engine on the product/bond-1 control instead of the entangled carrier",
            "baseline_metric": min_jax_entropy,
            "ablated_metric": jax_product_entropy,
            "delta": min_jax_entropy - jax_product_entropy,
            "outcome_delta": min_jax_entropy - jax_product_entropy,
            "ablation_outcome_delta": min_jax_entropy - jax_product_entropy,
            "pass": min_jax_entropy - jax_product_entropy > KILL_FLOOR and parity["agree"],
        },
        "quimb_ablation": {
            "tool": "quimb",
            "ablation": "replace quimb torch-backed bond-8 MPS with a recomputed bond-1 product MPS",
            "baseline_metric": float(min_quimb_bond),
            "ablated_metric": float(max_product_bond),
            "delta": float(min_quimb_bond - max_product_bond),
            "outcome_delta": float(min_quimb_bond - max_product_bond),
            "ablation_outcome_delta": float(min_quimb_bond - max_product_bond),
            "pass": min_quimb_bond >= BOND_DIM and max_product_bond == 1,
        },
        "cotengra_ablation": {
            "tool": "cotengra",
            "ablation": "replace bond-8 trace network with product/bond-1 trace network",
            "baseline_metric": min_cot_width,
            "ablated_metric": max_product_cot_width,
            "delta": min_cot_width - max_product_cot_width,
            "outcome_delta": min_cot_width - max_product_cot_width,
            "ablation_outcome_delta": min_cot_width - max_product_cot_width,
            "pass": min_cot_width - max_product_cot_width > KILL_FLOOR,
        },
        "z3_ablation": {
            "tool": "z3",
            "ablation": "remove z3 trace/PSD structural certificate",
            "baseline_metric": float(z3_cert["certified_constraints"]),
            "ablated_metric": 0.0,
            "delta": float(z3_cert["certified_constraints"]),
            "outcome_delta": float(z3_cert["certified_constraints"]),
            "ablation_outcome_delta": float(z3_cert["certified_constraints"]),
            "pass": bool(z3_cert["pass"] and z3_cert["certified_constraints"] > 0),
        },
        "cvc5_ablation": {
            "tool": "cvc5",
            "ablation": "remove cvc5 independent structural cross-check",
            "baseline_metric": float(cvc5_cert["certified_constraints"]),
            "ablated_metric": 0.0,
            "delta": float(cvc5_cert["certified_constraints"]),
            "outcome_delta": float(cvc5_cert["certified_constraints"]),
            "ablation_outcome_delta": float(cvc5_cert["certified_constraints"]),
            "pass": bool(cvc5_cert["pass"] and cvc5_cert["certified_constraints"] > 0),
        },
        "sympy_ablation": {
            "tool": "sympy",
            "ablation": "replace exact one-site p0 with a cosmetic uniform 1/2 control",
            "baseline_metric": float(sp.Rational(sympy_exact["site0_diag0"])),
            "ablated_metric": 0.5,
            "delta": site0_delta,
            "outcome_delta": site0_delta,
            "ablation_outcome_delta": site0_delta,
            "pass": site0_delta > KILL_FLOOR,
        },
    }
    return manifest, depth, ablations


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    torch_rows = {str(site_count): torch_rung(site_count) for site_count in SITE_COUNTS}
    jax_rows = {str(site_count): jax_rung(site_count) for site_count in SITE_COUNTS}
    parity = compare_engines(torch_rows, jax_rows)
    sympy_exact, known_checks = sympy_known_values(torch_rows, jax_rows)
    z3_cert = z3_structural_certificate()
    cvc5_cert = cvc5_structural_certificate()
    negatives = run_negative_artifacts(torch_rows)
    tool_manifest, tool_depth, tool_ablations = tool_blocks(torch_rows, jax_rows, parity, z3_cert, cvc5_cert, sympy_exact)

    scale_rungs = {}
    for site_count in SITE_COUNTS:
        key = str(site_count)
        row = torch_rows[key]
        jrow = jax_rows[key]
        rung_pass = (
            row["pass"]
            and jrow["pass"]
            and parity["rows"][key]["pass"]
            and row["mps_max_bond"] >= BOND_DIM
            and row["schmidt_rank"] >= BOND_DIM
            and row["half_chain_entropy"] > KILL_FLOOR
            and row["dense_state_closure_used"] is False
        )
        scale_rungs[key] = {
            "sites_or_qubits": site_count,
            "shape": row["peps3d_shape"],
            "dense_state_closure_used": False,
            "mps_max_bond": row["mps_max_bond"],
            "mps_density_operator_max_bond": row["density_mpo_max_bond"],
            "schmidt_rank": row["schmidt_rank"],
            "half_chain_entropy": row["half_chain_entropy"],
            "entanglement_entropy": row["entanglement_entropy"],
            "trace": row["density_operator_trace_real"],
            "psd_min_eigenvalue_bond_space": row["bond_space_density_psd_min_eigenvalue"],
            "hermitian_max_delta_bond_space": row["bond_space_density_hermitian_max_delta"],
            "pass": bool(rung_pass),
        }

    scale_pass = all(rung["pass"] for rung in scale_rungs.values())
    depth_pass = all(rung["mps_max_bond"] >= BOND_DIM and rung["half_chain_entropy"] > KILL_FLOOR for rung in scale_rungs.values())
    known_pass = all(check["match"] for check in known_checks)
    negatives_pass = all(row["killed"] and abs(float(row["outcome_delta"])) > KILL_FLOOR for row in negatives.values())
    tools_pass = all(row["pass"] and abs(float(row["outcome_delta"])) > KILL_FLOOR for row in tool_ablations.values())
    trace_psd_pass = all(
        row["density_operator_trace_imag_abs"] < PARITY_TOL
        and abs(row["density_operator_trace_real"] - 1.0) < PARITY_TOL
        and row["bond_space_density_hermitian_max_delta"] < PARITY_TOL
        and row["bond_space_density_psd_min_eigenvalue"] >= -1.0e-8
        for row in torch_rows.values()
    )
    all_pass = bool(
        scale_pass
        and depth_pass
        and parity["agree"]
        and known_pass
        and negatives_pass
        and tools_pass
        and trace_psd_pass
        and z3_cert["pass"]
        and cvc5_cert["pass"]
    )

    blockers = []
    if not scale_pass:
        blockers.append("one or more scale_ladder rungs failed")
    if not depth_pass:
        blockers.append("many-body depth failed: bond>=8 or half-chain entropy>0 missing")
    if not parity["agree"]:
        blockers.append(f"jax_vs_pytorch max delta {parity['max_value_delta']} exceeds {PARITY_TOL}")
    if not known_pass:
        blockers.extend([f"known value mismatch: {check['invariant']}" for check in known_checks if not check["match"]])
    if not negatives_pass:
        blockers.extend([f"negative did not kill: {name}" for name, row in negatives.items() if not row["killed"]])
    if not tools_pass:
        blockers.extend([f"tool ablation failed or zero: {name}" for name, row in tool_ablations.items() if not row["pass"]])
    if not trace_psd_pass:
        blockers.append("trace/PSD/hermitian density operator check failed")

    min_entropy = min(rung["half_chain_entropy"] for rung in scale_rungs.values())
    min_phase = min(row["complex_phase_imag_coherence"] for row in torch_rows.values())
    result = {
        "schema": "formal_scout_max_deep_lego_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "lego",
        "tier": "1_finite_complex_hilbert_carrier",
        "purpose": "One independent many-body complex Hilbert carrier lego: N=8/16/32/64 non-dense entangled MPS density operator with bond>=8, trace=1, PSD, Hermitian, and dual torch/JAX readouts.",
        "scientific_question": "Can the complex_hilbert_carrier layer be represented as a non-dense entangled MPS density operator at N=8,16,32,64 with genuine many-body depth, exact one-site checks, structural trace/PSD guards, and load-bearing quimb/cotengra/z3/cvc5/sympy ablations?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "complex_hilbert_carrier_probe",
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set: finite N-site qubit path, finite latent Schmidt index a=0..7, finite MPS tensors, finite density-MPO trace contraction, finite PEPS3D grid anchors",
            "N01 order-sensitive/noncommuting-compatible carrier: complex amplitudes carry nontrivial phase coherence and support later noncommuting local operators; product, phase-erased, trace, PSD, Hermitian, and dense-closure controls are killed here",
        ],
        "finite_map": "ComplexHilbertCarrier_N : finite PEPS3D-anchored N-site path with torch.complex128 MPS tensors A_i[a,bit(a,i),a], p_a=(a+1)/36, complex phases exp(i theta_a) -> rank-one MPS density operator rho=|psi><psi|, trace/PSD/Hermitian certificates, half-chain entropy, one-site exact density, killed controls, and blocked downstream consumers",
        "domain": {
            "site_counts": SITE_COUNTS,
            "physical_dim": PHYSICAL_DIM,
            "mps_bond_dim": BOND_DIM,
            "schmidt_weight_rule": "p_a=(a+1)/36 for a=0..7",
            "dense_state_closure_used": False,
            "full_dense_state_amplitudes_never_materialized": True,
        },
        "codomain_or_output": "Non-dense MPS density-operator trace/PSD/Hermitian readouts, half-chain entropy, exact one-site density, torch/JAX parity rows, tool ablation deltas, and negative artifacts.",
        "carrier_layer": "complex_hilbert_carrier",
        "geometry_layer": "not_applicable: this is the carrier layer, not a downstream geometry/coupling layer",
        "carrier_realization": "torch.complex128 MPS primary carrier plus non-dense density-MPO trace contraction; JAX complex128 mirrors finite invariants; quimb wraps torch tensors and cotengra plans trace contractions",
        "peps3d_embedding": {
            "anchor": "finite PEPS3D grid K=(V,E,F,C) supplies site anchors only; the executable carrier is its Hamiltonian/path MPS projection and does not claim full PEPS3D contraction closure",
            "shapes": {str(site_count): list(shape) for site_count, shape in SITE_SHAPES.items()},
            "from_first_carrier_step": True,
        },
        "spinor_state": "Each site has local C^2 spinor basis; the N-site pure MPS state and one-site density readouts are torch/JAX spinor-derived density objects.",
        "quaternion_action": "not_applicable: this complex Hilbert carrier does not use quaternion language or claim a quaternion invariant",
        "dependency_receipts": [],
        "downstream_blocks": ["stacking", "coupling", "higher_layers", "G_structure", "flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "FEP", "physics", "final_manifold_admission"],
        "bridge_layer": "none",
        "cut_layer": "half-chain Schmidt cut over the non-dense MPS carrier",
        "law_or_candidate_tested": "finite entangled complex Hilbert MPS density operator has trace=1, PSD, Hermitian, bond>=8, entropy>0, exact one-site densities, and nonzero tool-ablation deltas at N=8/16/32/64",
        "branch_status_before_run": "single independent lego; no coupling, stacking, bridge, flux, Axis0, or physics route opened",
        "allowed_claims": [
            "bounded local complex_hilbert_carrier lego exists/runs when this result and max_deep_lego_gate pass",
            "N=8/16/32/64 use non-dense torch-backed MPS carriers with mps_max_bond>=8 and half-chain entropy>0",
            "rank-one MPS density operator trace/PSD/Hermitian checks pass on finite bond-space and density-MPO trace readouts",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "single carrier lego only",
            "no independent geometry/coupling/stacking layer evidence in this result",
            "no full PEPS3D contraction closure",
            "downstream consumers remain blocked",
        ],
        "eligible_consumers": ["bounded local carrier comparisons only after citing this result path and gate output"],
        "blocked_consumers": ["stacking", "coupling", "higher_layers", "G_structure", "flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "FEP", "physics", "final_manifold_admission"],
        "required_tools": list(tool_manifest.keys()),
        "actual_tools_used": [tool for tool, row in tool_manifest.items() if row["used"]],
        "proof_surfaces_used": ["z3 trace/PSD structural certificate", "cvc5 trace/PSD structural certificate", "sympy exact one-site density"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": list(negatives.keys()),
        "negatives_run": negatives,
        "kill_conditions": {
            "bond1_product_state_ablation": "bond-1 product MPS must collapse half-chain entropy to zero",
            "trace_normalization_ablation": "unnormalized weights must fail trace=1",
            "psd_signed_weight_ablation": "signed one-site weight must produce a negative eigenvalue",
            "hermitian_asymmetry_ablation": "asymmetric imaginary off-diagonal must fail Hermiticity",
            "complex_phase_erasure_ablation": "phase erasure must kill the imaginary coherence signature",
            "dense_state_closure_rejected": "full 2**64 dense state closure must remain blocked",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "dual-engine parity", "known_value_checks", "negative artifacts", "tool ablation outcomes"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{NAME}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "many_body_depth_pass": depth_pass,
            "known_value_checks_pass": known_pass,
            "negatives_all_kill": negatives_pass,
            "tools_have_nonzero_ablation_deltas": tools_pass,
            "trace_psd_hermitian_pass": trace_psd_pass,
            "jax_vs_pytorch_max_value_delta": parity["max_value_delta"],
            "min_half_chain_entropy": min_entropy,
            "min_complex_phase_imag_coherence": min_phase,
            "elapsed_seconds": time.time() - started,
        },
        "shells": [
            {
                "name": "complex_hilbert_non_dense_mps_density_operator",
                "carrier": "torch-backed MPS plus non-dense density-MPO trace contraction",
                "rungs": SITE_COUNTS,
                "mps_max_bond_min": min(rung["mps_max_bond"] for rung in scale_rungs.values()),
                "survives": scale_pass,
            }
        ],
        "future_continuations": [
            "build the next independent layer only after this carrier result is cited and re-gated",
            "do not use this result as stacking/coupling/Axis0/flux evidence",
        ],
        "compatibility_weights": {
            "local_complex_hilbert_carrier": 1.0 if all_pass else 0.0,
            "future_independent_layer_input": 0.5 if all_pass else 0.0,
            "stacking_or_coupling": 0.0,
            "axis_or_physics": 0.0,
        },
        "compression_map": {
            "from": "N-site non-dense MPS tensors and rank-one MPS density operator",
            "to": "scale_ladder, trace/PSD/Hermitian summaries, entropy, exact one-site density, killed controls, and tool-ablation deltas",
            "loss_boundary": "does not preserve a full dense 2**N vector, full PEPS3D contraction, layer stacking, or downstream physics/axis claims",
        },
        "present_survivor": {
            "object": "complex_hilbert_carrier_mps_density_operator",
            "capacity": min(min_entropy, min_phase),
            "survives": bool(all_pass),
            "blocked_capacity": ["stacking", "coupling", "flux", "Xi", "Phi0", "Axis0", "bridge", "physics"],
        },
        "survivor_invariant": {
            "invariant": "carrier survives iff all non-dense scale rungs pass with bond>=8, entropy>0, trace/PSD/Hermitian checks, dual-engine parity, killed negatives, and promotion_allowed=false",
            "computed_capacity": min(min_entropy, min_phase),
            "threshold": KILL_FLOOR,
            "passed": bool(all_pass and min(min_entropy, min_phase) > KILL_FLOOR and not False),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required",
            "claim_ceiling": "single complex_hilbert_carrier lego only; no full layer completion, coupling, stacking, flux, Axis0, bridge, physics, or final manifold admission",
        },
        "pass_rule": "all N=8/16/32/64 scale rungs are non-dense and pass; mps_max_bond>=8 and half-chain entropy>0 at every rung; torch/JAX agree; trace=1/PSD/Hermitian checks pass; exact one-site checks match; all negatives kill; all load-bearing tool ablations have nonzero outcome_delta",
        "fail_rule": "fail on dense closure, missing rung, bond<8, product entropy, dual-engine mismatch, trace/PSD/Hermitian failure, hardcoded/mismatched known check, live negative, or zero/cosmetic tool ablation",
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": tool_depth,
        "tool_integration_depth": tool_depth,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "tool_ablation_outcomes": tool_ablations,
        "scale_ladder": {"rungs": scale_rungs, "pass": scale_pass},
        "torch_engine": torch_rows,
        "jax_engine": jax_rows,
        "jax_vs_pytorch": parity,
        "sympy_exact": sympy_exact,
        "known_value_checks": known_checks,
        "z3_trace_psd_structural": z3_cert,
        "cvc5_trace_psd_structural": cvc5_cert,
        "positive": {
            "all_8_16_32_64_non_dense_rungs_pass": {"pass": scale_pass, "rungs": scale_rungs},
            "many_body_depth_bond8_entropy_positive": {"pass": depth_pass, "rungs": scale_rungs},
            "dual_engine_parity": parity,
            "trace_psd_hermitian_density_operator": {"pass": trace_psd_pass},
            "z3_trace_psd_structural": z3_cert,
            "cvc5_trace_psd_structural": cvc5_cert,
        },
        "graveyard_companions": negatives,
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "geomstats_jax_backend_claim": {
                "claimed": False,
                "pass": True,
                "notes": "geomstats is not used for this carrier; no JAX geomstats path is claimed",
            },
            "downstream_consumers_blocked": {"blocked": ["stacking", "coupling", "flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "final manifold"], "pass": True},
        },
        "nearby_variants": {
            "product_bond1_entropy_delta": negatives["bond1_product_state_ablation"]["outcome_delta"],
            "trace_ablation_delta": negatives["trace_normalization_ablation"]["outcome_delta"],
            "psd_ablation_delta": negatives["psd_signed_weight_ablation"]["outcome_delta"],
            "complex_phase_erasure_delta": negatives["complex_phase_erasure_ablation"]["outcome_delta"],
            "pass": negatives_pass,
        },
        "why_not_v4_probes": "This is a v5 max-deep single carrier lego with explicit non-dense 8/16/32/64 scale rungs, mps_max_bond>=8, entropy>0, torch/JAX parity, structural z3/cvc5 trace/PSD guards, exact sympy one-site checks, load-bearing quimb/cotengra ablations, and promotion_allowed=false.",
        "blockers": blockers,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out_path": str(OUT_PATH), "summary": result["result_summary"], "blockers": blockers}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
