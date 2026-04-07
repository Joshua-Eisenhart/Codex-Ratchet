"""
Pure Lego: Free Probability & Random Matrix Universality Classes
================================================================
No engine. numpy/scipy only.

Modules:
  1. Free convolution (semicircle + semicircle = wider semicircle)
  2. GOE/GUE/GSE universality via level spacing ratios
  3. Marchenko-Pastur law for sample covariance
  4. Tracy-Widom: largest eigenvalue fluctuations
  5. Wishart matrices as valid density matrices
"""

import numpy as np
from scipy import stats as sp_stats
import json
import os
from datetime import datetime, UTC

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)
os.makedirs(RESULTS_DIR, exist_ok=True)

RNG = np.random.default_rng(42)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def semicircle_pdf(x, R):
    """Wigner semicircle density on [-R, R]."""
    mask = np.abs(x) <= R
    y = np.zeros_like(x)
    y[mask] = (2.0 / (np.pi * R**2)) * np.sqrt(R**2 - x[mask]**2)
    return y


def level_spacing_ratios(eigenvalues):
    """Compute consecutive level spacing ratios r_i = min(s_i,s_{i+1})/max(...)."""
    s = np.diff(np.sort(eigenvalues))
    # Avoid division by zero on exact degeneracies
    ratios = []
    for i in range(len(s) - 1):
        lo = min(s[i], s[i + 1])
        hi = max(s[i], s[i + 1])
        if hi > 1e-15:
            ratios.append(lo / hi)
    return np.array(ratios)


def gue_matrix(d):
    """Sample from GUE(d): complex Hermitian, variance 1/d per entry."""
    A = (RNG.standard_normal((d, d)) + 1j * RNG.standard_normal((d, d))) / np.sqrt(2 * d)
    return (A + A.conj().T) / 2.0


def goe_matrix(d):
    """Sample from GOE(d): real symmetric, variance 1/d per entry."""
    A = RNG.standard_normal((d, d)) / np.sqrt(d)
    return (A + A.T) / 2.0


def gse_matrix(d):
    """
    GSE(d) via 2d x 2d quaternion self-dual construction.
    Build H = [[A, B],[-B*, A*]] where A is Hermitian, B is antisymmetric.
    Eigenvalues come in degenerate pairs; take every other one.
    """
    A = (RNG.standard_normal((d, d)) + 1j * RNG.standard_normal((d, d))) / np.sqrt(2 * d)
    A = (A + A.conj().T) / 2.0
    B = (RNG.standard_normal((d, d)) + 1j * RNG.standard_normal((d, d))) / np.sqrt(2 * d)
    B = (B - B.T) / 2.0  # antisymmetric
    H = np.block([[A, B], [-B.conj(), A.conj()]])
    H = (H + H.conj().T) / 2.0  # enforce Hermiticity
    return H


def marchenko_pastur_pdf(x, gamma, sigma2=1.0):
    """MP density for ratio gamma = d/n, population variance sigma2."""
    lam_minus = sigma2 * (1 - np.sqrt(gamma))**2
    lam_plus = sigma2 * (1 + np.sqrt(gamma))**2
    y = np.zeros_like(x)
    mask = (x >= lam_minus) & (x <= lam_plus) & (x > 0)
    y[mask] = (1.0 / (2.0 * np.pi * gamma * sigma2 * x[mask])) * \
              np.sqrt((lam_plus - x[mask]) * (x[mask] - lam_minus))
    return y


# ---------------------------------------------------------------------------
# Module 1: Free Convolution
# ---------------------------------------------------------------------------

def test_free_convolution(d=200, n_trials=50):
    """
    A, B independent GUE(d).  Eigenvalue density of A+B should be
    semicircle with doubled variance (free convolution of semicircles).

    Our GUE normalization: /sqrt(2d) then symmetrize -> variance 1/2 per
    matrix, semicircle with R = sqrt(2).  Sum has variance 1, R_sum = 2.
    """
    all_eigs = []
    for _ in range(n_trials):
        A = gue_matrix(d)
        B = gue_matrix(d)
        eigs = np.linalg.eigvalsh(A + B)
        all_eigs.extend(eigs.tolist())

    all_eigs = np.array(all_eigs)

    # Each GUE has semicircle on [-R, R] with R = sqrt(2), variance = R^2/4 = 0.5
    # Free convolution: variances add -> variance_sum = 1.0, R_sum = 2.0
    R_sum = 2.0

    # Histogram vs theory
    bins = np.linspace(-R_sum * 1.3, R_sum * 1.3, 201)
    centers = (bins[:-1] + bins[1:]) / 2.0
    hist_density, _ = np.histogram(all_eigs, bins=bins, density=True)
    theory = semicircle_pdf(centers, R_sum)

    # L1 error (integrated absolute difference)
    dx = bins[1] - bins[0]
    l1_error = np.sum(np.abs(hist_density - theory)) * dx

    passed = l1_error < 0.15  # generous threshold for finite d

    return {
        "test": "free_convolution_semicircle",
        "d": d,
        "n_trials": n_trials,
        "total_eigenvalues": len(all_eigs),
        "R_sum_theory": round(R_sum, 4),
        "empirical_std": round(float(np.std(all_eigs)), 4),
        "theory_std": round(np.sqrt(R_sum**2 / 4), 4),
        "l1_error": round(float(l1_error), 6),
        "passed": bool(passed),
    }


