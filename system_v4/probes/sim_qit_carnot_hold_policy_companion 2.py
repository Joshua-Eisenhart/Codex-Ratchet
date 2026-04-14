#!/usr/bin/env python3
"""
QIT Carnot hold-policy companion.

This is a bounded two-bath qubit companion row that adds explicit finite
partial-thermalization holds to the canonical Carnot bookkeeping lane. The
goal is to compare baseline closure defect against fixed and adaptive hold
policies, not to claim a new canonical engine theorem.
"""

from __future__ import annotations

import json
import pathlib
from typing import Dict, List, Optional, Tuple

import numpy as np


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "QIT-aligned Carnot companion row with finite partial-thermalization hold "
    "policies. It compares baseline closure defect, fixed holds, and adaptive "
    "hold-stop rules on a qubit working substance. This is a bounded comparison "
    "surface, not a canonical engine theorem."
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
BASE_HOT_STEPS = 520
BASE_COLD_STEPS = 520
HOLD_RELAX_SCALE = 420.0
ADAPTIVE_CHUNK_STEPS = 80
ADAPTIVE_TOLERANCE = 0.01
ADAPTIVE_BUDGET = 800
FIXED_RETURN_HOLD_STEPS = 800
FIXED_FULL_CHAIN_HOLD_STEPS = 2000
RNG_SEED = 20260410
EPS = 1e-15

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"


def binary_entropy(p: float) -> float:
    p = min(max(float(p), EPS), 1.0 - EPS)
    return float(-(p * np.log(p) + (1.0 - p) * np.log(1.0 - p)))


def gibbs_excited_probability(temperature: float, gap: float) -> float:
    beta = 1.0 / float(temperature)
    weight = np.exp(-beta * gap)
    return float(weight / (1.0 + weight))


def density_from_probability(p_excited: float) -> np.ndarray:
    p = min(max(float(p_excited), 0.0), 1.0)
    return np.array([[1.0 - p, 0.0], [0.0, p]], dtype=float)


def trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    diff = (rho - sigma + (rho - sigma).T) / 2.0
    vals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(vals)))


def state_from_probability(p_excited: float, gap: float, temperature: float, label: str) -> dict:
    entropy = binary_entropy(p_excited)
    internal_energy = float(p_excited * gap)
    free_energy = float(internal_energy - temperature * entropy)
    rho = density_from_probability(p_excited)
    return {
        "label": label,
        "gap": float(gap),
        "temperature": float(temperature),
        "p_excited": float(p_excited),
        "entropy": entropy,
        "internal_energy": internal_energy,
        "free_energy": free_energy,
        "rho": rho,
    }


def relax_probability(p0: float, p_eq: float, steps: int) -> float:
    if steps <= 0:
        return float(p0)
    alpha = 1.0 - np.exp(-float(steps) / HOLD_RELAX_SCALE)
    return float((1.0 - alpha) * p0 + alpha * p_eq)


def isothermal_leg(
    before: dict,
    after_gap: float,
    bath_temperature: float,
    steps: int,
    label: str,
) -> dict:
    p_eq = gibbs_excited_probability(bath_temperature, after_gap)
    p_after = relax_probability(before["p_excited"], p_eq, steps)
    after = state_from_probability(p_after, after_gap, bath_temperature, label)
    delta_u = float(after["internal_energy"] - before["internal_energy"])
    delta_f = float(after["free_energy"] - before["free_energy"])
    work_by_system = float(-delta_f)
    heat_into_system = float(delta_u + work_by_system)
    return {
        "kind": "isothermal",
        "bath_temperature": float(bath_temperature),
        "steps": int(steps),
        "before": before,
        "after": after,
        "delta_u": delta_u,
        "work_by_system": work_by_system,
        "heat_into_system": heat_into_system,
        "target_probability": p_eq,
        "probability_mismatch_abs": float(abs(p_after - p_eq)),
        "trace_distance_to_target": float(
            trace_distance(after["rho"], density_from_probability(p_eq))
        ),
    }


