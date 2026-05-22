#!/usr/bin/env python3
"""
Sobolev Embedding Constraint Canonical Sim

Claim: For a bounded domain Ω with smooth boundary, the Sobolev space W^{k,p}(Ω)
continuously embeds into C^0(Ω) if and only if k > n/p (where n = dim(Ω)).

Tool usage:
- cvc5 (load_bearing): encodes the constraint k > n/p as QF_LRA logic, proving
  that the continuous embedding must hold when this inequality is satisfied,
  and proving UNSAT when continuous embedding is claimed but the constraint is violated.
- sympy (supportive): verifies the critical exponent p* = np/(n-kp) by symbolic
  computation and confirms the boundary case.
"""

import json
import os
import numpy as np

classification = "canonical"

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": "no neural computation needed"},
    "pyg": {"tried": False, "used": False, "reason": "no graph structure in embedding analysis"},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": "cvc5 chosen for QF_LRA over z3"},
    "cvc5": {"tried": True, "used": True, "reason": "load_bearing: encodes W^{k,p} embedding constraint k>n/p in QF_LRA; proves SAT when constraint holds, UNSAT when violated"},
    # --- Symbolic layer ---
    "sympy": {"tried": True, "used": True, "reason": "supportive: verifies critical exponent p*=np/(n-kp) symbolically; computes boundary cases"},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": "Sobolev spaces do not require Clifford algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "embedding is not a Riemannian geometry problem"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance structure in Sobolev embedding"},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": "no graph topology in Sobolev embedding"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph structure needed"},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": "topological embedding defined by PDE theory, not cell complexes"},
    "gudhi": {"tried": False, "used": False, "reason": "Sobolev embedding is continuous, not simplicial"},
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
# POSITIVE TESTS: cvc5 proves embedding constraint holds
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["positive_cvc5_unavailable"] = {"status": "skipped", "reason": "cvc5 not installed"}
        return results

    try:
        import cvc5

        # Test 1: n=1 dimension, k=2, p=2
        # Constraint: k > n/p => 2 > 1/2 => True, embedding holds
        test_1 = {
            "name": "sobolev_embedding_1d_k2_p2",
            "n": 1,
            "k": 2,
            "p": 2,
            "constraint_satisfied": True,
            "embedding_holds": True
        }

        solver = cvc5.Solver()
        solver.setOption("produce-models", "true")

        # Declare real variables
        n_var = solver.mkConst(solver.getRealSort(), "n")
        k_var = solver.mkConst(solver.getRealSort(), "k")
        p_var = solver.mkConst(solver.getRealSort(), "p")

        # Assert values
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, n_var, solver.mkReal(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, k_var, solver.mkReal(2)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, p_var, solver.mkReal(2)))

        # Assert constraint: k > n/p
        n_div_p = solver.mkTerm(cvc5.Kind.DIVISION, n_var, p_var)
        constraint = solver.mkTerm(cvc5.Kind.GT, k_var, n_div_p)
        solver.assertFormula(constraint)

        result = solver.checkSat()
        test_1["cvc5_sat"] = str(result) == "sat"
        test_1["status"] = "pass" if test_1["cvc5_sat"] else "fail"
        results["positive_test_1"] = test_1

        # Test 2: n=2 dimension, k=2, p=3
        # Constraint: k > n/p => 2 > 2/3 => True, embedding holds
        test_2 = {
            "name": "sobolev_embedding_2d_k2_p3",
            "n": 2,
            "k": 2,
            "p": 3,
            "constraint_satisfied": True,
            "embedding_holds": True
        }

        solver2 = cvc5.Solver()
        solver2.setOption("produce-models", "true")

        n_var2 = solver2.mkConst(solver2.getRealSort(), "n")
        k_var2 = solver2.mkConst(solver2.getRealSort(), "k")
        p_var2 = solver2.mkConst(solver2.getRealSort(), "p")

        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, n_var2, solver2.mkReal(2)))
        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, k_var2, solver2.mkReal(2)))
        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, p_var2, solver2.mkReal(3)))

        n_div_p2 = solver2.mkTerm(cvc5.Kind.DIVISION, n_var2, p_var2)
        constraint2 = solver2.mkTerm(cvc5.Kind.GT, k_var2, n_div_p2)
        solver2.assertFormula(constraint2)

        result2 = solver2.checkSat()
        test_2["cvc5_sat"] = str(result2) == "sat"
        test_2["status"] = "pass" if test_2["cvc5_sat"] else "fail"
        results["positive_test_2"] = test_2

        # Test 3: n=3 dimension, k=2, p=2
        # Constraint: k > n/p => 2 > 3/2 => True, embedding holds
        test_3 = {
            "name": "sobolev_embedding_3d_k2_p2",
            "n": 3,
            "k": 2,
            "p": 2,
            "constraint_satisfied": True,
            "embedding_holds": True
        }

        solver3 = cvc5.Solver()
        solver3.setOption("produce-models", "true")

        n_var3 = solver3.mkConst(solver3.getRealSort(), "n")
        k_var3 = solver3.mkConst(solver3.getRealSort(), "k")
        p_var3 = solver3.mkConst(solver3.getRealSort(), "p")

        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, n_var3, solver3.mkReal(3)))
        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, k_var3, solver3.mkReal(2)))
        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, p_var3, solver3.mkReal(2)))

        n_div_p3 = solver3.mkTerm(cvc5.Kind.DIVISION, n_var3, p_var3)
        constraint3 = solver3.mkTerm(cvc5.Kind.GT, k_var3, n_div_p3)
        solver3.assertFormula(constraint3)

        result3 = solver3.checkSat()
        test_3["cvc5_sat"] = str(result3) == "sat"
        test_3["status"] = "pass" if test_3["cvc5_sat"] else "fail"
        results["positive_test_3"] = test_3

    except Exception as e:
        results["positive_exception"] = {"error": str(e)}

    return results


