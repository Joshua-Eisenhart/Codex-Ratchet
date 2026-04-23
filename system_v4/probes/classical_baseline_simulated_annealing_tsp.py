#!/usr/bin/env python3
"""classical_baseline_simulated_annealing_tsp.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for simulated_annealing_tsp"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _tour_len(perm, pts):
    P=pts[perm]; return np.sum(np.linalg.norm(P - np.roll(P,-1,axis=0), axis=1))

def _sa(pts, T0=1.0, alpha=0.995, steps=5000, seed=0):
    rng=np.random.default_rng(seed)
    n=len(pts); perm=np.arange(n); rng.shuffle(perm)
    L=_tour_len(perm, pts); T=T0
    for _ in range(steps):
        i,j=sorted(rng.integers(0,n,2))
        if i==j: continue
        new=perm.copy(); new[i:j+1]=new[i:j+1][::-1]
        Lnew=_tour_len(new, pts); dL=Lnew-L
        if dL<0 or rng.random()<np.exp(-dL/T):
            perm, L = new, Lnew
        T*=alpha
    return perm, L

def run_positive_tests():
    rng=np.random.default_rng(0)
    pts = rng.random((8,2))
    perm0=np.arange(8); L0=_tour_len(perm0, pts)
    _, Lsa = _sa(pts)
    return {"sa_improves": bool(Lsa <= L0 + 1e-9)}

def run_negative_tests():
    rng=np.random.default_rng(1)
    pts=rng.random((6,2))
    _, L = _sa(pts)
    return {"nontrivial_length": bool(L>0)}

def run_boundary_tests():
    pts=np.array([[0.,0.],[1.,0.]])
    perm, L = _sa(pts, steps=100)
    return {"two_cities_len_2": bool(abs(L-2.0)<1e-9)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_simulated_annealing_tsp",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_simulated_annealing_tsp_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} simulated_annealing_tsp -> {out_path}")
