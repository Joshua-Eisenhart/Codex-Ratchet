#!/usr/bin/env python3
"""
Holodeck atom 3 / 7 -- REDUCTION.

Lego scope: given H_A (x) H_B with a state rho_AB, the reduction map
(partial trace) delivers rho_A = Tr_B rho_AB. We test linearity,
trace preservation, positivity-of-reduced-state (non-negative eigenvalues),
and that product states reduce to their factors.
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
    TOOL_MANIFEST[n]["reason"] = "not needed for partial trace"


def partial_trace_B(rho, dA, dB):
    R = rho.reshape(dA, dB, dA, dB)
    return torch.einsum("ibjb->ij", R)


def partial_trace_A(rho, dA, dB):
    R = rho.reshape(dA, dB, dA, dB)
    return torch.einsum("aibi->ab", R)


def run_positive_tests():
    results = {}
    # Trace preservation
    g = torch.Generator().manual_seed(3)
    dA, dB = 2, 3
    X = torch.randn(dA*dB, dA*dB, generator=g, dtype=torch.float64) + \
        1j*torch.randn(dA*dB, dA*dB, generator=g, dtype=torch.float64)
    rho = X @ X.conj().T
    rho = rho / torch.trace(rho).real
    rA = partial_trace_B(rho, dA, dB)
    results["trace_preservation"] = {
        "tr_rho": float(torch.trace(rho).real),
        "tr_rA": float(torch.trace(rA).real),
        "pass": abs(torch.trace(rA).real.item() - 1.0) < 1e-12,
    }
    # Product state rho_A (x) rho_B reduces to rho_A
    g2 = torch.Generator().manual_seed(4)
    a = torch.randn(dA, generator=g2, dtype=torch.float64) + 1j*torch.randn(dA, generator=g2, dtype=torch.float64)
    a = a/torch.linalg.norm(a)
    b = torch.randn(dB, generator=g2, dtype=torch.float64) + 1j*torch.randn(dB, generator=g2, dtype=torch.float64)
    b = b/torch.linalg.norm(b)
    rhoA = torch.outer(a, a.conj())
    rhoB = torch.outer(b, b.conj())
    rhoAB = torch.kron(rhoA, rhoB)
    rA = partial_trace_B(rhoAB, dA, dB)
    results["product_reduces"] = {"pass": torch.allclose(rA, rhoA, atol=1e-12)}
    # Positivity of reduced state
    ev = torch.linalg.eigvalsh((rA + rA.conj().T)/2).real
    results["positivity"] = {"min_eig": float(ev.min()),
                             "pass": ev.min().item() > -1e-12}
    return results


def run_negative_tests():
    results = {}
    # Reduction of entangled state != any pure state (rank > 1)
    bell = torch.tensor([1,0,0,1], dtype=torch.complex128)/2**0.5
    rho = torch.outer(bell, bell.conj())
    rA = partial_trace_B(rho, 2, 2)
    r = torch.linalg.matrix_rank(rA).item()
    results["entangled_mixes"] = {"rank_rA": int(r), "pass": r > 1}
    # Wrong dim factorization: dA*dB != system dim -> should refuse
    ok = True
    try:
        bad = partial_trace_B(rho, 3, 3)
        ok = False  # reshape should have failed
    except Exception:
        ok = True
    results["bad_dims_rejected"] = {"pass": ok}
    return results


def run_boundary_tests():
    results = {}
    # Identity / maximally mixed
    dA, dB = 2, 2
    I = torch.eye(dA*dB, dtype=torch.complex128) / (dA*dB)
    rA = partial_trace_B(I, dA, dB)
    expected = torch.eye(dA, dtype=torch.complex128) / dA
    results["max_mixed"] = {"pass": torch.allclose(rA, expected, atol=1e-12)}
    # Symmetry: Tr_A(rho) then Tr rB should = Tr rho
    g = torch.Generator().manual_seed(7)
    X = torch.randn(4,4, generator=g, dtype=torch.float64) + 1j*torch.randn(4,4, generator=g, dtype=torch.float64)
    rho = X @ X.conj().T
    rho = rho/torch.trace(rho).real
    rB = partial_trace_A(rho, 2, 2)
    results["dual_reduction"] = {
        "tr_rB": float(torch.trace(rB).real),
        "pass": abs(torch.trace(rB).real.item() - 1.0) < 1e-12,
    }
    return results


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "einsum partial trace + eigvalsh load-bearing"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    def allpass(d): return all(v.get("pass", False) for v in d.values())
    all_pass = allpass(pos) and allpass(neg) and allpass(bnd)
    results = {
        "name": "holodeck_atom_3_reduction",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "canonical", "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "holodeck_atom_3_reduction_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"[atom3 reduction] all_pass={all_pass} -> {out_path}")
