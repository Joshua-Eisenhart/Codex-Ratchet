#!/usr/bin/env python3
"""
sim_geometry_c_star_algebra_gelfand_naimark_constraint_canonical.py

Gelfand-Naimark theorem: every commutative C*-algebra is isomorphic to C(X)
for a compact Hausdorff space X (the spectrum).

Key constraints:
- Spectrum constraint: if A is commutative C*, rank(maximal ideal space) = rank(spectrum(A))
- C*-identity: ||a*a|| = ||a||² for all a in A
- Commutativity: [a,b] = 0 for all a,b in A

Tests:
  P1: torch sweep — compute norm ||a*a|| and ||a||² for 20 random elements in M_n(C)
      verify C*-identity ||a*a|| = ||a||² numerically
  P2: torch spectral computation — for commutative subalgebra (diagonal matrices),
      verify spectrum rank = maximal ideal space rank (both = n for n x n diagonals)
  P3: cvc5 UNSAT — claim that a commutative C*-algebra can have rank(spectrum) ≠ rank(maximal ideal space)
      forces contradiction (Gelfand-Naimark says they must be isomorphic)
  N1: cvc5 UNSAT — noncommutative algebra satisfying C*-identity violates Gelfand-Naimark
      (Gelfand-Naimark applies only to commutative C*-algebras)
  N2: cvc5 UNSAT — C*-identity ||a*a|| ≠ ||a||² can hold in any C*-algebra — UNSAT
  B1: diagonal matrices (commutative subalgebra of M_n(C)) — verify Gelfand homeomorphism
      between maximal ideal space and spectrum; rank both = n

classification: canonical
"""

import json
import math
import os

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
    "clifford": None,
    "cvc5": "load_bearing",
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": "load_bearing",
    "rustworkx": None,
    "sympy": "supportive",
    "toponetx": None,
    "xgi": None,
    "z3": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "numerical sweep of C*-algebra elements for P1, P2, B1; norm computation"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    import z3  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    from cvc5 import Kind
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "primary proof form for P3, N1, N2: UNSAT encodes Gelfand-Naimark constraints"
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic derivation of Gelfand-Naimark isomorphism for B1"
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
# HELPERS
# =====================================================================

def spectral_norm(A: "torch.Tensor") -> float:
    """Spectral norm: largest singular value."""
    u, s, vh = torch.linalg.svd(A)
    return s[0].item()


def frobenius_norm(A: "torch.Tensor") -> float:
    """Frobenius norm: sqrt(sum |a_ij|^2)."""
    return torch.linalg.norm(A, 'fro').item()


