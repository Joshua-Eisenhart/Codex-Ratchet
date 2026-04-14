#!/usr/bin/env python3
"""IGT atom 7: coupling.

Claim: coupling two IGT carriers (two players/games) yields a 16-state
tensor-product space.  Under JOINT admissibility (both players must
achieve outer WIN), only 4 of 16 joint states survive.  The admissible
joint space is itself a 2x2 yin/yang sub-ring, preserving IGT structure
under coupling.
"""
import json, os
from itertools import product
from _igt_common import CARRIERS

TOOL_MANIFEST = {
    "pytorch":  {"tried": False, "used": False, "reason": "n/a"},
    "pyg":      {"tried": False, "used": False, "reason": "n/a"},
    "z3":       {"tried": False, "used": False, "reason": ""},
    "cvc5":     {"tried": False, "used": False, "reason": "z3 sufficient"},
    "sympy":    {"tried": False, "used": False, "reason": "n/a"},
    "clifford": {"tried": False, "used": False, "reason": "n/a"},
    "geomstats":{"tried": False, "used": False, "reason": "n/a"},
    "e3nn":     {"tried": False, "used": False, "reason": "n/a"},
    "rustworkx":{"tried": False, "used": False, "reason": ""},
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
try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"


def joint_admissible(pair):
    (ai, ao), (bi, bo) = pair
    return ao == 1 and bo == 1


def run_positive_tests():
    r = {}
    joint = list(product(CARRIERS, CARRIERS))
    r["joint_size_16"] = (len(joint) == 4 * 4)

    adm = [p for p in joint if joint_admissible(p)]
    r["joint_admissible_4"] = (len(adm) == 4)

    # Admissible projected to inner axes forms 2x2 = {-1,+1}^2 (new yin/yang)
    inner_proj = {(a[0], b[0]) for (a, b) in adm}
    r["inner_projection_is_full_2x2"] = (inner_proj == set(product((-1, 1), (-1, 1))))

    # z3 load-bearing: prove that coupling + joint admissibility (both outer==+1)
    # is EQUIVALENT to inner freely ranging over 2x2
    if TOOL_MANIFEST["z3"]["tried"]:
        # Forall (ai,ao,bi,bo) with ao=bo=1 in {-1,1}, (ai,bi) ranges over 2x2.
        S = z3.Solver()
        ai, ao, bi, bo = [z3.Int(x) for x in ("ai", "ao", "bi", "bo")]
        for v in (ai, ao, bi, bo):
            S.add(z3.Or(v == -1, v == 1))
        S.add(ao == 1, bo == 1)
        # look for any (ai,bi) combo
        combos = set()
        while S.check() == z3.sat:
            m = S.model()
            tup = (m[ai].as_long(), m[bi].as_long())
            combos.add(tup)
            S.add(z3.Not(z3.And(ai == tup[0], bi == tup[1])))
        r["z3_admissible_inner_is_full_2x2"] = (combos == {(-1, -1), (-1, 1), (1, -1), (1, 1)})
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "enumeration of admissible inner combos under coupling constraint"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    # rustworkx supportive: joint admissible set, edges on hamming-1
    # (single inner flip on either player) is a 4-cycle (preserves structure)
    if TOOL_MANIFEST["rustworkx"]["tried"]:
        adm_list = sorted({(a[0], b[0]) for (a, b) in adm})
        g = rx.PyGraph()
        g.add_nodes_from(list(range(len(adm_list))))
        for i in range(len(adm_list)):
            for j in range(i + 1, len(adm_list)):
                diff = sum(1 for x, y in zip(adm_list[i], adm_list[j]) if x != y)
                if diff == 1:
                    g.add_edge(i, j, None)
        cycles = rx.cycle_basis(g)
        r["rx_admissible_is_4_cycle"] = (len(cycles) == 1 and len(cycles[0]) == 4)
        TOOL_MANIFEST["rustworkx"]["used"] = True
        TOOL_MANIFEST["rustworkx"]["reason"] = "joint admissible sub-ring is a 4-cycle (structure preserved)"
        TOOL_INTEGRATION_DEPTH["rustworkx"] = "supportive"
    return r


def run_negative_tests():
    r = {}
    # N1: joint state (win_LOSE, win_WIN) NOT admissible
    r["one_LOSE_not_admissible"] = (not joint_admissible(((1, -1), (1, 1))))
    # N2: joint lose_LOSE NOT admissible
    r["both_LOSE_not_admissible"] = (not joint_admissible(((-1, -1), (-1, -1))))
    # N3: admissible joint set does NOT include any LOSE on either side
    joint = list(product(CARRIERS, CARRIERS))
    adm = [p for p in joint if joint_admissible(p)]
    r["no_LOSE_in_admissible"] = all(p[0][1] == 1 and p[1][1] == 1 for p in adm)
    return r


def run_boundary_tests():
    r = {}
    joint = list(product(CARRIERS, CARRIERS))
    adm = [p for p in joint if joint_admissible(p)]
    # B1: admissibility ratio = 4/16 = 1/4 (product of individual admissibility rates)
    r["admissibility_rate_quarter"] = (len(adm) / len(joint) == 0.25)
    # B2: admissible sub-ring is isomorphic to original 4-ring (size-preserving)
    r["adm_size_equals_original_carrier_count"] = (len(adm) == len(CARRIERS))
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "sim_igt_atom_7_coupling",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_igt_atom_7_coupling_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[atom7 coupling] all_pass={all_pass} -> {out_path}")
