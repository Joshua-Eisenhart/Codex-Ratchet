#!/usr/bin/env python3
"""
SIM LEGO: cvc5 Frege System Soundness Constraint
================================================
Frege (Hilbert-style) proof systems use inference rules like modus ponens:
  From A and (A → B), derive B.

Modus ponens is sound: if A is a logical consequence and A→B is a logical consequence,
then B must be a logical consequence.

This sim tests the constraint: modus ponens is complete for the rule (A, A→B ⊢ B).
If A is asserted and A→B is asserted, then B must follow (or the system admits a contradiction).

Example: prove p→p via modus ponens chain.
  1. Assume p→p (tautology axiom)
  2. Assume p (hypothesis)
  3. Apply modus ponens: from p and p→p derive p  [already have p, so tautology holds]

Constraint verification: cvc5 proves UNSAT when:
  - Assertion: A ∧ (A→B)
  - Denial: ¬B

For the tautology p→p:
  - Assert: p and (p→p)
  - Deny: ¬(p→p), i.e., p ∧ ¬p
  - Should be UNSAT (contradiction found by cvc5)

Tool integration:
  cvc5  : load_bearing  -- UNSAT / SAT verdicts on Frege rule soundness (modus ponens, implication)
  sympy : supportive    -- symbolic truth tables for implication and modus ponens chain
"""

import json
import os

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- proof logic is symbolic"},
    "pyg": {"tried": False, "used": False, "reason": "not needed -- no graph learning layer"},
    "z3": {"tried": False, "used": False, "reason": "alternative solver; cvc5 is primary; this check relies on cvc5 QF_LRA verdicts rather than z3"},
    "cvc5": {"tried": True, "used": True, "reason": "load_bearing: UNSAT / SAT verdicts on modus ponens soundness constraint via QF_LRA"},
    "sympy": {"tried": True, "used": True, "reason": "supportive: symbolic truth tables and implication verification"},
    "clifford": {"tried": False, "used": False, "reason": "not needed -- no algebraic structure"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed -- no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency graph"},
    "xgi": {"tried": False, "used": False, "reason": "not needed -- no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed -- no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed -- no homology"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": "load_bearing",
    "sympy": "supportive",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

_cvc5_available = False
try:
    import cvc5
    _cvc5_available = True
except ImportError:
    pass

_sympy_available = False
try:
    import sympy as sp
    _sympy_available = True
except ImportError:
    pass


def positive_test_cvc5_modus_ponens_sound():
    """
    Test: modus ponens is sound.
    Assertion: p ∧ (p → q)
    Denial: ¬q
    cvc5 should find this UNSAT (contradiction).
    """
    if not _cvc5_available:
        return {"status": "cvc5 not installed", "pass": False}

    solver = cvc5.Solver()
    solver.setLogic("QF_LRA")

    # Boolean variables as 0/1 reals
    p = solver.mkConst(solver.getRealSort(), "p")
    q = solver.mkConst(solver.getRealSort(), "q")

    # Constraint: p and q are 0 or 1
    zero = solver.mkReal(0)
    one = solver.mkReal(1)

    solver.assertFormula(solver.mkTerm(cvc5.Kind.OR,
        solver.mkTerm(cvc5.Kind.EQUAL, p, zero),
        solver.mkTerm(cvc5.Kind.EQUAL, p, one)
    ))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.OR,
        solver.mkTerm(cvc5.Kind.EQUAL, q, zero),
        solver.mkTerm(cvc5.Kind.EQUAL, q, one)
    ))

    # Assert: p = 1 (p is true)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, p, one))

    # Assert: p → q (i.e., ¬p ∨ q, i.e., p ≤ q in terms of 0/1)
    # Equivalently: if p = 1, then q = 1
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, p, q))

    # Deny: q = 1 (q is false)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, q, zero))

    result = solver.checkSat()
    is_unsat = str(result) == "unsat"

    return {
        "assertion": "p ∧ (p → q)",
        "denial": "¬q",
        "result": str(result),
        "is_unsat": is_unsat,
        "modus_ponens_sound": is_unsat,
        "pass": is_unsat,
        "reason": "cvc5 proves contradiction; modus ponens is sound"
    }


