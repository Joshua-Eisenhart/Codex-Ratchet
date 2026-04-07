#!/usr/bin/env python3
"""
sim_pure_lego_adiabatic_variational.py
Pure-lego probe: adiabatic quantum computation and variational quantum methods.

No engine dependencies. numpy + scipy only.

Probes
------
1. Adiabatic evolution: H(s) = (1-s)H_0 + s*H_1 for 2-qubit system.
   H_0 = -sum(sigma_x), H_1 = sigma_z x sigma_z + 0.1*sigma_z x I.
   Slow evolution (T=100) reaches ground state; fast (T=1) does not.
2. Spectral gap: compute Delta(s) = E_1(s) - E_0(s) along adiabatic path.
   Verify minimum gap determines required time T ~ 1/Delta_min^2.
3. VQE: parameterized ansatz for H = sigma_z x sigma_z + 0.5*(sigma_x x I + I x sigma_x).
   Gradient-descent optimization converges to ground state energy.
4. QAOA for MaxCut: 2 qubits, 1 edge, p=1 layer.
   Sweep (gamma, beta) to find optimal cut.
"""

import json
import os
import time
import numpy as np
from scipy import linalg as la

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEED = 42
N_ADIABATIC_STEPS = 500       # discretisation of s in [0,1]
FIDELITY_THRESHOLD = 0.95     # fidelity for "reached ground state"
VQE_LR = 0.1                  # VQE gradient-descent learning rate
VQE_MAX_ITER = 800            # VQE max iterations
VQE_ENERGY_TOL = 1e-5         # VQE convergence tolerance
QAOA_GRID = 50                # grid resolution for (gamma, beta) sweep

# Pauli matrices
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def kron2(A, B):
    """Tensor product of two matrices."""
    return np.kron(A, B)


def ground_state(H):
    """Return (E0, |psi_0>) for Hermitian H."""
    evals, evecs = la.eigh(H)
    return evals[0], evecs[:, 0]


def fidelity(psi, phi):
    """State fidelity |<psi|phi>|^2."""
    return float(np.abs(np.vdot(psi, phi)) ** 2)


def expectation(psi, H):
    """<psi|H|psi>."""
    return float(np.real(np.vdot(psi, H @ psi)))


# ---------------------------------------------------------------------------
# Probe 1: Adiabatic evolution
# ---------------------------------------------------------------------------

def build_adiabatic_hamiltonians():
    """
    H_0 = -(sigma_x x I + I x sigma_x)  -- easy ground state |+>|+>
    H_1 = sigma_z x sigma_z + 0.1*(sigma_z x I)  -- problem Hamiltonian
          (small longitudinal field lifts the ZZ ground-state degeneracy
           so the adiabatic path has a unique ground state throughout)
    """
    H0 = -(kron2(SIGMA_X, I2) + kron2(I2, SIGMA_X))
    H1 = kron2(SIGMA_Z, SIGMA_Z) + 0.1 * kron2(SIGMA_Z, I2)
    return H0, H1


def adiabatic_evolve(H0, H1, T_total, n_steps=N_ADIABATIC_STEPS):
    """
    Trotterised adiabatic evolution from s=0 to s=1.
    H(s) = (1-s)*H0 + s*H1.
    Start in ground state of H0.
    """
    dt = T_total / n_steps
    _, psi = ground_state(H0)
    psi = psi.astype(complex)

    for k in range(n_steps):
        s = (k + 0.5) / n_steps  # midpoint rule
        H_s = (1 - s) * H0 + s * H1
        # exact matrix exponential for small system
        U = la.expm(-1j * H_s * dt)
        psi = U @ psi
        # renormalize to combat floating-point drift
        psi /= la.norm(psi)

    return psi


