#!/usr/bin/env python3
"""
sim_integration_symbolic_graph_manifold_stack.py

Curated bridge-stack reference sim for:
  pytorch + z3 + cvc5 + sympy + clifford + pyg + rustworkx + xgi +
  toponetx + gudhi + datasketch + pynndescent + umap + hdbscan + sklearn

Claim:
graph-family descriptors extracted from one shared solver/topology/geometry
surface should stay clusterable under manifold tools when the carrier bank is
coherent, degrade when features are collapsed, and remain mostly recoverable at
boundary noise. This is a reusable integration witness, not a nonclassical
claim.

Positive: clean cycle/star/path family bank.
Negative: same extracted families but aggressively collapsed into aliased
  manifold signatures.
Boundary: moderately mixed family bank.
"""

from __future__ import annotations

import json
import math
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cvc5
import gudhi
import hdbscan
import rustworkx as rx
import sympy as sp
import torch
import umap
import xgi
from clifford import Cl
from cvc5 import Kind
from datasketch import MinHash, MinHashLSH
from pynndescent import NNDescent
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from toponetx.classes import SimplicialComplex
from torch_geometric.data import Data
from torch_geometric.utils import degree as pyg_degree
from torch_geometric.utils import to_dense_adj
from z3 import Ints, Solver, sat


classification = "classical_baseline"
divergence_log = (
    "Classical integration baseline: this bridge stack joins solver, rotor, "
    "graph, hypergraph, simplicial, persistence, ANN, manifold, clustering, "
    "and sklearn metric surfaces on one shared graph-family bank."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor carrier for coordinates, adjacency aggregation, feature assembly, and collapse blending",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tree-law satisfiability witness over each extracted graph family",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT cross-check of the same tree-law witness",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Laplacian spectral-root witness per graph sample",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing rotor coordinates for cycle and star families",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph tensor surface for dense adjacency and degree signatures",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing diameter and connected-component witness",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hypergraph degree and line-graph witness",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial incidence witness over the same 1-skeleton",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Rips reconstruction witness from the carrier coordinates",
    },
    "datasketch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MinHash/LSH witness over discretized graph-family descriptors",
    },
    "pynndescent": {
        "tried": True,
        "used": True,
        "reason": "load-bearing approximate nearest-neighbor purity witness over extracted feature vectors",
    },
    "umap": {
        "tried": True,
        "used": True,
        "reason": "load-bearing manifold embedding witness for the graph-family bank",
    },
    "hdbscan": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density clustering witness on the manifold embedding",
    },
    "sklearn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing scaling and clustering-quality metrics over the shared embedding",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "datasketch": "load_bearing",
    "pynndescent": "load_bearing",
    "umap": "load_bearing",
    "hdbscan": "load_bearing",
    "sklearn": "load_bearing",
}

FAMILY_LABELS = {"cycle": 0, "star": 1, "path": 2}
FAMILY_ORDER = ["cycle", "star", "path"]
SAMPLES_PER_FAMILY = 8


def _rotated_points(angles: list[float]) -> torch.Tensor:
    _, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e12 = blades["e12"]
    coords = []
    for theta in angles:
        rotor = math.cos(theta / 2.0) + math.sin(theta / 2.0) * e12
        vec = rotor * e1 * ~rotor
        coords.append([float(vec[e1]), float(vec[e2])])
    return torch.tensor(coords, dtype=torch.float32)


def _deterministic_jitter(sample_index: int, count: int, scale: float) -> torch.Tensor:
    if scale <= 0.0:
        return torch.zeros((count, 2), dtype=torch.float32)
    values = []
    base = float(sample_index + 1)
    for idx in range(count):
        dx = scale * math.sin(base * 0.73 + idx * 1.11)
        dy = scale * math.cos(base * 0.41 + idx * 0.89)
        values.append([dx, dy])
    return torch.tensor(values, dtype=torch.float32)


