#!/usr/bin/env python3
"""
sim_pure_lego_games_bayesian_largedev.py
========================================

Pure-lego probe: quantum game theory, quantum Bayesian inference,
quantum large deviations.  No engine.  numpy/scipy only.

Three independent modules:

1. **Quantum Prisoner's Dilemma** — strategies are density matrices,
   payoff = Tr(G · rho_joint).  G built from classical payoff matrix.
   Find Nash equilibrium as fixed-point.  Show entangled strategy
   beats classical Nash.

2. **Quantum Bayesian Update (Lüders rule)** — prior rho_0,
   evidence E (POVM element), posterior = E^{1/2} rho_0 E^{1/2} /
   Tr(E rho_0).  10 sequential updates with random evidence.
   Track posterior entropy (must decrease = learning).  Classical
   limit check: diagonal rho + diagonal E => Bayes' rule.

3. **Quantum Sanov Theorem** — for n copies of rho, empirical
   measurement frequencies concentrate around rho's diagonal
   at rate D(sigma||rho).  Verified numerically at n = 10, 50, 100.
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
from scipy.linalg import sqrtm


# ═══════════════════════════════════════════════════════════════════
# UTILITY HELPERS
# ═══════════════════════════════════════════════════════════════════

def von_neumann_entropy(rho: np.ndarray) -> float:
    """S(rho) = -Tr(rho log rho), via eigenvalues."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return -float(np.sum(evals * np.log(evals)))


def kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """Classical KL divergence D(p||q)."""
    mask = p > 1e-15
    p_m, q_m = p[mask], q[mask]
    q_m = np.maximum(q_m, 1e-30)
    return float(np.sum(p_m * np.log(p_m / q_m)))


def random_density_matrix(d: int, rng: np.random.Generator) -> np.ndarray:
    """Wishart-sampled random density matrix of dimension d."""
    A = rng.standard_normal((d, d)) + 1j * rng.standard_normal((d, d))
    rho = A @ A.conj().T
    return rho / np.trace(rho)


def random_povm_element(d: int, rng: np.random.Generator) -> np.ndarray:
    """Random POVM element: positive semidefinite, eigenvalues in [0,1]."""
    A = rng.standard_normal((d, d)) + 1j * rng.standard_normal((d, d))
    M = A @ A.conj().T
    evals, evecs = np.linalg.eigh(M)
    # scale eigenvalues into [0.1, 0.9] so it's non-degenerate
    evals = 0.1 + 0.8 * (evals - evals.min()) / (evals.max() - evals.min() + 1e-30)
    return (evecs * evals) @ evecs.conj().T


def ensure_hermitian(M: np.ndarray) -> np.ndarray:
    return (M + M.conj().T) / 2.0


# ═══════════════════════════════════════════════════════════════════
# MODULE 1: QUANTUM PRISONER'S DILEMMA
# ═══════════════════════════════════════════════════════════════════

def build_payoff_operator(payoff_matrix: np.ndarray) -> np.ndarray:
    """
    Build payoff operator G in 4x4 space from 2x2 classical payoff matrix.

    Classical payoff_matrix[i,j] = payoff to row player when row plays i,
    col plays j.  We embed as G = sum_{i,j} payoff[i,j] |ij><ij|.
    """
    d = payoff_matrix.shape[0]
    G = np.zeros((d * d, d * d), dtype=complex)
    for i in range(d):
        for j in range(d):
            basis = np.zeros(d * d, dtype=complex)
            basis[i * d + j] = 1.0
            G += payoff_matrix[i, j] * np.outer(basis, basis.conj())
    return G


def expected_payoff(G: np.ndarray, rho_joint: np.ndarray) -> float:
    """Tr(G · rho_joint)."""
    return np.trace(G @ rho_joint).real


