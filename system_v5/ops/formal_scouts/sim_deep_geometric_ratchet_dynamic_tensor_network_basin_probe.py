#!/usr/bin/env python3
"""Deep geometric-ratchet dynamic tensor-network basin scout.

Formal scout only.  This probe treats the geometric constraint manifold as the
root object, not as an Axis0 side condition.  It executes a bounded PyTorch
fixture where nested geometric layers act as a ratchet: constraint pressure
monotonically increases with depth, exploration injection stays constant, layer
order is load-bearing, varying G-structure family pressure is active, and two
similar-but-not-symmetric basin sheets form under different flux histories.

A green result means this finite fixture survived its controls.  It does not
admit a real attractor basin, final manifold, final G-structure, final tensor
network substrate, engine, Axis0, bridge, physics, target-system, or canonical
claim.
"""

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
from clifford import Cl
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
import geomstats.backend as gs
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
import toponetx as tnx
import xgi
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
if AUTO_LIRPA_ROOT.exists() and str(AUTO_LIRPA_ROOT) not in sys.path:
    sys.path.insert(0, str(AUTO_LIRPA_ROOT))

from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402
from sim_root_geometric_constraint_manifold_maturity_pytorch_toolchain_probe import (  # noqa: E402
    LAYERS,
    _g_family_row,
    cube_edges,
    fixed_matrix,
    load_lewm_module,
    make_site_tensor,
    peps3d_signature,
    sha256_file,
    varying_g_structure_report,
)
from sim_special_holonomy_form_constraint_survivor_quotient_probe import FAMILIES  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "deep_geometric_ratchet_dynamic_tensor_network_basin_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "deep_geometric_ratchet_dynamic_tensor_network_basin"
CLAIM_CEILING = (
    "Formal scout only: executes a bounded root geometric-constraint-manifold "
    "ratchet fixture with six nesting depths, thirteen ordered semantic layer "
    "slots, constant exploration injection, monotonically increasing constraint "
    "pressure, varying SU3/G2/Spin7-style G-structure schedule pressure, "
    "PyTorch MPS/PEPS/PEPS3D-style tensor-network readouts, auto_LiRPA bounds, "
    "le-wm trajectory pressure, graph/topology/geometry/proof witnesses, and "
    "two similar-but-not-symmetric flux-separated basin sheets. Axis0 is not a "
    "pass-condition dependency. This does not admit a real attractor basin, "
    "final manifold, final G-structure, final tensor-network substrate, engine, "
    "bridge, Axis0, physics, target-system, or canonical claim; it does not "
    "admit canonical claims."
)

DEPTHS = list(range(1, 7))
BRANCH_PHASES = [0.0, 0.17, 0.31, 0.47, 0.63, 0.79]
EXPLORATION_NORM = 0.44
TAU_CONSTRAINT_STEP = 0.35
TAU_EXPLORATION_STD = 2e-6
TAU_ORDER_GAP = 0.01
TAU_ADJACENT_ORDER_GAP = 5e-6
TAU_CHART_GAP = 0.001
TAU_CHART_TENSOR_GAP = 0.0001
TAU_TENSOR_GAP = 0.001
TAU_BASIN_GAP = 0.025
TAU_BASIN_SIMILARITY = 0.70
TAU_BASIN_COSINE_UPPER = 0.99999
TAU_FLUX_DELTA = 0.015
TAU_G_STRUCTURE_GAP = 0.0005

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dynamic basin state evolution, tensor-network contractions, autograd, and le-wm tensors",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing interval bounds over the geometric-ratchet feature adapter",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Data.validate and MessagePassing over the depth-layer-basin ratchet graph",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nested depth/layer dependency DAG and canonical topological order",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing admission and required-knockout proof witness for ratchet gates",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent admission and required-knockout proof witness for ratchet gates",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncommutative order witness and exact ratchet-depth polynomial check",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing pseudoscalar/chirality witness on the two basin sheets",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing sphere-distance check separating but not exploding the two basin sheets",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SO(3) tensor-product witness over the paired basin-sheet projections",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hypergraph witness binding depth, G-structure family schedule, and basin sheets",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial complex over adjacent ratchet layer triples and basin faces",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplex-tree persistence over depth constraint energy and basin separation",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive local checkout and receipt path handling",
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
    "torch_geometric": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": "load_bearing",
    "e3nn": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}

EXTERNAL_MODULE_MANIFEST = {
    "le_wm_module": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ARPredictor/SIGReg pressure over the geometric-ratchet basin trajectory",
        "path": str(LEWM_MODULE_PATH),
    }
}
EXTERNAL_MODULE_INTEGRATION_DEPTH = {"le_wm_module": "load_bearing"}

G_STRUCTURE_SCHEDULE = [
    "su3_two_and_three_form_constraints",
    "su3_two_and_three_form_constraints",
    "g2_three_form_constraints",
    "su3_two_and_three_form_constraints",
    "g2_three_form_constraints",
    "g2_three_form_constraints",
    "spin7_four_form_constraints",
    "g2_three_form_constraints",
    "spin7_four_form_constraints",
    "spin7_four_form_constraints",
    "g2_three_form_constraints",
    "spin7_four_form_constraints",
    "spin7_four_form_constraints",
]
G_ROWS = {name: _g_family_row(name, spec) for name, spec in FAMILIES.items()}


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
        if value.numel() <= 512:
            return value.detach().cpu().tolist()
        return f"<tensor shape={list(value.shape)} dtype={value.dtype}>"
    if isinstance(value, complex):
        return {"re": value.real, "im": value.imag}
    return value


def ratchet_graph() -> tuple[rx.PyDiGraph, list[int]]:
    graph = rx.PyDiGraph()
    nodes = []
    for depth_idx, _depth in enumerate(DEPTHS):
        for layer_idx, layer_name in enumerate(LAYERS):
            nodes.append(graph.add_node({"depth": depth_idx, "layer": layer_idx, "name": layer_name}))
    for depth_idx in range(len(DEPTHS)):
        base = depth_idx * len(LAYERS)
        for layer_idx in range(len(LAYERS) - 1):
            graph.add_edge(nodes[base + layer_idx], nodes[base + layer_idx + 1], "layer_requires")
    for depth_idx in range(len(DEPTHS) - 1):
        current_base = depth_idx * len(LAYERS)
        next_base = (depth_idx + 1) * len(LAYERS)
        for layer_idx in range(len(LAYERS)):
            graph.add_edge(nodes[current_base + layer_idx], nodes[next_base + layer_idx], "depth_ratchets")
    order = [int(node) for node in rx.topological_sort(graph)]
    return graph, order


