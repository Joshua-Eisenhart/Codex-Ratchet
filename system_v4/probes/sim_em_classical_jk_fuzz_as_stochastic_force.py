#!/usr/bin/env python3
"""sim_em_classical_jk_fuzz_as_stochastic_force
Scope: doctrine 'jk fuzz = stochastic "causal" force' (user_causality_fep_doctrine.md
+ user_entropic_monism_doctrine.md). Classical Langevin baseline.
Numpy load_bearing: Langevin integrator; checks noise-driven drift matches
fluctuation-dissipation relation <x^2> = 2 D t.
"""
import json, os, numpy as np
SCOPE_NOTE = "Doctrine 'jk fuzz as stochastic force'. Langevin baseline FDT check. user_entropic_monism_doctrine.md"
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing Langevin integration"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "no SMT claim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def langevin(N=20000, T=1.0, dt=0.001, D=0.5, seed=0):
    rng = np.random.default_rng(seed)
    steps = int(T/dt); x = np.zeros(N)
    for _ in range(steps):
        x += np.sqrt(2*D*dt) * rng.standard_normal(N)
    return x

def run_positive_tests():
    x = langevin()
    var = float(x.var()); expected = 2*0.5*1.0
    return {"FDT_variance": {"pass": bool(abs(var - expected)/expected < 0.05), "var": var, "expected": expected}}

def run_negative_tests():
    x = langevin(D=0.0)
    return {"zero_D_no_spread": {"pass": bool(x.var() < 1e-12)}}

def run_boundary_tests():
    x = langevin(T=0.001, dt=0.0001)
    return {"short_time_small_var": {"pass": bool(x.var() < 0.01)}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {"name": "sim_em_classical_jk_fuzz_as_stochastic_force", "scope_note": SCOPE_NOTE,
               "classification": "classical_baseline", "tool_manifest": TOOL_MANIFEST,
               "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_em_classical_jk_fuzz_as_stochastic_force_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
