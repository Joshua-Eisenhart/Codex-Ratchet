#!/usr/bin/env python3
"""
sim_gerbe_carrier_cell_complex -- Family #3 Gerbes, lego 1/6.

Carrier = a 2D cell complex (triangulated S^2-like nerve) built with
toponetx.CellComplex. Gerbes are (higher) U(1)-bundles supported on
2-cells, so we must first verify the cell complex has a consistent
incidence: every 2-cell boundary is a closed 1-chain.
"""
import json, os
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "numpy":    {"tried": True, "used": True, "reason": "boundary matrix arithmetic"},
    "toponetx": {"tried": False,"used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "toponetx": "load_bearing"}

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"].update(tried=True, used=True,
        reason="CellComplex construction + incidence matrices for gerbe carrier")
except Exception as e:
    TOOL_MANIFEST["toponetx"]["reason"] = f"unavailable: {e}"


def build_tetra_complex():
    cc = CellComplex()
    faces = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    for f in faces:
        cc.add_cell(list(f), rank=2)
    return cc


def run_positive_tests():
    r = {}
    cc = build_tetra_complex()
    r["num_0_cells"] = len(cc.nodes)
    r["num_2_cells"] = len(cc.cells)
    # boundary of boundary = 0 (chain complex property prerequisite for gerbes)
    B1 = cc.incidence_matrix(1).toarray()
    B2 = cc.incidence_matrix(2).toarray()
    r["dd_zero"] = bool(np.allclose(B1 @ B2, 0))
    r["tetra_has_4_vertices"] = bool(len(cc.nodes) == 4)
    r["tetra_has_4_triangles"] = bool(len(cc.cells) == 4)
    return r


def run_negative_tests():
    r = {}
    cc = CellComplex()
    cc.add_cell([0, 1, 2], rank=2)
    B1 = cc.incidence_matrix(1).toarray()
    B2 = cc.incidence_matrix(2).toarray()
    # single triangle still satisfies dd=0, but has only one 2-cell -> no gerbe glueing
    r["single_triangle_insufficient_for_gluing"] = bool(len(cc.cells) == 1)
    r["single_triangle_dd_zero"] = bool(np.allclose(B1 @ B2, 0))
    # empty complex has no 2-cells -> no gerbe carrier
    empty = CellComplex()
    r["empty_complex_has_no_2cells"] = bool(len(empty.cells) == 0)
    return r


def run_boundary_tests():
    r = {}
    cc = build_tetra_complex()
    # Euler characteristic V - E + F of closed surface carrier
    V = len(cc.nodes); E = len(cc.edges); F = len(cc.cells)
    euler = V - E + F
    r["tetra_euler_characteristic"] = int(euler)
    r["tetra_euler_is_2"] = bool(euler == 2)  # tetra = S^2
    return r


if __name__ == "__main__":
    results = {
        "name": "gerbe_carrier_cell_complex",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gerbe_carrier_cell_complex_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(json.dumps({k: results[k] for k in ("positive", "negative", "boundary")},
                     indent=2, default=str))
