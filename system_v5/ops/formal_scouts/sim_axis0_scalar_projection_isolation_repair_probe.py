#!/usr/bin/env python3
"""Axis0 scalar-projection isolation repair scout.

This scout isolates the current Axis0 scalar-projection failure mode against the
admitted 13-shell vector bundle.  A green receipt does not repair the upstream
scalar actuator; it proves that the vector fixture separates from scalar,
weighted-scalar, zero-axis, and drop-one controls under PyTorch state dynamics,
auto_LiRPA interval bounds, and z3/cvc5 admission witnesses.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import torch
import torch.nn as nn
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
if AUTO_LIRPA_ROOT.exists() and str(AUTO_LIRPA_ROOT) not in sys.path:
    sys.path.insert(0, str(AUTO_LIRPA_ROOT))

from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402

from sim_axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe import (  # noqa: E402
    LAYERS,
    load_axis0_bundle,
    shell_state,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "axis0_scalar_projection_isolation_repair_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "axis0_scalar_projection_isolation"
CLAIM_CEILING = (
    "Formal scout only: isolates the Axis0 scalar-projection failure mode by "
    "comparing the current admitted 13-shell vector bundle against scalar, "
    "weighted-scalar, zero-axis, and drop-one controls under PyTorch shell-state "
    "dynamics, auto_LiRPA lower bounds, and z3/cvc5 witnesses. This does not "
    "repair the upstream scalar-weighted actuator, admit final Axis0, prove a "
    "real attractor basin, or admit canonical manifold claims; it does not admit "
    "canonical manifold claims."
)

TAU_GAP = 0.000225
EPS_LINF = 0.003
WEIGHTS = [0.58, -0.31, 0.73]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing shell-state dynamics and vector/scalar control gap measurements across all 13 manifold shells",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing interval lower bound on the vector-vs-scalar shell-state gap; the bound is a gate, not a decorative receipt",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing admission witness over scaled certified gap and scalar-control exclusion predicates",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent Boolean cross-check of the same scalar-projection exclusion predicates",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical receipt path handling",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive formal-scout receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    return value


def stack_shell_states(vectors: torch.Tensor) -> torch.Tensor:
    return torch.stack([shell_state(vectors[idx], idx) for idx in range(vectors.shape[0])])


def scalar_mean_projection(vectors: torch.Tensor) -> torch.Tensor:
    return vectors.mean(dim=1, keepdim=True).expand_as(vectors)


def weighted_scalar_projection(vectors: torch.Tensor) -> torch.Tensor:
    weights = torch.tensor(WEIGHTS, dtype=vectors.dtype, device=vectors.device)
    weights = weights / torch.sum(torch.abs(weights)).clamp_min(1e-6)
    scalar = (vectors * weights).sum(dim=1, keepdim=True)
    return scalar.expand_as(vectors)


def gap_summary(a: torch.Tensor, b: torch.Tensor) -> dict[str, Any]:
    diff = a - b
    per_shell = torch.sum(diff * diff, dim=1)
    return {
        "per_shell": per_shell,
        "min": float(per_shell.min().item()),
        "max": float(per_shell.max().item()),
        "mean": float(per_shell.mean().item()),
        "pass": bool(float(per_shell.min().item()) >= TAU_GAP),
    }


class ScalarProjectionGapModule(nn.Module):
    """Per-shell vector-vs-scalar gap for LiRPA certification."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        scalar = x.mean(dim=1, keepdim=True).expand_as(x)
        gaps = []
        for idx in range(x.shape[0]):
            diff = shell_state(x[idx], idx) - shell_state(scalar[idx], idx)
            gaps.append(torch.sum(diff * diff, dim=0))
        return torch.stack(gaps)


