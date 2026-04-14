#!/usr/bin/env python3
"""Canonical: Superdense coding channel capacity = 2 bits/qubit vs classical 1 bit/qubit.

Protocol:
  Pre-shared entanglement |Phi+>_AB = (|00>+|11>)/sqrt(2).
  Alice encodes 2 classical bits into one of {I, X, Z, ZX} applied to A.
  After she transmits A to Bob (one qubit), Bob measures AB in the Bell basis.
  The four encodings map |Phi+> to the four orthogonal Bell states -> 2 bits
  of mutual information.

Holevo for a single qubit channel without pre-shared entanglement: chi <= 1.
Superdense coding with entanglement: I(X;Y) = 2 (bits per qubit transmitted).

Positive: pytorch numerical construction of the four encoded density matrices,
  computation of the average rho_bar, and S(rho_bar) - avg S(rho_i) -> chi = 2.
Negative: without the shared entangled resource (encode on |0>_A instead),
  the four signal states collapse to at most 2 orthogonal states -> chi <= 1.
Boundary: slight depolarization of the shared Bell state reduces capacity
  smoothly but remains > 1 for small noise.

load_bearing: pytorch (all density matrices, partial traces, and the
von-Neumann entropy S(rho) = -tr(rho log rho) via torch.linalg.eigvalsh are
computed as torch tensors; the Holevo capacity chi is the torch-computed
quantum/classical gap).
"""
import json
import math
import os

import numpy as np

classification = "canonical"
divergence_log = None

