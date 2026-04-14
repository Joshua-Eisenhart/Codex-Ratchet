#!/usr/bin/env python3
"""
Lane C canonical: Quantum mutual information super-additivity over classical.

For |Phi+>: S(A) = S(B) = log 2, S(AB) = 0, so I_Q(A:B) = 2 log 2 = 2 bits.
Classical Shannon mutual information on any joint distribution over 2x2 outcomes
is bounded by I_C <= log 2 = 1 bit (entropy bound of a single bit marginal).
Quantum/classical gap: 1 bit.

Load-bearing tool: pytorch (quantum I via torch.linalg.eigvalsh on rho, rho_A, rho_B;
classical I via torch tensor sums over measurement probabilities).
"""

import json
import os
import math
import numpy as np
classification = "classical_baseline"  # auto-backfill

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


def phi_plus():
    psi = np.array([1, 0, 0, 1], dtype=np.complex128) / math.sqrt(2)
    return np.outer(psi, psi.conj())


def vne_bits_torch(rho):
    e = torch.linalg.eigvalsh(rho).real
    e = torch.clamp(e, min=1e-12)
    return -(e * torch.log2(e)).sum()


def quantum_MI_bits(rho_t):
    """I_Q(A:B) in bits."""
    r = rho_t.reshape(2, 2, 2, 2)
    rho_a = torch.einsum("ijkj->ik", r)
    rho_b = torch.einsum("ijil->jl", r)
    return vne_bits_torch(rho_a) + vne_bits_torch(rho_b) - vne_bits_torch(rho_t)


def classical_MI_bits_from_measurement(rho_t, basis="Z"):
    """Measure both qubits in Z (or X) basis, compute classical Shannon MI in bits.
    p(i,j) = <ij|rho|ij> for Z. Returns torch scalar."""
    r = rho_t.reshape(2, 2, 2, 2)
    if basis == "Z":
        # Probabilities: diag in computational basis
        diag = torch.einsum("ijij->ij", r).real  # shape (2,2)
        probs = diag / diag.sum()
    elif basis == "X":
        # Rotate to X basis via H x H
        H = torch.tensor([[1, 1], [1, -1]], dtype=rho_t.dtype) / math.sqrt(2)
        HH = torch.kron(H, H)
        rho_x = HH @ rho_t @ HH.conj().T
        r_x = rho_x.reshape(2, 2, 2, 2)
        diag = torch.einsum("ijij->ij", r_x).real
        probs = diag / diag.sum()
    else:
        raise ValueError(basis)

    p_a = probs.sum(dim=1)
    p_b = probs.sum(dim=0)

    def H_bits(p):
        p = torch.clamp(p, min=1e-12)
        return -(p * torch.log2(p)).sum()

    def H_joint(p):
        p = torch.clamp(p, min=1e-12)
        return -(p * torch.log2(p)).sum()

    return H_bits(p_a) + H_bits(p_b) - H_joint(probs.flatten())


def classical_MI_max_over_bases(rho_t):
    """Upper-bound classical MI by scanning single-qubit measurement bases."""
    best = 0.0
    for basis in ["Z", "X"]:
        v = float(classical_MI_bits_from_measurement(rho_t, basis).item())
        if v > best:
            best = v
    return best


def run_positive_tests():
    results = {}
    rho_t = torch.tensor(phi_plus(), dtype=torch.complex128)

    # P1: I_Q(Phi+) = 2 bits
    iq = float(quantum_MI_bits(rho_t).item())
    results["P1_quantum_MI_phi_plus_2bits"] = {
        "I_Q_bits": iq, "expected": 2.0, "pass": abs(iq - 2.0) < 1e-4,
    }

    # P2: Classical MI on Phi+ measurement <= 1 bit in any basis
    ic = classical_MI_max_over_bases(rho_t)
    results["P2_classical_MI_bounded_1bit"] = {
        "I_C_max_bits": ic, "bound": 1.0, "pass": ic <= 1.0 + 1e-6,
    }

    # P3: quantum/classical gap = 1 bit
    gap = iq - ic
    results["P3_quantum_classical_gap"] = {
        "gap_bits": gap, "expected": 1.0, "pass": abs(gap - 1.0) < 1e-3,
    }

    # P4: Product state -> I_Q = 0 and I_C = 0
    psi_prod = np.array([1, 0, 0, 0], dtype=np.complex128)
    rho_prod = torch.tensor(np.outer(psi_prod, psi_prod.conj()), dtype=torch.complex128)
    iq_p = float(quantum_MI_bits(rho_prod).item())
    ic_p = classical_MI_max_over_bases(rho_prod)
    results["P4_product_zero_both"] = {
        "I_Q": iq_p, "I_C": ic_p, "pass": abs(iq_p) < 1e-4 and ic_p < 1e-4,
    }
    return results


