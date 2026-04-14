#!/usr/bin/env python3
"""classical_axis0_entropy_gradient -- classical baseline numpy finite-difference
gradient of constraint-admissibility entropy S(p) = -sum p log p.

scope_note: system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md, section "Axis 0 /
entropy gradient"; cross-check CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md section
"Shannon / admissibility entropy". Classical baseline only; not a claim about
nonclassical I_c -- candidate admissibility probe, not a theorem.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH = build_manifest()
TOOL_MANIFEST["numpy"] = {"tried": True, "used": True, "reason": "fd gradient + entropy"}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


def S(p):
    p = np.clip(p, 1e-15, 1.0)
    return float(-(p * np.log(p)).sum())


def grad_fd(p, eps=1e-6):
    g = np.zeros_like(p)
    for i in range(len(p)):
        e = np.zeros_like(p); e[i] = eps
        g[i] = (S(p + e) - S(p - e)) / (2 * eps)
    return g


def run_positive_tests():
    r = {}
    p = np.array([0.25, 0.25, 0.25, 0.25])
    g = grad_fd(p)
    # analytic: dS/dp_i = -(log p_i + 1); at uniform = -(log 0.25 + 1)
    expected = -(np.log(0.25) + 1.0)
    ok = np.allclose(g, expected, atol=1e-3)
    r["uniform_grad"] = {"pass": bool(ok), "g": g.tolist(), "expected": expected}
    return r


def run_negative_tests():
    r = {}
    p = np.array([0.1, 0.2, 0.3, 0.4])
    g = grad_fd(p)
    # non-uniform: gradient must NOT be constant
    ok = not np.allclose(g, g[0], atol=1e-3)
    r["nonuniform_not_constant"] = {"pass": bool(ok), "g": g.tolist()}
    return r


def run_boundary_tests():
    r = {}
    p = np.array([0.99, 0.005, 0.005])
    g = grad_fd(p)
    ok = np.all(np.isfinite(g))
    r["near_degenerate_finite"] = {"pass": bool(ok), "g": g.tolist()}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "classical_axis0_entropy_gradient",
        "classification": "classical_baseline",
        "scope_note": "AXIS_AND_ENTROPY_REFERENCE.md Axis 0; CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md Shannon",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": allp,
    }
    write_results("classical_axis0_entropy_gradient", results)
