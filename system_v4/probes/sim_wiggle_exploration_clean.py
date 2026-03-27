#!/usr/bin/env python3
"""
Clean Wiggle Exploration
========================

This is a methodological cleanup of the broad wiggle sweep:
- remove exact duplicate candidate labels across axes
- mark dead candidates and exclude them from intra-axis agreement
- sweep multiple r values instead of one operating point

Still non-canon. Still exploratory.
"""

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np
import scipy.linalg as la

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

sx = np.array([[0, 1], [1, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)


def make_state(r, rng):
    psi_L = rng.normal(size=2) + 1j * rng.normal(size=2)
    psi_L /= np.linalg.norm(psi_L)
    psi_R = rng.normal(size=2) + 1j * rng.normal(size=2)
    psi_R /= np.linalg.norm(psi_R)
    psi = np.concatenate([psi_L, psi_R])
    psi /= np.linalg.norm(psi)
    rho_pure = np.outer(psi, np.conj(psi))
    rho = r * rho_pure + (1 - r) * np.eye(4, dtype=complex) / 4
    return rho, psi_L, psi_R


def noverlap(A, B):
    nA = np.linalg.norm(A, "fro")
    nB = np.linalg.norm(B, "fro")
    if nA < 1e-12 or nB < 1e-12:
        return 0.0
    return float(abs(np.trace(A.conj().T @ B)) / (nA * nB))


def ax0_A(rho, pL, pR):
    diag = np.diag(np.diag(rho))
    return rho - diag


def ax0_C(rho, pL, pR):
    ev, evc = np.linalg.eigh(rho)
    rho_top = np.outer(evc[:, -1], np.conj(evc[:, -1]))
    return rho - rho_top


def ax1_A(rho, pL, pR):
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
    rho_c /= max(abs(np.trace(rho_c)), 1e-12)
    return rho_c - rho_u


def ax1_B(rho, pL, pR):
    L = np.zeros((4, 4), dtype=complex)
    for k in range(3):
        L[k, k + 1] = 0.3
    lind = L @ rho @ L.conj().T - 0.5 * (L.conj().T @ L @ rho + rho @ L.conj().T @ L)
    H = np.zeros((4, 4), dtype=complex)
    H[:2, :2] = sz * 0.3
    ham = -1j * (H @ rho - rho @ H)
    return lind - ham


def ax2_A(rho, pL, pR):
    P = np.diag([1.0, 0.7, 1.0, 0.7]).astype(complex)
    rho_e = P @ rho @ P.conj().T
    rho_e /= max(abs(np.trace(rho_e)), 1e-12)
    H = np.zeros((4, 4), dtype=complex)
    H[:2, :2] = sx * 0.5
    rho_l = la.expm(-1j * H) @ rho @ la.expm(1j * H)
    return rho_e - rho_l


def ax2_C(rho, pL, pR):
    block = np.zeros_like(rho)
    block[:2, :2] = rho[:2, :2]
    block[2:, 2:] = rho[2:, 2:]
    return block - rho


def ax3_B(rho, pL, pR):
    P = np.zeros((4, 4), dtype=complex)
    P[0, 2] = 1
    P[1, 3] = 1
    P[2, 0] = 1
    P[3, 1] = 1
    rho_P = P @ rho @ P.conj().T
    return rho - rho_P


def ax3_C(rho, pL, pR):
    P = np.zeros((4, 4), dtype=complex)
    P[0, 2] = 1
    P[1, 3] = 1
    P[2, 0] = 1
    P[3, 1] = 1
    rho_P = P @ rho @ P.conj().T
    rho_CP = np.conj(rho_P)
    return rho - rho_CP


def ax3_D(rho, pL, pR):
    g5 = np.diag([1.0, 1.0, -1.0, -1.0]).astype(complex)
    return g5 @ rho - rho @ g5


def ax4_B(rho, pL, pR):
    n = 16
    H = np.zeros((4, 4), dtype=complex)
    H[:2, :2] = np.array([[0.3, 0.1 + 0.2j], [0.1 - 0.2j, -0.3]])
    H[2:, 2:] = np.array([[-0.2, 0.15 - 0.1j], [0.15 + 0.1j, 0.2]])
    H /= np.linalg.norm(H)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pcw = np.zeros_like(rho)
    pccw = np.zeros_like(rho)
    for t in range(n):
        Ucw = la.expm(-1j * H * ang[t] * 0.3)
        Uccw = la.expm(-1j * H * (-ang[t]) * 0.3)
        pcw += Ucw @ rho @ Ucw.conj().T
        pccw += Uccw @ rho @ Uccw.conj().T
    return (pcw - pccw) / n


def ax5_A(rho, pL, pR):
    H = np.zeros((4, 4), dtype=complex)
    H[:2, :2] = np.array([[0.3, 0.2 + 0.1j], [0.2 - 0.1j, -0.3]])
    H[2:, 2:] = np.array([[-0.1, 0.3 - 0.2j], [0.3 + 0.2j, 0.1]])
    H /= np.linalg.norm(H)
    eps = 0.2
    U1 = la.expm(-1j * H * eps)
    U2 = la.expm(-1j * H * 2 * eps)
    curv_h = U2 @ rho @ U2.conj().T - 2 * (U1 @ rho @ U1.conj().T) + rho
    diag = np.diag(np.diag(rho))
    curv_l = (1 - 2 * eps) * rho + 2 * eps * diag - 2 * ((1 - eps) * rho + eps * diag) + rho
    return curv_h - curv_l


def ax5_B(rho, pL, pR):
    A = np.zeros((4, 4), dtype=complex)
    for i in range(4):
        A[i, i] = (2 * i - 3) / 4
    sharp = A @ rho - rho @ A
    smooth = (A @ rho + rho @ A) / 2
    return sharp - smooth


def ax6_A(rho, pL, pR):
    A = np.zeros((4, 4), dtype=complex)
    A[:2, :2] = np.array([[0.5, 0.3 + 0.4j], [0.1 - 0.2j, -0.5]])
    A[2:, 2:] = np.array([[-0.3, 0.2 - 0.1j], [0.2 + 0.1j, 0.3]])
    A /= np.linalg.norm(A)
    return A @ rho - rho @ A


def ax6_B(rho, pL, pR):
    g5 = np.diag([1.0, -1.0, 1.0, -1.0]).astype(complex)
    return g5 @ rho - rho @ g5


def ax6_D(rho, pL, pR):
    ev, evc = np.linalg.eigh(rho)
    ev_s = np.sqrt(np.maximum(ev, 0))
    rho_sqrt = evc @ np.diag(ev_s) @ evc.conj().T
    A = np.zeros((4, 4), dtype=complex)
    A[:2, :2] = sx * 0.3
    A[2:, 2:] = sz * 0.3
    return rho_sqrt @ A - A @ rho_sqrt


ALL_CANDIDATES = [
    ("ax0_A", "ax0", ax0_A),
    ("ax0_C", "ax0", ax0_C),
    ("ax1_A", "ax1", ax1_A),
    ("ax1_B", "ax1", ax1_B),
    ("ax2_A", "ax2", ax2_A),
    ("ax2_C", "ax2", ax2_C),
    ("ax3_B", "ax3", ax3_B),
    ("ax3_C", "ax3", ax3_C),
    ("ax3_D", "ax3", ax3_D),
    ("ax4_B", "ax4", ax4_B),
    ("ax5_A", "ax5", ax5_A),
    ("ax5_B", "ax5", ax5_B),
    ("ax6_A", "ax6", ax6_A),
    ("ax6_B", "ax6", ax6_B),
    ("ax6_D", "ax6", ax6_D),
]


def run():
    n_trials = 200
    r_values = [1.0, 0.7, 0.5, 0.3]
    dead_threshold = 1e-2
    all_results = {}

    for r in r_values:
        n_cands = len(ALL_CANDIDATES)
        overlap = np.zeros((n_cands, n_cands))
        norms = np.zeros(n_cands)
        for trial in range(n_trials):
            rng = np.random.default_rng(trial + 3100000 + int(r * 1000))
            rho, pL, pR = make_state(r, rng)
            disps = []
            for _, _, fn in ALL_CANDIDATES:
                try:
                    disps.append(fn(rho, pL, pR))
                except Exception:
                    disps.append(np.zeros((4, 4), dtype=complex))
            for i in range(n_cands):
                norms[i] += np.linalg.norm(disps[i], "fro")
                for j in range(i + 1, n_cands):
                    ov = noverlap(disps[i], disps[j])
                    overlap[i, j] += ov
                    overlap[j, i] += ov
        overlap /= n_trials
        norms /= n_trials

        groups = {}
        for idx, (name, axis, _) in enumerate(ALL_CANDIDATES):
            groups.setdefault(axis, []).append(idx)

        intra = {}
        for axis, idxs in groups.items():
            live = [i for i in idxs if norms[i] >= dead_threshold]
            dead = [ALL_CANDIDATES[i][0] for i in idxs if norms[i] < dead_threshold]
            pairs = []
            for i in range(len(live)):
                for j in range(i + 1, len(live)):
                    pairs.append(overlap[live[i], live[j]])
            intra[axis] = {
                "live_candidates": [ALL_CANDIDATES[i][0] for i in live],
                "dead_candidates": dead,
                "pair_count": len(pairs),
                "min_overlap": float(min(pairs)) if pairs else None,
                "max_overlap": float(max(pairs)) if pairs else None,
                "avg_overlap": float(sum(pairs) / len(pairs)) if pairs else None,
            }

        all_results[f"r={r}"] = {
            "candidates": [c[0] for c in ALL_CANDIDATES],
            "axes": [c[1] for c in ALL_CANDIDATES],
            "overlap": overlap.tolist(),
            "norms": norms.tolist(),
            "intra_axis": intra,
        }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    payload = {
        "schema": "WIGGLE_EXPLORATION_CLEAN_v1",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "n_trials": n_trials,
        "r_values": r_values,
        "dead_threshold": dead_threshold,
        "results": all_results,
        "note": "Deduped broad wiggle rerun; dead candidates excluded from intra-axis agreement.",
    }
    out_file = os.path.join(out_dir, "wiggle_exploration_clean.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(json.dumps(payload, indent=2))
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    run()