def thermal_hold(
    before: dict,
    bath_temperature: float,
    gap: float,
    steps: int,
    label: str,
) -> dict:
    p_eq = gibbs_excited_probability(bath_temperature, gap)
    p_after = relax_probability(before["p_excited"], p_eq, steps)
    after = state_from_probability(p_after, gap, bath_temperature, label)
    delta_u = float(after["internal_energy"] - before["internal_energy"])
    return {
        "kind": "hold",
        "bath_temperature": float(bath_temperature),
        "gap": float(gap),
        "steps_requested": int(steps),
        "steps_used": int(steps),
        "before": before,
        "after": after,
        "delta_u": delta_u,
        "work_by_system": 0.0,
        "heat_into_system": delta_u,
        "target_probability": p_eq,
        "probability_mismatch_abs": float(abs(p_after - p_eq)),
        "trace_distance_to_target": float(
            trace_distance(after["rho"], density_from_probability(p_eq))
        ),
    }


def adiabatic_step(before: dict, after_gap: float, after_temperature: float, label: str) -> dict:
    after = state_from_probability(before["p_excited"], after_gap, after_temperature, label)
    delta_u = float(after["internal_energy"] - before["internal_energy"])
    return {
        "kind": "adiabatic",
        "before": before,
        "after": after,
        "delta_u": delta_u,
        "work_by_system": float(-delta_u),
        "heat_into_system": 0.0,
        "trace_distance_to_target": 0.0,
    }


def adaptive_hold(
    before: dict,
    bath_temperature: float,
    gap: float,
    chunk_steps: int,
    max_extra_steps: int,
    tolerance: float,
    label: str,
) -> tuple[dict, dict]:
    current = before
    steps_used = 0
    chunks = 0
    total_heat = 0.0
    stop_reason = "budget_exhausted"
    target = density_from_probability(gibbs_excited_probability(bath_temperature, gap))

    while steps_used < max_extra_steps:
        current_dist = trace_distance(current["rho"], target)
        if current_dist <= tolerance:
            stop_reason = "within_tolerance"
            break

        step = min(chunk_steps, max_extra_steps - steps_used)
        if step <= 0:
            break

        hold = thermal_hold(
            current,
            bath_temperature=bath_temperature,
            gap=gap,
            steps=step,
            label=f"{label}_chunk_{chunks}",
        )
        current = hold["after"]
        steps_used += step
        chunks += 1
        total_heat += hold["heat_into_system"]

    final_dist = trace_distance(current["rho"], target)
    if final_dist <= tolerance:
        stop_reason = "within_tolerance"
    elif steps_used == 0:
        stop_reason = "disabled"

    return current, {
        "kind": "adaptive_hold",
        "bath_temperature": float(bath_temperature),
        "gap": float(gap),
        "steps_requested": int(max_extra_steps),
        "steps_used": int(steps_used),
        "chunks": int(chunks),
        "stop_reason": stop_reason,
        "target_probability": float(target[1, 1]),
        "probability_mismatch_abs": float(abs(current["p_excited"] - target[1, 1])),
        "trace_distance_to_target": float(final_dist),
        "delta_u": float(total_heat),
        "work_by_system": 0.0,
        "heat_into_system": float(total_heat),
    }


