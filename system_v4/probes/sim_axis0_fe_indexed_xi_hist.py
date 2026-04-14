#!/usr/bin/env python3
"""
Axis 0 Fe-Indexed Xi_hist Probe
=================================
Tests whether indexing the Xi_hist construction to Fe-transition events
and using a 7-step compression window produces higher MI/Ic than
the Phase 4 full-trajectory winner.

Motivation (AXIS0_EC3_OPERATOR_COARISING_NOTE.md):
  - ga0 and MI co-arise at every step; peak at Fe-transition events
  - Fe steps carry MI=1.932 vs 1.750 for non-Fe steps (~10% higher)
  - T1 backward MI asymmetry peaks at lag=7 (compression horizon)
  - lag=4 dip confirms one EC-3 cycle = 4 steps; horizon = 1.75 cycles = 7 steps

Three bridge constructions tested against Phase 4 baseline:

  A — Phase 4 winner (baseline)
      cross_s1_symmetric_retro: full 32-step trajectory,
      exponential attractor-proximity weighting over all 31 pairs.
      MI=1.539 from prior campaign; recomputed here for direct comparison.

  B — Fe-indexed 7-step window
      For each of the 8 Fe-transition steps in a 32-step trajectory:
        take the 7-step window [t_Fe-6 .. t_Fe]
        build cross-s1 symmetric bridge within the window
        weight by attractor-proximity within the window
      Average across 8 Fe windows.

  C — Fe-transition pairs only
      Only use pairs (t, t+1) where step t+1 is a Fe-transition.
      These 8 pairs capture the Ti→Fe co-arising event directly.
      Weight by Fe-step MI magnitude.

  D — 7-step rolling window (lag=7 peak, no Fe indexing)
      For each step t, use the pair (t, t+7) — the maximum-asymmetry lag.
      Tests whether the 7-step lag alone (without Fe indexing) already wins.

FEP framing note:
  The Fe step is NOT the sensory correction in a strict FEP sense.
  Phase5A certified marginal-preserving MI ≈ 0 — the predictive prior
  (Bell bridge) dominates completely. The Fe jump is where the predictive
  model is INSTANTIATED (marginals expand), not where it is corrected by
  sensory data. The entire 4-step cycle is prediction unfolding.
  The 25%/75% Fe/non-Fe split is the ratio of instantiation to exploration,
  not correction to prediction.
"""

from __future__ import annotations
import json, os, sys
from datetime import UTC, datetime
import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this probes Fe-indexed Xi history bridges numerically, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "history-window bridge construction and scoring numerics"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER

TORUS_CONFIGS = [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]
PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL = np.outer(PSI_MINUS, PSI_MINUS.conj())
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
EPS = 1e-12
WINDOW = 7   # compression horizon (steps)


# --------------------------------------------------------------------------- #
# Utilities                                                                    #
# --------------------------------------------------------------------------- #

def vne(rho: np.ndarray) -> float:
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0


def ptr_B(r): return np.trace(r.reshape(2, 2, 2, 2), axis1=1, axis2=3)
def ptr_A(r): return np.trace(r.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def mi_val(rho: np.ndarray) -> float:
    return max(0.0, vne(ptr_B(rho)) + vne(ptr_A(rho)) - vne(rho))


def ic_val(rho: np.ndarray) -> float:
    return vne(ptr_A(rho)) - vne(rho)


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(s @ rho)))
                     for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def lr_asym(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0.01, 0.99))


def cross_s1_symmetric(rho_L1: np.ndarray, rho_R1: np.ndarray,
                        rho_L2: np.ndarray, rho_R2: np.ndarray) -> np.ndarray:
    """Phase 4 winner pattern: symmetric forward+backward Bell bridge."""
    p_f = lr_asym(rho_L1, rho_R2)
    rho_f = _ensure_valid_density((1 - p_f) * np.kron(rho_L1, rho_R2) + p_f * BELL)
    p_b = lr_asym(rho_L2, rho_R1)
    rho_b = _ensure_valid_density((1 - p_b) * np.kron(rho_L2, rho_R1) + p_b * BELL)
    return _ensure_valid_density(0.5 * rho_f + 0.5 * rho_b)


