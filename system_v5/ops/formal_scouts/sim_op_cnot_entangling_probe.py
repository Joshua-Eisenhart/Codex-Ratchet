#!/usr/bin/env python3
"""Stage-5 CNOT operator/channel/generator probe.

Finite map:
    CNOT_D : (basis index, block-local CNOT permutation, Kraus weight) ->
             output basis index and one-operator channel certificate.

The operator is carried as a permutation vector plus per-column Kraus weights.
No D x D dense operator is allocated for the 8/16/32/64 scale ladder.
"""

import jax

jax.config.update("jax_enable_x64", True)

import json
import pathlib
import sys
import time
import warnings
from fractions import Fraction
from typing import Any

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
THISFILE = ROOT / "sim_op_cnot_entangling_probe.py"
OBJECT_ID = "cnot_entangling_operator_channel"
RESULT = RESULT_DIR / "sim_op_cnot_entangling_probe_results.json"

SCALES = (8, 16, 32, 64)
BASE_DIM = 4
DTYPE = torch.float64
CDTYPE = torch.complex128
JAX_DTYPE = jnp.float64
LEAK = Fraction(9, 10)
EPS = 0.0
TOL = 1.0e-12
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "final_manifold"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": (
            "PRIMARY carrier and numeric checker: block-CNOT permutation-plus-weight channel, "
            "Kraus completeness defect, CNOT^2, and Bell entanglement recomputed after identity ablation."
        ),
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror recomputes permutation/channel defects and Bell entropy without NumPy.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "LOAD-BEARING proof only through smt_load_bearing verdict flip: exact CNOT completeness "
            "defect is SAT, leaky CNOT control is UNSAT under the same defect<=0 claim."
        ),
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": (
            "LOAD-BEARING proof cross-check only through the same smt_load_bearing SAT/UNSAT flip."
        ),
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "LOAD-BEARING exact rational source for the real/control completeness defects used by the SMT flip; "
            "no numeric ablation is claimed for sympy."
        ),
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": (
            "Cl(4) geometric-product witness for the local CNOT basis-blade orientation action; "
            "identity ablation recomputes and removes the CNOT orientation flip."
        ),
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported and not used; no .numpy() bridge or dense NumPy carrier is part of the claim.",
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


def cnot_perm_list(dim: int) -> list[int]:
    if dim % BASE_DIM != 0:
        raise ValueError(f"operator dimension must be a multiple of {BASE_DIM}: {dim}")
    perm = list(range(dim))
    for start in range(0, dim, BASE_DIM):
        perm[start + 0] = start + 0
        perm[start + 1] = start + 1
        perm[start + 2] = start + 3
        perm[start + 3] = start + 2
    return perm


def identity_perm_list(dim: int) -> list[int]:
    return list(range(dim))


def x_control_perm_list(dim: int) -> list[int]:
    if dim % BASE_DIM != 0:
        raise ValueError(f"operator dimension must be a multiple of {BASE_DIM}: {dim}")
    perm = list(range(dim))
    for start in range(0, dim, BASE_DIM):
        perm[start + 0] = start + 2
        perm[start + 1] = start + 3
        perm[start + 2] = start + 0
        perm[start + 3] = start + 1
    return perm


def compose_perm_list(after: list[int], before: list[int]) -> list[int]:
    if len(after) != len(before):
        raise ValueError("permutations must have the same length")
    return [after[before[i]] for i in range(len(before))]


def order_disagreement_count(dim: int, left: list[int], right: list[int]) -> int:
    if len(left) != dim or len(right) != dim:
        raise ValueError("permutation length mismatch")
    return sum(1 for i in range(dim) if left[i] != right[i])


def torch_perm(dim: int, *, identity: bool = False) -> torch.Tensor:
    values = identity_perm_list(dim) if identity else cnot_perm_list(dim)
    return torch.tensor(values, dtype=torch.long)


def jax_perm(dim: int, *, identity: bool = False) -> jax.Array:
    values = identity_perm_list(dim) if identity else cnot_perm_list(dim)
    return jnp.array(values, dtype=jnp.int64)


