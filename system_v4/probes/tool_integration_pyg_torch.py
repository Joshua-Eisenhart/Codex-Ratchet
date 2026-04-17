#!/usr/bin/env python3
"""
Tier A A4.3 tool-lego-integration probe for PyG + PyTorch.

PyTorch is load-bearing for parameterized node features, edge weights, losses, and
backpropagation. PyG is load-bearing for graph realization, message passing, and
batch pooling over those torch-derived tensors. Each section uses actual interop:
values computed in torch are fed into PyG, and PyG outputs are pulled back into a
PyTorch loss or comparison.

Hermes workers save and enqueue this probe but do not execute it directly.
"""

import json
import os
from typing import Any, Dict

classification = "canonical"
NAME = "tool_integration_pyg_torch"

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "PyTorch supplies the parameterized node features, learnable edge weights, tensor losses, and gradient checks that feed directly into the graph layer; removing torch breaks every integration claim.",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "PyG realizes the torch-built graphs, propagates weighted messages, validates graph structure, and pools graph summaries; removing PyG excludes the graph-side admissibility claim rather than just an import.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
}

try:
    import torch

    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    torch = None
    TOOL_MANIFEST["pytorch"]["reason"] = "PyTorch import failed on this machine; queued execution will decide whether tensor construction and autograd are available."

try:
    from torch_geometric.data import Batch, Data
    from torch_geometric.nn import MessagePassing, global_mean_pool

    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    Batch = Data = MessagePassing = global_mean_pool = None
    TOOL_MANIFEST["pyg"]["reason"] = "PyG import failed on this machine; queued execution will decide whether graph realization and message passing over torch tensors are available."


class WeightedNeighborConv(MessagePassing if MessagePassing is not None else object):
    def __init__(self):
        if MessagePassing is None:
            raise RuntimeError("PyG MessagePassing is unavailable")
        super().__init__(aggr="add")

    def forward(self, x, edge_index, edge_weight):
        return self.propagate(edge_index, x=x, edge_weight=edge_weight)

    def message(self, x_j, edge_weight):
        return x_j * edge_weight.view(-1, 1)



def _integration_ready() -> bool:
    return (
        TOOL_MANIFEST["pytorch"]["tried"]
        and TOOL_MANIFEST["pyg"]["tried"]
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
    return value



def _gate_results(section: str) -> Dict[str, Any]:
    missing = []
    if not TOOL_MANIFEST["pytorch"]["tried"]:
        missing.append("pytorch")
    if not TOOL_MANIFEST["pyg"]["tried"]:
        missing.append("pyg")
    return {f"{section}_import_gate": {"status": "skipped", "missing": missing}}



def _make_weighted_graph(feature_scale, left_edge_weight, right_edge_weight):
    node_positions = torch.tensor([[0.0], [1.0], [3.0]], dtype=torch.float32)
    x = feature_scale * node_positions
    edge_index = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long)
    edge_weight = torch.stack(
        [left_edge_weight, left_edge_weight, right_edge_weight, right_edge_weight]
    ).to(dtype=torch.float32)
    data = Data(x=x, edge_index=edge_index, edge_weight=edge_weight, num_nodes=3)
    return data



def _manual_weighted_sum(x, left_edge_weight, right_edge_weight):
    return torch.stack(
        [
            left_edge_weight * x[1],
            left_edge_weight * x[0] + right_edge_weight * x[2],
            right_edge_weight * x[1],
        ]
    )



def run_positive_tests():
    if not _integration_ready():
        return _gate_results("positive")

    conv = WeightedNeighborConv()
    results = {}

    feature_scale = torch.tensor(2.0, requires_grad=True)
    left_edge_weight = torch.tensor(1.5, requires_grad=True)
    right_edge_weight = torch.tensor(0.5, requires_grad=True)
    graph = _make_weighted_graph(feature_scale, left_edge_weight, right_edge_weight)
    propagated = conv(graph.x, graph.edge_index, graph.edge_weight)
    expected = _manual_weighted_sum(graph.x, left_edge_weight, right_edge_weight)
    loss = propagated.sum()
    loss.backward()
    _mark_used("pytorch", "pyg")
    results["torch_parameters_feed_pyg_message_passing_and_backprop"] = {
        "node_features_from_torch": _serialize(graph.x),
        "edge_weights_from_torch": _serialize(graph.edge_weight),
        "pyg_output": _serialize(propagated),
        "manual_expected": _serialize(expected),
        "matches_expected": bool(torch.allclose(propagated, expected, atol=1e-7, rtol=0.0)),
        "loss": _serialize(loss),
        "feature_scale_grad": _serialize(feature_scale.grad),
        "left_edge_weight_grad": _serialize(left_edge_weight.grad),
        "right_edge_weight_grad": _serialize(right_edge_weight.grad),
        "all_grads_present": all(
            grad is not None for grad in [feature_scale.grad, left_edge_weight.grad, right_edge_weight.grad]
        ),
    }

    batch_scale = torch.tensor(1.0, requires_grad=True)
    graph_a = Data(
        x=batch_scale * torch.tensor([[1.0], [3.0]], dtype=torch.float32),
        edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long),
        num_nodes=2,
    )
    graph_b = Data(
        x=batch_scale * torch.tensor([[2.0], [4.0], [8.0]], dtype=torch.float32),
        edge_index=torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long),
        num_nodes=3,
    )
    batch = Batch.from_data_list([graph_a, graph_b])
    pooled = global_mean_pool(batch.x, batch.batch)
    target = torch.tensor([[2.0], [14.0 / 3.0]], dtype=torch.float32)
    pooled_loss = torch.nn.functional.mse_loss(pooled, target)
    pooled_loss.backward()
    _mark_used("pytorch", "pyg")
    results["torch_feature_scaling_feeds_pyg_batch_pooling"] = {
        "batch_vector": _serialize(batch.batch),
        "pooled_means": _serialize(pooled),
        "expected_means": [[2.0], [14.0 / 3.0]],
        "matches_expected": bool(torch.allclose(pooled, target, atol=1e-7, rtol=0.0)),
        "pooling_loss": _serialize(pooled_loss),
        "batch_scale_grad": _serialize(batch_scale.grad),
        "batch_scale_grad_present": batch_scale.grad is not None,
    }

    return results



