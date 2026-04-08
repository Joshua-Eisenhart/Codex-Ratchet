#!/usr/bin/env python3
"""
SIM: Bridge cvc5 Cross-Check of Z3 Kernel Ordering Proofs

Re-implements the 4 UNSAT proofs from sim_bridge_z3_kernel_ordering.py
using cvc5 instead of z3, for independent solver confirmation.

Proofs:
  1. Entangled state (off-diagonal > 0, joint entropy < marginal) → I(A:B) > 0
     [Forbidden: I(A:B) ≤ 0] → UNSAT expected
  2. Coherent information I_c < I(A:B) always
     [Forbidden: I_c > I(A:B)] → UNSAT expected
  3. Separable states: CE ≥ I_c
     [Forbidden: CE < I_c for separable state] → UNSAT expected
  4. Product state → I(A:B) = 0
     [Forbidden: I(A:B) > 0 for product state] → UNSAT expected

Verdict mapping:
  UNSAT  = cvc5 agrees with z3 (forbidden config impossible)
  SAT    = disagreement with z3 (flag as ambiguous, record model)
  UNKNOWN = cvc5 timed out or gave up
"""

import json
import os
import time

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": "supportive",   # comparison reference only
    "cvc5": "load_bearing",
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    import z3 as _z3
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "Supportive: reference implementation for comparison; "
        "same 4 proofs run in z3 to confirm cvc5 agreement"
    )
    _z3_available = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    _z3_available = False
    _z3 = None

try:
    import cvc5 as _cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = (
        "Load-bearing: independent UNSAT proof solver; "
        "each of 4 kernel ordering proofs run through cvc5 QF_NRA"
    )
    _cvc5_available = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"
    _cvc5_available = False
    _cvc5 = None

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
# CVC5 PROOF HELPER
# =====================================================================

def run_cvc5_proof(constraints_fn, description, z3_verdict=None):
    """
    Run a cvc5 proof.

    constraints_fn: callable(tm, slv) -> None
        Sets up assertions on solver `slv` using TermManager `tm`.
    description: human-readable description of the proof.
    z3_verdict: expected verdict from z3 run ("unsat", "sat", None).

    Returns result dict with verdict, pass flag, agreement with z3.
    """
    if not _cvc5_available:
        return {
            "description": description,
            "verdict": "error",
            "pass": False,
            "note": "cvc5 not available",
            "agrees_with_z3": None,
        }

    try:
        tm = _cvc5.TermManager()
        slv = _cvc5.Solver(tm)
        slv.setLogic("QF_NRA")
        slv.setOption("produce-models", "true")

        constraints_fn(tm, slv)

        result = slv.checkSat()
        verdict = str(result)  # "unsat", "sat", "unknown"

        pass_flag = verdict == "unsat"
        agrees_with_z3 = None
        if z3_verdict is not None:
            agrees_with_z3 = (verdict == z3_verdict)

        note = (
            "UNSAT: cvc5 confirms forbidden configuration is impossible — proof holds."
            if verdict == "unsat"
            else (
                f"SAT: cvc5 found a counterexample — DISAGREEMENT with z3 ({z3_verdict}). AMBIGUOUS."
                if verdict == "sat" and z3_verdict == "unsat"
                else f"cvc5 verdict: {verdict}"
            )
        )

        return {
            "description": description,
            "verdict": verdict,
            "pass": pass_flag,
            "agrees_with_z3": agrees_with_z3,
            "z3_reference_verdict": z3_verdict,
            "note": note,
        }

    except Exception as e:
        return {
            "description": description,
            "verdict": "error",
            "pass": False,
            "error": str(e),
            "note": f"cvc5 raised exception: {e}",
            "agrees_with_z3": None,
        }


# =====================================================================
# Z3 REFERENCE RUNNER (for comparison)
# =====================================================================