def torch_weights(dim: int, *, leaky: bool = False) -> torch.Tensor:
    weights = torch.ones(dim, dtype=DTYPE)
    if leaky:
        for start in range(0, dim, BASE_DIM):
            # Column |11> -> |10> is the Gemini-specified leaky CNOT element.
            weights[start + 3] = float(LEAK)
    return weights


def jax_weights(dim: int, *, leaky: bool = False) -> jax.Array:
    values = [1.0 for _ in range(dim)]
    if leaky:
        for start in range(0, dim, BASE_DIM):
            values[start + 3] = float(LEAK)
    return jnp.array(values, dtype=JAX_DTYPE)


def apply_weighted_perm_torch(state: torch.Tensor, perm: torch.Tensor, weights: torch.Tensor) -> torch.Tensor:
    out = torch.zeros_like(state)
    out[perm] = weights.to(state.dtype) * state
    return out


def apply_weighted_perm_jax(state: jax.Array, perm: jax.Array, weights: jax.Array) -> jax.Array:
    return jnp.zeros_like(state).at[perm].set(weights.astype(state.dtype) * state)


def completeness_defect_torch(weights: torch.Tensor) -> float:
    return float(torch.max(torch.abs(weights * weights - torch.ones_like(weights))).item())


def completeness_defect_jax(weights: jax.Array) -> float:
    return float(jnp.max(jnp.abs(weights * weights - jnp.ones_like(weights))).item())


def duplicate_preimage_defect_torch(perm: torch.Tensor) -> int:
    return int(perm.numel() - torch.unique(perm).numel())


def cnot_involution_holds_torch(perm: torch.Tensor) -> bool:
    ident = torch.arange(perm.numel(), dtype=torch.long)
    return bool(torch.equal(perm[perm], ident))


def cnot_involution_holds_jax(perm: jax.Array) -> bool:
    ident = jnp.arange(perm.shape[0], dtype=jnp.int64)
    return bool(jnp.all(perm[perm] == ident).item())


def plus_zero_state_torch() -> torch.Tensor:
    inv_sqrt2 = torch.tensor(1.0 / (2.0**0.5), dtype=CDTYPE)
    return torch.tensor([1.0, 0.0, 1.0, 0.0], dtype=CDTYPE) * inv_sqrt2


def plus_zero_state_jax() -> jax.Array:
    inv_sqrt2 = jnp.array(1.0 / (2.0**0.5), dtype=jnp.complex128)
    return jnp.array([1.0, 0.0, 1.0, 0.0], dtype=jnp.complex128) * inv_sqrt2


def entropy_bits_from_state_torch(state: torch.Tensor) -> float:
    amps = state.reshape(2, 2)
    singular_values = torch.linalg.svdvals(amps)
    probs = torch.real(singular_values * torch.conj(singular_values))
    mask = probs > torch.tensor(1.0e-15, dtype=probs.dtype)
    entropy = -torch.sum(probs[mask] * torch.log2(probs[mask]))
    return float(entropy.item())


def concurrence_from_state_torch(state: torch.Tensor) -> float:
    a, b, c, d = state
    return float(torch.abs(2.0 * (a * d - b * c)).item())


def entropy_bits_from_state_jax(state: jax.Array) -> float:
    amps = state.reshape((2, 2))
    singular_values = jnp.linalg.svd(amps, compute_uv=False)
    probs = jnp.real(singular_values * jnp.conj(singular_values))
    masked = jnp.where(probs > 1.0e-15, probs, 1.0)
    entropy = -jnp.sum(jnp.where(probs > 1.0e-15, probs * jnp.log2(masked), 0.0))
    return float(entropy.item())


def concurrence_from_state_jax(state: jax.Array) -> float:
    a, b, c, d = state
    return float(jnp.abs(2.0 * (a * d - b * c)).item())


