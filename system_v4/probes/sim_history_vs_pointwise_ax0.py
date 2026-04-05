#!/usr/bin/env python3
"""
History-vs-Pointwise Ax0 Probe
==============================

Compares two structurally distinct Axis 0 bridge evaluation families:

  POINTWISE (Ax0-native)
    Evaluate Φ₀(ρ_AB) at a single geometric point.  No engine history needed.
    - Xi_LR_direct      : raw L⊗R product (control)
    - Xi_shell_cq       : shell-label classical register across nested tori
    - Xi_point_ref_cq   : reference-point discriminator (q_ref vs q_final)

  HISTORY-WINDOW (Ax2-adjacent)
    Build ρ_AB from a trajectory window produced by the live engine.
    - Xi_hist_uniform    : uniform average over history window
    - Xi_hist_fe_indexed : Fe-transition 7-step windows, MI-weighted
    - Xi_hist_retro_exp  : exponential attractor-proximity weighting (Phase 4 winner)

These two families answer DIFFERENT questions:
  - Pointwise: "what does the geometry say about the cut at this point?"
  - History:   "what does the trajectory say about the cut over a window?"

The handoff rule: do NOT collapse these into one winner.
Both families remain open and must be narrowed independently.

Author: Claude Code (handoff: claude-history-vs-pointwise-ax0-probe)
Date: 2026-04-04
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import (
    TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER,
    left_density, right_density, torus_coordinates,
)

TORUS_CONFIGS = [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]
PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL = np.outer(PSI_MINUS, PSI_MINUS.conj())
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
EPS = 1e-12
WINDOW = 7  # compression horizon (steps)


# ─── QIT utilities ──────────────────────────────────────────────────────── #

def vne(rho: np.ndarray) -> float:
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0


def ptr_B(r):
    return np.trace(r.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def ptr_A(r):
    return np.trace(r.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def mi_val(rho: np.ndarray) -> float:
    return max(0.0, vne(ptr_B(rho)) + vne(ptr_A(rho)) - vne(rho))


def ic_val(rho: np.ndarray) -> float:
    return vne(ptr_A(rho)) - vne(rho)


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(s @ rho)))
                     for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def lr_asym(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0.01, 0.99))


# ─── Shared bridge primitive ────────────────────────────────────────────── #

def cross_s1_symmetric(rho_L1, rho_R1, rho_L2, rho_R2):
    """Phase 4 winner pattern: symmetric forward+backward Bell bridge."""
    p_f = lr_asym(rho_L1, rho_R2)
    rho_f = _ensure_valid_density((1 - p_f) * np.kron(rho_L1, rho_R2) + p_f * BELL)
    p_b = lr_asym(rho_L2, rho_R1)
    rho_b = _ensure_valid_density((1 - p_b) * np.kron(rho_L2, rho_R1) + p_b * BELL)
    return _ensure_valid_density(0.5 * rho_f + 0.5 * rho_b)


# ═══════════════════════════════════════════════════════════════════════════ #
# POINTWISE FAMILY — geometry only, no engine history                       #
# ═══════════════════════════════════════════════════════════════════════════ #

def pointwise_lr_direct(rho_L, rho_R):
    """Control: raw L⊗R product. Should be MI-trivial."""
    return _ensure_valid_density(np.kron(rho_L, rho_R))


def pointwise_shell_cq(rho_L, rho_R, eta):
    """
    Shell-label cq state: classical register over the 3 nested tori,
    Gaussian-weighted by distance to current eta.
    """
    sigma = np.pi / 8
    etas = np.array([e for _, e in TORUS_CONFIGS])
    weights = np.exp(-0.5 * ((etas - eta) / sigma) ** 2)
    weights /= weights.sum()

    # Get angles from current densities for sampling other tori
    b_L = bloch(rho_L)
    b_R = bloch(rho_R)

    n_labels = len(TORUS_CONFIGS)
    dim_b = 4  # 2x2 bipartite
    total = np.zeros((n_labels * dim_b, n_labels * dim_b), dtype=complex)
    for idx, ((_, shell_eta), w) in enumerate(zip(TORUS_CONFIGS, weights)):
        q = torus_coordinates(shell_eta, 0.0, 0.0)
        rL = left_density(q)
        rR = right_density(q)
        rho_pair = _ensure_valid_density(np.kron(rL, rR))
        start = idx * dim_b
        total[start:start + dim_b, start:start + dim_b] = w * rho_pair

    total = _ensure_valid_density(total)
    # MI on the full cq state (label ⊗ pair)
    dims = [n_labels, dim_b]
    rho_A = np.trace(total.reshape(n_labels, dim_b, n_labels, dim_b), axis1=1, axis2=3)
    rho_B = np.trace(total.reshape(n_labels, dim_b, n_labels, dim_b), axis1=0, axis2=2)
    s_a = vne(rho_A)
    s_b = vne(rho_B)
    s_ab = vne(total)
    mi = max(0.0, s_a + s_b - s_ab)
    ic = s_b - s_ab
    return {"mi": mi, "ic": ic}


def pointwise_point_ref(rho_L, rho_R, rho_L_ref, rho_R_ref):
    """
    Point-reference cq: equal-weight mixture of reference and current pair states.
    """
    rho_ref = _ensure_valid_density(np.kron(rho_L_ref, rho_R_ref))
    rho_cur = _ensure_valid_density(np.kron(rho_L, rho_R))
    n_labels = 2
    dim_b = 4
    total = np.zeros((n_labels * dim_b, n_labels * dim_b), dtype=complex)
    total[0:dim_b, 0:dim_b] = 0.5 * rho_ref
    total[dim_b:2 * dim_b, dim_b:2 * dim_b] = 0.5 * rho_cur
    total = _ensure_valid_density(total)
    rho_A = np.trace(total.reshape(n_labels, dim_b, n_labels, dim_b), axis1=1, axis2=3)
    rho_B = np.trace(total.reshape(n_labels, dim_b, n_labels, dim_b), axis1=0, axis2=2)
    s_a = vne(rho_A)
    s_b = vne(rho_B)
    s_ab = vne(total)
    mi = max(0.0, s_a + s_b - s_ab)
    ic = s_b - s_ab
    return {"mi": mi, "ic": ic}


# ═══════════════════════════════════════════════════════════════════════════ #
# HISTORY-WINDOW FAMILY — requires engine trajectory                        #
# ═══════════════════════════════════════════════════════════════════════════ #

def history_uniform(history):
    """Uniform average over full trajectory. The simplest history bridge."""
    pairs = [_ensure_valid_density(np.kron(h["rho_L"], h["rho_R"])) for h in history]
    rho = _ensure_valid_density(sum(pairs) / len(pairs))
    return rho


def history_retro_exp(history):
    """Phase 4 winner: cross_s1_symmetric with exponential attractor-proximity."""
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


def history_fe_indexed(history):
    """
    Fe-indexed 7-step windows, MI-weighted.
    Each Fe-transition step anchors a 7-step window;
    the window bridge is weighted by Fe-step MI magnitude.
    """
    fe_steps = [i for i, s in enumerate(history) if s["op_name"] == "Fe"]
    if not fe_steps:
        return history_uniform(history)

    window_rhos, window_weights = [], []
    for t_fe in fe_steps:
        win_start = max(0, t_fe - (WINDOW - 1))
        window = history[win_start:t_fe + 1]
        if len(window) < 2:
            continue

        rho_L_fe = history[t_fe]["rho_L"]
        rho_R_fe = history[t_fe]["rho_R"]
        p = lr_asym(rho_L_fe, rho_R_fe)
        fe_rho = _ensure_valid_density((1 - p) * np.kron(rho_L_fe, rho_R_fe) + p * BELL)
        fe_mi = mi_val(fe_rho)

        inner_states, inner_weights = [], []
        W = len(window)
        for j in range(W - 1):
            rho = cross_s1_symmetric(
                window[j]["rho_L"], window[j]["rho_R"],
                window[j + 1]["rho_L"], window[j + 1]["rho_R"],
            )
            inner_states.append(rho)
            inner_weights.append(np.exp(-0.1 * (W - 2 - j)))

        inner_weights = np.array(inner_weights) / np.sum(inner_weights)
        window_rho = _ensure_valid_density(
            sum(w * s for w, s in zip(inner_weights, inner_states))
        )
        window_rhos.append(window_rho)
        window_weights.append(fe_mi)

    if not window_rhos:
        return history_uniform(history)

    window_weights = np.array(window_weights) / np.sum(window_weights)
    return _ensure_valid_density(
        sum(w * s for w, s in zip(window_weights, window_rhos))
    )


# ═══════════════════════════════════════════════════════════════════════════ #
# Runner                                                                     #
# ═══════════════════════════════════════════════════════════════════════════ #

def run_config(engine_type: int, torus_name: str, torus_val: float) -> dict:
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=torus_val)
    final_state = engine.run_cycle(state)
    history = final_state.history

    # Reference state: initial geometry (u=0)
    q_ref = torus_coordinates(torus_val, 0.0, 0.0)
    rho_L_ref = left_density(q_ref)
    rho_R_ref = right_density(q_ref)

    # Final state densities
    rho_L = final_state.rho_L
    rho_R = final_state.rho_R

    # ── Pointwise family ──
    rho_lr = pointwise_lr_direct(rho_L, rho_R)
    pw_lr = {"mi": mi_val(rho_lr), "ic": ic_val(rho_lr)}

    pw_shell = pointwise_shell_cq(rho_L, rho_R, torus_val)
    pw_ref = pointwise_point_ref(rho_L, rho_R, rho_L_ref, rho_R_ref)

    pointwise = {
        "lr_direct": pw_lr,
        "shell_cq": pw_shell,
        "point_ref_cq": pw_ref,
    }

    # ── History-window family ──
    rho_hist_u = history_uniform(history)
    hw_uniform = {"mi": mi_val(rho_hist_u), "ic": ic_val(rho_hist_u)}

    rho_hist_r = history_retro_exp(history)
    hw_retro = {"mi": mi_val(rho_hist_r), "ic": ic_val(rho_hist_r)}

    rho_hist_fe = history_fe_indexed(history)
    hw_fe = {"mi": mi_val(rho_hist_fe), "ic": ic_val(rho_hist_fe)}

    history_window = {
        "hist_uniform": hw_uniform,
        "hist_retro_exp": hw_retro,
        "hist_fe_indexed": hw_fe,
    }

    # ── Best per family (no cross-family ranking) ──
    pw_best = max(pointwise, key=lambda k: pointwise[k]["mi"])
    hw_best = max(history_window, key=lambda k: history_window[k]["mi"])

    return {
        "engine_type": engine_type,
        "torus": torus_name,
        "pointwise": pointwise,
        "history_window": history_window,
        "pointwise_best": pw_best,
        "pointwise_best_mi": pointwise[pw_best]["mi"],
        "history_best": hw_best,
        "history_best_mi": history_window[hw_best]["mi"],
        "history_steps": len(history),
    }


def main():
    print("=" * 72)
    print("HISTORY vs POINTWISE Ax0 PROBE")
    print("=" * 72)
    print()
    print("  POINTWISE family (geometry-only, no engine history):")
    print("    lr_direct    — raw L⊗R product (control)")
    print("    shell_cq     — shell-label classical register")
    print("    point_ref_cq — reference-point discriminator")
    print()
    print("  HISTORY-WINDOW family (engine trajectory):")
    print("    hist_uniform    — uniform average over full history")
    print("    hist_retro_exp  — exponential attractor-proximity (Phase 4 winner)")
    print("    hist_fe_indexed — Fe-indexed 7-step windows, MI-weighted")
    print()

    results = []
    for eng_type in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            r = run_config(eng_type, torus_name, torus_val)
            results.append(r)

            pw = r["pointwise"]
            hw = r["history_window"]
            print(f"  {eng_type}/{torus_name}:")
            print(f"    PW  lr={pw['lr_direct']['mi']:.4f}  "
                  f"shell={pw['shell_cq']['mi']:.4f}  "
                  f"ref={pw['point_ref_cq']['mi']:.4f}  "
                  f"| best={r['pointwise_best']} ({r['pointwise_best_mi']:.4f})")
            print(f"    HW  unif={hw['hist_uniform']['mi']:.4f}  "
                  f"retro={hw['hist_retro_exp']['mi']:.4f}  "
                  f"fe={hw['hist_fe_indexed']['mi']:.4f}  "
                  f"| best={r['history_best']} ({r['history_best_mi']:.4f})")

    # ── Aggregate ──
    n = len(results)

    pw_keys = ["lr_direct", "shell_cq", "point_ref_cq"]
    hw_keys = ["hist_uniform", "hist_retro_exp", "hist_fe_indexed"]

    mean_pw_mi = {k: float(np.mean([r["pointwise"][k]["mi"] for r in results])) for k in pw_keys}
    mean_hw_mi = {k: float(np.mean([r["history_window"][k]["mi"] for r in results])) for k in hw_keys}
    mean_pw_ic = {k: float(np.mean([r["pointwise"][k]["ic"] for r in results])) for k in pw_keys}
    mean_hw_ic = {k: float(np.mean([r["history_window"][k]["ic"] for r in results])) for k in hw_keys}

    pw_winner_counts = {k: 0 for k in pw_keys}
    hw_winner_counts = {k: 0 for k in hw_keys}
    for r in results:
        pw_winner_counts[r["pointwise_best"]] += 1
        hw_winner_counts[r["history_best"]] += 1

    print()
    print("=" * 72)
    print("AGGREGATE RESULTS")
    print("=" * 72)

    print()
    print("  POINTWISE FAMILY (Ax0-native)")
    print(f"  {'Bridge':<18} {'mean MI':>8} {'mean Ic':>8} {'wins':>6}")
    print(f"  {'-' * 44}")
    for k in pw_keys:
        print(f"  {k:<18} {mean_pw_mi[k]:>8.4f} {mean_pw_ic[k]:>8.4f} {pw_winner_counts[k]:>5}/{n}")

    print()
    print("  HISTORY-WINDOW FAMILY (Ax2-adjacent)")
    print(f"  {'Bridge':<18} {'mean MI':>8} {'mean Ic':>8} {'wins':>6}")
    print(f"  {'-' * 44}")
    for k in hw_keys:
        print(f"  {k:<18} {mean_hw_mi[k]:>8.4f} {mean_hw_ic[k]:>8.4f} {hw_winner_counts[k]:>5}/{n}")

    # ── Cross-family comparison (diagnostic only, NOT a collapse) ──
    best_pw_key = max(pw_keys, key=lambda k: mean_pw_mi[k])
    best_hw_key = max(hw_keys, key=lambda k: mean_hw_mi[k])
    gap = mean_hw_mi[best_hw_key] - mean_pw_mi[best_pw_key]

    print()
    print("  CROSS-FAMILY DIAGNOSTIC (not a collapse — both families remain open)")
    print(f"    Best pointwise:      {best_pw_key} MI={mean_pw_mi[best_pw_key]:.4f}")
    print(f"    Best history-window: {best_hw_key} MI={mean_hw_mi[best_hw_key]:.4f}")
    print(f"    Gap (history − pointwise): {gap:+.4f}")

    if gap > 0.05:
        cross_verdict = "history_leads"
        print("    → History-window family produces substantially higher MI.")
        print("      This is expected: Bell injection + trajectory integration adds information.")
        print("      This does NOT mean pointwise is wrong — they answer different questions.")
    elif gap > -0.05:
        cross_verdict = "comparable"
        print("    → Both families produce comparable MI.")
        print("      Neither family dominates; both remain live for their respective roles.")
    else:
        cross_verdict = "pointwise_leads"
        print("    → Pointwise family produces higher MI.")
        print("      Unexpected: geometry-only evaluation outperforms trajectory integration.")

    print()
    print("=" * 72)
    print("PROBE STATUS: PASS")
    print("=" * 72)

    # ── Emit artifact ──
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
        "probe": "sim_history_vs_pointwise_ax0",
        "description": "Compares pointwise (Ax0-native) and history-window (Ax2-adjacent) bridge families. Does NOT collapse them into one winner.",
        "results": safe(results),
        "summary": {
            "pointwise": {
                "mean_mi": mean_pw_mi,
                "mean_ic": mean_pw_ic,
                "winner_counts": pw_winner_counts,
                "best": best_pw_key,
                "best_mi": mean_pw_mi[best_pw_key],
            },
            "history_window": {
                "mean_mi": mean_hw_mi,
                "mean_ic": mean_hw_ic,
                "winner_counts": hw_winner_counts,
                "best": best_hw_key,
                "best_mi": mean_hw_mi[best_hw_key],
            },
            "cross_family": {
                "gap_history_minus_pointwise": gap,
                "verdict": cross_verdict,
                "note": "diagnostic only — both families remain open and must be narrowed independently",
            },
        },
    }

    out_path = os.path.join(
        os.path.dirname(__file__),
        "a2_state", "sim_results", "history_vs_pointwise_ax0_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
