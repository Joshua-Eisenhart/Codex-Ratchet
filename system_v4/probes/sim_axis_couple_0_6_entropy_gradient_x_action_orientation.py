#!/usr/bin/env python3
"""Axis 0 x Axis 6 pairwise coupling sim.
Axis 0 = entropy-gradient cut-state functional (I_c sign).
Axis 6 = operator-first vs terrain-first precedence (action orientation).
scope_note: see system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 0, 6).
Coupling question: does the sign of the entropy-gradient candidate depend on
action-orientation (operator-first vs terrain-first)? If orientation flips
the sign reliably, the two axes are coupled (not independent).
Exclusion language: coupling excludes the hypothesis that Axis 0's I_c sign
is invariant under Axis 6 precedence reordering.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "z3": None, "sympy": None}

import torch
TOOL_MANIFEST["pytorch"] = {"tried": True, "used": True,
    "reason": "autograd computes entropy-gradient I_c for both action orientations; sign comparison is load-bearing"}

def _rho(theta, op_first: bool):
    # 2-qubit toy state; precedence changes which factor is applied first.
    c, s = torch.cos(theta), torch.sin(theta)
    U = torch.stack([torch.stack([c, -s]), torch.stack([s, c])])
    D = torch.diag(torch.tensor([0.7, 0.3]))
    M = U @ D if op_first else D @ U
    rho = M @ M.T
    rho = rho / torch.trace(rho)
    return rho

def _Ic(rho):
    # signed entropy-gradient candidate: -tr(rho log rho) - log2
    eig = torch.linalg.eigvalsh(rho).clamp(min=1e-12)
    S = -(eig * torch.log(eig)).sum()
    return S - torch.log(torch.tensor(2.0))

def run_positive_tests():
    out = {}
    thetas = [0.3, 0.7, 1.1]
    for t in thetas:
        th = torch.tensor(t, requires_grad=True)
        Ia = _Ic(_rho(th, True))
        Ib = _Ic(_rho(th, False))
        ga = torch.autograd.grad(Ia, th, retain_graph=True)[0]
        th2 = torch.tensor(t, requires_grad=True)
        Ib2 = _Ic(_rho(th2, False))
        gb = torch.autograd.grad(Ib2, th2)[0]
        out[f"theta_{t}"] = {"grad_op_first": float(ga), "grad_terrain_first": float(gb),
                             "sign_flip": float(ga) * float(gb) < 0}
    out["coupling_detected"] = any(v["sign_flip"] for v in out.values() if isinstance(v, dict))
    return out

def run_negative_tests():
    # Negative: if we zero the rotation (theta=0) precedence shouldn't matter.
    th = torch.tensor(0.0, requires_grad=True)
    Ia = _Ic(_rho(th, True))
    th2 = torch.tensor(0.0, requires_grad=True)
    Ib = _Ic(_rho(th2, False))
    return {"trivial_theta_no_coupling": abs(float(Ia) - float(Ib)) < 1e-6}

def run_boundary_tests():
    th = torch.tensor(1e-6, requires_grad=True)
    Ia = _Ic(_rho(th, True))
    return {"near_identity_finite": bool(torch.isfinite(Ia))}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = bool(pos.get("coupling_detected")) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "axis_couple_0_6_entropy_gradient_x_action_orientation",
        "classification": "canonical",
        "scope_note": "system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 0 and 6)",
        "exclusion_claim": "coupling excludes Axis 0 I_c-sign invariance under Axis 6 precedence reordering",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis_couple_0_6_entropy_gradient_x_action_orientation_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
