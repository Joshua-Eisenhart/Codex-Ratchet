#!/usr/bin/env python3
"""
sim_cvc5_cross_check.py -- Cross-check strongest z3 UNSAT proofs with cvc5.

Verifies that z3 UNSAT results are not solver-specific artifacts by
re-encoding each proof in cvc5 (QF_NRA / QF_LRA) and comparing outcomes.

Proofs cross-checked:
  1. No-cloning:        x = x^2 for x in (0,1) is UNSAT
  2. Bloch contraction:  0.7^20 * r^2 > 0.01  is UNSAT  (r^2 in [0,1])
  3. Entanglement death: 0.49^10 * c > 0.001   is UNSAT  (c in [0,1])
  4. Noncommutation:     [A,B]=0 with A off-diag != 0, B diag distinct => UNSAT
"""

import json
import os
import time
import numpy as np
from fractions import Fraction

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": "not relevant"},
    "pyg": {"tried": False, "used": False, "reason": "not relevant"},
    # --- Proof layer ---
    "z3": {"tried": True, "used": True, "reason": "cross-check source solver"},
    "cvc5": {"tried": True, "used": True, "reason": "cross-check target solver"},
    # --- Symbolic layer ---
    "sympy": {"tried": False, "used": False, "reason": "not relevant"},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": "not relevant"},
    "geomstats": {"tried": False, "used": False, "reason": "not relevant"},
    "e3nn": {"tried": False, "used": False, "reason": "not relevant"},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": "not relevant"},
    "xgi": {"tried": False, "used": False, "reason": "not relevant"},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": "not relevant"},
    "gudhi": {"tried": False, "used": False, "reason": "not relevant"},
}

# Try importing each tool
try:
    import torch  # noqa: F401
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, And, Or, Not, unsat, sat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# HELPER: timed solver runs
# =====================================================================

def _timed(fn):
    """Run fn(), return (result, elapsed_seconds)."""
    t0 = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - t0


# =====================================================================
# PROOF 1: No-cloning  (x = x^2 for x in (0,1) => UNSAT)
# =====================================================================

def _proof1_z3():
    s = Solver()
    x = Real('overlap')
    s.add(x > 0, x < 1, x == x * x)
    return str(s.check())


def _proof1_cvc5():
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_NRA")
    rs = tm.getRealSort()
    x = tm.mkConst(rs, "overlap")
    zero, one = tm.mkReal(0), tm.mkReal(1)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.GT, x, zero))
    slv.assertFormula(tm.mkTerm(cvc5.Kind.LT, x, one))
    slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, x,
                                tm.mkTerm(cvc5.Kind.MULT, x, x)))
    return "unsat" if slv.checkSat().isUnsat() else "sat"


# =====================================================================
# PROOF 2: Bloch contraction  (0.7^20 * r^2 > 0.01 => UNSAT, r^2 in [0,1])
# =====================================================================

def _fraction_str(f):
    """Return (numerator_str, denominator_str) for a Fraction."""
    return str(f.numerator), str(f.denominator)


def _proof2_z3():
    s = Solver()
    r2 = Real('r_squared')
    coeff = Fraction(7, 10) ** 20  # exact rational
    threshold = Fraction(1, 100)
    s.add(r2 >= 0, r2 <= 1)
    s.add(r2 * int(coeff.numerator) > int(threshold.numerator)
          * int(coeff.denominator) / int(threshold.denominator))
    # Rewrite: coeff * r2 > threshold  =>  r2 * coeff_num / coeff_den > thr_num / thr_den
    # Cleaner: use RealVal
    from z3 import RealVal
    s2 = Solver()
    r2b = Real('r_squared')
    c = RealVal(f"{coeff.numerator}/{coeff.denominator}")
    t = RealVal(f"{threshold.numerator}/{threshold.denominator}")
    s2.add(r2b >= 0, r2b <= 1, c * r2b > t)
    return str(s2.check())


