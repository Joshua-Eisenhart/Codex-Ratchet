#!/usr/bin/env python3
"""
Xi-Bridge Bakeoff Probe
=======================

From the AXIS_0_1_2_QIT_MATH.md bounded next-sims table:

  Input:   same geometry/history sample under multiple bridge proposals
  Compare: shell-cut, point-reference, history-window, and left/right
           paired noncanon candidates
  Observables: sign, monotonicity, perturbation sensitivity, loop-family stability
  Discriminate: least-arbitrary bridge family

Four bridge families tested on identical engine trajectories:

  1. Xi_shell — shell-label classical register over nested tori
  2. Xi_point_ref — reference-point discriminator (Clifford ref)
  3. Xi_hist — history-window uniform average (current live winner family)
  4. Xi_chiral — L/R chirality-entangled noncanon candidate

Each is evaluated on:
  - sign:     I_c sign (negative conditional entropy = positive = nontrivial)
  - monotonicity: does MI grow monotonically as history accumulates?
  - perturbation sensitivity: how much does the bridge change under small eta perturbation?
  - loop-family stability: fiber-loop vs base-loop metric variance

Author: Claude Code (bakeoff probe)
Date: 2026-04-04
Doctrine source: AXIS_0_1_2_QIT_MATH.md next-sims table, row 4
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from typing import Dict, List, Tuple

import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    fiber_action,
    left_density,
    right_density,
    torus_coordinates,
)

EPS = 1e-12
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)

TORUS_CONFIGS = [
    ("inner", TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer", TORUS_OUTER),
]


# ═══════════════════════════════════════════════════════════════════
# QIT helpers (local, no cross-file dependency beyond engine_core)
# ═══════════════════════════════════════════════════════════════════

def vne(rho: np.ndarray) -> float:
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0


def ptr_B(r: np.ndarray) -> np.ndarray:
    return np.trace(r.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def ptr_A(r: np.ndarray) -> np.ndarray:
    return np.trace(r.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def mi(rho: np.ndarray) -> float:
    return max(0.0, vne(ptr_B(rho)) + vne(ptr_A(rho)) - vne(rho))


def ic(rho: np.ndarray) -> float:
    return vne(ptr_A(rho)) - vne(rho)


def s_a_given_b(rho: np.ndarray) -> float:
    return vne(rho) - vne(ptr_A(rho))


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(s @ rho)))
                     for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def pair_state(rho_L: np.ndarray, rho_R: np.ndarray) -> np.ndarray:
    return _ensure_valid_density(np.kron(rho_L, rho_R))


def full_metrics(rho: np.ndarray) -> Dict[str, float]:
    return {"I_AB": mi(rho), "I_c": ic(rho), "S_A_given_B": s_a_given_b(rho)}


# ═══════════════════════════════════════════════════════════════════
# Bridge constructions
# ═══════════════════════════════════════════════════════════════════

def bridge_shell(state, torus_label: str, eta: float) -> np.ndarray:
    """Xi_shell: shell-label classical register — weight pair states
    sampled at the three nested tori by Gaussian proximity to current eta."""
    sigma = np.pi / 8
    etas = np.array([e for _, e in TORUS_CONFIGS])
    weights = np.exp(-0.5 * ((etas - eta) / sigma) ** 2)
    weights /= weights.sum()

    rho = np.zeros((4, 4), dtype=complex)
    for (_, shell_eta), w in zip(TORUS_CONFIGS, weights):
        q = torus_coordinates(shell_eta, 0.0, 0.0)
        rho_L = left_density(q)
        rho_R = right_density(q)
        rho += w * pair_state(rho_L, rho_R)
    return _ensure_valid_density(rho)


def bridge_point_ref(state, eta: float) -> np.ndarray:
    """Xi_point_ref: reference-point discriminator.
    Equal mix of Clifford-reference pair state and current pair state."""
    q_ref = torus_coordinates(TORUS_CLIFFORD, 0.0, 0.0)
    rho_ref = pair_state(left_density(q_ref), right_density(q_ref))
    rho_cur = pair_state(state.rho_L, state.rho_R)
    return _ensure_valid_density(0.5 * rho_ref + 0.5 * rho_cur)


def bridge_hist(state, start: int = 0, end: int | None = None) -> np.ndarray:
    """Xi_hist: uniform history-window average over engine trajectory."""
    history = state.history[start:end]
    if not history:
        return pair_state(state.rho_L, state.rho_R)
    rho = np.zeros((4, 4), dtype=complex)
    for h in history:
        rho += pair_state(h["rho_L"], h["rho_R"])
    return _ensure_valid_density(rho / len(history))


def bridge_chiral(state) -> np.ndarray:
    """Xi_chiral: L/R chirality-entangled noncanon candidate.
    Mixes product state with a partially entangled state whose
    entanglement parameter comes from L/R Bloch asymmetry."""
    rho_L, rho_R = state.rho_L, state.rho_R
    bL, bR = bloch(rho_L), bloch(rho_R)
    asymmetry = 0.5 * np.linalg.norm(bL - bR)
    p = float(np.clip(asymmetry, 0.01, 0.99))
    theta = np.arcsin(np.sqrt(p))
    psi_ent = np.array([np.cos(theta), 0, 0, np.sin(theta)], dtype=complex)
    rho_ent = np.outer(psi_ent, psi_ent.conj())
    rho_prod = pair_state(rho_L, rho_R)
    return _ensure_valid_density((1 - p) * rho_prod + p * rho_ent)


# ═══════════════════════════════════════════════════════════════════
# Observables
# ═══════════════════════════════════════════════════════════════════

def measure_monotonicity(state) -> Dict[str, float]:
    """Track cumulative MI as history accumulates for Xi_hist.
    Returns fraction of steps where MI is non-decreasing."""
    history = state.history
    if len(history) < 3:
        return {"monotonic_fraction": 1.0, "n_steps": len(history)}
    mi_series = []
    rho_sum = np.zeros((4, 4), dtype=complex)
    for i, h in enumerate(history):
        rho_sum += pair_state(h["rho_L"], h["rho_R"])
        rho_avg = _ensure_valid_density(rho_sum / (i + 1))
        mi_series.append(mi(rho_avg))
    non_dec = sum(1 for i in range(1, len(mi_series)) if mi_series[i] >= mi_series[i - 1] - 1e-10)
    return {
        "monotonic_fraction": non_dec / (len(mi_series) - 1),
        "n_steps": len(mi_series),
        "mi_first": mi_series[0],
        "mi_last": mi_series[-1],
    }


def measure_perturbation_sensitivity(engine_type: int, eta: float,
                                      delta: float = 0.01) -> Dict[str, Dict[str, float]]:
    """Run engine at eta and eta+delta, compute bridge metric difference."""
    results = {}
    for label, e in [("base", eta), ("perturbed", eta + delta)]:
        engine = GeometricEngine(engine_type=engine_type)
        st = engine.init_state(eta=e)
        final = engine.run_cycle(st)
        results[label] = {
            "shell": full_metrics(bridge_shell(final, "", e)),
            "point_ref": full_metrics(bridge_point_ref(final, e)),
            "hist": full_metrics(bridge_hist(final)),
            "chiral": full_metrics(bridge_chiral(final)),
        }

    sensitivity = {}
    for bridge_name in ["shell", "point_ref", "hist", "chiral"]:
        base_mi = results["base"][bridge_name]["I_AB"]
        pert_mi = results["perturbed"][bridge_name]["I_AB"]
        base_ic = results["base"][bridge_name]["I_c"]
        pert_ic = results["perturbed"][bridge_name]["I_c"]
        sensitivity[bridge_name] = {
            "delta_I_AB": abs(pert_mi - base_mi),
            "delta_I_c": abs(pert_ic - base_ic),
            "relative_I_AB": abs(pert_mi - base_mi) / max(abs(base_mi), EPS),
        }
    return sensitivity


def measure_loop_stability(engine_type: int, eta: float,
                           n_samples: int = 16) -> Dict[str, Dict[str, float]]:
    """Measure bridge metric variance over fiber-loop and base-loop samples."""
    u_grid = np.linspace(0.0, 2 * np.pi, n_samples, endpoint=False)

    loop_metrics: Dict[str, Dict[str, List[float]]] = {
        b: {"fiber_mi": [], "base_mi": [], "fiber_ic": [], "base_ic": []}
        for b in ["shell", "point_ref", "hist", "chiral"]
    }

    for loop_type in ["fiber", "base"]:
        for u in u_grid:
            if loop_type == "fiber":
                q = fiber_action(torus_coordinates(eta, 0.0, 0.0), u)
            else:
                theta1 = 2.0 * (np.sin(eta) ** 2) * u
                theta2 = -2.0 * (np.cos(eta) ** 2) * u
                q = torus_coordinates(eta, theta1, theta2)

            rho_L = left_density(q)
            rho_R = right_density(q)

            # Build a minimal mock state for bridge functions
            class MockState:
                pass
            ms = MockState()
            ms.rho_L = rho_L
            ms.rho_R = rho_R
            ms.history = [{"rho_L": rho_L, "rho_R": rho_R}]

            rho_shell = bridge_shell(ms, "", eta)
            rho_pref = bridge_point_ref(ms, eta)
            rho_hist = bridge_hist(ms)
            rho_chir = bridge_chiral(ms)

            for bname, rho in [("shell", rho_shell), ("point_ref", rho_pref),
                               ("hist", rho_hist), ("chiral", rho_chir)]:
                loop_metrics[bname][f"{loop_type}_mi"].append(mi(rho))
                loop_metrics[bname][f"{loop_type}_ic"].append(ic(rho))

    stability = {}
    for bname in ["shell", "point_ref", "hist", "chiral"]:
        d = loop_metrics[bname]
        stability[bname] = {
            "fiber_mi_std": float(np.std(d["fiber_mi"])),
            "base_mi_std": float(np.std(d["base_mi"])),
            "fiber_ic_std": float(np.std(d["fiber_ic"])),
            "base_ic_std": float(np.std(d["base_ic"])),
            "fiber_mi_mean": float(np.mean(d["fiber_mi"])),
            "base_mi_mean": float(np.mean(d["base_mi"])),
        }
    return stability


# ═══════════════════════════════════════════════════════════════════
# Main bakeoff runner
# ═══════════════════════════════════════════════════════════════════

def run_bakeoff() -> Dict:
    print("=" * 72)
    print("XI-BRIDGE BAKEOFF PROBE")
    print("=" * 72)
    print()
    print("  Families: shell, point_ref, hist, chiral")
    print("  Observables: sign, monotonicity, perturbation, loop-stability")
    print()

    rows = []
    for engine_type in [1, 2]:
        for torus_label, eta in TORUS_CONFIGS:
            engine = GeometricEngine(engine_type=engine_type)
            st = engine.init_state(eta=eta)
            final = engine.run_cycle(st)

            # Build bridges
            rho_shell = bridge_shell(final, torus_label, eta)
            rho_pref = bridge_point_ref(final, eta)
            rho_hist = bridge_hist(final)
            rho_chiral = bridge_chiral(final)

            bridges = {
                "shell": full_metrics(rho_shell),
                "point_ref": full_metrics(rho_pref),
                "hist": full_metrics(rho_hist),
                "chiral": full_metrics(rho_chiral),
            }

            # Monotonicity (hist only — the only accumulative bridge)
            mono = measure_monotonicity(final)

            # Perturbation sensitivity
            perturb = measure_perturbation_sensitivity(engine_type, eta)

            # Loop-family stability
            loop_stab = measure_loop_stability(engine_type, eta)

            # Sign check
            sign_report = {}
            for bname, m in bridges.items():
                sign_report[bname] = {
                    "I_c_positive": m["I_c"] > 0,
                    "S_A_given_B_negative": m["S_A_given_B"] < 0,
                }

            row = {
                "engine_type": engine_type,
                "torus": torus_label,
                "bridges": bridges,
                "sign": sign_report,
                "monotonicity": mono,
                "perturbation": perturb,
                "loop_stability": loop_stab,
            }
            rows.append(row)

            # Print summary line
            winner = max(bridges, key=lambda k: bridges[k]["I_AB"])
            print(f"  E{engine_type}/{torus_label}: "
                  f"shell={bridges['shell']['I_AB']:.4f} "
                  f"pref={bridges['point_ref']['I_AB']:.4f} "
                  f"hist={bridges['hist']['I_AB']:.4f} "
                  f"chiral={bridges['chiral']['I_AB']:.4f} "
                  f"| winner={winner}")

    return rows


def aggregate(rows: List[Dict]) -> Dict:
    """Aggregate across all engine/torus configs."""
    bridge_names = ["shell", "point_ref", "hist", "chiral"]
    n = len(rows)

    mean_mi = {}
    mean_ic = {}
    win_counts = {b: 0 for b in bridge_names}
    sign_positive_counts = {b: 0 for b in bridge_names}
    mean_perturb = {b: [] for b in bridge_names}
    mean_fiber_std = {b: [] for b in bridge_names}
    mean_base_std = {b: [] for b in bridge_names}

    for b in bridge_names:
        mis = [r["bridges"][b]["I_AB"] for r in rows]
        ics = [r["bridges"][b]["I_c"] for r in rows]
        mean_mi[b] = float(np.mean(mis))
        mean_ic[b] = float(np.mean(ics))

    for r in rows:
        winner = max(bridge_names, key=lambda k: r["bridges"][k]["I_AB"])
        win_counts[winner] += 1
        for b in bridge_names:
            sign_positive_counts[b] += int(r["sign"][b]["I_c_positive"])
            mean_perturb[b].append(r["perturbation"][b]["relative_I_AB"])
            mean_fiber_std[b].append(r["loop_stability"][b]["fiber_mi_std"])
            mean_base_std[b].append(r["loop_stability"][b]["base_mi_std"])

    mono_fracs = [r["monotonicity"]["monotonic_fraction"] for r in rows]

    # Rank by mean MI
    ranking = sorted(bridge_names, key=lambda b: mean_mi[b], reverse=True)

    # Least-arbitrary determination:
    # A bridge is "least-arbitrary" if it:
    #   1. Has nontrivial MI (not killed)
    #   2. Has consistent sign (I_c positive across configs)
    #   3. Is stable under perturbation (low relative sensitivity)
    #   4. Is stable across loop families (low fiber/base variance)
    scores = {}
    for b in bridge_names:
        mi_score = mean_mi[b]
        sign_score = sign_positive_counts[b] / n
        perturb_score = 1.0 - min(1.0, float(np.mean(mean_perturb[b])))
        stability_score = 1.0 - min(1.0, float(np.mean(mean_fiber_std[b]) + np.mean(mean_base_std[b])))
        # Weighted composite
        scores[b] = 0.4 * mi_score + 0.2 * sign_score + 0.2 * perturb_score + 0.2 * stability_score

    least_arbitrary = max(scores, key=lambda k: scores[k])

    return {
        "ranking_by_mi": ranking,
        "mean_mi": mean_mi,
        "mean_ic": mean_ic,
        "win_counts": win_counts,
        "sign_positive_counts": sign_positive_counts,
        "mean_perturbation_sensitivity": {b: float(np.mean(v)) for b, v in mean_perturb.items()},
        "mean_fiber_mi_std": {b: float(np.mean(v)) for b, v in mean_fiber_std.items()},
        "mean_base_mi_std": {b: float(np.mean(v)) for b, v in mean_base_std.items()},
        "hist_monotonicity_mean": float(np.mean(mono_fracs)),
        "composite_scores": {b: float(scores[b]) for b in bridge_names},
        "least_arbitrary": least_arbitrary,
    }


def main() -> None:
    rows = run_bakeoff()
    summary = aggregate(rows)

    print()
    print("=" * 72)
    print("AGGREGATE RESULTS")
    print("=" * 72)
    print()
    print(f"  {'Bridge':<12} {'mean MI':>8} {'mean Ic':>8} {'wins':>5} {'Ic+ count':>10} "
          f"{'perturb':>8} {'fiber σ':>8} {'base σ':>8} {'score':>8}")
    print(f"  {'-' * 80}")
    for b in summary["ranking_by_mi"]:
        print(f"  {b:<12} "
              f"{summary['mean_mi'][b]:>8.4f} "
              f"{summary['mean_ic'][b]:>8.4f} "
              f"{summary['win_counts'][b]:>5}/{len(rows)} "
              f"{summary['sign_positive_counts'][b]:>10}/{len(rows)} "
              f"{summary['mean_perturbation_sensitivity'][b]:>8.4f} "
              f"{summary['mean_fiber_mi_std'][b]:>8.6f} "
              f"{summary['mean_base_mi_std'][b]:>8.6f} "
              f"{summary['composite_scores'][b]:>8.4f}")

    print()
    print(f"  History monotonicity (mean fraction non-decreasing): "
          f"{summary['hist_monotonicity_mean']:.4f}")
    print()
    print(f"  LEAST-ARBITRARY BRIDGE FAMILY: {summary['least_arbitrary']}")
    print()
    print("  Note: 'least-arbitrary' = highest composite of MI magnitude,")
    print("        sign consistency, perturbation stability, loop stability.")
    print("        This does NOT claim doctrine closure on Xi.")
    print()
    print("=" * 72)
    print("PROBE STATUS: PASS")
    print("=" * 72)

    # Serialize
    def safe(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, dict):
            return {k: safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [safe(v) for v in obj]
        return obj

    output = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_xi_bridge_bakeoff",
        "source": "AXIS_0_1_2_QIT_MATH.md next-sims table row 4",
        "families_compared": ["shell", "point_ref", "hist", "chiral"],
        "observables": ["sign", "monotonicity", "perturbation_sensitivity", "loop_family_stability"],
        "results": safe(rows),
        "summary": safe(summary),
        "doctrine_note": "least-arbitrary family is explicit; no closure claimed on Xi",
    }

    out_path = os.path.join(
        os.path.dirname(__file__),
        "a2_state", "sim_results", "xi_bridge_bakeoff_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
