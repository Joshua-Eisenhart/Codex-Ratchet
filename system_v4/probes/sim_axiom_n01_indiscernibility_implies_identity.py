#!/usr/bin/env python3
"""sim_axiom_n01_indiscernibility_implies_identity -- Leibniz closure in M(C).

Canonical sim atomizing the N01 quotient rule: in M(C) = S/~_M, if a,b
agree on ALL m in M then [a] = [b] in Q. Equivalently: the only way to
have [a] != [b] in Q is to exhibit a witnessing m with m(a) != m(b).
z3 is load-bearing: UNSAT when we assert (agreement on all m) AND
([a] != [b]) in the quotient encoding.
"""

import json, os
import numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def run_positive_tests():
    """With a finite M = {m_0, m_1, m_2} and two states a,b agreeing on
    every m_i, the equivalence class map q (a section of S->Q) must send
    them to the same class. Encoded: q(a) = q(b) is SAT when all m_i agree."""
    K = 3
    a, b = z3.Ints("a b")
    m = [z3.Function(f"m_{i}", z3.IntSort(), z3.IntSort()) for i in range(K)]
    q = z3.Function("q", z3.IntSort(), z3.IntSort())
    s = z3.Solver()
    # ~_M axiom: forall x,y: (forall i: m_i(x) = m_i(y)) -> q(x) = q(y)
    x, y = z3.Ints("x y")
    agree = z3.And(*[m[i](x) == m[i](y) for i in range(K)])
    s.add(z3.ForAll([x, y], z3.Implies(agree, q(x) == q(y))))
    # Witness: a,b agree on all m_i
    s.add(*[m[i](a) == m[i](b) for i in range(K)])
    # Must be able to satisfy q(a) = q(b)
    s.add(q(a) == q(b))
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing: encodes ~_M implies q(a)=q(b); checks SAT"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"result": str(s.check()), "pass": str(s.check()) == "sat"}


def run_negative_tests():
    """Violate the axiom: a,b agree on all m_i but q(a) != q(b). UNSAT
    given the ~_M implication axiom."""
    K = 3
    a, b = z3.Ints("a b")
    m = [z3.Function(f"m_{i}", z3.IntSort(), z3.IntSort()) for i in range(K)]
    q = z3.Function("q", z3.IntSort(), z3.IntSort())
    s = z3.Solver()
    x, y = z3.Ints("x y")
    agree = z3.And(*[m[i](x) == m[i](y) for i in range(K)])
    s.add(z3.ForAll([x, y], z3.Implies(agree, q(x) == q(y))))
    s.add(*[m[i](a) == m[i](b) for i in range(K)])
    s.add(q(a) != q(b))
    res = {"indiscernibles_split": str(s.check())}
    res["pass"] = (res["indiscernibles_split"] == "unsat")
    return res


def run_boundary_tests():
    """Numeric instance: 4 states with outcomes under M={m0,m1}. States 0
    and 2 share outcomes. Union-find produces partition respecting
    indiscernibility. torch supportive cross-check."""
    outcomes = torch.tensor([[0, 1],
                             [1, 0],
                             [0, 1],
                             [1, 1]])
    parent = list(range(4))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(x, y):
        parent[find(x)] = find(y)
    for i in range(4):
        for j in range(i + 1, 4):
            if torch.equal(outcomes[i], outcomes[j]):
                union(i, j)
    classes = {find(i) for i in range(4)}
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "supportive: numeric partition cross-check (0 and 2 share class)"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
    merged = find(0) == find(2)
    return {"num_classes": len(classes), "zero_two_merged": merged,
            "pass": merged and len(classes) == 3}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos.get("pass") and neg.get("pass") and bnd.get("pass"))
    results = {
        "name": "sim_axiom_n01_indiscernibility_implies_identity",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_axiom_n01_indiscernibility_implies_identity_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out_path}")
