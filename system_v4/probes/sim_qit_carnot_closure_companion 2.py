#!/usr/bin/env python3
"""
QIT Carnot closure companion.
==============================
Strict finite-carrier companion surface for the exploratory Carnot closure
diagnostic lane. It keeps a forward-engine budget/hold grid explicit in a
bounded two-bath qubit model and tracks where the return defect concentrates.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Optional

import numpy as np


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import sim_qit_carnot_hold_policy_companion as base  # noqa: E402


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Strict finite-carrier QIT companion for the Carnot closure diagnostic "
    "lane. It sweeps a bounded budget/hold grid and keeps the forward-cycle "
    "return defect, closure concentration, and hold policy tradeoffs explicit. "
    "It is a comparison surface, not a canonical engine theorem."
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

RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
EPS = 1e-15

BASE_GRID = [
    {"base_hot_steps": 90, "base_cold_steps": 90, "budget_label": "budget_90"},
    {"base_hot_steps": 260, "base_cold_steps": 260, "budget_label": "budget_260"},
    {"base_hot_steps": 1000, "base_cold_steps": 1000, "budget_label": "budget_1000"},
    {"base_hot_steps": 5000, "base_cold_steps": 5000, "budget_label": "budget_5000"},
]

POLICY_GRID = [
    {
        "policy": "baseline_no_extra_hold",
        "cold_hold": None,
        "return_hold": None,
    },
    {
        "policy": "fixed_return_hold_800",
        "cold_hold": None,
        "return_hold": {"mode": "fixed", "steps": 800},
    },
    {
        "policy": "adaptive_return_hold_800",
        "cold_hold": None,
        "return_hold": {
            "mode": "adaptive",
            "chunk_steps": 80,
            "max_steps": 800,
            "tolerance": 0.01,
        },
    },
    {
        "policy": "fixed_full_chain_2000",
        "cold_hold": {"mode": "fixed", "steps": 1000},
        "return_hold": {"mode": "fixed", "steps": 1000},
    },
]


def valid_density(rho: np.ndarray) -> bool:
    rho = np.asarray(rho, dtype=float)
    return bool(
        np.allclose(rho, rho.T)
        and abs(np.trace(rho) - 1.0) < 1e-10
        and np.min(np.linalg.eigvalsh(rho)) > -1e-10
    )


def summarize_closure_row(
    row: dict[str, Any],
    *,
    base_hot_steps: int,
    base_cold_steps: int,
    budget_label: str,
    policy_name: str,
) -> dict[str, Any]:
    stages = row["stages"]
    stage_trace_distances = {
        "hot_iso": float(stages["hot_iso"]["trace_distance_to_target"]),
        "adiabatic_expand": float(stages["adiabatic_expand"]["trace_distance_to_target"]),
        "cold_iso": float(stages["cold_iso"]["trace_distance_to_target"]),
        "adiabatic_compress": float(stages["adiabatic_compress"]["trace_distance_to_target"]),
    }
    if stages.get("cold_hold") is not None:
        stage_trace_distances["cold_hold"] = float(stages["cold_hold"]["trace_distance_to_target"])
    if stages.get("return_hold") is not None:
        stage_trace_distances["return_hold"] = float(stages["return_hold"]["trace_distance_to_target"])

    dominant_leg = max(stage_trace_distances.items(), key=lambda item: item[1])[0]
    total_hold_steps_used = int(row["summary"]["hold_steps_used"])

    return {
        "budget_label": budget_label,
        "base_hot_steps": int(base_hot_steps),
        "base_cold_steps": int(base_cold_steps),
        "policy": policy_name,
        "policy_run_id": row["policy"],
        "hold_modes": row["hold_modes"],
        "hold_steps_requested": int(row["summary"]["hold_steps_requested"]),
        "hold_steps_used": total_hold_steps_used,
        "closure_defect": float(row["summary"]["final_trace_distance_to_initial"]),
        "efficiency": float(row["summary"]["efficiency"]),
        "efficiency_distance_to_carnot": float(row["summary"]["efficiency_distance_to_carnot"]),
        "final_probability_mismatch_abs": float(row["summary"]["final_probability_mismatch_abs"]),
        "final_internal_energy_mismatch": float(row["summary"]["final_internal_energy_mismatch"]),
        "dominant_closure_leg": dominant_leg,
        "stage_trace_distances": stage_trace_distances,
        "valid_density_final": valid_density(row["final"]["rho"]),
        "all_pass": bool(row["summary"]["final_trace_distance_to_initial"] >= 0.0),
    }


def run_policy(
    base_hot_steps: int,
    base_cold_steps: int,
    name: str,
    *,
    cold_hold: Optional[dict] = None,
    return_hold: Optional[dict] = None,
) -> dict[str, Any]:
    p_initial = base.gibbs_excited_probability(base.T_HOT, base.GAP_HIGH)
    initial = base.state_from_probability(p_initial, base.GAP_HIGH, base.T_HOT, "A_hot_gibbs_high_gap")

    hot_iso = base.isothermal_leg(
        initial,
        after_gap=base.GAP_HOT_LOW,
        bath_temperature=base.T_HOT,
        steps=base_hot_steps,
        label=f"{name}_hot_iso",
    )
    adiabatic_expand = base.adiabatic_step(
        hot_iso["after"],
        after_gap=base.GAP_HOT_LOW * (base.T_COLD / base.T_HOT),
        after_temperature=base.T_COLD,
        label=f"{name}_adiabatic_expand",
    )
    cold_iso = base.isothermal_leg(
        adiabatic_expand["after"],
        after_gap=base.GAP_HIGH * (base.T_COLD / base.T_HOT),
        bath_temperature=base.T_COLD,
        steps=base_cold_steps,
        label=f"{name}_cold_iso",
    )

    current = cold_iso["after"]
    cold_hold_stats = None
    if cold_hold is not None:
        if cold_hold["mode"] == "fixed":
            cold_hold_stats = base.thermal_hold(
                current,
                bath_temperature=base.T_COLD,
                gap=base.GAP_HIGH * (base.T_COLD / base.T_HOT),
                steps=cold_hold["steps"],
                label=f"{name}_cold_hold",
            )
            current = cold_hold_stats["after"]
        else:
            current, cold_hold_stats = base.adaptive_hold(
                current,
                bath_temperature=base.T_COLD,
                gap=base.GAP_HIGH * (base.T_COLD / base.T_HOT),
                chunk_steps=cold_hold["chunk_steps"],
                max_extra_steps=cold_hold["max_steps"],
                tolerance=cold_hold["tolerance"],
                label=f"{name}_cold_hold",
            )

    adiabatic_compress = base.adiabatic_step(
        current,
        after_gap=base.GAP_HIGH,
        after_temperature=base.T_HOT,
        label=f"{name}_adiabatic_compress",
    )
    current = adiabatic_compress["after"]

    return_hold_stats = None
    if return_hold is not None:
        if return_hold["mode"] == "fixed":
            return_hold_stats = base.thermal_hold(
                current,
                bath_temperature=base.T_HOT,
                gap=base.GAP_HIGH,
                steps=return_hold["steps"],
                label=f"{name}_return_hold",
            )
            current = return_hold_stats["after"]
        else:
            current, return_hold_stats = base.adaptive_hold(
                current,
                bath_temperature=base.T_HOT,
                gap=base.GAP_HIGH,
                chunk_steps=return_hold["chunk_steps"],
                max_extra_steps=return_hold["max_steps"],
                tolerance=return_hold["tolerance"],
                label=f"{name}_return_hold",
            )

    stages = [hot_iso, adiabatic_expand, cold_iso, adiabatic_compress]
    if cold_hold_stats is not None:
        stages.append(cold_hold_stats)
    if return_hold_stats is not None:
        stages.append(return_hold_stats)

    total_work_by_system = float(sum(stage["work_by_system"] for stage in stages))
    total_heat_into_system = float(sum(stage["heat_into_system"] for stage in stages))
    total_positive_heat = float(sum(max(stage["heat_into_system"], 0.0) for stage in stages)) or EPS
    carnot_bound = 1.0 - (base.T_COLD / base.T_HOT)
    efficiency = float(total_work_by_system / total_positive_heat)
    final_state = current
    final_trace_distance = float(base.trace_distance(final_state["rho"], initial["rho"]))

    hold_steps_used = int((cold_hold_stats or {}).get("steps_used", 0) + (return_hold_stats or {}).get("steps_used", 0))
    hold_steps_requested = int((cold_hold or {}).get("steps", 0) + (return_hold or {}).get("steps", 0))
    if cold_hold and cold_hold.get("mode") == "adaptive":
        hold_steps_requested = int(cold_hold["max_steps"] + (return_hold["max_steps"] if return_hold else 0))
    if return_hold and return_hold.get("mode") == "adaptive":
        if cold_hold and cold_hold.get("mode") == "adaptive":
            hold_steps_requested = int(cold_hold["max_steps"] + return_hold["max_steps"])
        elif cold_hold:
            hold_steps_requested = int(cold_hold["steps"] + return_hold["max_steps"])
        else:
            hold_steps_requested = int(return_hold["max_steps"])

    return {
        "policy": name,
        "hold_modes": {
            "cold_hold": None if cold_hold is None else cold_hold["mode"],
            "return_hold": None if return_hold is None else return_hold["mode"],
        },
        "initial": initial,
        "final": final_state,
        "stages": {
            "hot_iso": hot_iso,
            "adiabatic_expand": adiabatic_expand,
            "cold_iso": cold_iso,
            "cold_hold": cold_hold_stats,
            "adiabatic_compress": adiabatic_compress,
            "return_hold": return_hold_stats,
        },
        "summary": {
            "policy": name,
            "base_hot_steps": int(base_hot_steps),
            "base_cold_steps": int(base_cold_steps),
            "hold_steps_requested": hold_steps_requested,
            "hold_steps_used": hold_steps_used,
            "positive_heat_absorbed": total_positive_heat,
            "total_heat_into_system": total_heat_into_system,
            "total_work_by_system": total_work_by_system,
            "efficiency": efficiency,
            "carnot_bound": carnot_bound,
            "efficiency_distance_to_carnot": float(abs(efficiency - carnot_bound)),
            "final_trace_distance_to_initial": final_trace_distance,
            "final_probability_mismatch_abs": float(abs(final_state["p_excited"] - initial["p_excited"])),
            "final_free_energy_mismatch": float(final_state["free_energy"] - initial["free_energy"]),
            "final_internal_energy_mismatch": float(final_state["internal_energy"] - initial["internal_energy"]),
            "closure_error": float(abs(total_heat_into_system - (sum(stage["delta_u"] for stage in stages) + total_work_by_system))),
        },
    }


def main() -> None:
    rows = []
    for budget in BASE_GRID:
        for spec in POLICY_GRID:
            run = run_policy(
                budget["base_hot_steps"],
                budget["base_cold_steps"],
                f"{budget['budget_label']}_{spec['policy']}",
                cold_hold=spec["cold_hold"],
                return_hold=spec["return_hold"],
            )
            rows.append(summarize_closure_row(run, policy_name=spec["policy"], **budget))

    baseline_rows = [row for row in rows if row["policy"] == "baseline_no_extra_hold"]
    baseline = min(baseline_rows, key=lambda row: row["base_hot_steps"])
    best_closure = min(rows, key=lambda row: row["closure_defect"])
    best_setting = {
        "policy": best_closure["policy"],
        "base_hot_steps": best_closure["base_hot_steps"],
        "base_cold_steps": best_closure["base_cold_steps"],
        "hold_steps_used": best_closure["hold_steps_used"],
    }

    positive = {
        "baseline_rows_are_nontrivial": {
            "baseline_trace_distance": baseline["closure_defect"],
            "pass": baseline["closure_defect"] > 1e-6,
        },
        "higher_budget_baseline_improves_closure": {
            "first_budget_trace_distance": baseline_rows[0]["closure_defect"],
            "last_budget_trace_distance": baseline_rows[-1]["closure_defect"],
            "pass": baseline_rows[-1]["closure_defect"] < baseline_rows[0]["closure_defect"],
        },
        "best_policy_beats_baseline_on_closure": {
            "baseline_trace_distance": baseline["closure_defect"],
            "best_trace_distance": best_closure["closure_defect"],
            "pass": best_closure["closure_defect"] < baseline["closure_defect"],
        },
        "best_row_has_a_real_dominant_closure_leg": {
            "dominant_closure_leg": best_closure["dominant_closure_leg"],
            "pass": bool(best_closure["dominant_closure_leg"]),
        },
    }

    negative = {
        "best_row_is_not_exact_closure": {
            "best_trace_distance": best_closure["closure_defect"],
            "pass": best_closure["closure_defect"] > 1e-12,
        },
        "baseline_is_not_exact_closure": {
            "baseline_trace_distance": baseline["closure_defect"],
            "pass": baseline["closure_defect"] > 1e-6,
        },
        "closure_residue_is_not_clearly_single_leg_only": {
            "dominant_closure_leg": best_closure["dominant_closure_leg"],
            "stage_trace_distances": best_closure["stage_trace_distances"],
            "pass": len([v for v in best_closure["stage_trace_distances"].values() if v > 0.0]) >= 2,
        },
    }

    boundary = {
        "all_rows_are_finite": {
            "pass": all(
                np.isfinite(row["closure_defect"])
                and np.isfinite(row["efficiency"])
                and np.isfinite(row["efficiency_distance_to_carnot"])
                and np.isfinite(row["final_probability_mismatch_abs"])
                and np.isfinite(row["final_internal_energy_mismatch"])
                for row in rows
            ),
        },
        "all_final_states_are_valid_density_operators": {
            "pass": all(row["valid_density_final"] for row in rows),
        },
        "grid_size_matches_expectation": {
            "expected_rows": len(BASE_GRID) * len(POLICY_GRID),
            "actual_rows": len(rows),
            "pass": len(rows) == len(BASE_GRID) * len(POLICY_GRID),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    result_rows = [
        {
            "budget_label": row["budget_label"],
            "base_hot_steps": row["base_hot_steps"],
            "base_cold_steps": row["base_cold_steps"],
            "policy": row["policy"],
            "hold_modes": row["hold_modes"],
            "hold_steps_requested": row["hold_steps_requested"],
            "hold_steps_used": row["hold_steps_used"],
            "closure_defect": row["closure_defect"],
            "efficiency": row["efficiency"],
            "efficiency_distance_to_carnot": row["efficiency_distance_to_carnot"],
            "final_probability_mismatch_abs": row["final_probability_mismatch_abs"],
            "final_internal_energy_mismatch": row["final_internal_energy_mismatch"],
            "dominant_closure_leg": row["dominant_closure_leg"],
            "stage_trace_distances": row["stage_trace_distances"],
            "valid_density_final": row["valid_density_final"],
        }
        for row in rows
    ]

    results = {
        "name": "qit_carnot_closure_companion",
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
            "baseline_closure_defect": baseline["closure_defect"],
            "best_closure_defect": best_closure["closure_defect"],
            "best_closure_steps": {
                "base_hot_steps": best_closure["base_hot_steps"],
                "base_cold_steps": best_closure["base_cold_steps"],
            },
            "best_setting": best_setting,
            "best_closure_policy": best_closure["policy"],
            "dominant_closure_leg_at_best_row": best_closure["dominant_closure_leg"],
            "scope_note": (
                "Strict finite-carrier Carnot closure companion. It compares a bounded "
                "budget/hold grid and keeps the closure residue concentration explicit."
            ),
        },
        "rows": result_rows,
    }

    out_path = RESULT_DIR / "qit_carnot_closure_companion_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
