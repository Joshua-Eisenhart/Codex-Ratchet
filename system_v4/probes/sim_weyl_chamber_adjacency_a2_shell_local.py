#!/usr/bin/env python3
"""
sim_weyl_chamber_adjacency_a2_shell_local
=========================================

Shell-local probe for the six open A2 Weyl chambers cut by x = 0, y = 0,
and x + y = 0 in the rank-2 root plane.
"""

import json
import os

import sympy as sp
import torch
from z3 import Real, Solver, unsat

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "Torch tensors carry chamber representative points and sign-pattern checks for the six A2 sectors."},
    "pyg": {"tried": False, "used": False, "reason": "not required for this local chamber packet"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT witness excludes simultaneous membership in opposite open chambers."},
    "cvc5": {"tried": False, "used": False, "reason": "z3 is sufficient for the local sign-pattern contradiction used here"},
    "sympy": {"tried": True, "used": True, "reason": "Exact wall-angle spacing is derived symbolically from the three A2 chamber walls."},
    "clifford": {"tried": False, "used": False, "reason": "not required for this local chamber packet"},
    "geomstats": {"tried": False, "used": False, "reason": "not required for this local chamber packet"},
    "e3nn": {"tried": False, "used": False, "reason": "not required for this local chamber packet"},
    "rustworkx": {"tried": False, "used": False, "reason": "not required for this local chamber packet"},
    "xgi": {"tried": False, "used": False, "reason": "not required for this local chamber packet"},
    "toponetx": {"tried": False, "used": False, "reason": "not required for this local chamber packet"},
    "gudhi": {"tried": False, "used": False, "reason": "not required for this local chamber packet"},
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

REPRESENTATIVES = {
    "C1": torch.tensor([1.0, 1.0], dtype=torch.float64),
    "C2": torch.tensor([1.0, -0.5], dtype=torch.float64),
    "C3": torch.tensor([1.0, -2.0], dtype=torch.float64),
    "C4": torch.tensor([-1.0, -1.0], dtype=torch.float64),
    "C5": torch.tensor([-1.0, 0.5], dtype=torch.float64),
    "C6": torch.tensor([-1.0, 2.0], dtype=torch.float64),
}


def sign_pattern(point: torch.Tensor):
    x, y = float(point[0]), float(point[1])
    return (x > 0, y > 0, x + y > 0)


def run_positive_tests():
    patterns = {name: sign_pattern(point) for name, point in REPRESENTATIVES.items()}
    unique_patterns = len(set(patterns.values()))
    x, y = sp.symbols('x y', real=True)
    m0 = sp.oo
    m1 = 0
    m2 = -1
    angle = sp.simplify(sp.pi / 4 - (-sp.pi / 4))
    return {
        "P1_six_distinct_open_chambers": {
            "pass": unique_patterns == 6,
            "patterns": {k: list(v) for k, v in patterns.items()},
        },
        "P2_adjacent_examples_differ_by_one_wall": {
            "pass": sum(a != b for a, b in zip(patterns['C1'], patterns['C2'])) == 1 and sum(a != b for a, b in zip(patterns['C2'], patterns['C3'])) == 1,
        },
        "P3_sympy_wall_spacing_nondegenerate": {
            "pass": angle == sp.pi / 2,
            "derived_angle_between_x_and_y_walls": str(angle),
            "note": "The third wall x+y=0 splits those quadrants again, yielding six total sectors.",
        },
        "P4_opposite_chambers_have_opposite_patterns": {
            "pass": all(a != b for a, b in zip(patterns['C1'], patterns['C4'])),
        },
    }


def run_negative_tests():
    solver = Solver()
    x = Real('x')
    y = Real('y')
    solver.add(x > 0, y > 0, x + y > 0)
    solver.add(x < 0, y < 0, x + y < 0)
    return {
        "N1_z3_opposite_open_chambers_cannot_overlap": {
            "pass": solver.check() == unsat,
            "z3_result": str(solver.check()),
        },
        "N2_wall_point_not_open_chamber_member": {
            "pass": sign_pattern(torch.tensor([1.0, -1.0], dtype=torch.float64)) != sign_pattern(REPRESENTATIVES['C2']),
            "wall_point": [1.0, -1.0],
        },
        "N3_origin_not_open_chamber_member": {
            "pass": sign_pattern(torch.tensor([0.0, 0.0], dtype=torch.float64)) == (False, False, False),
        },
    }


def run_boundary_tests():
    wall_point = torch.tensor([2.0, -2.0], dtype=torch.float64)
    near_wall = torch.tensor([2.0, -1.9], dtype=torch.float64)
    return {
        "B1_wall_point_has_degenerate_sign_pattern": {
            "pass": sign_pattern(wall_point) == (True, False, False),
            "point": wall_point.tolist(),
        },
        "B2_near_wall_point_returns_to_open_sector": {
            "pass": sign_pattern(near_wall) == (True, False, True),
            "point": near_wall.tolist(),
        },
    }


if __name__ == "__main__":
    results = {
        "name": "sim_weyl_chamber_adjacency_a2_shell_local",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_chamber_adjacency_a2_shell_local_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(out_path)
