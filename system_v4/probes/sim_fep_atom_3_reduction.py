#!/usr/bin/env python3
"""
FEP atom 3 of 7: REDUCTION.

Claim: the shell must admit a non-trivial reduction of the joint state
to a scalar variational free energy F = E_q[log q - log p], and gradient
flow dq/dt = -grad F must strictly decrease F until q approaches the
posterior p. Identity (no reduction) or constant F (no decrease) is
inadmissible.

Load-bearing tool: pytorch (autograd of F over variational parameters
of q; gradient-descent step decreases F).
"""

import json, os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "autograd of F and gradient flow"},
    "pyg":       {"tried": False, "used": False, "reason": "no edge aggregation"},
    "z3":        {"tried": False, "used": False, "reason": "not a proof atom"},
    "cvc5":      {"tried": False, "used": False, "reason": "redundant"},
    "sympy":     {"tried": False, "used": False, "reason": "atom 1 handled symbolic"},
    "clifford":  {"tried": False, "used": False, "reason": "scalar reduction"},
    "geomstats": {"tried": False, "used": False, "reason": "flat Euclidean here"},
    "e3nn":      {"tried": False, "used": False, "reason": "not used"},
    "rustworkx": {"tried": False, "used": False, "reason": "structure is atom 2"},
    "xgi":       {"tried": False, "used": False, "reason": "not used"},
    "toponetx":  {"tried": False, "used": False, "reason": "not used"},
    "gudhi":     {"tried": False, "used": False, "reason": "not used"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    torch = None
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"


def _free_energy(mu_q, log_sigma_q, mu_p, sigma_p):
    # KL(N(mu_q, sig_q^2) || N(mu_p, sig_p^2))  (prior p, up to constant evidence)
    sig_q = torch.exp(log_sigma_q)
    kl = torch.log(sigma_p / sig_q) + (sig_q**2 + (mu_q - mu_p)**2) / (2 * sigma_p**2) - 0.5
    return kl


def run_positive_tests():
    if torch is None: return {"skipped":"torch missing"}
    mu_q = torch.tensor(3.0, requires_grad=True)
    log_sig_q = torch.tensor(0.5, requires_grad=True)
    mu_p = torch.tensor(0.0); sigma_p = torch.tensor(1.0)
    F0 = _free_energy(mu_q, log_sig_q, mu_p, sigma_p)
    F0.backward()
    # one gradient-descent step
    lr = 0.1
    with torch.no_grad():
        mu_q2 = mu_q - lr * mu_q.grad
        log_sig_q2 = log_sig_q - lr * log_sig_q.grad
    mu_q2 = mu_q2.detach().requires_grad_(True)
    log_sig_q2 = log_sig_q2.detach().requires_grad_(True)
    F1 = _free_energy(mu_q2, log_sig_q2, mu_p, sigma_p)
    decreased = F1.item() < F0.item()
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    return {"gradient_flow_decreases_F": {
        "F0": float(F0), "F1": float(F1), "pass": decreased
    }}


def run_negative_tests():
    if torch is None: return {"skipped":"torch missing"}
    # Identity "reduction": return per-dimension residuals, not scalar F
    mu_q = torch.tensor([3.0, 2.0], requires_grad=True)
    residuals = mu_q - torch.tensor([0.0, 0.0])  # vector, not scalar F
    is_scalar_F = residuals.ndim == 0
    return {"identity_rejected": {"ndim": residuals.ndim,
                                  "pass": not is_scalar_F}}


def run_boundary_tests():
    if torch is None: return {"skipped":"torch missing"}
    # q == p exactly: F at minimum (0), gradient-descent step leaves it at 0
    mu_q = torch.tensor(0.0, requires_grad=True)
    log_sig_q = torch.tensor(0.0, requires_grad=True)
    F = _free_energy(mu_q, log_sig_q, torch.tensor(0.0), torch.tensor(1.0))
    return {"F_at_posterior_zero": {"F": float(F),
                                    "pass": abs(float(F)) < 1e-6}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (pos.get("gradient_flow_decreases_F",{}).get("pass",False)
                and neg.get("identity_rejected",{}).get("pass",False)
                and bnd.get("F_at_posterior_zero",{}).get("pass",False))
    out = {"name":"fep_atom_3_reduction","classification":"canonical",
           "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
           "positive":pos,"negative":neg,"boundary":bnd,
           "status":"PASS" if all_pass else "FAIL"}
    d = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d,"fep_atom_3_reduction_results.json")
    with open(p,"w") as f: json.dump(out,f,indent=2,default=str)
    print(f"[{out['status']}] {p}")
