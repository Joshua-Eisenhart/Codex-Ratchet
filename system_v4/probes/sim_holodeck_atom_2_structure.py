#!/usr/bin/env python3
"""
Holodeck atom 2 / 7 -- STRUCTURE.

Lego scope: impose tensor-product / subsystem structure on the carrier.
A holodeck scene requires a decomposition H = H_A (x) H_B so that local
probes can exist. We test that such a decomposition preserves dimension,
respects normalization, and that local operators factorize correctly.
"""

import json
import os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn",
    "rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

for name in ("pyg","z3","cvc5","sympy","clifford","geomstats","e3nn",
             "rustworkx","xgi","toponetx","gudhi"):
    TOOL_MANIFEST[name]["reason"] = "not needed at tensor-structure level"


def kron(A, B):
    return torch.kron(A, B)


def run_positive_tests():
    results = {}
    # dim(H_A (x) H_B) = dim A * dim B
    for dA, dB in [(2,2),(2,3),(3,4),(2,8)]:
        IA = torch.eye(dA, dtype=torch.complex128)
        IB = torch.eye(dB, dtype=torch.complex128)
        K = kron(IA, IB)
        results[f"dim_{dA}x{dB}"] = {"shape": list(K.shape),
                                     "pass": K.shape == (dA*dB, dA*dB)}
    # product state normalization
    g = torch.Generator().manual_seed(5)
    a = torch.randn(2, generator=g, dtype=torch.float64) + 1j*torch.randn(2, generator=g, dtype=torch.float64)
    a = a/torch.linalg.norm(a)
    b = torch.randn(3, generator=g, dtype=torch.float64) + 1j*torch.randn(3, generator=g, dtype=torch.float64)
    b = b/torch.linalg.norm(b)
    psi = kron(a.reshape(-1,1), b.reshape(-1,1)).reshape(-1)
    n = float(torch.linalg.norm(psi).real)
    results["product_norm"] = {"norm": n, "pass": abs(n-1) < 1e-12}
    # local operator factorization: (A (x) I)(I (x) B) = A (x) B
    A = torch.tensor([[1,1j],[1j,1]], dtype=torch.complex128)/2**0.5
    B = torch.tensor([[0,1],[1,0]], dtype=torch.complex128)
    IA = torch.eye(2, dtype=torch.complex128)
    IB = torch.eye(2, dtype=torch.complex128)
    lhs = kron(A,IB) @ kron(IA,B)
    rhs = kron(A,B)
    results["factorization"] = {"pass": torch.allclose(lhs, rhs, atol=1e-12)}
    return results


def run_negative_tests():
    results = {}
    # Non-product state cannot be written as a (x) b (entangled)
    # Bell state: 1/sqrt(2) (|00> + |11>)
    bell = torch.tensor([1,0,0,1], dtype=torch.complex128)/2**0.5
    # Try to find a,b with a(x)b = bell: compute reduced rank of reshaping
    M = bell.reshape(2,2)
    ranks = torch.linalg.matrix_rank(M).item()
    results["entangled_nonproduct"] = {"schmidt_rank": int(ranks),
                                       "pass": ranks > 1}
    # Dimension mismatch: kron of dA=2 vs dB=3 cannot be (4,4)
    IA = torch.eye(2, dtype=torch.complex128)
    IB = torch.eye(3, dtype=torch.complex128)
    K = kron(IA,IB)
    results["dim_mismatch_rejected"] = {"shape": list(K.shape),
                                        "pass": K.shape != (4,4)}
    return results


def run_boundary_tests():
    results = {}
    # Trivial factor: H (x) C = H
    a = torch.tensor([1.0+0j, 2.0+0j])/5**0.5
    trivial = torch.tensor([1.0+0j])
    psi = kron(a.reshape(-1,1), trivial.reshape(-1,1)).reshape(-1)
    results["trivial_factor"] = {"pass": torch.allclose(psi, a, atol=1e-12)}
    # Associativity dimensionally: (HA (x) HB) (x) HC = HA (x) (HB (x) HC)
    IA = torch.eye(2, dtype=torch.complex128)
    IB = torch.eye(2, dtype=torch.complex128)
    IC = torch.eye(2, dtype=torch.complex128)
    L = kron(kron(IA,IB),IC)
    R = kron(IA,kron(IB,IC))
    results["assoc"] = {"pass": torch.allclose(L, R, atol=1e-12)}
    return results


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "kron / matrix_rank / allclose load-bearing"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    def allpass(d): return all(v.get("pass", False) for v in d.values())
    all_pass = allpass(pos) and allpass(neg) and allpass(bnd)

    results = {
        "name": "holodeck_atom_2_structure",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "canonical",
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "holodeck_atom_2_structure_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"[atom2 structure] all_pass={all_pass} -> {out_path}")
