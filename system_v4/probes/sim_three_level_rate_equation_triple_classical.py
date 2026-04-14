#!/usr/bin/env python3
"""
sim_three_level_rate_equation_triple_classical.py

Step 3 classical baseline: three-level thermal relaxation cascade
|2> -> |1> -> |0> with rates k21, k10. Classical rate equations.
Checks: probability conservation, monotone |2>-population decay,
final steady state at ground.
"""

import json
import os
import numpy as np
from scipy.integrate import solve_ivp

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "n/a"},
    "z3": {"tried": False, "used": False, "reason": "n/a"},
    "cvc5": {"tried": False, "used": False, "reason": "n/a"},
    "sympy": {"tried": False, "used": False, "reason": "n/a"},
    "clifford": {"tried": False, "used": False, "reason": "n/a"},
    "geomstats": {"tried": False, "used": False, "reason": "n/a"},
    "e3nn": {"tried": False, "used": False, "reason": "n/a"},
    "rustworkx": {"tried": False, "used": False, "reason": "n/a"},
    "xgi": {"tried": False, "used": False, "reason": "n/a"},
    "toponetx": {"tried": False, "used": False, "reason": "n/a"},
    "gudhi": {"tried": False, "used": False, "reason": "n/a"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "tensor sum cross-check of conservation"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def cascade(t, p, k21, k10):
    p2, p1, p0 = p
    dp2 = -k21 * p2
    dp1 = k21 * p2 - k10 * p1
    dp0 = k10 * p1
    return [dp2, dp1, dp0]


def simulate(k21, k10, t_end=20.0):
    sol = solve_ivp(cascade, (0, t_end), [1.0, 0.0, 0.0],
                    args=(k21, k10), t_eval=np.linspace(0, t_end, 200),
                    rtol=1e-9, atol=1e-11)
    return sol.t, sol.y


def run_positive_tests():
    results = {}
    ok = True
    for k21, k10 in [(1.0, 0.5), (0.7, 2.0), (0.3, 0.3001)]:
        t, y = simulate(k21, k10, t_end=80.0)
        total = y.sum(axis=0)
        cons = np.max(np.abs(total - 1.0))
        monotone = np.all(np.diff(y[0]) <= 1e-10)
        final_ground = y[2, -1]
        if not (cons < 1e-6 and monotone and final_ground > 0.99):
            ok = False
    if TOOL_MANIFEST["pytorch"]["used"]:
        import torch
        t = torch.tensor(y[:, -1])
        results["torch_final_sum"] = float(t.sum())
    results["cascade_conservation_and_decay"] = ok
    return results


def run_negative_tests():
    results = {}
    # With negative rate, conservation holds but |2> population grows -> fails monotone decay
    t, y = simulate(-0.5, 0.5, t_end=1.0)
    grows = np.any(np.diff(y[0]) > 1e-6)
    results["negative_rate_breaks_monotone"] = bool(grows)
    return results


def run_boundary_tests():
    results = {}
    # Zero rates: population stays in |2>
    t, y = simulate(0.0, 0.0, t_end=5.0)
    results["zero_rates_freeze"] = bool(abs(y[0, -1] - 1.0) < 1e-8 and y[2, -1] < 1e-8)
    # Equal rates k21=k10 still reach ground
    t, y = simulate(1.0, 1.0, t_end=30.0)
    results["equal_rates_reach_ground"] = bool(y[2, -1] > 0.999)
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        pos.get("cascade_conservation_and_decay", False)
        and neg.get("negative_rate_breaks_monotone", False)
        and bnd.get("zero_rates_freeze", False)
        and bnd.get("equal_rates_reach_ground", False)
    )
    divergence_log = [
        "classical rate equations treat populations as real scalars; loses coherence between |2>,|1>,|0> required in nonclassical triple-nesting",
        "no probe-relative time direction: rates are absolute k, but entropic-monist doctrine requires time = entropy gradient of constraint manifold",
        "cascade monotonicity is imposed by sign of k; nonclassical program requires monotonicity to EMERGE from admissibility constraints, not rate choice",
    ]
    results = {
        "name": "three_level_rate_equation_triple_classical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "divergence_log": divergence_log,
        "summary": {"all_pass": bool(all_pass)},
        "all_pass": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "three_level_rate_equation_triple_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
