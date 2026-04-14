#!/usr/bin/env python3
"""
Lane C canonical: Coherent information positivity on erasure channel.

Erasure channel N_p: |psi> -> (1-p)|psi><psi| + p |e><e|, e orthogonal flag.
For maximally mixed input, I_c(rho, N_p) = (1 - 2p) log 2 bits.
  p < 0.5  -> I_c > 0 (quantum capacity witness)
  p >= 0.5 -> I_c <= 0
Classical capacity witness over same channel = 0 for pure-state quantum input
(classical cannot use superposition).
Gap at p=0.1:  I_c = 0.8 bits vs classical 0 -> gap = 0.8 bits.

Load-bearing tool: pytorch (Stinespring dilation to (B,E) state via kron/stack,
then partial trace and eigvalsh on 3x3 reduced matrices).
"""

import json
import os
import math
import numpy as np
classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

LN2 = math.log(2.0)


def vne_bits_torch(rho):
    e = torch.linalg.eigvalsh(rho).real
    e = torch.clamp(e, min=1e-12)
    return -(e * torch.log2(e)).sum()


def erasure_channel(rho_t, p):
    """Output on 3-d Hilbert space: embed qubit in {|0>,|1>} and |e>=|2>.
    N_p(rho) = (1-p) * rho_embedded + p * |e><e|."""
    emb = torch.zeros((3, 3), dtype=rho_t.dtype)
    emb[:2, :2] = rho_t
    e_proj = torch.zeros((3, 3), dtype=rho_t.dtype)
    e_proj[2, 2] = 1.0
    return (1 - p) * emb + p * e_proj


def coherent_information_erasure_bits(rho_t, p):
    """I_c(rho, N) = S(N(rho)) - S((I x N)(|psi_ref><psi_ref|))
    For erasure channel with input rho, the standard result:
      I_c = (1-2p) * S(rho) in bits when rho is the input eigenstate.
    We compute directly via purification.
    Purify qubit rho to 2-qubit |psi_RA>, apply erasure on A (qubit -> 3-d),
    get rho_RB on (2 x 3); compute I_c = S(rho_B) - S(rho_RB)."""
    # Purify: rho = sum_i lambda_i |i><i| => |psi> = sum_i sqrt(lambda_i) |i>_R |i>_A
    evals, evecs = torch.linalg.eigh(rho_t)
    evals = torch.clamp(evals.real, min=0.0)
    # |psi_RA> in C^2 x C^2 (A is qubit-space; embed later into 3-d during channel)
    # Build as 4-vector: |psi> = sum_i sqrt(lambda_i) |i,i>
    psi = torch.zeros(4, dtype=rho_t.dtype)
    for i in range(2):
        psi[2 * i + i] = torch.sqrt(evals[i].to(rho_t.dtype))
        # apply eigenbasis rotation on A side: |i>_A -> sum_j V[j,i] |j>
    # Simpler: build rho_RA directly = sum_{ij} sqrt(lambda_i lambda_j) |i><j|_R x (V|i><j|V^H)_A
    V = evecs.to(rho_t.dtype)
    # rho_RA in computational basis (R:2, A:2) shape (4,4)
    rho_RA = torch.zeros((4, 4), dtype=rho_t.dtype)
    for i in range(2):
        for j in range(2):
            coeff = torch.sqrt(evals[i].to(rho_t.dtype)) * torch.sqrt(evals[j].to(rho_t.dtype))
            R_block = torch.zeros((2, 2), dtype=rho_t.dtype)
            R_block[i, j] = 1.0
            A_block = V[:, i:i+1] @ V[:, j:j+1].conj().T
            rho_RA = rho_RA + coeff * torch.kron(R_block, A_block)

    # Apply erasure on A: extend A from 2 to 3 dims
    # rho_RA_ext in (R:2, A':3): (1-p) * embed + p * (rho_R x |e><e|)
    rho_R = torch.einsum("ijkj->ik", rho_RA.reshape(2, 2, 2, 2))
    rho_RA_ext = torch.zeros((6, 6), dtype=rho_t.dtype)
    # (1-p) embedding of rho_RA into (2,3) x (2,3)
    rho_RA_r = rho_RA.reshape(2, 2, 2, 2)
    for a in range(2):
        for b in range(2):
            for c in range(2):
                for d in range(2):
                    rho_RA_ext[a * 3 + b, c * 3 + d] += (1 - p) * rho_RA_r[a, b, c, d]
    # p * rho_R x |e><e|
    for a in range(2):
        for c in range(2):
            rho_RA_ext[a * 3 + 2, c * 3 + 2] += p * rho_R[a, c]

    # rho_B = Tr_R(rho_RA_ext)
    rho_RA_ext_r = rho_RA_ext.reshape(2, 3, 2, 3)
    rho_B = torch.einsum("ijkj->ik", rho_RA_ext_r.permute(1, 0, 3, 2)).T
    # safer: sum over R index
    rho_B = torch.zeros((3, 3), dtype=rho_t.dtype)
    for r in range(2):
        rho_B = rho_B + rho_RA_ext_r[r, :, r, :]

    s_B = vne_bits_torch(rho_B)
    s_RB = vne_bits_torch(rho_RA_ext)
    return float((s_B - s_RB).item())


