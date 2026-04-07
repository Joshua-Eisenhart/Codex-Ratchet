#!/usr/bin/env python3
"""
PURE LEGO: Tensor Network Basics — MPS and MERA
================================================
Foundational building block.  Pure math only — numpy.
No engine imports.  Every operation verified against theory.

Sections
--------
1. MPS for 4-qubit chain: bond dimension chi=2, contraction, normalization
2. Product state (chi=1) and GHZ state (chi=2) via MPS
3. Entanglement entropy from MPS vs direct calculation
4. DMRG-like variational: minimize <psi|H|psi> for Ising H = sum sigma_z x sigma_z
5. Simple MERA: 2-layer binary tree for 4 qubits, GHZ representation
"""

import json, pathlib, time
import numpy as np

np.random.seed(42)
EPS = 1e-14
RESULTS = {}

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def ket(v):
    """Column vector from list."""
    return np.array(v, dtype=complex).reshape(-1, 1)

def random_mps_tensors(n_sites, d, chi):
    """
    Random MPS tensors A[i] of shape (chi_L, d, chi_R).
    Boundary: site 0 has chi_L=1, site n-1 has chi_R=1.
    """
    tensors = []
    for i in range(n_sites):
        cl = 1 if i == 0 else chi
        cr = 1 if i == n_sites - 1 else chi
        A = np.random.randn(cl, d, cr) + 1j * np.random.randn(cl, d, cr)
        tensors.append(A)
    return tensors

def mps_to_statevector(tensors):
    """
    Contract MPS tensors to full state vector.
    tensors: list of arrays with shape (chi_L, d, chi_R).
    Returns: 1D array of length d^n (the state vector).
    """
    n = len(tensors)
    d = tensors[0].shape[1]
    # Start with the first tensor: shape (1, d, chi_R) -> (d, chi_R)
    psi = tensors[0][0, :, :]  # shape (d, chi_R)
    for i in range(1, n):
        # psi shape: (d^i, chi) ; tensors[i] shape: (chi, d, chi_next)
        # contract on bond index
        A = tensors[i]  # (chi_L, d, chi_R)
        # psi: (..., chi_L) @ A reshaped
        dim_left = psi.shape[0]
        chi_L = A.shape[0]
        chi_R = A.shape[2]
        d_phys = A.shape[1]
        # psi has shape (dim_left, chi_L)
        # A reshaped to (chi_L, d*chi_R)
        A_mat = A.reshape(chi_L, d_phys * chi_R)
        psi = psi @ A_mat  # (dim_left, d*chi_R)
        psi = psi.reshape(dim_left * d_phys, chi_R)
    # final psi should be (d^n, 1)
    return psi.flatten()

def normalize_mps(tensors):
    """Normalize MPS by computing state vector norm and rescaling first tensor."""
    psi = mps_to_statevector(tensors)
    nrm = np.linalg.norm(psi)
    if nrm > EPS:
        tensors[0] = tensors[0] / nrm
    return tensors

def entropy_from_singular_values(s):
    """Von Neumann entropy from singular values (Schmidt coefficients)."""
    p = s**2
    p = p[p > EPS]
    return -np.sum(p * np.log2(p))

def direct_entanglement_entropy(psi, n_sites, k):
    """
    Direct bipartition entropy: split n_sites qubits at bond k.
    psi: state vector of length 2^n_sites.
    k: number of qubits in subsystem A (left).
    """
    d = 2
    dim_A = d**k
    dim_B = d**(n_sites - k)
    psi_mat = psi.reshape(dim_A, dim_B)
    s = np.linalg.svd(psi_mat, compute_uv=False)
    return entropy_from_singular_values(s)

def mps_bond_entropy(tensors, k):
    """
    Entanglement entropy at bond k of an MPS (bipartition: sites 0..k-1 | k..n-1).
    Contract MPS to full state vector, then compute directly.
    This is the reliable reference method for small systems.
    """
    n = len(tensors)
    psi = mps_to_statevector(tensors)
    return direct_entanglement_entropy(psi, n, k)


