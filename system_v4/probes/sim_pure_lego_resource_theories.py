#!/usr/bin/env python3
"""
Pure Lego: Quantum Resource Theories — Coherence, Entanglement, Athermality
===========================================================================
Status: [Pure lego — no engine, numpy/scipy only]

Unified framework: every resource theory has three ingredients:
  (1) Free states   — the cheap, boring states
  (2) Free operations — channels that cannot create the resource
  (3) Resource monotones — quantifiers that never increase under free ops

Implemented resource theories:

  COHERENCE
    Free states:  diagonal (incoherent) in computational basis
    Free ops:     incoherent channels (Kraus ops diagonal up to permutation)
    Monotones:    l1 norm of coherence, relative entropy of coherence

  ENTANGLEMENT
    Free states:  separable (product) states
    Free ops:     LOCC (local operations + classical communication)
    Monotones:    concurrence, negativity, entanglement of formation

  ATHERMALITY
    Free states:  thermal Gibbs states rho_beta = exp(-beta H)/Z
    Free ops:     thermal operations (energy-preserving unitaries on sys+bath)
    Monotones:    non-equilibrium free energy, extractable work

  INTERCONVERSION
    Coherence -> Entanglement via CNOT:
      |+>|0> has C_l1 = 1, C_ent = 0
      CNOT|+0> = Bell Phi+ has C_l1 = 0 (locally), C_ent = 1
    Resource theories are FUNGIBLE under the right operations.

All quantities computed with explicit matrix operations.
No engine imports. Pure numpy/scipy.
"""

import numpy as np
from scipy.linalg import expm, logm
import json
import os

# =====================================================================
# INFRASTRUCTURE
# =====================================================================

class _NumpyEncoder(json.JSONEncoder):
    """Handle numpy scalars that vanilla json chokes on."""
    def default(self, obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)

# =====================================================================
# CONSTANTS & BASIS STATES
# =====================================================================

SIGMA_X = np.array([[0.0, 1.0], [1.0, 0.0]])
SIGMA_Y = np.array([[0.0, -1j], [1j, 0.0]])
SIGMA_Z = np.array([[1.0, 0.0], [0.0, -1.0]])
I2 = np.eye(2)

KET_0 = np.array([1.0, 0.0], dtype=complex)
KET_1 = np.array([0.0, 1.0], dtype=complex)
KET_PLUS = (KET_0 + KET_1) / np.sqrt(2)
KET_MINUS = (KET_0 - KET_1) / np.sqrt(2)

# Two-qubit basis
KET_00 = np.kron(KET_0, KET_0)
KET_01 = np.kron(KET_0, KET_1)
KET_10 = np.kron(KET_1, KET_0)
KET_11 = np.kron(KET_1, KET_1)

# Bell states
PHI_PLUS = (KET_00 + KET_11) / np.sqrt(2)
PHI_MINUS = (KET_00 - KET_11) / np.sqrt(2)
PSI_PLUS = (KET_01 + KET_10) / np.sqrt(2)
PSI_MINUS = (KET_01 - KET_10) / np.sqrt(2)

# CNOT gate (control=qubit 0, target=qubit 1)
CNOT = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
], dtype=complex)

KB = 1.0  # Boltzmann constant in natural units

# =====================================================================
# UTILITY FUNCTIONS
# =====================================================================

def ket_to_dm(psi):
    """Pure state vector -> density matrix."""
    psi = np.asarray(psi, dtype=complex).reshape(-1, 1)
    return psi @ psi.conj().T


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho ln rho). Uses eigenvalues for numerical safety."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals)))


