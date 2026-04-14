#!/usr/bin/env python3
"""
sim_dephasing_boundary_scan.py
==============================

Push the dephasing axis hard to find where I_c dies.

The existing phase diagram only sampled dephasing 0.01..0.5 and found all
400 cells positive.  This scan extends dephasing to 1.0 with fine resolution,
then does a 2D boundary scan varying both dephasing and Fi coupling theta.

Outputs: a2_state/sim_results/dephasing_boundary_scan_results.json
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
    compute_info_measures,
)


# ═══════════════════════════════════════════════════════════════════
# NUMPY SANITIZER
# ═══════════════════════════════════════════════════════════════════

def sanitize(obj):
    """Recursively convert numpy types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# ═══════════════════════════════════════════════════════════════════
# 1-D DEPHASING SCAN  (fi_theta = pi, 40 points 0.01..1.0)
# ═══════════════════════════════════════════════════════════════════

def run_1d_scan(n_cycles: int = 30) -> dict:
    """Scan dephasing from 0.01 to 1.0 at fi_theta=pi (best coupling).
    For each value, record max I_c, positive cycle count, mean I_c on cut1."""
    fi_theta = np.pi
    dephasing_values = np.linspace(0.01, 1.0, 40)

    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0  # |000>

    max_ic_list = []
    positive_cycles_list = []
    mean_ic_list = []

    for deph in dephasing_values:
        deph = float(deph)
        Ti = build_3q_Ti(strength=deph)
        Te = build_3q_Te(strength=deph, q=0.7)
        Fe = build_3q_Fe(strength=1.0, phi=0.4)
        Fi = build_3q_Fi(strength=1.0, theta=fi_theta)

        rho = rho_init.copy()
        ic_values = []

        for c in range(1, n_cycles + 1):
            rho = Ti(rho)
            rho = Fe(rho)
            rho = Te(rho)
            rho = Fi(rho)

            # I_c on cut1 (qubit 1 vs qubits 2,3)
            rho_B = partial_trace_keep(rho, [1, 2], [2, 2, 2])
            S_B = von_neumann_entropy(rho_B)
            S_AB = von_neumann_entropy(rho)
            ic = S_B - S_AB
            ic_values.append(ic)

        max_ic_list.append(max(ic_values))
        positive_cycles_list.append(sum(1 for v in ic_values if v > 1e-10))
        mean_ic_list.append(float(np.mean(ic_values)))

    return {
        "dephasing_values": dephasing_values.tolist(),
        "max_ic": max_ic_list,
        "positive_cycles": positive_cycles_list,
        "mean_ic": mean_ic_list,
    }


def find_boundary(dephasing_values, values, threshold, direction="below"):
    """Find dephasing value where 'values' crosses threshold.
    direction='below': find where values drops below threshold.
    Returns None if no crossing found."""
    for i in range(len(values) - 1):
        if direction == "below":
            if values[i] >= threshold and values[i + 1] < threshold:
                # Linear interpolation
                frac = (threshold - values[i]) / (values[i + 1] - values[i])
                return dephasing_values[i] + frac * (dephasing_values[i + 1] - dephasing_values[i])
        elif direction == "above":
            if values[i] <= threshold and values[i + 1] > threshold:
                frac = (threshold - values[i]) / (values[i + 1] - values[i])
                return dephasing_values[i] + frac * (dephasing_values[i + 1] - dephasing_values[i])
    return None


