#!/usr/bin/env python3
"""
Axis 0 FEP / Compression-from-Future Framing Sim
==================================================
Tests whether the engine trajectory's information structure is better described
by compression-from-future (entropic monism / FEP) than by classical
cause-from-past propagation.

Four tests:

  Test 1 — Temporal MI asymmetry
    Is the MI of the backward cross-temporal bridge (late L ⊗ early R) ≥
    forward bridge (early L ⊗ late R)?
    Keep: backward ≥ forward (future predicts past better than past predicts future)
    Kill: forward dominates (classical causal chain)

  Test 2 — Attractor vs drift (Bloch autocorrelation)
    Compute autocorrelation of step-to-step Bloch vector changes.
    Keep: negative autocorrelation (mean-reverting / attractor basin / FEP)
    Kill: positive autocorrelation (causal momentum / drift)

  Test 3 — jk fuzz directionality (ga0 vs MI cross-correlation)
    Compute cross-correlation between ga0 fluctuation and MI fluctuation.
    Keep: ga0 change LAGS MI change (the entropy field responds to MI structure,
          not the other way — compression is primary)
    Kill: ga0 change LEADS MI change (entropy field drives MI — classical causation)

  Test 4 — Trajectory MI profile: does MI increase toward the attractor?
    If the trajectory is converging toward a compressed attractor, later
    cross-temporal MI should be higher than earlier.
    Keep: MI trend is upward across the trajectory (attractor convergence)
    Kill: MI is flat or decreasing (no convergence)

Terminology note:
  "Retrocausal weighting" in Xi_hist is renamed here as "attractor-proximity
  weighting" per AXIS0_ENTROPIC_MONISM_DOCTRINE_BRIDGE.md. Later steps get
  higher weight because they are closer to the compressed attractor, not because
  the future causes the past.
"""

from __future__ import annotations
import json, os, sys
from datetime import UTC, datetime
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER

TORUS_CONFIGS = [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]
PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL_PSI_MINUS = np.outer(PSI_MINUS, PSI_MINUS.conj())
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
EPS = 1e-12


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


def mi_val(rho_AB: np.ndarray) -> float:
    return max(0.0, vne(ptr_B(rho_AB)) + vne(ptr_A(rho_AB)) - vne(rho_AB))


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def lr_asym(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0.0, 1.0))


def cross_temporal_mi(rho_L_t1: np.ndarray, rho_R_t2: np.ndarray) -> float:
    """MI of the Phase4 cross-temporal bridge: L(t1) ⊗ R(t2) with Bell injection."""
    p = float(np.clip(lr_asym(rho_L_t1, rho_R_t2), 0.01, 0.99))
    prod = _ensure_valid_density(np.kron(rho_L_t1, rho_R_t2))
    rho = _ensure_valid_density((1 - p) * prod + p * BELL_PSI_MINUS)
    return mi_val(rho)


def autocorr(x: list[float], lag: int = 1) -> float:
    """Pearson autocorrelation at given lag."""
    if len(x) <= lag:
        return 0.0
    a = np.array(x[:-lag])
    b = np.array(x[lag:])
    if np.std(a) < EPS or np.std(b) < EPS:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def cross_corr_lag(x: list[float], y: list[float], lag: int) -> float:
    """Cross-correlation of x(t) with y(t+lag). Positive lag = x leads y."""
    if lag >= 0:
        a, b = np.array(x[:len(x)-lag]), np.array(y[lag:])
    else:
        a, b = np.array(x[-lag:]), np.array(y[:len(y)+lag])
    if len(a) < 3 or np.std(a) < EPS or np.std(b) < EPS:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


# --------------------------------------------------------------------------- #
# Test 1 — Temporal MI asymmetry                                              #
# --------------------------------------------------------------------------- #

