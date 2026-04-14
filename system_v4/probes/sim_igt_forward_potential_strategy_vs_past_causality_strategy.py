#!/usr/bin/env python3
"""
sim_igt_forward_potential_strategy_vs_past_causality_strategy -- orientation
test. A forward-potential strategy conditions on future admissibility; a
past-causality strategy conditions on prior outcomes. The two disagree
when the short-horizon signal inverts the long-horizon attractor.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "scalar decisions"},
    "pyg":       {"tried": False, "used": False, "reason": "no graph"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "z3 suffices"},
    "sympy":     {"tried": False, "used": False, "reason": "discrete enumeration"},
    "clifford":  {"tried": False, "used": False, "reason": "no rotors"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi":       {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx":  {"tried": False, "used": False, "reason": "no complex"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from z3 import Int, Solver, And, Or, sat, Sum
    TOOL_MANIFEST["z3"]["tried"] = True
except Exception:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


def past_causality_choice(history):
    """Repeat the last outcome sign; +0 if empty."""
    return np.sign(history[-1]) if history else 0


def forward_potential_choice(remaining_future_potential):
    """Choose sign that maximizes admissibility of long-horizon attractor."""
    return np.sign(remaining_future_potential)


def run_positive_tests():
    r = {}
    history = [-1, -1]
    future_potential = +3  # favorable long-horizon
    past = int(past_causality_choice(history))
    forward = int(forward_potential_choice(future_potential))
    r["orientations_disagree"] = {"past": past, "forward": forward, "ok": past != forward}

    # z3: exists history and future where signs disagree
    h, f = Int("h"), Int("f")
    s = Solver()
    s.add(Or(h == -1, h == +1))
    s.add(Or(f == -3, f == +3))
    s.add(h * f < 0)  # opposite signs
    r["z3_disagreement_exists"] = {"ok": s.check() == sat}
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "SAT witness: past and forward orientations can disagree"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


def run_negative_tests():
    r = {}
    # When history sign matches future potential sign, they agree
    history = [+1]; future = +2
    r["agree_when_aligned"] = {
        "ok": past_causality_choice(history) == forward_potential_choice(future)
    }
    # z3: if h == +1 and f == +3 then h*f > 0 (cannot be <0)
    h, f = Int("h"), Int("f")
    s = Solver(); s.add(h == 1, f == 3, h * f < 0)
    unsat = s.check() != sat
    r["z3_aligned_no_disagreement"] = {"ok": unsat}
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


def run_boundary_tests():
    r = {}
    # Empty history -> past strategy has no opinion (returns 0)
    r["empty_history"] = {"ok": past_causality_choice([]) == 0}
    # Zero future potential -> forward strategy is indifferent
    r["zero_future"] = {"ok": forward_potential_choice(0) == 0}
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_igt_forward_potential_strategy_vs_past_causality_strategy",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    results["all_ok"] = all(results[k]["ok"] for k in ("positive", "negative", "boundary"))
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_igt_forward_potential_strategy_vs_past_causality_strategy_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}; all_ok={results['all_ok']}")
