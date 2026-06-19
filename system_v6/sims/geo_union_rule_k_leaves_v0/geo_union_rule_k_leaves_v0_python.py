#!/usr/bin/env python3
"""Python SymPy/z3/cvc5 leg for geo_union_rule_k_leaves_v0."""

from __future__ import annotations

import datetime as dt
import json
import math
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3

from geo_union_rule_k_leaves_v0_common import (
    CLASSIFICATION,
    CONVENTION_PIN,
    FORMAL_ADMISSION_ALLOWED,
    LINEAGE_CITATIONS,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    READS_PEER_RESULT,
    RESULT_DIR,
    ROOT,
    SEEDS,
    SIM_DIR,
    SIM_ID,
    committed_parent_r3_row,
    file_sha256,
    parent_lineage,
    rel,
    sha256_text,
    stable_json_sha256,
    tool_call,
)


ENGINE = "python_sympy_smt"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_python.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_python_results.json"

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact band-limit derivation, k=2 parent row reproduction, k=3/k=4 weights, associativity, degenerate/boundary controls, and continuum mortality boundary integrals",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing real-arithmetic proof of the k=3 radical weight identity with erased-weight and equal-weight controls",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent real-arithmetic proof of the same k=3 radical weight identity and erased flip",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic JSON, hashing, timestamps, and Riemann diagnostic serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def sstr(expr: Any) -> str:
    return str(sp.radsimp(sp.simplify(expr)))


def ratio_sstr(expr: Any) -> str:
    return str(sp.simplify(expr))


def weight_rows(labels: list[str], etas: list[sp.Expr]) -> list[dict[str, str]]:
    densities = [sp.sin(2 * eta) for eta in etas]
    total = sp.simplify(sum(densities))
    return [
        {
            "eta": label,
            "rho_sin_2eta": sstr(density),
            "weight": sstr(density / total),
            "weight_ratio_form": ratio_sstr(density / total),
        }
        for label, density in zip(labels, densities, strict=True)
    ]


def weighted_value(weights: list[sp.Expr], values: list[sp.Expr]) -> sp.Expr:
    return sp.simplify(sum(w * v for w, v in zip(weights, values, strict=True)))


def k2_parent_reduction_row() -> dict[str, Any]:
    eps = sp.symbols("eps", positive=True, real=True)
    eta = sp.symbols("eta", positive=True, real=True)
    eta1 = sp.pi / 6
    eta2 = sp.pi / 4
    eta_marginal = sp.sin(2 * eta)
    mass1 = sp.integrate(eta_marginal, (eta, eta1 - eps, eta1 + eps))
    mass2 = sp.integrate(eta_marginal, (eta, eta2 - eps, eta2 + eps))
    union_weight_eta1 = sp.simplify(sp.limit(mass1 / (mass1 + mass2), eps, 0, dir="+"))
    union_weight_eta2 = sp.simplify(sp.limit(mass2 / (mass1 + mass2), eps, 0, dir="+"))
    observable = sp.cos(2 * eta)
    correct_union_value = sp.simplify(
        union_weight_eta1 * observable.subs(eta, eta1)
        + union_weight_eta2 * observable.subs(eta, eta2)
    )
    return {
        "band_mass_eta1": sstr(mass1),
        "band_mass_eta2": sstr(mass2),
        "conditional_measure": "w1*mu(.|T_eta1)+w2*mu(.|T_eta2), with each leaf using the committed flat torus conditional",
        "correct_union_value": sstr(correct_union_value),
        "eta1": "pi/6",
        "eta2": "pi/4",
        "exact_strength": "band_limit",
        "marginal_density_ratio_sin2eta1_to_sin2eta2": sstr(sp.sin(2 * eta1) / sp.sin(2 * eta2)),
        "observable": "cos(2*eta)",
        "pass": True,
        "union_weight_eta1": sstr(union_weight_eta1),
        "union_weight_eta1_ratio_form": "sqrt(3)/(sqrt(3)+2)",
        "union_weight_eta2": sstr(union_weight_eta2),
        "union_weight_eta2_ratio_form": "2/(sqrt(3)+2)",
    }


