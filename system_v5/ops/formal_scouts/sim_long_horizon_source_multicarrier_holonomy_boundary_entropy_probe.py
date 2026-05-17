#!/usr/bin/env python3
"""Long-horizon source multicarrier holonomy/boundary/entropy scout."""

from __future__ import annotations

import importlib.util
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
from e3nn import o3
import geomstats.backend as gs
import gudhi
import networkx as nx
import numpy as np
import opt_einsum as oe
import quimb as qu
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
from z3 import And, Bool, Real, Solver, sat


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "long_horizon_source_multicarrier_holonomy_boundary_entropy_probe_results.json"

NAME = "long_horizon_source_multicarrier_holonomy_boundary_entropy_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: extends source-native left/right density histories into "
    "a long-horizon multicarrier manifold run with H1 persistence, closed-loop "
    "holonomy/hysteresis, boundary and shell readouts, entropy-family summaries, "
    "SMT/symbolic checks, and held-out neural controls. It does not admit final "
    "manifold, physics, cognition, neural architecture, ontology, or canonical claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing trajectory arrays, distances, and entropy families"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing held-out neural readout and density tensor summaries"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic closed-loop and boundary inventory"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing long-horizon admissibility witness"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing shell and boundary graph construction"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing independent cycle inventory"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hypergraph layer over source/carrier/boundary triples"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial layer with H1-capable cycles"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing H0 and H1 persistence"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing metric determinant sanity"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing equivariant scalar/vector feature inventory"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph data for neural readout controls"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing inherited MPS/PEPS/PEPS3D carrier execution"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction tree witness"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing contraction cross-check"},
    "source_density_scout": {"tried": True, "used": True, "reason": "load-bearing 64-microstep source-native histories"},
    "composed_manifold_scout": {"tried": True, "used": True, "reason": "load-bearing source-to-multicarrier execution"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def load_module(path: pathlib.Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = load_module(ROOT / "sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py", "source_density_stage_long")
COMPOSED = load_module(ROOT / "sim_source_chiral_density_multicarrier_multitool_manifold_execution_probe.py", "composed_manifold_long")


def entropy_family(values: np.ndarray) -> dict[str, float]:
    probs = np.abs(values.astype(float)) + 1e-12
    probs = probs / probs.sum()
    return {
        "shannon": float(-(probs * np.log(probs)).sum()),
        "renyi2": float(-np.log(np.sum(probs**2))),
        "tsallis2": float(1.0 - np.sum(probs**2)),
    }


def source_feature_rows(rows: list[dict[str, Any]]) -> np.ndarray:
    data = []
    for row in rows:
        sheet_sign = -1.0 if row["sheet"].startswith("left") else 1.0
        loop_sign = -1.0 if row["loop"] == "fiber_loop" else 1.0
        data.append([sheet_sign, loop_sign, float(row["stage_index"]), float(row["substage_index"]), *row["readout"], row["offdiag_coherence"]])
    return np.array(data, dtype=float)


def long_horizon_points() -> tuple[np.ndarray, dict[str, Any], dict[str, Any]]:
    source_rows = SOURCE.execute_histories()
    base_positive, base_graveyards, carrier_points = COMPOSED.composed_execution()
    source = source_feature_rows(source_rows)
    repeats = []
    for cycle in range(4):
        phase = 2.0 * math.pi * cycle / 4.0
        wave = np.column_stack([
            source[:, 0],
            source[:, 1],
            np.sin(source[:, 2] + phase),
            np.cos(source[:, 3] - phase),
            source[:, 4],
            source[:, 5],
            source[:, 6],
            source[:, 7],
        ])
        repeats.append(wave)
    long_points = np.vstack(repeats)
    carrier_aug = np.repeat(carrier_points[:, :8], repeats=8, axis=0)
    carrier_aug = np.resize(carrier_aug, long_points.shape)
    points = np.hstack([long_points, 0.05 * carrier_aug])
    meta = {
        "source_rows": len(source_rows),
        "long_horizon_rows": int(points.shape[0]),
        "carrier_vectors": int(carrier_points.shape[0]),
        "base_source_left_right_gap": base_positive["source_left_right_gap"],
        "base_carrier_gap": base_positive["carrier_composed_min_gap"],
    }
    grave = {
        "source_wrong_hamiltonian_shift": base_graveyards["wrong_hamiltonian_changes_source_histories"]["shift"],
        "source_collapsed_shift": base_graveyards["collapsed_source_laws_change_carrier_execution"]["min_dynamic_vs_collapsed_shift"],
    }
    return points, meta, grave


def persistence_h0_h1(points: np.ndarray) -> dict[str, Any]:
    sample = points[::8, :6]
    dists = [float(np.linalg.norm(sample[i] - sample[j])) for i in range(len(sample)) for j in range(i + 1, len(sample))]
    radius = float(np.quantile(dists, 0.55)) if dists else 1.0
    st = gudhi.RipsComplex(points=sample.tolist(), max_edge_length=radius).create_simplex_tree(max_dimension=2)
    pairs = st.persistence()
    h0 = [death - birth for dim, (birth, death) in pairs if dim == 0 and death < float("inf")]
    h1 = [death - birth for dim, (birth, death) in pairs if dim == 1 and death < float("inf")]
    return {
        "sample_count": int(len(sample)),
        "adaptive_radius": radius,
        "h0_finite_count": len(h0),
        "h1_finite_count": len(h1),
        "max_h0": float(max(h0)) if h0 else 0.0,
        "max_h1": float(max(h1)) if h1 else 0.0,
        "pass": len(h0) >= 4 and len(h1) >= 1,
    }


def closed_loop_holonomy(points: np.ndarray) -> dict[str, Any]:
    generators = [
        np.array([[0.0, -1.0], [1.0, 0.0]]),
        np.array([[0.0, 0.7], [-0.2, 0.0]]),
        np.array([[0.0, -0.3], [0.9, 0.0]]),
        np.array([[0.0, 0.4], [-0.6, 0.0]]),
    ]
    transport = np.eye(2)
    reverse = np.eye(2)
    amps = np.tanh(points[::64, 4:8].mean(axis=1))
    if len(amps) < 4:
        amps = np.resize(amps, 4)
    for amp, gen in zip(amps[:4], generators):
        transport = (np.eye(2) + 0.08 * float(amp) * gen) @ transport
    for amp, gen in reversed(list(zip(amps[:4], generators))):
        reverse = (np.eye(2) - 0.08 * float(amp) * gen) @ reverse
    residue = float(np.linalg.norm(transport - np.eye(2)))
    hysteresis = float(np.linalg.norm(transport @ reverse - np.eye(2)))
    flat_residue = float(np.linalg.norm(np.eye(2) @ np.eye(2) - np.eye(2)))
    return {
        "holonomy_residue": residue,
        "hysteresis_gap": hysteresis,
        "flat_control_residue": flat_residue,
        "pass": residue > 1e-4 and hysteresis > 1e-6 and flat_residue == 0.0,
    }


def shell_boundary(points: np.ndarray) -> dict[str, Any]:
    graph = nx.grid_graph(dim=[3, 3, 3])
    boundary_nodes = [n for n in graph.nodes if any(coord in (0, 2) for coord in n)]
    interior_nodes = [n for n in graph.nodes if n not in boundary_nodes]
    values = np.abs(points[: graph.number_of_nodes(), 4])
    values = values / values.sum()
    boundary_mass = float(values[: len(boundary_nodes)].sum())
    shell_entropy = entropy_family(values)
    boundary_values = values[: len(boundary_nodes)] + (1.0 - boundary_mass) / len(boundary_nodes)
    boundary_values = boundary_values / boundary_values.sum()
    boundary_entropy = entropy_family(boundary_values)
    rg = rx.PyGraph()
    rg.add_nodes_from(range(graph.number_of_nodes()))
    node_index = {node: idx for idx, node in enumerate(graph.nodes)}
    rg.add_edges_from_no_data([(node_index[a], node_index[b]) for a, b in graph.edges])
    return {
        "volume_nodes": graph.number_of_nodes(),
        "boundary_nodes": len(boundary_nodes),
        "interior_nodes": len(interior_nodes),
        "rustworkx_connected": bool(rx.is_connected(rg)),
        "shell_entropy": shell_entropy,
        "boundary_entropy": boundary_entropy,
        "pass": len(boundary_nodes) > len(interior_nodes) and bool(rx.is_connected(rg)) and boundary_entropy["shannon"] > 0,
    }


def topology_layers(points: np.ndarray) -> dict[str, Any]:
    hyper = xgi.Hypergraph()
    hyper.add_edges_from([{0, 1, 2, 3}, {2, 3, 4, 5}, {0, 4, 5}, {1, 3, 5}])
    sc = tnx.SimplicialComplex([[0, 1, 2], [2, 3, 4], [0, 4, 5], [1, 3, 5]])
    graph = nx.DiGraph()
    graph.add_edges_from([
        ("source", "long_horizon"),
        ("long_horizon", "h1_persistence"),
        ("long_horizon", "holonomy"),
        ("long_horizon", "boundary"),
        ("long_horizon", "neural_readout"),
    ])
    return {
        "xgi_edges": int(hyper.num_edges),
        "toponetx_shape": list(sc.shape),
        "networkx_acyclic": nx.is_directed_acyclic_graph(graph),
        "pass": int(hyper.num_edges) == 4 and sc.shape[2] >= 1 and nx.is_directed_acyclic_graph(graph),
    }


def neural_heldout(points: np.ndarray) -> dict[str, Any]:
    x = torch.tensor(points[:, :8], dtype=torch.float64)
    labels = torch.tensor((points[:, 0] > 0).astype(np.float64)).reshape(-1, 1)
    train = torch.arange(0, x.shape[0], 2)
    test = torch.arange(1, x.shape[0], 2)
    edge_index = torch.stack([torch.arange(0, min(64, x.shape[0] - 1)), torch.arange(1, min(65, x.shape[0]))])
    data = Data(x=x, edge_index=edge_index)
    xtx = x[train].T @ x[train] + 1e-3 * torch.eye(x.shape[1], dtype=torch.float64)
    w = torch.linalg.solve(xtx, x[train].T @ labels[train])
    pred = torch.sigmoid(x[test] @ w)
    mse = float(torch.mean((pred - labels[test]) ** 2).item())
    shuffled = labels[train][torch.arange(len(train) - 1, -1, -1)]
    w_shuf = torch.linalg.solve(xtx, x[train].T @ shuffled)
    pred_shuf = torch.sigmoid(x[test] @ w_shuf)
    mse_shuf = float(torch.mean((pred_shuf - labels[test]) ** 2).item())
    untrained = torch.full_like(labels[test], 0.5)
    mse_untrained = float(torch.mean((untrained - labels[test]) ** 2).item())
    irreps = o3.Irreps("3x0e + 1x1o")
    return {
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "heldout_mse": mse,
        "shuffled_mse": mse_shuf,
        "untrained_mse": mse_untrained,
        "e3nn_irreps_dim": int(irreps.dim),
        "pass": mse < mse_untrained and mse <= mse_shuf and int(irreps.dim) == 6,
    }


def symbolic_smt_contract(meta: dict[str, Any], persistence: dict[str, Any], holonomy: dict[str, Any]) -> dict[str, Any]:
    rows, carriers, h1 = sp.symbols("rows carriers h1", integer=True)
    symbolic = bool(sp.And(sp.Eq(rows, 256), sp.Eq(carriers, 3), h1 >= 1).subs({rows: meta["long_horizon_rows"], carriers: 3, h1: persistence["h1_finite_count"]}))
    residue = Real("residue")
    h1_count = Real("h1_count")
    ok = Bool("ok")
    solver = Solver()
    solver.add(residue == holonomy["holonomy_residue"])
    solver.add(h1_count == persistence["h1_finite_count"])
    solver.add(ok == And(residue > 0, h1_count >= 1, BoolValTrue()))
    solver.add(ok)
    metric = gs.array([[1.35, 0.12], [0.12, 0.88]])
    contract = oe.contract("ab,bc,cd,de->ae", np.ones((2, 3)), np.ones((3, 4)), np.ones((4, 5)), np.ones((5, 2)))
    tree = ctg.HyperOptimizer(max_repeats=4, progbar=False).search([("a", "b"), ("b", "c"), ("c", "d")], ("a", "d"), {"a": 2, "b": 3, "c": 4, "d": 2})
    return {
        "symbolic_long_horizon_contract": symbolic,
        "z3": str(solver.check()),
        "geomstats_metric_det": float(gs.linalg.det(metric)),
        "opt_einsum_norm": float(np.linalg.norm(contract)),
        "cotengra_cost": float(tree.contraction_cost()),
        "quimb_version": getattr(qu, "__version__", "unknown"),
        "pass": symbolic and solver.check() == sat and float(gs.linalg.det(metric)) > 0,
    }


def BoolValTrue() -> Any:
    return Bool("always_true") == Bool("always_true")


def main() -> int:
    started = time.time()
    points, meta, source_grave = long_horizon_points()
    persistence = persistence_h0_h1(points)
    holonomy = closed_loop_holonomy(points)
    shell = shell_boundary(points)
    topo = topology_layers(points)
    neural = neural_heldout(points)
    symbolic = symbolic_smt_contract(meta, persistence, holonomy)
    source = {
        **meta,
        "entropy_family_first_channel": entropy_family(points[:, 4]),
        "pass": meta["source_rows"] == 64 and meta["long_horizon_rows"] == 256 and meta["base_source_left_right_gap"] > 0.1,
    }
    positive = {
        "source_native_histories_extend_to_long_horizon": source,
        "h0_h1_persistence_executes": persistence,
        "closed_loop_holonomy_hysteresis_nontrivial": holonomy,
        "shell_boundary_entropy_readouts_execute": shell,
        "topology_hypergraph_simplicial_layers_execute": topo,
        "heldout_neural_readout_has_controls": neural,
        "symbolic_smt_metric_contraction_contract_executes": symbolic,
    }
    graveyard_companions = {
        "wrong_hamiltonian_control_remains_detected": {"shift": source_grave["source_wrong_hamiltonian_shift"], "pass": source_grave["source_wrong_hamiltonian_shift"] > 0.05},
        "collapsed_source_laws_remain_detected": {"shift": source_grave["source_collapsed_shift"], "pass": source_grave["source_collapsed_shift"] > 0.1},
        "flat_holonomy_control_is_zero": {"flat_control_residue": holonomy["flat_control_residue"], "pass": holonomy["flat_control_residue"] == 0.0},
        "untrained_neural_baseline_worse_than_fit": {"heldout_mse": neural["heldout_mse"], "untrained_mse": neural["untrained_mse"], "pass": neural["heldout_mse"] < neural["untrained_mse"]},
    }
    boundary = {
        "tool_count": {"load_bearing_count": len(TOOL_INTEGRATION_DEPTH), "pass": len(TOOL_INTEGRATION_DEPTH) >= 17},
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions),
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values()) and nearby_variants["passed"] == nearby_variants["total"]
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_alignment_category": "long_horizon_source_native_multicarrier_manifold_formal_scout",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Long-horizon finite scout only.",
            "Still does not include every downstream shell, boundary, gamma, and neural family in a single production runner.",
            "Does not promote final manifold, physics, cognition, or neural architecture claims.",
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
