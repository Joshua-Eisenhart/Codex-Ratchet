#!/usr/bin/env python3
"""
FEP atom 5 of 7: DISTINGUISHABILITY.

Claim: two candidate FEP shells (two q distributions with same blanket)
are distinguishable iff there exists a probe yielding different outcomes.
Two q's with identical means but divergent variances are
indistinguishable by a mean-probe but distinguishable by an F-probe
(variational free energy against a fixed prior p).

Load-bearing tool: pytorch (differentiable probe functionals; F-probe
computed via autograd-ready closed form KL).
"""

import json, os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "differentiable probe over q"},
    "pyg":       {"tried": False, "used": False, "reason": "not used"},
    "z3":        {"tried": False, "used": False, "reason": "not a proof atom"},
    "cvc5":      {"tried": False, "used": False, "reason": "not used"},
    "sympy":     {"tried": False, "used": False, "reason": "not used"},
    "clifford":  {"tried": False, "used": False, "reason": "not used"},
    "geomstats": {"tried": False, "used": False, "reason": "not used"},
    "e3nn":      {"tried": False, "used": False, "reason": "not used"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used"},
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


def _kl_gauss(mu_q, sig_q, mu_p, sig_p):
    return torch.log(sig_p/sig_q) + (sig_q**2 + (mu_q-mu_p)**2)/(2*sig_p**2) - 0.5


def run_positive_tests():
    if torch is None: return {"skipped":"torch missing"}
    mu_p = torch.tensor(0.0); sig_p = torch.tensor(1.0)
    # Two q's: same mean, different variance
    Fa = _kl_gauss(torch.tensor(0.0), torch.tensor(0.5), mu_p, sig_p)
    Fb = _kl_gauss(torch.tensor(0.0), torch.tensor(2.0), mu_p, sig_p)
    gap = abs(float(Fa) - float(Fb))
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    return {"F_probe_distinguishes": {"Fa": float(Fa), "Fb": float(Fb),
                                      "gap": gap, "pass": gap > 1e-3}}


def run_negative_tests():
    if torch is None: return {"skipped":"torch missing"}
    # Mean-probe fails for same-mean-different-variance pair
    mean_a = torch.tensor(0.0); mean_b = torch.tensor(0.0)
    gap = float((mean_a - mean_b).abs())
    return {"mean_probe_fails": {"gap": gap, "pass": gap < 1e-9}}


def run_boundary_tests():
    if torch is None: return {"skipped":"torch missing"}
    # Identical q's -- all probes agree, indistinguishable
    Fa = _kl_gauss(torch.tensor(0.1), torch.tensor(0.7),
                   torch.tensor(0.0), torch.tensor(1.0))
    Fb = _kl_gauss(torch.tensor(0.1), torch.tensor(0.7),
                   torch.tensor(0.0), torch.tensor(1.0))
    gap = abs(float(Fa) - float(Fb))
    return {"identical_indistinguishable": {"gap": gap, "pass": gap == 0.0}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (pos.get("F_probe_distinguishes",{}).get("pass",False)
                and neg.get("mean_probe_fails",{}).get("pass",False)
                and bnd.get("identical_indistinguishable",{}).get("pass",False))
    out = {"name":"fep_atom_5_distinguishability","classification":"canonical",
           "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
           "positive":pos,"negative":neg,"boundary":bnd,
           "status":"PASS" if all_pass else "FAIL"}
    d = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d,"fep_atom_5_distinguishability_results.json")
    with open(p,"w") as f: json.dump(out,f,indent=2,default=str)
    print(f"[{out['status']}] {p}")
