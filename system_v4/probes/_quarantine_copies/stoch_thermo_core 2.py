#!/usr/bin/env python3
"""
Shared stochastic thermodynamics helpers for bounded 1D Langevin probes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

import numpy as np


ArrayFn = Callable[[np.ndarray, Dict[str, float]], np.ndarray]


@dataclass(frozen=True)
class ProtocolStage:
    name: str
    steps: int
    temperature: float
    start_params: Dict[str, float]
    end_params: Dict[str, float]


def interpolate_params(start: Dict[str, float], end: Dict[str, float], alpha: float) -> Dict[str, float]:
    keys = set(start) | set(end)
    return {
        key: float(start.get(key, 0.0) + alpha * (end.get(key, 0.0) - start.get(key, 0.0)))
        for key in keys
    }


def simulate_protocol(
    x0: np.ndarray,
    stages: List[ProtocolStage],
    potential: ArrayFn,
    force: ArrayFn,
    dt: float,
    gamma: float,
    rng: np.random.Generator,
) -> Dict[str, object]:
    """
    Simulate an overdamped Langevin protocol and keep trajectory bookkeeping.

    Work increment is accumulated from explicit protocol changes:
      dW = U(x_t, λ_{t+1}) - U(x_t, λ_t)
    Heat is then:
      dQ = ΔU - dW
    """
    x = np.asarray(x0, dtype=float).copy()
    n = int(x.shape[0])

    total_work = np.zeros(n, dtype=float)
    total_heat = np.zeros(n, dtype=float)
    total_delta_u = np.zeros(n, dtype=float)
    stage_logs: List[Dict[str, float]] = []

    for stage in stages:
        stage_work = np.zeros(n, dtype=float)
        stage_heat = np.zeros(n, dtype=float)
        stage_delta_u = np.zeros(n, dtype=float)
        barrier_work = np.zeros(n, dtype=float)
        tilt_work = np.zeros(n, dtype=float)

        params_old = dict(stage.start_params)

        for step in range(stage.steps):
            alpha_next = float(step + 1) / float(stage.steps)
            params_new = interpolate_params(stage.start_params, stage.end_params, alpha_next)

            u_old = potential(x, params_old)
            u_switch = potential(x, params_new)
            dwork = u_switch - u_old

            # Split sub-mechanics for the common double-well parameters if present.
            if "tilt" in params_old or "tilt" in params_new:
                tilt_old = dict(params_old)
                tilt_new = dict(params_old)
                tilt_new["tilt"] = params_new.get("tilt", params_old.get("tilt", 0.0))
                tilt_work += potential(x, tilt_new) - potential(x, tilt_old)
            if "barrier" in params_old or "barrier" in params_new:
                barrier_old = dict(params_old)
                barrier_new = dict(params_old)
                barrier_new["barrier"] = params_new.get("barrier", params_old.get("barrier", 0.0))
                barrier_work += potential(x, barrier_new) - potential(x, barrier_old)

            drift = force(x, params_new) / gamma
            noise = np.sqrt(2.0 * stage.temperature * dt / gamma) * rng.standard_normal(n)
            x_new = x + drift * dt + noise

            u_new = potential(x_new, params_new)
            du = u_new - u_old
            dq = du - dwork

            stage_work += dwork
            stage_heat += dq
            stage_delta_u += du

            x = x_new
            params_old = params_new

        total_work += stage_work
        total_heat += stage_heat
        total_delta_u += stage_delta_u
        stage_logs.append(
            {
                "name": stage.name,
                "temperature": float(stage.temperature),
                "steps": int(stage.steps),
                "mean_work": float(np.mean(stage_work)),
                "mean_heat": float(np.mean(stage_heat)),
                "mean_delta_u": float(np.mean(stage_delta_u)),
                "mean_barrier_work": float(np.mean(barrier_work)),
                "mean_tilt_work": float(np.mean(tilt_work)),
            }
        )

    return {
        "x_final": x,
        "total_work": total_work,
        "total_heat": total_heat,
        "total_delta_u": total_delta_u,
        "stage_logs": stage_logs,
    }


def jarzynski_estimator(work: np.ndarray, temperature: float, delta_f: float) -> Dict[str, float]:
    beta = 1.0 / float(temperature)
    lhs_samples = np.exp(-beta * np.asarray(work, dtype=float))
    lhs = float(np.mean(lhs_samples))
    rhs = float(np.exp(-beta * delta_f))
    stderr = float(np.std(lhs_samples) / max(np.sqrt(lhs_samples.size), 1.0))
    return {
        "lhs_mean": lhs,
        "rhs": rhs,
        "ratio": float(lhs / rhs) if rhs != 0.0 else float("nan"),
        "std_error": stderr,
    }
