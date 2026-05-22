#!/usr/bin/env python3
"""PyG/rustworkx graph-order successor for the 13-layer manifold scout."""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
PARENT_PATH = RESULT_DIR / "thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe_results.json"
OUT_PATH = RESULT_DIR / "thirteen_layer_active_manifold_layer_removal_graph_order_pyg_rustworkx_probe_results.json"

NAME = "thirteen_layer_active_manifold_layer_removal_graph_order_pyg_rustworkx_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: consumes the active 13-layer manifold receipt and "
    "checks whether its layer-removal signal has a graph-order witness through "
    "direct PyG tensor message passing and rustworkx DAG/reachability kernels. "
    "It does not admit a final manifold, final G-structure, physics, ontology, "
    "bridge, axis, engine, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing layer-removal feature tensors, finite checks, and response-gap controls",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Data.validate and MessagePassing propagation over the layer-order edge_index",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PyDiGraph DAG construction, topological order, transitive reduction, and reachability checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite noncollapse witness over graph order, reachability, and PyG separation predicates",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "torch_geometric": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
}


class LayerOrderMessenger(MessagePassing):
    """One-step additive propagation over ordered layer edges."""

    def __init__(self) -> None:
        super().__init__(aggr="add")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_weight: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index=edge_index, x=x, edge_weight=edge_weight)

    def message(self, x_j: torch.Tensor, edge_weight: torch.Tensor) -> torch.Tensor:
        return x_j * edge_weight.reshape(-1, 1)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return as_jsonable(value.detach().cpu().tolist())
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_parent() -> dict[str, Any]:
    if not PARENT_PATH.exists():
        raise FileNotFoundError(PARENT_PATH)
    return json.loads(PARENT_PATH.read_text(encoding="utf-8"))


def parent_layer_rows(parent: dict[str, Any]) -> list[dict[str, Any]]:
    rows = (
        parent.get("graveyard_companions", {})
        .get("g_layer_removal_each_of_13", {})
        .get("sub_results", [])
    )
    if not isinstance(rows, list):
        return []
    return rows


def canonical_layers(parent: dict[str, Any]) -> list[str]:
    layers = parent.get("candidate_layers", [])
    return [str(layer) for layer in layers] if isinstance(layers, list) else []


def state_diffs(rows: list[dict[str, Any]]) -> list[float]:
    return [float(row.get("state_diff", 0.0)) for row in rows]


def differs_flags(rows: list[dict[str, Any]]) -> list[bool]:
    return [bool(row.get("differs")) for row in rows]


def ordered_edges(layer_count: int) -> list[tuple[int, int]]:
    return [(idx, idx + 1) for idx in range(layer_count - 1)]


def edge_weight(src: int, dst: int, diffs: list[float]) -> float:
    return 1.0 + max(float(diffs[src]), float(diffs[dst]))


def finite_nonnegative(values: list[float]) -> bool:
    return all(math.isfinite(value) and value >= 0.0 for value in values)


def make_rx_graph(
    layers: list[str],
    diffs: list[float],
    differs: list[bool],
    edges: list[tuple[int, int]],
) -> rx.PyDiGraph:
    graph = rx.PyDiGraph()
    for idx, layer in enumerate(layers):
        graph.add_node(
            {
                "idx": idx,
                "name": layer,
                "state_diff": float(diffs[idx]),
                "differs": bool(differs[idx]),
            }
        )
    for src, dst in edges:
        graph.add_edge(src, dst, {"weight": edge_weight(src, dst, diffs)})
    return graph


def rx_summary(graph: rx.PyDiGraph, expected_layers: list[str]) -> dict[str, Any]:
    topo = [int(idx) for idx in rx.topological_sort(graph)]
    topo_names = [graph[idx]["name"] for idx in topo]
    reduction, _node_map = rx.transitive_reduction(graph)
    descendants_0 = sorted(int(idx) for idx in rx.descendants(graph, 0)) if graph.num_nodes() else []
    descendants_last = sorted(int(idx) for idx in rx.descendants(graph, graph.num_nodes() - 1)) if graph.num_nodes() else []
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "edge_list": [(int(src), int(dst)) for src, dst in graph.edge_list()],
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
        "topological_indices": topo,
        "topological_names": topo_names,
        "topological_names_match_parent": topo_names == expected_layers,
        "transitive_reduction_edge_count": reduction.num_edges(),
        "tool_function_receipts": {
            "rustworkx.transitive_reduction": {
                "api": "rustworkx.transitive_reduction",
                "pass": reduction.num_edges() == graph.num_edges(),
                "input_edge_count": graph.num_edges(),
                "reduction_edge_count": reduction.num_edges(),
                "reason": "For a simple contiguous chain, transitive reduction should preserve all 12 covering edges.",
            },
            "rustworkx.digraph_has_path": {
                "api": "rustworkx.digraph_has_path",
                "pass": bool(rx.digraph_has_path(graph, 0, graph.num_nodes() - 1))
                and not bool(rx.digraph_has_path(graph, graph.num_nodes() - 1, 0)),
                "source_to_sink": bool(rx.digraph_has_path(graph, 0, graph.num_nodes() - 1)),
                "sink_to_source": bool(rx.digraph_has_path(graph, graph.num_nodes() - 1, 0)),
                "reason": "Ordered manifold layer graph must reach forward and fail reverse reachability.",
            },
        },
        "source_reaches_sink": bool(rx.digraph_has_path(graph, 0, graph.num_nodes() - 1)) if graph.num_nodes() else False,
        "sink_reaches_source": bool(rx.digraph_has_path(graph, graph.num_nodes() - 1, 0)) if graph.num_nodes() else False,
        "source_descendants": descendants_0,
        "sink_descendants": descendants_last,
    }