def run_policy(
    name: str,
    *,
    cold_hold: Optional[dict] = None,
    return_hold: Optional[dict] = None,
) -> dict:
    p_initial = gibbs_excited_probability(T_HOT, GAP_HIGH)
    initial = state_from_probability(p_initial, GAP_HIGH, T_HOT, "A_hot_gibbs_high_gap")

    hot_iso = isothermal_leg(
        initial,
        after_gap=GAP_HOT_LOW,
        bath_temperature=T_HOT,
        steps=BASE_HOT_STEPS,
        label="B_hot_gibbs_low_gap",
    )
    adiabatic_expand = adiabatic_step(
        hot_iso["after"],
        after_gap=GAP_HOT_LOW * (T_COLD / T_HOT),
        after_temperature=T_COLD,
        label="C_cold_ready_low_gap",
    )
    cold_iso = isothermal_leg(
        adiabatic_expand["after"],
        after_gap=GAP_HIGH * (T_COLD / T_HOT),
        bath_temperature=T_COLD,
        steps=BASE_COLD_STEPS,
        label="D_cold_gibbs_high_gap",
    )

    current = cold_iso["after"]
    cold_hold_stats = None
    if cold_hold is not None:
        if cold_hold["mode"] == "fixed":
            cold_hold_stats = thermal_hold(
                current,
                bath_temperature=T_COLD,
                gap=GAP_HIGH * (T_COLD / T_HOT),
                steps=cold_hold["steps"],
                label="E_cold_hold",
            )
            current = cold_hold_stats["after"]
        else:
            current, cold_hold_stats = adaptive_hold(
                current,
                bath_temperature=T_COLD,
                gap=GAP_HIGH * (T_COLD / T_HOT),
                chunk_steps=cold_hold["chunk_steps"],
                max_extra_steps=cold_hold["max_steps"],
                tolerance=cold_hold["tolerance"],
                label="E_cold_hold",
            )

    adiabatic_compress = adiabatic_step(
        current,
        after_gap=GAP_HIGH,
        after_temperature=T_HOT,
        label="F_hot_gibbs_high_gap_return",
    )
    current = adiabatic_compress["after"]

    return_hold_stats = None
    if return_hold is not None:
        if return_hold["mode"] == "fixed":
            return_hold_stats = thermal_hold(
                current,
                bath_temperature=T_HOT,
                gap=GAP_HIGH,
                steps=return_hold["steps"],
                label="G_hot_return_hold",
            )
            current = return_hold_stats["after"]
        else:
            current, return_hold_stats = adaptive_hold(
                current,
                bath_temperature=T_HOT,
                gap=GAP_HIGH,
                chunk_steps=return_hold["chunk_steps"],
                max_extra_steps=return_hold["max_steps"],
                tolerance=return_hold["tolerance"],
                label="G_hot_return_hold",
            )

    stages = [hot_iso, adiabatic_expand, cold_iso, adiabatic_compress]
    if cold_hold_stats is not None:
        stages.append(cold_hold_stats)
    if return_hold_stats is not None:
        stages.append(return_hold_stats)

    total_work_by_system = float(sum(stage["work_by_system"] for stage in stages))
    total_heat_into_system = float(sum(stage["heat_into_system"] for stage in stages))
    total_positive_heat = float(sum(max(stage["heat_into_system"], 0.0) for stage in stages))
    if total_positive_heat <= 0.0:
        total_positive_heat = EPS
    efficiency = float(total_work_by_system / total_positive_heat)
    carnot_bound = 1.0 - (T_COLD / T_HOT)
    final_state = current
    final_trace_distance = float(trace_distance(final_state["rho"], initial["rho"]))
    final_probability_mismatch_abs = float(abs(final_state["p_excited"] - initial["p_excited"]))
    final_free_energy_mismatch = float(final_state["free_energy"] - initial["free_energy"])
    final_internal_energy_mismatch = float(final_state["internal_energy"] - initial["internal_energy"])

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
            "base_hot_steps": BASE_HOT_STEPS,
            "base_cold_steps": BASE_COLD_STEPS,
            "hold_steps_requested": hold_steps_requested,
            "hold_steps_used": hold_steps_used,
            "positive_heat_absorbed": total_positive_heat,
            "total_heat_into_system": total_heat_into_system,
            "total_work_by_system": total_work_by_system,
            "efficiency": efficiency,
            "carnot_bound": carnot_bound,
            "efficiency_distance_to_carnot": float(abs(efficiency - carnot_bound)),
            "final_trace_distance_to_initial": final_trace_distance,
            "final_probability_mismatch_abs": final_probability_mismatch_abs,
            "final_free_energy_mismatch": final_free_energy_mismatch,
            "final_internal_energy_mismatch": final_internal_energy_mismatch,
            "closure_error": float(abs(total_heat_into_system - (sum(stage["delta_u"] for stage in stages) + total_work_by_system))),
        },
    }


def serialize(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"cannot serialize {type(obj)!r}")


