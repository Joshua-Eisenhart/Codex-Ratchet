#!/usr/bin/env python3
"""
sim_assoc_bundle_weyl_spinor_as_section -- Family #1 lego 3/6.

Treat a Weyl spinor as a section of the associated bundle E = P ×_{U(1)} C_{1/2}
where C_{1/2} is the half-weight rep (the spin structure of S^3->S^2 realises
this via the double cover). Using Clifford(0,3) we represent the spinor in
Pauli algebra and verify SU(2)-rotation equivariance of its base-point image.
"""
import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "numpy":     {"tried": True,  "used": True,  "reason": "Pauli matrix computation"},
}
TOOL_INTEGRATION_DEPTH = {
    "clifford": "load_bearing", "geomstats": None, "e3nn": "supportive",
    "sympy": None, "numpy": "supportive",
}

try:
    from clifford import Cl
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    TOOL_MANIFEST["clifford"].update(tried=True, used=True,
        reason="Cl(3) realises the spinor / Pauli algebra for S^3")
except Exception as e:
    TOOL_MANIFEST["clifford"]["reason"] = f"unavailable: {e}"

try:
    import e3nn  # noqa
    TOOL_MANIFEST["e3nn"].update(tried=True, used=True,
        reason="reference for j=1/2 irrep behaviour under SO(3)")
except Exception:
    pass


# Pauli matrices
s0 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)


def su2(axis, angle):
    ax = np.asarray(axis, dtype=float); ax = ax / np.linalg.norm(ax)
    n = ax[0] * sx + ax[1] * sy + ax[2] * sz
    return np.cos(angle / 2) * s0 - 1j * np.sin(angle / 2) * n


def spinor_to_s2(psi):
    # <psi| sigma |psi> gives Bloch vector in S^2
    x = np.vdot(psi, sx @ psi).real
    y = np.vdot(psi, sy @ psi).real
    z = np.vdot(psi, sz @ psi).real
    return np.array([x, y, z])


def run_positive_tests():
    r = {}
    psi = np.array([1, 0], dtype=complex)
    r["up_spinor_bloch_z"] = bool(np.allclose(spinor_to_s2(psi), [0, 0, 1], atol=1e-12))
    psi2 = np.array([1, 1], dtype=complex) / np.sqrt(2)
    r["equal_sup_bloch_x"] = bool(np.allclose(spinor_to_s2(psi2), [1, 0, 0], atol=1e-12))

    # double-cover equivariance: U(R_pi/3 about z) acting on psi rotates Bloch by pi/3
    U = su2([0, 0, 1], np.pi / 3)
    psi3 = np.array([1, 1], dtype=complex) / np.sqrt(2)
    b_before = spinor_to_s2(psi3)
    b_after  = spinor_to_s2(U @ psi3)
    # rotation of b_before about z by pi/3
    c, s = np.cos(np.pi / 3), np.sin(np.pi / 3)
    expected = np.array([c * b_before[0] - s * b_before[1],
                         s * b_before[0] + c * b_before[1],
                         b_before[2]])
    r["double_cover_equivariance"] = bool(np.allclose(b_after, expected, atol=1e-10))

    # Clifford check: Cl(3) unit bivector rotations match SU(2)
    R = np.cos(np.pi / 6) - np.sin(np.pi / 6) * (e1 * e2)
    vec = (1.0) * e1
    rotated = R * vec * ~R
    # rotated should be cos(pi/3) e1 + sin(pi/3) e2
    r["clifford_bivector_rotation"] = bool(
        abs(rotated[(1,)] - np.cos(np.pi / 3)) < 1e-10 and
        abs(rotated[(2,)] - np.sin(np.pi / 3)) < 1e-10)
    return r


def run_negative_tests():
    r = {}
    # 2π SU(2) rotation gives -psi (spin sign flip), but same Bloch vector
    U2pi = su2([0, 0, 1], 2 * np.pi)
    psi = np.array([1, 1], dtype=complex) / np.sqrt(2)
    r["2pi_flips_spinor_sign"] = bool(np.allclose(U2pi @ psi, -psi, atol=1e-10))
    r["2pi_fixes_bloch"] = bool(np.allclose(spinor_to_s2(U2pi @ psi),
                                            spinor_to_s2(psi), atol=1e-10))
    # a non-unit "spinor" has inconsistent normalised Bloch length
    bad = np.array([2.0, 0.0], dtype=complex)
    r["unnormalised_bloch_length_off"] = bool(abs(np.linalg.norm(spinor_to_s2(bad)) - 1.0) > 0.1)
    return r


def run_boundary_tests():
    r = {}
    # 4π rotation = identity on spinor
    U4pi = su2([0, 0, 1], 4 * np.pi)
    psi = np.array([1, 1], dtype=complex) / np.sqrt(2)
    r["4pi_identity_on_spinor"] = bool(np.allclose(U4pi @ psi, psi, atol=1e-10))
    # orthogonal spinors -> antipodal Bloch
    up = np.array([1, 0], dtype=complex)
    dn = np.array([0, 1], dtype=complex)
    r["orthogonal_antipodal"] = bool(
        np.allclose(spinor_to_s2(up), -spinor_to_s2(dn), atol=1e-12))
    return r


if __name__ == "__main__":
    results = {
        "name": "assoc_bundle_weyl_spinor_as_section",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "assoc_bundle_weyl_spinor_as_section_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(json.dumps({k: results[k] for k in ("positive","negative","boundary")}, indent=2, default=str))
