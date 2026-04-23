#!/usr/bin/env python3
"""
Carnot Asymmetric Isotherm Sweep
================================
Sweep hot- and cold-isotherm durations independently for the stochastic
harmonic Carnot lane.

This tests whether the forward closure defect is mainly a hot-leg budget issue,
a cold-leg budget issue, or a more balanced finite-time residue.
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
    DT,
    GAMMA,
    K_HIGH,
    K_HOT_LOW,
    N_TRAJ,
    RNG_SEED,
    T_COLD,
    T_HOT,
    adiabatic_jump,
    harmonic_force,
    harmonic_potential,
    mean_internal_energy,
    run_isothermal_leg,
    sample_equilibrium,
)


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Asymmetric hot/cold isotherm sweep for the stochastic harmonic Carnot lane. "
    "It asks whether forward closure and Carnot proximity improve more by "
    "lengthening the hot leg, the cold leg, or both."
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


def run_forward_cycle_asymmetric(hot_steps: int, cold_steps: int, seed_offset: int) -> dict:
    rng = np.random.default_rng(RNG_SEED + seed_offset)
    k_cold_low = K_HOT_LOW * (T_COLD / T_HOT)
    k_cold_high = K_HIGH * (T_COLD / T_HOT)

    x_a = sample_equilibrium(N_TRAJ, T_HOT, K_HIGH, rng)
    initial_variance = float(np.var(x_a))
    initial_internal_energy = mean_internal_energy(x_a, K_HIGH)

    hot_iso = run_isothermal_leg(x_a, T_HOT, K_HIGH, K_HOT_LOW, hot_steps, rng, "hot_isotherm_expansion")
    adiabatic_expand = adiabatic_jump(hot_iso["x"], K_HOT_LOW, k_cold_low)
    cold_iso = run_isothermal_leg(
        adiabatic_expand["x"],
        T_COLD,
        k_cold_low,
        k_cold_high,
        cold_steps,
        rng,
        "cold_isotherm_compression",
    )
    adiabatic_compress = adiabatic_jump(cold_iso["x"], k_cold_high, K_HIGH)

    q_hot = hot_iso["mean_heat"]
    q_cold = cold_iso["mean_heat"]
    work_on_system = hot_iso["mean_work"] + adiabatic_expand["mean_work"] + cold_iso["mean_work"] + adiabatic_compress["mean_work"]
    work_by_system = -work_on_system
    carnot_bound = 1.0 - T_COLD / T_HOT
    efficiency = work_by_system / q_hot if q_hot > 0.0 else float("nan")
    final_variance = float(np.var(adiabatic_compress["x"]))
    final_internal_energy = mean_internal_energy(adiabatic_compress["x"], K_HIGH)
    cycle_delta_u = (
        hot_iso["mean_delta_u"]
        + adiabatic_expand["mean_delta_u"]
        + cold_iso["mean_delta_u"]
        + adiabatic_compress["mean_delta_u"]
    )

    return {
        "hot_steps": int(hot_steps),
        "cold_steps": int(cold_steps),
        "q_hot": float(q_hot),
        "q_cold": float(q_cold),
        "work_by_system": float(work_by_system),
        "efficiency": float(efficiency),
        "carnot_bound": float(carnot_bound),
        "efficiency_distance_to_carnot": float(abs(efficiency - carnot_bound)),
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
    seed_offset = 3000
    for hot_steps in HOT_STEP_GRID:
        for cold_steps in COLD_STEP_GRID:
            rows.append(run_forward_cycle_asymmetric(hot_steps, cold_steps, seed_offset))
            seed_offset += 1

    best_closure = min(rows, key=lambda row: row["variance_mismatch_abs"])
    best_efficiency = min(rows, key=lambda row: row["efficiency_distance_to_carnot"])

    hot_dominant_rows = [row for row in rows if row["hot_steps"] > row["cold_steps"]]
    cold_dominant_rows = [row for row in rows if row["cold_steps"] > row["hot_steps"]]
    balanced_rows = [row for row in rows if row["hot_steps"] == row["cold_steps"]]

    positive = {
        "some_asymmetric_setting_improves_closure_over_the_balanced_baseline": {
            "best_closure_setting": {"hot_steps": best_closure["hot_steps"], "cold_steps": best_closure["cold_steps"]},
            "best_closure_variance_mismatch_abs": best_closure["variance_mismatch_abs"],
            "best_balanced_variance_mismatch_abs": min(row["variance_mismatch_abs"] for row in balanced_rows),
            "pass": best_closure["variance_mismatch_abs"] < min(row["variance_mismatch_abs"] for row in balanced_rows),
        },
        "some_high_budget_setting_moves_close_to_carnot": {
            "best_efficiency_setting": {"hot_steps": best_efficiency["hot_steps"], "cold_steps": best_efficiency["cold_steps"]},
            "best_efficiency_distance_to_carnot": best_efficiency["efficiency_distance_to_carnot"],
            "pass": best_efficiency["efficiency_distance_to_carnot"] < 0.05,
        },
        "hot_heavy_budget_beats_cold_heavy_budget_on_average_for_closure": {
            "hot_heavy_mean_variance_mismatch": float(np.mean([row["variance_mismatch_abs"] for row in hot_dominant_rows])),
            "cold_heavy_mean_variance_mismatch": float(np.mean([row["variance_mismatch_abs"] for row in cold_dominant_rows])),
            "pass": float(np.mean([row["variance_mismatch_abs"] for row in hot_dominant_rows]))
            < float(np.mean([row["variance_mismatch_abs"] for row in cold_dominant_rows])),
        },
    }

    negative = {
        "even_the_best_asymmetric_row_still_has_nonzero_cycle_return_error": {
            "cycle_delta_u": best_closure["cycle_delta_u"],
            "pass": abs(best_closure["cycle_delta_u"]) > 1e-3,
        },
        "cold_leg_budget_alone_is_not_sufficient_to_close_the_cycle": {
            "best_cold_heavy_variance_mismatch_abs": min(row["variance_mismatch_abs"] for row in cold_dominant_rows),
            "best_hot_heavy_variance_mismatch_abs": min(row["variance_mismatch_abs"] for row in hot_dominant_rows),
            "pass": min(row["variance_mismatch_abs"] for row in cold_dominant_rows)
            > min(row["variance_mismatch_abs"] for row in hot_dominant_rows),
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
        "name": "carnot_asymmetric_isotherm_sweep",
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
            "hot_step_grid": HOT_STEP_GRID,
            "cold_step_grid": COLD_STEP_GRID,
            "best_closure_setting": {"hot_steps": best_closure["hot_steps"], "cold_steps": best_closure["cold_steps"]},
            "best_closure_variance_mismatch_abs": best_closure["variance_mismatch_abs"],
            "best_efficiency_setting": {"hot_steps": best_efficiency["hot_steps"], "cold_steps": best_efficiency["cold_steps"]},
            "best_efficiency_distance_to_carnot": best_efficiency["efficiency_distance_to_carnot"],
            "scope_note": (
                "Asymmetric hot/cold isotherm sweep for the stochastic Carnot lane. "
                "It maps whether closure improves more by lengthening one thermal leg than the other."
            ),
        },
        "rows": rows,
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "carnot_asymmetric_isotherm_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
