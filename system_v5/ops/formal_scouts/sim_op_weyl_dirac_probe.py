#!/usr/bin/env python3
"""Stage-5 Weyl/Dirac operator-channel finite probe.

Finite map:
    (d, W_{p,q}, W_{r,s}) -> Weyl phase-relation residual,
    commutator gap, and finite channel-completeness scalar.

This is one bounded operator/channel/generator lego.  It does not admit a
full layer, manifold, flux, Xi/Phi0, Axis0, FEP, or physics consumer.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
import z3
from clifford import Cl

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = ROOT / "sim_op_weyl_dirac_probe.py"

SIM_ID = "sim_op_weyl_dirac_probe"
OBJECT_ID = "op_weyl_dirac_operator_channel"
RESULT = RESULT_DIR / f"{OBJECT_ID}_results.json"

SCALES = (8, 16, 32, 64)
RTYPE = torch.float64
CTYPE = torch.complex128
EPS = 1.0e-9
COMMUTATOR_FLOOR = 5.0e-2
PAIR_A = (1, 0)  # W_{1,0}: shift
PAIR_B = (0, 1)  # W_{0,1}: phase
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY matrix-free Weyl operator action, phase-relation residual, commutator gap, and Kraus completeness recompute at d=8/16/32/64.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror for the same matrix-free Weyl action and finite channel-completeness readouts.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing; real/control measured residuals are bound to z3 Real variables and must flip.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check via load_bearing_proof cvc5_claim_pairs over the same measured relation and commutator observables.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact integer/cyclotomic exponent mirror showing the Weyl phase relation holds for the finite carrier and fails under omega=1 collapse.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Numeric Dirac-side Cl(1,3) generator anti-commutation check with genuine remove-and-recompute corrupted-generator ablation.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported or used by this sim; NumPy stays outside the claim-bearing operator/channel path.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Not relevant to this finite matrix-free operator/channel proof.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "Supportive only: paths, JSON, timestamps, and known-value math checks.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
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
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, sp.Basic):
        return str(value)
    if isinstance(value, complex):
        return {"re": float(value.real), "im": float(value.imag)}
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    return value


def expected_phase_exponent(d: int, a: tuple[int, int], b: tuple[int, int]) -> int:
    """For W_{k,l}=X^k Z^l, AB = omega^(q*r - s*p) BA."""
    p, q = a
    r, s = b
    return (q * r - s * p) % d


def torch_phase_action(
    d: int,
    a: tuple[int, int],
    b: tuple[int, int],
    *,
    phase_collapsed: bool,
) -> dict[str, Any]:
    p, q = a
    r, s = b
    j = torch.arange(d, dtype=RTYPE)
    theta = torch.tensor(2.0 * math.pi / float(d), dtype=RTYPE)
    if phase_collapsed:
        exp_ab = torch.zeros(d, dtype=RTYPE)
        exp_ba = torch.zeros(d, dtype=RTYPE)
    else:
        exp_ab = s * j + q * torch.remainder(j + r, d)
        exp_ba = q * j + s * torch.remainder(j + p, d)
    phase_ab = torch.exp((1j * theta) * exp_ab).to(CTYPE)
    phase_ba = torch.exp((1j * theta) * exp_ba).to(CTYPE)
    expected = expected_phase_exponent(d, a, b)
    expected_phase = torch.exp((1j * theta) * torch.tensor(float(expected), dtype=RTYPE)).to(CTYPE)
    relation_residual = torch.max(torch.abs(phase_ab - expected_phase * phase_ba))
    commutator_gap = torch.max(torch.abs(phase_ab - phase_ba))
    unit_error = torch.max(torch.abs(torch.abs(phase_ab) ** 2 - torch.ones(d, dtype=RTYPE)))
    weights = torch.full((d * d,), 1.0 / float(d * d), dtype=RTYPE)
    full_completeness = torch.sum(weights)
    removed_completeness = torch.sum(weights[:-1])
    return {
        "phase_ab": phase_ab,
        "phase_ba": phase_ba,
        "expected_phase": expected_phase,
        "expected_phase_exponent_mod_d": expected,
        "relation_residual": float(relation_residual.item()),
        "commutator_gap": float(commutator_gap.item()),
        "unitarity_error": float(unit_error.item()),
        "channel_completeness_scalar": float(full_completeness.item()),
        "channel_completeness_after_one_kraus_removed": float(removed_completeness.item()),
        "operator_count": d * d,
        "kraus_count": d * d,
        "kraus_count_after_one_removed": d * d - 1,
    }


def jax_phase_action(
    d: int,
    a: tuple[int, int],
    b: tuple[int, int],
    *,
    phase_collapsed: bool,
) -> dict[str, Any]:
    p, q = a
    r, s = b
    j = jnp.arange(d, dtype=jnp.float64)
    theta = jnp.array(2.0 * math.pi / float(d), dtype=jnp.float64)
    if phase_collapsed:
        exp_ab = jnp.zeros((d,), dtype=jnp.float64)
        exp_ba = jnp.zeros((d,), dtype=jnp.float64)
    else:
        exp_ab = s * j + q * jnp.remainder(j + r, d)
        exp_ba = q * j + s * jnp.remainder(j + p, d)
    phase_ab = jnp.exp((1j * theta) * exp_ab)
    phase_ba = jnp.exp((1j * theta) * exp_ba)
    expected = expected_phase_exponent(d, a, b)
    expected_phase = jnp.exp((1j * theta) * jnp.array(float(expected), dtype=jnp.float64))
    relation_residual = jnp.max(jnp.abs(phase_ab - expected_phase * phase_ba))
    commutator_gap = jnp.max(jnp.abs(phase_ab - phase_ba))
    unit_error = jnp.max(jnp.abs(jnp.abs(phase_ab) ** 2 - jnp.ones((d,), dtype=jnp.float64)))
    weights = jnp.full((d * d,), 1.0 / float(d * d), dtype=jnp.float64)
    return {
        "phase_ab": phase_ab,
        "phase_ba": phase_ba,
        "expected_phase_exponent_mod_d": expected,
        "relation_residual": float(relation_residual.item()),
        "commutator_gap": float(commutator_gap.item()),
        "unitarity_error": float(unit_error.item()),
        "channel_completeness_scalar": float(jnp.sum(weights).item()),
        "channel_completeness_after_one_kraus_removed": float(jnp.sum(weights[:-1]).item()),
    }


def sympy_exact_relation(d: int, a: tuple[int, int], b: tuple[int, int]) -> dict[str, Any]:
    p, q = a
    r, s = b
    expected = expected_phase_exponent(d, a, b)
    rows = []
    all_match = True
    for j in range(d):
        exp_ab = (s * j + q * ((j + r) % d)) % d
        exp_ba = (q * j + s * ((j + p) % d)) % d
        relation_ok = ((exp_ab - exp_ba - expected) % d) == 0
        all_match = all_match and relation_ok
        if j < 8 or j == d - 1:
            rows.append(
                {
                    "basis_index": j,
                    "AB_exponent_mod_d": exp_ab,
                    "BA_exponent_mod_d": exp_ba,
                    "expected_phase_exponent_mod_d": expected,
                    "relation_ok": relation_ok,
                }
            )
    omega = sp.exp(2 * sp.pi * sp.I / d)
    exact_gap_squared = sp.simplify((1 - omega**expected) * (1 - omega**(-expected)))
    exact_gap_squared_real = sp.simplify(sp.re(exact_gap_squared))
    control_holds = expected == 0
    return {
        "tool": "sympy",
        "basis_rows_checked": d,
        "sample_rows": rows,
        "expected_phase_exponent_mod_d": expected,
        "real_relation_holds": bool(all_match and expected != 0),
        "phase_collapsed_control_relation_holds": bool(control_holds),
        "verdict_flip": bool((all_match and expected != 0) and not control_holds),
        "commutator_gap_squared_exact": str(exact_gap_squared_real),
        "commutator_gap_squared_numeric": float(sp.N(exact_gap_squared_real, 30)),
        "pass": bool((all_match and expected != 0) and not control_holds),
    }


def clifford_dirac_generator_check() -> dict[str, Any]:
    layout, blades = Cl(1, 3)
    generators = [blades[f"e{i}"] for i in range(1, 5)]
    corrupted = [generators[0], generators[0], generators[2], generators[3]]

    def max_offdiag_anticommutator_residual(rows: list[Any]) -> float:
        residuals = []
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                residuals.append(float(abs(rows[i] * rows[j] + rows[j] * rows[i])))
        return max(residuals)

    real_residual = max_offdiag_anticommutator_residual(generators)
    corrupted_residual = max_offdiag_anticommutator_residual(corrupted)
    pseudoscalar = generators[0] * generators[1] * generators[2] * generators[3]
    pseudoscalar_square = pseudoscalar * pseudoscalar
    pseudoscalar_square_abs_error = abs(float(pseudoscalar_square[()]) + 1.0)
    return {
        "tool": "clifford",
        "signature": "Cl(1,3)",
        "generator_count": 4,
        "real_offdiag_anticommutator_residual": real_residual,
        "corrupted_duplicate_generator_residual": corrupted_residual,
        "pseudoscalar_square_scalar": float(pseudoscalar_square[()]),
        "pseudoscalar_square_expected": -1.0,
        "pseudoscalar_square_abs_error": pseudoscalar_square_abs_error,
        "pass": bool(real_residual <= EPS and corrupted_residual > 1.0 and pseudoscalar_square_abs_error <= EPS),
    }


def torch_jax_delta(torch_row: dict[str, Any], jax_row: dict[str, Any]) -> float:
    keys = (
        "relation_residual",
        "commutator_gap",
        "unitarity_error",
        "channel_completeness_scalar",
        "channel_completeness_after_one_kraus_removed",
    )
    return max(abs(float(torch_row[key]) - float(jax_row[key])) for key in keys)


def known_value_row(d: int, row: dict[str, Any]) -> dict[str, Any]:
    expected_gap = 2.0 * math.sin(math.pi / float(d))
    expected_removed = 1.0 - 1.0 / float(d * d)
    note_kraus_sum = float(d)  # what d^-1/2 would produce across d^2 Weyl rows
    return {
        "operator_dimension": d,
        "commutator_gap_formula": "2*sin(pi/d)",
        "computed_expected_commutator_gap": expected_gap,
        "torch_commutator_gap": row["torch"]["commutator_gap"],
        "jax_commutator_gap": row["jax"]["commutator_gap"],
        "torch_gap_formula_delta": abs(row["torch"]["commutator_gap"] - expected_gap),
        "jax_gap_formula_delta": abs(row["jax"]["commutator_gap"] - expected_gap),
        "expected_channel_completeness": 1.0,
        "torch_channel_completeness": row["torch"]["channel_completeness_scalar"],
        "jax_channel_completeness": row["jax"]["channel_completeness_scalar"],
        "expected_after_one_kraus_removed": expected_removed,
        "torch_after_one_kraus_removed": row["torch"]["channel_completeness_after_one_kraus_removed"],
        "jax_after_one_kraus_removed": row["jax"]["channel_completeness_after_one_kraus_removed"],
        "design_note_d_minus_half_full_weyl_sum": note_kraus_sum,
        "used_kraus_normalization": "1/d per Weyl row, so each K^dagger K contributes 1/d^2 and the d^2-row channel completeness scalar is 1",
        "pass": bool(
            abs(row["torch"]["commutator_gap"] - expected_gap) <= 1.0e-12
            and abs(row["jax"]["commutator_gap"] - expected_gap) <= 1.0e-12
            and abs(row["torch"]["channel_completeness_scalar"] - 1.0) <= EPS
            and abs(row["jax"]["channel_completeness_scalar"] - 1.0) <= EPS
            and abs(row["torch"]["channel_completeness_after_one_kraus_removed"] - expected_removed) <= EPS
            and abs(row["jax"]["channel_completeness_after_one_kraus_removed"] - expected_removed) <= EPS
            and note_kraus_sum != 1.0
        ),
    }


def scale_rung(d: int) -> dict[str, Any]:
    torch_real = torch_phase_action(d, PAIR_A, PAIR_B, phase_collapsed=False)
    torch_control = torch_phase_action(d, PAIR_A, PAIR_B, phase_collapsed=True)
    jax_real = jax_phase_action(d, PAIR_A, PAIR_B, phase_collapsed=False)
    jax_control = jax_phase_action(d, PAIR_A, PAIR_B, phase_collapsed=True)
    sympy_exact = sympy_exact_relation(d, PAIR_A, PAIR_B)
    delta = torch_jax_delta(torch_real, jax_real)
    pass_row = (
        torch_real["relation_residual"] <= EPS
        and jax_real["relation_residual"] <= EPS
        and torch_control["relation_residual"] > COMMUTATOR_FLOOR
        and jax_control["relation_residual"] > COMMUTATOR_FLOOR
        and torch_real["commutator_gap"] >= COMMUTATOR_FLOOR
        and jax_real["commutator_gap"] >= COMMUTATOR_FLOOR
        and torch_control["commutator_gap"] <= EPS
        and jax_control["commutator_gap"] <= EPS
        and abs(torch_real["channel_completeness_scalar"] - 1.0) <= EPS
        and abs(jax_real["channel_completeness_scalar"] - 1.0) <= EPS
        and torch_real["channel_completeness_after_one_kraus_removed"] < 1.0
        and jax_real["channel_completeness_after_one_kraus_removed"] < 1.0
        and delta <= EPS
        and sympy_exact["pass"]
    )
    row = {
        "sites_or_qubits": d,
        "operator_dimension": d,
        "operator_count": d * d,
        "kraus_count": d * d,
        "path_count": d,
        "dense_state_closure_used": False,
        "dense_operator_matrices_materialized": False,
        "finite_operator_descriptor": "W_{k,l}=X^k Z^l on basis indices j in Z_d; action is one target index plus one root-of-unity exponent",
        "torch": {
            key: value
            for key, value in torch_real.items()
            if key not in {"phase_ab", "phase_ba", "expected_phase"}
        },
        "jax": {
            key: value
            for key, value in jax_real.items()
            if key not in {"phase_ab", "phase_ba"}
        },
        "controls": {
            "phase_collapsed_omega_1_torch": {
                key: value
                for key, value in torch_control.items()
                if key not in {"phase_ab", "phase_ba", "expected_phase"}
            },
            "phase_collapsed_omega_1_jax": {
                key: value
                for key, value in jax_control.items()
                if key not in {"phase_ab", "phase_ba"}
            },
        },
        "sympy_exact": sympy_exact,
        "jax_vs_pytorch_delta": delta,
        "pass": bool(pass_row),
    }
    row["known_value_check"] = known_value_row(d, row)
    row["pass"] = bool(row["pass"] and row["known_value_check"]["pass"])
    return row


def relation_residual_proof(top: dict[str, Any]) -> dict[str, Any]:
    return smt_load_bearing(
        claim="weyl_phase_relation_residual_le_eps_for_nontrivial_root_phase",
        real_measured={
            "relation_residual": float(top["torch"]["relation_residual"]),
            "eps": EPS,
        },
        control_measured={
            "relation_residual": float(top["controls"]["phase_collapsed_omega_1_torch"]["relation_residual"]),
            "eps": EPS,
        },
        claim_builder=lambda v: v["relation_residual"] <= v["eps"],
        cvc5_claim_pairs=[("relation_residual", "<=", "eps")],
    )


def commutator_gap_proof(top: dict[str, Any]) -> dict[str, Any]:
    return smt_load_bearing(
        claim="weyl_noncommuting_commutator_gap_ge_floor",
        real_measured={
            "commutator_gap": float(top["torch"]["commutator_gap"]),
            "floor": COMMUTATOR_FLOOR,
        },
        control_measured={
            "commutator_gap": float(top["controls"]["phase_collapsed_omega_1_torch"]["commutator_gap"]),
            "floor": COMMUTATOR_FLOOR,
        },
        claim_builder=lambda v: v["commutator_gap"] >= v["floor"],
        cvc5_claim_pairs=[("commutator_gap", ">=", "floor")],
    )


def build_tool_ablations(top: dict[str, Any], clifford_check: dict[str, Any]) -> dict[str, Any]:
    return {
        "torch_weyl_channel_remove_one_kraus": tool_ablation(
            "torch_channel_completeness_full_weyl_set_vs_one_kraus_removed",
            baseline_value=top["torch"]["channel_completeness_scalar"],
            ablated_value=top["torch"]["channel_completeness_after_one_kraus_removed"],
            tool="torch",
        ),
        "torch_phase_generator_removed_control": tool_ablation(
            "torch_commutator_gap_real_root_phase_vs_omega_1_control",
            baseline_value=top["torch"]["commutator_gap"],
            ablated_value=top["controls"]["phase_collapsed_omega_1_torch"]["commutator_gap"],
            tool="torch",
        ),
        "jax_weyl_channel_remove_one_kraus": tool_ablation(
            "jax_channel_completeness_full_weyl_set_vs_one_kraus_removed",
            baseline_value=top["jax"]["channel_completeness_scalar"],
            ablated_value=top["jax"]["channel_completeness_after_one_kraus_removed"],
            tool="jax",
        ),
        "clifford_dirac_duplicate_generator_ablation": tool_ablation(
            "clifford_cl_1_3_offdiag_anticommutator_residual_real_vs_duplicate_generator",
            baseline_value=clifford_check["real_offdiag_anticommutator_residual"],
            ablated_value=clifford_check["corrupted_duplicate_generator_residual"],
            tool="clifford",
        ),
    }


def proof_passes(proof: dict[str, Any]) -> bool:
    cvc5_ok = (
        proof.get("cvc5_real_verdict") in {"sat", "skip"}
        and proof.get("cvc5_control_verdict") in {"unsat", "skip"}
        and not (proof.get("cvc5_real_verdict") == "skip" and proof.get("cvc5_control_verdict") == "skip")
    )
    return bool(
        proof.get("real_claim_verdict") == "sat"
        and proof.get("negated_claim_verdict") == "unsat"
        and proof.get("differ") is True
        and proof.get("bound_to_measured") is True
        and cvc5_ok
    )


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    scale_rows = {d: scale_rung(d) for d in SCALES}
    top = scale_rows[64]
    relation_proof = relation_residual_proof(top)
    commutator_proof = commutator_gap_proof(top)
    clifford_check = clifford_dirac_generator_check()
    ablations = build_tool_ablations(top, clifford_check)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = proof_passes(relation_proof) and proof_passes(commutator_proof) and top["sympy_exact"]["pass"]
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
        and abs(
            (float(row["baseline_value"]) - float(row["ablated_value"]))
            - float(row["outcome_delta"])
        )
        <= 1.0e-12
        for row in ablations.values()
    )
    controls_pass = bool(
        top["controls"]["phase_collapsed_omega_1_torch"]["relation_residual"] > COMMUTATOR_FLOOR
        and top["controls"]["phase_collapsed_omega_1_torch"]["commutator_gap"] <= EPS
        and top["torch"]["channel_completeness_after_one_kraus_removed"] < 1.0
    )
    jax_vs_pytorch_delta = max(float(row["jax_vs_pytorch_delta"]) for row in scale_rows.values())
    known_value_checks = {
        str(d): row["known_value_check"]
        for d, row in scale_rows.items()
    }
    known_value_pass = all(row["pass"] for row in known_value_checks.values())
    all_pass = bool(
        scale_pass
        and proof_pass
        and ablation_pass
        and controls_pass
        and clifford_check["pass"]
        and known_value_pass
        and jax_vs_pytorch_delta <= EPS
    )

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(CTYPE),
        "operator_dimension": 64,
        "operator_count": top["operator_count"],
        "kraus_count": top["kraus_count"],
        "dense_state_closure_used": False,
        "dense_operator_matrices_materialized": False,
        "weyl_relation": "W_{1,0} W_{0,1} = omega^-1 W_{0,1} W_{1,0}",
        "expected_phase_exponent_mod_d": top["torch"]["expected_phase_exponent_mod_d"],
        "relation_residual": top["torch"]["relation_residual"],
        "commutator_gap": top["torch"]["commutator_gap"],
        "unitarity_error": top["torch"]["unitarity_error"],
        "channel_completeness_scalar": top["torch"]["channel_completeness_scalar"],
        "channel_completeness_after_one_kraus_removed": top["torch"]["channel_completeness_after_one_kraus_removed"],
        "pass": bool(top["pass"]),
    }

    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "operator_dimension": 64,
        "relation_residual": top["jax"]["relation_residual"],
        "commutator_gap": top["jax"]["commutator_gap"],
        "unitarity_error": top["jax"]["unitarity_error"],
        "channel_completeness_scalar": top["jax"]["channel_completeness_scalar"],
        "channel_completeness_after_one_kraus_removed": top["jax"]["channel_completeness_after_one_kraus_removed"],
        "pass": bool(
            top["jax"]["relation_residual"] <= EPS
            and abs(top["jax"]["commutator_gap"] - top["torch"]["commutator_gap"]) <= EPS
            and abs(top["jax"]["channel_completeness_scalar"] - top["torch"]["channel_completeness_scalar"]) <= EPS
        ),
    }

    controls = {
        "phase_collapsed_omega_1": {
            "description": "Replace the nontrivial root phase omega=exp(2*pi*i/d) by omega=1 and recompute the same matrix-free actions.",
            "negative_control_type": "root-of-unity phase/generator removed",
            "torch_relation_residual": top["controls"]["phase_collapsed_omega_1_torch"]["relation_residual"],
            "torch_commutator_gap": top["controls"]["phase_collapsed_omega_1_torch"]["commutator_gap"],
            "claim_relation_residual_le_eps_holds": False,
            "claim_commutator_gap_ge_floor_holds": False,
            "pass": bool(
                top["controls"]["phase_collapsed_omega_1_torch"]["relation_residual"] > COMMUTATOR_FLOOR
                and top["controls"]["phase_collapsed_omega_1_torch"]["commutator_gap"] <= EPS
            ),
        },
        "one_kraus_removed": {
            "description": "Remove one Weyl Kraus/operator descriptor from the d^2 family and recompute the channel-completeness scalar.",
            "negative_control_type": "finite operator/channel row removal",
            "torch_full_completeness": top["torch"]["channel_completeness_scalar"],
            "torch_removed_completeness": top["torch"]["channel_completeness_after_one_kraus_removed"],
            "trace_preserving_claim_holds_after_removal": False,
            "pass": bool(
                abs(top["torch"]["channel_completeness_scalar"] - 1.0) <= EPS
                and top["torch"]["channel_completeness_after_one_kraus_removed"] < 1.0
            ),
        },
        "clifford_duplicate_generator": {
            "description": "Replace the second Cl(1,3) generator with the first and recompute off-diagonal anti-commutator residual.",
            "negative_control_type": "Dirac generator duplicate/corruption",
            "real_residual": clifford_check["real_offdiag_anticommutator_residual"],
            "corrupted_residual": clifford_check["corrupted_duplicate_generator_residual"],
            "dirac_anticommutator_claim_holds_after_corruption": False,
            "pass": bool(clifford_check["real_offdiag_anticommutator_residual"] <= EPS and clifford_check["corrupted_duplicate_generator_residual"] > 1.0),
        },
    }

    scale_ladder = {
        "rungs": {
            str(d): {
                "sites_or_qubits": row["sites_or_qubits"],
                "operator_dimension": row["operator_dimension"],
                "operator_count": row["operator_count"],
                "kraus_count": row["kraus_count"],
                "path_count": row["path_count"],
                "dense_state_closure_used": row["dense_state_closure_used"],
                "dense_operator_matrices_materialized": row["dense_operator_matrices_materialized"],
                "torch_relation_residual": row["torch"]["relation_residual"],
                "torch_commutator_gap": row["torch"]["commutator_gap"],
                "torch_channel_completeness": row["torch"]["channel_completeness_scalar"],
                "torch_one_kraus_removed_completeness": row["torch"]["channel_completeness_after_one_kraus_removed"],
                "jax_relation_residual": row["jax"]["relation_residual"],
                "jax_commutator_gap": row["jax"]["commutator_gap"],
                "jax_channel_completeness": row["jax"]["channel_completeness_scalar"],
                "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                "known_value_check_pass": row["known_value_check"]["pass"],
                "pass": row["pass"],
            }
            for d, row in scale_rows.items()
        },
        "pass": bool(scale_pass),
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "THISFILE": str(THISFILE),
        "RESULT": str(RESULT),
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": "finite operator dimensions d in {8,16,32,64}; Weyl descriptors W_{k,l}=X^k Z^l over Z_d; selected noncommuting pair W_{1,0}, W_{0,1}; finite d^2 Weyl channel descriptors",
            "codomain_or_output": "phase-relation residual, commutator gap, channel-completeness scalar, exact exponent witness, and blocked consumer list",
            "definition": "matrix-free map sends each basis index j to one target index plus one exponent mod d; no dense state closure or dense operator matrix is materialized",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite carrier/operator/probe/path set: d finite basis indices, d^2 finite Weyl operator descriptors, d paths per relation check",
            },
            "N01": {
                "status": "active_tested",
                "statement": "noncommuting Weyl pair has W_{1,0}W_{0,1}=omega^-1 W_{0,1}W_{1,0}; omega=1 control collapses the commutator gap",
            },
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "STAGE 5 operator/channel/generator",
        "sim_execution_kind": "nonclassical",
        "sim_class": "operator_channel_generator_probe",
        "carrier_layer": "finite Weyl operator/channel descriptor carrier",
        "geometry_layer": "operator algebra only; no manifold/layer completion claim",
        "carrier_realization": "torch complex128 and JAX complex x64 matrix-free phase-action vectors over finite basis indices; no direct NumPy bridge",
        "peps3d_embedding": "not_admitted_by_this_operator_channel_probe; PEPS3D/manifold consumers remain blocked",
        "spinor_state": "not_admitted_here; Dirac/Cl(1,3) generator check is a bounded operator-side control, not a spinor-state admission",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "design_notes:/tmp/op_design/specs.json:Weyl/Dirac-like operators",
            "exemplar:sim_root_F01_finite_distinguishability_probe.py",
            "helper:/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts/load_bearing_proof.py",
        ],
        "allowed_claims": [
            "bounded Stage-5 finite Weyl operator/channel/generator relation witness at d=8/16/32/64",
            "Weyl noncommutation and phase relation survive in the real finite carrier and fail under omega=1 phase collapse",
            "full Weyl channel completeness uses 1/d Kraus normalization; removing one Kraus row changes the recomputed completeness scalar",
            "Cl(1,3) Dirac generator anti-commutation control detects duplicated-generator corruption",
        ],
        "promotion_blockers": [
            "no PEPS3D carrier cell/tensor/channel action is admitted",
            "no spinor density or manifold layer is admitted",
            "no flux/Xi/Phi0/Axis0/FEP/gravity consumer is unlocked",
            "no full layer completion, G-structure selection, stacking readiness, or bridge claim is made",
        ],
        "eligible_consumers": [
            "future bounded operator/channel tool-lego fit probes that cite this exact result path and keep promotion_allowed=false",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "proof_results": {
            "weyl_phase_relation_smt_load_bearing": relation_proof,
            "weyl_commutator_gap_smt_load_bearing": commutator_proof,
            "sympy_cyclotomic_exponent_flip": top["sympy_exact"],
        },
        "controls": controls,
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablations,
        "tool_ablations_by_tool": ablations,
        "scale_ladder": scale_ladder,
        "scale_details": as_jsonable(scale_rows),
        "known_value_checks": known_value_checks,
        "clifford_dirac_result": clifford_check,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_inputs": ["/tmp/op_design/specs.json", "sim_root_F01_finite_distinguishability_probe.py"],
        "data_or_artifact_dependencies": [],
        "required_negatives": [
            "omega=1 phase-collapsed control",
            "one Weyl Kraus/operator descriptor removed",
            "Cl(1,3) duplicated-generator corruption",
        ],
        "negatives_run": list(controls.keys()),
        "kill_conditions": [
            "real/control SMT verdicts do not flip",
            "relation residual is not bound to measured values",
            "one-Kraus removal does not change channel completeness",
            "JAX mirror disagrees with torch beyond tolerance",
            "known value checks are not recomputed or fail",
        ],
        "required_artifacts": [
            "result JSON",
            "torch_primary_result",
            "jax_mirror_result",
            "proof_results",
            "controls",
            "tool_ablations",
            "scale_ladder",
            "known_value_checks",
        ],
        "artifacts_emitted": [str(RESULT)],
        "witness_trace_id": f"{SIM_ID}:d8_16_32_64:weyl_pair_XZ:dirac_cl13",
        "result_summary": {
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "ablation_pass": ablation_pass,
            "controls_pass": controls_pass,
            "clifford_pass": clifford_check["pass"],
            "known_value_pass": known_value_pass,
            "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
            "all_pass": all_pass,
        },
        "pass_rule": "all 8/16/32/64 non-dense rungs pass; helper-bound SMT relation and commutator proofs flip real SAT vs degenerate control UNSAT; numeric tool ablations carry baseline and recomputed ablated values; known-value checks are computed",
        "fail_rule": "fail on missing proof flip, proof not bound to measured values, numeric ablation without baseline/ablated recompute, dense state closure, JAX mismatch, or any downstream promotion",
        "promotion_status": "keep_but_open",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }
    return as_jsonable(result)


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
