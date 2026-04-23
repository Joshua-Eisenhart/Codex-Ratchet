#!/usr/bin/env python3
"""
sim_capability_sympy_isolated.py -- Isolated tool-capability probe for sympy.

Classical_baseline capability probe: demonstrates sympy symbolic math can
compute derivatives, integrals, matrix algebra, polynomial factoring, and
equation solving. Honest CAN/CANNOT summary. No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates sympy symbolic computation capability alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": True,  "used": True,  "reason": "load-bearing: sympy symbolic engine is the sole subject; differentiation, integration, matrix algebra, and polynomial operations are all computed by sympy directly."},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": "load_bearing", "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

SYMPY_OK = False
try:
    import sympy as sp
    SYMPY_OK = True
except Exception:
    pass


def run_positive_tests():
    r = {}
    if not SYMPY_OK:
        r["sympy_available"] = {"pass": False, "detail": "sympy not importable"}
        return r
    r["sympy_available"] = {"pass": True, "version": sp.__version__}

    x, y = sp.symbols("x y")

    # --- Test 1: symbolic differentiation ---
    f = sp.sin(x) * sp.exp(x)
    df = sp.diff(f, x)
    # d/dx [sin(x)*exp(x)] = cos(x)*exp(x) + sin(x)*exp(x)
    expected = sp.cos(x) * sp.exp(x) + sp.sin(x) * sp.exp(x)
    eq = sp.simplify(df - expected) == 0
    r["differentiation"] = {
        "pass": bool(eq),
        "detail": f"d/dx[sin(x)*exp(x)] = {df}",
    }

    # --- Test 2: symbolic integration ---
    g = x**2
    ig = sp.integrate(g, x)
    expected_ig = sp.Rational(1, 3) * x**3
    eq2 = sp.simplify(ig - expected_ig) == 0
    r["integration"] = {
        "pass": bool(eq2),
        "detail": f"integral(x^2) = {ig}",
    }

    # --- Test 3: definite integral ---
    defint = sp.integrate(x**2, (x, 0, 1))
    r["definite_integral"] = {
        "pass": defint == sp.Rational(1, 3),
        "result": str(defint),
        "detail": "integral(x^2, 0, 1) = 1/3",
    }

    # --- Test 4: polynomial factoring ---
    poly = x**2 - 5*x + 6
    factored = sp.factor(poly)
    r["polynomial_factor"] = {
        "pass": factored == (x - 2) * (x - 3),
        "result": str(factored),
        "detail": "x^2 - 5x + 6 = (x-2)(x-3)",
    }

    # --- Test 5: solve equations ---
    solutions = sp.solve(x**2 - 4, x)
    r["equation_solve"] = {
        "pass": set(solutions) == {2, -2},
        "result": str(solutions),
        "detail": "x^2 = 4 has solutions x = ±2",
    }

    # --- Test 6: matrix algebra ---
    A = sp.Matrix([[1, 2], [3, 4]])
    det_A = A.det()
    r["matrix_determinant"] = {
        "pass": det_A == -2,
        "result": str(det_A),
        "detail": "det([[1,2],[3,4]]) = -2",
    }

    # --- Test 7: symbolic limit ---
    lim = sp.limit(sp.sin(x)/x, x, 0)
    r["limit"] = {
        "pass": lim == 1,
        "result": str(lim),
        "detail": "lim(sin(x)/x, x->0) = 1",
    }

    # --- Test 8: series expansion ---
    series = sp.series(sp.exp(x), x, 0, 4)
    expected_coeff = {0: 1, 1: 1, 2: sp.Rational(1, 2), 3: sp.Rational(1, 6)}
    coeff_ok = all(series.coeff(x, k) == v for k, v in expected_coeff.items())
    r["series_expansion"] = {
        "pass": bool(coeff_ok),
        "detail": f"exp(x) around 0 to order 4: {series}",
    }

    return r


def run_negative_tests():
    r = {}
    if not SYMPY_OK:
        r["sympy_unavailable"] = {"pass": True, "detail": "skip: sympy not installed"}
        return r

    x = sp.Symbol("x")

    # --- Neg 1: non-elementary integral stays unevaluated ---
    # sympy.integrate(exp(-x^2)) returns a special form, not a polynomial
    result = sp.integrate(sp.exp(-x**2), x)
    is_polynomial = result.is_polynomial(x)
    r["non_elementary_integral_not_polynomial"] = {
        "pass": not is_polynomial,
        "result": str(result),
        "detail": "integral(exp(-x^2)) is not a polynomial; sympy returns erf-based form",
    }

    # --- Neg 2: solve overdetermined system returns empty ---
    solutions = sp.solve([x - 1, x - 2], x)
    r["overdetermined_no_solution"] = {
        "pass": solutions == [] or solutions == {},
        "result": str(solutions),
        "detail": "x=1 AND x=2 has no solution",
    }

    # --- Neg 3: division by zero caught as zoo (complex infinity) ---
    result2 = sp.limit(1/x, x, 0)
    # limit from both sides is zoo (unsigned infinity) or oo depending on direction
    r["division_by_zero_handled"] = {
        "pass": result2 in (sp.zoo, sp.oo, -sp.oo, sp.nan) or result2.is_infinite,
        "result": str(result2),
        "detail": "lim(1/x, x->0) is ±oo or zoo, not a finite number",
    }

    return r


def run_boundary_tests():
    r = {}
    if not SYMPY_OK:
        r["sympy_unavailable"] = {"pass": True, "detail": "skip: sympy not installed"}
        return r

    x = sp.Symbol("x")

    # --- Boundary 1: zero polynomial ---
    z = sp.Integer(0)
    dz = sp.diff(z, x)
    r["derivative_of_zero"] = {
        "pass": dz == 0,
        "result": str(dz),
        "detail": "d/dx[0] = 0",
    }

    # --- Boundary 2: identity matrix determinant ---
    I = sp.eye(3)
    r["identity_determinant"] = {
        "pass": I.det() == 1,
        "result": str(I.det()),
        "detail": "det(I_3) = 1",
    }

    # --- Boundary 3: large power simplification ---
    result = sp.expand((x + 1)**10)
    coeff_10 = result.coeff(x, 10)
    r["large_power_expand"] = {
        "pass": coeff_10 == 1,
        "result": f"leading coeff: {coeff_10}",
        "detail": "(x+1)^10 leading coefficient is 1",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all([v.get("pass", False) for v in all_tests.values() if isinstance(v, dict) and "pass" in v])

    results = {
        "name": "sim_capability_sympy_isolated",
        "classification": classification,
        "overall_pass": overall,
        "capability_summary": {
            "CAN": [
                "compute exact symbolic derivatives and integrals",
                "factor polynomials and solve algebraic equations exactly",
                "compute matrix operations (det, inverse, eigenvalues) symbolically",
                "evaluate limits and series expansions",
                "handle arbitrary precision rational arithmetic",
                "simplify trigonometric, exponential, and logarithmic expressions",
            ],
            "CANNOT": [
                "guarantee finite computation for all integrals (non-elementary integrals may stall)",
                "replace numerical solvers for transcendental equations with no closed form",
                "perform fast numerical computation (use pytorch/numpy for that)",
                "decide validity of logical formulas (use z3/cvc5 for that)",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_sympy_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