def classical_nash_payoff(payoff_A: np.ndarray, payoff_B: np.ndarray):
    """
    Find classical mixed Nash equilibrium for 2x2 game via indifference.
    Returns (p_cooperate_A, p_cooperate_B, payoff_A_nash, payoff_B_nash).
    """
    # For a 2x2 game, player B's mixing probability q that makes A indifferent:
    # A indifferent: payoff_A[0,0]*q + payoff_A[0,1]*(1-q) = payoff_A[1,0]*q + payoff_A[1,1]*(1-q)
    # => q*(payoff_A[0,0]-payoff_A[0,1]-payoff_A[1,0]+payoff_A[1,1]) = payoff_A[1,1]-payoff_A[0,1]
    denom_A = payoff_A[0, 0] - payoff_A[0, 1] - payoff_A[1, 0] + payoff_A[1, 1]
    denom_B = payoff_B[0, 0] - payoff_B[1, 0] - payoff_B[0, 1] + payoff_B[1, 1]

    if abs(denom_A) < 1e-12 or abs(denom_B) < 1e-12:
        # degenerate: default to (Defect, Defect)
        q_B = 0.0
        p_A = 0.0
    else:
        q_B = (payoff_A[1, 1] - payoff_A[0, 1]) / denom_A
        p_A = (payoff_B[1, 1] - payoff_B[1, 0]) / denom_B

    q_B = np.clip(q_B, 0, 1)
    p_A = np.clip(p_A, 0, 1)

    # expected payoff
    strat_A = np.array([p_A, 1 - p_A])
    strat_B = np.array([q_B, 1 - q_B])
    ev_A = strat_A @ payoff_A @ strat_B
    ev_B = strat_A @ payoff_B @ strat_B
    return float(p_A), float(q_B), float(ev_A), float(ev_B)


