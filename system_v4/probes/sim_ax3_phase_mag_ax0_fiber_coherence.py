#!/usr/bin/env python3
"""
Ax3 Phase/Magnitude Split and Ax0 Fiber-Coherence Comparator
============================================================

Ax3:
  Test whether the chiral/gamma5 signal tracks the phase of branch coherence
  c = <psi_L | psi_R> more than its magnitude.

Ax0:
  Use engine-style fiber sample counts, but compare branch-coherence objects
  before density projection so the fiber phases do not vanish trivially.

Exploratory only.
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
import scipy.linalg as la
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    fiber_action,
    left_weyl_spinor,
    right_weyl_spinor,
    torus_coordinates,
)


I2 = np.eye(2, dtype=complex)
GAMMA5 = np.block([[I2, np.zeros((2, 2))], [np.zeros((2, 2)), -I2]])


def ga0_sample_count(ga0_level: float) -> int:
    return int(np.clip(1 + round(7 * float(np.clip(ga0_level, 0.0, 1.0))), 1, 8))


def random_spinor(rng):
    psi = rng.normal(size=2) + 1j * rng.normal(size=2)
    psi /= np.linalg.norm(psi)
    return psi


def random_dirac_spinor(rng):
    psi_L = random_spinor(rng)
    psi_R = random_spinor(rng)
    alpha = rng.uniform(0.15, 0.85)
    phi = rng.uniform(-np.pi, np.pi)
    psi = np.concatenate(
        [np.sqrt(alpha) * psi_L, np.exp(1j * phi) * np.sqrt(1 - alpha) * psi_R]
    )
    psi /= np.linalg.norm(psi)
    return psi_L, psi_R, psi


def ax3_gamma5(psi):
    theta = 0.45
    return la.expm(1j * theta * GAMMA5) @ psi - la.expm(-1j * theta * GAMMA5) @ psi


def branch_coherence(psi_L, psi_R):
    return np.vdot(psi_L, psi_R)


def fiber_coherence_average(q, ga0_level):
    n = ga0_sample_count(ga0_level)
    phases = np.linspace(0.0, 2 * np.pi, n, endpoint=False)
    acc = np.zeros((2, 2), dtype=complex)
    for phase in phases:
        qp = fiber_action(q, phase)
        psi_L = left_weyl_spinor(qp)
        psi_R = right_weyl_spinor(qp)
        acc += np.outer(psi_L, np.conj(psi_R))
    return acc / n


def normalized_overlap(a, b):
    av = np.asarray(a).reshape(-1)
    bv = np.asarray(b).reshape(-1)
    na = np.linalg.norm(av)
    nb = np.linalg.norm(bv)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(abs(np.vdot(av, bv)) / (na * nb))


def run_ax3():
    n_trials = 1200
    phase_vals = []
    mag_vals = []
    gamma_norms = []
    for trial in range(n_trials):
        rng = np.random.default_rng(12100000 + trial)
        psi_L, psi_R, psi = random_dirac_spinor(rng)
        d_gamma = ax3_gamma5(psi)
        c = branch_coherence(psi_L, psi_R)
        phase_feature = np.array([np.cos(np.angle(c + 1e-30j)), np.sin(np.angle(c + 1e-30j)), 0.0, 0.0])
        mag_feature = np.array([abs(c), 0.0, 0.0, 0.0])
        phase_vals.append(normalized_overlap(d_gamma[:4], phase_feature))
        mag_vals.append(normalized_overlap(d_gamma[:4], mag_feature))
        gamma_norms.append(np.linalg.norm(d_gamma))
    return {
        "n_trials": n_trials,
        "gamma5_vs_phase_mean": float(np.mean(phase_vals)),
        "gamma5_vs_phase_std": float(np.std(phase_vals)),
        "gamma5_vs_mag_mean": float(np.mean(mag_vals)),
        "gamma5_vs_mag_std": float(np.std(mag_vals)),
        "gamma5_norm": float(np.mean(gamma_norms)),
    }


def run_ax0():
    n_trials = 800
    configs = [
        ("inner", TORUS_INNER),
        ("clifford", TORUS_CLIFFORD),
        ("outer", TORUS_OUTER),
    ]
    ga0_pairs = [
        ("low_to_high", 0.1, 0.9),
        ("low_to_mid", 0.1, 0.5),
        ("mid_to_high", 0.5, 0.9),
    ]
    results = {}
    for label, eta in configs:
        pair_results = {}
        for pair_label, g0, g1 in ga0_pairs:
            norms = []
            for trial in range(n_trials):
                rng = np.random.default_rng(12200000 + 10000 * configs.index((label, eta)) + 1000 * ga0_pairs.index((pair_label, g0, g1)) + trial)
                t1 = rng.uniform(0, 2 * np.pi)
                t2 = rng.uniform(0, 2 * np.pi)
                q = torus_coordinates(eta, t1, t2)
                c0 = fiber_coherence_average(q, g0)
                c1 = fiber_coherence_average(q, g1)
                norms.append(np.linalg.norm(c1 - c0))
            pair_results[pair_label] = {
                "mean_norm": float(np.mean(norms)),
                "std_norm": float(np.std(norms)),
                "sample_counts": [ga0_sample_count(g0), ga0_sample_count(g1)],
            }
        results[label] = pair_results
    return results


def run():
    payload = {
        "schema": "AX3_PHASE_MAG_AX0_FIBER_COHERENCE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "ax3_phase_mag": run_ax3(),
        "ax0_fiber_coherence": run_ax0(),
        "note": "Exploratory spinor-phase split and pre-density fiber-coherence coarse comparator.",
    }
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "ax3_phase_mag_ax0_fiber_coherence.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(json.dumps(payload, indent=2))
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run()
