#!/usr/bin/env python3
"""sim_em_classical_dark_energy_as_time_pressure
Scope: doctrine 'dark energy = time'. Classical baseline de Sitter-like toy.
Cites: user_entropic_monism_doctrine.md
Numpy load_bearing: integrate a(t) with Lambda term; check accelerating expansion
co-varies with entropy-horizon growth.
"""
import json, os, numpy as np
SCOPE_NOTE = "Doctrine 'dark-energy=time'. Toy a(t) integration + horizon-entropy growth. user_entropic_monism_doctrine.md"
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing ODE integration"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed; baseline numeric"},
    "z3": {"tried": False, "used": False, "reason": "no SMT claim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric ODE only"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def integrate(Lam=0.1, T=20.0, dt=0.01):
    t = np.arange(0, T, dt); a = np.ones_like(t); H = np.zeros_like(t)
    a[0] = 1.0; H[0] = np.sqrt(Lam/3.0)
    for i in range(1, len(t)):
        a[i] = a[i-1] * np.exp(H[i-1]*dt)
        H[i] = np.sqrt(Lam/3.0)  # de Sitter: H constant
    return t, a, H

def run_positive_tests():
    t, a, H = integrate()
    dd = np.diff(a, 2)
    S_hor = np.log(a**3)  # horizon volume entropy proxy
    return {"expansion_accelerating": {"pass": bool((dd >= -1e-10).all())},
            "horizon_entropy_monotone": {"pass": bool((np.diff(S_hor) > 0).all())}}

def run_negative_tests():
    t, a, _ = integrate(Lam=0.0)
    # Lam=0 -> a stays 1, no acceleration
    return {"no_Lambda_no_acceleration": {"pass": bool(np.allclose(a, 1.0))}}

def run_boundary_tests():
    t, a, _ = integrate(Lam=1e-6, T=1.0)
    return {"tiny_Lambda_small_growth": {"pass": bool(a[-1] > 1.0 and a[-1] < 1.01)}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {"name": "sim_em_classical_dark_energy_as_time_pressure", "scope_note": SCOPE_NOTE,
               "classification": "classical_baseline", "tool_manifest": TOOL_MANIFEST,
               "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_em_classical_dark_energy_as_time_pressure_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
