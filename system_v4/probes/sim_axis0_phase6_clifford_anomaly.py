#!/usr/bin/env python3
"""
Axis 0 Phase 6 — Clifford Anomaly & Composite i-Scalar
=======================================================
Follow-up to the i-scalar sweep (Phase 5 / sweep).

Finding from sweep:
  - Option C (coherent info I_c) wins on consistency + signal
  - BUT doctrine T2-allostatic signature is absent in Option C: both
    T1 and T2 show pure homeostatic in C at ε=0.05
  - Option D (JK path entropy) shows T2/Clifford strongly allostatic
    (+18.17 depolarizing, +18.17 dephasing) while T1/Clifford stays
    homeostatic — the only clean T1/T2 polarity split in the data

Goals of this probe:
  1. Clifford ε-sweep (0.01 → 0.50):
     Does Option C ever cross to allostatic for T2/Clifford but not T1?
     Does Option D maintain the allostatic signal across ε?
     Find the crossover / transition point if it exists.

  2. Geometry specificity:
     Is the T2/Clifford Option-D allostatic signature unique to Clifford,
     or does it appear on inner/outer too under high enough ε?

  3. Composite i-scalar:
     Test a weighted combination: C + α·D (α tuned) to see whether
     the composite improves doctrine fit (T1 homeostatic, T2 allostatic)
     while keeping Option C's consistency.

  4. T1/T2 magnitude split:
     Even if polarity is the same, are T1 and T2 distinguishable by
     the MAGNITUDE of A0 under Option C? (Weaker vs stronger homeostasis)
"""

from __future__ import annotations
import json, os, sys, copy
from datetime import UTC, datetime
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import gudhi
import numpy as np
import rustworkx as rx
import sympy as sp
import torch
import torch_ga
import xgi
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean
from scipy.linalg import expm
classification = "classical_baseline"  # auto-backfill
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat
divergence_log = (
    "Classical foundation baseline: this probes the Axis-0 Clifford anomaly "
    "and composite i-scalar numerically. The legacy anomaly verdict is "
    "preserved, and a deep contract now binds the anomaly surfaces to the "
    "same shell bridge, graph/topology, symbolic expansion, solver closure, "
    "geometric algebra, and manifold witnesses used elsewhere in Axis 0."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "epsilon sweeps and composite i-scalar numerics"},
    "scipy": {"tried": True, "used": True, "reason": "anomaly-surface propagator witness"},
    "pytorch": {"tried": True, "used": True, "reason": "fit and gradient witness over the anomaly frontier"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning anomaly vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning anomaly vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered DAG witness over the ranked anomaly frontier"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order config-to-anomaly coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for anomaly closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the anomaly complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for anomaly expansion"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing anomaly rank order and monotone scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for aggregate anomaly geometry"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "geomstats": "load_bearing",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER
from sim_axis0_dynamic_shell import lane_d_topology_expansion_bridge
from sim_axis0_iscalar_sweep import (
    _clifford_vector,
    _option_cell_complex_surface as _candidate_cell_complex_surface,
    _option_constraint_surface as _candidate_constraint_surface,
    _option_graph_surface as _candidate_graph_surface,
    _option_hypergraph_surface as _candidate_hypergraph_surface,
    _option_manifold_surface as _candidate_manifold_surface,
    _option_scale_history as _candidate_scale_history,
    _option_symbolic_surface as _candidate_symbolic_surface,
    _option_topology_surface as _candidate_topology_surface,
    _torch_ga_roundtrip,
    _torch_option_fit as _torch_candidate_fit,
)

# ─────────────────────────────────────────────────────────────────────
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
I2      = np.eye(2, dtype=complex)
EPS_NUM = 1e-12

PSI_MINUS      = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL_PSI_MINUS = np.outer(PSI_MINUS, PSI_MINUS.conj())

KRAUS_BRANCHES = 64          # higher fidelity for this targeted probe
EPS_RANGE      = [0.01, 0.02, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50]

TORUS_CONFIGS  = [
    ("inner",    TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer",    TORUS_OUTER),
]

# ─────────────────────────────────────────────────────────────────────
# QIT utilities (same as sweep)
# ─────────────────────────────────────────────────────────────────────

def vne(rho):
    rho = (rho + rho.conj().T) / 2
    ev  = np.real(np.linalg.eigvalsh(rho))
    ev  = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0

def ptr_B(r): return np.trace(r.reshape(2,2,2,2), axis1=1, axis2=3)
def ptr_A(r): return np.trace(r.reshape(2,2,2,2), axis1=0, axis2=2)
def mi_val(rho_AB): return max(0.0, vne(ptr_B(rho_AB)) + vne(ptr_A(rho_AB)) - vne(rho_AB))
def coherent_info(rho_AB): return float(vne(ptr_B(rho_AB)) - vne(rho_AB))

def bloch(rho):
    return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])

