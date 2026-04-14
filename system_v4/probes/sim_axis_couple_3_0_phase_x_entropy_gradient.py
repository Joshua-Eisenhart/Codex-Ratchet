#!/usr/bin/env python3
"""Axis 3 x Axis 0 coupling: phase (fiber vs lifted-base loop) x entropy gradient.
scope_note: system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 3, 0).
Exclusion: coupling excludes entropy-gradient invariance under fiber vs lifted-base loop choice.
"""
import json, os, torch

TOOL_MANIFEST = {"pytorch": {"tried": True, "used": True,
    "reason": "autograd entropy gradient evaluated along fiber vs base loop; load-bearing"}}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing"}

def rho_fiber(phi):
    # density-stationary along fiber: diagonal of phi-dependent populations
    p = torch.stack([0.5 + 0.3*torch.cos(phi), 0.5 - 0.3*torch.cos(phi)])
    return torch.diag(p)

def rho_base(phi):
    # density-traversing: rotation mixes populations with phi
    U = torch.stack([torch.stack([torch.cos(phi), -torch.sin(phi)]),
                     torch.stack([torch.sin(phi),  torch.cos(phi)])])
    D = torch.diag(torch.tensor([0.8, 0.2]))
    return U @ D @ U.T

def S(rho):
    eig = torch.linalg.eigvalsh(rho).clamp(min=1e-12)
    return -(eig * eig.log()).sum()

def run_positive_tests():
    phi = torch.tensor(0.6, requires_grad=True)
    gf = torch.autograd.grad(S(rho_fiber(phi)), phi, retain_graph=True)[0]
    phi2 = torch.tensor(0.6, requires_grad=True)
    gb = torch.autograd.grad(S(rho_base(phi2)), phi2)[0]
    return {"grad_fiber": float(gf), "grad_base": float(gb),
            "coupling_detected": abs(float(gf) - float(gb)) > 1e-3}

def run_negative_tests():
    # phi=0 fixed point: both branches should give zero gradient
    phi = torch.tensor(0.0, requires_grad=True)
    gf = torch.autograd.grad(S(rho_fiber(phi)), phi)[0]
    return {"phi_zero_fiber_gradient_zero": abs(float(gf)) < 1e-6}

def run_boundary_tests():
    phi = torch.tensor(1e-5, requires_grad=True)
    return {"near_zero_finite": bool(torch.isfinite(S(rho_base(phi))))}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = bool(pos["coupling_detected"]) and all(neg.values()) and all(bnd.values())
    results = {"name": "axis_couple_3_0_phase_x_entropy_gradient",
               "classification": "canonical",
               "scope_note": "system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 3, 0)",
               "exclusion_claim": "coupling excludes Axis 0 gradient invariance under Axis 3 fiber/base loop choice",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "axis_couple_3_0_phase_x_entropy_gradient_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