TOOL_MANIFEST = {
    "numpy":   {"tried": True,  "used": True,  "reason": "scalar bookkeeping"},
    "pytorch": {"tried": False, "used": False, "reason": "placeholder -- filled below"},
    "sympy":   {"tried": False, "used": False, "reason": "not required -- numeric channel capacity"},
    "z3":      {"tried": False, "used": False, "reason": "not required -- capacity is numeric"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy":   "supportive",
    "pytorch": "load_bearing",
    "sympy":   None,
    "z3":      None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "density matrices as complex128 tensors; torch.linalg.eigvalsh "
        "computes von-Neumann entropies; Holevo capacity chi = S(rho_bar) - "
        "avg S(rho_i) is the torch-native quantum/classical gap"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    torch = None  # type: ignore


# ---------------------------------------------------------------------------
# Superdense coding machinery (torch)
# ---------------------------------------------------------------------------

def _pauli():
    I = torch.tensor([[1, 0], [0, 1]], dtype=torch.complex128)
    X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    return I, X, Z


def _phi_plus_rho():
    v = torch.tensor([[1.0], [0.0], [0.0], [1.0]], dtype=torch.complex128) / math.sqrt(2.0)
    return v @ v.conj().T


def _encoded_rhos():
    """Four Bell states as encoded density matrices on AB after Alice's operation."""
    rho_in = _phi_plus_rho()
    I, X, Z = _pauli()
    ops_A = [I, X, Z, Z @ X]
    rhos = []
    for U_A in ops_A:
        U = torch.kron(U_A, I)
        rho_out = U @ rho_in @ U.conj().T
        rhos.append(rho_out)
    return rhos


def _von_neumann_entropy(rho):
    """S(rho) = -tr(rho log2 rho) computed from eigenvalues."""
    # Hermitianize to kill numerical drift.
    rho_h = 0.5 * (rho + rho.conj().T)
    eigs = torch.linalg.eigvalsh(rho_h).real
    # Clamp negatives from numerical noise; log2(0) -> 0 contribution.
    eigs = torch.clamp(eigs, min=0.0)
    eps = 1e-15
    log2e = eigs * torch.log2(eigs + eps)
    # Where eigs==0, contribution must be 0 (not eps*log2(eps)).
    log2e = torch.where(eigs > 0, eigs * torch.log2(eigs.clamp(min=eps)),
                        torch.zeros_like(eigs))
    return -torch.sum(log2e).real


def _holevo_capacity(rhos, probs=None):
    if probs is None:
        n = len(rhos)
        probs = [1.0 / n] * n
    rho_bar = sum(p * r for p, r in zip(probs, rhos))
    S_bar = _von_neumann_entropy(rho_bar)
    avg_S = sum(p * _von_neumann_entropy(r) for p, r in zip(probs, rhos))
    return float((S_bar - avg_S).item())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

CLASSICAL_BOUND = 1.0   # bits per qubit without pre-shared entanglement (Holevo)
QUANTUM_BOUND = 2.0     # bits per qubit via superdense coding
TOL = 1e-6


def run_positive_tests():
    results = {}
    if torch is None:
        results["torch_available"] = False
        return results

    rhos = _encoded_rhos()
    # Orthogonality check: <phi_i | phi_j> should be 0 for i != j (Bell basis).
    overlaps = []
    ortho = True
    for i in range(4):
        for j in range(i + 1, 4):
            ov = float((rhos[i] * rhos[j]).sum().real.item())
            overlaps.append(ov)
            # tr(rho_i rho_j) = |<phi_i|phi_j>|^2 -> 0 for orthogonal pure states.
            if abs(ov) > 1e-9:
                ortho = False
    results["max_pairwise_overlap"] = max((abs(x) for x in overlaps), default=0.0)
    results["bell_basis_orthogonal"] = ortho

    # Holevo capacity with uniform prior over the 4 encoded states.
    chi = _holevo_capacity(rhos)
    results["holevo_capacity_chi"] = chi
    results["chi_ge_quantum_bound_minus_tol"] = chi >= QUANTUM_BOUND - 1e-6
    results["chi_gt_classical_bound"] = chi > CLASSICAL_BOUND + 1e-6
    results["quantum_classical_gap"] = chi - CLASSICAL_BOUND

    # Entropy of the average state: should be log2(4) = 2 (maximally mixed on 2 qubits
    # = I/4 since the four Bell states form an orthonormal basis).
    rho_bar = sum(0.25 * r for r in rhos)
    S_bar = float(_von_neumann_entropy(rho_bar).item())
    results["S_rho_bar"] = S_bar
    results["S_rho_bar_equals_2"] = abs(S_bar - 2.0) < 1e-6

    # Each encoded rho is pure: S = 0.
    S_each = [float(_von_neumann_entropy(r).item()) for r in rhos]
    results["S_each_encoded"] = S_each
    results["each_encoded_state_pure"] = all(abs(s) < 1e-6 for s in S_each)
    return results


def run_negative_tests():
    results = {}
    if torch is None:
        results["torch_available"] = False
        return results

    # Without pre-shared entanglement: Alice applies {I, X, Z, ZX} to |0>_A
    # and sends one qubit. Resulting signals:
    #   I|0> = |0>, X|0> = |1>, Z|0> = |0>, ZX|0> = -|1>  (3rd and 4th collapse to {0,1}).
    # -> at most 2 orthogonal signal states -> chi <= 1 bit.
    I, X, Z = _pauli()
    v0 = torch.tensor([[1.0], [0.0]], dtype=torch.complex128)
    ops_A = [I, X, Z, Z @ X]
    signal_rhos = []
    for U in ops_A:
        v = U @ v0
        signal_rhos.append(v @ v.conj().T)

    chi_no_ent = _holevo_capacity(signal_rhos)
    results["chi_without_entanglement"] = chi_no_ent
    results["chi_no_ent_le_classical"] = chi_no_ent <= CLASSICAL_BOUND + 1e-6
    results["chi_no_ent_lt_quantum_bound"] = chi_no_ent < QUANTUM_BOUND - 1e-6

    # Identity ensemble (all four encodings are I): chi must be 0.
    rhos_identity = [signal_rhos[0], signal_rhos[0], signal_rhos[0], signal_rhos[0]]
    chi_identity = _holevo_capacity(rhos_identity)
    results["chi_identity_ensemble"] = chi_identity
    results["chi_identity_is_zero"] = abs(chi_identity) < 1e-6

    # Sanity: classical bound strictly below quantum bound.
    results["classical_lt_quantum"] = CLASSICAL_BOUND < QUANTUM_BOUND
    return results


def run_boundary_tests():
    results = {}
    if torch is None:
        results["torch_available"] = False
        return results

    # Depolarize the shared Bell state: rho = (1-p) |Phi+><Phi+| + p I/4.
    # Apply Alice's four encodings; compute chi as a function of p.
    rho_phi = _phi_plus_rho()
    I_AB = torch.eye(4, dtype=torch.complex128)
    I, X, Z = _pauli()
    ops_A = [I, X, Z, Z @ X]

    chis = {}
    for p in (0.0, 0.05, 0.1, 0.25):
        rho = (1 - p) * rho_phi + p * (I_AB / 4.0)
        rhos = []
        for U_A in ops_A:
            U = torch.kron(U_A, I)
            rhos.append(U @ rho @ U.conj().T)
        chi = _holevo_capacity(rhos)
        chis[f"p={p}"] = chi
    results["chi_vs_depolarization"] = chis
    # Small noise still beats the classical bound.
    results["chi_at_small_noise_gt_classical"] = chis["p=0.05"] > CLASSICAL_BOUND
    # At p=0 we recover the ideal value 2.
    results["chi_at_zero_noise_equals_two"] = abs(chis["p=0.0"] - 2.0) < 1e-6

    # Monotone decrease with p (within the tested range).
    ps = [0.0, 0.05, 0.1, 0.25]
    vals = [chis[f"p={p}"] for p in ps]
    monotone = all(vals[i] >= vals[i + 1] - 1e-9 for i in range(len(vals) - 1))
    results["chi_monotone_decreasing_in_noise"] = monotone
    return results


def _all_bool_pass(d):
    for v in d.values():
        if isinstance(v, bool) and not v:
            return False
    return True


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = _all_bool_pass(pos) and _all_bool_pass(neg) and _all_bool_pass(bnd)

    gap = {
        "classical_holevo_bound_bits_per_qubit": CLASSICAL_BOUND,
        "superdense_bound_bits_per_qubit": QUANTUM_BOUND,
        "chi_superdense_measured": pos.get("holevo_capacity_chi"),
        "quantum_classical_gap_bits": (pos.get("holevo_capacity_chi") or 0.0) - CLASSICAL_BOUND,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "superdense_coding_capacity_canonical_results.json")

    payload = {
        "name": "superdense_coding_capacity_canonical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "gap": gap,
            "classical_baseline_cited": "Holevo bound 1 bit / qubit without pre-shared entanglement",
            "measured_quantum_value": pos.get("holevo_capacity_chi"),
        },
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"all_pass={all_pass} chi={pos.get('holevo_capacity_chi')} -> {out_path}")
