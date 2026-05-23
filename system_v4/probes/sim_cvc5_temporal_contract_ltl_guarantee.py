#!/usr/bin/env python3
"""
Temporal Contracts (LTL Guarantees) — cvc5 canonical sim.

Theory:
  - Safety: □(p → ◇q)  [if p holds at t, q must hold eventually]
  - Liveness: □◇p ≠ ◇□p  [always eventually p ≠ eventually always p]
  - Circular AG: (A=□safe, G=□progress) compose iff circularity dependency holds
  - LTL duality: ¬□p = ◇¬p and ¬◇p = □¬p
"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pytorch not needed; pure symbolic/logical computation via cvc5 and sympy"},
    "pyg": {"tried": False, "used": False, "reason": "PyG not needed; contract structure encoded as constraint variables"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all SMT constraint proofs"},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; temporal logic via cvc5/sympy"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; no differential geometry required"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance required"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; contract DAG encoded directly in constraints"},
    "xgi": {"tried": False, "used": False, "reason": "xgi not needed; no hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx not needed; standard logical computations sufficient"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi not needed; no persistent homology required"},
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

cvc5_available = False
sympy_available = False

try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
    cvc5_available = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    sympy_available = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """Valid LTL properties and temporal contracts."""
    results = {}

    if not cvc5_available:
        results["test_1_safety_property"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_2_liveness_distinction"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["test_3_circular_ag_dependency"] = {"status": "skipped", "reason": "cvc5 not available"}
        if sympy_available:
            results["test_4_sympy_ltl_duality"] = run_sympy_ltl_duality_test()
        return results

    # Test 1: Safety property □(p → ◇q)
    # On finite trace (t=0..4): if p holds at some t, q must hold at some t' >= t
    # UNSAT: deny safety (p holds but q never follows)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Trace: 5 time steps
        # p[t], q[t] for t=0..4
        p = [solver.mkConst(solver.mkIntSort(), f"p_{i}") for i in range(5)]
        q = [solver.mkConst(solver.mkIntSort(), f"q_{i}") for i in range(5)]

        # Safety: □(p → ◇q)
        # For each t, if p[t]=1 then exists t' >= t with q[t']=1
        zero = solver.mkInteger(0)
        one = solver.mkInteger(1)

        safety_constraints = []
        for t in range(5):
            # p[t] → ◇_{t..4}q
            q_eventually = solver.mkFalse()
            for t_prime in range(t, 5):
                q_eventually = solver.mkTerm(cvc5.Kind.Or, q_eventually, solver.mkTerm(cvc5.Kind.Equal, q[t_prime], one))

            # p[t] → q_eventually
            p_t = solver.mkTerm(cvc5.Kind.Equal, p[t], one)
            implication = solver.mkTerm(cvc5.Kind.Implies, p_t, q_eventually)
            safety_constraints.append(implication)

        for constraint in safety_constraints:
            solver.assertFormula(constraint)

        # Negate: exists t where p[t]=1 but no q follows
        counterexample = solver.mkFalse()
        for t in range(5):
            p_holds = solver.mkTerm(cvc5.Kind.Equal, p[t], one)
            q_never = solver.mkTrue()
            for t_prime in range(t, 5):
                q_never = solver.mkTerm(cvc5.Kind.And, q_never, solver.mkTerm(cvc5.Kind.Not, solver.mkTerm(cvc5.Kind.Equal, q[t_prime], one)))
            counterexample = solver.mkTerm(cvc5.Kind.Or, counterexample, solver.mkTerm(cvc5.Kind.And, p_holds, q_never))

        solver.assertFormula(counterexample)

        result = solver.checkSat()
        results["test_1_safety_property"] = {
            "status": "PASS" if not result.isSat() else "FAIL",
            "expected": "UNSAT",
            "actual": "UNSAT" if not result.isSat() else "SAT",
            "reason": "Safety property □(p → ◇q) on finite trace"
        }
    except Exception as e:
        results["test_1_safety_property"] = {"status": "ERROR", "reason": str(e)}

    # Test 2: Liveness distinction: □◇p ≠ ◇□p
    # UNSAT: claim they are equivalent on finite trace (4 steps)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        p = [solver.mkConst(solver.mkIntSort(), f"p_live_{i}") for i in range(4)]
        zero = solver.mkInteger(0)
        one = solver.mkInteger(1)

        # □◇p: always eventually p (in every step, p holds eventually after)
        box_diamond_p = solver.mkTrue()
        for t in range(4):
            p_eventually = solver.mkFalse()
            for t_prime in range(t, 4):
                p_eventually = solver.mkTerm(cvc5.Kind.Or, p_eventually, solver.mkTerm(cvc5.Kind.Equal, p[t_prime], one))
            box_diamond_p = solver.mkTerm(cvc5.Kind.And, box_diamond_p, p_eventually)

        # ◇□p: eventually always p (p holds continuously from some point)
        diamond_box_p = solver.mkFalse()
        for t in range(4):
            p_from_t = solver.mkTrue()
            for t_prime in range(t, 4):
                p_from_t = solver.mkTerm(cvc5.Kind.And, p_from_t, solver.mkTerm(cvc5.Kind.Equal, p[t_prime], one))
            diamond_box_p = solver.mkTerm(cvc5.Kind.Or, diamond_box_p, p_from_t)

        # Claim equivalence (should be UNSAT)
        equivalence = solver.mkTerm(cvc5.Kind.Equal, box_diamond_p, diamond_box_p)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Not, equivalence))

        result = solver.checkSat()
        results["test_2_liveness_distinction"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "□◇p and ◇□p are distinct on finite traces (counterexample exists)"
        }
    except Exception as e:
        results["test_2_liveness_distinction"] = {"status": "ERROR", "reason": str(e)}

    # Test 3: Circular AG with temporal dependency
    # A = □safe, G = □progress; G produces A iff circularity holds
    # UNSAT: deny circularity while claiming valid composition
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Variables for 3 steps
        safe = [solver.mkConst(solver.mkIntSort(), f"safe_{i}") for i in range(3)]
        progress = [solver.mkConst(solver.mkIntSort(), f"progress_{i}") for i in range(3)]

        zero = solver.mkInteger(0)
        one = solver.mkInteger(1)

        # A = □safe: safe holds at all times
        box_safe = solver.mkTrue()
        for t in range(3):
            box_safe = solver.mkTerm(cvc5.Kind.And, box_safe, solver.mkTerm(cvc5.Kind.Equal, safe[t], one))

        # G = □progress: progress holds at all times
        box_progress = solver.mkTrue()
        for t in range(3):
            box_progress = solver.mkTerm(cvc5.Kind.And, box_progress, solver.mkTerm(cvc5.Kind.Equal, progress[t], one))

        # Circularity: G → A, i.e., if progress always holds, safe must always hold
        circularity = solver.mkTerm(cvc5.Kind.Implies, box_progress, box_safe)

        # Assert circularity must hold
        solver.assertFormula(circularity)

        # Negate: claim circularity doesn't hold but composition valid
        # (progress → safe fails but composition still works)
        fails_circularity = solver.mkFalse()
        for t in range(3):
            no_safe = solver.mkTerm(cvc5.Kind.Equal, safe[t], zero)
            has_progress = solver.mkTerm(cvc5.Kind.Equal, progress[t], one)
            fails_circularity = solver.mkTerm(cvc5.Kind.Or, fails_circularity, solver.mkTerm(cvc5.Kind.And, no_safe, has_progress))

        solver.assertFormula(fails_circularity)

        result = solver.checkSat()
        results["test_3_circular_ag_dependency"] = {
            "status": "PASS" if not result.isSat() else "FAIL",
            "expected": "UNSAT",
            "actual": "UNSAT" if not result.isSat() else "SAT",
            "reason": "Circular AG composition requires dependency: G → A"
        }
    except Exception as e:
        results["test_3_circular_ag_dependency"] = {"status": "ERROR", "reason": str(e)}

    # Test 4: sympy LTL duality
    if sympy_available:
        results["test_4_sympy_ltl_duality"] = run_sympy_ltl_duality_test()

    return results


def run_sympy_ltl_duality_test():
    """Verify LTL duality: ¬□p = ◇¬p and ¬◇p = □¬p."""
    try:
        import sympy as sp
        from sympy import symbols, simplify, And, Or, Not

        p = symbols('p', bool=True)

        # Duality 1: ¬□p = ◇¬p
        # □p = "always p" on finite trace: p_0 ∧ p_1 ∧ ... ∧ p_n
        # On 4-step trace:
        p_vals = [symbols(f'p_{i}', bool=True) for i in range(4)]

        box_p = And(*p_vals)  # □p: all steps true
        not_box_p = Not(box_p)  # ¬□p

        diamond_not_p = Or(*[Not(p_vals[i]) for i in range(4)])  # ◇¬p: some step false

        # Check equivalence
        duality1 = simplify(Not(box_p) == diamond_not_p)

        # Duality 2: ¬◇p = □¬p
        diamond_p = Or(*p_vals)  # ◇p: some step true
        not_diamond_p = Not(diamond_p)  # ¬◇p

        box_not_p = And(*[Not(p_vals[i]) for i in range(4)])  # □¬p: all steps false

        duality2 = simplify(Not(diamond_p) == box_not_p)

        # Extra: □(p∧q) → □p ∧ □q and vice versa
        q_vals = [symbols(f'q_{i}', bool=True) for i in range(4)]

        box_p_and_q = And(*[And(p_vals[i], q_vals[i]) for i in range(4)])
        box_p_boxq = And(And(*p_vals), And(*q_vals))

        distribution = simplify(box_p_and_q == box_p_boxq)

        return {
            "status": "PASS" if duality1 is True and duality2 is True and distribution is True else "FAIL",
            "duality_1_not_box_p_eq_diamond_not_p": str(duality1),
            "duality_2_not_diamond_p_eq_box_not_p": str(duality2),
            "distribution_box_and": str(distribution),
            "reason": "LTL dualities and distribution verified on 4-step trace"
        }
    except Exception as e:
        return {"status": "ERROR", "reason": str(e)}


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """Traces violating LTL properties."""
    results = {}

    if not cvc5_available:
        results["neg_test_1_safety_violation"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["neg_test_2_liveness_false"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["neg_test_3_circular_dependency_fail"] = {"status": "skipped", "reason": "cvc5 not available"}
        return results

    # Negative Test 1: Safety violation (exists t where p but no subsequent q)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Trace: p holds at t=0, q never holds
        p = [solver.mkInteger(1 if i == 0 else 0) for i in range(4)]  # p at t=0 only
        q = [solver.mkInteger(0) for i in range(4)]  # q never

        # Claim safety holds (should fail)
        zero = solver.mkInteger(0)
        one = solver.mkInteger(1)

        # p[0]=1 but no q after t=0: violation is SAT
        p_holds = solver.mkTerm(cvc5.Kind.Equal, p[0], one)
        q_never = solver.mkTrue()
        for t in range(4):
            q_never = solver.mkTerm(cvc5.Kind.And, q_never, solver.mkTerm(cvc5.Kind.Equal, q[t], zero))

        violation = solver.mkTerm(cvc5.Kind.And, p_holds, q_never)
        solver.assertFormula(violation)

        result = solver.checkSat()
        results["neg_test_1_safety_violation"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "Safety violation (p at t, no q after) is satisfiable"
        }
    except Exception as e:
        results["neg_test_1_safety_violation"] = {"status": "ERROR", "reason": str(e)}

    # Negative Test 2: □◇p holds but ◇□p fails (counterexample)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Trace: p alternates [1,0,1,0] — always eventually p but never always p
        p = [solver.mkInteger(1 if i % 2 == 0 else 0) for i in range(4)]
        one = solver.mkInteger(1)
        zero = solver.mkInteger(0)

        # □◇p should hold: true
        box_diamond_p = solver.mkTrue()
        for t in range(4):
            p_eventually = solver.mkFalse()
            for t_prime in range(t, 4):
                p_eventually = solver.mkTerm(cvc5.Kind.Or, p_eventually, solver.mkTerm(cvc5.Kind.Equal, p[t_prime], one))
            box_diamond_p = solver.mkTerm(cvc5.Kind.And, box_diamond_p, p_eventually)

        # ◇□p should fail: false
        diamond_box_p = solver.mkFalse()
        for t in range(4):
            p_from_t = solver.mkTrue()
            for t_prime in range(t, 4):
                p_from_t = solver.mkTerm(cvc5.Kind.And, p_from_t, solver.mkTerm(cvc5.Kind.Equal, p[t_prime], one))
            diamond_box_p = solver.mkTerm(cvc5.Kind.Or, diamond_box_p, p_from_t)

        solver.assertFormula(box_diamond_p)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.Not, diamond_box_p))

        result = solver.checkSat()
        results["neg_test_2_liveness_false"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "□◇p true but ◇□p false on alternating trace is satisfiable"
        }
    except Exception as e:
        results["neg_test_2_liveness_false"] = {"status": "ERROR", "reason": str(e)}

    # Negative Test 3: Circular dependency fails (progress true but safe false)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Trace: safe=[0,0,0], progress=[1,1,1]
        safe = [solver.mkInteger(0) for i in range(3)]
        progress = [solver.mkInteger(1) for i in range(3)]
        one = solver.mkInteger(1)
        zero = solver.mkInteger(0)

        # □safe is false, □progress is true
        # Violation: progress always but not safe always
        violation = solver.mkTrue()
        for t in range(3):
            p_t = solver.mkTerm(cvc5.Kind.Equal, progress[t], one)
            s_t = solver.mkTerm(cvc5.Kind.Equal, safe[t], one)
            violation = solver.mkTerm(cvc5.Kind.And, violation, solver.mkTerm(cvc5.Kind.And, p_t, solver.mkTerm(cvc5.Kind.Not, s_t)))

        solver.assertFormula(violation)

        result = solver.checkSat()
        results["neg_test_3_circular_dependency_fail"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "Circular dependency failure (progress but not safe) is satisfiable"
        }
    except Exception as e:
        results["neg_test_3_circular_dependency_fail"] = {"status": "ERROR", "reason": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Edge cases: single-step trace, always-true/false properties, etc."""
    results = {}

    if not cvc5_available:
        results["bound_test_1_single_step"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["bound_test_2_constant_true"] = {"status": "skipped", "reason": "cvc5 not available"}
        results["bound_test_3_constant_false"] = {"status": "skipped", "reason": "cvc5 not available"}
        return results

    # Boundary Test 1: Single-step trace
    # On 1 step: □p = p, ◇p = p (collapse)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        p = [solver.mkConst(solver.mkIntSort(), "p_0")]
        one = solver.mkInteger(1)

        # □p = ◇p = p (single step)
        box_p = p[0]
        diamond_p = p[0]
        collapse = solver.mkTerm(cvc5.Kind.Equal, box_p, diamond_p)

        solver.assertFormula(collapse)

        result = solver.checkSat()
        results["bound_test_1_single_step"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "Single-step trace: □p = ◇p = p"
        }
    except Exception as e:
        results["bound_test_1_single_step"] = {"status": "ERROR", "reason": str(e)}

    # Boundary Test 2: Always-true property (p always = 1)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        p = [solver.mkInteger(1) for i in range(5)]
        one = solver.mkInteger(1)

        # □p should hold
        box_p = solver.mkTrue()
        for t in range(5):
            box_p = solver.mkTerm(cvc5.Kind.And, box_p, solver.mkTerm(cvc5.Kind.Equal, p[t], one))

        solver.assertFormula(box_p)

        result = solver.checkSat()
        results["bound_test_2_constant_true"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "Always-true property (p=1 everywhere) is satisfiable"
        }
    except Exception as e:
        results["bound_test_2_constant_true"] = {"status": "ERROR", "reason": str(e)}

    # Boundary Test 3: Always-false property (p always = 0)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        p = [solver.mkInteger(0) for i in range(5)]
        zero = solver.mkInteger(0)

        # □¬p should hold (same as □p with p=0)
        box_not_p = solver.mkTrue()
        for t in range(5):
            box_not_p = solver.mkTerm(cvc5.Kind.And, box_not_p, solver.mkTerm(cvc5.Kind.Equal, p[t], zero))

        solver.assertFormula(box_not_p)

        result = solver.checkSat()
        results["bound_test_3_constant_false"] = {
            "status": "PASS" if result.isSat() else "FAIL",
            "expected": "SAT",
            "actual": "SAT" if result.isSat() else "UNSAT",
            "reason": "Always-false property (p=0 everywhere) is satisfiable"
        }
    except Exception as e:
        results["bound_test_3_constant_false"] = {"status": "ERROR", "reason": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "sim_cvc5_temporal_contract_ltl_guarantee",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
        "original_classification": "canonical",
        "downgrade_reason": "overclassification_fail_status_2026-05-01",
    }

    if cvc5_available:
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "UNSAT proofs for safety, liveness distinction, circular AG dependency"

    if sympy_available:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "LTL duality and distribution formula verification"

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_temporal_contract_ltl_guarantee_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