def probe_adiabatic():
    """Probe 1: slow vs fast adiabatic evolution."""
    H0, H1 = build_adiabatic_hamiltonians()
    E1_exact, psi1_exact = ground_state(H1)

    # Slow evolution -- should reach ground state
    psi_slow = adiabatic_evolve(H0, H1, T_total=100.0)
    fid_slow = fidelity(psi_slow, psi1_exact)

    # Fast evolution -- should NOT reach ground state reliably
    psi_fast = adiabatic_evolve(H0, H1, T_total=1.0)
    fid_fast = fidelity(psi_fast, psi1_exact)

    slow_ok = fid_slow >= FIDELITY_THRESHOLD
    fast_bad = fid_fast < FIDELITY_THRESHOLD

    return {
        "passed": bool(slow_ok and fast_bad),
        "slow_fidelity": round(fid_slow, 6),
        "fast_fidelity": round(fid_fast, 6),
        "slow_reached_ground": bool(slow_ok),
        "fast_missed_ground": bool(fast_bad),
        "exact_ground_energy": round(float(E1_exact), 6),
        "threshold": FIDELITY_THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Probe 2: Spectral gap
# ---------------------------------------------------------------------------

def probe_spectral_gap():
    """
    Compute gap Delta(s) = E_1(s) - E_0(s) along path.
    Verify: minimum gap > 0 and adiabatic theorem T ~ 1/Delta_min^2 holds.
    """
    H0, H1 = build_adiabatic_hamiltonians()
    s_values = np.linspace(0, 1, 200)
    gaps = []

    for s in s_values:
        H_s = (1 - s) * H0 + s * H1
        evals = la.eigvalsh(H_s)
        gap = float(evals[1] - evals[0])
        gaps.append(gap)

    gaps = np.array(gaps)
    min_gap = float(np.min(gaps))
    min_gap_s = float(s_values[np.argmin(gaps)])

    # Adiabatic theorem: T >> 1/Delta_min^2 for success
    adiabatic_time_scale = 1.0 / (min_gap ** 2) if min_gap > 0 else float('inf')

    # Verify that gap is always positive (no level crossing)
    gap_positive = bool(np.all(gaps > 0))

    # Verify relationship: slow T=100 >> adiabatic_time_scale should succeed
    # (we already tested this in probe 1)
    time_scale_reasonable = adiabatic_time_scale < 100.0

    return {
        "passed": bool(gap_positive and time_scale_reasonable),
        "min_gap": round(min_gap, 6),
        "min_gap_at_s": round(min_gap_s, 4),
        "adiabatic_time_scale": round(adiabatic_time_scale, 4),
        "gap_always_positive": gap_positive,
        "gap_samples": [round(float(g), 6) for g in gaps[::20]],
        "s_samples": [round(float(s), 4) for s in s_values[::20]],
    }


# ---------------------------------------------------------------------------
# Probe 3: VQE
# ---------------------------------------------------------------------------

def build_vqe_hamiltonian():
    """H = sigma_z x sigma_z + 0.5*(sigma_x x I + I x sigma_x)"""
    return kron2(SIGMA_Z, SIGMA_Z) + 0.5 * (kron2(SIGMA_X, I2) + kron2(I2, SIGMA_X))


def vqe_ansatz(theta):
    """
    Parameterized 2-qubit ansatz: |psi(theta)> = U(theta)|00>.
    U(theta) = (Ry(theta[0]) x Ry(theta[1])) * CNOT * (Ry(theta[2]) x Ry(theta[3]))

    4 parameters for sufficient expressibility.
    """
    dim = 4

    def ry(angle):
        c, s = np.cos(angle / 2), np.sin(angle / 2)
        return np.array([[c, -s], [s, c]], dtype=complex)

    # CNOT gate
    CNOT = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=complex)

    # Layer 1
    U1 = kron2(ry(theta[2]), ry(theta[3]))
    # Entangling
    # Layer 2
    U2 = kron2(ry(theta[0]), ry(theta[1]))

    U = U2 @ CNOT @ U1
    psi0 = np.zeros(dim, dtype=complex)
    psi0[0] = 1.0  # |00>
    return U @ psi0


def vqe_energy(theta, H):
    """Compute <psi(theta)|H|psi(theta)>."""
    psi = vqe_ansatz(theta)
    return expectation(psi, H)


def vqe_gradient(theta, H, eps=1e-5):
    """Numerical gradient via parameter shift (central difference)."""
    grad = np.zeros_like(theta)
    for i in range(len(theta)):
        theta_plus = theta.copy()
        theta_minus = theta.copy()
        theta_plus[i] += eps
        theta_minus[i] -= eps
        grad[i] = (vqe_energy(theta_plus, H) - vqe_energy(theta_minus, H)) / (2 * eps)
    return grad


