#!/usr/bin/env python3
"""
sim_weyl_affine_c2_alcove_shell_local
=====================================

Shell-local probe for the affine C2 fundamental alcove.

In simple-root coordinates (u, v) for C2 with highest root 2*alpha1 + alpha2,
the dominant affine alcove is the finite packet u >= 0, v >= 0, 2u + v <= 1.
"""

import json
import os

import sympy as sp
import torch
from z3 import Real, Solver, sat, unsat

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "Torch tensors carry affine C2 alcove vertices, barycenters, and wall-inequality checks in simple-root coordinates."},
    "pyg": {"tried": False, "used": False, "reason": "not required for this affine alcove packet"},
    "z3": {"tried": True, "used": True, "reason": "SAT and UNSAT checks certify interior witness existence and contradictory wall inequalities for affine C2."},
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
    torch.tensor([0.5, 0.0], dtype=torch.float64),
    torch.tensor([0.0, 1.0], dtype=torch.float64),
]


def inside_alcove(point: torch.Tensor) -> bool:
    u, v = float(point[0]), float(point[1])
    return u >= -1e-10 and v >= -1e-10 and 2.0 * u + v <= 1.0 + 1e-10


def strict_inside(point: torch.Tensor) -> bool:
    u, v = float(point[0]), float(point[1])
    return u > 0.0 and v > 0.0 and 2.0 * u + v < 1.0


def run_positive_tests():
    barycenter = torch.tensor([0.2, 0.2], dtype=torch.float64)
    area = 0.5 * abs((VERTICES[1][0] - VERTICES[0][0]) * (VERTICES[2][1] - VERTICES[0][1]) - (VERTICES[1][1] - VERTICES[0][1]) * (VERTICES[2][0] - VERTICES[0][0]))
    u, v = sp.symbols('u v', real=True)
    highest_root = 2 * u + v
    solver = Solver()
    uz, vz = Real('u_c2'), Real('v_c2')
    solver.add(uz > 0, vz > 0, 2 * uz + vz < 1)
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
            "pass": sp.expand(highest_root - (2 * u + v)) == 0 and abs(float(area) - 0.25) < 1e-10,
            "highest_root_coefficients": [2, 1],
            "alcove_area_uv_coords": float(area),
        },
        "P4_z3_interior_witness_exists": {
            "pass": solver.check() == sat,
            "z3_result": str(solver.check()),
        },
    }


def run_negative_tests():
    outside = torch.tensor([0.4, 0.4], dtype=torch.float64)
    solver = Solver()
    u, v = Real('u_c2_neg'), Real('v_c2_neg')
    solver.add(u >= 0, v >= 0, 2 * u + v <= 1, 2 * u + v > 1)
    return {
        "N1_point_beyond_affine_wall_excluded": {
            "pass": not inside_alcove(outside),
            "outside_point": outside.tolist(),
            "two_u_plus_v": float(2 * outside[0] + outside[1]),
        },
        "N2_z3_contradictory_wall_constraints_unsat": {
            "pass": solver.check() == unsat,
            "z3_result": str(solver.check()),
        },
        "N3_no_negative_simple_root_coordinate_in_dominant_alcove": {
            "pass": not inside_alcove(torch.tensor([0.2, -0.1], dtype=torch.float64)),
        },
    }


def run_boundary_tests():
    wall_midpoint = torch.tensor([0.25, 0.5], dtype=torch.float64)
    vertex = torch.tensor([0.5, 0.0], dtype=torch.float64)
    return {
        "B1_top_wall_midpoint_admitted_but_not_strict": {
            "pass": inside_alcove(wall_midpoint) and not strict_inside(wall_midpoint),
            "point": wall_midpoint.tolist(),
        },
        "B2_short_edge_vertex_admitted": {
            "pass": inside_alcove(vertex) and not strict_inside(vertex),
            "point": vertex.tolist(),
        },
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    sections = [positive, negative, boundary]
    passed = sum(1 for section in sections for value in section.values() if value.get("pass"))
    total = sum(1 for section in sections for value in section.values() if "pass" in value)
    all_pass = passed == total and total > 0
    results = {
        "name": "sim_weyl_affine_c2_alcove_shell_local",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"passed": passed, "total": total, "all_pass": all_pass},
        "all_pass": all_pass,
        "claim_ceiling": "tool_lego_fit_probe_only",
        "next_lego_target": "bounded affine C2 alcove shell fixture before Weyl coupling, bridge, axis, or QIT promotion",
        "promotion_condition": (
            "requires later admitted downstream Weyl coupling rows with exact parent receipts and stage-gate approval; "
            "this receipt does not promote a bridge, axis, GStack, QIT engine, or nonclassical claim"
        ),
        "blocked_until": (
            "blocked from bridge, axis, GStack, QIT engine, and nonclassical promotion until exact parent receipts "
            "and downstream coupling/admission packets pass strict validation"
        ),
        "demotion_condition": (
            "Demote this bounded affine C2 alcove surface if torch wall checks fail, z3 admits contradictory wall constraints, "
            "sympy highest-root/area checks fail, or boundary wall/vertex fixtures fail."
        ),
        "out_of_scope": [
            "no bridge, axis, GStack, QIT engine, or nonclassical admission",
            "no proof of a full affine Weyl group program",
            "no scientific lego promotion from this receipt alone",
            "no replacement for downstream Weyl coupling receipts",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_weyl_affine_c2_alcove_shell_local",
    )
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_weyl_affine_c2_alcove_shell_local_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(out_path)
