#!/usr/bin/env python3
"""Classical baseline sim: SO(3) rotor composition lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: rotation composition via 3x3 orthogonal matrices on R^3.
Innately missing: SU(2) double cover. A 2*pi rotation returns identity
rather than -1. Sign ambiguity discarded at the rotation-matrix level;
spin-1/2 half-angle structure cannot be expressed.
"""
import json, os
import numpy as np

classification = "classical_baseline"
divergence_log = (
    "classical SO(3) rotor misses spin-1/2 double cover; "
    "sign ambiguity discarded; 2*pi rotation collapses to identity"
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "3x3 rotation matrix algebra"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline only"},
    "sympy": {"tried": False, "used": False, "reason": "numeric composition suffices"},
    "z3": {"tried": False, "used": False, "reason": "no admissibility claim"},
    "clifford": {"tried": False, "used": False, "reason": "would lift to Cl(3); deliberately excluded"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "supportive",
    "sympy": "supportive",
}


def Rx(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(t):
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def is_SO3(R, tol=1e-10):
    return (np.allclose(R @ R.T, np.eye(3), atol=tol)
            and abs(np.linalg.det(R) - 1.0) < tol)


def run_positive_tests():
    results = {}
    # Composition closure
    R1, R2 = Rx(0.37), Ry(1.1)
    R12 = R1 @ R2
    results["composition_in_SO3"] = is_SO3(R12)
    # Associativity
    R3 = Rz(-0.8)
    results["associativity"] = np.allclose((R1 @ R2) @ R3, R1 @ (R2 @ R3), atol=1e-12)
    # Inverse = transpose
    results["inverse_is_transpose"] = np.allclose(R1.T @ R1, np.eye(3), atol=1e-12)
    # 2pi returns to identity (this is WHERE double cover is lost)
    results["2pi_returns_identity"] = np.allclose(Rz(2 * np.pi), np.eye(3), atol=1e-10)
    return results


def run_negative_tests():
    results = {}
    # A non-orthogonal matrix should NOT be SO(3)
    bad = np.array([[1.0, 0.1, 0], [0, 1, 0], [0, 0, 1]])
    results["reject_non_orthogonal"] = not is_SO3(bad)
    # Reflection has det = -1, not SO(3)
    reflect = np.diag([1.0, 1.0, -1.0])
    results["reject_reflection"] = not is_SO3(reflect)
    # Non-commutativity: Rx(a) Ry(b) != Ry(b) Rx(a) in general
    A, B = Rx(0.5), Ry(0.7)
    results["noncommutative"] = not np.allclose(A @ B, B @ A, atol=1e-8)
    return results


def run_boundary_tests():
    results = {}
    # Small angle: first-order matches I + t*J
    t = 1e-6
    J = np.array([[0, 0, 0], [0, 0, -1], [0, 1, 0]])
    results["small_angle_linearization"] = np.allclose(Rx(t), np.eye(3) + t * J, atol=1e-10)
    # 4pi also returns to identity classically (double cover INVISIBLE here)
    results["4pi_equals_2pi_classically"] = np.allclose(Rz(4 * np.pi), Rz(2 * np.pi), atol=1e-10)
    # Axis-angle of full rotation around any axis equals identity
    axis = np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0)
    K = np.array([[0, -axis[2], axis[1]],
                  [axis[2], 0, -axis[0]],
                  [-axis[1], axis[0], 0]])
    R_full = np.eye(3) + np.sin(2 * np.pi) * K + (1 - np.cos(2 * np.pi)) * (K @ K)
    results["rodrigues_2pi_identity"] = np.allclose(R_full, np.eye(3), atol=1e-10)
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "so3_rotor_composition_classical",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "classical SO(3) rotor misses spin-1/2 double cover",
            "2pi rotation collapses to identity (should yield -1 on spinors)",
            "no half-angle representation available on 3x3 matrices",
            "cannot distinguish a state from itself after odd multiples of 2pi",
        ],
    }
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "so3_rotor_composition_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