def run_z3_reference_proofs():
    """Run the same 4 proofs via z3 to get reference verdicts."""
    if not _z3_available:
        return {k: "z3_unavailable" for k in [
            "proof1", "proof2", "proof3", "proof4"
        ]}

    verdicts = {}

    # Proof 1
    s1 = _z3.Solver()
    S_A1 = _z3.Real("S_A"); S_B1 = _z3.Real("S_B"); S_AB1 = _z3.Real("S_AB")
    I_AB1 = _z3.Real("I_AB"); off_diag1 = _z3.Real("off_diag")
    s1.add(S_A1 >= 0, S_B1 >= 0, S_AB1 >= 0)
    s1.add(off_diag1 > 0)
    s1.add(S_A1 == 1, S_B1 == 1)
    s1.add(S_AB1 < S_A1, S_AB1 <= S_A1 + S_B1)
    s1.add(I_AB1 == S_A1 + S_B1 - S_AB1)
    s1.add(I_AB1 <= 0)
    verdicts["proof1"] = str(s1.check())

    # Proof 2
    s2 = _z3.Solver()
    S_A2 = _z3.Real("S_A"); S_B2 = _z3.Real("S_B"); S_AB2 = _z3.Real("S_AB")
    I_c2 = _z3.Real("I_c"); I_AB2 = _z3.Real("I_AB")
    s2.add(S_A2 >= 0, S_B2 >= 0, S_AB2 >= 0)
    s2.add(I_c2 == S_B2 - S_AB2)
    s2.add(I_AB2 == S_A2 + S_B2 - S_AB2)
    s2.add(I_c2 > I_AB2)
    verdicts["proof2"] = str(s2.check())

    # Proof 3
    s3 = _z3.Solver()
    S_A3 = _z3.Real("S_A"); S_B3 = _z3.Real("S_B"); S_AB3 = _z3.Real("S_AB")
    CE3 = _z3.Real("CE"); Ic3 = _z3.Real("Ic")
    s3.add(S_A3 >= 0, S_B3 >= 0, S_AB3 >= 0)
    s3.add(S_AB3 >= S_B3, S_AB3 <= S_A3 + S_B3)
    s3.add(CE3 == S_AB3 - S_B3, Ic3 == S_B3 - S_AB3)
    s3.add(CE3 < Ic3)
    verdicts["proof3"] = str(s3.check())

    # Proof 4
    s4 = _z3.Solver()
    S_A4 = _z3.Real("S_A"); S_B4 = _z3.Real("S_B"); S_AB4 = _z3.Real("S_AB")
    I_AB4 = _z3.Real("I_AB")
    s4.add(S_A4 >= 0, S_B4 >= 0, S_AB4 >= 0)
    s4.add(S_AB4 == S_A4 + S_B4)
    s4.add(I_AB4 == S_A4 + S_B4 - S_AB4)
    s4.add(I_AB4 > 0)
    verdicts["proof4"] = str(s4.check())

    return verdicts


# =====================================================================
# CVC5 PROOF IMPLEMENTATIONS
# =====================================================================

def proof1_constraints(tm, slv):
    """
    Proof 1: Entangled state (off-diagonal > 0, joint entropy < marginal) → I(A:B) > 0.
    Forbidden: I(A:B) ≤ 0.
    Variables: S_A, S_B, S_AB, I_AB, off_diag (all Real).
    """
    Real = tm.getRealSort()

    S_A = tm.mkConst(Real, "S_A")
    S_B = tm.mkConst(Real, "S_B")
    S_AB = tm.mkConst(Real, "S_AB")
    I_AB = tm.mkConst(Real, "I_AB")
    off_diag = tm.mkConst(Real, "off_diag")

    zero = tm.mkReal(0)
    one = tm.mkReal(1)

    # S_A, S_B, S_AB >= 0
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_A, zero))
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_B, zero))
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_AB, zero))

    # off_diag > 0 (entangled)
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GT, off_diag, zero))

    # S_A = 1, S_B = 1 (maximally mixed marginals)
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, S_A, one))
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, S_B, one))

    # S_AB < S_A (joint entropy < marginal: hallmark of entangled pure state)
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.LT, S_AB, S_A))

    # Subadditivity: S_AB <= S_A + S_B
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.LEQ, S_AB,
                                 tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B)))

    # I_AB = S_A + S_B - S_AB
    slv.assertFormula(tm.mkTerm(
        _cvc5.Kind.EQUAL, I_AB,
        tm.mkTerm(_cvc5.Kind.SUB, tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B), S_AB)
    ))

    # FORBIDDEN: I(A:B) <= 0
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.LEQ, I_AB, zero))


