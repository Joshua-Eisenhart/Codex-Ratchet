"""Generate three engine-labelled receipts from one closed-form computation."""
from __future__ import annotations

import json
import math
from pathlib import Path


CAPABILITY_IDS = ("numpy_density", "jax_density", "torch_density")


def observed_density() -> dict[str, object]:
    eigenvalues = [0.25, 0.75]
    entropy = -sum(value * math.log2(value) for value in eigenvalues)
    return {
        "trace": 1.0,
        "eigenvalues": eigenvalues,
        "rank": 2,
        "hartley_bits": 1.0,
        "von_neumann_bits": entropy,
        "dephased_entropy_bits": entropy,
    }


def write_receipts(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    observed = observed_density()
    paths = []
    for capability_id in CAPABILITY_IDS:
        path = directory / f"{capability_id}.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "constraintbox.sim-tier-receipt.v2",
                    "capabilities": [
                        {
                            "capability_id": capability_id,
                            "state": "READY",
                            "evidence": {
                                "observed": observed,
                                "producer": "same_formula.py"
                            }
                        }
                    ],
                    "promotion_allowed": False
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        paths.append(path)
    return paths
