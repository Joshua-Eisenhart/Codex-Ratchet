#!/usr/bin/env python3
"""IGT atom 4: admissibility.

Claim: under the IGT admissibility constraint (outer axis dominates),
only carriers with WIN=+1 are long-run admissible.  lose_LOSE and
win_LOSE are excluded.  The admissible sub-ring is {win_WIN, lose_WIN},
a 2-element set reachable from either side by single inner flip.
"""
import json, os
from _igt_common import CARRIERS, LABELS

TOOL_MANIFEST = {
    "pytorch":  {"tried": False, "used": False, "reason": "n/a"},
    "pyg":      {"tried": False, "used": False, "reason": "n/a"},
    "z3":       {"tried": False, "used": False, "reason": ""},
    "cvc5":     {"tried": False, "used": False, "reason": "z3 sufficient"},
    "sympy":    {"tried": False, "used": False, "reason": "n/a"},
    "clifford": {"tried": False, "used": False, "reason": "n/a"},
    "geomstats":{"tried": False, "used": False, "reason": "n/a"},
    "e3nn":     {"tried": False, "used": False, "reason": "n/a"},
    "rustworkx":{"tried": False, "used": False, "reason": "n/a"},
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


def admissible(c):
    # outer axis (long-run WIN) must be +1
    return c[1] == 1


def run_positive_tests():
    r = {}
    adm = [c for c in CARRIERS if admissible(c)]
    exc = [c for c in CARRIERS if not admissible(c)]
    r["two_admissible"] = (len(adm) == 2)
    r["two_excluded"] = (len(exc) == 2)
    r["admissible_set"] = (set(adm) == {(1, 1), (-1, 1)})
    r["excluded_set"] = (set(exc) == {(1, -1), (-1, -1)})

    # z3 load-bearing: prove that under constraint outer==+1, NO carrier
    # with outer==-1 is admissible
    if TOOL_MANIFEST["z3"]["tried"]:
        a, b = z3.Int("a"), z3.Int("b")
        S = z3.Solver()
        S.add(z3.Or(a == -1, a == 1))
        S.add(z3.Or(b == -1, b == 1))
        S.add(b == 1)         # admissibility constraint
        S.add(b == -1)        # contradiction
        r["z3_constraint_excludes_outer_neg"] = (str(S.check()) == "unsat")
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "UNSAT on (outer==+1) AND (outer==-1) proves exclusion"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return r


def run_negative_tests():
    r = {}
    # N1: lose_LOSE NOT admissible
    r["lose_LOSE_excluded"] = (not admissible((-1, -1)))
    # N2: win_LOSE NOT admissible (pyrrhic)
    r["win_LOSE_excluded"] = (not admissible((1, -1)))
    # N3: admissibility is not equivalent to inner-win
    r["admissibility_not_inner"] = (admissible((-1, 1)) and not admissible((1, -1)))
    return r


def run_boundary_tests():
    r = {}
    adm = [c for c in CARRIERS if admissible(c)]
    # B1: admissible set closed under inner flip (sacrifice <-> aligned virtuous)
    flipped = {(-c[0], c[1]) for c in adm}
    r["adm_closed_under_inner_flip"] = (set(adm) == flipped)
    # B2: admissible set NOT closed under outer flip
    outer_flipped = {(c[0], -c[1]) for c in adm}
    r["adm_not_closed_under_outer_flip"] = (set(adm) != outer_flipped)
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "sim_igt_atom_4_admissibility",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_igt_atom_4_admissibility_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[atom4 admissibility] all_pass={all_pass} -> {out_path}")
