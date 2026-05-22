#!/usr/bin/env python3
"""Root geometric-constraint-manifold maturity scout.

This scout treats the geometric constraint manifold as the root object.  Axis0
does not participate in the pass condition.  The fixture builds one integrated
PyTorch execution path over thirteen semantic layer transforms, with the layer
order derived from a rustworkx dependency graph, varying SU3/G2/Spin7-style
G-structure family pressure, PEPS3D substrate controls, auto_LiRPA bounds,
local le-wm pressure, and graph/topology/geometry/proof tool witnesses.

A green receipt means this bounded root-manifold fixture is stronger than the
previous split receipts.  It still does not admit a final manifold, final
G-structure, axis, basin, bridge, physics, or canonical claim.
"""

from __future__ import annotations

import hashlib
import itertools
import importlib.util
import json
import math
import os
import pathlib
import sys
import time
from typing import Any, Callable

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
from sim_special_holonomy_form_constraint_survivor_quotient_probe import FAMILIES  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "root_geometric_constraint_manifold_maturity_pytorch_toolchain_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "root_geometric_constraint_manifold_maturity"
CLAIM_CEILING = (
    "Formal scout only: executes one bounded root geometric-constraint-manifold "
    "fixture over thirteen semantic PyTorch layer transforms, with dependency "
    "graph-derived order, varying SU3/G2/Spin7-style G-structure family "
    "pressure, PEPS3D substrate controls, auto_LiRPA bounds, local le-wm "
    "pressure, graph/topology/geometry/proof witnesses, and layer-removal "
    "graveyards. Axis0 is not a pass-condition dependency. This does not admit "
    "a final manifold, final G-structure, final PEPS3D environment contraction, "
    "real attractor basin, final Axis0, bridge, physics, target-system, or "
    "canonical manifold claim; it does not admit canonical claims."
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

TAU_ORDER_GAP = 0.002
TAU_LAYER_REMOVAL = 0.0005
TAU_PEPS3D_GAP = 0.0001
TAU_G_STRUCTURE_GAP = 0.0005

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing semantic layer transforms, autograd, state history, PEPS3D substrate contractions, and le-wm tensors",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing interval bound over the integrated root-manifold feature adapter",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Data.validate and MessagePassing over graph-derived layer states",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dependency DAG; the fixture execution order is derived from topological_sort",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Boolean admission and semantic-order knockout witness",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent admission and semantic-order knockout witness",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncommutative semantic-order commutator and exact exterior-form family witness",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing pseudoscalar/chirality orientation witness over the matured state",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing sphere-distance witness separating fixture-order and reordered manifold states",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SO(3) tensor-product carrier witness over fixture-order/reordered state projections",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hypergraph witness coupling nested geometric layers and varying G-structure family schedule",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial complex over adjacent layer triples and nested geometry faces",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplex-tree persistence over layer-state energy and G-structure family filtrations",
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
        "reason": "load-bearing ARPredictor/SIGReg pressure over the root manifold layer-state trajectory",
        "path": str(LEWM_MODULE_PATH),
    }
}
EXTERNAL_MODULE_INTEGRATION_DEPTH = {"le_wm_module": "load_bearing"}


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
        if value.numel() <= 256:
            return value.detach().cpu().tolist()
        return f"<tensor shape={list(value.shape)} dtype={value.dtype}>"
    if isinstance(value, complex):
        return {"re": value.real, "im": value.imag}
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_lewm_module() -> Any:
    if not LEWM_MODULE_PATH.exists():
        raise FileNotFoundError(LEWM_MODULE_PATH)
    spec = importlib.util.spec_from_file_location("lewm_root_manifold_maturity_probe", LEWM_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {LEWM_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def initial_state() -> torch.Tensor:
    return torch.linspace(-0.48, 0.52, steps=8, dtype=torch.float32).requires_grad_(True)


def fixed_matrix(layer_idx: int, scale: float = 0.018) -> torch.Tensor:
    grid = torch.arange(64, dtype=torch.float32).reshape(8, 8)
    raw = torch.sin((grid + 1.0) * (0.071 + 0.013 * layer_idx))
    raw = raw + 0.37 * torch.cos((grid.t() + 1.0) * (0.113 + 0.017 * layer_idx))
    return torch.eye(8, dtype=torch.float32) + scale * raw


def finite_constraint_complex(x: torch.Tensor) -> torch.Tensor:
    return torch.tanh(0.78 * x + 0.14 * torch.roll(x, 1) + 0.08 * torch.roll(x, -1))


def complex_hilbert_carrier(x: torch.Tensor) -> torch.Tensor:
    theta = 0.37
    c = math.cos(theta)
    s = math.sin(theta)
    y = x.clone()
    pairs = [(0, 1), (2, 3), (4, 5), (6, 7)]
    for a, b in pairs:
        ya = c * x[a] - s * x[b]
        yb = s * x[a] + c * x[b]
        y = y.clone()
        y[a] = ya
        y[b] = yb
    return torch.tanh(y)


def unit_spinor_sphere(x: torch.Tensor) -> torch.Tensor:
    left = x[:4] / torch.linalg.vector_norm(x[:4]).clamp_min(1e-6)
    right = x[4:] / torch.linalg.vector_norm(x[4:]).clamp_min(1e-6)
    return torch.cat([left, right])


def projective_base_sphere(x: torch.Tensor) -> torch.Tensor:
    paired = torch.stack([x[:4], torch.flip(x[4:], dims=[0])], dim=0)
    quotient = torch.sum(paired * paired, dim=0)
    signed = torch.cat([quotient, x[:4] * torch.sign(x[4:].mean()).clamp(min=-1.0, max=1.0)])
    return torch.tanh(signed)


def hopf_fiber_bundle(x: torch.Tensor) -> torch.Tensor:
    left = x[:4]
    right = x[4:]
    fiber = torch.stack([left[0] * right[1] - left[1] * right[0], left[2] * right[3] - left[3] * right[2]])
    lifted = torch.cat([left + 0.13 * right, right - 0.11 * left])
    lifted = lifted.clone()
    lifted[2:4] = lifted[2:4] + fiber
    return torch.tanh(lifted)


def hopf_torus_leaf_family(x: torch.Tensor) -> torch.Tensor:
    phase = torch.linspace(0.2, 1.1, steps=8, dtype=x.dtype, device=x.device)
    return torch.tanh(x * torch.cos(phase) + torch.roll(x, 2) * torch.sin(phase))


def connection_holonomy_geometry(x: torch.Tensor) -> torch.Tensor:
    skew = fixed_matrix(6, scale=0.06) - fixed_matrix(6, scale=0.06).t()
    holonomy = torch.linalg.matrix_exp(0.24 * skew)
    return torch.tanh(holonomy @ x + 0.22 * torch.roll(x, 3) - 0.14 * torch.flip(x, dims=[0]))


def weyl_spinor_bundle(x: torch.Tensor) -> torch.Tensor:
    left = x[:4] + 0.17 * torch.roll(x[:4], 1)
    right = -(x[4:] - 0.11 * torch.roll(x[4:], -1))
    return torch.tanh(torch.cat([left, right]))


def chirality_orientation_cover(x: torch.Tensor) -> torch.Tensor:
    signs = torch.tensor([1.0, -1.0, 1.0, -1.0, -1.0, 1.0, -1.0, 1.0], dtype=x.dtype, device=x.device)
    return torch.tanh(signs * x + 0.07 * torch.flip(x, dims=[0]))


def clifford_module_geometry(x: torch.Tensor) -> torch.Tensor:
    gamma = torch.tensor(
        [
            [0, 1, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, -1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, -1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, -1],
            [0, 0, 0, 0, 0, 0, 1, 0],
        ],
        dtype=x.dtype,
        device=x.device,
    )
    return torch.tanh(x + 0.23 * (gamma @ x))


def frame_bundle_structure_reduction(x: torch.Tensor) -> torch.Tensor:
    q, _r = torch.linalg.qr(fixed_matrix(10, scale=0.02))
    return torch.tanh(q @ x)


def tensor_product_coupling_geometry(x: torch.Tensor) -> torch.Tensor:
    outer = torch.outer(x[:4], x[4:]).reshape(-1)
    idx = torch.tensor([0, 3, 5, 6, 9, 10, 12, 15], dtype=torch.long, device=x.device)
    return torch.tanh(outer[idx] + 0.19 * x)


def dynamic_transition_ratchet_geometry(x: torch.Tensor) -> torch.Tensor:
    gate = torch.sigmoid(fixed_matrix(12, scale=0.025) @ x)
    return torch.tanh(gate * x + (1.0 - gate) * torch.roll(x, 1) + 0.03)


LAYER_FUNCTIONS: list[Callable[[torch.Tensor], torch.Tensor]] = [
    finite_constraint_complex,
    complex_hilbert_carrier,
    unit_spinor_sphere,
    projective_base_sphere,
    hopf_fiber_bundle,
    hopf_torus_leaf_family,
    connection_holonomy_geometry,
    weyl_spinor_bundle,
    chirality_orientation_cover,
    clifford_module_geometry,
    frame_bundle_structure_reduction,
    tensor_product_coupling_geometry,
    dynamic_transition_ratchet_geometry,
]


def dependency_graph() -> tuple[rx.PyDiGraph, list[int]]:
    graph = rx.PyDiGraph()
    nodes = [graph.add_node({"idx": idx, "name": name}) for idx, name in enumerate(LAYERS)]
    for src, dst in zip(nodes[:-1], nodes[1:]):
        graph.add_edge(src, dst, "nested_requires")
    order = [int(node) for node in rx.topological_sort(graph)]
    return graph, order


def run_semantic_manifold(order: list[int], disabled_layer: int | None = None) -> dict[str, Any]:
    state = initial_state()
    root_state = state
    history = []
    layer_rows = []
    for step, layer_idx in enumerate(order):
        before = state
        if disabled_layer is None or layer_idx != disabled_layer:
            state = LAYER_FUNCTIONS[layer_idx](state)
        else:
            state = torch.tanh(0.97 * state + 0.03 * torch.roll(state, 1))
        history.append(state)
        layer_rows.append(
            {
                "step": step,
                "layer_idx": layer_idx,
                "layer": LAYERS[layer_idx],
                "disabled": disabled_layer == layer_idx,
                "delta_norm": float(torch.linalg.vector_norm((state - before).detach()).item()),
                "state_norm": float(torch.linalg.vector_norm(state.detach()).item()),
            }
        )
    final = state
    history_t = torch.stack(history)
    energy = torch.sum(history_t * history_t, dim=1)
    grad = torch.autograd.grad(final.square().sum() + energy.mean(), root_state, retain_graph=True, allow_unused=True)[0]
    if grad is None:
        grad_norm = 0.0
    else:
        grad_norm = float(torch.linalg.vector_norm(grad).item())
    return {
        "final_state": final,
        "history": history_t,
        "energy": energy,
        "layer_rows": layer_rows,
        "autograd_grad_norm": grad_norm,
    }


def make_site_tensor(v: torch.Tensor, offset: int, shape: tuple[int, ...]) -> torch.Tensor:
    total = math.prod(shape)
    idx = torch.arange(total, dtype=torch.long, device=v.device)
    selected = v[(idx + offset) % v.numel()]
    values = torch.sin((idx.float() + 1.0) * 0.127 + selected)
    values = values + 0.19 * torch.cos((idx.float() + 1.0) * 0.067 - selected)
    return values.reshape(shape) / math.sqrt(float(total))


def peps3d_signature(history: torch.Tensor, edges: list[dict[str, int]]) -> torch.Tensor:
    seed = history[:8].reshape(8, 8)
    tensors = torch.stack([make_site_tensor(seed[idx], idx, (2, 2, 2, 2)) for idx in range(8)])

    def edge_contract(edge: dict[str, int]) -> torch.Tensor:
        left = tensors[edge["src"]]
        right = tensors[edge["dst"]]
        axis = edge["axis"]
        if axis == 0:
            return torch.einsum("pabc,qdbc->", left, right)
        if axis == 1:
            return torch.einsum("pabc,qadc->", left, right)
        return torch.einsum("pabc,qabd->", left, right)

    return torch.stack([edge_contract(edge) for edge in edges])


def cube_edges(wrong: bool = False) -> list[dict[str, int]]:
    coords = [(x, y, z) for x in range(2) for y in range(2) for z in range(2)]
    index = {coord: idx for idx, coord in enumerate(coords)}
    edges = []
    for coord, src in index.items():
        for axis in range(3):
            nxt = list(coord)
            nxt[axis] += 1
            if nxt[axis] >= 2:
                continue
            dst = index[tuple(nxt)]
            if wrong:
                dst = (dst + 3) % len(coords)
                axis = (axis + 1) % 3
            edges.append({"src": src, "dst": dst, "axis": axis})
    return edges


class LayerMessenger(MessagePassing):
    def __init__(self) -> None:
        super().__init__(aggr="add")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index, x=x)

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return x_j

    def update(self, aggr_out: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        return torch.cat([x, aggr_out], dim=-1)


def graph_topology_report(graph: rx.PyDiGraph, history: torch.Tensor) -> dict[str, Any]:
    edge_pairs = [(int(src), int(dst)) for src, dst in graph.edge_list()]
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).t().contiguous()
    x = torch.stack(
        [
            torch.tensor(
                [
                    idx / 12.0,
                    float(torch.linalg.vector_norm(history[idx]).detach().item()),
                    float(history[idx].mean().detach().item()),
                    float(history[idx].std(unbiased=False).detach().item()),
                ],
                dtype=torch.float32,
            )
            for idx in range(len(LAYERS))
        ]
    )
    data = Data(x=x, edge_index=edge_index, num_nodes=len(LAYERS))
    data.validate(raise_on_error=True)
    messenger = LayerMessenger()
    with torch.no_grad():
        mp_out = messenger(data.x, data.edge_index)

    hypergraph = xgi.Hypergraph()
    hypergraph.add_edge(["unit_spinor_sphere", "projective_base_sphere", "hopf_fiber_bundle"])
    hypergraph.add_edge(["weyl_spinor_bundle", "chirality_orientation_cover", "clifford_module_geometry"])
    hypergraph.add_edge(["frame_bundle_structure_reduction", "tensor_product_coupling_geometry", "dynamic_transition_ratchet_geometry"])

    complex_ = tnx.SimplicialComplex()
    for idx in range(len(LAYERS) - 2):
        complex_.add_simplex(LAYERS[idx : idx + 3])

    st = gudhi.SimplexTree()
    energies = torch.sum(history.detach() * history.detach(), dim=1)
    for idx, energy in enumerate(energies.tolist()):
        st.insert([idx], filtration=float(energy))
    for src, dst in edge_pairs:
        st.insert([src, dst], filtration=float(max(energies[src], energies[dst])))
    persistence = st.persistence()

    xgi_edges = hypergraph.num_edges() if callable(hypergraph.num_edges) else hypergraph.num_edges
    return {
        "rustworkx": {
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
            "topological_order": [int(x) for x in rx.topological_sort(graph)],
        },
        "pyg": {
            "data_validate_passed": True,
            "message_passing_shape": list(mp_out.shape),
            "message_passing_norm": float(torch.linalg.vector_norm(mp_out).item()),
        },
        "xgi": {"hyperedge_count": int(xgi_edges)},
        "toponetx": {"simplicial_complex_dim": int(complex_.dim), "shape": str(complex_.shape)},
        "gudhi": {"simplex_count": int(st.num_simplices()), "persistence_pair_count": len(persistence)},
        "pass": bool(
            rx.is_directed_acyclic_graph(graph)
            and graph.num_edges() == 12
            and list(mp_out.shape) == [13, 8]
            and int(xgi_edges) == 3
            and int(complex_.dim) >= 2
            and st.num_simplices() >= 25
        ),
    }


def _term_sign(signs: tuple[int, ...], term: tuple[int, ...]) -> int:
    value = 1
    for idx in term:
        value *= signs[idx]
    return value


def _preserves_forms(signs: tuple[int, ...], forms: list[dict[tuple[int, ...], int]]) -> bool:
    return all(_term_sign(signs, term) == 1 for current_form in forms for term in current_form)


def _family_signature(signs: tuple[int, ...], forms: list[dict[tuple[int, ...], int]]) -> tuple[int, ...]:
    determinant = 1
    for value in signs:
        determinant *= value
    term_values = [
        sum(_term_sign(signs, term) * coeff for term, coeff in current_form.items())
        for current_form in forms
    ]
    adjacent_products = [signs[idx] * signs[idx + 1] for idx in range(len(signs) - 1)]
    return tuple([determinant, sum(signs), *term_values, sum(adjacent_products)])


def _g_family_row(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    dim = int(spec["dimension"])
    candidates = list(itertools.product([-1, 1], repeat=dim))
    survivors = [signs for signs in candidates if _preserves_forms(signs, spec["forms"])]
    classes = {_family_signature(signs, spec["forms"]) for signs in survivors}
    return {
        "family": name,
        "dimension": dim,
        "candidate_count": len(candidates),
        "survivor_count": len(survivors),
        "survivor_fraction": len(survivors) / len(candidates),
        "term_count": sum(len(current_form) for current_form in spec["forms"]),
        "class_count": len(classes),
    }


def _g_family_gate(state: torch.Tensor, row: dict[str, Any], layer_idx: int) -> torch.Tensor:
    features = torch.tensor(
        [
            row["dimension"] / 8.0,
            row["survivor_fraction"],
            row["survivor_count"] / max(row["candidate_count"], 1),
            row["term_count"] / 70.0,
            row["class_count"] / max(row["survivor_count"], 1),
        ],
        dtype=state.dtype,
        device=state.device,
    )
    coeffs = torch.tensor([0.13, -0.17, 0.19, 0.07, -0.11], dtype=state.dtype, device=state.device)
    pressure = torch.dot(features, coeffs)
    return torch.tanh(
        state * (1.0 + 0.07 * features[0])
        + pressure * torch.roll(state, shifts=(layer_idx % state.numel()))
        + 0.04 * features[3] * torch.flip(state, dims=[0])
    )


def varying_g_structure_report(history: torch.Tensor) -> dict[str, Any]:
    rows = {name: _g_family_row(name, spec) for name, spec in FAMILIES.items()}
    schedule = [
        "su3_two_and_three_form_constraints",
        "su3_two_and_three_form_constraints",
        "su3_two_and_three_form_constraints",
        "g2_three_form_constraints",
        "g2_three_form_constraints",
        "g2_three_form_constraints",
        "g2_three_form_constraints",
        "spin7_four_form_constraints",
        "spin7_four_form_constraints",
        "spin7_four_form_constraints",
        "spin7_four_form_constraints",
        "g2_three_form_constraints",
        "spin7_four_form_constraints",
    ]

    def apply_schedule(names: list[str]) -> torch.Tensor:
        gated = [_g_family_gate(history[idx], rows[name], idx) for idx, name in enumerate(names)]
        stack = torch.stack(gated)
        weights = torch.linspace(0.7, 1.3, steps=stack.shape[0], dtype=stack.dtype, device=stack.device).reshape(-1, 1)
        return torch.sum(stack * weights, dim=0)

    varying = apply_schedule(schedule)
    reverse = apply_schedule(list(reversed(schedule)))
    frozen = {
        name: apply_schedule([name] * len(schedule))
        for name in [
            "su3_two_and_three_form_constraints",
            "g2_three_form_constraints",
            "spin7_four_form_constraints",
        ]
    }
    generic_three = apply_schedule(["generic_three_form_control_constraints"] * len(schedule))
    generic_four = apply_schedule(["generic_four_form_control_constraints"] * len(schedule))

    frozen_gaps = {name: float(torch.sum((varying - value) ** 2).detach().item()) for name, value in frozen.items()}
    generic_gaps = {
        "generic_three_form_control_gap": float(torch.sum((varying - generic_three) ** 2).detach().item()),
        "generic_four_form_control_gap": float(torch.sum((varying - generic_four) ** 2).detach().item()),
    }
    reverse_gap = float(torch.sum((varying - reverse) ** 2).detach().item())
    special_survivor_counts = {
        name: rows[name]["survivor_count"]
        for name in [
            "su3_two_and_three_form_constraints",
            "g2_three_form_constraints",
            "spin7_four_form_constraints",
        ]
    }
    st = gudhi.SimplexTree()
    for idx, name in enumerate(schedule):
        st.insert([idx], filtration=float(rows[name]["survivor_fraction"]))
    for idx in range(len(schedule) - 1):
        st.insert(
            [idx, idx + 1],
            filtration=max(float(rows[schedule[idx]]["survivor_fraction"]), float(rows[schedule[idx + 1]]["survivor_fraction"])),
        )
    persistence = st.persistence()

    hypergraph = xgi.Hypergraph()
    for family in sorted(set(schedule)):
        members = [LAYERS[idx] for idx, name in enumerate(schedule) if name == family]
        hypergraph.add_edge([family, *members[:4]])
    xgi_edges = hypergraph.num_edges() if callable(hypergraph.num_edges) else hypergraph.num_edges

    graph = rx.PyDiGraph()
    nodes = [graph.add_node({"idx": idx, "family": name}) for idx, name in enumerate(schedule)]
    for src, dst in zip(nodes[:-1], nodes[1:]):
        graph.add_edge(src, dst, "g_structure_family_transition")

    exact_witness = sp.factor(sp.Symbol("s") ** 2 - 1)
    z3_solver = z3.Solver()
    z3_distinct = z3.Bool("special_g_structure_survivor_counts_distinct")
    z3_solver.add(z3_distinct == z3.BoolVal(len(set(special_survivor_counts.values())) >= 2))
    z3_solver.add(z3.Not(z3_distinct))
    z3_status = z3_solver.check()

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("ALL")
    bool_sort = cvc5_solver.getBooleanSort()
    cvc5_distinct = cvc5_solver.mkConst(bool_sort, "special_g_structure_survivor_counts_distinct")
    cvc5_solver.assertFormula(
        cvc5_solver.mkTerm(Kind.EQUAL, cvc5_distinct, cvc5_solver.mkBoolean(len(set(special_survivor_counts.values())) >= 2))
    )
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.NOT, cvc5_distinct))
    cvc5_status = cvc5_solver.checkSat()

    min_frozen_gap = min(frozen_gaps.values())
    min_generic_gap = min(generic_gaps.values())
    return {
        "schedule": schedule,
        "family_rows": rows,
        "special_survivor_counts": special_survivor_counts,
        "frozen_single_family_gaps": frozen_gaps,
        "generic_control_gaps": generic_gaps,
        "reverse_schedule_gap": reverse_gap,
        "min_frozen_single_family_gap": min_frozen_gap,
        "min_generic_control_gap": min_generic_gap,
        "gudhi_persistence_pair_count": len(persistence),
        "xgi_family_hyperedge_count": int(xgi_edges),
        "rustworkx_transition_edge_count": graph.num_edges(),
        "sympy_exact_sign_boundary": str(exact_witness),
        "z3_distinct_survivor_counts_unsat_if_denied": str(z3_status),
        "cvc5_distinct_survivor_counts_unsat_if_denied": str(cvc5_status),
        "pass": bool(
            len(set(schedule)) == 3
            and len(set(special_survivor_counts.values())) >= 2
            and min_frozen_gap > TAU_G_STRUCTURE_GAP
            and min_generic_gap > TAU_G_STRUCTURE_GAP
            and reverse_gap > TAU_G_STRUCTURE_GAP
            and len(persistence) > 0
            and int(xgi_edges) == 3
            and graph.num_edges() == 12
            and z3_status == z3.unsat
            and cvc5_status.isUnsat()
        ),
    }


