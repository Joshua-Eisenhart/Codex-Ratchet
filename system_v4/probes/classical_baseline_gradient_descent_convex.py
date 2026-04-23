#!/usr/bin/env python3
"""classical_baseline_gradient_descent_convex.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for gradient_descent_convex"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _gd(grad, x0, lr=0.1, iters=500):
    x=np.array(x0, float)
    for _ in range(iters):
        x = x - lr*grad(x)
    return x

def run_positive_tests():
    # f = (x-3)^2 + (y+1)^2
    g = lambda p: np.array([2*(p[0]-3), 2*(p[1]+1)])
    r=_gd(g, [0.0, 0.0])
    return {"convex_min_found": bool(np.allclose(r, [3,-1], atol=1e-5))}

def run_negative_tests():
    g = lambda p: np.array([2*(p[0]-3), 2*(p[1]+1)])
    r=_gd(g, [0.0, 0.0])
    return {"not_origin": bool(np.linalg.norm(r)>1)}

def run_boundary_tests():
    g = lambda p: np.array([2*p[0]])
    r=_gd(g, [5.0])
    return {"reaches_zero": bool(abs(r[0])<1e-5)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_gradient_descent_convex",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_gradient_descent_convex_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} gradient_descent_convex -> {out_path}")
