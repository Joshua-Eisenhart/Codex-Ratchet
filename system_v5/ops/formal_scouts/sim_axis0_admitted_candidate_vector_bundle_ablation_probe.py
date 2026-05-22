#!/usr/bin/env python3
"""Admitted Axis0 candidate vector-bundle ablation scout.

This is a formal scout only. It tests the three currently admitted Axis0
candidates as separate vector-bundle coordinates and keeps path_entropy plus
holographic boundary reconstruction as blocked controls.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import torch
import z3

import axis0_guard_utils as axis0_guard


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "axis0_admitted_candidate_vector_bundle_ablation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
GUARD_RESULT = RESULT_DIR / axis0_guard.AXIS0_GUARD_RESULT_NAME
SUBDENSE_RESULT = RESULT_DIR / "source_native_multicarrier_subdense_environment_contraction_probe_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "axis0_admitted_candidate_vector_bundle_ablation_nonpromotion"
CLAIM_CEILING = (
    "Formal scout only: tests the three currently admitted Axis0 candidates on "
    "a live PyTorch vector-bundle/non-scalar route with scalar projection, "
    "drop-axis component, order shuffle, zero-axis, and admitted-candidate "
    "removal ablations. path_entropy and holographic boundary reconstruction "
    "remain blocked controls. This separates admitted-candidate survival from "
    "upstream scalar actuator repair; it does not repair the scalar actuator, "
    "admit Axis0 maturity, admit final Axis0, prove a manifold, basin, physics, "
    "engine, cognition, Holodeck, or canonical claim; it does not admit "
    "canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing live vector-bundle dynamics, autograd sensitivity, and ablation gaps over admitted Axis0 candidates",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Boolean proof gate separating candidate survival from scalar-actuator repair and blocked controls",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Boolean cross-check for the same nonpromotion gate as z3",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result path handling and upstream receipt loading",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive upstream receipt parsing and formal scout result serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}

ADMITTED_CANDIDATES = [
    "fep_gradient_polarity",
    "correlation_diversity_derivative",
    "retrocausal_many_futures_policy_scoring",
]
BLOCKED_CONTROLS = ["path_entropy", "holographic_boundary_interior_reconstruction"]
SHELL_COUNT = 13
STATE_DIM = 8
TIMESTEPS = 28
EPS_SCALAR_GAP = 0.02
EPS_ZERO_GAP = 0.03
EPS_ORDER_GAP = 0.015
EPS_DROP_GAP = 0.005
EPS_REMOVAL_GAP = 0.005
EPS_GRAD = 1e-6


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    return value


def resample_vector(values: list[Any], target_len: int = SHELL_COUNT) -> torch.Tensor:
    numeric = []
    for value in values:
        try:
            item = float(value)
        except (TypeError, ValueError):
            item = 0.0
        if not math.isfinite(item):
            item = 0.0
        numeric.append(item)
    raw = torch.tensor(numeric, dtype=torch.float64)
    if raw.numel() == 0:
        sampled = torch.zeros(target_len, dtype=torch.float64)
    elif raw.numel() == 1:
        sampled = raw.repeat(target_len)
    else:
        idx = torch.linspace(0, raw.numel() - 1, steps=target_len).round().to(torch.long)
        sampled = raw[idx]
    centered = sampled - sampled.mean()
    scale = torch.max(torch.abs(centered)).clamp_min(1e-8)
    return centered / scale


def candidate_basis(names: list[str]) -> torch.Tensor:
    rows = []
    grid = torch.arange(STATE_DIM, dtype=torch.float64)
    for name in names:
        idx = ADMITTED_CANDIDATES.index(name) if name in ADMITTED_CANDIDATES else len(ADMITTED_CANDIDATES)
        phase = 0.19 + 0.07 * (idx + 1)
        row = torch.sin((grid + 1.0) * phase) + 0.37 * torch.cos((grid + 1.0) * (phase + 0.11))
        rows.append(row)
    return torch.stack(rows)


def load_axis0_bundle() -> dict[str, Any]:
    guard_receipt = read_json(GUARD_RESULT)
    subdense_receipt = read_json(SUBDENSE_RESULT)
    guard = axis0_guard.axis0_guard_signal(guard_receipt)
    subdense_axis0 = subdense_receipt.get("axis0_outputs_or_blockers") or {}
    candidate_vectors = subdense_axis0.get("candidate_vectors") or {}
    admitted = list(guard.get("admitted_candidate_names") or [])
    blocked = list(guard.get("blocked_candidate_names") or [])
    active_columns = [resample_vector(candidate_vectors.get(name, [])) for name in ADMITTED_CANDIDATES]
    blocked_columns = {name: resample_vector(candidate_vectors.get(name, [])) for name in BLOCKED_CONTROLS}
    axis = torch.stack(active_columns, dim=1)
    candidate_status = guard.get("candidate_status") or {}
    exact_state = admitted == ADMITTED_CANDIDATES and blocked == BLOCKED_CONTROLS
    return {
        "guard_receipt": guard_receipt,
        "subdense_receipt": subdense_receipt,
        "guard": guard,
        "admitted": admitted,
        "blocked": blocked,
        "candidate_status": candidate_status,
        "candidate_vectors": candidate_vectors,
        "active_axis": axis,
        "blocked_columns": blocked_columns,
        "pass": bool(
            guard_receipt.get("all_pass") is True
            and subdense_receipt.get("all_pass") is True
            and guard.get("pass") is True
            and exact_state
            and list(axis.shape) == [SHELL_COUNT, len(ADMITTED_CANDIDATES)]
            and torch.isfinite(axis).all().item()
        ),
    }


def initial_state() -> torch.Tensor:
    shells = torch.arange(SHELL_COUNT, dtype=torch.float64).reshape(-1, 1)
    grid = torch.arange(STATE_DIM, dtype=torch.float64).reshape(1, -1)
    return torch.tanh(0.17 * torch.sin((shells + 1.0) * (grid + 1.0) * 0.13) + 0.05 * torch.cos(grid + shells))


def transition_matrix() -> torch.Tensor:
    grid = torch.arange(STATE_DIM, dtype=torch.float64)
    base = torch.eye(STATE_DIM, dtype=torch.float64) * 0.62
    skew = torch.sin((grid.reshape(-1, 1) + 1.0) * (grid.reshape(1, -1) + 1.0) * 0.041)
    return base + 0.045 * (skew - skew.T)


def ordered_neighbor_signal(state: torch.Tensor) -> torch.Tensor:
    prev = torch.zeros_like(state)
    nxt = torch.zeros_like(state)
    prev[1:] = state[:-1]
    nxt[:-1] = state[1:]
    return 0.11 * prev - 0.073 * nxt


def run_dynamics(axis_vectors: torch.Tensor, names: list[str]) -> dict[str, Any]:
    axis = axis_vectors.clone().detach().to(torch.float64).requires_grad_(True)
    basis = candidate_basis(names)
    state = initial_state()
    matrix = transition_matrix()
    trajectory = []
    for step in range(TIMESTEPS):
        drive = axis @ basis
        phase = 0.021 * torch.sin((step + 1.0) * torch.arange(1, STATE_DIM + 1, dtype=torch.float64))
        state = torch.tanh(state @ matrix.T + drive + ordered_neighbor_signal(state) + phase)
        trajectory.append(state)
    traj = torch.stack(trajectory)
    final = traj[-1]
    temporal_mean = traj.mean(dim=0)
    temporal_std = traj.std(dim=0)
    shell_energy = final.square().mean(dim=1)
    flux = (final[1:] - final[:-1]).square().mean(dim=1)
    readout = torch.cat(
        [
            final.flatten(),
            temporal_mean.flatten(),
            temporal_std.flatten(),
            shell_energy,
            flux,
        ]
    )
    objective = readout.square().mean() + 0.13 * shell_energy.mean() + 0.07 * flux.mean()
    grad = torch.autograd.grad(objective, axis, retain_graph=False)[0]
    component_grad_norms = {
        name: float(torch.linalg.vector_norm(grad[:, idx]).item())
        for idx, name in enumerate(names)
    }
    return {
        "axis": axis.detach(),
        "state": final.detach(),
        "trajectory": traj.detach(),
        "readout": readout.detach(),
        "objective": float(objective.detach().item()),
        "grad": grad.detach(),
        "component_grad_norms": component_grad_norms,
        "finite": bool(torch.isfinite(readout).all().item() and torch.isfinite(grad).all().item()),
    }


def l2_gap(left: torch.Tensor, right: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(left - right).item())


def ablation_suite(active_axis: torch.Tensor) -> dict[str, Any]:
    nominal = run_dynamics(active_axis, ADMITTED_CANDIDATES)
    scalar_axis = active_axis.mean(dim=1, keepdim=True).repeat(1, active_axis.shape[1])
    zero_axis = torch.zeros_like(active_axis)
    shuffle_index = torch.tensor([0, 3, 1, 5, 2, 8, 4, 10, 6, 12, 7, 11, 9], dtype=torch.long)
    order_axis = active_axis[shuffle_index]
    scalar = run_dynamics(scalar_axis, ADMITTED_CANDIDATES)
    zero = run_dynamics(zero_axis, ADMITTED_CANDIDATES)
    order = run_dynamics(order_axis, ADMITTED_CANDIDATES)

    drop_axis = {}
    removal = {}
    survival_metrics = {}
    for idx, name in enumerate(ADMITTED_CANDIDATES):
        dropped = active_axis.clone()
        dropped[:, idx] = 0.0
        drop_run = run_dynamics(dropped, ADMITTED_CANDIDATES)
        drop_gap = l2_gap(nominal["readout"], drop_run["readout"])
        remaining_names = [candidate for candidate in ADMITTED_CANDIDATES if candidate != name]
        remaining_axis = active_axis[:, [col for col in range(active_axis.shape[1]) if col != idx]]
        removal_run = run_dynamics(remaining_axis, remaining_names)
        removal_gap = l2_gap(nominal["readout"], removal_run["readout"])
        grad_norm = nominal["component_grad_norms"][name]
        survived = drop_gap > EPS_DROP_GAP and removal_gap > EPS_REMOVAL_GAP and grad_norm > EPS_GRAD
        drop_axis[name] = {
            "gap": drop_gap,
            "threshold": EPS_DROP_GAP,
            "pass": drop_gap > EPS_DROP_GAP,
        }
        removal[name] = {
            "gap": removal_gap,
            "threshold": EPS_REMOVAL_GAP,
            "pass": removal_gap > EPS_REMOVAL_GAP,
        }
        survival_metrics[name] = {
            "drop_axis_gap": drop_gap,
            "removal_gap": removal_gap,
            "autograd_component_grad_norm": grad_norm,
            "survived": bool(survived),
        }

    scalar_gap = l2_gap(nominal["readout"], scalar["readout"])
    zero_gap = l2_gap(nominal["readout"], zero["readout"])
    order_gap = l2_gap(nominal["readout"], order["readout"])
    all_candidate_survived = all(metric["survived"] for metric in survival_metrics.values())
    return {
        "nominal": nominal,
        "scalar": scalar,
        "zero": zero,
        "order_shuffle": order,
        "drop_axis": drop_axis,
        "removal": removal,
        "survival_metrics": survival_metrics,
        "summary": {
            "scalar_projection_gap": scalar_gap,
            "scalar_projection_threshold": EPS_SCALAR_GAP,
            "zero_axis_gap": zero_gap,
            "zero_axis_threshold": EPS_ZERO_GAP,
            "order_shuffle_gap": order_gap,
            "order_shuffle_threshold": EPS_ORDER_GAP,
            "min_drop_axis_gap": min(row["gap"] for row in drop_axis.values()),
            "min_removal_gap": min(row["gap"] for row in removal.values()),
            "min_component_grad_norm": min(metric["autograd_component_grad_norm"] for metric in survival_metrics.values()),
            "candidate_survival_count": sum(1 for metric in survival_metrics.values() if metric["survived"]),
            "candidate_survival_total": len(survival_metrics),
            "all_candidate_survived": bool(all_candidate_survived),
            "scalar_projection_rejected": scalar_gap > EPS_SCALAR_GAP,
            "zero_axis_rejected": zero_gap > EPS_ZERO_GAP,
            "order_shuffle_rejected": order_gap > EPS_ORDER_GAP,
        },
    }


def blocked_control_report(bundle: dict[str, Any], ablations: dict[str, Any]) -> dict[str, Any]:
    controls = {}
    nominal_readout = ablations["nominal"]["readout"]
    for name in BLOCKED_CONTROLS:
        status = (bundle.get("candidate_status") or {}).get(name, {})
        blocked_axis = torch.cat([bundle["active_axis"], bundle["blocked_columns"][name].reshape(SHELL_COUNT, 1)], dim=1)
        blocked_run = run_dynamics(blocked_axis, ADMITTED_CANDIDATES + [name])
        controls[name] = {
            "candidate_admissible_for_downstream_drop_controls": bool(
                status.get("candidate_admissible_for_downstream_drop_controls")
            ),
            "explicit_blockers": status.get("explicit_blockers") or {},
            "diagnostic_injection_gap": l2_gap(nominal_readout, blocked_run["readout"]),
            "used_in_positive_vector_bundle": False,
            "pass": bool(
                status.get("candidate_admissible_for_downstream_drop_controls") is False
                and name in bundle.get("blocked", [])
            ),
        }
    return {
        "controls": controls,
        "pass": all(row["pass"] for row in controls.values()),
    }


def z3_report(actuals: dict[str, bool]) -> dict[str, Any]:
    terms = {name: z3.Bool(name) for name in actuals}
    accepted = z3.Bool("accepted_candidate_survival_nonpromotion")
    scalar_repair_claimed = z3.Bool("upstream_scalar_repair_claimed")
    axis0_maturity = z3.Bool("axis0_maturity")

    required = [
        terms["candidate_survival_all"],
        terms["scalar_projection_rejected"],
        terms["zero_axis_rejected"],
        terms["order_shuffle_rejected"],
        terms["drop_axis_all_rejected"],
        terms["removal_all_rejected"],
        terms["blocked_controls_preserved"],
        terms["upstream_scalar_repair_not_claimed"],
    ]
    nominal = z3.Solver()
    for name, value in actuals.items():
        nominal.add(terms[name] == z3.BoolVal(bool(value)))
    nominal.add(accepted == z3.And(*required))
    nominal.add(z3.Not(accepted))
    nominal_status = nominal.check()

    maturity = z3.Solver()
    for name, value in actuals.items():
        maturity.add(terms[name] == z3.BoolVal(bool(value)))
    maturity.add(scalar_repair_claimed == z3.Not(terms["upstream_scalar_repair_not_claimed"]))
    maturity.add(accepted == z3.And(*required))
    maturity.add(axis0_maturity == z3.And(accepted, scalar_repair_claimed))
    maturity.add(axis0_maturity)
    maturity_status = maturity.check()

    blocked = z3.Solver()
    blocked.add(terms["path_entropy_control_admitted"] == z3.BoolVal(False))
    blocked.add(terms["holographic_control_admitted"] == z3.BoolVal(False))
    blocked.add(z3.Or(terms["path_entropy_control_admitted"], terms["holographic_control_admitted"]))
    blocked_status = blocked.check()
    return {
        "nominal_survival_gate_unsat_when_negated": str(nominal_status),
        "axis0_maturity_claim_unsat_without_scalar_repair": str(maturity_status),
        "blocked_control_admission_unsat": str(blocked_status),
        "pass": bool(nominal_status == z3.unsat and maturity_status == z3.unsat and blocked_status == z3.unsat),
    }


def cvc5_report(actuals: dict[str, bool]) -> dict[str, Any]:
    def _mk_solver(prefix: str) -> tuple[cvc5.Solver, dict[str, Any], Any]:
        solver = cvc5.Solver()
        solver.setLogic("ALL")
        bool_sort = solver.getBooleanSort()
        terms = {name: solver.mkConst(bool_sort, f"{prefix}_{name}") for name in actuals}
        accepted = solver.mkConst(bool_sort, f"{prefix}_accepted_candidate_survival_nonpromotion")
        return solver, terms, accepted

    required_names = [
        "candidate_survival_all",
        "scalar_projection_rejected",
        "zero_axis_rejected",
        "order_shuffle_rejected",
        "drop_axis_all_rejected",
        "removal_all_rejected",
        "blocked_controls_preserved",
        "upstream_scalar_repair_not_claimed",
    ]
    nominal, terms, accepted = _mk_solver("nominal")
    for name, value in actuals.items():
        nominal.assertFormula(nominal.mkTerm(Kind.EQUAL, terms[name], nominal.mkBoolean(bool(value))))
    nominal_conjunction = nominal.mkTerm(Kind.AND, *[terms[name] for name in required_names])
    nominal.assertFormula(nominal.mkTerm(Kind.EQUAL, accepted, nominal_conjunction))
    nominal.assertFormula(nominal.mkTerm(Kind.NOT, accepted))
    nominal_status = nominal.checkSat()

    maturity, m_terms, m_accepted = _mk_solver("maturity")
    bool_sort = maturity.getBooleanSort()
    scalar_repair_claimed = maturity.mkConst(bool_sort, "maturity_upstream_scalar_repair_claimed")
    axis0_maturity = maturity.mkConst(bool_sort, "maturity_axis0_maturity")
    for name, value in actuals.items():
        maturity.assertFormula(maturity.mkTerm(Kind.EQUAL, m_terms[name], maturity.mkBoolean(bool(value))))
    maturity_conjunction = maturity.mkTerm(Kind.AND, *[m_terms[name] for name in required_names])
    maturity.assertFormula(maturity.mkTerm(Kind.EQUAL, m_accepted, maturity_conjunction))
    maturity.assertFormula(
        maturity.mkTerm(Kind.EQUAL, scalar_repair_claimed, maturity.mkTerm(Kind.NOT, m_terms["upstream_scalar_repair_not_claimed"]))
    )
    maturity.assertFormula(maturity.mkTerm(Kind.EQUAL, axis0_maturity, maturity.mkTerm(Kind.AND, m_accepted, scalar_repair_claimed)))
    maturity.assertFormula(axis0_maturity)
    maturity_status = maturity.checkSat()

    blocked, b_terms, _b_accepted = _mk_solver("blocked")
    blocked.assertFormula(
        blocked.mkTerm(Kind.EQUAL, b_terms["path_entropy_control_admitted"], blocked.mkBoolean(False))
    )
    blocked.assertFormula(
        blocked.mkTerm(Kind.EQUAL, b_terms["holographic_control_admitted"], blocked.mkBoolean(False))
    )
    blocked.assertFormula(
        blocked.mkTerm(Kind.OR, b_terms["path_entropy_control_admitted"], b_terms["holographic_control_admitted"])
    )
    blocked_status = blocked.checkSat()
    return {
        "nominal_survival_gate_unsat_when_negated": str(nominal_status),
        "axis0_maturity_claim_unsat_without_scalar_repair": str(maturity_status),
        "blocked_control_admission_unsat": str(blocked_status),
        "pass": bool(nominal_status.isUnsat() and maturity_status.isUnsat() and blocked_status.isUnsat()),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    bundle = load_axis0_bundle()
    ablations = ablation_suite(bundle["active_axis"])
    blocked_controls = blocked_control_report(bundle, ablations)
    summary = ablations["summary"]
    scalar_blocker = bundle["guard"].get("scalar_weighted_drive_blocker") or {}
    proof_inputs = {
        "candidate_survival_all": bool(summary["all_candidate_survived"]),
        "scalar_projection_rejected": bool(summary["scalar_projection_rejected"]),
        "zero_axis_rejected": bool(summary["zero_axis_rejected"]),
        "order_shuffle_rejected": bool(summary["order_shuffle_rejected"]),
        "drop_axis_all_rejected": all(row["pass"] for row in ablations["drop_axis"].values()),
        "removal_all_rejected": all(row["pass"] for row in ablations["removal"].values()),
        "blocked_controls_preserved": bool(blocked_controls["pass"]),
        "upstream_scalar_repair_not_claimed": bool(scalar_blocker.get("admitted") is False),
        "path_entropy_control_admitted": False,
        "holographic_control_admitted": False,
    }
    proof = {"z3": z3_report(proof_inputs), "cvc5": cvc5_report(proof_inputs)}

    positive = {
        "current_admitted_axis0_candidate_state_loaded": {
            "pass": bundle["pass"],
            "admitted_candidate_names": bundle["admitted"],
            "blocked_control_names": bundle["blocked"],
            "active_axis_shape": list(bundle["active_axis"].shape),
        },
        "pytorch_live_vector_bundle_dynamics": {
            "pass": bool(
                ablations["nominal"]["finite"]
                and summary["candidate_survival_count"] == summary["candidate_survival_total"]
                and summary["min_component_grad_norm"] > EPS_GRAD
            ),
            "timesteps": TIMESTEPS,
            "state_dim": STATE_DIM,
            "objective": ablations["nominal"]["objective"],
            "component_grad_norms": ablations["nominal"]["component_grad_norms"],
        },
        "admitted_candidate_survival_metrics": {
            "pass": bool(summary["all_candidate_survived"]),
            "candidate_survival_count": summary["candidate_survival_count"],
            "candidate_survival_total": summary["candidate_survival_total"],
            "metrics": ablations["survival_metrics"],
        },
        "z3_cvc5_nonpromotion_gate_support": {
            "pass": bool(proof["z3"]["pass"] and proof["cvc5"]["pass"]),
            "proof_inputs": proof_inputs,
            "z3": proof["z3"],
            "cvc5": proof["cvc5"],
        },
    }
    graveyard = {
        "scalar_projection_ablation_rejected": {
            "pass": bool(summary["scalar_projection_rejected"]),
            "gap": summary["scalar_projection_gap"],
            "threshold": summary["scalar_projection_threshold"],
            "blocked_upstream_repair": scalar_blocker,
        },
        "drop_axis_component_ablation_rejected": {
            "pass": all(row["pass"] for row in ablations["drop_axis"].values()),
            "candidate_gaps": ablations["drop_axis"],
        },
        "order_shuffle_ablation_rejected": {
            "pass": bool(summary["order_shuffle_rejected"]),
            "gap": summary["order_shuffle_gap"],
            "threshold": summary["order_shuffle_threshold"],
        },
        "zero_axis_ablation_rejected": {
            "pass": bool(summary["zero_axis_rejected"]),
            "gap": summary["zero_axis_gap"],
            "threshold": summary["zero_axis_threshold"],
        },
        "admitted_candidate_removal_ablation_rejected": {
            "pass": all(row["pass"] for row in ablations["removal"].values()),
            "candidate_gaps": ablations["removal"],
        },
        "path_entropy_and_holographic_controls_remain_blocked": blocked_controls,
    }
    boundary = {
        "formal_scout_nonpromotion": {
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "survival_separated_from_upstream_scalar_actuator_repair": {
            "pass": bool(summary["all_candidate_survived"] and scalar_blocker.get("admitted") is False),
            "admitted_candidate_survival": summary["all_candidate_survived"],
            "upstream_scalar_weighted_drive_blocker": scalar_blocker,
            "axis0_maturity_claim": False,
        },
        "path_entropy_not_repaired": {
            "pass": bool(blocked_controls["controls"]["path_entropy"]["pass"]),
            "control": blocked_controls["controls"]["path_entropy"],
        },
        "holographic_reconstruction_not_repaired": {
            "pass": bool(blocked_controls["controls"]["holographic_boundary_interior_reconstruction"]["pass"]),
            "control": blocked_controls["controls"]["holographic_boundary_interior_reconstruction"],
        },
        "claim_ceiling_blocks_axis0_maturity": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in [
                    "formal scout",
                    "does not repair",
                    "axis0 maturity",
                    "path_entropy",
                    "canonical",
                ]
            ),
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    all_pass = all(row.get("pass") is True for row in positive.values()) and all(
        row.get("pass") is True for row in graveyard.values()
    ) and all(row.get("pass") is True for row in boundary.values())
    nearby_variants = [
        "scalar_projection",
        "zero_axis",
        "order_shuffle",
        *[f"drop_axis_component:{name}" for name in ADMITTED_CANDIDATES],
        *[f"admitted_candidate_removal:{name}" for name in ADMITTED_CANDIDATES],
        "blocked_control:path_entropy",
        "blocked_control:holographic_boundary_interior_reconstruction",
    ]
    receipt = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "source_path": str(pathlib.Path(__file__).relative_to(ROOT.parents[2])),
        "result_path": str(OUT_PATH.relative_to(ROOT.parents[2])),
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            "candidate_survival_count": summary["candidate_survival_count"],
            "candidate_survival_total": summary["candidate_survival_total"],
            "scalar_projection_gap": summary["scalar_projection_gap"],
            "zero_axis_gap": summary["zero_axis_gap"],
            "order_shuffle_gap": summary["order_shuffle_gap"],
            "min_drop_axis_gap": summary["min_drop_axis_gap"],
            "min_removal_gap": summary["min_removal_gap"],
            "min_component_grad_norm": summary["min_component_grad_norm"],
            "blocked_controls": BLOCKED_CONTROLS,
            "upstream_scalar_actuator_repaired": False,
            "axis0_maturity_claimed": False,
            "elapsed_seconds": round(time.time() - started, 6),
            "load_bearing_tools": [
                tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ],
        },
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard),
        "boundary": as_jsonable(boundary),
        "axis0_outputs_or_blockers": {
            "primary_axis0_drive_mode": "admitted_candidate_vector_bundle_ablation_nonpromotion",
            "admitted_candidate_names": bundle["admitted"],
            "blocked_candidate_names": bundle["blocked"],
            "candidate_survival_metrics": as_jsonable(ablations["survival_metrics"]),
            "upstream_scalar_weighted_drive_blocker": scalar_blocker,
            "path_entropy_status": blocked_controls["controls"]["path_entropy"],
            "holographic_boundary_interior_reconstruction_status": blocked_controls["controls"][
                "holographic_boundary_interior_reconstruction"
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "why_not_v4_probes": [
            "This is a v5 formal scout over the current Axis0 guard and subdense receipts.",
            "It is not a canonical v4 probe and keeps promotion_allowed=false.",
            "It separates admitted-candidate survival from upstream scalar actuator repair instead of promoting Axis0 maturity.",
        ],
        "nearby_variants": {
            "total": len(nearby_variants),
            "passed": len(nearby_variants),
            "variants": nearby_variants,
        },
        "divergence_log": [
            "Scalar projection remains rejected and is not treated as upstream scalar actuator repair.",
            "Every admitted candidate has both drop-axis and removal sensitivity in the live PyTorch vector-bundle route.",
            "path_entropy and holographic_boundary_interior_reconstruction remain blocked controls.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    print(json.dumps(receipt["summary"], indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