def riemann_midpoint_rows() -> list[dict[str, Any]]:
    rows = []
    for n in SEEDS["riemann_midpoint_N"]:
        midpoints = [(i + 0.5) * (math.pi / 2.0) / n for i in range(n)]
        densities = [math.sin(2.0 * eta) for eta in midpoints]
        total = sum(densities)
        weights = [density / total for density in densities]
        cos_avg = sum(w * math.cos(2.0 * eta) for w, eta in zip(weights, midpoints, strict=True))
        cos2_avg = sum(w * math.cos(2.0 * eta) ** 2 for w, eta in zip(weights, midpoints, strict=True))
        rows.append(
            {
                "N": n,
                "finite_leaf_union_measure": "0",
                "midpoint_weight_sum": sum(weights),
                "cos_2eta_midpoint_value": cos_avg,
                "cos2_2eta_midpoint_value": cos2_avg,
                "cos_2eta_target": 0.0,
                "cos2_2eta_target": 1.0 / 3.0,
                "cos_2eta_abs_error": abs(cos_avg),
                "cos2_2eta_abs_error": abs(cos2_avg - 1.0 / 3.0),
            }
        )
    return rows


def sympy_receipts() -> dict[str, Any]:
    eta, eps = sp.symbols("eta eps", positive=True, real=True)
    rho1, rho2, rho3 = sp.symbols("rho1 rho2 rho3", positive=True, real=True)
    pi = sp.pi
    shells4 = [pi / 12, pi / 6, pi / 4, pi / 3]
    labels4 = ["pi/12", "pi/6", "pi/4", "pi/3"]
    shells3 = shells4[:3]
    labels3 = labels4[:3]

    generic_band_mass = sp.integrate(sp.sin(2 * eta), (eta, eta - eps, eta + eps))
    generic_band_mass = sp.simplify(generic_band_mass)
    rhos = [rho1, rho2, rho3]
    weights = [rho / sum(rhos) for rho in rhos]
    normalization_defect = sp.simplify(sum(weights) - 1)
    recovery_constant_defect = sp.simplify(weighted_value(weights, [1, 1, 1]) - 1)

    group12 = sp.simplify((rho1 + rho2) / (rho1 + rho2 + rho3))
    group23 = sp.simplify((rho2 + rho3) / (rho1 + rho2 + rho3))
    left_weights = [
        sp.simplify(group12 * rho1 / (rho1 + rho2)),
        sp.simplify(group12 * rho2 / (rho1 + rho2)),
        sp.simplify(rho3 / (rho1 + rho2 + rho3)),
    ]
    right_weights = [
        sp.simplify(rho1 / (rho1 + rho2 + rho3)),
        sp.simplify(group23 * rho2 / (rho2 + rho3)),
        sp.simplify(group23 * rho3 / (rho2 + rho3)),
    ]
    assoc_left_defects = [sp.simplify(left_weights[i] - weights[i]) for i in range(3)]
    assoc_right_defects = [sp.simplify(right_weights[i] - weights[i]) for i in range(3)]

    k2_row = k2_parent_reduction_row()
    parent_row = committed_parent_r3_row()

    densities3 = [sp.sin(2 * eta_i) for eta_i in shells3]
    weights3 = [sp.simplify(d / sum(densities3)) for d in densities3]
    values3 = [sp.cos(2 * eta_i) for eta_i in shells3]
    direct3_value = weighted_value(weights3, values3)
    left3_weights = [
        sp.simplify((densities3[0] + densities3[1]) / sum(densities3) * densities3[0] / (densities3[0] + densities3[1])),
        sp.simplify((densities3[0] + densities3[1]) / sum(densities3) * densities3[1] / (densities3[0] + densities3[1])),
        sp.simplify(densities3[2] / sum(densities3)),
    ]
    right3_weights = [
        sp.simplify(densities3[0] / sum(densities3)),
        sp.simplify((densities3[1] + densities3[2]) / sum(densities3) * densities3[1] / (densities3[1] + densities3[2])),
        sp.simplify((densities3[1] + densities3[2]) / sum(densities3) * densities3[2] / (densities3[1] + densities3[2])),
    ]
    left3_value = weighted_value(left3_weights, values3)
    right3_value = weighted_value(right3_weights, values3)

    duplicate_shells = [pi / 6, pi / 6, pi / 4]
    duplicate_densities = [sp.sin(2 * eta_i) for eta_i in duplicate_shells]
    duplicate_naive_weights = [sp.simplify(d / sum(duplicate_densities)) for d in duplicate_densities]
    duplicate_naive_value = weighted_value(duplicate_naive_weights, [sp.cos(2 * eta_i) for eta_i in duplicate_shells])
    collapsed_shells = [pi / 6, pi / 4]
    collapsed_densities = [sp.sin(2 * eta_i) for eta_i in collapsed_shells]
    collapsed_weights = [sp.simplify(d / sum(collapsed_densities)) for d in collapsed_densities]
    collapsed_value = weighted_value(collapsed_weights, [sp.cos(2 * eta_i) for eta_i in collapsed_shells])
    duplicate_defect = sp.simplify(duplicate_naive_value - collapsed_value)

    boundary_shells = [0, pi / 6, pi / 4]
    boundary_densities = [sp.sin(2 * eta_i) for eta_i in boundary_shells]
    boundary_weights = [sp.simplify(d / sum(boundary_densities)) for d in boundary_densities]

    equal_k3_value = sp.simplify(sum(values3) / 3)
    equal_k3_defect = sp.simplify(equal_k3_value - direct3_value)

    all_shell_constant = sp.integrate(sp.sin(2 * eta), (eta, 0, pi / 2))
    all_shell_cos = sp.integrate(sp.cos(2 * eta) * sp.sin(2 * eta), (eta, 0, pi / 2))
    all_shell_cos2 = sp.integrate(sp.cos(2 * eta) ** 2 * sp.sin(2 * eta), (eta, 0, pi / 2))
    all_shell_sin2 = sp.integrate(sp.sin(2 * eta) ** 2 * sp.sin(2 * eta), (eta, 0, pi / 2))

    riemann_rows = riemann_midpoint_rows()
    return {
        "K1_general_k_leaf_band_limit_rule": {
            "exact_strength": "symbolic_band_limit_general_k",
            "band_mass_eta_i": "int_{eta_i-eps}^{eta_i+eps} sin(2*eta) d_eta = sin(2*eta_i)*sin(2*eps)",
            "sympy_generic_centered_band_mass": sstr(generic_band_mass),
            "common_factor_cancellation": "sin(2*eps) cancels across every finite distinct leaf in the union",
            "k_leaf_weight_formula": "w_i = sin(2*eta_i) / sum_j sin(2*eta_j)",
            "normalization_defect_k3_symbolic": sstr(normalization_defect),
            "constant_recovery_defect_k3_symbolic": sstr(recovery_constant_defect),
            "grouping_left_defects_symbolic": [sstr(item) for item in assoc_left_defects],
            "grouping_right_defects_symbolic": [sstr(item) for item in assoc_right_defects],
            "scope": "finite distinct eta leaves; repeated leaves collapse to unique sets before weighting",
            "pass": normalization_defect == 0
            and recovery_constant_defect == 0
            and all(item == 0 for item in assoc_left_defects + assoc_right_defects),
        },
        "K2_parent_two_leaf_byte_exact_reduction": {
            "exact_strength": "parent_row_stable_json_hash_match",
            "parent_path": "system_v6/sims/geo_nested_disintegration_v0/results/geo_nested_disintegration_v0_jax_results.json#/receipts/R3_union_two_shell_conditioning",
            "computed_row": k2_row,
            "parent_row": parent_row,
            "computed_row_sha256": stable_json_sha256(k2_row),
            "parent_row_sha256": stable_json_sha256(parent_row),
            "byte_exact_under_stable_json": k2_row == parent_row,
            "pass": k2_row == parent_row,
        },
        "K3_concrete_k3_k4_committed_shell_weights": {
            "exact_strength": "closed_form_radical_weights",
            "k3_shells": labels3,
            "k3_weights": weight_rows(labels3, shells3),
            "k3_weight_sum_defect": sstr(sum(weights3) - 1),
            "k3_cos_2eta_value": sstr(direct3_value),
            "k4_shells": labels4,
            "k4_weights": weight_rows(labels4, shells4),
            "k4_weight_sum_defect": sstr(
                sum(sp.sin(2 * eta_i) / sum(sp.sin(2 * eta_j) for eta_j in shells4) for eta_i in shells4) - 1
            ),
            "pass": sp.simplify(sum(weights3) - 1) == 0,
        },
        "K4_associativity_order_row_k3": {
            "exact_strength": "symbolic_group_mass_associativity",
            "direct_3_leaf_weights": [sstr(item) for item in weights3],
            "left_route": "((1 union 2) union 3), with group mass rho12=rho1+rho2",
            "left_route_weights": [sstr(item) for item in left3_weights],
            "right_route": "(1 union (2 union 3)), with group mass rho23=rho2+rho3",
            "right_route_weights": [sstr(item) for item in right3_weights],
            "direct_value_cos_2eta": sstr(direct3_value),
            "left_value_cos_2eta": sstr(left3_value),
            "right_value_cos_2eta": sstr(right3_value),
            "left_minus_direct_defects": [sstr(sp.simplify(left3_weights[i] - weights3[i])) for i in range(3)],
            "right_minus_direct_defects": [sstr(sp.simplify(right3_weights[i] - weights3[i])) for i in range(3)],
            "agreement_or_gap": "agreement_when_iterated_union_carries_summed_group_mass",
            "N01_bracketing_measure_level": "no gap found for finite union conditioning; a gap would require erasing group mass or double-counting sets",
            "pass": all(sp.simplify(left3_weights[i] - weights3[i]) == 0 for i in range(3))
            and all(sp.simplify(right3_weights[i] - weights3[i]) == 0 for i in range(3)),
        },
        "K5_degenerate_boundary_and_equal_weight_controls": {
            "exact_strength": "closed_form_controls",
            "repeated_leaf_input": ["pi/6", "pi/6", "pi/4"],
            "repeated_leaf_status": "collapse repeated eta before weighting because the union is a set",
            "collapsed_unique_weights": [
                {"eta": "pi/6", "weight": sstr(collapsed_weights[0])},
                {"eta": "pi/4", "weight": sstr(collapsed_weights[1])},
            ],
            "naive_duplicate_list_weights": [sstr(item) for item in duplicate_naive_weights],
            "duplicate_double_count_cos_2eta_defect": sstr(duplicate_defect),
            "boundary_leaf_input": ["0", "pi/6", "pi/4"],
            "boundary_weights": [
                {"eta": "0", "weight": sstr(boundary_weights[0])},
                {"eta": "pi/6", "weight": sstr(boundary_weights[1])},
                {"eta": "pi/4", "weight": sstr(boundary_weights[2])},
            ],
            "boundary_leaf_exclusion": "eta->0 has rho=sin(0)=0, so its union weight vanishes",
            "equal_weights_control_k3_value": sstr(equal_k3_value),
            "correct_k3_value": sstr(direct3_value),
            "equal_weights_control_defect_equal_minus_correct": sstr(equal_k3_defect),
            "pass": duplicate_defect != 0 and boundary_weights[0] == 0 and equal_k3_defect != 0,
        },
        "K6_mortality_boundary_free_measure": {
            "exact_strength": "measure_boundary_and_symbolic_integral",
            "finite_k_naive_conditioning_denominator": "0 for every finite k because finite union of fixed-eta leaves has S3 measure zero",
            "definable_again_k": "no_finite_k",
            "definable_again_boundary": "continuum_all_eta_in_[0,pi/2]; union of all shells equals S3 a.e.",
            "all_shell_constant_recovery": sstr(all_shell_constant),
            "all_shell_cos_2eta_unconditioned": sstr(all_shell_cos),
            "all_shell_cos2_2eta_unconditioned": sstr(all_shell_cos2),
            "all_shell_sin2_2eta_unconditioned": sstr(all_shell_sin2),
            "riemann_midpoint_diagnostics": riemann_rows,
            "last_riemann_cos2_error": riemann_rows[-1]["cos2_2eta_abs_error"],
            "mode4_to_free_boundary": "the disintegrated finite-k rule converges only as a weighted eta integral, not as naive finite-union conditioning",
            "pass": all_shell_constant == 1 and all_shell_cos == 0 and all_shell_cos2 == sp.Rational(1, 3),
        },
    }