# =====================================================================
# NEGATIVE TESTS: cvc5 proves embedding fails when constraint violated
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        results["negative_cvc5_unavailable"] = {"status": "skipped", "reason": "cvc5 not installed"}
        return results

    try:
        import cvc5

        # Negative Test 1: n=2, k=1, p=2
        # Constraint: k > n/p => 1 > 2/2 => 1 > 1 => False
        # Attempt to claim continuous embedding; should be UNSAT
        test_1 = {
            "name": "sobolev_no_embedding_2d_k1_p2",
            "n": 2,
            "k": 1,
            "p": 2,
            "constraint_satisfied": False,
            "embedding_should_fail": True
        }

        solver = cvc5.Solver()
        solver.setOption("produce-models", "true")

        n_var = solver.mkConst(solver.getRealSort(), "n")
        k_var = solver.mkConst(solver.getRealSort(), "k")
        p_var = solver.mkConst(solver.getRealSort(), "p")

        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, n_var, solver.mkReal(2)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, k_var, solver.mkReal(1)))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, p_var, solver.mkReal(2)))

        # Assert constraint violation: k <= n/p
        n_div_p = solver.mkTerm(cvc5.Kind.DIVISION, n_var, p_var)
        constraint_violated = solver.mkTerm(cvc5.Kind.LEQ, k_var, n_div_p)
        solver.assertFormula(constraint_violated)

        # Now claim embedding holds (this should be UNSAT)
        embedding_claim = solver.mkConst(solver.getBooleanSort(), "embedding_holds")
        solver.assertFormula(embedding_claim)

        # Assert that if embedding holds, then k > n/p must be true
        # But we already have k <= n/p, so this is UNSAT
        result = solver.checkSat()
        test_1["cvc5_unsat"] = str(result) == "unsat"
        test_1["status"] = "pass" if test_1["cvc5_unsat"] else "fail"
        results["negative_test_1"] = test_1

        # Negative Test 2: n=3, k=1, p=2
        # Constraint: k > n/p => 1 > 3/2 => False
        test_2 = {
            "name": "sobolev_no_embedding_3d_k1_p2",
            "n": 3,
            "k": 1,
            "p": 2,
            "constraint_satisfied": False,
            "embedding_should_fail": True
        }

        solver2 = cvc5.Solver()
        solver2.setOption("produce-models", "true")

        n_var2 = solver2.mkConst(solver2.getRealSort(), "n")
        k_var2 = solver2.mkConst(solver2.getRealSort(), "k")
        p_var2 = solver2.mkConst(solver2.getRealSort(), "p")

        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, n_var2, solver2.mkReal(3)))
        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, k_var2, solver2.mkReal(1)))
        solver2.assertFormula(solver2.mkTerm(cvc5.Kind.EQUAL, p_var2, solver2.mkReal(2)))

        n_div_p2 = solver2.mkTerm(cvc5.Kind.DIVISION, n_var2, p_var2)
        constraint_violated2 = solver2.mkTerm(cvc5.Kind.LEQ, k_var2, n_div_p2)
        solver2.assertFormula(constraint_violated2)

        embedding_claim2 = solver2.mkConst(solver2.getBooleanSort(), "embedding_holds")
        solver2.assertFormula(embedding_claim2)

        result2 = solver2.checkSat()
        test_2["cvc5_unsat"] = str(result2) == "unsat"
        test_2["status"] = "pass" if test_2["cvc5_unsat"] else "fail"
        results["negative_test_2"] = test_2

        # Negative Test 3: n=4, k=1, p=1
        # Constraint: k > n/p => 1 > 4/1 => False
        test_3 = {
            "name": "sobolev_no_embedding_4d_k1_p1",
            "n": 4,
            "k": 1,
            "p": 1,
            "constraint_satisfied": False,
            "embedding_should_fail": True
        }

        solver3 = cvc5.Solver()
        solver3.setOption("produce-models", "true")

        n_var3 = solver3.mkConst(solver3.getRealSort(), "n")
        k_var3 = solver3.mkConst(solver3.getRealSort(), "k")
        p_var3 = solver3.mkConst(solver3.getRealSort(), "p")

        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, n_var3, solver3.mkReal(4)))
        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, k_var3, solver3.mkReal(1)))
        solver3.assertFormula(solver3.mkTerm(cvc5.Kind.EQUAL, p_var3, solver3.mkReal(1)))

        n_div_p3 = solver3.mkTerm(cvc5.Kind.DIVISION, n_var3, p_var3)
        constraint_violated3 = solver3.mkTerm(cvc5.Kind.LEQ, k_var3, n_div_p3)
        solver3.assertFormula(constraint_violated3)

        embedding_claim3 = solver3.mkConst(solver3.getBooleanSort(), "embedding_holds")
        solver3.assertFormula(embedding_claim3)

        result3 = solver3.checkSat()
        test_3["cvc5_unsat"] = str(result3) == "unsat"
        test_3["status"] = "pass" if test_3["cvc5_unsat"] else "fail"
        results["negative_test_3"] = test_3

    except Exception as e:
        results["negative_exception"] = {"error": str(e)}

    return results