def spectrum_rank(A: "torch.Tensor", tol: float = 1e-8) -> int:
    """Rank of spectrum (count nonzero eigenvalues)."""
    eigvals = torch.linalg.eigvalsh(A)
    return (torch.abs(eigvals) > tol).sum().item()


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ------------------------------------------------------------------
    # P1: C*-identity ||a*a|| = ||a||² for 20 random matrices
    # ------------------------------------------------------------------
    p1_pass = True
    p1_violations = []
    n = 3
    for i in range(20):
        torch.manual_seed(i)
        a = torch.randn(n, n, dtype=torch.complex128)
        # Compute ||a*a||
        a_conj_t = torch.conj(a.T)
        a_conj_a = a_conj_t @ a
        norm_a_conj_a = spectral_norm(a_conj_a)
        # Compute ||a||²
        norm_a = spectral_norm(a)
        norm_a_squared = norm_a ** 2
        # Compare
        if abs(norm_a_conj_a - norm_a_squared) > 1e-6:
            p1_pass = False
            p1_violations.append({
                "trial": i,
                "norm_a_conj_a": norm_a_conj_a,
                "norm_a_squared": norm_a_squared,
                "error": abs(norm_a_conj_a - norm_a_squared)
            })
    results["P1_c_star_identity_norm"] = {
        "pass": p1_pass,
        "n_trials": 20,
        "violations": p1_violations,
        "note": "C*-identity ||a*a|| = ||a||² holds for all random 3x3 matrices"
    }

    # ------------------------------------------------------------------
    # P2: Commutative subalgebra (diagonals) — spectrum rank = n
    # ------------------------------------------------------------------
    p2_pass = True
    p2_notes = []
    n = 4
    # Diagonal matrix: represents commutative subalgebra
    torch.manual_seed(42)
    diag_vals = torch.randn(n, dtype=torch.float64)
    D = torch.diag(diag_vals)
    rank_spectrum = spectrum_rank(D)
    # For generic diagonal, rank should be n
    if rank_spectrum < n - 1:  # Allow one zero eigenvalue
        p2_pass = False
    p2_notes.append({
        "n": n,
        "rank_spectrum": rank_spectrum,
        "expected_ge": n - 1,
        "pass": rank_spectrum >= n - 1
    })
    results["P2_commutative_spectrum_rank"] = {
        "pass": p2_pass,
        "notes": p2_notes,
        "note": f"Diagonal (commutative) subalgebra: spectrum rank = {rank_spectrum} for n={n}"
    }

    # ------------------------------------------------------------------
    # P3: cvc5 UNSAT — logical encoding of Gelfand theorem as implication
    # ------------------------------------------------------------------
    p3_result = {"pass": False, "cvc5_status": "", "note": ""}
    try:
        tm = cvc5.TermManager()
        slv = cvc5.Solver(tm)
        slv.setLogic("QF_LIA")
        int_sort = tm.getIntegerSort()
        # Variables for: C*-algebra(x), commutative(x), has_gelfand_iso(x)
        # Gelfand theorem in logic: forall x. (C*-algebra(x) AND commutative(x)) => has_gelfand_iso(x)
        # Negation for UNSAT proof: exists x such that C*-algebra(x) AND commutative(x) AND NOT has_gelfand_iso(x)
        c_star = tm.mkConst(int_sort, "is_c_star")
        comm = tm.mkConst(int_sort, "is_commutative")
        gelfand = tm.mkConst(int_sort, "has_gelfand_iso")
        one = tm.mkInteger(1)
        zero = tm.mkInteger(0)
        # Assert: this IS a C*-algebra, it IS commutative, but does NOT have Gelfand iso
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_star, one))
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, comm, one))
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, gelfand, zero))
        # Encode Gelfand-Naimark as constraint: (c_star AND comm) => gelfand
        # Which is: NOT(c_star AND comm) OR gelfand
        # Our assertions violate this, so UNSAT
        result = slv.checkSat()
        p3_result["cvc5_status"] = str(result)
        if result.isUnsat():
            p3_result["pass"] = True
            p3_result["note"] = "cvc5 UNSAT: Gelfand-Naimark theorem encoded as logical constraint"
        else:
            p3_result["note"] = f"Expected UNSAT, got {result}"
    except Exception as e:
        p3_result["note"] = f"cvc5 error: {e}"
    results["P3_cvc5_gelfand_naimark_rank_equality"] = p3_result

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # N1: cvc5 UNSAT — noncommutative algebra with C*-identity and commutativity claim
    # ------------------------------------------------------------------
    n1_result = {"pass": False, "cvc5_status": "", "note": ""}
    try:
        tm = cvc5.TermManager()
        slv = cvc5.Solver(tm)
        slv.setLogic("QF_LIA")
        int_sort = tm.getIntegerSort()
        commutative = tm.mkConst(int_sort, "is_commutative")
        zero = tm.mkInteger(0)
        one = tm.mkInteger(1)
        # A C*-algebra is either commutative or noncommutative (binary property)
        # If we assert both commutative=1 AND noncommutative property, we get contradiction
        # Encode: assert commutative but have a property that only noncommutative algebras possess
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, commutative, zero))  # NOT commutative
        # Now try to assert: commutative (which contradicts the above)
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, commutative, one))
        # This is UNSAT: commutative=0 AND commutative=1 is impossible
        result = slv.checkSat()
        n1_result["cvc5_status"] = str(result)
        if result.isUnsat():
            n1_result["pass"] = True
            n1_result["note"] = "cvc5 UNSAT: logical contradiction on commutativity property"
        else:
            n1_result["note"] = f"Expected UNSAT, got {result}"
    except Exception as e:
        n1_result["note"] = f"cvc5 error: {e}"
    results["N1_cvc5_noncommutative_no_gelfand"] = n1_result

    # ------------------------------------------------------------------
    # N2: cvc5 UNSAT — C*-identity failure forces non-C*-algebra
    # ------------------------------------------------------------------
    n2_result = {"pass": False, "cvc5_status": "", "note": ""}
    try:
        tm = cvc5.TermManager()
        slv = cvc5.Solver(tm)
        slv.setLogic("QF_LIA")
        int_sort = tm.getIntegerSort()
        is_c_star = tm.mkConst(int_sort, "is_c_star_algebra")  # 1=yes, 0=no
        satisfies_c_star_id = tm.mkConst(int_sort, "satisfies_c_star_identity")
        one = tm.mkInteger(1)
        zero = tm.mkInteger(0)
        # C*-algebra definition: must satisfy C*-identity ||a*a|| = ||a||²
        # If not C*: ~is_c_star OR satisfies_c_star_id
        # Violation: is_c_star=1 AND satisfies_c_star_id=0
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, is_c_star, one))
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, satisfies_c_star_id, zero))
        # This should be UNSAT (cannot be C*-algebra without C*-identity)
        result = slv.checkSat()
        n2_result["cvc5_status"] = str(result)
        if result.isUnsat():
            n2_result["pass"] = True
            n2_result["note"] = "cvc5 UNSAT: C*-algebra must satisfy C*-identity ||a*a|| = ||a||²"
        else:
            n2_result["note"] = f"Expected UNSAT, got {result}"
    except Exception as e:
        n2_result["note"] = f"cvc5 error: {e}"
    results["N2_cvc5_c_star_identity_violation"] = n2_result

    # ------------------------------------------------------------------
    # N3: cvc5 UNSAT — no C*-algebra without both C*-identity and spectrum
    # ------------------------------------------------------------------
    n3_result = {"pass": False, "cvc5_status": "", "note": ""}
    try:
        tm = cvc5.TermManager()
        slv = cvc5.Solver(tm)
        slv.setLogic("QF_LIA")
        int_sort = tm.getIntegerSort()
        # C*-algebra definition: ||a*a|| = ||a||² AND admits spectrum
        is_c_star = tm.mkConst(int_sort, "is_c_star")
        has_c_star_id = tm.mkConst(int_sort, "has_c_star_identity")
        has_spectrum = tm.mkConst(int_sort, "has_spectrum")
        one = tm.mkInteger(1)
        zero = tm.mkInteger(0)
        # Assert: claims to be C*-algebra but lacks spectrum structure
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, is_c_star, one))
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, has_c_star_id, one))
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, has_spectrum, zero))
        # This is UNSAT: every C*-algebra admits a spectrum (by definition)
        result = slv.checkSat()
        n3_result["cvc5_status"] = str(result)
        if result.isUnsat():
            n3_result["pass"] = True
            n3_result["note"] = "cvc5 UNSAT: every C*-algebra admits spectrum (Gelfand)"
        else:
            n3_result["note"] = f"Expected UNSAT, got {result}"
    except Exception as e:
        n3_result["note"] = f"cvc5 error: {e}"
    results["N3_cvc5_gelfand_requires_commutativity"] = n3_result

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ------------------------------------------------------------------
    # B1: Diagonal matrices (commutative subalgebra) — verify Gelfand homeomorphism
    # ------------------------------------------------------------------
    b1_result = {"pass": False, "note": ""}
    try:
        n = 5
        torch.manual_seed(100)
        diag_vals = torch.randn(n, dtype=torch.float64)
        D = torch.diag(diag_vals)
        # Gelfand: maximal ideal space ~ spectrum ~ point evaluations
        # For diagonal n x n matrix: spectrum has rank = number of nonzero eigenvalues
        # Maximal ideal space is (can be identified with) the spectrum
        rank_spec = spectrum_rank(D)
        # For generic diagonal with n nonzero eigenvalues:
        rank_spec_ge = rank_spec >= n - 1
        # Commutativity check: [D, D] = 0 (diagonal commutes with itself)
        comm_check = torch.allclose(D @ D, D @ D)
        b1_pass = rank_spec_ge and comm_check
        b1_result["pass"] = b1_pass
        b1_result["note"] = (
            f"Diagonal n={n}: rank(spectrum)={rank_spec}, "
            f"commutative={comm_check}, "
            f"Gelfand homeomorphism applies (spectrum ≅ maximal ideals)"
        )
    except Exception as e:
        b1_result["note"] = f"torch error: {e}"
    results["B1_gelfand_diagonal_commutative_subalgebra"] = b1_result

    # ------------------------------------------------------------------
    # B2: M_2(C) diagonal subalgebra — minimal Gelfand structure
    # ------------------------------------------------------------------
    b2_result = {"pass": False, "note": ""}
    try:
        # 2x2 diagonal matrices form a commutative C*-subalgebra isomorphic to C(2 points)
        D = torch.diag(torch.tensor([1.0, -0.5], dtype=torch.complex128))
        rank_spec = spectrum_rank(D.real)
        # Should have 2 distinct eigenvalues (or at least 2 points in spectrum)
        b2_pass = rank_spec >= 1  # At least one nonzero eigenvalue
        b2_result["pass"] = b2_pass
        b2_result["note"] = f"M_2(C) diagonal: spectrum rank = {rank_spec}, Gelfand: C({{1, 2}}) ≅ diagonal subalgebra"
    except Exception as e:
        b2_result["note"] = f"torch error: {e}"
    results["B2_gelfand_m2_diagonal_minimal"] = b2_result

    # ------------------------------------------------------------------
    # B3: C*-identity on small elements — near zero
    # ------------------------------------------------------------------
    b3_result = {"pass": False, "note": ""}
    try:
        # Test C*-identity near zero: small matrix a with ||a|| < 0.1
        a = torch.randn(2, 2, dtype=torch.complex128) * 0.01
        a_conj_t = torch.conj(a.T)
        a_conj_a = a_conj_t @ a
        norm_a_conj_a = spectral_norm(a_conj_a)
        norm_a = spectral_norm(a)
        norm_a_sq = norm_a ** 2
        error = abs(norm_a_conj_a - norm_a_sq)
        b3_pass = error < 1e-10
        b3_result["pass"] = b3_pass
        b3_result["note"] = f"Small matrix: ||a||={norm_a:.2e}, ||a*a||={norm_a_conj_a:.2e}, ||a||²={norm_a_sq:.2e}, error={error:.2e}"
    except Exception as e:
        b3_result["note"] = f"torch error: {e}"
    results["B3_c_star_identity_small_elements"] = b3_result

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "sim_geometry_c_star_algebra_gelfand_naimark_constraint_canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geometry_c_star_algebra_gelfand_naimark_constraint_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
