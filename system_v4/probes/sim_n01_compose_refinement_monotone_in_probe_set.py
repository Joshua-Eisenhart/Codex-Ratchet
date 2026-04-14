#!/usr/bin/env python3
"""sim_n01_compose_refinement_monotone_in_probe_set -- For M ⊆ M', partition
S/~_{M'} refines S/~_M; class count is non-decreasing in |M|. z3 load-bearing
for the implication; concrete counting supportive.
"""
import json, os
from collections import defaultdict

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: TOOL_MANIFEST["z3"]["reason"] = "not installed"


def count_classes(S, probes):
    c = defaultdict(list)
    for s in S: c[tuple(p(s) for p in probes)].append(s)
    return len(c)


def run_positive_tests():
    # z3: (m1(a)=m1(b) AND m2(a)=m2(b)) => m1(a)=m1(b).
    a, b = z3.Ints("a b")
    m1 = z3.Function("m1", z3.IntSort(), z3.IntSort())
    m2 = z3.Function("m2", z3.IntSort(), z3.IntSort())
    s = z3.Solver()
    s.add(z3.Not(z3.Implies(z3.And(m1(a)==m1(b), m2(a)==m2(b)), m1(a)==m1(b))))
    r = str(s.check())
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing: UNSAT proves refinement monotonicity"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    # Count check
    S = list(range(12))
    ps = [lambda s: s%2, lambda s: s%3, lambda s: s%4]
    counts = [count_classes(S, ps[:k]) for k in range(len(ps)+1)]
    mono = all(counts[i] <= counts[i+1] for i in range(len(counts)-1))
    return {"implication": r, "counts": counts, "monotone": mono,
            "pass": r == "unsat" and mono}


def run_negative_tests():
    S = list(range(8))
    probes_M = [lambda s: s%2, lambda s: s%4]
    probes_Msub = [lambda s: s%4]  # drop one -> subset
    kM = count_classes(S, probes_M); kSub = count_classes(S, probes_Msub)
    # dropping probe should give kSub <= kM
    return {"kM": kM, "kSub": kSub, "pass": kSub <= kM}


def run_boundary_tests():
    S = list(range(5))
    k_empty = count_classes(S, [])
    k_full = count_classes(S, [lambda s: s])
    return {"empty": k_empty, "full": k_full, "pass": k_empty == 1 and k_full == 5}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_compose_refinement_monotone_in_probe_set"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
