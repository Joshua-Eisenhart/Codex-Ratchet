#!/usr/bin/env python3
"""Classical baseline: SO(3)/SO(2) = S^2 homogeneous space quotient.

Classical non-canonical Lane-B baseline for the g-structure tower program.
Verifies that the orbit of a fixed point under SO(3) is S^2, and that the
stabilizer of that point is SO(2).
"""
import json, os
import numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "cross-check orbit point tensor on unit sphere via torch.norm"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
    HAVE_TORCH = True
except ImportError:
    HAVE_TORCH = False
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def rand_so3(rng):
    A = rng.standard_normal((3, 3))
    Q, R = np.linalg.qr(A)
    Q = Q @ np.diag(np.sign(np.diag(R)))
    if np.linalg.det(Q) < 0:
        Q[:, 0] = -Q[:, 0]
    return Q


def rz(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def run_positive_tests():
    rng = np.random.default_rng(0)
    results = {}
    e3 = np.array([0.0, 0.0, 1.0])

    # orbit lives on S^2
    orbit_pts = []
    for _ in range(200):
        R = rand_so3(rng)
        p = R @ e3
        orbit_pts.append(p)
    orbit_pts = np.array(orbit_pts)
    norms = np.linalg.norm(orbit_pts, axis=1)
    results["orbit_on_unit_sphere"] = bool(np.allclose(norms, 1.0, atol=1e-10))

    if HAVE_TORCH:
        import torch
        t = torch.tensor(orbit_pts)
        results["orbit_on_unit_sphere_torch"] = bool(
            torch.allclose(torch.linalg.norm(t, dim=1), torch.ones(t.shape[0], dtype=t.dtype), atol=1e-10)
        )

    # stabilizer of e3 is SO(2): rotations about z-axis
    fix = []
    for theta in np.linspace(0, 2 * np.pi, 64):
        R = rz(theta)
        fix.append(np.allclose(R @ e3, e3, atol=1e-12))
    results["so2_stabilizer_fixes_pole"] = bool(all(fix))
    return results


def run_negative_tests():
    rng = np.random.default_rng(1)
    results = {}
    e3 = np.array([0.0, 0.0, 1.0])
    # non-SO(2) rotation about x-axis should move pole
    Rx = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0.0]])
    results["rx_moves_pole"] = bool(not np.allclose(Rx @ e3, e3, atol=1e-6))
    # non-orthogonal matrix should not preserve unit norm
    M = rng.standard_normal((3, 3))
    p = M @ e3
    results["nonortho_breaks_norm"] = bool(abs(np.linalg.norm(p) - 1.0) > 1e-6)
    return results


def run_boundary_tests():
    results = {}
    # identity is in SO(2) stabilizer
    results["identity_in_stabilizer"] = bool(np.allclose(np.eye(3) @ np.array([0, 0, 1.0]), [0, 0, 1.0]))
    # 2pi rotation = identity
    results["rz_2pi_is_identity"] = bool(np.allclose(rz(2 * np.pi), np.eye(3), atol=1e-10))
    return results


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())

    divergence_log = [
        "SO(3)/SO(2) classical baseline: no obstruction expected; classical quotient is S^2.",
        "No nonclassical admissibility probe applied here — this is Lane-B baseline only.",
    ]

    results = {
        "name": "homogeneous_space_so3_mod_so2_classical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "divergence_log": divergence_log,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "homogeneous_space_so3_mod_so2_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass={all_pass}")
    raise SystemExit(0 if all_pass else 1)
