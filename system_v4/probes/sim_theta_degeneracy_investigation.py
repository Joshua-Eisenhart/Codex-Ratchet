#!/usr/bin/env python3
"""
sim_theta_degeneracy_investigation.py
=====================================

Investigates the suspicious theta degeneracy in the 3-qubit bridge:
fi_theta values pi/4, pi/2, 3pi/4 produce IDENTICAL max I_c across
all dephasing values. Only theta=pi differs. Why?

Four investigations:
  1. Fine theta sweep (50 values, 0.01 to 2*pi) at fixed dephasing=0.05
  2. Operator analysis — are output density matrices identical?
  3. Remove ensure_valid_density — does clipping cause degeneracy?
  4. Remove Fi entirely — does Fe dominate?
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sim_3qubit_bridge_prototype import (
    I2, SIGMA_X, SIGMA_Y, SIGMA_Z,
    partial_trace_keep, von_neumann_entropy, ensure_valid_density,
    build_3q_Ti, build_3q_Fe, build_3q_Te, build_3q_Fi,
    compute_info_measures,
)

# ═══════════════════════════════════════════════════════════════════
# INVESTIGATION 1: Fine theta sweep
# ═══════════════════════════════════════════════════════════════════

def investigation_1_fine_sweep(n_theta=50, deph=0.05, n_cycles=30):
    """Sweep 50 theta values from 0.01 to 2*pi at fixed dephasing."""
    print("\n[INV 1] Fine theta sweep: {} values, deph={}, {} cycles".format(
        n_theta, deph, n_cycles))

    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0  # |000>

    theta_values = np.linspace(0.01, 2 * np.pi, n_theta)
    max_ic_values = []

    for theta in theta_values:
        Ti = build_3q_Ti(strength=deph)
        Fe = build_3q_Fe(strength=1.0, phi=0.4)
        Te = build_3q_Te(strength=deph, q=0.7)
        Fi = build_3q_Fi(strength=1.0, theta=float(theta))

        rho = rho_init.copy()
        best_ic = -999.0

        for c in range(1, n_cycles + 1):
            rho = Ti(rho)
            rho = Fe(rho)
            rho = Te(rho)
            rho = Fi(rho)
            info = compute_info_measures(rho)
            for cut_data in info.values():
                if cut_data["I_c"] > best_ic:
                    best_ic = cut_data["I_c"]

        max_ic_values.append(float(best_ic))

    theta_list = [float(t) for t in theta_values]
    print("  theta range: {:.4f} to {:.4f}".format(theta_list[0], theta_list[-1]))
    print("  max I_c range: {:.8f} to {:.8f}".format(min(max_ic_values), max(max_ic_values)))

    # Identify plateau vs non-plateau
    median_ic = float(np.median(max_ic_values))
    outliers = [(theta_list[i], max_ic_values[i])
                for i in range(len(theta_list))
                if abs(max_ic_values[i] - median_ic) > 0.01]
    print("  Median max I_c: {:.8f}".format(median_ic))
    print("  Outliers (>0.01 from median): {}".format(len(outliers)))
    for t, v in outliers[:10]:
        print("    theta={:.4f}  max_ic={:.8f}".format(t, v))

    return {
        "theta_values": theta_list,
        "max_ic": max_ic_values,
        "median_ic": median_ic,
        "num_outliers": len(outliers),
        "outlier_thetas": [o[0] for o in outliers],
        "outlier_ics": [o[1] for o in outliers],
    }


# ═══════════════════════════════════════════════════════════════════
# INVESTIGATION 2: Operator output analysis
# ═══════════════════════════════════════════════════════════════════

def investigation_2_operator_analysis():
    """For each theta in [pi/4, pi/2, 3pi/4, pi], apply Fi to |000><000|
    and check if output density matrices are identical."""
    print("\n[INV 2] Operator output analysis")

    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0

    thetas = {
        "pi/4": np.pi / 4,
        "pi/2": np.pi / 2,
        "3pi/4": 3 * np.pi / 4,
        "pi": np.pi,
    }

    # 2a: Single Fi application (no ensure_valid_density in the unitary)
    H_int = np.kron(np.kron(SIGMA_X, I2), SIGMA_Z)
    single_outputs = {}
    print("\n  --- Single Fi application (raw unitary, no EVD) ---")
    for name, theta in thetas.items():
        U = np.cos(theta / 2) * np.eye(8, dtype=complex) - 1j * np.sin(theta / 2) * H_int
        rho_out = U @ rho_init @ U.conj().T
        single_outputs[name] = rho_out
        diag = np.real(np.diag(rho_out))
        print("  theta={:6s}  diag={}".format(name, np.round(diag, 6)))

    # Check pairwise differences
    keys = list(thetas.keys())
    pairwise_diffs = {}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            diff = float(np.max(np.abs(single_outputs[keys[i]] - single_outputs[keys[j]])))
            pair = "{} vs {}".format(keys[i], keys[j])
            pairwise_diffs[pair] = diff
            print("  diff({}) = {:.10f}".format(pair, diff))

    outputs_identical = all(v < 1e-10 for v in pairwise_diffs.values())
    print("  All outputs identical? {}".format(outputs_identical))

    # 2b: Population analysis
    print("\n  --- Population analysis: |cos(theta/2)|^2 ---")
    for name, theta in thetas.items():
        pop_000 = np.cos(theta / 2) ** 2
        pop_100 = np.sin(theta / 2) ** 2
        print("  theta={:6s}  P(000)={:.6f}  P(100)={:.6f}".format(
            name, pop_000, pop_100))

    # 2c: Full cycle analysis — run one cycle Ti->Fe->Te->Fi for each theta
    # with WEAK dephasing to see where theta dependence gets killed
    print("\n  --- Full cycle stage-by-stage analysis (deph=0.05) ---")
    stage_outputs = {}
    for name, theta in thetas.items():
        Ti = build_3q_Ti(strength=0.05)
        Fe = build_3q_Fe(strength=1.0, phi=0.4)
        Te = build_3q_Te(strength=0.05, q=0.7)
        Fi = build_3q_Fi(strength=1.0, theta=float(theta))

        rho = rho_init.copy()
        stages = {}

        rho = Ti(rho)
        stages["post_Ti"] = rho.copy()
        rho = Fe(rho)
        stages["post_Fe"] = rho.copy()
        rho = Te(rho)
        stages["post_Te"] = rho.copy()
        rho = Fi(rho)
        stages["post_Fi"] = rho.copy()

        stage_outputs[name] = stages

    # Compare post-Ti, post-Fe, post-Te states (should be identical since
    # Ti, Fe, Te don't depend on theta and input is the same)
    print("\n  Pre-Fi states identical across theta values?")
    ref_key = keys[0]
    for stage_name in ["post_Ti", "post_Fe", "post_Te"]:
        diffs = []
        for k in keys[1:]:
            d = float(np.max(np.abs(
                stage_outputs[ref_key][stage_name] - stage_outputs[k][stage_name])))
            diffs.append(d)
        all_same = all(d < 1e-12 for d in diffs)
        print("  {} : all same = {} (max diff = {:.2e})".format(
            stage_name, all_same, max(diffs)))

    # Now compare post-Fi states
    print("\n  Post-Fi states (after full cycle 1):")
    post_fi_diffs = {}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            diff = float(np.max(np.abs(
                stage_outputs[keys[i]]["post_Fi"] - stage_outputs[keys[j]]["post_Fi"])))
            pair = "{} vs {}".format(keys[i], keys[j])
            post_fi_diffs[pair] = diff
            print("  diff({}) = {:.10f}".format(pair, diff))

    # 2d: Multi-cycle convergence check
    print("\n  --- Multi-cycle convergence (30 cycles, deph=0.05) ---")
    final_rhos = {}
    for name, theta in thetas.items():
        Ti = build_3q_Ti(strength=0.05)
        Fe = build_3q_Fe(strength=1.0, phi=0.4)
        Te = build_3q_Te(strength=0.05, q=0.7)
        Fi = build_3q_Fi(strength=1.0, theta=float(theta))

        rho = rho_init.copy()
        for _ in range(30):
            rho = Ti(rho)
            rho = Fe(rho)
            rho = Te(rho)
            rho = Fi(rho)
        final_rhos[name] = rho
        print("  theta={:6s}  final diag={}".format(
            name, np.round(np.real(np.diag(rho)), 6)))

    final_diffs = {}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            diff = float(np.max(np.abs(final_rhos[keys[i]] - final_rhos[keys[j]])))
            pair = "{} vs {}".format(keys[i], keys[j])
            final_diffs[pair] = diff
    print("  Final state pairwise diffs:")
    for pair, diff in final_diffs.items():
        print("    {} : {:.10f}".format(pair, diff))

    all_final_identical = all(v < 1e-6 for v in final_diffs.values())

    return {
        "single_fi_outputs_identical": outputs_identical,
        "single_fi_pairwise_diffs": pairwise_diffs,
        "post_cycle1_fi_diffs": post_fi_diffs,
        "final_30cycle_diffs": final_diffs,
        "all_final_states_identical": all_final_identical,
        "populations": {
            name: {
                "P_000": float(np.cos(theta / 2) ** 2),
                "P_100": float(np.sin(theta / 2) ** 2),
            }
            for name, theta in thetas.items()
        },
    }


# ═══════════════════════════════════════════════════════════════════
# INVESTIGATION 3: Remove ensure_valid_density
# ═══════════════════════════════════════════════════════════════════

def _apply_Ti_raw(rho, P0, P1, strength):
    """Ti without ensure_valid_density."""
    rho_proj = P0 @ rho @ P0 + P1 @ rho @ P1
    return strength * rho_proj + (1 - strength) * rho


def _apply_unitary_raw(rho, H_int, angle):
    """Unitary rotation without ensure_valid_density."""
    U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_int
    return U @ rho @ U.conj().T


def _apply_Te_raw(rho, P_plus, P_minus, mix):
    """Te without ensure_valid_density."""
    rho_proj = P_plus @ rho @ P_plus + P_minus @ rho @ P_minus
    return (1 - mix) * rho + mix * rho_proj


def investigation_3_no_evd(n_theta=50, deph=0.05, n_cycles=30):
    """Same theta sweep but WITHOUT ensure_valid_density after operators."""
    print("\n[INV 3] Theta sweep WITHOUT ensure_valid_density")

    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0

    # Pre-build fixed operators
    ZZ_I = np.kron(np.kron(SIGMA_Z, SIGMA_Z), I2)
    P0 = (np.eye(8, dtype=complex) + ZZ_I) / 2
    P1 = (np.eye(8, dtype=complex) - ZZ_I) / 2

    XX_I = np.kron(np.kron(SIGMA_X, SIGMA_X), I2)

    YY_I = np.kron(np.kron(SIGMA_Y, SIGMA_Y), I2)
    P_plus = (np.eye(8, dtype=complex) + YY_I) / 2
    P_minus = (np.eye(8, dtype=complex) - YY_I) / 2

    H_Fi = np.kron(np.kron(SIGMA_X, I2), SIGMA_Z)

    theta_values = np.linspace(0.01, 2 * np.pi, n_theta)
    max_ic_no_evd = []
    max_ic_with_evd = []

    for theta in theta_values:
        # --- WITHOUT EVD ---
        rho = rho_init.copy()
        best_ic_raw = -999.0
        valid = True
        for c in range(1, n_cycles + 1):
            rho = _apply_Ti_raw(rho, P0, P1, deph)
            rho = _apply_unitary_raw(rho, XX_I, 0.4)
            rho = _apply_Te_raw(rho, P_plus, P_minus, min(deph * 0.7, 1.0))
            rho = _apply_unitary_raw(rho, H_Fi, float(theta))
            # Force Hermiticity for entropy calc but do NOT clip eigenvalues
            rho_h = (rho + rho.conj().T) / 2
            tr = float(np.real(np.trace(rho_h)))
            if tr > 1e-15:
                rho_h_norm = rho_h / tr
            else:
                valid = False
                break
            # Check for negative eigenvalues
            evals = np.linalg.eigvalsh(rho_h_norm)
            min_eval = float(np.min(evals))
            if min_eval < -1e-10:
                # State has gone non-physical; note this but continue
                pass
            info = compute_info_measures(rho_h_norm)
            for cut_data in info.values():
                if cut_data["I_c"] > best_ic_raw:
                    best_ic_raw = cut_data["I_c"]

        if not valid:
            best_ic_raw = float("nan")
        max_ic_no_evd.append(float(best_ic_raw))

        # --- WITH EVD (standard) ---
        Ti = build_3q_Ti(strength=deph)
        Fe = build_3q_Fe(strength=1.0, phi=0.4)
        Te = build_3q_Te(strength=deph, q=0.7)
        Fi = build_3q_Fi(strength=1.0, theta=float(theta))

        rho = rho_init.copy()
        best_ic_evd = -999.0
        for c in range(1, n_cycles + 1):
            rho = Ti(rho)
            rho = Fe(rho)
            rho = Te(rho)
            rho = Fi(rho)
            info = compute_info_measures(rho)
            for cut_data in info.values():
                if cut_data["I_c"] > best_ic_evd:
                    best_ic_evd = cut_data["I_c"]
        max_ic_with_evd.append(float(best_ic_evd))

    theta_list = [float(t) for t in theta_values]

    # Compare
    diffs = [abs(a - b) for a, b in zip(max_ic_with_evd, max_ic_no_evd)
             if not (np.isnan(a) or np.isnan(b))]
    max_diff = max(diffs) if diffs else float("nan")
    mean_diff = float(np.mean(diffs)) if diffs else float("nan")
    print("  max diff (with vs without EVD): {:.10f}".format(max_diff))
    print("  mean diff: {:.10f}".format(mean_diff))
    evd_causes_degeneracy = max_diff > 0.01

    # Check if degeneracy persists without EVD
    no_evd_clean = [v for v in max_ic_no_evd if not np.isnan(v)]
    if no_evd_clean:
        no_evd_range = max(no_evd_clean) - min(no_evd_clean)
        print("  no-EVD I_c range: {:.8f}".format(no_evd_range))
        no_evd_degenerate = no_evd_range < 0.01
    else:
        no_evd_range = float("nan")
        no_evd_degenerate = False

    return {
        "theta_values": theta_list,
        "with_evd": max_ic_with_evd,
        "without_evd": max_ic_no_evd,
        "max_diff_evd_vs_no_evd": max_diff,
        "mean_diff_evd_vs_no_evd": mean_diff,
        "evd_causes_degeneracy": evd_causes_degeneracy,
        "no_evd_still_degenerate": no_evd_degenerate,
        "no_evd_ic_range": no_evd_range,
    }


# ═══════════════════════════════════════════════════════════════════
# INVESTIGATION 4: Remove Fi entirely
# ═══════════════════════════════════════════════════════════════════

def investigation_4_fi_removed(n_theta=50, deph=0.05, n_cycles=30):
    """Run Ti->Fe->Te only (no Fi). If max I_c matches the degenerate
    plateau, then Fi is irrelevant and Fe dominates."""
    print("\n[INV 4] Fi REMOVED — Ti->Fe->Te only")

    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0

    Ti = build_3q_Ti(strength=deph)
    Fe = build_3q_Fe(strength=1.0, phi=0.4)
    Te = build_3q_Te(strength=deph, q=0.7)

    rho = rho_init.copy()
    best_ic = -999.0
    best_cycle = 0
    best_cut = ""
    trajectory = []

    for c in range(1, n_cycles + 1):
        rho = Ti(rho)
        rho = Fe(rho)
        rho = Te(rho)
        info = compute_info_measures(rho)
        cycle_best = -999.0
        for cut_name, cut_data in info.items():
            if cut_data["I_c"] > best_ic:
                best_ic = cut_data["I_c"]
                best_cycle = c
                best_cut = cut_name
            if cut_data["I_c"] > cycle_best:
                cycle_best = cut_data["I_c"]
        trajectory.append(float(cycle_best))

    print("  No-Fi max I_c: {:.8f} (cycle {}, cut {})".format(
        best_ic, best_cycle, best_cut))

    # Now compare with the WITH-Fi sweep at a few thetas
    theta_samples = [np.pi / 4, np.pi / 2, 3 * np.pi / 4, np.pi]
    with_fi_ics = {}
    for theta in theta_samples:
        Ti2 = build_3q_Ti(strength=deph)
        Fe2 = build_3q_Fe(strength=1.0, phi=0.4)
        Te2 = build_3q_Te(strength=deph, q=0.7)
        Fi2 = build_3q_Fi(strength=1.0, theta=float(theta))

        rho = rho_init.copy()
        best = -999.0
        for c in range(1, n_cycles + 1):
            rho = Ti2(rho)
            rho = Fe2(rho)
            rho = Te2(rho)
            rho = Fi2(rho)
            info = compute_info_measures(rho)
            for cut_data in info.values():
                if cut_data["I_c"] > best:
                    best = cut_data["I_c"]
        label = "theta={:.4f}".format(float(theta))
        with_fi_ics[label] = float(best)
        print("  With Fi ({}): max I_c = {:.8f}".format(label, best))

    fi_irrelevant = all(
        abs(v - best_ic) < 0.001
        for k, v in with_fi_ics.items()
        if "3.1416" not in k  # exclude pi which we know differs
    )
    print("  Fi irrelevant (excl. theta=pi)? {}".format(fi_irrelevant))

    # Check: does Fi at theta~0 match no-Fi?
    Ti_z = build_3q_Ti(strength=deph)
    Fe_z = build_3q_Fe(strength=1.0, phi=0.4)
    Te_z = build_3q_Te(strength=deph, q=0.7)
    Fi_z = build_3q_Fi(strength=1.0, theta=0.001)
    rho = rho_init.copy()
    best_near_zero = -999.0
    for c in range(1, n_cycles + 1):
        rho = Ti_z(rho)
        rho = Fe_z(rho)
        rho = Te_z(rho)
        rho = Fi_z(rho)
        info = compute_info_measures(rho)
        for cut_data in info.values():
            if cut_data["I_c"] > best_near_zero:
                best_near_zero = cut_data["I_c"]
    print("  With Fi (theta~0): max I_c = {:.8f}".format(best_near_zero))
    print("  No-Fi vs theta~0 diff: {:.10f}".format(abs(best_ic - best_near_zero)))

    return {
        "no_fi_max_ic": float(best_ic),
        "no_fi_best_cycle": best_cycle,
        "no_fi_best_cut": best_cut,
        "no_fi_trajectory": trajectory,
        "with_fi_samples": with_fi_ics,
        "fi_near_zero_ic": float(best_near_zero),
        "fi_irrelevant_for_non_pi_thetas": fi_irrelevant,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  THETA DEGENERACY INVESTIGATION")
    print("  Why do pi/4, pi/2, 3pi/4 produce identical max I_c?")
    print("=" * 72)

    results = {}

    # Investigation 1
    results["fine_sweep"] = investigation_1_fine_sweep()

    # Investigation 2
    results["operator_analysis"] = investigation_2_operator_analysis()

    # Investigation 3
    evd_test = investigation_3_no_evd()
    results["ensure_valid_density_test"] = evd_test

    # Investigation 4
    results["fi_removed_test"] = investigation_4_fi_removed()

    # Synthesize diagnosis
    print("\n" + "=" * 72)
    print("  DIAGNOSIS")
    print("=" * 72)

    causes = []

    # Check if single Fi outputs are identical
    if results["operator_analysis"]["single_fi_outputs_identical"]:
        causes.append("Fi produces identical output states for all tested thetas (impossible for distinct thetas, indicates bug)")
    else:
        causes.append("Fi produces DIFFERENT output states per theta (expected)")

    # Check if final states converge
    if results["operator_analysis"]["all_final_states_identical"]:
        causes.append("After 30 cycles, all theta values converge to same fixed point (attractor dominates)")
    else:
        causes.append("Final states differ across thetas (no universal fixed-point convergence)")

    # Check EVD
    if evd_test["evd_causes_degeneracy"]:
        causes.append("ensure_valid_density clipping IS causing artificial degeneracy")
    elif evd_test["no_evd_still_degenerate"]:
        causes.append("Degeneracy persists without EVD — not a clipping artifact")
    else:
        causes.append("EVD removal breaks degeneracy — clipping is partly responsible")

    # Check Fi relevance
    if results["fi_removed_test"]["fi_irrelevant_for_non_pi_thetas"]:
        causes.append("Fi is IRRELEVANT for non-pi thetas: removing Fi gives same I_c as plateau")
    else:
        causes.append("Fi does contribute even at non-pi thetas")

    degeneracy_cause = "; ".join(causes)
    print("  " + degeneracy_cause.replace("; ", "\n  "))

    results["name"] = "theta_degeneracy_investigation"
    results["degeneracy_cause"] = degeneracy_cause
    results["operator_outputs_identical"] = results["operator_analysis"]["single_fi_outputs_identical"]
    results["timestamp"] = datetime.now(UTC).strftime("%Y-%m-%d")

    # Sanitize numpy types for JSON
    def sanitize(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [sanitize(x) for x in obj]
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, float) and np.isnan(obj):
            return None
        return obj

    results = sanitize(results)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "theta_degeneracy_investigation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults written to {}".format(out_path))

    return results


if __name__ == "__main__":
    main()
