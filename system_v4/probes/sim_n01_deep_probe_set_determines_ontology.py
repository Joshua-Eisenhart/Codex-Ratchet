#!/usr/bin/env python3
"""sim_n01_deep_probe_set_determines_ontology -- Adding a probe refines the
quotient S/~_M; it can never coarsen it. z3 load-bearing: UNSAT that a refined
relation is coarser than the original. Also concrete test: partition count
monotone non-decreasing with |M|.
"""
import json, os
from collections import defaultdict

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: TOOL_MANIFEST["z3"]["reason"] = "not installed"


def partition_count(states, probes):
    classes = defaultdict(list)
    for s in states:
        key = tuple(p(s) for p in probes)
        classes[key].append(s)
    return len(classes)


def run_positive_tests():
    S = list(range(8))
    p1 = lambda s: s % 2
    p2 = lambda s: s % 4
    p3 = lambda s: s
    k1 = partition_count(S, [p1])
    k2 = partition_count(S, [p1, p2])
    k3 = partition_count(S, [p1, p2, p3])
    monotone = k1 <= k2 <= k3
    # z3: if a,b indistinguishable under M', they are indistinguishable under M⊆M'
    a,b = z3.Ints("a b")
    m1 = z3.Function("m1", z3.IntSort(), z3.IntSort())
    m2 = z3.Function("m2", z3.IntSort(), z3.IntSort())
    s = z3.Solver()
    # ~_{m1,m2}(a,b) => ~_{m1}(a,b)
    s.add(z3.Not(z3.Implies(z3.And(m1(a)==m1(b), m2(a)==m2(b)), m1(a)==m1(b))))
    r = str(s.check())
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing: UNSAT proves refinement monotonicity"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"counts": [k1,k2,k3], "monotone": monotone, "refinement_check": r,
            "pass": monotone and r == "unsat"}


def run_negative_tests():
    # Claim: adding a probe can REDUCE classes -- must be impossible.
    # Try to find M' ⊃ M with fewer classes: concrete combinatorial check.
    S = list(range(6))
    M = [lambda s: s % 2]
    Mp = M + [lambda s: s // 2]
    kM = partition_count(S, M); kMp = partition_count(S, Mp)
    return {"kM": kM, "kMp": kMp, "reduced": kMp < kM, "pass": not (kMp < kM)}


def run_boundary_tests():
    # Empty probe set: 1 class. Add identity probe: N classes.
    S = list(range(5))
    k0 = partition_count(S, [])
    k1 = partition_count(S, [lambda s: s])
    return {"k0": k0, "k1": k1, "pass": k0 == 1 and k1 == 5}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_deep_probe_set_determines_ontology"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
