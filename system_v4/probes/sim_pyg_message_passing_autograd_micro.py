#!/usr/bin/env python3
"""PyG message-passing/autograd micro probe.

Tool-stage scope:
  - one primary tool: PyG
  - one API surface: torch_geometric.nn.MessagePassing.propagate
  - one tiny claim: a bounded directed graph message pass aggregates the
    intended source features and keeps gradients flowing through PyTorch.

This is pre-lego evidence. It does not promote a lego, coupling, bridge, or
stack claim.
"""

import json
import os

import torch
from torch_geometric.nn import MessagePassing

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"
NAME = "sim_pyg_message_passing_autograd_micro"
PROBE_FAMILY = "pyg_message_passing_autograd_micro"
CONSTRAINT_SET = "bounded_directed_cycle_message_passing_fixture"

_NOT_USED_REASON = (
    "not used: this micro probe isolates PyG MessagePassing.propagate with a "
    "PyTorch autograd backend; cross-tool coupling and lego promotion are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "PyTorch is supportive: tensors and autograd carry the gradient check "
            "for the PyG message-passing output."
        ),
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": (
            "PyG is load-bearing: MessagePassing.propagate produces the directed "
            "neighbor aggregation verdicts."
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


class SumMessage(MessagePassing):
    def __init__(self):
        super().__init__(aggr="add")

    def forward(self, x, edge_index):
        return self.propagate(edge_index, x=x)

    def message(self, x_j):
        return x_j


def _as_list(tensor):
    return [float(v) for v in tensor.detach().reshape(-1)]


def run_positive_tests():
    edge_index = torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long)
    x = torch.tensor([[1.0], [2.0], [3.0]], requires_grad=True)
    layer = SumMessage()
    out = layer(x, edge_index)
    loss = out.square().sum()
    loss.backward()

    return {
        "directed_cycle_aggregates_source_features": {
            "passed": torch.allclose(out.detach().reshape(-1), torch.tensor([3.0, 1.0, 2.0])),
            "expected_output": [3.0, 1.0, 2.0],
            "pyg_output": _as_list(out),
            "edge_semantics": "edge_index[0] sends source features to edge_index[1] targets",
        },
        "message_passing_preserves_autograd": {
            "passed": torch.allclose(x.grad.detach().reshape(-1), torch.tensor([2.0, 4.0, 6.0])),
            "expected_gradient": [2.0, 4.0, 6.0],
            "observed_gradient": _as_list(x.grad),
        },
    }


def run_negative_tests():
    layer = SumMessage()
    edge_index = torch.tensor([[1, 2, 0], [0, 1, 2]], dtype=torch.long)
    x = torch.tensor([[1.0], [2.0], [3.0]], requires_grad=True)
    reversed_out = layer(x, edge_index)
    expected_forward = torch.tensor([3.0, 1.0, 2.0])

    malformed_raised = False
    malformed_error = ""
    try:
        layer(x, torch.tensor([[0, 1, 2]], dtype=torch.long))
    except (IndexError, RuntimeError, ValueError) as exc:
        malformed_raised = True
        malformed_error = type(exc).__name__

    return {
        "reversed_edges_do_not_match_forward_cycle": {
            "passed": not torch.allclose(reversed_out.detach().reshape(-1), expected_forward),
            "forward_expected_output": [3.0, 1.0, 2.0],
            "reversed_edge_output": _as_list(reversed_out),
            "exclusion_note": "The edge orientation is load-bearing, not decorative.",
        },
        "malformed_edge_index_excluded": {
            "passed": malformed_raised,
            "expected": "PyG rejects an edge_index that is not shaped [2, num_edges]",
            "error_type": malformed_error,
        },
    }


