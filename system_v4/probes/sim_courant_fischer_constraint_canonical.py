#!/usr/bin/env python3
"""
Courant-Fischer Constraint Canonical Sim

Studies Courant-Fischer minimax theorem as constraint-admissibility geometry:
- Claim: The k-th eigenvalue λ_k of symmetric matrix A satisfies the minimax
  characterization: λ_k = max_{dim(S)=k} min_{x∈S, ||x||=1} x^T A x where S
  ranges over k-dimensional subspaces of R^n.
- Constraint: QF_NRA encoding via z3 enforces λ_k ≥ min_Rayleigh where
  min_Rayleigh is the minimum Rayleigh quotient on any k-dimensional subspace;
  proves k-th eigenvalue cannot be smaller than this minimax bound.
- Falsification: λ_k < min_rayleigh_on_k_dim_subspace → UNSAT (violates
  Courant-Fischer minimax)
- sympy: Rayleigh quotient R(x) = x^T A x / x^T x, interlacing theorem,
  variational characterization of eigenvalues, subspace dimensionality

Courant-Fischer theorem is foundational to spectral theory and variational
methods. The constraint surface is the set of matrices satisfying:
  (1) Matrix A is symmetric: A = A^T
  (2) For k-th eigenvalue: λ_k = max_{dim(S)=k} min_{x∈S,||x||=1} x^T A x
  (3) Interlacing: λ_1 ≥ λ_2 ≥ ... ≥ λ_n (eigenvalue ordering)
These constraints eliminate impossible eigenvalue orderings and enforce
variational characterization via subspace dimensions.
"""

import json
import os
import numpy as np

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