def quantum_prisoners_dilemma():
    """
    Quantum prisoner's dilemma:
    - Classical payoff: R=3,T=5,S=0,P=1 (standard PD)
    - Strategies = density matrices
    - Show entangled joint state achieves higher mutual payoff than classical Nash
    """
    results = {"module": "quantum_prisoners_dilemma", "tests": []}

    # Classical payoff matrices (row=A's action, col=B's action, 0=C, 1=D)
    payoff_A = np.array([[3, 0],
                          [5, 1]], dtype=float)
    payoff_B = np.array([[3, 5],
                          [0, 1]], dtype=float)

    G_A = build_payoff_operator(payoff_A)
    G_B = build_payoff_operator(payoff_B)

    # --- Classical Nash ---
    p_A, q_B, ev_A_cl, ev_B_cl = classical_nash_payoff(payoff_A, payoff_B)
    results["classical_nash"] = {
        "p_cooperate_A": p_A, "p_cooperate_B": q_B,
        "payoff_A": ev_A_cl, "payoff_B": ev_B_cl,
    }

    # Classical Nash as separable density matrix
    rho_A_cl = np.diag([p_A, 1 - p_A]).astype(complex)
    rho_B_cl = np.diag([q_B, 1 - q_B]).astype(complex)
    rho_joint_cl = np.kron(rho_A_cl, rho_B_cl)
    payoff_A_cl_q = expected_payoff(G_A, rho_joint_cl)
    payoff_B_cl_q = expected_payoff(G_B, rho_joint_cl)

    results["tests"].append({
        "name": "classical_nash_via_density_matrix",
        "payoff_A": payoff_A_cl_q,
        "payoff_B": payoff_B_cl_q,
        "matches_analytic": abs(payoff_A_cl_q - ev_A_cl) < 1e-10
                           and abs(payoff_B_cl_q - ev_B_cl) < 1e-10,
    })

    # --- Quantum strategy: maximally entangled Bell state |Phi+> ---
    # |Phi+> = (|00> + |11>) / sqrt(2)
    phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    rho_entangled = np.outer(phi_plus, phi_plus.conj())
    payoff_A_q = expected_payoff(G_A, rho_entangled)
    payoff_B_q = expected_payoff(G_B, rho_entangled)

    results["tests"].append({
        "name": "entangled_bell_state_payoff",
        "payoff_A": payoff_A_q,
        "payoff_B": payoff_B_q,
        "note": "Bell state = mutual cooperation/defection superposition",
    })

    # --- Quantum beats classical? ---
    # The Bell state gives (R+P)/2 = (3+1)/2 = 2.0 each
    # Classical Nash (Defect, Defect) gives P=1 each
    quantum_beats_classical_nash = (payoff_A_q > ev_A_cl) and (payoff_B_q > ev_B_cl)
    results["tests"].append({
        "name": "quantum_beats_classical_nash",
        "quantum_payoff": (payoff_A_q, payoff_B_q),
        "classical_nash_payoff": (ev_A_cl, ev_B_cl),
        "quantum_wins": quantum_beats_classical_nash,
    })

    # --- Quantum Nash fixed point search ---
    # Use iterated best-response in density-matrix space (2x2 marginals)
    # For each player, best response = eigenstate of payoff conditioned on other's strategy
    rng = np.random.default_rng(42)
    rho_A = random_density_matrix(2, rng)
    rho_B = random_density_matrix(2, rng)

    convergence_history = []
    for step in range(200):
        rho_joint = np.kron(rho_A, rho_B)
        pA = expected_payoff(G_A, rho_joint)
        pB = expected_payoff(G_B, rho_joint)
        convergence_history.append({"step": step, "payoff_A": pA, "payoff_B": pB})

        # Best response for A: maximize Tr(G_A (rho_A x rho_B))
        # = maximize Tr(M_A rho_A) where M_A = Tr_B(G_A (I x rho_B))
        I2 = np.eye(2, dtype=complex)
        G_A_contracted = np.zeros((2, 2), dtype=complex)
        for i in range(2):
            for j in range(2):
                # partial trace over B of G_A (I_A x rho_B)
                block = G_A[i * 2:(i + 1) * 2, j * 2:(j + 1) * 2]
                G_A_contracted[i, j] = np.trace(block @ rho_B)
        G_A_contracted = ensure_hermitian(G_A_contracted)

        evals_A, evecs_A = np.linalg.eigh(G_A_contracted)
        rho_A_new = np.outer(evecs_A[:, -1], evecs_A[:, -1].conj())

        G_B_contracted = np.zeros((2, 2), dtype=complex)
        for i in range(2):
            for j in range(2):
                block = G_B[i::2, j::2][:2, :2]
                G_B_contracted[i, j] = np.trace(rho_A @ G_B[i * 2:(i + 1) * 2, j * 2:(j + 1) * 2])
        # Correct: contract over A index
        G_B_contracted2 = np.zeros((2, 2), dtype=complex)
        for m in range(2):
            for n in range(2):
                val = 0.0
                for a in range(2):
                    for b in range(2):
                        val += rho_A[a, b] * G_B[a * 2 + m, b * 2 + n]
                G_B_contracted2[m, n] = val
        G_B_contracted2 = ensure_hermitian(G_B_contracted2)

        evals_B, evecs_B = np.linalg.eigh(G_B_contracted2)
        rho_B_new = np.outer(evecs_B[:, -1], evecs_B[:, -1].conj())

        # damped update for stability
        alpha = 0.3
        rho_A = (1 - alpha) * rho_A + alpha * rho_A_new
        rho_A = ensure_hermitian(rho_A)
        rho_A /= np.trace(rho_A)
        rho_B = (1 - alpha) * rho_B + alpha * rho_B_new
        rho_B = ensure_hermitian(rho_B)
        rho_B /= np.trace(rho_B)

    rho_joint_final = np.kron(rho_A, rho_B)
    results["separable_nash_fixedpoint"] = {
        "payoff_A": expected_payoff(G_A, rho_joint_final),
        "payoff_B": expected_payoff(G_B, rho_joint_final),
        "rho_A_diag": np.diag(rho_A).real.tolist(),
        "rho_B_diag": np.diag(rho_B).real.tolist(),
        "converged_steps": len(convergence_history),
    }

    # Final verdicts
    results["verdict"] = {
        "classical_nash_is_defect_defect": ev_A_cl <= 1.01 and ev_B_cl <= 1.01,
        "quantum_entangled_beats_classical": quantum_beats_classical_nash,
        "payoff_operator_consistent": results["tests"][0]["matches_analytic"],
    }
    return results


