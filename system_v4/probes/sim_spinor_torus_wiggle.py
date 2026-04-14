#!/usr/bin/env python3
"""
Spinor + Torus Wiggle Exploration
=================================

Part A: Ax3 on the spinor layer
  Compare candidate chirality observables before density projection.

Part B: Ax5 on the torus layer
  Compare candidate curvature / stage observables directly on nested tori.

Exploratory only. No canon claims.
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
import scipy.linalg as la
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER, torus_coordinates
from sim_L2_eight_stages import classify_stage, stage_invariants


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


def random_dirac_spinor(rng):
    psi_L = random_spinor(rng)
    psi_R = random_spinor(rng)
    alpha = rng.uniform(0.15, 0.85)
    phi = rng.uniform(-np.pi, np.pi)
    psi = np.concatenate(
        [np.sqrt(alpha) * psi_L, np.exp(1j * phi) * np.sqrt(1 - alpha) * psi_R]
    )
    psi /= np.linalg.norm(psi)
    return psi


def ax3_gamma5_spinor(psi):
    theta = 0.45
    return la.expm(1j * theta * GAMMA5) @ psi - la.expm(-1j * theta * GAMMA5) @ psi


def ax3_cp_spinor(psi):
    return psi - np.conj(P_SWAP @ psi)


def ax3_parity_spinor(psi):
    return psi - (P_SWAP @ psi)


def ax3_opposite_rot_spinor(psi):
    H = sz * 0.3 + sx * 0.2
    U = la.expm(-1j * H)
    Uc = np.conj(U)
    U4p = np.block([[U, np.zeros((2, 2))], [np.zeros((2, 2)), Uc]])
    U4m = np.block([[U.conj().T, np.zeros((2, 2))], [np.zeros((2, 2)), np.conj(U.conj().T)]])
    return U4p @ psi - U4m @ psi


AX3_CANDIDATES = [
    ("gamma5_phase", ax3_gamma5_spinor),
    ("cp_spinor", ax3_cp_spinor),
    ("parity_spinor", ax3_parity_spinor),
    ("opposite_rot", ax3_opposite_rot_spinor),
]


def run_ax3_spinor():
    n_trials = 400
    names = [n for n, _ in AX3_CANDIDATES]
    n = len(names)
    overlap = np.zeros((n, n))
    norms = np.zeros(n)
    for trial in range(n_trials):
        rng = np.random.default_rng(7100000 + trial)
        psi = random_dirac_spinor(rng)
        disps = [fn(psi) for _, fn in AX3_CANDIDATES]
        for i in range(n):
            norms[i] += np.linalg.norm(disps[i])
            for j in range(i + 1, n):
                ov = normalized_overlap(disps[i], disps[j])
                overlap[i, j] += ov
                overlap[j, i] += ov
    overlap /= n_trials
    norms /= n_trials
    return {"names": names, "overlap": overlap.tolist(), "norms": norms.tolist()}


def stage_vector(label):
    labels = ["Se", "Si", "Ne", "Ni"]
    v = np.zeros(4)
    v[labels.index(label)] = 1.0
    return v


def ax5_eta_scalar(eta, d_eta):
    return np.array([eta, np.cos(2 * eta), np.sin(2 * eta), d_eta, 0.0, 0.0], dtype=float)


def ax5_stage_onehot(eta, d_eta):
    return np.concatenate([stage_vector(classify_stage(eta, d_eta)), np.zeros(2, dtype=float)])


def ax5_stage_invariants(eta, d_eta):
    inv = stage_invariants(eta)
    return np.array(
        [inv["r1"], inv["r2"], inv["area"], inv["transverse"], inv["extrinsic_curvature"], d_eta],
        dtype=float,
    )


def ax5_torus_second_difference(eta, delta=0.08):
    e1 = max(0.01, eta - delta)
    e2 = eta
    e3 = min(np.pi / 2 - 0.01, eta + delta)
    t1 = 0.0
    t2 = 0.0
    q1 = torus_coordinates(e1, t1, t2)
    q2 = torus_coordinates(e2, t1, t2)
    q3 = torus_coordinates(e3, t1, t2)
    raw = q1 + q3 - 2 * q2
    return np.concatenate([raw, np.zeros(2, dtype=float)])


AX5_CANDIDATES = [
    ("eta_scalar", ax5_eta_scalar),
    ("stage_onehot", ax5_stage_onehot),
    ("stage_invariants", ax5_stage_invariants),
    ("torus_second_difference", ax5_torus_second_difference),
]


def run_ax5_torus():
    n_trials = 400
    names = [n for n, _ in AX5_CANDIDATES]
    pair_names = ["inner_vs_cliff", "cliff_vs_outer", "expanding_vs_compressing"]
    results = {}

    for pair in pair_names:
        disps = {name: [] for name in names}
        for trial in range(n_trials):
            rng = np.random.default_rng(8100000 + 1000 * pair_names.index(pair) + trial)
            if pair == "inner_vs_cliff":
                eta_a, eta_b = TORUS_INNER, TORUS_CLIFFORD
                d_eta = +0.1
            elif pair == "cliff_vs_outer":
                eta_a, eta_b = TORUS_CLIFFORD, TORUS_OUTER
                d_eta = +0.1
            else:
                eta_a, eta_b = TORUS_CLIFFORD + 0.05, TORUS_CLIFFORD - 0.05
                d_eta = rng.choice([-0.1, 0.1])

            for name, fn in AX5_CANDIDATES:
                if name == "torus_second_difference":
                    disp = fn(eta_b) - fn(eta_a)
                else:
                    disp = fn(eta_b, d_eta) - fn(eta_a, -d_eta)
                disps[name].append(np.asarray(disp).reshape(-1))

        overlap = np.zeros((len(names), len(names)))
        norms = np.zeros(len(names))
        for i in range(len(names)):
            for v in disps[names[i]]:
                norms[i] += np.linalg.norm(v)
            norms[i] /= n_trials
            for j in range(i + 1, len(names)):
                ov = 0.0
                for a, b in zip(disps[names[i]], disps[names[j]]):
                    ov += normalized_overlap(a, b)
                ov /= n_trials
                overlap[i, j] = ov
                overlap[j, i] = ov
        results[pair] = {"names": names, "overlap": overlap.tolist(), "norms": norms.tolist()}
    return results


def run():
    payload = {
        "schema": "SPINOR_TORUS_WIGGLE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "ax3_spinor": run_ax3_spinor(),
        "ax5_torus": run_ax5_torus(),
        "note": "Exploratory spinor/torus layer probe; no density projection for Ax3 candidates.",
    }
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "spinor_torus_wiggle.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(json.dumps(payload, indent=2))
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run()
