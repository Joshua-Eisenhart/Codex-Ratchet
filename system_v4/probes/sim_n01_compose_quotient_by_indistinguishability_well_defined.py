#!/usr/bin/env python3
"""sim_n01_compose_quotient_by_indistinguishability_well_defined -- The quotient
map pi: S -> S/~_M is well-defined iff ~ is an equivalence relation. z3
load-bearing for equivalence axioms; rustworkx supportive (connected components
equal partition classes).
"""
import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: TOOL_MANIFEST["z3"]["reason"] = "not installed"
try:
    import rustworkx as rx; TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError: TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"


def run_positive_tests():
    # z3: axioms refl/sym/trans => equivalence
    a, b, c = z3.Ints("a b c")
    m = z3.Function("m", z3.IntSort(), z3.IntSort())
    s = z3.Solver()
    s.add(z3.Not(z3.And(
        m(a) == m(a),
        z3.Implies(m(a)==m(b), m(b)==m(a)),
        z3.Implies(z3.And(m(a)==m(b), m(b)==m(c)), m(a)==m(c))
    )))
    r = str(s.check())
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing: UNSAT proves equivalence axioms"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    # rustworkx: build graph on S=0..5 with edges=indistinguishable pairs under m(x)=x%2
    g = rx.PyGraph()
    nodes = [g.add_node(i) for i in range(6)]
    for i in range(6):
        for j in range(i+1, 6):
            if i % 2 == j % 2:
                g.add_edge(i, j, None)
    comps = rx.connected_components(g)
    TOOL_MANIFEST["rustworkx"]["used"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = "supportive: connected-components = classes"
    TOOL_INTEGRATION_DEPTH["rustworkx"] = "supportive"
    return {"equiv_axioms": r, "num_components": len(comps),
            "pass": r == "unsat" and len(comps) == 2}


def run_negative_tests():
    # Build non-symmetric "relation" and show it is NOT equivalence (asymmetric pair exists).
    g = rx.PyDiGraph()
    for i in range(4): g.add_node(i)
    g.add_edge(0, 1, None)  # 0->1 but not 1->0
    has_back = g.has_edge(1, 0)
    return {"has_backedge": has_back, "pass": has_back is False}


def run_boundary_tests():
    g = rx.PyGraph(); g.add_node(0)
    return {"single_node_comps": len(rx.connected_components(g)),
            "pass": len(rx.connected_components(g)) == 1}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_compose_quotient_by_indistinguishability_well_defined"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
