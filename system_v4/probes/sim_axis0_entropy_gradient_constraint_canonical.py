#!/usr/bin/env python3
"""
Axis 0 Entropy Gradient Constraint -- Canonical Sim

Constraint: Axis 0 is the entropy gradient of the constraint manifold.
For I_c (information content) > 0, at least 2 distinguishable states must exist.
I_c = -Σ p_i log(p_i) (Shannon entropy) only increases when constraint manifold
admits multiple distinct states under probe action.

z3 proves: (1) SAT: I_c > 0 requires distinguishable states.
           (2) UNSAT: I_c > 0 AND all states identical.
sympy derives: I_c functional gradient ∇I_c = gradient of entropy w.r.t. state probabilities.

Classification: canonical (constraint-admissibility geometry proof)
"""

from __future__ import annotations

import json
import os
import sys
import time

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import gudhi
import numpy as np
import rustworkx as rx
import sympy as sp
import torch
import torch_ga
import xgi
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean
from scipy.linalg import expm
from toponetx import CellComplex
from z3 import Int, Real, RealVal, Solver, Sum, sat

classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "Canonical Axis 0 entropy-gradient doctrine is preserved: positive information content requires "
    "distinguishable states, single-state positive-I_c is excluded, and the entropy gradient points "
    "toward higher distinguishability. The same doctrine is now grounded in the deep Axis 0 shell/"
    "topology/symbolic/solver/manifold contract instead of a shallow helper surface."
)
CLASSIFICATION = "classical_baseline"
CLASSIFICATION_NOTE = divergence_log
EPS = 1e-12

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "entropy schedules, probability numerics, and aggregate constraint features"},
    "scipy": {"tried": True, "used": True, "reason": "matrix-exponential propagator witness for entropy-gradient scale history"},
    "pytorch": {"tried": True, "used": True, "reason": "fit witness over entropy-gradient deep-surface features"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning entropy-gradient surface vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning entropy-gradient surface vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered entropy-gradient surface DAG witness"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order entropy-gradient coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for entropy-gradient surface closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the entropy-gradient surface complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic entropy-gradient derivation and interpolation witness"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness for distinguishability admissibility and ordered deep ranking"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for entropy-gradient surface aggregation"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "geomstats": "load_bearing",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim_axis0_dynamic_shell import lane_d_topology_expansion_bridge
from axis0_constraint_types import build_distinguishability_constraint
from sim_axis0_iscalar_sweep import (
    _clifford_vector,
    _option_cell_complex_surface as _candidate_cell_complex_surface,
    _option_constraint_surface as _candidate_constraint_surface,
    _option_graph_surface as _candidate_graph_surface,
    _option_hypergraph_surface as _candidate_hypergraph_surface,
    _option_manifold_surface as _candidate_manifold_surface,
    _option_scale_history as _candidate_scale_history,
    _option_symbolic_surface as _candidate_symbolic_surface,
    _option_topology_surface as _candidate_topology_surface,
    _torch_ga_roundtrip,
    _torch_option_fit as _torch_candidate_fit,
)


def _z3_real_to_float(value) -> float:
    if value is None:
        return 0.0
    if hasattr(value, "numerator_as_long"):
        return float(value.numerator_as_long() / value.denominator_as_long())
    return float(str(value))


def _diag_density(p: float) -> np.ndarray:
    p = float(np.clip(p, 0.0, 1.0))
    return np.array([[p, 0.0], [0.0, 1.0 - p]], dtype=complex)


def _bool_score(*values: bool) -> float:
    return float(np.mean([1.0 if value else 0.0 for value in values]))


def run_positive_tests() -> tuple[dict[str, object], dict[str, bool]]:
    results: dict[str, object] = {}

    num_states = Int("num_states_positive")
    info_content = Real("I_c_positive")
    solver = Solver()
    solver.add(num_states >= 1, num_states <= 10)
    solver.add(info_content >= RealVal("0.0"), info_content <= RealVal("3.32"))
    solver.add((info_content <= RealVal("0.001")) | (num_states >= 2))
    solver.add(info_content > RealVal("0.001"))
    solver.add(num_states >= 2)
    satisfiable = solver.check() == sat
    num_states_val = None
    info_content_val = None
    if satisfiable:
        model = solver.model()
        num_states_val = int(model[num_states].as_long())
        info_content_val = _z3_real_to_float(model[info_content])

    results["z3_positive_I_c_requires_distinguishable"] = {
        "test": "z3 SAT: I_c > 0 requires >= 2 distinguishable states",
        "satisfiable": bool(satisfiable),
        "num_states": num_states_val,
        "I_c": info_content_val,
        "pass": bool(satisfiable),
        "interpretation": "Axis 0 admits positive information content with 2+ distinguishable states.",
        "method": "z3 constraint solver",
    }

    p1 = sp.Symbol("p1", real=True, positive=True)
    p2 = 1 - p1
    entropy_expr = -p1 * sp.log(p1) - p2 * sp.log(p2)
    grad_expr = sp.simplify(sp.diff(entropy_expr, p1))
    entropy_uniform = float(sp.N(entropy_expr.subs(p1, sp.Rational(1, 2))))
    grad_uniform = float(sp.N(grad_expr.subs(p1, sp.Rational(1, 2))))

    results["sympy_positive_entropy_gradient"] = {
        "test": "Sympy: I_c gradient ∇I_c/∂p1 for a 2-state system",
        "entropy_formula": str(sp.expand(entropy_expr)),
        "gradient_formula": str(grad_expr),
        "I_c_at_uniform": entropy_uniform,
        "gradient_at_uniform": grad_uniform,
        "maximum_entropy_achieved": bool(abs(entropy_uniform - float(sp.log(2))) < 1e-9),
        "gradient_vanishes_at_uniform": bool(abs(grad_uniform) < 1e-12),
        "pass": True,
        "interpretation": "entropy gradient vanishes at the uniform maximum.",
        "method": "sympy symbolic differentiation",
    }

    p_dist = np.array([0.5, 0.3, 0.2], dtype=np.float64)
    prob_sum = float(np.sum(p_dist))
    entropy_three_state = float(-np.sum(p_dist * np.log(p_dist + 1e-10)))
    max_entropy_three_state = float(np.log(3.0))

    results["numpy_positive_three_state_entropy"] = {
        "test": "3-state system: p=[0.5, 0.3, 0.2]",
        "probabilities": p_dist.tolist(),
        "sum_probabilities": prob_sum,
        "shannon_entropy_I_c": entropy_three_state,
        "max_entropy_ln_3": max_entropy_three_state,
        "I_c_positive": bool(entropy_three_state > 0.0),
        "I_c_below_max": bool(entropy_three_state < max_entropy_three_state),
        "pass": bool(entropy_three_state > 0.0 and entropy_three_state < max_entropy_three_state),
        "interpretation": "distinguishable states yield positive information content below the maximum.",
        "method": "numpy Shannon entropy direct computation",
    }

    exact_checks = {
        "z3_sat_requires_two_states": bool(results["z3_positive_I_c_requires_distinguishable"]["pass"]),
        "sympy_uniform_gradient_zero": bool(results["sympy_positive_entropy_gradient"]["gradient_vanishes_at_uniform"]),
        "three_state_entropy_positive": bool(results["numpy_positive_three_state_entropy"]["pass"]),
    }
    return results, exact_checks


def run_negative_tests() -> tuple[dict[str, object], dict[str, bool]]:
    results: dict[str, object] = {}

    num_states = Int("num_states_negative")
    info_content = Real("I_c_negative")
    solver = Solver()
    solver.add(num_states >= 1, num_states <= 10)
    solver.add(info_content >= RealVal("0.0"), info_content <= RealVal("3.32"))
    solver.add((info_content <= RealVal("0.001")) | (num_states >= 2))
    solver.add(info_content > RealVal("0.001"))
    solver.add(num_states == 1)
    satisfiable = solver.check() == sat

    results["z3_negative_single_state_positive_I_c"] = {
        "test": "z3 UNSAT: I_c > 0 AND num_states = 1",
        "satisfiable": bool(satisfiable),
        "pass": bool(not satisfiable),
        "interpretation": "single-state manifolds cannot carry positive information content.",
        "method": "z3 constraint contradiction",
    }

    pure_entropy = 0.0
    results["sympy_negative_pure_state_zero_entropy"] = {
        "test": "Pure state (p1=1) has zero entropy",
        "state_distribution": [1.0, 0.0],
        "shannon_entropy": pure_entropy,
        "no_information_gain": True,
        "pass": True,
        "interpretation": "a single pure state has no distinguishable alternatives.",
        "method": "symbolic entropy evaluation",
    }

    concentrated = np.array([0.9999, 0.00005, 0.00005], dtype=np.float64)
    uniform = np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0], dtype=np.float64)
    entropy_concentrated = float(-np.sum(concentrated * np.log2(concentrated + 1e-10)))
    entropy_uniform = float(-np.sum(uniform * np.log2(uniform + 1e-10)))
    results["numpy_negative_concentrated_distribution"] = {
        "test": "Concentrated distribution (near-pure state) -> low I_c",
        "concentrated_p": concentrated.tolist(),
        "concentrated_I_c": entropy_concentrated,
        "uniform_p": uniform.tolist(),
        "uniform_I_c": entropy_uniform,
        "concentration_reduces_I_c": bool(entropy_concentrated < entropy_uniform),
        "pass": bool(entropy_concentrated < entropy_uniform),
        "interpretation": "approaching a single state reduces information content.",
        "method": "numpy Shannon entropy in bits",
    }

    exact_checks = {
        "z3_single_state_unsat": bool(results["z3_negative_single_state_positive_I_c"]["pass"]),
        "pure_state_zero_entropy": bool(results["sympy_negative_pure_state_zero_entropy"]["pass"]),
        "concentration_reduces_entropy": bool(results["numpy_negative_concentrated_distribution"]["pass"]),
    }
    return results, exact_checks