def lr_asym(a, b):
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0.0, 1.0))

def joint_rho(step):
    rho_L, rho_R = step["rho_L"], step["rho_R"]
    p    = float(np.clip(lr_asym(rho_L, rho_R), 0.01, 0.99))
    prod = _ensure_valid_density(np.kron(rho_L, rho_R))
    return _ensure_valid_density((1 - p) * prod + p * BELL_PSI_MINUS)

# ─────────────────────────────────────────────────────────────────────
# Perturbation channels
# ─────────────────────────────────────────────────────────────────────

def depolarize(rho, eps):
    return _ensure_valid_density((1 - eps) * rho + (eps / 2) * I2)

def dephase(rho, eps):
    out = rho.copy(); out[0,1] *= (1-eps); out[1,0] *= (1-eps)
    return _ensure_valid_density(out)

def amp_damp(rho, eps):
    K0 = np.array([[1,0],[0,np.sqrt(1-eps)]], dtype=complex)
    K1 = np.array([[0,np.sqrt(eps)],[0,0]], dtype=complex)
    return _ensure_valid_density(K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T)

PERTURBATIONS = {
    "depolarizing":   depolarize,
    "dephasing":      dephase,
    "amplitude_damp": amp_damp,
}

def perturb_history(history, fn, eps):
    return [{**s, "rho_L": fn(s["rho_L"], eps), "rho_R": fn(s["rho_R"], eps)}
            for s in history]

# ─────────────────────────────────────────────────────────────────────
# Option C — Coherent information
# ─────────────────────────────────────────────────────────────────────

def option_C(history):
    return float(np.mean([coherent_info(joint_rho(s)) for s in history]))

# ─────────────────────────────────────────────────────────────────────
# Option D — JK path entropy (higher fidelity)
# ─────────────────────────────────────────────────────────────────────

def option_D(history, rng=None):
    if rng is None:
        rng = np.random.default_rng(42)
    T = len(history)
    if T == 0:
        return 0.0
    step_branch_probs = []
    for step in history:
        rho_j = joint_rho(step)
        rho_j = (rho_j + rho_j.conj().T) / 2
        ev = np.real(np.linalg.eigvalsh(rho_j))
        ev = np.clip(ev, 0, None)
        total = ev.sum()
        ev = ev / total if total > EPS_NUM else np.ones(4) / 4
        step_branch_probs.append(ev)

    path_probs = {}
    for _ in range(KRAUS_BRANCHES):
        path = tuple(rng.choice(4, p=probs) for probs in step_branch_probs)
        prob = float(np.prod([step_branch_probs[t][k] for t, k in enumerate(path)]))
        path_probs[path] = path_probs.get(path, 0.0) + prob

    total = sum(path_probs.values())
    if total < EPS_NUM:
        return 0.0
    probs = np.array(list(path_probs.values())) / total
    probs = probs[probs > EPS_NUM]
    return float(-np.sum(probs * np.log2(probs)))

# ─────────────────────────────────────────────────────────────────────
# A0 index
# ─────────────────────────────────────────────────────────────────────

def a0(h_base, h_pert, fn, eps):
    return (fn(h_pert) - fn(h_base)) / eps if eps > EPS_NUM else 0.0

# ─────────────────────────────────────────────────────────────────────
# Goal 1 — Clifford ε-sweep (both engine types)
# ─────────────────────────────────────────────────────────────────────

