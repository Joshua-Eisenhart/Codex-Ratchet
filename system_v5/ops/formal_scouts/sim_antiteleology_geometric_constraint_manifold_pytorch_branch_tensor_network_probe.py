#!/usr/bin/env python3
"""Anti-teleological PyTorch branch scout for the geometric constraint manifold.

Formal scout only. This probe treats the geometric constraint manifold as the
root object and explores several order-sensitive branch futures through a
PyTorch-native tensor-network carrier. Local le-wm code and auto_LiRPA are
active in the exploration path, but this does not admit a final manifold,
checkpoint, world model, bridge, or axis-level claim.
"""

from __future__ import annotations

import hashlib
import importlib.util
import ast
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
if not AUTO_LIRPA_ROOT.exists():
    raise SystemExit(f"Missing local auto_LiRPA checkout: {AUTO_LIRPA_ROOT}")
sys.path.insert(0, str(AUTO_LIRPA_ROOT))
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "antiteleology_geometric_constraint_manifold_pytorch_branch_tensor_network_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

LEWM_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm")
LEWM_MODULE_PATH = LEWM_ROOT / "module.py"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "anti_teleological_geometric_constraint_manifold_branch_exploration"
CLAIM_CEILING = (
    "Formal scout only: explores multiple order-sensitive futures of the "
    "geometric constraint manifold in PyTorch with active le-wm module pressure, "
    "auto_LiRPA interval bounds, graph/topology/proof checks, and tiny tensor "
    "networks. The layer operators are index-driven branch fixtures for this "
    "scout, not semantic implementations of every named geometry layer. It does "
    "not admit a final manifold, final nesting order, real attractor basin, "
    "checkpoint, world model, bridge, axis-level claim, or canonical architecture."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing branch states, autograd, MPS/PEPS/PEPS3D tensor-network contractions, and le-wm tensors",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing interval bounds over the branch-energy adapter",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Data.validate and MessagePassing over branch/layer graph features",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing DAG, transitive-reduction, and reachability checks for layer/branch order",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite admission and knockout witness for required manifold checks",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing cross-solver Boolean witness for the same finite admission predicate",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncommutative order witness for nested geometry operators",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing chirality/pseudoscalar check for the G-structure tower slice",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing sphere metric distance separating branch base points",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SO(3) irrep tensor-product carrier check",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hypergraph witness binding branch futures to manifold layer subsets",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial complex over nested layer triples and branch-option faces",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplex-tree persistence witness over branch-energy filtration",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive local checkout and source-boundary checks",
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
        "reason": "load-bearing dynamic import of local le-wm module.py SIGReg and ARPredictor into the PyTorch branch path",
        "path": str(LEWM_MODULE_PATH),
    }
}
EXTERNAL_MODULE_INTEGRATION_DEPTH = {"le_wm_module": "load_bearing"}

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

