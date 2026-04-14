#!/usr/bin/env python3
"""
Pure-lego discrete quantum walks on graphs.
No engine. numpy only.

1. Coined quantum walk on a line (n=20 sites, 100 steps, start at center)
   - Coin: Hadamard on C^2
   - Walk operator: W = S . (C x I)  where S is conditional shift
   - Verify: distribution is NOT Gaussian -- peaks at edges, linear spread

2. Continuous-time quantum walk via H = adjacency matrix, U(t) = exp(-iHt)
   - Cycle graph (n=8): verify periodicity
   - Complete graph: verify uniform mixing

3. Compare: quantum walk spread vs classical random walk spread
   - Quantum advantage = quadratic speedup in hitting time
"""

import json
import numpy as np
from pathlib import Path
classification = "classical_baseline"  # auto-backfill

RESULTS_DIR = Path(__file__).parent / "a2_state" / "sim_results"


# =============================================================================
# 1. COINED QUANTUM WALK ON A LINE
# =============================================================================

def coined_walk_on_line(n_sites=20, n_steps=100):
    """
    Coined quantum walk on a 1D line with n_sites positions.
    Hilbert space: C^2 (coin) x C^n (position).
    State vector dimension: 2 * n_sites.

    Coin states: |0> = left, |1> = right.
    Hadamard coin: H = (1/sqrt2) [[1,1],[1,-1]]
    Shift: S|0,x> = |0, x-1>,  S|1,x> = |1, x+1>  (absorbing boundaries)
    """
    dim = 2 * n_sites

    # Initial state: coin=|0>+|1> (equal superposition), position=center
    center = n_sites // 2
    psi = np.zeros(dim, dtype=complex)
    # |0, center> + i|1, center>  (asymmetric coin to get symmetric output)
    psi[0 * n_sites + center] = 1.0 / np.sqrt(2)
    psi[1 * n_sites + center] = 1j / np.sqrt(2)

    # Hadamard coin operator (acts on coin space)
    H_coin = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)

    # Build full coin operator: H_coin x I_position
    coin_op = np.kron(H_coin, np.eye(n_sites, dtype=complex))

    # Build shift operator S
    # S|0,x> = |0, x-1>,  S|1,x> = |1, x+1>
    shift_op = np.zeros((dim, dim), dtype=complex)
    for x in range(n_sites):
        # Left-mover: coin=0, shift x -> x-1
        if x - 1 >= 0:
            shift_op[0 * n_sites + (x - 1), 0 * n_sites + x] = 1.0
        # else: absorbed at boundary (no wrap)

        # Right-mover: coin=1, shift x -> x+1
        if x + 1 < n_sites:
            shift_op[1 * n_sites + (x + 1), 1 * n_sites + x] = 1.0
        # else: absorbed at boundary

    # Walk operator W = S . (C x I)
    walk_op = shift_op @ coin_op

    # Record probability distribution at each step
    prob_history = []
    for step in range(n_steps + 1):
        # Probability at each site = sum over coin states
        prob = np.zeros(n_sites)
        for c in range(2):
            prob += np.abs(psi[c * n_sites:(c + 1) * n_sites]) ** 2
        prob_history.append(prob.tolist())

        if step < n_steps:
            psi = walk_op @ psi

    final_prob = prob_history[-1]
    return final_prob, prob_history


def verify_non_gaussian(prob, n_sites=20):
    """
    Verify the quantum walk distribution is NOT Gaussian.
    Classical random walk -> Gaussian (bell curve, single central peak).
    Quantum walk -> peaks near the edges of the spread, dip in center.
    """
    center = n_sites // 2
    positions = np.arange(n_sites)

    # Compute moments
    mean = np.sum(positions * prob)
    variance = np.sum((positions - mean) ** 2 * prob)
    std_dev = np.sqrt(variance)

    # Check for bimodal structure: compare center prob to wing probs
    # Find the peak positions
    peak_idx = np.argsort(prob)[::-1]
    top_peaks = peak_idx[:4]

    # In a Gaussian, the peak should be at or very near the center
    # In a quantum walk, the peaks should be away from center
    peak_distances = np.abs(top_peaks - center)
    avg_peak_distance = np.mean(peak_distances)

    # Classical Gaussian: kurtosis ~ 3, quantum walk: lower kurtosis (flatter/bimodal)
    if std_dev > 0:
        kurtosis = np.sum((positions - mean) ** 4 * prob) / (std_dev ** 4)
    else:
        kurtosis = 0.0

    # Quantum walk spread is linear in t, classical is sqrt(t)
    # After 100 steps, quantum std_dev >> classical std_dev ~ sqrt(100) = 10
    # (but bounded by n_sites here)

    is_non_gaussian = avg_peak_distance > 1.0  # peaks not at center

    return {
        "mean": float(mean),
        "variance": float(variance),
        "std_dev": float(std_dev),
        "kurtosis": float(kurtosis),
        "gaussian_kurtosis": 3.0,
        "top_peak_positions": top_peaks.tolist(),
        "avg_peak_distance_from_center": float(avg_peak_distance),
        "is_non_gaussian": bool(is_non_gaussian),
        "verdict": "PASS: distribution is non-Gaussian (quantum walk signature)"
        if is_non_gaussian
        else "FAIL: distribution looks Gaussian",
    }


