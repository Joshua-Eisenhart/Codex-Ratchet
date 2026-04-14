#!/usr/bin/env python3
"""
sim_ic_phase_diagram_and_floquet.py
====================================

Two analyses on the 3-qubit bridge prototype that proved I_c > 0
from separable states:

Part 1 — Fine-grid phase diagram: dephasing strength vs Fi theta,
         20x20 sweep, locate exact boundary where I_c transitions
         from sustained-positive to decaying-negative.

Part 2 — Floquet / spectral analysis: construct the full-cycle
         superoperator Phi (64x64), extract eigenvalues, check
         whether the ~7-cycle oscillation period is a Floquet
         eigenvalue, compute spectral gap.
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sim_3qubit_bridge_prototype import (
    partial_trace_keep,
    von_neumann_entropy,
    ensure_valid_density,
    build_3q_Ti,
    build_3q_Fe,
    build_3q_Te,
    build_3q_Fi,
    I2,
    SIGMA_X,
    SIGMA_Y,
    SIGMA_Z,
)

OUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)


# ═══════════════════════════════════════════════════════════════════
# NUMPY JSON SANITIZER
# ═══════════════════════════════════════════════════════════════════

def sanitize(obj):
    """Recursively convert numpy types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.complexfloating,)):
        return {"re": float(obj.real), "im": float(obj.imag)}
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    return obj


# ═══════════════════════════════════════════════════════════════════
# PART 1 — PHASE DIAGRAM
# ═══════════════════════════════════════════════════════════════════