def proof2_constraints(tm, slv):
    """
    Proof 2: I_c < I(A:B) always.
    Forbidden: I_c > I(A:B) with S_A >= 0.
    """
    Real = tm.getRealSort()

    S_A = tm.mkConst(Real, "S_A")
    S_B = tm.mkConst(Real, "S_B")
    S_AB = tm.mkConst(Real, "S_AB")
    I_c = tm.mkConst(Real, "I_c")
    I_AB = tm.mkConst(Real, "I_AB")

    zero = tm.mkReal(0)

    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_A, zero))
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_B, zero))
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_AB, zero))

    # I_c = S_B - S_AB
    slv.assertFormula(tm.mkTerm(
        _cvc5.Kind.EQUAL, I_c,
        tm.mkTerm(_cvc5.Kind.SUB, S_B, S_AB)
    ))

    # I_AB = S_A + S_B - S_AB
    slv.assertFormula(tm.mkTerm(
        _cvc5.Kind.EQUAL, I_AB,
        tm.mkTerm(_cvc5.Kind.SUB, tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B), S_AB)
    ))

    # FORBIDDEN: I_c > I(A:B)
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GT, I_c, I_AB))


def proof3_constraints(tm, slv):
    """
    Proof 3: For separable states (S_AB >= S_B), CE >= I_c.
    Forbidden: CE < I_c for separable state.
    """
    Real = tm.getRealSort()

    S_A = tm.mkConst(Real, "S_A")
    S_B = tm.mkConst(Real, "S_B")
    S_AB = tm.mkConst(Real, "S_AB")
    CE = tm.mkConst(Real, "CE")
    Ic = tm.mkConst(Real, "Ic")

    zero = tm.mkReal(0)

    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_A, zero))
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_B, zero))
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_AB, zero))

    # Separable: S_AB >= S_B
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_AB, S_B))

    # Subadditivity: S_AB <= S_A + S_B
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.LEQ, S_AB,
                                 tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B)))

    # CE = S_AB - S_B
    slv.assertFormula(tm.mkTerm(
        _cvc5.Kind.EQUAL, CE,
        tm.mkTerm(_cvc5.Kind.SUB, S_AB, S_B)
    ))

    # Ic = S_B - S_AB
    slv.assertFormula(tm.mkTerm(
        _cvc5.Kind.EQUAL, Ic,
        tm.mkTerm(_cvc5.Kind.SUB, S_B, S_AB)
    ))

    # FORBIDDEN: CE < Ic
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.LT, CE, Ic))


def proof4_constraints(tm, slv):
    """
    Proof 4: Product state (S_AB = S_A + S_B) → I(A:B) = 0.
    Forbidden: I(A:B) > 0 for product state.
    """
    Real = tm.getRealSort()

    S_A = tm.mkConst(Real, "S_A")
    S_B = tm.mkConst(Real, "S_B")
    S_AB = tm.mkConst(Real, "S_AB")
    I_AB = tm.mkConst(Real, "I_AB")

    zero = tm.mkReal(0)

    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_A, zero))
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_B, zero))
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_AB, zero))

    # Product state: S_AB = S_A + S_B
    slv.assertFormula(tm.mkTerm(
        _cvc5.Kind.EQUAL, S_AB,
        tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B)
    ))

    # I_AB = S_A + S_B - S_AB
    slv.assertFormula(tm.mkTerm(
        _cvc5.Kind.EQUAL, I_AB,
        tm.mkTerm(_cvc5.Kind.SUB, tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B), S_AB)
    ))

    # FORBIDDEN: I(A:B) > 0 for product state
    slv.assertFormula(tm.mkTerm(_cvc5.Kind.GT, I_AB, zero))


