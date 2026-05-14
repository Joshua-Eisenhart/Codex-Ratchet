#!/usr/bin/env python3
"""
sim_sympy_symbolic_identity_micro.py -- SymPy symbolic identity micro-probe.

Tool-stage scope:
  tool_target: sympy
  function_surface: diff, integrate, factor, simplify over one-variable exact
    scalar expressions
  micro_claim: SymPy can certify a tiny derivative/integral identity for
    sin(x)^2, factor x^4 - 1 exactly, reject wrong scalar identities, and
    handle zero/constant symbolic boundaries.

This is pre-lego evidence only. It does not promote a lego, matrix identity,
integration search, broad simplification claim, or tool-tool coupling.
"""

import json
import os
import sys

from receipt_boundary import apply_default_receipt_boundary


classification = "canonical"
NAME = "sim_sympy_symbolic_identity_micro"
PROBE_FAMILY = "sympy_scalar_symbolic_identity_micro"
CONSTRAINT_SET = "exact_scalar_diff_integrate_factor_identity"

_NOT_USED_REASON = (
    "not used: this micro probe isolates SymPy scalar symbolic identity "
    "checks only; cross-tool coupling and lego promotion are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": "under test"},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "load-bearing: diff, integrate, factor, expand, and simplify produce "
        "the scalar symbolic identity verdicts"
    )
    SP_OK = True
    SP_VERSION = sp.__version__
except Exception as exc:
    SP_OK = False
    SP_VERSION = None
    TOOL_MANIFEST["sympy"]["reason"] = f"not installed: {exc}"


def _missing_sympy():
    return {"passed": False, "detail": "sympy unavailable"}


def _is_zero(expr):
    return sp.simplify(expr) == 0


def run_positive_tests():
    if not SP_OK:
        return {"sympy_available": _missing_sympy()}

    x = sp.Symbol("x")
    target = sp.sin(x) ** 2
    antiderivative = x / 2 - sp.sin(2 * x) / 4
    integrated = sp.integrate(target, x)
    derivative = sp.diff(antiderivative, x)
    polynomial = x**4 - 1
    expected_factor = (x - 1) * (x + 1) * (x**2 + 1)
    factored = sp.factor(polynomial)

    return {
        "sin_squared_antiderivative_certified": {
            "passed": _is_zero(integrated - antiderivative) and _is_zero(derivative - target),
            "expected": "integrate(sin(x)^2) = x/2 - sin(2*x)/4 up to exact simplification",
            "integrated": str(integrated),
            "derivative_of_candidate": str(derivative),
        },
        "factor_x4_minus_1_exactly": {
            "passed": factored == expected_factor and sp.expand(factored - polynomial) == 0,
            "expected": "(x - 1)*(x + 1)*(x**2 + 1)",
            "factored": str(factored),
            "expanded_difference": str(sp.expand(factored - polynomial)),
        },
        "diff_integrate_round_trip_for_named_fixture": {
            "passed": _is_zero(sp.diff(sp.integrate(target, x), x) - target),
            "expected": "diff(integrate(sin(x)^2, x), x) recovers sin(x)^2",
            "round_trip": str(sp.diff(sp.integrate(target, x), x)),
        },
    }


def run_negative_tests():
    if not SP_OK:
        return {"sympy_available": _missing_sympy()}

    x = sp.Symbol("x")
    target = sp.sin(x) ** 2
    wrong_antiderivative = x / 2 + sp.sin(2 * x) / 4
    wrong_derivative = sp.diff(wrong_antiderivative, x)
    polynomial = x**4 - 1
    wrong_factorization = (x**2 - 1) ** 2

    return {
        "wrong_antiderivative_excluded": {
            "passed": not _is_zero(wrong_derivative - target),
            "expected": "x/2 + sin(2*x)/4 is not an antiderivative of sin(x)^2",
            "wrong_derivative": str(wrong_derivative),
            "residual": str(sp.simplify(wrong_derivative - target)),
        },
        "wrong_factorization_excluded": {
            "passed": sp.expand(wrong_factorization - polynomial) != 0,
            "expected": "(x**2 - 1)**2 is not x**4 - 1",
            "expanded_wrong_factorization": str(sp.expand(wrong_factorization)),
            "expanded_residual": str(sp.expand(wrong_factorization - polynomial)),
        },
    }


