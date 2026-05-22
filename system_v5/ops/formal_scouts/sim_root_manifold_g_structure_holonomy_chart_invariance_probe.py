#!/usr/bin/env python3
"""Root-manifold G-structure holonomy chart-invariance scout.

Formal scout only. This is the next hardening step after the deep geometric
ratchet scout: it assumes the prior two-sheet signal may be a flux-chart
artifact and tries to kill that by rerunning the bounded ratchet under several
smooth orientation-preserving flux-coordinate reparameterizations.

A green receipt means this finite fixture preserved two-sheet separation,
sheet holonomy gap, dynamic tensor readouts, and varying G-structure pressure
across chart changes while rejecting symmetric, gauge-equivalent, and folded
non-diffeomorphic controls. It does not admit a real attractor basin, final
manifold, final G-structure, final holonomy class, engine, Axis0, bridge,
physics, target-system, or canonical claim.
"""

from __future__ import annotations

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
from sim_deep_geometric_ratchet_dynamic_tensor_network_basin_probe import (  # noqa: E402
    BRANCH_PHASES,
    DEPTHS,
    G_ROWS,
    G_STRUCTURE_SCHEDULE,
    LAYERS,
    basin_mix,
    canonical_layer_order_from_graph,
    constraint_strength,
    fixed_matrix,
    g_structure_features,
    initial_basin_state,
    load_lewm_module,
    normalized_exploration,
    sha256_file,
    tensor_network_signature,
)
from sim_root_geometric_constraint_manifold_maturity_pytorch_toolchain_probe import varying_g_structure_report  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "root_manifold_g_structure_holonomy_chart_invariance_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
LEWM_MODULE_PATH = pathlib.Path("/Users/joshuaeisenhart/GitHub/le-wm/module.py")

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "root_manifold_g_structure_holonomy_chart_invariance"
CLAIM_CEILING = (
    "Formal scout only: reruns the bounded root geometric-constraint-manifold "
    "ratchet fixture under multiple smooth flux-coordinate reparameterizations, "
    "checking two-sheet separation, sheet holonomy gap, dynamic tensor readouts, "
    "varying G-structure pressure, auto_LiRPA separation bounds, le-wm trajectory "
    "pressure, graph/topology/geometry/proof witnesses, and symmetric/gauge/"
    "folded-chart graveyards. Axis0 is not a pass-condition dependency. This "
    "does not admit a real attractor basin, final manifold, final G-structure, "
    "final holonomy class, engine, bridge, Axis0, physics, target-system, or "
    "canonical claim; it does not admit canonical claims."
)

VALID_CHARTS = ["identity", "sinusoidal", "two_harmonic", "shear", "curved"]
PHASES = [BRANCH_PHASES[1], BRANCH_PHASES[2], BRANCH_PHASES[3]]
TAU_HOLONOMY_GAP = 1e-5
TAU_BASIN_GAP = 0.025
TAU_FLUX_DELTA = 0.015
TAU_DERIVATIVE_MIN = 0.45
TAU_COSINE_LOWER = 0.70
TAU_COSINE_UPPER = 0.99999
TAU_GAUGE_GAP_MAX = 0.01
TAU_LIRPA_MARGIN = 0.001

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing charted ratchet dynamics, sheet holonomy tensors, feature adapters, and le-wm trajectory tensors",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing interval separation between valid chart features and gauge/symmetric controls",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Data.validate and MessagePassing over chart-layer-basin graph features",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing chart/layer dependency DAG and canonical layer order imported into the dynamics",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing arithmetic witness that gauge-equivalence denial conflicts with measured chart gaps",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent arithmetic witness for the same chart/gauge-equivalence boundary",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact chart-derivative and noncommutative sheet-holonomy expression witness",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing pseudoscalar orientation witness on chart-stable sheet vectors",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing sphere-distance witness between chart-stable sheet projections",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SO(3) tensor-product witness over the chart-stable sheet projections",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hypergraph witness binding charts, G-structure family schedule, and basin sheets",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial chart/layer/basin complex",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing persistence over chart holonomy-gap filtration",
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
        "reason": "load-bearing ARPredictor/SIGReg pressure over the chart family trajectory",
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
        if value.numel() <= 512:
            return value.detach().cpu().tolist()
        return f"<tensor shape={list(value.shape)} dtype={value.dtype}>"
    return value


def chart_value_and_derivative(kind: str, phi: float) -> tuple[float, float]:
    if kind == "identity":
        return phi, 1.0
    if kind == "sinusoidal":
        return phi + 0.17 * math.sin(phi + 0.1), 1.0 + 0.17 * math.cos(phi + 0.1)
    if kind == "two_harmonic":
        return phi + 0.11 * math.sin(2.0 * phi + 0.3), 1.0 + 0.22 * math.cos(2.0 * phi + 0.3)
    if kind == "shear":
        return 1.04 * phi + 0.06 * math.cos(phi), 1.04 - 0.06 * math.sin(phi)
    if kind == "curved":
        return (
            phi + 0.13 * math.sin(phi) + 0.07 * math.sin(3.0 * phi + 0.2),
            1.0 + 0.13 * math.cos(phi) + 0.21 * math.cos(3.0 * phi + 0.2),
        )
    if kind == "folded_control":
        return phi + 1.95 * math.sin(phi), 1.0 + 1.95 * math.cos(phi)
    raise ValueError(kind)


def charted_flux_field(
    depth_idx: int,
    layer_idx: int,
    phase: float,
    chart_kind: str,
    control_mode: str,
) -> tuple[torch.Tensor, float]:
    chart_phi, derivative = chart_value_and_derivative(chart_kind, phase)
    angles = torch.linspace(0.2, 1.6, steps=8, dtype=torch.float32)
    seed = torch.sin(angles * (1.0 + 0.09 * depth_idx) + chart_phi + 0.17 * layer_idx)
    scaled_seed = float(abs(derivative)) * seed
    if control_mode == "symmetric":
        left = scaled_seed
        right = scaled_seed
    elif control_mode == "gauge_equivalent":
        left = scaled_seed
        right = scaled_seed + 0.001 * torch.roll(scaled_seed, 1)
    else:
        left = scaled_seed
        right = 0.68 * torch.roll(scaled_seed, 1) + 0.19 * scaled_seed + 0.09 * torch.cos(
            angles + chart_phi + 0.31 * depth_idx
        )
    return 0.035 * torch.stack([left, right]), derivative