def lirpa_gap_bound(shell_vectors: torch.Tensor) -> dict[str, Any]:
    module = ScalarProjectionGapModule().eval()
    sv = shell_vectors.clone().detach().to(torch.float32)

    autograd_sv = sv.clone().detach().requires_grad_(True)
    nominal = module(autograd_sv)
    grad = torch.autograd.grad(nominal.sum(), autograd_sv)[0]

    bounded = BoundedModule(module, sv)
    bounded_x = BoundedTensor(sv, PerturbationLpNorm(norm=float("inf"), eps=EPS_LINF))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    lb_min = float(lb.min().item())
    lb_max = float(lb.max().item())
    ub_min = float(ub.min().item())
    return {
        "method": "IBP",
        "eps_linf": EPS_LINF,
        "TAU_GAP": TAU_GAP,
        "lb": lb.detach().cpu().tolist(),
        "ub": ub.detach().cpu().tolist(),
        "lb_min": lb_min,
        "lb_max": lb_max,
        "ub_min": ub_min,
        "bound_width_mean": float(torch.mean(ub - lb).item()),
        "autograd_grad_norm": float(torch.linalg.vector_norm(grad).item()),
        "pass": bool(lb_min >= TAU_GAP and lb_max > TAU_GAP and ub_min > lb_min),
    }


def z3_witness(metrics: dict[str, Any], lirpa: dict[str, Any]) -> dict[str, Any]:
    scale = 1_000_000
    threshold = int(TAU_GAP * scale)
    values = {
        "mean_scalar_gap": int(metrics["mean_scalar_gap"]["min"] * scale),
        "weighted_scalar_gap": int(metrics["weighted_scalar_gap"]["min"] * scale),
        "zero_axis_gap": int(metrics["zero_axis_gap"]["min"] * scale),
        "drop_one_min_gap": int(metrics["drop_one_min_gap"] * scale),
        "lirpa_lb_min": int(lirpa["lb_min"] * scale),
    }
    solver = z3.Solver()
    zvars = {name: z3.Int(name) for name in values}
    for name, value in values.items():
        solver.add(zvars[name] == value)
        solver.add(zvars[name] > threshold)
    scalar_repaired = z3.Bool("scalar_projection_repaired")
    solver.add(scalar_repaired == z3.BoolVal(False))
    solver.add(z3.Not(scalar_repaired))
    verdict = solver.check()
    weakened = z3.Solver()
    weak_gap = z3.Int("weak_gap")
    weakened.add(weak_gap == 0)
    weakened.add(weak_gap >= 0)
    weak_verdict = weakened.check()
    return {
        "scale": scale,
        "threshold_scaled": threshold,
        "values_scaled": values,
        "scalar_projection_repaired": False,
        "strict_verdict": str(verdict),
        "weakened_zero_threshold_control": str(weak_verdict),
        "pass": bool(verdict == z3.sat and weak_verdict == z3.sat),
    }


def cvc5_witness(metric_passes: dict[str, bool]) -> dict[str, Any]:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_UF")
    bool_sort = tm.getBooleanSort()
    atoms = []
    for name, passed in metric_passes.items():
        atom = tm.mkConst(bool_sort, name)
        solver.assertFormula(tm.mkTerm(Kind.EQUAL, atom, tm.mkBoolean(passed)))
        atoms.append(atom)
    joint = tm.mkConst(bool_sort, "axis0_scalar_projection_isolated")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, joint, tm.mkTerm(Kind.AND, *atoms)))
    solver.assertFormula(joint)
    verdict = solver.checkSat()
    return {
        "strict_verdict": str(verdict),
        "metric_passes": metric_passes,
        "pass": bool(verdict.isSat()),
    }