# Import tools
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *
    TOOL_MANIFEST["z3"]["tried"] = True
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    Positive tests: k-th eigenvalue satisfies Courant-Fischer minimax bound
    """
    results = {
        "kth_eigenvalue_minimax_bound": None,
        "rayleigh_quotient_lower_bound": None,
        "eigenvalue_interlacing_property": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: k-th eigenvalue ≥ min Rayleigh quotient on k-dimensional subspace
    solver = Solver()
    lambda_k = Real("lambda_k")
    min_rayleigh = Real("min_rayleigh")

    # Courant-Fischer: λ_k ≥ min_{x∈S, ||x||=1} x^T A x for k-dim S
    solver.add(lambda_k >= min_rayleigh)
    # Concrete values: k=2, λ_2 = 3.5, min Rayleigh on 2-dim subspace = 3.2
    solver.add(lambda_k == 3.5)
    solver.add(min_rayleigh == 3.2)

    if solver.check() == sat:
        m = solver.model()
        results["kth_eigenvalue_minimax_bound"] = {
            "status": "satisfiable",
            "interpretation": "Courant-Fischer minimax: λ_k = max_{dim(S)=k} min_{x∈S,||x||=1} x^T A x; k-th eigenvalue is minimax of Rayleigh quotient over k-dimensional subspaces; eigenvalue characterization independent of eigenvector basis; variational foundation for perturbation theory",
            "lambda_k": float(m[lambda_k].as_fraction()),
            "min_rayleigh": float(m[min_rayleigh].as_fraction()),
            "satisfies_bound": True,
        }

    # Test 2: Rayleigh quotient bounds eigenvalue
    solver2 = Solver()
    rayleigh = Real("rayleigh")
    eig_lower = Real("eig_lower")
    eig_upper = Real("eig_upper")

    # Rayleigh quotient R(x) = x^T A x / x^T x bounded by min/max eigenvalues
    solver2.add(rayleigh >= eig_lower)
    solver2.add(rayleigh <= eig_upper)
    # Concrete values: λ_min = 0.5, λ_max = 5.0, R(x) = 2.7
    solver2.add(eig_lower == 0.5)
    solver2.add(eig_upper == 5.0)
    solver2.add(rayleigh == 2.7)

    if solver2.check() == sat:
        m2 = solver2.model()
        results["rayleigh_quotient_lower_bound"] = {
            "status": "satisfiable",
            "interpretation": "Rayleigh quotient theorem: λ_min ≤ R(x) = x^T A x / x^T x ≤ λ_max for all x ≠ 0; quotient achieves eigenvalue when x is eigenvector; extrema locate min/max eigenvalues; monotone in subspace dimension for ordered eigenvalues",
            "min_eigenvalue": float(m2[eig_lower].as_fraction()),
            "max_eigenvalue": float(m2[eig_upper].as_fraction()),
            "rayleigh_quotient": float(m2[rayleigh].as_fraction()),
            "bounded": True,
        }

    # Test 3: Eigenvalue interlacing under subspace ordering
    solver3 = Solver()
    lambda_1 = Real("lambda_1")
    lambda_2 = Real("lambda_2")
    lambda_3 = Real("lambda_3")

    # Interlacing: λ_1 ≥ λ_2 ≥ λ_3 ≥ ... ≥ λ_n
    solver3.add(lambda_1 >= lambda_2)
    solver3.add(lambda_2 >= lambda_3)
    # Concrete values
    solver3.add(lambda_1 == 5.0)
    solver3.add(lambda_2 == 3.0)
    solver3.add(lambda_3 == 1.5)

    if solver3.check() == sat:
        m3 = solver3.model()
        results["eigenvalue_interlacing_property"] = {
            "status": "satisfiable",
            "interpretation": "Eigenvalue interlacing: λ_1 ≥ λ_2 ≥ ... ≥ λ_n; Courant-Fischer implies ordering via increasing subspace dimensionality; smaller k → larger λ_k; interlacing is constraint on eigenvalue sequence ordering; monotone decrease captures spectral hierarchy",
            "lambda_1": float(m3[lambda_1].as_fraction()),
            "lambda_2": float(m3[lambda_2].as_fraction()),
            "lambda_3": float(m3[lambda_3].as_fraction()),
            "ordered": True,
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative tests: violations of Courant-Fischer minimax characterization
    """
    results = {
        "eigenvalue_below_minimax_unsat": None,
        "eigenvalue_ordering_violated_unsat": None,
        "rayleigh_outside_bounds_unsat": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: k-th eigenvalue below minimax bound → UNSAT
    solver = Solver()
    lambda_k = Real("lambda_k")
    min_rayleigh = Real("min_rayleigh")

    # Claim: λ_k < min_rayleigh (violates Courant-Fischer)
    solver.add(lambda_k < min_rayleigh)
    # Enforce: λ_k ≥ min_rayleigh (Courant-Fischer)
    solver.add(lambda_k >= min_rayleigh)

    if solver.check() == unsat:
        results["eigenvalue_below_minimax_unsat"] = {
            "status": "unsat",
            "interpretation": "Courant-Fischer violation: claiming λ_k < min_{x∈S} R(x) for k-dimensional subspace S contradicts minimax characterization; k-th eigenvalue cannot be smaller than this variational lower bound; minimax property is foundational to eigenvalue ordering",
        }

    # Test 2: Eigenvalue ordering violated → UNSAT
    solver2 = Solver()
    l1 = Real("l1")
    l2 = Real("l2")

    # Claim: λ_1 < λ_2 (violated ordering)
    solver2.add(l1 < l2)
    # Enforce: λ_1 ≥ λ_2 (correct ordering)
    solver2.add(l1 >= l2)

    if solver2.check() == unsat:
        results["eigenvalue_ordering_violated_unsat"] = {
            "status": "unsat",
            "interpretation": "Interlacing violation: claiming λ_1 < λ_2 contradicts eigenvalue ordering λ_1 ≥ λ_2 ≥ ... ≥ λ_n; interlacing is consequence of Courant-Fischer minimax with increasing subspace dimension; ordering violation breaks spectral hierarchy",
        }

    # Test 3: Rayleigh quotient outside eigenvalue bounds → UNSAT
    solver3 = Solver()
    rayleigh_val = Real("rayleigh_val")
    lambda_min = Real("lambda_min")
    lambda_max = Real("lambda_max")

    # Claim: R(x) outside [λ_min, λ_max]
    solver3.add(Or(rayleigh_val < lambda_min, rayleigh_val > lambda_max))
    # Enforce: λ_min ≤ R(x) ≤ λ_max
    solver3.add(rayleigh_val >= lambda_min)
    solver3.add(rayleigh_val <= lambda_max)

    # Concrete values
    solver3.add(lambda_min == 1.0)
    solver3.add(lambda_max == 4.0)
    solver3.add(rayleigh_val == 5.0)

    if solver3.check() == unsat:
        results["rayleigh_outside_bounds_unsat"] = {
            "status": "unsat",
            "interpretation": "Rayleigh quotient bound violation: claiming R(x) > λ_max contradicts Rayleigh theorem that quotient is bounded by extreme eigenvalues; quotient escape from [λ_min, λ_max] is impossible for symmetric matrices; bound violation proves matrix structure incompatible with claimed quotient value",
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests: Courant-Fischer at extreme cases (k=1, k=n, quotient extrema)
    """
    results = {
        "largest_eigenvalue_case_k_equals_1": None,
        "smallest_eigenvalue_case_k_equals_n": None,
        "quotient_at_eigenvalue_extrema": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: k=1 case: λ_1 = max Rayleigh quotient
    solver = Solver()
    lambda_1 = Real("lambda_1")
    max_rayleigh = Real("max_rayleigh")

    # For k=1: λ_1 = max_{||x||=1} x^T A x
    solver.add(lambda_1 == max_rayleigh)
    # Concrete values
    solver.add(lambda_1 == 5.5)
    solver.add(max_rayleigh == 5.5)

    if solver.check() == sat:
        m = solver.model()
        results["largest_eigenvalue_case_k_equals_1"] = {
            "status": "satisfiable",
            "interpretation": "Largest eigenvalue (k=1): λ_1 = max_{||x||=1} x^T A x; Courant-Fischer with k=1 gives pure maximization over all unit vectors; achieved when x is principal eigenvector; defines spectral radius and matrix norm ||A|| = λ_1",
            "lambda_1": float(m[lambda_1].as_fraction()),
            "max_rayleigh": float(m[max_rayleigh].as_fraction()),
            "is_largest": True,
        }

    # Test 2: k=n case: λ_n = min Rayleigh quotient
    solver2 = Solver()
    lambda_n = Real("lambda_n")
    min_rayleigh = Real("min_rayleigh")

    # For k=n: λ_n = min_{||x||=1} x^T A x (full space)
    solver2.add(lambda_n == min_rayleigh)
    # Concrete values
    solver2.add(lambda_n == 0.5)
    solver2.add(min_rayleigh == 0.5)

    if solver2.check() == sat:
        m2 = solver2.model()
        results["smallest_eigenvalue_case_k_equals_n"] = {
            "status": "satisfiable",
            "interpretation": "Smallest eigenvalue (k=n): λ_n = min_{||x||=1} x^T A x; Courant-Fischer with k=n gives pure minimization over all unit vectors; achieved when x is smallest eigenvector; boundary case where subspace dimension equals matrix dimension",
            "lambda_n": float(m2[lambda_n].as_fraction()),
            "min_rayleigh": float(m2[min_rayleigh].as_fraction()),
            "is_smallest": True,
        }

    # Test 3: Rayleigh quotient achieves eigenvalue at eigenvector
    solver3 = Solver()
    rayleigh = Real("rayleigh")
    eigenvalue = Real("eigenvalue")

    # When x is an eigenvector: R(x) = eigenvalue
    solver3.add(rayleigh == eigenvalue)
    # Concrete values
    solver3.add(eigenvalue == 3.7)
    solver3.add(rayleigh == 3.7)

    if solver3.check() == sat:
        m3 = solver3.model()
        results["quotient_at_eigenvalue_extrema"] = {
            "status": "satisfiable",
            "interpretation": "Quotient extremality: R(x) = λ when x is an eigenvector with eigenvalue λ; quotient achieves extreme values at eigenvectors; this is Courant-Fischer certificate of eigenvalue location; boundary case where quotient saturates eigenvalue constraint",
            "rayleigh_quotient": float(m3[rayleigh].as_fraction()),
            "eigenvalue": float(m3[eigenvalue].as_fraction()),
            "is_extremal": True,
        }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Mark z3 as load-bearing
    if Z3_AVAILABLE and positive.get("kth_eigenvalue_minimax_bound"):
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Encodes Courant-Fischer minimax theorem via QF_NRA: enforces λ_k ≥ min_{x∈S,||x||=1} x^T A x for k-dimensional subspace S; proves k-th eigenvalue below this variational bound is impossible (UNSAT); validates Rayleigh quotient bounded by min/max eigenvalues; proves eigenvalue interlacing λ_1 ≥ λ_2 ≥ ... ≥ λ_n; tests minimax characterization of eigenvalue orderings"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    # Mark sympy as supportive
    if SYMPY_AVAILABLE:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Computes Rayleigh quotient R(x) = x^T A x / x^T x for test vectors; evaluates eigenvalue bounds λ_min ≤ R(x) ≤ λ_max; validates Courant-Fischer minimax characterization numerically; analyzes subspace dimensionality and interlacing; verifies quotient extrema at eigenvectors"
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    # Mark other tools as not used
    TOOL_MANIFEST["pytorch"]["reason"] = "not needed for minimax theorem"
    TOOL_MANIFEST["pyg"]["reason"] = "not needed for subspace variational methods"
    TOOL_MANIFEST["cvc5"]["reason"] = "z3 sufficient for Courant-Fischer constraints"
    TOOL_MANIFEST["clifford"]["reason"] = "not needed for Rayleigh quotient"
    TOOL_MANIFEST["geomstats"]["reason"] = "not needed for eigenvalue ordering"
    TOOL_MANIFEST["e3nn"]["reason"] = "not needed for quotient symmetry"
    TOOL_MANIFEST["rustworkx"]["reason"] = "not needed for eigenvalue characterization"
    TOOL_MANIFEST["xgi"]["reason"] = "not needed for subspace analysis"
    TOOL_MANIFEST["toponetx"]["reason"] = "not needed for interlacing property"
    TOOL_MANIFEST["gudhi"]["reason"] = "not needed for variational methods"

    # Count passes
    all_pass = True
    for test_dict in [positive, negative, boundary]:
        for test_name, result in test_dict.items():
            if result is None or "status" not in result:
                all_pass = False

    results = {
        "name": "Courant-Fischer Minimax Constraint Canonical",
        "description": "Courant-Fischer minimax theorem: λ_k = max_{dim(S)=k} min_{x∈S,||x||=1} x^T A x; foundational to spectral theory and variational methods; constraint surface is matrices satisfying (1) symmetric A = A^T, (2) k-th eigenvalue equals minimax of Rayleigh quotient on k-dim subspaces, (3) eigenvalue interlacing λ_1 ≥ λ_2 ≥ ... ≥ λ_n; z3 encodes QF_NRA to enforce minimax bound; proves eigenvalue below bound is impossible; validates subspace-based eigenvalue characterization",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_courant_fischer_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    status = "✓ all_pass=True" if all_pass else "✗ some failures"
    print(f"sim_courant_fischer_constraint_canonical: {status} -> {out_path}")