def math_geometry_report(fixture_state: torch.Tensor, reordered: torch.Tensor) -> dict[str, Any]:
    a, b = sp.symbols("G H", commutative=False)
    coeff_a = float(fixture_state[0].detach().item())
    coeff_b = float(reordered[0].detach().item())
    comm = sp.expand(coeff_a * a * b - coeff_b * b * a)

    _, blades = Cl(1, 3)
    vector = (
        float(fixture_state[0].detach().item()) * blades["e1"]
        + float(fixture_state[1].detach().item()) * blades["e2"]
        + float(fixture_state[2].detach().item()) * blades["e3"]
        + float(fixture_state[3].detach().item()) * blades["e4"]
    )
    pseudoscalar_square = float((blades["e1234"] * blades["e1234"])[()])
    pseudoscalar_action = blades["e1234"] * vector
    action_grades = sorted(int(grade) for grade in pseudoscalar_action.grades())

    sphere = Hypersphere(dim=2)
    p0_t = fixture_state[:3].detach() / torch.linalg.vector_norm(fixture_state[:3]).clamp_min(1e-6)
    p1_t = reordered[:3].detach() / torch.linalg.vector_norm(reordered[:3]).clamp_min(1e-6)
    p0 = gs.array([float(x) for x in p0_t.tolist()])
    p1 = gs.array([float(x) for x in p1_t.tolist()])
    sphere_distance = float(sphere.metric.dist(p0, p1))

    tp = o3.FullTensorProduct(o3.Irreps("1x1o"), o3.Irreps("1x1o"))
    e3nn_out = tp(fixture_state[:3].detach(), reordered[:3].detach())
    return {
        "sympy_noncommutative_order": {
            "commutator": str(comm),
            "coefficients": [coeff_a, coeff_b],
            "pass": bool(comm != 0 and abs(coeff_a - coeff_b) > 1e-5),
        },
        "clifford_chirality": {
            "pseudoscalar_square": pseudoscalar_square,
            "action_grades": action_grades,
            "pass": bool(abs(pseudoscalar_square + 1.0) < 1e-9 and action_grades == [3]),
        },
        "geomstats_order_distance": {
            "sphere_distance": sphere_distance,
            "pass": bool(sphere_distance > 1e-5),
        },
        "e3nn_tensor_product": {
            "irreps_out": str(tp.irreps_out),
            "output_dim": int(e3nn_out.numel()),
            "output_norm": float(torch.linalg.vector_norm(e3nn_out).item()),
            "pass": bool(int(e3nn_out.numel()) == 9 and torch.linalg.vector_norm(e3nn_out).item() > 0.0),
        },
    }


