#!/usr/bin/env python3
"""
Holodeck atom 5 / 7 -- DISTINGUISHABILITY.

Lego scope: when are two holodeck states distinguishable by probes?
We use trace distance D(rho,sigma) = 0.5 * ||rho - sigma||_1 as the
operational distinguishability measure. Tests:
  - D(rho, rho) = 0 (self)
  - D(rho, sigma) in [0,1]
  - Orthogonal pure states -> D = 1
  - Symmetry D(a,b)=D(b,a)
"""

import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn",
    "rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
for n in ("pyg","z3","cvc5","sympy","clifford","geomstats","e3nn",
          "rustworkx","xgi","toponetx","gudhi"):
    TOOL_MANIFEST[n]["reason"] = "not needed for trace-distance"


def trace_distance(rho, sigma):
    M = rho - sigma
    M = (M + M.conj().T)/2
    ev = torch.linalg.eigvalsh(M).real
    return 0.5 * ev.abs().sum()


def rand_rho(d, seed):
    g = torch.Generator().manual_seed(seed)
    X = torch.randn(d,d, generator=g, dtype=torch.float64) + 1j*torch.randn(d,d, generator=g, dtype=torch.float64)
    rho = X @ X.conj().T
    return rho/torch.trace(rho).real


def run_positive_tests():
    results = {}
    r = rand_rho(2, 1)
    d = float(trace_distance(r, r).item())
    results["self_zero"] = {"D": d, "pass": d < 1e-12}
    # orthogonal pure states |0>,|1> -> D = 1
    p0 = torch.tensor([[1,0],[0,0]], dtype=torch.complex128)
    p1 = torch.tensor([[0,0],[0,1]], dtype=torch.complex128)
    d01 = float(trace_distance(p0, p1).item())
    results["ortho_pure"] = {"D": d01, "pass": abs(d01 - 1.0) < 1e-12}
    # symmetry
    a = rand_rho(3, 2); b = rand_rho(3, 3)
    dab = float(trace_distance(a,b).item())
    dba = float(trace_distance(b,a).item())
    results["symmetry"] = {"D_ab": dab, "D_ba": dba,
                           "pass": abs(dab - dba) < 1e-12}
    return results


def run_negative_tests():
    results = {}
    # D != 0 when states actually differ (prevents trivial-pass)
    a = rand_rho(2, 10); b = rand_rho(2, 11)
    d = float(trace_distance(a,b).item())
    results["nonzero_diff"] = {"D": d, "pass": d > 1e-6}
    # Same pure state at different global phase: D must still be 0
    v = torch.tensor([1,1], dtype=torch.complex128)/2**0.5
    r1 = torch.outer(v, v.conj())
    vp = torch.exp(torch.tensor(1j*0.7)) * v
    r2 = torch.outer(vp, vp.conj())
    d = float(trace_distance(r1,r2).item())
    results["global_phase_indist"] = {"D": d, "pass": d < 1e-7}
    return results


def run_boundary_tests():
    results = {}
    # range bound
    a = rand_rho(4, 20); b = rand_rho(4, 21)
    d = float(trace_distance(a,b).item())
    results["range_bound"] = {"D": d, "pass": 0 - 1e-12 <= d <= 1 + 1e-12}
    # max mixed vs max mixed: D=0
    I2 = torch.eye(2, dtype=torch.complex128)/2
    d = float(trace_distance(I2, I2).item())
    results["mix_self"] = {"D": d, "pass": d < 1e-12}
    return results


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "eigvalsh + abs sum = load-bearing trace distance"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    def allpass(d): return all(v.get("pass", False) for v in d.values())
    all_pass = allpass(pos) and allpass(neg) and allpass(bnd)
    results = {
        "name": "holodeck_atom_5_distinguishability",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "canonical", "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "holodeck_atom_5_distinguishability_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"[atom5 distinguishability] all_pass={all_pass} -> {out_path}")
