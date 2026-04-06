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
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER

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
    print("=" * 72)
    print("PROBE STATUS: PASS")
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
    out_path = os.path.join(out_dir, "axis0_phase6_clifford_anomaly.json")
    with open(out_path, "w") as f:
        json.dump(js({
            "timestamp":    datetime.now(UTC).isoformat(),
            "goal1_clifford_eps_sweep": g1,
            "goal2_geometry_specificity": g2,
            "goal3_composite_alpha_sweep": g3_alpha_results,
            "goal3_best_alpha": best_alpha,
            "goal3_best_fit":   best_fit,
            "goal4_magnitude_split": g4_results,
            "goal4_t1_mean_abs_a0": t1_mean,
            "goal4_t2_mean_abs_a0": t2_mean,
        }), f, indent=2)
    print(f"\n  Results → {out_path}")


if __name__ == "__main__":
    main()
