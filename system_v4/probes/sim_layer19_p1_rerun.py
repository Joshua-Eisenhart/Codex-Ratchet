#!/usr/bin/env python3
"""
sim_layer19_p1_rerun.py
=======================

Layer 19 P1 rerun: Axis 0 gradient across torus latitudes.

Now that engine_3qubit has eta-dependent operator scaling (R_major/R_minor
modulating operator strengths via _build_ops), re-measure the I_c gradient
to confirm all 3 torus latitudes produce genuinely different trajectories.

Two sweeps:
  1. 3-point gradient: TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER (20 cycles)
  2. Fine 7-point sweep: eta = linspace(0.1, pi/2 - 0.1, 7)  (20 cycles)

Output: a2_state/sim_results/layer19_p1_gradient_rerun_results.json
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: the layer-19 P1 rerun is represented here by eta-sweep 3-qubit engine numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "eta sweeps, trajectory summaries, and gradient numerics"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "sympy": None,
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_3qubit import GeometricEngine3Q
from hopf_manifold import (
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER, torus_radii,
)


# =====================================================================
# Numpy sanitiser for JSON serialisation
# =====================================================================

def sanitize(obj):
    """Recursively convert numpy types to native Python types."""
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


# =====================================================================
# Run engine at one eta and return summary
# =====================================================================

def run_at_eta_summary(eta: float, n_cycles: int = 20,
                       dephasing: float = 0.05,
                       fi_theta: float = np.pi) -> dict:
    """Run the 3q engine at a given eta, return I_c stats for cut 1vs23."""
    engine = GeometricEngine3Q(
        engine_type=1,
        dephasing_strength=dephasing,
        fi_theta=fi_theta,
        eta=eta,
    )
    trajectories = engine.run_at_eta(
        eta, n_cycles, dephasing=dephasing, fi_theta=fi_theta,
    )
    ic_traj = trajectories["1vs23"]
    R_major, R_minor = torus_radii(eta)
    return {
        "eta": float(eta),
        "R_major": float(R_major),
        "R_minor": float(R_minor),
        "mean_ic": float(np.mean(ic_traj)),
        "max_ic": float(np.max(ic_traj)),
        "trajectory": [float(v) for v in ic_traj],
    }


# =====================================================================
# Main
# =====================================================================

def main():
    n_cycles = 20
    dephasing = 0.05
    fi_theta = np.pi

    print("=" * 72)
    print("  LAYER 19 P1 RERUN -- Eta-dependent operator scaling gradient")
    print("=" * 72)

    # ------------------------------------------------------------------
    # 1. Three-point gradient: INNER / CLIFFORD / OUTER
    # ------------------------------------------------------------------
    labels = {
        "INNER": TORUS_INNER,
        "CLIFFORD": TORUS_CLIFFORD,
        "OUTER": TORUS_OUTER,
    }

    three_point = {}
    for label, eta_val in labels.items():
        result = run_at_eta_summary(eta_val, n_cycles, dephasing, fi_theta)
        three_point[label] = result
        R_maj, R_min = torus_radii(eta_val)
        print(f"\n  {label:10s}  eta={eta_val:.6f}  "
              f"R_maj={R_maj:.6f}  R_min={R_min:.6f}")
        print(f"    mean I_c = {result['mean_ic']:+.10f}")
        print(f"    max  I_c = {result['max_ic']:+.10f}")
        print(f"    trajectory (first 5): "
              f"{[round(v, 8) for v in result['trajectory'][:5]]}")

    # Check all three differ
    means = [three_point[k]["mean_ic"] for k in ["INNER", "CLIFFORD", "OUTER"]]
    pairwise_diffs = [
        abs(means[0] - means[1]),
        abs(means[1] - means[2]),
        abs(means[0] - means[2]),
    ]
    all_three_differ = all(d > 1e-12 for d in pairwise_diffs)

    print(f"\n  Pairwise mean-I_c diffs: {[f'{d:.2e}' for d in pairwise_diffs]}")
    print(f"  ALL THREE DIFFER: {all_three_differ}")

    # ------------------------------------------------------------------
    # 2. Fine 7-point sweep
    # ------------------------------------------------------------------
    eta_fine = np.linspace(0.1, np.pi / 2 - 0.1, 7)
    fine_means = []
    fine_maxes = []

    print(f"\n{'=' * 72}")
    print("  FINE 7-POINT SWEEP")
    print(f"{'=' * 72}")
    print(f"  {'eta':>10s}  {'R_major':>10s}  {'R_minor':>10s}  "
          f"{'mean_Ic':>12s}  {'max_Ic':>12s}")
    print(f"  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*12}  {'-'*12}")

    for eta_val in eta_fine:
        result = run_at_eta_summary(eta_val, n_cycles, dephasing, fi_theta)
        fine_means.append(result["mean_ic"])
        fine_maxes.append(result["max_ic"])
        R_maj, R_min = torus_radii(eta_val)
        print(f"  {eta_val:10.6f}  {R_maj:10.6f}  {R_min:10.6f}  "
              f"{result['mean_ic']:+12.8f}  {result['max_ic']:+12.8f}")

    # Determine gradient shape
    diffs = np.diff(fine_means)
    if all(d >= -1e-14 for d in diffs):
        gradient_shape = "monotonic_increasing"
    elif all(d <= 1e-14 for d in diffs):
        gradient_shape = "monotonic_decreasing"
    elif np.argmax(fine_means) not in (0, len(fine_means) - 1):
        gradient_shape = "peaked"
    else:
        gradient_shape = "non_monotonic"

    best_idx = int(np.argmax(fine_means))
    best_eta = float(eta_fine[best_idx])

    print(f"\n  Gradient shape: {gradient_shape}")
    print(f"  Best eta (max mean I_c): {best_eta:.6f}  "
          f"(mean I_c = {fine_means[best_idx]:+.10f})")

    # Which eta gives best sustained I_c
    best_max_idx = int(np.argmax(fine_maxes))
    print(f"  Best eta (max peak I_c): {float(eta_fine[best_max_idx]):.6f}  "
          f"(max I_c = {fine_maxes[best_max_idx]:+.10f})")

    # ------------------------------------------------------------------
    # 3. Build and write output JSON
    # ------------------------------------------------------------------
    output = {
        "name": "layer19_p1_gradient_rerun",
        "note": "Rerun after eta-dependent operator scaling wired into engine_3qubit.py",
        "three_point_gradient": three_point,
        "all_three_differ": all_three_differ,
        "fine_sweep": {
            "eta_values": [float(v) for v in eta_fine],
            "mean_ic_values": [float(v) for v in fine_means],
            "max_ic_values": [float(v) for v in fine_maxes],
        },
        "gradient_shape": gradient_shape,
        "best_eta": best_eta,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%d"),
    }

    output = sanitize(output)

    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results",
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "layer19_p1_gradient_rerun_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")

    return output


if __name__ == "__main__":
    main()
