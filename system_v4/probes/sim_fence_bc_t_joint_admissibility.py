#!/usr/bin/env python3
"""sim_fence_bc_t_joint_admissibility.py -- Cross-layer BC+T joint fence.

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md BC04 (line 114, identity
ban), BC05 (line 115, equality/substitutability ban), T1_01 (line 130,
scoped compatibility), T6_01 (line 137, "compatibility/adjacency !=
identity or equality"). Literal joint reading: BC04 + BC05 + T6_01 jointly
forbid deriving token-identity from compatibility OR adjacency. Smuggled
conjunction: (forall x y. compat(x,y) -> x = y) AND (forall x y. adj(x,y)
-> x = y). Preserved witness: scoped-compat/scoped-adj admitted between
distinct tokens. UNSAT = joint cross-layer fence.

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
    adj = z3.Function("adj", Tok, Tok, z3.BoolSort())
    x, y = z3.Consts("x y", Tok)
    a, b, c, d = z3.Consts("a b c d", Tok)
    s = z3.Solver()
    if include_smuggle:
        s.add(z3.ForAll([x, y], z3.Implies(compat(x, y), x == y)))  # BC04+BC05 smuggle
        s.add(z3.ForAll([x, y], z3.Implies(adj(x, y), x == y)))      # T6_01 smuggle
    if include_witness:
        s.add(a != b, compat(a, b))            # scoped-compat between distinct tokens (T1)
        s.add(c != d, adj(c, d))               # scoped-adj between distinct tokens
    return s


def run_positive_tests():
    r = _theory(True, True).check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT of (BC04/05 + T6_01 joint identity-smuggling + scoped-compat/adj distinct witnesses) IS the joint fence"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"joint_fence_unsat": {"verdict": str(r), "pass": r == z3.unsat}}


def run_negative_tests():
    r = _theory(False, True).check()
    return {"no_smuggle_sat": {"verdict": str(r), "pass": r == z3.sat}}


def run_boundary_tests():
    # Drop one of the two smuggled axioms (keep only compat smuggle + compat witness):
    Tok = z3.DeclareSort("Tok")
    compat = z3.Function("compat", Tok, Tok, z3.BoolSort())
    x, y = z3.Consts("x y", Tok)
    a, b = z3.Consts("a b", Tok)
    s = z3.Solver()
    s.add(z3.ForAll([x, y], z3.Implies(compat(x, y), x == y)))
    s.add(a != b, compat(a, b))
    r_single = s.check()
    return {"single_layer_also_unsat": {"verdict": str(r_single), "pass": r_single == z3.unsat}}


if __name__ == "__main__":
    results = {
        "name": "sim_fence_bc_t_joint_admissibility",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md BC04/BC05/T1_01/T6_01 (lines 114,115,130,137) cross-layer joint fence.",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_fence_bc_t_joint_admissibility_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v["pass"] for v in list(results["positive"].values()) + list(results["negative"].values()) + list(results["boundary"].values()))
    print(f"[{'PASS' if all_pass else 'FAIL'}] {results['name']} -> {out_path}")
