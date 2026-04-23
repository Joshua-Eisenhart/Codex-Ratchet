#!/usr/bin/env python3
"""
Szilard Topology / Entropy Array
================================
Compare ordered-vs-scrambled Szilard-style control across several memory
landscape variants and several readout / entropy families.
"""

from __future__ import annotations

import json
import math
import pathlib

import numpy as np

from stoch_thermo_core import ProtocolStage, simulate_protocol
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Topology and entropy/readout array for a Szilard-style stochastic memory "
    "lane. It compares ordered versus scrambled control across several memory "
    "landscapes and several entropy/readout families."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "landauer_erasure",
    "measurement_feedback",
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
N_TRAJ = 2500
RNG_SEED = 20260410 + 4200
LEFT_THRESHOLD = 0.0
MEASUREMENT_FLIP_PROB = 0.08
MEAS_STEPS = 90
FEEDBACK_STEPS = 120
RESET_STEPS = 120
HOLD_STEPS = 60
X_MIN = -5.0
X_MAX = 5.0
X_GRID = 5001

TOPOLOGIES = {
    "standard_double_well": {
        "barrier_scale": 1.0,
        "shape_scale": 1.0,
        "tilt_scale": 1.0,
        "feedback_tilt": 1.9,
        "reset_tilt": 1.4,
    },
    "steep_double_well": {
        "barrier_scale": 1.6,
        "shape_scale": 1.0,
        "tilt_scale": 1.0,
        "feedback_tilt": 2.2,
        "reset_tilt": 1.7,
    },
    "wide_double_well": {
        "barrier_scale": 0.9,
        "shape_scale": 0.7,
        "tilt_scale": 1.0,
        "feedback_tilt": 1.7,
        "reset_tilt": 1.2,
    },
    "asymmetric_double_well": {
        "barrier_scale": 1.1,
        "shape_scale": 1.0,
        "tilt_scale": 1.25,
        "feedback_tilt": 1.9,
        "reset_tilt": 1.5,
    },
}


def binary_entropy_nats(p: float) -> float:
    p = min(max(float(p), 1e-15), 1.0 - 1e-15)
    return float(-(p * np.log(p) + (1.0 - p) * np.log(1.0 - p)))


def differential_entropy_proxy(x: np.ndarray) -> float:
    var = max(float(np.var(x)), 1e-15)
    return float(0.5 * np.log(2.0 * np.pi * np.e * var))


def potential_fn_factory(config: dict):
    barrier_scale = float(config["barrier_scale"])
    shape_scale = float(config["shape_scale"])
    tilt_scale = float(config["tilt_scale"])

    def potential(x: np.ndarray, params: dict) -> np.ndarray:
        barrier = barrier_scale * float(params.get("barrier", 1.5))
        tilt = tilt_scale * float(params.get("tilt", 0.0))
        y = shape_scale * x
        return barrier * (y * y - 1.0) ** 2 + tilt * x

    def force(x: np.ndarray, params: dict) -> np.ndarray:
        barrier = barrier_scale * float(params.get("barrier", 1.5))
        tilt = tilt_scale * float(params.get("tilt", 0.0))
        y = shape_scale * x
        d_u_dx = 4.0 * barrier * shape_scale * y * (y * y - 1.0) + tilt
        return -d_u_dx

    return potential, force


def equilibrium_free_energy(potential, barrier: float, tilt: float) -> float:
    xs = np.linspace(X_MIN, X_MAX, X_GRID)
    us = potential(xs, {"barrier": barrier, "tilt": tilt})
    weights = np.exp(-us / TEMPERATURE)
    z = np.trapezoid(weights, xs)
    return float(-TEMPERATURE * np.log(z))


def sample_initial_state(rng: np.random.Generator, shape_scale: float) -> np.ndarray:
    centers = rng.choice([-1.0, 1.0], size=N_TRAJ)
    spread = 0.20 / max(shape_scale, 0.5)
    return centers + spread * rng.standard_normal(N_TRAJ)


def measurement_stats(true_bits: np.ndarray, obs_bits: np.ndarray) -> dict:
    true_bits = np.asarray(true_bits, dtype=int)
    obs_bits = np.asarray(obs_bits, dtype=int)
    p_true1 = float(np.mean(true_bits == 1))
    p_obs1 = float(np.mean(obs_bits == 1))
    p11 = float(np.mean((true_bits == 1) & (obs_bits == 1)))
    p10 = float(np.mean((true_bits == 1) & (obs_bits == 0)))
    p01 = float(np.mean((true_bits == 0) & (obs_bits == 1)))
    p00 = float(np.mean((true_bits == 0) & (obs_bits == 0)))
    mi = 0.0
    for pxy, px, py in [
        (p11, p_true1, p_obs1),
        (p10, p_true1, 1.0 - p_obs1),
        (p01, 1.0 - p_true1, p_obs1),
        (p00, 1.0 - p_true1, 1.0 - p_obs1),
    ]:
        if pxy > 0.0:
            mi += pxy * np.log(pxy / (px * py))
    return {
        "accuracy": float(np.mean(true_bits == obs_bits)),
        "mutual_information": float(mi),
    }


