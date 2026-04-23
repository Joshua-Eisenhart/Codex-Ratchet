#!/usr/bin/env python3
"""
Canonical shell-local flux-boundary orientation probe.

Shell-local flux-candidate claim: on one plaquette, reversing the boundary orientation flips
signed circulation while preserving its magnitude; an open chain admits no such face witness.
"""

import json
import os

import numpy as np

classification = "canonical"
NAME = "sim_flux_boundary_orientation_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "tensor numerics are not needed for one-plaquette orientation signs"},
    "pyg": {"tried": False, "used": False, "reason": "message passing is not needed for one plaquette boundary orientation"},
    "z3": {"tried": False, "used": False, "reason": "incidence orientation already witnesses the local sign behavior"},
    "cvc5": {"tried": False, "used": False, "reason": "direct oriented-boundary algebra suffices for this shell-local flux candidate"},
    "sympy": {"tried": False, "used": False, "reason": "symbolic algebra is not required once the oriented boundary vectors are explicit"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for one-plaquette circulation signs"},
    "geomstats": {"tried": False, "used": False, "reason": "manifold geodesics are not needed for one-cell orientation reversal"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are outside this local flux-candidate lane"},
    "rustworkx": {"tried": False, "used": False, "reason": "graph-only tooling is secondary to the oriented cell-complex witness here"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraphs are not needed for one-plaquette boundary orientation"},
    "toponetx": {"tried": False, "used": False, "reason": "toponetx provides the load-bearing oriented boundary vector for the shell-local plaquette witness"},
    "gudhi": {"tried": False, "used": False, "reason": "gudhi supports the boundary-cycle witness that the local plaquette closes"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["gudhi"] = "supportive"

for _name, _importer in [
    ("pytorch", lambda: __import__("torch")),
    ("pyg", lambda: __import__("torch_geometric")),
    ("z3", lambda: __import__("z3")),
    ("cvc5", lambda: __import__("cvc5")),
    ("sympy", lambda: __import__("sympy")),
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


def square_cell_complex(with_face: bool = True):
    cc = CellComplex()
    for edge in ([0, 1], [1, 2], [2, 3], [3, 0]):
        cc.add_cell(edge, rank=1)
    if with_face:
        cc.add_cell([0, 1, 2, 3], rank=2)
    return cc


def boundary_vector():
    cc = square_cell_complex(with_face=True)
    return np.asarray(cc.incidence_matrix(2).todense(), dtype=float)[:, 0]


def signed_circulation(flux_sector: float, orientation: int):
    b = boundary_vector()
    edge_cochain = flux_sector * b
    return float(edge_cochain @ (orientation * b))


def run_positive_tests():
    b = boundary_vector()
    st = gudhi.SimplexTree()
    for vertex in range(4):
        st.insert([vertex], filtration=0.0)
    for edge in ([0, 1], [1, 2], [2, 3], [0, 3]):
        st.insert(edge, filtration=0.0)
    st.persistence(persistence_dim_max=True)
    forward = signed_circulation(1.0, +1)
    reverse = signed_circulation(1.0, -1)
    results = {
        "boundary_cycle_is_present": {"betti": st.betti_numbers(), "pass": bool(st.betti_numbers() == [1, 1])},
        "orientation_reversal_flips_signed_circulation": {"forward": forward, "reverse": reverse, "pass": bool(abs(forward + reverse) < 1e-10)},
        "orientation_reversal_preserves_magnitude": {"pass": bool(abs(abs(forward) - abs(reverse)) < 1e-10 and np.linalg.norm(b) > 0.0)},
    }
    TOOL_MANIFEST["toponetx"]["used"] = True
    TOOL_MANIFEST["gudhi"]["used"] = True
    return results


def run_negative_tests():
    open_cc = square_cell_complex(with_face=False)
    forward = signed_circulation(1.0, +1)
    return {
        "open_chain_has_no_face_witness": {"pass": bool(open_cc.shape[2] == 0)},
        "same_orientation_does_not_flip_sign": {"pass": bool(abs(forward + forward) > 1e-6)},
    }


def run_boundary_tests():
    zero_forward = signed_circulation(0.0, +1)
    zero_reverse = signed_circulation(0.0, -1)
    unit_forward = signed_circulation(1.0, +1)
    return {
        "zero_flux_sector_is_zero_in_both_orientations": {"pass": bool(abs(zero_forward) < 1e-10 and abs(zero_reverse) < 1e-10)},
        "unit_flux_sector_is_nontrivial": {"pass": bool(abs(unit_forward) > 1e-10)},
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local flux-candidate orientation on one plaquette boundary",
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
