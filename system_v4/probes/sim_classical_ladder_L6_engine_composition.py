#!/usr/bin/env python3
"""classical_ladder_L6_engine_composition -- classical numpy composition
of unitary engine operators testing non-commutativity and closure.

scope_note: system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md L6
engine composition; ENGINE_MATH_REFERENCE.md 4-operator engine.
Classical baseline.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH = build_manifest()
TOOL_MANIFEST["numpy"] = {"tried": True, "used": True, "reason": "matrix composition"}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

X = np.array([[0,1],[1,0]], complex)
Y = np.array([[0,-1j],[1j,0]], complex)
Z = np.array([[1,0],[0,-1]], complex)
I2 = np.eye(2, dtype=complex)


def run_positive_tests():
    r = {}
    # XY = iZ (engine composition identity)
    r["XY_eq_iZ"] = {"pass": np.allclose(X @ Y, 1j * Z)}
    # Unitarity preserved under composition
    U = X @ Y @ Z
    r["composition_unitary"] = {"pass": np.allclose(U @ U.conj().T, I2)}
    return r


def run_negative_tests():
    r = {}
    # Non-commutativity: XY != YX
    r["noncommute"] = {"pass": not np.allclose(X @ Y, Y @ X)}
    return r


def run_boundary_tests():
    r = {}
    # Identity element: IX = X
    r["identity_ok"] = {"pass": np.allclose(I2 @ X, X)}
    # Involution: X^2 = I
    r["X_involution"] = {"pass": np.allclose(X @ X, I2)}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "classical_ladder_L6_engine_composition",
        "classification": "classical_baseline",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md L6; ENGINE_MATH_REFERENCE.md 4-operator",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": allp,
    }
    write_results("classical_ladder_L6_engine_composition", results)
