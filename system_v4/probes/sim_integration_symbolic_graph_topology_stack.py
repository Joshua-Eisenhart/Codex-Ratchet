#!/usr/bin/env python3
"""
sim_integration_symbolic_graph_topology_stack.py

Curated mega-stack reference sim for:
  pytorch + z3 + cvc5 + sympy + clifford + pyg + rustworkx + xgi + toponetx + gudhi

Claim:
one small carrier shape should admit consistent readings across tensor,
solver, graph, hypergraph, cell-complex, and persistence surfaces instead of
integrating those tools ad hoc one by one.

Positive: 4-cycle carrier.
Negative: 4-node star carrier.
Boundary: 4-node path carrier.

This is a classical integration baseline. The point is tool-stack discipline
and reusable reference behavior, not a canonical nonclassical witness.
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
import rustworkx as rx
import sympy as sp
import torch
import xgi
from clifford import Cl
from cvc5 import Kind
from toponetx.classes import SimplicialComplex
from torch_geometric.data import Data
from torch_geometric.utils import degree as pyg_degree
from torch_geometric.utils import to_dense_adj
from z3 import Ints, Solver, sat


classification = "classical_baseline"
divergence_log = (
    "Classical integration baseline: this is a curated mega-stack reference "
    "lane joining solver, symbolic, graph, hypergraph, cell-complex, and "
    "persistence tools on one shared carrier family."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor carrier for node coordinates, dot products, and adjacency-driven aggregation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing solver cross-check that cycle carriers violate the tree edge-count law while star/path carriers satisfy it",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT cross-check of the same tree-vs-cycle arithmetic witness",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic Laplacian characteristic polynomial and spectral-root witness for cycle, star, and path carriers",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Cl(2) rotor construction of carrier orientations and point coordinates",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph tensor surface via PyG Data, dense adjacency extraction, and degree bookkeeping",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing shortest-path and connected-component witness on the same carrier graph",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hypergraph degree and line-graph witness on the same edge family",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial-complex incidence witness over the same 1-skeleton",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric Rips reconstruction of the 1-skeleton from the carrier coordinates",
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
}


def _rotated_points(angles: list[float]) -> torch.Tensor:
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e12 = blades["e12"]
    coords = []
    for theta in angles:
        rotor = math.cos(theta / 2.0) + math.sin(theta / 2.0) * e12
        vec = rotor * e1 * ~rotor
        coords.append([float(vec[e1]), float(vec[e2])])
    return torch.tensor(coords, dtype=torch.float32)


def _shape_spec(kind: str) -> tuple[torch.Tensor, list[tuple[int, int]], float]:
    if kind == "cycle":
        coords = _rotated_points([0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0])
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        return coords, edges, 1.5
    if kind == "star":
        leaves = _rotated_points([0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0])
        coords = torch.vstack([torch.zeros(1, 2, dtype=torch.float32), leaves])
        edges = [(0, 1), (0, 2), (0, 3)]
        return coords, edges, 1.4
    if kind == "path":
        coords = torch.tensor(
            [[-1.5, 0.0], [-0.5, 0.0], [0.5, 0.0], [1.5, 0.0]],
            dtype=torch.float32,
        )
        edges = [(0, 1), (1, 2), (2, 3)]
        return coords, edges, 1.1
    raise ValueError(f"unknown kind: {kind}")


def _pyg_metrics(coords: torch.Tensor, edges: list[tuple[int, int]]) -> dict[str, object]:
    directed = edges + [(j, i) for i, j in edges]
    edge_index = torch.tensor(directed, dtype=torch.long).t().contiguous()
    data = Data(x=coords, edge_index=edge_index)
    dense_adj = to_dense_adj(data.edge_index, max_num_nodes=coords.shape[0])[0]
    degrees = pyg_degree(data.edge_index[0], num_nodes=coords.shape[0]).to(dtype=torch.int64)
    aggregated = dense_adj @ coords
    return {
        "edge_index": edge_index,
        "dense_adj": dense_adj,
        "degree_pattern": [int(v) for v in degrees.tolist()],
        "adjacency_sum": int(dense_adj.sum().item()),
        "aggregate_norms": [float(v) for v in torch.linalg.norm(aggregated, dim=1).tolist()],
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
        "hyperedge_count": int(hypergraph.num_edges),
    }


def _toponetx_metrics(edges: list[tuple[int, int]]) -> dict[str, object]:
    sc = SimplicialComplex([list(edge) for edge in edges])
    b1 = sc.incidence_matrix(rank=1, signed=True)
    return {
        "dim": int(sc.dim),
        "shape": [int(v) for v in sc.shape],
        "b1_shape": [int(v) for v in b1.shape],
    }


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
    roots = [float(complex(root.evalf()).real) for root in sp.nroots(sp.expand(laplacian.charpoly().as_expr()))]
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


def _close(a: list[float], b: list[float], tol: float = 1e-5) -> bool:
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def _run_case(kind: str) -> dict[str, object]:
    coords, edges, max_edge_length = _shape_spec(kind)
    pyg_metrics = _pyg_metrics(coords, edges)
    rx_metrics = _rustworkx_metrics(coords.shape[0], edges)
    xgi_metrics = _xgi_metrics(coords.shape[0], edges)
    topo_metrics = _toponetx_metrics(edges)
    gudhi_metrics = _gudhi_metrics(coords, max_edge_length)
    spectral_roots = _sympy_roots(pyg_metrics["dense_adj"])
    z3_status = _z3_tree_status(coords.shape[0], rx_metrics["edge_count"])
    cvc5_status = _cvc5_tree_status(coords.shape[0], rx_metrics["edge_count"])

    dot_matrix = coords @ coords.T
    result = {
        "degree_pattern": pyg_metrics["degree_pattern"],
        "adjacency_sum": pyg_metrics["adjacency_sum"],
        "aggregate_norms": pyg_metrics["aggregate_norms"],
        "diameter": rx_metrics["diameter"],
        "component_count": rx_metrics["component_count"],
        "hypergraph_degrees": xgi_metrics["node_degrees"],
        "line_graph_nodes": xgi_metrics["line_graph_nodes"],
        "toponetx_shape": topo_metrics["shape"],
        "toponetx_b1_shape": topo_metrics["b1_shape"],
        "gudhi_num_vertices": gudhi_metrics["num_vertices"],
        "gudhi_num_simplices": gudhi_metrics["num_simplices"],
        "sympy_laplacian_roots": spectral_roots,
        "z3_tree_status": z3_status,
        "cvc5_tree_status": cvc5_status,
    }

    if kind == "cycle":
        result.update(
            {
                "node_norms": [float(v) for v in torch.linalg.norm(coords, dim=1).tolist()],
                "opposite_dot": float(dot_matrix[0, 2].item()),
                "adjacent_dot": float(dot_matrix[0, 1].item()),
            }
        )
        result["pass"] = bool(
            _close(result["node_norms"], [1.0, 1.0, 1.0, 1.0])
            and abs(result["opposite_dot"] + 1.0) <= 1e-5
            and abs(result["adjacent_dot"]) <= 1e-5
            and result["degree_pattern"] == [2, 2, 2, 2]
            and int(result["diameter"]) == 2
            and result["component_count"] == 1
            and result["hypergraph_degrees"] == [2, 2, 2, 2]
            and result["line_graph_nodes"] == 4
            and result["toponetx_shape"] == [4, 4]
            and result["toponetx_b1_shape"] == [4, 4]
            and result["gudhi_num_vertices"] == 4
            and result["gudhi_num_simplices"] == 8
            and _close(result["sympy_laplacian_roots"], [0.0, 2.0, 2.0, 4.0], tol=1e-4)
            and result["z3_tree_status"] == "unsat"
            and result["cvc5_tree_status"] == "unsat"
        )
    elif kind == "star":
        leaf_norms = [float(v) for v in torch.linalg.norm(coords[1:], dim=1).tolist()]
        result.update(
            {
                "center_norm": float(torch.linalg.norm(coords[0]).item()),
                "leaf_norms": leaf_norms,
            }
        )
        result["pass"] = bool(
            result["center_norm"] <= 1e-6
            and _close(sorted(leaf_norms), [1.0, 1.0, 1.0], tol=1e-5)
            and sorted(result["degree_pattern"]) == [1, 1, 1, 3]
            and int(result["diameter"]) == 2
            and result["component_count"] == 1
            and sorted(result["hypergraph_degrees"]) == [1, 1, 1, 3]
            and result["line_graph_nodes"] == 3
            and result["toponetx_shape"] == [4, 3]
            and result["toponetx_b1_shape"] == [4, 3]
            and result["gudhi_num_vertices"] == 4
            and result["gudhi_num_simplices"] == 7
            and _close(result["sympy_laplacian_roots"], [0.0, 1.0, 1.0, 4.0], tol=1e-4)
            and result["z3_tree_status"] == "sat"
            and result["cvc5_tree_status"] == "sat"
        )
    else:
        result["pass"] = bool(
            result["degree_pattern"] == [1, 2, 2, 1]
            and int(result["diameter"]) == 3
            and result["component_count"] == 1
            and result["hypergraph_degrees"] == [1, 2, 2, 1]
            and result["line_graph_nodes"] == 3
            and result["toponetx_shape"] == [4, 3]
            and result["toponetx_b1_shape"] == [4, 3]
            and result["gudhi_num_vertices"] == 4
            and result["gudhi_num_simplices"] == 7
            and _close(result["sympy_laplacian_roots"], [0.0, 0.5857864376, 2.0, 3.4142135624], tol=1e-3)
            and result["z3_tree_status"] == "sat"
            and result["cvc5_tree_status"] == "sat"
        )
    return result


def run_positive_tests() -> dict[str, object]:
    return _run_case("cycle")


def run_negative_tests() -> dict[str, object]:
    return _run_case("star")


def run_boundary_tests() -> dict[str, object]:
    return _run_case("path")


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
    out_path = os.path.join(
        out_dir,
        "sim_integration_symbolic_graph_topology_stack_results.json",
    )
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"overall_pass={results['overall_pass']} -> {out_path}")


if __name__ == "__main__":
    main()