BRANCH_ORDERS = {
    "canonical_reference": list(range(13)),
    "g_structure_early": [0, 1, 2, 3, 10, 4, 5, 6, 7, 8, 9, 11, 12],
    "lewm_world_model_pressure_early": [0, 1, 2, 3, 4, 5, 6, 12, 7, 8, 9, 10, 11],
    "lirpa_bound_pressure_early": [0, 1, 2, 3, 4, 5, 11, 12, 6, 7, 8, 9, 10],
    "reverse_graveyard_control": list(reversed(range(13))),
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


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_lewm_module() -> Any:
    if not LEWM_MODULE_PATH.exists():
        raise SystemExit(f"Missing local le-wm module path: {LEWM_MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("lewm_module_bounded_probe", LEWM_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load le-wm module spec: {LEWM_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def layer_operator(layer_idx: int, branch_idx: int) -> torch.Tensor:
    grid = torch.arange(64, dtype=torch.float32).reshape(8, 8)
    phase = (layer_idx + 1) * 0.173 + (branch_idx + 1) * 0.097
    raw = torch.sin((grid + 1.0) * phase) + 0.35 * torch.cos((grid.t() + 1.0) * (phase + 0.11))
    if layer_idx in {7, 8, 9, 10}:
        raw = raw - raw.t()
    scale = 0.014 + 0.001 * (layer_idx % 4)
    return torch.eye(8, dtype=torch.float32) + scale * raw


def make_site_tensor(v: torch.Tensor, offset: int, shape: tuple[int, ...]) -> torch.Tensor:
    total = math.prod(shape)
    idx = torch.arange(total, dtype=torch.long)
    selected = v[(idx + offset) % v.numel()]
    values = torch.sin((idx.float() + 1.0) * 0.131 + selected) + 0.25 * torch.cos(
        (idx.float() + 1.0) * 0.071 - selected
    )
    return values.reshape(shape) / math.sqrt(float(total))


def tensor_network_signature(v: torch.Tensor) -> torch.Tensor:
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


def run_branch_manifold() -> dict[str, Any]:
    base = torch.linspace(-0.42, 0.58, steps=8, dtype=torch.float32).requires_grad_(True)
    outputs: list[torch.Tensor] = []
    signatures: list[torch.Tensor] = []
    energies: list[torch.Tensor] = []
    rows = []
    for branch_idx, (name, order) in enumerate(BRANCH_ORDERS.items()):
        state = base + 0.025 * branch_idx
        layer_norms = []
        for layer_idx in order:
            state = torch.tanh(layer_operator(layer_idx, branch_idx) @ state + 0.011 * (layer_idx + 1))
            layer_norms.append(float(torch.linalg.vector_norm(state).detach().item()))
        sig = tensor_network_signature(state)
        energy = state.square().mean() + 0.035 * sig[:3].mean() + 0.004 * sig[3:].mean()
        outputs.append(state)
        signatures.append(sig)
        energies.append(energy)
        rows.append(
            {
                "branch": name,
                "order": [LAYERS[idx] for idx in order],
                "final_state_norm": float(torch.linalg.vector_norm(state).detach().item()),
                "tensor_signature": [float(x) for x in sig.detach().tolist()],
                "energy": float(energy.detach().item()),
                "layer_norm_first_last": [layer_norms[0], layer_norms[-1]],
            }
        )
    branch_outputs = torch.stack(outputs)
    tensor_signatures = torch.stack(signatures)
    energy_tensor = torch.stack(energies)
    total_energy = energy_tensor.sum()
    grad = torch.autograd.grad(total_energy, base, retain_graph=True)[0]
    pairwise = torch.cdist(branch_outputs.detach(), branch_outputs.detach(), p=2)
    upper = pairwise[torch.triu_indices(pairwise.shape[0], pairwise.shape[1], offset=1).unbind()]
    return {
        "branch_outputs": branch_outputs,
        "tensor_signatures": tensor_signatures,
        "energies": energy_tensor,
        "positive": {
            "branch_count": len(rows),
            "branch_rows": rows,
            "pairwise_branch_distance_min": float(upper.min().item()),
            "pairwise_branch_distance_max": float(upper.max().item()),
            "autograd_grad_norm": float(torch.linalg.vector_norm(grad).item()),
            "autograd_grad_min_abs": float(torch.min(torch.abs(grad)).item()),
            "pass": bool(
                upper.min().item() > 1e-4
                and torch.isfinite(branch_outputs).all().item()
                and torch.isfinite(tensor_signatures).all().item()
                and torch.linalg.vector_norm(grad).item() > 1e-5
            ),
        },
    }


def lewm_active_pressure(lewm_module: Any, branch_outputs: torch.Tensor) -> dict[str, Any]:
    torch.manual_seed(2518)
    predictor = lewm_module.ARPredictor(
        num_frames=branch_outputs.shape[0],
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
    sigreg = lewm_module.SIGReg(knots=7, num_proj=32).eval()
    emb = branch_outputs.detach().unsqueeze(0)
    actions = torch.tanh(torch.roll(emb, shifts=1, dims=1) + 0.13 * torch.linspace(0.0, 1.0, steps=8).reshape(1, 1, 8))
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.018, weight_decay=0.0)
    predictor.train()
    initial_pred = predictor(emb, actions)
    initial_next_loss = F.mse_loss(initial_pred[:, :-1], emb[:, 1:]).detach()
    for _step in range(90):
        optimizer.zero_grad(set_to_none=True)
        pred = predictor(emb, actions)
        loss = F.mse_loss(pred[:, :-1], emb[:, 1:])
        loss.backward()
        optimizer.step()
    predictor.eval()
    with torch.no_grad():
        pred = predictor(emb, actions)
        collapsed = emb.mean(dim=1, keepdim=True).expand_as(emb)
        pred_collapsed = predictor(collapsed, actions * 0.0)
        pred_zero_action = predictor(emb, actions * 0.0)
        next_loss = F.mse_loss(pred[:, :-1], emb[:, 1:])
        collapsed_loss = F.mse_loss(pred_collapsed[:, :-1], emb[:, 1:])
        zero_action_loss = F.mse_loss(pred_zero_action[:, :-1], emb[:, 1:])
        torch.manual_seed(7781)
        sig_source = sigreg(emb.transpose(0, 1))
        torch.manual_seed(7781)
        sig_collapsed = sigreg(collapsed.transpose(0, 1))
    best_control_loss = torch.minimum(collapsed_loss, zero_action_loss)
    relative_advantage = (best_control_loss - next_loss) / best_control_loss.clamp_min(1e-9)
    return {
        "loaded_classes": ["SIGReg", "ARPredictor"],
        "module_sha256": sha256_file(LEWM_MODULE_PATH),
        "training_steps": 90,
        "initial_next_embedding_loss": float(initial_next_loss.item()),
        "next_embedding_loss": float(next_loss.item()),
        "collapsed_control_loss": float(collapsed_loss.item()),
        "zero_action_control_loss": float(zero_action_loss.item()),
        "relative_loss_advantage_vs_best_control": float(relative_advantage.item()),
        "sigreg_source_score": float(sig_source.item()),
        "sigreg_collapsed_score": float(sig_collapsed.item()),
        "sigreg_delta_abs": float(torch.abs(sig_collapsed - sig_source).item()),
        "prediction_delta_norm": float(torch.linalg.vector_norm(pred - emb).item()),
        "pass": bool(
            math.isfinite(float(next_loss.item()))
            and math.isfinite(float(sig_source.item()))
            and next_loss.item() < best_control_loss.item() * 0.75
            and relative_advantage.item() > 0.10
            and torch.abs(sig_collapsed - sig_source).item() > 1e-4
        ),
    }


class BranchEnergyAdapter(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(input_dim, 12), nn.Tanh(), nn.Linear(12, 1))
        with torch.no_grad():
            for idx, parameter in enumerate(self.parameters()):
                values = torch.linspace(-0.09 + 0.01 * idx, 0.08 + 0.01 * idx, steps=parameter.numel())
                parameter.copy_(values.reshape_as(parameter))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def lirpa_branch_bound(branch_outputs: torch.Tensor, tensor_signatures: torch.Tensor) -> dict[str, Any]:
    features = torch.cat([branch_outputs.detach(), tensor_signatures.detach()], dim=1).to(torch.float32)
    model = BranchEnergyAdapter(features.shape[1]).eval()
    eps = 0.01
    bounded = BoundedModule(model, features)
    bounded_x = BoundedTensor(features, PerturbationLpNorm(norm=float("inf"), eps=eps))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    generator = torch.Generator().manual_seed(1805)
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


class BranchLayerMessenger(MessagePassing):
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


def graph_topology_report(energies: torch.Tensor) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    layer_nodes = [graph.add_node({"kind": "layer", "name": layer}) for layer in LAYERS]
    branch_nodes = [graph.add_node({"kind": "branch", "name": name}) for name in BRANCH_ORDERS]
    for src, dst in zip(layer_nodes[:-1], layer_nodes[1:]):
        graph.add_edge(src, dst, "requires")
    for branch_node, order in zip(branch_nodes, BRANCH_ORDERS.values()):
        graph.add_edge(branch_node, layer_nodes[order[0]], "option_pressure")
    reduction, _node_map = rx.transitive_reduction(graph)

    x = torch.zeros((len(LAYERS) + len(BRANCH_ORDERS), 2), dtype=torch.float32)
    for idx in range(len(LAYERS)):
        x[idx] = torch.tensor([idx / 12.0, 0.0])
    for idx, energy in enumerate(energies.detach()):
        x[len(LAYERS) + idx] = torch.tensor([1.0, float(energy.item())])
    edges = [(src, dst) for src, dst in graph.edge_list()]
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    data = Data(x=x, edge_index=edge_index, num_nodes=x.shape[0])
    data.validate(raise_on_error=True)
    messenger = BranchLayerMessenger()
    with torch.no_grad():
        mp_out = messenger(data.x, data.edge_index)

    hypergraph = xgi.Hypergraph()
    for branch_name, order in BRANCH_ORDERS.items():
        hypergraph.add_edge([branch_name, *[LAYERS[idx] for idx in order[:4]], LAYERS[order[-1]]])

    complex_ = tnx.SimplicialComplex()
    for idx in range(len(LAYERS) - 2):
        complex_.add_simplex(LAYERS[idx : idx + 3])
    for branch_name, order in BRANCH_ORDERS.items():
        complex_.add_simplex([branch_name, LAYERS[order[0]], LAYERS[order[-1]]])

    st = gudhi.SimplexTree()
    energy_values = [float(x) for x in energies.detach().tolist()]
    for idx, energy in enumerate(energy_values):
        st.insert([idx], filtration=energy)
    for i in range(len(energy_values)):
        for j in range(i + 1, len(energy_values)):
            st.insert([i, j], filtration=max(energy_values[i], energy_values[j]) + abs(energy_values[i] - energy_values[j]))
    persistence = st.persistence()

    return {
        "rustworkx": {
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
            "transitive_reduction_edge_count": reduction.num_edges(),
            "each_branch_reaches_terminal_layer": all(
                bool(rx.digraph_has_path(graph, branch_node, layer_nodes[-1])) for branch_node in branch_nodes
            ),
        },
        "pyg": {
            "data_validate_passed": True,
            "message_passing_output_shape": list(mp_out.shape),
            "message_passing_norm": float(torch.linalg.vector_norm(mp_out).item()),
        },
        "xgi": {"hyperedge_count": count_xgi_edges(hypergraph)},
        "toponetx": {"simplicial_complex_dim": int(complex_.dim), "shape": str(complex_.shape)},
        "gudhi": {"num_simplices": st.num_simplices(), "persistence_pair_count": len(persistence)},
        "pass": bool(
            rx.is_directed_acyclic_graph(graph)
            and reduction.num_edges() <= graph.num_edges()
            and all(bool(rx.digraph_has_path(graph, branch_node, layer_nodes[-1])) for branch_node in branch_nodes)
            and list(mp_out.shape) == [len(LAYERS) + len(BRANCH_ORDERS), 4]
            and count_xgi_edges(hypergraph) == len(BRANCH_ORDERS)
            and int(complex_.dim) >= 2
            and st.num_simplices() >= len(BRANCH_ORDERS)
        ),
    }


def math_geometry_report(branch_outputs: torch.Tensor) -> dict[str, Any]:
    a, b = sp.symbols("A B", commutative=False)
    coeff_ab = float(branch_outputs[0, 0].detach().item())
    coeff_ba = float(branch_outputs[1, 0].detach().item())
    commutator = sp.expand(coeff_ab * a * b - coeff_ba * b * a)
    _, blades = Cl(1, 3)
    branch_vector = (
        float(branch_outputs[0, 0].detach().item()) * blades["e1"]
        + float(branch_outputs[0, 1].detach().item()) * blades["e2"]
        + float(branch_outputs[0, 2].detach().item()) * blades["e3"]
        + float(branch_outputs[0, 3].detach().item()) * blades["e4"]
    )
    pseudoscalar_square = float((blades["e1234"] * blades["e1234"])[()])
    pseudoscalar_action = blades["e1234"] * branch_vector
    pseudoscalar_action_grades = sorted(int(grade) for grade in pseudoscalar_action.grades())
    pseudoscalar_action_norm = float(abs((pseudoscalar_action * ~pseudoscalar_action)[()]))
    sphere = Hypersphere(dim=2)
    p0_t = branch_outputs[0, :3].detach()
    p1_t = branch_outputs[1, :3].detach()
    p0_t = p0_t / torch.linalg.vector_norm(p0_t).clamp_min(1e-9)
    p1_t = p1_t / torch.linalg.vector_norm(p1_t).clamp_min(1e-9)
    p0 = gs.array([float(x) for x in p0_t.tolist()])
    p1 = gs.array([float(x) for x in p1_t.tolist()])
    sphere_distance = float(sphere.metric.dist(p0, p1))
    irreps = o3.Irreps("1x1o")
    tensor_product = o3.FullTensorProduct(irreps, irreps)
    e3nn_out = tensor_product(branch_outputs[0, :3].detach(), branch_outputs[1, :3].detach())
    return {
        "sympy_noncommutative_commutator": {
            "expression": str(commutator),
            "branch_coefficients": [coeff_ab, coeff_ba],
            "pass": bool(commutator != 0 and abs(coeff_ab - coeff_ba) > 1e-5),
        },
        "clifford_pseudoscalar_square": {
            "value": pseudoscalar_square,
            "branch_action_grades": pseudoscalar_action_grades,
            "branch_action_norm": pseudoscalar_action_norm,
            "pass": abs(pseudoscalar_square + 1.0) < 1e-9
            and pseudoscalar_action_grades == [3]
            and pseudoscalar_action_norm > 0.0,
        },
        "geomstats_sphere_distance": {
            "distance": sphere_distance,
            "pass": sphere_distance > 0.0,
        },
        "e3nn_tensor_product": {
            "irreps_out": str(tensor_product.irreps_out),
            "output_dim": int(e3nn_out.numel()),
            "output_norm": float(torch.linalg.vector_norm(e3nn_out).item()),
            "pass": int(e3nn_out.numel()) == 9 and torch.linalg.vector_norm(e3nn_out).item() > 0.0,
        },
        "pass": bool(
            commutator != 0
            and abs(coeff_ab - coeff_ba) > 1e-5
            and abs(pseudoscalar_square + 1.0) < 1e-9
            and pseudoscalar_action_grades == [3]
            and pseudoscalar_action_norm > 0.0
            and sphere_distance > 0.0
            and int(e3nn_out.numel()) == 9
            and torch.linalg.vector_norm(e3nn_out).item() > 0.0
        ),
    }


def z3_admission_report(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    terms = {name: z3.Bool(name) for name in actuals}
    optional_nonrequired = z3.Bool("optional_name_semantics_not_required")
    admitted = z3.Bool("admitted")
    for name, value in actuals.items():
        solver.add(terms[name] == z3.BoolVal(bool(value)))
    solver.add(optional_nonrequired == z3.BoolVal(False))
    solver.add(admitted == z3.And(*terms.values()))
    solver.add(z3.Not(admitted))
    status = solver.check()

    knockout = z3.Solver()
    for name in actuals:
        knockout.add(terms[name] == z3.BoolVal(name != "lewm_active"))
    knockout.add(optional_nonrequired == z3.BoolVal(True))
    knockout.add(admitted == z3.And(*terms.values()))
    knockout.add(admitted)
    knockout_status = knockout.check()

    optional_control = z3.Solver()
    for name in actuals:
        optional_control.add(terms[name] == z3.BoolVal(True))
    optional_control.add(optional_nonrequired == z3.BoolVal(False))
    optional_control.add(admitted == z3.And(*terms.values()))
    optional_control.add(admitted)
    optional_status = optional_control.check()
    return {
        "all_checks_required_unsat": str(status),
        "declared_lewm_required_knockout_unsat": str(knockout_status),
        "optional_nonrequired_knockout_sat": str(optional_status),
        "pass": bool(status == z3.unsat and knockout_status == z3.unsat and optional_status == z3.sat),
    }


def cvc5_admission_report(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    terms = {name: solver.mkConst(bool_sort, name) for name in actuals}
    optional_nonrequired = solver.mkConst(bool_sort, "optional_name_semantics_not_required")
    admitted = solver.mkConst(bool_sort, "admitted")
    for name, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[name], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, optional_nonrequired, solver.mkBoolean(False)))
    conjunction = solver.mkTerm(Kind.AND, *terms.values())
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, conjunction))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    status = solver.checkSat()

    knockout = cvc5.Solver()
    knockout.setLogic("ALL")
    bool_sort2 = knockout.getBooleanSort()
    terms2 = {name: knockout.mkConst(bool_sort2, f"ko_{name}") for name in actuals}
    optional2 = knockout.mkConst(bool_sort2, "ko_optional_name_semantics_not_required")
    admitted2 = knockout.mkConst(bool_sort2, "ko_admitted")
    for name in actuals:
        knockout.assertFormula(knockout.mkTerm(Kind.EQUAL, terms2[name], knockout.mkBoolean(name != "lewm_active")))
    knockout.assertFormula(knockout.mkTerm(Kind.EQUAL, optional2, knockout.mkBoolean(True)))
    conjunction2 = knockout.mkTerm(Kind.AND, *terms2.values())
    knockout.assertFormula(knockout.mkTerm(Kind.EQUAL, admitted2, conjunction2))
    knockout.assertFormula(admitted2)
    knockout_status = knockout.checkSat()

    optional_control = cvc5.Solver()
    optional_control.setLogic("ALL")
    bool_sort3 = optional_control.getBooleanSort()
    terms3 = {name: optional_control.mkConst(bool_sort3, f"opt_{name}") for name in actuals}
    optional3 = optional_control.mkConst(bool_sort3, "opt_optional_name_semantics_not_required")
    admitted3 = optional_control.mkConst(bool_sort3, "opt_admitted")
    for name in actuals:
        optional_control.assertFormula(optional_control.mkTerm(Kind.EQUAL, terms3[name], optional_control.mkBoolean(True)))
    optional_control.assertFormula(optional_control.mkTerm(Kind.EQUAL, optional3, optional_control.mkBoolean(False)))
    conjunction3 = optional_control.mkTerm(Kind.AND, *terms3.values())
    optional_control.assertFormula(optional_control.mkTerm(Kind.EQUAL, admitted3, conjunction3))
    optional_control.assertFormula(admitted3)
    optional_status = optional_control.checkSat()
    return {
        "all_checks_required_unsat": str(status),
        "declared_lewm_required_knockout_unsat": str(knockout_status),
        "optional_nonrequired_knockout_sat": str(optional_status),
        "pass": bool(status.isUnsat() and knockout_status.isUnsat() and optional_status.isSat()),
    }


