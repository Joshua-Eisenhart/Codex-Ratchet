#!/usr/bin/env python3
"""
sim_gerbe_higher_gauge_multishell

Bundle-gerbe sketch on nested Hopf tori: a gerbe carries a 2-form curvature B
whose integral over closed 2-cycles distinguishes admissible multi-shell
configurations from excluded ones. We realize B as a clifford 2-blade
(Cl(3) bivector) and its integral symbolically via sympy. Admissibility
test: sum of B-fluxes over the three pairwise-overlap 2-cells is
integer-quantized (mod 2pi) iff the shells coexist; otherwise excluded.
"""

import json
import os
import numpy as np

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
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"
    Cl = None

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    sp = None


# Cl(3) setup
layout, blades = Cl(3)
e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
e12, e23, e13 = blades["e12"], blades["e23"], blades["e13"]


def gerbe_curvature_2form(n):
    """Integer class n -> bivector B = n*e12 (flux quantum on shell)."""
    return n * e12


def flux_over_overlap(B, area):
    """Extract bivector coefficient (e12 component) and multiply by area."""
    return float((B * ~e12)(0)) * area  # scalar grade-0 projection


def admissibility_flux_sum(ns, areas):
    """Sum of shell fluxes. Admissible iff sum is integer multiple of 2pi
    (here we scale so quantum=1, admissible iff sum is near-integer)."""
    total = 0.0
    for n, a in zip(ns, areas):
        total += flux_over_overlap(gerbe_curvature_2form(n), a)
    # sympy symbolic quantization check
    q = sp.nsimplify(total, rational=True)
    return total, (sp.denom(q) == 1)


# ---------------------------------------------------------------------
# POSITIVE
# ---------------------------------------------------------------------
def run_positive_tests():
    res = {}
    # Three shells with integer classes and unit areas: admissible
    total, ok = admissibility_flux_sum([1, 2, 3], [1.0, 1.0, 1.0])
    res["integer_class_multishell_admissible"] = {"pass": ok, "flux": total}
    # Two-shell pair cancelling: admissible
    total, ok = admissibility_flux_sum([2, -2], [1.0, 1.0])
    res["cancelling_pair_admissible"] = {"pass": ok and abs(total) < 1e-12, "flux": total}
    return res


# ---------------------------------------------------------------------
# NEGATIVE
# ---------------------------------------------------------------------
def run_negative_tests():
    res = {}
    # Non-integer curvature (fractional area) => fails quantization => excluded
    total, ok = admissibility_flux_sum([1, 1, 1], [0.3, 0.3, 0.3])
    res["fractional_flux_excluded"] = {"pass": not ok, "flux": total}
    # Single irrational-class shell
    total, ok = admissibility_flux_sum([1], [float(np.pi) / 5.0])
    res["irrational_single_shell_excluded"] = {"pass": not ok, "flux": total}
    return res


# ---------------------------------------------------------------------
# BOUNDARY
# ---------------------------------------------------------------------
def run_boundary_tests():
    res = {}
    # Zero curvature is trivially admissible
    total, ok = admissibility_flux_sum([0, 0], [1.0, 1.0])
    res["zero_curvature_boundary"] = {"pass": ok and total == 0.0}
    # Large integer: still admissible
    total, ok = admissibility_flux_sum([1000], [1.0])
    res["large_integer_boundary"] = {"pass": ok, "flux": total}
    return res


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "Cl(3) bivector realizes gerbe 2-form curvature; grade-projection gives flux"
    )
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "symbolic quantization test: admissibility = integer class via nsimplify"
    )
    for k, v in TOOL_MANIFEST.items():
        if not v["used"] and not v["reason"]:
            v["reason"] = "not required for gerbe curvature admissibility test"

    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

    all_tests = {**pos, **neg, **bnd}
    all_pass = all(t["pass"] for t in all_tests.values())

    results = {
        "name": "sim_gerbe_higher_gauge_multishell",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "classification": "canonical",
        "language_discipline": "admissibility/exclusion only",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_gerbe_higher_gauge_multishell_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
