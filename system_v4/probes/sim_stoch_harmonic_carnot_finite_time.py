#!/usr/bin/env python3
"""
Finite-time stochastic Carnot sidecar on a 1D harmonic working substance.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

from stoch_thermo_core import ProtocolStage, simulate_protocol


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Operational finite-time stochastic Carnot sidecar on a 1D harmonic working "
    "substance. It exposes explicit hot/cold isothermal legs, adiabatic jumps, "
    "forward and reverse modes, and fast-vs-slow dissipation without claiming a "
    "runtime-engine realization."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "stochastic_thermodynamics",
    "carnot_cycle",
]

PRIMARY_LEGO_IDS = [
    "stochastic_thermodynamics",
    "carnot_cycle",
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

DT = 0.003
GAMMA = 1.0
N_TRAJ = 3500
FAST_STEPS = 90
SLOW_STEPS = 520
QUASISTATIC_STEPS = 5000
T_HOT = 2.0
T_COLD = 1.0
K_HIGH = 4.0
K_HOT_LOW = 1.5
RNG_SEED = 20260410 + 77


def harmonic_potential(x: np.ndarray, params: dict) -> np.ndarray:
    stiffness = float(params["k"])
    return 0.5 * stiffness * x * x


def harmonic_force(x: np.ndarray, params: dict) -> np.ndarray:
    stiffness = float(params["k"])
    return -stiffness * x


def sample_equilibrium(n: int, temperature: float, stiffness: float, rng: np.random.Generator) -> np.ndarray:
    sigma = np.sqrt(temperature / stiffness)
    return sigma * rng.standard_normal(n)


def mean_internal_energy(x: np.ndarray, stiffness: float) -> float:
    return float(np.mean(0.5 * stiffness * x * x))


def harmonic_free_energy(temperature: float, stiffness: float) -> float:
    # Partition function for classical 1D harmonic well up to additive constant.
    return -0.5 * temperature * np.log(2.0 * np.pi * temperature / stiffness)


def adiabatic_jump(x: np.ndarray, k_before: float, k_after: float) -> dict:
    u_before = 0.5 * k_before * x * x
    u_after = 0.5 * k_after * x * x
    dwork = u_after - u_before
    return {
        "x": x.copy(),
        "final_variance": float(np.var(x)),
        "mean_work": float(np.mean(dwork)),
        "mean_heat": 0.0,
        "mean_delta_u": float(np.mean(dwork)),
        "closure_error": 0.0,
    }


def run_isothermal_leg(
    x0: np.ndarray,
    temperature: float,
    k_start: float,
    k_end: float,
    steps: int,
    rng: np.random.Generator,
    label: str,
) -> dict:
    sim = simulate_protocol(
        x0=x0,
        stages=[
            ProtocolStage(
                name=label,
                steps=steps,
                temperature=temperature,
                start_params={"k": k_start},
                end_params={"k": k_end},
            )
        ],
        potential=harmonic_potential,
        force=harmonic_force,
        dt=DT,
        gamma=GAMMA,
        rng=rng,
    )
    return {
        "x": sim["x_final"],
        "final_variance": float(np.var(sim["x_final"])),
        "mean_work": float(np.mean(sim["total_work"])),
        "mean_heat": float(np.mean(sim["total_heat"])),
        "mean_delta_u": float(np.mean(sim["total_delta_u"])),
        "closure_error": abs(float(np.mean(sim["total_delta_u"])) - (float(np.mean(sim["total_work"])) + float(np.mean(sim["total_heat"])))),
        "stage_logs": sim["stage_logs"],
    }


def run_forward_cycle(steps: int, seed_offset: int) -> dict:
    rng = np.random.default_rng(RNG_SEED + seed_offset)
    k_cold_low = K_HOT_LOW * (T_COLD / T_HOT)
    k_cold_high = K_HIGH * (T_COLD / T_HOT)

    x_a = sample_equilibrium(N_TRAJ, T_HOT, K_HIGH, rng)
    initial_variance = float(np.var(x_a))
    initial_internal_energy = mean_internal_energy(x_a, K_HIGH)
    hot_iso = run_isothermal_leg(x_a, T_HOT, K_HIGH, K_HOT_LOW, steps, rng, "hot_isotherm_expansion")
    adiabatic_expand = adiabatic_jump(hot_iso["x"], K_HOT_LOW, k_cold_low)
    cold_iso = run_isothermal_leg(adiabatic_expand["x"], T_COLD, k_cold_low, k_cold_high, steps, rng, "cold_isotherm_compression")
    adiabatic_compress = adiabatic_jump(cold_iso["x"], k_cold_high, K_HIGH)

    q_hot = hot_iso["mean_heat"]
    q_cold = cold_iso["mean_heat"]
    work_on_system = hot_iso["mean_work"] + adiabatic_expand["mean_work"] + cold_iso["mean_work"] + adiabatic_compress["mean_work"]
    work_by_system = -work_on_system
    efficiency = work_by_system / q_hot
    carnot_bound = 1.0 - T_COLD / T_HOT
    final_variance = adiabatic_compress["final_variance"]
    final_internal_energy = mean_internal_energy(adiabatic_compress["x"], K_HIGH)
    cycle_delta_u = (
        hot_iso["mean_delta_u"]
        + adiabatic_expand["mean_delta_u"]
        + cold_iso["mean_delta_u"]
        + adiabatic_compress["mean_delta_u"]
    )

    return {
        "steps_per_isotherm": int(steps),
        "q_hot": float(q_hot),
        "q_cold": float(q_cold),
        "work_on_system": float(work_on_system),
        "work_by_system": float(work_by_system),
        "efficiency": float(efficiency),
        "carnot_bound": float(carnot_bound),
        "initial_variance": initial_variance,
        "final_variance": final_variance,
        "initial_internal_energy": initial_internal_energy,
        "final_internal_energy": final_internal_energy,
        "cycle_delta_u": float(cycle_delta_u),
        "closure_error": float(
            hot_iso["closure_error"] + cold_iso["closure_error"] + adiabatic_expand["closure_error"] + adiabatic_compress["closure_error"]
        ),
        "hot_iso": hot_iso,
        "adiabatic_expand": adiabatic_expand,
        "cold_iso": cold_iso,
        "adiabatic_compress": adiabatic_compress,
    }


def run_reverse_cycle(steps: int, seed_offset: int) -> dict:
    rng = np.random.default_rng(RNG_SEED + seed_offset)
    k_cold_low = K_HOT_LOW * (T_COLD / T_HOT)
    k_cold_high = K_HIGH * (T_COLD / T_HOT)

    x_a = sample_equilibrium(N_TRAJ, T_HOT, K_HIGH, rng)
    initial_variance = float(np.var(x_a))
    initial_internal_energy = mean_internal_energy(x_a, K_HIGH)
    adiabatic_to_cold = adiabatic_jump(x_a, K_HIGH, k_cold_high)
    cold_iso_reverse = run_isothermal_leg(adiabatic_to_cold["x"], T_COLD, k_cold_high, k_cold_low, steps, rng, "cold_isotherm_expansion_reverse")
    adiabatic_to_hot = adiabatic_jump(cold_iso_reverse["x"], k_cold_low, K_HOT_LOW)
    hot_iso_reverse = run_isothermal_leg(adiabatic_to_hot["x"], T_HOT, K_HOT_LOW, K_HIGH, steps, rng, "hot_isotherm_compression_reverse")

    q_cold_absorbed = cold_iso_reverse["mean_heat"]
    q_hot_released = hot_iso_reverse["mean_heat"]
    work_on_system = (
        adiabatic_to_cold["mean_work"]
        + cold_iso_reverse["mean_work"]
        + adiabatic_to_hot["mean_work"]
        + hot_iso_reverse["mean_work"]
    )
    work_by_system = -work_on_system
    work_input = work_on_system
    cop = q_cold_absorbed / work_input
    cop_carnot = T_COLD / (T_HOT - T_COLD)
    final_variance = hot_iso_reverse["final_variance"]
    final_internal_energy = mean_internal_energy(hot_iso_reverse["x"], K_HIGH)
    cycle_delta_u = (
        adiabatic_to_cold["mean_delta_u"]
        + cold_iso_reverse["mean_delta_u"]
        + adiabatic_to_hot["mean_delta_u"]
        + hot_iso_reverse["mean_delta_u"]
    )

    return {
        "steps_per_isotherm": int(steps),
        "q_cold_absorbed": float(q_cold_absorbed),
        "q_hot_released": float(q_hot_released),
        "work_on_system": float(work_on_system),
        "work_by_system": float(work_by_system),
        "work_input": float(work_input),
        "cop": float(cop),
        "cop_carnot": float(cop_carnot),
        "initial_variance": initial_variance,
        "final_variance": final_variance,
        "initial_internal_energy": initial_internal_energy,
        "final_internal_energy": final_internal_energy,
        "cycle_delta_u": float(cycle_delta_u),
        "closure_error": float(
            cold_iso_reverse["closure_error"] + hot_iso_reverse["closure_error"]
            + adiabatic_to_cold["closure_error"] + adiabatic_to_hot["closure_error"]
        ),
        "adiabatic_to_cold": adiabatic_to_cold,
        "cold_iso_reverse": cold_iso_reverse,
        "adiabatic_to_hot": adiabatic_to_hot,
        "hot_iso_reverse": hot_iso_reverse,
    }


def serialize_leg(leg: dict) -> dict:
    out = dict(leg)
    out.pop("x", None)
    return out


def serialize_cycle(cycle: dict) -> dict:
    out = dict(cycle)
    for key in list(out.keys()):
        if isinstance(out[key], dict) and ("mean_work" in out[key] or "stage_logs" in out[key]):
            out[key] = serialize_leg(out[key])
    return out


def main() -> None:
    forward_fast = run_forward_cycle(FAST_STEPS, 1)
    forward_slow = run_forward_cycle(SLOW_STEPS, 2)
    forward_quasistatic = run_forward_cycle(QUASISTATIC_STEPS, 5)
    reverse_fast = run_reverse_cycle(FAST_STEPS, 3)
    reverse_slow = run_reverse_cycle(SLOW_STEPS, 4)
    reverse_quasistatic = run_reverse_cycle(QUASISTATIC_STEPS, 6)

    positive = {
        "slow_forward_cycle_beats_fast_cycle_and_stays_below_carnot": {
            "fast_efficiency": forward_fast["efficiency"],
            "slow_efficiency": forward_slow["efficiency"],
            "carnot_bound": forward_slow["carnot_bound"],
            "pass": (
                forward_slow["efficiency"] > forward_fast["efficiency"]
                and forward_slow["efficiency"] < forward_slow["carnot_bound"] + 1e-9
            ),
        },
        "slow_forward_cycle_has_engine_signatures": {
            "q_hot": forward_slow["q_hot"],
            "q_cold": forward_slow["q_cold"],
            "work_by_system": forward_slow["work_by_system"],
            "pass": forward_slow["q_hot"] > 0.0 and forward_slow["q_cold"] < 0.0 and forward_slow["work_by_system"] > 0.0,
        },
        "quasistatic_forward_cycle_moves_closer_to_carnot_than_slow_cycle": {
            "slow_efficiency": forward_slow["efficiency"],
            "quasistatic_efficiency": forward_quasistatic["efficiency"],
            "carnot_bound": forward_quasistatic["carnot_bound"],
            "pass": (
                abs(forward_quasistatic["efficiency"] - forward_quasistatic["carnot_bound"])
                < abs(forward_slow["efficiency"] - forward_slow["carnot_bound"])
            ),
        },
        "slow_reverse_cycle_has_refrigerator_signatures": {
            "q_cold_absorbed": reverse_slow["q_cold_absorbed"],
            "q_hot_released": reverse_slow["q_hot_released"],
            "work_input": reverse_slow["work_input"],
            "pass": (
                reverse_slow["q_cold_absorbed"] > 0.0
                and reverse_slow["q_hot_released"] < 0.0
                and reverse_slow["work_input"] > 0.0
            ),
        },
        "quasistatic_reverse_cycle_moves_closer_to_carnot_cop_than_slow_cycle": {
            "slow_cop": reverse_slow["cop"],
            "quasistatic_cop": reverse_quasistatic["cop"],
            "carnot_cop": reverse_quasistatic["cop_carnot"],
            "pass": (
                reverse_quasistatic["cop"] > reverse_slow["cop"]
                and reverse_quasistatic["cop"] < reverse_quasistatic["cop_carnot"] + 1e-9
            ),
        },
    }

    negative = {
        "fast_forward_cycle_can_fail_to_operate_as_an_engine": {
            "fast_work_by_system": forward_fast["work_by_system"],
            "fast_efficiency": forward_fast["efficiency"],
            "pass": forward_fast["work_by_system"] <= 0.0 and forward_fast["efficiency"] <= 0.0,
        },
        "fast_reverse_cycle_does_not_saturate_carnot_cop": {
            "fast_cop": reverse_fast["cop"],
            "carnot_cop": reverse_fast["cop_carnot"],
            "pass": reverse_fast["cop"] < reverse_fast["cop_carnot"] - 0.05,
        },
        "slow_finite_time_lane_is_not_yet_the_reversible_limit": {
            "slow_efficiency": forward_slow["efficiency"],
            "reversible_bound": forward_slow["carnot_bound"],
            "slow_cop": reverse_slow["cop"],
            "reversible_cop_bound": reverse_slow["cop_carnot"],
            "pass": (
                abs(forward_slow["efficiency"] - forward_slow["carnot_bound"]) > 1e-2
                and abs(reverse_slow["cop"] - reverse_slow["cop_carnot"]) > 1e-2
            ),
        },
        "quasistatic_forward_cycle_still_has_nonzero_cycle_return_error": {
            "cycle_delta_u": forward_quasistatic["cycle_delta_u"],
            "initial_variance": forward_quasistatic["initial_variance"],
            "final_variance": forward_quasistatic["final_variance"],
            "pass": abs(forward_quasistatic["cycle_delta_u"]) > 1e-3,
        },
    }

    boundary = {
        "bookkeeping_closes_for_forward_and_reverse_cycles": {
            "forward_fast_closure_error": forward_fast["closure_error"],
            "forward_slow_closure_error": forward_slow["closure_error"],
            "reverse_fast_closure_error": reverse_fast["closure_error"],
            "reverse_slow_closure_error": reverse_slow["closure_error"],
            "pass": max(
                forward_fast["closure_error"],
                forward_slow["closure_error"],
                reverse_fast["closure_error"],
                reverse_slow["closure_error"],
                forward_quasistatic["closure_error"],
                reverse_quasistatic["closure_error"],
            ) < 1e-8,
        },
        "all_cycle_statistics_are_finite": {
            "pass": all(
                np.isfinite(v)
                for item in [forward_fast, forward_slow, forward_quasistatic, reverse_fast, reverse_slow, reverse_quasistatic]
                for key, v in item.items()
                if isinstance(v, (int, float))
            ),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    out = {
        "name": "stoch_harmonic_carnot_finite_time",
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
            "t_hot": T_HOT,
            "t_cold": T_COLD,
            "fast_steps": FAST_STEPS,
            "slow_steps": SLOW_STEPS,
            "quasistatic_steps": QUASISTATIC_STEPS,
            "forward_fast_efficiency": forward_fast["efficiency"],
            "forward_slow_efficiency": forward_slow["efficiency"],
            "forward_quasistatic_efficiency": forward_quasistatic["efficiency"],
            "forward_quasistatic_cycle_delta_u": forward_quasistatic["cycle_delta_u"],
            "carnot_bound": forward_slow["carnot_bound"],
            "reverse_fast_cop": reverse_fast["cop"],
            "reverse_slow_cop": reverse_slow["cop"],
            "reverse_quasistatic_cop": reverse_quasistatic["cop"],
            "reverse_quasistatic_cycle_delta_u": reverse_quasistatic["cycle_delta_u"],
            "reverse_carnot_cop": reverse_slow["cop_carnot"],
            "scope_note": (
                "Finite-time stochastic forward/reverse Carnot sidecar on a harmonic working substance; "
                "not a runtime-engine theorem."
            ),
        },
        "cycles": {
            "forward_fast": serialize_cycle(forward_fast),
            "forward_slow": serialize_cycle(forward_slow),
            "forward_quasistatic": serialize_cycle(forward_quasistatic),
            "reverse_fast": serialize_cycle(reverse_fast),
            "reverse_slow": serialize_cycle(reverse_slow),
            "reverse_quasistatic": serialize_cycle(reverse_quasistatic),
        },
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "stoch_harmonic_carnot_finite_time_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
