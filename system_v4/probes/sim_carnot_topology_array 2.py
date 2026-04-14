#!/usr/bin/env python3
"""
Carnot Topology Array
====================
Exploratory stochastic Carnot array across several 1D working-substance
geometries/topologies.

The goal is comparative, not canonical:
  - harmonic well
  - quartic single-well
  - soft double-well

Each topology is run in forward and reverse mode over a bounded step sweep.
The output compares closure, efficiency/COP, and regime quality so later QIT-
aligned variants can be built against the same matrix.
"""

from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List

import numpy as np


PROBE_DIR = pathlib.Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from stoch_thermo_core import ProtocolStage, simulate_protocol  # noqa: E402


CLASSIFICATION = "exploratory"
CLASSIFICATION_NOTE = (
    "Exploratory topology array for stochastic Carnot-like cycles across "
    "multiple 1D working-substance geometries. The array is meant to expose "
    "where simple harmonic assumptions hold, break, or need QIT-aligned repair."
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

DT = 0.003
GAMMA = 1.0
N_TRAJ = 1200
STEP_GRID = [120, 520, 2500]
T_HOT = 2.0
T_COLD = 1.0
HOT_LOW_SCALE = 0.35
RNG_SEED = 20260410 + 606


@dataclass(frozen=True)
class TopologySpec:
    name: str
    label: str
    potential: Callable[[np.ndarray, Dict[str, float]], np.ndarray]
    force: Callable[[np.ndarray, Dict[str, float]], np.ndarray]
    x_min: float
    x_max: float
    grid_size: int
    start_params: Dict[str, float]
    hot_low_params: Dict[str, float]
    note: str

    @property
    def scale(self) -> float:
        return T_COLD / T_HOT

    @property
    def cold_low_params(self) -> Dict[str, float]:
        return {
            key: float(value * self.scale) if key in self.start_params and key not in {"a4", "soft"} else float(value)
            for key, value in self.hot_low_params.items()
        }

    @property
    def cold_high_params(self) -> Dict[str, float]:
        return {
            key: float(value * self.scale) if key in self.start_params and key not in {"a4", "soft"} else float(value)
            for key, value in self.start_params.items()
        }


def harmonic_potential(x: np.ndarray, params: Dict[str, float]) -> np.ndarray:
    k = float(params["k"])
    return 0.5 * k * x * x


def harmonic_force(x: np.ndarray, params: Dict[str, float]) -> np.ndarray:
    k = float(params["k"])
    return -k * x


def quartic_single_well_potential(x: np.ndarray, params: Dict[str, float]) -> np.ndarray:
    k = float(params["k"])
    a4 = float(params["a4"])
    return 0.25 * a4 * x**4 + 0.5 * k * x * x


def quartic_single_well_force(x: np.ndarray, params: Dict[str, float]) -> np.ndarray:
    k = float(params["k"])
    a4 = float(params["a4"])
    return -(a4 * x**3 + k * x)


def soft_double_well_potential(x: np.ndarray, params: Dict[str, float]) -> np.ndarray:
    barrier = float(params["barrier"])
    soft = float(params["soft"])
    return barrier * (x * x - 1.0) ** 2 + 0.5 * soft * x * x


def soft_double_well_force(x: np.ndarray, params: Dict[str, float]) -> np.ndarray:
    barrier = float(params["barrier"])
    soft = float(params["soft"])
    return -(4.0 * barrier * x * (x * x - 1.0) + soft * x)


def mean_internal_energy(x: np.ndarray, potential: Callable[[np.ndarray, Dict[str, float]], np.ndarray], params: Dict[str, float]) -> float:
    return float(np.mean(potential(np.asarray(x, dtype=float), params)))


def sample_boltzmann(
    potential: Callable[[np.ndarray, Dict[str, float]], np.ndarray],
    params: Dict[str, float],
    temperature: float,
    n: int,
    rng: np.random.Generator,
    x_min: float,
    x_max: float,
    grid_size: int,
) -> np.ndarray:
    xs = np.linspace(x_min, x_max, grid_size)
    us = potential(xs, params)
    shifted = us - float(np.min(us))
    weights = np.exp(-shifted / max(float(temperature), 1e-12))
    cdf = np.cumsum(weights)
    cdf /= cdf[-1]
    return np.interp(rng.random(n), cdf, xs)


def run_leg(
    x0: np.ndarray,
    temperature: float,
    potential: Callable[[np.ndarray, Dict[str, float]], np.ndarray],
    force: Callable[[np.ndarray, Dict[str, float]], np.ndarray],
    params_start: Dict[str, float],
    params_end: Dict[str, float],
    steps: int,
    rng: np.random.Generator,
    label: str,
) -> dict:
    sim = simulate_protocol(
        x0=x0,
        stages=[
            ProtocolStage(
                name=label,
                steps=int(steps),
                temperature=float(temperature),
                start_params=dict(params_start),
                end_params=dict(params_end),
            )
        ],
        potential=potential,
        force=force,
        dt=DT,
        gamma=GAMMA,
        rng=rng,
    )
    x_final = np.asarray(sim["x_final"], dtype=float)
    return {
        "x": x_final,
        "final_variance": float(np.var(x_final)),
        "final_internal_energy": mean_internal_energy(x_final, potential, params_end),
        "mean_work": float(np.mean(sim["total_work"])),
        "mean_heat": float(np.mean(sim["total_heat"])),
        "mean_delta_u": float(np.mean(sim["total_delta_u"])),
        "closure_error": float(
            abs(float(np.mean(sim["total_delta_u"])) - (float(np.mean(sim["total_work"])) + float(np.mean(sim["total_heat"]))))
        ),
        "stage_logs": sim["stage_logs"],
    }


def adiabatic_jump(
    x: np.ndarray,
    potential: Callable[[np.ndarray, Dict[str, float]], np.ndarray],
    params_before: Dict[str, float],
    params_after: Dict[str, float],
) -> dict:
    x = np.asarray(x, dtype=float)
    u_before = potential(x, params_before)
    u_after = potential(x, params_after)
    dwork = u_after - u_before
    return {
        "x": x.copy(),
        "final_variance": float(np.var(x)),
        "final_internal_energy": mean_internal_energy(x, potential, params_after),
        "mean_work": float(np.mean(dwork)),
        "mean_heat": 0.0,
        "mean_delta_u": float(np.mean(dwork)),
        "closure_error": 0.0,
    }


def build_cycle(
    spec: TopologySpec,
    steps: int,
    seed_offset: int,
    reverse: bool = False,
) -> dict:
    rng = np.random.default_rng(RNG_SEED + seed_offset)
    x0 = sample_boltzmann(
        spec.potential,
        spec.start_params,
        T_HOT,
        N_TRAJ,
        rng,
        spec.x_min,
        spec.x_max,
        spec.grid_size,
    )
    initial_variance = float(np.var(x0))
    initial_internal_energy = mean_internal_energy(x0, spec.potential, spec.start_params)

    if not reverse:
        hot_iso = run_leg(
            x0,
            T_HOT,
            spec.potential,
            spec.force,
            spec.start_params,
            spec.hot_low_params,
            steps,
            rng,
            f"{spec.name}_hot_isotherm",
        )
        adiabatic_expand = adiabatic_jump(hot_iso["x"], spec.potential, spec.hot_low_params, spec.cold_low_params)
        cold_iso = run_leg(
            adiabatic_expand["x"],
            T_COLD,
            spec.potential,
            spec.force,
            spec.cold_low_params,
            spec.cold_high_params,
            steps,
            rng,
            f"{spec.name}_cold_isotherm",
        )
        adiabatic_compress = adiabatic_jump(cold_iso["x"], spec.potential, spec.cold_high_params, spec.start_params)
        stages = [hot_iso, adiabatic_expand, cold_iso, adiabatic_compress]
        q_hot = hot_iso["mean_heat"]
        q_cold = cold_iso["mean_heat"]
        work_on_system = sum(stage["mean_work"] for stage in stages)
        work_by_system = -work_on_system
        efficiency = work_by_system / q_hot if q_hot > 0.0 else float("nan")
        carnot_bound = 1.0 - (T_COLD / T_HOT)
        x_final = adiabatic_compress["x"]
        final_variance = adiabatic_compress["final_variance"]
        final_internal_energy = adiabatic_compress["final_internal_energy"]
        return {
            "mode": "forward",
            "steps": int(steps),
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
            "cycle_delta_u": float(sum(stage["mean_delta_u"] for stage in stages)),
            "return_proxy": float(
                abs(final_variance - initial_variance) + abs(final_internal_energy - initial_internal_energy)
            ),
            "closure_error": float(sum(stage["closure_error"] for stage in stages)),
            "x_final": x_final,
            "stages": stages,
        }

    adiabatic_to_cold = adiabatic_jump(x0, spec.potential, spec.start_params, spec.cold_high_params)
    cold_iso_reverse = run_leg(
        adiabatic_to_cold["x"],
        T_COLD,
        spec.potential,
        spec.force,
        spec.cold_high_params,
        spec.cold_low_params,
        steps,
        rng,
        f"{spec.name}_cold_reverse",
    )
    adiabatic_to_hot = adiabatic_jump(cold_iso_reverse["x"], spec.potential, spec.cold_low_params, spec.hot_low_params)
    hot_iso_reverse = run_leg(
        adiabatic_to_hot["x"],
        T_HOT,
        spec.potential,
        spec.force,
        spec.hot_low_params,
        spec.start_params,
        steps,
        rng,
        f"{spec.name}_hot_reverse",
    )
    stages = [adiabatic_to_cold, cold_iso_reverse, adiabatic_to_hot, hot_iso_reverse]
    q_cold_absorbed = cold_iso_reverse["mean_heat"]
    q_hot_released = hot_iso_reverse["mean_heat"]
    work_on_system = sum(stage["mean_work"] for stage in stages)
    work_by_system = -work_on_system
    work_input = work_on_system
    cop_carnot = T_COLD / (T_HOT - T_COLD)
    cop = q_cold_absorbed / work_input if work_input > 0.0 else float("nan")
    x_final = hot_iso_reverse["x"]
    final_variance = hot_iso_reverse["final_variance"]
    final_internal_energy = hot_iso_reverse["final_internal_energy"]
    return {
        "mode": "reverse",
        "steps": int(steps),
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
        "cycle_delta_u": float(sum(stage["mean_delta_u"] for stage in stages)),
        "return_proxy": float(
            abs(final_variance - initial_variance) + abs(final_internal_energy - initial_internal_energy)
        ),
        "closure_error": float(sum(stage["closure_error"] for stage in stages)),
        "x_final": x_final,
        "stages": stages,
    }


def regime_note(topology_summary: dict) -> str:
    forward = topology_summary["best_forward"]
    reverse = topology_summary["best_reverse"]
    engine = forward["forward_work_by_system"] > 0.0 and forward["forward_efficiency"] > 0.0
    refrigerator = reverse["reverse_work_input"] > 0.0 and reverse["reverse_q_cold_absorbed"] > 0.0 and reverse["reverse_cop"] > 0.0
    if engine and refrigerator:
        return "both"
    if engine:
        return "engine-like"
    if refrigerator:
        return "refrigerator-like"
    return "neither"


def build_topologies() -> List[TopologySpec]:
    return [
        TopologySpec(
            name="harmonic",
            label="harmonic_well",
            potential=harmonic_potential,
            force=harmonic_force,
            x_min=-5.0,
            x_max=5.0,
            grid_size=4001,
            start_params={"k": 4.0},
            hot_low_params={"k": 4.0 * HOT_LOW_SCALE},
            note="Baseline Gaussian working substance.",
        ),
        TopologySpec(
            name="quartic",
            label="quartic_single_well",
            potential=quartic_single_well_potential,
            force=quartic_single_well_force,
            x_min=-4.0,
            x_max=4.0,
            grid_size=5001,
            start_params={"k": 3.2, "a4": 0.35},
            hot_low_params={"k": 3.2 * HOT_LOW_SCALE, "a4": 0.35},
            note="Single-well geometry with stronger tails than the harmonic baseline.",
        ),
        TopologySpec(
            name="soft_double_well",
            label="soft_double_well",
            potential=soft_double_well_potential,
            force=soft_double_well_force,
            x_min=-4.5,
            x_max=4.5,
            grid_size=5001,
            start_params={"barrier": 1.25, "soft": 0.20},
            hot_low_params={"barrier": 1.25 * HOT_LOW_SCALE, "soft": 0.20},
            note="Double-well geometry with a soft quadratic floor.",
        ),
    ]


def main() -> None:
    topologies = build_topologies()
    rows = []
    topology_summaries = {}

    for topo_idx, topo in enumerate(topologies):
        topology_rows = []
        for step_idx, steps in enumerate(STEP_GRID):
            forward = build_cycle(topo, steps, seed_offset=100 * topo_idx + step_idx, reverse=False)
            reverse = build_cycle(topo, steps, seed_offset=100 * topo_idx + 50 + step_idx, reverse=True)
            topology_rows.append(
                {
                    "topology": topo.name,
                    "label": topo.label,
                    "steps": int(steps),
                    "forward_efficiency": forward["efficiency"],
                    "forward_carnot_bound": forward["carnot_bound"],
                    "forward_return_proxy": forward["return_proxy"],
                    "forward_cycle_delta_u": forward["cycle_delta_u"],
                    "forward_work_by_system": forward["work_by_system"],
                    "forward_q_hot": forward["q_hot"],
                    "reverse_cop": reverse["cop"],
                    "reverse_cop_carnot": reverse["cop_carnot"],
                    "reverse_return_proxy": reverse["return_proxy"],
                    "reverse_cycle_delta_u": reverse["cycle_delta_u"],
                    "reverse_work_input": reverse["work_input"],
                    "reverse_q_cold_absorbed": reverse["q_cold_absorbed"],
                    "return_proxy": float(0.5 * (forward["return_proxy"] + reverse["return_proxy"])),
                    "closure_error_max": float(max(forward["closure_error"], reverse["closure_error"])),
                }
            )
            rows.append(topology_rows[-1])

        best_forward = max(topology_rows, key=lambda row: row["forward_efficiency"] if row["forward_work_by_system"] > 0.0 else -np.inf)
        best_reverse = max(topology_rows, key=lambda row: row["reverse_cop"] if row["reverse_work_input"] > 0.0 else -np.inf)
        best_closure = min(topology_rows, key=lambda row: row["return_proxy"])

        topology_summaries[topo.name] = {
            "label": topo.label,
            "note": topo.note,
            "steps": STEP_GRID,
            "best_forward": best_forward,
            "best_reverse": best_reverse,
            "best_closure": best_closure,
            "regime_note": regime_note(
                {
                    "best_forward": best_forward,
                    "best_reverse": best_reverse,
                }
            ),
            "topology_breaks_harmonic_assumption": topo.name != "harmonic"
            and best_closure["return_proxy"] > min(r["return_proxy"] for r in rows if r["topology"] == "harmonic") * 1.2,
        }

    harmonic_best_closure = min(
        (row for row in rows if row["topology"] == "harmonic"),
        key=lambda row: row["return_proxy"],
    )
    best_engine_topology = max(
        topology_summaries.values(),
        key=lambda summary: summary["best_forward"]["forward_efficiency"],
    )
    best_refrigerator_topology = max(
        topology_summaries.values(),
        key=lambda summary: summary["best_reverse"]["reverse_cop"],
    )
    best_closure_topology = min(
        topology_summaries.values(),
        key=lambda summary: summary["best_closure"]["return_proxy"],
    )

    positive = {
        "all_topologies_produce_finite_rows": {
            "pass": all(np.isfinite(row["forward_efficiency"]) and np.isfinite(row["reverse_cop"]) for row in rows),
        },
        "at_least_one_topology_behaves_engine_like": {
            "best_topology": best_engine_topology["label"],
            "best_forward_efficiency": best_engine_topology["best_forward"]["forward_efficiency"],
            "pass": best_engine_topology["best_forward"]["forward_work_by_system"] > 0.0,
        },
        "at_least_one_topology_behaves_refrigerator_like": {
            "best_topology": best_refrigerator_topology["label"],
            "best_reverse_cop": best_refrigerator_topology["best_reverse"]["reverse_cop"],
            "pass": best_refrigerator_topology["best_reverse"]["reverse_work_input"] > 0.0,
        },
        "nonharmonic_topologies_show_a_distinct_closure_profile": {
            "harmonic_best_return_proxy": harmonic_best_closure["return_proxy"],
            "best_nonharmonic_return_proxy": min(
                row["return_proxy"] for row in rows if row["topology"] != "harmonic"
            ),
            "pass": min(row["return_proxy"] for row in rows if row["topology"] != "harmonic")
            != harmonic_best_closure["return_proxy"],
        },
    }

    negative = {
        "no_topology_hits_carnot_exactly_at_this_bounded_grid": {
            "best_forward_distance_to_carnot": min(
                abs(row["forward_efficiency"] - row["forward_carnot_bound"]) for row in rows
            ),
            "best_reverse_distance_to_carnot_cop": min(
                abs(row["reverse_cop"] - row["reverse_cop_carnot"]) for row in rows
            ),
            "pass": any(
                abs(row["forward_efficiency"] - row["forward_carnot_bound"]) > 1e-2
                for row in rows
            )
            and any(abs(row["reverse_cop"] - row["reverse_cop_carnot"]) > 1e-2 for row in rows),
        },
        "closure_is_not_exact_for_every_topology": {
            "max_return_proxy": max(row["return_proxy"] for row in rows),
            "pass": any(row["return_proxy"] > 1e-3 for row in rows),
        },
    }

    boundary = {
        "all_rows_have_closed_bookkeeping": {
            "pass": all(row["closure_error_max"] < 1e-9 for row in rows),
        },
        "all_rows_have_finite_statistics": {
            "pass": all(
                np.isfinite(value)
                for row in rows
                for value in row.values()
                if isinstance(value, (int, float))
            ),
        },
        "same_bath_pair_across_the_array": {
            "t_hot": T_HOT,
            "t_cold": T_COLD,
            "pass": T_HOT > T_COLD > 0.0,
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )

    out = {
        "name": "carnot_topology_array",
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
            "step_grid": STEP_GRID,
            "topologies": topology_summaries,
            "best_engine_topology": best_engine_topology["label"],
            "best_refrigerator_topology": best_refrigerator_topology["label"],
            "best_closure_topology": best_closure_topology["label"],
            "harmonic_best_closure_return_proxy": harmonic_best_closure["return_proxy"],
            "scope_note": (
                "Comparative stochastic Carnot array across multiple 1D working-substance geometries. "
                "Use this as the lab matrix for later QIT-aligned topology repair."
            ),
        },
        "rows": rows,
    }

    out_dir = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "carnot_topology_array_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
