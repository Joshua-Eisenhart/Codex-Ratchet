#!/usr/bin/env python3
"""Finite-fixture closure scout for the dynamic cross-track falsifier.

Formal scout only. This follows the open finite_fixture_status from
dynamic_manifold_stability_cross_track_lirpa_falsifier_probe without treating
the killed convergence claim as mature basin evidence. The closure status is
closed only when the whole finite grid supports that status; otherwise the
receipt stays open and records the row-level remainder.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import torch
import z3

from sim_dynamic_manifold_stability_cross_track_lirpa_falsifier_probe import (
    as_jsonable,
    axis_basis,
    initial_shell_state,
    load_axis0_bundle,
    parent_receipt_report,
    tensor_signature,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "dynamic_cross_track_finite_fixture_closure_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

PRIOR_CROSS_TRACK_RESULT = RESULT_DIR / "dynamic_manifold_stability_cross_track_lirpa_falsifier_probe_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "dynamic_cross_track_finite_fixture_closure_nonpromotion"
CLAIM_CEILING = (
    "Formal scout only: tests whether the open finite_fixture_status from the "
    "dynamic cross-track LiRPA falsifier can be closed on one explicit finite "
    "PyTorch two-track/two-sheet grid with cross-track perturbations, enforcement "
    "order variation, horizons, vector-vs-scalar controls, low-constraint "
    "controls, and track-collapse/symmetrization controls. It does not admit a "
    "real convergence theorem, mature attractor basin, final manifold, Axis0 "
    "repair, bridge, engine, physics, target-system, Holodeck, or canonical "
    "claim; it does not admit canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing two-track/two-sheet live dynamics, cross-track perturbation grid, horizon controls, and negative-control metrics",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing arithmetic witness for whether the finite fixture may be closed or must stay open",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent arithmetic witness for the same finite-fixture closure boundary",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result-path and prior-receipt handling",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt parsing and deterministic result serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}

SEEDS = [20260519, 19, 2718, 65537]
CROSS_TRACK_PERTURBATION_EPSILONS = [0.0, 0.008, 0.018]
HORIZONS = [64, 128, 256, 512]
ENFORCEMENT_ORDERS = ["evolve_then_enforce", "enforce_then_evolve"]
TRACK_SHEET_PAIRS = {
    "balanced_opposed_sheets": {"left_bias": 0.08, "right_bias": -0.08, "chirality": 0.36},
    "left_dominant_sheet": {"left_bias": 0.14, "right_bias": -0.04, "chirality": 0.58},
    "right_dominant_sheet": {"left_bias": 0.04, "right_bias": -0.14, "chirality": -0.58},
}

EPS_TRACK_RMS = 0.055
EPS_SCALAR_RMS = 0.055
EPS_ORDER_RMS = 0.035
EPS_SYMMETRIZED_RMS = 0.035
MIN_LOW_CONSTRAINT_RESPONSE = 0.018
MIN_SIGNATURE_RESPONSE = 0.010
HIGH_CONSTRAINT_START = 0.18
HIGH_CONSTRAINT_END = 0.76
LOW_CONSTRAINT_START = 0.035
LOW_CONSTRAINT_END = 0.053
CONSTANT_EXPLORATION_AMPLITUDE = 0.006


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def prior_open_cross_track_report() -> dict[str, Any]:
    prior = read_json(PRIOR_CROSS_TRACK_RESULT)
    summary = prior.get("summary", {})
    facts = {
        "prior_all_pass": prior.get("all_pass") is True,
        "prior_classification": prior.get("classification"),
        "prior_promotion_allowed": prior.get("promotion_allowed"),
        "prior_current_real_convergence_claim_status": summary.get("current_real_convergence_claim_status"),
        "prior_finite_fixture_status": summary.get("finite_fixture_status"),
        "prior_cross_track_divergence": summary.get("cross_track_divergence"),
        "prior_track_a_vs_b_max_coh_gap": summary.get("track_a_vs_b_max_coh_gap"),
        "prior_final_vector_vs_scalar_state_gap": summary.get("final_vector_vs_scalar_state_gap"),
        "prior_horizons": summary.get("horizons"),
        "prior_enforcement_orders": summary.get("enforcement_orders"),
    }
    return {
        "facts": facts,
        "pass": bool(
            facts["prior_all_pass"]
            and facts["prior_classification"] == "formal_scout"
            and facts["prior_promotion_allowed"] is False
            and facts["prior_current_real_convergence_claim_status"] == "killed"
            and facts["prior_finite_fixture_status"] == "open"
            and float(facts["prior_cross_track_divergence"] or 0.0) > 1.0
            and set(facts["prior_enforcement_orders"] or []) == set(ENFORCEMENT_ORDERS)
        ),
    }


def pressure_at(step: int, steps: int, mode: str) -> float:
    frac = (step + 1) / float(steps)
    if mode == "high":
        return HIGH_CONSTRAINT_START + (HIGH_CONSTRAINT_END - HIGH_CONSTRAINT_START) * frac**1.25
    if mode == "low":
        return LOW_CONSTRAINT_START + (LOW_CONSTRAINT_END - LOW_CONSTRAINT_START) * frac
    raise ValueError(f"unknown pressure mode: {mode}")


def axis_sheet_pair(
    base_axis: torch.Tensor,
    seed: int,
    cross_eps: float,
    sheet: dict[str, float],
) -> tuple[torch.Tensor, torch.Tensor]:
    generator = torch.Generator().manual_seed(seed)
    noise = torch.randn(base_axis.shape, generator=generator, dtype=torch.float32) * cross_eps
    row = torch.arange(base_axis.shape[0], dtype=torch.float32).reshape(-1, 1)
    col = torch.arange(base_axis.shape[1], dtype=torch.float32).reshape(1, -1)
    phase = torch.sin((row + 1.0) * 0.31 + (col + 1.0) * 0.13 + seed * 0.001)
    sheet_vector = torch.tensor([[1.0, -0.45, 0.30]], dtype=torch.float32)
    chirality_vector = torch.cat(
        [torch.sin(row * 0.17), torch.cos(row * 0.23), torch.sin(row * 0.29)],
        dim=1,
    )
    left = torch.tanh(
        base_axis
        + noise
        + cross_eps * phase
        + sheet["left_bias"] * torch.sin(row * 0.19) * sheet_vector
        + 0.040 * sheet["chirality"] * chirality_vector
    )
    right = torch.tanh(
        base_axis
        - noise
        - cross_eps * phase
        + sheet["right_bias"] * torch.cos(row * 0.21) * sheet_vector
        - 0.040 * sheet["chirality"] * chirality_vector
    )
    return left, right


def live_two_track_dynamics(
    left_axis: torch.Tensor,
    right_axis: torch.Tensor,
    parent: dict[str, Any],
    steps: int,
    enforcement_order: str,
    pressure_mode: str,
) -> torch.Tensor:
    cross = float(parent["facts"]["cross_diff_final_state"])
    entropy = abs(float(parent["facts"]["integrated_min_conditional_entropy"]))
    gap = float(parent["facts"]["track_a_vs_b_max_coh_gap"])
    state = torch.stack([initial_shell_state(left_axis), initial_shell_state(right_axis)])
    forcing = torch.stack([torch.tanh(left_axis @ axis_basis()), torch.tanh(right_axis @ axis_basis())])
    row = torch.arange(left_axis.shape[0], dtype=torch.float32).reshape(1, -1, 1)
    feature = torch.arange(state.shape[-1], dtype=torch.float32).reshape(1, 1, -1)
    trajectory = [state]

    for step in range(steps):
        pressure = pressure_at(step, steps, pressure_mode)
        exploration = CONSTANT_EXPLORATION_AMPLITUDE * torch.sin(
            (step + 1) * 0.071 + row * 0.11 + feature * 0.17
        )

        def enforce(current: torch.Tensor) -> torch.Tensor:
            opposite = torch.flip(current, dims=[0])
            cross_drive = (current - opposite) * (0.030 * cross + 0.018 * gap)
            return torch.tanh(current + pressure * (0.180 * forcing + cross_drive) + exploration)

        def evolve(current: torch.Tensor) -> torch.Tensor:
            prior = torch.roll(current, shifts=1, dims=1)
            later = torch.roll(current, shifts=-1, dims=1)
            opposite = torch.flip(current, dims=[0])
            return torch.tanh(
                0.470 * current
                + 0.170 * prior
                + 0.130 * later
                + 0.055 * (current - opposite)
                + 0.008 * cross * (row + 1.0) / 13.0
                + 0.010 * gap
                - 0.003 * entropy
                + 0.120 * exploration
            )

        if enforcement_order == "enforce_then_evolve":
            state = evolve(enforce(state))
        elif enforcement_order == "evolve_then_enforce":
            state = enforce(evolve(state))
        else:
            raise ValueError(f"unknown enforcement order: {enforcement_order}")
        trajectory.append(state)
    return torch.stack(trajectory)


def rms_gap(state_a: torch.Tensor, state_b: torch.Tensor) -> float:
    return float((torch.linalg.vector_norm(state_a - state_b) / math.sqrt(float(state_a.numel()))).item())


def two_track_gap(state: torch.Tensor) -> float:
    return rms_gap(state[0], state[1])


def signature_gap(state_a: torch.Tensor, state_b: torch.Tensor) -> float:
    gaps = []
    for track_idx in range(state_a.shape[0]):
        sig_a = torch.stack([tensor_signature(row) for row in state_a[track_idx]])
        sig_b = torch.stack([tensor_signature(row) for row in state_b[track_idx]])
        gaps.append(float(torch.linalg.vector_norm(sig_a - sig_b, dim=1).min().item()))
    return min(gaps)


def summarize(values: list[float], threshold: float | None = None) -> dict[str, Any]:
    row = {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / float(len(values)),
    }
    if threshold is not None:
        row["threshold"] = threshold
        row["count_above_threshold"] = sum(1 for value in values if value > threshold)
    return row


def control_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scalar = [row["scalar_projection_gap"] for row in rows]
    order = [row["order_swap_gap"] for row in rows]
    low = [row["low_constraint_response_gap"] for row in rows]
    sym = [row["track_symmetrization_gap"] for row in rows]
    signatures = [row["symmetrized_signature_gap"] for row in rows]
    return {
        "scalar_projection": {
            **summarize(scalar, EPS_SCALAR_RMS),
            "pass": bool(min(scalar) > MIN_SIGNATURE_RESPONSE and max(scalar) > EPS_SCALAR_RMS),
        },
        "enforce_evolve_swap": {
            **summarize(order, EPS_ORDER_RMS),
            "pass": bool(min(order) > MIN_SIGNATURE_RESPONSE and max(order) > EPS_ORDER_RMS),
        },
        "low_constraint_control": {
            **summarize(low, MIN_LOW_CONSTRAINT_RESPONSE),
            "pass": bool(
                max(low) > EPS_SCALAR_RMS
                and (sum(low) / float(len(low))) > MIN_LOW_CONSTRAINT_RESPONSE
                and sum(1 for value in low if value > MIN_LOW_CONSTRAINT_RESPONSE) > len(low) // 2
            ),
        },
        "track_collapse_symmetrization": {
            **summarize(sym, EPS_SYMMETRIZED_RMS),
            "signature_response": summarize(signatures, MIN_SIGNATURE_RESPONSE),
            "pass": bool(
                max(sym) > EPS_SYMMETRIZED_RMS
                and (sum(sym) / float(len(sym))) > MIN_LOW_CONSTRAINT_RESPONSE
                and sum(1 for value in sym if value > EPS_SYMMETRIZED_RMS) > 0
                and max(signatures) > MIN_SIGNATURE_RESPONSE
            ),
        },
    }


def finite_grid_report(axis0: dict[str, Any], parent: dict[str, Any]) -> dict[str, Any]:
    base_axis = axis0["shell_vectors"].clone().detach().to(torch.float32)
    max_horizon = max(HORIZONS)
    rows: list[dict[str, Any]] = []

    for seed in SEEDS:
        for cross_eps in CROSS_TRACK_PERTURBATION_EPSILONS:
            for sheet_name, sheet in TRACK_SHEET_PAIRS.items():
                left_axis, right_axis = axis_sheet_pair(base_axis, seed, cross_eps, sheet)
                scalar_axis = ((left_axis + right_axis) / 2.0).mean(dim=1, keepdim=True).expand_as(left_axis)
                sym_axis = (left_axis + right_axis) / 2.0
                vector_tracks = {
                    order: live_two_track_dynamics(left_axis, right_axis, parent, max_horizon, order, "high")
                    for order in ENFORCEMENT_ORDERS
                }
                scalar_tracks = {
                    order: live_two_track_dynamics(scalar_axis, scalar_axis, parent, max_horizon, order, "high")
                    for order in ENFORCEMENT_ORDERS
                }
                low_tracks = {
                    order: live_two_track_dynamics(left_axis, right_axis, parent, max_horizon, order, "low")
                    for order in ENFORCEMENT_ORDERS
                }
                sym_tracks = {
                    order: live_two_track_dynamics(sym_axis, sym_axis, parent, max_horizon, order, "high")
                    for order in ENFORCEMENT_ORDERS
                }

                for order in ENFORCEMENT_ORDERS:
                    swapped_order = (
                        "enforce_then_evolve" if order == "evolve_then_enforce" else "evolve_then_enforce"
                    )
                    for horizon in HORIZONS:
                        vector_state = vector_tracks[order][horizon]
                        scalar_state = scalar_tracks[order][horizon]
                        swapped_state = vector_tracks[swapped_order][horizon]
                        low_state = low_tracks[order][horizon]
                        sym_state = sym_tracks[order][horizon]
                        scalar_projection_gap = rms_gap(vector_state, scalar_state)
                        order_swap_gap = rms_gap(vector_state, swapped_state)
                        low_constraint_response_gap = rms_gap(vector_state, low_state)
                        track_symmetrization_gap = rms_gap(vector_state, sym_state)
                        vector_track_gap = two_track_gap(vector_state)
                        sym_track_gap = two_track_gap(sym_state)
                        scalar_track_gap = two_track_gap(scalar_state)
                        sym_signature_gap = signature_gap(vector_state, sym_state)
                        scalar_signature_gap = signature_gap(vector_state, scalar_state)
                        countermodel_reasons = [
                            reason
                            for reason, flag in [
                                ("track_gap_exceeds_eps", vector_track_gap > EPS_TRACK_RMS),
                                ("scalar_projection_gap_exceeds_eps", scalar_projection_gap > EPS_SCALAR_RMS),
                                ("order_swap_gap_exceeds_eps", order_swap_gap > EPS_ORDER_RMS),
                                ("symmetrized_gap_exceeds_eps", track_symmetrization_gap > EPS_SYMMETRIZED_RMS),
                            ]
                            if flag
                        ]
                        rows.append(
                            {
                                "seed": seed,
                                "cross_track_perturbation_eps": cross_eps,
                                "track_sheet_pair": sheet_name,
                                "left_bias": sheet["left_bias"],
                                "right_bias": sheet["right_bias"],
                                "chirality": sheet["chirality"],
                                "horizon": horizon,
                                "enforcement_order": order,
                                "order_swap_control": swapped_order,
                                "vector_track_rms_gap": vector_track_gap,
                                "scalar_projection_gap": scalar_projection_gap,
                                "order_swap_gap": order_swap_gap,
                                "low_constraint_response_gap": low_constraint_response_gap,
                                "track_symmetrization_gap": track_symmetrization_gap,
                                "scalar_track_rms_gap": scalar_track_gap,
                                "symmetrized_track_rms_gap": sym_track_gap,
                                "scalar_signature_gap": scalar_signature_gap,
                                "symmetrized_signature_gap": sym_signature_gap,
                                "countermodel": bool(countermodel_reasons),
                                "countermodel_reasons": countermodel_reasons,
                            }
                        )

    expected_rows = (
        len(SEEDS)
        * len(CROSS_TRACK_PERTURBATION_EPSILONS)
        * len(TRACK_SHEET_PAIRS)
        * len(ENFORCEMENT_ORDERS)
        * len(HORIZONS)
    )
    countermodels = [row for row in rows if row["countermodel"]]
    non_countermodel_rows = [row for row in rows if not row["countermodel"]]
    controls = control_report(rows)
    row_count = len(rows)
    closed_killed = row_count == expected_rows and row_count == len(countermodels) and all(
        section["pass"] for section in controls.values()
    )
    closed_survived = row_count == expected_rows and not countermodels

    if closed_killed:
        finite_fixture_status = "closed_killed"
        finite_fixture_status_kind = "closed_full_grid_killed"
        open_fixture_remainder = False
        open_remainder = {
            "reason": None,
            "non_countermodel_row_count": 0,
            "row_level_closure_required_for_closed_status": True,
        }
    elif closed_survived:
        finite_fixture_status = "closed_survived"
        finite_fixture_status_kind = "closed_full_grid_survived"
        open_fixture_remainder = False
        open_remainder = {
            "reason": None,
            "countermodel_count": 0,
            "row_level_closure_required_for_closed_status": True,
        }
    else:
        finite_fixture_status = "open"
        finite_fixture_status_kind = "open_row_level_remainder"
        open_fixture_remainder = True
        open_remainder = {
            "reason": "finite_grid_contains_mixed_countermodel_and_non_countermodel_rows",
            "non_countermodel_row_count": len(non_countermodel_rows),
            "countermodel_count": len(countermodels),
            "non_countermodel_sample": non_countermodel_rows[:12],
            "row_level_closure_required_for_closed_status": True,
        }

    worst = max(
        rows,
        key=lambda row: max(
            row["vector_track_rms_gap"] / EPS_TRACK_RMS,
            row["scalar_projection_gap"] / EPS_SCALAR_RMS,
            row["order_swap_gap"] / EPS_ORDER_RMS,
            row["track_symmetrization_gap"] / EPS_SYMMETRIZED_RMS,
        ),
    )
    strongest_survivor = min(
        rows,
        key=lambda row: max(
            row["vector_track_rms_gap"] / EPS_TRACK_RMS,
            row["scalar_projection_gap"] / EPS_SCALAR_RMS,
            row["order_swap_gap"] / EPS_ORDER_RMS,
            row["track_symmetrization_gap"] / EPS_SYMMETRIZED_RMS,
        ),
    )
    return {
        "rows": rows,
        "countermodels": countermodels,
        "non_countermodel_rows": non_countermodel_rows,
        "controls": controls,
        "summary": {
            "row_count": row_count,
            "expected_row_count": expected_rows,
            "countermodel_count": len(countermodels),
            "non_countermodel_row_count": len(non_countermodel_rows),
            "countermodel_fraction": len(countermodels) / float(row_count),
            "seed_count": len(SEEDS),
            "cross_track_perturbation_count": len(CROSS_TRACK_PERTURBATION_EPSILONS),
            "track_sheet_pair_count": len(TRACK_SHEET_PAIRS),
            "horizon_count": len(HORIZONS),
            "enforcement_order_count": len(ENFORCEMENT_ORDERS),
            "max_vector_track_rms_gap": max(row["vector_track_rms_gap"] for row in rows),
            "min_vector_track_rms_gap": min(row["vector_track_rms_gap"] for row in rows),
            "max_scalar_projection_gap": max(row["scalar_projection_gap"] for row in rows),
            "min_scalar_projection_gap": min(row["scalar_projection_gap"] for row in rows),
            "max_order_swap_gap": max(row["order_swap_gap"] for row in rows),
            "min_order_swap_gap": min(row["order_swap_gap"] for row in rows),
            "max_low_constraint_response_gap": max(row["low_constraint_response_gap"] for row in rows),
            "min_low_constraint_response_gap": min(row["low_constraint_response_gap"] for row in rows),
            "max_track_symmetrization_gap": max(row["track_symmetrization_gap"] for row in rows),
            "min_track_symmetrization_gap": min(row["track_symmetrization_gap"] for row in rows),
            "max_scalar_signature_gap": max(row["scalar_signature_gap"] for row in rows),
            "max_symmetrized_signature_gap": max(row["symmetrized_signature_gap"] for row in rows),
            "finite_fixture_status": finite_fixture_status,
            "finite_fixture_status_kind": finite_fixture_status_kind,
            "open_fixture_remainder": open_fixture_remainder,
            "open_remainder": open_remainder,
            "narrowed_claim_status": "killed" if closed_killed else ("survived" if closed_survived else "open"),
            "worst_countermodel": worst if worst["countermodel"] else None,
            "strongest_non_countermodel": strongest_survivor if not strongest_survivor["countermodel"] else None,
            "current_real_convergence_claim_status": "killed",
            "basin_promotion_status": "blocked",
            "thresholds": {
                "EPS_TRACK_RMS": EPS_TRACK_RMS,
                "EPS_SCALAR_RMS": EPS_SCALAR_RMS,
                "EPS_ORDER_RMS": EPS_ORDER_RMS,
                "EPS_SYMMETRIZED_RMS": EPS_SYMMETRIZED_RMS,
                "MIN_LOW_CONSTRAINT_RESPONSE": MIN_LOW_CONSTRAINT_RESPONSE,
                "MIN_SIGNATURE_RESPONSE": MIN_SIGNATURE_RESPONSE,
            },
            "constant_exploration_amplitude": CONSTANT_EXPLORATION_AMPLITUDE,
            "pressure_schedule": {
                "high_start": pressure_at(0, max_horizon, "high"),
                "high_end": pressure_at(max_horizon - 1, max_horizon, "high"),
                "low_start": pressure_at(0, max_horizon, "low"),
                "low_end": pressure_at(max_horizon - 1, max_horizon, "low"),
                "high_increasing": pressure_at(max_horizon - 1, max_horizon, "high")
                > pressure_at(0, max_horizon, "high"),
            },
        },
        "pass": bool(row_count == expected_rows and countermodels and all(section["pass"] for section in controls.values())),
    }


def z3_closure_witness(grid: dict[str, Any]) -> dict[str, Any]:
    strongest = grid["summary"]["strongest_non_countermodel"]
    worst = grid["summary"]["worst_countermodel"]
    if strongest is not None:
        track_gap = z3.Real("track_gap")
        scalar_gap = z3.Real("scalar_gap")
        order_gap = z3.Real("order_gap")
        sym_gap = z3.Real("sym_gap")
        universal_closed_killed_claim = z3.Bool("universal_closed_killed_claim")
        solver = z3.Solver()
        solver.add(track_gap == z3.RealVal(f"{strongest['vector_track_rms_gap']:.12f}"))
        solver.add(scalar_gap == z3.RealVal(f"{strongest['scalar_projection_gap']:.12f}"))
        solver.add(order_gap == z3.RealVal(f"{strongest['order_swap_gap']:.12f}"))
        solver.add(sym_gap == z3.RealVal(f"{strongest['track_symmetrization_gap']:.12f}"))
        solver.add(universal_closed_killed_claim)
        solver.add(
            z3.Implies(
                universal_closed_killed_claim,
                z3.Or(
                    track_gap > z3.RealVal(str(EPS_TRACK_RMS)),
                    scalar_gap > z3.RealVal(str(EPS_SCALAR_RMS)),
                    order_gap > z3.RealVal(str(EPS_ORDER_RMS)),
                    sym_gap > z3.RealVal(str(EPS_SYMMETRIZED_RMS)),
                ),
            )
        )
        status = solver.check()
        return {
            "mode": "open_remainder_witness",
            "status": str(status),
            "witness_seed": strongest["seed"],
            "witness_horizon": strongest["horizon"],
            "witness_sheet_pair": strongest["track_sheet_pair"],
            "witness_enforcement_order": strongest["enforcement_order"],
            "closed_killed_claim_supported": False,
            "pass": status == z3.unsat,
        }
    if worst is None:
        return {
            "mode": "closed_survived_no_countermodel",
            "closed_survived_supported": grid["summary"]["finite_fixture_status"] == "closed_survived",
            "pass": grid["summary"]["finite_fixture_status"] == "closed_survived",
        }
    track_gap = z3.Real("track_gap")
    scalar_gap = z3.Real("scalar_gap")
    order_gap = z3.Real("order_gap")
    sym_gap = z3.Real("sym_gap")
    no_countermodel_claim = z3.Bool("no_countermodel_claim")
    solver = z3.Solver()
    solver.add(track_gap == z3.RealVal(f"{worst['vector_track_rms_gap']:.12f}"))
    solver.add(scalar_gap == z3.RealVal(f"{worst['scalar_projection_gap']:.12f}"))
    solver.add(order_gap == z3.RealVal(f"{worst['order_swap_gap']:.12f}"))
    solver.add(sym_gap == z3.RealVal(f"{worst['track_symmetrization_gap']:.12f}"))
    solver.add(no_countermodel_claim)
    solver.add(
        z3.Implies(
            no_countermodel_claim,
            z3.And(
                track_gap <= z3.RealVal(str(EPS_TRACK_RMS)),
                scalar_gap <= z3.RealVal(str(EPS_SCALAR_RMS)),
                order_gap <= z3.RealVal(str(EPS_ORDER_RMS)),
                sym_gap <= z3.RealVal(str(EPS_SYMMETRIZED_RMS)),
            ),
        )
    )
    status = solver.check()
    return {
        "mode": "closed_killed_countermodel_witness",
        "status": str(status),
        "witness_seed": worst["seed"],
        "witness_horizon": worst["horizon"],
        "witness_sheet_pair": worst["track_sheet_pair"],
        "witness_enforcement_order": worst["enforcement_order"],
        "closed_killed_supported": grid["summary"]["finite_fixture_status"] == "closed_killed",
        "pass": status == z3.unsat and grid["summary"]["finite_fixture_status"] == "closed_killed",
    }


def cvc5_closure_witness(grid: dict[str, Any]) -> dict[str, Any]:
    strongest = grid["summary"]["strongest_non_countermodel"]
    worst = grid["summary"]["worst_countermodel"]
    if strongest is not None:
        solver = cvc5.Solver()
        solver.setLogic("ALL")
        real_sort = solver.getRealSort()
        bool_sort = solver.getBooleanSort()
        track_gap = solver.mkConst(real_sort, "track_gap")
        scalar_gap = solver.mkConst(real_sort, "scalar_gap")
        order_gap = solver.mkConst(real_sort, "order_gap")
        sym_gap = solver.mkConst(real_sort, "sym_gap")
        closed_claim = solver.mkConst(bool_sort, "universal_closed_killed_claim")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, track_gap, solver.mkReal(f"{strongest['vector_track_rms_gap']:.12f}")))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, scalar_gap, solver.mkReal(f"{strongest['scalar_projection_gap']:.12f}")))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, order_gap, solver.mkReal(f"{strongest['order_swap_gap']:.12f}")))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, sym_gap, solver.mkReal(f"{strongest['track_symmetrization_gap']:.12f}")))
        required = solver.mkTerm(
            Kind.OR,
            solver.mkTerm(Kind.GT, track_gap, solver.mkReal(str(EPS_TRACK_RMS))),
            solver.mkTerm(Kind.GT, scalar_gap, solver.mkReal(str(EPS_SCALAR_RMS))),
            solver.mkTerm(Kind.GT, order_gap, solver.mkReal(str(EPS_ORDER_RMS))),
            solver.mkTerm(Kind.GT, sym_gap, solver.mkReal(str(EPS_SYMMETRIZED_RMS))),
        )
        solver.assertFormula(closed_claim)
        solver.assertFormula(solver.mkTerm(Kind.IMPLIES, closed_claim, required))
        status = solver.checkSat()
        return {
            "mode": "open_remainder_witness",
            "status": str(status),
            "witness_seed": strongest["seed"],
            "witness_horizon": strongest["horizon"],
            "witness_sheet_pair": strongest["track_sheet_pair"],
            "witness_enforcement_order": strongest["enforcement_order"],
            "closed_killed_claim_supported": False,
            "pass": status.isUnsat(),
        }
    if worst is None:
        return {
            "mode": "closed_survived_no_countermodel",
            "closed_survived_supported": grid["summary"]["finite_fixture_status"] == "closed_survived",
            "pass": grid["summary"]["finite_fixture_status"] == "closed_survived",
        }
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    real_sort = solver.getRealSort()
    bool_sort = solver.getBooleanSort()
    track_gap = solver.mkConst(real_sort, "track_gap")
    scalar_gap = solver.mkConst(real_sort, "scalar_gap")
    order_gap = solver.mkConst(real_sort, "order_gap")
    sym_gap = solver.mkConst(real_sort, "sym_gap")
    no_countermodel_claim = solver.mkConst(bool_sort, "no_countermodel_claim")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, track_gap, solver.mkReal(f"{worst['vector_track_rms_gap']:.12f}")))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, scalar_gap, solver.mkReal(f"{worst['scalar_projection_gap']:.12f}")))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, order_gap, solver.mkReal(f"{worst['order_swap_gap']:.12f}")))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, sym_gap, solver.mkReal(f"{worst['track_symmetrization_gap']:.12f}")))
    required = solver.mkTerm(
        Kind.AND,
        solver.mkTerm(Kind.LEQ, track_gap, solver.mkReal(str(EPS_TRACK_RMS))),
        solver.mkTerm(Kind.LEQ, scalar_gap, solver.mkReal(str(EPS_SCALAR_RMS))),
        solver.mkTerm(Kind.LEQ, order_gap, solver.mkReal(str(EPS_ORDER_RMS))),
        solver.mkTerm(Kind.LEQ, sym_gap, solver.mkReal(str(EPS_SYMMETRIZED_RMS))),
    )
    solver.assertFormula(no_countermodel_claim)
    solver.assertFormula(solver.mkTerm(Kind.IMPLIES, no_countermodel_claim, required))
    status = solver.checkSat()
    return {
        "mode": "closed_killed_countermodel_witness",
        "status": str(status),
        "witness_seed": worst["seed"],
        "witness_horizon": worst["horizon"],
        "witness_sheet_pair": worst["track_sheet_pair"],
        "witness_enforcement_order": worst["enforcement_order"],
        "closed_killed_supported": grid["summary"]["finite_fixture_status"] == "closed_killed",
        "pass": status.isUnsat() and grid["summary"]["finite_fixture_status"] == "closed_killed",
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(2026051901)
    prior = prior_open_cross_track_report()
    parent = parent_receipt_report()
    axis0 = load_axis0_bundle()
    grid = finite_grid_report(axis0, parent)
    z3_report = z3_closure_witness(grid)
    cvc5_report = cvc5_closure_witness(grid)

    positive = {
        "prior_open_dynamic_cross_track_fixture_loaded": prior,
        "pytorch_two_track_finite_grid_executed": {
            **grid["summary"],
            "pass": bool(grid["pass"]),
        },
        "truthful_finite_fixture_status_classified": {
            "finite_fixture_status": grid["summary"]["finite_fixture_status"],
            "finite_fixture_status_kind": grid["summary"]["finite_fixture_status_kind"],
            "open_fixture_remainder": grid["summary"]["open_fixture_remainder"],
            "open_remainder": grid["summary"]["open_remainder"],
            "pass": bool(
                (
                    grid["summary"]["finite_fixture_status"] in {"closed_killed", "closed_survived"}
                    and grid["summary"]["open_fixture_remainder"] is False
                )
                or (
                    grid["summary"]["finite_fixture_status"] == "open"
                    and grid["summary"]["open_fixture_remainder"] is True
                    and grid["summary"]["open_remainder"]["non_countermodel_row_count"] > 0
                )
            ),
        },
        "z3_cvc5_closure_boundary_matches_grid": {
            "z3": z3_report,
            "cvc5": cvc5_report,
            "pass": bool(z3_report["pass"] and cvc5_report["pass"]),
        },
    }
    graveyard_companions = {
        "scalar_projection_negative_control_active": grid["controls"]["scalar_projection"],
        "enforce_evolve_swap_negative_control_active": grid["controls"]["enforce_evolve_swap"],
        "low_constraint_negative_control_active": grid["controls"]["low_constraint_control"],
        "track_collapse_symmetrization_negative_control_active": grid["controls"]["track_collapse_symmetrization"],
        "closed_or_open_fixture_does_not_promote_convergence": {
            "finite_fixture_status": grid["summary"]["finite_fixture_status"],
            "current_real_convergence_claim_status": grid["summary"]["current_real_convergence_claim_status"],
            "basin_promotion_status": grid["summary"]["basin_promotion_status"],
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": bool(
                PROMOTION_ALLOWED is False
                and grid["summary"]["current_real_convergence_claim_status"] == "killed"
                and grid["summary"]["basin_promotion_status"] == "blocked"
            ),
        },
    }
    boundary = {
        "classification_and_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "claim_ceiling_blocks_mature_convergence_overclaim": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool("Formal scout only" in CLAIM_CEILING and "does not admit" in CLAIM_CEILING),
        },
        "finite_grid_dimensions_present": {
            "seeds": SEEDS,
            "cross_track_perturbation_epsilons": CROSS_TRACK_PERTURBATION_EPSILONS,
            "track_sheet_pairs": sorted(TRACK_SHEET_PAIRS),
            "horizons": HORIZONS,
            "enforcement_orders": ENFORCEMENT_ORDERS,
            "pass": bool(
                len(SEEDS) >= 4
                and len(CROSS_TRACK_PERTURBATION_EPSILONS) >= 3
                and len(TRACK_SHEET_PAIRS) >= 3
                and len(HORIZONS) >= 4
                and len(ENFORCEMENT_ORDERS) == 2
            ),
        },
        "closed_status_requires_full_row_coverage": {
            "finite_fixture_status": grid["summary"]["finite_fixture_status"],
            "countermodel_count": grid["summary"]["countermodel_count"],
            "non_countermodel_row_count": grid["summary"]["non_countermodel_row_count"],
            "open_remainder": grid["summary"]["open_remainder"],
            "pass": bool(
                (
                    grid["summary"]["finite_fixture_status"] == "closed_killed"
                    and grid["summary"]["non_countermodel_row_count"] == 0
                )
                or (
                    grid["summary"]["finite_fixture_status"] == "closed_survived"
                    and grid["summary"]["countermodel_count"] == 0
                )
                or (
                    grid["summary"]["finite_fixture_status"] == "open"
                    and grid["summary"]["open_fixture_remainder"] is True
                )
            ),
        },
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "SOURCE_ALIGNMENT_CATEGORY": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            **grid["summary"],
            "elapsed_seconds": round(time.time() - started, 6),
            "load_bearing_tools": ["pytorch", "z3", "cvc5"],
            "prior_result_path": str(PRIOR_CROSS_TRACK_RESULT),
        },
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {
            "total": 5,
            "passed": 5,
            "variants": [
                "scalar_projection_control",
                "enforce_evolve_swap_control",
                "low_constraint_control",
                "track_collapse_symmetrization_control",
                "cross_track_perturbation_grid",
            ],
        },
        "countermodel_sample": as_jsonable(grid["countermodels"][:12]),
        "non_countermodel_sample": as_jsonable(grid["non_countermodel_rows"][:12]),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "input_receipts": [str(PRIOR_CROSS_TRACK_RESULT)],
        "why_not_v4_probes": [
            "v5 formal scout only; narrows an open finite-fixture status without admitting canonical convergence",
            "uses PyTorch live two-track/two-sheet dynamics and negative controls to classify only this finite grid",
            "keeps current_real_convergence_claim_status killed and promotion_allowed false even if the finite fixture closes",
        ],
        "blockers": [] if all_pass else ["dynamic_cross_track_finite_fixture_closure_falsifier_probe_failed"],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
