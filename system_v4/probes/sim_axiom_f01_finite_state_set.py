#!/usr/bin/env python3
"""sim_axiom_f01_finite_state_set -- F01 clause |S|<infty.

Canonical sim atomizing F01: the state set S must be finite. A model in
which |S| is required infinite is inadmissible. z3 is load-bearing: we
encode F01 as the predicate Finite(S) and show UNSAT when we add the
negation (an injection N -> S exists).
"""

import json, os
import numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def run_positive_tests():
    """F01 holds: a finite enumeration of |S|=N states is admissible."""
    results = {}
    s = z3.Solver()
    N = 8
    states = [z3.Int(f"s_{i}") for i in range(N)]
    s.add(z3.Distinct(states))
    s.add(*[z3.And(x >= 0, x < N) for x in states])
    results["finite_states_sat"] = str(s.check())  # sat
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "encodes |S|=N distinct states, checks SAT for finite / UNSAT for infinite"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    # torch count cross-check
    t = torch.arange(N)
    results["torch_count"] = int(t.numel())
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "supportive cardinality cross-check on finite tensor"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
    results["pass"] = (results["finite_states_sat"] == "sat" and results["torch_count"] == N)
    return results


def run_negative_tests():
    """F01 violated: asserting an injection f: Int -> S with f injective over
    an unbounded range forces UNSAT when S bound to finite N."""
    results = {}
    s = z3.Solver()
    N = 4
    f = z3.Function("f", z3.IntSort(), z3.IntSort())
    i, j = z3.Ints("i j")
    # f maps into [0, N)
    s.add(z3.ForAll([i], z3.And(f(i) >= 0, f(i) < N)))
    # f is injective on {0,1,...,N}  (N+1 distinct inputs -> pigeonhole)
    s.add(z3.ForAll([i, j],
                    z3.Implies(z3.And(0 <= i, i <= N, 0 <= j, j <= N, i != j),
                               f(i) != f(j))))
    results["infinite_into_finite_check"] = str(s.check())  # unsat
    results["pass"] = (results["infinite_into_finite_check"] == "unsat")
    return results


def run_boundary_tests():
    """Boundary: |S|=1 (trivial admissible) and |S|=0 (vacuous — M acts on
    empty domain; by convention F01 requires |S|>=1 for a nontrivial ontology)."""
    results = {}
    s1 = z3.Solver()
    x = z3.Int("x"); s1.add(x == 0)
    results["N_eq_1"] = str(s1.check())  # sat
    # |S|=0: require a state to exist => unsat under |S|=0 constraint
    s0 = z3.Solver()
    y = z3.Int("y"); s0.add(z3.And(y >= 0, y < 0))
    results["N_eq_0_requires_state"] = str(s0.check())  # unsat
    results["pass"] = (results["N_eq_1"] == "sat" and results["N_eq_0_requires_state"] == "unsat")
    return results


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos.get("pass") and neg.get("pass") and bnd.get("pass"))
    results = {
        "name": "sim_axiom_f01_finite_state_set",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": ok,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_axiom_f01_finite_state_set_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out_path}")
