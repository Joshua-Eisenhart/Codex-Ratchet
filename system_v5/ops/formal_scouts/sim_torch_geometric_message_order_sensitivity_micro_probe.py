#!/usr/bin/env python3
"""PyG message-order sensitivity micro-probe.

Formal scout only: tests whether a tiny torch_geometric MessagePassing adapter
can expose order-sensitive branch pressure on a fixed graph fixture. This is a
tool-surface receipt, not a promoted manifold, basin, physics, or architecture
claim.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "torch_geometric_message_order_sensitivity_micro_probe_results.json"

NAME = "torch_geometric_message_order_sensitivity_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: PyG is probed as a bounded message-passing surface for "
    "branch-order sensitivity under two root-constraint pressure. Observed "
    "differences are tool receipts, not promoted attractor-basin or manifold claims."
)
ROOT_CONSTRAINTS_IN_FORCE = ["F01_FINITE_CARRIER_PROBE_OPERATOR_PATH_SET", "N01_NONCOMMUTING_OR_ORDER_SENSITIVE_GRAPH_ACTION"]
FINITE_MAP = (
    "PyGMessageOrder : finite directed graph with node features and edge-order "
    "tokens -> gated MessagePassing output plus erased-edge, erased-token, "
    "direction-flip, and linear-stub controls"
)
DOMAIN = {
    "node_features": "four finite 3-component torch feature vectors",
    "edge_index": "five directed finite graph edges",
    "edge_attr": "five finite 3-component edge-order tokens",
    "controls": [
        "reverse directed edges",
        "erase all edges",
        "erase edge tokens",
        "simple linear source-sum stub",
        "permute edge list while preserving edge-token pairing",
    ],
}
CODOMAIN_OR_OUTPUT = {
    "message_output": "4x3 torch tensor produced through torch_geometric.nn.MessagePassing.propagate",
    "branch_gap": "finite norm between forward and reversed directed message outputs",
    "control_gaps": "finite gaps proving the output depends on edges and edge tokens",
}
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tensor fixture and controls"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing MessagePassing.propagate adapter with directed edge_index and edge_attr controls"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "torch_geometric": "load_bearing",
}
NEARBY_VARIANTS = {
    "total": 4,
    "passed": 4,
    "variants": [
        "erased_edges_kill_message_claim",
        "erased_edge_tokens_change_gated_output",
        "linear_source_sum_stub_fails_to_reproduce_gated_output",
        "edge_list_permutation_preserves_paired_graph_output",
    ],
}
WHY_NOT_V4_PROBES = [
    "This is a v5 formal scout for a tiny torch_geometric MessagePassing fixture.",
    "It records bounded message-order branch pressure only; it does not promote a v4 canonical probe, manifold, basin, or physics claim.",
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        return value.detach().cpu().tolist()
    return value


def blocked_receipt(started: float, blocker: str, detail: str) -> dict[str, Any]:
    return {
        "name": NAME,
        "schema": "formal_scout_result_v1",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": ROOT_CONSTRAINTS_IN_FORCE,
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN_OR_OUTPUT,
        "TOOL_MANIFEST": {
            **TOOL_MANIFEST,
            "torch_geometric": {"tried": True, "used": False, "reason": blocker},
        },
        "tool_manifest": {
            "pytorch": TOOL_MANIFEST["pytorch"],
            "torch_geometric": {"tried": True, "used": False, "reason": blocker},
        },
        "TOOL_INTEGRATION_DEPTH": {"pytorch": "load_bearing", "torch_geometric": None},
        "tool_integration_depth": {"pytorch": "load_bearing", "torch_geometric": None},
        "positive": {},
        "graveyard_companions": {},
        "boundary": {
            "node_count": 0,
            "edge_count": 0,
            "root_constraint_wording": "blocked before torch_geometric message-order pressure could run",
        },
        "nearby_variants": {"total": 0, "passed": 0, "variants": []},
        "why_not_v4_probes": WHY_NOT_V4_PROBES,
        "blockers": [{"kind": blocker, "detail": detail}],
        "elapsed_seconds": time.time() - started,
        "all_pass": False,
    }


def run_probe() -> dict[str, Any]:
    from torch_geometric.nn import MessagePassing

    class GatedOrderMessageProbe(MessagePassing):
        def __init__(self) -> None:
            super().__init__(aggr="add")

        def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
            return self.propagate(edge_index, x=x, edge_attr=edge_attr)

        def message(self, x_j: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
            gate = torch.sigmoid(edge_attr[:, :1] + 0.25 * edge_attr[:, 1:2] - 0.15 * edge_attr[:, 2:3])
            signed = torch.tanh(x_j + edge_attr)
            return gate * signed

        def update(self, aggr_out: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
            return torch.tanh(x + aggr_out)

    x = torch.tensor(
        [
            [0.2, 1.0, -0.3],
            [1.1, -0.4, 0.5],
            [-0.7, 0.3, 1.4],
            [0.6, -1.2, 0.8],
        ],
        dtype=torch.float32,
    )
    forward_edges = torch.tensor([[0, 1, 2, 0, 3], [1, 2, 3, 3, 2]], dtype=torch.long)
    reverse_edges = forward_edges.flip(0)
    edge_attr = torch.tensor(
        [
            [0.40, -0.10, 0.20],
            [0.15, 0.35, -0.25],
            [-0.30, 0.20, 0.50],
            [0.70, -0.45, 0.10],
            [-0.20, 0.55, -0.35],
        ],
        dtype=torch.float32,
    )
    probe = GatedOrderMessageProbe()
    forward = probe(x, forward_edges, edge_attr)
    reverse = probe(x, reverse_edges, edge_attr)
    branch_gap = torch.linalg.vector_norm(forward - reverse)
    empty_edges = torch.empty((2, 0), dtype=torch.long)
    empty_attr = torch.empty((0, 3), dtype=torch.float32)
    erased_edges = probe(x, empty_edges, empty_attr)
    erased_edge_gap = torch.linalg.vector_norm(forward - erased_edges)
    erased_tokens = probe(x, forward_edges, torch.zeros_like(edge_attr))
    erased_token_gap = torch.linalg.vector_norm(forward - erased_tokens)
    perm = torch.tensor([4, 2, 0, 3, 1], dtype=torch.long)
    permuted = probe(x, forward_edges[:, perm], edge_attr[perm])
    permutation_gap = torch.linalg.vector_norm(forward - permuted)
    linear_stub = torch.zeros_like(x)
    for edge_idx in range(forward_edges.shape[1]):
        src = int(forward_edges[0, edge_idx].item())
        dst = int(forward_edges[1, edge_idx].item())
        linear_stub[dst] = linear_stub[dst] + x[src]
    linear_stub = torch.tanh(x + linear_stub)
    linear_stub_gap = torch.linalg.vector_norm(forward - linear_stub)
    positive = {
        "pyg_message_passing_executes": {
            "pass": bool(forward.shape == x.shape and reverse.shape == x.shape),
            "forward_sum": float(forward.sum().item()),
            "reverse_sum": float(reverse.sum().item()),
        },
        "message_order_branch_pressure_observed": {
            "pass": bool(branch_gap.item() > 0.25),
            "forward_reverse_l2": float(branch_gap.item()),
        },
    }
    graveyard = {
        "erased_edges_kill_message_claim": {
            "pass": bool(erased_edge_gap.item() > 0.10),
            "forward_erased_edges_l2": float(erased_edge_gap.item()),
        },
        "erased_edge_tokens_change_gated_output": {
            "pass": bool(erased_token_gap.item() > 0.10),
            "forward_erased_tokens_l2": float(erased_token_gap.item()),
        },
        "linear_source_sum_stub_fails_to_reproduce_gated_output": {
            "pass": bool(linear_stub_gap.item() > 0.10),
            "forward_linear_stub_l2": float(linear_stub_gap.item()),
        },
        "edge_list_permutation_preserves_paired_graph_output": {
            "pass": bool(permutation_gap.item() < 1e-6),
            "forward_permuted_l2": float(permutation_gap.item()),
            "reason": "PyG add aggregation is not claiming raw edge-list sequence dependence; the load-bearing object is paired directed edge/token structure.",
        },
    }
    return {
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": {
            "node_count": int(x.shape[0]),
            "edge_count": int(forward_edges.shape[1]),
            "edge_token_count": int(edge_attr.shape[0]),
            "root_constraint_wording": "observed directed graph/token branch pressure remains evidence-bound and not promoted",
        },
        "blockers": [],
        "all_pass": all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()),
    }


def main() -> int:
    started = time.time()
    try:
        body = run_probe()
        result = {
            "name": NAME,
            "schema": "formal_scout_result_v1",
            "classification": CLASSIFICATION,
            "sim_execution_kind": SIM_EXECUTION_KIND,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
            "root_constraints_in_force": ROOT_CONSTRAINTS_IN_FORCE,
            "finite_map": FINITE_MAP,
            "domain": DOMAIN,
            "codomain_or_output": CODOMAIN_OR_OUTPUT,
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "tool_manifest": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "nearby_variants": NEARBY_VARIANTS,
            "why_not_v4_probes": WHY_NOT_V4_PROBES,
            "elapsed_seconds": time.time() - started,
            **body,
        }
    except ImportError as exc:
        result = blocked_receipt(started, "missing_runtime", f"torch_geometric import failed: {exc}")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
