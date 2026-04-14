#!/usr/bin/env python3
"""
Leviathan atom 5 of 7: DISTINGUISHABILITY.

Claim: two candidate shells are distinguishable iff there exists a probe
that yields different outcomes. Distinguishability is probe-relative; two
shells with identical carrier totals but divergent agent-level carriers
must be distinguishable by a variance probe but indistinguishable by a
sum probe.

Load-bearing tool: pytorch (probe = differentiable functional on carrier
vectors). Shows the probe-relative nature of distinguishability.
"""

import json, os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "differentiable probe functionals"},
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


def run_positive_tests():
    if torch is None: return {"skipped":"torch missing"}
    a = torch.tensor([2.5, 2.5, 2.5, 2.5])
    b = torch.tensor([0.0, 0.0, 5.0, 5.0])
    variance_probe = (a.var(unbiased=False) - b.var(unbiased=False)).abs().item()
    distinguishable = variance_probe > 1e-6
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    return {"variance_probe_distinguishes": {"gap": variance_probe,
                                             "pass": distinguishable}}


def run_negative_tests():
    if torch is None: return {"skipped":"torch missing"}
    a = torch.tensor([2.5, 2.5, 2.5, 2.5])
    b = torch.tensor([0.0, 0.0, 5.0, 5.0])
    sum_probe = (a.sum() - b.sum()).abs().item()
    return {"sum_probe_fails_to_distinguish": {"gap": sum_probe,
                                               "pass": sum_probe < 1e-6}}


def run_boundary_tests():
    if torch is None: return {"skipped":"torch missing"}
    a = torch.tensor([2.5, 2.5, 2.5, 2.5])
    gap = (a.var(unbiased=False) - a.var(unbiased=False)).abs().item()
    return {"identical_indistinguishable": {"gap": gap, "pass": gap == 0.0}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (pos.get("variance_probe_distinguishes",{}).get("pass",False)
                and neg.get("sum_probe_fails_to_distinguish",{}).get("pass",False)
                and bnd.get("identical_indistinguishable",{}).get("pass",False))
    out = {"name":"leviathan_atom_5_distinguishability","classification":"canonical",
           "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
           "positive":pos,"negative":neg,"boundary":bnd,
           "status":"PASS" if all_pass else "FAIL"}
    d = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d,"leviathan_atom_5_distinguishability_results.json")
    with open(p,"w") as f: json.dump(out,f,indent=2,default=str)
    print(f"[{out['status']}] {p}")
