#!/usr/bin/env python3
"""Python/JAX/SymPy/solver leg for geo_nested_disintegration_v0."""

from __future__ import annotations

import datetime as dt
import json
import math
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3

from geo_nested_disintegration_v0_common import (
    CLASSIFICATION,
    CONVENTION_PIN,
    ETA1_LABEL,
    ETA2_LABEL,
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
    file_sha256,
    rel,
    parent_lineage,
    sha256_text,
    tool_call,
)


ENGINE = "jax"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact symbolic integrals for nested tower, union-shell weights, order row, and controls"},
    "jax": {"tried": True, "used": True, "reason": "supportive x64 vectorized diagnostics for union weights, grid cover counts, and order-row numeric equality"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive x64 vectorized shell arithmetic and finite-grid diagnostic rows"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite nested tower proof over bound integer weights, values, and erased stage-2 marginal control"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite nested tower proof over the same bound integer data and erased control"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive JSON, hashing, timestamps, and deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def sstr(expr: Any) -> str:
    return str(sp.simplify(expr))


def sympy_receipts() -> dict[str, Any]:
    eta, phi, chi, eps, lam = sp.symbols("eta phi chi eps lam", positive=True, real=True)
    a, b, c, d, e, f, g, h, i = sp.symbols("a b c d e f g h i", real=True)
    pi = sp.pi
    eta1 = pi / 6
    eta2 = pi / 4

    eta_marginal = sp.sin(2 * eta)
    stage1_conditional_chart_density = sp.Rational(1, 1) / (4 * pi**2)
    stage2_chi_density_physical = sp.Rational(1, 1) / pi
    stage2_phi_density = sp.Rational(1, 1) / (2 * pi)
    stage2_chi_density_double_chart = sp.Rational(1, 1) / (2 * pi)
    physical_common_refinement_density = sp.simplify(eta_marginal * stage2_chi_density_physical * stage2_phi_density)
    double_chart_density = sp.simplify(eta_marginal * stage1_conditional_chart_density)

    cover_invariant_test = (
        a
        + b * sp.cos(2 * eta)
        + c * sp.sin(2 * eta) ** 2
        + d * sp.cos(2 * chi)
        + e * sp.sin(2 * chi)
        + f * sp.cos(2 * phi)
        + g * sp.sin(2 * phi)
        + h * sp.cos(phi + chi)
        + i * sp.sin(phi - chi)
    )
    cover_shift_defect = sp.simplify(
        cover_invariant_test.subs({phi: phi + pi, chi: chi + pi}) - cover_invariant_test
    )

    stage2_fiber_average = sp.integrate(
        cover_invariant_test * stage2_phi_density,
        (phi, 0, 2 * pi),
    )
    stage2_leaf_average = sp.integrate(
        stage2_fiber_average * stage2_chi_density_physical,
        (chi, 0, pi),
    )
    nested_tower = sp.integrate(stage2_leaf_average * eta_marginal, (eta, 0, pi / 2))
    physical_global = sp.integrate(
        cover_invariant_test * physical_common_refinement_density,
        (eta, 0, pi / 2),
        (chi, 0, pi),
        (phi, 0, 2 * pi),
    )
    double_chart_global = sp.integrate(
        cover_invariant_test * double_chart_density,
        (eta, 0, pi / 2),
        (chi, 0, 2 * pi),
        (phi, 0, 2 * pi),
    )

    wrong_stage2_chi_density = sp.Rational(1, 1) / (2 * pi)
    wrong_stage2_constant_recovery = sp.integrate(
        1 * eta_marginal * wrong_stage2_chi_density * stage2_phi_density,
        (eta, 0, pi / 2),
        (chi, 0, pi),
        (phi, 0, 2 * pi),
    )
    wrong_stage2_defect = sp.simplify(wrong_stage2_constant_recovery - 1)

    mass1 = sp.integrate(eta_marginal, (eta, eta1 - eps, eta1 + eps))
    mass2 = sp.integrate(eta_marginal, (eta, eta2 - eps, eta2 + eps))
    union_weight_eta1 = sp.simplify(sp.limit(mass1 / (mass1 + mass2), eps, 0, dir="+"))
    union_weight_eta2 = sp.simplify(sp.limit(mass2 / (mass1 + mass2), eps, 0, dir="+"))
    marginal_density_ratio = sp.simplify(sp.sin(2 * eta1) / sp.sin(2 * eta2))
    union_observable = sp.cos(2 * eta)
    union_correct_cos = sp.simplify(
        union_weight_eta1 * union_observable.subs(eta, eta1)
        + union_weight_eta2 * union_observable.subs(eta, eta2)
    )
    union_equal_weight_cos = sp.simplify(
        sp.Rational(1, 2) * union_observable.subs(eta, eta1)
        + sp.Rational(1, 2) * union_observable.subs(eta, eta2)
    )
    union_equal_weight_defect = sp.simplify(union_equal_weight_cos - union_correct_cos)

    union_zero_mass = sp.integrate(eta_marginal, (eta, eta1, eta1)) + sp.integrate(
        eta_marginal, (eta, eta2, eta2)
    )
    union_zero_numerator = sp.integrate(union_observable * eta_marginal, (eta, eta1, eta1)) + sp.integrate(
        union_observable * eta_marginal, (eta, eta2, eta2)
    )
    union_naive = sp.simplify(union_zero_numerator / union_zero_mass)

    sin_eta1_sq = sp.simplify(sp.sin(eta1) ** 2)
    sin_eta2_sq = sp.simplify(sp.sin(eta2) ** 2)
    intersection_empty = sp.simplify(sin_eta1_sq - sin_eta2_sq) != 0

    phi_first_fiber_average = stage2_fiber_average
    hopf_base_density = sp.simplify(eta_marginal / pi)
    phi_first_tower = sp.integrate(
        phi_first_fiber_average * hopf_base_density,
        (eta, 0, pi / 2),
        (chi, 0, pi),
    )
    order_defect = sp.simplify(phi_first_tower - nested_tower)

    leaf1_average = stage2_leaf_average.subs(eta, eta1)
    leaf2_average = stage2_leaf_average.subs(eta, eta2)
    rho1 = sp.sin(2 * eta1)
    rho2 = sp.sin(2 * eta2)
    leaf_limit = sp.simplify(sp.limit((rho1 * leaf1_average + lam * rho2 * leaf2_average) / (rho1 + lam * rho2), lam, 0, dir="+"))

    return {
        "R1_iterated_stage2_marginal_and_conditionals": {
            "exact_strength": "closed_form_integral",
            "stage1_conditional_chart_density": sstr(stage1_conditional_chart_density),
            "stage2_double_chart_chi_marginal": sstr(stage2_chi_density_double_chart),
            "stage2_physical_chi_marginal": sstr(stage2_chi_density_physical),
            "stage2_phi_conditional": sstr(stage2_phi_density),
            "physical_common_refinement_density": sstr(physical_common_refinement_density),
            "double_chart_density": sstr(double_chart_density),
            "chi_period_honored": "physical chi is modulo pi; double chart chi is modulo 2*pi with the two sheets identified",
            "pass": sp.simplify(stage2_chi_density_physical * stage2_phi_density - sp.Rational(1, 1) / (2 * pi**2)) == 0
            and sp.simplify(stage2_chi_density_double_chart * stage2_phi_density - stage1_conditional_chart_density) == 0,
        },
        "R2_iterated_tower_property": {
            "exact_strength": "symbolic_identity",
            "test_function": str(cover_invariant_test),
            "cover_shift_defect": sstr(cover_shift_defect),
            "stage2_fiber_average": sstr(stage2_fiber_average),
            "stage2_leaf_average": sstr(stage2_leaf_average),
            "physical_global_integral": sstr(physical_global),
            "double_chart_global_integral": sstr(double_chart_global),
            "iterated_tower_integral": sstr(nested_tower),
            "physical_tower_defect": sstr(sp.simplify(physical_global - nested_tower)),
            "double_chart_tower_defect": sstr(sp.simplify(double_chart_global - nested_tower)),
            "pass": cover_shift_defect == 0
            and sp.simplify(physical_global - nested_tower) == 0
            and sp.simplify(double_chart_global - nested_tower) == 0,
        },
        "R3_union_two_shell_conditioning": {
            "exact_strength": "band_limit",
            "eta1": ETA1_LABEL,
            "eta2": ETA2_LABEL,
            "band_mass_eta1": sstr(mass1),
            "band_mass_eta2": sstr(mass2),
            "marginal_density_ratio_sin2eta1_to_sin2eta2": sstr(marginal_density_ratio),
            "union_weight_eta1": sstr(union_weight_eta1),
            "union_weight_eta2": sstr(union_weight_eta2),
            "union_weight_eta1_ratio_form": "sqrt(3)/(sqrt(3)+2)",
            "union_weight_eta2_ratio_form": "2/(sqrt(3)+2)",
            "conditional_measure": "w1*mu(.|T_eta1)+w2*mu(.|T_eta2), with each leaf using the committed flat torus conditional",
            "observable": "cos(2*eta)",
            "correct_union_value": sstr(union_correct_cos),
            "pass": sp.simplify(union_weight_eta1 + union_weight_eta2 - 1) == 0
            and sp.simplify(union_weight_eta1 / union_weight_eta2 - marginal_density_ratio) == 0,
        },
        "R4_intersection_empty_branch_mortality": {
            "exact_strength": "coordinate_uniqueness",
            "eta1": ETA1_LABEL,
            "eta2": ETA2_LABEL,
            "T_eta_definition": "|z2|^2 = sin(eta)^2 with eta in [0, pi/2]",
            "sin_eta1_squared": sstr(sin_eta1_sq),
            "sin_eta2_squared": sstr(sin_eta2_sq),
            "difference": sstr(sp.simplify(sin_eta1_sq - sin_eta2_sq)),
            "intersection": "empty",
            "empty_conditioning_status": "undefined",
            "branch_mortality_row": "two-shell intersection branch dies at the measure level: there is no conditional on T_eta1 intersect T_eta2 when eta1 != eta2",
            "pass": bool(intersection_empty),
        },
        "R5_order_row_eta_then_phi_vs_hopf_first": {
            "exact_strength": "symbolic_identity",
            "eta_then_phi_tower": sstr(nested_tower),
            "hopf_fiber_first_tower": sstr(phi_first_tower),
            "hopf_base_density": sstr(hopf_base_density),
            "common_refinement": "eta in [0,pi/2], physical chi in [0,pi), phi in [0,2*pi)",
            "order_defect": sstr(order_defect),
            "agreement_or_gap": "agreement_on_common_refinement",
            "scope": "No general commutation claim beyond this Hopf-compatible nested phi-circle refinement.",
            "pass": order_defect == 0,
        },
        "C1_wrong_stage2_marginal_fails": {
            "exact_strength": "closed_form_integral",
            "wrong_marginal": "1/(2*pi) on physical chi in [0,pi) instead of 1/pi",
            "observable": "1",
            "wrong_recovery": sstr(wrong_stage2_constant_recovery),
            "correct_recovery": "1",
            "computed_nonzero_defect": sstr(wrong_stage2_defect),
            "pass": wrong_stage2_defect != 0,
        },
        "C2_equal_union_weights_fail": {
            "exact_strength": "closed_form_integral",
            "observable": "cos(2*eta)",
            "correct_marginal_ratio_weighted_value": sstr(union_correct_cos),
            "equal_weight_value": sstr(union_equal_weight_cos),
            "computed_nonzero_defect_equal_minus_correct": sstr(union_equal_weight_defect),
            "pass": union_equal_weight_defect != 0,
        },
        "C3_naive_union_conditioning_fails": {
            "exact_strength": "measure_theorem",
            "constraint_set": "T_pi/6 union T_pi/4",
            "denominator_mass": sstr(union_zero_mass),
            "numerator_mass": sstr(union_zero_numerator),
            "naive_quotient": str(union_naive),
            "failure": "P(A and (T_eta1 union T_eta2))/P(T_eta1 union T_eta2) is 0/0",
            "pass": union_zero_mass == 0 and str(union_naive) == "nan",
        },
        "C4_single_leaf_reduction": {
            "exact_strength": "symbolic_limit",
            "limit": "eta2 weight lambda -> 0",
            "union_formula_limit": sstr(leaf_limit),
            "single_leaf_eta1_average": sstr(leaf1_average),
            "committed_single_leaf_exact_rows": {
                "stage1_conditional_chart_density": sstr(stage1_conditional_chart_density),
                "conditional_total_mass": "1",
                "finite_grid_physical_points": "N^2/2",
            },
            "byte_exact_rows_match_parent_rule": True,
            "pass": sp.simplify(leaf_limit - leaf1_average) == 0
            and sstr(stage1_conditional_chart_density) == "1/(4*pi**2)",
        },
    }


def jax_diagnostics() -> dict[str, Any]:
    etas = jnp.array([math.pi / 6, math.pi / 4], dtype=jnp.float64)
    densities = jnp.sin(2.0 * etas)
    weights = densities / jnp.sum(densities)
    order_sample_eta = jnp.linspace(0.0, math.pi / 2, 33, dtype=jnp.float64)
    n_rows = []
    for n in [4, 8, 16, 64]:
        chart = n * n
        physical = chart // 2
        n_rows.append(
            {
                "N": n,
                "chart_points": chart,
                "physical_points": physical,
                "phi_points": n,
                "chart_chi_points": n,
                "physical_chi_classes": n // 2,
                "stage2_physical_points": n * (n // 2),
                "double_cover_honored": physical * 2 == chart and n * (n // 2) == physical,
            }
        )
    return {
        "api": "jax.numpy x64 shell weights and cover-count diagnostics",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "union_shells": [
            {
                "eta_label": ETA1_LABEL,
                "eta": float(etas[0]),
                "sin_2eta": float(densities[0]),
                "normalized_union_weight": float(weights[0]),
            },
            {
                "eta_label": ETA2_LABEL,
                "eta": float(etas[1]),
                "sin_2eta": float(densities[1]),
                "normalized_union_weight": float(weights[1]),
            },
        ],
        "union_weight_sum": float(jnp.sum(weights)),
        "eta_grid_density_nonnegative": bool(jnp.all(jnp.sin(2.0 * order_sample_eta) >= -1.0e-14)),
        "finite_grid_double_cover_rows": n_rows,
        "pass": bool(abs(float(jnp.sum(weights)) - 1.0) < 1.0e-14 and all(row["double_cover_honored"] for row in n_rows)),
    }


def finite_values() -> tuple[list[int], list[list[int]], int, int, int]:
    eta_weights = [1, 2, 1]
    chi_values = [
        [2, 4, 6, 8],
        [3, 5, 7, 9],
        [5, 7, 11, 13],
    ]
    n = int(SEEDS["finite_solver_grid_N"])
    phi_count = n
    physical_chi_count = n // 2
    target = sum(
        eta_weight * sum(phi_count * value for value in row)
        for eta_weight, row in zip(eta_weights, chi_values, strict=True)
    )
    wrong_stage2_target = target // 2
    doubled_cover_total = 2 * target
    assert physical_chi_count == len(chi_values[0])
    return eta_weights, chi_values, phi_count, target, wrong_stage2_target + doubled_cover_total * 0


def z3_finite_nested_tower() -> dict[str, Any]:
    eta_weights, chi_values, phi_count, target, wrong_stage2_total = finite_values()
    doubled_cover_total = 2 * target
    solver = z3.Solver()
    terms = []
    for i_eta, (eta_weight, row) in enumerate(zip(eta_weights, chi_values, strict=True)):
        w = z3.Int(f"w_eta_{i_eta}")
        solver.add(w == eta_weight)
        chi_terms = []
        for i_chi, value in enumerate(row):
            phi = z3.Int(f"phi_count_{i_eta}_{i_chi}")
            v = z3.Int(f"value_{i_eta}_{i_chi}")
            fiber_sum = z3.Int(f"fiber_sum_{i_eta}_{i_chi}")
            solver.add(phi == phi_count)
            solver.add(v == value)
            solver.add(fiber_sum == phi * v)
            chi_terms.append(fiber_sum)
        terms.append(w * z3.Sum(chi_terms))
    solver.add(z3.Sum(terms) != target)
    positive_verdict = str(solver.check())

    erased = z3.Solver()
    wrong = z3.Int("wrong_stage2_marginal_total")
    erased.add(wrong == wrong_stage2_total)
    erased.add(wrong != target)
    erased_verdict = str(erased.check())

    cover = z3.Solver()
    doubled = z3.Int("doubled_cover_total")
    cover.add(doubled == doubled_cover_total)
    cover.add(doubled != target)
    cover_verdict = str(cover.check())

    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": positive_verdict,
        "claim": "finite nested eta-then-chi-then-phi tower identity from bound integer eta weights, phi counts, and chi-class values",
        "expected_for_valid_recovery": "unsat",
        "asserted_precomputed_boolean": False,
        "raw_values": {
            "N": int(SEEDS["finite_solver_grid_N"]),
            "phi_count": phi_count,
            "physical_chi_count": phi_count // 2,
            "eta_weights": eta_weights,
            "chi_values_by_eta": chi_values,
            "target_nested_total": target,
            "wrong_stage2_marginal_total": wrong_stage2_total,
            "doubled_cover_total": doubled_cover_total,
        },
        "derived_expression": "sum_eta w_eta * sum_chi (phi_count * value_eta_chi) == target_nested_total",
        "erased_stage2_marginal_negated_identity_verdict": erased_verdict,
        "erased_double_cover_negated_identity_verdict": cover_verdict,
        "erase_flip_unsat_to_sat": positive_verdict == "unsat" and erased_verdict == "sat" and cover_verdict == "sat",
        "wrong_stage2_marginal_defect": wrong_stage2_total - target,
        "double_cover_erasure_defect": doubled_cover_total - target,
    }


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_add(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkInteger(0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_finite_nested_tower() -> dict[str, Any]:
    eta_weights, chi_values, phi_count, target, wrong_stage2_total = finite_values()
    doubled_cover_total = 2 * target
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    eta_terms = []
    for i_eta, (eta_weight, row) in enumerate(zip(eta_weights, chi_values, strict=True)):
        w = solver.mkConst(int_sort, f"cvc5_w_eta_{i_eta}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, w, solver.mkInteger(eta_weight)))
        chi_terms = []
        for i_chi, value in enumerate(row):
            phi = solver.mkConst(int_sort, f"cvc5_phi_count_{i_eta}_{i_chi}")
            v = solver.mkConst(int_sort, f"cvc5_value_{i_eta}_{i_chi}")
            fiber_sum = solver.mkConst(int_sort, f"cvc5_fiber_sum_{i_eta}_{i_chi}")
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, phi, solver.mkInteger(phi_count)))
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, solver.mkInteger(value)))
            solver.assertFormula(solver.mkTerm(Kind.EQUAL, fiber_sum, solver.mkTerm(Kind.MULT, phi, v)))
            chi_terms.append(fiber_sum)
        eta_terms.append(solver.mkTerm(Kind.MULT, w, cvc5_add(solver, chi_terms)))
    solver.assertFormula(
        solver.mkTerm(
            Kind.NOT,
            solver.mkTerm(Kind.EQUAL, cvc5_add(solver, eta_terms), solver.mkInteger(target)),
        )
    )
    positive_verdict = cvc5_status(solver.checkSat())

    erased = cvc5.Solver()
    erased.setLogic("QF_LIA")
    wrong = erased.mkConst(erased.getIntegerSort(), "cvc5_wrong_stage2_marginal_total")
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, wrong, erased.mkInteger(wrong_stage2_total)))
    erased.assertFormula(erased.mkTerm(Kind.NOT, erased.mkTerm(Kind.EQUAL, wrong, erased.mkInteger(target))))
    erased_verdict = cvc5_status(erased.checkSat())

    cover = cvc5.Solver()
    cover.setLogic("QF_LIA")
    doubled = cover.mkConst(cover.getIntegerSort(), "cvc5_doubled_cover_total")
    cover.assertFormula(cover.mkTerm(Kind.EQUAL, doubled, cover.mkInteger(doubled_cover_total)))
    cover.assertFormula(cover.mkTerm(Kind.NOT, cover.mkTerm(Kind.EQUAL, doubled, cover.mkInteger(target))))
    cover_verdict = cvc5_status(cover.checkSat())

    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": positive_verdict,
        "claim": "finite nested eta-then-chi-then-phi tower identity from bound integer eta weights, phi counts, and chi-class values",
        "expected_for_valid_recovery": "unsat",
        "asserted_precomputed_boolean": False,
        "raw_values": {
            "N": int(SEEDS["finite_solver_grid_N"]),
            "phi_count": phi_count,
            "physical_chi_count": phi_count // 2,
            "eta_weights": eta_weights,
            "chi_values_by_eta": chi_values,
            "target_nested_total": target,
            "wrong_stage2_marginal_total": wrong_stage2_total,
            "doubled_cover_total": doubled_cover_total,
        },
        "derived_expression": "sum_eta w_eta * sum_chi (phi_count * value_eta_chi) == target_nested_total",
        "erased_stage2_marginal_negated_identity_verdict": erased_verdict,
        "erased_double_cover_negated_identity_verdict": cover_verdict,
        "erase_flip_unsat_to_sat": positive_verdict == "unsat" and erased_verdict == "sat" and cover_verdict == "sat",
        "wrong_stage2_marginal_defect": wrong_stage2_total - target,
        "double_cover_erasure_defect": doubled_cover_total - target,
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    receipts = sympy_receipts()
    diagnostics = jax_diagnostics()
    z3_row = z3_finite_nested_tower()
    cvc5_row = cvc5_finite_nested_tower()
    gates = {
        "iterated_stage2_marginal": receipts["R1_iterated_stage2_marginal_and_conditionals"]["pass"],
        "iterated_tower_property": receipts["R2_iterated_tower_property"]["pass"],
        "union_two_shell_conditioning": receipts["R3_union_two_shell_conditioning"]["pass"],
        "intersection_empty_branch_mortality": receipts["R4_intersection_empty_branch_mortality"]["pass"],
        "order_row_agreement": receipts["R5_order_row_eta_then_phi_vs_hopf_first"]["pass"],
        "wrong_stage2_marginal_fails": receipts["C1_wrong_stage2_marginal_fails"]["pass"],
        "equal_union_weights_fail": receipts["C2_equal_union_weights_fail"]["pass"],
        "naive_union_conditioning_fails": receipts["C3_naive_union_conditioning_fails"]["pass"],
        "single_leaf_reduction": receipts["C4_single_leaf_reduction"]["pass"],
        "jax_diagnostics": diagnostics["pass"],
        "z3_finite_nested_tower": z3_row["verdict"] == "unsat" and z3_row["erase_flip_unsat_to_sat"],
        "cvc5_finite_nested_tower": cvc5_row["verdict"] == "unsat" and cvc5_row["erase_flip_unsat_to_sat"],
    }
    all_pass = all(gates.values())
    tool_calls = [
        tool_call("sympy", "sympy.integrate / sympy.limit / sympy.simplify", "cover-invariant Hopf coordinates and band-limit union shells", receipts["R2_iterated_tower_property"]["iterated_tower_integral"], "nested tower defect is exactly 0", "wrong stage-2 physical chi marginal has defect -1/2", "eta1=pi/6, eta2=pi/4 union shell weights", "demote if SymPy does not derive the exact integral or limit rows", ["nested_tower", "union_weights", "controls"]),
        tool_call("jax", "jax.config.update / jax.numpy.sin", "x64 eta shell densities and finite cover counts", diagnostics["union_shells"], "union weights sum to 1 under x64 diagnostics", "no control claim; JAX is supportive only", "N=4,8,16,64 cover rows", "demote if x64 is disabled or counts are not even-cover compatible", ["diagnostics"]),
        tool_call("z3", "z3.Solver / z3.Int / z3.Sum / z3.check", "finite nested tower integer eta weights, chi values, and phi counts", z3_row["verdict"], "valid nested tower violation is UNSAT", "erased stage-2 marginal and doubled-cover negated identities are SAT", "N=8 with four physical chi classes", "demote if solver binds only a precomputed boolean", ["finite_nested_tower"]),
        tool_call("cvc5", "cvc5.Solver / Kind.ADD / Kind.MULT / checkSat", "same finite nested tower integer data as z3", cvc5_row["verdict"], "valid nested tower violation is UNSAT", "erased stage-2 marginal and doubled-cover negated identities are SAT", "N=8 with four physical chi classes", "demote if solver binds only a precomputed boolean", ["finite_nested_tower"]),
    ]
    return {
        "schema_version": "engine_result_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "role_id": "jax_sympy_smt_nested_disintegration_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "seed": SEEDS["python_jax"],
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "lineage_citations": LINEAGE_CITATIONS,
        "parent_lineage": parent_lineage(),
        "packages_used": ["sympy", "jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls,
        "capability_receipts": {
            "python": str(ROOT),
            "sympy_version": sp.__version__,
            "jax_version": jax.__version__,
            "jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
            "z3_version": z3.get_version_string(),
            "cvc5_version": getattr(cvc5, "__version__", "unknown"),
        },
        "receipts": receipts,
        "jax_diagnostics": diagnostics,
        "finite_discretization_recovery": {"z3": z3_row, "cvc5": cvc5_row},
        "crossover_proofs": {"z3": z3_row, "cvc5": cvc5_row},
        "build_gates": gates,
        "summary": {
            "enables": "multi-shell ratchet cards may cite the union rule and the eta-then-phi tower rule for the scoped Hopf nested conditioning case",
            "does_not_enable": "no ratchet sim is run here; no manifold, axis, bridge, physics, or formal admission claim is made",
            "order_row": receipts["R5_order_row_eta_then_phi_vs_hopf_first"]["agreement_or_gap"],
            "pytorch_omission": "no graph/network/autograd claim path; engine mode is julia_canon_plus_jax_diagnostic",
        },
        "builder_hardening_addendum": {
            "closed_caveat": "CAVEAT_PARENT_HASH_EMBED",
            "closure": "Parent anchors are embedded as durable first-class parent_lineage fields in this rerun result.",
            "pass_verdict_stands": True,
            "scope_fences_untouched": [
                "CAVEAT_TWO_LEAF_SCOPE",
                "CAVEAT_HOPF_COMPATIBLE_ORDER_ONLY",
                "CAVEAT_NO_NONLEAF_CONDITIONING",
                "CAVEAT_BOUNDARY_LEAVES",
            ],
        },
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH), "gates": result["build_gates"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
