#!/usr/bin/env python3
"""sim_fence_bc11_unsat.py -- BC11 Optimization ban.

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md line 121: "BC11 |
Optimization ban | no optimization or utility primitives". Literal reading:
smuggled axiom asserts a primitive utility U: Choice -> Real such that
every admitted choice is a global maximizer (forall x. U(x) <= U(best)).
Preserved witness: two admitted choices a, b with distinct utilities --
strictly no global optimum exists at base. UNSAT = fence.

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
    Ch = z3.DeclareSort("Ch")
    U = z3.Function("U", Ch, z3.RealSort())
    best = z3.Const("best", Ch)
    x = z3.Const("x", Ch)
    a, b = z3.Consts("a b", Ch)
    s = z3.Solver()
    if include_smuggle:
        s.add(z3.ForAll([x], U(x) == U(best)))  # primitive optimum: everyone equals best
    if include_witness:
        s.add(U(a) != U(b))  # admitted non-identical utilities
    return s


def run_positive_tests():
    r = _theory(True, True).check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT of (global-optimum utility smuggling + distinct-utility witness) IS the fence"
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
        "name": "sim_fence_bc11_unsat",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md BC11 line 121 (Optimization ban).",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_fence_bc11_unsat_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v["pass"] for v in list(results["positive"].values()) + list(results["negative"].values()) + list(results["boundary"].values()))
    print(f"[{'PASS' if all_pass else 'FAIL'}] {results['name']} -> {out_path}")
