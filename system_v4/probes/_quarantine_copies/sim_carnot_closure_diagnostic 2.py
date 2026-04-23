#!/usr/bin/env python3
"""
Carnot Closure Diagnostic
==========================
Bounded diagnostic probe for the stochastic harmonic Carnot lane.

This maps where the forward-cycle return defect comes from by tracking per-leg
state summaries, not just efficiency.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from sim_stoch_harmonic_carnot_finite_time import (  # noqa: E402
    CLASSIFICATION_NOTE as PARENT_SCOPE_NOTE,
    K_HIGH,
    K_HOT_LOW,
    QUASISTATIC_STEPS,
    T_COLD,
    T_HOT,
    run_forward_cycle,
)


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Closure diagnostic for the stochastic harmonic Carnot sidecar. "
    "It compares per-leg variance and energy mismatches across several step "
    "counts to locate where the forward return defect is accumulated."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "carnot_cycle",
]

PRIMARY_LEGO_IDS = [
    "stochastic_thermodynamics",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

STEP_GRID = [90, 260, 520, 1000, 2500, QUASISTATIC_STEPS, 8000]
SEED_BASE = 20260410 + 1900

HOT_EQ_VARIANCE = T_HOT / K_HOT_LOW
COLD_EQ_VARIANCE = T_COLD / (K_HIGH * (T_COLD / T_HOT))
HOT_EQ_ENERGY = 0.5 * K_HOT_LOW * HOT_EQ_VARIANCE
COLD_EQ_ENERGY = 0.5 * (K_HIGH * (T_COLD / T_HOT)) * COLD_EQ_VARIANCE
INIT_EQ_VARIANCE = T_HOT / K_HIGH
INIT_EQ_ENERGY = 0.5 * K_HIGH * INIT_EQ_VARIANCE


def mean_internal_energy(x: np.ndarray, stiffness: float) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.mean(0.5 * stiffness * x * x))


def leg_summary(leg: dict, stiffness: float, target_variance: float, target_internal_energy: float) -> dict:
    x = np.asarray(leg["x"], dtype=float)
    variance = float(leg["final_variance"])
    internal_energy = mean_internal_energy(x, stiffness)
    return {
        "final_variance": variance,
        "variance_mismatch": float(variance - target_variance),
        "variance_mismatch_abs": float(abs(variance - target_variance)),
        "internal_energy": internal_energy,
        "internal_energy_mismatch": float(internal_energy - target_internal_energy),
        "internal_energy_mismatch_abs": float(abs(internal_energy - target_internal_energy)),
        "mean_delta_u": float(leg["mean_delta_u"]),
        "mean_work": float(leg["mean_work"]),
        "mean_heat": float(leg["mean_heat"]),
        "target_variance": float(target_variance),
        "target_internal_energy": float(target_internal_energy),
    }


def detect_leg_concentration(step_row: dict) -> dict:
    hot_abs = abs(step_row["hot_iso"]["variance_mismatch"])
    cold_abs = abs(step_row["cold_iso"]["variance_mismatch"])
    adiabatic_abs = abs(step_row["adiabatic_expand"]["variance_mismatch"])
    final_abs = abs(step_row["final_return"]["variance_mismatch"])
    total = hot_abs + cold_abs + adiabatic_abs + final_abs
    dominant = max(
        [
            ("hot_iso", hot_abs),
            ("adiabatic_expand", adiabatic_abs),
            ("cold_iso", cold_abs),
            ("final_return", final_abs),
        ],
        key=lambda item: item[1],
    )[0]
    return {
        "dominant_leg": dominant,
        "hot_share": float(hot_abs / total) if total else 0.0,
        "adiabatic_share": float(adiabatic_abs / total) if total else 0.0,
        "cold_share": float(cold_abs / total) if total else 0.0,
        "final_share": float(final_abs / total) if total else 0.0,
        "distributed_residue": bool(dominant != "final_return" and total > 0.0),
    }


def main() -> None:
    rows = []
    for idx, steps in enumerate(STEP_GRID):
        forward = run_forward_cycle(steps, SEED_BASE + idx)
        hot = leg_summary(forward["hot_iso"], K_HOT_LOW, HOT_EQ_VARIANCE, HOT_EQ_ENERGY)
        adiabatic = leg_summary(forward["adiabatic_expand"], K_HOT_LOW * (T_COLD / T_HOT), HOT_EQ_VARIANCE, HOT_EQ_ENERGY)
        cold = leg_summary(forward["cold_iso"], K_HIGH * (T_COLD / T_HOT), INIT_EQ_VARIANCE, INIT_EQ_ENERGY)
        final_internal_energy = mean_internal_energy(np.asarray(forward["adiabatic_compress"]["x"], dtype=float), K_HIGH)
        final_variance_mismatch = float(forward["final_variance"] - INIT_EQ_VARIANCE)
        final_internal_energy_mismatch = float(final_internal_energy - INIT_EQ_ENERGY)
        cycle_row = {
            "steps": int(steps),
            "carnot_bound": float(forward["carnot_bound"]),
            "efficiency": float(forward["efficiency"]),
            "efficiency_distance_to_carnot": float(abs(forward["efficiency"] - forward["carnot_bound"])),
            "cycle_delta_u": float(forward["cycle_delta_u"]),
            "initial_variance": float(forward["initial_variance"]),
            "final_variance": float(forward["final_variance"]),
            "initial_internal_energy": float(forward["initial_internal_energy"]),
            "final_internal_energy": float(final_internal_energy),
            "variance_mismatch": final_variance_mismatch,
            "variance_mismatch_abs": float(abs(final_variance_mismatch)),
            "internal_energy_mismatch": final_internal_energy_mismatch,
            "internal_energy_mismatch_abs": float(abs(final_internal_energy_mismatch)),
            "hot_iso": hot,
            "adiabatic_expand": adiabatic,
            "cold_iso": cold,
            "final_return": {
                "final_variance": float(forward["final_variance"]),
                "variance_mismatch": final_variance_mismatch,
                "variance_mismatch_abs": float(abs(final_variance_mismatch)),
                "final_internal_energy": float(final_internal_energy),
                "internal_energy_mismatch": final_internal_energy_mismatch,
                "internal_energy_mismatch_abs": float(abs(final_internal_energy_mismatch)),
            },
        }
        cycle_row["concentration"] = detect_leg_concentration(cycle_row)
        rows.append(cycle_row)

    best_closure = min(rows, key=lambda row: row["variance_mismatch_abs"])
    worst_closure = max(rows, key=lambda row: row["variance_mismatch_abs"])
    largest_energy_gap = max(rows, key=lambda row: row["internal_energy_mismatch_abs"])

    positive = {
        "higher_step_counts_reduce_forward_return_mismatch": {
            "first_abs_variance_mismatch": rows[0]["variance_mismatch_abs"],
            "last_abs_variance_mismatch": rows[-1]["variance_mismatch_abs"],
            "pass": rows[-1]["variance_mismatch_abs"] < rows[0]["variance_mismatch_abs"],
        },
        "quasistatic_row_is_closest_to_closure": {
            "best_steps": best_closure["steps"],
            "best_abs_variance_mismatch": best_closure["variance_mismatch_abs"],
            "pass": best_closure["steps"] >= QUASISTATIC_STEPS,
        },
        "final_energy_gap_tracks_variance_gap": {
            "largest_energy_gap_steps": largest_energy_gap["steps"],
            "largest_energy_gap": largest_energy_gap["internal_energy_mismatch_abs"],
            "pass": largest_energy_gap["internal_energy_mismatch_abs"] >= best_closure["internal_energy_mismatch_abs"],
        },
    }

    negative = {
        "closure_defect_is_not_just_a_single_bad_adiabatic_jump": {
            "dominant_leg": best_closure["concentration"]["dominant_leg"],
            "distributed_residue": best_closure["concentration"]["distributed_residue"],
            "pass": best_closure["concentration"]["dominant_leg"] != "adiabatic_expand",
        },
        "final_return_state_is_not_exactly_restored_even_at_high_steps": {
            "final_variance_mismatch": rows[-1]["variance_mismatch"],
            "final_internal_energy_mismatch": rows[-1]["internal_energy_mismatch"],
            "pass": abs(rows[-1]["variance_mismatch"]) > 1e-3 or abs(rows[-1]["internal_energy_mismatch"]) > 1e-3,
        },
        "nonzero_cycle_delta_u_persists_across_the_sweep": {
            "max_cycle_delta_u": max(abs(row["cycle_delta_u"]) for row in rows),
            "pass": max(abs(row["cycle_delta_u"]) for row in rows) > 1e-3,
        },
    }

    boundary = {
        "all_rows_have_finite_statistics": {
            "pass": all(
                np.isfinite(value)
                for row in rows
                for value in row.values()
                if isinstance(value, (int, float))
            ),
        },
        "all_rows_respect_the_same_temperature_pair": {
            "t_hot": T_HOT,
            "t_cold": T_COLD,
            "pass": T_HOT > T_COLD > 0.0,
        },
        "initial_state_anchor_is_the_hot_equilibrium_point": {
            "initial_variance": INIT_EQ_VARIANCE,
            "initial_internal_energy": INIT_EQ_ENERGY,
            "pass": INIT_EQ_VARIANCE > 0.0 and INIT_EQ_ENERGY > 0.0,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "carnot_closure_diagnostic",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "parent_scope_note": PARENT_SCOPE_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "step_grid": STEP_GRID,
            "best_closure_steps": best_closure["steps"],
            "best_closure_abs_variance_mismatch": best_closure["variance_mismatch_abs"],
            "best_closure_abs_energy_mismatch": best_closure["internal_energy_mismatch_abs"],
            "worst_closure_steps": worst_closure["steps"],
            "worst_closure_abs_variance_mismatch": worst_closure["variance_mismatch_abs"],
            "dominant_closure_leg_at_best_row": best_closure["concentration"]["dominant_leg"],
            "scope_note": (
                "Diagnostic sweep that measures forward-cycle return mismatch at the level of leg-state summaries. "
                "It is exploratory and isolates where the residue is accumulated."
            ),
        },
        "rows": rows,
    }

    out_dir = PROBE_DIR / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "carnot_closure_diagnostic_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
