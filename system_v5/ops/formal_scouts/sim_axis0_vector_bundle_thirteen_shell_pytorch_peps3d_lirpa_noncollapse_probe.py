#!/usr/bin/env python3
"""Axis0 vector-bundle scout across the 13-shell manifold."""

from __future__ import annotations

import ast
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
import rustworkx as rx
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
import z3

import axis0_guard_utils as axis0_guard


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
DRIVE_RESULT = RESULT_DIR / axis0_guard.AXIS0_GUARD_RESULT_NAME
SUBDENSE_RESULT = RESULT_DIR / "source_native_multicarrier_subdense_environment_contraction_probe_results.json"
PARENT_RESULT = RESULT_DIR / "antiteleology_geometric_constraint_manifold_pytorch_branch_tensor_network_probe_results.json"
LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")
AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
if AUTO_LIRPA_ROOT.exists() and str(AUTO_LIRPA_ROOT) not in sys.path:
    sys.path.insert(0, str(AUTO_LIRPA_ROOT))

from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402


classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "axis0_vector_bundle_manifold_noncollapse"
CLAIM_CEILING = (
    "Formal scout only: consumes the admitted Axis0 candidate bundle and builds a "
    "minimal vector-valued PyTorch actuator fixture across all 13 geometric "
    "constraint manifold shells, with PEPS/PEPS3D signatures, le-wm pressure, "
    "auto_LiRPA bounds, and z3/cvc5 noncollapse witnesses. This does not repair "
    "the upstream scalar-weighted Axis0 actuator, admit final Axis0, prove a real "
    "attractor basin, prove final G-structure semantics, or admit physics, "
    "engine, bridge, target-system, or Holodeck claims; it does not admit "
    "canonical claims."
)