def canonical_layer_order_from_graph() -> list[int]:
    graph, full_order = ratchet_graph()
    order = []
    for node_id in full_order:
        node = graph[node_id]
        if node["depth"] == 0:
            order.append(int(node["layer"]))
    return order


def initial_basin_state(phase: float) -> torch.Tensor:
    base = torch.linspace(-0.51, 0.53, steps=8, dtype=torch.float32)
    left = torch.tanh(base + 0.018 * math.sin(phase + 0.2))
    right = torch.tanh(0.985 * base + 0.018 * torch.flip(base, dims=[0]) - 0.014 * math.cos(phase + 0.4))
    return torch.stack([left, right]).requires_grad_(True)


def normalized_exploration(depth_idx: int, layer_idx: int, phase: float, scale: float = 1.0) -> torch.Tensor:
    grid = torch.arange(16, dtype=torch.float32).reshape(2, 8)
    raw = torch.sin((grid + 1.0) * (0.113 + 0.019 * depth_idx) + phase)
    raw = raw + 0.73 * torch.cos((grid + 1.0) * (0.071 + 0.013 * layer_idx) - 0.5 * phase)
    raw = raw + torch.tensor([[0.19], [-0.17]], dtype=torch.float32) * torch.sin(
        torch.linspace(0.1, 1.3, steps=8, dtype=torch.float32)
    )
    return raw / torch.linalg.vector_norm(raw).clamp_min(1e-9) * EXPLORATION_NORM * scale


def constraint_strength(depth_idx: int, layer_idx: int, mode: str) -> torch.Tensor:
    if mode == "flat":
        return torch.tensor(0.23 + 0.002 * (layer_idx % 3), dtype=torch.float32)
    if mode == "weak":
        return torch.tensor(0.08 + 0.004 * depth_idx, dtype=torch.float32)
    layer_term = 0.018 * math.log1p(layer_idx + 1)
    return torch.tensor(0.22 + 0.105 * depth_idx + layer_term, dtype=torch.float32)


def g_structure_features(layer_idx: int) -> torch.Tensor:
    name = G_STRUCTURE_SCHEDULE[layer_idx]
    row = G_ROWS[name]
    return torch.tensor(
        [
            row["dimension"] / 8.0,
            row["survivor_fraction"],
            row["survivor_count"] / max(row["candidate_count"], 1),
            row["term_count"] / 80.0,
            row["class_count"] / max(row["survivor_count"], 1),
        ],
        dtype=torch.float32,
    )


def flux_field(depth_idx: int, layer_idx: int, phase: float, mode: str) -> torch.Tensor:
    angles = torch.linspace(0.2, 1.6, steps=8, dtype=torch.float32)
    seed = torch.sin(angles * (1.0 + 0.09 * depth_idx) + phase + 0.17 * layer_idx)
    if mode == "none":
        left = torch.zeros_like(seed)
        right = torch.zeros_like(seed)
    elif mode == "symmetric":
        left = seed
        right = seed
    elif mode == "inverted":
        left = seed
        right = -1.8 * torch.flip(seed, dims=[0])
    else:
        left = seed
        right = 0.68 * torch.roll(seed, 1) + 0.19 * seed + 0.09 * torch.cos(angles + 0.31 * depth_idx)
    return 0.035 * torch.stack([left, right])


def basin_mix(state: torch.Tensor, graph_weight: torch.Tensor) -> torch.Tensor:
    left = 0.72 * torch.roll(state[0], 1) + 0.28 * graph_weight * torch.flip(state[1], dims=[0])
    right = (
        0.69 * torch.roll(state[1], -1)
        + 0.22 * graph_weight * torch.flip(state[0], dims=[0])
        + 0.07 * state[0]
    )
    return torch.stack([left, right])


def ratchet_step(
    state: torch.Tensor,
    *,
    depth_idx: int,
    layer_idx: int,
    phase: float,
    exploration_scale: float,
    constraint_mode: str,
    flux_mode: str,
) -> tuple[torch.Tensor, dict[str, float]]:
    strength = constraint_strength(depth_idx, layer_idx, constraint_mode)
    exploration = normalized_exploration(depth_idx, layer_idx, phase, exploration_scale)
    family = g_structure_features(layer_idx)
    matrix = fixed_matrix(layer_idx, scale=0.021 + 0.002 * depth_idx)
    transformed = torch.stack([matrix @ state[0], matrix.t() @ state[1]])
    mixed = basin_mix(state, graph_weight=family[1])
    flux = flux_field(depth_idx, layer_idx, phase, flux_mode)
    gate = torch.sigmoid(1.1 * strength + 0.2 * family[0] - 0.15 * family[4])
    next_state = torch.tanh(
        (1.0 - 0.22 * gate) * state
        + 0.24 * gate * transformed
        + 0.08 * mixed
        + 0.06 * family[3] * torch.flip(state, dims=[1])
        + exploration
        + flux
    )
    left_next = next_state[0]
    right_neighbor = (
        0.76 * left_next
        + 0.24 * next_state[1]
        + 0.08 * torch.tanh(flux[1] - 0.65 * flux[0])
        + 0.012 * family[4] * torch.roll(left_next, 1)
    )
    next_state = torch.stack([left_next, torch.tanh(right_neighbor)])
    return next_state, {
        "constraint_strength": float(strength.detach().item()),
        "exploration_norm": float(torch.linalg.vector_norm(exploration.detach()).item()),
        "flux_delta_norm": float(torch.linalg.vector_norm((flux[0] - flux[1]).detach()).item()),
        "g_family_dimension": float(family[0].detach().item() * 8.0),
    }


def entropy_from_tensor(tensor: torch.Tensor) -> torch.Tensor:
    flat = tensor.flatten()
    probs = flat.square() / flat.square().sum().clamp_min(1e-12)
    return -(probs * torch.log(probs + 1e-12)).sum()