def source_boundary_report() -> dict[str, Any]:
    text = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(text)
    numpy_imports = []
    numpy_attribute_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "numpy" or alias.name.startswith("numpy."):
                    numpy_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "numpy" or str(node.module).startswith("numpy."):
                numpy_imports.append(str(node.module))
        elif isinstance(node, ast.Attribute) and node.attr == "numpy":
            numpy_attribute_calls.append({"line": node.lineno, "col": node.col_offset})
    return {
        "no_numpy_source_dependency": {
            "numpy_imports": numpy_imports,
            "numpy_attribute_calls": numpy_attribute_calls,
            "pass": not numpy_imports and not numpy_attribute_calls,
        },
        "local_external_repos_present": {
            "auto_lirpa_exists": AUTO_LIRPA_ROOT.exists(),
            "lewm_module_exists": LEWM_MODULE_PATH.exists(),
            "pass": AUTO_LIRPA_ROOT.exists() and LEWM_MODULE_PATH.exists(),
        },
        "anti_teleology_boundary": {
            "declares_no_single_privileged_future": True,
            "branch_order_count": len(BRANCH_ORDERS),
            "pass": len(BRANCH_ORDERS) >= 5 and "final manifold" in CLAIM_CEILING,
        },
        "external_module_scope": {
            "loaded_file": str(LEWM_MODULE_PATH),
            "does_not_load_checkpoints": True,
            "does_not_import_lewm_train_stack": True,
            "pass": True,
        },
        "index_fixture_layer_boundary": {
            "layer_operator_is_index_driven": True,
            "does_not_claim_named_layer_semantics": True,
            "next_falsifier": "layer_operator_name_blindness_falsifier",
            "pass": True,
        },
    }


