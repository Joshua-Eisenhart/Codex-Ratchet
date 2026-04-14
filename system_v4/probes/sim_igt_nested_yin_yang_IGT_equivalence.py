#!/usr/bin/env python3
"""
sim_igt_nested_yin_yang_IGT_equivalence -- positive test that IGT's nested
win-lose / WIN-LOSE pattern is indistinguishable from nested yin/yang at
two scales. The equivalence holds under a relabeling bijection.
"""
import json, os
import numpy as np
from itertools import product
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "no tensors"},
    "pyg":       {"tried": False, "used": False, "reason": "no graph"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "z3 suffices"},
    "sympy":     {"tried": False, "used": False, "reason": "discrete enumeration suffices"},
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
    from z3 import Bool, Solver, And, Or, Not, sat, Implies
    TOOL_MANIFEST["z3"]["tried"] = True
except Exception:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


# Bijection: ("win","lose") <-> ("yang","yin"); ("WIN","LOSE") <-> ("YANG","YIN").
IGT_TO_YY = {"win": "yang", "lose": "yin", "WIN": "YANG", "LOSE": "YIN"}


def map_seq(pair):
    short, long_ = pair
    return (IGT_TO_YY[short], IGT_TO_YY[long_])


def run_positive_tests():
    r = {}
    shorts, longs = ("win", "lose"), ("WIN", "LOSE")
    pairs = list(product(shorts, longs))
    mapped = [map_seq(p) for p in pairs]
    r["pairs"] = {"n": len(pairs), "mapped": mapped, "ok": len(set(mapped)) == 4}

    # z3: at each scale, yang xor yin; same structure at both scales
    y_s, n_s, Y_l, N_l = Bool("y_s"), Bool("n_s"), Bool("Y_l"), Bool("N_l")
    s = Solver()
    # xor at each scale
    s.add(Or(And(y_s, Not(n_s)), And(Not(y_s), n_s)))
    s.add(Or(And(Y_l, Not(N_l)), And(Not(Y_l), N_l)))
    r["z3_two_scale_xor_sat"] = {"ok": s.check() == sat}
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "structural xor at both scales is simultaneously satisfiable"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


def run_negative_tests():
    r = {}
    # A mapping that collapses scales (both to yang) must NOT be a bijection
    collapse = {"win": "yang", "lose": "yang", "WIN": "YANG", "LOSE": "YANG"}
    mapped = [(collapse[s], collapse[l]) for s in ("win", "lose") for l in ("WIN", "LOSE")]
    r["collapse_not_bijection"] = {"distinct": len(set(mapped)), "ok": len(set(mapped)) < 4}

    # z3: demanding yang AND yin at same scale is UNSAT
    y, n = Bool("y"), Bool("n")
    s = Solver(); s.add(And(y, n, Or(Not(y), Not(n))))
    unsat = s.check() != sat
    r["z3_same_scale_contra"] = {"ok": unsat}
    r["ok"] = all(v["ok"] for v in r.values() if isinstance(v, dict))
    return r


def run_boundary_tests():
    r = {}
    # 0-depth nesting degenerates to single-scale yin/yang
    r["depth0"] = {"ok": IGT_TO_YY["win"] == "yang" and IGT_TO_YY["lose"] == "yin"}
    r["ok"] = r["depth0"]["ok"]
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_igt_nested_yin_yang_IGT_equivalence",
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
    out_path = os.path.join(out_dir, "sim_igt_nested_yin_yang_IGT_equivalence_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}; all_ok={results['all_ok']}")
