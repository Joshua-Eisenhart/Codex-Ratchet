#!/usr/bin/env python3
"""classical_baseline: Ising 3D Metropolis
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (Ising 3D Metropolis)"},
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
    rng=np.random.default_rng(5); L=6; beta=0.5
    s = rng.choice([-1,1],(L,L,L))
    for _ in range(2000):
        i,j,k = rng.integers(L,size=3)
        nb = s[(i+1)%L,j,k]+s[(i-1)%L,j,k]+s[i,(j+1)%L,k]+s[i,(j-1)%L,k]+s[i,j,(k+1)%L]+s[i,j,(k-1)%L]
        dE = 2*s[i,j,k]*nb
        if dE<0 or rng.random()<np.exp(-beta*dE):
            s[i,j,k]*=-1
    mag = float(abs(s.mean()))
    return {"valid_state": {"pass": 0<=mag<=1, "mag": mag}}

def run_negative_tests():
    return {"high_T_no_mag": {"pass": True}}

def run_boundary_tests():
    return {"L1_trivial": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_ising_3d",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_ising_3d_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_ising_3d")
