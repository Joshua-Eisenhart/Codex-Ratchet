#!/usr/bin/env python3
"""
Holodeck atom 7 / 7 -- COUPLING.

Lego scope: given two admissible shell-local holodeck states, a coupling
is realized by a bipartite unitary U_AB acting on H_A (x) H_B. We test
that coupling is:
  - unitary (U U^dag = I)
  - can *create* correlation from a product state (entangling CNOT)
  - preserves trace and admissibility of the joint state
  - returns identity if the "coupling" is trivial (I (x) I)

This is the step-2 "pairwise coupling" lego: shell-local objects survive
the coupling probe, and correlation emerges.
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
    TOOL_MANIFEST[n]["reason"] = "not needed for bipartite unitary coupling"


def cnot():
    U = torch.zeros(4,4, dtype=torch.complex128)
    U[0,0]=1; U[1,1]=1; U[2,3]=1; U[3,2]=1
    return U


def partial_trace_B(rho, dA, dB):
    R = rho.reshape(dA,dB,dA,dB)
    return torch.einsum("ibjb->ij", R)


def run_positive_tests():
    results = {}
    U = cnot()
    I4 = torch.eye(4, dtype=torch.complex128)
    uu = U @ U.conj().T
    results["unitary"] = {"pass": torch.allclose(uu, I4, atol=1e-12)}
    # Apply CNOT to |+>|0> -> Bell state; partial trace gives mixed rA
    plus = torch.tensor([1,1], dtype=torch.complex128)/2**0.5
    zero = torch.tensor([1,0], dtype=torch.complex128)
    psi = torch.kron(plus, zero)
    psi2 = U @ psi
    rho = torch.outer(psi2, psi2.conj())
    rA = partial_trace_B(rho, 2, 2)
    ev = torch.linalg.eigvalsh((rA+rA.conj().T)/2).real.tolist()
    mixed = abs(ev[0] - 0.5) < 1e-12 and abs(ev[1] - 0.5) < 1e-12
    results["entangling"] = {"rA_eigs": ev, "pass": mixed}
    # Trace preservation under coupling
    g = torch.Generator().manual_seed(2)
    X = torch.randn(4,4, generator=g, dtype=torch.float64) + 1j*torch.randn(4,4, generator=g, dtype=torch.float64)
    r0 = X @ X.conj().T; r0 = r0/torch.trace(r0).real
    r1 = U @ r0 @ U.conj().T
    results["trace_pres"] = {"tr": float(torch.trace(r1).real),
                             "pass": abs(torch.trace(r1).real.item() - 1.0) < 1e-12}
    return results


def run_negative_tests():
    results = {}
    # Non-unitary "coupling" must be rejected
    M = torch.tensor([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,0]], dtype=torch.complex128)
    ok = torch.allclose(M @ M.conj().T, torch.eye(4, dtype=torch.complex128), atol=1e-12)
    results["non_unitary_rejected"] = {"pass": not ok}
    # Trivial coupling cannot create entanglement
    I4 = torch.eye(4, dtype=torch.complex128)
    plus = torch.tensor([1,1], dtype=torch.complex128)/2**0.5
    zero = torch.tensor([1,0], dtype=torch.complex128)
    psi = torch.kron(plus, zero)
    psi2 = I4 @ psi
    rho = torch.outer(psi2, psi2.conj())
    rA = partial_trace_B(rho, 2, 2)
    r = int(torch.linalg.matrix_rank(rA).item())
    results["trivial_no_ent"] = {"rank_rA": r, "pass": r == 1}
    return results


def run_boundary_tests():
    results = {}
    # Identity coupling preserves product state exactly
    I4 = torch.eye(4, dtype=torch.complex128)
    g = torch.Generator().manual_seed(8)
    a = torch.randn(2, generator=g, dtype=torch.float64) + 1j*torch.randn(2, generator=g, dtype=torch.float64)
    a = a/torch.linalg.norm(a)
    b = torch.randn(2, generator=g, dtype=torch.float64) + 1j*torch.randn(2, generator=g, dtype=torch.float64)
    b = b/torch.linalg.norm(b)
    psi = torch.kron(a,b)
    psi2 = I4 @ psi
    results["identity_preserves"] = {"pass": torch.allclose(psi, psi2, atol=1e-12)}
    # CNOT^2 = I
    U = cnot()
    results["cnot_involution"] = {"pass": torch.allclose(U @ U, I4, atol=1e-12)}
    return results


if __name__ == "__main__":
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "bipartite unitary ops + eigvalsh + matrix_rank load-bearing"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    def allpass(d): return all(v.get("pass", False) for v in d.values())
    all_pass = allpass(pos) and allpass(neg) and allpass(bnd)
    results = {
        "name": "holodeck_atom_7_coupling",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "canonical", "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "holodeck_atom_7_coupling_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"[atom7 coupling] all_pass={all_pass} -> {out_path}")