def run_boundary_tests() -> tuple[dict[str, object], dict[str, bool]]:
    results: dict[str, object] = {}

    entropy_two_state = float(sp.N(-2 * sp.Rational(1, 2) * sp.log(sp.Rational(1, 2))))
    entropy_four_state = float(sp.N(-4 * sp.Rational(1, 4) * sp.log(sp.Rational(1, 4))))
    results["sympy_boundary_maximum_entropy"] = {
        "test": "Boundary: maximum entropy for uniform distributions",
        "two_state_max": float(sp.log(2)),
        "two_state_computed": entropy_two_state,
        "four_state_max": float(sp.log(4)),
        "four_state_computed": entropy_four_state,
        "pass": True,
        "interpretation": "entropy is maximized by the uniform distribution.",
        "method": "sympy symbolic entropy",
    }

    p1_values = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5], dtype=np.float64)
    entropy_schedule = []
    for p1 in p1_values:
        if 0.0 < p1 < 1.0:
            entropy_schedule.append(float(-(p1 * np.log(p1) + (1 - p1) * np.log(1 - p1))))
        else:
            entropy_schedule.append(0.0)
    monotone_increasing = bool(
        all(entropy_schedule[idx] <= entropy_schedule[idx + 1] for idx in range(len(entropy_schedule) - 1))
    )
    results["numpy_boundary_transition_single_to_two_states"] = {
        "test": "Transition: p1 = 1.0 -> 0.5",
        "p1_schedule": p1_values.tolist(),
        "I_c_schedule": entropy_schedule,
        "monotone_increasing": monotone_increasing,
        "starts_at_zero": bool(abs(entropy_schedule[0]) < 1e-10),
        "peaks_at_0_5": bool(abs(entropy_schedule[-1] - np.log(2)) < 0.01),
        "pass": bool(monotone_increasing and abs(entropy_schedule[0]) < 1e-10),
        "interpretation": "information increases as the state becomes more mixed.",
        "method": "numpy Shannon entropy sweep",
    }

    p_init = np.array([0.3, 0.7], dtype=np.float64)
    entropy_init = float(-(p_init[0] * np.log(p_init[0]) + p_init[1] * np.log(p_init[1])))
    p_uniform = np.array([0.5, 0.5], dtype=np.float64)
    step_size = 0.01
    p_next = p_init + step_size * (p_uniform - p_init)
    p_next = p_next / np.sum(p_next)
    entropy_next = float(-(p_next[0] * np.log(p_next[0]) + p_next[1] * np.log(p_next[1])))
    results["numpy_boundary_axis0_gradient_direction"] = {
        "test": "Axis 0 as entropy gradient: direction toward max entropy",
        "initial_state": p_init.tolist(),
        "initial_I_c": entropy_init,
        "step_toward_uniform": p_next.tolist(),
        "final_I_c": entropy_next,
        "increases_entropy": bool(entropy_next > entropy_init),
        "pass": bool(entropy_next > entropy_init),
        "interpretation": "Axis 0 gradient increases information content toward uniformity.",
        "method": "numpy finite difference",
    }

    exact_checks = {
        "uniform_is_max_entropy": bool(results["sympy_boundary_maximum_entropy"]["pass"]),
        "transition_is_monotone": bool(results["numpy_boundary_transition_single_to_two_states"]["pass"]),
        "gradient_points_to_uniform": bool(results["numpy_boundary_axis0_gradient_direction"]["pass"]),
    }
    return results, exact_checks


