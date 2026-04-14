#!/usr/bin/env python3
"""sim_fence_bc12_unsat.py -- BC12 Anti-smuggling (new terms need admissible defs).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md line 122: "BC12 |
Anti-smuggling | new terms need explicit admissible definitions". Literal
reading: smuggled axiom introduces a new predicate Q defined by an
undischarged definition Q(x) <-> Forbidden(x) where Forbidden is any
banned primitive (here: a second-order existence claim "Q collapses to
identity": forall x y. Q(x) & Q(y) -> x = y -- which smuggles BC04).
Preserved witness: two distinct tokens with Q(a) and Q(b). UNSAT = BC12
fence (the smuggled definition is not admissible because it re-introduces
BC04's identity collapse).

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
    Q = z3.Function("Q", Tok, z3.BoolSort())
    x, y = z3.Consts("x y", Tok)
    a, b = z3.Consts("a b", Tok)
    s = z3.Solver()
    if include_smuggle:
        # Q's undischarged "definition" collapses identity under Q
        s.add(z3.ForAll([x, y], z3.Implies(z3.And(Q(x), Q(y)), x == y)))
    if include_witness:
        s.add(a != b, Q(a), Q(b))
    return s


def run_positive_tests():
    r = _theory(True, True).check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT of (smuggled Q-definition + distinct-Q-witness) IS the fence"
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
        "name": "sim_fence_bc12_unsat",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md BC12 line 122 (Anti-smuggling).",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_fence_bc12_unsat_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v["pass"] for v in list(results["positive"].values()) + list(results["negative"].values()) + list(results["boundary"].values()))
    print(f"[{'PASS' if all_pass else 'FAIL'}] {results['name']} -> {out_path}")