def run_branch(
    x0: np.ndarray,
    potential,
    force,
    start_params: dict,
    end_params: dict,
    steps: int,
    rng: np.random.Generator,
):
    stage = ProtocolStage(
        name="branch",
        steps=steps,
        temperature=TEMPERATURE,
        start_params=start_params,
        end_params=end_params,
    )
    return simulate_protocol(
        x0=x0,
        stages=[stage],
        potential=potential,
        force=force,
        dt=DT,
        gamma=GAMMA,
        rng=rng,
    )


def run_protocol(topology_name: str, config: dict, order_name: str, rng_seed: int) -> dict:
    potential, force = potential_fn_factory(config)
    rng = np.random.default_rng(rng_seed)
    x = sample_initial_state(rng, float(config["shape_scale"]))
    true_initial_bits = (x >= LEFT_THRESHOLD).astype(int)
    measurement_record = None
    total_work = np.zeros(N_TRAJ, dtype=float)
    total_heat = np.zeros(N_TRAJ, dtype=float)
    total_delta_u = np.zeros(N_TRAJ, dtype=float)
    mi = None
    acc = None

    def run_stage(x_cur, start_params, end_params, steps):
        sim = simulate_protocol(
            x0=x_cur,
            stages=[ProtocolStage("stage", steps, TEMPERATURE, start_params, end_params)],
            potential=potential,
            force=force,
            dt=DT,
            gamma=GAMMA,
            rng=rng,
        )
        return sim["x_final"], sim["total_work"], sim["total_heat"], sim["total_delta_u"]

    order_steps = {
        "ordered": ["measurement", "feedback", "reset", "hold"],
        "feedback_first": ["feedback", "measurement", "reset", "hold"],
        "measurement_reset_feedback": ["measurement", "reset", "feedback", "hold"],
    }[order_name]

    for stage_name in order_steps:
        if stage_name == "measurement":
            x_before = x.copy()
            x, w, h, du = run_stage(x, {"barrier": 1.55, "tilt": 0.0}, {"barrier": 0.10, "tilt": 0.0}, MEAS_STEPS)
            total_work += w
            total_heat += h
            total_delta_u += du
            sensed = (x >= LEFT_THRESHOLD).astype(int)
            flips = rng.random(N_TRAJ) < MEASUREMENT_FLIP_PROB
            sensed = np.where(flips, 1 - sensed, sensed)
            measurement_record = sensed
            stats = measurement_stats((x_before >= LEFT_THRESHOLD).astype(int), sensed)
            acc = stats["accuracy"]
            mi = stats["mutual_information"]
        elif stage_name == "feedback":
            branch_work = np.zeros(N_TRAJ, dtype=float)
            branch_heat = np.zeros(N_TRAJ, dtype=float)
            branch_du = np.zeros(N_TRAJ, dtype=float)
            x_next = x.copy()
            if measurement_record is None:
                control_bits = rng.integers(0, 2, size=N_TRAJ)
                right_tilt = float(config["feedback_tilt"])
                left_tilt = -float(config["feedback_tilt"])
            else:
                control_bits = measurement_record
                right_tilt = float(config["feedback_tilt"])
                left_tilt = 0.15 * float(config["feedback_tilt"])
            right_mask = control_bits == 1
            left_mask = ~right_mask
            if np.any(right_mask):
                sim = run_branch(
                    x[right_mask],
                    potential,
                    force,
                    {"barrier": 0.10, "tilt": 0.0},
                    {"barrier": 1.55, "tilt": right_tilt},
                    FEEDBACK_STEPS,
                    rng,
                )
                x_next[right_mask] = sim["x_final"]
                branch_work[right_mask] = sim["total_work"]
                branch_heat[right_mask] = sim["total_heat"]
                branch_du[right_mask] = sim["total_delta_u"]
            if np.any(left_mask):
                sim = run_branch(
                    x[left_mask],
                    potential,
                    force,
                    {"barrier": 0.10, "tilt": 0.0},
                    {"barrier": 1.55, "tilt": left_tilt},
                    FEEDBACK_STEPS,
                    rng,
                )
                x_next[left_mask] = sim["x_final"]
                branch_work[left_mask] = sim["total_work"]
                branch_heat[left_mask] = sim["total_heat"]
                branch_du[left_mask] = sim["total_delta_u"]
            x = x_next
            total_work += branch_work
            total_heat += branch_heat
            total_delta_u += branch_du
        elif stage_name == "reset":
            x, w, h, du = run_stage(
                x,
                {"barrier": 1.55, "tilt": 0.15 * float(config["feedback_tilt"])},
                {"barrier": 1.55, "tilt": float(config["reset_tilt"])},
                RESET_STEPS,
            )
            measurement_record = None
            total_work += w
            total_heat += h
            total_delta_u += du
        elif stage_name == "hold":
            x, w, h, du = run_stage(
                x,
                {"barrier": 1.55, "tilt": float(config["reset_tilt"])},
                {"barrier": 1.55, "tilt": float(config["reset_tilt"])},
                HOLD_STEPS,
            )
            total_work += w
            total_heat += h
            total_delta_u += du

    final_left_fraction = float(np.mean(x < LEFT_THRESHOLD))
    logical_entropy = binary_entropy_nats(float(np.mean((x >= LEFT_THRESHOLD).astype(int))))
    spread_entropy = differential_entropy_proxy(x)
    initial_free_energy = equilibrium_free_energy(potential, 1.55, 0.0)
    final_free_energy = equilibrium_free_energy(potential, 1.55, float(config["reset_tilt"]))
    free_energy_gap = float(np.mean(total_work)) - max(final_free_energy - initial_free_energy, 0.0)
    closure_error = abs(float(np.mean(total_delta_u)) - float(np.mean(total_work)) - float(np.mean(total_heat)))

    return {
        "topology": topology_name,
        "order": order_name,
        "final_left_fraction": final_left_fraction,
        "logical_entropy": logical_entropy,
        "spread_entropy_proxy": spread_entropy,
        "measurement_accuracy": acc,
        "measurement_mutual_information": mi,
        "mean_work": float(np.mean(total_work)),
        "mean_heat": float(np.mean(total_heat)),
        "mean_delta_u": float(np.mean(total_delta_u)),
        "free_energy_gap_proxy": free_energy_gap,
        "closure_error": closure_error,
    }