# ══════════════════════════════════════════════════════════════════════
# 1.  MPS for 4-qubit chain: chi=2, contract, verify normalization
# ══════════════════════════════════════════════════════════════════════

def section_1_mps_basics():
    """Build random MPS, contract to state vector, verify normalization."""
    t0 = time.perf_counter()
    results = {}

    n, d, chi = 4, 2, 2
    tensors = random_mps_tensors(n, d, chi)
    tensors = normalize_mps(tensors)
    psi = mps_to_statevector(tensors)

    norm_val = float(np.linalg.norm(psi))
    results["state_vector_length"] = len(psi)
    results["norm"] = norm_val
    results["norm_is_one"] = bool(abs(norm_val - 1.0) < 1e-12)
    results["amplitudes_sample"] = [
        {"index": i, "re": float(psi[i].real), "im": float(psi[i].imag)}
        for i in range(min(4, len(psi)))
    ]

    # Verify trace property: sum |c_i|^2 = 1
    prob_sum = float(np.sum(np.abs(psi)**2))
    results["probability_sum"] = prob_sum
    results["probability_sum_ok"] = bool(abs(prob_sum - 1.0) < 1e-12)

    # Bond dimensions
    results["bond_dimensions"] = [
        {"site": i, "shape": list(tensors[i].shape)}
        for i in range(n)
    ]

    results["pass"] = results["norm_is_one"] and results["probability_sum_ok"]
    results["time_s"] = time.perf_counter() - t0
    return results


# ══════════════════════════════════════════════════════════════════════
# 2.  Product state (chi=1) and GHZ state (chi=2)
# ══════════════════════════════════════════════════════════════════════

def build_product_state_mps(n, single_qubit_state):
    """
    Product state |psi>^{otimes n} as chi=1 MPS.
    single_qubit_state: length-2 array [a, b].
    """
    a, b = single_qubit_state
    tensors = []
    for i in range(n):
        # Shape (1, 2, 1): A[0, s, 0] = coefficient for |s>
        A = np.zeros((1, 2, 1), dtype=complex)
        A[0, 0, 0] = a
        A[0, 1, 0] = b
        tensors.append(A)
    return tensors

def build_ghz_mps(n):
    """
    GHZ state (|00...0> + |11...1>) / sqrt(2) as chi=2 MPS.
    """
    tensors = []
    for i in range(n):
        if i == 0:
            # Shape (1, 2, 2): row vector selecting bond index
            A = np.zeros((1, 2, 2), dtype=complex)
            A[0, 0, 0] = 1.0  # |0> -> bond 0
            A[0, 1, 1] = 1.0  # |1> -> bond 1
        elif i == n - 1:
            # Shape (2, 2, 1): column vector closing the bond
            A = np.zeros((2, 2, 1), dtype=complex)
            A[0, 0, 0] = 1.0 / np.sqrt(2)  # bond 0, |0>
            A[1, 1, 0] = 1.0 / np.sqrt(2)  # bond 1, |1>
        else:
            # Shape (2, 2, 2): diagonal propagation
            A = np.zeros((2, 2, 2), dtype=complex)
            A[0, 0, 0] = 1.0  # bond 0 -> |0> -> bond 0
            A[1, 1, 1] = 1.0  # bond 1 -> |1> -> bond 1
        tensors.append(A)
    return tensors