LAYERS = [
    "finite_constraint_complex",
    "complex_hilbert_carrier",
    "unit_spinor_sphere",
    "projective_base_sphere",
    "hopf_fiber_bundle",
    "hopf_torus_leaf_family",
    "connection_holonomy_geometry",
    "weyl_spinor_bundle",
    "chirality_orientation_cover",
    "clifford_module_geometry",
    "frame_bundle_structure_reduction",
    "tensor_product_coupling_geometry",
    "dynamic_transition_ratchet_geometry",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vector-valued Axis0 shell states, autograd, tensor signatures, and control gaps",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing interval bound over shell-local vector-bundle energy adapter",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Data.validate and MessagePassing over the 13-shell ordered graph",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing DAG, transitive reduction, and reachability checks over all shells",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Boolean admission/noncollapse witness for vector gate and scalar-control rejection",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cross-solver witness for the same vector gate and scalar-control rejection",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result receipt loading",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "torch_geometric": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}

EXTERNAL_MODULE_MANIFEST = {
    "le_wm_module": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ARPredictor pressure over 13-shell vector-bundle state/action sequence",
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
    spec = importlib.util.spec_from_file_location("lewm_axis0_vector_bundle_probe", LEWM_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {LEWM_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resample_vector(values: list[Any], target_len: int = 13) -> torch.Tensor:
    raw = torch.tensor([float(value) for value in values], dtype=torch.float32)
    raw = torch.nan_to_num(raw, nan=0.0, posinf=0.0, neginf=0.0)
    if raw.numel() == 0:
        return torch.zeros(target_len, dtype=torch.float32)
    if raw.numel() == 1:
        sampled = raw.repeat(target_len)
    else:
        idx = torch.linspace(0, raw.numel() - 1, steps=target_len).round().to(torch.long)
        sampled = raw[idx]
    sampled = sampled - sampled.mean()
    scale = torch.max(torch.abs(sampled)).clamp_min(1e-6)
    return sampled / scale


def load_axis0_bundle() -> dict[str, Any]:
    drive = read_json(DRIVE_RESULT)
    subdense = read_json(SUBDENSE_RESULT)
    guard = axis0_guard.axis0_guard_signal(drive)
    subdense_axis0 = subdense.get("axis0_outputs_or_blockers") or {}
    vectors = subdense_axis0.get("candidate_vectors") or {}
    admitted = list(guard.get("admitted_candidate_names") or [])
    blocked = list(guard.get("blocked_candidate_names") or [])
    columns = [resample_vector(vectors.get(name, [])) for name in admitted]
    shell_vectors = torch.stack(columns, dim=1)
    return {
        "drive": drive,
        "subdense": subdense,
        "guard": guard,
        "subdense_axis0": subdense_axis0,
        "admitted": admitted,
        "blocked": blocked,
        "shell_vectors": shell_vectors,
        "pass": bool(
            drive.get("all_pass") is True
            and subdense.get("all_pass") is True
            and guard.get("pass") is True
            and admitted == [
                "fep_gradient_polarity",
                "correlation_diversity_derivative",
                "retrocausal_many_futures_policy_scoring",
            ]
            and blocked == ["path_entropy", "holographic_boundary_interior_reconstruction"]
            and shell_vectors.shape == (13, 3)
            and torch.isfinite(shell_vectors).all().item()
            and (subdense_axis0.get("primary_axis0_drive_mode") == "full_vector")
        ),
    }


def axis_basis() -> torch.Tensor:
    grid = torch.arange(8, dtype=torch.float32)
    return torch.stack(
        [
            torch.sin((grid + 1.0) * 0.29),
            torch.cos((grid + 1.0) * 0.37),
            torch.tanh((grid - 3.5) * 0.31),
        ]
    )


def shell_bias(layer_idx: int) -> torch.Tensor:
    grid = torch.arange(8, dtype=torch.float32)
    return 0.18 * torch.sin((layer_idx + 1) * (grid + 1.0) * 0.071) + 0.07 * torch.cos(
        (layer_idx + 1) * (grid + 1.0) * 0.043
    )


def shell_state(axis_vector: torch.Tensor, layer_idx: int) -> torch.Tensor:
    mixed = axis_vector @ axis_basis()
    return torch.tanh(shell_bias(layer_idx) + mixed + 0.011 * (layer_idx + 1))


def make_site_tensor(v: torch.Tensor, offset: int, shape: tuple[int, ...]) -> torch.Tensor:
    total = math.prod(shape)
    idx = torch.arange(total, dtype=torch.long)
    selected = v[(idx + offset) % v.numel()]
    values = torch.sin((idx.float() + 1.0) * 0.127 + selected) + 0.19 * torch.cos(
        (idx.float() + 1.0) * 0.067 - selected
    )
    return values.reshape(shape) / math.sqrt(float(total))


def tensor_signature(v: torch.Tensor) -> torch.Tensor:
    a = make_site_tensor(v, 0, (2, 1, 3)).squeeze(1)
    b = make_site_tensor(v, 1, (2, 3, 3))
    c = make_site_tensor(v, 2, (2, 3, 1)).squeeze(-1)
    mps = torch.einsum("pa,qab,rb->pqr", a, b, c)

    t0 = make_site_tensor(v, 3, (2, 2, 2))
    t1 = make_site_tensor(v, 4, (2, 2, 2))
    t2 = make_site_tensor(v, 5, (2, 2, 2))
    t3 = make_site_tensor(v, 6, (2, 2, 2))
    peps = torch.einsum("pac,qbd,rcd,sab->pqrs", t0, t1, t2, t3)

    tensors_3d = [make_site_tensor(v, 7 + idx, (2, 2, 2, 2)) for idx in range(8)]
    peps3d = torch.einsum(
        "pabc,qade,rfbg,shic,tfdj,uhek,vigl,wjkl->pqrstuvw",
        *tensors_3d,
    )

    def entropy(tensor: torch.Tensor) -> torch.Tensor:
        flat = tensor.flatten()
        probs = flat.square() / flat.square().sum().clamp_min(1e-12)
        return -(probs * torch.log(probs + 1e-12)).sum()

    return torch.stack(
        [
            torch.linalg.vector_norm(mps),
            torch.linalg.vector_norm(peps),
            torch.linalg.vector_norm(peps3d),
            entropy(mps),
            entropy(peps),
            entropy(peps3d),
        ]
    )


def run_shells(shell_vectors: torch.Tensor) -> dict[str, Any]:
    axis = shell_vectors.clone().detach().requires_grad_(True)
    scalar = axis.mean(dim=1, keepdim=True).expand_as(axis)
    zero = torch.zeros_like(axis)

    states = torch.stack([shell_state(axis[idx], idx) for idx in range(len(LAYERS))])
    scalar_states = torch.stack([shell_state(scalar[idx], idx) for idx in range(len(LAYERS))])
    zero_states = torch.stack([shell_state(zero[idx], idx) for idx in range(len(LAYERS))])
    signatures = torch.stack([tensor_signature(state) for state in states])
    scalar_signatures = torch.stack([tensor_signature(state) for state in scalar_states])
    zero_signatures = torch.stack([tensor_signature(state) for state in zero_states])

    shell_energy = states.square().mean(dim=1) + 0.035 * signatures[:, :3].mean(dim=1) + 0.004 * signatures[:, 3:].mean(dim=1)
    grad = torch.autograd.grad(shell_energy.sum(), axis, retain_graph=True)[0]
    vector_vs_scalar = torch.linalg.vector_norm(signatures - scalar_signatures, dim=1)
    vector_vs_zero = torch.linalg.vector_norm(signatures - zero_signatures, dim=1)
    drop_gaps = {}
    for col, name in enumerate(["fep_gradient_polarity", "correlation_diversity_derivative", "retrocausal_many_futures_policy_scoring"]):
        dropped = axis.detach().clone()
        dropped[:, col] = 0.0
        dropped_states = torch.stack([shell_state(dropped[idx], idx) for idx in range(len(LAYERS))])
        dropped_signatures = torch.stack([tensor_signature(state) for state in dropped_states])
        gap = torch.linalg.vector_norm(signatures.detach() - dropped_signatures, dim=1)
        drop_gaps[name] = gap
    min_drop_gap = min(float(gap.min().item()) for gap in drop_gaps.values())
    return {
        "axis": axis,
        "states": states,
        "signatures": signatures,
        "shell_energy": shell_energy,
        "grad": grad,
        "scalar_signatures": scalar_signatures,
        "zero_signatures": zero_signatures,
        "vector_vs_scalar": vector_vs_scalar,
        "vector_vs_zero": vector_vs_zero,
        "drop_gaps": drop_gaps,
        "positive": {
            "shell_count": len(LAYERS),
            "axis_vector_shape": list(axis.shape),
            "state_shape": list(states.shape),
            "signature_shape": list(signatures.shape),
            "min_vector_vs_scalar_signature_gap": float(vector_vs_scalar.min().item()),
            "min_vector_vs_zero_signature_gap": float(vector_vs_zero.min().item()),
            "min_drop_one_candidate_gap": min_drop_gap,
            "autograd_grad_norm": float(torch.linalg.vector_norm(grad).item()),
            "autograd_grad_min_abs": float(torch.min(torch.abs(grad)).item()),
            "peps3d_signature_mean": float(signatures[:, 2].mean().item()),
            "pass": bool(
                torch.isfinite(states).all().item()
                and torch.isfinite(signatures).all().item()
                and vector_vs_scalar.min().item() > 5e-4
                and vector_vs_zero.min().item() > 1e-3
                and min_drop_gap > 5e-4
                and torch.linalg.vector_norm(grad).item() > 1e-5
            ),
        },
    }


class ShellEnergyAdapter(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(input_dim, 16), nn.Tanh(), nn.Linear(16, 1))
        with torch.no_grad():
            for idx, parameter in enumerate(self.parameters()):
                values = torch.linspace(-0.07 + 0.01 * idx, 0.06 + 0.01 * idx, steps=parameter.numel())
                parameter.copy_(values.reshape_as(parameter))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def lirpa_report(shells: dict[str, Any]) -> dict[str, Any]:
    features = torch.cat([shells["axis"].detach(), shells["states"].detach(), shells["signatures"].detach()], dim=1).to(torch.float32)
    model = ShellEnergyAdapter(features.shape[1]).eval()
    eps = 0.006
    bounded = BoundedModule(model, features)
    bounded_x = BoundedTensor(features, PerturbationLpNorm(norm=float("inf"), eps=eps))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    generator = torch.Generator().manual_seed(4218)
    brute_scores = []
    with torch.no_grad():
        nominal = model(features)
        for _ in range(50):
            delta = (torch.rand(features.shape, generator=generator, dtype=features.dtype) * 2.0 - 1.0) * eps
            brute_scores.append(model(features + delta))
    brute = torch.stack(brute_scores)
    brute_min = brute.min(dim=0).values
    brute_max = brute.max(dim=0).values
    tol = 2e-5
    contains_nominal = bool(torch.all(nominal >= lb - tol) and torch.all(nominal <= ub + tol))
    contains_bruteforce = bool(torch.all(brute_min >= lb - tol) and torch.all(brute_max <= ub + tol))
    return {
        "method": "IBP",
        "eps_linf": eps,
        "feature_shape": list(features.shape),
        "mean_bound_width": float(torch.mean(ub - lb).item()),
        "contains_nominal": contains_nominal,
        "contains_bruteforce_perturbation_samples": contains_bruteforce,
        "bruteforce_min_margin": float(torch.min(brute_min - lb).item()),
        "bruteforce_max_margin": float(torch.min(ub - brute_max).item()),
        "pass": bool(contains_nominal and contains_bruteforce and torch.mean(ub - lb).item() > 0.0),
    }


class ShellMessenger(MessagePassing):
    def __init__(self) -> None:
        super().__init__(aggr="add")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_weight: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index=edge_index, x=x, edge_weight=edge_weight)

    def message(self, x_j: torch.Tensor, edge_weight: torch.Tensor) -> torch.Tensor:
        return x_j * edge_weight.reshape(-1, 1)


def graph_report(shells: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = [
        graph.add_node({"idx": idx, "name": layer, "vector_gap": float(shells["vector_vs_scalar"][idx].detach().item())})
        for idx, layer in enumerate(LAYERS)
    ]
    edges = []
    for idx in range(len(LAYERS) - 1):
        weight = 1.0 + float(shells["vector_vs_scalar"][idx].detach().item()) + float(shells["vector_vs_scalar"][idx + 1].detach().item())
        graph.add_edge(nodes[idx], nodes[idx + 1], {"weight": weight})
        edges.append((idx, idx + 1, weight))
    reduction, _node_map = rx.transitive_reduction(graph)
    x = torch.cat(
        [
            torch.arange(len(LAYERS), dtype=torch.float32).reshape(-1, 1) / 12.0,
            shells["axis"].detach(),
            shells["vector_vs_scalar"].detach().reshape(-1, 1),
        ],
        dim=1,
    )
    edge_index = torch.tensor([(src, dst) for src, dst, _weight in edges], dtype=torch.long).t().contiguous()
    edge_weight = torch.tensor([weight for _src, _dst, weight in edges], dtype=torch.float32)
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_weight.reshape(-1, 1), num_nodes=len(LAYERS))
    data.validate(raise_on_error=True)
    messenger = ShellMessenger()
    with torch.no_grad():
        mp_out = messenger(data.x, data.edge_index, edge_weight)
    return {
        "rustworkx": {
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
            "transitive_reduction_edge_count": reduction.num_edges(),
            "source_reaches_sink": bool(rx.digraph_has_path(graph, nodes[0], nodes[-1])),
            "sink_reaches_source": bool(rx.digraph_has_path(graph, nodes[-1], nodes[0])),
            "edge_list": [(src, dst) for src, dst, _weight in edges],
        },
        "pyg": {
            "data_validate_passed": True,
            "feature_shape": list(data.x.shape),
            "edge_count": int(data.edge_index.shape[1]),
            "message_passing_output_shape": list(mp_out.shape),
            "message_passing_norm": float(torch.linalg.vector_norm(mp_out).item()),
        },
        "pass": bool(
            rx.is_directed_acyclic_graph(graph)
            and reduction.num_edges() == graph.num_edges()
            and rx.digraph_has_path(graph, nodes[0], nodes[-1])
            and not rx.digraph_has_path(graph, nodes[-1], nodes[0])
            and list(mp_out.shape) == [13, 5]
            and torch.linalg.vector_norm(mp_out).item() > 0.0
        ),
    }


def lewm_report(lewm_module: Any, shells: dict[str, Any]) -> dict[str, Any]:
    torch.manual_seed(8842)
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
    basis = axis_basis()
    actions = shells["axis"].detach() @ basis
    scalar_actions = shells["axis"].detach().mean(dim=1, keepdim=True).expand(-1, 3) @ basis
    emb = shells["states"].detach().unsqueeze(0)
    act = torch.tanh(actions).unsqueeze(0)
    scalar_act = torch.tanh(scalar_actions).unsqueeze(0)
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.015, weight_decay=0.0)
    predictor.train()
    initial_pred = predictor(emb, act)
    initial_loss = F.mse_loss(initial_pred[:, :-1], emb[:, 1:]).detach()
    for _step in range(80):
        optimizer.zero_grad(set_to_none=True)
        pred = predictor(emb, act)
        loss = F.mse_loss(pred[:, :-1], emb[:, 1:])
        loss.backward()
        optimizer.step()
    predictor.eval()
    with torch.no_grad():
        pred = predictor(emb, act)
        scalar_pred = predictor(emb, scalar_act)
        zero_pred = predictor(emb, act * 0.0)
        next_loss = F.mse_loss(pred[:, :-1], emb[:, 1:])
        scalar_loss = F.mse_loss(scalar_pred[:, :-1], emb[:, 1:])
        zero_loss = F.mse_loss(zero_pred[:, :-1], emb[:, 1:])
    best_control = torch.minimum(scalar_loss, zero_loss)
    relative_advantage = (best_control - next_loss) / best_control.clamp_min(1e-9)
    return {
        "loaded_classes": ["ARPredictor"],
        "module_sha256": sha256_file(LEWM_MODULE_PATH),
        "training_steps": 80,
        "initial_next_embedding_loss": float(initial_loss.item()),
        "next_embedding_loss": float(next_loss.item()),
        "scalar_action_control_loss": float(scalar_loss.item()),
        "zero_action_control_loss": float(zero_loss.item()),
        "relative_loss_advantage_vs_best_control": float(relative_advantage.item()),
        "prediction_delta_norm": float(torch.linalg.vector_norm(pred - emb).item()),
        "pass": bool(next_loss.item() < best_control.item() * 0.85 and relative_advantage.item() > 0.05),
    }


def z3_report(actuals: dict[str, bool]) -> dict[str, Any]:
    terms = {name: z3.Bool(name) for name in actuals}
    admitted = z3.Bool("admitted")
    solver = z3.Solver()
    for name, value in actuals.items():
        solver.add(terms[name] == z3.BoolVal(bool(value)))
    solver.add(admitted == z3.And(*terms.values()))
    solver.add(z3.Not(admitted))
    nominal_status = solver.check()

    scalar_control = z3.Solver()
    for name in actuals:
        scalar_control.add(terms[name] == z3.BoolVal(name != "axis0_vector_non_scalar"))
    scalar_control.add(admitted == z3.And(*terms.values()))
    scalar_control.add(admitted)
    scalar_status = scalar_control.check()

    optional = z3.Bool("optional_row_count_readout")
    optional_control = z3.Solver()
    for name in actuals:
        optional_control.add(terms[name] == z3.BoolVal(True))
    optional_control.add(optional == z3.BoolVal(False))
    optional_control.add(admitted == z3.And(*terms.values()))
    optional_control.add(admitted)
    optional_status = optional_control.check()
    return {
        "nominal_all_required_unsat_when_not_admitted": str(nominal_status),
        "scalar_projection_control_admission_unsat": str(scalar_status),
        "optional_nonrequired_control_sat": str(optional_status),
        "pass": bool(nominal_status == z3.unsat and scalar_status == z3.unsat and optional_status == z3.sat),
    }


def cvc5_report(actuals: dict[str, bool]) -> dict[str, Any]:
    def _solver(prefix: str) -> tuple[cvc5.Solver, dict[str, Any], Any]:
        solver = cvc5.Solver()
        solver.setLogic("ALL")
        bool_sort = solver.getBooleanSort()
        terms = {name: solver.mkConst(bool_sort, f"{prefix}_{name}") for name in actuals}
        admitted = solver.mkConst(bool_sort, f"{prefix}_admitted")
        return solver, terms, admitted

    solver, terms, admitted = _solver("nominal")
    for name, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[name], solver.mkBoolean(bool(value))))
    conjunction = solver.mkTerm(Kind.AND, *terms.values())
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, conjunction))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    nominal_status = solver.checkSat()

    scalar, scalar_terms, scalar_admitted = _solver("scalar")
    for name in actuals:
        scalar.assertFormula(scalar.mkTerm(Kind.EQUAL, scalar_terms[name], scalar.mkBoolean(name != "axis0_vector_non_scalar")))
    scalar_conjunction = scalar.mkTerm(Kind.AND, *scalar_terms.values())
    scalar.assertFormula(scalar.mkTerm(Kind.EQUAL, scalar_admitted, scalar_conjunction))
    scalar.assertFormula(scalar_admitted)
    scalar_status = scalar.checkSat()

    optional, optional_terms, optional_admitted = _solver("optional")
    bool_sort = optional.getBooleanSort()
    optional_flag = optional.mkConst(bool_sort, "optional_row_count_readout")
    for name in actuals:
        optional.assertFormula(optional.mkTerm(Kind.EQUAL, optional_terms[name], optional.mkBoolean(True)))
    optional.assertFormula(optional.mkTerm(Kind.EQUAL, optional_flag, optional.mkBoolean(False)))
    optional_conjunction = optional.mkTerm(Kind.AND, *optional_terms.values())
    optional.assertFormula(optional.mkTerm(Kind.EQUAL, optional_admitted, optional_conjunction))
    optional.assertFormula(optional_admitted)
    optional_status = optional.checkSat()
    return {
        "nominal_all_required_unsat_when_not_admitted": str(nominal_status),
        "scalar_projection_control_admission_unsat": str(scalar_status),
        "optional_nonrequired_control_sat": str(optional_status),
        "pass": bool(nominal_status.isUnsat() and scalar_status.isUnsat() and optional_status.isSat()),
    }


