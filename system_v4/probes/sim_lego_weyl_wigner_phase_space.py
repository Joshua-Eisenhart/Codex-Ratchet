#!/usr/bin/env python3
"""
sim_lego_weyl_wigner_phase_space.py
------------------------------------
Pure math lego: Weyl-Wigner correspondence and phase-space quantum mechanics.

Implements the discrete Wigner function for qubit states on 2x2 phase space
using the Stratonovich-Weyl kernel formalism:

  Continuous:  W(x,p) = (1/pi) integral <x-y|rho|x+y> e^{2ipy} dy
  Discrete qubit: W(alpha) on Z_2 x Z_2  (4-point phase space)
  Stratonovich-Weyl kernel: A(n_hat) = (1/2)(I + sqrt(3) n_hat . sigma)

Tests:
  1. Discrete Wigner for |0>, |+>, maximally mixed
  2. Normalization: sum of W = 1 for all states
  3. Hudson's theorem: Gaussian-like states non-negative, others can go negative
  4. Wigner negativity as non-classicality witness
  5. Moyal star product: f star g via Moyal bracket

Classification: canonical (pytorch + sympy)
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": "not needed -- no graph structure"},
    "z3":         {"tried": False, "used": False, "reason": "not needed -- numerical + symbolic verification"},
    "cvc5":       {"tried": False, "used": False, "reason": "not needed"},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": "not needed -- Pauli algebra handled directly"},
    "geomstats":  {"tried": False, "used": False, "reason": "not needed"},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not needed"},
    "xgi":        {"tried": False, "used": False, "reason": "not needed"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed"},
    "gudhi":      {"tried": False, "used": False, "reason": "not needed"},
}

# --- Import pytorch ---
try:
    import torch
    torch.set_default_dtype(torch.float64)
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "core tensor ops: density matrices, Wigner functions, star products"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    raise SystemExit("PyTorch required for canonical sim.")

# --- Import sympy ---
try:
    import sympy as sp
    from sympy import (
        Matrix as SpMatrix, eye as sp_eye, sqrt as sp_sqrt,
        Rational, pi as sp_pi, symbols, conjugate, integrate, exp, I as sp_I
    )
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "exact symbolic Wigner function for |0> and star product verification"
except ImportError:
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = False
    TOOL_MANIFEST["sympy"]["reason"] = "not installed -- skipping symbolic cross-check"

SYMPY_AVAILABLE = TOOL_MANIFEST["sympy"]["used"]


def collect_tools_used():
    return sorted([name for name, meta in TOOL_MANIFEST.items() if meta["used"]])


def build_summary(results):
    record_total = 0
    explicit_total = 0
    explicit_passed = 0

    for section in ["positive", "negative", "boundary"]:
        for name, value in results[section].items():
            if not isinstance(value, dict):
                continue
            record_total += 1
            if "pass" in value:
                explicit_total += 1
                if value["pass"]:
                    explicit_passed += 1

    return {
        "record_total": record_total,
        "records_with_explicit_pass": explicit_total,
        "explicit_passed": explicit_passed,
        "explicit_failed": explicit_total - explicit_passed,
        "note": "Most Weyl-Wigner checks report named boolean invariants inside each record rather than a top-level pass field.",
    }


# =====================================================================
# PAULI MATRICES (torch, complex128)
# =====================================================================

I2 = torch.eye(2, dtype=torch.complex128)
sigma_x = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
sigma_y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
sigma_z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
PAULI = [sigma_x, sigma_y, sigma_z]


# =====================================================================
# CORE: Discrete Wigner function for qubits
# =====================================================================

def density_matrix(state_vec: torch.Tensor) -> torch.Tensor:
    """Pure state |psi> -> rho = |psi><psi|."""
    psi = state_vec.to(torch.complex128).reshape(-1, 1)
    return psi @ psi.conj().T


def bloch_vector(rho: torch.Tensor) -> torch.Tensor:
    """Extract Bloch vector (r_x, r_y, r_z) from single-qubit rho."""
    rx = torch.trace(rho @ sigma_x).real
    ry = torch.trace(rho @ sigma_y).real
    rz = torch.trace(rho @ sigma_z).real
    return torch.tensor([rx, ry, rz], dtype=torch.float64)


def _build_phase_point_ops():
    """
    Build the 4 phase-space point operators for the discrete qubit Wigner function.

    Uses the Wootters construction for d=2:
      A_{alpha} = (1/2)(I + (1/sqrt{3}) s_alpha . sigma)

    where s_alpha are the 4 tetrahedral sign patterns.

    Properties:
      sum_alpha A_alpha = 2I       (completeness)
      Tr(A_alpha) = 1              (unit trace)
      Tr(A_i A_j) = 1/3  (i!=j)   (Stratonovich-Weyl covariance)

    The normalized Wigner function is:
      W(alpha) = (1/d) Tr(rho A_alpha) = (1/2) Tr(rho A_alpha)
    so that sum_alpha W(alpha) = 1.
    """
    s3 = 1.0 / np.sqrt(3.0)
    signs = torch.tensor([
        [+1, +1, +1],   # (0,0)
        [+1, -1, -1],   # (0,1)
        [-1, +1, -1],   # (1,0)
        [-1, -1, +1],   # (1,1)
    ], dtype=torch.float64)

    ops = []
    for i in range(4):
        n_dot_sigma = sum(signs[i, k].item() * PAULI[k] for k in range(3))
        A_alpha = 0.5 * (I2 + s3 * n_dot_sigma)
        ops.append(A_alpha)
    return ops, signs


PHASE_POINT_OPS, TETRAHEDRAL_SIGNS = _build_phase_point_ops()


def discrete_wigner_qubit(rho: torch.Tensor) -> torch.Tensor:
    """
    Discrete Wigner function on Z_2 x Z_2 phase space for a single qubit.

    W(alpha) = (1/d) Tr(rho A_alpha) = (1/2) Tr(rho A_alpha)

    Normalized so sum_alpha W(alpha) = 1 (quasi-probability distribution).
    """
    d = 2  # qubit dimension
    W = torch.zeros(4, dtype=torch.float64)
    for i, A in enumerate(PHASE_POINT_OPS):
        W[i] = (1.0 / d) * torch.trace(rho @ A).real
    return W


def wigner_negativity(W: torch.Tensor) -> float:
    """
    Wigner negativity: sum of absolute values minus 1.
    N(rho) = (sum |W(alpha)| - 1) = amount of negative volume.
    Zero for non-negative Wigner functions.
    """
    return (torch.sum(torch.abs(W)) - 1.0).item()


# =====================================================================
# CORE: Moyal star product (discrete, qubit)
# =====================================================================

def phase_space_function(rho: torch.Tensor) -> torch.Tensor:
    """Return the 4-component Wigner representation of rho."""
    return discrete_wigner_qubit(rho)


def star_product_qubit(W_f: torch.Tensor, W_g: torch.Tensor) -> torch.Tensor:
    """
    Moyal star product on discrete qubit phase space.

    For qubit density matrices rho, sigma:
      W_{rho sigma}(alpha) = sum_{beta} K(alpha, beta) W_rho(beta) W_sigma(gamma)

    The star product kernel for d=2 Stratonovich-Weyl:
      (f star g)(alpha) = Tr(A_alpha rho_f rho_g)

    We reconstruct rho from W, multiply, then re-Wignerize.
    """
    rho_f = reconstruct_rho(W_f)
    rho_g = reconstruct_rho(W_g)
    rho_fg = rho_f @ rho_g
    # Wigner of the (unnormalized) operator product
    return discrete_wigner_qubit(rho_fg)


def reconstruct_rho(W: torch.Tensor) -> torch.Tensor:
    """
    Reconstruct density matrix from discrete Wigner function.

    Given W(alpha) = (1/d) Tr(rho A_alpha), the inverse is:
      rho = d * sum_alpha W(alpha) * A_alpha
          = 2 * sum_alpha W(alpha) * A_alpha

    Verify: Tr(rho) = 2 * sum W(alpha) * Tr(A_alpha) = 2 * 1 * 1 = 2
    Wait -- we need the dual frame. Since sum A = 2I:
      rho = sum_alpha W(alpha) * d * A_alpha
    gives Tr(rho) = d * sum W * 1 = 2 * 1 = 2. That's wrong.

    Correct inverse: A_alpha are an overcomplete frame with sum A = dI.
    The dual frame element is B_alpha = A_alpha (self-dual for this kernel).
    rho = sum_alpha W(alpha) * B_alpha where B_alpha = A_alpha.
    Check: (1/d) Tr(rho A_beta) = (1/d) sum_alpha W(alpha) Tr(A_alpha A_beta).
    For tetrahedral kernel: Tr(A_i A_j) = delta_{ij} + (1-delta_{ij})/3.
    Tr(A_i A_i) = Tr((1/4)(I + (2/sqrt3) n.sigma + (1/3) I)) = Tr((1/3)I + ...)

    Actually, let's just use the Bloch decomposition which is exact:
      rho = (1/2)(I + r . sigma)
      W(alpha) = (1/2)(1/2)(1 + (1/sqrt3) s_alpha . r) = (1/4)(1 + (1/sqrt3) s_alpha . r)
    So r_k = sqrt(3) * (1/4) sum_alpha s_alpha_k * (4*W(alpha) - 1)
    Actually simpler: from the 4 values of W, extract r via:
      sum_alpha s_alpha_k W(alpha) = (1/4) sum_alpha s_alpha_k + (1/(4 sqrt3)) r . (sum_alpha s_alpha_k s_alpha)
    Since sum_alpha s_alpha_k = 0 and sum_alpha s_{alpha,k} s_{alpha,j} = 4 delta_{kj}:
      sum_alpha s_alpha_k W(alpha) = (1/(4 sqrt3)) r_k * 4 = r_k / sqrt(3)
    So r_k = sqrt(3) * sum_alpha s_{alpha,k} * W(alpha).
    """
    s3 = np.sqrt(3.0)
    r = torch.zeros(3, dtype=torch.float64)
    for k in range(3):
        for i in range(4):
            r[k] += TETRAHEDRAL_SIGNS[i, k].item() * W[i].item()
        r[k] *= s3

    rho = 0.5 * (I2 + sum(r[k].item() * PAULI[k] for k in range(3)))
    return rho


# =====================================================================
# SYMPY: Continuous Wigner function for |0> (harmonic oscillator basis)
# =====================================================================

def symbolic_wigner_zero():
    """
    Compute W(x,p) for the vacuum |0> of harmonic oscillator.
    psi_0(x) = (1/pi)^{1/4} exp(-x^2/2)
    W(x,p) = (1/pi) exp(-x^2 - p^2)

    This is non-negative everywhere (Hudson's theorem).
    Returns dict with symbolic expression and verification.
    """
    if not SYMPY_AVAILABLE:
        return {"skipped": True, "reason": "sympy not available"}

    x, p, y = symbols('x p y', real=True)

    # Ground state wavefunction
    psi_0 = sp.pi ** (sp.Rational(-1, 4)) * exp(-x ** 2 / 2)

    # Wigner integrand: (1/pi) psi*(x+y) psi(x-y) e^{2ipy}
    psi_plus = psi_0.subs(x, x - y)
    psi_minus = conjugate(psi_0.subs(x, x + y))

    integrand = (1 / sp.pi) * psi_minus * psi_plus * exp(2 * sp_I * p * y)

    # Perform the integral over y
    W_symbolic = integrate(integrand, (y, -sp.oo, sp.oo))
    W_simplified = sp.simplify(W_symbolic)

    # Verify non-negativity: the result should be (1/pi) exp(-x^2 - p^2)
    expected = (1 / sp.pi) * exp(-x ** 2 - p ** 2)
    diff = sp.simplify(W_simplified - expected)

    # Verify normalization: integral over all phase space = 1
    norm = integrate(integrate(expected, (x, -sp.oo, sp.oo)), (p, -sp.oo, sp.oo))

    return {
        "W_symbolic": str(W_simplified),
        "expected": str(expected),
        "difference_from_expected": str(diff),
        "match": bool(diff == 0),
        "normalization": str(sp.simplify(norm)),
        "normalization_is_one": bool(sp.simplify(norm - 1) == 0),
        "non_negative_everywhere": True,  # (1/pi)e^{-x^2-p^2} > 0 for all x,p
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ------ Test 1: |0> Wigner function ------
    ket_0 = torch.tensor([1.0, 0.0], dtype=torch.complex128)
    rho_0 = density_matrix(ket_0)
    W_0 = discrete_wigner_qubit(rho_0)

    # |0> Bloch vector = (0,0,1), so W values should be specific
    results["wigner_ket0"] = {
        "W_values": W_0.tolist(),
        "sum_equals_1": abs(W_0.sum().item() - 1.0) < 1e-12,
        "all_non_negative": bool(torch.all(W_0 >= -1e-12)),
        "bloch_vector": bloch_vector(rho_0).tolist(),
    }

    # ------ Test 2: |1> Wigner function ------
    ket_1 = torch.tensor([0.0, 1.0], dtype=torch.complex128)
    rho_1 = density_matrix(ket_1)
    W_1 = discrete_wigner_qubit(rho_1)

    results["wigner_ket1"] = {
        "W_values": W_1.tolist(),
        "sum_equals_1": abs(W_1.sum().item() - 1.0) < 1e-12,
        "all_non_negative": bool(torch.all(W_1 >= -1e-12)),
        "bloch_vector": bloch_vector(rho_1).tolist(),
    }

    # ------ Test 3: |+> = (|0>+|1>)/sqrt(2) ------
    # Note: for single-qubit tetrahedral Wigner, ALL states have non-negative W
    # because max |n_hat . r| = 1/sqrt(3) for |r|=1, so W >= (1/4)(1-1/sqrt(3)) > 0.
    # Wigner negativity for qubits requires multi-qubit entangled states or
    # alternative (non-tetrahedral) kernel choices.
    ket_plus = torch.tensor([1.0, 1.0], dtype=torch.complex128) / np.sqrt(2)
    rho_plus = density_matrix(ket_plus)
    W_plus = discrete_wigner_qubit(rho_plus)
    neg_plus = wigner_negativity(W_plus)

    results["wigner_ket_plus"] = {
        "W_values": W_plus.tolist(),
        "sum_equals_1": abs(W_plus.sum().item() - 1.0) < 1e-12,
        "all_non_negative": bool(torch.all(W_plus >= -1e-12)),
        "wigner_negativity": neg_plus,
        "bloch_vector": bloch_vector(rho_plus).tolist(),
        "note": "single-qubit tetrahedral Wigner is non-negative for ALL states",
    }

    # ------ Test 4: Maximally mixed state = I/2 ------
    rho_mixed = I2 / 2.0
    W_mixed = discrete_wigner_qubit(rho_mixed)

    results["wigner_maximally_mixed"] = {
        "W_values": W_mixed.tolist(),
        "sum_equals_1": abs(W_mixed.sum().item() - 1.0) < 1e-12,
        "all_equal_quarter": bool(torch.allclose(W_mixed, torch.full((4,), 0.25))),
        "wigner_negativity": wigner_negativity(W_mixed),
        "bloch_vector": bloch_vector(rho_mixed).tolist(),
    }

    # ------ Test 5: Normalization for random states ------
    norm_checks = []
    for _ in range(20):
        psi = torch.randn(2, dtype=torch.complex128)
        psi = psi / torch.norm(psi)
        rho = density_matrix(psi)
        W = discrete_wigner_qubit(rho)
        norm_checks.append(abs(W.sum().item() - 1.0) < 1e-10)

    results["normalization_20_random"] = {
        "all_normalized": all(norm_checks),
        "count_passed": sum(norm_checks),
    }

    # ------ Test 6: Reconstruction roundtrip ------
    # rho -> W -> rho_reconstructed should match
    rho_test = density_matrix(ket_plus)
    W_test = discrete_wigner_qubit(rho_test)
    rho_recon = reconstruct_rho(W_test)
    recon_error = torch.norm(rho_test - rho_recon).item()

    results["reconstruction_roundtrip"] = {
        "frobenius_error": recon_error,
        "pass": recon_error < 1e-10,
    }

    # ------ Test 7: Star product (Moyal) ------
    # For pure state: rho^2 = rho, so star(W_rho, W_rho) should give W_rho
    W_0_star_0 = star_product_qubit(W_0, W_0)
    star_self_error = torch.norm(W_0_star_0 - W_0).item()

    results["star_product_idempotent"] = {
        "W_rho_star_W_rho": W_0_star_0.tolist(),
        "W_rho_original": W_0.tolist(),
        "error": star_self_error,
        "pass_idempotent": star_self_error < 1e-10,
    }

    # Star product of orthogonal states should give zero operator
    W_01 = star_product_qubit(W_0, W_1)
    results["star_product_orthogonal"] = {
        "W_0_star_W_1": W_01.tolist(),
        "trace_product": sum(W_01.tolist()),
        "trace_near_zero": abs(sum(W_01.tolist())) < 1e-10,
    }

    # ------ Test 8: Wigner negativity for single-qubit states ------
    # For tetrahedral kernel, ALL single-qubit states have non-negative W.
    # Negativity = sum|W| - 1 = 0 for all of them.
    neg_0 = wigner_negativity(W_0)
    neg_mixed = wigner_negativity(W_mixed)

    results["negativity_single_qubit"] = {
        "neg_ket0": neg_0,
        "neg_ket_plus": neg_plus,
        "neg_mixed": neg_mixed,
        "all_zero_negativity": all(n < 1e-10 for n in [neg_0, neg_plus, neg_mixed]),
        "note": "tetrahedral kernel: all single-qubit states non-negative",
    }

    # ------ Test 8b: 2-qubit Wigner negativity (Bell state) ------
    # For 2 qubits, use tensor product of phase-point operators.
    # Bell state |Phi+> = (|00>+|11>)/sqrt(2) shows negativity.
    bell_plus = torch.zeros(4, dtype=torch.complex128)
    bell_plus[0] = 1.0 / np.sqrt(2)  # |00>
    bell_plus[3] = 1.0 / np.sqrt(2)  # |11>
    rho_bell = bell_plus.reshape(4, 1) @ bell_plus.reshape(1, 4).conj()

    # 2-qubit discrete Wigner: 16-point phase space
    # A_{alpha,beta} = A_alpha tensor A_beta
    W_bell = torch.zeros(16, dtype=torch.float64)
    d2 = 4  # dimension for 2 qubits
    idx = 0
    for A_i in PHASE_POINT_OPS:
        for A_j in PHASE_POINT_OPS:
            A_ij = torch.kron(A_i, A_j)
            W_bell[idx] = (1.0 / d2) * torch.trace(rho_bell @ A_ij).real
            idx += 1

    neg_bell = (torch.sum(torch.abs(W_bell)) - 1.0).item()

    results["negativity_2qubit_bell"] = {
        "W_values": W_bell.tolist(),
        "sum_equals_1": abs(W_bell.sum().item() - 1.0) < 1e-12,
        "has_negative_entry": bool(torch.any(W_bell < -1e-12)),
        "wigner_negativity": neg_bell,
        "bell_state_shows_negativity": neg_bell > 1e-10,
        "min_W": W_bell.min().item(),
    }

    # ------ Test 9: Symbolic Wigner for |0> (continuous) ------
    results["symbolic_wigner_vacuum"] = symbolic_wigner_zero()

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    results = {}

    # ------ Neg 1: Invalid density matrix (not PSD, but Tr=1) -> Wigner sums to 1
    # but values can exceed physical range
    rho_bad = torch.tensor([[2.0, 0], [0, -1.0]], dtype=torch.complex128)
    W_bad = discrete_wigner_qubit(rho_bad)

    results["invalid_rho_not_psd"] = {
        "W_values": W_bad.tolist(),
        "sum": W_bad.sum().item(),
        "sum_equals_1": abs(W_bad.sum().item() - 1.0) < 1e-12,
        "has_value_exceeding_physical_range": bool(torch.any(torch.abs(W_bad) > 0.5 + 1e-10)),
        "note": "Tr(rho)=1 but not PSD; Wigner sums to 1 but entries exceed physical bounds",
    }

    # ------ Neg 2: Zero matrix -> Wigner should be all zeros ------
    rho_zero = torch.zeros(2, 2, dtype=torch.complex128)
    W_zero = discrete_wigner_qubit(rho_zero)

    results["zero_matrix_wigner"] = {
        "W_values": W_zero.tolist(),
        "all_zero": bool(torch.allclose(W_zero, torch.zeros(4))),
    }

    # ------ Neg 3: Star product non-commutativity ------
    # Use |0> and |+i> = (|0>+i|1>)/sqrt(2) which have projectors that
    # don't commute (they differ along y-axis of Bloch sphere).
    ket_0 = torch.tensor([1.0, 0.0], dtype=torch.complex128)
    ket_yi = torch.tensor([1.0, 1j], dtype=torch.complex128) / np.sqrt(2)
    W_z = discrete_wigner_qubit(density_matrix(ket_0))
    W_y = discrete_wigner_qubit(density_matrix(ket_yi))

    W_zy = star_product_qubit(W_z, W_y)
    W_yz = star_product_qubit(W_y, W_z)
    commutator_norm = torch.norm(W_zy - W_yz).item()

    results["star_product_non_commutative"] = {
        "W_0_star_yi": W_zy.tolist(),
        "W_yi_star_0": W_yz.tolist(),
        "commutator_norm": commutator_norm,
        "non_commutative": commutator_norm > 1e-10,
        "note": "|0> and |+i> projectors don't commute; star product reflects this",
    }

    # ------ Neg 4: Reconstruction of unphysical W fails density matrix check ------
    W_unphys = torch.tensor([1.0, 1.0, -0.5, -0.5], dtype=torch.float64)
    rho_unphys = reconstruct_rho(W_unphys)
    eigenvalues = torch.linalg.eigvalsh(rho_unphys.real)

    results["unphysical_wigner_reconstruction"] = {
        "input_W": W_unphys.tolist(),
        "reconstructed_eigenvalues": eigenvalues.tolist(),
        "has_negative_eigenvalue": bool(torch.any(eigenvalues < -1e-10)),
        "not_valid_state": bool(torch.any(eigenvalues < -1e-10)),
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ------ Boundary 1: States near poles of Bloch sphere ------
    # As state approaches |0>, negativity should approach 0
    epsilons = [1e-1, 1e-3, 1e-6, 1e-10]
    neg_values = []
    for eps in epsilons:
        psi = torch.tensor([1.0, eps], dtype=torch.complex128)
        psi = psi / torch.norm(psi)
        rho = density_matrix(psi)
        W = discrete_wigner_qubit(rho)
        neg_values.append(wigner_negativity(W))

    results["approach_pole_negativity"] = {
        "epsilons": epsilons,
        "negativities": neg_values,
        "monotone_decreasing": all(neg_values[i] >= neg_values[i + 1] - 1e-12
                                   for i in range(len(neg_values) - 1)),
    }

    # ------ Boundary 2: Numerical precision of reconstruction ------
    errors = []
    for _ in range(50):
        psi = torch.randn(2, dtype=torch.complex128)
        psi = psi / torch.norm(psi)
        rho = density_matrix(psi)
        W = discrete_wigner_qubit(rho)
        rho_back = reconstruct_rho(W)
        errors.append(torch.norm(rho - rho_back).item())

    results["reconstruction_precision_50"] = {
        "max_error": max(errors),
        "mean_error": sum(errors) / len(errors),
        "all_below_1e10": all(e < 1e-10 for e in errors),
    }

    # ------ Boundary 3: Wigner of maximally entangled (reduced state) ------
    # Tr_B(|Bell+>) = I/2 -> should match maximally mixed Wigner
    rho_reduced = I2 / 2.0
    W_reduced = discrete_wigner_qubit(rho_reduced)

    results["bell_reduced_is_mixed"] = {
        "W_values": W_reduced.tolist(),
        "all_quarter": bool(torch.allclose(W_reduced, torch.full((4,), 0.25))),
    }

    # ------ Boundary 4: Phase-space point operators sum to 2I ------
    A_sum = torch.zeros(2, 2, dtype=torch.complex128)
    traces = []
    for A in PHASE_POINT_OPS:
        A_sum += A
        traces.append(torch.trace(A).real.item())

    results["point_operators_sum_to_2I"] = {
        "sum_matrix_real": A_sum.real.tolist(),
        "matches_2I": bool(torch.allclose(A_sum, 2.0 * I2, atol=1e-12)),
        "individual_traces": traces,
        "all_traces_are_1": all(abs(t - 1.0) < 1e-12 for t in traces),
    }

    # ------ Boundary 5: Stratonovich-Weyl covariance ------
    # A_alpha are related by tetrahedral symmetry; verify pairwise traces
    pairwise_traces = []
    for i in range(4):
        for j in range(i + 1, 4):
            tr = torch.trace(PHASE_POINT_OPS[i] @ PHASE_POINT_OPS[j]).real.item()
            pairwise_traces.append(tr)

    # For tetrahedral kernel: Tr(A_i A_j) = 1/3 for i != j
    results["stratonovich_weyl_pairwise_traces"] = {
        "traces": pairwise_traces,
        "all_equal_one_third": all(abs(t - 1.0 / 3.0) < 1e-12 for t in pairwise_traces),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "Weyl-Wigner Phase Space -- Discrete Qubit Wigner Function",
        "probe": "lego_weyl_wigner_phase_space",
        "purpose": "Verify discrete qubit Wigner kernels, normalization, negativity, and Stratonovich-Weyl structure",
        "tool_manifest": TOOL_MANIFEST,
        "tools_used": collect_tools_used(),
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    results["summary"] = build_summary(results)

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_weyl_wigner_phase_space_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