def torch_entanglement_summary(identity: bool = False) -> dict[str, float]:
    perm = torch_perm(BASE_DIM, identity=identity)
    weights = torch_weights(BASE_DIM)
    out = apply_weighted_perm_torch(plus_zero_state_torch(), perm, weights)
    return {
        "entropy_bits": entropy_bits_from_state_torch(out),
        "concurrence": concurrence_from_state_torch(out),
        "output_norm": float(torch.linalg.norm(out).item()),
    }


def jax_entanglement_summary(identity: bool = False) -> dict[str, float]:
    perm = jax_perm(BASE_DIM, identity=identity)
    weights = jax_weights(BASE_DIM)
    out = apply_weighted_perm_jax(plus_zero_state_jax(), perm, weights)
    return {
        "entropy_bits": entropy_bits_from_state_jax(out),
        "concurrence": concurrence_from_state_jax(out),
        "output_norm": float(jnp.linalg.norm(out).item()),
    }


def sympy_exact_defects() -> dict[str, Any]:
    real_weights = [sp.Rational(1, 1) for _ in range(BASE_DIM)]
    control_weights = [sp.Rational(1, 1), sp.Rational(1, 1), sp.Rational(1, 1), sp.Rational(LEAK.numerator, LEAK.denominator)]
    real_defects = [abs(w * w - 1) for w in real_weights]
    control_defects = [abs(w * w - 1) for w in control_weights]
    real_defect = max(real_defects)
    control_defect = max(control_defects)
    cnot = sp.Matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
    identity = sp.eye(4)
    return {
        "tool": "sympy",
        "base_cnot_matrix_rows": [[int(cnot[row, col]) for col in range(4)] for row in range(4)],
        "real_completeness_defect": str(real_defect),
        "leaky_control_completeness_defect": str(control_defect),
        "expected_leaky_control_defect": "19/100",
        "cnot_squared_is_identity": bool(cnot * cnot == identity),
        "cnot_determinant": str(cnot.det()),
        "pass": bool(real_defect == 0 and control_defect == sp.Rational(19, 100) and cnot * cnot == identity),
        "bound_to_smt_load_bearing": True,
    }


def smt_completeness_proof(real_defect: float, control_defect: float) -> dict[str, Any]:
    return smt_load_bearing(
        claim="single_kraus_cnot_channel_completeness_defect_eq_zero",
        real_measured={"completeness_defect": real_defect, "eps": EPS},
        control_measured={"completeness_defect": control_defect, "eps": EPS},
        claim_builder=lambda v: v["completeness_defect"] <= v["eps"],
        cvc5_claim_pairs=[("completeness_defect", "<=", "eps")],
    )


def clifford_orientation_sign(perm: list[int]) -> float:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    _, blades = Cl(4, 0)
    basis = [blades[f"e{i}"] for i in range(1, 5)]
    product = basis[perm[0]] * basis[perm[1]] * basis[perm[2]] * basis[perm[3]]
    return float(product[(1, 2, 3, 4)])


def clifford_summary() -> dict[str, Any]:
    cnot_sign = clifford_orientation_sign(cnot_perm_list(BASE_DIM))
    identity_sign = clifford_orientation_sign(identity_perm_list(BASE_DIM))
    return {
        "tool": "clifford",
        "algebra": "Cl(4,0)",
        "observable": "pseudoscalar coefficient of product of CNOT-transformed basis vectors",
        "cnot_local_orientation_sign": cnot_sign,
        "identity_local_orientation_sign": identity_sign,
        "pass": bool(cnot_sign == -1.0 and identity_sign == 1.0),
    }


