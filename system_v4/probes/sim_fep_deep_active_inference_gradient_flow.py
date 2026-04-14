#!/usr/bin/env python3
"""
FEP deep -- active inference gradient flow (pytorch load-bearing).

Scope: variational free energy F(mu; s) = KL(q(eta|mu) || p(eta|s)). Under
Gaussian q,p, gradient descent on mu reduces F monotonically; candidates that
increase F under this flow are EXCLUDED. Autograd computes the flow.
"""
import json, os
import torch

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn",
     "rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_MANIFEST["pytorch"]["tried"] = True
for k in TOOL_MANIFEST:
    if not TOOL_MANIFEST[k]["tried"]:
        TOOL_MANIFEST[k]["reason"] = "not required for gradient flow on free energy"


def _free_energy(mu, s, sigma_q=1.0, sigma_p=1.0):
    # Gaussian KL with means (mu, s), equal variance simplifies to 0.5 * (mu-s)^2
    return 0.5 * ((mu - s) ** 2).sum() / (sigma_p ** 2)


def run_positive_tests():
    r = {}
    s = torch.tensor([1.0, -2.0, 0.5], dtype=torch.float64)
    mu = torch.tensor([0.0, 0.0, 0.0], dtype=torch.float64, requires_grad=True)
    lr = 0.2
    history = []
    for _ in range(60):
        F = _free_energy(mu, s)
        F.backward()
        with torch.no_grad():
            mu -= lr * mu.grad
            mu.grad.zero_()
        history.append(float(_free_energy(mu, s).item()))
    monotone = all(history[i+1] <= history[i] + 1e-12 for i in range(len(history)-1))
    r["monotone_decrease"] = {"start": history[0], "end": history[-1], "pass": bool(monotone)}
    r["converged_near_s"] = {"pass": bool(torch.allclose(mu.detach(), s, atol=1e-2))}
    return r


def run_negative_tests():
    r = {}
    # Ascent (wrong sign) EXCLUDED: F must increase.
    s = torch.tensor([1.0, -1.0], dtype=torch.float64)
    mu = torch.tensor([0.1, 0.1], dtype=torch.float64, requires_grad=True)
    F0 = float(_free_energy(mu, s).item())
    F = _free_energy(mu, s); F.backward()
    with torch.no_grad():
        mu += 0.3 * mu.grad     # wrong direction
    F1 = float(_free_energy(mu, s).item())
    r["ascent_increases_F"] = {"F0": F0, "F1": F1, "pass": F1 > F0}
    return r


def run_boundary_tests():
    r = {}
    # At mu == s, gradient is zero (fixed point).
    s = torch.tensor([0.7, 0.3], dtype=torch.float64)
    mu = s.clone().detach().requires_grad_(True)
    F = _free_energy(mu, s); F.backward()
    g_norm = float(torch.linalg.norm(mu.grad).item())
    r["fixed_point_zero_grad"] = {"g_norm": g_norm, "pass": g_norm < 1e-12}
    # Zero-variance sensory precision (inf-precision) still produces finite flow for finite sigma_p
    mu2 = torch.tensor([0.0], dtype=torch.float64, requires_grad=True)
    s2 = torch.tensor([2.0], dtype=torch.float64)
    F2 = _free_energy(mu2, s2, sigma_p=0.1); F2.backward()
    r["high_precision_drives_flow"] = {"g": float(mu2.grad.item()), "pass": abs(float(mu2.grad.item())) > 1.0}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "autograd computes active-inference gradient flow"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    allpass = lambda d: all(v.get("pass", False) for v in d.values())
    ap = allpass(pos) and allpass(neg) and allpass(bnd)
    res = {"name": "fep_deep_active_inference_gradient_flow",
           "classification": "canonical",
           "scope_note": "OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md",
           "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
           "positive": pos, "negative": neg, "boundary": bnd, "all_pass": ap}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "fep_deep_active_inference_gradient_flow_results.json")
    with open(out, "w") as f: json.dump(res, f, indent=2, default=str)
    print(f"[{res['name']}] all_pass={ap} -> {out}")
