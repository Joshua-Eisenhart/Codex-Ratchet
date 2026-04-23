#!/usr/bin/env python3
"""
sim_cvc5_deep_bc05_identity_fence_sibling.py

Sibling of BC04 fence at the BC05 layer. Lego: BC05 smuggled-transitivity
fence. Claim: under BC05, compatibility may be symmetric+reflexive but
NOT transitive. Encoding the smuggled transitivity axiom
  forall x y z. compat(x,y) & compat(y,z) -> compat(x,z)
together with a BC05 witness (compat(A,B), compat(B,C), NOT compat(A,C))
must be UNSAT. That UNSAT IS the fence proof.

Classification: canonical.
"""
import json, os

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "FOL admissibility claim, not numeric"},
    "pyg":     {"tried": False, "used": False, "reason": "no graph message passing"},
    "z3":      {"tried": False, "used": False, "reason": ""},
    "cvc5":    {"tried": False, "used": False, "reason": ""},
    "sympy":   {"tried": False, "used": False, "reason": "not symbolic algebra"},
    "clifford":{"tried": False, "used": False, "reason": "no GA"},
    "geomstats":{"tried": False, "used": False, "reason": "no manifold"},
    "e3nn":    {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx":{"tried": False, "used": False, "reason": "no graph search"},
    "xgi":     {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx":{"tried": False, "used": False, "reason": "no complex"},
    "gudhi":   {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import cvc5
    from cvc5 import Kind
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    cvc5 = None
try:
    import z3 as z3mod
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3mod = None


def _solver():
    tm = cvc5.TermManager(); s = cvc5.Solver(tm)
    s.setOption("produce-models", "true"); s.setLogic("UF")
    return tm, s


def cvc5_bc05_unsat():
    tm, s = _solver()
    Tok = tm.mkUninterpretedSort("Tok")
    compat = tm.mkConst(tm.mkFunctionSort([Tok, Tok], tm.getBooleanSort()), "compat")
    A = tm.mkConst(Tok, "A"); B = tm.mkConst(Tok, "B"); C = tm.mkConst(Tok, "C")
    x = tm.mkVar(Tok,"x"); y = tm.mkVar(Tok,"y"); z = tm.mkVar(Tok,"z")
    c_xy = tm.mkTerm(Kind.APPLY_UF, compat, x, y)
    c_yz = tm.mkTerm(Kind.APPLY_UF, compat, y, z)
    c_xz = tm.mkTerm(Kind.APPLY_UF, compat, x, z)
    body = tm.mkTerm(Kind.IMPLIES, tm.mkTerm(Kind.AND, c_xy, c_yz), c_xz)
    bvl = tm.mkTerm(Kind.VARIABLE_LIST, x, y, z)
    smug = tm.mkTerm(Kind.FORALL, bvl, body)
    s.assertFormula(smug)
    s.assertFormula(tm.mkTerm(Kind.APPLY_UF, compat, A, B))
    s.assertFormula(tm.mkTerm(Kind.APPLY_UF, compat, B, C))
    s.assertFormula(tm.mkTerm(Kind.NOT, tm.mkTerm(Kind.APPLY_UF, compat, A, C)))
    r = s.checkSat()
    return r.isUnsat(), str(r)


def z3_bc05_unsat():
    Tok = z3mod.DeclareSort("Tok")
    compat = z3mod.Function("compat", Tok, Tok, z3mod.BoolSort())
    A,B,C = [z3mod.Const(n, Tok) for n in ("A","B","C")]
    x,y,z = [z3mod.Const(n, Tok) for n in ("x","y","z")]
    s = z3mod.Solver()
    s.add(z3mod.ForAll([x,y,z], z3mod.Implies(z3mod.And(compat(x,y), compat(y,z)), compat(x,z))))
    s.add(compat(A,B)); s.add(compat(B,C)); s.add(z3mod.Not(compat(A,C)))
    return s.check() == z3mod.unsat, str(s.check())


def cvc5_bc05_sat_without_smuggle():
    tm, s = _solver()
    Tok = tm.mkUninterpretedSort("Tok")
    compat = tm.mkConst(tm.mkFunctionSort([Tok, Tok], tm.getBooleanSort()), "compat")
    A = tm.mkConst(Tok, "A"); B = tm.mkConst(Tok, "B"); C = tm.mkConst(Tok, "C")
    s.assertFormula(tm.mkTerm(Kind.APPLY_UF, compat, A, B))
    s.assertFormula(tm.mkTerm(Kind.APPLY_UF, compat, B, C))
    s.assertFormula(tm.mkTerm(Kind.NOT, tm.mkTerm(Kind.APPLY_UF, compat, A, C)))
    r = s.checkSat()
    return r.isSat(), str(r)


def cvc5_bc05_boundary_reflexive_only():
    """Boundary: reflexivity alone doesn't force cross-token compat ->
    a witness with reflexive self-compat and A!=C with NOT compat(A,C)
    must be SAT (fence is not vacuously closed)."""
    tm, s = _solver()
    Tok = tm.mkUninterpretedSort("Tok")
    compat = tm.mkConst(tm.mkFunctionSort([Tok, Tok], tm.getBooleanSort()), "compat")
    A = tm.mkConst(Tok, "A"); C = tm.mkConst(Tok, "C")
    s.assertFormula(tm.mkTerm(Kind.APPLY_UF, compat, A, A))
    s.assertFormula(tm.mkTerm(Kind.APPLY_UF, compat, C, C))
    s.assertFormula(tm.mkTerm(Kind.NOT, tm.mkTerm(Kind.APPLY_UF, compat, A, C)))
    s.assertFormula(tm.mkTerm(Kind.NOT, tm.mkTerm(Kind.EQUAL, A, C)))
    r = s.checkSat()
    return r.isSat(), str(r)


def run_positive_tests():
    ok, v = cvc5_bc05_unsat()
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 UNSAT on smuggled transitivity + BC05 witness IS fence proof"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    out = {"cvc5_bc05_unsat": {"pass": ok, "verdict": v}}
    if z3mod is not None:
        ok2, v2 = z3_bc05_unsat()
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "z3 parity UNSAT"
        TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
        out["z3_parity_unsat"] = {"pass": ok2, "verdict": v2}
    return out

def run_negative_tests():
    ok, v = cvc5_bc05_sat_without_smuggle()
    return {"cvc5_no_smuggle_sat": {"pass": ok, "verdict": v}}

def run_boundary_tests():
    ok, v = cvc5_bc05_boundary_reflexive_only()
    return {"cvc5_reflexive_only_sat": {"pass": ok, "verdict": v}}


if __name__ == "__main__":
    if cvc5 is None:
        print("BLOCKER: cvc5 not importable"); raise SystemExit(2)
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos,**neg,**bnd}.values())
    results = {
        "name": "sim_cvc5_deep_bc05_identity_fence_sibling",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_deep_bc05_identity_fence_sibling_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
