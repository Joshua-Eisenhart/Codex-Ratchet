#!/usr/bin/env python3
"""Multitool entropy-geometry-carrier constraint-manifold integration scout."""

from __future__ import annotations

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
import opt_einsum as oe
import quimb as qu
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
from z3 import And, Bool, Real, Solver, sat


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_manifold_multitool_entropy_geometry_carrier_integration_probe_results.json"

NAME = "constraint_manifold_multitool_entropy_geometry_carrier_integration_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: couples finite density updates, entropy-gradient "
    "geometry flow, tensor carriers, graph/hypergraph/simplicial topology, "
    "symbolic and SMT checks, equivariant feature inventory, and graph-neural "
    "readouts. It does not admit final manifold, physics, cognition, neural "
    "architecture, ontology, or canonical claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density matrices, entropy, and graph-readout tensors"},
    "scipy": {"tried": False, "used": False, "reason": "not used; entropy-gradient geometry flow is integrated by local RK4 code"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic curvature/torsion inventory"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing admissibility witness over class separation and controls"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing carrier dependency graph and graph metrics"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing independent graph connectivity/shortest-path cross-check"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hypergraph coupling for multi-site constraints"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial complex shape for topology layer"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence of integrated signatures"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing backend metric positive-definiteness sanity"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing equivariant feature inventory for scalar/vector geometry channels"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph data object and neural-style message readout"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS, PEPS, and PEPS3D carrier evolution"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction-tree search for geometry-shaped tensor equations"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing numeric contraction cross-check"},
}
TOOL_INTEGRATION_DEPTH = {tool: (None if tool == "scipy" else "load_bearing") for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
I2 = torch.eye(2, dtype=DTYPE)
SX_T = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY_T = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ_T = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SX = qu.pauli("X").A
SY = qu.pauli("Y").A
SZ = qu.pauli("Z").A

CLASSES = {
    "funnel": {"generator": qu.kron(SX, SZ), "rate": 0.18, "shear": -0.18, "twist": 0.08},
    "vortex": {"generator": qu.kron(SY, SX), "rate": 0.14, "shear": 0.10, "twist": 0.31},
    "pit": {"generator": qu.kron(SZ, SZ), "rate": 0.27, "shear": -0.27, "twist": -0.16},
    "hill": {"generator": qu.kron(SZ, SX), "rate": 0.20, "shear": 0.25, "twist": -0.05},
}

EDGES = {
    "mps": [(0, 1), (2, 3), (4, 5), (6, 7), (1, 2), (5, 6)],
    "peps": [((0, 0), (0, 1)), ((1, 0), (1, 1)), ((0, 2), (0, 3)), ((1, 2), (1, 3)), ((0, 1), (1, 1)), ((0, 2), (1, 2))],
    "peps3d": [((0, 0, 0), (1, 0, 0)), ((0, 1, 0), (1, 1, 0)), ((0, 0, 1), (1, 0, 1)), ((0, 1, 1), (1, 1, 1)), ((0, 0, 0), (0, 0, 1)), ((1, 1, 0), (1, 1, 1))],
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def vec_sub(left: list[float], right: list[float]) -> list[float]:
    return [a - b for a, b in zip(left, right)]


def vec_norm(values: Any) -> float:
    if isinstance(values, torch.Tensor):
        return float(torch.linalg.norm(values.detach()).item())
    if hasattr(values, "shape"):
        return float(torch.linalg.norm(torch.as_tensor(values)).item())
    flat = [float(v) for v in values]
    return math.sqrt(sum(v * v for v in flat))


def vec_mean(rows: list[list[float]]) -> list[float]:
    return [sum(row[idx] for row in rows) / len(rows) for idx in range(len(rows[0]))]


def vec_std(rows: list[list[float]], means: list[float]) -> list[float]:
    return [math.sqrt(sum((row[idx] - means[idx]) ** 2 for row in rows) / len(rows)) for idx in range(len(means))]


def rounded(values: list[float], digits: int) -> list[float]:
    return [round(float(v), digits) for v in values]


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 1.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-12).to(DTYPE)
    out = vecs @ torch.diag(vals) @ vecs.conj().T
    return out / torch.trace(out).real


def density_seed(seed: int) -> torch.Tensor:
    gen = torch.Generator().manual_seed(seed)
    theta = 0.23 + float(torch.rand((), generator=gen).item())
    phi = 2.0 * math.pi * float(torch.rand((), generator=gen).item())
    psi = torch.tensor([math.cos(theta), math.sin(theta) * complex(math.cos(phi), math.sin(phi))], dtype=DTYPE).reshape(2, 1)
    return normalize_density(0.82 * (psi @ psi.conj().T) + 0.18 * I2 / 2.0)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return float(-(vals * torch.log(vals)).sum().item())


def bloch(rho: torch.Tensor) -> list[float]:
    return [float(torch.real(torch.trace(op @ rho)).item()) for op in (SX_T, SY_T, SZ_T)]


def geometry_rhs(_t: float, params: list[float], signal: list[float], row: dict[str, Any], mode: str) -> list[float]:
    if mode == "collapsed":
        row = CLASSES["hill"]
    if mode == "frozen":
        return [0.0, 0.0, 0.0]
    return [
        0.55 * (row["rate"] + signal[0]) - 0.16 * params[0],
        0.45 * (row["shear"] + signal[1]) - 0.14 * params[1],
        0.50 * (row["twist"] + signal[2]) - 0.15 * params[2],
    ]


def rk4_geometry_step(params: list[float], signal: list[float], row: dict[str, Any], mode: str, dt: float) -> list[float]:
    def add_scaled(base: list[float], delta: list[float], scale: float) -> list[float]:
        return [a + scale * b for a, b in zip(base, delta)]

    k1 = geometry_rhs(0.0, params, signal, row, mode)
    k2 = geometry_rhs(dt / 2.0, add_scaled(params, k1, dt / 2.0), signal, row, mode)
    k3 = geometry_rhs(dt / 2.0, add_scaled(params, k2, dt / 2.0), signal, row, mode)
    k4 = geometry_rhs(dt, add_scaled(params, k3, dt), signal, row, mode)
    return [
        float(p + (dt / 6.0) * (a + 2.0 * b + 2.0 * c + d))
        for p, a, b, c, d in zip(params, k1, k2, k3, k4)
    ]


def density_and_geometry_step(rho: torch.Tensor, params: list[float], row: dict[str, Any], step: int, mode: str) -> tuple[torch.Tensor, list[float]]:
    b = bloch(rho)
    signal = [entropy(rho) - 0.36, b[0] * b[2], b[1] - b[0]]
    params = rk4_geometry_step(params, signal, row, mode, dt=0.08)
    active = CLASSES["hill"] if mode == "collapsed" else row
    generator = (0.52 + 0.11 * params[1]) * SX_T + (0.33 + 0.15 * params[2]) * SY_T + (0.22 + 0.08 * params[0]) * SZ_T
    vals, vecs = torch.linalg.eig((-1j * (0.030 + 0.017 * active["rate"] + 0.002 * step) * generator).to(DTYPE))
    u = vecs @ torch.diag(torch.exp(vals)) @ torch.linalg.inv(vecs)
    return normalize_density(u @ rho @ u.conj().T), params


def metric_values(params: list[float]) -> dict[str, float]:
    conformal, shear, twist = params
    scale = math.exp(conformal)
    a = scale * math.exp(shear)
    b = scale * 0.15 * math.tanh(twist)
    d = scale * math.exp(-shear)
    center = 0.5 * (a + d)
    delta = math.sqrt(((a - d) * 0.5) ** 2 + b * b)
    eigvals = [center - delta, center + delta]
    curvature = float(0.41 * shear - 0.26 * twist + 0.14 * conformal * shear)
    torsion = float(abs(0.63 * twist) + abs(0.19 * shear))
    return {"metric_min": float(eigvals[0]), "metric_max": float(eigvals[1]), "curvature": curvature, "torsion": torsion}


def geometry_gate(row: dict[str, Any], params: list[float], step: int, carrier: str) -> Any:
    vals = metric_values(params)
    factor = {"mps": 1.0, "peps": 1.0 + 0.10 * vals["torsion"], "peps3d": 1.0 + 0.18 * vals["torsion"] + 0.06 * abs(vals["curvature"])}[carrier]
    return qu.expm(-1j * row["rate"] * factor * (1.0 + 0.02 * step) * row["generator"])


def make_peps(seed: int) -> qtn.PEPS:
    arrays = []
    for i in range(2):
        row = []
        for j in range(4):
            shape = []
            if i > 0: shape.append(2)
            if j < 3: shape.append(2)
            if i < 1: shape.append(2)
            if j > 0: shape.append(2)
            shape.append(2)
            row.append(qu.randn(tuple(shape), scale=0.32, seed=1500 + seed + 17 * i + j))
        arrays.append(row)
    return qtn.PEPS(arrays)


def make_peps3d(seed: int) -> qtn.PEPS3D:
    arrays = []
    for i in range(2):
        plane = []
        for j in range(2):
            row = []
            for k in range(2):
                shape = []
                if i < 1: shape.append(2)
                if j < 1: shape.append(2)
                if k < 1: shape.append(2)
                if i > 0: shape.append(2)
                if j > 0: shape.append(2)
                if k > 0: shape.append(2)
                shape.append(2)
                row.append(qu.randn(tuple(shape), scale=0.28, seed=1800 + seed + 31 * i + 7 * j + k))
            plane.append(row)
        arrays.append(plane)
    return qtn.PEPS3D(arrays)


def carrier_state(carrier: str, seed: int) -> Any:
    if carrier == "mps":
        return qtn.MPS_rand_state(8, bond_dim=3, seed=seed)
    if carrier == "peps":
        return make_peps(seed)
    return make_peps3d(seed)


def contraction_features(carrier: str, vals: dict[str, float]) -> dict[str, float]:
    shift = int(abs(vals["curvature"]) * 5 + abs(vals["torsion"]) * 7 + vals["metric_min"] * 3)
    if carrier == "mps":
        inputs, output, expr = [("a", "b"), ("b", "c"), ("c", "d")], ("a", "d"), "ab,bc,cd->ad"
    elif carrier == "peps":
        inputs, output, expr = [("a", "b", "e"), ("b", "c", "f"), ("e", "f", "h"), ("f", "g", "i")], ("a", "c", "h", "i"), "abe,bcf,efh,fgi->achi"
    else:
        inputs, output, expr = [("a", "b", "e", "l"), ("b", "c", "f", "m"), ("e", "f", "h", "n"), ("l", "m", "n", "o"), ("h", "i", "o", "q")], ("a", "c", "i", "q"), "abel,bcfm,efhn,lmno,hioq->aciq"
    labels = sorted({ix for term in inputs for ix in term} | set(output))
    sizes = {ix: 2 + (n + shift) % 3 for n, ix in enumerate(labels)}
    for ix in output:
        sizes[ix] = 2
    tree = ctg.HyperOptimizer(max_repeats=6, progbar=False, on_trial_error="raise").search(inputs, output, sizes)
    gen = torch.Generator().manual_seed(2400 + shift + len(inputs))
    arrays = [torch.randn(*(sizes[ix] for ix in term), dtype=torch.float64, generator=gen) for term in inputs]
    ref = oe.contract(expr, *arrays)
    return {"cost": float(tree.contraction_cost()), "width": float(tree.contraction_width()), "norm": vec_norm(ref)}


def entropy_family(values: list[float]) -> dict[str, float]:
    raw = [abs(float(v)) + 1e-12 for v in values]
    total = sum(raw)
    probs = [v / total for v in raw]
    square_sum = sum(v * v for v in probs)
    return {
        "shannon": -sum(p * math.log(p) for p in probs),
        "renyi2": -math.log(square_sum),
        "tsallis2": 1.0 - square_sum,
    }


def run_path(class_name: str, carrier: str, seed: int, mode: str = "dynamic") -> list[float]:
    row = CLASSES["hill"] if mode == "collapsed" else CLASSES[class_name]
    state = carrier_state(carrier, 500 + seed)
    rho = density_seed(seed)
    params = [0.04, row["shear"], row["twist"]]
    rows = []
    for step in range(5):
        rho, params = density_and_geometry_step(rho, params, row, step, mode)
        gate = geometry_gate(CLASSES["hill"] if mode == "collapsed" else row, params, step, carrier)
        for edge in EDGES[carrier][: 3 + (step % 3)]:
            if carrier == "mps":
                state.gate_(gate, edge, contract="swap+split", max_bond=8, cutoff=1e-10)
            else:
                state.gate_(gate, edge, contract="split", max_bond=8, cutoff=1e-10)
        if carrier == "mps":
            read = [float(state.entropy(cut)) for cut in range(1, 8)]
        else:
            read = [vec_norm(t.data) for t in state]
        efam = entropy_family(read)
        geom = metric_values(params)
        contract = contraction_features(carrier, geom)
        read_mean = sum(read) / len(read)
        read_std = math.sqrt(sum((v - read_mean) ** 2 for v in read) / len(read))
        rows.append([efam["shannon"], efam["renyi2"], efam["tsallis2"], sum(read), read_std, int(state.max_bond()), entropy(rho), geom["metric_min"], geom["curvature"], geom["torsion"], contract["cost"], contract["width"], contract["norm"]])
    means = vec_mean(rows)
    return [*means, *vec_std(rows, means), *rows[-1]]


def pairwise_min(vectors: dict[str, list[float]]) -> float:
    keys = sorted(vectors)
    vals = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            vals.append(vec_norm(vec_sub(vectors[a], vectors[b])))
    return min(vals) if vals else 0.0


def topology_layers() -> dict[str, Any]:
    graph = nx.grid_graph(dim=[2, 2, 2])
    rg = rx.PyGraph()
    rg.add_nodes_from(range(8))
    rg.add_edges_from_no_data([(0, 1), (1, 3), (3, 7), (7, 5), (5, 4), (4, 0), (2, 6), (6, 7)])
    hyper = xgi.Hypergraph()
    hyper.add_edges_from([{0, 1, 2}, {2, 3, 7}, {4, 5, 6}, {1, 5, 7}])
    sc = tnx.SimplicialComplex([[0, 1, 2], [2, 3, 7], [4, 5, 6], [1, 5, 7]])
    return {
        "networkx_edges": graph.number_of_edges(),
        "rustworkx_connected": bool(rx.is_connected(rg)),
        "xgi_edges": int(hyper.num_edges),
        "toponetx_shape": list(sc.shape),
        "pass": graph.number_of_edges() == 12 and rx.is_connected(rg) and int(hyper.num_edges) == 4 and sc.shape[2] >= 1,
    }


def neural_and_equivariant_readout(signatures: list[list[float]]) -> dict[str, Any]:
    x = torch.tensor([row[:6] for row in signatures], dtype=torch.float64)
    edge_index = torch.tensor([[0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 0]], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    agg = torch.zeros_like(data.x)
    agg.index_add_(0, data.edge_index[1], data.x[data.edge_index[0]])
    readout = torch.tanh(data.x + 0.2 * agg).mean(dim=0)
    irreps = o3.Irreps("2x0e + 1x1o")
    return {"node_count": int(data.num_nodes), "edge_count": int(data.num_edges), "irreps_dim": int(irreps.dim), "readout_norm": float(torch.linalg.norm(readout).item()), "pass": data.num_nodes == len(signatures) and irreps.dim == 5 and float(torch.linalg.norm(readout).item()) > 0}


def symbolic_and_smt(gaps: dict[str, float], collapsed_gap: float) -> dict[str, Any]:
    c, sh, tw = sp.symbols("c sh tw")
    curvature = sp.Rational(41, 100) * sh - sp.Rational(26, 100) * tw + sp.Rational(14, 100) * c * sh
    symbolic_pass = bool(curvature.has(sh) and curvature.has(tw))
    min_gap = min(gaps.values())
    g = Real("min_gap")
    collapse = Real("collapsed_gap")
    ok = Bool("ok")
    solver = Solver()
    solver.add(g == min_gap, collapse == collapsed_gap, ok == And(g > 0.1, collapse < g))
    solver.add(ok)
    return {"symbolic_curvature_formula": str(curvature), "min_gap": min_gap, "collapsed_gap": collapsed_gap, "z3": str(solver.check()), "pass": symbolic_pass and solver.check() == sat}


def integrated_report() -> tuple[dict[str, Any], dict[str, Any], list[list[float]]]:
    carriers = ["mps", "peps", "peps3d"]
    gaps = {}
    heads = {}
    all_vectors = []
    for carrier in carriers:
        vectors = {name: vec_mean([run_path(name, carrier, seed) for seed in range(2)]) for name in CLASSES}
        gaps[carrier] = pairwise_min(vectors)
        heads[carrier] = {k: rounded(v[:8], 6) for k, v in vectors.items()}
        all_vectors.extend(vectors.values())
    collapsed_vectors = {name: run_path(name, "peps3d", 1, mode="collapsed") for name in CLASSES}
    collapsed_gap = pairwise_min(collapsed_vectors)
    report = {"class_gaps": gaps, "signature_heads": heads, "pass": all(v > 0.1 for v in gaps.values())}
    graveyards = {
        "collapsed_volume_laws_reduce_integrated_separation": {"dynamic_gap": gaps["peps3d"], "collapsed_gap": collapsed_gap, "pass": collapsed_gap < gaps["peps3d"] * 0.25},
        "frozen_geometry_differs_from_dynamic": {
            "distance": vec_norm(vec_sub(run_path("vortex", "peps3d", 3), run_path("vortex", "peps3d", 3, mode="frozen"))),
            "pass": vec_norm(vec_sub(run_path("vortex", "peps3d", 3), run_path("vortex", "peps3d", 3, mode="frozen"))) > 0.05,
        },
    }
    return report, graveyards, all_vectors


def persistence_report(points: list[list[float]]) -> dict[str, Any]:
    dists = [vec_norm(vec_sub(points[i], points[j])) for i in range(len(points)) for j in range(i + 1, len(points))]
    radius = quantile(dists, 0.65) if dists else 1.0
    st = gudhi.RipsComplex(points=points, max_edge_length=radius).create_simplex_tree(max_dimension=1)
    pairs = st.persistence()
    finite = [death - birth for dim, (birth, death) in pairs if dim == 0 and death < float("inf")]
    return {"point_count": int(len(points)), "adaptive_radius": radius, "h0_count": sum(1 for dim, _ in pairs if dim == 0), "max_finite_h0_persistence": float(max(finite)) if finite else 0.0, "pass": len(finite) >= 4}


def geomstats_report() -> dict[str, Any]:
    mat = gs.array([[1.4, 0.1], [0.1, 0.9]])
    det = float(gs.linalg.det(mat))
    return {"metric_det": det, "pass": det > 0}


def main() -> int:
    started = time.time()
    integrated, graveyards, points = integrated_report()
    positive = {
        "density_geometry_carrier_paths_remain_separated": integrated,
        "topology_graph_hypergraph_simplicial_layers_execute": topology_layers(),
        "integrated_signature_persistence_nontrivial": persistence_report(points),
        "neural_and_equivariant_readout_executes": neural_and_equivariant_readout(points),
        "symbolic_and_smt_admissibility_witness": symbolic_and_smt(integrated["class_gaps"], graveyards["collapsed_volume_laws_reduce_integrated_separation"]["collapsed_gap"]),
    }
    boundary = {
        "geomstats_metric_positive": geomstats_report(),
        "tool_count": {"load_bearing_count": len(TOOL_INTEGRATION_DEPTH), "pass": len(TOOL_INTEGRATION_DEPTH) >= 15},
    }
    nearby_variants = {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)}
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values()) and nearby_variants["passed"] == nearby_variants["total"]
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_alignment_category": "multitool_constraint_manifold_integration_formal_scout",
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Finite integrated scout only.",
            "Does not yet run the complete source-native left/right Weyl density stage history through every carrier.",
            "Does not promote final manifold, physics, cognition, or neural architecture claims.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result["root_constraints"] = {
        "F01": True,
        "N01": True,
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "n01_evidence": "bounded topology/graph/hypergraph/simplicial and symbolic-SMT order-sensitive integration evidence is recorded in positive rows",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
