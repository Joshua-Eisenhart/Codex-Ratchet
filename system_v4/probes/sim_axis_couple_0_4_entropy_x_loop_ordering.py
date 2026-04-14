#!/usr/bin/env python3
"""Axis 0 x Axis 4 coupling: entropy gradient x loop-order family (UEUE vs EUEU).
scope_note: system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 0, 4).
Exclusion: coupling excludes entropy-gradient invariance under loop-order permutation.
"""
import json, os, torch

TOOL_MANIFEST = {"pytorch": {"tried": True, "used": True,
    "reason": "autograd entropy gradient compared across UEUE vs EUEU op sequences; load-bearing"}}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing"}

def U_op(t):
    return torch.stack([torch.stack([torch.cos(t), -torch.sin(t)]),
                        torch.stack([torch.sin(t),  torch.cos(t)])])

def E_op(t):
    # asymmetric damping on two channels (dephasing-like, non-unitary)
    return torch.diag(torch.stack([1.0 + 0.5*torch.sin(t), 1.0 - 0.3*torch.sin(t)]))

def seq_state(ops, rho0):
    r = rho0
    for M in ops:
        r = M @ r @ M.T
    return r / torch.trace(r)

def S(rho):
    eig = torch.linalg.eigvalsh(rho).clamp(min=1e-12)
    return -(eig * eig.log()).sum()

def run_positive_tests():
    rho0 = torch.diag(torch.tensor([0.7, 0.3]))
    t = torch.tensor(0.5, requires_grad=True)
    u, e = U_op(t*1.3), E_op(t*0.7)
    s_uv = S(seq_state([u, e, u, e], rho0))
    g1 = torch.autograd.grad(s_uv, t, retain_graph=True)[0]
    t2 = torch.tensor(0.5, requires_grad=True)
    u2, e2 = U_op(t2*1.3), E_op(t2*0.7)
    s_ev = S(seq_state([e2, u2, e2, u2], rho0))
    g2 = torch.autograd.grad(s_ev, t2)[0]
    return {"grad_UEUE": float(g1), "grad_EUEU": float(g2),
            "coupling_detected": abs(float(g1) - float(g2)) > 1e-4}

def run_negative_tests():
    # At t=0 both sequences reduce to identity composition: gradient should
    # still exist, but grad_UEUE == grad_EUEU (no order dependence at origin).
    rho0 = torch.diag(torch.tensor([0.7, 0.3]))
    t = torch.tensor(0.0, requires_grad=True)
    u, e = U_op(t*1.3), E_op(t*0.7)
    s1 = S(seq_state([u, e, u, e], rho0))
    g1 = torch.autograd.grad(s1, t, retain_graph=True)[0]
    t2 = torch.tensor(0.0, requires_grad=True)
    u2, e2 = U_op(t2*1.3), E_op(t2*0.7)
    s2 = S(seq_state([e2, u2, e2, u2], rho0))
    g2 = torch.autograd.grad(s2, t2)[0]
    return {"t_zero_orders_agree": abs(float(g1) - float(g2)) < 1e-6}

def run_boundary_tests():
    rho0 = torch.diag(torch.tensor([0.7, 0.3]))
    t = torch.tensor(1e-6, requires_grad=True)
    return {"near_zero_finite": bool(torch.isfinite(S(seq_state([U_op(t)], rho0))))}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = bool(pos["coupling_detected"]) and all(neg.values()) and all(bnd.values())
    results = {"name": "axis_couple_0_4_entropy_x_loop_ordering",
               "classification": "canonical",
               "scope_note": "system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md (Axes 0, 4)",
               "exclusion_claim": "coupling excludes Axis 0 gradient invariance under Axis 4 loop-order permutation",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "axis_couple_0_4_entropy_x_loop_ordering_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {p}")
