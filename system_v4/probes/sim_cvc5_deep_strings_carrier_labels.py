#!/usr/bin/env python3
"""
sim_cvc5_deep_strings_carrier_labels.py

Deep cvc5 integration via string theory + regex. Lego: carrier label
admissibility. Admissible carriers match regex ^L[0-9]+$ (e.g. L0, L12)
and inadmissible labels contain any non-conforming character or prefix.

Claim 1 (positive, UNSAT): the concrete label "Q7" cannot be admissible
  (s = "Q7" AND s matches ^L[0-9]+$  ->  UNSAT).
Claim 2 (negative, SAT): there exists s matching ^L[0-9]+$
  with length >= 2.
Claim 3 (boundary, SAT): s = "L0" matches ^L[0-9]+$.

cvc5 string + regex theory is the decision procedure.

Classification: canonical.
"""
import json, os

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not numeric"},
    "pyg":     {"tried": False, "used": False, "reason": "no graph"},
    "z3":      {"tried": False, "used": False, "reason": ""},
    "cvc5":    {"tried": False, "used": False, "reason": ""},
    "sympy":   {"tried": False, "used": False, "reason": "no symbolic math"},
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
    s.setOption("produce-models", "true")
    s.setOption("strings-exp", "true")
    s.setOption("tlimit-per", "10000")
    s.setLogic("QF_SLIA")
    return tm, s


def _label_regex(tm):
    """^L[0-9]+$  as  "L" ++ (re.range "0" "9")+"""
    L = tm.mkTerm(Kind.STRING_TO_REGEXP, tm.mkString("L"))
    digit_re = tm.mkTerm(Kind.REGEXP_RANGE, tm.mkString("0"), tm.mkString("9"))
    plus = tm.mkTerm(Kind.REGEXP_PLUS, digit_re)
    return tm.mkTerm(Kind.REGEXP_CONCAT, L, plus)


def cvc5_strings_unsat_Q7_not_admissible():
    """lbl = 'Q7' AND lbl matches ^L[0-9]+$ -> UNSAT."""
    tm, s = _solver()
    S = tm.getStringSort()
    lbl = tm.mkConst(S, "lbl")
    rx = _label_regex(tm)
    s.assertFormula(tm.mkTerm(Kind.STRING_IN_REGEXP, lbl, rx))
    s.assertFormula(tm.mkTerm(Kind.EQUAL, lbl, tm.mkString("Q7")))
    r = s.checkSat()
    return r.isUnsat(), str(r)


def z3_strings_unsat_Q7_not_admissible():
    lbl = z3mod.String("lbl")
    L = z3mod.Re("L")
    digit_re = z3mod.Range("0", "9")
    rx = z3mod.Concat(L, z3mod.Plus(digit_re))
    s = z3mod.Solver()
    s.add(z3mod.InRe(lbl, rx))
    s.add(lbl == z3mod.StringVal("Q7"))
    return s.check() == z3mod.unsat, str(s.check())


def cvc5_strings_len_ge_2_sat():
    """Negative: admissible label with length >= 2 exists (e.g. 'L0')."""
    tm, s = _solver()
    S = tm.getStringSort()
    lbl = tm.mkConst(S, "lbl")
    rx = _label_regex(tm)
    s.assertFormula(tm.mkTerm(Kind.STRING_IN_REGEXP, lbl, rx))
    s.assertFormula(tm.mkTerm(Kind.GEQ,
                              tm.mkTerm(Kind.STRING_LENGTH, lbl),
                              tm.mkInteger(2)))
    s.assertFormula(tm.mkTerm(Kind.LEQ,
                              tm.mkTerm(Kind.STRING_LENGTH, lbl),
                              tm.mkInteger(4)))
    r = s.checkSat()
    return r.isSat(), str(r)


def cvc5_strings_L0_exact_sat():
    """Boundary: 'L0' itself is admissible."""
    tm, s = _solver()
    S = tm.getStringSort()
    lbl = tm.mkConst(S, "lbl")
    rx = _label_regex(tm)
    s.assertFormula(tm.mkTerm(Kind.STRING_IN_REGEXP, lbl, rx))
    s.assertFormula(tm.mkTerm(Kind.EQUAL, lbl, tm.mkString("L0")))
    r = s.checkSat()
    return r.isSat(), str(r)


def run_positive_tests():
    ok, v = cvc5_strings_unsat_Q7_not_admissible()
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 string+regex UNSAT on 'Q7' vs L[0-9]+ IS the exclusion proof"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    out = {"cvc5_str_Q7_unsat": {"pass": ok, "verdict": v}}
    if z3mod is not None:
        try:
            ok2, v2 = z3_strings_unsat_Q7_not_admissible()
            TOOL_MANIFEST["z3"]["used"] = True
            TOOL_MANIFEST["z3"]["reason"] = "z3 string parity UNSAT"
            TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
            out["z3_parity_unsat"] = {"pass": ok2, "verdict": v2}
        except Exception as e:
            out["z3_parity_unsat"] = {"pass": False, "verdict": f"z3 err: {e}"}
    return out

def run_negative_tests():
    ok, v = cvc5_strings_len_ge_2_sat()
    return {"cvc5_len_ge_2_sat": {"pass": ok, "verdict": v}}

def run_boundary_tests():
    ok, v = cvc5_strings_L0_exact_sat()
    return {"cvc5_L0_exact_sat": {"pass": ok, "verdict": v}}


if __name__ == "__main__":
    if cvc5 is None:
        print("BLOCKER: cvc5 not importable"); raise SystemExit(2)
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos,**neg,**bnd}.values())
    results = {
        "name": "sim_cvc5_deep_strings_carrier_labels",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_deep_strings_carrier_labels_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
