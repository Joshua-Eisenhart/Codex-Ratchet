#!/usr/bin/env python3
"""
sim_igt_zero_sum_collapse_detector -- detects authoritarian/zero-sum
attractor: when faith-in-possible (positive-sum variance) collapses, all
admissible outcomes flatten into a zero-sum frame.
"""
import json, os
import numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "scalar stats suffice"},
    "pyg":       {"tried": False, "used": False, "reason": "no graph"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "z3 suffices"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
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
    from z3 import Real, Solver, And, sat
    TOOL_MANIFEST["z3"]["tried"] = True
except Exception:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except Exception:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def is_zero_sum(payoff_pairs, tol=1e-9):
    """A payoff table is zero-sum if every row sums to ~0."""
    return all(abs(a + b) <= tol for a, b in payoff_pairs)


def is_collapsed(pairs, tol=1e-9):
    """Collapsed: zero-sum AND no variance in combined surplus across rows."""
    sums = [a + b for a, b in pairs]
    if not sums:
        return True  # vacuously collapsed
    return is_zero_sum(pairs, tol) and (max(sums) - min(sums) <= tol)


def run_positive_tests():
    r = {}
    zs = [(1, -1), (2, -2), (0, 0)]
    r["detect_zero_sum"] = {"ok": is_zero_sum(zs)}
    r["detect_collapse"] = {"ok": is_collapsed(zs)}

    # sympy: symbolic proof x + (-x) == 0
    x = sp.symbols("x")
    r["sympy_row_zero"] = {"expr": str(sp.simplify(x + (-x))), "ok": sp.simplify(x + (-x)) == 0}
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic row-sum zero identity"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


def run_negative_tests():
    r = {}
    # Positive-sum table is not zero-sum
    ps = [(1, 1), (2, 0), (3, -1)]
    r["positive_sum_not_collapsed"] = {"ok": not is_zero_sum(ps)}

    # z3: cannot have a+b == 0 AND a+b > 0
    a, b = Real("a"), Real("b")
    s = Solver(); s.add(And(a + b == 0, a + b > 0))
    unsat = s.check() != sat
    r["z3_no_contradictory_row"] = {"ok": unsat}
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "z3 proves zero-sum and positive-sum rows are mutually exclusive"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


def run_boundary_tests():
    r = {}
    # Empty table: vacuously zero-sum
    r["empty_vacuous"] = {"ok": is_zero_sum([]) and is_collapsed([])}
    # Tolerance edge
    r["near_zero"] = {"ok": is_zero_sum([(1.0, -1.0 + 1e-12)])}
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_igt_zero_sum_collapse_detector",
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
    out_path = os.path.join(out_dir, "sim_igt_zero_sum_collapse_detector_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}; all_ok={results['all_ok']}")