def _proof2_cvc5():
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LRA")
    rs = tm.getRealSort()
    r2 = tm.mkConst(rs, "r_squared")
    zero, one = tm.mkReal(0), tm.mkReal(1)
    coeff = Fraction(7, 10) ** 20
    threshold = Fraction(1, 100)
    c_n, c_d = _fraction_str(coeff)
    t_n, t_d = _fraction_str(threshold)
    c_term = tm.mkReal(c_n, c_d)
    t_term = tm.mkReal(t_n, t_d)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.GEQ, r2, zero))
    slv.assertFormula(tm.mkTerm(cvc5.Kind.LEQ, r2, one))
    product = tm.mkTerm(cvc5.Kind.MULT, c_term, r2)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.GT, product, t_term))
    return "unsat" if slv.checkSat().isUnsat() else "sat"


# =====================================================================
# PROOF 3: Entanglement death  (0.49^10 * c > 0.001 => UNSAT, c in [0,1])
# =====================================================================

def _proof3_z3():
    from z3 import RealVal
    s = Solver()
    c = Real('c_offdiag')
    coeff = Fraction(49, 100) ** 10
    threshold = Fraction(1, 1000)
    cv = RealVal(f"{coeff.numerator}/{coeff.denominator}")
    tv = RealVal(f"{threshold.numerator}/{threshold.denominator}")
    s.add(c >= 0, c <= 1, cv * c > tv)
    return str(s.check())


def _proof3_cvc5():
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LRA")
    rs = tm.getRealSort()
    c = tm.mkConst(rs, "c_offdiag")
    zero, one = tm.mkReal(0), tm.mkReal(1)
    coeff = Fraction(49, 100) ** 10
    threshold = Fraction(1, 1000)
    c_n, c_d = _fraction_str(coeff)
    t_n, t_d = _fraction_str(threshold)
    c_term = tm.mkReal(c_n, c_d)
    t_term = tm.mkReal(t_n, t_d)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.GEQ, c, zero))
    slv.assertFormula(tm.mkTerm(cvc5.Kind.LEQ, c, one))
    product = tm.mkTerm(cvc5.Kind.MULT, c_term, c)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.GT, product, t_term))
    return "unsat" if slv.checkSat().isUnsat() else "sat"


# =====================================================================
# PROOF 4: Noncommutation necessity
#   B = diag(b1, b2), b1 != b2
#   A = [[a11, a12], [a12_conj, a22]]  (Hermitian, real for simplicity)
#   [A,B] = 0 => a12*(b1-b2) = 0 => a12=0 since b1!=b2
#   Assert a12 != 0  => UNSAT
# =====================================================================

def _proof4_z3():
    s = Solver()
    a12 = Real('a12')
    b1 = Real('b1')
    b2 = Real('b2')
    # [A,B]=0 implies a12*(b1-b2)=0
    s.add(a12 * (b1 - b2) == 0)
    # b1 != b2 (distinct eigenvalues)
    s.add(b1 != b2)
    # a12 != 0  (non-diagonal requirement)
    s.add(a12 != 0)
    return str(s.check())


def _proof4_cvc5():
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_NRA")
    rs = tm.getRealSort()
    a12 = tm.mkConst(rs, "a12")
    b1 = tm.mkConst(rs, "b1")
    b2 = tm.mkConst(rs, "b2")
    zero = tm.mkReal(0)
    diff = tm.mkTerm(cvc5.Kind.SUB, b1, b2)
    prod = tm.mkTerm(cvc5.Kind.MULT, a12, diff)
    # a12*(b1-b2) = 0
    slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, prod, zero))
    # b1 != b2
    not_eq = tm.mkTerm(cvc5.Kind.NOT,
                       tm.mkTerm(cvc5.Kind.EQUAL, b1, b2))
    slv.assertFormula(not_eq)
    # a12 != 0
    a12_ne = tm.mkTerm(cvc5.Kind.NOT,
                       tm.mkTerm(cvc5.Kind.EQUAL, a12, zero))
    slv.assertFormula(a12_ne)
    return "unsat" if slv.checkSat().isUnsat() else "sat"


