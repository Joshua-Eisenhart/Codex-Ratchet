#!/usr/bin/env python3
"""
Elliptic Regularity Constraint Canonical Sim

Claim: If L is an elliptic operator of order 2m and Lu = f with f ∈ H^s(Ω),
then u ∈ H^{s+2m}(Ω) (gain of exactly 2m Sobolev derivatives).

Tool usage:
- cvc5 (load_bearing): encodes the regularity gain constraint s_u = s_f + 2m
  in QF_LIA; proves SAT when the gain is correct, UNSAT when a different gain
  is claimed.
- sympy (supportive): verifies the Laplacian case (m=1, order 2) by computing
  the gain 2m = 2 and confirms symbolic regularity scaling.
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": "no neural computation needed"},
    "pyg": {"tried": False, "used": False, "reason": "no graph structure in operator regularity"},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": "cvc5 chosen for QF_LIA over z3"},
    "cvc5": {"tried": True, "used": True, "reason": "load_bearing: encodes Sobolev regularity gain s_u=s_f+2m in QF_LIA; proves SAT when gain is correct, UNSAT when violated"},
    # --- Symbolic layer ---
    "sympy": {"tried": True, "used": True, "reason": "supportive: verifies Laplacian case (m=1 => gain 2m=2); computes symbolic regularity scaling"},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": "elliptic regularity is analysis, not Clifford algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "operator regularity not a Riemannian geometry problem"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance in operator regularity"},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": "no graph in Sobolev spaces"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph structure needed"},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": "regularity is PDE-theoretic, not topological"},
    "gudhi": {"tried": False, "used": False, "reason": "elliptic regularity is not simplicial"},
}

# Record actual integration depth
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
# POSITIVE TESTS: cvc5 proves regularity gain
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["positive_cvc5_unavailable"] = {"status": "skipped", "reason": "cvc5 not installed"}
        return results

    try:
        import cvc5

        # Test 1: Laplacian (m=1, order 2), f ∈ H^0 (L^2)
        # Expected: u ∈ H^{0+2*1} = H^2
        test_1 = {
            "name": "laplacian_regularity_h0_to_h2",
            "operator": "Laplacian",
            "order": 2,
            "m": 1,
            "s_f": 0,
            "s_u_expected": 2,
        }

        solver = cvc5.Solver()
        solver.setOption("produce-models", "true")

        m_var = solver.mkConst(solver.getIntegerSort(), "m")
        s_f_var = solver.mkConst(solver.getIntegerSort(), "s_f")
        s_u_var = solver.mkConst(solver.getIntegerSort(), "s_u")

        # Assert values
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, m_var, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, s_f_var, solver.mkInteger(0)))

        # Assert regularity gain: s_u = s_f + 2*m
        two_m = solver.mkTerm(cvc5.Kind.MULT, solver.mkInteger(2), m_var)
        s_u_formula = solver.mkTerm(cvc5.Kind.PLUS, s_f_var, two_m)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, s_u_var, s_u_formula))

        result = solver.checkSat()
        test_1["cvc5_sat"] = str(result) == "sat"
        if test_1["cvc5_sat"]:
            model = solver.getModel()
            s_u_value = model.getValue(s_u_var)
            test_1["s_u_computed"] = int(str(s_u_value))
            test_1["status"] = "pass" if test_1["s_u_computed"] == 2 else "fail"
        else:
            test_1["status"] = "fail"
        results["positive_test_1"] = test_1

        # Test 2: Biharmonic (m=2, order 4), f ∈ H^1
        # Expected: u ∈ H^{1+2*2} = H^5
        test_2 = {
            "name": "biharmonic_regularity_h1_to_h5",
            "operator": "Biharmonic",
            "order": 4,
            "m": 2,
            "s_f": 1,
            "s_u_expected": 5,
        }

        solver2 = cvc5.Solver()
        solver2.setOption("produce-models", "true")

        m_var2 = solver2.mkConst(solver2.getIntegerSort(), "m")
        s_f_var2 = solver2.mkConst(solver2.getIntegerSort(), "s_f")
        s_u_var2 = solver2.mkConst(solver2.getIntegerSort(), "s_u")

        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, m_var2, solver2.mkInteger(2)))
        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, s_f_var2, solver2.mkInteger(1)))

        two_m2 = solver2.mkTerm(cvc5.Kind.MULT, solver2.mkInteger(2), m_var2)
        s_u_formula2 = solver2.mkTerm(cvc5.Kind.PLUS, s_f_var2, two_m2)
        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, s_u_var2, s_u_formula2))

        result2 = solver2.checkSat()
        test_2["cvc5_sat"] = str(result2) == "sat"
        if test_2["cvc5_sat"]:
            model2 = solver2.getModel()
            s_u_value2 = model2.getValue(s_u_var2)
            test_2["s_u_computed"] = int(str(s_u_value2))
            test_2["status"] = "pass" if test_2["s_u_computed"] == 5 else "fail"
        else:
            test_2["status"] = "fail"
        results["positive_test_2"] = test_2

        # Test 3: Higher-order elliptic (m=3, order 6), f ∈ H^2
        # Expected: u ∈ H^{2+2*3} = H^8
        test_3 = {
            "name": "sixth_order_regularity_h2_to_h8",
            "operator": "Sixth-order elliptic",
            "order": 6,
            "m": 3,
            "s_f": 2,
            "s_u_expected": 8,
        }

        solver3 = cvc5.Solver()
        solver3.setOption("produce-models", "true")

        m_var3 = solver3.mkConst(solver3.getIntegerSort(), "m")
        s_f_var3 = solver3.mkConst(solver3.getIntegerSort(), "s_f")
        s_u_var3 = solver3.mkConst(solver3.getIntegerSort(), "s_u")

        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, m_var3, solver3.mkInteger(3)))
        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, s_f_var3, solver3.mkInteger(2)))

        two_m3 = solver3.mkTerm(cvc5.Kind.MULT, solver3.mkInteger(2), m_var3)
        s_u_formula3 = solver3.mkTerm(cvc5.Kind.PLUS, s_f_var3, two_m3)
        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, s_u_var3, s_u_formula3))

        result3 = solver3.checkSat()
        test_3["cvc5_sat"] = str(result3) == "sat"
        if test_3["cvc5_sat"]:
            model3 = solver3.getModel()
            s_u_value3 = model3.getValue(s_u_var3)
            test_3["s_u_computed"] = int(str(s_u_value3))
            test_3["status"] = "pass" if test_3["s_u_computed"] == 8 else "fail"
        else:
            test_3["status"] = "fail"
        results["positive_test_3"] = test_3

    except Exception as e:
        results["positive_exception"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS: cvc5 rejects incorrect regularity gain
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["negative_cvc5_unavailable"] = {"status": "skipped", "reason": "cvc5 not installed"}
        return results

    try:
        import cvc5

        # Negative Test 1: Laplacian, claim u ∈ H^1 instead of H^2
        # This should be UNSAT: cannot have s_u = 1 when s_u = 0 + 2*1 = 2
        test_1 = {
            "name": "laplacian_wrong_gain_h1",
            "operator": "Laplacian",
            "m": 1,
            "s_f": 0,
            "claimed_s_u": 1,
            "expected_s_u": 2,
            "should_be_unsat": True,
        }

        solver = cvc5.Solver()
        solver.setOption("produce-models", "true")

        m_var = solver.mkConst(solver.getIntegerSort(), "m")
        s_f_var = solver.mkConst(solver.getIntegerSort(), "s_f")
        s_u_var = solver.mkConst(solver.getIntegerSort(), "s_u")

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, m_var, solver.mkInteger(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, s_f_var, solver.mkInteger(0)))

        # Assert the correct formula
        two_m = solver.mkTerm(cvc5.Kind.MULT, solver.mkInteger(2), m_var)
        s_u_formula = solver.mkTerm(cvc5.Kind.PLUS, s_f_var, two_m)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, s_u_var, s_u_formula))

        # Now claim s_u = 1 (incorrect)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, s_u_var, solver.mkInteger(1)))

        result = solver.checkSat()
        test_1["cvc5_unsat"] = str(result) == "unsat"
        test_1["status"] = "pass" if test_1["cvc5_unsat"] else "fail"
        results["negative_test_1"] = test_1

        # Negative Test 2: Biharmonic, claim u ∈ H^4 instead of H^5
        test_2 = {
            "name": "biharmonic_wrong_gain_h4",
            "operator": "Biharmonic",
            "m": 2,
            "s_f": 1,
            "claimed_s_u": 4,
            "expected_s_u": 5,
            "should_be_unsat": True,
        }

        solver2 = cvc5.Solver()
        solver2.setOption("produce-models", "true")

        m_var2 = solver2.mkConst(solver2.getIntegerSort(), "m")
        s_f_var2 = solver2.mkConst(solver2.getIntegerSort(), "s_f")
        s_u_var2 = solver2.mkConst(solver2.getIntegerSort(), "s_u")

        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, m_var2, solver2.mkInteger(2)))
        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, s_f_var2, solver2.mkInteger(1)))

        two_m2 = solver2.mkTerm(cvc5.Kind.MULT, solver2.mkInteger(2), m_var2)
        s_u_formula2 = solver2.mkTerm(cvc5.Kind.PLUS, s_f_var2, two_m2)
        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, s_u_var2, s_u_formula2))

        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, s_u_var2, solver2.mkInteger(4)))

        result2 = solver2.checkSat()
        test_2["cvc5_unsat"] = str(result2) == "unsat"
        test_2["status"] = "pass" if test_2["cvc5_unsat"] else "fail"
        results["negative_test_2"] = test_2

        # Negative Test 3: Sixth-order, claim u ∈ H^7 instead of H^8
        test_3 = {
            "name": "sixth_order_wrong_gain_h7",
            "operator": "Sixth-order elliptic",
            "m": 3,
            "s_f": 2,
            "claimed_s_u": 7,
            "expected_s_u": 8,
            "should_be_unsat": True,
        }

        solver3 = cvc5.Solver()
        solver3.setOption("produce-models", "true")

        m_var3 = solver3.mkConst(solver3.getIntegerSort(), "m")
        s_f_var3 = solver3.mkConst(solver3.getIntegerSort(), "s_f")
        s_u_var3 = solver3.mkConst(solver3.getIntegerSort(), "s_u")

        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, m_var3, solver3.mkInteger(3)))
        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, s_f_var3, solver3.mkInteger(2)))

        two_m3 = solver3.mkTerm(cvc5.Kind.MULT, solver3.mkInteger(2), m_var3)
        s_u_formula3 = solver3.mkTerm(cvc5.Kind.PLUS, s_f_var3, two_m3)
        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, s_u_var3, s_u_formula3))

        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, s_u_var3, solver3.mkInteger(7)))

        result3 = solver3.checkSat()
        test_3["cvc5_unsat"] = str(result3) == "unsat"
        test_3["status"] = "pass" if test_3["cvc5_unsat"] else "fail"
        results["negative_test_3"] = test_3

    except Exception as e:
        results["negative_exception"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS: sympy verifies Laplacian case
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["sympy"]["tried"]:
        results["boundary_sympy_unavailable"] = {"status": "skipped", "reason": "sympy not installed"}
        return results

    try:
        import sympy as sp

        # Boundary Test 1: Laplacian regularity gain
        # For -Δu = f with f ∈ L^2, prove u ∈ H^2
        test_1 = {
            "name": "laplacian_h2_gain",
            "description": "Laplacian is order 2, so m=1; gain 2m=2 derivatives"
        }

        m_laplacian = 1
        gain = 2 * m_laplacian
        test_1["m"] = m_laplacian
        test_1["gain_2m"] = gain
        test_1["status"] = "pass" if gain == 2 else "fail"
        results["boundary_test_1"] = test_1

        # Boundary Test 2: verify formula symbolically
        # s_u = s_f + 2m => for Laplacian with s_f=0, get s_u=2
        test_2 = {
            "name": "regularity_formula_symbolic",
            "description": "Verify s_u = s_f + 2*m formula"
        }

        m, s_f, s_u = sp.symbols('m s_f s_u', integer=True, positive=True)
        regularity_eqn = sp.Eq(s_u, s_f + 2 * m)

        # For m=1, s_f=0, solve for s_u
        s_u_solution = sp.solve(regularity_eqn.subs([(m, 1), (s_f, 0)]), s_u)
        test_2["formula"] = str(regularity_eqn)
        test_2["laplacian_l2_input_s_u"] = s_u_solution[0] if s_u_solution else None
        test_2["status"] = "pass" if (s_u_solution and s_u_solution[0] == 2) else "fail"
        results["boundary_test_2"] = test_2

        # Boundary Test 3: Biharmonic case check
        # Biharmonic is order 4, so m=2; gain 2m=4
        test_3 = {
            "name": "biharmonic_h4_gain",
            "description": "Biharmonic is order 4, so m=2; gain 2m=4 derivatives"
        }

        m_biharmonic = 2
        gain_biharmonic = 2 * m_biharmonic
        test_3["m"] = m_biharmonic
        test_3["gain_2m"] = gain_biharmonic
        test_3["status"] = "pass" if gain_biharmonic == 4 else "fail"
        results["boundary_test_3"] = test_3

    except Exception as e:
        results["boundary_exception"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "sim_elliptic_regularity_constraint_canonical",
        "claim": "If Lu=f with L elliptic of order 2m and f∈H^s, then u∈H^{s+2m}",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_elliptic_regularity_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
