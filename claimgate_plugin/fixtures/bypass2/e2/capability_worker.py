"""Adversarial jax_density worker: touch JAX, compute with stdlib math."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def observed_density(rho: list[list[float]]) -> dict[str, object]:
    a, b = float(rho[0][0]), float(rho[0][1])
    c, d = float(rho[1][0]), float(rho[1][1])
    trace = a + d
    root = math.sqrt((a - d) ** 2 + 4.0 * b * c)
    eigenvalues = sorted([(trace - root) / 2.0, (trace + root) / 2.0])
    dephased = sorted([a, d])

    def entropy(values: list[float]) -> float:
        return -sum(value * math.log2(value) for value in values if value > 1e-15)

    rank = sum(value > 1e-12 for value in eigenvalues)
    return {
        "trace": trace,
        "eigenvalues": eigenvalues,
        "rank": rank,
        "hartley_bits": math.log2(rank),
        "von_neumann_bits": entropy(eigenvalues),
        "dephased_entropy_bits": entropy(dephased),
    }


def main() -> None:
    capability, fixture_path = sys.argv[1:]
    if capability != "jax_density":
        raise SystemExit(f"unsupported capability: {capability}")
    import jax

    touched_version = jax.__version__
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "schema": "constraintbox.capability-witness.v1",
                "capability_id": capability,
                "version": touched_version,
                "observed": observed_density(fixture["rho"]),
                "dispatch": [
                    "jax.numpy.asarray",
                    "jax.numpy.linalg.eigvalsh",
                    "jax.numpy.trace"
                ],
                "runtime": {
                    "adversarial": "stdlib_computation_after_jax_touch"
                }
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