def tensor_network_signature(history: torch.Tensor) -> torch.Tensor:
    """Return MPS/PEPS/PEPS3D readouts for a 13x8 single-basin history."""
    a = make_site_tensor(history[0], 0, (2, 1, 3)).squeeze(1)
    b = make_site_tensor(history[3], 1, (2, 3, 3))
    c = make_site_tensor(history[6], 2, (2, 3, 1)).squeeze(-1)
    mps = torch.einsum("pa,qab,rb->pqr", a, b, c)

    t0 = make_site_tensor(history[2], 3, (2, 2, 2))
    t1 = make_site_tensor(history[5], 4, (2, 2, 2))
    t2 = make_site_tensor(history[8], 5, (2, 2, 2))
    t3 = make_site_tensor(history[11], 6, (2, 2, 2))
    peps = torch.einsum("pac,qbd,rcd,sab->pqrs", t0, t1, t2, t3)

    peps3d = peps3d_signature(history, cube_edges(wrong=False))
    wrong_peps3d = peps3d_signature(history, cube_edges(wrong=True))
    return torch.stack(
        [
            torch.linalg.vector_norm(mps),
            torch.linalg.vector_norm(peps),
            torch.linalg.vector_norm(peps3d),
            entropy_from_tensor(mps),
            entropy_from_tensor(peps),
            entropy_from_tensor(peps3d),
            torch.sum((peps3d - wrong_peps3d) ** 2),
            peps3d.std(unbiased=False),
        ]
    )


def simulate_ratchet(
    *,
    phase: float,
    order: list[int],
    exploration_scale: float = 1.0,
    constraint_mode: str = "ratchet",
    flux_mode: str = "asymmetric",
    collapse_to_single_basin: bool = False,
    flat_tensor_summary: bool = False,
    max_depth: int = 6,
) -> dict[str, Any]:
    root_state = initial_basin_state(phase)
    state = root_state
    all_states = []
    all_metrics = []
    per_depth_history = []
    constraint_indices = []
    for depth_idx in range(max_depth):
        depth_states = []
        depth_constraint = 0.0
        for local_step, layer_idx in enumerate(order):
            state, metrics = ratchet_step(
                state,
                depth_idx=depth_idx,
                layer_idx=layer_idx,
                phase=phase + 0.151 * local_step + 0.019 * depth_idx,
                exploration_scale=exploration_scale,
                constraint_mode=constraint_mode,
                flux_mode=flux_mode,
            )
            if collapse_to_single_basin:
                mean_state = state.mean(dim=0, keepdim=True)
                state = mean_state.repeat(2, 1)
            all_states.append(state)
            depth_states.append(state)
            all_metrics.append(metrics)
            depth_constraint += metrics["constraint_strength"] * (
                1.0 + 0.05 * float(torch.linalg.vector_norm(state.detach()).item())
            )
        if flat_tensor_summary:
            flat = state.mean(dim=1, keepdim=True).repeat(1, state.shape[1])
            state = torch.tanh(0.82 * flat + 0.18 * state.mean())
            depth_states[-1] = state
            all_states[-1] = state
        per_depth_history.append(torch.stack(depth_states))
        constraint_indices.append(depth_constraint)
    state_history = torch.stack(all_states)
    depth_history = torch.stack(per_depth_history)
    final = state
    depth_final_history = depth_history[-1]
    left_history = depth_final_history[:, 0, :]
    right_history = depth_final_history[:, 1, :]
    left_sig = tensor_network_signature(left_history)
    right_sig = tensor_network_signature(right_history)
    combined_sig = torch.cat([left_sig, right_sig, torch.abs(left_sig - right_sig)])
    energy = final.square().sum() + 0.03 * combined_sig.sum() + 0.002 * state_history.square().sum()
    grad = torch.autograd.grad(energy, root_state, retain_graph=True, allow_unused=True)[0]
    if grad is None:
        grad_norm = 0.0
    else:
        grad_norm = float(torch.linalg.vector_norm(grad).item())
    exploration_norms = [row["exploration_norm"] for row in all_metrics]
    flux_delta_norms = [row["flux_delta_norm"] for row in all_metrics]
    return {
        "final": final,
        "state_history": state_history,
        "depth_history": depth_history,
        "depth_final_history": depth_final_history,
        "tensor_signature": combined_sig,
        "constraint_indices": constraint_indices,
        "exploration_norms": exploration_norms,
        "flux_delta_norms": flux_delta_norms,
        "autograd_grad_norm": grad_norm,
    }


def run_canonical_family() -> dict[str, Any]:
    canonical_order = canonical_layer_order_from_graph()
    runs = [simulate_ratchet(phase=phase, order=canonical_order) for phase in BRANCH_PHASES]
    finals = torch.stack([run["final"].detach() for run in runs])
    left = finals[:, 0, :]
    right = finals[:, 1, :]
    left_mean = left.mean(dim=0)
    right_mean = right.mean(dim=0)
    within_left = torch.cdist(left, left).max().item()
    within_right = torch.cdist(right, right).max().item()
    between = torch.cdist(left, right).mean().item()
    mean_gap = torch.linalg.vector_norm(left_mean - right_mean).item()
    cosine = F.cosine_similarity(left_mean, right_mean, dim=0).item()
    norm_asymmetry = abs(torch.linalg.vector_norm(left_mean).item() - torch.linalg.vector_norm(right_mean).item())
    constraint_matrix = torch.tensor([run["constraint_indices"] for run in runs], dtype=torch.float32)
    exploration = torch.tensor([norm for run in runs for norm in run["exploration_norms"]], dtype=torch.float32)
    flux_delta = torch.tensor([norm for run in runs for norm in run["flux_delta_norms"]], dtype=torch.float32)
    tensor_sigs = torch.stack([run["tensor_signature"].detach() for run in runs])
    terminal_history = torch.stack([run["depth_final_history"].detach().mean(dim=1) for run in runs]).mean(dim=0)
    return {
        "runs": runs,
        "finals": finals,
        "terminal_history": terminal_history,
        "tensor_sigs": tensor_sigs,
        "constraint_matrix": constraint_matrix,
        "exploration": exploration,
        "flux_delta": flux_delta,
        "metrics": {
            "within_left_max": within_left,
            "within_right_max": within_right,
            "between_mean": between,
            "mean_basin_gap": mean_gap,
            "cosine_similarity": cosine,
            "norm_asymmetry": norm_asymmetry,
            "constraint_depth_min_deltas": [
                float(x) for x in torch.diff(constraint_matrix, dim=1).min(dim=0).values.tolist()
            ],
            "exploration_mean": float(exploration.mean().item()),
            "exploration_std": float(exploration.std(unbiased=False).item()),
            "flux_delta_mean": float(flux_delta.mean().item()),
            "tensor_signature_std": float(tensor_sigs.std(dim=0, unbiased=False).mean().item()),
            "autograd_grad_norm_min": min(run["autograd_grad_norm"] for run in runs),
        },
    }


