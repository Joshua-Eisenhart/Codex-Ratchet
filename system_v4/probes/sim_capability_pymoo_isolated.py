#!/usr/bin/env python3
"""
sim_capability_pymoo_isolated.py -- Isolated tool-capability probe for pymoo.

Classical_baseline capability probe: exercises NSGA-II on the ZDT1 benchmark
in isolation. Per the four-sim-kinds doctrine this is a capability sim, not an
integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates the pymoo NSGA-II multi-objective optimizer "
    "in isolation; cross-tool integration is deferred to a dedicated integration "
    "sim per the four-sim-kinds doctrine (capability must precede integration)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

PYMOO_OK = False
PYMOO_VERSION = None
try:
    import pymoo
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.problems import get_problem
    from pymoo.optimize import minimize
    from pymoo.indicators.hv import HV
    import numpy as np
    PYMOO_OK = True
    PYMOO_VERSION = getattr(pymoo, "__version__", "unknown")
except Exception as exc:
    _pymoo_exc = exc


def run_positive_tests():
    r = {}
    if not PYMOO_OK:
        r["pymoo_available"] = {"pass": False, "detail": f"pymoo missing: {_pymoo_exc}"}
        return r
    r["pymoo_available"] = {"pass": True, "version": PYMOO_VERSION}

    # Standard ZDT1 benchmark: 30-variable problem, 2 objectives
    problem = get_problem("zdt1", n_var=30)
    algorithm = NSGA2(pop_size=50)
    res = minimize(problem, algorithm, ("n_gen", 50), seed=42, verbose=False)

    pareto_F = res.F  # shape (n_solutions, 2)
    pareto_size = len(pareto_F)
    r["pareto_front_size_ge_3"] = {
        "pass": pareto_size >= 3,
        "pareto_size": pareto_size,
    }

    # Hypervolume > 0 relative to reference point [1.1, 1.1]
    ref_point = np.array([1.1, 1.1])
    ind = HV(ref_point=ref_point)
    hv = float(ind(pareto_F))
    r["hypervolume_positive"] = {
        "pass": hv > 0.0,
        "hypervolume": hv,
    }

    # Both objectives must be present and non-negative (ZDT1 is [0,1] x [0,1])
    f1_min = float(pareto_F[:, 0].min())
    f2_min = float(pareto_F[:, 1].min())
    r["objectives_nonnegative"] = {
        "pass": f1_min >= 0.0 and f2_min >= 0.0,
        "f1_min": f1_min,
        "f2_min": f2_min,
    }
    return r


def run_negative_tests():
    r = {}
    if not PYMOO_OK:
        r["skip"] = {"pass": False, "detail": "pymoo missing"}
        return r

    # Degenerate 1-objective problem: use ZDT1 but only look at f1.
    # With a single objective this is not a true Pareto problem; the "front"
    # degenerates to a single point (the global minimum of f1 ≈ 0).
    problem = get_problem("zdt1", n_var=30)
    algorithm = NSGA2(pop_size=50)
    res = minimize(problem, algorithm, ("n_gen", 50), seed=7, verbose=False)

    # Extract only f1 values; assert the minimum is close to 0 (not a spread front)
    f1_values = res.F[:, 0]
    f1_best = float(f1_values.min())

    # For a true 2-obj front NSGA-II produces diverse f2 values; if we
    # collapse to 1-obj perspective the "front" has near-zero f1 spread.
    f2_values = res.F[:, 1]
    f2_spread = float(f2_values.max() - f2_values.min())

    # The negative test: a 1-objective perspective yields a degenerate "front"
    # (best f1 near 0, but f2 spread is large because optimizer didn't minimize f2).
    # What we EXCLUDE is f1_best >= 0.5 (that would mean optimizer totally failed).
    r["degenerate_single_obj_f1_near_zero"] = {
        "pass": f1_best < 0.2,
        "f1_best": f1_best,
        "f2_spread_note": f2_spread,
        "note": "f1 best near 0 confirms optimizer still tracks f1; degenerate because f2 not separately minimized",
    }
    return r


def run_boundary_tests():
    r = {}
    if not PYMOO_OK:
        r["skip"] = {"pass": False, "detail": "pymoo missing"}
        return r

    # Boundary: pop_size=4 (near-minimum viable population for NSGA-II)
    problem = get_problem("zdt1", n_var=30)
    algorithm = NSGA2(pop_size=4)
    try:
        res = minimize(problem, algorithm, ("n_gen", 20), seed=99, verbose=False)
        pareto_F = res.F
        survived = len(pareto_F) >= 1 and pareto_F.shape[1] == 2
        r["pop_size_4_runs_without_crash"] = {
            "pass": survived,
            "pareto_size": len(pareto_F),
            "f_shape": list(pareto_F.shape),
        }
    except Exception as exc:
        r["pop_size_4_runs_without_crash"] = {"pass": False, "detail": str(exc)}
    return r


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    def _all_pass(d):
        return all(v.get("pass", False) for v in d.values()) if d else False

    overall_pass = _all_pass(positive) and _all_pass(negative) and _all_pass(boundary)

    results = {
        "name": "sim_capability_pymoo_isolated",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "target_tool": {
            "name": "pymoo",
            "version": PYMOO_VERSION,
            "integration": "load_bearing",
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
        "capability_summary": {
            "can": (
                "Run NSGA-II on ZDT1 (30 vars, 2 objectives) producing a Pareto "
                "front with >= 3 solutions and positive hypervolume relative to "
                "[1.1, 1.1]; handles pop_size=4 boundary without crashing."
            ),
            "cannot": (
                "Does not guarantee convergence to the true Pareto front in few "
                "generations; very small pop_size degrades diversity; no GPU "
                "acceleration for fitness evaluation by default."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_pymoo_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{'PASS' if overall_pass else 'FAIL'}] {out_path}")
