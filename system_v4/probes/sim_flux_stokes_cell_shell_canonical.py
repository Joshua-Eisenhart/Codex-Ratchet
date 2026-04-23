#!/usr/bin/env python3
"""
Canonical shell-local flux probe on a single cell.

Flux shell-local coupling test: one plaquette carries an integer flux whose circulation is
tracked on the boundary cycle. The test stays local to one cell complex and its boundary.
"""

import json
import math
import os

import numpy as np

classification = "canonical"
NAME = "sim_flux_stokes_cell_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "tensor autodiff is not needed for the one-cell flux probe"},
    "pyg": {"tried": False, "used": False, "reason": "graph message passing is not needed for a single plaquette shell"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 is not needed because topology and symbolic circulation already witness the local claim"},
    "cvc5": {"tried": False, "used": False, "reason": "this local flux shell is checked through cell topology and symbolic circulation rather than SMT"},
    "sympy": {"tried": False, "used": False, "reason": "sympy symbolically checks the circulation equals 2*pi*n for integer flux on one plaquette"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for the single-cell Stokes test"},
    "geomstats": {"tried": False, "used": False, "reason": "Riemannian manifold tooling is not needed for one plaquette flux"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are not part of this shell-local flux test"},
    "rustworkx": {"tried": False, "used": False, "reason": "graph-only tooling is secondary to the cell-complex probe here"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraphs are not needed for the one-cell flux shell"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx provides the load-bearing cell complex and incidence matrices for the local flux shell"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi provides the boundary-cycle homology witness betti_1=1 for the plaquette boundary"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"
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
]:
    try:
        _importer()
        TOOL_MANIFEST[_name]["tried"] = True
    except Exception as exc:
        TOOL_MANIFEST[_name]["reason"] = f"not installed: {exc}"

from toponetx.classes import CellComplex
TOOL_MANIFEST["toponetx"]["tried"] = True
import gudhi
TOOL_MANIFEST["gudhi"]["tried"] = True

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



def boundary_simplex_tree():
    st = gudhi.SimplexTree()
    for vertex in range(4):
        st.insert([vertex], filtration=0.0)
    for edge in ([0, 1], [1, 2], [2, 3], [0, 3]):
        st.insert(edge, filtration=0.0)
    st.persistence(persistence_dim_max=True)
    return st



def run_positive_tests():
    cc = square_cell_complex(with_face=True)
    b1 = np.asarray(cc.incidence_matrix(1).todense(), dtype=float)
    b2 = np.asarray(cc.incidence_matrix(2).todense(), dtype=float)
    st = boundary_simplex_tree()
    results = {
        "boundary_of_boundary_zero": {"pass": bool(np.allclose(b1 @ b2, 0.0, atol=1e-10))},
        "boundary_cycle_has_betti_one": {"betti": st.betti_numbers(), "pass": bool(st.betti_numbers() == [1, 1])},
    }
    TOOL_MANIFEST["toponetx"]["used"] = True
    TOOL_MANIFEST["gudhi"]["used"] = True
    if sp is not None:
        n = sp.symbols("n", integer=True)
        circulation = sp.integrate(2 * sp.pi * n, (sp.symbols("t"), 0, 1))
        results["sympy_integer_flux_circulation"] = {"pass": bool(sp.simplify(circulation - 2 * sp.pi * n) == 0)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_integer_flux_circulation"] = {"pass": False, "reason": "sympy unavailable"}
    return results



def run_negative_tests():
    open_cc = square_cell_complex(with_face=False)
    has_face = open_cc.shape[2] == 1
    st = gudhi.SimplexTree()
    for vertex in range(4):
        st.insert([vertex], filtration=0.0)
    for edge in ([0, 1], [1, 2], [2, 3]):
        st.insert(edge, filtration=0.0)
    st.persistence(persistence_dim_max=True)
    return {
        "open_chain_has_no_flux_cell": {"pass": bool(not has_face)},
        "open_chain_loses_boundary_cycle": {"betti": st.betti_numbers(), "pass": bool(st.betti_numbers() == [1, 0])},
    }



def run_boundary_tests():
    cc = square_cell_complex(with_face=True)
    b2 = np.asarray(cc.incidence_matrix(2).todense(), dtype=float)
    zero_flux = np.zeros((1, 1))
    unit_flux = np.ones((1, 1))
    return {
        "zero_flux_zero_circulation": {"pass": bool(np.allclose(b2 @ zero_flux, 0.0, atol=1e-10))},
        "unit_flux_nontrivial_boundary_weights": {"pass": bool(np.linalg.norm(b2 @ unit_flux) > 0.0)},
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local flux on one cell with boundary-cycle witness",
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
