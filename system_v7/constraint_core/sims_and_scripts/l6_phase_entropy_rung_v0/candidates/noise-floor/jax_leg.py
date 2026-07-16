#!/usr/bin/env python3
"""Independently evaluate the shared basis with JAX float64."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import jaxlib


SCRIPT_DIR = Path(__file__).resolve().parent
SURFACE_PATH = SCRIPT_DIR.parent.parent / "surface" / "surface_v1.json"
VARIANTS_PATH = SCRIPT_DIR / "variants_v1.json"
OUTPUT_PATH = SCRIPT_DIR / "jax_leg_values_v1.json"


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


def phi(row: dict[str, Any]) -> jax.Array:
    dtype = jnp.float64
    a = jnp.asarray(row["a"], dtype=dtype)
    shell_radius = jnp.asarray(row["shell_radius"], dtype=dtype)
    purity = jnp.asarray(row["purity"], dtype=dtype)
    negativity = jnp.asarray(row["negativity"], dtype=dtype)
    entropy_bits = jnp.asarray(row["entropy_bits"], dtype=dtype)
    orientation = jnp.asarray(float(row["orientation"]), dtype=dtype)
    chern_signed = jnp.asarray(row["chern_signed"], dtype=dtype)
    pi = jnp.asarray(jnp.pi, dtype=dtype)
    features = jnp.asarray(
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
            jnp.sin(pi * a),
            jnp.cos(pi * shell_radius),
            orientation * entropy_bits,
            jnp.asarray(1.0, dtype=dtype),
        ],
        dtype=dtype,
    )
    if features.dtype != jnp.float64:
        raise RuntimeError(f"feature dtype is {features.dtype}")
    return features


def main() -> int:
    if not jax.config.x64_enabled:
        raise RuntimeError("JAX x64 is disabled")
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
        weights = jnp.asarray(variant["weights"], dtype=jnp.float64)
        if weights.dtype != jnp.float64:
            raise RuntimeError(f"weight dtype is {weights.dtype}")
        values[variant["variant_id"]] = [
            float(jnp.dot(weights, row_features)) for row_features in features
        ]

    output = {
        "engine": "jax",
        "engine_versions": {"jax": jax.__version__, "jaxlib": jaxlib.__version__},
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
