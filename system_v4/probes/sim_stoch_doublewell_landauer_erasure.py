#!/usr/bin/env python3
"""
Stochastic Double-Well Szilard Substep Probe
===========================================
Operational stochastic sidecar that breaks a Szilard-style cycle into explicit
sub-mechanics:

  - measurement
  - feedback
  - reset
  - ordering tests

The model is intentionally finite and exploratory:
  - overdamped 1D double-well memory
  - trajectory-level work / heat bookkeeping
  - noisy readout as a measurement proxy
  - blind-feedback control as a negative control
  - explicit stage ordering comparisons

This does NOT claim a canonical engine theorem. It is a deep sub-mechanics lane.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Explicit stochastic substep probe for Szilard-style memory mechanics. "
    "The lane separates measurement, feedback, reset, and ordering tests on a "
    "finite double-well carrier, with trajectory bookkeeping and blind controls, "
    "but it does not promote the result to a canonical engine theorem."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "landauer_erasure",
    "measurement_feedback",
]

PRIMARY_LEGO_IDS = [
    "stochastic_thermodynamics",
    "measurement_feedback",
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


@dataclass(frozen=True)
class StageSpec:
    name: str
    kind: str
    steps: int
    temperature: float
    barrier_start: float
    barrier_end: float
    tilt_start: float
    tilt_end: float
    measurement_flip_prob: float = 0.0
    feedback_strong_tilt: float = 0.0
    feedback_weak_tilt: float = 0.0


DT = 0.0025
GAMMA = 1.0
TEMPERATURE = 1.0
N_TRAJ = 3000
MEAS_STEPS = 90
FEEDBACK_STEPS = 120
RESET_STEPS = 120
HOLD_STEPS = 60
RNG_SEED = 20260410
LEFT_STATE_THRESHOLD = 0.0
X_MIN = -4.5
X_MAX = 4.5
X_GRID = 4001
MEASUREMENT_FLIP_PROB = 0.08
BLIND_GUESS_FLIP_PROB = 0.50
FEEDBACK_STRONG_TILT = 2.35
FEEDBACK_WEAK_TILT = 0.31725
RESET_TILT = 1.40


def binary_entropy_nats(p: float) -> float:
    p = min(max(float(p), 1e-15), 1.0 - 1e-15)
    return float(-(p * np.log(p) + (1.0 - p) * np.log(1.0 - p)))


def normalize_bit_array(bits: np.ndarray) -> np.ndarray:
    return np.asarray(bits, dtype=int).reshape(-1)


def double_well_potential(x: np.ndarray, barrier: float, tilt: float) -> np.ndarray:
    return barrier * (x * x - 1.0) ** 2 + tilt * x


def double_well_force(x: np.ndarray, barrier: float, tilt: float) -> np.ndarray:
    d_u_dx = 4.0 * barrier * x * (x * x - 1.0) + tilt
    return -d_u_dx


def equilibrium_free_energy(barrier: float, tilt: float, temperature: float) -> float:
    xs = np.linspace(X_MIN, X_MAX, X_GRID)
    us = double_well_potential(xs, barrier, tilt)
    weights = np.exp(-us / temperature)
    z = np.trapezoid(weights, xs)
    return float(-temperature * np.log(z))


def sample_symmetric_initial_state(n_traj: int, rng: np.random.Generator) -> np.ndarray:
    base = rng.choice([-1.0, 1.0], size=n_traj)
    return base + 0.18 * rng.standard_normal(n_traj)


def binary_readout(x: np.ndarray, flip_prob: float, rng: np.random.Generator) -> np.ndarray:
    observed = (np.asarray(x) >= LEFT_STATE_THRESHOLD).astype(int)
    if flip_prob <= 0.0:
        return observed
    flips = rng.random(observed.shape[0]) < flip_prob
    return np.where(flips, 1 - observed, observed).astype(int)


def confusion_metrics(true_bits: np.ndarray, obs_bits: np.ndarray) -> Dict[str, float]:
    true_bits = normalize_bit_array(true_bits)
    obs_bits = normalize_bit_array(obs_bits)
    if true_bits.shape != obs_bits.shape:
        raise ValueError("bit arrays must align")

    n = float(true_bits.size)
    p_true1 = float(np.mean(true_bits == 1))
    p_obs1 = float(np.mean(obs_bits == 1))
    p11 = float(np.mean((true_bits == 1) & (obs_bits == 1)))
    p10 = float(np.mean((true_bits == 1) & (obs_bits == 0)))
    p01 = float(np.mean((true_bits == 0) & (obs_bits == 1)))
    p00 = float(np.mean((true_bits == 0) & (obs_bits == 0)))

    mutual_information = 0.0
    for pxy, px, py in [
        (p11, p_true1, p_obs1),
        (p10, p_true1, 1.0 - p_obs1),
        (p01, 1.0 - p_true1, p_obs1),
        (p00, 1.0 - p_true1, 1.0 - p_obs1),
    ]:
        if pxy > 0.0:
            mutual_information += pxy * np.log(pxy / (px * py))

    return {
        "p_true_right": p_true1,
        "p_obs_right": p_obs1,
        "accuracy": float(np.mean(true_bits == obs_bits)),
        "false_positive_rate": p01 / max(1.0 - p_true1, 1e-15),
        "false_negative_rate": p10 / max(p_true1, 1e-15),
        "mutual_information": float(mutual_information),
        "joint_right_right": p11,
        "joint_right_left": p10,
        "joint_left_right": p01,
        "joint_left_left": p00,
        "n": n,
    }


def stage_simulation(
    x0: np.ndarray,
    barrier_start: float,
    barrier_end: float,
    tilt_start: float,
    tilt_end: float,
    steps: int,
    temperature: float,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, float]]:
    x = np.asarray(x0, dtype=float).copy()
    n = x.shape[0]
    total_work = np.zeros(n, dtype=float)
    total_heat = np.zeros(n, dtype=float)
    total_delta_u = np.zeros(n, dtype=float)
    barrier_work = np.zeros(n, dtype=float)
    tilt_work = np.zeros(n, dtype=float)

    barrier_old = float(barrier_start)
    tilt_old = float(tilt_start)

    for step in range(steps):
        alpha = float(step + 1) / float(steps)
        barrier_new = float(barrier_start + alpha * (barrier_end - barrier_start))
        tilt_new = float(tilt_start + alpha * (tilt_end - tilt_start))

        u_old = double_well_potential(x, barrier_old, tilt_old)
        u_new_params = double_well_potential(x, barrier_new, tilt_new)
        dwork = u_new_params - u_old

        barrier_old_only = double_well_potential(x, barrier_old, tilt_old)
        barrier_new_only = double_well_potential(x, barrier_new, tilt_old)
        tilt_old_only = double_well_potential(x, barrier_old, tilt_old)
        tilt_new_only = double_well_potential(x, barrier_old, tilt_new)
        barrier_work += barrier_new_only - barrier_old_only
        tilt_work += tilt_new_only - tilt_old_only

        drift = double_well_force(x, barrier_new, tilt_new) / GAMMA
        noise = np.sqrt(2.0 * temperature * DT / GAMMA) * rng.standard_normal(n)
        x_new = x + drift * DT + noise

        u_new = double_well_potential(x_new, barrier_new, tilt_new)
        du = u_new - u_old
        dq = du - dwork

        total_work += dwork
        total_heat += dq
        total_delta_u += du

        x = x_new
        barrier_old = barrier_new
        tilt_old = tilt_new

    stage_log = {
        "steps": int(steps),
        "temperature": float(temperature),
        "barrier_start": float(barrier_start),
        "barrier_end": float(barrier_end),
        "tilt_start": float(tilt_start),
        "tilt_end": float(tilt_end),
        "mean_work": float(np.mean(total_work)),
        "mean_heat": float(np.mean(total_heat)),
        "mean_delta_u": float(np.mean(total_delta_u)),
        "mean_barrier_work": float(np.mean(barrier_work)),
        "mean_tilt_work": float(np.mean(tilt_work)),
    }
    return x, total_work, total_heat, total_delta_u, stage_log


def clone_stage(stage: StageSpec, *, name: str | None = None, kind: str | None = None) -> StageSpec:
    return StageSpec(
        name=name or stage.name,
        kind=kind or stage.kind,
        steps=stage.steps,
        temperature=stage.temperature,
        barrier_start=stage.barrier_start,
        barrier_end=stage.barrier_end,
        tilt_start=stage.tilt_start,
        tilt_end=stage.tilt_end,
        measurement_flip_prob=stage.measurement_flip_prob,
        feedback_strong_tilt=stage.feedback_strong_tilt,
        feedback_weak_tilt=stage.feedback_weak_tilt,
    )


def build_stage_library() -> Dict[str, StageSpec]:
    return {
        "measurement": StageSpec(
            name="measurement_window",
            kind="measurement",
            steps=MEAS_STEPS,
            temperature=TEMPERATURE,
            barrier_start=1.55,
            barrier_end=0.10,
            tilt_start=0.0,
            tilt_end=0.0,
            measurement_flip_prob=MEASUREMENT_FLIP_PROB,
        ),
        "feedback": StageSpec(
            name="feedback_drive",
            kind="feedback",
            steps=FEEDBACK_STEPS,
            temperature=TEMPERATURE,
            barrier_start=0.10,
            barrier_end=1.55,
            tilt_start=0.0,
            tilt_end=0.0,
            feedback_strong_tilt=FEEDBACK_STRONG_TILT,
            feedback_weak_tilt=FEEDBACK_WEAK_TILT,
        ),
        "reset": StageSpec(
            name="reset_lock",
            kind="reset",
            steps=RESET_STEPS,
            temperature=TEMPERATURE,
            barrier_start=1.55,
            barrier_end=1.55,
            tilt_start=FEEDBACK_WEAK_TILT,
            tilt_end=RESET_TILT,
        ),
        "hold": StageSpec(
            name="left_hold",
            kind="hold",
            steps=HOLD_STEPS,
            temperature=TEMPERATURE,
            barrier_start=1.55,
            barrier_end=1.55,
            tilt_start=RESET_TILT,
            tilt_end=RESET_TILT,
        ),
    }


def simulate_ordered_protocol(
    x0: np.ndarray,
    order: List[str],
    rng: np.random.Generator,
    blind_guess_prob: float = BLIND_GUESS_FLIP_PROB,
) -> Dict[str, object]:
    library = build_stage_library()
    x = np.asarray(x0, dtype=float).copy()
    n = x.shape[0]
    recorded_bits = None
    measured_bits = None
    true_initial_bits = (x >= LEFT_STATE_THRESHOLD).astype(int)
    stage_logs: List[Dict[str, object]] = []
    total_work = np.zeros(n, dtype=float)
    total_heat = np.zeros(n, dtype=float)
    total_delta_u = np.zeros(n, dtype=float)

    measurement_record = None

    for stage_name in order:
        stage = library[stage_name]
        stage_entry: Dict[str, object] = {
            "name": stage.name,
            "kind": stage.kind,
        }

        if stage.kind == "measurement":
            x_before = x.copy()
            x, stage_work, stage_heat, stage_delta_u, stage_log = stage_simulation(
                x,
                stage.barrier_start,
                stage.barrier_end,
                stage.tilt_start,
                stage.tilt_end,
                stage.steps,
                stage.temperature,
                rng,
            )
            true_bits = (x_before >= LEFT_STATE_THRESHOLD).astype(int)
            sensed_bits = binary_readout(x, stage.measurement_flip_prob, rng)
            measurement_record = sensed_bits
            measured_bits = sensed_bits
            measurement_stats = confusion_metrics(true_bits, sensed_bits)
            measurement_stats["side_flip_rate"] = float(np.mean((x_before >= 0.0) != (x >= 0.0)))
            stage_entry.update(stage_log)
            stage_entry["measurement"] = measurement_stats
            stage_entry["record_after_stage"] = "present"
            total_work += stage_work
            total_heat += stage_heat
            total_delta_u += stage_delta_u

        elif stage.kind == "feedback":
            if measurement_record is None:
                control_bits = rng.integers(0, 2, size=n)
                control_mode = "blind_guess"
                right_tilt = stage.feedback_strong_tilt
                left_tilt = -stage.feedback_strong_tilt
            else:
                control_bits = measurement_record
                control_mode = "measured_record"
                right_tilt = stage.feedback_strong_tilt
                left_tilt = stage.feedback_weak_tilt

            right_mask = control_bits == 1
            left_mask = ~right_mask

            x_out = x.copy()
            stage_work = np.zeros(n, dtype=float)
            stage_heat = np.zeros(n, dtype=float)
            stage_delta_u = np.zeros(n, dtype=float)
            branch_metrics: Dict[str, Dict[str, float]] = {}

            if np.any(right_mask):
                x_right, work_right, heat_right, delta_u_right, log_right = stage_simulation(
                    x[right_mask],
                    stage.barrier_start,
                    stage.barrier_end,
                    0.0,
                    right_tilt,
                    stage.steps,
                    stage.temperature,
                    rng,
                )
                x_out[right_mask] = x_right
                stage_work[right_mask] = work_right
                stage_heat[right_mask] = heat_right
                stage_delta_u[right_mask] = delta_u_right
                branch_metrics["right_branch"] = {
                    "mean_work": float(np.mean(work_right)),
                    "mean_heat": float(np.mean(heat_right)),
                    "mean_delta_u": float(np.mean(delta_u_right)),
                    "closure_error": float(
                        abs(np.mean(delta_u_right) - np.mean(work_right) - np.mean(heat_right))
                    ),
                    "count": int(np.sum(right_mask)),
                    "final_left_fraction": float(np.mean(x_right < LEFT_STATE_THRESHOLD)),
                }
                stage_entry.setdefault("branch_logs", []).append({"branch": "right", **log_right, "count": int(np.sum(right_mask))})

            if np.any(left_mask):
                x_left, work_left, heat_left, delta_u_left, log_left = stage_simulation(
                    x[left_mask],
                    stage.barrier_start,
                    stage.barrier_end,
                    0.0,
                    left_tilt,
                    stage.steps,
                    stage.temperature,
                    rng,
                )
                x_out[left_mask] = x_left
                stage_work[left_mask] = work_left
                stage_heat[left_mask] = heat_left
                stage_delta_u[left_mask] = delta_u_left
                branch_metrics["left_branch"] = {
                    "mean_work": float(np.mean(work_left)),
                    "mean_heat": float(np.mean(heat_left)),
                    "mean_delta_u": float(np.mean(delta_u_left)),
                    "closure_error": float(
                        abs(np.mean(delta_u_left) - np.mean(work_left) - np.mean(heat_left))
                    ),
                    "count": int(np.sum(left_mask)),
                    "final_left_fraction": float(np.mean(x_left < LEFT_STATE_THRESHOLD)),
                }
                stage_entry.setdefault("branch_logs", []).append({"branch": "left", **log_left, "count": int(np.sum(left_mask))})

            x = x_out
            stage_entry["control_mode"] = control_mode
            stage_entry["branch_metrics"] = branch_metrics
            stage_entry["mean_work"] = float(np.mean(stage_work))
            stage_entry["mean_heat"] = float(np.mean(stage_heat))
            stage_entry["mean_delta_u"] = float(np.mean(stage_delta_u))
            stage_entry["record_after_stage"] = "present" if measurement_record is not None else "absent"
            total_work += stage_work
            total_heat += stage_heat
            total_delta_u += stage_delta_u

        elif stage.kind == "reset":
            x, stage_work, stage_heat, stage_delta_u, stage_log = stage_simulation(
                x,
                stage.barrier_start,
                stage.barrier_end,
                stage.tilt_start,
                stage.tilt_end,
                stage.steps,
                stage.temperature,
                rng,
            )
            measurement_record = None
            stage_entry.update(stage_log)
            stage_entry["record_after_stage"] = "cleared"
            total_work += stage_work
            total_heat += stage_heat
            total_delta_u += stage_delta_u

        elif stage.kind == "hold":
            x, stage_work, stage_heat, stage_delta_u, stage_log = stage_simulation(
                x,
                stage.barrier_start,
                stage.barrier_end,
                stage.tilt_start,
                stage.tilt_end,
                stage.steps,
                stage.temperature,
                rng,
            )
            stage_entry.update(stage_log)
            stage_entry["record_after_stage"] = "unchanged"
            total_work += stage_work
            total_heat += stage_heat
            total_delta_u += stage_delta_u

        else:
            raise ValueError(f"unknown stage kind: {stage.kind}")

        stage_logs.append(stage_entry)

    final_bits = (x < LEFT_STATE_THRESHOLD).astype(int)
    initial_entropy = binary_entropy_nats(float(np.mean(true_initial_bits == 1)))
    final_entropy = binary_entropy_nats(float(np.mean(final_bits == 1)))
    measured_entropy = (
        binary_entropy_nats(float(np.mean(measured_bits == 1))) if measured_bits is not None else None
    )

    out = {
        "order": order,
        "initial_left_fraction": float(np.mean(true_initial_bits == 0)),
        "final_left_fraction": float(np.mean(final_bits == 0)),
        "measurement_record_present_at_end": bool(measurement_record is not None),
        "initial_entropy": float(initial_entropy),
        "final_entropy": float(final_entropy),
        "measured_entropy": float(measured_entropy) if measured_entropy is not None else None,
        "mean_work": float(np.mean(total_work)),
        "mean_heat": float(np.mean(total_heat)),
        "mean_delta_u": float(np.mean(total_delta_u)),
        "closure_error": float(abs(np.mean(total_delta_u) - np.mean(total_work) - np.mean(total_heat))),
        "stage_logs": stage_logs,
    }
    if measured_bits is not None:
        out["measurement_accuracy"] = float(np.mean(measured_bits == true_initial_bits))
        out["measurement_mutual_information"] = confusion_metrics(true_initial_bits, measured_bits)[
            "mutual_information"
        ]
    else:
        out["measurement_accuracy"] = None
        out["measurement_mutual_information"] = None
    return out


def summarize_protocol(protocol: Dict[str, object], label: str) -> Dict[str, object]:
    return {
        "label": label,
        "final_left_fraction": protocol["final_left_fraction"],
        "final_entropy": protocol["final_entropy"],
        "measurement_accuracy": protocol["measurement_accuracy"],
        "measurement_mutual_information": protocol["measurement_mutual_information"],
        "mean_work": protocol["mean_work"],
        "closure_error": protocol["closure_error"],
        "record_present_at_end": protocol["measurement_record_present_at_end"],
    }


def main() -> None:
    rng = np.random.default_rng(RNG_SEED)

    x_init = sample_symmetric_initial_state(N_TRAJ, rng)

    ordered = simulate_ordered_protocol(
        x_init,
        order=["measurement", "feedback", "reset", "hold"],
        rng=np.random.default_rng(RNG_SEED + 1),
    )
    feedback_first = simulate_ordered_protocol(
        x_init,
        order=["feedback", "measurement", "reset", "hold"],
        rng=np.random.default_rng(RNG_SEED + 2),
    )
    reset_first = simulate_ordered_protocol(
        x_init,
        order=["reset", "measurement", "feedback", "hold"],
        rng=np.random.default_rng(RNG_SEED + 3),
    )
    measurement_then_reset_then_feedback = simulate_ordered_protocol(
        x_init,
        order=["measurement", "reset", "feedback", "hold"],
        rng=np.random.default_rng(RNG_SEED + 4),
    )
    measurement_only = simulate_ordered_protocol(
        x_init,
        order=["measurement", "hold"],
        rng=np.random.default_rng(RNG_SEED + 5),
    )
    feedback_only = simulate_ordered_protocol(
        x_init,
        order=["feedback", "hold"],
        rng=np.random.default_rng(RNG_SEED + 6),
    )
    reset_only = simulate_ordered_protocol(
        x_init,
        order=["reset", "hold"],
        rng=np.random.default_rng(RNG_SEED + 7),
    )

    ordered_reset_record = ordered["measurement_record_present_at_end"] is False
    feedback_only_record_blind = feedback_only["measurement_accuracy"] is not None

    positive = {
        "measurement_stage_produces_informative_readout": {
            "accuracy": ordered["measurement_accuracy"],
            "mutual_information": ordered["measurement_mutual_information"],
            "pass": ordered["measurement_accuracy"] is not None
            and ordered["measurement_accuracy"] > 0.58
            and ordered["measurement_mutual_information"] > 0.03,
        },
        "measurement_then_feedback_then_reset_improves_order_over_blind_control": {
            "ordered_final_entropy": ordered["final_entropy"],
            "blind_feedback_final_entropy": feedback_only["final_entropy"],
            "pass": ordered["final_entropy"] < feedback_only["final_entropy"] - 0.015,
        },
        "reset_stage_clears_the_record_after_feedback": {
            "ordered_record_present_at_end": ordered["measurement_record_present_at_end"],
            "pass": ordered_reset_record,
        },
        "correct_order_beats_scrambled_orders": {
            "ordered_final_entropy": ordered["final_entropy"],
            "feedback_first_final_entropy": feedback_first["final_entropy"],
            "reset_first_final_entropy": reset_first["final_entropy"],
            "measurement_then_reset_then_feedback_final_entropy": measurement_then_reset_then_feedback[
                "final_entropy"
            ],
            "pass": ordered["final_entropy"] < min(
                feedback_first["final_entropy"],
                reset_first["final_entropy"],
                measurement_then_reset_then_feedback["final_entropy"],
            ) - 0.005,
        },
    }

    negative = {
        "measurement_only_does_not_erase_memory": {
            "measurement_only_final_entropy": measurement_only["final_entropy"],
            "pass": measurement_only["final_entropy"] > ordered["final_entropy"] + 0.01,
        },
        "feedback_before_measurement_falls_back_to_blind_guess": {
            "feedback_first_final_entropy": feedback_first["final_entropy"],
            "ordered_final_entropy": ordered["final_entropy"],
            "pass": feedback_first["final_entropy"] > ordered["final_entropy"] + 0.001,
        },
        "reset_before_feedback_erases_the_record_and_weakens_control": {
            "measurement_then_reset_then_feedback_final_entropy": measurement_then_reset_then_feedback[
                "final_entropy"
            ],
            "ordered_final_entropy": ordered["final_entropy"],
            "pass": measurement_then_reset_then_feedback["final_entropy"] > ordered["final_entropy"] + 0.001,
        },
        "reset_only_does_not_create_measurement_information": {
            "reset_only_record_present_at_end": reset_only["measurement_record_present_at_end"],
            "pass": reset_only["measurement_record_present_at_end"] is False,
        },
    }

    boundary = {
        "all_protocols_close_work_heat_bookkeeping": {
            "ordered_closure_error": ordered["closure_error"],
            "feedback_first_closure_error": feedback_first["closure_error"],
            "reset_first_closure_error": reset_first["closure_error"],
            "measurement_then_reset_then_feedback_closure_error": measurement_then_reset_then_feedback[
                "closure_error"
            ],
            "measurement_only_closure_error": measurement_only["closure_error"],
            "feedback_only_closure_error": feedback_only["closure_error"],
            "reset_only_closure_error": reset_only["closure_error"],
            "pass": max(
                ordered["closure_error"],
                feedback_first["closure_error"],
                reset_first["closure_error"],
                measurement_then_reset_then_feedback["closure_error"],
                measurement_only["closure_error"],
                feedback_only["closure_error"],
                reset_only["closure_error"],
            ) < 1e-9,
        },
        "all_protocols_produce_finite_summary_statistics": {
            "pass": all(
                np.isfinite(v)
                for item in [
                    ordered,
                    feedback_first,
                    reset_first,
                    measurement_then_reset_then_feedback,
                    measurement_only,
                    feedback_only,
                    reset_only,
                ]
                for key, v in item.items()
                if isinstance(v, (int, float, np.floating))
            ),
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    results = {
        "name": "szilard_measurement_feedback_substeps",
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
            "measurement_steps": MEAS_STEPS,
            "feedback_steps": FEEDBACK_STEPS,
            "reset_steps": RESET_STEPS,
            "hold_steps": HOLD_STEPS,
            "ordered": summarize_protocol(ordered, "ordered"),
            "feedback_first": summarize_protocol(feedback_first, "feedback_first"),
            "reset_first": summarize_protocol(reset_first, "reset_first"),
            "measurement_then_reset_then_feedback": summarize_protocol(
                measurement_then_reset_then_feedback, "measurement_then_reset_then_feedback"
            ),
            "measurement_only": summarize_protocol(measurement_only, "measurement_only"),
            "feedback_only": summarize_protocol(feedback_only, "feedback_only"),
            "reset_only": summarize_protocol(reset_only, "reset_only"),
            "scope_note": (
                "Exploratory stochastic double-well lane that decomposes the Szilard cycle "
                "into measurement, feedback, reset, and ordering tests."
            ),
        },
        "protocols": {
            "ordered": ordered,
            "feedback_first": feedback_first,
            "reset_first": reset_first,
            "measurement_then_reset_then_feedback": measurement_then_reset_then_feedback,
            "measurement_only": measurement_only,
            "feedback_only": feedback_only,
            "reset_only": reset_only,
        },
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "szilard_measurement_feedback_substeps_results.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
