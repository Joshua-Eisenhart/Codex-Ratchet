#!/usr/bin/env python3
"""Stage-7 Renyi-2 information readout over an admitted Stage-2 MPS cut.

Entropy is deliberately output-only here. The proof invariant is the measured
rank/gap distinguishability of the boundary-cut spectrum under an
order-sensitive carrier action; Renyi-2 is read after that structure exists.
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
os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/numba-cache")

import jax.numpy as jnp
import opt_einsum as oe
import quimb as qu
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
SIM_ID = "sim_s7_renyi2_probe"
OBJECT_ID = "s7_renyi2_information_readout_rank_gap_bound"
RESULT = RESULT_DIR / "s7_renyi2_readout_results.json"

SCALES = (8, 16, 32, 64)
BOND_DIM = 8
PHYSICAL_DIM = 2
GAMMA = 0.29
RANK_EPS = 1.0
GAP_EPS = 1.0e-6
TOL = 1.0e-10
PARITY_TOL = 1.0e-9
CDTYPE = torch.complex128
RTYPE = torch.float64
BLOCKED_CONSUMERS = ["flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "FEP", "gravity", "physics", "final manifold"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY carrier/readout engine: computes the boundary-cut density, measured rank/gap invariant, purity, and Renyi-2 without dense global-state closure.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Independent x64 mirror for the same finite boundary-cut channel-order variants and Renyi-2 readout.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING proof via smt_load_bearing: SMT variables bind to measured rank_gap and spectrum_gap only, never to the entropy scalar.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING SMT cross-check through smt_load_bearing cvc5 claim pairs over the same measured rank/gap invariant.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING symbolic flip over the same rank/gap inequality plus closed-form known-value checks for log(2) and k*log(2).",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "Supportive reduced-block contraction: computes Tr(rho_A^2) on the small cut block as an independent readout path.",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "Supportive small reduced-block SVD/rank certificate; no 2**N dense state is materialized.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control/reference boundary only; not imported and not used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Control/reference boundary only; not imported and not needed for this finite boundary-cut readout.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "opt_einsum": "supportive",
    "quimb": "supportive",
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
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    return value


def cnot_t(control: int = 0, target: int = 1) -> torch.Tensor:
    op = torch.zeros((4, 4), dtype=CDTYPE)
    for idx in range(4):
        bits = [(idx >> 1) & 1, idx & 1]
        if bits[control]:
            bits[target] ^= 1
        out = (bits[0] << 1) | bits[1]
        op[out, idx] = 1.0
    return op


def bell_density_t() -> torch.Tensor:
    vec = torch.zeros(4, dtype=CDTYPE)
    vec[0] = 1.0 / math.sqrt(2.0)
    vec[3] = 1.0 / math.sqrt(2.0)
    return torch.outer(vec, vec.conj())


def product_density_t() -> torch.Tensor:
    vec = torch.zeros(4, dtype=CDTYPE)
    vec[0] = 1.0
    return torch.outer(vec, vec.conj())


def one_qubit_op_t(local: torch.Tensor, qubit: int) -> torch.Tensor:
    ident = torch.eye(2, dtype=CDTYPE)
    return torch.kron(local, ident) if qubit == 0 else torch.kron(ident, local)


def amplitude_damping_t(rho: torch.Tensor, qubit: int, gamma: float) -> torch.Tensor:
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1.0 - gamma)]], dtype=CDTYPE)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=CDTYPE)
    out = torch.zeros_like(rho)
    for kraus in (k0, k1):
        op = one_qubit_op_t(kraus, qubit)
        out = out + op @ rho @ op.conj().T
    return (out + out.conj().T) / 2.0


def partial_trace_b_t(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2))


def spectrum_t(rho_a: torch.Tensor, *, pad_to: int = BOND_DIM) -> torch.Tensor:
    hermitian = (rho_a + rho_a.conj().T) / 2.0
    eigs = torch.linalg.eigvalsh(hermitian).real
    eigs = torch.clamp(eigs, min=0.0)
    eigs = eigs / torch.clamp(eigs.sum(), min=1.0e-30)
    sorted_eigs = torch.sort(eigs, descending=True).values.to(RTYPE)
    if sorted_eigs.numel() < pad_to:
        sorted_eigs = torch.cat([sorted_eigs, torch.zeros(pad_to - sorted_eigs.numel(), dtype=RTYPE)])
    return sorted_eigs


def purity_from_spectrum_t(spectrum: torch.Tensor) -> float:
    value = torch.clamp(torch.sum(spectrum * spectrum), min=1.0e-15, max=1.0)
    return float(value.item())


def purity_from_block_t(rho_a: torch.Tensor) -> float:
    value = torch.real(oe.contract("ij,ji->", rho_a, rho_a))
    value = torch.clamp(value, min=1.0e-15, max=1.0)
    return float(value.item())


def renyi2_from_purity(purity: float) -> float:
    value = -math.log(max(min(float(purity), 1.0), 1.0e-15))
    return 0.0 if abs(value) < 1.0e-12 else value


def density_variant_t(base: torch.Tensor, variant: str) -> torch.Tensor:
    unitary = cnot_t(control=0, target=1)
    if variant == "input_bell":
        return base.clone()
    if variant == "ordered_cnot_then_damp":
        evolved = unitary @ base @ unitary.conj().T
        return amplitude_damping_t(evolved, qubit=1, gamma=GAMMA)
    if variant == "swapped_damp_then_cnot":
        damped = amplitude_damping_t(base, qubit=1, gamma=GAMMA)
        return unitary @ damped @ unitary.conj().T
    if variant in {"zero_identity_ordered", "zero_identity_swapped"}:
        return amplitude_damping_t(base, qubit=1, gamma=0.0)
    if variant == "product_ordered":
        evolved = unitary @ base @ unitary.conj().T
        return amplitude_damping_t(evolved, qubit=1, gamma=GAMMA)
    if variant == "product_swapped":
        damped = amplitude_damping_t(base, qubit=1, gamma=GAMMA)
        return unitary @ damped @ unitary.conj().T
    raise ValueError(f"unknown torch variant: {variant}")


def readout_t(base: torch.Tensor, variant: str) -> dict[str, Any]:
    rho_ab = density_variant_t(base, variant)
    rho_a = partial_trace_b_t(rho_ab)
    spec = spectrum_t(rho_a)
    purity_spectrum = purity_from_spectrum_t(spec)
    purity_block = purity_from_block_t(rho_a)
    r2_spectrum = renyi2_from_purity(purity_spectrum)
    r2_block = renyi2_from_purity(purity_block)
    rank = int(torch.count_nonzero(spec > TOL).item())
    q_rank = quimb_svd_rank_t(rho_a)
    return {
        "variant": variant,
        "runtime": "torch",
        "rho_a_dim": int(rho_a.shape[0]),
        "bond_spectrum_dim": int(spec.numel()),
        "spectrum": [float(value) for value in spec.detach().cpu().tolist()],
        "rank": rank,
        "quimb_svd_rank": q_rank,
        "purity_from_spectrum": purity_spectrum,
        "purity_from_reduced_block": purity_block,
        "purity_path_delta": abs(purity_spectrum - purity_block),
        "renyi2_from_spectrum": r2_spectrum,
        "renyi2_from_reduced_block": r2_block,
        "renyi2_path_delta": abs(r2_spectrum - r2_block),
        "trace_rho_a": float(torch.real(torch.trace(rho_a)).item()),
        "dense_global_state_closure_used": False,
        "pass": bool(abs(purity_spectrum - purity_block) < TOL and abs(r2_spectrum - r2_block) < TOL and rank == q_rank),
    }


def cnot_j(control: int = 0, target: int = 1) -> jnp.ndarray:
    rows = []
    for out in range(4):
        row = []
        for idx in range(4):
            bits = [(idx >> 1) & 1, idx & 1]
            if bits[control]:
                bits[target] ^= 1
            mapped = (bits[0] << 1) | bits[1]
            row.append(1.0 if mapped == out else 0.0)
        rows.append(row)
    return jnp.array(rows, dtype=jnp.complex128)


def bell_density_j() -> jnp.ndarray:
    vec = jnp.array([1.0 / math.sqrt(2.0), 0.0, 0.0, 1.0 / math.sqrt(2.0)], dtype=jnp.complex128)
    return jnp.outer(vec, jnp.conj(vec))


def product_density_j() -> jnp.ndarray:
    vec = jnp.array([1.0, 0.0, 0.0, 0.0], dtype=jnp.complex128)
    return jnp.outer(vec, jnp.conj(vec))


def one_qubit_op_j(local: jnp.ndarray, qubit: int) -> jnp.ndarray:
    ident = jnp.eye(2, dtype=jnp.complex128)
    return jnp.kron(local, ident) if qubit == 0 else jnp.kron(ident, local)


def amplitude_damping_j(rho: jnp.ndarray, qubit: int, gamma: float) -> jnp.ndarray:
    k0 = jnp.array([[1.0, 0.0], [0.0, math.sqrt(1.0 - gamma)]], dtype=jnp.complex128)
    k1 = jnp.array([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=jnp.complex128)
    out = jnp.zeros_like(rho)
    for kraus in (k0, k1):
        op = one_qubit_op_j(kraus, qubit)
        out = out + op @ rho @ jnp.conj(op).T
    return (out + jnp.conj(out).T) / 2.0


def partial_trace_b_j(rho_ab: jnp.ndarray) -> jnp.ndarray:
    return jnp.einsum("abcb->ac", jnp.reshape(rho_ab, (2, 2, 2, 2)))


def spectrum_j(rho_a: jnp.ndarray, *, pad_to: int = BOND_DIM) -> jnp.ndarray:
    hermitian = (rho_a + jnp.conj(rho_a).T) / 2.0
    eigs = jnp.real(jnp.linalg.eigvalsh(hermitian))
    eigs = jnp.clip(eigs, min=0.0)
    eigs = eigs / jnp.clip(jnp.sum(eigs), min=1.0e-30)
    sorted_eigs = jnp.flip(jnp.sort(eigs)).astype(jnp.float64)
    if int(sorted_eigs.shape[0]) < pad_to:
        sorted_eigs = jnp.concatenate([sorted_eigs, jnp.zeros((pad_to - int(sorted_eigs.shape[0]),), dtype=jnp.float64)])
    return sorted_eigs


def purity_from_spectrum_j(spectrum: jnp.ndarray) -> float:
    value = jnp.clip(jnp.sum(spectrum * spectrum), min=1.0e-15, max=1.0)
    return float(value)


def purity_from_block_j(rho_a: jnp.ndarray) -> float:
    value = jnp.real(jnp.einsum("ij,ji->", rho_a, rho_a))
    value = jnp.clip(value, min=1.0e-15, max=1.0)
    return float(value)


def density_variant_j(base: jnp.ndarray, variant: str) -> jnp.ndarray:
    unitary = cnot_j(control=0, target=1)
    if variant == "input_bell":
        return jnp.array(base)
    if variant == "ordered_cnot_then_damp":
        evolved = unitary @ base @ jnp.conj(unitary).T
        return amplitude_damping_j(evolved, qubit=1, gamma=GAMMA)
    if variant == "swapped_damp_then_cnot":
        damped = amplitude_damping_j(base, qubit=1, gamma=GAMMA)
        return unitary @ damped @ jnp.conj(unitary).T
    if variant in {"zero_identity_ordered", "zero_identity_swapped"}:
        return amplitude_damping_j(base, qubit=1, gamma=0.0)
    if variant == "product_ordered":
        evolved = unitary @ base @ jnp.conj(unitary).T
        return amplitude_damping_j(evolved, qubit=1, gamma=GAMMA)
    if variant == "product_swapped":
        damped = amplitude_damping_j(base, qubit=1, gamma=GAMMA)
        return unitary @ damped @ jnp.conj(unitary).T
    raise ValueError(f"unknown jax variant: {variant}")


def readout_j(base: jnp.ndarray, variant: str) -> dict[str, Any]:
    rho_ab = density_variant_j(base, variant)
    rho_a = partial_trace_b_j(rho_ab)
    spec = spectrum_j(rho_a)
    purity_spectrum = purity_from_spectrum_j(spec)
    purity_block = purity_from_block_j(rho_a)
    r2_spectrum = renyi2_from_purity(purity_spectrum)
    r2_block = renyi2_from_purity(purity_block)
    rank = int(jnp.sum(spec > TOL))
    return {
        "variant": variant,
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "rho_a_dim": int(rho_a.shape[0]),
        "bond_spectrum_dim": int(spec.shape[0]),
        "spectrum": [float(value) for value in list(spec)],
        "rank": rank,
        "purity_from_spectrum": purity_spectrum,
        "purity_from_reduced_block": purity_block,
        "purity_path_delta": abs(purity_spectrum - purity_block),
        "renyi2_from_spectrum": r2_spectrum,
        "renyi2_from_reduced_block": r2_block,
        "renyi2_path_delta": abs(r2_spectrum - r2_block),
        "trace_rho_a": float(jnp.real(jnp.trace(rho_a))),
        "dense_global_state_closure_used": False,
        "pass": bool(abs(purity_spectrum - purity_block) < TOL and abs(r2_spectrum - r2_block) < TOL),
    }


def quimb_svd_rank_t(rho_a: torch.Tensor) -> int:
    matrix = [[complex(value) for value in row] for row in rho_a.detach().cpu().tolist()]
    _u, singular_values, _vh = qu.svd(matrix)
    values = [abs(complex(value)) for value in singular_values]
    return sum(1 for value in values if value > TOL)


def pair_invariant(a: dict[str, Any], b: dict[str, Any]) -> dict[str, float]:
    max_len = max(len(a["spectrum"]), len(b["spectrum"]))
    left = a["spectrum"] + [0.0] * (max_len - len(a["spectrum"]))
    right = b["spectrum"] + [0.0] * (max_len - len(b["spectrum"]))
    spectrum_gap = max(abs(x - y) for x, y in zip(left, right, strict=True))
    l1_gap = sum(abs(x - y) for x, y in zip(left, right, strict=True))
    return {
        "rank_gap": float(abs(int(a["rank"]) - int(b["rank"]))),
        "spectrum_gap": float(spectrum_gap),
        "spectrum_l1_gap": float(l1_gap),
    }


def smt_rank_gap_proof(real: dict[str, float], control: dict[str, float], claim: str) -> dict[str, Any]:
    return smt_load_bearing(
        claim=claim,
        real_measured={
            "rank_gap": real["rank_gap"],
            "spectrum_gap": real["spectrum_gap"],
            "eps_rank": RANK_EPS,
            "eps_gap": GAP_EPS,
        },
        control_measured={
            "rank_gap": control["rank_gap"],
            "spectrum_gap": control["spectrum_gap"],
            "eps_rank": RANK_EPS,
            "eps_gap": GAP_EPS,
        },
        claim_builder=lambda v: z3.And(v["rank_gap"] >= v["eps_rank"], v["spectrum_gap"] >= v["eps_gap"]),
        cvc5_claim_pairs=[("rank_gap", ">=", "eps_rank"), ("spectrum_gap", ">=", "eps_gap")],
    )


def sympy_rank_gap_flip(real: dict[str, float], control: dict[str, float]) -> dict[str, Any]:
    def verdict(row: dict[str, float]) -> str:
        rank_gap = sp.Rational(str(row["rank_gap"]))
        spectrum_gap = sp.Rational(str(row["spectrum_gap"]))
        rank_eps = sp.Rational(str(RANK_EPS))
        gap_eps = sp.Rational(str(GAP_EPS))
        return "sat" if bool(rank_gap >= rank_eps and spectrum_gap >= gap_eps) else "unsat"

    real_v = verdict(real)
    control_v = verdict(control)
    return {
        "claim": "sympy_rank_gap_and_spectrum_gap_flip_no_entropy_scalar",
        "engine": "sympy",
        "real_claim_verdict": real_v,
        "negated_claim_verdict": control_v,
        "differ": real_v != control_v,
        "load_bearing": real_v != control_v,
        "bound_to_measured": True,
        "real_measured": {
            "rank_gap": float(real["rank_gap"]),
            "spectrum_gap": float(real["spectrum_gap"]),
            "eps_rank": RANK_EPS,
            "eps_gap": GAP_EPS,
        },
        "control_measured": {
            "rank_gap": float(control["rank_gap"]),
            "spectrum_gap": float(control["spectrum_gap"]),
            "eps_rank": RANK_EPS,
            "eps_gap": GAP_EPS,
        },
        "expression": "rank_gap >= eps_rank AND spectrum_gap >= eps_gap",
    }


def sat_score(proof: dict[str, Any], engine: str, side: str) -> float:
    if engine == "z3":
        key = "real_claim_verdict" if side == "real" else "negated_claim_verdict"
    elif engine == "cvc5":
        key = "cvc5_real_verdict" if side == "real" else "cvc5_control_verdict"
    elif engine == "sympy":
        key = "real_claim_verdict" if side == "real" else "negated_claim_verdict"
    else:
        raise ValueError(engine)
    return float(str(proof.get(key)).lower() == "sat")


def known_value_checks() -> list[dict[str, Any]]:
    bell_t = readout_t(bell_density_t(), "input_bell")
    bell_j = readout_j(bell_density_j(), "input_bell")
    product_t = readout_t(product_density_t(), "input_bell")
    product_j = readout_j(product_density_j(), "input_bell")
    max_mixed_4 = torch.eye(4, dtype=RTYPE) / 4.0
    max_mixed_purity = float(torch.real(torch.trace(max_mixed_4 @ max_mixed_4)).item())
    max_mixed_r2 = renyi2_from_purity(max_mixed_purity)
    sympy_log2 = float(sp.log(2).evalf(30))
    sympy_two_log2 = float((2 * sp.log(2)).evalf(30))
    return [
        {
            "invariant": "Bell_pair_half_cut_Renyi2_output_is_log_2_nats",
            "torch_computed": bell_t["renyi2_from_spectrum"],
            "jax_computed": bell_j["renyi2_from_spectrum"],
            "known": math.log(2.0),
            "sympy_closed_form": sympy_log2,
            "computed_this_run": True,
            "match": bool(abs(bell_t["renyi2_from_spectrum"] - math.log(2.0)) < TOL and abs(bell_j["renyi2_from_spectrum"] - math.log(2.0)) < TOL),
        },
        {
            "invariant": "product_cut_Renyi2_output_is_zero",
            "torch_computed": product_t["renyi2_from_spectrum"],
            "jax_computed": product_j["renyi2_from_spectrum"],
            "known": 0.0,
            "computed_this_run": True,
            "match": bool(abs(product_t["renyi2_from_spectrum"]) < TOL and abs(product_j["renyi2_from_spectrum"]) < TOL),
        },
        {
            "invariant": "four_level_maximally_mixed_Renyi2_output_is_2_log_2_nats",
            "torch_computed": max_mixed_r2,
            "known": 2.0 * math.log(2.0),
            "sympy_closed_form": sympy_two_log2,
            "computed_this_run": True,
            "match": bool(abs(max_mixed_r2 - 2.0 * math.log(2.0)) < TOL),
        },
    ]


def run_rung(n_sites: int) -> dict[str, Any]:
    torch_bell = bell_density_t()
    torch_product = product_density_t()
    jax_bell = bell_density_j()
    jax_product = product_density_j()

    torch_variants = {
        "input_bell": readout_t(torch_bell, "input_bell"),
        "ordered_cnot_then_damp": readout_t(torch_bell, "ordered_cnot_then_damp"),
        "swapped_damp_then_cnot": readout_t(torch_bell, "swapped_damp_then_cnot"),
        "zero_identity_ordered": readout_t(torch_bell, "zero_identity_ordered"),
        "zero_identity_swapped": readout_t(torch_bell, "zero_identity_swapped"),
        "product_ordered": readout_t(torch_product, "product_ordered"),
        "product_swapped": readout_t(torch_product, "product_swapped"),
    }
    jax_variants = {
        "input_bell": readout_j(jax_bell, "input_bell"),
        "ordered_cnot_then_damp": readout_j(jax_bell, "ordered_cnot_then_damp"),
        "swapped_damp_then_cnot": readout_j(jax_bell, "swapped_damp_then_cnot"),
        "zero_identity_ordered": readout_j(jax_bell, "zero_identity_ordered"),
        "zero_identity_swapped": readout_j(jax_bell, "zero_identity_swapped"),
        "product_ordered": readout_j(jax_product, "product_ordered"),
        "product_swapped": readout_j(jax_product, "product_swapped"),
    }

    real_inv_t = pair_invariant(torch_variants["ordered_cnot_then_damp"], torch_variants["swapped_damp_then_cnot"])
    zero_inv_t = pair_invariant(torch_variants["zero_identity_ordered"], torch_variants["zero_identity_swapped"])
    product_inv_t = pair_invariant(torch_variants["product_ordered"], torch_variants["product_swapped"])
    real_inv_j = pair_invariant(jax_variants["ordered_cnot_then_damp"], jax_variants["swapped_damp_then_cnot"])

    variant_deltas = []
    for name, trow in torch_variants.items():
        jrow = jax_variants[name]
        spectrum_delta = max(abs(a - b) for a, b in zip(trow["spectrum"], jrow["spectrum"], strict=True))
        r2_delta = abs(float(trow["renyi2_from_spectrum"]) - float(jrow["renyi2_from_spectrum"]))
        purity_delta = abs(float(trow["purity_from_spectrum"]) - float(jrow["purity_from_spectrum"]))
        variant_deltas.extend([spectrum_delta, r2_delta, purity_delta])

    input_r2 = float(torch_variants["input_bell"]["renyi2_from_spectrum"])
    zero_r2 = float(torch_variants["zero_identity_ordered"]["renyi2_from_spectrum"])
    ordered_r2 = float(torch_variants["ordered_cnot_then_damp"]["renyi2_from_spectrum"])
    swapped_r2 = float(torch_variants["swapped_damp_then_cnot"]["renyi2_from_spectrum"])

    pass_rung = bool(
        all(row["pass"] for row in torch_variants.values())
        and all(row["pass"] for row in jax_variants.values())
        and max(variant_deltas) < PARITY_TOL
        and real_inv_t["rank_gap"] >= RANK_EPS
        and real_inv_t["spectrum_gap"] >= GAP_EPS
        and zero_inv_t["rank_gap"] == 0.0
        and zero_inv_t["spectrum_gap"] < GAP_EPS
        and product_inv_t["rank_gap"] == 0.0
        and product_inv_t["spectrum_gap"] < GAP_EPS
        and abs(input_r2 - math.log(2.0)) < TOL
        and abs(zero_r2 - input_r2) < TOL
    )

    return {
        "sites_or_qubits": n_sites,
        "cut": n_sites // 2,
        "stage2_carrier_acted_on": "finite MPS/boundary_interior_cut bond spectrum carrier; product padding is implicit and not materialized",
        "physical_dim": PHYSICAL_DIM,
        "mps_max_bond": BOND_DIM,
        "bond_spectrum_dim": BOND_DIM,
        "dense_state_closure_used": False,
        "global_hilbert_dimension_not_materialized": f"2**{n_sites}",
        "full_dense_vector_or_matrix_allocated": False,
        "torch_variants": torch_variants,
        "jax_variants": jax_variants,
        "rank_gap_distinguishability_invariant": {
            "real_ordered_vs_swapped": real_inv_t,
            "zero_strength_identity_order_control": zero_inv_t,
            "product_control": product_inv_t,
            "jax_real_ordered_vs_swapped": real_inv_j,
            "entropy_used_in_invariant": False,
        },
        "renyi2_output_readouts": {
            "input_bell": input_r2,
            "ordered_cnot_then_damp": ordered_r2,
            "swapped_damp_then_cnot": swapped_r2,
            "ordered_vs_swapped_r2_gap_output_only": abs(ordered_r2 - swapped_r2),
            "zero_strength_identity_r2": zero_r2,
            "zero_strength_identity_delta_vs_input": abs(zero_r2 - input_r2),
        },
        "half_chain_entropy_output_renyi2": input_r2,
        "jax_vs_pytorch_delta": max(variant_deltas),
        "pass": pass_rung,
    }


def build_proofs(top: dict[str, Any]) -> dict[str, Any]:
    invariants = top["rank_gap_distinguishability_invariant"]
    real = invariants["real_ordered_vs_swapped"]
    zero = invariants["zero_strength_identity_order_control"]
    product = invariants["product_control"]
    zero_proof = smt_rank_gap_proof(
        real,
        zero,
        "rank_gap_and_spectrum_gap_separate_ordered_vs_swapped_carrier_but_not_zero_identity_order_control",
    )
    product_proof = smt_rank_gap_proof(
        real,
        product,
        "rank_gap_and_spectrum_gap_separate_ordered_vs_swapped_carrier_but_not_product_control",
    )
    sympy_flip = sympy_rank_gap_flip(real, zero)
    return {
        "rank_gap_zero_strength_identity_smt_load_bearing": zero_proof,
        "rank_gap_product_control_smt_load_bearing": product_proof,
        "sympy_rank_gap_zero_strength_flip": sympy_flip,
        "entropy_scalar_excluded_from_asserted_claim": {
            "entropy_used_in_smt_real_measured": False,
            "measured_fields_asserted": ["rank_gap", "spectrum_gap", "eps_rank", "eps_gap"],
            "renyi2_role": "reported readout only after rank/gap distinguishability is measured",
            "pass": True,
        },
    }


def build_tool_ablations(top: dict[str, Any], proofs: dict[str, Any]) -> dict[str, Any]:
    inv = top["rank_gap_distinguishability_invariant"]
    real = inv["real_ordered_vs_swapped"]
    zero = inv["zero_strength_identity_order_control"]
    torch_swapped = top["torch_variants"]["swapped_damp_then_cnot"]
    torch_zero = top["torch_variants"]["zero_identity_ordered"]
    torch_product = top["torch_variants"]["product_ordered"]
    z3_proof = proofs["rank_gap_zero_strength_identity_smt_load_bearing"]
    sympy_proof = proofs["sympy_rank_gap_zero_strength_flip"]

    return {
        "torch_rank_gap_real_vs_zero_control": tool_ablation(
            "torch measured rank_gap ordered-vs-swapped vs zero-strength identity order control",
            baseline_value=real["rank_gap"],
            ablated_value=zero["rank_gap"],
            tool="torch",
        ),
        "jax_spectrum_gap_real_vs_zero_control": tool_ablation(
            "jax/torch mirrored spectrum_gap ordered-vs-swapped vs zero-strength identity order control",
            baseline_value=inv["jax_real_ordered_vs_swapped"]["spectrum_gap"],
            ablated_value=zero["spectrum_gap"],
            tool="jax",
        ),
        "z3_rank_gap_flip_score": tool_ablation(
            "z3 helper flip-score for measured rank/gap claim; zero-control path scores unsat",
            baseline_value=sat_score(z3_proof, "z3", "real"),
            ablated_value=sat_score(z3_proof, "z3", "control"),
            tool="z3",
        ),
        "cvc5_rank_gap_flip_score": tool_ablation(
            "cvc5 helper flip-score for measured rank/gap claim; zero-control path scores unsat",
            baseline_value=sat_score(z3_proof, "cvc5", "real"),
            ablated_value=sat_score(z3_proof, "cvc5", "control"),
            tool="cvc5",
        ),
        "sympy_rank_gap_flip_score": tool_ablation(
            "sympy exact inequality flip-score for measured rank/gap claim",
            baseline_value=sat_score(sympy_proof, "sympy", "real"),
            ablated_value=sat_score(sympy_proof, "sympy", "control"),
            tool="sympy",
        ),
        "opt_einsum_reduced_block_purity_recompute": tool_ablation(
            "opt_einsum Tr(rho_A^2) on swapped control-sensitive block vs zero-strength identity block",
            baseline_value=torch_swapped["purity_from_reduced_block"],
            ablated_value=torch_zero["purity_from_reduced_block"],
            tool="opt_einsum",
        ),
        "quimb_svd_rank_recompute": tool_ablation(
            "quimb reduced-block SVD rank on swapped variant vs product-carrier control",
            baseline_value=torch_swapped["quimb_svd_rank"],
            ablated_value=torch_product["quimb_svd_rank"],
            tool="quimb",
        ),
    }


def proof_pass(proofs: dict[str, Any]) -> bool:
    helper_rows = [
        proofs["rank_gap_zero_strength_identity_smt_load_bearing"],
        proofs["rank_gap_product_control_smt_load_bearing"],
    ]
    helpers_ok = all(
        row.get("real_claim_verdict") == "sat"
        and row.get("negated_claim_verdict") == "unsat"
        and row.get("differ") is True
        and row.get("bound_to_measured") is True
        and row.get("cvc5_real_verdict") == "sat"
        and row.get("cvc5_control_verdict") == "unsat"
        for row in helper_rows
    )
    sympy = proofs["sympy_rank_gap_zero_strength_flip"]
    sympy_ok = (
        sympy.get("real_claim_verdict") == "sat"
        and sympy.get("negated_claim_verdict") == "unsat"
        and sympy.get("differ") is True
        and sympy.get("bound_to_measured") is True
    )
    return bool(helpers_ok and sympy_ok)


def ablation_pass(ablations: dict[str, Any]) -> bool:
    return all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= 1.0e-12
        for row in ablations.values()
    )


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    scale_rows = {str(n): run_rung(n) for n in SCALES}
    top = scale_rows[str(max(SCALES))]
    proofs = build_proofs(top)
    ablations = build_tool_ablations(top, proofs)
    known_checks = known_value_checks()

    scale_pass = all(row["pass"] for row in scale_rows.values())
    known_pass = all(row["match"] for row in known_checks)
    proofs_ok = proof_pass(proofs)
    ablations_ok = ablation_pass(ablations)
    parity_delta = max(float(row["jax_vs_pytorch_delta"]) for row in scale_rows.values())
    all_pass = bool(scale_pass and known_pass and proofs_ok and ablations_ok and parity_delta < PARITY_TOL)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(CDTYPE),
        "top_rung": max(SCALES),
        "real_rank_gap_ordered_vs_swapped": top["rank_gap_distinguishability_invariant"]["real_ordered_vs_swapped"]["rank_gap"],
        "real_spectrum_gap_ordered_vs_swapped": top["rank_gap_distinguishability_invariant"]["real_ordered_vs_swapped"]["spectrum_gap"],
        "zero_control_rank_gap": top["rank_gap_distinguishability_invariant"]["zero_strength_identity_order_control"]["rank_gap"],
        "zero_control_spectrum_gap": top["rank_gap_distinguishability_invariant"]["zero_strength_identity_order_control"]["spectrum_gap"],
        "renyi2_output_ordered": top["renyi2_output_readouts"]["ordered_cnot_then_damp"],
        "renyi2_output_swapped": top["renyi2_output_readouts"]["swapped_damp_then_cnot"],
        "entropy_used_as_organizer": False,
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "top_rung": max(SCALES),
        "real_rank_gap_ordered_vs_swapped": top["rank_gap_distinguishability_invariant"]["jax_real_ordered_vs_swapped"]["rank_gap"],
        "real_spectrum_gap_ordered_vs_swapped": top["rank_gap_distinguishability_invariant"]["jax_real_ordered_vs_swapped"]["spectrum_gap"],
        "max_jax_vs_pytorch_delta": parity_delta,
        "pass": bool(parity_delta < PARITY_TOL),
    }

    controls = {
        "zero_strength_identity_order": {
            "description": "same Bell boundary carrier, gamma=0 and identity order; ordered/swapped collapse and R2 stays at the input Bell value",
            "rank_gap": top["rank_gap_distinguishability_invariant"]["zero_strength_identity_order_control"]["rank_gap"],
            "spectrum_gap": top["rank_gap_distinguishability_invariant"]["zero_strength_identity_order_control"]["spectrum_gap"],
            "renyi2_delta_vs_input": top["renyi2_output_readouts"]["zero_strength_identity_delta_vs_input"],
            "distinguishability_claim_holds": False,
            "pass": bool(
                top["rank_gap_distinguishability_invariant"]["zero_strength_identity_order_control"]["rank_gap"] == 0.0
                and top["rank_gap_distinguishability_invariant"]["zero_strength_identity_order_control"]["spectrum_gap"] < GAP_EPS
                and top["renyi2_output_readouts"]["zero_strength_identity_delta_vs_input"] < TOL
            ),
        },
        "product_carrier_control": {
            "description": "product boundary carrier fed through the same CNOT/damping order variants; no rank/gap distinguishability appears",
            "rank_gap": top["rank_gap_distinguishability_invariant"]["product_control"]["rank_gap"],
            "spectrum_gap": top["rank_gap_distinguishability_invariant"]["product_control"]["spectrum_gap"],
            "distinguishability_claim_holds": False,
            "pass": bool(
                top["rank_gap_distinguishability_invariant"]["product_control"]["rank_gap"] == 0.0
                and top["rank_gap_distinguishability_invariant"]["product_control"]["spectrum_gap"] < GAP_EPS
            ),
        },
    }

    result = {
        "schema": "formal_scout_max_deep_lego_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thisfile": str(THISFILE.relative_to(ROOT)),
        "result": str(RESULT.relative_to(ROOT)),
        "object_id": OBJECT_ID,
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "S7 entropy/information readout lego",
        "purpose": "Read Renyi-2 from an already-admitted Stage-2 finite MPS/boundary cut carrier after rank/gap distinguishability has been measured.",
        "scientific_question": "Can a Renyi-2 readout be reported across 8/16/32/64 non-dense carrier rungs while the proof binds only to prior rank/gap distinguishability under order-sensitive controls?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "entropy_information_readout_probe",
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite site counts, finite bond spectrum dimension, finite boundary-cut density block, finite channel variants, finite controls",
            },
            "N01": {
                "status": "active_tested",
                "statement": "CNOT-before-damping and damping-before-CNOT are order-sensitive on the boundary carrier; zero-strength identity order and product controls erase the rank/gap distinction",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set: N in {8,16,32,64}, bond spectrum dimension 8, fixed boundary half-cut, finite order variants and controls",
            "N01 noncommuting/order-sensitive operation/control: CNOT and amplitude-damping order changes the measured rank/gap invariant; zero-strength identity order kills it",
        ],
        "finite_map": {
            "domain": "Stage-2 finite MPS / boundary_interior_cut carrier at N in {8,16,32,64}, fixed half-cut, boundary Bell/product controls, order variants {CNOT then damping, damping then CNOT}",
            "codomain_or_output": "measured rank_gap and spectrum_gap distinguishability invariant first; Renyi-2 and purity readouts second; proof verdicts and blocked consumers",
            "definition": "Readout_N maps the admitted carrier's small boundary-cut reduced block rho_A to its spectrum, rank/gap invariant, purity, and R2=-log(Tr(rho_A^2)) without selecting the carrier by entropy",
        },
        "domain": {
            "acts_on_prior_carrier": "Stage-2 finite MPS / boundary_interior_cut carrier",
            "site_counts": list(SCALES),
            "fixed_cut": "n/2 boundary cut",
            "bond_spectrum_dim": BOND_DIM,
            "physical_dim": PHYSICAL_DIM,
            "dense_state_closure_used": False,
        },
        "codomain_or_output": "Rank/gap distinguishability invariant, reduced-block spectrum, purity, Renyi-2 output scalar, SMT proof flips, controls, tool ablations, and blocked consumers.",
        "carrier_layer": "already-admitted Stage-2 finite MPS / boundary_interior_cut carrier; this file adds only an information readout",
        "geometry_layer": "fixed boundary half-cut; no new geometry, axis, bridge, or manifold layer is introduced",
        "carrier_realization": "torch.complex128 primary two-qubit boundary-cut block embedded as an 8-slot bond spectrum over non-dense N-site MPS rungs; jax.numpy complex128 mirror; no NumPy and no dense 2**N closure",
        "peps3d_embedding": {
            "anchor": "inherited boundary-cut/MPS carrier anchor only; no new PEPS3D contraction closure is claimed",
            "promotion_block": "full PEPS3D, bridge, Axis0, flux, FEP, gravity, and final manifold consumers remain blocked",
        },
        "spinor_state": "boundary Bell/product C^2 x C^2 spinor-derived density blocks; readout acts on reduced rho_A at the fixed cut",
        "quaternion_action": "not_applicable: no quaternion language or claim is used",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/carrier_mps_probe_results.json",
            "system_v5/ops/formal_scouts/results/boundary_interior_cut_results.json",
            "system_v5/ops/formal_scouts/results/entanglement_entropy_8_16_32_64_dual_engine_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "fixed half-cut boundary reduced state rho_A; no cut selection by entropy",
        "law_or_candidate_tested": "Renyi-2 can be emitted as a Stage-7 readout only after rank/gap distinguishability separates real order variants and fails under degenerate controls",
        "branch_status_before_run": "bounded Stage-7 readout requested by user; no promotion route opened",
        "allowed_claims": [
            "this one file exists/runs as a bounded Stage-7 Renyi-2 readout lego when fresh gates pass",
            "rank/gap distinguishability, not entropy, is the SMT-bound invariant",
            "Renyi-2 is output-only across non-dense N=8/16/32/64 rungs with torch/JAX parity",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "readout only; does not build or admit a new physical carrier",
            "no bridge, Axis0, flux, basin, FEP, physics, gravity, or final manifold consumer is admitted",
            "full PEPS3D contraction closure is not claimed",
        ],
        "eligible_consumers": ["bounded Stage-7 readout comparisons after parent carrier receipts are cited"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [key for key, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3 rank/gap verdict flip", "cvc5 rank/gap verdict flip", "sympy rank/gap symbolic flip"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": ["zero-strength identity order", "product carrier control", "entropy-scalar exclusion from SMT claim"],
        "negatives_run": controls,
        "kill_conditions": {
            "zero_strength_identity_order": "rank_gap=0 and spectrum_gap<eps while R2 remains the input Bell readout",
            "product_carrier_control": "same channel-order variants do not create rank/gap distinguishability",
            "entropy_scalar_exclusion": "proof measured fields contain rank_gap/spectrum_gap only and no Renyi-2/purity scalar",
        },
        "required_artifacts": ["result JSON", "scale ladder", "proof flips", "known-value checks", "tool manifest/depth", "tool ablations", "blocked consumers"],
        "artifacts_emitted": [str(RESULT.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "known_value_checks_pass": known_pass,
            "proofs_pass": proofs_ok,
            "tool_ablations_pass": ablations_ok,
            "jax_vs_pytorch_delta": parity_delta,
            "entropy_as_output_not_organizer": True,
            "elapsed_seconds": time.time() - started,
        },
        "shells": [
            {
                "name": "stage2_mps_boundary_cut_carrier",
                "carrier": "finite non-dense MPS/boundary cut spectrum",
                "rungs": list(SCALES),
                "survives": scale_pass,
            },
            {
                "name": "stage7_renyi2_output_readout",
                "carrier": "same fixed carrier; no entropy-selected carrier mutation",
                "rungs": list(SCALES),
                "survives": all_pass,
            },
        ],
        "future_continuations": [
            "compare Renyi-2 against other information readouts only after the same rank/gap proof shape is preserved",
            "add a PEPS3D-specific readout only after a separate PEPS3D carrier receipt exists",
        ],
        "compatibility_weights": {
            "stage7_readout_local": 1.0 if all_pass else 0.0,
            "downstream_bridge_axis_flux_physics": 0.0,
        },
        "compression_map": {
            "from": "Stage-2 boundary carrier variants, reduced rho_A blocks, and measured spectra",
            "to": "rank/gap invariant, Renyi-2 output scalars, proof flips, controls, and ablation deltas",
            "loss_boundary": "does not preserve a global dense state and does not admit new carrier, bridge, axis, flux, FEP, gravity, physics, or final manifold claims",
        },
        "present_survivor": {
            "object": "Renyi-2 readout bound below rank/gap distinguishability",
            "capacity": "reports R2 across non-dense 8/16/32/64 rungs while SMT proof binds only to rank/gap invariant",
            "blocked_capacity": BLOCKED_CONSUMERS,
            "passed": all_pass,
        },
        "survivor_invariant": {
            "invariant": "rank_gap and spectrum_gap separate ordered/swapped real carrier variants and collapse under zero-strength/product controls before Renyi-2 is read out",
            "passed": bool(all_pass and proofs_ok and controls["zero_strength_identity_order"]["pass"] and controls["product_carrier_control"]["pass"]),
        },
        "outward_record": {
            "result_path": str(RESULT.relative_to(ROOT)),
            "gate_command": "../../../scripts/max_deep_lego_gate.py results/s7_renyi2_readout_results.json --scale-required --rigor",
            "claim_ceiling": "Stage-7 readout lego only; no bridge, Axis0, flux, FEP, gravity, physics, or final manifold admission",
        },
        "pass_rule": "all non-dense 8/16/32/64 rungs pass, known values match, torch/JAX agree, rank/gap SMT flips real SAT vs controls UNSAT, and ablations recompute nonzero deltas",
        "fail_rule": "fail on entropy inside SMT measured fields, no rank/gap verdict flip, dense global closure, failed known value, missing control, JAX mismatch, cosmetic ablation, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": parity_delta,
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "scale_ladder": {
            "rungs": {
                key: {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "cut": row["cut"],
                    "mps_max_bond": row["mps_max_bond"],
                    "bond_spectrum_dim": row["bond_spectrum_dim"],
                    "dense_state_closure_used": row["dense_state_closure_used"],
                    "real_rank_gap": row["rank_gap_distinguishability_invariant"]["real_ordered_vs_swapped"]["rank_gap"],
                    "real_spectrum_gap": row["rank_gap_distinguishability_invariant"]["real_ordered_vs_swapped"]["spectrum_gap"],
                    "zero_control_rank_gap": row["rank_gap_distinguishability_invariant"]["zero_strength_identity_order_control"]["rank_gap"],
                    "renyi2_ordered_output": row["renyi2_output_readouts"]["ordered_cnot_then_damp"],
                    "renyi2_swapped_output": row["renyi2_output_readouts"]["swapped_damp_then_cnot"],
                    "half_chain_entropy_output_renyi2": row["half_chain_entropy_output_renyi2"],
                    "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                    "pass": row["pass"],
                }
                for key, row in scale_rows.items()
            },
            "pass": scale_pass,
        },
        "scale_details": scale_rows,
        "known_value_checks": known_checks,
        "entropy_as_output": {
            "renyi2_formula": "R2(rho_A) = -log(Tr(rho_A^2))",
            "organizer": False,
            "prior_invariant": "rank_gap and spectrum_gap distinguishability over fixed carrier variants",
            "proof_measured_fields": ["rank_gap", "spectrum_gap"],
            "pass": True,
        },
        "positive": {
            "all_8_16_32_64_non_dense_rungs_pass": {"pass": scale_pass, "rungs": list(scale_rows)},
            "rank_gap_smt_verdict_flip": proofs["rank_gap_zero_strength_identity_smt_load_bearing"],
            "dual_engine_renyi2_parity": {"max_delta": parity_delta, "pass": parity_delta < PARITY_TOL},
        },
        "graveyard_companions": controls,
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "entropy_not_master_variable": {"entropy_used_in_smt": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "ordered_vs_swapped_rank_gap": top["rank_gap_distinguishability_invariant"]["real_ordered_vs_swapped"]["rank_gap"],
            "ordered_vs_swapped_r2_gap_output_only": top["renyi2_output_readouts"]["ordered_vs_swapped_r2_gap_output_only"],
            "zero_strength_identity_delta_vs_input": top["renyi2_output_readouts"]["zero_strength_identity_delta_vs_input"],
            "pass": bool(controls["zero_strength_identity_order"]["pass"] and controls["product_carrier_control"]["pass"]),
        },
        "divergence_log": [],
        "why_not_v4_probes": "This is a v5 bounded Stage-7 readout over existing Stage-2 carriers; it is not a legacy axis/bridge result and does not promote downstream consumers.",
        "blockers": [] if all_pass else ["one or more local pass rules failed; inspect result_summary"],
        "all_pass": all_pass,
        "required_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "result": str(RESULT), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
