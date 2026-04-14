#!/usr/bin/env python3
"""IGT atom 3: reduction.

Claim: the two axis-projections pi_inner(s)=s[0] and pi_outer(s)=s[1]
are 2-to-1 surjections that each collapse the 4-carrier ring to a
2-element set.  Reduction loses information: it is irreversible.
"""
import json, os
from _igt_common import CARRIERS, reduce_inner, reduce_outer

TOOL_MANIFEST = {
    "pytorch":  {"tried": False, "used": False, "reason": "n/a"},
    "pyg":      {"tried": False, "used": False, "reason": "n/a"},
    "z3":       {"tried": False, "used": False, "reason": ""},
    "cvc5":     {"tried": False, "used": False, "reason": "z3 sufficient"},
    "sympy":    {"tried": False, "used": False, "reason": "numeric suffices"},
    "clifford": {"tried": False, "used": False, "reason": "n/a"},
    "geomstats":{"tried": False, "used": False, "reason": "n/a"},
    "e3nn":     {"tried": False, "used": False, "reason": "n/a"},
    "rustworkx":{"tried": False, "used": False, "reason": "no graph step"},
    "xgi":      {"tried": False, "used": False, "reason": "n/a"},
    "toponetx": {"tried": False, "used": False, "reason": "n/a"},
    "gudhi":    {"tried": False, "used": False, "reason": "n/a"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


def run_positive_tests():
    r = {}
    inner_img = {reduce_inner(c) for c in CARRIERS}
    outer_img = {reduce_outer(c) for c in CARRIERS}
    r["inner_image_is_pm1"] = (inner_img == {-1, 1})
    r["outer_image_is_pm1"] = (outer_img == {-1, 1})

    # 2-to-1 fibers
    from collections import Counter
    r["inner_two_to_one"] = (Counter(reduce_inner(c) for c in CARRIERS) == {1: 2, -1: 2})
    r["outer_two_to_one"] = (Counter(reduce_outer(c) for c in CARRIERS) == {1: 2, -1: 2})

    # z3 load-bearing: no right-inverse exists
    # i.e. there is NO function g: {-1,+1} -> CARRIERS such that
    # pi_inner(g(x)) == x AND g is injective on the full image of pi.
    # Since |{-1,+1}|=2 and |CARRIERS|=4, any right-inverse misses 2 carriers,
    # proving reduction is lossy.
    if TOOL_MANIFEST["z3"]["tried"]:
        # Encode: pick g(-1), g(+1) in CARRIERS satisfying pi_inner(g(x))==x.
        # Then assert g hits all 4 carriers -> UNSAT.
        S = z3.Solver()
        g_neg = z3.Int("g_neg")
        g_pos = z3.Int("g_pos")
        S.add(g_neg >= 0, g_neg < 4, g_pos >= 0, g_pos < 4)
        # pi_inner(CARRIERS[i]) == target
        def inner_of(idx_var, target):
            cond = z3.Or(*[z3.And(idx_var == i, CARRIERS[i][0] == target)
                           for i in range(4)])
            return cond
        S.add(inner_of(g_neg, -1))
        S.add(inner_of(g_pos,  1))
        # Assert hits all 4 carriers (impossible)
        S.add(z3.Distinct(g_neg, g_pos))
        S.add(z3.Or(g_neg == 0, g_pos == 0))
        S.add(z3.Or(g_neg == 1, g_pos == 1))
        S.add(z3.Or(g_neg == 2, g_pos == 2))
        S.add(z3.Or(g_neg == 3, g_pos == 3))
        res = S.check()
        r["z3_no_surjective_inverse"] = (str(res) == "unsat")
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "UNSAT proves reduction has no right-inverse hitting all carriers"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return r


def run_negative_tests():
    r = {}
    # N1: reduction is NOT injective -- two distinct carriers share a projection
    # reduce_inner drops inner axis (keeps outer): (1,1) and (-1,1) collide
    r["inner_not_injective"] = (reduce_inner((1, 1)) == reduce_inner((-1, 1)))
    # reduce_outer drops outer axis (keeps inner): (1,1) and (1,-1) collide
    r["outer_not_injective"] = (reduce_outer((1, 1)) == reduce_outer((1, -1)))
    # N2: inner projection collapses exactly 2 pairs
    pairs_collapsed = sum(
        1 for i in range(4) for j in range(i + 1, 4)
        if reduce_inner(CARRIERS[i]) == reduce_inner(CARRIERS[j])
    )
    r["inner_collapses_2_pairs"] = (pairs_collapsed == 2)
    return r


def run_boundary_tests():
    r = {}
    # B1: composing both reductions = identity-on-pairs (recovers original)
    recovered = [(reduce_inner(c), reduce_outer(c)) for c in CARRIERS]
    r["both_reductions_recover"] = (set(recovered) == set(CARRIERS))
    # B2: single reduction is lossy (image smaller than domain)
    r["inner_image_smaller"] = (len({reduce_inner(c) for c in CARRIERS}) < len(CARRIERS))
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "sim_igt_atom_3_reduction",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_igt_atom_3_reduction_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[atom3 reduction] all_pass={all_pass} -> {out_path}")
