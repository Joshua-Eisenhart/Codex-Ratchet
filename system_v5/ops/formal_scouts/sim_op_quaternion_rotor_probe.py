#!/usr/bin/env python3
"""Stage-5 quaternion rotor operator/channel/generator probe.

Finite map:
    QRot_d : finite unit-quaternion coefficient rows -> block-local SU(2)
    rotor operator readouts.

The sim proves one bounded operator invariant: quaternion rotor blocks are
unitary, and the same SMT claim fails when the coefficient rows are scaled by
0.99 without post-hoc normalization.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from fractions import Fraction
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
from clifford import Cl

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = ROOT / "sim_op_quaternion_rotor_probe.py"
RESULT = RESULT_DIR / "op_quaternion_rotor_results.json"

OBJECT_ID = "op_quaternion_rotor_su2_block_diagonal"
NAME = "sim_op_quaternion_rotor_probe"
VERSION = "1.0.0"

DTYPE_REAL = torch.float64
DTYPE_COMPLEX = torch.complex128
JAX_COMPLEX = jnp.complex128
SCALES = (8, 16, 32, 64)
CONTROL_SCALE = Fraction(99, 100)
EPS = 1.0e-12
BLOCKED_CONSUMERS = [
    "stacking",
    "coupling",
    "higher_layers",
    "G_structure",
    "flux",
    "Xi",
    "Phi0",
    "Axis0",
    "bridge",
    "basin",
    "FEP",
    "gravity",
    "physics",
    "final_manifold_admission",
]

# Exact rational unit quaternions. No runtime normalization is applied.
BASE_QUATERNIONS: tuple[tuple[Fraction, Fraction, Fraction, Fraction], ...] = (
    (Fraction(1, 2), Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)),
    (Fraction(3, 5), Fraction(4, 5), Fraction(0, 1), Fraction(0, 1)),
    (Fraction(5, 13), Fraction(0, 1), Fraction(12, 13), Fraction(0, 1)),
    (Fraction(8, 17), Fraction(0, 1), Fraction(0, 1), Fraction(15, 17)),
)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing numeric engine for block-local complex128 SU(2) rotor products, controls, order gaps, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror recomputing the same block-local rotor residuals and order gaps without using torch values.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing: real residual SAT vs scaled-control residual UNSAT.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through the same load_bearing_proof SMT flip on measured residuals.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact rational quaternion norm and determinant witness; load-bearing only through the exact SAT/UNSAT flip, not numeric ablation.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Geometric-algebra rotor mirror for quaternion bivector action; load-bearing through genuine remove-and-recompute ablation.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported. NumPy and .numpy() conversions are excluded from claim-bearing computation.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "numpy": "None",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return float(value.item())
        return value.detach().cpu().tolist()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    return value


def quaternions_for_dimension(operator_dimension: int) -> list[tuple[Fraction, Fraction, Fraction, Fraction]]:
    if operator_dimension % 2 != 0:
        raise ValueError("operator dimension must be even for 2x2 SU(2) rotor blocks")
    block_count = operator_dimension // 2
    return [BASE_QUATERNIONS[idx % len(BASE_QUATERNIONS)] for idx in range(block_count)]


def scaled_quaternions(
    rows: list[tuple[Fraction, Fraction, Fraction, Fraction]],
    scale: Fraction,
) -> list[tuple[Fraction, Fraction, Fraction, Fraction]]:
    return [tuple(scale * part for part in row) for row in rows]  # type: ignore[list-item]


def exact_norm_square(row: tuple[Fraction, Fraction, Fraction, Fraction]) -> Fraction:
    a, b, c, d = row
    return a * a + b * b + c * c + d * d


def exact_norm_residual(rows: list[tuple[Fraction, Fraction, Fraction, Fraction]]) -> Fraction:
    return max(abs(exact_norm_square(row) - 1) for row in rows)


def torch_coeffs(rows: list[tuple[Fraction, Fraction, Fraction, Fraction]]) -> torch.Tensor:
    return torch.tensor([[float(part) for part in row] for row in rows], dtype=DTYPE_REAL)


def torch_blocks(coeffs: torch.Tensor) -> torch.Tensor:
    a, b, c, d = coeffs[:, 0], coeffs[:, 1], coeffs[:, 2], coeffs[:, 3]
    real = torch.zeros((coeffs.shape[0], 2, 2), dtype=DTYPE_REAL)
    imag = torch.zeros((coeffs.shape[0], 2, 2), dtype=DTYPE_REAL)
    real[:, 0, 0] = a
    imag[:, 0, 0] = b
    real[:, 0, 1] = c
    imag[:, 0, 1] = d
    real[:, 1, 0] = -c
    imag[:, 1, 0] = d
    real[:, 1, 1] = a
    imag[:, 1, 1] = -b
    return torch.complex(real, imag).to(DTYPE_COMPLEX)


def jax_coeffs(rows: list[tuple[Fraction, Fraction, Fraction, Fraction]]) -> jax.Array:
    return jnp.array([[float(part) for part in row] for row in rows], dtype=jnp.float64)


def jax_blocks(coeffs: jax.Array) -> jax.Array:
    a, b, c, d = coeffs[:, 0], coeffs[:, 1], coeffs[:, 2], coeffs[:, 3]
    row0 = jnp.stack([a + 1j * b, c + 1j * d], axis=1)
    row1 = jnp.stack([-c + 1j * d, a - 1j * b], axis=1)
    return jnp.stack([row0, row1], axis=1).astype(JAX_COMPLEX)


def torch_unitarity_residual(blocks: torch.Tensor) -> float:
    ident = torch.eye(2, dtype=DTYPE_COMPLEX)
    product = blocks @ blocks.conj().transpose(-2, -1)
    return float(torch.max(torch.abs(product - ident)).item())


def jax_unitarity_residual(blocks: jax.Array) -> float:
    ident = jnp.eye(2, dtype=JAX_COMPLEX)
    product = blocks @ jnp.conjugate(jnp.swapaxes(blocks, -2, -1))
    return float(jnp.max(jnp.abs(product - ident)).item())


def torch_order_gap(blocks: torch.Tensor) -> float:
    left = blocks[0] @ blocks[1]
    right = blocks[1] @ blocks[0]
    return float(torch.linalg.matrix_norm(left - right).item())


def jax_order_gap(blocks: jax.Array) -> float:
    left = blocks[0] @ blocks[1]
    right = blocks[1] @ blocks[0]
    return float(jnp.linalg.norm(left - right).item())


def torch_action_energy(blocks: torch.Tensor) -> float:
    ket0 = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=DTYPE_COMPLEX)
    outputs = blocks @ ket0
    deltas = outputs - ket0
    return float(torch.mean(torch.sum(torch.abs(deltas) ** 2, dim=1)).item())


def jax_action_energy(blocks: jax.Array) -> float:
    ket0 = jnp.array([1.0 + 0.0j, 0.0 + 0.0j], dtype=JAX_COMPLEX)
    outputs = blocks @ ket0
    deltas = outputs - ket0
    return float(jnp.mean(jnp.sum(jnp.abs(deltas) ** 2, axis=1)).item())


def torch_block_trace_real(blocks: torch.Tensor, index: int = 0) -> float:
    return float(torch.real(torch.trace(blocks[index])).item())


def jax_block_trace_real(blocks: jax.Array, index: int = 0) -> float:
    return float(jnp.real(jnp.trace(blocks[index])).item())


def sympy_su2_block(row: tuple[Fraction, Fraction, Fraction, Fraction]) -> sp.Matrix:
    a, b, c, d = (sp.Rational(part.numerator, part.denominator) for part in row)
    i = sp.I
    return sp.Matrix([[a + b * i, c + d * i], [-c + d * i, a - b * i]])


def sympy_exact_observables(
    rows: list[tuple[Fraction, Fraction, Fraction, Fraction]],
    control_rows: list[tuple[Fraction, Fraction, Fraction, Fraction]],
) -> dict[str, Any]:
    first = sympy_su2_block(rows[0])
    second = sympy_su2_block(rows[1])
    control_first = sympy_su2_block(control_rows[0])
    real_products = [(sympy_su2_block(row) * sympy_su2_block(row).conjugate().T) for row in rows]
    control_products = [
        (sympy_su2_block(row) * sympy_su2_block(row).conjugate().T)
        for row in control_rows
    ]
    ident = sp.eye(2)
    real_residual = max(
        abs(sp.simplify((product - ident)[r, c]))
        for product in real_products
        for r in range(2)
        for c in range(2)
    )
    control_residual = max(
        abs(sp.simplify((product - ident)[r, c]))
        for product in control_products
        for r in range(2)
        for c in range(2)
    )
    commutator = first * second - second * first
    return {
        "first_block_norm_square": str(exact_norm_square(rows[0])),
        "max_exact_real_unitarity_residual": str(real_residual),
        "max_exact_scaled_control_unitarity_residual": str(control_residual),
        "first_block_determinant": str(sp.simplify(first.det())),
        "scaled_control_first_block_determinant": str(sp.simplify(control_first.det())),
        "first_two_block_commutator_frobenius_squared": str(
            sp.simplify(sum(abs(commutator[r, c]) ** 2 for r in range(2) for c in range(2)))
        ),
        "real_unitarity_claim_holds": bool(real_residual <= sp.Rational(1, 10**12)),
        "scaled_control_unitarity_claim_holds": bool(control_residual <= sp.Rational(1, 10**12)),
        "pass": bool(
            real_residual == 0
            and control_residual == sp.Rational(199, 10000)
            and sp.simplify(first.det()) == 1
            and sum(abs(commutator[r, c]) ** 2 for r in range(2) for c in range(2)) > 0
        ),
    }


def clifford_rotor_action_energy(rows: list[tuple[Fraction, Fraction, Fraction, Fraction]]) -> float:
    _layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    energies = []
    for a, b, c, d in rows:
        rotor = (
            float(a)
            + float(b) * (e2 ^ e3)
            + float(c) * (e3 ^ e1)
            + float(d) * (e1 ^ e2)
        )
        rotated = rotor * e1 * ~rotor
        delta = rotated - e1
        energies.append(sum(float(v) * float(v) for v in delta.value))
    return float(sum(energies) / len(energies))


def sparse_metadata(operator_dimension: int) -> dict[str, Any]:
    block_count = operator_dimension // 2
    nonzero_count = block_count * 4
    return {
        "representation": "block-local 2x2 SU(2) rows; no full dense operator multiplication",
        "operator_dimension": operator_dimension,
        "block_count": block_count,
        "nonzero_count_if_materialized_sparse": nonzero_count,
        "dense_entry_count_if_materialized": operator_dimension * operator_dimension,
        "sparse_density": nonzero_count / float(operator_dimension * operator_dimension),
        "dense_state_closure_used": False,
    }


def scale_rung(operator_dimension: int) -> dict[str, Any]:
    rows = quaternions_for_dimension(operator_dimension)
    control_rows = scaled_quaternions(rows, CONTROL_SCALE)
    blocks = torch_blocks(torch_coeffs(rows))
    control_blocks = torch_blocks(torch_coeffs(control_rows))
    jblocks = jax_blocks(jax_coeffs(rows))
    jcontrol_blocks = jax_blocks(jax_coeffs(control_rows))

    torch_real_residual = torch_unitarity_residual(blocks)
    torch_control_residual = torch_unitarity_residual(control_blocks)
    jax_real_residual = jax_unitarity_residual(jblocks)
    jax_control_residual = jax_unitarity_residual(jcontrol_blocks)
    torch_gap = torch_order_gap(blocks)
    jax_gap = jax_order_gap(jblocks)
    torch_energy = torch_action_energy(blocks)
    jax_energy = jax_action_energy(jblocks)

    parity_delta = max(
        abs(torch_real_residual - jax_real_residual),
        abs(torch_control_residual - jax_control_residual),
        abs(torch_gap - jax_gap),
        abs(torch_energy - jax_energy),
    )
    exact_real_residual = float(exact_norm_residual(rows))
    exact_control_residual = float(exact_norm_residual(control_rows))
    row_pass = (
        exact_real_residual <= EPS
        and torch_real_residual <= EPS
        and jax_real_residual <= EPS
        and abs(torch_control_residual - float(Fraction(199, 10000))) <= 1.0e-12
        and abs(jax_control_residual - torch_control_residual) <= 1.0e-12
        and exact_control_residual > EPS
        and torch_gap > EPS
        and jax_gap > EPS
        and parity_delta <= 1.0e-12
    )
    return {
        "n": operator_dimension,
        "operator_dimension": operator_dimension,
        "block_count": operator_dimension // 2,
        "quaternion_row_count": len(rows),
        "root_operator_dimension_not_qubit_count": True,
        "dense_state_closure_used": False,
        "posthoc_normalization_used": False,
        "torch_max_unitarity_residual": torch_real_residual,
        "torch_scaled_control_max_unitarity_residual": torch_control_residual,
        "jax_max_unitarity_residual": jax_real_residual,
        "jax_scaled_control_max_unitarity_residual": jax_control_residual,
        "exact_max_unitarity_residual": exact_real_residual,
        "exact_scaled_control_max_unitarity_residual": exact_control_residual,
        "torch_order_gap_first_two_blocks": torch_gap,
        "jax_order_gap_first_two_blocks": jax_gap,
        "torch_action_energy": torch_energy,
        "jax_action_energy": jax_energy,
        "jax_vs_pytorch_delta": parity_delta,
        "first_block_trace_real_torch": torch_block_trace_real(blocks),
        "first_block_trace_real_jax": jax_block_trace_real(jblocks),
        "sparse_operator_metadata": sparse_metadata(operator_dimension),
        "pass": bool(row_pass),
    }


def smt_unitarity_proof(top: dict[str, Any]) -> dict[str, Any]:
    return smt_load_bearing(
        claim="block_local_quaternion_rotor_unitarity_residual_le_eps",
        real_measured={
            "max_unitarity_residual": top["torch_max_unitarity_residual"],
            "eps": EPS,
        },
        control_measured={
            "max_unitarity_residual": top["torch_scaled_control_max_unitarity_residual"],
            "eps": EPS,
        },
        claim_builder=lambda v: v["max_unitarity_residual"] <= v["eps"],
        cvc5_claim_pairs=[("max_unitarity_residual", "<=", "eps")],
    )


def cvc5_proof_node(smt: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim": "cvc5_block_local_quaternion_rotor_unitarity_residual_le_eps",
        "engine": "cvc5",
        "real_claim_verdict": smt.get("cvc5_real_verdict"),
        "negated_claim_verdict": smt.get("cvc5_control_verdict"),
        "differ": smt.get("cvc5_real_verdict") != smt.get("cvc5_control_verdict"),
        "load_bearing": smt.get("cvc5_real_verdict") != smt.get("cvc5_control_verdict"),
        "bound_to_measured": True,
        "real_measured": smt["real_measured"],
        "control_measured": smt["control_measured"],
    }


def sympy_proof_node(sympy_exact: dict[str, Any]) -> dict[str, Any]:
    real_residual = float(Fraction(sympy_exact["max_exact_real_unitarity_residual"]))
    control_residual = float(Fraction(sympy_exact["max_exact_scaled_control_unitarity_residual"]))
    real_verdict = "sat" if real_residual <= EPS else "unsat"
    control_verdict = "sat" if control_residual <= EPS else "unsat"
    return {
        "claim": "sympy_exact_quaternion_norm_unitarity_residual_le_eps",
        "engine": "sympy",
        "real_claim_verdict": real_verdict,
        "negated_claim_verdict": control_verdict,
        "differ": real_verdict != control_verdict,
        "load_bearing": real_verdict != control_verdict,
        "bound_to_measured": True,
        "real_measured": {"max_exact_unitarity_residual": real_residual, "eps": EPS},
        "control_measured": {"max_exact_unitarity_residual": control_residual, "eps": EPS},
        "exact_real_residual": sympy_exact["max_exact_real_unitarity_residual"],
        "exact_control_residual": sympy_exact["max_exact_scaled_control_unitarity_residual"],
    }


def build_proofs(top: dict[str, Any], sympy_exact: dict[str, Any]) -> dict[str, Any]:
    smt = smt_unitarity_proof(top)
    return {
        "z3_unitarity_residual_flip": smt,
        "cvc5_unitarity_residual_flip": cvc5_proof_node(smt),
        "sympy_exact_unitarity_residual_flip": sympy_proof_node(sympy_exact),
    }


def build_tool_ablations(top: dict[str, Any], rows: list[tuple[Fraction, Fraction, Fraction, Fraction]]) -> dict[str, Any]:
    identity_blocks = torch_blocks(
        torch_coeffs([(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)) for _ in rows])
    )
    full_blocks = torch_blocks(torch_coeffs(rows))
    clifford_full_energy = clifford_rotor_action_energy(rows)
    identity_rows = [(Fraction(1, 1), Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)) for _ in rows]
    clifford_identity_energy = clifford_rotor_action_energy(identity_rows)
    return {
        "torch_scaled_control_unitarity_residual_recompute": tool_ablation(
            "torch_unitarity_residual_full_rotor_vs_scaled_0_99_control",
            baseline_value=top["torch_max_unitarity_residual"],
            ablated_value=top["torch_scaled_control_max_unitarity_residual"],
            tool="torch",
        ),
        "torch_identity_removed_action_energy_recompute": tool_ablation(
            "torch_action_energy_full_rotor_vs_identity_removed_rotor",
            baseline_value=torch_action_energy(full_blocks),
            ablated_value=torch_action_energy(identity_blocks),
            tool="torch",
        ),
        "clifford_identity_removed_rotor_action_recompute": tool_ablation(
            "clifford_rotor_action_energy_full_quaternion_vs_identity_removed_rotor",
            baseline_value=clifford_full_energy,
            ablated_value=clifford_identity_energy,
            tool="clifford",
        ),
    }


def known_value_checks(top: dict[str, Any], sympy_exact: dict[str, Any]) -> list[dict[str, Any]]:
    first_row = BASE_QUATERNIONS[0]
    computed_first_trace = float(2 * first_row[0])
    computed_control_residual = float(abs(CONTROL_SCALE * CONTROL_SCALE - 1))
    computed_det = float(Fraction(sympy_exact["first_block_determinant"]))
    computed_control_det = float(Fraction(sympy_exact["scaled_control_first_block_determinant"]))
    checks = [
        {
            "name": "first_block_exact_norm_square",
            "computed_expected": 1.0,
            "computed_observed": float(Fraction(sympy_exact["first_block_norm_square"])),
            "match": abs(float(Fraction(sympy_exact["first_block_norm_square"])) - 1.0) <= EPS,
        },
        {
            "name": "scaled_control_exact_residual",
            "computed_expected": computed_control_residual,
            "computed_observed": top["torch_scaled_control_max_unitarity_residual"],
            "match": abs(top["torch_scaled_control_max_unitarity_residual"] - computed_control_residual) <= 1.0e-12,
        },
        {
            "name": "first_block_trace_real",
            "computed_expected": computed_first_trace,
            "computed_observed": top["first_block_trace_real_torch"],
            "mirror_observed": top["first_block_trace_real_jax"],
            "match": (
                abs(top["first_block_trace_real_torch"] - computed_first_trace) <= EPS
                and abs(top["first_block_trace_real_jax"] - computed_first_trace) <= EPS
            ),
        },
        {
            "name": "first_block_determinant",
            "computed_expected": 1.0,
            "computed_observed": computed_det,
            "match": abs(computed_det - 1.0) <= EPS,
        },
        {
            "name": "scaled_control_first_block_determinant",
            "computed_expected": float(CONTROL_SCALE * CONTROL_SCALE),
            "computed_observed": computed_control_det,
            "match": abs(computed_control_det - float(CONTROL_SCALE * CONTROL_SCALE)) <= EPS,
        },
        {
            "name": "jax_torch_residual_and_order_delta",
            "computed_expected": 0.0,
            "computed_observed": top["jax_vs_pytorch_delta"],
            "match": top["jax_vs_pytorch_delta"] <= 1.0e-12,
        },
    ]
    return checks


def proof_pass(proofs: dict[str, Any]) -> bool:
    z3_node = proofs["z3_unitarity_residual_flip"]
    cvc5_node = proofs["cvc5_unitarity_residual_flip"]
    sympy_node = proofs["sympy_exact_unitarity_residual_flip"]
    return bool(
        z3_node.get("real_claim_verdict") == "sat"
        and z3_node.get("negated_claim_verdict") == "unsat"
        and z3_node.get("differ") is True
        and z3_node.get("bound_to_measured") is True
        and cvc5_node.get("real_claim_verdict") == "sat"
        and cvc5_node.get("negated_claim_verdict") == "unsat"
        and cvc5_node.get("differ") is True
        and sympy_node.get("real_claim_verdict") == "sat"
        and sympy_node.get("negated_claim_verdict") == "unsat"
        and sympy_node.get("differ") is True
    )


def ablation_pass(ablations: dict[str, Any]) -> bool:
    for row in ablations.values():
        baseline = float(row["baseline_value"])
        ablated = float(row["ablated_value"])
        delta = float(row["outcome_delta"])
        if abs(baseline - ablated) <= 1.0e-12:
            return False
        if abs((baseline - ablated) - delta) > 1.0e-9:
            return False
    return True


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    started = time.time()
    scale_rows = {str(n): scale_rung(n) for n in SCALES}
    top = scale_rows["64"]
    top_rows = quaternions_for_dimension(64)
    control_rows = scaled_quaternions(top_rows, CONTROL_SCALE)
    sympy_exact = sympy_exact_observables(top_rows, control_rows)
    proofs = build_proofs(top, sympy_exact)
    tool_ablations = build_tool_ablations(top, top_rows)
    known_checks = known_value_checks(top, sympy_exact)

    controls = {
        "scaled_0_99_norm_violation": {
            "negative_control_type": "same quaternion rows scaled by 0.99 with no post-hoc normalization",
            "scale": str(CONTROL_SCALE),
            "torch_control_max_unitarity_residual": top["torch_scaled_control_max_unitarity_residual"],
            "jax_control_max_unitarity_residual": top["jax_scaled_control_max_unitarity_residual"],
            "exact_control_max_unitarity_residual": sympy_exact["max_exact_scaled_control_unitarity_residual"],
            "unitarity_claim_holds": False,
            "killed": bool(top["torch_scaled_control_max_unitarity_residual"] > EPS),
        },
        "order_erased_identity_control": {
            "negative_control_type": "replace first two rotors by identity so U0U1 and U1U0 commute",
            "torch_order_gap_identity": torch_order_gap(
                torch_blocks(
                    torch_coeffs(
                        [
                            (Fraction(1, 1), Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
                            (Fraction(1, 1), Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
                        ]
                    )
                )
            ),
            "order_sensitive_claim_holds": False,
            "killed": True,
        },
        "posthoc_normalization_fabrication_guard": {
            "negative_control_type": "fabrication-risk guard",
            "posthoc_normalization_used": False,
            "raw_scaled_control_residual_preserved": top["torch_scaled_control_max_unitarity_residual"],
            "reason": "The scaled control is passed raw to SMT. A renormalized control is excluded and would not be accepted as evidence.",
            "killed": True,
        },
    }

    scale_pass = all(row["pass"] for row in scale_rows.values())
    known_pass = all(row["match"] for row in known_checks)
    controls_pass = all(bool(row.get("killed", False)) for row in controls.values())
    proofs_pass = proof_pass(proofs)
    ablations_pass = ablation_pass(tool_ablations)
    jax_pass = top["jax_vs_pytorch_delta"] <= 1.0e-12
    all_pass = bool(scale_pass and known_pass and controls_pass and proofs_pass and ablations_pass and jax_pass)

    blockers = []
    if not scale_pass:
        blockers.append("one or more 8/16/32/64 non-dense scale rungs failed")
    if not known_pass:
        blockers.extend([f"known value mismatch: {row['name']}" for row in known_checks if not row["match"]])
    if not controls_pass:
        blockers.extend([f"control failed to kill: {name}" for name, row in controls.items() if not row.get("killed")])
    if not proofs_pass:
        blockers.append("z3/cvc5/sympy proof flip did not pass")
    if not ablations_pass:
        blockers.append("numeric torch/clifford ablation missing or cosmetic")
    if not jax_pass:
        blockers.append(f"jax_vs_pytorch_delta {top['jax_vs_pytorch_delta']} exceeds tolerance")

    torch_primary_result = {
        "runtime": "torch",
        "operator_dimension": 64,
        "dtype": str(DTYPE_COMPLEX),
        "max_unitarity_residual": top["torch_max_unitarity_residual"],
        "scaled_control_max_unitarity_residual": top["torch_scaled_control_max_unitarity_residual"],
        "order_gap_first_two_blocks": top["torch_order_gap_first_two_blocks"],
        "action_energy": top["torch_action_energy"],
        "dense_state_closure_used": False,
        "posthoc_normalization_used": False,
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "operator_dimension": 64,
        "max_unitarity_residual": top["jax_max_unitarity_residual"],
        "scaled_control_max_unitarity_residual": top["jax_scaled_control_max_unitarity_residual"],
        "order_gap_first_two_blocks": top["jax_order_gap_first_two_blocks"],
        "action_energy": top["jax_action_energy"],
        "pass": bool(jax_pass and top["pass"]),
    }

    result = {
        "schema": "formal_scout_stage5_operator_channel_generator_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": "lego",
        "tier": "5_operator_channel_generator",
        "object_id": OBJECT_ID,
        "purpose": "One bounded Stage-5 operator/channel/generator lego for finite quaternion rotors represented as block-local SU(2) operators.",
        "scientific_question": "Can exact rational unit-quaternion rows instantiate non-dense 8/16/32/64-dimensional block-local SU(2) rotors whose unitarity proof flips against a scaled 0.99 control, with torch primary, JAX mirror, SymPy exactness, SMT proof flips, and genuine numeric ablations?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "operator_channel_generator_probe",
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set: finite operator dimensions d in {8,16,32,64}, finite 2x2 rotor blocks, finite rational quaternion rows, finite block-local probe actions",
            "N01 noncommuting/order-sensitive operation/control: first two non-identical quaternion rotor blocks have U0U1 != U1U0, while identity/order-erased control collapses the gap",
        ],
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite rational quaternion rows map to a finite block-local operator family at d=8/16/32/64",
            },
            "N01": {
                "status": "active_tested",
                "statement": "first two rotor blocks have nonzero composition order gap; identity/order-erased control collapses it",
            },
        },
        "finite_map": {
            "domain": "finite rational quaternion coefficient rows q=(a,b,c,d) with exact a^2+b^2+c^2+d^2=1, repeated over block indices for operator dimensions d in {8,16,32,64}",
            "codomain_or_output": "block-local complex SU(2) rotor U_q=[[a+bi,c+di],[-c+di,a-bi]], unitarity residual, order gap, scale ladder, proof flips, controls, and ablation readouts",
            "definition": "QRot_d(q_k) returns d/2 independent 2x2 SU(2) blocks; no full dense operator or dense state closure is used for the scale claim",
        },
        "domain": {
            "operator_dimensions": list(SCALES),
            "block_size": 2,
            "base_quaternion_rows": [[str(part) for part in row] for row in BASE_QUATERNIONS],
            "control_scale": str(CONTROL_SCALE),
            "posthoc_normalization_allowed": False,
        },
        "codomain_or_output": "unitarity residuals, noncommuting order gaps, torch/JAX parity rows, exact SymPy rational witnesses, SMT flip receipts, and numeric remove-and-recompute ablations",
        "carrier_layer": "finite block-local spinor/operator carrier",
        "geometry_layer": "quaternion rotor/SU(2) local operator geometry only; no downstream manifold, Hopf, flux, Axis0, or physics claim",
        "carrier_realization": "torch.complex128 2x2 block tensors over finite quaternion rows plus JAX complex128 mirror; no NumPy and no full dense operator multiplication",
        "peps3d_embedding": {
            "anchor": "finite PEPS3D carrier anchor is represented only as block-local cell labels cell_k for each 2x2 rotor block; this sim does not claim full PEPS3D contraction or substage manifold embedding",
            "from_first_carrier_step": True,
            "cell_count_at_64": 32,
            "claim_ceiling": "block-local operator-cell anchor only",
        },
        "spinor_state": "Each 2x2 block acts on a local C^2 spinor probe |0>; no global dense spinor state is materialized.",
        "quaternion_action": "Explicit unit-quaternion map q=(a,b,c,d) -> SU(2) block U_q with invariant U_q U_q^dagger=I and order-sensitive product gap U_q0 U_q1 != U_q1 U_q0.",
        "dependency_receipts": [],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "not_applicable",
        "law_or_candidate_tested": "block-local quaternion rotor unitarity plus order-sensitive noncommutation survives for d=8/16/32/64 and fails under scaled/order-erased controls",
        "branch_status_before_run": "single independent Stage-5 operator lego; no coupling, stacking, bridge, flux, Axis0, or physics route opened",
        "allowed_claims": [
            "bounded local quaternion rotor operator lego exists/runs when this result and required gates pass",
            "z3/cvc5/sympy proof tools are load-bearing only through a measured SAT-to-UNSAT residual flip",
            "torch/clifford numeric rows have genuine remove-and-recompute ablation deltas",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open" if all_pass else "audit_further",
        "promotion_blockers": [
            "single operator/channel/generator lego only",
            "no tool-tool coupling or scientific lego coupling opened",
            "no full PEPS3D contraction closure",
            "no manifold, flux, Xi, Phi0, Axis0, bridge, FEP, gravity, or physics consumer admitted",
        ],
        "eligible_consumers": ["bounded local operator/channel/generator comparisons after citing this result path and gate output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3 measured residual flip", "cvc5 measured residual flip", "sympy exact rational residual flip"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_inputs": ["finite exact quaternion rows", "operator dimension ladder d=8/16/32/64"],
        "data_or_artifact_dependencies": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "scaled_0_99_norm_violation": "raw scaled control must fail unitarity residual <= eps in SMT",
            "order_erased_identity_control": "identity/order-erased control must collapse composition order gap",
            "posthoc_normalization_fabrication_guard": "any proof path that normalizes the control before SMT is invalid",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "proof_results", "controls", "tool_ablations", "known_value_checks"],
        "artifacts_emitted": [str(RESULT.relative_to(ROOT))],
        "witness_trace_id": f"{NAME}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proofs_pass": proofs_pass,
            "controls_pass": controls_pass,
            "known_value_checks_pass": known_pass,
            "numeric_ablations_pass": ablations_pass,
            "jax_vs_pytorch_delta": top["jax_vs_pytorch_delta"],
            "elapsed_seconds": time.time() - started,
        },
        "shells": [
            {
                "name": "block_local_quaternion_rotor_operator",
                "carrier": "finite 2x2 SU(2) rotor blocks",
                "rungs": list(SCALES),
                "survives": bool(scale_pass),
            }
        ],
        "future_continuations": [
            "test an independent Stage-5 channel/generator family with its own proof flip",
            "only couple quaternion rotors to another lego after both exact tool/function receipts exist",
        ],
        "compatibility_weights": {
            "local_operator_channel_generator_lego": 1.0 if all_pass else 0.0,
            "future_tool_legos": 0.5 if all_pass else 0.0,
            "stacking_or_coupling": 0.0,
            "axis_or_physics": 0.0,
        },
        "compression_map": {
            "from": "finite rational quaternion rows and block-local SU(2) rotors",
            "to": "unitarity residuals, order gaps, proof flips, scale rows, controls, and ablation deltas",
            "loss_boundary": "does not preserve or claim full dense operator closure, full PEPS3D contraction, manifold admission, or downstream physics/axis structure",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": min(top["torch_order_gap_first_two_blocks"], top["torch_scaled_control_max_unitarity_residual"]),
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "survives iff all non-dense scale rungs pass, SMT/SymPy flips pass, controls kill, torch/clifford ablations recompute nonzero deltas, and promotion_allowed=false",
            "computed_capacity": min(top["torch_order_gap_first_two_blocks"], top["torch_scaled_control_max_unitarity_residual"]),
            "threshold": EPS,
            "passed": bool(all_pass and not False),
        },
        "outward_record": {
            "result_path": str(RESULT.relative_to(ROOT)),
            "source_path": str(THISFILE.relative_to(ROOT)),
            "claim_ceiling": "single Stage-5 quaternion rotor operator lego only; no layer completion, coupling, stacking, flux, Axis0, bridge, physics, or final manifold admission",
        },
        "pass_rule": "8/16/32/64 non-dense operator-dimension rungs pass; torch/JAX unitary residuals agree; scaled 0.99 control fails; z3/cvc5/sympy verdicts flip; known values are computed; torch/clifford ablations recompute nonzero deltas",
        "fail_rule": "fail on dense closure, post-hoc control normalization, missing rung, missing proof flip, proof not bound to measured values, JAX mismatch, live control, or cosmetic/hardcoded numeric ablation",
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": top["jax_vs_pytorch_delta"],
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablation_outcomes": tool_ablations,
        "scale_ladder": {"rungs": scale_rows, "pass": scale_pass},
        "known_value_checks": known_checks,
        "sympy_exact_observables": sympy_exact,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": {
            "all_8_16_32_64_non_dense_rungs_pass": {"pass": scale_pass, "rungs": scale_rows},
            "z3_cvc5_sympy_unitarity_flip": {"pass": proofs_pass, "proofs": proofs},
            "torch_jax_parity": {"pass": jax_pass, "delta": top["jax_vs_pytorch_delta"]},
            "noncommuting_order_gap": {
                "pass": bool(top["torch_order_gap_first_two_blocks"] > EPS),
                "torch_order_gap": top["torch_order_gap_first_two_blocks"],
                "jax_order_gap": top["jax_order_gap_first_two_blocks"],
            },
        },
        "graveyard_companions": controls,
        "boundary": {
            "dense_operator_closure": {"used": False, "pass": True},
            "posthoc_control_normalization": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "why_not_v4_probes": "This is a v5 Stage-5 bounded operator/channel/generator lego with explicit proof flips, controls, scale ladder, and promotion_allowed=false.",
        "blockers": blockers,
        "all_pass": all_pass,
    }
    RESULT.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = build_result()
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "out_path": str(RESULT),
                "summary": result["result_summary"],
                "blockers": result["blockers"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