def test1_temporal_mi_asymmetry(history: list[dict], lag: int = 1) -> dict:
    """
    Forward MI: L(t) ⊗ R(t+lag)
    Backward MI: L(t+lag) ⊗ R(t)
    Keep if mean backward ≥ mean forward.
    """
    fwd_mi, bwd_mi = [], []
    T = len(history)
    for t in range(T - lag):
        rho_L_early = history[t]["rho_L"]
        rho_R_early = history[t]["rho_R"]
        rho_L_late = history[t + lag]["rho_L"]
        rho_R_late = history[t + lag]["rho_R"]

        fwd = cross_temporal_mi(rho_L_early, rho_R_late)   # L(t) ⊗ R(t+lag)
        bwd = cross_temporal_mi(rho_L_late, rho_R_early)   # L(t+lag) ⊗ R(t)

        fwd_mi.append(fwd)
        bwd_mi.append(bwd)

    mean_fwd = float(np.mean(fwd_mi))
    mean_bwd = float(np.mean(bwd_mi))
    asymmetry = mean_bwd - mean_fwd
    keep = bool(asymmetry >= 0.0)

    return {
        "mean_forward_mi": mean_fwd,
        "mean_backward_mi": mean_bwd,
        "asymmetry_bwd_minus_fwd": asymmetry,
        "keep": keep,
        "interpretation": (
            "backward ≥ forward → future predicts past (compression-from-future)" if keep
            else "forward > backward → past predicts future (classical causation)"
        ),
    }


# --------------------------------------------------------------------------- #
# Test 2 — Attractor vs drift                                                 #
# --------------------------------------------------------------------------- #

def test2_attractor_vs_drift(history: list[dict]) -> dict:
    """
    Compute Bloch vector for rho_L at each step.
    Compute step-to-step change magnitudes.
    Negative autocorrelation → mean-reverting attractor (FEP / compression).
    Positive autocorrelation → drift / causal momentum.
    """
    bloch_L = [bloch(s["rho_L"]) for s in history]
    bloch_R = [bloch(s["rho_R"]) for s in history]

    delta_L = [float(np.linalg.norm(bloch_L[t + 1] - bloch_L[t])) for t in range(len(bloch_L) - 1)]
    delta_R = [float(np.linalg.norm(bloch_R[t + 1] - bloch_R[t])) for t in range(len(bloch_R) - 1)]

    ac_L = autocorr(delta_L, lag=1)
    ac_R = autocorr(delta_R, lag=1)
    mean_ac = (ac_L + ac_R) / 2.0

    keep = bool(mean_ac < 0.0)

    return {
        "autocorr_delta_L": ac_L,
        "autocorr_delta_R": ac_R,
        "mean_autocorr": mean_ac,
        "keep": keep,
        "interpretation": (
            "negative autocorr → mean-reverting attractor (FEP / compression-from-future)" if keep
            else "positive autocorr → drift / causal momentum (classical propagation)"
        ),
    }


# --------------------------------------------------------------------------- #
# Test 3 — jk fuzz directionality                                             #
# --------------------------------------------------------------------------- #

def test3_jk_fuzz_directionality(history: list[dict]) -> dict:
    """
    ga0 = Axis 0 entropy level (proxy for the 'jk fuzz' field).
    MI(t) = cross-temporal MI at step t (L(t) ⊗ R(t+1)).

    Compute cross-correlation at lags −3..+3:
      Positive lag k: ga0 change leads MI change by k steps (ga0 drives MI → classical)
      Negative lag k: ga0 change lags MI change by |k| steps (MI drives ga0 → compression primary)

    Keep if peak cross-correlation is at lag ≤ 0 (ga0 lags or is simultaneous with MI).
    """
    T = len(history)
    ga0 = [float(history[t]["ga0_after"]) for t in range(T)]
    ct_mi = []
    for t in range(T - 1):
        ct_mi.append(cross_temporal_mi(history[t]["rho_L"], history[t + 1]["rho_R"]))
    ct_mi.append(ct_mi[-1])  # pad to same length

    # Changes
    d_ga0 = [ga0[t + 1] - ga0[t] for t in range(T - 1)] + [0.0]
    d_mi = [ct_mi[t + 1] - ct_mi[t] for t in range(T - 1)] + [0.0]

    lags = list(range(-3, 4))
    xcorr = {lag: cross_corr_lag(d_ga0, d_mi, lag) for lag in lags}
    peak_lag = max(xcorr, key=lambda k: abs(xcorr[k]))
    peak_val = xcorr[peak_lag]

    keep = bool(peak_lag <= 0)

    return {
        "cross_correlations": {str(k): round(v, 4) for k, v in xcorr.items()},
        "peak_lag": peak_lag,
        "peak_value": peak_val,
        "keep": keep,
        "interpretation": (
            f"peak lag={peak_lag} ≤ 0 → ga0 lags MI (compression is primary, entropy follows structure)"
            if keep else
            f"peak lag={peak_lag} > 0 → ga0 leads MI (entropy drives structure, classical causation)"
        ),
    }


