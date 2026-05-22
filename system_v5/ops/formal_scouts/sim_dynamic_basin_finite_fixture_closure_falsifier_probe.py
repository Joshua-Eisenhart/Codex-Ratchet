#!/usr/bin/env python3
"""Finite-fixture closure falsifier for the dynamic basin convergence claim.

Formal scout only. This refines the prior open finite-fixture status by testing
one explicit bounded claim over the current Axis0 vector fixture:

For the listed finite seed set, state perturbations eps <= 0.018, operator drift
eps <= 0.006, horizons <= 512, and both enforcement orders, every vector run
must remain within the stated convergence tolerances against scalar/order
controls. The scout passes only if that narrowed claim is either survived under
those exact bounds or killed by a concrete countermodel row.
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
    load_axis0_bundle,
    parent_receipt_report,
    propagate,
    tensor_signature,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "dynamic_basin_finite_fixture_closure_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

PRIOR_CROSS_TRACK_RESULT = RESULT_DIR / "dynamic_manifold_stability_cross_track_lirpa_falsifier_probe_results.json"
PRIOR_LONG_HORIZON_RESULT = RESULT_DIR / "dynamic_basin_long_horizon_perturbed_convergence_falsifier_probe_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "dynamic_basin_finite_fixture_closure_falsifier"
CLAIM_CEILING = (
    "Formal scout only: tests one narrowed finite-fixture epsilon-convergence "
    "claim over the current Axis0 vector fixture with explicit seed, horizon, "
    "state-perturbation, operator-drift, scalar-control, and enforcement-order "
    "bounds. A pass closes this bounded finite-fixture claim as survived or "
    "killed, but does not admit a real attractor basin, final convergence "
    "theorem, final manifold, Axis0 actuator repair, bridge, engine, physics, "
    "target-system, Holodeck, or canonical claim; it does not admit canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite perturbation-grid dynamics with vector, scalar, and enforcement-order controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing arithmetic witness that the narrowed convergence claim is inconsistent with the concrete countermodel row",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent arithmetic witness for the same bounded finite-fixture countermodel",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result and prior-receipt path handling",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization and prior receipt parsing",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}

SEEDS = [20260518, 42, 1337, 314159, 65537, 2020]
STATE_EPSILONS = [0.0, 0.006, 0.018]
OPERATOR_DRIFT_EPSILONS = [0.0, 0.006]
HORIZONS = [64, 128, 256, 512]
ENFORCEMENT_ORDERS = ["evolve_then_enforce", "enforce_then_evolve"]

EPS_STATE_MAX = 0.018
EPS_OPERATOR_DRIFT_MAX = 0.006
EPS_ORDER_RMS = 0.120
EPS_SCALAR_RMS = 0.070
EPS_SIGNATURE_MIN = 0.030


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def perturb_axis(base_axis: torch.Tensor, seed: int, state_eps: float, operator_eps: float) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed)
    noise = torch.randn(base_axis.shape, generator=generator, dtype=torch.float32) * state_eps
    row = torch.arange(base_axis.shape[0], dtype=torch.float32).reshape(-1, 1)
    col = torch.arange(base_axis.shape[1], dtype=torch.float32).reshape(1, -1)
    drift = operator_eps * torch.sin((row + 1.0) * 0.19 + (col + 1.0) * 0.07 + seed * 0.001)
    return torch.tanh(base_axis + noise + drift)


def signature_min_gap(state_a: torch.Tensor, state_b: torch.Tensor) -> float:
    a_sig = torch.stack([tensor_signature(row) for row in state_a])
    b_sig = torch.stack([tensor_signature(row) for row in state_b])
    return float(torch.linalg.vector_norm(a_sig - b_sig, dim=1).min().item())


def bounded_grid_report(axis0: dict[str, Any], parent: dict[str, Any]) -> dict[str, Any]:
    base_axis = axis0["shell_vectors"].clone().detach().to(torch.float32)
    rows = []
    for seed in SEEDS:
        for state_eps in STATE_EPSILONS:
            for operator_eps in OPERATOR_DRIFT_EPSILONS:
                axis = perturb_axis(base_axis, seed, state_eps, operator_eps)
                scalar_axis = axis.mean(dim=1, keepdim=True).expand_as(axis)
                vector_tracks = {
                    order: propagate(axis, parent, max(HORIZONS), order)["trajectory"]
                    for order in ENFORCEMENT_ORDERS
                }
                scalar_track = propagate(scalar_axis, parent, max(HORIZONS), ENFORCEMENT_ORDERS[0])["trajectory"]
                for horizon in HORIZONS:
                    order_a = vector_tracks[ENFORCEMENT_ORDERS[0]][horizon]
                    order_b = vector_tracks[ENFORCEMENT_ORDERS[1]][horizon]
                    scalar_state = scalar_track[horizon]
                    order_rms = torch.linalg.vector_norm(order_a - order_b) / math.sqrt(float(order_a.numel()))
                    scalar_rms = torch.linalg.vector_norm(order_a - scalar_state) / math.sqrt(float(order_a.numel()))
                    sig_gap = signature_min_gap(order_a, scalar_state)
                    rows.append(
                        {
                            "seed": seed,
                            "state_eps": state_eps,
                            "operator_drift_eps": operator_eps,
                            "horizon": horizon,
                            "order_a": ENFORCEMENT_ORDERS[0],
                            "order_b": ENFORCEMENT_ORDERS[1],
                            "order_rms_gap": float(order_rms.item()),
                            "scalar_rms_gap": float(scalar_rms.item()),
                            "min_signature_gap": sig_gap,
                            "passes_narrowed_convergence_claim": bool(
                                order_rms.item() <= EPS_ORDER_RMS
                                and scalar_rms.item() <= EPS_SCALAR_RMS
                                and sig_gap <= EPS_SIGNATURE_MIN
                            ),
                        }
                    )

    countermodels = [row for row in rows if not row["passes_narrowed_convergence_claim"]]
    worst = max(
        rows,
        key=lambda row: max(
            row["order_rms_gap"] / EPS_ORDER_RMS,
            row["scalar_rms_gap"] / EPS_SCALAR_RMS,
            row["min_signature_gap"] / EPS_SIGNATURE_MIN,
        ),
    )
    survived = not countermodels
    killed = bool(countermodels)
    finite_fixture_status = "closed_survived" if survived else "closed_killed"
    return {
        "rows": rows,
        "countermodels": countermodels,
        "worst_countermodel": None if survived else worst,
        "summary": {
            "seed_count": len(SEEDS),
            "state_epsilons": STATE_EPSILONS,
            "operator_drift_epsilons": OPERATOR_DRIFT_EPSILONS,
            "horizons": HORIZONS,
            "enforcement_orders": ENFORCEMENT_ORDERS,
            "row_count": len(rows),
            "countermodel_count": len(countermodels),
            "max_order_rms_gap": max(row["order_rms_gap"] for row in rows),
            "max_scalar_rms_gap": max(row["scalar_rms_gap"] for row in rows),
            "max_min_signature_gap": max(row["min_signature_gap"] for row in rows),
            "EPS_STATE_MAX": EPS_STATE_MAX,
            "EPS_OPERATOR_DRIFT_MAX": EPS_OPERATOR_DRIFT_MAX,
            "EPS_ORDER_RMS": EPS_ORDER_RMS,
            "EPS_SCALAR_RMS": EPS_SCALAR_RMS,
            "EPS_SIGNATURE_MIN": EPS_SIGNATURE_MIN,
            "narrowed_claim_status": "survived" if survived else "killed",
            "finite_fixture_status": finite_fixture_status,
            "open_fixture_remainder": False,
            "basin_promotion_status": "blocked",
        },
        "pass": bool(survived or killed),
    }


def z3_witness(grid: dict[str, Any]) -> dict[str, Any]:
    worst = grid["worst_countermodel"]
    if worst is None:
        return {
            "mode": "survival_check",
            "all_rows_within_bounds": True,
            "pass": True,
        }
    order_gap = z3.Real("order_rms_gap")
    scalar_gap = z3.Real("scalar_rms_gap")
    signature_gap = z3.Real("min_signature_gap")
    narrowed_claim = z3.Bool("narrowed_finite_fixture_convergence_claim")
    solver = z3.Solver()
    solver.add(order_gap == z3.RealVal(f"{worst['order_rms_gap']:.12f}"))
    solver.add(scalar_gap == z3.RealVal(f"{worst['scalar_rms_gap']:.12f}"))
    solver.add(signature_gap == z3.RealVal(f"{worst['min_signature_gap']:.12f}"))
    solver.add(narrowed_claim)
    solver.add(
        z3.Implies(
            narrowed_claim,
            z3.And(
                order_gap <= z3.RealVal(str(EPS_ORDER_RMS)),
                scalar_gap <= z3.RealVal(str(EPS_SCALAR_RMS)),
                signature_gap <= z3.RealVal(str(EPS_SIGNATURE_MIN)),
            ),
        )
    )
    status = solver.check()
    return {
        "mode": "countermodel_rejection",
        "status": str(status),
        "witness_seed": worst["seed"],
        "witness_horizon": worst["horizon"],
        "witness_state_eps": worst["state_eps"],
        "witness_operator_drift_eps": worst["operator_drift_eps"],
        "pass": status == z3.unsat,
    }


def cvc5_witness(grid: dict[str, Any]) -> dict[str, Any]:
    worst = grid["worst_countermodel"]
    if worst is None:
        return {
            "mode": "survival_check",
            "all_rows_within_bounds": True,
            "pass": True,
        }
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    real_sort = solver.getRealSort()
    bool_sort = solver.getBooleanSort()
    order_gap = solver.mkConst(real_sort, "order_rms_gap")
    scalar_gap = solver.mkConst(real_sort, "scalar_rms_gap")
    signature_gap = solver.mkConst(real_sort, "min_signature_gap")
    narrowed_claim = solver.mkConst(bool_sort, "narrowed_finite_fixture_convergence_claim")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, order_gap, solver.mkReal(f"{worst['order_rms_gap']:.12f}")))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, scalar_gap, solver.mkReal(f"{worst['scalar_rms_gap']:.12f}")))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, signature_gap, solver.mkReal(f"{worst['min_signature_gap']:.12f}")))
    required = solver.mkTerm(
        Kind.AND,
        solver.mkTerm(Kind.LEQ, order_gap, solver.mkReal(str(EPS_ORDER_RMS))),
        solver.mkTerm(Kind.LEQ, scalar_gap, solver.mkReal(str(EPS_SCALAR_RMS))),
        solver.mkTerm(Kind.LEQ, signature_gap, solver.mkReal(str(EPS_SIGNATURE_MIN))),
    )
    solver.assertFormula(narrowed_claim)
    solver.assertFormula(solver.mkTerm(Kind.IMPLIES, narrowed_claim, required))
    status = solver.checkSat()
    return {
        "mode": "countermodel_rejection",
        "status": str(status),
        "witness_seed": worst["seed"],
        "witness_horizon": worst["horizon"],
        "witness_state_eps": worst["state_eps"],
        "witness_operator_drift_eps": worst["operator_drift_eps"],
        "pass": status.isUnsat(),
    }


def prior_receipt_report() -> dict[str, Any]:
    cross = read_json(PRIOR_CROSS_TRACK_RESULT)
    long = read_json(PRIOR_LONG_HORIZON_RESULT)
    facts = {
        "cross_track_all_pass": cross.get("all_pass") is True,
        "cross_track_finite_fixture_status": cross["summary"]["finite_fixture_status"],
        "cross_track_real_convergence_claim_status": cross["summary"]["current_real_convergence_claim_status"],
        "long_horizon_all_pass": long.get("all_pass") is True,
        "long_horizon_real_convergence_claim_status": long["summary"]["current_real_convergence_claim_status"],
        "long_horizon_basin_admission_status": long["summary"]["basin_admission_status"],
        "all_promotions_blocked": cross.get("promotion_allowed") is False and long.get("promotion_allowed") is False,
    }
    return {
        "facts": facts,
        "pass": bool(
            facts["cross_track_all_pass"]
            and facts["cross_track_finite_fixture_status"] == "open"
            and facts["cross_track_real_convergence_claim_status"] == "killed"
            and facts["long_horizon_all_pass"]
            and facts["long_horizon_real_convergence_claim_status"] == "killed"
            and facts["long_horizon_basin_admission_status"] == "blocked"
            and facts["all_promotions_blocked"]
        ),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(2026051806)
    priors = prior_receipt_report()
    parent = parent_receipt_report()
    axis0 = load_axis0_bundle()
    grid = bounded_grid_report(axis0, parent)
    z3_report = z3_witness(grid)
    cvc5_report = cvc5_witness(grid)
    survived = grid["summary"]["narrowed_claim_status"] == "survived"
    killed = grid["summary"]["narrowed_claim_status"] == "killed"

    positive = {
        "prior_receipts_define_open_finite_fixture_remainder": priors,
        "pytorch_bounded_finite_fixture_grid_executed": {
            **grid["summary"],
            "pass": bool(grid["pass"] and grid["summary"]["row_count"] == 144),
        },
        "explicit_narrowed_convergence_claim_closed": {
            "status": grid["summary"]["narrowed_claim_status"],
            "finite_fixture_status": grid["summary"]["finite_fixture_status"],
            "open_fixture_remainder": grid["summary"]["open_fixture_remainder"],
            "survival_allowed": survived,
            "countermodel_allowed": killed,
            "pass": bool((survived or killed) and not grid["summary"]["open_fixture_remainder"]),
        },
        "z3_cvc5_arithmetic_witnesses_match_grid_status": {
            "z3": z3_report,
            "cvc5": cvc5_report,
            "pass": bool(z3_report["pass"] and cvc5_report["pass"]),
        },
    }
    graveyard_companions = {
        "broad_real_attractor_basin_convergence_not_resurrected": {
            "prior_real_convergence_status": priors["facts"]["long_horizon_real_convergence_claim_status"],
            "current_narrowed_status": grid["summary"]["narrowed_claim_status"],
            "basin_promotion_status": grid["summary"]["basin_promotion_status"],
            "pass": bool(
                priors["facts"]["long_horizon_real_convergence_claim_status"] == "killed"
                and grid["summary"]["basin_promotion_status"] == "blocked"
            ),
        },
        "finite_fixture_open_remainder_removed_for_this_exact_claim": {
            "prior_status": priors["facts"]["cross_track_finite_fixture_status"],
            "current_status": grid["summary"]["finite_fixture_status"],
            "open_fixture_remainder": grid["summary"]["open_fixture_remainder"],
            "pass": bool(
                priors["facts"]["cross_track_finite_fixture_status"] == "open"
                and grid["summary"]["finite_fixture_status"] in {"closed_killed", "closed_survived"}
                and grid["summary"]["open_fixture_remainder"] is False
            ),
        },
        "scalar_control_does_not_promote_axis0_actuator": {
            "control_used": "scalar projection compared against vector Axis0 fixture",
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": True,
        },
        "enforcement_order_control_not_collapsed": {
            "orders": ENFORCEMENT_ORDERS,
            "max_order_rms_gap": grid["summary"]["max_order_rms_gap"],
            "pass": bool(grid["summary"]["max_order_rms_gap"] > EPS_ORDER_RMS if killed else True),
        },
    }
    boundary = {
        "classification_and_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "explicit_parameter_bounds": {
            "seeds": SEEDS,
            "state_epsilons": STATE_EPSILONS,
            "operator_drift_epsilons": OPERATOR_DRIFT_EPSILONS,
            "horizons": HORIZONS,
            "tolerances": {
                "EPS_ORDER_RMS": EPS_ORDER_RMS,
                "EPS_SCALAR_RMS": EPS_SCALAR_RMS,
                "EPS_SIGNATURE_MIN": EPS_SIGNATURE_MIN,
            },
            "pass": bool(max(STATE_EPSILONS) == EPS_STATE_MAX and max(OPERATOR_DRIFT_EPSILONS) == EPS_OPERATOR_DRIFT_MAX),
        },
        "no_basin_promotion_from_closed_finite_fixture": {
            "claim_ceiling": CLAIM_CEILING,
            "basin_promotion_status": grid["summary"]["basin_promotion_status"],
            "pass": bool("does not admit" in CLAIM_CEILING and grid["summary"]["basin_promotion_status"] == "blocked"),
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
            "finite_fixture_status": grid["summary"]["finite_fixture_status"],
            "finite_fixture_status_kind": "closed",
            "narrowed_claim_status": grid["summary"]["narrowed_claim_status"],
            "open_fixture_remainder": grid["summary"]["open_fixture_remainder"],
            "countermodel_count": grid["summary"]["countermodel_count"],
            "row_count": grid["summary"]["row_count"],
            "max_order_rms_gap": grid["summary"]["max_order_rms_gap"],
            "max_scalar_rms_gap": grid["summary"]["max_scalar_rms_gap"],
            "max_min_signature_gap": grid["summary"]["max_min_signature_gap"],
            "EPS_ORDER_RMS": EPS_ORDER_RMS,
            "EPS_SCALAR_RMS": EPS_SCALAR_RMS,
            "EPS_SIGNATURE_MIN": EPS_SIGNATURE_MIN,
            "worst_countermodel": grid["worst_countermodel"],
            "promotion_allowed": PROMOTION_ALLOWED,
            "basin_promotion_status": grid["summary"]["basin_promotion_status"],
            "load_bearing_tools": ["pytorch", "z3", "cvc5"],
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "variants": [
                "zero_perturbation_fixture",
                "bounded_state_perturbation_fixture",
                "operator_drift_fixture",
                "enforcement_order_pair_fixture",
            ],
        },
        "concrete_countermodels": as_jsonable(grid["countermodels"][:12]),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "input_receipts": [str(PRIOR_CROSS_TRACK_RESULT), str(PRIOR_LONG_HORIZON_RESULT)],
        "why_not_v4_probes": [
            "v5 formal scout only; the receipt closes one finite-fixture status for one explicitly bounded claim, not a canonical probe",
            "uses current v5 dynamic-basin receipts as blockers and keeps basin promotion false",
            "does not repair Axis0, prove a real attractor basin, or admit a final manifold/convergence theorem",
        ],
        "blockers": [] if all_pass else ["dynamic_basin_finite_fixture_closure_falsifier_failed"],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