def charted_step(
    state: torch.Tensor,
    *,
    depth_idx: int,
    layer_idx: int,
    phase: float,
    chart_kind: str,
    control_mode: str,
) -> tuple[torch.Tensor, dict[str, float]]:
    chart_phase, derivative = chart_value_and_derivative(chart_kind, phase)
    strength = constraint_strength(depth_idx, layer_idx, "ratchet")
    exploration = normalized_exploration(depth_idx, layer_idx, chart_phase, 1.0)
    family = g_structure_features(layer_idx)
    matrix = fixed_matrix(layer_idx, scale=0.021 + 0.002 * depth_idx + 0.0015 * math.sin(chart_phase))
    transformed = torch.stack([matrix @ state[0], matrix.t() @ state[1]])
    mixed = basin_mix(state, graph_weight=family[1])
    flux, _flux_derivative = charted_flux_field(depth_idx, layer_idx, phase, chart_kind, control_mode)
    gate = torch.sigmoid(1.1 * strength + 0.2 * family[0] - 0.15 * family[4] + 0.035 * math.sin(chart_phase))
    next_state = torch.tanh(
        (1.0 - 0.22 * gate) * state
        + 0.24 * gate * transformed
        + 0.08 * mixed
        + 0.06 * family[3] * torch.flip(state, dims=[1])
        + exploration
        + flux
    )
    left_next = next_state[0]
    if control_mode == "gauge_equivalent":
        left_preimage = torch.atanh(left_next.clamp(-0.999999, 0.999999))
        right_neighbor = left_preimage + 0.0005 * left_next
    else:
        right_neighbor = (
            0.76 * left_next
            + 0.24 * next_state[1]
            + 0.08 * torch.tanh(flux[1] - 0.65 * flux[0])
            + 0.012 * family[4] * torch.roll(left_next, 1)
        )
    next_state = torch.stack([left_next, torch.tanh(right_neighbor)])
    return next_state, {
        "derivative": float(derivative),
        "flux_delta_norm": float(torch.linalg.vector_norm((flux[0] - flux[1]).detach()).item()),
        "exploration_norm": float(torch.linalg.vector_norm(exploration.detach()).item()),
    }


def sheet_holonomy(sheet_history: torch.Tensor, dims: tuple[int, int, int] = (5, 6, 7)) -> float:
    points = sheet_history[:, list(dims)]
    points = points / torch.linalg.vector_norm(points, dim=1, keepdim=True).clamp_min(1e-9)
    total = 0.0
    for idx in range(points.shape[0] - 2):
        a, b, c = points[idx], points[idx + 1], points[idx + 2]
        numerator = torch.dot(a, torch.cross(b, c, dim=0))
        denominator = 1.0 + torch.dot(a, b) + torch.dot(b, c) + torch.dot(c, a)
        total += math.atan2(float(numerator), float(denominator))
    return total


def simulate_chart(chart_kind: str, *, phase: float, control_mode: str = "asymmetric") -> dict[str, Any]:
    order = canonical_layer_order_from_graph()
    root_state = initial_basin_state(phase)
    state = root_state
    all_states = []
    depth_rows = []
    derivatives = []
    flux_deltas = []
    for depth_idx in range(len(DEPTHS)):
        depth_states = []
        for local_step, layer_idx in enumerate(order):
            step_phase = phase + 0.151 * local_step + 0.019 * depth_idx
            state, metrics = charted_step(
                state,
                depth_idx=depth_idx,
                layer_idx=layer_idx,
                phase=step_phase,
                chart_kind=chart_kind,
                control_mode=control_mode,
            )
            all_states.append(state)
            depth_states.append(state)
            derivatives.append(metrics["derivative"])
            flux_deltas.append(metrics["flux_delta_norm"])
        depth_rows.append(torch.stack(depth_states))
    state_history = torch.stack(all_states)
    depth_history = torch.stack(depth_rows)
    depth_final_history = depth_history[-1]
    left_history = depth_final_history[:, 0, :]
    right_history = depth_final_history[:, 1, :]
    left_sig = tensor_network_signature(left_history)
    right_sig = tensor_network_signature(right_history)
    tensor_signature = torch.cat([left_sig, right_sig, torch.abs(left_sig - right_sig)])
    left_final = state[0].detach()
    right_final = state[1].detach()
    cosine = float(F.cosine_similarity(left_final, right_final, dim=0).item())
    hol_left = sheet_holonomy(left_history.detach())
    hol_right = sheet_holonomy(right_history.detach())
    terminal_history = depth_final_history.detach().mean(dim=1)
    g_structure = varying_g_structure_report(terminal_history)
    return {
        "chart": chart_kind,
        "control_mode": control_mode,
        "phase": phase,
        "final": state.detach(),
        "state_history": state_history.detach(),
        "depth_final_history": depth_final_history.detach(),
        "tensor_signature": tensor_signature.detach(),
        "basin_gap": float(torch.linalg.vector_norm(left_final - right_final).item()),
        "cosine_similarity": cosine,
        "norm_asymmetry": float(abs(torch.linalg.vector_norm(left_final).item() - torch.linalg.vector_norm(right_final).item())),
        "flux_delta_mean": float(torch.tensor(flux_deltas, dtype=torch.float32).mean().item()),
        "chart_derivative_min": float(min(derivatives)),
        "chart_derivative_max": float(max(derivatives)),
        "left_holonomy": hol_left,
        "right_holonomy": hol_right,
        "holonomy_gap": abs(hol_left - hol_right),
        "g_structure_pass": bool(g_structure["pass"]),
        "g_structure_min_control_gap": float(
            min(
                g_structure["min_frozen_single_family_gap"],
                g_structure["min_generic_control_gap"],
                g_structure["reverse_schedule_gap"],
            )
        ),
    }


