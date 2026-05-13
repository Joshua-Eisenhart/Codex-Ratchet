#!/usr/bin/env python3
"""
Tier A A4.5 tool-lego-integration probe for TopoNetX + PyG.

TopoNetX is load-bearing for simplicial-complex admission and for the Hasse-graph
structure that the graph side consumes. PyG is load-bearing for graph
realization, validation, message passing, and batched pooling over that
TopoNetX-derived structure. Each section uses actual interop: TopoNetX outputs
are translated into PyG Data objects and then checked against manual or
validation-side expectations.

Hermes workers save and enqueue this probe but do not execute it directly.
"""

import json
import os
from typing import Any, Dict, Iterable, List, Sequence

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"
NAME = "tool_integration_toponetx_pyg"

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "supportive dependency for PyG tensor construction; not the load-bearing integration surface in this packet.",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "PyG realizes the TopoNetX-derived carrier as Data objects, validates graph integrity, propagates simplex-dimension features, and pools graph summaries; removing PyG excludes the integration claim rather than leaving a decorative import.",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not used: this packet checks topology-to-graph tensor integration, not SMT satisfiability.",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not used: this packet checks topology-to-graph tensor integration, not cvc5 solver constraints.",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not used: no symbolic algebra surface is exercised.",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not used: no geometric algebra surface is exercised.",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not used: no manifold metric or geodesic surface is exercised.",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not used: no equivariant representation surface is exercised.",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not used: graph realization is through PyG, not rustworkx DAG algorithms.",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "not used: the fixture is a simplicial-complex Hasse graph, not a hypergraph.",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "TopoNetX admits the simplicial complexes, exposes the Hasse-graph carrier, and supplies the node/edge structure that PyG consumes; without those topology outputs the graph-side claim is under-specified.",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not used: no persistence or simplex-tree surface is exercised.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": "load_bearing",
    "pytorch": "supportive",
    "rustworkx": None,
    "sympy": None,
    "toponetx": "load_bearing",
    "xgi": None,
    "z3": None,
}

CANDIDATE_SIM_SPEC = {
    "operation_sequence": [
        "admit finite simplicial-complex fixtures with TopoNetX",
        "convert each complex to its TopoNetX Hasse graph",
        "sort Hasse nodes and encode simplex dimension as a one-column PyTorch feature tensor",
        "translate Hasse graph edges into a directed PyG edge_index",
        "apply a custom PyG MessagePassing layer that sums neighbouring simplex-dimension features",
        "batch independent TopoNetX-derived PyG Data fixtures with Batch.from_data_list",
        "pool batched simplex-dimension features with global_mean_pool",
        "compare PyG outputs against manual neighbour sums and validation controls",
    ],
    "carrier_topology": (
        "Finite simplicial-complex Hasse graph fixtures: TopoNetX supplies simplex nodes and "
        "incidence edges, while PyG consumes the directed graph tensor representation."
    ),
    "observable": {
        "primary": "PyG message-passing output over TopoNetX-derived Hasse graph edge_index",
        "secondary": [
            "batched graph mean of simplex-dimension features",
            "PyG validation status for truncated Hasse graph export",
            "duplicate-simplex rejection before graph construction",
            "singleton complex empty-edge output",
            "minimal-edge complex neighbour-sum output",
        ],
    },
    "pass_fail_predicate": (
        "Pass iff TopoNetX-derived Hasse graph tensors make PyG MessagePassing and "
        "global_mean_pool match manual expectations, while invalid duplicate, truncated, "
        "singleton, and minimal-edge controls behave as declared."
    ),
    "graveyards": [
        "duplicate-vertex simplex should be rejected before PyG graph realization",
        "truncated Hasse export should fail PyG Data validation",
        "singleton TopoNetX complex should produce an empty edge_index and zero message output",
        "single-edge TopoNetX complex should match manual neighbour-sum output",
    ],
    "baselines": [
        "manual neighbour-sum baseline over the directed Hasse edge_index",
        "manual batched simplex-dimension mean baseline",
        "invalid duplicate-simplex baseline",
        "truncated PyG Data validation baseline",
        "singleton no-edge baseline",
    ],
    "alternative_formulations": [
        "encode simplex cardinality and orientation as multi-column node features instead of dimension only",
        "use only PyG Data validation without MessagePassing to isolate graph-realization behaviour",
        "replace the custom MessagePassing layer with a standard PyG convolution over the same Hasse edge_index",
    ],
    "tool_function_needs": [
        "toponetx.classes.SimplicialComplex for finite complex admission",
        "SimplicialComplex.to_hasse_graph for topology-derived graph structure",
        "torch_geometric.data.Data for Hasse graph tensor fixtures",
        "torch_geometric.data.Batch.from_data_list for batched fixtures",
        "torch_geometric.nn.MessagePassing.propagate for neighbour aggregation",
        "torch_geometric.nn.global_mean_pool for graph-level pooling",
    ],
    "lego_coupling_target": "bounded topology-to-graph tool-integration evidence for later topology-to-graph lego-fit packets",
    "claim_ceiling": (
        "finite tool_integration_toponetx_pyg tool-integration receipt only; no bridge, "
        "GStack, axis, QIT, or nonclassical admission"
    ),
}

