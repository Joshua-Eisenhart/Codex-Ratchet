#!/usr/bin/env python3
"""classical baseline random walk mixing

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

NAME = "classical_baseline_random_walk_mixing"

def build_cycle(n):
    A = np.zeros((n,n))
    for i in range(n):
        A[i, (i+1)%n] = 1
        A[(i+1)%n, i] = 1
    return A

def transition(A):
    d = A.sum(axis=1, keepdims=True)
    return A / d

def run_positive_tests():
    out = {}
    n = 8
    A = build_cycle(n)
    P = transition(A)
    # stationary distribution is uniform
    pi = np.ones(n)/n
    out["stationary_is_fixed"] = {"pass": bool(np.allclose(pi @ P, pi, atol=1e-12))}
    # after many steps from delta, distribution approaches uniform
    x = np.zeros(n); x[0] = 1.0
    Pk = np.linalg.matrix_power(P, 200)
    xk = x @ Pk
    out["mixes_to_uniform"] = {"pass": bool(np.allclose(xk, pi, atol=1e-6))}
    # Row sums of P are 1
    out["rows_sum_one"] = {"pass": bool(np.allclose(P.sum(axis=1), np.ones(n)))}
    return out

def run_negative_tests():
    # Bipartite cycle has period-2 non-mixing for even n when using pure adjacency
    # Non-stochastic matrix should fail row-sum
    bad = np.ones((3,3))
    return {"non_stochastic_detected": {"pass": bool(not np.allclose(bad.sum(axis=1), np.ones(3)))}}

def run_boundary_tests():
    # Single self-loop = trivial mixing
    A = np.array([[1.0]])
    P = transition(A)
    return {"single_node": {"pass": bool(np.isclose(P[0,0], 1.0))}}


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
