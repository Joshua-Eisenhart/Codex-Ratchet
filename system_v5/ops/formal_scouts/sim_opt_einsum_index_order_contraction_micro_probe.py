#!/usr/bin/env python3
"""opt_einsum finite index-order contraction micro-probe."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import opt_einsum as oe


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "opt_einsum_index_order_contraction_micro_probe_results.json"

NAME = "opt_einsum_index_order_contraction_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "opt_einsum_tool_admission_index_order_micro_probe"
CLAIM_CEILING = (
    "Formal scout only: opt_einsum is probed as a finite index-order contraction "
    "surface. This is tool-function evidence only and does not promote a manifold, "
    "basin, bridge, engine, axis, or target-system claim."
)
TOOL_MANIFEST = {
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite einsum contraction and contraction-path surface",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, path handling, and timestamps",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "opt_einsum": "load_bearing",
    "python_stdlib": "supportive",
}
NEARBY_VARIANTS = {
    "total": 1,
    "passed": 1,
    "variants": ["different_index_label_order_changes_readout"],
}
WHY_NOT_V4_PROBES = [
    "This is a v5 formal scout for one opt_einsum tool-function surface.",
    "It records a bounded finite contraction receipt only; it is not a v4 canonical sim, manifold proof, or basin proof.",
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def manual_contract(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    return [
        [
            sum(a[row][inner] * b[inner][col] for inner in range(len(b)))
            for col in range(len(b[0]))
        ]
        for row in range(len(a))
    ]


def run_probe() -> dict[str, Any]:
    left = [[1, 2], [3, 5]]
    right = [[2, 7], [11, 13]]

    contracted = oe.contract("ab,bc->ac", left, right)
    expected = manual_contract(left, right)
    alternate_index_order = oe.contract("ab,cb->ac", left, right)
    path, path_info = oe.contract_path("ab,bc->ac", left, right, optimize="optimal")
    index_order_gap = sum(
        abs(int(contracted[row][col]) - int(alternate_index_order[row][col]))
        for row in range(2)
        for col in range(2)
    )

    positive = {
        "opt_einsum_contract_matches_manual_finite_product": {
            "pass": contracted.tolist() == expected,
            "contracted": contracted,
            "expected": expected,
        },
        "contract_path_is_bounded_and_nonempty": {
            "pass": bool(path) and getattr(path_info, "opt_cost", 0) > 0,
            "path": path,
            "optimized_cost": int(getattr(path_info, "opt_cost", 0)),
            "largest_intermediate": int(getattr(path_info, "largest_intermediate", 0)),
        },
    }
    graveyard_companions = {
        "different_index_label_order_changes_readout": {
            "pass": index_order_gap > 0,
            "index_order_gap_l1": index_order_gap,
            "alternate_index_order": alternate_index_order,
        }
    }
    boundary = {
        "finite_fixture_only": {
            "pass": True,
            "shape": [2, 2],
            "claim": "finite two-by-two contraction fixture only",
        },
        "tool_admission_only": {
            "pass": True,
            "claim": "receipt admits an opt_einsum tool-function surface, not a downstream manifold claim",
        },
    }
    return {
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "blockers": [],
        "all_pass": all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values()),
    }


def blocked_receipt(started: float, blocker: str, detail: str) -> dict[str, Any]:
    manifest = {
        **TOOL_MANIFEST,
        "opt_einsum": {"tried": True, "used": False, "reason": blocker},
    }
    return {
        "name": NAME,
        "schema": "formal_scout_result_v1",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": manifest,
        "tool_manifest": manifest,
        "TOOL_INTEGRATION_DEPTH": {"opt_einsum": None, "python_stdlib": "supportive"},
        "tool_integration_depth": {"opt_einsum": None, "python_stdlib": "supportive"},
        "nearby_variants": {"total": 0, "passed": 0, "variants": []},
        "why_not_v4_probes": WHY_NOT_V4_PROBES,
        "positive": {},
        "graveyard_companions": {},
        "boundary": {"blocked_before_tool_execution": {"pass": False, "detail": detail}},
        "blockers": [{"kind": blocker, "detail": detail}],
        "elapsed_seconds": time.time() - started,
        "all_pass": False,
    }


def main() -> int:
    started = time.time()
    try:
        body = run_probe()
        result = {
            "name": NAME,
            "schema": "formal_scout_result_v1",
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "classification": CLASSIFICATION,
            "sim_execution_kind": SIM_EXECUTION_KIND,
            "promotion_allowed": PROMOTION_ALLOWED,
            "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
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
        result = blocked_receipt(started, "missing_import", f"opt_einsum import failed: {exc}")
    except Exception as exc:
        result = blocked_receipt(
            started,
            "runtime_error",
            f"opt_einsum micro probe failed: {type(exc).__name__}: {exc}",
        )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