def scale_rung(dim: int) -> dict[str, Any]:
    perm = torch_perm(dim)
    identity_perm = torch_perm(dim, identity=True)
    cnot_list = cnot_perm_list(dim)
    ident_list = identity_perm_list(dim)
    x_control = x_control_perm_list(dim)
    cnot_after_x = compose_perm_list(cnot_list, x_control)
    x_after_cnot = compose_perm_list(x_control, cnot_list)
    ident_after_x = compose_perm_list(ident_list, x_control)
    x_after_ident = compose_perm_list(x_control, ident_list)
    n01_order_gap = order_disagreement_count(dim, cnot_after_x, x_after_cnot)
    n01_order_erased_gap = order_disagreement_count(dim, ident_after_x, x_after_ident)
    weights = torch_weights(dim)
    control_weights = torch_weights(dim, leaky=True)
    jperm = jax_perm(dim)
    jweights = jax_weights(dim)
    jcontrol_weights = jax_weights(dim, leaky=True)

    torch_defect = completeness_defect_torch(weights)
    torch_control_defect = completeness_defect_torch(control_weights)
    jax_defect = completeness_defect_jax(jweights)
    jax_control_defect = completeness_defect_jax(jcontrol_weights)
    torch_ent = torch_entanglement_summary(identity=False)
    torch_identity_ent = torch_entanglement_summary(identity=True)
    jax_ent = jax_entanglement_summary(identity=False)
    jax_identity_ent = jax_entanglement_summary(identity=True)

    pass_rung = (
        duplicate_preimage_defect_torch(perm) == 0
        and cnot_involution_holds_torch(perm)
        and cnot_involution_holds_jax(jperm)
        and bool(torch.equal(identity_perm, torch.arange(dim, dtype=torch.long)))
        and torch_defect <= TOL
        and jax_defect <= TOL
        and abs(torch_control_defect - float(Fraction(19, 100))) <= TOL
        and abs(jax_control_defect - torch_control_defect) <= TOL
        and abs(torch_ent["entropy_bits"] - 1.0) <= TOL
        and abs(torch_identity_ent["entropy_bits"]) <= TOL
        and abs(jax_ent["entropy_bits"] - torch_ent["entropy_bits"]) <= TOL
        and abs(jax_identity_ent["entropy_bits"] - torch_identity_ent["entropy_bits"]) <= TOL
        and n01_order_gap == dim
        and n01_order_erased_gap == 0
    )

    return {
        "sites_or_qubits": dim,
        "operator_dimension": dim,
        "operator_block_count": dim // BASE_DIM,
        "nonzero_operator_entries": dim,
        "dense_operator_entries_if_allocated": dim * dim,
        "dense_state_closure_used": False,
        "dense_operator_allocated": False,
        "carrier_storage": "permutation_vector_plus_column_weights",
        "torch_completeness_defect": torch_defect,
        "torch_leaky_control_completeness_defect": torch_control_defect,
        "jax_completeness_defect": jax_defect,
        "jax_leaky_control_completeness_defect": jax_control_defect,
        "jax_vs_pytorch_delta": max(abs(jax_defect - torch_defect), abs(jax_control_defect - torch_control_defect)),
        "permutation_duplicate_preimage_defect": duplicate_preimage_defect_torch(perm),
        "cnot_squared_is_identity_torch": cnot_involution_holds_torch(perm),
        "cnot_squared_is_identity_jax": cnot_involution_holds_jax(jperm),
        "n01_order_witness": {
            "operation_left": "CNOT_after_X_control",
            "operation_right": "X_control_after_CNOT",
            "disagreement_count": n01_order_gap,
            "order_erased_identity_disagreement_count": n01_order_erased_gap,
            "base_left_map": compose_perm_list(cnot_perm_list(BASE_DIM), x_control_perm_list(BASE_DIM)),
            "base_right_map": compose_perm_list(x_control_perm_list(BASE_DIM), cnot_perm_list(BASE_DIM)),
            "pass": bool(n01_order_gap == dim and n01_order_erased_gap == 0),
        },
        "torch_entanglement_entropy_bits": torch_ent["entropy_bits"],
        "torch_identity_ablation_entropy_bits": torch_identity_ent["entropy_bits"],
        "torch_concurrence": torch_ent["concurrence"],
        "torch_identity_ablation_concurrence": torch_identity_ent["concurrence"],
        "jax_entanglement_entropy_bits": jax_ent["entropy_bits"],
        "jax_identity_ablation_entropy_bits": jax_identity_ent["entropy_bits"],
        "jax_concurrence": jax_ent["concurrence"],
        "jax_identity_ablation_concurrence": jax_identity_ent["concurrence"],
        "pass": bool(pass_rung),
    }