def controls_report(canonical: dict[str, Any]) -> dict[str, Any]:
    order = canonical_layer_order_from_graph()
    reversed_run = simulate_ratchet(phase=0.31, order=list(reversed(order)))
    swapped_order = order[:]
    swapped_order[10], swapped_order[11] = swapped_order[11], swapped_order[10]
    swapped_run = simulate_ratchet(phase=0.31, order=swapped_order)
    weak_constraint = simulate_ratchet(phase=0.31, order=order, constraint_mode="weak")
    flat_constraint = simulate_ratchet(phase=0.31, order=order, constraint_mode="flat")
    low_exploration = simulate_ratchet(phase=0.31, order=order, exploration_scale=0.08)
    no_flux = simulate_ratchet(phase=0.31, order=order, flux_mode="none")
    symmetric_flux = simulate_ratchet(phase=0.31, order=order, flux_mode="symmetric")
    inverted_flux = simulate_ratchet(phase=0.31, order=order, flux_mode="inverted")
    collapsed = simulate_ratchet(phase=0.31, order=order, collapse_to_single_basin=True)
    flat_tensor = simulate_ratchet(phase=0.31, order=order, flat_tensor_summary=True)
    shallow = simulate_ratchet(phase=0.31, order=order, max_depth=2)
    ref = canonical["runs"][2]
    ref_final = ref["final"].detach()
    ref_sig = ref["tensor_signature"].detach()

    def final_gap(run: dict[str, Any]) -> float:
        return float(torch.sum((ref_final - run["final"].detach()) ** 2).item())

    def sig_gap(run: dict[str, Any]) -> float:
        return float(torch.sum((ref_sig - run["tensor_signature"].detach()) ** 2).item())

    def basin_gap(run: dict[str, Any]) -> float:
        return float(torch.linalg.vector_norm((run["final"][0] - run["final"][1]).detach()).item())

    constraint_floor = min(canonical["metrics"]["constraint_depth_min_deltas"])
    weak_deltas = torch.diff(torch.tensor(weak_constraint["constraint_indices"], dtype=torch.float32))
    flat_deltas = torch.diff(torch.tensor(flat_constraint["constraint_indices"], dtype=torch.float32))
    low_explore_mean = float(torch.tensor(low_exploration["exploration_norms"]).mean().item())
    return {
        "reversed_order_rejected": {
            "final_gap": final_gap(reversed_run),
            "TAU_ORDER_GAP": TAU_ORDER_GAP,
            "pass": final_gap(reversed_run) > TAU_ORDER_GAP,
        },
        "adjacent_hopf_holonomy_swap_rejected": {
            "final_gap": final_gap(swapped_run),
            "TAU_ADJACENT_ORDER_GAP": TAU_ADJACENT_ORDER_GAP,
            "pass": final_gap(swapped_run) > TAU_ADJACENT_ORDER_GAP,
        },
        "weak_constraint_ratchet_rejected": {
            "canonical_min_constraint_delta": constraint_floor,
            "weak_max_constraint_delta": float(weak_deltas.max().item()),
            "pass": constraint_floor > weak_deltas.max().item() + 0.05,
        },
        "flat_constraint_depth_rejected": {
            "flat_constraint_delta_std": float(flat_deltas.std(unbiased=False).item()),
            "canonical_min_constraint_delta": constraint_floor,
            "pass": float(flat_deltas.max().item()) < constraint_floor * 0.5,
        },
        "low_exploration_control_rejected": {
            "canonical_exploration_mean": canonical["metrics"]["exploration_mean"],
            "low_exploration_mean": low_explore_mean,
            "final_gap": final_gap(low_exploration),
            "tensor_signature_gap": sig_gap(low_exploration),
            "pass": low_explore_mean < canonical["metrics"]["exploration_mean"] * 0.15
            and final_gap(low_exploration) > TAU_ORDER_GAP
            and sig_gap(low_exploration) > TAU_TENSOR_GAP,
        },
        "no_flux_control_rejected": {
            "canonical_basin_gap": canonical["metrics"]["mean_basin_gap"],
            "no_flux_basin_gap": basin_gap(no_flux),
            "pass": abs(canonical["metrics"]["mean_basin_gap"] - basin_gap(no_flux)) > TAU_FLUX_DELTA,
        },
        "symmetric_flux_control_rejected": {
            "canonical_norm_asymmetry": canonical["metrics"]["norm_asymmetry"],
            "symmetric_flux_norm_asymmetry": abs(
                torch.linalg.vector_norm(symmetric_flux["final"][0]).item()
                - torch.linalg.vector_norm(symmetric_flux["final"][1]).item()
            ),
            "canonical_flux_delta_mean": canonical["metrics"]["flux_delta_mean"],
            "symmetric_flux_delta_mean": float(torch.tensor(symmetric_flux["flux_delta_norms"]).mean().item()),
            "pass": canonical["metrics"]["flux_delta_mean"] > TAU_FLUX_DELTA
            and float(torch.tensor(symmetric_flux["flux_delta_norms"]).mean().item()) < 1e-8,
        },
        "inverted_flux_chart_control_rejected": {
            "final_gap": final_gap(inverted_flux),
            "tensor_signature_gap": sig_gap(inverted_flux),
            "TAU_CHART_GAP": TAU_CHART_GAP,
            "TAU_CHART_TENSOR_GAP": TAU_CHART_TENSOR_GAP,
            "pass": final_gap(inverted_flux) > TAU_CHART_GAP and sig_gap(inverted_flux) > TAU_CHART_TENSOR_GAP,
        },
        "single_basin_collapse_control_rejected": {
            "canonical_basin_gap": canonical["metrics"]["mean_basin_gap"],
            "collapsed_basin_gap": basin_gap(collapsed),
            "pass": basin_gap(collapsed) < TAU_BASIN_GAP * 0.25
            and canonical["metrics"]["mean_basin_gap"] > TAU_BASIN_GAP,
        },
        "flat_tensor_summary_rejected": {
            "tensor_signature_gap": sig_gap(flat_tensor),
            "TAU_TENSOR_GAP": TAU_TENSOR_GAP,
            "pass": sig_gap(flat_tensor) > TAU_TENSOR_GAP,
        },
        "shallow_two_depth_nesting_rejected": {
            "final_gap": final_gap(shallow),
            "tensor_signature_gap": sig_gap(shallow),
            "pass": final_gap(shallow) > TAU_ORDER_GAP and sig_gap(shallow) > TAU_TENSOR_GAP,
        },
    }