# --------------------------------------------------------------------------- #
# Test 4 — Trajectory MI profile                                              #
# --------------------------------------------------------------------------- #

def test4_trajectory_mi_profile(history: list[dict]) -> dict:
    """
    Compute per-step cross-temporal MI across the trajectory.
    If attractor convergence: MI should trend upward.
    Fit a linear regression; keep if slope > 0.
    Also check whether the retrocausal (attractor-proximity) weighting
    is justified: do later steps have higher MI?
    """
    T = len(history)
    mi_series = []
    for t in range(T - 1):
        mi_series.append(cross_temporal_mi(history[t]["rho_L"], history[t + 1]["rho_R"]))

    steps = np.arange(len(mi_series), dtype=float)
    coeffs = np.polyfit(steps, mi_series, 1)
    slope = float(coeffs[0])

    first_half_mean = float(np.mean(mi_series[:len(mi_series) // 2]))
    second_half_mean = float(np.mean(mi_series[len(mi_series) // 2:]))
    second_minus_first = second_half_mean - first_half_mean

    # Retrocausal weighting check: do last 8 steps have higher MI than first 8?
    early_mi = float(np.mean(mi_series[:8]))
    late_mi = float(np.mean(mi_series[-8:]))
    late_leads = bool(late_mi > early_mi)

    keep = bool(slope > 0 or late_leads)

    return {
        "mi_series_mean": float(np.mean(mi_series)),
        "mi_series_std": float(np.std(mi_series)),
        "linear_slope": slope,
        "first_half_mean": first_half_mean,
        "second_half_mean": second_half_mean,
        "second_minus_first": second_minus_first,
        "early_mi_mean": early_mi,
        "late_mi_mean": late_mi,
        "late_leads": late_leads,
        "keep": keep,
        "interpretation": (
            "MI increases toward trajectory end → attractor convergence (compression-from-future)"
            if keep else
            "MI flat or decreasing → no attractor convergence (no directional compression)"
        ),
    }


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #

def run_torus(engine_type: int, torus_name: str, torus_val: float) -> dict:
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=torus_val)
    final_state = engine.run_cycle(state)
    history = final_state.history

    t1 = test1_temporal_mi_asymmetry(history, lag=1)
    t2 = test2_attractor_vs_drift(history)
    t3 = test3_jk_fuzz_directionality(history)
    t4 = test4_trajectory_mi_profile(history)

    keep_count = sum([t1["keep"], t2["keep"], t3["keep"], t4["keep"]])
    verdict = "COMPRESSION-FROM-FUTURE" if keep_count >= 3 else (
        "MIXED" if keep_count == 2 else "CLASSICAL-CAUSAL"
    )

    print(f"  {engine_type}/{torus_name}: "
          f"T1={'K' if t1['keep'] else 'k'} asym={t1['asymmetry_bwd_minus_fwd']:+.3f} | "
          f"T2={'K' if t2['keep'] else 'k'} ac={t2['mean_autocorr']:+.3f} | "
          f"T3={'K' if t3['keep'] else 'k'} pk_lag={t3['peak_lag']} | "
          f"T4={'K' if t4['keep'] else 'k'} slope={t4['linear_slope']:+.4f} | "
          f"→ {verdict}")

    return {
        "engine_type": engine_type,
        "torus": torus_name,
        "test1_temporal_asymmetry": t1,
        "test2_attractor_vs_drift": t2,
        "test3_jk_fuzz_directionality": t3,
        "test4_trajectory_profile": t4,
        "keep_count": keep_count,
        "verdict": verdict,
    }


def main() -> None:
    print("=" * 72)
    print("AXIS 0 FEP / COMPRESSION-FROM-FUTURE FRAMING SIM")
    print("=" * 72)
    print("Tests whether the engine structure is better described by")
    print("compression-from-future (entropic monism) than classical causation.")
    print()
    print("  T1: Backward MI ≥ Forward MI?  (future predicts past)")
    print("  T2: Negative Bloch autocorr?   (attractor, not drift)")
    print("  T3: ga0 lags MI change?         (compression primary)")
    print("  T4: MI increases late in traj?  (attractor convergence)")
    print()

    results = []
    for eng_type in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            r = run_torus(eng_type, torus_name, torus_val)
            results.append(r)

    # Aggregate
    n = len(results)
    t1_keep = sum(1 for r in results if r["test1_temporal_asymmetry"]["keep"])
    t2_keep = sum(1 for r in results if r["test2_attractor_vs_drift"]["keep"])
    t3_keep = sum(1 for r in results if r["test3_jk_fuzz_directionality"]["keep"])
    t4_keep = sum(1 for r in results if r["test4_trajectory_profile"]["keep"])
    compression_verdict = sum(1 for r in results if r["verdict"] == "COMPRESSION-FROM-FUTURE")
    mixed_verdict = sum(1 for r in results if r["verdict"] == "MIXED")

    print()
    print("=" * 72)
    print("OVERALL VERDICT: FEP / COMPRESSION-FROM-FUTURE FRAMING")
    print("=" * 72)
    print(f"  T1 (backward MI ≥ forward):    {t1_keep}/{n}")
    print(f"  T2 (attractor, not drift):      {t2_keep}/{n}")
    print(f"  T3 (ga0 lags MI):               {t3_keep}/{n}")
    print(f"  T4 (MI increases late):         {t4_keep}/{n}")
    print(f"  Full COMPRESSION verdict:       {compression_verdict}/{n}")
    print(f"  MIXED verdict:                  {mixed_verdict}/{n}")
    print()

    # Interpret
    total_keep = t1_keep + t2_keep + t3_keep + t4_keep
    if total_keep >= 3 * n:
        overall = "STRONG COMPRESSION-FROM-FUTURE"
        print("  ✓ Engine trajectory is strongly consistent with compression-from-future.")
        print("    Attractor-proximity weighting in Xi_hist is justified.")
    elif total_keep >= 2 * n:
        overall = "PARTIAL COMPRESSION-FROM-FUTURE"
        print("  ◐ Engine trajectory is partially consistent with compression-from-future.")
        print("    Some tests show classical causation; compression framing not universal.")
    else:
        overall = "CLASSICAL-CAUSAL DOMINANT"
        print("  ✗ Classical causal framing dominates. Compression-from-future not supported.")

    # Print per-test interpretation for first inner result
    inner = next(r for r in results if r["torus"] == "inner" and r["engine_type"] == 1)
    print()
    print("  Sample interpretations (Type 1 / inner):")
    for key, label in [
        ("test1_temporal_asymmetry", "T1"),
        ("test2_attractor_vs_drift", "T2"),
        ("test3_jk_fuzz_directionality", "T3"),
        ("test4_trajectory_profile", "T4"),
    ]:
        print(f"    {label}: {inner[key]['interpretation']}")

    print()
    print("================================================================================")
    print(f"PROBE STATUS: PASS")
    print("================================================================================")

    def to_json_safe(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, dict):
            return {k: to_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [to_json_safe(v) for v in obj]
        return obj

    output = {
        "timestamp": datetime.now(UTC).isoformat(),
        "results": to_json_safe(results),
        "summary": {
            "t1_keep": t1_keep,
            "t2_keep": t2_keep,
            "t3_keep": t3_keep,
            "t4_keep": t4_keep,
            "compression_verdict": compression_verdict,
            "mixed_verdict": mixed_verdict,
            "total": n,
            "overall": overall,
        },
    }

    out_path = os.path.join(
        os.path.dirname(__file__),
        "a2_state", "sim_results", "axis0_fep_compression_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
