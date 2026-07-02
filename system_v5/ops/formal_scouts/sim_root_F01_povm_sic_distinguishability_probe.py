#!/usr/bin/env python3
import jax
jax.config.update("jax_enable_x64", True)

import json
import pathlib
import sys
import time
from itertools import product
from typing import Any

import jax.numpy as jnp
import sympy as sp
import torch
import z3

sys.path.append("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
from load_bearing_proof import smt_load_bearing, tool_ablation


torch.set_default_dtype(torch.float64)

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "root_F01_povm_sic_distinguishability_probe"
OBJECT_ID = "F01_povm_sic"
OUT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
SCALE_DIMS = (8, 16, 32, 64)
EPS = 1.0e-9

BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": (
            "PRIMARY claim-bearing numeric engine: constructs torch complex128 "
            "density operators and product qubit-SIC POVM effects, then recomputes "
            "Born-response separation margins against the incomplete control."
        ),
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": (
            "parity MIRROR with x64 enabled before jax.numpy import; independently "
            "recomputes the same Born-response margins and reports JAX-vs-torch delta."
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "PROOF load-bearing through load_bearing_proof.smt_load_bearing: "
            "binds the measured real/control margins to Real variables and requires "
            "the separation claim to flip."
        ),
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": (
            "PROOF load-bearing cross-check through smt_load_bearing cvc5_claim_pairs; "
            "the same measured margin inequality flips under the incomplete control."
        ),
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "PROOF load-bearing symbolic mirror: exact product-SIC offdiagonal "
            "Born-response margin is recomputed and collapses for diagonal controls."
        ),
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used; NumPy is control-only and unnecessary for this F01 sim.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "not used; SciPy is control-only and unnecessary for this F01 sim.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive only: JSON emission, paths, timestamps, and finite product indexing.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "numpy": None,
    "scipy": None,
    "python_stdlib": "supportive",
}


def qubits_for_dim(dim: int) -> int:
    q = dim.bit_length() - 1
    if 2**q != dim:
        raise ValueError(f"dimension must be a power of two, got {dim}")
    return q


def torch_qubit_sic_effects() -> torch.Tensor:
    ctype = torch.complex128
    one = torch.tensor(1.0, dtype=torch.float64)
    inv_sqrt3 = one / torch.sqrt(torch.tensor(3.0, dtype=torch.float64))
    bloch = torch.tensor(
        [
            [1.0, 1.0, 1.0],
            [1.0, -1.0, -1.0],
            [-1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0],
        ],
        dtype=torch.float64,
    ) * inv_sqrt3
    identity = torch.eye(2, dtype=ctype)
    sigma_x = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=ctype)
    sigma_y = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=ctype)
    sigma_z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=ctype)
    effects = []
    for rx, ry, rz in bloch:
        effects.append((identity + rx * sigma_x + ry * sigma_y + rz * sigma_z) / 4.0)
    return torch.stack(effects)


def torch_basis_effects() -> torch.Tensor:
    zero = torch.zeros((2, 2), dtype=torch.complex128)
    e0 = zero.clone()
    e1 = zero.clone()
    e0[0, 0] = 1.0
    e1[1, 1] = 1.0
    return torch.stack([e0, e1])


def jax_qubit_sic_effects() -> jnp.ndarray:
    inv_sqrt3 = jnp.float64(1.0) / jnp.sqrt(jnp.float64(3.0))
    bloch = jnp.array(
        [
            [1.0, 1.0, 1.0],
            [1.0, -1.0, -1.0],
            [-1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0],
        ],
        dtype=jnp.float64,
    ) * inv_sqrt3
    identity = jnp.eye(2, dtype=jnp.complex128)
    sigma_x = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    sigma_y = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
    sigma_z = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    return jnp.stack(
        [(identity + rx * sigma_x + ry * sigma_y + rz * sigma_z) / 4.0 for rx, ry, rz in bloch]
    )