def chart_family_report() -> dict[str, Any]:
    rows = []
    for chart in VALID_CHARTS:
        runs = [simulate_chart(chart, phase=phase) for phase in PHASES]
        tensor_stack = torch.stack([run["tensor_signature"] for run in runs])
        rows.append(
            {
                "chart": chart,
                "phase_count": len(PHASES),
                "basin_gap_min": min(run["basin_gap"] for run in runs),
                "basin_gap_max": max(run["basin_gap"] for run in runs),
                "cosine_min": min(run["cosine_similarity"] for run in runs),
                "cosine_max": max(run["cosine_similarity"] for run in runs),
                "norm_asymmetry_min": min(run["norm_asymmetry"] for run in runs),
                "flux_delta_min": min(run["flux_delta_mean"] for run in runs),
                "holonomy_gap_min": min(run["holonomy_gap"] for run in runs),
                "holonomy_gap_max": max(run["holonomy_gap"] for run in runs),
                "derivative_min": min(run["chart_derivative_min"] for run in runs),
                "derivative_max": max(run["chart_derivative_max"] for run in runs),
                "tensor_signature_std": float(tensor_stack.std(dim=0, unbiased=False).mean().item()),
                "g_structure_all_pass": all(run["g_structure_pass"] for run in runs),
                "g_structure_min_control_gap": min(run["g_structure_min_control_gap"] for run in runs),
                "representative_final": runs[1]["final"],
                "representative_tensor_signature": runs[1]["tensor_signature"],
            }
        )
    valid_checks = [
        row["basin_gap_min"] > TAU_BASIN_GAP
        and row["cosine_min"] > TAU_COSINE_LOWER
        and row["cosine_max"] < TAU_COSINE_UPPER
        and row["flux_delta_min"] > TAU_FLUX_DELTA
        and row["holonomy_gap_min"] > TAU_HOLONOMY_GAP
        and row["derivative_min"] > TAU_DERIVATIVE_MIN
        and row["g_structure_all_pass"]
        for row in rows
    ]
    return {"rows": rows, "pass": all(valid_checks)}


def controls_report() -> dict[str, Any]:
    gauge_runs = [
        simulate_chart(chart, phase=phase, control_mode="gauge_equivalent")
        for chart in VALID_CHARTS
        for phase in PHASES
    ]
    symmetric_runs = [
        simulate_chart(chart, phase=phase, control_mode="symmetric")
        for chart in VALID_CHARTS
        for phase in PHASES
    ]
    folded = simulate_chart("folded_control", phase=PHASES[1], control_mode="asymmetric")
    gauge_basin_gap_max = max(run["basin_gap"] for run in gauge_runs)
    gauge_holonomy_gap_max = max(run["holonomy_gap"] for run in gauge_runs)
    symmetric_flux_delta_max = max(run["flux_delta_mean"] for run in symmetric_runs)
    return {
        "gauge_equivalent_sheet_rejected": {
            "chart_phase_count": len(gauge_runs),
            "basin_gap": gauge_basin_gap_max,
            "basin_gap_max": gauge_basin_gap_max,
            "holonomy_gap": gauge_holonomy_gap_max,
            "holonomy_gap_max": gauge_holonomy_gap_max,
            "TAU_GAUGE_GAP_MAX": TAU_GAUGE_GAP_MAX,
            "TAU_HOLONOMY_GAP": TAU_HOLONOMY_GAP,
            "pass": gauge_basin_gap_max < TAU_GAUGE_GAP_MAX and gauge_holonomy_gap_max < TAU_HOLONOMY_GAP,
        },
        "symmetric_flux_chart_rejected": {
            "chart_phase_count": len(symmetric_runs),
            "flux_delta_mean": symmetric_flux_delta_max,
            "flux_delta_max": symmetric_flux_delta_max,
            "pass": symmetric_flux_delta_max < 1e-8,
        },
        "folded_non_diffeomorphic_chart_rejected": {
            "derivative_min": folded["chart_derivative_min"],
            "TAU_DERIVATIVE_MIN": TAU_DERIVATIVE_MIN,
            "pass": folded["chart_derivative_min"] < 0.0,
        },
    }


class ChartMessenger(MessagePassing):
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


def chart_row_clears_signal(row: dict[str, Any]) -> bool:
    return bool(
        row["basin_gap_min"] > TAU_BASIN_GAP
        and row["holonomy_gap_min"] > TAU_HOLONOMY_GAP
        and row["flux_delta_min"] > TAU_FLUX_DELTA
        and row["derivative_min"] > TAU_DERIVATIVE_MIN
        and row["g_structure_all_pass"]
    )