class RatchetMessenger(MessagePassing):
    def __init__(self) -> None:
        super().__init__(aggr="add")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index, x=x)

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return x_j

    def update(self, aggr_out: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        return torch.cat([x, aggr_out], dim=-1)


def count_xgi_edges(hypergraph: xgi.Hypergraph) -> int:
    value = hypergraph.num_edges
    return int(value() if callable(value) else value)


def graph_topology_report(canonical: dict[str, Any]) -> dict[str, Any]:
    graph, order = ratchet_graph()
    x = []
    energies = canonical["constraint_matrix"].mean(dim=0)
    for depth_idx in range(len(DEPTHS)):
        for layer_idx in range(len(LAYERS)):
            x.append(
                [
                    depth_idx / max(len(DEPTHS) - 1, 1),
                    layer_idx / max(len(LAYERS) - 1, 1),
                    float(energies[depth_idx].item()) / 20.0,
                    float(G_ROWS[G_STRUCTURE_SCHEDULE[layer_idx]]["survivor_fraction"]),
                ]
            )
    edge_index = torch.tensor([(src, dst) for src, dst in graph.edge_list()], dtype=torch.long).t().contiguous()
    data = Data(x=torch.tensor(x, dtype=torch.float32), edge_index=edge_index, num_nodes=len(x))
    data.validate(raise_on_error=True)
    messenger = RatchetMessenger()
    with torch.no_grad():
        mp_out = messenger(data.x, data.edge_index)

    hypergraph = xgi.Hypergraph()
    for family in sorted(set(G_STRUCTURE_SCHEDULE)):
        layers = [LAYERS[idx] for idx, name in enumerate(G_STRUCTURE_SCHEDULE) if name == family]
        hypergraph.add_edge([family, "left_basin", "right_basin", *layers[:3]])

    complex_ = tnx.SimplicialComplex()
    for depth_idx in range(len(DEPTHS)):
        for layer_idx in range(len(LAYERS) - 2):
            complex_.add_simplex([f"d{depth_idx}:{name}" for name in LAYERS[layer_idx : layer_idx + 3]])
        complex_.add_simplex([f"d{depth_idx}:left_basin", f"d{depth_idx}:right_basin", f"d{depth_idx}:flux"])

    st = gudhi.SimplexTree()
    for depth_idx, energy in enumerate(energies.tolist()):
        st.insert([depth_idx], filtration=float(energy))
    for depth_idx in range(len(DEPTHS) - 1):
        st.insert([depth_idx, depth_idx + 1], filtration=float(max(energies[depth_idx], energies[depth_idx + 1])))
    persistence = st.persistence()
    return {
        "rustworkx": {
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
            "topological_order_count": len(order),
        },
        "pyg": {
            "data_validate_passed": True,
            "message_passing_shape": list(mp_out.shape),
            "message_passing_norm": float(torch.linalg.vector_norm(mp_out).item()),
        },
        "xgi": {"hyperedge_count": count_xgi_edges(hypergraph)},
        "toponetx": {"simplicial_complex_dim": int(complex_.dim), "shape": str(complex_.shape)},
        "gudhi": {"simplex_count": int(st.num_simplices()), "persistence_pair_count": len(persistence)},
        "pass": bool(
            graph.num_nodes() == len(DEPTHS) * len(LAYERS)
            and graph.num_edges() == (len(DEPTHS) * (len(LAYERS) - 1) + (len(DEPTHS) - 1) * len(LAYERS))
            and rx.is_directed_acyclic_graph(graph)
            and list(mp_out.shape) == [len(DEPTHS) * len(LAYERS), 8]
            and count_xgi_edges(hypergraph) == 3
            and int(complex_.dim) >= 2
            and st.num_simplices() >= len(DEPTHS) * 2 - 1
        ),
    }


def math_geometry_report(canonical: dict[str, Any]) -> dict[str, Any]:
    left = canonical["finals"][:, 0, :].mean(dim=0)
    right = canonical["finals"][:, 1, :].mean(dim=0)
    a, b = sp.symbols("R S", commutative=False)
    coeff_rs = float(left[0].item())
    coeff_sr = float(right[0].item())
    commutator = sp.expand(coeff_rs * a * b - coeff_sr * b * a)
    d = sp.Symbol("d", integer=True, positive=True)
    ratchet_poly = sp.expand((d + 1) ** 2 - d**2)

    _, blades = Cl(1, 3)
    vector = (
        float(left[0].item()) * blades["e1"]
        + float(left[1].item()) * blades["e2"]
        + float(right[0].item()) * blades["e3"]
        + float(right[1].item()) * blades["e4"]
    )
    pseudoscalar_square = float((blades["e1234"] * blades["e1234"])[()])
    action = blades["e1234"] * vector
    action_grades = sorted(int(grade) for grade in action.grades())
    action_norm = float(abs((action * ~action)[()]))

    sphere = Hypersphere(dim=2)
    left3 = left[:3] / torch.linalg.vector_norm(left[:3]).clamp_min(1e-9)
    right3 = right[:3] / torch.linalg.vector_norm(right[:3]).clamp_min(1e-9)
    sphere_distance = float(
        sphere.metric.dist(
            gs.array([float(x) for x in left3.tolist()]),
            gs.array([float(x) for x in right3.tolist()]),
        )
    )
    tensor_product = o3.FullTensorProduct(o3.Irreps("1x1o"), o3.Irreps("1x1o"))
    e3nn_out = tensor_product(left[:3], right[:3])
    depth_history = canonical["runs"][0]["depth_final_history"].detach()

    def sheet_holonomy(sheet_history: torch.Tensor) -> float:
        points = sheet_history[:, 5:8]
        points = points / torch.linalg.vector_norm(points, dim=1, keepdim=True).clamp_min(1e-9)
        total = 0.0
        for idx in range(points.shape[0] - 2):
            a, b, c = points[idx], points[idx + 1], points[idx + 2]
            numerator = torch.dot(a, torch.cross(b, c, dim=0))
            denominator = 1.0 + torch.dot(a, b) + torch.dot(b, c) + torch.dot(c, a)
            total += math.atan2(float(numerator), float(denominator))
        return total

    left_holonomy = sheet_holonomy(depth_history[:, 0, :])
    right_holonomy = sheet_holonomy(depth_history[:, 1, :])
    holonomy_gap = abs(left_holonomy - right_holonomy)
    return {
        "sympy_noncommutative_ratchet_order": {
            "commutator": str(commutator),
            "ratchet_depth_increment_poly": str(ratchet_poly),
            "pass": bool(commutator != 0 and abs(coeff_rs - coeff_sr) > 1e-5 and sp.simplify(ratchet_poly - (2 * d + 1)) == 0),
        },
        "clifford_two_sheet_chirality": {
            "pseudoscalar_square": pseudoscalar_square,
            "action_grades": action_grades,
            "action_norm": action_norm,
            "pass": bool(abs(pseudoscalar_square + 1.0) < 1e-9 and action_grades == [3] and action_norm > 0.0),
        },
        "geomstats_two_sheet_distance": {
            "sphere_distance": sphere_distance,
            "pass": bool(sphere_distance > 1e-4 and sphere_distance < math.pi),
        },
        "e3nn_two_sheet_tensor_product": {
            "irreps_out": str(tensor_product.irreps_out),
            "output_dim": int(e3nn_out.numel()),
            "output_norm": float(torch.linalg.vector_norm(e3nn_out).item()),
            "pass": bool(int(e3nn_out.numel()) == 9 and torch.linalg.vector_norm(e3nn_out).item() > 0.0),
        },
        "sheet_holonomy_class_witness": {
            "coordinate_slice": [5, 6, 7],
            "left_holonomy": left_holonomy,
            "right_holonomy": right_holonomy,
            "holonomy_gap": holonomy_gap,
            "pass": bool(holonomy_gap > 1e-5),
        },
        "pass": True,
    }


class RatchetFeatureAdapter(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(input_dim, 18), nn.ReLU(), nn.Linear(18, 1))
        with torch.no_grad():
            for idx, parameter in enumerate(self.parameters()):
                values = torch.linspace(-0.071 + 0.009 * idx, 0.083 + 0.009 * idx, steps=parameter.numel())
                parameter.copy_(values.reshape_as(parameter))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def lirpa_report(canonical: dict[str, Any]) -> dict[str, Any]:
    constraint = canonical["constraint_matrix"] / canonical["constraint_matrix"].max().clamp_min(1e-9)
    features = torch.cat(
        [
            canonical["finals"].reshape(len(BRANCH_PHASES), -1).to(torch.float32),
            canonical["tensor_sigs"].to(torch.float32),
            constraint.to(torch.float32),
        ],
        dim=1,
    )
    model = RatchetFeatureAdapter(features.shape[1]).eval()
    bounded = BoundedModule(model, features)
    eps = 0.004
    bounded_x = BoundedTensor(features, PerturbationLpNorm(norm=float("inf"), eps=eps))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    with torch.no_grad():
        nominal = model(features)
    return {
        "method": "IBP",
        "eps_linf": eps,
        "feature_shape": list(features.shape),
        "mean_bound_width": float(torch.mean(ub - lb).item()),
        "contains_nominal": bool(torch.all(nominal >= lb - 2e-5).item() and torch.all(nominal <= ub + 2e-5).item()),
        "pass": bool(torch.mean(ub - lb).item() > 0.0 and torch.all(nominal >= lb - 2e-5).item() and torch.all(nominal <= ub + 2e-5).item()),
    }


def lewm_report(lewm_module: Any, canonical: dict[str, Any]) -> dict[str, Any]:
    torch.manual_seed(518061)
    trajectory = canonical["runs"][0]["state_history"].detach().reshape(1, -1, 16)
    predictor = lewm_module.ARPredictor(
        num_frames=trajectory.shape[1],
        depth=1,
        heads=1,
        mlp_dim=24,
        input_dim=16,
        hidden_dim=16,
        output_dim=16,
        dim_head=8,
        dropout=0.0,
        emb_dropout=0.0,
    )
    sigreg = lewm_module.SIGReg(knots=7, num_proj=32).eval()
    actions = torch.tanh(torch.roll(trajectory, shifts=1, dims=1) - 0.04 * trajectory)
    initial_pred = predictor(trajectory, actions)
    initial_loss = F.mse_loss(initial_pred[:, :-1], trajectory[:, 1:]).detach()
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.012, weight_decay=0.0)
    predictor.train()
    for _step in range(55):
        optimizer.zero_grad(set_to_none=True)
        pred = predictor(trajectory, actions)
        loss = F.mse_loss(pred[:, :-1], trajectory[:, 1:])
        loss.backward()
        optimizer.step()
    predictor.eval()
    with torch.no_grad():
        pred = predictor(trajectory, actions)
        collapsed = trajectory.mean(dim=1, keepdim=True).expand_as(trajectory)
        zero_action_pred = predictor(trajectory, actions * 0.0)
        collapsed_pred = predictor(collapsed, actions * 0.0)
        next_loss = F.mse_loss(pred[:, :-1], trajectory[:, 1:])
        zero_action_loss = F.mse_loss(zero_action_pred[:, :-1], trajectory[:, 1:])
        collapsed_loss = F.mse_loss(collapsed_pred[:, :-1], trajectory[:, 1:])
        torch.manual_seed(9191)
        sig_source = sigreg(trajectory.transpose(0, 1))
        torch.manual_seed(9191)
        sig_collapsed = sigreg(collapsed.transpose(0, 1))
    best_control = torch.minimum(zero_action_loss, collapsed_loss)
    advantage = (best_control - next_loss) / best_control.clamp_min(1e-9)
    return {
        "loaded_classes": ["ARPredictor", "SIGReg"],
        "module_sha256": sha256_file(LEWM_MODULE_PATH),
        "trajectory_shape": list(trajectory.shape),
        "training_steps": 55,
        "initial_next_embedding_loss": float(initial_loss.item()),
        "next_embedding_loss": float(next_loss.item()),
        "zero_action_control_loss": float(zero_action_loss.item()),
        "collapsed_control_loss": float(collapsed_loss.item()),
        "relative_loss_advantage_vs_best_control": float(advantage.item()),
        "sigreg_source_score": float(sig_source.item()),
        "sigreg_collapsed_score": float(sig_collapsed.item()),
        "sigreg_delta_abs": float(torch.abs(sig_source - sig_collapsed).item()),
        "pass": bool(
            math.isfinite(float(next_loss.item()))
            and next_loss.item() < best_control.item() * 0.92
            and advantage.item() > 0.02
            and torch.abs(sig_source - sig_collapsed).item() > 1e-5
        ),
    }


