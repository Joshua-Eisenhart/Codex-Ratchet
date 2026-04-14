#!/usr/bin/env python3
"""
sim_three_rotor_so3_composition_triple_classical.py

Step 3 classical baseline: three SO(3) rotations R1, R2, R3 composition
and conjugation cycle closure. Checks:
  (R1 R2 R3)(R1 R2 R3)^T = I   (orthogonality preserved)
  det(R1 R2 R3) = 1
  conjugation cycle: R3^T R2^T R1^T (R1 R2 R3) = I
"""

import json
import os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "n/a"},
    "z3": {"tried": False, "used": False, "reason": "n/a"},
    "cvc5": {"tried": False, "used": False, "reason": "n/a"},
    "sympy": {"tried": False, "used": False, "reason": "n/a"},
    "clifford": {"tried": False, "used": False, "reason": "no rotor algebra used"},
    "geomstats": {"tried": False, "used": False, "reason": "n/a"},
    "e3nn": {"tried": False, "used": False, "reason": "n/a"},
    "rustworkx": {"tried": False, "used": False, "reason": "n/a"},
    "xgi": {"tried": False, "used": False, "reason": "n/a"},
    "toponetx": {"tried": False, "used": False, "reason": "n/a"},
    "gudhi": {"tried": False, "used": False, "reason": "n/a"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "tensor det cross-check"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def rot_axis_angle(axis, theta):
    a = axis / np.linalg.norm(axis)
    K = np.array([[0, -a[2], a[1]],
                  [a[2], 0, -a[0]],
                  [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(theta)*K + (1-np.cos(theta))*(K @ K)


def run_positive_tests():
    results = {}
    rng = np.random.default_rng(5)
    ok = True
    for _ in range(16):
        R1 = rot_axis_angle(rng.normal(size=3), rng.uniform(0, np.pi))
        R2 = rot_axis_angle(rng.normal(size=3), rng.uniform(0, np.pi))
        R3 = rot_axis_angle(rng.normal(size=3), rng.uniform(0, np.pi))
        R = R1 @ R2 @ R3
        ortho = np.max(np.abs(R @ R.T - np.eye(3)))
        det = np.linalg.det(R)
        cycle = np.max(np.abs(R3.T @ R2.T @ R1.T @ R - np.eye(3)))
        if not (ortho < 1e-10 and abs(det - 1) < 1e-10 and cycle < 1e-10):
            ok = False

    if TOOL_MANIFEST["pytorch"]["used"]:
        import torch
        t = torch.tensor(R)
        results["torch_det"] = float(torch.linalg.det(t))

    results["so3_triple_closure"] = ok
    return results


def run_negative_tests():
    results = {}
    # A non-orthogonal matrix in the chain breaks closure
    R1 = rot_axis_angle(np.array([1.0, 0, 0]), 0.3)
    R2 = np.array([[2.0, 0, 0], [0, 1, 0], [0, 0, 1]])  # not in SO(3)
    R3 = rot_axis_angle(np.array([0, 1.0, 0]), 0.5)
    R = R1 @ R2 @ R3
    results["nonorthogonal_breaks_closure"] = bool(
        np.max(np.abs(R @ R.T - np.eye(3))) > 1e-3
    )
    return results


def run_boundary_tests():
    results = {}
    # Identity triple
    I = np.eye(3)
    R = I @ I @ I
    results["identity_triple_is_identity"] = bool(np.max(np.abs(R - I)) < 1e-14)
    # Angle = 2pi full rotations return identity
    R = rot_axis_angle(np.array([0, 0, 1.0]), 2*np.pi)
    results["full_rotation_identity"] = bool(np.max(np.abs(R - I)) < 1e-10)
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        pos.get("so3_triple_closure", False)
        and neg.get("nonorthogonal_breaks_closure", False)
        and bnd.get("identity_triple_is_identity", False)
        and bnd.get("full_rotation_identity", False)
    )
    divergence_log = [
        "classical SO(3) triple composition loses the Spin(3)=SU(2) double cover -- nonclassical triple-nesting requires +/- sign tracking across the cycle",
        "no holonomy / Berry phase from nested rotor coupling is visible at SO(3) level",
        "operator ordering treated as free; nonclassical program needs noncommuting constraint-ordering as load-bearing",
    ]
    results = {
        "name": "three_rotor_so3_composition_triple_classical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "divergence_log": divergence_log,
        "summary": {"all_pass": bool(all_pass)},
        "all_pass": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "three_rotor_so3_composition_triple_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
