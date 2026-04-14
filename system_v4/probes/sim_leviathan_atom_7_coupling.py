#!/usr/bin/env python3
"""
Leviathan atom 7 of 7: COUPLING.

Claim: two admissible shells coexist iff their joint carrier, structure,
reduction, admissibility, and chirality remain simultaneously satisfiable.
A destructive coupling (e.g., one shell forces monopoly while the other
forbids it) must be UNSAT -- the shells cannot coexist.

Load-bearing tool: z3 (joint SMT system over two shells' admissibility
constraints). This is the shell-coupling canonical form: per project
doctrine, coupling is the probe that decides shell membership.
"""

import json, os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "numeric feasibility is secondary"},
    "pyg":       {"tried": False, "used": False, "reason": "not used"},
    "z3":        {"tried": False, "used": False, "reason": "joint admissibility SMT"},
    "cvc5":      {"tried": False, "used": False, "reason": "redundant cross-check"},
    "sympy":     {"tried": False, "used": False, "reason": "not used"},
    "clifford":  {"tried": False, "used": False, "reason": "not used"},
    "geomstats": {"tried": False, "used": False, "reason": "not used"},
    "e3nn":      {"tried": False, "used": False, "reason": "not used"},
    "rustworkx": {"tried": False, "used": False, "reason": "structure atoms handle graphs"},
    "xgi":       {"tried": False, "used": False, "reason": "not used"},
    "toponetx":  {"tried": False, "used": False, "reason": "not used"},
    "gudhi":     {"tried": False, "used": False, "reason": "not used"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3 = None
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


def _joint(shellA_constraints, shellB_constraints):
    s = z3.Solver()
    a = [z3.Real(f"a{i}") for i in range(4)]
    b = [z3.Real(f"b{i}") for i in range(4)]
    for x in a+b: s.add(x >= 0)
    s.add(z3.Sum(a) > 0); s.add(z3.Sum(b) > 0)
    shellA_constraints(s, a)
    shellB_constraints(s, b)
    return s.check()


def _balanced(s, xs):
    total = z3.Sum(xs)
    for x in xs: s.add(x * len(xs) >= 0.5 * total)
    for x in xs: s.add(x <= 0.5 * total)


def _monopoly_required(s, xs):
    total = z3.Sum(xs)
    s.add(xs[0] >= 0.9 * total)


def _monopoly_forbidden(s, xs):
    total = z3.Sum(xs)
    for x in xs: s.add(x <= 0.3 * total)


def run_positive_tests():
    if z3 is None: return {"skipped":"z3 missing"}
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    r = _joint(_balanced, _balanced)
    return {"two_balanced_shells_coexist": {"z3": str(r), "pass": r == z3.sat}}


def run_negative_tests():
    if z3 is None: return {"skipped":"z3 missing"}
    # Shell A forbids monopoly; Shell B requires it. Since they are
    # separate, they could coexist -- but if we couple them (same agents),
    # coupling is UNSAT.
    s = z3.Solver()
    xs = [z3.Real(f"x{i}") for i in range(4)]
    for x in xs: s.add(x >= 0)
    s.add(z3.Sum(xs) > 0)
    _monopoly_forbidden(s, xs)
    _monopoly_required(s, xs)
    r = s.check()
    return {"destructive_coupling_unsat": {"z3": str(r), "pass": r == z3.unsat}}


def run_boundary_tests():
    if z3 is None: return {"skipped":"z3 missing"}
    # Trivial coupling: one shell with no extra constraints -- should be SAT
    r = _joint(_balanced, lambda s, xs: None)
    return {"trivial_coupling_sat": {"z3": str(r), "pass": r == z3.sat}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (pos.get("two_balanced_shells_coexist",{}).get("pass",False)
                and neg.get("destructive_coupling_unsat",{}).get("pass",False)
                and bnd.get("trivial_coupling_sat",{}).get("pass",False))
    out = {"name":"leviathan_atom_7_coupling","classification":"canonical",
           "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
           "positive":pos,"negative":neg,"boundary":bnd,
           "status":"PASS" if all_pass else "FAIL"}
    d = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d,"leviathan_atom_7_coupling_results.json")
    with open(p,"w") as f: json.dump(out,f,indent=2,default=str)
    print(f"[{out['status']}] {p}")