try:
    from toponetx.classes import SimplicialComplex

    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    SimplicialComplex = None
    TOOL_MANIFEST["toponetx"]["reason"] = "TopoNetX import failed on this machine; queued execution will decide whether simplicial-complex and Hasse-graph APIs are available."

try:
    import torch
    from torch_geometric.data import Batch, Data
    from torch_geometric.nn import MessagePassing, global_mean_pool

    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
except ImportError:
    torch = None
    Batch = Data = MessagePassing = global_mean_pool = None
    TOOL_MANIFEST["pyg"]["reason"] = "PyG import failed on this machine; queued execution will decide whether graph realization, validation, and message passing over TopoNetX-derived carriers are available."
    TOOL_MANIFEST["pytorch"]["reason"] = "PyTorch import failed with PyG; tensor substrate unavailable."


class SimplexNeighborSum(MessagePassing if MessagePassing is not None else object):
    def __init__(self):
        if MessagePassing is None:
            raise RuntimeError("PyG MessagePassing is unavailable")
        super().__init__(aggr="add")

    def forward(self, x, edge_index):
        return self.propagate(edge_index, x=x)

    def message(self, x_j):
        return x_j


def _integration_ready() -> bool:
    return (
        TOOL_MANIFEST["toponetx"]["tried"]
        and TOOL_MANIFEST["pyg"]["tried"]
        and SimplicialComplex is not None
        and torch is not None
        and Data is not None
        and MessagePassing is not None
        and Batch is not None
        and global_mean_pool is not None
    )


def _mark_used(*tools: str) -> None:
    for tool in tools:
        TOOL_MANIFEST[tool]["used"] = True


def _serialize(value: Any) -> Any:
    if value is None:
        return None
    if torch is not None and isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if isinstance(value, set):
        return sorted(_serialize(v) for v in value)
    return value


def _gate_results(section: str) -> Dict[str, Any]:
    missing = []
    if not TOOL_MANIFEST["toponetx"]["tried"]:
        missing.append("toponetx")
    if not TOOL_MANIFEST["pyg"]["tried"]:
        missing.append("pyg")
    return {f"{section}_import_gate": {"status": "skipped", "missing": missing}}


def _normalize_simplex(node: Any) -> Any:
    if isinstance(node, frozenset):
        if len(node) == 1:
            return next(iter(node))
        return sorted(node)
    if isinstance(node, (tuple, list, set)):
        seq = list(node)
        if len(seq) == 1:
            return seq[0]
        return sorted(seq)
    if hasattr(node, "elements"):
        elements = list(node.elements)
        if len(elements) == 1:
            return elements[0]
        return sorted(elements)
    return node


def _simplex_dimension(node: Any) -> int:
    normalized = _normalize_simplex(node)
    if isinstance(normalized, list):
        return max(len(normalized) - 1, 0)
    return 0


def _sorted_hasse_nodes(nodes: Iterable[Any]) -> List[Any]:
    return sorted(nodes, key=lambda node: (_simplex_dimension(node), repr(_normalize_simplex(node))))


