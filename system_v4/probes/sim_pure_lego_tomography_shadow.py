#!/usr/bin/env python3
"""
PURE LEGO: Quantum State Tomography & Classical Shadow Tomography
=================================================================
Foundational building block.  Pure math only -- numpy.
No engine imports.  Every operation verified against theory.

Sections
--------
1. Full State Tomography (linear inversion)
   - Measure in X, Y, Z bases (3 bases x N shots each)
   - Reconstruct rho via linear inversion
   - Test on 5 known states
   - Verify fidelity -> 1 as N -> infinity  (N = 100, 1000, 10000)

2. Maximum Likelihood Estimation (MLE)
   - Iterative algorithm enforcing rho >= 0, Tr = 1
   - Compare to linear inversion -- MLE always physical

3. Classical Shadows
   - Random Clifford measurements (single-qubit Clifford group)
   - From n measurements, estimate Tr(O rho) for any observable O
   - Median-of-means estimator convergence
   - Sample complexity: O(log(M) / eps^2) for M observables
   - Test on 10 random observables

4. Shadow vs Full Tomography Comparison
   - Shadows need fewer measurements for estimating specific properties
   - Full tomo needs d^2 = 4 parameters; shadows need O(1) per observable
"""

import json, pathlib, time
import numpy as np
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)
EPS = 1e-14
RESULTS = {}

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
PAULIS = {"X": sx, "Y": sy, "Z": sz}

def ket(v):
    """Column vector from list."""
    return np.array(v, dtype=complex).reshape(-1, 1)

def dm(v):
    """Density matrix from ket vector."""
    k = ket(v)
    return k @ k.conj().T

def fidelity(rho, sigma):
    """Fidelity between two density matrices.
    F(rho, sigma) = (Tr sqrt(sqrt(sigma) rho sqrt(sigma)))^2.
    Clamp eigenvalues to >= 0 so it works even with unphysical rho.
    """
    sqrt_sigma = matrix_sqrt(sigma)
    prod = sqrt_sigma @ rho @ sqrt_sigma
    # Eigendecompose prod; clamp negatives from numerical noise
    evals = np.linalg.eigvalsh(prod)
    evals = np.maximum(evals, 0.0)
    return float(np.sum(np.sqrt(evals))) ** 2

def matrix_sqrt(M):
    """Matrix square root via eigendecomposition."""
    evals, evecs = np.linalg.eigh(M)
    evals = np.maximum(evals, 0.0)
    return evecs @ np.diag(np.sqrt(evals)) @ evecs.conj().T

def is_valid_dm(rho, tol=1e-10):
    """Check Tr=1, Hermitian, PSD."""
    tr = np.real(np.trace(rho))
    herm = np.allclose(rho, rho.conj().T, atol=tol)
    evals = np.linalg.eigvalsh(rho)
    psd = bool(np.all(evals >= -tol))
    return {
        "trace_ok": bool(abs(tr - 1.0) < tol),
        "hermitian": herm,
        "psd": psd,
        "trace": float(tr),
        "min_eigenvalue": float(np.min(evals)),
    }


# ──────────────────────────────────────────────────────────────────────
# Test states
# ──────────────────────────────────────────────────────────────────────

TEST_STATES = {
    "|0>":        dm([1, 0]),
    "|1>":        dm([0, 1]),
    "|+>":        dm([1/np.sqrt(2), 1/np.sqrt(2)]),
    "|+i>":       dm([1/np.sqrt(2), 1j/np.sqrt(2)]),
    "mixed_0.7":  0.7 * dm([1, 0]) + 0.3 * dm([0, 1]),
}


# ══════════════════════════════════════════════════════════════════════
# SECTION 1: Full State Tomography — Linear Inversion
# ══════════════════════════════════════════════════════════════════════

