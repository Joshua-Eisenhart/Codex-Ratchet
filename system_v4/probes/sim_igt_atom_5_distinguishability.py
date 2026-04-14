#!/usr/bin/env python3
"""IGT atom 5: distinguishability.

Claim: probes are partial -- the inner-probe and outer-probe each see
2-element quotients, so pairs of carriers become INDISTINGUISHABLE
under a single probe.  Only the JOINT probe distinguishes all 4.
"""
import json, os
from itertools import combinations
from _igt_common import CARRIERS, distinguishable

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


def run_positive_tests():
    r = {}
    pairs = list(combinations(CARRIERS, 2))

    # Inner probe: 2 distinguishable pairs out of 6 (the ones with different inner)
    inner_dist = sum(1 for a, b in pairs if distinguishable(a, b, "inner"))
    outer_dist = sum(1 for a, b in pairs if distinguishable(a, b, "outer"))
    full_dist  = sum(1 for a, b in pairs if distinguishable(a, b, "full"))

    r["inner_probe_distinguishes_4"] = (inner_dist == 4)
    r["outer_probe_distinguishes_4"] = (outer_dist == 4)
    r["full_probe_distinguishes_all_6"] = (full_dist == 6)

    # P: indistinguishable pairs under inner probe -- exactly 2 (the inner-matched pairs)
    inner_indist = [(a, b) for a, b in pairs if not distinguishable(a, b, "inner")]
    r["inner_two_indistinguishable_pairs"] = (len(inner_indist) == 2)

    # z3 load-bearing: NO single-axis probe can distinguish all 4 carriers
    # (i.e., for either probe choice there exists a pair that collapses)
    if TOOL_MANIFEST["z3"]["tried"]:
        # For each probe in {inner, outer}, there exist distinct a,b in CARRIERS
        # with probe(a)==probe(b).
        results_z3 = {}
        for probe in ("inner", "outer"):
            S = z3.Solver()
            ia, ib = z3.Int("ia"), z3.Int("ib")
            S.add(ia >= 0, ia < 4, ib >= 0, ib < 4, ia != ib)
            eq_terms = []
            for i in range(4):
                for j in range(4):
                    if i != j:
                        ai = CARRIERS[i][0] if probe == "inner" else CARRIERS[i][1]
                        aj = CARRIERS[j][0] if probe == "inner" else CARRIERS[j][1]
                        if ai == aj:
                            eq_terms.append(z3.And(ia == i, ib == j))
            S.add(z3.Or(*eq_terms))
            results_z3[probe] = (str(S.check()) == "sat")
        r["z3_inner_collapses_some_pair"] = results_z3["inner"]
        r["z3_outer_collapses_some_pair"] = results_z3["outer"]
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "SAT witness shows each partial probe is insufficient"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return r


def run_negative_tests():
    r = {}
    # N1: (1,1) and (1,-1) are indistinguishable under inner probe
    r["winWIN_winLOSE_indist_inner"] = (not distinguishable((1, 1), (1, -1), "inner"))
    # N2: (1,1) and (-1,1) are indistinguishable under outer probe
    r["winWIN_loseWIN_indist_outer"] = (not distinguishable((1, 1), (-1, 1), "outer"))
    # N3: but both are distinguishable under full probe
    r["full_probe_sees_all"] = all(
        distinguishable(a, b, "full")
        for a, b in combinations(CARRIERS, 2)
    )
    return r


def run_boundary_tests():
    r = {}
    # B1: identity is never distinguishable from itself
    r["identity_indist_full"] = (not distinguishable((1, 1), (1, 1), "full"))
    # B2: invalid probe raises
    try:
        distinguishable((1, 1), (1, -1), "bogus")
        r["invalid_probe_raises"] = False
    except ValueError:
        r["invalid_probe_raises"] = True
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "sim_igt_atom_5_distinguishability",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_igt_atom_5_distinguishability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[atom5 distinguishability] all_pass={all_pass} -> {out_path}")
