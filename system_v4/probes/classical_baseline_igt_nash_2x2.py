#!/usr/bin/env python3
"""classical baseline igt nash 2x2

classical_baseline, numpy-only. Non-canon. Lane_B-eligible.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "numpy":    {"tried": True,  "used": True,  "reason": "load-bearing linear algebra / rng for classical baseline"},
    "pytorch":  {"tried": False, "used": False, "reason": "classical_baseline sim; torch not required"},
    "pyg":      {"tried": False, "used": False, "reason": "no graph-NN step in this baseline"},
    "z3":       {"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"},
    "cvc5":     {"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"},
    "sympy":    {"tried": False, "used": False, "reason": "numerical identity sufficient; symbolic not needed here"},
    "clifford": {"tried": False, "used": False, "reason": "matrix rep baseline; Cl(n) algebra deferred to canonical lane"},
    "geomstats":{"tried": False, "used": False, "reason": "flat/discrete baseline; manifold tooling out of scope"},
    "e3nn":     {"tried": False, "used": False, "reason": "no equivariant NN in baseline"},
    "rustworkx":{"tried": False, "used": False, "reason": "small adjacency handled by numpy"},
    "xgi":      {"tried": False, "used": False, "reason": "no hypergraph structure in this sim"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex in this sim"},
    "gudhi":    {"tried": False, "used": False, "reason": "no persistent homology in this sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None,
    "xgi": None, "toponetx": None, "gudhi": None,
}

NAME = "classical_baseline_igt_nash_2x2"

# Coordination game: payoffs for (A,B); pure Nash at (0,0) and (1,1).
PA = np.array([[2,0],[0,1]])
PB = np.array([[2,0],[0,1]])

def is_nash(i, j):
    # i is best response to j for A; j is best response to i for B
    a_ok = PA[i,j] >= PA[1-i, j]
    b_ok = PB[i,j] >= PB[i, 1-j]
    return bool(a_ok and b_ok)

def run_positive_tests():
    return {
        "nash_00": {"pass": is_nash(0,0)},
        "nash_11": {"pass": is_nash(1,1)},
    }

def run_negative_tests():
    return {
        "not_nash_01": {"pass": bool(not is_nash(0,1))},
        "not_nash_10": {"pass": bool(not is_nash(1,0))},
    }

def run_boundary_tests():
    # symmetry under swap
    return {"symmetric": {"pass": bool(np.array_equal(PA, PB))}}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        all(v.get("pass") for v in pos.values()) and
        all(v.get("pass") for v in neg.values()) and
        all(v.get("pass") for v in bnd.values())
    )
    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, NAME + "_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{NAME}: all_pass={all_pass} -> {out_path}")
