#!/usr/bin/env python3
"""classical_baseline_logistic_bifurcation.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for logistic_bifurcation"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _orbit(r, x0=0.5, burn=500, keep=100):
    x=x0
    for _ in range(burn): x=r*x*(1-x)
    out=[]
    for _ in range(keep):
        x=r*x*(1-x); out.append(x)
    return np.array(out)

def run_positive_tests():
    o_stable=_orbit(2.5); o_chaos=_orbit(3.9)
    return {"fixed_point_below_3": bool(o_stable.std()<1e-6),
            "chaotic_at_3p9": bool(o_chaos.std()>0.1)}

def run_negative_tests():
    o=_orbit(3.9)
    return {"chaos_not_fixed": bool(o.std()>1e-3)}

def run_boundary_tests():
    o=_orbit(0.5)
    return {"subcritical_to_zero": bool(o[-1]<1e-6)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_logistic_bifurcation",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_logistic_bifurcation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} logistic_bifurcation -> {out_path}")