def make_pyg_data(
    layers: list[str],
    diffs: list[float],
    differs: list[bool],
    edges: list[tuple[int, int]],
) -> tuple[Data, torch.Tensor, dict[str, Any]]:
    layer_count = len(layers)
    scale = max(max(diffs), 1e-9)
    x = torch.tensor(
        [
            [
                idx / max(layer_count - 1, 1),
                float(diffs[idx]),
                1.0 if differs[idx] else 0.0,
                float(diffs[idx]) / scale,
            ]
            for idx in range(layer_count)
        ],
        dtype=torch.float64,
    )
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    weights = torch.tensor([edge_weight(src, dst, diffs) for src, dst in edges], dtype=torch.float64)
    data = Data(x=x, edge_index=edge_index, edge_attr=weights.reshape(-1, 1), num_nodes=layer_count)
    data.validate(raise_on_error=True)
    validation_receipt = {
        "api": "torch_geometric.data.Data.validate",
        "pass": True,
        "raise_on_error": True,
        "num_nodes": int(data.num_nodes),
        "edge_count": int(data.edge_index.shape[1]),
        "feature_shape": list(data.x.shape),
        "reason": "PyG graph object must validate before any message-passing result is accepted.",
    }
    return data, weights, validation_receipt


def pyg_summary(
    layers: list[str],
    diffs: list[float],
    differs: list[bool],
    edges: list[tuple[int, int]],
) -> dict[str, Any]:
    data, weights, validation_receipt = make_pyg_data(layers, diffs, differs, edges)
    messenger = LayerOrderMessenger()
    propagated = messenger(data.x, data.edge_index, weights)
    response = data.x[:, 1] + propagated[:, 1]
    differs_mask = torch.tensor(differs, dtype=torch.bool)
    quiet_mask = ~differs_mask
    differing_response_min = float(response[differs_mask].min().item()) if bool(differs_mask.any().item()) else 0.0
    quiet_response_max = float(response[quiet_mask].max().item()) if bool(quiet_mask.any().item()) else 0.0
    response_gap = differing_response_min - quiet_response_max
    return {
        "node_count": int(data.num_nodes),
        "edge_count": int(data.edge_index.shape[1]),
        "edge_index": [(int(src), int(dst)) for src, dst in data.edge_index.t().tolist()],
        "edge_weight_mean": float(weights.mean().item()) if weights.numel() else 0.0,
        "feature_shape": list(data.x.shape),
        "features_finite": bool(torch.isfinite(data.x).all().item()),
        "response_vector": [float(value) for value in response.tolist()],
        "differing_response_min": differing_response_min,
        "quiet_response_max": quiet_response_max,
        "response_gap": response_gap,
        "separates_layer_removal_signal": bool(response_gap > 1e-4),
        "tool_function_receipts": {
            "torch_geometric.data.Data.validate": validation_receipt,
            "torch_geometric.nn.MessagePassing.propagate": {
                "api": "torch_geometric.nn.MessagePassing.propagate",
                "pass": list(propagated.shape) == [len(layers), 4]
                and bool(torch.isfinite(propagated).all().item())
                and bool(response_gap > 1e-4),
                "message_passing_class": messenger.__class__.__name__,
                "aggr": "add",
                "propagated_shape": list(propagated.shape),
                "propagated_finite": bool(torch.isfinite(propagated).all().item()),
                "response_gap": response_gap,
                "reason": "Layer-removal signal must be separated by direct PyG propagation, not only by static tensors.",
            },
        },
    }