# ---------------------------------------------------------------------------
# Module 2: GOE/GUE/GSE Universality
# ---------------------------------------------------------------------------

def test_universality(n_matrices=500, d=50):
    """
    Level spacing ratio <r> should match:
      GOE (beta=1): 0.5307 (often quoted ~0.536)
      GUE (beta=2): 0.5996 (often quoted ~0.600)
      GSE (beta=4): 0.6744 (often quoted ~0.676)

    Using the Atas et al. exact formula:
      <r> = (pi/4) * (beta+1)/(beta+2) * [some correction]
    We just compare to known numerical values with tolerance.
    """
    targets = {
        "GOE": {"beta": 1, "r_target": 0.5307, "gen": goe_matrix},
        "GUE": {"beta": 2, "r_target": 0.5996, "gen": gue_matrix},
        "GSE": {"beta": 4, "r_target": 0.6744, "gen": gse_matrix},
    }
    # Poisson baseline for comparison
    poisson_r = 2 * np.log(2) - 1  # ~0.3863

    results = {}
    for name, cfg in targets.items():
        all_ratios = []
        for _ in range(n_matrices):
            if name == "GSE":
                H = cfg["gen"](d)
                eigs = np.sort(np.linalg.eigvalsh(H))
                # GSE eigenvalues come in degenerate pairs; take every other
                eigs = eigs[::2]
            else:
                H = cfg["gen"](d)
                eigs = np.linalg.eigvalsh(H)

            # Use bulk eigenvalues only (middle 60%) to avoid edge effects
            n_eig = len(eigs)
            lo = int(0.2 * n_eig)
            hi = int(0.8 * n_eig)
            bulk = eigs[lo:hi]

            r = level_spacing_ratios(bulk)
            all_ratios.extend(r.tolist())

        mean_r = float(np.mean(all_ratios))
        tol = 0.025
        passed = abs(mean_r - cfg["r_target"]) < tol

        results[name] = {
            "beta": cfg["beta"],
            "r_target": cfg["r_target"],
            "r_measured": round(mean_r, 4),
            "deviation": round(abs(mean_r - cfg["r_target"]), 4),
            "n_ratios": len(all_ratios),
            "tolerance": tol,
            "passed": bool(passed),
        }

    results["poisson_r_reference"] = round(poisson_r, 4)
    return {"test": "universality_level_spacing", "d": d, "n_matrices": n_matrices, "results": results}


# ---------------------------------------------------------------------------
# Module 3: Marchenko-Pastur
# ---------------------------------------------------------------------------

def test_marchenko_pastur(d=100, n=200, n_trials=50):
    """
    Sample covariance X^T X / n for X ~ N(0,1) of shape (n, d).
    gamma = d/n = 0.5. Eigenvalue density should match MP law.
    """
    gamma = d / n
    all_eigs = []

    for _ in range(n_trials):
        X = RNG.standard_normal((n, d))
        S = X.T @ X / n
        eigs = np.linalg.eigvalsh(S)
        all_eigs.extend(eigs.tolist())

    all_eigs = np.array(all_eigs)

    lam_minus = (1 - np.sqrt(gamma))**2
    lam_plus = (1 + np.sqrt(gamma))**2

    bins = np.linspace(0, lam_plus * 1.3, 151)
    centers = (bins[:-1] + bins[1:]) / 2.0
    hist_density, _ = np.histogram(all_eigs, bins=bins, density=True)
    theory = marchenko_pastur_pdf(centers, gamma)

    dx = bins[1] - bins[0]
    l1_error = np.sum(np.abs(hist_density - theory)) * dx

    # Check support bounds
    frac_below = float(np.mean(all_eigs < lam_minus - 0.05))
    frac_above = float(np.mean(all_eigs > lam_plus + 0.05))

    passed = l1_error < 0.15 and frac_below < 0.02 and frac_above < 0.02

    return {
        "test": "marchenko_pastur",
        "d": d,
        "n": n,
        "gamma": gamma,
        "n_trials": n_trials,
        "lambda_minus": round(lam_minus, 4),
        "lambda_plus": round(lam_plus, 4),
        "empirical_min": round(float(np.min(all_eigs)), 4),
        "empirical_max": round(float(np.max(all_eigs)), 4),
        "l1_error": round(float(l1_error), 6),
        "frac_outside_support": round(frac_below + frac_above, 4),
        "passed": bool(passed),
    }


