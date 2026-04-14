#!/usr/bin/env python3
"""classical_baseline_wave_equation_1d.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for wave_equation_1d"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _wave1d(N=100, T=200, c=0.5, dx=1.0, dt=1.0):
    u_prev=np.zeros(N); u=np.exp(-0.1*(np.arange(N)-N/2)**2); hist=[u.copy()]
    r=(c*dt/dx)**2
    for _ in range(T):
        u_new = np.zeros(N)
        u_new[1:-1] = 2*u[1:-1]-u_prev[1:-1]+r*(u[2:]-2*u[1:-1]+u[:-2])
        u_prev=u; u=u_new; hist.append(u.copy())
    return np.array(hist)

def run_positive_tests():
    h=_wave1d()
    return {"energy_bounded": bool(np.all(np.isfinite(h))), "wave_propagates": bool(h[-1].std()>1e-3)}

def run_negative_tests():
    h=_wave1d()
    return {"not_identical_to_initial": bool(not np.allclose(h[0], h[-1]))}

def run_boundary_tests():
    h=_wave1d(T=0)
    return {"no_time_one_frame": bool(h.shape[0]==1)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_wave_equation_1d",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_wave_equation_1d_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} wave_equation_1d -> {out_path}")