def run_phase_diagram(n_cycles: int = 30) -> dict:
    """Sweep dephasing vs Fi theta on a 20x20 grid.
    Initial state: |000> (separable).
    Uses cut1 (q1 vs q2q3) for I_c."""

    dephasing_vals = np.linspace(0.01, 0.5, 20)
    theta_vals = np.linspace(0.1, np.pi, 20)

    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0

    max_ic_grid = np.zeros((20, 20))
    cycle_of_max_grid = np.zeros((20, 20), dtype=int)
    positive_cycle_grid = np.zeros((20, 20), dtype=int)
    mean_ic_grid = np.zeros((20, 20))

    dims = [2, 2, 2]

    for i, deph in enumerate(dephasing_vals):
        for j, theta in enumerate(theta_vals):
            Ti = build_3q_Ti(strength=float(deph))
            Fe = build_3q_Fe(strength=1.0, phi=0.4)
            Te = build_3q_Te(strength=float(deph), q=0.7)
            Fi = build_3q_Fi(strength=1.0, theta=float(theta))

            rho = rho_init.copy()
            best_ic = -999.0
            best_cyc = 0
            pos_cyc = 0
            ic_sum = 0.0

            for c in range(1, n_cycles + 1):
                rho = Ti(rho)
                rho = Fe(rho)
                rho = Te(rho)
                rho = Fi(rho)

                # cut1: A=[0], B=[1,2]
                rho_B = partial_trace_keep(rho, [1, 2], dims)
                S_B = von_neumann_entropy(rho_B)
                S_AB = von_neumann_entropy(rho)
                ic = S_B - S_AB

                ic_sum += ic
                if ic > best_ic:
                    best_ic = ic
                    best_cyc = c
                if ic > 1e-10:
                    pos_cyc += 1

            max_ic_grid[i, j] = best_ic
            cycle_of_max_grid[i, j] = best_cyc
            positive_cycle_grid[i, j] = pos_cyc
            mean_ic_grid[i, j] = ic_sum / n_cycles

    # Find boundary: for theta=pi, find dephasing crossover
    theta_pi_idx = 19  # last column = theta closest to pi
    boundary_deph_at_theta_pi = None
    for i in range(19):
        if max_ic_grid[i, theta_pi_idx] > 1e-10 and max_ic_grid[i + 1, theta_pi_idx] <= 1e-10:
            # Linear interpolation
            v0 = max_ic_grid[i, theta_pi_idx]
            v1 = max_ic_grid[i + 1, theta_pi_idx]
            frac = v0 / (v0 - v1) if v0 != v1 else 0.5
            boundary_deph_at_theta_pi = float(
                dephasing_vals[i] + frac * (dephasing_vals[i + 1] - dephasing_vals[i])
            )
            break
    if boundary_deph_at_theta_pi is None:
        # All positive or all negative — report edge
        if max_ic_grid[0, theta_pi_idx] > 1e-10:
            boundary_deph_at_theta_pi = float(dephasing_vals[-1])  # all positive
        else:
            boundary_deph_at_theta_pi = float(dephasing_vals[0])  # all negative

    # Find boundary: for deph=0.05, find theta crossover
    deph_005_idx = 0  # first row is deph=0.01, find closest to 0.05
    deph_005_idx = int(np.argmin(np.abs(dephasing_vals - 0.05)))
    boundary_theta_at_deph_005 = None
    for j in range(19):
        if max_ic_grid[deph_005_idx, j] <= 1e-10 and max_ic_grid[deph_005_idx, j + 1] > 1e-10:
            v0 = max_ic_grid[deph_005_idx, j]
            v1 = max_ic_grid[deph_005_idx, j + 1]
            frac = -v0 / (v1 - v0) if v1 != v0 else 0.5
            boundary_theta_at_deph_005 = float(
                theta_vals[j] + frac * (theta_vals[j + 1] - theta_vals[j])
            )
            break
    if boundary_theta_at_deph_005 is None:
        if max_ic_grid[deph_005_idx, 0] > 1e-10:
            boundary_theta_at_deph_005 = float(theta_vals[0])  # all positive
        else:
            boundary_theta_at_deph_005 = float(theta_vals[-1])  # all negative

    result = {
        "name": "ic_phase_diagram",
        "grid_size": [20, 20],
        "dephasing_values": dephasing_vals.tolist(),
        "theta_values": theta_vals.tolist(),
        "max_ic_grid": max_ic_grid.tolist(),
        "cycle_of_max_grid": cycle_of_max_grid.tolist(),
        "positive_cycle_grid": positive_cycle_grid.tolist(),
        "mean_ic_grid": mean_ic_grid.tolist(),
        "boundary_dephasing_at_theta_pi": boundary_deph_at_theta_pi,
        "boundary_theta_at_deph_005": boundary_theta_at_deph_005,
        "timestamp": "2026-04-05",
    }

    return result


# ═══════════════════════════════════════════════════════════════════
# PART 2 — FLOQUET / SPECTRAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════

def build_superoperator_unitary(U: np.ndarray) -> np.ndarray:
    """Superoperator for unitary channel: rho -> U rho U^dag.
    In vec(rho) basis: S = U tensor conj(U)."""
    return np.kron(U, U.conj())


def build_superoperator_dephasing(projectors: list) -> np.ndarray:
    """Superoperator for Luders dephasing: rho -> sum_k P_k rho P_k.
    S = sum_k P_k tensor conj(P_k)."""
    d = projectors[0].shape[0]
    S = np.zeros((d * d, d * d), dtype=complex)
    for P in projectors:
        S += np.kron(P, P.conj())
    return S


def build_superoperator_mixed_dephasing(projectors: list, mix: float) -> np.ndarray:
    """Superoperator for partial dephasing: rho -> mix * (sum P_k rho P_k) + (1-mix) * rho.
    S = mix * S_deph + (1-mix) * I."""
    d = projectors[0].shape[0]
    S_deph = build_superoperator_dephasing(projectors)
    S_id = np.eye(d * d, dtype=complex)
    return mix * S_deph + (1 - mix) * S_id