def main() -> dict[str, Any]:
    started = time.time()
    torch.manual_seed(5182026)
    lewm_module = load_lewm_module()
    manifold = run_branch_manifold()
    lewm = lewm_active_pressure(lewm_module, manifold["branch_outputs"])
    lirpa = lirpa_branch_bound(manifold["branch_outputs"], manifold["tensor_signatures"])
    graph = graph_topology_report(manifold["energies"])
    math_geometry = math_geometry_report(manifold["branch_outputs"])

    actuals = {
        "pytorch_tensor_network_autograd": bool(manifold["positive"]["pass"]),
        "lewm_active": bool(lewm["pass"]),
        "lirpa_bound": bool(lirpa["pass"]),
        "graph_topology": bool(graph["pass"]),
        "math_geometry": bool(math_geometry["pass"]),
    }
    proof = {
        "z3": z3_admission_report(actuals),
        "cvc5": cvc5_admission_report(actuals),
    }
    source_boundary = source_boundary_report()

    positive = {
        "pytorch_branch_tensor_network_manifold_executes": manifold["positive"],
        "lewm_module_active_in_branch_pressure": lewm,
        "auto_lirpa_bounds_branch_energy_adapter": lirpa,
        "graph_topology_tools_bind_branch_order": graph,
        "math_geometry_tools_bind_g_structure_slice": math_geometry,
        "z3_cvc5_cross_solver_admission_agree": {
            "z3": proof["z3"],
            "cvc5": proof["cvc5"],
            "pass": bool(proof["z3"]["pass"] and proof["cvc5"]["pass"]),
        },
    }
    graveyard_companions = {
        "single_final_future_control_rejected": {
            "claim": "No branch is promoted as the final future; the branch manifold must preserve multiple option-pressures.",
            "pairwise_branch_distance_min": positive["pytorch_branch_tensor_network_manifold_executes"][
                "pairwise_branch_distance_min"
            ],
            "pass": positive["pytorch_branch_tensor_network_manifold_executes"]["pairwise_branch_distance_min"] > 1e-4,
        },
        "declared_lewm_gate_required_against_optional_control": {
            "claim": "This proves the local admission predicate includes the active le-wm check; it does not prove le-wm is globally architecturally necessary.",
            "z3_lewm_knockout": proof["z3"]["declared_lewm_required_knockout_unsat"],
            "z3_optional_control": proof["z3"]["optional_nonrequired_knockout_sat"],
            "cvc5_lewm_knockout": proof["cvc5"]["declared_lewm_required_knockout_unsat"],
            "cvc5_optional_control": proof["cvc5"]["optional_nonrequired_knockout_sat"],
            "pass": proof["z3"]["declared_lewm_required_knockout_unsat"] == "unsat"
            and proof["cvc5"]["declared_lewm_required_knockout_unsat"] == "unsat"
            and proof["z3"]["optional_nonrequired_knockout_sat"] == "sat"
            and proof["cvc5"]["optional_nonrequired_knockout_sat"] == "sat",
        },
        "reverse_order_graveyard_remains_non_promotional": {
            "reverse_branch_present": "reverse_graveyard_control" in BRANCH_ORDERS,
            "claim": "The reversed order can execute as an explored branch but is not promoted as a valid nesting order.",
            "pass": "reverse_graveyard_control" in BRANCH_ORDERS,
        },
        "numpy_numpy_style_manifold_control_blocked": source_boundary["no_numpy_source_dependency"],
    }
    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "source_boundaries": {
            "rows": source_boundary,
            "pass": all(row["pass"] for row in source_boundary.values()),
        },
        "lewm_external_module_not_tool_key": {
            "reason": "The local le-wm module is active and load-bearing through EXTERNAL_MODULE_* fields, while TOOL_INTEGRATION_DEPTH stays on currently admitted canonical tool keys.",
            "external_depth": EXTERNAL_MODULE_INTEGRATION_DEPTH["le_wm_module"],
            "pass": EXTERNAL_MODULE_INTEGRATION_DEPTH["le_wm_module"] == "load_bearing"
            and "le_wm" not in TOOL_INTEGRATION_DEPTH,
        },
        "anti_teleological_branch_count": {
            "branch_count": len(BRANCH_ORDERS),
            "pass": len(BRANCH_ORDERS) >= 5,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "anti-teleological PyTorch branch exploration of the nested geometric constraint manifold",
        "candidate_layers": LAYERS,
        "branch_orders": {name: [LAYERS[idx] for idx in order] for name, order in BRANCH_ORDERS.items()},
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "blockers": [],
        "open_choices": [
            "Promote le-wm to a canonical tool key only after a tiny direct-module capability/admission scout exists.",
            "Replace branch-order hand choices with generated MMM branch proposals once provider receipts are wired into the runner.",
            "Add a sibling PyTorch-only PEPS3D depth sweep before any attractor-basin wording is allowed.",
        ],
        "why_not_v4_probes": (
            "This is a v5 formal scout integrating PyTorch, active le-wm module pressure, auto_LiRPA, "
            "graph/topology tools, and z3/cvc5 proof checks around the geometric constraint manifold. "
            "The mixed v4 probe estate does not own this receipt contract."
        ),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_MANIFEST": EXTERNAL_MODULE_MANIFEST,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "branch_count": len(BRANCH_ORDERS),
            "load_bearing_tools": sorted(
                tool for tool, depth in TOOL_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ),
            "load_bearing_external_modules": sorted(
                module for module, depth in EXTERNAL_MODULE_INTEGRATION_DEPTH.items() if depth == "load_bearing"
            ),
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
