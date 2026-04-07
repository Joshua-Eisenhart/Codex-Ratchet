#!/usr/bin/env python3
"""
sim_pure_lego_sic_mub.py
========================

Pure lego probe: SIC-POVM and Mutually Unbiased Bases for qubits (d=2).
No engine dependencies. numpy/scipy only.

Constructs:
  1. SIC-POVM for d=2: 4 rank-1 projectors from tetrahedron vertices on
     the Bloch sphere.  Verifies completeness, SIC inner-product condition,
     and informational completeness via density-matrix reconstruction.
  2. Three MUBs for d=2: Z, X, Y eigenbases.  Verifies mutual unbiasedness
     and that 3 = d+1 is the maximum count.
  3. Reconstructs a random density matrix from SIC probabilities and from
     MUB probabilities independently.  Compares reconstruction fidelity.

Outputs JSON results to a2_state/sim_results/.
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
from numpy.linalg import eigvalsh

# ═══════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════
D = 2  # qubit dimension

I2 = np.eye(D, dtype=complex)
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
SIGMAS = [SIGMA_X, SIGMA_Y, SIGMA_Z]

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)

# ═══════════════════════════════════════════════════════════════════
# Utility helpers
# ═══════════════════════════════════════════════════════════════════

def random_density_matrix(d=2, seed=None):
    """Generate a random valid density matrix via Ginibre ensemble."""
    rng = np.random.default_rng(seed)
    G = rng.standard_normal((d, d)) + 1j * rng.standard_normal((d, d))
    rho = G @ G.conj().T
    rho /= np.trace(rho)
    return rho


def fidelity(rho, sigma):
    """Quantum fidelity F(rho, sigma) for two density matrices.

    Uses the formula F = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2.
    For numerical stability with near-pure states, clamp eigenvalues.
    """
    from scipy.linalg import sqrtm
    sqrt_rho = sqrtm(rho)
    product = sqrt_rho @ sigma @ sqrt_rho
    # Force hermiticity
    product = (product + product.conj().T) / 2
    evals = eigvalsh(product)
    evals = np.maximum(evals, 0.0)
    return float(np.sum(np.sqrt(evals)) ** 2)


def is_valid_density(rho, tol=1e-10):
    """Check hermiticity, trace=1, positive semi-definiteness."""
    herm = np.allclose(rho, rho.conj().T, atol=tol)
    tr = np.isclose(np.trace(rho).real, 1.0, atol=tol)
    psd = np.all(eigvalsh(rho) > -tol)
    return herm and tr and psd


# ═══════════════════════════════════════════════════════════════════
# 1. SIC-POVM construction for d=2
# ═══════════════════════════════════════════════════════════════════

def build_sic_povm_d2():
    """Build the 4-element SIC-POVM for a qubit.

    The 4 Bloch vectors are the vertices of a regular tetrahedron
    inscribed in the Bloch sphere.  One standard choice:
        n0 = ( 0,  0,  1)
        n1 = (2sqrt(2)/3, 0, -1/3)
        n2 = (-sqrt(2)/3, sqrt(6)/3, -1/3)
        n3 = (-sqrt(2)/3, -sqrt(6)/3, -1/3)

    Each POVM element: Pi_k = (I + n_k . sigma) / (2d) = (I + n_k . sigma) / 4
    Note: (I + n_k . sigma)/2 is the rank-1 projector |psi_k><psi_k|,
    so Pi_k = |psi_k><psi_k| / d.
    """
    s2 = np.sqrt(2)
    s6 = np.sqrt(6)

    bloch_vectors = np.array([
        [0, 0, 1],
        [2*s2/3, 0, -1.0/3],
        [-s2/3, s6/3, -1.0/3],
        [-s2/3, -s6/3, -1.0/3],
    ])

    # Verify tetrahedron: all pairwise dot products should be -1/3
    for i in range(4):
        assert np.isclose(np.linalg.norm(bloch_vectors[i]), 1.0), \
            f"Bloch vector {i} not unit length"
    for i in range(4):
        for j in range(i+1, 4):
            dot = bloch_vectors[i] @ bloch_vectors[j]
            assert np.isclose(dot, -1.0/3, atol=1e-12), \
                f"Tetrahedron check failed: n{i}.n{j} = {dot}, expected -1/3"

    povm_elements = []
    for k in range(4):
        n = bloch_vectors[k]
        Pi_k = (I2 + n[0]*SIGMA_X + n[1]*SIGMA_Y + n[2]*SIGMA_Z) / (2 * D)
        povm_elements.append(Pi_k)

    return bloch_vectors, povm_elements


def verify_sic_povm(povm_elements):
    """Verify completeness and SIC inner-product condition."""
    results = {}
    d = D
    n_elements = len(povm_elements)

    # --- Completeness: sum of all elements = Identity ---
    total = sum(povm_elements)
    completeness_error = float(np.max(np.abs(total - I2)))
    results["completeness_max_error"] = completeness_error
    results["completeness_pass"] = completeness_error < 1e-12

    # --- SIC condition: Tr(Pi_i Pi_j) = (d*delta_ij + 1) / (d*(d+1)) ---
    # For d=2: diagonal = (2+1)/(2*3) = 1/2,  off-diag = 1/(2*3) = 1/6
    # But our Pi_k = projector/d, so Tr(Pi_i Pi_j) for the SIC-POVM is:
    #   (d*delta + 1) / (d^2 * (d+1))
    # For d=2: diagonal = 3/12 = 1/4, off-diag = 1/12
    expected_diag = (d * 1 + 1) / (d**2 * (d + 1))
    expected_off = 1.0 / (d**2 * (d + 1))

    sic_errors = []
    sic_pairs = []
    for i in range(n_elements):
        for j in range(n_elements):
            tr_val = np.trace(povm_elements[i] @ povm_elements[j]).real
            expected = expected_diag if i == j else expected_off
            err = abs(tr_val - expected)
            sic_errors.append(err)
            if i <= j:
                sic_pairs.append({
                    "i": i, "j": j,
                    "Tr(Pi_i Pi_j)": float(tr_val),
                    "expected": float(expected),
                    "error": float(err),
                })

    results["sic_condition_max_error"] = float(max(sic_errors))
    results["sic_condition_pass"] = max(sic_errors) < 1e-12
    results["sic_pairs"] = sic_pairs
    results["expected_diagonal"] = float(expected_diag)
    results["expected_off_diagonal"] = float(expected_off)

    return results


def sic_reconstruct(povm_elements, rho):
    """Reconstruct density matrix from SIC-POVM measurement probabilities.

    For a SIC-POVM with elements Pi_k = |psi_k><psi_k|/d, the Born
    probabilities are p_k = Tr(rho Pi_k).

    Reconstruction formula (exact for SIC):
        rho = sum_k [ (d+1)*p_k - 1/d ] * d * Pi_k

    This follows from the SIC frame property: the Pi_k form a tight frame
    for the space of Hermitian operators.
    """
    d = D
    n = len(povm_elements)

    # Born probabilities
    probs = np.array([np.trace(rho @ Pi).real for Pi in povm_elements])

    # Reconstruction
    rho_rec = np.zeros((d, d), dtype=complex)
    for k in range(n):
        coeff = (d + 1) * probs[k] - 1.0 / d
        rho_rec += coeff * d * povm_elements[k]

    return rho_rec, probs


# ═══════════════════════════════════════════════════════════════════
# 2. Mutually Unbiased Bases for d=2
# ═══════════════════════════════════════════════════════════════════

def build_mubs_d2():
    """Build the 3 MUBs for d=2: Z, X, Y eigenbases.

    Z basis: |0>, |1>
    X basis: |+> = (|0>+|1>)/sqrt(2),  |-> = (|0>-|1>)/sqrt(2)
    Y basis: |+i> = (|0>+i|1>)/sqrt(2), |-i> = (|0>-i|1>)/sqrt(2)
    """
    s = 1.0 / np.sqrt(2)

    z_basis = [
        np.array([1, 0], dtype=complex),
        np.array([0, 1], dtype=complex),
    ]
    x_basis = [
        np.array([s, s], dtype=complex),
        np.array([s, -s], dtype=complex),
    ]
    y_basis = [
        np.array([s, 1j*s], dtype=complex),
        np.array([s, -1j*s], dtype=complex),
    ]

    return [
        ("Z", z_basis),
        ("X", x_basis),
        ("Y", y_basis),
    ]


def verify_mubs(mubs):
    """Verify mutual unbiasedness: |<a|b>|^2 = 1/d for cross-basis pairs."""
    results = {}
    d = D
    n_bases = len(mubs)

    # Check orthonormality within each basis
    ortho_checks = []
    for name, basis in mubs:
        for i in range(d):
            for j in range(d):
                overlap = abs(np.vdot(basis[i], basis[j]))**2
                expected = 1.0 if i == j else 0.0
                ortho_checks.append({
                    "basis": name, "i": i, "j": j,
                    "overlap_sq": float(overlap),
                    "expected": expected,
                    "pass": np.isclose(overlap, expected, atol=1e-12),
                })
    results["orthonormality"] = ortho_checks
    results["orthonormality_pass"] = all(c["pass"] for c in ortho_checks)

    # Check mutual unbiasedness between different bases
    mub_checks = []
    for a_idx in range(n_bases):
        for b_idx in range(a_idx + 1, n_bases):
            name_a, basis_a = mubs[a_idx]
            name_b, basis_b = mubs[b_idx]
            for i in range(d):
                for j in range(d):
                    overlap_sq = abs(np.vdot(basis_a[i], basis_b[j]))**2
                    expected = 1.0 / d
                    mub_checks.append({
                        "bases": f"{name_a}-{name_b}",
                        "i": i, "j": j,
                        "overlap_sq": float(overlap_sq),
                        "expected": float(expected),
                        "error": float(abs(overlap_sq - expected)),
                        "pass": np.isclose(overlap_sq, expected, atol=1e-12),
                    })

    results["mutual_unbiasedness"] = mub_checks
    results["mutual_unbiasedness_pass"] = all(c["pass"] for c in mub_checks)
    results["num_mubs"] = n_bases
    results["max_mubs_for_d2"] = D + 1
    results["is_maximal_set"] = n_bases == D + 1

    return results


def mub_reconstruct(mubs, rho):
    """Reconstruct density matrix from MUB measurement probabilities.

    For d=2 with d+1=3 complete MUBs, the Bloch-vector reconstruction:
    Each MUB basis measures one Pauli component of rho = (I + r.sigma)/2.
    Z basis gives r_z, X basis gives r_x, Y basis gives r_y, via
        r_alpha = p_{alpha,0} - p_{alpha,1}
    where p_{alpha,k} = Tr(rho |alpha,k><alpha,k|).

    Then rho = (I + r_x X + r_y Y + r_z Z) / 2.
    """
    d = D

    # Map basis label to Pauli for Bloch reconstruction
    pauli_map = {"Z": SIGMA_Z, "X": SIGMA_X, "Y": SIGMA_Y}

    rho_rec = I2 / d  # start with I/2

    for name, basis in mubs:
        probs = []
        for k in range(d):
            psi = basis[k].reshape(-1, 1)
            proj = psi @ psi.conj().T
            p_k = np.trace(rho @ proj).real
            probs.append(p_k)
        # Bloch component: r_alpha = p_0 - p_1
        r_alpha = probs[0] - probs[1]
        rho_rec += (r_alpha / 2.0) * pauli_map[name]

    return rho_rec


# ═══════════════════════════════════════════════════════════════════
# 3. Informational completeness check
# ═══════════════════════════════════════════════════════════════════

def check_informational_completeness_sic(povm_elements):
    """Check that SIC-POVM is informationally complete.

    A POVM is IC iff its elements span the space of d x d Hermitian matrices,
    which has real dimension d^2.  For d=2, we need 4 linearly independent
    elements (as real vectors in R^4), and we have exactly 4 POVM elements.
    """
    d = D
    # Flatten each element to a real vector (Hermitian => use real+imag of upper triangle)
    # Simpler: just vectorize and check rank
    mat = np.array([Pi.flatten() for Pi in povm_elements])  # shape (4, 4) complex
    # Treat as real: stack real and imag
    mat_real = np.hstack([mat.real, mat.imag])
    rank = np.linalg.matrix_rank(mat_real, tol=1e-10)

    return {
        "num_elements": len(povm_elements),
        "required_rank": d**2,
        "actual_rank": int(rank),
        "informationally_complete": rank == d**2,
    }


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("SIC-POVM & MUB Pure Lego Probe  (d=2, qubits)")
    print("=" * 70)

    all_results = {
        "probe": "sim_pure_lego_sic_mub",
        "timestamp": datetime.now(UTC).isoformat(),
        "dimension": D,
    }

    # ── Build SIC-POVM ──
    print("\n[1] Building SIC-POVM (tetrahedron)...")
    bloch_vecs, sic_elements = build_sic_povm_d2()
    all_results["sic_bloch_vectors"] = bloch_vecs.tolist()

    print("    Verifying SIC conditions...")
    sic_verify = verify_sic_povm(sic_elements)
    all_results["sic_verification"] = sic_verify

    print(f"    Completeness:  {'PASS' if sic_verify['completeness_pass'] else 'FAIL'}"
          f"  (max err = {sic_verify['completeness_max_error']:.2e})")
    print(f"    SIC condition: {'PASS' if sic_verify['sic_condition_pass'] else 'FAIL'}"
          f"  (max err = {sic_verify['sic_condition_max_error']:.2e})")

    # ── Informational completeness ──
    print("\n[2] Checking informational completeness of SIC-POVM...")
    ic_result = check_informational_completeness_sic(sic_elements)
    all_results["sic_informational_completeness"] = ic_result
    print(f"    Rank: {ic_result['actual_rank']} / {ic_result['required_rank']}"
          f"  =>  IC: {'YES' if ic_result['informationally_complete'] else 'NO'}")

    # ── Build MUBs ──
    print("\n[3] Building 3 MUBs (Z, X, Y)...")
    mubs = build_mubs_d2()
    mub_verify = verify_mubs(mubs)
    all_results["mub_verification"] = mub_verify

    print(f"    Orthonormality:       {'PASS' if mub_verify['orthonormality_pass'] else 'FAIL'}")
    print(f"    Mutual unbiasedness:  {'PASS' if mub_verify['mutual_unbiasedness_pass'] else 'FAIL'}")
    print(f"    Maximal set (d+1=3):  {'YES' if mub_verify['is_maximal_set'] else 'NO'}")

    # ── Reconstruction comparison ──
    print("\n[4] Density matrix reconstruction comparison...")
    n_trials = 20
    sic_fidelities = []
    mub_fidelities = []

    for trial in range(n_trials):
        rho = random_density_matrix(d=D, seed=42 + trial)

        # SIC reconstruction
        rho_sic, sic_probs = sic_reconstruct(sic_elements, rho)
        f_sic = fidelity(rho, rho_sic)
        sic_fidelities.append(f_sic)

        # MUB reconstruction
        rho_mub = mub_reconstruct(mubs, rho)
        f_mub = fidelity(rho, rho_mub)
        mub_fidelities.append(f_mub)

    sic_fid_arr = np.array(sic_fidelities)
    mub_fid_arr = np.array(mub_fidelities)

    recon_results = {
        "n_trials": n_trials,
        "sic_fidelity_mean": float(sic_fid_arr.mean()),
        "sic_fidelity_min": float(sic_fid_arr.min()),
        "sic_fidelity_max": float(sic_fid_arr.max()),
        "sic_fidelity_std": float(sic_fid_arr.std()),
        "mub_fidelity_mean": float(mub_fid_arr.mean()),
        "mub_fidelity_min": float(mub_fid_arr.min()),
        "mub_fidelity_max": float(mub_fid_arr.max()),
        "mub_fidelity_std": float(mub_fid_arr.std()),
        "both_exact_reconstruction": bool(
            np.all(sic_fid_arr > 1.0 - 1e-10) and np.all(mub_fid_arr > 1.0 - 1e-10)
        ),
    }
    all_results["reconstruction_comparison"] = recon_results

    print(f"    SIC fidelity: mean={sic_fid_arr.mean():.12f}  "
          f"min={sic_fid_arr.min():.12f}")
    print(f"    MUB fidelity: mean={mub_fid_arr.mean():.12f}  "
          f"min={mub_fid_arr.min():.12f}")
    print(f"    Both exact:   {recon_results['both_exact_reconstruction']}")

    # ── One detailed example ──
    print("\n[5] Detailed single-state example...")
    rho_example = random_density_matrix(d=D, seed=1337)
    rho_sic_ex, sic_probs_ex = sic_reconstruct(sic_elements, rho_example)
    rho_mub_ex = mub_reconstruct(mubs, rho_example)

    example = {
        "rho_original": {
            "real": rho_example.real.tolist(),
            "imag": rho_example.imag.tolist(),
        },
        "sic_probabilities": sic_probs_ex.tolist(),
        "rho_sic_reconstructed": {
            "real": rho_sic_ex.real.tolist(),
            "imag": rho_sic_ex.imag.tolist(),
        },
        "rho_mub_reconstructed": {
            "real": rho_mub_ex.real.tolist(),
            "imag": rho_mub_ex.imag.tolist(),
        },
        "sic_fidelity": fidelity(rho_example, rho_sic_ex),
        "mub_fidelity": fidelity(rho_example, rho_mub_ex),
        "sic_reconstruction_error_frobenius": float(
            np.linalg.norm(rho_example - rho_sic_ex, 'fro')
        ),
        "mub_reconstruction_error_frobenius": float(
            np.linalg.norm(rho_example - rho_mub_ex, 'fro')
        ),
        "sic_reconstructed_is_valid_density": is_valid_density(rho_sic_ex),
        "mub_reconstructed_is_valid_density": is_valid_density(rho_mub_ex),
    }
    all_results["detailed_example"] = example

    print(f"    SIC recon fidelity:  {example['sic_fidelity']:.14f}")
    print(f"    MUB recon fidelity:  {example['mub_fidelity']:.14f}")
    print(f"    SIC Frobenius error: {example['sic_reconstruction_error_frobenius']:.2e}")
    print(f"    MUB Frobenius error: {example['mub_reconstruction_error_frobenius']:.2e}")

    # ── Verdicts ──
    all_pass = (
        sic_verify["completeness_pass"]
        and sic_verify["sic_condition_pass"]
        and ic_result["informationally_complete"]
        and mub_verify["orthonormality_pass"]
        and mub_verify["mutual_unbiasedness_pass"]
        and mub_verify["is_maximal_set"]
        and recon_results["both_exact_reconstruction"]
    )

    all_results["all_pass"] = all_pass

    print("\n" + "=" * 70)
    print(f"OVERALL VERDICT: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}")
    print("=" * 70)

    # ── Write output ──
    # Custom encoder for numpy types
    class NumpyEncoder(json.JSONEncoder):
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

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "sic_mub_pure_lego_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, cls=NumpyEncoder)
    print(f"\nResults written to: {out_path}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