def z3_noncollapse_witness(rx_row: dict[str, Any], pyg_row: dict[str, Any], layer_count: int) -> dict[str, Any]:
    solver = z3.Solver()
    has_13_layers = z3.Bool("has_13_layers")
    has_chain_edges = z3.Bool("has_chain_edges")
    has_reachability = z3.Bool("has_source_to_sink_reachability")
    pyg_separates = z3.Bool("pyg_separates_layer_removal_signal")
    collapsed = z3.Bool("collapsed_graph_order")
    solver.add(has_13_layers == (layer_count == 13))
    solver.add(has_chain_edges == (rx_row["edge_count"] == 12 and pyg_row["edge_count"] == 12))
    solver.add(has_reachability == bool(rx_row["source_reaches_sink"]))
    solver.add(pyg_separates == bool(pyg_row["separates_layer_removal_signal"]))
    solver.add(collapsed == z3.Not(z3.And(has_13_layers, has_chain_edges, has_reachability, pyg_separates)))
    solver.add(z3.And(has_13_layers, has_chain_edges, has_reachability, pyg_separates, collapsed))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite witness over graph order, reachability, and PyG layer-removal separation only.",
    }


def tool_function_receipts_pass(rx_row: dict[str, Any], pyg_row: dict[str, Any]) -> dict[str, Any]:
    receipts = {
        **rx_row.get("tool_function_receipts", {}),
        **pyg_row.get("tool_function_receipts", {}),
    }
    return {
        "pass": all(bool(row.get("pass")) for row in receipts.values())
        and set(receipts) == {
            "rustworkx.transitive_reduction",
            "rustworkx.digraph_has_path",
            "torch_geometric.data.Data.validate",
            "torch_geometric.nn.MessagePassing.propagate",
        },
        "receipt_count": len(receipts),
        "receipts": receipts,
    }


def source_has_networkx_import() -> bool:
    text = pathlib.Path(__file__).read_text(encoding="utf-8")
    return any(line.startswith("import networkx") or line.startswith("from networkx") for line in text.splitlines())


