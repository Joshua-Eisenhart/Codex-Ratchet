#!/usr/bin/env python3
"""
Canonical shell-local U(1) structure probe via SO(2) matrices.

Structure object: U(1) realized as the shell-local rotation group SO(2).
Reduction test: reflections are excluded because det=-1 leaves the shell.
"""

import json
import math
import os

import numpy as np

classification = "canonical"
NAME = "sim_u1_structure_matrix_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "tensor autodiff is unnecessary for the matrix-structure shell test"},
    "pyg": {"tried": False, "used": False, "reason": "graph tools are not needed for the SO(2) realization of U(1)"},
    "z3": {"tried": False, "used": False, "reason": "no SMT solver is needed for the matrix-membership checks"},
    "cvc5": {"tried": False, "used": False, "reason": "matrix-group closure is verified directly rather than with SMT"},
    "sympy": {"tried": False, "used": False, "reason": "sympy symbolically confirms determinant one and angle-addition structure"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for the matrix-shell realization"},
    "geomstats": {"tried": False, "used": False, "reason": "geomstats provides the load-bearing SO(2) membership and composition operations"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are not needed for a shell-local matrix group"},
    "rustworkx": {"tried": False, "used": False, "reason": "cycle graphs are outside this matrix realization scope"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraph structure is not needed for SO(2) shell closure"},
    "toponetx": {"tried": False, "used": False, "reason": "cell complexes are not part of this matrix-only shell probe"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology is not needed for SO(2) membership"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

for _name, _importer in [
    ("pytorch", lambda: __import__("torch")),
    ("pyg", lambda: __import__("torch_geometric")),
    ("z3", lambda: __import__("z3")),
    ("cvc5", lambda: __import__("cvc5")),
    ("clifford", lambda: __import__("clifford")),
    ("e3nn", lambda: __import__("e3nn")),
    ("rustworkx", lambda: __import__("rustworkx")),
    ("xgi", lambda: __import__("xgi")),
    ("toponetx", lambda: __import__("toponetx")),
    ("gudhi", lambda: __import__("gudhi")),
]:
    try:
        _importer()
        TOOL_MANIFEST[_name]["tried"] = True
    except Exception as exc:
        TOOL_MANIFEST[_name]["reason"] = f"not installed: {exc}"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

from geomstats.geometry.special_orthogonal import SpecialOrthogonal
TOOL_MANIFEST["geomstats"]["tried"] = True

GROUP = SpecialOrthogonal(n=2, point_type="matrix")


def rotation(theta: float) -> np.ndarray:
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s], [s, c]], dtype=float)



def run_positive_tests():
    thetas = [0.0, math.pi / 6.0, math.pi / 3.0, math.pi]
    belongs = [bool(GROUP.belongs(rotation(theta))) for theta in thetas]
    compose = GROUP.compose(rotation(math.pi / 5.0), rotation(math.pi / 7.0))
    expected = rotation(math.pi / 5.0 + math.pi / 7.0)
    results = {
        "geomstats_rotation_membership": {"thetas": thetas, "belongs": belongs, "pass": bool(all(belongs))},
        "geomstats_group_composition": {"pass": bool(np.allclose(compose, expected, atol=1e-10))},
    }
    TOOL_MANIFEST["geomstats"]["used"] = True
    if sp is not None:
        theta = sp.symbols("theta", real=True)
        mat = sp.Matrix([[sp.cos(theta), -sp.sin(theta)], [sp.sin(theta), sp.cos(theta)]])
        determinant_one = sp.simplify(mat.det() - 1) == 0
        results["sympy_det_one"] = {"pass": bool(determinant_one)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_det_one"] = {"pass": False, "reason": "sympy unavailable"}
    return results



def run_negative_tests():
    reflection = np.array([[1.0, 0.0], [0.0, -1.0]])
    reflection_belongs = bool(GROUP.belongs(reflection))
    det_reflection = float(np.linalg.det(reflection))
    return {
        "reflection_excluded": {
            "determinant": det_reflection,
            "pass": bool((not reflection_belongs) and abs(det_reflection + 1.0) < 1e-10),
        },
        "nonorthogonal_matrix_excluded": {
            "pass": bool(not GROUP.belongs(np.array([[1.0, 1.0], [0.0, 1.0]]))),
        },
    }



def run_boundary_tests():
    identity = rotation(0.0)
    periodic = rotation(2.0 * math.pi)
    return {
        "identity_angle_zero": {"pass": bool(np.allclose(identity, np.eye(2), atol=1e-10))},
        "two_pi_returns_identity": {"pass": bool(np.allclose(periodic, np.eye(2), atol=1e-10))},
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local U(1) structure object via SO(2) matrices",
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
