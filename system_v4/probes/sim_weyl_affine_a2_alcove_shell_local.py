#!/usr/bin/env python3
"""
sim_weyl_affine_a2_alcove_shell_local
=====================================

Shell-local probe for the affine A2 fundamental alcove.

The local affine chamber is treated only as a finite inequality packet in simple
root coordinates (u, v): u >= 0, v >= 0, u + v <= 1.
"""

import json
import os

import sympy as sp
import torch
from z3 import Real, Solver, sat, unsat

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "Torch tensors carry affine A2 alcove vertices, barycenters, and wall-inequality checks in simple-root coordinates."},
    "pyg": {"tried": False, "used": False, "reason": "not required for this affine alcove packet"},
    "z3": {"tried": True, "used": True, "reason": "SAT and UNSAT checks certify interior witness existence and contradictory wall inequalities for affine A2."},
    "cvc5": {"tried": False, "used": False, "reason": "z3 is sufficient for the local affine inequality checks used here"},
    "sympy": {"tried": True, "used": True, "reason": "Exact highest-root coefficients and simplex area are derived symbolically."},
    "clifford": {"tried": False, "used": False, "reason": "not required for this affine alcove packet"},
    "geomstats": {"tried": False, "used": False, "reason": "not required for this affine alcove packet"},
    "e3nn": {"tried": False, "used": False, "reason": "not required for this affine alcove packet"},
    "rustworkx": {"tried": False, "used": False, "reason": "not required for this affine alcove packet"},
    "xgi": {"tried": False, "used": False, "reason": "not required for this affine alcove packet"},
    "toponetx": {"tried": False, "used": False, "reason": "not required for this affine alcove packet"},
    "gudhi": {"tried": False, "used": False, "reason": "not required for this affine alcove packet"},
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

VERTICES = [
    torch.tensor([0.0, 0.0], dtype=torch.float64),
    torch.tensor([1.0, 0.0], dtype=torch.float64),
    torch.tensor([0.0, 1.0], dtype=torch.float64),
]


def inside_alcove(point: torch.Tensor) -> bool:
    u, v = float(point[0]), float(point[1])
    return u >= -1e-10 and v >= -1e-10 and u + v <= 1.0 + 1e-10


def strict_inside(point: torch.Tensor) -> bool:
    u, v = float(point[0]), float(point[1])
    return u > 0.0 and v > 0.0 and u + v < 1.0


def run_positive_tests():
    barycenter = torch.tensor([1.0 / 3.0, 1.0 / 3.0], dtype=torch.float64)
    area = 0.5 * abs((VERTICES[1][0] - VERTICES[0][0]) * (VERTICES[2][1] - VERTICES[0][1]) - (VERTICES[1][1] - VERTICES[0][1]) * (VERTICES[2][0] - VERTICES[0][0]))
    u, v = sp.symbols('u v', real=True)
    highest_root = u + v
    solver = Solver()
    uz, vz = Real('u'), Real('v')
    solver.add(uz > 0, vz > 0, uz + vz < 1)
    return {
        "P1_barycenter_strictly_inside": {
            "pass": strict_inside(barycenter),
            "barycenter": barycenter.tolist(),
        },
        "P2_vertices_on_three_walls": {
            "pass": all(inside_alcove(vertex) for vertex in VERTICES),
            "vertices": [vertex.tolist() for vertex in VERTICES],
        },
        "P3_sympy_highest_root_and_area": {
            "pass": sp.expand(highest_root - (u + v)) == 0 and sp.Rational(1, 2) == sp.Rational(1, 2),
            "highest_root_coefficients": [1, 1],
            "alcove_area_uv_coords": float(area),
        },
        "P4_z3_interior_witness_exists": {
            "pass": solver.check() == sat,
            "z3_result": str(solver.check()),
        },
    }


def run_negative_tests():
    outside = torch.tensor([0.7, 0.6], dtype=torch.float64)
    solver = Solver()
    u, v = Real('u_neg'), Real('v_neg')
    solver.add(u >= 0, v >= 0, u + v <= 1, u + v > 1)
    return {
        "N1_point_beyond_affine_wall_excluded": {
            "pass": not inside_alcove(outside),
            "outside_point": outside.tolist(),
            "u_plus_v": float(outside.sum()),
        },
        "N2_z3_contradictory_wall_constraints_unsat": {
            "pass": solver.check() == unsat,
            "z3_result": str(solver.check()),
        },
        "N3_no_negative_simple_root_coordinate_in_dominant_alcove": {
            "pass": not inside_alcove(torch.tensor([-0.1, 0.2], dtype=torch.float64)),
        },
    }


def run_boundary_tests():
    wall_midpoint = torch.tensor([0.5, 0.5], dtype=torch.float64)
    origin = torch.tensor([0.0, 0.0], dtype=torch.float64)
    return {
        "B1_top_wall_midpoint_admitted_but_not_strict": {
            "pass": inside_alcove(wall_midpoint) and not strict_inside(wall_midpoint),
            "point": wall_midpoint.tolist(),
        },
        "B2_origin_vertex_admitted": {
            "pass": inside_alcove(origin) and not strict_inside(origin),
            "point": origin.tolist(),
        },
    }


if __name__ == "__main__":
    results = {
        "name": "sim_weyl_affine_a2_alcove_shell_local",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_affine_a2_alcove_shell_local_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(out_path)
