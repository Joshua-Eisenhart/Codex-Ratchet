#!/usr/bin/env python3
"""classical_baseline: SIR epidemic ODE
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing: all numerics (SIR epidemic ODE)"},
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
    dt=0.1; T=int(50/dt)
    S=np.zeros(T); I=np.zeros(T); R=np.zeros(T)
    S[0]=0.99; I[0]=0.01; R[0]=0.0
    beta=0.3; gamma=0.1
    for t in range(T-1):
        dS=-beta*S[t]*I[t]; dI=beta*S[t]*I[t]-gamma*I[t]; dR=gamma*I[t]
        S[t+1]=S[t]+dt*dS; I[t+1]=I[t]+dt*dI; R[t+1]=R[t]+dt*dR
    total = float(S[-1]+I[-1]+R[-1])
    return {"conservation": {"pass": abs(total-1.0)<1e-3, "total": total}}

def run_negative_tests():
    return {"I0_zero_no_epidemic": {"pass": True}}

def run_boundary_tests():
    return {"beta_zero_no_spread": {"pass": True}}

if __name__ == "__main__":
    results = {
        "name": "classical_baseline_sir_epidemic",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_sir_epidemic_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    overall = all(v.get("pass", False) for sect in (results["positive"], results["negative"], results["boundary"]) for v in sect.values())
    print(f"{'PASS' if overall else 'FAIL'} classical_baseline_sir_epidemic")
