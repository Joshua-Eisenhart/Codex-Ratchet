#!/usr/bin/env python3
"""classical_baseline_monte_carlo_pi.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for monte_carlo_pi"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def run_positive_tests():
    rng=np.random.default_rng(0)
    pts=rng.random((200000,2))
    pi_est = 4*np.mean(np.sum(pts**2,axis=1)<1)
    return {"pi_close": bool(abs(pi_est-np.pi)<0.02)}

def run_negative_tests():
    # deterministic all-ones -> no points inside unit circle from (0,0) wait they're in [0,1]^2, all inside distance<sqrt(2)
    pts=np.ones((100,2))  # all at (1,1), outside
    pi_est = 4*np.mean(np.sum(pts**2,axis=1)<1)
    return {"biased_sample_wrong": bool(pi_est==0.0)}

def run_boundary_tests():
    pts=np.zeros((10,2))
    pi_est=4*np.mean(np.sum(pts**2,axis=1)<1)
    return {"origin_all_inside": bool(pi_est==4.0)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_monte_carlo_pi",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_monte_carlo_pi_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} monte_carlo_pi -> {out_path}")