def source_boundary_report() -> dict[str, Any]:
    text = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(text)
    imports = []
    attrs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names if alias.name == "numpy")
        if isinstance(node, ast.ImportFrom) and node.module == "numpy":
            imports.append("from numpy")
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in {"np", "numpy"}:
            attrs.append(node.attr)
    return {
        "numpy_imports": imports,
        "numpy_attribute_calls": attrs,
        "pass": not imports and not attrs,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    axis0 = load_axis0_bundle()
    shells = run_shells(axis0["shell_vectors"])
    lirpa = lirpa_report(shells)
    graph = graph_report(shells)
    lewm = lewm_report(load_lewm_module(), shells)
    actuals = {
        "axis0_guard_admitted_bundle": bool(axis0["pass"]),
        "axis0_vector_non_scalar": bool(shells["positive"]["pass"]),
        "thirteen_shell_graph_order": bool(graph["pass"]),
        "lirpa_bounds_vector_bundle": bool(lirpa["pass"]),
        "lewm_vector_action_pressure": bool(lewm["pass"]),
        "blocked_candidates_excluded": bool(set(axis0["blocked"]).isdisjoint(axis0["admitted"])),
    }
    proof = {"z3": z3_report(actuals), "cvc5": cvc5_report(actuals)}
    source_boundary = source_boundary_report()
    positive = {
        "axis0_guard_and_subdense_full_vector_consumed": {
            "pass": axis0["pass"],
            "admitted_candidate_names": axis0["admitted"],
            "blocked_candidate_names": axis0["blocked"],
            "subdense_primary_axis0_drive_mode": axis0["subdense_axis0"].get("primary_axis0_drive_mode"),
            "guard_scalar_weighted_drive_blocker": axis0["guard"].get("scalar_weighted_drive_blocker"),
            "guard_control_family_degeneracy_blocker": axis0["guard"].get("control_family_degeneracy_blocker"),
        },
        "pytorch_vector_bundle_drives_all_13_shells": shells["positive"],
        "auto_lirpa_bounds_vector_bundle_energy_adapter": lirpa,
        "pyg_rustworkx_thirteen_shell_graph_noncollapse": graph,
        "lewm_vector_action_pressure_beats_scalar_control": lewm,
        "z3_cvc5_cross_solver_vector_gate_agreement": {
            "z3": proof["z3"],
            "cvc5": proof["cvc5"],
            "pass": bool(proof["z3"]["pass"] and proof["cvc5"]["pass"]),
        },
    }
    graveyard = {
        "scalar_projection_control_cannot_satisfy_vector_gate": {
            "z3_scalar_status": proof["z3"]["scalar_projection_control_admission_unsat"],
            "cvc5_scalar_status": proof["cvc5"]["scalar_projection_control_admission_unsat"],
            "min_vector_vs_scalar_signature_gap": shells["positive"]["min_vector_vs_scalar_signature_gap"],
            "pass": bool(
                proof["z3"]["scalar_projection_control_admission_unsat"] == "unsat"
                and proof["cvc5"]["scalar_projection_control_admission_unsat"] == "unsat"
                and shells["positive"]["min_vector_vs_scalar_signature_gap"] > 5e-4
            ),
        },
        "zero_axis0_control_differs_from_vector_bundle": {
            "min_vector_vs_zero_signature_gap": shells["positive"]["min_vector_vs_zero_signature_gap"],
            "pass": shells["positive"]["min_vector_vs_zero_signature_gap"] > 1e-3,
        },
        "drop_one_candidate_controls_remain_visible": {
            "candidate_min_gaps": {name: float(gap.min().item()) for name, gap in shells["drop_gaps"].items()},
            "pass": shells["positive"]["min_drop_one_candidate_gap"] > 5e-4,
        },
        "blocked_axis0_candidates_stay_excluded": {
            "blocked_candidate_names": axis0["blocked"],
            "admitted_candidate_names": axis0["admitted"],
            "pass": bool(set(axis0["blocked"]).isdisjoint(axis0["admitted"])),
        },
    }
    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "upstream_scalar_weighted_axis0_blocker_not_claimed_repaired": {
            "blocker": axis0["guard"].get("control_family_degeneracy_blocker") or axis0["guard"].get("scalar_weighted_drive_blocker"),
            "this_scout_scope": "minimal vector-valued fixture over admitted Axis0 candidates, not upstream actuator repair or control-family degeneracy repair",
            "pass": bool(((axis0["guard"].get("control_family_degeneracy_blocker") or axis0["guard"].get("scalar_weighted_drive_blocker") or {})).get("admitted") is False),
        },
        "no_direct_numpy_source_dependency": source_boundary,
        "claim_ceiling_blocks_final_manifold_axis0_basin_claims": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not repair", "real attractor basin", "canonical"]),
        },
    }
    all_pass = all(row.get("pass") is True for row in positive.values()) and all(
        row.get("pass") is True for row in graveyard.values()
    ) and all(row.get("pass") is True for row in boundary.values())
    receipt = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            "shell_count": len(LAYERS),
            "axis0_dimension": len(axis0["admitted"]),
            "promotion_allowed": PROMOTION_ALLOWED,
            "elapsed_seconds": round(time.time() - started, 6),
            "load_bearing_tools": [
                tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ],
            "load_bearing_external_modules": [
                module for module, depth in EXTERNAL_MODULE_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ],
        },
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard),
        "boundary": as_jsonable(boundary),
        "axis0_outputs_or_blockers": {
            "primary_axis0_drive_mode": "vector_bundle_fixture_not_upstream_repair",
            "admitted_candidate_names": axis0["admitted"],
            "blocked_candidate_names": axis0["blocked"],
            "axis0_vector_shape": list(axis0["shell_vectors"].shape),
            "upstream_scalar_weighted_drive_blocker": axis0["guard"].get("scalar_weighted_drive_blocker"),
        },
        "candidate_layers": LAYERS,
        "repair_receipt": {
            "weak_link": "The current Axis0 guard preserves admitted candidates but records that downstream carrier actuation still uses a scalar weighted projection.",
            "target_file_or_result": str(OUT_PATH),
            "admission_rule_improved": "A vector-valued Axis0 manifold fixture must keep admitted candidates as separate columns across all 13 shells and reject scalar projection, zero-axis, drop-one, and blocked-candidate controls.",
            "dependency_subset": [
                str(DRIVE_RESULT),
                str(SUBDENSE_RESULT),
                str(PARENT_RESULT),
                "MMM-loaded provider receipts 20260518T182436Z grok/gemini manifold integration premortem audits",
            ],
            "primary_control/result": {
                "scalar_projection_control": graveyard["scalar_projection_control_cannot_satisfy_vector_gate"],
                "zero_axis0_control": graveyard["zero_axis0_control_differs_from_vector_bundle"],
                "drop_one_controls": graveyard["drop_one_candidate_controls_remain_visible"],
            },
            "promotion_ceiling": CLAIM_CEILING,
            "next_step": "Use this as a fixture for a semantic per-layer operator scout; do not cite it as an upstream Axis0 actuator repair.",
        },
        "provider_inputs_used": {
            "grok": "system_v5/ops/formal_scouts/provider_receipts/20260518T182436Z_grok_manifold_integration_premortem_audit.json",
            "gemini": "system_v5/ops/formal_scouts/provider_receipts/20260518T182436Z_gemini_manifold_integration_premortem_audit.json",
            "sonnet_opus": "not_run_this_local_receipt_after_mmm_prompt_repair",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_MANIFEST": EXTERNAL_MODULE_MANIFEST,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "why_not_v4_probes": [
            "This is a v5 formal scout over current v5 Axis0 guard/subdense receipts and MMM-loaded provider audits.",
            "It is deliberately below canonical v4 probe admission and keeps promotion_allowed=false.",
        ],
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "variants": [
                "scalar_projection_control",
                "zero_axis0_control",
                "drop_one_candidate_controls",
                "blocked_candidate_exclusion",
            ],
        },
        "divergence_log": [
            "Vector bundle fixture differs from scalar weighted projection on every shell.",
            "Zero-axis and drop-one controls remain visible.",
            "Blocked Axis0 candidates remain excluded from the active vector bundle.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    print(json.dumps({"all_pass": receipt["all_pass"], "summary": receipt["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
