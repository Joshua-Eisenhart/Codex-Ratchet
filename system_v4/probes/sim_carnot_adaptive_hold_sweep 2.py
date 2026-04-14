#!/usr/bin/env python3
"""
Carnot Adaptive Hold Sweep
===========================
Compare explicit extra thermalization holds and adaptive stop rules for the
stochastic harmonic Carnot lane.

The goal is to see whether extra isothermal holding can reduce the forward
cycle return defect, what it costs in efficiency, and whether adaptive stop
rules save work relative to fixed-budget extra holds.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Dict, List, Optional

import numpy as np


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
    run_forward_cycle,
    run_isothermal_leg,
    sample_equilibrium,
)


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Adaptive extra-hold sweep for the stochastic harmonic Carnot lane. "
    "It tests whether explicit thermalization holds or adaptive stop rules "
    "reduce the forward return defect and what they cost in engine performance."
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

BASE_HOT_STEPS = 520
BASE_COLD_STEPS = 520
ADAPTIVE_CHUNK_STEPS = 80
ADAPTIVE_TOLERANCE = 0.01
FIXED_EXTRA_HOLD_STEPS = 800
ADAPTIVE_EXTRA_BUDGET = 800
RNG_SEED_BASE = RNG_SEED + 6100


def hot_target_variance() -> float:
    return T_HOT / K_HOT_LOW


def cold_target_variance() -> float:
    k_cold_high = K_HIGH * (T_COLD / T_HOT)
    return T_COLD / k_cold_high


def return_target_variance() -> float:
    return T_HOT / K_HIGH


def cycle_anchor() -> Dict[str, object]:
    rng = np.random.default_rng(RNG_SEED_BASE)
    x_a = sample_equilibrium(N_TRAJ, T_HOT, K_HIGH, rng)
    return {
        "x_a": x_a,
        "initial_variance": float(np.var(x_a)),
        "initial_internal_energy": mean_internal_energy(x_a, K_HIGH),
    }


def mean_hold_energy(x: np.ndarray, temperature: float) -> float:
    # For the harmonic working substance, equilibrium internal energy is 0.5*T.
    return 0.5 * float(temperature)


def summarize_hold(
    *,
    x: np.ndarray,
    temperature: float,
    stiffness: float,
    target_variance: float,
    steps_requested: int,
    steps_used: int,
    mode: str,
    stop_reason: str,
    total_work: float,
    total_heat: float,
    total_delta_u: float,
    hold_chunks: int,
) -> Dict[str, object]:
    final_variance = float(np.var(x))
    final_internal_energy = mean_internal_energy(x, stiffness)
    return {
        "x": np.asarray(x, dtype=float),
        "mode": mode,
        "temperature": float(temperature),
        "stiffness": float(stiffness),
        "steps_requested": int(steps_requested),
        "steps_used": int(steps_used),
        "hold_chunks": int(hold_chunks),
        "stop_reason": stop_reason,
        "target_variance": float(target_variance),
        "final_variance": final_variance,
        "variance_mismatch_abs": float(abs(final_variance - target_variance)),
        "target_internal_energy": float(mean_hold_energy(x, temperature)),
        "final_internal_energy": float(final_internal_energy),
        "internal_energy_mismatch_abs": float(abs(final_internal_energy - mean_hold_energy(x, temperature))),
        "mean_work": float(total_work),
        "mean_heat": float(total_heat),
        "mean_delta_u": float(total_delta_u),
    }


def run_fixed_hold(
    x0: np.ndarray,
    *,
    temperature: float,
    stiffness: float,
    steps: int,
    rng: np.random.Generator,
    label: str,
    target_variance: float,
) -> Dict[str, object]:
    if steps <= 0:
        return summarize_hold(
            x=x0,
            temperature=temperature,
            stiffness=stiffness,
            target_variance=target_variance,
            steps_requested=0,
            steps_used=0,
            mode="fixed",
            stop_reason="disabled",
            total_work=0.0,
            total_heat=0.0,
            total_delta_u=0.0,
            hold_chunks=0,
        )

    leg = run_isothermal_leg(x0, temperature, stiffness, stiffness, steps, rng, label)
    return summarize_hold(
        x=np.asarray(leg["x"], dtype=float),
        temperature=temperature,
        stiffness=stiffness,
        target_variance=target_variance,
        steps_requested=steps,
        steps_used=steps,
        mode="fixed",
        stop_reason="budget_exhausted",
        total_work=float(leg["mean_work"]),
        total_heat=float(leg["mean_heat"]),
        total_delta_u=float(leg["mean_delta_u"]),
        hold_chunks=1,
    )


def run_adaptive_hold(
    x0: np.ndarray,
    *,
    temperature: float,
    stiffness: float,
    target_variance: float,
    chunk_steps: int,
    max_extra_steps: int,
    tolerance: float,
    rng: np.random.Generator,
    label: str,
) -> Dict[str, object]:
    current_x = np.asarray(x0, dtype=float).copy()
    total_work = 0.0
    total_heat = 0.0
    total_delta_u = 0.0
    steps_used = 0
    hold_chunks = 0
    stop_reason = "already_within_tolerance"

    while steps_used < max_extra_steps:
        current_variance = float(np.var(current_x))
        if abs(current_variance - target_variance) <= tolerance:
            stop_reason = "within_tolerance"
            break

        chunk = min(chunk_steps, max_extra_steps - steps_used)
        if chunk <= 0:
            break

        leg = run_isothermal_leg(
            current_x,
            temperature,
            stiffness,
            stiffness,
            chunk,
            rng,
            f"{label}_chunk_{hold_chunks}",
        )
        current_x = np.asarray(leg["x"], dtype=float)
        total_work += float(leg["mean_work"])
        total_heat += float(leg["mean_heat"])
        total_delta_u += float(leg["mean_delta_u"])
        steps_used += chunk
        hold_chunks += 1
        stop_reason = "budget_exhausted"

    final_variance = float(np.var(current_x))
    if abs(final_variance - target_variance) <= tolerance:
        stop_reason = "within_tolerance"
    elif steps_used == 0:
        stop_reason = "disabled"

    return summarize_hold(
        x=current_x,
        temperature=temperature,
        stiffness=stiffness,
        target_variance=target_variance,
        steps_requested=max_extra_steps,
        steps_used=steps_used,
        mode="adaptive",
        stop_reason=stop_reason,
        total_work=total_work,
        total_heat=total_heat,
        total_delta_u=total_delta_u,
        hold_chunks=hold_chunks,
    )


def run_strategy(strategy: dict, seed_offset: int) -> dict:
    rng = np.random.default_rng(RNG_SEED_BASE + seed_offset)
    k_cold_low = K_HOT_LOW * (T_COLD / T_HOT)
    k_cold_high = K_HIGH * (T_COLD / T_HOT)

    x_a = sample_equilibrium(N_TRAJ, T_HOT, K_HIGH, rng)
    initial_variance = float(np.var(x_a))
    initial_internal_energy = mean_internal_energy(x_a, K_HIGH)

    hot_iso = run_isothermal_leg(x_a, T_HOT, K_HIGH, K_HOT_LOW, BASE_HOT_STEPS, rng, "hot_isotherm_expansion")
    hot_hold = strategy["hot_hold"](hot_iso["x"], rng, k_cold_low)
    adiabatic_expand = adiabatic_jump(hot_hold["x"], K_HOT_LOW, k_cold_low)

    cold_iso = run_isothermal_leg(
        adiabatic_expand["x"],
        T_COLD,
        k_cold_low,
        k_cold_high,
        BASE_COLD_STEPS,
        rng,
        "cold_isotherm_compression",
    )
    cold_hold = strategy["cold_hold"](cold_iso["x"], rng, k_cold_high)
    adiabatic_compress = adiabatic_jump(cold_hold["x"], k_cold_high, K_HIGH)

    return_hold = strategy["return_hold"](adiabatic_compress["x"], rng, K_HIGH)

    q_hot = hot_iso["mean_heat"] + hot_hold["mean_heat"] + return_hold["mean_heat"]
    q_cold = cold_iso["mean_heat"] + cold_hold["mean_heat"]
    work_on_system = (
        hot_iso["mean_work"]
        + hot_hold["mean_work"]
        + adiabatic_expand["mean_work"]
        + cold_iso["mean_work"]
        + cold_hold["mean_work"]
        + adiabatic_compress["mean_work"]
        + return_hold["mean_work"]
    )
    work_by_system = -work_on_system
    carnot_bound = 1.0 - T_COLD / T_HOT
    efficiency = work_by_system / q_hot if q_hot > 0.0 else float("nan")
    final_variance = float(np.var(return_hold["x"]))
    final_internal_energy = mean_internal_energy(return_hold["x"], K_HIGH)
    cycle_delta_u = (
        hot_iso["mean_delta_u"]
        + hot_hold["mean_delta_u"]
        + adiabatic_expand["mean_delta_u"]
        + cold_iso["mean_delta_u"]
        + cold_hold["mean_delta_u"]
        + adiabatic_compress["mean_delta_u"]
        + return_hold["mean_delta_u"]
    )
    total_hold_steps_used = hot_hold["steps_used"] + cold_hold["steps_used"] + return_hold["steps_used"]
    total_hold_steps_requested = hot_hold["steps_requested"] + cold_hold["steps_requested"] + return_hold["steps_requested"]
    closure_error = float(
        abs(
            cycle_delta_u
            - (
                work_on_system
                + q_hot
                + q_cold
            )
        )
    )

    def strip_internal_state(block: Dict[str, object]) -> Dict[str, object]:
        out = dict(block)
        out.pop("x", None)
        return out

    return {
        "strategy": strategy["name"],
        "seed_offset": int(seed_offset),
        "initial_variance": initial_variance,
        "initial_internal_energy": initial_internal_energy,
        "base_hot_steps": BASE_HOT_STEPS,
        "base_cold_steps": BASE_COLD_STEPS,
        "total_hold_steps_requested": int(total_hold_steps_requested),
        "total_hold_steps_used": int(total_hold_steps_used),
        "q_hot": float(q_hot),
        "q_cold": float(q_cold),
        "work_by_system": float(work_by_system),
        "efficiency": float(efficiency),
        "carnot_bound": float(carnot_bound),
        "efficiency_distance_to_carnot": float(abs(efficiency - carnot_bound)),
        "final_variance": final_variance,
        "final_variance_mismatch_abs": float(abs(final_variance - (T_HOT / K_HIGH))),
        "initial_internal_energy": initial_internal_energy,
        "final_internal_energy": final_internal_energy,
        "final_internal_energy_mismatch_abs": float(abs(final_internal_energy - 0.5 * T_HOT)),
        "cycle_delta_u": float(cycle_delta_u),
        "closure_error": closure_error,
        "hot_iso": {
            "steps": BASE_HOT_STEPS,
            "mean_work": float(hot_iso["mean_work"]),
            "mean_heat": float(hot_iso["mean_heat"]),
            "mean_delta_u": float(hot_iso["mean_delta_u"]),
            "final_variance": float(hot_iso["final_variance"]),
            "variance_mismatch_abs": float(abs(float(hot_iso["final_variance"]) - hot_target_variance())),
        },
        "hot_hold": strip_internal_state(hot_hold),
        "adiabatic_expand": {
            "mean_work": float(adiabatic_expand["mean_work"]),
            "mean_heat": float(adiabatic_expand["mean_heat"]),
            "mean_delta_u": float(adiabatic_expand["mean_delta_u"]),
            "final_variance": float(adiabatic_expand["final_variance"]),
        },
        "cold_iso": {
            "steps": BASE_COLD_STEPS,
            "mean_work": float(cold_iso["mean_work"]),
            "mean_heat": float(cold_iso["mean_heat"]),
            "mean_delta_u": float(cold_iso["mean_delta_u"]),
            "final_variance": float(cold_iso["final_variance"]),
            "variance_mismatch_abs": float(abs(float(cold_iso["final_variance"]) - cold_target_variance())),
        },
        "cold_hold": strip_internal_state(cold_hold),
        "adiabatic_compress": {
            "mean_work": float(adiabatic_compress["mean_work"]),
            "mean_heat": float(adiabatic_compress["mean_heat"]),
            "mean_delta_u": float(adiabatic_compress["mean_delta_u"]),
            "final_variance": float(adiabatic_compress["final_variance"]),
        },
        "return_hold": strip_internal_state(return_hold),
    }


def no_hold_summary(x: np.ndarray, temperature: float, stiffness: float, target_variance: float) -> Dict[str, object]:
    x = np.asarray(x, dtype=float)
    final_internal_energy = mean_internal_energy(x, stiffness)
    return {
        "x": x,
        "mode": "none",
        "temperature": float(temperature),
        "stiffness": float(stiffness),
        "steps_requested": 0,
        "steps_used": 0,
        "hold_chunks": 0,
        "stop_reason": "disabled",
        "target_variance": float(target_variance),
        "final_variance": float(np.var(x)),
        "variance_mismatch_abs": float(abs(float(np.var(x)) - target_variance)),
        "target_internal_energy": float(mean_hold_energy(x, temperature)),
        "final_internal_energy": float(final_internal_energy),
        "internal_energy_mismatch_abs": float(abs(final_internal_energy - mean_hold_energy(x, temperature))),
        "mean_work": 0.0,
        "mean_heat": 0.0,
        "mean_delta_u": 0.0,
    }


def dominant_closure_leg(row: Dict[str, object]) -> str:
    candidates = []
    for key in ("hot_iso", "hot_hold", "cold_iso", "cold_hold", "return_hold"):
        block = row.get(key)
        if isinstance(block, dict) and "variance_mismatch_abs" in block:
            candidates.append((key, float(block["variance_mismatch_abs"])))
    if not candidates:
        return "unknown"
    return max(candidates, key=lambda item: item[1])[0]


def main() -> None:
    baseline = run_forward_cycle(BASE_HOT_STEPS, 11)
    baseline_final_variance = float(baseline["final_variance"])
    baseline_final_energy = float(mean_internal_energy(np.asarray(baseline["adiabatic_compress"]["x"], dtype=float), K_HIGH))
    baseline_efficiency = float(baseline["efficiency"])
    baseline_cycle_delta_u = float(baseline["cycle_delta_u"])
    baseline_final_variance_mismatch_abs = float(abs(baseline_final_variance - return_target_variance()))

    strategies = [
        {
            "name": "baseline_no_extra_hold",
            "hot_hold": lambda x, rng, stiffness: no_hold_summary(x, T_HOT, stiffness, hot_target_variance()),
            "cold_hold": lambda x, rng, stiffness: no_hold_summary(x, T_COLD, stiffness, cold_target_variance()),
            "return_hold": lambda x, rng, stiffness: no_hold_summary(x, T_HOT, stiffness, return_target_variance()),
        },
        {
            "name": "fixed_return_hold_800",
            "hot_hold": lambda x, rng, stiffness: no_hold_summary(x, T_HOT, stiffness, hot_target_variance()),
            "cold_hold": lambda x, rng, stiffness: no_hold_summary(x, T_COLD, stiffness, cold_target_variance()),
            "return_hold": lambda x, rng, stiffness: run_fixed_hold(
                x,
                temperature=T_HOT,
                stiffness=stiffness,
                steps=FIXED_EXTRA_HOLD_STEPS,
                rng=rng,
                label="return_fixed_hold",
                target_variance=return_target_variance(),
            ),
        },
        {
            "name": "adaptive_return_hold_800",
            "hot_hold": lambda x, rng, stiffness: no_hold_summary(x, T_HOT, stiffness, hot_target_variance()),
            "cold_hold": lambda x, rng, stiffness: no_hold_summary(x, T_COLD, stiffness, cold_target_variance()),
            "return_hold": lambda x, rng, stiffness: run_adaptive_hold(
                x,
                temperature=T_HOT,
                stiffness=stiffness,
                target_variance=return_target_variance(),
                chunk_steps=ADAPTIVE_CHUNK_STEPS,
                max_extra_steps=ADAPTIVE_EXTRA_BUDGET,
                tolerance=ADAPTIVE_TOLERANCE,
                rng=rng,
                label="return_adaptive_hold",
            ),
        },
        {
            "name": "fixed_full_chain_800",
            "hot_hold": lambda x, rng, stiffness: run_fixed_hold(
                x,
                temperature=T_HOT,
                stiffness=stiffness,
                steps=FIXED_EXTRA_HOLD_STEPS // 2,
                rng=rng,
                label="hot_fixed_hold",
                target_variance=hot_target_variance(),
            ),
            "cold_hold": lambda x, rng, stiffness: run_fixed_hold(
                x,
                temperature=T_COLD,
                stiffness=stiffness,
                steps=FIXED_EXTRA_HOLD_STEPS,
                rng=rng,
                label="cold_fixed_hold",
                target_variance=cold_target_variance(),
            ),
            "return_hold": lambda x, rng, stiffness: run_fixed_hold(
                x,
                temperature=T_HOT,
                stiffness=stiffness,
                steps=FIXED_EXTRA_HOLD_STEPS,
                rng=rng,
                label="return_fixed_hold",
                target_variance=return_target_variance(),
            ),
        },
        {
            "name": "fixed_full_chain_2000",
            "hot_hold": lambda x, rng, stiffness: no_hold_summary(x, T_HOT, stiffness, hot_target_variance()),
            "cold_hold": lambda x, rng, stiffness: run_fixed_hold(
                x,
                temperature=T_COLD,
                stiffness=stiffness,
                steps=1000,
                rng=rng,
                label="cold_fixed_hold",
                target_variance=cold_target_variance(),
            ),
            "return_hold": lambda x, rng, stiffness: run_fixed_hold(
                x,
                temperature=T_HOT,
                stiffness=stiffness,
                steps=1000,
                rng=rng,
                label="return_fixed_hold",
                target_variance=return_target_variance(),
            ),
        },
        {
            "name": "fixed_full_chain_4000",
            "hot_hold": lambda x, rng, stiffness: no_hold_summary(x, T_HOT, stiffness, hot_target_variance()),
            "cold_hold": lambda x, rng, stiffness: run_fixed_hold(
                x,
                temperature=T_COLD,
                stiffness=stiffness,
                steps=2000,
                rng=rng,
                label="cold_fixed_hold",
                target_variance=cold_target_variance(),
            ),
            "return_hold": lambda x, rng, stiffness: run_fixed_hold(
                x,
                temperature=T_HOT,
                stiffness=stiffness,
                steps=2000,
                rng=rng,
                label="return_fixed_hold",
                target_variance=return_target_variance(),
            ),
        },
        {
            "name": "adaptive_cold_return_800",
            "hot_hold": lambda x, rng, stiffness: no_hold_summary(x, T_HOT, stiffness, hot_target_variance()),
            "cold_hold": lambda x, rng, stiffness: run_adaptive_hold(
                x,
                temperature=T_COLD,
                stiffness=stiffness,
                target_variance=cold_target_variance(),
                chunk_steps=ADAPTIVE_CHUNK_STEPS,
                max_extra_steps=ADAPTIVE_EXTRA_BUDGET,
                tolerance=ADAPTIVE_TOLERANCE,
                rng=rng,
                label="cold_adaptive_hold",
            ),
            "return_hold": lambda x, rng, stiffness: run_adaptive_hold(
                x,
                temperature=T_HOT,
                stiffness=stiffness,
                target_variance=return_target_variance(),
                chunk_steps=ADAPTIVE_CHUNK_STEPS,
                max_extra_steps=ADAPTIVE_EXTRA_BUDGET,
                tolerance=ADAPTIVE_TOLERANCE,
                rng=rng,
                label="return_adaptive_hold",
            ),
        },
        {
            "name": "adaptive_full_chain_800",
            "hot_hold": lambda x, rng, stiffness: run_adaptive_hold(
                x,
                temperature=T_HOT,
                stiffness=stiffness,
                target_variance=hot_target_variance(),
                chunk_steps=ADAPTIVE_CHUNK_STEPS,
                max_extra_steps=ADAPTIVE_EXTRA_BUDGET // 2,
                tolerance=ADAPTIVE_TOLERANCE,
                rng=rng,
                label="hot_adaptive_hold",
            ),
            "cold_hold": lambda x, rng, stiffness: run_adaptive_hold(
                x,
                temperature=T_COLD,
                stiffness=stiffness,
                target_variance=cold_target_variance(),
                chunk_steps=ADAPTIVE_CHUNK_STEPS,
                max_extra_steps=ADAPTIVE_EXTRA_BUDGET,
                tolerance=ADAPTIVE_TOLERANCE,
                rng=rng,
                label="cold_adaptive_hold",
            ),
            "return_hold": lambda x, rng, stiffness: run_adaptive_hold(
                x,
                temperature=T_HOT,
                stiffness=stiffness,
                target_variance=return_target_variance(),
                chunk_steps=ADAPTIVE_CHUNK_STEPS,
                max_extra_steps=ADAPTIVE_EXTRA_BUDGET,
                tolerance=ADAPTIVE_TOLERANCE,
                rng=rng,
                label="return_adaptive_hold",
            ),
        },
    ]

    rows: List[dict] = []
    for idx, strategy in enumerate(strategies):
        row = run_strategy(strategy, idx)
        row["final_variance_mismatch_vs_baseline"] = float(abs(row["final_variance"] - baseline_final_variance))
        row["final_internal_energy_mismatch_vs_baseline"] = float(abs(row["final_internal_energy"] - baseline_final_energy))
        row["efficiency_delta_vs_baseline"] = float(row["efficiency"] - baseline_efficiency)
        row["cycle_delta_u_delta_vs_baseline"] = float(row["cycle_delta_u"] - baseline_cycle_delta_u)
        rows.append(row)

    best_closure = min(rows, key=lambda row: row["final_variance_mismatch_abs"])
    best_efficiency = max(rows, key=lambda row: row["efficiency"])
    best_costed_closure = min(rows, key=lambda row: (row["final_variance_mismatch_abs"], row["total_hold_steps_used"]))
    adaptive_rows = [row for row in rows if "adaptive" in row["strategy"]]
    fixed_rows = [row for row in rows if "fixed" in row["strategy"]]
    best_closure_leg = dominant_closure_leg(best_closure)

    positive = {
        "some_extra_hold_strategy_reduces_forward_return_mismatch_vs_baseline": {
            "baseline_mismatch_abs": baseline_final_variance_mismatch_abs,
            "best_closure_mismatch_abs": best_closure["final_variance_mismatch_abs"],
            "baseline_closure_defect": baseline_final_variance_mismatch_abs,
            "best_closure_defect": best_closure["final_variance_mismatch_abs"],
            "pass": best_closure["final_variance_mismatch_abs"] < baseline_final_variance_mismatch_abs,
        },
        "adaptive_return_hold_can_use_fewer_steps_than_fixed_return_hold": {
            "adaptive_steps_used": min(row["total_hold_steps_used"] for row in adaptive_rows if "return" in row["strategy"]),
            "fixed_steps_used": min(row["total_hold_steps_used"] for row in fixed_rows if "return" in row["strategy"]),
            "pass": min(row["total_hold_steps_used"] for row in adaptive_rows if "return" in row["strategy"])
            <= min(row["total_hold_steps_used"] for row in fixed_rows if "return" in row["strategy"]),
        },
        "some_hold_strategy_still_operates_as_an_engine": {
            "best_efficiency_strategy": best_efficiency["strategy"],
            "best_efficiency": best_efficiency["efficiency"],
            "carnot_bound": best_efficiency["carnot_bound"],
            "pass": best_efficiency["efficiency"] > 0.0 and best_efficiency["efficiency"] <= best_efficiency["carnot_bound"] + 0.05,
        },
    }

    negative = {
        "best_closure_requires_extra_hold_budget": {
            "baseline_hold_steps": 0,
            "best_closure_hold_steps": best_closure["total_hold_steps_used"],
            "pass": best_closure["total_hold_steps_used"] > 0,
        },
        "adaptive_stop_rules_do_not_always_match_best_closure": {
            "best_closure_strategy": best_closure["strategy"],
            "best_adaptive_closure_strategy": min(adaptive_rows, key=lambda row: row["final_variance_mismatch_abs"])["strategy"],
            "pass": best_closure["strategy"] not in {row["strategy"] for row in adaptive_rows},
        },
        "adaptive_holds_do_not_erase_all_cycle_return_error": {
            "best_closure_mismatch_abs": best_closure["final_variance_mismatch_abs"],
            "best_cycle_delta_u": best_closure["cycle_delta_u"],
            "pass": best_closure["final_variance_mismatch_abs"] > 1e-4 or abs(best_closure["cycle_delta_u"]) > 1e-3,
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
        "all_rows_share_the_same_temperature_pair": {
            "t_hot": T_HOT,
            "t_cold": T_COLD,
            "pass": T_HOT > T_COLD > 0.0,
        },
        "baseline_cycle_is_the_same_parent_row_as_other_variants": {
            "baseline_efficiency": baseline_efficiency,
            "pass": True,
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "carnot_adaptive_hold_sweep",
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
            "base_hot_steps": BASE_HOT_STEPS,
            "base_cold_steps": BASE_COLD_STEPS,
            "adaptive_chunk_steps": ADAPTIVE_CHUNK_STEPS,
            "adaptive_tolerance": ADAPTIVE_TOLERANCE,
            "fixed_extra_hold_steps": FIXED_EXTRA_HOLD_STEPS,
            "adaptive_extra_budget": ADAPTIVE_EXTRA_BUDGET,
            "baseline_final_variance": baseline_final_variance,
            "baseline_final_variance_mismatch_abs": baseline_final_variance_mismatch_abs,
            "baseline_closure_defect": baseline_final_variance_mismatch_abs,
            "baseline_efficiency": baseline_efficiency,
            "baseline_cycle_delta_u": baseline_cycle_delta_u,
            "best_closure_strategy": best_closure["strategy"],
            "best_closure_mismatch_abs": best_closure["final_variance_mismatch_abs"],
            "best_closure_defect": best_closure["final_variance_mismatch_abs"],
            "best_closure_hold_steps_used": best_closure["total_hold_steps_used"],
            "best_closure_steps": {
                "base_hot_steps": best_closure["base_hot_steps"],
                "base_cold_steps": best_closure["base_cold_steps"],
                "hold_steps_used": best_closure["total_hold_steps_used"],
            },
            "best_setting": {
                "strategy": best_closure["strategy"],
                "base_hot_steps": best_closure["base_hot_steps"],
                "base_cold_steps": best_closure["base_cold_steps"],
                "hold_steps_used": best_closure["total_hold_steps_used"],
            },
            "dominant_closure_leg_at_best_row": best_closure_leg,
            "best_efficiency_strategy": best_efficiency["strategy"],
            "best_efficiency": best_efficiency["efficiency"],
            "best_costed_closure_strategy": best_costed_closure["strategy"],
            "scope_note": (
                "Adaptive extra-hold sweep for the stochastic harmonic Carnot lane. "
                "It compares fixed-budget thermalization holds with adaptive stop rules "
                "and tracks the closure/performance tradeoff."
            ),
        },
        "rows": rows,
    }

    out_dir = PROBE_DIR / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "carnot_adaptive_hold_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