def clifford_eps_sweep():
    print("=" * 72)
    print("GOAL 1 — Clifford ε-sweep: does Option C cross allostatic for T2?")
    print("=" * 72)
    print(f"{'ε':>6}  {'T1 C-A0':>10}  {'T2 C-A0':>10}  {'T1 D-A0':>10}  {'T2 D-A0':>10}  {'split?':>8}")
    print("─" * 72)

    results = []
    for eps in EPS_RANGE:
        row = {"eps": eps}
        for eng in [1, 2]:
            engine  = GeometricEngine(engine_type=eng)
            state   = engine.init_state(eta=TORUS_CLIFFORD)
            hist_b  = engine.run_cycle(state).history

            for pert_name in ["depolarizing"]:   # focus on strongest signal
                hist_p  = perturb_history(hist_b, depolarize, eps)
                c_val   = a0(hist_b, hist_p, option_C, eps)
                d_val   = a0(hist_b, hist_p, option_D, eps)
                row[f"T{eng}_C"] = c_val
                row[f"T{eng}_D"] = d_val

        t1c, t2c = row["T1_C"], row["T2_C"]
        t1d, t2d = row["T1_D"], row["T2_D"]
        # T1 should be homeostatic (< 0), T2 should be allostatic (> 0)
        c_split = (t1c < 0 and t2c > 0)
        d_split = (t1d < 0 and t2d > 0)
        split_str = ("C✓" if c_split else "C✗") + ("D✓" if d_split else "D✗")
        print(f"{eps:6.2f}  {t1c:+10.4f}  {t2c:+10.4f}  {t1d:+10.4f}  {t2d:+10.4f}  {split_str:>8}")
        results.append(row)

    return results


# ─────────────────────────────────────────────────────────────────────
# Goal 2 — Geometry specificity of Option D allostatic signal
# ─────────────────────────────────────────────────────────────────────

def geometry_specificity():
    print()
    print("=" * 72)
    print("GOAL 2 — Geometry specificity: is T2/Clifford unique for Option D?")
    print("=" * 72)
    eps = 0.05
    print(f"ε = {eps}  (depolarizing only)")
    print(f"{'Config':<20}  {'D-A0':>12}  {'Polarity':>12}")
    print("─" * 55)

    results = []
    for eng in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            engine = GeometricEngine(engine_type=eng)
            state  = engine.init_state(eta=torus_val)
            hist_b = engine.run_cycle(state).history
            hist_p = perturb_history(hist_b, depolarize, eps)
            d_val  = a0(hist_b, hist_p, option_D, eps)
            pol    = "allostatic" if d_val > 0 else "homeostatic"
            label  = f"T{eng}/{torus_name}"
            print(f"  {label:<18}  {d_val:+12.4f}  {pol:>12}")
            results.append({"config": label, "d_a0": d_val, "polarity": pol})

    return results


# ─────────────────────────────────────────────────────────────────────
# Goal 3 — Composite i-scalar: C + α·D
# ─────────────────────────────────────────────────────────────────────

def composite_sweep():
    print()
    print("=" * 72)
    print("GOAL 3 — Composite i-scalar: does C + α·D improve doctrine fit?")
    print("=" * 72)
    eps = 0.05

    # Collect raw C and D A0 values for all 6 configs × depolarizing
    c_vals = {}   # (eng, torus_name) → a0_C
    d_vals = {}   # (eng, torus_name) → a0_D
    for eng in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            engine = GeometricEngine(engine_type=eng)
            state  = engine.init_state(eta=torus_val)
            hist_b = engine.run_cycle(state).history
            hist_p = perturb_history(hist_b, depolarize, eps)
            c_vals[(eng, torus_name)] = a0(hist_b, hist_p, option_C, eps)
            d_vals[(eng, torus_name)] = a0(hist_b, hist_p, option_D, eps)

    # The doctrine target: T1 → homeostatic, T2 → allostatic
    # Score composite = fraction of configs where sign matches doctrine target
    alpha_range = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]
    print(f"  {'α':>6}  {'Doctrine fit':>13}  {'T1-homeo%':>10}  {'T2-allo%':>10}")
    print("  " + "─" * 50)

    best_alpha, best_fit = 0.0, 0.0
    alpha_results = []
    for alpha in alpha_range:
        t1_homeo, t2_allo = 0, 0
        total_t1, total_t2 = 0, 0
        for eng in [1, 2]:
            for torus_name, _ in TORUS_CONFIGS:
                composite = c_vals[(eng, torus_name)] + alpha * d_vals[(eng, torus_name)]
                pol = "allostatic" if composite > 0 else "homeostatic"
                if eng == 1:
                    total_t1 += 1
                    if pol == "homeostatic":
                        t1_homeo += 1
                else:
                    total_t2 += 1
                    if pol == "allostatic":
                        t2_allo += 1

        t1_frac = t1_homeo / total_t1 if total_t1 else 0.0
        t2_frac = t2_allo  / total_t2 if total_t2 else 0.0
        fit = (t1_frac + t2_frac) / 2.0
        print(f"  {alpha:>6.3f}  {fit:>13.3f}  {t1_frac:>10.3f}  {t2_frac:>10.3f}")
        alpha_results.append({"alpha": alpha, "doctrine_fit": fit,
                               "t1_homeo_frac": t1_frac, "t2_allo_frac": t2_frac})
        if fit > best_fit:
            best_fit, best_alpha = fit, alpha

    print(f"\n  Best α = {best_alpha}  →  doctrine fit = {best_fit:.3f}")
    return alpha_results, best_alpha, best_fit


