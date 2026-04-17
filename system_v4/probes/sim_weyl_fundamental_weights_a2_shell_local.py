#!/usr/bin/env python3
"""
sim_weyl_fundamental_weights_a2_shell_local
===========================================

Shell-local probe for A2 fundamental weights and the dominant weight cone.

This stays finite and local: simple roots, coroot pairings, inverse Cartan data,
and dominant-weight inequalities only.
"""

import json
import math
import os

import sympy as sp
import torch
from z3 import Real, Solver, unsat

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "Torch tensors reconstruct A2 simple roots and fundamental weights in Euclidean coordinates and verify coroot-pairing identities numerically."},
    "pyg": {"tried": False, "used": False, "reason": "not required for this shell-local weight packet"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT witness excludes a false pairing assignment for the A2 fundamental-weight duality equations."},
    "cvc5": {"tried": False, "used": False, "reason": "z3 is sufficient for the local linear contradiction used here"},
    "sympy": {"tried": True, "used": True, "reason": "Exact inverse Cartan matrix and fundamental-weight coefficients are derived symbolically."},
    "clifford": {"tried": False, "used": False, "reason": "not required for this shell-local weight packet"},
    "geomstats": {"tried": False, "used": False, "reason": "not required for this shell-local weight packet"},
    "e3nn": {"tried": False, "used": False, "reason": "not required for this shell-local weight packet"},
    "rustworkx": {"tried": False, "used": False, "reason": "not required for this shell-local weight packet"},
    "xgi": {"tried": False, "used": False, "reason": "not required for this shell-local weight packet"},
    "toponetx": {"tried": False, "used": False, "reason": "not required for this shell-local weight packet"},
    "gudhi": {"tried": False, "used": False, "reason": "not required for this shell-local weight packet"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

SQRT3_2 = math.sqrt(3.0) / 2.0
ALPHA1 = torch.tensor([1.0, 0.0], dtype=torch.float64)
ALPHA2 = torch.tensor([-0.5, SQRT3_2], dtype=torch.float64)
COROOT1 = 2.0 * ALPHA1
COROOT2 = 2.0 * ALPHA2


def pairing(weight: torch.Tensor, coroot: torch.Tensor) -> float:
    return float(torch.dot(weight, coroot))


def run_positive_tests():
    cartan = sp.Matrix([[2, -1], [-1, 2]])
    cartan_inv = cartan.inv()
    omega1_coeffs = cartan_inv[:, 0]
    omega2_coeffs = cartan_inv[:, 1]
    omega1 = float(omega1_coeffs[0]) * ALPHA1 + float(omega1_coeffs[1]) * ALPHA2
    omega2 = float(omega2_coeffs[0]) * ALPHA1 + float(omega2_coeffs[1]) * ALPHA2
    pairing_matrix = torch.tensor([
        [pairing(omega1, COROOT1), pairing(omega1, COROOT2)],
        [pairing(omega2, COROOT1), pairing(omega2, COROOT2)],
    ], dtype=torch.float64)
    dominant_example = 2.0 * omega1 + 1.0 * omega2
    return {
        "P1_sympy_inverse_cartan_coefficients": {
            "pass": cartan_inv == sp.Matrix([[sp.Rational(2, 3), sp.Rational(1, 3)], [sp.Rational(1, 3), sp.Rational(2, 3)]]),
            "inverse_cartan": str(cartan_inv),
        },
        "P2_pytorch_coroot_pairing_identity": {
            "pass": torch.max(torch.abs(pairing_matrix - torch.eye(2, dtype=torch.float64))).item() < 1e-10,
            "pairing_matrix": pairing_matrix.tolist(),
        },
        "P3_dominant_weight_example_has_nonnegative_simple_coeffs": {
            "pass": pairing(dominant_example, COROOT1) >= 0 and pairing(dominant_example, COROOT2) >= 0,
            "dominant_weight_coroot_pairings": [pairing(dominant_example, COROOT1), pairing(dominant_example, COROOT2)],
        },
        "P4_weights_not_equal_to_simple_roots": {
            "pass": torch.max(torch.abs(omega1 - ALPHA1)).item() > 1e-6 and torch.max(torch.abs(omega2 - ALPHA2)).item() > 1e-6,
            "omega1": omega1.tolist(),
            "omega2": omega2.tolist(),
        },
    }


def run_negative_tests():
    solver = Solver()
    a, b = Real('a'), Real('b')
    # In the simple-root basis omega1 = a*alpha1 + b*alpha2.
    # Duality conditions use the A2 Cartan rows:
    #   <omega1, alpha1^vee> = 2a - b = 1
    #   <omega1, alpha2^vee> = -a + 2b = 0
    # Add the contradictory false assignment 2a - b = 0 to force UNSAT.
    solver.add(2 * a - b == 1)
    solver.add(-a + 2 * b == 0)
    solver.add(2 * a - b == 0)
    return {
        "N1_z3_false_pairing_assignment_unsat": {
            "pass": solver.check() == unsat,
            "z3_result": str(solver.check()),
        },
        "N2_zero_weight_not_strictly_dominant": {
            "pass": pairing(torch.zeros(2, dtype=torch.float64), COROOT1) == 0 and pairing(torch.zeros(2, dtype=torch.float64), COROOT2) == 0,
        },
        "N3_simple_root_basis_not_orthonormal": {
            "pass": abs(float(torch.dot(ALPHA1, ALPHA2)) + 0.5) < 1e-10,
            "alpha1_dot_alpha2": float(torch.dot(ALPHA1, ALPHA2)),
        },
    }


def run_boundary_tests():
    cartan_inv = torch.tensor([[2.0 / 3.0, 1.0 / 3.0], [1.0 / 3.0, 2.0 / 3.0]], dtype=torch.float64)
    zero_weight = torch.zeros(2, dtype=torch.float64)
    omega1 = cartan_inv[0, 0] * ALPHA1 + cartan_inv[1, 0] * ALPHA2
    return {
        "B1_zero_weight_on_cone_apex": {
            "pass": pairing(zero_weight, COROOT1) == 0 and pairing(zero_weight, COROOT2) == 0,
        },
        "B2_first_fundamental_weight_on_one_wall": {
            "pass": abs(pairing(omega1, COROOT1) - 1.0) < 1e-10 and abs(pairing(omega1, COROOT2)) < 1e-10,
            "pairings": [pairing(omega1, COROOT1), pairing(omega1, COROOT2)],
        },
    }


if __name__ == "__main__":
    results = {
        "name": "sim_weyl_fundamental_weights_a2_shell_local",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_fundamental_weights_a2_shell_local_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(out_path)
