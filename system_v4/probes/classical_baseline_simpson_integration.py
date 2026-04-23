#!/usr/bin/env python3
"""classical_baseline_simpson_integration.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for simpson_integration"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _simpson(f, a, b, n=100):
    if n%2: n+=1
    x=np.linspace(a,b,n+1); y=f(x)
    h=(b-a)/n
    return h/3*(y[0]+y[-1] + 4*y[1:-1:2].sum() + 2*y[2:-2:2].sum())

def run_positive_tests():
    # integral of sin from 0 to pi = 2
    I=_simpson(np.sin, 0, np.pi)
    return {"sin_0_pi": bool(abs(I-2.0)<1e-6)}

def run_negative_tests():
    I=_simpson(np.cos, 0, np.pi)
    # integral cos 0..pi = 0, not 2
    return {"cos_not_2": bool(abs(I-2.0)>1)}

def run_boundary_tests():
    I=_simpson(lambda x: np.ones_like(x), 0, 1)
    return {"const_one": bool(abs(I-1.0)<1e-10)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_simpson_integration",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_simpson_integration_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} simpson_integration -> {out_path}")
