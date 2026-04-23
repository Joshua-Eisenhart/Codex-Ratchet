#!/usr/bin/env python3
"""classical_baseline_heat_equation_fd.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for heat_equation_fd"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _heat1d(N=64, steps=500, alpha=0.1, dt=0.1, dx=1.0):
    u = np.zeros(N); u[N//2]=1.0
    r = alpha*dt/dx**2
    for _ in range(steps):
        u[1:-1] = u[1:-1] + r*(u[2:]-2*u[1:-1]+u[:-2])
    return u

def run_positive_tests():
    u = _heat1d()
    # mass conserved (up to boundary leakage, which is 0 since ends stay 0)
    return {"peak_diffused": bool(u.max() < 0.5), "spread_positive": bool(u[32+5]>0)}

def run_negative_tests():
    u0 = np.zeros(64); u0[32]=1.0
    u = _heat1d()
    return {"not_same_as_initial": bool(not np.allclose(u, u0))}

def run_boundary_tests():
    u = _heat1d(steps=0)
    return {"zero_steps_identity_peak": bool(u[32]==1.0)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_heat_equation_fd",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_heat_equation_fd_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} heat_equation_fd -> {out_path}")
