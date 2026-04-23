#!/usr/bin/env python3
"""sim_fence_t7_cvc5_parity.py -- T7 (no verbatim T7 row; cvc5 load-bearing).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md lines 128-141 list
T1/T2/T3/T4/T6/T8; T7 has NO verbatim entry. Flagged as ambiguous.
Most-literal reading adopted: T7 sits between T6 (anti-identity/
anti-scalarization) and T8 (anti-geometry). Encoded as complement of
T6_03 (Anti-scalarization, line 138): "no scalar rank/distance from
topology". Smuggled: primitive rank: Tok -> Int, with rank-order
coinciding with adjacency (forall x y. adj(x,y) -> rank(x) < rank(y) or
rank(y) < rank(x) -- adjacency forces distinguishing rank). Witness:
adj(a,b) AND rank(a) == rank(b). UNSAT via cvc5 = fence. cvc5 is the
load-bearing solver (z3 used only as parity cross-check).

classification: canonical
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _fence_unsat_common import fresh_manifest

TOOL_MANIFEST = fresh_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import cvc5
    from cvc5 import Kind
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    cvc5 = None
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed -- BLOCKER"

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3 = None
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


def _cvc5_check(include_witness=True, include_smuggle=True):
    tm = cvc5.TermManager()
    s = cvc5.Solver(tm)
    s.setOption("produce-models", "true")
    s.setLogic("UFLIA")
    Tok = tm.mkUninterpretedSort("Tok")
    Bool = tm.getBooleanSort(); Int = tm.getIntegerSort()
    adj = tm.mkConst(tm.mkFunctionSort([Tok, Tok], Bool), "adj")
    rank = tm.mkConst(tm.mkFunctionSort([Tok], Int), "rank")
    a = tm.mkConst(Tok, "a"); b = tm.mkConst(Tok, "b")
    if include_smuggle:
        x = tm.mkVar(Tok, "x"); y = tm.mkVar(Tok, "y")
        ax_lhs = tm.mkTerm(Kind.APPLY_UF, adj, x, y)
        rx = tm.mkTerm(Kind.APPLY_UF, rank, x)
        ry = tm.mkTerm(Kind.APPLY_UF, rank, y)
        lt1 = tm.mkTerm(Kind.LT, rx, ry)
        lt2 = tm.mkTerm(Kind.LT, ry, rx)
        ax_rhs = tm.mkTerm(Kind.OR, lt1, lt2)
        body = tm.mkTerm(Kind.IMPLIES, ax_lhs, ax_rhs)
        bvl = tm.mkTerm(Kind.VARIABLE_LIST, x, y)
        s.assertFormula(tm.mkTerm(Kind.FORALL, bvl, body))
    if include_witness:
        s.assertFormula(tm.mkTerm(Kind.APPLY_UF, adj, a, b))
        ra = tm.mkTerm(Kind.APPLY_UF, rank, a)
        rb = tm.mkTerm(Kind.APPLY_UF, rank, b)
        s.assertFormula(tm.mkTerm(Kind.EQUAL, ra, rb))
    r = s.checkSat()
    return "unsat" if r.isUnsat() else ("sat" if r.isSat() else "unknown")


def _z3_check(include_witness=True, include_smuggle=True):
    Tok = z3.DeclareSort("Tok")
    adj = z3.Function("adj", Tok, Tok, z3.BoolSort())
    rank = z3.Function("rank", Tok, z3.IntSort())
    x, y = z3.Consts("x y", Tok)
    a, b = z3.Consts("a b", Tok)
    s = z3.Solver()
    if include_smuggle:
        s.add(z3.ForAll([x, y], z3.Implies(adj(x, y), z3.Or(rank(x) < rank(y), rank(y) < rank(x)))))
    if include_witness:
        s.add(adj(a, b), rank(a) == rank(b))
    r = s.check()
    return "unsat" if r == z3.unsat else ("sat" if r == z3.sat else "unknown")


def run_positive_tests():
    v_cvc5 = _cvc5_check(True, True)
    v_z3 = _z3_check(True, True)
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "UNSAT of (rank-distinguishes-adjacency smuggling + equal-rank adjacent witness) IS the fence"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "parity cross-check of cvc5 UNSAT verdict"
    TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
    return {
        "cvc5_fence_unsat": {"verdict": v_cvc5, "pass": v_cvc5 == "unsat"},
        "z3_parity_unsat": {"verdict": v_z3, "pass": v_z3 == "unsat"},
        "parity_match": {"pass": v_cvc5 == v_z3},
    }


def run_negative_tests():
    v = _cvc5_check(include_witness=True, include_smuggle=False)
    return {"cvc5_witness_only_sat": {"verdict": v, "pass": v == "sat"}}


def run_boundary_tests():
    # cvc5 returns 'unknown' on quantifier-only (no model finder trigger);
    # use z3 for this parity branch, which handles the existential model.
    v = _z3_check(include_witness=False, include_smuggle=True)
    return {"z3_smuggle_only_sat": {"verdict": v, "pass": v == "sat"}}


if __name__ == "__main__":
    results = {
        "name": "sim_fence_t7_cvc5_parity",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md -- no T7 row verbatim; literal surrogate (T6_03 rank/scalarization, line 138). Flagged.",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    # Re-run negative/boundary labels correctly (witness-only means no smuggle+witness contradiction)
    # Actually: _cvc5_check(True, False) includes smuggle only (False=no witness) -> SAT expected
    #          _cvc5_check(False, True) includes witness only (False=no smuggle) -> SAT expected
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_fence_t7_cvc5_parity_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v["pass"] for v in list(results["positive"].values()) + list(results["negative"].values()) + list(results["boundary"].values()))
    print(f"[{'PASS' if all_pass else 'FAIL'}] {results['name']} -> {out_path}")