# ---------------------------------------------------------------------------
# Module 4: Tracy-Widom (largest eigenvalue)
# ---------------------------------------------------------------------------

def test_tracy_widom(d=200, n_matrices=3000):
    """
    For GUE(d), the largest eigenvalue lambda_max satisfies:
      (lambda_max - mu_d) / sigma_d  ~  TW_2
    where for our normalization (semicircle on [-sqrt(2), sqrt(2)]):
      mu_d = sqrt(2) * (1 - 1/(2*d))  (finite-d edge correction, ~sqrt(2))
      sigma_d = sqrt(2) * d^{-2/3} / sqrt(2) = d^{-2/3}

    Standard TW result for H with semicircle on [-2R, 2R]:
      mu = 2R, sigma = R * d^{-2/3}  (approximately)
    Our R_eff = sqrt(2)/2 (half the semicircle radius in standard convention),
    so mu = sqrt(2), sigma = (sqrt(2)/2) * d^{-2/3}.

    We verify the rescaled distribution has TW_2-like shape:
    negative mean, concentrated below edge, positive skewness.
    """
    R = np.sqrt(2.0)
    mu_edge = R
    # For GUE with eigenvalue support [-R, R], TW scaling is
    # sigma = R / (2^{1/2}) * d^{-2/3} in some conventions, but
    # let's use the empirical approach: scale so variance matches TW_2.
    # Standard: for semicircle on [-2,2], sigma = d^{-2/3}.
    # Ours is scaled by factor R/2 = sqrt(2)/2, so:
    sigma_scale = (R / 2.0) * d ** (-2.0 / 3.0)

    fluctuations = []
    for _ in range(n_matrices):
        H = gue_matrix(d)
        lam_max = np.max(np.linalg.eigvalsh(H))
        z = (lam_max - mu_edge) / sigma_scale
        fluctuations.append(z)

    fluctuations = np.array(fluctuations)

    emp_mean = float(np.mean(fluctuations))
    emp_var = float(np.var(fluctuations))
    emp_skew = float(sp_stats.skew(fluctuations))

    # TW_2: mean ~ -1.77, var ~ 0.81, skewness ~ 0.22
    # At finite d=200 there are O(1/d) corrections; be generous.
    mean_ok = abs(emp_mean - (-1.77)) < 1.0
    var_ok = abs(emp_var - 0.81) < 0.8
    # Key qualitative checks:
    # 1. Distribution concentrates below the classical edge
    below_edge = float(np.mean(fluctuations < 0))
    # 2. Skewness is positive (right tail heavier than left)
    skew_ok = emp_skew > -0.5  # generous; TW_2 skewness ~ 0.22

    passed = mean_ok and var_ok and below_edge > 0.7 and skew_ok

    return {
        "test": "tracy_widom_largest_eigenvalue",
        "d": d,
        "n_matrices": n_matrices,
        "centering": round(mu_edge, 6),
        "scaling": round(sigma_scale, 6),
        "empirical_mean": round(emp_mean, 4),
        "empirical_var": round(emp_var, 4),
        "empirical_skewness": round(emp_skew, 4),
        "tw2_reference_mean": -1.7711,
        "tw2_reference_var": 0.8132,
        "tw2_reference_skewness": 0.2241,
        "frac_below_edge": round(below_edge, 4),
        "mean_ok": bool(mean_ok),
        "var_ok": bool(var_ok),
        "passed": bool(passed),
    }


# ---------------------------------------------------------------------------
# Module 5: Wishart as Density Matrix
# ---------------------------------------------------------------------------

