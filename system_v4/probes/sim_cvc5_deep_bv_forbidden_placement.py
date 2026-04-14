#!/usr/bin/env python3
"""
sim_cvc5_deep_bv_forbidden_placement.py

Deep cvc5 integration via bit-vector theory (QF_BV). Lego: an 8-bit
state carrier with a forbidden placement pattern. Rules:
  (a) population-count(state) must be even (parity rule), and
  (b) bits 0 and 7 must not both be set (endpoint exclusion).
Claim: there exists NO 8-bit state with popcount=3 that also satisfies
(a) (contradiction: 3 is odd). cvc5 QF_BV must return UNSAT.

Negative: popcount=2 with endpoints forbidden -> SAT (many models).
Boundary: the all-zero state satisfies parity AND endpoint rule -> SAT.

Classification: canonical (bit-vector decision procedure is load-bearing).
"""
import json, os

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not a numeric tensor claim"},
    "pyg":     {"tried": False, "used": False, "reason": "no graph"},
    "z3":      {"tried": False, "used": False, "reason": ""},
    "cvc5":    {"tried": False, "used": False, "reason": ""},
    "sympy":   {"tried": False, "used": False, "reason": "no symbolic algebra"},
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
    s.setOption("produce-models", "true"); s.setLogic("QF_BV")
    return tm, s


def _bit(tm, state, i, bv8):
    """Extract bit i as a 1-bit BV."""
    # cvc5 extract op takes (high, low)
    ext_op = tm.mkOp(Kind.BITVECTOR_EXTRACT, i, i)
    return tm.mkTerm(ext_op, state)


def _popcount_eq(tm, state, target):
    """Build sum of zero-extended bits and compare equal to target (as 8-bit)."""
    bits = []
    for i in range(8):
        b = _bit(tm, state, i, 8)
        # zero-extend 1-bit to 8-bit
        ze_op = tm.mkOp(Kind.BITVECTOR_ZERO_EXTEND, 7)
        bits.append(tm.mkTerm(ze_op, b))
    total = bits[0]
    for b in bits[1:]:
        total = tm.mkTerm(Kind.BITVECTOR_ADD, total, b)
    return tm.mkTerm(Kind.EQUAL, total, tm.mkBitVector(8, target))


def _parity_even(tm, state):
    """popcount mod 2 == 0."""
    bits = []
    for i in range(8):
        b = _bit(tm, state, i, 8)
        ze_op = tm.mkOp(Kind.BITVECTOR_ZERO_EXTEND, 7)
        bits.append(tm.mkTerm(ze_op, b))
    total = bits[0]
    for b in bits[1:]:
        total = tm.mkTerm(Kind.BITVECTOR_ADD, total, b)
    two = tm.mkBitVector(8, 2)
    rem = tm.mkTerm(Kind.BITVECTOR_UREM, total, two)
    return tm.mkTerm(Kind.EQUAL, rem, tm.mkBitVector(8, 0))


def _endpoints_not_both(tm, state):
    """NOT (bit0 == 1 AND bit7 == 1)."""
    b0 = _bit(tm, state, 0, 8)
    b7 = _bit(tm, state, 7, 8)
    one1 = tm.mkBitVector(1, 1)
    both = tm.mkTerm(Kind.AND,
                     tm.mkTerm(Kind.EQUAL, b0, one1),
                     tm.mkTerm(Kind.EQUAL, b7, one1))
    return tm.mkTerm(Kind.NOT, both)


def cvc5_bv_forbidden_unsat():
    tm, s = _solver()
    BV8 = tm.mkBitVectorSort(8)
    st = tm.mkConst(BV8, "st")
    s.assertFormula(_parity_even(tm, st))
    s.assertFormula(_endpoints_not_both(tm, st))
    s.assertFormula(_popcount_eq(tm, st, 3))  # odd -> contradicts parity
    res = s.checkSat()
    return res.isUnsat(), str(res)


def z3_bv_forbidden_unsat():
    st = z3mod.BitVec("st", 8)
    def bit(i): return z3mod.Extract(i, i, st)
    def ze(b): return z3mod.ZeroExt(7, b)
    total = ze(bit(0))
    for i in range(1, 8):
        total = total + ze(bit(i))
    s = z3mod.Solver()
    s.add(total % 2 == 0)
    s.add(z3mod.Not(z3mod.And(bit(0) == 1, bit(7) == 1)))
    s.add(total == 3)
    return s.check() == z3mod.unsat, str(s.check())


def cvc5_bv_popcount2_sat():
    """Negative: popcount=2 with endpoints forbidden -> SAT."""
    tm, s = _solver()
    BV8 = tm.mkBitVectorSort(8)
    st = tm.mkConst(BV8, "st")
    s.assertFormula(_parity_even(tm, st))
    s.assertFormula(_endpoints_not_both(tm, st))
    s.assertFormula(_popcount_eq(tm, st, 2))
    res = s.checkSat()
    return res.isSat(), str(res)


def cvc5_bv_all_zero_sat():
    """Boundary: all-zero state (popcount=0) satisfies both rules -> SAT."""
    tm, s = _solver()
    BV8 = tm.mkBitVectorSort(8)
    st = tm.mkConst(BV8, "st")
    s.assertFormula(_parity_even(tm, st))
    s.assertFormula(_endpoints_not_both(tm, st))
    s.assertFormula(tm.mkTerm(Kind.EQUAL, st, tm.mkBitVector(8, 0)))
    res = s.checkSat()
    return res.isSat(), str(res)


def run_positive_tests():
    ok, v = cvc5_bv_forbidden_unsat()
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 QF_BV UNSAT on parity+popcount=3 IS the forbidden-placement proof"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    out = {"cvc5_bv_forbidden_unsat": {"pass": ok, "verdict": v}}
    if z3mod is not None:
        ok2, v2 = z3_bv_forbidden_unsat()
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "z3 BV parity UNSAT"
        TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
        out["z3_parity_unsat"] = {"pass": ok2, "verdict": v2}
    return out

def run_negative_tests():
    ok, v = cvc5_bv_popcount2_sat()
    return {"cvc5_popcount2_sat": {"pass": ok, "verdict": v}}

def run_boundary_tests():
    ok, v = cvc5_bv_all_zero_sat()
    return {"cvc5_all_zero_sat": {"pass": ok, "verdict": v}}


if __name__ == "__main__":
    if cvc5 is None:
        print("BLOCKER: cvc5 not importable"); raise SystemExit(2)
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos,**neg,**bnd}.values())
    results = {
        "name": "sim_cvc5_deep_bv_forbidden_placement",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_deep_bv_forbidden_placement_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
