#!/usr/bin/env python3
"""
Axis-5 Discrete Calculus Rosetta SIM
======================================
Falsifiable thesis: Axis-5 Wave/Line families implement two non-equivalent
discrete operator algebras that behave like integration-type (smoothing) vs
differentiation-type (boundary extraction), with strict non-triviality.

EvidenceToken: PASS if HS overlap < 1e-5 AND both Choi norms > 1e-6.
"""

import numpy as np
import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken, von_neumann_entropy


def make_fourier(d):
    F = np.zeros((d, d), dtype=complex)
    for j in range(d):
        for k in range(d):
            F[j, k] = np.exp(2j * np.pi * j * k / d) / np.sqrt(d)
    return F


def wave_channel(rho, d):
    """Integration-type: Laplacian smoothing + Fourier mixing (Wave/FeFi)."""
    Lap = np.zeros((d, d), dtype=complex)
    for i in range(d):
        Lap[i, i] = -2.0
        if i > 0: Lap[i, i - 1] = 1.0
        if i < d - 1: Lap[i, i + 1] = 1.0
    Lap /= d
    eLap = np.eye(d, dtype=complex) + Lap * 0.05
    rho_smooth = eLap @ rho @ eLap.conj().T
    F = make_fourier(d)
    return F @ rho_smooth @ F.conj().T


def line_channel(rho, d):
    """Differentiation-type: Gradient partition + Dirac projection (Line/TeTi)."""
    G = np.zeros((d, d), dtype=complex)
    for i in range(d - 1):
        G[i, i] = -1.0
        G[i, i + 1] = 1.0
    # Normalize by Frobenius norm (not by d) to prevent collapse at high dims
    G_norm = np.linalg.norm(G, 'fro')
    if G_norm > 1e-12:
        G = G / G_norm
    rho_grad = G @ rho @ G.conj().T
    # Enforce trace-1 PSD after gradient extraction
    tr = np.real(np.trace(rho_grad))
    if tr > 1e-12:
        rho_grad /= tr
    else:
        rho_grad = np.eye(d, dtype=complex) / d
    return np.diag(np.diagonal(rho_grad)).astype(complex)


def build_choi(channel, d):
    """Choi-Jamiołkowski representation."""
    choi = np.zeros((d ** 2, d ** 2), dtype=complex)
    for i in range(d):
        for j in range(d):
            E = np.zeros((d, d), dtype=complex)
            E[i, j] = 1.0
            out = channel(E, d)
            for u in range(d):
                for v in range(d):
                    choi[i * d + u, j * d + v] = out[u, v]
    return choi / d


def hs_inner(A, B):
    raw = np.real(np.trace(A.conj().T @ B))
    nA = np.real(np.trace(A.conj().T @ A))
    nB = np.real(np.trace(B.conj().T @ B))
    denom = np.sqrt(max(nA, 1e-30) * max(nB, 1e-30))
    return raw / denom


def run_calculus_rosetta():
    print("=" * 72)
    print("AXIS-5 DISCRETE CALCULUS ROSETTA SIM")
    print("=" * 72)

    DIMS = [4, 8, 16, 32]
    EPS = 1e-5
    MIN_NORM = 1e-6
    tokens = []
    all_results = []

    for d in DIMS:
        J_wave = build_choi(wave_channel, d)
        J_line = build_choi(line_channel, d)

        norm_wave = float(np.linalg.norm(J_wave, 'fro'))
        norm_line = float(np.linalg.norm(J_line, 'fro'))
        overlap = float(hs_inner(J_wave, J_line))

        # Demonstrate effect: apply to maximally mixed state
        rho_test = np.eye(d, dtype=complex) / d
        rho_wave = wave_channel(rho_test, d)
        rho_line = line_channel(rho_test, d)
        S_wave = von_neumann_entropy(rho_wave)
        S_line = von_neumann_entropy(rho_line)

        trivial_wave = norm_wave < MIN_NORM
        trivial_line = norm_line < MIN_NORM
        orthogonal = abs(overlap) < EPS

        status = "PASS" if (orthogonal and not trivial_wave and not trivial_line) else "KILL"
        kill_reason = ""
        if trivial_wave:
            kill_reason = "NULL_WAVE_CHOI"
        elif trivial_line:
            kill_reason = "NULL_LINE_CHOI"
        elif not orthogonal:
            kill_reason = f"OVERLAP={overlap:.6f}"

        result = {
            "d": d, "overlap": overlap,
            "norm_wave": norm_wave, "norm_line": norm_line,
            "S_wave": S_wave, "S_line": S_line,
            "status": status, "kill_reason": kill_reason,
        }
        all_results.append(result)

        print(f"  d={d:3d}  overlap={overlap:+.2e}  ‖wave‖={norm_wave:.4f}  ‖line‖={norm_line:.4f}  "
              f"S_wave={S_wave:.3f}  S_line={S_line:.3f}  [{status}]")

    all_pass = all(r["status"] == "PASS" for r in all_results)
    if all_pass:
        tokens.append(EvidenceToken("E_SIM_CALCULUS_ROSETTA_OK", "S_SIM_AXIS5_CALCULUS_ROSETTA", "PASS",
                                    float(np.mean([abs(r["overlap"]) for r in all_results]))))
    else:
        tokens.append(EvidenceToken("", "S_SIM_AXIS5_CALCULUS_ROSETTA", "KILL",
                                    float(np.mean([abs(r["overlap"]) for r in all_results])),
                                    "DIMENSION_DEPENDENT_FAILURE"))

    print(f"\n  OVERALL: {'PASS ✓' if all_pass else 'KILL ✗'}")

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "axis5_discrete_calculus_rosetta_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "dimensions": DIMS, "epsilon": EPS, "min_norm": MIN_NORM,
            "results": all_results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_calculus_rosetta()
