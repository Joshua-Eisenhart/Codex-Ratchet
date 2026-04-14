#!/usr/bin/env python3
"""
Refined Ax3 / Ax5 Wiggle
========================

Refine two promising branches:

- Ax3 at the Weyl-pair layer:
    compare direct relative-phase/chiral observables against earlier
    spinor candidates without projecting to density too early.

- Ax5 at the torus layer:
    compare signed-eta asymmetry, eta second-difference curvature,
    and partial-transport hysteresis using the Hopf torus primitives.

Exploratory only.
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
import scipy.linalg as la
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this refines Ax3/Ax5 candidate observables numerically, not as a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "Weyl-pair and torus observable numerics"},
    "scipy": {"tried": True, "used": True, "reason": "matrix exponentials for chiral transforms"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "scipy": "supportive"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    inter_torus_transport,
    inter_torus_transport_partial,
    left_weyl_spinor,
    right_weyl_spinor,
    torus_coordinates,
)


sx = np.array([[0, 1], [1, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)
GAMMA5 = np.block([[I2, np.zeros((2, 2))], [np.zeros((2, 2)), -I2]])
P_SWAP = np.block([[np.zeros((2, 2)), I2], [I2, np.zeros((2, 2))]])


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


def random_weyl_pair(rng):
    return random_spinor(rng), random_spinor(rng)


def dirac_from_pair(psi_L, psi_R, alpha=0.5, phi=0.0):
    psi = np.concatenate(
        [np.sqrt(alpha) * psi_L, np.exp(1j * phi) * np.sqrt(1 - alpha) * psi_R]
    )
    psi /= np.linalg.norm(psi)
    return psi


def ax3_rel_phase_scalar(psi_L, psi_R):
    z = np.vdot(psi_L, psi_R)
    return np.array([np.real(z), np.imag(z), np.angle(z + 1e-30j), 0.0], dtype=float)


def ax3_gamma5_phase(psi):
    theta = 0.45
    return la.expm(1j * theta * GAMMA5) @ psi - la.expm(-1j * theta * GAMMA5) @ psi


def ax3_cp_spinor(psi):
    return psi - np.conj(P_SWAP @ psi)


def ax3_opposite_rot(psi_L, psi_R):
    H = sz * 0.3 + sx * 0.2
    U = la.expm(-1j * H)
    a = dirac_from_pair(U @ psi_L, np.conj(U) @ psi_R)
    b = dirac_from_pair(U.conj().T @ psi_L, np.conj(U.conj().T) @ psi_R)
    return a - b


def run_ax3():
    n_trials = 500
    names = ["rel_phase_scalar", "gamma5_phase", "cp_spinor", "opposite_rot"]
    overlap = np.zeros((4, 4))
    norms = np.zeros(4)
    for trial in range(n_trials):
        rng = np.random.default_rng(9100000 + trial)
        psi_L, psi_R = random_weyl_pair(rng)
        psi = dirac_from_pair(psi_L, psi_R, alpha=rng.uniform(0.15, 0.85), phi=rng.uniform(-np.pi, np.pi))
        disps = [
            ax3_rel_phase_scalar(psi_L, psi_R),
            ax3_gamma5_phase(psi),
            ax3_cp_spinor(psi),
            ax3_opposite_rot(psi_L, psi_R),
        ]
        for i in range(4):
            norms[i] += np.linalg.norm(disps[i])
            for j in range(i + 1, 4):
                ov = normalized_overlap(disps[i], disps[j])
                overlap[i, j] += ov
                overlap[j, i] += ov
    return {
        "names": names,
        "overlap": (overlap / n_trials).tolist(),
        "norms": (norms / n_trials).tolist(),
    }


def q_at(eta, t1, t2):
    return torus_coordinates(eta, t1, t2)


def ax5_signed_eta(eta_from, eta_to):
    def signed(eta):
        return np.cos(eta) - np.sin(eta)
    return np.array([signed(eta_to) - signed(eta_from), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=float)


def ax5_eta_second_difference(eta_center, delta=0.08):
    e1 = max(0.01, eta_center - delta)
    e2 = eta_center
    e3 = min(np.pi / 2 - 0.01, eta_center + delta)
    vals = [np.cos(e) - np.sin(e) for e in [e1, e2, e3]]
    return np.array([vals[0] + vals[2] - 2 * vals[1], 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=float)


def ax5_partial_transport_hysteresis(q, eta_from, eta_to):
    q_half = inter_torus_transport_partial(q, eta_from, eta_to, 0.5)
    q_target = inter_torus_transport(q, eta_from, eta_to)
    q_back = inter_torus_transport_partial(q_target, eta_to, eta_from, 0.5)
    return np.concatenate([q_half - q, q_back - q_target])


def ax5_torus_radius_delta(eta_from, eta_to):
    vec = np.array([
        np.cos(eta_to) - np.cos(eta_from),
        np.sin(eta_to) - np.sin(eta_from),
        np.cos(2 * eta_to) - np.cos(2 * eta_from),
    ])
    return np.concatenate([vec, np.zeros(5, dtype=float)])


def run_ax5():
    n_trials = 400
    pairs = [
        ("inner_to_cliff", TORUS_INNER, TORUS_CLIFFORD),
        ("cliff_to_outer", TORUS_CLIFFORD, TORUS_OUTER),
        ("inner_to_outer", TORUS_INNER, TORUS_OUTER),
    ]
    all_results = {}
    for label, eta_from, eta_to in pairs:
        names = ["signed_eta", "eta_second_difference", "partial_transport_hysteresis", "torus_radius_delta"]
        overlap = np.zeros((4, 4))
        norms = np.zeros(4)
        eta_center = 0.5 * (eta_from + eta_to)
        for trial in range(n_trials):
            rng = np.random.default_rng(9200000 + 1000 * pairs.index((label, eta_from, eta_to)) + trial)
            t1 = rng.uniform(0, 2 * np.pi)
            t2 = rng.uniform(0, 2 * np.pi)
            q = q_at(eta_from, t1, t2)
            disps = [
                ax5_signed_eta(eta_from, eta_to),
                ax5_eta_second_difference(eta_center),
                ax5_partial_transport_hysteresis(q, eta_from, eta_to),
                ax5_torus_radius_delta(eta_from, eta_to),
            ]
            for i in range(4):
                norms[i] += np.linalg.norm(disps[i])
                for j in range(i + 1, 4):
                    ov = normalized_overlap(disps[i], disps[j])
                    overlap[i, j] += ov
                    overlap[j, i] += ov
        all_results[label] = {
            "names": names,
            "overlap": (overlap / n_trials).tolist(),
            "norms": (norms / n_trials).tolist(),
        }
    return all_results


def run():
    payload = {
        "schema": "AX3_AX5_REFINED_WIGGLE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "ax3_refined": run_ax3(),
        "ax5_refined": run_ax5(),
        "note": "Exploratory refined wiggle; spinor/torus layers only.",
    }
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "ax3_ax5_refined_wiggle.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(json.dumps(payload, indent=2))
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run()
