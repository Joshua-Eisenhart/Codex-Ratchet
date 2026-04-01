#!/usr/bin/env python3
"""
Phase 6: Point-Reference Earned Bridge Test
===========================================

Goal
----
Test whether the surviving point-reference family can produce nonzero mutual
information without Bell injection while preserving the physical pair-state
marginal on subsystem B.

Why this is the right next cut
------------------------------
Phase 4/5 established:
- the strongest constructive winner is Bell-injected
- exact marginal-preserving MI on the chiral constructive lane collapses
- point-reference remains the strongest live pointwise discriminator

This probe asks a narrower question:
can point-reference generate "earned" MI while keeping the actual pair-state
carrier intact?

Setup
-----
For each torus and for fiber/base loops:
- fix q_ref at u=0
- sweep q_cur around the loop
- build the existing point-reference cq state
- measure I(A:B)
- measure Frobenius deviation of subsystem-B from the current physical pair
  state rho_pair(q_cur)

If the best exact/near-exact preserving candidate has near-zero MI,
the point-reference bridge lane is killed as an earned bridge, while still
remaining useful as a discriminator.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from axis0_xi_strict_bakeoff_sim import (  # noqa: E402
    TORUS_CONFIGS,
    exact_base_q,
    exact_fiber_q,
    metrics_for_cut_state,
    pair_state_from_q,
    partial_trace,
    xi_point_ref_cq_from_qs,
)


EPS = 1e-12
N_SAMPLES = 32
TOLS = [1e-6, 1e-3, 1e-2]


def summarize_rows(rows):
    i_vals = np.asarray([row["I_AB"] for row in rows], dtype=float)
    dev_vals = np.asarray([row["dev_B"] for row in rows], dtype=float)
    return {
        "count": int(len(rows)),
        "mean_I_AB": float(np.mean(i_vals)),
        "max_I_AB": float(np.max(i_vals)),
        "min_I_AB": float(np.min(i_vals)),
        "mean_dev_B": float(np.mean(dev_vals)),
        "min_dev_B": float(np.min(dev_vals)),
        "max_dev_B": float(np.max(dev_vals)),
    }


def best_under_tol(rows, tol):
    eligible = [row for row in rows if row["dev_B"] <= tol]
    if not eligible:
        return {
            "tol": float(tol),
            "count": 0,
            "best_I_AB": 0.0,
            "best_dev_B": None,
            "best_u": None,
            "best_source": None,
        }
    best = max(eligible, key=lambda row: row["I_AB"])
    return {
        "tol": float(tol),
        "count": int(len(eligible)),
        "best_I_AB": float(best["I_AB"]),
        "best_dev_B": float(best["dev_B"]),
        "best_u": float(best["u"]),
        "best_source": str(best["source"]),
    }


def run_loop_suite(torus_label, eta, loop_label, q_fn):
    u_grid = np.linspace(0.0, 2.0 * np.pi, N_SAMPLES, endpoint=False)
    q_ref = q_fn(eta, 0.0)
    rows = []

    for u in u_grid:
        q_cur = q_fn(eta, float(u))
        rho_ref, dims, _ = xi_point_ref_cq_from_qs(q_ref, q_cur)
        metrics = metrics_for_cut_state(rho_ref, dims)
        rho_b = partial_trace(rho_ref, dims, [1])
        rho_target = pair_state_from_q(q_cur)
        dev_b = float(np.linalg.norm(rho_b - rho_target, ord="fro"))
        rows.append(
            {
                "torus": torus_label,
                "loop": loop_label,
                "u": float(u),
                "source": "point_reference_cq",
                "I_AB": float(metrics["I_AB"]),
                "I_c_A_to_B": float(metrics["I_c_A_to_B"]),
                "S_A_given_B": float(metrics["S_A_given_B"]),
                "dev_B": dev_b,
                "exact_preserving": bool(dev_b <= 1e-9),
            }
        )

    exact_rows = [row for row in rows if row["exact_preserving"]]
    best_overall = max(rows, key=lambda row: row["I_AB"])
    best_exact = max(exact_rows, key=lambda row: row["I_AB"]) if exact_rows else None

    return {
        "torus": torus_label,
        "eta": float(eta),
        "loop": loop_label,
        "summary": summarize_rows(rows),
        "best_overall": {
            "I_AB": float(best_overall["I_AB"]),
            "dev_B": float(best_overall["dev_B"]),
            "u": float(best_overall["u"]),
        },
        "best_exact": (
            {
                "I_AB": float(best_exact["I_AB"]),
                "dev_B": float(best_exact["dev_B"]),
                "u": float(best_exact["u"]),
            }
            if best_exact is not None
            else None
        ),
        "tol_sweep": [best_under_tol(rows, tol) for tol in TOLS],
        "rows": rows,
    }


def main():
    print("=" * 80)
    print("PHASE 6: POINT-REFERENCE EARNED BRIDGE TEST")
    print("=" * 80)

    suites = []
    for torus_label, eta in TORUS_CONFIGS:
        print(f"\n  Torus: {torus_label}")
        for loop_label, q_fn in (("fiber", exact_fiber_q), ("base", exact_base_q)):
            suite = run_loop_suite(torus_label, eta, loop_label, q_fn)
            suites.append(suite)
            best_overall = suite["best_overall"]
            best_exact = suite["best_exact"]
            print(
                f"    {loop_label:<5} "
                f"best_overall_I={best_overall['I_AB']:.6f} "
                f"dev_B={best_overall['dev_B']:.6f} "
                f"best_exact_I={(best_exact['I_AB'] if best_exact else 0.0):.6f}"
            )

    exact_best_vals = [
        suite["best_exact"]["I_AB"] for suite in suites if suite["best_exact"] is not None
    ]
    tol_1e3_best_vals = [
        next(item["best_I_AB"] for item in suite["tol_sweep"] if abs(item["tol"] - 1e-3) < EPS)
        for suite in suites
    ]
    base_exact_vals = [
        suite["best_exact"]["I_AB"]
        for suite in suites
        if suite["loop"] == "base" and suite["best_exact"] is not None
    ]
    fiber_exact_vals = [
        suite["best_exact"]["I_AB"]
        for suite in suites
        if suite["loop"] == "fiber" and suite["best_exact"] is not None
    ]

    mean_exact_best = float(np.mean(exact_best_vals)) if exact_best_vals else 0.0
    mean_tol_1e3_best = float(np.mean(tol_1e3_best_vals)) if tol_1e3_best_vals else 0.0

    verdict = {
        "mean_best_exact_I_AB": mean_exact_best,
        "mean_best_tol_1e3_I_AB": mean_tol_1e3_best,
        "base_exact_nontrivial_count": int(sum(val > 1e-3 for val in base_exact_vals)),
        "fiber_exact_nontrivial_count": int(sum(val > 1e-3 for val in fiber_exact_vals)),
        "point_reference_earned_bridge_survives": bool(mean_exact_best > 1e-3),
        "point_reference_discriminator_survives": True,
        "controller_read": (
            "point_reference_remains_discriminator_only"
            if mean_exact_best <= 1e-3
            else "point_reference_has_nontrivial_earned_bridge_signal"
        ),
    }

    print(f"\n{'=' * 80}")
    print("VERDICTS")
    print(f"{'=' * 80}")
    print(f"  Mean best exact-preserving I(A:B): {mean_exact_best:.6f}")
    print(f"  Mean best <=1e-3 preserving I(A:B): {mean_tol_1e3_best:.6f}")
    print(f"  Base exact nontrivial count:        {verdict['base_exact_nontrivial_count']}/3")
    print(f"  Fiber exact nontrivial count:       {verdict['fiber_exact_nontrivial_count']}/3")
    if verdict["point_reference_earned_bridge_survives"]:
        print("  ✓ Point-reference earned bridge signal survives strict preserving test")
    else:
        print("  ⚠ Point-reference earned bridge signal collapses under strict preserving test")
        print("    Point-reference remains useful as a discriminator, not as an earned bridge")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis0_phase6_point_reference_results.json")
    with open(out_path, "w") as f:
        json.dump(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "n_samples": N_SAMPLES,
                "tolerances": TOLS,
                "suites": suites,
                "verdict": verdict,
            },
            f,
            indent=2,
        )

    print(f"\nWrote {out_path}")
    print(f"\n{'=' * 80}")
    print("PROBE STATUS: PASS")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
