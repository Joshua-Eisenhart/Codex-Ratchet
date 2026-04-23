#!/usr/bin/env python3
"""
Carnot Reverse Asymmetric Sweep
===============================
Independent hot/cold isotherm duration sweep for the reverse refrigerator lane
of the stochastic harmonic Carnot sidecar.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
classification = "classical_baseline"  # auto-backfill


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from sim_stoch_harmonic_carnot_finite_time import (  # noqa: E402
    CLASSIFICATION_NOTE as PARENT_SCOPE_NOTE,
    K_HIGH,
    K_HOT_LOW,
    N_TRAJ,
    RNG_SEED,
    T_COLD,
    T_HOT,
    adiabatic_jump,
    mean_internal_energy,
    run_isothermal_leg,
    sample_equilibrium,
)


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Asymmetric hot/cold isotherm sweep for the reverse stochastic Carnot lane. "
    "It maps refrigerator COP and return mismatch as hot and cold thermalization "
    "budgets vary independently."
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

HOT_STEP_GRID = [520, 1000, 2500, 5000]
COLD_STEP_GRID = [520, 1000, 2500, 5000]


def run_reverse_cycle_asymmetric(cold_steps: int, hot_steps: int, seed_offset: int) -> dict:
    rng = np.random.default_rng(RNG_SEED + seed_offset)
    k_cold_low = K_HOT_LOW * (T_COLD / T_HOT)
    k_cold_high = K_HIGH * (T_COLD / T_HOT)

    x_a = sample_equilibrium(N_TRAJ, T_HOT, K_HIGH, rng)
    initial_variance = float(np.var(x_a))
    initial_internal_energy = mean_internal_energy(x_a, K_HIGH)

    adiabatic_to_cold = adiabatic_jump(x_a, K_HIGH, k_cold_high)
    cold_iso_reverse = run_isothermal_leg(
        adiabatic_to_cold["x"],
        T_COLD,
        k_cold_high,
        k_cold_low,
        cold_steps,
        rng,
        "cold_isotherm_expansion_reverse",
    )
    adiabatic_to_hot = adiabatic_jump(cold_iso_reverse["x"], k_cold_low, K_HOT_LOW)
    hot_iso_reverse = run_isothermal_leg(
        adiabatic_to_hot["x"],
        T_HOT,
        K_HOT_LOW,
        K_HIGH,
        hot_steps,
        rng,
        "hot_isotherm_compression_reverse",
    )

    q_cold_absorbed = cold_iso_reverse["mean_heat"]
    q_hot_released = hot_iso_reverse["mean_heat"]
    work_on_system = (
        adiabatic_to_cold["mean_work"]
        + cold_iso_reverse["mean_work"]
        + adiabatic_to_hot["mean_work"]
        + hot_iso_reverse["mean_work"]
    )
    work_input = work_on_system
    cop = q_cold_absorbed / work_input if work_input > 0.0 else float("nan")
    cop_carnot = T_COLD / (T_HOT - T_COLD)
    final_variance = float(np.var(hot_iso_reverse["x"]))
    final_internal_energy = mean_internal_energy(hot_iso_reverse["x"], K_HIGH)
    cycle_delta_u = (
        adiabatic_to_cold["mean_delta_u"]
        + cold_iso_reverse["mean_delta_u"]
        + adiabatic_to_hot["mean_delta_u"]
        + hot_iso_reverse["mean_delta_u"]
    )

    return {
        "cold_steps": int(cold_steps),
        "hot_steps": int(hot_steps),
        "q_cold_absorbed": float(q_cold_absorbed),
        "q_hot_released": float(q_hot_released),
        "work_input": float(work_input),
        "cop": float(cop),
        "cop_carnot": float(cop_carnot),
        "cop_distance_to_carnot": float(abs(cop - cop_carnot)),
        "initial_variance": initial_variance,
        "final_variance": final_variance,
        "variance_mismatch_abs": float(abs(final_variance - (T_HOT / K_HIGH))),
        "initial_internal_energy": initial_internal_energy,
        "final_internal_energy": final_internal_energy,
        "internal_energy_mismatch_abs": float(abs(final_internal_energy - 0.5 * T_HOT)),
        "cycle_delta_u": float(cycle_delta_u),
    }


def main() -> None:
    rows = []
    seed_offset = 6000
    for cold_steps in COLD_STEP_GRID:
        for hot_steps in HOT_STEP_GRID:
            rows.append(run_reverse_cycle_asymmetric(cold_steps, hot_steps, seed_offset))
            seed_offset += 1

    best_closure = min(rows, key=lambda row: row["variance_mismatch_abs"])
    best_cop = min(rows, key=lambda row: row["cop_distance_to_carnot"])

    hot_heavy_rows = [row for row in rows if row["hot_steps"] > row["cold_steps"]]
    cold_heavy_rows = [row for row in rows if row["cold_steps"] > row["hot_steps"]]
    balanced_rows = [row for row in rows if row["hot_steps"] == row["cold_steps"]]

    positive = {
        "some_asymmetric_setting_improves_reverse_closure_over_balanced_baseline": {
            "best_closure_setting": {"cold_steps": best_closure["cold_steps"], "hot_steps": best_closure["hot_steps"]},
            "best_closure_variance_mismatch_abs": best_closure["variance_mismatch_abs"],
            "best_balanced_variance_mismatch_abs": min(row["variance_mismatch_abs"] for row in balanced_rows),
            "pass": best_closure["variance_mismatch_abs"] < min(row["variance_mismatch_abs"] for row in balanced_rows),
        },
        "some_high_budget_setting_moves_close_to_carnot_cop": {
            "best_cop_setting": {"cold_steps": best_cop["cold_steps"], "hot_steps": best_cop["hot_steps"]},
            "best_cop_distance_to_carnot": best_cop["cop_distance_to_carnot"],
            "pass": best_cop["cop_distance_to_carnot"] < 0.05,
        },
        "cold_heavy_budget_beats_hot_heavy_budget_on_average_for_reverse_closure": {
            "cold_heavy_mean_variance_mismatch": float(np.mean([row["variance_mismatch_abs"] for row in cold_heavy_rows])),
            "hot_heavy_mean_variance_mismatch": float(np.mean([row["variance_mismatch_abs"] for row in hot_heavy_rows])),
            "pass": float(np.mean([row["variance_mismatch_abs"] for row in cold_heavy_rows]))
            < float(np.mean([row["variance_mismatch_abs"] for row in hot_heavy_rows])),
        },
    }

    negative = {
        "even_the_best_reverse_row_still_has_nonzero_cycle_return_error": {
            "cycle_delta_u": best_closure["cycle_delta_u"],
            "pass": abs(best_closure["cycle_delta_u"]) > 1e-3,
        },
        "hot_leg_budget_alone_is_not_sufficient_to_optimize_reverse_closure": {
            "best_hot_heavy_variance_mismatch_abs": min(row["variance_mismatch_abs"] for row in hot_heavy_rows),
            "best_cold_heavy_variance_mismatch_abs": min(row["variance_mismatch_abs"] for row in cold_heavy_rows),
            "pass": min(row["variance_mismatch_abs"] for row in hot_heavy_rows)
            > min(row["variance_mismatch_abs"] for row in cold_heavy_rows),
        },
    }

    boundary = {
        "all_rows_are_finite": {
            "pass": all(
                np.isfinite(value)
                for row in rows
                for value in row.values()
                if isinstance(value, (int, float))
            ),
        },
        "all_rows_operate_on_the_same_temperature_pair": {
            "t_hot": T_HOT,
            "t_cold": T_COLD,
            "pass": T_HOT > T_COLD > 0.0,
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    out = {
        "name": "carnot_reverse_asymmetric_sweep",
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
            "cold_step_grid": COLD_STEP_GRID,
            "hot_step_grid": HOT_STEP_GRID,
            "best_closure_setting": {"cold_steps": best_closure["cold_steps"], "hot_steps": best_closure["hot_steps"]},
            "best_closure_variance_mismatch_abs": best_closure["variance_mismatch_abs"],
            "best_cop_setting": {"cold_steps": best_cop["cold_steps"], "hot_steps": best_cop["hot_steps"]},
            "best_cop_distance_to_carnot": best_cop["cop_distance_to_carnot"],
            "scope_note": (
                "Asymmetric hot/cold isotherm sweep for the reverse stochastic Carnot lane. "
                "It maps how refrigerator quality and return mismatch depend on thermalization budget."
            ),
        },
        "rows": rows,
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "carnot_reverse_asymmetric_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