def binary_search_boundary(target_fn, lo, hi, threshold=0.0, tol=1e-6, max_iter=50):
    """Binary search for the dephasing value where target_fn crosses threshold.
    target_fn(deph) returns a scalar.  Assumes target_fn(lo)>threshold, target_fn(hi)<threshold."""
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        val = target_fn(mid)
        if abs(val - threshold) < tol:
            return mid
        if val > threshold:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def max_ic_at_dephasing(deph, fi_theta=np.pi, n_cycles=30):
    """Return max I_c (cut1) for a given dephasing value."""
    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0

    Ti = build_3q_Ti(strength=deph)
    Te = build_3q_Te(strength=deph, q=0.7)
    Fe = build_3q_Fe(strength=1.0, phi=0.4)
    Fi = build_3q_Fi(strength=1.0, theta=fi_theta)

    rho = rho_init.copy()
    best = -999.0
    for _ in range(1, n_cycles + 1):
        rho = Ti(rho)
        rho = Fe(rho)
        rho = Te(rho)
        rho = Fi(rho)
        rho_B = partial_trace_keep(rho, [1, 2], [2, 2, 2])
        S_B = von_neumann_entropy(rho_B)
        S_AB = von_neumann_entropy(rho)
        ic = S_B - S_AB
        if ic > best:
            best = ic
    return best


# ═══════════════════════════════════════════════════════════════════
# 2-D BOUNDARY SCAN  (dephasing x theta near the boundary)
# ═══════════════════════════════════════════════════════════════════

