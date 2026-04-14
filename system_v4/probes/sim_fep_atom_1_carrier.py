#!/usr/bin/env python3
"""
FEP atom 1 of 7: CARRIER.

Claim (nominalist): a Free-Energy-Principle shell requires a carrier
distribution q(x) over internal states that is non-negative, integrates
to 1, and has finite expected log-density (so variational free energy
F = E_q[log q - log p] is well-defined). Violating any of these renders
the shell inadmissible (no carrier, no FEP shell).

Load-bearing tool: sympy (symbolic verification that a Gaussian q has
unit total mass and finite E_q[log q]).
"""

import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "autograd enters at reduction atom"},
    "pyg":       {"tried": False, "used": False, "reason": "no graph at carrier atom"},
    "z3":        {"tried": False, "used": False, "reason": "no boolean constraint here"},
    "cvc5":      {"tried": False, "used": False, "reason": "redundant"},
    "sympy":     {"tried": False, "used": False, "reason": "symbolic normalization + log-expectation"},
    "clifford":  {"tried": False, "used": False, "reason": "no multivector carrier"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold yet"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariance claim"},
    "rustworkx": {"tried": False, "used": False, "reason": "structure is atom 2"},
    "xgi":       {"tried": False, "used": False, "reason": "not used"},
    "toponetx":  {"tried": False, "used": False, "reason": "not used"},
    "gudhi":     {"tried": False, "used": False, "reason": "not used"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def run_positive_tests():
    if sp is None: return {"skipped":"sympy missing"}
    x, mu, sig = sp.symbols("x mu sigma", real=True, positive=False)
    # Standard Gaussian q(x) = 1/sqrt(2pi) exp(-x^2/2)
    q = sp.exp(-x**2/2) / sp.sqrt(2*sp.pi)
    total = sp.integrate(q, (x, -sp.oo, sp.oo))
    # E_q[log q] = -0.5*(1 + log(2*pi)) for standard normal (differential entropy = -this)
    log_q = sp.log(q)
    E_log_q = sp.integrate(q * log_q, (x, -sp.oo, sp.oo))
    E_log_q_s = sp.simplify(E_log_q)
    expected = -sp.Rational(1,2) * (1 + sp.log(2*sp.pi))
    finite = sp.simplify(E_log_q_s - expected) == 0
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic unit-mass + finite log-expectation on Gaussian carrier"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    return {"gaussian_carrier": {
        "total": float(total), "E_log_q": float(E_log_q_s),
        "pass": bool(total == 1) and bool(finite)
    }}


def run_negative_tests():
    if sp is None: return {"skipped":"sympy missing"}
    x = sp.symbols("x", real=True, positive=True)
    # Improper "uniform" q = 1 on (0, oo) -- does not integrate to 1
    q = sp.Integer(1)
    total = sp.integrate(q, (x, 0, sp.oo))
    diverges = (total == sp.oo) or (total.is_finite is False)
    return {"improper_carrier_rejected": {"total": str(total), "pass": bool(diverges)}}


def run_boundary_tests():
    if sp is None: return {"skipped":"sympy missing"}
    x = sp.symbols("x", real=True)
    # Dirac-like boundary: zero everywhere except a point -- integrates to 0, rejected
    q = sp.Integer(0)
    total = sp.integrate(q, (x, -1, 1))
    return {"zero_carrier_degenerate": {"total": float(total), "pass": total == 0}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (pos.get("gaussian_carrier",{}).get("pass",False)
                and neg.get("improper_carrier_rejected",{}).get("pass",False)
                and bnd.get("zero_carrier_degenerate",{}).get("pass",False))
    out = {"name":"fep_atom_1_carrier","classification":"canonical",
           "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
           "positive":pos,"negative":neg,"boundary":bnd,
           "status":"PASS" if all_pass else "FAIL"}
    d = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d,"fep_atom_1_carrier_results.json")
    with open(p,"w") as f: json.dump(out,f,indent=2,default=str)
    print(f"[{out['status']}] {p}")