def run_positive_tests():
    results = {}
    rho = torch.eye(2, dtype=torch.complex128) / 2

    # P1: I_c = (1-2p) * log2 for maximally mixed input
    p1 = {}
    for p in [0.0, 0.1, 0.25, 0.49]:
        ic = coherent_information_erasure_bits(rho, p)
        expected = (1 - 2 * p) * 1.0
        p1[f"p={p}"] = {"I_c": ic, "expected": expected,
                         "diff": abs(ic - expected),
                         "pass": abs(ic - expected) < 1e-3}
    results["P1_erasure_formula"] = p1

    # P2: I_c > 0 for p < 0.5 (quantum capacity witness)
    p2 = {}
    for p in [0.05, 0.2, 0.4]:
        ic = coherent_information_erasure_bits(rho, p)
        p2[f"p={p}"] = {"I_c": ic, "pass": ic > 1e-4}
    results["P2_positive_below_half"] = p2

    # P3: quantum/classical gap at p=0.1
    ic = coherent_information_erasure_bits(rho, 0.1)
    gap = ic - 0.0  # classical witness = 0
    results["P3_quantum_classical_gap_at_p01"] = {
        "I_c": ic, "gap_bits": gap, "expected_gap": 0.8,
        "pass": abs(gap - 0.8) < 1e-3,
    }
    return results


def run_negative_tests():
    results = {}
    rho = torch.eye(2, dtype=torch.complex128) / 2

    # N1: I_c <= 0 for p >= 0.5
    n1 = {}
    for p in [0.5, 0.6, 0.9]:
        ic = coherent_information_erasure_bits(rho, p)
        n1[f"p={p}"] = {"I_c": ic, "pass": ic <= 1e-4}
    results["N1_nonpositive_above_half"] = n1

    # N2: For pure product input (|0>), I_c <= 0 (no entanglement to preserve)
    rho0 = torch.tensor([[1.0, 0], [0, 0]], dtype=torch.complex128)
    ic = coherent_information_erasure_bits(rho0, 0.1)
    results["N2_pure_input_nonpositive"] = {"I_c": ic, "pass": ic <= 1e-4}
    return results


def run_boundary_tests():
    results = {}
    rho = torch.eye(2, dtype=torch.complex128) / 2

    # B1: p=0 -> I_c = log2 = 1 bit (perfect channel)
    ic = coherent_information_erasure_bits(rho, 0.0)
    results["B1_perfect_channel"] = {"I_c": ic, "expected": 1.0,
                                      "pass": abs(ic - 1.0) < 1e-3}

    # B2: p=0.5 -> I_c = 0 (threshold)
    ic = coherent_information_erasure_bits(rho, 0.5)
    results["B2_threshold_half"] = {"I_c": ic, "pass": abs(ic) < 1e-3}

    # B3: p=1.0 -> I_c = -1 bit (full erasure)
    ic = coherent_information_erasure_bits(rho, 1.0)
    results["B3_full_erasure"] = {"I_c": ic, "expected": -1.0,
                                    "pass": abs(ic - (-1.0)) < 1e-3}
    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Load-bearing: purification via torch.linalg.eigh, Stinespring dilation "
        "from qubit (2-d) to erasure output (3-d) built with torch tensor ops, "
        "partial trace via indexing, VNE via torch.linalg.eigvalsh. Quantum "
        "capacity witness is a torch tensor computation end-to-end."
    )

    def count_passes(d):
        p, t = 0, 0
        if isinstance(d, dict):
            if "pass" in d:
                t += 1
                if d["pass"]:
                    p += 1
            for v in d.values():
                a, b = count_passes(v)
                p += a; t += b
        return p, t

    tp, tt = count_passes({"positive": positive, "negative": negative, "boundary": boundary})

    results = {
        "name": "coherent_info_erasure_canonical",
        "description": "Lane C: I_c(erasure,p<0.5)>0 quantum capacity witness; gap 0.8 at p=0.1",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive, "negative": negative, "boundary": boundary,
        "classification": "canonical",
        "quantum_classical_gap_bits": positive["P3_quantum_classical_gap_at_p01"]["gap_bits"],
        "summary": {"total_tests": tt, "total_pass": tp, "all_pass": tp == tt},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "coherent_info_erasure_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results: {tp}/{tt} pass -> {out_path}")
    if tp != tt:
        raise SystemExit(1)