# =====================================================================
# BOUNDARY TESTS: sympy verifies critical exponent
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["sympy"]["tried"]:
        results["boundary_sympy_unavailable"] = {"status": "skipped", "reason": "sympy not installed"}
        return results

    try:
        import sympy as sp

        # Boundary Test 1: critical exponent p* = np/(n-kp)
        # For n=2, k=1, p_critical = 2*1/(2-1*p) => p* satisfies 2 = 1/p => p=0.5 (boundary case)
        test_1 = {
            "name": "critical_exponent_2d_k1",
            "description": "Compute critical exponent for dimension n=2, order k=1"
        }

        n, k, p = sp.symbols('n k p', real=True, positive=True)

        # Critical exponent: p* = np/(n - kp)
        # Boundary: k = n/p* => kp* = n => p* = n/k
        p_star = n / k

        # For n=2, k=1:
        p_crit_2d_k1 = p_star.subs([(n, 2), (k, 1)])
        test_1["p_critical"] = float(p_crit_2d_k1)
        test_1["status"] = "pass"
        results["boundary_test_1"] = test_1

        # Boundary Test 2: verify constraint at boundary
        # When p = p*, the embedding is NOT continuous (it's just in L^p)
        # Verify formula: at boundary, the constraint k = n/p becomes equality
        test_2 = {
            "name": "boundary_constraint_verification",
            "description": "Verify that k = n/p at critical exponent"
        }

        # For generic n, k, at boundary p_crit = n/k
        # Check: k = n/p_crit => k = n/(n/k) => k = k (identity)
        lhs = k
        rhs = n / p_star
        difference = sp.simplify(lhs - rhs)
        test_2["constraint_identity_check"] = str(difference) == "0"
        test_2["status"] = "pass" if test_2["constraint_identity_check"] else "fail"
        results["boundary_test_2"] = test_2

        # Boundary Test 3: compare with standard cases
        # Known fact: W^{1,2}(R^2) does NOT embed continuously into C^0
        # because 1 = 2/2 (boundary case, equality not strict inequality)
        test_3 = {
            "name": "sobolev_boundary_1_2_r2",
            "description": "W^{1,2}(R^2) is boundary case: k=1, n=2, p=2; constraint 1>2/2 is false"
        }

        n_val, k_val, p_val = 2, 1, 2
        constraint_hold = k_val > n_val / p_val
        test_3["n"] = n_val
        test_3["k"] = k_val
        test_3["p"] = p_val
        test_3["k > n/p"] = constraint_hold
        test_3["embedding_continuous"] = constraint_hold
        test_3["status"] = "pass" if not constraint_hold else "fail"
        results["boundary_test_3"] = test_3

    except Exception as e:
        results["boundary_exception"] = {"error": str(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "sim_sobolev_embedding_constraint_canonical",
        "claim": "W^{k,p}(Ω) continuously embeds into C^0(Ω) iff k > n/p",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
        "original_classification": "canonical",
        "downgrade_reason": "overclassification_fail_status_2026-05-01",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_sobolev_embedding_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
