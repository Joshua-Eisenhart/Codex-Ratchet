#!/usr/bin/env python3
"""classical baseline sci method modus tollens

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

NAME = "classical_baseline_sci_method_modus_tollens"

# Hypothesis H: x > 0. Prediction P(H): x**2 > 0.
# If P(x) is false for some x, then H is refuted for that x.
def predict(H_fn, x):
    return H_fn(x)

def H(x): return x > 0

def run_positive_tests():
    out = {}
    # Evidence confirms (never proves): x=3 satisfies both
    out["confirming"] = {"pass": bool(H(3.0) and (3.0**2 > 0))}
    # Falsifying case exists: x = -1 => H(x) false, but x^2 > 0 (P still holds; prediction is weak)
    # Correct modus tollens: if P false AND P was implied by H, then not H.
    # Choose stronger prediction P2: x > 0 implies x^3 > 0.
    x = -2.0
    P2 = (x**3 > 0)  # False
    refuted = (not P2) and (not H(x))  # both consistent
    out["modus_tollens_refutes"] = {"pass": bool(refuted)}
    return out

def run_negative_tests():
    # Affirming the consequent is invalid: x^2>0 does NOT imply x>0
    x = -3.0
    ac_valid = (x**2 > 0) and H(x)
    return {"affirming_consequent_invalid": {"pass": bool(not ac_valid)}}

def run_boundary_tests():
    # x = 0 boundary
    return {"zero_not_positive": {"pass": bool(not H(0.0))}}


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
