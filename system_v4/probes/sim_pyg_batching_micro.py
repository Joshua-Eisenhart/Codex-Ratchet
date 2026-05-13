#!/usr/bin/env python3
"""PyG Batch.from_data_list micro probe.

Tool-stage scope:
  - one primary tool: PyG
  - one API surface: torch_geometric.data.Batch.from_data_list
  - one tiny claim: batching tiny Data graph fixtures concatenates tensor
    attributes while offsetting graph-local edge indexes and preserving graph
    membership metadata.

This is tool_function_micro_only evidence. It does not train a model, promote a
graph-cell lego, couple e3nn, use HeteroData, or make bridge/axis claims.
"""

import json
import os

import torch
from torch_geometric.data import Batch, Data

classification = "canonical"
NAME = "sim_pyg_batching_micro"
PROBE_FAMILY = "pyg_batching_micro"
CONSTRAINT_SET = "tiny_data_fixtures_batch_from_data_list"

_NOT_USED_REASON = (
    "not used: this micro probe isolates PyG Batch.from_data_list on tiny Data "
    "fixtures; proof tools, topology tools, equivariance tools, and graph-cell "
    "promotion are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "PyTorch is supportive: tensors provide the tiny graph fixtures and "
            "expected batched values checked against PyG output."
        ),
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": (
            "PyG is load-bearing: Batch.from_data_list is the only API surface "
            "under test and supplies the offset edge_index, batch vector, and ptr."
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
TOOL_INTEGRATION_DEPTH["pyg"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"


def _make_fixtures():
    graph_a = Data(
        x=torch.tensor([[1.0], [2.0], [3.0]], dtype=torch.float),
        edge_index=torch.tensor([[0, 1], [1, 2]], dtype=torch.long),
        y=torch.tensor([10], dtype=torch.long),
    )
    graph_b = Data(
        x=torch.tensor([[5.0], [7.0]], dtype=torch.float),
        edge_index=torch.tensor([[0], [1]], dtype=torch.long),
        y=torch.tensor([20], dtype=torch.long),
    )
    return graph_a, graph_b


def _tensor_list(tensor):
    return tensor.detach().cpu().tolist()


def run_positive_tests():
    graph_a, graph_b = _make_fixtures()
    batch = Batch.from_data_list([graph_a, graph_b])

    expected_x = torch.tensor([[1.0], [2.0], [3.0], [5.0], [7.0]])
    expected_edge_index = torch.tensor([[0, 1, 3], [1, 2, 4]], dtype=torch.long)
    expected_batch = torch.tensor([0, 0, 0, 1, 1], dtype=torch.long)
    expected_ptr = torch.tensor([0, 3, 5], dtype=torch.long)
    expected_y = torch.tensor([10, 20], dtype=torch.long)

    return {
        "batch_offsets_second_graph_edge_index": {
            "passed": torch.equal(batch.edge_index, expected_edge_index),
            "expected_edge_index": _tensor_list(expected_edge_index),
            "observed_edge_index": _tensor_list(batch.edge_index),
            "fixture_note": "graph_b edge 0->1 is shifted to global edge 3->4",
        },
        "batch_concatenates_node_features": {
            "passed": torch.equal(batch.x, expected_x),
            "expected_x": _tensor_list(expected_x),
            "observed_x": _tensor_list(batch.x),
        },
        "batch_records_graph_membership": {
            "passed": torch.equal(batch.batch, expected_batch) and torch.equal(batch.ptr, expected_ptr),
            "expected_batch": _tensor_list(expected_batch),
            "observed_batch": _tensor_list(batch.batch),
            "expected_ptr": _tensor_list(expected_ptr),
            "observed_ptr": _tensor_list(batch.ptr),
        },
        "batch_preserves_graph_level_targets": {
            "passed": torch.equal(batch.y, expected_y),
            "expected_y": _tensor_list(expected_y),
            "observed_y": _tensor_list(batch.y),
        },
    }


def run_negative_tests():
    graph_a, graph_b = _make_fixtures()
    batch = Batch.from_data_list([graph_a, graph_b])

    stale_unoffset_edge_index = torch.cat([graph_a.edge_index, graph_b.edge_index], dim=1)
    wrong_membership = torch.tensor([0, 0, 0, 0, 0], dtype=torch.long)

    return {
        "raw_concatenation_does_not_match_pyg_offsets": {
            "passed": not torch.equal(batch.edge_index, stale_unoffset_edge_index),
            "stale_unoffset_edge_index": _tensor_list(stale_unoffset_edge_index),
            "pyg_edge_index": _tensor_list(batch.edge_index),
            "exclusion_note": "Batch.from_data_list must not leave later graph edge indexes in local coordinates.",
        },
        "single_membership_vector_excluded": {
            "passed": not torch.equal(batch.batch, wrong_membership),
            "wrong_membership": _tensor_list(wrong_membership),
            "pyg_batch": _tensor_list(batch.batch),
            "exclusion_note": "The output is a disjoint batch, not one unlabeled merged graph.",
        },
    }


def run_boundary_tests():
    single_node_graph = Data(
        x=torch.tensor([[11.0]], dtype=torch.float),
        edge_index=torch.empty((2, 0), dtype=torch.long),
    )
    batch = Batch.from_data_list([single_node_graph])

    empty_raised = False
    empty_error = ""
    try:
        Batch.from_data_list([])
    except (IndexError, RuntimeError, ValueError) as exc:
        empty_raised = True
        empty_error = type(exc).__name__

    return {
        "single_graph_empty_edge_batch_is_well_formed": {
            "passed": (
                batch.num_graphs == 1
                and batch.num_nodes == 1
                and batch.edge_index.shape == (2, 0)
                and torch.equal(batch.batch, torch.tensor([0], dtype=torch.long))
                and torch.equal(batch.ptr, torch.tensor([0, 1], dtype=torch.long))
            ),
            "num_graphs": int(batch.num_graphs),
            "num_nodes": int(batch.num_nodes),
            "edge_index_shape": list(batch.edge_index.shape),
            "batch": _tensor_list(batch.batch),
            "ptr": _tensor_list(batch.ptr),
        },
        "empty_data_list_rejected": {
            "passed": empty_raised,
            "expected": "Batch.from_data_list requires at least one Data object",
            "error_type": empty_error,
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
        "scope": "tool_function_micro_only",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "operation_sequence": [
            "construct two tiny torch_geometric.data.Data graph fixtures with local edge indexes",
            "call torch_geometric.data.Batch.from_data_list on the fixture list",
            "compare batched node-feature concatenation to the manual tensor baseline",
            "compare batched edge_index to the expected PyG graph-local offset baseline",
            "compare batch and ptr graph-membership metadata to expected tensors",
            "run adjacent negative fixtures for raw unoffset concatenation and a single unlabeled membership vector",
            "run boundary fixtures for one empty-edge graph and an empty input list",
        ],
        "carrier_topology": (
            "finite disjoint graph fixtures represented as PyG Data objects and "
            "batched into one disconnected graph carrier with explicit node "
            "membership metadata; no topology, graph-cell, bridge, axis, GStack, "
            "or nonclassical carrier is claimed"
        ),
        "observable": {
            "node_feature_tensor": "batched x tensor equals manual concatenation of graph_a.x and graph_b.x",
            "offset_edge_index": "second graph local edge 0->1 is shifted to global edge 3->4",
            "graph_membership": "batch vector and ptr delimit graph membership after batching",
            "graph_level_targets": "y values are preserved as graph-level targets",
            "negative_controls": "raw unoffset edge concatenation and all-zero graph membership must not match PyG output",
            "boundary_controls": "single empty-edge graph remains well-formed and empty input list raises",
        },
        "pass_fail_predicate": (
            "All positive, negative, and boundary checks must pass: Batch.from_data_list "
            "must concatenate node features, offset later graph edge indexes, preserve "
            "graph membership metadata and targets, reject raw-unoffset and unlabeled "
            "membership alternatives, accept a one-node empty-edge graph, and reject an "
            "empty data-list input."
        ),
        "graveyards": [
            "raw concatenation of edge_index without node-offset correction -- must differ from PyG output",
            "single all-zero membership vector for all nodes -- must differ from PyG batch metadata",
            "empty data list treated as a meaningful batch -- must raise instead",
            "graph-level target y dropped during batching -- must fail target preservation",
        ],
        "baselines": [
            "manual torch.cat node-feature concatenation",
            "manual edge_index offset for graph_b by graph_a.num_nodes",
            "manual graph-membership batch vector [0, 0, 0, 1, 1]",
            "manual ptr vector [0, 3, 5]",
        ],
        "alternative_formulations": [
            "NetworkX disjoint_union node relabeling followed by PyG Data conversion",
            "manual PyTorch-only batching dictionary with x, edge_index, batch, and ptr",
            "PyG Batch.from_data_list over more than two fixtures in a later boundary packet",
        ],
        "tool_function_needs": [
            "torch_geometric.data.Data",
            "torch_geometric.data.Batch.from_data_list",
            "Batch.edge_index offsetting",
            "Batch.batch graph-membership vector",
            "Batch.ptr graph-boundary vector",
            "torch.equal",
            "torch.tensor",
        ],
        "lego_coupling_target": [
            "pyg_data_batching_fixture",
            "graph_fixture_handoff_rows",
            "later graph-message-passing micro packets",
        ],
        "surviving_alternatives": [
            "PyG Data loaders, HeteroData batching, message passing, training loops, and graph-cell uses remain separate future surfaces."
        ],
        "claim_ceiling": "tool_function_micro_only",
        "next_lego_target": (
            "minimal PyG Data batching fixture before graph-native or "
            "graph-cell promotion"
        ),
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact "
            "function receipt and passes strict runner admission; this MICRO "
            "row does not promote any lego"
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact graph "
            "target, parent receipt use, and active stage gate for promotion"
        ),
        "demotion_condition": (
            "Demote PyG for this batching surface if Batch.from_data_list stops "
            "offsetting graph-local edge indexes, loses graph membership metadata, "
            "or silently accepts an empty data list as a meaningful batch."
        ),
        "out_of_scope": [
            "no training",
            "no HeteroData use",
            "no e3nn coupling",
            "no graph-cell promotion",
            "no bridge claim",
            "no axis claim",
            "no proof of the whole PyG library",
        ],
        "criteria_checked": [
            "node feature concatenation",
            "edge_index offsetting across Data fixtures",
            "graph membership vector and ptr construction",
            "graph-level target preservation",
            "single empty-edge graph boundary",
            "empty data list rejection",
        ],
        "summary": {"passed": sum(1 for test in flat_tests if test.get("passed")), "total": len(flat_tests)},
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
