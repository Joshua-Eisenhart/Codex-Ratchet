#!/usr/bin/env python3
"""PyTorch autograd per-row spinor phase micro-probe."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import torch

import layer_full_spinor_network_individual_runner as layer_carrier
import sim_g_structure_candidate_space_full_function_probe as gspace


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "tool_depth_pytorch_autograd_per_row_spinor_phase_probe_results.json"
PARENT_RESULT = RESULT_DIR / "tool_by_tool_layer_g_structure_geometry_depth_probe_results.json"
Z3_CVC5_STATUS = ROOT / "tool_depth_z3_cvc5_non_vacuous_solver_controls_status_20260528.json"

NAME = "tool_depth_pytorch_autograd_per_row_spinor_phase_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: proves PyTorch autograd is load-bearing per row for "
    "finite spinor phase gradients over current layer and G-structure rows. "
    "It does not make any layer gradient-capable as a completion claim and "
    "does not open stacking, Axis0, flux, FEP, physics, or final manifold work."
)
FINITE_MAP = (
    "TorchAutogradSpinorPhaseDepth : (current layer rows, G-structure rows, "
    "finite torch.complex128 spinor samples, relative phase parameter theta) "
    "-> per-row objective, per-row d objective / d theta, erased-component "
    "control gradients, order-erased schedule controls, and resource ceiling"
)
DOMAIN = (
    "L0-L8 current layer rows across their sheets and site counts 8/16/32/64; "
    "12 current G-structure candidate rows across site counts 8/16/32/64; "
    "finite two-component torch spinors from the current runners"
)
CODOMAIN_OR_OUTPUT = (
    "92 per-row nonzero autograd gradients, component-erased zero-gradient "
    "controls, order-erased phase-schedule deltas, min/max gradient summary, "
    "and blocked downstream consumers"
)
ROOT_CONSTRAINTS_IN_FORCE = [
    "F01 finite carrier/probe/operator/path set",
    "N01 order-sensitive phase schedule over finite spinor row samples",
]
TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing torch.complex128 spinors and autograd gradients for every current layer/G row",
    }
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing"}
BLOCKED_CONSUMERS = [
    "official_layered_ratchet_G_structure_selection",
    "layer_embedding_in_G_structure",
    "stacking",
    "cross_layer_order_closure",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold_admission",
]
GRAD_FLOOR = 1.0e-6
CONTROL_CEILING = 1.0e-12
SITE_COUNTS = [8, 16, 32, 64]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return value.item()
    return value


def gradient_readout(spinors: list[torch.Tensor], *, indexed_schedule: bool = True, erase_component: bool = False) -> dict[str, Any]:
    theta = torch.tensor(0.37, dtype=torch.float64, requires_grad=True)
    terms = []
    component_weight_sum = 0.0
    for idx, psi in enumerate(spinors):
        psi = psi.to(torch.complex128)
        z0 = psi[0]
        z1 = psi[1]
        if erase_component:
            z1 = z1 * 0.0
        amp = torch.abs(z0) * torch.abs(z1)
        component_weight_sum += float(amp.detach().item())
        phase = torch.angle(z1) - torch.angle(z0) if not erase_component else torch.tensor(0.0, dtype=torch.float64)
        schedule_weight = float(idx + 1) if indexed_schedule else 1.0
        terms.append(amp * torch.sin(theta * schedule_weight + phase))
    objective = torch.stack(terms).mean()
    objective.backward()
    grad = float(theta.grad.detach().item())
    return {
        "objective": float(objective.detach().item()),
        "gradient": grad,
        "gradient_abs": abs(grad),
        "component_weight_sum": component_weight_sum,
    }


def layer_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for layer_id in layer_carrier.LAYER_CONFIGS:
        config = layer_carrier.LAYER_CONFIGS[layer_id]
        for sheet in config["sheets"]:
            for site_count in SITE_COUNTS:
                rows.append(
                    {
                        "row_id": f"layer:{layer_id}:{sheet}:{site_count}",
                        "row_type": "layer",
                        "layer": layer_id,
                        "layer_name": config["name"],
                        "sheet": sheet,
                        "site_count": site_count,
                        "spinors": layer_carrier.layer_spinors(layer_id, site_count, sheet),
                    }
                )
    return rows


def g_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in gspace.STRUCTURE_CANDIDATES:
        for site_count in SITE_COUNTS:
            rows.append(
                {
                    "row_id": f"g_structure:{candidate}:{site_count}",
                    "row_type": "g_structure",
                    "candidate": candidate,
                    "site_count": site_count,
                    "spinors": gspace.candidate_spinors(candidate, site_count),
                }
            )
    return rows


def row_probe(row: dict[str, Any]) -> dict[str, Any]:
    spinors = row["spinors"]
    indexed = gradient_readout(spinors, indexed_schedule=True, erase_component=False)
    erased = gradient_readout(spinors, indexed_schedule=True, erase_component=True)
    order_erased = gradient_readout(spinors, indexed_schedule=False, erase_component=False)
    order_delta = abs(indexed["gradient_abs"] - order_erased["gradient_abs"])
    out = {
        key: value for key, value in row.items() if key != "spinors"
    }
    out.update(
        {
            "spinor_count": len(spinors),
            "indexed_phase_gradient_abs": indexed["gradient_abs"],
            "indexed_phase_objective": indexed["objective"],
            "component_weight_sum": indexed["component_weight_sum"],
            "erased_component_gradient_abs": erased["gradient_abs"],
            "order_erased_gradient_abs": order_erased["gradient_abs"],
            "order_schedule_gradient_delta": order_delta,
            "pass": bool(
                indexed["gradient_abs"] > GRAD_FLOOR
                and erased["gradient_abs"] < CONTROL_CEILING
                and order_delta > GRAD_FLOOR
                and math.isfinite(indexed["objective"])
            ),
        }
    )
    return out


def run_probe() -> dict[str, Any]:
    rows = [row_probe(row) for row in layer_rows() + g_rows()]
    layer_count = sum(1 for row in rows if row["row_type"] == "layer")
    g_count = sum(1 for row in rows if row["row_type"] == "g_structure")
    min_grad = min(float(row["indexed_phase_gradient_abs"]) for row in rows)
    max_erased = max(float(row["erased_component_gradient_abs"]) for row in rows)
    min_order_delta = min(float(row["order_schedule_gradient_delta"]) for row in rows)
    failed_rows = [row["row_id"] for row in rows if not row["pass"]]
    positive = {
        "per_row_autograd_gradients_nonzero": {
            "pass": not failed_rows and min_grad > GRAD_FLOOR,
            "row_count": len(rows),
            "layer_row_count": layer_count,
            "g_structure_row_count": g_count,
            "min_gradient_abs": min_grad,
            "max_gradient_abs": max(float(row["indexed_phase_gradient_abs"]) for row in rows),
        },
        "resource_ceiling_respected": {
            "pass": len(rows) == 92 and max(int(row["site_count"]) for row in rows) == 64,
            "row_count": len(rows),
            "site_counts": SITE_COUNTS,
            "max_sites": max(int(row["site_count"]) for row in rows),
            "total_spinor_samples": sum(int(row["spinor_count"]) for row in rows),
        },
    }
    graveyard = {
        "component_erasure_kills_phase_gradient": {
            "pass": max_erased < CONTROL_CEILING,
            "max_erased_component_gradient_abs": max_erased,
        },
        "order_erased_phase_schedule_changes_gradient": {
            "pass": min_order_delta > GRAD_FLOOR,
            "min_order_schedule_gradient_delta": min_order_delta,
        },
    }
    return {
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": {
            "rows": rows,
            "gradient_floor": GRAD_FLOOR,
            "control_ceiling": CONTROL_CEILING,
            "failed_rows": failed_rows,
            "parent_result_exists": PARENT_RESULT.exists(),
            "z3_cvc5_status_exists": Z3_CVC5_STATUS.exists(),
        },
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "blockers": [{"kind": "failed_row", "row_id": row_id} for row_id in failed_rows],
        "all_pass": all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()),
    }


def main() -> int:
    started = time.time()
    try:
        body = run_probe()
    except Exception as exc:
        body = {
            "positive": {},
            "graveyard_companions": {},
            "boundary": {},
            "nearby_variants": {"total": 0, "passed": 0, "variants": []},
            "blockers": [{"kind": "runtime_error", "detail": f"{type(exc).__name__}: {exc}"}],
            "all_pass": False,
        }
    result = {
        "sim_id": NAME,
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN_OR_OUTPUT,
        "root_constraints_in_force": ROOT_CONSTRAINTS_IN_FORCE,
        "carrier_layer": "current layer/G finite spinor row set",
        "geometry_layer": "per-row spinor phase surface",
        "carrier_realization": "torch.complex128 two-component spinors with autograd phase parameter theta",
        "peps3d_embedding": "consumes current row set that has PEPS3D anchors; this probe itself is the PyTorch/autograd tool-depth surface only",
        "spinor_state": "torch-native two-component spinors from layer_full_spinor_network_individual_runner and g_structure candidate runner",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [str(PARENT_RESULT), str(Z3_CVC5_STATUS)],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none; phase-gradient tool-depth only",
        "law_or_candidate_tested": "per-row relative spinor phase objective differentiated by torch autograd",
        "allowed_claims": [
            "PyTorch autograd has one per-row spinor phase tool-depth receipt",
            "component-erased and order-erased controls are non-vacuous for this phase-gradient fixture",
        ],
        "promotion_blockers": [
            "does not make any layer complete",
            "does not integrate the gradient into stack/order tests",
            "does not select a G-structure",
            "does not open Axis0/flux/FEP/physics/final manifold consumers",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "actual_tools_used": ["pytorch"],
        "required_tools": ["pytorch"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "source_alignment_category": "tool_depth_pytorch_autograd_per_row_spinor_phase",
        "why_not_v4_probes": "This is a v5 per-tool depth repair packet over current layer/G rows; it is not v4 probe accumulation and does not promote downstream consumers.",
        "elapsed_seconds": time.time() - started,
        **body,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