def run_2d_boundary_scan(n_cycles: int = 30) -> dict:
    """Map the boundary region: dephasing 0.4..1.0 x theta in {pi/4, pi/2, 3pi/4, pi}."""
    dephasing_values = np.linspace(0.4, 1.0, 20)
    theta_values = [np.pi / 4, np.pi / 2, 3 * np.pi / 4, np.pi]

    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0

    max_ic_grid = []  # 20 x 4

    for deph in dephasing_values:
        deph = float(deph)
        row = []
        for theta in theta_values:
            Ti = build_3q_Ti(strength=deph)
            Te = build_3q_Te(strength=deph, q=0.7)
            Fe = build_3q_Fe(strength=1.0, phi=0.4)
            Fi = build_3q_Fi(strength=1.0, theta=theta)

            rho = rho_init.copy()
            best_ic = -999.0
            for _ in range(1, n_cycles + 1):
                rho = Ti(rho)
                rho = Fe(rho)
                rho = Te(rho)
                rho = Fi(rho)
                rho_B = partial_trace_keep(rho, [1, 2], [2, 2, 2])
                S_B = von_neumann_entropy(rho_B)
                S_AB = von_neumann_entropy(rho)
                ic = S_B - S_AB
                if ic > best_ic:
                    best_ic = ic
            row.append(best_ic)
        max_ic_grid.append(row)

    return {
        "dephasing_values": dephasing_values.tolist(),
        "theta_values": [float(t) for t in theta_values],
        "max_ic_grid": max_ic_grid,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  DEPHASING BOUNDARY SCAN — Finding where I_c dies")
    print("=" * 72)

    # --- 1-D scan ---
    print("\n[1/3] Running 1-D scan: dephasing 0.01..1.0 at fi_theta=pi ...")
    scan_1d = run_1d_scan(n_cycles=30)

    dv = scan_1d["dephasing_values"]
    mic = scan_1d["max_ic"]
    pc = scan_1d["positive_cycles"]
    mnic = scan_1d["mean_ic"]

    # Print table
    print(f"\n  {'deph':>8s}  {'max_Ic':>10s}  {'pos_cyc':>8s}  {'mean_Ic':>10s}")
    print("  " + "-" * 42)
    for i in range(len(dv)):
        marker = " <-- DEAD" if mic[i] <= 1e-10 else ""
        print(f"  {dv[i]:8.4f}  {mic[i]:+10.6f}  {pc[i]:8d}  {mnic[i]:+10.6f}{marker}")

    # Find boundaries via interpolation
    boundary_max_ic_zero = find_boundary(dv, mic, 0.0, direction="below")
    boundary_50pct = find_boundary(dv, pc, 15.0, direction="below")
    boundary_mean_ic_zero = find_boundary(dv, mnic, 0.0, direction="below")

    # --- Binary search refinement for max_ic=0 boundary ---
    print("\n[2/3] Binary search for precise max_Ic=0 boundary ...")
    if boundary_max_ic_zero is not None:
        # Refine
        precise_boundary = binary_search_boundary(
            lambda d: max_ic_at_dephasing(d, fi_theta=np.pi, n_cycles=30),
            lo=max(boundary_max_ic_zero - 0.05, 0.01),
            hi=min(boundary_max_ic_zero + 0.05, 1.0),
            threshold=0.0,
            tol=1e-8,
        )
        boundary_max_ic_zero = precise_boundary
        print(f"  Refined boundary (max_Ic=0): dephasing = {precise_boundary:.8f}")
    else:
        # Check if all values are positive or all negative
        if all(v > 1e-10 for v in mic):
            print("  WARNING: I_c never crosses zero in [0.01, 1.0] — all positive!")
            print("  Extending search to dephasing=5.0 ...")
            # Extended search
            for ext_deph in np.linspace(1.0, 5.0, 40):
                ext_val = max_ic_at_dephasing(float(ext_deph))
                if ext_val <= 1e-10:
                    # Found it, binary search
                    precise_boundary = binary_search_boundary(
                        lambda d: max_ic_at_dephasing(d),
                        lo=float(ext_deph - (5.0 - 1.0) / 40),
                        hi=float(ext_deph),
                        threshold=0.0,
                        tol=1e-8,
                    )
                    boundary_max_ic_zero = precise_boundary
                    print(f"  Found boundary at dephasing = {precise_boundary:.8f}")
                    break
            else:
                print("  I_c still positive at dephasing=5.0 — boundary not found in range")
                boundary_max_ic_zero = None
        elif all(v <= 1e-10 for v in mic):
            print("  All values non-positive — boundary is below 0.01")
            boundary_max_ic_zero = 0.0
        else:
            print("  Could not interpolate boundary — non-monotonic?")

    # Refine 50% positive boundary
    if boundary_50pct is None and all(p >= 15 for p in pc):
        print("  50% positive boundary not found in [0.01, 1.0] — all above 50%")
    # Refine mean I_c boundary
    if boundary_mean_ic_zero is None and all(m > 0 for m in mnic):
        print("  Mean I_c boundary not found in [0.01, 1.0] — all positive means")

    scan_1d["boundary_max_ic_zero"] = boundary_max_ic_zero
    scan_1d["boundary_50pct_positive"] = boundary_50pct
    scan_1d["boundary_mean_ic_zero"] = boundary_mean_ic_zero

    print(f"\n  Boundary summary:")
    print(f"    max_Ic crosses 0 at dephasing  = {boundary_max_ic_zero}")
    print(f"    50% positive cycles at dephasing = {boundary_50pct}")
    print(f"    mean_Ic crosses 0 at dephasing = {boundary_mean_ic_zero}")

    # --- 2-D boundary scan ---
    print("\n[3/3] Running 2-D boundary scan: dephasing 0.4..1.0 x 4 theta values ...")
    scan_2d = run_2d_boundary_scan(n_cycles=30)

    # Print 2D grid
    theta_labels = ["pi/4", "pi/2", "3pi/4", "pi"]
    print(f"\n  {'deph':>8s}  " + "  ".join(f"{t:>10s}" for t in theta_labels))
    print("  " + "-" * 52)
    for i, deph in enumerate(scan_2d["dephasing_values"]):
        vals = "  ".join(f"{scan_2d['max_ic_grid'][i][j]:+10.6f}" for j in range(4))
        print(f"  {deph:8.4f}  {vals}")

    # --- Assemble output ---
    output = sanitize({
        "name": "dephasing_boundary_scan",
        "1d_scan": scan_1d,
        "2d_boundary_scan": scan_2d,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%d"),
    })

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "dephasing_boundary_scan_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults written to {out_path}")
    print("=" * 72)

    return output


if __name__ == "__main__":
    main()
