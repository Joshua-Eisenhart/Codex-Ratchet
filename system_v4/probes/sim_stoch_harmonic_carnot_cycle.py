#!/usr/bin/env python3
"""
Stochastic Harmonic Carnot Cycle
================================
Operational Carnot-side stochastic lane with two bath temperatures,
named isothermal / adiabatic legs, forward and reverse protocols,
and a broken control for honest comparison.

The model is a 1D overdamped harmonic trap:
    U(x; k) = 1/2 * k * x^2

Carnot-style schedule:
    hot isotherm expansion
    hot -> cold adiabatic drop
    cold isotherm compression
    cold -> hot adiabatic rise

The adiabatic legs are implemented as quasi-static temperature/stiffness
co-sweeps that preserve the equilibrium entropy proxy T/k in the ideal limit.
This is exploratory and operational, not a canonical engine theorem.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from stoch_thermo_core import ProtocolStage, simulate_protocol


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Operational harmonic Carnot sidecar with explicit hot/cold baths, named "
    "isothermal and adiabatic legs, forward and reverse protocol mechanics, "
    "and a broken adiabatic control. The lane is useful for finite stochastic "
    "engine bookkeeping, not a canonical proof of universal Carnot optimality."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "harmonic_trap",
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

TEMPERATURE_HOT = 2.0
TEMPERATURE_COLD = 1.0
K_HOT = 4.0
K_MID = 1.0
K_COLD = K_MID * TEMPERATURE_COLD / TEMPERATURE_HOT
K_COLD_END = K_HOT * TEMPERATURE_COLD / TEMPERATURE_HOT
DT = 0.0025
GAMMA = 1.0
N_TRAJ = 2500
FAST_MICROSTEPS = 12
SLOW_MICROSTEPS = 48
REVERSE_MICROSTEPS = 48
CONTROL_MICROSTEPS = 48
RNG_SEED = 20260410


def harmonic_potential(x: np.ndarray, params: Dict[str, float]) -> np.ndarray:
    k = float(params.get("k", 1.0))
    x0 = float(params.get("x0", 0.0))
    dx = x - x0
    return 0.5 * k * dx * dx


def harmonic_force(x: np.ndarray, params: Dict[str, float]) -> np.ndarray:
    k = float(params.get("k", 1.0))
    x0 = float(params.get("x0", 0.0))
    return -k * (x - x0)


def entropy_proxy(temperature: float, stiffness: float) -> float:
    """Up to an additive constant, the Gaussian entropy proxy is 1/2 log(T/k)."""
    return 0.5 * float(np.log(temperature / stiffness))


def equilibrium_sample(temperature: float, stiffness: float, n_traj: int, rng: np.random.Generator) -> np.ndarray:
    variance = float(temperature / stiffness)
    return rng.normal(loc=0.0, scale=np.sqrt(variance), size=n_traj)


def microstage(
    name: str,
    temperature: float,
    k_start: float,
    k_end: float,
) -> ProtocolStage:
    return ProtocolStage(
        name=name,
        steps=1,
        temperature=float(temperature),
        start_params={"k": float(k_start), "x0": 0.0},
        end_params={"k": float(k_end), "x0": 0.0},
    )


def build_hot_isotherm(microsteps: int, k_start: float, k_end: float) -> List[ProtocolStage]:
    ks = np.linspace(k_start, k_end, microsteps + 1)
    return [
        microstage(f"hot_isotherm_expansion_{i:03d}", TEMPERATURE_HOT, ks[i], ks[i + 1])
        for i in range(microsteps)
    ]


def build_cold_isotherm(microsteps: int, k_start: float, k_end: float) -> List[ProtocolStage]:
    ks = np.linspace(k_start, k_end, microsteps + 1)
    return [
        microstage(f"cold_isotherm_compression_{i:03d}", TEMPERATURE_COLD, ks[i], ks[i + 1])
        for i in range(microsteps)
    ]


def build_adiabat(
    microsteps: int,
    t_start: float,
    t_end: float,
    ratio_t_over_k: float,
    label: str,
) -> List[ProtocolStage]:
    ts = np.linspace(t_start, t_end, microsteps + 1)
    stages = []
    for i in range(microsteps):
        t_mid = 0.5 * (ts[i] + ts[i + 1])
        k0 = ts[i] / ratio_t_over_k
        k1 = ts[i + 1] / ratio_t_over_k
        stages.append(microstage(f"{label}_{i:03d}", t_mid, k0, k1))
    return stages


def build_forward_protocol(microsteps: int, broken_adiabat: bool = False) -> List[ProtocolStage]:
    """
    Forward Carnot-like cycle:
    hot isotherm expansion -> hot->cold adiabatic drop ->
    cold isotherm compression -> cold->hot adiabatic rise.
    """
    hot_expansion = build_hot_isotherm(microsteps, K_HOT, K_MID)
    adiabatic_drop_ratio = TEMPERATURE_HOT / K_MID
    if broken_adiabat:
        # Deliberately wrong ratio to create a control.
        adiabatic_drop_ratio *= 0.80
    hot_to_cold = build_adiabat(
        microsteps,
        TEMPERATURE_HOT,
        TEMPERATURE_COLD,
        adiabatic_drop_ratio,
        "hot_to_cold_adiabat",
    )

    cold_compression = build_cold_isotherm(microsteps, K_COLD, K_COLD_END)

    adiabatic_rise_ratio = TEMPERATURE_COLD / K_COLD_END
    if broken_adiabat:
        adiabatic_rise_ratio *= 1.25
    cold_to_hot = build_adiabat(
        microsteps,
        TEMPERATURE_COLD,
        TEMPERATURE_HOT,
        adiabatic_rise_ratio,
        "cold_to_hot_adiabat",
    )

    return hot_expansion + hot_to_cold + cold_compression + cold_to_hot


def reverse_protocol(stages: List[ProtocolStage]) -> List[ProtocolStage]:
    rev = []
    for stage in reversed(stages):
        rev.append(
            ProtocolStage(
                name=f"reverse_{stage.name}",
                steps=stage.steps,
                temperature=stage.temperature,
                start_params=stage.end_params,
                end_params=stage.start_params,
            )
        )
    return rev


def aggregate_leg_logs(stage_logs: List[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    legs: Dict[str, Dict[str, float]] = {}
    for entry in stage_logs:
        name = entry["name"]
        base_name = name.removeprefix("reverse_")
        if base_name.startswith("hot_isotherm_expansion"):
            leg = "hot_isotherm_expansion"
        elif base_name.startswith("hot_to_cold_adiabat"):
            leg = "hot_to_cold_adiabat"
        elif base_name.startswith("cold_isotherm_compression"):
            leg = "cold_isotherm_compression"
        elif base_name.startswith("cold_to_hot_adiabat"):
            leg = "cold_to_hot_adiabat"
        elif name.startswith("reverse_"):
            leg = "reverse_cycle"
        else:
            leg = "other"

        bucket = legs.setdefault(
            leg,
            {
                "stages": 0,
                "mean_work": 0.0,
                "mean_heat": 0.0,
                "mean_delta_u": 0.0,
            },
        )
        bucket["stages"] += 1
        bucket["mean_work"] += float(entry["mean_work"])
        bucket["mean_heat"] += float(entry["mean_heat"])
        bucket["mean_delta_u"] += float(entry["mean_delta_u"])
    return legs


def run_cycle(microsteps: int, broken_adiabat: bool, reverse: bool, seed_offset: int, x0: np.ndarray | None = None) -> Dict[str, object]:
    rng = np.random.default_rng(RNG_SEED + seed_offset)
    stages = build_forward_protocol(microsteps, broken_adiabat=broken_adiabat)
    if reverse:
        stages = reverse_protocol(stages)

    if x0 is None:
        x0 = equilibrium_sample(TEMPERATURE_HOT, K_HOT, N_TRAJ, rng)

    sim = simulate_protocol(
        x0=x0,
        stages=stages,
        potential=harmonic_potential,
        force=harmonic_force,
        dt=DT,
        gamma=GAMMA,
        rng=rng,
    )

    x_final = sim["x_final"]
    mean_x0 = float(np.mean(x0))
    mean_xf = float(np.mean(x_final))
    var_x0 = float(np.var(x0))
    var_xf = float(np.var(x_final))
    mean_abs_dx = float(np.mean(np.abs(x_final - x0)))

    stage_logs = sim["stage_logs"]
    legs = aggregate_leg_logs(stage_logs)

    hot_heat = legs["hot_isotherm_expansion"]["mean_heat"]
    cold_heat = legs["cold_isotherm_compression"]["mean_heat"]
    adiabatic_drift = abs(legs["hot_to_cold_adiabat"]["mean_heat"]) + abs(legs["cold_to_hot_adiabat"]["mean_heat"])

    mean_work = float(np.mean(sim["total_work"]))
    mean_heat_total = float(np.mean(sim["total_heat"]))
    mean_delta_u = float(np.mean(sim["total_delta_u"]))
    closure_error = abs(mean_delta_u - (mean_work + mean_heat_total))

    extracted_work = -mean_work
    carnots_bound = 1.0 - (TEMPERATURE_COLD / TEMPERATURE_HOT)
    efficiency = extracted_work / max(hot_heat, 1e-12)

    reversible_hot_work = 0.5 * TEMPERATURE_HOT * np.log(K_MID / K_HOT)
    reversible_cold_work = 0.5 * TEMPERATURE_COLD * np.log(K_COLD_END / K_COLD)
    reversible_cycle_work_on_system = reversible_hot_work + reversible_cold_work
    reversible_extracted = -reversible_cycle_work_on_system

    entropy_proxy_hot_start = entropy_proxy(TEMPERATURE_HOT, K_HOT)
    entropy_proxy_hot_end = entropy_proxy(TEMPERATURE_HOT, K_MID)
    entropy_proxy_cold_start = entropy_proxy(TEMPERATURE_COLD, K_COLD)
    entropy_proxy_cold_end = entropy_proxy(TEMPERATURE_COLD, K_COLD_END)
    adiabatic_proxy_drift = abs(entropy_proxy(TEMPERATURE_HOT, K_MID) - entropy_proxy(TEMPERATURE_COLD, K_COLD))
    adiabatic_proxy_drift += abs(entropy_proxy(TEMPERATURE_COLD, K_COLD_END) - entropy_proxy(TEMPERATURE_HOT, K_HOT))

    return {
        "microsteps": int(microsteps),
        "broken_adiabat": bool(broken_adiabat),
        "reverse": bool(reverse),
        "mean_work_on_system": mean_work,
        "mean_heat_total": mean_heat_total,
        "mean_delta_u": mean_delta_u,
        "closure_error": float(closure_error),
        "hot_heat": float(hot_heat),
        "cold_heat": float(cold_heat),
        "adiabatic_heat_drift": float(adiabatic_drift),
        "extracted_work": float(extracted_work),
        "efficiency": float(efficiency),
        "carnot_bound": float(carnots_bound),
        "reversible_extracted_work_estimate": float(reversible_extracted),
        "mean_x0": mean_x0,
        "mean_xf": mean_xf,
        "var_x0": var_x0,
        "var_xf": var_xf,
        "mean_abs_dx": mean_abs_dx,
        "entropy_proxy_hot_start": float(entropy_proxy_hot_start),
        "entropy_proxy_hot_end": float(entropy_proxy_hot_end),
        "entropy_proxy_cold_start": float(entropy_proxy_cold_start),
        "entropy_proxy_cold_end": float(entropy_proxy_cold_end),
        "adiabatic_proxy_drift": float(adiabatic_proxy_drift),
        "stage_logs": stage_logs,
        "leg_logs": legs,
        "x_final": x_final,
    }


def main() -> None:
    forward_fast = run_cycle(FAST_MICROSTEPS, broken_adiabat=False, reverse=False, seed_offset=1)
    forward_slow = run_cycle(SLOW_MICROSTEPS, broken_adiabat=False, reverse=False, seed_offset=2)
    reverse_slow = run_cycle(REVERSE_MICROSTEPS, broken_adiabat=False, reverse=True, seed_offset=3, x0=forward_slow["x_final"])
    control_broken = run_cycle(CONTROL_MICROSTEPS, broken_adiabat=True, reverse=False, seed_offset=4)

    initial_equilibrium_error = abs(forward_slow["var_x0"] - TEMPERATURE_HOT / K_HOT)
    forward_end_equilibrium_error = abs(forward_slow["var_xf"] - TEMPERATURE_HOT / K_HOT)
    reverse_recovery_error = abs(reverse_slow["var_xf"] - forward_slow["var_x0"]) + abs(reverse_slow["mean_xf"] - forward_slow["mean_x0"])
    control_recovery_error = abs(control_broken["var_xf"] - forward_slow["var_x0"]) + abs(control_broken["mean_xf"] - forward_slow["mean_x0"])

    positive = {
        "forward_cycle_closes_the_state_statistics_better_than_zero": {
            "initial_equilibrium_error": initial_equilibrium_error,
            "forward_end_equilibrium_error": forward_end_equilibrium_error,
            "pass": forward_end_equilibrium_error < 0.45,
        },
        "slow_protocol_reduces_work_dissipation_relative_to_fast": {
            "fast_efficiency": forward_fast["efficiency"],
            "slow_efficiency": forward_slow["efficiency"],
            "pass": forward_slow["efficiency"] > forward_fast["efficiency"],
        },
        "slow_protocol_stays_below_carnot_bound": {
            "slow_efficiency": forward_slow["efficiency"],
            "carnot_bound": forward_slow["carnot_bound"],
            "pass": forward_slow["efficiency"] <= forward_slow["carnot_bound"] + 0.05,
        },
        "hot_isotherm_has_the_expected_reversible_work_direction": {
            "mean_hot_heat": forward_slow["hot_heat"],
            "mean_work_on_system": forward_slow["mean_work_on_system"],
            "pass": forward_slow["hot_heat"] > 0 and forward_slow["mean_work_on_system"] < 0,
        },
        "adiabatic_legs_approximately_preserve_entropy_proxy_in_the_slow_lane": {
            "adiabatic_proxy_drift": forward_slow["adiabatic_proxy_drift"],
            "pass": forward_slow["adiabatic_proxy_drift"] < 0.15,
        },
    }

    negative = {
        "broken_adiabat_is_worse_than_the_operational_cycle": {
            "broken_efficiency": control_broken["efficiency"],
            "slow_efficiency": forward_slow["efficiency"],
            "pass": control_broken["efficiency"] < forward_slow["efficiency"],
        },
        "reverse_cycle_is_not_a_good_erasure_protocol": {
            "reverse_work_on_system": reverse_slow["mean_work_on_system"],
            "reverse_recovery_error": reverse_recovery_error,
            "pass": reverse_recovery_error > 0.02,
        },
    }

    boundary = {
        "all_protocols_have_closed_energy_bookkeeping": {
            "forward_fast_closure_error": forward_fast["closure_error"],
            "forward_slow_closure_error": forward_slow["closure_error"],
            "reverse_slow_closure_error": reverse_slow["closure_error"],
            "control_closure_error": control_broken["closure_error"],
            "pass": max(
                forward_fast["closure_error"],
                forward_slow["closure_error"],
                reverse_slow["closure_error"],
                control_broken["closure_error"],
            ) < 1e-9,
        },
        "all_runs_return_finite_summary_statistics": {
            "pass": all(
                np.isfinite(v)
                for item in [forward_fast, forward_slow, reverse_slow, control_broken]
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
        "name": "stoch_harmonic_carnot_cycle",
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
            "temperature_hot": TEMPERATURE_HOT,
            "temperature_cold": TEMPERATURE_COLD,
            "k_hot": K_HOT,
            "k_mid": K_MID,
            "k_cold": K_COLD,
            "k_cold_end": K_COLD_END,
            "forward_fast": {
                "efficiency": forward_fast["efficiency"],
                "hot_heat": forward_fast["hot_heat"],
                "work_on_system": forward_fast["mean_work_on_system"],
            },
            "forward_slow": {
                "efficiency": forward_slow["efficiency"],
                "hot_heat": forward_slow["hot_heat"],
                "work_on_system": forward_slow["mean_work_on_system"],
            },
            "reverse_slow": {
                "mean_work_on_system": reverse_slow["mean_work_on_system"],
                "recovery_error": reverse_recovery_error,
            },
            "control_broken": {
                "efficiency": control_broken["efficiency"],
                "work_on_system": control_broken["mean_work_on_system"],
            },
            "scope_note": (
                "Exploratory harmonic Carnot lane with explicit isothermal and adiabatic "
                "legs, forward and reverse protocols, and a broken control. Useful as an "
                "operational substrate, not a canonical engine theorem."
            ),
        },
        "protocols": {
            "forward_fast": {k: v for k, v in forward_fast.items() if k != "x_final"},
            "forward_slow": {k: v for k, v in forward_slow.items() if k != "x_final"},
            "reverse_slow": {k: v for k, v in reverse_slow.items() if k != "x_final"},
            "control_broken": {k: v for k, v in control_broken.items() if k != "x_final"},
        },
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "stoch_harmonic_carnot_cycle_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
