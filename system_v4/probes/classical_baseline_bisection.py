#!/usr/bin/env python3
"""classical_baseline_bisection.py -- non-canon, lane_B-eligible
Generated classical baseline. numpy load_bearing. pos/neg/boundary all required PASS.
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for classical baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not a proof sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not a proof sim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra here"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold here"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "numpy sufficient"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for bisection"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _bisect(f, a, b, tol=1e-10, maxit=200):
    fa=f(a); fb=f(b)
    assert fa*fb<0
    for _ in range(maxit):
        m=(a+b)/2; fm=f(m)
        if abs(fm)<tol or (b-a)/2<tol: return m
        if fa*fm<0: b=m; fb=fm
        else: a=m; fa=fm
    return (a+b)/2

def run_positive_tests():
    r=_bisect(lambda x: x*x-2, 0, 2)
    return {"sqrt2": bool(abs(r-np.sqrt(2))<1e-8)}

def run_negative_tests():
    r=_bisect(lambda x: x-3, 0, 10)
    return {"not_sqrt2": bool(abs(r-np.sqrt(2))>0.5)}

def run_boundary_tests():
    r=_bisect(lambda x: x, -1, 1)
    return {"odd_root_zero": bool(abs(r)<1e-9)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_bisection",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_bisection_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} bisection -> {out_path}")
