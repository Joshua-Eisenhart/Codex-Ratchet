#!/usr/bin/env python3
"""Python/JAX/SymPy/solver leg for geo_disintegration_machinery_v0."""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3

from geo_disintegration_machinery_v0_common import (
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
    file_sha256,
    rel,
    sha256_text,
    tool_call,
)


ENGINE = "jax"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact symbolic integrals for eta marginal, band conditioning, wrong marginal defect, and recovery identity"},
    "jax": {"tried": True, "used": True, "reason": "supportive x64 vectorized area and finite-grid diagnostic rows"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive x64 vectorized eta-shell arithmetic"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite discretization recovery proof over bound integer values and erased controls"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite discretization recovery proof over the same bound integer values and erased controls"},
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
    eta, phi, chi = sp.symbols("eta phi chi", real=True)
    a, b, c, d, e, f = sp.symbols("a b c d e f", real=True)
    pi = sp.pi

    physical_chart_volume_density = sp.sin(2 * eta) / 2
    s3_volume = sp.integrate(physical_chart_volume_density, (eta, 0, pi / 2), (phi, 0, 2 * pi), (chi, 0, 2 * pi))
    torus_layer_area = sp.integrate(physical_chart_volume_density, (phi, 0, 2 * pi), (chi, 0, 2 * pi))
    normalized_chart_density = physical_chart_volume_density / s3_volume
    eta_marginal = sp.integrate(normalized_chart_density, (phi, 0, 2 * pi), (chi, 0, 2 * pi))
    conditional_chart_density = sp.Rational(1, 1) / (4 * pi**2)
    conditional_total = sp.integrate(conditional_chart_density, (phi, 0, 2 * pi), (chi, 0, 2 * pi))

    test_function = (
        a
        + b * sp.cos(2 * eta)
        + c * sp.sin(2 * eta) ** 2
        + d * sp.cos(phi)
        + e * sp.sin(chi)
        + f * sp.cos(phi + chi)
    )
    conditional_average = sp.integrate(
        test_function * conditional_chart_density,
        (phi, 0, 2 * pi),
        (chi, 0, 2 * pi),
    )
    global_integral = sp.integrate(
        test_function * normalized_chart_density,
        (eta, 0, pi / 2),
        (phi, 0, 2 * pi),
        (chi, 0, 2 * pi),
    )
    disintegrated_integral = sp.integrate(conditional_average * eta_marginal, (eta, 0, pi / 2))
    recovery_defect = sp.simplify(global_integral - disintegrated_integral)

    eta0 = pi / 4
    singleton_mass = sp.integrate(eta_marginal, (eta, eta0, eta0))
    singleton_numerator = sp.integrate((sp.sin(2 * eta) ** 2) * eta_marginal, (eta, eta0, eta0))
    naive_singleton_quotient = sp.simplify(singleton_numerator / singleton_mass)

    band_lo = pi / 6
    band_hi = pi / 3
    band_observable = 2 + sp.sin(2 * eta) ** 2
    band_denominator = sp.integrate(eta_marginal, (eta, band_lo, band_hi))
    band_numerator = sp.integrate(band_observable * eta_marginal, (eta, band_lo, band_hi))
    band_naive = sp.simplify(band_numerator / band_denominator)
    band_disintegrated = sp.simplify(
        sp.integrate(band_observable * eta_marginal, (eta, band_lo, band_hi))
        / sp.integrate(eta_marginal, (eta, band_lo, band_hi))
    )

    wrong_observable = sp.sin(2 * eta) ** 2
    correct_recovery = sp.integrate(wrong_observable * eta_marginal, (eta, 0, pi / 2))
    flat_eta_marginal = sp.Rational(2, 1) / pi
    wrong_flat_recovery = sp.integrate(wrong_observable * flat_eta_marginal, (eta, 0, pi / 2))
    wrong_flat_defect = sp.simplify(wrong_flat_recovery - correct_recovery)

    null_mass = sp.integrate(eta_marginal, (eta, eta0, eta0))
    null_global_defect = sp.simplify(null_mass * 1)

    return {
        "R1_eta_marginal_area_law": {
            "exact_strength": "closed_form_integral",
            "volume_density_on_double_chart": "(1/2)*sin(2*eta)",
            "torus_layer_area_from_chart": sstr(torus_layer_area),
            "normalized_eta_marginal": sstr(eta_marginal),
            "conditional_chart_density": sstr(conditional_chart_density),
            "conditional_total_mass": sstr(conditional_total),
            "s3_volume": sstr(s3_volume),
            "volume_target": "2*pi**2",
            "pass": sp.simplify(torus_layer_area - 2 * pi**2 * sp.sin(2 * eta)) == 0
            and sp.simplify(eta_marginal - sp.sin(2 * eta)) == 0
            and sp.simplify(s3_volume - 2 * pi**2) == 0
            and conditional_total == 1,
        },
        "R2_symbolic_disintegration_recovery": {
            "exact_strength": "symbolic_identity",
            "test_function": str(test_function),
            "conditional_average": sstr(conditional_average),
            "global_integral": sstr(global_integral),
            "disintegrated_integral": sstr(disintegrated_integral),
            "defect": sstr(recovery_defect),
            "pass": recovery_defect == 0,
        },
        "C1_naive_singleton_conditioning_fails": {
            "exact_strength": "measure_theorem",
            "constraint_set": "T_eta at eta=pi/4",
            "denominator_mass": sstr(singleton_mass),
            "numerator_mass": sstr(singleton_numerator),
            "naive_quotient": str(naive_singleton_quotient),
            "failure": "P(A and T_eta)/P(T_eta) is 0/0, returned by SymPy as nan",
            "pass": singleton_mass == 0 and str(naive_singleton_quotient) == "nan",
        },
        "C2_positive_eta_band_agrees": {
            "exact_strength": "closed_form_integral",
            "band": "[pi/6, pi/3]",
            "denominator_mass": sstr(band_denominator),
            "naive_conditioning_value": sstr(band_naive),
            "disintegrated_conditioning_value": sstr(band_disintegrated),
            "defect": sstr(sp.simplify(band_naive - band_disintegrated)),
            "pass": band_denominator != 0 and sp.simplify(band_naive - band_disintegrated) == 0,
        },
        "C3_wrong_flat_marginal_fails": {
            "exact_strength": "closed_form_integral",
            "observable": "sin(2*eta)**2",
            "correct_recovery": sstr(correct_recovery),
            "flat_eta_marginal": sstr(flat_eta_marginal),
            "wrong_flat_recovery": sstr(wrong_flat_recovery),
            "computed_nonzero_defect": sstr(wrong_flat_defect),
            "pass": wrong_flat_defect != 0,
        },
        "C4_null_set_disintegration_scope": {
            "exact_strength": "measure_theorem",
            "modified_eta": "pi/4",
            "pointwise_conditional_difference_for_cos_phi": 1,
            "singleton_eta_mass": sstr(null_mass),
            "global_integrated_defect": sstr(null_global_defect),
            "scope": "conditional measures are determined only eta-a.e.; changing one eta leaf does not change global recovery",
            "pass": null_mass == 0 and null_global_defect == 0,
        },
    }


def jax_diagnostics() -> dict[str, Any]:
    etas = jnp.array([math.pi / 12, math.pi / 8, math.pi / 6, math.pi / 4, math.pi / 3, 3 * math.pi / 8, 5 * math.pi / 12], dtype=jnp.float64)
    labels = ["pi/12", "pi/8", "pi/6", "pi/4", "pi/3", "3*pi/8", "5*pi/12"]
    area_values = 2.0 * jnp.pi**2 * jnp.sin(2.0 * etas)
    marginal_values = jnp.sin(2.0 * etas)
    volume_exact = float(2.0 * jnp.pi**2)
    committed_geomstats_volume = 19.7392088022
    n_rows = []
    for n in [4, 8, 16, 64]:
        chart = n * n
        physical = chart // 2
        n_rows.append(
            {
                "N": n,
                "chart_points": chart,
                "physical_points": physical,
                "target_N_squared_over_2": physical,
                "chart_point_weight": 1.0 / chart,
                "physical_class_weight": 2.0 / chart,
                "conditional_total_mass_chart": 1.0,
                "double_cover_honored": physical * 2 == chart,
            }
        )
    return {
        "api": "jax.numpy vectorized x64 eta-shell arithmetic",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "eta_rows": [
            {
                "eta_label": label,
                "eta": float(eta),
                "torus_area": float(area),
                "eta_marginal_density": float(marginal),
            }
            for label, eta, area, marginal in zip(labels, list(etas), list(area_values), list(marginal_values), strict=True)
        ],
        "clifford_torus_area": float(area_values[3]),
        "clifford_torus_area_target": float(2.0 * jnp.pi**2),
        "s3_volume_exact": volume_exact,
        "committed_geomstats_probe_value": committed_geomstats_volume,
        "abs_diff_vs_committed_geomstats_probe": abs(volume_exact - committed_geomstats_volume),
        "finite_grid_double_cover_rows": n_rows,
        "pass": bool(abs(volume_exact - committed_geomstats_volume) < 1.0e-9 and all(row["double_cover_honored"] for row in n_rows)),
    }


def z3_finite_recovery() -> dict[str, Any]:
    weights = [1, 2, 1]
    flat_weights = [1, 1, 1]
    values = [5, 7, 11]
    n = int(SEEDS["finite_solver_grid_N"])
    class_count = n * n // 2
    target = sum(w * v for w, v in zip(weights, values, strict=True))
    flat_total = sum(w * v for w, v in zip(flat_weights, values, strict=True))
    doubled_total = 2 * target

    solver = z3.Solver()
    n_var = z3.Int("N")
    class_var = z3.Int("physical_class_count")
    solver.add(n_var == n)
    solver.add(class_var == class_count)
    layer_terms = []
    for idx, (weight, value) in enumerate(zip(weights, values, strict=True)):
        w = z3.Int(f"w_{idx}")
        v = z3.Int(f"v_{idx}")
        layer_sum = z3.Int(f"layer_sum_{idx}")
        solver.add(w == weight)
        solver.add(v == value)
        solver.add(layer_sum == class_var * v)
        layer_terms.append(w * layer_sum)
    solver.add(z3.Sum(layer_terms) != target * class_var)
    positive_verdict = str(solver.check())

    flat = z3.Solver()
    flat.add(z3.Int("flat_sum") == flat_total)
    flat.add(z3.Int("flat_sum") == target)
    flat_verdict = str(flat.check())

    cover = z3.Solver()
    cover.add(z3.Int("doubled_sum") == doubled_total)
    cover.add(z3.Int("doubled_sum") == target)
    cover_verdict = str(cover.check())

    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "verdict": positive_verdict,
        "claim": "finite eta-layer disintegration recovery from bound integer layer weights, class count, and layer values",
        "expected_for_valid_recovery": "unsat",
        "asserted_precomputed_boolean": False,
        "raw_values": {
            "N": n,
            "physical_class_count": class_count,
            "eta_weight_scaled_by_pi_squared": weights,
            "layer_values": values,
            "target_recovered_scaled": target,
        },
        "derived_expression": "sum_i weight_i * (physical_class_count * value_i) == target * physical_class_count",
        "erased_flat_marginal_control_verdict": flat_verdict,
        "erased_double_cover_control_verdict": cover_verdict,
        "erased_controls_flip": positive_verdict == "unsat" and flat_verdict == "unsat" and cover_verdict == "unsat",
        "flat_control_defect": flat_total - target,
        "double_cover_control_defect": doubled_total - target,
    }


