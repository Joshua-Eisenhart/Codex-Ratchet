#!/usr/bin/env python3
"""cotengra contraction-order pressure micro-probe."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "cotengra_contraction_order_pressure_micro_probe_results.json"

NAME = "cotengra_contraction_order_pressure_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: cotengra is probed as a contraction-order pressure surface. "
    "Optimizer cost differences remain tool evidence and are not promoted."
)
TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing dense contraction control"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction tree search"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "cotengra": "load_bearing",
}
NEARBY_VARIANTS = {
    "total": 1,
    "passed": 1,
    "variants": ["collapsed_boundary_tensor_changes_readout"],
}
WHY_NOT_V4_PROBES = [
    "This is a v5 formal scout for a tiny cotengra contraction-order micro fixture.",
    "It records bounded contraction-order tool pressure only; it does not promote a v4 canonical probe, manifold, basin, or physics claim.",
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
            "cotengra": {"tried": True, "used": False, "reason": blocker},
        },
        "tool_manifest": {
            "pytorch": TOOL_MANIFEST["pytorch"],
            "cotengra": {"tried": True, "used": False, "reason": blocker},
        },
        "TOOL_INTEGRATION_DEPTH": {"pytorch": "load_bearing", "cotengra": None},
        "tool_integration_depth": {"pytorch": "load_bearing", "cotengra": None},
        "positive": {},
        "graveyard_companions": {},
        "boundary": {"tensor_count": 0, "root_constraint_wording": "blocked before cotengra tool pressure could run"},
        "nearby_variants": {"total": 0, "passed": 0, "variants": []},
        "why_not_v4_probes": WHY_NOT_V4_PROBES,
        "blockers": [{"kind": blocker, "detail": detail}],
        "elapsed_seconds": time.time() - started,
        "all_pass": False,
    }


def run_probe() -> dict[str, Any]:
    import cotengra as ctg

    inputs = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("a", "e")]
    output = ("c",)
    size_dict = {"a": 2, "b": 3, "c": 4, "d": 3, "e": 2}
    optimizer = ctg.HyperOptimizer(max_repeats=8, progbar=False, on_trial_error="raise")
    tree = optimizer.search(inputs, output, size_dict)
    contraction_cost = float(tree.contraction_cost())
    contraction_width = float(tree.contraction_width())

    a = torch.arange(1, 7, dtype=torch.float32).reshape(2, 3) / 7.0
    b = torch.arange(1, 13, dtype=torch.float32).reshape(3, 4) / 11.0
    c = torch.arange(1, 13, dtype=torch.float32).reshape(4, 3) / 13.0
    d = torch.arange(1, 7, dtype=torch.float32).reshape(3, 2) / 5.0
    e = torch.tensor([[0.3, -0.2], [0.4, 0.1]], dtype=torch.float32)
    structured = torch.einsum("ab,bc,cd,de,ae->c", a, b, c, d, e)
    collapsed = torch.einsum("ab,bc,cd,de,ae->c", a, b, c, d, torch.ones_like(e))
    output_gap = torch.linalg.vector_norm(structured - collapsed)
    naive_pair_pressure = float(2 * 3 * 4 * 3 * 2)
    positive = {
        "cotengra_tree_search_executes": {
            "pass": bool(contraction_cost > 0.0 and contraction_width > 0.0),
            "contraction_cost": contraction_cost,
            "contraction_width": contraction_width,
            "naive_pair_pressure": naive_pair_pressure,
        },
        "contraction_order_pressure_below_naive_fixture": {
            "pass": bool(contraction_cost < naive_pair_pressure),
            "contraction_cost": contraction_cost,
            "naive_pair_pressure": naive_pair_pressure,
        },
    }
    graveyard = {
        "collapsed_boundary_tensor_changes_readout": {
            "pass": bool(output_gap.item() > 0.1),
            "structured_vs_collapsed_l2": float(output_gap.item()),
        }
    }
    return {
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": {"tensor_count": len(inputs), "root_constraint_wording": "tool pressure only, not promoted"},
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
        result = blocked_receipt(started, "missing_import", f"cotengra import failed: {exc}")
    except Exception as exc:
        result = blocked_receipt(started, "runtime_error", f"cotengra micro probe failed: {type(exc).__name__}: {exc}")
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
