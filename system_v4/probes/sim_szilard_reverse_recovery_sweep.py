#!/usr/bin/env python3
"""
Szilard Reverse/Recovery Sweep
===============================
Explores forward erasure, naive reverse, and designed recovery protocols
across protocol durations for an overdamped double-well memory.

Goal:
- quantify when logical uncertainty is erased
- quantify when it is restored
- compare a naive reverse schedule against a designed recovery schedule
- keep work / heat / closure bookkeeping explicit
"""

from __future__ import annotations

import json
import pathlib

import numpy as np

from stoch_thermo_core import ProtocolStage, simulate_protocol
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Exploratory Szilard reverse/recovery sweep on a finite double-well carrier. "
    "It compares forward erasure, naive reverse, and designed recovery across "
    "protocol durations, while keeping trajectory bookkeeping explicit."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "landauer_erasure",
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

DT = 0.0025
GAMMA = 1.0
TEMPERATURE = 1.0
N_TRAJ = 4000
RNG_SEED = 20260410
LEFT_STATE_THRESHOLD = 0.0
PROTOCOL_STEPS = [60, 120, 240, 420]
MAX_LOGICAL_ENTROPY = float(np.log(2.0))


def binary_entropy_nats(p: float) -> float:
    p = min(max(float(p), 1e-15), 1.0 - 1e-15)
    return float(-(p * np.log(p) + (1.0 - p) * np.log(1.0 - p)))


def double_well_potential(x: np.ndarray, params: dict) -> np.ndarray:
    barrier = float(params.get("barrier", 1.5))
    tilt = float(params.get("tilt", 0.0))
    return barrier * (x * x - 1.0) ** 2 + tilt * x


def double_well_force(x: np.ndarray, params: dict) -> np.ndarray:
    barrier = float(params.get("barrier", 1.5))
    tilt = float(params.get("tilt", 0.0))
    return -(4.0 * barrier * x * (x * x - 1.0) + tilt)


def sample_symmetric_initial_state(n_traj: int, rng: np.random.Generator) -> np.ndarray:
    base = rng.choice([-1.0, 1.0], size=n_traj)
    return base + 0.18 * rng.standard_normal(n_traj)


def sample_left_reset_state(n_traj: int, rng: np.random.Generator) -> np.ndarray:
    return -1.0 + 0.18 * rng.standard_normal(n_traj)


def equilibrium_free_energy(params: dict, x_min: float = -4.5, x_max: float = 4.5, n_grid: int = 4001) -> float:
    xs = np.linspace(x_min, x_max, n_grid)
    us = double_well_potential(xs, params)
    weights = np.exp(-us / TEMPERATURE)
    z = np.trapezoid(weights, xs)
    return float(-TEMPERATURE * np.log(z))