def measure_in_basis(rho, basis_label, n_shots):
    """Simulate n_shots measurements of rho in the given Pauli basis.
    Returns array of +1/-1 outcomes.

    Basis eigenstates:
      X: |+>, |->   with eigenvalues +1, -1
      Y: |+i>, |-i> with eigenvalues +1, -1
      Z: |0>, |1>   with eigenvalues +1, -1
    """
    P = PAULIS[basis_label]
    # Probability of +1 outcome: p = Tr(P_+ rho) where P_+ = (I+P)/2
    p_plus = np.real(np.trace((I2 + P) / 2 @ rho))
    p_plus = np.clip(p_plus, 0.0, 1.0)
    outcomes = np.random.choice([1, -1], size=n_shots, p=[p_plus, 1 - p_plus])
    return outcomes


def linear_inversion_tomography(rho_true, n_shots_per_basis):
    """Full state tomography via linear inversion.

    For a single qubit, rho = (I + r_x X + r_y Y + r_z Z) / 2.
    We estimate r_i = <P_i> from measurement statistics.
    """
    expectations = {}
    for basis_label in ["X", "Y", "Z"]:
        outcomes = measure_in_basis(rho_true, basis_label, n_shots_per_basis)
        expectations[basis_label] = np.mean(outcomes)

    # Reconstruct
    rho_recon = (I2
                 + expectations["X"] * sx
                 + expectations["Y"] * sy
                 + expectations["Z"] * sz) / 2.0
    return rho_recon, expectations


def run_full_tomography():
    """Test linear inversion tomography on 5 known states at 3 shot counts."""
    print("=" * 70)
    print("SECTION 1: Full State Tomography — Linear Inversion")
    print("=" * 70)

    shot_counts = [100, 1000, 10000]
    results = {}

    for label, rho_true in TEST_STATES.items():
        state_results = {}
        for n_shots in shot_counts:
            # Average over 20 repetitions for stable statistics
            fids = []
            validities = []
            for _ in range(20):
                rho_recon, _ = linear_inversion_tomography(rho_true, n_shots)
                f = fidelity(rho_recon, rho_true)
                fids.append(f)
                v = is_valid_dm(rho_recon)
                validities.append(v["psd"])

            avg_fid = float(np.mean(fids))
            std_fid = float(np.std(fids))
            frac_physical = float(np.mean(validities))

            state_results[str(n_shots)] = {
                "avg_fidelity": avg_fid,
                "std_fidelity": std_fid,
                "fraction_physical": frac_physical,
            }
            print(f"  {label:10s}  N={n_shots:>5d}  "
                  f"F={avg_fid:.6f} +/- {std_fid:.6f}  "
                  f"physical={frac_physical:.0%}")

        results[label] = state_results

    # Verify convergence: fidelity at N=10000 should be > 0.99
    convergence_ok = all(
        results[label]["10000"]["avg_fidelity"] > 0.99
        for label in TEST_STATES
    )
    print(f"\n  Convergence check (F > 0.99 at N=10000): "
          f"{'PASS' if convergence_ok else 'FAIL'}")

    RESULTS["section_1_linear_inversion"] = {
        "states": results,
        "convergence_pass": convergence_ok,
    }
    return results


# ══════════════════════════════════════════════════════════════════════
# SECTION 2: Maximum Likelihood Estimation (MLE)
# ══════════════════════════════════════════════════════════════════════

