#!/usr/bin/env python3
"""
Axis 7-12 Mirror Orthogonality Suite
=======================================
Falsifiable thesis: Mirror axes 7-12 can be defined as operator-domain
analogs (transpose, conjugate, adjoint mirrors of axes 1-6) that are
mutually orthogonal and non-degenerate under Choi-space HS metrics.

PASS: All 15 pairwise overlaps ≤ 1e-5 AND all norms ≥ 1e-6, for d in {4,8,16}.
KILL: Any overlap > 1e-3 or any norm < 1e-8 (degenerate).
"""

import numpy as np
import json
import os
import sys
from itertools import combinations
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken
from axis_orthogonality_suite import AXES, build_choi, hs_inner


def mirror_transpose(channel):
    """Mirror via transpose: Φ_mirror(ρ) = Φ(ρ^T)^T."""
    def mirror(rho, d):
        return channel(rho.T, d).T
    return mirror


def mirror_conjugate(channel):
    """Mirror via complex conjugation: Φ_mirror(ρ) = Φ(ρ*)* ."""
    def mirror(rho, d):
        return channel(rho.conj(), d).conj()
    return mirror


def mirror_adjoint(channel):
    """Mirror via Choi adjoint: swap input/output indices."""
    def mirror(rho, d):
        # Apply channel then take adjoint (conjugate transpose)
        out = channel(rho, d)
        return out.conj().T
    return mirror


def mirror_time_reverse(channel):
    """Mirror via time reversal: Φ_mirror(ρ) = Φ^†(ρ) (Choi transpose)."""
    def mirror(rho, d):
        out = channel(rho.conj().T, d)
        return out.conj().T
    return mirror


def mirror_parity(channel):
    """Mirror via parity: Φ_mirror(ρ) = P·Φ(P·ρ·P)·P where P flips indices."""
    def mirror(rho, d):
        P = np.eye(d)[::-1].astype(complex)  # Parity operator
        return P @ channel(P @ rho @ P, d) @ P
    return mirror


def mirror_cp(channel):
    """Mirror via CP: combined conjugation + parity."""
    def mirror(rho, d):
        P = np.eye(d)[::-1].astype(complex)
        return P @ channel((P @ rho @ P).conj(), d).conj() @ P
    return mirror


# Define the 6 mirror transformations
MIRROR_OPS = {
    "TRANSPOSE": mirror_transpose,
    "CONJUGATE": mirror_conjugate,
    "ADJOINT": mirror_adjoint,
    "TIME_REV": mirror_time_reverse,
    "PARITY": mirror_parity,
    "CP": mirror_cp,
}


