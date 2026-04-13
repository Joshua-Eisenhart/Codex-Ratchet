#!/usr/bin/env python3
"""Classical baseline sim: operator_coordinate_representation lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: an operator A in basis {e_i} has matrix [A]_ij = <e_i, A e_j>;
change of basis U gives [A]' = U^H [A] U; invariants (trace, det, spectrum)
are basis-independent.
Innately missing: Cl(n) rotor / gauge-covariant representation; constraint
geometry where certain bases are inadmissible. Classical sim treats all
bases as equally valid — useful failure data for nonclassical bases that
violate admissibility.
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "matrix basis change"},
    "clifford": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def change_basis(A, U):
    return U.conj().T @ A @ U

def run_positive_tests():
    A = np.array([[2.0, 1.0], [1.0, 3.0]])
    # unitary basis rotation
    th = 0.7
    U = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    Ap = change_basis(A, U)
    return {
        "trace_invariant": abs(np.trace(A) - np.trace(Ap)) < 1e-9,
        "det_invariant": abs(np.linalg.det(A) - np.linalg.det(Ap)) < 1e-9,
        "spectrum_invariant": bool(np.allclose(
            np.sort(np.linalg.eigvalsh(A)), np.sort(np.linalg.eigvalsh(Ap)), atol=1e-9)),
    }

def run_negative_tests():
    A = np.array([[2.0, 1.0], [1.0, 3.0]])
    # non-unitary "basis change" -> invariants should NOT be preserved
    M = np.array([[2.0, 0.0], [0.0, 1.0]])
    Ap = M.conj().T @ A @ M
    return {
        "non_unitary_breaks_trace": abs(np.trace(A) - np.trace(Ap)) > 1e-6,
    }

def run_boundary_tests():
    A = np.eye(3) * 1.5
    U = np.eye(3)
    Ap = change_basis(A, U)
    # identity basis change: matrix unchanged
    return {
        "identity_basis_noop": bool(np.allclose(A, Ap)),
        "diag_spectrum_preserved": bool(np.allclose(
            np.sort(np.diag(A)), np.sort(np.linalg.eigvalsh(Ap)))),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "operator_coordinate_representation_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "summary": {"all_pass": all_pass},
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "operator_coordinate_representation_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
