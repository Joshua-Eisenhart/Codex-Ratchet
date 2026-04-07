"""
Pure Lego: Quantum Markov Chains & Conditional Independence
============================================================
No engine. numpy/scipy only.

Tests:
  1. Quantum conditional mutual information I(A:C|B) via von Neumann entropies
  2. Product state  => I(A:C|B) = 0  (quantum Markov chain A-B-C)
  3. GHZ state      => I(A:C|B) > 0  (NOT a quantum Markov chain)
  4. Classical Markov chain as diagonal density matrix => classical CI matches quantum
  5. Petz recovery map: if I(A:C|B)=0, rho_ABC = R_{B->BC}(rho_AB)
  6. Strong subadditivity: I(A:C|B) >= 0 for random states
"""

import numpy as np
from scipy.linalg import logm, expm
import json
import os
from datetime import datetime, UTC

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)

# ---------------------------------------------------------------------------
#  Utility: partial trace for 3-qubit (2x2x2) systems
# ---------------------------------------------------------------------------

def partial_trace(rho, keep, dims=(2, 2, 2)):
    """
    Partial trace of a density matrix over subsystems NOT in `keep`.
    keep: tuple of subsystem indices to keep (0=A, 1=B, 2=C).
    dims: dimensions of each subsystem.
    """
    n = len(dims)
    d_total = int(np.prod(dims))
    assert rho.shape == (d_total, d_total), f"Shape mismatch: {rho.shape} vs ({d_total},{d_total})"

    # Reshape into tensor with n ket indices and n bra indices
    rho_t = rho.reshape(list(dims) + list(dims))

    # Determine which axes to trace out
    trace_out = sorted(set(range(n)) - set(keep))

    # Trace from highest index to lowest to avoid axis-shift issues
    for ax in reversed(trace_out):
        # Trace pairs: ket axis=ax, bra axis=ax+n_remaining
        n_remaining = rho_t.ndim // 2
        rho_t = np.trace(rho_t, axis1=ax, axis2=ax + n_remaining)

    # Reshape to matrix
    d_keep = int(np.prod([dims[k] for k in keep]))
    return rho_t.reshape(d_keep, d_keep)


def von_neumann_entropy(rho):
    """S(rho) = -Tr(rho log2 rho), using eigenvalues for numerical stability."""
    eigvals = np.real(np.linalg.eigvalsh(rho))
    eigvals = eigvals[eigvals > 1e-15]
    return -np.sum(eigvals * np.log2(eigvals))


def conditional_mutual_info(rho_abc, dims=(2, 2, 2)):
    """
    I(A:C|B) = S(AB) + S(BC) - S(B) - S(ABC)
    """
    rho_ab = partial_trace(rho_abc, keep=(0, 1), dims=dims)
    rho_bc = partial_trace(rho_abc, keep=(1, 2), dims=dims)
    rho_b = partial_trace(rho_abc, keep=(1,), dims=dims)

    s_ab = von_neumann_entropy(rho_ab)
    s_bc = von_neumann_entropy(rho_bc)
    s_b = von_neumann_entropy(rho_b)
    s_abc = von_neumann_entropy(rho_abc)

    return s_ab + s_bc - s_b - s_abc


# ---------------------------------------------------------------------------
#  State builders
# ---------------------------------------------------------------------------

def product_state_abc():
    """
    Product state |psi_A> x |psi_B> x |psi_C>.
    A-B-C is trivially a quantum Markov chain.
    """
    psi_a = np.array([1, 0], dtype=complex)
    psi_b = np.array([0, 1], dtype=complex)
    psi_c = np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=complex)
    psi_abc = np.kron(np.kron(psi_a, psi_b), psi_c)
    return np.outer(psi_abc, psi_abc.conj())


def ghz_state_abc():
    """
    GHZ state: (|000> + |111>) / sqrt(2).
    Maximally entangled across A-B-C; NOT a quantum Markov chain.
    """
    psi = np.zeros(8, dtype=complex)
    psi[0] = 1 / np.sqrt(2)   # |000>
    psi[7] = 1 / np.sqrt(2)   # |111>
    return np.outer(psi, psi.conj())


def classical_markov_chain():
    """
    Classical Markov chain A-B-C as a diagonal density matrix.
    P(A,B,C) = P(A|B) P(B) P(C|B)  =>  P(A,C|B) = P(A|B)P(C|B)
    i.e. A and C are conditionally independent given B.

    Encoding: |abc> with a,b,c in {0,1}.
    B is uniform. A=B with prob 0.8, else flip. C=B with prob 0.7, else flip.
    """
    probs = np.zeros(8)
    p_b = 0.5
    for b in range(2):
        for a in range(2):
            p_a_given_b = 0.8 if a == b else 0.2
            for c in range(2):
                p_c_given_b = 0.7 if c == b else 0.3
                idx = a * 4 + b * 2 + c
                probs[idx] = p_a_given_b * p_b * p_c_given_b
    return np.diag(probs)