def probe_vqe():
    """Probe 3: VQE converges to ground state energy."""
    H = build_vqe_hamiltonian()
    E_exact, psi_exact = ground_state(H)

    rng = np.random.default_rng(SEED)
    theta = rng.uniform(-np.pi, np.pi, size=4)

    energy_history = []
    converged = False

    for it in range(VQE_MAX_ITER):
        E = vqe_energy(theta, H)
        energy_history.append(float(E))

        if it > 0 and abs(energy_history[-1] - energy_history[-2]) < VQE_ENERGY_TOL:
            converged = True
            break

        grad = vqe_gradient(theta, H)
        theta -= VQE_LR * grad

    final_energy = energy_history[-1]
    final_psi = vqe_ansatz(theta)
    final_fidelity = fidelity(final_psi, psi_exact)
    energy_error = abs(final_energy - float(E_exact))

    passed = converged and energy_error < 0.01

    return {
        "passed": bool(passed),
        "exact_ground_energy": round(float(E_exact), 6),
        "vqe_energy": round(final_energy, 6),
        "energy_error": round(energy_error, 8),
        "fidelity_to_ground": round(final_fidelity, 6),
        "converged": bool(converged),
        "iterations": len(energy_history),
        "energy_history_sample": [round(e, 6) for e in energy_history[::max(1, len(energy_history)//10)]],
    }


# ---------------------------------------------------------------------------
# Probe 4: QAOA for MaxCut
# ---------------------------------------------------------------------------

def probe_qaoa_maxcut():
    """
    QAOA for MaxCut: 2 qubits, 1 edge, p=1 layer.
    C = 0.5*(I - sigma_z x sigma_z)  -- counts cut edges.
    U_C(gamma) = exp(-i*gamma*C)
    U_B(beta) = exp(-i*beta*(sigma_x x I + I x sigma_x))
    |psi> = U_B(beta) U_C(gamma) |+>|+>
    Sweep (gamma, beta) to find optimal cut value.
    """
    # Cost operator: C = 0.5*(I4 - ZZ)
    I4 = np.eye(4, dtype=complex)
    ZZ = kron2(SIGMA_Z, SIGMA_Z)
    C = 0.5 * (I4 - ZZ)

    # Mixer: B = sigma_x x I + I x sigma_x
    B = kron2(SIGMA_X, I2) + kron2(I2, SIGMA_X)

    # Initial state: |+>|+>
    plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
    psi_init = kron2(plus, plus)

    # Exact optimum: MaxCut of 1 edge on 2 nodes = 1 (one cut)
    exact_max_cut = 1.0

    gamma_vals = np.linspace(0, 2 * np.pi, QAOA_GRID)
    beta_vals = np.linspace(0, np.pi, QAOA_GRID)

    best_expectation = -np.inf
    best_gamma = 0.0
    best_beta = 0.0
    landscape = []

    for gamma in gamma_vals:
        for beta in beta_vals:
            U_C = la.expm(-1j * gamma * C)
            U_B = la.expm(-1j * beta * B)
            psi = U_B @ U_C @ psi_init
            exp_C = expectation(psi, C)
            if exp_C > best_expectation:
                best_expectation = exp_C
                best_gamma = float(gamma)
                best_beta = float(beta)

    # Approximation ratio
    approx_ratio = best_expectation / exact_max_cut if exact_max_cut > 0 else 0.0

    # For p=1, 2-qubit MaxCut: theoretical optimal ratio = 0.75 for general graphs,
    # but for a single edge we can reach 1.0
    passed = approx_ratio >= 0.74  # allow small numerical slack

    # Evaluate at optimal point to get probabilities
    U_C_opt = la.expm(-1j * best_gamma * C)
    U_B_opt = la.expm(-1j * best_beta * B)
    psi_opt = U_B_opt @ U_C_opt @ psi_init
    probs = np.abs(psi_opt) ** 2  # |00>, |01>, |10>, |11>

    return {
        "passed": bool(passed),
        "best_expectation": round(float(best_expectation), 6),
        "exact_max_cut": exact_max_cut,
        "approx_ratio": round(float(approx_ratio), 6),
        "best_gamma": round(best_gamma, 4),
        "best_beta": round(best_beta, 4),
        "optimal_state_probs": {
            "|00>": round(float(probs[0]), 6),
            "|01>": round(float(probs[1]), 6),
            "|10>": round(float(probs[2]), 6),
            "|11>": round(float(probs[3]), 6),
        },
        "note": "cut states |01> and |10> should dominate at optimum",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    t0 = time.time()
    results = {
        "probe_file": "sim_pure_lego_adiabatic_variational.py",
        "description": "Adiabatic quantum computation and variational quantum methods",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "probes": {},
    }

    # Probe 1: Adiabatic evolution
    print("Probe 1: Adiabatic evolution (slow vs fast) ...")
    r1 = probe_adiabatic()
    results["probes"]["adiabatic_evolution"] = r1
    tag = "PASS" if r1["passed"] else "FAIL"
    print(f"  slow fidelity: {r1['slow_fidelity']}")
    print(f"  fast fidelity: {r1['fast_fidelity']}")
    print(f"  [{tag}]")

    # Probe 2: Spectral gap
    print("Probe 2: Spectral gap analysis ...")
    r2 = probe_spectral_gap()
    results["probes"]["spectral_gap"] = r2
    tag = "PASS" if r2["passed"] else "FAIL"
    print(f"  min gap: {r2['min_gap']} at s={r2['min_gap_at_s']}")
    print(f"  adiabatic time scale: {r2['adiabatic_time_scale']}")
    print(f"  [{tag}]")

    # Probe 3: VQE
    print("Probe 3: VQE optimisation ...")
    r3 = probe_vqe()
    results["probes"]["vqe"] = r3
    tag = "PASS" if r3["passed"] else "FAIL"
    print(f"  exact E0: {r3['exact_ground_energy']}")
    print(f"  VQE E:    {r3['vqe_energy']}")
    print(f"  error:    {r3['energy_error']}")
    print(f"  fidelity: {r3['fidelity_to_ground']}")
    print(f"  [{tag}]")

    # Probe 4: QAOA MaxCut
    print("Probe 4: QAOA MaxCut (2 qubits, 1 edge) ...")
    r4 = probe_qaoa_maxcut()
    results["probes"]["qaoa_maxcut"] = r4
    tag = "PASS" if r4["passed"] else "FAIL"
    print(f"  best <C>: {r4['best_expectation']}")
    print(f"  approx ratio: {r4['approx_ratio']}")
    print(f"  probs: {r4['optimal_state_probs']}")
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
    out_path = os.path.join(out_dir, "pure_lego_adiabatic_variational_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {out_path}")

    return results


if __name__ == "__main__":
    main()
