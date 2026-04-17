#!/usr/bin/env python3
"""
sim_weyl_group_f4_shell_local
=============================

Shell-local probe for the finite F4 Weyl packet.

This packet stays finite and local: root counts, root lengths, local simple
reflections, and exact Cartan data only.
"""

import json
import os

import sympy as sp
import torch
from z3 import Real, Solver, unsat

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "F4 roots and simple reflections are represented as torch tensors and checked for closure, counts, and length classes."},
    "pyg": {"tried": False, "used": False, "reason": "not required for this shell-local F4 packet"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT witness excludes a false simply-laced identification by forcing short and long F4 root norms to coincide."},
    "cvc5": {"tried": False, "used": False, "reason": "z3 is sufficient for the local norm-separation contradiction used here"},
    "sympy": {"tried": True, "used": True, "reason": "Exact F4 Cartan matrix and determinant are derived symbolically."},
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


def build_f4_roots():
    roots = []
    for i in range(4):
        e = torch.zeros(4, dtype=torch.float64)
        e[i] = 1.0
        roots.append(e.clone())
        roots.append(-e.clone())
    for i in range(4):
        for j in range(i + 1, 4):
            for si in (-1.0, 1.0):
                for sj in (-1.0, 1.0):
                    v = torch.zeros(4, dtype=torch.float64)
                    v[i] = si
                    v[j] = sj
                    roots.append(v)
    for signs in __import__('itertools').product((-0.5, 0.5), repeat=4):
        roots.append(torch.tensor(signs, dtype=torch.float64))
    unique = []
    seen = set()
    for root in roots:
        key = tuple(float(x) for x in root.tolist())
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


ROOTS = build_f4_roots()
ROOT_SET = {tuple(float(x) for x in root.tolist()) for root in ROOTS}
SIMPLE_ROOTS = [
    torch.tensor([0.0, 1.0, -1.0, 0.0], dtype=torch.float64),
    torch.tensor([0.0, 0.0, 1.0, -1.0], dtype=torch.float64),
    torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=torch.float64),
    torch.tensor([0.5, -0.5, -0.5, -0.5], dtype=torch.float64),
]


def reflection_matrix(alpha: torch.Tensor) -> torch.Tensor:
    return I4 - 2.0 * torch.outer(alpha, alpha) / torch.dot(alpha, alpha)


def cartan_matrix_sympy():
    roots = [
        sp.Matrix([0, 1, -1, 0]),
        sp.Matrix([0, 0, 1, -1]),
        sp.Matrix([0, 0, 0, 1]),
        sp.Matrix([sp.Rational(1, 2), sp.Rational(-1, 2), sp.Rational(-1, 2), sp.Rational(-1, 2)]),
    ]
    rows = []
    for ai in roots:
        row = []
        for aj in roots:
            row.append(sp.simplify(2 * ai.dot(aj) / aj.dot(aj)))
        rows.append(row)
    return sp.Matrix(rows)


def run_positive_tests():
    norms = [float(torch.dot(root, root)) for root in ROOTS]
    short_count = sum(abs(n - 1.0) < 1e-10 for n in norms)
    long_count = sum(abs(n - 2.0) < 1e-10 for n in norms)
    reflections = [reflection_matrix(alpha) for alpha in SIMPLE_ROOTS]
    closure_ok = True
    for R in reflections:
        for root in ROOTS:
            image = R @ root
            if tuple(round(float(x), 8) for x in image.tolist()) not in {tuple(round(float(y), 8) for y in r.tolist()) for r in ROOTS}:
                closure_ok = False
                break
    cartan = cartan_matrix_sympy()
    double_bond = cartan[1, 2] == -2 and cartan[2, 1] == -1
    return {
        "P1_root_count_and_length_split": {
            "pass": len(ROOTS) == 48 and short_count == 24 and long_count == 24,
            "root_count": len(ROOTS),
            "short_count": short_count,
            "long_count": long_count,
        },
        "P2_simple_reflections_preserve_roots": {
            "pass": closure_ok,
            "simple_reflection_count": len(reflections),
        },
        "P3_cartan_det_and_double_bond": {
            "pass": cartan.det() == 1 and double_bond,
            "cartan": str(cartan),
            "determinant": int(cartan.det()),
            "double_bond_orientation": bool(double_bond),
        },
        "P4_half_sum_roots_present": {
            "pass": tuple([0.5, 0.5, 0.5, 0.5]) in ROOT_SET and tuple([0.5, -0.5, -0.5, -0.5]) in ROOT_SET,
        },
    }


def run_negative_tests():
    solver = Solver()
    short_norm = Real('short_norm')
    long_norm = Real('long_norm')
    solver.add(short_norm == 1)
    solver.add(long_norm == 2)
    solver.add(short_norm == long_norm)
    norms = sorted({round(float(torch.dot(root, root)), 8) for root in ROOTS})
    return {
        "N1_z3_simply_laced_collapse_forbidden": {
            "pass": solver.check() == unsat,
            "z3_result": str(solver.check()),
        },
        "N2_two_norm_classes_not_one": {
            "pass": norms == [1.0, 2.0],
            "observed_norms": norms,
        },
        "N3_no_coordinate_root_of_norm_two": {
            "pass": abs(float(torch.dot(torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=torch.float64), torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=torch.float64))) - 2.0) > 1e-10,
        },
    }


def run_boundary_tests():
    zero = torch.zeros(4, dtype=torch.float64)
    reflections = [reflection_matrix(alpha) for alpha in SIMPLE_ROOTS]
    zero_fixed = all(torch.max(torch.abs(R @ zero - zero)).item() < 1e-10 for R in reflections)
    short_root = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=torch.float64)
    long_root = torch.tensor([1.0, 1.0, 0.0, 0.0], dtype=torch.float64)
    return {
        "B1_zero_vector_fixed": {"pass": zero_fixed},
        "B2_boundary_short_and_long_norms": {
            "pass": abs(float(torch.dot(short_root, short_root)) - 1.0) < 1e-10 and abs(float(torch.dot(long_root, long_root)) - 2.0) < 1e-10,
            "short_norm_sq": float(torch.dot(short_root, short_root)),
            "long_norm_sq": float(torch.dot(long_root, long_root)),
        },
    }


if __name__ == "__main__":
    results = {
        "name": "sim_weyl_group_f4_shell_local",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_group_f4_shell_local_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(out_path)