def graph_topology_report(chart_report: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    chart_nodes = [graph.add_node({"kind": "chart", "chart": row["chart"]}) for row in chart_report["rows"]]
    layer_nodes = [graph.add_node({"kind": "layer", "name": name}) for name in LAYERS]
    basin_left = graph.add_node({"kind": "basin", "name": "left_sheet"})
    basin_right = graph.add_node({"kind": "basin", "name": "right_sheet"})
    chart_edge_signals = []
    for chart_node, row in zip(chart_nodes, chart_report["rows"]):
        signal = float(row["basin_gap_min"] + row["holonomy_gap_min"] * 10000.0 + row["flux_delta_min"])
        chart_edge_signals.append(signal)
        graph.add_edge(chart_node, layer_nodes[0], {"relation": "chart_drives", "signal": signal})
    layer_edge_signals = []
    for idx, (src, dst) in enumerate(zip(layer_nodes[:-1], layer_nodes[1:])):
        g_features = g_structure_features(idx)
        signal = float(
            G_ROWS[G_STRUCTURE_SCHEDULE[idx]]["survivor_fraction"]
            + 0.01 * torch.linalg.vector_norm(g_features).item()
            + 0.001 * constraint_strength(idx % len(DEPTHS), idx, "ratchet")
        )
        layer_edge_signals.append(signal)
        graph.add_edge(src, dst, {"relation": "layer_requires", "signal": signal})
    sheet_edge_signal = min(float(row["basin_gap_min"]) for row in chart_report["rows"])
    graph.add_edge(layer_nodes[-1], basin_left, {"relation": "forms", "signal": sheet_edge_signal})
    graph.add_edge(layer_nodes[-1], basin_right, {"relation": "forms", "signal": sheet_edge_signal})

    x_rows = []
    for row in chart_report["rows"]:
        x_rows.append(
            [
                row["basin_gap_min"],
                row["holonomy_gap_min"] * 10000.0,
                row["flux_delta_min"],
                row["derivative_min"],
            ]
        )
    for idx, _layer in enumerate(LAYERS):
        x_rows.append([idx / 12.0, G_ROWS[G_STRUCTURE_SCHEDULE[idx]]["survivor_fraction"], 0.0, 1.0])
    x_rows.extend([[1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]])
    edge_index = torch.tensor([(src, dst) for src, dst in graph.edge_list()], dtype=torch.long).t().contiguous()
    data = Data(x=torch.tensor(x_rows, dtype=torch.float32), edge_index=edge_index, num_nodes=len(x_rows))
    data.validate(raise_on_error=True)
    messenger = ChartMessenger()
    with torch.no_grad():
        mp_out = messenger(data.x, data.edge_index)
        chart_ablated_x = data.x.clone()
        chart_ablated_x[: len(VALID_CHARTS)] = 0.0
        mp_chart_ablated = messenger(chart_ablated_x, data.edge_index)
    mp_norm = float(torch.linalg.vector_norm(mp_out).item())
    mp_chart_delta = float(torch.linalg.vector_norm(mp_out - mp_chart_ablated).item())
    chart_feature_sum = data.x[: len(VALID_CHARTS)].sum(dim=0)
    layer_zero_aggregate = mp_out[len(VALID_CHARTS), 4:]
    aggregate_error = float(torch.linalg.vector_norm(layer_zero_aggregate - chart_feature_sum).item())
    aggregate_norm = float(torch.linalg.vector_norm(layer_zero_aggregate).item())
    graph_edge_signal_min = min(chart_edge_signals + layer_edge_signals + [sheet_edge_signal])
    layer_edge_signal_range = max(layer_edge_signals) - min(layer_edge_signals)
    chart_signal_stds = {
        key: float(torch.tensor([row[key] for row in chart_report["rows"]], dtype=torch.float32).std(unbiased=False).item())
        for key in [
            "basin_gap_min",
            "holonomy_gap_min",
            "flux_delta_min",
            "derivative_min",
            "g_structure_min_control_gap",
        ]
    }

    hypergraph = xgi.Hypergraph()
    g_families = sorted(set(G_STRUCTURE_SCHEDULE))
    active_chart_names = []
    rejected_chart_names = []
    for row in chart_report["rows"]:
        if chart_row_clears_signal(row):
            active_chart_names.append(row["chart"])
            hypergraph.add_edge([row["chart"], "left_sheet", "right_sheet", *g_families])
        else:
            rejected_chart_names.append(row["chart"])

    complex_ = tnx.SimplicialComplex()
    for row in chart_report["rows"]:
        if chart_row_clears_signal(row):
            complex_.add_simplex([row["chart"], "left_sheet", "right_sheet"])
    for idx in range(len(LAYERS) - 2):
        complex_.add_simplex(LAYERS[idx : idx + 3])

    st = gudhi.SimplexTree()
    for idx, row in enumerate(chart_report["rows"]):
        st.insert([idx], filtration=float(row["holonomy_gap_min"]))
    for idx in range(len(chart_report["rows"]) - 1):
        st.insert(
            [idx, idx + 1],
            filtration=max(
                float(chart_report["rows"][idx]["holonomy_gap_min"]),
                float(chart_report["rows"][idx + 1]["holonomy_gap_min"]),
            ),
        )
    persistence = st.persistence()
    min_basin_gap = min(float(row["basin_gap_min"]) for row in chart_report["rows"])
    holonomy_values = [float(row["holonomy_gap_min"]) for row in chart_report["rows"]]
    holonomy_filtration_range = max(holonomy_values) - min(holonomy_values)
    finite_persistence_lifetimes = [
        float(death - birth)
        for _dim, (birth, death) in persistence
        if math.isfinite(float(death)) and death > birth
    ]
    max_finite_persistence_lifetime = max(finite_persistence_lifetimes) if finite_persistence_lifetimes else 0.0
    return {
        "rustworkx": {
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
            "graph_edge_signal_min": graph_edge_signal_min,
            "layer_edge_signal_range": layer_edge_signal_range,
            "sheet_edge_signal": sheet_edge_signal,
            "runtime_edge_signal_gate": bool(
                graph_edge_signal_min > 0.0
                and layer_edge_signal_range > 0.0
                and sheet_edge_signal > TAU_BASIN_GAP
            ),
        },
        "pyg": {
            "data_validate_passed": True,
            "message_passing_shape": list(mp_out.shape),
            "message_passing_norm": mp_norm,
            "chart_ablation_delta": mp_chart_delta,
            "chart_ablation_delta_gt_min_basin_gap": mp_chart_delta > min_basin_gap,
            "message_passing_norm_gt_min_basin_gap": mp_norm > min_basin_gap,
            "layer_zero_aggregate_norm": aggregate_norm,
            "chart_feature_sum_norm": float(torch.linalg.vector_norm(chart_feature_sum).item()),
            "aggregate_error": aggregate_error,
            "aggregate_matches_chart_sum": aggregate_error < 1e-6,
        },
        "xgi": {
            "hyperedge_count": count_xgi_edges(hypergraph),
            "g_structure_family_count": len(g_families),
            "g_structure_families": g_families,
            "active_chart_names": active_chart_names,
            "rejected_chart_names": rejected_chart_names,
            "active_chart_count": len(active_chart_names),
        },
        "toponetx": {
            "simplicial_complex_dim": int(complex_.dim),
            "shape": str(complex_.shape),
            "data_gated_chart_simplex_count": len(active_chart_names),
            "data_gated_chart_simplexes_cover_valid_charts": set(active_chart_names) == set(VALID_CHARTS),
        },
        "gudhi": {
            "simplex_count": int(st.num_simplices()),
            "persistence_pair_count": len(persistence),
            "holonomy_filtration_range": holonomy_filtration_range,
            "holonomy_filtration_range_over_min": holonomy_filtration_range / max(min(holonomy_values), 1e-12),
            "finite_persistence_lifetime_count": len(finite_persistence_lifetimes),
            "max_finite_persistence_lifetime": max_finite_persistence_lifetime,
        },
        "chart_signal_stds": chart_signal_stds,
        "pass": bool(
            rx.is_directed_acyclic_graph(graph)
            and graph_edge_signal_min > 0.0
            and layer_edge_signal_range > 0.0
            and sheet_edge_signal > TAU_BASIN_GAP
            and mp_chart_delta > min_basin_gap
            and aggregate_error < 1e-6
            and aggregate_norm > min_basin_gap
            and mp_norm > min_basin_gap
            and set(active_chart_names) == set(VALID_CHARTS)
            and not rejected_chart_names
            and len(g_families) == 3
            and len(active_chart_names) == len(VALID_CHARTS)
            and min_basin_gap > TAU_BASIN_GAP
            and max_finite_persistence_lifetime > 1e-9
            and holonomy_filtration_range > 1e-9
            and holonomy_filtration_range / max(min(holonomy_values), 1e-12) > 0.01
            and chart_signal_stds["basin_gap_min"] > 1e-4
            and chart_signal_stds["flux_delta_min"] > 1e-4
            and chart_signal_stds["holonomy_gap_min"] > 1e-8
            and chart_signal_stds["derivative_min"] > 1e-3
            and chart_signal_stds["g_structure_min_control_gap"] > 1e-6
        ),
    }


def symbolic_chart_derivative_expr(kind: str, phi: sp.Symbol) -> sp.Expr:
    if kind == "identity":
        return sp.Integer(1)
    if kind == "sinusoidal":
        return sp.diff(phi + sp.Rational(17, 100) * sp.sin(phi + sp.Rational(1, 10)), phi)
    if kind == "two_harmonic":
        return sp.diff(phi + sp.Rational(11, 100) * sp.sin(2 * phi + sp.Rational(3, 10)), phi)
    if kind == "shear":
        return sp.diff(sp.Rational(104, 100) * phi + sp.Rational(6, 100) * sp.cos(phi), phi)
    if kind == "curved":
        return sp.diff(
            phi
            + sp.Rational(13, 100) * sp.sin(phi)
            + sp.Rational(7, 100) * sp.sin(3 * phi + sp.Rational(2, 10)),
            phi,
        )
    raise ValueError(kind)


def simulated_step_phases() -> list[float]:
    order = canonical_layer_order_from_graph()
    return [
        phase + 0.151 * local_step + 0.019 * depth_idx
        for phase in PHASES
        for depth_idx in range(len(DEPTHS))
        for local_step, _layer_idx in enumerate(order)
    ]


def math_geometry_report(chart_report: dict[str, Any]) -> dict[str, Any]:
    h_l, h_r = sp.symbols("H_L H_R", commutative=False)
    coeff_l = chart_report["rows"][0]["holonomy_gap_min"]
    coeff_r = chart_report["rows"][-1]["holonomy_gap_min"]
    comm = sp.expand(coeff_l * h_l * h_r - coeff_r * h_r * h_l)
    holonomy_coeff_delta = abs(float(coeff_l) - float(coeff_r))
    min_holonomy_gap = min(float(row["holonomy_gap_min"]) for row in chart_report["rows"])
    phi = sp.symbols("phi")
    step_phases = simulated_step_phases()
    derivative_rows = []
    for row in chart_report["rows"]:
        derivative_expr = symbolic_chart_derivative_expr(row["chart"], phi)
        values = [float(derivative_expr.subs(phi, sp.Float(phase))) for phase in step_phases]
        symbolic_min = min(values)
        symbolic_max = max(values)
        derivative_rows.append(
            {
                "chart": row["chart"],
                "symbolic_derivative": str(derivative_expr),
                "symbolic_min": symbolic_min,
                "symbolic_max": symbolic_max,
                "runtime_min": row["derivative_min"],
                "runtime_max": row["derivative_max"],
                "min_abs_error": abs(symbolic_min - row["derivative_min"]),
                "max_abs_error": abs(symbolic_max - row["derivative_max"]),
                "pass": abs(symbolic_min - row["derivative_min"]) < 1e-6
                and abs(symbolic_max - row["derivative_max"]) < 1e-6,
            }
        )

    _, blades = Cl(1, 3)
    pseudoscalar_square = float((blades["e1234"] * blades["e1234"])[()])
    sphere = Hypersphere(dim=2)
    tensor_product = o3.FullTensorProduct(o3.Irreps("1x1o"), o3.Irreps("1x1o"))
    geometry_rows = []
    for row in chart_report["rows"]:
        final = row["representative_final"]
        left = final[0]
        right = final[1]
        vector = (
            float(left[0].item()) * blades["e1"]
            + float(left[1].item()) * blades["e2"]
            + float(right[0].item()) * blades["e3"]
            + float(right[1].item()) * blades["e4"]
        )
        pseudoscalar_action = blades["e1234"] * vector
        action_grades = sorted(int(grade) for grade in pseudoscalar_action.grades())
        pseudoscalar_action_norm = math.sqrt(sum(float(coeff) * float(coeff) for coeff in pseudoscalar_action.value))
        runtime_vector_norm = math.sqrt(
            float(left[0].item()) ** 2
            + float(left[1].item()) ** 2
            + float(right[0].item()) ** 2
            + float(right[1].item()) ** 2
        )
        runtime_sheet_delta_4d = math.sqrt(sum(float((left[idx] - right[idx]).item()) ** 2 for idx in range(4)))
        left3 = left[:3] / torch.linalg.vector_norm(left[:3]).clamp_min(1e-9)
        right3 = right[:3] / torch.linalg.vector_norm(right[:3]).clamp_min(1e-9)
        sphere_distance = float(
            sphere.metric.dist(gs.array([float(x) for x in left3.tolist()]), gs.array([float(x) for x in right3.tolist()]))
        )
        e3nn_out = tensor_product(left[:3], right[:3])
        e3nn_self = tensor_product(left[:3], left[:3])
        e3nn_norm = float(torch.linalg.vector_norm(e3nn_out).item())
        e3nn_sheet_delta = float(torch.linalg.vector_norm(e3nn_out - e3nn_self).item())
        geometry_rows.append(
            {
                "chart": row["chart"],
                "action_grades": action_grades,
                "pseudoscalar_action_norm": pseudoscalar_action_norm,
                "runtime_vector_norm": runtime_vector_norm,
                "runtime_sheet_delta_4d": runtime_sheet_delta_4d,
                "sphere_distance": sphere_distance,
                "e3nn_output_norm": e3nn_norm,
                "e3nn_sheet_tensor_delta_vs_self": e3nn_sheet_delta,
            }
        )
    sympy_pass = all(row["pass"] for row in derivative_rows)
    min_pseudoscalar_action_norm = min(row["pseudoscalar_action_norm"] for row in geometry_rows)
    min_runtime_vector_norm = min(row["runtime_vector_norm"] for row in geometry_rows)
    min_runtime_sheet_delta_4d = min(row["runtime_sheet_delta_4d"] for row in geometry_rows)
    min_sphere_distance = min(row["sphere_distance"] for row in geometry_rows)
    max_sphere_distance = max(row["sphere_distance"] for row in geometry_rows)
    min_e3nn_norm = min(row["e3nn_output_norm"] for row in geometry_rows)
    min_e3nn_delta = min(row["e3nn_sheet_tensor_delta_vs_self"] for row in geometry_rows)
    sphere_distance_std = float(torch.tensor([row["sphere_distance"] for row in geometry_rows]).std(unbiased=False).item())
    e3nn_delta_std = float(
        torch.tensor([row["e3nn_sheet_tensor_delta_vs_self"] for row in geometry_rows]).std(unbiased=False).item()
    )
    clifford_pass = (
        abs(pseudoscalar_square + 1.0) < 1e-9
        and min_pseudoscalar_action_norm > 0.1
        and min_runtime_vector_norm > 0.1
        and min_runtime_sheet_delta_4d > TAU_BASIN_GAP
    )
    geomstats_pass = bool(min_sphere_distance > 1e-4 and max_sphere_distance < 2.5 and sphere_distance_std > 1e-6)
    e3nn_pass = bool(min_e3nn_norm > 0.1 * min_sphere_distance and min_e3nn_delta > 0.05 * min_sphere_distance and e3nn_delta_std > 1e-6)
    return {
        "sympy_chart_derivative_and_holonomy_order": {
            "noncommutative_holonomy_expr": str(comm),
            "holonomy_coeff_delta": holonomy_coeff_delta,
            "holonomy_coeff_delta_threshold": max(1e-7, 0.005 * min_holonomy_gap),
            "step_phase_count": len(step_phases),
            "derivative_rows": derivative_rows,
            "pass": bool(comm != 0 and holonomy_coeff_delta > max(1e-7, 0.005 * min_holonomy_gap) and sympy_pass),
        },
        "clifford_orientation": {
            "pseudoscalar_square": pseudoscalar_square,
            "geometry_rows": geometry_rows,
            "min_pseudoscalar_action_norm": min_pseudoscalar_action_norm,
            "min_runtime_vector_norm": min_runtime_vector_norm,
            "min_runtime_sheet_delta_4d": min_runtime_sheet_delta_4d,
            "pass": bool(clifford_pass),
        },
        "geomstats_sheet_distance": {
            "min_sphere_distance": min_sphere_distance,
            "max_sphere_distance": max_sphere_distance,
            "sphere_distance_std": sphere_distance_std,
            "pass": geomstats_pass,
        },
        "e3nn_sheet_tensor_product": {
            "irreps_out": str(tensor_product.irreps_out),
            "min_output_norm": min_e3nn_norm,
            "min_sheet_tensor_delta_vs_self": min_e3nn_delta,
            "sheet_tensor_delta_std": e3nn_delta_std,
            "pass": e3nn_pass,
        },
        "pass": bool(sympy_pass and clifford_pass and geomstats_pass and e3nn_pass),
    }


class ChartSeparationAdapter(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(6, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.tensor([[0.22, 0.12, 2.0, 0.30, 0.06, 0.25]], dtype=torch.float32))
            self.linear.bias.zero_()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x).squeeze(-1)


def feature_row_from_metrics(metrics: dict[str, Any]) -> list[float]:
    return [
        float(metrics["basin_gap"]),
        float(metrics["norm_asymmetry"]),
        float(metrics["flux_delta_mean"]),
        float(metrics["holonomy_gap"] * 10000.0),
        float(torch.linalg.vector_norm(metrics["tensor_signature"]).item() / 20.0),
        float(1.0 - metrics["cosine_similarity"]),
    ]


def feature_row_from_chart(row: dict[str, Any]) -> list[float]:
    return [
        float(row["basin_gap_min"]),
        float(row["norm_asymmetry_min"]),
        float(row["flux_delta_min"]),
        float(row["holonomy_gap_min"] * 10000.0),
        float(torch.linalg.vector_norm(row["representative_tensor_signature"]).item() / 20.0),
        float(1.0 - row["cosine_max"]),
    ]


def lirpa_report(chart_report: dict[str, Any]) -> dict[str, Any]:
    valid_features = torch.tensor([feature_row_from_chart(row) for row in chart_report["rows"]], dtype=torch.float32)
    controls = [
        simulate_chart(chart, phase=PHASES[1], control_mode="gauge_equivalent")
        for chart in VALID_CHARTS
    ] + [
        simulate_chart(chart, phase=PHASES[1], control_mode="symmetric")
        for chart in VALID_CHARTS
    ]
    control_features = torch.tensor([feature_row_from_metrics(row) for row in controls], dtype=torch.float32)
    model = ChartSeparationAdapter().eval()
    eps = 0.0002
    valid_bounded = BoundedModule(model, valid_features)
    valid_x = BoundedTensor(valid_features, PerturbationLpNorm(norm=float("inf"), eps=eps))
    valid_lb, valid_ub = valid_bounded.compute_bounds(x=(valid_x,), method="IBP")
    control_bounded = BoundedModule(model, control_features)
    control_x = BoundedTensor(control_features, PerturbationLpNorm(norm=float("inf"), eps=eps))
    control_lb, control_ub = control_bounded.compute_bounds(x=(control_x,), method="IBP")
    margin = float((valid_lb.min() - control_ub.max()).item())
    return {
        "method": "IBP",
        "eps_linf": eps,
        "valid_feature_shape": list(valid_features.shape),
        "control_feature_shape": list(control_features.shape),
        "valid_lb_min": float(valid_lb.min().item()),
        "valid_ub_max": float(valid_ub.max().item()),
        "control_lb_min": float(control_lb.min().item()),
        "control_ub_max": float(control_ub.max().item()),
        "separation_margin": margin,
        "pass": bool(margin > TAU_LIRPA_MARGIN),
    }


def lewm_report(lewm_module: Any, chart_report: dict[str, Any]) -> dict[str, Any]:
    torch.manual_seed(518062)
    frames = torch.stack([row["representative_final"].reshape(-1) for row in chart_report["rows"]]).detach()
    trajectory = frames.unsqueeze(0)
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
    actions = torch.tanh(torch.roll(trajectory, shifts=1, dims=1) - 0.05 * trajectory)
    initial_pred = predictor(trajectory, actions)
    initial_loss = F.mse_loss(initial_pred[:, :-1], trajectory[:, 1:]).detach()
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.015, weight_decay=0.0)
    predictor.train()
    for _step in range(70):
        optimizer.zero_grad(set_to_none=True)
        pred = predictor(trajectory, actions)
        loss = F.mse_loss(pred[:, :-1], trajectory[:, 1:])
        loss.backward()
        optimizer.step()
    predictor.eval()
    with torch.no_grad():
        pred = predictor(trajectory, actions)
        collapsed = trajectory.mean(dim=1, keepdim=True).expand_as(trajectory)
        amplitude_collapsed = trajectory * 0.25
        zero_action_pred = predictor(trajectory, actions * 0.0)
        collapsed_pred = predictor(collapsed, actions * 0.0)
        next_loss = F.mse_loss(pred[:, :-1], trajectory[:, 1:])
        zero_action_loss = F.mse_loss(zero_action_pred[:, :-1], trajectory[:, 1:])
        collapsed_loss = F.mse_loss(collapsed_pred[:, :-1], trajectory[:, 1:])
        torch.manual_seed(6262)
        sig_source = sigreg(trajectory.transpose(0, 1))
        torch.manual_seed(6262)
        sig_collapsed = sigreg(collapsed.transpose(0, 1))
        torch.manual_seed(6262)
        sig_amplitude_collapsed = sigreg(amplitude_collapsed.transpose(0, 1))
    best_control = torch.minimum(zero_action_loss, collapsed_loss)
    advantage = (best_control - next_loss) / best_control.clamp_min(1e-9)
    sig_amplitude_delta = torch.abs(sig_source - sig_amplitude_collapsed)
    return {
        "loaded_classes": ["ARPredictor", "SIGReg"],
        "module_sha256": sha256_file(LEWM_MODULE_PATH),
        "trajectory_shape": list(trajectory.shape),
        "training_steps": 70,
        "initial_next_embedding_loss": float(initial_loss.item()),
        "next_embedding_loss": float(next_loss.item()),
        "zero_action_control_loss": float(zero_action_loss.item()),
        "collapsed_control_loss": float(collapsed_loss.item()),
        "relative_loss_advantage_vs_best_control": float(advantage.item()),
        "sigreg_source_score": float(sig_source.item()),
        "sigreg_collapsed_score": float(sig_collapsed.item()),
        "sigreg_delta_abs": float(torch.abs(sig_source - sig_collapsed).item()),
        "sigreg_amplitude_collapsed_score": float(sig_amplitude_collapsed.item()),
        "sigreg_amplitude_delta_abs": float(sig_amplitude_delta.item()),
        "pass": bool(
            math.isfinite(float(next_loss.item()))
            and next_loss.item() < best_control.item() * 0.92
            and advantage.item() > 0.02
            and sig_amplitude_delta.item() > 0.05
        ),
    }