# =====================================================================
# POSITIVE TESTS: 4 cvc5 UNSAT proofs
# =====================================================================

def run_positive_tests():
    results = {}

    if not _cvc5_available:
        return {"error": "cvc5 not available"}

    # Get z3 reference verdicts for comparison
    z3_verdicts = run_z3_reference_proofs()

    # Proof 1
    results["proof1_entangled_implies_MI_positive"] = run_cvc5_proof(
        proof1_constraints,
        "Entangled state (off-diagonal > 0, joint entropy < marginal) must have I(A:B) > 0. "
        "Forbidden: I(A:B) <= 0.",
        z3_verdict=z3_verdicts.get("proof1"),
    )

    # Proof 2
    results["proof2_coherent_info_strictly_weaker_than_MI"] = run_cvc5_proof(
        proof2_constraints,
        "Coherent information I_c = S(B) - S(AB) < I(A:B) = S(A) + S(B) - S(AB). "
        "Forbidden: I_c > I(A:B).",
        z3_verdict=z3_verdicts.get("proof2"),
    )

    # Proof 3
    results["proof3_separable_kernel_ordering_CE_ge_Ic"] = run_cvc5_proof(
        proof3_constraints,
        "For separable states (S_AB >= S_B, i.e. CE >= 0): CE >= I_c. "
        "Forbidden: CE < I_c.",
        z3_verdict=z3_verdicts.get("proof3"),
    )

    # Proof 4
    results["proof4_product_state_zero_MI"] = run_cvc5_proof(
        proof4_constraints,
        "Product state (S_AB = S_A + S_B) must have I(A:B) = 0. "
        "Forbidden: I(A:B) > 0.",
        z3_verdict=z3_verdicts.get("proof4"),
    )

    # Summary
    proof_results = [v for k, v in results.items() if k.startswith("proof")]
    unsat_count = sum(1 for v in proof_results if v.get("verdict") == "unsat")
    all_unsat = all(v.get("pass", False) for v in proof_results)
    all_agree_z3 = all(v.get("agrees_with_z3", False) for v in proof_results
                       if v.get("agrees_with_z3") is not None)

    disagreements = [
        k for k, v in results.items()
        if k.startswith("proof") and v.get("agrees_with_z3") is False
    ]

    results["summary"] = {
        "total_proofs": 4,
        "unsat_count": unsat_count,
        "all_unsat": all_unsat,
        "all_agree_with_z3": all_agree_z3,
        "disagreements": disagreements,
        "z3_reference_verdicts": z3_verdicts,
    }

    return results


# =====================================================================
# NEGATIVE TESTS: SAT-able configurations should NOT be UNSAT
# =====================================================================

