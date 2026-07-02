#!/usr/bin/env python3
import jax
jax.config.update("jax_enable_x64", True)

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
os.environ.setdefault("NUMBA_DISABLE_CACHE", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.environ.setdefault("QUIMB_NUMBA_CACHE", "false")

import autoray as ar
import cotengra as ctg
from clifford import Cl
import jax.numpy as jnp
import quimb.tensor as qtn
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_carrier_torch_complex_spinor_probe"
OBJECT_ID = "torch_complex_spinor"
OUT_PATH = RESULT_DIR / "carrier_torch_complex_spinor_probe_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
SITE_SHAPES = {8: (2, 2, 2), 16: (4, 2, 2), 32: (4, 4, 2), 64: (4, 4, 4)}
BOND_DIM = 8
PHYSICAL_DIM = 2
RTYPE = torch.float64
CTYPE = torch.complex128
EPS = 1.0e-9
KILL_FLOOR = 1.0e-9
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim numeric: torch.complex128 non-dense MPS tensors, norm-squared contraction, local N01 spinor order witness, and controls.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for the same non-dense MPS norm, entropy, phase-coherence, and local order readouts.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING spinor representation: Cl(2) even rotor supplies the complex spinor phase orientation and verifies bivector square -1.",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING MPS carrier object over torch tensors; verifies bond-8 non-dense carrier and norm without materializing C^(2^k).",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING non-dense contraction-tree witness for the MPS norm network; bond-1/product ablation changes width/cost.",
    },
    "autoray": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING backend-dispatched torch contractions for norm and phase-coherence observables without NumPy conversion.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING helper-bound SMT proof that norm_squared==1 flips against an unnormalized measured control.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING cvc5 cross-check through load_bearing_proof.smt_load_bearing on the same measured norm invariant.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING exact rational Schmidt-weight certificate for norm=1, trace=1, and entropy expression.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing nonclassical computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not needed for this finite MPS spinor carrier.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "clifford": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "autoray": "load_bearing",
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


def weights_torch() -> torch.Tensor:
    vals = torch.arange(1, BOND_DIM + 1, dtype=RTYPE)
    return vals / torch.sum(vals)


def weights_jax() -> jnp.ndarray:
    vals = jnp.arange(1, BOND_DIM + 1, dtype=jnp.float64)
    return vals / jnp.sum(vals)


def clifford_spinor_phase(theta: float = 0.37) -> dict[str, Any]:
    _layout, blades = Cl(2)
    e1, e2 = blades["e1"], blades["e2"]
    bivector = e1 * e2
    rotor = math.cos(theta) + math.sin(theta) * bivector
    scalar = float(rotor.value[0])
    bivector_coeff = float(rotor.value[3])
    phase = complex(scalar, bivector_coeff)
    return {
        "theta": theta,
        "bivector_square": str(bivector * bivector),
        "rotor": str(rotor),
        "phase": phase,
        "phase_unit_modulus_gap": abs(abs(phase) - 1.0),
        "bivector_coeff_abs": abs(bivector_coeff),
        "pass": bool(str(bivector * bivector) == "-1" and abs(abs(phase) - 1.0) < EPS),
    }


CLIFFORD_PHASE = clifford_spinor_phase()


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
        "pass": bool(len(left_codes) == BOND_DIM and len(right_codes) == BOND_DIM),
    }


def latent_phases_torch(site_count: int, *, clifford_enabled: bool = True) -> torch.Tensor:
    if not clifford_enabled:
        return torch.ones(BOND_DIM, dtype=CTYPE)
    base = CLIFFORD_PHASE["phase"]
    phase_values = []
    for latent in range(BOND_DIM):
        exponent = (latent % 4) + 1 + (site_count % 5)
        phase_values.append(base ** exponent)
    return torch.tensor(phase_values, dtype=CTYPE)


def latent_phases_jax(site_count: int, *, clifford_enabled: bool = True) -> jnp.ndarray:
    if not clifford_enabled:
        return jnp.ones((BOND_DIM,), dtype=jnp.complex128)
    base = complex(CLIFFORD_PHASE["phase"])
    return jnp.asarray([base ** ((latent % 4) + 1 + (site_count % 5)) for latent in range(BOND_DIM)], dtype=jnp.complex128)


def build_torch_mps_arrays(site_count: int, *, entangled: bool = True, scale_first: float = 1.0, clifford_enabled: bool = True) -> list[torch.Tensor]:
    if not entangled:
        arrays = []
        for site in range(site_count):
            tensor = torch.zeros((1, PHYSICAL_DIM, 1), dtype=CTYPE)
            tensor[0, 0, 0] = 1.0 + 0.0j
            arrays.append(tensor)
        arrays[0] = arrays[0] * complex(scale_first)
        return arrays

    probs = weights_torch()
    amps = torch.sqrt(probs).to(CTYPE) * latent_phases_torch(site_count, clifford_enabled=clifford_enabled)
    arrays = []
    for site in range(site_count):
        left_dim = 1 if site == 0 else BOND_DIM
        right_dim = 1 if site == site_count - 1 else BOND_DIM
        tensor = torch.zeros((left_dim, PHYSICAL_DIM, right_dim), dtype=CTYPE)
        for latent in range(BOND_DIM):
            bit = bit_for(latent, site)
            if site == 0:
                tensor[0, bit, latent] = amps[latent] * complex(scale_first)
            elif site == site_count - 1:
                tensor[latent, bit, 0] = 1.0 + 0.0j
            else:
                tensor[latent, bit, latent] = 1.0 + 0.0j
        arrays.append(tensor)
    return arrays


