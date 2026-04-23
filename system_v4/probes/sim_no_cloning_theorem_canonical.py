#!/usr/bin/env python3
"""No-cloning theorem: a unitary U with U|psi>|0> = |psi>|psi> for two
nonorthogonal states |a>, |b> requires <a|b> = <a|b>^2, forcing <a|b> in {0,1}.
For nonorthogonal 0<|<a|b>|<1 this is a contradiction.

Load-bearing: sympy (exact symbolic inner-product preservation contradiction).
"""

import json
import os

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Exact symbolic solve of c == c**2 for inner-product preservation "
        "(unitarity) vs cloning; load-bearing for no-cloning contradiction."
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    raise


def cloning_contradiction(c_value):
    """Given inner product c = <a|b>, cloning + unitarity forces c = c^2.
    Returns (gap, allowed). gap = |c - c^2|, allowed = c in {0, 1}."""
    c = sp.Symbol("c", complex=True)
    eq = sp.Eq(c, c * c)  # unitarity preserves inner product: <a|b> = <a|b>^2
    sols = sp.solve(eq, c)
    c_val = sp.sympify(c_value)
    gap = sp.Abs(c_val - c_val ** 2)
    allowed = any(sp.simplify(c_val - s) == 0 for s in sols)
    return float(gap), bool(allowed), [complex(s) for s in sols]


def run_positive_tests():
    # Nonorthogonal <a|b> = 1/2: cloning is forbidden, gap > 0
    gap, allowed, sols = cloning_contradiction(sp.Rational(1, 2))
    return {
        "nonorthogonal_c_half_gap": gap,
        "allowed_values": [str(s) for s in sols],
        "cloning_forbidden": (not allowed) and gap > 0,
    }


def run_negative_tests():
    # c = 0 (orthogonal): cloning-compatible; gap = 0
    gap, allowed, _ = cloning_contradiction(0)
    return {
        "orthogonal_gap": gap,
        "orthogonal_allowed": bool(allowed and gap == 0),
    }


def run_boundary_tests():
    # c = 1 (identical states): trivially cloneable; gap = 0
    gap1, allowed1, _ = cloning_contradiction(1)
    # c = 1/sqrt(2): another nonorthogonal boundary, forbidden
    gap2, allowed2, _ = cloning_contradiction(1 / sp.sqrt(2))
    return {
        "identical_gap": gap1,
        "identical_allowed": bool(allowed1 and gap1 == 0),
        "c_inv_sqrt2_gap": gap2,
        "c_inv_sqrt2_forbidden": (not allowed2) and gap2 > 0,
    }


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        bool(pos["cloning_forbidden"])
        and bool(neg["orthogonal_allowed"])
        and bool(bnd["identical_allowed"])
        and bool(bnd["c_inv_sqrt2_forbidden"])
    )
    results = {
        "name": "no_cloning_theorem_canonical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "quantum_classical_gap": {
            "metric": "|c - c^2| for <a|b>=1/2",
            "gap": pos["nonorthogonal_c_half_gap"],
        },
        "summary": {"all_pass": bool(all_pass)},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "no_cloning_theorem_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
