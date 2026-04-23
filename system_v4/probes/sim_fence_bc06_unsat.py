#!/usr/bin/env python3
"""sim_fence_bc06_unsat.py -- BC06 Order ban (no global total order).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md line 116: "BC06 | Order
ban | no global total order; only explicit finite sequencing". Literal
reading: smuggled axiom asserts a global total order <= on all tokens
(reflexive, antisymmetric, transitive, total). Preserved witness: two
tokens admitted as explicitly non-sequenced, i.e. not(a<=b) and not(b<=a).
Totality forbids this; UNSAT = fence.

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
    le = z3.Function("le", Tok, Tok, z3.BoolSort())
    x, y, z = z3.Consts("x y z", Tok)
    a, b = z3.Consts("a b", Tok)
    s = z3.Solver()
    if include_smuggle:
        s.add(z3.ForAll([x], le(x, x)))
        s.add(z3.ForAll([x, y], z3.Implies(z3.And(le(x, y), le(y, x)), x == y)))
        s.add(z3.ForAll([x, y, z], z3.Implies(z3.And(le(x, y), le(y, z)), le(x, z))))
        s.add(z3.ForAll([x, y], z3.Or(le(x, y), le(y, x))))  # totality
    if include_witness:
        s.add(a != b, z3.Not(le(a, b)), z3.Not(le(b, a)))
    return s


def run_positive_tests():
    r = _theory(True, True).check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT of (total-order smuggling + incomparable-witness) IS the fence"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"fence_unsat": {"verdict": str(r), "pass": r == z3.unsat}}


def run_negative_tests():
    r = _theory(False, True).check()
    return {"no_smuggle_sat": {"verdict": str(r), "pass": r == z3.sat}}


def run_boundary_tests():
    r = _theory(True, False).check()
    return {"total_order_alone_sat": {"verdict": str(r), "pass": r == z3.sat}}


if __name__ == "__main__":
    results = {
        "name": "sim_fence_bc06_unsat",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md BC06 line 116 (Order ban).",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_fence_bc06_unsat_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v["pass"] for v in list(results["positive"].values()) + list(results["negative"].values()) + list(results["boundary"].values()))
    print(f"[{'PASS' if all_pass else 'FAIL'}] {results['name']} -> {out_path}")