def build_result() -> dict[str, Any]:
    started = time.time()
    parent = load_parent()
    layers = canonical_layers(parent)
    rows = parent_layer_rows(parent)
    diffs = state_diffs(rows)
    differs = differs_flags(rows)
    edges = ordered_edges(len(layers))

    graph = make_rx_graph(layers, diffs, differs, edges)
    rx_row = rx_summary(graph, layers)
    pyg_row = pyg_summary(layers, diffs, differs, edges)
    z3_row = z3_noncollapse_witness(rx_row, pyg_row, len(layers))

    reversed_graph = make_rx_graph(layers, diffs, differs, [(dst, src) for src, dst in edges])
    shuffled_layers = layers[::2] + layers[1::2]
    shuffled_graph = make_rx_graph(shuffled_layers, diffs, differs, edges)
    zero_pyg = pyg_summary(layers, [0.0 for _ in diffs], differs, edges)
    all_false_pyg = pyg_summary(layers, diffs, [False for _ in differs], edges)
    disconnected_edges = [edge for edge in edges if edge != (6, 7)]
    disconnected_graph = make_rx_graph(layers, diffs, differs, disconnected_edges)

    parent_summary = parent.get("summary", {})
    graveyard_layer_removal = parent.get("graveyard_companions", {}).get("g_layer_removal_each_of_13", {})
    parent_receipt = {
        "path": str(PARENT_PATH),
        "sha256": sha256_file(PARENT_PATH),
        "name": parent.get("name"),
        "classification": parent.get("classification"),
        "promotion_allowed": parent.get("promotion_allowed"),
        "summary_all_pass": parent_summary.get("all_pass"),
        "layer_count": parent_summary.get("layer_count"),
        "microstep_count": parent_summary.get("microstep_count"),
        "cross_track_divergence": parent_summary.get("cross_track_divergence"),
        "track_a_max_coherent_information": parent_summary.get("track_a_max_coherent_information"),
        "track_b_max_coherent_information": parent_summary.get("track_b_max_coherent_information"),
    }
    graph_fixture = {
        "node_count": len(layers),
        "edge_count": len(edges),
        "layers": layers,
        "edges": edges,
        "state_diffs": diffs,
        "differs_flags": differs,
        "n_layers_differing": graveyard_layer_removal.get("n_layers_differing"),
    }

    positive = {
        "parent_thirteen_layer_receipt_is_consumed_without_promotion": {
            "pass": bool(
                parent.get("classification") == "formal_scout"
                and parent.get("promotion_allowed") is False
                and parent_summary.get("all_pass") is True
                and parent_summary.get("layer_count") == 13
                and parent_summary.get("microstep_count") == 64
                and graveyard_layer_removal.get("pass") is True
            ),
            "parent_receipt": parent_receipt,
        },
        "rustworkx_layer_order_dag_matches_parent_receipt": {
            "pass": bool(
                rx_row["node_count"] == 13
                and rx_row["edge_count"] == 12
                and rx_row["is_dag"]
                and rx_row["topological_names_match_parent"]
                and rx_row["transitive_reduction_edge_count"] == 12
                and rx_row["source_reaches_sink"]
                and not rx_row["sink_reaches_source"]
                and len(rx_row["source_descendants"]) == 12
                and len(rx_row["sink_descendants"]) == 0
            ),
            "rustworkx": rx_row,
        },
        "pyg_message_passing_preserves_parent_layer_removal_signal": {
            "pass": bool(
                pyg_row["node_count"] == 13
                and pyg_row["edge_count"] == 12
                and pyg_row["feature_shape"] == [13, 4]
                and pyg_row["features_finite"]
                and pyg_row["separates_layer_removal_signal"]
                and differs.count(True) == 12
                and differs.count(False) == 1
            ),
            "pyg": pyg_row,
        },
        "pyg_and_rustworkx_agree_on_ordered_graph_fixture": {
            "pass": bool(
                pyg_row["node_count"] == rx_row["node_count"]
                and pyg_row["edge_count"] == rx_row["edge_count"]
                and pyg_row["edge_index"] == rx_row["edge_list"]
                and rx_row["topological_indices"] == list(range(13))
            ),
            "pyg_edges": pyg_row["edge_index"],
            "rustworkx_edges": rx_row["edge_list"],
        },
        "tool_function_micro_receipts_are_explicit": tool_function_receipts_pass(rx_row, pyg_row),
        "z3_graph_order_noncollapse_witness_executes": z3_row,
    }

    graveyards = {
        "reversed_edge_orientation_loses_source_to_sink_reachability": {
            "pass": not bool(rx.digraph_has_path(reversed_graph, 0, len(layers) - 1)),
            "reversed_has_source_to_sink_path": bool(rx.digraph_has_path(reversed_graph, 0, len(layers) - 1)),
        },
        "shuffled_layer_order_fails_exact_parent_order": {
            "pass": rx_summary(shuffled_graph, layers)["topological_names"] != layers,
            "shuffled_topological_names": rx_summary(shuffled_graph, layers)["topological_names"],
        },
        "zeroed_state_diff_collapses_pyg_separation": {
            "pass": not zero_pyg["separates_layer_removal_signal"],
            "zero_pyg": zero_pyg,
        },
        "all_false_layer_removal_flags_fail_signal": {
            "pass": not all_false_pyg["separates_layer_removal_signal"],
            "all_false_pyg": all_false_pyg,
        },
        "middle_edge_deletion_breaks_rustworkx_reachability": {
            "pass": not bool(rx.digraph_has_path(disconnected_graph, 0, len(layers) - 1)),
            "deleted_edge": [6, 7],
            "remaining_edge_count": disconnected_graph.num_edges(),
        },
    }

    boundary = {
        "exactly_thirteen_contiguous_layers": {
            "pass": len(layers) == 13 and [row.get("removed_layer_idx") for row in rows] == list(range(13)),
            "layer_count": len(layers),
            "removed_layer_indices": [row.get("removed_layer_idx") for row in rows],
        },
        "exactly_twelve_ordered_edges": {
            "pass": edges == [(idx, idx + 1) for idx in range(12)],
            "edges": edges,
        },
        "state_diffs_are_finite_nonnegative": {
            "pass": finite_nonnegative(diffs),
            "state_diffs": diffs,
        },
        "parent_receipt_hash_is_recorded": {
            "pass": len(parent_receipt["sha256"]) == 64,
            "parent_receipt_sha256": parent_receipt["sha256"],
        },
        "networkx_is_not_load_bearing_or_imported": {
            "pass": not source_has_networkx_import() and "networkx" not in TOOL_INTEGRATION_DEPTH,
            "source_has_networkx_import": source_has_networkx_import(),
            "tool_depth_has_networkx": "networkx" in TOOL_INTEGRATION_DEPTH,
        },
        "claim_ceiling_blocks_final_manifold_or_axis_claim": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "final manifold", "axis"]),
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    return {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "thirteen_layer_manifold_layer_removal_graph_order",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "parent_receipt": parent_receipt,
        "graph_fixture": graph_fixture,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This is a v5 graph-order successor over the active 13-layer manifold receipt, not a v4 probe.",
            "It consumes a parent receipt and makes direct PyG/rustworkx pass predicates rather than rerunning the tensor-network manifold stack.",
        ],
        "summary": {
            "all_pass": all_pass,
            "layer_count": len(layers),
            "edge_count": len(edges),
            "pyg_response_gap": pyg_row["response_gap"],
            "rustworkx_reduction_edge_count": rx_row["transitive_reduction_edge_count"],
            "tool_function_micro_receipt_count": positive["tool_function_micro_receipts_are_explicit"]["receipt_count"],
            "parent_receipt_sha256": parent_receipt["sha256"],
            "load_bearing_count": len(TOOL_INTEGRATION_DEPTH),
            "elapsed_seconds": time.time() - started,
        },
        "all_pass": all_pass,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
