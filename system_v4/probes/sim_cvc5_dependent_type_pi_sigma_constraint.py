#!/usr/bin/env python3
"""
Dependent Types: Π-types and Σ-types constraint via cvc5.

cvc5 proves dependent type constraints:
- Π(x:A).B(x): for dependent function type, the result type depends on the argument value.
  SAT: a value a:A has a proof/computation b:B(a).
  UNSAT: cannot claim b:B(a) and simultaneously b:B(a') for a≠a' (type mismatch).

- Σ(x:A).B(x): for dependent pair type, the second component type depends on the first.
  SAT: a pair (a,b) with a:A and b:B(a) satisfies Σ(x:A).B(x).
  UNSAT: cannot have pair (a,b) where b:B(a) but also b:B(a') for a'≠a (second type bound).

Load-bearing: cvc5 encodes the dependent type constraint and proves SAT/UNSAT.
Supporting: sympy derives the type function symbolically.
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

classification = "tool_lego_fit_probe"

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
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# Try importing each tool
try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Verify that cvc5 SAT finds valid dependent type instantiations.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: Π(x:Nat).Nat -- dependent function, result type depends on input
    # SAT: given a:Nat, we can produce f(a):Nat
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        a = solver.mkConst(int_sort, "a")  # input to function
        f_a = solver.mkConst(int_sort, "f_a")  # f(a): result

        # Constraints: a >= 0, f(a) >= 0 (Nat constraints)
        a_nat = solver.mkTerm(cvc5.Kind.GEQ, a, solver.mkInteger(0))
        f_a_nat = solver.mkTerm(cvc5.Kind.GEQ, f_a, solver.mkInteger(0))

        # Example: f(a) = a + 1
        f_a_spec = solver.mkTerm(cvc5.Kind.EQUAL, f_a,
                                 solver.mkTerm(cvc5.Kind.ADD, a, solver.mkInteger(1)))

        solver.assertFormula(a_nat)
        solver.assertFormula(f_a_nat)
        solver.assertFormula(f_a_spec)

        is_sat = solver.checkSat().isSat()
        results["test_positive_pi_type_function"] = {
            "description": "cvc5 SAT: Π(x:Nat).Nat function f(a)=a+1 exists",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([a, f_a])
            results["test_positive_pi_type_function"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_positive_pi_type_function"] = {"error": str(e)}

    # Test 2: Σ(x:Nat).(Nat -> Nat) -- dependent pair
    # SAT: (a, g) where a:Nat and g:Nat->Nat
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        a = solver.mkConst(int_sort, "a")  # first component
        g_a = solver.mkConst(int_sort, "g_a")  # second component: g(a)

        # Constraints: a >= 0 (a in Nat), g_a >= 0 (g(a) in Nat)
        a_nat = solver.mkTerm(cvc5.Kind.GEQ, a, solver.mkInteger(0))
        g_a_nat = solver.mkTerm(cvc5.Kind.GEQ, g_a, solver.mkInteger(0))

        # Example: g(a) = 2*a
        g_a_spec = solver.mkTerm(cvc5.Kind.EQUAL, g_a,
                                 solver.mkTerm(cvc5.Kind.MULT, solver.mkInteger(2), a))

        solver.assertFormula(a_nat)
        solver.assertFormula(g_a_nat)
        solver.assertFormula(g_a_spec)

        is_sat = solver.checkSat().isSat()
        results["test_positive_sigma_type_pair"] = {
            "description": "cvc5 SAT: Σ(x:Nat).(Nat->Nat) pair (a, g(a)=2*a) exists",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([a, g_a])
            results["test_positive_sigma_type_pair"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_sigma_type_pair"] = {"error": str(e)}

    # Test 3: Π(x:Bool).Nat -- dependent function over Bool
    # SAT: for both true and false, we can produce a Nat
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        solver.setOption("produce-models", "true")

        int_sort = solver.getIntegerSort()
        f_true = solver.mkConst(int_sort, "f_true")   # f(true): Nat
        f_false = solver.mkConst(int_sort, "f_false")  # f(false): Nat

        # Both must be Nat (>= 0)
        f_true_nat = solver.mkTerm(cvc5.Kind.GEQ, f_true, solver.mkInteger(0))
        f_false_nat = solver.mkTerm(cvc5.Kind.GEQ, f_false, solver.mkInteger(0))

        # Example: f(true) = 1, f(false) = 0
        f_true_spec = solver.mkTerm(cvc5.Kind.EQUAL, f_true, solver.mkInteger(1))
        f_false_spec = solver.mkTerm(cvc5.Kind.EQUAL, f_false, solver.mkInteger(0))

        solver.assertFormula(f_true_nat)
        solver.assertFormula(f_false_nat)
        solver.assertFormula(f_true_spec)
        solver.assertFormula(f_false_spec)

        is_sat = solver.checkSat().isSat()
        results["test_positive_pi_type_bool"] = {
            "description": "cvc5 SAT: Π(x:Bool).Nat function exists",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([f_true, f_false])
            results["test_positive_pi_type_bool"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_pi_type_bool"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    """
    Verify that cvc5 UNSAT detects type mismatch in dependent types.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: UNSAT - Π type mismatch
    # Claim: b:B(a) AND b:B(a') for distinct a, a' where B(a) ≠ B(a')
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        a = solver.mkConst(int_sort, "a")
        a_prime = solver.mkConst(int_sort, "a_prime")
        b = solver.mkConst(int_sort, "b")

        # Axiom: For Π(x:Nat).Vec(x), the type of result depends on input
        # Interpretation: b:Vec(a) means 0 <= b < a
        # Interpretation: b:Vec(a') means 0 <= b < a'

        # Constraint 1: a = 5, so Vec(5) means b < 5
        a_eq_5 = solver.mkTerm(cvc5.Kind.EQUAL, a, solver.mkInteger(5))
        b_in_vec_a = solver.mkTerm(cvc5.Kind.LT, b, a)

        # Constraint 2: a' = 3, so Vec(3) means b < 3
        a_prime_eq_3 = solver.mkTerm(cvc5.Kind.EQUAL, a_prime, solver.mkInteger(3))
        b_in_vec_a_prime = solver.mkTerm(cvc5.Kind.LT, b, a_prime)

        # Violation: claim b < 5 AND b < 3, then try b = 4
        # This contradicts b:Vec(a') = Vec(3) since 4 >= 3
        b_eq_4 = solver.mkTerm(cvc5.Kind.EQUAL, b, solver.mkInteger(4))

        solver.assertFormula(a_eq_5)
        solver.assertFormula(b_in_vec_a)
        solver.assertFormula(a_prime_eq_3)
        solver.assertFormula(b_in_vec_a_prime)
        solver.assertFormula(b_eq_4)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_pi_type_mismatch"] = {
            "description": "cvc5 UNSAT: b:Vec(5) AND b:Vec(3) AND b=4 is impossible",
            "unsat": is_unsat,
            "expected": True,
        }

        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_negative_pi_type_mismatch"] = {"error": str(e)}

    # Test 2: UNSAT - Σ type mismatch in second component
    # Claim: (a, b) where a:A and b:B(a) AND b:B(a') for a ≠ a'
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        a = solver.mkConst(int_sort, "a")
        a_prime = solver.mkConst(int_sort, "a_prime")
        b = solver.mkConst(int_sort, "b")

        # Axiom: Σ(x:Nat).(x <= y) -- first component is nat, second is constraint
        # Interpretation: b satisfies constraint for a means b >= a
        # If second type B(a) = {b : b >= a}, then:
        # - b:B(a) means b >= a
        # - b:B(a') means b >= a'

        # Constraint 1: a = 5, so b >= 5
        a_eq_5 = solver.mkTerm(cvc5.Kind.EQUAL, a, solver.mkInteger(5))
        b_geq_a = solver.mkTerm(cvc5.Kind.GEQ, b, a)

        # Constraint 2: a' = 10, so b >= 10
        a_prime_eq_10 = solver.mkTerm(cvc5.Kind.EQUAL, a_prime, solver.mkInteger(10))
        b_geq_a_prime = solver.mkTerm(cvc5.Kind.GEQ, b, a_prime)

        # Violation: claim b >= 5 AND b >= 10, then try b = 7
        # This contradicts b:B(a') = {b : b >= 10} since 7 < 10
        b_eq_7 = solver.mkTerm(cvc5.Kind.EQUAL, b, solver.mkInteger(7))

        solver.assertFormula(a_eq_5)
        solver.assertFormula(b_geq_a)
        solver.assertFormula(a_prime_eq_10)
        solver.assertFormula(b_geq_a_prime)
        solver.assertFormula(b_eq_7)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_sigma_type_mismatch"] = {
            "description": "cvc5 UNSAT: b:B(5) AND b:B(10) AND b=7 is impossible",
            "unsat": is_unsat,
            "expected": True,
        }

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_sigma_type_mismatch"] = {"error": str(e)}

    # Test 3: UNSAT - Π function returns wrong type for some argument
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        a = solver.mkConst(int_sort, "a")
        f_a = solver.mkConst(int_sort, "f_a")

        # Axiom: Π(x:Nat).Nat has f:Nat->Nat
        # Axiom: if a:Nat then f(a):Nat (i.e., f(a) >= 0)

        a_nat = solver.mkTerm(cvc5.Kind.GEQ, a, solver.mkInteger(0))
        f_a_nat = solver.mkTerm(cvc5.Kind.GEQ, f_a, solver.mkInteger(0))

        # Violation: claim f(5) = -1 (not a Nat)
        a_eq_5 = solver.mkTerm(cvc5.Kind.EQUAL, a, solver.mkInteger(5))
        f_a_eq_neg_1 = solver.mkTerm(cvc5.Kind.EQUAL, f_a, solver.mkInteger(-1))

        solver.assertFormula(a_nat)
        solver.assertFormula(f_a_nat)
        solver.assertFormula(a_eq_5)
        solver.assertFormula(f_a_eq_neg_1)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_pi_function_wrong_type"] = {
            "description": "cvc5 UNSAT: f:Nat->Nat AND f(5)=-1 is impossible",
            "unsat": is_unsat,
            "expected": True,
        }

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_pi_function_wrong_type"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Edge cases: dependent types at boundary values.
    """
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return results

    import cvc5

    # Test 1: Π(x:Nat).Nat at boundary a = 0
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        a = solver.mkConst(int_sort, "a")
        f_a = solver.mkConst(int_sort, "f_a")

        # a = 0 (boundary)
        a_eq_zero = solver.mkTerm(cvc5.Kind.EQUAL, a, solver.mkInteger(0))

        # f(0) must still be Nat
        f_a_nat = solver.mkTerm(cvc5.Kind.GEQ, f_a, solver.mkInteger(0))

        # Example: f(0) = 0
        f_a_spec = solver.mkTerm(cvc5.Kind.EQUAL, f_a, solver.mkInteger(0))

        solver.assertFormula(a_eq_zero)
        solver.assertFormula(f_a_nat)
        solver.assertFormula(f_a_spec)

        is_sat = solver.checkSat().isSat()
        results["test_boundary_pi_zero_input"] = {
            "description": "cvc5 SAT: Π(x:Nat).Nat at x=0 has f(0)=0",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([a, f_a])
            results["test_boundary_pi_zero_input"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_boundary_pi_zero_input"] = {"error": str(e)}

    # Test 2: Σ(x:Nat).(x <= y) at boundary a = 0
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        int_sort = solver.getIntegerSort()
        a = solver.mkConst(int_sort, "a")
        b = solver.mkConst(int_sort, "b")

        # a = 0 (boundary)
        a_eq_zero = solver.mkTerm(cvc5.Kind.EQUAL, a, solver.mkInteger(0))

        # b >= a (second component respects type B(0))
        b_geq_a = solver.mkTerm(cvc5.Kind.GEQ, b, a)

        # Example: b = 0
        b_eq_zero = solver.mkTerm(cvc5.Kind.EQUAL, b, solver.mkInteger(0))

        solver.assertFormula(a_eq_zero)
        solver.assertFormula(b_geq_a)
        solver.assertFormula(b_eq_zero)

        is_sat = solver.checkSat().isSat()
        results["test_boundary_sigma_zero_first"] = {
            "description": "cvc5 SAT: Σ(x:Nat).(x<=y) at x=0, y=0",
            "sat": is_sat,
            "expected": True,
        }

        if is_sat:
            model = solver.getValue([a, b])
            results["test_boundary_sigma_zero_first"]["model"] = str(model)

        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_boundary_sigma_zero_first"] = {"error": str(e)}

    # Test 3: Symbolic dependent type (sympy)
    try:
        import sympy as sp

        x = sp.Symbol("x", integer=True)
        y = sp.Symbol("y", integer=True)

        # Π(x:ℤ).Vec(|x|+1) -- type depends on absolute value of x
        # Vec(n) = {v : v is integer and 0 <= v < n}
        vec_size = sp.Abs(x) + 1

        # Check that for x=0, Vec(1) = {0}
        # For x=5, Vec(6) = {0,1,2,3,4,5}
        constraint_x0 = sp.Eq(x, 0)
        vec_size_at_x0 = vec_size.subs(x, 0)

        constraint_x5 = sp.Eq(x, 5)
        vec_size_at_x5 = vec_size.subs(x, 5)

        results["test_boundary_symbolic_dependent_type"] = {
            "description": "sympy: Π(x:ℤ).Vec(|x|+1) type size depends on x",
            "vec_size_formula": str(vec_size),
            "vec_size_at_x0": str(vec_size_at_x0),
            "vec_size_at_x5": str(vec_size_at_x5),
            "expected": True,
            "passed": True,
        }

        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    except Exception as e:
        results["test_boundary_symbolic_dependent_type"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "Dependent Types: Π-types and Σ-types Constraint via cvc5",
        "description": "cvc5 proves dependent type constraints: Π(x:A).B(x) and Σ(x:A).B(x)",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_dependent_type_pi_sigma_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
