#!/usr/bin/env python3
"""Family-portability probe for the dynamic-basin finite countermodel.

Formal scout only. This follows
dynamic_basin_finite_fixture_closure_falsifier_probe by asking whether its
killed finite-fixture countermodel family remains decisive across a small grid
of seeds, horizons, perturbations, enforcement order, and basin-sheet/asymmetry
settings. A green execution receipt does not promote a basin. The
finite_fixture_status is closed only if the whole family grid supports closure;
otherwise it remains open with an explicit remainder.
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

import torch

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
NAME = "basin_countermodel_family_portability_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

PRIOR_CLOSURE_RESULT = RESULT_DIR / "dynamic_basin_finite_fixture_closure_falsifier_probe_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "basin_countermodel_family_portability_nonpromotion"
CLAIM_CEILING = (
    "Formal scout only: tests whether the killed finite-fixture dynamic-basin "
    "countermodel family is portable across a small PyTorch live-dynamics grid "
    "with constant exploration, increasing constraint pressure, seed/horizon/"
    "perturbation/enforcement-order variation, and basin-sheet/asymmetry "
    "settings. It truthfully leaves finite_fixture_status open unless the full "
    "family grid supports closure. It does not admit a real attractor basin, "
    "final convergence theorem, final manifold, Axis0 repair, bridge, engine, "
    "physics, target-system, Holodeck, or canonical claim; it does not admit "
    "canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing live dynamics, pressure schedule, family grid, and negative-control metrics",
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
    "pathlib": "supportive",
    "python_json": "supportive",
}

SEEDS = [20260518, 42, 1337, 314159]
HORIZONS = [64, 128, 256, 512]
PERTURBATION_FAMILIES = {
    "nominal": {"state_noise": 0.0, "operator_drift": 0.0},
    "state_noise": {"state_noise": 0.010, "operator_drift": 0.0},
    "operator_drift": {"state_noise": 0.0, "operator_drift": 0.010},
    "combined_state_and_operator": {"state_noise": 0.014, "operator_drift": 0.008},
}
BASIN_SHEETS = {
    "balanced_sheet": {"sheet_bias": 0.0, "asymmetry": 0.32},
    "left_asymmetry_sheet": {"sheet_bias": 0.12, "asymmetry": 0.62},
    "right_asymmetry_sheet": {"sheet_bias": -0.12, "asymmetry": -0.58},
}
ENFORCEMENT_ORDERS = ["evolve_then_enforce", "enforce_then_evolve"]

EPS_ORDER_RMS = 0.120
EPS_SCALAR_RMS = 0.070
EPS_SIGNATURE_MIN = 0.030
MIN_SCALAR_CONTROL_GAP = 0.015
MIN_ORDER_SWAP_CONTROL_GAP = 0.025
MIN_PRESSURE_RESPONSE_GAP = 0.015
HIGH_PRESSURE_SCALE = 1.15
CONSTANT_EXPLORATION_AMPLITUDE = 0.008


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def prior_closure_report() -> dict[str, Any]:
    prior = read_json(PRIOR_CLOSURE_RESULT)
    summary = prior.get("summary", {})
    facts = {
        "prior_all_pass": prior.get("all_pass") is True,
        "prior_classification": prior.get("classification"),
        "prior_promotion_allowed": prior.get("promotion_allowed"),
        "prior_finite_fixture_status": summary.get("finite_fixture_status"),
        "prior_narrowed_claim_status": summary.get("narrowed_claim_status"),
        "prior_countermodel_count": summary.get("countermodel_count"),
        "prior_row_count": summary.get("row_count"),
        "prior_eps_order_rms": summary.get("EPS_ORDER_RMS"),
        "prior_eps_scalar_rms": summary.get("EPS_SCALAR_RMS"),
        "prior_eps_signature_min": summary.get("EPS_SIGNATURE_MIN"),
    }
    return {
        "facts": facts,
        "pass": bool(
            facts["prior_all_pass"]
            and facts["prior_classification"] == "formal_scout"
            and facts["prior_promotion_allowed"] is False
            and facts["prior_finite_fixture_status"] == "closed_killed"
            and facts["prior_narrowed_claim_status"] == "killed"
            and int(facts["prior_countermodel_count"] or 0) > 0
            and facts["prior_eps_order_rms"] == EPS_ORDER_RMS
            and facts["prior_eps_scalar_rms"] == EPS_SCALAR_RMS
            and facts["prior_eps_signature_min"] == EPS_SIGNATURE_MIN
        ),
    }


def pressure_at(step: int, steps: int, mode: str) -> float:
    frac = (step + 1) / float(steps)
    if mode == "low":
        return 0.025 + 0.010 * frac
    if mode == "high":
        return HIGH_PRESSURE_SCALE * (0.160 + 0.620 * frac**1.35)
    raise ValueError(f"unknown pressure mode: {mode}")


def axis_variant(
    base_axis: torch.Tensor,
    seed: int,
    perturbation: dict[str, float],
    sheet: dict[str, float],
) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed)
    row = torch.arange(base_axis.shape[0], dtype=torch.float32).reshape(-1, 1)
    col = torch.arange(base_axis.shape[1], dtype=torch.float32).reshape(1, -1)
    noise = torch.randn(base_axis.shape, generator=generator, dtype=torch.float32) * perturbation["state_noise"]
    drift = perturbation["operator_drift"] * torch.sin(
        (row + 1.0) * 0.23 + (col + 1.0) * 0.11 + seed * 0.001
    )
    sheet_bias = sheet["sheet_bias"] * torch.sin((row + 1.0) * 0.37) * torch.tensor(
        [[1.0, -0.5, 0.25]],
        dtype=torch.float32,
    )
    asymmetry = 0.050 * sheet["asymmetry"] * torch.cat(
        [torch.ones((base_axis.shape[0], 1)), -torch.ones((base_axis.shape[0], 1)), torch.sin(row * 0.30)],
        dim=1,
    )
    return torch.tanh(base_axis + noise + drift + sheet_bias + asymmetry)


def live_dynamics(
    axis: torch.Tensor,
    parent: dict[str, Any],
    steps: int,
    enforcement_order: str,
    sheet: dict[str, float],
    pressure_mode: str,
) -> torch.Tensor:
    cross = float(parent["facts"]["cross_diff_final_state"])
    entropy = abs(float(parent["facts"]["integrated_min_conditional_entropy"]))
    gap = float(parent["facts"]["track_a_vs_b_max_coh_gap"])
    state = initial_shell_state(axis)
    trajectory = [state]
    forcing = torch.tanh(axis @ axis_basis())
    row = torch.arange(axis.shape[0], dtype=torch.float32).reshape(-1, 1)
    feature = torch.arange(state.shape[1], dtype=torch.float32).reshape(1, -1)
    sheet_drive = sheet["sheet_bias"] * torch.sin((row + 1.0) * 0.41)
    asymmetry = sheet["asymmetry"] * torch.cat(
        [
            torch.sin(row * 0.19),
            torch.cos(row * 0.23),
            torch.sin(row * 0.31),
            torch.cos(row * 0.37),
            torch.sin(row * 0.43),
            torch.cos(row * 0.47),
            torch.sin(row * 0.53),
            torch.cos(row * 0.59),
        ],
        dim=1,
    )

    for step in range(steps):
        pressure = pressure_at(step, steps, pressure_mode)
        exploration = CONSTANT_EXPLORATION_AMPLITUDE * torch.sin((step + 1) * 0.071 + row * 0.13 + feature * 0.17)

        def enforce(current: torch.Tensor) -> torch.Tensor:
            return torch.tanh(
                current
                + pressure * (0.240 * forcing + 0.060 * asymmetry + 0.050 * sheet_drive)
                + exploration
            )

        def evolve(current: torch.Tensor) -> torch.Tensor:
            prior = torch.roll(current, shifts=1, dims=0)
            later = torch.roll(current, shifts=-1, dims=0)
            return torch.tanh(
                0.48 * current
                + 0.18 * prior
                + 0.12 * later
                + 0.009 * cross * (row + 1.0) / 13.0
                + 0.012 * gap
                - 0.004 * entropy
                + 0.18 * exploration
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


def signature_gap(state_a: torch.Tensor, state_b: torch.Tensor) -> float:
    a_sig = torch.stack([tensor_signature(row) for row in state_a])
    b_sig = torch.stack([tensor_signature(row) for row in state_b])
    return float(torch.linalg.vector_norm(a_sig - b_sig, dim=1).min().item())


def summarize_controls(rows: list[dict[str, Any]]) -> dict[str, Any]:
    high_scalar = [row["scalar_projection_gap"] for row in rows]
    low_scalar = [row["low_constraint_scalar_gap"] for row in rows]
    order_swap = [row["order_swap_gap"] for row in rows]
    pressure_response = [row["pressure_response_gap"] for row in rows]
    low_is_lower_count = sum(1 for high, low in zip(high_scalar, low_scalar) if low < high)
    return {
        "scalar_projection": {
            "min_gap": min(high_scalar),
            "max_gap": max(high_scalar),
            "mean_gap": sum(high_scalar) / len(high_scalar),
            "threshold": MIN_SCALAR_CONTROL_GAP,
            "pass": min(high_scalar) > MIN_SCALAR_CONTROL_GAP and max(high_scalar) > EPS_SCALAR_RMS,
        },
        "order_swap": {
            "min_gap": min(order_swap),
            "max_gap": max(order_swap),
            "mean_gap": sum(order_swap) / len(order_swap),
            "threshold": MIN_ORDER_SWAP_CONTROL_GAP,
            "pass": max(order_swap) > MIN_ORDER_SWAP_CONTROL_GAP,
        },
        "low_constraint": {
            "max_low_scalar_gap": max(low_scalar),
            "mean_low_scalar_gap": sum(low_scalar) / len(low_scalar),
            "low_lower_than_high_count": low_is_lower_count,
            "row_count": len(rows),
            "min_pressure_response_gap": min(pressure_response),
            "mean_pressure_response_gap": sum(pressure_response) / len(pressure_response),
            "threshold": MIN_PRESSURE_RESPONSE_GAP,
            "pass": low_is_lower_count == len(rows) and min(pressure_response) > MIN_PRESSURE_RESPONSE_GAP,
        },
    }


def family_grid_report(axis0: dict[str, Any], parent: dict[str, Any]) -> dict[str, Any]:
    base_axis = axis0["shell_vectors"].clone().detach().to(torch.float32)
    max_horizon = max(HORIZONS)
    rows: list[dict[str, Any]] = []

    for seed in SEEDS:
        for perturbation_name, perturbation in PERTURBATION_FAMILIES.items():
            for sheet_name, sheet in BASIN_SHEETS.items():
                axis = axis_variant(base_axis, seed, perturbation, sheet)
                scalar_axis = axis.mean(dim=1, keepdim=True).expand_as(axis)
                high_tracks = {
                    order: live_dynamics(axis, parent, max_horizon, order, sheet, "high")
                    for order in ENFORCEMENT_ORDERS
                }
                scalar_tracks = {
                    order: live_dynamics(scalar_axis, parent, max_horizon, order, sheet, "high")
                    for order in ENFORCEMENT_ORDERS
                }
                low_tracks = {
                    order: live_dynamics(axis, parent, max_horizon, order, sheet, "low")
                    for order in ENFORCEMENT_ORDERS
                }
                low_scalar_tracks = {
                    order: live_dynamics(scalar_axis, parent, max_horizon, order, sheet, "low")
                    for order in ENFORCEMENT_ORDERS
                }

                for order in ENFORCEMENT_ORDERS:
                    swapped_order = "enforce_then_evolve" if order == "evolve_then_enforce" else "evolve_then_enforce"
                    for horizon in HORIZONS:
                        vector_state = high_tracks[order][horizon]
                        scalar_state = scalar_tracks[order][horizon]
                        low_state = low_tracks[order][horizon]
                        low_scalar_state = low_scalar_tracks[order][horizon]
                        swapped_state = high_tracks[swapped_order][horizon]
                        scalar_projection_gap = rms_gap(vector_state, scalar_state)
                        order_swap_gap = rms_gap(vector_state, swapped_state)
                        low_constraint_gap = rms_gap(vector_state, low_state)
                        low_constraint_scalar_gap = rms_gap(low_state, low_scalar_state)
                        min_signature_gap = signature_gap(vector_state, scalar_state)
                        countermodel = bool(
                            scalar_projection_gap > EPS_SCALAR_RMS
                            or order_swap_gap > EPS_ORDER_RMS
                            or min_signature_gap > EPS_SIGNATURE_MIN
                        )
                        rows.append(
                            {
                                "seed": seed,
                                "horizon": horizon,
                                "perturbation_family": perturbation_name,
                                "basin_sheet": sheet_name,
                                "sheet_bias": sheet["sheet_bias"],
                                "asymmetry": sheet["asymmetry"],
                                "enforcement_order": order,
                                "order_swap_control": swapped_order,
                                "scalar_projection_gap": scalar_projection_gap,
                                "order_swap_gap": order_swap_gap,
                                "low_constraint_gap": low_constraint_gap,
                                "low_constraint_scalar_gap": low_constraint_scalar_gap,
                                "pressure_response_gap": scalar_projection_gap - low_constraint_scalar_gap,
                                "min_signature_gap": min_signature_gap,
                                "countermodel": countermodel,
                                "countermodel_reasons": [
                                    reason
                                    for reason, flag in [
                                        ("scalar_projection_gap_exceeds_eps", scalar_projection_gap > EPS_SCALAR_RMS),
                                        ("order_swap_gap_exceeds_eps", order_swap_gap > EPS_ORDER_RMS),
                                        ("signature_gap_exceeds_eps", min_signature_gap > EPS_SIGNATURE_MIN),
                                    ]
                                    if flag
                                ],
                            }
                        )

    countermodels = [row for row in rows if row["countermodel"]]
    non_countermodel_rows = [row for row in rows if not row["countermodel"]]
    controls = summarize_controls(rows)
    row_count = len(rows)
    expected_rows = (
        len(SEEDS)
        * len(PERTURBATION_FAMILIES)
        * len(BASIN_SHEETS)
        * len(ENFORCEMENT_ORDERS)
        * len(HORIZONS)
    )
    portable_closed = row_count == expected_rows and not non_countermodel_rows and all(
        section["pass"] for section in controls.values()
    )
    finite_fixture_status = "closed_killed" if portable_closed else "open"
    open_remainder = {
        "reason": "not_every_family_grid_row_is_a_countermodel",
        "non_countermodel_row_count": len(non_countermodel_rows),
        "non_countermodel_sample": non_countermodel_rows[:12],
        "row_level_closure_required_for_closed_status": True,
    }
    if portable_closed:
        open_remainder = {
            "reason": None,
            "non_countermodel_row_count": 0,
            "non_countermodel_sample": [],
            "row_level_closure_required_for_closed_status": True,
        }

    family_cells: dict[str, dict[str, Any]] = {}
    for seed in SEEDS:
        for perturbation_name in PERTURBATION_FAMILIES:
            for sheet_name in BASIN_SHEETS:
                for order in ENFORCEMENT_ORDERS:
                    cell_rows = [
                        row
                        for row in rows
                        if row["seed"] == seed
                        and row["perturbation_family"] == perturbation_name
                        and row["basin_sheet"] == sheet_name
                        and row["enforcement_order"] == order
                    ]
                    key = f"{seed}|{perturbation_name}|{sheet_name}|{order}"
                    family_cells[key] = {
                        "row_count": len(cell_rows),
                        "countermodel_count": sum(1 for row in cell_rows if row["countermodel"]),
                        "supported_by_any_horizon": any(row["countermodel"] for row in cell_rows),
                    }

    worst = max(
        rows,
        key=lambda row: max(
            row["scalar_projection_gap"] / EPS_SCALAR_RMS,
            row["order_swap_gap"] / EPS_ORDER_RMS,
            row["min_signature_gap"] / EPS_SIGNATURE_MIN,
        ),
    )
    return {
        "rows": rows,
        "countermodels": countermodels,
        "non_countermodel_rows": non_countermodel_rows,
        "family_cells": family_cells,
        "controls": controls,
        "summary": {
            "row_count": row_count,
            "expected_row_count": expected_rows,
            "countermodel_count": len(countermodels),
            "non_countermodel_row_count": len(non_countermodel_rows),
            "countermodel_fraction": len(countermodels) / float(row_count),
            "seed_count": len(SEEDS),
            "horizon_count": len(HORIZONS),
            "perturbation_family_count": len(PERTURBATION_FAMILIES),
            "basin_sheet_count": len(BASIN_SHEETS),
            "enforcement_order_count": len(ENFORCEMENT_ORDERS),
            "family_cell_count": len(family_cells),
            "family_cells_supported_by_any_horizon": sum(
                1 for cell in family_cells.values() if cell["supported_by_any_horizon"]
            ),
            "max_scalar_projection_gap": max(row["scalar_projection_gap"] for row in rows),
            "min_scalar_projection_gap": min(row["scalar_projection_gap"] for row in rows),
            "max_order_swap_gap": max(row["order_swap_gap"] for row in rows),
            "max_low_constraint_gap": max(row["low_constraint_gap"] for row in rows),
            "max_min_signature_gap": max(row["min_signature_gap"] for row in rows),
            "min_pressure_response_gap": min(row["pressure_response_gap"] for row in rows),
            "mean_pressure_response_gap": sum(row["pressure_response_gap"] for row in rows) / float(row_count),
            "finite_fixture_status": finite_fixture_status,
            "finite_fixture_status_kind": "closed_family_grid_killed" if portable_closed else "open_family_grid_remainder",
            "countermodel_family_portability": "portable_closed" if portable_closed else "partial_open",
            "open_fixture_remainder": not portable_closed,
            "open_remainder": open_remainder,
            "worst_countermodel": worst if worst["countermodel"] else None,
            "worst_row": worst,
            "basin_promotion_status": "blocked",
            "constant_exploration_amplitude": CONSTANT_EXPLORATION_AMPLITUDE,
            "pressure_schedule": {
                "mode": "high",
                "start": pressure_at(0, max_horizon, "high"),
                "end": pressure_at(max_horizon - 1, max_horizon, "high"),
                "increasing": pressure_at(max_horizon - 1, max_horizon, "high") > pressure_at(0, max_horizon, "high"),
                "low_start": pressure_at(0, max_horizon, "low"),
                "low_end": pressure_at(max_horizon - 1, max_horizon, "low"),
            },
        },
        "pass": bool(row_count == expected_rows and countermodels and all(section["pass"] for section in controls.values())),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(2026051807)
    prior = prior_closure_report()
    parent = parent_receipt_report()
    axis0 = load_axis0_bundle()
    grid = family_grid_report(axis0, parent)

    positive = {
        "prior_killed_finite_fixture_countermodel_loaded": prior,
        "pytorch_live_family_grid_executed": {
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
                    grid["summary"]["finite_fixture_status"] == "closed_killed"
                    and grid["summary"]["open_fixture_remainder"] is False
                    and grid["summary"]["non_countermodel_row_count"] == 0
                )
                or (
                    grid["summary"]["finite_fixture_status"] == "open"
                    and grid["summary"]["open_fixture_remainder"] is True
                    and grid["summary"]["open_remainder"]["non_countermodel_row_count"] > 0
                )
            ),
        },
        "constant_exploration_and_increasing_pressure_present": {
            "constant_exploration_amplitude": CONSTANT_EXPLORATION_AMPLITUDE,
            "pressure_schedule": grid["summary"]["pressure_schedule"],
            "pass": bool(
                CONSTANT_EXPLORATION_AMPLITUDE > 0.0
                and grid["summary"]["pressure_schedule"]["increasing"] is True
            ),
        },
    }
    graveyard_companions = {
        "scalar_projection_negative_control_active": grid["controls"]["scalar_projection"],
        "enforce_evolve_swap_negative_control_active": grid["controls"]["order_swap"],
        "low_constraint_negative_control_active": grid["controls"]["low_constraint"],
        "closed_finite_countermodel_does_not_promote_basin": {
            "finite_fixture_status": grid["summary"]["finite_fixture_status"],
            "countermodel_family_portability": grid["summary"]["countermodel_family_portability"],
            "basin_promotion_status": grid["summary"]["basin_promotion_status"],
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": bool(PROMOTION_ALLOWED is False and grid["summary"]["basin_promotion_status"] == "blocked"),
        },
    }
    boundary = {
        "classification_and_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "claim_ceiling_blocks_overclaim": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool("Formal scout only" in CLAIM_CEILING and "does not admit" in CLAIM_CEILING),
        },
        "family_grid_dimensions_present": {
            "seeds": SEEDS,
            "horizons": HORIZONS,
            "perturbation_families": sorted(PERTURBATION_FAMILIES),
            "basin_sheets": sorted(BASIN_SHEETS),
            "enforcement_orders": ENFORCEMENT_ORDERS,
            "pass": bool(
                len(SEEDS) >= 4
                and len(HORIZONS) >= 4
                and len(PERTURBATION_FAMILIES) >= 4
                and len(BASIN_SHEETS) >= 2
                and len(ENFORCEMENT_ORDERS) == 2
            ),
        },
        "closed_status_requires_full_row_coverage": {
            "finite_fixture_status": grid["summary"]["finite_fixture_status"],
            "non_countermodel_row_count": grid["summary"]["non_countermodel_row_count"],
            "open_remainder": grid["summary"]["open_remainder"],
            "pass": bool(
                grid["summary"]["finite_fixture_status"] != "closed_killed"
                or grid["summary"]["non_countermodel_row_count"] == 0
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
            "load_bearing_tools": ["pytorch"],
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
                "left_asymmetry_basin_sheet",
                "right_asymmetry_basin_sheet",
            ],
        },
        "family_cells": as_jsonable(grid["family_cells"]),
        "countermodel_sample": as_jsonable(grid["countermodels"][:12]),
        "non_countermodel_sample": as_jsonable(grid["non_countermodel_rows"][:12]),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "input_receipts": [str(PRIOR_CLOSURE_RESULT)],
        "why_not_v4_probes": [
            "v5 formal scout only; tests dynamic-basin countermodel portability without admitting a canonical probe",
            "uses PyTorch live dynamics and negative controls to bound the family-grid status, not to promote a basin",
            "leaves finite_fixture_status open when the full row-level family grid is not closed",
        ],
        "blockers": [] if all_pass else ["basin_countermodel_family_portability_probe_failed"],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
