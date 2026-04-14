#!/usr/bin/env python3
"""
Geometry Negative: Transport-Delta Joint Ablation
=================================================

Same-carrier proxy check for the surviving pre-Axis candidate branch:
  chirality-separated loop-sensitive transport deltas.

We compare four conditions on the same Hopf carrier sample:
  1. live chiral + true base traversal
  2. no chirality + true base traversal
  3. live chiral + swapped(base->fiber) law
  4. no chirality + swapped(base->fiber) law

This is a proxy witness, not a final theorem. It asks whether the candidate
branch remains strongest only when both chirality separation and loop-law
assignment are present together.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

import numpy as np

classification = "canonical"

from hopf_manifold import (
    TORUS_CLIFFORD,
    TORUS_INNER,
    TORUS_OUTER,
    fiber_phase_left,
    fiber_phase_right,
    left_weyl_spinor,
    right_weyl_spinor,
    torus_coordinates,
)


RESULTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state",
    "sim_results",
    "neg_transport_delta_joint_ablation_results.json",
)


def density(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, psi.conj())


def frob(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b, ord="fro"))


def base_coords(phi0: float, chi0: float, eta: float, u: float) -> tuple[float, float]:
    return (phi0 - np.cos(2 * eta) * u, chi0 + u)


def branch_score(
    rho_L0: np.ndarray,
    rho_R0: np.ndarray,
    rho_L_next: np.ndarray,
    rho_R_next: np.ndarray,
) -> dict:
    traversal = max(frob(rho_L_next, rho_L0), frob(rho_R_next, rho_R0))
    split = frob(rho_L_next, rho_R_next)
    return {
        "traversal": float(traversal),
        "split": float(split),
        "score": float(traversal * split),
    }


def direct_runtime(
    rho_L0: np.ndarray,
    rho_R0: np.ndarray,
    rho_L_next: np.ndarray,
    rho_R_next: np.ndarray,
) -> dict:
    traversal_L = frob(rho_L_next, rho_L0)
    traversal_R = frob(rho_R_next, rho_R0)
    split_next = frob(rho_L_next, rho_R_next)
    return {
        "traversal_L": float(traversal_L),
        "traversal_R": float(traversal_R),
        "min_traversal": float(min(traversal_L, traversal_R)),
        "max_traversal": float(max(traversal_L, traversal_R)),
        "sheet_split": float(split_next),
    }


def run() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    rng = np.random.default_rng(42)
    etas = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    u = np.pi / 4

    cases = []
    live_scores = []
    flat_scores = []
    swapped_scores = []
    combined_scores = []

    for eta in etas:
        for trial in range(4):
            phi0 = float(rng.uniform(0, 2 * np.pi))
            chi0 = float(rng.uniform(0, 2 * np.pi))
            phi_b, chi_b = base_coords(phi0, chi0, eta, u)

            q0 = torus_coordinates(eta, phi0, chi0)
            q_b = torus_coordinates(eta, phi_b, chi_b)

            psi_L0 = left_weyl_spinor(q0)
            psi_R0 = right_weyl_spinor(q0)
            rho_L0 = density(psi_L0)
            rho_R0 = density(psi_R0)

            psi_L_base = left_weyl_spinor(q_b)
            psi_R_base = right_weyl_spinor(q_b)
            rho_L_base = density(psi_L_base)
            rho_R_base = density(psi_R_base)

            psi_L_fiber = fiber_phase_left(psi_L0, u)
            psi_R_fiber = fiber_phase_right(psi_R0, u)
            rho_L_fiber = density(psi_L_fiber)
            rho_R_fiber = density(psi_R_fiber)

            live = branch_score(rho_L0, rho_R0, rho_L_base, rho_R_base)
            no_chirality = branch_score(rho_L0, rho_L0, rho_L_base, rho_L_base)
            swapped = branch_score(rho_L0, rho_R0, rho_L_fiber, rho_R_fiber)
            combined = branch_score(rho_L0, rho_L0, rho_L_fiber, rho_L_fiber)
            live_direct = direct_runtime(rho_L0, rho_R0, rho_L_base, rho_R_base)
            no_chirality_direct = direct_runtime(rho_L0, rho_R0, rho_L_base, rho_L_base)
            swapped_direct = direct_runtime(rho_L0, rho_R0, rho_L_fiber, rho_R_fiber)
            combined_direct = direct_runtime(rho_L0, rho_R0, rho_L_fiber, rho_L_fiber)

            live_transport_gap = live["traversal"] - swapped["traversal"]
            flat_transport_gap = no_chirality["traversal"] - combined["traversal"]
            swapped_transport_gap = swapped["traversal"]
            combined_transport_gap = combined["traversal"]

            live_scores.append(live["score"])
            flat_scores.append(no_chirality["score"])
            swapped_scores.append(swapped["score"])
            combined_scores.append(combined["score"])

            cases.append(
                {
                    "eta": float(eta),
                    "trial": int(trial),
                    "live": {**live, **live_direct},
                    "no_chirality": {**no_chirality, **no_chirality_direct},
                    "swapped_loop": {**swapped, **swapped_direct},
                    "combined": {**combined, **combined_direct},
                    "transport_gap": {
                        "live": float(live_transport_gap),
                        "no_chirality": float(flat_transport_gap),
                        "swapped_loop": float(swapped_transport_gap),
                        "combined": float(combined_transport_gap),
                    },
                }
            )

    summary = {
        "live_min_score": float(min(live_scores)),
        "live_mean_score": float(np.mean(live_scores)),
        "flat_max_score": float(max(flat_scores)),
        "flat_mean_score": float(np.mean(flat_scores)),
        "swapped_max_score": float(max(swapped_scores)),
        "swapped_mean_score": float(np.mean(swapped_scores)),
        "combined_max_score": float(max(combined_scores)),
        "combined_mean_score": float(np.mean(combined_scores)),
        "flat_beats_live_count": int(sum(1 for live, flat in zip(live_scores, flat_scores) if flat >= live)),
        "swapped_beats_live_count": int(sum(1 for live, swapped in zip(live_scores, swapped_scores) if swapped >= live)),
        "combined_beats_live_count": int(sum(1 for live, combined in zip(live_scores, combined_scores) if combined >= live)),
        "live_min_transport_gap": float(min(case["transport_gap"]["live"] for case in cases)),
        "flat_max_transport_gap": float(max(case["transport_gap"]["no_chirality"] for case in cases)),
        "swapped_max_transport_gap": float(max(case["transport_gap"]["swapped_loop"] for case in cases)),
        "combined_max_transport_gap": float(max(case["transport_gap"]["combined"] for case in cases)),
        "combined_gap_retention": float(
            max(case["transport_gap"]["combined"] for case in cases)
            / max(min(case["transport_gap"]["live"] for case in cases), 1e-12)
        ),
        "live_min_sheet_split": float(min(case["live"]["sheet_split"] for case in cases)),
        "flat_max_sheet_split": float(max(case["no_chirality"]["sheet_split"] for case in cases)),
        "swapped_max_sheet_split": float(max(case["swapped_loop"]["sheet_split"] for case in cases)),
        "combined_max_sheet_split": float(max(case["combined"]["sheet_split"] for case in cases)),
        "live_min_direct_min_traversal": float(min(case["live"]["min_traversal"] for case in cases)),
        "flat_min_direct_min_traversal": float(min(case["no_chirality"]["min_traversal"] for case in cases)),
        "swapped_max_direct_min_traversal": float(max(case["swapped_loop"]["min_traversal"] for case in cases)),
        "combined_max_direct_min_traversal": float(max(case["combined"]["min_traversal"] for case in cases)),
    }

    nonproxy_runtime_support = (
        summary["live_min_direct_min_traversal"] > 0.1
        and summary["live_min_sheet_split"] > 0.1
        and summary["flat_max_sheet_split"] < 1e-12
        and summary["swapped_max_direct_min_traversal"] < 1e-12
        and summary["combined_max_sheet_split"] < 1e-12
        and summary["combined_max_direct_min_traversal"] < 1e-12
    )

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "cases": cases,
        "summary": summary,
        "owner_read": {
            "status": "nonproxy_runtime_support" if nonproxy_runtime_support else "proxy_only",
            "candidate_branch": "chirality-separated loop-sensitive transport deltas",
            "interpretation": "live branch keeps direct sheet-split and direct per-sheet traversal on the same carrier while no-chirality and swapped-loop ablations collapse those observables",
        },
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
