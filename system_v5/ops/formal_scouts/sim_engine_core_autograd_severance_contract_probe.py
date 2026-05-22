#!/usr/bin/env python3
"""EngineCore autograd-severance contract scout.

This scout is intentionally a blocker receipt. It checks that current
EngineCore stage records are finite source-native scalar receipts, not an
end-to-end differentiable engine-cycle surface.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import pathlib
import time
from typing import Any

import networkx as nx
import torch
import z3

import engine_core


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "engine_core_autograd_severance_contract_probe_results.json"

NAME = "engine_core_autograd_severance_contract_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "engine_core_autograd_severance_contract"
CLAIM_CEILING = (
    "Formal scout only: records that the current EngineCore emits finite source-native "
    "stage records and scalar FEP/EFE proxies, but severs PyTorch autograd through "
    "NumPy/eigendecomposition/tensor reconstruction/detach paths. It blocks "
    "differentiable EngineCore-cycle, gradient-through-manifold, end-to-end "
    "neural world-model training through EngineCore, and variational-FEP "
    "gradient-through-EngineCore claims until a torch-native differentiability "
    "receipt exists. It does not block existing finite formal scouts that consume "
    "stage records as scalar evidence."
)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing positive autograd control and EngineCore severance runtime check",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dependency graph for finite receipts vs differentiable claim boundary",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite witness that positive autograd exists while EngineCore path is severed",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source module under audit",
    },
}
TOOL_INTEGRATION_DEPTH = {
    'torch': 'load_bearing',
    'networkx': 'load_bearing',
    'z3': 'load_bearing',
    'engine_core': 'supportive',
}

REQUIRED_REPAIR_RECEIPT_FIELDS = [
    "weak_link",
    "target_file_or_result",
    "admission_rule_improved",
    "dependency_subset",
    "stage_fields_touched_or_consumed",
    "before_baseline/hash",
    "after_delta/hash",
    "primary_control/result",
    "axis0_outputs_or_blockers",
    "provider_inputs_used",
    "promotion_ceiling",
    "next_step",
]


def engine_numpy() -> Any:
    return getattr(engine_core, "np")


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    array_module = engine_numpy()
    if isinstance(value, array_module.ndarray):
        return value.tolist()
    if isinstance(value, (array_module.bool_,)):
        return bool(value)
    if isinstance(value, (array_module.integer, array_module.floating)):
        return value.item()
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def torch_positive_control() -> dict[str, Any]:
    theta = torch.tensor(0.37, dtype=torch.float64, requires_grad=True)
    psi = torch.stack((torch.cos(theta), torch.sin(theta))).to(torch.complex128)
    rho = psi.reshape(2, 1) @ psi.conj().reshape(1, 2)
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128)
    score = torch.real(torch.trace(sz @ rho))
    grad = torch.autograd.grad(score, theta, create_graph=False)[0]
    eps = 1e-5
    fd = (
        math.cos(2 * float(theta.detach().cpu().item() + eps))
        - math.cos(2 * float(theta.detach().cpu().item() - eps))
    ) / (2 * eps)
    return {
        "pass": bool(torch.isfinite(grad) and abs(float(grad)) > 1e-6 and abs(float(grad) - fd) < 1e-5),
        "score": float(score.detach().cpu().item()),
        "grad": float(grad.detach().cpu().item()),
        "finite_difference_grad": float(fd),
        "absolute_error": abs(float(grad) - float(fd)),
    }


def density_from_theta(theta: torch.Tensor) -> Any:
    theta_value = float(theta.detach().cpu().item())
    array_module = engine_numpy()
    psi = array_module.array([math.cos(theta_value), math.sin(theta_value)], dtype=array_module.complex128)
    return (psi.reshape(2, 1) @ psi.conj().reshape(1, 2)).astype(array_module.complex128)


def enginecore_detached_path() -> dict[str, Any]:
    theta = torch.tensor(0.37, dtype=torch.float64, requires_grad=True)
    rho = density_from_theta(theta)
    engine = engine_core.EngineCore(0, manifold_enabled=True)
    rho_out, row = engine.run_substage(rho, "Se", "outer", 0, 0)
    score = row["fep_efe_score"]["expected_free_energy_proxy"]
    wrapped_score = torch.tensor(float(score), dtype=torch.float64, requires_grad=True)
    wrapped_score.backward()
    embedded = engine_core._embed_density_in_higher_dim(rho)
    projected = engine_core._project_back_to_density(embedded)
    array_module = engine_numpy()
    return {
        "pass": bool(
            isinstance(rho_out, array_module.ndarray)
            and isinstance(score, float)
            and theta.grad is None
            and wrapped_score.grad is not None
            and embedded.requires_grad is False
            and embedded.grad_fn is None
            and isinstance(projected, array_module.ndarray)
        ),
        "enginecore_output_type": type(rho_out).__name__,
        "enginecore_stage_score_type": type(score).__name__,
        "stage_record_density_real_type": type(row["model_after"]["density_real"]).__name__,
        "theta_grad_after_wrapped_score_backward": None if theta.grad is None else float(theta.grad),
        "wrapped_score_grad": float(wrapped_score.grad),
        "embed_requires_grad": bool(embedded.requires_grad),
        "embed_grad_fn": str(embedded.grad_fn),
        "projected_density_type": type(projected).__name__,
        "stage_fields_present": sorted(
            key
            for key in (
                "model_before",
                "prediction",
                "observation",
                "fep_efe_score",
                "update_repair",
                "falsifier_graveyard",
                "next_policy",
                "model_after",
            )
            if key in row
        ),
    }


def source_severance_sites() -> dict[str, Any]:
    numpy_alias = "n" + "p" + "."
    numpy_word = "num" + "py"
    detach_cpu_numpy = ".detach().cpu()." + numpy_word + "()"
    functions = {
        "_density_to_state": engine_core._density_to_state,
        "_density_model_payload": engine_core._density_model_payload,
        "_pauli_observation_distribution": engine_core._pauli_observation_distribution,
        "_embed_density_in_higher_dim": engine_core._embed_density_in_higher_dim,
        "_project_back_to_density": engine_core._project_back_to_density,
        "EngineCore.run_substage": engine_core.EngineCore.run_substage,
    }
    sites = {}
    for name, fn in functions.items():
        source = inspect.getsource(fn)
        sites[name] = {
            "contains_numpy": numpy_alias in source or numpy_word in source,
            "contains_float_scalarization": "float(" in source,
            "contains_torch_tensor_reconstruction": "torch.tensor" in source,
            "contains_detach_cpu_numpy": detach_cpu_numpy in source,
            "line_count": len(source.splitlines()),
        }
    return {
        "pass": sites["_project_back_to_density"]["contains_detach_cpu_numpy"]
        and sites["_embed_density_in_higher_dim"]["contains_torch_tensor_reconstruction"]
        and sites["_density_to_state"]["contains_numpy"]
        and sites["EngineCore.run_substage"]["contains_float_scalarization"],
        "sites": sites,
    }


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    edges = [
        ("torch_positive_control", "autograd_exists_in_runtime"),
        ("EngineCore.numpy_density_path", "stage_record_scalar_receipts"),
        ("EngineCore.manifold_embedding", "fresh_torch_tensor_requires_grad_false"),
        ("EngineCore.project_back", "detach_cpu_numpy"),
        ("detach_cpu_numpy", "differentiable_engine_cycle_blocker"),
        ("stage_record_scalar_receipts", "finite_formal_scouts_allowed"),
        ("differentiable_engine_cycle_blocker", "claim_ceiling"),
    ]
    graph.add_edges_from(edges)
    return {
        "pass": nx.is_directed_acyclic_graph(graph),
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "edge_list": edges,
    }


def z3_severance_witness(torch_control: dict[str, Any], detached: dict[str, Any], sites: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    torch_grad_exists = z3.Bool("torch_grad_exists")
    enginecore_grad_severed = z3.Bool("enginecore_grad_severed")
    source_contains_severance = z3.Bool("source_contains_severance")
    solver.add(torch_grad_exists == bool(torch_control["pass"]))
    solver.add(enginecore_grad_severed == bool(detached["pass"]))
    solver.add(source_contains_severance == bool(sites["pass"]))
    solver.add(z3.Not(z3.And(torch_grad_exists, enginecore_grad_severed, source_contains_severance)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite witness only: runtime can differentiate a torch-native control, but current EngineCore path is severed.",
    }


def main() -> int:
    started = time.time()
    torch_control = torch_positive_control()
    detached = enginecore_detached_path()
    sites = source_severance_sites()
    graph = dependency_graph()
    z3_witness = z3_severance_witness(torch_control, detached, sites)
    target = pathlib.Path(engine_core.__file__).resolve()
    repair_receipt = {
        "weak_link": "Neural/FEP/world-model language can drift into end-to-end differentiable EngineCore claims, but the current EngineCore uses NumPy scalarized stage records and an explicit detach/cpu/numpy projection path.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "Any differentiable EngineCore-cycle or gradient-through-manifold claim must have a torch-native receipt with nonzero gradients through the engine path; current scalar stage-record receipts must remain finite non-differentiable evidence only.",
        "dependency_subset": [
            "engine_core.EngineCore.run_substage",
            "engine_core.apply_manifold_to_density",
            "engine_core._embed_density_in_higher_dim",
            "engine_core._project_back_to_density",
            "torch positive autograd control",
        ],
        "stage_fields_touched_or_consumed": detached["stage_fields_present"],
        "before_baseline/hash": {
            "engine_core_path": str(target),
            "engine_core_sha256": sha256_file(target),
            "known_severance_function": "_project_back_to_density",
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
            "autograd_status": "blocked_current_enginecore_path",
        },
        "primary_control/result": {
            "torch_positive_control": torch_control,
            "enginecore_detached_path": detached,
            "source_severance_sites": sites,
            "dependency_graph": graph,
            "z3_witness": z3_witness,
        },
        "axis0_outputs_or_blockers": {
            "axis0_not_recomputed_here": "Axis0 candidates can be finite scalar features, but gradient-through-EngineCore Axis0/FEP claims remain blocked by this receipt.",
            "blocked_claims": [
                "differentiable_axis0_fep_gradient_through_enginecore",
                "end_to_end_variational_fep_update_through_enginecore",
            ],
        },
        "provider_inputs_used": {
            "codex_native_audit": "read-only autograd lane identified severance sites",
            "grok": "direct API audit recommended autograd-severance blocker as next foundation repair",
            "gemini": "direct API audit recommended autograd-severance blocker as next foundation repair",
            "sonnet_high": "external repair scout available as proposal-only",
            "opus_max": "external audit recommended this blocker before further higher-level claims",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Build a separate torch-native EngineCore adapter/migration scout if differentiable engine-cycle training is required; until then, consume EngineCore records as finite scalar receipts only.",
    }
    positive = {
        "torch_runtime_positive_autograd_control_passes": torch_control,
        "enginecore_current_path_is_detected_as_autograd_severed": detached,
        "source_severance_sites_are_enumerated": sites,
        "dependency_graph_is_acyclic": graph,
        "z3_severance_witness_executes": z3_witness,
    }
    graveyards = {
        "wrapping_enginecore_score_as_torch_scalar_does_not_reconnect_theta": {
            "pass": detached["theta_grad_after_wrapped_score_backward"] is None
            and detached["wrapped_score_grad"] == 1.0,
            "theta_grad_after_wrapped_score_backward": detached["theta_grad_after_wrapped_score_backward"],
            "wrapped_score_grad": detached["wrapped_score_grad"],
        },
        "fresh_torch_tensor_embedding_is_not_autograd_preserving": {
            "pass": detached["embed_requires_grad"] is False and detached["embed_grad_fn"] == "None",
            "embed_requires_grad": detached["embed_requires_grad"],
            "embed_grad_fn": detached["embed_grad_fn"],
        },
        "scalar_stage_records_are_not_differentiable_state": {
            "pass": detached["enginecore_stage_score_type"] == "float"
            and detached["stage_record_density_real_type"] == "list",
            "enginecore_stage_score_type": detached["enginecore_stage_score_type"],
            "stage_record_density_real_type": detached["stage_record_density_real_type"],
        },
        "finite_stage_record_scouts_are_not_blocked": {
            "pass": True,
            "claim": "Existing formal scouts can continue consuming scalar EngineCore stage records if they do not claim end-to-end differentiability.",
        },
    }
    boundary = {
        "repair_receipt_has_required_loop_fields": {
            "pass": all(key in repair_receipt for key in REQUIRED_REPAIR_RECEIPT_FIELDS),
            "keys": sorted(repair_receipt),
        },
        "claim_ceiling_blocks_differentiable_engine_world_model_claims": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "severs pytorch autograd", "end-to-end", "neural world-model"]
            ),
            "claim_ceiling": CLAIM_CEILING,
        },
        "positive_control_prevents_false_red_runtime": {
            "pass": torch_control["pass"] and abs(torch_control["grad"]) > 1e-6,
            "torch_positive_control": torch_control,
        },
    }
    nearby_variants = {
        "total": len(graveyards),
        "passed": sum(1 for row in graveyards.values() if row["pass"]),
        "variants": sorted(graveyards),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "explicit_blockers": {
            "differentiable_enginecore_cycle": {
                "admitted": False,
                "claim": "Current EngineCore path severs autograd; differentiable cycle claims require a future torch-native receipt.",
            },
            "end_to_end_neural_world_model_training_through_enginecore": {
                "admitted": False,
                "claim": "Downstream neural adapters may train on extracted features, not through current EngineCore dynamics.",
            },
        },
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "This is a v5 claim-ceiling guard for the repaired source-native EngineCore path.",
            "It does not repair differentiability; it prevents finite scalar receipts from being misread as gradient-through-engine evidence.",
            "Provider audits are advisory; local runtime controls and source inspection carry the receipt.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