def random_pure_state_abc(rng):
    """Random Haar-distributed pure state on 3 qubits."""
    psi = rng.standard_normal(8) + 1j * rng.standard_normal(8)
    psi /= np.linalg.norm(psi)
    return np.outer(psi, psi.conj())


def random_mixed_state_abc(rng, rank=4):
    """Random mixed state via partial trace of a larger pure state."""
    d = 8
    d_env = max(rank, 2)
    psi = rng.standard_normal(d * d_env) + 1j * rng.standard_normal(d * d_env)
    psi /= np.linalg.norm(psi)
    psi_mat = psi.reshape(d, d_env)
    return psi_mat @ psi_mat.conj().T


# ---------------------------------------------------------------------------
#  Petz recovery map
# ---------------------------------------------------------------------------

def matrix_log(m):
    """Safe matrix logarithm for positive semidefinite matrices."""
    eigvals, eigvecs = np.linalg.eigh(m)
    eigvals = np.maximum(eigvals, 1e-30)
    return eigvecs @ np.diag(np.log(eigvals)) @ eigvecs.conj().T


def matrix_power(m, p):
    """Matrix to real power for positive semidefinite matrices."""
    eigvals, eigvecs = np.linalg.eigh(m)
    eigvals = np.maximum(np.real(eigvals), 1e-30)
    return eigvecs @ np.diag(eigvals ** p) @ eigvecs.conj().T


def petz_recovery_map(rho_abc, dims=(2, 2, 2)):
    """
    Petz recovery map R_{B->BC}: given rho_AB, reconstruct rho_ABC.
    R_{B->BC}(rho_AB) = rho_BC^{1/2} (rho_B^{-1/2} rho_AB rho_B^{-1/2}) x I_C  rho_BC^{1/2}

    For a quantum Markov state, rho_ABC = R_{B->BC}(rho_AB) exactly.
    We implement via the explicit Petz formula.
    """
    d_a, d_b, d_c = dims
    d_total = d_a * d_b * d_c

    rho_ab = partial_trace(rho_abc, keep=(0, 1), dims=dims)
    rho_bc = partial_trace(rho_abc, keep=(1, 2), dims=dims)
    rho_b = partial_trace(rho_abc, keep=(1,), dims=dims)

    # sigma_B^{-1/2}
    sigma_b_inv_half = matrix_power(rho_b, -0.5)

    # sigma_BC^{1/2}
    sigma_bc_half = matrix_power(rho_bc, 0.5)
    sigma_bc_inv_half = matrix_power(rho_bc, -0.5)

    # Embed rho_AB into ABC space: rho_AB tensor I_C
    rho_ab_full = np.kron(rho_ab, np.eye(d_c))

    # Embed sigma_B^{-1/2} into AB space: I_A tensor sigma_B^{-1/2}
    sigma_b_inv_half_ab = np.kron(np.eye(d_a), sigma_b_inv_half)
    # Then into ABC: (I_A tensor sigma_B^{-1/2}) tensor I_C
    sigma_b_inv_half_abc = np.kron(sigma_b_inv_half_ab, np.eye(d_c))

    # Embed sigma_BC^{1/2} into ABC: I_A tensor sigma_BC^{1/2}
    sigma_bc_half_abc = np.kron(np.eye(d_a), sigma_bc_half)
    sigma_bc_inv_half_abc = np.kron(np.eye(d_a), sigma_bc_inv_half)

    # Embed sigma_B into BC space for the denominator: sigma_B tensor I_C
    sigma_b_bc = np.kron(rho_b, np.eye(d_c))
    sigma_b_inv_half_bc = matrix_power(sigma_b_bc, -0.5)
    # Careful: we need I_A tensor (sigma_B tensor I_C)^{-1/2}
    # But (sigma_B tensor I_C)^{-1/2} != sigma_B^{-1/2} tensor I_C in general
    # Actually for tensor products: (A tensor B)^p = A^p tensor B^p
    # So sigma_b_inv_half_abc is correct.

    # Petz recovery: R(X) = sigma_BC^{1/2} sigma_B^{-1/2} X sigma_B^{-1/2} sigma_BC^{1/2}
    # where X lives in AB space, embedded into ABC as X tensor I_C
    # But the correct Petz map for partial trace over C is:
    # R_{B->BC}(omega_AB) = sigma_BC^{1/2} (sigma_B^{-1/2} omega_B sigma_B^{-1/2} tensor I_A)...
    #
    # Let's use the direct formula from Fawzi-Renner:
    # rho_ABC^{recovered} = sigma_BC^{1/2} (sigma_B^{-1/2} rho_AB sigma_B^{-1/2} \otimes I_C) sigma_BC^{1/2}
    # But we need to be careful about the ordering of subsystems.
    #
    # Cleaner approach: work in the ABC basis directly.

    # Step 1: sigma_B^{-1/2} in ABC space (acts on B only)
    # = I_A \otimes sigma_B^{-1/2} \otimes I_C
    step1 = sigma_b_inv_half_abc @ rho_ab_full @ sigma_b_inv_half_abc

    # Step 2: sigma_BC^{1/2} in ABC space (acts on BC only)
    # = I_A \otimes sigma_BC^{1/2}
    recovered = sigma_bc_half_abc @ step1 @ sigma_bc_half_abc

    # Normalize
    tr = np.trace(recovered)
    if np.abs(tr) > 1e-15:
        recovered = recovered / tr

    # Ensure Hermiticity
    recovered = (recovered + recovered.conj().T) / 2

    return recovered


