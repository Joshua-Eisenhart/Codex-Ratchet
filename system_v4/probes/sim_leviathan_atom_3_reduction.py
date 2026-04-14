#!/usr/bin/env python3
"""
Leviathan atom 3 of 7: REDUCTION.

Claim: the shell must admit a non-trivial reduction of per-agent carrier
to a shell-level summary (a many-to-one map that preserves at least the
total). A reduction that is pure identity (no compression) is not a shell
reduction; a reduction that collapses to zero is degenerate.

Load-bearing tool: pytorch (autograd-friendly sum reduction over a
per-agent carrier vector; tests differentiability of the shell summary
w.r.t. agent contributions -- the ratchet substrate).
"""

import json, os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "autograd reduction over carrier"},
    "pyg":       {"tried": False, "used": False, "reason": "no edge-based aggregation yet"},
    "z3":        {"tried": False, "used": False, "reason": "numerical reduction not boolean"},
    "cvc5":      {"tried": False, "used": False, "reason": "redundant"},
    "sympy":     {"tried": False, "used": False, "reason": "symbolic done in atom 1"},
    "clifford":  {"tried": False, "used": False, "reason": "scalar reduction here"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold mean here"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "structure is atom 2"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed"},
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
    c = torch.tensor([1.0, 2.0, 3.0, 4.0], requires_grad=True)
    S = c.sum()
    S.backward()
    grads_all_one = bool(torch.allclose(c.grad, torch.ones_like(c)))
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    return {"sum_reduction": {"S": float(S), "grad_ones": grads_all_one,
                              "pass": float(S) == 10.0 and grads_all_one}}


def run_negative_tests():
    if torch is None: return {"skipped":"torch missing"}
    c = torch.tensor([1.0, 2.0, 3.0, 4.0], requires_grad=True)
    # identity "reduction" -- not a reduction; per-agent still separate
    S = c  # no compression
    is_reduction = S.ndim == 0
    return {"identity_rejected": {"is_reduction": is_reduction, "pass": not is_reduction}}


def run_boundary_tests():
    if torch is None: return {"skipped":"torch missing"}
    c = torch.zeros(4, requires_grad=True)
    S = c.sum()
    # degenerate but well-defined
    return {"zero_carrier_reduction": {"S": float(S), "pass": float(S) == 0.0}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (pos.get("sum_reduction",{}).get("pass",False)
                and neg.get("identity_rejected",{}).get("pass",False)
                and bnd.get("zero_carrier_reduction",{}).get("pass",False))
    out = {"name":"leviathan_atom_3_reduction","classification":"canonical",
           "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
           "positive":pos,"negative":neg,"boundary":bnd,
           "status":"PASS" if all_pass else "FAIL"}
    d = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d,"leviathan_atom_3_reduction_results.json")
    with open(p,"w") as f: json.dump(out,f,indent=2,default=str)
    print(f"[{out['status']}] {p}")
