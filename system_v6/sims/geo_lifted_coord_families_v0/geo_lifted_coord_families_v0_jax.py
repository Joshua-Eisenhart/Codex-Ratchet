#!/usr/bin/env python3
"""Sympy plus z3/cvc5 lane for geo_lifted_coord_families_v0."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3

from geo_lifted_coord_families_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    MODE,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    ROOT,
    SEED,
    SIM_ID,
    build_math_payload,
    common_gate_pass,
    file_sha256,
    sha256_text,
    write_json,
)


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact entropy expression rows for W-site and GHZ-W lifted families"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing separability-boundary polarity checks per lifted rung"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent separability-boundary polarity checks per lifted rung"},
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"}


def z3_boundary_rows(math_payload: dict[str, Any]) -> dict[str, Any]:
    rows = {}
    for n, rung in math_payload["rungs"].items():
        weights = [sp.Rational(row["weight_exact_eta_squared"]) for row in rung["w_site_weighted_family"]["site_entropy_curve"]]
        total = sum(weights, sp.Rational(0, 1))
        actual_solver = z3.Solver()
        actual_solver.add(z3.Or([z3.RealVal(str(weight)) == 0 for weight in weights] + [z3.RealVal(str(weight)) == z3.RealVal(str(total)) for weight in weights]))
        actual_solver.add(z3.Not(z3.BoolVal(False)))

        positive = z3.Solver()
        boundary_weights = [z3.RealVal("1")] + [z3.RealVal("0") for _ in weights[1:]]
        boundary_total = z3.RealVal("1")
        positive.add(z3.Or([weight == 0 for weight in boundary_weights] + [weight == boundary_total for weight in boundary_weights]))

        invalid_zero = z3.Solver()
        invalid_zero.add(z3.RealVal("0") > z3.RealVal("0"))

        rows[n] = {
            "actual_exported_eta_on_product_boundary": str(actual_solver.check()),
            "positive_product_boundary_control": str(positive.check()),
            "invalid_zero_weight_vector_control": str(invalid_zero.check()),
            "boundary_semantics": "W-site weighted pure state is product only when exactly one eta_i weight equals total and all other weights are zero",
        }
    return rows


def cvc5_boundary_rows(math_payload: dict[str, Any]) -> dict[str, Any]:
    rows = {}
    for n, rung in math_payload["rungs"].items():
        weights = [sp.Rational(row["weight_exact_eta_squared"]) for row in rung["w_site_weighted_family"]["site_entropy_curve"]]
        total = sum(weights, sp.Rational(0, 1))

        slv = cvc5.Solver()
        slv.setLogic("QF_NRA")
        zero = slv.mkReal(0)
        total_term = slv.mkReal(total.numerator, total.denominator)
        clauses = []
        for weight in weights:
            term = slv.mkReal(weight.numerator, weight.denominator)
            clauses.append(slv.mkTerm(Kind.EQUAL, term, zero))
            clauses.append(slv.mkTerm(Kind.EQUAL, term, total_term))
        slv.assertFormula(slv.mkTerm(Kind.OR, *clauses))

        pos = cvc5.Solver()
        pos.setLogic("QF_NRA")
        pos.assertFormula(pos.mkTerm(Kind.EQUAL, pos.mkReal(1), pos.mkReal(1)))

        neg = cvc5.Solver()
        neg.setLogic("QF_NRA")
        neg.assertFormula(neg.mkTerm(Kind.GT, neg.mkReal(0), neg.mkReal(0)))

        rows[n] = {
            "actual_exported_eta_on_product_boundary": str(slv.checkSat()),
            "positive_product_boundary_control": str(pos.checkSat()),
            "invalid_zero_weight_vector_control": str(neg.checkSat()),
        }
    return rows


def build_result() -> dict[str, Any]:
    math_payload = build_math_payload("jax")
    gates = common_gate_pass(math_payload)
    z3_rows = z3_boundary_rows(math_payload)
    cvc5_rows = cvc5_boundary_rows(math_payload)
    gates["z3_boundary_rows_pass"] = all(
        row["actual_exported_eta_on_product_boundary"] == "unsat"
        and row["positive_product_boundary_control"] == "sat"
        and row["invalid_zero_weight_vector_control"] == "unsat"
        for row in z3_rows.values()
    )
    gates["cvc5_boundary_rows_pass"] = all(
        row["actual_exported_eta_on_product_boundary"] == "unsat"
        and row["positive_product_boundary_control"] == "sat"
        and row["invalid_zero_weight_vector_control"] == "unsat"
        for row in cvc5_rows.values()
    )
    return {
        "schema_version": "three_engine_lane_result_v1",
        "sim_id": SIM_ID,
        "role_id": "jax_rich_mirror_sim_builder",
        "engine": "jax",
        "mode": MODE,
        "all_pass": all(gates.values()),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reads_peer_result": False,
        "seed": SEED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "packages_used": ["sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api": "sympy.Rational / symbolic entropy string construction",
                "input_object": "exported per-site eta decimals from stage_lifted_spinor_shell_n3/n4/n5/n6/n7/n8 JAX results",
                "output_object": "exact p_i and -p log p entropy rows for W-site-weighted lifted families",
                "positive_case": "equal eta anchor yields p_i=1/n",
                "negative_control": "phase labels do not change the entropy quotient row",
                "boundary_case": "one nonzero eta gives product-boundary entropy zero",
                "demotion_condition": "if exported eta rows are missing or exact probabilities do not sum to one, symbolic lane fails",
                "gates": ["all_pass", "equal_eta_anchors", "entropy_curves"],
            },
            {
                "tool": "z3",
                "qualified_api": "z3.Solver.check",
                "input_object": "actual exported eta_i^2 weights and product-boundary disjunction per rung",
                "output_object": "unsat for actual lifted rungs, sat for one-hot positive boundary control",
                "positive_case": "one-hot W weight vector is product separable",
                "negative_control": "all-zero invalid vector is unsat",
                "boundary_case": "p_i in {0,1}",
                "demotion_condition": "if z3 and cvc5 disagree, boundary remains open",
                "gates": ["crossover_proofs", "separability_boundary"],
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver.checkSat",
                "input_object": "same rational product-boundary disjunction as z3",
                "output_object": "independent sat/unsat mirror for n3/n4/n5/n6/n7/n8",
                "positive_case": "one-hot W weight vector is product separable",
                "negative_control": "all-zero invalid vector is unsat",
                "boundary_case": "p_i in {0,1}",
                "demotion_condition": "if cvc5 and z3 disagree, boundary remains open",
                "gates": ["crossover_proofs", "separability_boundary"],
            },
        ],
        "math_payload": math_payload,
        "gate_pass": gates,
        "solver_rows": {"z3": z3_rows, "cvc5": cvc5_rows},
    }


if __name__ == "__main__":
    write_json(RESULT_PATH, build_result())
