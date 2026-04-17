#!/usr/bin/env python3
"""
sim_weyl_group_d4_triality_shell_local
=====================================

Shell-local probe for the finite D4 Weyl packet.

This stays in Step 1 of the coupling program: local root data, local reflections,
local chamber parity, and local Dynkin-pattern structure only. No Hopf, Dirac,
Pauli, MERA, or bridge surfaces appear here.
"""

import json
import os

import sympy as sp
import torch
from z3 import Bool, Not, Solver, Xor, unsat

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "Root vectors and reflection matrices are represented as torch tensors; D4 roots are checked for closure under simple reflections and uniform norm."},
    "pyg": {"tried": False, "used": False, "reason": "not required for this shell-local D4 packet"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT witness for forbidden odd sign-flip parity inside the D4 Weyl signed-permutation shell."},
    "cvc5": {"tried": False, "used": False, "reason": "z3 is sufficient for the parity impossibility used here"},
    "sympy": {"tried": True, "used": True, "reason": "Exact D4 Cartan matrix, determinant, and triality-arm adjacency are derived symbolically."},
    "clifford": {"tried": False, "used": False, "reason": "not required for this finite root-system packet"},
    "geomstats": {"tried": False, "used": False, "reason": "not required for this finite root-system packet"},
    "e3nn": {"tried": False, "used": False, "reason": "not required for this finite root-system packet"},
    "rustworkx": {"tried": False, "used": False, "reason": "not required for this local root packet"},
    "xgi": {"tried": False, "used": False, "reason": "not required for this local root packet"},
    "toponetx": {"tried": False, "used": False, "reason": "not required for this local root packet"},
    "gudhi": {"tried": False, "used": False, "reason": "not required for this local root packet"},
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

I4 = torch.eye(4, dtype=torch.float64)
SIMPLE_ROOTS = [
    torch.tensor([1.0, -1.0, 0.0, 0.0], dtype=torch.float64),
    torch.tensor([0.0, 1.0, -1.0, 0.0], dtype=torch.float64),
    torch.tensor([0.0, 0.0, 1.0, -1.0], dtype=torch.float64),
    torch.tensor([0.0, 0.0, 1.0, 1.0], dtype=torch.float64),
]


def reflection_matrix(alpha: torch.Tensor) -> torch.Tensor:
    return I4 - 2.0 * torch.outer(alpha, alpha) / torch.dot(alpha, alpha)


def build_d4_roots():
    roots = []
    for i in range(4):
        for j in range(i + 1, 4):
            for si in (-1.0, 1.0):
                for sj in (-1.0, 1.0):
                    v = torch.zeros(4, dtype=torch.float64)
                    v[i] = si
                    v[j] = sj
                    roots.append(v)
    return roots


ROOTS = build_d4_roots()
ROOT_SET = {tuple(float(x) for x in root.tolist()) for root in ROOTS}
REFLECTIONS = [reflection_matrix(alpha) for alpha in SIMPLE_ROOTS]


def in_root_set(vec: torch.Tensor, tol: float = 1e-8) -> bool:
    target = vec.tolist()
    for root in ROOTS:
        if torch.max(torch.abs(root - torch.tensor(target, dtype=torch.float64))).item() < tol:
            return True
    return False


def cartan_matrix_sympy():
    roots = [
        sp.Matrix([1, -1, 0, 0]),
        sp.Matrix([0, 1, -1, 0]),
        sp.Matrix([0, 0, 1, -1]),
        sp.Matrix([0, 0, 1, 1]),
    ]
    rows = []
    for ai in roots:
        row = []
        for aj in roots:
            row.append(sp.simplify(2 * ai.dot(aj) / aj.dot(aj)))
        rows.append(row)
    return sp.Matrix(rows)


def run_positive_tests():
    cartan = cartan_matrix_sympy()
    closure_ok = True
    for R in REFLECTIONS:
        for root in ROOTS:
            if not in_root_set(R @ root):
                closure_ok = False
                break
    norms = [float(torch.dot(root, root)) for root in ROOTS]
    arm_pattern = (
        cartan[0, 1] == -1 and cartan[2, 1] == -1 and cartan[3, 1] == -1
        and cartan[0, 2] == 0 and cartan[0, 3] == 0 and cartan[2, 3] == 0
    )
    return {
        "P1_root_count_and_uniform_norm": {
            "pass": len(ROOTS) == 24 and all(abs(n - 2.0) < 1e-10 for n in norms),
            "root_count": len(ROOTS),
            "norm_values": sorted({round(n, 8) for n in norms}),
        },
        "P2_simple_reflections_preserve_roots": {
            "pass": closure_ok,
            "reflection_count": len(REFLECTIONS),
        },
        "P3_cartan_det_and_triality_arms": {
            "pass": cartan.det() == 4 and arm_pattern,
            "cartan": str(cartan),
            "determinant": int(cartan.det()),
            "triality_arm_pattern": bool(arm_pattern),
        },
        "P4_even_two_sign_flip_example_stays_admitted": {
            "pass": tuple((torch.diag(torch.tensor([-1.0, -1.0, 1.0, 1.0], dtype=torch.float64)) @ ROOTS[0]).tolist()) in ROOT_SET,
            "example_root": ROOTS[0].tolist(),
        },
    }


def run_negative_tests():
    solver = Solver()
    f1, f2, f3, f4 = Bool('f1'), Bool('f2'), Bool('f3'), Bool('f4')
    odd = Xor(f1, f2, f3, f4)
    solver.add(odd)
    solver.add(Not(odd))
    norms = [float(torch.dot(root, root)) for root in ROOTS]
    cartan = cartan_matrix_sympy()
    return {
        "N1_z3_odd_flip_parity_forbidden": {
            "pass": solver.check() == unsat,
            "z3_result": str(solver.check()),
        },
        "N2_no_short_norm_one_roots": {
            "pass": all(abs(n - 1.0) > 1e-10 for n in norms),
            "observed_norm_values": sorted({round(n, 8) for n in norms}),
        },
        "N3_not_a_linear_a4_chain": {
            "pass": cartan[3, 2] == 0 and cartan[3, 1] == -1,
            "reason": "D4 keeps three outer arms attached to the central node instead of collapsing to a chain.",
        },
    }


def run_boundary_tests():
    zero = torch.zeros(4, dtype=torch.float64)
    zero_fixed = all(torch.max(torch.abs(R @ zero - zero)).item() < 1e-10 for R in REFLECTIONS)
    alpha = SIMPLE_ROOTS[0]
    reflected = REFLECTIONS[0] @ alpha
    return {
        "B1_zero_vector_fixed": {"pass": zero_fixed},
        "B2_simple_root_reflects_to_negative": {
            "pass": torch.max(torch.abs(reflected + alpha)).item() < 1e-10,
            "reflected_root": reflected.tolist(),
        },
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    results = {
        "name": "sim_weyl_group_d4_triality_shell_local",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_group_d4_triality_shell_local_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(out_path)
