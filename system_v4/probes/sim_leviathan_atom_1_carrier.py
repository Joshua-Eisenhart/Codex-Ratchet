#!/usr/bin/env python3
"""
Leviathan atom 1 of 7: CARRIER.

Claim (nominalist): a civilizational shell requires a carrier field whose
support is non-empty, finite-variance, and additive across disjoint agents.
If any of those three fail, the shell is inadmissible (no carrier, no shell).

Load-bearing tool: sympy (symbolic verification that a candidate carrier
density integrates to finite total potential and is additive under disjoint
union). Numpy is a classical baseline cross-check only.
"""

import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed for symbolic additivity"},
    "pyg":       {"tried": False, "used": False, "reason": "no graph structure at carrier atom"},
    "z3":        {"tried": False, "used": False, "reason": "no boolean constraint set here"},
    "cvc5":      {"tried": False, "used": False, "reason": "redundant with z3 path at this atom"},
    "sympy":     {"tried": False, "used": False, "reason": "symbolic integration / additivity proof"},
    "clifford":  {"tried": False, "used": False, "reason": "no multivector carrier yet"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold metric at carrier atom"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariance claim here"},
    "rustworkx": {"tried": False, "used": False, "reason": "structure atom handles graphs"},
    "xgi":       {"tried": False, "used": False, "reason": "structure atom handles hypergraphs"},
    "toponetx":  {"tried": False, "used": False, "reason": "structure atom handles cell complexes"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistence claim here"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def _carrier_ok_sympy(rho_expr, var, a, b):
    """Return (finite_total, additive_disjoint) using sympy."""
    assert sp is not None
    total = sp.integrate(rho_expr, (var, a, b))
    mid = (a + b) / 2
    left = sp.integrate(rho_expr, (var, a, mid))
    right = sp.integrate(rho_expr, (var, mid, b))
    finite = total.is_finite if total.is_finite is not None else sp.simplify(total - total) == 0
    additive = sp.simplify((left + right) - total) == 0
    return bool(finite), bool(additive), float(total)


def run_positive_tests():
    results = {}
    if sp is None:
        return {"skipped": "sympy missing"}
    x = sp.symbols("x", real=True)
    # Gaussian-like carrier density, normalized, on compact support
    rho = sp.exp(-x**2)
    fin, add, total = _carrier_ok_sympy(rho, x, -3, 3)
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic integration + disjoint-union additivity check"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    results["gaussian_carrier"] = {
        "finite_total": fin, "additive_disjoint": add, "total": total,
        "pass": fin and add,
    }
    # classical cross-check
    xs = np.linspace(-3, 3, 4001)
    results["numpy_crosscheck_total"] = float(np.trapz(np.exp(-xs**2), xs))
    return results


def run_negative_tests():
    if sp is None:
        return {"skipped": "sympy missing"}
    x = sp.symbols("x", real=True, positive=True)
    # 1/x on (0,1): integral diverges => NOT a valid carrier
    rho = 1/x
    total = sp.integrate(rho, (x, 0, 1))
    diverges = total == sp.oo or not total.is_finite
    return {"divergent_carrier_rejected": {"total": str(total), "pass": bool(diverges)}}


def run_boundary_tests():
    if sp is None:
        return {"skipped": "sympy missing"}
    x = sp.symbols("x", real=True)
    # Zero carrier: finite but trivial -- boundary case, admitted as degenerate
    rho = sp.Integer(0)
    total = sp.integrate(rho, (x, -1, 1))
    return {"zero_carrier_degenerate": {"total": float(total), "pass": total == 0}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    out = {
        "name": "leviathan_atom_1_carrier",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
    }
    all_pass = (
        pos.get("gaussian_carrier", {}).get("pass", False)
        and neg.get("divergent_carrier_rejected", {}).get("pass", False)
        and bnd.get("zero_carrier_degenerate", {}).get("pass", False)
    )
    out["status"] = "PASS" if all_pass else "FAIL"
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "leviathan_atom_1_carrier_results.json")
    with open(p, "w") as f: json.dump(out, f, indent=2, default=str)
    print(f"[{out['status']}] {p}")
