#!/usr/bin/env python3
"""sim_em_classical_time_as_entropy_increment
Scope: illumination sim (time=entropy-increasing). Classical baseline.
Cites: user_entropic_monism_doctrine.md
Numpy load_bearing: simulates coarse-grained diffusion and measures dS/dt>=0.
"""
import json, os, numpy as np
SCOPE_NOTE = "Doctrine 'time=entropy increasing'. Baseline diffusion; dS/dt sign test. See user_entropic_monism_doctrine.md"
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing diffusion + entropy calc"},
    "pytorch": {"tried": False, "used": False, "reason": "bridge sim 09 handles autograd time-arrow"},
    "z3": {"tried": False, "used": False, "reason": "not an admissibility claim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
    "clifford": {"tried": False, "used": False, "reason": "no geometry"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def entropy(p):
    p = p[p > 0]; return float(-(p * np.log(p)).sum())

def diffuse(p0, steps=50):
    p = p0.copy(); S = [entropy(p)]
    for _ in range(steps):
        p = 0.5*p + 0.25*np.roll(p, 1) + 0.25*np.roll(p, -1)
        p /= p.sum(); S.append(entropy(p))
    return np.array(S)

def run_positive_tests():
    p0 = np.zeros(32); p0[16] = 1.0
    S = diffuse(p0)
    dS = np.diff(S)
    return {"monotone_increase": {"pass": bool((dS >= -1e-12).all()), "dS_min": float(dS.min())}}

def run_negative_tests():
    # uniform is fixed point; no strict increase — but also no decrease
    p0 = np.ones(32)/32
    S = diffuse(p0); dS = np.diff(S)
    return {"uniform_no_decrease": {"pass": bool((dS >= -1e-12).all())},
            "reverse_time_violates_arrow": {"pass": bool((np.diff(S[::-1]) <= 1e-12).all())}}

def run_boundary_tests():
    p0 = np.zeros(4); p0[0] = 1.0
    S = diffuse(p0, steps=5)
    return {"small_lattice": {"pass": bool(S[-1] > S[0]), "S0": float(S[0]), "Sfinal": float(S[-1])}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {"name": "sim_em_classical_time_as_entropy_increment", "scope_note": SCOPE_NOTE,
               "classification": "classical_baseline", "tool_manifest": TOOL_MANIFEST,
               "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_em_classical_time_as_entropy_increment_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
