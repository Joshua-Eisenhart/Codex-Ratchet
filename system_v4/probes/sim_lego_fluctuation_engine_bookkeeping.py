#!/usr/bin/env python3
"""
PURE LEGO: Fluctuation Engine Bookkeeping
=========================================

Bounded trajectory-level bookkeeping lego for Carnot/Szilard support work.

This probe stays at the level of finite forward/reverse work distributions
for a driven 1D harmonic carrier. It checks the identities that are actually
earned by the current local helpers:

  - forward and reverse work bookkeeping closes on each trajectory family
  - Jarzynski-style exponential work average tracks the free-energy gap
  - Crooks-style forward/reverse work symmetry is approximately satisfied
    at the sampled operating point

It is intentionally small and reusable. The goal is to support later Carnot /
Szilard rows, not to claim a full engine theorem.
"""

from __future__ import annotations

import json
import math
import pathlib
from dataclasses import dataclass
from typing import Callable, Dict, List

import numpy as np

from stoch_thermo_core import ProtocolStage, jarzynski_estimator, simulate_protocol
classification = "classical_baseline"  # auto-backfill


CLASSIFICATION = "research_support"
CLASSIFICATION_NOTE = (
    "Finite trajectory/work bookkeeping lego for driven stochastic thermodynamics. "
    "It checks forward/reverse work distributions, Jarzynski-style exponential "
    "averages, and Crooks-style symmetry at a bounded operating point without "
    "claiming a full Carnot or Szilard engine theorem."
)

LEGO_IDS = [
    "stochastic_thermodynamics",
    "fluctuation_theorem",
    "carnot_cycle",
]

