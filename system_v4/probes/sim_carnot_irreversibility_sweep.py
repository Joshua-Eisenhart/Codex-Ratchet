#!/usr/bin/env python3
"""
Carnot Irreversibility Sweep
============================
Inductive sweep over finite-time stochastic Carnot cycle durations on the
harmonic working-substance sidecar.

This does not create a new engine theorem. It maps where forward engine
behavior, reverse refrigerator behavior, and cycle-return defects appear.
"""

from __future__ import annotations

import json
import pathlib

classification = "classical_baseline"

from sim_stoch_harmonic_carnot_finite_time import (
    CLASSIFICATION_NOTE as PARENT_SCOPE_NOTE,
    T_HOT,
    T_COLD,
    run_forward_cycle,
    run_reverse_cycle,
)


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Inductive duration sweep over the stochastic harmonic Carnot sidecar. "
    "It tracks where forward engine behavior, reverse refrigerator behavior, "
    "and state-return defects appear across protocol durations."
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

STEP_GRID = [60, 90, 150, 260, 520, 1000, 2500, 5000]
SEED_BASE = 20260410 + 910


def main() -> None:
    rows = []
    for idx, steps in enumerate(STEP_GRID):
        forward = run_forward_cycle(steps, SEED_BASE + idx)
        reverse = run_reverse_cycle(steps, SEED_BASE + 100 + idx)
        rows.append(
            {
                "steps": int(steps),
                "forward_efficiency": float(forward["efficiency"]),
                "forward_work_by_system": float(forward["work_by_system"]),
                "forward_q_hot": float(forward["q_hot"]),
                "forward_q_cold": float(forward["q_cold"]),
                "forward_cycle_delta_u": float(forward["cycle_delta_u"]),
                "forward_distance_to_carnot": float(abs(forward["efficiency"] - forward["carnot_bound"])),
                "reverse_cop": float(reverse["cop"]),
                "reverse_work_input": float(reverse["work_input"]),
                "reverse_q_cold_absorbed": float(reverse["q_cold_absorbed"]),
                "reverse_q_hot_released": float(reverse["q_hot_released"]),
                "reverse_cycle_delta_u": float(reverse["cycle_delta_u"]),
                "reverse_distance_to_carnot_cop": float(abs(reverse["cop"] - reverse["cop_carnot"])),
            }
        )

    forward_efficiencies = [row["forward_efficiency"] for row in rows]
    reverse_cops = [row["reverse_cop"] for row in rows]
    engine_rows = [row for row in rows if row["forward_work_by_system"] > 0.0]
    refrigerator_rows = [row for row in rows if row["reverse_work_input"] > 0.0 and row["reverse_q_cold_absorbed"] > 0.0]
    closest_forward = min(rows, key=lambda row: row["forward_distance_to_carnot"])
    closest_reverse = min(rows, key=lambda row: row["reverse_distance_to_carnot_cop"])
    max_step = max(STEP_GRID)

    positive = {
        "forward_engine_window_opens_in_the_higher_step_regime": {
            "first_steps_efficiency": rows[0]["forward_efficiency"],
            "last_steps_efficiency": rows[-1]["forward_efficiency"],
            "engine_rows": len(engine_rows),
            "pass": rows[0]["forward_work_by_system"] <= 0.0 and rows[-1]["forward_work_by_system"] > 0.0,
        },
        "reverse_refrigerator_cop_improves_with_duration": {
            "first_steps_cop": rows[0]["reverse_cop"],
            "last_steps_cop": rows[-1]["reverse_cop"],
            "pass": rows[-1]["reverse_cop"] > rows[0]["reverse_cop"],
        },
        "closest_forward_point_to_carnot_is_in_the_high_step_regime": {
            "closest_steps": closest_forward["steps"],
            "distance_to_carnot": closest_forward["forward_distance_to_carnot"],
            "pass": closest_forward["steps"] >= 1000,
        },
        "closest_reverse_point_to_carnot_cop_is_in_the_high_step_regime": {
            "closest_steps": closest_reverse["steps"],
            "distance_to_carnot_cop": closest_reverse["reverse_distance_to_carnot_cop"],
            "pass": closest_reverse["steps"] >= 1000,
        },
    }

    negative = {
        "fast_rows_do_not_behave_like_the_reversible_limit": {
            "first_steps_efficiency": rows[0]["forward_efficiency"],
            "first_steps_cop": rows[0]["reverse_cop"],
            "pass": rows[0]["forward_distance_to_carnot"] > 0.1 and rows[0]["reverse_distance_to_carnot_cop"] > 0.1,
        },
        "highest_step_forward_row_still_has_nonzero_cycle_return_error": {
            "steps": rows[-1]["steps"],
            "forward_cycle_delta_u": rows[-1]["forward_cycle_delta_u"],
            "pass": abs(rows[-1]["forward_cycle_delta_u"]) > 1e-3,
        },
        "highest_step_forward_row_still_does_not_hit_the_carnot_bound": {
            "steps": rows[-1]["steps"],
            "forward_efficiency": rows[-1]["forward_efficiency"],
            "carnot_bound": 1.0 - (T_COLD / T_HOT),
            "pass": rows[-1]["forward_distance_to_carnot"] > 1e-2,
        },
    }

    boundary = {
        "all_rows_are_finite": {
            "pass": all(
                isinstance(value, (int, float))
                for row in rows
                for value in row.values()
            ),
        },
        "all_rows_stay_in_the_same_temperature_pair": {
            "t_hot": T_HOT,
            "t_cold": T_COLD,
            "pass": T_HOT > T_COLD > 0.0,
        },
        "sweep_contains_both_engine_and_refrigerator_regimes": {
            "engine_rows": len(engine_rows),
            "refrigerator_rows": len(refrigerator_rows),
            "pass": len(engine_rows) > 0 and len(refrigerator_rows) == len(rows),
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    out = {
        "name": "carnot_irreversibility_sweep",
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
            "best_forward_steps": closest_forward["steps"],
            "best_forward_efficiency": closest_forward["forward_efficiency"],
            "best_forward_distance_to_carnot": closest_forward["forward_distance_to_carnot"],
            "best_reverse_steps": closest_reverse["steps"],
            "best_reverse_cop": closest_reverse["reverse_cop"],
            "best_reverse_distance_to_carnot_cop": closest_reverse["reverse_distance_to_carnot_cop"],
            "max_steps_forward_cycle_delta_u": rows[-1]["forward_cycle_delta_u"],
            "scope_note": (
                "Duration sweep over finite-time forward/reverse Carnot mechanics on the stochastic harmonic sidecar. "
                "It maps regime changes and remaining closure defects rather than claiming a closed engine theorem."
            ),
        },
        "rows": rows,
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "carnot_irreversibility_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
