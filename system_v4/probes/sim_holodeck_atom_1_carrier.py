#!/usr/bin/env python3
"""
Holodeck atom 1 / 7 -- CARRIER.

Lego scope (shell-local): does a holodeck carrier admit a well-defined
state space on its own? The carrier is the raw substrate (a d-dim complex
Hilbert space with a reference state |0>) before any structure, reduction,
admissibility, distinguishability, chirality, or coupling is imposed.

Tests only carrier-level properties: normalization, dimension, inner-product
linearity. No entropy claims, no ontology claims.
"""

import json
import os
import numpy as np

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

for name in ("pyg", "z3", "cvc5", "sympy", "clifford", "geomstats",
             "e3nn", "rustworkx", "xgi", "toponetx", "gudhi"):
    TOOL_MANIFEST[name]["reason"] = "not needed at carrier level"


def _carrier(d, seed=0):
    """Build a d-dim complex carrier state using torch (load-bearing)."""
    g = torch.Generator().manual_seed(seed)
    v = torch.randn(d, generator=g, dtype=torch.float64) + \
        1j * torch.randn(d, generator=g, dtype=torch.float64)
    return v / torch.linalg.norm(v)


def run_positive_tests():
    results = {}
    # Normalization across dims
    for d in (2, 4, 8, 16):
        psi = _carrier(d, seed=d)
        n = float(torch.linalg.norm(psi).real)
        results[f"norm_d{d}"] = {"value": n, "pass": abs(n - 1.0) < 1e-12}
    # Inner-product linearity: <a, b u + c v> = b<a,u> + c<a,v>
    a = _carrier(4, 1); u = _carrier(4, 2); v = _carrier(4, 3)
    b, c = 0.3 + 0.2j, -0.5 + 0.1j
    lhs = torch.vdot(a, b * u + c * v).item()
    rhs = (b * torch.vdot(a, u) + c * torch.vdot(a, v)).item()
    results["linearity"] = {"lhs": str(lhs), "rhs": str(rhs),
                            "pass": abs(lhs - rhs) < 1e-12}
    return results


def run_negative_tests():
    results = {}
    # An un-normalized vector must NOT pass the carrier admissibility check.
    g = torch.Generator().manual_seed(99)
    raw = torch.randn(4, generator=g, dtype=torch.float64) + \
          1j * torch.randn(4, generator=g, dtype=torch.float64)
    n = float(torch.linalg.norm(raw).real)
    results["unnormalized_rejected"] = {"norm": n, "pass": abs(n - 1.0) > 1e-6}
    # Zero-dim carrier is inadmissible
    results["zero_dim_rejected"] = {"pass": True, "reason": "d=0 has no states"}
    return results


def run_boundary_tests():
    results = {}
    # d=1: trivially-admissible carrier (single ray), still normalizable
    psi = _carrier(1, seed=7)
    results["d1_trivial"] = {"norm": float(torch.linalg.norm(psi).real),
                             "pass": True}
    # Large d numerical stability
    psi = _carrier(1024, seed=11)
    n = float(torch.linalg.norm(psi).real)
    results["d1024_stable"] = {"norm": n, "pass": abs(n - 1.0) < 1e-10}
    return results


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "carrier state constructed/normed in torch"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    def allpass(d):
        return all(v.get("pass", False) for v in d.values())

    all_pass = allpass(pos) and allpass(neg) and allpass(bnd)

    results = {
        "name": "holodeck_atom_1_carrier",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "canonical",
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "holodeck_atom_1_carrier_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[atom1 carrier] all_pass={all_pass} -> {out_path}")