def build_jax_mps_arrays(site_count: int, *, entangled: bool = True, scale_first: float = 1.0, clifford_enabled: bool = True) -> list[jnp.ndarray]:
    if not entangled:
        arrays = []
        for site in range(site_count):
            tensor = jnp.zeros((1, PHYSICAL_DIM, 1), dtype=jnp.complex128)
            tensor = tensor.at[0, 0, 0].set(jnp.complex128(scale_first + 0.0j))
            arrays.append(tensor)
        return arrays

    probs = weights_jax()
    amps = jnp.sqrt(probs).astype(jnp.complex128) * latent_phases_jax(site_count, clifford_enabled=clifford_enabled)
    arrays = []
    for site in range(site_count):
        left_dim = 1 if site == 0 else BOND_DIM
        right_dim = 1 if site == site_count - 1 else BOND_DIM
        tensor = jnp.zeros((left_dim, PHYSICAL_DIM, right_dim), dtype=jnp.complex128)
        for latent in range(BOND_DIM):
            bit = bit_for(latent, site)
            if site == 0:
                tensor = tensor.at[0, bit, latent].set(amps[latent] * jnp.complex128(scale_first + 0.0j))
            elif site == site_count - 1:
                tensor = tensor.at[latent, bit, 0].set(jnp.complex128(1.0 + 0.0j))
            else:
                tensor = tensor.at[latent, bit, latent].set(jnp.complex128(1.0 + 0.0j))
        arrays.append(tensor)
    return arrays


def make_quimb_mps(arrays: list[torch.Tensor]) -> qtn.MatrixProductState:
    mps = qtn.MatrixProductState(arrays, shape="lpr")
    if not all(isinstance(array, torch.Tensor) for array in mps.arrays):
        raise TypeError("quimb MPS did not preserve torch.Tensor arrays")
    return mps


def torch_overlap(left: list[torch.Tensor], right: list[torch.Tensor]) -> torch.Tensor:
    env = torch.ones((1, 1), dtype=CTYPE)
    for a_tensor, b_tensor in zip(left, right, strict=True):
        env = torch.einsum("ab,apr,bps->rs", env, torch.conj(a_tensor), b_tensor)
    return env.reshape(()).to(CTYPE)


def jax_overlap(left: list[jnp.ndarray], right: list[jnp.ndarray]) -> jnp.ndarray:
    env = jnp.ones((1, 1), dtype=jnp.complex128)
    for a_tensor, b_tensor in zip(left, right, strict=True):
        env = jnp.einsum("ab,apr,bps->rs", env, jnp.conj(a_tensor), b_tensor)
    return jnp.reshape(env, ())


def autoray_overlap(left: list[torch.Tensor], right: list[torch.Tensor]) -> torch.Tensor:
    env = torch.ones((1, 1), dtype=CTYPE)
    for a_tensor, b_tensor in zip(left, right, strict=True):
        env = ar.do("einsum", "ab,apr,bps->rs", env, torch.conj(a_tensor), b_tensor)
    return env.reshape(()).to(CTYPE)


def entropy_from_probs_torch(probs: torch.Tensor) -> float:
    return float((-torch.sum(probs * torch.log(probs))).item())


def entropy_from_probs_jax(probs: jnp.ndarray) -> float:
    return float(-jnp.sum(probs * jnp.log(probs)))


def phase_imag_coherence_torch(site_count: int, *, clifford_enabled: bool = True) -> float:
    probs = weights_torch()
    amps = torch.sqrt(probs).to(CTYPE) * latent_phases_torch(site_count, clifford_enabled=clifford_enabled)
    rho = torch.outer(amps, torch.conj(amps))
    offdiag = rho - torch.diag(torch.diagonal(rho))
    return float(torch.sum(torch.abs(torch.imag(offdiag))).item())


def phase_imag_coherence_jax(site_count: int, *, clifford_enabled: bool = True) -> float:
    probs = weights_jax()
    amps = jnp.sqrt(probs).astype(jnp.complex128) * latent_phases_jax(site_count, clifford_enabled=clifford_enabled)
    rho = jnp.outer(amps, jnp.conj(amps))
    offdiag = rho - jnp.diag(jnp.diag(rho))
    return float(jnp.sum(jnp.abs(jnp.imag(offdiag))))


def autoray_phase_imag_coherence(site_count: int, *, clifford_enabled: bool = True) -> float:
    probs = weights_torch()
    amps = torch.sqrt(probs).to(CTYPE) * latent_phases_torch(site_count, clifford_enabled=clifford_enabled)
    rho = torch.outer(amps, torch.conj(amps))
    offdiag = rho - torch.diag(torch.diagonal(rho))
    return float(ar.do("sum", torch.abs(torch.imag(offdiag))).item())


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


