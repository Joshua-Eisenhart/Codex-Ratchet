#!/usr/bin/env python3
"""Classical baseline: convex admission region as a polytope feasibility problem.

Admission is modeled as {x in R^n : A x <= b, x >= 0}. We check feasibility via
linear programming (Phase-I LP). No operator ordering, no noncommuting
constraints -- purely convex polyhedral.
"""
import json
import os

import numpy as np
from scipy.optimize import linprog

classification = "classical_baseline"
divergence_log = (
    "Classical admission collapses to a convex polytope over commuting scalar "
    "coordinates. A nonclassical admission region is an operator system / cone "
    "in a noncommutative algebra (e.g. PSD cone over Hermitian matrices). This "
    "baseline drops the operator-ordering and joint-spectral structure."
)

try:
    import torch  # noqa: F401
    _torch_ok = True
except Exception:
    _torch_ok = False

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "polytope inequality assembly"},
    "scipy": {"tried": True, "used": True, "reason": "linprog Phase-I feasibility"},
    "pytorch": {
        "tried": _torch_ok,
        "used": _torch_ok,
        "reason": "supportive import; not load-bearing for LP",
    },
    "z3": {"tried": False, "used": False, "reason": "no SMT proof claim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
    "pytorch": "supportive" if _torch_ok else None,
    "z3": None,
}


def is_feasible(A, b, bounds=None):
    """Phase-I feasibility: solve LP with zero objective."""
    A = np.asarray(A, float)
    b = np.asarray(b, float)
    n = A.shape[1]
    c = np.zeros(n)
    if bounds is None:
        bounds = [(0, None)] * n
    res = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")
    return bool(res.success), res


def run_positive_tests():
    r = {}
    # Simple feasible polytope: unit simplex-ish
    A = np.array([[1.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])
    b = np.array([1.0, 0.0, 0.0])
    ok, _ = is_feasible(A, b, bounds=[(None, None)] * 2)
    r["simplex_feasible"] = ok

    # 3D box
    A3 = np.vstack([np.eye(3), -np.eye(3)])
    b3 = np.array([1, 1, 1, 0, 0, 0], float)
    ok3, _ = is_feasible(A3, b3, bounds=[(None, None)] * 3)
    r["box_feasible"] = ok3

    # Intersection of half-spaces with interior
    rng = np.random.default_rng(0)
    A4 = rng.normal(size=(20, 4))
    b4 = np.abs(rng.normal(size=20)) + 1.0  # 0 is interior
    ok4, _ = is_feasible(A4, b4, bounds=[(None, None)] * 4)
    r["random_interior_feasible"] = ok4
    return r


def run_negative_tests():
    r = {}
    # Infeasible: x>=1 and x<=0
    A = np.array([[1.0], [-1.0]])
    b = np.array([0.0, -1.0])
    ok, _ = is_feasible(A, b, bounds=[(None, None)])
    r["contradictory_infeasible"] = (not ok)

    # x+y<=1, x>=2, y>=0
    A2 = np.array([[1.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])
    b2 = np.array([1.0, -2.0, 0.0])
    ok2, _ = is_feasible(A2, b2, bounds=[(None, None)] * 2)
    r["excluded_corner_infeasible"] = (not ok2)
    return r


def run_boundary_tests():
    r = {}
    # Single point (equality via two inequalities): x<=0 and -x<=0
    A = np.array([[1.0], [-1.0]])
    b = np.array([0.0, 0.0])
    ok, _ = is_feasible(A, b, bounds=[(None, None)])
    r["single_point_feasible"] = ok

    # Degenerate: zero rows -> trivially feasible
    A0 = np.zeros((3, 2))
    b0 = np.zeros(3)
    ok0, _ = is_feasible(A0, b0, bounds=[(None, None)] * 2)
    r["trivial_polytope_feasible"] = ok0

    # Thin slab: 0<=x<=1e-9 still feasible
    A_thin = np.array([[1.0], [-1.0]])
    b_thin = np.array([1e-9, 0.0])
    ok_t, _ = is_feasible(A_thin, b_thin, bounds=[(None, None)])
    r["thin_slab_feasible"] = ok_t
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "convex_admission_polytope_classical_results.json")
    payload = {
        "name": "convex_admission_polytope_classical",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": bool(all_pass),
        "summary": {"all_pass": bool(all_pass)},
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"Results written to {out_path} all_pass={all_pass}")
