#!/usr/bin/env python3
"""
Tool-capability probe for SymPy.

This probe checks that SymPy survives several exact symbolic tasks in isolation:
- positive: factorization, exact linear solve, symbolic differentiation/integration round-trip
- negative: inconsistent system exclusion, no real root admission for x**2 + 1, failed divisibility
- boundary: zero polynomial, repeated-root discriminant collapse, removable singularity limit

The probe is canonical by process only after it is committed and enqueued; Hermes workers do not execute it.
"""

import json
import os

import sympy as sp

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact symbolic algebra is the load-bearing substrate for factoring, solving, and limit checks in every test section.",
    }
}

TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing"}
classification = "canonical"
NAME = "tool_capability_sympy"
SCOPE_NOTE = "Tier A SymPy capability probe: isolated exact symbolic algebra, solving, and limit behavior only."
CANONICAL_TOOL_NAMES = (
    "pytorch",
    "pyg",
    "z3",
    "cvc5",
    "sympy",
    "clifford",
    "geomstats",
    "e3nn",
    "rustworkx",
    "xgi",
    "toponetx",
    "gudhi",
)
for _tool_name in CANONICAL_TOOL_NAMES:
    TOOL_MANIFEST.setdefault(
        _tool_name,
        {
            "tried": False,
            "used": False,
            "reason": f"not used; {NAME} isolates sympy capability only",
        },
    )
    TOOL_INTEGRATION_DEPTH.setdefault(_tool_name, None)


def _serialize(value):
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if isinstance(value, set):
        return sorted(_serialize(v) for v in value)
    if isinstance(value, sp.Basic):
        return sp.srepr(value) if value.is_Atom else str(value)
    return value


def _row_passes(row):
    if row.get("status") == "skipped":
        return False
    keys = (
        "matches_expected",
        "all_zero_residuals",
        "roundtrip_exact",
        "is_emptyset",
        "nonzero_remainder",
        "stays_zero",
        "discriminant_zero",
        "double_root_at_2",
        "equals_one",
    )
    hits = [bool(row[key]) for key in keys if key in row]
    return bool(hits) and all(hits)


def _section_passes(section):
    return bool(section) and all(_row_passes(row) for row in section.values())


def run_positive_tests():
    x, y = sp.symbols("x y", real=True)
    results = {}

    poly = x**4 - 10 * x**2 + 9
    expected_factor = (x - 3) * (x - 1) * (x + 1) * (x + 3)
    factored = sp.factor(poly)
    results["factor_quartic_exactly"] = {
        "input": str(poly),
        "factored": str(factored),
        "expected": str(expected_factor),
        "matches_expected": sp.expand(factored - expected_factor) == 0,
    }

    equations = [
        sp.Eq(2 * x + y, 1),
        sp.Eq(x - y, sp.Rational(1, 3)),
    ]
    solution = sp.solve(equations, (x, y), dict=True)[0]
    residuals = [sp.simplify(eq.lhs.subs(solution) - eq.rhs) for eq in equations]
    results["solve_linear_system_exactly"] = {
        "equations": [str(eq) for eq in equations],
        "solution": {str(k): str(v) for k, v in solution.items()},
        "residuals": [str(r) for r in residuals],
        "all_zero_residuals": all(r == 0 for r in residuals),
    }

    expr = sp.sin(x) * sp.exp(x)
    recovered = sp.simplify(sp.diff(sp.integrate(expr, x), x) - expr)
    results["differentiate_integral_roundtrip"] = {
        "expression": str(expr),
        "roundtrip_residual": str(recovered),
        "roundtrip_exact": recovered == 0,
    }

    return results


def run_negative_tests():
    x, y = sp.symbols("x y", real=True)
    results = {}

    inconsistent = sp.linsolve([
        sp.Eq(x + y, 1),
        sp.Eq(x + y, 2),
    ], (x, y))
    results["reject_inconsistent_linear_system"] = {
        "solution_set": str(inconsistent),
        "is_emptyset": inconsistent == sp.EmptySet,
    }

    no_real_roots = sp.solveset(sp.Eq(x**2 + 1, 0), x, domain=sp.S.Reals)
    results["exclude_real_roots_for_x2_plus_1"] = {
        "solution_set": str(no_real_roots),
        "is_emptyset": no_real_roots == sp.EmptySet,
    }

    dividend = x**3 - 1
    divisor = x + 1
    quotient, remainder = sp.div(dividend, divisor)
    results["failed_divisibility_detected"] = {
        "dividend": str(dividend),
        "divisor": str(divisor),
        "quotient": str(quotient),
        "remainder": str(remainder),
        "nonzero_remainder": remainder != 0,
    }

    return results


def run_boundary_tests():
    x = sp.symbols("x", real=True)
    results = {}

    zero_factor = sp.factor(0)
    results["zero_polynomial_factorization"] = {
        "factored": str(zero_factor),
        "stays_zero": zero_factor == 0,
    }

    repeated = (x - 2) ** 2
    discriminant = sp.discriminant(sp.expand(repeated), x)
    roots = sp.roots(sp.expand(repeated), x)
    results["repeated_root_discriminant_collapse"] = {
        "polynomial": str(sp.expand(repeated)),
        "discriminant": str(discriminant),
        "root_multiplicities": {str(k): v for k, v in roots.items()},
        "discriminant_zero": discriminant == 0,
        "double_root_at_2": roots == {sp.Integer(2): 2},
    }

    removable = sp.limit(sp.sin(x) / x, x, 0)
    results["removable_singularity_limit"] = {
        "expression": "sin(x)/x",
        "limit_at_zero": str(removable),
        "equals_one": removable == 1,
    }

    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_passes(positive),
        "negative_all_pass": _section_passes(negative),
        "boundary_all_pass": _section_passes(boundary),
        "promotion_allowed": False,
        "claim_ceiling": "isolated_sympy_capability_only",
        "scope_note": SCOPE_NOTE,
    }
    summary["all_pass"] = bool(summary["positive_all_pass"] and summary["negative_all_pass"] and summary["boundary_all_pass"])
    results = {
        "name": NAME,
        "classification": classification,
        "classification_note": SCOPE_NOTE,
        "divergence_log": SCOPE_NOTE,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w") as f:
        json.dump(_serialize(results), f, indent=2)
    print(f"Results written to {out_path}")