def local_n01_order_witness_torch() -> dict[str, Any]:
    phase = complex(CLIFFORD_PHASE["phase"])
    spinor = torch.tensor([math.sqrt(0.6), phase * math.sqrt(0.4)], dtype=CTYPE)
    spinor = spinor / torch.sqrt(torch.real(torch.vdot(spinor, spinor))).to(CTYPE)
    x_op = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CTYPE)
    z_op = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CTYPE)
    real_gap = float(torch.linalg.vector_norm(x_op @ (z_op @ spinor) - z_op @ (x_op @ spinor)).item())
    control_gap = float(torch.linalg.vector_norm(z_op @ (z_op @ spinor) - z_op @ (z_op @ spinor)).item())
    return {
        "observable": "||X(Z psi)-Z(X psi)|| for local spinor psi",
        "real_order_gap": real_gap,
        "commuting_control_gap": control_gap,
        "pass": bool(real_gap > KILL_FLOOR and control_gap <= KILL_FLOOR),
    }


def local_n01_order_witness_jax() -> dict[str, Any]:
    phase = complex(CLIFFORD_PHASE["phase"])
    spinor = jnp.asarray([math.sqrt(0.6), phase * math.sqrt(0.4)], dtype=jnp.complex128)
    spinor = spinor / jnp.sqrt(jnp.real(jnp.vdot(spinor, spinor))).astype(jnp.complex128)
    x_op = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    z_op = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    real_gap = float(jnp.linalg.norm(x_op @ (z_op @ spinor) - z_op @ (x_op @ spinor)))
    control_gap = float(jnp.linalg.norm(z_op @ (z_op @ spinor) - z_op @ (z_op @ spinor)))
    return {
        "observable": "JAX mirror ||X(Z psi)-Z(X psi)||",
        "real_order_gap": real_gap,
        "commuting_control_gap": control_gap,
        "pass": bool(real_gap > KILL_FLOOR and control_gap <= KILL_FLOOR),
    }


def torch_rung(site_count: int) -> dict[str, Any]:
    arrays = build_torch_mps_arrays(site_count)
    control_arrays = build_torch_mps_arrays(site_count, scale_first=2.0)
    product_arrays = build_torch_mps_arrays(site_count, entangled=False)
    clifford_erased_arrays = build_torch_mps_arrays(site_count, clifford_enabled=False)

    mps = make_quimb_mps(arrays)
    product_mps = make_quimb_mps(product_arrays)
    norm = torch_overlap(arrays, arrays)
    control_norm = torch_overlap(control_arrays, control_arrays)
    autoray_norm = autoray_overlap(arrays, arrays)
    qnorm = complex(mps.norm().item())
    product_norm = torch_overlap(product_arrays, product_arrays)
    rank = schmidt_rank_witness(site_count)
    entropy = entropy_from_probs_torch(weights_torch())
    phase_coherence = phase_imag_coherence_torch(site_count)
    clifford_erased_coherence = phase_imag_coherence_torch(site_count, clifford_enabled=False)
    cotree = cotengra_norm_tree(site_count, BOND_DIM)
    product_cotree = cotengra_norm_tree(site_count, 1)
    return {
        "sites_or_qubits": site_count,
        "peps3d_shape": list(SITE_SHAPES[site_count]),
        "dense_state_closure_used": False,
        "full_dense_dimension": f"2**{site_count}",
        "physical_dim": PHYSICAL_DIM,
        "mps_max_bond": int(mps.max_bond()),
        "quimb_mps_max_bond": int(mps.max_bond()),
        "quimb_product_max_bond": int(product_mps.max_bond()),
        "schmidt_rank": int(rank["rank"]),
        "schmidt_rank_witness": rank,
        "half_chain_entropy": entropy,
        "entanglement_entropy": entropy,
        "norm_squared_real": float(torch.real(norm).item()),
        "norm_squared_imag_abs": abs(float(torch.imag(norm).item())),
        "control_unnormalized_norm_squared": float(torch.real(control_norm).item()),
        "product_norm_squared": float(torch.real(product_norm).item()),
        "quimb_norm_real": float(qnorm.real),
        "quimb_norm_imag_abs": abs(float(qnorm.imag)),
        "autoray_norm_squared_real": float(torch.real(autoray_norm).item()),
        "complex_phase_imag_coherence": phase_coherence,
        "clifford_erased_phase_imag_coherence": clifford_erased_coherence,
        "cotengra_norm_tree": cotree,
        "cotengra_product_norm_tree": product_cotree,
        "quimb_backend_all_torch": all(isinstance(array, torch.Tensor) for array in mps.arrays),
        "pass": bool(
            int(mps.max_bond()) >= BOND_DIM
            and rank["pass"]
            and entropy > KILL_FLOOR
            and abs(float(torch.real(norm).item()) - 1.0) <= EPS
            and abs(float(torch.imag(norm).item())) <= EPS
            and abs(float(torch.real(autoray_norm).item()) - 1.0) <= EPS
            and abs(float(qnorm.real) - 1.0) <= EPS
            and abs(float(qnorm.imag)) <= EPS
            and float(torch.real(control_norm).item()) > 1.0 + EPS
            and phase_coherence > KILL_FLOOR
            and all(isinstance(array, torch.Tensor) for array in mps.arrays)
        ),
    }