def run_boundary_tests():
    edge_index = torch.tensor([[0], [1]], dtype=torch.long)
    x = torch.tensor([[5.0], [7.0], [11.0]], requires_grad=True)
    layer = SumMessage()
    out = layer(x, edge_index)
    out.sum().backward()

    return {
        "isolated_node_receives_zero_message": {
            "passed": torch.allclose(out.detach().reshape(-1), torch.tensor([0.0, 5.0, 0.0])),
            "expected_output": [0.0, 5.0, 0.0],
            "pyg_output": _as_list(out),
            "boundary_note": "Node 2 has no incoming edge and receives the additive identity.",
        },
        "isolated_node_has_zero_gradient_from_output_sum": {
            "passed": torch.allclose(x.grad.detach().reshape(-1), torch.tensor([1.0, 0.0, 0.0])),
            "expected_gradient": [1.0, 0.0, 0.0],
            "observed_gradient": _as_list(x.grad),
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
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "operation_sequence": [
            "define a minimal torch_geometric.nn.MessagePassing subclass with additive aggregation",
            "construct a three-node directed cycle edge_index and scalar node-feature tensor",
            "call MessagePassing.propagate through the subclass forward method",
            "compare propagated output to the manual source-to-target aggregation baseline",
            "backpropagate a squared-output loss through the PyG propagation result",
            "run negative fixtures for reversed edge orientation and malformed edge_index shape",
            "run boundary fixtures for an isolated node receiving the additive identity and zero gradient",
        ],
        "carrier_topology": (
            "finite directed graph fixture with scalar PyTorch node features and "
            "PyG source-to-target edge_index semantics; no density matrix, graph-cell, "
            "bridge, axis, GStack, QIT, or nonclassical carrier is claimed"
        ),
        "observable": {
            "directed_aggregation": "output node features equal manual incoming-neighbor source sums",
            "autograd_gradient": "PyTorch gradients flow from squared propagated output back to input node features",
            "edge_orientation_control": "reversing edge_index changes the propagated output",
            "malformed_edge_control": "edge_index not shaped [2, num_edges] raises",
            "isolated_node_boundary": "node with no incoming edge receives zero under additive aggregation",
            "isolated_node_gradient_boundary": "node not contributing to output sum has zero gradient",
        },
        "pass_fail_predicate": (
            "All positive, negative, and boundary checks must pass: propagate must "
            "match manual directed aggregation, preserve autograd gradients through "
            "the output, distinguish reversed-edge orientation, reject malformed "
            "edge_index input, and handle isolated-node additive identity and "
            "gradient boundaries as expected."
        ),
        "graveyards": [
            "edge_index orientation treated as decorative -- reversed edges would match the forward cycle and must fail",
            "malformed one-row edge_index accepted silently -- must raise instead",
            "isolated node receives a nonzero additive message -- must fail boundary",
            "input feature gradients do not propagate through MessagePassing output -- must fail autograd check",
        ],
        "baselines": [
            "manual source-to-target aggregation for directed cycle 0->1, 1->2, 2->0",
            "manual gradient of squared outputs under the directed cycle fixture",
            "manual additive identity for a node with no incoming edges",
            "manual isolated-node gradient expectation under out.sum()",
        ],
        "alternative_formulations": [
            "manual PyTorch scatter-add implementation over edge_index",
            "NetworkX predecessor-sum computation followed by tensor comparison",
            "PyG GCNConv or SAGEConv message-passing checks in separate API-surface packets",
        ],
        "tool_function_needs": [
            "torch_geometric.nn.MessagePassing",
            "MessagePassing.propagate",
            "MessagePassing.message",
            "torch.tensor",
            "Tensor.square",
            "Tensor.sum",
            "Tensor.backward",
            "torch.allclose",
        ],
        "lego_coupling_target": [
            "pyg_message_passing_fixture",
            "graph_autograd_handoff_rows",
            "later density_or_graph_carrier_micro_packets",
        ],
        "surviving_alternatives": [
            "Other PyG layers, batching, heterogeneous graphs, and density-matrix gradients remain separate future micro surfaces."
        ],
        "demotion_condition": (
            "Demote PyG for this surface if MessagePassing.propagate does not "
            "respect edge orientation, if malformed edge indexes are silently "
            "accepted, or if gradients do not flow through the bounded output."
        ),
        "out_of_scope": [
            "no density-matrix entropy claim",
            "no lego promotion",
            "no tool-tool coupling beyond PyTorch backend support",
            "no bridge claim",
            "no proof of the whole PyG library",
        ],
        "criteria_checked": [
            "PyG directed source-to-target aggregation",
            "PyTorch autograd through PyG message-passing output",
            "edge-orientation exclusion",
            "isolated-node boundary behavior",
        ],
        "claim_ceiling": "tool_function_micro_only",
        "next_lego_target": "bounded PyG message-passing fixture before graph or density carrier lego promotion",
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact PyG "
            "MessagePassing receipt; this micro row does not promote any lego"
        ),
        "blocked_until": (
            "blocked from lego, bridge, axis, engine, or nonclassical promotion until "
            "a downstream target passes strict admission with this receipt as a named parent"
        ),
        "summary": {"passed": sum(1 for test in flat_tests if test.get("passed")), "total": len(flat_tests)},
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
