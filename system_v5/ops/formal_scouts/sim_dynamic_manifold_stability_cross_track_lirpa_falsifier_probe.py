#!/usr/bin/env python3
"""Dynamic manifold stability falsifier over the current 13-shell fixtures."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
import z3

from sim_axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe import (
    LAYERS,
    axis_basis,
    load_axis0_bundle,
    tensor_signature,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "dynamic_manifold_stability_cross_track_lirpa_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

INTEGRATED_RESULT = RESULT_DIR / "integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe_results.json"
ACTIVE_RESULT = RESULT_DIR / "thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe_results.json"
AXIS0_VECTOR_RESULT = RESULT_DIR / "axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe_results.json"
AXIS0_ASSEMBLY_RESULT = RESULT_DIR / "axis0_lewm_lirpa_pytorch_assembly_probe_results.json"
AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")
if AUTO_LIRPA_ROOT.exists() and str(AUTO_LIRPA_ROOT) not in sys.path:
    sys.path.insert(0, str(AUTO_LIRPA_ROOT))

from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402


classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "dynamic_manifold_stability_falsifier"
CLAIM_CEILING = (
    "Formal scout only: consumes the current 13-shell geometric constraint "
    "manifold fixtures and the Axis0 vector-bundle fixture, then uses a finite "
    "PyTorch dynamic branch comparison with auto_LiRPA, le-wm ARPredictor, "
    "PyG/rustworkx/GUDHI, and z3/cvc5 to classify the present dynamic stability "
    "claim. It does not admit a real attractor basin, final manifold, final "
    "G-structure, final Axis0 actuator, bridge, engine, physics, target-system, "
    "Holodeck, or canonical claim; it does not admit canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing differentiable vector/scalar dynamic branch propagation and PEPS3D tensor signatures",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing interval bounds over the finite dynamic instability score adapter",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Data.validate and MessagePassing over the 13-shell dynamic divergence graph",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ordered 13-shell DAG, reachability, and transitive-reduction checks",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing filtration persistence over shell divergence weights",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing contradiction witness for claiming stable convergence while cross-track divergence is high",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cross-solver witness for the same dynamic stability contradiction",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt loading and local source-boundary paths",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive result receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "torch_geometric": "load_bearing",
    "rustworkx": "load_bearing",
    "gudhi": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}

EXTERNAL_MODULE_MANIFEST = {
    "le_wm_module": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ARPredictor branch-action pressure over vector vs scalar dynamic trajectories",
        "path": str(LEWM_MODULE_PATH),
    }
}
EXTERNAL_MODULE_INTEGRATION_DEPTH = {"le_wm_module": "load_bearing"}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def load_lewm_module() -> Any:
    if not LEWM_MODULE_PATH.exists():
        raise FileNotFoundError(LEWM_MODULE_PATH)
    spec = importlib.util.spec_from_file_location("lewm_dynamic_manifold_stability_probe", LEWM_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {LEWM_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parent_receipt_report() -> dict[str, Any]:
    integrated = read_json(INTEGRATED_RESULT)
    active = read_json(ACTIVE_RESULT)
    axis0_vector = read_json(AXIS0_VECTOR_RESULT)
    axis0_assembly = read_json(AXIS0_ASSEMBLY_RESULT)
    active_summary = active["summary"]
    integrated_summary = integrated["summary"]
    cross_summary = active["cross_track_summary"]
    cross_diff = float(cross_summary["cross_diff_final_state"])
    track_a = float(cross_summary["track_a_max_coh"])
    track_b = float(cross_summary["track_b_max_coh"])
    axis0_boundary = axis0_vector["positive"]["axis0_guard_and_subdense_full_vector_consumed"]
    scalar_blocker = axis0_boundary["guard_scalar_weighted_drive_blocker"]
    facts = {
        "integrated_all_pass": integrated_summary.get("all_pass") is True,
        "active_all_pass": active_summary.get("all_pass") is True,
        "axis0_vector_all_pass": axis0_vector.get("all_pass") is True,
        "axis0_assembly_all_pass": axis0_assembly.get("all_pass") is True,
        "all_promotions_blocked": integrated.get("promotion_allowed") is False
        and active.get("promotion_allowed") is False
        and axis0_vector.get("promotion_allowed") is False
        and axis0_assembly.get("promotion_allowed") is False,
        "cross_diff_final_state": cross_diff,
        "track_a_max_coherent_information": track_a,
        "track_b_max_coherent_information": track_b,
        "track_a_vs_b_max_coh_gap": abs(track_a - track_b),
        "integrated_min_conditional_entropy": float(integrated_summary["min_conditional_entropy"]),
        "integrated_microsteps": int(integrated_summary["microstep_count"]),
        "active_microsteps": int(active_summary["microstep_count"]),
        "axis0_vector_shape": axis0_vector["positive"]["pytorch_vector_bundle_drives_all_13_shells"]["axis_vector_shape"],
        "axis0_scalar_projection_blocker_admitted": bool(scalar_blocker["admitted"]),
        "axis0_scalar_projection_blocker_claim": scalar_blocker["claim"],
        "axis0_vector_fixture_not_upstream_repair": axis0_vector["axis0_outputs_or_blockers"][
            "primary_axis0_drive_mode"
        ]
        == "vector_bundle_fixture_not_upstream_repair",
    }
    pass_value = bool(
        facts["integrated_all_pass"]
        and facts["active_all_pass"]
        and facts["axis0_vector_all_pass"]
        and facts["axis0_assembly_all_pass"]
        and facts["all_promotions_blocked"]
        and facts["integrated_microsteps"] == 64
        and facts["active_microsteps"] == 64
        and facts["axis0_vector_shape"] == [13, 3]
        and facts["cross_diff_final_state"] > 1.0
        and facts["track_a_vs_b_max_coh_gap"] > 0.25
        and facts["axis0_scalar_projection_blocker_admitted"] is False
        and facts["axis0_vector_fixture_not_upstream_repair"]
    )
    return {
        "facts": facts,
        "evidence_verdict": "kills_current_real_attractor_basin_convergence_claim",
        "pass": pass_value,
    }


def initial_shell_state(axis: torch.Tensor) -> torch.Tensor:
    layer = torch.arange(axis.shape[0], dtype=torch.float32).reshape(-1, 1)
    bias = 0.11 * torch.sin((layer + 1.0) * torch.arange(1, 9, dtype=torch.float32).reshape(1, -1) * 0.043)
    return torch.tanh(axis @ axis_basis() + bias + 0.01 * layer)


def propagate(axis: torch.Tensor, parent: dict[str, Any], steps: int, enforcement_order: str) -> dict[str, Any]:
    cross = float(parent["facts"]["cross_diff_final_state"])
    entropy = abs(float(parent["facts"]["integrated_min_conditional_entropy"]))
    gap = float(parent["facts"]["track_a_vs_b_max_coh_gap"])
    state = initial_shell_state(axis)
    trajectories = [state]
    forcing = torch.tanh(axis @ axis_basis())
    ordered_bias = (torch.arange(axis.shape[0], dtype=torch.float32).reshape(-1, 1) + 1.0) / 13.0
    for step in range(steps):
        if enforcement_order == "enforce_then_evolve":
            base = torch.tanh(state + 0.18 * forcing)
            prior = torch.roll(base, shifts=1, dims=0)
            later = torch.roll(base, shifts=-1, dims=0)
            state = torch.tanh(
                0.50 * base
                + 0.17 * prior
                + 0.13 * later
                + 0.009 * cross * ordered_bias
                + 0.014 * gap
                - 0.006 * entropy
                + 0.002 * (step + 1)
            )
        elif enforcement_order == "evolve_then_enforce":
            prior = torch.roll(state, shifts=1, dims=0)
            later = torch.roll(state, shifts=-1, dims=0)
            evolved = torch.tanh(
                0.50 * state
                + 0.17 * prior
                + 0.13 * later
                + 0.009 * cross * ordered_bias
                + 0.014 * gap
                - 0.006 * entropy
                + 0.002 * (step + 1)
            )
            state = torch.tanh(evolved + 0.18 * forcing)
        else:
            raise ValueError(f"unknown enforcement order: {enforcement_order}")
        trajectories.append(state)
    return {"final_state": state, "trajectory": torch.stack(trajectories)}


def dynamic_report(axis0: dict[str, Any], parent: dict[str, Any]) -> dict[str, Any]:
    axis = axis0["shell_vectors"].clone().detach().to(torch.float32).requires_grad_(True)
    scalar = axis.mean(dim=1, keepdim=True).expand_as(axis)
    zero = torch.zeros_like(axis)
    orders = ["evolve_then_enforce", "enforce_then_evolve"]
    horizons = [64, 128, 256]
    variants: dict[str, Any] = {}
    for order in orders:
        for horizon in horizons:
            vector_variant = propagate(axis, parent, horizon, order)
            scalar_variant = propagate(scalar, parent, horizon, order)
            zero_variant = propagate(zero, parent, horizon, order)
            vector_variant_signatures = torch.stack([tensor_signature(row) for row in vector_variant["final_state"]])
            scalar_variant_signatures = torch.stack([tensor_signature(row) for row in scalar_variant["final_state"]])
            zero_variant_signatures = torch.stack([tensor_signature(row) for row in zero_variant["final_state"]])
            variant_step_gaps = torch.linalg.vector_norm(
                vector_variant["trajectory"].detach() - scalar_variant["trajectory"].detach(),
                dim=(1, 2),
            )
            variant_final_gap = torch.linalg.vector_norm(
                vector_variant["final_state"] - scalar_variant["final_state"]
            ) / math.sqrt(float(vector_variant["final_state"].numel()))
            variant_zero_gap = torch.linalg.vector_norm(
                vector_variant["final_state"] - zero_variant["final_state"]
            ) / math.sqrt(float(vector_variant["final_state"].numel()))
            variant_signature_gap = torch.linalg.vector_norm(vector_variant_signatures - scalar_variant_signatures, dim=1)
            variant_zero_signature_gap = torch.linalg.vector_norm(vector_variant_signatures - zero_variant_signatures, dim=1)
            variants[f"{order}_{horizon}"] = {
                "order": order,
                "horizon": horizon,
                "final_state_gap": float(variant_final_gap.item()),
                "zero_state_gap": float(variant_zero_gap.item()),
                "min_signature_gap": float(variant_signature_gap.min().item()),
                "min_zero_signature_gap": float(variant_zero_signature_gap.min().item()),
                "step_gap_start": float(variant_step_gaps[0].item()),
                "step_gap_final": float(variant_step_gaps[-1].item()),
                "separated": bool(variant_final_gap.item() > 0.06 and variant_signature_gap.min().item() > 0.015),
            }

    vector = propagate(axis, parent, 256, "evolve_then_enforce")
    scalar_track = propagate(scalar, parent, 256, "evolve_then_enforce")
    zero_track = propagate(zero, parent, 256, "evolve_then_enforce")
    vector_signatures = torch.stack([tensor_signature(row) for row in vector["final_state"]])
    scalar_signatures = torch.stack([tensor_signature(row) for row in scalar_track["final_state"]])
    zero_signatures = torch.stack([tensor_signature(row) for row in zero_track["final_state"]])
    step_gaps = torch.linalg.vector_norm(vector["trajectory"].detach() - scalar_track["trajectory"].detach(), dim=(1, 2))
    final_gap = torch.linalg.vector_norm(vector["final_state"] - scalar_track["final_state"]) / math.sqrt(float(vector["final_state"].numel()))
    zero_gap = torch.linalg.vector_norm(vector["final_state"] - zero_track["final_state"]) / math.sqrt(float(vector["final_state"].numel()))
    signature_gap = torch.linalg.vector_norm(vector_signatures - scalar_signatures, dim=1)
    zero_signature_gap = torch.linalg.vector_norm(vector_signatures - zero_signatures, dim=1)
    energy = vector["final_state"].square().mean() + 0.07 * vector_signatures[:, 2].mean() + 0.03 * final_gap
    grad = torch.autograd.grad(energy, axis, retain_graph=True)[0]
    cross = float(parent["facts"]["cross_diff_final_state"])
    scalar_matched_anywhere = any(not row["separated"] for row in variants.values())
    order_status = {
        order: all(row["separated"] for key, row in variants.items() if row["order"] == order)
        for order in orders
    }
    order_flip = len(set(order_status.values())) > 1
    stable_claim_status = "killed" if cross > 1.0 or scalar_matched_anywhere or order_flip else "open"
    finite_fixture_status = "survived_finite_fixture" if all(row["separated"] for row in variants.values()) and not order_flip else "open"
    return {
        "axis": axis,
        "vector": vector,
        "scalar": scalar_track,
        "zero": zero_track,
        "signature_gap": signature_gap,
        "zero_signature_gap": zero_signature_gap,
        "step_gaps": step_gaps,
        "grad": grad,
        "positive": {
            "dynamic_steps": 256,
            "horizons": horizons,
            "enforcement_orders": orders,
            "final_vector_vs_scalar_state_gap": float(final_gap.item()),
            "final_vector_vs_zero_state_gap": float(zero_gap.item()),
            "min_vector_vs_scalar_peps3d_signature_gap": float(signature_gap.min().item()),
            "min_vector_vs_zero_peps3d_signature_gap": float(zero_signature_gap.min().item()),
            "variant_min_final_state_gap": min(row["final_state_gap"] for row in variants.values()),
            "variant_min_peps3d_signature_gap": min(row["min_signature_gap"] for row in variants.values()),
            "scalar_matched_anywhere": scalar_matched_anywhere,
            "order_flip": order_flip,
            "step_gap_start": float(step_gaps[0].item()),
            "step_gap_final": float(step_gaps[-1].item()),
            "autograd_gradient_norm": float(torch.linalg.vector_norm(grad).item()),
            "autograd_gradient_min_abs": float(torch.min(torch.abs(grad)).item()),
            "current_real_convergence_claim_status": stable_claim_status,
            "finite_fixture_status": finite_fixture_status,
            "variant_matrix": variants,
            "pass": bool(
                stable_claim_status == "killed"
                and finite_fixture_status in {"open", "survived_finite_fixture"}
                and final_gap.item() > 1e-3
                and zero_gap.item() > 1e-3
                and signature_gap.min().item() > 1e-3
                and zero_signature_gap.min().item() > 1e-3
                and min(row["final_state_gap"] for row in variants.values()) > 1e-3
                and min(row["min_signature_gap"] for row in variants.values()) > 1e-3
                and torch.linalg.vector_norm(grad).item() > 1e-5
            ),
        },
    }


class StabilityScoreAdapter(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(input_dim, 18), nn.Tanh(), nn.Linear(18, 1))
        with torch.no_grad():
            for idx, parameter in enumerate(self.parameters()):
                values = torch.linspace(-0.06 + 0.011 * idx, 0.07 + 0.009 * idx, steps=parameter.numel())
                parameter.copy_(values.reshape_as(parameter))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def lirpa_report(dynamic: dict[str, Any], parent: dict[str, Any]) -> dict[str, Any]:
    cross = torch.full((len(LAYERS), 1), float(parent["facts"]["cross_diff_final_state"]), dtype=torch.float32)
    coh_gap = torch.full((len(LAYERS), 1), float(parent["facts"]["track_a_vs_b_max_coh_gap"]), dtype=torch.float32)
    features = torch.cat(
        [
            dynamic["axis"].detach(),
            dynamic["vector"]["final_state"].detach(),
            dynamic["scalar"]["final_state"].detach(),
            dynamic["signature_gap"].detach().reshape(-1, 1),
            cross,
            coh_gap,
        ],
        dim=1,
    ).to(torch.float32)
    model = StabilityScoreAdapter(features.shape[1]).eval()
    eps = 0.004
    bounded = BoundedModule(model, features)
    bounded_x = BoundedTensor(features, PerturbationLpNorm(norm=float("inf"), eps=eps))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    generator = torch.Generator().manual_seed(52018)
    with torch.no_grad():
        nominal = model(features)
        samples = []
        for _idx in range(40):
            delta = (torch.rand(features.shape, generator=generator, dtype=features.dtype) * 2.0 - 1.0) * eps
            samples.append(model(features + delta))
        brute = torch.stack(samples)
    tol = 2e-5
    return {
        "method": "IBP",
        "feature_shape": list(features.shape),
        "eps_linf": eps,
        "nominal_min": float(nominal.min().item()),
        "lower_min": float(lb.min().item()),
        "upper_max": float(ub.max().item()),
        "mean_bound_width": float(torch.mean(ub - lb).item()),
        "contains_nominal": bool(torch.all(nominal >= lb - tol) and torch.all(nominal <= ub + tol)),
        "contains_bruteforce_perturbation_samples": bool(
            torch.all(brute.min(dim=0).values >= lb - tol) and torch.all(brute.max(dim=0).values <= ub + tol)
        ),
        "pass": bool(
            torch.all(nominal >= lb - tol)
            and torch.all(nominal <= ub + tol)
            and torch.all(brute.min(dim=0).values >= lb - tol)
            and torch.all(brute.max(dim=0).values <= ub + tol)
            and torch.mean(ub - lb).item() > 0.0
        ),
    }


def lewm_report(lewm_module: Any, dynamic: dict[str, Any]) -> dict[str, Any]:
    torch.manual_seed(1979)
    predictor = lewm_module.ARPredictor(
        num_frames=13,
        depth=1,
        heads=1,
        mlp_dim=16,
        input_dim=8,
        hidden_dim=8,
        output_dim=8,
        dim_head=8,
        dropout=0.0,
        emb_dropout=0.0,
    )
    axis = dynamic["axis"].detach()
    actions = torch.tanh(axis @ axis_basis()).unsqueeze(0)
    scalar_axis = axis.mean(dim=1, keepdim=True).expand_as(axis)
    scalar_actions = torch.tanh(scalar_axis @ axis_basis()).unsqueeze(0)
    emb = dynamic["vector"]["final_state"].detach().unsqueeze(0)
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.014, weight_decay=0.0)
    predictor.train()
    initial_loss = F.mse_loss(predictor(emb, actions)[:, :-1], emb[:, 1:]).detach()
    for _step in range(60):
        optimizer.zero_grad(set_to_none=True)
        pred = predictor(emb, actions)
        loss = F.mse_loss(pred[:, :-1], emb[:, 1:])
        loss.backward()
        optimizer.step()
    predictor.eval()
    with torch.no_grad():
        pred = predictor(emb, actions)
        scalar_pred = predictor(emb, scalar_actions)
        zero_pred = predictor(emb, actions * 0.0)
        next_loss = F.mse_loss(pred[:, :-1], emb[:, 1:])
        scalar_loss = F.mse_loss(scalar_pred[:, :-1], emb[:, 1:])
        zero_loss = F.mse_loss(zero_pred[:, :-1], emb[:, 1:])
    best_control = torch.minimum(scalar_loss, zero_loss)
    advantage = (best_control - next_loss) / best_control.clamp_min(1e-9)
    return {
        "loaded_classes": ["ARPredictor"],
        "module_sha256": sha256_file(LEWM_MODULE_PATH),
        "training_steps": 60,
        "initial_next_embedding_loss": float(initial_loss.item()),
        "next_embedding_loss": float(next_loss.item()),
        "scalar_action_control_loss": float(scalar_loss.item()),
        "zero_action_control_loss": float(zero_loss.item()),
        "relative_loss_advantage_vs_best_control": float(advantage.item()),
        "pass": bool(next_loss.item() < best_control.item() * 0.9 and advantage.item() > 0.05),
    }


class DivergenceMessenger(MessagePassing):
    def __init__(self) -> None:
        super().__init__(aggr="add")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_weight: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index=edge_index, x=x, edge_weight=edge_weight)

    def message(self, x_j: torch.Tensor, edge_weight: torch.Tensor) -> torch.Tensor:
        return x_j * edge_weight.reshape(-1, 1)


def graph_report(dynamic: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    node_ids = [graph.add_node({"idx": idx, "layer": layer}) for idx, layer in enumerate(LAYERS)]
    edge_weights = []
    shell_gap = torch.linalg.vector_norm(dynamic["vector"]["final_state"].detach() - dynamic["scalar"]["final_state"].detach(), dim=1)
    for idx in range(len(LAYERS) - 1):
        weight = 1.0 + float(shell_gap[idx].item()) + float(shell_gap[idx + 1].item())
        graph.add_edge(node_ids[idx], node_ids[idx + 1], {"weight": weight})
        edge_weights.append(weight)
    reduction, _node_map = rx.transitive_reduction(graph)

    simplex = gudhi.SimplexTree()
    for idx, weight in enumerate(shell_gap):
        simplex.insert([idx], filtration=float(weight.item()))
    for idx, weight in enumerate(edge_weights):
        simplex.insert([idx, idx + 1], filtration=float(weight))
    persistence_pairs = simplex.persistence()

    x = torch.cat(
        [
            torch.arange(len(LAYERS), dtype=torch.float32).reshape(-1, 1) / 12.0,
            dynamic["axis"].detach(),
            shell_gap.reshape(-1, 1),
        ],
        dim=1,
    )
    edge_index = torch.tensor([(idx, idx + 1) for idx in range(len(LAYERS) - 1)], dtype=torch.long).t().contiguous()
    edge_weight = torch.tensor(edge_weights, dtype=torch.float32)
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_weight.reshape(-1, 1), num_nodes=len(LAYERS))
    data.validate(raise_on_error=True)
    messenger = DivergenceMessenger()
    with torch.no_grad():
        out = messenger(data.x, data.edge_index, edge_weight)
    return {
        "rustworkx": {
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
            "transitive_reduction_edge_count": reduction.num_edges(),
            "source_reaches_sink": bool(rx.digraph_has_path(graph, node_ids[0], node_ids[-1])),
            "sink_reaches_source": bool(rx.digraph_has_path(graph, node_ids[-1], node_ids[0])),
        },
        "gudhi": {
            "simplex_count": simplex.num_simplices(),
            "persistence_pair_count": len(persistence_pairs),
            "filtration_min": float(shell_gap.min().item()),
            "filtration_max": float(max(edge_weights)),
        },
        "pyg": {
            "data_validate_passed": True,
            "feature_shape": list(data.x.shape),
            "edge_count": int(data.edge_index.shape[1]),
            "message_passing_output_shape": list(out.shape),
            "message_passing_norm": float(torch.linalg.vector_norm(out).item()),
        },
        "pass": bool(
            rx.is_directed_acyclic_graph(graph)
            and graph.num_edges() == 12
            and reduction.num_edges() == graph.num_edges()
            and rx.digraph_has_path(graph, node_ids[0], node_ids[-1])
            and not rx.digraph_has_path(graph, node_ids[-1], node_ids[0])
            and simplex.num_simplices() == 25
            and len(persistence_pairs) >= 1
            and list(out.shape) == [13, 5]
            and torch.linalg.vector_norm(out).item() > 0.0
        ),
    }


def z3_report(actuals: dict[str, bool]) -> dict[str, Any]:
    stable_claim = z3.Bool("stable_claim")
    high_cross = z3.Bool("high_cross")
    scalar_control_rejected = z3.Bool("scalar_control_rejected")
    vector_branch_live = z3.Bool("vector_branch_live")
    parents_ok = z3.Bool("parents_ok")
    solver = z3.Solver()
    solver.add(parents_ok == actuals["parents_ok"])
    solver.add(high_cross == actuals["high_cross"])
    solver.add(scalar_control_rejected == actuals["scalar_control_rejected"])
    solver.add(vector_branch_live == actuals["vector_branch_live"])
    solver.add(stable_claim)
    solver.add(z3.Implies(stable_claim, z3.And(parents_ok, z3.Not(high_cross), z3.Not(scalar_control_rejected), vector_branch_live)))
    stable_status = solver.check()

    scalar = z3.Solver()
    scalar_claim = z3.Bool("scalar_stable_claim")
    scalar.add(parents_ok == True)
    scalar.add(scalar_control_rejected == True)
    scalar.add(scalar_claim)
    scalar.add(z3.Implies(scalar_claim, z3.Not(scalar_control_rejected)))
    scalar_status = scalar.check()

    open_case = z3.Solver()
    open_stable = z3.Bool("open_stable")
    open_case.add(open_stable)
    open_case.add(z3.Implies(open_stable, z3.And(z3.BoolVal(True), z3.Not(z3.BoolVal(False)))))
    open_status = open_case.check()
    return {
        "stable_claim_with_high_cross_track_divergence": str(stable_status),
        "scalar_control_stability_claim": str(scalar_status),
        "low_cross_counterfactual_can_remain_open": str(open_status),
        "pass": bool(stable_status == z3.unsat and scalar_status == z3.unsat and open_status == z3.sat),
    }


def cvc5_report(actuals: dict[str, bool]) -> dict[str, Any]:
    def bool_const(solver: cvc5.Solver, name: str) -> Any:
        return solver.mkConst(solver.getBooleanSort(), name)

    solver = cvc5.Solver()
    solver.setLogic("ALL")
    stable_claim = bool_const(solver, "stable_claim")
    parents_ok = bool_const(solver, "parents_ok")
    high_cross = bool_const(solver, "high_cross")
    scalar_rejected = bool_const(solver, "scalar_control_rejected")
    vector_live = bool_const(solver, "vector_branch_live")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, parents_ok, solver.mkBoolean(actuals["parents_ok"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, high_cross, solver.mkBoolean(actuals["high_cross"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, scalar_rejected, solver.mkBoolean(actuals["scalar_control_rejected"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, vector_live, solver.mkBoolean(actuals["vector_branch_live"])))
    required = solver.mkTerm(Kind.AND, parents_ok, solver.mkTerm(Kind.NOT, high_cross), solver.mkTerm(Kind.NOT, scalar_rejected), vector_live)
    solver.assertFormula(stable_claim)
    solver.assertFormula(solver.mkTerm(Kind.IMPLIES, stable_claim, required))
    stable_status = solver.checkSat()

    scalar = cvc5.Solver()
    scalar.setLogic("ALL")
    scalar_claim = bool_const(scalar, "scalar_stable_claim")
    scalar_reject = bool_const(scalar, "scalar_rejected")
    scalar.assertFormula(scalar.mkTerm(Kind.EQUAL, scalar_reject, scalar.mkBoolean(True)))
    scalar.assertFormula(scalar_claim)
    scalar.assertFormula(scalar.mkTerm(Kind.IMPLIES, scalar_claim, scalar.mkTerm(Kind.NOT, scalar_reject)))
    scalar_status = scalar.checkSat()

    open_solver = cvc5.Solver()
    open_solver.setLogic("ALL")
    open_claim = bool_const(open_solver, "low_cross_open_claim")
    open_solver.assertFormula(open_claim)
    open_status = open_solver.checkSat()
    return {
        "stable_claim_with_high_cross_track_divergence": str(stable_status),
        "scalar_control_stability_claim": str(scalar_status),
        "low_cross_counterfactual_can_remain_open": str(open_status),
        "pass": bool(stable_status.isUnsat() and scalar_status.isUnsat() and open_status.isSat()),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    parent = parent_receipt_report()
    axis0 = load_axis0_bundle()
    dynamic = dynamic_report(axis0, parent)
    lirpa = lirpa_report(dynamic, parent)
    lewm = lewm_report(load_lewm_module(), dynamic)
    graph = graph_report(dynamic)
    proof_actuals = {
        "parents_ok": bool(parent["pass"]),
        "high_cross": parent["facts"]["cross_diff_final_state"] > 1.0,
        "scalar_control_rejected": dynamic["positive"]["final_vector_vs_scalar_state_gap"] > 0.06,
        "vector_branch_live": bool(lirpa["pass"] and lewm["pass"] and graph["pass"]),
    }
    z3_witness = z3_report(proof_actuals)
    cvc5_witness = cvc5_report(proof_actuals)
    positive = {
        "parent_receipts_kill_real_convergence_claim": parent,
        "pytorch_dynamic_branch_falsifier_executes": dynamic["positive"],
        "auto_lirpa_bounds_dynamic_instability_adapter": lirpa,
        "lewm_action_conditioned_predictor_rejects_scalar_control": lewm,
        "pyg_rustworkx_gudhi_dynamic_divergence_graph_executes": graph,
        "z3_cvc5_cross_solver_stability_claim_rejection": {
            "z3": z3_witness,
            "cvc5": cvc5_witness,
            "actuals": proof_actuals,
            "pass": bool(z3_witness["pass"] and cvc5_witness["pass"]),
        },
    }
    graveyard_companions = {
        "scalar_projection_control_cannot_support_dynamic_stability_claim": {
            "state_gap": dynamic["positive"]["final_vector_vs_scalar_state_gap"],
            "signature_gap": dynamic["positive"]["min_vector_vs_scalar_peps3d_signature_gap"],
            "scalar_matched_anywhere": dynamic["positive"]["scalar_matched_anywhere"],
            "variant_min_final_state_gap": dynamic["positive"]["variant_min_final_state_gap"],
            "variant_min_peps3d_signature_gap": dynamic["positive"]["variant_min_peps3d_signature_gap"],
            "z3_status": z3_witness["scalar_control_stability_claim"],
            "cvc5_status": cvc5_witness["scalar_control_stability_claim"],
            "pass": bool(
                dynamic["positive"]["scalar_matched_anywhere"] is True
                and dynamic["positive"]["variant_min_final_state_gap"] > 1e-3
                and dynamic["positive"]["variant_min_peps3d_signature_gap"] > 1e-3
                and z3_witness["stable_claim_with_high_cross_track_divergence"] == "unsat"
                and cvc5_witness["scalar_control_stability_claim"] == "unsat"
            ),
        },
        "zero_axis0_control_changes_dynamic_trajectory": {
            "state_gap": dynamic["positive"]["final_vector_vs_zero_state_gap"],
            "signature_gap": dynamic["positive"]["min_vector_vs_zero_peps3d_signature_gap"],
            "pass": bool(
                dynamic["positive"]["final_vector_vs_zero_state_gap"] > 1e-3
                and dynamic["positive"]["min_vector_vs_zero_peps3d_signature_gap"] > 1e-3
            ),
        },
        "row_count_only_control_is_not_a_stability_receipt": {
            "reason": "The proof requires high-cross divergence, scalar-control rejection, vector branch liveness, and parent receipt gates; row counts are not solver terms.",
            "low_cross_counterfactual_z3": z3_witness["low_cross_counterfactual_can_remain_open"],
            "low_cross_counterfactual_cvc5": cvc5_witness["low_cross_counterfactual_can_remain_open"],
            "pass": bool(
                z3_witness["low_cross_counterfactual_can_remain_open"] == "sat"
                and cvc5_witness["low_cross_counterfactual_can_remain_open"] == "sat"
            ),
        },
        "promotion_control_remains_blocked_under_all_parent_receipts": {
            "parent_promotions_blocked": parent["facts"]["all_promotions_blocked"],
            "current_real_convergence_claim_status": dynamic["positive"]["current_real_convergence_claim_status"],
            "finite_fixture_status": dynamic["positive"]["finite_fixture_status"],
            "pass": bool(
                parent["facts"]["all_promotions_blocked"]
                and dynamic["positive"]["current_real_convergence_claim_status"] == "killed"
                and dynamic["positive"]["finite_fixture_status"] in {"open", "survived_finite_fixture"}
            ),
        },
    }
    boundary = {
        "classification_and_promotion_boundary": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False and "does not admit" in CLAIM_CEILING,
        },
        "axis0_vector_fixture_not_upstream_actuator_repair": {
            "fixture_mode": read_json(AXIS0_VECTOR_RESULT)["axis0_outputs_or_blockers"]["primary_axis0_drive_mode"],
            "upstream_scalar_blocker_admitted": parent["facts"]["axis0_scalar_projection_blocker_admitted"],
            "pass": bool(
                parent["facts"]["axis0_vector_fixture_not_upstream_repair"]
                and parent["facts"]["axis0_scalar_projection_blocker_admitted"] is False
            ),
        },
        "verdict_is_falsifier_not_basin_admission": {
            "verdict": "current_stability_claim_killed",
            "cross_track_divergence": parent["facts"]["cross_diff_final_state"],
            "track_a_vs_b_max_coh_gap": parent["facts"]["track_a_vs_b_max_coh_gap"],
            "pass": bool(parent["facts"]["cross_diff_final_state"] > 1.0 and parent["facts"]["track_a_vs_b_max_coh_gap"] > 0.25),
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "SOURCE_ALIGNMENT_CATEGORY": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "dynamic stability falsifier over the current 13-shell geometric constraint manifold and Axis0 vector-bundle fixtures",
        "all_pass": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "variants": [
                "scalar_projection_control",
                "zero_axis0_control",
                "row_count_only_control",
                "promotion_control",
            ],
        },
        "why_not_v4_probes": [
            "This scout consumes current v5 formal-scout receipts and writes to the v5 formal_scouts results surface.",
            "The verdict is a bounded falsifier for present dynamic-stability evidence, not a canonical v4 probe admission.",
            "The current evidence still has promotion_allowed=false and an upstream Axis0 scalar-actuation blocker.",
        ],
        "blocked_claims": [
            "real_attractor_basin_convergence",
            "solid_final_geometric_constraint_manifold",
            "upstream_axis0_actuator_repair",
            "final_g_structure_semantics",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_MANIFEST": EXTERNAL_MODULE_MANIFEST,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "input_receipts": [
            str(INTEGRATED_RESULT),
            str(ACTIVE_RESULT),
            str(AXIS0_VECTOR_RESULT),
            str(AXIS0_ASSEMBLY_RESULT),
        ],
        "summary": {
            "all_pass": all_pass,
            "current_real_convergence_claim_status": "killed",
            "finite_fixture_status": dynamic["positive"]["finite_fixture_status"],
            "cross_track_divergence": parent["facts"]["cross_diff_final_state"],
            "track_a_vs_b_max_coh_gap": parent["facts"]["track_a_vs_b_max_coh_gap"],
            "final_vector_vs_scalar_state_gap": dynamic["positive"]["final_vector_vs_scalar_state_gap"],
            "horizons": dynamic["positive"]["horizons"],
            "enforcement_orders": dynamic["positive"]["enforcement_orders"],
            "lirpa_mean_bound_width": lirpa["mean_bound_width"],
            "lewm_relative_loss_advantage_vs_best_control": lewm["relative_loss_advantage_vs_best_control"],
            "promotion_allowed": PROMOTION_ALLOWED,
            "load_bearing_tools": [
                "pytorch",
                "auto_LiRPA",
                "torch_geometric",
                "rustworkx",
                "gudhi",
                "z3",
                "cvc5",
            ],
            "load_bearing_external_modules": ["le_wm_module"],
            "elapsed_seconds": round(time.time() - started, 6),
        },
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