def positive_test_sympy_implication_truth_table():
    """
    Test: verify implication truth table via sympy.
    p → q ≡ ¬p ∨ q. Rows where p=1 and q=1: TRUE. Row p=1, q=0: FALSE.
    """
    if not _sympy_available:
        return {"status": "sympy not installed", "pass": False}

    p, q = sp.symbols("p q", integer=True)
    implication = ~p | q  # p → q ≡ ¬p ∨ q

    # Test truth table
    tt = {}
    for pval in [0, 1]:
        for qval in [0, 1]:
            subs_result = implication.subs([(p, pval), (q, qval)])
            tt[(pval, qval)] = bool(subs_result)

    # Expected: p→q is false only when p=1, q=0
    expected = {
        (0, 0): True,   # ¬p ∨ q = 1 ∨ 0 = 1
        (0, 1): True,   # ¬p ∨ q = 1 ∨ 1 = 1
        (1, 0): False,  # ¬p ∨ q = 0 ∨ 0 = 0
        (1, 1): True,   # ¬p ∨ q = 0 ∨ 1 = 1
    }

    tt_correct = tt == expected

    # Modus ponens: if p=1 and p→q, then q=1
    mp_case = tt[(1, 1)] and not tt[(1, 0)]

    return {
        "truth_table": {str(k): v for k, v in tt.items()},
        "expected": {str(k): v for k, v in expected.items()},
        "truth_table_correct": tt_correct,
        "modus_ponens_case_holds": mp_case,
        "pass": tt_correct and mp_case,
        "reason": "sympy truth table confirms p→q semantics and modus ponens validity"
    }


def positive_test_cvc5_tautology_p_to_p():
    """
    Test: the tautology p → p.
    Assertion: assert that ¬(p → p), i.e., p ∧ ¬p
    cvc5 should find this UNSAT (p→p is always true).
    """
    if not _cvc5_available:
        return {"status": "cvc5 not installed", "pass": False}

    solver = cvc5.Solver()
    solver.setLogic("QF_LRA")

    p = solver.mkConst(solver.getRealSort(), "p")
    zero = solver.mkReal(0)
    one = solver.mkReal(1)

    # p is 0 or 1
    solver.assertFormula(solver.mkTerm(cvc5.Kind.OR,
        solver.mkTerm(cvc5.Kind.EQUAL, p, zero),
        solver.mkTerm(cvc5.Kind.EQUAL, p, one)
    ))

    # Deny p → p: assert p ∧ ¬p
    # p = 1 and p = 0 (contradiction)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, p, one))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, p, zero))

    result = solver.checkSat()
    is_unsat = str(result) == "unsat"

    return {
        "tautology": "p → p",
        "negation_asserted": "p ∧ ¬p",
        "result": str(result),
        "is_unsat": is_unsat,
        "tautology_verified": is_unsat,
        "pass": is_unsat,
        "reason": "cvc5 proves p→p is tautology by UNSAT on negation"
    }


def negative_test_cvc5_invalid_modus_ponens_premise():
    """
    Test: if premise p is false and p→q is true, q can be arbitrary.
    Assertion: ¬p ∧ (p → q) ∧ ¬q
    This should be SAT (no contradiction), showing modus ponens does not apply.
    """
    if not _cvc5_available:
        return {"status": "cvc5 not installed", "pass": False}

    solver = cvc5.Solver()
    solver.setLogic("QF_LRA")

    p = solver.mkConst(solver.getRealSort(), "p")
    q = solver.mkConst(solver.getRealSort(), "q")
    zero = solver.mkReal(0)
    one = solver.mkReal(1)

    # p, q are 0 or 1
    solver.assertFormula(solver.mkTerm(cvc5.Kind.OR,
        solver.mkTerm(cvc5.Kind.EQUAL, p, zero),
        solver.mkTerm(cvc5.Kind.EQUAL, p, one)
    ))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.OR,
        solver.mkTerm(cvc5.Kind.EQUAL, q, zero),
        solver.mkTerm(cvc5.Kind.EQUAL, q, one)
    ))

    # Assert: ¬p (p = 0)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, p, zero))

    # Assert: p → q (p ≤ q)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, p, q))

    # Assert: ¬q (q = 0)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, q, zero))

    result = solver.checkSat()
    is_sat = str(result) == "sat"

    return {
        "assertion": "¬p ∧ (p → q) ∧ ¬q",
        "result": str(result),
        "is_sat": is_sat,
        "modus_ponens_not_triggered": is_sat,
        "pass": is_sat,
        "reason": "SAT: modus ponens only applies when premise p is true"
    }