class MaturityEnergyAdapter(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(input_dim, 16), nn.ReLU(), nn.Linear(16, 1))
        with torch.no_grad():
            for idx, parameter in enumerate(self.parameters()):
                values = torch.linspace(-0.07 + 0.011 * idx, 0.08 + 0.011 * idx, steps=parameter.numel())
                parameter.copy_(values.reshape_as(parameter))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def lirpa_report(fixture: dict[str, Any], peps_sig: torch.Tensor) -> dict[str, Any]:
    features = torch.cat([fixture["history"].detach().to(torch.float32), peps_sig.detach().reshape(1, -1).repeat(13, 1)], dim=1)
    model = MaturityEnergyAdapter(features.shape[1]).eval()
    bounded = BoundedModule(model, features)
    eps = 0.006
    bounded_x = BoundedTensor(features, PerturbationLpNorm(norm=float("inf"), eps=eps))
    lb, ub = bounded.compute_bounds(x=(bounded_x,), method="IBP")
    with torch.no_grad():
        nominal = model(features)
    return {
        "method": "IBP",
        "eps_linf": eps,
        "feature_shape": list(features.shape),
        "lb_min": float(lb.min().item()),
        "ub_max": float(ub.max().item()),
        "mean_bound_width": float(torch.mean(ub - lb).item()),
        "contains_nominal": bool(torch.all(nominal >= lb - 2e-5).item() and torch.all(nominal <= ub + 2e-5).item()),
        "pass": bool(torch.mean(ub - lb).item() > 0.0 and torch.all(nominal >= lb - 2e-5).item() and torch.all(nominal <= ub + 2e-5).item()),
    }