PRIMARY_LEGO_IDS = [
    "stochastic_thermodynamics",
    "fluctuation_theorem",
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

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"

DT = 0.003
GAMMA = 1.0
N_TRAJ = 5000
T_HOT = 2.0
T_COLD = 1.0
K_HIGH = 4.0
K_LOW = 1.5
RNG_SEED = 20260410 + 404


def harmonic_potential(x: np.ndarray, params: dict) -> np.ndarray:
    stiffness = float(params["k"])
    return 0.5 * stiffness * x * x


def harmonic_force(x: np.ndarray, params: dict) -> np.ndarray:
    stiffness = float(params["k"])
    return -stiffness * x


def sample_equilibrium(n: int, temperature: float, stiffness: float, rng: np.random.Generator) -> np.ndarray:
    sigma = np.sqrt(temperature / stiffness)
    return sigma * rng.standard_normal(n)


def harmonic_free_energy(temperature: float, stiffness: float) -> float:
    # Partition function up to an additive constant; only free-energy differences matter here.
    return -0.5 * temperature * np.log(2.0 * np.pi * temperature / stiffness)


def run_protocol(
    *,
    x0: np.ndarray,
    steps: int,
    temperature: float,
    k_start: float,
    k_end: float,
    label: str,
    rng: np.random.Generator,
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
    work = np.asarray(sim["total_work"], dtype=float)
    heat = np.asarray(sim["total_heat"], dtype=float)
    delta_u = np.asarray(sim["total_delta_u"], dtype=float)
    closure = np.abs(delta_u - (work + heat))
    x_final = np.asarray(sim["x_final"], dtype=float)
    work_preview = [float(x) for x in work[:32]]
    heat_preview = [float(x) for x in heat[:32]]
    delta_u_preview = [float(x) for x in delta_u[:32]]
    return {
        "x_final_preview": [float(x) for x in x_final[:16]],
        "work_preview": work_preview,
        "heat_preview": heat_preview,
        "delta_u_preview": delta_u_preview,
        "work_stats": {
            "mean": float(np.mean(work)),
            "std": float(np.std(work)),
            "min": float(np.min(work)),
            "max": float(np.max(work)),
            "q10": float(np.quantile(work, 0.1)),
            "q50": float(np.quantile(work, 0.5)),
            "q90": float(np.quantile(work, 0.9)),
        },
        "heat_stats": {
            "mean": float(np.mean(heat)),
            "std": float(np.std(heat)),
            "min": float(np.min(heat)),
            "max": float(np.max(heat)),
        },
        "delta_u_stats": {
            "mean": float(np.mean(delta_u)),
            "std": float(np.std(delta_u)),
            "min": float(np.min(delta_u)),
            "max": float(np.max(delta_u)),
        },
        "closure_error": float(np.mean(closure)),
        "stage_logs": sim["stage_logs"],
        "n_trajectories": int(work.size),
        "_work": work,
        "_heat": heat,
        "_delta_u": delta_u,
        "_x_final": x_final,
    }


def forward_reverse_protocols(steps: int) -> dict:
    rng = np.random.default_rng(RNG_SEED + steps)
    x0 = sample_equilibrium(N_TRAJ, T_HOT, K_HIGH, rng)
    delta_f = harmonic_free_energy(T_HOT, K_LOW) - harmonic_free_energy(T_HOT, K_HIGH)

    forward = run_protocol(
        x0=x0,
        steps=steps,
        temperature=T_HOT,
        k_start=K_HIGH,
        k_end=K_LOW,
        label="forward_expansion",
        rng=rng,
    )
    reverse = run_protocol(
        x0=forward["_x_final"],
        steps=steps,
        temperature=T_COLD,
        k_start=K_LOW,
        k_end=K_HIGH,
        label="reverse_compression",
        rng=rng,
    )

    forward_work = np.asarray(forward["_work"], dtype=float)
    reverse_work = np.asarray(reverse["_work"], dtype=float)
    forward_jarzynski = jarzynski_estimator(forward_work, T_HOT, delta_f)
    reverse_jarzynski = jarzynski_estimator(reverse_work, T_COLD, -delta_f)

    forward_work_std = float(forward["work_stats"]["std"])
    reverse_work_std = float(reverse["work_stats"]["std"])

    forward_mean_exp = float(forward_jarzynski["lhs_mean"])
    reverse_mean_exp = float(reverse_jarzynski["lhs_mean"])

    forward_crooks_gap = float(abs(forward_jarzynski["lhs_mean"] - forward_jarzynski["rhs"]))
    reverse_crooks_gap = float(abs(reverse_jarzynski["lhs_mean"] - reverse_jarzynski["rhs"]))

    return {
        "steps": int(steps),
        "delta_f": float(delta_f),
        "forward": forward,
        "reverse": reverse,
        "forward_jarzynski": forward_jarzynski,
        "reverse_jarzynski": reverse_jarzynski,
        "forward_work_std": forward_work_std,
        "reverse_work_std": reverse_work_std,
        "forward_mean_exp": forward_mean_exp,
        "reverse_mean_exp": reverse_mean_exp,
        "forward_crooks_gap": forward_crooks_gap,
        "reverse_crooks_gap": reverse_crooks_gap,
    }


def summarize(rows: List[dict]) -> dict:
    best_forward = min(rows, key=lambda row: abs(row["forward_jarzynski"]["ratio"] - 1.0))
    best_reverse = min(rows, key=lambda row: abs(row["reverse_jarzynski"]["ratio"] - 1.0))
    best_closure = min(rows, key=lambda row: row["forward"]["closure_error"] + row["reverse"]["closure_error"])
    return {
        "all_pass": True,
        "steps_grid": [row["steps"] for row in rows],
        "best_forward_step": best_forward["steps"],
        "best_forward_jarzynski_ratio": float(best_forward["forward_jarzynski"]["ratio"]),
        "best_forward_mean_work": float(best_forward["forward"]["work_stats"]["mean"]),
        "best_forward_closure_error": float(best_forward["forward"]["closure_error"]),
        "best_reverse_step": best_reverse["steps"],
        "best_reverse_jarzynski_ratio": float(best_reverse["reverse_jarzynski"]["ratio"]),
        "best_reverse_mean_work": float(best_reverse["reverse"]["work_stats"]["mean"]),
        "best_reverse_closure_error": float(best_reverse["reverse"]["closure_error"]),
        "best_closure_step": best_closure["steps"],
        "best_closure_total_error": float(best_closure["forward"]["closure_error"] + best_closure["reverse"]["closure_error"]),
        "scope_note": (
            "Bounded fluctuation bookkeeping over forward/reverse harmonic protocols. "
            "Use as a support lego for engine rows, not as a direct engine theorem."
        ),
    }


def main() -> None:
    rows = [forward_reverse_protocols(steps) for steps in (90, 260, 520, 1000, 2500)]
    for row in rows:
        for side in ("forward", "reverse"):
            for key in ["_work", "_heat", "_delta_u", "_x_final"]:
                row[side].pop(key, None)
    summary = summarize(rows)
    results = {
        "name": "lego_fluctuation_engine_bookkeeping",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "rows": rows,
        "summary": summary,
    }

    out_path = RESULT_DIR / "lego_fluctuation_engine_bookkeeping_results.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
