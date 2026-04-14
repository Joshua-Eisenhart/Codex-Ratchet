#!/usr/bin/env python3
"""classical_baseline_dla_aggregation.py -- non-canon, lane_B-eligible
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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric core for dla_aggregation"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def _dla(N=60, n_particles=200, seed=0):
    rng=np.random.default_rng(seed)
    grid=np.zeros((N,N),dtype=int); c=N//2; grid[c,c]=1
    for _ in range(n_particles):
        x,y = rng.integers(0,N,2)
        for _ in range(2000):
            d=rng.integers(0,4)
            x=(x+[1,-1,0,0][d])%N; y=(y+[0,0,1,-1][d])%N
            if any(0<=x+dx<N and 0<=y+dy<N and grid[x+dx,y+dy] for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]):
                grid[x,y]=1; break
    return grid

def run_positive_tests():
    g=_dla()
    return {"cluster_grew": bool(g.sum()>5), "seed_still_there": bool(g[30,30]==1)}

def run_negative_tests():
    g=_dla(n_particles=0)
    return {"no_particles_only_seed": bool(g.sum()==1)}

def run_boundary_tests():
    g=_dla(N=10, n_particles=5)
    return {"small_runs": bool(g.sum()>=1)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_dla_aggregation",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "classification": "classical_baseline",
        "lane": "lane_B",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_dla_aggregation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} dla_aggregation -> {out_path}")