def build_known_value_checks(
    top: dict[str, Any],
    proof: dict[str, Any],
    sympy_result: dict[str, Any],
    clifford_result: dict[str, Any],
) -> list[dict[str, Any]]:
    checks = [
        {
            "name": "base_cnot_permutation",
            "computed": cnot_perm_list(BASE_DIM),
            "expected": [0, 1, 3, 2],
            "match": cnot_perm_list(BASE_DIM) == [0, 1, 3, 2],
        },
        {
            "name": "real_completeness_defect_zero",
            "computed": top["torch_completeness_defect"],
            "expected": 0.0,
            "match": abs(float(top["torch_completeness_defect"])) <= TOL,
        },
        {
            "name": "leaky_control_defect_19_over_100",
            "computed": top["torch_leaky_control_completeness_defect"],
            "expected": float(Fraction(19, 100)),
            "match": abs(float(top["torch_leaky_control_completeness_defect"]) - float(Fraction(19, 100))) <= TOL,
        },
        {
            "name": "sympy_exact_leaky_defect",
            "computed": sympy_result["leaky_control_completeness_defect"],
            "expected": "19/100",
            "match": sympy_result["leaky_control_completeness_defect"] == "19/100",
        },
        {
            "name": "z3_verdict_flip",
            "computed": [proof["real_claim_verdict"], proof["negated_claim_verdict"]],
            "expected": ["sat", "unsat"],
            "match": proof["real_claim_verdict"] == "sat" and proof["negated_claim_verdict"] == "unsat",
        },
        {
            "name": "cvc5_verdict_flip",
            "computed": [proof.get("cvc5_real_verdict"), proof.get("cvc5_control_verdict")],
            "expected": ["sat", "unsat"],
            "match": proof.get("cvc5_real_verdict") == "sat" and proof.get("cvc5_control_verdict") == "unsat",
        },
        {
            "name": "bell_entropy_bits",
            "computed": top["torch_entanglement_entropy_bits"],
            "expected": 1.0,
            "match": abs(float(top["torch_entanglement_entropy_bits"]) - 1.0) <= TOL,
        },
        {
            "name": "identity_ablation_entropy_bits",
            "computed": top["torch_identity_ablation_entropy_bits"],
            "expected": 0.0,
            "match": abs(float(top["torch_identity_ablation_entropy_bits"])) <= TOL,
        },
        {
            "name": "n01_cnot_x_control_order_disagreement",
            "computed": top["n01_order_witness"]["disagreement_count"],
            "expected": top["operator_dimension"],
            "match": top["n01_order_witness"]["disagreement_count"] == top["operator_dimension"],
        },
        {
            "name": "n01_order_erased_identity_control",
            "computed": top["n01_order_witness"]["order_erased_identity_disagreement_count"],
            "expected": 0,
            "match": top["n01_order_witness"]["order_erased_identity_disagreement_count"] == 0,
        },
        {
            "name": "clifford_orientation_flip",
            "computed": [
                clifford_result["cnot_local_orientation_sign"],
                clifford_result["identity_local_orientation_sign"],
            ],
            "expected": [-1.0, 1.0],
            "match": (
                clifford_result["cnot_local_orientation_sign"] == -1.0
                and clifford_result["identity_local_orientation_sign"] == 1.0
            ),
        },
    ]
    return checks