# =====================================================================
# POSITIVE TESTS -- all 4 proofs must be UNSAT in both solvers
# =====================================================================

def run_positive_tests():
    results = {}
    proofs = [
        ("no_cloning",           _proof1_z3, _proof1_cvc5),
        ("bloch_contraction",    _proof2_z3, _proof2_cvc5),
        ("entanglement_death",   _proof3_z3, _proof3_cvc5),
        ("noncommutation",       _proof4_z3, _proof4_cvc5),
    ]
    for name, z3_fn, cvc5_fn in proofs:
        z3_res, z3_t = _timed(z3_fn)
        cvc5_res, cvc5_t = _timed(cvc5_fn)
        agree = (z3_res == cvc5_res == "unsat")
        results[name] = {
            "z3_result": z3_res,
            "z3_time_s": round(z3_t, 6),
            "cvc5_result": cvc5_res,
            "cvc5_time_s": round(cvc5_t, 6),
            "solvers_agree": agree,
            "both_unsat": agree,
            "pass": agree,
        }
    return results


# =====================================================================
# NEGATIVE TESTS -- SAT cases (relaxed constraints must be satisfiable)
# =====================================================================

def _neg1_z3():
    """x = x^2 with x in [0,1] (closed) -- SAT at x=0 or x=1."""
    s = Solver()
    x = Real('overlap')
    s.add(x >= 0, x <= 1, x == x * x)
    return str(s.check())


def _neg1_cvc5():
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_NRA")
    rs = tm.getRealSort()
    x = tm.mkConst(rs, "overlap")
    zero, one = tm.mkReal(0), tm.mkReal(1)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.GEQ, x, zero))
    slv.assertFormula(tm.mkTerm(cvc5.Kind.LEQ, x, one))
    slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, x,
                                tm.mkTerm(cvc5.Kind.MULT, x, x)))
    r = slv.checkSat()
    return "sat" if r.isSat() else "unsat"


def _neg2_z3():
    """Bloch contraction with threshold lowered to 0.0001 -- SAT."""
    from z3 import RealVal
    s = Solver()
    r2 = Real('r_squared')
    coeff = Fraction(7, 10) ** 20
    threshold = Fraction(1, 10000)  # 0.0001 < 0.7^20 ~ 0.000798
    cv = RealVal(f"{coeff.numerator}/{coeff.denominator}")
    tv = RealVal(f"{threshold.numerator}/{threshold.denominator}")
    s.add(r2 >= 0, r2 <= 1, cv * r2 > tv)
    return str(s.check())


def _neg2_cvc5():
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LRA")
    rs = tm.getRealSort()
    r2 = tm.mkConst(rs, "r_squared")
    zero, one = tm.mkReal(0), tm.mkReal(1)
    coeff = Fraction(7, 10) ** 20
    threshold = Fraction(1, 10000)
    c_n, c_d = _fraction_str(coeff)
    t_n, t_d = _fraction_str(threshold)
    c_term = tm.mkReal(c_n, c_d)
    t_term = tm.mkReal(t_n, t_d)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.GEQ, r2, zero))
    slv.assertFormula(tm.mkTerm(cvc5.Kind.LEQ, r2, one))
    product = tm.mkTerm(cvc5.Kind.MULT, c_term, r2)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.GT, product, t_term))
    r = slv.checkSat()
    return "sat" if r.isSat() else "unsat"


def _neg3_z3():
    """Entanglement death with threshold lowered to 0.0001 -- SAT."""
    from z3 import RealVal
    s = Solver()
    c = Real('c_offdiag')
    coeff = Fraction(49, 100) ** 10
    threshold = Fraction(1, 10000)  # 0.0001 < 0.49^10 ~ 0.000741
    cv = RealVal(f"{coeff.numerator}/{coeff.denominator}")
    tv = RealVal(f"{threshold.numerator}/{threshold.denominator}")
    s.add(c >= 0, c <= 1, cv * c > tv)
    return str(s.check())


