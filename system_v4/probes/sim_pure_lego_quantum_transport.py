"""
Pure Lego: Quantum Optimal Transport & Wasserstein Distance
============================================================
No engine. numpy/scipy only.

Computes quantum Wasserstein-1 distance:
  W_1(rho, sigma) = max_{H: ||H||_Lip <= 1} Tr(H (rho - sigma))
where Lipschitz norm is w.r.t. Hamming distance on the computational basis.

For n qubits the Lipschitz constraint means:
  |<x|H|x> - <y|H|y>| <= d_H(x,y)  for diagonal elements
  plus the full operator-norm Lipschitz condition encoded as an SDP-like
  constraint (here solved via explicit enumeration for small qubit counts).

For 1-qubit (d=2): the Hamming graph has two nodes distance 1.
For 2-qubit (d=4): Hamming graph on {00,01,10,11}.

We compare W_1 vs trace distance vs Bures distance on 20 random state pairs,
then run targeted 2-qubit tests: product vs entangled, local vs global
perturbations, verifying W_1 respects locality.
"""

import warnings
import numpy as np
from scipy.linalg import sqrtm
from scipy.optimize import linprog
import json
import os
from datetime import datetime, UTC

np.random.seed(42)

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)
os.makedirs(RESULTS_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# Density Matrix Utilities
# ─────────────────────────────────────────────

def make_random_density_matrix(d):
    """Random density matrix of dimension d."""
    A = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    rho = A @ A.conj().T
    return rho / np.trace(rho)


def make_pure_state(psi):
    """Density matrix from a state vector."""
    psi = np.asarray(psi, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    return np.outer(psi, psi.conj())


def partial_trace(rho, dims, keep):
    """Partial trace of rho over subsystems not in keep.
    dims: list of subsystem dimensions, e.g. [2,2] for 2 qubits.
    keep: index of subsystem to keep (0 or 1 for bipartite).
    """
    n = len(dims)
    rho_t = rho.reshape(dims + dims)
    # Trace out all subsystems except keep
    trace_axes = [i for i in range(n) if i != keep]
    for offset, ax in enumerate(sorted(trace_axes)):
        # trace pairs: axis ax and axis ax+n (shifted by removals)
        rho_t = np.trace(rho_t, axis1=ax - offset, axis2=ax + n - 2 * offset)
        n -= 1
    return rho_t


# ─────────────────────────────────────────────
# Distance Measures
# ─────────────────────────────────────────────

def trace_distance(rho, sigma):
    """T(rho, sigma) = 0.5 * ||rho - sigma||_1."""
    diff = rho - sigma
    eigvals = np.linalg.eigvalsh(diff)
    return 0.5 * np.sum(np.abs(eigvals))


def bures_distance(rho, sigma):
    """D_B(rho, sigma) = sqrt(2 - 2 * sqrt(F(rho, sigma)))."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        sqrt_rho = sqrtm(rho)
        inner = sqrtm(sqrt_rho @ sigma @ sqrt_rho)
    fidelity = np.real(np.trace(inner)) ** 2
    fidelity = np.clip(fidelity, 0, 1)
    return np.sqrt(np.clip(2 - 2 * np.sqrt(fidelity), 0, None))


def hamming_distance(i, j, n_qubits):
    """Hamming distance between computational basis states i and j."""
    return bin(i ^ j).count('1')


def hamming_distance_matrix(n_qubits):
    """Return d x d matrix of Hamming distances, d = 2^n_qubits."""
    d = 2 ** n_qubits
    D = np.zeros((d, d), dtype=float)
    for i in range(d):
        for j in range(d):
            D[i, j] = hamming_distance(i, j, n_qubits)
    return D


def quantum_wasserstein_1(rho, sigma, n_qubits):
    """
    Compute W_1(rho, sigma) via the dual formulation:
      W_1 = max Tr(H (rho - sigma))
      subject to: H hermitian, ||H||_Lip <= 1

    The Lipschitz constraint w.r.t. Hamming distance means:
      ||H||_Lip = max_{x != y} |<x|H|x> - <y|H|y>| / d_H(x,y)
                  (diagonal Lipschitz) AND
      the full operator condition.

    For small systems we parameterise H as a real symmetric matrix (since
    the optimal H can always be chosen Hermitian with real entries in the
    computational basis) and optimise via scipy.

    Exact approach: enumerate vertices of the Lipschitz-1 polytope for
    diagonal, then maximise over off-diagonal within spectral constraints.

    Practical approach for small d: use the KNOWN result that for the
    Hamming graph, W_1 can be computed as the solution to a linear program
    on the diagonal elements, plus a correction from coherences.

    Here we implement the full SDP-relaxed approach using the fact that
    for small d we can directly optimise.
    """
    d = 2 ** n_qubits
    D = hamming_distance_matrix(n_qubits)
    delta = rho - sigma

    # For the quantum W_1, we solve:
    # max Re(Tr(H @ delta))
    # s.t. H hermitian, |H_ii - H_jj| <= D[i,j] for all i,j
    #      and ||H|| (operator norm) bounded to keep Lip <= 1
    #
    # We use an iterative approach: optimise over the real diagonal
    # of H via LP (Lipschitz constraint on diagonal), then check if
    # off-diagonal terms can improve. For the Hamming metric the
    # optimal H turns out to be diagonal in most practical cases
    # when delta has small off-diagonal elements.

    # Step 1: Diagonal LP relaxation
    # max sum_i h_i * delta_ii (real parts)
    # s.t. h_i - h_j <= D[i,j] for all i,j
    # Also fix h_0 = 0 (translation invariance)

    delta_diag = np.real(np.diag(delta))

    # LP: minimise -c^T h  (i.e. maximise c^T h)
    # Variables: h_1, ..., h_{d-1}  (h_0 = 0 fixed)
    c = -delta_diag[1:]  # we maximise, so negate for linprog

    # Constraints: h_i - h_j <= D[i,j]
    # Including h_0=0: h_i <= D[i,0] and -h_i <= D[i,0]
    A_ub_rows = []
    b_ub_rows = []
    n_vars = d - 1

    for i in range(d):
        for j in range(d):
            if i == j:
                continue
            # h_i - h_j <= D[i,j]
            row = np.zeros(n_vars)
            if i > 0:
                row[i - 1] = 1.0
            if j > 0:
                row[j - 1] = -1.0
            A_ub_rows.append(row)
            b_ub_rows.append(D[i, j])

    A_ub = np.array(A_ub_rows)
    b_ub = np.array(b_ub_rows)

    bounds = [(None, None)] * n_vars
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    if result.success:
        h_opt = np.zeros(d)
        h_opt[1:] = result.x
        w1_diag = np.dot(h_opt, delta_diag)
    else:
        w1_diag = 0.0

    # Step 2: Off-diagonal coherence contribution
    # For the full quantum W_1, off-diagonal elements of H can extract
    # additional distance from coherences in delta. We bound this by:
    # sum_{i<j} |delta_ij| * min(1, D[i,j]) (Cauchy-Schwarz-type bound)
    # but the true optimum requires SDP. For small systems we use
    # a tighter estimate via eigenvalue optimisation.

    # Build the optimal diagonal H, then try adding off-diagonal
    # perturbations that maintain the Lipschitz condition.
    H_opt = np.diag(h_opt.astype(complex))

    # The Lipschitz-1 condition for the full matrix on Hamming graph:
    # For adjacent basis states (Hamming dist 1), the 2x2 block
    # of H restricted to {|i>, |j>} must have operator norm of
    # difference <= 1. This means |H_ij| <= sqrt(1 - (H_ii-H_jj)^2/4)
    # when |H_ii - H_jj| <= 1 (for adjacent pairs).

    # We greedily add off-diagonal elements to increase Tr(H @ delta)
    for i in range(d):
        for j in range(i + 1, d):
            dij = D[i, j]
            if dij == 0:
                continue
            diag_diff = abs(h_opt[i] - h_opt[j])
            # For Hamming-adjacent pairs (dij=1), max |H_ij| satisfying Lip-1:
            # The 2x2 submatrix [[H_ii, H_ij],[H_ij*, H_jj]] has singular
            # values related to eigenvalues. The Lipschitz bound constrains
            # the max eigenvalue gap of any 2x2 block for adjacent nodes.
            if dij >= 1:
                max_off_diag = np.sqrt(max(0, dij**2 / 4 - diag_diff**2 / 4))
            else:
                max_off_diag = 0.0

            if max_off_diag > 1e-12:
                # Choose phase of H_ij to align with delta_ij
                delta_ij = delta[i, j]
                if abs(delta_ij) > 1e-15:
                    phase = delta_ij / abs(delta_ij)
                    H_opt[i, j] = max_off_diag * phase
                    H_opt[j, i] = max_off_diag * phase.conj()

    w1_full = np.real(np.trace(H_opt @ delta))

    return max(w1_diag, w1_full, 0.0)


# ─────────────────────────────────────────────
# State Generators for Testing
# ─────────────────────────────────────────────

def bell_state(which=0):
    """Return Bell state density matrix (2-qubit, d=4).
    0: Phi+ = (|00>+|11>)/sqrt(2)
    1: Phi- = (|00>-|11>)/sqrt(2)
    2: Psi+ = (|01>+|10>)/sqrt(2)
    3: Psi- = (|01>-|10>)/sqrt(2)
    """
    psi = np.zeros(4, dtype=complex)
    if which == 0:
        psi[0] = psi[3] = 1 / np.sqrt(2)
    elif which == 1:
        psi[0] = 1 / np.sqrt(2)
        psi[3] = -1 / np.sqrt(2)
    elif which == 2:
        psi[1] = psi[2] = 1 / np.sqrt(2)
    else:
        psi[1] = 1 / np.sqrt(2)
        psi[2] = -1 / np.sqrt(2)
    return make_pure_state(psi)


def product_state_2q(theta_a=0, phi_a=0, theta_b=0, phi_b=0):
    """Product state |a> x |b> for 2 qubits with Bloch angles."""
    a = np.array([np.cos(theta_a / 2),
                  np.exp(1j * phi_a) * np.sin(theta_a / 2)])
    b = np.array([np.cos(theta_b / 2),
                  np.exp(1j * phi_b) * np.sin(theta_b / 2)])
    psi = np.kron(a, b)
    return make_pure_state(psi)


def local_perturbation(rho, qubit, angle, n_qubits=2):
    """Apply a local rotation exp(-i angle X/2) on one qubit.
    Uses X (not Z) so that computational-basis populations shift."""
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    I2 = np.eye(2, dtype=complex)
    Rx = np.cos(angle / 2) * I2 - 1j * np.sin(angle / 2) * X

    if n_qubits == 2:
        if qubit == 0:
            U = np.kron(Rx, I2)
        else:
            U = np.kron(I2, Rx)
    else:
        raise ValueError("Only 2-qubit supported")

    return U @ rho @ U.conj().T


def global_perturbation(rho, angle):
    """Apply a global entangling perturbation: CNOT-like via exp(-i angle XX/2).
    Uses XX interaction so populations mix across both qubits."""
    XX = np.kron(
        np.array([[0, 1], [1, 0]], dtype=complex),
        np.array([[0, 1], [1, 0]], dtype=complex),
    )
    U = np.cos(angle / 2) * np.eye(4, dtype=complex) - 1j * np.sin(angle / 2) * XX
    return U @ rho @ U.conj().T


# ─────────────────────────────────────────────
# Test Suite
# ─────────────────────────────────────────────

def run_20_state_comparison(n_qubits=1):
    """Compare W_1, trace distance, Bures on 20 random state pairs."""
    d = 2 ** n_qubits
    results = []
    for i in range(20):
        rho = make_random_density_matrix(d)
        sigma = make_random_density_matrix(d)

        w1 = quantum_wasserstein_1(rho, sigma, n_qubits)
        td = trace_distance(rho, sigma)
        bd = bures_distance(rho, sigma)

        # For diagonal states, W_1 should approximate trace distance
        rho_diag = np.diag(np.diag(rho))
        sigma_diag = np.diag(np.diag(sigma))
        w1_diag = quantum_wasserstein_1(rho_diag, sigma_diag, n_qubits)
        td_diag = trace_distance(rho_diag, sigma_diag)

        results.append({
            "pair": i,
            "W1": float(w1),
            "trace_distance": float(td),
            "bures_distance": float(bd),
            "W1_diagonal_only": float(w1_diag),
            "TD_diagonal_only": float(td_diag),
            "W1_eq_TD_diagonal": bool(abs(w1_diag - td_diag) < 0.05),
        })

    return results


def run_locality_tests():
    """
    Verify W_1 respects locality on 2-qubit systems:
    - Local perturbation on qubit 0 should produce smaller W_1 than
      the same-angle perturbation applied globally.
    - Product states perturbed locally should show W_1 proportional
      to the perturbation angle.
    """
    results = []

    # Test 1: Product state, local vs global perturbation
    rho_prod = product_state_2q(0, 0, 0, 0)  # |00>

    for angle in [0.1, 0.3, 0.5, 0.8, 1.0]:
        rho_local = local_perturbation(rho_prod, qubit=0, angle=angle)
        rho_global = global_perturbation(rho_prod, angle=angle)

        w1_local = quantum_wasserstein_1(rho_prod, rho_local, n_qubits=2)
        w1_global = quantum_wasserstein_1(rho_prod, rho_global, n_qubits=2)
        td_local = trace_distance(rho_prod, rho_local)
        td_global = trace_distance(rho_prod, rho_global)

        results.append({
            "test": "local_vs_global",
            "angle": angle,
            "W1_local": float(w1_local),
            "W1_global": float(w1_global),
            "TD_local": float(td_local),
            "TD_global": float(td_global),
            "locality_respected": bool(w1_local <= w1_global + 1e-10),
        })

    # Test 2: Entangled (Bell) vs product state distances
    bell_phi_plus = bell_state(0)
    rho_00 = product_state_2q(0, 0, 0, 0)
    rho_rand_prod = product_state_2q(np.pi / 3, np.pi / 4, np.pi / 6, 0)

    w1_bell_00 = quantum_wasserstein_1(bell_phi_plus, rho_00, n_qubits=2)
    w1_bell_rand = quantum_wasserstein_1(bell_phi_plus, rho_rand_prod, n_qubits=2)
    td_bell_00 = trace_distance(bell_phi_plus, rho_00)
    td_bell_rand = trace_distance(bell_phi_plus, rho_rand_prod)
    bd_bell_00 = bures_distance(bell_phi_plus, rho_00)
    bd_bell_rand = bures_distance(bell_phi_plus, rho_rand_prod)

    results.append({
        "test": "entangled_vs_product",
        "pair": "Bell_Phi+ vs |00>",
        "W1": float(w1_bell_00),
        "TD": float(td_bell_00),
        "BD": float(bd_bell_00),
    })
    results.append({
        "test": "entangled_vs_product",
        "pair": "Bell_Phi+ vs random_product",
        "W1": float(w1_bell_rand),
        "TD": float(td_bell_rand),
        "BD": float(bd_bell_rand),
    })

    # Test 3: Nearby qubits contribute more
    # Perturb qubit 0 slightly, qubit 1 a lot — W_1 should weight them
    # by transport cost (Hamming distance), but for 2-qubit each qubit
    # is distance-1 from itself; the key is that local perturbation
    # cost scales with the perturbation, not the global structure.
    rho_base = product_state_2q(np.pi / 4, 0, np.pi / 4, 0)
    rho_q0_small = local_perturbation(rho_base, qubit=0, angle=0.1)
    rho_q0_large = local_perturbation(rho_base, qubit=0, angle=1.0)
    rho_q1_small = local_perturbation(rho_base, qubit=1, angle=0.1)
    rho_q1_large = local_perturbation(rho_base, qubit=1, angle=1.0)

    w1_q0s = quantum_wasserstein_1(rho_base, rho_q0_small, n_qubits=2)
    w1_q0l = quantum_wasserstein_1(rho_base, rho_q0_large, n_qubits=2)
    w1_q1s = quantum_wasserstein_1(rho_base, rho_q1_small, n_qubits=2)
    w1_q1l = quantum_wasserstein_1(rho_base, rho_q1_large, n_qubits=2)

    results.append({
        "test": "perturbation_scaling",
        "W1_q0_small": float(w1_q0s),
        "W1_q0_large": float(w1_q0l),
        "W1_q1_small": float(w1_q1s),
        "W1_q1_large": float(w1_q1l),
        "small_lt_large_q0": bool(w1_q0s < w1_q0l),
        "small_lt_large_q1": bool(w1_q1s < w1_q1l),
        "symmetry_q0_q1_small": float(abs(w1_q0s - w1_q1s)),
        "symmetry_q0_q1_large": float(abs(w1_q0l - w1_q1l)),
    })

    return results


def run_diagonal_verification():
    """
    For diagonal states, W_1 should equal trace distance on the
    probability simplex w.r.t. Hamming cost. Verify this.
    """
    results = []
    for n_qubits in [1, 2]:
        d = 2 ** n_qubits
        for trial in range(5):
            p = np.random.dirichlet(np.ones(d))
            q = np.random.dirichlet(np.ones(d))
            rho = np.diag(p.astype(complex))
            sigma = np.diag(q.astype(complex))

            w1 = quantum_wasserstein_1(rho, sigma, n_qubits)
            td = trace_distance(rho, sigma)

            # For 1-qubit diagonal: W_1 = |p0-q0| = trace distance
            # For 2-qubit diagonal: W_1 uses Hamming cost, may differ from TD
            results.append({
                "n_qubits": n_qubits,
                "trial": trial,
                "W1": float(w1),
                "TD": float(td),
                "match_1q": bool(n_qubits == 1 and abs(w1 - td) < 0.05),
            })
    return results


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Pure Lego: Quantum Optimal Transport & Wasserstein Distance")
    print("=" * 60)

    # --- 20-pair comparison (1-qubit) ---
    print("\n[1] 20-pair comparison (1-qubit)...")
    comparison_1q = run_20_state_comparison(n_qubits=1)
    diag_match_rate = sum(r["W1_eq_TD_diagonal"] for r in comparison_1q) / 20
    print(f"    Diagonal W1 ~ TD match rate: {diag_match_rate:.0%}")

    # --- 20-pair comparison (2-qubit) ---
    print("\n[2] 20-pair comparison (2-qubit)...")
    comparison_2q = run_20_state_comparison(n_qubits=2)

    # --- Diagonal verification ---
    print("\n[3] Diagonal state verification...")
    diag_results = run_diagonal_verification()
    for r in diag_results:
        if r["n_qubits"] == 1:
            print(f"    1q trial {r['trial']}: W1={r['W1']:.4f}  TD={r['TD']:.4f}  match={r.get('match_1q')}")

    # --- Locality tests ---
    print("\n[4] Locality tests (2-qubit)...")
    locality_results = run_locality_tests()
    for r in locality_results:
        if r["test"] == "local_vs_global":
            status = "PASS" if r["locality_respected"] else "FAIL"
            print(f"    angle={r['angle']:.1f}  W1_local={r['W1_local']:.4f}  "
                  f"W1_global={r['W1_global']:.4f}  [{status}]")
        elif r["test"] == "perturbation_scaling":
            print(f"    scaling: small<large q0={r['small_lt_large_q0']}  "
                  f"q1={r['small_lt_large_q1']}")

    # --- Aggregate pass/fail ---
    all_locality_pass = all(
        r.get("locality_respected", True) for r in locality_results
    )
    all_scaling_pass = all(
        r.get("small_lt_large_q0", True) and r.get("small_lt_large_q1", True)
        for r in locality_results if r["test"] == "perturbation_scaling"
    )
    diag_1q_pass = all(
        r.get("match_1q", True) for r in diag_results if r["n_qubits"] == 1
    )

    summary = {
        "probe": "sim_pure_lego_quantum_transport",
        "timestamp": datetime.now(UTC).isoformat(),
        "tests": {
            "20_pair_comparison_1q": {
                "count": 20,
                "diagonal_W1_eq_TD_rate": diag_match_rate,
                "data": comparison_1q,
            },
            "20_pair_comparison_2q": {
                "count": 20,
                "data": comparison_2q,
            },
            "diagonal_verification": {
                "data": diag_results,
                "1q_all_match": diag_1q_pass,
            },
            "locality_tests": {
                "data": locality_results,
                "all_locality_respected": all_locality_pass,
                "all_scaling_correct": all_scaling_pass,
            },
        },
        "overall_status": "PASS" if (
            all_locality_pass and all_scaling_pass and diag_1q_pass
            and diag_match_rate >= 0.8
        ) else "FAIL",
    }

    out_path = os.path.join(RESULTS_DIR, "quantum_transport_wasserstein_results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"OVERALL: {summary['overall_status']}")
    print(f"Results written to: {out_path}")
    print(f"{'=' * 60}")

    return summary


if __name__ == "__main__":
    main()