# --------------------------------------------------------------------------- #
# Bridge A — Phase 4 winner (baseline)                                        #
# --------------------------------------------------------------------------- #

def bridge_A_phase4_winner(history: list[dict]) -> np.ndarray:
    """Full trajectory, exponential attractor-proximity weighting."""
    T = len(history)
    states, weights = [], []
    for i in range(T - 1):
        rho = cross_s1_symmetric(
            history[i]["rho_L"], history[i]["rho_R"],
            history[i + 1]["rho_L"], history[i + 1]["rho_R"],
        )
        states.append(rho)
        weights.append(np.exp(-0.1 * (T - 2 - i)))
    weights = np.array(weights) / np.sum(weights)
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


# --------------------------------------------------------------------------- #
# Bridge B — Fe-indexed 7-step window                                         #
# --------------------------------------------------------------------------- #

def bridge_B_fe_indexed(history: list[dict]) -> np.ndarray:
    """
    For each Fe-transition step: build Phase 4 bridge within 7-step window.
    Weight each window by the Fe-step's MI magnitude (Fe steps with higher MI
    carry more information about the compression horizon).
    """
    fe_steps = [i for i, s in enumerate(history) if s["op_name"] == "Fe"]

    window_rhos, window_weights = [], []
    for t_fe in fe_steps:
        win_start = max(0, t_fe - (WINDOW - 1))
        window = history[win_start: t_fe + 1]
        if len(window) < 2:
            continue

        # Fe-step MI magnitude as window weight
        rho_L_fe = history[t_fe]["rho_L"]
        rho_R_fe = history[t_fe]["rho_R"]
        p = lr_asym(rho_L_fe, rho_R_fe)
        fe_rho = _ensure_valid_density((1 - p) * np.kron(rho_L_fe, rho_R_fe) + p * BELL)
        fe_mi = mi_val(fe_rho)

        # Build bridge within window using attractor-proximity weighting
        inner_states, inner_weights = [], []
        W = len(window)
        for j in range(W - 1):
            rho = cross_s1_symmetric(
                window[j]["rho_L"], window[j]["rho_R"],
                window[j + 1]["rho_L"], window[j + 1]["rho_R"],
            )
            inner_states.append(rho)
            inner_weights.append(np.exp(-0.1 * (W - 2 - j)))  # attractor-proximity

        inner_weights = np.array(inner_weights) / np.sum(inner_weights)
        window_rho = _ensure_valid_density(
            sum(w * s for w, s in zip(inner_weights, inner_states))
        )
        window_rhos.append(window_rho)
        window_weights.append(fe_mi)

    window_weights = np.array(window_weights) / np.sum(window_weights)
    return _ensure_valid_density(
        sum(w * s for w, s in zip(window_weights, window_rhos))
    )


# --------------------------------------------------------------------------- #
# Bridge C — Fe-transition pairs only                                         #
# --------------------------------------------------------------------------- #

def bridge_C_fe_pairs_only(history: list[dict]) -> np.ndarray:
    """
    Only Ti→Fe pairs: step i (Ti) and step i+1 (Fe).
    The direct co-arising event. Weight by Fe-step MI magnitude.
    """
    states, weights = [], []
    for i in range(len(history) - 1):
        if history[i + 1]["op_name"] != "Fe":
            continue
        rho = cross_s1_symmetric(
            history[i]["rho_L"], history[i]["rho_R"],
            history[i + 1]["rho_L"], history[i + 1]["rho_R"],
        )
        p = lr_asym(history[i + 1]["rho_L"], history[i + 1]["rho_R"])
        fe_rho = _ensure_valid_density(
            (1 - p) * np.kron(history[i + 1]["rho_L"], history[i + 1]["rho_R"]) + p * BELL
        )
        fe_mi = mi_val(fe_rho)
        states.append(rho)
        weights.append(fe_mi)

    weights = np.array(weights) / np.sum(weights)
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


# --------------------------------------------------------------------------- #
# Bridge D — 7-step lag pairs (no Fe indexing)                               #
# --------------------------------------------------------------------------- #

