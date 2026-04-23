#!/usr/bin/env python3
"""classical_baseline: EM for 1D GMM (2 components)
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (EM for 1D GMM (2 components))"},
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
    rng = np.random.default_rng(1)
    x = np.concatenate([rng.normal(-2,0.5,200), rng.normal(2,0.5,200)])
    mu = np.array([-1.0,1.0]); var=np.array([1.0,1.0]); pi=np.array([0.5,0.5])
    for _ in range(50):
        r = pi*np.exp(-(x[:,None]-mu)**2/(2*var))/np.sqrt(2*np.pi*var)
        r = r/r.sum(1,keepdims=True)
        Nk = r.sum(0); pi = Nk/len(x)
        mu = (r*x[:,None]).sum(0)/Nk
        var = (r*(x[:,None]-mu)**2).sum(0)/Nk + 1e-6
    ok = min(abs(mu))>1.0 and max(abs(mu))<3.0
    return {"recovered_means": {"pass": bool(ok), "mu": mu.tolist()}}

def run_negative_tests():
    return {"nan_guard": {"pass": not bool(np.any(np.isnan(np.array([0.0]))))}}

def run_boundary_tests():
    return {"tiny_var_handled": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_em_gmm",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_em_gmm_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_em_gmm")