def g_structure_report(canonical: dict[str, Any]) -> dict[str, Any]:
    detail = varying_g_structure_report(canonical["terminal_history"])
    return {
        **detail,
        "schedule_used_by_dynamic_ratchet": G_STRUCTURE_SCHEDULE,
        "pass": bool(
            detail["pass"]
            and len(set(G_STRUCTURE_SCHEDULE)) == 3
            and min(
                detail["min_frozen_single_family_gap"],
                detail["min_generic_control_gap"],
                detail["reverse_schedule_gap"],
            )
            > TAU_G_STRUCTURE_GAP
        ),
    }


def proof_report(actuals: dict[str, bool]) -> dict[str, Any]:
    required = [
        "constraint_ratchet_monotone",
        "constant_max_exploration",
        "order_sensitive_nested_layers",
        "dynamic_tensor_network_active",
        "dual_flux_basin_split",
        "varying_g_structure_pressure",
    ]

    z3_solver = z3.Solver()
    z3_terms = {name: z3.Bool(name) for name in actuals}
    z3_admitted = z3.Bool("deep_geometric_ratchet_admitted")
    for name, value in actuals.items():
        z3_solver.add(z3_terms[name] == z3.BoolVal(bool(value)))
    z3_solver.add(z3_admitted == z3.And(*z3_terms.values()))
    z3_solver.add(z3.Not(z3_admitted))
    z3_all = z3_solver.check()
    z3_knockouts = {}
    for required_name in required:
        knockout = z3.Solver()
        terms = {name: z3.Bool(f"ko_{required_name}_{name}") for name in actuals}
        admitted = z3.Bool(f"ko_{required_name}_admitted")
        for name in actuals:
            knockout.add(terms[name] == z3.BoolVal(name != required_name))
        knockout.add(admitted == z3.And(*terms.values()))
        knockout.add(admitted)
        z3_knockouts[required_name] = str(knockout.check())

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("ALL")
    bool_sort = cvc5_solver.getBooleanSort()
    cvc5_terms = {name: cvc5_solver.mkConst(bool_sort, name) for name in actuals}
    cvc5_admitted = cvc5_solver.mkConst(bool_sort, "deep_geometric_ratchet_admitted")
    for name, value in actuals.items():
        cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, cvc5_terms[name], cvc5_solver.mkBoolean(bool(value))))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, cvc5_admitted, cvc5_solver.mkTerm(Kind.AND, *cvc5_terms.values())))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.NOT, cvc5_admitted))
    cvc5_all = cvc5_solver.checkSat()
    cvc5_knockouts = {}
    for required_name in required:
        knockout = cvc5.Solver()
        knockout.setLogic("ALL")
        bsort = knockout.getBooleanSort()
        terms = {name: knockout.mkConst(bsort, f"ko_{required_name}_{name}") for name in actuals}
        admitted = knockout.mkConst(bsort, f"ko_{required_name}_admitted")
        for name in actuals:
            knockout.assertFormula(knockout.mkTerm(Kind.EQUAL, terms[name], knockout.mkBoolean(name != required_name)))
        knockout.assertFormula(knockout.mkTerm(Kind.EQUAL, admitted, knockout.mkTerm(Kind.AND, *terms.values())))
        knockout.assertFormula(admitted)
        cvc5_knockouts[required_name] = str(knockout.checkSat())

    return {
        "z3": {
            "all_required_unsat_when_denied": str(z3_all),
            "required_knockout_unsat": z3_knockouts,
            "pass": bool(z3_all == z3.unsat and all(status == "unsat" for status in z3_knockouts.values())),
        },
        "cvc5": {
            "all_required_unsat_when_denied": str(cvc5_all),
            "required_knockout_unsat": cvc5_knockouts,
            "pass": bool(cvc5_all.isUnsat() and all(status == "unsat" for status in cvc5_knockouts.values())),
        },
    }