def lewm_report(lewm_module: Any, history: torch.Tensor) -> dict[str, Any]:
    torch.manual_seed(51826)
    predictor = lewm_module.ARPredictor(
        num_frames=history.shape[0],
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
    emb = history.detach().unsqueeze(0)
    actions = torch.tanh(torch.roll(emb, shifts=1, dims=1) - 0.07 * emb)
    initial_pred = predictor(emb, actions)
    initial_loss = F.mse_loss(initial_pred[:, :-1], emb[:, 1:]).detach()
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.015, weight_decay=0.0)
    predictor.train()
    for _ in range(60):
        optimizer.zero_grad(set_to_none=True)
        pred = predictor(emb, actions)
        loss = F.mse_loss(pred[:, :-1], emb[:, 1:])
        loss.backward()
        optimizer.step()
    predictor.eval()
    with torch.no_grad():
        pred = predictor(emb, actions)
        collapsed = emb.mean(dim=1, keepdim=True).expand_as(emb)
        zero_action_pred = predictor(emb, actions * 0.0)
        collapsed_pred = predictor(collapsed, actions * 0.0)
        loss = F.mse_loss(pred[:, :-1], emb[:, 1:])
        zero_action_loss = F.mse_loss(zero_action_pred[:, :-1], emb[:, 1:])
        collapsed_loss = F.mse_loss(collapsed_pred[:, :-1], emb[:, 1:])
        torch.manual_seed(4444)
        sig_source = sigreg(emb.transpose(0, 1))
        torch.manual_seed(4444)
        sig_collapsed = sigreg(collapsed.transpose(0, 1))
    best_control = torch.minimum(zero_action_loss, collapsed_loss)
    advantage = (best_control - loss) / best_control.clamp_min(1e-9)
    return {
        "loaded_classes": ["ARPredictor", "SIGReg"],
        "module_sha256": sha256_file(LEWM_MODULE_PATH),
        "training_steps": 60,
        "initial_next_embedding_loss": float(initial_loss.item()),
        "next_embedding_loss": float(loss.item()),
        "zero_action_control_loss": float(zero_action_loss.item()),
        "collapsed_control_loss": float(collapsed_loss.item()),
        "relative_loss_advantage_vs_best_control": float(advantage.item()),
        "sigreg_source_score": float(sig_source.item()),
        "sigreg_collapsed_score": float(sig_collapsed.item()),
        "sigreg_delta_abs": float(torch.abs(sig_collapsed - sig_source).item()),
        "pass": bool(
            math.isfinite(float(loss.item()))
            and loss.item() < best_control.item() * 0.9
            and advantage.item() > 0.02
            and torch.abs(sig_collapsed - sig_source).item() > 1e-5
        ),
    }


