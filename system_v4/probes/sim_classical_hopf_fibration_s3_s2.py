#!/usr/bin/env python3
"""classical_hopf_fibration_s3_s2 -- classical numpy Hopf map
h: S^3 -> S^2, (z1,z2) |-> (2 Re z1 z2*, 2 Im z1 z2*, |z1|^2-|z2|^2).

scope_note: system_v5/new docs/ENGINE_MATH_REFERENCE.md, section "Hopf
fibration / U(1) equivariance"; LADDERS_FENCES_ADMISSION_REFERENCE.md
fibration fences. Classical baseline; e3nn bridge is canonical.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH = build_manifest()
TOOL_MANIFEST["numpy"] = {"tried": True, "used": True, "reason": "hopf map"}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


def hopf(z1, z2):
    x = 2 * (z1 * np.conj(z2)).real
    y = 2 * (z1 * np.conj(z2)).imag
    z = (abs(z1) ** 2 - abs(z2) ** 2)
    return np.array([x, y, z])


def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    passes = []
    for _ in range(50):
        z1 = rng.normal() + 1j * rng.normal()
        z2 = rng.normal() + 1j * rng.normal()
        n = np.sqrt(abs(z1)**2 + abs(z2)**2)
        z1 /= n; z2 /= n
        p = hopf(z1, z2)
        passes.append(abs(np.linalg.norm(p) - 1.0) < 1e-9)
    r["s3_to_s2"] = {"pass": all(passes), "n": len(passes)}
    return r


def run_negative_tests():
    r = {}
    # Non-normalized S^3 input should NOT produce unit S^2 output
    p = hopf(2.0 + 0j, 0 + 0j)  # |z1|^2-|z2|^2 = 4, norm=4
    r["non_unit_input_not_unit"] = {"pass": abs(np.linalg.norm(p) - 1.0) > 0.1}
    return r


def run_boundary_tests():
    r = {}
    # U(1) equivariance: multiplying (z1,z2) by e^{i phi} leaves h invariant
    z1 = (1/np.sqrt(2)) + 0j; z2 = 0 + (1/np.sqrt(2))*1j
    p1 = hopf(z1, z2)
    phi = 1.234
    p2 = hopf(z1 * np.exp(1j*phi), z2 * np.exp(1j*phi))
    r["u1_invariance"] = {"pass": np.allclose(p1, p2, atol=1e-10)}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "classical_hopf_fibration_s3_s2",
        "classification": "classical_baseline",
        "scope_note": "ENGINE_MATH_REFERENCE.md Hopf fibration; LADDERS_FENCES_ADMISSION_REFERENCE.md fibration",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": allp,
    }
    write_results("classical_hopf_fibration_s3_s2", results)
