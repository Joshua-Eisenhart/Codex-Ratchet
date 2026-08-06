"""Isolated fixed graph/topology worker used by ConstraintBox.

This worker deliberately has no request-selected executable, topology, graph,
or API surface.  Its parent supplies one typed binding and, for its own
severance checks, one exact API label.  The normal path exercises the actual
installed libraries; a severance path exits immediately at the named call
site so the parent can demonstrate that the path is not a JSON-only wrapper.
"""

from __future__ import annotations

import importlib.metadata
import json
import os
import sys
from typing import Any


REQUEST_SCHEMA = "constraintbox.graph-topology-worker-request.v1"
WITNESS_SCHEMA = "constraintbox.graph-topology-worker-witness.v1"
FAILURE_SCHEMA = "constraintbox.graph-topology-worker-failure.v1"
WORKER_ARGUMENT = "--constraintbox-graph-topology-worker-v1"
SEVERED_EXIT_CODE = 92
SEVERED_PREFIX = "CONSTRAINTBOX_GRAPH_TOPOLOGY_OPERATION_SEVERED:"
EXACT_APIS = (
    "gudhi.SimplexTree.compute_persistence",
    "toponetx.SimplicialComplex.hodge_laplacian_matrix",
    "xgi.Hypergraph.add_edges_from",
    "networkx.number_connected_components",
    "igraph.Graph.components",
    "rustworkx.connected_components",
    "torch_geometric.utils.get_laplacian",
    "torch.linalg.eigvalsh",
)
_DISTRIBUTIONS = (
    "gudhi",
    "TopoNetX",
    "xgi",
    "networkx",
    "igraph",
    "rustworkx",
    "torch",
    "torch-geometric",
)


class OperationSevered(RuntimeError):
    """A controller-requested operation-severance control reached its target."""


def _emit(value: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()


def _read_request() -> tuple[dict[str, str], str | None]:
    try:
        value = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"worker request is not JSON: {exc}") from exc
    if not isinstance(value, dict) or set(value) != {"schema", "binding", "poison_api"}:
        raise ValueError("worker request has an unexpected shape")
    if value.get("schema") != REQUEST_SCHEMA:
        raise ValueError("worker request schema is invalid")
    binding = value.get("binding")
    if not isinstance(binding, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in binding.items()
    ):
        raise ValueError("worker binding is invalid")
    poison_api = value.get("poison_api")
    if poison_api is not None and poison_api not in EXACT_APIS:
        raise ValueError("worker poison API is not controller-owned")
    return dict(binding), poison_api


def _maybe_sever(poison_api: str | None, api: str) -> None:
    if poison_api == api:
        raise OperationSevered(api)


def _gudhi_b1(filled: bool, poison_api: str | None) -> int:
    import gudhi

    complex_ = gudhi.SimplexTree()
    for simplex in ((0, 1), (1, 2), (0, 2)):
        complex_.insert(simplex)
    if filled:
        complex_.insert((0, 1, 2))
    _maybe_sever(poison_api, "gudhi.SimplexTree.compute_persistence")
    complex_.compute_persistence(persistence_dim_max=True)
    betti = complex_.betti_numbers()
    return int(betti[1]) if len(betti) > 1 else 0


def _toponetx_b1(filled: bool, poison_api: str | None) -> int:
    import torch
    from toponetx import SimplicialComplex

    simplices: list[tuple[int, ...]] = [(0, 1), (1, 2), (0, 2)]
    if filled:
        simplices.append((0, 1, 2))
    complex_ = SimplicialComplex(simplices)
    _maybe_sever(poison_api, "toponetx.SimplicialComplex.hodge_laplacian_matrix")
    laplacian = complex_.hodge_laplacian_matrix(rank=1).toarray()
    _maybe_sever(poison_api, "torch.linalg.eigvalsh")
    eigenvalues = torch.linalg.eigvalsh(
        torch.tensor(laplacian.tolist(), dtype=torch.float64)
    )
    return int(torch.sum(torch.abs(eigenvalues) < 1e-8).item())


def _xgi_edge_sizes(filled: bool, poison_api: str | None) -> list[int]:
    import xgi

    hypergraph = xgi.Hypergraph()
    edges: list[set[int]] = [{0, 1}, {1, 2}, {0, 2}]
    if filled:
        edges.append({0, 1, 2})
    _maybe_sever(poison_api, "xgi.Hypergraph.add_edges_from")
    hypergraph.add_edges_from(edges)
    return sorted(len(edge) for edge in hypergraph.edges.members())