def build_full_cycle_superop(deph: float, theta: float) -> np.ndarray:
    """Construct Phi = Phi_Fi . Phi_Te . Phi_Fe . Phi_Ti as a 64x64 superoperator.

    We must replicate the exact channel from the operator builders:
    - Ti: ZZ dephasing on q1,q2 with mix=deph (polarity_up=True)
    - Fe: XX rotation on q1,q2 with phi=0.4, strength=1.0
    - Te: YY dephasing on q1,q2 with mix=min(deph*0.7, 1.0)
    - Fi: XZ rotation on q1,q3 with theta=theta, strength=1.0
    """
    I8 = np.eye(8, dtype=complex)

    # Ti: ZZ x I projectors
    ZZ = np.kron(SIGMA_Z, SIGMA_Z)
    ZZ_I = np.kron(ZZ, I2)
    P0_Ti = (I8 + ZZ_I) / 2
    P1_Ti = (I8 - ZZ_I) / 2
    mix_Ti = deph  # polarity_up=True -> strength
    S_Ti = build_superoperator_mixed_dephasing([P0_Ti, P1_Ti], mix_Ti)

    # Fe: XX x I unitary, phi=0.4, strength=1.0, polarity_up=True
    XX = np.kron(SIGMA_X, SIGMA_X)
    H_Fe = np.kron(XX, I2)
    angle_Fe = 0.4 / 2  # phi * strength / 2
    U_Fe = np.cos(angle_Fe) * I8 - 1j * np.sin(angle_Fe) * H_Fe
    S_Fe = build_superoperator_unitary(U_Fe)

    # Te: YY x I projectors
    YY = np.kron(SIGMA_Y, SIGMA_Y)
    YY_I = np.kron(YY, I2)
    P_plus_Te = (I8 + YY_I) / 2
    P_minus_Te = (I8 - YY_I) / 2
    mix_Te = min(deph * 0.7, 1.0)  # polarity_up=True
    S_Te = build_superoperator_mixed_dephasing([P_plus_Te, P_minus_Te], mix_Te)

    # Fi: X x I x Z unitary
    H_Fi = np.kron(np.kron(SIGMA_X, I2), SIGMA_Z)
    angle_Fi = theta / 2  # theta * strength / 2, strength=1.0
    U_Fi = np.cos(angle_Fi) * I8 - 1j * np.sin(angle_Fi) * H_Fi
    S_Fi = build_superoperator_unitary(U_Fi)

    # Compose: Phi = S_Fi . S_Te . S_Fe . S_Ti (rightmost applied first)
    Phi = S_Fi @ S_Te @ S_Fe @ S_Ti
    return Phi


def extract_trajectory_ic(deph: float, theta: float, n_cycles: int = 60) -> list:
    """Run the operator cycle and extract I_c trajectory (cut1)."""
    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0
    dims = [2, 2, 2]

    Ti = build_3q_Ti(strength=deph)
    Fe = build_3q_Fe(strength=1.0, phi=0.4)
    Te = build_3q_Te(strength=deph, q=0.7)
    Fi = build_3q_Fi(strength=1.0, theta=theta)

    rho = rho_init.copy()
    trajectory = []

    for c in range(1, n_cycles + 1):
        rho = Ti(rho)
        rho = Fe(rho)
        rho = Te(rho)
        rho = Fi(rho)

        rho_B = partial_trace_keep(rho, [1, 2], dims)
        S_B = von_neumann_entropy(rho_B)
        S_AB = von_neumann_entropy(rho)
        ic = S_B - S_AB
        trajectory.append(float(ic))

    return trajectory


def estimate_period_from_trajectory(traj: list) -> float:
    """Estimate oscillation period from I_c trajectory via FFT."""
    if len(traj) < 4:
        return 0.0
    x = np.array(traj)
    x = x - np.mean(x)  # remove DC
    fft = np.fft.rfft(x)
    magnitudes = np.abs(fft)
    # Skip DC component (index 0)
    if len(magnitudes) < 2:
        return 0.0
    peak_idx = np.argmax(magnitudes[1:]) + 1
    if magnitudes[peak_idx] < 1e-15:
        return 0.0
    period = len(traj) / peak_idx
    return float(period)


