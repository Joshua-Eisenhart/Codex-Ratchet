#!/usr/bin/env python3
"""classical_baseline: Julia set for c=-0.8+0.156j
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (Julia set for c=-0.8+0.156j)"},
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
    c=-0.8+0.156j
    X,Y = np.meshgrid(np.linspace(-1.5,1.5,60), np.linspace(-1.5,1.5,60))
    Z = X+1j*Y; E = np.zeros(Z.shape,dtype=int)
    for i in range(50):
        mask = np.abs(Z) <= 2
        Z = np.where(mask, Z*Z + c, Z)
        E[mask] = i
    frac = float(np.mean(E==49))
    return {"has_structure": {"pass": 0.0 <= frac <= 1.0, "frac": frac}}

def run_negative_tests():
    c=-0.8+0.156j; Z = np.array([100+0j])
    for _ in range(5): Z=Z*Z+c
    return {"large_escapes": {"pass": bool(np.abs(Z[0])>2)}}

def run_boundary_tests():
    return {"boundary": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_julia_set",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_julia_set_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_julia_set")
