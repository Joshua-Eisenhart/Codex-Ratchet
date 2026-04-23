#!/usr/bin/env python3
"""
sim_pymoo_nsga2_pareto_admissibility.py

Canonical sim. NSGA-II (pymoo) two-objective search over a small
admissible/forbidden region. Objectives: minimize constraint violation
(distance into forbidden ball) and minimize complexity (L1 norm of
decision vector). Exclusion language: candidates that minimize violation
survive; the forbidden interior excludes them.
"""

import json
import os
import numpy as np

TOOL_MANIFEST = {
    "pymoo": {"tried": False, "used": False, "reason": ""},
    "numpy": {"tried": True, "used": True, "reason": "objective arithmetic and hypervolume indicator"},
}
TOOL_INTEGRATION_DEPTH = {"pymoo": None, "numpy": "supportive"}

try:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.optimize import minimize
    from pymoo.indicators.hv import HV
    TOOL_MANIFEST["pymoo"]["tried"] = True
    TOOL_MANIFEST["pymoo"]["used"] = True
    TOOL_MANIFEST["pymoo"]["reason"] = "NSGA-II evolutionary search of Pareto front over admissibility/complexity objectives"
    TOOL_INTEGRATION_DEPTH["pymoo"] = "load_bearing"
    PYMOO_OK = True
except ImportError as e:
    TOOL_MANIFEST["pymoo"]["reason"] = f"not installed: {e}"
    PYMOO_OK = False


# Forbidden ball: center=(0.5,0.5,0.5,0.5), radius=0.25. Candidates inside are excluded.
FORBIDDEN_CENTER = np.array([0.5, 0.5, 0.5, 0.5])
FORBIDDEN_RADIUS = 0.25


def violation(x):
    d = np.linalg.norm(x - FORBIDDEN_CENTER)
    return max(0.0, FORBIDDEN_RADIUS - d)  # positive inside the forbidden ball


def complexity(x):
    # "Complexity" = distance from the forbidden-ball center. Conflicting with
    # violation: low complexity (close to center) -> high violation (deep in
    # forbidden interior). High complexity (far) -> zero violation.
    return float(np.linalg.norm(x - FORBIDDEN_CENTER))


if PYMOO_OK:
    class AdmissibilityProblem(ElementwiseProblem):
        def __init__(self):
            super().__init__(n_var=4, n_obj=2, n_constr=0, xl=-1.0, xu=1.0)

        def _evaluate(self, x, out, *args, **kwargs):
            out["F"] = [violation(x), complexity(x)]


def run_positive_tests():
    if not PYMOO_OK:
        return {"pymoo_available": False}
    problem = AdmissibilityProblem()
    algo = NSGA2(pop_size=40)
    res = minimize(problem, algo, ("n_gen", 40), seed=1, verbose=False)
    F = res.F
    ref = np.array([1.0, 3.5])
    hv = float(HV(ref_point=ref).do(F))
    pareto_size = int(F.shape[0])
    return {
        "pareto_front_size": pareto_size,
        "hypervolume": hv,
        "pareto_size_ge_3": pareto_size >= 3,
        "hypervolume_positive": hv > 0.0,
        "surviving_min_violation": float(F[:, 0].min()),
    }


def run_negative_tests():
    # Negative: a candidate inside the forbidden ball is excluded (violation>0).
    inside = FORBIDDEN_CENTER.copy()
    v = violation(inside)
    return {"interior_excluded": v > 0, "interior_violation": float(v)}


def run_boundary_tests():
    # Boundary: exactly on the forbidden-ball surface -> violation == 0 (admissible edge).
    on_surface = FORBIDDEN_CENTER + np.array([FORBIDDEN_RADIUS, 0, 0, 0])
    v = violation(on_surface)
    return {"on_surface_violation": float(v), "surface_admissible": v <= 1e-12}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    passed = (
        PYMOO_OK
        and pos.get("pareto_size_ge_3", False)
        and pos.get("hypervolume_positive", False)
        and neg.get("interior_excluded", False)
        and bnd.get("surface_admissible", False)
    )
    results = {
        "name": "sim_pymoo_nsga2_pareto_admissibility",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "passed": bool(passed),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_pymoo_nsga2_pareto_admissibility_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={passed} -> {out_path}")
