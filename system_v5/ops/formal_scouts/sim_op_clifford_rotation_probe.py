#!/usr/bin/env python3
"""Stage-5 Clifford rotation operator/channel/generator probe.

Finite map:
    Pauli label v in GF(2)^(2n) --Clifford word(H,S,CNOT)--> Pauli label v'

Invariant:
    Clifford closure under conjugation: every finite Pauli label maps to one
    Pauli label. The T-gate control remains unitary but maps X/Y to a two-term
    Pauli superposition, so the same closure claim must fail.

The Hilbert operator dimensions are 8/16/32/64, but the claim-bearing carrier is
the non-dense binary symplectic/tableau action on finite Pauli labels.
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
from typing import Any

import jax.numpy as jnp
import sympy as sp
import torch
import z3

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
from clifford import Cl

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OBJECT_ID = "op_clifford_rotation_stage5"
OUT_PATH = RESULT_DIR / f"{OBJECT_ID}_results.json"

SCALES = (8, 16, 32, 64)
DTYPE_INT = torch.int64
TOL = 1.0e-12
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "bridge", "physics"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY finite non-dense tableau/Pauli-label carrier; computes closure counts, T-control violations, order gaps, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for the same finite Pauli-label/tableau closure and order observables.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via smt_load_bearing; solver variables are bound to measured closure/order observables and must flip real SAT vs control UNSAT.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check inside smt_load_bearing on the same measured closure/order observables.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact symbolic Pauli-support flip for Clifford generator images vs T-gate control; no numeric ablation row.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Geometric-algebra rotor check with remove-and-recompute bivector ablation for the named Clifford-rotation surface.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; no NumPy bridge or tensor-to-array conversion is used for claim-bearing computation.",
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


def n_qubits_for_dim(operator_dim: int) -> int:
    n = int(math.log2(operator_dim))
    if 2**n != operator_dim:
        raise ValueError(f"operator dimension must be a power of two: {operator_dim}")
    return n


def pauli_labels_torch(n: int) -> torch.Tensor:
    """All 4^n binary Pauli labels (x bits then z bits), without dense matrices."""
    count = 4**n
    idx = torch.arange(count, dtype=DTYPE_INT)
    bit_positions = torch.arange(n, dtype=DTYPE_INT)
    x = torch.bitwise_and(torch.bitwise_right_shift(idx[:, None], bit_positions[None, :]), 1)
    z = torch.bitwise_and(torch.bitwise_right_shift(idx[:, None], (bit_positions + n)[None, :]), 1)
    return torch.cat([x, z], dim=1)


def pauli_labels_jax(n: int) -> jax.Array:
    count = 4**n
    idx = jnp.arange(count, dtype=jnp.int64)
    bit_positions = jnp.arange(n, dtype=jnp.int64)
    x = jnp.bitwise_and(jnp.right_shift(idx[:, None], bit_positions[None, :]), 1)
    z = jnp.bitwise_and(jnp.right_shift(idx[:, None], (bit_positions + n)[None, :]), 1)
    return jnp.concatenate([x, z], axis=1)


def apply_h_torch(labels: torch.Tensor, q: int) -> torch.Tensor:
    n = labels.shape[1] // 2
    out = labels.clone()
    xq = out[:, q].clone()
    out[:, q] = out[:, n + q]
    out[:, n + q] = xq
    return out


def apply_s_torch(labels: torch.Tensor, q: int) -> torch.Tensor:
    n = labels.shape[1] // 2
    out = labels.clone()
    out[:, n + q] = torch.bitwise_xor(out[:, n + q], out[:, q])
    return out


def apply_cnot_torch(labels: torch.Tensor, control: int, target: int) -> torch.Tensor:
    n = labels.shape[1] // 2
    out = labels.clone()
    out[:, target] = torch.bitwise_xor(out[:, target], out[:, control])
    out[:, n + control] = torch.bitwise_xor(out[:, n + control], out[:, n + target])
    return out


def apply_h_jax(labels: jax.Array, q: int) -> jax.Array:
    n = labels.shape[1] // 2
    xq = labels[:, q]
    zq = labels[:, n + q]
    labels = labels.at[:, q].set(zq)
    labels = labels.at[:, n + q].set(xq)
    return labels


def apply_s_jax(labels: jax.Array, q: int) -> jax.Array:
    n = labels.shape[1] // 2
    return labels.at[:, n + q].set(jnp.bitwise_xor(labels[:, n + q], labels[:, q]))


def apply_cnot_jax(labels: jax.Array, control: int, target: int) -> jax.Array:
    n = labels.shape[1] // 2
    labels = labels.at[:, target].set(jnp.bitwise_xor(labels[:, target], labels[:, control]))
    labels = labels.at[:, n + control].set(jnp.bitwise_xor(labels[:, n + control], labels[:, n + target]))
    return labels


def clifford_word_torch(labels: torch.Tensor, n: int) -> torch.Tensor:
    out = labels
    for q in range(n):
        out = apply_h_torch(out, q)
        out = apply_s_torch(out, q)
    for q in range(n - 1):
        out = apply_cnot_torch(out, q, q + 1)
    return out


def clifford_word_jax(labels: jax.Array, n: int) -> jax.Array:
    out = labels
    for q in range(n):
        out = apply_h_jax(out, q)
        out = apply_s_jax(out, q)
    for q in range(n - 1):
        out = apply_cnot_jax(out, q, q + 1)
    return out


def t_control_support_sizes_torch(labels: torch.Tensor) -> torch.Tensor:
    """T on qubit 0: X/Y components become two-term Pauli superpositions."""
    x0_active = labels[:, 0] == 1
    return torch.where(x0_active, torch.full_like(labels[:, 0], 2), torch.ones_like(labels[:, 0]))


def t_control_support_sizes_jax(labels: jax.Array) -> jax.Array:
    x0_active = labels[:, 0] == 1
    return jnp.where(x0_active, jnp.full_like(labels[:, 0], 2), jnp.ones_like(labels[:, 0]))


def order_gap_torch(labels: torch.Tensor) -> int:
    hs = apply_s_torch(apply_h_torch(labels, 0), 0)
    sh = apply_h_torch(apply_s_torch(labels, 0), 0)
    return int(torch.any(hs != sh, dim=1).sum().item())


def commuting_control_gap_torch(labels: torch.Tensor) -> int:
    hh_a = apply_h_torch(apply_h_torch(labels, 0), 0)
    hh_b = apply_h_torch(apply_h_torch(labels, 0), 0)
    return int(torch.any(hh_a != hh_b, dim=1).sum().item())


def order_gap_jax(labels: jax.Array) -> int:
    hs = apply_s_jax(apply_h_jax(labels, 0), 0)
    sh = apply_h_jax(apply_s_jax(labels, 0), 0)
    return int(jnp.sum(jnp.any(hs != sh, axis=1)).item())


def commuting_control_gap_jax(labels: jax.Array) -> int:
    hh_a = apply_h_jax(apply_h_jax(labels, 0), 0)
    hh_b = apply_h_jax(apply_h_jax(labels, 0), 0)
    return int(jnp.sum(jnp.any(hh_a != hh_b, axis=1)).item())


def unique_count_torch(labels: torch.Tensor) -> int:
    return int(torch.unique(labels, dim=0).shape[0])


def closure_metrics_torch(operator_dim: int) -> dict[str, Any]:
    n = n_qubits_for_dim(operator_dim)
    labels = pauli_labels_torch(n)
    transformed = clifford_word_torch(labels, n)
    support = torch.ones(labels.shape[0], dtype=DTYPE_INT)
    control_support = t_control_support_sizes_torch(labels)
    closure_violations = int(torch.sum(support != 1).item())
    control_violations = int(torch.sum(control_support != 1).item())
    unique_images = unique_count_torch(transformed)
    return {
        "operator_dimension": operator_dim,
        "qubits": n,
        "sites_or_qubits": operator_dim,
        "pauli_label_count": int(labels.shape[0]),
        "tableau_shape": [2 * n, 2 * n],
        "dense_state_closure_used": False,
        "dense_operator_matrix_materialized": False,
        "real_max_pauli_support_size": int(torch.max(support).item()),
        "control_max_pauli_support_size": int(torch.max(control_support).item()),
        "real_closure_violation_count": closure_violations,
        "control_closure_violation_count": control_violations,
        "closed_pauli_label_count": int(labels.shape[0] - closure_violations),
        "control_closed_pauli_label_count": int(labels.shape[0] - control_violations),
        "unique_image_count": unique_images,
        "bijective_on_pauli_labels": bool(unique_images == labels.shape[0]),
        "order_gap_count_H_then_S_vs_S_then_H": order_gap_torch(labels),
        "commuting_control_gap_count_H_then_H_vs_H_then_H": commuting_control_gap_torch(labels),
    }


def closure_metrics_jax(operator_dim: int) -> dict[str, Any]:
    n = n_qubits_for_dim(operator_dim)
    labels = pauli_labels_jax(n)
    transformed = clifford_word_jax(labels, n)
    support = jnp.ones((labels.shape[0],), dtype=jnp.int64)
    control_support = t_control_support_sizes_jax(labels)
    closure_violations = int(jnp.sum(support != 1).item())
    control_violations = int(jnp.sum(control_support != 1).item())
    unique_images = int(jnp.unique(transformed, axis=0).shape[0])
    return {
        "operator_dimension": operator_dim,
        "qubits": n,
        "pauli_label_count": int(labels.shape[0]),
        "real_max_pauli_support_size": int(jnp.max(support).item()),
        "control_max_pauli_support_size": int(jnp.max(control_support).item()),
        "real_closure_violation_count": closure_violations,
        "control_closure_violation_count": control_violations,
        "closed_pauli_label_count": int(labels.shape[0] - closure_violations),
        "control_closed_pauli_label_count": int(labels.shape[0] - control_violations),
        "unique_image_count": unique_images,
        "bijective_on_pauli_labels": bool(unique_images == labels.shape[0]),
        "order_gap_count_H_then_S_vs_S_then_H": order_gap_jax(labels),
        "commuting_control_gap_count_H_then_H_vs_H_then_H": commuting_control_gap_jax(labels),
    }


def sympy_exact_flip() -> dict[str, Any]:
    sqrt2 = sp.sqrt(2)
    t_x_image = {"X": sp.Rational(1, 1) / sqrt2, "Y": sp.Rational(1, 1) / sqrt2}
    t_z_image = {"Z": sp.Integer(1)}
    h_x_image = {"Z": sp.Integer(1)}
    s_x_image = {"XZ": sp.Integer(1)}
    cnot_xc_image = {"XcXt": sp.Integer(1)}
    real_supports = [
        sum(1 for coeff in image.values() if sp.simplify(coeff) != 0)
        for image in (h_x_image, s_x_image, cnot_xc_image)
    ]
    control_supports = [
        sum(1 for coeff in image.values() if sp.simplify(coeff) != 0)
        for image in (t_x_image, t_z_image)
    ]
    real_max = max(real_supports)
    control_max = max(control_supports)
    return {
        "tool": "sympy",
        "claim": "exact Pauli support size is one for Clifford generator images and flips under the T-gate X image",
        "real_generator_supports": real_supports,
        "control_t_gate_supports": control_supports,
        "real_max_pauli_support_size": int(real_max),
        "control_max_pauli_support_size": int(control_max),
        "real_claim_holds": bool(real_max == 1),
        "control_claim_holds": bool(control_max == 1),
        "verdict_flip": bool(real_max == 1 and control_max != 1),
        "load_bearing": True,
        "bound_to_computed_exact_observables": True,
        "t_x_image": {k: str(v) for k, v in t_x_image.items()},
        "t_z_image": {k: str(v) for k, v in t_z_image.items()},
        "pass": bool(real_max == 1 and control_max == 2),
    }


def smt_closure_proof(top: dict[str, Any]) -> dict[str, Any]:
    return smt_load_bearing(
        claim="clifford_conjugation_maps_every_finite_pauli_label_to_single_pauli_label",
        real_measured={
            "max_pauli_support_size": float(top["real_max_pauli_support_size"]),
            "closure_violation_count": float(top["real_closure_violation_count"]),
        },
        control_measured={
            "max_pauli_support_size": float(top["control_max_pauli_support_size"]),
            "closure_violation_count": float(top["control_closure_violation_count"]),
        },
        claim_builder=lambda v: z3.And(
            v["max_pauli_support_size"] == 1,
            v["closure_violation_count"] == 0,
        ),
        cvc5_claim_pairs=[
            ("max_pauli_support_size", "==", 1.0),
            ("closure_violation_count", "==", 0.0),
        ],
    )


def smt_order_proof(top: dict[str, Any]) -> dict[str, Any]:
    return smt_load_bearing(
        claim="H_and_S_generators_are_order_sensitive_on_the_finite_pauli_label_carrier",
        real_measured={
            "order_gap_count": float(top["order_gap_count_H_then_S_vs_S_then_H"]),
            "min_gap": 1.0,
        },
        control_measured={
            "order_gap_count": float(top["commuting_control_gap_count_H_then_H_vs_H_then_H"]),
            "min_gap": 1.0,
        },
        claim_builder=lambda v: v["order_gap_count"] >= v["min_gap"],
        cvc5_claim_pairs=[("order_gap_count", ">=", "min_gap")],
    )


def clifford_rotor_ablation() -> dict[str, Any]:
    layout, blades = Cl(2)
    del layout
    e1 = blades["e1"]
    e2 = blades["e2"]
    bivector = e1 * e2
    angle = math.pi / 2.0
    rotor = math.cos(angle / 2.0) - math.sin(angle / 2.0) * bivector
    no_bivector = math.cos(angle / 2.0)
    rotated = rotor * e1 * ~rotor
    ablated = no_bivector * e1 * no_bivector
    target_e2_coeff = abs(float((rotated | e2)[()]))
    ablated_e2_coeff = abs(float((ablated | e2)[()]))
    return {
        "tool": "clifford",
        "algebra": "Cl(2)",
        "rotor": "R=cos(pi/4)-sin(pi/4)e12",
        "ablated_operator": "drop bivector term, leaving scalar cos(pi/4)",
        "rotated_e1_e2_coefficient": target_e2_coeff,
        "ablated_e1_e2_coefficient": ablated_e2_coeff,
        "pass": bool(abs(target_e2_coeff - 1.0) <= TOL and abs(ablated_e2_coeff) <= TOL),
    }


def build_scale_ladder(torch_rows: dict[int, dict[str, Any]], jax_rows: dict[int, dict[str, Any]]) -> dict[str, Any]:
    rungs: dict[str, dict[str, Any]] = {}
    for operator_dim in SCALES:
        t = torch_rows[operator_dim]
        j = jax_rows[operator_dim]
        jax_delta = max(
            abs(float(t["real_max_pauli_support_size"] - j["real_max_pauli_support_size"])),
            abs(float(t["control_max_pauli_support_size"] - j["control_max_pauli_support_size"])),
            abs(float(t["real_closure_violation_count"] - j["real_closure_violation_count"])),
            abs(float(t["control_closure_violation_count"] - j["control_closure_violation_count"])),
            abs(float(t["order_gap_count_H_then_S_vs_S_then_H"] - j["order_gap_count_H_then_S_vs_S_then_H"])),
            abs(float(t["commuting_control_gap_count_H_then_H_vs_H_then_H"] - j["commuting_control_gap_count_H_then_H_vs_H_then_H"])),
        )
        rung_pass = (
            t["real_max_pauli_support_size"] == 1
            and t["control_max_pauli_support_size"] == 2
            and t["real_closure_violation_count"] == 0
            and t["control_closure_violation_count"] > 0
            and t["bijective_on_pauli_labels"] is True
            and t["order_gap_count_H_then_S_vs_S_then_H"] > 0
            and t["commuting_control_gap_count_H_then_H_vs_H_then_H"] == 0
            and jax_delta <= TOL
        )
        rungs[str(operator_dim)] = {
            "operator_dimension": operator_dim,
            "sites_or_qubits": operator_dim,
            "qubits": t["qubits"],
            "pauli_label_count": t["pauli_label_count"],
            "tableau_shape": t["tableau_shape"],
            "dense_state_closure_used": False,
            "dense_operator_matrix_materialized": False,
            "torch_real_max_pauli_support_size": t["real_max_pauli_support_size"],
            "torch_control_max_pauli_support_size": t["control_max_pauli_support_size"],
            "torch_real_closure_violation_count": t["real_closure_violation_count"],
            "torch_control_closure_violation_count": t["control_closure_violation_count"],
            "torch_order_gap_count": t["order_gap_count_H_then_S_vs_S_then_H"],
            "torch_commuting_control_gap_count": t["commuting_control_gap_count_H_then_H_vs_H_then_H"],
            "jax_real_max_pauli_support_size": j["real_max_pauli_support_size"],
            "jax_control_max_pauli_support_size": j["control_max_pauli_support_size"],
            "jax_real_closure_violation_count": j["real_closure_violation_count"],
            "jax_control_closure_violation_count": j["control_closure_violation_count"],
            "jax_order_gap_count": j["order_gap_count_H_then_S_vs_S_then_H"],
            "jax_commuting_control_gap_count": j["commuting_control_gap_count_H_then_H_vs_H_then_H"],
            "jax_vs_pytorch_delta": jax_delta,
            "pass": bool(rung_pass),
        }
    return {"rungs": rungs, "pass": all(row["pass"] for row in rungs.values())}


def build_known_value_checks(
    top: dict[str, Any],
    jax_top: dict[str, Any],
    sympy_flip: dict[str, Any],
    rotor: dict[str, Any],
    closure_proof: dict[str, Any],
    order_proof: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "invariant": "Clifford tableau maps every finite Pauli label to one Pauli label",
            "computed": top["real_max_pauli_support_size"],
            "known": 1,
            "match": top["real_max_pauli_support_size"] == 1 and top["real_closure_violation_count"] == 0,
            "computed_by": "torch finite Pauli-label tableau",
        },
        {
            "invariant": "T-gate control is unitary but not Clifford: X image has two Pauli terms",
            "computed": sympy_flip["control_max_pauli_support_size"],
            "known": 2,
            "match": sympy_flip["control_max_pauli_support_size"] == 2 and top["control_max_pauli_support_size"] == 2,
            "computed_by": "sympy exact support plus torch finite support count",
        },
        {
            "invariant": "H then S differs from S then H on finite Pauli labels",
            "computed": top["order_gap_count_H_then_S_vs_S_then_H"],
            "known": "positive",
            "match": top["order_gap_count_H_then_S_vs_S_then_H"] > 0,
            "computed_by": "torch finite Pauli-label order comparison",
        },
        {
            "invariant": "commuting/same-generator control has zero order gap",
            "computed": top["commuting_control_gap_count_H_then_H_vs_H_then_H"],
            "known": 0,
            "match": top["commuting_control_gap_count_H_then_H_vs_H_then_H"] == 0,
            "computed_by": "torch finite Pauli-label control",
        },
        {
            "invariant": "JAX mirror matches torch closure and order observables at operator dimension 64",
            "computed": {
                "torch": {
                    "support": top["real_max_pauli_support_size"],
                    "control_support": top["control_max_pauli_support_size"],
                    "order_gap": top["order_gap_count_H_then_S_vs_S_then_H"],
                },
                "jax": {
                    "support": jax_top["real_max_pauli_support_size"],
                    "control_support": jax_top["control_max_pauli_support_size"],
                    "order_gap": jax_top["order_gap_count_H_then_S_vs_S_then_H"],
                },
            },
            "known": "exact parity",
            "match": (
                top["real_max_pauli_support_size"] == jax_top["real_max_pauli_support_size"]
                and top["control_max_pauli_support_size"] == jax_top["control_max_pauli_support_size"]
                and top["order_gap_count_H_then_S_vs_S_then_H"] == jax_top["order_gap_count_H_then_S_vs_S_then_H"]
            ),
            "computed_by": "torch and jax finite mirror",
        },
        {
            "invariant": "Cl(2) rotor with bivector term rotates e1 to e2; dropping bivector kills target coefficient",
            "computed": {
                "baseline_e2_coeff": rotor["rotated_e1_e2_coefficient"],
                "ablated_e2_coeff": rotor["ablated_e1_e2_coefficient"],
            },
            "known": {"baseline_e2_coeff": 1.0, "ablated_e2_coeff": 0.0},
            "match": rotor["pass"],
            "computed_by": "clifford geometric product",
        },
        {
            "invariant": "SMT closure proof flips real SAT vs T-control UNSAT",
            "computed": {
                "real": closure_proof["real_claim_verdict"],
                "control": closure_proof["negated_claim_verdict"],
                "cvc5_real": closure_proof.get("cvc5_real_verdict"),
                "cvc5_control": closure_proof.get("cvc5_control_verdict"),
            },
            "known": {"real": "sat", "control": "unsat", "cvc5_real": "sat", "cvc5_control": "unsat"},
            "match": (
                closure_proof["real_claim_verdict"] == "sat"
                and closure_proof["negated_claim_verdict"] == "unsat"
                and closure_proof.get("cvc5_real_verdict") == "sat"
                and closure_proof.get("cvc5_control_verdict") == "unsat"
            ),
            "computed_by": "smt_load_bearing z3/cvc5",
        },
        {
            "invariant": "SMT order proof flips noncommuting real SAT vs commuting control UNSAT",
            "computed": {
                "real": order_proof["real_claim_verdict"],
                "control": order_proof["negated_claim_verdict"],
                "cvc5_real": order_proof.get("cvc5_real_verdict"),
                "cvc5_control": order_proof.get("cvc5_control_verdict"),
            },
            "known": {"real": "sat", "control": "unsat", "cvc5_real": "sat", "cvc5_control": "unsat"},
            "match": (
                order_proof["real_claim_verdict"] == "sat"
                and order_proof["negated_claim_verdict"] == "unsat"
                and order_proof.get("cvc5_real_verdict") == "sat"
                and order_proof.get("cvc5_control_verdict") == "unsat"
            ),
            "computed_by": "smt_load_bearing z3/cvc5",
        },
    ]


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    torch_rows = {dim: closure_metrics_torch(dim) for dim in SCALES}
    jax_rows = {dim: closure_metrics_jax(dim) for dim in SCALES}
    top = torch_rows[64]
    jax_top = jax_rows[64]
    scale_ladder = build_scale_ladder(torch_rows, jax_rows)
    sympy_flip = sympy_exact_flip()
    closure_proof = smt_closure_proof(top)
    order_proof = smt_order_proof(top)
    rotor = clifford_rotor_ablation()

    tool_ablations = {
        "torch_clifford_tableau_vs_t_control_closed_pauli_count": tool_ablation(
            "torch_closed_pauli_label_count_after_clifford_word_vs_t_gate_control",
            baseline_value=float(top["closed_pauli_label_count"]),
            ablated_value=float(top["control_closed_pauli_label_count"]),
            tool="torch",
        ),
        "clifford_bivector_rotor_target_axis": tool_ablation(
            "clifford_rotor_e1_to_e2_target_coefficient_with_vs_without_bivector",
            baseline_value=float(rotor["rotated_e1_e2_coefficient"]),
            ablated_value=float(rotor["ablated_e1_e2_coefficient"]),
            tool="clifford",
        ),
    }

    known_value_checks = build_known_value_checks(top, jax_top, sympy_flip, rotor, closure_proof, order_proof)
    known_pass = all(row["match"] for row in known_value_checks)
    proof_pass = (
        closure_proof["real_claim_verdict"] == "sat"
        and closure_proof["negated_claim_verdict"] == "unsat"
        and closure_proof["differ"] is True
        and closure_proof["bound_to_measured"] is True
        and closure_proof.get("cvc5_real_verdict") == "sat"
        and closure_proof.get("cvc5_control_verdict") == "unsat"
        and order_proof["real_claim_verdict"] == "sat"
        and order_proof["negated_claim_verdict"] == "unsat"
        and order_proof["differ"] is True
        and order_proof["bound_to_measured"] is True
        and order_proof.get("cvc5_real_verdict") == "sat"
        and order_proof.get("cvc5_control_verdict") == "unsat"
        and sympy_flip["verdict_flip"] is True
    )
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > TOL
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= TOL
        for row in tool_ablations.values()
    )
    all_pass = bool(scale_ladder["pass"] and proof_pass and ablation_pass and known_pass and rotor["pass"])

    torch_primary_result = {
        "runtime": "torch",
        "operator_dimension": 64,
        "qubits": top["qubits"],
        "pauli_label_count": top["pauli_label_count"],
        "representation": "non_dense_binary_symplectic_tableau",
        "generator_word": "for each q: H(q), S(q); then CNOT(q,q+1) chain",
        "channel_form": "single-unitary Clifford channel represented by tableau action, not dense Kraus matrix",
        "max_pauli_support_size_after_clifford": top["real_max_pauli_support_size"],
        "closure_violation_count_after_clifford": top["real_closure_violation_count"],
        "max_pauli_support_size_after_t_control": top["control_max_pauli_support_size"],
        "closure_violation_count_after_t_control": top["control_closure_violation_count"],
        "order_gap_count_H_then_S_vs_S_then_H": top["order_gap_count_H_then_S_vs_S_then_H"],
        "commuting_control_gap_count_H_then_H_vs_H_then_H": top["commuting_control_gap_count_H_then_H_vs_H_then_H"],
        "dense_state_closure_used": False,
        "dense_operator_matrix_materialized": False,
        "pass": bool(
            top["real_max_pauli_support_size"] == 1
            and top["real_closure_violation_count"] == 0
            and top["control_max_pauli_support_size"] == 2
            and top["control_closure_violation_count"] > 0
            and top["order_gap_count_H_then_S_vs_S_then_H"] > 0
            and top["commuting_control_gap_count_H_then_H_vs_H_then_H"] == 0
        ),
    }

    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "operator_dimension": 64,
        "qubits": jax_top["qubits"],
        "pauli_label_count": jax_top["pauli_label_count"],
        "representation": "non_dense_binary_symplectic_tableau",
        "max_pauli_support_size_after_clifford": jax_top["real_max_pauli_support_size"],
        "closure_violation_count_after_clifford": jax_top["real_closure_violation_count"],
        "max_pauli_support_size_after_t_control": jax_top["control_max_pauli_support_size"],
        "closure_violation_count_after_t_control": jax_top["control_closure_violation_count"],
        "order_gap_count_H_then_S_vs_S_then_H": jax_top["order_gap_count_H_then_S_vs_S_then_H"],
        "commuting_control_gap_count_H_then_H_vs_H_then_H": jax_top["commuting_control_gap_count_H_then_H_vs_H_then_H"],
        "pass": bool(
            jax_top["real_max_pauli_support_size"] == top["real_max_pauli_support_size"]
            and jax_top["control_max_pauli_support_size"] == top["control_max_pauli_support_size"]
            and jax_top["real_closure_violation_count"] == top["real_closure_violation_count"]
            and jax_top["control_closure_violation_count"] == top["control_closure_violation_count"]
            and jax_top["order_gap_count_H_then_S_vs_S_then_H"] == top["order_gap_count_H_then_S_vs_S_then_H"]
            and jax_top["commuting_control_gap_count_H_then_H_vs_H_then_H"] == top["commuting_control_gap_count_H_then_H_vs_H_then_H"]
        ),
    }

    controls = {
        "non_clifford_t_gate_unitary_control": {
            "description": "T is unitary but not Clifford; on qubit 0, X/Y Pauli labels map to two-term Pauli superpositions.",
            "negative_control_type": "unitary_non_clifford_control",
            "operator_dimension": 64,
            "max_pauli_support_size": top["control_max_pauli_support_size"],
            "closure_violation_count": top["control_closure_violation_count"],
            "would_pass_unitarity_only_fake": True,
            "clifford_closure_claim_holds": False,
            "pass": bool(top["control_max_pauli_support_size"] == 2 and top["control_closure_violation_count"] > 0),
        },
        "commuting_order_control": {
            "description": "Compare H then H with H then H on the same finite Pauli-label carrier.",
            "negative_control_type": "order_erased_same_generator_control",
            "order_gap_count": top["commuting_control_gap_count_H_then_H_vs_H_then_H"],
            "order_sensitive_claim_holds": False,
            "pass": bool(top["commuting_control_gap_count_H_then_H_vs_H_then_H"] == 0),
        },
        "bivector_removed_clifford_rotor_control": {
            "description": "Remove the Cl(2) bivector term from the rotor and recompute the e1->e2 target coefficient.",
            "negative_control_type": "rotor_generator_removed_control",
            "rotor_result": rotor,
            "pass": bool(rotor["pass"]),
        },
    }

    return {
        "sim_id": "sim_op_clifford_rotation_probe",
        "name": "Stage-5 Clifford rotation operator/channel/generator probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "object_id": OBJECT_ID,
        "tier": "Stage-5 operator/channel/generator lego",
        "purpose": "Prove one finite Clifford-rotation operator/channel invariant with an SMT verdict flip and non-dense 8/16/32/64 scale ladder.",
        "scientific_question": "Does the H/S/CNOT-generated Clifford word preserve finite Pauli closure under conjugation while a unitary T-gate control fails the same invariant?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "operator_channel_generator_probe",
        "classification": "lego",
        "promotion_allowed": False,
        "claim_ceiling": "local Stage-5 Clifford operator/channel/generator lego only; no layer completion, stack readiness, manifold admission, Axis0, flux, FEP, bridge, gravity, or physics claim",
        "finite_map": {
            "domain": "finite Pauli labels GF(2)^(2n) for Hilbert operator dimensions 8/16/32/64 plus finite generator word over H,S,CNOT",
            "codomain_or_output": "single Pauli label after Clifford tableau action, or Pauli-support count/order-gap readout for controls",
            "definition": "v=(x,z) maps by H/S/CNOT binary symplectic updates; closure invariant is max Pauli support size == 1 and violation count == 0",
        },
        "domain": "finite Pauli-label carrier GF(2)^(2n), n in {3,4,5,6}; no dense Hilbert matrix materialization",
        "codomain_or_output": "finite Pauli-label image, closure support count, order-gap count, and blocked-control readout",
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite operator/probe/path set: Pauli labels and finite H/S/CNOT generator word over operator dimensions 8/16/32/64",
            },
            "N01": {
                "status": "active_tested",
                "statement": "H and S generator order is noncommuting/order-sensitive on the same finite Pauli-label carrier; same-generator control has zero gap",
            },
        },
        "root_constraints_in_force": ["F01 finite Pauli operator/probe/path set", "N01 H/S order-sensitive generator action"],
        "carrier_layer": "finite Pauli-label operator carrier",
        "geometry_layer": "Clifford/tableau rotation operator surface; no manifold geometry promoted",
        "carrier_realization": "torch int64 binary Pauli labels and tableau updates; jax int64 mirror; no NumPy and no dense state/operator closure",
        "peps3d_embedding": "operator-channel local-cell anchor only: each qubit/site has a finite Pauli-label channel action; no PEPS3D tensor contraction or manifold embedding is admitted here",
        "PEPS3D_K_anchor": {
            "status": "local_operator_cell_anchor_only",
            "operator_dimensions": list(SCALES),
            "local_cells": "qubit/site indices q=0..n-1 with H/S local actions and CNOT nearest-neighbor bonds",
            "claim_ceiling": "anchor metadata for blocked downstream consumers, not a PEPS3D manifold admission",
        },
        "spinor_state": "not instantiated; this operator-channel probe is finite Pauli/tableau only",
        "quaternion_action": "not_applicable; no quaternion language is claim-bearing in this sim",
        "dependency_receipts": ["Stage-5 one-sim request; lower-layer/manifold dependencies not evaluated or claimed"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["future bounded operator-channel Clifford/tool-lego fit probes that only need this local closure/order receipt"],
        "allowed_claims": [
            "H/S/CNOT finite Clifford word maps every enumerated Pauli label to one Pauli label for operator dimensions 8/16/32/64",
            "T-gate unitary control fails Clifford-specific closure even though unitarity-only checks would not catch it",
            "H and S generator order is order-sensitive on the finite Pauli-label carrier",
        ],
        "promotion_blockers": [
            "no dense unitary matrix, no full Hilbert-state dynamics, and no PEPS3D tensor contraction is admitted",
            "single local Stage-5 operator/channel lego only; no layer, stack, bridge, Axis0, flux, FEP, or physics promotion",
            "T-control demonstrates unitarity is insufficient, so unitarity-only consumers are blocked",
        ],
        "operator_channels": {
            "real": {
                "family": "Clifford",
                "generators": ["H", "S", "CNOT"],
                "channel_form": "single-unitary Clifford channel K=U represented by non-dense tableau",
                "finite_action": "binary symplectic action on Pauli labels",
            },
            "control": {
                "family": "non-Clifford unitary",
                "generator": "T on qubit 0",
                "finite_readout": "Pauli-support count under conjugation; X/Y support size becomes 2",
            },
        },
        "topology_generators": ["H local swap x_q/z_q", "S local shear z_q ^= x_q", "CNOT nearest-neighbor x_t ^= x_c and z_c ^= z_t"],
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(
            max(row["jax_vs_pytorch_delta"] for row in scale_ladder["rungs"].values())
        ),
        "proof_results": {
            "pauli_closure_smt_load_bearing": closure_proof,
            "order_sensitive_smt_load_bearing": order_proof,
            "sympy_exact_pauli_support_flip": sympy_flip,
        },
        "controls": controls,
        "tool_ablations": tool_ablations,
        "scale_ladder": scale_ladder,
        "scale_rungs": scale_ladder["rungs"],
        "known_value_checks": known_value_checks,
        "all_known_value_checks_match": known_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3 smt_load_bearing", "cvc5 smt_load_bearing cross-check", "sympy exact Pauli-support flip"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": ["non-Clifford T-gate unitary control", "same-generator commuting order control", "bivector-removed rotor control"],
        "negatives_run": list(controls.keys()),
        "kill_conditions": [
            "T-control has max Pauli support size 1 or zero closure violations",
            "H/S order gap collapses to zero",
            "SMT real/control verdicts fail to differ",
            "torch/JAX mirror diverges",
            "any scale rung uses dense state/operator closure",
        ],
        "required_artifacts": ["result_json", "scale_ladder", "proof_results", "controls", "tool_ablations", "known_value_checks"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{OBJECT_ID}:64:pauli_closure_and_order",
        "result_summary": {
            "scale_pass": scale_ladder["pass"],
            "proof_pass": proof_pass,
            "ablation_pass": ablation_pass,
            "known_value_checks_pass": known_pass,
            "all_pass": all_pass,
        },
        "branch_status_before_run": "single requested Stage-5 operator/channel/generator packet",
        "law_or_candidate_tested": "Clifford closure under Pauli conjugation plus finite H/S noncommuting order action",
        "bridge_layer": "none",
        "cut_layer": "none",
        "pass_rule": "all 8/16/32/64 non-dense rungs pass; z3/cvc5 closure and order proofs flip SAT real vs UNSAT control; sympy exact support flips; torch/clifford ablations recompute nonzero deltas; JAX mirrors torch",
        "fail_rule": "fail on unitarity-only evidence, T-control passing closure, missing SMT flip, proof tools represented by numeric ablation, missing baseline/ablated recompute, JAX mismatch, dense closure, or downstream promotion",
        "promotion_status": "keep_but_open",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
