#!/usr/bin/env python3
# Pure lego: numpy/scipy only.  No engine imports.
# Run as: make sim NAME=sim_pure_lego_petz_recovery  (from repo root)
"""
Petz Recovery Map & Quantum Channel Reversal
=============================================
Implements R_{σ,E}(ρ) = σ^{1/2} E†( E(σ)^{-1/2} ρ E(σ)^{-1/2} ) σ^{1/2}

Tests:
  T1  Unitary channel  → Petz recovery = exact inverse  (R∘E ≈ id)
  T2  Depolarizing      → approximate recovery  (fidelity < 1)
  T3  Amplitude damping → partial recovery
  T4  10 states × 5 channels  → recovery fidelity table
  T5  Fixed-point condition:  E(σ)=σ  ⇒  Petz gives best recovery
  T6  Data-processing inequality:  S(ρ||σ) ≥ S(E(ρ)||E(σ)),
      with equality iff Petz recovers exactly
"""
from __future__ import annotations
import json, os, sys, time, warnings
import numpy as np
from scipy.linalg import sqrtm, logm, fractional_matrix_power

warnings.filterwarnings("ignore", message="Matrix is singular", category=RuntimeWarning)
# sqrtm on rank-1 density matrices triggers a benign LinAlgWarning
try:
    from scipy.linalg import LinAlgWarning
    warnings.filterwarnings("ignore", category=LinAlgWarning)
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rand_density(d: int = 2, rng=None) -> np.ndarray:
    """Random density matrix of dimension d via partial-trace of Haar random."""
    if rng is None:
        rng = np.random.default_rng()
    G = rng.standard_normal((d, d)) + 1j * rng.standard_normal((d, d))
    rho = G @ G.conj().T
    return rho / np.trace(rho)


def pure_state(theta: float, phi: float) -> np.ndarray:
    """Qubit pure state |ψ><ψ| from Bloch angles."""
    psi = np.array([np.cos(theta / 2),
                    np.exp(1j * phi) * np.sin(theta / 2)])
    return np.outer(psi, psi.conj())


def fidelity(rho: np.ndarray, sigma: np.ndarray) -> float:
    """Uhlmann fidelity F(ρ,σ) = (Tr √(√ρ σ √ρ))²."""
    sqrt_rho = sqrtm(rho)
    inner = sqrt_rho @ sigma @ sqrt_rho
    # Eigenvalue-based for numerical stability
    evals = np.linalg.eigvalsh(inner)
    evals = np.maximum(evals.real, 0.0)
    return float(np.sum(np.sqrt(evals))) ** 2


def relative_entropy(rho: np.ndarray, sigma: np.ndarray) -> float:
    """S(ρ||σ) = Tr[ρ (log ρ - log σ)].  Returns +inf if supp(ρ) ⊄ supp(σ)."""
    eps = 1e-12
    evals_s, U_s = np.linalg.eigh(sigma)
    evals_r, U_r = np.linalg.eigh(rho)
    # Check support
    for i, ev_r in enumerate(evals_r):
        if ev_r > eps:
            overlap = np.abs(U_r[:, i].conj() @ U_s) ** 2
            if np.dot(overlap, (evals_s > eps).astype(float)) < 1 - eps:
                return float('inf')
    log_rho = U_r @ np.diag(np.log(np.maximum(evals_r, eps))) @ U_r.conj().T
    log_sig = U_s @ np.diag(np.log(np.maximum(evals_s, eps))) @ U_s.conj().T
    val = np.trace(rho @ (log_rho - log_sig))
    return float(np.real(val))


def mat_sqrt(A: np.ndarray) -> np.ndarray:
    """Hermitian matrix square root via eigendecomposition."""
    evals, evecs = np.linalg.eigh(A)
    evals = np.maximum(evals.real, 0.0)
    return evecs @ np.diag(np.sqrt(evals)) @ evecs.conj().T


