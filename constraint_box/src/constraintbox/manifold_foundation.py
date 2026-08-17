"""Typed, finite-first validation for the time-first manifold seed.

This module is deliberately a controller-side intake check.  It validates a
small finite object and its declared maps; it does not decide whether the
object is a physical manifold, whether a direction is literally chiral, or
whether the proposed layer order is canonical.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .intake import canonical_json, parse_json_object


FOUNDATION_SCHEMA = "constraintbox.manifold-foundation-seed.v1"
RECEIPT_SCHEMA = "constraintbox.manifold-foundation-validation.v1"


class ManifoldFoundationError(ValueError):
    """Raised when a foundation seed is not a typed finite object."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _positive_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ManifoldFoundationError(f"{path} must be a positive integer")
    return value


def _nonempty_text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifoldFoundationError(f"{path} must be non-empty text")
    return value


def _exact_keys(value: Any, expected: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifoldFoundationError(f"{path} must be an object")
    actual = set(value)
    if actual != expected:
        raise ManifoldFoundationError(
            f"{path} fields differ: missing={sorted(expected - actual)!r}, "
            f"extra={sorted(actual - expected)!r}"
        )
    return value


def _finite_capacity(count: int, path: str) -> float:
    if count <= 0:
        raise ManifoldFoundationError(f"{path} must be positive")
    value = math.log2(count)
    if not math.isfinite(value):
        raise ManifoldFoundationError(f"{path} is not finite")
    return value


def validate_foundation(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and measure one time-first finite foundation seed.

    The first accepted constraint is finitude.  ``zero_object`` is a typed
    boundary/root label, not the scalar zero of an algebra.  The two order
    words are measured on a finite witness map; non-associativity remains a
    candidate layer until a bracketed witness is supplied.
    """

    root = _exact_keys(
        payload,
        {
            "schema",
            "foundation_id",
            "carrier",
            "time",
            "dual_engines",
            "layers",
            "claim_ceiling",
            "promotion_allowed",
        },
        "$",
    )
    if root["schema"] != FOUNDATION_SCHEMA:
        raise ManifoldFoundationError("unsupported foundation schema")
    foundation_id = _nonempty_text(root["foundation_id"], "$.foundation_id")
    if root["promotion_allowed"] is not False:
        raise ManifoldFoundationError("$.promotion_allowed must be false")
    claim_ceiling = _nonempty_text(root["claim_ceiling"], "$.claim_ceiling")

    carrier = _exact_keys(
        root["carrier"],
        {"support_ids", "zero_object", "capacity_name"},
        "$.carrier",
    )
    support_ids = carrier["support_ids"]
    if (
        not isinstance(support_ids, list)
        or not support_ids
        or any(not isinstance(value, str) or not value for value in support_ids)
        or len(set(support_ids)) != len(support_ids)
    ):
        raise ManifoldFoundationError("$.carrier.support_ids must be unique non-empty text")
    zero = _exact_keys(
        carrier["zero_object"],
        {"label", "role", "scalar_zero"},
        "$.carrier.zero_object",
    )
    _nonempty_text(zero["label"], "$.carrier.zero_object.label")
    _nonempty_text(zero["role"], "$.carrier.zero_object.role")
    if zero["scalar_zero"] is not False:
        raise ManifoldFoundationError(
            "$.carrier.zero_object.scalar_zero must be false until an algebra is declared"
        )
    _nonempty_text(carrier["capacity_name"], "$.carrier.capacity_name")

    time = _exact_keys(
        root["time"],
        {"ticks", "support_counts", "capacity_bits", "delta_capacity_bits"},
        "$.time",
    )
    ticks = time["ticks"]
    counts = time["support_counts"]
    if not isinstance(ticks, list) or not ticks or ticks != list(range(len(ticks))):
        raise ManifoldFoundationError("$.time.ticks must be consecutive from zero")
    if not isinstance(counts, list) or len(counts) != len(ticks):
        raise ManifoldFoundationError("$.time.support_counts must align with ticks")
    counts = [_positive_int(value, f"$.time.support_counts[{index}]") for index, value in enumerate(counts)]
    if counts[0] != len(support_ids):
        raise ManifoldFoundationError("initial support count must equal carrier support size")
    expected_capacity = [_finite_capacity(value, f"$.time.support_counts[{index}]") for index, value in enumerate(counts)]
    observed_capacity = time["capacity_bits"]
    if not isinstance(observed_capacity, list) or len(observed_capacity) != len(counts):
        raise ManifoldFoundationError("$.time.capacity_bits must align with support_counts")
    capacity_error = max(
        abs(float(observed) - expected)
        for observed, expected in zip(observed_capacity, expected_capacity, strict=True)
    )
    expected_delta = [
        expected_capacity[index + 1] - expected_capacity[index]
        for index in range(len(expected_capacity) - 1)
    ]
    delta = time["delta_capacity_bits"]
    if not isinstance(delta, list) or len(delta) != len(expected_delta):
        raise ManifoldFoundationError("$.time.delta_capacity_bits must be one shorter than capacity_bits")
    delta_error = max(
        [
            abs(float(observed) - expected)
            for observed, expected in zip(delta, expected_delta, strict=True)
        ]
        or [0.0]
    )
    gradient_positive = all(value > 0 for value in expected_delta)

    engines = _exact_keys(
        root["dual_engines"],
        {"left_order", "right_order", "witness_domain", "left_output", "right_output"},
        "$.dual_engines",
    )
    left_order = engines["left_order"]
    right_order = engines["right_order"]
    if left_order != ["open", "bind"] or right_order != ["bind", "open"]:
        raise ManifoldFoundationError(
            "dual engines must expose the typed candidate orders open->bind and bind->open"
        )
    domain = _nonempty_text(engines["witness_domain"], "$.dual_engines.witness_domain")
    left_output = _nonempty_text(engines["left_output"], "$.dual_engines.left_output")
    right_output = _nonempty_text(engines["right_output"], "$.dual_engines.right_output")
    order_gap = left_output != right_output
    if not order_gap:
        raise ManifoldFoundationError("REFUSE_ORDER_GAP_COLLAPSED")
    if capacity_error > 1e-9 or delta_error > 1e-9:
        raise ManifoldFoundationError("REFUSE_CAPACITY_MISMATCH")

    layers = root["layers"]
    if not isinstance(layers, list) or not layers:
        raise ManifoldFoundationError("$.layers must be a non-empty array")
    layer_ids: list[str] = []
    layer_rows: list[dict[str, str]] = []
    for index, layer in enumerate(layers):
        item = _exact_keys(
            layer,
            {"id", "constraint", "status", "witness"},
            f"$.layers[{index}]",
        )
        layer_id = _nonempty_text(item["id"], f"$.layers[{index}].id")
        if layer_id in layer_ids:
            raise ManifoldFoundationError("layer ids must be unique")
        layer_ids.append(layer_id)
        constraint = _nonempty_text(item["constraint"], f"$.layers[{index}].constraint")
        status = _nonempty_text(item["status"], f"$.layers[{index}].status")
        _nonempty_text(item["witness"], f"$.layers[{index}].witness")
        if index == 0 and (layer_id != "C0_finitude" or status != "accepted_seed"):
            raise ManifoldFoundationError("C0_finitude must be the accepted first constraint")
        if layer_id == "C3_nonassociativity" and status not in {"candidate", "unvalidated"}:
            raise ManifoldFoundationError("non-associativity must remain candidate/unvalidated")
        layer_rows.append({"id": layer_id, "status": status, "constraint": constraint})

    static_supports = [
        {"tick": tick, "W": count, "K": capacity}
        for tick, count, capacity in zip(ticks, counts, expected_capacity, strict=True)
    ]
    return {
        "schema": RECEIPT_SCHEMA,
        "operation": "finite_time_first_seed_validation.v1",
        "foundation_id": foundation_id,
        "status": "PASS",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": claim_ceiling,
        "checks": {
            "finite_first": True,
            "support_counts": counts,
            "capacity_bits_recomputed": expected_capacity,
            "delta_capacity_bits_recomputed": expected_delta,
            "capacity_max_abs_error": capacity_error,
            "delta_capacity_max_abs_error": delta_error,
            "positive_capacity_gradient": gradient_positive,
            "dual_order_gap": order_gap,
            "witness_domain": domain,
            "layer_ids": layer_ids,
            "nonassociativity_deferred": "C3_nonassociativity" in layer_ids,
        },
        "surface": {
            "kind": "static_finite_supports",
            "not": ["attractor", "engine", "tda", "measured_distinguishability"],
            "static_supports": static_supports,
            "constraints": layer_rows,
            "engines": {
                "left_order": list(left_order),
                "right_order": list(right_order),
                "left_output": left_output,
                "right_output": right_output,
                "order_gap": order_gap,
            },
            "capacities": {
                "support": {
                    "status": "computed",
                    "W": counts,
                    "K": expected_capacity,
                    "delta_K": expected_delta,
                },
                "fibre": {
                    "status": "unearned",
                    "reason": "no projection declared on this seed",
                },
                "record": {
                    "status": "unearned",
                    "reason": "no bound observation rows on this seed",
                },
                "summed": False,
            },
        },
    }


def validate_foundation_file(path: Path) -> dict[str, Any]:
    """Read one strict JSON seed and return a source-bound validation receipt."""

    path = path.expanduser().resolve(strict=True)
    payload = parse_json_object(path.read_bytes())
    receipt = validate_foundation(payload)
    receipt["source_path"] = str(path)
    receipt["source_sha256"] = _sha256(path)
    receipt["input_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return receipt


def write_foundation_receipt(path: Path, output: Path) -> dict[str, Any]:
    receipt = validate_foundation_file(path)
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="python -m constraintbox.manifold_foundation")
    parser.add_argument("seed", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        receipt = validate_foundation_file(args.seed)
    except (OSError, ManifoldFoundationError, ValueError) as exc:
        body = {
            "schema": RECEIPT_SCHEMA,
            "operation": "finite_time_first_seed_validation.v1",
            "status": "REFUSE",
            "reason": str(exc),
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        }
        text = json.dumps(body, indent=2, sort_keys=True) + "\n"
        if args.out is not None:
            args.out.write_text(text, encoding="utf-8")
        sys.stdout.write(text)
        return 2
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
