#!/usr/bin/env python3
"""NetworkX to PyG graph roundtrip micro probe.

Tool-stage scope:
  - two primary tools: NetworkX and PyG
  - one API surface: NetworkX DiGraph edge/node data converted into PyG Data
    and torch_geometric.nn.MessagePassing.propagate
  - one tiny claim: a bounded directed graph preserves node mapping, edge
    orientation, isolated nodes, and incoming-neighbor sums across the handoff.

This is pre-lego evidence. It does not promote a lego, bridge, axis, or broad
graph-learning claim.
"""

import json
import os

import networkx as nx
import torch
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"
NAME = "sim_integration_networkx_pyg_graph_roundtrip_micro"
PROBE_FAMILY = "networkx_pyg_graph_roundtrip_micro"
CONSTRAINT_SET = "bounded_directed_graph_roundtrip_fixture"

PYG_PRIOR_RECEIPT = (
    "system_v4/probes/a2_state/sim_results/"
    "sim_pyg_message_passing_autograd_micro_results.json"
)

_NOT_USED_REASON = (
    "not used: this micro probe isolates NetworkX-to-PyG graph conversion and "
    "message passing on a tiny directed fixture; proof, geometry, topology, "
    "optimization, lego, and bridge claims are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "PyTorch is supportive: tensor storage, equality checks, and numeric "
            "message values carry the PyG execution."
        ),
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": (
            "PyG is load-bearing: Data.validate and MessagePassing.propagate "
            "produce the graph-handoff verdicts."
        ),
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": (
            "NetworkX is load-bearing: DiGraph nodes, features, and directed "
            "edges are the source graph that PyG must preserve."
        ),
    },
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["networkx"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["pyg"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

CANDIDATE_SIM_SPEC = {
    "operation_sequence": [
        "construct a bounded NetworkX DiGraph with node features and directed edges",
        "convert NetworkX node order, features, and directed edges into PyG Data tensors",
        "validate the PyG Data object",
        "apply PyG MessagePassing.propagate with source-to-target sum aggregation",
        "compare PyG incoming-neighbour sums against NetworkX predecessor sums",
        "run reversed-orientation, duplicate/missing node-order, isolated-node, and empty-graph controls",
    ],
    "carrier_topology": (
        "Finite directed graph fixture: NetworkX is the source graph representation, "
        "PyG Data is the tensor carrier, and edge orientation is preserved as edge_index source-to-target order."
    ),
    "observable": {
        "primary": "PyG message output compared to NetworkX incoming-predecessor feature sums",
        "secondary": [
            "node and edge count preservation",
            "node-order mapping dictionary",
            "reversed edge-orientation output",
            "duplicate and missing node-order rejection",
            "isolated-node zero incoming message",
            "empty graph Data shape",
        ],
    },
    "pass_fail_predicate": (
        "Pass iff NetworkX-to-PyG conversion preserves node mapping, edge orientation, "
        "node/edge counts, isolated nodes, and empty graph shape, while reversed orientation "
        "and invalid node-order controls are excluded."
    ),
    "graveyards": [
        "reversed PyG edge orientation should not reproduce the NetworkX incoming-neighbour sums",
        "duplicate node-order mapping should be rejected",
        "missing node-order mapping should be rejected",
        "isolated node should survive conversion with zero incoming message",
        "empty NetworkX graph should become valid zero-node zero-edge PyG Data",
    ],
    "baselines": [
        "NetworkX predecessor-sum baseline",
        "PyG Data.validate baseline",
        "reversed edge_index orientation baseline",
        "invalid node-order mapping baseline",
        "isolated-node and empty-graph boundary baselines",
    ],
    "alternative_formulations": [
        "use an undirected NetworkX Graph converted to two directed PyG edges per edge",
        "include edge attributes and compare weighted message passing",
        "batch multiple NetworkX-derived PyG Data fixtures before pooling",
    ],
    "tool_function_needs": [
        "networkx.DiGraph node and edge APIs for source fixture construction",
        "DiGraph.predecessors for incoming-neighbour reference sums",
        "torch_geometric.data.Data and Data.validate for graph tensor realization",
        "torch_geometric.nn.MessagePassing.propagate for source-to-target aggregation",
    ],
    "lego_coupling_target": "bounded NetworkX-to-PyG graph handoff fixture before graph-cell or density-carrier lego promotion",
    "claim_ceiling": "tool_tool_micro_integration_only",
}


class SumMessage(MessagePassing):
    def __init__(self):
        super().__init__(aggr="add")

    def forward(self, x, edge_index):
        return self.propagate(edge_index, x=x)

    def message(self, x_j):
        return x_j


def build_cycle_graph():
    graph = nx.DiGraph()
    graph.add_node("a", feature=1.0)
    graph.add_node("b", feature=2.0)
    graph.add_node("c", feature=3.0)
    graph.add_edges_from([("a", "b"), ("b", "c"), ("c", "a")])
    return graph


def networkx_incoming_sum(graph):
    return {
        node: sum(float(graph.nodes[src]["feature"]) for src in graph.predecessors(node))
        for node in graph.nodes
    }


def graph_to_pyg(graph, *, node_order=None):
    order = list(node_order or graph.nodes)
    if len(set(order)) != len(order) or set(order) != set(graph.nodes):
        raise ValueError("node_order must contain each NetworkX node exactly once")

    index = {node: idx for idx, node in enumerate(order)}
    edge_pairs = []
    for src, dst in graph.edges:
        edge_pairs.append([index[src], index[dst]])
    if edge_pairs:
        edge_index = torch.tensor(edge_pairs, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)

    x = torch.tensor([[float(graph.nodes[node]["feature"])] for node in order])
    data = Data(x=x, edge_index=edge_index, num_nodes=len(order))
    data.validate(raise_on_error=True)
    return data, index


def _as_list(tensor):
    return [float(v) for v in tensor.detach().reshape(-1)]


def run_positive_tests():
    graph = build_cycle_graph()
    data, index = graph_to_pyg(graph)
    out = SumMessage()(data.x, data.edge_index)
    nx_reference = networkx_incoming_sum(graph)
    expected = torch.tensor([nx_reference[node] for node in graph.nodes])

    return {
        "networkx_edges_roundtrip_into_pyg_messages": {
            "passed": torch.allclose(out.reshape(-1), expected),
            "networkx_reference": [float(v) for v in expected],
            "pyg_output": _as_list(out),
            "node_order": list(graph.nodes),
            "node_index": index,
            "edge_semantics": "NetworkX edge src->dst becomes PyG edge_index[0]->edge_index[1]",
        },
        "pyg_data_preserves_node_and_edge_counts": {
            "passed": int(data.num_nodes) == graph.number_of_nodes()
            and data.edge_index.shape == (2, graph.number_of_edges()),
            "networkx_nodes": graph.number_of_nodes(),
            "pyg_num_nodes": int(data.num_nodes),
            "networkx_edges": graph.number_of_edges(),
            "pyg_edge_index_shape": list(data.edge_index.shape),
        },
    }


def run_negative_tests():
    graph = build_cycle_graph()
    data, _ = graph_to_pyg(graph)
    reversed_edge_index = data.edge_index.flip(0)
    reversed_out = SumMessage()(data.x, reversed_edge_index)
    expected_forward = torch.tensor([3.0, 1.0, 2.0])

    duplicate_order_rejected = False
    duplicate_error = ""
    try:
        graph_to_pyg(graph, node_order=["a", "a", "c"])
    except ValueError as exc:
        duplicate_order_rejected = True
        duplicate_error = str(exc)

    missing_order_rejected = False
    missing_error = ""
    try:
        graph_to_pyg(graph, node_order=["a", "b"])
    except ValueError as exc:
        missing_order_rejected = True
        missing_error = str(exc)

    return {
        "reversed_orientation_excluded": {
            "passed": not torch.allclose(reversed_out.reshape(-1), expected_forward),
            "forward_expected_output": [3.0, 1.0, 2.0],
            "reversed_edge_output": _as_list(reversed_out),
            "exclusion_note": "The NetworkX-to-PyG edge orientation is load-bearing.",
        },
        "duplicate_or_missing_node_mapping_excluded": {
            "passed": duplicate_order_rejected and missing_order_rejected,
            "duplicate_error": duplicate_error,
            "missing_error": missing_error,
            "exclusion_note": "A node mapping must cover each graph node exactly once.",
        },
    }


def run_boundary_tests():
    graph = nx.DiGraph()
    graph.add_node("source", feature=5.0)
    graph.add_node("target", feature=7.0)
    graph.add_node("isolated", feature=11.0)
    graph.add_edge("source", "target")

    data, _ = graph_to_pyg(graph)
    out = SumMessage()(data.x, data.edge_index)

    empty = nx.DiGraph()
    empty_data, _ = graph_to_pyg(empty)

    return {
        "isolated_node_is_preserved_with_zero_incoming_message": {
            "passed": int(data.num_nodes) == 3
            and torch.allclose(out.reshape(-1), torch.tensor([0.0, 5.0, 0.0])),
            "node_order": list(graph.nodes),
            "expected_output": [0.0, 5.0, 0.0],
            "pyg_output": _as_list(out),
            "boundary_note": "The isolated NetworkX node survives the PyG Data handoff through num_nodes.",
        },
        "empty_graph_handoff_is_valid_zero_edge_data": {
            "passed": int(empty_data.num_nodes) == 0
            and list(empty_data.edge_index.shape) == [2, 0]
            and list(empty_data.x.shape) == [0],
            "pyg_num_nodes": int(empty_data.num_nodes),
            "pyg_edge_index_shape": list(empty_data.edge_index.shape),
            "pyg_x_shape": list(empty_data.x.shape),
        },
    }


def _flatten_sections(*sections):
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    flat_tests = _flatten_sections(positive, negative, boundary)
    all_pass = all(test.get("passed") for test in flat_tests)

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        **CANDIDATE_SIM_SPEC,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "prior_function_receipts": {"pyg": PYG_PRIOR_RECEIPT},
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "NetworkX algorithm coverage, PyG batching, heterogeneous graphs, graph neural networks, and lego graph-cell promotion remain separate future receipts.",
            "The older NetworkX capability JSON is treated as contextual history, not as a strict prior receipt for this clean integration micro.",
        ],
        "demotion_condition": (
            "Demote this NetworkX-PyG handoff if node mappings are not exact, "
            "edge orientation is not preserved, isolated nodes disappear, or "
            "PyG messages diverge from NetworkX incoming-neighbor sums."
        ),
        "out_of_scope": [
            "no graph-cell lego promotion",
            "no density-matrix or bridge claim",
            "no GNN training claim",
            "no proof of the whole NetworkX or PyG libraries",
            "no tool-tool coupling beyond this exact graph handoff",
        ],
        "criteria_checked": [
            "NetworkX directed graph node/edge extraction",
            "exact node-order mapping into PyG Data",
            "PyG source-to-target message passing",
            "edge-orientation exclusion",
            "isolated-node boundary preservation",
        ],
        "claim_ceiling": "tool_tool_micro_integration_only",
        "next_lego_target": "bounded NetworkX-to-PyG graph handoff fixture before graph-cell or density-carrier lego promotion",
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact "
            "NetworkX-PyG handoff receipt plus its PyG parent receipt; this micro "
            "row does not promote a lego or broad graph-learning claim"
        ),
        "blocked_until": (
            "blocked from lego, bridge, axis, engine, or nonclassical promotion until "
            "a downstream target passes strict admission with this receipt as a named parent"
        ),
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=NAME)

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