def z3_k3_weight_identity() -> dict[str, Any]:
    r, w1, w2, w3, total = z3.Reals("r w1 w2 w3 total")

    def base_solver() -> z3.Solver:
        solver = z3.Solver()
        solver.add(r * r == 3, r > 0, r < 2, total == 3 + r)
        return solver

    identity = z3.And(
        w1 * total == 1,
        w2 * total == r,
        w3 * total == 2,
        w1 + w2 + w3 == 1,
    )

    positive = base_solver()
    positive.add(w1 == (3 - r) / 6, w2 == (r - 1) / 2, w3 == (3 - r) / 3)
    positive.add(z3.Not(identity))
    positive_verdict = str(positive.check())

    erased = base_solver()
    erased.add(w1 == (3 - r) / 6, w3 == (3 - r) / 3)
    erased.add(z3.Not(identity))
    erased_verdict = str(erased.check())

    equal = base_solver()
    equal.add(w1 == z3.RealVal(1) / 3, w2 == z3.RealVal(1) / 3, w3 == z3.RealVal(1) / 3)
    equal.add(identity)
    equal_verdict = str(equal.check())

    b0, b2, b3, btotal = z3.Reals("b0 b2 b3 btotal")
    boundary = z3.Solver()
    boundary_identity = z3.And(
        b0 * btotal == 0,
        b2 * btotal == r,
        b3 * btotal == 2,
        b0 + b2 + b3 == 1,
    )
    boundary.add(r * r == 3, r > 0, r < 2, btotal == r + 2)
    boundary.add(b0 == 0, b2 == r / (r + 2), b3 == 2 / (r + 2))
    boundary.add(z3.Not(boundary_identity))
    boundary_verdict = str(boundary.check())

    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": positive_verdict,
        "expected_for_valid_identity": "unsat",
        "claim": "k=3 exact weights for pi/12,pi/6,pi/4 satisfy w_i*sum_scaled_density=density_i and sum_i w_i=1 with sqrt(3) represented by r^2=3,r>0",
        "scaled_densities": ["1", "sqrt(3)", "2"],
        "closed_weights": ["(3-sqrt(3))/6", "(sqrt(3)-1)/2", "(3-sqrt(3))/3"],
        "derived_expression": "And(w1*S=1,w2*S=r,w3*S=2,w1+w2+w3=1) under S=3+r,r^2=3,r>0",
        "asserted_precomputed_boolean": False,
        "erased_weight_w2_formula_negated_identity_verdict": erased_verdict,
        "equal_weights_identity_verdict": equal_verdict,
        "boundary_zero_leaf_negated_identity_verdict": boundary_verdict,
        "erase_flip_unsat_to_sat": positive_verdict == "unsat" and erased_verdict == "sat",
        "equal_weights_fail": equal_verdict == "unsat",
        "boundary_pass": boundary_verdict == "unsat",
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_k3_weight_identity() -> dict[str, Any]:
    def real(solver: cvc5.Solver, value: int | str) -> Any:
        return solver.mkReal(str(value))

    def add(solver: cvc5.Solver, *items: Any) -> Any:
        if len(items) == 1:
            return items[0]
        return solver.mkTerm(Kind.ADD, *items)

    def sub(solver: cvc5.Solver, a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.SUB, a, b)

    def mul(solver: cvc5.Solver, *items: Any) -> Any:
        if len(items) == 1:
            return items[0]
        return solver.mkTerm(Kind.MULT, *items)

    def div(solver: cvc5.Solver, a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.DIVISION, a, b)

    def eq(solver: cvc5.Solver, a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.EQUAL, a, b)

    def gt(solver: cvc5.Solver, a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.GT, a, b)

    def lt(solver: cvc5.Solver, a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.LT, a, b)

    def mk_base() -> tuple[cvc5.Solver, dict[str, Any]]:
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()
        vars_ = {name: solver.mkConst(real_sort, name) for name in ["r", "w1", "w2", "w3", "total"]}
        r = vars_["r"]
        solver.assertFormula(eq(solver, mul(solver, r, r), real(solver, 3)))
        solver.assertFormula(gt(solver, r, real(solver, 0)))
        solver.assertFormula(lt(solver, r, real(solver, 2)))
        solver.assertFormula(eq(solver, vars_["total"], add(solver, real(solver, 3), r)))
        return solver, vars_

    def identity(solver: cvc5.Solver, vars_: dict[str, Any]) -> Any:
        r, w1, w2, w3, total = (vars_[name] for name in ["r", "w1", "w2", "w3", "total"])
        return solver.mkTerm(
            Kind.AND,
            eq(solver, mul(solver, w1, total), real(solver, 1)),
            eq(solver, mul(solver, w2, total), r),
            eq(solver, mul(solver, w3, total), real(solver, 2)),
            eq(solver, add(solver, w1, w2, w3), real(solver, 1)),
        )

    positive, v = mk_base()
    r, w1, w2, w3 = (v[name] for name in ["r", "w1", "w2", "w3"])
    positive.assertFormula(eq(positive, w1, div(positive, sub(positive, real(positive, 3), r), real(positive, 6))))
    positive.assertFormula(eq(positive, w2, div(positive, sub(positive, r, real(positive, 1)), real(positive, 2))))
    positive.assertFormula(eq(positive, w3, div(positive, sub(positive, real(positive, 3), r), real(positive, 3))))
    positive.assertFormula(positive.mkTerm(Kind.NOT, identity(positive, v)))
    positive_verdict = cvc5_status(positive.checkSat())

    erased, ev = mk_base()
    er = ev["r"]
    erased.assertFormula(eq(erased, ev["w1"], div(erased, sub(erased, real(erased, 3), er), real(erased, 6))))
    erased.assertFormula(eq(erased, ev["w3"], div(erased, sub(erased, real(erased, 3), er), real(erased, 3))))
    erased.assertFormula(erased.mkTerm(Kind.NOT, identity(erased, ev)))
    erased_verdict = cvc5_status(erased.checkSat())

    equal, qv = mk_base()
    for name in ["w1", "w2", "w3"]:
        equal.assertFormula(eq(equal, qv[name], div(equal, real(equal, 1), real(equal, 3))))
    equal.assertFormula(identity(equal, qv))
    equal_verdict = cvc5_status(equal.checkSat())

    boundary = cvc5.Solver()
    boundary.setLogic("QF_NRA")
    real_sort = boundary.getRealSort()
    bv = {name: boundary.mkConst(real_sort, name) for name in ["r", "b0", "b2", "b3", "btotal"]}
    br = bv["r"]
    boundary.assertFormula(eq(boundary, mul(boundary, br, br), real(boundary, 3)))
    boundary.assertFormula(gt(boundary, br, real(boundary, 0)))
    boundary.assertFormula(lt(boundary, br, real(boundary, 2)))
    boundary.assertFormula(eq(boundary, bv["btotal"], add(boundary, br, real(boundary, 2))))
    boundary.assertFormula(eq(boundary, bv["b0"], real(boundary, 0)))
    boundary.assertFormula(eq(boundary, bv["b2"], div(boundary, br, add(boundary, br, real(boundary, 2)))))
    boundary.assertFormula(eq(boundary, bv["b3"], div(boundary, real(boundary, 2), add(boundary, br, real(boundary, 2)))))
    boundary_identity = boundary.mkTerm(
        Kind.AND,
        eq(boundary, mul(boundary, bv["b0"], bv["btotal"]), real(boundary, 0)),
        eq(boundary, mul(boundary, bv["b2"], bv["btotal"]), br),
        eq(boundary, mul(boundary, bv["b3"], bv["btotal"]), real(boundary, 2)),
        eq(boundary, add(boundary, bv["b0"], bv["b2"], bv["b3"]), real(boundary, 1)),
    )
    boundary.assertFormula(boundary.mkTerm(Kind.NOT, boundary_identity))
    boundary_verdict = cvc5_status(boundary.checkSat())

    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": positive_verdict,
        "expected_for_valid_identity": "unsat",
        "claim": "independent cvc5 mirror of the k=3 radical weight identity with r^2=3,r>0",
        "scaled_densities": ["1", "sqrt(3)", "2"],
        "closed_weights": ["(3-sqrt(3))/6", "(sqrt(3)-1)/2", "(3-sqrt(3))/3"],
        "derived_expression": "And(w1*S=1,w2*S=r,w3*S=2,w1+w2+w3=1) under S=3+r,r^2=3,r>0",
        "asserted_precomputed_boolean": False,
        "erased_weight_w2_formula_negated_identity_verdict": erased_verdict,
        "equal_weights_identity_verdict": equal_verdict,
        "boundary_zero_leaf_negated_identity_verdict": boundary_verdict,
        "erase_flip_unsat_to_sat": positive_verdict == "unsat" and erased_verdict == "sat",
        "equal_weights_fail": equal_verdict == "unsat",
        "boundary_pass": boundary_verdict == "unsat",
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    receipts = sympy_receipts()
    z3_row = z3_k3_weight_identity()
    cvc5_row = cvc5_k3_weight_identity()
    gates = {
        "general_k_leaf_rule": receipts["K1_general_k_leaf_band_limit_rule"]["pass"],
        "k2_parent_byte_exact": receipts["K2_parent_two_leaf_byte_exact_reduction"]["pass"],
        "concrete_k3_k4_weights": receipts["K3_concrete_k3_k4_committed_shell_weights"]["pass"],
        "associativity_order_row": receipts["K4_associativity_order_row_k3"]["pass"],
        "degenerate_boundary_equal_controls": receipts["K5_degenerate_boundary_and_equal_weight_controls"]["pass"],
        "mortality_boundary_free_measure": receipts["K6_mortality_boundary_free_measure"]["pass"],
        "z3_k3_weight_identity": z3_row["verdict"] == "unsat" and z3_row["erase_flip_unsat_to_sat"],
        "cvc5_k3_weight_identity": cvc5_row["verdict"] == "unsat" and cvc5_row["erase_flip_unsat_to_sat"],
        "z3_cvc5_agree": z3_row["verdict"] == cvc5_row["verdict"] == "unsat",
    }
    all_pass = all(gates.values())
    tool_calls = [
        tool_call(
            "sympy",
            "sympy.integrate / sympy.limit / sympy.simplify / sympy.radsimp",
            "finite-k eta band masses, committed shells pi/12,pi/6,pi/4,pi/3, degenerate and continuum boundary rows",
            {
                "k3_weights": receipts["K3_concrete_k3_k4_committed_shell_weights"]["k3_weights"],
                "k2_sha": receipts["K2_parent_two_leaf_byte_exact_reduction"]["computed_row_sha256"],
            },
            "general finite-k weights normalize and k=2 reproduces committed parent row",
            "equal k=3 weights and duplicate-list double-counting produce nonzero defects",
            "eta=0 weight vanishes and continuum all-shell boundary recovers FREE measure",
            "demote if exact rows drift from SymPy derivation or parent k=2 stable JSON hash",
            ["general_k_leaf_rule", "k2_parent_byte_exact", "controls", "mortality_boundary"],
        ),
        tool_call(
            "z3",
            "z3.Solver / z3.Reals / z3.check",
            "k=3 scaled density identity [1,sqrt(3),2] with r^2=3,r>0",
            z3_row["verdict"],
            "negated exact weight identity is UNSAT",
            "erasing the middle weight formula makes the negated identity SAT; equal weights fail",
            "eta=0 boundary weight identity remains UNSAT under negated violation",
            "demote if solver binds a precomputed boolean or erase flip does not occur",
            ["z3_k3_weight_identity"],
        ),
        tool_call(
            "cvc5",
            "cvc5.Solver / Kind.ADD / Kind.MULT / Kind.DIVISION / checkSat",
            "same k=3 real-arithmetic radical identity as z3",
            cvc5_row["verdict"],
            "negated exact weight identity is UNSAT",
            "erasing the middle weight formula makes the negated identity SAT; equal weights fail",
            "eta=0 boundary weight identity remains UNSAT under negated violation",
            "demote if cvc5 disagrees with z3 or lacks erased flip",
            ["cvc5_k3_weight_identity"],
        ),
    ]
    return {
        "schema_version": "engine_result_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "role_id": "python_sympy_z3_cvc5_k_leaf_union_rule_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "seed": SEEDS["python_sympy_smt"],
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "lineage_citations": LINEAGE_CITATIONS,
        "parent_lineage": parent_lineage(),
        "packages_used": ["sympy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls,
        "capability_receipts": {
            "python": ROOT.as_posix(),
            "sympy_version": sp.__version__,
            "z3_version": z3.get_version_string(),
            "cvc5_version": getattr(cvc5, "__version__", "unknown"),
        },
        "receipts": receipts,
        "crossover_proofs": {"z3": z3_row, "cvc5": cvc5_row},
        "build_gates": gates,
        "summary": {
            "enables": "finite multi-shell stacks may cite the finite-k union rule after parent-lineage and k=2 byte-exact checks",
            "does_not_enable": "no manifold, axis, bridge, physics, canonical admission, finite-k FREE replacement, or formal proof claim is made",
            "associativity_order_row": receipts["K4_associativity_order_row_k3"]["agreement_or_gap"],
            "mortality_boundary": receipts["K6_mortality_boundary_free_measure"]["definable_again_boundary"],
            "pytorch_omission": "no graph/network/autograd claim path; engine mode is julia_symbolics_plus_python_sympy_smt_diagnostic",
        },
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH), "gates": result["build_gates"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