def classical_random_walk_on_line(n_sites=20, n_steps=100):
    """
    Classical random walk: probability distribution via transition matrix.
    """
    # Transition matrix: at each site, go left or right with prob 0.5
    T = np.zeros((n_sites, n_sites))
    for x in range(n_sites):
        if x - 1 >= 0:
            T[x - 1, x] += 0.5
        if x + 1 < n_sites:
            T[x + 1, x] += 0.5
        # absorbing boundaries: probability lost at edges

    center = n_sites // 2
    prob = np.zeros(n_sites)
    prob[center] = 1.0

    for _ in range(n_steps):
        prob = T @ prob

    return prob


# =============================================================================
# 2. CONTINUOUS-TIME QUANTUM WALK
# =============================================================================

def matrix_exp_neg_i(H, t):
    """Compute U(t) = exp(-i H t) via eigendecomposition."""
    eigenvalues, eigenvectors = np.linalg.eigh(H)
    # U = V . diag(exp(-i lambda t)) . V^dag
    phases = np.exp(-1j * eigenvalues * t)
    return eigenvectors @ np.diag(phases) @ eigenvectors.conj().T


def ctqw_on_cycle(n=8, t_max=50, dt=0.5):
    """
    Continuous-time quantum walk on cycle graph C_n.
    H = adjacency matrix of cycle.
    Verify: periodicity (return probability oscillates).
    """
    # Adjacency matrix of cycle
    H = np.zeros((n, n), dtype=float)
    for i in range(n):
        H[i, (i + 1) % n] = 1.0
        H[(i + 1) % n, i] = 1.0

    # Initial state: localized at node 0
    psi0 = np.zeros(n, dtype=complex)
    psi0[0] = 1.0

    times = np.arange(0, t_max + dt, dt)
    return_probs = []

    for t in times:
        U = matrix_exp_neg_i(H, t)
        psi_t = U @ psi0
        p_return = float(np.abs(psi_t[0]) ** 2)
        return_probs.append(p_return)

    # Check periodicity: does return probability come back near 1?
    return_probs_arr = np.array(return_probs)
    # Find local maxima
    local_maxima_indices = []
    for i in range(1, len(return_probs_arr) - 1):
        if (return_probs_arr[i] > return_probs_arr[i - 1] and
                return_probs_arr[i] > return_probs_arr[i + 1] and
                return_probs_arr[i] > 0.5):
            local_maxima_indices.append(i)

    has_periodicity = len(local_maxima_indices) >= 2

    # Estimate period from maxima
    if len(local_maxima_indices) >= 2:
        periods = np.diff([times[i] for i in local_maxima_indices])
        avg_period = float(np.mean(periods))
    else:
        avg_period = None

    return {
        "graph": f"cycle_C{n}",
        "t_max": t_max,
        "n_time_points": len(times),
        "return_prob_samples": {
            f"t={float(times[i]):.1f}": float(return_probs[i])
            for i in range(0, len(times), max(1, len(times) // 10))
        },
        "local_maxima_times": [float(times[i]) for i in local_maxima_indices],
        "local_maxima_values": [float(return_probs_arr[i]) for i in local_maxima_indices],
        "has_periodicity": bool(has_periodicity),
        "estimated_period": avg_period,
        "verdict": "PASS: periodic return probability observed"
        if has_periodicity
        else "FAIL: no clear periodicity detected",
    }


def ctqw_on_complete_graph(n_primary=4, n_secondary=8, t_max=20, dt=0.05):
    """
    Continuous-time quantum walk on complete graph K_n.
    H = adjacency matrix = J - I.

    Known result: K_4 achieves exact instantaneous uniform mixing
    (all nodes reach probability 1/4 simultaneously). K_n for n>4
    does NOT achieve exact uniform mixing, but non-initial nodes
    are always symmetric and reach max prob = 4/n^2.

    We verify on K_4: exact uniform mixing (all probs = 0.25 at some t).
    We also show K_8 symmetry + bounded mixing as comparison.
    """
    results = {}

    for n in [n_primary, n_secondary]:
        H = np.ones((n, n), dtype=float) - np.eye(n, dtype=float)
        psi0 = np.zeros(n, dtype=complex)
        psi0[0] = 1.0

        times = np.arange(0, t_max + dt, dt)

        best_l2 = float("inf")
        best_t = 0.0
        best_probs = None
        max_non_initial = 0.0
        symmetry_holds = True

        for t in times:
            U = matrix_exp_neg_i(H, t)
            psi_t = U @ psi0
            probs = np.abs(psi_t) ** 2

            non_initial = probs[1:]
            if np.max(non_initial) - np.min(non_initial) > 1e-10:
                symmetry_holds = False
            max_non_initial = max(max_non_initial, float(np.max(non_initial)))

            uniform = np.ones(n) / n
            l2 = float(np.linalg.norm(probs - uniform))
            if l2 < best_l2:
                best_l2 = l2
                best_t = float(t)
                best_probs = probs.copy()

        achieves_uniform = best_l2 < 0.01  # very close to uniform

        results[f"K{n}"] = {
            "n_nodes": n,
            "target_uniform_prob": 1.0 / n,
            "symmetry_among_non_initial_nodes": bool(symmetry_holds),
            "max_non_initial_node_prob": float(max_non_initial),
            "best_mixing_time": best_t,
            "best_l2_from_uniform": best_l2,
            "probs_at_best_mixing": best_probs.tolist() if best_probs is not None else [],
            "achieves_uniform_mixing": bool(achieves_uniform),
        }

    # Primary test: K_4 must achieve uniform mixing
    k4_pass = results["K4"]["achieves_uniform_mixing"]
    # Secondary: K_8 must show symmetry (known: does NOT achieve uniform)
    k8_symmetry = results["K8"]["symmetry_among_non_initial_nodes"]

    return {
        "graph": "complete_graph_suite",
        "K4_result": results["K4"],
        "K8_result": results["K8"],
        "K4_uniform_mixing": bool(k4_pass),
        "K8_symmetry_confirmed": bool(k8_symmetry),
        "K8_note": (
            "K_8 does NOT achieve exact uniform mixing (known result for n>4). "
            f"Max non-initial prob = {results['K8']['max_non_initial_node_prob']:.6f} "
            f"vs target 1/8 = 0.125. This equals 4/n^2 = {4/64:.6f} as expected."
        ),
        "verdict": (
            "PASS: K4 achieves exact uniform mixing, K8 shows correct symmetry"
            if k4_pass and k8_symmetry
            else "FAIL: unexpected mixing behavior"
        ),
    }


# =============================================================================
# 3. SPREAD COMPARISON: QUANTUM vs CLASSICAL
# =============================================================================

def spread_comparison(max_steps=100, n_sites=201):
    """
    Compare the spread (std dev) of quantum walk vs classical walk
    as a function of number of steps.
    Quantum: std ~ t (linear)
    Classical: std ~ sqrt(t)
    """
    center = n_sites // 2
    positions = np.arange(n_sites)

    # --- Classical setup ---
    T_classical = np.zeros((n_sites, n_sites))
    for x in range(n_sites):
        if x - 1 >= 0:
            T_classical[x - 1, x] += 0.5
        if x + 1 < n_sites:
            T_classical[x + 1, x] += 0.5

    prob_classical = np.zeros(n_sites)
    prob_classical[center] = 1.0

    # --- Quantum setup ---
    dim = 2 * n_sites
    H_coin = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    coin_op = np.kron(H_coin, np.eye(n_sites, dtype=complex))

    shift_op = np.zeros((dim, dim), dtype=complex)
    for x in range(n_sites):
        if x - 1 >= 0:
            shift_op[0 * n_sites + (x - 1), 0 * n_sites + x] = 1.0
        if x + 1 < n_sites:
            shift_op[1 * n_sites + (x + 1), 1 * n_sites + x] = 1.0

    walk_op = shift_op @ coin_op

    psi = np.zeros(dim, dtype=complex)
    psi[0 * n_sites + center] = 1.0 / np.sqrt(2)
    psi[1 * n_sites + center] = 1j / np.sqrt(2)

    # --- Run both ---
    sample_steps = [10, 20, 30, 50, 70, 100]
    results = {}

    for step in range(max_steps + 1):
        if step in sample_steps:
            # Classical std
            total_c = np.sum(prob_classical)
            if total_c > 1e-12:
                p_c = prob_classical / total_c
                mean_c = np.sum(positions * p_c)
                std_c = np.sqrt(np.sum((positions - mean_c) ** 2 * p_c))
            else:
                std_c = 0.0

            # Quantum std
            prob_q = np.zeros(n_sites)
            for c in range(2):
                prob_q += np.abs(psi[c * n_sites:(c + 1) * n_sites]) ** 2
            total_q = np.sum(prob_q)
            if total_q > 1e-12:
                p_q = prob_q / total_q
                mean_q = np.sum(positions * p_q)
                std_q = np.sqrt(np.sum((positions - mean_q) ** 2 * p_q))
            else:
                std_q = 0.0

            results[step] = {
                "classical_std": float(std_c),
                "quantum_std": float(std_q),
                "ratio_q_over_c": float(std_q / std_c) if std_c > 1e-12 else None,
                "expected_classical_sqrt_t": float(np.sqrt(step)),
            }

        if step < max_steps:
            prob_classical = T_classical @ prob_classical
            psi = walk_op @ psi

    # Verify quantum advantage: ratio should grow (linear / sqrt = sqrt(t))
    ratios = [
        v["ratio_q_over_c"]
        for v in results.values()
        if v["ratio_q_over_c"] is not None
    ]
    ratio_increasing = all(
        ratios[i + 1] > ratios[i] * 0.9  # allow small noise
        for i in range(len(ratios) - 1)
    )

    return {
        "spread_by_step": results,
        "ratio_trend_increasing": bool(ratio_increasing),
        "quantum_advantage_explanation":
            "Quantum walk spread grows linearly in t, classical grows as sqrt(t). "
            "The ratio quantum_std / classical_std grows as ~sqrt(t), "
            "demonstrating quadratic speedup in spatial spread (hitting time).",
        "verdict": "PASS: quantum walk shows quadratic speedup over classical"
        if ratio_increasing
        else "FAIL: speedup trend not detected",
    }


# =============================================================================
# 4. HITTING TIME COMPARISON
# =============================================================================

def hitting_time_comparison(n_sites=20):
    """
    Compare hitting times: steps needed for probability to reach
    the opposite end of a line graph.
    Classical: O(n^2), Quantum: O(n).

    Uses reflecting boundaries so probability is conserved and the
    classical walk actually reaches the far end.
    """
    center = 0  # start at left
    target = n_sites - 1  # hit right end
    threshold = 0.005  # probability threshold to count as "hit"

    # --- Classical (reflecting boundaries) ---
    T_classical = np.zeros((n_sites, n_sites))
    for x in range(n_sites):
        if x == 0:
            # reflect: can only go right
            T_classical[1, 0] = 0.5
            T_classical[0, 0] = 0.5  # stay with prob 0.5
        elif x == n_sites - 1:
            # reflect: can only go left
            T_classical[n_sites - 2, n_sites - 1] = 0.5
            T_classical[n_sites - 1, n_sites - 1] = 0.5
        else:
            T_classical[x - 1, x] = 0.5
            T_classical[x + 1, x] = 0.5

    prob_c = np.zeros(n_sites)
    prob_c[center] = 1.0
    classical_hit = None
    for step in range(1, 5000):
        prob_c = T_classical @ prob_c
        if prob_c[target] >= threshold:
            classical_hit = step
            break

    # --- Quantum (reflecting: left-movers at 0 become right-movers, etc.) ---
    dim = 2 * n_sites
    H_coin = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    coin_op = np.kron(H_coin, np.eye(n_sites, dtype=complex))

    shift_op = np.zeros((dim, dim), dtype=complex)
    for x in range(n_sites):
        # Left-mover (coin=0): x -> x-1
        if x - 1 >= 0:
            shift_op[0 * n_sites + (x - 1), 0 * n_sites + x] = 1.0
        else:
            # Reflect: left-mover at 0 becomes right-mover at 0
            shift_op[1 * n_sites + 0, 0 * n_sites + 0] = 1.0

        # Right-mover (coin=1): x -> x+1
        if x + 1 < n_sites:
            shift_op[1 * n_sites + (x + 1), 1 * n_sites + x] = 1.0
        else:
            # Reflect: right-mover at n-1 becomes left-mover at n-1
            shift_op[0 * n_sites + (n_sites - 1), 1 * n_sites + (n_sites - 1)] = 1.0

    walk_op = shift_op @ coin_op

    psi = np.zeros(dim, dtype=complex)
    psi[1 * n_sites + center] = 1.0  # right-moving from left end

    quantum_hit = None
    for step in range(1, 5000):
        psi = walk_op @ psi
        prob_q = (np.abs(psi[0 * n_sites + target]) ** 2 +
                  np.abs(psi[1 * n_sites + target]) ** 2)
        if prob_q >= threshold:
            quantum_hit = step
            break

    speedup = None
    if classical_hit and quantum_hit and quantum_hit > 0:
        speedup = classical_hit / quantum_hit

    return {
        "n_sites": n_sites,
        "start": center,
        "target": target,
        "threshold": threshold,
        "classical_hitting_step": classical_hit,
        "quantum_hitting_step": quantum_hit,
        "speedup_ratio": float(speedup) if speedup else None,
        "expected_scaling": "classical O(n^2) vs quantum O(n)",
        "verdict": (
            f"PASS: quantum hits {speedup:.1f}x faster"
            if speedup and speedup > 1.5
            else "MARGINAL or FAIL: speedup not clearly observed"
        ),
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    results = {}

    # 1. Coined walk on line
    print("Running coined quantum walk on line (n=20, 100 steps)...")
    final_prob, prob_history = coined_walk_on_line(n_sites=20, n_steps=100)
    gaussian_check = verify_non_gaussian(final_prob, n_sites=20)
    results["coined_walk_line"] = {
        "n_sites": 20,
        "n_steps": 100,
        "final_probability_distribution": final_prob,
        "non_gaussian_verification": gaussian_check,
    }
    print(f"  -> {gaussian_check['verdict']}")

    # 2a. CTQW on cycle
    print("Running continuous-time QW on cycle C8...")
    cycle_result = ctqw_on_cycle(n=8, t_max=50, dt=0.5)
    results["ctqw_cycle_C8"] = cycle_result
    print(f"  -> {cycle_result['verdict']}")

    # 2b. CTQW on complete graphs (K4 + K8)
    print("Running continuous-time QW on complete graphs K4, K8...")
    complete_result = ctqw_on_complete_graph(n_primary=4, n_secondary=8, t_max=20, dt=0.05)
    results["ctqw_complete_graph"] = complete_result
    print(f"  -> {complete_result['verdict']}")

    # 3. Spread comparison
    print("Running spread comparison (quantum vs classical, up to 100 steps)...")
    spread_result = spread_comparison(max_steps=100, n_sites=201)
    results["spread_comparison"] = spread_result
    print(f"  -> {spread_result['verdict']}")

    # 4. Hitting time
    print("Running hitting time comparison (n=20 line)...")
    hitting_result = hitting_time_comparison(n_sites=20)
    results["hitting_time"] = hitting_result
    print(f"  -> {hitting_result['verdict']}")

    # Summary
    verdicts = [
        gaussian_check["verdict"],
        cycle_result["verdict"],
        complete_result["verdict"],
        spread_result["verdict"],
        hitting_result["verdict"],
    ]
    all_pass = all("PASS" in v for v in verdicts)
    results["summary"] = {
        "all_pass": all_pass,
        "verdicts": verdicts,
        "description": (
            "Pure-lego quantum walks on graphs. "
            "Coined discrete-time walk on line, "
            "continuous-time walks on cycle and complete graph, "
            "spread comparison, and hitting time comparison."
        ),
    }

    # Write results
    out_path = RESULTS_DIR / "pure_lego_quantum_walks_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {out_path}")
    print(f"Overall: {'ALL PASS' if all_pass else 'SOME FAILURES'}")

    return results


if __name__ == "__main__":
    main()
