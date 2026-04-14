#!/usr/bin/env python3
"""classical_ladder_L0_spectral_baseline -- classical numpy eigen-decomposition
of graph Laplacian as L0 spectral admissibility baseline.

scope_note: system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md, L0
spectral section; ENGINE_MATH_REFERENCE.md spectral operators. Classical
baseline; non-canonical geometry.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH = build_manifest()
TOOL_MANIFEST["numpy"] = {"tried": True, "used": True, "reason": "eigh"}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


def laplacian(A):
    D = np.diag(A.sum(1))
    return D - A


def run_positive_tests():
    r = {}
    # Path graph of 4 nodes, connected -> 1 zero eigenvalue
    A = np.array([[0,1,0,0],[1,0,1,0],[0,1,0,1],[0,0,1,0]], float)
    L = laplacian(A)
    w = np.linalg.eigvalsh(L)
    r["connected_one_zero"] = {"pass": int(np.sum(w < 1e-9)) == 1, "eig": w.tolist()}
    r["all_nonneg"] = {"pass": bool(np.all(w > -1e-9))}
    return r


def run_negative_tests():
    r = {}
    # Disconnected (2 components) -> 2 zero eigenvalues
    A = np.array([[0,1,0,0],[1,0,0,0],[0,0,0,1],[0,0,1,0]], float)
    L = laplacian(A)
    w = np.linalg.eigvalsh(L)
    r["disconnected_two_zeros"] = {"pass": int(np.sum(w < 1e-9)) == 2, "eig": w.tolist()}
    return r


def run_boundary_tests():
    r = {}
    # single node
    A = np.array([[0.0]])
    L = laplacian(A)
    w = np.linalg.eigvalsh(L)
    r["single_node"] = {"pass": abs(w[0]) < 1e-12}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "classical_ladder_L0_spectral_baseline",
        "classification": "classical_baseline",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md L0 spectral; ENGINE_MATH_REFERENCE.md spectral",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": allp,
    }
    write_results("classical_ladder_L0_spectral_baseline", results)