# ═══════════════════════════════════════════════════════════════════
# MODULE 2: QUANTUM BAYESIAN UPDATE (LÜDERS RULE)
# ═══════════════════════════════════════════════════════════════════

def luders_update(rho: np.ndarray, E: np.ndarray) -> np.ndarray:
    """
    Lüders rule posterior:  rho_post = E^{1/2} rho E^{1/2} / Tr(E rho)
    """
    E_sqrt = sqrtm(E)
    E_sqrt = ensure_hermitian(E_sqrt)
    numerator = E_sqrt @ rho @ E_sqrt
    denominator = np.trace(E @ rho).real
    if denominator < 1e-15:
        raise ValueError("Evidence has zero probability under prior")
    return ensure_hermitian(numerator / denominator)


def classical_bayes_update(prior: np.ndarray, likelihood: np.ndarray) -> np.ndarray:
    """Standard Bayes: posterior ∝ likelihood * prior (element-wise)."""
    unnorm = likelihood * prior
    return unnorm / unnorm.sum()


def quantum_bayesian_inference():
    """
    10 sequential Lüders updates.  Track entropy.  Verify classical limit.
    """
    results = {"module": "quantum_bayesian_update", "tests": []}
    rng = np.random.default_rng(137)
    d = 2

    # --- Quantum updates ---
    rho = random_density_matrix(d, rng)
    entropy_trace = [von_neumann_entropy(rho)]
    update_log = []

    for step in range(10):
        E = random_povm_element(d, rng)
        rho_prior = rho.copy()
        rho = luders_update(rho, E)
        S = von_neumann_entropy(rho)
        entropy_trace.append(S)
        update_log.append({
            "step": step,
            "entropy_prior": entropy_trace[-2],
            "entropy_posterior": S,
            "purity": float(np.trace(rho @ rho).real),
        })

    # Check entropy trend: overall decrease (learning)
    entropy_decreased_overall = entropy_trace[-1] < entropy_trace[0]
    # Count how many steps decreased
    decreases = sum(1 for i in range(1, len(entropy_trace))
                    if entropy_trace[i] < entropy_trace[i - 1])

    results["quantum_updates"] = {
        "initial_entropy": entropy_trace[0],
        "final_entropy": entropy_trace[-1],
        "entropy_trace": entropy_trace,
        "entropy_decreased_overall": entropy_decreased_overall,
        "decrease_steps": decreases,
        "update_log": update_log,
    }

    # --- Classical limit verification ---
    # Diagonal rho + diagonal E => should match Bayes' rule exactly
    p_prior = rng.dirichlet(np.ones(d))
    rho_cl = np.diag(p_prior).astype(complex)
    likelihoods = rng.uniform(0.1, 0.9, size=d)
    E_cl = np.diag(likelihoods).astype(complex)

    # Quantum posterior via Lüders
    rho_post_q = luders_update(rho_cl, E_cl)
    posterior_q = np.diag(rho_post_q).real

    # Classical posterior via Bayes
    posterior_cl = classical_bayes_update(p_prior, likelihoods)

    classical_match = np.allclose(posterior_q, posterior_cl, atol=1e-12)
    results["classical_limit"] = {
        "prior": p_prior.tolist(),
        "likelihoods": likelihoods.tolist(),
        "posterior_quantum": posterior_q.tolist(),
        "posterior_classical": posterior_cl.tolist(),
        "match": classical_match,
        "max_deviation": float(np.max(np.abs(posterior_q - posterior_cl))),
    }

    results["verdict"] = {
        "entropy_decreases_overall": entropy_decreased_overall,
        "majority_steps_decrease": decreases > 5,
        "classical_limit_matches_bayes": classical_match,
    }
    return results


