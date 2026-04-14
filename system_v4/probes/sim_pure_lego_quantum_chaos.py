#!/usr/bin/env python3
"""
sim_pure_lego_quantum_chaos.py
Pure-lego probe: quantum chaos signatures via level-spacing statistics
and eigenstate thermalization hypothesis (ETH) checks.

No engine dependencies. numpy + scipy only.

Probes
------
1. GUE random matrix  -> Wigner-Dyson r ≈ 0.5307
2. Integrable (non-interacting σ_z) -> Poisson r ≈ 0.3863
3. Chaotic (random Heisenberg) -> Wigner-Dyson r ≈ 0.5307
4. ETH diagonal smoothness + off-diagonal scaling
"""

import json
import os
import time
import numpy as np
from scipy import linalg as la
classification = "classical_baseline"  # auto-backfill

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
N_QUBITS = 4
DIM = 2 ** N_QUBITS  # 16
SEED = 42

# Reference values for spacing ratio <r>
# Atas et al., PRL 110, 084101 (2013)
R_WD_GOE = 0.5307    # Wigner-Dyson (GOE, beta=1)
R_WD_GUE = 0.5996    # Wigner-Dyson (GUE, beta=2)
R_POISSON = 0.3863   # Poisson (integrable)
TOLERANCE = 0.06     # acceptance band for finite-size matrices

# Pauli matrices
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
IDENTITY_2 = np.eye(2, dtype=complex)

PAULIS = [SIGMA_X, SIGMA_Y, SIGMA_Z]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def kron_chain(ops):
    """Tensor product of a list of 2x2 operators."""
    result = ops[0]
    for op in ops[1:]:
        result = np.kron(result, op)
    return result


def single_site_op(op, site, n_qubits):
    """Embed a single-qubit operator at `site` in an n_qubits chain."""
    ops = [IDENTITY_2] * n_qubits
    ops[site] = op
    return kron_chain(ops)


def two_site_heisenberg(i, j, n_qubits):
    """σ_i · σ_j = σ_x⊗σ_x + σ_y⊗σ_y + σ_z⊗σ_z on sites i,j."""
    H = np.zeros((DIM, DIM), dtype=complex)
    for pauli in PAULIS:
        H += single_site_op(pauli, i, n_qubits) @ single_site_op(pauli, j, n_qubits)
    return H


def spacing_ratios(eigenvalues):
    """
    Compute consecutive spacing ratios r_n = min(s_n, s_{n+1})/max(s_n, s_{n+1}).
    eigenvalues must be sorted.
    """
    evals = np.sort(np.real(eigenvalues))
    spacings = np.diff(evals)
    # Remove near-zero spacings (degeneracies) to avoid division issues
    spacings = spacings[spacings > 1e-12]
    if len(spacings) < 2:
        return np.array([]), 0.0
    s_n = spacings[:-1]
    s_n1 = spacings[1:]
    r = np.minimum(s_n, s_n1) / np.maximum(s_n, s_n1)
    return r, float(np.mean(r))


# ---------------------------------------------------------------------------
# Probe 1: GUE random matrix
# ---------------------------------------------------------------------------

def probe_gue(rng):
    """
    Draw ensemble of GUE matrices, verify Wigner-Dyson statistics.

    Use d=256 for the pure GUE test to reduce finite-size effects.
    The bulk eigenvalues (middle 80%) are used to avoid edge effects.
    """
    gue_dim = 256
    n_realizations = 100
    all_ratios = []
    sample_evals = None

    for _ in range(n_realizations):
        A = rng.standard_normal((gue_dim, gue_dim)) + 1j * rng.standard_normal((gue_dim, gue_dim))
        H = (A + A.conj().T) / 2.0
        evals = np.sort(la.eigvalsh(H))
        if sample_evals is None:
            sample_evals = evals

        # Use bulk eigenvalues (middle 80%) to avoid edge effects
        n_edge = gue_dim // 10
        bulk = evals[n_edge:-n_edge]
        r_vals, _ = spacing_ratios(bulk)
        all_ratios.extend(r_vals.tolist())

    r_mean = float(np.mean(all_ratios))
    passed = abs(r_mean - R_WD_GUE) < TOLERANCE
    return {
        "probe": "GUE_random_matrix",
        "dimension": gue_dim,
        "n_realizations": n_realizations,
        "n_ratios_collected": len(all_ratios),
        "r_mean": round(r_mean, 4),
        "r_expected": R_WD_GUE,
        "delta": round(abs(r_mean - R_WD_GUE), 4),
        "tolerance": TOLERANCE,
        "passed": bool(passed),
        "eigenvalue_range": [round(float(sample_evals[0]), 4), round(float(sample_evals[-1]), 4)],
    }


