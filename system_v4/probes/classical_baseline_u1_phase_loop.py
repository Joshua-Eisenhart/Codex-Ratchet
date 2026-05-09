#!/usr/bin/env python3
"""classical baseline u1 phase loop

classical_baseline, numpy-only. Non-canon. Lane_B-eligible.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "numpy":    {"tried": True,  "used": True,  "reason": "load-bearing linear algebra / rng for classical baseline"},
    "pytorch":  {"tried": False, "used": False, "reason": "classical_baseline sim; torch not required"},
    "pyg":      {"tried": False, "used": False, "reason": "no graph-NN step in this baseline"},
    "z3":       {"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"},
    "cvc5":     {"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"},
    "sympy":    {"tried": False, "used": False, "reason": "numerical identity sufficient; symbolic not needed here"},
    "clifford": {"tried": False, "used": False, "reason": "matrix rep baseline; Cl(n) algebra deferred to canonical lane"},
    "geomstats":{"tried": False, "used": False, "reason": "flat/discrete baseline; manifold tooling out of scope"},
    "e3nn":     {"tried": False, "used": False, "reason": "no equivariant NN in baseline"},
    "rustworkx":{"tried": False, "used": False, "reason": "small adjacency handled by numpy"},
    "xgi":      {"tried": False, "used": False, "reason": "no hypergraph structure in this sim"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex in this sim"},
    "gudhi":    {"tried": False, "used": False, "reason": "no persistent homology in this sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None,
    "xgi": None, "toponetx": None, "gudhi": None,
}

NAME = "classical_baseline_u1_phase_loop"

def run_positive_tests():
    out = {}
    # discretize loop into N links with phases summing to 0 mod 2pi => holonomy trivial
    N = 64
    rng = np.random.default_rng(0)
    phases = rng.standard_normal(N)
    phases -= phases.sum() / N  # remove mean so sum=0
    hol = np.exp(1j*phases.sum())
    out["zero_mean_holonomy_trivial"] = {"pass": bool(np.isclose(hol, 1.0, atol=1e-10))}
    # Winding: phases = 2*pi/N each -> total = 2*pi -> trivial holonomy but winding 1
    phi = 2*np.pi/N
    hol2 = np.exp(1j*N*phi)
    out["winding_one_hol_trivial"] = {"pass": bool(np.isclose(hol2, 1.0, atol=1e-10))}
    # Gauge invariance: adding d(lambda) around closed loop changes nothing
    lam = rng.standard_normal(N)
    dlam = np.roll(lam, -1) - lam  # sums to 0
    hol3 = np.exp(1j*(phases + dlam).sum())
    out["gauge_invariance"] = {"pass": bool(np.isclose(hol3, 1.0, atol=1e-10))}
    return out

def run_negative_tests():
    # Nonzero net phase breaks triviality
    phases = np.array([0.3]*10)
    hol = np.exp(1j*phases.sum())
    return {"nonzero_phase_not_trivial": {"pass": bool(not np.isclose(hol, 1.0, atol=1e-6))}}

def run_boundary_tests():
    return {"empty_loop_trivial": {"pass": bool(np.isclose(np.exp(1j*0.0), 1.0))}}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        all(v.get("pass") for v in pos.values()) and
        all(v.get("pass") for v in neg.values()) and
        all(v.get("pass") for v in bnd.values())
    )
    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, NAME + "_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{NAME}: all_pass={all_pass} -> {out_path}")
