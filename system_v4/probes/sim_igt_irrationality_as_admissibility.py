#!/usr/bin/env python3
"""
sim_igt_irrationality_as_admissibility -- 'irrational' short-horizon moves
(negative immediate payoff) can be admissible under long-horizon WIN
admissibility. The irrational label is probe-relative.
"""
import json, os
import numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "scalar sequence"},
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
    from z3 import Int, Solver, And, Or, sat, Sum
    TOOL_MANIFEST["z3"]["tried"] = True
except Exception:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except Exception:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def short_rational(move): return move >= 0
def long_admissible(seq, horizon_target=1): return sum(seq) >= horizon_target


def run_positive_tests():
    r = {}
    # A sacrificial move: irrational short-term (-1), admissible long-horizon overall
    seq = [-1, +1, +1]
    r["sacrifice_admissible"] = {
        "short_rational_at_0": short_rational(seq[0]),
        "long_admissible": long_admissible(seq, 1),
        "ok": (not short_rational(seq[0])) and long_admissible(seq, 1),
    }

    # z3: exists sequence with x0<0 and sum>=1
    x = [Int(f"x{i}") for i in range(3)]
    s = Solver()
    for xi in x: s.add(Or(xi == -1, xi == +1))
    s.add(x[0] < 0); s.add(Sum(x) >= 1)
    r["z3_witness"] = {"ok": s.check() == sat}
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "SAT witness shows irrational-short-and-admissible-long is nonempty"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


def run_negative_tests():
    r = {}
    # All irrational moves cannot be long-admissible at horizon_target=1
    seq = [-1, -1, -1]
    r["all_irrational_inadmissible"] = {"ok": not long_admissible(seq, 1)}

    # sympy: if every x_i = -1 then sum = -n < 1
    n = 3
    total = sp.Add(*([-1] * n))
    r["sympy_total"] = {"total": int(total), "ok": int(total) < 1}
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic total check for the all-irrational branch"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


def run_boundary_tests():
    r = {}
    # Exact horizon boundary: sum == target
    seq = [-1, +1, +1]
    r["boundary_equal"] = {"ok": long_admissible(seq, 1)}
    seq2 = [-1, -1, +1]
    r["just_below"] = {"ok": not long_admissible(seq2, 1)}
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_igt_irrationality_as_admissibility",
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
    out_path = os.path.join(out_dir, "sim_igt_irrationality_as_admissibility_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}; all_ok={results['all_ok']}")
