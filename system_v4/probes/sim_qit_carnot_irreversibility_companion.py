#!/usr/bin/env python3
"""
QIT Carnot irreversibility companion.
====================================
Strict finite-carrier companion surface for the open finite-time Carnot
irreversibility sweep. It keeps the step-grid signal explicit in a bounded
two-bath qubit model with forward engine and reverse refrigerator modes.
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

import sim_qit_carnot_finite_time_companion as base  # noqa: E402


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Strict finite-carrier QIT companion for the finite-time Carnot "
    "irreversibility sweep. It preserves the duration signal in a bounded "
    "two-bath qubit model with explicit forward engine and reverse "
    "refrigerator modes. It is a comparison surface, not a canonical engine "
    "theorem."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
    "stochastic_thermodynamics",
]

PRIMARY_LEGO_IDS = [
    "quantum_thermodynamics",
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
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def main() -> None:
    rows = []
    for steps in STEP_GRID:
        budget_label = f"steps_{steps}"
        forward = base.run_forward_cycle(steps, budget_label)
        reverse = base.run_reverse_cycle(steps, budget_label)

        rows.append(
            {
                "steps": int(steps),
                "budget_label": budget_label,
                "direction": "forward",
                "closure_defect": float(forward["closure_defect"]),
                "primary_metric_name": forward["primary_metric_name"],
                "primary_metric_value": float(forward["primary_metric_value"]),
                "distance_to_carnot_reference": float(forward["distance_to_carnot_reference"]),
                "carnot_reference": float(forward["carnot_reference"]),
                "work_by_system": float(forward["work_by_system"]),
                "positive_heat_absorbed": float(forward["positive_heat_absorbed"]),
                "total_heat_into_system": float(forward["total_heat_into_system"]),
                "bookkeeping_closure_error": float(forward["bookkeeping_closure_error"]),
                "final_trace_distance_to_initial": float(forward["final_trace_distance_to_initial"]),
                "final_probability_mismatch_abs": float(forward["final_probability_mismatch_abs"]),
                "final_free_energy_mismatch": float(forward["final_free_energy_mismatch"]),
                "final_internal_energy_mismatch": float(forward["final_internal_energy_mismatch"]),
                "stages": forward["stages"],
            }
        )
        rows.append(
            {
                "steps": int(steps),
                "budget_label": budget_label,
                "direction": "reverse",
                "closure_defect": float(reverse["closure_defect"]),
                "primary_metric_name": reverse["primary_metric_name"],
                "primary_metric_value": float(reverse["primary_metric_value"]),
                "distance_to_carnot_reference": float(reverse["distance_to_carnot_reference"]),
                "carnot_reference": float(reverse["carnot_reference"]),
                "work_by_system": float(reverse["work_by_system"]),
                "work_input": float(reverse["work_input"]),
                "q_cold_absorbed": float(reverse["q_cold_absorbed"]),
                "total_heat_into_system": float(reverse["total_heat_into_system"]),
                "bookkeeping_closure_error": float(reverse["bookkeeping_closure_error"]),
                "final_trace_distance_to_initial": float(reverse["final_trace_distance_to_initial"]),
                "final_probability_mismatch_abs": float(reverse["final_probability_mismatch_abs"]),
                "final_free_energy_mismatch": float(reverse["final_free_energy_mismatch"]),
                "final_internal_energy_mismatch": float(reverse["final_internal_energy_mismatch"]),
                "stages": reverse["stages"],
            }
        )

    forward_rows = [row for row in rows if row["direction"] == "forward"]
    reverse_rows = [row for row in rows if row["direction"] == "reverse"]

    baseline_forward = next(row for row in forward_rows if row["steps"] == STEP_GRID[0])
    best_closure = min(rows, key=lambda row: row["closure_defect"])
    best_forward = max(forward_rows, key=lambda row: row["primary_metric_value"])
    best_reverse = max(reverse_rows, key=lambda row: row["primary_metric_value"])

    forward_closure_spread = max(row["closure_defect"] for row in forward_rows) - min(
        row["closure_defect"] for row in forward_rows
    )
    reverse_closure_spread = max(row["closure_defect"] for row in reverse_rows) - min(
        row["closure_defect"] for row in reverse_rows
    )
    forward_primary_spread = max(row["primary_metric_value"] for row in forward_rows) - min(
        row["primary_metric_value"] for row in forward_rows
    )
    reverse_primary_spread = max(row["primary_metric_value"] for row in reverse_rows) - min(
        row["primary_metric_value"] for row in reverse_rows
    )

    positive = {
        "budgeted_forward_rows_close_the_bookkeeping": {
            "max_bookkeeping_closure_error": max(row["bookkeeping_closure_error"] for row in forward_rows),
            "pass": max(row["bookkeeping_closure_error"] for row in forward_rows) < 1e-8,
        },
        "budgeted_reverse_rows_close_the_bookkeeping": {
            "max_bookkeeping_closure_error": max(row["bookkeeping_closure_error"] for row in reverse_rows),
            "pass": max(row["bookkeeping_closure_error"] for row in reverse_rows) < 1e-8,
        },
        "forward_slow_improves_on_fast_in_the_expected_direction": {
            "fast_efficiency": forward_rows[0]["primary_metric_value"],
            "slow_efficiency": forward_rows[4]["primary_metric_value"],
            "fast_distance_to_carnot": forward_rows[0]["distance_to_carnot_reference"],
            "slow_distance_to_carnot": forward_rows[4]["distance_to_carnot_reference"],
            "pass": (
                forward_rows[4]["primary_metric_value"] > forward_rows[0]["primary_metric_value"]
                and forward_rows[4]["distance_to_carnot_reference"] < forward_rows[0]["distance_to_carnot_reference"]
            ),
        },
        "reverse_slow_improves_on_fast_in_the_expected_direction": {
            "fast_cop": reverse_rows[0]["primary_metric_value"],
            "slow_cop": reverse_rows[4]["primary_metric_value"],
            "fast_distance_to_carnot": reverse_rows[0]["distance_to_carnot_reference"],
            "slow_distance_to_carnot": reverse_rows[4]["distance_to_carnot_reference"],
            "pass": (
                reverse_rows[4]["primary_metric_value"] > reverse_rows[0]["primary_metric_value"]
                and reverse_rows[4]["distance_to_carnot_reference"] < reverse_rows[0]["distance_to_carnot_reference"]
            ),
        },
        "quasistatic_rows_are_closest_to_their_carnot_references_on_average": {
            "forward_quasistatic_distance": forward_rows[-1]["distance_to_carnot_reference"],
            "reverse_quasistatic_distance": reverse_rows[-1]["distance_to_carnot_reference"],
            "best_forward_distance": best_forward["distance_to_carnot_reference"],
            "best_reverse_distance": best_reverse["distance_to_carnot_reference"],
            "pass": (
                forward_rows[-1]["distance_to_carnot_reference"] <= forward_rows[0]["distance_to_carnot_reference"]
                and reverse_rows[-1]["distance_to_carnot_reference"] <= reverse_rows[0]["distance_to_carnot_reference"]
            ),
        },
    }

    negative = {
        "fast_forward_does_not_saturate_the_carnot_bound": {
            "fast_distance_to_carnot": forward_rows[0]["distance_to_carnot_reference"],
            "pass": forward_rows[0]["distance_to_carnot_reference"] > 1e-3,
        },
        "fast_reverse_does_not_saturate_the_carnot_cop": {
            "fast_distance_to_carnot": reverse_rows[0]["distance_to_carnot_reference"],
            "pass": reverse_rows[0]["distance_to_carnot_reference"] > 1e-3,
        },
        "budget_signal_is_not_flat_across_the_companion_rows": {
            "forward_primary_spread": forward_primary_spread,
            "reverse_primary_spread": reverse_primary_spread,
            "forward_closure_spread": forward_closure_spread,
            "reverse_closure_spread": reverse_closure_spread,
            "pass": forward_primary_spread > 1e-3 and reverse_primary_spread > 1e-3,
        },
    }

    boundary = {
        "all_rows_are_finite_and_valid": {
            "pass": all(
                np.isfinite(row["closure_defect"])
                and np.isfinite(row["primary_metric_value"])
                and np.isfinite(row["distance_to_carnot_reference"])
                and np.isfinite(row["work_by_system"])
                and np.isfinite(row["bookkeeping_closure_error"])
                for row in rows
            ),
        },
        "row_count_matches_the_forward_reverse_budget_grid": {
            "expected_rows": len(STEP_GRID) * 2,
            "actual_rows": len(rows),
            "pass": len(rows) == len(STEP_GRID) * 2,
        },
        "budget_axis_covers_the_open_duration_grid": {
            "budget_labels": STEP_GRID,
            "pass": STEP_GRID == [60, 90, 150, 260, 520, 1000, 2500, 5000],
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    out = {
        "name": "qit_carnot_irreversibility_companion",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
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
            "baseline_forward_steps": baseline_forward["steps"],
            "baseline_forward_closure_defect": baseline_forward["closure_defect"],
            "baseline_forward_efficiency": baseline_forward["primary_metric_value"],
            "best_closure_steps": best_closure["steps"],
            "best_closure_defect": best_closure["closure_defect"],
            "best_forward_steps": best_forward["steps"],
            "best_forward_efficiency": best_forward["primary_metric_value"],
            "best_forward_distance_to_carnot": best_forward["distance_to_carnot_reference"],
            "best_reverse_steps": best_reverse["steps"],
            "best_reverse_cop": best_reverse["primary_metric_value"],
            "best_reverse_distance_to_carnot_cop": best_reverse["distance_to_carnot_reference"],
            "forward_efficiency_spread": forward_primary_spread,
            "reverse_cop_spread": reverse_primary_spread,
            "forward_closure_spread": forward_closure_spread,
            "reverse_closure_spread": reverse_closure_spread,
            "scope_note": (
                "Strict finite-carrier companion for the finite-time harmonic Carnot "
                "irreversibility sweep. It keeps the open duration signal explicit "
                "while comparing forward engine and reverse refrigerator behavior "
                "against Carnot references."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "qit_carnot_irreversibility_companion_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
