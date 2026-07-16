#!/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""JAX x64 value leg for declared-reference quantum relative entropy."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


def _load(path: Path) -> tuple[dict[str, object], str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _row_density(row: dict[str, object]) -> jax.Array:
    angle = jnp.asarray(row["a"], dtype=jnp.float64)
    orientation = jnp.asarray(row["orientation"], dtype=jnp.float64)
    psi = jnp.asarray(
        [jnp.cos(angle), orientation * jnp.sin(angle)], dtype=jnp.complex128
    )
    return psi[:, None] * jnp.conjugate(psi[None, :])


def _reference_density(reference: dict[str, object]) -> jax.Array:
    x, y, z = (
        jnp.asarray(value, dtype=jnp.float64)
        for value in reference["reference_bloch_vector"]
    )
    one = jnp.asarray(1.0, dtype=jnp.float64)
    return jnp.asarray(
        [
            [(one + z) / 2.0, (x - 1j * y) / 2.0],
            [(x + 1j * y) / 2.0, (one - z) / 2.0],
        ],
        dtype=jnp.complex128,
    )


def _relative_entropy_nats(rho: jax.Array, sigma: jax.Array) -> jax.Array:
    rho_eigenvalues = jnp.linalg.eigvalsh(rho)
    positive = rho_eigenvalues > jnp.asarray(1.0e-300, dtype=jnp.float64)
    safe_rho = jnp.where(positive, rho_eigenvalues, 1.0)
    rho_log_rho = jnp.sum(jnp.where(positive, rho_eigenvalues * jnp.log(safe_rho), 0.0))

    sigma_eigenvalues, sigma_eigenvectors = jnp.linalg.eigh(sigma)
    log_sigma = (sigma_eigenvectors * jnp.log(sigma_eigenvalues)[None, :]) @ jnp.conjugate(
        sigma_eigenvectors.T
    )
    rho_log_sigma = jnp.real(jnp.trace(rho @ log_sigma))
    return rho_log_rho - rho_log_sigma


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: jax_leg.py <rows_v1.json> <references_v1.json> <out.json>")

    assert jax.config.x64_enabled
    rows_payload, rows_sha256 = _load(Path(sys.argv[1]))
    references_payload, references_sha256 = _load(Path(sys.argv[2]))
    rows = sorted(rows_payload["rows"], key=lambda row: int(row["row_id"]))
    references = references_payload["references"]
    if len(rows) != 18:
        raise ValueError(f"expected 18 rows, received {len(rows)}")
    if len(references) != 11:
        raise ValueError(f"expected 11 references, received {len(references)}")

    row_densities = [_row_density(row) for row in rows]
    variants = []
    for reference in references:
        sigma = _reference_density(reference)
        values = jnp.asarray(
            [_relative_entropy_nats(rho, sigma) for rho in row_densities],
            dtype=jnp.float64,
        )
        assert values.dtype == jnp.dtype(jnp.float64)
        variants.append(
            {
                "variant_id": reference["variant_id"],
                "values": [float(value) for value in jax.device_get(values)],
            }
        )

    output = {
        "schema_version": "l6_phase_entropy_candidate_leg/1.0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "substrate": "jax",
        "version": jax.__version__,
        "x64": True,
        "dtype": "float64/complex128",
        "rows_input_sha256": rows_sha256,
        "references_input_sha256": references_sha256,
        "variants": variants,
    }
    Path(sys.argv[3]).write_text(
        json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