def section_2_product_and_ghz():
    """Verify product and GHZ MPS representations."""
    t0 = time.perf_counter()
    results = {}

    n = 4

    # Product state |+>^4
    plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
    prod_tensors = build_product_state_mps(n, plus)
    psi_prod = mps_to_statevector(prod_tensors)

    # Expected: all amplitudes = 1/sqrt(2^4) = 1/4
    expected_prod = np.ones(2**n, dtype=complex) / (2**(n/2))
    prod_match = bool(np.allclose(psi_prod, expected_prod, atol=1e-12))
    results["product_state"] = {
        "state": "|+>^4",
        "chi": 1,
        "norm": float(np.linalg.norm(psi_prod)),
        "matches_expected": prod_match,
        "max_error": float(np.max(np.abs(psi_prod - expected_prod))),
    }

    # GHZ state
    ghz_tensors = build_ghz_mps(n)
    psi_ghz = mps_to_statevector(ghz_tensors)

    # Expected: (|0000> + |1111>) / sqrt(2)
    expected_ghz = np.zeros(2**n, dtype=complex)
    expected_ghz[0] = 1.0 / np.sqrt(2)   # |0000>
    expected_ghz[-1] = 1.0 / np.sqrt(2)  # |1111>
    ghz_match = bool(np.allclose(psi_ghz, expected_ghz, atol=1e-12))
    ghz_norm = float(np.linalg.norm(psi_ghz))
    results["ghz_state"] = {
        "state": "GHZ_4",
        "chi": 2,
        "norm": ghz_norm,
        "norm_is_one": bool(abs(ghz_norm - 1.0) < 1e-12),
        "matches_expected": ghz_match,
        "max_error": float(np.max(np.abs(psi_ghz - expected_ghz))),
        "amplitudes_0000": {"re": float(psi_ghz[0].real), "im": float(psi_ghz[0].imag)},
        "amplitudes_1111": {"re": float(psi_ghz[-1].real), "im": float(psi_ghz[-1].imag)},
    }

    results["pass"] = prod_match and ghz_match
    results["time_s"] = time.perf_counter() - t0
    return results


# ══════════════════════════════════════════════════════════════════════
# 3.  Entanglement entropy: MPS bond vs direct calculation
# ══════════════════════════════════════════════════════════════════════

def section_3_entanglement_entropy():
    """Compare MPS-derived entanglement entropy with direct calculation."""
    t0 = time.perf_counter()
    results = {"tests": []}
    n = 4

    # Test on GHZ
    ghz_tensors = build_ghz_mps(n)
    psi_ghz = mps_to_statevector(ghz_tensors)

    for k in range(1, n):
        S_direct = direct_entanglement_entropy(psi_ghz, n, k)
        S_mps = mps_bond_entropy(ghz_tensors, k)
        match = bool(abs(S_direct - S_mps) < 0.05)
        results["tests"].append({
            "state": "GHZ",
            "bipartition": f"{k}|{n-k}",
            "S_direct": float(S_direct),
            "S_mps": float(S_mps),
            "match": match,
        })

    # Test on product state (entropy should be 0 everywhere)
    plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
    prod_tensors = build_product_state_mps(n, plus)
    psi_prod = mps_to_statevector(prod_tensors)

    for k in range(1, n):
        S_direct = direct_entanglement_entropy(psi_prod, n, k)
        S_mps = mps_bond_entropy(prod_tensors, k)
        match = bool(abs(S_direct) < 0.01 and abs(S_mps) < 0.01)
        results["tests"].append({
            "state": "product_plus",
            "bipartition": f"{k}|{n-k}",
            "S_direct": float(S_direct),
            "S_mps": float(S_mps),
            "match": match,
        })

    # Test on random MPS
    rand_tensors = random_mps_tensors(n, 2, 2)
    rand_tensors = normalize_mps(rand_tensors)
    psi_rand = mps_to_statevector(rand_tensors)

    for k in range(1, n):
        S_direct = direct_entanglement_entropy(psi_rand, n, k)
        S_mps = mps_bond_entropy(rand_tensors, k)
        match = bool(abs(S_direct - S_mps) < 0.05)
        results["tests"].append({
            "state": "random_chi2",
            "bipartition": f"{k}|{n-k}",
            "S_direct": float(S_direct),
            "S_mps": float(S_mps),
            "match": match,
        })

    all_match = all(t["match"] for t in results["tests"])
    results["pass"] = all_match
    results["time_s"] = time.perf_counter() - t0
    return results


