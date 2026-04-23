#!/usr/bin/env python3
"""
sim_spectral_triple_carrier.py -- Simplest concrete spectral triple (A, H, D).

Carrier lego for the SpectralTriple column in the tool-lego integration matrix.
  A = M_2(C) (complex 2x2 matrices, *-algebra)
  H = C^2
  D = sigma_x (Pauli-X), self-adjoint

Verifies:
  (1) D is self-adjoint: D = D^*
  (2) Compact resolvent: automatic in finite dim (any bounded op on f.d. H is compact)
  (3) [D, a] is bounded for all a in A (finite dim => always bounded; we check
      operator norm stays finite over a sampled/symbolic basis)
"""

import json
import os
import numpy as np

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

# numpy is the load-bearing linear-algebra layer for this carrier.
TOOL_MANIFEST["pytorch"]["reason"] = "not needed; finite-dim 2x2 linear algebra handled by numpy"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


# ---------------------------------------------------------------------
# Core objects
# ---------------------------------------------------------------------

D = np.array([[0.0 + 0j, 1.0 + 0j],
              [1.0 + 0j, 0.0 + 0j]])  # Pauli-X


def dagger(M):
    return M.conj().T


def commutator(X, Y):
    return X @ Y - Y @ X


def op_norm(M):
    # spectral norm = largest singular value
    return float(np.linalg.norm(M, ord=2))


# ---------------------------------------------------------------------
# POSITIVE TESTS
# ---------------------------------------------------------------------

def run_positive_tests():
    results = {}

    # (1) D self-adjoint
    results["D_self_adjoint"] = {
        "pass": bool(np.allclose(D, dagger(D))),
        "residual": float(np.linalg.norm(D - dagger(D))),
    }

    # (2) Compact resolvent -- trivial in finite dim; verify (D - i)^{-1} exists.
    res = np.linalg.inv(D - 1j * np.eye(2))
    results["compact_resolvent"] = {
        "pass": True,
        "note": "finite-dim: every bounded operator is compact",
        "resolvent_norm": op_norm(res),
    }

    # (3) [D, a] bounded for a basis of M_2(C).
    basis = [
        np.array([[1, 0], [0, 0]], dtype=complex),
        np.array([[0, 1], [0, 0]], dtype=complex),
        np.array([[0, 0], [1, 0]], dtype=complex),
        np.array([[0, 0], [0, 1]], dtype=complex),
    ]
    norms = [op_norm(commutator(D, a)) for a in basis]
    results["bounded_commutators_basis"] = {
        "pass": all(np.isfinite(n) for n in norms),
        "norms": norms,
    }

    # Random sampled a in M_2(C): [D, a] bounded by 2 * ||a||.
    rng = np.random.default_rng(0)
    sample_checks = []
    for _ in range(32):
        a = rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
        lhs = op_norm(commutator(D, a))
        rhs = 2.0 * op_norm(a)  # ||D||=1, triangle gives 2||D|| ||a||
        sample_checks.append(lhs <= rhs + 1e-9)
    results["bounded_commutators_random"] = {
        "pass": all(sample_checks),
        "n_samples": len(sample_checks),
    }

    # Sympy supportive cross-check: exact [D, a] for generic symbolic a.
    if sp is not None:
        a11, a12, a21, a22 = sp.symbols("a11 a12 a21 a22")
        Ds = sp.Matrix([[0, 1], [1, 0]])
        As = sp.Matrix([[a11, a12], [a21, a22]])
        C = sp.simplify(Ds * As - As * Ds)
        expected = sp.Matrix([[a21 - a12, a22 - a11],
                              [a11 - a22, a12 - a21]])
        results["sympy_exact_commutator"] = {
            "pass": bool(sp.simplify(C - expected) == sp.zeros(2, 2)),
            "form": str(C.tolist()),
        }
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "exact symbolic verification of [D,a] form"
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    return results


# ---------------------------------------------------------------------
# NEGATIVE TESTS
# ---------------------------------------------------------------------

def run_negative_tests():
    results = {}

    # A non-self-adjoint candidate must fail the self-adjoint check.
    D_bad = np.array([[0, 1], [0, 0]], dtype=complex)
    results["non_self_adjoint_rejected"] = {
        "pass": not np.allclose(D_bad, dagger(D_bad)),
        "residual": float(np.linalg.norm(D_bad - dagger(D_bad))),
    }

    # A non-* element (we allow arbitrary a in A; algebra is all of M_2(C)),
    # but commutator with identity must vanish (sanity / structural check).
    I = np.eye(2, dtype=complex)
    results["identity_commutes_with_D"] = {
        "pass": bool(np.allclose(commutator(D, I), np.zeros((2, 2)))),
    }

    return results


# ---------------------------------------------------------------------
# BOUNDARY TESTS
# ---------------------------------------------------------------------

def run_boundary_tests():
    results = {}

    # Zero algebra element -> zero commutator.
    Z = np.zeros((2, 2), dtype=complex)
    results["zero_element"] = {
        "pass": bool(np.allclose(commutator(D, Z), Z)),
    }

    # D commutes with itself.
    results["D_commutes_with_D"] = {
        "pass": bool(np.allclose(commutator(D, D), np.zeros((2, 2)))),
    }

    # Large-norm a: commutator still finite and bounded by 2||a||.
    a_big = 1e6 * np.array([[0, 1], [0, 0]], dtype=complex)
    lhs = op_norm(commutator(D, a_big))
    rhs = 2.0 * op_norm(a_big)
    results["large_norm_bound"] = {
        "pass": bool(lhs <= rhs + 1e-3),
        "lhs": lhs,
        "rhs": rhs,
    }

    return results


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

if __name__ == "__main__":
    # numpy is load-bearing: all structural verifications (self-adjointness,
    # resolvent existence, operator norms of commutators) are computed via
    # numpy linear algebra. No numeric claim in this sim is reachable
    # without it.
    TOOL_MANIFEST["pytorch"]["used"] = False
    TOOL_MANIFEST_numpy_note = {
        "tried": True,
        "used": True,
        "reason": "spectral norms, resolvent inverse, and commutator matrices "
                  "for the (A,H,D) triple are all computed with numpy; the "
                  "self-adjoint, compact-resolvent, and boundedness claims "
                  "are load-bearing on numpy linear algebra.",
    }
    TOOL_MANIFEST["numpy"] = TOOL_MANIFEST_numpy_note
    TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    def all_pass(block):
        return all(v.get("pass", False) for v in block.values())

    overall = all_pass(positive) and all_pass(negative) and all_pass(boundary)

    results = {
        "name": "sim_spectral_triple_carrier",
        "description": "Simplest concrete spectral triple (M_2(C), C^2, sigma_x)",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_spectral_triple_carrier_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass={overall}")
