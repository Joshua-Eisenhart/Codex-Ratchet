#!/usr/bin/env python3
"""
QIT Carnot finite-time companion.
=================================
Strict finite-carrier companion surface for the exploratory finite-time
stochastic Carnot lane. It preserves the fast/slow/quasistatic budget signal
in a bounded two-bath qubit model, with explicit forward engine and reverse
refrigerator modes.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import sim_qit_carnot_hold_policy_companion as base  # noqa: E402


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Strict finite-carrier QIT companion for the finite-time Carnot lane. "
    "It preserves fast/slow/quasistatic tradeoffs in a bounded two-bath qubit "
    "model with explicit forward engine and reverse refrigerator modes. It is a "
    "comparison surface, not a canonical engine theorem."
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

T_HOT = 2.0
T_COLD = 1.0
GAP_HIGH = 3.0
GAP_HOT_LOW = 1.0

BUDGET_GRID = [
    {"budget_label": "fast", "steps_per_isotherm": 90},
    {"budget_label": "slow", "steps_per_isotherm": 520},
    {"budget_label": "quasistatic", "steps_per_isotherm": 5000},
]

RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
EPS = 1e-15


def compact_state(state: dict) -> dict:
    return {
        "label": state["label"],
        "gap": float(state["gap"]),
        "temperature": float(state["temperature"]),
        "p_excited": float(state["p_excited"]),
        "entropy": float(state["entropy"]),
        "internal_energy": float(state["internal_energy"]),
        "free_energy": float(state["free_energy"]),
    }


def compact_isothermal(stage: dict) -> dict:
    return {
        "kind": "isothermal",
        "bath_temperature": float(stage["bath_temperature"]),
        "steps": int(stage["steps"]),
        "delta_u": float(stage["delta_u"]),
        "work_by_system": float(stage["work_by_system"]),
        "heat_into_system": float(stage["heat_into_system"]),
        "closure_error": float(stage.get("closure_error", 0.0)),
        "probability_mismatch_abs": float(stage["probability_mismatch_abs"]),
        "trace_distance_to_target": float(stage["trace_distance_to_target"]),
    }


def compact_adiabatic(stage: dict) -> dict:
    return {
        "kind": "adiabatic",
        "delta_u": float(stage["delta_u"]),
        "work_by_system": float(stage["work_by_system"]),
        "heat_into_system": float(stage["heat_into_system"]),
        "closure_error": float(stage.get("closure_error", 0.0)),
        "trace_distance_to_target": float(stage["trace_distance_to_target"]),
    }


def initial_state() -> dict:
    p_initial = base.gibbs_excited_probability(T_HOT, GAP_HIGH)
    return base.state_from_probability(p_initial, GAP_HIGH, T_HOT, "A_hot_gibbs_high_gap")


def final_row_state(row: dict) -> dict:
    return compact_state(row["final"])


def run_forward_cycle(steps_per_isotherm: int, budget_label: str) -> dict:
    initial = initial_state()
    hot_iso = base.isothermal_leg(
        initial,
        after_gap=GAP_HOT_LOW,
        bath_temperature=T_HOT,
        steps=steps_per_isotherm,
        label=f"{budget_label}_hot_isotherm_expansion",
    )
    adiabatic_expand = base.adiabatic_step(
        hot_iso["after"],
        after_gap=GAP_HOT_LOW * (T_COLD / T_HOT),
        after_temperature=T_COLD,
        label=f"{budget_label}_cold_ready_low_gap",
    )
    cold_iso = base.isothermal_leg(
        adiabatic_expand["after"],
        after_gap=GAP_HIGH * (T_COLD / T_HOT),
        bath_temperature=T_COLD,
        steps=steps_per_isotherm,
        label=f"{budget_label}_cold_isotherm_compression",
    )
    adiabatic_compress = base.adiabatic_step(
        cold_iso["after"],
        after_gap=GAP_HIGH,
        after_temperature=T_HOT,
        label=f"{budget_label}_hot_return_gap",
    )

    stages = [hot_iso, adiabatic_expand, cold_iso, adiabatic_compress]
    total_work_by_system = float(sum(stage["work_by_system"] for stage in stages))
    total_heat_into_system = float(sum(stage["heat_into_system"] for stage in stages))
    bookkeeping_closure_error = float(sum(float(stage.get("closure_error", 0.0)) for stage in stages))
    positive_heat_absorbed = float(sum(max(stage["heat_into_system"], 0.0) for stage in stages))
    if positive_heat_absorbed <= 0.0:
        positive_heat_absorbed = EPS
    carnot_bound = 1.0 - (T_COLD / T_HOT)
    efficiency = float(total_work_by_system / positive_heat_absorbed)
    final = adiabatic_compress["after"]
    closure_defect = float(base.trace_distance(final["rho"], initial["rho"]))

    return {
        "row_id": f"forward_{budget_label}",
        "direction": "forward",
        "budget_label": budget_label,
        "steps_per_isotherm": int(steps_per_isotherm),
        "initial": compact_state(initial),
        "final": compact_state(final),
        "closure_defect": closure_defect,
        "primary_metric_name": "efficiency",
        "primary_metric_value": efficiency,
        "distance_to_carnot_reference": float(abs(efficiency - carnot_bound)),
        "carnot_reference": float(carnot_bound),
        "work_by_system": total_work_by_system,
        "positive_heat_absorbed": positive_heat_absorbed,
        "total_heat_into_system": total_heat_into_system,
        "bookkeeping_closure_error": bookkeeping_closure_error,
        "final_trace_distance_to_initial": closure_defect,
        "final_probability_mismatch_abs": float(abs(final["p_excited"] - initial["p_excited"])),
        "final_free_energy_mismatch": float(final["free_energy"] - initial["free_energy"]),
        "final_internal_energy_mismatch": float(final["internal_energy"] - initial["internal_energy"]),
        "stages": {
            "hot_iso": compact_isothermal(hot_iso),
            "adiabatic_expand": compact_adiabatic(adiabatic_expand),
            "cold_iso": compact_isothermal(cold_iso),
            "adiabatic_compress": compact_adiabatic(adiabatic_compress),
        },
    }


def run_reverse_cycle(steps_per_isotherm: int, budget_label: str) -> dict:
    initial = initial_state()
    adiabatic_to_cold = base.adiabatic_step(
        initial,
        after_gap=GAP_HIGH * (T_COLD / T_HOT),
        after_temperature=T_COLD,
        label=f"{budget_label}_cold_ready_high_gap",
    )
    cold_iso_reverse = base.isothermal_leg(
        adiabatic_to_cold["after"],
        after_gap=GAP_HOT_LOW * (T_COLD / T_HOT),
        bath_temperature=T_COLD,
        steps=steps_per_isotherm,
        label=f"{budget_label}_cold_isotherm_reverse",
    )
    adiabatic_to_hot = base.adiabatic_step(
        cold_iso_reverse["after"],
        after_gap=GAP_HOT_LOW,
        after_temperature=T_HOT,
        label=f"{budget_label}_hot_ready_low_gap",
    )
    hot_iso_reverse = base.isothermal_leg(
        adiabatic_to_hot["after"],
        after_gap=GAP_HIGH,
        bath_temperature=T_HOT,
        steps=steps_per_isotherm,
        label=f"{budget_label}_hot_isotherm_reverse",
    )

    stages = [adiabatic_to_cold, cold_iso_reverse, adiabatic_to_hot, hot_iso_reverse]
    total_work_by_system = float(sum(stage["work_by_system"] for stage in stages))
    total_heat_into_system = float(sum(stage["heat_into_system"] for stage in stages))
    bookkeeping_closure_error = float(sum(float(stage.get("closure_error", 0.0)) for stage in stages))
    q_cold_absorbed = float(cold_iso_reverse["heat_into_system"])
    work_input = float(-total_work_by_system)
    cop_carnot = T_COLD / (T_HOT - T_COLD)
    cop = float(q_cold_absorbed / work_input) if abs(work_input) > EPS else float("inf")
    final = hot_iso_reverse["after"]
    closure_defect = float(base.trace_distance(final["rho"], initial["rho"]))

    return {
        "row_id": f"reverse_{budget_label}",
        "direction": "reverse",
        "budget_label": budget_label,
        "steps_per_isotherm": int(steps_per_isotherm),
        "initial": compact_state(initial),
        "final": compact_state(final),
        "closure_defect": closure_defect,
        "primary_metric_name": "cop",
        "primary_metric_value": cop,
        "distance_to_carnot_reference": float(abs(cop - cop_carnot)),
        "carnot_reference": float(cop_carnot),
        "work_by_system": total_work_by_system,
        "work_input": work_input,
        "q_cold_absorbed": q_cold_absorbed,
        "total_heat_into_system": total_heat_into_system,
        "bookkeeping_closure_error": bookkeeping_closure_error,
        "final_trace_distance_to_initial": closure_defect,
        "final_probability_mismatch_abs": float(abs(final["p_excited"] - initial["p_excited"])),
        "final_free_energy_mismatch": float(final["free_energy"] - initial["free_energy"]),
        "final_internal_energy_mismatch": float(final["internal_energy"] - initial["internal_energy"]),
        "stages": {
            "adiabatic_to_cold": compact_adiabatic(adiabatic_to_cold),
            "cold_iso_reverse": compact_isothermal(cold_iso_reverse),
            "adiabatic_to_hot": compact_adiabatic(adiabatic_to_hot),
            "hot_iso_reverse": compact_isothermal(hot_iso_reverse),
        },
    }


def mean(values) -> float:
    values = list(values)
    return float(np.mean(values)) if values else 0.0


def main() -> None:
    rows = []
    for budget in BUDGET_GRID:
        rows.append(run_forward_cycle(budget["steps_per_isotherm"], budget["budget_label"]))
        rows.append(run_reverse_cycle(budget["steps_per_isotherm"], budget["budget_label"]))

    forward_rows = [row for row in rows if row["direction"] == "forward"]
    reverse_rows = [row for row in rows if row["direction"] == "reverse"]

    baseline_forward = next(row for row in forward_rows if row["budget_label"] == "fast")
    best_closure = min(rows, key=lambda row: row["closure_defect"])
    best_forward = max(forward_rows, key=lambda row: row["primary_metric_value"])
    best_reverse = max(reverse_rows, key=lambda row: row["primary_metric_value"])
    fastest_forward = next(row for row in forward_rows if row["budget_label"] == "fast")
    slowest_forward = next(row for row in forward_rows if row["budget_label"] == "quasistatic")
    fastest_reverse = next(row for row in reverse_rows if row["budget_label"] == "fast")
    slowest_reverse = next(row for row in reverse_rows if row["budget_label"] == "quasistatic")

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
            "fast_efficiency": fastest_forward["primary_metric_value"],
            "slow_efficiency": next(row for row in forward_rows if row["budget_label"] == "slow")["primary_metric_value"],
            "fast_distance_to_carnot": fastest_forward["distance_to_carnot_reference"],
            "slow_distance_to_carnot": next(row for row in forward_rows if row["budget_label"] == "slow")["distance_to_carnot_reference"],
            "pass": (
                next(row for row in forward_rows if row["budget_label"] == "slow")["primary_metric_value"]
                > fastest_forward["primary_metric_value"]
                and next(row for row in forward_rows if row["budget_label"] == "slow")["distance_to_carnot_reference"]
                < fastest_forward["distance_to_carnot_reference"]
            ),
        },
        "reverse_slow_improves_on_fast_in_the_expected_direction": {
            "fast_cop": fastest_reverse["primary_metric_value"],
            "slow_cop": next(row for row in reverse_rows if row["budget_label"] == "slow")["primary_metric_value"],
            "fast_distance_to_carnot": fastest_reverse["distance_to_carnot_reference"],
            "slow_distance_to_carnot": next(row for row in reverse_rows if row["budget_label"] == "slow")["distance_to_carnot_reference"],
            "pass": (
                next(row for row in reverse_rows if row["budget_label"] == "slow")["primary_metric_value"]
                > fastest_reverse["primary_metric_value"]
                and next(row for row in reverse_rows if row["budget_label"] == "slow")["distance_to_carnot_reference"]
                < fastest_reverse["distance_to_carnot_reference"]
            ),
        },
        "quasistatic_rows_are_closest_to_their_carnot_references_on_average": {
            "forward_quasistatic_distance": slowest_forward["distance_to_carnot_reference"],
            "reverse_quasistatic_distance": slowest_reverse["distance_to_carnot_reference"],
            "best_forward_distance": best_forward["distance_to_carnot_reference"],
            "best_reverse_distance": best_reverse["distance_to_carnot_reference"],
            "pass": (
                slowest_forward["distance_to_carnot_reference"] <= fastest_forward["distance_to_carnot_reference"]
                and slowest_reverse["distance_to_carnot_reference"] <= fastest_reverse["distance_to_carnot_reference"]
            ),
        },
    }

    negative = {
        "fast_forward_does_not_saturate_the_carnot_bound": {
            "fast_distance_to_carnot": fastest_forward["distance_to_carnot_reference"],
            "pass": fastest_forward["distance_to_carnot_reference"] > 1e-3,
        },
        "fast_reverse_does_not_saturate_the_carnot_cop": {
            "fast_distance_to_carnot": fastest_reverse["distance_to_carnot_reference"],
            "pass": fastest_reverse["distance_to_carnot_reference"] > 1e-3,
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
            "expected_rows": len(BUDGET_GRID) * 2,
            "actual_rows": len(rows),
            "pass": len(rows) == len(BUDGET_GRID) * 2,
        },
        "budget_axis_covers_fast_slow_quasistatic": {
            "budget_labels": [item["budget_label"] for item in BUDGET_GRID],
            "pass": [item["budget_label"] for item in BUDGET_GRID] == ["fast", "slow", "quasistatic"],
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    summary = {
        "all_pass": bool(all_pass),
        "budget_axis": [item["budget_label"] for item in BUDGET_GRID],
        "budget_steps_per_isotherm": [item["steps_per_isotherm"] for item in BUDGET_GRID],
        "baseline_forward_budget_label": baseline_forward["budget_label"],
        "baseline_forward_closure_defect": baseline_forward["closure_defect"],
        "baseline_forward_bookkeeping_closure_error": baseline_forward["bookkeeping_closure_error"],
        "baseline_forward_efficiency": baseline_forward["primary_metric_value"],
        "best_closure_row_id": best_closure["row_id"],
        "best_closure_budget_label": best_closure["budget_label"],
        "best_closure_direction": best_closure["direction"],
        "best_closure_defect": best_closure["closure_defect"],
        "best_closure_bookkeeping_closure_error": best_closure["bookkeeping_closure_error"],
        "best_forward_row_id": best_forward["row_id"],
        "best_forward_budget_label": best_forward["budget_label"],
        "best_forward_efficiency": best_forward["primary_metric_value"],
        "best_forward_distance_to_carnot": best_forward["distance_to_carnot_reference"],
        "best_reverse_row_id": best_reverse["row_id"],
        "best_reverse_budget_label": best_reverse["budget_label"],
        "best_reverse_cop": best_reverse["primary_metric_value"],
        "best_reverse_distance_to_carnot": best_reverse["distance_to_carnot_reference"],
        "forward_efficiency_spread": forward_primary_spread,
        "reverse_cop_spread": reverse_primary_spread,
        "forward_closure_spread": forward_closure_spread,
        "reverse_closure_spread": reverse_closure_spread,
        "fast_to_quasistatic_forward_efficiency_gain": slowest_forward["primary_metric_value"] - fastest_forward["primary_metric_value"],
        "fast_to_quasistatic_reverse_cop_gain": slowest_reverse["primary_metric_value"] - fastest_reverse["primary_metric_value"],
        "scope_note": (
            "Strict finite-carrier companion for the finite-time harmonic Carnot sidecar. "
            "It keeps the budget axis explicit while comparing forward engine and reverse "
            "refrigerator behavior against the Carnot references."
        ),
    }

    results = {
        "name": "qit_carnot_finite_time_companion",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "rows": rows,
    }

    out_path = RESULT_DIR / "qit_carnot_finite_time_companion_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