# ---------------------------------------------------------------------------
# Probe 2: Integrable Hamiltonian (non-interacting σ_z)
# ---------------------------------------------------------------------------

def probe_integrable(rng):
    """
    H = Σ_i h_i σ_z^(i), non-interacting.
    Should show Poisson level statistics.

    NOTE: The raw spectrum of Σ h_i σ_z^(i) has massive degeneracies and
    regular structure. To get clean Poisson statistics, we need many
    independent symmetry sectors. We use random h_i and unfold the spectrum
    to remove the global density of states trend, then compute spacing ratios.

    For a more robust test, we average over multiple random realizations.
    """
    n_realizations = 200
    all_ratios = []

    for _ in range(n_realizations):
        h_fields = rng.standard_normal(N_QUBITS) * 3.0
        # Add small incommensurate fields to break exact degeneracies
        h_fields += rng.uniform(0.01, 0.1, N_QUBITS)

        H = np.zeros((DIM, DIM), dtype=complex)
        for i in range(N_QUBITS):
            H += h_fields[i] * single_site_op(SIGMA_Z, i, N_QUBITS)

        evals = np.sort(np.real(la.eigvalsh(H)))

        # Unfolding: map eigenvalues through their cumulative distribution
        # For integrable systems with few degrees of freedom, use local unfolding
        spacings = np.diff(evals)
        # Remove exact degeneracies
        spacings = spacings[spacings > 1e-10]
        if len(spacings) < 2:
            continue

        # Local unfolding via polynomial fit
        indices = np.arange(len(evals))
        coeffs = np.polyfit(evals, indices, deg=3)
        unfolded = np.polyval(coeffs, evals)
        uf_spacings = np.diff(unfolded)
        uf_spacings = uf_spacings[uf_spacings > 1e-10]

        if len(uf_spacings) < 2:
            continue

        s_n = uf_spacings[:-1]
        s_n1 = uf_spacings[1:]
        r = np.minimum(s_n, s_n1) / np.maximum(s_n, s_n1)
        all_ratios.extend(r.tolist())

    r_mean = float(np.mean(all_ratios)) if all_ratios else 0.0
    passed = abs(r_mean - R_POISSON) < TOLERANCE

    return {
        "probe": "integrable_noninteracting_sigma_z",
        "dimension": DIM,
        "n_qubits": N_QUBITS,
        "n_realizations": n_realizations,
        "n_ratios_collected": len(all_ratios),
        "r_mean": round(r_mean, 4),
        "r_expected": R_POISSON,
        "delta": round(abs(r_mean - R_POISSON), 4),
        "tolerance": TOLERANCE,
        "passed": bool(passed),
    }


# ---------------------------------------------------------------------------
# Probe 3: Chaotic Hamiltonian (random Heisenberg)
# ---------------------------------------------------------------------------

def build_chaotic_hamiltonian(rng):
    """Build a single chaotic random Heisenberg Hamiltonian with symmetry-breaking fields."""
    J = rng.standard_normal((N_QUBITS, N_QUBITS))
    J = (J + J.T) / 2

    H = np.zeros((DIM, DIM), dtype=complex)
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            H += J[i, j] * two_site_heisenberg(i, j, N_QUBITS)

    # Random on-site fields in x, y, z to break all symmetries
    # σ_y fields break time-reversal -> GUE
    for i in range(N_QUBITS):
        for k, pauli in enumerate(PAULIS):
            H += rng.standard_normal() * 0.3 * single_site_op(pauli, i, N_QUBITS)

    assert np.allclose(H, H.conj().T), "Hamiltonian not Hermitian"
    return H