def _shape_spec(kind: str, sample_index: int, jitter_scale: float) -> tuple[torch.Tensor, list[tuple[int, int]], float]:
    if kind == "cycle":
        coords = _rotated_points([0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0])
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        max_edge_length = 1.55
    elif kind == "star":
        leaves = _rotated_points([0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0])
        coords = torch.vstack([torch.zeros(1, 2, dtype=torch.float32), leaves])
        edges = [(0, 1), (0, 2), (0, 3)]
        max_edge_length = 1.45
    elif kind == "path":
        coords = torch.tensor(
            [[-1.5, 0.0], [-0.5, 0.0], [0.5, 0.0], [1.5, 0.0]],
            dtype=torch.float32,
        )
        edges = [(0, 1), (1, 2), (2, 3)]
        max_edge_length = 1.15
    else:
        raise ValueError(f"unknown kind: {kind}")
    return coords + _deterministic_jitter(sample_index, coords.shape[0], jitter_scale), edges, max_edge_length


def _pyg_metrics(coords: torch.Tensor, edges: list[tuple[int, int]]) -> dict[str, object]:
    directed = edges + [(j, i) for i, j in edges]
    edge_index = torch.tensor(directed, dtype=torch.long).t().contiguous()
    data = Data(x=coords, edge_index=edge_index)
    dense_adj = to_dense_adj(data.edge_index, max_num_nodes=coords.shape[0])[0]
    degrees = pyg_degree(data.edge_index[0], num_nodes=coords.shape[0]).to(dtype=torch.int64)
    aggregated = dense_adj @ coords
    return {
        "dense_adj": dense_adj,
        "degree_pattern": [int(v) for v in degrees.tolist()],
        "aggregate_norm_mean": float(torch.linalg.norm(aggregated, dim=1).mean().item()),
    }


def _rustworkx_metrics(num_nodes: int, edges: list[tuple[int, int]]) -> dict[str, object]:
    graph = rx.PyGraph()
    nodes = [graph.add_node(i) for i in range(num_nodes)]
    for a, b in edges:
        graph.add_edge(nodes[a], nodes[b], 1.0)
    diameter = 0.0
    for node in nodes:
        lengths = rx.dijkstra_shortest_path_lengths(graph, node, lambda w: w)
        diameter = max(diameter, max(lengths.values()))
    return {
        "edge_count": int(graph.num_edges()),
        "diameter": float(diameter),
        "component_count": int(len(rx.connected_components(graph))),
    }


def _xgi_metrics(num_nodes: int, edges: list[tuple[int, int]]) -> dict[str, object]:
    hypergraph = xgi.Hypergraph()
    hypergraph.add_nodes_from(range(num_nodes))
    hypergraph.add_edges_from([list(edge) for edge in edges])
    return {
        "node_degrees": [int(hypergraph.degree(i)) for i in range(num_nodes)],
        "line_graph_nodes": int(xgi.convert.to_line_graph(hypergraph).number_of_nodes()),
    }


def _toponetx_metrics(edges: list[tuple[int, int]]) -> dict[str, object]:
    sc = SimplicialComplex([list(edge) for edge in edges])
    b1 = sc.incidence_matrix(rank=1, signed=True)
    return {"shape": [int(v) for v in sc.shape], "b1_shape": [int(v) for v in b1.shape]}


def _gudhi_metrics(coords: torch.Tensor, max_edge_length: float) -> dict[str, object]:
    simplex_tree = gudhi.RipsComplex(
        points=coords.detach().cpu().numpy(),
        max_edge_length=max_edge_length,
    ).create_simplex_tree(max_dimension=1)
    return {
        "num_vertices": int(simplex_tree.num_vertices()),
        "num_simplices": int(simplex_tree.num_simplices()),
    }


def _sympy_roots(dense_adj: torch.Tensor) -> list[float]:
    adjacency = sp.Matrix([[int(v) for v in row] for row in dense_adj.tolist()])
    laplacian = sp.diag(*[sum(adjacency.row(i)) for i in range(adjacency.rows)]) - adjacency
    roots = [
        float(complex(root.evalf()).real)
        for root in sp.nroots(sp.expand(laplacian.charpoly().as_expr()))
    ]
    return sorted(roots)


def _z3_tree_status(node_count: int, edge_count: int) -> str:
    n, e = Ints("n e")
    solver = Solver()
    solver.add(n == node_count, e == edge_count, e == n - 1)
    return "sat" if solver.check() == sat else "unsat"


def _cvc5_tree_status(node_count: int, edge_count: int) -> str:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_LIA")
    int_sort = tm.getIntegerSort()
    n = tm.mkConst(int_sort, "n")
    e = tm.mkConst(int_sort, "e")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, n, tm.mkInteger(node_count)))
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, e, tm.mkInteger(edge_count)))
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, e, tm.mkTerm(Kind.SUB, n, tm.mkInteger(1))))
    return "sat" if solver.checkSat().isSat() else "unsat"