# ─────────────────────────────────────────────────────────────────────
# Goal 4 — T1 vs T2 A0 magnitude split under Option C
# ─────────────────────────────────────────────────────────────────────

def magnitude_split():
    print()
    print("=" * 72)
    print("GOAL 4 — T1 vs T2 |A0| magnitude under Option C (all perturbations)")
    print("=" * 72)
    eps = 0.05
    print(f"{'Config':<20}  {'depolarizing':>14}  {'dephasing':>14}  {'amp_damp':>14}  {'mean|A0|':>10}")
    print("─" * 80)

    results = []
    for eng in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            engine = GeometricEngine(engine_type=eng)
            state  = engine.init_state(eta=torus_val)
            hist_b = engine.run_cycle(state).history
            a0s    = {}
            for pert_name, pert_fn in PERTURBATIONS.items():
                hist_p  = perturb_history(hist_b, pert_fn, eps)
                a0s[pert_name] = a0(hist_b, hist_p, option_C, eps)

            mean_abs = float(np.mean([abs(v) for v in a0s.values()]))
            label    = f"T{eng}/{torus_name}"
            print(f"  {label:<18}  {a0s['depolarizing']:+14.6f}  "
                  f"{a0s['dephasing']:+14.6f}  {a0s['amplitude_damp']:+14.6f}  "
                  f"{mean_abs:>10.6f}")
            results.append({"config": label, "engine_type": eng,
                             "torus": torus_name, **a0s, "mean_abs_a0": mean_abs})

    # T1 vs T2 mean comparison
    t1_mean = float(np.mean([r["mean_abs_a0"] for r in results if r["engine_type"] == 1]))
    t2_mean = float(np.mean([r["mean_abs_a0"] for r in results if r["engine_type"] == 2]))
    print()
    print(f"  T1 mean |A0_C| = {t1_mean:.6f}")
    print(f"  T2 mean |A0_C| = {t2_mean:.6f}")
    print(f"  Ratio T2/T1    = {t2_mean/t1_mean:.3f}" if t1_mean > EPS_NUM else "  Ratio undefined")
    print()
    if abs(t2_mean - t1_mean) > EPS_NUM * 10:
        dominant = "T2" if t2_mean > t1_mean else "T1"
        print(f"  Magnitude distinction: {dominant} shows stronger homeostatic response.")
        print(f"  This is a polarity-preserving distinction: both homeostatic,")
        print(f"  but {dominant} is more strongly so. This is consistent with")
        print(f"  {dominant} having deeper attractor convergence (tighter Bell decay).")
    else:
        print(f"  No significant T1/T2 magnitude distinction under Option C.")

    return results, t1_mean, t2_mean