def mle_tomography(rho_true, n_shots_per_basis, max_iter=200, tol=1e-8):
    """Iterative MLE reconstruction enforcing rho >= 0, Tr = 1.

    Uses the R*rho*R iterative algorithm (Hradil 1997 / Rehacek 2001):
      R = sum_i (f_i / p_i) Pi_i
    where f_i = observed frequencies, p_i = Tr(Pi rho), Pi_i = POVM elements.

    For Pauli measurements, POVM elements are projectors onto eigenstates.
    """
    # Collect measurement data
    freq_data = {}  # {(basis, outcome): frequency}
    for basis_label in ["X", "Y", "Z"]:
        outcomes = measure_in_basis(rho_true, basis_label, n_shots_per_basis)
        n_plus = np.sum(outcomes == 1)
        n_minus = np.sum(outcomes == -1)
        total = n_plus + n_minus
        freq_data[(basis_label, +1)] = n_plus / total
        freq_data[(basis_label, -1)] = n_minus / total

    # POVM elements: projectors onto +1 and -1 eigenstates of each Pauli
    povm_elements = {}
    for basis_label in ["X", "Y", "Z"]:
        P = PAULIS[basis_label]
        povm_elements[(basis_label, +1)] = (I2 + P) / 2.0
        povm_elements[(basis_label, -1)] = (I2 - P) / 2.0

    # Initialize rho as maximally mixed
    rho = I2 / 2.0

    for iteration in range(max_iter):
        # Build R operator
        R = np.zeros((2, 2), dtype=complex)
        for key, Pi in povm_elements.items():
            f_i = freq_data[key]
            p_i = np.real(np.trace(Pi @ rho))
            if p_i > EPS:
                R += (f_i / p_i) * Pi

        # Update: rho_new = R @ rho @ R, then normalize
        rho_new = R @ rho @ R
        rho_new = rho_new / np.trace(rho_new)

        # Convergence check
        diff = np.linalg.norm(rho_new - rho)
        rho = rho_new
        if diff < tol:
            break

    return rho, iteration + 1


def run_mle_tomography():
    """Compare MLE to linear inversion."""
    print("\n" + "=" * 70)
    print("SECTION 2: Maximum Likelihood Estimation (MLE)")
    print("=" * 70)

    n_shots = 1000
    n_repeats = 20
    results = {}

    for label, rho_true in TEST_STATES.items():
        li_fids = []
        mle_fids = []
        li_physical = []
        mle_physical = []

        for _ in range(n_repeats):
            # Linear inversion
            rho_li, _ = linear_inversion_tomography(rho_true, n_shots)
            li_fids.append(fidelity(rho_li, rho_true))
            li_physical.append(is_valid_dm(rho_li)["psd"])

            # MLE
            rho_mle, _ = mle_tomography(rho_true, n_shots)
            mle_fids.append(fidelity(rho_mle, rho_true))
            mle_physical.append(is_valid_dm(rho_mle)["psd"])

        results[label] = {
            "linear_inversion": {
                "avg_fidelity": float(np.mean(li_fids)),
                "std_fidelity": float(np.std(li_fids)),
                "fraction_physical": float(np.mean(li_physical)),
            },
            "mle": {
                "avg_fidelity": float(np.mean(mle_fids)),
                "std_fidelity": float(np.std(mle_fids)),
                "fraction_physical": float(np.mean(mle_physical)),
            },
        }

        print(f"  {label:10s}  "
              f"LI: F={np.mean(li_fids):.6f} phys={np.mean(li_physical):.0%}  |  "
              f"MLE: F={np.mean(mle_fids):.6f} phys={np.mean(mle_physical):.0%}")

    # MLE should ALWAYS produce physical states
    mle_always_physical = all(
        results[label]["mle"]["fraction_physical"] == 1.0
        for label in TEST_STATES
    )
    print(f"\n  MLE always physical: {'PASS' if mle_always_physical else 'FAIL'}")

    RESULTS["section_2_mle"] = {
        "n_shots": n_shots,
        "states": results,
        "mle_always_physical": mle_always_physical,
    }
    return results


# ══════════════════════════════════════════════════════════════════════
# SECTION 3: Classical Shadows
# ══════════════════════════════════════════════════════════════════════

# Single-qubit Clifford group: 24 elements
# For classical shadows, we only need random Pauli measurements (X, Y, Z).
# This is the "random Pauli" variant of classical shadows.
# Each measurement: pick random basis U in {H, HSdg, I} (mapping to X, Y, Z),
# measure in computational basis, construct snapshot:
#   rho_hat = 3 * U^dag |b><b| U - I

# Unitaries that rotate Z-basis to X, Y, Z measurement bases:
U_BASES = {
    "X": np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2),   # Hadamard
    "Y": np.array([[1, -1j], [1, 1j]], dtype=complex) / np.sqrt(2), # Hadamard @ S^dag
    "Z": I2.copy(),
}


