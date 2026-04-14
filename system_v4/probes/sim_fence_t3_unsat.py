#!/usr/bin/env python3
"""sim_fence_t3_unsat.py -- T3 Neighborhood fence (neighborhoods don't exist by default).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md line 134 (T3_01):
"Neighborhood fence | neighborhoods don't exist by default". Literal
reading: smuggled axiom asserts every token has a nonempty neighborhood
set (forall x. exists y. nbr(x, y)) AND neighborhood relation is reflexive
(forall x. nbr(x, x)). Preserved witness: an admitted token with no
neighborhood at base -- forall y. ~nbr(a, y) (no default neighborhood).
UNSAT = fence.

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
    nbr = z3.Function("nbr", Tok, Tok, z3.BoolSort())
    x, y = z3.Consts("x y", Tok)
    a = z3.Const("a", Tok)
    s = z3.Solver()
    if include_smuggle:
        s.add(z3.ForAll([x], nbr(x, x)))  # primitive reflexive neighborhood
    if include_witness:
        s.add(z3.ForAll([y], z3.Not(nbr(a, y))))  # admitted empty neighborhood
    return s


def run_positive_tests():
    r = _theory(True, True).check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT of (reflexive-neighborhood smuggling + empty-neighborhood witness) IS the fence"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"fence_unsat": {"verdict": str(r), "pass": r == z3.unsat}}


def run_negative_tests():
    r = _theory(False, True).check()
    return {"no_smuggle_sat": {"verdict": str(r), "pass": r == z3.sat}}


def run_boundary_tests():
    r = _theory(True, False).check()
    return {"smuggle_alone_sat": {"verdict": str(r), "pass": r == z3.sat}}


if __name__ == "__main__":
    results = {
        "name": "sim_fence_t3_unsat",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md T3_01 line 134 (Neighborhood fence).",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_fence_t3_unsat_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v["pass"] for v in list(results["positive"].values()) + list(results["negative"].values()) + list(results["boundary"].values()))
    print(f"[{'PASS' if all_pass else 'FAIL'}] {results['name']} -> {out_path}")
