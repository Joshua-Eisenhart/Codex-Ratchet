#!/usr/bin/env python3
"""Independently evaluate the shared basis with Torch float64."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import torch


SCRIPT_DIR = Path(__file__).resolve().parent
SURFACE_PATH = SCRIPT_DIR.parent.parent / "surface" / "surface_v1.json"
VARIANTS_PATH = SCRIPT_DIR / "variants_v1.json"
OUTPUT_PATH = SCRIPT_DIR / "torch_leg_values_v1.json"
DTYPE = torch.float64


def json_bytes(data: Any) -> bytes:
    return (
        json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def create_or_require_identical(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            print(f"BYTE_IDENTITY_FINDING={path.name}", file=sys.stderr)
            raise RuntimeError(f"existing content differs for {path}")
        return
    path.write_bytes(content)


def scalar(value: Any) -> torch.Tensor:
    result = torch.tensor(value, dtype=DTYPE)
    if result.dtype != DTYPE:
        raise RuntimeError(f"scalar dtype is {result.dtype}")
    return result


def phi(row: dict[str, Any]) -> torch.Tensor:
    a = scalar(row["a"])
    shell_radius = scalar(row["shell_radius"])
    purity = scalar(row["purity"])
    negativity = scalar(row["negativity"])
    entropy_bits = scalar(row["entropy_bits"])
    orientation = scalar(float(row["orientation"]))
    chern_signed = scalar(row["chern_signed"])
    pi = torch.acos(scalar(-1.0))
    features = torch.stack(
        [
            a,
            shell_radius,
            purity,
            negativity,
            entropy_bits,
            orientation,
            chern_signed,
            a * entropy_bits,
            shell_radius * purity,
            negativity * entropy_bits,
            a * a,
            entropy_bits * entropy_bits,
            torch.sin(pi * a),
            torch.cos(pi * shell_radius),
            orientation * entropy_bits,
            scalar(1.0),
        ]
    )
    if features.dtype != DTYPE:
        raise RuntimeError(f"feature dtype is {features.dtype}")
    return features


def main() -> int:
    torch.set_default_dtype(DTYPE)
    surface = json.loads(SURFACE_PATH.read_bytes())
    variants_document = json.loads(VARIANTS_PATH.read_bytes())
    rows = sorted(
        surface["row_blocks"]["fixture_observations"],
        key=lambda row: int(row["row_id"]),
    )
    row_order = [int(row["row_id"]) for row in rows]
    if row_order != list(range(18)):
        raise RuntimeError(f"unexpected row order: {row_order}")
    features = [phi(row) for row in rows]

    values: dict[str, list[float]] = {}
    for variant in variants_document["variants"]:
        weights = torch.tensor(variant["weights"], dtype=DTYPE)
        if weights.dtype != DTYPE:
            raise RuntimeError(f"weight dtype is {weights.dtype}")
        values[variant["variant_id"]] = [
            float(torch.dot(weights, row_features).item()) for row_features in features
        ]

    output = {
        "engine": "torch",
        "engine_versions": {"torch": torch.__version__},
        "reads_peer_result": False,
        "row_order": row_order,
        "values": values,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
    }
    create_or_require_identical(OUTPUT_PATH, json_bytes(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