def run_negative_tests():
    results = {}

    if not _cvc5_available:
        return {"error": "cvc5 not available"}

    # Check: entangled state with I(A:B) > 0 IS satisfiable (SAT expected)
    def sat_entangled(tm, slv):
        Real = tm.getRealSort()
        S_A = tm.mkConst(Real, "S_A")
        S_B = tm.mkConst(Real, "S_B")
        S_AB = tm.mkConst(Real, "S_AB")
        I_AB = tm.mkConst(Real, "I_AB")
        zero = tm.mkReal(0)
        one = tm.mkReal(1)

        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_A, zero))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_B, zero))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_AB, zero))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, S_A, one))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, S_B, one))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.LT, S_AB, S_A))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.LEQ, S_AB, tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B)))
        slv.assertFormula(tm.mkTerm(
            _cvc5.Kind.EQUAL, I_AB,
            tm.mkTerm(_cvc5.Kind.SUB, tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B), S_AB)
        ))
        # SHOULD be SAT: I(A:B) > 0
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GT, I_AB, zero))

    try:
        tm = _cvc5.TermManager()
        slv = _cvc5.Solver(tm)
        slv.setLogic("QF_NRA")
        slv.setOption("produce-models", "true")
        sat_entangled(tm, slv)
        result = slv.checkSat()
        verdict = str(result)
        results["sat_check_entangled_state_has_positive_MI"] = {
            "description": "Entangled state with I(A:B) > 0 should be SAT (valid config exists)",
            "verdict": verdict,
            "pass": verdict == "sat",
            "note": "SAT expected — confirms positive proof space is non-empty.",
        }
    except Exception as e:
        results["sat_check_entangled_state_has_positive_MI"] = {
            "description": "Entangled state with I(A:B) > 0 should be SAT",
            "verdict": "error",
            "pass": False,
            "note": str(e),
        }

    # Check: product state with I(A:B) = 0 IS satisfiable (SAT expected)
    def sat_product(tm, slv):
        Real = tm.getRealSort()
        S_A = tm.mkConst(Real, "S_A")
        S_B = tm.mkConst(Real, "S_B")
        S_AB = tm.mkConst(Real, "S_AB")
        I_AB = tm.mkConst(Real, "I_AB")
        zero = tm.mkReal(0)

        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_A, zero))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_B, zero))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.GEQ, S_AB, zero))
        slv.assertFormula(tm.mkTerm(
            _cvc5.Kind.EQUAL, S_AB,
            tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B)
        ))
        slv.assertFormula(tm.mkTerm(
            _cvc5.Kind.EQUAL, I_AB,
            tm.mkTerm(_cvc5.Kind.SUB, tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B), S_AB)
        ))
        # SHOULD be SAT: I(A:B) = 0
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, I_AB, zero))

    try:
        tm = _cvc5.TermManager()
        slv = _cvc5.Solver(tm)
        slv.setLogic("QF_NRA")
        slv.setOption("produce-models", "true")
        sat_product(tm, slv)
        result = slv.checkSat()
        verdict = str(result)
        results["sat_check_product_state_zero_MI_satisfiable"] = {
            "description": "Product state with I(A:B) = 0 should be SAT",
            "verdict": verdict,
            "pass": verdict == "sat",
            "note": "SAT expected — product states with zero MI do exist.",
        }
    except Exception as e:
        results["sat_check_product_state_zero_MI_satisfiable"] = {
            "description": "Product state with I(A:B) = 0 should be SAT",
            "verdict": "error",
            "pass": False,
            "note": str(e),
        }

    return results


# =====================================================================
# BOUNDARY TESTS: maximally mixed state boundary cases
# =====================================================================