def _manual_neighbor_sum(x, edge_index):
    output = torch.zeros_like(x)
    for source, target in edge_index.t().tolist():
        output[target] += x[source]
    return output


def _toponetx_to_pyg(facets: Sequence[Sequence[int]]) -> Dict[str, Any]:
    complex_ = SimplicialComplex(facets)
    hasse = complex_.to_hasse_graph()
    ordered_nodes = _sorted_hasse_nodes(hasse.nodes())
    node_map = {node: idx for idx, node in enumerate(ordered_nodes)}

    directed_edges: List[List[int]] = []
    for left, right in hasse.edges():
        left_idx = node_map[left]
        right_idx = node_map[right]
        directed_edges.append([left_idx, right_idx])
        directed_edges.append([right_idx, left_idx])

    if directed_edges:
        edge_index = torch.tensor(directed_edges, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)

    node_dims = [_simplex_dimension(node) for node in ordered_nodes]
    x = torch.tensor([[float(dim)] for dim in node_dims], dtype=torch.float32)
    data = Data(x=x, edge_index=edge_index, num_nodes=len(ordered_nodes))
    return {
        "facets": [list(facet) for facet in facets],
        "complex": complex_,
        "hasse": hasse,
        "ordered_nodes": ordered_nodes,
        "normalized_nodes": [_normalize_simplex(node) for node in ordered_nodes],
        "node_dimensions": node_dims,
        "data": data,
    }


def run_positive_tests():
    if not _integration_ready():
        return _gate_results("positive")

    conv = SimplexNeighborSum()
    results = {}

    square_fill = _toponetx_to_pyg([[0, 1, 2], [0, 2, 3]])
    propagated = conv(square_fill["data"].x, square_fill["data"].edge_index)
    manual = _manual_neighbor_sum(square_fill["data"].x, square_fill["data"].edge_index)
    _mark_used("toponetx", "pyg")
    results["toponetx_hasse_graph_feeds_pyg_message_passing"] = {
        "facets": square_fill["facets"],
        "toponetx_nodes": _serialize(square_fill["normalized_nodes"]),
        "simplex_dimensions_from_toponetx": square_fill["node_dimensions"],
        "pyg_edge_index": _serialize(square_fill["data"].edge_index),
        "pyg_output": _serialize(propagated),
        "manual_expected": _serialize(manual),
        "matches_expected": bool(torch.allclose(propagated, manual, atol=1e-7, rtol=0.0)),
        "hasse_node_count": int(square_fill["hasse"].number_of_nodes()),
        "hasse_edge_count": int(square_fill["hasse"].number_of_edges()),
    }

    interval = _toponetx_to_pyg([[0, 1]])
    filled_triangle = _toponetx_to_pyg([[5, 6, 7]])
    batch = Batch.from_data_list([interval["data"], filled_triangle["data"]])
    pooled = global_mean_pool(batch.x, batch.batch)
    expected = torch.tensor(
        [
            [sum(interval["node_dimensions"]) / len(interval["node_dimensions"])],
            [sum(filled_triangle["node_dimensions"]) / len(filled_triangle["node_dimensions"])],
        ],
        dtype=torch.float32,
    )
    _mark_used("toponetx", "pyg")
    results["toponetx_complex_family_feeds_pyg_batch_pooling"] = {
        "facets_per_complex": [interval["facets"], filled_triangle["facets"]],
        "node_dimensions_per_complex": [interval["node_dimensions"], filled_triangle["node_dimensions"]],
        "batch_vector": _serialize(batch.batch),
        "pooled_means": _serialize(pooled),
        "expected_means": _serialize(expected),
        "matches_expected": bool(torch.allclose(pooled, expected, atol=1e-7, rtol=0.0)),
    }

    return results


