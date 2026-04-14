#!/usr/bin/env python3
"""sim_fence_t5_unsat.py -- T5 (no verbatim T5 row; flagged).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md lines 128-141 list
T1/T2/T3/T4/T6/T8 rows; T5 has NO verbatim entry. Flagged as ambiguous.
Most-literal reading adopted: T5 occupies the position between "path
non-collapse" (T4_03, line 136) and identity/scalarization (T6, lines
137-138), so we encode T5 as the complement of T2_03 (Local adjacency
only, line 133): "adjacency is NOT reachability/transitive closure".
Smuggled: forall x y z. adj(x,y) & adj(y,z) -> adj(x,z) (closure).
Witness: adj(a,b) & adj(b,c) & ~adj(a,c). UNSAT = fence.

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
    adj = z3.Function("adj", Tok, Tok, z3.BoolSort())
    x, y, z = z3.Consts("x y z", Tok)
    a, b, c = z3.Consts("a b c", Tok)
    s = z3.Solver()
    if include_smuggle:
        s.add(z3.ForAll([x, y, z], z3.Implies(z3.And(adj(x, y), adj(y, z)), adj(x, z))))
    if include_witness:
        s.add(adj(a, b), adj(b, c), z3.Not(adj(a, c)))
    return s


def run_positive_tests():
    r = _theory(True, True).check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT of (transitive-closure smuggling + local-only witness) IS the fence"
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
        "name": "sim_fence_t5_unsat",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md -- no T5 row verbatim; literal surrogate (T2_03 complement, line 133). Flagged.",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_fence_t5_unsat_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v["pass"] for v in list(results["positive"].values()) + list(results["negative"].values()) + list(results["boundary"].values()))
    print(f"[{'PASS' if all_pass else 'FAIL'}] {results['name']} -> {out_path}")