def _connectivity_case(
    edges: tuple[tuple[int, int], ...], poison_api: str | None
) -> dict[str, int]:
    import igraph as ig
    import networkx as nx
    import rustworkx as rx
    import torch
    from torch_geometric.data import Data
    from torch_geometric.utils import get_laplacian

    networkx_graph = nx.Graph()
    networkx_graph.add_nodes_from(range(4))
    networkx_graph.add_edges_from(edges)
    _maybe_sever(poison_api, "networkx.number_connected_components")
    networkx_components = int(nx.number_connected_components(networkx_graph))

    igraph_graph = ig.Graph(n=4, edges=edges, directed=False)
    _maybe_sever(poison_api, "igraph.Graph.components")
    igraph_components = int(len(igraph_graph.components()))

    rustworkx_graph = rx.PyGraph()
    rustworkx_graph.add_nodes_from([None] * 4)
    rustworkx_graph.add_edges_from_no_data(edges)
    _maybe_sever(poison_api, "rustworkx.connected_components")
    rustworkx_components = int(len(rx.connected_components(rustworkx_graph)))

    directed_edges = list(edges) + [(right, left) for left, right in edges]
    edge_index = torch.tensor(directed_edges, dtype=torch.long).t().contiguous()
    data = Data(edge_index=edge_index, num_nodes=4)
    _maybe_sever(poison_api, "torch_geometric.utils.get_laplacian")
    laplacian_index, laplacian_weight = get_laplacian(
        data.edge_index,
        num_nodes=data.num_nodes,
        normalization=None,
    )
    laplacian = torch.zeros((4, 4), dtype=torch.float64)
    laplacian.index_put_(
        (laplacian_index[0], laplacian_index[1]),
        laplacian_weight.to(torch.float64),
        accumulate=True,
    )
    _maybe_sever(poison_api, "torch.linalg.eigvalsh")
    pyg_components = int(
        torch.sum(torch.abs(torch.linalg.eigvalsh(laplacian)) < 1e-8).item()
    )
    return {
        "networkx": networkx_components,
        "igraph": igraph_components,
        "rustworkx": rustworkx_components,
        "pyg_torch": pyg_components,
    }


def _observation(poison_api: str | None) -> dict[str, Any]:
    return {
        "topology": {
            "cycle": {
                "gudhi_b1": _gudhi_b1(False, poison_api),
                "toponetx_b1": _toponetx_b1(False, poison_api),
                "xgi_edge_sizes": _xgi_edge_sizes(False, poison_api),
            },
            "filled": {
                "gudhi_b1": _gudhi_b1(True, poison_api),
                "toponetx_b1": _toponetx_b1(True, poison_api),
                "xgi_edge_sizes": _xgi_edge_sizes(True, poison_api),
            },
        },
        "connectivity": {
            "disconnected": _connectivity_case(((0, 1), (2, 3)), poison_api),
            "chain": _connectivity_case(((0, 1), (1, 2), (2, 3)), poison_api),
        },
    }


def _runtime() -> dict[str, Any]:
    return {
        "implementation": sys.implementation.name,
        "version": list(sys.version_info[:3]),
        "distributions": {
            distribution: importlib.metadata.version(distribution)
            for distribution in _DISTRIBUTIONS
        },
    }


def main() -> int:
    if sys.argv[1:] != [WORKER_ARGUMENT]:
        sys.stderr.write("graph/topology worker accepts one fixed controller argument\n")
        return 64
    try:
        binding, poison_api = _read_request()
        observed = _observation(poison_api)
        _emit(
            {
                "schema": WITNESS_SCHEMA,
                "binding": binding,
                "exact_api": list(EXACT_APIS),
                "worker_pid": os.getpid(),
                "runtime": _runtime(),
                "observed": observed,
            }
        )
        return 0
    except OperationSevered as exc:
        sys.stderr.write(f"{SEVERED_PREFIX}{exc}\n")
        return SEVERED_EXIT_CODE
    except Exception as exc:
        _emit(
            {
                "schema": FAILURE_SCHEMA,
                "error_type": type(exc).__name__,
                "error": str(exc).splitlines()[0][:400],
            }
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