def main() -> None:
    rows = []
    seed = RNG_SEED
    for topology_name, config in TOPOLOGIES.items():
        ordered = run_protocol(topology_name, config, "ordered", seed)
        feedback_first = run_protocol(topology_name, config, "feedback_first", seed + 1)
        measurement_reset_feedback = run_protocol(topology_name, config, "measurement_reset_feedback", seed + 2)
        seed += 10
        best_scrambled = min(feedback_first["logical_entropy"], measurement_reset_feedback["logical_entropy"])
        rows.append(
            {
                "topology": topology_name,
                "ordered_logical_entropy": ordered["logical_entropy"],
                "ordered_spread_entropy_proxy": ordered["spread_entropy_proxy"],
                "ordered_measurement_accuracy": ordered["measurement_accuracy"],
                "ordered_measurement_mi": ordered["measurement_mutual_information"],
                "ordered_free_energy_gap_proxy": ordered["free_energy_gap_proxy"],
                "feedback_first_logical_entropy": feedback_first["logical_entropy"],
                "measurement_reset_feedback_logical_entropy": measurement_reset_feedback["logical_entropy"],
                "best_scrambled_logical_entropy": best_scrambled,
                "ordering_margin": float(best_scrambled - ordered["logical_entropy"]),
                "closure_error_max": max(
                    ordered["closure_error"],
                    feedback_first["closure_error"],
                    measurement_reset_feedback["closure_error"],
                ),
            }
        )

    best_row = max(rows, key=lambda row: row["ordering_margin"])
    positive = {
        "some_topology_has_positive_ordering_margin": {
            "best_topology": best_row["topology"],
            "best_margin": best_row["ordering_margin"],
            "pass": best_row["ordering_margin"] > 0.005,
        },
        "measurement_information_is_present_in_all_ordered_rows": {
            "min_measurement_mi": float(min(row["ordered_measurement_mi"] for row in rows)),
            "pass": min(row["ordered_measurement_mi"] for row in rows) > 0.03,
        },
        "topology_changes_nonlogical_entropy_proxy": {
            "spread_entropy_range": float(max(row["ordered_spread_entropy_proxy"] for row in rows) - min(row["ordered_spread_entropy_proxy"] for row in rows)),
            "pass": (max(row["ordered_spread_entropy_proxy"] for row in rows) - min(row["ordered_spread_entropy_proxy"] for row in rows)) > 0.01,
        },
    }

    negative = {
        "not_all_topologies_give_the_same_ordering_margin": {
            "margin_range": float(max(row["ordering_margin"] for row in rows) - min(row["ordering_margin"] for row in rows)),
            "pass": (max(row["ordering_margin"] for row in rows) - min(row["ordering_margin"] for row in rows)) > 0.003,
        },
        "at_least_one_topology_remains_weak_for_ordering": {
            "worst_margin": float(min(row["ordering_margin"] for row in rows)),
            "pass": min(row["ordering_margin"] for row in rows) < 0.005,
        },
    }

    boundary = {
        "all_rows_have_closed_bookkeeping": {
            "max_closure_error": float(max(row["closure_error_max"] for row in rows)),
            "pass": max(row["closure_error_max"] for row in rows) < 1e-8,
        },
        "all_rows_are_finite": {
            "pass": all(
                np.isfinite(value)
                for row in rows
                for key, value in row.items()
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
        "name": "szilard_topology_entropy_array",
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
            "topologies": list(TOPOLOGIES.keys()),
            "best_topology": best_row["topology"],
            "best_margin": best_row["ordering_margin"],
            "scope_note": (
                "Topology and entropy/readout array for the Szilard-style stochastic lane. "
                "It compares logical entropy, information, spread proxy, and free-energy-gap proxy across memory landscapes."
            ),
        },
        "rows": rows,
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "szilard_topology_entropy_array_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
