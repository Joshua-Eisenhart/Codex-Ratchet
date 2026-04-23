#!/usr/bin/env python3
"""sim_sympy_gaussian_integral -- Certifies integral_{-inf}^{inf} exp(-x^2) dx = sqrt(pi)
exactly via sympy.integrate. Includes scaled and shifted boundary cases.
"""
import json, os
import numpy as np
import sympy as sp

TOOL_MANIFEST = {
    "pytorch":{"tried":False,"used":False,"reason":"no symbolic integration"},
    "pyg":{"tried":False,"used":False,"reason":"n/a"},
    "z3":{"tried":False,"used":False,"reason":"transcendental integrals outside SMT"},
    "cvc5":{"tried":False,"used":False,"reason":"same"},
    "sympy":{"tried":True,"used":True,"reason":"sympy.integrate returns sqrt(pi) exactly; equality tested symbolically"},
    "clifford":{"tried":False,"used":False,"reason":"n/a"},
    "geomstats":{"tried":False,"used":False,"reason":"n/a"},
    "e3nn":{"tried":False,"used":False,"reason":"n/a"},
    "rustworkx":{"tried":False,"used":False,"reason":"n/a"},
    "xgi":{"tried":False,"used":False,"reason":"n/a"},
    "toponetx":{"tried":False,"used":False,"reason":"n/a"},
    "gudhi":{"tried":False,"used":False,"reason":"n/a"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"


def run_positive_tests():
    x = sp.symbols('x', real=True)
    val = sp.integrate(sp.exp(-x**2), (x, -sp.oo, sp.oo))
    eq = sp.simplify(val - sp.sqrt(sp.pi)) == 0
    return {"gaussian_integral_exact": eq, "value": str(val)}


def run_negative_tests():
    x = sp.symbols('x', real=True)
    val = sp.integrate(sp.exp(-x**2), (x, -sp.oo, sp.oo))
    return {"not_equal_to_pi": sp.simplify(val - sp.pi) != 0,
            "not_equal_to_2sqrtpi": sp.simplify(val - 2*sp.sqrt(sp.pi)) != 0}


def run_boundary_tests():
    x = sp.symbols('x', real=True)
    a = sp.symbols('a', positive=True)
    # scaled: integral exp(-a x^2) = sqrt(pi/a)
    val_scaled = sp.integrate(sp.exp(-a*x**2), (x, -sp.oo, sp.oo))
    eq_scaled = sp.simplify(val_scaled - sp.sqrt(sp.pi/a)) == 0
    # shifted: integral exp(-(x-mu)^2) = sqrt(pi)
    mu = sp.symbols('mu', real=True)
    val_shift = sp.integrate(sp.exp(-(x-mu)**2), (x, -sp.oo, sp.oo))
    eq_shift = sp.simplify(val_shift - sp.sqrt(sp.pi)) == 0
    # half-line: integral_0^inf exp(-x^2) = sqrt(pi)/2
    val_half = sp.integrate(sp.exp(-x**2), (x, 0, sp.oo))
    eq_half = sp.simplify(val_half - sp.sqrt(sp.pi)/2) == 0
    return {"scaled": eq_scaled, "shifted": eq_shift, "half_line": eq_half}


def run_ablation():
    # numeric quad only approximates.
    from scipy.integrate import quad
    val, err = quad(lambda x: np.exp(-x*x), -np.inf, np.inf)
    return {"numpy_scipy_numeric_only": True,
            "numeric_value": float(val),
            "residual_vs_sqrt_pi": float(abs(val - np.sqrt(np.pi))),
            "reported_error_estimate": float(err),
            "note": "quad returns float approximation; cannot certify exact sqrt(pi) identity"}


if __name__ == "__main__":
    results = {
        "name": "sympy_gaussian_integral",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "ablation": run_ablation(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sympy_gaussian_integral_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