def bridge_D_lag7_pairs(history: list[dict]) -> np.ndarray:
    """
    Cross-temporal pairs at lag=7 (the compression horizon).
    No Fe indexing — tests whether the lag alone explains the gain.
    Exponential attractor-proximity weighting over all lag=7 pairs.
    """
    T = len(history)
    lag = WINDOW  # 7
    states, weights = [], []
    for i in range(T - lag):
        rho = cross_s1_symmetric(
            history[i]["rho_L"], history[i]["rho_R"],
            history[i + lag]["rho_L"], history[i + lag]["rho_R"],
        )
        states.append(rho)
        weights.append(np.exp(-0.1 * (T - lag - 1 - i)))

    weights = np.array(weights) / np.sum(weights)
    return _ensure_valid_density(sum(w * s for w, s in zip(weights, states)))


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #

def run_torus(engine_type: int, torus_name: str, torus_val: float) -> dict:
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=torus_val)
    final_state = engine.run_cycle(state)
    history = final_state.history

    # Fe step statistics
    fe_indices = [i for i, s in enumerate(history) if s["op_name"] == "Fe"]
    mi_series = []
    for i in range(len(history) - 1):
        p = lr_asym(history[i]["rho_L"], history[i + 1]["rho_R"])
        rho = _ensure_valid_density(
            (1 - p) * np.kron(history[i]["rho_L"], history[i + 1]["rho_R"]) + p * BELL
        )
        mi_series.append(mi_val(rho))

    fe_mi_mean = float(np.mean([mi_series[i] for i in fe_indices if i < len(mi_series)]))
    non_fe_mi_mean = float(np.mean([mi_series[i] for i in range(len(mi_series)) if i not in fe_indices]))

    # Build all four bridges
    rho_A = bridge_A_phase4_winner(history)
    rho_B = bridge_B_fe_indexed(history)
    rho_C = bridge_C_fe_pairs_only(history)
    rho_D = bridge_D_lag7_pairs(history)

    results = {}
    for label, rho in [("A_phase4_winner", rho_A), ("B_fe_indexed", rho_B),
                        ("C_fe_pairs_only", rho_C), ("D_lag7_pairs", rho_D)]:
        results[label] = {
            "mi": mi_val(rho),
            "ic": ic_val(rho),
        }

    winner = max(results, key=lambda k: results[k]["mi"])
    winner_mi = results[winner]["mi"]
    baseline_mi = results["A_phase4_winner"]["mi"]
    gain = winner_mi - baseline_mi

    print(f"  {engine_type}/{torus_name}: "
          f"A={baseline_mi:.4f} "
          f"B={results['B_fe_indexed']['mi']:.4f} "
          f"C={results['C_fe_pairs_only']['mi']:.4f} "
          f"D={results['D_lag7_pairs']['mi']:.4f} "
          f"| winner={winner} gain={gain:+.4f}")

    return {
        "engine_type": engine_type,
        "torus": torus_name,
        "fe_step_count": len(fe_indices),
        "fe_mi_mean": fe_mi_mean,
        "non_fe_mi_mean": non_fe_mi_mean,
        "fe_advantage": fe_mi_mean - non_fe_mi_mean,
        "bridges": results,
        "winner": winner,
        "winner_mi": winner_mi,
        "baseline_mi": baseline_mi,
        "gain_over_baseline": gain,
    }


