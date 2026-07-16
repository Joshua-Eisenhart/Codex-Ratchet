#!/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""Compute marginal von Neumann entropy candidate values with JAX."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


SCHEMA_VERSION = "l6_phase_entropy_candidate_values/1.0"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
EXPECTED_ROW_COUNT = 18
EIGENVALUE_CUTOFF = 1.0e-300

VARIANT_GRID = (
    (
        "mvn_bits_from_radius",
        "from_radius",
        "bits",
        "S(rho) from eigvalsh(diag((1+shell_radius)/2, (1-shell_radius)/2))",
    ),
    (
        "mvn_nats_from_radius",
        "from_radius",
        "nats",
        "S(rho) from eigvalsh(diag((1+shell_radius)/2, (1-shell_radius)/2))",
    ),
    (
        "mvn_bits_from_purity",
        "from_purity",
        "bits",
        "S(rho) from eigvalsh(diag(p,1-p)), p=(1+sqrt(max(0,2*purity-1)))/2",
    ),
    (
        "mvn_nats_from_purity",
        "from_purity",
        "nats",
        "S(rho) from eigvalsh(diag(p,1-p)), p=(1+sqrt(max(0,2*purity-1)))/2",
    ),
    (
        "mvn_bits_from_negativity",
        "from_negativity",
        "bits",
        "S(rho) from eigvalsh(diag(p,1-p)), p=(1+sqrt(max(0,1-4*negativity^2)))/2",
    ),
    (
        "mvn_nats_from_negativity",
        "from_negativity",
        "nats",
        "S(rho) from eigvalsh(diag(p,1-p)), p=(1+sqrt(max(0,1-4*negativity^2)))/2",
    ),
    (
        "mvn_bits_from_state",
        "from_state",
        "bits",
        "S(Tr_B |psi><psi|) from eigvalsh, psi=cos(a)|00>+orientation*sin(a)|11>",
    ),
    (
        "mvn_nats_from_state",
        "from_state",
        "nats",
        "S(Tr_B |psi><psi|) from eigvalsh, psi=cos(a)|00>+orientation*sin(a)|11>",
    ),
)


def _load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    rows = payload["rows"]
    if len(rows) != EXPECTED_ROW_COUNT:
        raise ValueError(f"expected {EXPECTED_ROW_COUNT} rows, received {len(rows)}")
    ordered = sorted(rows, key=lambda row: int(row["row_id"]))
    if [int(row["row_id"]) for row in ordered] != list(range(EXPECTED_ROW_COUNT)):
        raise ValueError("row_id values must be exactly 0 through 17")
    return ordered


def _diagonal_marginal(probability: jax.Array) -> jax.Array:
    """Construct a batch of explicit 2x2 diagonal Hermitian matrices."""

    zero = jnp.zeros_like(probability, dtype=jnp.float64)
    return jnp.stack(
        (
            jnp.stack((probability, zero), axis=-1),
            jnp.stack((zero, jnp.asarray(1.0, dtype=jnp.float64) - probability), axis=-1),
        ),
        axis=-2,
    )


def _state_marginal(
    angles: jax.Array, orientations: jax.Array
) -> jax.Array:
    """Construct rho_AB and trace subsystem B for every input state."""

    batch_size = angles.shape[0]
    psi = jnp.zeros((batch_size, 4), dtype=jnp.complex128)
    psi = psi.at[:, 0].set(jnp.cos(angles).astype(jnp.complex128))
    psi = psi.at[:, 3].set(
        (orientations * jnp.sin(angles)).astype(jnp.complex128)
    )
    rho_ab = psi[:, :, None] * jnp.conjugate(psi[:, None, :])
    rho_tensor = jnp.reshape(rho_ab, (batch_size, 2, 2, 2, 2))
    return jnp.trace(rho_tensor, axis1=2, axis2=4)


def _entropy_from_eigenvalues(eigenvalues: jax.Array, log_base: str) -> jax.Array:
    clipped = jnp.maximum(eigenvalues, jnp.asarray(0.0, dtype=jnp.float64))
    cutoff = jnp.asarray(EIGENVALUE_CUTOFF, dtype=jnp.float64)
    included = clipped > cutoff
    safe_values = jnp.where(included, clipped, jnp.asarray(1.0, dtype=jnp.float64))
    entropy_nats = -jnp.sum(
        jnp.where(
            included,
            clipped * jnp.log(safe_values),
            jnp.asarray(0.0, dtype=jnp.float64),
        ),
        axis=-1,
    )
    if log_base == "bits":
        return entropy_nats / jnp.log(jnp.asarray(2.0, dtype=jnp.float64))
    return entropy_nats


def _evaluate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    shell_radius = jnp.asarray(
        [row["shell_radius"] for row in rows], dtype=jnp.float64
    )
    purity = jnp.asarray([row["purity"] for row in rows], dtype=jnp.float64)
    negativity = jnp.asarray(
        [row["negativity"] for row in rows], dtype=jnp.float64
    )
    angles = jnp.asarray([row["a"] for row in rows], dtype=jnp.float64)
    orientations = jnp.asarray(
        [row["orientation"] for row in rows], dtype=jnp.float64
    )

    for array in (shell_radius, purity, negativity, angles, orientations):
        assert array.dtype == jnp.dtype(jnp.float64)

    one = jnp.asarray(1.0, dtype=jnp.float64)
    two = jnp.asarray(2.0, dtype=jnp.float64)
    four = jnp.asarray(4.0, dtype=jnp.float64)
    zero = jnp.asarray(0.0, dtype=jnp.float64)

    radius_probability = (one + shell_radius) / two
    purity_probability = (
        one + jnp.sqrt(jnp.maximum(zero, two * purity - one))
    ) / two
    negativity_probability = (
        one + jnp.sqrt(jnp.maximum(zero, one - four * negativity * negativity))
    ) / two

    eigenvalues_by_route = {
        "from_radius": jnp.linalg.eigvalsh(_diagonal_marginal(radius_probability)),
        "from_purity": jnp.linalg.eigvalsh(_diagonal_marginal(purity_probability)),
        "from_negativity": jnp.linalg.eigvalsh(
            _diagonal_marginal(negativity_probability)
        ),
        "from_state": jnp.linalg.eigvalsh(_state_marginal(angles, orientations)),
    }

    variants: list[dict[str, Any]] = []
    for variant_id, route, log_base, formula in VARIANT_GRID:
        values = _entropy_from_eigenvalues(eigenvalues_by_route[route], log_base)
        assert values.dtype == jnp.dtype(jnp.float64)
        variants.append(
            {
                "variant_id": variant_id,
                "parameters": {
                    "reconstruction_route": route,
                    "log_base": log_base,
                    "formula": formula,
                },
                "values": [float(value) for value in jax.device_get(values)],
            }
        )
    return variants


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: jax_leg.py <rows_v1.json> <out.json>")

    assert jax.config.x64_enabled
    dtype_probe = jnp.asarray(0.0, dtype=jnp.float64)
    assert dtype_probe.dtype == jnp.dtype(jnp.float64)

    input_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()
    rows = _load_rows(input_path)
    result = {
        "schema_version": SCHEMA_VERSION,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "seed": 0,
        "substrate": "jax",
        "engine": {
            "version": jax.__version__,
            "x64": True,
            "dtype": "float64",
        },
        "variants": _evaluate(rows),
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=False, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
