#!/usr/bin/env python3
"""classical_weyl_lr_extraction_projector -- classical numpy projectors
P_L = (I - gamma5)/2, P_R = (I + gamma5)/2 on a Dirac 4-spinor basis.

scope_note: system_v5/new docs/ENGINE_MATH_REFERENCE.md, section "Weyl
projection / chirality"; LADDERS_FENCES_ADMISSION_REFERENCE.md chirality fences.
Classical baseline; Cl(3) rotor bridge is the canonical one.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH = build_manifest()
TOOL_MANIFEST["numpy"] = {"tried": True, "used": True, "reason": "projector matmul"}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

# Chiral (Weyl) basis: gamma5 = diag(-I, +I)
g5 = np.diag([-1, -1, 1, 1]).astype(complex)
I4 = np.eye(4, dtype=complex)
PL = 0.5 * (I4 - g5)
PR = 0.5 * (I4 + g5)


def run_positive_tests():
    r = {}
    r["PL_idem"] = {"pass": np.allclose(PL @ PL, PL)}
    r["PR_idem"] = {"pass": np.allclose(PR @ PR, PR)}
    r["sum_identity"] = {"pass": np.allclose(PL + PR, I4)}
    psi_L = np.array([1, 0, 0, 0], dtype=complex)
    r["left_extracts"] = {"pass": np.allclose(PL @ psi_L, psi_L) and np.allclose(PR @ psi_L, 0)}
    return r


def run_negative_tests():
    r = {}
    r["PL_PR_orthogonal"] = {"pass": np.allclose(PL @ PR, 0)}
    psi_R = np.array([0, 0, 1, 0], dtype=complex)
    r["right_not_left"] = {"pass": not np.allclose(PL @ psi_R, psi_R)}
    return r


def run_boundary_tests():
    r = {}
    psi = np.array([0.5, 0.5, 0.5, 0.5], dtype=complex)
    reconstructed = PL @ psi + PR @ psi
    r["decomposition_reconstructs"] = {"pass": np.allclose(reconstructed, psi)}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "classical_weyl_lr_extraction_projector",
        "classification": "classical_baseline",
        "scope_note": "ENGINE_MATH_REFERENCE.md Weyl projection; LADDERS_FENCES_ADMISSION_REFERENCE.md chirality",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": allp,
    }
    write_results("classical_weyl_lr_extraction_projector", results)
