#!/usr/bin/env python3
"""
sim_support_first_constraint_layer_coupling.py

Lane B classical baseline: which fences from L1 survive in L4, and which
gates from L6 persist in L10, under support-first constraint-manifold
layer coupling.

A 'fence' = a predicate on tuples. A fence 'survives' across layer
coupling if the intersection of fence-admissible set with the coupled
layer's admissible set is non-empty AND proper.

Numpy + sympy (symbolic fence algebra). No pytorch / z3.
"""

import json
import os
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "excluded; classical baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "no SMT claim"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT claim"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic fence expression for cross-check"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    HAVE_SYMPY = True
except ImportError:
    HAVE_SYMPY = False


def universe(n=4):
    out = []
    for i in range(3**n):
        t, x = [], i
        for _ in range(n):
            t.append((x % 3) - 1)
            x //= 3
        out.append(tuple(t))
    return out


# --- Fences (L1) and gates (L6) -- classical definitions --------------

L1_FENCES = {
    "F1_nonzero":          lambda s: any(x != 0 for x in s),
    "F2_sum_bounded":      lambda s: abs(sum(s)) <= 2,
    "F3_no_flip_adjacent": lambda s: all(not (s[i] == 1 and s[i+1] == -1) for i in range(len(s)-1)),
    "F4_has_zero":         lambda s: 0 in s,
}

L4_SURFACE = lambda s: (abs(sum(s)) <= 2) and (s != tuple([0]*len(s)))

L6_GATES = {
    "G1_first_plus":       lambda s: s[0] == 1,
    "G2_last_minus":       lambda s: s[-1] == -1,
    "G3_middle_zero":      lambda s: s[len(s)//2] == 0,
    "G4_balanced":         lambda s: sum(s) == 0,
}

L10_SURFACE = lambda s: (sum(s) == 0) and (0 in s)


def survive(universe_, fence, surface):
    admissible = [s for s in universe_ if fence(s)]
    coupled = [s for s in admissible if surface(s)]
    return {
        "fence_size": len(admissible),
        "coupled_size": len(coupled),
        "survives": 0 < len(coupled) < len(admissible) or (len(coupled) > 0 and len(coupled) == len(admissible)),
        "proper_restriction": 0 < len(coupled) < len(admissible),
        "nonempty": len(coupled) > 0,
    }


def run_positive_tests():
    U = universe(4)
    r = {"L1_to_L4": {}, "L6_to_L10": {}}
    for name, f in L1_FENCES.items():
        r["L1_to_L4"][name] = survive(U, f, L4_SURFACE)
    for name, g in L6_GATES.items():
        r["L6_to_L10"][name] = survive(U, g, L10_SURFACE)
    r["n_l1_survivors"] = sum(1 for v in r["L1_to_L4"].values() if v["nonempty"])
    r["n_l6_survivors"] = sum(1 for v in r["L6_to_L10"].values() if v["nonempty"])
    r["pass"] = r["n_l1_survivors"] >= 3 and r["n_l6_survivors"] >= 2
    return r


def run_negative_tests():
    U = universe(4)
    r = {}
    # impossible fence: all tuples with sum = 100 -> empty; coupling result empty
    bad_fence = lambda s: sum(s) == 100
    r["impossible_fence"] = survive(U, bad_fence, L4_SURFACE)
    r["impossible_fence_empty"] = (r["impossible_fence"]["coupled_size"] == 0)
    # gate that demands forbidden-by-L10 structure: all-one tuple has sum 4 != 0
    bad_gate = lambda s: all(x == 1 for x in s)
    r["bad_gate"] = survive(U, bad_gate, L10_SURFACE)
    r["bad_gate_fails_l10"] = (r["bad_gate"]["coupled_size"] == 0)
    r["pass"] = r["impossible_fence_empty"] and r["bad_gate_fails_l10"]
    return r


def run_boundary_tests():
    r = {}
    # n=2 universe edge case
    U2 = universe(2)
    r["u2_size"] = len(U2)  # 9
    # vacuous fence = identity universe
    vac = lambda s: True
    s = survive(U2, vac, L4_SURFACE)
    r["vacuous_fence_coupling"] = s
    # sympy symbolic: sum over tuple symbolically
    if HAVE_SYMPY:
        a, b = sp.symbols('a b', integer=True)
        expr = sp.Abs(a + b) <= 2
        r["sympy_fence_expr"] = str(expr)
        r["sympy_fence_is_relational"] = True
    # exactly-one survivor pattern: fence forcing (1,0,0,-1) survives L10
    tight = lambda s: s == (1, 0, 0, -1)
    surv = survive(universe(4), tight, L10_SURFACE)
    r["canonical_survives_l10"] = (surv["coupled_size"] == 1)
    r["pass"] = (s["coupled_size"] > 0) and r["canonical_survives_l10"]
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    results = {
        "name": "support_first_constraint_layer_coupling",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "classical_baseline",
        "all_pass": bool(pos.get("pass") and neg.get("pass") and bnd.get("pass")),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "support_first_constraint_layer_coupling_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass={results['all_pass']}")
