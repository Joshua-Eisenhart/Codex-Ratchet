#!/usr/bin/env python3
"""Entropy-gradient sign under noncommuting operator precedence.

This bounded probe compares a signed entropy-gradient candidate under two
operation orders: rotation before diagonal weighting versus diagonal weighting
before rotation. If the gradient sign changes, the result shows dependence on
operator precedence. This is not a target-system claim.
"""
import json, os
import numpy as np

classification = "tool_lego_fit_probe"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "sympy": None,
    "z3": None,
}

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
        "name": "entropy_gradient_operator_precedence_sign_gap",
        "classification": classification,
        "scope_note": "bounded entropy-gradient sign comparison under two noncommuting operation orders",
        "exclusion_claim": "excludes invariance of this entropy-gradient sign under operator-precedence reordering for the tested toy family",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entropy_gradient_operator_precedence_sign_gap_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
