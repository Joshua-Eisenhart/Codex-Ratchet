#!/usr/bin/env python3
"""
tool_capability_pyg.py

Tier A A0.4 tool-capability probe for PyG.

This probe keeps scope thin: PyG is the only tool listed in the manifest, and
all sections exercise PyG data validation, batching, and message propagation.
The probe is canonical by process once committed and enqueued, but Hermes does
not execute it directly.
"""

import json
import os

classification = "canonical"
NAME = "tool_capability_pyg"

TOOL_MANIFEST = {
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "PyG is the sole graph-learning tool under test; its Data, Batch, pooling, and message-passing APIs are load-bearing in every section.",
    }
}

TOOL_INTEGRATION_DEPTH = {"pyg": "load_bearing"}

try:
    import torch
    from torch_geometric.data import Batch, Data
    from torch_geometric.nn import MessagePassing, global_mean_pool

    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    torch = None
    Batch = Data = MessagePassing = global_mean_pool = None
    TOOL_MANIFEST["pyg"]["reason"] = "PyG import failed on this machine; queue execution will show whether torch-geometric and its runtime substrate are installed."


class SumNeighborConv(MessagePassing if MessagePassing is not None else object):
    def __init__(self):
        if MessagePassing is None:
            raise RuntimeError("PyG MessagePassing is unavailable")
        super().__init__(aggr="add")

    def forward(self, x, edge_index):
        return self.propagate(edge_index, x=x)

    def message(self, x_j):
        return x_j


def _mark_pyg_used() -> None:
    TOOL_MANIFEST["pyg"]["used"] = True


def _tensor_to_list(value):
    if value is None:
        return None
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): _tensor_to_list(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_tensor_to_list(v) for v in value]
    return value


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["pyg"]["tried"]:
        results["pyg_import_gate"] = {"status": "skipped", "reason": "PyG not importable"}
        return results

    conv = SumNeighborConv()

    # Positive 1: directed message passing on a three-node path.
    x = torch.tensor([[1.0], [2.0], [4.0]])
    edge_index = torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long)
    propagated = conv(x, edge_index)
    _mark_pyg_used()
    results["path_graph_neighbor_sum"] = {
        "status": "ok",
        "expected": [[2.0], [5.0], [2.0]],
        "actual": _tensor_to_list(propagated),
        "matches_expected": _tensor_to_list(propagated) == [[2.0], [5.0], [2.0]],
        "edge_index": _tensor_to_list(edge_index),
    }

    # Positive 2: batching keeps graph membership and pooled means separate.
    batch = Batch.from_data_list(
        [
            Data(
                x=torch.tensor([[1.0], [2.0]]),
                edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long),
            ),
            Data(
                x=torch.tensor([[3.0], [5.0], [7.0]]),
                edge_index=torch.tensor([[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long),
            ),
        ]
    )
    pooled = global_mean_pool(batch.x, batch.batch)
    _mark_pyg_used()
    results["batch_and_pool_two_graphs"] = {
        "status": "ok",
        "batch_vector": _tensor_to_list(batch.batch),
        "expected_means": [[1.5], [5.0]],
        "actual_means": _tensor_to_list(pooled),
        "matches_expected": _tensor_to_list(pooled) == [[1.5], [5.0]],
        "num_graphs": int(batch.num_graphs),
    }

    # Positive 3: Data.validate admits a well-formed graph.
    valid_graph = Data(
        x=torch.tensor([[0.0], [1.0], [0.0]]),
        edge_index=torch.tensor([[0, 1, 2], [1, 2, 1]], dtype=torch.long),
        num_nodes=3,
    )
    is_valid = valid_graph.validate(raise_on_error=False)
    _mark_pyg_used()
    results["validate_well_formed_graph"] = {
        "status": "ok",
        "expected": True,
        "actual": bool(is_valid),
        "num_nodes": int(valid_graph.num_nodes),
        "num_edges": int(valid_graph.edge_index.size(1)),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["pyg"]["tried"]:
        results["pyg_import_gate"] = {"status": "skipped", "reason": "PyG not importable"}
        return results

    # Negative 1: edge indices outside declared node range are excluded.
    out_of_range = Data(
        x=torch.tensor([[1.0], [2.0]]),
        edge_index=torch.tensor([[0, 1], [1, 2]], dtype=torch.long),
        num_nodes=2,
    )
    valid_flag = out_of_range.validate(raise_on_error=False)
    try:
        out_of_range.validate(raise_on_error=True)
        error_text = None
    except ValueError as exc:
        error_text = str(exc)
    _mark_pyg_used()
    results["exclude_out_of_range_edge_index"] = {
        "status": "ok",
        "expected": False,
        "actual": bool(valid_flag),
        "raised_value_error": error_text is not None,
        "error": error_text,
    }

    # Negative 2: malformed edge_index rank is excluded.
    malformed = Data(
        x=torch.tensor([[1.0], [2.0]]),
        edge_index=torch.tensor([[0, 1]], dtype=torch.long),
    )
    malformed_flag = malformed.validate(raise_on_error=False)
    try:
        malformed.validate(raise_on_error=True)
        malformed_error = None
    except ValueError as exc:
        malformed_error = str(exc)
    _mark_pyg_used()
    results["exclude_bad_edge_index_shape"] = {
        "status": "ok",
        "expected": False,
        "actual": bool(malformed_flag),
        "raised_value_error": malformed_error is not None,
        "error": malformed_error,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["pyg"]["tried"]:
        results["pyg_import_gate"] = {"status": "skipped", "reason": "PyG not importable"}
        return results

    conv = SumNeighborConv()

    # Boundary 1: isolated single-node graph stays well-defined.
    isolated_x = torch.tensor([[7.0]])
    isolated_edges = torch.empty((2, 0), dtype=torch.long)
    isolated_messages = conv(isolated_x, isolated_edges)
    _mark_pyg_used()
    results["isolated_single_node_graph"] = {
        "status": "ok",
        "expected": [[0.0]],
        "actual": _tensor_to_list(isolated_messages),
        "matches_expected": _tensor_to_list(isolated_messages) == [[0.0]],
        "edge_count": int(isolated_edges.size(1)),
    }

    # Boundary 2: parallel edges accumulate duplicate messages exactly once per edge.
    duplicate_x = torch.tensor([[1.0], [0.0]])
    duplicate_edges = torch.tensor([[0, 0], [1, 1]], dtype=torch.long)
    duplicate_messages = conv(duplicate_x, duplicate_edges)
    _mark_pyg_used()
    results["parallel_edges_accumulate"] = {
        "status": "ok",
        "expected": [[0.0], [2.0]],
        "actual": _tensor_to_list(duplicate_messages),
        "matches_expected": _tensor_to_list(duplicate_messages) == [[0.0], [2.0]],
        "edge_index": _tensor_to_list(duplicate_edges),
    }

    # Boundary 3: a singleton batch still reports one graph and preserves its mean.
    singleton_batch = Batch.from_data_list(
        [
            Data(
                x=torch.tensor([[4.0], [6.0]]),
                edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long),
            )
        ]
    )
    singleton_mean = global_mean_pool(singleton_batch.x, singleton_batch.batch)
    _mark_pyg_used()
    results["singleton_batch_pool"] = {
        "status": "ok",
        "expected": [[5.0]],
        "actual": _tensor_to_list(singleton_mean),
        "matches_expected": _tensor_to_list(singleton_mean) == [[5.0]],
        "num_graphs": int(singleton_batch.num_graphs),
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
        json.dump(_tensor_to_list(results), handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
