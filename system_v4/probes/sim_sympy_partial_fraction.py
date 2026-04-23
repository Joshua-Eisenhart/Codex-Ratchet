#!/usr/bin/env python3
"""sim_sympy_partial_fraction -- exact partial-fraction decomposition of a
rational transfer function, certified by recombination equality.
H(s) = (2s^2 + 3s + 5) / ((s-1)(s+2)(s+3))
"""
import json, os
import numpy as np
import sympy as sp

TOOL_MANIFEST = {
    "pytorch":{"tried":False,"used":False,"reason":"no symbolic rationals"},
    "pyg":{"tried":False,"used":False,"reason":"n/a"},
    "z3":{"tried":False,"used":False,"reason":"rational identity better in sympy"},
    "cvc5":{"tried":False,"used":False,"reason":"same"},
    "sympy":{"tried":True,"used":True,"reason":"apart() yields exact rational residues; together() recombines to original exactly"},
    "clifford":{"tried":False,"used":False,"reason":"n/a"},
    "geomstats":{"tried":False,"used":False,"reason":"n/a"},
    "e3nn":{"tried":False,"used":False,"reason":"n/a"},
    "rustworkx":{"tried":False,"used":False,"reason":"n/a"},
    "xgi":{"tried":False,"used":False,"reason":"n/a"},
    "toponetx":{"tried":False,"used":False,"reason":"n/a"},
    "gudhi":{"tried":False,"used":False,"reason":"n/a"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"


def run_positive_tests():
    s = sp.symbols('s')
    H = (2*s**2 + 3*s + 5) / ((s-1)*(s+2)*(s+3))
    Hpf = sp.apart(H, s)
    # Residues: R1 at s=1: (2+3+5)/((3)(4)) = 10/12 = 5/6
    # R2 at s=-2: (8-6+5)/((-3)(1)) = 7/-3 = -7/3
    # R3 at s=-3: (18-9+5)/((-4)(-1)) = 14/4 = 7/2
    expected = sp.Rational(5,6)/(s-1) + sp.Rational(-7,3)/(s+2) + sp.Rational(7,2)/(s+3)
    match_expected = sp.simplify(Hpf - expected) == 0
    # Recombine check
    recomb = sp.together(Hpf)
    recomb_matches = sp.simplify(recomb - H) == 0
    return {"apart_matches_expected_residues": match_expected,
            "together_recovers_original": recomb_matches,
            "decomposition": str(Hpf)}


def run_negative_tests():
    s = sp.symbols('s')
    H = (2*s**2 + 3*s + 5) / ((s-1)*(s+2)*(s+3))
    wrong = sp.Rational(1,2)/(s-1) + sp.Rational(-7,3)/(s+2) + sp.Rational(7,2)/(s+3)
    return {"wrong_residue_detected": sp.simplify(sp.together(wrong) - H) != 0}


def run_boundary_tests():
    # Repeated pole: (1)/(s-1)^2 -> apart returns itself
    s = sp.symbols('s')
    H = 1/(s-1)**2
    Hpf = sp.apart(H, s)
    # Improper rational (deg num >= deg den): polynomial + proper part
    H2 = (s**3 + 1)/(s-1)
    H2pf = sp.apart(H2, s)
    recomb2 = sp.simplify(sp.together(H2pf) - H2) == 0
    return {"repeated_pole_stable": sp.simplify(Hpf - H) == 0,
            "improper_handled": recomb2}


def run_ablation():
    # numpy/scipy residues are floats; exact rational residues cannot be recovered.
    from scipy.signal import residue
    num = [2, 3, 5]
    # den = (s-1)(s+2)(s+3) = s^3 + 4s^2 + s - 6
    den = [1, 4, 1, -6]
    r, p, k = residue(num, den)
    return {"numpy_residues_float": True,
            "residues": [complex(x).real for x in r],
            "poles": [complex(x).real for x in p],
            "note": "floats approximate 5/6, -7/3, 7/2; sympy certifies exact rationals"}


if __name__ == "__main__":
    results = {
        "name": "sympy_partial_fraction",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "ablation": run_ablation(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sympy_partial_fraction_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