def jax_basis_effects() -> jnp.ndarray:
    e0 = jnp.array([[1.0, 0.0], [0.0, 0.0]], dtype=jnp.complex128)
    e1 = jnp.array([[0.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
    return jnp.stack([e0, e1])


def torch_density_pair(dim: int) -> tuple[torch.Tensor, torch.Tensor]:
    rho_plus = torch.zeros((dim, dim), dtype=torch.complex128)
    rho_minus = torch.zeros((dim, dim), dtype=torch.complex128)
    last = dim - 1
    for rho, sign in ((rho_plus, 1.0), (rho_minus, -1.0)):
        rho[0, 0] = 0.5
        rho[last, last] = 0.5
        rho[0, last] = 0.5 * sign
        rho[last, 0] = 0.5 * sign
    return rho_plus, rho_minus


def jax_density_pair(dim: int) -> tuple[jnp.ndarray, jnp.ndarray]:
    rho_plus = jnp.zeros((dim, dim), dtype=jnp.complex128)
    rho_minus = jnp.zeros((dim, dim), dtype=jnp.complex128)
    last = dim - 1
    rho_plus = rho_plus.at[0, 0].set(0.5)
    rho_plus = rho_plus.at[last, last].set(0.5)
    rho_plus = rho_plus.at[0, last].set(0.5)
    rho_plus = rho_plus.at[last, 0].set(0.5)
    rho_minus = rho_minus.at[0, 0].set(0.5)
    rho_minus = rho_minus.at[last, last].set(0.5)
    rho_minus = rho_minus.at[0, last].set(-0.5)
    rho_minus = rho_minus.at[last, 0].set(-0.5)
    return rho_plus, rho_minus


def bit_at(index: int, qubits: int, q: int) -> int:
    return (index >> (qubits - q - 1)) & 1


def torch_delta_entries(delta: torch.Tensor) -> list[tuple[int, int, complex]]:
    nz = torch.nonzero(torch.abs(delta) > 0.0, as_tuple=False)
    return [(int(i), int(j), complex(delta[int(i), int(j)].item())) for i, j in nz]


def jax_delta_entries(delta: jnp.ndarray) -> list[tuple[int, int, complex]]:
    rows, cols = jnp.nonzero(jnp.abs(delta) > 0.0)
    return [(int(i), int(j), complex(delta[int(i), int(j)])) for i, j in zip(rows.tolist(), cols.tolist())]


def torch_born_response_for_product_effect(
    entries: list[tuple[int, int, complex]],
    local_effects: torch.Tensor,
    effect_ids: tuple[int, ...],
    qubits: int,
) -> torch.Tensor:
    response = torch.tensor(0.0 + 0.0j, dtype=torch.complex128)
    for row, col, value in entries:
        matrix_entry = torch.tensor(1.0 + 0.0j, dtype=torch.complex128)
        for q, effect_id in enumerate(effect_ids):
            row_bit = bit_at(row, qubits, q)
            col_bit = bit_at(col, qubits, q)
            matrix_entry = matrix_entry * local_effects[effect_id, col_bit, row_bit]
        response = response + torch.tensor(value, dtype=torch.complex128) * matrix_entry
    return response


def jax_born_response_for_product_effect(
    entries: list[tuple[int, int, complex]],
    local_effects: jnp.ndarray,
    effect_ids: tuple[int, ...],
    qubits: int,
) -> jnp.ndarray:
    response = jnp.array(0.0 + 0.0j, dtype=jnp.complex128)
    for row, col, value in entries:
        matrix_entry = jnp.array(1.0 + 0.0j, dtype=jnp.complex128)
        for q, effect_id in enumerate(effect_ids):
            row_bit = bit_at(row, qubits, q)
            col_bit = bit_at(col, qubits, q)
            matrix_entry = matrix_entry * local_effects[effect_id, col_bit, row_bit]
        response = response + jnp.array(value, dtype=jnp.complex128) * matrix_entry
    return response


def torch_response_margin(dim: int, local_effects: torch.Tensor) -> dict[str, Any]:
    qubits = qubits_for_dim(dim)
    rho_i, rho_j = torch_density_pair(dim)
    delta = rho_i - rho_j
    entries = torch_delta_entries(delta)
    effect_tuples = list(product(range(int(local_effects.shape[0])), repeat=qubits))
    responses = torch.stack(
        [
            torch_born_response_for_product_effect(entries, local_effects, effect_ids, qubits)
            for effect_ids in effect_tuples
        ]
    )
    abs_responses = torch.abs(responses)
    max_idx = int(torch.argmax(abs_responses).item())
    margin = float(abs_responses[max_idx].item())
    completeness = torch.zeros((2, 2), dtype=torch.complex128)
    for effect in local_effects:
        completeness = completeness + effect
    completeness_error = float(torch.linalg.matrix_norm(completeness - torch.eye(2, dtype=torch.complex128)).item())
    return {
        "engine": "torch",
        "hilbert_dim": dim,
        "qubits": qubits,
        "effect_count": len(effect_tuples),
        "dtype": "torch.complex128",
        "density_trace_rho_i": float(torch.trace(rho_i).real.item()),
        "density_trace_rho_j": float(torch.trace(rho_j).real.item()),
        "density_delta_nonzero_entries": len(entries),
        "local_povm_completeness_error": completeness_error,
        "separation_margin": margin,
        "max_effect_index": list(effect_tuples[max_idx]),
        "max_response_real": float(responses[max_idx].real.item()),
        "max_response_imag": float(responses[max_idx].imag.item()),
        "dense_state_closure_used": False,
        "pass": bool(margin >= EPS and completeness_error <= 1.0e-12),
    }


def jax_response_margin(dim: int, local_effects: jnp.ndarray) -> dict[str, Any]:
    qubits = qubits_for_dim(dim)
    rho_i, rho_j = jax_density_pair(dim)
    delta = rho_i - rho_j
    entries = jax_delta_entries(delta)
    effect_tuples = list(product(range(int(local_effects.shape[0])), repeat=qubits))
    responses = jnp.stack(
        [
            jax_born_response_for_product_effect(entries, local_effects, effect_ids, qubits)
            for effect_ids in effect_tuples
        ]
    )
    abs_responses = jnp.abs(responses)
    max_idx = int(jnp.argmax(abs_responses))
    margin = float(abs_responses[max_idx])
    completeness = jnp.sum(local_effects, axis=0)
    completeness_error = float(jnp.linalg.norm(completeness - jnp.eye(2, dtype=jnp.complex128)))
    return {
        "engine": "jax",
        "hilbert_dim": dim,
        "qubits": qubits,
        "effect_count": len(effect_tuples),
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "density_delta_nonzero_entries": len(entries),
        "local_povm_completeness_error": completeness_error,
        "separation_margin": margin,
        "max_effect_index": list(effect_tuples[max_idx]),
        "max_response_real": float(jnp.real(responses[max_idx])),
        "max_response_imag": float(jnp.imag(responses[max_idx])),
        "dense_state_closure_used": False,
        "pass": bool(margin >= EPS and completeness_error <= 1.0e-12),
    }


def sympy_response_margin(dim: int, *, use_sic: bool = True) -> dict[str, Any]:
    qubits = qubits_for_dim(dim)
    sqrt3 = sp.sqrt(3)
    i = sp.I
    if use_sic:
        bloch = [
            (sp.Integer(1), sp.Integer(1), sp.Integer(1)),
            (sp.Integer(1), sp.Integer(-1), sp.Integer(-1)),
            (sp.Integer(-1), sp.Integer(1), sp.Integer(-1)),
            (sp.Integer(-1), sp.Integer(-1), sp.Integer(1)),
        ]
        local_offdiagonal = [(rx / sqrt3 - i * ry / sqrt3) / 4 for rx, ry, _ in bloch]
        exact_family = "tensor product of exact qubit SIC effects (I + r.sigma)/4"
    else:
        local_offdiagonal = [sp.Integer(0), sp.Integer(0)]
        exact_family = "tensor product of exact diagonal computational-basis effects"
    best_abs = sp.Integer(0)
    best_tuple: tuple[int, ...] | None = None
    best_response = sp.Integer(0)
    for effect_ids in product(range(len(local_offdiagonal)), repeat=qubits):
        product_entry = sp.Integer(1)
        for effect_id in effect_ids:
            product_entry *= local_offdiagonal[effect_id]
        response = sp.simplify(product_entry + sp.conjugate(product_entry))
        response_abs = abs(complex(sp.N(response, 40)))
        if best_tuple is None or response_abs > float(sp.N(best_abs, 40)):
            best_abs = sp.Abs(response)
            best_tuple = effect_ids
            best_response = response
    margin = float(sp.N(best_abs, 40))
    return {
        "engine": "sympy",
        "exact_family": exact_family,
        "hilbert_dim": dim,
        "qubits": qubits,
        "effect_count": len(local_offdiagonal) ** qubits,
        "exact_best_response": str(sp.simplify(best_response)),
        "exact_best_abs": str(sp.simplify(best_abs)),
        "best_effect_index": list(best_tuple or ()),
        "separation_margin": margin,
        "pass": bool(margin >= EPS) if use_sic else bool(margin < EPS),
    }


def informational_completeness_witness() -> dict[str, Any]:
    sqrt3 = sp.sqrt(3)
    i = sp.I
    bloch = [
        (sp.Integer(1), sp.Integer(1), sp.Integer(1)),
        (sp.Integer(1), sp.Integer(-1), sp.Integer(-1)),
        (sp.Integer(-1), sp.Integer(1), sp.Integer(-1)),
        (sp.Integer(-1), sp.Integer(-1), sp.Integer(1)),
    ]
    rows = []
    for rx, ry, rz in bloch:
        effect = sp.Matrix(
            [
                [(1 + rz / sqrt3) / 4, (rx / sqrt3 - i * ry / sqrt3) / 4],
                [(rx / sqrt3 + i * ry / sqrt3) / 4, (1 - rz / sqrt3) / 4],
            ]
        )
        rows.append([effect[0, 0], effect[0, 1], effect[1, 0], effect[1, 1]])
    local_rank = sp.Matrix(rows).rank()
    return {
        "effect_family": "tensor product of local qubit SIC POVMs",
        "local_operator_span_rank": int(local_rank),
        "local_operator_space_dim": 4,
        "product_ic_reason": "rank-4 local SIC effects tensor to a dimension^2 product effect frame on (C^2)^m",
        "global_equiangular_sic_claimed": False,
        "pass": bool(local_rank == 4),
    }


def proof_for_margins(real_margin: float, control_margin: float) -> dict[str, Any]:
    return smt_load_bearing(
        "Born responses separate rho_i,rho_j: max_p |Tr((rho_i-rho_j) E_p)| >= eps",
        real_measured={"margin": real_margin, "eps": EPS},
        control_measured={"margin": control_margin, "eps": EPS},
        claim_builder=lambda v: v["margin"] >= v["eps"],
        cvc5_claim_pairs=[("margin", ">=", "eps")],
    )


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
    raise ValueError(f"unknown proof engine: {engine}")


def aggregate_proof_flip_score(proofs: dict[str, Any], engine: str) -> float:
    return float(all(proof_flip_score(proof, engine) == 1.0 for proof in proofs.values()))


def build_result() -> dict[str, Any]:
    started = time.time()
    torch_sic = torch_qubit_sic_effects()
    torch_control = torch_basis_effects()
    jax_sic = jax_qubit_sic_effects()
    jax_control = jax_basis_effects()
    ic_witness = informational_completeness_witness()

    torch_rungs: dict[str, Any] = {}
    jax_rungs: dict[str, Any] = {}
    sympy_rungs: dict[str, Any] = {}
    sympy_control_rungs: dict[str, Any] = {}
    proof_rungs: dict[str, Any] = {}
    proof_erased_rungs: dict[str, Any] = {}
    scale_rungs: dict[str, Any] = {}

    for dim in SCALE_DIMS:
        key = str(dim)
        torch_full = torch_response_margin(dim, torch_sic)
        torch_reduced = torch_response_margin(dim, torch_control)
        jax_full = jax_response_margin(dim, jax_sic)
        jax_reduced = jax_response_margin(dim, jax_control)
        sympy_full = sympy_response_margin(dim, use_sic=True)
        sympy_reduced = sympy_response_margin(dim, use_sic=False)
        proof = proof_for_margins(torch_full["separation_margin"], torch_reduced["separation_margin"])
        proof_erased = proof_for_margins(torch_full["separation_margin"], torch_full["separation_margin"])
        torch_rungs[key] = {"full_sic": torch_full, "incomplete_control": torch_reduced}
        jax_rungs[key] = {"full_sic": jax_full, "incomplete_control": jax_reduced}
        sympy_rungs[key] = sympy_full
        sympy_control_rungs[key] = sympy_reduced
        proof_rungs[key] = proof
        proof_erased_rungs[key] = proof_erased
        scale_rungs[key] = {
            "sites_or_qubits": dim,
            "hilbert_dim": dim,
            "qubits": qubits_for_dim(dim),
            "full_sic_effect_count": torch_full["effect_count"],
            "incomplete_control_effect_count": torch_reduced["effect_count"],
            "dense_state_closure_used": False,
            "torch_separation_margin": torch_full["separation_margin"],
            "torch_control_margin": torch_reduced["separation_margin"],
            "jax_separation_margin": jax_full["separation_margin"],
            "jax_control_margin": jax_reduced["separation_margin"],
            "sympy_separation_margin": sympy_full["separation_margin"],
            "sympy_control_margin": sympy_reduced["separation_margin"],
            "informationally_complete_product_povm": bool(
                ic_witness["pass"] and torch_full["effect_count"] == dim * dim
            ),
            "proof_verdict_flips": bool(proof["differ"]),
            "pass": bool(
                torch_full["pass"]
                and torch_reduced["separation_margin"] < EPS
                and jax_full["pass"]
                and jax_reduced["separation_margin"] < EPS
                and sympy_full["pass"]
                and sympy_reduced["pass"]
                and ic_witness["pass"]
                and proof["differ"]
            ),
        }

    max_jax_delta = max(
        abs(
            torch_rungs[str(dim)]["full_sic"]["separation_margin"]
            - jax_rungs[str(dim)]["full_sic"]["separation_margin"]
        )
        for dim in SCALE_DIMS
    )
    min_torch_margin = min(torch_rungs[str(dim)]["full_sic"]["separation_margin"] for dim in SCALE_DIMS)
    max_control_margin = max(torch_rungs[str(dim)]["incomplete_control"]["separation_margin"] for dim in SCALE_DIMS)

    sympy_baseline = min(sympy_rungs[str(dim)]["separation_margin"] for dim in SCALE_DIMS)
    sympy_control = max(sympy_control_rungs[str(dim)]["separation_margin"] for dim in SCALE_DIMS)
    jax_baseline = min(jax_rungs[str(dim)]["full_sic"]["separation_margin"] for dim in SCALE_DIMS)
    jax_control_margin = max(jax_rungs[str(dim)]["incomplete_control"]["separation_margin"] for dim in SCALE_DIMS)
    z3_flip_score = aggregate_proof_flip_score(proof_rungs, "z3")
    z3_erased_score = aggregate_proof_flip_score(proof_erased_rungs, "z3")
    cvc5_flip_score = aggregate_proof_flip_score(proof_rungs, "cvc5")
    cvc5_erased_score = aggregate_proof_flip_score(proof_erased_rungs, "cvc5")

    tool_ablations = {
        "torch": tool_ablation(
            "torch Born-response margin recomputed after removing the informationally-complete SIC effect family",
            baseline_value=min_torch_margin,
            ablated_value=max_control_margin,
            tool="torch",
        ),
        "jax": tool_ablation(
            "jax Born-response parity margin recomputed after removing the informationally-complete SIC effect family",
            baseline_value=jax_baseline,
            ablated_value=jax_control_margin,
            tool="jax",
        ),
        "z3": tool_ablation(
            "z3 own flip-score from smt_load_bearing real Born separation vs same-input decoupled control",
            baseline_value=z3_flip_score,
            ablated_value=z3_erased_score,
            tool="z3",
        ),
        "cvc5": tool_ablation(
            "cvc5 own flip-score from smt_load_bearing cvc5_claim_pairs vs same-input decoupled control",
            baseline_value=cvc5_flip_score,
            ablated_value=cvc5_erased_score,
            tool="cvc5",
        ),
        "sympy": tool_ablation(
            "sympy exact symbolic Born-response margin recomputed with the SIC offdiagonal symbolic step removed",
            baseline_value=sympy_baseline,
            ablated_value=sympy_control,
            tool="sympy",
        ),
    }

    scale_pass = all(rung["pass"] for rung in scale_rungs.values())
    proof_pass = all(
        row["differ"]
        and row["real_claim_verdict"] == "sat"
        and row["negated_claim_verdict"] == "unsat"
        and row.get("cvc5_real_verdict") == "sat"
        and row.get("cvc5_control_verdict") == "unsat"
        for row in proof_rungs.values()
    )
    ablation_pass = all(abs(row["outcome_delta"]) > EPS for row in tool_ablations.values())
    required_pass = bool(scale_pass and proof_pass and ablation_pass and max_jax_delta <= 1.0e-12)

    return {
        "schema": "PER_SIM_CONTRACT_ROOT_STAGE1_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "tier": "stage_1_root_constraint",
        "sim_execution_kind": "nonclassical",
        "sim_class": "constraint_probe",
        "finite_map": {
            "domain": "density operators rho_i,rho_j on Hilbert dimensions 8,16,32,64 and finite product qubit-SIC POVM effects E_p",
            "codomain_or_output": "Born-response vector p -> Tr(rho E_p) and pair separation margin max_p |Tr((rho_i-rho_j)E_p)|",
        },
        "domain": "finite density-operator pairs and finite POVM effect families over dimensions 8,16,32,64",
        "codomain_or_output": "finite Born-response vectors and separation margins",
        "root_constraints": {
            "F01": {
                "role": "active",
                "description": "finite carrier/probe/effect set; product qubit-SIC POVM separates the tested density operators",
            },
            "N01": {
                "role": "referenced_not_promoted",
                "description": "finite tensor-product effect ordering is fixed for reproducible probes; no N01 noncommutation claim is promoted by this F01 sim",
            },
        },
        "root_constraints_in_force": ["F01_finite_povm_response_distinguishability", "N01_referenced_not_promoted"],
        "law_or_candidate_tested": "Born responses from an informationally complete product-SIC POVM separate a coherence-only density-pair that incomplete diagonal effects cannot separate",
        "torch_primary_result": {
            "engine": "torch",
            "dtype": "torch.complex128",
            "claim": "product qubit-SIC Born responses separate rho_i and rho_j; incomplete diagonal controls do not",
            "rungs": torch_rungs,
            "min_full_sic_margin": min_torch_margin,
            "max_incomplete_control_margin": max_control_margin,
            "pass": all(
                torch_rungs[str(dim)]["full_sic"]["pass"]
                and torch_rungs[str(dim)]["incomplete_control"]["separation_margin"] < EPS
                for dim in SCALE_DIMS
            ),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "x64_enabled": bool(jax.config.read("jax_enable_x64")),
            "claim": "JAX parity mirror recomputes the same finite Born-response separation margins",
            "rungs": jax_rungs,
            "pass": all(
                jax_rungs[str(dim)]["full_sic"]["pass"]
                and jax_rungs[str(dim)]["incomplete_control"]["separation_margin"] < EPS
                for dim in SCALE_DIMS
            ),
        },
        "jax_vs_pytorch_delta": max_jax_delta,
        "proof_results": {
            "born_response_separation_smt_load_bearing": proof_rungs,
            "sympy_exact_product_sic_margin": sympy_rungs,
            "sympy_exact_incomplete_control_margin": sympy_control_rungs,
            "informational_completeness_witness": ic_witness,
            "all_smt_verdicts_flip": proof_pass,
            "helper_used": "load_bearing_proof.smt_load_bearing",
        },
        "controls": {
            "negative_control_carriers_used": {
                "incomplete_computational_basis_povm": {
                    "description": "diagonal product-basis POVM sees the same diagonal probabilities for rho_i and rho_j and erases coherence",
                    "max_control_margin": max_control_margin,
                    "effect_count_by_dim": {str(dim): torch_rungs[str(dim)]["incomplete_control"]["effect_count"] for dim in SCALE_DIMS},
                    "pass": bool(max_control_margin < EPS),
                },
                "probe_erased_or_reduced_effect_set": {
                    "description": "full product qubit-SIC effect family is replaced by a non-IC diagonal effect set before recomputing the observable",
                    "baseline_min_margin": min_torch_margin,
                    "ablated_max_margin": max_control_margin,
                    "kills_claim": bool(min_torch_margin >= EPS and max_control_margin < EPS),
                },
                "proof_engine_erased_or_decoupled": {
                    "description": "SMT proof engines are fed the same measured Born separation on real and control sides, so the engine-local flip cannot occur",
                    "z3_flip_score": z3_flip_score,
                    "z3_erased_score": z3_erased_score,
                    "cvc5_flip_score": cvc5_flip_score,
                    "cvc5_erased_score": cvc5_erased_score,
                    "pass": bool(
                        z3_flip_score == 1.0
                        and z3_erased_score == 0.0
                        and cvc5_flip_score == 1.0
                        and cvc5_erased_score == 0.0
                    ),
                },
            }
        },
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "scale_ladder": {
            "rungs": scale_rungs,
            "scale_axis": "Hilbert dimension; product-SIC effect count is dimension^2",
            "dense_state_closure_used": False,
            "pass": scale_pass,
        },
        "resource_blocker": None,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "allowed_claims": [
            "F01 finite POVM response distinguishability for the tested density-pair only",
            "local stage-1 lego evidence only",
        ],
        "promotion_blockers": [
            "does not test Xi",
            "does not test Phi0",
            "does not test Axis0",
            "does not test flux",
            "does not test FEP",
            "does not test gravity",
            "does not promote N01",
            "does not establish a global equiangular SIC theorem",
        ],
        "classification": "lego",
        "promotion_allowed": False,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["load_bearing_proof.smt_load_bearing", "sympy_exact_product_sic_margin"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "divergence_log": [],
        "required_pass": required_pass,
        "all_pass": required_pass,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result_path": str(OUT_PATH.relative_to(ROOT)), "required_pass": result["required_pass"]}, indent=2))
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