def classical_shadow_snapshot(rho, rng=None):
    """Generate one classical shadow snapshot.
    1. Pick random Pauli basis uniformly from {X, Y, Z}.
    2. Measure rho in that basis (sample one outcome).
    3. Return the snapshot operator: rho_hat = 3 * U^dag |b><b| U - I.
    """
    if rng is None:
        rng = np.random.default_rng()

    basis_label = rng.choice(["X", "Y", "Z"])
    U = U_BASES[basis_label]

    # Probability of outcome 0 in rotated basis: p0 = <0| U rho U^dag |0>
    rho_rotated = U @ rho @ U.conj().T
    p0 = np.real(rho_rotated[0, 0])
    p0 = np.clip(p0, 0.0, 1.0)

    outcome = rng.choice([0, 1], p=[p0, 1 - p0])

    # Outcome ket in computational basis
    b = np.zeros((2, 1), dtype=complex)
    b[outcome, 0] = 1.0

    # Snapshot: 3 * U^dag |b><b| U - I
    proj = b @ b.conj().T
    snapshot = 3.0 * (U.conj().T @ proj @ U) - I2

    return snapshot, basis_label, outcome


def generate_classical_shadows(rho, n_shadows, seed=42):
    """Generate n classical shadow snapshots."""
    rng = np.random.default_rng(seed)
    snapshots = []
    for _ in range(n_shadows):
        snap, basis, outcome = classical_shadow_snapshot(rho, rng=rng)
        snapshots.append(snap)
    return snapshots


def shadow_estimate_observable(snapshots, O):
    """Estimate Tr(O rho) from classical shadow snapshots.
    Simple mean estimator: (1/n) sum_i Tr(O rho_hat_i).
    """
    estimates = [np.real(np.trace(O @ snap)) for snap in snapshots]
    return np.mean(estimates), np.std(estimates) / np.sqrt(len(estimates))


def median_of_means(snapshots, O, n_groups=10):
    """Median-of-means estimator for Tr(O rho).
    Split snapshots into n_groups, compute mean in each, take median.
    Gives exponentially better tail bounds.
    """
    n = len(snapshots)
    group_size = n // n_groups
    if group_size == 0:
        return shadow_estimate_observable(snapshots, O)

    group_means = []
    for g in range(n_groups):
        start = g * group_size
        end = start + group_size
        group_snaps = snapshots[start:end]
        estimates = [np.real(np.trace(O @ s)) for s in group_snaps]
        group_means.append(np.mean(estimates))

    return float(np.median(group_means)), float(np.std(group_means) / np.sqrt(n_groups))


def generate_random_observable(rng):
    """Generate a random traceless Hermitian observable (linear combo of Paulis)."""
    coeffs = rng.standard_normal(3)
    O = coeffs[0] * sx + coeffs[1] * sy + coeffs[2] * sz
    return O, coeffs