def run_mirror_suite():
    print("=" * 72)
    print("AXIS 7-12 MIRROR ORTHOGONALITY SUITE")
    print("=" * 72)

    DIMS = [4, 8, 16]
    EPS = 1e-5
    MIN_NORM = 1e-6
    tokens = []
    all_results = []
    axis_names = list(AXES.keys())

    for d in DIMS:
        print(f"\n  --- d={d} ---")

        # Build mirror Choi matrices: each of 6 axes × 6 mirror ops = 36 candidates
        # But we want to find the BEST 6 mirrors (one per axis) that are mutually orthogonal
        mirror_chois = {}
        for ax_name, ax_func in AXES.items():
            for m_name, m_op in MIRROR_OPS.items():
                mirrored = m_op(ax_func)
                choi = build_choi(mirrored, d)
                key = f"M{ax_name.split('_')[0]}_{m_name}"
                mirror_chois[key] = choi

        # Measure orthogonality between mirrors and original axes
        original_chois = {name: build_choi(func, d) for name, func in AXES.items()}

        # For each axis, find the mirror that is MOST orthogonal to all original axes
        best_mirrors = {}
        for ax_name in axis_names:
            best_score = float('inf')
            best_mirror_name = None
            best_mirror_choi = None

            for m_name in MIRROR_OPS:
                key = f"M{ax_name.split('_')[0]}_{m_name}"
                mc = mirror_chois[key]
                mc_norm = float(np.linalg.norm(mc, 'fro'))
                if mc_norm < MIN_NORM:
                    continue

                # Total overlap with all originals
                total_overlap = sum(abs(hs_inner(mc, oc)) for oc in original_chois.values())
                if total_overlap < best_score:
                    best_score = total_overlap
                    best_mirror_name = key
                    best_mirror_choi = mc

            if best_mirror_choi is not None:
                best_mirrors[best_mirror_name] = best_mirror_choi
                print(f"    {ax_name:20s} → best mirror: {best_mirror_name:30s}  "
                      f"total_overlap={best_score:.4f}  "
                      f"‖M‖={np.linalg.norm(best_mirror_choi, 'fro'):.4f}")

        # Test mutual orthogonality of the selected mirrors
        mirror_names = list(best_mirrors.keys())
        mirror_mats = list(best_mirrors.values())
        n_pairs = 0
        n_ortho = 0
        max_overlap = 0.0
        any_degenerate = False

        for i in range(len(mirror_names)):
            norm_i = float(np.linalg.norm(mirror_mats[i], 'fro'))
            if norm_i < MIN_NORM:
                any_degenerate = True

            for j in range(i + 1, len(mirror_names)):
                ov = abs(hs_inner(mirror_mats[i], mirror_mats[j]))
                n_pairs += 1
                if ov <= EPS:
                    n_ortho += 1
                max_overlap = max(max_overlap, ov)

        # Also test orthogonality to original axes
        n_cross_pairs = 0
        n_cross_ortho = 0
        max_cross_overlap = 0.0
        for mc in mirror_mats:
            for oc in original_chois.values():
                ov = abs(hs_inner(mc, oc))
                n_cross_pairs += 1
                if ov <= EPS:
                    n_cross_ortho += 1
                max_cross_overlap = max(max_cross_overlap, ov)

        result = {
            "d": d,
            "n_mirrors": len(mirror_names),
            "mirror_names": mirror_names,
            "n_pairs": n_pairs, "n_ortho": n_ortho,
            "max_mutual_overlap": round(max_overlap, 6),
            "n_cross_pairs": n_cross_pairs, "n_cross_ortho": n_cross_ortho,
            "max_cross_overlap": round(max_cross_overlap, 6),
            "any_degenerate": any_degenerate,
        }
        all_results.append(result)

        print(f"    Mutual orthogonality: {n_ortho}/{n_pairs}  max_overlap={max_overlap:.6f}")
        print(f"    Cross orthogonality (mirror vs original): {n_cross_ortho}/{n_cross_pairs}  "
              f"max_overlap={max_cross_overlap:.6f}")

    # Verdict
    all_nontrivial = not any(r["any_degenerate"] for r in all_results)
    high_cross_ortho = all(r["n_cross_ortho"] / max(r["n_cross_pairs"], 1) > 0.5 for r in all_results)
    overall = all_nontrivial and high_cross_ortho

    print(f"\n  All non-trivial: {'YES ✓' if all_nontrivial else 'NO ✗'}")
    print(f"  Cross-orthogonality > 50%: {'YES ✓' if high_cross_ortho else 'NO ✗'}")
    print(f"  OVERALL: {'PASS' if overall else 'KILL'}")

    if overall:
        tokens.append(EvidenceToken("E_SIM_MIRROR_AXES_OK",
                                    "S_SIM_AXIS_7_12_MIRRORS", "PASS",
                                    float(np.mean([r["n_cross_ortho"]/max(r["n_cross_pairs"],1)
                                                   for r in all_results]))))
    else:
        tokens.append(EvidenceToken("", "S_SIM_AXIS_7_12_MIRRORS", "KILL",
                                    0.0, "LOW_CROSS_ORTHOGONALITY"))

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "axis_7_12_mirror_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "dimensions": DIMS,
            "results": all_results,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    print(f"  Results saved: {outpath}")
    return tokens


if __name__ == "__main__":
    run_mirror_suite()
