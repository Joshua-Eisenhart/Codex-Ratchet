#!/usr/bin/env python3
"""
Leviathan atom 4 of 7: ADMISSIBILITY.

Claim: only reductions that simultaneously satisfy (a) total-carrier
lower bound, (b) diversity lower bound, (c) no-monopoly upper bound are
admissible shells. Encode these as a boolean constraint system and
require UNSAT for the forbidden configurations.

Load-bearing tool: z3 (SMT structural-impossibility proof). This is the
canonical proof form per project doctrine.
"""

import json, os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not a proof tool"},
    "pyg":       {"tried": False, "used": False, "reason": "not used"},
    "z3":        {"tried": False, "used": False, "reason": "SMT UNSAT proof of inadmissibility"},
    "cvc5":      {"tried": False, "used": False, "reason": "cross-check only"},
    "sympy":     {"tried": False, "used": False, "reason": "boolean not symbolic integration"},
    "clifford":  {"tried": False, "used": False, "reason": "not used"},
    "geomstats": {"tried": False, "used": False, "reason": "not used"},
    "e3nn":      {"tried": False, "used": False, "reason": "not used"},
    "rustworkx": {"tried": False, "used": False, "reason": "connectedness is atom 2"},
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


def _admissible(min_total, min_diversity, max_share, carriers_lb):
    """Ask z3 whether an assignment satisfying all constraints exists."""
    s = z3.Solver()
    n = len(carriers_lb)
    xs = [z3.Real(f"x{i}") for i in range(n)]
    for x, lb in zip(xs, carriers_lb):
        s.add(x >= lb)
    total = z3.Sum(xs)
    s.add(total >= min_total)
    # diversity: each agent at least min_diversity * total / n
    for x in xs:
        s.add(x * n >= min_diversity * total)
    # no-monopoly: each agent at most max_share * total
    for x in xs:
        s.add(x <= max_share * total)
    return s.check()


def run_positive_tests():
    if z3 is None: return {"skipped":"z3 missing"}
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    # loose but non-trivial: diversity 0.5, max_share 0.5, total >= 4, n=4
    r = _admissible(min_total=4, min_diversity=0.5, max_share=0.5,
                    carriers_lb=[0,0,0,0])
    return {"balanced_shell_sat": {"z3": str(r), "pass": r == z3.sat}}


def run_negative_tests():
    if z3 is None: return {"skipped":"z3 missing"}
    # monopoly forbidden: require each x <= 0.2 * total but also one agent
    # carries at least 0.9 * total -- must be UNSAT
    s = z3.Solver()
    n = 4
    xs = [z3.Real(f"x{i}") for i in range(n)]
    for x in xs: s.add(x >= 0)
    total = z3.Sum(xs)
    s.add(total > 0)
    for x in xs: s.add(x <= 0.2 * total)
    s.add(xs[0] >= 0.9 * total)
    r = s.check()
    return {"monopoly_unsat": {"z3": str(r), "pass": r == z3.unsat}}


def run_boundary_tests():
    if z3 is None: return {"skipped":"z3 missing"}
    # exactly uniform assignment -- admissible edge
    r = _admissible(min_total=4, min_diversity=1.0, max_share=0.25,
                    carriers_lb=[1,1,1,1])
    return {"uniform_edge_sat": {"z3": str(r), "pass": r == z3.sat}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (pos.get("balanced_shell_sat",{}).get("pass",False)
                and neg.get("monopoly_unsat",{}).get("pass",False)
                and bnd.get("uniform_edge_sat",{}).get("pass",False))
    out = {"name":"leviathan_atom_4_admissibility","classification":"canonical",
           "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
           "positive":pos,"negative":neg,"boundary":bnd,
           "status":"PASS" if all_pass else "FAIL"}
    d = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d,"leviathan_atom_4_admissibility_results.json")
    with open(p,"w") as f: json.dump(out,f,indent=2,default=str)
    print(f"[{out['status']}] {p}")