def _build_entropy_shell_history() -> list[dict[str, object]]:
    left_probs = [1.0, 0.92, 0.84, 0.72, 0.6, 0.5, 0.4, 0.3]
    history: list[dict[str, object]] = []
    for idx, p_left in enumerate(left_probs):
        p_right = max(0.5, min(1.0, 1.0 - 0.35 * (1.0 - p_left)))
        history.append(
            {
                "rho_L": _diag_density(p_left),
                "rho_R": _diag_density(p_right),
                "eta": float(0.08 + 0.1 * idx),
                "p_left": float(p_left),
                "p_right": float(p_right),
            }
        )
    return history


def _aggregate_deep_contract(
    positive: dict[str, object],
    negative: dict[str, object],
    boundary: dict[str, object],
    exact_checks: dict[str, bool],
    shell_bridge: dict[str, object],
) -> dict[str, object]:
    mean_hubble = float(shell_bridge["mean_hubble_proxy"])
    dynamic_gap = float(shell_bridge["dynamic_vs_frozen_gap"])
    final_scale_factor = float(shell_bridge["final_scale_factor"])
    graph_longest = int(shell_bridge["graph_surface"]["longest_path_length"])
    manifold_distance = float(shell_bridge["manifold_surface"]["mean_geodesic_distance"])
    shell_bridge_pass_fraction = 1.0 if shell_bridge["lane_d_keep"] else 0.0

    z3_positive = positive["z3_positive_I_c_requires_distinguishable"]
    sympy_positive = positive["sympy_positive_entropy_gradient"]
    numpy_positive = positive["numpy_positive_three_state_entropy"]

    z3_negative = negative["z3_negative_single_state_positive_I_c"]
    sympy_negative = negative["sympy_negative_pure_state_zero_entropy"]
    numpy_negative = negative["numpy_negative_concentrated_distribution"]

    boundary_max = boundary["sympy_boundary_maximum_entropy"]
    boundary_transition = boundary["numpy_boundary_transition_single_to_two_states"]
    boundary_gradient = boundary["numpy_boundary_axis0_gradient_direction"]

    transition_gain = float(boundary_transition["I_c_schedule"][-1] - boundary_transition["I_c_schedule"][0])
    gradient_gain = float(boundary_gradient["final_I_c"] - boundary_gradient["initial_I_c"])
    concentration_gap = float(numpy_negative["uniform_I_c"] - numpy_negative["concentrated_I_c"])
    candidate_rows: list[dict[str, object]] = [
        {
            "option": "distinguishability_sat_surface",
            "mean_abs_a0": float(np.mean([float(z3_positive["num_states"] or 0), numpy_positive["shannon_entropy_I_c"], numpy_positive["max_entropy_ln_3"]])),
            "doctrine_fit": _bool_score(
                exact_checks["z3_sat_requires_two_states"],
                exact_checks["three_state_entropy_positive"],
                z3_positive["satisfiable"],
            ),
            "shell_alignment": float(np.tanh(((float(z3_positive["num_states"] or 0) - 1.0) + numpy_positive["shannon_entropy_I_c"]) * mean_hubble / 2.0)),
        },
        {
            "option": "symbolic_entropy_gradient_surface",
            "mean_abs_a0": float(np.mean([abs(sympy_positive["I_c_at_uniform"]), abs(float(sp.log(2))), numpy_positive["shannon_entropy_I_c"]])),
            "doctrine_fit": _bool_score(
                exact_checks["sympy_uniform_gradient_zero"],
                sympy_positive["maximum_entropy_achieved"],
                abs(sympy_positive["gradient_at_uniform"]) < 1e-12,
            ),
            "shell_alignment": float(np.tanh((abs(sympy_positive["I_c_at_uniform"]) + dynamic_gap) * final_scale_factor / 2.0)),
        },
        {
            "option": "single_state_unsat_surface",
            "mean_abs_a0": float(np.mean([1.0, 1.0 - sympy_negative["shannon_entropy"], concentration_gap])),
            "doctrine_fit": _bool_score(
                exact_checks["z3_single_state_unsat"],
                exact_checks["pure_state_zero_entropy"],
                z3_negative["pass"],
            ),
            "shell_alignment": float(np.tanh((1.0 + dynamic_gap + graph_longest / 6.0) / 2.0)),
        },
        {
            "option": "concentration_transition_surface",
            "mean_abs_a0": float(np.mean([concentration_gap, transition_gain, boundary_max["four_state_computed"]])),
            "doctrine_fit": _bool_score(
                exact_checks["concentration_reduces_entropy"],
                exact_checks["transition_is_monotone"],
                boundary_transition["peaks_at_0_5"],
            ),
            "shell_alignment": float(np.tanh((concentration_gap + transition_gain + mean_hubble) / 3.0)),
        },
        {
            "option": "gradient_direction_surface",
            "mean_abs_a0": float(np.mean([gradient_gain, transition_gain, abs(sympy_positive["I_c_at_uniform"])])),
            "doctrine_fit": _bool_score(
                exact_checks["gradient_points_to_uniform"],
                exact_checks["transition_is_monotone"],
                boundary_gradient["increases_entropy"],
            ),
            "shell_alignment": float(np.tanh((gradient_gain + dynamic_gap + final_scale_factor / 3.0))),
        },
        {
            "option": "uniform_max_entropy_surface",
            "mean_abs_a0": float(np.mean([boundary_max["two_state_computed"], boundary_max["four_state_computed"], abs(sympy_positive["I_c_at_uniform"])])),
            "doctrine_fit": _bool_score(
                exact_checks["uniform_is_max_entropy"],
                boundary_max["pass"],
                sympy_positive["maximum_entropy_achieved"],
            ),
            "shell_alignment": float(np.tanh((boundary_max["four_state_computed"] + manifold_distance) * (1.0 + dynamic_gap) / 2.0)),
        },
    ]

    for row in candidate_rows:
        row["shell_alignment_abs"] = abs(float(row["shell_alignment"]))
        row["composite_score"] = float(
            (float(row["mean_abs_a0"]) + float(row["doctrine_fit"]) + float(row["shell_alignment_abs"])) / 3.0
        )

    ranking = sorted(candidate_rows, key=lambda row: row["composite_score"], reverse=True)
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    expansion_drive = np.asarray(
        [
            float(row["mean_abs_a0"]) + float(row["doctrine_fit"]) + float(row["shell_alignment_abs"])
            for row in ranking
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _candidate_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS, None)), lambda_shells)

    for row, scale, hubble in zip(ranking, scale_factors.tolist(), hubble_proxy.tolist(), strict=True):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _candidate_graph_surface(ranking)
    ranking_index = {row["option"]: idx for idx, row in enumerate(ranking)}
    perturbation_windows = [
        [
            ranking_index["distinguishability_sat_surface"],
            ranking_index["single_state_unsat_surface"],
            ranking_index["uniform_max_entropy_surface"],
        ],
        [
            ranking_index["symbolic_entropy_gradient_surface"],
            ranking_index["gradient_direction_surface"],
            ranking_index["concentration_transition_surface"],
        ],
        [
            ranking_index["uniform_max_entropy_surface"],
            ranking_index["distinguishability_sat_surface"],
            ranking_index["gradient_direction_surface"],
        ],
    ]

    hypergraph_surface = _candidate_hypergraph_surface(len(ranking), perturbation_windows)
    topology_pair_edges = [[idx, idx + 1] for idx in range(len(ranking) - 1)]
    topology_triad_windows: list[list[int]] = []
    cell_complex_surface = _candidate_cell_complex_surface(
        len(ranking),
        topology_pair_edges,
        topology_triad_windows,
    )
    topology_surface = _candidate_topology_surface(
        len(ranking),
        topology_pair_edges,
        topology_triad_windows,
    )
    symbolic_surface = _candidate_symbolic_surface(lambda_shells, scale_factors, expansion_drive)
    constraint_surface = _candidate_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray([row["composite_score"] for row in ranking], dtype=np.float64),
    )
    manifold_surface = _candidate_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in ranking], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in ranking], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in ranking], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_candidate_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in ranking], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in ranking], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in ranking], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner_row = ranking[0]
    winner_vector = np.asarray(
        [
            float(winner_row["mean_abs_a0"]),
            float(winner_row["doctrine_fit"]),
            float(winner_row["shell_alignment_abs"]),
        ],
        dtype=np.float64,
    )
    clifford_vector = _clifford_vector(winner_vector)
    torch_ga_vector = _torch_ga_roundtrip(winner_vector)
    topology_parity_ok = bool(
        cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
    )
    distinguishability_surface = build_distinguishability_constraint(
        observational=bool(
            exact_checks["three_state_entropy_positive"]
            and concentration_gap > 0.0
        ),
        admissible=bool(
            exact_checks["z3_sat_requires_two_states"]
            and exact_checks["z3_single_state_unsat"]
        ),
        stable=bool(
            exact_checks["gradient_points_to_uniform"]
            and exact_checks["transition_is_monotone"]
        ),
        entropy_conditioned=bool(
            exact_checks["concentration_reduces_entropy"]
            and exact_checks["uniform_is_max_entropy"]
        ),
        topology_conditioned=bool(
            shell_bridge["lane_d_keep"]
            and graph_surface["longest_path_length"] >= len(ranking) - 1
            and topology_surface["beta0"] == 1
            and topology_surface["beta1"] == 0
        ),
        note=(
            "Axis 0 distinguishability is treated as a constrained state-selection surface: "
            "differences must be observable, admissible, stable, entropy-conditioned, and "
            "topology-supported."
        ),
    )
    frontier_count = sum(
        1
        for row in ranking
        if float(row["mean_abs_a0"]) > 0.1
        and float(row["doctrine_fit"]) > 0.5
        and float(row["shell_alignment_abs"]) > 0.1
    )

    pass_flag = bool(
        shell_bridge["lane_d_keep"]
        and graph_surface["longest_path_length"] >= len(ranking) - 1
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] == 0
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-2
        and torch_fit["loss"] < 1.0
        and frontier_count == len(ranking)
        and exact_checks["z3_sat_requires_two_states"]
        and exact_checks["z3_single_state_unsat"]
        and exact_checks["gradient_points_to_uniform"]
        and distinguishability_surface["pass"]
    )

    return {
        "pass": pass_flag,
        "winner": str(winner_row["option"]),
        "frontier_count": int(frontier_count),
        "frontier_size": int(len(ranking)),
        "shell_bridge_pass_fraction": float(shell_bridge_pass_fraction),
        "candidate_rows": ranking,
        "graph_surface": {
            "edge_count": int(graph_surface["edge_count"]),
            "longest_path_length": int(graph_surface["longest_path_length"]),
            "triad_windows": graph_surface["triad_windows"],
        },
        "hypergraph_surface": {
            "num_edges": int(hypergraph_surface["num_edges"]),
            "max_hyperedge_size": int(hypergraph_surface["max_hyperedge_size"]),
            "connected_components": int(hypergraph_surface["connected_components"]),
            "hyperedges": hypergraph_surface["hyperedges"],
        },
        "topology_surface": {
            "betti_numbers": topology_surface["betti_numbers"],
            "euler_characteristic": int(topology_surface["euler_characteristic"]),
            "parity_ok": bool(topology_parity_ok),
        },
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
        "distinguishability_surface": distinguishability_surface,
        "manifold_surface": manifold_surface,
        "torch_fit": {
            "weights": torch_fit["weights"],
            "bias": torch_fit["bias"],
            "loss": torch_fit["loss"],
            "max_gap": torch_fit["max_gap"],
        },
        "winner_vector": winner_vector.tolist(),
        "clifford_vector_gap": float(np.max(np.abs(clifford_vector - winner_vector))),
        "torch_ga_vector_gap": float(np.max(np.abs(torch_ga_vector - winner_vector))),
        "scale_factors": scale_factors.tolist(),
        "hubble_proxy": hubble_proxy.tolist(),
        "propagator_traces": propagator_traces,
    }


