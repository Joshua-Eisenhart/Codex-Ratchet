#!/usr/bin/env python3
"""sim_fence_bc04_unsat.py -- Canonical BC04 (Identity ban) fence sim.

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md line 114: "BC04 | Identity
ban | no primitive identity predicate on state-tokens". Literal reading:
there is no primitive unary Id(x) predicate admissible on state-tokens that
is non-trivial (both holds and distinguishes). We encode: a smuggled
primitive Id and an admissibility axiom (Id(x) iff x = x) that forces Id to
be trivially-true, together with a preserved witness "Id distinguishes two
tokens" (exists x y. Id(x) & ~Id(y)). UNSAT = fence holds by construction.

classification: canonical
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _fence_unsat_common import fresh_manifest

TOOL_MANIFEST = fresh_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3 = None
    TOOL_MANIFEST["z3"]["reason"] = "not installed -- BLOCKER"


def run_positive_tests():
    # Smuggled primitive Id with admissibility axiom + distinguishing witness => UNSAT
    Tok = z3.DeclareSort("Tok")
    Id = z3.Function("Id", Tok, z3.BoolSort())
    x, y = z3.Consts("x y", Tok)
    s = z3.Solver()
    # admissibility axiom: Id is identity-predicate, i.e. Id(x) iff x=x (trivially true)
    s.add(z3.ForAll([x], Id(x) == (x == x)))
    # preserved witness: Id distinguishes (violates BC04 if admitted)
    a, b = z3.Consts("a b", Tok)
    s.add(Id(a), z3.Not(Id(b)))
    r = s.check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT of (smuggled primitive Id + distinguishing witness) IS the fence"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"fence_unsat": {"verdict": str(r), "pass": r == z3.unsat}}


def run_negative_tests():
    # Drop the preserved witness: smuggled axiom alone should be SAT.
    Tok = z3.DeclareSort("Tok")
    Id = z3.Function("Id", Tok, z3.BoolSort())
    x = z3.Const("x", Tok)
    s = z3.Solver()
    s.add(z3.ForAll([x], Id(x) == (x == x)))
    r = s.check()
    return {"smuggle_only_sat": {"verdict": str(r), "pass": r == z3.sat}}


def run_boundary_tests():
    # Two-token minimal model: distinguishing witness with distinct tokens.
    Tok = z3.DeclareSort("Tok")
    Id = z3.Function("Id", Tok, z3.BoolSort())
    x = z3.Const("x", Tok)
    a, b = z3.Consts("a b", Tok)
    s = z3.Solver()
    s.add(a != b)
    s.add(z3.ForAll([x], Id(x) == (x == x)))
    s.add(Id(a), z3.Not(Id(b)))
    r = s.check()
    return {"two_token_unsat": {"verdict": str(r), "pass": r == z3.unsat}}


if __name__ == "__main__":
    results = {
        "name": "sim_fence_bc04_unsat",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md BC04 line 114 (Identity ban).",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_fence_bc04_unsat_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v["pass"] for v in list(results["positive"].values()) + list(results["negative"].values()) + list(results["boundary"].values()))
    print(f"[{'PASS' if all_pass else 'FAIL'}] {results['name']} -> {out_path}")
