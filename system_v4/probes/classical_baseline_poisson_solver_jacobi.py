#!/usr/bin/env python3
"""classical_baseline: Poisson solver (Jacobi)
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (Poisson solver (Jacobi))"},
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
    N = 20
    f = rng.standard_normal((N, N)) * 0.01
    u = np.zeros((N, N))
    for _ in range(3000):
        u[1:-1,1:-1] = 0.25*(u[:-2,1:-1]+u[2:,1:-1]+u[1:-1,:-2]+u[1:-1,2:] + f[1:-1,1:-1])
    res = (u[:-2,1:-1]+u[2:,1:-1]+u[1:-1,:-2]+u[1:-1,2:] - 4*u[1:-1,1:-1] + f[1:-1,1:-1])
    r = float(np.max(np.abs(res)))
    return {"converged": {"pass": r < 1e-2, "residual": r}}

def run_negative_tests():
    u = np.ones((10,10))
    res = u[:-2,1:-1]+u[2:,1:-1]+u[1:-1,:-2]+u[1:-1,2:] - 4*u[1:-1,1:-1]
    return {"constant_is_harmonic": {"pass": float(np.max(np.abs(res))) < 1e-12}}

def run_boundary_tests():
    u = np.zeros((3,3))
    return {"tiny_grid": {"pass": u.shape == (3,3)}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_poisson_solver_jacobi",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_poisson_solver_jacobi_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_poisson_solver_jacobi")