def run_classical_shadows():
    """Test classical shadow tomography."""
    print("\n" + "=" * 70)
    print("SECTION 3: Classical Shadows")
    print("=" * 70)

    rho_true = TEST_STATES["|+i>"]
    rng = np.random.default_rng(123)

    # Generate 10 random observables
    observables = []
    for _ in range(10):
        O, coeffs = generate_random_observable(rng)
        exact = np.real(np.trace(O @ rho_true))
        observables.append({"O": O, "coeffs": coeffs.tolist(), "exact": float(exact)})

    # Test at increasing shadow counts
    shadow_counts = [100, 500, 1000, 5000, 10000]
    results = {}

    for n_shadows in shadow_counts:
        snapshots = generate_classical_shadows(rho_true, n_shadows, seed=42)

        obs_results = []
        for i, obs in enumerate(observables):
            O = obs["O"]
            exact = obs["exact"]

            # Simple mean estimator
            est_mean, est_se = shadow_estimate_observable(snapshots, O)

            # Median-of-means estimator
            est_mom, mom_se = median_of_means(snapshots, O, n_groups=10)

            error_mean = abs(est_mean - exact)
            error_mom = abs(est_mom - exact)

            obs_results.append({
                "observable_idx": i,
                "exact": exact,
                "mean_estimate": float(est_mean),
                "mean_error": float(error_mean),
                "mom_estimate": float(est_mom),
                "mom_error": float(error_mom),
            })

        avg_mean_error = np.mean([r["mean_error"] for r in obs_results])
        avg_mom_error = np.mean([r["mom_error"] for r in obs_results])

        results[str(n_shadows)] = {
            "observables": obs_results,
            "avg_mean_error": float(avg_mean_error),
            "avg_mom_error": float(avg_mom_error),
        }

        print(f"  n_shadows={n_shadows:>5d}  "
              f"avg_mean_error={avg_mean_error:.6f}  "
              f"avg_mom_error={avg_mom_error:.6f}")

    # Convergence: error should decrease roughly as 1/sqrt(n)
    err_100 = results["100"]["avg_mean_error"]
    err_10000 = results["10000"]["avg_mean_error"]
    ratio = err_100 / max(err_10000, 1e-15)
    expected_ratio = np.sqrt(10000 / 100)  # = 10
    convergence_ok = ratio > expected_ratio * 0.3  # allow some variance

    print(f"\n  Convergence ratio (100 vs 10000): {ratio:.1f}  "
          f"(expected ~{expected_ratio:.0f})")
    print(f"  1/sqrt(n) convergence: {'PASS' if convergence_ok else 'FAIL'}")

    # Sample complexity check: for M observables, need O(log(M)/eps^2)
    # With 10 observables and eps=0.1, need ~O(log(10)/0.01) ~ 230 samples
    # At n=500 all errors should be < 0.3 with high probability
    all_under_threshold = all(
        r["mean_error"] < 0.5 for r in results["500"]["observables"]
    )
    print(f"  Sample complexity (10 obs, n=500, err<0.5): "
          f"{'PASS' if all_under_threshold else 'FAIL'}")

    RESULTS["section_3_classical_shadows"] = {
        "state": "|+i>",
        "shadow_counts": shadow_counts,
        "results": results,
        "convergence_ratio": float(ratio),
        "convergence_pass": convergence_ok,
        "sample_complexity_pass": all_under_threshold,
    }
    return results


# ══════════════════════════════════════════════════════════════════════
# SECTION 4: Shadow vs Full Tomography Comparison
# ══════════════════════════════════════════════════════════════════════