def run_boundary_tests():
    results = {}

    if not _cvc5_available:
        return {"error": "cvc5 not available"}

    # Boundary: maximally mixed state S_A=1, S_B=1, S_AB=2
    # CE = S_AB - S_B = 1, I_c = S_B - S_AB = -1
    # CE < I_c should be UNSAT (CE=1 >= I_c=-1)
    def boundary_ce_lt_ic(tm, slv):
        Real = tm.getRealSort()
        S_A = tm.mkConst(Real, "S_A")
        S_B = tm.mkConst(Real, "S_B")
        S_AB = tm.mkConst(Real, "S_AB")
        CE = tm.mkConst(Real, "CE")
        Ic = tm.mkConst(Real, "Ic")

        one = tm.mkReal(1)
        two = tm.mkReal(2)

        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, S_A, one))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, S_B, one))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, S_AB, two))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, CE,
                                     tm.mkTerm(_cvc5.Kind.SUB, S_AB, S_B)))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, Ic,
                                     tm.mkTerm(_cvc5.Kind.SUB, S_B, S_AB)))
        # FORBIDDEN: CE < Ic
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.LT, CE, Ic))

    try:
        tm = _cvc5.TermManager()
        slv = _cvc5.Solver(tm)
        slv.setLogic("QF_NRA")
        slv.setOption("produce-models", "true")
        boundary_ce_lt_ic(tm, slv)
        result = slv.checkSat()
        verdict = str(result)
        results["boundary_maximally_mixed_CE_ge_Ic"] = {
            "description": "Maximally mixed state: CE=1, I_c=-1. CE < I_c should be UNSAT.",
            "verdict": verdict,
            "pass": verdict == "unsat",
            "note": "UNSAT expected: CE=1 >= I_c=-1 at maximally mixed boundary.",
        }
    except Exception as e:
        results["boundary_maximally_mixed_CE_ge_Ic"] = {
            "description": "Maximally mixed state boundary",
            "verdict": "error",
            "pass": False,
            "note": str(e),
        }

    # Boundary: MI < CE for maximally mixed state IS satisfiable (SAT expected)
    def boundary_mi_lt_ce(tm, slv):
        Real = tm.getRealSort()
        S_A = tm.mkConst(Real, "S_A")
        S_B = tm.mkConst(Real, "S_B")
        S_AB = tm.mkConst(Real, "S_AB")

        one = tm.mkReal(1)
        two = tm.mkReal(2)

        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, S_A, one))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, S_B, one))
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.EQUAL, S_AB, two))

        MI = tm.mkTerm(_cvc5.Kind.SUB, tm.mkTerm(_cvc5.Kind.ADD, S_A, S_B), S_AB)
        CE = tm.mkTerm(_cvc5.Kind.SUB, S_AB, S_B)
        slv.assertFormula(tm.mkTerm(_cvc5.Kind.LT, MI, CE))

    try:
        tm = _cvc5.TermManager()
        slv = _cvc5.Solver(tm)
        slv.setLogic("QF_NRA")
        slv.setOption("produce-models", "true")
        boundary_mi_lt_ce(tm, slv)
        result = slv.checkSat()
        verdict = str(result)
        results["boundary_maximally_mixed_MI_lt_CE_is_SAT"] = {
            "description": "Maximally mixed state: MI=0, CE=1. MI < CE should be SAT.",
            "verdict": verdict,
            "pass": verdict == "sat",
            "note": "SAT expected: MI < CE is achievable at the maximally mixed boundary.",
        }
    except Exception as e:
        results["boundary_maximally_mixed_MI_lt_CE_is_SAT"] = {
            "description": "Maximally mixed state MI < CE boundary",
            "verdict": "error",
            "pass": False,
            "note": str(e),
        }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t0 = time.time()

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    elapsed = time.time() - t0

    pos_summary = positive.get("summary", {})
    neg_pass = all(v.get("pass", False) for v in negative.values() if isinstance(v, dict))
    bound_pass = all(v.get("pass", False) for v in boundary.values() if isinstance(v, dict))
    all_unsat = pos_summary.get("all_unsat", False)
    all_agree = pos_summary.get("all_agree_with_z3", False)
    disagreements = pos_summary.get("disagreements", [])

    results = {
        "name": "Bridge cvc5 Cross-Check of Z3 Kernel Ordering Proofs",
        "schema_version": "1.0",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "total_proofs": 4,
            "cvc5_unsat_count": pos_summary.get("unsat_count", 0),
            "all_proofs_unsat": all_unsat,
            "all_agree_with_z3": all_agree,
            "disagreements": disagreements,
            "z3_reference_verdicts": pos_summary.get("z3_reference_verdicts", {}),
            "negative_pass": neg_pass,
            "boundary_pass": bound_pass,
            "total_time_s": elapsed,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_cvc5_crosscheck_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    print(f"\n=== CVC5 CROSS-CHECK RESULTS ===")
    print(f"cvc5 UNSAT proofs: {pos_summary.get('unsat_count', 0)}/4")
    print(f"All UNSAT: {all_unsat}")
    print(f"All agree with z3: {all_agree}")
    if disagreements:
        print(f"DISAGREEMENTS: {disagreements}")
    else:
        print(f"No disagreements with z3.")
    for k, v in positive.items():
        if k.startswith("proof") and isinstance(v, dict):
            verdict = v.get("verdict", "?")
            agree = v.get("agrees_with_z3", "?")
            passed = "PASS" if v.get("pass") else "FAIL"
            print(f"  {k}: cvc5={verdict} agrees_z3={agree} [{passed}]")
    print(f"Negative tests pass: {neg_pass}")
    print(f"Boundary tests pass: {bound_pass}")
    print(f"Time: {elapsed:.3f}s")
