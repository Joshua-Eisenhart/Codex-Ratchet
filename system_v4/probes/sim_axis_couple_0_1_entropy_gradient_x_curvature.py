#!/usr/bin/env python3
"""Axis 0 x Axis 1 coupling: entropy-gradient vs derived terrain curvature branch.
scope_note: system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 0, 1).
Exclusion: coupling excludes independence of entropy gradient from the
Se/Ni vs Ne/Si terrain branch (curvature sign).
"""
import json, os, torch

TOOL_MANIFEST = {"pytorch": {"tried": True, "used": True,
    "reason": "autograd entropy gradient evaluated on both curvature branches; decisive"}}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing"}

def _S(p):
    p = p.clamp(min=1e-12)
    return -(p * p.log()).sum()

def _branch(x, kappa):
    # kappa>0: Se/Ni concentrates; kappa<0: Ne/Si disperses
    logits = kappa * torch.stack([x, 2*x, 0.5*x*x, -x])
    return torch.softmax(logits, dim=0)

def run_positive_tests():
    out = {}
    for kappa in (1.5, -1.5):
        x = torch.tensor(0.4, requires_grad=True)
        S = _S(_branch(x, kappa))
        g = torch.autograd.grad(S, x)[0]
        out[f"kappa_{kappa}"] = float(g)
    out["branch_dependence"] = abs(out["kappa_1.5"] - out["kappa_-1.5"]) > 1e-3
    return out

def run_negative_tests():
    # kappa=0 => uniform distribution, gradient must vanish, no curvature coupling
    x = torch.tensor(0.4, requires_grad=True)
    S = _S(_branch(x, 0.0))
    g = torch.autograd.grad(S, x)[0]
    return {"flat_curvature_no_gradient": abs(float(g)) < 1e-6}

def run_boundary_tests():
    x = torch.tensor(1e-5, requires_grad=True)
    S = _S(_branch(x, 1.5))
    return {"near_zero_finite": bool(torch.isfinite(S))}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = bool(pos["branch_dependence"]) and all(neg.values()) and all(bnd.values())
    results = {"name": "axis_couple_0_1_entropy_gradient_x_curvature",
               "classification": "canonical",
               "scope_note": "system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 0, 1)",
               "exclusion_claim": "coupling excludes Axis 0 gradient independence from Axis 1 curvature branch",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "axis_couple_0_1_entropy_gradient_x_curvature_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
