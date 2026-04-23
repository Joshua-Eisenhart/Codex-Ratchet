"""Classical baseline: IGT nested win-lose cycle.

Mirrors the IGT (Infinite Game Theory) framework's self-similar nested-cycle
motif with a classical analog: rock-paper-scissors tournament as a directed
cycle graph. We verify the payoff matrix is antisymmetric, has zero trace, and
that no pure strategy dominates (Nash equilibrium is uniform mixed).

scope_note: classical_baseline mirror of IGT nested cycles
(OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md IGT framework).
"""
import numpy as np
from _common import write_results


def rps_payoff():
    return np.array([
        [0, -1,  1],
        [1,  0, -1],
        [-1, 1,  0],
    ], dtype=float)


def run_positive():
    M = rps_payoff()
    antisym = np.allclose(M, -M.T)
    tr = float(np.trace(M))
    # Uniform strategy expected payoff vs any pure = 0
    uni = np.ones(3) / 3.0
    payoffs = M @ uni
    return {
        "antisymmetric": {"pass": bool(antisym)},
        "zero_trace": {"trace": tr, "pass": tr == 0},
        "uniform_is_equalizer": {"payoffs": payoffs.tolist(), "pass": bool(np.allclose(payoffs, 0.0))},
    }


def run_negative():
    # A payoff matrix with a dominant row violates the cycle structure.
    M = np.array([[0, 1, 1], [-1, 0, 1], [-1, -1, 0]], dtype=float)
    uni = np.ones(3) / 3.0
    payoffs = M @ uni
    dominated = bool(np.all(payoffs[0] >= payoffs))
    return {"dominant_strategy_breaks_cycle": {"payoffs": payoffs.tolist(), "pass": dominated}}


def run_boundary():
    # Two-player zero game: degenerate cycle of length 2.
    M = np.array([[0, -1], [1, 0]], dtype=float)
    return {"2cycle_antisym": {"pass": bool(np.allclose(M, -M.T))}}


if __name__ == "__main__":
    write_results(
        "sim_classical_igt_nested_win_lose_cycle",
        "classical_baseline mirror of IGT nested win-lose cycle (OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_igt_nested_win_lose_cycle_results.json",
    )