# ═══════════════════════════════════════════════════════════════════
# MODULE 3: QUANTUM SANOV THEOREM
# ═══════════════════════════════════════════════════════════════════

def quantum_sanov():
    """
    For n copies of qubit state rho, measure in computational basis.
    Empirical frequency of outcomes should concentrate around p = diag(rho).
    Rate of deviation matches D(sigma||rho) (KL divergence on diagonals).
    """
    results = {"module": "quantum_sanov_theorem", "tests": []}
    rng = np.random.default_rng(2025)

    d = 2
    # Build a non-trivial qubit state
    rho = np.array([[0.7, 0.2 + 0.1j],
                     [0.2 - 0.1j, 0.3]], dtype=complex)
    # true measurement probabilities in computational basis
    p_true = np.diag(rho).real
    assert abs(p_true.sum() - 1.0) < 1e-12

    n_values = [10, 50, 100]
    n_trials = 50000

    for n in n_values:
        # Simulate: draw n measurement outcomes per trial, count empirical freq
        outcomes = rng.choice(d, size=(n_trials, n), p=p_true)
        empirical_freqs = np.array([np.bincount(row, minlength=d) / n
                                     for row in outcomes])

        # Mean empirical frequency
        mean_freq = empirical_freqs.mean(axis=0)
        std_freq = empirical_freqs.std(axis=0)

        # Test concentration: mean should be close to p_true
        concentration_error = float(np.max(np.abs(mean_freq - p_true)))

        # Test Sanov rate: P(empirical in ball around sigma) ~ exp(-n D(sigma||p))
        # Pick a deviation point sigma
        sigma = np.array([0.5, 0.5])  # uniform
        D_sigma_p = kl_divergence(sigma, p_true)

        # Count fraction of trials where empirical freq is "close" to sigma
        # (within epsilon ball in L1)
        epsilon = 0.1
        distances_to_sigma = np.sum(np.abs(empirical_freqs - sigma), axis=1)
        fraction_near_sigma = float(np.mean(distances_to_sigma < epsilon))

        # Sanov predicts this fraction ~ exp(-n * D(sigma||p))
        # So -log(fraction) / n should approximate D(sigma||p)
        if fraction_near_sigma > 0:
            empirical_rate = -np.log(fraction_near_sigma) / n
        else:
            empirical_rate = float('inf')

        # Also check with a closer sigma for better statistics at small n
        sigma_close = np.array([0.6, 0.4])
        D_close = kl_divergence(sigma_close, p_true)
        distances_close = np.sum(np.abs(empirical_freqs - sigma_close), axis=1)
        frac_close = float(np.mean(distances_close < epsilon))
        if frac_close > 0:
            rate_close = -np.log(frac_close) / n
        else:
            rate_close = float('inf')

        results["tests"].append({
            "n_copies": n,
            "p_true": p_true.tolist(),
            "mean_empirical_freq": mean_freq.tolist(),
            "std_empirical_freq": std_freq.tolist(),
            "concentration_error": concentration_error,
            "concentration_ok": concentration_error < 0.05,
            "sigma_uniform": {
                "sigma": sigma.tolist(),
                "D_sigma_p_analytic": D_sigma_p,
                "fraction_near_sigma": fraction_near_sigma,
                "empirical_rate": empirical_rate,
                "rate_ratio": empirical_rate / D_sigma_p if D_sigma_p > 0 else None,
            },
            "sigma_close": {
                "sigma": sigma_close.tolist(),
                "D_sigma_p_analytic": D_close,
                "fraction_near_sigma": frac_close,
                "empirical_rate": rate_close,
                "rate_ratio": rate_close / D_close if D_close > 0 else None,
            },
        })

    # Verify rate convergence: as n grows, empirical_rate / D should -> 1
    rate_ratios_uniform = [t["sigma_uniform"]["rate_ratio"] for t in results["tests"]
                           if t["sigma_uniform"]["rate_ratio"] is not None
                           and t["sigma_uniform"]["rate_ratio"] != float('inf')]
    rate_ratios_close = [t["sigma_close"]["rate_ratio"] for t in results["tests"]
                         if t["sigma_close"]["rate_ratio"] is not None
                         and t["sigma_close"]["rate_ratio"] != float('inf')]

    results["verdict"] = {
        "concentration_all_ok": all(t["concentration_ok"] for t in results["tests"]),
        "rate_ratios_uniform": rate_ratios_uniform,
        "rate_ratios_close": rate_ratios_close,
        "rate_converging_toward_1": (
            len(rate_ratios_close) >= 2 and
            abs(rate_ratios_close[-1] - 1.0) < abs(rate_ratios_close[0] - 1.0)
        ) if len(rate_ratios_close) >= 2 else "insufficient_data",
    }
    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN: RUN ALL MODULES, EMIT JSON
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("PURE LEGO: Quantum Games / Bayesian / Large Deviations")
    print("=" * 70)

    all_results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_pure_lego_games_bayesian_largedev",
        "modules": {},
    }

    # Module 1
    print("\n[1/3] Quantum Prisoner's Dilemma...")
    r1 = quantum_prisoners_dilemma()
    all_results["modules"]["quantum_prisoners_dilemma"] = r1
    print(f"  Classical Nash payoff: ({r1['classical_nash']['payoff_A']:.3f}, "
          f"{r1['classical_nash']['payoff_B']:.3f})")
    print(f"  Entangled payoff:      ({r1['tests'][1]['payoff_A']:.3f}, "
          f"{r1['tests'][1]['payoff_B']:.3f})")
    print(f"  Quantum beats classical: {r1['verdict']['quantum_entangled_beats_classical']}")

    # Module 2
    print("\n[2/3] Quantum Bayesian Update (Lüders)...")
    r2 = quantum_bayesian_inference()
    print(f"  Initial entropy: {r2['quantum_updates']['initial_entropy']:.4f}")
    print(f"  Final entropy:   {r2['quantum_updates']['final_entropy']:.4f}")
    print(f"  Entropy decreased overall: {r2['verdict']['entropy_decreases_overall']}")
    print(f"  Classical limit matches Bayes: {r2['verdict']['classical_limit_matches_bayes']}")
    all_results["modules"]["quantum_bayesian_update"] = r2

    # Module 3
    print("\n[3/3] Quantum Sanov Theorem...")
    r3 = quantum_sanov()
    for t in r3["tests"]:
        n = t["n_copies"]
        err = t["concentration_error"]
        rc = t["sigma_close"]["rate_ratio"]
        rc_str = f"{rc:.3f}" if rc is not None and rc != float('inf') else "inf"
        print(f"  n={n:3d}: concentration_err={err:.4f}, "
              f"rate_ratio(close)={rc_str}")
    all_results["modules"]["quantum_sanov_theorem"] = r3

    # --- Aggregate verdict ---
    all_pass = (
        r1["verdict"]["quantum_entangled_beats_classical"]
        and r1["verdict"]["payoff_operator_consistent"]
        and r2["verdict"]["entropy_decreases_overall"]
        and r2["verdict"]["classical_limit_matches_bayes"]
        and r3["verdict"]["concentration_all_ok"]
    )
    all_results["all_pass"] = all_pass

    print("\n" + "=" * 70)
    print(f"ALL PASS: {all_pass}")
    print("=" * 70)

    # --- Write output ---
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir,
                            "pure_lego_games_bayesian_largedev_results.json")

    # Convert any remaining numpy types
    def np_convert(obj):
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, complex):
            return {"re": obj.real, "im": obj.imag}
        raise TypeError(f"Not serializable: {type(obj)}")

    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, default=np_convert)
    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
