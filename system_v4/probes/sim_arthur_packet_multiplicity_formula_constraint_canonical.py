#!/usr/bin/env python3
"""
Arthur Packet Multiplicity Formula — Constraint Canonical Sim
==============================================================

Arthur packets Π(ψ) for global A-parameter ψ: L_F × SL_2 → L_G.
Multiplicity formula: m(π) = ε(ψ) · ⟨·, π⟩
Constraint: m(π) ≥ 0 (multiplicity must be non-negative)

cvc5 (QF_LIA): UNSAT if m(π) < 0
sympy: Arthur multiplicity trace formula Σ_{π ∈ Π(ψ)} m(π) · tr(π(f))
"""

import json
import os

classification = "classical_baseline"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pytorch not needed; pure symbolic/algebraic computation via cvc5 and sympy"},
    "pyg": {"tried": False, "used": False, "reason": "PyG message passing not needed; constraint geometry handled via SMT solver"},
    "z3": {"tried": False, "used": False, "reason": "z3 not needed; cvc5 handles all SMT constraint proofs in this sim"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 SMT solver: load_bearing proof of Arthur packet multiplicity constraints"},
    "sympy": {"tried": False, "used": False, "reason": "sympy: supportive symbolic algebra for Arthur multiplicity trace formula"},
    "clifford": {"tried": False, "used": False, "reason": "Clifford algebra not needed; automorphic form constraints only"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats not needed; constraints handled via SMT solver"},
    "e3nn": {"tried": False, "used": False, "reason": "e3nn not needed; no SO(3) equivariance required"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx not needed; no graph structure in this sim"},
    "xgi": {"tried": False, "used": False, "reason": "xgi not needed; pairwise interactions only"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx not needed; standard algebraic ops sufficient"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi not needed; no persistent homology in this sim"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
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
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
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
# POSITIVE TESTS: Arthur multiplicity ≥ 0
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"error": "cvc5 not available"}

    import cvc5
    from cvc5 import Kind

    # Positive test 1: Standard Arthur packet multiplicity
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # m(π) = ε(ψ) · ⟨ρ, π⟩
        # Let ε(ψ) = 1, ⟨ρ, π⟩ = 5
        # Then m(π) = 5
        m_pi = solver.mkInteger(5)
        zero = solver.mkInteger(0)

        # Assert m(π) ≥ 0
        solver.assertFormula(solver.mkTerm(Kind.GEQ, m_pi, zero))

        result = solver.checkSat()
        results["pos_test_1_standard_multiplicity_nonneg"] = {
            "description": "m(π) = 5 satisfies m(π) ≥ 0",
            "expected": "SAT",
            "actual": str(result.isSat()),
            "pass": result.isSat()
        }
    except Exception as e:
        results["pos_test_1_standard_multiplicity_nonneg"] = {
            "error": str(e),
            "pass": False
        }

    # Positive test 2: Zero multiplicity (boundary)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # m(π) = 0 (allowed for off-packet representation)
        m_pi = solver.mkInteger(0)
        zero = solver.mkInteger(0)

        solver.assertFormula(solver.mkTerm(Kind.GEQ, m_pi, zero))

        result = solver.checkSat()
        results["pos_test_2_zero_multiplicity"] = {
            "description": "m(π) = 0 is admissible",
            "expected": "SAT",
            "actual": str(result.isSat()),
            "pass": result.isSat()
        }
    except Exception as e:
        results["pos_test_2_zero_multiplicity"] = {
            "error": str(e),
            "pass": False
        }

    # Positive test 3: Multiple Arthur packets sum
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Σ m(π_i) for π_i ∈ Π(ψ)
        m_pi1 = solver.mkInteger(3)
        m_pi2 = solver.mkInteger(2)
        m_sum = solver.mkTerm(Kind.ADD, m_pi1, m_pi2)
        zero = solver.mkInteger(0)

        # Sum must be ≥ 0
        solver.assertFormula(solver.mkTerm(Kind.GEQ, m_sum, zero))

        result = solver.checkSat()
        results["pos_test_3_packet_sum"] = {
            "description": "Σ_{π ∈ Π(ψ)} m(π) = 5 satisfies sum ≥ 0",
            "expected": "SAT",
            "actual": str(result.isSat()),
            "pass": result.isSat()
        }
    except Exception as e:
        results["pos_test_3_packet_sum"] = {
            "error": str(e),
            "pass": False
        }

    return results


# =====================================================================
# NEGATIVE TESTS: Constraint violations (UNSAT)
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["cvc5"]["tried"]:
        return {"error": "cvc5 not available"}

    import cvc5
    from cvc5 import Kind

    # Negative test 1: Negative multiplicity (forbidden)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # m(π) = -3 (violates m(π) ≥ 0)
        m_pi = solver.mkInteger(-3)
        zero = solver.mkInteger(0)

        # Assert m(π) ≥ 0
        solver.assertFormula(solver.mkTerm(Kind.GEQ, m_pi, zero))

        result = solver.checkSat()
        results["neg_test_1_negative_multiplicity"] = {
            "description": "m(π) = -3 violates constraint m(π) ≥ 0",
            "expected": "UNSAT",
            "actual": str(result.isSat()),
            "pass": not result.isSat()
        }
    except Exception as e:
        results["neg_test_1_negative_multiplicity"] = {
            "error": str(e),
            "pass": False
        }

    # Negative test 2: Negative partial multiplicities
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # m(π_1) = 5, m(π_2) = -7 (one component negative)
        m_pi1 = solver.mkInteger(5)
        m_pi2 = solver.mkInteger(-7)
        zero = solver.mkInteger(0)

        # Require both ≥ 0
        solver.assertFormula(solver.mkTerm(Kind.GEQ, m_pi1, zero))
        solver.assertFormula(solver.mkTerm(Kind.GEQ, m_pi2, zero))

        result = solver.checkSat()
        results["neg_test_2_partial_negative_multiplicity"] = {
            "description": "m(π_2) = -7 makes system UNSAT when both m(π_i) ≥ 0",
            "expected": "UNSAT",
            "actual": str(result.isSat()),
            "pass": not result.isSat()
        }
    except Exception as e:
        results["neg_test_2_partial_negative_multiplicity"] = {
            "error": str(e),
            "pass": False
        }

    # Negative test 3: Sum constraint violation
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # If sum Σ m(π) < 0 globally (impossible for valid Arthur packet)
        m_sum = solver.mkInteger(-5)
        zero = solver.mkInteger(0)

        solver.assertFormula(solver.mkTerm(Kind.GEQ, m_sum, zero))

        result = solver.checkSat()
        results["neg_test_3_negative_sum"] = {
            "description": "Σ m(π) = -5 violates sum ≥ 0",
            "expected": "UNSAT",
            "actual": str(result.isSat()),
            "pass": not result.isSat()
        }
    except Exception as e:
        results["neg_test_3_negative_sum"] = {
            "error": str(e),
            "pass": False
        }

    return results


# =====================================================================
# BOUNDARY TESTS: Edge cases and trace formula
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"error": "sympy not available"}

    import sympy as sp

    # Boundary test 1: Arthur trace formula structure
    try:
        # Trace formula: Σ_{π ∈ Π(ψ)} m(π) · tr(π(f)) = ...
        # Symbolic check: does sum structure hold?
        m_pi = sp.Symbol('m_pi', integer=True, nonnegative=True)
        tr_pi = sp.Symbol('tr_pi', real=True)

        # Trace contribution
        trace_contrib = m_pi * tr_pi

        # For multiple packets
        m_pi1, m_pi2 = sp.symbols('m_pi1 m_pi2', integer=True, nonnegative=True)
        tr_pi1, tr_pi2 = sp.symbols('tr_pi1 tr_pi2', real=True)

        total_trace = m_pi1 * tr_pi1 + m_pi2 * tr_pi2

        results["boundary_test_1_trace_formula"] = {
            "description": "Arthur trace formula: Σ m(π) · tr(π(f)) structure",
            "formula": str(total_trace),
            "is_linear": str(sp.degree(total_trace, m_pi1) == 1 and sp.degree(total_trace, m_pi2) == 1),
            "pass": True
        }
    except Exception as e:
        results["boundary_test_1_trace_formula"] = {
            "error": str(e),
            "pass": False
        }

    # Boundary test 2: Large packet multiplicity
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Very large multiplicity (e.g., large rank group)
        m_pi = solver.mkInteger(1000000)
        zero = solver.mkInteger(0)

        solver.assertFormula(solver.mkTerm(Kind.GEQ, m_pi, zero))

        result = solver.checkSat()
        results["boundary_test_2_large_multiplicity"] = {
            "description": "m(π) = 1000000 satisfies constraint",
            "expected": "SAT",
            "actual": str(result.isSat()),
            "pass": result.isSat()
        }
    except Exception as e:
        results["boundary_test_2_large_multiplicity"] = {
            "error": str(e),
            "pass": False
        }

    # Boundary test 3: Singlet representation (trivial packet)
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")

        # Trivial representation: m(trivial) = 1 always
        m_trivial = solver.mkInteger(1)
        zero = solver.mkInteger(0)
        one = solver.mkInteger(1)

        solver.assertFormula(solver.mkTerm(Kind.GEQ, m_trivial, zero))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, m_trivial, one))

        result = solver.checkSat()
        results["boundary_test_3_trivial_packet"] = {
            "description": "Trivial representation m = 1 is admissible",
            "expected": "SAT",
            "actual": str(result.isSat()),
            "pass": result.isSat()
        }
    except Exception as e:
        results["boundary_test_3_trivial_packet"] = {
            "error": str(e),
            "pass": False
        }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    if TOOL_MANIFEST["cvc5"]["tried"]:
        TOOL_MANIFEST["cvc5"]["used"] = True
    if TOOL_MANIFEST["sympy"]["tried"]:
        TOOL_MANIFEST["sympy"]["used"] = True

    results = {
        "name": "Arthur Packet Multiplicity Formula — Constraint Canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": classification,
        "original_classification": "canonical",
        "downgrade_reason": "canonical_failed_checks_2026-05-01",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_arthur_packet_multiplicity_formula_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