def probe_chaotic_heisenberg(rng):
    """
    H = Σ_{i<j} J_ij (σ_i · σ_j) with random couplings, ensemble-averaged.
    Should show Wigner-Dyson (GUE) level statistics.
    Returns stats and a single representative (evals, evecs, H) for ETH.
    """
    n_realizations = 200
    all_ratios = []
    # Keep the first realization for ETH probe
    eth_evals, eth_evecs, eth_H = None, None, None

    # First compute empirical GUE reference at d=16 (finite-size calibration)
    cal_rng = np.random.default_rng(9999)
    cal_ratios = []
    for _ in range(2000):
        A = cal_rng.standard_normal((DIM, DIM)) + 1j * cal_rng.standard_normal((DIM, DIM))
        Hcal = (A + A.conj().T) / 2.0
        ev = la.eigvalsh(Hcal)
        rv, _ = spacing_ratios(ev)
        cal_ratios.extend(rv.tolist())
    r_gue_d16 = float(np.mean(cal_ratios))

    for idx in range(n_realizations):
        H = build_chaotic_hamiltonian(rng)
        evals, evecs = la.eigh(H)
        if idx == 0:
            eth_evals, eth_evecs, eth_H = evals, evecs, H
        r_vals, _ = spacing_ratios(evals)
        all_ratios.extend(r_vals.tolist())

    r_mean = float(np.mean(all_ratios))
    # Compare against finite-size GUE reference, not infinite-d
    passed = abs(r_mean - r_gue_d16) < TOLERANCE

    return {
        "probe": "chaotic_random_heisenberg",
        "dimension": DIM,
        "n_qubits": N_QUBITS,
        "n_realizations": n_realizations,
        "n_ratios_collected": len(all_ratios),
        "r_mean": round(r_mean, 4),
        "r_expected_infinite_d": R_WD_GUE,
        "r_gue_finite_d16": round(r_gue_d16, 4),
        "delta_vs_finite_gue": round(abs(r_mean - r_gue_d16), 4),
        "tolerance": TOLERANCE,
        "passed": bool(passed),
        "eigenvalue_range": [round(float(eth_evals[0]), 4), round(float(eth_evals[-1]), 4)],
    }, eth_evals, eth_evecs, eth_H


# ---------------------------------------------------------------------------
# Probe 4: Eigenstate Thermalization Hypothesis (ETH)
# ---------------------------------------------------------------------------

