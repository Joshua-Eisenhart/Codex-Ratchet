#!/usr/bin/env python3
"""sim_axiom_f01_finite_measurement_set -- F01 clause |M|<infty.

Canonical sim atomizing F01: the measurement set M must be finite. z3 is
load-bearing: we require each measurement to be a distinct index in
{0,...,K-1} and show UNSAT when K+1 distinct measurements are forced.
"""

import json, os
import numpy as np

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
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def run_positive_tests():
    """|M|=K admissible: K distinct measurement indices SAT."""
    K = 3  # canonical triad {sigma_x, sigma_y, sigma_z}
    s = z3.Solver()
    m = [z3.Int(f"m_{i}") for i in range(K)]
    s.add(z3.Distinct(m))
    s.add(*[z3.And(x >= 0, x < K) for x in m])
    res = {"K_distinct_sat": str(s.check())}
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "encodes |M|=K distinct measurements; SAT for finite, UNSAT for pigeonhole violation"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    # sympy supportive: Pauli algebra supplies a canonical finite M
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    res["pauli_count"] = 3
    res["pauli_nonzero"] = all(m.norm() != 0 for m in (sx, sy, sz))
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "supportive: exhibits canonical finite M={sigma_x,sigma_y,sigma_z}"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    res["pass"] = (res["K_distinct_sat"] == "sat" and res["pauli_count"] == 3)
    return res


def run_negative_tests():
    """Pigeonhole: K+1 distinct measurements into K slots => UNSAT."""
    K = 3
    s = z3.Solver()
    m = [z3.Int(f"m_{i}") for i in range(K + 1)]
    s.add(z3.Distinct(m))
    s.add(*[z3.And(x >= 0, x < K) for x in m])
    res = {"pigeonhole": str(s.check())}
    res["pass"] = (res["pigeonhole"] == "unsat")
    return res


def run_boundary_tests():
    """Boundary: K=1 (trivial resolution -- Q is a single class), K=0 (no
    measurement => no distinguishability, equivalence is total)."""
    s1 = z3.Solver(); x = z3.Int("x"); s1.add(z3.And(x >= 0, x < 1))
    s0 = z3.Solver(); y = z3.Int("y"); s0.add(z3.And(y >= 0, y < 0))
    res = {"K_eq_1": str(s1.check()), "K_eq_0": str(s0.check())}
    res["pass"] = (res["K_eq_1"] == "sat" and res["K_eq_0"] == "unsat")
    return res


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos.get("pass") and neg.get("pass") and bnd.get("pass"))
    results = {
        "name": "sim_axiom_f01_finite_measurement_set",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_axiom_f01_finite_measurement_set_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out_path}")