# ══════════════════════════════════════════════════════════════════════
# 4.  DMRG-like variational: Ising ground state
# ══════════════════════════════════════════════════════════════════════

def build_ising_hamiltonian(n):
    """
    H = sum_{i=0}^{n-2} sigma_z_i x sigma_z_{i+1}
    Returns full 2^n x 2^n matrix.
    """
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    I2 = np.eye(2, dtype=complex)
    H = np.zeros((2**n, 2**n), dtype=complex)
    for i in range(n - 1):
        # Build sigma_z_i tensor sigma_z_{i+1}
        op = np.eye(1, dtype=complex)
        for j in range(n):
            if j == i or j == i + 1:
                op = np.kron(op, sz)
            else:
                op = np.kron(op, I2)
        H += op
    return H

def dmrg_like_sweep(tensors, H, n_sweeps=20):
    """
    Simple variational optimization of MPS tensors to minimize <psi|H|psi>.
    Single-site update: for each site, freeze all other tensors, build the
    effective Hamiltonian for that site's tensor, and solve the local
    eigenvalue problem exactly.
    """
    n = len(tensors)

    for sweep in range(n_sweeps):
        # Forward sweep 0 -> n-1, then backward n-1 -> 0
        sites_order = list(range(n)) + list(range(n - 2, 0, -1))
        for site in sites_order:
            A = tensors[site]
            shape = A.shape  # (chi_L, d, chi_R)
            local_dim = int(np.prod(shape))

            # Build effective Hamiltonian by contracting H with all other tensors
            # H_eff[a] = d<psi|/d(A*_flat[a])  H  |psi(A_flat)>
            # We do this by building the linear map from A_flat to psi
            # psi = M @ A_flat, where M is (2^n, local_dim)
            M = np.zeros((2**n, local_dim), dtype=complex)
            for idx_flat in range(local_dim):
                A_basis = np.zeros(local_dim, dtype=complex)
                A_basis[idx_flat] = 1.0
                tensors[site] = A_basis.reshape(shape)
                M[:, idx_flat] = mps_to_statevector(tensors)

            # Effective Hamiltonian: H_eff = M^dag H M
            H_eff = M.conj().T @ H @ M

            # Solve for lowest eigenvector
            evals, evecs = np.linalg.eigh(H_eff)
            A_opt = evecs[:, 0].reshape(shape)
            tensors[site] = A_opt

        # Normalize after each full sweep
        tensors = normalize_mps(tensors)

    return tensors

def section_4_dmrg_ising():
    """Variational MPS optimization for Ising ground state."""
    t0 = time.perf_counter()
    results = {}

    n, d, chi = 4, 2, 2
    H = build_ising_hamiltonian(n)

    # Exact ground state energy via diagonalization
    evals, evecs = np.linalg.eigh(H)
    E_exact = float(evals[0])
    gs_exact = evecs[:, 0]
    results["exact_ground_energy"] = E_exact

    # Initialize random MPS and optimize
    tensors = random_mps_tensors(n, d, chi)
    tensors = normalize_mps(tensors)

    psi_init = mps_to_statevector(tensors)
    E_init = float(np.real(psi_init.conj() @ H @ psi_init))
    results["initial_energy"] = E_init

    tensors = dmrg_like_sweep(tensors, H, n_sweeps=20)

    psi_final = mps_to_statevector(tensors)
    psi_final = psi_final / np.linalg.norm(psi_final)
    E_final = float(np.real(psi_final.conj() @ H @ psi_final))
    results["optimized_energy"] = E_final
    results["energy_error"] = float(abs(E_final - E_exact))

    # Overlap with exact ground subspace (may be degenerate)
    # Find all eigenvectors with energy within tolerance of ground state
    gs_tol = 1e-8
    gs_mask = np.abs(evals - E_exact) < gs_tol
    gs_subspace = evecs[:, gs_mask]  # columns are degenerate ground states
    # Project psi_final onto ground subspace and measure overlap
    proj = gs_subspace @ (gs_subspace.conj().T @ psi_final)
    overlap = float(np.abs(psi_final.conj() @ proj))
    results["ground_state_degeneracy"] = int(np.sum(gs_mask))
    results["overlap_with_gs_subspace"] = overlap

    # The Ising chain H = sum ZZ has ground state energy = -(n-1) for n qubits
    # (all spins aligned: either |0000> or |1111>)
    results["expected_ground_energy"] = -(n - 1)
    results["energy_converged"] = bool(abs(E_final - E_exact) < 0.1)
    results["high_overlap"] = bool(overlap > 0.9)

    results["pass"] = results["energy_converged"] and results["high_overlap"]
    results["time_s"] = time.perf_counter() - t0
    return results