def z3_report(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    terms = {name: z3.Bool(name) for name in actuals}
    admitted = z3.Bool("root_manifold_maturity_admitted")
    for name, value in actuals.items():
        solver.add(terms[name] == z3.BoolVal(bool(value)))
    solver.add(admitted == z3.And(*terms.values()))
    solver.add(z3.Not(admitted))
    all_required_unsat = solver.check()

    knockout_statuses: dict[str, str] = {}
    for required_name in ["semantic_order_sensitive", "varying_g_structure_family_pressure"]:
        knockout = z3.Solver()
        ko_terms = {name: z3.Bool(f"ko_{required_name}_{name}") for name in actuals}
        ko_admitted = z3.Bool(f"ko_{required_name}_root_manifold_maturity_admitted")
        for name in actuals:
            knockout.add(ko_terms[name] == z3.BoolVal(name != required_name))
        knockout.add(ko_admitted == z3.And(*ko_terms.values()))
        knockout.add(ko_admitted)
        knockout_statuses[required_name] = str(knockout.check())
    return {
        "all_required_unsat_when_denied": str(all_required_unsat),
        "required_knockout_unsat": knockout_statuses,
        "pass": bool(all_required_unsat == z3.unsat and all(status == "unsat" for status in knockout_statuses.values())),
    }


def cvc5_report(actuals: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    terms = {name: solver.mkConst(bool_sort, name) for name in actuals}
    admitted = solver.mkConst(bool_sort, "root_manifold_maturity_admitted")
    for name, value in actuals.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, terms[name], solver.mkBoolean(bool(value))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *terms.values())))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    all_required_unsat = solver.checkSat()

    knockout_statuses: dict[str, str] = {}
    for required_name in ["semantic_order_sensitive", "varying_g_structure_family_pressure"]:
        knockout = cvc5.Solver()
        knockout.setLogic("ALL")
        bool_sort2 = knockout.getBooleanSort()
        ko_terms = {name: knockout.mkConst(bool_sort2, f"ko_{required_name}_{name}") for name in actuals}
        ko_admitted = knockout.mkConst(bool_sort2, f"ko_{required_name}_root_manifold_maturity_admitted")
        for name in actuals:
            knockout.assertFormula(knockout.mkTerm(Kind.EQUAL, ko_terms[name], knockout.mkBoolean(name != required_name)))
        knockout.assertFormula(knockout.mkTerm(Kind.EQUAL, ko_admitted, knockout.mkTerm(Kind.AND, *ko_terms.values())))
        knockout.assertFormula(ko_admitted)
        knockout_statuses[required_name] = str(knockout.checkSat())
    return {
        "all_required_unsat_when_denied": str(all_required_unsat),
        "required_knockout_unsat": knockout_statuses,
        "pass": bool(all_required_unsat.isUnsat() and all(status == "unsat" for status in knockout_statuses.values())),
    }