def protocol_erase(total_steps: int, use_tilt: bool = True) -> list[ProtocolStage]:
    split = [max(8, total_steps // 4), max(8, total_steps // 4), max(8, total_steps // 4)]
    split.append(max(8, total_steps - sum(split)))
    target_tilt = 1.8 if use_tilt else 0.0
    return [
        ProtocolStage("lower_barrier", split[0], TEMPERATURE, {"barrier": 1.55, "tilt": 0.0}, {"barrier": 0.05, "tilt": 0.0}),
        ProtocolStage("tilt_left", split[1], TEMPERATURE, {"barrier": 0.05, "tilt": 0.0}, {"barrier": 0.05, "tilt": target_tilt}),
        ProtocolStage("raise_barrier", split[2], TEMPERATURE, {"barrier": 0.05, "tilt": target_tilt}, {"barrier": 1.55, "tilt": target_tilt}),
        ProtocolStage("left_lock_hold", split[3], TEMPERATURE, {"barrier": 1.55, "tilt": target_tilt}, {"barrier": 1.55, "tilt": target_tilt}),
    ]


def protocol_naive_reverse(total_steps: int, use_tilt: bool = True) -> list[ProtocolStage]:
    stages = protocol_erase(total_steps, use_tilt=use_tilt)
    return [
        ProtocolStage(
            name=f"naive_reverse_{stage.name}",
            steps=stage.steps,
            temperature=stage.temperature,
            start_params=stage.end_params,
            end_params=stage.start_params,
        )
        for stage in reversed(stages)
    ]


def protocol_recovery(total_steps: int) -> list[ProtocolStage]:
    split = [max(8, total_steps // 4), max(8, total_steps // 4), max(8, total_steps // 4)]
    split.append(max(8, total_steps - sum(split)))
    return [
        ProtocolStage("release_barrier", split[0], TEMPERATURE, {"barrier": 1.55, "tilt": 1.8}, {"barrier": 0.05, "tilt": 1.8}),
        ProtocolStage("reverse_tilt_washout", split[1], TEMPERATURE, {"barrier": 0.05, "tilt": 1.8}, {"barrier": 0.05, "tilt": -1.8}),
        ProtocolStage("untilt_low_barrier", split[2], TEMPERATURE, {"barrier": 0.05, "tilt": -1.8}, {"barrier": 0.05, "tilt": 0.0}),
        ProtocolStage("raise_barrier_symmetric", split[3], TEMPERATURE, {"barrier": 0.05, "tilt": 0.0}, {"barrier": 1.55, "tilt": 0.0}),
    ]


def run_protocol(mode: str, total_steps: int, seed: int, use_tilt: bool = True) -> dict:
    rng = np.random.default_rng(RNG_SEED + seed)
    if mode == "erase":
        x0 = sample_symmetric_initial_state(N_TRAJ, rng)
        protocol = protocol_erase(total_steps, use_tilt=use_tilt)
        initial_params = {"barrier": 1.55, "tilt": 0.0}
        final_params = {"barrier": 1.55, "tilt": 1.8 if use_tilt else 0.0}
    elif mode == "naive_reverse":
        x0 = sample_left_reset_state(N_TRAJ, rng)
        protocol = protocol_naive_reverse(total_steps, use_tilt=use_tilt)
        initial_params = {"barrier": 1.55, "tilt": 1.8 if use_tilt else 0.0}
        final_params = {"barrier": 1.55, "tilt": 0.0}
    elif mode == "recovery":
        x0 = sample_left_reset_state(N_TRAJ, rng)
        protocol = protocol_recovery(total_steps)
        initial_params = {"barrier": 1.55, "tilt": 1.8}
        final_params = {"barrier": 1.55, "tilt": 0.0}
    else:
        raise ValueError(f"unknown mode: {mode}")

    sim = simulate_protocol(
        x0=x0,
        stages=protocol,
        potential=double_well_potential,
        force=double_well_force,
        dt=DT,
        gamma=GAMMA,
        rng=rng,
    )

    x_final = sim["x_final"]
    p_left_init = float(np.mean(x0 < LEFT_STATE_THRESHOLD))
    p_left_final = float(np.mean(x_final < LEFT_STATE_THRESHOLD))
    logical_entropy_init = binary_entropy_nats(p_left_init)
    logical_entropy_final = binary_entropy_nats(p_left_final)
    entropy_restoration_fraction = logical_entropy_final / MAX_LOGICAL_ENTROPY
    entropy_gap_to_uniform = MAX_LOGICAL_ENTROPY - logical_entropy_final
    info_erased = logical_entropy_init - logical_entropy_final
    mean_work = float(np.mean(sim["total_work"]))
    mean_heat = float(np.mean(sim["total_heat"]))
    mean_delta_u = float(np.mean(sim["total_delta_u"]))
    closure_error = abs(mean_delta_u - (mean_work + mean_heat))
    delta_f = equilibrium_free_energy(final_params) - equilibrium_free_energy(initial_params)

    return {
        "mode": mode,
        "steps": int(total_steps),
        "use_tilt": bool(use_tilt),
        "p_left_init": p_left_init,
        "p_left_final": p_left_final,
        "logical_entropy_init": logical_entropy_init,
        "logical_entropy_final": logical_entropy_final,
        "entropy_restoration_fraction": entropy_restoration_fraction,
        "entropy_gap_to_uniform": entropy_gap_to_uniform,
        "info_erased": info_erased,
        "mean_work": mean_work,
        "mean_heat": mean_heat,
        "mean_delta_u": mean_delta_u,
        "closure_error": closure_error,
        "equilibrium_delta_f": delta_f,
        "landauer_floor": max(delta_f, 0.0),
        "landauer_gap": mean_work - max(delta_f, 0.0),
        "stage_logs": sim["stage_logs"],
    }


def main() -> None:
    rows = []
    by_steps = {}

    for steps in PROTOCOL_STEPS:
        erase = run_protocol("erase", steps, seed=10 + steps, use_tilt=True)
        naive = run_protocol("naive_reverse", steps, seed=20 + steps, use_tilt=True)
        recovery = run_protocol("recovery", steps, seed=30 + steps, use_tilt=True)
        no_tilt = run_protocol("erase", steps, seed=40 + steps, use_tilt=False)

        rows.append(
            {
                "steps": steps,
                "erase_success": erase["p_left_final"],
                "erase_logical_entropy_final": erase["logical_entropy_final"],
                "erase_entropy_restoration_fraction": erase["entropy_restoration_fraction"],
                "erase_work": erase["mean_work"],
                "erase_landauer_gap": erase["landauer_gap"],
                "naive_reverse_final_entropy": naive["logical_entropy_final"],
                "naive_reverse_entropy_restoration_fraction": naive["entropy_restoration_fraction"],
                "naive_reverse_success": naive["p_left_final"],
                "recovery_final_entropy": recovery["logical_entropy_final"],
                "recovery_entropy_restoration_fraction": recovery["entropy_restoration_fraction"],
                "recovery_success": recovery["p_left_final"],
                "no_tilt_success": no_tilt["p_left_final"],
                "no_tilt_work": no_tilt["mean_work"],
                "closure_error_max": max(
                    erase["closure_error"],
                    naive["closure_error"],
                    recovery["closure_error"],
                    no_tilt["closure_error"],
                ),
            }
        )

        by_steps[str(steps)] = {
            "erase": erase,
            "naive_reverse": naive,
            "recovery": recovery,
            "no_tilt": no_tilt,
        }

    # Cross-duration monotonicity / restoration checks.
    erase_successes = [row["erase_success"] for row in rows]
    recovery_entropies = [row["recovery_final_entropy"] for row in rows]
    naive_entropies = [row["naive_reverse_final_entropy"] for row in rows]
    no_tilt_successes = [row["no_tilt_success"] for row in rows]

    positive = {
        "erasure_improves_with_longer_protocols": {
            "first_success": erase_successes[0],
            "last_success": erase_successes[-1],
            "pass": erase_successes[-1] > erase_successes[0] + 0.05,
        },
        "recovery_restores_more_entropy_than_naive_reverse": {
            "mean_naive_entropy": float(np.mean(naive_entropies)),
            "mean_recovery_entropy": float(np.mean(recovery_entropies)),
            "pass": float(np.mean(recovery_entropies)) > float(np.mean(naive_entropies)) + 0.10,
        },
        "no_tilt_control_stays_worse_than_tilted_erasure": {
            "mean_no_tilt_success": float(np.mean(no_tilt_successes)),
            "mean_erase_success": float(np.mean(erase_successes)),
            "pass": float(np.mean(no_tilt_successes)) < float(np.mean(erase_successes)) - 0.05,
        },
    }

    negative = {
        "naive_reverse_is_not_reliable_restoration": {
            "mean_naive_reverse_entropy": float(np.mean(naive_entropies)),
            "pass": float(np.mean(naive_entropies)) < 0.69,
        },
        "recovery_is_not_perfect_restoration": {
            "mean_recovery_entropy": float(np.mean(recovery_entropies)),
            "pass": float(np.mean(recovery_entropies)) < 0.69,
        },
    }

    boundary = {
        "all_protocols_have_closed_work_heat_bookkeeping": {
            "pass": all(
                max(v["closure_error"] for v in by_steps[str(steps)].values()) < 1e-9
                for steps in PROTOCOL_STEPS
            ),
        },
        "all_summary_values_are_finite": {
            "pass": all(
                np.isfinite(value)
                for row in rows
                for value in row.values()
                if isinstance(value, (int, float))
            ),
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    out = {
        "name": "szilard_reverse_recovery_sweep",
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
            "temperature": TEMPERATURE,
            "n_trajectories": N_TRAJ,
            "protocol_steps": PROTOCOL_STEPS,
            "mean_erase_success": float(np.mean(erase_successes)),
            "mean_recovery_entropy": float(np.mean(recovery_entropies)),
            "mean_naive_reverse_entropy": float(np.mean(naive_entropies)),
            "mean_recovery_entropy_restoration_fraction": float(
                np.mean([row["recovery_entropy_restoration_fraction"] for row in rows])
            ),
            "mean_naive_reverse_entropy_restoration_fraction": float(
                np.mean([row["naive_reverse_entropy_restoration_fraction"] for row in rows])
            ),
            "scope_note": (
                "Duration sweep for erase / naive reverse / designed recovery on a finite "
                "double-well memory. Exploratory, not canonical."
            ),
        },
        "rows": rows,
        "by_steps": by_steps,
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "szilard_reverse_recovery_sweep_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