def _neg3_cvc5():
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_LRA")
    rs = tm.getRealSort()
    c = tm.mkConst(rs, "c_offdiag")
    zero, one = tm.mkReal(0), tm.mkReal(1)
    coeff = Fraction(49, 100) ** 10
    threshold = Fraction(1, 10000)
    c_n, c_d = _fraction_str(coeff)
    t_n, t_d = _fraction_str(threshold)
    c_term = tm.mkReal(c_n, c_d)
    t_term = tm.mkReal(t_n, t_d)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.GEQ, c, zero))
    slv.assertFormula(tm.mkTerm(cvc5.Kind.LEQ, c, one))
    product = tm.mkTerm(cvc5.Kind.MULT, c_term, c)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.GT, product, t_term))
    r = slv.checkSat()
    return "sat" if r.isSat() else "unsat"


def _neg4_z3():
    """Noncommutation with b1=b2 allowed -- SAT (degenerate eigenvalues)."""
    s = Solver()
    a12 = Real('a12')
    b1 = Real('b1')
    b2 = Real('b2')
    s.add(a12 * (b1 - b2) == 0)
    # Allow b1 == b2 (drop distinct requirement)
    s.add(a12 != 0)
    return str(s.check())


def _neg4_cvc5():
    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("QF_NRA")
    rs = tm.getRealSort()
    a12 = tm.mkConst(rs, "a12")
    b1 = tm.mkConst(rs, "b1")
    b2 = tm.mkConst(rs, "b2")
    zero = tm.mkReal(0)
    diff = tm.mkTerm(cvc5.Kind.SUB, b1, b2)
    prod = tm.mkTerm(cvc5.Kind.MULT, a12, diff)
    slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, prod, zero))
    a12_ne = tm.mkTerm(cvc5.Kind.NOT,
                       tm.mkTerm(cvc5.Kind.EQUAL, a12, zero))
    slv.assertFormula(a12_ne)
    r = slv.checkSat()
    return "sat" if r.isSat() else "unsat"


def run_negative_tests():
    results = {}
    negatives = [
        ("no_cloning_closed_interval",      _neg1_z3, _neg1_cvc5,  "sat"),
        ("bloch_low_threshold",             _neg2_z3, _neg2_cvc5,  "sat"),
        ("entanglement_low_threshold",      _neg3_z3, _neg3_cvc5,  "sat"),
        ("noncommutation_degenerate_eigs",  _neg4_z3, _neg4_cvc5,  "sat"),
    ]
    for name, z3_fn, cvc5_fn, expected in negatives:
        z3_res, z3_t = _timed(z3_fn)
        cvc5_res, cvc5_t = _timed(cvc5_fn)
        agree = (z3_res == cvc5_res == expected)
        results[name] = {
            "expected": expected,
            "z3_result": z3_res,
            "z3_time_s": round(z3_t, 6),
            "cvc5_result": cvc5_res,
            "cvc5_time_s": round(cvc5_t, 6),
            "solvers_agree": z3_res == cvc5_res,
            "pass": agree,
        }
    return results


# =====================================================================
# BOUNDARY TESTS -- edge-case encodings
# =====================================================================