def main() -> None:
    baseline = run_policy("baseline_no_extra_hold")
    fixed_return = run_policy(
        "fixed_return_hold_800",
        return_hold={"mode": "fixed", "steps": FIXED_RETURN_HOLD_STEPS},
    )
    adaptive_return = run_policy(
        "adaptive_return_hold_800",
        return_hold={
            "mode": "adaptive",
            "chunk_steps": ADAPTIVE_CHUNK_STEPS,
            "max_steps": ADAPTIVE_BUDGET,
            "tolerance": ADAPTIVE_TOLERANCE,
        },
    )
    fixed_full_chain = run_policy(
        "fixed_full_chain_2000",
        cold_hold={"mode": "fixed", "steps": FIXED_FULL_CHAIN_HOLD_STEPS // 2},
        return_hold={"mode": "fixed", "steps": FIXED_FULL_CHAIN_HOLD_STEPS // 2},
    )
    adaptive_cold_return = run_policy(
        "adaptive_cold_return_800",
        cold_hold={
            "mode": "adaptive",
            "chunk_steps": ADAPTIVE_CHUNK_STEPS,
            "max_steps": ADAPTIVE_BUDGET,
            "tolerance": ADAPTIVE_TOLERANCE,
        },
        return_hold={
            "mode": "adaptive",
            "chunk_steps": ADAPTIVE_CHUNK_STEPS,
            "max_steps": ADAPTIVE_BUDGET,
            "tolerance": ADAPTIVE_TOLERANCE,
        },
    )

    rows = [
        baseline,
        fixed_return,
        adaptive_return,
        fixed_full_chain,
        adaptive_cold_return,
    ]

    baseline_defect = baseline["summary"]["final_trace_distance_to_initial"]
    best_closure = min(rows, key=lambda row: row["summary"]["final_trace_distance_to_initial"])
    best_efficiency = max(rows, key=lambda row: row["summary"]["efficiency"])
    adaptive_return_saved = fixed_return["summary"]["hold_steps_used"] > adaptive_return["summary"]["hold_steps_used"]
    adaptive_full_saved = fixed_full_chain["summary"]["hold_steps_used"] > adaptive_cold_return["summary"]["hold_steps_used"]

    positive = {
        "baseline_has_nonzero_return_defect": {
            "baseline_trace_distance": baseline_defect,
            "pass": baseline_defect > 1e-6,
        },
        "fixed_return_hold_reduces_return_defect_vs_baseline": {
            "baseline_trace_distance": baseline_defect,
            "fixed_return_trace_distance": fixed_return["summary"]["final_trace_distance_to_initial"],
            "pass": fixed_return["summary"]["final_trace_distance_to_initial"] < baseline_defect,
        },
        "adaptive_return_hold_uses_fewer_steps_than_fixed_return_hold": {
            "fixed_steps_used": fixed_return["summary"]["hold_steps_used"],
            "adaptive_steps_used": adaptive_return["summary"]["hold_steps_used"],
            "pass": adaptive_return_saved,
        },
        "fixed_full_chain_has_the_best_closure": {
            "best_closure_policy": best_closure["policy"],
            "best_closure_trace_distance": best_closure["summary"]["final_trace_distance_to_initial"],
            "pass": best_closure["policy"] == "fixed_full_chain_2000",
        },
    }

    negative = {
        "adaptive_hold_does_not_always_match_the_best_fixed_closure": {
            "best_fixed_closure": fixed_full_chain["summary"]["final_trace_distance_to_initial"],
            "best_adaptive_closure": adaptive_cold_return["summary"]["final_trace_distance_to_initial"],
            "pass": adaptive_cold_return["summary"]["final_trace_distance_to_initial"]
            > fixed_full_chain["summary"]["final_trace_distance_to_initial"],
        },
        "adaptive_hold_policies_do_not_match_the_best_efficiency_while_saving_budget": {
            "best_efficiency_policy": best_efficiency["policy"],
            "adaptive_return_efficiency": adaptive_return["summary"]["efficiency"],
            "adaptive_cold_return_efficiency": adaptive_cold_return["summary"]["efficiency"],
            "pass": (
                adaptive_return["summary"]["efficiency"] < best_efficiency["summary"]["efficiency"]
                and adaptive_cold_return["summary"]["efficiency"] < best_efficiency["summary"]["efficiency"]
            ),
        },
        "adaptive_policies_save_budget_relative_to_their_fixed_companions": {
            "fixed_return_steps_used": fixed_return["summary"]["hold_steps_used"],
            "adaptive_return_steps_used": adaptive_return["summary"]["hold_steps_used"],
            "fixed_full_chain_steps_used": fixed_full_chain["summary"]["hold_steps_used"],
            "adaptive_full_chain_steps_used": adaptive_cold_return["summary"]["hold_steps_used"],
            "pass": adaptive_return_saved and adaptive_full_saved,
        },
    }

    boundary = {
        "all_rows_are_valid_density_operators": {
            "pass": all(
                np.allclose(row["final"]["rho"], row["final"]["rho"].T)
                and abs(np.trace(row["final"]["rho"]) - 1.0) < 1e-10
                and np.min(np.linalg.eigvalsh(row["final"]["rho"])) > -1e-10
                for row in rows
            )
        },
        "all_rows_have_finite_statistics": {
            "pass": all(
                np.isfinite(row["summary"]["final_trace_distance_to_initial"])
                and np.isfinite(row["summary"]["efficiency"])
                and np.isfinite(row["summary"]["hold_steps_used"])
                for row in rows
            )
        },
        "policy_grid_has_baseline_fixed_and_adaptive_rows": {
            "row_count": len(rows),
            "pass": len(rows) == 5,
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    result_rows = []
    for row in rows:
        result_rows.append(
            {
                "policy": row["policy"],
                "hold_modes": row["hold_modes"],
                "hold_steps_used": row["summary"]["hold_steps_used"],
                "hold_steps_requested": row["summary"]["hold_steps_requested"],
                "work_by_system": row["summary"]["total_work_by_system"],
                "positive_heat_absorbed": row["summary"]["positive_heat_absorbed"],
                "efficiency": row["summary"]["efficiency"],
                "efficiency_distance_to_carnot": row["summary"]["efficiency_distance_to_carnot"],
                "final_trace_distance_to_initial": row["summary"]["final_trace_distance_to_initial"],
                "final_probability_mismatch_abs": row["summary"]["final_probability_mismatch_abs"],
                "final_free_energy_mismatch": row["summary"]["final_free_energy_mismatch"],
                "final_internal_energy_mismatch": row["summary"]["final_internal_energy_mismatch"],
                "stages": {
                    "hot_iso": {
                        "steps": row["stages"]["hot_iso"]["steps"],
                        "heat_into_system": row["stages"]["hot_iso"]["heat_into_system"],
                        "work_by_system": row["stages"]["hot_iso"]["work_by_system"],
                    },
                    "cold_iso": {
                        "steps": row["stages"]["cold_iso"]["steps"],
                        "heat_into_system": row["stages"]["cold_iso"]["heat_into_system"],
                        "work_by_system": row["stages"]["cold_iso"]["work_by_system"],
                    },
                    "cold_hold": None
                    if row["stages"]["cold_hold"] is None
                    else {
                        "steps_used": row["stages"]["cold_hold"]["steps_used"],
                        "stop_reason": row["stages"]["cold_hold"].get("stop_reason"),
                        "heat_into_system": row["stages"]["cold_hold"]["heat_into_system"],
                        "trace_distance_to_target": row["stages"]["cold_hold"]["trace_distance_to_target"],
                    },
                    "return_hold": None
                    if row["stages"]["return_hold"] is None
                    else {
                        "steps_used": row["stages"]["return_hold"]["steps_used"],
                        "stop_reason": row["stages"]["return_hold"].get("stop_reason"),
                        "heat_into_system": row["stages"]["return_hold"]["heat_into_system"],
                        "trace_distance_to_target": row["stages"]["return_hold"]["trace_distance_to_target"],
                    },
                },
            }
        )

    results = {
        "name": "qit_carnot_hold_policy_companion",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "baseline": result_rows[0],
        "rows": result_rows,
        "summary": {
            "all_pass": all_pass,
            "temperature_pair": {"t_hot": T_HOT, "t_cold": T_COLD},
            "gap_pair": {"gap_high": GAP_HIGH, "gap_hot_low": GAP_HOT_LOW},
            "baseline_final_trace_distance_to_initial": baseline_defect,
            "baseline_efficiency": baseline["summary"]["efficiency"],
            "fixed_return_trace_distance_to_initial": fixed_return["summary"]["final_trace_distance_to_initial"],
            "adaptive_return_trace_distance_to_initial": adaptive_return["summary"]["final_trace_distance_to_initial"],
            "fixed_full_chain_trace_distance_to_initial": fixed_full_chain["summary"]["final_trace_distance_to_initial"],
            "adaptive_cold_return_trace_distance_to_initial": adaptive_cold_return["summary"]["final_trace_distance_to_initial"],
            "best_closure_policy": best_closure["policy"],
            "best_closure_trace_distance_to_initial": best_closure["summary"]["final_trace_distance_to_initial"],
            "best_efficiency_policy": best_efficiency["policy"],
            "best_efficiency": best_efficiency["summary"]["efficiency"],
            "adaptive_return_saved_steps_vs_fixed": adaptive_return_saved,
            "adaptive_cold_return_saved_steps_vs_fixed": adaptive_full_saved,
            "scope_note": (
                "Finite-state QIT Carnot hold-policy companion. It compares baseline "
                "closure defect, fixed-hold policies, and adaptive hold-stop rules "
                "on a qubit two-bath working substance. Use it as a strict companion "
                "surface for the exploratory hold-policy lane."
            ),
        },
    }

    out_path = RESULT_DIR / "qit_carnot_hold_policy_companion_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=serialize) + "\n")
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