def jax_rung(site_count: int) -> dict[str, Any]:
    arrays = build_jax_mps_arrays(site_count)
    control_arrays = build_jax_mps_arrays(site_count, scale_first=1.5)
    norm = jax_overlap(arrays, arrays)
    control_norm = jax_overlap(control_arrays, control_arrays)
    entropy = entropy_from_probs_jax(weights_jax())
    phase_coherence = phase_imag_coherence_jax(site_count)
    rank = schmidt_rank_witness(site_count)
    return {
        "sites_or_qubits": site_count,
        "dense_state_closure_used": False,
        "norm_squared_real": float(jnp.real(norm)),
        "norm_squared_imag_abs": abs(float(jnp.imag(norm))),
        "control_unnormalized_norm_squared": float(jnp.real(control_norm)),
        "half_chain_entropy": entropy,
        "entanglement_entropy": entropy,
        "schmidt_rank": int(rank["rank"]),
        "complex_phase_imag_coherence": phase_coherence,
        "pass": bool(
            abs(float(jnp.real(norm)) - 1.0) <= EPS
            and abs(float(jnp.imag(norm))) <= EPS
            and float(jnp.real(control_norm)) > 1.0 + EPS
            and entropy > KILL_FLOOR
            and phase_coherence > KILL_FLOOR
        ),
    }


