#!/usr/bin/env python3
"""
Phase 6: Point-Reference Earned Bridge Test
===========================================

Goal
----
Test whether the surviving point-reference family can produce nonzero mutual
information without Bell injection while preserving the physical pair-state
marginal on subsystem B.

Why this is the right next cut
------------------------------
Phase 4/5 established:
- the strongest constructive winner is Bell-injected
- exact marginal-preserving MI on the chiral constructive lane collapses
- point-reference remains the strongest live pointwise discriminator

This probe asks a narrower question:
can point-reference generate "earned" MI while keeping the actual pair-state
carrier intact?

Setup
-----
For each torus and for fiber/base loops:
- fix q_ref at u=0
- sweep q_cur around the loop
- build the existing point-reference cq state
- measure I(A:B)
- measure Frobenius deviation of subsystem-B from the current physical pair
  state rho_pair(q_cur)

If the best exact/near-exact preserving candidate has near-zero MI,
the point-reference bridge lane is killed as an earned bridge, while still
remaining useful as a discriminator.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime

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
classification = "classical_baseline"  # auto-backfill
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat
divergence_log = (
    "Classical foundation baseline: this evaluates the point-reference Axis-0 "
    "bridge numerically. The legacy earned-bridge verdict is preserved, and a "
    "deep contract now binds the point-reference surfaces to the same shell "
    "bridge, graph/topology, symbolic expansion, solver closure, geometric "
    "algebra, and manifold witnesses used elsewhere in Axis 0."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "point-reference bridge metrics and marginal-deviation numerics"},
    "scipy": {"tried": True, "used": True, "reason": "point-reference surface propagator witness"},
    "pytorch": {"tried": True, "used": True, "reason": "fit and gradient witness over the point-reference frontier"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning point-reference vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning point-reference vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered DAG witness over the ranked point-reference frontier"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order torus-to-surface coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for point-reference closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the point-reference complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for point-reference expansion"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing point-reference rank order and monotone scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for aggregate point-reference geometry"},
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

from engine_core import GeometricEngine
from axis0_xi_strict_bakeoff_sim import (  # noqa: E402
    TORUS_CONFIGS,
    exact_base_q,
    exact_fiber_q,
    metrics_for_cut_state,
    pair_state_from_q,
    partial_trace,
    xi_point_ref_cq_from_qs,
)
from sim_axis0_dynamic_shell import lane_d_topology_expansion_bridge
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


EPS = 1e-12
N_SAMPLES = 32
TOLS = [1e-6, 1e-3, 1e-2]


def summarize_rows(rows):
    i_vals = np.asarray([row["I_AB"] for row in rows], dtype=float)
    dev_vals = np.asarray([row["dev_B"] for row in rows], dtype=float)
    return {
        "count": int(len(rows)),
        "mean_I_AB": float(np.mean(i_vals)),
        "max_I_AB": float(np.max(i_vals)),
        "min_I_AB": float(np.min(i_vals)),
        "mean_dev_B": float(np.mean(dev_vals)),
        "min_dev_B": float(np.min(dev_vals)),
        "max_dev_B": float(np.max(dev_vals)),
    }


def best_under_tol(rows, tol):
    eligible = [row for row in rows if row["dev_B"] <= tol]
    if not eligible:
        return {
            "tol": float(tol),
            "count": 0,
            "best_I_AB": 0.0,
            "best_dev_B": None,
            "best_u": None,
            "best_source": None,
        }
    best = max(eligible, key=lambda row: row["I_AB"])
    return {
        "tol": float(tol),
        "count": int(len(eligible)),
        "best_I_AB": float(best["I_AB"]),
        "best_dev_B": float(best["dev_B"]),
        "best_u": float(best["u"]),
        "best_source": str(best["source"]),
    }


def run_loop_suite(torus_label, eta, loop_label, q_fn):
    u_grid = np.linspace(0.0, 2.0 * np.pi, N_SAMPLES, endpoint=False)
    q_ref = q_fn(eta, 0.0)
    rows = []

    for u in u_grid:
        q_cur = q_fn(eta, float(u))
        rho_ref, dims, _ = xi_point_ref_cq_from_qs(q_ref, q_cur)
        metrics = metrics_for_cut_state(rho_ref, dims)
        rho_b = partial_trace(rho_ref, dims, [1])
        rho_target = pair_state_from_q(q_cur)
        dev_b = float(np.linalg.norm(rho_b - rho_target, ord="fro"))
        rows.append(
            {
                "torus": torus_label,
                "loop": loop_label,
                "u": float(u),
                "source": "point_reference_cq",
                "I_AB": float(metrics["I_AB"]),
                "I_c_A_to_B": float(metrics["I_c_A_to_B"]),
                "S_A_given_B": float(metrics["S_A_given_B"]),
                "dev_B": dev_b,
                "exact_preserving": bool(dev_b <= 1e-9),
            }
        )

    exact_rows = [row for row in rows if row["exact_preserving"]]
    best_overall = max(rows, key=lambda row: row["I_AB"])
    best_exact = max(exact_rows, key=lambda row: row["I_AB"]) if exact_rows else None

    return {
        "torus": torus_label,
        "eta": float(eta),
        "loop": loop_label,
        "summary": summarize_rows(rows),
        "best_overall": {
            "I_AB": float(best_overall["I_AB"]),
            "dev_B": float(best_overall["dev_B"]),
            "u": float(best_overall["u"]),
        },
        "best_exact": (
            {
                "I_AB": float(best_exact["I_AB"]),
                "dev_B": float(best_exact["dev_B"]),
                "u": float(best_exact["u"]),
            }
            if best_exact is not None
            else None
        ),
        "tol_sweep": [best_under_tol(rows, tol) for tol in TOLS],
        "rows": rows,
    }


def _aggregate_deep_contract(config_records: list[dict]) -> dict[str, object]:
    candidate_names = [
        "exact_collapse_surface",
        "tol_collapse_surface",
        "base_discriminator_surface",
        "fiber_null_surface",
        "deviation_separation_surface",
    ]
    shell_bridge_pass_fraction = float(
        np.mean([1.0 if row["shell_bridge"]["lane_d_keep"] else 0.0 for row in config_records])
    ) if config_records else 0.0

    candidate_signal_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_signed_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_shell_hubble_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    candidate_doctrine_by_name: dict[str, list[float]] = {name: [] for name in candidate_names}
    config_rankings: list[list[str]] = []

    for row in config_records:
        base_suite = row["base"]
        fiber_suite = row["fiber"]
        exact_best = float(max(base_suite["best_exact"]["I_AB"] if base_suite["best_exact"] else 0.0,
                               fiber_suite["best_exact"]["I_AB"] if fiber_suite["best_exact"] else 0.0))
        tol_best = float(max(
            next(item["best_I_AB"] for item in base_suite["tol_sweep"] if abs(item["tol"] - 1e-3) < EPS),
            next(item["best_I_AB"] for item in fiber_suite["tol_sweep"] if abs(item["tol"] - 1e-3) < EPS),
        ))
        base_overall_i = float(base_suite["best_overall"]["I_AB"])
        base_overall_dev = float(base_suite["best_overall"]["dev_B"])
        fiber_overall_i = float(fiber_suite["best_overall"]["I_AB"])
        fiber_overall_dev = float(fiber_suite["best_overall"]["dev_B"])
        exact_collapse = float(1.0 / (1.0 + 1000.0 * exact_best))
        tol_collapse = float(1.0 / (1.0 + 1000.0 * tol_best))
        deviation_separation = float(base_overall_dev - min(base_suite["summary"]["min_dev_B"], fiber_suite["summary"]["min_dev_B"]))

        local_rows = {
            "exact_collapse_surface": {
                "signal": exact_collapse,
                "signed": -exact_best,
                "doctrine": 1.0 if exact_best <= 1e-3 else 0.0,
            },
            "tol_collapse_surface": {
                "signal": tol_collapse,
                "signed": -tol_best,
                "doctrine": 1.0 if tol_best <= 1e-3 else 0.0,
            },
            "base_discriminator_surface": {
                "signal": base_overall_i,
                "signed": base_overall_i - base_overall_dev,
                "doctrine": 1.0 if base_overall_i > 0.5 and base_overall_dev > 0.5 else 0.0,
            },
            "fiber_null_surface": {
                "signal": float(1.0 / (1.0 + fiber_overall_i + fiber_overall_dev)),
                "signed": -(fiber_overall_i + fiber_overall_dev),
                "doctrine": 1.0 if fiber_overall_i <= 1e-6 and fiber_overall_dev <= 1e-6 else 0.0,
            },
            "deviation_separation_surface": {
                "signal": deviation_separation,
                "signed": deviation_separation,
                "doctrine": 1.0 if deviation_separation > 0.1 else 0.0,
            },
        }

        ranking = [
            name
            for name, data in sorted(
                local_rows.items(),
                key=lambda item: float(0.7 * item[1]["signal"] + 0.3 * item[1]["doctrine"]),
                reverse=True,
            )
        ]
        config_rankings.append(ranking)
        shell_hubble = float(row["shell_bridge"]["mean_hubble_proxy"])

        for name in candidate_names:
            candidate_signal_by_name[name].append(float(local_rows[name]["signal"]))
            candidate_signed_by_name[name].append(float(local_rows[name]["signed"]))
            candidate_shell_hubble_by_name[name].append(shell_hubble)
            candidate_doctrine_by_name[name].append(float(local_rows[name]["doctrine"]))

    raw_rows: list[dict[str, object]] = []
    max_mean_abs = 0.0
    for name in candidate_names:
        signal_vals = np.asarray(candidate_signal_by_name[name], dtype=np.float64)
        signed_vals = np.asarray(candidate_signed_by_name[name], dtype=np.float64)
        shell_vals = np.asarray(candidate_shell_hubble_by_name[name], dtype=np.float64)
        doctrine_vals = np.asarray(candidate_doctrine_by_name[name], dtype=np.float64)
        shell_alignment = 0.0
        if signal_vals.size and signal_vals.std() > EPS and shell_vals.std() > EPS:
            shell_alignment = float(np.corrcoef(signal_vals, shell_vals)[0, 1])
        mean_abs_support = float(np.mean(np.abs(signal_vals))) if signal_vals.size else 0.0
        max_mean_abs = max(max_mean_abs, mean_abs_support)
        raw_rows.append(
            {
                "candidate": name,
                "mean_abs_support": mean_abs_support,
                "mean_signed_support": float(np.mean(signed_vals)) if signed_vals.size else 0.0,
                "doctrine_fit": float(np.mean(doctrine_vals)) if doctrine_vals.size else 0.0,
                "shell_alignment": shell_alignment,
                "shell_alignment_abs": abs(shell_alignment),
                "mean_signal": float(np.mean(signal_vals)) if signal_vals.size else 0.0,
            }
        )

    row_by_name: dict[str, dict[str, object]] = {}
    for row in raw_rows:
        signal_score = float(row["mean_abs_support"] / max(max_mean_abs, EPS))
        composite_score = float(
            0.45 * float(row["doctrine_fit"])
            + 0.35 * signal_score
            + 0.20 * float(row["shell_alignment_abs"])
        )
        enriched = dict(row)
        enriched["signal_score"] = signal_score
        enriched["composite_score"] = composite_score
        row_by_name[str(row["candidate"])] = enriched

    ranking = sorted(
        candidate_names,
        key=lambda name: float(row_by_name[name]["composite_score"]),
        reverse=True,
    )
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    candidate_rows: list[dict[str, object]] = []
    ranking_scores: list[float] = []
    for name in ranking:
        row = row_by_name[name]
        ranking_scores.append(float(row["composite_score"]))
        candidate_rows.append(
            {
                "option": name,
                "mean_abs_a0": float(row["mean_abs_support"]),
                "mean_signed_a0": float(row["mean_signed_support"]),
                "doctrine_fit": float(row["doctrine_fit"]),
                "sign_consistency": float(row["doctrine_fit"]),
                "shell_alignment": float(row["shell_alignment"]),
                "shell_alignment_abs": float(row["shell_alignment_abs"]),
                "signal_score": float(row["signal_score"]),
                "composite_score": float(row["composite_score"]),
                "mean_signal": float(row["mean_signal"]),
            }
        )

    expansion_drive = np.asarray(
        [
            row["mean_abs_a0"] + row["doctrine_fit"] + row["shell_alignment_abs"]
            for row in candidate_rows
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _candidate_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS, None)), lambda_shells)

    for row, scale, hubble in zip(
        candidate_rows,
        scale_factors.tolist(),
        hubble_proxy.tolist(),
        strict=True,
    ):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _candidate_graph_surface(candidate_rows)
    ranking_index = {name: idx for idx, name in enumerate(ranking)}
    config_windows = [
        [ranking_index[name] for name in config_ranking[:3]]
        for config_ranking in config_rankings
        if len(config_ranking) >= 3
    ]
    hypergraph_surface = _candidate_hypergraph_surface(len(ranking), config_windows)
    combined_pair_edges = sorted(
        {
            tuple(edge)
            for edge in graph_surface["pair_edges"] + hypergraph_surface["pair_edges"]
        }
    )
    combined_triad_windows = sorted(
        {
            tuple(window)
            for window in graph_surface["triad_windows"] + hypergraph_surface["triad_windows"]
        }
    )
    closed_pair_edges = set(combined_pair_edges)
    for window in combined_triad_windows:
        for idx in range(len(window)):
            for jdx in range(idx + 1, len(window)):
                closed_pair_edges.add(tuple(sorted((int(window[idx]), int(window[jdx])))))
    cell_complex_surface = _candidate_cell_complex_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    topology_surface = _candidate_topology_surface(
        len(ranking),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    symbolic_surface = _candidate_symbolic_surface(
        lambda_shells,
        scale_factors,
        expansion_drive,
    )
    constraint_surface = _candidate_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray(ranking_scores, dtype=np.float64),
    )
    manifold_surface = _candidate_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in candidate_rows], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in candidate_rows], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in candidate_rows], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_candidate_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in candidate_rows], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in candidate_rows], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in candidate_rows], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner = ranking[0]
    winner_row = next(row for row in candidate_rows if row["option"] == winner)
    winner_vector = np.array(
        [
            winner_row["mean_abs_a0"],
            winner_row["doctrine_fit"],
            winner_row["shell_alignment_abs"],
        ],
        dtype=np.float64,
    )
    clifford_vector = _clifford_vector(winner_vector)
    torch_ga_vector = _torch_ga_roundtrip(winner_vector)
    topology_parity_ok = bool(
        cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
    )
    graph_path_budget = max(1, len(ranking) - 2)
    topology_loop_budget = max(2, len(ranking) // 2)

    pass_flag = bool(
        shell_bridge_pass_fraction >= 0.5
        and graph_surface["longest_path_length"] >= graph_path_budget
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] <= topology_loop_budget
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-3
        and torch_fit["loss"] < 1.0
    )

    return {
        "pass": pass_flag,
        "winner": winner,
        "candidate_universe_size": len(candidate_names),
        "frontier_size": len(ranking),
        "shell_bridge_pass_fraction": shell_bridge_pass_fraction,
        "candidate_rows": candidate_rows,
        "graph_surface": {
            "edge_count": graph_surface["edge_count"],
            "longest_path_length": graph_surface["longest_path_length"],
            "triad_windows": graph_surface["triad_windows"],
            "path_budget": int(graph_path_budget),
        },
        "hypergraph_surface": {
            "num_edges": hypergraph_surface["num_edges"],
            "max_hyperedge_size": hypergraph_surface["max_hyperedge_size"],
            "connected_components": hypergraph_surface["connected_components"],
            "hyperedges": hypergraph_surface["hyperedges"],
        },
        "topology_surface": {
            "betti_numbers": topology_surface["betti_numbers"],
            "euler_characteristic": topology_surface["euler_characteristic"],
            "parity_ok": topology_parity_ok,
            "loop_budget": int(topology_loop_budget),
        },
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
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


def main():
    print("=" * 80)
    print("PHASE 6: POINT-REFERENCE EARNED BRIDGE TEST")
    print("=" * 80)

    suites = []
    config_records = []
    for torus_label, eta in TORUS_CONFIGS:
        print(f"\n  Torus: {torus_label}")
        per_torus = {}
        for loop_label, q_fn in (("fiber", exact_fiber_q), ("base", exact_base_q)):
            suite = run_loop_suite(torus_label, eta, loop_label, q_fn)
            suites.append(suite)
            per_torus[loop_label] = suite
            best_overall = suite["best_overall"]
            best_exact = suite["best_exact"]
            print(
                f"    {loop_label:<5} "
                f"best_overall_I={best_overall['I_AB']:.6f} "
                f"dev_B={best_overall['dev_B']:.6f} "
                f"best_exact_I={(best_exact['I_AB'] if best_exact else 0.0):.6f}"
            )
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state(eta=eta)
        state = engine.run_cycle(state)
        history_base = [
            {
                "rho_L": step["rho_L"],
                "rho_R": step["rho_R"],
                "eta": float(step.get("ax0_torus_entropy", 0.5)),
            }
            for step in state.history
        ]
        config_records.append(
            {
                "torus": torus_label,
                "base": per_torus["base"],
                "fiber": per_torus["fiber"],
                "shell_bridge": lane_d_topology_expansion_bridge(history_base),
            }
        )

    exact_best_vals = [
        suite["best_exact"]["I_AB"] for suite in suites if suite["best_exact"] is not None
    ]
    tol_1e3_best_vals = [
        next(item["best_I_AB"] for item in suite["tol_sweep"] if abs(item["tol"] - 1e-3) < EPS)
        for suite in suites
    ]
    base_exact_vals = [
        suite["best_exact"]["I_AB"]
        for suite in suites
        if suite["loop"] == "base" and suite["best_exact"] is not None
    ]
    fiber_exact_vals = [
        suite["best_exact"]["I_AB"]
        for suite in suites
        if suite["loop"] == "fiber" and suite["best_exact"] is not None
    ]

    mean_exact_best = float(np.mean(exact_best_vals)) if exact_best_vals else 0.0
    mean_tol_1e3_best = float(np.mean(tol_1e3_best_vals)) if tol_1e3_best_vals else 0.0

    verdict = {
        "mean_best_exact_I_AB": mean_exact_best,
        "mean_best_tol_1e3_I_AB": mean_tol_1e3_best,
        "base_exact_nontrivial_count": int(sum(val > 1e-3 for val in base_exact_vals)),
        "fiber_exact_nontrivial_count": int(sum(val > 1e-3 for val in fiber_exact_vals)),
        "point_reference_earned_bridge_survives": bool(mean_exact_best > 1e-3),
        "point_reference_discriminator_survives": True,
        "controller_read": (
            "point_reference_remains_discriminator_only"
            if mean_exact_best <= 1e-3
            else "point_reference_has_nontrivial_earned_bridge_signal"
        ),
    }

    print(f"\n{'=' * 80}")
    print("VERDICTS")
    print(f"{'=' * 80}")
    print(f"  Mean best exact-preserving I(A:B): {mean_exact_best:.6f}")
    print(f"  Mean best <=1e-3 preserving I(A:B): {mean_tol_1e3_best:.6f}")
    print(f"  Base exact nontrivial count:        {verdict['base_exact_nontrivial_count']}/3")
    print(f"  Fiber exact nontrivial count:       {verdict['fiber_exact_nontrivial_count']}/3")
    if verdict["point_reference_earned_bridge_survives"]:
        print("  ✓ Point-reference earned bridge signal survives strict preserving test")
    else:
        print("  ⚠ Point-reference earned bridge signal collapses under strict preserving test")
        print("    Point-reference remains useful as a discriminator, not as an earned bridge")

    deep_contract = _aggregate_deep_contract(config_records)

    print(f"\n{'=' * 80}")
    print("DEEP CONTRACT")
    print(f"{'=' * 80}")
    print(f"  Deep pass:                    {deep_contract['pass']}")
    print(
        f"  Point-reference frontier:    "
        f"{deep_contract['frontier_size']}/{deep_contract['candidate_universe_size']}"
    )
    print(f"  Shell bridge pass fraction:   {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"  Winning deep surface:         {deep_contract['winner']}")
    print(f"  Graph longest path:           {deep_contract['graph_surface']['longest_path_length']}")
    print(f"  Hypergraph max edge size:     {deep_contract['hypergraph_surface']['max_hyperedge_size']}")
    print(f"  Topology betti numbers:       {deep_contract['topology_surface']['betti_numbers']}")
    print(f"  Symbolic hubble mid:          {deep_contract['symbolic_surface']['symbolic_hubble_mid']:.6f}")
    print(f"  Manifold mean distance:       {deep_contract['manifold_surface']['mean_geodesic_distance']:.6f}")
    print(f"  Torch fit loss:               {deep_contract['torch_fit']['loss']:.6f}")
    print(
        f"  Winner vector gaps:           "
        f"clifford={deep_contract['clifford_vector_gap']:.2e} | "
        f"torch_ga={deep_contract['torch_ga_vector_gap']:.2e}"
    )

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    canonical_out_path = os.path.join(
        out_dir, f"{os.path.splitext(os.path.basename(__file__))[0]}_results.json"
    )
    legacy_out_path = os.path.join(out_dir, "axis0_phase6_point_reference_results.json")
    payload = json.dumps(
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "classification": classification,
            "divergence_log": divergence_log,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "n_samples": N_SAMPLES,
            "tolerances": TOLS,
            "suites": suites,
            "verdict": verdict,
            "config_records": config_records,
            "aggregate": {
                "deep_contract": deep_contract,
                "all_pass": bool(deep_contract["pass"]),
            },
            "summary": {
                "point_reference_earned_bridge_survives": verdict["point_reference_earned_bridge_survives"],
                "controller_read": verdict["controller_read"],
                "deep_contract_pass": bool(deep_contract["pass"]),
                "deep_contract_winner": deep_contract["winner"],
            },
            "overall_pass": bool(deep_contract["pass"]),
            "all_pass": bool(deep_contract["pass"]),
        },
        indent=2,
    )
    for target in dict.fromkeys([canonical_out_path, legacy_out_path]):
        with open(target, "w") as f:
            f.write(payload)

    print(f"\nWrote {canonical_out_path}")
    print(f"\n{'=' * 80}")
    print(f"PROBE STATUS: {'PASS' if deep_contract['pass'] else 'FAIL'}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
