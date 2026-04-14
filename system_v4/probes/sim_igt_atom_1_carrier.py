#!/usr/bin/env python3
"""IGT atom 1: carrier.

Claim: the IGT carrier set is exactly the 4-element product
{win,lose} x {WIN,LOSE} = {-1,+1}^2 -- nothing more, nothing less.
"""
import json, os, itertools
import numpy as np
from _igt_common import CARRIERS, LABELS

TOOL_MANIFEST = {
    "pytorch":  {"tried": False, "used": False, "reason": "not needed -- 4-element finite set"},
    "pyg":      {"tried": False, "used": False, "reason": "no graph yet (atom 1)"},
    "z3":       {"tried": False, "used": False, "reason": ""},
    "cvc5":     {"tried": False, "used": False, "reason": "z3 sufficient"},
    "sympy":    {"tried": False, "used": False, "reason": "no symbolic manipulation"},
    "clifford": {"tried": False, "used": False, "reason": "geometry deferred to atom 6"},
    "geomstats":{"tried": False, "used": False, "reason": "n/a"},
    "e3nn":     {"tried": False, "used": False, "reason": "n/a"},
    "rustworkx":{"tried": False, "used": False, "reason": "no graph"},
    "xgi":      {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no complex"},
    "gudhi":    {"tried": False, "used": False, "reason": "no filtration"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
try:
    import numpy  # baseline
except ImportError:
    pass


def run_positive_tests():
    r = {}
    # P1: carrier count = 4
    r["carrier_count_eq_4"] = (len(CARRIERS) == 4)
    # P2: all carriers are in {-1,+1}^2
    r["carriers_in_signs_squared"] = all(
        a in (-1, 1) and b in (-1, 1) for (a, b) in CARRIERS
    )
    # P3: uniqueness
    r["carriers_unique"] = (len(set(CARRIERS)) == 4)
    # P4: labels cover all carriers
    r["labels_cover"] = (set(LABELS.keys()) == set(CARRIERS))

    # P5: z3 load-bearing -- there is NO 5th (a,b) with a,b in {-1,+1}
    # distinct from the 4 carriers.
    if TOOL_MANIFEST["z3"]["tried"]:
        a, b = z3.Int("a"), z3.Int("b")
        s = z3.Solver()
        s.add(z3.Or(a == -1, a == 1))
        s.add(z3.Or(b == -1, b == 1))
        # force distinct from all 4 carriers
        for (x, y) in CARRIERS:
            s.add(z3.Not(z3.And(a == x, b == y)))
        res = s.check()
        r["z3_no_fifth_carrier"] = (str(res) == "unsat")
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "UNSAT proves carrier set is exhaustive"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return r


def run_negative_tests():
    r = {}
    # N1: (0,0) is NOT a valid carrier
    r["zero_not_carrier"] = ((0, 0) not in CARRIERS)
    # N2: three-valued axis rejected
    r["three_valued_rejected"] = ((2, 1) not in CARRIERS)
    # N3: duplicate injection fails uniqueness
    bogus = CARRIERS + [CARRIERS[0]]
    r["duplicate_breaks_uniqueness"] = (len(set(bogus)) != len(bogus))
    return r


def run_boundary_tests():
    r = {}
    # B1: cardinality = 2^2
    r["cardinality_is_2_to_2"] = (len(CARRIERS) == 2 ** 2)
    # B2: sum of all carriers = (0,0) (balanced yin/yang)
    s = tuple(np.sum(np.array(CARRIERS), axis=0).tolist())
    r["sum_is_zero"] = (s == (0, 0))
    # B3: product of all components per axis = +1 (paired)
    prods = np.prod(np.array(CARRIERS), axis=0).tolist()
    r["axis_products_plus1"] = (prods == [1, 1])
    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "sim_igt_atom_1_carrier",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_igt_atom_1_carrier_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[atom1 carrier] all_pass={all_pass} -> {out_path}")