def run_boundary_tests():
    results = {}

    # Boundary 1: no-cloning at exact boundary x=0 (should be SAT)
    def _bnd1_z3():
        s = Solver()
        x = Real('x')
        s.add(x == 0, x == x * x)
        return str(s.check())

    def _bnd1_cvc5():
        tm = cvc5.TermManager()
        slv = cvc5.Solver(tm)
        slv.setLogic("QF_NRA")
        rs = tm.getRealSort()
        x = tm.mkConst(rs, "x")
        zero = tm.mkReal(0)
        slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, x, zero))
        slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, x,
                                    tm.mkTerm(cvc5.Kind.MULT, x, x)))
        return "sat" if slv.checkSat().isSat() else "unsat"

    z3_r1, z3_t1 = _timed(_bnd1_z3)
    cvc5_r1, cvc5_t1 = _timed(_bnd1_cvc5)
    results["no_cloning_at_zero"] = {
        "expected": "sat",
        "z3_result": z3_r1,
        "cvc5_result": cvc5_r1,
        "pass": z3_r1 == cvc5_r1 == "sat",
    }

    # Boundary 2: no-cloning at exact boundary x=1 (should be SAT)
    def _bnd2_z3():
        s = Solver()
        x = Real('x')
        s.add(x == 1, x == x * x)
        return str(s.check())

    def _bnd2_cvc5():
        tm = cvc5.TermManager()
        slv = cvc5.Solver(tm)
        slv.setLogic("QF_NRA")
        rs = tm.getRealSort()
        x = tm.mkConst(rs, "x")
        one = tm.mkReal(1)
        slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, x, one))
        slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, x,
                                    tm.mkTerm(cvc5.Kind.MULT, x, x)))
        return "sat" if slv.checkSat().isSat() else "unsat"

    z3_r2, z3_t2 = _timed(_bnd2_z3)
    cvc5_r2, cvc5_t2 = _timed(_bnd2_cvc5)
    results["no_cloning_at_one"] = {
        "expected": "sat",
        "z3_result": z3_r2,
        "cvc5_result": cvc5_r2,
        "pass": z3_r2 == cvc5_r2 == "sat",
    }

    # Boundary 3: Bloch contraction at exact threshold boundary
    # 0.7^20 * 1.0 = 0.7^20 ~ 7.98e-4.  Assert == 0.01 => UNSAT
    def _bnd3_z3():
        from z3 import RealVal
        s = Solver()
        r2 = Real('r_squared')
        coeff = Fraction(7, 10) ** 20
        threshold = Fraction(1, 100)
        cv = RealVal(f"{coeff.numerator}/{coeff.denominator}")
        tv = RealVal(f"{threshold.numerator}/{threshold.denominator}")
        s.add(r2 >= 0, r2 <= 1, cv * r2 == tv)
        return str(s.check())

    def _bnd3_cvc5():
        tm = cvc5.TermManager()
        slv = cvc5.Solver(tm)
        slv.setLogic("QF_LRA")
        rs = tm.getRealSort()
        r2 = tm.mkConst(rs, "r_squared")
        zero, one = tm.mkReal(0), tm.mkReal(1)
        coeff = Fraction(7, 10) ** 20
        threshold = Fraction(1, 100)
        c_n, c_d = _fraction_str(coeff)
        t_n, t_d = _fraction_str(threshold)
        c_term = tm.mkReal(c_n, c_d)
        t_term = tm.mkReal(t_n, t_d)
        slv.assertFormula(tm.mkTerm(cvc5.Kind.GEQ, r2, zero))
        slv.assertFormula(tm.mkTerm(cvc5.Kind.LEQ, r2, one))
        product = tm.mkTerm(cvc5.Kind.MULT, c_term, r2)
        slv.assertFormula(tm.mkTerm(cvc5.Kind.EQUAL, product, t_term))
        r = slv.checkSat()
        return "sat" if r.isSat() else "unsat"

    # 0.01 / 0.7^20 ~ 12.53 which is > 1, so r2 in [0,1] can't reach it => UNSAT
    z3_r3, z3_t3 = _timed(_bnd3_z3)
    cvc5_r3, cvc5_t3 = _timed(_bnd3_cvc5)
    results["bloch_exact_threshold"] = {
        "expected": "unsat",
        "z3_result": z3_r3,
        "cvc5_result": cvc5_r3,
        "pass": z3_r3 == cvc5_r3 == "unsat",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = (
        all(v["pass"] for v in pos.values())
        and all(v["pass"] for v in neg.values())
        and all(v["pass"] for v in bnd.values())
    )

    results = {
        "name": "cvc5_cross_check",
        "description": "Cross-check z3 UNSAT proofs with cvc5 independent solver",
        "tool_manifest": TOOL_MANIFEST,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cvc5_cross_check_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