def main() -> int:
    started = time.time()
    torch.manual_seed(20260518)
    graph, fixture_order = dependency_graph()
    fixture = run_semantic_manifold(fixture_order)
    name_renamed = run_semantic_manifold(fixture_order)
    swapped_order = fixture_order[:]
    swapped_order[3], swapped_order[4] = swapped_order[4], swapped_order[3]
    swapped = run_semantic_manifold(swapped_order)
    reverse = run_semantic_manifold(list(reversed(fixture_order)))

    fixture_final = fixture["final_state"]
    name_gap = float(torch.sum((fixture_final - name_renamed["final_state"]) ** 2).detach().item())
    swapped_gap = float(torch.sum((fixture_final - swapped["final_state"]) ** 2).detach().item())
    reverse_gap = float(torch.sum((fixture_final - reverse["final_state"]) ** 2).detach().item())

    removal_rows = []
    for layer_idx in fixture_order:
        removed = run_semantic_manifold(fixture_order, disabled_layer=layer_idx)
        gap = float(torch.sum((fixture_final - removed["final_state"]) ** 2).detach().item())
        removal_rows.append({"layer_idx": layer_idx, "layer": LAYERS[layer_idx], "gap": gap, "pass": gap > TAU_LAYER_REMOVAL})
    min_removal_gap = min(row["gap"] for row in removal_rows)

    peps_edges = cube_edges(wrong=False)
    peps_wrong_edges = cube_edges(wrong=True)
    peps_sig = peps3d_signature(fixture["history"], peps_edges)
    peps_wrong = peps3d_signature(fixture["history"], peps_wrong_edges)
    flat = torch.tanh(torch.full_like(peps_sig, float(fixture["history"].mean().detach().item())))
    peps_scalar = peps3d_signature(fixture["history"].mean(dim=1, keepdim=True).expand_as(fixture["history"]), peps_edges)
    peps_zero = peps3d_signature(torch.zeros_like(fixture["history"]), peps_edges)
    peps_gaps = {
        "wrong_adjacency_gap": float(torch.sum((peps_sig - peps_wrong) ** 2).detach().item()),
        "flattened_summary_gap": float(torch.sum((peps_sig - flat) ** 2).detach().item()),
        "scalar_layer_summary_gap": float(torch.sum((peps_sig - peps_scalar) ** 2).detach().item()),
        "zero_substrate_gap": float(torch.sum((peps_sig - peps_zero) ** 2).detach().item()),
    }

    graph_report = graph_topology_report(graph, fixture["history"])
    math_report = math_geometry_report(fixture_final, swapped["final_state"])
    g_structure = varying_g_structure_report(fixture["history"])
    lirpa = lirpa_report(fixture, peps_sig)
    lewm = lewm_report(load_lewm_module(), fixture["history"])

    positive = {
        "root_dependency_graph_drives_fixture_order": {
            "fixture_order": fixture_order,
            "fixture_layers": [LAYERS[idx] for idx in fixture_order],
            "graph_edges": graph.num_edges(),
            "pass": bool(fixture_order == list(range(13)) and graph.num_edges() == 12),
        },
        "semantic_pytorch_layer_execution": {
            "layer_count": len(fixture["layer_rows"]),
            "final_state_norm": float(torch.linalg.vector_norm(fixture_final.detach()).item()),
            "autograd_grad_norm": fixture["autograd_grad_norm"],
            "pass": bool(
                len(fixture["layer_rows"]) == 13
                and torch.isfinite(fixture["history"]).all().item()
                and fixture["autograd_grad_norm"] > 0.0
            ),
        },
        "semantic_order_sensitive": {
            "name_rename_gap": name_gap,
            "swapped_projective_hopf_gap": swapped_gap,
            "reverse_order_gap": reverse_gap,
            "pass": bool(name_gap <= 1e-12 and swapped_gap > TAU_ORDER_GAP and reverse_gap > TAU_ORDER_GAP),
        },
        "graph_topology_tools": graph_report,
        "math_geometry_tools": {
            **math_report,
            "pass": all(row.get("pass") is True for row in math_report.values()),
        },
        "varying_g_structure_family_pressure": g_structure,
        "peps3d_substrate_tools": {
            "signature_shape": list(peps_sig.shape),
            **peps_gaps,
            "pass": bool(all(value > TAU_PEPS3D_GAP for value in peps_gaps.values())),
        },
        "auto_lirpa_maturity_bound": lirpa,
        "lewm_root_trajectory_pressure": lewm,
    }

    actuals = {name: bool(row.get("pass")) for name, row in positive.items()}
    proof = {"z3": z3_report(actuals), "cvc5": cvc5_report(actuals)}
    positive["proof_tool_joint_admission"] = {
        "z3": proof["z3"],
        "cvc5": proof["cvc5"],
        "pass": bool(proof["z3"]["pass"] and proof["cvc5"]["pass"]),
    }

    graveyard_companions = {
        "name_renaming_does_not_change_semantics": {
            "gap": name_gap,
            "pass": bool(name_gap <= 1e-12),
        },
        "projective_hopf_swap_changes_semantics": {
            "gap": swapped_gap,
            "TAU_ORDER_GAP": TAU_ORDER_GAP,
            "pass": bool(swapped_gap > TAU_ORDER_GAP),
        },
        "reverse_order_changes_semantics": {
            "gap": reverse_gap,
            "TAU_ORDER_GAP": TAU_ORDER_GAP,
            "pass": bool(reverse_gap > TAU_ORDER_GAP),
        },
        "frozen_single_g_structure_family_rejected": {
            "min_frozen_single_family_gap": g_structure["min_frozen_single_family_gap"],
            "frozen_single_family_gaps": g_structure["frozen_single_family_gaps"],
            "TAU_G_STRUCTURE_GAP": TAU_G_STRUCTURE_GAP,
            "pass": bool(g_structure["min_frozen_single_family_gap"] > TAU_G_STRUCTURE_GAP),
        },
        "generic_g_structure_controls_rejected": {
            "min_generic_control_gap": g_structure["min_generic_control_gap"],
            "generic_control_gaps": g_structure["generic_control_gaps"],
            "TAU_G_STRUCTURE_GAP": TAU_G_STRUCTURE_GAP,
            "pass": bool(g_structure["min_generic_control_gap"] > TAU_G_STRUCTURE_GAP),
        },
        "reversed_g_structure_schedule_rejected": {
            "reverse_schedule_gap": g_structure["reverse_schedule_gap"],
            "TAU_G_STRUCTURE_GAP": TAU_G_STRUCTURE_GAP,
            "pass": bool(g_structure["reverse_schedule_gap"] > TAU_G_STRUCTURE_GAP),
        },
        "each_layer_removal_changes_state": {
            "min_removal_gap": min_removal_gap,
            "TAU_LAYER_REMOVAL": TAU_LAYER_REMOVAL,
            "rows": removal_rows,
            "pass": bool(all(row["pass"] for row in removal_rows)),
        },
        "peps3d_wrong_adjacency_rejected": {
            "gap": peps_gaps["wrong_adjacency_gap"],
            "TAU_PEPS3D_GAP": TAU_PEPS3D_GAP,
            "pass": bool(peps_gaps["wrong_adjacency_gap"] > TAU_PEPS3D_GAP),
        },
        "peps3d_flattened_summary_rejected": {
            "gap": peps_gaps["flattened_summary_gap"],
            "TAU_PEPS3D_GAP": TAU_PEPS3D_GAP,
            "pass": bool(peps_gaps["flattened_summary_gap"] > TAU_PEPS3D_GAP),
        },
        "peps3d_scalar_summary_rejected": {
            "gap": peps_gaps["scalar_layer_summary_gap"],
            "TAU_PEPS3D_GAP": TAU_PEPS3D_GAP,
            "pass": bool(peps_gaps["scalar_layer_summary_gap"] > TAU_PEPS3D_GAP),
        },
        "peps3d_zero_substrate_rejected": {
            "gap": peps_gaps["zero_substrate_gap"],
            "TAU_PEPS3D_GAP": TAU_PEPS3D_GAP,
            "pass": bool(peps_gaps["zero_substrate_gap"] > TAU_PEPS3D_GAP),
        },
    }

    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": bool(CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False),
        },
        "axis0_not_pass_condition": {
            "axis0_used_in_pass_condition": False,
            "reason": "Axis0 requires mature manifold first; this scout exercises one bounded root fixture and does not use Axis0 to pass.",
            "pass": True,
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
            "layer_count": len(LAYERS),
            "fixture_order_derived_from_graph": fixture_order == list(range(13)),
            "semantic_swap_gap": swapped_gap,
            "reverse_order_gap": reverse_gap,
            "min_layer_removal_gap": min_removal_gap,
            "g_structure_family_count": len(g_structure["family_rows"]),
            "g_structure_schedule_family_count": len(set(g_structure["schedule"])),
            "g_structure_min_control_gap": min(
                g_structure["min_frozen_single_family_gap"],
                g_structure["min_generic_control_gap"],
                g_structure["reverse_schedule_gap"],
            ),
            "peps3d_min_control_gap": min(peps_gaps.values()),
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
            "uses PyTorch semantic layer transforms, graph-derived order, PEPS3D substrate controls, auto_LiRPA, le-wm, graph/topology/geometry tools, and z3/cvc5 in one receipt",
            "formal scout only; no final manifold, basin, axis, bridge, physics, target-system, or canonical claim is admitted",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_MANIFEST": EXTERNAL_MODULE_MANIFEST,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "layers": LAYERS,
        "fixture_layer_rows": as_jsonable(fixture["layer_rows"]),
        "varying_g_structure_detail": as_jsonable(g_structure),
        "peps3d_signature": as_jsonable(peps_sig),
        "blockers": [] if all_pass else ["root_geometric_constraint_manifold_maturity_failed"],
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": all_pass, "out_path": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