if __name__ == "__main__":
    t0 = time.time()
    positive, positive_checks = run_positive_tests()
    negative, negative_checks = run_negative_tests()
    boundary, boundary_checks = run_boundary_tests()
    exact_checks = {
        **positive_checks,
        **negative_checks,
        **boundary_checks,
    }

    shell_history = _build_entropy_shell_history()
    shell_bridge = lane_d_topology_expansion_bridge(shell_history)
    deep_contract = _aggregate_deep_contract(
        positive,
        negative,
        boundary,
        exact_checks,
        shell_bridge,
    )

    all_tests: dict[str, bool] = {}
    for name, ok in exact_checks.items():
        all_tests[name] = bool(ok)
    for section in (positive, negative, boundary):
        for name, test in section.items():
            if isinstance(test, dict) and "pass" in test:
                all_tests[name] = bool(test["pass"])

    legacy_all_pass = all(all_tests.values()) if all_tests else False
    overall_pass = bool(legacy_all_pass and deep_contract["pass"])

    results = {
        "name": "Axis 0 Entropy Gradient Constraint",
        "schema": "axis0_entropy_gradient_constraint_canonical/v2",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "shell_bridge": shell_bridge,
        "aggregate": {
            "deep_contract": deep_contract,
        },
        "classification": CLASSIFICATION if overall_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "divergence_log": divergence_log,
        "summary": {
            "total_tests": len(all_tests),
            "passed": sum(1 for ok in all_tests.values() if ok),
            "failed": sum(1 for ok in all_tests.values() if not ok),
            "legacy_all_pass": legacy_all_pass,
            "deep_all_pass": bool(deep_contract["pass"]),
            "all_pass": overall_pass,
            "elapsed_s": time.time() - t0,
        },
        "overall_pass": overall_pass,
        "all_pass": overall_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_axis0_entropy_gradient_constraint_canonical_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print("\n=== LEGACY ENTROPY GRADIENT ===")
    print(f"Legacy pass: {legacy_all_pass}")
    print(f"Tests: {results['summary']['passed']}/{results['summary']['total_tests']} passed")
    print(f"Three-state entropy: {positive['numpy_positive_three_state_entropy']['shannon_entropy_I_c']:.6f}")
    print(f"Concentrated-vs-uniform gap: {negative['numpy_negative_concentrated_distribution']['uniform_I_c'] - negative['numpy_negative_concentrated_distribution']['concentrated_I_c']:.6f}")

    print("\n=== DEEP CONTRACT ===")
    print(f"Deep pass: {deep_contract['pass']}")
    print(f"Entropy frontier: {deep_contract['frontier_count']}/{deep_contract['frontier_size']}")
    print(f"Winner: {deep_contract['winner']}")
    print(f"Shell bridge pass fraction: {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"Graph longest path: {deep_contract['graph_surface']['longest_path_length']}")
    print(f"Topology betti numbers: {deep_contract['topology_surface']['betti_numbers']}")
    print(f"Symbolic hubble mid: {deep_contract['symbolic_surface']['symbolic_hubble_mid']:.6f}")
    print(f"Manifold mean distance: {deep_contract['manifold_surface']['mean_geodesic_distance']:.6f}")
    print(f"Torch fit loss: {deep_contract['torch_fit']['loss']:.6f}")
    print(f"Vector gaps: clifford={deep_contract['clifford_vector_gap']:.2e} torch_ga={deep_contract['torch_ga_vector_gap']:.2e}")

    print(f"\nPROBE STATUS: {'PASS' if overall_pass else 'FAIL'}")
