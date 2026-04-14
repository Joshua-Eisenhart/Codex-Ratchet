#!/usr/bin/env python3
"""classical baseline fep predictive coding

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

NAME = "classical_baseline_fep_predictive_coding"

def run_positive_tests():
    rng = np.random.default_rng(0)
    out = {}
    # Observations y = W x + noise; infer x by least squares
    W = rng.standard_normal((8, 4))
    x_true = rng.standard_normal(4)
    y = W @ x_true + 0.01*rng.standard_normal(8)
    x_hat, *_ = np.linalg.lstsq(W, y, rcond=None)
    out["residual_small"] = {"pass": bool(np.linalg.norm(W@x_hat - y) < 0.2)}
    out["estimate_close"] = {"pass": bool(np.linalg.norm(x_hat - x_true) < 0.2)}
    return out

def run_negative_tests():
    rng = np.random.default_rng(1)
    W = rng.standard_normal((8,4))
    y = rng.standard_normal(8)
    x_zero = np.zeros(4)
    r_zero = np.linalg.norm(W@x_zero - y)
    x_hat, *_ = np.linalg.lstsq(W, y, rcond=None)
    r_opt = np.linalg.norm(W@x_hat - y)
    return {"zero_worse_than_lstsq": {"pass": bool(r_zero >= r_opt - 1e-10)}}

def run_boundary_tests():
    # Square invertible: residual exactly 0
    W = np.eye(3)
    y = np.array([1.0, -2.0, 3.0])
    x_hat, *_ = np.linalg.lstsq(W, y, rcond=None)
    return {"invertible_zero_residual": {"pass": bool(np.allclose(W@x_hat, y, atol=1e-12))}}


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