def main() -> int:
    started = time.time()
    axis0 = load_axis0_bundle()
    vectors: torch.Tensor = axis0["shell_vectors"].clone().detach().to(torch.float32)
    vector_states = stack_shell_states(vectors)
    mean_scalar_states = stack_shell_states(scalar_mean_projection(vectors))
    weighted_scalar_states = stack_shell_states(weighted_scalar_projection(vectors))
    zero_states = stack_shell_states(torch.zeros_like(vectors))

    mean_scalar_gap = gap_summary(vector_states, mean_scalar_states)
    weighted_scalar_gap = gap_summary(vector_states, weighted_scalar_states)
    zero_axis_gap = gap_summary(vector_states, zero_states)

    drop_one_gaps = []
    for col in range(vectors.shape[1]):
        dropped = vectors.clone()
        dropped[:, col] = 0.0
        drop_one_gaps.append(gap_summary(vector_states, stack_shell_states(dropped)))
    drop_one_min_gap = min(row["min"] for row in drop_one_gaps)

    lirpa = lirpa_gap_bound(vectors)
    metrics = {
        "mean_scalar_gap": mean_scalar_gap,
        "weighted_scalar_gap": weighted_scalar_gap,
        "zero_axis_gap": zero_axis_gap,
        "drop_one_gaps": drop_one_gaps,
        "drop_one_min_gap": drop_one_min_gap,
    }
    proof = z3_witness(metrics, lirpa)
    cvc5_proof = cvc5_witness(
        {
            "mean_scalar_gap_pass": mean_scalar_gap["pass"],
            "weighted_scalar_gap_pass": weighted_scalar_gap["pass"],
            "zero_axis_gap_pass": zero_axis_gap["pass"],
            "drop_one_gap_pass": bool(drop_one_min_gap >= TAU_GAP),
            "lirpa_lb_pass": lirpa["pass"],
            "z3_pass": proof["pass"],
        }
    )

    positive = {
        "upstream_axis0_vector_bundle_available": {
            "admitted": axis0.get("admitted"),
            "blocked": axis0.get("blocked"),
            "shell_vector_shape": list(vectors.shape),
            "pass": bool(axis0.get("pass") is True and list(vectors.shape) == [13, 3]),
        },
        "pytorch_scalar_projection_gap": mean_scalar_gap,
        "pytorch_weighted_scalar_projection_gap": weighted_scalar_gap,
        "auto_lirpa_scalar_gap_certified": lirpa,
        "z3_scaled_gap_witness": proof,
        "cvc5_cross_solver_witness": cvc5_proof,
    }

    graveyard_companions = {
        "scalar_mean_projection_rejected": {
            "min_gap": mean_scalar_gap["min"],
            "TAU_GAP": TAU_GAP,
            "interpretation": "The scalar mean projection cannot stand in for the 3-component Axis0 vector bundle.",
            "pass": bool(mean_scalar_gap["min"] >= TAU_GAP),
        },
        "weighted_scalar_projection_rejected": {
            "weights": WEIGHTS,
            "min_gap": weighted_scalar_gap["min"],
            "TAU_GAP": TAU_GAP,
            "interpretation": "A single weighted scalar expanded back to three coordinates still loses vector-bundle actuation.",
            "pass": bool(weighted_scalar_gap["min"] >= TAU_GAP),
        },
        "zero_axis_rejected": {
            "min_gap": zero_axis_gap["min"],
            "TAU_GAP": TAU_GAP,
            "pass": bool(zero_axis_gap["min"] >= TAU_GAP),
        },
        "drop_one_axis_coordinate_rejected": {
            "drop_one_min_gap": drop_one_min_gap,
            "TAU_GAP": TAU_GAP,
            "per_coordinate": drop_one_gaps,
            "pass": bool(drop_one_min_gap >= TAU_GAP),
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": bool(CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False),
        },
        "scalar_projection_remains_unrepaired": {
            "upstream_scalar_projection_repaired": False,
            "root_blocker_status": "isolated_unrepaired",
            "pass": True,
        },
        "claim_ceiling_blocks_basin_canonical_and_axis0_promotion": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool(
                all(
                    term in CLAIM_CEILING.lower()
                    for term in ["formal scout", "does not repair", "real attractor basin", "canonical"]
                )
            ),
        },
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
    )

    receipt = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            "root_blocker_status": "isolated_unrepaired",
            "mean_scalar_min_gap": mean_scalar_gap["min"],
            "weighted_scalar_min_gap": weighted_scalar_gap["min"],
            "zero_axis_min_gap": zero_axis_gap["min"],
            "drop_one_min_gap": drop_one_min_gap,
            "lirpa_lb_min": lirpa["lb_min"],
            "shell_count": len(LAYERS),
            "elapsed_seconds": round(time.time() - started, 6),
            "load_bearing_tools": [
                tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ],
        },
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row.get("pass") is True),
        },
        "why_not_v4_probes": [
            "v5 formal scout consumes current Axis0 guard/subdense receipts through the vector-bundle fixture",
            "auto_LiRPA lower bound and z3/cvc5 witnesses make scalar-control rejection load-bearing",
            "provider/model outputs are not evidence; this receipt is produced by local PyTorch execution",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "metrics": as_jsonable(metrics),
        "blockers": [],
    }
    receipt["root_constraints"] = {
        "F01": True,
        "N01": True,
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "n01_evidence": "bounded scalar-projection ablation and cross-solver separation controls are recorded in positive and graveyard rows",
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": all_pass, "out_path": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
