#!/usr/bin/env python3
"""
Ax5 Torus Hysteresis vs Engine-Style GA0 Coarse-Graining
========================================================

Use the actual engine-style Hopf-fiber sampling rule for Axis 0 and compare it
against torus transport hysteresis on the torus layer.

Exploratory only.
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this compares torus hysteresis against GA0 coarse-graining numerically, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "torus transport and coarse-graining numerics"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    fiber_action,
    inter_torus_transport_partial,
    left_density,
    right_density,
    torus_coordinates,
)


def normalized_overlap(a, b):
    av = np.asarray(a).reshape(-1)
    bv = np.asarray(b).reshape(-1)
    na = np.linalg.norm(av)
    nb = np.linalg.norm(bv)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(abs(np.vdot(av, bv)) / (na * nb))


def ga0_sample_count(ga0_level: float) -> int:
    return int(np.clip(1 + round(7 * float(np.clip(ga0_level, 0.0, 1.0))), 1, 8))


def fiber_coarse_grained_density(q, ga0_level, spinor):
    n_samples = ga0_sample_count(ga0_level)
    if n_samples <= 1:
        return left_density(q) if spinor == "left" else right_density(q)
    phases = np.linspace(0.0, 2 * np.pi, n_samples, endpoint=False)
    rho = np.zeros((2, 2), dtype=complex)
    for phase in phases:
        q_phase = fiber_action(q, phase)
        rho += left_density(q_phase) if spinor == "left" else right_density(q_phase)
    rho /= n_samples
    return rho


def axis0_ga0_displacement(q, ga0_a, ga0_b):
    rhoLa = fiber_coarse_grained_density(q, ga0_a, "left")
    rhoRa = fiber_coarse_grained_density(q, ga0_a, "right")
    rhoLb = fiber_coarse_grained_density(q, ga0_b, "left")
    rhoRb = fiber_coarse_grained_density(q, ga0_b, "right")
    return np.concatenate([(rhoLb - rhoLa).flatten(), (rhoRb - rhoRa).flatten()])


def torus_hysteresis(q, eta_from, eta_to, alpha=0.5):
    q_half = inter_torus_transport_partial(q, eta_from, eta_to, alpha)
    q_full = inter_torus_transport_partial(q, eta_from, eta_to, 1.0)
    q_back = inter_torus_transport_partial(q_full, eta_to, eta_from, alpha)
    return np.concatenate([q_half - q, q_back - q_full])


def run():
    n_trials = 800
    configs = [
        ("inner_to_cliff", TORUS_INNER, TORUS_CLIFFORD),
        ("cliff_to_outer", TORUS_CLIFFORD, TORUS_OUTER),
        ("inner_to_outer", TORUS_INNER, TORUS_OUTER),
    ]
    ga0_pairs = [
        ("low_to_high", 0.1, 0.9),
        ("mid_to_high", 0.5, 0.9),
        ("low_to_mid", 0.1, 0.5),
    ]
    results = {}
    for label, eta_from, eta_to in configs:
        pair_results = {}
        for pair_label, ga0_a, ga0_b in ga0_pairs:
            overlaps = []
            axis0_norm = 0.0
            hyst_norm = 0.0
            for trial in range(n_trials):
                rng = np.random.default_rng(11100000 + 10000 * configs.index((label, eta_from, eta_to)) + 1000 * ga0_pairs.index((pair_label, ga0_a, ga0_b)) + trial)
                t1 = rng.uniform(0, 2 * np.pi)
                t2 = rng.uniform(0, 2 * np.pi)
                q = torus_coordinates(eta_from, t1, t2)
                d0 = axis0_ga0_displacement(q, ga0_a, ga0_b)
                d5 = torus_hysteresis(q, eta_from, eta_to, alpha=0.5)
                overlaps.append(normalized_overlap(d0, d5))
                axis0_norm += np.linalg.norm(d0)
                hyst_norm += np.linalg.norm(d5)
            pair_results[pair_label] = {
                "mean_overlap": float(np.mean(overlaps)),
                "std_overlap": float(np.std(overlaps)),
                "axis0_norm": float(axis0_norm / n_trials),
                "hysteresis_norm": float(hyst_norm / n_trials),
                "ga0_sample_counts": [ga0_sample_count(ga0_a), ga0_sample_count(ga0_b)],
            }
        results[label] = pair_results

    payload = {
        "schema": "AX5_TORUS_HYSTERESIS_VS_GA0_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_trials": n_trials,
        "results": results,
        "note": "Engine-style GA0 fiber coarse-graining vs torus hysteresis on torus layer.",
    }
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "ax5_torus_hysteresis_vs_ga0.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(json.dumps(payload, indent=2))
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run()