# ---------------------------------------------------------------------------
#  Tests
# ---------------------------------------------------------------------------

def test_product_state():
    """Product state should have I(A:C|B) = 0 (quantum Markov chain)."""
    rho = product_state_abc()
    cmi = conditional_mutual_info(rho)
    passed = np.abs(cmi) < 1e-10
    return {
        "test": "product_state_I(A:C|B)=0",
        "I(A:C|B)": float(cmi),
        "passed": bool(passed),
    }


def test_ghz_state():
    """GHZ state should have I(A:C|B) > 0 (NOT a quantum Markov chain)."""
    rho = ghz_state_abc()
    cmi = conditional_mutual_info(rho)
    passed = cmi > 0.01
    return {
        "test": "ghz_state_I(A:C|B)>0",
        "I(A:C|B)": float(cmi),
        "passed": bool(passed),
    }


def test_classical_markov():
    """Classical Markov chain: diagonal density matrix should give I(A:C|B) = 0."""
    rho = classical_markov_chain()
    cmi = conditional_mutual_info(rho)
    passed = np.abs(cmi) < 1e-10
    return {
        "test": "classical_markov_I(A:C|B)=0",
        "I(A:C|B)": float(cmi),
        "passed": bool(passed),
    }


def test_strong_subadditivity(n_trials=50):
    """I(A:C|B) >= 0 for random states (strong subadditivity of von Neumann entropy)."""
    rng = np.random.default_rng(42)
    violations = []
    min_cmi = float("inf")

    for i in range(n_trials):
        if i % 2 == 0:
            rho = random_pure_state_abc(rng)
        else:
            rho = random_mixed_state_abc(rng, rank=rng.integers(2, 8))
        cmi = conditional_mutual_info(rho)
        min_cmi = min(min_cmi, cmi)
        if cmi < -1e-10:
            violations.append({"trial": i, "I(A:C|B)": float(cmi)})

    passed = len(violations) == 0
    return {
        "test": "strong_subadditivity_I(A:C|B)>=0",
        "n_trials": n_trials,
        "min_I(A:C|B)": float(min_cmi),
        "violations": violations,
        "passed": bool(passed),
    }


def test_petz_recovery_product():
    """For product state (I=0), Petz recovery should exactly reconstruct rho_ABC."""
    rho = product_state_abc()
    recovered = petz_recovery_map(rho)
    fidelity = np.real(np.trace(rho @ recovered))
    trace_dist = 0.5 * np.sum(np.abs(np.linalg.eigvalsh(rho - recovered)))
    passed = trace_dist < 1e-6
    return {
        "test": "petz_recovery_product_state",
        "trace_distance": float(trace_dist),
        "fidelity": float(fidelity),
        "passed": bool(passed),
    }


def test_petz_recovery_classical_markov():
    """For classical Markov chain (I=0), Petz recovery should exactly reconstruct."""
    rho = classical_markov_chain()
    recovered = petz_recovery_map(rho)
    trace_dist = 0.5 * np.sum(np.abs(np.linalg.eigvalsh(rho - recovered)))
    passed = trace_dist < 1e-6
    return {
        "test": "petz_recovery_classical_markov",
        "trace_distance": float(trace_dist),
        "passed": bool(passed),
    }


def test_petz_recovery_ghz_fails():
    """For GHZ state (I>0), Petz recovery should NOT exactly reconstruct."""
    rho = ghz_state_abc()
    recovered = petz_recovery_map(rho)
    trace_dist = 0.5 * np.sum(np.abs(np.linalg.eigvalsh(rho - recovered)))
    passed = trace_dist > 0.01
    return {
        "test": "petz_recovery_ghz_fails",
        "trace_distance": float(trace_dist),
        "passed": bool(passed),
    }


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    results = {
        "probe": "pure_lego_quantum_markov",
        "description": "Quantum Markov chains, conditional independence, Petz recovery",
        "timestamp": datetime.now(UTC).isoformat(),
        "tests": [],
    }

    tests = [
        test_product_state,
        test_ghz_state,
        test_classical_markov,
        test_strong_subadditivity,
        test_petz_recovery_product,
        test_petz_recovery_classical_markov,
        test_petz_recovery_ghz_fails,
    ]

    all_passed = True
    for t in tests:
        print(f"Running {t.__name__}...")
        result = t()
        results["tests"].append(result)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"  {status}: {result['test']}")
        if not result["passed"]:
            all_passed = False

    results["all_passed"] = all_passed

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "pure_lego_quantum_markov_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_path}")
    print(f"Overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return results


if __name__ == "__main__":
    main()