def run_negative_tests():
    if not _integration_ready():
        return _gate_results("negative")

    conv = WeightedNeighborConv()
    results = {}

    detached_edge_weight = torch.tensor(2.0, requires_grad=True)
    feature_scale = torch.tensor(1.0, requires_grad=True)
    graph = _make_weighted_graph(feature_scale, detached_edge_weight.detach(), torch.tensor(1.0))
    propagated = conv(graph.x, graph.edge_index, graph.edge_weight)
    loss = propagated.sum()
    loss.backward()
    _mark_used("pytorch", "pyg")
    results["detached_torch_edge_weight_excludes_gradient_return_from_pyg"] = {
        "edge_weights_fed_to_pyg": _serialize(graph.edge_weight),
        "pyg_output": _serialize(propagated),
        "feature_scale_grad": _serialize(feature_scale.grad),
        "detached_edge_weight_grad": _serialize(detached_edge_weight.grad),
        "feature_gradient_survives": feature_scale.grad is not None,
        "detached_edge_weight_blocks_grad": detached_edge_weight.grad is None,
    }

    invalid_num_nodes = torch.tensor(2)
    malformed = Data(
        x=torch.tensor([[1.0], [2.0]], dtype=torch.float32),
        edge_index=torch.tensor([[0, 1], [1, 2]], dtype=torch.long),
        num_nodes=int(invalid_num_nodes.item()),
    )
    valid_flag = malformed.validate(raise_on_error=False)
    try:
        malformed.validate(raise_on_error=True)
        error_text = None
    except ValueError as exc:
        error_text = str(exc)
    _mark_used("pytorch", "pyg")
    results["torch_built_out_of_range_edges_are_excluded_by_pyg_validation"] = {
        "num_nodes_from_torch": int(invalid_num_nodes.item()),
        "edge_index_from_torch": _serialize(malformed.edge_index),
        "pyg_validate_flag": bool(valid_flag),
        "raised_value_error": error_text is not None,
        "error": error_text,
    }

    return results



def run_boundary_tests():
    if not _integration_ready():
        return _gate_results("boundary")

    conv = WeightedNeighborConv()
    results = {}

    zero_weight = torch.tensor(0.0, requires_grad=True)
    boundary_scale = torch.tensor(3.0, requires_grad=True)
    boundary_graph = _make_weighted_graph(boundary_scale, zero_weight, torch.tensor(0.0))
    propagated = conv(boundary_graph.x, boundary_graph.edge_index, boundary_graph.edge_weight)
    zero_loss = propagated.sum()
    zero_loss.backward()
    _mark_used("pytorch", "pyg")
    results["zero_torch_edge_weights_yield_zero_pyg_messages"] = {
        "node_features_from_torch": _serialize(boundary_graph.x),
        "edge_weights_from_torch": _serialize(boundary_graph.edge_weight),
        "pyg_output": _serialize(propagated),
        "expected": [[0.0], [0.0], [0.0]],
        "matches_expected": bool(
            torch.allclose(propagated, torch.zeros_like(propagated), atol=1e-7, rtol=0.0)
        ),
        "boundary_scale_grad": _serialize(boundary_scale.grad),
        "zero_weight_grad": _serialize(zero_weight.grad),
    }

    singleton_scale = torch.tensor(4.0, requires_grad=True)
    singleton = Data(
        x=singleton_scale * torch.tensor([[1.0]], dtype=torch.float32),
        edge_index=torch.empty((2, 0), dtype=torch.long),
        edge_weight=torch.empty((0,), dtype=torch.float32),
        num_nodes=1,
    )
    singleton_out = conv(singleton.x, singleton.edge_index, singleton.edge_weight)
    _mark_used("pytorch", "pyg")
    results["single_node_torch_graph_survives_empty_pyg_edge_set"] = {
        "node_features_from_torch": _serialize(singleton.x),
        "pyg_output": _serialize(singleton_out),
        "expected": [[0.0]],
        "matches_expected": bool(
            torch.allclose(singleton_out, torch.zeros_like(singleton_out), atol=1e-7, rtol=0.0)
        ),
        "singleton_scale_requires_grad": bool(singleton.x.requires_grad),
    }

    return results


if __name__ == "__main__":
    results = {
        "name": NAME,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(_serialize(results), handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
