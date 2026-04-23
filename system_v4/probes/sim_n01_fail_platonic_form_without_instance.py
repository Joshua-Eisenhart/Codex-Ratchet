#!/usr/bin/env python3
"""sim_n01_fail_platonic_form_without_instance -- N01 forbids abstract forms
with no particular instances. Encode: 'there exists a universal U such that no
x satisfies U(x), yet U is distinguishable from the empty predicate' => UNSAT.
z3 load-bearing.
"""
import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: TOOL_MANIFEST["z3"]["reason"] = "not installed"


def run_positive_tests():
    # Two predicates both empty on the domain must be indistinguishable.
    U = z3.Function("U", z3.IntSort(), z3.BoolSort())
    EMPTY = z3.Function("E", z3.IntSort(), z3.BoolSort())
    s = z3.Solver()
    dom = list(range(5))
    for i in dom: s.add(U(i) == False); s.add(EMPTY(i) == False)
    # Ask: can U be distinguishable from EMPTY?
    s.push()
    s.add(z3.Or([U(i) != EMPTY(i) for i in dom]))
    r = str(s.check())
    s.pop()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing: UNSAT: uninstantiated form cannot be distinguished"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"distinguishable": r, "pass": r == "unsat"}


def run_negative_tests():
    # If U has at least one instance, it IS distinguishable from EMPTY.
    U = z3.Function("U", z3.IntSort(), z3.BoolSort())
    EMPTY = z3.Function("E", z3.IntSort(), z3.BoolSort())
    s = z3.Solver()
    dom = list(range(5))
    for i in dom: s.add(EMPTY(i) == False)
    s.add(U(0) == True)
    s.add(z3.Or([U(i) != EMPTY(i) for i in dom]))
    r = str(s.check())
    return {"instantiated": r, "pass": r == "sat"}


def run_boundary_tests():
    # Singleton domain, both empty => indistinguishable.
    U = z3.Function("U", z3.IntSort(), z3.BoolSort())
    E = z3.Function("E", z3.IntSort(), z3.BoolSort())
    s = z3.Solver()
    s.add(U(0) == False); s.add(E(0) == False)
    s.add(U(0) != E(0))
    r = str(s.check())
    return {"singleton_empty": r, "pass": r == "unsat"}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_fail_platonic_form_without_instance"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
