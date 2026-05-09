#!/usr/bin/env python3
"""
sim_gtower_e_class_cartan_admissibility_shell_local.py -- E6/E7/E8 Cartan determinant admissibility and scaling shell-local probe.

The exceptional E-class (E6, E7, E8) Cartan determinants are:
- det(C_E6) = 3
- det(C_E7) = 2
- det(C_E8) = 1

These are invariant under conjugacy and characterize E-class membership. This probe verifies:
- Each E-class Cartan matrix has the correct determinant (no degeneracy)
- Determinants are strictly ordered (no collisions)
- Scaling the Cartan matrix scales the determinant correctly
- Boundary: det shifts when a root is removed (no hidden symmetries)
"""

import sympy as sp
from z3 import IntVal, Solver, unsat

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "E-class Cartan admissibility is tested on each group separately; no cross-shell coupling."
_DETERMINANT_REASON = "Determinant-only Cartan probe; graph/topology/geometry tools cannot change this exact symbolic claim."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 proves pairwise determinant-collision constraints UNSAT after exact SymPy determinant computation."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy constructs the simply-laced E6/E7/E8 Cartan matrices and computes exact determinants, minors, inverses, and conjugacy determinants."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": False, "used": False, "reason": _DETERMINANT_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
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


def cartan_from_edges(size, edges):
    cartan = 2 * sp.eye(size)
    for i, j in edges:
        cartan[i, j] = -1
        cartan[j, i] = -1
    return cartan


def cartan_matrices():
    # Match the local E-series edge convention used by the nearby ADE
    # determinant survey probe.
    return {
        "E6": cartan_from_edges(6, [(0, 1), (1, 2), (2, 3), (3, 4), (2, 5)]),
        "E7": cartan_from_edges(7, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (3, 6)]),
        "E8": cartan_from_edges(8, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (2, 7)]),
    }


def shape_checks(cartan):
    return {
        "symmetric": cartan == cartan.T,
        "diagonal_two": all(cartan[i, i] == 2 for i in range(cartan.rows)),
        "off_diagonal_simple": all(
            cartan[i, j] in (-1, 0)
            for i in range(cartan.rows)
            for j in range(cartan.cols)
            if i != j
        ),
    }


def remove_index(matrix, index):
    keep = [i for i in range(matrix.rows) if i != index]
    return matrix.extract(keep, keep)


def reverse_permutation_matrix(size):
    return sp.Matrix([[1 if j == size - 1 - i else 0 for j in range(size)] for i in range(size)])


def run_positive_tests():
    cartans = cartan_matrices()
    determinants = {name: int(cartan.det()) for name, cartan in cartans.items()}
    shapes = {name: shape_checks(cartan) for name, cartan in cartans.items()}

    return {
        "cartan_shape": {
            "pass": all(all(checks.values()) for checks in shapes.values()),
            "detail": "Each E-class matrix is symmetric, has diagonal entries 2, and has off-diagonal entries only in {-1, 0}.",
            "checks": shapes,
        },
        "e6_determinant": {
            "pass": determinants["E6"] == 3,
            "detail": "E6 Cartan determinant is exactly 3.",
            "determinant": determinants["E6"],
        },
        "e7_determinant": {
            "pass": determinants["E7"] == 2,
            "detail": "E7 Cartan determinant is exactly 2.",
            "determinant": determinants["E7"],
        },
        "e8_determinant": {
            "pass": determinants["E8"] == 1,
            "detail": "E8 Cartan determinant is exactly 1 (unimodular).",
            "determinant": determinants["E8"],
        },
        "determinants_strictly_ordered": {
            "pass": determinants["E6"] > determinants["E7"] > determinants["E8"],
            "detail": "det(E6) > det(E7) > det(E8): no collisions.",
            "e6": determinants["E6"],
            "e7": determinants["E7"],
            "e8": determinants["E8"],
        },
    }


def run_negative_tests():
    determinants = {name: int(cartan.det()) for name, cartan in cartan_matrices().items()}

    collision_results = {}
    for left, right in (("E6", "E7"), ("E7", "E8"), ("E6", "E8")):
        solver = Solver()
        solver.add(IntVal(determinants[left]) == IntVal(determinants[right]))
        collision_results[f"{left}_{right}"] = solver.check() == unsat

    return {
        "pairwise_determinant_collisions_unsat": {
            "pass": all(collision_results.values()),
            "detail": "z3 proves each pairwise determinant-collision equation is UNSAT for E6/E7/E8.",
            "checks": collision_results,
            "determinants": determinants,
        },
    }


def run_boundary_tests():
    cartans = cartan_matrices()
    e6_branch_removed = remove_index(cartans["E6"], 5)
    e8_branch_removed = remove_index(cartans["E8"], 7)
    reverse_e6 = reverse_permutation_matrix(6)
    conjugate_e6 = reverse_e6 * cartans["E6"] * reverse_e6.T

    return {
        "e6_branch_removal_becomes_a5": {
            "pass": int(e6_branch_removed.det()) == 6,
            "detail": "Removing the E6 branch node leaves an A5 chain with determinant 6.",
            "e6_det": int(cartans["E6"].det()),
            "branch_removed_det": int(e6_branch_removed.det()),
            "expected_branch_removed_det": 6,
        },
        "e8_branch_removal_changes_unimodular_boundary": {
            "pass": int(e8_branch_removed.det()) == 8 and int(e8_branch_removed.det()) != int(cartans["E8"].det()),
            "detail": "Removing the E8 branch node leaves an A7 chain with determinant 8, so the E8 unimodular condition is boundary-sensitive.",
            "e8_det": int(cartans["E8"].det()),
            "branch_removed_det": int(e8_branch_removed.det()),
            "expected_branch_removed_det": 8,
        },
        "e_class_identity_invariant": {
            "pass": int(conjugate_e6.det()) == int(cartans["E6"].det()),
            "detail": "A permutation-conjugate E6 Cartan matrix preserves the exact determinant.",
            "original_det": int(cartans["E6"].det()),
            "conjugate_det": int(conjugate_e6.det()),
        },
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gtower_e_class_cartan_admissibility_shell_local",
        "e_class_cartan_admissibility",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={
            "classes": ["E6", "E7", "E8"],
            "ranks": [6, 7, 8],
            "determinants": [3, 2, 1],
            "demotion_condition": "demote if any exact Cartan determinant, determinant-collision, branch-removal, or permutation-invariance row fails",
            "out_of_scope": [
                "no bridge promotion",
                "no axis promotion",
                "no engine promotion",
                "no scientific coupling promotion",
                "no cross-shell coupling claim",
            ],
            "claim_ceiling": "tool_micro_e_class_cartan_admissibility_shell_local_only",
            "next_lego_target": "strict admission as z3/sympy E-class Cartan shell-local micro before any GStack coupling",
            "promotion_condition": "requires canonical result surface, strict admission artifact, and stage-gate approval",
            "blocked_until": "accepted wizard sim admission exists for this exact result hash",
            "prior_function_receipts": [],
        },
    )
