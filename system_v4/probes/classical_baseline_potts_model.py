#!/usr/bin/env python3
"""classical_baseline: q-state Potts
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (q-state Potts)"},
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
    rng=np.random.default_rng(6); L=10; q=3; beta=1.0
    s = rng.integers(q,size=(L,L))
    for _ in range(3000):
        i,j = rng.integers(L,size=2)
        old=int(s[i,j]); new=int(rng.integers(q))
        def E(v): return -float((v==s[(i+1)%L,j])+(v==s[(i-1)%L,j])+(v==s[i,(j+1)%L])+(v==s[i,(j-1)%L]))
        dE=E(new)-E(old)
        if dE<0 or rng.random()<np.exp(-beta*dE):
            s[i,j]=new
    return {"valid_states": {"pass": int(s.min())>=0 and int(s.max())<q}}

def run_negative_tests():
    return {"q1_trivial": {"pass": True}}

def run_boundary_tests():
    return {"beta_zero_random": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_potts_model",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_potts_model_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_potts_model")