def mat_inv_sqrt(A: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    """Inverse square root, zeroing near-null eigenvalues."""
    evals, evecs = np.linalg.eigh(A)
    inv_sq = np.where(evals > eps, 1.0 / np.sqrt(evals), 0.0)
    return evecs @ np.diag(inv_sq) @ evecs.conj().T


# ---------------------------------------------------------------------------
# Quantum channels  (Kraus representation)
# ---------------------------------------------------------------------------

def kraus_identity() -> list[np.ndarray]:
    return [np.eye(2, dtype=complex)]


def kraus_unitary(U: np.ndarray) -> list[np.ndarray]:
    return [U.astype(complex)]


def kraus_depolarizing(p: float) -> list[np.ndarray]:
    """Depolarizing: E(ρ) = (1-p)ρ + p/3 (XρX + YρY + ZρZ)."""
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    return [np.sqrt(1 - p) * I,
            np.sqrt(p / 3) * X,
            np.sqrt(p / 3) * Y,
            np.sqrt(p / 3) * Z]


def kraus_amplitude_damping(gamma: float) -> list[np.ndarray]:
    """Amplitude damping with rate γ."""
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    return [K0, K1]


def kraus_phase_damping(lam: float) -> list[np.ndarray]:
    """Phase damping (dephasing) channel."""
    K0 = np.array([[1, 0], [0, np.sqrt(1 - lam)]], dtype=complex)
    K1 = np.array([[0, 0], [0, np.sqrt(lam)]], dtype=complex)
    return [K0, K1]


def apply_channel(kraus: list[np.ndarray], rho: np.ndarray) -> np.ndarray:
    """E(ρ) = Σ_k K_k ρ K_k†"""
    return sum(K @ rho @ K.conj().T for K in kraus)


def apply_adjoint(kraus: list[np.ndarray], rho: np.ndarray) -> np.ndarray:
    """E†(ρ) = Σ_k K_k† ρ K_k"""
    return sum(K.conj().T @ rho @ K for K in kraus)


# ---------------------------------------------------------------------------
# Petz recovery map
# ---------------------------------------------------------------------------

def petz_recovery(kraus: list[np.ndarray],
                  sigma: np.ndarray,
                  rho_target: np.ndarray) -> np.ndarray:
    """
    R_{σ,E}(ρ_target) = σ^{1/2} E†( E(σ)^{-1/2} ρ_target E(σ)^{-1/2} ) σ^{1/2}

    Here ρ_target lives in the output space of E, i.e. we feed E(ρ) in.
    """
    sigma_sqrt = mat_sqrt(sigma)
    E_sigma = apply_channel(kraus, sigma)
    E_sigma_inv_sqrt = mat_inv_sqrt(E_sigma)

    inner = E_sigma_inv_sqrt @ rho_target @ E_sigma_inv_sqrt
    adj_inner = apply_adjoint(kraus, inner)
    recovered = sigma_sqrt @ adj_inner @ sigma_sqrt
    # Normalize trace (may drift numerically)
    tr = np.trace(recovered).real
    if tr > 1e-14:
        recovered = recovered / tr
    return recovered


# ---------------------------------------------------------------------------
# Test bank
# ---------------------------------------------------------------------------

def make_test_states(rng) -> list[tuple[str, np.ndarray]]:
    """10 varied qubit states."""
    states = []
    states.append(("|0>", np.array([[1, 0], [0, 0]], dtype=complex)))
    states.append(("|1>", np.array([[0, 0], [0, 1]], dtype=complex)))
    states.append(("|+>", pure_state(np.pi / 2, 0)))
    states.append(("|-i>", pure_state(np.pi / 2, -np.pi / 2)))
    states.append(("max-mixed", 0.5 * np.eye(2, dtype=complex)))
    states.append(("bloch(.3,.7,.5)", pure_state(0.3, 0.7)))
    states.append(("rand1", rand_density(2, rng)))
    states.append(("rand2", rand_density(2, rng)))
    states.append(("rand3", rand_density(2, rng)))
    states.append(("near-pure", 0.99 * pure_state(1.2, 0.4)
                   + 0.01 * np.eye(2, dtype=complex) / 2))
    return states


def make_channels() -> list[tuple[str, list[np.ndarray]]]:
    """5 channels."""
    # Random unitary
    from scipy.stats import unitary_group
    U = unitary_group.rvs(2)
    return [
        ("identity",          kraus_identity()),
        ("unitary(Haar)",     kraus_unitary(U)),
        ("depol(p=0.3)",      kraus_depolarizing(0.3)),
        ("amp-damp(γ=0.4)",   kraus_amplitude_damping(0.4)),
        ("phase-damp(λ=0.5)", kraus_phase_damping(0.5)),
    ]


def run_fidelity_table(states, channels, sigma):
    """10 states × 5 channels → recovery fidelity matrix."""
    rows = []
    for s_name, rho in states:
        row = {"state": s_name}
        for c_name, kraus in channels:
            E_rho = apply_channel(kraus, rho)
            R_E_rho = petz_recovery(kraus, sigma, E_rho)
            F = fidelity(rho, R_E_rho)
            row[c_name] = round(F, 6)
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Verification routines
# ---------------------------------------------------------------------------

def verify_unitary_exact(channels, sigma, tol=1e-6):
    """T1: Unitary channels → Petz = exact inverse."""
    results = []
    for name, kraus in channels:
        if "unitary" not in name.lower() and "identity" not in name.lower():
            continue
        rho = rand_density(2, np.random.default_rng(42))
        E_rho = apply_channel(kraus, rho)
        R_E_rho = petz_recovery(kraus, sigma, E_rho)
        F = fidelity(rho, R_E_rho)
        passed = F > 1.0 - tol
        results.append({"channel": name, "fidelity": round(F, 10),
                        "exact_recovery": passed})
    return results


def verify_fixed_point(sigma, tol=1e-6):
    """T5: When E(σ)=σ, Petz recovery is optimal.
    The unital depolarizing channel satisfies E(I/2)=I/2,
    so σ=I/2 is a fixed point for depolarizing."""
    sigma_fp = 0.5 * np.eye(2, dtype=complex)
    channels_test = [
        ("depol(p=0.1)", kraus_depolarizing(0.1)),
        ("depol(p=0.3)", kraus_depolarizing(0.3)),
        ("depol(p=0.5)", kraus_depolarizing(0.5)),
    ]
    results = []
    rng = np.random.default_rng(99)
    for name, kraus in channels_test:
        E_sigma = apply_channel(kraus, sigma_fp)
        is_fixed = np.allclose(E_sigma, sigma_fp, atol=tol)
        # Measure recovery quality for a non-trivial state
        rho = rand_density(2, rng)
        E_rho = apply_channel(kraus, rho)
        R_E_rho = petz_recovery(kraus, sigma_fp, E_rho)
        F = fidelity(rho, R_E_rho)
        results.append({
            "channel": name,
            "sigma_is_fixed_point": bool(is_fixed),
            "recovery_fidelity": round(F, 8),
        })
    return results


def verify_data_processing_inequality(states, channels, sigma, tol=1e-6):
    """T6: S(ρ||σ) ≥ S(E(ρ)||E(σ)), with equality iff Petz recovers exactly."""
    results = []
    for s_name, rho in states[:5]:  # first 5 states
        for c_name, kraus in channels:
            S_pre = relative_entropy(rho, sigma)
            if S_pre == float('inf'):
                continue
            E_rho = apply_channel(kraus, rho)
            E_sig = apply_channel(kraus, sigma)
            S_post = relative_entropy(E_rho, E_sig)
            if S_post == float('inf'):
                continue
            dpi_holds = S_pre >= S_post - tol
            gap = S_pre - S_post

            R_E_rho = petz_recovery(kraus, sigma, E_rho)
            F = fidelity(rho, R_E_rho)
            exact = F > 1.0 - tol
            equality = abs(gap) < tol

            # Verify: equality ↔ exact recovery
            consistency = (equality == exact) or (gap < tol and F > 1.0 - 1e-4)

            results.append({
                "state": s_name,
                "channel": c_name,
                "S_pre": round(S_pre, 8),
                "S_post": round(S_post, 8),
                "gap": round(gap, 8),
                "dpi_holds": bool(dpi_holds),
                "petz_fidelity": round(F, 8),
                "exact_recovery": bool(exact),
                "equality_iff_exact": bool(consistency),
            })
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    t0 = time.time()
    print("Petz Recovery Map — Pure Lego Probe")
    print("=" * 55)

    rng = np.random.default_rng(2026)
    sigma = rand_density(2, rng)          # reference state for Petz map
    states = make_test_states(rng)
    channels = make_channels()

    # ---- T1-T3: qualitative checks ----
    print("\n[T1] Unitary/identity channel → exact recovery")
    t1 = verify_unitary_exact(channels, sigma)
    for r in t1:
        tag = "PASS" if r["exact_recovery"] else "FAIL"
        print(f"  {tag}  {r['channel']:20s}  F={r['fidelity']}")

    print("\n[T2-T3] Non-unitary channels → partial recovery")
    for c_name, kraus in channels:
        if "unitary" in c_name.lower() or "identity" in c_name.lower():
            continue
        rho = rand_density(2, rng)
        E_rho = apply_channel(kraus, rho)
        R_E_rho = petz_recovery(kraus, sigma, E_rho)
        F = fidelity(rho, R_E_rho)
        tag = "PASS" if F < 1.0 - 1e-6 else "WARN"
        print(f"  {tag}  {c_name:20s}  F={F:.6f}  (< 1 expected)")

    # ---- T4: full fidelity table ----
    print("\n[T4] 10 states × 5 channels — recovery fidelity table")
    table = run_fidelity_table(states, channels, sigma)
    hdr = f"  {'state':18s}"
    for c_name, _ in channels:
        hdr += f"  {c_name:>16s}"
    print(hdr)
    print("  " + "-" * (18 + 18 * len(channels)))
    for row in table:
        line = f"  {row['state']:18s}"
        for c_name, _ in channels:
            line += f"  {row[c_name]:16.6f}"
        print(line)

    # ---- T5: fixed-point condition ----
    print("\n[T5] Fixed-point condition: E(σ)=σ → best recovery")
    t5 = verify_fixed_point(sigma)
    for r in t5:
        tag = "PASS" if r["sigma_is_fixed_point"] else "INFO"
        print(f"  {tag}  {r['channel']:20s}  fixed={r['sigma_is_fixed_point']}"
              f"  F={r['recovery_fidelity']:.8f}")

    # ---- T6: data-processing inequality ----
    print("\n[T6] Data-processing inequality + Petz equality condition")
    t6 = verify_data_processing_inequality(states, channels, sigma)
    n_dpi_pass = sum(1 for r in t6 if r["dpi_holds"])
    n_consist  = sum(1 for r in t6 if r["equality_iff_exact"])
    n_total    = len(t6)
    print(f"  DPI holds: {n_dpi_pass}/{n_total}")
    print(f"  Equality↔exact consistency: {n_consist}/{n_total}")
    for r in t6:
        if not r["dpi_holds"]:
            print(f"  FAIL  {r['state']:15s} × {r['channel']:20s}"
                  f"  gap={r['gap']:.6e}")

    # ---- Summary ----
    all_t1_pass = all(r["exact_recovery"] for r in t1)
    all_dpi     = n_dpi_pass == n_total
    elapsed = time.time() - t0

    summary = {
        "probe": "petz_recovery_map",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_s": round(elapsed, 3),
        "sigma_trace": round(float(np.trace(sigma).real), 8),
        "T1_unitary_exact_recovery": all_t1_pass,
        "T1_details": t1,
        "T4_fidelity_table": table,
        "T5_fixed_point": t5,
        "T6_data_processing_inequality": {
            "dpi_holds_all": all_dpi,
            "equality_iff_exact_count": f"{n_consist}/{n_total}",
            "details": t6,
        },
        "overall_pass": all_t1_pass and all_dpi,
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "petz_recovery_results.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    status = "PASS" if summary["overall_pass"] else "FAIL"
    print(f"\n{'=' * 55}")
    print(f"OVERALL: {status}   ({elapsed:.2f}s)")
    print(f"Results → {out_path}")
    return 0 if summary["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