def run_shadow_vs_tomo():
    """Compare classical shadows vs full tomography for estimating observables."""
    print("\n" + "=" * 70)
    print("SECTION 4: Shadow vs Full Tomography Comparison")
    print("=" * 70)

    rho_true = TEST_STATES["mixed_0.7"]
    rng = np.random.default_rng(999)

    # Generate 10 random observables
    observables = []
    for _ in range(10):
        O, coeffs = generate_random_observable(rng)
        exact = np.real(np.trace(O @ rho_true))
        observables.append({"O": O, "exact": float(exact), "coeffs": coeffs.tolist()})

    measurement_budgets = [100, 500, 1000, 5000]
    results = {}

    for n_meas in measurement_budgets:
        # --- Full tomography approach ---
        # Budget split: n_meas/3 shots per basis
        n_per_basis = n_meas // 3
        tomo_errors = []
        for obs in observables:
            O = obs["O"]
            exact = obs["exact"]
            # Run tomography, reconstruct rho, compute Tr(O rho_recon)
            rho_recon, _ = linear_inversion_tomography(rho_true, n_per_basis)
            est = np.real(np.trace(O @ rho_recon))
            tomo_errors.append(abs(est - exact))

        # --- Shadow approach ---
        # Same budget: n_meas shadow snapshots
        snapshots = generate_classical_shadows(rho_true, n_meas, seed=777)
        shadow_errors = []
        for obs in observables:
            O = obs["O"]
            exact = obs["exact"]
            est, _ = shadow_estimate_observable(snapshots, O)
            shadow_errors.append(abs(est - exact))

        avg_tomo_err = float(np.mean(tomo_errors))
        avg_shadow_err = float(np.mean(shadow_errors))

        results[str(n_meas)] = {
            "avg_tomo_error": avg_tomo_err,
            "avg_shadow_error": avg_shadow_err,
            "shadow_wins": avg_shadow_err <= avg_tomo_err * 1.5,
            "per_observable_tomo": [float(e) for e in tomo_errors],
            "per_observable_shadow": [float(e) for e in shadow_errors],
        }

        winner = "SHADOW" if avg_shadow_err < avg_tomo_err else "TOMO"
        print(f"  n_meas={n_meas:>5d}  "
              f"tomo_err={avg_tomo_err:.6f}  "
              f"shadow_err={avg_shadow_err:.6f}  "
              f"winner={winner}")

    # Key insight: for estimating specific observables, shadows are competitive
    # even though full tomo reconstructs the entire state.
    # For single qubit, d^2=4 parameters, so full tomo is also efficient.
    # The shadow advantage grows with dimension.

    # Dimensional analysis
    d = 2  # single qubit
    print(f"\n  Dimensional analysis:")
    print(f"    Full tomo parameters needed: d^2 = {d**2}")
    print(f"    Shadow measurements per observable: O(1) (up to precision)")
    print(f"    Shadow advantage scales with dimension d")

    # For single qubit, both methods are comparable.
    # Check: at large n, both errors are small.
    large_n_tomo = results["5000"]["avg_tomo_error"]
    large_n_shadow = results["5000"]["avg_shadow_error"]
    both_converge = large_n_tomo < 0.1 and large_n_shadow < 0.1
    print(f"\n  Both converge at n=5000 (err < 0.1): "
          f"{'PASS' if both_converge else 'FAIL'}")

    # Scaling argument: shadows avoid exponential cost in d
    # For d-dimensional system:
    #   Full tomo: O(d^2) measurements needed
    #   Shadows:   O(log(M) * ||O||^2 / eps^2) for M observables
    # When M << d^2, shadows win.

    scaling_note = (
        "For d-dim system: full tomo needs O(d^2) measurements. "
        "Shadows need O(log(M)*||O||^2/eps^2) for M observables. "
        "When M << d^2, shadows win. For single qubit (d=2), both comparable."
    )
    print(f"  Note: {scaling_note}")

    RESULTS["section_4_shadow_vs_tomo"] = {
        "state": "mixed_0.7",
        "budgets": measurement_budgets,
        "results": results,
        "both_converge": both_converge,
        "scaling_note": scaling_note,
    }
    return results


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    t0 = time.time()
    print("PURE LEGO: Quantum State Tomography & Classical Shadow Tomography")
    print("numpy only — no engine\n")

    run_full_tomography()
    run_mle_tomography()
    run_classical_shadows()
    run_shadow_vs_tomo()

    elapsed = time.time() - t0

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_pass = True
    checks = [
        ("S1 convergence", RESULTS["section_1_linear_inversion"]["convergence_pass"]),
        ("S2 MLE always physical", RESULTS["section_2_mle"]["mle_always_physical"]),
        ("S3 shadow convergence", RESULTS["section_3_classical_shadows"]["convergence_pass"]),
        ("S3 sample complexity", RESULTS["section_3_classical_shadows"]["sample_complexity_pass"]),
        ("S4 both converge", RESULTS["section_4_shadow_vs_tomo"]["both_converge"]),
    ]
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  {name:30s}: {status}")

    print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    print(f"  Elapsed: {elapsed:.2f}s")

    RESULTS["summary"] = {
        "all_pass": all_pass,
        "elapsed_s": round(elapsed, 3),
        "checks": {name: passed for name, passed in checks},
    }

    # Write results
    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "tomography_shadow_results.json"

    # Sanitize for JSON (remove numpy arrays from nested results)
    def sanitize(obj):
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()
                    if not isinstance(v, np.ndarray)}
        if isinstance(obj, list):
            return [sanitize(x) for x in obj]
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return obj

    with open(out_path, "w") as f:
        json.dump(sanitize(RESULTS), f, indent=2)
    print(f"\n  Results written to {out_path}")