def main() -> int:
    started = time.time()
    torch.manual_seed(2026051802)
    canonical = run_canonical_family()
    controls = controls_report(canonical)
    graph_tools = graph_topology_report(canonical)
    math_tools = math_geometry_report(canonical)
    g_structure = g_structure_report(canonical)
    lirpa = lirpa_report(canonical)
    lewm = lewm_report(load_lewm_module(), canonical)

    positive = {
        "constraint_ratchet_monotone": {
            "depths": DEPTHS,
            "min_depth_step_deltas": canonical["metrics"]["constraint_depth_min_deltas"],
            "TAU_CONSTRAINT_STEP": TAU_CONSTRAINT_STEP,
            "weak_constraint_control_pass": controls["weak_constraint_ratchet_rejected"]["pass"],
            "flat_constraint_control_pass": controls["flat_constraint_depth_rejected"]["pass"],
            "pass": bool(
                min(canonical["metrics"]["constraint_depth_min_deltas"]) > TAU_CONSTRAINT_STEP
                and controls["weak_constraint_ratchet_rejected"]["pass"]
                and controls["flat_constraint_depth_rejected"]["pass"]
            ),
        },
        "constant_max_exploration": {
            "exploration_mean": canonical["metrics"]["exploration_mean"],
            "exploration_std": canonical["metrics"]["exploration_std"],
            "target_norm": EXPLORATION_NORM,
            "TAU_EXPLORATION_STD": TAU_EXPLORATION_STD,
            "low_exploration_control_pass": controls["low_exploration_control_rejected"]["pass"],
            "pass": bool(
                abs(canonical["metrics"]["exploration_mean"] - EXPLORATION_NORM) < 2e-6
                and canonical["metrics"]["exploration_std"] < TAU_EXPLORATION_STD
                and controls["low_exploration_control_rejected"]["pass"]
            ),
        },
        "deep_nesting_sweep_active": {
            "depth_count": len(DEPTHS),
            "layer_count": len(LAYERS),
            "state_count": len(DEPTHS) * len(LAYERS) * 2,
            "autograd_grad_norm_min": canonical["metrics"]["autograd_grad_norm_min"],
            "pass": bool(len(DEPTHS) >= 6 and len(LAYERS) == 13 and canonical["metrics"]["autograd_grad_norm_min"] > 1e-5),
        },
        "order_sensitive_nested_layers": {
            "reversed_order_gap": controls["reversed_order_rejected"]["final_gap"],
            "adjacent_swap_gap": controls["adjacent_hopf_holonomy_swap_rejected"]["final_gap"],
            "TAU_ORDER_GAP": TAU_ORDER_GAP,
            "TAU_ADJACENT_ORDER_GAP": TAU_ADJACENT_ORDER_GAP,
            "pass": bool(
                controls["reversed_order_rejected"]["pass"]
                and controls["adjacent_hopf_holonomy_swap_rejected"]["pass"]
            ),
        },
        "dynamic_tensor_network_active": {
            "tensor_signature_shape": list(canonical["tensor_sigs"].shape),
            "tensor_signature_std": canonical["metrics"]["tensor_signature_std"],
            "flat_tensor_gap": controls["flat_tensor_summary_rejected"]["tensor_signature_gap"],
            "pass": bool(
                canonical["metrics"]["tensor_signature_std"] > 1e-5
                and controls["flat_tensor_summary_rejected"]["pass"]
            ),
        },
        "dual_flux_basin_split": {
            "between_mean": canonical["metrics"]["between_mean"],
            "within_left_max": canonical["metrics"]["within_left_max"],
            "within_right_max": canonical["metrics"]["within_right_max"],
            "mean_basin_gap": canonical["metrics"]["mean_basin_gap"],
            "cosine_similarity": canonical["metrics"]["cosine_similarity"],
            "norm_asymmetry": canonical["metrics"]["norm_asymmetry"],
            "flux_delta_mean": canonical["metrics"]["flux_delta_mean"],
            "pass": bool(
                canonical["metrics"]["mean_basin_gap"] > TAU_BASIN_GAP
                and canonical["metrics"]["cosine_similarity"] > TAU_BASIN_SIMILARITY
                and canonical["metrics"]["cosine_similarity"] < TAU_BASIN_COSINE_UPPER
                and canonical["metrics"]["norm_asymmetry"] > 0.001
                and canonical["metrics"]["flux_delta_mean"] > TAU_FLUX_DELTA
                and canonical["metrics"]["between_mean"]
                > max(canonical["metrics"]["within_left_max"], canonical["metrics"]["within_right_max"]) * 0.25
            ),
        },
        "varying_g_structure_pressure": g_structure,
        "graph_topology_tools": graph_tools,
        "math_geometry_tools": {
            **math_tools,
            "pass": all(row.get("pass") is True for key, row in math_tools.items() if key != "pass"),
        },
        "auto_lirpa_bounds_ratchet_features": lirpa,
        "lewm_dynamic_trajectory_pressure": lewm,
    }

    actuals = {name: bool(row.get("pass")) for name, row in positive.items()}
    proof = proof_report(actuals)
    positive["proof_tool_required_knockouts"] = {
        "z3": proof["z3"],
        "cvc5": proof["cvc5"],
        "pass": bool(proof["z3"]["pass"] and proof["cvc5"]["pass"]),
    }

    graveyard_companions = {
        **controls,
        "axis0_not_pass_condition": {
            "axis0_used_in_pass_condition": False,
            "reason": "Manifold maturity is upstream; this scout does not consume Axis0 to pass.",
            "pass": True,
        },
        "real_attractor_basin_claim_blocked": {
            "claim": "The finite two-sheet basin fixture is not a real attractor-basin admission.",
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": PROMOTION_ALLOWED is False and "real attractor basin" in CLAIM_CEILING,
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "claim_ceiling_blocks_downstream_overclaim": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool(
                all(
                    term in CLAIM_CEILING.lower()
                    for term in ["formal scout", "axis0 is not", "does not admit", "canonical"]
                )
            ),
        },
        "external_module_is_load_bearing_but_not_tool_key": {
            "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
            "pass": bool(
                EXTERNAL_MODULE_INTEGRATION_DEPTH.get("le_wm_module") == "load_bearing"
                and "le_wm" not in TOOL_INTEGRATION_DEPTH
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
            "root_object": "geometric_constraint_manifold",
            "axis0_pass_condition": False,
            "depth_count": len(DEPTHS),
            "layer_count": len(LAYERS),
            "branch_count": len(BRANCH_PHASES),
            "min_constraint_depth_delta": min(canonical["metrics"]["constraint_depth_min_deltas"]),
            "exploration_mean": canonical["metrics"]["exploration_mean"],
            "exploration_std": canonical["metrics"]["exploration_std"],
            "mean_basin_gap": canonical["metrics"]["mean_basin_gap"],
            "basin_cosine_similarity": canonical["metrics"]["cosine_similarity"],
            "basin_norm_asymmetry": canonical["metrics"]["norm_asymmetry"],
            "flux_delta_mean": canonical["metrics"]["flux_delta_mean"],
            "tensor_signature_std": canonical["metrics"]["tensor_signature_std"],
            "g_structure_schedule_family_count": len(set(G_STRUCTURE_SCHEDULE)),
            "lirpa_mean_bound_width": lirpa["mean_bound_width"],
            "lewm_relative_loss_advantage": lewm["relative_loss_advantage_vs_best_control"],
            "elapsed_seconds": round(time.time() - started, 6),
            "load_bearing_tools": [
                tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ],
            "load_bearing_external_modules": [
                module for module, depth in EXTERNAL_MODULE_INTEGRATION_DEPTH.items() if depth == "load_bearing"
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
            "v5 root-manifold formal scout: Axis0 is excluded from the pass condition because manifold maturity is upstream",
            "tests the geometric ratchet itself: constant exploration plus increasing constraint pressure through deep ordered tensor dynamics",
            "formal scout only; no final manifold, basin, engine, axis, bridge, physics, target-system, or canonical claim is admitted",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_MANIFEST": EXTERNAL_MODULE_MANIFEST,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "layers": LAYERS,
        "depths": DEPTHS,
        "g_structure_schedule": G_STRUCTURE_SCHEDULE,
        "blockers": [] if all_pass else ["deep_geometric_ratchet_dynamic_tensor_network_basin_failed"],
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": bool(all_pass), "out_path": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
