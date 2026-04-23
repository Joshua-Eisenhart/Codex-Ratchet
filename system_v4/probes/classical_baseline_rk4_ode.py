#!/usr/bin/env python3
"""classical_baseline_rk4_ode.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for rk4_ode"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _rk4(f, y0, t):
    y=np.zeros((len(t), *np.shape(y0))); y[0]=y0
    for i in range(len(t)-1):
        h=t[i+1]-t[i]
        k1=f(t[i], y[i])
        k2=f(t[i]+h/2, y[i]+h*k1/2)
        k3=f(t[i]+h/2, y[i]+h*k2/2)
        k4=f(t[i]+h, y[i]+h*k3)
        y[i+1]=y[i]+h*(k1+2*k2+2*k3+k4)/6
    return y

def run_positive_tests():
    # dy/dt = y, y(0)=1 -> y(1)=e
    t=np.linspace(0,1,100); y=_rk4(lambda t,y: y, 1.0, t)
    return {"exponential_at_1": bool(abs(y[-1]-np.e)<1e-6)}

def run_negative_tests():
    t=np.linspace(0,1,100); y=_rk4(lambda t,y: y, 1.0, t)
    return {"not_constant": bool(y[-1]!=y[0])}

def run_boundary_tests():
    t=np.array([0.0]); y=_rk4(lambda t,y: y, 1.0, t)
    return {"single_point": bool(y[0]==1.0)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_rk4_ode",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_rk4_ode_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} rk4_ode -> {out_path}")