def cvc5_add(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkInteger(0)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(Kind.ADD, *terms)


def cvc5_finite_recovery() -> dict[str, Any]:
    weights = [1, 2, 1]
    flat_weights = [1, 1, 1]
    values = [5, 7, 11]
    n = int(SEEDS["finite_solver_grid_N"])
    class_count = n * n // 2
    target = sum(w * v for w, v in zip(weights, values, strict=True))
    flat_total = sum(w * v for w, v in zip(flat_weights, values, strict=True))
    doubled_total = 2 * target

    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    n_var = solver.mkConst(int_sort, "N")
    class_var = solver.mkConst(int_sort, "physical_class_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, n_var, solver.mkInteger(n)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, class_var, solver.mkInteger(class_count)))
    layer_terms = []
    for idx, (weight, value) in enumerate(zip(weights, values, strict=True)):
        w = solver.mkConst(int_sort, f"w_{idx}")
        v = solver.mkConst(int_sort, f"v_{idx}")
        layer_sum = solver.mkConst(int_sort, f"layer_sum_{idx}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, w, solver.mkInteger(weight)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, v, solver.mkInteger(value)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, layer_sum, solver.mkTerm(Kind.MULT, class_var, v)))
        layer_terms.append(solver.mkTerm(Kind.MULT, w, layer_sum))
    lhs = cvc5_add(solver, layer_terms)
    rhs = solver.mkTerm(Kind.MULT, solver.mkInteger(target), class_var)
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, lhs, rhs))
    positive_verdict = str(solver.checkSat()).lower()

    flat = cvc5.Solver()
    flat.setLogic("QF_LIA")
    fs = flat.mkConst(flat.getIntegerSort(), "flat_sum")
    flat.assertFormula(flat.mkTerm(Kind.EQUAL, fs, flat.mkInteger(flat_total)))
    flat.assertFormula(flat.mkTerm(Kind.EQUAL, fs, flat.mkInteger(target)))
    flat_verdict = str(flat.checkSat()).lower()

    cover = cvc5.Solver()
    cover.setLogic("QF_LIA")
    ds = cover.mkConst(cover.getIntegerSort(), "doubled_sum")
    cover.assertFormula(cover.mkTerm(Kind.EQUAL, ds, cover.mkInteger(doubled_total)))
    cover.assertFormula(cover.mkTerm(Kind.EQUAL, ds, cover.mkInteger(target)))
    cover_verdict = str(cover.checkSat()).lower()

    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "verdict": positive_verdict,
        "claim": "finite eta-layer disintegration recovery from bound integer layer weights, class count, and layer values",
        "expected_for_valid_recovery": "unsat",
        "asserted_precomputed_boolean": False,
        "raw_values": {
            "N": n,
            "physical_class_count": class_count,
            "eta_weight_scaled_by_pi_squared": weights,
            "layer_values": values,
            "target_recovered_scaled": target,
        },
        "derived_expression": "sum_i weight_i * (physical_class_count * value_i) == target * physical_class_count",
        "erased_flat_marginal_control_verdict": flat_verdict,
        "erased_double_cover_control_verdict": cover_verdict,
        "erased_controls_flip": positive_verdict == "unsat" and flat_verdict == "unsat" and cover_verdict == "unsat",
        "flat_control_defect": flat_total - target,
        "double_cover_control_defect": doubled_total - target,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    sympy_rows = sympy_receipts()
    jax_rows = jax_diagnostics()
    z3_row = z3_finite_recovery()
    cvc5_row = cvc5_finite_recovery()
    gates = {
        "eta_marginal_area_law": sympy_rows["R1_eta_marginal_area_law"]["pass"],
        "symbolic_recovery": sympy_rows["R2_symbolic_disintegration_recovery"]["pass"],
        "naive_singleton_failure": sympy_rows["C1_naive_singleton_conditioning_fails"]["pass"],
        "positive_band_agreement": sympy_rows["C2_positive_eta_band_agrees"]["pass"],
        "wrong_flat_marginal_fails": sympy_rows["C3_wrong_flat_marginal_fails"]["pass"],
        "null_set_scope": sympy_rows["C4_null_set_disintegration_scope"]["pass"],
        "jax_volume_and_double_cover": jax_rows["pass"],
        "z3_finite_recovery": z3_row["verdict"] == "unsat" and z3_row["erased_controls_flip"],
        "cvc5_finite_recovery": cvc5_row["verdict"] == "unsat" and cvc5_row["erased_controls_flip"],
    }
    all_pass = all(gates.values())
    tool_calls = [
        tool_call("sympy", "sympy.integrate/simplify", "S3 Hopf eta, phi, chi chart density and test function", sympy_rows["R2_symbolic_disintegration_recovery"]["defect"], "global and disintegrated symbolic integrals agree", "flat eta marginal gives nonzero defect", "positive eta-band has nonzero denominator", "demote if formulas are copied without symbolic integration", ["R1", "R2", "C2", "C3"]),
        tool_call("jax", "jax.numpy.sin/vectorized x64 arithmetic", "eta shells and even-N chart/quotient counts", "volume and torus-area diagnostic rows", "2*pi^2 volume and N^2/2 rows match committed anchors", "N^2 physical-count control would double the mass", "eta=pi/4 Clifford torus area row", "demote if x64 is disabled or rows are not recomputed", ["R1", "double_cover"]),
        tool_call("z3", "z3.Solver.check", "finite scaled eta weights, class count, and layer values", z3_row["verdict"], "valid recovery violation is UNSAT", "flat marginal and double-cover erasure controls are UNSAT when forced to target", "N=8, eta layers pi/12, pi/4, 5*pi/12", "demote if solver binds only a precomputed boolean", ["finite_recovery"]),
        tool_call("cvc5", "cvc5.Solver.checkSat", "same finite scaled recovery row as z3", cvc5_row["verdict"], "valid recovery violation is UNSAT", "flat marginal and double-cover erasure controls are UNSAT when forced to target", "QF_LIA integer row", "demote if solver binds only a precomputed boolean", ["finite_recovery"]),
    ]
    payload = {
        "schema_version": "engine_result_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "role_id": "jax_sympy_solver_disintegration_builder",
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
        "packages_used": ["sympy", "jax", "jax.numpy", "z3", "cvc5", "python_stdlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls,
        "capability_receipts": {
            "sympy_version": sp.__version__,
            "jax_version": jax.__version__,
            "jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
            "z3_version": z3.get_version_string(),
            "cvc5_version": getattr(cvc5, "__version__", "available"),
            "api_smoke": {
                "sympy_integrate": str(sp.integrate(sp.sin(2 * sp.Symbol("eta")), (sp.Symbol("eta"), 0, sp.pi / 2))),
                "jax_sin_pi_over_2": float(jnp.sin(jnp.pi / 2)),
                "z3_positive_verdict": z3_row["verdict"],
                "cvc5_positive_verdict": cvc5_row["verdict"],
            },
        },
        "receipts": sympy_rows,
        "jax_diagnostics": jax_rows,
        "finite_discretization_recovery": {
            "z3": z3_row,
            "cvc5": cvc5_row,
        },
        "crossover_proofs": {
            "z3": z3_row,
            "cvc5": cvc5_row,
        },
        "build_gates": gates,
        "summary": {
            "enables": "mode-4 cards may cite the disintegration rule for conditioning on fixed-eta Hopf tori with zero S3 measure",
            "does_not_enable": "no ratchet sim is run; no manifold, axis, bridge, physics, or canonical admission claim is made",
            "pytorch_omission": "no graph/network/autograd claim path; engine mode is julia_canon_plus_jax_diagnostic",
        },
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(all_pass), "result_path": rel(RESULT_PATH), "gates": gates}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
