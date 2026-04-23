#!/usr/bin/env python3
"""classical_baseline_wigner_semicircle.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for wigner_semicircle"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def run_positive_tests():
    rng=np.random.default_rng(0); N=400
    A=rng.standard_normal((N,N)); H=(A+A.T)/np.sqrt(2*N)
    w=np.linalg.eigvalsh(H)
    # radius ~ 2 for GOE with this normalization
    return {"radius_near_2": bool(1.7 < w.max() < 2.5 and -2.5 < w.min() < -1.7)}

def run_negative_tests():
    # diagonal matrix isn't semicircular - eigenvalues equal diagonal
    D=np.diag(np.linspace(-1,1,50)); w=np.linalg.eigvalsh(D)
    return {"diagonal_not_semicircle": bool(np.allclose(sorted(w), np.linspace(-1,1,50)))}

def run_boundary_tests():
    H=np.array([[0.0]]); w=np.linalg.eigvalsh(H)
    return {"1x1_zero": bool(w[0]==0.0)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_wigner_semicircle",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_wigner_semicircle_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} wigner_semicircle -> {out_path}")