def run_boundary_tests():
    if not SP_OK:
        return {"sympy_available": _missing_sympy()}

    x = sp.Symbol("x")
    zero_expr = sp.Integer(0)
    constant = sp.Integer(7)
    zero_integral = sp.integrate(zero_expr, x)
    constant_derivative = sp.diff(constant, x)
    constant_integral = sp.integrate(constant, x)
    zero_factor = sp.factor(zero_expr)
    unit_factor = sp.factor(sp.Integer(1))

    return {
        "zero_expression_boundary": {
            "passed": zero_integral == 0 and zero_factor == 0,
            "expected": "integrate(0, x) and factor(0) preserve exact zero",
            "zero_integral": str(zero_integral),
            "zero_factor": str(zero_factor),
        },
        "constant_derivative_boundary": {
            "passed": constant_derivative == 0 and sp.diff(constant_integral, x) == constant,
            "expected": "diff(7, x) = 0 and diff(integrate(7, x), x) = 7",
            "constant_derivative": str(constant_derivative),
            "constant_integral": str(constant_integral),
        },
        "unit_factor_boundary": {
            "passed": unit_factor == 1 and sp.expand(unit_factor - 1) == 0,
            "expected": "factor(1) remains the exact multiplicative unit",
            "unit_factor": str(unit_factor),
        },
    }


def _flatten_sections(*sections):
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    flat_tests = _flatten_sections(positive, negative, boundary)
    all_pass = all(test.get("passed") for test in flat_tests)

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "function_surface": "sympy.diff, sympy.integrate, sympy.factor, sympy.expand, and sympy.simplify over exact scalar expressions",
        "micro_claim": (
            "SymPy certifies a tiny sin(x)^2 derivative/integral identity and "
            "exactly factors x^4 - 1 while rejecting named wrong scalar identities."
        ),
        "operation_sequence": [
            "construct exact one-variable scalar expressions sin(x)^2 and x^4 - 1",
            "compute integrate(sin(x)^2, x), diff(candidate_antiderivative, x), factor(x^4 - 1), expand(factorization)",
            "simplify residuals for the named correct identities",
            "run wrong-antiderivative and wrong-factorization graveyards",
            "run zero, constant, and unit symbolic boundary checks",
        ],
        "carrier_topology": (
            "one formal scalar variable over exact symbolic expressions; no "
            "density carrier, graph, manifold, bundle, or topology claim"
        ),
        "observable": (
            "exact symbolic residuals after simplify/expand plus equality of "
            "the named factorization and boundary expressions"
        ),
        "pass_fail_predicate": (
            "correct derivative/integral and factorization residuals reduce to "
            "zero; named wrong identities have nonzero residuals; zero, "
            "constant, and unit boundaries remain exact"
        ),
        "graveyards": [
            "wrong antiderivative x/2 + sin(2*x)/4 has nonzero derivative residual",
            "wrong factorization (x**2 - 1)**2 has nonzero expanded residual",
            "zero, constant, and unit boundaries prevent treating generic simplification as the claim",
        ],
        "baselines": [
            "numeric finite-difference or quadrature checks are intentionally not used as proof of exact symbolic identity",
            "boundary fixtures 0, 7, and 1 provide exact scalar sanity baselines",
        ],
        "alternative_formulations": [
            "cvc5 or z3 real-arithmetic encoding of bounded polynomial identities",
            "SymPy matrix identity micro probe for non-scalar exact algebra",
            "operator-family lego fit packet after exact scalar and matrix surfaces both have receipts",
        ],
        "tool_function_needs": {
            "sympy": ["diff", "integrate", "factor", "expand", "simplify"],
        },
        "lego_coupling_target": "symbolic_identity_micro; exact_algebra_support; operator_family_later_only",
        "sympy_version": SP_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other one-variable exact scalar identities may survive; this receipt only covers the named sin(x)^2 and x^4 - 1 fixtures.",
            "Equivalent antiderivatives that differ by a constant remain admissible when their derivative reduces exactly to sin(x)^2.",
        ],
        "demotion_condition": (
            "Demote SymPy for this scalar symbolic surface if diff/integrate "
            "cannot certify the named sin(x)^2 identity, if factor cannot "
            "produce and re-expand the exact x^4 - 1 factorization, if the "
            "wrong antiderivative or wrong factorization is admitted, or if "
            "zero/constant boundaries fail exact simplification."
        ),
        "out_of_scope": [
            "no matrix identity claim",
            "no integration search benchmark",
            "no broad symbolic simplification claim",
            "no operator-family admission beyond the named scalar fixtures",
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no proof of the whole SymPy library",
        ],
        "criteria_checked": [
            "SymPy integrates sin(x)^2 to the exact named antiderivative",
            "SymPy differentiates the named antiderivative back to sin(x)^2",
            "SymPy factors x^4 - 1 and the factorization re-expands exactly",
            "A wrong antiderivative is excluded by nonzero residual",
            "A wrong factorization is excluded by nonzero expanded residual",
            "Zero and constant symbolic boundaries remain exact",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_sympy_symbolic_identity_micro",
        target="Use as bounded SymPy scalar symbolic identity function evidence before exact-algebra or operator-family lego fit packets.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
    sys.exit(0)