def main() -> None:
    print("=" * 72)
    print("AXIS 0 Fe-INDEXED Xi_hist PROBE")
    print("=" * 72)
    print("Comparing Fe-indexed bridge constructions against Phase 4 winner.")
    print()
    print("  A = Phase 4 winner (baseline): full trajectory, exp weighting")
    print("  B = Fe-indexed 7-step window: 8 windows at Fe steps, MI-weighted")
    print("  C = Fe pairs only: Ti→Fe adjacent pairs, MI-weighted")
    print("  D = lag=7 pairs: compression horizon lag, no Fe indexing")
    print()

    results = []
    for eng_type in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            r = run_torus(eng_type, torus_name, torus_val)
            results.append(r)

    # Aggregate
    n = len(results)
    winner_counts = {"A_phase4_winner": 0, "B_fe_indexed": 0,
                     "C_fe_pairs_only": 0, "D_lag7_pairs": 0}
    for r in results:
        winner_counts[r["winner"]] += 1

    mean_gains = {
        k: float(np.mean([r["bridges"][k]["mi"] - r["baseline_mi"] for r in results]))
        for k in ["B_fe_indexed", "C_fe_pairs_only", "D_lag7_pairs"]
    }
    mean_mi = {
        k: float(np.mean([r["bridges"][k]["mi"] for r in results]))
        for k in ["A_phase4_winner", "B_fe_indexed", "C_fe_pairs_only", "D_lag7_pairs"]
    }
    mean_ic = {
        k: float(np.mean([r["bridges"][k]["ic"] for r in results]))
        for k in ["A_phase4_winner", "B_fe_indexed", "C_fe_pairs_only", "D_lag7_pairs"]
    }
    mean_fe_adv = float(np.mean([r["fe_advantage"] for r in results]))

    print()
    print("=" * 72)
    print("OVERALL RESULTS")
    print("=" * 72)
    print(f"  Fe-step MI advantage over non-Fe: {mean_fe_adv:+.4f}")
    print()
    print(f"  {'Bridge':<20} {'mean MI':>8} {'mean Ic':>8} {'gain vs A':>10} {'wins':>5}")
    print(f"  {'-'*55}")
    for k, label in [
        ("A_phase4_winner", "A Phase4 baseline"),
        ("B_fe_indexed",    "B Fe-indexed 7-win"),
        ("C_fe_pairs_only", "C Fe pairs only"),
        ("D_lag7_pairs",    "D lag=7 pairs"),
    ]:
        gain_str = f"{mean_gains.get(k, 0.0):+.4f}" if k != "A_phase4_winner" else "   —"
        print(f"  {label:<20} {mean_mi[k]:>8.4f} {mean_ic[k]:>8.4f} {gain_str:>10} {winner_counts[k]:>5}/{n}")

    print()

    # Interpretation
    best_new = max(["B_fe_indexed", "C_fe_pairs_only", "D_lag7_pairs"],
                   key=lambda k: mean_mi[k])
    best_gain = mean_gains[best_new]

    if best_gain > 0.05:
        print(f"  ✓ KEEP — {best_new} beats Phase 4 winner by {best_gain:+.4f} MI")
        print("    Fe-indexed construction provides meaningful improvement.")
    elif best_gain > 0.0:
        print(f"  ◐ MARGINAL — {best_new} marginally improves by {best_gain:+.4f} MI")
        print("    Fe indexing helps but not dramatically.")
    else:
        print(f"  ✗ KILL — Phase 4 winner holds; Fe indexing adds no MI gain")
        print("    The full-trajectory exponential weighting is already optimal.")

    # FEP framing note
    print()
    print("  FEP framing:")
    print(f"    Fe steps = {results[0]['fe_step_count']}/32 = 25% of trajectory")
    print(f"    Fe MI mean: {float(np.mean([r['fe_mi_mean'] for r in results])):.4f}")
    print(f"    Non-Fe MI: {float(np.mean([r['non_fe_mi_mean'] for r in results])):.4f}")
    print("    Interpretation: Fe is prediction INSTANTIATION, not sensory correction.")
    print("    Phase5A certified marginal-preserving MI ≈ 0 → prediction dominates.")
    print("    The entire 4-step cycle is the prior unfolding; Fe is its peak.")

    print()
    print("================================================================================")
    print("PROBE STATUS: PASS")
    print("================================================================================")

    def safe(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.bool_,)): return bool(obj)
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, dict): return {k: safe(v) for k, v in obj.items()}
        if isinstance(obj, list): return [safe(v) for v in obj]
        return obj

    output = {
        "timestamp": datetime.now(UTC).isoformat(),
        "compression_horizon_steps": WINDOW,
        "results": safe(results),
        "summary": {
            "winner_counts": winner_counts,
            "mean_mi": mean_mi,
            "mean_ic": mean_ic,
            "mean_gains_vs_A": mean_gains,
            "best_new_bridge": best_new,
            "best_gain": best_gain,
            "mean_fe_advantage": mean_fe_adv,
        },
    }

    out_path = os.path.join(
        os.path.dirname(__file__),
        "a2_state", "sim_results", "axis0_fe_indexed_xi_hist_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
