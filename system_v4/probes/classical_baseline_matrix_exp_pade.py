#!/usr/bin/env python3
"""classical_baseline_matrix_exp_pade.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for matrix_exp_pade"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _expm_series(A, n=40):
    N=A.shape[0]; S=np.eye(N); term=np.eye(N)
    for k in range(1,n):
        term = term @ A / k; S = S + term
    return S

def run_positive_tests():
    A=np.array([[0,1],[-1,0]],float)
    E=_expm_series(A*np.pi/2)
    R=np.array([[0,1],[-1,0]],float)
    return {"rotation_90": bool(np.allclose(E, R, atol=1e-6))}

def run_negative_tests():
    A=np.array([[0,1],[-1,0]],float)
    E=_expm_series(A)
    return {"not_identity": bool(not np.allclose(E, np.eye(2)))}

def run_boundary_tests():
    A=np.zeros((3,3))
    E=_expm_series(A)
    return {"zero_exp_identity": bool(np.allclose(E, np.eye(3)))}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_matrix_exp_pade",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_matrix_exp_pade_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} matrix_exp_pade -> {out_path}")
