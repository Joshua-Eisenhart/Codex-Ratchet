#!/usr/bin/env python3
"""sim 1: gudhi persistent homology Betti numbers on sampled torus match (1,2,1).
Derived from SIM_TEMPLATE. Canonical. Gudhi is load-bearing; numpy only samples points.
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not required for PH on point cloud"},
    "pyg": {"tried": False, "used": False, "reason": "no graph MP in this test"},
    "z3": {"tried": False, "used": False, "reason": "no symbolic constraint"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT"},
    "sympy": {"tried": False, "used": False, "reason": "numeric persistence only"},
    "clifford": {"tried": False, "used": False, "reason": "no rotor algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "not required"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance test"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "cross-checked in sim2"},
    "gudhi": {"tried": True, "used": True, "reason": "Rips filtration + persistence computes Betti from point cloud; load-bearing"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"

import gudhi

def sample_torus(n, R=2.0, r=0.7, seed=0):
    rng = np.random.default_rng(seed)
    u = rng.uniform(0, 2*np.pi, n); v = rng.uniform(0, 2*np.pi, n)
    return np.stack([(R+r*np.cos(v))*np.cos(u), (R+r*np.cos(v))*np.sin(u), r*np.sin(v)], axis=1)

def betti(points, max_edge=1.2, max_dim=3):
    rc = gudhi.RipsComplex(points=points, max_edge_length=max_edge)
    st = rc.create_simplex_tree(max_dimension=max_dim)
    st.compute_persistence()
    b = st.betti_numbers()
    while len(b) < 3: b.append(0)
    return b[:3]

def run_positive_tests():
    r = {}
    for seed in [0, 1, 2]:
        pts = sample_torus(800, seed=seed)
        b = betti(pts)
        r[f"torus_seed{seed}"] = {"betti": b, "expected": [1,2,1], "pass": b == [1,2,1]}
    return r

def run_negative_tests():
    # sphere should give (1,0,1); explicitly NOT (1,2,1)
    rng = np.random.default_rng(0)
    n = 600
    x = rng.normal(size=(n,3)); x /= np.linalg.norm(x, axis=1, keepdims=True)
    b = betti(x, max_edge=0.8)
    return {"sphere_not_torus": {"betti": b, "pass": b != [1,2,1] and b[0]==1 and b[1]==0}}

def run_boundary_tests():
    # undersampled torus fails to recover b1=2
    pts = sample_torus(40, seed=0)
    b = betti(pts, max_edge=1.2)
    return {"undersampled_torus_fails": {"betti": b, "pass": b != [1,2,1]}}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "gudhi_torus_betti_canonical",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "gudhi_torus_betti_canonical_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
    print(f"ALL_PASS={all_pass}")