def run_floquet_analysis() -> dict:
    """Floquet spectral analysis for the best regime (deph=0.05, theta=pi)."""
    deph = 0.05
    theta = float(np.pi)

    print("  Building 64x64 superoperator...")
    Phi = build_full_cycle_superop(deph, theta)
    print(f"  Superoperator shape: {Phi.shape}")

    print("  Computing eigenvalues...")
    eigenvalues = np.linalg.eig(Phi)[0]

    # Sort by magnitude (descending)
    mags = np.abs(eigenvalues)
    phases = np.angle(eigenvalues)
    order = np.argsort(-mags)
    eigenvalues = eigenvalues[order]
    mags = mags[order]
    phases = phases[order]

    # Top 10 eigenvalues
    top_eigs = []
    for k in range(min(10, len(eigenvalues))):
        mag = float(mags[k])
        phase = float(phases[k])
        period = float(2 * np.pi / abs(phase)) if abs(phase) > 1e-12 else float('inf')
        top_eigs.append({
            "rank": k + 1,
            "magnitude": round(mag, 10),
            "phase_rad": round(phase, 10),
            "period_cycles": round(period, 4) if period != float('inf') else None,
        })

    # Spectral gap
    spectral_gap = float(1.0 - mags[1]) if len(mags) > 1 else 0.0

    # Check for ~7-cycle eigenvalue: arg ~ 2*pi/7 ~ 0.898
    target_phase = 2 * np.pi / 7
    closest_to_7 = None
    closest_dist = 999.0
    for k in range(len(eigenvalues)):
        dist = abs(abs(phases[k]) - target_phase)
        if dist < closest_dist:
            closest_dist = dist
            closest_to_7 = {
                "eigenvalue_rank": int(np.where(order == order[k])[0][0]) + 1,
                "magnitude": round(float(mags[k]), 10),
                "phase_rad": round(float(phases[k]), 10),
                "implied_period": round(float(2 * np.pi / abs(phases[k])), 4) if abs(phases[k]) > 1e-12 else None,
                "phase_distance_from_2pi_over_7": round(float(closest_dist), 10),
            }

    # Check for ~50-cycle eigenvalue (dual-stack)
    target_phase_50 = 2 * np.pi / 50
    closest_to_50 = None
    closest_dist_50 = 999.0
    for k in range(len(eigenvalues)):
        dist = abs(abs(phases[k]) - target_phase_50)
        if dist < closest_dist_50:
            closest_dist_50 = dist
            closest_to_50 = {
                "magnitude": round(float(mags[k]), 10),
                "phase_rad": round(float(phases[k]), 10),
                "implied_period": round(float(2 * np.pi / abs(phases[k])), 4) if abs(phases[k]) > 1e-12 else None,
                "phase_distance_from_2pi_over_50": round(float(closest_dist_50), 10),
            }

    # Extract observed trajectory and estimate period
    print("  Extracting I_c trajectory (60 cycles)...")
    traj = extract_trajectory_ic(deph, theta, n_cycles=60)
    observed_period = estimate_period_from_trajectory(traj)

    # Predicted period from dominant non-trivial eigenvalue
    predicted_period = None
    for eig in top_eigs:
        if eig["period_cycles"] is not None and eig["magnitude"] > 0.5:
            if eig["period_cycles"] < 100:  # reasonable
                predicted_period = eig["period_cycles"]
                break

    match = False
    if predicted_period is not None and observed_period > 0:
        match = abs(predicted_period - observed_period) / max(observed_period, 1e-10) < 0.15

    # Type 2 ordering: reverse polarity pattern
    # In the bridge prototype, Type 2 uses reversed operator ordering
    print("  Building Type 2 superoperator (reversed ordering)...")
    # Type 2: Fi -> Te -> Fe -> Ti (reversed application order)
    I8 = np.eye(8, dtype=complex)

    # Rebuild individual superops
    ZZ = np.kron(SIGMA_Z, SIGMA_Z)
    ZZ_I = np.kron(ZZ, I2)
    P0_Ti = (I8 + ZZ_I) / 2
    P1_Ti = (I8 - ZZ_I) / 2
    S_Ti = build_superoperator_mixed_dephasing([P0_Ti, P1_Ti], deph)

    XX = np.kron(SIGMA_X, SIGMA_X)
    H_Fe = np.kron(XX, I2)
    U_Fe = np.cos(0.2) * I8 - 1j * np.sin(0.2) * H_Fe
    S_Fe = build_superoperator_unitary(U_Fe)

    YY = np.kron(SIGMA_Y, SIGMA_Y)
    YY_I = np.kron(YY, I2)
    P_plus_Te = (I8 + YY_I) / 2
    P_minus_Te = (I8 - YY_I) / 2
    S_Te = build_superoperator_mixed_dephasing([P_plus_Te, P_minus_Te], min(deph * 0.7, 1.0))

    H_Fi = np.kron(np.kron(SIGMA_X, I2), SIGMA_Z)
    U_Fi = np.cos(theta / 2) * I8 - 1j * np.sin(theta / 2) * H_Fi
    S_Fi = build_superoperator_unitary(U_Fi)

    # Type 2: reversed -> Ti applied last: Phi2 = S_Ti . S_Fe . S_Te . S_Fi
    Phi2 = S_Ti @ S_Fe @ S_Te @ S_Fi
    eigs2 = np.linalg.eig(Phi2)[0]
    mags2 = np.abs(eigs2)
    phases2 = np.angle(eigs2)
    order2 = np.argsort(-mags2)
    mags2 = mags2[order2]
    phases2 = phases2[order2]

    top_eigs_type2 = []
    for k in range(min(10, len(eigs2))):
        mag = float(mags2[k])
        phase = float(phases2[k])
        period = float(2 * np.pi / abs(phase)) if abs(phase) > 1e-12 else None
        top_eigs_type2.append({
            "rank": k + 1,
            "magnitude": round(mag, 10),
            "phase_rad": round(phase, 10),
            "period_cycles": round(period, 4) if period is not None else None,
        })

    spectral_gap_type2 = float(1.0 - mags2[1]) if len(mags2) > 1 else 0.0

    # Check type2 for ~50-cycle eigenvalue
    closest_to_50_type2 = None
    closest_dist_50_t2 = 999.0
    for k in range(len(eigs2)):
        dist = abs(abs(phases2[k]) - target_phase_50)
        if dist < closest_dist_50_t2:
            closest_dist_50_t2 = dist
            closest_to_50_type2 = {
                "magnitude": round(float(mags2[k]), 10),
                "phase_rad": round(float(phases2[k]), 10),
                "implied_period": round(float(2 * np.pi / abs(phases2[k])), 4) if abs(phases2[k]) > 1e-12 else None,
                "phase_distance_from_2pi_over_50": round(float(closest_dist_50_t2), 10),
            }

    result = {
        "name": "floquet_spectral_analysis",
        "parameters": {"dephasing": deph, "fi_theta": round(theta, 6)},
        "superoperator_size": 64,
        "type1_forward_order": {
            "top_eigenvalues": top_eigs,
            "spectral_gap": round(spectral_gap, 10),
            "closest_to_7cycle": closest_to_7,
            "closest_to_50cycle": closest_to_50,
        },
        "type2_reversed_order": {
            "top_eigenvalues": top_eigs_type2,
            "spectral_gap": round(spectral_gap_type2, 10),
            "closest_to_50cycle": closest_to_50_type2,
        },
        "observed_trajectory_60cycles": [round(v, 8) for v in traj],
        "predicted_oscillation_period": predicted_period,
        "observed_oscillation_period": round(observed_period, 4),
        "match": match,
        "timestamp": "2026-04-05",
    }

    return result


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  I_c PHASE DIAGRAM & FLOQUET SPECTRAL ANALYSIS")
    print("=" * 72)

    # Part 1: Phase diagram
    print("\n[Part 1] Running 20x20 phase diagram sweep...")
    phase_result = run_phase_diagram(n_cycles=30)
    print(f"  Grid computed. Boundary at theta=pi: deph = {phase_result['boundary_dephasing_at_theta_pi']:.4f}")
    print(f"  Boundary at deph=0.05: theta = {phase_result['boundary_theta_at_deph_005']:.4f}")

    # Summary stats
    grid = np.array(phase_result["max_ic_grid"])
    pos_grid = np.array(phase_result["positive_cycle_grid"])
    n_positive = int(np.sum(grid > 1e-10))
    print(f"  Grid cells with max I_c > 0: {n_positive}/400")
    print(f"  Max I_c in grid: {np.max(grid):.6f}")
    print(f"  Max sustained positive cycles: {int(np.max(pos_grid))}")

    # Part 2: Floquet analysis
    print(f"\n[Part 2] Running Floquet spectral analysis...")
    floquet_result = run_floquet_analysis()

    print(f"\n  Top 5 eigenvalues (Type 1):")
    for eig in floquet_result["type1_forward_order"]["top_eigenvalues"][:5]:
        per_str = f"{eig['period_cycles']:.2f}" if eig["period_cycles"] is not None else "inf"
        print(f"    rank {eig['rank']:2d}: |lambda|={eig['magnitude']:.6f}  "
              f"phase={eig['phase_rad']:+.6f}  period={per_str}")

    print(f"\n  Spectral gap (Type 1): {floquet_result['type1_forward_order']['spectral_gap']:.6f}")
    print(f"  Predicted period: {floquet_result['predicted_oscillation_period']}")
    print(f"  Observed period (FFT): {floquet_result['observed_oscillation_period']:.2f}")
    print(f"  Match: {floquet_result['match']}")

    c7 = floquet_result["type1_forward_order"]["closest_to_7cycle"]
    if c7:
        print(f"\n  Closest eigenvalue to 7-cycle period:")
        print(f"    |lambda|={c7['magnitude']:.6f}, phase={c7['phase_rad']:+.6f}, "
              f"implied period={c7['implied_period']}")
        print(f"    Phase distance from 2pi/7: {c7['phase_distance_from_2pi_over_7']:.6f}")

    print(f"\n  Top 5 eigenvalues (Type 2 / reversed):")
    for eig in floquet_result["type2_reversed_order"]["top_eigenvalues"][:5]:
        per_str = f"{eig['period_cycles']:.2f}" if eig["period_cycles"] is not None else "inf"
        print(f"    rank {eig['rank']:2d}: |lambda|={eig['magnitude']:.6f}  "
              f"phase={eig['phase_rad']:+.6f}  period={per_str}")

    print(f"\n  Spectral gap (Type 2): {floquet_result['type2_reversed_order']['spectral_gap']:.6f}")

    # Write outputs
    os.makedirs(OUT_DIR, exist_ok=True)

    phase_path = os.path.join(OUT_DIR, "ic_phase_diagram_results.json")
    with open(phase_path, "w") as f:
        json.dump(sanitize(phase_result), f, indent=2)
    print(f"\n  Phase diagram -> {phase_path}")

    floquet_path = os.path.join(OUT_DIR, "floquet_spectral_analysis_results.json")
    with open(floquet_path, "w") as f:
        json.dump(sanitize(floquet_result), f, indent=2)
    print(f"  Floquet analysis -> {floquet_path}")

    print("\n" + "=" * 72)
    print("  DONE")
    print("=" * 72)


if __name__ == "__main__":
    main()
