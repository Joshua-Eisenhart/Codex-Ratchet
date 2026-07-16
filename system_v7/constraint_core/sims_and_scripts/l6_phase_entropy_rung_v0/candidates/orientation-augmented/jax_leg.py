#!/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""Compute orientation-augmented candidate values with JAX float64."""

from __future__ import annotations

import json
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "rows_input_v1.json"
OUTPUT_PATH = BASE_DIR / "jax_values_v1.json"


def _binary_entropy_bits(radius: jax.Array) -> jax.Array:
    """Return H2((1 + radius) / 2), including the 0 log(0) limit."""

    probability = (jnp.asarray(1.0, dtype=jnp.float64) + radius) / jnp.asarray(
        2.0, dtype=jnp.float64
    )
    complement = jnp.asarray(1.0, dtype=jnp.float64) - probability

    def entropy_term(x: jax.Array) -> jax.Array:
        safe_x = jnp.where(x == 0.0, jnp.asarray(1.0, dtype=jnp.float64), x)
        return jnp.where(
            x == 0.0,
            jnp.asarray(0.0, dtype=jnp.float64),
            x * jnp.log2(safe_x),
        )

    return -(entropy_term(probability) + entropy_term(complement))


def _as_column(values: jax.Array) -> jax.Array:
    return jnp.reshape(values, (-1, 1))


def _evaluate_variants(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    r = jnp.asarray([row["shell_radius"] for row in rows], dtype=jnp.float64)
    neg = jnp.asarray([row["negativity"] for row in rows], dtype=jnp.float64)
    pur = jnp.asarray([row["purity"] for row in rows], dtype=jnp.float64)
    sig = jnp.asarray([row["orientation"] for row in rows], dtype=jnp.float64)
    ch = jnp.asarray([row["chern_signed"] for row in rows], dtype=jnp.float64)

    one = jnp.asarray(1.0, dtype=jnp.float64)
    h2 = _binary_entropy_bits(r)
    linear_entropy = one - pur
    renyi2 = -jnp.log2(pur)
    sqrt_product = jnp.sqrt(jnp.maximum(h2 * (one - h2), 0.0))

    registry: list[tuple[str, list[str], jax.Array]] = [
        ("OA01_tooth_r_sigma", ["radial", "orientation"], jnp.stack((r, sig), axis=1)),
        (
            "OA02_tooth_H2_sigma",
            ["entropy", "orientation"],
            jnp.stack((h2, sig), axis=1),
        ),
        (
            "OA03_tooth_neg_sigma",
            ["negativity", "orientation"],
            jnp.stack((neg, sig), axis=1),
        ),
        (
            "OA04_tooth_linent_sigma",
            ["linear_entropy", "orientation"],
            jnp.stack((linear_entropy, sig), axis=1),
        ),
        ("OA05_signed_entropy", ["signed_entropy"], _as_column(sig * h2)),
        (
            "OA06_signed_entropy_affine",
            ["signed_entropy_affine"],
            _as_column(sig * (one + h2)),
        ),
        ("OA07_signed_negativity", ["signed_negativity"], _as_column(sig * neg)),
        (
            "OA08_signed_linear_entropy",
            ["signed_linear_entropy"],
            _as_column(sig * linear_entropy),
        ),
        ("OA09_signed_renyi2", ["signed_renyi2"], _as_column(sig * renyi2)),
        (
            "OA10_signed_entropy_deficit",
            ["signed_entropy_deficit"],
            _as_column(sig * (one - h2)),
        ),
        (
            "OA11_chern_weighted_entropy",
            ["chern_weighted_entropy"],
            _as_column(ch * h2),
        ),
        (
            "OA12_chern_weighted_entropy_affine",
            ["chern_weighted_entropy_affine"],
            _as_column(ch * (one + h2)),
        ),
        (
            "OA13_radius_plus_signed_entropy_l05",
            ["radius_plus_signed_entropy"],
            _as_column(r + jnp.asarray(0.5, dtype=jnp.float64) * sig * h2),
        ),
        (
            "OA14_radius_plus_signed_entropy_l2",
            ["radius_plus_signed_entropy"],
            _as_column(r + jnp.asarray(2.0, dtype=jnp.float64) * sig * h2),
        ),
        (
            "OA15_entropy_plus_signed_radius",
            ["entropy_plus_signed_radius"],
            _as_column(h2 + sig * r),
        ),
        (
            "OA16_signed_entropy_sqrtprod",
            ["signed_entropy_sqrtprod"],
            _as_column(sig * sqrt_product),
        ),
    ]

    return {
        variant_id: {
            "channels": channels,
            "values": jax.device_get(values).tolist(),
        }
        for variant_id, channels, values in registry
    }


def main() -> None:
    with INPUT_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    rows = sorted(payload["rows"], key=lambda row: row["row_id"])
    result = {
        "substrate": "jax",
        "schema_version": "l6_phase_entropy_candidate_values/1.0",
        "variants": _evaluate_variants(rows),
    }

    with OUTPUT_PATH.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=False, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
