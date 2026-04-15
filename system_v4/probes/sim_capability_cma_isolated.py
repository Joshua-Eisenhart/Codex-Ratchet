#!/usr/bin/env python3
"""
sim_capability_cma_isolated.py
CMA-ES (Covariance Matrix Adaptation Evolution Strategy) isolated capability probe.
Isolates and characterizes black-box evolutionary optimization via the cma library.
classification = "classical_baseline"
"""

import json
import math
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- 12 standard tools, all not-used (isolation probe)
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; coupling with tensor computation tools deferred to a dedicated integration sim per four-sim-kinds doctrine"},
    "pyg":       {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; graph-neural integration deferred to a dedicated integration sim per four-sim-kinds doctrine"},
    "z3":        {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; constraint satisfaction is a separate concern addressed by a dedicated integration sim per four-sim-kinds doctrine"},
    "cvc5":      {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; formal verification is a separate concern addressed by a dedicated integration sim per four-sim-kinds doctrine"},
    "sympy":     {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; symbolic gradient analysis deferred to a dedicated integration sim per four-sim-kinds doctrine"},
    "clifford":  {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; geometric algebra coupling deferred to a dedicated integration sim per four-sim-kinds doctrine"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; Riemannian geometry coupling deferred to a dedicated integration sim per four-sim-kinds doctrine"},
    "e3nn":      {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; equivariant network coupling deferred to a dedicated integration sim per four-sim-kinds doctrine"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; graph algorithm coupling deferred to a dedicated integration sim per four-sim-kinds doctrine"},
    "xgi":       {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; hypergraph coupling deferred to a dedicated integration sim per four-sim-kinds doctrine"},
    "toponetx":  {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; topological complex coupling deferred to a dedicated integration sim per four-sim-kinds doctrine"},
    "gudhi":     {"tried": False, "used": False, "reason": "not used: this probe isolates CMA-ES evolutionary strategy capability; persistent homology coupling deferred to a dedicated integration sim per four-sim-kinds doctrine"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

TARGET_TOOL = {
    "name": "cma",
    "import": "import cma; cma.fmin2",
    "role": "load_bearing",
    "can": [
        "black-box optimization without gradients using covariance matrix adaptation",
        "adapts its search distribution covariance to the landscape curvature automatically",
        "handles moderate-dimensional continuous optimization effectively up to ~100D",
        "restarts and sigma adaptation make it robust to ill-conditioned landscapes",
    ],
    "cannot": [
        "handle discrete or combinatorial variables natively without encoding tricks",
        "guarantee finding the global optimum on multimodal landscapes",
        "replace z3 or cvc5 for symbolic constraint satisfaction or formal proof",
        "exploit gradient information even when available (purely black-box)",
    ],
}

import cma


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # Positive 1: minimize quadratic f(x) = sum((x - target)^2) in 3D
    target = np.array([1.0, 2.0, 3.0])

    def quadratic(x):
        return float(np.sum((np.array(x) - target) ** 2))

    x0 = [0.0, 0.0, 0.0]
    xbest, es = cma.fmin2(
        quadratic, x0, 0.5,
        options={"maxiter": 200, "verbose": -9, "seed": 42}
    )
    best_val = es.result.fbest
    dist_to_target = float(np.linalg.norm(np.array(xbest) - target))

    pass_close = dist_to_target < 0.1
    pass_val = best_val < 0.01

    results["positive_3d_quadratic"] = {
        "target": target.tolist(),
        "x_best": [float(v) for v in xbest],
        "fbest": float(best_val),
        "dist_to_target": float(dist_to_target),
        "pass_close_to_target": pass_close,
        "pass_low_value": pass_val,
        "pass": pass_close and pass_val,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # Negative: Rastrigin function has many local minima
    # CMA-ES may get trapped; we document this as expected behavior
    def rastrigin(x):
        x = np.array(x)
        n = len(x)
        return float(10 * n + np.sum(x ** 2 - 10 * np.cos(2 * math.pi * x)))

    x0 = [2.5, 2.5, 2.5]  # start away from global optimum at [0,0,0]
    xbest, es = cma.fmin2(
        rastrigin, x0, 0.5,
        options={"maxiter": 300, "verbose": -9, "seed": 7}
    )
    best_val = float(es.result.fbest)
    global_opt = 0.0  # Rastrigin global min = 0 at origin

    # Expected: may NOT find global min; fbest > 0 is acceptable (local trap)
    # Pass criterion: CMA ran without error and returned a finite value
    ran_without_error = math.isfinite(best_val)
    # Document whether it found global min or got trapped
    found_global = best_val < 0.1

    results["negative_rastrigin_local_trap"] = {
        "x_best": [float(v) for v in xbest],
        "fbest": float(best_val),
        "global_optimum": global_opt,
        "found_global_optimum": found_global,
        "ran_without_error": ran_without_error,
        "note": "CMA-ES may be trapped in local minimum on Rastrigin; fbest > 0 is expected and acceptable",
        "pass": ran_without_error,  # pass = ran cleanly, not that global was found
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # Boundary: 1D optimization (scalar wrapped in list)
    def f1d(x):
        return float((x[0] - 5.0) ** 2)

    x0_1d = [0.0]
    xbest_1d, es_1d = cma.fmin2(
        f1d, x0_1d, 0.5,
        options={"maxiter": 200, "verbose": -9, "seed": 1}
    )
    best_1d = float(es_1d.result.fbest)
    dist_1d = abs(xbest_1d[0] - 5.0)

    pass_1d = dist_1d < 0.1

    results["boundary_1d_scalar"] = {
        "x_best": float(xbest_1d[0]),
        "fbest": float(best_1d),
        "target": 5.0,
        "dist_to_target": float(dist_1d),
        "pass_close": pass_1d,
        "pass": pass_1d,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = (
        pos["positive_3d_quadratic"]["pass"]
        and neg["negative_rastrigin_local_trap"]["pass"]
        and bnd["boundary_1d_scalar"]["pass"]
    )

    results = {
        "name": "sim_capability_cma_isolated",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "target_tool": TARGET_TOOL,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_cma_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {all_pass}")
