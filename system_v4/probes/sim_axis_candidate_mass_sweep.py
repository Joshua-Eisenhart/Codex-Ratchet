#!/usr/bin/env python3
"""
Axis Candidate Mass Sweep on Normalized Weyl-Dirac States
=========================================================

Purpose:
  Do not freeze a single guessed math for Ax3/Ax4/Ax5/Ax6 too early.
  Instead, sweep multiple candidate operationalizations on a corrected
  normalized 4x4 Dirac-density construction and measure which signals
  survive across entropy and Weyl-weight regimes.

State model:
  - Sample two normalized Weyl spinors psi_L, psi_R in C^2
  - Sample chirality weight alpha in (0,1) and relative phase phi
  - Build normalized Dirac spinor:
      Psi = [sqrt(alpha) psi_L, exp(i phi) sqrt(1-alpha) psi_R]
  - Build rho_pure = |Psi><Psi|
  - Build mixed state rho = r rho_pure + (1-r) I/4
  - Normalize / project to valid density operator

Output:
  - Candidate norms by entropy
  - Pairwise overlaps between all tested candidates
  - Best / worst surviving constructions
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
import scipy.linalg as la
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)
GAMMA5 = np.block([[I2, np.zeros((2, 2))], [np.zeros((2, 2)), -I2]])


def ensure_valid(rho: np.ndarray) -> np.ndarray:
    rho = (rho + rho.conj().T) / 2
    ev, evc = np.linalg.eigh(rho)
    ev = np.maximum(ev, 0.0)
    rho = evc @ np.diag(ev) @ evc.conj().T
    tr = np.trace(rho)
    if abs(tr) > 1e-12:
        rho /= tr
    return rho


def normalized_overlap(A: np.ndarray, B: np.ndarray) -> float:
    nA = np.linalg.norm(A, "fro")
    nB = np.linalg.norm(B, "fro")
    if nA < 1e-12 or nB < 1e-12:
        return 0.0
    return float(abs(np.trace(A.conj().T @ B)) / (nA * nB))


def random_spinor(rng: np.random.Generator) -> np.ndarray:
    psi = rng.normal(size=2) + 1j * rng.normal(size=2)
    psi /= np.linalg.norm(psi)
    return psi


def random_normalized_dirac_density(r: float, rng: np.random.Generator):
    psi_L = random_spinor(rng)
    psi_R = random_spinor(rng)
    alpha = rng.uniform(0.15, 0.85)
    phi = rng.uniform(-np.pi, np.pi)
    psi = np.concatenate(
        [np.sqrt(alpha) * psi_L, np.exp(1j * phi) * np.sqrt(1.0 - alpha) * psi_R]
    )
    psi /= np.linalg.norm(psi)
    rho_pure = np.outer(psi, np.conj(psi))
    rho = r * rho_pure + (1.0 - r) * I4 / 4.0
    rho = ensure_valid(rho)
    return rho, psi_L, psi_R, alpha, phi, psi


def block_swap() -> np.ndarray:
    P = np.zeros((4, 4), dtype=complex)
    P[0, 2] = 1
    P[1, 3] = 1
    P[2, 0] = 1
    P[3, 1] = 1
    return P


P_SWAP = block_swap()


def ax0_coarse(rho, *_):
    diag = np.diag(np.diag(rho))
    return (0.2 * rho + 0.8 * diag) - (0.8 * rho + 0.2 * diag)


def ax1_dissipation(rho, *_):
    H = np.zeros((4, 4), dtype=complex)
    H[0, 0] = 0.3
    H[1, 1] = -0.3
    U = la.expm(-1j * H)
    rho_u = U @ rho @ U.conj().T

    g = 0.3
    K0 = np.eye(4, dtype=complex)
    K0[1, 1] = np.sqrt(1 - g)
    K1 = np.zeros((4, 4), dtype=complex)
    K1[0, 1] = np.sqrt(g)
    rho_c = K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T
    rho_c = ensure_valid(rho_c)
    return rho_c - rho_u


def ax2_boundary(rho, *_):
    P = np.diag([1.0, 0.7, 1.0, 0.7]).astype(complex)
    rho_e = ensure_valid(P @ rho @ P.conj().T)
    H = np.zeros((4, 4), dtype=complex)
    H[:2, :2] = sx * 0.5
    rho_l = la.expm(-1j * H) @ rho @ la.expm(1j * H)
    return rho_e - rho_l


def ax3_cp_mirror(rho, *_):
    rho_p = P_SWAP @ rho @ P_SWAP.conj().T
    rho_cp = np.conj(rho_p)
    return rho - rho_cp


def ax3_parity_exchange(rho, *_):
    return rho - (P_SWAP @ rho @ P_SWAP.conj().T)


def ax3_gamma5_phase(rho, *_):
    theta = 0.45
    U_plus = la.expm(1j * theta * GAMMA5)
    U_minus = la.expm(-1j * theta * GAMMA5)
    rho_plus = U_plus @ rho @ U_plus.conj().T
    rho_minus = U_minus @ rho @ U_minus.conj().T
    return rho_plus - rho_minus


def ax4_composition_order(rho, *_):
    def mA(r_):
        return 0.7 * r_ + 0.3 * np.diag(np.diag(r_))

    gamma = 0.2
    K0 = np.eye(4, dtype=complex)
    K0[1, 1] = np.sqrt(1 - gamma)
    K1 = np.zeros((4, 4), dtype=complex)
    K1[0, 1] = np.sqrt(gamma)

    def mB(r_):
        return ensure_valid(K0 @ r_ @ K0.conj().T + K1 @ r_ @ K1.conj().T)

    return mB(mA(rho)) - mA(mB(rho))


def ax4_path_direction(rho, *_):
    n_steps = 16
    H = np.zeros((4, 4), dtype=complex)
    H[:2, :2] = np.array([[0.3, 0.1 + 0.2j], [0.1 - 0.2j, -0.3]])
    H[2:, 2:] = np.array([[-0.2, 0.15 - 0.1j], [0.15 + 0.1j, 0.2]])
    H /= np.linalg.norm(H)
    angles = np.linspace(0, 2 * np.pi, n_steps, endpoint=False)
    path_cw = np.zeros((4, 4), dtype=complex)
    path_ccw = np.zeros((4, 4), dtype=complex)
    for a in angles:
        U_cw = la.expm(-1j * H * a * 0.3)
        U_ccw = la.expm(1j * H * a * 0.3)
        path_cw += U_cw @ rho @ U_cw.conj().T
        path_ccw += U_ccw @ rho @ U_ccw.conj().T
    return (path_cw - path_ccw) / n_steps


def ax4_process_commutator(rho, *_):
    A = np.zeros((4, 4), dtype=complex)
    A[:2, :2] = np.array([[0.5, 0.2 + 0.1j], [0.2 - 0.1j, -0.5]])
    B = np.zeros((4, 4), dtype=complex)
    B[2:, 2:] = np.array([[-0.4, 0.3 - 0.2j], [0.3 + 0.2j, 0.4]])
    A /= np.linalg.norm(A)
    B /= np.linalg.norm(B)
    UA = la.expm(-1j * A * 0.25)
    UB = la.expm(-1j * B * 0.25)
    rho_ab = UB @ (UA @ rho @ UA.conj().T) @ UB.conj().T
    rho_ba = UA @ (UB @ rho @ UB.conj().T) @ UA.conj().T
    return rho_ab - rho_ba


def ax5_curvature_geodesic(rho, *_):
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


def ax5_entropy_shape(rho, *_):
    diag = np.diag(np.diag(rho))
    anti = rho + rho.conj().T
    anti /= max(np.linalg.norm(anti, "fro"), 1e-12)
    return anti - diag


def ax6_action_side(rho, *_):
    A = np.zeros((4, 4), dtype=complex)
    A[:2, :2] = np.array([[0.5, 0.3 + 0.4j], [0.1 - 0.2j, -0.5]])
    A[2:, 2:] = np.array([[-0.3, 0.2 - 0.1j], [0.2 + 0.1j, 0.3]])
    A /= np.linalg.norm(A)
    return A @ rho - rho @ A


def ax6_left_right_channel(rho, *_):
    A = np.zeros((4, 4), dtype=complex)
    A[:2, :2] = np.array([[0.6, 0.2], [0.2, -0.6]], dtype=complex)
    A[2:, 2:] = np.array([[-0.4, 0.3j], [-0.3j, 0.4]], dtype=complex)
    A /= np.linalg.norm(A)
    left = ensure_valid(A @ rho @ A.conj().T)
    right = ensure_valid(A.conj().T @ rho @ A)
    return left - right


CANDIDATES = [
    ("Ax0_coarse", "Ax0", ax0_coarse),
    ("Ax1_dissipation", "Ax1", ax1_dissipation),
    ("Ax2_boundary", "Ax2", ax2_boundary),
    ("Ax3_cp_mirror", "Ax3", ax3_cp_mirror),
    ("Ax3_parity_exchange", "Ax3", ax3_parity_exchange),
    ("Ax3_gamma5_phase", "Ax3", ax3_gamma5_phase),
    ("Ax4_composition_order", "Ax4", ax4_composition_order),
    ("Ax4_path_direction", "Ax4", ax4_path_direction),
    ("Ax4_process_commutator", "Ax4", ax4_process_commutator),
    ("Ax5_curvature_geodesic", "Ax5", ax5_curvature_geodesic),
    ("Ax5_entropy_shape", "Ax5", ax5_entropy_shape),
    ("Ax6_action_side", "Ax6", ax6_action_side),
    ("Ax6_left_right_channel", "Ax6", ax6_left_right_channel),
]


def run():
    n_trials = 300
    r_values = [1.0, 0.8, 0.6, 0.4, 0.2]
    n_c = len(CANDIDATES)
    results = {}

    print("=" * 88)
    print("AXIS CANDIDATE MASS SWEEP")
    print(f"{n_trials} trials per entropy; normalized Weyl-Dirac mixed states")
    print("=" * 88)

    for r in r_values:
        overlap = np.zeros((n_c, n_c))
        norms = np.zeros(n_c)
        alpha_vals = []

        for trial in range(n_trials):
            rng = np.random.default_rng(2700000 + int(r * 1000) * 10000 + trial)
            rho, psi_L, psi_R, alpha, phi, psi = random_normalized_dirac_density(r, rng)
            alpha_vals.append(alpha)
            disps = [fn(rho, psi_L, psi_R, alpha, phi, psi) for _, _, fn in CANDIDATES]
            for i in range(n_c):
                norms[i] += np.linalg.norm(disps[i], "fro")
                for j in range(i + 1, n_c):
                    ov = normalized_overlap(disps[i], disps[j])
                    overlap[i, j] += ov
                    overlap[j, i] += ov

        overlap /= n_trials
        norms /= n_trials

        family_best = {}
        for i, (name, family, _) in enumerate(CANDIDATES):
            family_best.setdefault(family, []).append(
                {
                    "name": name,
                    "norm": float(norms[i]),
                    "max_overlap": float(max(overlap[i, j] for j in range(n_c) if j != i)),
                }
            )
        for family in family_best:
            family_best[family].sort(key=lambda x: (x["max_overlap"], -x["norm"]))

        results[f"r={r}"] = {
            "mean_alpha": float(np.mean(alpha_vals)),
            "candidate_names": [c[0] for c in CANDIDATES],
            "families": [c[1] for c in CANDIDATES],
            "norms": norms.tolist(),
            "overlap": overlap.tolist(),
            "family_best": family_best,
        }

        print(f"\n--- r={r} ---")
        for family in ["Ax3", "Ax4", "Ax5", "Ax6"]:
            best = family_best[family][0]
            print(
                f"{family}: best={best['name']} norm={best['norm']:.4f} max_ov={best['max_overlap']:.4f}"
            )

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "axis_candidate_mass_sweep.json")
    payload = {
        "schema": "AXIS_CANDIDATE_MASS_SWEEP_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_trials": n_trials,
        "r_values": r_values,
        "results": results,
        "note": "Exploratory candidate sweep on normalized Weyl-Dirac mixed states; not canon.",
    }
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run()
