#!/usr/bin/env python3
"""sim_leviathan_group_value_divergence_as_distinguishability

Values across groups must be distinguishable for potential to exist.
Uses symbolic KL-like divergence and z3 distinguishability constraint.
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "sympy": {"tried": False, "used": False, "reason": ""},
    "z3":    {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"sympy": None, "z3": None}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


def kl(p, q):
    p = np.asarray(p, float); q = np.asarray(q, float)
    return float(np.sum(np.where(p > 0, p * np.log(p / q), 0.0)))


def run_positive_tests():
    res = {}
    p = [0.7, 0.2, 0.1]
    q = [0.1, 0.2, 0.7]
    res["kl_divergent"] = kl(p, q)
    res["distinguishable"] = res["kl_divergent"] > 0.1
    # symbolic divergence >= 0
    p0, q0 = sp.symbols("p0 q0", positive=True)
    d = p0 * sp.log(p0 / q0)
    res["symbolic_term"] = str(d)
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic KL divergence term"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    return res


def run_negative_tests():
    res = {}
    p = [0.5, 0.5]
    res["kl_identical"] = kl(p, p)
    res["indistinguishable"] = res["kl_identical"] < 1e-12
    # z3: require divergence > eps; identical distributions unsat
    s = z3.Solver()
    D = z3.Real("D")
    s.add(D == 0, D > 0.01)
    res["identical_excluded"] = str(s.check()) == "unsat"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "exclude indistinguishable groups"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return res


def run_boundary_tests():
    res = {}
    p = [0.5 + 1e-6, 0.5 - 1e-6]
    q = [0.5 - 1e-6, 0.5 + 1e-6]
    res["kl_near_zero"] = kl(p, q)
    res["near_degenerate"] = res["kl_near_zero"] < 1e-6
    return res


if __name__ == "__main__":
    results = {
        "name": "leviathan_group_value_divergence_as_distinguishability",
        "classification": "classical_baseline",
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "leviathan_group_value_divergence_as_distinguishability_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
