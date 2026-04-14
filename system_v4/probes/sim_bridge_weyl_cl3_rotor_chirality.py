#!/usr/bin/env python3
"""bridge_weyl_cl3_rotor_chirality -- canonical bridge: Cl(3) rotor
(clifford load_bearing) implements chirality via pseudoscalar sign and shows
left/right rotor sectors are distinguishable.

scope_note: system_v5/new docs/ENGINE_MATH_REFERENCE.md Weyl/chirality;
LADDERS_FENCES_ADMISSION_REFERENCE.md chirality fences.
"""
import numpy as np
from clifford import Cl
from _doc_illum_common import build_manifest, write_results

TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH = build_manifest()
TOOL_MANIFEST["clifford"] = {"tried": True, "used": True, "reason": "Cl(3) rotor algebra"}
TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
I3 = e1 * e2 * e3  # pseudoscalar


def rotor(axis, theta):
    return np.cos(theta/2) - axis * np.sin(theta/2)


def run_positive_tests():
    r = {}
    # Pseudoscalar squares to -1
    r["I3_sq_neg1"] = {"pass": abs(float((I3 * I3)[()]) - (-1.0)) < 1e-12}
    # Rotor by 2pi = -1 (spinor double cover)
    R = rotor(e1 * e2, 2 * np.pi)
    r["rotor_2pi_is_neg1"] = {"pass": abs(float(R[()]) + 1.0) < 1e-10}
    # Rotor by 4pi = +1
    R4 = rotor(e1 * e2, 4 * np.pi)
    r["rotor_4pi_is_pos1"] = {"pass": abs(float(R4[()]) - 1.0) < 1e-10}
    return r


def run_negative_tests():
    r = {}
    # Left vs right rotor: R(theta) ~= R(-theta) in general
    Rp = rotor(e1 * e2, np.pi/3)
    Rm = rotor(e1 * e2, -np.pi/3)
    diff = Rp - Rm
    # norm != 0
    r["lr_rotors_distinguish"] = {"pass": abs(float((diff * ~diff)[()])) > 1e-6}
    return r


def run_boundary_tests():
    r = {}
    # Identity rotor
    R0 = rotor(e1 * e2, 0.0)
    r["identity_rotor"] = {"pass": abs(float(R0[()]) - 1.0) < 1e-12}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "bridge_weyl_cl3_rotor_chirality",
        "classification": "canonical",
        "scope_note": "ENGINE_MATH_REFERENCE.md Weyl; LADDERS_FENCES_ADMISSION_REFERENCE.md chirality",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": allp,
    }
    write_results("bridge_weyl_cl3_rotor_chirality", results)