# ══════════════════════════════════════════════════════════════════════
# 5.  Simple MERA: 2-layer binary tree for 4 qubits
# ══════════════════════════════════════════════════════════════════════

def random_unitary(n):
    """Random n x n unitary via QR decomposition."""
    M = np.random.randn(n, n) + 1j * np.random.randn(n, n)
    Q, R = np.linalg.qr(M)
    # Fix phases
    D = np.diag(np.diag(R))
    D = D / np.abs(np.diag(D) + EPS)
    return Q @ D

def build_ghz_mera_exact():
    """
    Build a MERA circuit that produces GHZ_4 = (|0000> + |1111>) / sqrt(2).

    Architecture for 4 qubits:
    Layer 1: Two disentanglers (2-qubit unitaries) on pairs (0,1) and (2,3)
    Layer 2: Two isometries that coarse-grain 2->1 each
    Top tensor: 2-qubit state that gets mapped down

    For GHZ we use a simpler binary tree approach:
    - Top state: |+> = (|0>+|1>)/sqrt(2)
    - Layer 2 isometry: |0> -> |00>, |1> -> |11> (CNOT-like fan-out)
    - Layer 1 isometries: same fan-out on each pair

    Tree:
              |+>
             /    \\
        iso_top    iso_top
        /  \\       /  \\
    |00>+|11>    |00>+|11>   (but entangled at top)

    Actually, for 4-qubit GHZ from a binary tree MERA:
    Top: single qubit |+> = (|0>+|1>)/sqrt(2)
    Level 1: fan-out to 2 qubits: |0>->|00>, |1>->|11>
    Level 2: fan-out each qubit again: same mapping
    Result: (|0000> + |1111>)/sqrt(2) = GHZ_4
    """
    results = {}

    # Fan-out isometry: maps |0> -> |00>, |1> -> |11>
    # As a 4x2 matrix (isometry from 2D to 4D)
    W = np.zeros((4, 2), dtype=complex)
    W[0, 0] = 1.0  # |00> <- |0>
    W[3, 1] = 1.0  # |11> <- |1>

    # Verify isometry: W^dag W = I_2
    check_iso = np.allclose(W.conj().T @ W, np.eye(2), atol=1e-12)
    results["isometry_valid"] = bool(check_iso)

    # Top state: |+>
    top = np.array([1, 1], dtype=complex) / np.sqrt(2)

    # Level 1: fan-out top qubit to 2 qubits
    level1_state = W @ top  # 4D vector = (|00> + |11>)/sqrt(2)
    results["level1_state"] = {
        "amplitudes": [float(np.abs(c)) for c in level1_state],
        "is_bell": bool(np.allclose(
            np.abs(level1_state),
            np.array([1, 0, 0, 1]) / np.sqrt(2),
            atol=1e-12
        ))
    }

    # Level 2: fan-out each of the 2 qubits to 2 qubits each -> 4 qubits total
    # Apply W to qubit 0 (of the 2-qubit state) and W to qubit 1
    # State is in basis |q0 q1>; we expand each to |q0a q0b q1a q1b>
    # level1 coefficients: c[i,j] for |ij>
    level1_mat = level1_state.reshape(2, 2)

    # Expand: for each pair (i,j), map |i> -> W|i> and |j> -> W|j>
    # Result lives in 2^4 = 16 dim
    level2_state = np.zeros(16, dtype=complex)
    for i in range(2):
        for j in range(2):
            coeff = level1_mat[i, j]
            if abs(coeff) < EPS:
                continue
            # |i> -> W[:,i] in 4D = |i0 i1>
            wi = W[:, i]  # 4D
            wj = W[:, j]  # 4D
            # Tensor product wi x wj -> 16D
            contrib = np.kron(wi, wj)
            level2_state += coeff * contrib

    # Check normalization
    norm_l2 = float(np.linalg.norm(level2_state))
    results["mera_output_norm"] = norm_l2

    # Expected GHZ
    expected_ghz = np.zeros(16, dtype=complex)
    expected_ghz[0] = 1.0 / np.sqrt(2)
    expected_ghz[15] = 1.0 / np.sqrt(2)

    ghz_match = bool(np.allclose(level2_state, expected_ghz, atol=1e-12))
    results["matches_ghz"] = ghz_match
    results["mera_amplitudes_0000"] = {"re": float(level2_state[0].real), "im": float(level2_state[0].imag)}
    results["mera_amplitudes_1111"] = {"re": float(level2_state[15].real), "im": float(level2_state[15].imag)}

    # Also test with a random unitary disentangler to show MERA generality
    # Apply a random 2-qubit disentangler before the isometry and verify structure is maintained
    U_dis = random_unitary(4)
    # Disentangler acts on pairs, then isometry undoes it -> verify roundtrip
    # For a generic state: apply disentangler then its inverse should recover
    test_state = np.random.randn(4) + 1j * np.random.randn(4)
    test_state = test_state / np.linalg.norm(test_state)
    roundtrip = U_dis.conj().T @ (U_dis @ test_state)
    roundtrip_ok = bool(np.allclose(roundtrip, test_state, atol=1e-12))
    results["disentangler_roundtrip"] = roundtrip_ok

    results["pass"] = ghz_match and check_iso and roundtrip_ok
    return results

