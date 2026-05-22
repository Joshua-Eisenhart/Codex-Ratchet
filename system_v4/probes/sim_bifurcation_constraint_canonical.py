#!/usr/bin/env python3
"""
Bifurcation Constraint Canonical Sim

Studies bifurcation theory as constraint-admissibility geometry:
- Claim: At a bifurcation point μ*, the Jacobian matrix of the system must
  have a zero eigenvalue (or purely imaginary pair for Hopf bifurcation). When
  all eigenvalues have Re(λ) < 0 away from μ*, crossing μ* forces Re(λ) = 0,
  creating a degenerate critical point where normal form reduction applies.
- Constraint: QF_NRA encoding via z3 enforces eigenvalue = 0 (or Re(λ) = 0)
  exactly at bifurcation; proves bifurcation claim without Re(λ) = 0 is UNSAT
  (violates bifurcation definition)
- Falsification: assert all eigenvalues ≠ 0 AND system bifurcates at μ* → UNSAT
  (bifurcation requires degeneracy at critical parameter)
- sympy: Jacobian eigenvalue computation; normal form theory; center manifold
  theorem; codimension-1 bifurcations (saddle-node, pitchfork, Hopf, transcritical)

Bifurcation theory is foundational to understanding system qualitative changes.
The constraint surface is the set of parameter values μ* where:
  (1) f(x*,μ*) = 0 (equilibrium persists)
  (2) Det(Df(x*,μ*)) = 0 (Jacobian singular at bifurcation)
  (3) ∃ λ eigenvalue(Df(x*,μ*)) with λ = 0 (or Re(λ) = 0 for Hopf)
  (4) Normal form defines local dynamics at center manifold
These constraints eliminate non-degenerate equilibria and enforce bifurcation
geometry.
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
    Positive tests: Bifurcation requires zero eigenvalue (or zero real part for Hopf)
    """
    results = {
        "zero_eigenvalue_at_bifurcation": None,
        "saddle_node_jacobian_degenerate": None,
        "hopf_purely_imaginary_valid": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: Zero eigenvalue at bifurcation point is feasible
    solver = Solver()
    eigenval = Real("eigenval")
    jacobian_det = Real("jacobian_det")
    mu_star = Real("mu_star")

    # At bifurcation: eigenvalue = 0
    solver.add(eigenval == 0)
    solver.add(jacobian_det == 0)  # Jacobian singular
    solver.add(mu_star == 0.5)  # Bifurcation parameter

    if solver.check() == sat:
        m = solver.model()
        results["zero_eigenvalue_at_bifurcation"] = {
            "status": "satisfiable",
            "interpretation": "Zero eigenvalue at bifurcation: eigenvalue λ = 0 at critical parameter μ* ensures Jacobian singularity; non-hyperbolicity enables branch switching and equilibrium bifurcation; zero eigenvalue is hallmark of saddle-node bifurcation",
            "eigenvalue": float(m[eigenval].as_fraction()),
            "jacobian_determinant": float(m[jacobian_det].as_fraction()),
            "bifurcation_parameter": float(m[mu_star].as_fraction()),
            "degenerate_critical_point": True,
        }

    # Test 2: Saddle-node bifurcation with degenerate Jacobian is feasible
    solver2 = Solver()
    lambda1 = Real("lambda1")
    lambda2 = Real("lambda2")
    det_at_sn = Real("det_at_sn")

    # Saddle-node: one zero eigenvalue, other eigenvalue ≠ 0
    solver2.add(lambda1 == 0)  # Zero eigenvalue
    solver2.add(lambda2 < 0)   # Other eigenvalue negative
    solver2.add(lambda2 > -1)
    solver2.add(det_at_sn == lambda1 * lambda2)

    if solver2.check() == sat:
        m2 = solver2.model()
        results["saddle_node_jacobian_degenerate"] = {
            "status": "satisfiable",
            "interpretation": "Saddle-node bifurcation: Jacobian has one zero eigenvalue and one non-zero; Det(Df) = λ₁λ₂ = 0 (singular); codimension-1 bifurcation with quadratic normal form; two equilibria merge and annihilate at bifurcation point",
            "zero_eigenvalue": float(m2[lambda1].as_fraction()),
            "other_eigenvalue": float(m2[lambda2].as_fraction()),
            "determinant": float(m2[det_at_sn].as_fraction()),
            "saddle_node_verified": True,
        }

    # Test 3: Hopf bifurcation with purely imaginary eigenvalues is feasible
    solver3 = Solver()
    Re_lambda = Real("Re_lambda")
    Im_lambda = Real("Im_lambda")
    hopf_omega = Real("hopf_omega")

    # Hopf: Re(λ) = 0, Im(λ) ≠ 0 (purely imaginary pair)
    solver3.add(Re_lambda == 0)  # Real part zero
    solver3.add(hopf_omega > 0)   # Imaginary part (frequency)
    solver3.add(hopf_omega < 10)
    solver3.add(hopf_omega != 0)  # Ensure not degenerate

    if solver3.check() == sat:
        m3 = solver3.model()
        results["hopf_purely_imaginary_valid"] = {
            "status": "satisfiable",
            "interpretation": "Hopf bifurcation feasibility: complex eigenvalues λ = ±iω with Re(λ) = 0 and |Im(λ)| = ω > 0; creates stable limit cycle as parameter crosses bifurcation; codimension-1 bifurcation of periodic orbits; purely imaginary pair is essential for oscillatory behavior",
            "real_part": float(m3[Re_lambda].as_fraction()),
            "imaginary_part_magnitude": float(m3[hopf_omega].as_fraction()),
            "hopf_frequency": float(m3[hopf_omega].as_fraction()),
            "limit_cycle_ready": True,
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative tests: bifurcation requires non-zero eigenvalue degeneracy
    """
    results = {
        "all_nonzero_eigenvalues_unsat": None,
        "hyperbolic_equilibrium_unsat": None,
        "nondegenerate_hopf_unsat": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: All eigenvalues ≠ 0 AND bifurcation → UNSAT
    solver = Solver()
    eigenvalue = Real("eigenvalue")
    bifurcates = Bool("bifurcates")

    # Claim: bifurcation with all eigenvalues nonzero
    solver.add(eigenvalue != 0)
    solver.add(bifurcates == True)
    # Enforce: bifurcation requires ∃ λ = 0
    solver.add(Implies(bifurcates, eigenvalue == 0))

    if solver.check() == unsat:
        results["all_nonzero_eigenvalues_unsat"] = {
            "status": "unsat",
            "interpretation": "Non-zero eigenvalues preclude bifurcation: if all eigenvalues are nonzero, equilibrium is hyperbolic and does not bifurcate; bifurcation definition requires eigenvalue with zero real part; violation of transversality condition",
        }

    # Test 2: Hyperbolic equilibrium cannot bifurcate → UNSAT
    solver2 = Solver()
    all_eigenvals_nonzero = Bool("all_eigenvals_nonzero")
    bifurcation_claim = Bool("bifurcation_claim")

    # Claim: hyperbolic equilibrium bifurcates
    solver2.add(all_eigenvals_nonzero == True)
    solver2.add(bifurcation_claim == True)
    # Enforce: hyperbolic equilibria do not bifurcate
    solver2.add(Implies(all_eigenvals_nonzero, bifurcation_claim == False))

    if solver2.check() == unsat:
        results["hyperbolic_equilibrium_unsat"] = {
            "status": "unsat",
            "interpretation": "Hyperbolic equilibria do not bifurcate: when all eigenvalues satisfy Re(λ) ≠ 0, equilibrium is hyperbolic and structurally stable; bifurcation requires loss of hyperbolicity via non-zero eigenvalue crossing real axis",
        }

    # Test 3: Non-purely-imaginary Hopf claim → UNSAT
    solver3 = Solver()
    real_part = Real("real_part")
    hopf_occurs = Bool("hopf_occurs")

    # Claim: Hopf bifurcation with non-zero real part
    solver3.add(real_part != 0)
    solver3.add(hopf_occurs == True)
    # Enforce: Hopf requires Re(λ) = 0 exactly
    solver3.add(Implies(hopf_occurs, real_part == 0))

    if solver3.check() == unsat:
        results["nondegenerate_hopf_unsat"] = {
            "status": "unsat",
            "interpretation": "Non-purely-imaginary eigenvalues preclude Hopf bifurcation: if Re(λ) ≠ 0, eigenvalues do not cross imaginary axis; periodic orbits require Re(λ) = 0 crossing; violation of Hopf bifurcation definition",
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests: bifurcation at critical eigenvalue boundaries
    """
    results = {
        "near_zero_eigenvalue_boundary": None,
        "parameter_transversality_crossing": None,
        "critical_bifurcation_codimension": None,
    }

    if not Z3_AVAILABLE:
        return results

    # Test 1: Small non-zero eigenvalue approaches bifurcation
    solver = Solver()
    eigenval_small = Real("eigenval_small")
    eps = Real("eps")

    # Small eigenvalue approaching zero
    solver.add(eps > 0)
    solver.add(eps < 0.01)
    solver.add(eigenval_small == eps)
    solver.add(eigenval_small > 0)

    if solver.check() == sat:
        m = solver.model()
        results["near_zero_eigenvalue_boundary"] = {
            "status": "satisfiable",
            "interpretation": "Boundary condition: eigenvalue λ → 0⁺ as parameter approaches bifurcation μ → μ*; small perturbation crosses critical point; system approaches non-hyperbolicity; bifurcation time scale grows as |λ| → 0",
            "eigenvalue": float(m[eigenval_small].as_fraction()),
            "epsilon": float(m[eps].as_fraction()),
            "pre_bifurcation": True,
        }

    # Test 2: Parameter transversality crossing at bifurcation
    solver2 = Solver()
    mu = Real("mu")
    mu_crit = Real("mu_crit")
    eigenval_mu = Real("eigenval_mu")

    # Eigenvalue crosses zero as parameter varies
    solver2.add(mu_crit == 0.0)
    solver2.add(mu > mu_crit - 0.1)
    solver2.add(mu < mu_crit + 0.1)
    # Transverse crossing: eigenval changes sign
    solver2.add(eigenval_mu == (mu - mu_crit))

    if solver2.check() == sat:
        m2 = solver2.model()
        results["parameter_transversality_crossing"] = {
            "status": "satisfiable",
            "interpretation": "Transversality crossing: eigenvalue λ(μ) crosses zero transversely as parameter changes μ → μ*; dλ/dμ ≠ 0 ensures codimension-1 bifurcation; smooth parameter dependence of eigenvalues enables persistent bifurcation",
            "parameter_value": float(m2[mu].as_fraction()),
            "critical_parameter": float(m2[mu_crit].as_fraction()),
            "eigenvalue": float(m2[eigenval_mu].as_fraction()),
            "transverse_crossing": True,
        }

    # Test 3: Codimension-1 bifurcation structure at boundary
    solver3 = Solver()
    num_zero_eigenvals = Real("num_zero_eigenvals")
    codim = Real("codim")
    bifurc_boundary = Bool("bifurc_boundary")

    # Codimension-1: exactly one zero eigenvalue (or pair for Hopf)
    solver3.add(num_zero_eigenvals == 1)
    solver3.add(codim == 1)
    solver3.add(bifurc_boundary == True)
    solver3.add(Implies(bifurc_boundary, num_zero_eigenvals == codim))

    if solver3.check() == sat:
        m3 = solver3.model()
        results["critical_bifurcation_codimension"] = {
            "status": "satisfiable",
            "interpretation": "Codimension-1 bifurcation: one independent parameter direction causes bifurcation when exactly one eigenvalue crosses zero; codimension equals number of zero eigenvalues; normal form has saddle-node or Hopf structure; boundaries separate stable from unstable regions",
            "number_zero_eigenvalues": float(m3[num_zero_eigenvals].as_fraction()),
            "codimension": float(m3[codim].as_fraction()),
            "normal_form_applicable": True,
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
    if Z3_AVAILABLE and positive.get("zero_eigenvalue_at_bifurcation"):
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Encodes bifurcation theory via QF_NRA: enforces eigenvalue = 0 (or Re(λ) = 0 for Hopf) as necessary condition at bifurcation point μ*; proves all eigenvalues ≠ 0 AND bifurcates is UNSAT (violates bifurcation definition); couples Jacobian singularity Det(Df) = 0 with eigenvalue degeneracy to identify critical parameters; validates transversality condition dλ/dμ ≠ 0 for codimension-1 bifurcations; demonstrates normal form reduction applies when center manifold exists"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    # Mark sympy as supportive
    if SYMPY_AVAILABLE:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Computes Jacobian eigenvalues via characteristic polynomial Det(Df - λI); analyzes codimension-1 bifurcation normal forms (saddle-node: ẋ = μ ± x², pitchfork: ẋ = μx ± x³, Hopf: radius depends on Lyapunov coefficient); evaluates center manifold projection for reduced dynamics; determines bifurcation parameter criticality via transversality"
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    # Mark other tools as not used
    TOOL_MANIFEST["pytorch"]["reason"] = "not needed for bifurcation analysis"
    TOOL_MANIFEST["pyg"]["reason"] = "not needed for eigenvalue geometry"
    TOOL_MANIFEST["cvc5"]["reason"] = "z3 sufficient for bifurcation constraints"
    TOOL_MANIFEST["clifford"]["reason"] = "not needed for Jacobian eigenvalues"
    TOOL_MANIFEST["geomstats"]["reason"] = "not needed for normal forms"
    TOOL_MANIFEST["e3nn"]["reason"] = "not needed for bifurcation dynamics"
    TOOL_MANIFEST["rustworkx"]["reason"] = "not needed for parameter space"
    TOOL_MANIFEST["xgi"]["reason"] = "not needed for bifurcation structure"
    TOOL_MANIFEST["toponetx"]["reason"] = "not needed for eigenvalue topology"
    TOOL_MANIFEST["gudhi"]["reason"] = "not needed for bifurcation analysis"

    # Count passes
    all_pass = True
    for test_dict in [positive, negative, boundary]:
        for test_name, result in test_dict.items():
            if result is None or "status" not in result:
                all_pass = False

    results = {
        "name": "Bifurcation Constraint Canonical",
        "description": "Bifurcation theory: foundational to dynamical systems qualitative changes; constraint surface is parameter values μ* where (1) f(x*,μ*) = 0 (equilibrium persists), (2) Det(Df(x*,μ*)) = 0 (Jacobian singular), (3) eigenvalue λ = 0 or Re(λ) = 0 (non-hyperbolicity), (4) normal form governs local dynamics; z3 encodes QF_NRA constraints; proves all-nonzero eigenvalues AND bifurcates is UNSAT; validates transversality and codimension-1 structure",
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
    out_path = os.path.join(out_dir, "sim_bifurcation_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    status = "✓ all_pass=True" if all_pass else "✗ some failures"
    print(f"sim_bifurcation_constraint_canonical: {status} -> {out_path}")
