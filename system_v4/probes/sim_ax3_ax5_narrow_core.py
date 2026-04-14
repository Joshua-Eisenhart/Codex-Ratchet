#!/usr/bin/env python3
"""
Narrow Core Probe for Ax3 and Ax5
=================================

Ax3:
  Compare two tight spinor-layer observables only:
  - gamma5 branch-phase action
  - direct branch-relative phase/coherence

Ax5:
  Compare torus-layer hysteresis against torus-layer coarse-graining only.

No canon claims.
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
import scipy.linalg as la
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this is a narrow numerical probe over Ax3/Ax5 observables, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "spinor and torus observable numerics"},
    "scipy": {"tried": True, "used": True, "reason": "matrix exponentials for gamma5 action"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "scipy": "supportive"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    fiber_action,
    inter_torus_transport_partial,
    left_density,
    left_weyl_spinor,
    right_density,
    right_weyl_spinor,
    torus_coordinates,
)


I2 = np.eye(2, dtype=complex)
GAMMA5 = np.block([[I2, np.zeros((2, 2))], [np.zeros((2, 2)), -I2]])


def normalized_overlap(a, b):
    av = np.asarray(a).reshape(-1)
    bv = np.asarray(b).reshape(-1)
    na = np.linalg.norm(av)
    nb = np.linalg.norm(bv)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(abs(np.vdot(av, bv)) / (na * nb))


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


def ax3_relative_coherence(psi_L, psi_R):
    z = np.vdot(psi_L, psi_R)
    # keep direct branch coherence rather than projecting away
    return np.array(
        [np.real(z), np.imag(z), np.abs(z), np.angle(z + 1e-30j)],
        dtype=float,
    )


def run_ax3():
    n_trials = 800
    overlaps = []
    gamma_norm = 0.0
    rel_norm = 0.0
    for trial in range(n_trials):
        rng = np.random.default_rng(10100000 + trial)
        psi_L, psi_R, psi = random_dirac_spinor(rng)
        d_gamma = ax3_gamma5(psi)
        d_rel = ax3_relative_coherence(psi_L, psi_R)
        overlaps.append(normalized_overlap(d_gamma[:4], d_rel))
        gamma_norm += np.linalg.norm(d_gamma)
        rel_norm += np.linalg.norm(d_rel)
    return {
        "n_trials": n_trials,
        "mean_overlap": float(np.mean(overlaps)),
        "std_overlap": float(np.std(overlaps)),
        "gamma5_norm": float(gamma_norm / n_trials),
        "relative_coherence_norm": float(rel_norm / n_trials),
    }


def q_at(eta, t1, t2):
    return torus_coordinates(eta, t1, t2)


def torus_coarse_displacement(q, n_samples):
    phases = np.linspace(0.0, 2 * np.pi, n_samples, endpoint=False)
    rhoL = np.zeros((2, 2), dtype=complex)
    rhoR = np.zeros((2, 2), dtype=complex)
    for phase in phases:
        qp = fiber_action(q, phase)
        rhoL += left_density(qp)
        rhoR += right_density(qp)
    rhoL /= n_samples
    rhoR /= n_samples
    return np.concatenate([rhoL.flatten(), rhoR.flatten()])


def torus_hysteresis(q, eta_from, eta_to, alpha=0.5):
    q_half = inter_torus_transport_partial(q, eta_from, eta_to, alpha)
    q_full = inter_torus_transport_partial(q, eta_from, eta_to, 1.0)
    q_back = inter_torus_transport_partial(q_full, eta_to, eta_from, alpha)
    return np.concatenate([q_half - q, q_back - q_full])


def run_ax5():
    n_trials = 600
    configs = [
        ("inner_to_cliff", TORUS_INNER, TORUS_CLIFFORD),
        ("cliff_to_outer", TORUS_CLIFFORD, TORUS_OUTER),
        ("inner_to_outer", TORUS_INNER, TORUS_OUTER),
    ]
    results = {}
    for label, eta_from, eta_to in configs:
        overlaps = []
        coarse_norm = 0.0
        hyst_norm = 0.0
        for trial in range(n_trials):
            rng = np.random.default_rng(10200000 + 1000 * configs.index((label, eta_from, eta_to)) + trial)
            t1 = rng.uniform(0, 2 * np.pi)
            t2 = rng.uniform(0, 2 * np.pi)
            q = q_at(eta_from, t1, t2)
            d_coarse = torus_coarse_displacement(q, n_samples=4) - torus_coarse_displacement(q, n_samples=8)
            d_hyst = torus_hysteresis(q, eta_from, eta_to, alpha=0.5)
            overlaps.append(normalized_overlap(d_coarse[:8], d_hyst))
            coarse_norm += np.linalg.norm(d_coarse)
            hyst_norm += np.linalg.norm(d_hyst)
        results[label] = {
            "mean_overlap": float(np.mean(overlaps)),
            "std_overlap": float(np.std(overlaps)),
            "coarse_norm": float(coarse_norm / n_trials),
            "hysteresis_norm": float(hyst_norm / n_trials),
        }
    return results


def run():
    payload = {
        "schema": "AX3_AX5_NARROW_CORE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "ax3_core": run_ax3(),
        "ax5_core": run_ax5(),
        "note": "Narrow core wiggle: spinor coherence vs gamma5, torus hysteresis vs torus coarse-graining.",
    }
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "ax3_ax5_narrow_core.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(json.dumps(payload, indent=2))
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run()
