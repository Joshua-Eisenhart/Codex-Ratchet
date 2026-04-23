#!/usr/bin/env python3
"""bridge_axis0_gradient_autograd -- canonical bridge: compute Axis 0 entropy
gradient via pytorch autograd (load_bearing). Cross-checks classical FD baseline.

scope_note: system_v5/docs/AXIS_AND_ENTROPY_REFERENCE.md, Axis 0 gradient;
CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md entropy definition.
"""
import numpy as np
import torch
from _doc_illum_common import build_manifest, write_results

classification = "classical_baseline"
TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}
TM = TOOL_MANIFEST
DEPTH = TOOL_INTEGRATION_DEPTH


def grad_autograd(p_np):
    p = torch.tensor(p_np, dtype=torch.float64, requires_grad=True)
    S = -(p * torch.log(p.clamp_min(1e-15))).sum()
    S.backward()
    return p.grad.detach().numpy()


def run_positive_tests():
    r = {}
    p = np.array([0.25, 0.25, 0.25, 0.25])
    g = grad_autograd(p)
    expected = -(np.log(0.25) + 1.0)
    r["uniform_matches_analytic"] = {"pass": np.allclose(g, expected, atol=1e-8), "g": g.tolist()}
    # Cross-check vs FD
    def S(p):
        p = np.clip(p, 1e-15, 1); return float(-(p * np.log(p)).sum())
    eps = 1e-6
    g_fd = np.array([(S(p + eps*np.eye(4)[i]) - S(p - eps*np.eye(4)[i]))/(2*eps) for i in range(4)])
    r["autograd_matches_FD"] = {"pass": np.allclose(g, g_fd, atol=1e-4)}
    return r


def run_negative_tests():
    r = {}
    p = np.array([0.1, 0.2, 0.3, 0.4])
    g = grad_autograd(p)
    r["nonuniform_not_constant"] = {"pass": not np.allclose(g, g[0], atol=1e-4)}
    return r


def run_boundary_tests():
    r = {}
    p = np.array([0.98, 0.01, 0.01])
    g = grad_autograd(p)
    r["near_degenerate_finite"] = {"pass": bool(np.all(np.isfinite(g)))}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    TM["pytorch"] = {"tried": True, "used": True, "reason": "autograd dS/dp"}
    DEPTH["pytorch"] = "load_bearing"
    results = {
        "name": "bridge_axis0_gradient_autograd",
        "classification": classification,
        "scope_note": "AXIS_AND_ENTROPY_REFERENCE.md Axis 0; CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md entropy",
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": allp,
    }
    write_results("bridge_axis0_gradient_autograd", results)
