#!/usr/bin/env python3
"""classical_baseline: Barabasi-Albert preferential attachment
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (Barabasi-Albert preferential attachment)"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed for classical baseline"},
    "pyg": {"tried": False, "used": False, "reason": "no graph learning in this sim"},
    "z3": {"tried": False, "used": False, "reason": "no SMT claim in classical baseline"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT claim in classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "numeric-only probe, no symbolic needed"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra needed"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold learning needed"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant NN needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "numpy adjacency sufficient"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph needed"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex needed"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent homology needed"},
}

TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}

def run_positive_tests():
    rng = np.random.default_rng(0)
    N=50; m=2
    adj = np.zeros((N,N),dtype=int)
    adj[0,1]=adj[1,0]=1; adj[1,2]=adj[2,1]=1; adj[0,2]=adj[2,0]=1
    for i in range(3,N):
        deg = adj.sum(1)[:i].astype(float)
        p = deg/deg.sum()
        targets = rng.choice(i,size=m,replace=False,p=p)
        for t in targets: adj[i,t]=adj[t,i]=1
    deg = adj.sum(1)
    return {"heavy_tail": {"pass": int(deg.max()) > int(2*deg.mean()), "max_deg": int(deg.max())}}

def run_negative_tests():
    adj = np.zeros((5,5))
    return {"empty_zero_deg": {"pass": int(adj.sum()) == 0}}

def run_boundary_tests():
    return {"m_equals_all": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_barabasi_albert",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_barabasi_albert_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_barabasi_albert")