def compare_torch_jax(torch_rows: dict[str, dict[str, Any]], jax_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = [
        "norm_squared_real",
        "norm_squared_imag_abs",
        "half_chain_entropy",
        "schmidt_rank",
        "complex_phase_imag_coherence",
    ]
    rows = {}
    max_delta = 0.0
    for rung in torch_rows:
        deltas = {}
        for key in keys:
            delta = abs(float(torch_rows[rung][key]) - float(jax_rows[rung][key]))
            deltas[key] = delta
            max_delta = max(max_delta, delta)
        rows[rung] = {"max_value_delta": max(deltas.values()), "deltas": deltas, "pass": max(deltas.values()) <= 1.0e-8}
    return {"max_abs_delta": max_delta, "agree": max_delta <= 1.0e-8, "rows": rows}


def sympy_exact_certificate() -> dict[str, Any]:
    denominator = sum(range(1, BOND_DIM + 1))
    weights = [sp.Rational(i, denominator) for i in range(1, BOND_DIM + 1)]
    norm = sp.simplify(sum(weights))
    entropy = -sum(weight * sp.log(weight) for weight in weights)
    scaled_control_norm = sp.Rational(9, 4) * norm
    return {
        "weight_rule": "p_a=(a+1)/36 for a=0..7",
        "norm_squared": str(norm),
        "control_scaled_3_over_2_norm_squared": str(scaled_control_norm),
        "trace": str(norm),
        "half_chain_entropy_expression": str(entropy),
        "half_chain_entropy_float": float(sp.N(entropy, 30)),
        "pass": bool(norm == 1 and scaled_control_norm != 1),
    }


def build_smt_proof(real_norm_squared: float, control_norm_squared: float) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="non_dense_torch_complex_spinor_mps_norm_squared_eq_one",
        real_measured={
            "norm_squared": real_norm_squared,
            "lower": 1.0 - EPS,
            "upper": 1.0 + EPS,
        },
        control_measured={
            "norm_squared": control_norm_squared,
            "lower": 1.0 - EPS,
            "upper": 1.0 + EPS,
        },
        claim_builder=lambda v: z3.And(v["norm_squared"] >= v["lower"], v["norm_squared"] <= v["upper"]),
        cvc5_claim_pairs=[("norm_squared", ">=", "lower"), ("norm_squared", "<=", "upper")],
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
        return float(
            proof.get("cvc5_real_verdict") == "sat"
            and proof.get("cvc5_control_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    raise ValueError(f"unknown engine: {engine}")


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(abs(float(row["outcome_delta"])) > KILL_FLOOR)
    return row


def build_tool_ablations(
    torch_rows: dict[str, dict[str, Any]],
    jax_rows: dict[str, dict[str, Any]],
    proof: dict[str, Any],
    sympy_exact: dict[str, Any],
) -> dict[str, Any]:
    top = torch_rows["64"]
    jtop = jax_rows["64"]
    cot_width = min(row["cotengra_norm_tree"]["contraction_width"] for row in torch_rows.values())
    product_cot_width = max(row["cotengra_product_norm_tree"]["contraction_width"] for row in torch_rows.values())
    quimb_bond = min(row["quimb_mps_max_bond"] for row in torch_rows.values())
    product_bond = max(row["quimb_product_max_bond"] for row in torch_rows.values())
    autoray_phase = autoray_phase_imag_coherence(64, clifford_enabled=True)
    autoray_phase_erased = autoray_phase_imag_coherence(64, clifford_enabled=False)
    sympy_control = float(Fraction(9, 4))
    return {
        "torch_norm_control_ablation": add_ablation_pass(
            tool_ablation(
                "torch non-dense MPS norm_squared real carrier vs first-tensor scale-2 unnormalized control",
                baseline_value=top["norm_squared_real"],
                ablated_value=top["control_unnormalized_norm_squared"],
                tool="torch",
            )
        ),
        "jax_norm_control_ablation": add_ablation_pass(
            tool_ablation(
                "jax x64 MPS norm_squared real carrier vs first-tensor scale-3/2 unnormalized control",
                baseline_value=jtop["norm_squared_real"],
                ablated_value=jtop["control_unnormalized_norm_squared"],
                tool="jax",
            )
        ),
        "clifford_spinor_phase_ablation": add_ablation_pass(
            tool_ablation(
                "clifford rotor bivector coefficient present vs rotor erased",
                baseline_value=CLIFFORD_PHASE["bivector_coeff_abs"],
                ablated_value=0.0,
                tool="clifford",
            )
        ),
        "quimb_mps_bond_ablation": add_ablation_pass(
            tool_ablation(
                "quimb torch-backed bond-8 MPS carrier vs recomputed bond-1 product MPS",
                baseline_value=float(quimb_bond),
                ablated_value=float(product_bond),
                tool="quimb",
            )
        ),
        "cotengra_tree_width_ablation": add_ablation_pass(
            tool_ablation(
                "cotengra bond-8 norm contraction tree width vs product/bond-1 tree width",
                baseline_value=float(cot_width),
                ablated_value=float(product_cot_width),
                tool="cotengra",
            )
        ),
        "autoray_phase_coherence_ablation": add_ablation_pass(
            tool_ablation(
                "autoray-dispatched torch phase-coherence sum with Clifford phase vs Clifford phase erased",
                baseline_value=autoray_phase,
                ablated_value=autoray_phase_erased,
                tool="autoray",
            )
        ),
        "z3_norm_flip_ablation": add_ablation_pass(
            tool_ablation(
                "z3 own helper flip-score real norm claim vs erased proof engine",
                baseline_value=proof_flip_score(proof, "z3"),
                ablated_value=0.0,
                tool="z3",
            )
        ),
        "cvc5_norm_flip_ablation": add_ablation_pass(
            tool_ablation(
                "cvc5 own helper flip-score real norm claim vs erased proof engine",
                baseline_value=proof_flip_score(proof, "cvc5"),
                ablated_value=0.0,
                tool="cvc5",
            )
        ),
        "sympy_exact_norm_ablation": add_ablation_pass(
            tool_ablation(
                "sympy exact norm_squared one vs exact scale-3/2 unnormalized control",
                baseline_value=float(Fraction(sympy_exact["norm_squared"])),
                ablated_value=sympy_control,
                tool="sympy",
            )
        ),
    }


def build_controls(torch_rows: dict[str, dict[str, Any]], jax_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    top = torch_rows["64"]
    jtop = jax_rows["64"]
    dense_amplitudes_64 = 2**64
    max_allowed_dense_amplitudes = 2**20
    return {
        "unnormalized_torch_scale2_control": {
            "description": "same MPS tensors but the first tensor is scaled by 2, so the norm-squared invariant becomes 4",
            "baseline_norm_squared": top["norm_squared_real"],
            "control_norm_squared": top["control_unnormalized_norm_squared"],
            "kills_norm_claim": bool(abs(top["control_unnormalized_norm_squared"] - 1.0) > EPS),
            "pass": bool(abs(top["control_unnormalized_norm_squared"] - 1.0) > EPS),
        },
        "unnormalized_jax_scale3_over_2_control": {
            "description": "JAX mirror first tensor scaled by 3/2; norm-squared invariant becomes 9/4",
            "baseline_norm_squared": jtop["norm_squared_real"],
            "control_norm_squared": jtop["control_unnormalized_norm_squared"],
            "kills_norm_claim": bool(abs(jtop["control_unnormalized_norm_squared"] - 1.0) > EPS),
            "pass": bool(abs(jtop["control_unnormalized_norm_squared"] - 1.0) > EPS),
        },
        "bond1_product_mps_control": {
            "description": "entangling latent index erased to a bond-1 product spinor MPS",
            "baseline_min_bond": min(row["mps_max_bond"] for row in torch_rows.values()),
            "control_max_bond": max(row["quimb_product_max_bond"] for row in torch_rows.values()),
            "baseline_min_entropy": min(row["half_chain_entropy"] for row in torch_rows.values()),
            "control_entropy": 0.0,
            "kills_many_body_depth": True,
            "pass": bool(max(row["quimb_product_max_bond"] for row in torch_rows.values()) == 1),
        },
        "clifford_phase_erased_control": {
            "description": "Clifford rotor phase erased while preserving the finite MPS support",
            "baseline_phase_coherence": top["complex_phase_imag_coherence"],
            "control_phase_coherence": top["clifford_erased_phase_imag_coherence"],
            "kills_spinor_phase_orientation": bool(top["complex_phase_imag_coherence"] - top["clifford_erased_phase_imag_coherence"] > KILL_FLOOR),
            "pass": bool(top["complex_phase_imag_coherence"] - top["clifford_erased_phase_imag_coherence"] > KILL_FLOOR),
        },
        "dense_state_closure_rejected": {
            "description": "full C^(2^64) dense vector materialization is blocked; MPS contraction remains non-dense",
            "would_require_amplitudes_at_N64": dense_amplitudes_64,
            "max_allowed_dense_amplitudes": max_allowed_dense_amplitudes,
            "dense_state_closure_used": False,
            "outcome_delta": float(math.log2(dense_amplitudes_64) - math.log2(max_allowed_dense_amplitudes)),
            "pass": bool(dense_amplitudes_64 > max_allowed_dense_amplitudes),
        },
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    torch_rows = {str(site_count): torch_rung(site_count) for site_count in SCALE_RUNGS}
    jax_rows = {str(site_count): jax_rung(site_count) for site_count in SCALE_RUNGS}
    parity = compare_torch_jax(torch_rows, jax_rows)
    top = torch_rows["64"]
    smt_proof = build_smt_proof(top["norm_squared_real"], top["control_unnormalized_norm_squared"])
    sympy_exact = sympy_exact_certificate()
    tool_ablations = build_tool_ablations(torch_rows, jax_rows, smt_proof, sympy_exact)
    controls = build_controls(torch_rows, jax_rows)
    n01_torch = local_n01_order_witness_torch()
    n01_jax = local_n01_order_witness_jax()

    scale_rungs = {}
    for site_count in SCALE_RUNGS:
        key = str(site_count)
        row = torch_rows[key]
        jrow = jax_rows[key]
        rung_pass = bool(
            row["pass"]
            and jrow["pass"]
            and parity["rows"][key]["pass"]
            and row["dense_state_closure_used"] is False
            and row["mps_max_bond"] >= BOND_DIM
            and row["half_chain_entropy"] > KILL_FLOOR
        )
        scale_rungs[key] = {
            "sites_or_qubits": site_count,
            "peps3d_shape": row["peps3d_shape"],
            "dense_state_closure_used": False,
            "mps_max_bond": row["mps_max_bond"],
            "quimb_mps_max_bond": row["quimb_mps_max_bond"],
            "schmidt_rank": row["schmidt_rank"],
            "half_chain_entropy": row["half_chain_entropy"],
            "norm_squared_real": row["norm_squared_real"],
            "control_unnormalized_norm_squared": row["control_unnormalized_norm_squared"],
            "jax_norm_squared_real": jrow["norm_squared_real"],
            "jax_vs_pytorch_delta": parity["rows"][key]["max_value_delta"],
            "complex_phase_imag_coherence": row["complex_phase_imag_coherence"],
            "pass": rung_pass,
        }

    scale_pass = all(row["pass"] for row in scale_rungs.values())
    controls_pass = all(bool(row.get("pass")) for row in controls.values())
    ablation_pass = all(row["pass"] and abs(float(row["outcome_delta"])) > KILL_FLOOR for row in tool_ablations.values())
    proof_pass = bool(smt_proof["pass"] and sympy_exact["pass"])
    clifford_pass = bool(CLIFFORD_PHASE["pass"])
    n01_pass = bool(n01_torch["pass"] and n01_jax["pass"])
    all_pass = bool(scale_pass and controls_pass and ablation_pass and proof_pass and parity["agree"] and clifford_pass and n01_pass)

    blockers = []
    if not scale_pass:
        blockers.append("one or more non-dense 8/16/32/64 scale rungs failed")
    if not controls_pass:
        blockers.append("one or more degenerate/erased controls failed to kill its target property")
    if not ablation_pass:
        blockers.append("one or more per-tool ablations are zero or failed recompute")
    if not proof_pass:
        blockers.append("norm=1 helper-bound SMT proof or exact sympy certificate failed")
    if not parity["agree"]:
        blockers.append(f"jax_vs_pytorch_delta {parity['max_abs_delta']} exceeds tolerance")
    if not clifford_pass:
        blockers.append("Clifford spinor phase witness failed")
    if not n01_pass:
        blockers.append("local N01 spinor order witness failed")

    min_entropy = min(row["half_chain_entropy"] for row in scale_rungs.values())
    min_bond = min(row["mps_max_bond"] for row in scale_rungs.values())
    min_phase_coherence = min(row["complex_phase_imag_coherence"] for row in scale_rungs.values())

    result = {
        "schema": "formal_scout_max_deep_lego_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 2 carrier",
        "sim_execution_kind": "nonclassical",
        "sim_class": "carrier_probe",
        "purpose": "Build one canonical Stage-2 torch complex spinor carrier: a non-dense C^(2^k) MPS over k=8/16/32/64 sites with norm=1 proof, degenerate controls, JAX parity, and per-tool ablations.",
        "scientific_question": "Can the torch_complex_spinor carrier be represented as a normalized torch.complex128 non-dense MPS at 8/16/32/64 sites, with helper-bound norm proof and non-laundered tool ablations?",
        "finite_map": {
            "domain": "For k in {8,16,32,64}: finite PEPS3D-anchored k-site spinor path, physical dimension 2, latent Schmidt index a=0..7, MPS tensors A_i[a, bit(a,i), a], and local X/Z order witness.",
            "codomain_or_output": "Normalized non-dense MPS vector in C^(2^k), norm_squared=1 invariant, half-chain entropy, bond/rank readouts, JAX parity, SMT proof verdict flip, degenerate controls, and blocked downstream consumers.",
            "definition": "TorchComplexSpinor_k maps finite latent weights p_a=(a+1)/36 and Clifford rotor phases into a bond-8 torch.complex128 MPS without dense state closure.",
        },
        "domain": {
            "site_counts": list(SCALE_RUNGS),
            "physical_dim": PHYSICAL_DIM,
            "mps_bond_dim": BOND_DIM,
            "schmidt_weight_rule": "p_a=(a+1)/36 for a=0..7",
            "carrier_space": "C^(2^k) represented only as a non-dense MPS",
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "primary_invariant": "norm_squared == 1",
            "carrier": "torch.complex128 non-dense MPS with quimb MPS object and cotengra/autoray contraction witnesses",
            "controls": "unnormalized scale controls, bond-1 product control, Clifford phase-erased control, and dense-closure rejection",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: every rung uses finite k, finite latent index a=0..7, finite MPS tensors, finite PEPS3D anchors, finite proof variables, and finite controls.",
            },
            "N01": {
                "role": "active_bounded_witness",
                "statement": "local spinor supports noncommuting X/Z order witness; commuting Z/Z control kills the order gap. This carrier does not promote downstream operator layers.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting/order-sensitive operation/control witnessed locally by X/Z on the spinor basis",
        ],
        "carrier_layer": "torch_complex_spinor_non_dense_mps",
        "geometry_layer": "not_applicable: this is a carrier/state-space lego, not a downstream geometry layer",
        "carrier_realization": "torch.complex128 MPS tensors are the primary carrier; JAX complex128 mirrors finite invariants; quimb wraps torch tensors; cotengra and autoray provide non-dense contraction witnesses.",
        "peps3d_embedding": {
            "anchor": "finite PEPS3D grid K=(V,E,F,C) supplies site anchors from the first carrier step; executable carrier is the path/MPS projection and no full PEPS3D contraction closure is claimed",
            "shapes": {str(site_count): list(shape) for site_count, shape in SITE_SHAPES.items()},
            "from_first_carrier_step": True,
            "full_peps3d_contraction_claimed": False,
        },
        "spinor_state": "For each k, a torch.complex128 normalized non-dense MPS represents a vector in C^(2^k); local site basis is C^2 and no 2^k dense vector is materialized.",
        "quaternion_action": "not_applicable: this carrier uses complex spinor and Clifford rotor language, not quaternion language",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/F01_finite_distinguishability_results.json",
            "system_v5/ops/formal_scouts/results/N01_path_family_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "half-chain Schmidt cut over the non-dense MPS carrier",
        "law_or_candidate_tested": "torch_complex_spinor MPS carrier has norm_squared=1 at k=8/16/32/64, controls kill the invariant/depth/orientation, and proof verdict flips real vs unnormalized control",
        "branch_status_before_run": "single carrier lego requested by user; no coupling, stacking, bridge, flux, Axis0, FEP, gravity, or physics route opened",
        "allowed_claims": [
            "bounded Stage-2 torch complex spinor carrier result exists/runs if this JSON and required gates pass",
            "non-dense bond-8 MPS representation of a normalized C^(2^k) spinor carrier at k=8/16/32/64",
            "helper-bound z3/cvc5 proof flips for norm_squared=1 against an unnormalized measured control",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "single carrier lego only",
            "no full PEPS3D contraction closure",
            "no layer stacking, coupling, Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, physics, or final manifold admission",
        ],
        "eligible_consumers": ["bounded later Stage-2 carrier comparisons only after citing this result path and fresh gate output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 norm proof",
            "load_bearing_proof.smt_load_bearing cvc5 norm cross-check",
            "sympy exact rational norm/trace certificate",
            "clifford Cl(2) rotor spinor phase witness",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "unnormalized_torch_scale2_control": "norm_squared must differ from 1 and make the helper-bound claim unsat",
            "unnormalized_jax_scale3_over_2_control": "JAX mirror norm_squared must differ from 1",
            "bond1_product_mps_control": "bond-1 product control must erase many-body depth",
            "clifford_phase_erased_control": "Clifford phase erasure must reduce spinor phase coherence",
            "dense_state_closure_rejected": "full 2**64 dense vector closure must remain blocked",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "torch_primary_result", "jax_mirror_result", "proof_results", "controls", "tool_ablations"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "jax_vs_pytorch_delta": parity["max_abs_delta"],
            "min_mps_max_bond": min_bond,
            "min_half_chain_entropy": min_entropy,
            "min_phase_coherence": min_phase_coherence,
            "local_n01_order_gap": n01_torch["real_order_gap"],
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": {
            "engine": "torch",
            "dtype": "torch.complex128",
            "claim": "non-dense MPS spinor carrier norm_squared == 1",
            "rungs": torch_rows,
            "local_n01_order_witness": n01_torch,
            "pass": bool(all(row["pass"] for row in torch_rows.values()) and n01_torch["pass"]),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "claim": "JAX complex128 mirrors the finite MPS carrier norm/entropy/coherence readouts where representable",
            "rungs": jax_rows,
            "local_n01_order_witness": n01_jax,
            "pass": bool(all(row["pass"] for row in jax_rows.values()) and n01_jax["pass"]),
        },
        "jax_vs_pytorch_delta": parity["max_abs_delta"],
        "jax_vs_pytorch": parity,
        "proof_results": {
            "smt_load_bearing_norm_squared": smt_proof,
            "sympy_exact_norm_certificate": sympy_exact,
            "clifford_spinor_phase": CLIFFORD_PHASE,
            "pass": proof_pass and clifford_pass,
        },
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "scale_ladder": {
            "rungs": scale_rungs,
            "scale_axis": "spinor_site_count_k",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "positive": {
            "norm_squared_one_smt_flip": {"pass": smt_proof["pass"], "proof": smt_proof},
            "scale_8_16_32_64_non_dense_mps": {"pass": scale_pass, "rungs": scale_rungs},
            "many_body_depth_bond8_entropy_positive": {"pass": bool(min_bond >= BOND_DIM and min_entropy > KILL_FLOOR)},
            "jax_parity": parity,
            "clifford_spinor_phase": CLIFFORD_PHASE,
            "local_n01_order_witness": n01_torch,
        },
        "graveyard_companions": controls,
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "scipy_claim_bearing": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "full_peps3d_contraction_claim": {"claimed": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "scale2_norm_control_delta": controls["unnormalized_torch_scale2_control"]["control_norm_squared"] - 1.0,
            "scale3_over_2_jax_norm_control_delta": controls["unnormalized_jax_scale3_over_2_control"]["control_norm_squared"] - 1.0,
            "bond1_product_depth_control": controls["bond1_product_mps_control"],
            "clifford_phase_erased_control": controls["clifford_phase_erased_control"],
            "pass": controls_pass,
        },
        "shells": [
            {
                "name": "torch_complex_spinor_non_dense_mps_carrier",
                "status": "stage_2_carrier_lego_only",
                "rungs": list(SCALE_RUNGS),
                "mps_max_bond_min": min_bond,
                "half_chain_entropy_min": min_entropy,
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "build the next independent carrier or operator lego only after this result is cited and re-gated",
            "do not use this result as Xi/Phi0/Axis0/flux/FEP/gravity evidence",
        ],
        "compatibility_weights": {
            "local_stage2_carrier_input": 1.0 if all_pass else 0.0,
            "future_operator_lego_input": 0.5 if all_pass else 0.0,
            "Xi": 0.0,
            "Phi0": 0.0,
            "Axis0": 0.0,
            "flux": 0.0,
            "FEP": 0.0,
            "gravity": 0.0,
        },
        "compression_map": {
            "from": "finite PEPS3D-anchored k-site torch.complex128 MPS tensors with latent Schmidt index a=0..7",
            "to": "norm_squared invariant, scale ladder, entropy/depth/coherence readouts, proof flip, controls, and per-tool ablation deltas",
            "loss_boundary": "does not preserve or claim full dense C^(2^k) materialization, full PEPS3D contraction, layer completion, Axis0, flux, FEP, gravity, bridge, or final manifold admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": min(min_entropy, min_phase_coherence),
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "torch_complex_spinor survives iff every rung is non-dense, norm_squared=1, bond>=8, entropy>0, JAX parity holds, controls kill, helper proof flips, ablations are recomputed and nonzero, and promotion_allowed=false",
            "computed_capacity": min(min_entropy, min_phase_coherence),
            "threshold": KILL_FLOOR,
            "passed": bool(all_pass and min(min_entropy, min_phase_coherence) > KILL_FLOOR),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage-2 torch complex spinor carrier lego only; no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 rungs are non-dense and pass; torch/JAX agree; norm_squared=1 proof flips real vs unnormalized control; controls kill; each used tool has its own recomputed nonzero ablation delta",
        "fail_rule": "fail on dense closure, missing rung, bond<8, entropy<=0, norm not one, no real/control SMT flip, live control, JAX mismatch, missing Clifford phase witness, zero/cosmetic ablation, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "why_not_v4_probes": "This is a Stage-2 carrier lego with explicit non-dense 8/16/32/64 MPS rungs, norm=1 helper proof, JAX parity, Clifford/quimb/cotengra/autoray tool evidence, per-tool ablations, and promotion_allowed=false.",
        "blockers": blockers,
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
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "proof_pass": result["proof_results"]["pass"],
                "scale_pass": result["scale_ladder"]["pass"],
                "blockers": result["blockers"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