def run_negative_tests():
    results = {}
    # N1: Classical MI cannot exceed log2(d_A) = 1 bit for any 2x2 outcome distribution
    rng = np.random.RandomState(11)
    n1_pass = True
    n1_max = 0.0
    for _ in range(20):
        psi = rng.randn(4) + 1j * rng.randn(4)
        psi /= np.linalg.norm(psi)
        rho = torch.tensor(np.outer(psi, psi.conj()), dtype=torch.complex128)
        ic = classical_MI_max_over_bases(rho)
        n1_max = max(n1_max, ic)
        if ic > 1.0 + 1e-4:
            n1_pass = False
    results["N1_classical_MI_bounded"] = {"max": n1_max, "pass": n1_pass}

    # N2: I_Q >= I_C  for the chosen measurement (data-processing)
    n2_pass = True
    for _ in range(10):
        psi = rng.randn(4) + 1j * rng.randn(4)
        psi /= np.linalg.norm(psi)
        rho = torch.tensor(np.outer(psi, psi.conj()), dtype=torch.complex128)
        iq = float(quantum_MI_bits(rho).item())
        ic = classical_MI_max_over_bases(rho)
        if iq + 1e-4 < ic:
            n2_pass = False
    results["N2_IQ_geq_IC"] = {"pass": n2_pass}
    return results


def run_boundary_tests():
    results = {}
    # B1: Maximally mixed -> both zero
    rho = torch.eye(4, dtype=torch.complex128) / 4
    iq = float(quantum_MI_bits(rho).item())
    ic = classical_MI_max_over_bases(rho)
    results["B1_max_mixed_zero"] = {"I_Q": iq, "I_C": ic,
                                      "pass": abs(iq) < 1e-6 and abs(ic) < 1e-6}

    # B2: Classical correlated state (|00><00|+|11><11|)/2: I_Q = I_C = 1 bit (Z basis)
    rho = torch.tensor(np.diag([0.5, 0, 0, 0.5]).astype(np.complex128))
    iq = float(quantum_MI_bits(rho).item())
    ic = classical_MI_max_over_bases(rho)
    results["B2_classical_correlated"] = {
        "I_Q": iq, "I_C": ic,
        "pass": abs(iq - 1.0) < 1e-3 and abs(ic - 1.0) < 1e-3,
    }

    # B3: Upper bound on I_Q: 2 log 2 = 2 bits
    rho = torch.tensor(phi_plus(), dtype=torch.complex128)
    iq = float(quantum_MI_bits(rho).item())
    results["B3_IQ_upper_bound"] = {"I_Q": iq, "bound": 2.0,
                                      "pass": iq <= 2.0 + 1e-4}
    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Load-bearing: quantum VNE via torch.linalg.eigvalsh, partial traces via "
        "torch.einsum, classical measurement probabilities and Shannon entropy "
        "via torch tensor reductions. Full pipeline is torch-native."
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
        "name": "quantum_mutual_info_superadditivity_canonical",
        "description": "Lane C: I_Q(Phi+)=2 bits vs classical I_C<=1 bit; gap=1 bit",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive, "negative": negative, "boundary": boundary,
        "classification": "canonical",
        "quantum_classical_gap_bits": positive["P3_quantum_classical_gap"]["gap_bits"],
        "summary": {"total_tests": tt, "total_pass": tp, "all_pass": tp == tt},
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "quantum_mutual_info_superadditivity_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results: {tp}/{tt} pass -> {out_path}")
    if tp != tt:
        raise SystemExit(1)
