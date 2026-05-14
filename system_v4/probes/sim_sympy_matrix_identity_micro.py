#!/usr/bin/env python3
"""
sim_sympy_matrix_identity_micro.py -- SymPy matrix inverse identity micro-probe.

Tool-stage scope:
  tool_target: sympy
  function_surface: Matrix.inv plus Matrix.equals over exact 2x2 matrices
  micro_claim: SymPy can certify A*A.inv() = I and A.inv()*A = I for
    an invertible exact matrix, and exclude wrong or singular inverse claims.

This is pre-lego evidence only. It does not promote an operator family, bridge
claim, or tool-tool coupling.
"""

import json
import os
import sys

from receipt_boundary import apply_default_receipt_boundary


CLASSIFICATION = "canonical"
classification = CLASSIFICATION
NAME = "sim_sympy_matrix_identity_micro"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not used: this exact symbolic matrix identity micro has no tensor or autograd surface"},
    "pyg": {"tried": False, "used": False, "reason": "not used: no message-passing graph or PyG data object appears in this matrix fixture"},
    "z3": {"tried": False, "used": False, "reason": "not used: no SMT encoding is needed for SymPy exact Matrix.inv/equals checks"},
    "cvc5": {"tried": False, "used": False, "reason": "not used: no SMT encoding is needed for SymPy exact Matrix.inv/equals checks"},
    "sympy": {"tried": False, "used": False, "reason": "under test"},
    "clifford": {"tried": False, "used": False, "reason": "not used: no geometric algebra blade, rotor, or MultiVector operation appears in this fixture"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: no manifold metric, geodesic, or group operation appears in this fixture"},
    "e3nn": {"tried": False, "used": False, "reason": "not used: no equivariance, irrep, or Wigner-D surface appears in this fixture"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used: no graph reachability or DAG operation appears in this matrix fixture"},
    "xgi": {"tried": False, "used": False, "reason": "not used: no hyperedge incidence or higher-order graph operation appears in this fixture"},
    "toponetx": {"tried": False, "used": False, "reason": "not used: no cell complex, chain group, or boundary operator appears in this fixture"},
    "gudhi": {"tried": False, "used": False, "reason": "not used: no persistence, filtration, or simplex tree operation appears in this fixture"},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "load-bearing: Matrix.inv computes the exact candidate inverse and "
        "Matrix.equals/simplify decide the identity verdict"
    )
    SP_OK = True
    SP_VERSION = sp.__version__
except Exception as exc:
    SP_OK = False
    SP_VERSION = None
    TOOL_MANIFEST["sympy"]["reason"] = f"not installed: {exc}"


def _missing_sympy():
    return {"pass": False, "detail": "sympy unavailable"}


def _matrix_zero(matrix):
    return all(sp.simplify(entry) == 0 for entry in matrix)


def run_positive_tests():
    if not SP_OK:
        return {"sympy_available": _missing_sympy()}

    A = sp.Matrix([[2, 1], [1, 1]])
    inv_a = A.inv()
    identity = sp.eye(2)
    right_identity = A * inv_a
    left_identity = inv_a * A

    return {
        "C1_right_inverse_identity": {
            "pass": right_identity.equals(identity),
            "fixture": str(A),
            "expected": "A * A.inv() = I",
            "got": str(right_identity),
        },
        "C2_left_inverse_identity": {
            "pass": left_identity.equals(identity),
            "fixture": str(A),
            "expected": "A.inv() * A = I",
            "got": str(left_identity),
        },
        "C3_simplify_agrees_with_equals": {
            "pass": _matrix_zero(right_identity - identity) and _matrix_zero(left_identity - identity),
            "expected": "entrywise simplify reduces both inverse identities to zero",
        },
    }


def run_negative_tests():
    if not SP_OK:
        return {"sympy_available": _missing_sympy()}

    A = sp.Matrix([[2, 1], [1, 1]])
    wrong_inverse = sp.Matrix([[1, -1], [-1, 3]])
    wrong_product = A * wrong_inverse
    identity = sp.eye(2)
    singular = sp.Matrix([[1, 2], [2, 4]])

    try:
        singular.inv()
        singular_inverse_excluded = False
        singular_error = "no error"
    except Exception as exc:
        singular_inverse_excluded = True
        singular_error = type(exc).__name__

    return {
        "C4_wrong_inverse_excluded": {
            "pass": wrong_product.equals(identity) is False and not _matrix_zero(wrong_product - identity),
            "expected": "wrong inverse candidate is not admitted",
            "got": str(wrong_product),
        },
        "C5_singular_inverse_excluded": {
            "pass": singular.det() == 0 and singular_inverse_excluded,
            "expected": "determinant-zero matrix is not invertible",
            "determinant": str(singular.det()),
            "exception": singular_error,
        },
    }


def run_boundary_tests():
    if not SP_OK:
        return {"sympy_available": _missing_sympy()}

    t = sp.Symbol("t")
    boundary = sp.diag(1, t)
    det_boundary = sp.factor(boundary.det())
    identity = sp.eye(2)
    scale = sp.Symbol("scale", nonzero=True)
    A = sp.Matrix([[2, 1], [1, 1]])
    scaled = scale * A
    scaled_identity = scaled * scaled.inv()

    return {
        "C6_symbolic_determinant_boundary": {
            "pass": det_boundary == t and det_boundary.subs(t, 0) == 0 and det_boundary.subs(t, 1) == 1,
            "expected": "invertibility boundary is exactly determinant t = 0",
            "determinant": str(det_boundary),
        },
        "C7_identity_matrix_boundary": {
            "pass": identity.inv().equals(identity) and (identity * identity.inv()).equals(identity),
            "expected": "I is its own inverse and remains admitted at the neutral boundary",
        },
        "C8_nonzero_scalar_boundary": {
            "pass": scaled_identity.equals(identity) and _matrix_zero(scaled_identity - identity),
            "expected": "(scale*A) * (scale*A).inv() = I for nonzero symbolic scale",
            "got": str(scaled_identity),
        },
    }


def _all_pass(section):
    return all(bool(value.get("pass", False)) for value in section.values())


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _all_pass(positive),
        "negative_all_pass": _all_pass(negative),
        "boundary_all_pass": _all_pass(boundary),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": NAME,
        "probe_family": "M_sympy_matrix_inverse_identity",
        "constraint_set": "C_exact_matrix_inverse_identity",
        "function_surface": "sympy.Matrix.inv plus Matrix.equals over exact 2x2 matrices",
        "micro_claim": "SymPy certifies exact matrix inverse identity and excludes wrong or singular inverse claims.",
        "operation_sequence": [
            "construct one exact invertible 2x2 integer matrix",
            "compute Matrix.inv for the fixture",
            "multiply A*A.inv() and A.inv()*A",
            "compare both products with the identity matrix using Matrix.equals and entrywise simplify",
            "run wrong-inverse and singular-matrix graveyards",
            "run determinant, identity-matrix, and nonzero-symbolic-scale boundary checks",
        ],
        "carrier_topology": (
            "exact 2x2 symbolic matrix fixture over SymPy expressions; no "
            "density carrier, graph, manifold, bundle, or topology claim"
        ),
        "observable": (
            "Matrix.equals identity verdicts, entrywise simplified residuals, "
            "determinant boundary value, and singular inverse exception class"
        ),
        "pass_fail_predicate": (
            "right and left inverse products equal I; entrywise residuals reduce "
            "to zero; wrong inverse and determinant-zero inverse claims are "
            "excluded; determinant/identity/nonzero-scale boundaries behave as declared"
        ),
        "graveyards": [
            "wrong inverse candidate produces non-identity product and nonzero residual",
            "determinant-zero matrix raises an inverse exclusion",
            "symbolic determinant boundary t=0 prevents hidden promotion to all matrices",
        ],
        "baselines": [
            "identity matrix is its own inverse at the neutral boundary",
            "nonzero symbolic scalar multiple preserves inverse identity",
            "determinant t for diag(1,t) gives the exact invertibility boundary",
        ],
        "alternative_formulations": [
            "compute adjugate/determinant inverse formula and compare to Matrix.inv",
            "encode 2x2 inverse equations in z3 or cvc5 over bounded rational fixtures",
            "extend to operator-family lego fit only after exact scalar and matrix receipts exist",
        ],
        "tool_function_needs": {
            "sympy": ["Matrix", "Matrix.inv", "Matrix.equals", "simplify", "factor", "det"],
        },
        "lego_coupling_target": "exact_matrix_identity_micro; operator_family_later_only",
        "classification": CLASSIFICATION,
        "sympy_version": SP_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "criteria_checked": [
            "C1: right inverse identity A*A.inv() = I",
            "C2: left inverse identity A.inv()*A = I",
            "C3: entrywise simplify agrees with Matrix.equals",
            "C4: wrong inverse candidate is excluded",
            "C5: determinant-zero matrix inverse is excluded",
            "C6: symbolic determinant boundary t = 0 is explicit",
            "C7: identity matrix inverse is the neutral boundary",
            "C8: nonzero symbolic scalar multiple preserves inverse identity",
        ],
        "surviving_alternatives": [
            "Other invertible exact matrices remain admissible under this micro surface.",
            "Singular matrices remain admissible for non-inverse matrix identities, but not for inverse identity claims.",
        ],
        "demotion_condition": (
            "Demote SymPy Matrix.inv/Matrix.equals for this surface if exact inverse identities do not reduce "
            "to identity, if a wrong inverse is admitted, or if singular inverse claims are not excluded."
        ),
        "out_of_scope": [
            "lego promotion",
            "tool-tool coupling",
            "bridge claim",
            "whole SymPy library proof",
            "operator-family admission beyond this exact matrix inverse identity fixture",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_sympy_matrix_identity_micro",
        target="Use as bounded SymPy exact matrix-inverse identity function evidence before operator-family lego fit packets.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
    sys.exit(0 if summary["all_pass"] else 1)