def boundary_test_cvc5_chain_modus_ponens():
    """
    Test: a chain of modus ponens applications.
    Assertions:
      - p (hypothesis)
      - p → q (first rule)
      - q → r (second rule)
    Denial: ¬r
    cvc5 should find UNSAT (r must follow by chain).
    """
    if not _cvc5_available:
        return {"status": "cvc5 not installed", "pass": False}

    solver = cvc5.Solver()
    solver.setLogic("QF_LRA")

    p = solver.mkConst(solver.getRealSort(), "p")
    q = solver.mkConst(solver.getRealSort(), "q")
    r = solver.mkConst(solver.getRealSort(), "r")
    zero = solver.mkReal(0)
    one = solver.mkReal(1)

    # p, q, r are 0 or 1
    for var in [p, q, r]:
        solver.assertFormula(solver.mkTerm(cvc5.Kind.OR,
            solver.mkTerm(cvc5.Kind.EQUAL, var, zero),
            solver.mkTerm(cvc5.Kind.EQUAL, var, one)
        ))

    # Assert: p = 1
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, p, one))

    # Assert: p → q (p ≤ q)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, p, q))

    # Assert: q → r (q ≤ r)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.LEQ, q, r))

    # Deny: r = 0
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, r, zero))

    result = solver.checkSat()
    is_unsat = str(result) == "unsat"

    return {
        "chain": "p ∧ (p→q) ∧ (q→r) ∧ ¬r",
        "result": str(result),
        "is_unsat": is_unsat,
        "chain_modus_ponens_valid": is_unsat,
        "pass": is_unsat,
        "reason": "cvc5 proves chain modus ponens derives r by transitivity"
    }


def boundary_test_sympy_implication_chain():
    """
    Test: verify implication chains via sympy.
    p → q → r means (p → (q → r)) in right-associative notation.
    """
    if not _sympy_available:
        return {"status": "sympy not installed", "pass": False}

    p, q, r = sp.symbols("p q r", integer=True)

    # Three implications in chain
    p_to_q = ~p | q  # p → q
    q_to_r = ~q | r  # q → r
    p_to_r = ~p | r  # p → r (transitive conclusion)

    # Check transitivity: (p→q) ∧ (q→r) → (p→r)
    # This should be a tautology
    tautology = ((p_to_q & q_to_r) >> p_to_r)

    # Evaluate at a few points
    test_cases = [
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 0),
        (0, 1, 1),
        (1, 0, 0),
        (1, 0, 1),
        (1, 1, 0),
        (1, 1, 1),
    ]

    all_true = True
    for pval, qval, rval in test_cases:
        subs = tautology.subs([(p, pval), (q, qval), (r, rval)])
        if not bool(subs):
            all_true = False
            break

    return {
        "formula": "(p→q) ∧ (q→r) → (p→r)",
        "is_tautology": all_true,
        "test_cases_passed": all_true,
        "pass": all_true,
        "reason": "sympy confirms implication chain is tautology on all truth values"
    }


def run_positive_tests():
    results = {}
    results.update(positive_test_cvc5_modus_ponens_sound())
    results.update(positive_test_sympy_implication_truth_table())
    results.update(positive_test_cvc5_tautology_p_to_p())
    return results


def run_negative_tests():
    results = {}
    results.update(negative_test_cvc5_invalid_modus_ponens_premise())
    return results


def run_boundary_tests():
    results = {}
    results.update(boundary_test_cvc5_chain_modus_ponens())
    results.update(boundary_test_sympy_implication_chain())
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = bool(pos.get("pass")) and bool(neg.get("pass")) and bool(bnd.get("pass"))

    results = {
        "name": "cvc5_frege_system_constraint",
        "classification": classification if all_pass else "classical_baseline",
        "original_classification": classification,
        "downgrade_reason": None if all_pass else "summary_all_pass_false_2026-05-01",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": {
            "all_pass": bool(all_pass),
            "cvc5_load_bearing": "UNSAT / SAT verdicts on modus ponens soundness and implication validity",
            "sympy_supportive": "symbolic truth tables and tautology verification",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cvc5_frege_system_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
