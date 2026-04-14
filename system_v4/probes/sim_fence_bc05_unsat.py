#!/usr/bin/env python3
"""sim_fence_bc05_unsat.py -- BC05 Equality-as-substitutability ban.

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md line 115: "BC05 | Equality
ban | no primitive equality-as-substitutability". Literal reading:
compatibility (~) does not license substitutability under an arbitrary
predicate P. Smuggled axiom: forall x y. x ~ y -> (P(x) <-> P(y)). Witness:
a ~ b AND P(a) AND not P(b). UNSAT = fence.

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


def _theory(include_witness=True, include_smuggle=True):
    Tok = z3.DeclareSort("Tok")
    compat = z3.Function("compat", Tok, Tok, z3.BoolSort())
    P = z3.Function("P", Tok, z3.BoolSort())
    x, y = z3.Consts("x y", Tok)
    a, b = z3.Consts("a b", Tok)
    s = z3.Solver()
    if include_smuggle:
        s.add(z3.ForAll([x, y], z3.Implies(compat(x, y), P(x) == P(y))))
    if include_witness:
        s.add(compat(a, b), P(a), z3.Not(P(b)))
    return s


def run_positive_tests():
    r = _theory(True, True).check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT of (substitutability axiom + distinguishing witness) IS the fence"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"fence_unsat": {"verdict": str(r), "pass": r == z3.unsat}}


def run_negative_tests():
    r = _theory(False, True).check()
    return {"no_smuggle_sat": {"verdict": str(r), "pass": r == z3.sat}}


def run_boundary_tests():
    r = _theory(True, False).check()
    return {"no_witness_sat": {"verdict": str(r), "pass": r == z3.sat}}


if __name__ == "__main__":
    results = {
        "name": "sim_fence_bc05_unsat",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md BC05 line 115 (Equality ban).",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_fence_bc05_unsat_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v["pass"] for v in list(results["positive"].values()) + list(results["negative"].values()) + list(results["boundary"].values()))
    print(f"[{'PASS' if all_pass else 'FAIL'}] {results['name']} -> {out_path}")