def proof_report(chart_report: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    min_basin = min(row["basin_gap_min"] for row in chart_report["rows"])
    min_holonomy = min(row["holonomy_gap_min"] for row in chart_report["rows"])
    min_flux = min(row["flux_delta_min"] for row in chart_report["rows"])
    min_derivative = min(row["derivative_min"] for row in chart_report["rows"])
    max_cosine = max(row["cosine_max"] for row in chart_report["rows"])
    gauge_gap = controls["gauge_equivalent_sheet_rejected"]["basin_gap"]
    gauge_hol = controls["gauge_equivalent_sheet_rejected"]["holonomy_gap"]

    z3_solver = z3.Solver()
    z_min_basin = z3.Real("min_basin_gap")
    z_min_hol = z3.Real("min_holonomy_gap")
    z_min_flux = z3.Real("min_flux_delta")
    z_min_deriv = z3.Real("min_chart_derivative")
    z_max_cos = z3.Real("max_cosine")
    z3_solver.add(z_min_basin == z3.RealVal(f"{min_basin:.12f}"))
    z3_solver.add(z_min_hol == z3.RealVal(f"{min_holonomy:.12f}"))
    z3_solver.add(z_min_flux == z3.RealVal(f"{min_flux:.12f}"))
    z3_solver.add(z_min_deriv == z3.RealVal(f"{min_derivative:.12f}"))
    z3_solver.add(z_max_cos == z3.RealVal(f"{max_cosine:.12f}"))
    required = z3.And(
        z_min_basin > z3.RealVal(str(TAU_BASIN_GAP)),
        z_min_hol > z3.RealVal(str(TAU_HOLONOMY_GAP)),
        z_min_flux > z3.RealVal(str(TAU_FLUX_DELTA)),
        z_min_deriv > z3.RealVal(str(TAU_DERIVATIVE_MIN)),
        z_max_cos < z3.RealVal(str(TAU_COSINE_UPPER)),
    )
    z3_solver.add(z3.Not(required))
    z3_required_unsat = z3_solver.check()

    z3_gauge = z3.Solver()
    g_gap = z3.Real("gauge_gap")
    g_hol = z3.Real("gauge_holonomy_gap")
    z3_gauge.add(g_gap == z3.RealVal(f"{gauge_gap:.12f}"))
    z3_gauge.add(g_hol == z3.RealVal(f"{gauge_hol:.12f}"))
    z3_gauge.add(g_gap < z3.RealVal(str(TAU_GAUGE_GAP_MAX)))
    z3_gauge.add(g_hol < z3.RealVal(str(TAU_HOLONOMY_GAP)))
    z3_gauge_sat = z3_gauge.check()

    cvc = cvc5.Solver()
    cvc.setLogic("ALL")
    real = cvc.getRealSort()
    c_min_basin = cvc.mkConst(real, "min_basin_gap")
    c_min_hol = cvc.mkConst(real, "min_holonomy_gap")
    c_min_flux = cvc.mkConst(real, "min_flux_delta")
    c_min_deriv = cvc.mkConst(real, "min_chart_derivative")
    c_max_cos = cvc.mkConst(real, "max_cosine")

    def rv(value: float) -> cvc5.Term:
        return cvc.mkReal(f"{value:.12f}")

    cvc.assertFormula(cvc.mkTerm(Kind.EQUAL, c_min_basin, rv(min_basin)))
    cvc.assertFormula(cvc.mkTerm(Kind.EQUAL, c_min_hol, rv(min_holonomy)))
    cvc.assertFormula(cvc.mkTerm(Kind.EQUAL, c_min_flux, rv(min_flux)))
    cvc.assertFormula(cvc.mkTerm(Kind.EQUAL, c_min_deriv, rv(min_derivative)))
    cvc.assertFormula(cvc.mkTerm(Kind.EQUAL, c_max_cos, rv(max_cosine)))
    c_required = cvc.mkTerm(
        Kind.AND,
        cvc.mkTerm(Kind.GT, c_min_basin, rv(TAU_BASIN_GAP)),
        cvc.mkTerm(Kind.GT, c_min_hol, rv(TAU_HOLONOMY_GAP)),
        cvc.mkTerm(Kind.GT, c_min_flux, rv(TAU_FLUX_DELTA)),
        cvc.mkTerm(Kind.GT, c_min_deriv, rv(TAU_DERIVATIVE_MIN)),
        cvc.mkTerm(Kind.LT, c_max_cos, rv(TAU_COSINE_UPPER)),
    )
    cvc.assertFormula(cvc.mkTerm(Kind.NOT, c_required))
    cvc_required_unsat = cvc.checkSat()

    gauge_cvc = cvc5.Solver()
    gauge_cvc.setLogic("ALL")
    greal = gauge_cvc.getRealSort()
    c_gap = gauge_cvc.mkConst(greal, "gauge_gap")
    c_hol = gauge_cvc.mkConst(greal, "gauge_holonomy_gap")

    def grv(value: float) -> cvc5.Term:
        return gauge_cvc.mkReal(f"{value:.12f}")

    gauge_cvc.assertFormula(gauge_cvc.mkTerm(Kind.EQUAL, c_gap, grv(gauge_gap)))
    gauge_cvc.assertFormula(gauge_cvc.mkTerm(Kind.EQUAL, c_hol, grv(gauge_hol)))
    gauge_cvc.assertFormula(gauge_cvc.mkTerm(Kind.LT, c_gap, grv(TAU_GAUGE_GAP_MAX)))
    gauge_cvc.assertFormula(gauge_cvc.mkTerm(Kind.LT, c_hol, grv(TAU_HOLONOMY_GAP)))
    cvc_gauge_sat = gauge_cvc.checkSat()

    return {
        "z3": {
            "arithmetic_required_unsat_when_denied": str(z3_required_unsat),
            "gauge_equivalent_control_sat": str(z3_gauge_sat),
            "pass": bool(z3_required_unsat == z3.unsat and z3_gauge_sat == z3.sat),
        },
        "cvc5": {
            "arithmetic_required_unsat_when_denied": str(cvc_required_unsat),
            "gauge_equivalent_control_sat": str(cvc_gauge_sat),
            "pass": bool(cvc_required_unsat.isUnsat() and cvc_gauge_sat.isSat()),
        },
    }


def main() -> int:
    started = time.time()
    torch.manual_seed(2026051803)
    chart_report = chart_family_report()
    controls = controls_report()
    graph_tools = graph_topology_report(chart_report)
    math_tools = math_geometry_report(chart_report)
    lirpa = lirpa_report(chart_report)
    lewm = lewm_report(load_lewm_module(), chart_report)
    proof = proof_report(chart_report, controls)

    positive = {
        "chart_family_orientation_preserving": {
            "valid_charts": VALID_CHARTS,
            "min_derivative": min(row["derivative_min"] for row in chart_report["rows"]),
            "TAU_DERIVATIVE_MIN": TAU_DERIVATIVE_MIN,
            "pass": min(row["derivative_min"] for row in chart_report["rows"]) > TAU_DERIVATIVE_MIN,
        },
        "two_sheet_separation_survives_chart_reparameterization": {
            "min_basin_gap": min(row["basin_gap_min"] for row in chart_report["rows"]),
            "min_cosine": min(row["cosine_min"] for row in chart_report["rows"]),
            "max_cosine": max(row["cosine_max"] for row in chart_report["rows"]),
            "min_flux_delta": min(row["flux_delta_min"] for row in chart_report["rows"]),
            "pass": bool(
                min(row["basin_gap_min"] for row in chart_report["rows"]) > TAU_BASIN_GAP
                and min(row["cosine_min"] for row in chart_report["rows"]) > TAU_COSINE_LOWER
                and max(row["cosine_max"] for row in chart_report["rows"]) < TAU_COSINE_UPPER
                and min(row["flux_delta_min"] for row in chart_report["rows"]) > TAU_FLUX_DELTA
            ),
        },
        "sheet_holonomy_gap_survives_chart_family": {
            "min_holonomy_gap": min(row["holonomy_gap_min"] for row in chart_report["rows"]),
            "max_holonomy_gap": max(row["holonomy_gap_max"] for row in chart_report["rows"]),
            "TAU_HOLONOMY_GAP": TAU_HOLONOMY_GAP,
            "pass": min(row["holonomy_gap_min"] for row in chart_report["rows"]) > TAU_HOLONOMY_GAP,
        },
        "varying_g_structure_pressure_survives_chart_family": {
            "schedule_family_count": len(set(G_STRUCTURE_SCHEDULE)),
            "min_g_structure_control_gap": min(row["g_structure_min_control_gap"] for row in chart_report["rows"]),
            "all_charts_pass_g_structure": all(row["g_structure_all_pass"] for row in chart_report["rows"]),
            "pass": len(set(G_STRUCTURE_SCHEDULE)) == 3 and all(row["g_structure_all_pass"] for row in chart_report["rows"]),
        },
        "graph_topology_tools": graph_tools,
        "math_geometry_tools": {
            **math_tools,
            "pass": all(row.get("pass") is True for key, row in math_tools.items() if key != "pass"),
        },
        "auto_lirpa_chart_control_separation": lirpa,
        "lewm_chart_trajectory_pressure": lewm,
        "proof_tool_chart_arithmetic_witness": {
            "z3": proof["z3"],
            "cvc5": proof["cvc5"],
            "pass": bool(proof["z3"]["pass"] and proof["cvc5"]["pass"]),
        },
    }

    graveyard_companions = {
        **controls,
        "axis0_not_pass_condition": {
            "axis0_used_in_pass_condition": False,
            "reason": "The chart-invariance scout tests root manifold sheet geometry, not Axis0.",
            "pass": True,
        },
        "real_attractor_basin_claim_blocked": {
            "claim": "Chart-invariance under this finite fixture is not a real attractor-basin admission.",
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
            "chart_count": len(VALID_CHARTS),
            "phase_count": len(PHASES),
            "min_chart_derivative": min(row["derivative_min"] for row in chart_report["rows"]),
            "min_basin_gap": min(row["basin_gap_min"] for row in chart_report["rows"]),
            "max_basin_cosine": max(row["cosine_max"] for row in chart_report["rows"]),
            "min_flux_delta": min(row["flux_delta_min"] for row in chart_report["rows"]),
            "min_holonomy_gap": min(row["holonomy_gap_min"] for row in chart_report["rows"]),
            "g_structure_schedule_family_count": len(set(G_STRUCTURE_SCHEDULE)),
            "lirpa_separation_margin": lirpa["separation_margin"],
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
        "chart_rows": as_jsonable(chart_report["rows"]),
        "why_not_v4_probes": [
            "v5 root-manifold formal scout: Axis0 is excluded from the pass condition because manifold maturity is upstream",
            "tests whether the two-sheet ratchet signal survives smooth flux-chart reparameterization instead of only one coordinate chart",
            "formal scout only; no final manifold, basin, holonomy class, engine, axis, bridge, physics, target-system, or canonical claim is admitted",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_MANIFEST": EXTERNAL_MODULE_MANIFEST,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "blockers": [] if all_pass else ["root_manifold_g_structure_holonomy_chart_invariance_failed"],
    }
    OUT_PATH.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"name": NAME, "all_pass": bool(all_pass), "out_path": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