def von_neumann_entropy_ln(rho):
    """S(rho) using natural log."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log(evals)))


def partial_trace(rho_ab, dim_a, dim_b, trace_out="B"):
    """Partial trace of bipartite rho_ab.  trace_out='B' keeps A."""
    rho = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    if trace_out == "B":
        return np.trace(rho, axis1=1, axis2=3)
    else:
        return np.trace(rho, axis1=0, axis2=2)


def partial_transpose(rho_ab, dim_a, dim_b):
    """Partial transpose w.r.t. subsystem B."""
    rho = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    # Transpose indices for B: swap axes 1 and 3
    rho_pt = rho.transpose(0, 3, 2, 1)
    return rho_pt.reshape(dim_a * dim_b, dim_a * dim_b)


# =====================================================================
# COHERENCE RESOURCE THEORY
# =====================================================================

def is_incoherent(rho, tol=1e-10):
    """Check if rho is diagonal (incoherent in computational basis)."""
    off_diag = rho.copy()
    np.fill_diagonal(off_diag, 0)
    return float(np.sum(np.abs(off_diag))) < tol


def dephase(rho):
    """Apply full dephasing: kill all off-diagonal elements.
    This is the canonical incoherent operation (free op for coherence)."""
    return np.diag(np.diag(rho)).astype(complex)


def coherence_l1(rho):
    """l1 norm of coherence: C_l1(rho) = sum_{i!=j} |rho_{ij}|."""
    off_diag = rho.copy()
    np.fill_diagonal(off_diag, 0)
    return float(np.sum(np.abs(off_diag)))


def coherence_relative_entropy(rho):
    """Relative entropy of coherence: C_re(rho) = S(dephase(rho)) - S(rho).
    Uses log base 2."""
    rho_diag = dephase(rho)
    return von_neumann_entropy(rho_diag) - von_neumann_entropy(rho)


# =====================================================================
# ENTANGLEMENT RESOURCE THEORY
# =====================================================================

def concurrence_2qubit(rho):
    """Concurrence for a 2-qubit state (Wootters formula).
    C(rho) = max(0, l1 - l2 - l3 - l4) where l_i are sqrt of eigenvalues
    of rho * (sigma_y x sigma_y) rho* (sigma_y x sigma_y) in decreasing order."""
    sy_sy = np.kron(SIGMA_Y, SIGMA_Y)
    rho_tilde = sy_sy @ rho.conj() @ sy_sy
    product = rho @ rho_tilde
    evals = np.linalg.eigvals(product)
    # Eigenvalues should be real and non-negative; take sqrt of abs
    sqrt_evals = np.sort(np.sqrt(np.abs(evals.real)))[::-1]
    c = sqrt_evals[0] - sqrt_evals[1] - sqrt_evals[2] - sqrt_evals[3]
    return float(max(0, c))


def negativity(rho, dim_a=2, dim_b=2):
    """Negativity: N(rho) = (||rho^{T_B}||_1 - 1) / 2.
    ||.||_1 = sum of absolute eigenvalues."""
    rho_pt = partial_transpose(rho, dim_a, dim_b)
    evals = np.linalg.eigvalsh(rho_pt)
    return float((np.sum(np.abs(evals)) - 1.0) / 2.0)


def entanglement_of_formation_2qubit(rho):
    """EoF for 2-qubit state via Wootters formula:
    EoF = h((1 + sqrt(1 - C^2)) / 2) where h is binary entropy."""
    C = concurrence_2qubit(rho)
    if C < 1e-15:
        return 0.0
    x = (1.0 + np.sqrt(1.0 - C**2)) / 2.0
    # Binary entropy (log base 2)
    if x < 1e-15 or x > 1 - 1e-15:
        return 0.0
    return float(-x * np.log2(x) - (1 - x) * np.log2(1 - x))


def is_separable_pure(psi, dim_a=2, dim_b=2, tol=1e-10):
    """Check if a pure bipartite state is separable (product state).
    A pure state is separable iff its Schmidt rank is 1."""
    mat = psi.reshape(dim_a, dim_b)
    sv = np.linalg.svd(mat, compute_uv=False)
    return int(np.sum(sv > tol)) == 1


# =====================================================================
# ATHERMALITY RESOURCE THEORY
# =====================================================================

def thermal_state(H, beta):
    """Build thermal state rho_beta = exp(-beta H) / Z."""
    rho_unnorm = expm(-beta * H)
    Z = np.trace(rho_unnorm).real
    return rho_unnorm / Z, Z


def free_energy(rho, H, T):
    """Non-equilibrium free energy: F(rho) = Tr(rho H) - T * S(rho).
    Uses natural log for consistency with kT."""
    energy = np.trace(rho @ H).real
    S = von_neumann_entropy_ln(rho)
    return float(energy - T * S)


def extractable_work(rho, H, T):
    """Extractable work = F(rho) - F(rho_thermal).
    Always >= 0 by the second law."""
    F_rho = free_energy(rho, H, T)
    beta = 1.0 / (KB * T)
    rho_th, Z = thermal_state(H, beta)
    F_th = -T * np.log(Z)  # F_eq = -kT ln Z
    return float(F_rho - F_th)


def relative_entropy_to_thermal(rho, H, T):
    """D(rho || rho_thermal) = beta * (F(rho) - F_eq).
    This is the athermality monotone."""
    beta = 1.0 / (KB * T)
    W = extractable_work(rho, H, T)
    return float(beta * W)


# =====================================================================
# TEST SUITE
# =====================================================================

def test_coherence_theory():
    """Test the coherence resource theory."""
    results = {}

    # --- Free states are incoherent (diagonal) ---
    rho_ground = ket_to_dm(KET_0)
    rho_mixed = np.eye(2) / 2.0
    rho_plus = ket_to_dm(KET_PLUS)

    results["free_state_ground_is_incoherent"] = is_incoherent(rho_ground)
    results["free_state_mixed_is_incoherent"] = is_incoherent(rho_mixed)
    results["plus_state_is_NOT_incoherent"] = not is_incoherent(rho_plus)

    # --- Monotone: l1 coherence ---
    c_l1_ground = coherence_l1(rho_ground)
    c_l1_plus = coherence_l1(rho_plus)
    results["C_l1_ground"] = c_l1_ground
    results["C_l1_plus"] = c_l1_plus
    results["C_l1_plus_equals_1"] = abs(c_l1_plus - 1.0) < 1e-10

    # --- Monotone: relative entropy of coherence ---
    c_re_ground = coherence_relative_entropy(rho_ground)
    c_re_plus = coherence_relative_entropy(rho_plus)
    results["C_re_ground"] = c_re_ground
    results["C_re_plus"] = c_re_plus
    results["C_re_plus_equals_1"] = abs(c_re_plus - 1.0) < 1e-10

    # --- Free op (dephasing) cannot increase coherence ---
    rho_test = 0.7 * ket_to_dm(KET_PLUS) + 0.3 * ket_to_dm(KET_0)
    c_before = coherence_l1(rho_test)
    c_after = coherence_l1(dephase(rho_test))
    results["dephasing_kills_coherence"] = c_after < 1e-10
    results["dephasing_does_not_increase_C"] = c_after <= c_before + 1e-10

    # --- Minus state also has coherence 1 ---
    c_l1_minus = coherence_l1(ket_to_dm(KET_MINUS))
    results["C_l1_minus_equals_1"] = abs(c_l1_minus - 1.0) < 1e-10

    return results


def test_entanglement_theory():
    """Test the entanglement resource theory."""
    results = {}

    # --- Free states: separable ---
    results["product_00_is_separable"] = is_separable_pure(KET_00)
    results["bell_phi_plus_NOT_separable"] = not is_separable_pure(PHI_PLUS)

    # --- Monotones on product state (should be 0) ---
    rho_prod = ket_to_dm(KET_00)
    results["concurrence_product"] = concurrence_2qubit(rho_prod)
    results["negativity_product"] = negativity(rho_prod)
    results["EoF_product"] = entanglement_of_formation_2qubit(rho_prod)
    results["product_concurrence_zero"] = concurrence_2qubit(rho_prod) < 1e-10

    # --- Monotones on maximally entangled Bell state ---
    rho_bell = ket_to_dm(PHI_PLUS)
    c_bell = concurrence_2qubit(rho_bell)
    n_bell = negativity(rho_bell)
    eof_bell = entanglement_of_formation_2qubit(rho_bell)
    results["concurrence_bell"] = c_bell
    results["negativity_bell"] = n_bell
    results["EoF_bell"] = eof_bell
    results["bell_concurrence_equals_1"] = abs(c_bell - 1.0) < 1e-10
    results["bell_negativity_equals_0.5"] = abs(n_bell - 0.5) < 1e-10
    results["bell_EoF_equals_1"] = abs(eof_bell - 1.0) < 1e-10

    # --- All four Bell states are maximally entangled ---
    for name, state in [("phi+", PHI_PLUS), ("phi-", PHI_MINUS),
                         ("psi+", PSI_PLUS), ("psi-", PSI_MINUS)]:
        c = concurrence_2qubit(ket_to_dm(state))
        results[f"concurrence_{name}"] = c
        results[f"{name}_maximally_entangled"] = abs(c - 1.0) < 1e-10

    # --- Werner state: rho_w = p |Phi+><Phi+| + (1-p) I/4 ---
    # Concurrence = max(0, (3p-1)/2) for Werner state
    for p in [0.0, 0.33, 0.5, 0.8, 1.0]:
        rho_w = p * ket_to_dm(PHI_PLUS) + (1 - p) * np.eye(4) / 4.0
        c_w = concurrence_2qubit(rho_w)
        c_expected = max(0, (3 * p - 1) / 2)
        results[f"werner_p={p}_concurrence"] = c_w
        results[f"werner_p={p}_matches_formula"] = abs(c_w - c_expected) < 1e-6

    return results


def test_athermality_theory():
    """Test the athermality resource theory."""
    results = {}

    # H = -sigma_Z so that |0> has energy -1 (ground) and |1> has energy +1 (excited)
    H = -SIGMA_Z.astype(complex)

    # --- Free state: thermal at various temperatures ---
    for T in [0.5, 1.0, 2.0, 10.0]:
        beta = 1.0 / T
        rho_th, Z = thermal_state(H, beta)
        # Thermal state is always diagonal in energy eigenbasis
        results[f"thermal_T={T}_is_diagonal"] = is_incoherent(rho_th)
        # Extractable work from thermal state is 0
        W = extractable_work(rho_th, H, T)
        results[f"thermal_T={T}_extractable_work"] = W
        results[f"thermal_T={T}_W_is_zero"] = abs(W) < 1e-10

    # --- Athermal state: pure ground state |0> has extractable work ---
    T = 1.0
    rho_ground = ket_to_dm(KET_0)
    W_ground = extractable_work(rho_ground, H, T)
    results["ground_state_extractable_work"] = W_ground
    results["ground_state_W_positive"] = W_ground > -1e-10

    # --- Athermal state: maximally mixed has extractable work ---
    rho_max_mixed = np.eye(2, dtype=complex) / 2.0
    W_mixed = extractable_work(rho_max_mixed, H, T)
    results["max_mixed_extractable_work"] = W_mixed

    # --- Pure excited state |1>: higher energy, more extractable work ---
    rho_excited = ket_to_dm(KET_1)
    W_excited = extractable_work(rho_excited, H, T)
    results["excited_state_extractable_work"] = W_excited
    results["excited_W_greater_than_ground_W"] = W_excited > W_ground

    # --- Free energy ordering: F(rho_pure) >= F(rho_thermal) ---
    F_ground = free_energy(rho_ground, H, T)
    rho_th, Z = thermal_state(H, 1.0 / T)
    F_th = free_energy(rho_th, H, T)
    results["F_ground_geq_F_thermal"] = F_ground >= F_th - 1e-10

    # --- High-T limit: thermal -> maximally mixed ---
    rho_highT, _ = thermal_state(H, beta=0.001)
    results["high_T_approaches_mixed"] = np.allclose(rho_highT, np.eye(2) / 2, atol=1e-3)

    # --- Low-T limit: thermal -> ground state |0> ---
    rho_lowT, _ = thermal_state(H, beta=100.0)
    results["low_T_approaches_ground"] = np.allclose(rho_lowT, ket_to_dm(KET_0), atol=1e-3)

    return results


def test_interconversion():
    """Test resource interconversion: coherence -> entanglement via CNOT.

    Key physical fact: a CNOT gate converts LOCAL coherence into
    BIPARTITE entanglement. The coherence resource is traded for
    entanglement resource. Resources are FUNGIBLE.

    |+>|0> :  C_l1 = 1 (local coherence), Concurrence = 0
    CNOT|+0> = |Phi+> :  C_l1(local) = 0, Concurrence = 1
    """
    results = {}

    # --- Input state: |+>|0> ---
    psi_in = np.kron(KET_PLUS, KET_0)
    rho_in = ket_to_dm(psi_in)

    # Local coherence of qubit A
    rho_A_in = partial_trace(rho_in, 2, 2, trace_out="B")
    c_l1_local_in = coherence_l1(rho_A_in)
    results["input_local_coherence_A"] = c_l1_local_in
    results["input_local_coherence_equals_1"] = abs(c_l1_local_in - 1.0) < 1e-10

    # Entanglement of input
    c_ent_in = concurrence_2qubit(rho_in)
    results["input_concurrence"] = c_ent_in
    results["input_concurrence_is_zero"] = c_ent_in < 1e-10

    # --- Apply CNOT ---
    psi_out = CNOT @ psi_in
    rho_out = ket_to_dm(psi_out)

    # Verify output is Bell Phi+
    overlap = abs(np.dot(psi_out.conj(), PHI_PLUS))**2
    results["output_is_bell_phi_plus"] = abs(overlap - 1.0) < 1e-10

    # Local coherence of qubit A after CNOT
    rho_A_out = partial_trace(rho_out, 2, 2, trace_out="B")
    c_l1_local_out = coherence_l1(rho_A_out)
    results["output_local_coherence_A"] = c_l1_local_out
    results["output_local_coherence_is_zero"] = c_l1_local_out < 1e-10

    # Entanglement of output
    c_ent_out = concurrence_2qubit(rho_out)
    results["output_concurrence"] = c_ent_out
    results["output_concurrence_equals_1"] = abs(c_ent_out - 1.0) < 1e-10

    # --- The fungibility statement ---
    # Coherence in = 1, Entanglement in = 0
    # Coherence out = 0, Entanglement out = 1
    # Total "resource" is conserved in this conversion
    results["coherence_to_entanglement_conversion"] = (
        abs(c_l1_local_in - 1.0) < 1e-10 and
        c_ent_in < 1e-10 and
        c_l1_local_out < 1e-10 and
        abs(c_ent_out - 1.0) < 1e-10
    )

    # --- Reverse: local dephasing destroys entanglement but not coherence-free ---
    # Apply dephasing to qubit A of Bell state (should kill entanglement)
    # Kraus: |0><0| rho |0><0| + |1><1| rho |1><1| on A
    K0 = np.kron(np.outer(KET_0, KET_0), I2)
    K1 = np.kron(np.outer(KET_1, KET_1), I2)
    rho_dephased = K0 @ rho_out @ K0.conj().T + K1 @ rho_out @ K1.conj().T
    c_ent_dephased = concurrence_2qubit(rho_dephased)
    results["dephasing_A_kills_entanglement"] = c_ent_dephased < 1e-10

    # --- Mixed interconversion: partial coherence -> partial entanglement ---
    # State with coherence p: rho = p|+><+| + (1-p)|0><0|
    for p in [0.25, 0.5, 0.75]:
        rho_A = p * ket_to_dm(KET_PLUS) + (1 - p) * ket_to_dm(KET_0)
        # Purify: make a 2-qubit pure state with this reduced state on A
        # Use |psi> = sqrt(p)|+>|0> + sqrt(1-p)|0>|1> (not quite right for
        # mixed state interconversion, so just use the product state approach)
        psi_partial = np.kron(
            np.sqrt(p) * KET_PLUS + np.sqrt(1 - p) * KET_0,
            KET_0,
        )
        # Normalize
        psi_partial = psi_partial / np.linalg.norm(psi_partial)
        rho_partial_in = ket_to_dm(psi_partial)

        rho_A_partial = partial_trace(rho_partial_in, 2, 2, trace_out="B")
        c_in = coherence_l1(rho_A_partial)

        psi_partial_out = CNOT @ psi_partial
        rho_partial_out = ket_to_dm(psi_partial_out)
        c_out = concurrence_2qubit(rho_partial_out)

        results[f"partial_p={p}_coherence_in"] = c_in
        results[f"partial_p={p}_entanglement_out"] = c_out
        results[f"partial_p={p}_ent_positive"] = c_out > 1e-10

    return results


def test_monotone_properties():
    """Verify that monotones satisfy the defining properties of resource monotones:
    (a) Zero on free states
    (b) Non-negative
    (c) Non-increasing under free operations
    """
    results = {}

    # --- Coherence monotone properties ---
    # (a) Zero on free (incoherent) states
    for name, rho in [("ground", ket_to_dm(KET_0)),
                       ("excited", ket_to_dm(KET_1)),
                       ("mixed", np.eye(2, dtype=complex) / 2)]:
        results[f"coh_l1_zero_on_{name}"] = coherence_l1(rho) < 1e-10
        results[f"coh_re_zero_on_{name}"] = abs(coherence_relative_entropy(rho)) < 1e-10

    # (b) Non-negative on arbitrary states
    np.random.seed(42)
    for i in range(10):
        psi = np.random.randn(2) + 1j * np.random.randn(2)
        psi = psi / np.linalg.norm(psi)
        rho = ket_to_dm(psi)
        results[f"coh_l1_nonneg_rand{i}"] = coherence_l1(rho) >= -1e-15
        results[f"coh_re_nonneg_rand{i}"] = coherence_relative_entropy(rho) >= -1e-15

    # (c) Non-increasing under dephasing (free op)
    for i in range(10):
        psi = np.random.randn(2) + 1j * np.random.randn(2)
        psi = psi / np.linalg.norm(psi)
        rho = ket_to_dm(psi)
        results[f"coh_l1_monotone_rand{i}"] = (
            coherence_l1(dephase(rho)) <= coherence_l1(rho) + 1e-10
        )

    # --- Entanglement monotone properties ---
    # (a) Zero on separable states
    for name, psi in [("00", KET_00), ("01", KET_01),
                       ("plus_zero", np.kron(KET_PLUS, KET_0))]:
        rho = ket_to_dm(psi)
        results[f"ent_conc_zero_on_{name}"] = concurrence_2qubit(rho) < 1e-10
        results[f"ent_neg_zero_on_{name}"] = negativity(rho) < 1e-10

    # (b) Non-negative on random 2-qubit states
    for i in range(10):
        psi = np.random.randn(4) + 1j * np.random.randn(4)
        psi = psi / np.linalg.norm(psi)
        rho = ket_to_dm(psi)
        results[f"ent_conc_nonneg_rand{i}"] = concurrence_2qubit(rho) >= -1e-15
        results[f"ent_neg_nonneg_rand{i}"] = negativity(rho) >= -1e-15

    return results


# =====================================================================
# MAIN
# =====================================================================

def main():
    all_results = {}
    all_pass = True

    sections = [
        ("coherence_resource_theory", test_coherence_theory),
        ("entanglement_resource_theory", test_entanglement_theory),
        ("athermality_resource_theory", test_athermality_theory),
        ("resource_interconversion", test_interconversion),
        ("monotone_properties", test_monotone_properties),
    ]

    for name, test_fn in sections:
        print(f"\n{'='*60}")
        print(f"  {name.upper()}")
        print(f"{'='*60}")
        results = test_fn()
        all_results[name] = results

        section_pass = True
        for k, v in results.items():
            if isinstance(v, bool):
                status = "PASS" if v else "FAIL"
                if not v:
                    section_pass = False
                    all_pass = False
                print(f"  [{status}] {k}")
            else:
                print(f"         {k} = {v:.6f}" if isinstance(v, float) else f"         {k} = {v}")

        all_results[f"{name}_all_pass"] = section_pass

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")

    total_bool = 0
    total_pass = 0
    for section in all_results.values():
        if isinstance(section, dict):
            for v in section.values():
                if isinstance(v, bool):
                    total_bool += 1
                    if v:
                        total_pass += 1

    all_results["total_checks"] = total_bool
    all_results["total_passed"] = total_pass
    all_results["all_pass"] = all_pass

    print(f"  {total_pass}/{total_bool} checks passed")
    print(f"  ALL PASS: {all_pass}")

    # --- Write output ---
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "pure_lego_resource_theories_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, cls=_NumpyEncoder)
    print(f"\n  Results -> {out_path}")


if __name__ == "__main__":
    main()
