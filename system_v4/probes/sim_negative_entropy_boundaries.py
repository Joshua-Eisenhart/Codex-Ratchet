#!/usr/bin/env python3
"""
Negative Entropy Boundaries Battery
====================================
Pure numpy/scipy probe -- NO engine dependency.

Tests where entropy measures diverge, become undefined, or give
numerically wrong answers.  Ten sections:

  T1  vN entropy of pure state: numerical eigenvalue noise -> negative S
  T2  Renyi alpha < 0, alpha = 0, alpha -> 1 limit
  T3  Relative entropy D(rho||sigma) when supp(rho) not in supp(sigma)
  T4  Conditional entropy S(A|B) for maximally entangled / near-entangled
  T5  Mutual information for product state: should be 0
  T6  Tsallis q -> inf: convergence to min-entropy
  T7  Linear entropy for d=2 and d=100 pure/max-mixed
  T8  All entropies on rank-1 to rank-2 boundary
  T9  Entropy of non-density-matrices
  T10 Shannon vs vN: maximal disagreement
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
from scipy.linalg import logm

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_log2(x):
    """log2 with 0*log(0)=0 convention."""
    x = np.asarray(x, dtype=float)
    out = np.zeros_like(x)
    mask = x > 0
    out[mask] = np.log2(x[mask])
    return out


def vn_entropy(rho):
    """Von Neumann entropy in bits from eigenvalues of rho."""
    evals = np.linalg.eigvalsh(rho)
    evals = np.real(evals)
    return float(-np.sum(evals * _safe_log2(evals)))


def vn_entropy_clipped(rho):
    """Von Neumann entropy clipping negative eigenvalues to 0."""
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = np.clip(evals, 0, None)
    s = evals.sum()
    if s > 0:
        evals = evals / s  # renormalise after clip
    return float(-np.sum(evals * _safe_log2(evals)))


def renyi_entropy(rho, alpha):
    """Renyi-alpha entropy in bits.  alpha != 1."""
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 0]
    if len(evals) == 0:
        return float('nan')
    if alpha == 0:
        return float(np.log2(len(evals)))
    if alpha == 1:
        return float(-np.sum(evals * _safe_log2(evals)))
    val = np.sum(evals ** alpha)
    if val <= 0:
        return float('nan')
    return float(np.log2(val) / (1 - alpha))


def tsallis_entropy(rho, q):
    """Tsallis-q entropy (natural units)."""
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 0]
    if len(evals) == 0:
        return float('nan')
    if q == 1:
        return float(-np.sum(evals * np.log(evals)))
    return float((1 - np.sum(evals ** q)) / (q - 1))


def min_entropy(rho):
    """Min-entropy = -log2(lambda_max)."""
    evals = np.real(np.linalg.eigvalsh(rho))
    return float(-np.log2(max(evals)))


def linear_entropy(rho):
    """Linear entropy = 1 - Tr(rho^2)."""
    return float(1.0 - np.real(np.trace(rho @ rho)))


def relative_entropy(rho, sigma):
    """Quantum relative entropy D(rho||sigma) = Tr(rho (log rho - log sigma)).
    Returns +inf when supp(rho) not in supp(sigma)."""
    evals_sigma = np.real(np.linalg.eigvalsh(sigma))
    evals_rho = np.real(np.linalg.eigvalsh(rho))
    # Check support condition
    rho_support = evals_rho > 1e-14
    sigma_support = evals_sigma > 1e-14
    # Project rho into sigma's eigenbasis and check
    # Simpler: use matrix log
    try:
        log_rho = logm(rho)
        log_sigma = logm(sigma)
    except Exception:
        return float('inf')
    # If sigma has zero eigenvalues where rho doesn't, result is +inf
    for i, (er, es) in enumerate(zip(sorted(evals_rho, reverse=True),
                                      sorted(evals_sigma, reverse=True))):
        pass  # using matrix approach instead
    val = np.real(np.trace(rho @ (log_rho - log_sigma)))
    # Check for support violation explicitly
    U_sigma = np.linalg.eigh(sigma)[1]
    rho_in_sigma_basis = U_sigma.conj().T @ rho @ U_sigma
    for i, es in enumerate(evals_sigma):
        if es < 1e-14 and abs(rho_in_sigma_basis[i, i]) > 1e-14:
            return float('inf')
    return float(np.real(val))


def shannon_entropy(probs):
    """Shannon entropy in bits from probability vector."""
    p = np.asarray(probs, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def make_pure_state(d, idx=0):
    """Return |idx><idx| as a d x d density matrix."""
    rho = np.zeros((d, d), dtype=complex)
    rho[idx, idx] = 1.0
    return rho


def make_max_mixed(d):
    """Return I/d."""
    return np.eye(d, dtype=complex) / d


def make_bell_state():
    """Return |Phi+><Phi+| density matrix for 2 qubits."""
    phi = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    return np.outer(phi, phi.conj())


def partial_trace(rho_ab, d_a, d_b, trace_out='B'):
    """Partial trace of rho_ab over subsystem B (or A)."""
    rho = rho_ab.reshape(d_a, d_b, d_a, d_b)
    if trace_out == 'B':
        return np.trace(rho, axis1=1, axis2=3)
    else:
        return np.trace(rho, axis1=0, axis2=2)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_t1_vn_pure_state_noise():
    """T1: vN entropy of pure state with numerical noise."""
    print("\n  [T1] vN entropy of pure state: eigenvalue noise thresholds")
    rho_pure = make_pure_state(2)
    s_exact = vn_entropy(rho_pure)
    s_clipped = vn_entropy_clipped(rho_pure)

    # Inject controlled noise levels
    noise_levels = np.logspace(-18, -6, 50)
    results = []
    crossover_noise = None
    for eps in noise_levels:
        rho_noisy = rho_pure.copy()
        # Add hermitian noise
        noise = np.array([[eps, 0], [0, -eps]], dtype=complex)
        rho_n = rho_noisy + noise
        s_raw = vn_entropy(rho_n)
        s_clip = vn_entropy_clipped(rho_n)
        results.append({
            "noise_level": float(eps),
            "s_raw": s_raw,
            "s_clipped": s_clip,
            "s_raw_negative": s_raw < -1e-15,
        })
        if crossover_noise is None and abs(s_raw) > 1e-10:
            crossover_noise = float(eps)

    # Also test what numpy eigvalsh actually gives for a pure state
    evals_pure = np.linalg.eigvalsh(rho_pure)
    min_eval = float(min(evals_pure))

    negative_count = sum(1 for r in results if r["s_raw_negative"])
    worst_negative = min(r["s_raw"] for r in results)

    print(f"    Exact pure state S: {s_exact:.2e}")
    print(f"    Clipped pure state S: {s_clipped:.2e}")
    print(f"    Min eigenvalue from eigvalsh(pure): {min_eval:.2e}")
    print(f"    Noise levels producing negative S: {negative_count}/{len(results)}")
    print(f"    Worst negative S: {worst_negative:.2e}")
    print(f"    Crossover noise (|S|>1e-10): {crossover_noise}")

    return {
        "s_exact_pure": s_exact,
        "s_clipped_pure": s_clipped,
        "min_eigenvalue_pure": min_eval,
        "negative_count": negative_count,
        "worst_negative_s": worst_negative,
        "crossover_noise_level": crossover_noise,
        "noise_sweep": results,
    }


def test_t2_renyi_edge_cases():
    """T2: Renyi alpha edge cases."""
    print("\n  [T2] Renyi alpha edge cases")
    rho_mixed = make_max_mixed(4)
    rho_pure = make_pure_state(4)
    rho_rank2 = np.zeros((4, 4), dtype=complex)
    rho_rank2[0, 0] = 0.5
    rho_rank2[1, 1] = 0.5

    # alpha < 0: should be undefined / blow up
    alpha_neg_results = []
    for alpha in [-2.0, -1.0, -0.5, -0.1]:
        try:
            s = renyi_entropy(rho_mixed, alpha)
            alpha_neg_results.append({"alpha": alpha, "value": s, "error": None})
        except Exception as e:
            alpha_neg_results.append({"alpha": alpha, "value": None, "error": str(e)})

    # alpha = 0: log(rank)
    s_a0_mixed = renyi_entropy(rho_mixed, 0)  # should be log2(4)=2
    s_a0_pure = renyi_entropy(rho_pure, 0)    # should be log2(1)=0
    s_a0_rank2 = renyi_entropy(rho_rank2, 0)  # should be log2(2)=1
    # Zero matrix: rank 0
    s_a0_zero = renyi_entropy(np.zeros((2, 2)), 0)

    # alpha -> 1: should converge to vN
    alphas_near_1 = [0.5, 0.9, 0.99, 0.999, 0.9999, 1.0001, 1.001, 1.01, 1.1, 1.5, 2.0]
    convergence = []
    s_vn = vn_entropy(rho_mixed)
    for a in alphas_near_1:
        s_r = renyi_entropy(rho_mixed, a)
        convergence.append({"alpha": a, "renyi": s_r, "error_vs_vn": abs(s_r - s_vn)})

    print(f"    alpha=0 max_mixed(4): {s_a0_mixed:.4f} (expect 2.0)")
    print(f"    alpha=0 pure: {s_a0_pure:.4f} (expect 0.0)")
    print(f"    alpha=0 rank-2: {s_a0_rank2:.4f} (expect 1.0)")
    print(f"    alpha=0 zero matrix: {s_a0_zero}")
    print(f"    alpha<0 results: {[r['value'] for r in alpha_neg_results]}")
    conv_strs = ["{:.4f}->{:.2e}".format(c["alpha"], c["error_vs_vn"]) for c in convergence]
    print("    alpha->1 convergence errors: {}".format(conv_strs))

    return {
        "alpha_negative": alpha_neg_results,
        "alpha_0_max_mixed_4": s_a0_mixed,
        "alpha_0_pure": s_a0_pure,
        "alpha_0_rank2": s_a0_rank2,
        "alpha_0_zero_matrix": s_a0_zero,
        "alpha_near_1_convergence": convergence,
        "vn_reference": s_vn,
    }


def test_t3_relative_entropy_support():
    """T3: Relative entropy divergence when supports mismatch."""
    print("\n  [T3] Relative entropy D(rho||sigma) support violations")

    # Case 1: rho has support outside sigma
    rho = make_max_mixed(2)  # full support
    sigma = make_pure_state(2)  # rank-1 support
    d_case1 = relative_entropy(rho, sigma)

    # Case 2: sigma has larger support (should be finite)
    rho2 = make_pure_state(2)
    sigma2 = make_max_mixed(2)
    d_case2 = relative_entropy(rho2, sigma2)

    # Case 3: identical states
    d_case3 = relative_entropy(rho, rho)

    # Case 4: approaching support boundary -- sigma eigenvalue -> 0
    boundary_results = []
    for eps in np.logspace(-1, -14, 28):
        sigma_eps = np.array([[1.0 - eps, 0], [0, eps]], dtype=complex)
        rho_full = make_max_mixed(2)
        d = relative_entropy(rho_full, sigma_eps)
        boundary_results.append({"sigma_min_eval": float(eps), "D": d})

    print(f"    D(max_mixed || pure): {d_case1} (expect +inf)")
    print(f"    D(pure || max_mixed): {d_case2:.4f} (expect ln(2)=0.6931 nats)")
    print(f"    D(rho || rho): {d_case3:.2e} (expect 0.0)")
    print(f"    D as sigma_min -> 0: {boundary_results[-1]['D']:.4f} -> diverging")

    return {
        "support_violation_inf": d_case1,
        "pure_vs_mixed": d_case2,
        "self_relative_entropy": d_case3,
        "boundary_approach": boundary_results,
    }


def test_t4_conditional_entropy():
    """T4: Conditional entropy S(A|B) for entangled states.

    For PURE bipartite states |psi>_AB, S(AB)=0 so S(A|B) = -S(B),
    which is negative whenever there is any entanglement (trivial crossing
    at the product boundary).

    The interesting crossing is for MIXED states.  We use the Werner state:
        rho_W(p) = p |Phi+><Phi+| + (1-p) I/4
    At p=1 (Bell), S(A|B) = -1.  At p=0 (max mixed), S(A|B) = 0.
    Somewhere in between it crosses zero -- that is the entanglement
    boundary for conditional entropy.
    """
    print("\n  [T4] Conditional entropy S(A|B) for entangled / near-entangled")

    # Pure Bell state baseline
    rho_bell = make_bell_state()
    rho_a = partial_trace(rho_bell, 2, 2, 'B')
    rho_b = partial_trace(rho_bell, 2, 2, 'A')
    s_ab = vn_entropy(rho_bell)
    s_b = vn_entropy(rho_b)
    s_a = vn_entropy(rho_a)
    cond_bell = s_ab - s_b

    print(f"    Bell state: S(AB)={s_ab:.4f}, S(A)={s_a:.4f}, S(B)={s_b:.4f}")
    print(f"    S(A|B) = {cond_bell:.4f} (expect -1.0)")

    # Pure-state sweep: cos(t)|00> + sin(t)|11>
    thetas = np.linspace(0.001, np.pi / 4, 100)
    pure_sweep = []
    for t in thetas:
        psi = np.array([np.cos(t), 0, 0, np.sin(t)], dtype=complex)
        rho = np.outer(psi, psi.conj())
        r_b = partial_trace(rho, 2, 2, 'A')
        s_tot = vn_entropy(rho)
        s_b_val = vn_entropy(r_b)
        cond = s_tot - s_b_val  # = -S(B) for pure states
        pure_sweep.append({"theta": float(t), "S_A_given_B": cond, "S_B": s_b_val})

    print(f"    Pure sweep: S(A|B) range [{pure_sweep[0]['S_A_given_B']:.6f}, "
          f"{pure_sweep[-1]['S_A_given_B']:.4f}]")
    print(f"    (All negative for entangled pure states -- crossing at product boundary)")

    # Werner state sweep: rho_W(p) = p|Phi+><Phi+| + (1-p)I/4
    ps = np.linspace(0, 1, 500)
    werner_sweep = []
    zero_crossing_p = None
    for p in ps:
        rho_w = p * rho_bell + (1 - p) * np.eye(4, dtype=complex) / 4
        r_b_w = partial_trace(rho_w, 2, 2, 'A')
        s_ab_w = vn_entropy(rho_w)
        s_b_w = vn_entropy(r_b_w)
        cond_w = s_ab_w - s_b_w
        werner_sweep.append({"p": float(p), "S_AB": s_ab_w, "S_B": s_b_w,
                             "S_A_given_B": cond_w})
        if zero_crossing_p is None and cond_w < 0:
            zero_crossing_p = float(p)

    # Refine zero crossing via binary search
    if zero_crossing_p is not None:
        lo, hi = zero_crossing_p - 0.002, zero_crossing_p
        lo = max(lo, 0.0)
        for _ in range(80):
            mid = (lo + hi) / 2
            rho_w = mid * rho_bell + (1 - mid) * np.eye(4, dtype=complex) / 4
            r_b_w = partial_trace(rho_w, 2, 2, 'A')
            cond_w = vn_entropy(rho_w) - vn_entropy(r_b_w)
            if cond_w < 0:
                hi = mid
            else:
                lo = mid
        zero_crossing_p_precise = (lo + hi) / 2
    else:
        zero_crossing_p_precise = None

    print(f"    Werner zero-crossing at p = {zero_crossing_p_precise}")
    if zero_crossing_p_precise is not None:
        print(f"    (1/3 = {1/3:.10f} -- SSA bound for Werner states)")

    return {
        "bell_S_A_given_B": cond_bell,
        "bell_S_AB": s_ab,
        "bell_S_A": s_a,
        "bell_S_B": s_b,
        "pure_sweep_sample": pure_sweep[::10],
        "werner_zero_crossing_p": zero_crossing_p_precise,
        "werner_sweep_sample": werner_sweep[::50],
    }


def test_t5_mi_product_state():
    """T5: Mutual information for product states -- should be exactly 0."""
    print("\n  [T5] Mutual information for product states")

    rng = np.random.default_rng(99)
    mi_values = []
    for _ in range(100):
        # Random 2-qubit product state
        a = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
        rho_a = a @ a.conj().T
        rho_a /= np.trace(rho_a)
        b = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
        rho_b = b @ b.conj().T
        rho_b /= np.trace(rho_b)

        rho_ab = np.kron(rho_a, rho_b)
        s_ab = vn_entropy(rho_ab)
        s_a = vn_entropy(rho_a)
        s_b = vn_entropy(rho_b)
        mi = s_a + s_b - s_ab
        mi_values.append(mi)

    mi_arr = np.array(mi_values)
    print(f"    MI stats over 100 product states:")
    print(f"    mean: {np.mean(mi_arr):.2e}")
    print(f"    max |MI|: {np.max(np.abs(mi_arr)):.2e}")
    print(f"    std: {np.std(mi_arr):.2e}")
    print(f"    Any |MI| > 1e-10? {np.any(np.abs(mi_arr) > 1e-10)}")

    return {
        "mi_mean": float(np.mean(mi_arr)),
        "mi_max_abs": float(np.max(np.abs(mi_arr))),
        "mi_std": float(np.std(mi_arr)),
        "mi_exceeds_1e10": bool(np.any(np.abs(mi_arr) > 1e-10)),
        "mi_exceeds_1e12": bool(np.any(np.abs(mi_arr) > 1e-12)),
    }


def test_t6_tsallis_to_min_entropy():
    """T6: Tsallis q -> inf convergence to min-entropy."""
    print("\n  [T6] Tsallis q -> inf convergence to min-entropy")

    rng = np.random.default_rng(77)
    test_states = {
        "max_mixed_4": make_max_mixed(4),
        "pure_4": make_pure_state(4),
        "rank2_4": np.diag([0.7, 0.3, 0, 0]).astype(complex),
        "random_4": None,
    }
    a = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
    rho_rand = a @ a.conj().T
    rho_rand /= np.trace(rho_rand)
    test_states["random_4"] = rho_rand

    qs = [2, 5, 10, 20, 50, 100, 500, 1000, 5000]
    results = {}

    for name, rho in test_states.items():
        s_min = min_entropy(rho)
        convergence = []
        for q in qs:
            # Tsallis in natural units; convert Renyi to compare
            s_renyi_q = renyi_entropy(rho, q)
            convergence.append({
                "q": q,
                "renyi_q": s_renyi_q,
                "error_vs_min": abs(s_renyi_q - s_min) if not np.isnan(s_renyi_q) else None,
            })
        # At what q does |error| < 1e-3?
        converged_q = None
        for c in convergence:
            if c["error_vs_min"] is not None and c["error_vs_min"] < 1e-3:
                converged_q = c["q"]
                break

        results[name] = {
            "min_entropy": s_min,
            "convergence": convergence,
            "converged_at_q": converged_q,
        }
        print(f"    {name}: min_entropy={s_min:.4f}, converges at q={converged_q}")

    return results


def test_t7_linear_entropy_dimensions():
    """T7: Linear entropy for various dimensions and states."""
    print("\n  [T7] Linear entropy for d=2 and d=100")

    results = {}
    for d in [2, 4, 10, 50, 100]:
        le_pure = linear_entropy(make_pure_state(d))
        le_mixed = linear_entropy(make_max_mixed(d))
        expected_mixed = (d - 1) / d
        error_pure = abs(le_pure)
        error_mixed = abs(le_mixed - expected_mixed)
        results[f"d={d}"] = {
            "pure": le_pure,
            "max_mixed": le_mixed,
            "expected_max_mixed": expected_mixed,
            "error_pure": error_pure,
            "error_max_mixed": error_mixed,
        }
        print(f"    d={d}: pure={le_pure:.2e} (expect 0), "
              f"max_mixed={le_mixed:.6f} (expect {expected_mixed:.6f}), "
              f"error={error_mixed:.2e}")

    return results


def test_t8_rank_boundary():
    """T8: All entropies on rank-1 to rank-2 boundary."""
    print("\n  [T8] Rank-1 -> rank-2 boundary transition")

    d = 4
    epsilons = np.logspace(-15, -1, 60)
    sweep = []
    for eps in epsilons:
        # rank-1 + epsilon weight on second eigenvalue
        evals = np.array([1.0 - eps, eps, 0, 0])
        rho = np.diag(evals).astype(complex)

        s_vn = vn_entropy(rho)
        s_lin = linear_entropy(rho)
        s_r2 = renyi_entropy(rho, 2)
        s_r0 = renyi_entropy(rho, 0)
        s_tsa = tsallis_entropy(rho, 2)
        s_min = min_entropy(rho)

        sweep.append({
            "epsilon": float(eps),
            "rank": int(np.sum(evals > 1e-15)),
            "vn": s_vn,
            "linear": s_lin,
            "renyi_2": s_r2,
            "renyi_0": s_r0,
            "tsallis_2": s_tsa,
            "min_entropy": s_min,
        })

    # Find where Renyi-0 jumps (rank transition)
    rank_jump_eps = None
    for i in range(1, len(sweep)):
        if sweep[i]["renyi_0"] != sweep[i - 1]["renyi_0"]:
            rank_jump_eps = sweep[i]["epsilon"]
            break

    print(f"    Renyi-0 rank jump at epsilon ~ {rank_jump_eps}")
    print(f"    At eps=1e-15: vN={sweep[0]['vn']:.2e}, Renyi-0={sweep[0]['renyi_0']:.4f}")
    print(f"    At eps=1e-1: vN={sweep[-1]['vn']:.4f}, Renyi-0={sweep[-1]['renyi_0']:.4f}")

    return {
        "rank_jump_epsilon": rank_jump_eps,
        "sweep_sample": sweep[::6],  # every 6th
    }


def test_t9_non_density_matrix():
    """T9: What happens with non-density-matrices?"""
    print("\n  [T9] Entropy of non-density-matrices")

    cases = {}

    # Case A: Not positive semi-definite (negative eigenvalue)
    rho_neg = np.array([[1.5, 0], [0, -0.5]], dtype=complex)
    try:
        s = vn_entropy(rho_neg)
        cases["negative_eigenvalue"] = {"vn": s, "error": None,
                                        "note": "Gave answer despite invalid input"}
    except Exception as e:
        cases["negative_eigenvalue"] = {"vn": None, "error": str(e)}

    # Case B: Not trace-1
    rho_trace2 = np.eye(2, dtype=complex)  # trace = 2
    try:
        s = vn_entropy(rho_trace2)
        cases["trace_2"] = {"vn": s, "error": None}
    except Exception as e:
        cases["trace_2"] = {"vn": None, "error": str(e)}

    # Case C: Not hermitian
    rho_nonherm = np.array([[0.5, 0.3], [0.1, 0.5]], dtype=complex)
    try:
        s = vn_entropy(rho_nonherm)
        cases["non_hermitian"] = {"vn": s, "error": None}
    except Exception as e:
        cases["non_hermitian"] = {"vn": None, "error": str(e)}

    # Case D: All zeros
    rho_zero = np.zeros((2, 2), dtype=complex)
    try:
        s = vn_entropy(rho_zero)
        cases["zero_matrix"] = {"vn": s, "error": None}
    except Exception as e:
        cases["zero_matrix"] = {"vn": None, "error": str(e)}

    # Case E: Identity (trace = d, not 1)
    rho_id4 = np.eye(4, dtype=complex)
    try:
        s = vn_entropy(rho_id4)
        cases["identity_4x4"] = {"vn": s, "error": None,
                                 "note": "Should be 2.0 only if normalised to I/4"}
    except Exception as e:
        cases["identity_4x4"] = {"vn": None, "error": str(e)}

    # Case F: Complex eigenvalues (not hermitian)
    rho_complex = np.array([[0, -1], [1, 0]], dtype=complex)
    try:
        s = vn_entropy(rho_complex)
        cases["complex_eigenvalues"] = {"vn": s, "error": None}
    except Exception as e:
        cases["complex_eigenvalues"] = {"vn": None, "error": str(e)}

    for name, result in cases.items():
        print(f"    {name}: vn={result.get('vn')}, error={result.get('error')}")

    return cases


def test_t10_shannon_vs_vn():
    """T10: When do Shannon (diagonal) and vN disagree maximally?"""
    print("\n  [T10] Shannon vs vN: maximal disagreement")

    rng = np.random.default_rng(123)

    # For a density matrix, Shannon(diag) and vN differ when off-diagonals
    # carry information.  Maximum disagreement: pure state with maximal
    # off-diagonal coherence but uniform diagonal.
    #
    # |+> = (|0>+|1>)/sqrt(2): diag = [0.5, 0.5] -> Shannon = 1 bit
    # But vN = 0 (pure state).
    rho_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
    s_vn_plus = vn_entropy(rho_plus)
    s_sh_plus = shannon_entropy(np.diag(np.real(rho_plus)))

    # Survey random states for max disagreement
    max_disagree = 0
    max_disagree_state = None
    disagreements = []
    for _ in range(1000):
        # Random pure state in d=4
        psi = rng.normal(size=4) + 1j * rng.normal(size=4)
        psi /= np.linalg.norm(psi)
        rho = np.outer(psi, psi.conj())
        s_vn = vn_entropy(rho)
        s_sh = shannon_entropy(np.diag(np.real(rho)))
        diff = abs(s_sh - s_vn)
        disagreements.append(diff)
        if diff > max_disagree:
            max_disagree = diff
            max_disagree_state = {
                "diagonal": np.real(np.diag(rho)).tolist(),
                "shannon": s_sh,
                "vn": s_vn,
            }

    # Also test: random mixed states
    mixed_disagree = []
    for _ in range(1000):
        a = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
        rho = a @ a.conj().T
        rho /= np.trace(rho)
        s_vn = vn_entropy(rho)
        s_sh = shannon_entropy(np.diag(np.real(rho)))
        mixed_disagree.append(abs(s_sh - s_vn))

    print(f"    |+> state: Shannon={s_sh_plus:.4f}, vN={s_vn_plus:.4f}, diff={abs(s_sh_plus - s_vn_plus):.4f}")
    print(f"    Max disagreement (pure d=4): {max_disagree:.4f}")
    print(f"    Max disagreement (mixed d=4): {max(mixed_disagree):.4f}")
    print(f"    Mean disagreement (pure): {np.mean(disagreements):.4f}")
    print(f"    Mean disagreement (mixed): {np.mean(mixed_disagree):.4f}")

    return {
        "plus_state_shannon": s_sh_plus,
        "plus_state_vn": s_vn_plus,
        "plus_state_disagreement": abs(s_sh_plus - s_vn_plus),
        "max_disagreement_pure_d4": max_disagree,
        "max_disagreement_state": max_disagree_state,
        "mean_disagreement_pure_d4": float(np.mean(disagreements)),
        "max_disagreement_mixed_d4": float(max(mixed_disagree)),
        "mean_disagreement_mixed_d4": float(np.mean(mixed_disagree)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_all():
    print("=" * 72)
    print("NEGATIVE ENTROPY BOUNDARIES BATTERY")
    print("  Pure numpy/scipy -- no engine dependency")
    print("=" * 72)

    all_results = {}
    all_results["T1_vn_pure_noise"] = test_t1_vn_pure_state_noise()
    all_results["T2_renyi_edge_cases"] = test_t2_renyi_edge_cases()
    all_results["T3_relative_entropy_support"] = test_t3_relative_entropy_support()
    all_results["T4_conditional_entropy"] = test_t4_conditional_entropy()
    all_results["T5_mi_product_state"] = test_t5_mi_product_state()
    all_results["T6_tsallis_min_entropy"] = test_t6_tsallis_to_min_entropy()
    all_results["T7_linear_entropy_dims"] = test_t7_linear_entropy_dimensions()
    all_results["T8_rank_boundary"] = test_t8_rank_boundary()
    all_results["T9_non_density_matrix"] = test_t9_non_density_matrix()
    all_results["T10_shannon_vs_vn"] = test_t10_shannon_vs_vn()

    # Summary
    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)

    findings = [
        f"T1: Eigenvalue noise at ~{all_results['T1_vn_pure_noise'].get('crossover_noise_level', '?')} "
        f"makes vN entropy non-negligible",
        f"T2: Renyi alpha<0 gives finite but meaningless values; "
        f"alpha=0 on zero matrix = {all_results['T2_renyi_edge_cases']['alpha_0_zero_matrix']}",
        f"T3: D(rho||sigma) = {all_results['T3_relative_entropy_support']['support_violation_inf']} "
        f"when support violated (expect +inf)",
        f"T4: Bell S(A|B) = {all_results['T4_conditional_entropy']['bell_S_A_given_B']:.4f} "
        f"(expect -1.0), Werner zero crossing at p={all_results['T4_conditional_entropy']['werner_zero_crossing_p']}",
        f"T5: Product state MI max|MI| = {all_results['T5_mi_product_state']['mi_max_abs']:.2e}",
        f"T6: Tsallis->min-entropy convergence q varies by state",
        f"T7: Linear entropy d=100 pure = {all_results['T7_linear_entropy_dims']['d=100']['pure']:.2e}",
        "T8: Renyi-0 rank jump at eps ~ {} (None = no transition in sweep)".format(
            all_results['T8_rank_boundary']['rank_jump_epsilon']),
        f"T9: Non-density-matrix inputs silently accepted by eigvalsh",
        f"T10: Shannon vs vN max disagreement (pure d=4) = "
        f"{all_results['T10_shannon_vs_vn']['max_disagreement_pure_d4']:.4f} bits",
    ]
    for f in findings:
        print(f"    {f}")

    # Save
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "negative_entropy_boundaries_results.json")

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "name": "Negative_Entropy_Boundaries_Battery",
        "results": all_results,
        "findings": findings,
    }

    with open(outpath, "w") as fh:
        json.dump(payload, fh, indent=2, default=str)

    print(f"\n  Results saved: {outpath}")
    return all_results


if __name__ == "__main__":
    run_all()
