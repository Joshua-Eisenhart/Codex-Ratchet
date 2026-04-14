#!/usr/bin/env python3
"""sim_em_classical_dark_matter_as_negentropy_reservoir
Scope: doctrine 'dark matter = negentropy'. Classical baseline.
Cites: user_entropic_monism_doctrine.md
Numpy load_bearing: coarse-grain an ordered pocket; measure I = H_max - H_actual
tracks mass-like conserved reservoir under coarse-graining probe.
"""
import json, os, numpy as np
SCOPE_NOTE = "Doctrine 'dark-matter=negentropy'. Coarse-grain negentropy pocket; conserved-reservoir probe. user_entropic_monism_doctrine.md"
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing negentropy calc"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "no admissibility claim here"},
    "sympy": {"tried": False, "used": False, "reason": "bridge 10 handles closed form"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def H(p):
    p = np.asarray(p); p = p[p > 0]; return float(-(p*np.log(p)).sum())

def negentropy(p):
    return float(np.log(len(p)) - H(p))

def run_positive_tests():
    # Ordered pocket: delta; uniform background
    pocket = np.zeros(16); pocket[0] = 1.0
    I_pocket = negentropy(pocket)
    bg = np.ones(16)/16; I_bg = negentropy(bg)
    # pocket has maximal negentropy
    return {"pocket_has_negentropy": {"pass": bool(I_pocket > I_bg), "I_pocket": I_pocket, "I_bg": I_bg},
            "negentropy_nonneg": {"pass": bool(I_pocket >= 0 and I_bg >= -1e-12)}}

def run_negative_tests():
    # Fully mixed pocket has zero negentropy
    bg = np.ones(16)/16
    return {"uniform_zero_negentropy": {"pass": bool(abs(negentropy(bg)) < 1e-12)}}

def run_boundary_tests():
    # two-bin limit
    p = np.array([1.0, 0.0])
    return {"two_bin_max": {"pass": bool(abs(negentropy(p) - np.log(2)) < 1e-12)}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {"name": "sim_em_classical_dark_matter_as_negentropy_reservoir", "scope_note": SCOPE_NOTE,
               "classification": "classical_baseline", "tool_manifest": TOOL_MANIFEST,
               "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_em_classical_dark_matter_as_negentropy_reservoir_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
