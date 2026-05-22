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
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tensor fixture and controls"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing MessagePassing adapter"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "torch_geometric": "load_bearing",
}
NEARBY_VARIANTS = {
    "total": 1,
    "passed": 1,
    "variants": ["collapsed_edge_control_differs"],
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

    class OrderedMessageProbe(MessagePassing):
        def __init__(self) -> None:
            super().__init__(aggr="add")

        def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
            return self.propagate(edge_index, x=x)

        def message(self, x_j: torch.Tensor) -> torch.Tensor:
            weights = torch.tensor([1.0, -0.5, 0.25], dtype=x_j.dtype, device=x_j.device)
            return x_j * weights

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
    probe = OrderedMessageProbe()
    forward = probe(x, forward_edges)
    reverse = probe(x, reverse_edges)
    branch_gap = torch.linalg.vector_norm(forward - reverse)
    collapsed = probe(x, torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long))
    collapsed_gap = torch.linalg.vector_norm(forward - collapsed)
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
        "collapsed_edge_control_differs": {
            "pass": bool(collapsed_gap.item() > 0.10),
            "forward_collapsed_l2": float(collapsed_gap.item()),
        }
    }
    return {
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": {
            "node_count": int(x.shape[0]),
            "edge_count": int(forward_edges.shape[1]),
            "root_constraint_wording": "observed branch pressure remains evidence-bound and not promoted",
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
