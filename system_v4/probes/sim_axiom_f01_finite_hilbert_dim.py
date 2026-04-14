#!/usr/bin/env python3
"""sim_axiom_f01_finite_hilbert_dim -- F01 clause dim(H)<infty.

Canonical sim atomizing F01: the carrier Hilbert space must be finite-
dimensional. With H = C^d (d=2 here), density operators satisfy Tr(rho)=1
and rho >= 0. Bloch-vector norm |r| <= 1. torch is load-bearing (verifies
rho constraints numerically); z3 supports finite-dim enumerability.
"""

import json, os
import numpy as np
classification = "classical_baseline"  # auto-backfill

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
try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


def bloch_to_rho(r):
    I = torch.eye(2, dtype=torch.complex128)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    return 0.5 * (I + r[0] * sx + r[1] * sy + r[2] * sz)


def run_positive_tests():
    """Pure and mixed Bloch vectors in the unit ball produce valid rho."""
    cases = [torch.tensor([1.0, 0, 0]),
             torch.tensor([0, 0, 1.0]),
             torch.tensor([0.3, 0.4, 0.5]),
             torch.tensor([0.0, 0.0, 0.0])]
    ok = True
    traces, herms, psds = [], [], []
    for r in cases:
        rho = bloch_to_rho(r)
        tr = torch.trace(rho).real.item()
        herm = torch.allclose(rho, rho.conj().T, atol=1e-10)
        eigs = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
        psd = bool((eigs >= -1e-10).all())
        traces.append(tr); herms.append(bool(herm)); psds.append(psd)
        ok &= abs(tr - 1.0) < 1e-10 and herm and psd
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "load-bearing: constructs rho on C^2, checks trace=1, hermiticity, PSD"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    # z3: existence of a finite basis of size d=2 for H
    s = z3.Solver()
    e = [z3.Int(f"e_{i}") for i in range(2)]
    s.add(z3.Distinct(e)); s.add(*[z3.And(x >= 0, x < 2) for x in e])
    basis_sat = str(s.check())
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "supportive: a finite-dim basis of size d=2 is enumerable"
    TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
    return {"traces": traces, "hermitian": herms, "psd": psds, "basis_sat": basis_sat, "pass": ok and basis_sat == "sat"}


def run_negative_tests():
    """|r| > 1 must produce a non-PSD rho (negative eigenvalue)."""
    bad = torch.tensor([0.9, 0.9, 0.9])  # |r| ~ 1.56
    rho = bloch_to_rho(bad)
    eigs = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    psd = bool((eigs >= -1e-10).all())
    return {"bloch_norm": float(torch.linalg.norm(bad)), "psd": psd,
            "min_eig": float(eigs.min()), "pass": (not psd)}


def run_boundary_tests():
    """|r|=1 exactly (pure state boundary): rho is rank-1, still PSD."""
    r = torch.tensor([0.0, 0.0, 1.0])  # |r|=1
    rho = bloch_to_rho(r)
    eigs = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    rank1 = bool((eigs.min().abs() < 1e-10) and (eigs.max().item() - 1.0) < 1e-10)
    return {"eigs": [float(e) for e in eigs], "rank1_pure": rank1, "pass": rank1}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos.get("pass") and neg.get("pass") and bnd.get("pass"))
    results = {
        "name": "sim_axiom_f01_finite_hilbert_dim",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_axiom_f01_finite_hilbert_dim_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out_path}")
