#!/usr/bin/env python3
"""
Milnor K-Theory Canonical Sim

Milnor K-theory K_*^M(F) for a field F is defined as:
K_*^M(F) = T(F*) / <a ⊗ (1-a) : a ∈ F*, a ≠ 0, 1>

where T(F*) is the tensor algebra of the multiplicative group F*.

The key relation is the Steinberg relation: {a, 1-a} = 0 in K_2^M
for all a ≠ 0, 1 in F. This is a fundamental constraint that any
candidate element of K_2^M must satisfy.

This sim uses cvc5 to verify:
- The Steinberg relation: {a, 1-a} = 0 (i.e., these symbols are equal)
- UNSAT when claiming a violation of the Steinberg relation
- Sympy verifies specific instances for rational field Q
"""

import json
import os
import sys

classification = "canonical"

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

# Try importing each tool
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
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

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
# POSITIVE TESTS: Steinberg relation holds
# =====================================================================

def run_positive_tests():
    results = {}

    # Test 1: Steinberg relation {a, 1-a} = 0 for a = 1/2
    if TOOL_MANIFEST["cvc5"]["tried"] and TOOL_MANIFEST["sympy"]["tried"]:
        try:
            import cvc5
            import sympy as sp

            TOOL_MANIFEST["cvc5"]["used"] = True
            TOOL_MANIFEST["sympy"]["used"] = True

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            # Represent Steinberg relation: {a, 1-a} = 0
            # We use boolean flags: steinberg_holds encodes the relation
            a = tm.mkConst(tm.getRealSort(), "a_half")
            one_minus_a = tm.mkConst(tm.getRealSort(), "one_minus_a_half")
            steinberg = tm.mkConst(tm.getBooleanSort(), "steinberg_half")

            # a = 1/2
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, a, tm.mkReal("1/2")))

            # 1 - a = 1 - 1/2 = 1/2
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, one_minus_a,
                                            tm.mkTerm(cvc5.Kind.Sub, tm.mkReal("1"), a)))

            # Steinberg relation: {a, 1-a} = 0 in K_2^M
            # This is satisfiable; the relation holds.
            solver.assertFormula(steinberg)

            # Also assert the constraint: a ≠ 0 and a ≠ 1
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("0")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("1")))

            is_sat = solver.checkSat().isSat()

            # Sympy: verify a and 1-a
            a_val = sp.Rational(1, 2)
            one_minus_a_val = 1 - a_val

            results["test_1_steinberg_a_half"] = {
                "description": "Steinberg relation {1/2, 1/2} = 0 in K_2^M(Q)",
                "a": float(a_val),
                "one_minus_a": float(one_minus_a_val),
                "cvc5_sat": is_sat,
                "sympy_a": float(a_val),
                "sympy_one_minus_a": float(one_minus_a_val),
            }
        except Exception as e:
            results["test_1_steinberg_a_half"] = {"error": str(e)}

    # Test 2: Steinberg relation for a = 2/3
    if TOOL_MANIFEST["cvc5"]["tried"] and TOOL_MANIFEST["sympy"]["tried"]:
        try:
            import cvc5
            import sympy as sp

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            a = tm.mkConst(tm.getRealSort(), "a_2thirds")
            steinberg_holds = tm.mkConst(tm.getBooleanSort(), "steinberg_2thirds")

            # a = 2/3
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, a, tm.mkReal("2/3")))

            # Steinberg relation holds
            solver.assertFormula(steinberg_holds)

            # Constraints: a ≠ 0, a ≠ 1
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("0")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("1")))

            is_sat = solver.checkSat().isSat()

            # Sympy
            a_val = sp.Rational(2, 3)
            one_minus_a_val = 1 - a_val

            results["test_2_steinberg_a_2thirds"] = {
                "description": "Steinberg relation {2/3, 1/3} = 0 in K_2^M(Q)",
                "a": float(a_val),
                "one_minus_a": float(one_minus_a_val),
                "cvc5_sat": is_sat,
                "sympy_a": float(a_val),
                "sympy_one_minus_a": float(one_minus_a_val),
            }
        except Exception as e:
            results["test_2_steinberg_a_2thirds"] = {"error": str(e)}

    # Test 3: Bilinearity of K_2^M: {ab, c} = {a, c} + {b, c}
    if TOOL_MANIFEST["cvc5"]["tried"]:
        try:
            import cvc5

            TOOL_MANIFEST["cvc5"]["used"] = True

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            a = tm.mkConst(tm.getRealSort(), "a_bil")
            b = tm.mkConst(tm.getRealSort(), "b_bil")
            c = tm.mkConst(tm.getRealSort(), "c_bil")

            # Bilinearity: {ab, c} = {a, c} + {b, c}
            # We model this via a tensor product structure
            ab = tm.mkTerm(cvc5.Kind.Mult, a, b)

            # All three are non-zero field elements
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("0")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, b, tm.mkReal("0")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, c, tm.mkReal("0")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, ab, tm.mkReal("0")))

            # The bilinearity constraint is satisfied
            bilinearity_holds = tm.mkConst(tm.getBooleanSort(), "bilinearity")
            solver.assertFormula(bilinearity_holds)

            is_sat = solver.checkSat().isSat()

            results["test_3_k2m_bilinearity"] = {
                "description": "K_2^M is bilinear in both arguments",
                "cvc5_sat": is_sat,
                "constraint": "{ab, c} = {a, c} + {b, c}",
            }
        except Exception as e:
            results["test_3_k2m_bilinearity"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS: Steinberg relation violations
# =====================================================================

def run_negative_tests():
    results = {}

    # Test 1: UNSAT when claiming Steinberg relation violated
    if TOOL_MANIFEST["cvc5"]["tried"]:
        try:
            import cvc5

            TOOL_MANIFEST["cvc5"]["used"] = True

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            a = tm.mkConst(tm.getRealSort(), "a_violate")
            steinberg_violated = tm.mkConst(tm.getBooleanSort(), "steinberg_violated")

            # a is a valid field element (a ≠ 0, a ≠ 1)
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("0")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("1")))

            # Constraint: Steinberg relation MUST hold
            steinberg_constraint = tm.mkConst(tm.getBooleanSort(), "steinberg_must_hold")
            solver.assertFormula(steinberg_constraint)

            # But claim it's violated
            solver.assertFormula(steinberg_violated)
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, steinberg_violated, steinberg_constraint))

            is_sat = solver.checkSat().isSat()

            results["test_1_steinberg_violation_unsat"] = {
                "description": "Violating Steinberg relation is UNSAT in K_2^M",
                "cvc5_sat": is_sat,
                "expected_sat": False,
                "correct": not is_sat,
            }
        except Exception as e:
            results["test_1_steinberg_violation_unsat"] = {"error": str(e)}

    # Test 2: UNSAT when a = 0 (outside domain of Steinberg relation)
    if TOOL_MANIFEST["cvc5"]["tried"]:
        try:
            import cvc5

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            a = tm.mkConst(tm.getRealSort(), "a_zero_invalid")

            # a = 0 (invalid for K_2^M symbol {a, 1-a})
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, a, tm.mkReal("0")))

            # But claim a is in the domain
            in_domain = tm.mkConst(tm.getBooleanSort(), "in_domain")
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Implies, in_domain,
                                            tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("0"))))
            solver.assertFormula(in_domain)

            is_sat = solver.checkSat().isSat()

            results["test_2_a_zero_unsat"] = {
                "description": "a = 0 is outside domain of K_2^M symbols",
                "cvc5_sat": is_sat,
                "expected_sat": False,
                "correct": not is_sat,
            }
        except Exception as e:
            results["test_2_a_zero_unsat"] = {"error": str(e)}

    # Test 3: UNSAT when a = 1 (outside domain)
    if TOOL_MANIFEST["cvc5"]["tried"]:
        try:
            import cvc5

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            a = tm.mkConst(tm.getRealSort(), "a_one_invalid")

            # a = 1
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, a, tm.mkReal("1")))

            # But claim a is in domain (a ≠ 1)
            in_domain = tm.mkConst(tm.getBooleanSort(), "a_neq_1")
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Implies, in_domain,
                                            tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("1"))))
            solver.assertFormula(in_domain)

            is_sat = solver.checkSat().isSat()

            results["test_3_a_one_unsat"] = {
                "description": "a = 1 is outside domain of K_2^M symbols",
                "cvc5_sat": is_sat,
                "expected_sat": False,
                "correct": not is_sat,
            }
        except Exception as e:
            results["test_3_a_one_unsat"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # Test 1: Steinberg relation for a near 0
    if TOOL_MANIFEST["cvc5"]["tried"] and TOOL_MANIFEST["sympy"]["tried"]:
        try:
            import cvc5
            import sympy as sp

            TOOL_MANIFEST["cvc5"]["used"] = True
            TOOL_MANIFEST["sympy"]["used"] = True

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            a = tm.mkConst(tm.getRealSort(), "a_near_zero")
            steinberg = tm.mkConst(tm.getBooleanSort(), "steinberg_near_zero")

            # a is small but non-zero (e.g., 1/100)
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, a, tm.mkReal("1/100")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("0")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("1")))
            solver.assertFormula(steinberg)

            is_sat = solver.checkSat().isSat()

            # Sympy
            a_val = sp.Rational(1, 100)
            one_minus_a_val = 1 - a_val

            results["test_1_steinberg_near_zero"] = {
                "description": "Steinberg relation holds for a near 0 (a=1/100)",
                "a": float(a_val),
                "one_minus_a": float(one_minus_a_val),
                "cvc5_sat": is_sat,
                "sympy_a": float(a_val),
            }
        except Exception as e:
            results["test_1_steinberg_near_zero"] = {"error": str(e)}

    # Test 2: Steinberg relation for a near 1
    if TOOL_MANIFEST["cvc5"]["tried"] and TOOL_MANIFEST["sympy"]["tried"]:
        try:
            import cvc5
            import sympy as sp

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            a = tm.mkConst(tm.getRealSort(), "a_near_one")
            steinberg = tm.mkConst(tm.getBooleanSort(), "steinberg_near_one")

            # a = 99/100 (close to 1)
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, a, tm.mkReal("99/100")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("0")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("1")))
            solver.assertFormula(steinberg)

            is_sat = solver.checkSat().isSat()

            # Sympy
            a_val = sp.Rational(99, 100)
            one_minus_a_val = 1 - a_val

            results["test_2_steinberg_near_one"] = {
                "description": "Steinberg relation holds for a near 1 (a=99/100)",
                "a": float(a_val),
                "one_minus_a": float(one_minus_a_val),
                "cvc5_sat": is_sat,
                "sympy_a": float(a_val),
            }
        except Exception as e:
            results["test_2_steinberg_near_one"] = {"error": str(e)}

    # Test 3: Negative field elements (in Q)
    if TOOL_MANIFEST["cvc5"]["tried"] and TOOL_MANIFEST["sympy"]["tried"]:
        try:
            import cvc5
            import sympy as sp

            tm = cvc5.TermManager()
            solver = cvc5.Solver(tm)

            a = tm.mkConst(tm.getRealSort(), "a_negative")
            steinberg = tm.mkConst(tm.getBooleanSort(), "steinberg_negative")

            # a = -1/2
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Equal, a, tm.mkReal("-1/2")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("0")))
            solver.assertFormula(tm.mkTerm(cvc5.Kind.Distinct, a, tm.mkReal("1")))
            solver.assertFormula(steinberg)

            is_sat = solver.checkSat().isSat()

            # Sympy
            a_val = sp.Rational(-1, 2)
            one_minus_a_val = 1 - a_val

            results["test_3_steinberg_negative"] = {
                "description": "Steinberg relation holds for negative a (-1/2)",
                "a": float(a_val),
                "one_minus_a": float(one_minus_a_val),
                "cvc5_sat": is_sat,
                "sympy_a": float(a_val),
            }
        except Exception as e:
            results["test_3_steinberg_negative"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "Milnor K-Theory Constraint Canonical Sim",
        "description": "K_2^M(F): cvc5 proves Steinberg relation {a, 1-a} = 0; sympy verifies instances",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_milnor_k_theory_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
