#!/usr/bin/env python3
"""
Process + Geometry Wiggle Exploration
=====================================

Two bounded explorations:

1. Ax4/Ax6 process wiggle
   Test whether process-level records separate candidate process-direction
   observables from action-side observables better than endpoint state
   displacements do.

2. Ax5 geometry wiggle
   Test whether torus/extrinsic-curvature observables behave less like Ax0
   than the current entropy-shape and generic-Hamiltonian curvature proxies.

This is exploratory only. No canon claims.
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
import scipy.linalg as la

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER, coherent_state_density, torus_coordinates


sx = np.array([[0, 1], [1, 0]], dtype=complex)
I4 = np.eye(4, dtype=complex)


def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    ev, evc = np.linalg.eigh(rho)
    ev = np.maximum(ev, 0)
    rho = evc @ np.diag(ev) @ evc.conj().T
    tr = np.trace(rho)
    if abs(tr) > 1e-12:
        rho /= tr
    return rho


def normalized_overlap(A, B):
    a = np.asarray(A).reshape(-1)
    b = np.asarray(B).reshape(-1)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(abs(np.vdot(a, b)) / (na * nb))


def random_spinor(rng):
    psi = rng.normal(size=2) + 1j * rng.normal(size=2)
    psi /= np.linalg.norm(psi)
    return psi


def random_normalized_dirac_density(r, rng):
    psi_L = random_spinor(rng)
    psi_R = random_spinor(rng)
    alpha = rng.uniform(0.15, 0.85)
    phi = rng.uniform(-np.pi, np.pi)
    psi = np.concatenate(
        [np.sqrt(alpha) * psi_L, np.exp(1j * phi) * np.sqrt(1 - alpha) * psi_R]
    )
    psi /= np.linalg.norm(psi)
    rho_pure = np.outer(psi, np.conj(psi))
    rho = ensure_valid(r * rho_pure + (1 - r) * I4 / 4.0)
    return rho


def ax0_coarse(rho):
    diag = np.diag(np.diag(rho))
    return (0.2 * rho + 0.8 * diag) - (0.8 * rho + 0.2 * diag)


def ax0_coarse_2x2(rho):
    diag = np.diag(np.diag(rho))
    return (0.2 * rho + 0.8 * diag) - (0.8 * rho + 0.2 * diag)


def flatten_path(path):
    return np.concatenate([p.flatten() for p in path])


def build_maps():
    gamma = 0.25
    K0 = np.eye(4, dtype=complex)
    K0[1, 1] = np.sqrt(1 - gamma)
    K1 = np.zeros((4, 4), dtype=complex)
    K1[0, 1] = np.sqrt(gamma)

    def damping(rho):
        return ensure_valid(K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T)

    def dephase(rho):
        return 0.7 * rho + 0.3 * np.diag(np.diag(rho))

    A = np.zeros((4, 4), dtype=complex)
    A[:2, :2] = np.array([[0.5, 0.3 + 0.4j], [0.1 - 0.2j, -0.5]])
    A[2:, 2:] = np.array([[-0.3, 0.2 - 0.1j], [0.2 + 0.1j, 0.3]])
    A /= np.linalg.norm(A)

    def left_action(rho):
        return ensure_valid(A @ rho @ A.conj().T)

    def right_action(rho):
        return ensure_valid(A.conj().T @ rho @ A)

    return damping, dephase, left_action, right_action, A


def ax4_endpoint(rho):
    damping, dephase, _, _, _ = build_maps()
    return damping(dephase(rho)) - dephase(damping(rho))


def ax4_path_record(rho, n_steps=8):
    damping, dephase, _, _, _ = build_maps()
    path_ab = [rho]
    path_ba = [rho]
    ra = rho.copy()
    rb = rho.copy()
    for _ in range(n_steps):
        ra = damping(dephase(ra))
        rb = dephase(damping(rb))
        path_ab.append(ra)
        path_ba.append(rb)
    return flatten_path(path_ab) - flatten_path(path_ba)


def ax6_endpoint(rho):
    _, _, _, _, A = build_maps()
    return A @ rho - rho @ A


def ax6_path_record(rho, n_steps=8):
    _, _, left_action, right_action, _ = build_maps()
    path_l = [rho]
    path_r = [rho]
    rl = rho.copy()
    rr = rho.copy()
    for _ in range(n_steps):
        rl = left_action(rl)
        rr = right_action(rr)
        path_l.append(rl)
        path_r.append(rr)
    return flatten_path(path_l) - flatten_path(path_r)


def ax5_generic_curvature(rho):
    H_curved = np.zeros((4, 4), dtype=complex)
    H_curved[:2, :2] = np.array([[0.3, 0.2 + 0.1j], [0.2 - 0.1j, -0.3]])
    H_curved[2:, 2:] = np.array([[-0.1, 0.3 - 0.2j], [0.3 + 0.2j, 0.1]])
    H_curved /= np.linalg.norm(H_curved)
    eps = 0.2
    U1 = la.expm(-1j * H_curved * eps)
    U2 = la.expm(-1j * H_curved * 2 * eps)
    rho_eps = U1 @ rho @ U1.conj().T
    rho_2eps = U2 @ rho @ U2.conj().T
    curv_high = rho_2eps - 2 * rho_eps + rho
    diag = np.diag(np.diag(rho))
    rho_eps_l = (1 - eps) * rho + eps * diag
    rho_2eps_l = (1 - 2 * eps) * rho + 2 * eps * diag
    curv_low = rho_2eps_l - 2 * rho_eps_l + rho
    return curv_high - curv_low


def torus_state(eta, t1, t2):
    return coherent_state_density(torus_coordinates(eta, t1, t2))


def ax5_torus_extrinsic_transport(rng):
    t1 = rng.uniform(0, 2 * np.pi)
    t2 = rng.uniform(0, 2 * np.pi)
    rho_inner = torus_state(TORUS_INNER, t1, t2)
    rho_cliff = torus_state(TORUS_CLIFFORD, t1, t2)
    rho_outer = torus_state(TORUS_OUTER, t1, t2)
    return (rho_inner + rho_outer - 2 * rho_cliff)


def ax5_torus_curvature_scalar(rng):
    t1 = rng.uniform(0, 2 * np.pi)
    t2 = rng.uniform(0, 2 * np.pi)
    etas = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    parts = []
    for eta in etas:
        rho = torus_state(eta, t1, t2)
        k = np.cos(2 * eta)
        parts.append(k * rho.flatten())
    return np.concatenate(parts)


def run_process_wiggle():
    n_trials = 300
    r_values = [1.0, 0.7, 0.4, 0.2]
    out = {}
    for r in r_values:
        vals = {"ax4_endpoint_vs_ax6_endpoint": 0.0, "ax4_path_vs_ax6_path": 0.0, "ax4_path_vs_ax6_endpoint": 0.0}
        norms = {"ax4_endpoint": 0.0, "ax4_path": 0.0, "ax6_endpoint": 0.0, "ax6_path": 0.0}
        for trial in range(n_trials):
            rng = np.random.default_rng(5100000 + int(r * 1000) * 1000 + trial)
            rho = random_normalized_dirac_density(r, rng)
            d4e = ax4_endpoint(rho)
            d4p = ax4_path_record(rho)
            d6e = ax6_endpoint(rho)
            d6p = ax6_path_record(rho)
            vals["ax4_endpoint_vs_ax6_endpoint"] += normalized_overlap(d4e, d6e)
            vals["ax4_path_vs_ax6_path"] += normalized_overlap(d4p, d6p)
            vals["ax4_path_vs_ax6_endpoint"] += normalized_overlap(d4p, d6e)
            norms["ax4_endpoint"] += np.linalg.norm(d4e)
            norms["ax4_path"] += np.linalg.norm(d4p)
            norms["ax6_endpoint"] += np.linalg.norm(d6e)
            norms["ax6_path"] += np.linalg.norm(d6p)
        out[f"r={r}"] = {
            "overlaps": {k: v / n_trials for k, v in vals.items()},
            "norms": {k: v / n_trials for k, v in norms.items()},
        }
    return out


def run_geometry_wiggle():
    n_trials = 300
    out = {"ax0_vs_generic_curvature": 0.0, "ax0_vs_torus_extrinsic_transport": 0.0, "ax0_vs_torus_curvature_scalar": 0.0}
    norms = {"ax0": 0.0, "generic_curvature": 0.0, "torus_extrinsic_transport": 0.0, "torus_curvature_scalar": 0.0}
    for trial in range(n_trials):
        rng = np.random.default_rng(6100000 + trial)
        rho = random_normalized_dirac_density(0.6, rng)
        d0 = ax0_coarse(rho)
        d5g = ax5_generic_curvature(rho)
        d5t = ax5_torus_extrinsic_transport(rng)
        d5s = ax5_torus_curvature_scalar(rng)
        t1 = rng.uniform(0, 2 * np.pi)
        t2 = rng.uniform(0, 2 * np.pi)
        rho_cliff = torus_state(TORUS_CLIFFORD, t1, t2)
        d0_torus = ax0_coarse_2x2(rho_cliff)
        out["ax0_vs_generic_curvature"] += normalized_overlap(d0, d5g)
        out["ax0_vs_torus_extrinsic_transport"] += normalized_overlap(d0_torus, d5t)
        out["ax0_vs_torus_curvature_scalar"] += normalized_overlap(np.tile(d0_torus.flatten(), 3), d5s)
        norms["ax0"] += np.linalg.norm(d0)
        norms["generic_curvature"] += np.linalg.norm(d5g)
        norms["torus_extrinsic_transport"] += np.linalg.norm(d5t)
        norms["torus_curvature_scalar"] += np.linalg.norm(d5s)
    return {
        "overlaps": {k: v / n_trials for k, v in out.items()},
        "norms": {k: v / n_trials for k, v in norms.items()},
    }


def run():
    process = run_process_wiggle()
    geometry = run_geometry_wiggle()
    payload = {
        "schema": "PROCESS_GEOMETRY_WIGGLE_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "process_wiggle": process,
        "geometry_wiggle": geometry,
        "note": "Exploratory process/geometry wiggle; normalized states; not canon.",
    }
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "process_geometry_wiggle.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(json.dumps(payload, indent=2))
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run()
