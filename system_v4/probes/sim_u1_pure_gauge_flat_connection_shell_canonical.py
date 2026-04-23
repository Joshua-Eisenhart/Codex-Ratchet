#!/usr/bin/env python3
"""
Canonical shell-local U(1) pure-gauge flat-connection probe.

QED-style shell-local claim: on one plaquette, an exact U(1) edge assignment pulled back
from vertex phases has zero local curl, while a perturbed non-exact assignment does not.
"""

import json
import math
import os

import numpy as np

classification = "canonical"
NAME = "sim_u1_pure_gauge_flat_connection_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "tensor numerics are not needed for one-plaquette exactness"},
    "pyg": {"tried": False, "used": False, "reason": "message passing is not needed for one plaquette flatness"},
    "z3": {"tried": False, "used": False, "reason": "topological incidence already witnesses exactness on the local plaquette"},
    "cvc5": {"tried": False, "used": False, "reason": "direct cochain algebra suffices for this shell-local flatness test"},
    "sympy": {"tried": False, "used": False, "reason": "sympy symbolically checks the local d^2=0 identity behind exact U(1) edge data"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for a scalar plaquette connection"},
    "geomstats": {"tried": False, "used": False, "reason": "manifold geodesics are not needed for one-plaquette exactness"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are outside this local gauge patch"},
    "rustworkx": {"tried": False, "used": False, "reason": "graph-only tooling is secondary to the cell-complex witness here"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraphs are not needed for one-plaquette U(1) flatness"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx provides the load-bearing incidence operators for shell-local exactness and curl"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology is not needed for the exact-vs-non-exact local curl check"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

for _name, _importer in [
    ("pytorch", lambda: __import__("torch")),
    ("pyg", lambda: __import__("torch_geometric")),
    ("z3", lambda: __import__("z3")),
    ("cvc5", lambda: __import__("cvc5")),
    ("clifford", lambda: __import__("clifford")),
    ("geomstats", lambda: __import__("geomstats")),
    ("e3nn", lambda: __import__("e3nn")),
    ("rustworkx", lambda: __import__("rustworkx")),
    ("xgi", lambda: __import__("xgi")),
    ("gudhi", lambda: __import__("gudhi")),
]:
    try:
        _importer()
        TOOL_MANIFEST[_name]["tried"] = True
    except Exception as exc:
        TOOL_MANIFEST[_name]["reason"] = f"not installed: {exc}"

from toponetx.classes import CellComplex
TOOL_MANIFEST["toponetx"]["tried"] = True

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def square_cell_complex(with_face: bool = True):
    cc = CellComplex()
    for edge in ([0, 1], [1, 2], [2, 3], [3, 0]):
        cc.add_cell(edge, rank=1)
    if with_face:
        cc.add_cell([0, 1, 2, 3], rank=2)
    return cc


def local_operators():
    cc = square_cell_complex(with_face=True)
    b1 = np.asarray(cc.incidence_matrix(1).todense(), dtype=float)
    b2 = np.asarray(cc.incidence_matrix(2).todense(), dtype=float)
    return b1, b2


def exact_edge_assignment(vertex_phases):
    b1, _ = local_operators()
    return b1.T @ np.asarray(vertex_phases, dtype=float)


def plaquette_curl(edge_assignment):
    _, b2 = local_operators()
    return float(np.asarray(edge_assignment, dtype=float) @ b2[:, 0])


def run_positive_tests():
    edge_assignment = exact_edge_assignment([0.0, 0.4, 1.0, 1.5])
    b1, b2 = local_operators()
    results = {
        "incidence_composition_zero": {"pass": bool(np.allclose(b1 @ b2, 0.0, atol=1e-10))},
        "exact_assignment_has_zero_local_curl": {"curl": plaquette_curl(edge_assignment), "pass": bool(abs(plaquette_curl(edge_assignment)) < 1e-10)},
    }
    TOOL_MANIFEST["toponetx"]["used"] = True
    if sp is not None:
        g0, g1, g2, g3 = sp.symbols("g0 g1 g2 g3", real=True)
        exact_sum = (g1 - g0) + (g2 - g1) + (g3 - g2) + (g0 - g3)
        results["sympy_exact_one_form_closes"] = {"pass": bool(sp.simplify(exact_sum) == 0)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_exact_one_form_closes"] = {"pass": False, "reason": "sympy unavailable"}
    return results


def run_negative_tests():
    exact_assignment = exact_edge_assignment([0.0, 0.4, 1.0, 1.5])
    perturbed = exact_assignment.copy()
    perturbed[0] += math.pi / 7.0
    return {
        "perturbed_edge_assignment_not_flat": {"curl": plaquette_curl(perturbed), "pass": bool(abs(plaquette_curl(perturbed)) > 1e-6)},
        "non_exact_assignment_differs_from_exact_shell": {"pass": bool(np.linalg.norm(perturbed - exact_assignment) > 1e-6)},
    }


def run_boundary_tests():
    zero_assignment = exact_edge_assignment([0.0, 0.0, 0.0, 0.0])
    periodic_assignment = exact_edge_assignment([0.0, 2.0 * math.pi, 2.0 * math.pi, 2.0 * math.pi])
    return {
        "constant_vertex_phase_has_zero_edges": {"pass": bool(np.allclose(zero_assignment, 0.0, atol=1e-10))},
        "two_pi_vertex_shift_stays_flat": {"curl": plaquette_curl(periodic_assignment), "pass": bool(abs(plaquette_curl(periodic_assignment)) < 1e-10)},
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local QED-style one-plaquette pure gauge exactness and flatness",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "passes_local_rerun": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, RESULTS_BASENAME)
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"{NAME}: {'PASS' if all_pass else 'FAIL'} -> {out_path}")