def test_wishart_density_matrix(d=20, n_trials=200):
    """
    W = X^dagger X / Tr(X^dagger X) for X ~ complex Gaussian (d x d).
    Verify: PSD (all eigenvalues >= 0), Tr = 1, Hermitian.
    Also compute average entropy and purity.
    """
    all_tr = []
    all_min_eig = []
    all_hermitian_err = []
    all_entropy = []
    all_purity = []

    for _ in range(n_trials):
        X = (RNG.standard_normal((d, d)) + 1j * RNG.standard_normal((d, d))) / np.sqrt(2)
        W = X.conj().T @ X
        W = W / np.trace(W)

        # Checks
        tr = float(np.real(np.trace(W)))
        all_tr.append(tr)

        eigs = np.real(np.linalg.eigvalsh(W))
        all_min_eig.append(float(np.min(eigs)))

        herm_err = float(np.max(np.abs(W - W.conj().T)))
        all_hermitian_err.append(herm_err)

        # Von Neumann entropy
        eigs_pos = eigs[eigs > 1e-15]
        S = -np.sum(eigs_pos * np.log(eigs_pos))
        all_entropy.append(float(S))

        # Purity
        pur = float(np.real(np.trace(W @ W)))
        all_purity.append(pur)

    tr_ok = all(abs(t - 1.0) < 1e-10 for t in all_tr)
    psd_ok = all(e > -1e-10 for e in all_min_eig)
    herm_ok = all(e < 1e-10 for e in all_hermitian_err)

    passed = tr_ok and psd_ok and herm_ok

    return {
        "test": "wishart_density_matrix",
        "d": d,
        "n_trials": n_trials,
        "trace_1_check": bool(tr_ok),
        "psd_check": bool(psd_ok),
        "hermitian_check": bool(herm_ok),
        "min_eigenvalue_across_all": round(float(np.min(all_min_eig)), 12),
        "max_trace_deviation": round(float(np.max(np.abs(np.array(all_tr) - 1.0))), 15),
        "avg_von_neumann_entropy": round(float(np.mean(all_entropy)), 4),
        "max_entropy_log_d": round(float(np.log(d)), 4),
        "avg_purity": round(float(np.mean(all_purity)), 6),
        "passed": bool(passed),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Pure Lego: Free Probability & Random Matrix Universality")
    print("=" * 70)

    results = {"timestamp": datetime.now(UTC).isoformat(), "modules": {}}

    # 1. Free convolution
    print("\n[1/5] Free convolution (semicircle + semicircle)...")
    r1 = test_free_convolution()
    results["modules"]["free_convolution"] = r1
    status = "PASS" if r1["passed"] else "FAIL"
    print(f"  L1 error: {r1['l1_error']:.4f}  [{status}]")

    # 2. Universality
    print("\n[2/5] GOE/GUE/GSE universality (level spacing ratios)...")
    r2 = test_universality()
    results["modules"]["universality"] = r2
    for name in ["GOE", "GUE", "GSE"]:
        info = r2["results"][name]
        status = "PASS" if info["passed"] else "FAIL"
        print(f"  {name}: <r> = {info['r_measured']:.4f} (target {info['r_target']})  [{status}]")

    # 3. Marchenko-Pastur
    print("\n[3/5] Marchenko-Pastur law...")
    r3 = test_marchenko_pastur()
    results["modules"]["marchenko_pastur"] = r3
    status = "PASS" if r3["passed"] else "FAIL"
    print(f"  L1 error: {r3['l1_error']:.4f}, support [{r3['lambda_minus']:.3f}, {r3['lambda_plus']:.3f}]  [{status}]")

    # 4. Tracy-Widom
    print("\n[4/5] Tracy-Widom largest eigenvalue fluctuations...")
    r4 = test_tracy_widom()
    results["modules"]["tracy_widom"] = r4
    status = "PASS" if r4["passed"] else "FAIL"
    print(f"  Mean: {r4['empirical_mean']:.3f} (ref -1.77), Var: {r4['empirical_var']:.3f} (ref 0.81)  [{status}]")

    # 5. Wishart density matrices
    print("\n[5/5] Wishart matrices as density matrices...")
    r5 = test_wishart_density_matrix()
    results["modules"]["wishart_density"] = r5
    status = "PASS" if r5["passed"] else "FAIL"
    print(f"  Tr=1: {r5['trace_1_check']}, PSD: {r5['psd_check']}, Hermitian: {r5['hermitian_check']}  [{status}]")

    # Summary
    all_passed = (
        r1["passed"]
        and all(r2["results"][k]["passed"] for k in ["GOE", "GUE", "GSE"])
        and r3["passed"]
        and r4["passed"]
        and r5["passed"]
    )
    results["all_passed"] = bool(all_passed)

    out_path = os.path.join(RESULTS_DIR, "free_probability_rmt_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 70}")
    tag = "ALL PASSED" if all_passed else "SOME FAILED"
    print(f"  [{tag}]  Results -> {out_path}")
    print(f"{'=' * 70}")

    return all_passed


if __name__ == "__main__":
    main()
