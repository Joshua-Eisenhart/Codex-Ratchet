#!/usr/bin/env python3
"""classical_constraint_manifold_layers_nested -- classical numpy test that
nested constraint layers (L0 ⊃ L1 ⊃ L2) produce monotonically smaller admissible
state sets.

scope_note: system_v5/new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md,
section "Constraint manifold / layer nesting"; LADDERS_FENCES_ADMISSION_REFERENCE.md
admission ladder. Classical baseline.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH = build_manifest()
TOOL_MANIFEST["numpy"] = {"tried": True, "used": True, "reason": "set admissibility"}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


def sample_states(n=2000, seed=0):
    rng = np.random.default_rng(seed)
    pts = rng.normal(size=(n, 3))
    return pts / np.linalg.norm(pts, axis=1, keepdims=True)  # S^2


def L0(pts):  # nothing excluded
    return np.ones(len(pts), bool)


def L1(pts):  # northern hemisphere
    return pts[:, 2] >= 0


def L2(pts):  # north cap pi/4
    return pts[:, 2] >= np.cos(np.pi / 4)


def run_positive_tests():
    r = {}
    pts = sample_states()
    a0, a1, a2 = L0(pts).sum(), L1(pts).sum(), L2(pts).sum()
    r["monotone_nesting"] = {"pass": bool(a0 >= a1 >= a2), "counts": [int(a0), int(a1), int(a2)]}
    r["strict_shrink"] = {"pass": bool(a0 > a1 > a2)}
    return r


def run_negative_tests():
    r = {}
    # L2 admits must be subset of L1 admits
    pts = sample_states()
    m1, m2 = L1(pts), L2(pts)
    r["L2_subset_L1"] = {"pass": bool(np.all(m2 <= m1))}
    return r


def run_boundary_tests():
    r = {}
    # empty input
    pts = np.zeros((0, 3))
    r["empty_safe"] = {"pass": L0(pts).sum() == 0}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "classical_constraint_manifold_layers_nested",
        "classification": "classical_baseline",
        "scope_note": "CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md layer nesting; LADDERS_FENCES_ADMISSION_REFERENCE.md",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": allp,
    }
    write_results("classical_constraint_manifold_layers_nested", results)