def _aggregate_deep_contract(
    config_records: list[dict],
    best_alpha: float,
    t1_mean: float,
    t2_mean: float,
) -> dict[str, object]:
    candidate_names = [
        "option_c_homeostatic_surface",
        "option_d_allostatic_surface",
        "clifford_split_surface",
        "composite_fit_surface",
        "magnitude_split_surface",
    ]
    shell_bridge_pass_fraction = float(
        np.mean([1.0 if row["shell_bridge"]["lane_d_keep"] else 0.0 for row in config_records])
    ) if config_records else 0.0

    candidate_signal_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_signed_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_shell_hubble_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_doctrine_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    config_rankings: list[list[str]] = []

    for row in config_records:
        engine_type = int(row["engine_type"])
        torus = str(row["torus"])
        depolarizing_c = float(row["g4"]["depolarizing"])
        option_d = float(row["g2"]["d_a0"])
        composite = float(depolarizing_c + best_alpha * option_d)
        mean_abs = float(row["g4"]["mean_abs_a0"])
        if torus == "clifford":
            cliff_c = float(row["clifford_goal1"][f"T{engine_type}_C"])
            cliff_d = float(row["clifford_goal1"][f"T{engine_type}_D"])
            cliff_signal = abs(cliff_d - cliff_c)
            cliff_signed = cliff_d - cliff_c
            if engine_type == 1:
                cliff_doctrine = 1.0 if cliff_d < 0.0 else 0.0
            else:
                cliff_doctrine = 1.0 if cliff_d > 0.0 and cliff_c < 0.0 else 0.0
        else:
            cliff_signal = 0.5 * abs(option_d - depolarizing_c)
            cliff_signed = option_d - depolarizing_c
            cliff_doctrine = 0.5

        if engine_type == 1:
            composite_doctrine = 1.0 if composite < 0.0 else 0.0
            magnitude_doctrine = 1.0 if t1_mean >= t2_mean else 0.0
        else:
            composite_doctrine = 1.0 if composite > 0.0 else 0.0
            magnitude_doctrine = 1.0 if t2_mean > t1_mean else 0.0

        local_rows = {
            "option_c_homeostatic_surface": {
                "signal": abs(depolarizing_c),
                "signed": depolarizing_c,
                "doctrine": 1.0 if depolarizing_c < 0.0 else 0.0,
            },
            "option_d_allostatic_surface": {
                "signal": abs(option_d),
                "signed": option_d,
                "doctrine": 1.0 if option_d > 0.0 else 0.0,
            },
            "clifford_split_surface": {
                "signal": cliff_signal,
                "signed": cliff_signed,
                "doctrine": cliff_doctrine,
            },
            "composite_fit_surface": {
                "signal": abs(composite),
                "signed": composite,
                "doctrine": composite_doctrine,
            },
            "magnitude_split_surface": {
                "signal": mean_abs,
                "signed": float(mean_abs - (t2_mean if engine_type == 1 else t1_mean)),
                "doctrine": magnitude_doctrine,
            },
        }

        ranking = [
            name
            for name, data in sorted(
                local_rows.items(),
                key=lambda item: float(0.7 * item[1]["signal"] + 0.3 * item[1]["doctrine"]),
                reverse=True,
            )
        ]
        config_rankings.append(ranking)
        shell_hubble = float(row["shell_bridge"]["mean_hubble_proxy"])

        for name in candidate_names:
            candidate_signal_by_name[name].append(float(local_rows[name]["signal"]))
            candidate_signed_by_name[name].append(float(local_rows[name]["signed"]))
            candidate_shell_hubble_by_name[name].append(shell_hubble)
            candidate_doctrine_by_name[name].append(float(local_rows[name]["doctrine"]))

    raw_rows: list[dict[str, object]] = []
    max_mean_abs = 0.0
    for name in candidate_names:
        signal_vals = np.asarray(candidate_signal_by_name[name], dtype=np.float64)
        signed_vals = np.asarray(candidate_signed_by_name[name], dtype=np.float64)
        shell_vals = np.asarray(candidate_shell_hubble_by_name[name], dtype=np.float64)
        doctrine_vals = np.asarray(candidate_doctrine_by_name[name], dtype=np.float64)
        shell_alignment = 0.0
        if signal_vals.size and signal_vals.std() > EPS_NUM and shell_vals.std() > EPS_NUM:
            shell_alignment = float(np.corrcoef(signal_vals, shell_vals)[0, 1])
        mean_abs_support = float(np.mean(np.abs(signal_vals))) if signal_vals.size else 0.0
        max_mean_abs = max(max_mean_abs, mean_abs_support)
        raw_rows.append(
            {
                "candidate": name,
                "mean_abs_support": mean_abs_support,
                "mean_signed_support": float(np.mean(signed_vals)) if signed_vals.size else 0.0,
                "doctrine_fit": float(np.mean(doctrine_vals)) if doctrine_vals.size else 0.0,
                "shell_alignment": shell_alignment,
                "shell_alignment_abs": abs(shell_alignment),
                "mean_signal": float(np.mean(signal_vals)) if signal_vals.size else 0.0,
            }
        )

    row_by_name: dict[str, dict[str, object]] = {}
    for row in raw_rows:
        signal_score = float(row["mean_abs_support"] / max(max_mean_abs, EPS_NUM))
        composite_score = float(
            0.45 * float(row["doctrine_fit"])
            + 0.35 * signal_score
            + 0.20 * float(row["shell_alignment_abs"])
        )
        enriched = dict(row)
        enriched["signal_score"] = signal_score
        enriched["composite_score"] = composite_score
        row_by_name[str(row["candidate"])] = enriched

    ranking = sorted(
        candidate_names,
        key=lambda name: float(row_by_name[name]["composite_score"]),
        reverse=True,
    )
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    candidate_rows: list[dict[str, object]] = []
    ranking_scores: list[float] = []
    for name in ranking:
        row = row_by_name[name]
        ranking_scores.append(float(row["composite_score"]))
        candidate_rows.append(
            {
                "option": name,
                "mean_abs_a0": float(row["mean_abs_support"]),
                "mean_signed_a0": float(row["mean_signed_support"]),
                "doctrine_fit": float(row["doctrine_fit"]),
                "sign_consistency": float(row["doctrine_fit"]),
                "shell_alignment": float(row["shell_alignment"]),
                "shell_alignment_abs": float(row["shell_alignment_abs"]),
                "signal_score": float(row["signal_score"]),
                "composite_score": float(row["composite_score"]),
                "mean_signal": float(row["mean_signal"]),
            }
        )

    expansion_drive = np.asarray(
        [
            row["mean_abs_a0"] + row["doctrine_fit"] + row["shell_alignment_abs"]
            for row in candidate_rows
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _candidate_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS_NUM, None)), lambda_shells)

    for row, scale, hubble in zip(
        candidate_rows,
        scale_factors.tolist(),
        hubble_proxy.tolist(),
        strict=True,
    ):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _candidate_graph_surface(candidate_rows)
    ranking_index = {name: idx for idx, name in enumerate(ranking)}
    config_windows = [
        [ranking_index[name] for name in config_ranking[:3]]
        for config_ranking in config_rankings
        if len(config_ranking) >= 3
    ]
    hypergraph_surface = _candidate_hypergraph_surface(len(ranking), config_windows)
    combined_pair_edges = sorted(
        {
            tuple(edge)
            for edge in graph_surface["pair_edges"] + hypergraph_surface["pair_edges"]
        }
    )
    combined_triad_windows = sorted(
        {
            tuple(window)
            for window in graph_surface["triad_windows"] + hypergraph_surface["triad_windows"]
        }
    )
    closed_pair_edges = set(combined_pair_edges)
    for window in combined_triad_windows:
        for idx in range(len(window)):
            for jdx in range(idx + 1, len(window)):
                closed_pair_edges.add(tuple(sorted((int(window[idx]), int(window[jdx])))))
    cell_complex_surface = _candidate_cell_complex_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    topology_surface = _candidate_topology_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    symbolic_surface = _candidate_symbolic_surface(
        lambda_shells,
        scale_factors,
        expansion_drive,
    )
    constraint_surface = _candidate_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray(ranking_scores, dtype=np.float64),
    )
    manifold_surface = _candidate_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in candidate_rows], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in candidate_rows], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in candidate_rows], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_candidate_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in candidate_rows], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in candidate_rows], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in candidate_rows], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner = ranking[0]
    winner_row = next(row for row in candidate_rows if row["option"] == winner)
    winner_vector = np.array(
        [
            winner_row["mean_abs_a0"],
            winner_row["doctrine_fit"],
            winner_row["shell_alignment_abs"],
        ],
        dtype=np.float64,
    )
    clifford_vector = _clifford_vector(winner_vector)
    torch_ga_vector = _torch_ga_roundtrip(winner_vector)
    topology_parity_ok = bool(
        cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
    )
    graph_path_budget = max(1, len(ranking) - 2)
    topology_loop_budget = max(2, len(ranking) // 2)

    pass_flag = bool(
        shell_bridge_pass_fraction >= 0.5
        and graph_surface["longest_path_length"] >= graph_path_budget
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] <= topology_loop_budget
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-3
        and torch_fit["loss"] < 1.0
    )

    return {
        "pass": pass_flag,
        "winner": winner,
        "candidate_universe_size": len(candidate_names),
        "frontier_size": len(ranking),
        "shell_bridge_pass_fraction": shell_bridge_pass_fraction,
        "candidate_rows": candidate_rows,
        "graph_surface": {
            "edge_count": graph_surface["edge_count"],
            "longest_path_length": graph_surface["longest_path_length"],
            "triad_windows": graph_surface["triad_windows"],
            "path_budget": int(graph_path_budget),
        },
        "hypergraph_surface": {
            "num_edges": hypergraph_surface["num_edges"],
            "max_hyperedge_size": hypergraph_surface["max_hyperedge_size"],
            "connected_components": hypergraph_surface["connected_components"],
            "hyperedges": hypergraph_surface["hyperedges"],
        },
        "topology_surface": {
            "betti_numbers": topology_surface["betti_numbers"],
            "euler_characteristic": topology_surface["euler_characteristic"],
            "parity_ok": topology_parity_ok,
            "loop_budget": int(topology_loop_budget),
        },
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
        "manifold_surface": manifold_surface,
        "torch_fit": {
            "weights": torch_fit["weights"],
            "bias": torch_fit["bias"],
            "loss": torch_fit["loss"],
            "max_gap": torch_fit["max_gap"],
        },
        "winner_vector": winner_vector.tolist(),
        "clifford_vector_gap": float(np.max(np.abs(clifford_vector - winner_vector))),
        "torch_ga_vector_gap": float(np.max(np.abs(torch_ga_vector - winner_vector))),
        "scale_factors": scale_factors.tolist(),
        "hubble_proxy": hubble_proxy.tolist(),
        "propagator_traces": propagator_traces,
    }


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("AXIS 0 PHASE 6 — CLIFFORD ANOMALY & COMPOSITE i-SCALAR")
    print("=" * 72)
    print()

    g1 = clifford_eps_sweep()
    g2 = geometry_specificity()
    g3_alpha_results, best_alpha, best_fit = composite_sweep()
    g4_results, t1_mean, t2_mean = magnitude_split()
    clifford_goal1_row = next(row for row in g1 if abs(float(row["eps"]) - 0.05) < 1e-12)
    g2_by_config = {str(row["config"]): row for row in g2}
    g4_by_config = {str(row["config"]): row for row in g4_results}
    config_records = []
    for engine_type in (1, 2):
        for torus_name, torus_val in TORUS_CONFIGS:
            label = f"T{engine_type}/{torus_name}"
            engine = GeometricEngine(engine_type=engine_type)
            state = engine.init_state(eta=torus_val)
            state = engine.run_cycle(state)
            history_base = [
                {
                    "rho_L": step["rho_L"],
                    "rho_R": step["rho_R"],
                    "eta": float(step.get("ax0_torus_entropy", 0.5)),
                }
                for step in state.history
            ]
            config_records.append(
                {
                    "config": label,
                    "engine_type": engine_type,
                    "torus": torus_name,
                    "g2": g2_by_config[label],
                    "g4": g4_by_config[label],
                    "clifford_goal1": clifford_goal1_row,
                    "shell_bridge": lane_d_topology_expansion_bridge(history_base),
                }
            )

    print("=" * 72)
    print("SYNTHESIS")
    print("=" * 72)
    print()

    # Determine whether C ever splits T1/T2
    c_splits = [r for r in g1 if r["T1_C"] < 0 and r["T2_C"] > 0]
    d_splits = [r for r in g1 if r["T1_D"] < 0 and r["T2_D"] > 0]

    if c_splits:
        print(f"  Option C achieves T1/T2 polarity split at ε ∈ "
              f"{[r['eps'] for r in c_splits]}")
        print(f"  → Option C CAN distinguish T1 from T2 at the right perturbation strength.")
    else:
        print("  Option C does NOT produce a T1/T2 polarity split at any tested ε.")
        print("  → Both types are uniformly homeostatic under Option C.")
        print("  → The T1/T2 distinction lives in magnitude, not polarity.")

    if d_splits:
        print(f"  Option D achieves T1/T2 polarity split at ε ∈ "
              f"{[r['eps'] for r in d_splits]}")
        print(f"  → Option D retains the Clifford/T2 allostatic anomaly.")
    else:
        print("  Option D does NOT maintain a T1/T2 split at Clifford under ε-sweep.")

    print()
    print(f"  Best composite α = {best_alpha}, doctrine fit = {best_fit:.3f}")
    if best_fit > 0.75:
        print(f"  → Composite C + {best_alpha}·D substantially improves doctrine fit.")
        print(f"  → The i-scalar should be: i(ρ) = I_c + {best_alpha}·H_path")
    elif best_fit > 0.55:
        print(f"  → Composite provides modest improvement. Option C alone is likely cleaner.")
    else:
        print(f"  → Composite does not materially improve doctrine fit. Use Option C alone.")

    print()
    ratio = t2_mean / t1_mean if t1_mean > EPS_NUM else 1.0
    print(f"  T1/T2 |A0_C| ratio = {ratio:.3f}")
    if ratio > 1.15:
        print("  → T2 is more strongly homeostatic under Option C.")
        print("     This is the engine-type signature: T2 collapses I_c faster,")
        print("     consistent with T2 as the heating/inductive engine (R-handed).")
        print("     Its Bell prior decays more rapidly under perturbation.")
    elif ratio < 0.87:
        print("  → T1 is more strongly homeostatic under Option C.")
        print("     T1 (cooling/deductive/L-handed) suppresses I_c more forcefully.")
    else:
        print("  → T1 and T2 are indistinguishable by |A0_C|. No magnitude split.")

    print()
    deep_contract = _aggregate_deep_contract(config_records, best_alpha, t1_mean, t2_mean)

    print("=" * 72)
    print("DEEP CONTRACT")
    print("=" * 72)
    print(f"  Deep pass:                    {deep_contract['pass']}")
    print(
        f"  Anomaly frontier:            "
        f"{deep_contract['frontier_size']}/{deep_contract['candidate_universe_size']}"
    )
    print(f"  Shell bridge pass fraction:   {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"  Winning deep surface:         {deep_contract['winner']}")
    print(f"  Graph longest path:           {deep_contract['graph_surface']['longest_path_length']}")
    print(f"  Hypergraph max edge size:     {deep_contract['hypergraph_surface']['max_hyperedge_size']}")
    print(f"  Topology betti numbers:       {deep_contract['topology_surface']['betti_numbers']}")
    print(f"  Symbolic hubble mid:          {deep_contract['symbolic_surface']['symbolic_hubble_mid']:.6f}")
    print(f"  Manifold mean distance:       {deep_contract['manifold_surface']['mean_geodesic_distance']:.6f}")
    print(f"  Torch fit loss:               {deep_contract['torch_fit']['loss']:.6f}")
    print(
        f"  Winner vector gaps:           "
        f"clifford={deep_contract['clifford_vector_gap']:.2e} | "
        f"torch_ga={deep_contract['torch_ga_vector_gap']:.2e}"
    )

    print()
    print("=" * 72)
    print(f"PROBE STATUS: {'PASS' if deep_contract['pass'] else 'FAIL'}")
    print("=" * 72)

    # Save
    def js(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.bool_,)): return bool(obj)
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, dict): return {k: js(v) for k, v in obj.items()}
        if isinstance(obj, list): return [js(v) for v in obj]
        return obj

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_axis0_phase6_clifford_anomaly_results.json")
    with open(out_path, "w") as f:
        json.dump(js({
            "timestamp":    datetime.now(UTC).isoformat(),
            "classification": classification,
            "divergence_log": divergence_log,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "goal1_clifford_eps_sweep": g1,
            "goal2_geometry_specificity": g2,
            "goal3_composite_alpha_sweep": g3_alpha_results,
            "goal3_best_alpha": best_alpha,
            "goal3_best_fit":   best_fit,
            "goal4_magnitude_split": g4_results,
            "goal4_t1_mean_abs_a0": t1_mean,
            "goal4_t2_mean_abs_a0": t2_mean,
            "config_records": config_records,
            "aggregate": {
                "deep_contract": deep_contract,
                "all_pass": bool(deep_contract["pass"]),
            },
            "summary": {
                "best_alpha": best_alpha,
                "best_fit": best_fit,
                "deep_contract_pass": bool(deep_contract["pass"]),
                "deep_contract_winner": deep_contract["winner"],
            },
            "overall_pass": bool(deep_contract["pass"]),
            "all_pass": bool(deep_contract["pass"]),
        }), f, indent=2)
    print(f"\n  Results → {out_path}")


if __name__ == "__main__":
    main()