def build_tool_ablations(top: dict[str, Any], clifford_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "torch_bell_entropy_cnot_vs_identity": tool_ablation(
            "torch_Bell_entropy_bits_after_CNOT_vs_identity_removed",
            baseline_value=top["torch_entanglement_entropy_bits"],
            ablated_value=top["torch_identity_ablation_entropy_bits"],
            tool="torch",
        ),
        "torch_concurrence_cnot_vs_identity": tool_ablation(
            "torch_concurrence_after_CNOT_vs_identity_removed",
            baseline_value=top["torch_concurrence"],
            ablated_value=top["torch_identity_ablation_concurrence"],
            tool="torch",
        ),
        "clifford_orientation_cnot_vs_identity": tool_ablation(
            "clifford_local_pseudoscalar_orientation_sign_after_CNOT_vs_identity_removed",
            baseline_value=clifford_result["cnot_local_orientation_sign"],
            ablated_value=clifford_result["identity_local_orientation_sign"],
            tool="clifford",
        ),
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    started = time.time()

    scale_rows = {str(dim): scale_rung(dim) for dim in SCALES}
    top = scale_rows["64"]
    sympy_result = sympy_exact_defects()
    proof = smt_completeness_proof(
        real_defect=float(Fraction(sympy_result["real_completeness_defect"])),
        control_defect=float(Fraction(sympy_result["leaky_control_completeness_defect"])),
    )
    clifford_result = clifford_summary()
    tool_ablations = build_tool_ablations(top, clifford_result)
    known_checks = build_known_value_checks(top, proof, sympy_result, clifford_result)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = (
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
    )
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > TOL
        and abs(
            abs(float(row["baseline_value"]) - float(row["ablated_value"]))
            - abs(float(row["outcome_delta"]))
        )
        <= TOL
        for row in tool_ablations.values()
    )
    known_pass = all(check["match"] for check in known_checks)
    parity_delta = max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())
    all_pass = bool(scale_pass and proof_pass and ablation_pass and known_pass and parity_delta <= TOL)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(DTYPE),
        "complex_dtype_for_state_probe": str(CDTYPE),
        "operator_dimension": top["operator_dimension"],
        "carrier_storage": top["carrier_storage"],
        "dense_operator_allocated": False,
        "completeness_defect": top["torch_completeness_defect"],
        "leaky_control_completeness_defect": top["torch_leaky_control_completeness_defect"],
        "cnot_squared_is_identity": top["cnot_squared_is_identity_torch"],
        "n01_order_witness": top["n01_order_witness"],
        "bell_entropy_bits": top["torch_entanglement_entropy_bits"],
        "identity_ablation_entropy_bits": top["torch_identity_ablation_entropy_bits"],
        "bell_concurrence": top["torch_concurrence"],
        "identity_ablation_concurrence": top["torch_identity_ablation_concurrence"],
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "operator_dimension": top["operator_dimension"],
        "completeness_defect": top["jax_completeness_defect"],
        "leaky_control_completeness_defect": top["jax_leaky_control_completeness_defect"],
        "cnot_squared_is_identity": top["cnot_squared_is_identity_jax"],
        "bell_entropy_bits": top["jax_entanglement_entropy_bits"],
        "identity_ablation_entropy_bits": top["jax_identity_ablation_entropy_bits"],
        "bell_concurrence": top["jax_concurrence"],
        "identity_ablation_concurrence": top["jax_identity_ablation_concurrence"],
        "pass": bool(
            top["cnot_squared_is_identity_jax"]
            and abs(top["jax_completeness_defect"] - top["torch_completeness_defect"]) <= TOL
            and abs(top["jax_leaky_control_completeness_defect"] - top["torch_leaky_control_completeness_defect"]) <= TOL
            and abs(top["jax_entanglement_entropy_bits"] - top["torch_entanglement_entropy_bits"]) <= TOL
        ),
    }

    controls = {
        "leaky_cnot_column_control": {
            "description": "Scale the local |11> -> |10> CNOT column amplitude from 1 to 0.9 in every block.",
            "negative_control_type": "Kraus-completeness-breaking leaky operator",
            "completeness_defect": top["torch_leaky_control_completeness_defect"],
            "claim_holds": False,
            "pass": bool(abs(top["torch_leaky_control_completeness_defect"] - float(Fraction(19, 100))) <= TOL),
        },
        "identity_entangler_removed": {
            "description": "Replace the local CNOT block with identity and recompute Bell entropy/concurrence.",
            "negative_control_type": "entangling operation removed",
            "entropy_bits": top["torch_identity_ablation_entropy_bits"],
            "concurrence": top["torch_identity_ablation_concurrence"],
            "claim_holds": False,
            "pass": bool(abs(top["torch_identity_ablation_entropy_bits"]) <= TOL and abs(top["torch_identity_ablation_concurrence"]) <= TOL),
        },
    }

    result = {
        "schema": "stage5_operator_channel_generator_result_v1",
        "sim_id": "sim_op_cnot_entangling_probe",
        "name": "sim_op_cnot_entangling_probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": str(THISFILE),
        "result_path": str(RESULT),
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": (
                "operator dimensions D in {8,16,32,64}; finite basis columns j in [0,D); "
                "block-local CNOT permutation p=[0,1,3,2] repeated D/4 times; column weights w_j"
            ),
            "codomain_or_output": (
                "permutation-plus-weight single-Kraus channel K_D with output basis p(j), "
                "K_D^dagger K_D completeness defect, entangling Bell-state readout, and controls"
            ),
            "definition": "K_D |j> = w_j |p(j)>; real CNOT has all w_j=1; leaky control has w_{block+3}=9/10.",
        },
        "domain": {
            "operator_dimensions": list(SCALES),
            "local_basis": ["|00>", "|01>", "|10>", "|11>"],
            "base_cnot_permutation_input_to_output": cnot_perm_list(BASE_DIM),
            "carrier_storage": "length-D permutation vector plus length-D weight vector",
        },
        "codomain_or_output": {
            "single_kraus_channel_certificate": "max_j |w_j|^2 - 1 absolute defect",
            "operator_invariant": "K_D^dagger K_D = I_D, represented without allocating K_D",
            "entanglement_readout": "CNOT(|+0>) Bell entropy/concurrence versus identity ablation",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite operator dimensions, finite basis columns, finite permutation map, finite controls",
            },
            "N01": {
                "status": "active_tested",
                "statement": "CNOT is an order-sensitive controlled operation; CNOT after X_control differs from X_control after CNOT, while identity order-erasure commutes",
            },
        },
        "root_constraints_in_force": {
            "F01": "finite carrier/probe/operator set: D in {8,16,32,64}, D nonzero Kraus entries, finite controls",
            "N01": "controlled target flip is order-sensitive: finite maps CNOT o X_control and X_control o CNOT disagree on every basis state at each rung; identity order-erasure has zero disagreement",
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "Stage 5 operator/channel/generator lego",
        "purpose": "Verify CNOT as a finite non-dense single-Kraus entangling operator/channel with exact proof flip and numeric remove/recompute ablations.",
        "scientific_question": "Does the finite CNOT channel satisfy exact Kraus completeness while a leaky control fails, and does the CNOT operation generate Bell entanglement that identity removal kills?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "operator_channel_generator_probe",
        "carrier_layer": "finite non-dense permutation-plus-weight channel carrier",
        "geometry_layer": "not_applicable; no manifold/G-structure/Axis0 claim",
        "carrier_realization": {
            "torch": "torch length-D int64 permutation plus float64 weights; local complex128 state probe",
            "jax": "jax x64 mirror of permutation, weights, and state probe",
            "dense_operator_allocated": False,
            "numpy_imported": False,
        },
        "peps3d_embedding": "not_admitted_by_this_operator_channel_packet; PEPS3D/manifold consumers remain blocked",
        "spinor_state": "not_applicable_to_this_CNOT_channel_packet",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["root_operator_channel_packet_no_lower_dependency"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "single-Kraus CNOT channel completeness plus CNOT entangling action on |+0>",
        "branch_status_before_run": "new requested Stage-5 operator/channel/generator sim",
        "allowed_claims": [
            "local CNOT operator/channel lego over finite dimensions 8/16/32/64",
            "non-dense permutation-plus-weight representation satisfies K^dagger K=I for real CNOT",
            "leaky CNOT column control fails the same SMT-bound completeness claim",
            "CNOT entangles |+0> into a Bell state while identity ablation does not",
        ],
        "promotion_blockers": [
            "no PEPS3D manifold carrier admitted",
            "no coupled higher-stage evidence",
            "no bridge, Axis0, flux, FEP, gravity, or final manifold consumer unlocked",
        ],
        "eligible_consumers": ["future bounded operator/channel lego coupling tests after parent receipts are current"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(parity_delta),
        "jax_vs_pytorch": {
            "max_value_delta": float(parity_delta),
            "agree": bool(parity_delta <= TOL),
        },
        "proof_results": {
            "smt_load_bearing_completeness_flip": proof,
            "sympy_exact_defect_source": sympy_result,
        },
        "controls": controls,
        "torch_primary": torch_primary_result,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "scale_ladder": {
            "rungs": {
                dim: {
                    "sites_or_qubits": row["sites_or_qubits"],
                    "operator_dimension": row["operator_dimension"],
                    "operator_block_count": row["operator_block_count"],
                    "nonzero_operator_entries": row["nonzero_operator_entries"],
                    "dense_operator_entries_if_allocated": row["dense_operator_entries_if_allocated"],
                    "dense_state_closure_used": row["dense_state_closure_used"],
                    "dense_operator_allocated": row["dense_operator_allocated"],
                    "torch_completeness_defect": row["torch_completeness_defect"],
                    "torch_leaky_control_completeness_defect": row["torch_leaky_control_completeness_defect"],
                    "jax_completeness_defect": row["jax_completeness_defect"],
                    "jax_leaky_control_completeness_defect": row["jax_leaky_control_completeness_defect"],
                    "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                    "n01_order_disagreement_count": row["n01_order_witness"]["disagreement_count"],
                    "n01_order_erased_identity_disagreement_count": row["n01_order_witness"]["order_erased_identity_disagreement_count"],
                    "torch_entanglement_entropy_bits": row["torch_entanglement_entropy_bits"],
                    "torch_identity_ablation_entropy_bits": row["torch_identity_ablation_entropy_bits"],
                    "pass": row["pass"],
                }
                for dim, row in scale_rows.items()
            },
            "pass": bool(scale_pass),
        },
        "scale_rungs": scale_rows,
        "scale_details": scale_rows,
        "clifford_result": clifford_result,
        "known_value_checks": known_checks,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["load_bearing_proof.smt_load_bearing z3", "load_bearing_proof.smt_load_bearing cvc5", "sympy exact rational defect source"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_inputs": [],
        "data_or_artifact_dependencies": [],
        "required_negatives": ["leaky CNOT column", "identity entangler removed"],
        "negatives_run": list(controls.keys()),
        "kill_conditions": "Leaky control must make completeness_defect>0 and identity ablation must make Bell entropy/concurrence zero.",
        "required_artifacts": ["result JSON", "scale_ladder", "proof_results", "controls", "tool_ablations", "known_value_checks"],
        "artifacts_emitted": [str(RESULT)],
        "witness_trace_id": "sim_op_cnot_entangling_probe:permutation-channel:64",
        "pass_rule": "all 8/16/32/64 non-dense rungs pass; z3/cvc5 SMT verdict flips SAT(real)->UNSAT(leaky control); sympy exact defect is 19/100 for control; torch/clifford ablations recompute nonzero deltas; JAX mirrors torch",
        "fail_rule": "fail on dense operator allocation, missing proof flip, fake/cosmetic ablation, JAX mismatch, live leaky control, identity still entangling, or downstream promotion",
        "promotion_status": "keep_but_open",
        "claim_ceiling": "operator/channel lego evidence only; not bridge, manifold, Axis0, flux, FEP, gravity, or final admission evidence",
        "blockers": [] if all_pass else [
            name
            for name, ok in {
                "scale_ladder": scale_pass,
                "proof_flip": proof_pass,
                "tool_ablations": ablation_pass,
                "known_value_checks": known_pass,
                "jax_parity": parity_delta <= TOL,
            }.items()
            if not ok
        ],
        "all_pass": all_pass,
        "required_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "elapsed_seconds": round(time.time() - started, 6),
            "max_operator_dimension": max(SCALES),
            "dense_operator_allocated": False,
            "max_jax_vs_pytorch_delta": float(parity_delta),
            "classification": "lego",
            "promotion_allowed": False,
        },
    }
    return result


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out_path": str(RESULT), "required_pass": result["required_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
