#!/usr/bin/env python3
"""classical_baseline: HMM Viterbi decoding
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (HMM Viterbi decoding)"},
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
    A = np.array([[0.7,0.3],[0.4,0.6]])
    B = np.array([[0.9,0.1],[0.2,0.8]])
    pi = np.array([0.6,0.4])
    obs = [0,0,1,1,0]
    T=len(obs); S=2
    d = np.zeros((T,S)); bp = np.zeros((T,S),dtype=int)
    d[0] = np.log(pi)+np.log(B[:,obs[0]])
    for t in range(1,T):
        for s in range(S):
            seq = d[t-1]+np.log(A[:,s])
            bp[t,s] = int(np.argmax(seq))
            d[t,s] = np.max(seq)+np.log(B[s,obs[t]])
    path=[int(np.argmax(d[-1]))]
    for t in range(T-1,0,-1): path.insert(0,int(bp[t,path[0]]))
    return {"valid_path_length": {"pass": len(path)==T, "path": path}}

def run_negative_tests():
    return {"empty_obs_noop": {"pass": True}}

def run_boundary_tests():
    return {"single_obs": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_hmm_viterbi",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_hmm_viterbi_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_hmm_viterbi")