def probe_eth(evals, evecs, H, rng):
    """
    ETH check using O = σ_z on first qubit.

    Diagonal: <n|O|n> should be a smooth function of E_n.
    Off-diagonal: |<n|O|m>|^2 should scale as e^{-S(E)} ~ 1/D
    where D is the Hilbert space dimension.
    """
    O = single_site_op(SIGMA_Z, 0, N_QUBITS)

    # Observable in energy eigenbasis
    O_eig = evecs.conj().T @ O @ evecs

    # --- Diagonal ETH ---
    diag = np.real(np.diag(O_eig))

    # Smoothness check: fit polynomial to diagonal vs energy
    # Residuals should be small for a smooth function
    coeffs = np.polyfit(evals, diag, deg=3)
    fitted = np.polyval(coeffs, evals)
    residuals = diag - fitted
    rms_residual = float(np.sqrt(np.mean(residuals ** 2)))
    diag_range = float(np.max(diag) - np.min(diag))
    # Relative residual: smooth means small fluctuations around the fit
    relative_residual = rms_residual / max(diag_range, 1e-10)

    # For d=16 (small), fluctuations are O(1/sqrt(D)) ~ 0.25
    # So we use a generous threshold
    diag_smooth = relative_residual < 0.5

    # --- Off-diagonal ETH ---
    # |<n|O|m>|^2 for n != m
    off_diag_sq = np.abs(O_eig) ** 2
    np.fill_diagonal(off_diag_sq, 0)

    # Mean off-diagonal |O_{nm}|^2
    n_offdiag = DIM * (DIM - 1)
    mean_offdiag_sq = float(np.sum(off_diag_sq) / n_offdiag)

    # ETH predicts |O_{nm}|^2 ~ e^{-S(E)} ~ 1/D for microcanonical
    # For our operator with ||O|| = 1 (eigenvalues ±1), and D=16:
    # expected scale ~ 1/D = 0.0625
    expected_scale = 1.0 / DIM
    scale_ratio = mean_offdiag_sq / expected_scale

    # Check that off-diagonal elements scale roughly as 1/D
    # Allow factor of 5 for finite-size effects
    offdiag_scaling_ok = 0.05 < scale_ratio < 5.0

    # --- Energy-resolved off-diagonal structure ---
    # For states near the middle of the spectrum, off-diagonal
    # elements should be roughly uniform (no large outliers)
    mid = DIM // 2
    window = DIM // 4
    mid_slice = off_diag_sq[mid - window:mid + window, mid - window:mid + window]
    mid_mean = float(np.mean(mid_slice[mid_slice > 0]))
    mid_std = float(np.std(mid_slice[mid_slice > 0]))
    # Coefficient of variation should be O(1) for random-matrix-like
    cv = mid_std / max(mid_mean, 1e-15)

    passed = diag_smooth and offdiag_scaling_ok

    return {
        "probe": "ETH_check_sigma_z_qubit_0",
        "observable": "sigma_z site 0",
        "dimension": DIM,
        "diagonal_eth": {
            "rms_residual": round(rms_residual, 6),
            "diag_range": round(diag_range, 4),
            "relative_residual": round(relative_residual, 4),
            "smooth": bool(diag_smooth),
        },
        "offdiagonal_eth": {
            "mean_offdiag_sq": round(mean_offdiag_sq, 6),
            "expected_1_over_D": round(expected_scale, 6),
            "scale_ratio": round(scale_ratio, 4),
            "scaling_ok": bool(offdiag_scaling_ok),
            "mid_spectrum_cv": round(cv, 4),
        },
        "passed": bool(passed),
        "diagnostic_diagonal_elements": [round(float(d), 4) for d in diag],
        "diagnostic_energies": [round(float(e), 4) for e in evals],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    rng = np.random.default_rng(SEED)
    t0 = time.time()

    results = {
        "probe_name": "pure_lego_quantum_chaos",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "parameters": {
            "n_qubits": N_QUBITS,
            "dimension": DIM,
            "seed": SEED,
            "r_wigner_dyson_gue": R_WD_GUE,
            "r_poisson": R_POISSON,
            "tolerance": TOLERANCE,
        },
        "probes": {},
    }

    # Probe 1: GUE
    print("Probe 1: GUE random matrix ...")
    gue_result = probe_gue(rng)
    results["probes"]["gue"] = gue_result
    tag = "PASS" if gue_result["passed"] else "FAIL"
    print(f"  r_mean = {gue_result['r_mean']} (expected {R_WD_GUE}) [{tag}]")

    # Probe 2: Integrable
    print("Probe 2: Integrable (non-interacting sigma_z) ...")
    integ_result = probe_integrable(rng)
    results["probes"]["integrable"] = integ_result
    tag = "PASS" if integ_result["passed"] else "FAIL"
    print(f"  r_mean = {integ_result['r_mean']} (expected {R_POISSON}) [{tag}]")

    # Probe 3: Chaotic Heisenberg
    print("Probe 3: Chaotic random Heisenberg ...")
    chaos_result, evals, evecs, H = probe_chaotic_heisenberg(rng)
    results["probes"]["chaotic"] = chaos_result
    tag = "PASS" if chaos_result["passed"] else "FAIL"
    print(f"  r_mean = {chaos_result['r_mean']} (expected {R_WD_GUE}) [{tag}]")

    # Probe 4: ETH
    print("Probe 4: ETH check ...")
    eth_result = probe_eth(evals, evecs, H, rng)
    results["probes"]["eth"] = eth_result
    tag = "PASS" if eth_result["passed"] else "FAIL"
    print(f"  diagonal smooth: {eth_result['diagonal_eth']['smooth']}")
    print(f"  offdiag scaling: {eth_result['offdiagonal_eth']['scaling_ok']}")
    print(f"  [{tag}]")

    # Summary
    elapsed = time.time() - t0
    all_passed = all(
        results["probes"][k]["passed"] for k in results["probes"]
    )
    results["summary"] = {
        "all_passed": bool(all_passed),
        "elapsed_seconds": round(elapsed, 3),
        "probe_count": len(results["probes"]),
    }

    print(f"\n{'='*60}")
    print(f"ALL PASSED: {all_passed}  ({elapsed:.3f}s)")
    print(f"{'='*60}")

    # Write output
    out_dir = os.path.join(
        os.path.dirname(__file__), "a2_state", "sim_results"
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "quantum_chaos_lego_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {out_path}")

    return results


if __name__ == "__main__":
    main()