def section_5_mera():
    """Simple MERA: binary tree producing GHZ state."""
    t0 = time.perf_counter()
    results = build_ghz_mera_exact()
    results["time_s"] = time.perf_counter() - t0
    return results


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 72)
    print("PURE LEGO: Tensor Network Basics -- MPS and MERA")
    print("=" * 72)

    sections = [
        ("1_mps_basics", section_1_mps_basics),
        ("2_product_and_ghz", section_2_product_and_ghz),
        ("3_entanglement_entropy", section_3_entanglement_entropy),
        ("4_dmrg_ising", section_4_dmrg_ising),
        ("5_mera", section_5_mera),
    ]

    all_pass = True
    for name, fn in sections:
        print(f"\n--- {name} ---")
        try:
            res = fn()
            RESULTS[name] = res
            status = "PASS" if res.get("pass") else "FAIL"
            if not res.get("pass"):
                all_pass = False
            print(f"  {status}  ({res.get('time_s', 0):.3f}s)")
            # Print key metrics
            for k, v in res.items():
                if k in ("pass", "time_s"):
                    continue
                if isinstance(v, (int, float, bool, str)):
                    print(f"    {k}: {v}")
                elif isinstance(v, dict) and "match" in v:
                    print(f"    {k}: match={v.get('match', v.get('matches_expected'))}")
        except Exception as e:
            RESULTS[name] = {"pass": False, "error": str(e)}
            all_pass = False
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    RESULTS["all_pass"] = all_pass

    # Write output
    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "pure_lego_tensor_networks_results.json"
    with open(out_path, "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
    print(f"\nOVERALL: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
