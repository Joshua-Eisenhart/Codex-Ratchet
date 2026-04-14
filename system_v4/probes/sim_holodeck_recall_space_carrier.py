#!/usr/bin/env python3
"""sim_holodeck_recall_space_carrier -- recall space as projective carrier.

Thesis: the holodeck "carrier" is a projective space P^n (rays, not vectors).
Two vectors v, lambda*v with lambda != 0 must be indistinguishable on the
carrier. We verify this using sympy symbolic normalization and a numpy
sanity check. This is a classical_baseline: no nonclassical tool is
load-bearing; sympy is load-bearing for the exact equivalence.
"""
import numpy as np
import sympy as sp
import sys, os
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import write_results, summary_ok

divergence_log = "Classical baseline: holodeck recall-space carrier is modeled here by symbolic ray-equivalence checks and numeric sanity checks, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "numeric cross-check of rays"},
    "sympy": {"tried": True, "used": True, "reason": "exact projective equivalence via rank/collinearity"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "sympy": "supportive",
    "clifford": None,
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def ray(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def sym_ray_eq(v, w):
    v = sp.Matrix(v); w = sp.Matrix(w)
    # rays equal iff v x w = 0 (collinear) and both nonzero
    if v.norm() == 0 or w.norm() == 0:
        return False
    # cross via wedge in 3D; generalize with rank of [v|w]
    M = v.row_join(w)
    return M.rank() == 1


def run_positive_tests():
    r = {}
    v = [1.0, 2.0, 3.0]
    lam = 4.7
    r["ray_collapse_numeric"] = np.allclose(ray(v), ray([lam * x for x in v]))
    r["ray_collapse_symbolic"] = sym_ray_eq(v, [lam * x for x in v])
    # three distinct rays are distinct
    r["distinct_rays"] = not sym_ray_eq([1, 0, 0], [0, 1, 0])
    return r


def run_negative_tests():
    r = {}
    # A bogus claim: nonparallel vectors are the same ray -- MUST be False
    r["nonparallel_same_ray"] = sym_ray_eq([1, 0, 0], [1, 1, 0])
    # Zero vector is a valid ray -- MUST be False
    r["zero_is_ray"] = sym_ray_eq([0, 0, 0], [1, 0, 0])
    return r


def run_boundary_tests():
    r = {}
    # negative scalar still same projective ray
    r["negative_scalar_same_ray"] = sym_ray_eq([1, 2, 3], [-1, -2, -3])
    # very small scalar (nonzero) still same ray
    r["tiny_scalar_same_ray"] = sym_ray_eq([1, 2, 3], [sp.Rational(1, 10**9), sp.Rational(2, 10**9), sp.Rational(3, 10**9)])
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_recall_space_carrier",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_recall_space_carrier", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)
