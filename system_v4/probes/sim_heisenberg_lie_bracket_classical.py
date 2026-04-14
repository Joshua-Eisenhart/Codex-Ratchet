#!/usr/bin/env python3
"""Classical baseline sim: Lie bracket nilpotency on the Heisenberg algebra.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: the 3x3 Heisenberg algebra h_3 spanned by X, Y, Z with
[X,Y] = Z and [X,Z] = [Y,Z] = 0. Step-2 nilpotent structure is exact.
Innately missing: noncommutative exponentiation and the CCR at operator
level. Although the commutator [X,Y]=Z is faithfully encoded, the
BCH / Weyl-form unitary structure is NOT: classical exp(X) exp(Y) via
matrix exponentiation of strictly upper-triangular matrices collapses
because Z is nilpotent. The canonical bosonic CCR [x,p] = i hbar with
nonzero c-number center, and Stone-von Neumann uniqueness, are absent.
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "step-2 nilpotency survives; CCR [x,p]=i*hbar as operators on L^2, "
    "and the Weyl-form unitary composition, are not represented"
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "matrix bracket and exp"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "numeric matrices suffice"},
    "z3": {"tried": False, "used": False, "reason": "no admissibility"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "supportive",
    "sympy": "supportive",
}


def bracket(A, B):
    return A @ B - B @ A


X = np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], dtype=float)
Y = np.array([[0, 0, 0], [0, 0, 1], [0, 0, 0]], dtype=float)
Z = np.array([[0, 0, 1], [0, 0, 0], [0, 0, 0]], dtype=float)


def run_positive_tests():
    results = {}
    # Defining relation [X,Y] = Z
    results["XY_bracket_is_Z"] = np.allclose(bracket(X, Y), Z, atol=1e-12)
    # Center: [X,Z] = [Y,Z] = 0
    results["X_Z_central"] = np.allclose(bracket(X, Z), 0, atol=1e-12)
    results["Y_Z_central"] = np.allclose(bracket(Y, Z), 0, atol=1e-12)
    # Step-2 nilpotent: [[A,B],C] = 0 for all A,B,C in algebra
    for A in (X, Y, Z):
        for B in (X, Y, Z):
            for C in (X, Y, Z):
                assert np.allclose(bracket(bracket(A, B), C), 0, atol=1e-12)
    results["step_2_nilpotent"] = True
    # Antisymmetry and Jacobi
    results["antisymmetry"] = np.allclose(bracket(X, Y) + bracket(Y, X), 0, atol=1e-12)
    JAC = bracket(X, bracket(Y, Z)) + bracket(Y, bracket(Z, X)) + bracket(Z, bracket(X, Y))
    results["jacobi"] = np.allclose(JAC, 0, atol=1e-12)
    return results


def run_negative_tests():
    results = {}
    # X and Y do not commute
    results["XY_not_commutative"] = not np.allclose(bracket(X, Y), 0, atol=1e-12)
    # Arbitrary non-algebra matrix is NOT in the span — det check
    M = np.eye(3)
    # I is not nilpotent
    results["I_not_nilpotent"] = not np.allclose(np.linalg.matrix_power(M, 3), 0, atol=1e-12)
    # Mixing in a non-central element would break the step-2 property
    W = np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0]], dtype=float)
    results["W_out_of_algebra"] = not np.allclose(bracket(bracket(W, X), Y), 0, atol=1e-12)
    return results


def run_boundary_tests():
    results = {}
    # exp(X) exp(Y) vs exp(X+Y) differs by (1/2)[X,Y] = (1/2) Z, BCH to 2nd order
    A = np.eye(3) + X + 0.5 * X @ X + (1 / 6) * X @ X @ X  # actually exp(X) = I+X since X^2=0
    # X^2 = 0 for this X
    results["X_squared_zero"] = np.allclose(X @ X, 0, atol=1e-12)
    results["Y_squared_zero"] = np.allclose(Y @ Y, 0, atol=1e-12)
    expX = np.eye(3) + X
    expY = np.eye(3) + Y
    expX_expY = expX @ expY
    expY_expX = expY @ expX
    # BCH: exp(X) exp(Y) = exp(X + Y + 1/2 [X,Y]) since higher brackets vanish
    bch = np.eye(3) + (X + Y) + 0.5 * Z + 0.5 * (X + Y) @ (X + Y)
    # (X+Y)^2 = XY + YX = Z + (-Z) ... actually XY = Z, YX = 0, so (X+Y)^2 = Z
    results["BCH_closed_form"] = np.allclose(expX_expY, bch, atol=1e-10)
    # Non-commutativity: expX expY != expY expX
    results["exp_noncommutes"] = not np.allclose(expX_expY, expY_expX, atol=1e-10)
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "heisenberg_lie_bracket_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "CCR [x,p] = i*hbar at operator level on infinite-dim L^2 absent",
            "Stone-von Neumann uniqueness invisible in nilpotent matrix rep",
            "Weyl unitary form exp(i(aX+bY+cZ)) and its phase cocycle missing",
            "no center with nontrivial unitary character",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "heisenberg_lie_bracket_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