def _quantize(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def _expected_signature(kind: str) -> dict[str, object]:
    if kind == "cycle":
        return {
            "degree_pattern": [2, 2, 2, 2],
            "diameter": 2,
            "shape": [4, 4],
            "simplices": 8,
            "z3": "unsat",
            "cvc5": "unsat",
        }
    return {
        "degree_pattern": [1, 2, 2, 1] if kind == "path" else [3, 1, 1, 1],
        "diameter": 3 if kind == "path" else 2,
        "shape": [4, 3],
        "simplices": 7,
        "z3": "sat",
        "cvc5": "sat",
    }


def _extract_sample(kind: str, sample_index: int, jitter_scale: float) -> dict[str, object]:
    coords, edges, max_edge_length = _shape_spec(kind, sample_index, jitter_scale)
    pyg_metrics = _pyg_metrics(coords, edges)
    rx_metrics = _rustworkx_metrics(coords.shape[0], edges)
    xgi_metrics = _xgi_metrics(coords.shape[0], edges)
    topo_metrics = _toponetx_metrics(edges)
    gudhi_metrics = _gudhi_metrics(coords, max_edge_length)
    spectral_roots = _sympy_roots(pyg_metrics["dense_adj"])
    z3_status = _z3_tree_status(coords.shape[0], rx_metrics["edge_count"])
    cvc5_status = _cvc5_tree_status(coords.shape[0], rx_metrics["edge_count"])
    pairwise_mean = float(torch.pdist(coords).mean().item())
    radial_mean = float(torch.linalg.norm(coords, dim=1).mean().item())

    expected = _expected_signature(kind)
    signature_ok = bool(
        sorted(pyg_metrics["degree_pattern"]) == sorted(expected["degree_pattern"])
        and int(rx_metrics["diameter"]) == expected["diameter"]
        and topo_metrics["shape"] == expected["shape"]
        and gudhi_metrics["num_simplices"] == expected["simplices"]
        and z3_status == expected["z3"]
        and cvc5_status == expected["cvc5"]
    )

    feature_vector = [float(v) for v in pyg_metrics["degree_pattern"]] + [
        float(rx_metrics["diameter"]),
        float(rx_metrics["edge_count"]),
        float(xgi_metrics["line_graph_nodes"]),
        float(topo_metrics["shape"][1]),
        float(gudhi_metrics["num_simplices"]),
    ] + [float(v) for v in spectral_roots] + [
        1.0 if z3_status == "sat" else 0.0,
        1.0 if cvc5_status == "sat" else 0.0,
        pairwise_mean,
        pyg_metrics["aggregate_norm_mean"],
        radial_mean,
    ]

    token_roots = [_quantize(root, 1) for root in spectral_roots]
    tokens = [
        f"deg={'-'.join(str(v) for v in pyg_metrics['degree_pattern'])}",
        f"diam={int(rx_metrics['diameter'])}",
        f"line={xgi_metrics['line_graph_nodes']}",
        f"shape={topo_metrics['shape'][1]}",
        f"simp={gudhi_metrics['num_simplices']}",
        f"tree_z3={z3_status}",
        f"tree_cvc5={cvc5_status}",
    ] + [f"root={root}" for root in token_roots]

    return {
        "kind": kind,
        "label": FAMILY_LABELS[kind],
        "feature_vector": feature_vector,
        "tokens": tokens,
        "signature_ok": signature_ok,
        "solver_agree": z3_status == cvc5_status,
        "z3_status": z3_status,
        "cvc5_status": cvc5_status,
    }


def _noise_vector(index: int, dim: int, scale: float) -> torch.Tensor:
    values = []
    base = float(index + 1)
    for offset in range(dim):
        value = math.sin(base * (offset + 1) * 0.31) + math.cos(base * (offset + 1) * 0.17)
        values.append(scale * value)
    return torch.tensor(values, dtype=torch.float32)


def _collapse_rows(rows: torch.Tensor, strength: float, scramble_rows: bool) -> torch.Tensor:
    working = rows
    if scramble_rows:
        order = []
        for sample_index in range(SAMPLES_PER_FAMILY):
            for family_index in range(len(FAMILY_ORDER)):
                order.append(family_index * SAMPLES_PER_FAMILY + sample_index)
        working = rows[torch.tensor(order, dtype=torch.long)]
    if strength <= 0.0:
        return working.clone()
    mean = working.mean(dim=0, keepdim=True)
    mixed = []
    for index in range(working.shape[0]):
        base = (1.0 - strength) * working[index] + strength * mean[0]
        mixed.append(base + _noise_vector(index, working.shape[1], 0.02))
    return torch.stack(mixed)


def _lsh_precision(labels: list[int], tokens_per_sample: list[list[str]]) -> float:
    num_perm = 64
    lsh = MinHashLSH(threshold=0.7, num_perm=num_perm)
    signatures = []
    for index, tokens in enumerate(tokens_per_sample):
        sig = MinHash(num_perm=num_perm)
        for token in tokens:
            sig.update(token.encode("utf-8"))
        lsh.insert(str(index), sig)
        signatures.append(sig)

    precisions = []
    for index, sig in enumerate(signatures):
        hits = [int(value) for value in lsh.query(sig) if int(value) != index]
        if not hits:
            precisions.append(0.0)
            continue
        same = sum(1 for hit in hits if labels[hit] == labels[index])
        precisions.append(same / len(hits))
    return float(sum(precisions) / len(precisions))


def _neighbor_purity(features: torch.Tensor, labels: list[int]) -> float:
    index = NNDescent(features.detach().cpu().numpy(), n_neighbors=6, random_state=42)
    neighbor_ids, _ = index.neighbor_graph
    purities = []
    for row_index, ids in enumerate(neighbor_ids):
        neighbors = [int(value) for value in ids if int(value) != row_index]
        if not neighbors:
            purities.append(0.0)
            continue
        same = sum(1 for neighbor in neighbors if labels[neighbor] == labels[row_index])
        purities.append(same / len(neighbors))
    return float(sum(purities) / len(purities))


def _cluster_metrics(features: torch.Tensor, labels: list[int]) -> dict[str, float | int]:
    embedder = umap.UMAP(n_neighbors=6, min_dist=0.0, n_components=2, random_state=42)
    embedding = torch.tensor(embedder.fit_transform(features.detach().cpu().numpy()), dtype=torch.float32)
    clusters = hdbscan.HDBSCAN(min_cluster_size=4, min_samples=2).fit_predict(
        embedding.detach().cpu().numpy()
    )
    assigned_mask = clusters != -1
    assigned_fraction = float(assigned_mask.mean())
    cluster_count = int(len({int(value) for value in clusters if int(value) != -1}))
    ari = float(adjusted_rand_score(labels, clusters))
    if cluster_count >= 2 and int(assigned_mask.sum()) >= cluster_count:
        silhouette = float(
            silhouette_score(
                embedding.detach().cpu().numpy()[assigned_mask],
                clusters[assigned_mask],
            )
        )
    else:
        silhouette = -1.0

    purity_mass = 0
    purity_total = 0
    for cluster in sorted({int(value) for value in clusters if int(value) != -1}):
        members = [idx for idx, value in enumerate(clusters) if int(value) == cluster]
        label_counts: dict[int, int] = {}
        for member in members:
            label_counts[labels[member]] = label_counts.get(labels[member], 0) + 1
        purity_mass += max(label_counts.values())
        purity_total += len(members)
    cluster_purity = float(purity_mass / purity_total) if purity_total else 0.0

    return {
        "assigned_fraction": assigned_fraction,
        "cluster_count": cluster_count,
        "ari": ari,
        "silhouette": silhouette,
        "cluster_purity": cluster_purity,
    }


def _family_fractions(samples: list[dict[str, object]]) -> dict[str, float]:
    solver_agreement = sum(1 for sample in samples if sample["solver_agree"]) / len(samples)
    signature_ok = sum(1 for sample in samples if sample["signature_ok"]) / len(samples)
    cycle_unsat = sum(
        1
        for sample in samples
        if sample["kind"] == "cycle" and sample["z3_status"] == "unsat" and sample["cvc5_status"] == "unsat"
    ) / SAMPLES_PER_FAMILY
    tree_sat = sum(
        1
        for sample in samples
        if sample["kind"] != "cycle" and sample["z3_status"] == "sat" and sample["cvc5_status"] == "sat"
    ) / (2 * SAMPLES_PER_FAMILY)
    return {
        "solver_agreement_fraction": float(solver_agreement),
        "signature_ok_fraction": float(signature_ok),
        "cycle_unsat_fraction": float(cycle_unsat),
        "tree_sat_fraction": float(tree_sat),
    }


def _run_case(
    name: str,
    jitter_scale: float,
    collapse_strength: float,
    collapse_tokens: bool,
    scramble_rows: bool,
) -> dict[str, object]:
    samples = []
    for kind in FAMILY_ORDER:
        for sample_index in range(SAMPLES_PER_FAMILY):
            samples.append(_extract_sample(kind, sample_index, jitter_scale))

    labels = [int(sample["label"]) for sample in samples]
    rows = torch.tensor([sample["feature_vector"] for sample in samples], dtype=torch.float32)
    mixed_rows = _collapse_rows(rows, collapse_strength, scramble_rows=scramble_rows)
    scaled = torch.tensor(StandardScaler().fit_transform(mixed_rows.detach().cpu().numpy()), dtype=torch.float32)

    tokens_per_sample = []
    for index, sample in enumerate(samples):
        if collapse_tokens:
            tokens_per_sample.append([f"collapsed={index % 2}", "family=blurred", "roots=coarse"])
        else:
            tokens_per_sample.append(list(sample["tokens"]))

    lsh_precision = _lsh_precision(labels, tokens_per_sample)
    knn_purity = _neighbor_purity(scaled, labels)
    cluster_metrics = _cluster_metrics(scaled, labels)
    fractions = _family_fractions(samples)

    result = {
        "sample_count": len(samples),
        "feature_dim": int(rows.shape[1]),
        "collapse_strength": float(collapse_strength),
        "scramble_rows": bool(scramble_rows),
        "lsh_precision": lsh_precision,
        "knn_purity": knn_purity,
        **cluster_metrics,
        **fractions,
    }

    if name == "positive":
        result["pass"] = bool(
            result["signature_ok_fraction"] == 1.0
            and result["solver_agreement_fraction"] == 1.0
            and result["cycle_unsat_fraction"] == 1.0
            and result["tree_sat_fraction"] == 1.0
            and result["cluster_count"] == 3
            and result["assigned_fraction"] >= 0.95
            and result["ari"] >= 0.95
            and result["silhouette"] >= 0.70
            and result["cluster_purity"] >= 0.95
            and result["knn_purity"] >= 0.95
            and result["lsh_precision"] >= 0.95
        )
    elif name == "boundary":
        result["pass"] = bool(
            result["signature_ok_fraction"] == 1.0
            and result["solver_agreement_fraction"] == 1.0
            and result["cycle_unsat_fraction"] == 1.0
            and result["tree_sat_fraction"] == 1.0
            and result["cluster_count"] == 3
            and result["assigned_fraction"] >= 0.90
            and result["ari"] >= 0.90
            and result["silhouette"] >= 0.55
            and result["cluster_purity"] >= 0.90
            and result["knn_purity"] >= 0.90
            and result["lsh_precision"] >= 0.95
        )
    else:
        result["pass"] = bool(
            result["signature_ok_fraction"] == 1.0
            and result["solver_agreement_fraction"] == 1.0
            and result["cycle_unsat_fraction"] == 1.0
            and result["tree_sat_fraction"] == 1.0
            and result["ari"] <= 0.35
            and result["cluster_purity"] <= 0.55
            and result["knn_purity"] <= 0.55
            and result["lsh_precision"] <= 0.55
        )
    return result


def run_positive_tests() -> dict[str, object]:
    return _run_case(
        "positive",
        jitter_scale=0.02,
        collapse_strength=0.0,
        collapse_tokens=False,
        scramble_rows=False,
    )


def run_negative_tests() -> dict[str, object]:
    return _run_case(
        "negative",
        jitter_scale=0.02,
        collapse_strength=0.90,
        collapse_tokens=True,
        scramble_rows=True,
    )


def run_boundary_tests() -> dict[str, object]:
    return _run_case(
        "boundary",
        jitter_scale=0.04,
        collapse_strength=0.30,
        collapse_tokens=False,
        scramble_rows=False,
    )


def main() -> None:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    overall_pass = bool(positive["pass"] and negative["pass"] and boundary["pass"])
    results = {
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_integration_symbolic_graph_manifold_stack_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"overall_pass={results['overall_pass']} -> {out_path}")


if __name__ == "__main__":
    main()
