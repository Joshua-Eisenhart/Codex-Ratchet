#!/usr/bin/env python3
"""
sim_capability_evotorch_isolated.py -- Isolated capability probe for evotorch.

Classical_baseline capability probe: exercises evotorch SNES minimizing a
4D quadratic ||x||^2. In isolation per the four-sim-kinds doctrine; pays
down the 2026-04-14 discipline-debt entry for evolutionary tools.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates the evotorch SNES optimizer in isolation; "
    "cross-tool integration is deferred to a separate integration sim per the "
    "four-sim-kinds doctrine (capability probe must precede integration sim)."
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
# NOTE: evotorch uses pytorch as a dependency to represent tensors, but this
# probe does not exercise pytorch as a separately-tested tool; the quadratic
# objective is trivially evaluable without autograd or any torch-specific API.

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

EVO_OK = False
EVO_VERSION = None
try:
    import torch
    import evotorch
    from evotorch import Problem
    from evotorch.algorithms import SNES
    EVO_OK = True
    EVO_VERSION = getattr(evotorch, "__version__", "unknown")
except Exception as exc:
    _evo_exc = exc


def _make_problem():
    def sphere(x: "torch.Tensor") -> "torch.Tensor":
        return (x ** 2).sum(dim=-1)
    return Problem(
        "min",
        sphere,
        solution_length=4,
        initial_bounds=(-5.0, 5.0),
        vectorized=True,
    )


def run_positive_tests():
    r = {}
    if not EVO_OK:
        r["evotorch_available"] = {"pass": False, "detail": f"evotorch missing: {_evo_exc}"}
        return r
    r["evotorch_available"] = {"pass": True, "version": EVO_VERSION}

    torch.manual_seed(0)
    problem = _make_problem()
    algo = SNES(problem, popsize=20, stdev_init=2.0)
    algo.run(num_generations=50)
    best = algo.status["best"].evals.item()
    r["snes_minimizes_sphere"] = {
        "pass": best < 0.5,
        "best_eval": float(best),
    }
    return r


def run_negative_tests():
    r = {}
    if not EVO_OK:
        r["skip"] = {"pass": False, "detail": "evotorch missing"}
        return r
    problem = _make_problem()
    raised = False
    try:
        # Bad popsize: -1 causes a negative-dimension RuntimeError when run() is
        # called; construction itself does not validate (evotorch defers validation
        # to the first tensor allocation during the run step).
        algo = SNES(problem, popsize=-1, stdev_init=1.0)
        algo.run(num_generations=1)
    except Exception:
        raised = True
    r["bad_popsize_raises"] = {"pass": raised}
    return r


def run_boundary_tests():
    r = {}
    if not EVO_OK:
        r["skip"] = {"pass": False, "detail": "evotorch missing"}
        return r
    torch.manual_seed(1)
    problem = _make_problem()
    algo = SNES(problem, popsize=8, stdev_init=1.0)
    # Zero-step run: status initialized, no regression occurred.
    algo.run(num_generations=0)
    # Must not crash; status may have 'best' after init evals or be empty.
    has_center = "center" in algo.status
    r["zero_step_run_stable"] = {"pass": has_center}
    return r


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    def _all_pass(d):
        return all(v.get("pass", False) for v in d.values()) if d else False

    overall_pass = _all_pass(positive) and _all_pass(negative) and _all_pass(boundary)

    results = {
        "name": "sim_capability_evotorch_isolated",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "target_tool": {"name": "evotorch", "version": EVO_VERSION, "integration": "load_bearing"},
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
        "capability_summary": {
            "can": "SNES drives a 4D sphere objective below 0.5 within 50 "
                   "generations at popsize=20 on CPU tensors; raises on negative "
                   "popsize at run time and survives a zero-generation run.",
            "cannot": "Does not by itself pick a step-size schedule; stdev_init "
                      "must be chosen problem-aware or convergence stalls.",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_evotorch_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{'PASS' if overall_pass else 'FAIL'}] {out_path}")
