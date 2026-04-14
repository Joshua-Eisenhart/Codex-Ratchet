#!/usr/bin/env python3
"""
sim_z3_capability.py -- Tool-capability isolation sim for z3.

Governing rule (durable, owner+Hermes 2026-04-13):
z3 is declared load_bearing in many nonclassical-proof sims but has no capability
probe. This is the bounded isolation probe that unblocks z3 for nonclassical use.

Contract:
- Job: encode small classical-forbidden assumptions (commutativity violation,
  non-contextuality violation, KCBS-like inequality bound) and discharge SAT/UNSAT
  to formally witness exclusion/admissibility.
- Minimal bounded task: Bool/Int/Real variables, And/Or/Not/Implies, push/pop,
  check_sat returns sat/unsat deterministically on small encodings.
- Failure modes: version drift (solver name changes), non-determinism on
  under-constrained problems, unknown outcome on nonlinear. Surface here.
- Decorative = `import z3` with no solver.check() result affecting outcome.
  Load-bearing = the sat/unsat verdict IS the claim.
- Baseline = hand-truth-table on tiny propositional problems; z3 must agree.
"""

import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- proof-layer probe"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed"},
    "z3":        {"tried": False, "used": False, "reason": "under test"},
    "cvc5":      {"tried": False, "used": False, "reason": "separate cvc5 probe handles parity"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- pure SMT"},
    "clifford":  {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "geomstats": {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "e3nn":      {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "rustworkx": {"tried": False, "used": False, "reason": "not graph-relevant"},
    "xgi":       {"tried": False, "used": False, "reason": "not graph-relevant"},
    "toponetx":  {"tried": False, "used": False, "reason": "not topology-relevant"},
    "gudhi":     {"tried": False, "used": False, "reason": "not topology-relevant"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None,
    "z3": "load_bearing",
    "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "capability under test -- SAT/UNSAT on small nonclassical encodings"
    Z3_OK = True
    Z3_VERSION = z3.get_version_string()
except Exception as exc:
    Z3_OK = False
    Z3_VERSION = None
    TOOL_MANIFEST["z3"]["reason"] = f"not installed: {exc}"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    r = {}
    if not Z3_OK:
        r["z3_available"] = {"pass": False, "detail": "z3 missing"}
        return r
    r["z3_available"] = {"pass": True, "version": Z3_VERSION}

    # 1. Simple SAT: x and y booleans, x AND y is satisfiable.
    s = z3.Solver()
    x, y = z3.Bools("x y")
    s.add(z3.And(x, y))
    res = s.check()
    r["simple_sat"] = {
        "pass": res == z3.sat and bool(s.model().eval(x)) and bool(s.model().eval(y)),
        "result": str(res),
    }

    # 2. Commutativity violation UNSAT proof.
    # Encode hypothetical classical claim: for bit observables a,b with outcomes
    # +/-1, assume ab = ba always AND correlation E(ab)=-E(ba). This is contradictory.
    s = z3.Solver()
    a, b = z3.Ints("a b")
    s.add(a * a == 1, b * b == 1)              # +/-1 outcomes
    s.add(a * b == b * a)                       # classical commute
    s.add(a * b != b * a)                       # assumed nonclassical
    res_comm = s.check()
    r["commutativity_contradiction_unsat"] = {
        "pass": res_comm == z3.unsat,
        "result": str(res_comm),
        "detail": "commute AND not-commute must be UNSAT",
    }

    # 3. Non-contextuality violation (toy KCBS-like): 5 binary outcomes on a 5-cycle
    # with pairwise-exclusion constraints; classical max of sum = 2, so sum >= 3 is UNSAT.
    s = z3.Solver()
    v = [z3.Int(f"v{i}") for i in range(5)]
    for vi in v:
        s.add(z3.Or(vi == 0, vi == 1))
    # 5-cycle exclusion: adjacent pair cannot both be 1.
    for i in range(5):
        s.add(z3.Not(z3.And(v[i] == 1, v[(i + 1) % 5] == 1)))
    s.add(z3.Sum(v) >= 3)
    res_nc = s.check()
    r["noncontextuality_bound_unsat"] = {
        "pass": res_nc == z3.unsat,
        "result": str(res_nc),
        "detail": "max independent set in C5 is 2; sum>=3 must be UNSAT classically",
    }

    # 4. Push/pop state isolation.
    s = z3.Solver()
    p = z3.Bool("p")
    s.add(p)
    s.push()
    s.add(z3.Not(p))
    after_push = s.check()
    s.pop()
    after_pop = s.check()
    r["push_pop_isolation"] = {
        "pass": after_push == z3.unsat and after_pop == z3.sat,
        "push_result": str(after_push),
        "pop_result": str(after_pop),
    }

    return r


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    r = {}
    if not Z3_OK:
        r["z3_available"] = {"pass": False, "detail": "z3 missing"}
        return r

    # Trivial UNSAT: p AND not p.
    s = z3.Solver()
    p = z3.Bool("p")
    s.add(p, z3.Not(p))
    res = s.check()
    r["contradiction_unsat"] = {
        "pass": res == z3.unsat,
        "result": str(res),
    }

    # SAT formula must not be rejected: p OR not p.
    s = z3.Solver()
    s.add(z3.Or(p, z3.Not(p)))
    res2 = s.check()
    r["tautology_sat"] = {
        "pass": res2 == z3.sat,
        "result": str(res2),
    }

    # Ensure z3 rejects ill-formed: mixing Bool and Int without cast should raise.
    raised = False
    err = None
    try:
        z3.And(z3.Int("i"), z3.Bool("b"))
    except Exception as exc:
        raised = True
        err = type(exc).__name__
    r["ill_formed_raises"] = {
        "pass": raised,
        "error_type": err,
        "detail": "And over Int+Bool must raise",
    }
    return r


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    r = {}
    if not Z3_OK:
        r["z3_available"] = {"pass": False, "detail": "z3 missing"}
        return r

    # Empty solver is SAT (vacuously).
    s = z3.Solver()
    r["empty_solver_sat"] = {"pass": s.check() == z3.sat}

    # Small linear integer system: x+y==10, x-y==4 => x=7, y=3.
    s = z3.Solver()
    x, y = z3.Ints("x y")
    s.add(x + y == 10, x - y == 4)
    res = s.check()
    model_ok = False
    if res == z3.sat:
        m = s.model()
        model_ok = (m[x].as_long() == 7 and m[y].as_long() == 3)
    r["linear_system_solution"] = {
        "pass": res == z3.sat and model_ok,
        "result": str(res),
    }

    # Real arithmetic inequality: x^2 < 0 unsat over reals.
    s = z3.Solver()
    xr = z3.Real("x")
    s.add(xr * xr < 0)
    r["real_nonnegativity_unsat"] = {"pass": s.check() == z3.unsat}

    return r


# =====================================================================
# MAIN
# =====================================================================

def _all_pass(section):
    return all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_z3_capability",
        "purpose": "Tool-capability isolation probe for z3 -- unblocks load-bearing SAT/UNSAT use.",
        "z3_version": Z3_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "witness_file": "system_v4/probes/sim_bridge_chain_integration.py",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "z3_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