def run_negative_tests():
    if not _integration_ready():
        return _gate_results("negative")

    results = {}

    try:
        SimplicialComplex([[0, 0, 1]])
        status = "unexpected_success"
        detail = "duplicate-node simplex was admitted"
    except ValueError as exc:
        _mark_used("toponetx")
        status = "value_error"
        detail = str(exc)
    results["duplicate_vertex_simplex_is_excluded_before_pyg_realization"] = {
        "status": status,
        "expected": "value_error",
        "detail": detail,
        "pyg_graph_built": False,
    }

    valid = _toponetx_to_pyg([[0, 1, 2]])
    truncated = Data(
        x=valid["data"].x[:-1],
        edge_index=valid["data"].edge_index,
        num_nodes=valid["data"].num_nodes - 1,
    )
    validation_flag = truncated.validate(raise_on_error=False)
    try:
        truncated.validate(raise_on_error=True)
        validation_error = None
    except ValueError as exc:
        validation_error = str(exc)
    _mark_used("toponetx", "pyg")
    results["truncated_toponetx_export_is_excluded_by_pyg_validation"] = {
        "toponetx_nodes": _serialize(valid["normalized_nodes"]),
        "original_edge_index": _serialize(valid["data"].edge_index),
        "truncated_num_nodes": int(truncated.num_nodes),
        "pyg_validate_flag": bool(validation_flag),
        "raised_value_error": validation_error is not None,
        "error": validation_error,
    }

    return results


def run_boundary_tests():
    if not _integration_ready():
        return _gate_results("boundary")

    conv = SimplexNeighborSum()
    results = {}

    singleton = _toponetx_to_pyg([[9]])
    singleton_output = conv(singleton["data"].x, singleton["data"].edge_index)
    _mark_used("toponetx", "pyg")
    results["singleton_toponetx_vertex_survives_empty_pyg_edge_set"] = {
        "facets": singleton["facets"],
        "toponetx_nodes": _serialize(singleton["normalized_nodes"]),
        "edge_count": int(singleton["data"].edge_index.size(1)),
        "pyg_output": _serialize(singleton_output),
        "expected": [[0.0]],
        "matches_expected": bool(torch.allclose(singleton_output, torch.zeros_like(singleton_output), atol=1e-7, rtol=0.0)),
    }

    minimal_edge = _toponetx_to_pyg([[2, 3]])
    minimal_output = conv(minimal_edge["data"].x, minimal_edge["data"].edge_index)
    minimal_manual = _manual_neighbor_sum(minimal_edge["data"].x, minimal_edge["data"].edge_index)
    _mark_used("toponetx", "pyg")
    results["single_toponetx_edge_survives_minimal_pyg_message_passing"] = {
        "facets": minimal_edge["facets"],
        "toponetx_nodes": _serialize(minimal_edge["normalized_nodes"]),
        "simplex_dimensions_from_toponetx": minimal_edge["node_dimensions"],
        "pyg_edge_index": _serialize(minimal_edge["data"].edge_index),
        "pyg_output": _serialize(minimal_output),
        "manual_expected": _serialize(minimal_manual),
        "matches_expected": bool(torch.allclose(minimal_output, minimal_manual, atol=1e-7, rtol=0.0)),
    }

    return results


def _case_pass(case: Dict[str, Any]) -> bool:
    if case.get("status") == "skipped":
        return False
    if "matches_expected" in case:
        return bool(case["matches_expected"])
    if "expected" in case and "status" in case:
        return case.get("status") == case.get("expected")
    if "pyg_validate_flag" in case:
        return bool((not case.get("pyg_validate_flag")) and case.get("raised_value_error"))
    return False


def _section_all_pass(section: Dict[str, Dict[str, Any]]) -> bool:
    return bool(section) and all(_case_pass(case) for case in section.values())


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_all_pass(positive),
        "negative_all_pass": _section_all_pass(negative),
        "boundary_all_pass": _section_all_pass(boundary),
    }
    summary["all_pass"] = all(summary.values())
    results = {
        "name": NAME,
        "classification": classification,
        **CANDIDATE_SIM_SPEC,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "criteria_checked": [
            "TopoNetX Hasse graph feeds PyG message passing",
            "TopoNetX complex family feeds PyG batch pooling",
            "Invalid duplicate-vertex simplex is excluded before PyG realization",
            "Truncated TopoNetX export is excluded by PyG validation",
            "Singleton and minimal-edge TopoNetX boundaries survive PyG realization",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target="Use as bounded TopoNetX to PyG tool-integration evidence before topology-to-graph lego fit packets.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(_serialize(results), handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
    if not summary["all_pass"]:
        raise SystemExit(1)
